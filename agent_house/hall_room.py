"""Shared Hall Room storage, team memory, and run telemetry.

Write-authority invariant: ONLY 'hall-room-verifier' may promote records into
hall_room.json and hall_room.md.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_house.config import (
    HALL_ROOM_JSON,
    HALL_ROOM_MD,
    MEMORY_MD,
    RUNS_JSONL,
    STATE_DIR,
)

HALL_ROOM_WRITER = "hall-room-verifier"
ALLOWED_HALL_ROOM_WRITERS = {"hall-room-verifier", "yt-video-verifier"}
MAX_MEMORY_BULLETS = 30


class HallRoomAccessError(PermissionError):
    """Raised when a non-verifier agent attempts to mutate the Hall Room."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=path.suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def load_hall_room(json_path: Path = HALL_ROOM_JSON) -> dict[str, Any]:
    if not json_path.exists():
        return {
            "schema_version": "2.0.0",
            "house_name": "Neon Agent House (Multi-Wing)",
            "write_authority": sorted(ALLOWED_HALL_ROOM_WRITERS),
            "updated_at": _utc_now(),
            "verified_opportunities": [],
            "verified_youtube_shorts": [],
        }
    return json.loads(json_path.read_text(encoding="utf-8"))


def render_hall_room_markdown(board: dict[str, Any]) -> str:
    lines = [
        "# Neon Agent House — Shared Hall Room",
        "",
        f"> **Write Authority:** Exclusively `{HALL_ROOM_WRITER}` | **Last Updated:** {board.get('updated_at', _utc_now())}",
        "",
    ]
    opportunities = board.get("verified_opportunities", [])
    if not opportunities:
        lines.append("_No verified opportunities promoted yet._")
        return "\n".join(lines) + "\n"

    for opp in opportunities:
        lines.extend(
            [
                f"## {opp.get('niche_id', 'unknown')} — {opp.get('title', 'Untitled')}",
                f"- **Status:** `{opp.get('status', 'VERIFIED')}` | **Research Score:** {opp.get('research_score', 0)}/100 | **MVP Score:** {opp.get('mvp_score', 'pending')}",
                f"- **Buyer Persona:** {opp.get('buyer_persona', '')}",
                f"- **Recurring Pain:** {opp.get('recurring_pain', '')}",
                f"- **Recommended Offer:** {opp.get('recommended_price_point', '')} | **Fixed Stack Cost:** {opp.get('fixed_stack_cost', '$0/mo')}",
                f"- **Unit Economics:** {opp.get('unit_economics_summary', '')}",
                f"- **Top Risk:** {opp.get('top_distribution_risk', '')}",
                "- **Verified Primary Evidence:**",
            ]
        )
        for ev in opp.get("evidence", []):
            lines.append(
                f"  - \"{ev.get('verbatim_quote', '')}\" — {ev.get('source_url', '')} ({ev.get('source_context', '')})"
            )
        lines.append("- **Verified Competitors:**")
        for comp in opp.get("competitors", []):
            lines.append(
                f"  - **{comp.get('name', '')}**: {comp.get('verified_price_tiers', '')} ({comp.get('live_pricing_url', '')}) — Gap: {comp.get('main_gap', '')}"
            )
        mvp = opp.get("mvp")
        if mvp:
            lines.extend(
                [
                    "- **Verified MVP Artifact:**",
                    f"  - Spec: `{mvp.get('spec_path', '')}`",
                    f"  - Runnable Artifact: `{mvp.get('artifact_path', '')}`",
                    f"  - Test Command: `{mvp.get('test_command', '')}` (exit={mvp.get('test_exit_code', '')})",
                ]
            )
        lines.append("")

    shorts = board.get("verified_youtube_shorts", [])
    if shorts:
        lines.extend(["---", "", "# Wing 2 — Verified YouTube Shorts (`yt-video-verifier`)", ""])
        for sh in shorts:
            lines.extend(
                [
                    f"## {sh.get('short_id', 'short')} — {sh.get('title', 'Untitled Short')}",
                    f"- **Status:** `{sh.get('status', 'QA_PASSED')}` | **QA Score:** {sh.get('qa_score', 0)}/100 | **Resolution:** {sh.get('resolution', '1080x1920')} | **Duration:** {sh.get('duration_sec', 0)}s",
                    f"- **Linked Wing 1 Product:** `{sh.get('linked_niche_id', '')}` ({sh.get('cta_url', '')})",
                    f"- **MP4 File:** `{sh.get('video_path', '')}`",
                    f"- **Thumbnail:** `{sh.get('thumbnail_path', '')}`",
                    f"- **YouTube URL:** {sh.get('youtube_url', 'ready_for_upload')}",
                    "",
                ]
            )
    return "\n".join(lines).strip() + "\n"


