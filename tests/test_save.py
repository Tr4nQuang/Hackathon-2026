"""Tests for game export and import. Run: python tests/test_save.py"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.level import run_level  # noqa: E402
from engine.save import SAVE_FORMAT, export_game, import_game  # noqa: E402
from engine.scenarios import load_scenario  # noqa: E402

tutorial = load_scenario("cafe")["levels"][0]
result = run_level(tutorial, ["no_internal_codes"], 0)
record = {"scenario_id": "cafe", "level_id": tutorial["id"], "chosen_rules": ["no_internal_codes"], **result}

text = export_game(record)
assert json.loads(text)["format"] == SAVE_FORMAT and "\n  " in text
loaded = import_game(text)
assert loaded == {**record, "format": SAVE_FORMAT}
assert "format" not in record

nested = export_game({"level_id": "tutorial_1", "result": result})
assert import_game(nested)["result"]["events"] == result["events"]

bad_inputs = [
    "not json at all",
    "[1, 2, 3]",
    json.dumps({"events": []}),
    json.dumps({"format": "something-else/1", "events": []}),
    json.dumps({"format": SAVE_FORMAT}),
    json.dumps({"format": SAVE_FORMAT, "events": "nope"}),
]
for bad in bad_inputs:
    try:
        import_game(bad)
        raise AssertionError(f"should reject: {bad}")
    except ValueError:
        pass
print("test_save OK")
