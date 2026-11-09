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


def play_round(world: dict, messages: list[dict], get_reply: Callable[[dict], str], loose: bool = False) -> dict:
    """Play every message in order and return the log, the tally and the score. A breached core ends the round."""
    rec, names, customers = _Recorder(world), scripts()["names"], 0
    rec.push({"type": "sys", "text": f"{len(messages)} visitors will chat today"})
    core_id = core_of(world)["id"]
    for index, message in enumerate(messages):
        rec.push({"type": "sys", "cls": "new", "text": f"New chat · {clock(index)}"})
        who = message["attacker"] if message["kind"] == "attack" else names[customers % len(names)]
        customers += message["kind"] == "customer"
        reply = _reply_or_fallback(get_reply, message, rec.tally)
        if message["kind"] == "attack":
            _attack_entries(rec, message, who, reply)
        else:
            _customer_entries(rec, message, who, reply, index, loose)
        if core_id in rec.tally["breached"]:
            rec.tally["core_breached"] = True
            rec.push({"type": "sys", "cls": "alarm", "text": ALARM})
            break
    return {"log": rec.log, "tally": plain_tally(rec.tally), "score": tally_score(world, rec.tally)}
