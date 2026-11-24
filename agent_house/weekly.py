"""Weekly Self-Improvement Loop for Neon Agent House (v2+ initial-score aware).

Reads runs.jsonl + memory.md, computes north-star metrics (First-Pass Rate %,
packages/week, initial vs final scores, retries per agent), identifies the true
weakest agent, and drafts ONE surgical prompt proposal to state/weekly_reviews/.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_house.config import MEMORY_MD, RUNS_JSONL, WEEKLY_REVIEWS_DIR
from agent_house.hall_room import load_run_logs, read_memory

PROPOSED_IMPROVEMENTS = {
    "pain_point_scout": (
        "Run agent_house.discovery_tools.preflight_filter_urls() before submitting so blocked 403/404 links "
        "never fail Round 0, and copy exact verbatim quotes directly from live HN/GitHub responses."
    ),
    "market_roi_analyst": (
        "Require explicit formula breakdown (price_usd * (1 - platform_fee_rate) * buyers) "
        "and verify live HTTP 200 pricing text on every competitor /pricing page before submitting."
    ),
    "mvp_builder": (
        "Require both a passing --self-test flag and a standalone dark-mode interactive HTML UI "
        "plus buyer ZIP package before handing off to hall-room-verifier."
    ),
}


def run_weekly_review(
    *,
    runs_path: Path = RUNS_JSONL,
    memory_path: Path = MEMORY_MD,
    output_dir: Path = WEEKLY_REVIEWS_DIR,
) -> dict[str, Any]:
    logs = load_run_logs(runs_path)
    if not logs:
        return {
            "status": "NO_RUNS_YET",
            "message": "No entries in runs.jsonl yet. Run at least one directive first.",
        }

    total_runs = len(logs)
    first_pass_count = sum(1 for r in logs if r.get("first_pass"))
    first_pass_rate = round((first_pass_count / total_runs) * 100, 1)
    packages_delivered = sum(int(r.get("verified_packages_delivered", 0)) for r in logs)

    initial_scores: dict[str, list[float]] = defaultdict(list)
    final_scores: dict[str, list[float]] = defaultdict(list)
    retries_total: dict[str, int] = defaultdict(int)

    for row in logs:
        init_map = row.get("initial_scores") or row.get("scores") or {}
        final_map = row.get("scores") or {}
        retry_map = row.get("retries_by_agent") or {}
        for agent, score in init_map.items():
            initial_scores[agent].append(float(score))
        for agent, score in final_map.items():
            final_scores[agent].append(float(score))
        for agent, count in retry_map.items():
            retries_total[agent] += int(count)

    avg_initial = {
        agent: round(sum(vals) / len(vals), 1)
        for agent, vals in initial_scores.items()
        if vals
    }
    avg_final = {
        agent: round(sum(vals) / len(vals), 1)
        for agent, vals in final_scores.items()
        if vals
    }

    # Pick weakest agent by lowest Round-0 initial score, breaking ties by highest retry count
    weakest_agent = (
        min(
            avg_initial,
            key=lambda a: (avg_initial[a], -retries_total.get(a, 0)),
        )
        if avg_initial
        else "pain_point_scout"
    )
    proposal = PROPOSED_IMPROVEMENTS.get(
        weakest_agent,
        "Tighten the agent's DONE WELL checklist to eliminate its top recurring Verifier failure.",
    )

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_dir.mkdir(parents=True, exist_ok=True)
    review_path = output_dir / f"{today}.md"
    memory_lines = len(read_memory(memory_path).splitlines())

    report_md = "\n".join(
        [
            f"# Agent House Weekly Improvement Proposal — {today}",
            "",
            "## North-Star Metrics",
            f"- **Total Runs Analyzed:** {total_runs}",
            f"- **Verifier First-Pass Rate:** {first_pass_rate}% ({first_pass_count}/{total_runs})",
            f"- **Validated Monetization Packages Delivered:** {packages_delivered}",
            f"- **Team Memory Footprint:** {memory_lines} lines (`state/memory.md`)",
            "",
            "## Per-Agent Performance (Round-0 Initial vs Final Score & Retries)",
            *[
                f"- `{agent}`: initial **{avg_initial.get(agent, 0)}/100** → final **{avg_final.get(agent, 0)}/100** (retries: {retries_total.get(agent, 0)})"
                for agent in sorted(avg_initial)
            ],
            "",
            f"## Weakest Agent Identified: `{weakest_agent}` (initial avg {avg_initial.get(weakest_agent, 0)}/100, retries={retries_total.get(weakest_agent, 0)})",
            "",
            "## Proposed Single Prompt Change (Awaiting Your Approval)",
            f"- **Target Skill:** `.agent/skills/{weakest_agent.replace('_', '-')}/SKILL.md`",
            f"- **Proposed Edit:** {proposal}",
            "",
            "> **Approval Gate:** No prompt files were modified. Reply `approve` to apply this exact change.",
            "",
        ]
    )
    review_path.write_text(report_md, encoding="utf-8")

    return {
        "status": "PROPOSAL_READY",
        "review_path": str(review_path),
        "total_runs": total_runs,
        "first_pass_rate_pct": first_pass_rate,
        "packages_delivered": packages_delivered,
        "avg_initial_scores": avg_initial,
        "avg_final_scores": avg_final,
        "retries_by_agent": dict(retries_total),
        "weakest_agent": weakest_agent,
        "proposed_change": proposal,
    }
