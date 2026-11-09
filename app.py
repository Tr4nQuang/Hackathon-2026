"""Chatbot Defense Arena, Streamlit entry point. Routes by st.session_state["screen"]."""

import streamlit as st

from ui import common, data, endless, playback, progress, screens, shell, theme

st.set_page_config(page_title="Chatbot Defense Arena", page_icon="\U0001f6e1️", layout="wide")

SCREENS = {
    "home": screens.home_screen,
    "levels": screens.level_select_screen,
    "level": screens.level_screen,
    "playback": playback.playback_screen,
    "results": playback.results_screen,
    "endless_select": endless.endless_select_screen,
    "endless": endless.endless_screen,
}


def init_state() -> None:
    """Set the session defaults once."""
    defaults = {"screen": "home", "level_id": None, "section_id": None, "progress": {}, "run": None,
                "attempts": {}, "endless_last_run": None,
                "pb_step": 0, "pb_playing": False, "pb_last": 0.0,
                "guide_index": 0, "guide_done": False, "guide_skipped": False}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = data.new_session_id()


init_state()
progress.load_saved_progress({level["id"] for level in common.get_scenario()["levels"]})
theme.apply_theme()
shell.topbar()
if st.session_state.get("shown_screen") != st.session_state["screen"]:
    st.session_state["shown_screen"] = st.session_state["screen"]
    common.scroll_to_top()
SCREENS.get(st.session_state["screen"], screens.home_screen)()
progress.write_pending_progress()
