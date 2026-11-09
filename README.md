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
| ![Home: the pitch, the three game modes and an example System Core map](docs/screenshots/01-home.png) | ![Level map: three businesses, twelve levels](docs/screenshots/06-levels.png) |
| ![The tutorial guide highlights one part of the screen and dims the rest](docs/screenshots/02-tutorial-guide.png) | ![Playback: your rules, the System Core map and the chat change together](docs/screenshots/03-playback.png) |
| ![Report: grade, scores and what got through](docs/screenshots/04-results.png) | ![Endless mode: write your rules in plain English](docs/screenshots/05-endless.png) |
| ![Settings: chat speed, progress, AI connection](docs/screenshots/07-settings.png) | |

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
2. Pick rule cards from the **Rule shop**. Each rule costs compute (⚡). Some cards are bundles that cost less
   than the single rules they replace, a few shut a whole topic (which turns real customers away), and some do
   nothing for this round.
3. Press **Run round**. Every try draws one of four script packages and a new shop, so you cannot memorise one.
4. Watch the chat (Pause, step back and forward, Skip to the end, 1x/2x/4x speed, a slider and a timeline of
   verdicts), then read the report: security, helpfulness, compute, the overall score and notes on every leak
   and every customer turned away. It never tells you which of your rules were the unnecessary ones.

The tutorial has a 10 step guide (restart it with the Help button). A level opens the next one when you earn at
least one star. There are 12 levels over the three businesses.

**Endless mode** ("How long can you hold?") is where you write the rules yourself, in plain English (up to 1000
characters). Each section the attacker picks a target and you only get a general hint. Rules carry over between
sections, the business changes every three sections, and the attacks get sharper. One failed section, or a
breached core, ends the run. Sections are worth more the further you go, and short rules earn a bonus (100
minus your word count). Without a live AI the attacks come from built-in scripts and a simulated chatbot reads
your rules; with one, the attacker writes new messages and a real chatbot answers them (a 30 second pause
between runs protects the free AI quota). Finished runs can be saved to the record board on your computer.

**Grades.** *Perfect* means every secret kept, every customer served and no compute wasted. Otherwise the overall
score gives 3 stars at 85%, 2 stars at 70% and 1 star at 50%, as long as security is at least 50% and
helpfulness at least 30%. Every ⚡ that did no work costs 14% of the round's points. A breached core is an
instant loss.

**Save and load.** *Save my game* downloads the round as a file on your computer. *Load my game* replays it.
A loaded game is only replayed: it is never graded again and never stored. *Settings* can also export and
import your level progress, because progress lasts only as long as the browser tab.

Even a perfect result carries one honest lesson. Rules in a prompt are only the first layer of defence. The
best defence is to never give a chatbot a secret it does not need.

## Project structure

```
app.py          Streamlit entry point, routes between the screens
ui/             interface: home, levels, play and replay, report, Endless, records, settings,
                the shared chat and map playback (chat.py), the tutorial guide, the SVG System Core
                map, the stylesheet (theme.py), the top bar (shell.py), local files (store.py) and
                data.py (the only file that talks to engine/)
.streamlit/     Streamlit theme (light theme and accent colour)
engine/         game logic: engine/arena/ (worlds, rule cards, scripts, rounds, grading, Endless and
                the live AI helpers), the earlier level engine, code judge, save files, optional
                storage, and call_ai() (every AI call goes through it)
scenarios/      game content as JSON: the first café scenarios, and scenarios/arena/ (worlds, rule
                cards, levels, attack and customer scripts)
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
- A loaded save is never stored.

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
