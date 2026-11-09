"""Small helpers shared by all screens: navigation, progress, starting a try and a few page scripts."""

import time
import uuid

import streamlit as st

from ui import data

STAR = "★"
NO_STAR = "☆"
PERSONAL_DATA_NOTICE = "Do not enter real personal information. Everything here is fictional."
WORLD_ICON = {"cafe": "☕", "dealer": "\U0001f697", "uni": "\U0001f393"}

SCROLL_TO_TOP = (
    "<script>/* scroll {count} */(function () {{"
    "var main = document.querySelector('[data-testid=\"stMain\"]') || document.querySelector('section.main');"
    "if (main) {{ main.scrollTo(0, 0); }} window.scrollTo(0, 0);"
    "}})();</script>"
)
SCROLL_TO_LATEST = (
    "<script>/* latest {token} */(function () {{"
    "var body = document.querySelector('.st-key-chat_body');"
    "if (body) {{ body.scrollTo({{top: body.scrollHeight, behavior: 'smooth'}}); }}"
    "}})();</script>"
)


def show_svg(svg: str) -> None:
    """Show SVG built by ui.map. st.html strips SVG, so use st.markdown; the div keeps it a raw HTML block."""
    st.markdown(f"<div>{svg}</div>", unsafe_allow_html=True)


def run_script(script: str) -> None:
    """Run one of our own fixed scripts in the page. Streamlit only re-runs a script whose text changed."""
    try:
        st.html(script, unsafe_allow_javascript=True)
    except TypeError:
        pass  # an older Streamlit without unsafe_allow_javascript: the scroll position simply stays


def scroll_to_top() -> None:
    """Scroll to the top of the page when a screen opens."""
    state = st.session_state
    state["scroll_count"] = state.get("scroll_count", 0) + 1
    run_script(SCROLL_TO_TOP.format(count=state["scroll_count"]))


def scroll_to_latest(token: str) -> None:
    """Scroll the chat window (not the page) down to the newest entry."""
    run_script(SCROLL_TO_LATEST.format(token=token))


def eyebrow(text: str, key: str) -> None:
    """Show a small uppercase line above a heading."""
    with st.container(key=f"eyebrow_{key}"):
        st.caption(text)


def goto(screen: str) -> None:
    """Switch to another screen (used as a button callback)."""
    st.session_state["screen"] = screen


def open_place(screen: str) -> None:
    """Open a place from the top bar or the home page. A finished Endless run is left behind, so Endless starts at its lobby."""
    state = st.session_state
    if screen == "endless" and (state.get("endless") or {}).get("status") == "over":
        state["endless"] = None
    goto(screen)


def level_title(level: dict) -> str:
    """Return the heading of a level: Tutorial, or its number and name."""
    return "Tutorial" if level.get("tutorial") else f"Level {level['key']} \u00b7 {level['title']}"


def stars_text(count: int) -> str:
    """Return three stars, filled for the stars earned."""
    return STAR * count + NO_STAR * (3 - count)


# ---- levels and progress ----------------------------------------------------------------------

def level_state(index: int, levels: list[dict], progress: dict) -> dict:
    """Return whether a level is unlocked (the first, or after a pass on the one before), done and perfect."""
    mine = progress.get(levels[index]["id"])
    before = progress.get(levels[index - 1]["id"]) if index else None
    return {"unlocked": index == 0 or bool(before and before["stars"] > 0), "done": bool(mine and mine["stars"] > 0),
            "perfect": bool(mine and mine["perfect"]), "stars": mine["stars"] if mine else 0}


def record_progress(level: dict, result: dict) -> None:
    """Remember the best stars and points of a level, and that the tutorial was done."""
    state = st.session_state
    grade, passed = result["grade"], result["grade"]["pass"]
    if level.get("tutorial"):
        if passed:
            state["progress"]["tutorial"] = {"stars": grade["stars"], "best": result["points"], "perfect": grade["key"] == "perfect"}
        return
    old = state["progress"].get(level["id"], {"stars": 0, "best": 0, "perfect": False})
    state["progress"][level["id"]] = {"stars": max(old["stars"], grade["stars"] if passed else 0),
                                      "best": max(old["best"], result["points"]), "perfect": old["perfect"] or grade["key"] == "perfect"}


def begin_try(level_id: str) -> None:
    """Start a try of a level: draw a script package (not the last one) and build its shop, then open the play screen."""
    state = st.session_state
    level = data.content.get_level(level_id)
    package = data.play.pick_package(level, state["last_package"].get(level_id))
    state["last_package"][level_id] = package
    state.update(level_id=level_id, attempt=data.play.new_try(level, package), result=None,
                 try_no=state["try_no"] + 1, pb_step=0, pb_playing=False, screen="play")


def retry_level() -> None:
    """Try the same level again with new scripts and a new shop."""
    begin_try(st.session_state["level_id"])


def start_tutorial() -> None:
    """Open the tutorial from its first guide step."""
    from ui import guide  # imported here: guide imports this module

    guide.restart()
    begin_try("tutorial")


def next_level_id(level_id: str) -> str | None:
    """Return the id of the level after this one, or None after the last (and for the tutorial)."""
    ids = [level["id"] for level in data.content.get_levels()]
    return ids[ids.index(level_id) + 1] if level_id in ids and ids.index(level_id) < len(ids) - 1 else None


def storage_mode(level_id: str) -> str:
    """Return the storage mode of a level run: tutorial or level."""
    return "tutorial" if level_id == "tutorial" else "level"


def new_run_id() -> str:
    """Return a new id for a finished round."""
    return str(uuid.uuid4())


def start_playback() -> None:
    """Show the first entry of the current round and let the chat play on its own."""
    st.session_state.update(pb_step=0, pb_playing=True, pb_last=time.monotonic(), pb_auto=True, pb_end_since=None)
