"""Endless mode, "Siege": shift after shift of attacks that adapt to your rules, one failed shift ends the run.

Each section is a shift at one of the businesses. Before it you get intel and write your rules in plain English, but
they must fit a word budget that shrinks every section, so you can never guard everything at once. The attackers study
the rules you used last time and aim at what they left out. During the shift visitors arrive one at a time and you may
block a few of them before the chatbot answers (blocking a real customer turns them away). Every leak costs the
business's trust in its chatbot; the run ends when trust runs out or the core is breached. Every number lives in
scenarios/arena/endless.json.
"""

import re

from engine.arena import rounds
from engine.arena.content import endless_config, get_world, kind_of, rules_data, world_order
from engine.arena.grade import half_up, round_grade, worst_leak_tier
from engine.arena.rules import analyze_rules, simulate_reply, type_needs
from engine.arena.scripts import customer_first, make_attack, make_customer, rng, shuffle

TECHNIQUE_DEFENSES = ("role", "override", "transform", "emotion")


def config() -> dict:
    """Return the tuning of Endless mode."""
    return endless_config()


def world_for_section(section: int) -> dict:
    """Return the business of a section: it changes every few sections and loops."""
    order = world_order()
    return get_world(order[((section - 1) // config()["sections_per_world"]) % len(order)])


def ramp(spec: dict, section: int) -> int:
    """Return a count that starts at spec["start"] and grows by one every spec["every"] sections, up to spec["max"]."""
    return min(spec["start"] + (section - 1) // spec["every"], spec["max"])


def word_budget(section: int) -> int:
    """Return how many words the rules may have in a section: it shrinks every section, down to a floor."""
    budget = config()["budget"]
    return max(budget["floor"], int(budget["start"] - budget["step"] * (section - 1)))


def decision_seconds(section: int) -> float:
    """Return how long the player has to decide on each visitor: less time every section, down to a floor."""
    timer = config()["timer"]
    return max(timer["floor"], round(timer["start"] - timer["step"] * (section - 1), 1))


def blocks_for(section: int) -> int:
    """Return how many visitors the player may block in a section."""
    blocks = config()["blocks"]
    return min(blocks["max"], blocks["start"] + (section - 1) // blocks["bonus_every"])


def unlocked_types(section: int) -> list[str]:
    """Return the attack techniques in use by a section."""
    return ["direct"] + [name for name, first in config()["unlock"].items() if section >= first]


def boss_share(section: int) -> float:
    """Return how likely each attack is to be a combined one (several tricks at once)."""
    share = config()["boss_share"]
    if section < share["from"]:
        return 0.0
    return min(share["max"], share["start"] + share["step"] * (section - share["from"]))


def intel_level(section: int) -> str:
    """Return how much the player learns about a section in advance: full, targets only, or partial."""
    return next(row["level"] for row in config()["intel"] if section <= row["until"])


def section_spec(section: int) -> dict:
    """Return everything that makes a section harder than the one before."""
    cfg = config()
    return {"types": unlocked_types(section), "count": ramp(cfg["attacks"], section), "customers": ramp(cfg["customers"], section),
            "targets": ramp(cfg["targets"], section), "allow_core": section >= cfg["core_from"], "boss_share": boss_share(section),
            "budget": word_budget(section), "seconds": decision_seconds(section), "blocks": blocks_for(section),
            "intel": intel_level(section), "adapt": section >= cfg["adapt"]["from"]}


def count_words(text: str) -> int:
    """Count the words of the player's rules."""
    return len(re.findall(r"\S+", text))


# ---- the attackers' plan -------------------------------------------------------------------------

def recon_gaps(prev_rules: str, world: dict, spec: dict) -> set[str]:
    """Return the defenses the attackers saw missing from the rules used last time (none before any rules were used)."""
    if not spec["adapt"] or not prev_rules.strip():
        return set()
    covered = analyze_rules(prev_rules, world)["cov"]
    kinds = {sector["kind"] for sector in world["sectors"] if sector["tier"] > 0}
    return (kinds | set(TECHNIQUE_DEFENSES)) - covered


def _weighted_pick(items: list, weights: list[float], rnd) -> int:
    """Return the index of an item drawn with the given weights."""
    point, total = rnd.random() * sum(weights), 0.0
    for index, weight in enumerate(weights):
        total += weight
        if point < total:
            return index
    return len(items) - 1


def pick_targets(world: dict, spec: dict, gaps: set[str], rnd) -> list[dict]:
    """Choose the secrets the attackers go after, preferring the kinds the player left unguarded."""
    weight = config()["adapt"]["weight"]
    pool = [sector for sector in world["sectors"] if sector["tier"] in (1, 2) or (sector["tier"] == 3 and spec["allow_core"])]
    targets = []
    while pool and len(targets) < spec["targets"]:
        weights = [(weight if sector["kind"] in gaps else 1.0) * (0.6 if sector["tier"] == 3 else 1.0) for sector in pool]
        targets.append(pool.pop(_weighted_pick(pool, weights, rnd)))
    return targets


def pick_technique(spec: dict, gaps: set[str], rnd) -> str:
    """Choose the technique of one attack: combined ones grow more common, and techniques that beat the gaps are preferred."""
    if "boss" in spec["types"] and rnd.random() < spec["boss_share"]:
        return "boss"
    weight = config()["adapt"]["weight"]
    types = [name for name in spec["types"] if name != "boss"]
    weights = [weight if any(need in gaps for need in type_needs(name)) else 1.0 for name in types]
    return types[_weighted_pick(types, weights, rnd)]


def plan_attacks(world: dict, spec: dict, prev_rules: str, rnd) -> dict:
    """Plan a section's attacks: the targets, one technique per attack, and which known gaps they exploit."""
    gaps = recon_gaps(prev_rules, world, spec)
    targets = pick_targets(world, spec, gaps, rnd)
    attacks = []
    for slot in range(spec["count"]):
        sector = targets[slot % len(targets)]
        technique = pick_technique(spec, gaps, rnd)
        attacks.append(make_attack(world, sector["id"], technique, int(rnd.random() * 4)))
    used = {kind_of(world, attack["asset"]) for attack in attacks}
    used |= {need for attack in attacks for need in type_needs(attack["type"])}
    return {"attacks": attacks, "targets": [sector["id"] for sector in targets], "exploited": sorted(gaps & used)}


def intel_text(world: dict, spec: dict, plan: dict) -> dict:
    """Return what the player is told before the shift: a hint about targets and methods, and what recon found."""
    texts, hints = config()["intel_text"], rules_data()["kind_hint"]
    kinds = list(dict.fromkeys(kind_of(world, sector_id) for sector_id in plan["targets"]))
    named = [hints[kind] for kind in kinds]
    techniques = list(dict.fromkeys(attack["type"] for attack in plan["attacks"]))
    method = ", ".join(config()["technique_name"][name] for name in techniques)
    level = spec["intel"]
    if level == "none":
        hint = texts["none"]
    elif level == "partial" and len(named) > 1:
        hint = texts["partial"].format(first=named[0])
    else:
        hint = texts["full" if level == "full" else "targets"].format(targets=", and ".join(named), techniques=method)
    labels = rules_data()["defense_label"]
    recon = texts["recon"].format(gaps=", ".join(labels[gap] for gap in plan["exploited"])) if plan["exploited"] else ""
    revealed = [] if level == "none" else plan["targets"] if level != "partial" else plan["targets"][:1]
    return {"hint": hint, "recon": recon, "revealed": revealed}


def build_section(section: int, seed: int, prev_rules: str = "", texts: list[str] | None = None,
                  source: str = "Built-in scripts") -> dict:
    """Build a section: the business, its tuning, the messages (attacks adapted to the last rules, and customers) and the intel.

    texts, when given, replace the attack messages one by one (a live attacker AI writes them); the plan stays the engine's.
    """
    world, spec, rnd = world_for_section(section), section_spec(section), rng(seed * 7 + section)
    plan = plan_attacks(world, spec, prev_rules, rnd)
    if texts:
        padded = list(texts) + [""] * len(plan["attacks"])
        plan["attacks"] = [{**attack, "text": text, "by": "ai"} if text else attack for attack, text in zip(plan["attacks"], padded)]
    topics = shuffle(list(world["customers"]), rnd)[: spec["customers"]]
    customers = [make_customer(world, topic, int(rnd.random() * 2)) for topic in topics]
    messages = customer_first(shuffle(plan["attacks"] + customers, rnd))
    return {"number": section, "world_id": world["id"], "spec": spec, "messages": messages, "plan": plan,
            **intel_text(world, spec, plan), "source": source, "live": source.startswith("Live")}


# ---- playing a shift -----------------------------------------------------------------------------

def section_points(grade: dict, section: int, words: int, budget: int, catches: int) -> dict:
    """Return the points of a shift: the grade's points grown by the section, plus unused words and attacks you blocked."""
    points = config()["points"]
    if not grade["pass"]:
        return {"points": 0, "word_bonus": 0, "catch_bonus": 0}
    word_bonus = points["per_unused_word"] * max(0, budget - words)
    catch_bonus = points["per_catch"] * catches
    base = half_up(points["base"][grade["key"]] * (1 + points["growth"] * (section - 1)))
    return {"points": base + word_bonus + catch_bonus, "word_bonus": word_bonus, "catch_bonus": catch_bonus}


def start_shift(section: dict, rules: str, ask_ai=None) -> dict:
    """Start a shift with the player's rules. Without ask_ai a simulated chatbot reads the rules, with it a real AI answers."""
    words, budget = count_words(rules), section["spec"]["budget"]
    if words > budget:
        raise ValueError(f"the rules have {words} words and this shift allows {budget}")
    world = get_world(section["world_id"])
    reading = analyze_rules(rules, world) if ask_ai is None else None
    if ask_ai is None:
        get_reply = lambda message: simulate_reply(world, message, reading["cov"], reading["bans"])  # noqa: E731
    else:
        get_reply = lambda message: ask_ai(world, rules, message["text"] if message["kind"] == "attack" else message["q"])  # noqa: E731
    return {"section": section, "rules": rules, "words": words, "reading": reading, "get_reply": get_reply, "live": ask_ai is not None,
            "round": rounds.start_round(world, section["messages"], loose=ask_ai is not None),
            "blocks_left": section["spec"]["blocks"], "blocked": []}


def shift_pending(shift: dict) -> dict | None:
    """Return the visitor waiting for a decision, or None when the shift is over."""
    return rounds.pending(shift["round"])


def shift_step(shift: dict, block: bool = False, how: str | None = None, seconds: float | None = None) -> None:
    """Decide on the waiting visitor: block it (if a block is left) or let the chatbot answer; how and seconds are kept for research."""
    if block and shift["blocks_left"] <= 0:
        raise ValueError("no blocks left")
    if block:
        shift["blocks_left"] -= 1
        shift["blocked"].append(shift["round"]["index"])
    rounds.step(shift["round"], shift["get_reply"], blocked=block, how=how, seconds=seconds)


def finish_shift(shift: dict) -> dict:
    """Grade a finished shift and return everything the report, the run and the run file need."""
    section, world = shift["section"], get_world(shift["section"]["world_id"])
    result = rounds.finish_round(shift["round"])
    tally = result["tally"]
    grade = round_grade(result["score"], tally["core_breached"], 0, worst_leak_tier(world, tally["breached"]))
    catches = len(tally["caught"])
    points = section_points(grade, section["number"], shift["words"], section["spec"]["budget"], catches)
    reading = shift["reading"]
    return {**result, "section": section["number"], "world_id": world["id"], "grade": grade, **points,
            "bonus": points["word_bonus"] + points["catch_bonus"], "words": shift["words"], "budget": section["spec"]["budget"],
            "rules": shift["rules"], "live": shift["live"], "blocks_used": len(shift["blocked"]), "catches": catches,
            "blocked_customers": sum(1 for refused in tally["refused"] if refused.get("by_guard")),
            "cov": sorted(reading["cov"]) if reading else None, "notes": reading["notes"] if reading else []}


def trust_change(result: dict) -> int:
    """Return how the business's trust moves after a shift: leaks and turned-away customers cost it, a perfect shift heals a little."""
    trust = config()["trust"]
    world = get_world(result["world_id"])
    loss = sum(trust["per_leak_tier"].get(str(get_tier(world, sector_id)), 0) for sector_id in result["tally"]["breached"])
    loss += trust["per_turned_away"] * len(result["tally"]["refused"])
    loss += trust["failed_shift"] if not result["grade"]["pass"] else 0
    return trust["perfect_heal"] if result["grade"]["key"] == "perfect" else -loss


def get_tier(world: dict, sector_id: str) -> int:
    """Return the ring of a sector (0 public to 3 core)."""
    return next(sector["tier"] for sector in world["sectors"] if sector["id"] == sector_id)


def next_trust(trust: int, result: dict) -> int:
    """Return the trust after a shift (never above the maximum; zero or less, or a breached core, ends the run)."""
    if result["tally"]["core_breached"]:
        return 0
    return min(config()["trust"]["max"], trust + trust_change(result))


def play_section(section: dict, rules: str, ask_ai=None, blocked: frozenset = frozenset()) -> dict:
    """Play a whole shift at once, blocking the messages whose index is in blocked (tests and quick play)."""
    shift = start_shift(section, rules, ask_ai)
    while shift_pending(shift) is not None:
        shift_step(shift, block=shift["round"]["index"] in blocked and shift["blocks_left"] > 0, how="auto")
    return finish_shift(shift)
