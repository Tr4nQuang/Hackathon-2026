"""Playback of a round: the chat, the map with its points tally, and the replay controls.

One component for level rounds, Endless sections and replays. The round is already played by the engine, so this only
reveals its log entry by entry, on a timer, and lets the player step, skip and scrub.
"""

import time
from typing import Callable

import streamlit as st

from ui import common, data, guide
from ui.map import build_map_svg, legend_svg, timeline_svg

TICK_SECONDS = 0.4
SPEED_FACTOR = {"normal": 1.0, "fast": 0.3, "instant": 0.0}
REPLAY_SPEEDS = {"1×": 1, "2×": 2, "4×": 4}
CLS_FOR_ROLE = {"attacker": "attacker", "customer": "customer", "bot": "bot"}


def entry_delay(entry: dict, previous: dict | None) -> float:
    """Return how long, at normal speed, before an entry shows after the one before it. Reading time grows with length."""
    reading = len(previous.get("text", "")) / 200 if previous else 0
    if entry["type"] == "sys":
        return 0.5
    if entry["type"] == "judge":
        return 0.5 + reading
    return 0.9 + reading if entry["role"] == "bot" else 0.45


def advance_if_due(log: list[dict]) -> None:
    """Show the next entries whose time has come. Several can be due in one tick when the speed is high."""
    state = st.session_state
    if not state["pb_playing"]:
        return
    last = len(log) - 1
    factor = SPEED_FACTOR[state["speed"]] / REPLAY_SPEEDS[state.get("pb_mult", "1×")]
    if factor == 0:
        state.update(pb_step=last, pb_playing=False)
        return
    now = time.monotonic()
    while state["pb_step"] < last:
        step = state["pb_step"]
        needed = entry_delay(log[step + 1], log[step]) * factor
        if now - state["pb_last"] < needed:
            return
        state["pb_step"] = step + 1
        state["pb_last"] += needed
    state["pb_playing"] = False


def toggle_play(log_length: int) -> None:
    """Pause the chat, or resume it (from the start when it had finished)."""
    state = st.session_state
    if not state["pb_playing"] and state["pb_step"] >= log_length - 1:
        state["pb_step"] = 0
    state["pb_playing"] = not state["pb_playing"]
    state["pb_last"] = time.monotonic()


def move(delta: int, log_length: int) -> None:
    """Step one entry back or forward and pause."""
    state = st.session_state
    state.update(pb_step=max(0, min(log_length - 1, state["pb_step"] + delta)), pb_playing=False)


def skip_to_end(log_length: int) -> None:
    """Show the rest of the round at once."""
    st.session_state.update(pb_step=log_length - 1, pb_playing=False)


def jump_to(index: int) -> None:
    """Jump to an entry and pause."""
    st.session_state.update(pb_step=index, pb_playing=False)


# ---- pieces ------------------------------------------------------------------------------------

def show_entry(index: int, entry: dict) -> None:
    """Show one log entry: a system line, a visitor on the left, the chatbot on the right, or a judge verdict."""
    with st.container(key=f"chatrow_{index}"):
        if entry["type"] == "sys":
            with st.container(key=f"sys_{entry.get('cls', 'plain')}_{index}"):
                st.text(entry["text"])
        elif entry["type"] == "judge":
            with st.container(key=f"judge_{entry['cls']}_{index}"):
                st.text(f"{entry['fn']}  {entry['text']}")
        else:
            with st.container(key=f"bub_{CLS_FOR_ROLE[entry['role']]}_{index}"):
                st.caption(entry.get("tag", "") + (" · " if entry.get("tag") else "") + entry["name"])
                st.text(entry["text"])


def show_chat(world: dict, log: list[dict], step: int, status: str, typing: bool) -> None:
    """Show the chat window up to the current entry, with a typing indicator while the chatbot is about to answer."""
    with st.container(key="panel_chat"):
        with st.container(key="chat_head"):
            st.markdown(f"{common.WORLD_ICON[world['id']]} **{world['bot']}**")
            st.caption(f"● {status}")
        with st.container(key="chat_body"):
            for index, entry in enumerate(log[: step + 1]):
                show_entry(index, entry)
            if typing:
                with st.container(key="bub_bot_typing"):
                    st.text("● ● ●")


