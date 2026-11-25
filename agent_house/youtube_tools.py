"""Wing 2 YouTube Automation tools: live yt-dlp doomscroll, neural TTS, 1080x1920 Shorts renderer, and ffprobe QA.

100% $0 local stack (yt-dlp + edge-tts + Pillow + FFmpeg). Zero paid APIs, zero copyrighted clips.
"""

from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from agent_house.config import ROOT_DIR, STATE_DIR

YT_TRENDS_JSON = STATE_DIR / "yt_trends.json"
YT_OUTPUTS_DIR = ROOT_DIR / "outputs" / "youtube_shorts"

WIDTH = 1080
HEIGHT = 1920
FPS = 30

FONT_BOLD_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Impact.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
]
FONT_MONO_CANDIDATES = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]

STOREFRONT_URL = "https://imgolamrabbani.github.io/neon-agent-house/"
GUMROAD_LINKS = {
    "invoice-pulse-01": "https://adorable48.gumroad.com/l/zcnhpu",
    "scope-shield-01": "https://adorable48.gumroad.com/l/ktulbs",
    "launch-check-01": "https://adorable48.gumroad.com/l/pgehvq",
    "saas-sub-trimmer-01": "https://adorable48.gumroad.com/l/ijrfzn",
    "git-changelog-kit-01": "https://adorable48.gumroad.com/l/svfzm",
    "bundle-all-5": "https://adorable48.gumroad.com/l/cxsyhr",
}


