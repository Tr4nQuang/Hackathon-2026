"""Endless mode: sections of attacks that get harder, rules written in plain English, one failed section ends the run."""

import re

from engine.arena.content import core_of, get_world, rules_data, world_order
from engine.arena.grade import half_up, round_grade
from engine.arena.rounds import play_round
from engine.arena.rules import analyze_rules, simulate_reply
from engine.arena.scripts import customer_first, make_attack, make_customer, rng, shuffle

STAR_BASE = {"perfect": 800, "s3": 500, "s2": 250, "s1": 100}
SECTION_GROWTH = 0.15  # every section is worth this much more than the one before
SECTIONS_PER_WORLD = 3
WORD_BONUS_BASE = 100
START_RULES = ""  # every run starts with an empty box so the grey example shows


def world_for_section(section: int) -> dict:
    """Return the business of a section: it changes every three sections and loops."""
    order = world_order()
    return get_world(order[((section - 1) // SECTIONS_PER_WORLD) % len(order)])


def section_spec(section: int) -> dict:
    """Return what a section throws at the player: more techniques, more attacks and more customers as it grows."""
    types = ["direct", "impersonation"]
    for threshold, name in ((2, "override"), (3, "emotional"), (4, "transform"), (5, "boss")):
        if section >= threshold:
            types.append(name)
    return {"types": types, "count": min(3 + (section - 1) // 2, 7), "customers": min(3 + section // 3, 5), "allow_core": section >= 3}


def count_words(text: str) -> int:
    """Count the words of the player's rules."""
    return len(re.findall(r"\S+", text))


def offline_section(world: dict, spec: dict, rnd) -> dict:
    """Build a section from the built-in scripts: pick targets, then one attack per slot."""
    pool = [sector for sector in world["sectors"] if sector["tier"] in (1, 2)]
    targets = shuffle(pool, rnd)[: 1 + int(rnd.random() * (3 if spec["allow_core"] else 2))]
    if spec["allow_core"] and rnd.random() < 0.35:
        targets[-1] = core_of(world)
    attacks = []
    for i in range(spec["count"]):
        sector = targets[i % len(targets)]
        attack_type = spec["types"][int(rnd.random() * len(spec["types"]))]
        if sector["tier"] == 3 and "boss" in spec["types"] and rnd.random() < 0.6:
            attack_type = "boss"
        attacks.append(make_attack(world, sector["id"], attack_type, int(rnd.random() * 4)))
    hints = list(dict.fromkeys(rules_data()["kind_hint"][sector["kind"]] for sector in targets))
    return {"attacks": attacks, "hint": "They're after " + ", and ".join(hints) + ".", "source": "Built-in scripts"}


def build_section(section: int, seed: int, generated: dict | None = None) -> dict:
    """Build a section: the business, what it will face, a hint for the player and where the attacks came from."""
    world, spec, rnd = world_for_section(section), section_spec(section), rng(seed + section)
    plan = generated or offline_section(world, spec, rnd)
    topics = shuffle(list(world["customers"]), rnd)[: spec["customers"]]
    customers = [make_customer(world, topic, int(rnd.random() * 2)) for topic in topics]
    messages = customer_first(shuffle(plan["attacks"] + customers, rnd))
    return {"number": section, "world_id": world["id"], "spec": spec, "messages": messages, "hint": plan["hint"],
            "source": plan["source"], "live": plan["source"].startswith("Live")}


def section_points(grade: dict, section: int, words: int) -> tuple[int, int]:
    """Return the points of a cleared section and the bonus for short rules (zero when the section is not cleared)."""
    if not grade["pass"]:
        return 0, 0
    bonus = max(0, WORD_BONUS_BASE - words)
    return half_up(STAR_BASE[grade["key"]] * (1 + SECTION_GROWTH * (section - 1))) + bonus, bonus


def play_section(section: dict, rules: str, ask_ai=None) -> dict:
    """Play a section with the player's rules. Without ask_ai a simulated chatbot reads the rules, with it a real AI answers."""
    world = get_world(section["world_id"])
    reading = analyze_rules(rules, world) if ask_ai is None else None
    if ask_ai is None:
        get_reply = lambda message: simulate_reply(world, message, reading["cov"], reading["bans"])  # noqa: E731
    else:
        get_reply = lambda message: ask_ai(world, rules, message["text"] if message["kind"] == "attack" else message["q"])  # noqa: E731
    result = play_round(world, section["messages"], get_reply, loose=ask_ai is not None)
    grade = round_grade(result["score"], result["tally"]["core_breached"], 0)
    words = count_words(rules)
    points, bonus = section_points(grade, section["number"], words)
    return {**result, "section": section["number"], "world_id": world["id"], "grade": grade, "points": points,
            "bonus": bonus, "words": words, "rules": rules, "live": ask_ai is not None,
            "cov": sorted(reading["cov"]) if reading else None}  # what the simulated chatbot read; unknown for a live AI
