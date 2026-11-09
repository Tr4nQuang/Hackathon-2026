"""Balance test: every level has a perfect rule set of size min_rules and traps never pay. Run: python tests/test_balance.py"""

import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.grading import grade_level  # noqa: E402
from engine.level import run_level  # noqa: E402
from engine.scenarios import list_scenarios, load_scenario  # noqa: E402


def grades(level: dict, rules: tuple[str, ...]) -> list[str]:
    """Return the grade of a rule set on every attack package of the level."""
    return [grade_level(run_level(level, list(rules), i), level["min_rules"])["grade"]
            for i in range(len(level["attack_packages"]))]


def check_ids(level: dict) -> None:
    """Assert every zone id and rule id used by the level exists."""
    zones = {zone["id"] for zone in level["map_zones"]}
    rules = {rule["id"] for rule in level["rules"]}
    for package in level["attack_packages"]:
        for attack in package:
            assert attack["target_zone"] in zones and set(attack["blocked_by"]) <= rules
    for question in level["customer_questions"]:
        assert question["zone"] in zones and set(question["broken_by"]) <= rules


def check_level(level: dict) -> tuple[str, ...]:
    """Assert the balance rules for one level and return its smallest perfect rule set."""
    check_ids(level)
    rule_ids = [rule["id"] for rule in level["rules"]]
    perfect = [subset for size in range(len(rule_ids) + 1)
               for subset in itertools.combinations(rule_ids, size)
               if all(grade == "perfect" for grade in grades(level, subset))]
    assert perfect, f"{level['id']}: no rule set is perfect on every package"
    assert len(perfect[0]) == level["min_rules"], (level["id"], perfect[0], level["min_rules"])
    for rule in level["rules"]:
        if rule.get("kind") == "trap":
            assert all(g in ("fail", "lose") for g in grades(level, (rule["id"],))), (level["id"], rule["id"])
            if level["id"].startswith("level_"):  # broad trap: blocks attacks but refuses a real customer
                assert any(rule["id"] in a["blocked_by"] for p in level["attack_packages"] for a in p)
                assert any(rule["id"] in q["broken_by"] for q in level["customer_questions"])
    assert sum(rule.get("kind") == "trap" for rule in level["rules"]) == 1, level["id"]
    return perfect[0]


for info in list_scenarios():
    for level in load_scenario(info["id"])["levels"]:
        print(f"{info['id']}/{level['id']}: smallest perfect set {list(check_level(level))}")
print("test_balance OK")
