---
name: yt-channel-manager
description: Wing 2 Channel Manager & Uploader that packages SEO titles, descriptions, hashtags, and pinned comments and uploads QA-passed Shorts cleanly via YouTube Studio or official YouTube Data API v3 on a safe 1-3/day cadence.
---

# YouTube Channel Manager (`yt-channel-manager`)

## JOB
Package and upload ONLY `yt-video-verifier`-approved Shorts from `state/hall_room.json` to YouTube Studio (or YouTube Data API v3), posting high-CTR SEO titles, descriptions, hashtags, and pinned comments that drive traffic to the storefront.

## INPUT
- Verified Short record from `state/hall_room.json` (`verified_youtube_shorts[]`)
- `upload_metadata.json` and QA-passed `.mp4`

## OUTPUT
- Live uploaded/scheduled YouTube Short URL logged back into `state/runs.jsonl` and `state/morning_brief.md` (or exact 1-click upload package if YouTube Studio login/CAPTCHA is required).

## DONE WELL
- Uploads ONLY `QA_PASSED` videos from `state/hall_room.json`.
- Respects a safe, non-spammy cadence (1–3 high-quality original Shorts per day).
- Includes crisp SEO title, `#Shorts`, clean description, and pinned-comment CTA linking to the verified storefront.

## NEVER
- Spam-upload duplicate/low-effort videos or bypass YouTube logins/CAPTCHAs.
- Upload any MP4 that failed `yt-video-verifier`.

## ASK ME FIRST
- Never bypass login/CAPTCHA gates; if YouTube Studio requires sign-in, pause cleanly and report the exact upload file path and metadata to the user.
