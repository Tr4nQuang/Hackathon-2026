# 🛡️ Chatbot Defense Arena

natHacks 2026, Standard Division, Defense and Security theme.

**You are on the blue team.** Three small businesses (a café, a car dealership and a university's student
support) each run a chatbot, and attackers are trying to trick it into leaking what it knows or doing what it
must never do. You choose or write the rules that protect the chatbot, then watch the attackers and the real
customers talk to it while a map of the business, the **System Core**, changes message by message. You score
for every secret kept (**security**) and for every real customer still served (**helpfulness**), and every rule
costs compute, so "refuse everything" and "switch on everything" never win.

## Why this matters

- More and more small businesses add an AI chatbot to their website. The chatbot often knows internal things
  such as staff discount codes, customer data or pricing rules.
- Attackers use **prompt injection**, which means tricking the chatbot with carefully worded messages, to pull
  that information out. Prompt injection is ranked as the number one risk in the OWASP Top 10 for Large
  Language Model Applications.
- It has already cost real money and trust. A Chevrolet dealership chatbot in the US was tricked into agreeing
  to sell a car for one dollar, and a Canadian tribunal held Air Canada responsible for wrong information its
  chatbot gave a customer.
- Large companies can buy protection. Small businesses usually have no security team and no affordable tool
  made for them. This game teaches owners and staff how the attacks work, and its engine can later test a real
  chatbot the same way.

## Screenshots

| | |
|---|---|
| ![Home: the pitch, the three game modes and an example System Core map](docs/screenshots/01-home.png) | ![Level map: a winding path of numbered bubbles, stars earned below each](docs/screenshots/06-levels.png) |
| ![The tutorial guide highlights one part of the screen and dims the rest](docs/screenshots/02-tutorial-guide.png) | ![Playback: your rules, the System Core map and the chat change together](docs/screenshots/03-playback.png) |
| ![Report: grade, scores and what got through](docs/screenshots/04-results.png) | ![Endless mode: write your rules in plain English](docs/screenshots/05-endless.png) |
| ![Settings: chat speed and progress](docs/screenshots/07-settings.png) | |

The look follows your system: light or dark, with the same colours as the original browser demo. The page loads its
fonts (Archivo, Atkinson Hyperlegible, IBM Plex Mono) from Google Fonts and falls back to system fonts offline.

## Run it

