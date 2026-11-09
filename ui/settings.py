"""Game settings: chat speed, level progress (reset, export, import) and the AI and storage status."""

import streamlit as st

from ui import common, data, store

SPEEDS = ("normal", "fast", "instant")
AI_HELP = ("The API key is never typed into the game. It is read from the .env file on the computer that runs the game, "
           "and that file is never committed. To switch on live AI, copy .env.example to .env, set USE_FAKE_AI=false, "
           "add your own GEMINI_API_KEY and restart the game.")
STORAGE_HELP = "Anonymous results are only stored when you tick the box on a report, and only if SUPABASE_URL and SUPABASE_KEY are set in .env."
PROGRESS_NOTE = ("Level stars and best scores last until you close this tab. Export them to keep them, "
                 "and import the file next time.")


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
    st.session_state.update(progress={}, confirm_reset=False, last_package={})


def import_progress() -> None:
    """Read the uploaded progress file and merge it into this session's progress; show a message if it is not usable."""
    state = st.session_state
    uploaded = state.get("import_progress")
    if uploaded is None:
        return
    level_ids = [level["id"] for level in data.content.get_levels()]
    try:
        loaded = store.progress_from_json(uploaded.getvalue().decode("utf-8"), level_ids)
    except (ValueError, UnicodeDecodeError) as error:
        state["import_note"] = ("error", str(error))
        return
    state["progress"] = store.merge_progress(state["progress"], loaded)
    state["import_note"] = ("ok", f"Imported progress for {len(loaded)} level{'s' if len(loaded) != 1 else ''}. The better result of each level was kept.")


def speed_panel() -> None:
    """Show the chat speed choice."""
    with st.container(key="panel_speed"):
        st.subheader("Chat speed")
        st.caption("How fast attacks and replies appear during a round.")
        st.radio("Chat speed", SPEEDS, index=SPEEDS.index(st.session_state["speed"]), format_func=str.capitalize, horizontal=True,
                 key="speed_pick", on_change=set_speed, label_visibility="collapsed")


def progress_panel() -> None:
    """Show reset, export and import of the level progress."""
    state = st.session_state
    with st.container(key="panel_progress"):
        st.subheader("Progress")
        st.caption(PROGRESS_NOTE)
        if state.get("confirm_reset"):
            st.write("Erase all level progress? This can't be undone.")
            erase, keep, _ = st.columns([2, 2, 5])
            erase.button("Erase progress", key="set_erase", on_click=reset_progress)
            keep.button("Cancel", key="set_cancel", on_click=cancel_reset)
        else:
            reset, export, _ = st.columns([2, 2, 5])
            reset.button("Reset level progress", key="set_reset", on_click=ask_reset)
            export.download_button("Export progress", data=store.progress_to_json(state["progress"]), file_name="chatbot-defense-progress.json",
                                   mime="application/json", key="set_export")
        st.file_uploader("Import progress", type="json", key="import_progress", on_change=import_progress)
        kind, message = state.get("import_note", (None, ""))
        if kind == "error":
            st.error(message)
        elif kind == "ok":
            st.success(message)


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
