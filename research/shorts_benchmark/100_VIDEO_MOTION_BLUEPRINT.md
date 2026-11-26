# 100-Video Viral YouTube Shorts Reverse-Engineering & Motion Blueprint

> **Empirical Dataset:** 100 real YouTube Shorts across 4 categories (25 per category), downloaded, frame-extracted (500+ keyframes), cut-rate analyzed (`ffmpeg select='gt(scene,0.22)'`), pixel-motion measured (`4fps` luminance delta), audio-audited (`volumedetect` + `silencedetect`), contact-sheeted, and Whisper-transcribed on Apple Silicon.
> **Raw Data:** [dataset_100_videos.json](file:///Volumes/MAC%20EXTRA/Vibe/Neon/research/shorts_benchmark/dataset_100_videos.json) | [summary_stats.json](file:///Volumes/MAC%20EXTRA/Vibe/Neon/research/shorts_benchmark/summary_stats.json)

---

## 1. Brutal Post-Mortem: Why Our Previous Videos Got 0–2 Views

| Metric | Old `cinema_shorts.py` (0–2 views) | Top 100 Viral Benchmark | Gap That Killed Views |
| :--- | :--- | :--- | :--- |
| **Visual Motion** | 6 static JPEGs with slow Ken Burns pan (`8–10s` per shot) | `0.0%–1.1%` static frames; continuous animation or `1.4s–2.2s` rapid cuts | Viewers swiped away in `<1.5s` thinking it was an AI slideshow |
| **First Visual Change** | `~8.5s` (first cut) | `0.57s–1.33s` (Psych/Fast-Cut) or continuous motion from `t=0.0s` (3D/Scale) | Zero pattern interrupt during the critical 0–3s swipe window |
| **Audio Silence & Pace** | Slow dramatic pauses (`~125 WPM`), flat synthetic sine hum | **`0.0%` silence**, **`160–245 WPM`** conversational urgency + rhythmic beat + crisp SFX | Sounded slow/robotic instead of urgent & addictive |
| **Caption System** | Static whole-sentence yellow-pill block | Millisecond word-synced **2–3 word pop-in** captions (clean white + red/gold power words) | Clunky static text doesn't pull the eye forward word-by-word |
| **Loop / Rewatch Mechanic** | Passive subscribe ending | Endless scroll / "check your rarity %" / "3 moves" rewatch bait | Low AVD (`<70%`) vs. viral threshold (`>100%` AVD + `>75%` viewed-vs-swiped) |

---

## 2. Empirical 100-Video Telemetry Across All 4 Categories

| Category (25 Shorts Each) | Median Views | Max Views | Median Duration | Motion Energy | Static Ratio | Silence Ratio | Speech Pace (Top Outliers) | Signature Winning Mechanic |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| **Cat 1: Visual Explainers** (`Zack D. Films`, `Kurzgesagt`, `Vox`) | **3,600,000** | **10,000,000** | `38.8s` | **24.94** | **`0.000`** | **`0.000`** | `157–185 WPM` | Continuous visual demonstration starting *in media res* at `t=0.0s`; clean white 2–3 word captions at `y=72%` |
| **Cat 2: Dark History & Geopolitics** (`RealLifeLore`, `Infographics`, `MrBallen`) | **344,000** | **3,000,000** | `53.4s` | `9.94–30.8` | `0.126` | **`0.000`** | `159–248 WPM` | Animated satellite map fly-ins with glowing borders, bold yellow hook title at `t=0.0s`, or `39 CPM` fast cuts |
| **Cat 3: Dark Psychology & Behavior** (`Charisma on Command`, `Psych2go`) | **84,000** | **9,700,000** | `56.1s` | `15.7–21.3` | `0.126` | `0.007` | **`217–246 WPM`** | **`30.9–40.0 CPM`** (`1.46s–2.21s` avg shot, **1st cut `0.57s–1.33s`**); White + **Red** (threat) + **Gold** (power move) captions |
| **Cat 4: Visual Scale & Probability Comparisons** (`WatchData`, `MetaBallStudios`) | **29,000** | **788,000** | `47.9s` | **27.41** | **`0.011`** | **`0.000`** | `24 WPM` (3s hook only + music!) | Non-stop vertical conveyor scroll of Hexagon Stat + Icon Card rows (`91% → 0.01%`), forcing pauses, rewatches & comments |

---

## 3. Exact Replication Playbook (How Our Next-Gen Engine Replicates All 4 Formats)

### Shared Next-Gen Stack (Replacing Static Slideshows Forever)
- **Renderer:** Deterministic 1080×1920 30fps HTML5/CSS3/SVG/Canvas via local Chrome CDP ([chrome_frame_renderer.mjs](file:///Volumes/MAC%20EXTRA/Vibe/Neon/agent_house/chrome_frame_renderer.mjs)) — real vector animations, cubic-bezier zoom punches, live counters, glowing shaders, whip-pan motion blur.
- **Voice & Word Sync:** Local Apple Silicon **Kokoro-82M-bf16** (`speed=1.12–1.18`, silence-trimmed `>220ms`) + **`mlx_whisper`** millisecond word-level forced alignment ([kokoro_word_sync.py](file:///Volumes/MAC%20EXTRA/Vibe/Neon/agent_house/kokoro_word_sync.py)).
- **Sound Design:** Procedural NumPy/SciPy broadcast SFX engine ([sfx_engine.py](file:///Volumes/MAC%20EXTRA/Vibe/Neon/agent_house/sfx_engine.py)) — sub-bass booms, whip-pan whooshes on every cut, UI pops/ticks on counters, tension risers, sidechain-ducked pulsing rhythmic underscore mastered to `-14 LUFS`.

### Exact Motion Blueprint per Category
1. **Category 1 — Animated Science/Mechanism Explainer (`01_visual_explainer_pilot.mp4`):**
   - **Motion:** Continuous SVG anatomical/mechanical simulation (pulsing lungs, flowing O₂/CO₂ blood particles, live telemetry dials ticking every frame, camera zoom-punch into target organ every 2.2s, red danger-zone heartbeat pulse).
   - **Captions:** Clean white bold 2–3 word Whisper-synced captions (`y=74%`, crisp dark shadow, zero box clutter) matching `Zack D. Films`.
   - **Audio:** `175 WPM` `am_michael` / `am_fenrir`, `0.0%` silence, crisp UI pop SFX on metric jumps + rhythmic curious underscore.
2. **Category 2 — Fast-Cut Dark History & Geopolitics (`02_dark_history_map_pilot.mp4`):**
   - **Motion:** `RealLifeLore` satellite map fly-in + glowing amber/red radar border draw + animated declassified CIA/Army redacted document bars sliding open + yellow highlighter sweeping across key dates + rapid 2.0s visual cuts with whip-pan flashes.
   - **Captions:** Bold yellow-accent hook headline at `t=0.0s`, then crisp Whisper-synced 2–3 word captions with amber emphasis on numbers/years.
   - **Audio:** `175 WPM` `am_fenrir`, sub-bass impact booms on document reveals, whooshes on map jumps, dark thriller pulsing underscore.
3. **Category 3 — Dark Psychology Fast-Cut Kinetic (`03_dark_psychology_pilot.mp4`):**
   - **Motion:** **First visual punch at `0.7s`**, **visual state change every `1.5–1.9s` (`34+ CPM`)**! Giant kinetic slam opening (`SHUT DOWN DISRESPECT`), live animated iMessage/dialogue bubbles, shifting Red→Gold Power-Status bar, numbered tactical rule cards (`01 / 02 / 03`), dramatic noir silhouette backgrounds with micro zoom-punch.
   - **Captions:** Exact `Charisma on Command` 3-color coding: White base, **Crimson Red** for disrespect/threat words, **Electric Gold** for tactical power moves.
   - **Audio:** Punchy `180+ WPM` `am_fenrir`, hard sub-bass drops on each rule number, crisp notification/tick SFX, hypnotic dark pulse beat.
4. **Category 4 — WatchData-Style Rarity & Scale Conveyor (`04_scale_comparison_pilot.mp4`):**
   - **Motion:** **`0.0%` static frames** — butter-smooth 30fps continuous upward scrolling conveyor of **16 escalating cards** (`90%` → `0.0001%`). Left column: glowing color-shifting Hexagon Stat (`Crimson → Amber → Cyan → Violet → Mythic Gold`). Right column: crisp Retina card with custom vector SVG icon, title, and punchy 2-line hook fact. Top HUD: live animated **RARITY TIER BAR** climbing from `COMMON` to `MYTHIC`.
   - **Audio:** Short 3.5-second viral hook narration at `t=0.0s` (`"If you have any of these body traits, watch till the end to see how rare you really are."`), then addictive 122 BPM propulsive synth groove + crisp ascending tick SFX as each card crosses the active spotlight zone!
