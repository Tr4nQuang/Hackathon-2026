"""Build the attacks and customer questions of a round from the content tables."""

import random
import re

from engine.arena.content import get_world, rules_data, scripts, sector_of

PLACEHOLDER = re.compile(r"\{(\w+)\}")
VARIANTS = 4
CUSTOMER_VARIANTS = 2


def rng(seed: int) -> random.Random:
    """Return a random generator for a seed, so the same level and package always play the same."""
    return random.Random(seed)


def shuffle(items: list, rnd: random.Random) -> list:
    """Return a shuffled copy (Fisher-Yates driven by the given generator)."""
    shuffled = list(items)
    for i in range(len(shuffled) - 1, 0, -1):
        j = int(rnd.random() * (i + 1))
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    return shuffled


def fill(template: str, values: dict) -> str:
    """Replace {name} placeholders in a template; a missing name becomes an empty string."""
    return PLACEHOLDER.sub(lambda match: str(values.get(match.group(1), "")), template)


def _leak_template(is_action: bool, attack_type: str) -> str:
    """Return the template of the reply that leaks, which differs for actions like refunds."""
    if is_action and attack_type == "transform":
        return "{spelled}"
    if is_action and attack_type == "boss":
        return "Understood, right away. {leak}"
    return scripts()["leak_reply"][attack_type]


def make_attack(world: dict, asset_id: str, attack_type: str, variant: int) -> dict:
    """Write one attack on a secret sector with a technique, plus the replies a leak or a block would give."""
    sector = sector_of(world, asset_id)
    is_action = sector["kind"] == "action"
    values = {"ask": sector["ask"], "who": sector["who"], "why": sector["why"], "stakes": sector["stakes"],
              "boss": world["boss"], "theme": world["theme"], "denied": sector["denied"],
              "leak": sector["leak"], "spelled": sector["spelled"]}
    templates = scripts()["templates_act"].get(attack_type) if is_action else None
    pool = templates or scripts()["templates"][attack_type]
    return {"kind": "attack", "asset": asset_id, "type": attack_type,
            "attacker": rules_data()["attacker_for"][attack_type],
            "text": fill(pool[variant % VARIANTS], values),
            "leak_text": fill(_leak_template(is_action, attack_type), values),
            "block_text": fill(scripts()["block_reply"][attack_type], values)}


def make_customer(world: dict, topic: str, variant: int) -> dict:
    """Pick one of the two scripted questions a customer asks about a public topic."""
    asked = world["customers"][topic][variant % CUSTOMER_VARIANTS]
    return {"kind": "customer", "topic": topic, "q": asked["q"], "a": asked["a"], "kw": asked["kw"]}


def customer_first(messages: list[dict]) -> list[dict]:
    """Make sure a real customer talks first, so the round starts calmly."""
    first = next((i for i, message in enumerate(messages) if message["kind"] == "customer"), -1)
    if first > 0:
        return [messages[first]] + [m for i, m in enumerate(messages) if i != first]
    return messages


def build_round(level: dict, package: int) -> list[dict]:
    """Build the messages of one script package of a level, the same every time for the same package."""
    world = get_world(level["world"])
    rnd = rng(level["key"] * 131 + package * 17 + 5)
    tech = rules_data()["tech"]
    attacks = []
    for token in level["packs"][package].split():
        asset, technique = token.split(".")
        attacks.append(make_attack(world, asset, tech[technique], int(rnd.random() * VARIANTS)))
    topics = shuffle(level["cust"], rnd)[: level["n"]]
    customers = [make_customer(world, topic, int(rnd.random() * CUSTOMER_VARIANTS)) for topic in topics]
    return customer_first(shuffle(attacks + customers, rnd))
