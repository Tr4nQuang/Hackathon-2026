"""Tests for the scripted level engine. Run: python tests/test_level.py"""

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.level import explain_result, pick_package, run_level  # noqa: E402
from engine.scenarios import load_scenario  # noqa: E402

cafe = load_scenario("cafe")
tutorial = cafe["levels"][0]
rings = {zone["id"]: zone["ring"] for zone in tutorial["map_zones"]}
secret_ids = [z for z, ring in rings.items() if ring != "outer"]
outer_ids = [z for z, ring in rings.items() if ring == "outer"]

assert pick_package(tutorial, random.Random(1)) == 0
for level in cafe["levels"]:
    assert 0 <= pick_package(level) < len(level["attack_packages"])

safe = run_level(tutorial, ["no_internal_codes"], 0)
assert all(state == "safe" for state in safe["events"][-1]["map"].values())
assert safe["security"]["earned"] == safe["security"]["total"] > 0
assert safe["helpfulness"]["earned"] == safe["helpfulness"]["total"] > 0
assert not safe["core_hacked"] and safe["rules_used"] == 1 and safe["package_index"] == 0

polite = run_level(tutorial, ["be_polite"], 0)
assert all(polite["events"][-1]["map"][z] == "lost" for z in secret_ids)
assert polite["core_hacked"] and polite["security"]["earned"] == 0

refuse = run_level(tutorial, ["refuse_all"], 0)
assert all(e["outcome"] == "blocked" for e in refuse["events"] if e["sender"] == "attacker")
assert all(refuse["events"][-1]["map"][z] == "lost" for z in outer_ids)
assert refuse["helpfulness"]["earned"] == 0 and refuse["security"]["earned"] == refuse["security"]["total"]

# Events alternate and the map after the last event matches the scores.
for result in (safe, polite, refuse):
    senders = [e["sender"] for e in result["events"]]
    assert senders[:4] == ["attacker", "customer", "attacker", "customer"]
    assert [e["step"] for e in result["events"]] == list(range(1, len(senders) + 1))
    final = result["events"][-1]["map"]
    points = {z["id"]: z["points"] for z in tutorial["map_zones"]}
    lost_points = sum(points[z] for z, state in final.items() if state == "lost")
    earned = result["security"]["earned"] + result["helpfulness"]["earned"]
    assert earned == result["security"]["total"] + result["helpfulness"]["total"] - lost_points

try:
    run_level(tutorial, ["no_such_rule"], 0)
    raise AssertionError("unknown rule must raise")
except ValueError:
    pass

items = explain_result(tutorial, ["refuse_all", "be_polite"], refuse)
refusals = [item for item in items if item["kind"] == "refusal"]
assert len(refusals) == len(outer_ids)
assert all(item["caused_by_rules"] == ["refuse_all"] for item in refusals)
leaks = explain_result(tutorial, ["be_polite"], polite)
assert leaks and all(item["kind"] == "leak" and item["attack_type"] and item["coach_tip"] for item in leaks)
assert explain_result(tutorial, ["no_internal_codes"], safe) == []

# Same shape and numbers as the hand made reference in docs/sample_results.json.
sample = json.loads((ROOT / "docs" / "sample_results.json").read_text(encoding="utf-8"))
for name, run in sample["samples"].items():
    real = run_level(tutorial, run["chosen_rules"], 0)
    expected = run["result"]
    for key in ("security", "helpfulness", "core_hacked", "rules_used", "package_index"):
        assert real[key] == expected[key], (name, key, real[key], expected[key])
    assert set(real["events"][0]) == set(expected["events"][0])
    assert real["events"][-1]["map"] == expected["events"][-1]["map"], name
print("test_level OK")
