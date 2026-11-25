"""Official YouTube Data API v3 Resumable Uploader (Zero Browser Prompts).

Uses official OAuth 2.0 credentials stored strictly OUTSIDE git
(~/.config/neon-agent-house/youtube_token.json). Once authorized once via
`./run_house.sh yt-auth`, every upload runs 100% hands-free from Python with
automatic token refresh, full SEO metadata, optional scheduled publishAt,
and optional auto-posted CTA comment.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from agent_house.config import HALL_ROOM_JSON, HALL_ROOM_MD
from agent_house.hall_room import promote_verified_short

# Scopes: youtube.upload (upload videos) + youtube.force-ssl (post CTA first comment)
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "neon-agent-house"
DEFAULT_CLIENT_SECRETS = Path(
    os.environ.get("YOUTUBE_CLIENT_SECRETS", str(DEFAULT_CONFIG_DIR / "client_secret.json"))
)
DEFAULT_TOKEN_PATH = Path(
    os.environ.get("YOUTUBE_TOKEN_PATH", str(DEFAULT_CONFIG_DIR / "youtube_token.json"))
)


def is_youtube_api_configured(
    *,
    token_path: Path = DEFAULT_TOKEN_PATH,
    client_secrets: Path = DEFAULT_CLIENT_SECRETS,
) -> dict[str, Any]:
    return {
        "client_secrets_path": str(client_secrets),
        "client_secrets_exists": client_secrets.is_file(),
        "token_path": str(token_path),
        "token_exists": token_path.is_file(),
        "ready_for_unattended_upload": token_path.is_file(),
    }


def authorize_youtube_oauth(
    *,
    client_secrets: Path = DEFAULT_CLIENT_SECRETS,
    token_path: Path = DEFAULT_TOKEN_PATH,
    port: int = 0,
) -> Path:
    """One-time local browser OAuth flow storing a refreshable token for unattended uploads."""
    if not client_secrets.is_file():
        raise FileNotFoundError(
            f"Missing Google OAuth Desktop client file at: {client_secrets}\n"
            "Setup (free, ~2 min once):\n"
            "  1. Open https://console.cloud.google.com/apis/library/youtube.googleapis.com and Enable YouTube Data API v3.\n"
            "  2. Go to APIs & Services -> Credentials -> Create Credentials -> OAuth client ID (Desktop app).\n"
            f"  3. Download the JSON file to: {client_secrets}\n"
            "  4. Run: ./run_house.sh yt-auth"
        )

    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), SCOPES)
    creds = flow.run_local_server(port=port, prompt="consent", access_type="offline")
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    os.chmod(token_path, 0o600)
    return token_path


def _load_credentials(token_path: Path = DEFAULT_TOKEN_PATH):
    if not token_path.is_file():
        raise FileNotFoundError(
            f"YouTube OAuth token not found at {token_path}. Run `./run_house.sh yt-auth` once to authorize unattended uploads."
        )
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json(), encoding="utf-8")
        os.chmod(token_path, 0o600)
    return creds


def upload_short_via_api(
    metadata_or_dir: Path | dict[str, Any],
    *,
    privacy_status: str = "public",
    publish_at_iso: str | None = None,
    post_cta_comment: bool = True,
    token_path: Path = DEFAULT_TOKEN_PATH,
    hall_room_json: Path = HALL_ROOM_JSON,
    hall_room_md: Path = HALL_ROOM_MD,
) -> dict[str, Any]:
    """Upload a QA-verified Short directly via YouTube Data API v3 with full SEO metadata."""
    if isinstance(metadata_or_dir, Path):
        meta_path = (
            metadata_or_dir / "upload_metadata.json"
            if metadata_or_dir.is_dir()
            else metadata_or_dir
        )
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        metadata = dict(metadata_or_dir)

    video_path = Path(metadata["video_path"])
    if not video_path.is_file():
        raise FileNotFoundError(f"Rendered Short MP4 not found: {video_path}")

    creds = _load_credentials(token_path)
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    youtube = build("youtube", "v3", credentials=creds)

    status_body: dict[str, Any] = {
        "privacyStatus": "private" if publish_at_iso else privacy_status,
        "selfDeclaredMadeForKids": bool(metadata.get("made_for_kids", False)),
    }
    if publish_at_iso:
        status_body["publishAt"] = publish_at_iso

    body = {
        "snippet": {
            "title": metadata["title"][:100],
            "description": metadata["description"][:5000],
            "tags": metadata.get("tags", []),
            "categoryId": str(metadata.get("category_id", "28")),
            "defaultLanguage": metadata.get("default_language", "en"),
            "defaultAudioLanguage": metadata.get("default_audio_language", "en"),
        },
        "status": status_body,
    }

    media = MediaFileUpload(str(video_path), mimetype="video/mp4", chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _, response = request.next_chunk()

    video_id = response["id"]
    youtube_url = f"https://youtube.com/shorts/{video_id}"

    # Auto-post the CTA first comment for immediate clickable conversion
    comment_posted = False
    comment_error = None
    pinned_text = (metadata.get("pinned_comment") or "").strip()
    if post_cta_comment and pinned_text and privacy_status == "public" and not publish_at_iso:
        try:
            youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {"snippet": {"textOriginal": pinned_text}},
                    }
                },
            ).execute()
            comment_posted = True
        except Exception as exc:
            comment_error = str(exc)

    # Atomically update Hall Room with live YouTube URL
    if metadata.get("short_id"):
        promote_verified_short(
            caller="yt-video-verifier",
            entry={
                "short_id": metadata["short_id"],
                "status": "PUBLISHED_YOUTUBE" if not publish_at_iso else "SCHEDULED_YOUTUBE",
                "youtube_video_id": video_id,
                "youtube_url": youtube_url,
            },
            json_path=hall_room_json,
            md_path=hall_room_md,
        )

    return {
        "status": "UPLOADED",
        "video_id": video_id,
        "youtube_url": youtube_url,
        "privacy_status": status_body["privacyStatus"],
        "publish_at": publish_at_iso,
        "cta_comment_posted": comment_posted,
        "cta_comment_error": comment_error,
    }
