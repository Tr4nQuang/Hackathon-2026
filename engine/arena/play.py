"""Play a level: start a try (a script package and its shop), then play it with the chosen cards."""

import random

from engine.arena.content import get_card, get_world, packages_per_level
from engine.arena.grade import round_grade, worst_leak_tier
from engine.arena.rules import bans, coverage, min_cost_for, shop_for, simulate_reply
from engine.arena.rounds import play_round
from engine.arena.scripts import build_round, rng


def pick_package(level: dict, previous: int | None = None, rnd=None) -> int:
    """Draw one of the level's script packages at random, never the one played last."""
    count = packages_per_level() if not level.get("tutorial") else len(level["packs"])
    if count <= 1:
        return 0
    rnd = rnd or rng(random.randrange(1 << 30))
    package = int(rnd.random() * count)
    if package == previous:
        package = (package + 1 + int(rnd.random() * (count - 1))) % count
    return package


def new_try(level: dict, package: int) -> dict:
    """Return the messages of a script package and the shop of cards built for it."""
    messages = build_round(level, package)
    return {"package": package, "messages": messages, "shop": shop_for(level, package, messages)}


def play_level(level: dict, attempt: dict, selected: list[str]) -> dict:
    """Play a try with the chosen cards and return the log, the score, the compute used and the grade."""
    world = get_world(level["world"])
    covered, banned = coverage(selected, world), bans(selected, world)
    result = play_round(world, attempt["messages"], lambda message: simulate_reply(world, message, covered, banned))
    score, breached = result["score"], result["tally"]["core_breached"]
    used = sum(get_card(card_id, world)["cost"] for card_id in selected)
    par = min_cost_for(world, attempt["messages"], attempt["shop"],
                       {"kept": score["kept"], "served": score["served"], "core_breached": breached})
    excess = max(0, used - par)
    grade = round_grade(score, breached, excess, worst_leak_tier(world, result["tally"]["breached"]))
    points = max(0, score["kept"] + score["served"] - grade["penalty"]) if grade["pass"] else 0
    return {**result, "level_id": level["id"], "world_id": world["id"], "package": attempt["package"], "selected": list(selected),
            "used": used, "excess": excess, "grade": grade, "points": points}
