"""One-command CLI runner for Neon Agent House (Google ADK 2.x)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from google.adk.runners import InMemoryRunner
from google.genai import types

from agent_house.config import DEFAULT_MODEL_ID, get_gemini_api_key
from agent_house.continuous import run_continuous_sync
from agent_house.graph import build_agent_house_workflow
from agent_house.weekly import run_weekly_review
from agent_house.youtube_graph import run_youtube_wing_sync
from agent_house.youtube_uploader import (
    authorize_youtube_oauth,
    is_youtube_api_configured,
    upload_short_via_api,
)


def _make_replay_providers(replay_data: dict[str, Any]):
    """Build deterministic replay providers from a researched artifact bundle.

    Supports multi-round sequences (list of rounds) to exercise the real ADK 2.x
    max-2-round Verifier quality loop end-to-end.
    """
    scout_rounds = replay_data["pain_point_scout_rounds"]
    analyst_rounds = replay_data["market_roi_analyst_rounds"]
    builder_rounds = replay_data["mvp_builder_rounds"]

    def scout_provider(_brief: dict[str, Any], round_num: int, _fixes: list[str]) -> dict[str, Any]:
        idx = min(round_num, len(scout_rounds) - 1)
        return scout_rounds[idx]

    def analyst_provider(_brief: dict[str, Any], round_num: int, _fixes: list[str]) -> dict[str, Any]:
        idx = min(round_num, len(analyst_rounds) - 1)
        return analyst_rounds[idx]

    def builder_provider(_niche: dict[str, Any], round_num: int, _fixes: list[str]) -> dict[str, Any]:
        idx = min(round_num, len(builder_rounds) - 1)
        return builder_rounds[idx]

    return scout_provider, analyst_provider, builder_provider


async def run_workflow_once(
    *,
    directive: str,
    model: str = DEFAULT_MODEL_ID,
    replay_file: Path | None = None,
    version_tag: str = "v1",
    external_release: bool = False,
    external_preauthorized: bool = False,
    check_live_urls: bool = True,
    execute_mvp_test: bool = True,
) -> list[dict[str, Any]]:
    """Run the Google ADK 2.x Workflow and return every emitted node event."""
    scout_provider = analyst_provider = builder_provider = None
    if replay_file is not None:
        replay_data = json.loads(replay_file.read_text(encoding="utf-8"))
        scout_provider, analyst_provider, builder_provider = _make_replay_providers(replay_data)

    workflow = build_agent_house_workflow(
        model=model,
        scout_provider=scout_provider,
        analyst_provider=analyst_provider,
        builder_provider=builder_provider,
        check_live_urls=check_live_urls,
        execute_mvp_test=execute_mvp_test,
        version_tag=version_tag,
    )

    runner = InMemoryRunner(node=workflow, app_name="neon_agent_house")
    session = await runner.session_service.create_session(
        app_name="neon_agent_house",
        user_id="solo_builder",
    )

    payload = json.dumps(
        {
            "directive": directive,
            "final_command": True,
            "external_release_requested": external_release,
            "external_preauthorized": external_preauthorized,
        }
    )
    user_msg = types.Content(role="user", parts=[types.Part.from_text(text=payload)])

    events_out: list[dict[str, Any]] = []
    async for ev in runner.run_async(
        user_id="solo_builder",
        session_id=session.id,
        new_message=user_msg,
    ):
        node_name = getattr(ev, "author", "") or getattr(getattr(ev, "node_info", None), "name", "")
        route = getattr(getattr(ev, "actions", None), "route", None)
        entry: dict[str, Any] = {
            "author": node_name,
            "route": route,
            "output": getattr(ev, "output", None),
        }
        events_out.append(entry)
    await runner.close()
    return events_out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent-house",
        description="Run Neon Agent House (Google ADK 2.x graph workflow + weekly improvement loop).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run a directive through the full ADK 2.x graph.")
    run_p.add_argument("directive", help="Broad micro-niche monetization directive.")
    run_p.add_argument("--model", default=DEFAULT_MODEL_ID, help=f"Gemini model ID (default: {DEFAULT_MODEL_ID}).")
    run_p.add_argument("--replay-file", type=Path, default=None, help="Optional JSON artifact bundle to execute through the ADK 2.x graph without calling the Gemini API.")
    run_p.add_argument("--version-tag", default="v1", help="Version tag logged in runs.jsonl (v1, v2, v3).")
    run_p.add_argument("--external-release", action="store_true", help="Request external release (triggers HITL ApprovalGate unless --preauthorized).")
    run_p.add_argument("--preauthorized", action="store_true", help="Pre-authorize external release inside final command.")
    run_p.add_argument("--skip-live-urls", action="store_true", help="Skip live HTTP URL checks (offline tests only).")

    sub.add_parser("weekly", help="Run the weekly self-improvement audit and draft ONE prompt proposal.")

    cont_p = sub.add_parser("continuous", help="Run Agent House v4 continuous multi-niche portfolio loop (never idles on 1 product).")
    cont_p.add_argument("--max-new", type=int, default=3, help="Max new queued niches to execute in this cycle.")
    cont_p.add_argument("--model", default=DEFAULT_MODEL_ID, help=f"Gemini model ID (default: {DEFAULT_MODEL_ID}).")
    cont_p.add_argument("--skip-live-urls", action="store_true", help="Skip live HTTP URL checks (offline tests only).")

    yt_p = sub.add_parser("youtube", help="Run Wing 2 YouTube Automation House (doomscroll -> render 1080x1920 Short -> 100/100 SEO & QA -> auto-upload).")
    yt_p.add_argument("--niche-id", default="invoice-pulse-01", help="Hall Room niche_id to turn into a YouTube Short.")
    yt_p.add_argument("--short-id", default=None, help="Optional output short_id.")
    yt_p.add_argument("--skip-live-doomscroll", action="store_true", help="Reuse cached state/yt_trends.json instead of querying YouTube.")
    yt_p.add_argument("--no-auto-upload", action="store_true", help="Render & QA only without uploading via YouTube API.")
    yt_p.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"], help="YouTube visibility (default: public).")

    sub.add_parser("yt-auth", help="One-time OAuth sign-in to authorize hands-free YouTube Data API v3 uploads (zero future prompts).")

    up_p = sub.add_parser("yt-upload", help="Upload an already-rendered Short directory directly via YouTube Data API v3.")
    up_p.add_argument("short_dir", type=Path, help="Path to Short folder (e.g., outputs/youtube_shorts/yt-short-01).")
    up_p.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    up_p.add_argument("--publish-at", default=None, help="Optional RFC3339 schedule timestamp (e.g., 2026-11-26T14:00:00Z).")

    args = parser.parse_args(argv)

    if args.command == "weekly":
        result = run_weekly_review()
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "continuous":
        result = run_continuous_sync(
            model=args.model,
            max_new_runs=args.max_new,
            check_live_urls=not args.skip_live_urls,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "yt-auth":
        token_path = authorize_youtube_oauth()
        print(json.dumps({"status": "AUTHORIZED", "token_path": str(token_path), "ready": True}, indent=2))
        return 0

    if args.command == "yt-upload":
        status = is_youtube_api_configured()
        if not status["ready_for_unattended_upload"]:
            print(json.dumps({"status": "AWAITING_ONE_TIME_YT_AUTH", **status}, indent=2))
            return 2
        res = upload_short_via_api(
            args.short_dir,
            privacy_status=args.privacy,
            publish_at_iso=args.publish_at,
            post_cta_comment=True,
        )
        print(json.dumps(res, indent=2))
        return 0

    if args.command == "youtube":
        events = run_youtube_wing_sync(
            niche_id=args.niche_id,
            short_id=args.short_id,
            skip_live_doomscroll=args.skip_live_doomscroll,
            auto_upload=not args.no_auto_upload,
            privacy_status=args.privacy,
        )
        print(json.dumps(events, indent=2, default=str))
        return 0

    if args.replay_file is None and not get_gemini_api_key():
        print(
            "ERROR: GEMINI_API_KEY is not set in your environment.\n"
            "Fix: export GEMINI_API_KEY='your-key' for live gemini-4-neon runs, "
            "or pass --replay-file <bundle.json> to run researched artifacts through the ADK 2.x graph.",
            file=sys.stderr,
        )
        return 2

    events = asyncio.run(
        run_workflow_once(
            directive=args.directive,
            model=args.model,
            replay_file=args.replay_file,
            version_tag=args.version_tag,
            external_release=args.external_release,
            external_preauthorized=args.preauthorized,
            check_live_urls=not args.skip_live_urls,
        )
    )
    print(json.dumps(events, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
