# Chatbot Defense Arena

natHacks 2026 project (Defense & Security theme). A game where the player defends a
small business chatbot against prompt injection attacks. Points are earned for blocking
attacks AND for still serving real customers, so "refuse everything" never wins.

## Hard rules
- All code, comments, docstrings, commit messages and UI text are in English.
- Python 3.11+ with Streamlit for the interface.
- Never hardcode API keys. Keys live in `.env` (gitignored). Never print or log them.
- Every AI call goes through `call_ai()` in `engine/ai.py`. Nothing else imports an AI SDK.
- Game content lives in `scenarios/*.json`, never hardcoded in Python.
- Keep functions small, typed, and with a one line docstring.
- Do not change the contract below without telling the whole team first.

## Folder ownership
- `engine/` game logic: AI calls, judge, rounds, easy mode
- `app.py`, `ui/` interface (Streamlit screens)
- `scenarios/` game content (JSON)
- `docs/`, `README.md` pitch, written summary, slides material

## Working together
Two people, each with their own Claude account, share this repo. GitHub is the only
shared space, so these rules keep both sessions from overwriting each other.
- Never push to `main`. Work on your own branch (`<your-name>/<topic>`), open a pull
  request, and let the other person review and merge it.
- Run `git pull origin main` before starting and rebase or merge it before opening a PR.
- Keep PRs small and stay inside your folders (see Folder ownership). If a change must
  touch the other person's folder, say so in the PR description.
- Never delete files in bulk. A deletion goes through a PR with the reason written in it.
- If you change the contract below, update it in the same PR and tell the other person.
- `python test_engine.py` must pass before you open a PR.
- Never commit `.env` or any API key.

## Contract (engine to interface)
```python
from engine.rounds import run_round      # medium mode
from engine.easy import resolve_choice   # easy mode
from engine.scenarios import load_scenario, list_scenarios

run_round(scenario: dict, player_rules: str, level_index: int = 0) -> dict
# {
#   "messages": [
#     {"sender": "attacker" | "customer", "text": str, "reply": str,
#      "leaked": bool, "served": bool}
#   ],
#   "security_score": int, "helpfulness_score": int,
#   "total_attacks": int, "total_customers": int
# }

resolve_choice(scenario: dict, level_index: int, card_id: str) -> dict
# {"outcome": "correct" | "leaked" | "too_strict",
#  "messages": [same shape as above], "coach_tip": str, "feedback": str}
```

## Scenario JSON shape
See `scenarios/cafe.json`. Top level keys: `id`, `name`, `description`, `secrets`,
`chatbot_prompt`, `customer_questions` (each with `text` and `expected_keywords`), `levels`.
Each level: `title`, `attack_type`, `story`, `attacks`, `rule_cards`, `easy_mode`, `coach_tip`.

## Running
- `USE_FAKE_AI=true` (default) returns canned replies and costs no tokens. Use it while building UI.
- `python test_engine.py` checks the engine without the interface.
- `streamlit run app.py` starts the game.
