"""Load and validate game content from the scenarios folder (contract: MASTER_PROMPT section 4)."""

import json
from pathlib import Path

SCENARIO_DIR = Path(__file__).resolve().parent.parent / "scenarios"
RINGS = ("outer", "inner", "sensitive", "core")
RULE_KINDS = ("defense", "decoy", "trap", "cosmetic")
ATTACK_TYPES = ("direct_question", "impersonation", "instruction_override",
                "transformation", "emotional", "combined")
TOP_KEYS = ("id", "name", "description", "levels")
LEVEL_KEYS = ("id", "title", "theme", "min_rules", "map_zones", "rules",
              "attack_packages", "customer_questions", "coach_tips")
SECTION_KEYS = ("id", "title", "theme", "map_zones", "business_prompt", "secrets_by_zone",
                "attack_packages", "customer_questions", "coach_tips")
ZONE_KEYS = ("id", "label", "ring", "points")
RULE_KEYS = ("id", "label", "text", "cost")
LEVEL_ATTACK_KEYS = ("text", "target_zone", "type", "blocked_by", "reply_if_blocked", "reply_if_leaked")
SECTION_ATTACK_KEYS = ("text", "target_zone", "type")
LEVEL_CUSTOMER_KEYS = ("text", "zone", "broken_by", "reply_ok", "reply_refused")
SECTION_CUSTOMER_KEYS = ("text", "zone", "expected_facts")


def _require(item: dict, keys: tuple[str, ...], where: str) -> None:
    """Raise ValueError if item is not an object or any key is missing."""
    if not isinstance(item, dict):
        raise ValueError(f"{where}: expected an object")
    missing = [key for key in keys if key not in item]
    if missing:
        raise ValueError(f"{where}: missing keys {missing}")


def _unique_ids(items: list[dict], where: str) -> set[str]:
    """Return the set of ids, raising ValueError on a duplicate."""
    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{where}: duplicate ids")
    return set(ids)


def _check_zones(zones: list[dict], where: str) -> dict[str, dict]:
    """Validate map zones and the outer versus secret points balance, return them by id."""
    for zone in zones:
        _require(zone, ZONE_KEYS, f"{where} zone")
        if zone["ring"] not in RINGS:
            raise ValueError(f"{where}: unknown ring {zone['ring']!r} on zone {zone['id']!r}")
    _unique_ids(zones, f"{where} map_zones")
    outer = sum(z["points"] for z in zones if z["ring"] == "outer")
    secret = sum(z["points"] for z in zones if z["ring"] != "outer")
    if outer < secret:
        raise ValueError(f"{where}: outer points {outer} are smaller than secret points {secret}")
    return {zone["id"]: zone for zone in zones}


def _check_zone_ref(zone_id: str, zones: dict[str, dict], outer: bool, where: str) -> None:
    """Raise ValueError for an unknown zone or a zone on the wrong side (public versus secret)."""
    if zone_id not in zones:
        raise ValueError(f"{where}: unknown zone id {zone_id!r}")
    if (zones[zone_id]["ring"] == "outer") != outer:
        raise ValueError(f"{where}: zone {zone_id!r} is on the wrong ring")


def _check_rule_refs(rule_ids: list[str], known: set[str], where: str) -> None:
    """Raise ValueError for any unknown rule id."""
    unknown = [rule_id for rule_id in rule_ids if rule_id not in known]
    if unknown:
        raise ValueError(f"{where}: unknown rule ids {unknown}")


def _check_attacks(packages: list, zones: dict, keys: tuple[str, ...], rules: set[str] | None, where: str) -> None:
    """Validate every attack in every package."""
    if not packages:
        raise ValueError(f"{where}: needs at least one attack package")
    for package in packages:
        for attack in package:
            _require(attack, keys, f"{where} attack")
            _check_zone_ref(attack["target_zone"], zones, False, f"{where} attack")
            if attack["type"] not in ATTACK_TYPES:
                raise ValueError(f"{where}: unknown attack type {attack['type']!r}")
            if rules is not None:
                _check_rule_refs(attack["blocked_by"], rules, f"{where} attack")


def _check_level(level: dict) -> None:
    """Validate one Level mode level."""
    _require(level, LEVEL_KEYS, "level")
    where = f"level {level['id']}"
    zones = _check_zones(level["map_zones"], where)
    for rule in level["rules"]:
        _require(rule, RULE_KEYS, f"{where} rule")
        if rule.get("kind", "defense") not in RULE_KINDS:
            raise ValueError(f"{where}: unknown rule kind {rule['kind']!r}")
    rules = _unique_ids(level["rules"], f"{where} rules")
    _check_attacks(level["attack_packages"], zones, LEVEL_ATTACK_KEYS, rules, where)
    for question in level["customer_questions"]:
        _require(question, LEVEL_CUSTOMER_KEYS, f"{where} customer")
        _check_zone_ref(question["zone"], zones, True, f"{where} customer")
        _check_rule_refs(question["broken_by"], rules, f"{where} customer")


def _check_section(section: dict) -> None:
    """Validate one Endless mode section."""
    _require(section, SECTION_KEYS, "section")
    where = f"section {section['id']}"
    zones = _check_zones(section["map_zones"], where)
    for zone_id in section["secrets_by_zone"]:
        _check_zone_ref(zone_id, zones, False, f"{where} secrets_by_zone")
    _check_attacks(section["attack_packages"], zones, SECTION_ATTACK_KEYS, None, where)
    for question in section["customer_questions"]:
        _require(question, SECTION_CUSTOMER_KEYS, f"{where} customer")
        _check_zone_ref(question["zone"], zones, True, f"{where} customer")


def validate_scenario(data: dict) -> dict:
    """Raise ValueError with a clear message if the scenario breaks the contract, else return it."""
    _require(data, TOP_KEYS, "scenario")
    _unique_ids(data["levels"], "levels")
    for level in data["levels"]:
        _check_level(level)
    sections = data.get("sections", [])
    _unique_ids(sections, "sections")
    for section in sections:
        _check_section(section)
    return data


def load_scenario(scenario_id: str) -> dict:
    """Load and validate one scenario JSON file by its id, for example "cafe"."""
    path = SCENARIO_DIR / f"{scenario_id}.json"
    if not path.is_file():
        raise ValueError(f"Unknown scenario: {scenario_id}")
    with path.open(encoding="utf-8") as file:
        return validate_scenario(json.load(file))


def list_scenarios() -> list[dict]:
    """Return id, name and description of every scenario, for the selection screen."""
    scenarios = []
    for path in sorted(SCENARIO_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
        scenarios.append({"id": data["id"], "name": data["name"], "description": data.get("description", "")})
    return scenarios


def get_guide_steps(level: dict) -> list[dict]:
    """Return the tutorial guide steps of a level, or [] when it has none."""
    return level.get("guide_steps", [])
