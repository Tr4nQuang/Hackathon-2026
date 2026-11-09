# How Chatbot Defense Arena works (the short version)

A one-page tour for teammates. The full detail is in `README.md`.

## The game in one sentence

You defend a small business chatbot against prompt injection. You score for **secrets kept** (security) and
**real customers served** (helpfulness), so "refuse everything" never wins.

## One shift, step by step

1. **Intel.** You see what the attackers are after (and, early on, how).
2. **Rules.** You write the chatbot's rules in plain English, inside a **word budget**, so you can't guard everything.
3. **Visitors.** Messages arrive one at a time. Nobody says who is an attacker. You **Block** (a few per shift) or
   **Let it through** before a countdown ends. Blocking a real customer turns them away.
4. **Report.** Stars, security %, helpfulness %, words used, and notes on every leak and every customer turned away.

## The System Core map

Each business is a map of four rings. A secret's value grows toward the centre:
public 10 · internal 25 · sensitive 50 · core (admin password) 150.
An internal leak caps the grade at 2 stars, a personal data or money leak fails the shift, and a breached core is an
instant loss.

## Two modes

| | Campaign (Levels) | Endless: Siege |
|---|---|---|
| What | Tutorial + 12 hand-made levels over 3 businesses | Shift after shift until trust runs out |
| Gets harder by | Blocks from level 4, VIP clients from level 6, less intel | Budget 22 → 11 words, countdown 12 s → 4 s, more attackers |
| Special | Each try draws 1 of 4 attack packages | Attackers read your last rules and target the gaps; leaks cost trust |

## Where things live in the code

| Folder | Owner | What is in it |
|---|---|---|
| `engine/arena/` | Dong | The game rules: rule reader (`rules.py`), rounds and visitors (`rounds.py`), grades (`grade.py`), levels (`campaign.py`), Siege (`endless.py`), live AI (`live.py`) |
| `engine/` | Dong | `ai.py` (the only place that calls Gemini), `storage.py` (opt-in research data), `export.py` (the run file) |
| `scenarios/arena/` | Dong | All content as JSON: businesses, levels, Endless tuning, attack and customer scripts |
| `ui/` and `app.py` | James | The Streamlit screens. `ui/data.py` is the only file that talks to `engine/` |
| `tests/` | Dong | `python test_engine.py` runs every test |

## AI or no AI

- **Default (`USE_FAKE_AI=true`):** no key needed. Attacks come from scripts and a simulated chatbot reads your rules.
  Levels always work this way.
- **Live (Endless only):** with `GEMINI_API_KEY` and `USE_FAKE_AI=false`, an attacker AI writes attacks around your
  rules and a real chatbot answers.
- Scoring is **always plain code**, never an AI, so it is objective and free.

## Data

Progress saves in the player's browser only. If a player ticks the consent box, one anonymous row per shift goes to
Supabase (when it is set up): scores, the rules they wrote, their block choices and the chat, with no name and with
email addresses and phone numbers removed.

## The lesson we want players to leave with

Rules in a prompt are only the first layer. The best defence is never giving a chatbot a secret it does not need.
