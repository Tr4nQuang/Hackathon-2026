"""Save my game and Load my game: a finished round as a JSON file on the player's computer, replay only."""

import uuid

import streamlit as st

from ui import common, data
from ui.map import STATES

MAX_ENTRIES = 600
MAX_TEXT = 3000
SCORE_KEYS = ("at_stake", "kept", "lost", "asked", "served")
ENTRY_TYPES = ("sys", "msg", "judge")
ROLES = ("attacker", "customer", "bot")
JUDGE_CLASSES = ("good", "bad", "warn")
LOADED_NOTICE = "This is a replay of a saved game. Loaded games are not graded again and are never stored."


def save_record(result: dict, level: dict | None = None) -> dict:
    """Return what Save my game writes: the rules, the grade and every entry of the round, enough to replay it."""
    return {"scenario_id": "arena", "mode": "level" if level else "endless", "level_id": level["id"] if level else "endless",
            "world_id": result["world_id"], "chosen_rules": result.get("selected"), "player_rules": result.get("rules"),
            "package": result.get("package"), "events": result["log"], "tally": result["tally"], "score": result["score"],
            "grade": result["grade"]}


def _text_ok(value: object) -> bool:
    """Return True for a short string."""
    return isinstance(value, str) and len(value) <= MAX_TEXT


def _entry_ok(entry: object) -> bool:
    """Return True when a log entry has everything the replay needs, with safe types."""
    if not isinstance(entry, dict) or entry.get("type") not in ENTRY_TYPES or not _text_ok(entry.get("text")):
        return False
    if entry["type"] == "msg" and (entry.get("role") not in ROLES or not _text_ok(entry.get("name"))
                                   or not _text_ok(entry.get("tag", ""))):
        return False
    if entry["type"] == "judge" and (entry.get("cls") not in JUDGE_CLASSES or not _text_ok(entry.get("fn"))):
        return False
    state, score = entry.get("map"), entry.get("score")
    if not isinstance(state, dict) or not all(isinstance(k, str) and v in STATES for k, v in state.items()):
        return False
    return isinstance(score, dict) and all(isinstance(score.get(key), int) for key in SCORE_KEYS)


def check_log(log: object) -> list[dict]:
    """Return the log of a save, raising ValueError if it is missing, too long or malformed."""
    if not isinstance(log, list) or not log:
        raise ValueError("This save has no messages to replay.")
    if len(log) > MAX_ENTRIES or not all(_entry_ok(entry) for entry in log):
        raise ValueError("This save has malformed messages.")
    return log


def replay_from_save(record: dict) -> dict:
    """Return the log and world of a parsed save, raising ValueError if it does not fit this game."""
    log = check_log(record.get("events"))
    try:
        world = data.content.get_world(str(record.get("world_id", "")))
    except ValueError as error:
        raise ValueError("This save is for a business that is not in this game.") from error
    sector_ids = {sector["id"] for sector in world["sectors"]}
    if not all(set(entry["map"]) <= sector_ids for entry in log):
        raise ValueError("This save does not match its business.")
    return {"log": log, "world_id": world["id"]}


def load_game(key: str) -> None:
    """Read the uploaded save file and start its replay; show a message if it is not usable."""
    state = st.session_state
    uploaded = state.get(key)
    if uploaded is None:
        return
    try:
        loaded = replay_from_save(data.import_game(uploaded.getvalue().decode("utf-8")))
    except (ValueError, UnicodeDecodeError) as error:
        state["load_error"] = str(error)
        return
    state.pop("load_error", None)
    state.update(replay_log=loaded["log"], replay_world=loaded["world_id"], replay_back="home", replay_loaded=True)
    common.start_playback()
    common.goto("replay")


def load_game_widget(key: str) -> None:
    """Show the Load my game uploader. The file is only replayed, never graded or stored."""
    st.file_uploader("Load my game", type="json", key=key, on_change=load_game, args=(key,))
    if st.session_state.get("load_error"):
        st.error(st.session_state["load_error"])


def new_run_id() -> str:
    """Return a new id for a finished round."""
    return str(uuid.uuid4())
