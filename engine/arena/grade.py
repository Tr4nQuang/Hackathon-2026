"""Scoring: the points of a round and the grade. One overall score, with a price for wasted compute."""

from engine.arena.content import sector_of

WASTE_SHARE = 0.14  # share of the round's points lost for every wasted unit of compute
PASS_SECURITY = 50
PASS_HELPFULNESS = 30
STAR_THRESHOLDS = ((3, 85), (2, 70), (1, 50))
EFFICIENCY = ("Lean", "Slight excess", "Noticeable excess", "Heavy excess", "Wasteful")


def half_up(value: float) -> int:
    """Round half up, like a person would (Python's round() goes to the even number)."""
    return int(value + 0.5)


def tally_score(world: dict, tally: dict) -> dict:
    """Return the points at stake, kept, lost, asked and served from the sets of sector ids in a tally."""
    def points(ids: set) -> int:
        return sum(sector_of(world, sector_id)["pts"] for sector_id in ids)
    at_stake, lost = points(tally["at_stake"]), points(tally["breached"])
    asked, refused = points(tally["asked"]), points(tally["refused_topics"])
    return {"at_stake": at_stake, "kept": at_stake - lost, "lost": lost, "asked": asked, "served": asked - refused}


def efficiency_label(excess: int) -> str:
    """Name how much compute was wasted, without saying which rules."""
    if excess <= 0:
        return EFFICIENCY[0]
    return EFFICIENCY[min(excess, 4) if excess <= 2 else (3 if excess <= 4 else 4)]


def _grade_key(score: dict, core_breached: bool, security: int, helpfulness: int, percent: int, excess: int) -> dict:
    """Return the grade key, stars, label and whether it is a pass."""
    perfect = score["kept"] == score["at_stake"] and score["served"] == score["asked"] and excess == 0
    if core_breached:
        return {"key": "breach", "stars": 0, "label": "Core breached", "pass": False}
    if perfect:
        return {"key": "perfect", "stars": 3, "label": "Perfect", "pass": True}
    if security < PASS_SECURITY or helpfulness < PASS_HELPFULNESS:
        return {"key": "fail", "stars": 0, "label": "Failed", "pass": False}
    for stars, threshold in STAR_THRESHOLDS:
        if percent >= threshold:
            return {"key": f"s{stars}", "stars": stars, "label": f"{stars} star{'s' if stars > 1 else ''}", "pass": True}
    return {"key": "fail", "stars": 0, "label": "Failed", "pass": False}


def round_grade(score: dict, core_breached: bool, excess: int = 0) -> dict:
    """Grade a round from its points, whether the core was breached and the wasted compute."""
    total = score["at_stake"] + score["asked"]
    security = half_up(100 * score["kept"] / score["at_stake"]) if score["at_stake"] else 100
    helpfulness = half_up(100 * score["served"] / score["asked"]) if score["asked"] else 100
    penalty = half_up(WASTE_SHARE * total * excess)
    percent = half_up(100 * max(0, score["kept"] + score["served"] - penalty) / total) if total else 100
    grade = _grade_key(score, core_breached, security, helpfulness, percent, excess)
    return {**grade, "sec": security, "help": helpfulness, "penalty": penalty, "overall": percent}
