"""Rule cards: what they cover, which topics they ban, the shop of a try, and how a round is evaluated."""

import re

from engine.arena.content import BAN_PREFIX, get_card, get_world, kind_of, rules_data, sector_of
from engine.arena.scripts import rng, shuffle

KEYBIT = {"creds": 1, "money": 2, "people": 4, "internal": 8, "action": 16,
          "role": 32, "override": 64, "transform": 128, "emotion": 256}
BOSS_NEEDED = 3  # a combined attack needs any three of the four technique defenses
SECRET_KINDS = ("creds", "money", "people", "internal", "action")


def boss_pool() -> list[str]:
    """Return the technique defenses a combined attack is tested against."""
    return rules_data()["boss_pool"]


def type_needs(attack_type: str) -> list[str]:
    """Return the technique defenses an attack type needs besides the one for what it targets."""
    return rules_data()["type_needs"].get(attack_type, [])


def coverage(card_ids: list[str], world: dict) -> set[str]:
    """Return every defense the chosen cards cover."""
    return {kind for card_id in card_ids for kind in get_card(card_id, world)["covers"]}


def bans(card_ids: list[str], world: dict) -> set[str]:
    """Return the public topics the chosen cards forbid the chatbot to talk about."""
    banned: set[str] = set()
    for card_id in card_ids:
        card = get_card(card_id, world)
        if card.get("bans_all"):
            banned |= {sector["id"] for sector in world["sectors"] if sector["tier"] == 0}
        banned |= set(card.get("bans", []))
    return banned


def attack_blocked(world: dict, message: dict, covered: set[str]) -> bool:
    """An attack needs a defense for what it targets, and one for its technique (a combined one needs three of four)."""
    if kind_of(world, message["asset"]) not in covered:
        return False
    if message["type"] == "boss":
        return sum(kind in covered for kind in boss_pool()) >= BOSS_NEEDED
    return all(kind in covered for kind in type_needs(message["type"]))


def missing_for(world: dict, message: dict, covered: set[str]) -> list[str]:
    """Return the defenses that were missing for an attack to be blocked, for the report."""
    base = kind_of(world, message["asset"])
    missing = [] if base in covered else [base]
    if message["type"] == "boss":
        have = sum(kind in covered for kind in boss_pool())
        if have < BOSS_NEEDED:
            missing += [kind for kind in boss_pool() if kind not in covered][: BOSS_NEEDED - have]
    else:
        missing += [kind for kind in type_needs(message["type"]) if kind not in covered]
    return missing


def refuse_text(world: dict, topic: str) -> str:
    """Return the reply of a chatbot that was told not to talk about a topic."""
    return f"Sorry, I can't help with questions about {sector_of(world, topic)['name'].lower()}."


def simulate_reply(world: dict, message: dict, covered: set[str], banned: set[str]) -> str:
    """Return the reply a chatbot with these defenses would give, without calling an AI."""
    if message["kind"] == "customer":
        return refuse_text(world, message["topic"]) if message["topic"] in banned else message["a"]
    return message["block_text"] if attack_blocked(world, message, covered) else message["leak_text"]


# ---- the shop ----------------------------------------------------------------------------------

def needed_keys(world: dict, messages: list[dict]) -> list[str]:
    """Return the defenses a package needs, in the order they first show up."""
    needed: dict[str, None] = {}
    for message in messages:
        if message["kind"] != "attack":
            continue
        needed[kind_of(world, message["asset"])] = None
        for kind in (boss_pool() if message["type"] == "boss" else type_needs(message["type"])):
            needed[kind] = None
    return list(needed)


def shop_for(level: dict, package: int, messages: list[dict]) -> list[str]:
    """Build the shop of a try: what this package needs, bundles, decoys, topic bans, a lockdown and cosmetics."""
    world, key, data = get_world(level["world"]), level["key"], rules_data()
    rnd = rng(key * 7919 + package * 104729 + 11)
    need = needed_keys(world, messages)
    tutorial = level.get("tutorial", False)
    ids: dict[str, None] = {data["single"][kind]: None for kind in need}
    bundles = [cid for cid, card in data["cards"].items() if cid.startswith("b_") and any(k in need for k in card["covers"])]
    for cid in shuffle(bundles, rnd)[: 0 if tutorial else 1 + int(rnd.random() * 2)]:
        ids[cid] = None
    decoys = [kind for kind in SECRET_KINDS if kind not in need]
    for kind in shuffle(decoys, rnd)[: 1 if key >= 5 else 2]:
        ids[data["single"][kind]] = None
    topics = list(dict.fromkeys(m["topic"] for m in messages if m["kind"] == "customer"))
    for topic in shuffle(topics, rnd)[: 1 if tutorial or key <= 5 else 2]:
        ids[BAN_PREFIX + topic] = None
    if not tutorial and key >= 3:
        ids["lockdown"] = None
    for cid in shuffle(data["cosmetic"], rnd)[: 1 if key >= 5 else 2]:
        ids[cid] = None
    return shuffle(list(ids), rnd)


