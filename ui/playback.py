"""Chat playback and the results screen, shared by Level mode and Endless mode."""

import time
import uuid

import streamlit as st

from ui import common, data, guide
from ui.common import STAR
from ui.map import build_map_svg, legend_svg

SPEEDS = {"Slow": 1.6, "Normal": 1.0, "Fast": 0.4}
BASE_DELAY_SECONDS = 2.0
SECONDS_PER_CHAR = 1 / 60
TICK_SECONDS = 0.5
SENDERS = ("attacker", "customer")
OUTCOME_TEXT = {"blocked": "✔ blocked", "leaked": "✕ leaked",
                "served": "✔ served", "refused": "⊘ refused"}
JUDGE_CLASS = {"blocked": "good", "served": "good", "leaked": "bad", "refused": "warn"}
EVENT_KEYS = ("sender", "text", "reply", "zone", "outcome", "map")
GREAT_RULES_TIP = "Even great rules can fail. Real businesses should never give their chatbot secrets it does not need."
CONSENT_TEXT = "Share my anonymous results to help research. No name or personal data is saved."
LOADED_NOTICE ="This is a replay of a saved game. Loaded games are not graded again and are never stored."
BACK_SCREEN = {"level": "level", "endless": "endless"}


# ---- playback ----------------------------------------------------------------------------------

def message_delay(event: dict, speed: str) -> float:
    """Return how many seconds to keep a message on screen: longer replies stay longer."""
    return (BASE_DELAY_SECONDS + len(event["reply"]) * SECONDS_PER_CHAR) * SPEEDS[speed]


def advance_if_due(events: list[dict]) -> None:
    """Show the next message when the current one has been on screen long enough."""
    state = st.session_state
    if not state["pb_playing"]:
        return
    if state["pb_step"] >= len(events) - 1:
        state["pb_playing"] = False
        return
    delay = message_delay(events[state["pb_step"]], state.get("pb_speed", "Normal"))
    if time.monotonic() - state["pb_last"] >= delay:
        state["pb_step"] += 1
        state["pb_last"] = time.monotonic()


def toggle_play() -> None:
    """Pause the chat, or resume it."""
    state = st.session_state
    state["pb_playing"] = not state["pb_playing"]
    state["pb_last"] = time.monotonic()


def next_message(last: int) -> None:
    """Show one more message and pause."""
    state = st.session_state
    state["pb_step"] = min(last, state["pb_step"] + 1)
    state["pb_playing"] = False


def play_all(last: int) -> None:
    """Jump to the last message."""
    st.session_state.update(pb_step=last, pb_playing=False)


def scrub_to(index: int) -> None:
    """Jump to the message at this index and pause."""
    st.session_state.update(pb_step=index, pb_playing=False)


def attack_types(source: dict) -> dict[str, str]:
    """Return the attack type of every attack text in the level or section."""
    return {attack["text"]: attack["type"] for package in source["attack_packages"] for attack in package}


def judge_text(event: dict, zones: dict[str, dict]) -> str:
    """Return the judge's one line verdict for a message, with the points it moved."""
    zone = zones.get(event["zone"], {"label": event["zone"], "points": 0})
    points = zone["points"]
    return {"blocked": f"\u2714 Judge: secret kept, +{points} pts",
            "leaked": f"\u2715 Judge: {zone['label']} leaked, -{points} pts",
            "served": f"\u2714 Judge: customer helped, +{points} pts",
            "refused": f"\u2298 Judge: customer turned away, -{points} pts"}[event["outcome"]]


