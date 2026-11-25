"""Higgsfield-Style AI Cinema Shorts Engine for Wing 2 ('The Deep Chronicle').

Takes 9:16 AI cinema keyframes (or video clips when Veo/Flow is connected),
applies smooth 30fps sub-pixel camera motion (dolly zoom-in, slow pull-back,
cinematic pan, thriller tremor shake), atmospheric vignette + film grain,
dramatic deep-voice neural narration (edge-tts en-US-ChristopherNeural),
Hans-Zimmer-style sub-bass drone + sonar pulse bed normalized to -14 LUFS,
and synced cinema-gold kinetic captions -> 1080x1920 H.264 YouTube Short.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from agent_house.config import ROOT_DIR
from agent_house.youtube_seo import YOUTUBE_CATEGORY_SCIENCE_TECH, score_youtube_seo
from agent_house.youtube_tools import FONT_BOLD_CANDIDATES, _probe_duration, verify_rendered_short

CINEMA_OUT_DIR = ROOT_DIR / "outputs" / "youtube_shorts"
ELEVENLABS_ENV_FILE = Path.home() / ".config" / "neon-agent-house" / "elevenlabs.env"
# Brian (deep, resonant American documentary narrator on ElevenLabs)
DEFAULT_ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "nPczCjzI2devNBz1zQrb")
DEFAULT_ELEVENLABS_MODEL = os.environ.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
WIDTH = 1080
HEIGHT = 1920
FPS = 30


def _font(size: int) -> Any:
    for p in FONT_BOLD_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def _get_elevenlabs_api_key() -> str | None:
    """Read ElevenLabs API key strictly from env var or private ~/.config file (never git)."""
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if key:
        return key
    if ELEVENLABS_ENV_FILE.is_file():
        for line in ELEVENLABS_ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("ELEVENLABS_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _synthesize_elevenlabs(text: str, out_mp3: Path, api_key: str) -> None:
    """Call ElevenLabs eleven_multilingual_v2 for human Netflix-documentary narration."""
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_ELEVENLABS_VOICE_ID)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128"
    payload = json.dumps(
        {
            "text": text,
            "model_id": DEFAULT_ELEVENLABS_MODEL,
            "voice_settings": {
                "stability": 0.42,
                "similarity_boost": 0.80,
                "style": 0.35,
                "use_speaker_boost": True,
            },
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        out_mp3.write_bytes(resp.read())


def _synthesize_dramatic_voice(
    text: str,
    out_wav: Path,
    voice: str = "en-US-BrianMultilingualNeural",
) -> tuple[float, str]:
    """3-Tier Broadcast Voice Engine:
    1) ElevenLabs eleven_multilingual_v2 (when valid key is configured)
    2) en-US-BrianMultilingualNeural (zero artificial pitch shift, warm studio mic EQ)
    3) macOS say fallback (offline)
    Returns (duration_sec, engine_used).
    """
    mp3_tmp = out_wav.with_suffix(".mp3")
    engine_used = "unknown"

    el_key = _get_elevenlabs_api_key()
    if el_key:
        try:
            _synthesize_elevenlabs(text, mp3_tmp, el_key)
            engine_used = "elevenlabs"
        except Exception:
            mp3_tmp.unlink(missing_ok=True)

    if engine_used == "unknown":
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "edge_tts",
                    "--voice",
                    voice,
                    "--rate=+0%",
                    "--text",
                    text,
                    "--write-media",
                    str(mp3_tmp),
                ],
                check=True,
                capture_output=True,
                timeout=25,
            )
            engine_used = f"edge_tts:{voice}"
        except Exception:
            mp3_tmp.unlink(missing_ok=True)

    if mp3_tmp.is_file() and mp3_tmp.stat().st_size > 1000:
        # Warm studio condenser vocal EQ: gentle chest boost (180Hz) + de-harsh (3.2kHz) + smooth compression
        vocal_eq = "highpass=f=75,equalizer=f=180:t=q:w=1.2:g=3.0,equalizer=f=3200:t=q:w=1.5:g=-1.8,acompressor=threshold=-18dB:ratio=2.8:attack=10:release=120"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(mp3_tmp), "-af", vocal_eq, "-ar", "44100", "-ac", "2", str(out_wav)],
            check=True,
        )
        mp3_tmp.unlink(missing_ok=True)
    else:
        aiff_tmp = out_wav.with_suffix(".aiff")
        subprocess.run(["say", "-v", "Daniel", "-r", "175", "-o", str(aiff_tmp), text], check=True)
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(aiff_tmp), "-ar", "44100", "-ac", "2", str(out_wav)],
            check=True,
        )
        aiff_tmp.unlink(missing_ok=True)
        engine_used = "macos_say"

    return _probe_duration(out_wav), engine_used


def _prepare_plate(image_path: Path) -> Image.Image:
    """Load & cover-fit image to oversized 1296x2304 canvas for buttery smooth zoom/pan."""
    target_w, target_h = int(WIDTH * 1.2), int(HEIGHT * 1.2)
    im = Image.open(image_path).convert("RGB")
    src_ratio = im.width / im.height
    dst_ratio = target_w / target_h
    if src_ratio > dst_ratio:
        new_h = target_h
        new_w = int(round(new_h * src_ratio))
    else:
        new_w = target_w
        new_h = int(round(new_w / src_ratio))
    im = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    im = im.crop((left, top, left + target_w, top + target_h))
    # Subtle contrast boost for dramatic IMAX cinema look
    im = ImageEnhance.Contrast(im).enhance(1.08)
    return im


def _make_vignette_mask() -> Image.Image:
    """Create a dark cinema vignette + bottom gradient scrim so subtitles pop sharply."""
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # Top subtle cinema shadow
    for y in range(0, 260, 4):
        alpha = int(140 * (1 - y / 260))
        draw.rectangle([(0, y), (WIDTH, y + 4)], fill=(4, 8, 16, alpha))
    # Bottom rich gradient scrim for crystal-clear captions
    for y in range(1100, HEIGHT, 4):
        t = (y - 1100) / (HEIGHT - 1100)
        alpha = int(215 * (t ** 1.25))
        draw.rectangle([(0, y), (WIDTH, y + 4)], fill=(4, 8, 16, alpha))
    return overlay


def _camera_crop(plate: Image.Image, motion: str, t: float) -> Image.Image:
    """Smooth eased 30fps virtual camera move (dolly-in, pull-out, pan, thriller tremor)."""
    pw, ph = plate.size
    # Smooth cubic ease-in-out
    e = t * t * (3 - 2 * t)
    shake_x = shake_y = 0.0

    if motion == "dolly_in":
        scale = 1.0 + 0.14 * e
        cx, cy = pw * 0.5, ph * (0.50 - 0.02 * e)
    elif motion == "pull_out":
        scale = 1.15 - 0.13 * e
        cx, cy = pw * 0.5, ph * (0.48 + 0.02 * e)
    elif motion == "pan_right":
        scale = 1.10
        cx, cy = pw * (0.46 + 0.08 * e), ph * 0.5
    elif motion == "pan_up":
        scale = 1.12
        cx, cy = pw * 0.5, ph * (0.55 - 0.10 * e)
    elif motion == "tremor_zoom":
        scale = 1.04 + 0.13 * e
        shake_x = math.sin(t * 42.0) * 7.0 * (1 - 0.3 * t)
        shake_y = math.cos(t * 37.0) * 6.0 * (1 - 0.3 * t)
        cx, cy = pw * 0.5 + shake_x, ph * 0.5 + shake_y
    else:
        scale = 1.02 + 0.12 * e
        cx, cy = pw * 0.5, ph * 0.5

    crop_w = pw / scale
    crop_h = ph / scale
    left = max(0.0, min(pw - crop_w, cx - crop_w / 2))
    top = max(0.0, min(ph - crop_h, cy - crop_h / 2))
    cropped = plate.crop((left, top, left + crop_w, top + crop_h))
    return cropped.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)


def _draw_cinema_overlays(
    frame: Image.Image,
    vignette: Image.Image,
    *,
    scene_label: str,
    narration: str,
    progress_scene: float,
    progress_global: float,
    fonts: dict[str, Any],
    fade_alpha: float = 0.0,
) -> Image.Image:
    rgba = frame.convert("RGBA")
    rgba.alpha_composite(vignette)
    draw = ImageDraw.Draw(rgba)

    # Ultra-thin gold cinematic progress line at top
    draw.rectangle([(60, 72), (WIDTH - 60, 80)], fill=(255, 255, 255, 45))
    bar_w = int((WIDTH - 120) * max(0.01, min(1.0, progress_global)))
    draw.rectangle([(60, 72), (60 + bar_w, 80)], fill=(245, 197, 66, 235))

    # Subtle documentary chapter tag top-left
    if scene_label:
        lbl = scene_label.upper()
        bb = draw.textbbox((0, 0), lbl, font=fonts["tag"])
        tw = bb[2] - bb[0]
        draw.rounded_rectangle([(68, 120), (68 + tw + 44, 174)], radius=27, fill=(8, 14, 26, 175), outline=(245, 197, 66, 200), width=2)
        draw.text((90, 132), lbl, font=fonts["tag"], fill=(245, 197, 66, 255))

    # Viral cinema word-highlighted captions in Shorts safe zone (x centered at 510, y=1320..1520)
    words = narration.split()
    if words:
        active_idx = min(len(words) - 1, int(progress_scene * len(words)))
        chunk_size = 3
        chunk_start = (active_idx // chunk_size) * chunk_size
        chunk = words[chunk_start : chunk_start + chunk_size]
        local_active = active_idx - chunk_start

        space_w = 24
        word_boxes = []
        for w in chunk:
            wt = w.upper()
            wb = draw.textbbox((0, 0), wt, font=fonts["caption"])
            word_boxes.append((wt, wb[2] - wb[0], wb[3] - wb[1]))

        total_w = sum(x[1] for x in word_boxes) + space_w * max(0, len(word_boxes) - 1)
        cx = 515
        cy = 1350
        rows = [(word_boxes[:2], 0), (word_boxes[2:], 2)] if (total_w > 840 and len(word_boxes) == 3) else [(word_boxes, 0)]

        for row_items, offset in rows:
            rw = sum(x[1] for x in row_items) + space_w * max(0, len(row_items) - 1)
            x = cx - rw // 2
            for j, (wtxt, ww, wh) in enumerate(row_items):
                is_active = (offset + j) == local_active
                if is_active:
                    draw.rounded_rectangle([(x - 16, cy - 12), (x + ww + 16, cy + wh + 18)], radius=18, fill=(245, 197, 66, 255))
                    draw.text((x, cy), wtxt, font=fonts["caption"], fill=(8, 12, 20, 255))
                else:
                    # Heavy cinematic stroke shadow for max legibility over bright imagery
                    for ox, oy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 5)]:
                        draw.text((x + ox, cy + oy), wtxt, font=fonts["caption"], fill=(0, 0, 0, 220))
                    draw.text((x, cy), wtxt, font=fonts["caption"], fill=(255, 255, 255, 255))
                x += ww + space_w
            cy += 98

    # Subtle brand signature above YouTube bottom chrome
    draw.text((70, 1615), "THE DEEP CHRONICLE", font=fonts["brand"], fill=(245, 197, 66, 175))

    rgb = rgba.convert("RGB")
    if fade_alpha > 0.01:
        black = Image.new("RGB", (WIDTH, HEIGHT), (4, 6, 12))
        rgb = Image.blend(rgb, black, min(1.0, fade_alpha))
    return rgb


def build_cinema_seo(
    *,
    title: str,
    hook_summary: str,
    chapters: list[tuple[str, str]],
    tags: list[str],
    hashtags: list[str],
    pinned_question: str,
) -> dict[str, Any]:
    chapters_str = "\n".join(f"{ts} {lbl}" for ts, lbl in chapters)
    tags_clean = list(dict.fromkeys(tags))[:20]
    hashtags_clean = hashtags[:5]
    description = (
        f"{hook_summary}\n"
        "Subscribe to The Deep Chronicle for daily untold history, abyssal ocean mysteries, and forgotten worlds: "
        "https://www.youtube.com/@TheDeepChronicle\n\n"
        f"Chapters:\n{chapters_str}\n\n"
        "Crafted with original AI cinema visuals & atmospheric sound design.\n"
        f"{' '.join(hashtags_clean)}"
    )
    pinned_comment = (
        f"{pinned_question} "
        "Subscribe for tomorrow's deep-dive: https://www.youtube.com/@TheDeepChronicle"
    )
    seo = {
        "title": title,
        "description": description,
        "pinned_comment": pinned_comment,
        "tags": tags_clean,
        "hashtags": hashtags_clean,
        "category_id": "27",  # Education / Documentary
        "default_language": "en",
        "default_audio_language": "en",
        "made_for_kids": False,
    }
    seo["seo_audit"] = score_youtube_seo(seo)
    return seo


def render_cinema_short(
    *,
    short_id: str,
    scenes: list[dict[str, Any]],
    seo: dict[str, Any],
    output_root: Path = CINEMA_OUT_DIR,
) -> dict[str, Any]:
    """Render a full Higgsfield-style moving AI cinema 1080x1920 YouTube Short."""
    out_dir = output_root / short_id
    out_dir.mkdir(parents=True, exist_ok=True)
    video_path = out_dir / f"{short_id}.mp4"
    thumb_path = out_dir / "thumbnail.png"
    meta_path = out_dir / "upload_metadata.json"

    fonts = {
        "tag": _font(30),
        "caption": _font(68),
        "brand": _font(26),
    }
    vignette = _make_vignette_mask()
    plates = [_prepare_plate(Path(s["image_path"])) for s in scenes]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        wavs: list[Path] = []
        durations: list[float] = []

        voice_engines: list[str] = []
        for idx, sc in enumerate(scenes):
            raw_w = tmp_dir / f"v_{idx}.wav"
            _, eng = _synthesize_dramatic_voice(sc["narration"], raw_w)
            voice_engines.append(eng)
            pad_w = tmp_dir / f"vp_{idx}.wav"
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", str(raw_w), "-af", "apad=pad_dur=0.22", "-ar", "44100", "-ac", "2", str(pad_w)],
                check=True,
            )
            wavs.append(pad_w)
            durations.append(_probe_duration(pad_w))

        total_dur = sum(durations)
        concat_txt = tmp_dir / "concat.txt"
        concat_txt.write_text("\n".join(f"file '{p.as_posix()}'" for p in wavs) + "\n", encoding="utf-8")
        voice_full = tmp_dir / "voice_full.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(voice_full)],
            check=True,
        )

        # Deep cinema Hans-Zimmer-style sub-bass drone + subtle underwater sonar pulse (-14 LUFS master)
        mixed_audio = tmp_dir / "cinema_master.m4a"
        drone_expr = (
            "0.07*sin(2*PI*55*t)"
            "+0.04*sin(2*PI*82.4*t)*(0.6+0.4*sin(2*PI*0.25*t))"
            "+0.03*sin(2*PI*660*t)*exp(-6*mod(t\\,4))"
        )
        subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error",
                "-i", str(voice_full),
                "-f", "lavfi", "-t", f"{total_dur:.2f}",
                "-i", f"aevalsrc=exprs={drone_expr}:s=44100:c=stereo",
                "-filter_complex",
                "[0:a]loudnorm=I=-14:TP=-1.5:LRA=9[v];[1:a]lowpass=f=1200,volume=0.32[b];[v][b]amix=inputs=2:duration=first:dropout_transition=2[out]",
                "-map", "[out]", "-c:a", "aac", "-b:a", "192k", str(mixed_audio),
            ],
            check=True,
        )

        # Save dramatic high-CTR cover thumbnail from Scene 4 (encounter) or Scene 0
        thumb_idx = min(3, len(plates) - 1)
        thumb_frame = _camera_crop(plates[thumb_idx], scenes[thumb_idx].get("motion", "dolly_in"), 0.55)
        thumb_final = _draw_cinema_overlays(
            thumb_frame,
            vignette,
            scene_label=scenes[0].get("label", "11,000 METERS DEEP"),
            narration="POWER LOST AT 11,000M",
            progress_scene=0.5,
            progress_global=0.5,
            fonts=fonts,
        )
        thumb_final.save(thumb_path, format="PNG")

        ffmpeg_cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "rgb24", "-r", str(FPS),
            "-i", "-",
            "-i", str(mixed_audio),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-c:a", "copy",
            "-movflags", "+faststart", "-shortest",
            str(video_path),
        ]
        proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
        assert proc.stdin is not None
        elapsed = 0.0
        try:
            for sc, plate, dur in zip(scenes, plates, durations):
                n_frames = max(1, int(round(dur * FPS)))
                fade_frames = 7
                for f_idx in range(n_frames):
                    t_sc = f_idx / max(1, n_frames - 1)
                    t_gl = (elapsed + f_idx / FPS) / max(0.1, total_dur)
                    fade = 0.0
                    if f_idx < fade_frames:
                        fade = (1.0 - f_idx / fade_frames) * 0.65
                    elif f_idx > n_frames - fade_frames:
                        fade = ((f_idx - (n_frames - fade_frames)) / fade_frames) * 0.65
                    cam_img = _camera_crop(plate, sc.get("motion", "dolly_in"), t_sc)
                    final_frame = _draw_cinema_overlays(
                        cam_img,
                        vignette,
                        scene_label=sc.get("label", ""),
                        narration=sc["narration"],
                        progress_scene=t_sc,
                        progress_global=t_gl,
                        fonts=fonts,
                        fade_alpha=fade,
                    )
                    proc.stdin.write(final_frame.tobytes())
                elapsed += dur
        finally:
            proc.stdin.close()
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"FFmpeg cinema encode failed (exit={ret})")

    metadata = {
        "short_id": short_id,
        "linked_niche_id": "the-deep-chronicle",
        **seo,
        "cta_url": "https://www.youtube.com/@TheDeepChronicle",
        "video_path": str(video_path),
        "thumbnail_path": str(thumb_path),
        "duration_sec": round(_probe_duration(video_path), 2),
        "resolution": f"{WIDTH}x{HEIGHT}",
        "voice_engine": voice_engines[0] if voice_engines else "unknown",
    }
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    qa = verify_rendered_short(metadata)
    return {"metadata": metadata, "qa": qa}
