# Progress

Contract: docs/MASTER_PROMPT.md section 4.

## Phases
- [x] Phase 0 (A) Skeleton
- [x] Phase 1 (A) engine/ai.py
- [x] Phase 2 (A) Loader and tutorial level
- [x] Phase 3 (A) Level engine
- [x] Phase 4 (A) Grading
- [x] Phase 5 (A) Save and load
- [x] Phase 6 (B) Interface part 1
- [x] Phase 7 (B) Playback and results
- [x] Phase 8 (B) Tutorial guide
- [x] Phase 9 (A) More levels and balance test
- [x] Phase 10 (A) Endless engine
- [x] Phase 11 (B) Endless interface
- [x] Phase 12 Storage (part A done, part B done)
- [x] Phase 13 Final checks (part A done, part B done)

## Decisions
- Person A works on one branch, dong/auto-run, with one pull request for phases 0 to 13A (user request).
- CLAUDE.md contract and scenario shape sections now point to docs/MASTER_PROMPT.md section 4.
- test_engine.py now just runs tests/run_all.py.

- call_ai reads USE_FAKE_AI at call time (not import time), so tests can switch it per process.

- scenarios/cafe.json is a copy of docs/cafe.json (old prototype format removed). The loader also accepts attack type "combined", used by the content file.
- The old app.py, engine/easy.py and engine/rounds.py no longer work with the new cafe.json. Expected, Phase 6 (James) rewrites app.py; Phases 3 and 10 replace the old engine files.

- security and helpfulness totals count only the zones attacked or asked about in the played package (same as docs/check_cafe_design.py). Zones nobody touched stay safe on the map but add no points.
- Event steps start at 1, like docs/sample_results.json.
- engine/easy.py deleted in Phase 3, superseded by engine/level.py.

- Grading: "perfect" also needs no length penalty (written rules up to 400 characters). Scores and percentages are rounded to whole numbers.

- import_game accepts "events" at the top level of the record or inside a nested "result" dict.

- Phase 9: the optional level_3 and level_4 were not added (content was frozen in docs/cafe.json). tests/test_balance.py checks every level of every scenario.

- Endless: a secret found in ANY reply (attacker or customer) marks its zone lost on that event. An attack outcome is "leaked" if its reply leaked any secret. Secrets shorter than 6 letters or digits (the "$2.10" supplier price) only match as a whole token, so "2100" is not a leak.
- engine/rounds.py deleted and engine/judge.py rewritten in Phase 10 (superseded by engine/endless.py and the new judge). is_served is gone, use is_helpful.

- Storage: build_row stores rules_used only for tutorial/level, rules_chars only for endless, guide_skipped only for tutorial, ai_model and ai_temperature only for endless. ENGINE_VERSION is "1.0.0". record_play is offline tested only (no Supabase keys yet).

## Notes for James
- Contract check of your branch claude/practical-mayer-3uwyov (not merged into main yet): ui/data.py calls load_scenario, pick_package and run_level with the section 4 names and shapes. No mismatch found. With this branch your tests/test_app_smoke.py passes against the real engine (checked in a scratch worktree, your files untouched).
- Small difference only in your stand-in (_standin_run_level): it counts every zone of a ring in the totals, the real engine counts only zones attacked or asked about. The stand-in is no longer used once engine/level.py exists.
- main's app.py still imports engine.easy and engine.rounds, which this branch deletes, so app.py on main will not start until your Phase 6 app.py is merged. Expected (master prompt Phase 0 notice).
- Both branches create docs/PROGRESS.md, so the second one merged will get a merge conflict there. Keep both sets of ticks and notes.
- Phase 13 part A: tests pass, no .env, data/ or key like strings (AIza, sb_, eyJ) tracked, requirements.txt installs on Python 3.14.

## Frontend notes (B, James)
Phases 6, 7, 8, 11, 12B and 13B are done. Optional phases 15 and 17 (Endless run interface, level path) were not started. Everything was checked in a real browser with USE_FAKE_AI=true; nothing has been run against real Gemini or Supabase (no keys).

