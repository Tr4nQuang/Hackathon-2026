"""Adapter between the interface and the engine, the only file in ui/ that imports engine/."""

import os

from engine.ai import GEMINI_MODEL
from engine import records as board
from engine.arena import content, endless, grade, live, play, rules
from engine.endless import MAX_RULES_CHARS
from engine.storage import new_session_id, record_play

__all__ = [
    "MAX_RULES_CHARS", "board", "content", "endless", "grade", "live", "new_session_id",
    "play", "record_play", "rules", "ai_settings", "get_guide_steps", "storage_configured", "storage_grade", "storage_result",
]

GRADE_FOR_STORAGE = {"perfect": "perfect", "s1": "stars", "s2": "stars", "s3": "stars", "fail": "fail", "breach": "lose"}


def ai_settings() -> tuple[str, float]:
    """Return the model name and temperature stored with an Endless run ("fake-ai" in fake mode)."""
    fake = os.getenv("USE_FAKE_AI", "true").strip().lower() == "true"
    return ("fake-ai" if fake else GEMINI_MODEL), live.REPLY_TEMPERATURE


def storage_configured() -> bool:
    """Return True when anonymous result storage is set up (both values exist; neither is ever shown)."""
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"))


def get_guide_steps(level: dict) -> list[dict]:
    """Return the tutorial guide steps of a level, or [] when it has none."""
    return level.get("guide_steps", [])


def storage_grade(result: dict) -> dict:
    """Return a grade in the shape engine.storage expects: grade, stars, score and both percentages."""
    grade_info = result["grade"]
    return {"grade": GRADE_FOR_STORAGE[grade_info["key"]], "stars": grade_info["stars"],
            "score": max(0, min(100, grade_info["overall"])), "security_pct": grade_info["sec"],
            "helpfulness_pct": grade_info["help"]}


def storage_result(result: dict) -> dict:
    """Return a result in the shape engine.storage expects: which zones leaked or turned a customer away, no text."""
    tally = result["tally"]
    events = [{"zone": zone, "outcome": "leaked"} for zone in tally["breached"]]
    events += [{"zone": zone, "outcome": "refused"} for zone in tally["refused_topics"]]
    return {"events": events, "package_index": result.get("package", 0), "rules_used": len(result.get("selected", [])),
            "core_hacked": tally["core_breached"]}
