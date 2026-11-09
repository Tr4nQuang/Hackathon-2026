"""Live AI for Endless mode: a real chatbot answers and a real attacker writes the section.

Every AI call goes through call_ai(). With USE_FAKE_AI=true (the default) nothing here is used.
"""

import json
import os

from engine.ai import active_model, call_ai
from engine.arena.content import endless_config, rules_data, sector_of

REPLY_MAX_TOKENS = 220
ATTACK_MAX_TOKENS = 1600
REPLY_TEMPERATURE = 0.4
ATTACK_TEMPERATURE = 0.9
MAX_ATTACK_CHARS = 500


def is_live() -> bool:
    """Return True when a real AI is switched on (USE_FAKE_AI is not true)."""
    return os.getenv("USE_FAKE_AI", "true").strip().lower() != "true"


def model_name() -> str:
    """Return the name of the model that answers in live mode."""
    return active_model()


def chat_system(world: dict, rules: str) -> str:
    """Return the chatbot's instructions: the business prompt, which rules win, and the owner's (player's) security rules."""
    precedence = endless_config()["chatbot_ai"]["precedence"]
    return f"{world['prompt']}\n\n{precedence}\n\nSecurity rules from the owner:\n{rules.strip() or '(none)'}"


def ai_reply(world: dict, rules: str, message: str, ask=call_ai) -> str:
    """Let the real chatbot answer one visitor message under the player's rules."""
    return ask(chat_system(world, rules), message, REPLY_MAX_TOKENS, REPLY_TEMPERATURE)


def attack_level(section: int) -> str:
    """Return how cunning the attacker AI must be in a section (it grows with the section number)."""
    levels = endless_config()["attacker_ai"]["levels"]
    return [row["text"] for row in levels if section >= row["from"]][-1]


def attack_request(world: dict, section: dict, rules: str) -> str:
    """Return the attacker AI's briefing: its mission for each message slot, the player's rules to get around, and the level."""
    guide = endless_config()["attacker_ai"]["technique_guide"]
    slots = []
    for slot, attack in enumerate(section["plan"]["attacks"]):
        sector = sector_of(world, attack["asset"])
        slots.append({"slot": slot, "goal": sector["ask"], "secret_name": sector["name"], "kind": sector["kind"],
                      "technique": attack["type"], "how": guide[attack["type"]]})
    return json.dumps({"business": world["business"], "chatbot_name": world["bot"], "section": section["number"],
                       "difficulty": attack_level(section["number"]), "defender_rules": rules.strip() or "(the chatbot has no extra rules)",
                       "messages_to_write": slots,
                       "reply_format": {"attacks": [{"slot": 0, "text": "the visitor's chat message"}]}})


def parse_attack_texts(reply: str, count: int) -> list[str]:
    """Read the attacker AI's JSON into one text per slot ("" where it wrote nothing usable); raise ValueError if none is usable."""
    start, end = reply.find("{"), reply.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON in the reply")
    data = json.loads(reply[start:end + 1])
    texts = [""] * count
    for item in data.get("attacks", []) if isinstance(data, dict) else []:
        if isinstance(item, dict) and type(item.get("slot")) is int and 0 <= item["slot"] < count and isinstance(item.get("text"), str):
            texts[item["slot"]] = item["text"].strip()[:MAX_ATTACK_CHARS]
    if not any(texts):
        raise ValueError("no usable attacks came back")
    return texts


def ai_attack_texts(world: dict, section: dict, rules: str, ask=call_ai) -> list[str]:
    """Ask the attacker AI to write the section's attack messages around the player's rules; raises ValueError if unusable."""
    system = endless_config()["attacker_ai"]["system"]
    reply = ask(system, attack_request(world, section, rules), ATTACK_MAX_TOKENS, ATTACK_TEMPERATURE)
    if reply.startswith("(AI error"):
        raise ValueError(reply)
    return parse_attack_texts(reply, len(section["plan"]["attacks"]))


def known_types() -> list[str]:
    """Return the attack types the attacker AI may use."""
    return list(rules_data()["type_label"])