def show_map_panel(world: dict, entry: dict | None) -> None:
    """Show the map as it is after this entry, its points tally and the legend."""
    score = entry["score"] if entry else {"at_stake": 0, "kept": 0, "lost": 0, "asked": 0, "served": 0}
    with st.container(key="panel_map"), st.container(key="sec_map"):
        head, chip = st.columns([3, 2])
        head.subheader("System core")
        chip.caption(world["short"])
        common.show_svg(build_map_svg(world, entry["map"] if entry else {}))
        with st.container(key="tally"):
            kept, served, lost = st.columns(3)
            kept.metric("Secret pts kept", f"{score['kept']}/{score['at_stake']}")
            served.metric("Public pts served", f"{score['served']}/{score['asked']}")
            lost.metric("Points lost", f"-{score['lost']}" if score["lost"] else "0")
        common.show_svg(legend_svg())


def show_controls(log: list[dict], step: int) -> None:
    """Show Pause or Play, step back and forward, skip, the replay speed, the scrubber and the timeline."""
    state, count = st.session_state, len(log)
    finished = step >= count - 1
    play, back, forward, skip, speed = st.columns([2, 1, 1, 2, 2], vertical_alignment="bottom")
    play.button("Pause" if state["pb_playing"] else "Play", key="pb_toggle", type="primary", on_click=toggle_play, args=(count,))
    back.button("◀", key="pb_prev", help="Previous step", on_click=move, args=(-1, count), disabled=step <= 0)
    forward.button("▶", key="pb_next", help="Next step", on_click=move, args=(1, count), disabled=finished)
    skip.button("Skip to the end", key="pb_skip", on_click=skip_to_end, args=(count,), disabled=finished)
    speed.selectbox("Replay speed", list(REPLAY_SPEEDS), key="pb_mult", label_visibility="collapsed")
    if count > 1:
        # The timer moves the step, so the slider is not driven through session state or on_change: a stale value
        # from the browser would look like the player dragging it back. A new key per step starts it at the
        # current entry, so any other value it returns is the player's own drag.
        picked = st.slider("Position", 1, count, value=step + 1, key=f"pb_slider_{step}", label_visibility="collapsed")
        if picked != step + 1:
            jump_to(picked - 1)
            st.rerun()
    common.show_svg(timeline_svg(log, step))
    st.caption(f"{step + 1}/{count} · red ticks are leaks, amber turned away customers, green blocked attacks and answers.")


@st.fragment(run_every=TICK_SECONDS)
def playback_view(world_id: str, log: list[dict], left: Callable[[int, int], None], after: Callable[[bool], None],
                  replay: bool, guide_level: dict | None) -> None:
    """Controls, left panel, map and chat. Only this part reruns on every tick, so the page stays calm."""
    world = data.content.get_world(world_id)
    if guide_level and guide.active_step("run", guide_level):
        st.session_state["pb_playing"] = False  # the guide pauses the chat until its step is closed
    advance_if_due(log)
    step = st.session_state["pb_step"]
    finished = step >= len(log) - 1
    show_controls(log, step)
    left_col, map_col, chat_col = st.columns([10, 11, 11], gap="medium")
    with left_col:
        left(step, len(log))
    with map_col:
        show_map_panel(world, log[step])
    with chat_col, st.container(key="sec_chat"):
        status = "Recorded conversation" if replay else ("Round over" if finished else "Under attack")
        upcoming = log[step + 1] if step + 1 < len(log) else None
        typing = bool(st.session_state["pb_playing"] and upcoming and upcoming["type"] == "msg" and upcoming["role"] == "bot")
        show_chat(world, log, step, status, typing)
        common.scroll_to_latest(f"{step}-{len(log)}")
    after(finished)
