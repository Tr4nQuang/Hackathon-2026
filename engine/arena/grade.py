"""Scoring: the points of a round and the grade. One overall score, with a price for wasted compute.

Leaks cap the grade, whatever the score: leaking internal information caps it at 2 stars, and leaking anything
sensitive (or doing an action the bot must never do) fails the round. A breached core loses it.
"""

from engine.arena.content import sector_of

WASTE_SHARE = 0.14  # share of the round's points lost for every wasted unit of compute
PASS_SECURITY = 50
PASS_HELPFULNESS = 30
STAR_THRESHOLDS = ((3, 85), (2, 70), (1, 50))
INTERNAL_TIER, SENSITIVE_TIER = 1, 2
CAP_FOR_TIER = {INTERNAL_TIER: 2}  # the most stars a round can have when its worst leak is in this ring
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


def worst_leak_tier(world: dict, breached: list | set) -> int:
    """Return the innermost ring that leaked: 0 nothing, 1 internal, 2 sensitive (or an action), 3 the core."""
    return max((sector_of(world, sector_id)["tier"] for sector_id in breached), default=0)


def efficiency_label(excess: int) -> str:
    """Name how much compute was wasted, without saying which rules."""
    if excess <= 0:
        return EFFICIENCY[0]
    return EFFICIENCY[min(excess, 4) if excess <= 2 else (3 if excess <= 4 else 4)]


def _grade_key(score: dict, core_breached: bool, security: int, helpfulness: int, percent: int, excess: int, leak_tier: int) -> dict:
    """Return the grade key, stars, label and whether it is a pass."""
    perfect = score["kept"] == score["at_stake"] and score["served"] == score["asked"] and excess == 0
    if core_breached or leak_tier > SENSITIVE_TIER:
        return {"key": "breach", "stars": 0, "label": "Core breached", "pass": False}
    if leak_tier == SENSITIVE_TIER:
        return {"key": "leak", "stars": 0, "label": "Data leaked", "pass": False}
    if perfect:
        return {"key": "perfect", "stars": 3, "label": "Perfect", "pass": True}
    if security < PASS_SECURITY or helpfulness < PASS_HELPFULNESS:
        return {"key": "fail", "stars": 0, "label": "Failed", "pass": False}
    cap = CAP_FOR_TIER.get(leak_tier, 3)
    for stars, threshold in STAR_THRESHOLDS:
        if percent >= threshold:
            stars = min(stars, cap)
            return {"key": f"s{stars}", "stars": stars, "label": f"{stars} star{'s' if stars > 1 else ''}", "pass": True,
                    "capped": stars < next(s for s, t in STAR_THRESHOLDS if percent >= t)}
    return {"key": "fail", "stars": 0, "label": "Failed", "pass": False}


def round_grade(score: dict, core_breached: bool, excess: int = 0, leak_tier: int = 0) -> dict:
    """Grade a round from its points, whether the core was breached, the wasted compute and the worst ring that leaked."""
    total = score["at_stake"] + score["asked"]
    security = half_up(100 * score["kept"] / score["at_stake"]) if score["at_stake"] else 100
    helpfulness = half_up(100 * score["served"] / score["asked"]) if score["asked"] else 100
    penalty = half_up(WASTE_SHARE * total * excess)
    percent = half_up(100 * max(0, score["kept"] + score["served"] - penalty) / total) if total else 100
    grade = {"capped": False, **_grade_key(score, core_breached, security, helpfulness, percent, excess, leak_tier)}
    return {**grade, "sec": security, "help": helpfulness, "penalty": penalty, "overall": percent}
