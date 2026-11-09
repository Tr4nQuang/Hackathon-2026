"""Game settings: chat speed, resetting level progress, and the AI and storage status."""

import streamlit as st

from ui import common, data, progress

SPEEDS = ("normal", "fast", "instant")
AI_HELP = ("The API key is never typed into the game. It is read from the .env file on the computer that runs the game, "
           "and that file is never committed. To switch on live AI, copy .env.example to .env, set USE_FAKE_AI=false, "
           "add your own GEMINI_API_KEY and restart the game.")
STORAGE_HELP = "Anonymous results are only stored when you tick the box on a report, and only if SUPABASE_URL and SUPABASE_KEY are set in .env."
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


def connection_panel() -> None:
    """Show whether live AI and result storage are on. It never shows a key and has no field for one."""
    with st.container(key="panel_connection"):
        head, chip = st.columns([3, 2], vertical_alignment="center")
        head.subheader("AI connection")
        chip.caption(f"Live AI ready · {data.live.model_name()}" if data.live.is_live() else "Built-in scripts · USE_FAKE_AI=true")
        st.write(AI_HELP)
        st.caption(("Result storage is set up. " if data.storage_configured() else "Result storage is not set up. ") + STORAGE_HELP)


def settings_screen() -> None:
    """Show the game settings."""
    _, middle, _ = st.columns([1, 8, 1])
    with middle:
        common.eyebrow("Settings", "settings")
        st.header("Game settings")
        speed_panel()
        progress_panel()
        connection_panel()
