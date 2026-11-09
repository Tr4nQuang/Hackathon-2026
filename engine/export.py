"""The Endless run file a player sends to the admin: one CSV row per section played.

Why CSV: the admin can open it in Excel or Google Sheets without any tool, many files merge by simple stacking
(tools/merge_runs.py does it), and a section is a flat record. The file is UTF-8 with a byte order mark so Excel
reads accents correctly. It holds no name. Anything in the rules that looks like an email address or a phone number is
replaced by [removed], and cells that a spreadsheet would run as a formula are made harmless.
"""

import csv
import io
import re
from datetime import datetime, timezone

from engine.storage import REMOVED, scrub

FORMAT_VERSION = 2  # 2: Siege (word budget, your blocks, trust)
BOM = "﻿"
FORMULA_START = ("=", "+", "-", "@", "\t", "\r")
COLUMNS = (
    "format", "run_id", "session_id", "played_at", "section", "business", "grade", "points", "security_pct", "helpfulness_pct",
    "overall_pct", "words", "rules_chars", "rules_text", "rules_redacted", "leaked_zones", "refused_zones", "leaks",
    "customers_turned_away", "secret_points_kept", "secret_points_at_stake", "public_points_served", "public_points_asked",
    "core_breached", "ai_mode", "ai_model", "run_score_after", "word_budget", "blocks_used", "attacks_blocked_by_you",
    "customers_blocked_by_you", "trust_after",
)


def redact(text: str) -> tuple[str, bool]:
    """Return the text with email addresses and phone numbers replaced, and whether anything was replaced."""
    cleaned = scrub(text)
    return cleaned, cleaned != text


def safe_cell(value: object) -> object:
    """Return a cell a spreadsheet will show as text: a leading = + - @ (or tab or return) gets an apostrophe in front."""
    if isinstance(value, str) and value.startswith(FORMULA_START):
        return "'" + value
    return value


def section_row(result: dict, run_id: str, session_id: str, run_score_after: int, ai_model: str, when: datetime | None = None,
                trust_after: int = 0) -> dict:
    """Return the file row of one played Endless section, from the engine's result of that section."""
    rules, redacted = redact(result["rules"])
    tally, score, grade = result["tally"], result["score"], result["grade"]
    live = bool(result["live"])
    return {
        "format": FORMAT_VERSION, "run_id": run_id, "session_id": session_id,
        "played_at": (when or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"), "section": result["section"],
        "business": result["world_id"], "grade": grade["key"], "points": result["points"], "security_pct": grade["sec"],
        "helpfulness_pct": grade["help"], "overall_pct": grade["overall"], "words": result["words"], "rules_chars": len(result["rules"]),
        "rules_text": rules, "rules_redacted": redacted, "leaked_zones": ";".join(tally["breached"]),
        "refused_zones": ";".join(tally["refused_topics"]), "leaks": len(tally["leaks"]), "customers_turned_away": len(tally["refused"]),
        "secret_points_kept": score["kept"], "secret_points_at_stake": score["at_stake"], "public_points_served": score["served"],
        "public_points_asked": score["asked"], "core_breached": bool(tally["core_breached"]),
        "ai_mode": "live" if live else "simulated", "ai_model": ai_model if live else "built-in scripts", "run_score_after": run_score_after,
        "word_budget": result.get("budget", 0), "blocks_used": result.get("blocks_used", 0), "attacks_blocked_by_you": result.get("catches", 0),
        "customers_blocked_by_you": result.get("blocked_customers", 0), "trust_after": trust_after,
    }


def row_ok(row: object) -> bool:
    """Return True when a row has exactly the file's columns with plain values (used on rows read back from the browser)."""
    return (isinstance(row, dict) and set(row) == set(COLUMNS)
            and all(type(value) in (str, int, bool) and (type(value) is not str or len(value) <= 1200) for value in row.values()))


def csv_text(rows: list[dict]) -> str:
    """Return the file text for rows: a byte order mark, the header and one line per row. Raises ValueError for a bad row."""
    if not all(row_ok(row) for row in rows):
        raise ValueError("a row does not match the run file format")
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator="\r\n")
    writer.writeheader()
    writer.writerows({name: safe_cell(row[name]) for name in COLUMNS} for row in rows)
    return BOM + out.getvalue()


def read_rows(text: str) -> list[dict]:
    """Read the rows of a run file (as csv_text wrote them, or merged). Raises ValueError if the header is not this format."""
    reader = csv.DictReader(io.StringIO(text.lstrip(BOM), newline=""))
    if tuple(reader.fieldnames or ()) != COLUMNS:
        raise ValueError("this is not a Chatbot Defense Arena run file")
    return list(reader)


def file_name(run_id: str, when: datetime | None = None) -> str:
    """Return a file name for a run: the date and the first characters of its id."""
    stamp = (when or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M")
    return f"chatbot-defense-run-{stamp}-{re.sub(r'[^0-9a-f]', '', run_id)[:8]}.csv"
