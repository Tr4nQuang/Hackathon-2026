"""The level map: a winding path of numbered bubbles through the three businesses, each unlocked by passing the one before."""

import math

import streamlit as st

from ui import common, data, icons

BANNER_PX = 104  # height of the row of a business banner
ROW_PX = 122  # height of the row of a level
DISC_CENTRE_PX = 40  # where the centre of a level's bubble sits in its row
ZIGZAG_PERCENT = 26  # how far the path swings left and right of the middle
ZIGZAG_STEP = 1.15


def level_x(index: int) -> float:
    """Return where a level sits across the path, as a percentage of its width."""
    return 50 + ZIGZAG_PERCENT * math.sin(index * ZIGZAG_STEP)


def path_points(levels: list[dict]) -> tuple[list[tuple[float, int]], int]:
    """Return the centre of every level's bubble as (percent across, pixels down), and the height of the whole path."""
    points, y, last_world = [], 0, None
    for index, level in enumerate(levels):
        if level["world"] != last_world:
            y, last_world = y + BANNER_PX, level["world"]
        points.append((level_x(index), y + DISC_CENTRE_PX))
        y += ROW_PX
    return points, y


def path_svg(points: list[tuple[float, int]], height: int) -> str:
    """Return the dotted line that winds through the bubbles. It is stretched across the width, so x is in percent."""
    parts = []
    for k, (x, y) in enumerate(points):
        if k == 0:
            parts.append(f"M{x:.1f} {y}")
        else:
            middle = (points[k - 1][1] + y) / 2
            parts.append(f"C{points[k - 1][0]:.1f} {middle} {x:.1f} {middle} {x:.1f} {y}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 {height}" preserveAspectRatio="none" aria-hidden="true" '
            f'style="width:100%;height:{height}px;display:block"><path d="{"".join(parts)}" fill="none" '
            f'style="stroke:var(--line,#d2dbe3)" stroke-width="6" stroke-linecap="round" stroke-dasharray="2 14" '
            f'vector-effect="non-scaling-stroke"/></svg>')


def position_css(count: int) -> str:
    """Return the CSS that puts each level's bubble at its place across the path."""
    rules = " ".join(f".st-key-lvl_{index} {{ left: {level_x(index):.1f}%; }}" for index in range(count))
    return f"<style>{rules}</style>"


def level_state_name(index: int, info: dict, first_open: int) -> str:
    """Return the look of a level's bubble: locked, perfect, done, next (the one to play now) or open."""
    if not info["unlocked"]:
        return "locked"
    return "perfect" if info["perfect"] else "done" if info["done"] else "next" if index == first_open else "open"


def level_bubble(index: int, levels: list[dict], progress: dict, first_open: int) -> None:
    """Show one level as a numbered bubble you press to play, with the stars earned and the title below."""
    level = levels[index]
    info = common.level_state(index, levels, progress)
    state = level_state_name(index, info, first_open)
    with st.container(key=f"lvlrow_{index}"), st.container(key=f"lvl_{index}"):
        with st.container(key=f"disc_{state}_{index}"):
            st.button("\U0001f512" if state == "locked" else str(index + 1), key=f"play_{level['id']}", disabled=state == "locked",
                      on_click=common.begin_try, args=(level["id"],), help=f"Level {index + 1}: {level['title']}")
        if info["done"]:
            with st.container(key=f"lvlstars_{index}"):
                st.caption(common.stars_text(info["stars"]))
        with st.container(key=f"lvltitle_{index}"):
            st.markdown(f"**{level['title']}**" + (" · Perfect" if info["perfect"] else ""))


def levels_screen() -> None:
    """Show the level path with a banner for each business."""
    progress = st.session_state["progress"]
    levels = data.content.get_levels()
    states = [common.level_state(i, levels, progress) for i in range(len(levels))]
    first_open = next((i for i, info in enumerate(states) if info["unlocked"] and not info["done"]), -1)
    total = sum(info["stars"] for info in states)
    with st.container(key="levelhead"):
        common.eyebrow(f"Level mode · {total}/{3 * len(levels)} stars", "levels")
        st.header("Defend all three businesses")
        st.write("Clear a level with at least 1 star to unlock the next. Each try draws one of "
                 f"{data.content.packages_per_level()} attack packages, so the attacks change between tries. From level 4 you can block visitors, "
                 "and some levels hide a VIP client.")
    st.html(position_css(len(levels)))
    points, height = path_points(levels)
    with st.container(key="levelpath"):
        with st.container(key="pathsvg"):
            common.show_svg(path_svg(points, height))
        for world_id in data.content.world_order():
            world = data.content.get_world(world_id)
            mine = [i for i, level in enumerate(levels) if level["world"] == world_id]
            done = sum(states[i]["done"] for i in mine)
            with st.container(key=f"worldrow_{world_id}"), st.container(key=f"world_{world_id}"):
                st.markdown(icons.heading(world_id, world["name"], f"{world['short']} · {done}/{len(mine)} cleared"), unsafe_allow_html=True)
            for index in mine:
                level_bubble(index, levels, progress, first_open)
