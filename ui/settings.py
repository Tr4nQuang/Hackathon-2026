"""Game settings: chat speed and resetting the saved progress."""

import streamlit as st

from ui import common, progress

SPEEDS = ("normal", "fast", "instant")
PROGRESS_NOTE = ("Level stars, best scores and Endless section bests are saved only in this browser on this computer, "
                 "and never sent anywhere.")


def set_speed() -> None:
    """Remember the chat speed picked in the settings."""
    st.session_state["speed"] = st.session_state["speed_pick"]


def ask_reset() -> None:
    """Ask the player to confirm erasing the level progress."""
    st.session_state["confirm_reset"] = True


def cancel_reset() -> None:
    """Keep the level progress."""
    st.session_state["confirm_reset"] = False


def reset_progress() -> None:
    """Erase all level progress."""
    progress.clear_saved()


def speed_panel() -> None:
    """Show the chat speed choice."""
    with st.container(key="panel_speed"):
        st.subheader("Chat speed")
        st.caption("How fast attacks and replies appear during a round.")
        with st.container(key="speed_seg"):  # styled as a pill shaped segmented control in ui/theme.py
            st.radio("Chat speed", SPEEDS, index=SPEEDS.index(st.session_state["speed"]), format_func=str.capitalize,
                     horizontal=True, key="speed_pick", on_change=set_speed, label_visibility="collapsed")


def progress_panel() -> None:
    """Show the reset of the level progress (it asks first)."""
    state = st.session_state
    with st.container(key="panel_progress"):
        st.subheader("Progress")
        st.caption(PROGRESS_NOTE)
        if state.get("confirm_reset"):
            st.write("Erase all level and Endless progress saved in this browser? This can't be undone.")
            erase, keep, _ = st.columns([2, 2, 5])
            erase.button("Erase progress", key="set_erase", on_click=reset_progress)
            keep.button("Cancel", key="set_cancel", on_click=cancel_reset)
        else:
            reset, _ = st.columns([2, 7])
            reset.button("Reset progress", key="set_reset", on_click=ask_reset)


def settings_screen() -> None:
    """Show the game settings."""
    _, middle, _ = st.columns([1, 8, 1])
    with middle:
        common.eyebrow("Settings", "settings")
        st.header("Game settings")
        speed_panel()
        progress_panel()
