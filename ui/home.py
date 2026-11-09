"""The home screen: the pitch, the three game modes, and how a round is graded."""

import streamlit as st

from ui import common, data, endless, progress, store
from ui.common import STAR
from ui.map import build_map_svg

EXAMPLE_STATE = {"hours": "served", "menu": "served", "student": "refused", "i1": "safe", "pii": "safe",
                 "srv": "breached", "bank": "target", "act": "safe"}
HERO_NOTE = ("Every business, person and secret is fictional. The tutorial and Level mode run without AI. Endless mode "
             "uses a live AI when USE_FAKE_AI=false and a Gemini key is set; otherwise it uses built-in attack scripts.")
GRADING_TEXT = ("Security is the share of attacked points you kept. Helpfulness is the share of public questions answered. "
                "Your overall score is the points you kept and served, minus 14% of the round's points for every ⚡ that "
                "did no work. Leaks cap the grade whatever the score: an internal leak means 2 stars at most, and leaking personal "
                "data, money or doing a forbidden action fails the round. The report never says which rules were the extra ones.")


def mode_card(key: str, eyebrow: str, title: str, text: str, left: str, right: str) -> None:
    """Show one game mode as a card."""
    with st.container(key=f"mode_{key}"):
        common.eyebrow(eyebrow, f"mode_{key}")
        st.subheader(title)
        st.write(text)
        st.caption(f"{left} · {right}")


def star_title(count: int) -> str:
    """Return the stars as markdown: filled stars bold and empty stars italic, so CSS can colour them apart."""
    empty = 3 - count
    return f"**{STAR * count}**" + (f" *{common.NO_STAR * empty}*" if empty else "")  # the space is closed up in CSS


def grade_tiles() -> None:
    """Show how a round is graded: Perfect, three star levels and a fail."""
    stars = dict(data.grade.STAR_THRESHOLDS)
    tiles = [("perfect", "**Perfect**", "100% security, 100% helpfulness, no wasted compute"),
             ("s3", star_title(3), f"Overall score {stars[3]}% or more, and nothing leaked"),
             ("s2", star_title(2), f"Overall score {stars[2]}% or more. An internal leak caps you here"),
             ("s1", star_title(1), f"Overall score {stars[1]}% or more, with security at least {data.grade.PASS_SECURITY}% and "
                                   f"helpfulness at least {data.grade.PASS_HELPFULNESS}%. Still a pass."),
             ("fail", "**Fail**", "Below that, or any leak of personal data, money or a forbidden action. A breached core is an instant loss.")]
    for column, (key, title, text) in zip(st.columns(len(tiles)), tiles):
        with column, st.container(key=f"gtile_{key}"):
            st.markdown(title)
            st.write(text)


def continue_panel(cleared: int, total: int) -> None:
    """Show Continue with the saved progress, and a Start over link that asks once before clearing it."""
    state = st.session_state
    score, sections = progress.endless_totals(state.get("endless_best", {}))
    stars = sum(row["stars"] for row in state["progress"].values())
    st.button(f"Continue · {cleared}/{total} levels · {stars} {STAR}", type="primary", key="home_continue",
              on_click=common.goto, args=("levels",), use_container_width=True)
    saved = state.get("saved_run")
    if saved:
        st.button(f"Continue your Endless run · shift {saved['section']} · {saved['score']} points · trust {saved['trust']}" if not saved["over"] else
                  f"See your last Endless run · {saved['score']} points", key="home_resume_run", on_click=endless.resume_run,
                  use_container_width=True)
    if sections:
        st.caption(f"Endless saved: Score {score} · Cleared {sections}")
    if not state.get("home_confirm_reset"):
        st.button("Start over", type="tertiary", key="home_start_over", on_click=lambda: state.update(home_confirm_reset=True))
        return
    st.write("Erase all level and Endless progress saved in this browser?")
    yes, cancel, _ = st.columns([2, 2, 3])
    yes.button("Yes, start over", key="home_reset_yes", on_click=lambda: (progress.clear_saved(), state.update(home_confirm_reset=False)))
    cancel.button("Cancel", key="home_reset_no", on_click=lambda: state.update(home_confirm_reset=False))


def home_screen() -> None:
    """Show the pitch, the three game modes and how a round is graded."""
    state = st.session_state
    levels = data.content.get_levels()
    cleared = sum(1 for level in levels if state["progress"].get(level["id"], {}).get("stars", 0) > 0)
    text_col, map_col = st.columns([11, 9], gap="large")
    with text_col, st.container(key="hero"):
        common.eyebrow("natHacks 2026 · Defense & Security", "hero")
        st.markdown("# Every chatbot has a core. **Don't let it get hacked.**")
        with st.container(key="lede"):
            st.write("You're the blue team for a business chatbot. Choose or write its rules, then watch AI attackers go after "
                     "what it knows while real customers still need answers. The closer to the core, the more it is worth: "
                     "admin passwords, bank accounts, personal records and actions the bot should never take. Opening hours "
                     "sit at the edge.")
        saved = progress.has_saved()
        if saved:
            continue_panel(cleared, len(levels))
        tutorial, play, endless = st.columns(3)
        tutorial.button("Play the tutorial", type="secondary" if saved else "primary", key="home_tutorial", on_click=common.start_tutorial, use_container_width=True)
        play.button("Level mode", key="home_play", on_click=common.goto, args=("levels",), use_container_width=True)
        endless.button("Endless mode", key="home_endless", on_click=common.open_place, args=("endless",), use_container_width=True)
        st.caption(HERO_NOTE)
    with map_col:
        common.show_svg(build_map_svg(data.content.get_world("cafe"), EXAMPLE_STATE))
    first, second, third = st.columns(3, gap="medium")
    top = store.top_score()
    with first:
        mode_card("tutorial", "Start here", "Tutorial", "One guided round at Polar Bean Café. Learn the System Core map, "
                  "compute costs and two-way scoring.", "1 script package", "Done ✓" if "tutorial" in state["progress"] else "About 3 minutes")
    with second:
        mode_card("levels", "Level mode", f"{len(levels)} levels, 3 worlds", "Pick rule cards using as little compute as you can. "
                  "Every try brings a new shop and new attack scripts, and rules that do no work cost you stars.",
                  "Café · Dealership · University", f"{cleared}/{len(levels)} cleared")
    with third:
        mode_card("endless", "Endless mode · Siege", "How long can you hold?", "Guard a live chat, shift after shift. Your rules "
                  "must fit a shrinking word budget, visitors don't say who they are, and the attackers adapt to what you left out.",
                  "Live AI ready" if data.live.is_live() else "Built-in scripts", f"Top score {top}" if top else "No records yet")
    common.eyebrow("Grading", "grading")
    st.subheader("Security and helpfulness, both at once")
    st.write(GRADING_TEXT)
    grade_tiles()
