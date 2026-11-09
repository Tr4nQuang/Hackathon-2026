"""Visual theme: one stylesheet for the whole app (a blue team console look, light or dark like the player's system).

Custom blocks are `st.container(key=...)`, which Streamlit exposes as the CSS class `st-key-<key>`. Text inside
them is still shown with st.text and st.markdown, never as HTML.
"""

import streamlit as st

FONTS = ("@import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800"
         "&family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap');")

TOKENS = """
:root {
  color-scheme: light;
  --bg: #edf1f4; --surface: #ffffff; --surface-2: #f5f8fa; --ink: #12202b; --muted: #56687a; --line: #d2dbe3;
  --accent: #1a5da8; --accent-ink: #ffffff; --accent-soft: #e0ebf7; --bean: #6a4529; --bean-soft: #f4ece5;
  --good: #1b7653; --good-soft: #dff1e8; --bad: #b4302a; --bad-soft: #fae4e2;
  --warn: #8f5e0e; --warn-soft: #faefd9; --attack: #8a2f4d; --attack-soft: #f7e6ec;
  --t0: #dce9f7; --t1: #afcbee; --t2: #5f93d6; --t3: #1f4f92; --t2-ink: #ffffff; --t3-ink: #ffffff;
  --breach: #1e252c; --breach-ink: #f2766d; --gold: #b7791f; --shadow: 0 1px 2px rgba(18,32,43,.06), 0 6px 20px rgba(18,32,43,.06);
  --f-display: "Archivo", "Helvetica Neue", Arial, sans-serif;
  --f-body: "Atkinson Hyperlegible", system-ui, -apple-system, "Segoe UI", sans-serif;
  --f-mono: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --bg: #0d161d; --surface: #14212b; --surface-2: #192833; --ink: #e4ecf2; --muted: #93a6b5; --line: #26394a;
    --accent: #6ea6ec; --accent-ink: #08131c; --accent-soft: #1a3049; --bean: #d2a47e; --bean-soft: #2a2119;
    --good: #52c59a; --good-soft: #123329; --bad: #f2766d; --bad-soft: #3a1a19;
    --warn: #e5b252; --warn-soft: #352812; --attack: #ee8fae; --attack-soft: #381c27;
    --t0: #1b2f45; --t1: #244a72; --t2: #3570b5; --t3: #8cbbf2; --t2-ink: #e4ecf2; --t3-ink: #08131c;
    --breach: #040709; --breach-ink: #f2766d; --gold: #e5b252; --shadow: 0 1px 2px rgba(0,0,0,.3), 0 6px 20px rgba(0,0,0,.25);
  }
}
"""

PAGE = """
.stApp { background: var(--bg); color: var(--ink); font-family: var(--f-body); }
.stApp button, .stApp input, .stApp textarea, .stApp select { font-family: inherit; }
.stApp h1, .stApp h2, .stApp h3 { font-family: var(--f-display); font-stretch: 112%; }
.stApp [data-testid="stSidebar"] { display: none; }
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], footer { display: none !important; }
[data-testid="stMainBlockContainer"] { max-width: 1280px; padding: 1rem 1.25rem 4rem; }
.stApp h1, .stApp h2, .stApp h3 { font-weight: 800; letter-spacing: -.01em; color: var(--ink); }
.stApp p, .stApp label, .stApp li { color: var(--ink); }
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p { color: var(--muted); }
.stButton > button, .stDownloadButton > button {
  border-radius: 999px; border: 1px solid var(--line); background: var(--surface); color: var(--ink);
  font-weight: 700; padding: .45rem 1.1rem; transition: background .12s ease, transform .12s ease; }
.stButton > button:hover, .stDownloadButton > button:hover { background: var(--surface-2); border-color: var(--accent); color: var(--ink); }
.stButton > button:active { transform: translateY(1px); }
.stButton > button[kind="primary"] { background: var(--accent); color: var(--accent-ink); border-color: var(--accent); }
.stButton > button[kind="primary"]:hover { filter: brightness(1.08); color: var(--accent-ink); }
.stButton > button[kind="tertiary"] { border: 0; background: transparent; color: var(--muted); }
.stButton > button[kind="tertiary"]:hover { background: var(--surface-2); color: var(--ink); }
.stButton > button p, .stDownloadButton > button p { color: inherit; }
.stButton > button:disabled { opacity: .5; }
[data-testid="stHeaderActionElements"] { display: none; }
/* Streamlit offsets the 1rem paragraph margin with a negative margin on its containers. Inside our own blocks
   both go, otherwise the next element slides up over the text. */
[class*="st-key-"] [data-testid="stMarkdownContainer"] p, [class*="st-key-"] [data-testid="stCaptionContainer"] p { margin: 0; }
[class*="st-key-"] [data-testid="stMarkdownContainer"], [class*="st-key-"] [data-testid="stCaptionContainer"] { margin-bottom: 0; }
[data-testid="stMetric"] { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: .75rem .9rem; }
[data-testid="stMetricLabel"] p { color: var(--muted); font-size: .8rem; }
[data-testid="stMetricValue"] { font-weight: 800; font-variant-numeric: tabular-nums; }
[data-testid="stAlert"] { border-radius: 10px; }
textarea { font-family: var(--f-mono) !important; font-size: .9rem; }
"""

