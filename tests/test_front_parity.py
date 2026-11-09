"""The browser game (js/, data/) and the Python engine (engine/arena/, scenarios/arena/) must describe the same game.

The browser game keeps its content in JavaScript data files and the Python engine in JSON, so this test loads both
(with Node) and compares worlds, sectors, rule cards, levels and attack packages. Skipped when Node is not installed.
Run: python tests/test_front_parity.py
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.arena import content  # noqa: E402

DUMP = """
const [cards, levels, worlds] = await Promise.all([import('./data/cards.js'), import('./data/levels.js'), import('./data/worlds/index.js')]);
console.log(JSON.stringify({ order: worlds.WORLD_ORDER, worlds: worlds.WORLDS, cards: cards.CARDS, levels: levels.LEVELS, tutorial: levels.TUTORIAL }));
"""


def load_front() -> dict | None:
    """Return the browser game's content as JSON, or None when Node is missing."""
    node = shutil.which("node")
    if node is None:
        return None
    result = subprocess.run([node, "--input-type=module", "-e", DUMP], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr[-500:]
    return json.loads(result.stdout)


def test_worlds_match() -> None:
    """Same businesses in the same order, with the same sectors, points, tiers and customer topics."""
    front = load_front()
    if front is None:
        print("skip: node is not installed")
        return
    assert front["order"] == content.world_order()
    for world_id in content.world_order():
        mine, theirs = content.get_world(world_id), front["worlds"][world_id]
        assert (mine["name"], mine["short"], mine["bot"]) == (theirs["name"], theirs["short"], theirs["bot"]), world_id
        assert [(s["id"], s["tier"], s["pts"]) for s in mine["sectors"]] == [(s["id"], s["tier"], s["pts"]) for s in theirs["sectors"]], world_id
        assert sorted(mine["customers"]) == sorted(theirs["customers"]), world_id


def test_rule_cards_match() -> None:
    """Same rule cards with the same names, costs and defenses."""
    front = load_front()
    if front is None:
        return
    mine = content.rules_data()["cards"]
    assert sorted(mine) == sorted(front["cards"])
    for card_id, card in mine.items():
        theirs = front["cards"][card_id]
        assert (card["label"], card["cost"], sorted(card["covers"])) == (theirs["label"], theirs["cost"], sorted(theirs["covers"])), card_id


def test_levels_match() -> None:
    """Same twelve levels and tutorial: titles, businesses and attack packages."""
    front = load_front()
    if front is None:
        return
    mine = content.get_levels()
    assert len(mine) == len(front["levels"]) == 12
    for ours, theirs in zip(mine, front["levels"]):
        assert (ours["title"], ours["world"], ours["packs"]) == (theirs["title"], theirs["world"], theirs["packs"]), ours["id"]
    assert content.get_tutorial()["world"] == front["tutorial"]["world"]


def test_every_script_parses_and_every_import_exists() -> None:
    """Each JavaScript file is valid module syntax, and every relative import points at a file that exists."""
    node = shutil.which("node")
    for path in sorted(list((ROOT / "js").rglob("*.js")) + list((ROOT / "data").rglob("*.js"))):
        text = path.read_text(encoding="utf-8")
        if node:
            result = subprocess.run([node, "--input-type=module", "--check"], input=text, capture_output=True, text=True, timeout=30)
            assert result.returncode == 0, f"{path}: {result.stderr[-300:]}"
        for target in re.findall(r"from\s+[\"'](\.[^\"']+)[\"']", text):
            assert (path.parent / target).resolve().is_file(), f"{path} imports a missing file {target}"


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_") and callable(test):
            test()
            print(f"ok  {name}")
    print("test_front_parity OK")