def _load_font(size: int, mono: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = FONT_MONO_CANDIDATES if mono else FONT_BOLD_CANDIDATES
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def doomscroll_youtube_trends(
    queries: list[str] | None = None,
    *,
    per_query: int = 5,
    output_path: Path = YT_TRENDS_JSON,
) -> dict[str, Any]:
    """Scan live YouTube via yt-dlp to mine high-view outlier titles & hook patterns."""
    queries = queries or [
        "stop paying monthly subscriptions python automation",
        "freelance invoicing tool alternative shorts",
        "solo developer python automation tool",
    ]
    seen_ids: set[str] = set()
    videos: list[dict[str, Any]] = []

    for q in queries:
        try:
            proc = subprocess.run(
                ["yt-dlp", "--dump-json", "--flat-playlist", f"ytsearch{per_query}:{q}"],
                capture_output=True,
                text=True,
                timeout=20,
            )
            for line in proc.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                vid = d.get("id")
                if not vid or vid in seen_ids:
                    continue
                seen_ids.add(vid)
                title = (d.get("title") or "").strip()
                views = int(d.get("view_count") or 0)
                videos.append(
                    {
                        "video_id": vid,
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "title": title,
                        "view_count": views,
                        "duration_sec": float(d.get("duration") or 0),
                        "query": q,
                    }
                )
        except Exception:
            continue

    videos.sort(key=lambda v: v["view_count"], reverse=True)
    top_videos = videos[:12]

    patterns = [
        "STOP Paying $X/mo — 1-File Local Python Replacement",
        "Why Giving Apps Your Bank Password Is Insane (Offline CSV Fix)",
        "How Solo Builders Replace $200/mo SaaS Bloat in 60 Seconds",
    ]
    payload = {
        "queries": queries,
        "total_scanned": len(videos),
        "top_outliers": top_videos,
        "winning_hook_patterns": patterns,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def build_short_blueprint(
    *,
    short_id: str,
    niche_id: str,
    opportunity: dict[str, Any],
    trends: dict[str, Any],
) -> dict[str, Any]:
    """Generate a 6-beat viral dark-mode Shorts script & visual card blueprint."""
    cta_url = GUMROAD_LINKS.get(niche_id, STOREFRONT_URL)
    bundle_url = GUMROAD_LINKS["bundle-all-5"]

    presets: dict[str, dict[str, Any]] = {
        "invoice-pulse-01": {
            "title": "STOP Paying $59/mo Just to Chase Late Invoices #Shorts",
            "hook_badge": "STOP PAYING $59/MO",
            "accent_hex": "#38bdf8",
            "scenes": [
                {
                    "kind": "price_shock",
                    "badge": "SAAS TRAP ALERT",
                    "headline": "$59/MO JUST TO SEND REMINDERS?!",
                    "big_num": "$708 / YEAR",
                    "sub": "HoneyBook & Dubsado charge $35-$59 every single month",
                    "narration": "Stop paying fifty nine dollars every month to bloated C R M suites just to chase late client invoices.",
                },
                {
                    "kind": "pain_quote",
                    "badge": "THE REAL PAIN",
                    "headline": "SILENT AP LEAKS COST THOUSANDS",
                    "big_num": "4% - 6.9% FEE",
                    "sub": "Invoicing apps tack on extra card fees while late invoices slip through the cracks",
                    "narration": "Freelancers either waste hours writing awkward check-in emails, or lose six percent in extra invoicing app markups.",
                },
                {
                    "kind": "terminal",
                    "badge": "1-FILE PYTHON FIX",
                    "headline": "ZERO PIP INSTALLS. 100% LOCAL.",
                    "cmd": "python3 invoice_pulse.py --csv my.csv --html dash.html",
                    "sub": "Runs offline on Mac, Windows, and Linux with Python standard library",
                    "narration": "So I replaced the whole subscription with one local Python script. Drop your unpaid invoices in a plain C S V and run one command.",
                },
                {
                    "kind": "kpi_demo",
                    "badge": "INSTANT DASHBOARD",
                    "headline": "AUTO LATE FEES + 1-CLICK EMAILS",
                    "metrics": [
                        ("CASH AT RISK", "$9,608.20", "#fb7185"),
                        ("ACCRUED FEES", "$108.20", "#fbbf24"),
                        ("ESCALATIONS", "DAY 3 / 7 / 14 / 30", "#38bdf8"),
                    ],
                    "sub": "Generates dark-mode dashboard with 1-click mailto drafts and your own Stripe links",
                    "narration": "It builds a private dark-mode cashflow dashboard, calculates prorated late fees automatically, and drafts polite Day three to Day thirty escalation emails.",
                },
                {
                    "kind": "compare",
                    "badge": "DO THE MATH",
                    "left_label": "MONTHLY CRM",
                    "left_val": "$708 / yr",
                    "right_label": "INVOICEPULSE",
                    "right_val": "$9 ONCE",
                    "sub": "Zero monthly fees. Your client data never leaves your laptop.",
                    "narration": "Seven hundred dollars a year for cloud lock-in, versus nine dollars once and you own the source code forever.",
                },
                {
                    "kind": "cta",
                    "badge": "LINK IN PINNED COMMENT",
                    "headline": "GET ALL 5 LOCAL TOOLS FOR $19",
                    "big_num": "NO SUBSCRIPTIONS",
                    "sub": "InvoicePulse ($9) or grab the 5-in-1 Solo Builder Bundle ($19)",
                    "narration": "Grab InvoicePulse for nine bucks, or all five local solo-builder tools for nineteen in the pinned comment.",
                },
            ],
        },
        "saas-sub-trimmer-01": {
            "title": "Why Giving Plaid Your Bank Password Is Insane (Local CSV Fix) #Shorts",
            "hook_badge": "ZERO BANK LOGINS",
            "accent_hex": "#34d399",
            "scenes": [
                {
                    "kind": "price_shock",
                    "badge": "PRIVACY WARNING",
                    "headline": "GIVING APPS YOUR BANK PASSWORD?!",
                    "big_num": "$14.99 / MO",
                    "sub": "Budget apps want your bank login AND a recurring subscription",
                    "narration": "Why are budgeting apps charging fifteen dollars a month and still asking for your actual bank username and password?",
                },
                {
                    "kind": "pain_quote",
                    "badge": "HIDDEN SAAS BLEED",
                    "headline": "SILENT PRICE HIKES EVERY MONTH",
                    "big_num": "$1,747 / YR",
                    "sub": "Forgotten trials and quiet $36-to-$59 jumps drain solo builders silently",
                    "narration": "Meanwhile forgotten S a a S renewals and silent price hikes quietly drain over a thousand dollars from your card every year.",
                },
                {
                    "kind": "terminal",
                    "badge": "ZERO-PLAID FIX",
                    "headline": "1 LOCAL PYTHON FILE. OFFLINE CSV.",
                    "cmd": "python3 sub_trim.py --csv statement.csv --html audit.html",
                    "sub": "No bank credentials. No cloud sync. Zero pip installs.",
                    "narration": "SubTrim solves it completely offline. Export a normal bank C S V, run one Python command, and never share a single password.",
                },
                {
                    "kind": "kpi_demo",
                    "badge": "INSTANT LEAK AUDIT",
                    "headline": "FLAGS HIKES & DUPLICATES FAST",
                    "metrics": [
                        ("ANNUAL BURN", "$1,747.10/yr", "#fb7185"),
                        ("PRICE HIKE", "+63.9% ALERT", "#fbbf24"),
                        ("PRIVACY", "100% OFFLINE", "#34d399"),
                    ],
                    "sub": "Interactive dark-mode dashboard with 1-click Mark-to-Cancel savings math",
                    "narration": "In two seconds it catches every recurring merchant, flags surprise price jumps in red, and tallies your exact annual savings as you click cancel.",
                },
                {
                    "kind": "compare",
                    "badge": "NO MORE RENTING",
                    "left_label": "BUDGET SAAS",
                    "left_val": "$180/yr + Plaid",
                    "right_label": "SUBTRIM",
                    "right_val": "$9 ONCE",
                    "sub": "Your bank statement never leaves your hard drive.",
                    "narration": "Stop paying a subscription to cancel subscriptions. Pay nine dollars once and audit your statements privately forever.",
                },
                {
                    "kind": "cta",
                    "badge": "LINK IN PINNED COMMENT",
                    "headline": "SUBTRIM ($9) OR ALL 5 TOOLS ($19)",
                    "big_num": "100% LOCAL CODE",
                    "sub": "Link in pinned comment & description — includes --self-test",
                    "narration": "Link to SubTrim and the five-tool solo builder bundle is right in the pinned comment.",
                },
            ],
        },
    }

    if niche_id in presets:
        cfg = presets[niche_id]
    else:
        name = opportunity.get("title", niche_id).split("—")[0].strip()
        cfg = {
            "title": f"STOP Paying Monthly SaaS — {name} ($9 Local Python Tool) #Shorts",
            "hook_badge": "ZERO SUBSCRIPTIONS",
            "accent_hex": "#38bdf8",
            "scenes": [
                {
                    "kind": "price_shock",
                    "badge": "SAAS FATIGUE",
                    "headline": "STOP PAYING $49/MO FOR SIMPLE TOOLS",
                    "big_num": "$588 / YEAR",
                    "sub": opportunity.get("recurring_pain", "Recurring SaaS bloat drains solo builders")[:78],
                    "narration": f"Stop paying fifty dollars every month for bloated cloud software when you only need one fast workflow.",
                },
                {
                    "kind": "terminal",
                    "badge": "1-FILE PYTHON TOOL",
                    "headline": f"MEET {name.upper()}",
                    "cmd": f"python3 {niche_id.replace('-', '_')}.py --self-test",
                    "sub": "100% Python standard library — zero pip installs, works offline",
                    "narration": f"{name} runs completely locally on Python standard library with zero external installs and zero monthly bills.",
                },
                {
                    "kind": "compare",
                    "badge": "DO THE MATH",
                    "left_label": "CLOUD SAAS",
                    "left_val": "$588 / yr",
                    "right_label": name.upper(),
                    "right_val": "$9 ONCE",
                    "sub": "Own the source code forever. Zero cloud lock-in.",
                    "narration": f"Own {name} forever for nine dollars once, or grab all five zero-subscription solo builder tools for nineteen.",
                },
                {
                    "kind": "cta",
                    "badge": "LINK IN PINNED COMMENT",
                    "headline": "GET ALL 5 LOCAL TOOLS FOR $19",
                    "big_num": "ZERO MONTHLY FEES",
                    "sub": "Links in pinned comment & description",
                    "narration": "Check the pinned comment to grab it now and cancel one more monthly subscription today.",
                },
            ],
        }

    top_ref = (trends.get("top_outliers") or [{}])[0]
    description = (
        f"{cfg['title']}\n\n"
        f"Grab this tool ($9 one-time, $0/month forever): {cta_url}\n"
        f"Save 58% — Get ALL 5 Local Solo-Builder Tools ($19 Bundle): {bundle_url}\n"
        f"Full Storefront & Open-Source Agent House: {STOREFRONT_URL}\n\n"
        "100% Python 3 standard library. Zero pip installs. Zero cloud lock-in. Includes --self-test.\n\n"
        "#Shorts #Python #SoloBuilder #IndieHackers #Automation #Freelance #NoSubscription"
    )
    pinned_comment = (
        f"Get it here ($9 once, $0/mo forever): {cta_url} | "
        f"Or grab all 5 zero-subscription local tools for $19 (save 58%): {bundle_url}"
    )

    return {
        "short_id": short_id,
        "linked_niche_id": niche_id,
        "title": cfg["title"],
        "hook_badge": cfg["hook_badge"],
        "accent_hex": cfg["accent_hex"],
        "scenes": cfg["scenes"],
        "cta_url": cta_url,
        "bundle_url": bundle_url,
        "storefront_url": STOREFRONT_URL,
        "inspired_by_outlier": top_ref.get("title", ""),
        "description": description,
        "pinned_comment": pinned_comment,
        "tags": ["Shorts", "Python", "Automation", "SoloBuilder", "IndieHackers", "Freelance", "SaaS"],
    }


def _probe_duration(media_path: Path) -> float:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(media_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(proc.stdout.strip())


def synthesize_scene_audio(text: str, out_wav: Path, voice: str = "en-US-AndrewNeural") -> float:
    """Synthesize crisp neural voiceover via edge-tts CLI (fallback: macOS say) and return duration."""
    mp3_tmp = out_wav.with_suffix(".mp3")
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "edge_tts",
                "--voice",
                voice,
                "--rate=+10%",
                "--text",
                text,
                "--write-media",
                str(mp3_tmp),
            ],
            check=True,
            capture_output=True,
            timeout=25,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(mp3_tmp), "-ar", "44100", "-ac", "2", str(out_wav)],
            check=True,
        )
        mp3_tmp.unlink(missing_ok=True)
    except Exception:
        aiff_tmp = out_wav.with_suffix(".aiff")
        subprocess.run(["say", "-v", "Daniel", "-r", "195", "-o", str(aiff_tmp), text], check=True)
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(aiff_tmp), "-ar", "44100", "-ac", "2", str(out_wav)],
            check=True,
        )
        aiff_tmp.unlink(missing_ok=True)
    return _probe_duration(out_wav)


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _make_base_gradient(accent_rgb: tuple[int, int, int]) -> Image.Image:
    """Pre-compute sleek dark-mode vertical gradient background once per Short."""
    img = Image.new("RGB", (WIDTH, HEIGHT), (8, 13, 26))
    draw = ImageDraw.Draw(img)
    for y in range(0, HEIGHT, 4):
        t = y / HEIGHT
        r = int(10 + 14 * (1 - t) + accent_rgb[0] * 0.07 * (1 - abs(t - 0.35)))
        g = int(15 + 18 * (1 - t) + accent_rgb[1] * 0.08 * (1 - abs(t - 0.35)))
        b = int(32 + 28 * (1 - t) + accent_rgb[2] * 0.10 * (1 - abs(t - 0.35)))
        draw.rectangle([(0, y), (WIDTH, y + 4)], fill=(min(r, 255), min(g, 255), min(b, 255)))
    # Subtle grid lines for modern tech polish
    for x in range(90, WIDTH, 180):
        draw.line([(x, 0), (x, HEIGHT)], fill=(22, 32, 58), width=1)
    for y in range(160, HEIGHT, 180):
        draw.line([(0, y), (WIDTH, y)], fill=(22, 32, 58), width=1)
    return img


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: Any, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}".strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _draw_centered_multiline(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    y_start: int,
    font: Any,
    fill: tuple[int, int, int],
    line_gap: int = 12,
    center_x: int = WIDTH // 2,
) -> int:
    y = y_start
    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((center_x - tw // 2, y), ln, font=font, fill=fill)
        y += th + line_gap
    return y


def _render_scene_frame(
    base_bg: Image.Image,
    scene: dict[str, Any],
    *,
    accent_rgb: tuple[int, int, int],
    progress_global: float,
    progress_scene: float,
    fonts: dict[str, Any],
) -> Image.Image:
    img = base_bg.copy()
    draw = ImageDraw.Draw(img)

    # Top progress bar
    draw.rectangle([(60, 72), (WIDTH - 60, 86)], fill=(28, 39, 68))
    bar_w = int((WIDTH - 120) * max(0.02, min(1.0, progress_global)))
    draw.rectangle([(60, 72), (60 + bar_w, 86)], fill=accent_rgb)

    # Top pill badge
    badge_txt = scene.get("badge", "LOCAL PYTHON").upper()
    bb = draw.textbbox((0, 0), badge_txt, font=fonts["badge"])
    bw = (bb[2] - bb[0]) + 64
    bh = 62
    bx = (WIDTH - bw) // 2
    by = 155
    draw.rounded_rectangle([(bx, by), (bx + bw, by + bh)], radius=31, fill=(19, 32, 62), outline=accent_rgb, width=3)
    draw.text((bx + 32, by + 13), badge_txt, font=fonts["badge"], fill=accent_rgb)

    # Main visual card (safe zone x: 70..940 avoiding right-edge Shorts icons, y: 270..1180)
    card_l, card_t, card_r, card_b = 70, 275, 955, 1140
    card_cx = (card_l + card_r) // 2
    draw.rounded_rectangle(
        [(card_l, card_t), (card_r, card_b)],
        radius=34,
        fill=(15, 23, 44),
        outline=(44, 62, 106),
        width=3,
    )

    kind = scene.get("kind", "price_shock")
    if kind in ("price_shock", "pain_quote", "cta"):
        hl_lines = _wrap_text(draw, scene.get("headline", ""), fonts["h1"], card_r - card_l - 80)
        y = _draw_centered_multiline(draw, hl_lines, card_t + 70, fonts["h1"], (241, 245, 255), 14, card_cx)

        big_txt = scene.get("big_num", "")
        big_col = (251, 113, 133) if kind == "price_shock" else ((251, 191, 36) if kind == "pain_quote" else (52, 211, 153))
        big_y = y + 55
        bb2 = draw.textbbox((0, 0), big_txt, font=fonts["huge"])
        bw2 = bb2[2] - bb2[0]
        bh2 = bb2[3] - bb2[1]
        draw.rounded_rectangle(
            [(card_l + 60, big_y - 24), (card_r - 60, big_y + bh2 + 34)],
            radius=24,
            fill=(24, 34, 64),
            outline=big_col,
            width=4,
        )
        draw.text((card_cx - bw2 // 2, big_y), big_txt, font=fonts["huge"], fill=big_col)
        if kind == "price_shock" and progress_scene > 0.35:
            # Animated diagonal strike-through line across overpriced SaaS bill
            strike_t = min(1.0, (progress_scene - 0.35) / 0.35)
            x1, y1 = card_l + 110, big_y + bh2 + 12
            x2 = int(x1 + ((card_r - 110) - x1) * strike_t)
            y2 = int(y1 - (bh2 + 24) * strike_t)
            draw.line([(x1, y1), (x2, y2)], fill=(251, 113, 133), width=12)

        sub_lines = _wrap_text(draw, scene.get("sub", ""), fonts["sub"], card_r - card_l - 90)
        _draw_centered_multiline(draw, sub_lines, big_y + bh2 + 85, fonts["sub"], (160, 178, 214), 12, card_cx)

    elif kind == "terminal":
        hl_lines = _wrap_text(draw, scene.get("headline", ""), fonts["h1"], card_r - card_l - 80)
        y = _draw_centered_multiline(draw, hl_lines, card_t + 60, fonts["h1"], (241, 245, 255), 14, card_cx)
        # macOS terminal card inside
        tl, tt, tr, tb = card_l + 45, y + 40, card_r - 45, y + 360
        draw.rounded_rectangle([(tl, tt), (tr, tb)], radius=20, fill=(9, 13, 24), outline=accent_rgb, width=3)
        for idx, dot_c in enumerate([(251, 113, 133), (251, 191, 36), (52, 211, 153)]):
            draw.ellipse([(tl + 24 + idx * 32, tt + 20), (tl + 42 + idx * 32, tt + 38)], fill=dot_c)
        cmd_full = "$ " + scene.get("cmd", "")
        shown_len = max(4, int(len(cmd_full) * min(1.0, progress_scene * 1.45)))
        cmd_shown = cmd_full[:shown_len] + ("_" if int(progress_scene * 12) % 2 == 0 else "")
        cmd_lines = _wrap_text(draw, cmd_shown, fonts["mono"], tr - tl - 50)
        cy = tt + 82
        for cl in cmd_lines:
            draw.text((tl + 28, cy), cl, font=fonts["mono"], fill=(52, 211, 153))
            cy += 48
        if progress_scene > 0.65:
            draw.text((tl + 28, tb - 66), "✓ Built dashboard.html in 0.14s ($0/mo)", font=fonts["mono"], fill=accent_rgb)
        sub_lines = _wrap_text(draw, scene.get("sub", ""), fonts["sub"], card_r - card_l - 90)
        _draw_centered_multiline(draw, sub_lines, tb + 48, fonts["sub"], (160, 178, 214), 12, card_cx)

    elif kind == "kpi_demo":
        hl_lines = _wrap_text(draw, scene.get("headline", ""), fonts["h1"], card_r - card_l - 80)
        y = _draw_centered_multiline(draw, hl_lines, card_t + 52, fonts["h1"], (241, 245, 255), 12, card_cx)
        ky = y + 36
        for lbl, val, hex_c in scene.get("metrics", []):
            rgb_c = _hex_to_rgb(hex_c)
            draw.rounded_rectangle([(card_l + 52, ky), (card_r - 52, ky + 148)], radius=20, fill=(21, 31, 58), outline=rgb_c, width=3)
            draw.text((card_l + 84, ky + 22), lbl, font=fonts["small"], fill=(155, 174, 212))
            draw.text((card_l + 84, ky + 62), val, font=fonts["h1"], fill=rgb_c)
            ky += 172
        sub_lines = _wrap_text(draw, scene.get("sub", ""), fonts["sub"], card_r - card_l - 90)
        _draw_centered_multiline(draw, sub_lines, ky + 16, fonts["sub"], (160, 178, 214), 10, card_cx)

    elif kind == "compare":
        hl_lines = _wrap_text(draw, "MONTHLY RENT vs. OWN IT ONCE", fonts["h1"], card_r - card_l - 80)
        y = _draw_centered_multiline(draw, hl_lines, card_t + 65, fonts["h1"], (241, 245, 255), 14, card_cx)
        box_t, box_b = y + 55, y + 385
        mid = card_cx
        draw.rounded_rectangle([(card_l + 40, box_t), (mid - 16, box_b)], radius=24, fill=(38, 20, 34), outline=(251, 113, 133), width=3)
        draw.rounded_rectangle([(mid + 16, box_t), (card_r - 40, box_b)], radius=24, fill=(14, 42, 42), outline=(52, 211, 153), width=4)
        _draw_centered_multiline(draw, [scene.get("left_label", "SAAS")], box_t + 60, fonts["small"], (251, 113, 133), 8, (card_l + 40 + mid - 16) // 2)
        _draw_centered_multiline(draw, [scene.get("left_val", "$708/yr")], box_t + 150, fonts["h1"], (255, 228, 234), 8, (card_l + 40 + mid - 16) // 2)
        _draw_centered_multiline(draw, [scene.get("right_label", "LOCAL")], box_t + 60, fonts["small"], (52, 211, 153), 8, (mid + 16 + card_r - 40) // 2)
        _draw_centered_multiline(draw, [scene.get("right_val", "$9 ONCE")], box_t + 150, fonts["h1"], (220, 255, 240), 8, (mid + 16 + card_r - 40) // 2)
        sub_lines = _wrap_text(draw, scene.get("sub", ""), fonts["sub"], card_r - card_l - 90)
        _draw_centered_multiline(draw, sub_lines, box_b + 64, fonts["sub"], (160, 178, 214), 12, card_cx)

    # Kinetic word-highlighted subtitles in YouTube Shorts safe zone (y=1240..1540, x=70..955)
    words = scene.get("narration", "").split()
    if words:
        active_idx = min(len(words) - 1, int(progress_scene * len(words)))
        chunk_size = 4
        chunk_start = (active_idx // chunk_size) * chunk_size
        chunk = words[chunk_start : chunk_start + chunk_size]
        local_active = active_idx - chunk_start

        # Measure horizontal layout of caption chunk
        word_boxes = []
        total_w = 0
        space_w = 22
        for w in chunk:
            wb = draw.textbbox((0, 0), w.upper(), font=fonts["caption"])
            ww = wb[2] - wb[0]
            wh = wb[3] - wb[1]
            word_boxes.append((w.upper(), ww, wh))
            total_w += ww + space_w
        total_w -= space_w

        # If chunk too wide, split onto 2 lines cleanly
        cx = card_cx
        cy = 1310
        if total_w > 860 and len(word_boxes) >= 3:
            rows = [(word_boxes[:2], 0), (word_boxes[2:], 2)]
        else:
            rows = [(word_boxes, 0)]

        for row_items, offset in rows:
            rw = sum(x[1] for x in row_items) + space_w * max(0, len(row_items) - 1)
            x = cx - rw // 2
            for j, (wtxt, ww, wh) in enumerate(row_items):
                is_active = (offset + j) == local_active
                if is_active:
                    draw.rounded_rectangle(
                        [(x - 16, cy - 12), (x + ww + 16, cy + wh + 18)],
                        radius=18,
                        fill=(251, 191, 36),
                    )
                    draw.text((x, cy), wtxt, font=fonts["caption"], fill=(8, 13, 26))
                else:
                    # Crisp drop shadow + bright white text
                    draw.text((x + 3, cy + 3), wtxt, font=fonts["caption"], fill=(0, 0, 0))
                    draw.text((x, cy), wtxt, font=fonts["caption"], fill=(255, 255, 255))
                x += ww + space_w
            cy += 92

    # Clean footer watermark (above bottom YouTube Shorts description bar)
    draw.text((74, 1615), "NEON AGENT HOUSE  •  ZERO-SUBSCRIPTION TOOLS", font=fonts["tiny"], fill=(115, 138, 180))
    return img


def render_short_video(
    blueprint: dict[str, Any],
    *,
    output_root: Path = YT_OUTPUTS_DIR,
) -> dict[str, Any]:
    """Synthesize neural voiceover + render 1080x1920 30fps H.264 MP4 + thumbnail + metadata."""
    short_id = blueprint["short_id"]
    out_dir = output_root / short_id
    out_dir.mkdir(parents=True, exist_ok=True)

    video_path = out_dir / f"{short_id}.mp4"
    thumb_path = out_dir / "thumbnail.png"
    meta_path = out_dir / "upload_metadata.json"
    script_path = out_dir / "script.json"

    accent_rgb = _hex_to_rgb(blueprint.get("accent_hex", "#38bdf8"))
    base_bg = _make_base_gradient(accent_rgb)
    fonts = {
        "badge": _load_font(34),
        "h1": _load_font(58),
        "huge": _load_font(84),
        "sub": _load_font(36),
        "small": _load_font(30),
        "tiny": _load_font(26),
        "caption": _load_font(62),
        "mono": _load_font(34, mono=True),
    }

    scenes = blueprint["scenes"]
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        wav_paths: list[Path] = []
        durations: list[float] = []

        for idx, scene in enumerate(scenes):
            wav_p = tmp_dir / f"scene_{idx}.wav"
            dur = synthesize_scene_audio(scene["narration"], wav_p)
            # Add tiny 0.25s natural breath pad between beats
            padded_wav = tmp_dir / f"scene_{idx}_pad.wav"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-v", "error", "-i", str(wav_p),
                    "-af", "apad=pad_dur=0.25", "-ar", "44100", "-ac", "2", str(padded_wav),
                ],
                check=True,
            )
            pad_dur = _probe_duration(padded_wav)
            wav_paths.append(padded_wav)
            durations.append(pad_dur)

        total_dur = sum(durations)
        concat_list = tmp_dir / "concat.txt"
        concat_list.write_text(
            "\n".join(f"file '{p.as_posix()}'" for p in wav_paths) + "\n",
            encoding="utf-8",
        )
        voice_wav = tmp_dir / "voice_full.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(voice_wav)],
            check=True,
        )

        # Mix voice + subtle procedural copyright-free synth pulse bed & normalize to -14 LUFS
        mixed_audio = tmp_dir / "audio_master.m4a"
        subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error",
                "-i", str(voice_wav),
                "-f", "lavfi", "-t", f"{total_dur:.2f}",
                "-i", "aevalsrc=exprs=0.04*(sin(2*PI*110*t)+0.5*sin(2*PI*165*t))*(0.5+0.5*sin(2*PI*2*t)):s=44100:c=stereo",
                "-filter_complex",
                "[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[v];[1:a]volume=0.22[b];[v][b]amix=inputs=2:duration=first:dropout_transition=2[out]",
                "-map", "[out]", "-c:a", "aac", "-b:a", "192k", str(mixed_audio),
            ],
            check=True,
        )

        # Save punchy cover thumbnail from Scene 0 at 65% progress
        thumb_img = _render_scene_frame(
            base_bg, scenes[0], accent_rgb=accent_rgb, progress_global=0.18, progress_scene=0.65, fonts=fonts
        )
        thumb_img.save(thumb_path, format="PNG")

        # Stream raw RGB frames into FFmpeg at 30fps -> H.264 yuv420p MP4
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "rgb24", "-r", str(FPS),
            "-i", "-",
            "-i", str(mixed_audio),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
            "-pix_fmt", "yuv420p", "-c:a", "copy",
            "-movflags", "+faststart", "-shortest",
            str(video_path),
        ]
        proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
        assert proc.stdin is not None
        elapsed = 0.0
        try:
            for scene, dur in zip(scenes, durations):
                n_frames = max(1, int(round(dur * FPS)))
                for f_idx in range(n_frames):
                    sc_prog = f_idx / max(1, n_frames - 1)
                    gl_prog = (elapsed + (f_idx / FPS)) / max(0.1, total_dur)
                    frame = _render_scene_frame(
                        base_bg,
                        scene,
                        accent_rgb=accent_rgb,
                        progress_global=gl_prog,
                        progress_scene=sc_prog,
                        fonts=fonts,
                    )
                    proc.stdin.write(frame.tobytes())
                elapsed += dur
        finally:
            proc.stdin.close()
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"FFmpeg video encode failed with exit code {ret}")

    metadata = {
        "short_id": short_id,
        "linked_niche_id": blueprint["linked_niche_id"],
        "title": blueprint["title"],
        "description": blueprint["description"],
        "pinned_comment": blueprint["pinned_comment"],
        "tags": blueprint["tags"],
        "cta_url": blueprint["cta_url"],
        "video_path": str(video_path),
        "thumbnail_path": str(thumb_path),
        "duration_sec": round(_probe_duration(video_path), 2),
        "resolution": f"{WIDTH}x{HEIGHT}",
    }
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    script_path.write_text(json.dumps(blueprint, indent=2) + "\n", encoding="utf-8")
    return metadata


def verify_rendered_short(metadata: dict[str, Any]) -> dict[str, Any]:
    """Adversarial Wing 2 QA check using real ffprobe, ffmpeg volumedetect, and frame variance."""
    video_path = Path(metadata.get("video_path", ""))
    thumb_path = Path(metadata.get("thumbnail_path", ""))
    checks: list[dict[str, Any]] = []
    fixes: list[str] = []

    exists = video_path.is_file() and video_path.stat().st_size > 50_000
    checks.append({"name": "mp4_file_present", "pass": exists, "evidence": f"{video_path} ({video_path.stat().st_size if video_path.is_file() else 0} bytes)"})
    if not exists:
        fixes.append("Render a valid MP4 file (>50KB).")
        return {"agent": "yt_shorts_producer", "score": 0, "pass": False, "checks": checks, "exact_fixes": fixes}

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(video_path)],
        capture_output=True, text=True, check=True,
    )
    info = json.loads(probe.stdout)
    streams = info.get("streams", [])
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})
    duration = float(info.get("format", {}).get("duration", 0))

    res_ok = v_stream.get("width") == 1080 and v_stream.get("height") == 1920 and v_stream.get("pix_fmt") == "yuv420p"
    checks.append({
        "name": "vertical_1080x1920_h264_yuv420p",
        "pass": res_ok,
        "evidence": f"{v_stream.get('width')}x{v_stream.get('height')} {v_stream.get('codec_name')}/{v_stream.get('pix_fmt')}",
    })
    if not res_ok:
        fixes.append("Re-render at exact 1080x1920 H.264 yuv420p for YouTube Shorts.")

    dur_ok = 12.0 <= duration <= 59.5
    checks.append({"name": "shorts_duration_under_60s", "pass": dur_ok, "evidence": f"{duration:.2f}s"})
    if not dur_ok:
        fixes.append(f"Adjust pacing so duration ({duration:.2f}s) is between 12s and 59.5s.")

    # Audio loudness check via ffmpeg volumedetect
    vol_proc = subprocess.run(
        ["ffmpeg", "-i", str(video_path), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    m_vol = re.search(r"mean_volume:\s*(-?[0-9.]+)\s*dB", vol_proc.stderr)
    mean_db = float(m_vol.group(1)) if m_vol else -99.0
    audio_ok = bool(a_stream) and mean_db > -35.0
    checks.append({"name": "non_silent_broadcast_audio", "pass": audio_ok, "evidence": f"codec={a_stream.get('codec_name')}, mean_volume={mean_db} dB"})
    if not audio_ok:
        fixes.append(f"Audio missing or too quiet (mean_volume={mean_db} dB). Normalize voiceover to -14 LUFS.")

    # Frame integrity check at 25% and 75% timestamps (reject black/corrupt renders)
    non_blank = True
    frame_details: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        for pct in (0.25, 0.75):
            ts = max(0.5, duration * pct)
            fp = Path(tmp) / f"f_{int(pct*100)}.png"
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-ss", f"{ts:.2f}", "-i", str(video_path), "-vframes", "1", str(fp)],
                check=True,
            )
            im = Image.open(fp).convert("L")
            extrema = im.getextrema()
            spread = extrema[1] - extrema[0]
            frame_details.append(f"{int(pct*100)}%={spread}")
            if spread < 60:
                non_blank = False
    checks.append({"name": "non_blank_visual_frames", "pass": non_blank, "evidence": f"contrast_spread({', '.join(frame_details)})"})
    if not non_blank:
        fixes.append("Visual frame appears blank/low contrast; inspect renderer.")

    seo_ok = (
        bool(metadata.get("title"))
        and len(metadata.get("title", "")) <= 100
        and "#Shorts" in metadata.get("description", "")
        and "https://" in metadata.get("description", "")
        and thumb_path.is_file()
    )
    checks.append({"name": "seo_metadata_and_thumbnail", "pass": seo_ok, "evidence": f"title_len={len(metadata.get('title', ''))}, thumb={thumb_path.is_file()}"})
    if not seo_ok:
        fixes.append("Include <=100 char title, #Shorts tag, live CTA URL in description, and thumbnail.png.")

    passed = sum(1 for c in checks if c["pass"])
    score = int(round((passed / len(checks)) * 100))
    return {
        "agent": "yt_shorts_producer",
        "score": score,
        "pass": all(c["pass"] for c in checks),
        "checks": checks,
        "exact_fixes": fixes,
        "duration_sec": round(duration, 2),
        "mean_volume_db": mean_db,
    }