### Decisions
- Map rendering: `st.html` strips SVG in Streamlit 1.67 (the map came out empty), so ui/common.py shows it with `st.markdown(..., unsafe_allow_html=True)` inside a `<div>` so markdown never touches the labels. Every label is escaped in ui/map.py. The map marks a lost inner, sensitive or core zone "leaked" and a lost outer zone "refused" (words, not only colour).
- ui/data.py is the only file in ui/ that imports engine/ and always uses the real engine (the Phase 6 stand-in scenario was removed).
- Playback: a `st.fragment(run_every=0.5)` advances the chat on its own (delay grows with reply length, Slow/Normal/Fast multiply it). The scrubber must not use `on_change` or a forced session value: a timer tick sent the browser's stale slider value back and reset the chat to message 1. It now has a new key per step and any value other than the current message is treated as the player's drag.
- Tutorial guide: sections are `st.container(key="sec_<target>")`, the highlight is CSS on `.st-key-sec_<target>` and the other sections of the screen are dimmed. Step 7 pauses the chat until it is closed. Pressing Start early jumps the guide to step 7.
- Every screen change scrolls to the top with a small script through `st.html(..., unsafe_allow_javascript=True)`. Streamlit only re-runs a script whose text changed, so the script text carries a counter.
- Consent: the checkbox is per run (key includes run_id), unticked by default, and `record_play` is called at most once per run. Loaded saves have no checkbox and are never graded or stored. The player is told when storage is not set up.
- Endless: 30 second cooldown (`ENDLESS_COOLDOWN_SECONDS` in ui/endless.py) counted down by a fragment. Explanations for Endless are built in ui/playback.py (`explain_endless`) from the leaked and refused events, because the engine has no explain function for sections.
- The level screen shows `level["story"]` when present, otherwise the scenario description. Rule cards show the label (toggle) and the rule text only, never side effects. Order is JSON order until Phase 16.
- A Level mode run counts as a pass at one star or more and unlocks the next level; the progress lives in the browser session only.

- Interface redesign (after feedback that the first interface looked bad): the look follows the team's browser demo, used as a design reference only. Nothing from the demo was copied or committed; the stylesheet, the map and the screens were written from scratch for this repo. It is a "blue team console": a top bar with navigation, a three column play screen (rule shop, system core map, chat), a blue ramp for the map rings (the closer to the centre, the darker), hatching for a turned away customer, dark for a breached secret, a live points tally, and chat bubbles with colour coded judge chips. The demo's own JavaScript engine, its server.py and its API key page were not used: the Python engine, the fake AI default and the "no key field in the UI" rule are unchanged.
- ui/theme.py holds one stylesheet. Custom blocks are `st.container(key=...)` (Streamlit exposes the key as a CSS class), and all message text still goes through `st.text` / `st.markdown`, never raw HTML; SVG built in ui/map.py is the only HTML. The app is locked to a light theme in .streamlit/config.toml, because mixing Streamlit's light widgets with a dark page made the message text unreadable.
- Streamlit gives caption and markdown containers a negative bottom margin that offsets the paragraph margin. Zeroing the paragraph margin alone made the next element overlap the text, so both are removed together inside our own blocks.
- The map takes `state` (lost zones), `marks` (served or safe) and `focus` (the attacked or asked about zone, drawn with a flashing outline). The playback derives them from the events, and shows a tally of secret points kept, public points served and points lost.
- A replay of a loaded save shows the rules stored in the save when they are there, and still works when they are not (a test covers both).
- Fonts are the system fonts on purpose: no request to an outside font server, so the game works offline.

### Notes
- tests/test_app_smoke.py (B) covers the map, the engine contract against docs/sample_results.json, playback, results, save and load, the guide walkthrough, Endless, the cooldown and the consent rules. It is picked up by tests/run_all.py.
- Known limits: the level select and progress reset when the page is reloaded; Endless was only run with fake AI replies, so helpfulness is low there until a real key is used.


## Arena parity (B, James): the game now follows the original browser demo
Branch james/arena-parity. The goal was to make the Streamlit game the same game as the team's browser demo, with every feature the demo had, and to keep the features added here, restyled to match. The demo is a design and rules reference only: its HTML, JavaScript, server and key page are not in this repo, and no code was copied. The content tables (three businesses, rule cards, twelve levels, attack and customer scripts) were carried over as JSON data, the logic was rewritten in Python.

