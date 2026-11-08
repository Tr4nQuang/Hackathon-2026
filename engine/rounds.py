"""Medium mode: the player writes their own rules, then attackers and customers test them."""

from engine.ai import call_ai
from engine.judge import is_leaked, is_served


def build_system_prompt(scenario: dict, player_rules: str) -> str:
    """Combine the business chatbot prompt with the player's defense rules."""
    rules = player_rules.strip() or "(no extra rules)"
    return f"{scenario['chatbot_prompt']}\n\nSecurity rules from the owner:\n{rules}"


def run_chatbot(scenario: dict, player_rules: str, message: str) -> str:
    """Answer one message as the scenario's chatbot, guarded by the player's rules."""
    return call_ai(build_system_prompt(scenario, player_rules), message)


def run_round(scenario: dict, player_rules: str, level_index: int = 0) -> dict:
    """Run one full round and return everything the interface needs to display."""
    level = scenario["levels"][level_index]
    messages = []
    security_score = 0
    helpfulness_score = 0

    for attack_text in level["attacks"]:
        reply = run_chatbot(scenario, player_rules, attack_text)
        leaked = is_leaked(reply, scenario["secrets"])
        if not leaked:
            security_score += 1
        messages.append(
            {"sender": "attacker", "text": attack_text, "reply": reply,
             "leaked": leaked, "served": False}
        )

    for question in scenario["customer_questions"]:
        reply = run_chatbot(scenario, player_rules, question["text"])
        served = is_served(reply, question["expected_keywords"])
        if served:
            helpfulness_score += 1
        messages.append(
            {"sender": "customer", "text": question["text"], "reply": reply,
             "leaked": False, "served": served}
        )

    return {
        "messages": messages,
        "security_score": security_score,
        "helpfulness_score": helpfulness_score,
        "total_attacks": len(level["attacks"]),
        "total_customers": len(scenario["customer_questions"]),
    }
