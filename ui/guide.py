"""Tutorial guide: a coach that shows one step at a time, with the target section highlighted and the others dimmed."""

import time

import streamlit as st

from ui import data

# The guide follows the play screen: "play" is the screen before the round, "run" while the chat plays, "report" after.
TARGET_SCREEN = {
    "story": "play", "map": "play", "theme": "play", "rules": "play", "start_button": "play",
    "chat": "run",
    "results": "report", "replay_button": "report", "retry_next_buttons": "report",
}
SCREEN_SECTIONS = {
    "play": ("story", "map", "theme", "rules", "start_button"),
    "run": ("chat", "map"),
    "report": ("results", "replay_button", "retry_next_buttons"),
}
HIGHLIGHT_COLOR = "#f59e0b"
DIMMED_OPACITY = 0.35


def restart() -> None:
    """Start the guide again from the first step."""
    st.session_state.update(guide_index=0, guide_done=False, guide_skipped=False)


def skip() -> None:
    """Close the guide for good (the Help button restarts it)."""
    st.session_state.update(guide_done=True, guide_skipped=True)


def advance(steps: list[dict]) -> None:
    """Go to the next step, or finish after the last one. Leaving the chat step resumes the playback."""
    state = st.session_state
    index = state["guide_index"]
    if steps[index]["target"] == "chat":
        state.update(pb_playing=True, pb_last=time.monotonic())
    if index + 1 >= len(steps):
        state["guide_done"] = True
    else:
        state["guide_index"] = index + 1


def active_step(screen: str, source: dict) -> dict | None:
    """Return the guide step to show on this screen, or None when the guide is off or belongs elsewhere."""
    steps = data.get_guide_steps(source)
    state = st.session_state
    if not steps or state["guide_done"] or state["guide_index"] >= len(steps):
        return None
    step = steps[state["guide_index"]]
    return step if TARGET_SCREEN.get(step["target"]) == screen else None


def sync(screen: str, source: dict) -> None:
    """Move the guide forward when the player reached a screen before its steps (for example ran the round early)."""
    steps = data.get_guide_steps(source)
    state = st.session_state
    if not steps or state["guide_done"] or screen == "play":
        return
    first = next((i for i, step in enumerate(steps) if TARGET_SCREEN.get(step["target"]) == screen), None)
    if first is not None and state["guide_index"] < first:
        state["guide_index"] = first


def highlight_css(screen: str, target: str) -> str:
    """Return CSS that outlines the target section and dims the other sections of the screen."""
    dimmed = ", ".join(f".st-key-sec_{name}" for name in SCREEN_SECTIONS[screen] if name != target)
    return (f"<style>{dimmed} {{opacity: {DIMMED_OPACITY};}} "
            f".st-key-sec_{target} {{outline: 4px solid {HIGHLIGHT_COLOR}; outline-offset: 4px; "
            f"border-radius: 8px;}}</style>")


def show(screen: str, source: dict) -> None:
    """Show the coach box and the highlight for this screen, if a step belongs here."""
    sync(screen, source)
    step = active_step(screen, source)
    if step is None:
        return
    steps = data.get_guide_steps(source)
    index = st.session_state["guide_index"]
    st.html(highlight_css(screen, step["target"]))
    with st.container(key="guide_box"):
        avatar, body = st.columns([1, 14], vertical_alignment="top")
        with avatar, st.container(key="coach_avatar"):
            st.markdown("C")
        with body:
            st.markdown(f"**Tutorial, step {index + 1} of {len(steps)}: {step['title']}**")
            st.write(step["text"])
            next_col, skip_col, _ = st.columns([1, 2, 6])
            next_col.button("Got it" if index + 1 == len(steps) else "Next", type="primary", key="guide_next",
                            on_click=advance, args=(steps,))
            skip_col.button("Skip tutorial", key="guide_skip", on_click=skip)
