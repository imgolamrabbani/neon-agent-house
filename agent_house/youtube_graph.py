"""Wing 2: YouTube Automation House Graph on Google ADK 2.15.0.

Architecture (Zero deprecated SequentialAgent / ParallelAgent / LoopAgent):
  START -> yt_lead_intake
    -> (parallel fan-out) yt_trend_scout (live yt-dlp doomscroll) & yt_product_hook_mapper (Hall Room products)
    -> yt_research_join (JoinNode)
    -> yt_shorts_producer (neural TTS + 1080x1920 MP4 + kinetic captions + thumbnail)
    -> yt_video_verifier (ffprobe + volumedetect + frame variance QA, max 2 retry rounds -> Hall Room)
    -> yt_channel_manager (SEO upload package, runs.jsonl telemetry, memory.md lesson)
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from google.adk import Context, Event, Workflow
from google.adk.events import EventActions
from google.adk.runners import InMemoryRunner
from google.adk.workflow import JoinNode, START
from google.genai import types

from agent_house.config import DEFAULT_MODEL_ID, HALL_ROOM_JSON, HALL_ROOM_MD, MAX_QUALITY_ROUNDS, MEMORY_MD, RUNS_JSONL
from agent_house.hall_room import append_memory_lesson, append_run_log, load_hall_room, promote_verified_short
from agent_house.youtube_tools import (
    YT_OUTPUTS_DIR,
    YT_TRENDS_JSON,
    build_short_blueprint,
    doomscroll_youtube_trends,
    render_short_video,
    verify_rendered_short,
)
from agent_house.youtube_uploader import is_youtube_api_configured, upload_short_via_api


def build_youtube_wing_workflow(
    *,
    hall_room_json: Path = HALL_ROOM_JSON,
    hall_room_md: Path = HALL_ROOM_MD,
    memory_md: Path = MEMORY_MD,
    runs_jsonl: Path = RUNS_JSONL,
    trends_json: Path = YT_TRENDS_JSON,
    output_root: Path = YT_OUTPUTS_DIR,
    skip_live_doomscroll: bool = False,
    auto_upload: bool = True,
    privacy_status: str = "public",
) -> Workflow:
    """Construct the Wing 2 YouTube Automation ADK 2.x Workflow graph."""

    def yt_lead_intake(ctx: Context, node_input: Any) -> dict[str, Any]:
        raw = node_input
        if hasattr(raw, "parts") and raw.parts:
            raw = "\n".join(getattr(p, "text", "") for p in raw.parts if getattr(p, "text", None))
        payload = json.loads(raw) if isinstance(raw, str) and raw.strip().startswith("{") else {"niche_id": str(raw)}
        ctx.state["target_niche_id"] = payload.get("niche_id") or "invoice-pulse-01"
        ctx.state["short_id"] = payload.get("short_id") or f"yt-{ctx.state['target_niche_id']}"
        ctx.state["qa_round"] = 0
        ctx.state["qa_fixes"] = []
        ctx.state["node_trace"] = [{"node": "yt_lead_intake", "short_id": ctx.state["short_id"]}]
        return payload

    def yt_trend_scout(ctx: Context, node_input: Any) -> dict[str, Any]:
        """Parallel Branch A: Doomscroll live YouTube trends via yt-dlp."""
        if skip_live_doomscroll and trends_json.exists():
            trends = json.loads(trends_json.read_text(encoding="utf-8"))
        elif skip_live_doomscroll:
            trends = {
                "total_scanned": 3,
                "top_outliers": [{"title": "STOP Paying $200/m — Free Local Alternative", "view_count": 426830}],
                "winning_hook_patterns": ["STOP Paying $X/mo — 1-File Local Replacement"],
            }
        else:
            trends = doomscroll_youtube_trends(output_path=trends_json)
        ctx.state["yt_trends"] = trends
        ctx.state["node_trace"].append({"node": "yt_trend_scout", "outliers": len(trends.get("top_outliers", []))})
        return trends

    def yt_product_hook_mapper(ctx: Context, node_input: Any) -> dict[str, Any]:
        """Parallel Branch B: Pull verified Wing 1 opportunity from shared Hall Room."""
        board = load_hall_room(hall_room_json)
        target_id = ctx.state["target_niche_id"]
        match = next(
            (o for o in board.get("verified_opportunities", []) if o.get("niche_id") == target_id),
            {"niche_id": target_id, "title": target_id, "recurring_pain": "Monthly SaaS subscriptions"},
        )
        ctx.state["linked_opportunity"] = match
        ctx.state["node_trace"].append({"node": "yt_product_hook_mapper", "niche_id": target_id})
        return match

    yt_research_join = JoinNode(name="yt_research_join")

    def yt_shorts_producer(ctx: Context, node_input: Any) -> dict[str, Any]:
        """Script, voice, and render a real 1080x1920 MP4 Short locally."""
        blueprint = build_short_blueprint(
            short_id=ctx.state["short_id"],
            niche_id=ctx.state["target_niche_id"],
            opportunity=ctx.state["linked_opportunity"],
            trends=ctx.state["yt_trends"],
        )
        metadata = render_short_video(blueprint, output_root=output_root)
        ctx.state["short_metadata"] = metadata
        ctx.state["node_trace"].append(
            {
                "node": "yt_shorts_producer",
                "round": ctx.state["qa_round"],
                "video_path": metadata["video_path"],
                "duration_sec": metadata["duration_sec"],
            }
        )
        return metadata

    def yt_video_verifier(ctx: Context, node_input: Any) -> Event:
        """Adversarial QA Checker (max 2 retry rounds) & exclusive Hall Room Shorts scribe."""
        round_num = int(ctx.state.get("qa_round", 0))
        metadata = ctx.state["short_metadata"]
        qa = verify_rendered_short(metadata)
        ctx.state["yt_qa"] = qa

        if qa["pass"]:
            record = {
                "short_id": metadata["short_id"],
                "title": metadata["title"],
                "status": "QA_PASSED_READY_FOR_UPLOAD",
                "qa_score": qa["score"],
                "resolution": metadata["resolution"],
                "duration_sec": qa["duration_sec"],
                "mean_volume_db": qa["mean_volume_db"],
                "linked_niche_id": metadata["linked_niche_id"],
                "cta_url": metadata["cta_url"],
                "video_path": metadata["video_path"],
                "thumbnail_path": metadata["thumbnail_path"],
                "youtube_url": "ready_for_upload",
            }
            promote_verified_short(
                caller="yt-video-verifier",
                entry=record,
                json_path=hall_room_json,
                md_path=hall_room_md,
            )
            ctx.state["verified_short"] = record
            ctx.state["node_trace"].append({"node": "yt_video_verifier", "round": round_num, "status": "PASS", "score": qa["score"]})
            return Event(output=qa, actions=EventActions(route="PASS"))

        if round_num < MAX_QUALITY_ROUNDS:
            ctx.state["qa_round"] = round_num + 1
            ctx.state["qa_fixes"] = qa["exact_fixes"]
            ctx.state["node_trace"].append({"node": "yt_video_verifier", "round": round_num, "status": "RETRY", "score": qa["score"]})
            return Event(output=qa, actions=EventActions(route="RETRY_PRODUCER"))

        ctx.state["node_trace"].append({"node": "yt_video_verifier", "round": round_num, "status": "ESCALATE", "score": qa["score"]})
        return Event(output=qa, actions=EventActions(route="ESCALATE"))

    def yt_channel_manager(ctx: Context, node_input: Any) -> dict[str, Any]:
        """Auto-upload via YouTube Data API v3 when OAuth token is present (always allowed), log telemetry."""
        sh = dict(ctx.state["verified_short"])
        qa = ctx.state["yt_qa"]
        upload_result: dict[str, Any] = {"status": "SKIPPED_NO_UPLOAD_FLAG"}

        if auto_upload:
            cfg_status = is_youtube_api_configured()
            if cfg_status["ready_for_unattended_upload"]:
                upload_result = upload_short_via_api(
                    ctx.state["short_metadata"],
                    privacy_status=privacy_status,
                    post_cta_comment=True,
                    hall_room_json=hall_room_json,
                    hall_room_md=hall_room_md,
                )
                sh["status"] = "PUBLISHED_YOUTUBE"
                sh["youtube_url"] = upload_result["youtube_url"]
            else:
                upload_result = {
                    "status": "AWAITING_ONE_TIME_YT_AUTH",
                    "hint": "Place Google OAuth Desktop client_secret.json at ~/.config/neon-agent-house/client_secret.json and run `./run_house.sh yt-auth` once.",
                }

        append_run_log(
            {
                "version": "v5.1-youtube-api",
                "wing": "youtube_shorts",
                "directive": f"Produce & upload YouTube Short for {sh['linked_niche_id']}",
                "niche_id": sh["short_id"],
                "status": sh["status"],
                "youtube_url": sh.get("youtube_url", ""),
                "first_pass": ctx.state["qa_round"] == 0,
                "research_rounds": 0,
                "mvp_rounds": ctx.state["qa_round"],
                "scores": {"yt_shorts_producer": qa["score"]},
                "initial_scores": {"yt_shorts_producer": qa["score"]},
                "retries_by_agent": {"yt_shorts_producer": ctx.state["qa_round"]},
                "verified_packages_delivered": 1,
                "model": DEFAULT_MODEL_ID,
            },
            runs_path=runs_jsonl,
        )
        append_memory_lesson(
            f"[v5.1-yt] Verified '{sh['short_id']}' ({sh['duration_sec']}s, QA={qa['score']}/100, upload={upload_result['status']}).",
            memory_path=memory_md,
        )
        return {
            "status": sh["status"],
            "short": sh,
            "qa": qa,
            "upload": upload_result,
            "node_trace": ctx.state["node_trace"],
        }

    def yt_escalate(ctx: Context, node_input: Any) -> dict[str, Any]:
        return {
            "status": "ESCALATED_ROUND_2",
            "qa": ctx.state.get("yt_qa", {}),
            "node_trace": ctx.state.get("node_trace", []),
        }

    return Workflow(
        name="neon_youtube_wing",
        description="Wing 2 YouTube Automation House on Google ADK 2.x (doomscroll -> parallel product hook -> render 1080x1920 MP4 -> ffprobe QA -> upload package).",
        edges=[
            (START, yt_lead_intake),
            (yt_lead_intake, yt_trend_scout),
            (yt_lead_intake, yt_product_hook_mapper),
            (yt_trend_scout, yt_research_join),
            (yt_product_hook_mapper, yt_research_join),
            (yt_research_join, yt_shorts_producer),
            (yt_shorts_producer, yt_video_verifier),
            (
                yt_video_verifier,
                {
                    "PASS": yt_channel_manager,
                    "RETRY_PRODUCER": yt_shorts_producer,
                    "ESCALATE": yt_escalate,
                },
            ),
        ],
    )


async def run_youtube_wing_once(
    *,
    niche_id: str = "invoice-pulse-01",
    short_id: str | None = None,
    skip_live_doomscroll: bool = False,
    auto_upload: bool = True,
    privacy_status: str = "public",
) -> list[dict[str, Any]]:
    wf = build_youtube_wing_workflow(
        skip_live_doomscroll=skip_live_doomscroll,
        auto_upload=auto_upload,
        privacy_status=privacy_status,
    )
    runner = InMemoryRunner(node=wf, app_name="neon_youtube_wing")
    session = await runner.session_service.create_session(app_name="neon_youtube_wing", user_id="solo_builder")
    payload = json.dumps({"niche_id": niche_id, "short_id": short_id or f"yt-{niche_id}"})
    msg = types.Content(role="user", parts=[types.Part.from_text(text=payload)])
    out: list[dict[str, Any]] = []
    async for ev in runner.run_async(user_id="solo_builder", session_id=session.id, new_message=msg):
        out.append({"author": ev.author, "route": ev.actions.route, "output": ev.output})
    await runner.close()
    return out


def run_youtube_wing_sync(**kwargs: Any) -> list[dict[str, Any]]:
    return asyncio.run(run_youtube_wing_once(**kwargs))