SHELL = """
.st-key-topbar { background: var(--surface); border: 1px solid var(--line); border-radius: 14px;
  padding: .55rem 1rem; margin-bottom: 1.1rem; box-shadow: var(--shadow); }
.st-key-topbar [data-testid="stHorizontalBlock"] { align-items: center; }
.st-key-brand p { margin: 0; }
[class*="st-key-panel"] { background: var(--surface); border: 1px solid var(--line); border-radius: 14px;
  padding: 1.1rem; box-shadow: var(--shadow); min-width: 0; }
.st-key-panel_map { position: sticky; top: .75rem; }
[data-testid="stHorizontalBlock"]:has(.st-key-panel_map) { align-items: stretch; }
.st-key-goal { background: var(--attack-soft); border-radius: 10px; padding: .7rem 1rem; gap: .5rem; }
.st-key-goal p { margin: 0; }
[class*="st-key-goalk_"] p { font-family: var(--f-mono); font-size: .7rem; letter-spacing: .06em; text-transform: uppercase; font-weight: 600; color: var(--attack) !important; }
[class*="st-key-eyebrow"] p { font-family: var(--f-mono); font-size: .75rem; letter-spacing: .08em;
  text-transform: uppercase; color: var(--muted) !important; margin: 0; }
"""

HOME = """
.st-key-hero h1 { font-size: clamp(2rem, 4.4vw, 3.2rem); line-height: 1.08; margin: .3rem 0 .8rem; }
.st-key-hero h1 strong { color: var(--accent); font-weight: 800; }
[class*="st-key-lede"] p { font-size: 1.1rem; color: var(--muted); max-width: 58ch; }
[class*="st-key-mode_"] { background: var(--surface); border: 1px solid var(--line); border-radius: 14px;
  padding: 1.1rem; transition: border-color .15s ease, transform .15s ease; height: 100%; }
[class*="st-key-mode_"]:hover { border-color: var(--accent); transform: translateY(-2px); }
[class*="st-key-gtile_"] { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: .75rem .9rem; min-height: 7.5rem; }
[class*="st-key-gtile_"] p { font-size: .85rem; color: var(--muted); margin: 0; }
[class*="st-key-gtile_"] strong { color: var(--ink); font-size: 1rem; }
.st-key-levelhead { max-width: 560px; margin: 0 auto; width: 100%; }
.st-key-levelpath { position: relative; max-width: 560px; margin: 0 auto; width: 100%; gap: 0; }
.st-key-pathsvg { position: absolute; top: 0; left: 0; width: 100%; z-index: 0; pointer-events: none; }
[class*="st-key-worldrow_"] { height: 104px !important; flex: none; justify-content: center; position: relative; z-index: 1; }
[class*="st-key-worldrow_"] [class*="st-key-world_"] { margin: 0; }
[class*="st-key-lvlrow_"] { height: 122px !important; flex: none; position: relative; z-index: 1; }
[class*="st-key-lvl_"] { position: absolute; top: 8px; width: 130px; transform: translateX(-50%); align-items: center; gap: 4px; }
[class*="st-key-lvl_"] > div { width: auto; }
[class*="st-key-disc_"] button { width: 64px; height: 64px; min-height: 0; padding: 0; border-radius: 50%; border: 0; background: var(--accent);
  box-shadow: 0 4px 0 color-mix(in srgb, var(--accent) 60%, black); transition: transform .12s ease; justify-content: center; }
[class*="st-key-disc_"] button p { margin: 0; color: var(--accent-ink); font-size: 1.5rem; font-weight: 800; line-height: 1; }
[class*="st-key-disc_"] button:hover:not(:disabled) { transform: translateY(-2px); background: var(--accent); }
[class*="st-key-disc_done"] button { background: var(--good); box-shadow: 0 4px 0 color-mix(in srgb, var(--good) 60%, black); }
[class*="st-key-disc_done"] button:hover:not(:disabled) { background: var(--good); }
[class*="st-key-disc_perfect"] button { background: var(--gold); box-shadow: 0 4px 0 color-mix(in srgb, var(--gold) 60%, black); }
[class*="st-key-disc_perfect"] button:hover:not(:disabled) { background: var(--gold); }
[class*="st-key-disc_locked"] button { background: var(--surface-2) !important; border: 2px solid var(--line); box-shadow: none; opacity: 1; cursor: default; }
[class*="st-key-disc_locked"] button p { color: var(--muted); font-size: 1.2rem; }
[class*="st-key-disc_next"] button { outline: 5px solid var(--accent-soft); animation: pulse 1.6s ease-in-out infinite; }
@keyframes pulse { 50% { outline-color: transparent; } }
@media (prefers-reduced-motion: reduce) { [class*="st-key-disc_next"] button { animation: none; } }
.stApp [class*="st-key-lvlstars_"] [data-testid="stCaptionContainer"] p { color: var(--gold); font-size: .95rem; letter-spacing: .1em; margin: 0; text-align: center; }
[class*="st-key-lvltitle_"] { background: var(--bg); border-radius: 4px; padding: 0 4px; }
[class*="st-key-lvltitle_"] p { font-size: .82rem; line-height: 1.2; text-align: center; margin: 0; }
"""

