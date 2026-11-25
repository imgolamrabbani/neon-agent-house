"""Agent House v4 — Continuous Never-Idle Multi-Niche Portfolio Engine.

Instead of stopping after 1 product and hoping for sales, v4 continuously drains
state/niche_queue.json through the full Google ADK 2.15.0 Workflow graph,
skips already-verified niches, logs portfolio velocity, and regenerates the
unified multi-product catalog summary.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_house.config import DEFAULT_MODEL_ID, HALL_ROOM_JSON, STATE_DIR, get_gemini_api_key
from agent_house.hall_room import load_hall_room

NICHE_QUEUE_JSON = STATE_DIR / "niche_queue.json"
PORTFOLIO_STATUS_JSON = STATE_DIR / "portfolio_status.json"


def load_niche_queue(queue_path: Path = NICHE_QUEUE_JSON) -> dict[str, Any]:
    if not queue_path.exists():
        return {"revenue_target_usd": 5.0, "max_products_per_cycle": 3, "queue": []}
    return json.loads(queue_path.read_text(encoding="utf-8"))


async def run_continuous_portfolio(
    *,
    queue_path: Path = NICHE_QUEUE_JSON,
    hall_room_json: Path = HALL_ROOM_JSON,
    status_path: Path = PORTFOLIO_STATUS_JSON,
    model: str = DEFAULT_MODEL_ID,
    max_new_runs: int = 3,
    check_live_urls: bool = True,
) -> dict[str, Any]:
    """Execute queued unverified niches back-to-back through ADK 2.15.0 Workflow."""
    from agent_house.cli import run_workflow_once

    qdata = load_niche_queue(queue_path)
    board = load_hall_room(hall_room_json)
    already_verified = {
        opp.get("niche_id")
        for opp in board.get("verified_opportunities", [])
        if opp.get("status") == "READY_FOR_MONETIZATION"
    }

    executed: list[dict[str, Any]] = []
    skipped: list[str] = []
    pending_live_key: list[str] = []

    for item in qdata.get("queue", []):
        niche_id = item.get("niche_id", "")
        if niche_id in already_verified:
            skipped.append(niche_id)
            continue
        if len(executed) >= max_new_runs:
            break

        bundle_path_str = item.get("replay_file")
        bundle_path = Path(bundle_path_str) if bundle_path_str else None
        if bundle_path is None and not get_gemini_api_key():
            pending_live_key.append(niche_id)
            continue
        if bundle_path and not bundle_path.exists():
            continue

        events = await run_workflow_once(
            directive=item["directive"],
            model=model,
            replay_file=bundle_path,
            version_tag=item.get("version_tag", "v4"),
            check_live_urls=check_live_urls,
        )
        final_outputs = [e["output"] for e in events if isinstance(e.get("output"), dict)]
        final_pkg = final_outputs[-1] if final_outputs else {"status": "UNKNOWN"}
        executed.append(
            {
                "niche_id": niche_id,
                "status": final_pkg.get("status"),
                "scores": final_pkg.get("scores", {}),
                "research_rounds": final_pkg.get("research_rounds", 0),
                "mvp_rounds": final_pkg.get("mvp_rounds", 0),
            }
        )

    updated_board = load_hall_room(hall_room_json)
    summary = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": "v4",
        "revenue_target_usd": qdata.get("revenue_target_usd", 5.0),
        "total_verified_products": len(updated_board.get("verified_opportunities", [])),
        "verified_niche_ids": [o.get("niche_id") for o in updated_board.get("verified_opportunities", [])],
        "executed_this_cycle": executed,
        "skipped_already_verified": skipped,
        "pending_live_api_key": pending_live_key,
        "remaining_backlog": [
            i.get("niche_id")
            for i in qdata.get("queue", [])
            if i.get("niche_id")
            not in {o.get("niche_id") for o in updated_board.get("verified_opportunities", [])}
        ],
    }
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def run_continuous_sync(**kwargs: Any) -> dict[str, Any]:
    return asyncio.run(run_continuous_portfolio(**kwargs))
