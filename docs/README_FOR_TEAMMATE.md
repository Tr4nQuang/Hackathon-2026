# Chatbot Defense Arena: handoff for the frontend teammate

Project: natHacks 2026, Standard Division, theme Defense and Security. Submission is due Monday Nov 9, 2026 at 11 AM MDT.
Game: the player defends a fictional café chatbot (Beanie) from prompt injection, scored on security and helpfulness, shown on a round "system core map".

## Split of work
- Dong (backend): engine/, scenarios/, tests/ (phases 0 to 5, 9, 10, 12A, 13A, then optional 14, 16, 18 in docs/MASTER_PROMPT.md)
- Teammate (frontend): app.py, ui/, README.md, docs/ (phases 6, 7, 8, 11, 12B, 13B, then optional 15 and 17)
- The contract between both sides is section 4 of docs/MASTER_PROMPT.md. Do not change function names or return shapes without writing it in docs/PROGRESS.md under Decisions.

## Files in this package
- MASTER_PROMPT.md: the build instructions Claude Code follows (authoritative).
- PLAN.md: the full plan (also available as Chatbot_Defense_Arena_Plan.docx).
- guide_steps.json: the 10 tutorial guide steps.
- sample_results.json: example engine outputs so the frontend can be built before the engine exists (use through ui/data.py).
- supabase.sql: table for optional anonymous play storage (run once in the Supabase SQL editor).

## How to run
1. Put the files above into docs/ in the shared GitHub repo.
2. Open the repo folder in Claude Code and paste one line:
   Read docs/MASTER_PROMPT.md and follow it. ROLE=B     (Dong uses ROLE=A)
3. After each phase finishes, run /clear and paste the same line again. Progress is tracked in docs/PROGRESS.md.
4. Run git pull often so you get the engine as soon as Dong pushes it.

## Rules
- Never put API keys in code or chat. Keys live only in a local .env file, which is git ignored.
- USE_FAKE_AI=true is the default, so the whole app runs without any key.
- Show AI replies with st.text, never as HTML.

## About the earlier browser demo
The teammate's demo is a design reference only. Do not commit its HTML or server files. Section 7 of MASTER_PROMPT.md lists the ideas we adopted from it.

Game content is pre-written in docs/cafe.json (4 levels, 2 Endless sections). Check it with: python docs/check_cafe_design.py docs/cafe.json