def promote_verified_short(
    *,
    caller: str,
    entry: dict[str, Any],
    json_path: Path = HALL_ROOM_JSON,
    md_path: Path = HALL_ROOM_MD,
) -> dict[str, Any]:
    """Atomically upsert a QA-verified YouTube Short into hall_room.json & hall_room.md."""
    if caller not in ALLOWED_HALL_ROOM_WRITERS:
        raise HallRoomAccessError(
            f"Access denied: '{caller}' cannot write to Hall Room. Authorized: {sorted(ALLOWED_HALL_ROOM_WRITERS)}."
        )
    if not entry.get("short_id"):
        raise ValueError("Verified YouTube Short entry requires 'short_id'.")

    board = load_hall_room(json_path)
    board["schema_version"] = "2.0.0"
    board["updated_at"] = _utc_now()
    entry_copy = dict(entry)
    entry_copy["verified_at"] = board["updated_at"]

    shorts = board.setdefault("verified_youtube_shorts", [])
    replaced = False
    for idx, existing in enumerate(shorts):
        if existing.get("short_id") == entry_copy["short_id"]:
            merged = dict(existing)
            merged.update(entry_copy)
            shorts[idx] = merged
            replaced = True
            break
    if not replaced:
        shorts.append(entry_copy)

    _atomic_write(json_path, json.dumps(board, indent=2) + "\n")
    _atomic_write(md_path, render_hall_room_markdown(board))
    return board


def promote_verified_entry(
    *,
    caller: str,
    entry: dict[str, Any],
    json_path: Path = HALL_ROOM_JSON,
    md_path: Path = HALL_ROOM_MD,
) -> dict[str, Any]:
    """Atomically upsert a verified opportunity into hall_room.json & hall_room.md."""
    if caller != HALL_ROOM_WRITER:
        raise HallRoomAccessError(
            f"Access denied: '{caller}' cannot write to Hall Room. Only '{HALL_ROOM_WRITER}' is authorized."
        )
    if not entry.get("niche_id"):
        raise ValueError("Verified Hall Room entry requires 'niche_id'.")

    board = load_hall_room(json_path)
    board["updated_at"] = _utc_now()
    entry_copy = dict(entry)
    entry_copy["verified_at"] = board["updated_at"]

    opportunities = board.setdefault("verified_opportunities", [])
    replaced = False
    for idx, existing in enumerate(opportunities):
        if existing.get("niche_id") == entry_copy["niche_id"]:
            merged = dict(existing)
            merged.update(entry_copy)
            opportunities[idx] = merged
            replaced = True
            break
    if not replaced:
        opportunities.append(entry_copy)

    _atomic_write(json_path, json.dumps(board, indent=2) + "\n")
    _atomic_write(md_path, render_hall_room_markdown(board))
    return board


def read_memory(memory_path: Path = MEMORY_MD) -> str:
    if not memory_path.exists():
        return ""
    return memory_path.read_text(encoding="utf-8")


def append_memory_lesson(lesson: str, memory_path: Path = MEMORY_MD) -> None:
    """Append a single concise bullet under Learned Patterns, capping total bullets."""
    cleaned = " ".join(lesson.strip().split())
    if not cleaned:
        return
    current = read_memory(memory_path)
    bullet = f"- {cleaned}"
    if bullet in current:
        return

    lines = current.splitlines() if current else ["# Agent House Team Memory (`memory.md`)", "", "## Learned Patterns"]
    lines = [ln for ln in lines if ln.strip() != "- (Populated automatically after Run 1.)"]
    if "## Learned Patterns" not in lines:
        lines.extend(["", "## Learned Patterns"])
    lines.append(bullet)

    # Enforce 30-bullet cap by pruning oldest Learned Patterns bullets first
    bullet_indices = [i for i, ln in enumerate(lines) if ln.startswith("- ")]
    if len(bullet_indices) > MAX_MEMORY_BULLETS:
        try:
            lp_start = lines.index("## Learned Patterns") + 1
        except ValueError:
            lp_start = 0
        lp_bullets = [i for i in bullet_indices if i >= lp_start]
        excess = len(bullet_indices) - MAX_MEMORY_BULLETS
        to_drop = set(lp_bullets[:excess])
        lines = [ln for i, ln in enumerate(lines) if i not in to_drop]

    _atomic_write(memory_path, "\n".join(lines).strip() + "\n")


def append_run_log(record: dict[str, Any], runs_path: Path = RUNS_JSONL) -> dict[str, Any]:
    runs_path.parent.mkdir(parents=True, exist_ok=True)
    stamped = {"timestamp": _utc_now(), **record}
    with runs_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(stamped) + "\n")
    return stamped


def load_run_logs(runs_path: Path = RUNS_JSONL) -> list[dict[str, Any]]:
    if not runs_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw in runs_path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if raw:
            rows.append(json.loads(raw))
    return rows
