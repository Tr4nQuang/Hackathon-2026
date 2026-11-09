"""Local files: the record board (kept on the computer that runs the game) and level progress export."""

import json
import os
from pathlib import Path

RECORDS_PATH = Path(__file__).resolve().parent.parent / "data" / "records.json"  # data/ is git ignored
MAX_ROWS = 20
MAX_NAME = 24
MAX_SCORE = 10_000_000
LEVEL_IDS_KEY = "tutorial"


def load_records() -> list[dict]:
    """Return the record board, best first. A missing or damaged file gives an empty board."""
    try:
        rows = json.loads(RECORDS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    good = [row for row in rows if isinstance(row, dict) and isinstance(row.get("name"), str)
            and isinstance(row.get("best"), int) and 0 < row["best"] <= MAX_SCORE]
    return sorted(good, key=lambda row: row["best"], reverse=True)[:MAX_ROWS]


def top_score() -> int | None:
    """Return the best score on the board, or None when it is empty."""
    rows = load_records()
    return rows[0]["best"] if rows else None


def submit_record(name: str, score: int, sections: int) -> str:
    """Add a run to the record board (one row per name, the best kept) and return a message for the player."""
    if score <= 0:
        return "No points this run, so nothing was recorded."
    name = (name or "Player").strip()[:MAX_NAME] or "Player"
    rows = load_records()
    mine = next((row for row in rows if row["name"].lower() == name.lower()), None)
    if mine is None:
        rows.append({"name": name, "best": score, "sections": sections})
    elif score > mine["best"]:
        mine.update(best=score, sections=sections)
    rows = sorted(rows, key=lambda row: row["best"], reverse=True)[:MAX_ROWS]
    try:
        RECORDS_PATH.parent.mkdir(parents=True, exist_ok=True)
        temporary = RECORDS_PATH.with_suffix(".tmp")
        temporary.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        os.replace(temporary, RECORDS_PATH)
    except OSError:
        return "Couldn't save to this computer's record board."
    return "Saved to this computer's record board."


def progress_to_json(progress: dict) -> str:
    """Return level progress as JSON text for the player to keep."""
    return json.dumps({"format": "chatbot-defense-arena/progress-1", "progress": progress}, indent=2)


def progress_from_json(text: str, level_ids: list[str]) -> dict:
    """Read progress JSON, raising ValueError when it is not a progress file or has values out of range."""
    try:
        data = json.loads(text)
    except ValueError as error:
        raise ValueError("This file is not valid JSON.") from error
    if not isinstance(data, dict) or data.get("format") != "chatbot-defense-arena/progress-1" or not isinstance(data.get("progress"), dict):
        raise ValueError("This file is not a progress file of this game.")
    progress = {}
    for key, row in data["progress"].items():
        if key not in [LEVEL_IDS_KEY, *level_ids] or not isinstance(row, dict):
            continue
        stars, best = row.get("stars"), row.get("best")
        if not (isinstance(stars, int) and 0 <= stars <= 3 and isinstance(best, int) and 0 <= best <= MAX_SCORE):
            raise ValueError("This progress file has values that do not fit this game.")
        progress[key] = {"stars": stars, "best": best, "perfect": bool(row.get("perfect"))}
    return progress


def merge_progress(current: dict, loaded: dict) -> dict:
    """Return both sets of level progress together, keeping the better stars, score and Perfect of each level."""
    merged = {key: dict(row) for key, row in current.items()}
    for key, row in loaded.items():
        mine = merged.get(key)
        merged[key] = dict(row) if mine is None else {"stars": max(mine["stars"], row["stars"]), "best": max(mine["best"], row["best"]),
                                                        "perfect": mine["perfect"] or row["perfect"]}
    return merged
