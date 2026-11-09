# Chatbot Defense Arena

natHacks 2026 project (Defense & Security theme). A game where the player defends a
small business chatbot against prompt injection attacks. It has two front ends on one Python engine:
the **browser game** (`index.html`, `css/`, `js/`, `data/`, served by `server.py`, the main UI) and the
**Streamlit game** (`app.py`, `ui/`). Points are earned for blocking
attacks AND for still serving real customers, so "refuse everything" never wins.

## Hard rules
- All code, comments, docstrings, commit messages and UI text are in English.
- Python 3.11+. Streamlit for the Streamlit interface; plain HTML, CSS and ES modules (no build step, no npm packages) for the browser interface.
- Never hardcode API keys. Keys live in `.env` (gitignored). Never print or log them.
- Every AI call goes through `call_ai()` in `engine/ai.py`. Nothing else imports an AI SDK.
- Game content lives in `scenarios/*.json`, never hardcoded in Python.
- Keep functions small, typed, and with a one line docstring.
- Do not change the contract without telling the whole team first.

## Folder ownership
- Person A (Dong): `engine/`, `scenarios/`, `tests/`
- Person B (James): `app.py`, `ui/`, `index.html`, `css/`, `js/`, `data/`, `server.py`, `README.md`, `docs/`

## Working together
Two people, each with their own Claude account, share this repo. GitHub is the only
shared space, so these rules keep both sessions from overwriting each other.
- Never push to `main`. Work on your own branch (`<your-name>/<topic>`), open a pull
  request, and let the other person review and merge it.
- Run `git pull origin main` before starting and rebase or merge it before opening a PR.
- Keep PRs small and stay inside your folders (see Folder ownership). If a change must
  touch the other person's folder, say so in the PR description.
- Never delete files in bulk. A deletion goes through a PR with the reason written in it.
- If you change the contract, update it in the same PR and tell the other person.
- `python test_engine.py` must pass before you open a PR.
- Never commit `.env` or any API key.

## Contract
The engine to interface contract and the scenario JSON shape are in
`docs/MASTER_PROMPT.md` section 4. That file wins over everything else.
Show AI replies and player text with `st.text`, never as HTML or markdown. In the browser game, escape
every text with `esc()` before it goes into HTML. `server.py` never serves code, `.env` or dotfiles, and
there is no page or endpoint for typing an API key: it stays in `.env`.

## Running
- `USE_FAKE_AI=true` (default) returns canned replies and costs no tokens. Use it while building UI.
- `python tests/run_all.py` (or `python test_engine.py`) runs every test.
- `python server.py` starts the browser game at http://localhost:8000 (the main UI; live AI, record board and
  anonymous storage go through the Python engine).
- `streamlit run app.py` starts the Streamlit game (same engine, same record board file `local_data/records.json`).
- `tests/test_front_parity.py` checks that `data/` (browser) and `scenarios/arena/` (Python) describe the same game.
