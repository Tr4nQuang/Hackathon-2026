"""The live shift component shared by Endless and the campaign: visitors arrive one at a time and the player decides on each.

A "run" here is any dict in the session that holds a `cur` (world_id, spec, messages), a `shift` (engine/arena/endless.start_shift),
the visitor's `deadline` and `reveal_until`. Endless keeps it in session["endless"], a level in session["lvl_run"].
"""

import time
from typing import Callable

import streamlit as st

from ui import chat, common, data

TICK_SECONDS = 0.5
REVEAL_SECONDS = {"normal": 1.4, "fast": 0.6, "instant": 0.2}  # how long a reply stays alone before the next visitor


def decide(key: str, block: bool) -> None:
    """Block the waiting visitor or let the chatbot answer, then pause briefly so the reply can be read."""
    run = st.session_state[key]
    shift = run["shift"]
    if shift is None or data.endless.shift_pending(shift) is None:
        return
    data.endless.shift_step(shift, block=block and shift["blocks_left"] > 0)
    run.update(deadline=None, reveal_until=time.monotonic() + REVEAL_SECONDS.get(st.session_state.get("speed", "normal"), 1.4))


def decision_bar(key: str, run: dict, visitor: dict, left: float, when: str) -> None:
    """Show the waiting visitor's message with the countdown and the two choices, at the top where nothing needs scrolling."""
    shift, seconds = run["shift"], run["cur"]["spec"]["seconds"]
    with st.container(key="decision"):
        message, choice = st.columns([3, 2], gap="medium", vertical_alignment="center")
        with message:
            st.caption(f"Visitor · {when} · attacker or customer? Only the message tells you.")
            st.text(visitor["text"] if visitor["kind"] == "attack" else visitor["q"])
        with choice:
            if seconds:
                st.progress(max(0.0, min(1.0, left / seconds)), text=f"{left:.0f} s · then the chatbot answers")
            block, let = st.columns(2)
            block.button(f"Block · {shift['blocks_left']} left", key="e_block", type="primary", on_click=decide, args=(key, True),
                         disabled=shift["blocks_left"] <= 0, use_container_width=True)
            let.button("Let it through", key="e_let", on_click=decide, args=(key, False), use_container_width=True)


def shift_panel(run: dict, number: int, total: int) -> None:
    """Show the left panel during a shift: the rules in force, blocks left and progress."""
    shift = run["shift"]
    with st.container(key="panel_rules_used"):
        st.subheader("On duty")
        st.text(run["rules"] or "(no rules: the chatbot will answer anything)")
        st.caption(f"Visitor {min(number, total)} of {total} · {shift['blocks_left']} block{'' if shift['blocks_left'] == 1 else 's'} left")


@st.fragment(run_every=TICK_SECONDS)
def shift_view(key: str, on_end: Callable[[], None], active: str) -> None:
    """The live shift: only this part reruns on every tick, to count down, time out and show each reply."""
    run = st.session_state.get(key)
    if not run or run.get("status") != active or run["shift"] is None:
        return
    shift, now = run["shift"], time.monotonic()
    world = data.content.get_world(run["cur"]["world_id"])
    visitor = data.endless.shift_pending(shift)
    waiting = now < run["reveal_until"]
    if visitor is None and not waiting:
        on_end()
        st.rerun()
    seconds = run["cur"]["spec"]["seconds"]
    if visitor is not None and not waiting and seconds:
        if run["deadline"] is None:
            run["deadline"] = now + seconds
        if now >= run["deadline"]:
            decide(key, False)
            visitor, waiting = data.endless.shift_pending(shift), True
    log, total = shift["round"]["rec"].log, len(run["cur"]["messages"])
    show_visitor = visitor if not waiting else None
    when = data.endless.rounds.clock(shift["round"]["index"]) if show_visitor else ""
    if show_visitor is not None:
        decision_bar(key, run, show_visitor, max(0.0, (run["deadline"] or now) - now), when)
    else:
        with st.container(key="decision_wait"):
            st.caption("The chatbot is answering..." if visitor is not None or not waiting else "Shift over. Opening the report...")
    left_col, map_col, chat_col = st.columns([10, 11, 11], gap="medium")
    with left_col:
        shift_panel(run, shift["round"]["index"] + 1, total)
    with map_col:
        chat.show_map_panel(world, log[-1])
    with chat_col, st.container(key="sec_chat"):
        chat.show_chat(world, log, len(log) - 1, "Under attack", False, show_visitor, when)
        common.scroll_to_latest(f"{len(log)}-{bool(show_visitor)}")
