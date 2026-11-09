"""Turn a level or section result into a grade, stars and a score."""

import math

RULE_PENALTY = 5
LENGTH_PENALTY = 2
FREE_RULES_CHARS = 400
LENGTH_STEP_CHARS = 100
STAR_THRESHOLDS = ((3, 90), (2, 75), (1, 60))
PERFECT_STARS = 3


def _pct(side: dict) -> int:
    """Return earned over total as a whole percentage (100 when there is nothing to earn)."""
    return round(100 * side["earned"] / side["total"]) if side["total"] else 100


def penalty(result: dict, min_rules: int) -> int:
    """Return the points lost for extra rules and for long written rules."""
    extra_rules = max(0, result["rules_used"] - min_rules)
    extra_chars = max(0, result.get("rules_chars", 0) - FREE_RULES_CHARS)
    return RULE_PENALTY * extra_rules + LENGTH_PENALTY * math.ceil(extra_chars / LENGTH_STEP_CHARS)


def grade_level(result: dict, min_rules: int) -> dict:
    """Return grade ("perfect", "stars", "fail" or "lose"), stars, score and both percentages."""
    security, helpfulness = result["security"], result["helpfulness"]
    pcts = {"security_pct": _pct(security), "helpfulness_pct": _pct(helpfulness)}
    if result["core_hacked"]:
        return {"grade": "lose", "stars": 0, "score": 0, **pcts}
    total = security["total"] + helpfulness["total"]
    raw = 100 * (security["earned"] + helpfulness["earned"]) / total if total else 100
    score = max(0, round(raw - penalty(result, min_rules)))
    flawless = security["earned"] == security["total"] and helpfulness["earned"] == helpfulness["total"]
    if flawless and result["rules_used"] <= min_rules and penalty(result, min_rules) == 0:
        return {"grade": "perfect", "stars": PERFECT_STARS, "score": score, **pcts}
    for stars, threshold in STAR_THRESHOLDS:
        if score >= threshold:
            return {"grade": "stars", "stars": stars, "score": score, **pcts}
    return {"grade": "fail", "stars": 0, "score": score, **pcts}
