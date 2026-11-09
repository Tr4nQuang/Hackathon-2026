"""Tests for the browser saved progress object. Run: python tests/test_progress.py"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.progress import PROGRESS_VERSION, build_progress, merge_stars, parse_progress  # noqa: E402

KNOWN = {"tutorial_1", "tutorial_2", "level_1"}

saved = build_progress({"tutorial_1": 2})
assert saved == {"version": PROGRESS_VERSION, "stars": {"tutorial_1": 2}}
assert set(saved) == {"version", "stars"}  # nothing else, no player text

stars = merge_stars({"tutorial_1": 2}, "tutorial_1", 1)
assert stars == {"tutorial_1": 2}
stars = merge_stars(stars, "tutorial_1", 3)
assert stars == {"tutorial_1": 3}
assert merge_stars(stars, "level_1", 0) == {"tutorial_1": 3}
assert merge_stars({}, "level_1", 1) == {"level_1": 1}

text = json.dumps(build_progress({"tutorial_1": 3, "level_1": 1}))
assert parse_progress(text, KNOWN) == {"tutorial_1": 3, "level_1": 1}
mixed = json.dumps({"version": PROGRESS_VERSION, "stars": {"tutorial_1": 2, "unknown_level": 3, "tutorial_2": 4,
                                                           "level_1": "3", "level_2": True}})
assert parse_progress(mixed, KNOWN) == {"tutorial_1": 2}
for bad in (None, "", "not json", "[1, 2]", json.dumps({"stars": {"tutorial_1": 2}}),
            json.dumps({"version": 99, "stars": {"tutorial_1": 2}}),
            json.dumps({"version": PROGRESS_VERSION, "stars": [1, 2]}),
            json.dumps({"version": PROGRESS_VERSION, "stars": {"tutorial_1": -1}})):
    assert parse_progress(bad, KNOWN) == {}, bad
print("test_progress OK")