PLAY = """
[class*="st-key-rcard_"] { background: var(--surface); border: 1px solid var(--line); border-radius: 10px;
  padding: .6rem .8rem; gap: 0; transition: border-color .12s ease, background .12s ease; }
[class*="st-key-rcard_"]:hover { border-color: var(--accent); }
[class*="st-key-rcard_"]:has(input:checked) { border-color: var(--accent); background: var(--accent-soft); }
[class*="st-key-rcard_"] label p { font-weight: 700; font-size: .95rem; text-align: left; padding-left: 0 !important; }
[class*="st-key-rcard_"] [data-testid="stHorizontalBlock"] { align-items: center; gap: .5rem; }
[class*="st-key-rcard_"] [data-testid="stCaptionContainer"] p { font-family: var(--f-mono); font-weight: 600; font-size: .85rem; color: var(--gold) !important; text-align: right; white-space: nowrap; }
[class*="st-key-rcard_"] [data-testid="stMarkdownContainer"] p { font-size: .85rem; color: var(--muted); line-height: 1.4; padding-left: 1.5rem; }
.st-key-budget { background: var(--surface-2); border-radius: 10px; padding: .6rem .9rem; }
.st-key-tally [data-testid="stMetric"] { text-align: center; padding: .5rem .3rem; background: var(--surface-2); border: 0; }
.st-key-tally [data-testid="stMetricValue"] { font-size: 1.4rem; justify-content: center; }
.st-key-tally [data-testid="stMetricLabel"] { justify-content: center; }
.legend-row p { font-size: .8rem; color: var(--muted); }
/* The chat looks like a phone: a bezel, a speaker slot and a status bar on top, a home bar below, a fixed height. */
.st-key-panel_chat { padding: 0 !important; gap: 0; overflow: hidden; border-radius: 34px; border: 6px solid color-mix(in srgb, var(--ink) 18%, var(--surface));
  background: var(--surface); flex: none !important; height: 44rem !important; min-height: 44rem; max-height: 88vh; box-shadow: var(--shadow); }
.st-key-panel_chat::before { content: ""; display: block; flex: none; height: 1.5rem; background: linear-gradient(var(--line), var(--line)) center / 4.2rem .32rem no-repeat, var(--bean-soft); }
.st-key-panel_chat::after { content: ""; display: block; flex: none; height: 1.4rem; background: linear-gradient(var(--line), var(--line)) center / 6.5rem .3rem no-repeat, var(--surface); }
.st-key-chat_head { border-bottom: 1px solid var(--line); padding: .35rem 1rem .75rem; background: var(--bean-soft); flex: none; }
.cda-head { display: flex; align-items: center; gap: .7rem; min-width: 0; }
.cda-logo { width: 2.1rem; height: 2.1rem; border-radius: 8px; background: var(--bean); display: grid; place-items: center; flex: none; }
.cda-logo svg { width: 1.2rem; height: 1.2rem; display: block; }
.cda-ic { stroke-linecap: round; stroke-linejoin: round; }
.cda-ic-cup, .cda-ic-car, .cda-ic-cap { fill: none; stroke: var(--surface); stroke-width: 1.9; }
.cda-ic-shield { fill: var(--accent); } .cda-ic-bolt { fill: var(--gold); }
.cda-headtext { display: flex; flex-direction: column; gap: .1rem; line-height: 1.25; min-width: 0; }
.cda-headtext b { font-family: var(--f-display); font-stretch: 108%; font-size: 1rem; color: var(--ink); }
.cda-sub { font-size: .8rem; color: var(--muted); display: flex; align-items: center; gap: .4rem; }
.cda-dot { width: .45rem; height: .45rem; border-radius: 50%; background: var(--good); display: inline-block; flex: none; }
.cda-brand { display: flex; align-items: center; gap: .6rem; }
.cda-brand svg { width: 1.6rem; height: 1.6rem; display: block; }
.cda-brand b { font-family: var(--f-display); font-stretch: 118%; font-weight: 800; font-size: 1.05rem; letter-spacing: -.01em; color: var(--ink); }
.cda-cost { display: flex; align-items: center; justify-content: flex-end; gap: .2rem; font-family: var(--f-mono); font-weight: 600; font-size: .85rem; color: var(--gold); }
.cda-cost svg { width: .9rem; height: .9rem; display: block; }
.st-key-panel_chat > div:has(> .st-key-chat_body) { flex: 1 1 0 !important; min-height: 0; display: flex; flex-direction: column; }
.st-key-panel_chat > div:has(> .st-key-chat_head) { flex: none; }
.st-key-chat_body { padding: 1rem; gap: .55rem; flex: 1 1 0; min-height: 0; overflow-y: auto; overscroll-behavior: contain; scrollbar-gutter: stable; }
.st-key-chat_body > * { flex: none; }
[class*="st-key-msg_"] { max-width: 88%; width: fit-content; gap: .15rem; }
[class*="st-key-msg_attacker"], [class*="st-key-msg_customer"] { align-self: flex-start; align-items: flex-start; }
[class*="st-key-msg_bot"] { align-self: flex-end; align-items: flex-end; margin-left: auto; }
[class*="st-key-msg_"] [data-testid="stCaptionContainer"] p { font-size: .75rem; color: var(--muted); }
[class*="st-key-msg_attacker"] [data-testid="stCaptionContainer"] p { color: var(--attack); font-weight: 700; }
[class*="st-key-bub_"] { width: fit-content; max-width: 100%; padding: .55rem .85rem; border-radius: 16px; gap: .1rem; }
[class*="st-key-bub_"] [data-testid="stText"], [class*="st-key-bub_"] [data-testid="stText"] * {
  font-family: inherit; font-size: .95rem; white-space: pre-wrap; overflow-wrap: anywhere; }
[class*="st-key-bub_attacker"] { background: var(--attack-soft); border-bottom-left-radius: 4px; }
[class*="st-key-bub_customer"] { background: var(--accent-soft); border-bottom-left-radius: 4px; }
[class*="st-key-bub_bot"] { background: var(--surface-2); border: 1px solid var(--line); border-bottom-right-radius: 4px; }
[class*="st-key-judge_"] { width: fit-content; max-width: 94%; margin-left: auto; padding: .25rem .65rem; border-radius: 6px; }
[class*="st-key-judge_"] * { margin: 0; font-family: var(--f-mono); font-size: .78rem; font-weight: 600; }
[class*="st-key-judge_good"] { background: var(--good-soft); } [class*="st-key-judge_good"] * { color: var(--good); }
[class*="st-key-judge_bad"] { background: var(--bad-soft); } [class*="st-key-judge_bad"] * { color: var(--bad); }
[class*="st-key-judge_warn"] { background: var(--warn-soft); } [class*="st-key-judge_warn"] * { color: var(--warn); }
[class*="st-key-sep_"] p { text-align: center; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: .72rem; color: var(--muted); margin: .4rem 0 0; }
"""

