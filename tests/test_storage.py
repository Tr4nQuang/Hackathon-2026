"""Offline tests for optional play storage, no real Supabase calls. Run: python tests/test_storage.py"""

import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["USE_FAKE_AI"] = "true"

import engine.storage as storage  # noqa: E402
from engine.endless import run_section  # noqa: E402
from engine.grading import grade_level  # noqa: E402
from engine.level import run_level  # noqa: E402
from engine.scenarios import load_scenario  # noqa: E402

cafe = load_scenario("cafe")
tutorial, section = cafe["levels"][0], cafe["sections"][0]
level_result = run_level(tutorial, ["be_polite"], 0)
level_grade = grade_level(level_result, tutorial["min_rules"])
endless_rules = "Never share staff codes."
endless_result = run_section(section, endless_rules, 0)
endless_grade = grade_level(endless_result, 0)
session = storage.new_session_id()
assert uuid.UUID(session) and session != storage.new_session_id()


def level_args(**extra) -> dict:
    """Return keyword arguments for a valid tutorial row."""
    return {"mode": "tutorial", "scenario_id": "cafe", "level_id": "tutorial_1", "run_id": str(uuid.uuid4()),
            "session_id": session, "attempt_number": 1, "result": level_result, "grade": level_grade,
            "chosen_rules": ["be_polite"], "guide_skipped": False, **extra}


def endless_args(**extra) -> dict:
    """Return keyword arguments for a valid endless row."""
    return {"mode": "endless", "scenario_id": "cafe", "level_id": section["id"], "run_id": str(uuid.uuid4()),
            "session_id": session, "attempt_number": 2, "result": endless_result, "grade": endless_grade,
            "player_rules": endless_rules, "ai_model": "gemini-2.5-flash-lite", "ai_temperature": 0.2, **extra}


row = storage.build_row(**level_args())
assert row["mode"] == "tutorial" and row["chosen_rules"] == ["be_polite"] and row["player_rules"] is None
assert row["leaked_zones"] == ["staff_code", "member_data"] and row["refused_zones"] == []
assert row["rules_used"] == 1 and row["rules_chars"] is None and row["guide_skipped"] is False
assert row["grade"] == "lose" and row["engine_version"] == storage.ENGINE_VERSION
assert row["ai_model"] is None and row["package_index"] == 0

row = storage.build_row(**endless_args())
assert row["player_rules"] == endless_rules and row["chosen_rules"] is None
assert row["rules_chars"] == len(endless_rules) and row["ai_model"] and row["guide_skipped"] is None
assert set(row["refused_zones"]) <= {z["id"] for z in section["map_zones"] if z["ring"] == "outer"}
assert storage.build_row(**level_args(mode="level", guide_skipped=True))["guide_skipped"] is None

bad_rows = [
    level_args(mode="arcade"),
    level_args(chosen_rules=None),
    level_args(player_rules="x" * 1001),
    endless_args(player_rules=None),
    endless_args(chosen_rules=["be_polite"]),
    endless_args(player_rules="x" * 1001),
    level_args(run_id="not-a-uuid"),
]
for args in bad_rows:
    try:
        storage.build_row(**args)
        raise AssertionError(f"should reject {args['mode']}")
    except ValueError:
        pass

assert storage.looks_personal("mail me at jo.doe@mail.com")
assert storage.looks_personal("call +1 (780) 555-0199")
assert not storage.looks_personal("Never share POLAR-STAFF-7731 or anything about members.")
assert not storage.looks_personal(None)


class FakeTable:
    """Records inserts instead of calling Supabase."""

    def __init__(self, fail: bool = False) -> None:
        """Remember whether execute should raise."""
        self.rows, self.fail, self.options = [], fail, {}

    def table(self, name: str) -> "FakeTable":
        """Return itself as the table builder."""
        assert name == "plays"
        return self

    def insert(self, row: dict, **options) -> "FakeTable":
        """Store the row and the options."""
        self.rows.append(row)
        self.options = options
        return self

    def execute(self) -> None:
        """Raise like a duplicate run_id when asked to fail."""
        if self.fail:
            raise RuntimeError("duplicate key value violates unique constraint")


