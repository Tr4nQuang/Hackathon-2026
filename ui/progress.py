"""Browser saved progress: best stars per level only, no personal data, no rules, no player text."""

import json

import streamlit as st

PROGRESS_VERSION = 1
STORAGE_KEY = "chatbot-defense-arena-progress"
MAX_STARS = 3


def build_progress(stars: dict[str, int]) -> dict:
    """Return the object written to localStorage."""
    return {"version": PROGRESS_VERSION, "stars": dict(stars)}


def merge_stars(stars: dict[str, int], level_id: str, new_stars: int) -> dict[str, int]:
    """Return a copy of stars keeping the best result for level_id (0 stars is never stored)."""
    merged = dict(stars)
    if new_stars >= 1:
        merged[level_id] = max(merged.get(level_id, 0), new_stars)
    return merged


def parse_progress(text: str | None, known_ids: set[str]) -> dict[str, int]:
    """Return valid {level_id: stars} from saved text; anything invalid is ignored."""
    try:
        data = json.loads(text or "")
    except (TypeError, ValueError):
        return {}
    if not isinstance(data, dict) or data.get("version") != PROGRESS_VERSION or not isinstance(data.get("stars"), dict):
        return {}
    return {level_id: stars for level_id, stars in data["stars"].items()
            if level_id in known_ids and type(stars) is int and 1 <= stars <= MAX_STARS}


def _js_eval(expression: str, key: str):
    """Run one JS expression in the browser; return its value, or None until it answers or if it fails."""
    try:
        from streamlit_js_eval import streamlit_js_eval

        return streamlit_js_eval(js_expressions=expression, key=key)
    except Exception:  # noqa: BLE001 blocked storage or a broken component must never stop the game
        return None


def load_saved_progress(known_ids: set[str]) -> None:
    """Merge the browser's saved stars into st.session_state["progress"], once per session."""
    state = st.session_state
    if state.get("progress_loaded"):
        return
    expression = f"(() => {{ try {{ return localStorage.getItem({json.dumps(STORAGE_KEY)}) || '' }} catch (e) {{ return '' }} }})()"
    text = _js_eval(expression, "progress_load")
    if text is None:
        return  # the component answers on a later rerun
    state["progress_loaded"] = True
    saved = parse_progress(text, known_ids)
    for level_id, stars in saved.items():
        state["progress"] = merge_stars(state["progress"], level_id, stars)
    state["progress_saved"] = bool(saved)
    if saved:
        st.rerun()


def request_save() -> None:
    """Mark the progress to be written to the browser on this run."""
    st.session_state["progress_save_n"] = st.session_state.get("progress_save_n", 0) + 1


def write_pending_progress() -> None:
    """Write st.session_state["progress"] to localStorage until the browser confirms it."""
    state = st.session_state
    n = state.get("progress_save_n", 0)
    if n == state.get("progress_saved_n", 0):
        return
    text = json.dumps(json.dumps(build_progress(state["progress"])))
    expression = (f"(() => {{ try {{ localStorage.setItem({json.dumps(STORAGE_KEY)}, {text}); return 1 }} "
                  f"catch (e) {{ return 0 }} }})()")
    if _js_eval(expression, f"progress_save_{n}") is not None:
        state["progress_saved_n"] = n
        state["progress_saved"] = bool(state["progress"])
