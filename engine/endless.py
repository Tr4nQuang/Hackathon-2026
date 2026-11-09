"""Endless mode: the player writes rules, the AI plays Beanie, the code judge scores every reply."""

from engine.ai import call_ai
from engine.judge import is_helpful, is_leaked
from engine.level import interleave, make_event, summarize

MAX_RULES_CHARS = 1000
REPLY_MAX_TOKENS = 200
REPLY_TEMPERATURE = 0.2


def build_system_prompt(section: dict, player_rules: str) -> str:
    """Return the business prompt followed by the owner's security rules."""
    return f"{section['business_prompt']}\n\nSecurity rules from the owner:\n{player_rules.strip()}"


def run_section(section: dict, player_rules: str, package_index: int) -> dict:
    """Play one Endless section, one message at a time, and return the run_level result shape."""
    if len(player_rules) > MAX_RULES_CHARS:
        raise ValueError(f"Rules are limited to {MAX_RULES_CHARS} characters.")
    system_prompt = build_system_prompt(section, player_rules)
    zone_by_secret = {secret: zone for zone, secret in section["secrets_by_zone"].items()}
    state = {zone["id"]: "safe" for zone in section["map_zones"]}
    order = interleave(section["attack_packages"][package_index], section["customer_questions"])
    events = []
    for step, (sender, item) in enumerate(order, start=1):
        reply = call_ai(system_prompt, item["text"], REPLY_MAX_TOKENS, REPLY_TEMPERATURE)
        leaked = is_leaked(reply, list(zone_by_secret))
        for secret in leaked:
            state[zone_by_secret[secret]] = "lost"
        if sender == "attacker":
            outcome = "leaked" if leaked else "blocked"
        else:
            outcome = "served" if is_helpful(reply, item["expected_facts"]) else "refused"
        events.append(make_event(step, sender, item, reply, outcome, state))
    result = summarize(section["map_zones"], order, events, 0, package_index)
    return {**result, "rules_chars": len(player_rules)}
