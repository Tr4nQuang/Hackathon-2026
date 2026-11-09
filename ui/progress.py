"""Browser saved progress, kept in this browser only (localStorage): level stars and Endless section bests, and the Endless run
in progress so it can be continued after the game is closed. The run holds the rules the player wrote, their grades and the
rows of the run file. It never holds a name, and nothing here is sent anywhere.
"""

import json
import uuid

import streamlit as st

from ui import data

PROGRESS_VERSION = 2
STORAGE_KEY = "chatbot-defense-arena-progress"
MAX_STARS = 3
MAX_POINTS = 10_000_000
MAX_SECTION = 999
MAX_RULES = 1000
MAX_HISTORY = 200
MAX_SEED = 10**9
RUN_KEYS = {"section", "score", "passed", "rules", "seed", "run_id", "over", "history"}
HISTORY_KEYS = {"n", "world", "grade", "points", "row"}


def _count(value: object, top: int) -> bool:
    """Return True for a plain int from 0 to top (bools are not counts)."""
    return type(value) is int and 0 <= value <= top


# ---- the progress object: plain data, no Streamlit -----------------------------------------------

def build_progress(levels: dict, endless: dict, run: dict | None = None) -> dict:
    """Return the object written to localStorage (the Endless run in progress is only there when there is one)."""
    saved = {"version": PROGRESS_VERSION, "levels": dict(levels), "endless": dict(endless)}
    if run:
        saved["run"] = run
    return saved


def merge_level(levels: dict, level_id: str, stars: int, points: int, perfect: bool) -> dict:
    """Return a copy of levels keeping the best stars and points and any perfect."""
    old = levels.get(level_id, {"stars": 0, "best": 0, "perfect": False})
    return {**levels, level_id: {"stars": max(old["stars"], stars), "best": max(old["best"], points),
                                 "perfect": old["perfect"] or perfect}}


def merge_section(endless: dict, section: int, points: int, cleared: bool) -> dict:
    """Return a copy of the Endless bests keeping the best points of a section number and whether it was ever cleared."""
    key = str(section)
    old = endless.get(key, {"best": 0, "cleared": False})
    return {**endless, key: {"best": max(old["best"], points), "cleared": old["cleared"] or cleared}}


def endless_totals(endless: dict) -> tuple[int, int]:
    """Return the saved Score (best points of the cleared sections) and the Cleared count."""
    cleared = [row for row in endless.values() if row["cleared"]]
    return sum(row["best"] for row in cleared), len(cleared)


def _valid_level(row: object) -> bool:
    """Return True for {"stars", "best", "perfect"} with sane values."""
    return (isinstance(row, dict) and set(row) == {"stars", "best", "perfect"} and _count(row["stars"], MAX_STARS)
            and _count(row["best"], MAX_POINTS) and type(row["perfect"]) is bool)


def _valid_section(key: object, row: object) -> bool:
    """Return True for a section number key and {"best", "cleared"} with sane values."""
    return (isinstance(key, str) and key.isdigit() and 1 <= int(key) <= MAX_SECTION and isinstance(row, dict)
            and set(row) == {"best", "cleared"} and _count(row["best"], MAX_POINTS) and type(row["cleared"]) is bool)


def parse_progress(text: str | None, known_levels: set[str]) -> tuple[dict, dict]:
    """Return (levels, endless) from saved text; invalid entries, or the whole thing if malformed, are ignored."""
    try:
        data = json.loads(text or "")
    except (TypeError, ValueError):
        return {}, {}
    if not isinstance(data, dict) or data.get("version") != PROGRESS_VERSION:
        return {}, {}
    levels = data.get("levels") if isinstance(data.get("levels"), dict) else {}
    endless = data.get("endless") if isinstance(data.get("endless"), dict) else {}
    return ({key: row for key, row in levels.items() if key in known_levels and _valid_level(row)},
            {key: row for key, row in endless.items() if _valid_section(key, row)})


def _short_text(value: object, top: int) -> bool:
    """Return True for a string of at most top characters."""
    return isinstance(value, str) and len(value) <= top


def _valid_history_row(row: object) -> bool:
    """Return True for {"n", "world", "grade", "points", "row"} with sane values and a valid run file row."""
    return (isinstance(row, dict) and set(row) == HISTORY_KEYS and _count(row["n"], MAX_SECTION) and row["n"] >= 1
            and _short_text(row["world"], 40) and _short_text(row["grade"], 40) and _count(row["points"], MAX_POINTS)
            and data.run_file.row_ok(row["row"]))


