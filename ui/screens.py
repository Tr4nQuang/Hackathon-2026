"""Home, level select and level screens. They use st.session_state and reach the engine only through ui.data."""

import streamlit as st

from ui import common, data, guide, progress
from ui.common import PERSONAL_DATA_NOTICE, STAR
from ui.map import build_map_svg, legend_svg

STATUS_TEXT = {"open": "▶ Open", "locked": "\U0001f512 Locked"}
HERO_NOTE = "Every business, person and secret here is fictional. Level mode needs no AI and no key."


def level_status(levels: list[dict], index: int, progress: dict) -> str:
    """Return "cleared", "open" or "locked" for the level at the given index."""
    if progress.get(levels[index]["id"], 0) >= 1:
        return "cleared"
    if index == 0 or progress.get(levels[index - 1]["id"], 0) >= 1:
        return "open"
    return "locked"


def rule_key(level_id: str, rule_id: str) -> str:
    """Return the session state key of a rule toggle."""
    return f"rule_{level_id}_{rule_id}"


def selected_rules(level: dict) -> list[str]:
    """Return the ids of the rules the player switched on, in list order."""
    return [rule["id"] for rule in level["rules"]
            if st.session_state.get(rule_key(level["id"], rule["id"]))]


def start_round() -> None:
    """Run the chosen level with the selected rules and move to the playback screen."""
    scenario = common.get_scenario()
    level = common.find_by_id(scenario["levels"], st.session_state["level_id"])
    chosen = selected_rules(level)
    package_index = data.pick_package(level)
    result = data.run_level(level, chosen, package_index)
    grade = data.grade_level(result, level["min_rules"])
    common.new_run(scenario["id"], "level", level["id"], chosen, None, package_index, result, grade)
    common.goto("playback")


def start_tutorial() -> None:
    """Open the first level with its guide from step one."""
    guide.restart()
    common.open_level(common.get_scenario()["levels"][0]["id"])


def demo_map(level: dict) -> str:
    """Return an example map after an attack: one leak, one turned away customer, the rest safe or served."""
    zones = level["map_zones"]
    secrets = [z["id"] for z in zones if z["ring"] != "outer"]
    outer = [z["id"] for z in zones if z["ring"] == "outer"]
    lost = {secrets[0]: "lost", outer[0]: "lost"} if secrets and outer else {}
    marks = {**{zone: "served" for zone in outer[1:]}, **{zone: "safe" for zone in secrets[1:]}}
    return build_map_svg(zones, state=lost, marks=marks)


def mode_card(key: str, eyebrow: str, title: str, text: str, foot: str) -> None:
    """Show one game mode as a card."""
    with st.container(key=f"mode_{key}"):
        common.eyebrow(eyebrow, f"mode_{key}")
        st.subheader(title)
        st.write(text)
        st.caption(foot)


def grade_tiles() -> None:
    """Show how a round is graded."""
    stars = dict(data.STAR_THRESHOLDS)
    tiles = [("Perfect", "100% security and 100% helpfulness with no more rules than needed."),
             (STAR * 3, f"A score of {stars[3]} or more."), (STAR * 2, f"A score of {stars[2]} or more."),
             (STAR, f"A score of {stars[1]} or more. Still a pass."),
             ("Fail or lose", "A lower score, or the core was hacked. A breached core is an instant loss.")]
    for column, (title, text) in zip(st.columns(len(tiles)), tiles):
        with column, st.container(key=f"gtile_{title[:3]}"):
            st.markdown(f"**{title}**")
            st.write(text)


def clear_progress() -> None:
    """Forget the saved stars in this session and in the browser."""
    st.session_state.update(progress={}, confirm_reset=False)
    progress.request_save()


def continue_panel(levels: list[dict]) -> None:
    """Show Continue with the saved stars, and a Start over link that asks once before clearing."""
    stars = sum(st.session_state["progress"].values())
    st.button(f"Continue · {stars}/{3 * len(levels)} {STAR}", type="primary", key="home_continue",
              on_click=common.goto, args=("levels",), use_container_width=True)
    if not st.session_state.get("confirm_reset"):
        st.button("Start over", type="tertiary", key="home_start_over",
                  on_click=lambda: st.session_state.update(confirm_reset=True))
        return
    st.caption("Clear your saved stars and locked levels in this browser?")
    yes, cancel = st.columns(2)
    yes.button("Yes, start over", key="home_reset_yes", on_click=clear_progress, use_container_width=True)
    cancel.button("Cancel", key="home_reset_no", on_click=lambda: st.session_state.update(confirm_reset=False),
                  use_container_width=True)


def home_screen() -> None:
    """Show the pitch, the three game modes and how a round is graded."""
    scenario = common.get_scenario()
    levels, sections = scenario["levels"], scenario.get("sections", [])
    text_col, map_col = st.columns([11, 9], gap="large")
    with text_col, st.container(key="hero"):
        common.eyebrow("natHacks 2026 · Defense & Security", "hero")
        st.markdown("# Keep the secrets safe. **Keep the customers happy.**")
        with st.container(key="lede"):
            st.write("You are the blue team for a business chatbot. Write its rules, then watch attackers go after "
                     "what it knows while real customers still need answers. The closer to the core, the more it is "
                     "worth. Opening hours sit at the edge, admin passwords at the centre.")
        saved = bool(st.session_state["progress"])
        if saved:
            continue_panel(levels)
        tutorial, play, endless = st.columns(3)
        tutorial.button("Play the tutorial", type="secondary" if saved else "primary", key="home_tutorial",
                        on_click=start_tutorial, use_container_width=True)
        play.button("Level mode", key="home_play", on_click=common.goto, args=("levels",), use_container_width=True)
        endless.button("Endless mode", key="home_endless", on_click=common.goto, args=("endless_select",),
                       disabled=not sections, use_container_width=True)
        st.caption(HERO_NOTE)
    with map_col:
        common.show_svg(demo_map(levels[0]))
    first, second, third = st.columns(3, gap="medium")
    with first:
        mode_card("tutorial", "Start here", "Tutorial", "One guided round. Learn the system core map, the rules "
                  "and the two sided score.", "10 steps · about 3 minutes")
    with second:
        mode_card("levels", "Level mode", f"{len(levels)} levels", "Pick rules from a list. A random attack package "
                  "is drawn each try, and extra rules cost points.", "Scripted, no AI needed")
    with third:
        mode_card("endless", "Endless mode", "Write your own rules", "A real AI plays the chatbot and hand written "
                  "attackers go after it.", f"{len(sections)} sections · needs a Gemini key for real AI")
    common.eyebrow("Grading", "grading")
    st.subheader("Security and helpfulness, both at once")
    st.write("Security is the share of secret points you kept. Helpfulness is the share of public questions "
             "answered. Refusing everything fails, and so does leaking.")
    grade_tiles()



