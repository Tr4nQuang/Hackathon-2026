"""Small helpers shared by all screens: navigation, lookups and creating a finished run."""

import time
import uuid
from functools import lru_cache

import streamlit as st

from ui import data, progress

STAR = "★"
BOT_NAME = "Beanie"
PERSONAL_DATA_NOTICE = "Do not enter real personal information."


def show_svg(svg: str) -> None:
    """Show SVG built by ui.map. st.html strips SVG, so use st.markdown; the div keeps it a raw HTML block."""
    st.markdown(f"<div>{svg}</div>", unsafe_allow_html=True)


SCROLL_TO_TOP = (
    "<script>/* scroll {count} */(function () {{"
    "var main = document.querySelector('[data-testid=\"stMain\"]') || document.querySelector('section.main');"
    "if (main) {{ main.scrollTo(0, 0); }} window.scrollTo(0, 0);"
    "}})();</script>"
)


def scroll_to_top() -> None:
    """Scroll to the top of the page. The chat is long, so the next screen must not open halfway down."""
    state = st.session_state
    state["scroll_count"] = state.get("scroll_count", 0) + 1
    try:
        # Our own script, no user text in it. Streamlit only re-runs a script whose text changed, hence the count.
        st.html(SCROLL_TO_TOP.format(count=state["scroll_count"]), unsafe_allow_javascript=True)
    except TypeError:
        pass  # an older Streamlit without unsafe_allow_javascript: the scroll position simply stays


SCROLL_TO_LATEST = (
    "<script>/* latest {token} */(function () {{"
    "var chips = document.querySelectorAll('[class*=\"st-key-judge_\"]');"
    "if (chips.length) {{ chips[chips.length - 1].scrollIntoView({{block: 'nearest', behavior: 'smooth'}}); }}"
    "}})();</script>"
)


def scroll_to_latest(token: str) -> None:
    """Keep the newest chat message in view. The text changes with the token so the script runs again."""
    try:
        st.html(SCROLL_TO_LATEST.format(token=token), unsafe_allow_javascript=True)  # our own script
    except TypeError:
        pass  # an older Streamlit without unsafe_allow_javascript


def eyebrow(text: str, key: str) -> None:
    """Show a small uppercase line above a heading."""
    with st.container(key=f"eyebrow_{key}"):
        st.caption(text)


def goto(screen: str) -> None:
    """Switch to another screen (used as a button callback)."""
    st.session_state["screen"] = screen


def open_level(level_id: str) -> None:
    """Remember the chosen level and show its screen."""
    st.session_state["level_id"] = level_id
    goto("level")


@lru_cache(maxsize=4)
def get_scenario(scenario_id: str = "cafe") -> dict:
    """Load a scenario once. Callers must treat the result as read only."""
    return data.load_scenario(scenario_id)


def find_by_id(items: list[dict], item_id: str) -> dict:
    """Return the level or section with the given id."""
    for item in items:
        if item["id"] == item_id:
            return item
    raise ValueError(f"Unknown id: {item_id}")


def find_source(scenario_id: str, mode: str, source_id: str) -> dict:
    """Return the level (Level mode) or section (Endless mode) a run was played on."""
    scenario = get_scenario(scenario_id)
    return find_by_id(scenario["sections" if mode == "endless" else "levels"], source_id)


def run_source(run: dict) -> dict:
    """Return the level or section of a run."""
    return find_source(run["scenario_id"], run["mode"], run["level_id"])


def storage_mode(mode: str, source_id: str) -> str:
    """Return the storage mode: endless, tutorial (ids starting with tutorial) or level."""
    if mode == "endless":
        return "endless"
    return "tutorial" if source_id.startswith("tutorial") else "level"


def start_playback() -> None:
    """Show the first message of the current run and let the chat play on its own."""
    st.session_state.update(pb_step=0, pb_playing=True, pb_last=time.monotonic())


def new_run(scenario_id: str, mode: str, source_id: str, chosen_rules: list[str] | None,
            player_rules: str | None, package_index: int, result: dict, grade: dict) -> None:
    """Store a finished run, count the attempt, update level progress and start its playback."""
    state = st.session_state
    state["attempts"][source_id] = state["attempts"].get(source_id, 0) + 1
    if mode == "level" and grade["stars"] >= 1:
        state["progress"][source_id] = max(state["progress"].get(source_id, 0), grade["stars"])
        progress.request_save()
    state["run"] = {
        "run_id": str(uuid.uuid4()), "mode": mode, "scenario_id": scenario_id, "level_id": source_id,
        "chosen_rules": chosen_rules, "player_rules": player_rules, "package_index": package_index,
        "result": result, "grade": grade, "attempt": state["attempts"][source_id],
        "loaded": False, "recorded": False, "saved": False,
    }
    start_playback()
