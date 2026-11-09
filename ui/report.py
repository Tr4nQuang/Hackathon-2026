"""The round report: grade, scores, what got through, what to do next. Also Save my game, Load my game and consent."""

import streamlit as st

from ui import common, data, guide, saves
from ui.common import STAR

GREAT_RULES_TIP = "Even great rules can fail. Real businesses should never give their chatbot secrets it does not need."
CONSENT_TEXT = "Share my anonymous results to help research. No name or personal data is saved."
LOW_STATS = "Failed on compute: too many rules that did no work."


def defense_names(kinds: list[str]) -> str:
    """Return the names of missing defenses, for example 'guarding logins and passwords, ignoring identity claims'."""
    labels = data.content.rules_data()["defense_label"]
    return ", ".join(labels[kind] for kind in kinds)


def tally_notes(tally: dict, world: dict, covered: set[str] | None) -> list[dict]:
    """Say what got through and who was turned away. With covered=None (a live AI read the rules) it names no missing defense."""
    type_label = data.content.rules_data()["type_label"]
    notes = []
    for leak in tally["leaks"]:
        message, names = leak["message"], " and ".join(data.content.sector_of(world, sector_id)["name"].lower() for sector_id in leak["leaked"])
        action = data.content.sector_of(world, message["asset"])["kind"] == "action"
        missing = data.rules.missing_for(world, message, covered) if covered is not None else []
        text = f"**{message['attacker']}** {'got the bot to do' if action else 'got'} **{names}** with {type_label[message['type']].lower()}."
        if missing:
            text += f" Nothing in your rules covered {defense_names(missing)}."
        notes.append({"kind": "leak", "chip": "Action" if action else "Leak", "text": text})
    for refused in tally["refused"]:
        name = data.content.sector_of(world, refused["topic"])["name"].lower()
        notes.append({"kind": "refusal", "chip": "Turned away", "text": f"A customer asking about **{name}** got no answer."})
    return notes


def clean_note(wasted: bool) -> dict:
    """Return the note for a round with nothing to report."""
    return {"kind": "clean", "chip": "Clean", "text": "No leaks, no turned-away customers" + (", and no wasted compute" if wasted else "") + "."}


def report_notes(result: dict, world: dict) -> list[dict]:
    """Return the notes of a level round. It never says which rules were the unnecessary ones."""
    notes = tally_notes(result["tally"], world, data.rules.coverage(result["selected"], world))
    if result["excess"] > 0:
        lead = "Far more compute than this job needed." if result["excess"] >= 5 else "Some compute did no work."
        notes.append({"kind": "efficiency", "chip": "Efficiency", "text": f"{lead} It cost you {result['grade']['penalty']} points. "
                      "Think about which of your rules this attack team really needed."})
    return notes or [clean_note(result["excess"] == 0)]


def show_notes(notes: list[dict]) -> None:
    """Show the notes, one card each with a coloured edge."""
    for index, note in enumerate(notes):
        with st.container(key=f"note_{note['kind']}_{index}"):
            st.markdown(f"**{note['chip']}** · {note['text']}")


def show_badge(grade: dict) -> None:
    """Show the grade as a big badge with its stars."""
    kind = "perfect" if grade["key"] == "perfect" else "pass" if grade["pass"] else "fail"
    stars = f"  {STAR * grade['stars']}" if grade["pass"] else ""
    with st.container(key=f"grade_{kind}"):
        st.markdown(f"{grade['label']}{stars}")


def summary_text(result: dict, level: dict) -> str:
    """Return the one sentence under the badge."""
    grade = result["grade"]
    if grade["key"] == "breach":
        return "The core was breached, so the round ended on the spot. Protect the centre first."
    if grade["pass"]:
        return "Final level cleared. All three businesses are defended." if level["id"] == "level_12" else "Level passed."
    return LOW_STATS if grade["sec"] >= 50 and grade["help"] >= 30 else "Not enough to pass. Check the notes and the replay, then try again."


