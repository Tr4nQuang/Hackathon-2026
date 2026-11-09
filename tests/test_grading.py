"""Tests for level grading. Run: python tests/test_grading.py"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.grading import grade_level  # noqa: E402
from engine.level import run_level  # noqa: E402
from engine.scenarios import load_scenario  # noqa: E402


def result(sec: int, hel: int, used: int = 1, core: bool = False, chars: int | None = None) -> dict:
    """Build a minimal result with 100 points on each side."""
    data = {"security": {"earned": sec, "total": 100}, "helpfulness": {"earned": hel, "total": 100},
            "core_hacked": core, "rules_used": used}
    if chars is not None:
        data["rules_chars"] = chars
    return data


assert grade_level(result(100, 100), 1) == {"grade": "perfect", "stars": 3, "score": 100,
                                            "security_pct": 100, "helpfulness_pct": 100}
assert grade_level(result(100, 100, used=2), 1)["grade"] == "stars"
assert grade_level(result(100, 100, used=2), 1)["score"] == 95
assert grade_level(result(100, 100, used=4), 1)["score"] == 85
assert grade_level(result(90, 90), 1)["stars"] == 3
assert grade_level(result(80, 80), 1)["stars"] == 2
assert grade_level(result(60, 60), 1)["stars"] == 1
assert grade_level(result(50, 60), 1)["grade"] == "fail"
assert grade_level(result(100, 100, core=True), 1)["grade"] == "lose"
assert grade_level(result(0, 0, used=50), 1)["score"] == 0

# Length penalty: 2 points per started 100 characters above 400.
assert grade_level(result(100, 100, used=0, chars=400), 0)["grade"] == "perfect"
assert grade_level(result(100, 100, used=0, chars=401), 0)["score"] == 98
assert grade_level(result(100, 100, used=0, chars=401), 0)["grade"] == "stars"
assert grade_level(result(100, 100, used=0, chars=1000), 0)["score"] == 88

tutorial = load_scenario("cafe")["levels"][0]
min_rules = tutorial["min_rules"]
assert grade_level(run_level(tutorial, ["no_internal_codes"], 0), min_rules)["grade"] == "perfect"
assert grade_level(run_level(tutorial, ["refuse_all"], 0), min_rules)["grade"] == "fail"
assert grade_level(run_level(tutorial, ["be_polite"], 0), min_rules)["grade"] == "lose"

sample = json.loads((ROOT / "docs" / "sample_results.json").read_text(encoding="utf-8"))
for name, run in sample["samples"].items():
    assert grade_level(run_level(tutorial, run["chosen_rules"], 0), min_rules) == run["grade"], name
print("test_grading OK")
