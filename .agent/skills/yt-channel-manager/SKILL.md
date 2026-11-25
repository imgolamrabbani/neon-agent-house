---
name: yt-channel-manager
description: Wing 2 Channel Manager & Hands-Free YouTube Data API v3 Uploader. Applies 100/100 YouTube Shorts SEO and auto-uploads QA-passed Shorts without asking permission once OAuth is authorized.
---

# YouTube Channel Manager (`yt-channel-manager`)

## JOB
Apply outstanding YouTube Shorts SEO (`agent_house/youtube_seo.py`: mobile-first high-CTR title, above-the-fold CTA links, semantic keyword description, timestamped chapters, 3–5 focused hashtags, <=500-char API tag list, Science & Tech category 28) and **automatically upload** ONLY `yt-video-verifier`-approved Shorts from `state/hall_room.json` via the official **YouTube Data API v3** (`agent_house/youtube_uploader.py`).

## INPUT
- Verified Short record from `state/hall_room.json` (`verified_youtube_shorts[]`)
- `upload_metadata.json` and QA-passed `.mp4`

## OUTPUT
- Live uploaded YouTube Shorts URL (`https://youtube.com/shorts/<id>`) + auto-posted CTA first comment, logged to `state/hall_room.json`, `state/hall_room.md`, and `state/runs.jsonl`.

## DONE WELL
- SEO audit score equals `100/100` before upload.
- Uploads ONLY `yt-video-verifier`-approved Shorts automatically with zero permission prompts (standing always-allowed user directive).
- Respects safe channel cadence (1–3 high-quality original Shorts per day).

## NEVER
- Ask the user for permission before uploading a QA-passed Short (always allowed by standing user directive).
- Commit `client_secret.json` or `youtube_token.json` into git.
- Upload any MP4 that failed `yt-video-verifier`.

## ASK ME FIRST
- Never ask permission to upload verified Shorts.
- Only surface a clear 1-time setup pointer if `~/.config/neon-agent-house/youtube_token.json` has not yet been authorized via `./run_house.sh yt-auth`.