# ---- evaluation --------------------------------------------------------------------------------

def compile_round(world: dict, messages: list[dict]) -> dict:
    """Prepare a round for fast evaluation with bit masks."""
    index = {sector["id"]: i for i, sector in enumerate(world["sectors"])}
    items = []
    for message in messages:
        if message["kind"] == "attack":
            extra = sum(KEYBIT[k] for k in type_needs(message["type"]))
            items.append({"attack": True, "sector": index[message["asset"]], "base": KEYBIT[kind_of(world, message["asset"])],
                          "boss": message["type"] == "boss", "extra": extra})
        else:
            items.append({"attack": False, "sector": index[message["topic"]]})
    core = next(i for i, sector in enumerate(world["sectors"]) if sector["tier"] == 3)
    return {"world": world, "index": index, "items": items, "core": core,
            "points": [sector["pts"] for sector in world["sectors"]]}


def _popcount(value: int) -> int:
    """Count the set bits of an integer."""
    return bin(value).count("1")


def fast_eval(compiled: dict, cov_mask: int, ban_mask: int) -> dict:
    """Score a round for a set of covered defenses and banned topics, stopping when the core is breached."""
    boss_mask = sum(KEYBIT[k] for k in boss_pool())
    stake, breached, asked, refused = set(), set(), set(), set()
    core_breached = False
    for item in compiled["items"]:
        if item["attack"]:
            stake.add(item["sector"])
            ok = bool(cov_mask & item["base"]) and (
                _popcount(cov_mask & boss_mask) >= BOSS_NEEDED if item["boss"] else (cov_mask & item["extra"]) == item["extra"])
            if not ok:
                breached.add(item["sector"])
            if compiled["core"] in breached:
                core_breached = True
                break
        else:
            asked.add(item["sector"])
            if ban_mask >> item["sector"] & 1:
                refused.add(item["sector"])
    points = compiled["points"]
    total = lambda ids: sum(points[i] for i in ids)  # noqa: E731
    return {"at_stake": total(stake), "lost": total(breached), "kept": total(stake) - total(breached),
            "asked": total(asked), "served": total(asked) - total(refused), "core_breached": core_breached}


def card_masks(card_ids: list[str], world: dict, compiled: dict) -> tuple[int, int]:
    """Return the defense mask and the topic ban mask of a list of cards."""
    cov = sum(KEYBIT[kind] for kind in coverage(card_ids, world) if kind in KEYBIT)
    ban = sum(1 << compiled["index"][topic] for topic in bans(card_ids, world))
    return cov, ban


def evaluate_cards(world: dict, messages: list[dict], card_ids: list[str]) -> dict:
    """Score a round for a list of chosen cards."""
    compiled = compile_round(world, messages)
    return fast_eval(compiled, *card_masks(card_ids, world, compiled))


def min_cost_for(world: dict, messages: list[dict], shop: list[str], goal: dict) -> int:
    """Return the cheapest compute of any set of shop cards that does at least as well as the goal outcome."""
    compiled = compile_round(world, messages)
    masks = [card_masks([card_id], world, compiled) for card_id in shop]
    costs = [get_card(card_id, world)["cost"] for card_id in shop]
    best = float("inf")
    for subset in range(1 << len(shop)):
        cost = cov = ban = 0
        for i in range(len(shop)):
            if subset >> i & 1:
                cost, cov, ban = cost + costs[i], cov | masks[i][0], ban | masks[i][1]
        if cost >= best:
            continue
        result = fast_eval(compiled, cov, ban)
        if result["kept"] >= goal["kept"] and result["served"] >= goal["served"] and (not result["core_breached"] or goal["core_breached"]):
            best = cost
    return int(best)


