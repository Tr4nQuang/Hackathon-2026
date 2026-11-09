"""Play a round message by message and record a log the interface can show and replay."""

from typing import Callable

from engine.arena.content import core_of, rules_data, scripts, sector_of
from engine.arena.grade import tally_score
from engine.arena.judge import is_helpful, is_refusal, leaked_assets

OFFLINE_NOTE = "(No reply: the AI call failed, so this message was skipped.)"
ALARM = "CORE BREACHED · ROUND OVER"


def clock(index: int) -> str:
    """Return the time of day shown on the n-th chat of a round, starting around ten in the morning."""
    minutes = 10 * 60 + 12 + index * 4 + (index * 7) % 3
    hours = minutes // 60
    return f"{hours - 12 if hours > 12 else hours}:{minutes % 60:02d} {'PM' if hours >= 12 else 'AM'}"


def new_tally() -> dict:
    """Return an empty tally of what a round has put at stake, lost, asked and refused."""
    return {"at_stake": set(), "breached": set(), "asked": set(), "refused_topics": set(),
            "leaks": [], "refused": [], "offline": 0, "core_breached": False}


def plain_tally(tally: dict) -> dict:
    """Return a tally with lists instead of sets, so it can be saved as JSON."""
    return {key: sorted(value) if isinstance(value, set) else value for key, value in tally.items()}


class _Recorder:
    """Keeps the log, the map state and the tally of a round and stamps each entry with them."""

    def __init__(self, world: dict) -> None:
        self.world, self.state, self.tally, self.log = world, {}, new_tally(), []

    def push(self, entry: dict) -> None:
        """Add an entry with the map and the score as they are right after it."""
        self.log.append({**entry, "map": dict(self.state), "score": tally_score(self.world, self.tally)})


def _attack_entries(rec: _Recorder, message: dict, who: str, reply: str) -> None:
    """Record an attack, the chatbot's reply and the judge's verdict."""
    world, state, tally = rec.world, rec.state, rec.tally
    tally["at_stake"].add(message["asset"])
    if state.get(message["asset"]) != "breached":
        state[message["asset"]] = "target"
    label = rules_data()["type_label"][message["type"]]
    rec.push({"type": "msg", "role": "attacker", "name": who, "tag": f"Attacker · {label}", "text": message["text"]})
    rec.push({"type": "msg", "role": "bot", "name": world["bot"], "text": reply})
    leaked = leaked_assets(world, reply)
    action = sector_of(world, message["asset"])["kind"] == "action"
    if leaked:
        for sector_id in leaked:
            state[sector_id] = "breached"
            tally["breached"].add(sector_id)
            tally["at_stake"].add(sector_id)
        tally["leaks"].append({"message": message, "leaked": leaked})
        names = " and ".join(sector_of(world, sector_id)["name"].lower() for sector_id in leaked)
        rec.push({"type": "judge", "cls": "bad", "fn": "unapproved_action() → True" if action else "is_leaked() → True",
                  "text": f"{'Did' if action else 'Leaked'} {names}. Those points are gone."})
        return
    if state.get(message["asset"]) != "breached":
        state[message["asset"]] = "safe"
    rec.push({"type": "judge", "cls": "good", "fn": "unapproved_action() → False" if action else "is_leaked() → False",
              "text": "Nothing unapproved was done. Attack blocked." if action else "Nothing leaked. Attack blocked."})


def _customer_entries(rec: _Recorder, message: dict, who: str, reply: str, index: int, loose: bool) -> None:
    """Record a customer question, the reply, the verdict and the customer's closing line."""
    state, tally, texts = rec.state, rec.tally, scripts()
    tally["asked"].add(message["topic"])
    if state.get(message["topic"]) != "refused":
        state[message["topic"]] = "asking"
    rec.push({"type": "msg", "role": "customer", "name": who, "tag": "Customer", "text": message["q"]})
    rec.push({"type": "msg", "role": "bot", "name": rec.world["bot"], "text": reply})
    if is_helpful(reply, message["kw"], loose):
        if state.get(message["topic"]) != "refused":
            state[message["topic"]] = "served"
        rec.push({"type": "judge", "cls": "good", "fn": "is_helpful() → True", "text": "Customer got their answer."})
        rec.push({"type": "msg", "role": "customer", "name": who, "tag": "Customer", "text": texts["thanks"][index % len(texts["thanks"])]})
        return
    state[message["topic"]] = "refused"
    tally["refused_topics"].add(message["topic"])
    tally["refused"].append(message)
    rec.push({"type": "judge", "cls": "warn", "fn": "is_refusal() → True" if is_refusal(reply) else "is_helpful() → False",
              "text": "Customer was turned away. Public points lost."})
    rec.push({"type": "msg", "role": "customer", "name": who, "tag": "Customer", "text": texts["lost"][index % len(texts["lost"])]})


def _reply_or_fallback(get_reply: Callable[[dict], str], message: dict, tally: dict) -> str:
    """Ask for the chatbot's reply; when that fails use the scripted one and count the failure."""
    try:
        reply = get_reply(message)
        if isinstance(reply, str) and not reply.startswith("(AI error"):
            return reply
    except Exception:  # noqa: BLE001 a failed AI call must not end the round
        pass
    tally["offline"] += 1
    return message["a"] if message["kind"] == "customer" else message.get("block_text", OFFLINE_NOTE)


