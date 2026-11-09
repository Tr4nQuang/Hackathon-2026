# Chatbot Defense Arena

natHacks 2026, Standard Division, Defense and Security theme.

Try it at https://chatbot-defense-arena.streamlit.app

In this game you protect a small business's chatbot. People keep messaging it. Some are customers asking about
opening hours or the menu, and some are attackers trying to get it to leak the staff schedule, the bank account or
the admin password. You write the chatbot's rules and decide who gets through. If a secret leaks you lose points,
but if you turn a real customer away you lose points too, so you can't just tell the bot to refuse everything.

## Why we made this

A lot of small businesses are putting AI chatbots on their websites now, and those chatbots usually know more than
they should. The way people attack them is called prompt injection. You write a message that tricks the bot into
ignoring its instructions. OWASP lists it as the top risk for apps built on large language models, and it has
already caused real problems. A Chevrolet dealership's chatbot agreed to sell someone a car for one dollar, and Air
Canada had to honour a refund policy its chatbot made up.

Big companies have security teams for this. A café or a small dealership doesn't. We wanted something the person
who actually runs the chatbot could play in a few minutes and come away understanding what can go wrong.

## What's in it

| | |
|---|---|
| ![Home screen](docs/screenshots/01-home.png) | ![Level map](docs/screenshots/06-levels.png) |
| ![Tutorial guide](docs/screenshots/02-tutorial-guide.png) | ![A shift in progress](docs/screenshots/03-playback.png) |
| ![Report after a shift](docs/screenshots/04-results.png) | ![Endless mode](docs/screenshots/05-endless.png) |

There are three made up businesses, a café, a car dealership and a university help desk. Each one is drawn as a map
with four rings. Public stuff like the menu sits on the outside and is worth 10 points. Internal information is worth
25, things like staff records, refunds and the bank account are worth 50, and the admin password in the middle is
worth 150. When something leaks its zone goes dark, and if the middle one goes you lose the round straight away.

The tutorial walks you through everything in 10 steps. After that there are 12 levels. You read some intel about what
the attackers want, write rules in plain English within a word limit, and watch the chat play out. From level 4 you
also have to decide on each visitor yourself, either blocking them or letting them talk to the bot, before a timer
runs out. You don't get told who is an attacker.

Endless mode keeps going until you run out of trust. Every shift you get fewer words, less time and better attackers,
and the attackers read the rules you used last time and go after whatever you left out. If you add a Gemini key, the
attacks are written by one AI and the chatbot is another AI that actually follows your rules. Without a key it still
works using our own scripts.

After every shift there's a report showing what leaked, who got turned away and why, plus a replay you can scrub
through.

## How we built it

It's Python with Streamlit. A few decisions we spent time on.

**The scoring is done by code, not by an AI.** We check each reply for the actual secret text. If we had used an AI to
judge, the judge could be tricked by the same messages the chatbot is being tricked by, and it would cost money every
round.

**Only Endless mode uses live AI.** The tutorial and the levels are scripted, so they're fast, free, and every player
gets the same fair round. Endless is where you want the attacks to be different every time, so that's where the AI goes.

**We don't train any model.** Every AI in the game is a single call to Gemini with instructions for its role. We say
this up front because it's easy to oversell.

**It keeps working when Gemini doesn't.** During the hackathon one Gemini model stopped working for new keys and
another was overloaded for a while. Now the game tries a few models in order, remembers the one that works, and falls
back to scripts if none answer.

**Keys stay on the server.** There's no page where you type a key, and the database key we use can add rows but can't
read them back.

All the game content (businesses, secrets, levels, attack scripts, difficulty settings) lives in JSON files under
`scenarios/`, so adding a level doesn't need any code. There are 16 test files with around 590 checks, and none of them
need an API key or internet.

## How it's different

Most games about this, like Gandalf by Lakera, have you play the attacker. Tensor Trust lets players attack and defend
each other, and tools like Promptfoo are for developers. We put you on defence and made being helpful count as much as
being safe, because that's the actual tradeoff a business has to make. We haven't seen another game that does it this
way, but we're not claiming to be the first.

## What we learned

The most surprising thing came from our own play data. When we first hooked up Gemini, Endless mode turned out to be
way too easy. We had 20 shifts in a row cleared with the same eight word rule that was already sitting in the box, and
not one failed. Gemini just refuses obvious attacks by itself. That told us two things. The game needed to be harder
(so the rules box now starts empty, the word limit shrinks every shift, and the attacker writes around your rules),
and the real risk isn't a careful assistant leaking a password when asked. It's chatbots that are set up to please
customers, and actions like refunds and discounts.

## What the data is for

If a player ticks the consent box, we save one row per shift in Supabase. It's off by default and asked again every
time. We save the rules they wrote, what leaked, what they blocked, and the messages and replies. No names, and email
addresses and phone numbers are stripped out.