def show_chat(events: list[dict], step: int, source: dict) -> None:
    """Show the messages up to step: customers and attackers on the left, the chatbot on the right."""
    zones = {zone["id"]: zone for zone in source["map_zones"]}
    types = attack_types(source)
    finished = step >= len(events) - 1
    with st.container(key="panel_chat"):
        with st.container(key="chat_head"):
            st.markdown(f"\u2615 **{common.BOT_NAME}**")
            st.caption("\u25cf Round over" if finished else "\u25cf Under attack")
        with st.container(key="chat_body"):
            for index, event in enumerate(events[: step + 1]):
                with st.container(key=f"sep_{index}"):
                    st.markdown(f"New chat \u00b7 {index + 1} of {len(events)}")
                attacker = event["sender"] == "attacker"
                with st.container(key=f"bub_{event['sender']}_{index}"):
                    kind = types.get(event["text"], "attack").replace("_", " ")
                    st.caption(f"Attacker \u00b7 {kind}" if attacker else "Customer")
                    st.text(event["text"])
                with st.container(key=f"bub_bot_{index}"):
                    st.caption(common.BOT_NAME)
                    st.text(event["reply"])
                with st.container(key=f"judge_{JUDGE_CLASS[event['outcome']]}_{index}"):
                    st.text(judge_text(event, zones))


def tally(events: list[dict], step: int, zones: dict[str, dict]) -> dict[str, int]:
    """Return the points kept, served and lost so far."""
    totals = {"kept": 0, "served": 0, "lost": 0}
    for event in events[: step + 1]:
        points = zones.get(event["zone"], {"points": 0})["points"]
        key = {"blocked": "kept", "served": "served"}.get(event["outcome"], "lost")
        totals[key] += points
    return totals


def map_marks(events: list[dict], step: int) -> tuple[dict, dict, tuple[str, str]]:
    """Return the lost zones, the good outcomes so far, and the zone in focus with how it is shown."""
    marks = {}
    for event in events[: step + 1]:
        if event["outcome"] in ("blocked", "served"):
            marks[event["zone"]] = "safe" if event["outcome"] == "blocked" else "served"
    now = events[step]
    return now["map"], marks, (now["zone"], "target" if now["sender"] == "attacker" else "asking")


def show_map(events: list[dict], step: int, source: dict) -> None:
    """Show the map as it is after this message, with its points tally and legend."""
    state, marks, focus = map_marks(events, step)
    zones = {zone["id"]: zone for zone in source["map_zones"]}
    totals = tally(events, step, zones)
    with st.container(key="panel_map"), st.container(key="sec_map"):
        st.subheader("System core")
        common.show_svg(build_map_svg(source["map_zones"], state=state, marks=marks, focus=focus))
        with st.container(key="tally"):
            kept, served, lost = st.columns(3)
            kept.metric("Secret pts kept", totals["kept"])
            served.metric("Public pts served", totals["served"])
            lost.metric("Points lost", f"-{totals['lost']}" if totals["lost"] else "0")
        common.show_svg(legend_svg([zone["ring"] for zone in source["map_zones"]]))


def show_rules_summary(run: dict, source: dict, step: int, count: int) -> None:
    """Show what the player chose for this round and what the attackers are after."""
    with st.container(key="panel_rules_used"):
        st.subheader("Your rules this round")
        if run["mode"] == "endless":
            st.text(run.get("player_rules") or "(no rules written)")
        else:
            labels = {rule["id"]: rule["label"] for rule in source["rules"]}
            chosen = run.get("chosen_rules") or []
            for rule_id in chosen:
                st.write(f"• {labels.get(rule_id, rule_id)}")
            if not chosen:
                st.write("No rules chosen")
        with st.container(key="goal"):
            st.markdown(f"**Attacker's goal.** {source['theme']}")
        st.caption(f"Message {step + 1} of {count}")


def show_controls(events: list[dict], step: int) -> None:
    """Show Pause or Resume, Next message, Play all, the speed selector and the scrubber."""
    state, last = st.session_state, len(events) - 1
    finished = step >= last
    play, nxt, every, speed = st.columns([1, 1, 1, 2])
    play.button("Pause" if state["pb_playing"] else "Resume", key="pb_toggle",
                on_click=toggle_play, disabled=finished)
    nxt.button("Next message", key="pb_next", on_click=next_message, args=(last,), disabled=finished)
    every.button("Play all", key="pb_all", on_click=play_all, args=(last,), disabled=finished)
    speed.radio("Speed", list(SPEEDS), index=1, key="pb_speed", horizontal=True)
    if last > 0:
        # The timer moves the step, so the slider is not driven through session state or on_change: a stale
        # value from the browser would look like the player dragging it back. A new key per step starts it at
        # the current message, so any other value it returns is the player's own drag.
        picked = st.slider("Message", 1, last + 1, value=step + 1, key=f"pb_slider_{step}")
        if picked != step + 1:
            scrub_to(picked - 1)
            st.rerun()


