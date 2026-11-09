"""The record board of Endless runs: a small JSON file on the computer that runs the game.
One row per player name, the best score kept."""

import json
import os
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "local_data" / "records.json"  # local_data/ is git ignored
MAX_ROWS = 20
MAX_NAME = 24
MAX_SCORE = 10_000_000


def load_records(path: Path | None = None) -> list[dict]:
    """Return the record board, best first. A missing or damaged file gives an empty board."""
    try:
        rows = json.loads((path or DEFAULT_PATH).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(rows, list):
        return []
    good = [row for row in rows if isinstance(row, dict) and isinstance(row.get("name"), str)
            and type(row.get("best")) is int and 0 < row["best"] <= MAX_SCORE]
    return sorted(good, key=lambda row: row["best"], reverse=True)[:MAX_ROWS]


def top_score(path: Path | None = None) -> int | None:
    """Return the best score on the board, or None when it is empty."""
    rows = load_records(path)
    return rows[0]["best"] if rows else None


def clean_name(name: object) -> str:
    """Return a player name of at most MAX_NAME characters ("Player" when empty)."""
    return (str(name or "Player").strip()[:MAX_NAME]) or "Player"


def submit_record(name: object, score: int, sections: int, path: Path | None = None) -> str:
    """Add a run to the board (one row per name, the best kept) and return a message for the player."""
    path = path or DEFAULT_PATH
    if score <= 0:
        return "No points this run, so nothing was recorded."
    score, sections = min(int(score), MAX_SCORE), max(0, int(sections))
    name = clean_name(name)
    rows = load_records(path)
    mine = next((row for row in rows if row["name"].lower() == name.lower()), None)
    if mine is None:
        rows.append({"name": name, "best": score, "sections": sections})
    elif score > mine["best"]:
        mine.update(best=score, sections=sections)
    rows = sorted(rows, key=lambda row: row["best"], reverse=True)[:MAX_ROWS]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        os.replace(temporary, path)
    except OSError:
        return "Couldn't save to this computer's record board."
    return "Saved to this computer's record board."
