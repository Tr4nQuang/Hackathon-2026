"""The top bar: brand, AI status and the five main places, shown on every screen."""

import streamlit as st

from ui import common, data

NAV = (
    ("Home", "home", ("home",)),
    ("Levels", "levels", ("levels", "play", "report")),
    ("Endless", "endless", ("endless",)),
    ("Records", "records", ("records",)),
    ("Settings", "settings", ("settings",)),
)


def current_group() -> str:
    """Return the nav item the player is in. A replay belongs to the place it was opened from."""
    state = st.session_state
    screen = state["screen"]
    if screen == "replay":
        screen = {"report": "report", "endless": "endless"}.get(state.get("replay_back"), "home")
    return next((target for _, target, screens in NAV if screen in screens), "home")


def topbar() -> None:
    """Show the brand, the AI tag and the nav buttons; the current place is highlighted."""
    here = current_group()
    with st.container(key="topbar"):
        brand, tag, *buttons = st.columns([4, 2, 1.3, 1.3, 1.3, 1.3, 1.3], gap="small", vertical_alignment="center")
        with brand, st.container(key="brand"):
            st.markdown("\U0001f6e1️ **Chatbot Defense Arena**")
        with tag, st.container(key="ai_tag"):
            st.caption("Live AI on" if data.live.is_live() else "Demo build")
        for column, (label, target, _) in zip(buttons, NAV):
            column.button(label, key=f"nav_{target}", type="primary" if target == here else "tertiary",
                          on_click=common.open_place, args=(target,), use_container_width=True)
