"""Tests for the browser saved progress object (levels and Endless). Run: python tests/test_progress.py"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import export  # noqa: E402
from engine.arena import endless as arena_endless  # noqa: E402
from ui.progress import (PROGRESS_VERSION, build_progress, endless_totals, merge_level,  # noqa: E402
                         merge_section, parse_progress, parse_run)

KNOWN = {"tutorial", "cafe_1", "cafe_2"}

# Levels: build, merge keeping the best.
levels = merge_level({}, "cafe_1", 2, 300, False)
levels = merge_level(levels, "cafe_1", 1, 450, False)
assert levels == {"cafe_1": {"stars": 2, "best": 450, "perfect": False}}
levels = merge_level(levels, "cafe_1", 3, 100, True)
assert levels["cafe_1"] == {"stars": 3, "best": 450, "perfect": True}
assert merge_level(levels, "cafe_1", 0, 0, False)["cafe_1"] == levels["cafe_1"]

# Endless: best points per section number and whether it was ever cleared.
endless = merge_section({}, 1, 800, True)
endless = merge_section(endless, 1, 500, False)
endless = merge_section(endless, 2, 300, False)
assert endless == {"1": {"best": 800, "cleared": True}, "2": {"best": 300, "cleared": False}}
endless = merge_section(endless, 2, 200, True)
assert endless["2"] == {"best": 300, "cleared": True}
assert endless_totals(endless) == (1100, 2)
assert endless_totals({}) == (0, 0)

# The saved object holds numbers only: no names, no rules, no player text.
saved = build_progress(levels, endless)
assert set(saved) == {"version", "levels", "endless"} and saved["version"] == PROGRESS_VERSION
assert parse_progress(json.dumps(saved), KNOWN) == (levels, endless)

# Invalid entries are dropped one by one.
mixed = {"version": PROGRESS_VERSION,
         "levels": {"cafe_1": {"stars": 2, "best": 10, "perfect": False},
                    "unknown_level": {"stars": 3, "best": 10, "perfect": True},
                    "cafe_2": {"stars": 4, "best": 10, "perfect": False},
                    "tutorial": {"stars": True, "best": 10, "perfect": False},
                    "x": "nope"},
         "endless": {"1": {"best": 500, "cleared": True},
                     "0": {"best": 5, "cleared": True},
                     "two": {"best": 5, "cleared": True},
                     "3": {"best": -1, "cleared": True},
                     "4": {"best": 5, "cleared": "yes"},
                     "5": {"best": 5, "cleared": True, "rules": "Never share the code"}}}
assert parse_progress(json.dumps(mixed), KNOWN) == ({"cafe_1": {"stars": 2, "best": 10, "perfect": False}},
                                                    {"1": {"best": 500, "cleared": True}})

# Malformed or old data is ignored as a whole.
for bad in (None, "", "not json", "[1, 2]", json.dumps({"levels": {}}),
            json.dumps({"version": 1, "stars": {"cafe_1": 2}}),
            json.dumps({"version": PROGRESS_VERSION, "levels": [1], "endless": "x"})):
    assert parse_progress(bad, KNOWN) == ({}, {}), bad

# The Endless run in progress: kept with the rules and the rows of the run file, validated field by field.
result = arena_endless.play_section(arena_endless.build_section(1, 7), "Never share any login, password or bank detail.")
row = export.section_row(result, "11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222", 120, "m")
run = {"section": 2, "score": 120, "passed": 1, "rules": "Never share any login.", "seed": 7, "run_id": "11111111-1111-1111-1111-111111111111",
       "over": False, "history": [{"n": 1, "world": "Café", "grade": "2 stars", "points": 120, "row": row}]}
assert "run" not in build_progress(levels, endless) and build_progress(levels, endless, run)["run"] == run
assert parse_run(json.dumps(build_progress(levels, endless, run))) == run
assert parse_progress(json.dumps(build_progress(levels, endless, run)), KNOWN) == (levels, endless)  # the bests are read as before
for field, value in (("section", 0), ("score", -1), ("passed", 2), ("rules", "x" * 1001), ("seed", 10**9 + 1), ("run_id", "nope"), ("over", "no"),
                     ("history", "x"), ("history", [{**run["history"][0], "row": {**row, "points": 1.5}}]), ("history", [{**run["history"][0], "n": 0}]),
                     ("history", [{**run["history"][0], "name": "Ann"}]), ("history", run["history"] * 201)):
    assert parse_run(json.dumps(build_progress({}, {}, {**run, field: value}))) is None, field
assert parse_run(json.dumps(build_progress({}, {}, {**run, "extra": 1}))) is None and parse_run(json.dumps(build_progress({}, {}, {k: v for k, v in run.items() if k != "seed"}))) is None
for bad in (None, "", "not json", json.dumps({"version": 1, "run": run}), json.dumps({"version": PROGRESS_VERSION}), json.dumps({"version": PROGRESS_VERSION, "run": [1]})):
    assert parse_run(bad) is None, bad
print("test_progress OK")