def level_card(levels: list[dict], index: int, progress: dict, first_open: int) -> None:
    """Show one level on the level path: a numbered disc, the title and theme, and a Play button."""
    level, status = levels[index], level_status(levels, index, progress)
    stars = progress.get(level["id"], 0)
    state = {"locked": "locked", "cleared": "perfect" if stars == 3 else "done"}.get(status, "next" if index == first_open else "open")
    with st.container(key=f"lvl_{index}"):
        disc, info, action = st.columns([1, 6, 2], vertical_alignment="center")
        with disc, st.container(key=f"disc_{state}_{index}"):
            st.markdown("\U0001f512" if status == "locked" else str(index + 1))
        with info:
            st.subheader(level["title"])
            st.write(level["theme"])
            st.caption(f"{STAR * stars} Cleared" if status == "cleared" else STATUS_TEXT[status])
        action.button("Play" if status != "cleared" else "Play again", key=f"play_{level['id']}",
                      disabled=status == "locked", on_click=common.open_level, args=(level["id"],),
                      type="primary" if state == "next" else "secondary", use_container_width=True)


def level_select_screen() -> None:
    """Show every level with its status; the next level opens after a pass."""
    scenario = common.get_scenario()
    levels, progress = scenario["levels"], st.session_state["progress"]
    total = sum(progress.get(level["id"], 0) for level in levels)
    first_open = next((i for i in range(len(levels)) if level_status(levels, i, progress) == "open"), -1)
    st.button("← Home", key="levels_back", on_click=common.goto, args=("home",))
    common.eyebrow(f"Level mode · {total}/{3 * len(levels)} stars", "levels")
    st.header(f"Defend {scenario['name']}")
    st.write("Clear a level with at least one star to unlock the next. Each try draws a random attack package.")
    for index in range(len(levels)):
        level_card(levels, index, progress, first_open)


def rule_card(level: dict, rule: dict) -> None:
    """Show one rule as a card: a toggle with the rule's name and its sentence under it."""
    with st.container(key=f"rcard_{rule['id']}"):
        st.toggle(rule["label"], key=rule_key(level["id"], rule["id"]))
        st.write(rule["text"])


def rules_panel(level: dict) -> None:
    """Show the rule cards, the count and the cost note, and the Start button."""
    with st.container(key="panel_rules"):
        with st.container(key="sec_rules"):
            st.subheader("Rule shop")
            st.caption("Each rule is a sentence added to Beanie's instructions. Extra rules cost points.")
            for rule in level["rules"]:
                rule_card(level, rule)
            with st.container(key="budget"):
                st.write(f"Rules selected: {len(selected_rules(level))}")
            st.caption(PERSONAL_DATA_NOTICE)
        with st.container(key="sec_start_button"):
            st.button("Start", type="primary", key="start_run", on_click=start_round, use_container_width=True)


def map_panel(zones: list[dict]) -> None:
    """Show the empty system core map with its legend."""
    with st.container(key="panel_map"), st.container(key="sec_map"):
        st.subheader("System core")
        common.show_svg(build_map_svg(zones))
        common.show_svg(legend_svg([zone["ring"] for zone in zones]))


def chat_waiting() -> None:
    """Show the chat window before the round: it fills in on the next screen."""
    with st.container(key="panel_chat"):
        with st.container(key="chat_head"):
            st.markdown(f"☕ **{common.BOT_NAME}**")
            st.caption("● Waiting for your rules")
        with st.container(key="chat_body"):
            st.caption("Choose your rules, then press Start. Attackers and customers show up here, one chat at a time.")


def level_screen() -> None:
    """Show the story, the attacker's goal, the rule shop, the map and the chat window of the current level."""
    scenario = common.get_scenario()
    level = common.find_by_id(scenario["levels"], st.session_state["level_id"])
    back_col, help_col, _ = st.columns([1, 1, 6])
    back_col.button("← Levels", key="level_back", on_click=common.goto, args=("levels",))
    if data.get_guide_steps(level):
        help_col.button("Help", key="level_help", on_click=guide.restart)
    guide.show("level", level)
    with st.container(key="sec_story"):
        common.eyebrow(scenario["name"], "level")
        st.header(level["title"])
        st.write(level.get("story") or scenario["description"])
    with st.container(key="sec_theme"), st.container(key="goal"):
        st.markdown(f"**Attacker's goal.** {level['theme']}")
    rules_col, map_col, chat_col = st.columns([10, 11, 11], gap="medium")
    with rules_col:
        rules_panel(level)
    with map_col:
        map_panel(level["map_zones"])
    with chat_col:
        chat_waiting()
