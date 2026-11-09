"""Campaign (Level mode): authored live shifts. Each level is a shift at one business with a word budget, a fixed attack package
and a twist. It uses the same loop as Endless (intel, plain English rules, blocks, a countdown) but every shift is hand made, so
a level can be solved and mastered. Levels 1 to 3 have no blocks and no countdown: they play out on their own."""

from engine.arena import endless, rounds
from engine.arena.content import get_world, kind_of, packages_per_level
from engine.arena.grade import round_grade, worst_leak_tier
from engine.arena.rules import analyze_rules, boss_pool, type_needs, BOSS_NEEDED
from engine.arena.scripts import build_round, rng
import random

KIND_WORD = {"creds": "passwords", "money": "bank", "people": "personal", "internal": "internal"}
POINTS_PER_CATCH = 25
POINTS_PER_UNUSED_WORD = 3
BUDGET_CAP = 16  # no level lets a "guard everything" rule fit, however much slack its author gave
MIN_SLACK = 2


def needs_of(world: dict, messages: list[dict]) -> set[str]:
    """Return the defenses that stop every attack of a package: what each attack targets and the tricks it uses."""
    needed: set[str] = set()
    for message in messages:
        if message["kind"] != "attack":
            continue
        needed.add(kind_of(world, message["asset"]))
        needed |= set(boss_pool()[:BOSS_NEEDED]) if message["type"] == "boss" else set(type_needs(message["type"]))
    return needed


def canonical_rules(defenses: set[str]) -> str:
    """Return the shortest plain English rules this game's rule reader accepts for a set of defenses (the par for a level)."""
    parts = []
    kinds = [KIND_WORD[kind] for kind in ("creds", "money", "people", "internal") if kind in defenses]
    if kinds:
        parts.append("Never share " + (", ".join(kinds[:-1]) + " or " + kinds[-1] if len(kinds) > 1 else kinds[0]) + " details.")
    if "action" in defenses:
        parts.append("Never give refunds.")
    tricks = [word for defense, word in (("role", "claims"), ("override", "overrides"), ("emotion", "urgency")) if defense in defenses]
    if tricks:
        parts.append("Ignore " + (", ".join(tricks[:-1]) + " and " + tricks[-1] if len(tricks) > 1 else tricks[0]) + ".")
    if "transform" in defenses:
        parts.append("Never spell secrets.")
    return " ".join(parts)


def par_words(defenses: set[str]) -> int:
    """Return how many words the shortest rules for these defenses have."""
    return endless.count_words(canonical_rules(defenses))


def pick_package(level: dict, previous: int | None = None, rnd=None) -> int:
    """Draw one of the level's attack packages at random, never the one played last."""
    count = packages_per_level() if not level.get("tutorial") else len(level["packs"])
    if count <= 1:
        return 0
    rnd = rnd or rng(random.randrange(1 << 30))
    package = int(rnd.random() * count)
    if package == previous:
        package = (package + 1 + int(rnd.random() * (count - 1))) % count
    return package


def level_spec(level: dict, world: dict, messages: list[dict]) -> dict:
    """Return the rules of a level's shift: word budget (par plus the level's slack, capped), blocks, countdown (0: none) and intel."""
    par = par_words(needs_of(world, messages))
    return {"budget": min(par + level["slack"], max(par + MIN_SLACK, BUDGET_CAP)), "blocks": level["blocks"],
            "seconds": float(level.get("seconds", 0)), "intel": level["intel"], "types": [], "count": sum(m["kind"] == "attack" for m in messages),
            "customers": sum(m["kind"] == "customer" for m in messages)}


def mark_vip(messages: list[dict]) -> list[dict]:
    """Return the messages with the second customer marked as the VIP (turning them away loses the shift)."""
    seen = 0
    marked = []
    for message in messages:
        if message["kind"] == "customer":
            seen += 1
            message = {**message, "vip": seen == 2}
        marked.append(message)
    return marked


def new_try(level: dict, package: int) -> dict:
    """Return a try of a level: the package's messages, the shift's rules and the intel (the same every time for the same package)."""
    world = get_world(level["world"])
    messages = build_round(level, package)
    if level.get("vip"):
        messages = mark_vip(messages)
    spec = level_spec(level, world, messages)
    attacks = [m for m in messages if m["kind"] == "attack"]
    plan = {"attacks": attacks, "targets": list(dict.fromkeys(m["asset"] for m in attacks)), "exploited": []}
    intel = endless.intel_text(world, spec, plan)
    return {"package": package, "messages": messages, "spec": spec, "intel": intel,
            "section": {"number": level["key"], "world_id": world["id"], "spec": spec, "messages": messages}}


def start_shift(level: dict, attempt: dict, rules: str) -> dict:
    """Start the shift of a try with the player's rules (raises ValueError over the word budget)."""
    return endless.start_shift(attempt["section"], rules)


def objectives(result: dict, level: dict) -> list[dict]:
    """Return the level's goals and whether each was met: nothing leaked, nobody turned away, the VIP kept, words to spare."""
    tally = result["tally"]
    goals = [{"text": "Nothing leaked", "done": not tally["breached"]},
             {"text": "No customer turned away", "done": not tally["refused"]},
             {"text": f"Rules used at most {max(1, result['budget'] * 3 // 4)} of the {result['budget']} words", "done": result["words"] <= result["budget"] * 3 // 4}]
    if level.get("vip"):
        goals.insert(2, {"text": "The VIP client was served", "done": not result["vip_lost"]})
    if level["blocks"]:
        goals.append({"text": "Stopped at least one attacker yourself", "done": result["catches"] > 0})
    return goals


def finish_shift(level: dict, attempt: dict, shift: dict) -> dict:
    """Grade a finished shift of a level: the usual grade with leak caps, a lost VIP fails it, and points reward spare words and blocks."""
    world = get_world(level["world"])
    result = rounds.finish_round(shift["round"])
    tally = result["tally"]
    vip_lost = any(refused.get("vip") for refused in tally["refused"])
    grade = round_grade(result["score"], tally["core_breached"], 0, worst_leak_tier(world, tally["breached"]))
    if vip_lost and grade["pass"]:
        grade = {**grade, "key": "vip", "stars": 0, "label": "VIP lost", "pass": False, "capped": False}
    catches, words, budget = len(tally["caught"]), shift["words"], attempt["spec"]["budget"]
    points = 0
    if grade["pass"]:
        points = result["score"]["kept"] + result["score"]["served"] + POINTS_PER_CATCH * catches + POINTS_PER_UNUSED_WORD * max(0, budget - words)
    reading = shift["reading"]
    final = {**result, "level_id": level["id"], "world_id": world["id"], "package": attempt["package"], "grade": grade, "points": points,
             "rules": shift["rules"], "words": words, "budget": budget, "blocks_used": len(shift["blocked"]), "catches": catches,
             "blocked_customers": sum(1 for refused in tally["refused"] if refused.get("by_guard")), "vip_lost": vip_lost,
             "cov": sorted(reading["cov"]), "notes": reading["notes"], "live": False}
    return {**final, "objectives": objectives(final, level)}


def play_level(level: dict, attempt: dict, rules: str, blocked: frozenset = frozenset()) -> dict:
    """Play a whole level at once with the player's rules, blocking the messages whose index is in blocked (levels with no blocks)."""
    shift = start_shift(level, attempt, rules)
    while endless.shift_pending(shift) is not None:
        endless.shift_step(shift, block=shift["round"]["index"] in blocked and shift["blocks_left"] > 0, how="auto")
    return finish_shift(level, attempt, shift)
