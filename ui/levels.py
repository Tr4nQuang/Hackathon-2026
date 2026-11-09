"""The level map: three businesses, twelve levels, each unlocked by passing the one before."""

import streamlit as st

from ui import common, data


def level_card(index: int, levels: list[dict], progress: dict, first_open: int) -> None:
    """Show one level: a numbered disc, the title and goal, its stars and a Play button."""
    level = levels[index]
    info = common.level_state(index, levels, progress)
    state = "locked" if not info["unlocked"] else "perfect" if info["perfect"] else "done" if info["done"] else "next" if index == first_open else "open"
    with st.container(key=f"lvl_{index}"):
        disc, text, action = st.columns([1, 6, 2], vertical_alignment="center")
        with disc, st.container(key=f"disc_{state}_{index}"):
            st.markdown("\U0001f512" if state == "locked" else str(index + 1))
        with text:
            st.subheader(level["title"] + (" · Perfect" if info["perfect"] else ""))
            st.write(level["goal"])
            st.caption(common.stars_text(info["stars"]) + " Cleared" if info["done"] else
                       ("\U0001f512 Locked" if state == "locked" else "▶ Open"))
        action.button("Play again" if info["done"] else "Play", key=f"play_{level['id']}", disabled=state == "locked",
                      type="primary" if state == "next" else "secondary", on_click=common.begin_try, args=(level["id"],),
                      use_container_width=True)


def levels_screen() -> None:
    """Show the level map with a banner for each business."""
    progress = st.session_state["progress"]
    levels = data.content.get_levels()
    states = [common.level_state(i, levels, progress) for i in range(len(levels))]
    first_open = next((i for i, info in enumerate(states) if info["unlocked"] and not info["done"]), -1)
    total = sum(info["stars"] for info in states)
    common.eyebrow(f"Level mode · {total}/{3 * len(levels)} stars", "levels")
    st.header("Defend all three businesses")
    st.write("Clear a level with at least 1 star to unlock the next. Each try draws one of "
             f"{data.content.packages_per_level()} script packages, so the attacks change between tries.")
    for world_id in data.content.world_order():
        world = data.content.get_world(world_id)
        mine = [i for i, level in enumerate(levels) if level["world"] == world_id]
        done = sum(states[i]["done"] for i in mine)
        with st.container(key=f"world_{world_id}"):
            st.subheader(f"{common.WORLD_ICON[world_id]} {world['name']}")
            st.caption(f"{world['short']} · {done}/{len(mine)} cleared")
        for index in mine:
            level_card(index, levels, progress, first_open)
