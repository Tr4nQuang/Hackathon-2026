"""Turn a finished round into a JSON save file and back. The engine never writes files itself."""

import json

SAVE_FORMAT = "chatbot-defense-arena/1"


def export_game(record: dict) -> str:
    """Return the record as pretty JSON tagged with the save format."""
    return json.dumps({**record, "format": SAVE_FORMAT}, indent=2, ensure_ascii=False)


def import_game(text: str) -> dict:
    """Parse a save file, raising ValueError if it is not a valid save of this game."""
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError("This file is not valid JSON.") from error
    if not isinstance(data, dict) or data.get("format") != SAVE_FORMAT:
        raise ValueError("This file is not a Chatbot Defense Arena save.")
    # "events" may sit at the top or inside a nested "result", whichever way the interface builds the record.
    nested = data.get("result") if isinstance(data.get("result"), dict) else {}
    if not isinstance(data.get("events", nested.get("events")), list):
        raise ValueError("This save has no events to replay.")
    return data
