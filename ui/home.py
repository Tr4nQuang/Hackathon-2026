"""The home screen: the pitch, the three game modes, and how a round is graded."""

import streamlit as st

from ui import common, data, saves, store
from ui.common import STAR
from ui.map import build_map_svg

EXAMPLE_STATE = {"hours": "served", "menu": "served", "student": "refused", "i1": "safe", "pii": "safe",
                 "srv": "breached", "bank": "target", "act": "safe"}
HERO_NOTE = ("Every business, person and secret is fictional. The tutorial and Level mode run without AI. Endless mode "
             "uses a live AI when USE_FAKE_AI=false and a Gemini key is set; otherwise it uses built-in attack scripts.")
GRADING_TEXT = ("Security is the share of attacked points you kept. Helpfulness is the share of public questions answered. "
                "Your overall score is the points you kept and served, minus 14% of the round's points for every ⚡ that "
                "did no work. The report never says which rules were the extra ones.")


def mode_card(key: str, eyebrow: str, title: str, text: str, left: str, right: str) -> None:
    """Show one game mode as a card."""
    with st.container(key=f"mode_{key}"):
        common.eyebrow(eyebrow, f"mode_{key}")
        st.subheader(title)
        st.write(text)
        st.caption(f"{left} · {right}")


def grade_tiles() -> None:
    """Show how a round is graded: Perfect, three star levels and a fail."""
    stars = dict(data.grade.STAR_THRESHOLDS)
    tiles = [("Perfect", "100% security, 100% helpfulness, no wasted compute"),
             (common.stars_text(3), f"Overall score {stars[3]}% or more"), (common.stars_text(2), f"Overall score {stars[2]}% or more"),
             (common.stars_text(1), f"Overall score {stars[1]}% or more, with security at least {data.grade.PASS_SECURITY}% and "
                                    f"helpfulness at least {data.grade.PASS_HELPFULNESS}%. Still a pass."),
             ("Fail", "Below that, or a breached core, which is an instant loss.")]
    for column, (title, text) in zip(st.columns(len(tiles)), tiles):
        with column, st.container(key=f"gtile_{title[:3]}"):
            st.markdown(f"**{title}**")
            st.write(text)


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
        tutorial, play, endless = st.columns(3)
        tutorial.button("Play the tutorial", type="primary", key="home_tutorial", on_click=common.start_tutorial, use_container_width=True)
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
        mode_card("endless", "Endless mode", "How long can you hold?", "Write your own rules. The attacker picks a new target "
                  "every section and gets sharper. One failed section ends the run.",
                  "Live AI ready" if data.live.is_live() else "Built-in scripts", f"Top score {top}" if top else "No records yet")
    common.eyebrow("Grading", "grading")
    st.subheader("Security and helpfulness, both at once")
    st.write(GRADING_TEXT)
    grade_tiles()
    saves.load_game_widget("load_home")