@st.fragment(run_every=TICK_SECONDS)
def playback_view() -> None:
    """Rules, map and chat for the current run. Only this part reruns on every tick, so the page stays calm."""
    run = st.session_state["run"]
    source = common.run_source(run)
    events = run["result"]["events"]
    if guide.active_step("playback", source):
        st.session_state["pb_playing"] = False  # the guide pauses the chat until its step is closed
    advance_if_due(events)
    step = st.session_state["pb_step"]
    show_controls(events, step)
    rules_col, map_col, chat_col = st.columns([10, 11, 11], gap="medium")
    with rules_col:
        show_rules_summary(run, source, step, len(events))
    with map_col:
        show_map(events, step, source)
    with chat_col, st.container(key="sec_chat"):
        show_chat(events, step, source)
        common.scroll_to_latest(f"{run['run_id']}-{step}")
    if step >= len(events) - 1 and st.button("See results", type="primary", key="pb_results"):
        common.goto("results")
        st.rerun()  # a button inside a fragment only reruns the fragment, so rerun the whole app


def playback_screen() -> None:
    """Show the chat playback of the current run."""
    run = st.session_state["run"]
    source = common.run_source(run)
    st.button("\u2190 Back", key="pb_back", on_click=common.goto, args=(BACK_SCREEN[run["mode"]],))
    guide.show("playback", source)
    common.eyebrow(f"{common.get_scenario(run['scenario_id'])['name']} \u00b7 {source['title']}", "playback")
    st.header("Watch the round")
    playback_view()


# ---- saving and loading ------------------------------------------------------------------------

def check_events(events: object) -> list[dict]:
    """Return the events of a save, raising ValueError if they are missing or malformed."""
    if not isinstance(events, list) or not events:
        raise ValueError("This save has no messages to replay.")
    for event in events:
        if not isinstance(event, dict) or any(key not in event for key in EVENT_KEYS):
            raise ValueError("This save has malformed messages.")
        if not all(isinstance(event[key], str) for key in EVENT_KEYS[:5]) or not isinstance(event["map"], dict):
            raise ValueError("This save has malformed messages.")
        if event["sender"] not in SENDERS or event["outcome"] not in OUTCOME_TEXT:
            raise ValueError("This save has malformed messages.")
    return events


def run_from_save(record: dict) -> dict:
    """Build a replay-only run from a parsed save file, raising ValueError if it does not fit this game."""
    result = record["result"] if isinstance(record.get("result"), dict) else record
    events = check_events(result.get("events"))
    mode = "endless" if record.get("mode") == "endless" else "level"
    scenario_id, source_id = str(record.get("scenario_id", "cafe")), str(record.get("level_id", ""))
    try:
        common.find_source(scenario_id, mode, source_id)
    except (ValueError, OSError, KeyError) as error:
        raise ValueError("This save is for a level that is not in this game.") from error
    chosen, written = record.get("chosen_rules"), record.get("player_rules")
    return {"run_id": str(uuid.uuid4()), "mode": mode, "scenario_id": scenario_id, "level_id": source_id,
            "chosen_rules": [rule for rule in chosen if isinstance(rule, str)] if isinstance(chosen, list) else None,
            "player_rules": written if isinstance(written, str) else None,
            "result": {"events": events}, "loaded": True, "recorded": True, "saved": False}


def load_game(key: str) -> None:
    """Read the uploaded save file and start its replay; show a message if it is not usable."""
    state = st.session_state
    uploaded = state.get(key)
    if uploaded is None:
        return
    try:
        state["run"] = run_from_save(data.import_game(uploaded.getvalue().decode("utf-8")))
    except (ValueError, UnicodeDecodeError) as error:
        state["load_error"] = str(error)
        return
    state.pop("load_error", None)
    common.start_playback()
    common.goto("playback")


def load_game_widget(key: str) -> None:
    """Show the Load my game uploader. The file is only replayed, never graded or stored."""
    st.file_uploader("Load my game", type="json", key=key, on_change=load_game, args=(key,))
    if st.session_state.get("load_error"):
        st.error(st.session_state["load_error"])


