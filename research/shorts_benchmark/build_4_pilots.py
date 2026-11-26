#!/usr/bin/env python3
"""Next-Gen Viral Shorts 4-Category Pilot Factory.

Renders 4 completely distinct, non-slideshow 1080x1920 30fps pilot Shorts calibrated
to our 100-video empirical benchmark:
  1) outputs/pilot_showdown/01_visual_explainer_pilot.mp4  (Animated Mechanism / Anatomy)
  2) outputs/pilot_showdown/02_dark_history_map_pilot.mp4  (Satellite Map + Declassified Fast-Cut)
  3) outputs/pilot_showdown/03_dark_psychology_pilot.mp4   (34+ CPM Fast-Cut Dark Psychology)
  4) outputs/pilot_showdown/04_scale_comparison_pilot.mp4  (WatchData Continuous Rarity Conveyor)

Run under `/Users/mdgolamrabbani/mcp-servers/mlx-audio/.venv/bin/python`.
"""
from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from agent_house.kokoro_word_sync import synthesize_with_word_timestamps
from agent_house.sfx_engine import build_viral_master_audio

OUT_DIR = ROOT / "outputs" / "pilot_showdown"
RENDERER_MJS = ROOT / "agent_house" / "chrome_frame_renderer.mjs"


def clean_words(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge split apostrophe/punctuation sub-tokens from Whisper (e.g., "don'" + "t" -> "don't")."""
    merged: list[dict[str, Any]] = []
    for w in words:
        txt = str(w.get("word", "")).strip()
        if not txt:
            continue
        if merged and (txt.startswith("'") or txt.startswith("’") or txt in {".", ",", "?", "!", ":", ";", "%"} or merged[-1]["word"].endswith("'") or merged[-1]["word"].endswith("’")):
            merged[-1]["word"] = merged[-1]["word"] + txt
            merged[-1]["end"] = w["end"]
        else:
            merged.append({"word": txt, "start": w["start"], "end": w["end"]})
    return merged


def img_to_data_uri(path: str | Path) -> str:
    p = Path(path)
    if not p.is_file():
        return ""
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode("ascii")


def render_html_video(html_content: str, audio_m4a: Path, out_mp4: Path, duration: float, work_dir: Path) -> None:
    html_file = work_dir / f"{out_mp4.stem}.html"
    html_file.write_text(html_content, encoding="utf-8")
    subprocess.run(
        [
            "node",
            str(RENDERER_MJS),
            "--html", str(html_file),
            "--audio", str(audio_m4a),
            "--out", str(out_mp4),
            "--duration", f"{duration:.2f}",
            "--fps", "30",
            "--width", "1080",
            "--height", "1920",
        ],
        check=True,
    )


def verify_pilot_metrics(mp4: Path) -> dict[str, Any]:
    import re
    import numpy as np

    probe = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height:format=duration",
            "-of", "json", str(mp4),
        ],
        text=True,
    )
    pj = json.loads(probe)
    dur = round(float(pj["format"]["duration"]), 2)
    w = int(pj["streams"][0]["width"])
    h = int(pj["streams"][0]["height"])

    # Measure motion energy & static frame ratio (exact same metric as our 100-video benchmark!)
    m_proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(mp4), "-vf", "fps=4,scale=90:160,format=gray", "-f", "rawvideo", "-"],
        capture_output=True,
        check=True,
    )
    raw = m_proc.stdout
    nf = len(raw) // (90 * 160)
    arr = np.frombuffer(raw[: nf * 90 * 160], dtype=np.uint8).reshape((nf, 90 * 160)).astype(np.float32)
    diffs = np.abs(arr[1:] - arr[:-1]).mean(axis=1)

    au = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(mp4), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    mdb = re.search(r"mean_volume:\s*(-?[0-9.]+)\s*dB", au.stderr)
    mean_db = float(mdb.group(1)) if mdb else -16.0
    return {
        "file": str(mp4),
        "size_mb": round(mp4.stat().st_size / (1024 * 1024), 2),
        "resolution": f"{w}x{h}",
        "duration_sec": dur,
        "motion_energy": round(float(diffs.mean()), 2),
        "static_frame_ratio": round(float((diffs < 1.0).mean()), 3),
        "mean_volume_db": mean_db,
    }


# ---------------------------------------------------------------------------
# PILOT 1: CATEGORY 1 — VISUAL SCIENCE / MECHANISM ANIMATED EXPLAINER
# ---------------------------------------------------------------------------
def build_pilot_1_explainer(work_dir: Path) -> dict[str, Any]:
    print("\n=== BUILDING PILOT 1: Category 1 — Animated Visual Science Explainer ===")
    script = (
        "The second you hold your breath, your lungs don't run out of oxygen. "
        "Instead, your blood fills up with carbon dioxide. "
        "After thirty seconds, your heart rate actually drops by twenty percent to save energy. "
        "By sixty seconds, tiny CO2 sensors inside your brainstem fire a massive panic alarm, "
        "forcing your diaphragm to violently spasm for air. "
        "And here is the crazy part: your blood still has seventy percent of its oxygen left. "
        "That choking panic isn't suffocation — it's your brain lying to you to make you breathe early."
    )
    wav = work_dir / "p1_voice.wav"
    words_json = work_dir / "p1_words.json"
    voice_info = synthesize_with_word_timestamps(
        script_text=script,
        out_wav=wav,
        out_words_json=words_json,
        voice="am_michael",
        speed=1.15,
    )
    dur = voice_info["duration_sec"]
    words = clean_words(voice_info["words"])

    events = [
        {"t": 0.05, "kind": "boom", "gain": 0.9},
        {"t": dur * 0.16, "kind": "whoosh", "gain": 0.85},
        {"t": dur * 0.30, "kind": "pop", "gain": 0.9},
        {"t": dur * 0.46, "kind": "riser", "gain": 0.9},
        {"t": dur * 0.48, "kind": "boom", "gain": 1.0},
        {"t": dur * 0.65, "kind": "whoosh", "gain": 0.9},
        {"t": dur * 0.78, "kind": "pop", "gain": 0.95},
        {"t": dur * 0.88, "kind": "boom", "gain": 0.95},
    ]
    master = work_dir / "p1_master.m4a"
    build_viral_master_audio(voice_wav=wav, out_m4a=master, events=events, mood="explainer")

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#070d19;font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","Helvetica Neue",sans-serif;color:#fff;}}
#stage{{position:relative;width:1080px;height:1920px;overflow:hidden;background:radial-gradient(circle at 50% 42%,#112645 0%,#060b16 70%);}}
#grid{{position:absolute;inset:0;background-image:linear-gradient(rgba(56,189,248,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(56,189,248,.07) 1px,transparent 1px);background-size:64px 64px;}}
#hud{{position:absolute;top:115px;left:56px;right:56px;display:flex;gap:18px;z-index:20;}}
.gauge{{flex:1;background:rgba(12,22,42,.82);border:2px solid rgba(56,189,248,.32);border-radius:22px;padding:18px 20px;backdrop-filter:blur(10px);}}
.g-label{{font-size:20px;font-weight:700;letter-spacing:1.6px;color:#94a3b8;text-transform:uppercase;}}
.g-val{{font-size:46px;font-weight:900;margin-top:4px;font-variant-numeric:tabular-nums;}}
.g-bar{{height:10px;border-radius:6px;background:rgba(255,255,255,.12);margin-top:10px;overflow:hidden;}}
.g-fill{{height:100%;border-radius:6px;}}
#phase-pill{{position:absolute;top:295px;left:50%;transform:translateX(-50%);padding:12px 30px;border-radius:999px;font-size:26px;font-weight:800;letter-spacing:2px;background:rgba(15,23,42,.88);border:2px solid #38bdf8;color:#7dd3fc;z-index:20;white-space:nowrap;}}
#cam{{position:absolute;inset:0;transform-origin:540px 880px;will-change:transform;}}
#anatomy{{position:absolute;top:310px;left:60px;width:960px;height:1120px;}}
#alarm-overlay{{position:absolute;inset:0;background:radial-gradient(circle at 50% 38%,rgba(239,68,68,.38),transparent 62%);opacity:0;pointer-events:none;z-index:15;}}
#callout{{position:absolute;right:68px;top:520px;width:310px;background:rgba(10,18,34,.92);border:2px solid #38bdf8;border-radius:20px;padding:18px 20px;z-index:25;opacity:0;}}
#callout-title{{font-size:22px;font-weight:900;color:#38bdf8;letter-spacing:1px;}}
#callout-body{{font-size:22px;font-weight:600;color:#e2e8f0;margin-top:6px;line-height:1.25;}}
#caption-wrap{{position:absolute;left:60px;right:60px;bottom:340px;text-align:center;z-index:40;min-height:150px;display:flex;align-items:center;justify-content:center;}}
.cap-line{{display:inline-flex;flex-wrap:wrap;justify-content:center;gap:14px 26px;}}
.w{{font-size:62px;font-weight:900;color:#ffffff;text-shadow:0 6px 24px rgba(0,0,0,.95),0 0 6px rgba(0,0,0,1),-3px -3px 0 #000,3px -3px 0 #000,-3px 3px 0 #000,3px 3px 0 #000;transition:none;display:inline-block;padding:0 4px;}}
.w.active{{color:#38bdf8;transform:scale(1.09);}}
.w.danger{{color:#f87171;transform:scale(1.10);}}
#prog{{position:absolute;top:0;left:0;height:10px;background:linear-gradient(90deg,#38bdf8,#f43f5e);z-index:50;}}
</style></head>
<body>
<div id="stage">
  <div id="prog"></div>
  <div id="grid"></div>
  <div id="alarm-overlay"></div>
  <div id="hud">
    <div class="gauge" id="g-o2"><div class="g-label">BLOOD O₂</div><div class="g-val" id="v-o2" style="color:#38bdf8">99%</div><div class="g-bar"><div class="g-fill" id="b-o2" style="width:99%;background:#38bdf8"></div></div></div>
    <div class="gauge" id="g-co2"><div class="g-label">BLOOD CO₂</div><div class="g-val" id="v-co2" style="color:#fbbf24">40</div><div class="g-bar"><div class="g-fill" id="b-co2" style="width:28%;background:#fbbf24"></div></div></div>
    <div class="gauge" id="g-hr"><div class="g-label">HEART BPM</div><div class="g-val" id="v-hr" style="color:#34d399">74</div><div class="g-bar"><div class="g-fill" id="b-hr" style="width:65%;background:#34d399"></div></div></div>
  </div>
  <div id="phase-pill">00s • BREATH HOLD INITIATED</div>
  <div id="cam">
    <svg id="anatomy" viewBox="0 0 960 1120" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="lungGrad" cx="50%" cy="45%" r="55%">
          <stop id="lg1" offset="0%" stop-color="#38bdf8" stop-opacity="0.85"/>
          <stop id="lg2" offset="100%" stop-color="#1e3a8a" stop-opacity="0.92"/>
        </radialGradient>
        <radialGradient id="brainGrad" cx="50%" cy="50%" r="55%">
          <stop id="bg1" offset="0%" stop-color="#60a5fa" stop-opacity="0.9"/>
          <stop id="bg2" offset="100%" stop-color="#1e293b" stop-opacity="0.95"/>
        </radialGradient>
        <filter id="glow"><feGaussianBlur stdDeviation="12" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <!-- Human silhouette outline -->
      <path d="M480,40 C560,40 605,98 605,175 C605,235 572,282 542,306 L542,360 C650,382 765,450 810,570 L840,1040 L120,1040 L150,570 C195,450 310,382 418,360 L418,306 C388,282 355,235 355,175 C355,98 400,40 480,40 Z"
            fill="rgba(15,28,54,0.68)" stroke="rgba(148,163,184,0.35)" stroke-width="5"/>
      <!-- Brain + Brainstem chemoreceptor -->
      <g id="brain-group">
        <path d="M480,74 C535,74 574,114 570,168 C568,204 542,226 508,228 L508,295 L452,295 L452,228 C418,226 392,204 390,168 C386,114 425,74 480,74 Z"
              fill="url(#brainGrad)" stroke="#93c5fd" stroke-width="4" filter="url(#glow)"/>
        <circle id="brainstem-node" cx="480" cy="252" r="24" fill="#38bdf8" filter="url(#glow)"/>
        <circle id="alarm-ring" cx="480" cy="252" r="28" fill="none" stroke="#ef4444" stroke-width="7" opacity="0"/>
      </g>
      <!-- Trachea & Bronchi -->
      <path d="M464,310 L464,495 L380,555 M496,310 L496,495 L580,555" fill="none" stroke="#bae6fd" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
      <!-- Left & Right Lungs -->
      <g id="lungs-group" transform-origin="480 650">
        <path d="M446,475 C355,465 245,545 220,690 C205,785 245,860 335,855 C405,850 446,800 446,725 Z"
              fill="url(#lungGrad)" stroke="#7dd3fc" stroke-width="5" filter="url(#glow)"/>
        <path d="M514,475 C605,465 715,545 740,690 C755,785 715,860 625,855 C555,850 514,800 514,725 Z"
              fill="url(#lungGrad)" stroke="#7dd3fc" stroke-width="5" filter="url(#glow)"/>
        <!-- Alveoli branch glow lines -->
        <path d="M390,560 L320,625 M390,560 L345,710 M320,625 L270,690 M570,560 L640,625 M570,560 L615,710 M640,625 L690,690"
              stroke="rgba(224,242,254,0.7)" stroke-width="6" stroke-linecap="round"/>
      </g>
      <!-- Beating Heart -->
      <g id="heart-group" transform-origin="480 690">
        <path d="M480,758 C480,758 416,712 416,664 C416,634 440,614 464,624 C474,628 480,638 480,638 C480,638 486,628 496,624 C520,614 544,634 544,664 C544,712 480,758 480,758 Z"
              fill="#f43f5e" stroke="#fecdd3" stroke-width="4" filter="url(#glow)"/>
      </g>
      <!-- Diaphragm arch -->
      <path id="diaphragm" d="M210,895 Q480,825 750,895" fill="none" stroke="#fbbf24" stroke-width="14" stroke-linecap="round" filter="url(#glow)"/>
      <!-- Animated O2 & CO2 bloodstream particles -->
      <g id="particles"></g>
    </svg>
  </div>
  <div id="callout"><div id="callout-title">DIVE REFLEX</div><div id="callout-body">Heart slows -20% to conserve oxygen</div></div>
  <div id="caption-wrap"><div class="cap-line" id="cap"></div></div>
</div>
<script>
const WORDS = {json.dumps(words)};
const DUR = {dur:.3f};
const DANGER_SET = new Set(["carbon","dioxide","panic","alarm","violently","spasm","choking","suffocation","lying","co2"]);

// Pre-build 28 animated blood particles inside SVG
const pGroup = document.getElementById("particles");
const pEls = [];
for (let i = 0; i < 28; i++) {{
  const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  c.setAttribute("r", i % 3 === 0 ? "11" : "8");
  c.setAttribute("filter", "url(#glow)");
  pGroup.appendChild(c);
  pEls.push({{el: c, seed: i * 0.37, lane: i % 2 === 0 ? -1 : 1}});
}}

function easeOut(x) {{ return 1 - Math.pow(1 - Math.max(0, Math.min(1, x)), 3); }}

function buildCaption(t) {{
  let idx = -1;
  for (let i = 0; i < WORDS.length; i++) {{
    if (t >= WORDS[i].start - 0.04 && t <= WORDS[i].end + 0.14) {{ idx = i; break; }}
    if (WORDS[i].start <= t) idx = i;
  }}
  if (idx < 0) return "";
  const chunkStart = Math.floor(idx / 3) * 3;
  const chunk = WORDS.slice(chunkStart, chunkStart + 3);
  return chunk.map((w, j) => {{
    const absIdx = chunkStart + j;
    const isAct = absIdx === idx;
    const clean = w.word.toLowerCase().replace(/[^a-z0-9]/g, "");
    const cls = isAct ? (DANGER_SET.has(clean) ? "w danger" : "w active") : "w";
    return `<span class="${{cls}}">${{w.word}}</span>`;
  }}).join("");
}}

window.renderFrame = function(t, f) {{
  const p = Math.min(1, t / DUR);
  document.getElementById("prog").style.width = (p * 100).toFixed(2) + "%";

  // Telemetry simulation
  const o2 = Math.round(99 - p * 28);
  const co2 = Math.round(40 + Math.pow(p, 1.35) * 34);
  const hr = p < 0.25 ? 74 : (p < 0.55 ? Math.round(74 - (p - 0.25) * 80) : Math.round(50 + (p - 0.55) * 62));

  document.getElementById("v-o2").textContent = o2 + "%";
  document.getElementById("b-o2").style.width = o2 + "%";
  document.getElementById("v-co2").textContent = co2;
  document.getElementById("b-co2").style.width = Math.min(100, Math.round((co2 - 30) * 2.1)) + "%";
  document.getElementById("v-co2").style.color = co2 > 56 ? "#ef4444" : "#fbbf24";
  document.getElementById("b-co2").style.background = co2 > 56 ? "#ef4444" : "#fbbf24";
  document.getElementById("v-hr").textContent = hr;
  document.getElementById("b-hr").style.width = Math.min(100, hr) + "%";

  // Phase banner + dynamic camera choreography (fast visual focus shifts!)
  const cam = document.getElementById("cam");
  const pill = document.getElementById("phase-pill");
  const callout = document.getElementById("callout");
  let scale = 1.0, tx = 0, ty = 0, shakeX = 0, shakeY = 0;

  if (p < 0.16) {{
    const k = easeOut(p / 0.16);
    scale = 1.18 - 0.14 * k;
    pill.textContent = "00s • BREATH HOLD STARTS";
    callout.style.opacity = 0;
  }} else if (p < 0.32) {{
    const k = easeOut((p - 0.16) / 0.16);
    scale = 1.06 + 0.18 * k; ty = -40 * k;
    pill.textContent = "15s • CO₂ RISING IN BLOOD";
    callout.style.opacity = k;
    document.getElementById("callout-title").textContent = "CO₂ BUILDUP";
    document.getElementById("callout-body").textContent = "Blood turns acidic as CO₂ rises — not O₂ loss";
  }} else if (p < 0.48) {{
    const k = easeOut((p - 0.32) / 0.16);
    scale = 1.28 + 0.08 * Math.sin(t * 2); ty = -70;
    pill.textContent = "30s • MAMMALIAN DIVE REFLEX";
    callout.style.opacity = 1;
    document.getElementById("callout-title").textContent = "HEART SLOWS -20%";
    document.getElementById("callout-body").textContent = "Pulse drops to conserve oxygen for brain";
  }} else if (p < 0.66) {{
    const k = easeOut((p - 0.48) / 0.18);
    scale = 1.52; ty = 340 * k;
    pill.textContent = "60s • BRAINSTEM PANIC ALARM";
    pill.style.borderColor = "#ef4444"; pill.style.color = "#fca5a5";
    callout.style.opacity = 1; callout.style.borderColor = "#ef4444";
    document.getElementById("callout-title").style.color = "#f87171";
    document.getElementById("callout-title").textContent = "FALSE PANIC SIGNAL";
    document.getElementById("callout-body").textContent = "Brainstem chemoreceptors trigger urgent gasp";
  }} else if (p < 0.80) {{
    scale = 1.24; ty = -170;
    shakeX = Math.sin(t * 48) * 10;
    shakeY = Math.cos(t * 53) * 8;
    pill.textContent = "DIAPHRAGM SPASM CONTRACTIONS";
    callout.style.opacity = 1;
    document.getElementById("callout-title").textContent = "DIAPHRAGM SPASM";
    document.getElementById("callout-body").textContent = "Involuntary rib contractions force breathing";
  }} else {{
    const k = easeOut((p - 0.80) / 0.20);
    scale = 1.18 - 0.14 * k; ty = 0;
    pill.textContent = "70% OXYGEN STILL REMAINING";
    pill.style.borderColor = "#34d399"; pill.style.color = "#6ee7b7";
    callout.style.borderColor = "#34d399";
    document.getElementById("callout-title").style.color = "#34d399";
    document.getElementById("callout-title").textContent = "THE BRAIN'S LIE";
    document.getElementById("callout-body").textContent = "70% O₂ left — alarm fires minutes before danger";
  }}
  cam.style.transform = `translate(${{(tx + shakeX).toFixed(1)}}px, ${{(ty + shakeY).toFixed(1)}}px) scale(${{scale.toFixed(4)}})`;

  // Continuous living organ animations
  const beatHz = hr / 60;
  const beat = Math.pow(Math.max(0, Math.sin(t * Math.PI * 2 * beatHz)), 6);
  document.getElementById("heart-group").setAttribute("transform", `translate(480,690) scale(${{(1 + beat * 0.14).toFixed(3)}}) translate(-480,-690)`);

  const lungPulse = 1 + Math.sin(t * 2.2) * 0.025 + (p > 0.66 && p < 0.80 ? Math.sin(t * 28) * 0.04 : 0);
  document.getElementById("lungs-group").setAttribute("transform", `translate(480,650) scale(${{lungPulse.toFixed(3)}}) translate(-480,-650)`);

  // Lung color gradually shifts cyan -> purple/crimson as CO2 climbs
  const rC = Math.round(56 + p * 185);
  const gC = Math.round(189 - p * 120);
  const bC = Math.round(248 - p * 145);
  document.getElementById("lg1").setAttribute("stop-color", `rgb(${{rC}},${{gC}},${{bC}})`);

  // Diaphragm spasm wave
  const dY = 825 + (p > 0.66 && p < 0.80 ? Math.sin(t * 36) * 34 : Math.sin(t * 2.6) * 10);
  document.getElementById("diaphragm").setAttribute("d", `M210,895 Q480,${{dY.toFixed(1)}} 750,895`);

  // Brainstem panic pulse ring
  const alarmActive = p > 0.47 && p < 0.82;
  const ringProg = (t * 2.4) % 1;
  document.getElementById("alarm-ring").setAttribute("r", (26 + ringProg * 95).toFixed(1));
  document.getElementById("alarm-ring").setAttribute("opacity", alarmActive ? ((1 - ringProg) * 0.95).toFixed(2) : "0");
  document.getElementById("brainstem-node").setAttribute("fill", alarmActive ? "#ef4444" : "#38bdf8");
  document.getElementById("alarm-overlay").style.opacity = alarmActive ? (0.28 + 0.25 * Math.sin(t * 14)).toFixed(2) : "0";

  // Flowing O2/CO2 particles rising from lungs up carotid arteries to brainstem
  for (let i = 0; i < pEls.length; i++) {{
    const item = pEls[i];
    const prog = (t * 0.38 + item.seed) % 1;
    const x = 480 + item.lane * (170 * (1 - prog) + 28 * prog) + Math.sin(t * 4 + i) * 18;
    const y = 760 - prog * 515;
    item.el.setAttribute("cx", x.toFixed(1));
    item.el.setAttribute("cy", y.toFixed(1));
    const isCO2 = (i / pEls.length) < (0.15 + p * 0.8);
    item.el.setAttribute("fill", isCO2 ? "#f43f5e" : "#38bdf8");
    item.el.setAttribute("opacity", (Math.sin(prog * Math.PI) * 0.92).toFixed(2));
  }}

  document.getElementById("cap").innerHTML = buildCaption(t);
}};
window.__RENDER_READY__ = true;
</script>
</body></html>"""

    out_mp4 = OUT_DIR / "01_visual_explainer_pilot.mp4"
    render_html_video(html, master, out_mp4, dur, work_dir)
    return {**verify_pilot_metrics(out_mp4), "voice": voice_info["voice"], "wpm": voice_info["wpm"]}


# ---------------------------------------------------------------------------
# PILOT 2: CATEGORY 2 — FAST-CUT DARK HISTORY & GEOPOLITICAL MAP DOC
# ---------------------------------------------------------------------------
def build_pilot_2_dark_history(work_dir: Path, img_ice: str, img_tunnel: str) -> dict[str, Any]:
    print("\n=== BUILDING PILOT 2: Category 2 — Fast-Cut Dark History & Map Documentary ===")
    script = (
        "In 1959, the US Army secretly built a nuclear-powered city deep inside Greenland's ice sheet. "
        "Publicly, they called it Camp Century, a peaceful Arctic research base. "
        "Declassified files revealed the real mission: Project Iceworm. "
        "The Pentagon planned to carve two thousand five hundred miles of tunnels beneath the glacier "
        "to hide six hundred nuclear missiles aimed straight at the Soviet Union. "
        "They even hauled in a portable nuclear reactor, a theater, and a hospital for two hundred soldiers. "
        "One problem: the ice sheet wasn't solid. It slowly crushed the steel tunnels until the base was abandoned in 1967, "
        "leaving radioactive waste buried under the melting Arctic ice to this day."
    )
    wav = work_dir / "p2_voice.wav"
    words_json = work_dir / "p2_words.json"
    voice_info = synthesize_with_word_timestamps(
        script_text=script,
        out_wav=wav,
        out_words_json=words_json,
        voice="am_fenrir",
        speed=1.15,
    )
    dur = voice_info["duration_sec"]
    words = clean_words(voice_info["words"])

    # Rapid ~2.1s cut cadence with booms & whooshes!
    cut_fracs = [0.0, 0.08, 0.17, 0.27, 0.38, 0.49, 0.60, 0.72, 0.84, 0.92]
    events = [{"t": 0.03, "kind": "boom", "gain": 1.0}]
    for cf in cut_fracs[1:]:
        events.append({"t": dur * cf, "kind": "whoosh", "gain": 0.85})
    events.extend([
        {"t": dur * 0.27, "kind": "boom", "gain": 0.95},
        {"t": dur * 0.49, "kind": "boom", "gain": 0.95},
        {"t": dur * 0.72, "kind": "riser", "gain": 0.9},
        {"t": dur * 0.84, "kind": "boom", "gain": 1.0},
    ])
    master = work_dir / "p2_master.m4a"
    build_viral_master_audio(voice_wav=wav, out_m4a=master, events=events, mood="thriller")

    ice_uri = img_to_data_uri(img_ice)
    tun_uri = img_to_data_uri(img_tunnel)

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#05080f;font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","Helvetica Neue",sans-serif;color:#fff;}}
#stage{{position:relative;width:1080px;height:1920px;overflow:hidden;background:#05080f;}}
.layer{{position:absolute;inset:0;opacity:0;}}
.bg-img{{width:100%;height:100%;object-fit:cover;transform-origin:center center;filter:contrast(1.12) saturate(1.08);}}
#vignette{{position:absolute;inset:0;background:radial-gradient(circle at 50% 45%,transparent 28%,rgba(3,6,14,.86) 100%);z-index:18;pointer-events:none;}}
#flash{{position:absolute;inset:0;background:#fff;opacity:0;z-index:45;pointer-events:none;}}
#top-tag{{position:absolute;top:115px;left:54px;padding:10px 24px;border-radius:10px;background:rgba(15,23,42,.9);border:2px solid #f59e0b;color:#fcd34d;font-size:24px;font-weight:900;letter-spacing:2.4px;z-index:30;}}
#year-counter{{position:absolute;top:112px;right:54px;font-size:42px;font-weight:900;font-variant-numeric:tabular-nums;color:#f8fafc;text-shadow:0 4px 16px rgba(0,0,0,.9);z-index:30;}}
#hook-banner{{position:absolute;top:245px;left:48px;right:48px;text-align:center;z-index:32;opacity:0;}}
#hook-banner span{{display:inline-block;font-size:74px;font-weight:950;line-height:1.02;color:#facc15;text-transform:uppercase;text-shadow:0 8px 28px rgba(0,0,0,.95),-4px -4px 0 #000,4px -4px 0 #000,-4px 4px 0 #000,4px 4px 0 #000;}}
/* Declassified CIA/Army Memo Card */
#memo-layer{{display:flex;align-items:center;justify-content:center;background:radial-gradient(circle at 50% 45%,#1a1f2e,#070a12);z-index:12;}}
#memo-paper{{width:860px;background:#e8dfc8;color:#111827;border-radius:12px;padding:54px 56px;box-shadow:0 35px 90px rgba(0,0,0,.85);transform-origin:center;border:3px solid #94a3b8;}}
.stamp{{display:inline-block;border:6px solid #dc2626;color:#dc2626;font-size:34px;font-weight:900;letter-spacing:4px;padding:6px 20px;transform:rotate(-5deg);margin-bottom:26px;}}
.memo-h{{font-family:"Courier New",monospace;font-size:28px;font-weight:900;border-bottom:3px solid #1f2937;padding-bottom:14px;margin-bottom:24px;}}
.memo-p{{font-family:"Courier New",monospace;font-size:32px;line-height:1.58;font-weight:700;position:relative;}}
.redact-wrap{{position:relative;display:inline-block;padding:0 8px;}}
.redact-bar{{position:absolute;inset:0;background:#111827;transform-origin:right center;}}
.hl-wrap{{position:relative;display:inline-block;padding:0 6px;}}
.hl-bg{{position:absolute;inset:2px 0;background:rgba(250,204,21,.75);z-index:-1;transform-origin:left center;}}
/* Sub-ice blueprint layer */
#bp-layer{{background:radial-gradient(circle at 50% 45%,#0b2545,#040b18);z-index:12;}}
#caption-wrap{{position:absolute;left:56px;right:56px;bottom:330px;text-align:center;z-index:40;min-height:150px;display:flex;align-items:center;justify-content:center;}}
.cap-line{{display:inline-flex;flex-wrap:wrap;justify-content:center;gap:14px 26px;}}
.w{{font-size:62px;font-weight:900;color:#ffffff;text-shadow:0 6px 24px rgba(0,0,0,.95),-3px -3px 0 #000,3px -3px 0 #000,-3px 3px 0 #000,3px 3px 0 #000;display:inline-block;padding:0 4px;}}
.w.active{{color:#facc15;transform:scale(1.09);}}
#prog{{position:absolute;top:0;left:0;height:10px;background:linear-gradient(90deg,#f59e0b,#ef4444);z-index:50;}}
</style></head>
<body>
<div id="stage">
  <div id="prog"></div>

  <!-- Layer A: RealLifeLore-style Satellite Greenland Map Zoom -->
  <div class="layer" id="l-map">
    <svg id="map-svg" viewBox="0 0 1080 1920" width="1080" height="1920" style="transform-origin:540px 760px;">
      <rect width="1080" height="1920" fill="#071222"/>
      <!-- Latitude/Longitude tactical grid -->
      <g stroke="rgba(56,189,248,0.14)" stroke-width="2">
        <line x1="0" y1="360" x2="1080" y2="360"/><line x1="0" y1="720" x2="1080" y2="720"/><line x1="0" y1="1080" x2="1080" y2="1080"/><line x1="0" y1="1440" x2="1080" y2="1440"/>
        <line x1="270" y1="0" x2="270" y2="1920"/><line x1="540" y1="0" x2="540" y2="1920"/><line x1="810" y1="0" x2="810" y2="1920"/>
      </g>
      <!-- Stylized Arctic landmass: Canada / Iceland / glowing Greenland -->
      <path d="M-20,620 L180,680 L230,900 L140,1180 L-20,1260 Z" fill="#132238" stroke="#334155" stroke-width="3"/>
      <path d="M840,1040 L990,1010 L1060,1100 L960,1160 L850,1120 Z" fill="#132238" stroke="#334155" stroke-width="3"/>
      <!-- Greenland territory outline with animated amber border -->
      <path id="greenland" d="M475,270 L660,295 L795,430 L815,670 L740,940 L635,1170 L535,1275 L465,1140 L410,930 L345,760 L330,520 L395,350 Z"
            fill="rgba(245,158,11,0.18)" stroke="#f59e0b" stroke-width="7" stroke-linejoin="round"/>
      <!-- Camp Century pin + animated radar rings -->
      <circle id="radar1" cx="432" cy="560" r="24" fill="none" stroke="#ef4444" stroke-width="5"/>
      <circle id="radar2" cx="432" cy="560" r="56" fill="none" stroke="#f59e0b" stroke-width="4"/>
      <circle cx="432" cy="560" r="14" fill="#ef4444"/>
      <line x1="432" y1="560" x2="660" y2="470" stroke="#facc15" stroke-width="4" stroke-dasharray="10 8"/>
      <rect x="655" y="425" width="325" height="92" rx="14" fill="rgba(10,16,30,0.92)" stroke="#facc15" stroke-width="3"/>
      <text x="680" y="465" fill="#facc15" font-size="26" font-weight="900">CAMP CENTURY</text>
      <text x="680" y="498" fill="#cbd5e1" font-size="21" font-weight="700">77.17° N • 61.13° W</text>
    </svg>
  </div>

  <!-- Layer B: Arctic Ice Radar Cinema Plate -->
  <div class="layer" id="l-ice"><img class="bg-img" id="img-ice" src="{ice_uri}"/></div>

  <!-- Layer C: Declassified CIA/Army Memo with Sliding Redaction & Highlighter -->
  <div class="layer" id="memo-layer">
    <div id="memo-paper">
      <div class="stamp">DECLASSIFIED • 1996</div>
      <div class="memo-h">U.S. ARMY POLAR R&amp;D • FILE #ICW-1959</div>
      <div class="memo-p">
        CODE NAME: <span class="redact-wrap"><span style="color:#b91c1c;font-weight:900;">PROJECT ICEWORM</span><span class="redact-bar" id="rb1"></span></span><br/><br/>
        OBJECTIVE: CARVE <span class="hl-wrap">2,500 MILES<span class="hl-bg" id="hl1"></span></span> OF SUB-ICE TUNNELS TO DEPLOY <span class="redact-wrap"><span style="color:#b91c1c;font-weight:900;">600 NUCLEAR MISSILES</span><span class="redact-bar" id="rb2"></span></span> UNDER GREENLAND'S GLACIER.
      </div>
    </div>
  </div>

  <!-- Layer D: Subterranean Ice Tunnel Cinema Plate -->
  <div class="layer" id="l-tunnel"><img class="bg-img" id="img-tun" src="{tun_uri}"/></div>

  <!-- Layer E: Sub-Ice Nuclear Reactor & Tunnel Cross-Section Blueprint -->
  <div class="layer" id="bp-layer">
    <svg viewBox="0 0 1080 1920" width="1080" height="1920">
      <!-- Ice glacier cross-section -->
      <rect x="0" y="420" width="1080" height="820" fill="rgba(56,189,248,0.12)"/>
      <path d="M0,440 Q260,395 540,435 T1080,415 L1080,480 L0,480 Z" fill="#bae6fd" opacity="0.85"/>
      <text x="80" y="395" fill="#7dd3fc" font-size="28" font-weight="900" letter-spacing="2">ARCTIC SURFACE (-56°C)</text>
      <!-- Tunnel Network drawing animated -->
      <g stroke="#facc15" stroke-width="10" fill="none" stroke-linecap="round">
        <line id="tun-main" x1="120" y1="760" x2="960" y2="760" stroke-dasharray="900" stroke-dashoffset="900"/>
        <line x1="280" y1="760" x2="280" y2="960"/><line x1="540" y1="760" x2="540" y2="960"/><line x1="800" y1="760" x2="800" y2="960"/>
      </g>
      <!-- PM-2A Portable Nuclear Reactor pulsing node -->
      <g id="reactor" transform="translate(540,980)">
        <circle id="rx-pulse" r="65" fill="rgba(239,68,68,0.28)" stroke="#ef4444" stroke-width="5"/>
        <rect x="-85" y="-42" width="170" height="84" rx="14" fill="#1e293b" stroke="#facc15" stroke-width="4"/>
        <text x="0" y="-6" text-anchor="middle" fill="#facc15" font-size="24" font-weight="900">PM-2A</text>
        <text x="0" y="24" text-anchor="middle" fill="#fff" font-size="18" font-weight="800">NUCLEAR CORE</text>
      </g>
      <!-- Left & Right facility callouts -->
      <rect x="140" y="940" width="240" height="82" rx="14" fill="rgba(15,23,42,0.92)" stroke="#38bdf8" stroke-width="3"/>
      <text x="260" y="976" text-anchor="middle" fill="#38bdf8" font-size="22" font-weight="900">21 TUNNELS</text>
      <text x="260" y="1004" text-anchor="middle" fill="#e2e8f0" font-size="18" font-weight="700">200 SOLDIERS</text>
      <rect x="700" y="940" width="250" height="82" rx="14" fill="rgba(15,23,42,0.92)" stroke="#ef4444" stroke-width="3"/>
      <text x="825" y="976" text-anchor="middle" fill="#f87171" font-size="22" font-weight="900">CRUSHED 1967</text>
      <text x="825" y="1004" text-anchor="middle" fill="#e2e8f0" font-size="18" font-weight="700">TOXIC WASTE LEFT</text>
    </svg>
  </div>

  <div id="vignette"></div>
  <div id="flash"></div>
  <div id="top-tag">NORTHWEST GREENLAND</div>
  <div id="year-counter">1959</div>
  <div id="hook-banner"><span>SECRET CITY<br/>UNDER THE ICE</span></div>
  <div id="caption-wrap"><div class="cap-line" id="cap"></div></div>
</div>
<script>
const WORDS = {json.dumps(words)};
const DUR = {dur:.3f};
const CUTS = {json.dumps(cut_fracs)};

function easeOut(x) {{ return 1 - Math.pow(1 - Math.max(0, Math.min(1, x)), 3); }}

function buildCaption(t) {{
  let idx = -1;
  for (let i = 0; i < WORDS.length; i++) {{
    if (t >= WORDS[i].start - 0.04 && t <= WORDS[i].end + 0.14) {{ idx = i; break; }}
    if (WORDS[i].start <= t) idx = i;
  }}
  if (idx < 0) return "";
  const s = Math.floor(idx / 3) * 3;
  return WORDS.slice(s, s + 3).map((w, j) => `<span class="w ${{s+j===idx ? 'active':''}}">${{w.word}}</span>`).join("");
}}

window.renderFrame = function(t, f) {{
  const p = Math.min(1, t / DUR);
  document.getElementById("prog").style.width = (p * 100).toFixed(2) + "%";

  // Subtle white film-flash on rapid cuts
  let flashOp = 0;
  for (const cf of CUTS) {{
    const dt = Math.abs(t - cf * DUR);
    if (cf > 0 && dt < 0.11) flashOp = Math.max(flashOp, (1 - dt / 0.11) * 0.42);
  }}
  document.getElementById("flash").style.opacity = flashOp.toFixed(3);

  // Hook title slam (0 - 2.6s)
  document.getElementById("hook-banner").style.opacity = t < 2.6 ? (t < 2.2 ? 1 : (2.6 - t) / 0.4).toFixed(2) : "0";

  // Hide all layers first
  ["l-map","l-ice","memo-layer","l-tunnel","bp-layer"].forEach(id => document.getElementById(id).style.opacity = "0");

  const tag = document.getElementById("top-tag");
  const yr = document.getElementById("year-counter");

  if (p < 0.17) {{
    document.getElementById("l-map").style.opacity = "1";
    const k = easeOut(p / 0.17);
    const ms = 0.92 + 0.55 * k;
    document.getElementById("map-svg").style.transform = `scale(${{ms.toFixed(3)}}) translate(${{(60*k).toFixed(1)}}px, ${{(90*k).toFixed(1)}}px)`;
    const rp = (t * 1.8) % 1;
    document.getElementById("radar1").setAttribute("r", (16 + rp * 85).toFixed(1));
    document.getElementById("radar1").setAttribute("opacity", (1 - rp).toFixed(2));
    tag.textContent = "NORTHWEST GREENLAND"; yr.textContent = "1959";
  }} else if (p < 0.27) {{
    document.getElementById("l-ice").style.opacity = "1";
    const k = easeOut((p - 0.17) / 0.10);
    document.getElementById("img-ice").style.transform = `scale(${{(1.22 - 0.12 * k).toFixed(3)}})`;
    tag.textContent = "CAMP CENTURY • COVER STORY"; yr.textContent = "1959";
  }} else if (p < 0.49) {{
    document.getElementById("memo-layer").style.opacity = "1";
    const k = Math.min(1, (p - 0.27) / 0.22);
    document.getElementById("memo-paper").style.transform = `scale(${{(0.94 + 0.08 * easeOut(k)).toFixed(3)}}) rotate(${{(-1.5 + 1.5 * k).toFixed(2)}}deg)`;
    document.getElementById("rb1").style.transform = `scaleX(${{Math.max(0, 1 - k * 3.5).toFixed(3)}})`;
    document.getElementById("hl1").style.transform = `scaleX(${{Math.min(1, Math.max(0, (k - 0.25) * 3.5)).toFixed(3)}})`;
    document.getElementById("rb2").style.transform = `scaleX(${{Math.max(0, 1 - Math.max(0, k - 0.52) * 3.5).toFixed(3)}})`;
    tag.textContent = "DECLASSIFIED • PROJECT ICEWORM"; yr.textContent = "1960";
  }} else if (p < 0.66) {{
    document.getElementById("l-tunnel").style.opacity = "1";
    const k = (p - 0.49) / 0.17;
    document.getElementById("img-tun").style.transform = `scale(${{(1.04 + 0.18 * k).toFixed(3)}}) translateX(${{(Math.sin(t*3)*12).toFixed(1)}}px)`;
    tag.textContent = "28 FEET UNDER SOLID ICE"; yr.textContent = "1962";
  }} else if (p < 0.84) {{
    document.getElementById("bp-layer").style.opacity = "1";
    const k = easeOut((p - 0.66) / 0.18);
    document.getElementById("tun-main").setAttribute("stroke-dashoffset", Math.round(900 * (1 - k)));
    const rx = 58 + Math.sin(t * 10) * 14;
    document.getElementById("rx-pulse").setAttribute("r", rx.toFixed(1));
    tag.textContent = "PORTABLE NUCLEAR REACTOR"; yr.textContent = p > 0.76 ? "1967" : "1964";
  }} else {{
    document.getElementById("l-ice").style.opacity = "1";
    const k = (p - 0.84) / 0.16;
    document.getElementById("img-ice").style.transform = `scale(${{(1.15 + 0.14 * k).toFixed(3)}})`;
    document.getElementById("img-ice").style.filter = "contrast(1.25) saturate(1.25) hue-rotate(-14deg)";
    tag.textContent = "MELTING GLACIER • STILL BURIED"; yr.textContent = "2090";
  }}

  document.getElementById("cap").innerHTML = buildCaption(t);
}};
window.__RENDER_READY__ = true;
</script>
</body></html>"""

    out_mp4 = OUT_DIR / "02_dark_history_map_pilot.mp4"
    render_html_video(html, master, out_mp4, dur, work_dir)
    return {**verify_pilot_metrics(out_mp4), "voice": voice_info["voice"], "wpm": voice_info["wpm"]}


# ---------------------------------------------------------------------------
# PILOT 3: CATEGORY 3 — FAST-CUT DARK PSYCHOLOGY KINETIC (34+ CPM!)
# ---------------------------------------------------------------------------
def build_pilot_3_psychology(work_dir: Path, img_stare: str, img_chess: str) -> dict[str, Any]:
    print("\n=== BUILDING PILOT 3: Category 3 — Fast-Cut Dark Psychology (34+ CPM) ===")
    script = (
        "When someone disrespects you in front of others, never defend yourself. "
        "Defending yourself instantly proves they hold the power. "
        "Instead, use these three quiet psychological moves. "
        "Move one: the three-second stare. Hold calm eye contact in total silence for three full seconds. "
        "Their brain panics and starts scrambling to walk the insult back. "
        "Move two: ask calmly, did you mean to say that out loud? "
        "Now the whole room's awkwardness flips straight onto them. "
        "Move three: smile slightly and change the topic like they don't matter. "
        "The calmest person in the room always wins."
    )
    wav = work_dir / "p3_voice.wav"
    words_json = work_dir / "p3_words.json"
    voice_info = synthesize_with_word_timestamps(
        script_text=script,
        out_wav=wav,
        out_words_json=words_json,
        voice="am_fenrir",
        speed=1.18,
    )
    dur = voice_info["duration_sec"]
    words = clean_words(voice_info["words"])

    # High-velocity 34+ CPM beat cuts (visual state pulse every ~1.7s!)
    n_beats = 20
    events = [{"t": 0.02, "kind": "boom", "gain": 1.0}]
    for i in range(1, n_beats):
        bt = (i / n_beats) * dur
        kind = "boom" if i in (4, 10, 15, 18) else ("pop" if i % 2 == 0 else "whoosh")
        events.append({"t": bt, "kind": kind, "gain": 0.85})
    master = work_dir / "p3_master.m4a"
    build_viral_master_audio(voice_wav=wav, out_m4a=master, events=events, mood="psychology")

    stare_uri = img_to_data_uri(img_stare)
    chess_uri = img_to_data_uri(img_chess)

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#06060b;font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","Helvetica Neue",sans-serif;color:#fff;}}
#stage{{position:relative;width:1080px;height:1920px;overflow:hidden;background:#06060b;}}
#bg-wrap{{position:absolute;inset:0;}}
.bg-img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0;filter:brightness(0.45) contrast(1.22);transform-origin:center;}}
#power-hud{{position:absolute;top:110px;left:56px;right:56px;background:rgba(12,12,20,.88);border:2px solid rgba(255,255,255,.14);border-radius:20px;padding:18px 24px;z-index:30;}}
.ph-row{{display:flex;justify-content:space-between;font-size:21px;font-weight:900;letter-spacing:1.8px;margin-bottom:10px;}}
.ph-bar{{height:16px;border-radius:10px;background:#ef4444;overflow:hidden;position:relative;}}
#ph-you{{height:100%;background:linear-gradient(90deg,#f59e0b,#facc15);width:22%;}}
#slam-title{{position:absolute;top:295px;left:40px;right:40px;text-align:center;font-size:112px;font-weight:950;line-height:0.96;letter-spacing:-2px;color:rgba(255,255,255,.14);text-transform:uppercase;z-index:12;}}
#center-card{{position:absolute;top:520px;left:76px;right:76px;z-index:28;}}
.card-box{{background:rgba(14,16,28,.92);border:3px solid rgba(250,204,21,.55);border-radius:28px;padding:40px 42px;box-shadow:0 30px 90px rgba(0,0,0,.85);text-align:center;}}
.move-badge{{display:inline-block;padding:8px 24px;border-radius:999px;font-size:24px;font-weight:900;letter-spacing:2.5px;margin-bottom:18px;}}
.card-h{{font-size:56px;font-weight:950;line-height:1.1;margin-bottom:14px;}}
.card-sub{{font-size:30px;color:#cbd5e1;font-weight:600;line-height:1.35;}}
#timer-big{{font-size:118px;font-weight:950;color:#facc15;font-variant-numeric:tabular-nums;margin-top:8px;text-shadow:0 0 40px rgba(250,204,21,.45);}}
#flash{{position:absolute;inset:0;background:#fff;opacity:0;z-index:45;pointer-events:none;}}
#caption-wrap{{position:absolute;left:54px;right:54px;bottom:335px;text-align:center;z-index:40;min-height:160px;display:flex;align-items:center;justify-content:center;}}
.cap-line{{display:inline-flex;flex-wrap:wrap;justify-content:center;gap:14px 26px;}}
.w{{font-size:60px;font-weight:950;text-transform:uppercase;color:#ffffff;text-shadow:0 6px 24px rgba(0,0,0,.95),-3px -3px 0 #000,3px -3px 0 #000,-3px 3px 0 #000,3px 3px 0 #000;display:inline-block;padding:0 4px;}}
.w.active{{color:#facc15;transform:scale(1.09);}}
.w.threat{{color:#ef4444;transform:scale(1.09);}}
#prog{{position:absolute;top:0;left:0;height:10px;background:linear-gradient(90deg,#ef4444,#facc15);z-index:50;}}
</style></head>
<body>
<div id="stage">
  <div id="prog"></div>
  <div id="bg-wrap">
    <img class="bg-img" id="bg1" src="{stare_uri}"/>
    <img class="bg-img" id="bg2" src="{chess_uri}"/>
  </div>
  <div id="slam-title">SHUT DOWN<br/>DISRESPECT</div>
  <div id="power-hud">
    <div class="ph-row"><span style="color:#facc15">YOUR STATUS: <span id="pct-you">22%</span></span><span style="color:#f87171">THEIR CONTROL</span></div>
    <div class="ph-bar"><div id="ph-you"></div></div>
  </div>
  <div id="center-card"></div>
  <div id="flash"></div>
  <div id="caption-wrap"><div class="cap-line" id="cap"></div></div>
</div>
<script>
const WORDS = {json.dumps(words)};
const DUR = {dur:.3f};
const THREAT_SET = new Set(["disrespects","never","defend","defending","panics","insult","awkwardness"]);

function easeOut(x) {{ return 1 - Math.pow(1 - Math.max(0, Math.min(1, x)), 3); }}

function buildCaption(t) {{
  let idx = -1;
  for (let i = 0; i < WORDS.length; i++) {{
    if (t >= WORDS[i].start - 0.04 && t <= WORDS[i].end + 0.14) {{ idx = i; break; }}
    if (WORDS[i].start <= t) idx = i;
  }}
  if (idx < 0) return "";
  const s = Math.floor(idx / 3) * 3;
  return WORDS.slice(s, s + 3).map((w, j) => {{
    const clean = w.word.toLowerCase().replace(/[^a-z0-9]/g, "");
    const act = s + j === idx;
    const cls = act ? (THREAT_SET.has(clean) ? "w threat" : "w active") : (THREAT_SET.has(clean) ? "w threat" : "w");
    return `<span class="${{cls}}">${{w.word}}</span>`;
  }}).join("");
}}

window.renderFrame = function(t, f) {{
  const p = Math.min(1, t / DUR);
  document.getElementById("prog").style.width = (p * 100).toFixed(2) + "%";

  // Rapid 1.75s zoom-punch rhythm (34+ CPM kinetic feel!)
  const beatDur = DUR / 20;
  const beatIdx = Math.floor(t / beatDur);
  const beatLocal = (t % beatDur) / beatDur;
  const punchScale = 1.16 - 0.10 * easeOut(beatLocal * 2.5);

  const bg1 = document.getElementById("bg1");
  const bg2 = document.getElementById("bg2");
  const useChess = beatIdx % 2 === 1 || p > 0.72;
  bg1.style.opacity = useChess ? "0" : "1";
  bg2.style.opacity = useChess ? "1" : "0";
  const tilt = (beatIdx % 2 === 0 ? 1 : -1) * 1.4;
  bg1.style.transform = `scale(${{punchScale.toFixed(3)}}) rotate(${{tilt}}deg)`;
  bg2.style.transform = `scale(${{punchScale.toFixed(3)}}) rotate(${{-tilt}}deg)`;

  // Crisp subtle transition flash every beat cut
  const fOp = beatLocal < 0.09 && beatIdx > 0 ? (1 - beatLocal / 0.09) * 0.28 : 0;
  document.getElementById("flash").style.opacity = fOp.toFixed(3);

  // Power status shifts from 20% -> 96% as moves execute
  const youPct = Math.round(20 + easeOut(Math.max(0, (p - 0.16) / 0.78)) * 76);
  document.getElementById("pct-you").textContent = youPct + "%";
  document.getElementById("ph-you").style.width = youPct + "%";

  // Center dynamic psychological card changes rapidly across beats!
  const card = document.getElementById("center-card");
  const popS = 0.94 + 0.06 * easeOut(beatLocal * 3.5);
  card.style.transform = `scale(${{popS.toFixed(3)}})`;

  if (p < 0.14) {{
    card.innerHTML = `<div class="card-box" style="border-color:#ef4444"><div class="move-badge" style="background:rgba(239,68,68,.22);color:#fca5a5">⚠️ THE TRAP</div><div class="card-h" style="color:#f87171">NEVER DEFEND</div><div class="card-sub">Explaining yourself signals low status instantly.</div></div>`;
  }} else if (p < 0.25) {{
    card.innerHTML = `<div class="card-box" style="border-color:#facc15"><div class="move-badge" style="background:rgba(250,204,21,.2);color:#fde047">DARK PSYCHOLOGY</div><div class="card-h">3 QUIET MOVES</div><div class="card-sub">Flip control of the room in under 5 seconds.</div></div>`;
  }} else if (p < 0.50) {{
    const sec = Math.min(3.0, ((p - 0.25) / 0.18) * 3.0).toFixed(1);
    card.innerHTML = `<div class="card-box" style="border-color:#facc15"><div class="move-badge" style="background:rgba(250,204,21,.2);color:#fde047">MOVE 01</div><div class="card-h">THE 3-SECOND STARE</div><div id="timer-big">${{sec}}s</div><div class="card-sub">Zero words. Calm eyes. Let their brain panic.</div></div>`;
  }} else if (p < 0.74) {{
    card.innerHTML = `<div class="card-box" style="border-color:#38bdf8"><div class="move-badge" style="background:rgba(56,189,248,.2);color:#7dd3fc">MOVE 02</div><div class="card-h">THE CALM MIRROR</div><div class="card-sub" style="color:#fff;font-size:34px;margin-top:10px;">“Did you mean to say that out loud?”</div></div>`;
  }} else {{
    card.innerHTML = `<div class="card-box" style="border-color:#34d399"><div class="move-badge" style="background:rgba(52,211,153,.2);color:#6ee7b7">MOVE 03 • CHECKMATE</div><div class="card-h" style="color:#facc15">SMILE &amp; MOVE ON</div><div class="card-sub">The calmest person in the room always wins.</div></div>`;
  }}

  document.getElementById("cap").innerHTML = buildCaption(t);
}};
window.__RENDER_READY__ = true;
</script>
</body></html>"""

    out_mp4 = OUT_DIR / "03_dark_psychology_pilot.mp4"
    render_html_video(html, master, out_mp4, dur, work_dir)
    return {**verify_pilot_metrics(out_mp4), "voice": voice_info["voice"], "wpm": voice_info["wpm"]}


# ---------------------------------------------------------------------------
# PILOT 4: CATEGORY 4 — WATCHDATA CONTINUOUS RARITY CONVEYOR (0.0% STATIC!)
# ---------------------------------------------------------------------------
def build_pilot_4_scale_comparison(work_dir: Path) -> dict[str, Any]:
    print("\n=== BUILDING PILOT 4: Category 4 — WatchData-Style Rarity Conveyor ===")
    # Empirical WatchData formula: punchy 3.5s spoken hook at t=0.0s, then pure addictive scroll + ticks + beat!
    hook_script = "If you have any of these body traits, watch until the end to see how rare you really are."
    wav_hook = work_dir / "p4_hook.wav"
    words_json = work_dir / "p4_words.json"
    voice_info = synthesize_with_word_timestamps(
        script_text=hook_script,
        out_wav=wav_hook,
        out_words_json=words_json,
        voice="am_michael",
        speed=1.12,
    )
    # Pad voice WAV with silence to full 42.0s conveyor duration so sfx_engine builds the full 42s propulsive track!
    dur = 42.0
    wav_full = work_dir / "p4_voice_42s.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(wav_hook), "-af", f"apad=whole_dur={dur}", "-ar", "44100", "-ac", "1", str(wav_full)],
        check=True,
    )

    traits = [
        ("90%", "OF HUMANS", "Right-Handed", "Nine in ten humans naturally dominate with their right hand.", "#dc2626", "✋"),
        ("70%", "OF HUMANS", "Can Roll Tongue", "Most people can curl their tongue edges into a tube.", "#dc2626", "👅"),
        ("35%", "OF HUMANS", "Born Without Wisdom Teeth", "Evolution is slowly phasing wisdom teeth out.", "#ea580c", "🦷"),
        ("25%", "OF HUMANS", "Sun Sneezing Reflex", "Bright sunlight instantly triggers uncontrollable sneezes.", "#ea580c", "☀️"),
        ("20%", "OF HUMANS", "Cheek Dimples", "Caused by a shortened zygomaticus facial muscle.", "#d97706", "😊"),
        ("15%", "OF HUMANS", "Outie Belly Button", "Only about one in seven humans has an outward navel.", "#d97706", "🌀"),
        ("10%", "OF HUMANS", "Left-Handed", "Historically rare and strongly linked to visual creativity.", "#0284c7", "✍️"),
        ("8%", "OF HUMANS", "Blue Eyes", "Every blue-eyed person shares one ancestor from 10,000 years ago.", "#0284c7", "👁️"),
        ("2%", "OF HUMANS", "Natural Green Eyes", "The rarest common eye color found across the planet.", "#059669", "💚"),
        ("1%", "OF HUMANS", "True Ambidextrous", "Equal precision and speed using both left and right hands.", "#059669", "⚡"),
        ("0.6%", "OF HUMANS", "Complete Heterochromia", "Two completely different iris colors in the same person.", "#7c3aed", "🔮"),
        ("0.5%", "OF HUMANS", "Extra Cervical Rib", "Born with a rare extra rib above the first normal rib.", "#7c3aed", "🦴"),
        ("0.1%", "OF HUMANS", "Double Eyelashes", "Distichiasis gives two full rows of eyelashes per lid.", "#9333ea", "✨"),
        ("0.05%", "OF HUMANS", "Perfect Pitch", "Can identify any musical note instantly without reference.", "#c026d3", "🎵"),
        ("0.01%", "OF HUMANS", "Unbreakable Bones", "LRP5 gene mutation makes bones up to 8x denser than normal.", "#eab308", "🛡️"),
        ("1 IN 6M", "MYTHIC", "Golden Blood (Rh-Null)", "Fewer than 50 people alive carry zero Rh antigens.", "#f59e0b", "👑"),
    ]

    # Sync crisp tick/pop SFX as each of the 16 cards crosses the center spotlight + boom on finale!
    events = [{"t": 0.05, "kind": "boom", "gain": 0.85}]
    for i in range(len(traits)):
        card_t = 2.6 + i * ((dur - 5.2) / len(traits))
        events.append({"t": card_t, "kind": "boom" if i == len(traits) - 1 else "tick", "gain": 0.9 if i == len(traits) - 1 else 0.72})
    events.append({"t": dur - 3.0, "kind": "riser", "gain": 0.85})
    master = work_dir / "p4_master.m4a"
    build_viral_master_audio(voice_wav=wav_full, out_m4a=master, events=events, mood="scale")

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#101521;font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","Helvetica Neue",sans-serif;color:#fff;}}
#stage{{position:relative;width:1080px;height:1920px;overflow:hidden;background:radial-gradient(circle at 50% 48%,#182236 0%,#0c111b 75%);}}
#grid{{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);background-size:60px 60px;}}
#top-hud{{position:absolute;top:0;left:0;right:0;height:270px;background:linear-gradient(180deg,rgba(10,14,24,.98) 72%,rgba(10,14,24,0));padding:88px 54px 20px;z-index:30;}}
#top-title{{font-size:48px;font-weight:950;letter-spacing:-0.5px;text-align:center;color:#fff;}}
#tier-row{{display:flex;justify-content:space-between;align-items:center;margin-top:16px;font-size:22px;font-weight:900;letter-spacing:2px;}}
#meter-track{{height:16px;border-radius:10px;background:rgba(255,255,255,.12);margin-top:10px;overflow:hidden;}}
#meter-fill{{height:100%;width:5%;background:linear-gradient(90deg,#ef4444,#f59e0b,#38bdf8,#a855f7,#facc15);border-radius:10px;}}
#viewport{{position:absolute;top:240px;left:0;right:0;bottom:140px;overflow:hidden;}}
#belt{{position:absolute;left:52px;right:52px;top:0;will-change:transform;}}
.row{{height:290px;margin-bottom:34px;display:flex;align-items:center;gap:28px;transform-origin:center center;}}
.hex-wrap{{width:270px;height:270px;flex-shrink:0;position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;}}
.hex-svg{{position:absolute;inset:0;width:100%;height:100%;}}
.hex-num{{position:relative;z-index:2;font-size:56px;font-weight:950;color:#fff;line-height:1;text-shadow:0 4px 12px rgba(0,0,0,.55);}}
.hex-sub{{position:relative;z-index:2;font-size:20px;font-weight:800;letter-spacing:1.5px;color:rgba(255,255,255,.92);margin-top:8px;}}
.card{{flex:1;height:256px;background:rgba(22,30,48,.94);border:3px solid rgba(255,255,255,.14);border-radius:26px;padding:24px 30px;display:flex;flex-direction:column;justify-content:space-between;box-shadow:0 18px 40px rgba(0,0,0,.55);}}
.card-top{{display:flex;align-items:center;justify-content:space-between;gap:14px;background:#f8fafc;color:#0f172a;padding:12px 20px;border-radius:14px;}}
.card-title{{font-size:30px;font-weight:950;line-height:1.1;}}
.card-ico{{font-size:40px;line-height:1;}}
.card-desc{{font-size:25px;color:#cbd5e1;font-weight:600;line-height:1.35;margin-top:12px;}}
#bottom-fade{{position:absolute;bottom:0;left:0;right:0;height:230px;background:linear-gradient(0deg,rgba(10,14,24,.98) 45%,rgba(10,14,24,0));z-index:28;display:flex;align-items:flex-end;justify-content:center;padding-bottom:68px;}}
#cta-pill{{font-size:28px;font-weight:900;color:#facc15;letter-spacing:1px;padding:12px 28px;border-radius:999px;background:rgba(250,204,21,.14);border:2px solid rgba(250,204,21,.5);}}
#hook-cap{{position:absolute;top:760px;left:64px;right:64px;text-align:center;z-index:35;pointer-events:none;}}
.hc{{display:inline-block;font-size:58px;font-weight:950;color:#fff;background:rgba(10,14,24,.88);padding:20px 32px;border-radius:24px;border:3px solid #38bdf8;box-shadow:0 20px 60px rgba(0,0,0,.85);}}
#prog{{position:absolute;top:0;left:0;height:10px;background:linear-gradient(90deg,#ef4444,#38bdf8,#facc15);z-index:50;}}
</style></head>
<body>
<div id="stage">
  <div id="prog"></div>
  <div id="grid"></div>
  <div id="top-hud">
    <div id="top-title">HOW RARE IS YOUR BODY?</div>
    <div id="tier-row"><span id="tier-name" style="color:#f87171">TIER: COMMON</span><span id="rank-txt" style="color:#94a3b8">1 / 16</span></div>
    <div id="meter-track"><div id="meter-fill"></div></div>
  </div>
  <div id="viewport"><div id="belt"></div></div>
  <div id="hook-cap"></div>
  <div id="bottom-fade"><div id="cta-pill">COMMENT YOUR RAREST TRAIT 👇</div></div>
</div>
<script>
const TRAITS = {json.dumps(traits)};
const DUR = {dur:.3f};
const ROW_H = 324;

const belt = document.getElementById("belt");
const rowEls = TRAITS.map((tr, i) => {{
  const [stat, sub, title, desc, color, ico] = tr;
  const div = document.createElement("div");
  div.className = "row";
  div.innerHTML = `
    <div class="hex-wrap">
      <svg class="hex-svg" viewBox="0 0 240 240">
        <polygon points="120,8 222,64 222,176 120,232 18,176 18,64" fill="${{color}}" stroke="rgba(255,255,255,0.65)" stroke-width="6"/>
      </svg>
      <div class="hex-num" style="font-size:${{stat.length > 4 ? '44px' : '56px'}}">${{stat}}</div>
      <div class="hex-sub">${{sub}}</div>
    </div>
    <div class="card" style="border-color:${{color}}99">
      <div class="card-top"><div class="card-title">${{title}}</div><div class="card-ico">${{ico}}</div></div>
      <div class="card-desc">${{desc}}</div>
    </div>`;
  belt.appendChild(div);
  return div;
}});

window.renderFrame = function(t, f) {{
  const p = Math.min(1, t / DUR);
  document.getElementById("prog").style.width = (p * 100).toFixed(2) + "%";

  // Smooth continuous upward scroll from card 0 at bottom to card 15 centered at end (0.0% static frames!)
  const startY = 1280;
  const endY = -(TRAITS.length - 1) * ROW_H + 560;
  const scrollY = startY + (endY - startY) * p;
  belt.style.transform = `translateY(${{scrollY.toFixed(1)}}px)`;

  // Highlight & subtly scale whichever row is passing through the center focal zone
  let activeIdx = 0;
  let bestDist = 99999;
  for (let i = 0; i < rowEls.length; i++) {{
    const centerY = scrollY + i * ROW_H + 145;
    const dist = Math.abs(centerY - 680);
    if (dist < bestDist) {{ bestDist = dist; activeIdx = i; }}
    const focus = Math.max(0, 1 - dist / 620);
    const sc = 0.94 + 0.08 * focus;
    const op = 0.52 + 0.48 * focus;
    rowEls[i].style.transform = `scale(${{sc.toFixed(3)}})`;
    rowEls[i].style.opacity = op.toFixed(3);
  }}

  document.getElementById("rank-txt").textContent = `${{activeIdx + 1}} / ${{TRAITS.length}}`;
  document.getElementById("meter-fill").style.width = `${{Math.max(6, Math.round(((activeIdx + 1) / TRAITS.length) * 100))}}%`;
  const tierEl = document.getElementById("tier-name");
  if (activeIdx < 4) {{ tierEl.textContent = "TIER: COMMON"; tierEl.style.color = "#f87171"; }}
  else if (activeIdx < 8) {{ tierEl.textContent = "TIER: UNCOMMON"; tierEl.style.color = "#fb923c"; }}
  else if (activeIdx < 12) {{ tierEl.textContent = "TIER: RARE"; tierEl.style.color = "#38bdf8"; }}
  else if (activeIdx < 15) {{ tierEl.textContent = "TIER: ULTRA RARE"; tierEl.style.color = "#c084fc"; }}
  else {{ tierEl.textContent = "TIER: MYTHIC (1 IN 6M)"; tierEl.style.color = "#facc15"; }}

  // Show punchy opening spoken hook overlay for first 3.6s then vanish cleanly
  const hc = document.getElementById("hook-cap");
  if (t < 3.6) {{
    const op = t < 3.1 ? 1 : (3.6 - t) / 0.5;
    hc.style.opacity = op.toFixed(2);
    hc.innerHTML = `<div class="hc">Watch till the end to see<br/><span style="color:#facc15">HOW RARE YOU ARE</span></div>`;
  }} else {{
    hc.style.opacity = "0";
  }}
}};
window.__RENDER_READY__ = true;
</script>
</body></html>"""

    out_mp4 = OUT_DIR / "04_scale_comparison_pilot.mp4"
    render_html_video(html, master, out_mp4, dur, work_dir)
    return {**verify_pilot_metrics(out_mp4), "voice": voice_info["voice"], "wpm": voice_info["wpm"]}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cfg_path = Path(sys.argv[1])
    assets = json.loads(cfg_path.read_text(encoding="utf-8"))
    results = {}
    with tempfile.TemporaryDirectory() as td:
        wdir = Path(td)
        results["cat1_explainer"] = build_pilot_1_explainer(wdir)
        results["cat2_dark_history"] = build_pilot_2_dark_history(wdir, assets["ice"], assets["tunnel"])
        results["cat3_dark_psychology"] = build_pilot_3_psychology(wdir, assets["stare"], assets["chess"])
        results["cat4_scale_comparison"] = build_pilot_4_scale_comparison(wdir)

    report_path = OUT_DIR / "pilot_showdown_report.json"
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("\n=== ALL 4 PILOTS RENDERED & MEASURED ===")
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
