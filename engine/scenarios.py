"""Load game content from the scenarios folder."""

import json
from pathlib import Path

SCENARIO_DIR = Path(__file__).resolve().parent.parent / "scenarios"


def load_scenario(scenario_id: str) -> dict:
    """Load one scenario JSON file by its id, for example "cafe"."""
    path = SCENARIO_DIR / f"{scenario_id}.json"
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def list_scenarios() -> list[dict]:
    """Return id, name and description of every scenario, for the selection screen."""
    scenarios = []
    for path in sorted(SCENARIO_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
        scenarios.append(
            {"id": data["id"], "name": data["name"], "description": data.get("description", "")}
        )
    return scenarios
