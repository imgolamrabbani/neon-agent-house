"""Google ADK 2.x Graph Workflow for Neon Agent House.

Built directly on Google ADK 2.15.0 Workflow primitives:
- Workflow(edges=[...])
- JoinNode for parallel fan-out / fan-in
- Event(actions=EventActions(route=...)) for deterministic conditional routing
- Capped max-2-round Verifier quality loops (research + MVP)
- Native RequestInput Human-in-the-Loop gate for unapproved external actions only
- Zero deprecated SequentialAgent, ParallelAgent, or LoopAgent classes.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from google.adk import Agent, Context, Event, Workflow
from google.adk.events import EventActions, RequestInput
from google.adk.workflow import JoinNode, START

from agent_house.config import (
    DEFAULT_MODEL_ID,
    HALL_ROOM_JSON,
    HALL_ROOM_MD,
    MAX_QUALITY_ROUNDS,
    MEMORY_MD,
    RUNS_JSONL,
    get_gemini_api_key,
)
from agent_house.hall_room import (
    HALL_ROOM_WRITER,
    append_memory_lesson,
    append_run_log,
    promote_verified_entry,
    read_memory,
)
from agent_house.prompts import load_skill_prompt
from agent_house.verifier_tools import (
    verify_economics_report,
    verify_mvp_bundle,
    verify_pain_report,
)


def _extract_json_block(text: str) -> dict[str, Any]:
    """Parse raw JSON or a ```json fenced block from an LLM response."""
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.S)
    if fence:
        cleaned = fence.group(1)
    return json.loads(cleaned)


def build_live_llm_agents(model: str = DEFAULT_MODEL_ID) -> dict[str, Agent]:
    """Instantiate live Google ADK 2.x LlmAgents backed by Gemini 4 Neon."""
    return {
        "house_lead": Agent(
            name="house_lead_llm",
            model=model,
            instruction=load_skill_prompt("house-lead"),
        ),
        "pain_point_scout": Agent(
            name="pain_point_scout_llm",
            model=model,
            instruction=load_skill_prompt("pain-point-scout"),
        ),
        "market_roi_analyst": Agent(
            name="market_roi_analyst_llm",
            model=model,
            instruction=load_skill_prompt("market-roi-analyst"),
        ),
        "mvp_builder": Agent(
            name="mvp_builder_llm",
            model=model,
            instruction=load_skill_prompt("mvp-builder"),
        ),
        "hall_room_verifier": Agent(
            name="hall_room_verifier_llm",
            model=model,
            instruction=load_skill_prompt("hall-room-verifier"),
        ),
    }


def _call_gemini_json(
    *,
    model: str,
    system_instruction: str,
    user_prompt: str,
) -> dict[str, Any]:
    """Call Gemini API directly using GEMINI_API_KEY env var for structured room output."""
    api_key = get_gemini_api_key()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Export GEMINI_API_KEY in your shell for live mode, "
            "or run with --replay-file to execute the ADK 2.x graph on researched artifacts."
        )
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
        ),
    )
    return _extract_json_block(response.text or "{}")


def build_agent_house_workflow(
    *,
    model: str = DEFAULT_MODEL_ID,
    scout_provider: Callable[[dict[str, Any], int, list[str]], dict[str, Any]] | None = None,
    analyst_provider: Callable[[dict[str, Any], int, list[str]], dict[str, Any]] | None = None,
    builder_provider: Callable[[dict[str, Any], int, list[str]], dict[str, Any]] | None = None,
    check_live_urls: bool = True,
    execute_mvp_test: bool = True,
    hall_room_json: Path = HALL_ROOM_JSON,
    hall_room_md: Path = HALL_ROOM_MD,
    memory_md: Path = MEMORY_MD,
    runs_jsonl: Path = RUNS_JSONL,
    version_tag: str = "v1",
) -> Workflow:
    """Build the Neon Agent House ADK 2.x graph workflow.

    Graph topology:
      START -> house_lead_intake
        -> (parallel fan-out) pain_point_scout & market_roi_analyst
        -> research_join (JoinNode)
        -> research_verifier (max 2 retry rounds -> research_retry_fanout, or ESCALATE, or PASS)
        -> mvp_builder
        -> mvp_verifier (max 2 retry rounds -> mvp_builder, or ESCALATE, or PASS)
        -> house_lead_finalize
        -> external_approval_gate (RequestInput only when external release requested & unapproved)
    """
    lead_prompt = load_skill_prompt("house-lead")
    scout_prompt = load_skill_prompt("pain-point-scout")
    analyst_prompt = load_skill_prompt("market-roi-analyst")
    builder_prompt = load_skill_prompt("mvp-builder")

    def house_lead_intake(ctx: Context, node_input: Any) -> dict[str, Any]:
        """Node 1: House Lead reads memory.md and fans out non-overlapping briefs."""
        raw_input = node_input
        if hasattr(raw_input, "parts") and raw_input.parts:
            texts = [getattr(p, "text", "") for p in raw_input.parts if getattr(p, "text", None)]
            raw_input = "\n".join(texts)

        if isinstance(raw_input, str):
            try:
                payload = json.loads(raw_input)
            except json.JSONDecodeError:
                payload = {"directive": raw_input}
        elif isinstance(raw_input, dict):
            payload = dict(raw_input)
        else:
            payload = {"directive": str(raw_input)}

        directive = payload.get("directive") or str(node_input)
        memory_text = read_memory(memory_md)

        ctx.state["directive"] = directive
        ctx.state["final_command"] = bool(payload.get("final_command", True))
        ctx.state["external_release_requested"] = bool(
            payload.get("external_release_requested", False)
        )
        ctx.state["external_preauthorized"] = bool(
            payload.get("external_preauthorized", False)
        )
        ctx.state["memory_snapshot"] = memory_text
        ctx.state["research_round"] = 0
        ctx.state["mvp_round"] = 0
        ctx.state["scout_passed"] = False
        ctx.state["analyst_passed"] = False
        ctx.state["scout_fixes"] = []
        ctx.state["analyst_fixes"] = []
        ctx.state["mvp_fixes"] = []
        ctx.state["initial_scores"] = {}
        ctx.state["retries_by_agent"] = {
            "pain_point_scout": 0,
            "market_roi_analyst": 0,
            "mvp_builder": 0,
        }
        ctx.state["node_trace"] = []

        briefs = {
            "directive": directive,
            "demand_brief": {
                "directive": directive,
                "goal": "Find >=3 primary-source buyer pain quotes with live URLs.",
                "exclusions": memory_text,
            },
            "economics_brief": {
                "directive": directive,
                "goal": "Audit >=3 real competitors with live pricing URLs and $0 fixed stack unit economics.",
                "fixed_cost_constraint_usd": 0,
                "exclusions": memory_text,
            },
        }
        ctx.state["briefs"] = briefs
        ctx.state["node_trace"].append(
            {
                "node": "house_lead_intake",
                "status": "OK",
                "summary": f"Loaded memory.md ({len(memory_text.splitlines())} lines) and dispatched parallel briefs.",
            }
        )
        return briefs

    def research_retry_fanout(ctx: Context, node_input: Any) -> dict[str, Any]:
        """Re-dispatch only failing discovery rooms while passing rooms reuse cached results."""
        ctx.state["research_round"] = int(ctx.state.get("research_round", 0)) + 1
        return ctx.state["briefs"]

    def pain_point_scout(ctx: Context, node_input: Any) -> dict[str, Any]:
        """Parallel Branch A: Niche & Demand Room."""
        if ctx.state.get("scout_passed") and ctx.state.get("pain_report"):
            return ctx.state["pain_report"]

        round_num = int(ctx.state.get("research_round", 0))
        fixes = list(ctx.state.get("scout_fixes", []))
        brief = ctx.state["briefs"]["demand_brief"]

        if scout_provider is not None:
            report = scout_provider(brief, round_num, fixes)
        else:
            prompt = (
                f"DEMAND BRIEF:\n{json.dumps(brief, indent=2)}\n\n"
                f"RETRY ROUND: {round_num}\nFIXES REQUIRED: {json.dumps(fixes)}\n\n"
                "Return strict JSON with key 'candidates': list of objects containing "
                "niche_id, title, buyer_persona, recurring_pain, current_workaround, "
                "urgency_signal, and evidence (>=3 objects with verbatim_quote, source_url, source_context)."
            )
            report = _call_gemini_json(
                model=model,
                system_instruction=scout_prompt,
                user_prompt=prompt,
            )

        ctx.state["pain_report"] = report
        ctx.state["node_trace"].append(
            {
                "node": "pain_point_scout",
                "round": round_num,
                "status": "DRAFTED",
                "candidates": len(report.get("candidates", [])),
            }
        )
        return report

    def market_roi_analyst(ctx: Context, node_input: Any) -> dict[str, Any]:
        """Parallel Branch B: Economics & Pricing Room."""
        if ctx.state.get("analyst_passed") and ctx.state.get("economics_report"):
            return ctx.state["economics_report"]

        round_num = int(ctx.state.get("research_round", 0))
        fixes = list(ctx.state.get("analyst_fixes", []))
        brief = ctx.state["briefs"]["economics_brief"]

        if analyst_provider is not None:
            report = analyst_provider(brief, round_num, fixes)
        else:
            prompt = (
                f"ECONOMICS BRIEF:\n{json.dumps(brief, indent=2)}\n\n"
                f"RETRY ROUND: {round_num}\nFIXES REQUIRED: {json.dumps(fixes)}\n\n"
                "Return strict JSON with keys: competitors (>=3 with name, live_pricing_url, "
                "verified_price_tiers, main_gap), recommended_price_point, fixed_monthly_cost_usd (must be 0), "
                "estimated_mvp_hours, unit_economics (price_usd, platform_fee_rate, conservative_monthly_buyers, "
                "base_monthly_buyers, conservative_monthly_net_usd, base_monthly_net_usd), top_distribution_risk."
            )
            report = _call_gemini_json(
                model=model,
                system_instruction=analyst_prompt,
                user_prompt=prompt,
            )

        ctx.state["economics_report"] = report
        ctx.state["node_trace"].append(
            {
                "node": "market_roi_analyst",
                "round": round_num,
                "status": "DRAFTED",
                "competitors": len(report.get("competitors", [])),
            }
        )
        return report

    research_join = JoinNode(name="research_join")

    def research_verifier(ctx: Context, node_input: Any) -> Event:
        """Hall Room Verifier — Research Quality Gate (max 2 retry rounds)."""
        round_num = int(ctx.state.get("research_round", 0))
        pain_report = (
            node_input.get("pain_point_scout")
            if isinstance(node_input, dict) and "pain_point_scout" in node_input
            else ctx.state.get("pain_report", {})
        )
        economics_report = (
            node_input.get("market_roi_analyst")
            if isinstance(node_input, dict) and "market_roi_analyst" in node_input
            else ctx.state.get("economics_report", {})
        )

        scout_eval = verify_pain_report(pain_report, check_live_urls=check_live_urls)
        analyst_eval = verify_economics_report(
            economics_report, check_live_urls=check_live_urls
        )

        ctx.state["scout_passed"] = scout_eval["pass"]
        ctx.state["analyst_passed"] = analyst_eval["pass"]
        ctx.state["scout_fixes"] = scout_eval["exact_fixes"]
        ctx.state["analyst_fixes"] = analyst_eval["exact_fixes"]
        if round_num == 0:
            ctx.state["initial_scores"]["pain_point_scout"] = scout_eval["score"]
            ctx.state["initial_scores"]["market_roi_analyst"] = analyst_eval["score"]
        if not scout_eval["pass"]:
            ctx.state["retries_by_agent"]["pain_point_scout"] += 1
        if not analyst_eval["pass"]:
            ctx.state["retries_by_agent"]["market_roi_analyst"] += 1
        ctx.state["research_verification"] = {
            "round": round_num,
            "pain_point_scout": scout_eval,
            "market_roi_analyst": analyst_eval,
            "combined_score": int(round((scout_eval["score"] + analyst_eval["score"]) / 2)),
        }

        if scout_eval["pass"] and analyst_eval["pass"]:
            top_niche = pain_report["candidates"][0]
            ue = economics_report["unit_economics"]
            hall_entry = {
                "niche_id": top_niche["niche_id"],
                "title": top_niche["title"],
                "status": "RESEARCH_VERIFIED",
                "buyer_persona": top_niche["buyer_persona"],
                "recurring_pain": top_niche["recurring_pain"],
                "current_workaround": top_niche.get("current_workaround", ""),
                "urgency_signal": top_niche.get("urgency_signal", ""),
                "evidence": top_niche["evidence"],
                "competitors": economics_report["competitors"],
                "recommended_price_point": economics_report["recommended_price_point"],
                "fixed_stack_cost": f"${economics_report['fixed_monthly_cost_usd']}/mo",
                "estimated_mvp_hours": economics_report.get("estimated_mvp_hours", 6),
                "unit_economics": ue,
                "unit_economics_summary": (
                    f"Conservative: {ue['conservative_monthly_buyers']} buyers/mo = ${ue['conservative_monthly_net_usd']}/mo net | "
                    f"Base: {ue['base_monthly_buyers']} buyers/mo = ${ue['base_monthly_net_usd']}/mo net"
                ),
                "top_distribution_risk": economics_report["top_distribution_risk"],
                "research_score": ctx.state["research_verification"]["combined_score"],
            }
            promote_verified_entry(
                caller=HALL_ROOM_WRITER,
                entry=hall_entry,
                json_path=hall_room_json,
                md_path=hall_room_md,
            )
            ctx.state["verified_niche"] = hall_entry
            ctx.state["node_trace"].append(
                {
                    "node": "research_verifier",
                    "round": round_num,
                    "status": "PASS",
                    "scout_score": scout_eval["score"],
                    "analyst_score": analyst_eval["score"],
                }
            )
            return Event(
                output=ctx.state["research_verification"],
                actions=EventActions(route="PASS"),
            )

        if round_num < MAX_QUALITY_ROUNDS:
            ctx.state["node_trace"].append(
                {
                    "node": "research_verifier",
                    "round": round_num,
                    "status": "RETRY",
                    "scout_score": scout_eval["score"],
                    "analyst_score": analyst_eval["score"],
                    "fixes": {
                        "pain_point_scout": scout_eval["exact_fixes"],
                        "market_roi_analyst": analyst_eval["exact_fixes"],
                    },
                }
            )
            return Event(
                output=ctx.state["research_verification"],
                actions=EventActions(route="RETRY_RESEARCH"),
            )

        ctx.state["escalation_reason"] = {
            "stage": "research_verifier",
            "round": round_num,
            "scout_fixes": scout_eval["exact_fixes"],
            "analyst_fixes": analyst_eval["exact_fixes"],
        }
        ctx.state["node_trace"].append(
            {
                "node": "research_verifier",
                "round": round_num,
                "status": "ESCALATE",
                "scout_score": scout_eval["score"],
                "analyst_score": analyst_eval["score"],
            }
        )
        return Event(
            output=ctx.state["escalation_reason"],
            actions=EventActions(route="ESCALATE"),
        )

    def mvp_builder(ctx: Context, node_input: Any) -> dict[str, Any]:
        """Build Room: builds runnable starter MVP artifact + build spec."""
        round_num = int(ctx.state.get("mvp_round", 0))
        fixes = list(ctx.state.get("mvp_fixes", []))
        verified_niche = ctx.state["verified_niche"]

        if builder_provider is not None:
            bundle = builder_provider(verified_niche, round_num, fixes)
        else:
            prompt = (
                f"VERIFIED NICHE:\n{json.dumps(verified_niche, indent=2)}\n\n"
                f"RETRY ROUND: {round_num}\nFIXES REQUIRED: {json.dumps(fixes)}\n\n"
                "Return strict JSON with keys: spec_markdown, artifact_filename, artifact_code, test_command."
            )
            llm_out = _call_gemini_json(
                model=model,
                system_instruction=builder_prompt,
                user_prompt=prompt,
            )
            niche_dir = Path(hall_room_json).resolve().parent.parent / "mvp_bundle" / verified_niche["niche_id"]
            niche_dir.mkdir(parents=True, exist_ok=True)
            spec_path = niche_dir / "build_spec.md"
            artifact_path = niche_dir / llm_out["artifact_filename"]
            spec_path.write_text(llm_out["spec_markdown"], encoding="utf-8")
            artifact_path.write_text(llm_out["artifact_code"], encoding="utf-8")
            bundle = {
                "niche_id": verified_niche["niche_id"],
                "spec_path": str(spec_path),
                "artifact_path": str(artifact_path),
                "test_command": llm_out["test_command"],
            }

        ctx.state["mvp_bundle"] = bundle
        ctx.state["node_trace"].append(
            {
                "node": "mvp_builder",
                "round": round_num,
                "status": "BUILT",
                "artifact_path": bundle.get("artifact_path", ""),
            }
        )
        return bundle

    def mvp_verifier(ctx: Context, node_input: Any) -> Event:
        """Hall Room Verifier — MVP Build Quality Gate (max 2 retry rounds)."""
        round_num = int(ctx.state.get("mvp_round", 0))
        bundle = ctx.state["mvp_bundle"]
        mvp_eval = verify_mvp_bundle(bundle, execute_test=execute_mvp_test)

        ctx.state["mvp_verification"] = {
            "round": round_num,
            "mvp_builder": mvp_eval,
        }
        ctx.state["mvp_fixes"] = mvp_eval["exact_fixes"]
        if round_num == 0:
            ctx.state["initial_scores"]["mvp_builder"] = mvp_eval["score"]
        if not mvp_eval["pass"]:
            ctx.state["retries_by_agent"]["mvp_builder"] += 1

        if mvp_eval["pass"]:
            niche = dict(ctx.state["verified_niche"])
            niche["status"] = "READY_FOR_MONETIZATION"
            niche["mvp_score"] = mvp_eval["score"]
            niche["mvp"] = {
                "spec_path": bundle.get("spec_path", ""),
                "artifact_path": bundle.get("artifact_path", ""),
                "dashboard_path": bundle.get("dashboard_path", ""),
                "zip_path": bundle.get("zip_path", ""),
                "test_command": bundle.get("test_command", ""),
                "test_exit_code": 0,
            }
            promote_verified_entry(
                caller=HALL_ROOM_WRITER,
                entry=niche,
                json_path=hall_room_json,
                md_path=hall_room_md,
            )
            ctx.state["verified_niche"] = niche
            ctx.state["node_trace"].append(
                {
                    "node": "mvp_verifier",
                    "round": round_num,
                    "status": "PASS",
                    "mvp_score": mvp_eval["score"],
                }
            )
            return Event(
                output=ctx.state["mvp_verification"],
                actions=EventActions(route="PASS"),
            )

        if round_num < MAX_QUALITY_ROUNDS:
            ctx.state["mvp_round"] = round_num + 1
            ctx.state["node_trace"].append(
                {
                    "node": "mvp_verifier",
                    "round": round_num,
                    "status": "RETRY",
                    "mvp_score": mvp_eval["score"],
                    "fixes": mvp_eval["exact_fixes"],
                }
            )
            return Event(
                output=ctx.state["mvp_verification"],
                actions=EventActions(route="RETRY_MVP"),
            )

        ctx.state["escalation_reason"] = {
            "stage": "mvp_verifier",
            "round": round_num,
            "mvp_fixes": mvp_eval["exact_fixes"],
        }
        ctx.state["node_trace"].append(
            {
                "node": "mvp_verifier",
                "round": round_num,
                "status": "ESCALATE",
                "mvp_score": mvp_eval["score"],
            }
        )
        return Event(
            output=ctx.state["escalation_reason"],
            actions=EventActions(route="ESCALATE"),
        )

    def house_lead_finalize(ctx: Context, node_input: Any) -> Event:
        """House Lead synthesizes verified Hall Room entry, logs run, updates memory."""
        niche = ctx.state["verified_niche"]
        res_v = ctx.state["research_verification"]
        mvp_v = ctx.state["mvp_verification"]

        first_pass = (res_v["round"] == 0) and (mvp_v["round"] == 0)
        run_record = append_run_log(
            {
                "version": version_tag,
                "directive": ctx.state["directive"],
                "niche_id": niche["niche_id"],
                "status": "VERIFIED_COMPLETE",
                "first_pass": first_pass,
                "research_rounds": res_v["round"],
                "mvp_rounds": mvp_v["round"],
                "scores": {
                    "pain_point_scout": res_v["pain_point_scout"]["score"],
                    "market_roi_analyst": res_v["market_roi_analyst"]["score"],
                    "mvp_builder": mvp_v["mvp_builder"]["score"],
                },
                "initial_scores": dict(ctx.state.get("initial_scores", {})),
                "retries_by_agent": dict(ctx.state.get("retries_by_agent", {})),
                "verified_packages_delivered": 1,
                "model": model,
            },
            runs_path=runs_jsonl,
        )
        append_memory_lesson(
            f"[{version_tag}] Verified '{niche['niche_id']}' "
            f"(Scout={res_v['pain_point_scout']['score']}, "
            f"Analyst={res_v['market_roi_analyst']['score']}, "
            f"Builder={mvp_v['mvp_builder']['score']}, "
            f"retries={res_v['round'] + mvp_v['round']}).",
            memory_path=memory_md,
        )

        package = {
            "status": "VERIFIED_COMPLETE",
            "version": version_tag,
            "niche_id": niche["niche_id"],
            "title": niche["title"],
            "buyer_persona": niche["buyer_persona"],
            "recurring_pain": niche["recurring_pain"],
            "recommended_price_point": niche["recommended_price_point"],
            "fixed_stack_cost": niche["fixed_stack_cost"],
            "unit_economics_summary": niche["unit_economics_summary"],
            "top_distribution_risk": niche["top_distribution_risk"],
            "mvp": niche["mvp"],
            "scores": run_record["scores"],
            "research_rounds": res_v["round"],
            "mvp_rounds": mvp_v["round"],
            "node_trace": ctx.state["node_trace"],
            "hall_room_json": str(hall_room_json),
            "hall_room_md": str(hall_room_md),
        }
        ctx.state["final_package"] = package
        needs_gate = bool(ctx.state.get("external_release_requested")) and not bool(
            ctx.state.get("external_preauthorized")
        )
        route = "NEED_EXTERNAL_APPROVAL" if needs_gate else "LOCAL_DONE"
        return Event(output=package, actions=EventActions(route=route))

    def house_lead_escalate(ctx: Context, node_input: Any) -> dict[str, Any]:
        """House Lead reports Round-2 Verifier exhaustion without polluting Hall Room."""
        reason = ctx.state.get("escalation_reason", {})
        res_v = ctx.state.get("research_verification", {})
        mvp_v = ctx.state.get("mvp_verification", {})
        scores = {
            "pain_point_scout": res_v.get("pain_point_scout", {}).get("score", 0),
            "market_roi_analyst": res_v.get("market_roi_analyst", {}).get("score", 0),
            "mvp_builder": mvp_v.get("mvp_builder", {}).get("score", 0),
        }
        append_run_log(
            {
                "version": version_tag,
                "directive": ctx.state.get("directive", ""),
                "niche_id": None,
                "status": "ESCALATED_ROUND_2",
                "first_pass": False,
                "research_rounds": res_v.get("round", 0),
                "mvp_rounds": mvp_v.get("round", 0),
                "scores": scores,
                "verified_packages_delivered": 0,
                "escalation_reason": reason,
                "model": model,
            },
            runs_path=runs_jsonl,
        )
        return {
            "status": "ESCALATED_ROUND_2",
            "escalation_reason": reason,
            "scores": scores,
            "node_trace": ctx.state.get("node_trace", []),
        }

    def external_approval_gate(ctx: Context, node_input: Any):
        """Native ADK 2.x HITL pause before any unapproved external publish/push/spend."""
        pkg = ctx.state.get("final_package", {})
        yield RequestInput(
            message=(
                f"External release requested for verified package '{pkg.get('niche_id')}'. "
                "Reply 'APPROVE' to proceed with external release, or 'HOLD' to keep local only."
            ),
            payload={"niche_id": pkg.get("niche_id"), "scores": pkg.get("scores")},
        )

    def external_release_complete(ctx: Context, node_input: Any) -> dict[str, Any]:
        """Finalize after human response at ApprovalGate."""
        decision = str(node_input).strip().upper()
        pkg = dict(ctx.state.get("final_package", {}))
        pkg["external_release_decision"] = "APPROVED" if decision == "APPROVE" else "HELD_LOCAL"
        return pkg

    def local_delivery_complete(ctx: Context, node_input: Any) -> dict[str, Any]:
        """Zero-interruption completion for finalized local commands."""
        pkg = dict(ctx.state.get("final_package", {}))
        pkg["external_release_decision"] = "LOCAL_ONLY_AUTONOMOUS"
        return pkg

    return Workflow(
        name="neon_agent_house",
        description="5-agent Agent House graph on Google ADK 2.x with parallel discovery, JoinNode, max-2-round Verifier loops, and external HITL gate.",
        edges=[
            (START, house_lead_intake),
            # Parallel fan-out & JoinNode fan-in
            (house_lead_intake, pain_point_scout),
            (house_lead_intake, market_roi_analyst),
            (pain_point_scout, research_join),
            (market_roi_analyst, research_join),
            (research_join, research_verifier),
            # Research quality loop (max 2 rounds)
            (
                research_verifier,
                {
                    "PASS": mvp_builder,
                    "RETRY_RESEARCH": research_retry_fanout,
                    "ESCALATE": house_lead_escalate,
                },
            ),
            (research_retry_fanout, pain_point_scout),
            (research_retry_fanout, market_roi_analyst),
            # MVP quality loop (max 2 rounds)
            (mvp_builder, mvp_verifier),
            (
                mvp_verifier,
                {
                    "PASS": house_lead_finalize,
                    "RETRY_MVP": mvp_builder,
                    "ESCALATE": house_lead_escalate,
                },
            ),
            # Autonomous local finish vs external-release HITL pause
            (
                house_lead_finalize,
                {
                    "LOCAL_DONE": local_delivery_complete,
                    "NEED_EXTERNAL_APPROVAL": external_approval_gate,
                },
            ),
            (external_approval_gate, external_release_complete),
        ],
    )
