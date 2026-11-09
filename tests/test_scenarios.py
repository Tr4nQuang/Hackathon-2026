"""Tests for the scenario loader. Run: python tests/test_scenarios.py"""

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.scenarios import get_guide_steps, list_scenarios, load_scenario, validate_scenario  # noqa: E402

GUIDE_TARGETS = ["story", "map", "theme", "rules", "start_button", "chat",
                 "results", "replay_button", "retry_next_buttons"]

cafe = load_scenario("cafe")


def rejects(change) -> bool:
    """Return True if validate_scenario raises ValueError on a copy changed by change()."""
    broken = copy.deepcopy(cafe)
    change(broken)
    try:
        validate_scenario(broken)
    except ValueError:
        return True
    return False


assert [lvl["id"] for lvl in cafe["levels"]][:4] == ["tutorial_1", "tutorial_2", "level_1", "level_2"]
assert {s["id"] for s in cafe["sections"]} >= {"endless_1", "endless_2"}
assert any(s["id"] == "cafe" for s in list_scenarios())

steps = get_guide_steps(cafe["levels"][0])
assert len(steps) == 10
assert all(step["target"] in GUIDE_TARGETS for step in steps)
assert steps[0]["target"] == "story" and steps[-1]["target"] == "retry_next_buttons"
assert get_guide_steps(cafe["levels"][1]) == []

assert rejects(lambda d: d.pop("levels"))
assert rejects(lambda d: d["levels"][0].pop("rules"))
assert rejects(lambda d: d["levels"][0]["map_zones"][0].update(ring="middle"))
assert rejects(lambda d: d["levels"][0]["attack_packages"][0][0].update(target_zone="nowhere"))
assert rejects(lambda d: d["levels"][0]["attack_packages"][0][0]["blocked_by"].append("no_such_rule"))
assert rejects(lambda d: d["levels"][0]["customer_questions"][0]["broken_by"].append("no_such_rule"))
assert rejects(lambda d: d["levels"][0]["customer_questions"][0].update(zone="nowhere"))
assert rejects(lambda d: d["levels"][0]["rules"][0].update(kind="magic"))
assert rejects(lambda d: d["levels"][0]["map_zones"][-1].update(points=999))
assert rejects(lambda d: d["sections"][0]["map_zones"][-1].update(points=999))
assert rejects(lambda d: d["sections"][0]["secrets_by_zone"].update(nowhere="X"))
assert not rejects(lambda d: d["levels"][0]["rules"][0].pop("kind", None))
try:
    load_scenario("no_such_world")
    raise AssertionError("missing scenario must raise")
except ValueError:
    pass
print("test_scenarios OK")