You need Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
python test_engine.py              # runs every test (engine and interface), no API cost
streamlit run app.py
```

By default `USE_FAKE_AI=true`, so the whole game runs **without any API key**. Level mode never needs an AI at
all. Endless mode then uses built-in attack scripts, and a simulated chatbot reads your plain English rules.

To play Endless mode against a live AI (a real chatbot and a real attacker), create a key in Google AI Studio, put it in `.env` as `GEMINI_API_KEY`
and set `USE_FAKE_AI=false`. Keys live only in `.env`, which git ignores. The game has no page for typing a key
and never prints one.

## How to play

**The System Core map.** Every business is a map with four rings. The outer ring is public information the
chatbot *should* share (opening hours, the menu, deals, loyalty), worth 10 points a zone. Inside it come
internal information (25 points), sensitive data such as staff details, bank accounts, refunds and the server
(50 points), and at the centre the **core**, the admin password (150 points). The closer to the centre, the more
it is worth, and a breached core ends the round on the spot. A dark zone means a secret was **breached**, a
hatched zone means a real customer was **turned away**, and a green or ticked zone means it was kept or served.
The chat and the map change together, message by message.

**Tutorial and Level mode** are scripted, fast and free.
1. Read the attacker's goal and style (the hint at what they will try).
2. Tick rule cards in the **Rule shop**. Each rule costs compute (⚡). Some cards are bundles that cost less
   than the single rules they replace, a few shut a whole topic (which turns real customers away), and some do
   nothing for this round.
3. Press **Run round**. Every try draws one of four script packages and a new shop, so you cannot memorise one.
4. Watch the chat in its phone-style window (Pause, step back and forward, Skip to the end, 1x/2x/4x speed, a
   slider and a timeline of verdicts). When the last message is in, the report opens by itself: security, helpfulness, compute, the overall score and notes on every leak
   and every customer turned away. It never tells you which of your rules were the unnecessary ones.

The tutorial has a 10 step guide (restart it with the Help button). A level opens the next one when you earn at
least one star. There are 12 levels over the three businesses.

**Endless mode: Siege** ("How long can you hold?") is a live shift at the chatbot, again and again, each one harder.
1. **Intel.** Before each shift you learn what the attackers are after (and, early on, how). The targets flash red on
   the map. A recon line tells you what they learned from your last rules: "nothing in them covered ignoring identity
   claims, so expect them to try that."
2. **Rules on a budget.** You start with an empty rules box. Your plain English rules must fit a word budget that
   shrinks every shift (22 words, then 21, ... down to 11), so you can never guard everything: choose. Vague rules
   backfire: "never reveal anything" also silences real customers, "confidential" alone protects nothing, and a line
   without an instruction (never, don't, ignore...) does nothing. Rules carry over to the next shift.
3. **The shift.** Visitors arrive one at a time and **nobody tells you who is an attacker**. Each waits for your call
   with a countdown: **Block** them (three blocks per shift, more later) or **Let it through** to the chatbot, which
   answers under your rules. Blocking a real customer turns them away. When time runs out, the chatbot answers.
4. **Trust.** Leaks cost the business's trust in its chatbot (10 for internal information, 25 for personal data, money
   or a forbidden action, 3 per turned-away customer); a perfect shift gives 5 back. The run ends when trust runs out,
   or at once if the core is breached.
5. **The attackers adapt.** They study the rules you used last time and go for what they left out. Every shift has more
   attackers and customers, more targets, combined attacks that need several defenses at once, less time per visitor
   and fewer words. Intel gets patchier the deeper you go.

A shift scores 800 / 500 / 250 / 100 for Perfect / 3 / 2 / 1 stars, 20% more for every shift survived, plus 10 per
unused word and 100 per attacker you blocked yourself. Without a live AI the attacks come from built-in scripts and a
simulated chatbot reads your rules. With one, an attacker AI is briefed on its target, its technique, how hard this shift
must be and **your current rules**, and writes the attacks around them; a real chatbot answers. Finished runs can be saved
to the record board on your computer. All the tuning is in `scenarios/arena/endless.json`.

**Grades.** *Perfect* means every secret kept, every customer served and no compute wasted. Otherwise the overall
score gives 3 stars at 85%, 2 stars at 70% and 1 star at 50%, as long as security is at least 50% and
helpfulness at least 30%. Every ⚡ that did no work costs 14% of the round's points. **Leaks cap the grade whatever
the score**: an internal leak means 2 stars at most, leaking personal data or money, or doing a forbidden action, fails
the round, and a breached core is an instant loss.

**Progress and continuing later.** Level stars, best scores and your best points for each Endless shift are saved
automatically, only in this browser on this computer, and never sent anywhere. An Endless run in progress is kept too
(its shift, score, trust, the rules you wrote and one line of results per shift), so you can close the game and come back:
press *Continue your Endless run* on the Home screen or in the Endless lobby. It starts at the next shift with your
rules and score. A run that ended is kept as "last run" so you can still see its result and download its file. The saved
run is replaced when you finish a shift of a new run, and *Start over* on Home (it asks once) clears everything. Leaving in the middle of a shift brings a fresh one
(different visitors) when you come back. The chat of earlier shifts is not kept, so there is no replay of them after closing.

**Sending your Endless run to the admin.** When a run is over, *Download run file (CSV)* gives one file with one line per
shift: when it was played, the business, the grade and points, security and helpfulness, how many words and characters
your rules had and the budget, **the rules you wrote**, which zones leaked or turned a customer away, how many visitors you
blocked, the trust left, and whether live AI was used. It has
no name, and anything that looks like an email address or phone number in your rules is replaced by `[removed]`. The file is
a CSV (UTF-8) so the admin can open it in Excel or Google Sheets. Nothing is sent by the game: you choose whether to send the
file (for example by email). The admin puts many files together with:

```bash
python tools/merge_runs.py folder_with_the_files -o all_endless_runs.csv
```

It skips files that are not run files, keeps a section that was sent twice once, sorts by time and prints a short summary.

Even a perfect result carries one honest lesson. Rules in a prompt are only the first layer of defence. The
best defence is to never give a chatbot a secret it does not need.

## Project structure

```
app.py          Streamlit entry point, routes between the screens
ui/             interface: home, levels, play and replay, report, Endless, records, settings, browser
                saved progress (progress.py),
                the shared chat and map playback (chat.py), the tutorial guide, the SVG System Core
                map, the stylesheet (theme.py), the top bar (shell.py), local files (store.py) and
                data.py (the only file that talks to engine/)