def _blocked_entries(rec: _Recorder, message: dict, who: str, index: int) -> None:
    """Record a message the player blocked before the chatbot saw it: an attack is stopped, a customer is turned away."""
    world, state, tally = rec.world, rec.state, rec.tally
    if message["kind"] == "attack":
        tally["at_stake"].add(message["asset"])
        tally["caught"].append(message)
        if state.get(message["asset"]) != "breached":
            state[message["asset"]] = "safe"
        label = rules_data()["type_label"][message["type"]]
        rec.push({"type": "msg", "role": "attacker", "name": who, "tag": f"Attacker · {label}", "text": message["text"]})
        rec.push({"type": "judge", "cls": "good", "fn": "guard.block() → attack", "text": "You blocked it before the chatbot saw it."})
        return
    tally["asked"].add(message["topic"])
    tally["refused_topics"].add(message["topic"])
    tally["refused"].append({**message, "by_guard": True})
    state[message["topic"]] = "refused"
    rec.push({"type": "msg", "role": "customer", "name": who, "tag": "Customer", "text": message["q"]})
    rec.push({"type": "judge", "cls": "warn", "fn": "guard.block() → customer", "text": "You blocked a real customer. Public points lost."})
    rec.push({"type": "msg", "role": "customer", "name": who, "tag": "Customer", "text": scripts()["lost"][index % len(scripts()["lost"])]})


def start_round(world: dict, messages: list[dict], loose: bool = False) -> dict:
    """Start a round that is played one message at a time (step), so the player can block messages as they arrive."""
    rec = _Recorder(world)
    rec.tally["caught"] = []
    rec.push({"type": "sys", "text": f"{len(messages)} visitors will chat today"})
    return {"rec": rec, "messages": messages, "index": 0, "customers": 0, "loose": loose, "done": not messages, "visits": []}


def pending(round_state: dict) -> dict | None:
    """Return the next message of the round, or None when the round is over."""
    return None if round_state["done"] else round_state["messages"][round_state["index"]]


def _visit(message: dict, blocked: bool, reply: str | None, tally: dict, before: tuple[int, int, int], how: str | None,
           seconds: float | None) -> dict:
    """Return the research record of one visitor: who it was, what the player decided, how fast, and what happened."""
    attack = message["kind"] == "attack"
    leaks, refused, offline = len(tally["leaks"]), len(tally["refused"]), tally["offline"]
    if blocked:
        outcome = "caught" if attack else "turned_away"
    elif attack:
        outcome = "leaked" if leaks > before[0] else "stopped"
    else:
        outcome = "refused" if refused > before[1] else "served"
    return {"kind": message["kind"], "technique": message.get("type"), "target": message.get("asset") if attack else message.get("topic"),
            "vip": bool(message.get("vip")), "decision": how or ("block" if blocked else "let"),
            "seconds": None if seconds is None else round(seconds, 1), "outcome": outcome,
            "leaked": tally["leaks"][-1]["leaked"] if outcome == "leaked" else [], "offline": offline > before[2],
            "text": message["text"] if attack else message["q"], "reply": reply}


def step(round_state: dict, get_reply: Callable[[dict], str], blocked: bool = False, how: str | None = None,
         seconds: float | None = None) -> None:
    """Play the next message: let the chatbot answer it, or (blocked) stop it before the chatbot sees it.

    how ("block", "let", "timeout" or "auto") and seconds (time to decide) are only recorded for research."""
    message, rec = pending(round_state), round_state["rec"]
    if message is None:
        raise ValueError("the round is over")
    index = round_state["index"]
    rec.push({"type": "sys", "cls": "new", "text": f"New chat · {clock(index)}"})
    names = scripts()["names"]
    who = message["attacker"] if message["kind"] == "attack" else names[round_state["customers"] % len(names)]
    round_state["customers"] += message["kind"] == "customer"
    before, reply = (len(rec.tally["leaks"]), len(rec.tally["refused"]), rec.tally["offline"]), None
    if blocked:
        _blocked_entries(rec, message, who, index)
    elif message["kind"] == "attack":
        reply = _reply_or_fallback(get_reply, message, rec.tally)
        _attack_entries(rec, message, who, reply)
    else:
        reply = _reply_or_fallback(get_reply, message, rec.tally)
        _customer_entries(rec, message, who, reply, index, round_state["loose"])
    round_state["visits"].append(_visit(message, blocked, reply, rec.tally, before, how, seconds))
    round_state["index"] += 1
    if core_of(rec.world)["id"] in rec.tally["breached"]:
        rec.tally["core_breached"] = True
        rec.push({"type": "sys", "cls": "alarm", "text": ALARM})
        round_state["done"] = True
    elif round_state["index"] >= len(round_state["messages"]):
        round_state["done"] = True


def finish_round(round_state: dict) -> dict:
    """Return the log, the tally and the score of a round."""
    rec = round_state["rec"]
    tally = plain_tally(rec.tally)
    tally.setdefault("caught", [])
    return {"log": rec.log, "tally": tally, "score": tally_score(rec.world, rec.tally), "visits": round_state["visits"]}


def play_round(world: dict, messages: list[dict], get_reply: Callable[[dict], str], loose: bool = False,
               blocked: frozenset = frozenset()) -> dict:
    """Play every message in order (blocking the ones whose index is in blocked) and return the log, the tally and the score."""
    round_state = start_round(world, messages, loose)
    while pending(round_state) is not None:
        step(round_state, get_reply, round_state["index"] in blocked)
    return finish_round(round_state)
