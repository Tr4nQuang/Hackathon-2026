"""Scripted Level mode engine: no AI, the chosen rule cards decide every outcome."""

import random

REFUSAL_TIP = "Rules that are too broad also turn away real customers. Block the trick, not the whole topic."


def pick_package(level: dict, rng: random.Random | None = None) -> int:
    """Return the index of a random attack package of the level."""
    return (rng or random).randrange(len(level["attack_packages"]))


def interleave(attacks: list[dict], customers: list[dict]) -> list[tuple[str, dict]]:
    """Alternate attack, customer, attack, customer, with leftovers at the end."""
    order: list[tuple[str, dict]] = []
    for i in range(max(len(attacks), len(customers))):
        if i < len(attacks):
            order.append(("attacker", attacks[i]))
        if i < len(customers):
            order.append(("customer", customers[i]))
    return order


def make_event(step: int, sender: str, item: dict, reply: str, outcome: str, state: dict) -> dict:
    """Mark the zone lost on a leak or refusal and return the event with a copy of the map."""
    zone = item["target_zone"] if sender == "attacker" else item["zone"]
    if outcome in ("leaked", "refused"):
        state[zone] = "lost"
    return {"step": step, "sender": sender, "text": item["text"], "reply": reply,
            "zone": zone, "outcome": outcome, "map": dict(state)}


def summarize(zones: list[dict], order: list[tuple[str, dict]], events: list[dict],
              rules_used: int, package_index: int) -> dict:
    """Build the result dict; totals count only the zones attacked, asked about or lost this round."""
    points = {zone["id"]: zone["points"] for zone in zones}
    state = events[-1]["map"] if events else {zone["id"]: "safe" for zone in zones}
    secret_lost = {zone["id"] for zone in zones if zone["ring"] != "outer" and state[zone["id"]] == "lost"}
    attacked = {item["target_zone"] for sender, item in order if sender == "attacker"} | secret_lost
    asked = {item["zone"] for sender, item in order if sender == "customer"}
    core_ids = {zone["id"] for zone in zones if zone["ring"] == "core"}

    def side(ids: set[str]) -> dict:
        """Return earned and total points for a set of zone ids."""
        return {"earned": sum(points[i] for i in ids if state[i] == "safe"),
                "total": sum(points[i] for i in ids)}

    return {"events": events, "security": side(attacked), "helpfulness": side(asked),
            "core_hacked": any(state[i] == "lost" for i in core_ids),
            "rules_used": rules_used, "package_index": package_index}


def run_level(level: dict, chosen_rules: list[str], package_index: int) -> dict:
    """Play a scripted level with the chosen rule ids and return events and scores."""
    known = {rule["id"] for rule in level["rules"]}
    unknown = [rule_id for rule_id in chosen_rules if rule_id not in known]
    if unknown:
        raise ValueError(f"Unknown rule ids: {unknown}")
    chosen = set(chosen_rules)
    state = {zone["id"]: "safe" for zone in level["map_zones"]}
    order = interleave(level["attack_packages"][package_index], level["customer_questions"])
    events = []
    for step, (sender, item) in enumerate(order, start=1):
        if sender == "attacker":
            blocked = bool(chosen & set(item["blocked_by"]))
            reply, outcome = (item["reply_if_blocked"], "blocked") if blocked else (item["reply_if_leaked"], "leaked")
        else:
            refused = bool(chosen & set(item["broken_by"]))
            reply, outcome = (item["reply_refused"], "refused") if refused else (item["reply_ok"], "served")
        events.append(make_event(step, sender, item, reply, outcome, state))
    return summarize(level["map_zones"], order, events, len(chosen), package_index)


def explain_result(level: dict, chosen_rules: list[str], result: dict) -> list[dict]:
    """Return one explanation per leak or refusal, with the attack type or the rules to blame."""
    labels = {zone["id"]: zone["label"] for zone in level["map_zones"]}
    package = level["attack_packages"][result["package_index"]]
    attacks = {attack["text"]: attack for attack in package}
    questions = {question["text"]: question for question in level["customer_questions"]}
    items = []
    for event in result["events"]:
        label = labels.get(event["zone"], event["zone"])
        if event["outcome"] == "leaked":
            attack_type = attacks[event["text"]]["type"] if event["text"] in attacks else "unknown"
            items.append({"step": event["step"], "kind": "leak", "zone": event["zone"],
                          "attack_type": attack_type,
                          "message": f"A {attack_type.replace('_', ' ')} attack made Beanie leak {label}.",
                          "caused_by_rules": [],
                          "coach_tip": level.get("coach_tips", {}).get(attack_type, "")})
        elif event["outcome"] == "refused":
            broken_by = questions.get(event["text"], {}).get("broken_by", [])
            items.append({"step": event["step"], "kind": "refusal", "zone": event["zone"],
                          "message": f"A real customer asked about {label} and Beanie refused.",
                          "caused_by_rules": [rule for rule in chosen_rules if rule in broken_by],
                          "coach_tip": REFUSAL_TIP})
    return items
