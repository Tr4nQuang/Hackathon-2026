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

## Continue after closing, and the Endless run file (branch james/resume-and-export)
- Continue: the Endless run in progress is saved in the same browser object as the level progress (ui/progress.py, key `run`, validated field by field on load). It holds the section to play next, score, cleared count, the rules text, the seed, and one history row per section (with its run file row). It is saved after every section and when the run is ended, and replaced when a new run plays its first section. Home and the Endless lobby show Continue. This changes the earlier rule "nothing you type is saved": the rules text is now kept in the player's own browser (localStorage) only, so a run can really continue; nothing is sent anywhere.
- The chat of earlier sections is not kept (too big for localStorage), so a continued run has no replay of sections played before closing, and anonymous Supabase storage only covers sections played in this session.
- Run file: engine/export.py writes one CSV row per section (27 columns). Why CSV: opens in Excel or Sheets, merges by stacking, one flat record per section. UTF-8 with a BOM for Excel, CRLF lines, formula-looking cells get an apostrophe (CSV injection), emails and phone numbers are removed from the rules (`rules_redacted` says so), no name. Nothing is sent by the game: the player downloads and sends the file. tools/merge_runs.py (for the admin) merges many files, skips bad ones, drops duplicate sections and prints a summary.
- Tests: tests/test_export.py (rows, redaction, CSV safety, round trip, merge tool), tests/test_progress.py (saved run validation) and flows in tests/test_app_smoke.py (save, close, continue, failed run, Start over, one download only).

## Siege: Endless redesign and leak caps (branch james/siege-redesign)
Feedback after playing: the Endless run started with a ready-made rule that could pass everything, one perfect rule carried every section, the live AI attacker had no clear mission, difficulty stopped growing, and a round could leak important data and still get 3 stars.

- Grading (all modes, engine/arena/grade.py): leaks cap the grade whatever the score. Internal leak: at most 2 stars (`capped`); sensitive data, money or a forbidden action: grade `leak` ("Data leaked"), a fail; core: `breach`. Storage maps `leak` to `fail`. The level report and Home explain it. Before, a 25 or 50 point leak out of ~300 points could still reach 85%.
- Rule reader (engine/arena/rules.py): a sentence needs an instruction (never, don't, ignore, refuse...) to count; catch-alls ("never reveal anything") still guard data but also ban every public topic (customers refused); "confidential/sensitive" alone guards nothing. analyze_rules returns `notes` (catch_all, vague, no_directive) shown before the shift and in the report. Before, a 9-word catch-all covered 7 of 9 defenses.
- Endless "Siege" (engine/arena/endless.py, tuning in scenarios/arena/endless.json): empty rules at the start; a word budget that shrinks (22 → 11); intel (full → targets only → partial) and a recon line; attackers weighted 3x toward the defenses missing from the rules used last time; attacks, customers, targets, combined-attack share grow; decision time shrinks (12 s → 4 s); 3 blocks per shift (+1 every 4, max 5); trust (100) replaces "one failed section ends the run": leaks and turned-away customers cost trust, a perfect shift heals 5, the run ends at 0 trust or a breached core. Scoring: grade base × (1 + 0.2 × (shift − 1)) + 10 per unused word + 100 per attack you blocked.
- Shifts are played one visitor at a time (rounds.start_round / step / finish_round; play_round still plays a whole round). Visitors show no role until you decide; Block or Let it through, with a countdown that lets the chatbot answer when it ends. Starting a shift re-seeds the run, so quitting halfway brings different visitors.
- Live AI (engine/arena/live.py): the attacker AI gets a mission briefing per message (target, technique and how to use it, difficulty level 1–6 by shift, the player's current rules to get around) and returns one text per slot; the engine keeps the plan, so intel and difficulty are the same with and without AI. The chatbot prompt states that the owner's rules override the business prompt. The 30 second cooldown is gone. Not tested against real Gemini here (no key).
- Simulation used for tuning (80 seeds, simulated chatbot, perfect blocking): a fixed 19-word "guard everything" rule stops fitting the budget at shift 4; a player who rewrites rules from the intel and recon survives a median of 13 shifts (10–16) with about 57% more points than a lazy fixed-priority player (median 11).
- Run file format 2 adds word_budget, blocks_used, attacks_blocked_by_you, customers_blocked_by_you, trust_after. Saved runs in the browser now hold trust; runs saved by the previous version are not continued.

## Campaign of live shifts (branch james/campaign-shifts)
Feedback: after Siege, the levels and the tutorial still played like the old card shop. Now every level is an authored live shift with the same ideas as Endless, and the card shop is retired from the screens.

- Level design (scenarios/arena/levels.json): every level has `slack` (spare words), `blocks`, `seconds` (countdown), `intel` (full / targets / partial / none), `vip` and a `twist` line. Levels 1-3 have no blocks or countdown and play out by themselves (the earlier playback screen); levels 4-12 are interactive (1 to 3 blocks, countdown 14 s down to 7 s); VIP clients appear in levels 6, 8, 10 and 12; intel thins out from level 9. The tutorial has 20 words of slack, no blocks and full intel; its 10 guide steps were retexted for intel, rules and the shift.
- Engine (engine/arena/campaign.py, new): `new_try` draws an attack package and builds the shift spec; the word budget is the words of the shortest rules that stop that package (`canonical_rules`, `par_words`) plus the level's slack, at least 2 and at most max(par + 2, 16), so a "guard everything" rule only fits packages that really need nearly everything. `start_shift` / `finish_shift` play one visitor at a time with the shared round engine; `play_level` plays it all at once for levels 1-3 and for tests. A VIP is the second customer message; turning them away (blocking or refusing) gives the new grade `vip` (a fail, stored as `fail`). Points = secrets kept + public served + 25 per catch + 3 per unused word, 0 if the shift fails. `objectives` feeds the report checklist.
- UI: ui/shift.py (new) holds the countdown shift view shared by Endless and the levels (state key `lvl_run` for levels, `endless_run` unchanged). ui/play.py is the new level screen (intel, rules box with word counter and rule warnings, Start shift). The report shows words used / budget, blocks, a goal checklist and notes. Home, Levels and Help texts no longer mention cards or compute.
- Not removed on purpose: the card shop code (engine/arena/play.py, rules.shop_for and friends, cards.json) and its tests still exist and pass, but no screen uses them. Delete them in a separate PR if the team agrees.
- Tests: tests/test_arena.py (every level x package solvable within budget, budget cap, level ordering, VIP, blocks, intel, package rotation), tests/test_ui_pure.py (campaign notes, VIP storage), tests/test_app_smoke.py (levels with intel and rules box, perfect round, failed round, new try, budget, interactive levels, countdown, VIP).
- This touches Dong's folders (engine/arena/, scenarios/arena/, tests/). The contract in docs/MASTER_PROMPT.md is unchanged.