def _valid_run(run: object) -> bool:
    """Return True for a saved Endless run with every field in range."""
    if not isinstance(run, dict) or set(run) != RUN_KEYS:
        return False
    try:
        uuid.UUID(str(run["run_id"]))
    except ValueError:
        return False
    return (_count(run["section"], MAX_SECTION) and run["section"] >= 1 and _count(run["score"], MAX_POINTS) and _count(run["passed"], MAX_SECTION)
            and _short_text(run["rules"], MAX_RULES) and _count(run["seed"], MAX_SEED) and type(run["over"]) is bool
            and isinstance(run["history"], list) and len(run["history"]) <= MAX_HISTORY and run["passed"] <= len(run["history"])
            and all(_valid_history_row(row) for row in run["history"]))


def parse_run(text: str | None) -> dict | None:
    """Return the saved Endless run in the text, or None when there is none or any part of it is not valid."""
    try:
        saved = json.loads(text or "")
    except (TypeError, ValueError):
        return None
    if not isinstance(saved, dict) or saved.get("version") != PROGRESS_VERSION:
        return None
    return saved["run"] if _valid_run(saved.get("run")) else None


# ---- the browser side: every read and write is wrapped so blocked storage changes nothing ----------

def _js_eval(expression: str, key: str):
    """Run one JS expression in the browser; return its value, or None until it answers or if it fails."""
    try:
        from streamlit_js_eval import streamlit_js_eval

        return streamlit_js_eval(js_expressions=expression, key=key)
    except Exception:  # noqa: BLE001 blocked storage or a broken component must never stop the game
        return None


def has_saved() -> bool:
    """Return True when there is level or Endless progress to continue from."""
    state = st.session_state
    return bool(state["progress"] or state.get("endless_best") or state.get("saved_run"))


def load_saved_progress(known_levels: set[str]) -> None:
    """Merge the browser's saved progress into the session, once per session."""
    state = st.session_state
    if state.get("progress_loaded"):
        return
    try:
        expression = f"(() => {{ try {{ return localStorage.getItem({json.dumps(STORAGE_KEY)}) || '' }} catch (e) {{ return '' }} }})()"
        text = _js_eval(expression, "progress_load")
        if text is None:
            return  # the component answers on a later rerun
        state["progress_loaded"] = True
        levels, endless = parse_progress(text, known_levels)
        state["saved_run"] = parse_run(text)
        for level_id, row in levels.items():
            state["progress"] = merge_level(state["progress"], level_id, row["stars"], row["best"], row["perfect"])
        best = state.setdefault("endless_best", {})
        for key, row in endless.items():
            best = merge_section(best, int(key), row["best"], row["cleared"])
        state["endless_best"] = best
    except Exception:  # noqa: BLE001 bad saved data must never stop the game
        state["progress_loaded"] = True
        return
    if levels or endless or state.get("saved_run"):
        st.rerun()


def request_save() -> None:
    """Mark the progress to be written to the browser on this run."""
    st.session_state["progress_save_n"] = st.session_state.get("progress_save_n", 0) + 1


def save_run(snapshot: dict | None) -> None:
    """Keep the Endless run in progress (or None when there is none) in this session and in the browser."""
    st.session_state["saved_run"] = snapshot
    request_save()


def record_section(section: int, points: int, cleared: bool) -> None:
    """Remember the best points of an Endless section number and save it."""
    state = st.session_state
    state["endless_best"] = merge_section(state.get("endless_best", {}), section, points, cleared)
    request_save()


def clear_saved() -> None:
    """Forget level and Endless progress in this session and in the browser."""
    st.session_state.update(progress={}, endless_best={}, saved_run=None, confirm_reset=False, last_package={})
    request_save()


def write_pending_progress() -> None:
    """Write the progress to localStorage until the browser confirms it."""
    state = st.session_state
    n = state.get("progress_save_n", 0)
    if n == state.get("progress_saved_n", 0):
        return
    try:
        text = json.dumps(json.dumps(build_progress(state["progress"], state.get("endless_best", {}), state.get("saved_run"))))
        expression = (f"(() => {{ try {{ localStorage.setItem({json.dumps(STORAGE_KEY)}, {text}); return 1 }} "
                      f"catch (e) {{ return 0 }} }})()")
        if _js_eval(expression, f"progress_save_{n}") is not None:
            state["progress_saved_n"] = n
    except Exception:  # noqa: BLE001 a failed save must never stop the game
        state["progress_saved_n"] = n
