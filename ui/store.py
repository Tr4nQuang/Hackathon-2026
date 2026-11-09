"""The record board for the Streamlit screens: the shared board file of engine/records.py, through ui/data.py."""

from ui import data

RECORDS_PATH = data.board.DEFAULT_PATH  # tests point this at a temporary file
MAX_NAME = data.board.MAX_NAME


def load_records() -> list[dict]:
    """Return the record board, best first."""
    return data.board.load_records(RECORDS_PATH)


def top_score() -> int | None:
    """Return the best score on the board, or None when it is empty."""
    return data.board.top_score(RECORDS_PATH)


def submit_record(name: str, score: int, sections: int) -> str:
    """Add a run to the record board and return a message for the player."""
    return data.board.submit_record(name, score, sections, RECORDS_PATH)
