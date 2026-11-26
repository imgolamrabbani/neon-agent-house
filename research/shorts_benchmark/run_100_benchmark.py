#!/usr/bin/env python3
"""100-Video Empirical YouTube Shorts Benchmark (4 Categories x 25 Viral Shorts).

Discovers, downloads, extracts frames, measures cut velocity (CPM), shot length,
first-cut timing, pixel motion energy, audio loudness/silence ratio, builds visual
contact sheets, and transcribes top viral hooks with Apple Silicon mlx_whisper.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
VIDEOS_DIR = ROOT / "videos"
FRAMES_DIR = ROOT / "frames"
SHEETS_DIR = ROOT / "contact_sheets"
MANIFEST_PATH = ROOT / "manifest_100.json"
DATASET_PATH = ROOT / "dataset_100_videos.json"
SUMMARY_PATH = ROOT / "summary_stats.json"

CATEGORIES: dict[str, dict[str, Any]] = {
    "cat1_visual_explainer": {
        "label": "3D / Animated Visual Science & Mechanism Explainers",
        "channels": [
            "https://www.youtube.com/@zackdfilms/shorts",
            "https://www.youtube.com/@kurzgesagt/shorts",
            "https://www.youtube.com/@Veritasium/shorts",
            "https://www.youtube.com/@Vox/shorts",
            "https://www.youtube.com/@BranchEducation/shorts",
            "https://www.youtube.com/@CleoAbram/shorts",
        ],
        "queries": ["zack d films", "kurzgesagt shorts", "how it works 3d animation"],
    },
    "cat2_dark_history": {
        "label": "Fast-Cut Dark History & Unsolved Mystery Documentaries",
        "channels": [
            "https://www.youtube.com/@MrBallen/shorts",
            "https://www.youtube.com/@WeirdHistory/shorts",
            "https://www.youtube.com/@JohnnyHarris/shorts",
            "https://www.youtube.com/@RealLifeLore/shorts",
            "https://www.youtube.com/@TheInfographicsShow/shorts",
            "https://www.youtube.com/@SimpleHistory/shorts",
        ],
        "queries": ["mrballen shorts", "weird history shorts", "johnny harris shorts"],
    },
    "cat3_psychology_mind": {
        "label": "Dark Psychology & Human Behavior Kinetic Stories",
        "channels": [
            "https://www.youtube.com/@Psych2go/shorts",
            "https://www.youtube.com/@CharismaonCommand/shorts",
            "https://www.youtube.com/@BrainyDose/shorts",
            "https://www.youtube.com/@PracticalPsychology/shorts",
            "https://www.youtube.com/@ImprovementPill/shorts",
            "https://www.youtube.com/@MindsetMentor/shorts",
            "https://www.youtube.com/@ChaseHughesOfficial/shorts",
        ],
        "queries": ["dark psychology facts shorts", "psych2go shorts", "body language tricks shorts"],
    },
    "cat4_scale_comparison": {
        "label": "Visual Scale, Ranking & Animated Data Comparisons",
        "channels": [
            "https://www.youtube.com/@MetaBallStudios/shorts",
            "https://www.youtube.com/@ReigarwComparisons/shorts",
            "https://www.youtube.com/@WatchDataVerified/shorts",
            "https://www.youtube.com/@TheRankings/shorts",
            "https://www.youtube.com/@REDLINE_Comparisons/shorts",
            "https://www.youtube.com/@DataDuck/shorts",
            "https://www.youtube.com/@GlobalDataOfficial/shorts",
            "https://www.youtube.com/@VisualComparison/shorts",
        ],
        "queries": ["metaballstudios shorts", "size comparison 3d", "probability comparison", "depth of the ocean comparison"],
    },
}


def run_cmd(cmd: list[str], timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def discover_category(cat_key: str, target_pool: int = 55) -> list[dict[str, Any]]:
    cfg = CATEGORIES[cat_key]
    seen: dict[str, dict[str, Any]] = {}

    def ingest_stdout(stdout: str, source: str, assume_shorts: bool = False) -> None:
        for line in stdout.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                item = json.loads(line)
            except Exception:
                continue
            vid = item.get("id")
            if not vid or vid in seen:
                continue
            dur = item.get("duration")
            if dur is not None:
                try:
                    dur_f = float(dur)
                except Exception:
                    continue
                if not (8.0 <= dur_f <= 75.0):
                    continue
            elif assume_shorts:
                dur_f = 45.0
            else:
                continue
            views = int(item.get("view_count") or 0)
            url = f"https://www.youtube.com/shorts/{vid}"
            seen[vid] = {
                "id": vid,
                "category": cat_key,
                "title": item.get("title") or "",
                "channel": item.get("channel") or item.get("uploader") or source,
                "duration_sec": round(dur_f, 2),
                "view_count": views,
                "url": url,
                "source": source,
            }

    # 1. Harvest directly from verified mega-viral channel /shorts tabs (top 18 Shorts per channel)
    for ch_url in cfg.get("channels", []):
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--dump-json",
            "--no-warnings",
            "--playlist-items",
            "1:18",
            ch_url,
        ]
        try:
            proc = run_cmd(cmd, timeout=40)
            ingest_stdout(proc.stdout, ch_url, assume_shorts=True)
        except Exception:
            continue

    # 2. Fallback search if we have fewer than 40 candidates
    if len(seen) < 40:
        for q in cfg.get("queries", []):
            cmd = [
                "yt-dlp",
                "--flat-playlist",
                "--dump-json",
                "--no-warnings",
                f"ytsearch25:{q}",
            ]
            try:
                proc = run_cmd(cmd, timeout=45)
                ingest_stdout(proc.stdout, q, assume_shorts=False)
            except Exception:
                continue

    ranked = sorted(seen.values(), key=lambda x: x["view_count"], reverse=True)
    return ranked[:target_pool]


def phase_discover() -> dict[str, list[dict[str, Any]]]:
    print("=== PHASE 1: Discovering viral Shorts across 4 categories ===")
    pool: dict[str, list[dict[str, Any]]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(discover_category, cat): cat for cat in CATEGORIES}
        for fut in concurrent.futures.as_completed(futs):
            cat = futs[fut]
            items = fut.result()
            pool[cat] = items
            top_v = items[0]["view_count"] if items else 0
            print(f"  [{cat}] found {len(items)} Shorts candidates (top views: {top_v:,})")
    MANIFEST_PATH.write_text(json.dumps(pool, indent=2), encoding="utf-8")
    return pool


def download_one(item: dict[str, Any]) -> dict[str, Any] | None:
    cat_dir = VIDEOS_DIR / item["category"]
    cat_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = cat_dir / f"{item['id']}.mp4"
    if out_mp4.is_file() and out_mp4.stat().st_size > 20_000:
        item["video_path"] = str(out_mp4)
        return item
    cmd = [
        "yt-dlp",
        "--no-warnings",
        "--no-playlist",
        "-f",
        "best[height<=480][ext=mp4]/bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format",
        "mp4",
        "--socket-timeout",
        "15",
        "--retries",
        "1",
        "-o",
        str(out_mp4),
        item["url"],
    ]
    try:
        proc = run_cmd(cmd, timeout=45)
        if proc.returncode == 0 and out_mp4.is_file() and out_mp4.stat().st_size > 20_000:
            item["video_path"] = str(out_mp4)
            return item
    except Exception:
        pass
    out_mp4.unlink(missing_ok=True)
    return None


def phase_download(pool: dict[str, list[dict[str, Any]]], per_cat: int = 25) -> list[dict[str, Any]]:
    print(f"=== PHASE 2: Downloading {per_cat} Shorts per category (100 total) ===")
    selected: list[dict[str, Any]] = []
    for cat, candidates in pool.items():
        got: list[dict[str, Any]] = []
        # Process in parallel batches until we have 25 verified downloaded MP4s for this category
        idx = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            while len(got) < per_cat and idx < len(candidates):
                need = per_cat - len(got)
                batch = candidates[idx : idx + max(need + 4, 8)]
                idx += len(batch)
                futs = [ex.submit(download_one, dict(c)) for c in batch]
                for fut in concurrent.futures.as_completed(futs):
                    res = fut.result()
                    if res is not None and len(got) < per_cat:
                        got.append(res)
        got.sort(key=lambda x: x["view_count"], reverse=True)
        print(f"  [{cat}] downloaded {len(got)}/{per_cat} MP4s")
        selected.extend(got)
    print(f"  TOTAL DOWNLOADED: {len(selected)} videos")
    return selected


def analyze_one(item: dict[str, Any]) -> dict[str, Any]:
    vid = item["id"]
    cat = item["category"]
    mp4 = Path(item["video_path"])
    fdir = FRAMES_DIR / cat / vid
    fdir.mkdir(parents=True, exist_ok=True)

    # 1. Probe exact duration, dimensions, fps
    probe = run_cmd(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate:format=duration",
            "-of",
            "json",
            str(mp4),
        ],
        timeout=20,
    )
    width = height = 0
    fps = 30.0
    dur = float(item.get("duration_sec") or 30.0)
    try:
        pj = json.loads(probe.stdout)
        if pj.get("streams"):
            st = pj["streams"][0]
            width = int(st.get("width") or 0)
            height = int(st.get("height") or 0)
            rfr = str(st.get("r_frame_rate") or "30/1")
            if "/" in rfr:
                n, d = rfr.split("/", 1)
                fps = round(float(n) / max(1.0, float(d)), 2)
        if pj.get("format", {}).get("duration"):
            dur = round(float(pj["format"]["duration"]), 2)
    except Exception:
        pass

    # 2. Extract 5 timeline frames (hook 0.2s, 1.8s, 30%, 60%, 88%)
    sample_times = [
        ("t00_hook", min(0.25, max(0.0, dur * 0.02))),
        ("t01_beat2", min(1.8, dur * 0.15)),
        ("t02_mid1", dur * 0.35),
        ("t03_mid2", dur * 0.62),
        ("t04_end", max(0.5, dur * 0.88)),
    ]
    extracted_frames: list[str] = []
    brightness_vals: list[float] = []
    saturation_vals: list[float] = []
    center_contrast_vals: list[float] = []
    for name, ts in sample_times:
        out_jpg = fdir / f"{name}.jpg"
        if not out_jpg.is_file():
            run_cmd(
                [
                    "ffmpeg",
                    "-y",
                    "-v",
                    "error",
                    "-ss",
                    f"{ts:.2f}",
                    "-i",
                    str(mp4),
                    "-frames:v",
                    "1",
                    "-q:v",
                    "3",
                    str(out_jpg),
                ],
                timeout=15,
            )
        if out_jpg.is_file():
            extracted_frames.append(str(out_jpg))
            try:
                im = Image.open(out_jpg).convert("RGB").resize((180, 320))
                arr = np.asarray(im, dtype=np.float32)
                brightness_vals.append(float(arr.mean()))
                mx = arr.max(axis=2)
                mn = arr.min(axis=2)
                sat = np.where(mx > 0, (mx - mn) / (mx + 1e-5), 0.0)
                saturation_vals.append(float(sat.mean()))
                # Caption zone contrast (middle-to-lower third: y=45%..80%)
                cap_zone = arr[144:256, 18:162, :]
                center_contrast_vals.append(float(cap_zone.std()))
            except Exception:
                pass

    # 3. FFmpeg scene-change cut detection (gt(scene,0.22))
    sc_proc = run_cmd(
        [
            "ffmpeg",
            "-v",
            "info",
            "-i",
            str(mp4),
            "-vf",
            "select='gt(scene,0.22)',showinfo",
            "-f",
            "null",
            "-",
        ],
        timeout=35,
    )
    cut_times: list[float] = []
    for m in re.finditer(r"pts_time:([0-9.]+)", sc_proc.stderr):
        t = float(m.group(1))
        if not cut_times or (t - cut_times[-1]) >= 0.25:
            cut_times.append(round(t, 2))
    cut_count = len(cut_times)
    cpm = round((cut_count / max(1.0, dur)) * 60.0, 1)
    avg_shot_sec = round(dur / max(1, cut_count + 1), 2)
    first_cut_sec = round(cut_times[0], 2) if cut_times else round(dur, 2)

    # 4. Continuous Pixel Motion Energy (4 fps 90x160 grayscale stream -> mean abs diff)
    motion_mean = 0.0
    motion_p90 = 0.0
    static_ratio = 0.0
    try:
        m_proc = subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                str(mp4),
                "-vf",
                "fps=4,scale=90:160,format=gray",
                "-f",
                "rawvideo",
                "-",
            ],
            capture_output=True,
            timeout=25,
        )
        raw = m_proc.stdout
        frame_sz = 90 * 160
        n_frames = len(raw) // frame_sz
        if n_frames >= 3:
            frames_arr = np.frombuffer(raw[: n_frames * frame_sz], dtype=np.uint8).reshape((n_frames, frame_sz)).astype(np.float32)
            diffs = np.abs(frames_arr[1:] - frames_arr[:-1]).mean(axis=1)
            motion_mean = round(float(diffs.mean()), 2)
            motion_p90 = round(float(np.percentile(diffs, 90)), 2)
            static_ratio = round(float((diffs < 1.5).mean()), 3)
    except Exception:
        pass

    # 5. Audio loudness & silence ratio
    au_proc = run_cmd(
        [
            "ffmpeg",
            "-v",
            "info",
            "-i",
            str(mp4),
            "-af",
            "volumedetect,silencedetect=noise=-35dB:d=0.35",
            "-f",
            "null",
            "-",
        ],
        timeout=25,
    )
    mean_db = -20.0
    m_db = re.search(r"mean_volume:\s*(-?[0-9.]+)\s*dB", au_proc.stderr)
    if m_db:
        mean_db = float(m_db.group(1))
    sil_total = sum(float(m.group(1)) for m in re.finditer(r"silence_duration:\s*([0-9.]+)", au_proc.stderr))
    silence_ratio = round(min(1.0, sil_total / max(1.0, dur)), 3)

    return {
        **item,
        "width": width,
        "height": height,
        "fps": fps,
        "duration_sec": dur,
        "cut_count": cut_count,
        "cuts_per_minute": cpm,
        "avg_shot_sec": avg_shot_sec,
        "first_cut_sec": first_cut_sec,
        "cut_timestamps": cut_times[:25],
        "motion_energy_mean": motion_mean,
        "motion_energy_p90": motion_p90,
        "static_frame_ratio": static_ratio,
        "mean_volume_db": mean_db,
        "silence_ratio": silence_ratio,
        "brightness_mean": round(statistics.mean(brightness_vals), 1) if brightness_vals else 0.0,
        "saturation_mean": round(statistics.mean(saturation_vals), 3) if saturation_vals else 0.0,
        "caption_zone_contrast": round(statistics.mean(center_contrast_vals), 1) if center_contrast_vals else 0.0,
        "frames": extracted_frames,
    }


def build_contact_sheet(cat_key: str, records: list[dict[str, Any]]) -> Path:
    SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    top5 = sorted(records, key=lambda r: r["view_count"], reverse=True)[:5]
    cell_w, cell_h = 220, 390
    pad = 12
    header_h = 54
    cols = 5
    rows = len(top5)
    W = cols * cell_w + (cols + 1) * pad
    H = header_h + rows * (cell_h + 36) + pad
    sheet = Image.new("RGB", (W, H), (14, 18, 28))
    draw = ImageDraw.Draw(sheet)
    try:
        font_b = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 18)
        font_s = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 13)
    except Exception:
        font_b = font_s = ImageFont.load_default()

    draw.text((pad, 14), f"{cat_key.upper()} — TOP 5 VIRAL OUTLIERS (Hook 0.2s -> 1.8s -> 35% -> 62% -> 88%)", fill=(248, 250, 252), font=font_b)

    for r_idx, rec in enumerate(top5):
        y0 = header_h + r_idx * (cell_h + 36)
        label = (
            f"#{r_idx+1} | {rec['view_count']:,} views | {rec['duration_sec']}s | "
            f"{rec['cuts_per_minute']} CPM (avg shot {rec['avg_shot_sec']}s, 1st cut {rec['first_cut_sec']}s) | "
            f"motion={rec['motion_energy_mean']} | {rec['title'][:58]}"
        )
        draw.text((pad, y0), label, fill=(56, 189, 248), font=font_s)
        for c_idx, fpath in enumerate(rec.get("frames", [])[:cols]):
            x0 = pad + c_idx * (cell_w + pad)
            try:
                im = Image.open(fpath).convert("RGB").resize((cell_w, cell_h), Image.Resampling.LANCZOS)
                sheet.paste(im, (x0, y0 + 22))
            except Exception:
                pass
    out_path = SHEETS_DIR / f"{cat_key}_top5_contact_sheet.jpg"
    sheet.save(out_path, "JPEG", quality=88)
    return out_path


def transcribe_top_hooks(records: list[dict[str, Any]], top_k: int = 3) -> dict[str, list[dict[str, Any]]]:
    print("=== PHASE 4: Transcribing Top 3 Viral Hooks per Category via Apple Silicon mlx_whisper ===")
    import mlx_whisper  # type: ignore

    by_cat: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        by_cat.setdefault(rec["category"], []).append(rec)

    out: dict[str, list[dict[str, Any]]] = {}
    for cat, items in by_cat.items():
        top = sorted(items, key=lambda r: r["view_count"], reverse=True)[:top_k]
        cat_hooks: list[dict[str, Any]] = []
        for rec in top:
            try:
                res = mlx_whisper.transcribe(
                    rec["video_path"],
                    path_or_hf_repo="mlx-community/whisper-tiny-mlx",
                    word_timestamps=True,
                )
                text = (res.get("text") or "").strip()
                words = []
                for seg in res.get("segments", []):
                    for w in seg.get("words", []):
                        words.append((w.get("word", "").strip(), round(float(w.get("start", 0)), 2)))
                hook_3s = " ".join(w for w, st in words if st <= 3.5).strip()
                wpm = round((len(text.split()) / max(1.0, rec["duration_sec"])) * 60.0, 1)
                cat_hooks.append(
                    {
                        "id": rec["id"],
                        "title": rec["title"],
                        "view_count": rec["view_count"],
                        "duration_sec": rec["duration_sec"],
                        "wpm": wpm,
                        "hook_first_3_5s": hook_3s,
                        "full_transcript": text[:650],
                    }
                )
                print(f"  [{cat}] {rec['id']} ({rec['view_count']:,} views, {wpm} WPM): {hook_3s[:90]}")
            except Exception as exc:
                print(f"  [{cat}] {rec['id']} whisper skipped: {exc}")
        out[cat] = cat_hooks
    return out


def summarize(records: list[dict[str, Any]], hooks: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "total_videos_analyzed": len(records),
        "categories": {},
    }
    for cat in CATEGORIES:
        recs = [r for r in records if r["category"] == cat]
        if not recs:
            continue
        views = [r["view_count"] for r in recs]
        summary["categories"][cat] = {
            "label": CATEGORIES[cat]["label"],
            "count": len(recs),
            "median_views": int(statistics.median(views)),
            "max_views": max(views),
            "median_duration_sec": round(statistics.median([r["duration_sec"] for r in recs]), 2),
            "median_cuts_per_minute": round(statistics.median([r["cuts_per_minute"] for r in recs]), 1),
            "median_avg_shot_sec": round(statistics.median([r["avg_shot_sec"] for r in recs]), 2),
            "median_first_cut_sec": round(statistics.median([r["first_cut_sec"] for r in recs]), 2),
            "median_motion_energy": round(statistics.median([r["motion_energy_mean"] for r in recs]), 2),
            "median_static_ratio": round(statistics.median([r["static_frame_ratio"] for r in recs]), 3),
            "median_volume_db": round(statistics.median([r["mean_volume_db"] for r in recs]), 1),
            "median_silence_ratio": round(statistics.median([r["silence_ratio"] for r in recs]), 3),
            "median_brightness": round(statistics.median([r["brightness_mean"] for r in recs]), 1),
            "median_saturation": round(statistics.median([r["saturation_mean"] for r in recs]), 3),
            "top_hooks": hooks.get(cat, []),
        }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-cat", type=int, default=25)
    parser.add_argument("--skip-discover", action="store_true")
    args = parser.parse_args()

    t0 = time.time()
    if args.skip_discover and MANIFEST_PATH.is_file():
        pool = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    else:
        pool = phase_discover()

    downloaded = phase_download(pool, per_cat=args.per_cat)

    print(f"=== PHASE 3: Extracting frames & measuring motion/cuts on {len(downloaded)} videos ===")
    analyzed: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(analyze_one, item) for item in downloaded]
        for idx, fut in enumerate(concurrent.futures.as_completed(futs), 1):
            analyzed.append(fut.result())
            if idx % 20 == 0 or idx == len(downloaded):
                print(f"  analyzed {idx}/{len(downloaded)} videos ({time.time()-t0:.1f}s elapsed)")

    DATASET_PATH.write_text(json.dumps(analyzed, indent=2), encoding="utf-8")

    for cat in CATEGORIES:
        cat_recs = [r for r in analyzed if r["category"] == cat]
        if cat_recs:
            sheet = build_contact_sheet(cat, cat_recs)
            print(f"  contact sheet saved: {sheet}")

    hooks = transcribe_top_hooks(analyzed, top_k=3)
    summary = summarize(analyzed, hooks)
    print("=== BENCHMARK COMPLETE ===")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
