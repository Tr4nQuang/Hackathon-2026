# 🛡️ Chatbot Defense Arena

natHacks 2026, Standard Division, Defense and Security theme.

**You are on the blue team.** Three small businesses (a café, a car dealership and a university's student
support) each run a chatbot, and attackers are trying to trick it into leaking what it knows or doing what it
must never do. You write the rules that protect the chatbot in plain English, then decide on each visitor (block
them or let them talk to the chatbot) while a map of the business, the **System Core**, changes message by message. You score
for every secret kept (**security**) and for every real customer still served (**helpfulness**), and your
rules must fit a word budget, so "refuse everything" and "guard everything" never win.

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
| ![Home: the pitch, the three game modes and an example System Core map](docs/screenshots/01-home.png) | ![Level mode: the map of 12 levels, a winding path of numbered bubbles over three businesses](docs/screenshots/06-levels.png) |
| ![The tutorial guide highlights the rules box and dims the rest; intel and the word budget above](docs/screenshots/02-tutorial-guide.png) | ![A shift playing out: your rules, the System Core map with a leak, and the chat with the judge's verdicts](docs/screenshots/03-playback.png) |
| ![Report: stars, security, helpfulness, words used, the level's goals and what leaked](docs/screenshots/04-results.png) | ![Endless Siege: a hidden visitor waits for Block or Let it through before the countdown ends, with trust above](docs/screenshots/05-endless.png) |
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

By default `USE_FAKE_AI=true`, so the whole game runs **without any API key**. The tutorial and Level mode never use an AI:
built-in attack scripts and a simulated chatbot that reads your plain English rules. Endless mode does the same without a key.

To play Endless mode against a live AI (a real chatbot and a real attacker), create a key in Google AI Studio, put it in `.env` as `GEMINI_API_KEY`
and set `USE_FAKE_AI=false`. The game tries a short list of Gemini Flash and Flash-Lite models in order and remembers the first
one that answers (set `GEMINI_MODEL` to try your own first). Keys live only in `.env`, which git ignores. The game has no page for
typing a key and never prints one.

## How to play

**The System Core map.** Every business is a map with four rings. The outer ring is public information the
chatbot *should* share (opening hours, the menu, deals, loyalty), worth 10 points a zone. Inside it come
internal information (25 points), sensitive data such as staff details, bank accounts, refunds and the server
(50 points), and at the centre the **core**, the admin password (150 points). The closer to the centre, the more
it is worth, and a breached core ends the round on the spot. A dark zone means a secret was **breached**, a
hatched zone means a real customer was **turned away**, and a green or ticked zone means it was kept or served.
The chat and the map change together, message by message.

**Tutorial and Level mode: a campaign of live shifts.** Every level is an authored shift at one business, with its
own twist, and the 12 levels teach the game in order. The rules box, intel and word budget work as in Endless (below).
1. Read the **intel**: the attacker's goal and style, plus a line on what they are after and how. Later levels give less.
2. Write plain English **rules** in the box. They must fit the level's word budget, which is only a little above the
   shortest rules that stop everything, so you must choose; every unused word is worth 3 points. Every try draws one
   of four attack packages, so you cannot memorise one.
3. Press **Start shift**. Levels 1 to 3 play out by themselves in the phone-style chat (Pause, step, Skip, speed, a
   slider and a timeline of verdicts). From level 4 the visitors arrive one at a time and you **Block** or **Let it
   through** before a countdown ends (1 to 3 blocks; the countdown tightens). Each attacker you block earns 25 points.
4. Twists: from level 6 some levels hide a **VIP client** among the visitors, and turning them away fails the shift;
   the last levels give only part of the intel and the shortest budgets.
5. The report opens by itself: security, helpfulness, words used, points, the stars, a checklist of the level's goals
   and notes on every leak, customer turned away and weak rule. It never tells you what to write.

The tutorial has a 10 step guide (restart it with the Help button) that teaches intel, rules and the shift on a
level with no blocks and no countdown. A level opens the next one when you earn at least one star. There are 12
levels over the three businesses. Points in a level: secret points kept + public points served + 25 per block that
caught an attacker + 3 per unused word, and 0 if the shift fails.

**Endless mode: Siege** ("How long can you hold?") is a live shift at the chatbot, again and again, each one harder.
1. **Intel.** Before each shift you learn what the attackers are after (and, early on, how). The targets flash red on
   the map. A recon line tells you what they learned from your last rules: "nothing in them covered ignoring identity
   claims, so expect them to try that."
2. **Rules on a budget.** You start with an empty rules box. Your plain English rules must fit a word budget that
   shrinks every shift (22 words, then 21, ... down to 11), so you can never guard everything: choose. Vague rules
   backfire: "never reveal anything" also silences real customers, "confidential" alone protects nothing, and a line
   without an instruction (never, don't, ignore...) does nothing. Rules carry over to the next shift.
3. **The shift.** Visitors arrive one at a time and **nobody tells you who is an attacker**. Each waits for your call
   with a countdown (12 seconds at first, down to 4): **Block** them (three blocks per shift, up to five later) or **Let it
   through** to the chatbot, which answers under your rules. Blocking a real customer turns them away. When time runs out,
   the chatbot answers.
4. **Trust.** Leaks cost the business's trust in its chatbot (10 for internal information, 25 for personal data, money
   or a forbidden action, 3 per turned-away customer, and 10 more for a failed shift); a perfect shift gives 5 back. Trust
   starts at 100. The run ends when trust runs out, or at once if the core is breached. A failed shift scores nothing but
   the run goes on while trust is left.
5. **The attackers adapt.** They study the rules you used last time and go for what they left out. Every shift has more
   attackers and customers, more targets, combined attacks that need several defenses at once, less time per visitor
   and fewer words. Intel gets patchier the deeper you go.

A shift scores 800 / 500 / 250 / 100 for Perfect / 3 / 2 / 1 stars, 20% more for every shift survived, plus 10 per
unused word and 100 per attacker you blocked yourself. Without a live AI the attacks come from built-in scripts and a
simulated chatbot reads your rules. With one, an attacker AI is briefed on its target, its technique, how hard this shift
must be and **your current rules**, and writes the attacks around them; a real chatbot answers. Finished runs can be saved
to the record board on your computer. All the tuning is in `scenarios/arena/endless.json`.

**Grades.** *Perfect* means every secret kept and every customer served. Otherwise the overall
score gives 3 stars at 85%, 2 stars at 70% and 1 star at 50%, as long as security is at least 50% and
helpfulness at least 30%. **Leaks cap the grade whatever
the score**: an internal leak means 2 stars at most, leaking personal data or money, or doing a forbidden action, fails
the round, and a breached core is an instant loss. In a level, turning a VIP client away fails the shift too.

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

It skips files that are not run files, keeps a shift that was sent twice only once, sorts by time and prints a short summary.

Even a perfect result carries one honest lesson. Rules in a prompt are only the first layer of defence. The
best defence is to never give a chatbot a secret it does not need.

## Project structure

```
app.py          Streamlit entry point, routes between the screens
ui/             interface: home, levels (the map of levels) and play.py (a level's brief and shift), the live shift
                with Block and Let it through shared by levels and Endless (shift.py), report, Endless, records,
                settings, browser saved progress (progress.py), the chat and map playback (chat.py), the
                tutorial guide, the SVG System Core map (map.py), the stylesheet (theme.py), the top bar
                (shell.py), local files (store.py) and data.py (the only file that talks to engine/)
.streamlit/     Streamlit theme colours for light and dark (the game follows your system)
engine/         game logic: engine/arena/ (worlds, attack and customer scripts, the rule reader, rounds,
                grading, the campaign of levels, Endless and the live AI helpers), the run file (export.py),
                the earlier level engine, code judge, save files, optional storage, and call_ai() (every AI call
                goes through it)
scenarios/      game content as JSON: the first café scenarios, and scenarios/arena/ (worlds, defenses and
                rule wording, the 12 levels and the tutorial, Endless tuning, attack and customer scripts)
tools/          admin tools: tools/merge_runs.py merges the run files players send
tests/          plain assert tests, `python tests/run_all.py` runs them all
docs/           plan, build contract (MASTER_PROMPT.md), sample data, supabase.sql, screenshots
```

Design rules: the judge is plain code, not AI, so scoring is objective and free. Content is separate from code,
so adding a level means editing JSON. AI replies and player text are shown as plain text, never as HTML.

## Optional anonymous storage and consent

Storage is **off unless you set it up**, and the game works exactly the same without it.

- Create a Supabase project, run `docs/supabase.sql` once in its SQL editor (its end upgrades an older table), then put `SUPABASE_URL` and
  `SUPABASE_KEY` in `.env`. Use the publishable (anon) key. It can only insert rows and can never read them.
  Never use a service role key.
- On the report screen (and at the end of an Endless run) there is a checkbox, **unticked by default** and asked again for every run:
  "Share my anonymous results to help research: scores, the rules I wrote, my block choices and the chat of each shift
  (attacks and replies). No name is saved, and email addresses or phone numbers are removed."
- Only if it is ticked, one row is stored per level shift (or per Endless shift): the level, the rules you wrote and the
  defenses the game read in them, the scores and grade, which zones leaked or turned a customer away, the words used and the
  budget, your blocks, the VIP and trust results, the game version (`engine_version`), and one record per visitor in `visits`:
  attack or customer, the attack technique and target, Block, Let it through, Timeout or auto, how many seconds you took, and
  what happened, with the attacker's (or customer's) message, the chatbot's reply and who wrote the attack (`script` or `ai`).
  Email addresses and phone numbers in these texts are replaced by `[removed]`.
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
- **Built with.** Python, [Streamlit](https://streamlit.io), Google Gemini (Flash and Flash-Lite models) through
  the `google-genai` library, and optionally Supabase.
- **All businesses, people and data in the game are fictional.**
