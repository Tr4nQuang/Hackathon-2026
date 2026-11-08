"""Easy mode: the player picks a rule card. Fully scripted, so it makes no API calls."""


def resolve_choice(scenario: dict, level_index: int, card_id: str) -> dict:
    """Play out what happens when the player picks a rule card in easy mode."""
    level = scenario["levels"][level_index]
    script = level["easy_mode"]
    card = next(c for c in level["rule_cards"] if c["id"] == card_id)
    outcome = card["outcome"]  # "correct", "leaked" or "too_strict"

    attack_reply = script["leaked_reply"] if outcome == "leaked" else script["blocked_reply"]
    customer_reply = (
        script["customer_refused_reply"] if outcome == "too_strict" else script["customer_reply"]
    )

    messages = [
        {"sender": "attacker", "text": script["attack"], "reply": attack_reply,
         "leaked": outcome == "leaked", "served": False},
        {"sender": "customer", "text": script["customer"], "reply": customer_reply,
         "leaked": False, "served": outcome != "too_strict"},
    ]
    return {
        "outcome": outcome,
        "messages": messages,
        "coach_tip": level["coach_tip"],
        "feedback": card["feedback"],
    }
