"""Verification tests for Neon Agent House Google ADK 2.x Workflow graph."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from google.adk.runners import InMemoryRunner
from google.genai import types

from agent_house.graph import build_agent_house_workflow
from agent_house.hall_room import HallRoomAccessError, load_hall_room, promote_verified_entry
from agent_house.weekly import run_weekly_review


def _good_pain_report() -> dict:
    return {
        "candidates": [
            {
                "niche_id": "test-niche-01",
                "title": "Invoice Follow-Up Automation",
                "buyer_persona": "Solo freelance web developers",
                "recurring_pain": "Manually chasing unpaid invoices across spreadsheets",
                "current_workaround": "Manual Gmail reminders",
                "urgency_signal": "Direct cashflow delay",
                "evidence": [
                    {"verbatim_quote": "I kept losing hours every week writing checking in emails for unpaid invoices.", "source_url": "https://news.ycombinator.com/item?id=47243082", "source_context": "HN 2026"},
                    {"verbatim_quote": "The invoicing SaaS I was using raised its card processing fee to 6.9%.", "source_url": "https://news.ycombinator.com/item?id=48920389", "source_context": "HN 2026"},
                    {"verbatim_quote": "Around 10k had been overlooked by AP over the course of a few years.", "source_url": "https://news.ycombinator.com/item?id=18129101", "source_context": "HN"},
                ],
            }
        ]
    }


def _bad_pain_report() -> dict:
    return {
        "candidates": [
            {
                "niche_id": "test-niche-01",
                "title": "Dropshipping Magic",
                "buyer_persona": "",
                "recurring_pain": "",
                "evidence": [{"verbatim_quote": "short", "source_url": "not-a-url"}],
            }
        ]
    }


def _good_economics_report() -> dict:
    return {
        "competitors": [
            {"name": "HoneyBook", "live_pricing_url": "https://www.honeybook.com/pricing", "verified_price_tiers": "$36-$129/mo", "main_gap": "Expensive monthly subscription"},
            {"name": "Dubsado", "live_pricing_url": "https://www.dubsado.com/pricing", "verified_price_tiers": "$35-$55/mo", "main_gap": "Heavy CRM setup"},
            {"name": "HelloBonsai", "live_pricing_url": "https://www.hellobonsai.com/pricing", "verified_price_tiers": "$15-$59/user/mo", "main_gap": "Per-seat recurring cost"},
        ],
        "recommended_price_point": "$29 one-time",
        "fixed_monthly_cost_usd": 0,
        "estimated_mvp_hours": 6,
        "unit_economics": {
            "price_usd": 29,
            "platform_fee_rate": 0.10,
            "conservative_monthly_buyers": 10,
            "base_monthly_buyers": 35,
            "conservative_monthly_net_usd": 261.0,
            "base_monthly_net_usd": 913.5,
        },
        "top_distribution_risk": "Organic customer acquisition without paid ads requires strong launch distribution.",
    }


def _make_mvp(tmp_path: Path, valid: bool = True) -> dict:
    mvp_dir = tmp_path / "mvp"
    mvp_dir.mkdir(exist_ok=True)
    spec = mvp_dir / "build_spec.md"
    spec.write_text("# Build Spec\n" + ("Detailed architecture and weekend checklist. " * 15), encoding="utf-8")
    script = mvp_dir / "tool.py"
    if valid:
        script.write_text(
            "#!/usr/bin/env python3\n"
            "\"\"\"Zero-dependency starter invoice tracker MVP for solo freelancers.\"\"\"\n"
            "def audit_overdue(items):\n"
            "    return [i for i in items if i['days_overdue'] > 0]\n\n"
            "def main():\n"
            "    items = [{'client': 'Acme Studio', 'days_overdue': 14, 'amount': 1200}]\n"
            "    overdue = audit_overdue(items)\n"
            "    total = sum(i['amount'] for i in overdue)\n"
            "    print(f'Overdue invoices: {len(overdue)} | Total: ${total}')\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n",
            encoding="utf-8",
        )
    else:
        script.write_text("# TODO stub\nraise NotImplementedError()\n", encoding="utf-8")
    return {
        "niche_id": "test-niche-01",
        "spec_path": str(spec),
        "artifact_path": str(script),
        "test_command": "{python} tool.py",
    }


def _run_graph(wf, payload: dict) -> list:
    async def _exec():
        runner = InMemoryRunner(node=wf, app_name="test_house")
        session = await runner.session_service.create_session(app_name="test_house", user_id="u1")
        msg = types.Content(role="user", parts=[types.Part.from_text(text=json.dumps(payload))])
        evs = []
        async for ev in runner.run_async(user_id="u1", session_id=session.id, new_message=msg):
            evs.append(ev)
        await runner.close()
        return evs

    return asyncio.run(_exec())


def test_hall_room_write_authority_enforced(tmp_path: Path):
    with pytest.raises(HallRoomAccessError):
        promote_verified_entry(
            caller="pain-point-scout",
            entry={"niche_id": "x"},
            json_path=tmp_path / "hall_room.json",
            md_path=tmp_path / "hall_room.md",
        )


def test_parallel_fanout_retry_loop_and_hall_room_promotion(tmp_path: Path):
    scout_calls = []

    def scout_fn(_brief, round_num, fixes):
        scout_calls.append((round_num, fixes))
        return _bad_pain_report() if round_num == 0 else _good_pain_report()

    wf = build_agent_house_workflow(
        scout_provider=scout_fn,
        analyst_provider=lambda _b, _r, _f: _good_economics_report(),
        builder_provider=lambda _n, _r, _f: _make_mvp(tmp_path, valid=True),
        check_live_urls=False,
        execute_mvp_test=True,
        hall_room_json=tmp_path / "hall_room.json",
        hall_room_md=tmp_path / "hall_room.md",
        memory_md=tmp_path / "memory.md",
        runs_jsonl=tmp_path / "runs.jsonl",
        version_tag="v1",
    )

    events = _run_graph(wf, {"directive": "Solo freelancer ops", "final_command": True})
    outputs = [e.output for e in events if getattr(e, "output", None)]
    final_pkg = outputs[-1]

    assert len(scout_calls) == 2  # Round 0 failed -> Verifier routed retry -> Round 1 passed
    assert final_pkg["status"] == "VERIFIED_COMPLETE"
    assert final_pkg["research_rounds"] == 1
    assert final_pkg["mvp_rounds"] == 0
    assert final_pkg["external_release_decision"] == "LOCAL_ONLY_AUTONOMOUS"

    board = load_hall_room(tmp_path / "hall_room.json")
    assert len(board["verified_opportunities"]) == 1
    assert board["verified_opportunities"][0]["status"] == "READY_FOR_MONETIZATION"

    weekly = run_weekly_review(
        runs_path=tmp_path / "runs.jsonl",
        memory_path=tmp_path / "memory.md",
        output_dir=tmp_path / "weekly_reviews",
    )
    assert weekly["status"] == "PROPOSAL_READY"
    assert weekly["packages_delivered"] == 1
    assert weekly["weakest_agent"] == "pain_point_scout"
    assert weekly["retries_by_agent"]["pain_point_scout"] == 1
    assert weekly["avg_initial_scores"]["pain_point_scout"] < 100


def test_quote_grounding_catches_fabricated_quote():
    from agent_house.verifier_tools import _quote_grounded_in_page

    ok_real, ratio_real = _quote_grounded_in_page(
        "I kept losing hours every week writing checking in emails for unpaid invoices.",
        "Hey HN, I kept losing hours every week writing just checking in emails for unpaid invoices.",
    )
    ok_fake, ratio_fake = _quote_grounded_in_page(
        "Quantum blockchain toaster revolutionizes banana farming instantly.",
        "Hey HN, I kept losing hours every week writing emails for unpaid invoices.",
    )
    assert ok_real and ratio_real >= 0.45
    assert not ok_fake and ratio_fake < 0.45


def test_round_2_escalation_never_pollutes_hall_room(tmp_path: Path):
    wf = build_agent_house_workflow(
        scout_provider=lambda _b, _r, _f: _bad_pain_report(),
        analyst_provider=lambda _b, _r, _f: _good_economics_report(),
        builder_provider=lambda _n, _r, _f: _make_mvp(tmp_path, valid=True),
        check_live_urls=False,
        execute_mvp_test=True,
        hall_room_json=tmp_path / "hall_room.json",
        hall_room_md=tmp_path / "hall_room.md",
        memory_md=tmp_path / "memory.md",
        runs_jsonl=tmp_path / "runs.jsonl",
    )
    events = _run_graph(wf, {"directive": "Bad run test", "final_command": True})
    final_out = [e.output for e in events if getattr(e, "output", None)][-1]
    assert final_out["status"] == "ESCALATED_ROUND_2"
    assert final_out["escalation_reason"]["round"] == 2
    assert load_hall_room(tmp_path / "hall_room.json")["verified_opportunities"] == []


def test_external_release_pauses_at_adk_hitl_gate(tmp_path: Path):
    wf = build_agent_house_workflow(
        scout_provider=lambda _b, _r, _f: _good_pain_report(),
        analyst_provider=lambda _b, _r, _f: _good_economics_report(),
        builder_provider=lambda _n, _r, _f: _make_mvp(tmp_path, valid=True),
        check_live_urls=False,
        execute_mvp_test=True,
        hall_room_json=tmp_path / "hall_room.json",
        hall_room_md=tmp_path / "hall_room.md",
        memory_md=tmp_path / "memory.md",
        runs_jsonl=tmp_path / "runs.jsonl",
    )
    events = _run_graph(
        wf,
        {
            "directive": "External release gate check",
            "final_command": True,
            "external_release_requested": True,
            "external_preauthorized": False,
        },
    )
    # ADK 2.x RequestInput produces an interrupt/input-request event pausing before external_release_complete
    final_outputs = [e.output for e in events if getattr(e, "output", None)]
    assert not any(
        isinstance(o, dict) and o.get("external_release_decision") == "APPROVED"
        for o in final_outputs
    )
    assert any(
        "External release requested" in str(e) for e in events
    )


def test_v4_continuous_queue_skips_verified_and_runs_new(tmp_path: Path):
    from agent_house.continuous import run_continuous_sync

    qpath = tmp_path / "niche_queue.json"
    bpath = tmp_path / "bundle.json"
    mvp = _make_mvp(tmp_path, valid=True)
    bpath.write_text(
        json.dumps(
            {
                "directive": "Queue test",
                "pain_point_scout_rounds": [_good_pain_report()],
                "market_roi_analyst_rounds": [_good_economics_report()],
                "mvp_builder_rounds": [mvp],
            }
        ),
        encoding="utf-8",
    )
    qpath.write_text(
        json.dumps(
            {
                "revenue_target_usd": 5.0,
                "queue": [
                    {
                        "niche_id": "test-niche-01",
                        "directive": "Queue test",
                        "replay_file": str(bpath),
                        "version_tag": "v4",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    # Smoke-verify continuous loader & deduplication status
    from agent_house.continuous import load_niche_queue
    loaded = load_niche_queue(qpath)
    assert loaded["revenue_target_usd"] == 5.0
    assert len(loaded["queue"]) == 1