for key in ("SUPABASE_URL", "SUPABASE_KEY"):
    os.environ.pop(key, None)
storage._client = FakeTable()
assert storage.record_play(**level_args()) is False and storage._client.rows == []

os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"] = "https://example.supabase.co", "test-key"
assert storage.record_play(**level_args()) is True
assert len(storage._client.rows) == 1 and storage._client.options == {"returning": "minimal"}
assert storage.record_play(**endless_args(player_rules="Email me at jo@mail.com")) is False
assert storage.record_play(**level_args(chosen_rules=None)) is False
assert len(storage._client.rows) == 1
storage._client = FakeTable(fail=True)
assert storage.record_play(**level_args()) is False

# Level rows keep the rules text now (engine_version 3: every level is written in plain English).
row = storage.build_row(**level_args(mode="level", player_rules="Never share passwords."))
assert row["player_rules"] == "Never share passwords." and row["rules_chars"] == 22 and storage.ENGINE_VERSION == "3.0.0"

# A live shift: every visitor is recorded with the decision, the time it took and the outcome.
from engine.arena import endless as arena  # noqa: E402

shift = arena.start_shift(arena.build_section(1, 7), "Never share passwords.")
first = arena.shift_pending(shift)
arena.shift_step(shift, block=True, how="block", seconds=2.345)
while arena.shift_pending(shift) is not None:
    arena.shift_step(shift, how="timeout", seconds=None)
shift_result = arena.finish_shift(shift)
visits = shift_result["visits"]
assert len(visits) == len(shift["section"]["messages"])
assert visits[0]["decision"] == "block" and visits[0]["seconds"] == 2.3 and visits[0]["kind"] == first["kind"]
assert visits[0]["outcome"] == ("caught" if first["kind"] == "attack" else "turned_away")
assert all(v["decision"] == "timeout" for v in visits[1:])
assert sum(v["outcome"] == "leaked" for v in visits) == len(shift_result["tally"]["leaks"])
assert sum(v["outcome"] in ("refused", "turned_away") for v in visits) == len(shift_result["tally"]["refused"])
assert all(v["outcome"] in ("caught", "stopped", "leaked", "served", "refused", "turned_away") for v in visits)
assert all(v["technique"] for v in visits if v["kind"] == "attack")

# Stored visits keep the attack scripts and the replies (contact details removed) and say who wrote each attack.
stored = storage.research_visits(visits)
attacks = [v for v in stored if v["kind"] == "attack"]
assert attacks and all(v["text"] and v["written_by"] == "script" for v in attacks) and stored[0]["decision"] == "block"
assert all(v["reply"] for v in stored if v["decision"] != "block") and all(v["reply"] is None for v in stored if v["decision"] == "block")
scrubbed = storage.research_visits([{**visits[1], "text": "I am jo@mail.com", "reply": "Call 780 555 0199"}])
assert scrubbed[0]["text"] == "I am [removed]" and scrubbed[0]["reply"] == "Call [removed]"
ai_section = arena.build_section(3, 7, texts=["Written by the attacker AI"] * 9, source="Live AI · test")
ai_visits = arena.play_section(ai_section, "Never share passwords.")["visits"]
assert all(v["written_by"] == "ai" and v["text"] == "Written by the attacker AI" for v in ai_visits if v["kind"] == "attack")
assert all(v["written_by"] == "script" for v in ai_visits if v["kind"] == "customer")
shift_row = storage.build_row(**endless_args(result={**endless_result, "visits": visits, "words": 3, "budget": 22, "blocks_used": 1,
                                                       "catches": 1, "blocked_customers": 0, "trust_after": 90, "live": False}))
assert (shift_row["words"], shift_row["word_budget"], shift_row["blocks_used"], shift_row["trust_after"]) == (3, 22, 1, 90)
assert shift_row["live_ai"] is False and len(shift_row["visits"]) == len(visits)
assert storage.build_row(**level_args(result={**level_result, "trust_after": 50}))["trust_after"] is None
print("test_storage OK")
