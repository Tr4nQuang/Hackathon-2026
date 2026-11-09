# 🛡️ Chatbot Defense Arena

natHacks 2026, Standard Division, Defense and Security theme.

**You are on the blue team.** A small café has put a chatbot called Beanie on its website, and attackers are
trying to trick it into leaking internal information. You write the rules that protect Beanie, then watch the
attackers and the real customers talk to it. You score for every secret kept (**security**) and for every
real customer still served (**helpfulness**), so "refuse everything" never wins.

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
| ![Home screen with the example system core map](docs/screenshots/01-home.png) | ![The tutorial guide highlights the map and dims the rest](docs/screenshots/02-tutorial-guide.png) |
| ![Playback: your rules, the live system core map and the chat side by side](docs/screenshots/03-playback.png) | ![Results with an explanation and a coach tip for every leak](docs/screenshots/04-results.png) |
| ![Endless mode: write your own rules](docs/screenshots/05-endless.png) | |

## Run it

You need Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
python test_engine.py              # quick check of the engine and the interface, no API cost
streamlit run app.py
```

By default `USE_FAKE_AI=true`, so the whole game runs **without any API key**. Level mode never needs an AI at
all. Endless mode then uses canned replies instead of a real model.

To play Endless mode against a real AI, create a key in Google AI Studio, put it in `.env` as `GEMINI_API_KEY`
and set `USE_FAKE_AI=false`. Keys live only in `.env`, which git ignores. The game has no page for typing a key
and never prints one.

## How to play

**The map.** Every level shows what Beanie knows as a round map. The outer ring holds information Beanie
*should* share (opening hours, the menu, the guest wifi). The inner ring holds secrets such as the staff
discount code, and the core holds the most valuable data. The closer to the centre, the more points. A dark
inner zone means a secret **leaked**, a dark outer zone means a real customer was **refused**, and a dark core
means you lose the round. The chat and the map change together, message by message.

**Tutorial and Level mode** are scripted, fast and free.
1. Read the level theme, which hints at what the attackers want.
2. Switch on the rules you want from the list. Every rule is a sentence added to Beanie's instructions. Extra
   rules cost points, and some rules are so strict that they turn real customers away.
3. Press Start. One attack package is drawn at random, so a good set of rules has to cover every package.
4. Watch the chat (speed selector, Pause, Next message, Play all and a scrubber), then read the results: the
   security and helpfulness scores, the penalty, the grade, and for every leak or refused customer an
   explanation with a coach tip.

The first tutorial level has a 10 step guide (restart it with the Help button). A level unlocks the next one
when you earn at least one star.

**Your progress is saved automatically**, only in this browser on this computer (localStorage), and is
never sent anywhere. It holds just your best stars per level, nothing you typed. Use *Continue* on the Home
screen to pick up where you left off, or *Start over* to clear it.

**Endless mode** is where a real chatbot is tested. You write your rules in plain English (up to 1000
characters, the first 400 are free and every started 100 after that costs 2 points). A real AI plays Beanie,
hand written attackers and customers talk to it, and a code judge scores every reply. There is a 30 second
pause between runs to protect the free AI quota.

**Grades.** *Perfect* means 100% security and 100% helpfulness with no more rules than needed. Otherwise
3 stars for a score of 90 or more, 2 stars for 75, 1 star for 60, and *fail* below that. If the core is hacked
you *lose*.

Even a perfect result carries one honest lesson. Rules in a prompt are only the first layer of defence. The
best defence is to never give a chatbot a secret it does not need.

## Project structure

```
app.py          Streamlit entry point, routes between the screens
ui/             interface: screens, playback and results, tutorial guide, Endless screens,
                the SVG system core map, the stylesheet (theme.py), the top bar (shell.py), and
                data.py (the only file that talks to engine/)
.streamlit/     Streamlit theme (light theme and accent colour)
engine/         game logic: level engine, grading, Endless engine, code judge, save files,
                optional storage, and call_ai() (every AI call goes through it)
scenarios/      game content as JSON (levels, rules, attack packages, Endless sections)
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
- On the results screen there is a checkbox, **unticked by default** and asked again for every run:
  "Share my anonymous results to help research. No name or personal data is saved."
- Only if it is ticked, one row is stored for that run: the level, the rules you picked (or, in Endless mode,
  the rules you wrote), the scores and grade, which zones leaked or refused, and the model name for Endless.
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