.streamlit/     Streamlit theme (light theme and accent colour)
engine/         game logic: engine/arena/ (worlds, rule cards, scripts, rounds, grading, Endless and
                the live AI helpers), the earlier level engine, code judge, save files, optional
                storage, and call_ai() (every AI call goes through it)
scenarios/      game content as JSON: the first café scenarios, and scenarios/arena/ (worlds, rule
                cards, levels, attack and customer scripts)
tools/          admin tools: tools/merge_runs.py merges the run files players send
tests/          plain assert tests, `python tests/run_all.py` runs them all
docs/           plan, build contract (MASTER_PROMPT.md), sample data, supabase.sql, screenshots
```

Design rules: the judge is plain code, not AI, so scoring is objective and free. Content is separate from code,
so adding a level means editing JSON. AI replies and player text are shown as plain text, never as HTML.

## Optional anonymous storage and consent

Storage is **off unless you set it up**, and the game works exactly the same without it.

- Create a Supabase project, run `docs/supabase.sql` once in its SQL editor, then put `SUPABASE_URL` and
  `SUPABASE_KEY` in `.env`. Use the publishable (anon) key. It can only insert rows and can never read them.
  Never use a service role key.
- On the report screen (and at the end of an Endless run) there is a checkbox, **unticked by default** and asked again for every run:
  "Share my anonymous results to help research. No name or personal data is saved."
- Only if it is ticked, one row is stored for that run: the level, the rules you picked (or, in Endless mode,
  the rules you wrote, one row per section), the scores and grade, which zones leaked or refused, and the model name for Endless.
  No name, nickname or email is stored. The engine skips saving when written rules look like an email address
  or a phone number. A short notice under every rule box asks players not to type real personal information.

## Credits and sources

- **Team.** Built during natHacks 2026 (November 6 to 9) at the University of Alberta. Engine and content:
  Dong. Interface, README and docs: James.
- **The problem.** OWASP Top 10 for Large Language Model Applications (prompt injection ranked first). The
  Chevrolet dealership one dollar chatbot and the Air Canada chatbot tribunal case are widely reported public
  incidents.
- **Related work, and how this differs.** Gandalf by Lakera and CrowdStrike AI Unlocked let players *attack* an
  AI. Here players *defend*, and helpfulness is measured with fake customers who ask real questions. Tensor
  Trust (a UC Berkeley research game) has players write defences and attack each other. Promptfoo is open
  source automated red teaming from the command line, and Lakera (now part of Check Point) and WitnessAI sell
  enterprise AI security. This project is made for people who cannot code and for small businesses. We have
  not found another product that combines these pieces this way, and we do not claim to be the first.
- **Built with.** Python, [Streamlit](https://streamlit.io), Google Gemini (`gemini-2.5-flash-lite`) through
  the `google-genai` library, and optionally Supabase.
- **All businesses, people and data in the game are fictional.**
