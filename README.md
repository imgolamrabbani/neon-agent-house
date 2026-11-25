# Neon Agent House v5 — Multi-Wing Autonomous Product + YouTube Shorts Engine

A **Multi-Wing Autonomous Agent House** built on **Google ADK 2.x** (`google-adk>=2.15.0`) and **Gemini 4 Neon** (`gemini-4-neon`), with **9 Antigravity skills**, shared write-locked **Hall Room** (`state/hall_room.json` & `state/hall_room.md`), adversarial max-2-round Verifier loops, and scheduled self-improvement.

## Two Autonomous Wings Sharing One Hall Room
- **Wing 1 — Digital Products House (`agent_house/graph.py` & `continuous.py`):** Parallel buyer-pain + competitor-pricing discovery → quote-in-live-page Verifier → runnable Python stdlib + dark-mode HTML MVP + ZIP packaging → Gumroad & GitHub Pages storefront (`5/5` verified products + `$19` All-5 Bundle live).
- **Wing 2 — YouTube Automation House (`agent_house/youtube_graph.py` & `youtube_tools.py`):** Live `yt-dlp` YouTube trend "doomscroll" → parallel Hall Room product hook mapping → neural TTS (`edge-tts`) + `1080×1920` 30fps dark-mode kinetic-caption MP4 renderer (`Pillow` + `FFmpeg`) → adversarial `ffprobe`/`volumedetect`/frame-variance Video Verifier → SEO upload package.

## Install & Run in 3 Steps

1. **Create a virtual environment and install dependencies:**
   ```bash
   uv venv --python 3.12 .venv
   uv pip install --python .venv/bin/python -e ".[dev]"
   ```
2. **Set your Gemini API key in your shell (only needed for standalone live LLM runs outside Antigravity):**
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"
   ```
3. **Run either Wing with one command:**
   ```bash
   # Wing 1: Continuous multi-niche product portfolio
   ./run_house.sh continuous --max-new 3

   # Wing 2: Doomscroll YouTube + render & QA-verify a 1080x1920 Short
   ./run_house.sh youtube --niche-id invoice-pulse-01 --short-id yt-short-01

   # Weekly self-improvement audit
   ./run_house.sh weekly
   ```
