"""Chatbot Defense Arena, Streamlit entry point. Routes by st.session_state["screen"]."""

import streamlit as st

from ui import common, data, endless, home, levels, play, records, report, settings, shell, theme

st.set_page_config(page_title="Chatbot Defense Arena", page_icon="\U0001f6e1️", layout="wide")

SCREENS = {
    "home": home.home_screen,
    "levels": levels.levels_screen,
    "play": play.play_screen,
    "report": report.report_screen,
    "replay": play.replay_screen,
    "endless": endless.endless_screen,
    "records": records.records_screen,
    "settings": settings.settings_screen,
}


def init_state() -> None:
    """Set the session defaults once."""
    defaults = {"screen": "home", "level_id": None, "attempt": None, "result": None, "try_no": 0, "last_package": {},
                "progress": {}, "attempts": {}, "speed": "normal", "endless": None, "confirm_reset": False,
                "player_name": "",
                "pb_step": 0, "pb_playing": False, "pb_last": 0.0,
                "replay_log": None, "replay_world": None, "replay_back": "home",
                "guide_index": 0, "guide_done": False, "guide_skipped": False}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = data.new_session_id()


init_state()
theme.apply_theme()
shell.topbar()
if st.session_state.get("shown_screen") != st.session_state["screen"]:
    st.session_state["shown_screen"] = st.session_state["screen"]
    common.scroll_to_top()
SCREENS.get(st.session_state["screen"], home.home_screen)()