### What changed
- engine/arena/ is a pure Python port of the demo: worlds with four rings (10/25/50/150 points), rule cards with the defenses they cover, bundles, topic bans and a lockdown card, per-try shops, a fast evaluator and a cheapest-perfect-set search, grading (waste share 14%, stars at 85/70/50, security 50 and helpfulness 30 to pass, a breached core is an instant loss), Endless sections, a plain English rules reader, and live AI helpers that go through call_ai(). Content is in scenarios/arena/*.json (a subfolder, so the earlier scenario loader and tests are untouched).
- The interface is rebuilt around it: top bar, home, level map, rule shop with compute costs, System Core map with hours, deals, loyalty and the rest, the chat with judge lines, report notes, replay with a timeline, Endless (lobby, sections, section report, run over, record board), Records and Settings.
- Kept from before and restyled: the tutorial guide (adapted to the compute mechanics), consent once per run with anonymous storage, and replay speeds.

### Differences from the demo, on purpose
- There is no API key field in the game. The key stays in .env (project rule). Settings only shows whether live AI and storage are set up, never a value.
- The record board is a local file (data/records.json, git ignored), not a shared server board.
- Level progress and Endless section bests are saved in the browser (localStorage, through ui/progress.py by Boctok0); Settings can reset them.
- The level map is the demo's winding path: numbered bubbles (locked, next, done, perfect), stars earned below, a dotted line through them and a banner for each business.
- No JSON file upload or download anywhere. Save my game, Load my game and the progress export and import were removed (by request). engine/save.py is unchanged and still tested.
- The 30 second pause between Endless runs only applies with live AI (it protects the free quota).
- Notes name the missing defense on a leak, but never say which rules were unnecessary (as in the demo).

### Notes
- This work touches engine/, scenarios/ and tests/ (Dong's folders): engine/arena/, scenarios/arena/, tests/test_arena.py, tests/test_ui_pure.py and a rewritten tests/test_app_smoke.py. ui/screens.py and ui/playback.py were deleted because the new screens replace them. The old engine, loader, storage and save modules are unchanged and still pass their tests.
- Tests: tests/test_arena.py (engine), tests/test_ui_pure.py (map, local files, saves, notes, Endless run) and tests/test_app_smoke.py (flows in Streamlit's AppTest). Every shop of every level and package is checked to allow a Perfect round.

### Look and flow changes after review (B, James)
- The theme now follows the system, light or dark, with the demo's own colour tokens (ui/theme.py, and `[theme.light]` / `[theme.dark]` in .streamlit/config.toml so Streamlit's widgets match). This replaces the earlier decision to lock a light theme. The map has `--t2-ink` / `--t3-ink` tokens because the core is light and its text dark in dark mode.
- Fonts are the demo's (Archivo, Atkinson Hyperlegible, IBM Plex Mono) loaded from Google Fonts, with system fallbacks. This replaces the earlier "system fonts only" decision, and means the page makes one request to fonts.googleapis.com.
- Rule cards use checkboxes (not toggles), the compute cost on the right in gold.
- The chat is a phone-style window: logo, name and status in the header, a fixed height with its own scrollbar, the sender above each bubble.
- When the chat reaches its last message the report opens by itself after 1.2 seconds (the round, and an Endless section). It happens once per round, so Close does not bounce back. The Report button stays as a fallback.
- Icons are inline SVG drawn in ui/icons.py (shield, cup, car, cap, bolt), not emoji, so they line up in the top bar, business banners, chat header and rule costs. The chat is a phone frame: bezel, speaker slot, status bar, home bar and a fixed 44rem height whose body scrolls.

## Browser game as the main interface (branch james/aalebell-fork)
This branch is the browser demo fork (AAlebell/Hackathon-James-trian-fork-2026, the original demo split into ES modules) with all of `main` merged in. The browser game is now the main interface and the Streamlit game is kept.

- Front end: `index.html`, `css/`, `js/`, `data/` are the fork's, with only these changes: the developer panel for typing an API key is replaced by an AI connection panel (status, test button, no key field), and reports have a consent box (js/services/share.js).
- Back end: `server.py` is rewritten on the Python engine. AI replies and attacks go through `call_ai()` (Gemini, key in `.env` only), records through `engine/records.py` (one file, `local_data/records.json`, shared with the Streamlit game), anonymous plays through `engine/storage.py`. The fork's Anthropic client, passcode, `/api/dev/*` endpoints and key saving are gone (hard rule: no key typed into the game).
- `engine/records.py` is new (the logic that was in `ui/store.py`, which is now a thin adapter). `engine/arena/live.py` gained helpers for the browser game (`chatbot_reply`, `plan_attacks`, `is_ready`).
- `.gitignore` tracks the fork's `data/` folder and ignores `local_data/` (the record board).
- Tests: `tests/test_server.py` (static files, same-origin POSTs, validation, records, AI helpers, no key endpoints) and `tests/test_front_parity.py` (Node loads `data/` and compares worlds, cards and levels with `scenarios/arena/`; all JavaScript parses and its imports exist). The browser flow was also walked through in a real browser: tutorial, consent box, Endless, record board, settings.
- Not done: the browser game has no tutorial skip button (so `guide_skipped` is always false), and the Streamlit-only extras (the 10-step highlight guide, Continue / Start over on Home) are not in the browser game.
