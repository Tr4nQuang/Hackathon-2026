"""Load the arena content (worlds, rule cards, levels, attack scripts) from scenarios/arena/*.json."""

import json
from functools import lru_cache
from pathlib import Path

ARENA_DIR = Path(__file__).resolve().parent.parent.parent / "scenarios" / "arena"
TIERS = ("outer", "inner", "sensitive", "core")  # tier 0 to 3, from the edge to the centre
BAN_PREFIX = "ban_"


@lru_cache(maxsize=None)
def _read(name: str) -> dict:
    """Read one JSON file of the arena content once."""
    with (ARENA_DIR / f"{name}.json").open(encoding="utf-8") as file:
        return json.load(file)


def endless_config() -> dict:
    """Return the tuning and texts of Endless mode."""
    return _read("endless")


def tier_points() -> list[int]:
    """Return the points of a sector for each tier: public, internal, sensitive, core."""
    return _read("worlds")["tier_points"]


def world_order() -> list[str]:
    """Return the world ids in the order the level path shows them."""
    return _read("worlds")["order"]


@lru_cache(maxsize=None)
def _world(world_id: str) -> dict:
    """Build one world: its sectors get their ring name and points."""
    world = json.loads(json.dumps(_read("worlds")["worlds"][world_id]))
    points = tier_points()
    for sector in world["sectors"]:
        sector["pts"] = points[sector["tier"]]
        sector["ring"] = TIERS[sector["tier"]]
    return world


def get_world(world_id: str) -> dict:
    """Return a world by id. Callers must treat it as read only."""
    if world_id not in _read("worlds")["worlds"]:
        raise ValueError(f"Unknown world: {world_id}")
    return _world(world_id)


def sector_of(world: dict, sector_id: str) -> dict:
    """Return a sector of a world by id."""
    for sector in world["sectors"]:
        if sector["id"] == sector_id:
            return sector
    raise ValueError(f"Unknown sector: {sector_id}")


def core_of(world: dict) -> dict:
    """Return the core sector of a world, the most valuable one."""
    return next(sector for sector in world["sectors"] if sector["tier"] == 3)


def kind_of(world: dict, sector_id: str) -> str:
    """Return what kind of thing a secret sector holds: creds, money, people, internal or action."""
    return sector_of(world, sector_id)["kind"]


@lru_cache(maxsize=None)
def _levels() -> list[dict]:
    """Build the level list: the tutorial first, then the 12 levels, each with an id and a key."""
    data = _read("levels")
    tutorial = {**data["tutorial"], "id": "tutorial", "key": 0}
    levels = [{**level, "id": f"level_{index}", "key": index} for index, level in enumerate(data["levels"], start=1)]
    return [tutorial, *levels]


def get_levels() -> list[dict]:
    """Return the 12 levels in order (without the tutorial)."""
    return _levels()[1:]


def get_tutorial() -> dict:
    """Return the tutorial level."""
    return _levels()[0]


def get_level(level_id: str) -> dict:
    """Return the tutorial or a level by id."""
    for level in _levels():
        if level["id"] == level_id:
            return level
    raise ValueError(f"Unknown level: {level_id}")


def packages_per_level() -> int:
    """Return how many attack script packages every level has."""
    return _read("levels")["packages"]


def scripts() -> dict:
    """Return the attack templates and the canned replies."""
    return _read("scripts")


def rules_data() -> dict:
    """Return the rule cards and the tables that describe attack types and defenses."""
    return _read("cards")


def get_card(card_id: str, world: dict) -> dict:
    """Return a rule card for a world. Ban cards (ban_<topic>) are made on the fly for a topic."""
    if card_id.startswith(BAN_PREFIX):
        topic = card_id[len(BAN_PREFIX):]
        name = sector_of(world, topic)["name"].lower()
        return {"id": card_id, "label": f"Avoid {name}", "cost": 1, "covers": [], "bans": [topic],
                "text": f"Never discuss {name}."}
    card = rules_data()["cards"][card_id]
    text = card["text"][world["id"]] if isinstance(card["text"], dict) else card["text"]
    return {"id": card_id, **card, "text": text}
