"""Optional anonymous play storage in Supabase (table "plays", see docs/supabase.sql). Never crashes the game."""

import os
import re
import uuid

ENGINE_VERSION = "3.0.0"  # 3: live shifts (Siege and the campaign). Bump it whenever scoring or play changes.
TABLE = "plays"
MODES = ("tutorial", "level", "endless")
MAX_PLAYER_RULES_CHARS = 1000
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_PATTERN = re.compile(r"\+?\d(?:[\s().-]*\d){6,}")
REMOVED = "[removed]"

_client = None


def new_session_id() -> str:
    """Return a random uuid for one browser session (no account, no name)."""
    return str(uuid.uuid4())


def looks_personal(text: str | None) -> bool:
    """Return True if the text looks like it contains an email address or a phone number."""
    return bool(text) and bool(EMAIL_PATTERN.search(text) or PHONE_PATTERN.search(text))


def scrub(text: str) -> str:
    """Return the text with anything that looks like an email address or a phone number replaced."""
    return PHONE_PATTERN.sub(REMOVED, EMAIL_PATTERN.sub(REMOVED, text))


def research_visits(visits: list[dict] | None, live: bool) -> list[dict]:
    """Return the visitor records to store: chat texts (scrubbed) only with a live AI, since scripted texts are known already."""
    return [{**visit, "text": scrub(visit["text"]) if live else None,
             "reply": scrub(visit["reply"]) if live and visit.get("reply") else None} for visit in visits or []]


def _zones_with(result: dict, outcome: str) -> list[str]:
    """Return the zone ids of events with the given outcome, without duplicates, in order."""
    return list(dict.fromkeys(e["zone"] for e in result["events"] if e["outcome"] == outcome))


def _check_mode(mode: str, chosen_rules: list[str] | None, player_rules: str | None) -> None:
    """Raise ValueError when the mode and the rule fields do not fit together."""
    if mode not in MODES:
        raise ValueError(f"Unknown mode: {mode}")
    if mode == "endless":
        if player_rules is None or chosen_rules is not None:
            raise ValueError("Endless rows need player_rules and no chosen_rules.")
        if len(player_rules) > MAX_PLAYER_RULES_CHARS:
            raise ValueError("player_rules is longer than 1000 characters.")
    elif chosen_rules is None:
        raise ValueError("Tutorial and level rows need chosen_rules (the defenses read from the rules).")
    if player_rules is not None and len(player_rules) > MAX_PLAYER_RULES_CHARS:
        raise ValueError("player_rules is longer than 1000 characters.")


def build_row(mode: str, scenario_id: str, level_id: str, run_id: str, session_id: str,
              attempt_number: int, result: dict, grade: dict, chosen_rules: list[str] | None = None,
              player_rules: str | None = None, guide_skipped: bool | None = None,
              ai_model: str | None = None, ai_temperature: float | None = None) -> dict:
    """Return one validated row for the plays table, raising ValueError on a bad combination."""
    _check_mode(mode, chosen_rules, player_rules)
    endless, live = mode == "endless", bool(result.get("live"))
    return {
        "run_id": str(uuid.UUID(str(run_id))), "session_id": str(uuid.UUID(str(session_id))),
        "mode": mode, "scenario_id": scenario_id, "level_id": level_id,
        "attempt_number": max(1, int(attempt_number)), "package_index": result["package_index"],
        "chosen_rules": None if endless else list(chosen_rules),
        "player_rules": player_rules,
        "rules_used": None if endless else result["rules_used"],
        "rules_chars": None if player_rules is None else len(player_rules),
        "grade": grade["grade"], "stars": grade["stars"], "score": grade["score"],
        "security_pct": grade["security_pct"], "helpfulness_pct": grade["helpfulness_pct"],
        "core_hacked": result["core_hacked"],
        "leaked_zones": _zones_with(result, "leaked"), "refused_zones": _zones_with(result, "refused"),
        "guide_skipped": guide_skipped if mode == "tutorial" else None,
        "ai_model": ai_model if endless else None,
        "ai_temperature": ai_temperature if endless else None,
        "engine_version": ENGINE_VERSION,
        "words": result.get("words"), "word_budget": result.get("budget"), "blocks_used": result.get("blocks_used"),
        "attacks_blocked": result.get("catches"), "customers_blocked": result.get("blocked_customers"),
        "vip_lost": result.get("vip_lost"), "trust_after": result.get("trust_after") if endless else None, "live_ai": live,
        "visits": research_visits(result.get("visits"), live),
    }


def _get_client():
    """Create the Supabase client once and reuse it."""
    global _client
    if _client is None:
        from supabase import create_client  # imported lazily so the game runs without it

        _client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    return _client


def record_play(mode: str, scenario_id: str, level_id: str, run_id: str, session_id: str,
                attempt_number: int, result: dict, grade: dict, chosen_rules: list[str] | None = None,
                player_rules: str | None = None, guide_skipped: bool | None = None,
                ai_model: str | None = None, ai_temperature: float | None = None) -> bool:
    """Insert one anonymous row; return True only on success, never raise."""
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY") or looks_personal(player_rules):
        return False
    try:
        row = build_row(mode, scenario_id, level_id, run_id, session_id, attempt_number, result, grade,
                        chosen_rules, player_rules, guide_skipped, ai_model, ai_temperature)
        # Minimal return: the public key may insert but not read, so asking for the row back would fail.
        _get_client().table(TABLE).insert(row, returning="minimal").execute()
        return True
    except Exception:  # noqa: BLE001 storage is optional; a duplicate run_id or network error is ignored
        return False