Players can also keep their own copy. When an Endless run ends, *Download run file (Excel)* gives a workbook with a
sheet for the run, one for each shift, one for every visitor and a guide to the columns. Nothing is sent unless the
player chooses to send the file, and an admin can merge many of them with
`python tools/merge_runs.py folder_with_the_files -o all_endless_runs.xlsx`.

We collect it for four reasons.

1. **Tuning the game.** This already paid off. It's how we found out Endless was too easy.
2. **Seeing what actually works.** Over time it becomes a set of real attacks next to real defences written by
   non-experts, so we can see which kinds of rules hold up and which phrasings slip past them.
3. **Checking whether people learn.** If security and helpfulness go up over someone's tries, the game is teaching
   something. If they don't, we need to change it.
4. **Building a better attacker later.** The same data could be used to train an attacker that learns which tricks
   beat which defences.

Right now the dataset is small since it's only us and a few testers. It's the setup that matters at this stage.

## What doesn't work yet

The levels are scripted, so they teach the idea of each defence but don't prove a rule would stop a real AI. Endless
is where that gets tested. The record board resets when the hosted app restarts. Scores are calculated in the game, so
someone determined could cheat. And live AI is limited by Gemini's free tier.

## Where it could go

The part we're most interested in is pointing the same engine at a real business's chatbot. It would send the
attacks and the customer questions, score the replies the same way, and give the owner a report of what leaked and
which customers got refused. That could become a cheap testing service for small businesses.

Before that we'd want to run a proper playtest with local small business staff and student workers, use the data to
check whether people actually improve, move the record board into Supabase, and add more businesses. The biggest
constraints are AI costs and rate limits, privacy, and the fact that Streamlit is good for a prototype but a real
product would need a proper web app.

## Running it yourself

You need Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
python test_engine.py              # runs every test, no API cost
streamlit run app.py
```

It runs without any key because `USE_FAKE_AI=true` is the default. For live AI in Endless mode, get a key from Google
AI Studio, put it in `.env` as `GEMINI_API_KEY` and set `USE_FAKE_AI=false`. To save play data, run
`docs/supabase.sql` once in a Supabase project and add `SUPABASE_URL` and `SUPABASE_KEY` (the publishable key).

## Scoring, in short

Perfect means nothing leaked and nobody was turned away. Otherwise you get 3 stars at 85%, 2 at 70% and 1 at 50%, as
long as security is at least 50% and helpfulness at least 30%. Some leaks cap your grade no matter the score. Internal
information means 2 stars at most, personal data, money or a forbidden action means you fail, and losing the core is
an instant loss. All the Endless numbers are in `scenarios/arena/endless.json`.

## Project layout

```
app.py          Streamlit entry point
ui/             screens, the map, chat playback, tutorial guide, styling
engine/         game logic, the code judge, live AI helpers, storage, call_ai()
scenarios/      all game content as JSON
tools/          admin tools, like merging downloaded run files
tests/          plain assert tests (python tests/run_all.py)
docs/           plan, build contract, supabase.sql, screenshots
```

## Credits

Made by four first year students at the University of Alberta during natHacks 2026, November 6 to 9.

### The problem

- [OWASP Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/),
  where prompt injection is listed first. The [2023 list as a PDF](https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-2023-v1_1.pdf).
- The Chevrolet chatbot that agreed to sell a 2024 Tahoe for one dollar, reported by
  [GM Authority](https://www.gmauthority.com/blog/2023/12/gm-dealer-chat-bot-agrees-to-sell-2024-chevy-tahoe-for-1/)
  and logged in the [AI Incident Database](https://incidentdatabase.ai/entities/chevrolet-of-watsonville).
- Moffatt v. Air Canada, 2024 BCCRT 149, where a BC tribunal held the airline responsible for what its chatbot said.
  The [tribunal decision](https://decisions.civilresolutionbc.ca/crt/crtd/en/525448/1/document.do) and a
  [plain summary from Manatt](https://manatt.com/insights/newsletters/advertising-law/ai-gone-wild-airline-has-to-honor-a-refund-policy).

### Related work

- [Gandalf by Lakera](https://gandalf.lakera.ai), a game where you trick an AI into giving up a password.
  Lakera is now part of Check Point, see the [Check Point announcement](https://www.checkpoint.com/press-releases/check-point-acquires-lakera/).
- [CrowdStrike AI Unlocked](https://www.crowdstrike.com/en-us/blog/introducing-ai-unlocked-interactive-prompt-injection-challenge/),
  an interactive prompt injection challenge.
- [Tensor Trust](https://tensortrust.ai), a game where players attack and defend each other, and its
  [research paper](https://arxiv.org/abs/2311.01011).
- [Promptfoo](https://www.promptfoo.dev), open source testing and red teaming for LLM apps.
- [WitnessAI](https://witness.ai), AI security for companies.

### Built with

- [Python](https://www.python.org) and [Streamlit](https://streamlit.io)
- [Google Gemini API](https://ai.google.dev)
- [Supabase](https://supabase.com)

Everything in the game, businesses, people and data, is fictional.