def save_record(run: dict) -> dict:
    """Return what Save my game writes: everything needed to replay the round."""
    keys = ("scenario_id", "mode", "level_id", "chosen_rules", "player_rules", "package_index", "result", "grade")
    return {key: run[key] for key in keys}


# ---- results -----------------------------------------------------------------------------------

def explain_endless(section: dict, result: dict) -> list[dict]:
    """Return one explanation per leak or refused customer of an Endless run."""
    labels = {zone["id"]: zone["label"] for zone in section["map_zones"]}
    attacks = {a["text"]: a for package in section["attack_packages"] for a in package}
    items = []
    for event in result["events"]:
        label = labels.get(event["zone"], event["zone"])
        if event["outcome"] == "leaked":
            kind = attacks.get(event["text"], {}).get("type", "unknown")
            items.append({"step": event["step"], "kind": "leak", "attack_type": kind,
                          "message": f"A {kind.replace('_', ' ')} attack made Beanie leak {label}.",
                          "caused_by_rules": [], "coach_tip": section.get("coach_tips", {}).get(kind, "")})
        elif event["outcome"] == "refused":
            items.append({"step": event["step"], "kind": "refusal",
                          "message": f"A real customer asked about {label} and did not get a helpful answer.",
                          "caused_by_rules": [], "coach_tip": data.REFUSAL_TIP})
    return items


def show_explanation(item: dict, rule_labels: dict[str, str], index: int = 0) -> None:
    """Show one leak or refusal with its attack type, the rule to blame and the coach tip."""
    with st.container(key=f"note_{item['kind']}_{index}"):
        st.markdown(f"**{'Leak' if item['kind'] == 'leak' else 'Turned away'}** \u00b7 message {item['step']}")
        st.text(item["message"])
        if item.get("attack_type"):
            st.caption(f"Attack type: {item['attack_type'].replace('_', ' ')}")
        blamed = [rule_labels.get(rule_id, rule_id) for rule_id in item.get("caused_by_rules", [])]
        if blamed:
            st.write("Rule that turned them away: " + ", ".join(blamed))
        if item.get("coach_tip"):
            st.info(f"Coach tip: {item['coach_tip']}")


def show_grade(grade: dict) -> None:
    """Show the grade banner."""
    kind, text = {
        "lose": ("fail", "Core hacked"), "perfect": ("perfect", f"Perfect {STAR * 3}"),
        "stars": ("pass", f"{STAR * grade['stars']} {grade['stars']} star{'s' if grade['stars'] > 1 else ''}"),
    }.get(grade["grade"], ("fail", "Fail"))
    with st.container(key=f"grade_{kind}"):
        st.markdown(text)
    if grade["grade"] == "lose":
        st.caption("The core was hacked, so this round is lost whatever the score.")
    elif grade["grade"] == "fail":
        st.warning("Not enough points. Try again with different rules.")


def show_scores(run: dict, source: dict) -> None:
    """Show security, helpfulness, the penalty and the score as separate numbers."""
    grade, result = run["grade"], run["result"]
    min_rules = source.get("min_rules", 0)
    security, helpfulness = result["security"], result["helpfulness"]
    lost_points = data.penalty(result, min_rules)
    cols = st.columns(4)
    cols[0].metric("Security", f"{grade['security_pct']}%")
    cols[0].caption(f"{security['earned']}/{security['total']} points")
    cols[1].metric("Helpfulness", f"{grade['helpfulness_pct']}%")
    cols[1].caption(f"{helpfulness['earned']}/{helpfulness['total']} points")
    cols[2].metric("Penalty", f"-{lost_points}" if lost_points else "0")
    cols[3].metric("Score", grade["score"])
    st.caption("Extra rules, and written rules longer than "
               f"{data.FREE_RULES_CHARS} characters, cost points.")


