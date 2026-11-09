"""The play screen of a level: rule shop, system core map and chat. Setting up, the live round, and the replay."""

import streamlit as st

from ui import chat, common, data, guide, progress

PACKAGE_LETTERS = "ABCD"
SHOP_NOTE = ("Each rule costs compute (⚡). Rules that do no work lower your grade, "
             "and you won't be told which ones afterwards.")


WAITING_TEXT = "Choose your rules, then press Run round. Visitors and attackers show up here, one chat at a time."


def card_key(try_no: int, card_id: str) -> str:
    """Return the session state key of a rule card's toggle in one try."""
    return f"card_{try_no}_{card_id}"


def selected_cards(attempt: dict, try_no: int) -> list[str]:
    """Return the cards the player switched on, in shop order."""
    return [card_id for card_id in attempt["shop"] if st.session_state.get(card_key(try_no, card_id))]


def run_round() -> None:
    """Play the try with the chosen cards, save the progress and start the chat playback."""
    state = st.session_state
    level = data.content.get_level(state["level_id"])
    result = data.play.play_level(level, state["attempt"], selected_cards(state["attempt"], state["try_no"]))
    state["attempts"][level["id"]] = state["attempts"].get(level["id"], 0) + 1
    result.update(run_id=common.new_run_id(), attempt=state["attempts"][level["id"]], recorded=False, saved=False)
    state["result"] = result
    common.record_progress(level, result)
    progress.request_save()
    common.start_playback()


def show_header(level: dict, world: dict) -> None:
    """Show the world, the title, and the attacker's goal and style."""
    packs = "1 script package" if level.get("tutorial") else f"1 of {len(level['packs'])} script packages, drawn at random"
    with st.container(key="sec_story"):
        common.eyebrow(f"{world['name']} · {packs}", "play")
        st.header(common.level_title(level))
    with st.container(key="sec_theme"), st.container(key="goal"):
        st.markdown(f"**Attacker's goal.** {level['goal']}")
        st.markdown(f"**Their style.** {level['style']}")


def rule_card(world: dict, card_id: str, try_no: int) -> None:
    """Show one rule as a card: a toggle with its name and compute cost, and its sentence under it."""
    card = data.content.get_card(card_id, world)
    with st.container(key=f"rcard_{card_id}"):
        st.toggle(f"{card['label']}  ·  {card['cost']}⚡", key=card_key(try_no, card_id))
        st.write(card["text"])


def rules_panel(world: dict, attempt: dict, try_no: int) -> None:
    """Show the rule shop of this try, the compute used so far and the Run round button."""
    chosen = selected_cards(attempt, try_no)
    used = sum(data.content.get_card(card_id, world)["cost"] for card_id in chosen)
    with st.container(key="panel_rules"):
        with st.container(key="sec_rules"):
            head, chip = st.columns([3, 2])
            head.subheader("Rule shop")
            chip.caption(f"{len(attempt['shop'])} rules")
            st.caption(SHOP_NOTE)
            for card_id in attempt["shop"]:
                rule_card(world, card_id, try_no)
            with st.container(key="budget"):
                st.write(f"Compute used: {used}⚡ · Rules selected: {len(chosen)}")
            st.caption(common.PERSONAL_DATA_NOTICE)
        with st.container(key="sec_start_button"):
            st.button("Run round", type="primary", key="run_round", on_click=run_round, use_container_width=True)


def map_panel_empty(world: dict) -> None:
    """Show the map before the round: nothing attacked yet."""
    chat.show_map_panel(world, None)


def chat_waiting(world: dict, text: str = WAITING_TEXT) -> None:
    """Show the empty chat window before the round."""
    with st.container(key="panel_chat"):
        with st.container(key="chat_head"):
            st.markdown(f"{common.WORLD_ICON[world['id']]} **{world['bot']}**")
            st.caption("● Waiting for your rules")
        with st.container(key="chat_body"):
            st.caption(text)


def leave_to_levels() -> None:
    """Go back to the level map from inside the chat fragment (needs a full rerun)."""
    common.goto("levels")
    st.rerun()


def rules_used_panel(world: dict, level: dict, result: dict):
    """Return the left panel shown during and after the round: the rules used, the compute, and what to do next."""
    def panel(step: int, count: int) -> None:
        with st.container(key="panel_rules_used"):
            st.subheader("Your rules this round")
            for card_id in result["selected"]:
                card = data.content.get_card(card_id, world)
                st.write(f"• {card['label']}  ·  {card['cost']}⚡")
            if not result["selected"]:
                st.write("No rules chosen")
            with st.container(key="budget"):
                st.write(f"Compute used: {result['used']}⚡ · {data.grade.efficiency_label(result['excess'])}")
            finished = step >= count - 1
            if st.button("Try again with new scripts", key="retry_try", use_container_width=True):
                common.retry_level()
                st.rerun()
            if finished and st.button("Report", key="open_report", use_container_width=True):
                common.goto("report")
                st.rerun()
            if st.button("Go to Level mode" if level.get("tutorial") else "Level map", key="to_levels", use_container_width=True):
                leave_to_levels()
    return panel


def report_button(finished: bool) -> None:
    """Show the See report button once the chat has finished."""
    if finished and st.button("See report", type="primary", key="pb_report"):
        common.goto("report")
        st.rerun()  # a button inside a fragment only reruns the fragment, so rerun the whole app


def play_screen() -> None:
    """Show the level in play: setting up the rules, the chat playing live, or the finished round."""
    state = st.session_state
    level = data.content.get_level(state["level_id"])
    world = data.content.get_world(level["world"])
    result = state["result"]
    back, help_col, _ = st.columns([1, 1, 6])
    back.button("← Levels", key="play_back", on_click=common.goto, args=("levels",))
    if data.get_guide_steps(level):
        help_col.button("Help", key="level_help", on_click=guide.restart)
    guide.show("run" if result else "play", level)
    show_header(level, world)
    if result:
        chat.playback_view(world["id"], result["log"], rules_used_panel(world, level, result), report_button,
                           False, level if data.get_guide_steps(level) else None)
        return
    rules_col, map_col, chat_col = st.columns([10, 11, 11], gap="medium")
    with rules_col:
        rules_panel(world, state["attempt"], state["try_no"])
    with map_col:
        map_panel_empty(world)
    with chat_col, st.container(key="sec_chat"):
        chat_waiting(world)


# ---- replay ------------------------------------------------------------------------------------

def leave_replay() -> None:
    """Go back to where the replay was opened from (needs a full rerun inside the fragment)."""
    common.goto(st.session_state["replay_back"])
    st.rerun()


def replay_panel(world: dict):
    """Return the left panel of the replay: what it shows and the way back."""
    def panel(step: int, count: int) -> None:
        with st.container(key="panel_rules_used"):
            st.subheader("Replay")
            st.write(f"Watch the core of {world['name']} change, message by message. Step, skip or drag the slider.")
            back = "Back to report" if st.session_state["replay_back"] == "report" else (
                "Back to the section report" if st.session_state["replay_back"] == "endless" else "Back")
            if st.button(back, key="replay_back_btn", use_container_width=True):
                leave_replay()
    return panel


def replay_screen() -> None:
    """Show a recorded round again: the chat and the map change together, with full playback controls."""
    state = st.session_state
    world = data.content.get_world(state["replay_world"])
    common.eyebrow(f"Replay · {world['name']}", "replay")
    st.header("Watch the core change, message by message")
    chat.playback_view(world["id"], state["replay_log"], replay_panel(world), lambda finished: None, True, None)