RESULTS = """
[class*="st-key-grade_"] { border-radius: 14px; padding: .9rem 1.2rem; border: 1px solid var(--line); background: var(--surface); }
[class*="st-key-grade_"] p { margin: 0; font-size: 2rem; font-weight: 800; letter-spacing: -.01em; line-height: 1.1; }
[class*="st-key-grade_perfect"] p { color: var(--gold); }
[class*="st-key-grade_pass"] p { color: var(--good); }
[class*="st-key-grade_fail"] { background: var(--bad-soft); border-color: transparent; }
[class*="st-key-grade_fail"] p { color: var(--bad); }
[class*="st-key-note_"] { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: .7rem 1rem; gap: .2rem; }
[class*="st-key-note_leak"] { border-left: 5px solid var(--bad); }
[class*="st-key-note_refusal"] { border-left: 5px solid var(--warn); }
"""

ARENA = """
.st-key-ai_tag p { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: .7rem; letter-spacing: .06em; text-transform: uppercase;
  border: 1px solid var(--line); border-radius: 999px; padding: 2px 9px; width: fit-content; color: var(--muted) !important; white-space: nowrap; }
[class*="st-key-chatrow_"] { gap: .1rem; }
[class*="st-key-sys_"] * { text-align: center; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: .72rem; color: var(--muted); margin: 0; }
[class*="st-key-sys_new"] { border-top: 1px solid var(--line); margin-top: .5rem; padding-top: .25rem; }
[class*="st-key-sys_alarm"] { background: var(--bad); border-radius: 6px; padding: .35rem .8rem; }
[class*="st-key-sys_alarm"] * { color: #ffffff; font-weight: 700; letter-spacing: .06em; }
.st-key-bub_bot_typing { opacity: .7; }
.st-key-guide_box { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: .8rem 1rem; margin-bottom: 1rem; box-shadow: var(--shadow); }
.st-key-coach_avatar { width: 2.2rem !important; height: 2.2rem !important; flex: none; border-radius: 50%; background: var(--accent);
  display: flex; flex-direction: column; align-items: center; justify-content: center; }
.st-key-coach_avatar p { color: var(--accent-ink) !important; font-weight: 800; margin: 0; }
[class*="st-key-world_"] { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: .6rem 1rem; margin-top: 1rem; gap: 0; }
[class*="st-key-note_efficiency"] { border-left: 5px solid var(--accent); }
[class*="st-key-note_clean"] { border-left: 5px solid var(--good); }
.st-key-panel_report { gap: .9rem; }
"""

CSS = f"<style>{FONTS}{TOKENS}{PAGE}{SHELL}{HOME}{PLAY}{RESULTS}{ARENA}</style>"


def apply_theme() -> None:
    """Add the stylesheet to the page. It is the same text on every run, so the browser keeps it."""
    st.html(CSS)