def show_results_block(run: dict, source: dict) -> None:
    """Show the grade, the scores and an explanation for every leak and refusal."""
    show_grade(run["grade"])
    show_scores(run, source)
    if run["mode"] == "endless":
        st.subheader("Your rules")
        st.text(run["player_rules"] or "(no rules written)")
        items = explain_endless(source, run["result"])
    else:
        items = data.explain_result(source, run["chosen_rules"], run["result"])
    for index, item in enumerate(items):
        show_explanation(item, {rule["id"]: rule["label"] for rule in source.get("rules", [])}, index)
    if run["grade"]["grade"] == "perfect" or run["grade"]["stars"] == 3:
        st.info(GREAT_RULES_TIP)


def replay() -> None:
    """Play the chat and the map again from the first message."""
    common.start_playback()
    common.goto("playback")


def next_level_id(run: dict) -> str | None:
    """Return the id of the level after this one, or None."""
    levels = common.get_scenario(run["scenario_id"])["levels"]
    ids = [level["id"] for level in levels]
    index = ids.index(run["level_id"]) if run["level_id"] in ids else -1
    return ids[index + 1] if 0 <= index < len(ids) - 1 else None


def show_navigation(run: dict) -> None:
    """Show Retry, Next (or the section list) and the way back."""
    endless = run["mode"] == "endless"
    retry, onward, back = st.columns(3)
    retry.button("Retry", key="rs_retry", on_click=common.goto, args=("endless" if endless else "level",))
    if endless:
        onward.button("Other sections", key="rs_next", on_click=common.goto, args=("endless_select",))
    else:
        following = next_level_id(run)
        onward.button("Next", key="rs_next", on_click=common.open_level, args=(following,),
                      disabled=following is None or run["grade"]["stars"] < 1)
    back.button("Home", key="rs_home", on_click=common.goto, args=("home",))


def record_args(run: dict, source: dict) -> dict:
    """Return the arguments of engine.storage.record_play for a finished run."""
    mode = common.storage_mode(run["mode"], run["level_id"])
    args = {"mode": mode, "scenario_id": run["scenario_id"], "level_id": run["level_id"],
            "run_id": run["run_id"], "session_id": st.session_state["session_id"],
            "attempt_number": run["attempt"], "result": run["result"], "grade": run["grade"]}
    if mode == "endless":
        model, temperature = data.ai_settings()
        args.update(player_rules=run["player_rules"], ai_model=model, ai_temperature=temperature)
    else:
        args["chosen_rules"] = run["chosen_rules"]
        if mode == "tutorial" and data.get_guide_steps(source):
            args["guide_skipped"] = st.session_state["guide_skipped"]
    return args


def consent_box(run: dict, source: dict) -> None:
    """Show the consent checkbox (unticked) and store the run, once, only if it is ticked."""
    ticked = st.checkbox(CONSENT_TEXT, key=f"consent_{run['run_id']}")
    if ticked and not run["recorded"]:
        run["recorded"] = True
        run["saved"] = data.record_play(**record_args(run, source))
    if ticked:
        st.caption("Thank you, your anonymous result was saved." if run["saved"]
                   else "Storage is not set up here, so nothing was saved.")


def show_save_load(run: dict) -> None:
    """Show Save my game and Load my game."""
    save, load = st.columns(2)
    with save:
        st.download_button("Save my game", data=data.export_game(save_record(run)),
                           file_name=f"chatbot-defense-{run['level_id']}.json", mime="application/json",
                           key="rs_save")
    with load:
        load_game_widget("load_results")


def loaded_results(run: dict) -> None:
    """Results screen of a loaded game: replay only, no grade and no storage."""
    st.info(LOADED_NOTICE)
    replay_col, back_col = st.columns(2)
    replay_col.button("Replay", key="rs_replay", on_click=replay)
    back_col.button("Home", key="rs_home", on_click=common.goto, args=("home",))


def results_screen() -> None:
    """Show the results of the current run."""
    run = st.session_state["run"]
    st.header("Results")
    if run["loaded"]:
        loaded_results(run)
        return
    source = common.run_source(run)
    guide.show("results", source)
    with st.container(key="sec_results"):
        show_results_block(run, source)
    with st.container(key="sec_replay_button"):
        st.button("Replay", key="rs_replay", on_click=replay)
    with st.container(key="sec_retry_next_buttons"):
        show_navigation(run)
    consent_box(run, source)
