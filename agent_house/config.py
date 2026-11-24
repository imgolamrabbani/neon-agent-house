"""Configuration for Neon Agent House.

API keys are read strictly from environment variables and never hardcoded.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT_DIR / ".agent" / "skills"
STATE_DIR = ROOT_DIR / "state"
HALL_ROOM_JSON = STATE_DIR / "hall_room.json"
HALL_ROOM_MD = STATE_DIR / "hall_room.md"
MEMORY_MD = STATE_DIR / "memory.md"
RUNS_JSONL = STATE_DIR / "runs.jsonl"
WEEKLY_REVIEWS_DIR = STATE_DIR / "weekly_reviews"
MVP_ROOT_DIR = ROOT_DIR / "mvp_bundle"

# Exact Gemini 4 Neon model ID verified from ai.google.dev/gemini-api/docs/models
DEFAULT_MODEL_ID = os.environ.get("AGENT_HOUSE_MODEL", "gemini-4-neon")
MAX_QUALITY_ROUNDS = 2
MIN_PASS_SCORE = 85


def get_gemini_api_key() -> str | None:
    """Return Gemini API key from environment without logging or caching."""
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
