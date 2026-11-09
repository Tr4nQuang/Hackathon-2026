"""The record board: the best Endless runs that were saved on this computer."""

import streamlit as st

from ui import common, store

BOARD_NOTE = "Saved on this computer only. Scores from other computers are not shown here."
EMPTY_NOTE = "No records yet. Finish an Endless run to set the first one."


def board_rows(rows: list[dict], my_name: str) -> list[dict]:
    """Return the board as table rows. The player's own row says (you). Names stay plain text in a table, never HTML."""
    mine = (my_name or "").strip().lower()
    return [{"#": place, "Player": row["name"] + (" (you)" if mine and row["name"].lower() == mine else ""),
             "Best": row["best"], "Sections": row.get("sections")} for place, row in enumerate(rows, start=1)]


def board_panel() -> None:
    """Show the record board with a note about where it is kept."""
    rows = store.load_records()
    st.subheader("Record board")
    st.caption(BOARD_NOTE)
    if rows:
        st.dataframe(board_rows(rows, st.session_state.get("player_name", "")), hide_index=True, width="stretch")
    else:
        st.caption(EMPTY_NOTE)


def records_screen() -> None:
    """Show the record board on its own page."""
    _, middle, _ = st.columns([1, 8, 1])
    with middle:
        common.eyebrow("Endless mode", "records")
        st.header("Record board")
        with st.container(key="panel_board"):
            board_panel()
        st.button("Play Endless", type="primary", key="rec_play", on_click=common.open_place, args=("endless",))