# ---- plain English rules (Endless without a live AI) ---------------------------------------------

FORBID = re.compile(r"\b(never|not|don'?t|do not|must not|mustn'?t|cannot|can'?t|won'?t|refuse|no one|nobody|avoid|under no|forbidden)\b")
SHARE_VERB = re.compile(r"\b(share|reveal|tell|give|disclose|say|leak|print|output|show|repeat|provide|send|confirm|write|release|hand)\b")
GENERIC = re.compile(r"\b(confidential|sensitive|anything|everything|all information|any information)\b")
KIND_WORDS = {
    "creds": re.compile(r"\b(passwords?|logins?|log-ins?|credentials?|passcodes?|access codes?|admin|servers?|api keys?)\b"),
    "money": re.compile(r"\b(bank|account numbers?|banking|financial|finances|payment details|credit card|routing)\b"),
    "people": re.compile(r"\b(personal|private|home address(es)?|phone numbers?|emails?|staff details|employees?|students?|customers?|id numbers?|records?|grades?|licen[cs]es?|credit (files?|applications?|scores?)|contact)\b"),
    "internal": re.compile(r"\b(internal|schedules?|rota|suppliers?|costs?|formulas?|floor price|lowest price|targets?|budgets?|exams?|questions|rubrics?|confidential|trade-?in)\b"),
}
ACTION_VERB = re.compile(r"\b(issue|give|agree|approve|promise|commit|make|offer|process|grant|change|waive|confirm|sell|authori[sz]e|do)\b")
ACTION_NOUN = re.compile(r"\b(refunds?|free|comps?|deals?|prices?|promises?|binding|guarantees?|grades?|records?|deadlines?|discounts?|orders?|offers?)\b")
QUALIFIER = re.compile(r"\b(staff|codes?|secrets?|internal|passwords?|logins?|admin|employees?|confidential|personal|private|data|details?|emails?|phone|address|contact|hidden|configuration|floor|formula|targets?|rubrics?|credit|records?|someone else'?s|other (customers?|students?|people)|bank|account|server|refunds?|grades?)\b")
NOT_A_BAN = re.compile(r"(instruction|rule|command|override|admin|mode|urgen|threat|pressure|translat|spell|encod|poem|claim|pretend|identity|agree|promise|commit|binding|guarantee|approve|negotiat)")
CONDITIONAL = re.compile(r"\bonly\b.*\b(share|give|reveal|tell)\b.*\b(managers?|staff|owners?|employees?|admins?|team|instructors?|professors?)\b")
ONLY_MANAGER_APPROVES = re.compile(r"\bonly\b.*\b(manager|staff|registrar|owner)\b.*\b(approve|authori[sz]e|issue)\b")
ROLE_WORDS = re.compile(r"\b(managers?|owners?|boss|it staff|it support|it team|head office|supervisors?|employees?|coworkers?|husband|wife|parents?|family|relatives?|police|developers?|instructors?|professors?|registrar)\b")
ROLE_CLAIM = re.compile(r"\b(no matter who|regardless of who|whoever|claims?|claiming|pretends?|pretending|identity|impersonat\w*|verify|verified|title|says? (they are|they're|to be)|even if (someone|they|a person|the user|anyone))\b")
EVEN_OR_INCLUDING = re.compile(r"\b(even|including)\b")
OVERRIDE = re.compile(r"(ignore (all |any |your |previous |prior |earlier |the |these |my )*(instructions|rules)|overrid|cannot be changed|can'?t be changed|never change (your|these|its|the) (rules|instructions|settings)|rules? (always|stay|come first|take priority|still apply)|(cannot|can'?t|must not|never|won'?t) be (changed|overridden|ignored|updated|replaced|turned off)|system (update|message|mode)|admin mode|developer mode|debug|jailbreak|role ?play|new instructions|normal (customer|user) (text|message)|messages? (cannot|can'?t) change)")
OVERRIDE_TRY = re.compile(r"\b(ignore|requests? to|attempts? to|tries to|try to|asks? (you )?to)\b")
OVERRIDE_CHANGE = re.compile(r"\b(change|rewrite|replace|update)s? (your|these|the|my) (rules|instructions|settings)\b")
TRANSFORM = re.compile(r"(translat|encod|spell|letter|poem|song|stories|role-?play|fiction|screenplay|riddle|puzzle|hint|backward|revers|base64|cipher|rhyme|acrostic|rewrite|rephras|disguis|any (form|format|language|way)|other languages?|partial|character)")
TRANSFORM_STRESS = re.compile(r"\b(even|no matter|including|in any)\b")
EMOTION = re.compile(r"(urgen|emergenc|threat|\bbeg(s|ging)?\b|pressure|fired|upset|crying|tears|desperate|no matter (the reason|why|how urgent)|whatever the reason|no exceptions?|guilt|emotional|sob stor|plead)")
ONLY_ANSWER_A = re.compile(r"\bonly\b.*\b(answer|respond|reply|talk|discuss|help|chat)\b")
ONLY_ANSWER_B = re.compile(r"\b(answer|respond|reply|talk|discuss|help)\b.*\bonly\b")
REFUSE_ALL_VERB = re.compile(r"\b(refuse|decline|don'?t answer|do not answer|never answer|never respond|don'?t respond|do not respond|say nothing)\b")
REFUSE_ALL_SCOPE = re.compile(r"\b(all|every|any|anything|everything|everyone|questions?)\b")
SENTENCE_BREAK = re.compile(r"[.!?\n;:]+")