def show_stats(result: dict) -> None:
    """Show security, helpfulness, compute and the overall score as four tiles."""
    grade, score = result["grade"], result["score"]
    security, helpfulness, compute, overall = st.columns(4)
    security.metric("Security", f"{grade['sec']}%")
    security.caption(f"{score['kept']}/{score['at_stake']} pts kept")
    helpfulness.metric("Helpfulness", f"{grade['help']}%")
    helpfulness.caption(f"{score['served']}/{score['asked']} pts")
    compute.metric("Compute", f"{result['used']}⚡")
    compute.caption(data.grade.efficiency_label(result["excess"]))
    overall.metric("Overall", f"{grade['overall']}%")
    overall.caption(f"{result['points']} points")


def watch_replay() -> None:
    """Open the replay of this round."""
    state = st.session_state
    result = state["result"]
    state.update(replay_log=result["log"], replay_world=result["world_id"], replay_back="report", replay_loaded=False)
    common.start_playback()
    common.goto("replay")


def storage_args(result: dict, level: dict) -> dict:
    """Return the arguments of engine.storage.record_play for a finished level round."""
    mode = common.storage_mode(level["id"])
    args = {"mode": mode, "scenario_id": "arena", "level_id": level["id"], "run_id": result["run_id"],
            "session_id": st.session_state["session_id"], "attempt_number": result["attempt"],
            "result": data.storage_result(result), "grade": data.storage_grade(result), "chosen_rules": result["selected"]}
    if mode == "tutorial" and data.get_guide_steps(level):
        args["guide_skipped"] = st.session_state["guide_skipped"]
    return args


def consent_box(result: dict, level: dict) -> None:
    """Show the consent checkbox (unticked) and store the round, once, only if it is ticked."""
    ticked = st.checkbox(CONSENT_TEXT, key=f"consent_{result['run_id']}")
    if ticked and not result["recorded"]:
        result["recorded"] = True
        result["saved"] = data.record_play(**storage_args(result, level))
    if ticked:
        st.caption("Thank you, your anonymous result was saved." if result["saved"]
                   else "Storage is not set up here, so nothing was saved.")


def actions(result: dict, level: dict) -> None:
    """Show Watch replay, Try again, Next level or Go to Level mode, the level map and Close."""
    passed, tutorial = result["grade"]["pass"], bool(level.get("tutorial"))
    following = common.next_level_id(level["id"])
    with st.container(key="sec_replay_button"):
        st.button("Watch replay", type="primary", key="rp_replay", on_click=watch_replay)
    with st.container(key="sec_retry_next_buttons"):
        retry, onward, levels, close = st.columns(4)
        retry.button("Try again", key="rp_retry", on_click=common.retry_level, use_container_width=True)
        if tutorial:
            onward.button("Go to Level mode", key="rp_next", on_click=common.goto, args=("levels",), use_container_width=True)
        elif passed and following:
            onward.button("Next level", key="rp_next", on_click=common.begin_try, args=(following,), use_container_width=True)
        else:
            onward.empty()
        if not tutorial:
            levels.button("Level map", key="rp_levels", on_click=common.goto, args=("levels",), use_container_width=True)
        close.button("Close", key="rp_close", on_click=common.goto, args=("play",), use_container_width=True)


def report_screen() -> None:
    """Show the report of the round just played."""
    state = st.session_state
    level, result = data.content.get_level(state["level_id"]), state["result"]
    world = data.content.get_world(level["world"])
    guide.show("report", level)
    _, middle, _ = st.columns([1, 8, 1])
    with middle, st.container(key="panel_report"):
        with st.container(key="sec_results"):
            common.eyebrow(f"{common.level_title(level)} · script package {'ABCD'[result['package']]}", "report")
            show_badge(result["grade"])
            st.write(summary_text(result, level))
            show_stats(result)
            show_notes(report_notes(result, world))
            if result["grade"]["key"] == "perfect" or result["grade"]["stars"] == 3:
                st.info(GREAT_RULES_TIP)
        actions(result, level)
        consent_box(result, level)
        save, load = st.columns(2)
        with save:
            st.download_button("Save my game", data=data.export_game(saves.save_record(result, level)),
                               file_name=f"chatbot-defense-{level['id']}.json", mime="application/json", key="rp_save")
        with load:
            saves.load_game_widget("load_report")
