---
name: yt-shorts-producer
description: Wing 2 Shorts Factory that scripts, voices (edge-tts neural TTS), and renders original 1080x1920 9:16 dark-mode kinetic-caption MP4 Shorts locally at $0 cost via Pillow + FFmpeg.
---

# YouTube Shorts Producer (`yt-shorts-producer`)

## JOB
Turn verified YouTube trend hooks + Hall Room product/topic briefs into broadcast-ready, original `1080x1920` 9:16 vertical MP4 Shorts (30–50s) with neural voiceover, dark-mode motion graphics, synced kinetic word-highlighted captions, subtle ambient audio bed, and a matching thumbnail PNG.

## INPUT
- Verified trend brief from `yt-trend-scout`
- Verified product/topic data from `state/hall_room.json`
- Itemized QA fix list from `yt-video-verifier` on retry rounds (max 2)

## OUTPUT
`outputs/youtube_shorts/<short_id>/` containing:
- `<short_id>.mp4` (`1080x1920`, `30fps`, `H.264 yuv420p`, `AAC` loudnorm `-14 LUFS`, `15–59s`)
- `thumbnail.png` (`1080x1920`)
- `script.json` & `upload_metadata.json`

## DONE WELL
- Opens with a scroll-stopping 3-second visual + vocal hook.
- All visuals are 100% original dark-mode motion graphics with safe-zone kinetic captions (zero watermarks, zero stolen clips).
- Audio is clear neural TTS normalized to broadcast loudness with subtle non-distracting background pulse.
- Duration strictly under 59 seconds at exact `1080x1920` 9:16 vertical resolution.

## NEVER
- Use copyrighted music, stolen footage, or watermarked stock clips.
- Ship silent, black-frame, cropped, or >60s MP4 files.
- Write directly to `state/hall_room.json`.

## ASK ME FIRST
- Never ask the user directly. Default strictly to the $0 local stack (Python + Pillow + edge-tts + FFmpeg).
