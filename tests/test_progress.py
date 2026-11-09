"""Tests for the browser saved progress object (levels and Endless). Run: python tests/test_progress.py"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.progress import (PROGRESS_VERSION, build_progress, endless_totals, merge_level,  # noqa: E402
                         merge_section, parse_progress)

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
print("test_progress OK")
