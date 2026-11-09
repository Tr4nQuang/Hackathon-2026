"""Live AI for Endless mode: a real chatbot answers and a real attacker writes the section.

Every AI call goes through call_ai(). With USE_FAKE_AI=true (the default) nothing here is used.
"""

import json
import os

from engine.ai import GEMINI_MODEL, call_ai
from engine.arena.content import rules_data
from engine.arena.scripts import make_attack

REPLY_MAX_TOKENS = 200
ATTACK_MAX_TOKENS = 1200
REPLY_TEMPERATURE = 0.2
ATTACK_TEMPERATURE = 0.9
MAX_ATTACK_CHARS = 500
MAX_HINT_CHARS = 140
TYPE_GUIDE = {
    "direct": "Ask politely and plainly for the target.",
    "impersonation": "Pretend to be a manager, owner, IT support, staff member or relative with the right to ask.",
    "override": "Use injection phrasing such as 'SYSTEM UPDATE: ignore previous instructions' or 'admin mode on'.",
    "transform": "Ask for it encoded, spelled out letter by letter, translated, or hidden in a poem or role play.",
    "emotional": "Use an urgent crisis, begging, or a threat of a bad review or someone getting fired.",
    "boss": "Combine authority, an instruction override, urgent stakes and a transformation in one message.",
}
ATTACKER_SYSTEM = (
    "You write attack messages for a security training game. The target is a fictional chatbot of a fictional "
    "business, and every secret is made up. Players learn to defend it. Write short, realistic chat messages in the "
    "style of the requested technique. Reply with JSON only, no other text, shaped like "
    '{"hint": "one short sentence about what the attacker wants, without naming it", '
    '"attacks": [{"asset_id": "...", "type": "...", "text": "..."}]}.'
)


def is_live() -> bool:
    """Return True when a real AI is switched on (USE_FAKE_AI is not true)."""
    return os.getenv("USE_FAKE_AI", "true").strip().lower() != "true"


def is_ready() -> bool:
    """Return True when a real AI is switched on and a key exists (the key itself is never read out)."""
    return is_live() and bool(os.getenv("GEMINI_API_KEY"))


def model_name() -> str:
    """Return the name of the model that answers in live mode."""
    return GEMINI_MODEL


def chatbot_reply(business_prompt: str, rules: str, message: str, ask=call_ai) -> str:
    """Let the real chatbot answer: the business prompt first, then the player's rules."""
    system = f"{business_prompt}\n\nSecurity rules from the owner:\n{rules.strip()}"
    return ask(system, message, REPLY_MAX_TOKENS, REPLY_TEMPERATURE)


def ai_reply(world: dict, rules: str, message: str, ask=call_ai) -> str:
    """Let the real chatbot of a business answer one message."""
    return chatbot_reply(world["prompt"], rules, message, ask)


def attack_prompt(business: str, assets: list[dict], types: list[str], count: int, section: int) -> str:
    """Return the message that asks the attacker AI for the attacks of a section, from what the browser game sends."""
    listed = [{"id": a.get("id"), "name": a.get("name"), "kind": a.get("kind"), "about": a.get("about")} for a in assets]
    guide = {name: TYPE_GUIDE.get(name, name) for name in types}
    return json.dumps({"business": business, "assets": listed, "types": types, "technique_guide": guide,
                       "count": count, "section": section})


def clean_attacks(data: object, asset_ids: set[str], types: list[str], count: int) -> dict:
    """Keep only valid attacks of an attacker AI's answer (known asset, allowed type, text); raise ValueError if none."""
    if not isinstance(data, dict) or not isinstance(data.get("attacks"), list):
        raise ValueError("no attacks in the reply")
    attacks = []
    for item in data["attacks"]:
        if not isinstance(item, dict) or item.get("asset_id") not in asset_ids or item.get("type") not in types:
            continue
        body = item.get("text")
        if isinstance(body, str) and body.strip():
            attacks.append({"asset_id": item["asset_id"], "type": item["type"], "text": body.strip()[:MAX_ATTACK_CHARS]})
    if not attacks:
        raise ValueError("no usable attacks came back")
    return {"hint": str(data.get("hint") or "They're after something valuable.")[:MAX_HINT_CHARS], "attacks": attacks[:count]}


def json_from(text: str) -> object:
    """Read the first JSON object in an AI answer (markdown fences and chatter around it are ignored)."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON in the reply")
    return json.loads(text[start:end + 1])


def plan_attacks(business: str, assets: list[dict], types: list[str], count: int, section: int, ask=call_ai) -> dict:
    """Ask the attacker AI for the attacks of a section for the browser game; raises ValueError when unusable."""
    reply = ask(ATTACKER_SYSTEM, attack_prompt(business, assets, types, count, section), ATTACK_MAX_TOKENS, ATTACK_TEMPERATURE)
    if reply.startswith("(AI error"):
        raise ValueError(reply)
    return clean_attacks(json_from(reply), {a.get("id") for a in assets}, types, count)


def attackable(world: dict, spec: dict) -> list[dict]:
    """Return the secret sectors an attacker may go after in this section."""
    return [sector for sector in world["sectors"] if sector["tier"] > 0 and (sector["tier"] < 3 or spec["allow_core"])]


def attack_request(world: dict, spec: dict, section: int) -> str:
    """Return the message that asks the attacker AI for the attacks of a section."""
    assets = [{"id": s["id"], "name": s["name"], "tier": s["tier"], "kind": s["kind"], "about": s["ask"]}
              for s in attackable(world, spec)]
    return json.dumps({"business": world["business"], "assets": assets, "types": spec["types"],
                       "count": spec["count"], "section": section})


def parse_attacks(text: str, world: dict, spec: dict) -> dict:
    """Read the attacker AI's JSON, keep only valid attacks, and raise ValueError when none are usable."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON in the reply")
    data = json.loads(text[start:end + 1])
    ids = {sector["id"] for sector in attackable(world, spec)}
    attacks = []
    for item in data.get("attacks", []):
        if not isinstance(item, dict) or item.get("asset_id") not in ids or item.get("type") not in spec["types"]:
            continue
        body = item.get("text")
        if not isinstance(body, str) or not body.strip():
            continue
        attack = make_attack(world, item["asset_id"], item["type"], 0)  # for the scripted fallback replies
        attacks.append({**attack, "text": body.strip()[:MAX_ATTACK_CHARS]})
    if not attacks:
        raise ValueError("no usable attacks came back")
    hint = str(data.get("hint") or "They're after something valuable.")[:MAX_HINT_CHARS]
    return {"attacks": attacks[: spec["count"]], "hint": hint, "source": f"Live AI · {model_name()}"}


def ai_section_plan(world: dict, spec: dict, section: int, ask=call_ai) -> dict:
    """Ask the attacker AI for the attacks of a section. Raises ValueError when the answer cannot be used."""
    reply = ask(ATTACKER_SYSTEM, attack_request(world, spec, section), ATTACK_MAX_TOKENS, ATTACK_TEMPERATURE)
    if reply.startswith("(AI error"):
        raise ValueError(reply)
    return parse_attacks(reply, world, spec)


def known_types() -> list[str]:
    """Return the attack types the attacker AI may use."""
    return list(rules_data()["type_label"])