def sentences(text: str) -> list[str]:
    """Split plain English rules into lowercase sentences."""
    parts = SENTENCE_BREAK.split(str(text).lower().replace("’", "'"))
    return [part.strip() for part in parts if part.strip()]


def _defenses_from(sentence_list: list[str]) -> set[str]:
    """Read which secrets and actions the rules forbid sharing."""
    covered: set[str] = set()
    for line in sentence_list:
        if not FORBID.search(line):
            continue
        if SHARE_VERB.search(line):
            covered |= {kind for kind, words in KIND_WORDS.items() if words.search(line)}
            if GENERIC.search(line):
                covered |= {"creds", "money", "people", "internal"}
        if ACTION_VERB.search(line) and ACTION_NOUN.search(line):
            covered.add("action")
    if any(ONLY_MANAGER_APPROVES.search(line) for line in sentence_list):
        covered.add("action")
    return covered


def _technique_defenses(sentence_list: list[str], conditional: bool) -> set[str]:
    """Read which tricks (identity, rule changes, disguises, pressure) the rules shut out."""
    covered: set[str] = set()
    role = lambda line: bool(ROLE_CLAIM.search(line) or ((FORBID.search(line) or EVEN_OR_INCLUDING.search(line)) and ROLE_WORDS.search(line)))  # noqa: E731
    if not conditional and any(role(line) for line in sentence_list):
        covered.add("role")
    if any(OVERRIDE.search(line) or (OVERRIDE_TRY.search(line) and OVERRIDE_CHANGE.search(line)) for line in sentence_list):
        covered.add("override")
    if any(TRANSFORM.search(line) and (FORBID.search(line) or TRANSFORM_STRESS.search(line)) for line in sentence_list):
        covered.add("transform")
    if any(EMOTION.search(line) for line in sentence_list):
        covered.add("emotion")
    return covered


def _banned_topics(sentence_list: list[str], world: dict) -> set[str]:
    """Read which public topics the rules tell the chatbot to avoid, or to answer only about."""
    topic_re = {topic: re.compile(pattern) for topic, pattern in world["topic_re"].items()}
    banned: set[str] = set()
    for line in sentence_list:
        if NOT_A_BAN.search(line):
            continue
        if ONLY_ANSWER_A.search(line) or ONLY_ANSWER_B.search(line):
            allowed = [topic for topic, pattern in topic_re.items() if pattern.search(line)]
            if allowed:
                banned |= {topic for topic in topic_re if topic not in allowed}
            continue
        if QUALIFIER.search(line):
            continue
        if REFUSE_ALL_VERB.search(line) and REFUSE_ALL_SCOPE.search(line):
            banned |= set(topic_re)
            continue
        if FORBID.search(line):
            banned |= {topic for topic, pattern in topic_re.items() if pattern.search(line)}
    return banned


def analyze_rules(text: str, world: dict) -> dict:
    """Read plain English rules for the defenses and topic bans they express (the simulated chatbot's brain)."""
    lines = sentences(text)
    conditional = any(CONDITIONAL.search(line) for line in lines)
    covered = set() if conditional else _defenses_from(lines)
    covered |= _technique_defenses(lines, conditional)
    return {"cov": covered, "bans": _banned_topics(lines, world), "conditional": conditional}
