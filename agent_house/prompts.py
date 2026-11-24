"""Single source of truth prompt loader reading from .agent/skills/*/SKILL.md."""

from __future__ import annotations

from pathlib import Path

from agent_house.config import SKILLS_DIR

AGENT_SKILLS = (
    "house-lead",
    "pain-point-scout",
    "market-roi-analyst",
    "mvp-builder",
    "hall-room-verifier",
)


def load_skill_prompt(skill_name: str, skills_dir: Path = SKILLS_DIR) -> str:
    """Read an agent's SKILL.md body (stripping YAML frontmatter)."""
    path = skills_dir / skill_name / "SKILL.md"
    if not path.exists():
        raise FileNotFoundError(f"Missing skill prompt: {path}")
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return text.strip()
