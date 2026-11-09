"""Visual theme: one stylesheet for the whole app (a blue team console look, light theme).

Custom blocks are `st.container(key=...)`, which Streamlit exposes as the CSS class `st-key-<key>`. Text inside
them is still shown with st.text and st.markdown, never as HTML.
"""

import streamlit as st

TOKENS = """
:root {
  color-scheme: light;
  --bg: #edf1f4; --surface: #ffffff; --surface-2: #f5f8fa; --ink: #12202b; --muted: #56687a; --line: #d2dbe3;
  --accent: #1a5da8; --accent-ink: #ffffff; --accent-soft: #e0ebf7;
  --good: #1b7653; --good-soft: #dff1e8; --bad: #b4302a; --bad-soft: #fae4e2;
  --warn: #8f5e0e; --warn-soft: #faefd9; --attack: #8a2f4d; --attack-soft: #f7e6ec;
  --t0: #dce9f7; --t1: #afcbee; --t2: #5f93d6; --t3: #1f4f92;
  --breach: #1e252c; --breach-ink: #f2766d; --gold: #b7791f; --shadow: 0 1px 2px rgba(18,32,43,.06), 0 6px 20px rgba(18,32,43,.06);
}
"""

PAGE = """
.stApp { background: var(--bg); color: var(--ink); }
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
textarea { font-family: ui-monospace, Menlo, Consolas, monospace !important; font-size: .9rem; }
"""

SHELL = """
.st-key-topbar { background: var(--surface); border: 1px solid var(--line); border-radius: 14px;
  padding: .55rem 1rem; margin-bottom: 1.1rem; box-shadow: var(--shadow); }
.st-key-topbar [data-testid="stHorizontalBlock"] { align-items: center; }
.st-key-brand p { margin: 0; font-weight: 800; font-size: 1.1rem; letter-spacing: -.01em; }
[class*="st-key-panel"] { background: var(--surface); border: 1px solid var(--line); border-radius: 14px;
  padding: 1.1rem; box-shadow: var(--shadow); min-width: 0; }
.st-key-panel_map { position: sticky; top: .75rem; }
[data-testid="stHorizontalBlock"]:has(.st-key-panel_map) { align-items: stretch; }
.st-key-goal { background: var(--attack-soft); border-radius: 10px; padding: .85rem 1.1rem; }
.st-key-goal p { margin: 0; }
[class*="st-key-eyebrow"] p { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: .75rem; letter-spacing: .08em;
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
[class*="st-key-disc_"] { width: 3.4rem !important; height: 3.4rem !important; flex: none; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 0;
  background: var(--accent); box-shadow: 0 4px 0 rgba(0,0,0,.25); }
[class*="st-key-disc_"] > div { width: auto; }
[class*="st-key-disc_"] p { margin: 0; color: var(--accent-ink); font-weight: 800; font-size: 1.3rem; text-align: center; }
[class*="st-key-disc_done"] { background: var(--good); }
[class*="st-key-disc_perfect"] { background: var(--gold); }
[class*="st-key-disc_locked"] { background: var(--surface-2); border: 2px solid var(--line); box-shadow: none; }
[class*="st-key-disc_locked"] p { color: var(--muted); }
[class*="st-key-disc_next"] { outline: 5px solid var(--accent-soft); }
[class*="st-key-lvl_"] { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: .9rem 1.1rem; }
"""

PLAY = """
[class*="st-key-rcard_"] { background: var(--surface); border: 1px solid var(--line); border-radius: 10px;
  padding: .55rem .8rem; gap: .1rem; transition: border-color .12s ease, background .12s ease; }
[class*="st-key-rcard_"]:hover { border-color: var(--accent); }
[class*="st-key-rcard_"]:has(input:checked) { border-color: var(--accent); background: var(--accent-soft); }
[class*="st-key-rcard_"] label p { font-weight: 700; }
[class*="st-key-rcard_"] [data-testid="stMarkdownContainer"] p { font-size: .85rem; color: var(--muted); }
.st-key-budget { background: var(--surface-2); border-radius: 10px; padding: .6rem .9rem; }
.st-key-tally [data-testid="stMetric"] { text-align: center; padding: .5rem .3rem; background: var(--surface-2); border: 0; }
.st-key-tally [data-testid="stMetricValue"] { font-size: 1.4rem; justify-content: center; }
.st-key-tally [data-testid="stMetricLabel"] { justify-content: center; }
.legend-row p { font-size: .8rem; color: var(--muted); }
.st-key-panel_chat { padding: 0 !important; gap: 0; overflow: hidden; }
.st-key-chat_head { border-bottom: 1px solid var(--line); padding: .7rem 1rem; gap: .1rem; background: var(--surface-2); }
.st-key-chat_head p { font-weight: 800; }
.st-key-chat_body { padding: 1rem; gap: .5rem; min-height: 22rem; }
[class*="st-key-bub_"] { width: fit-content; max-width: 88%; padding: .55rem .85rem; border-radius: 14px; gap: .1rem; }
[class*="st-key-bub_"] [data-testid="stText"], [class*="st-key-bub_"] [data-testid="stText"] * {
  font-family: inherit; font-size: .95rem; white-space: pre-wrap; overflow-wrap: anywhere; }
[class*="st-key-bub_"] [data-testid="stCaptionContainer"] p { font-size: .72rem; margin: 0; letter-spacing: .04em; text-transform: uppercase; }
[class*="st-key-bub_attacker"] { background: var(--attack-soft); border-bottom-left-radius: 4px; }
[class*="st-key-bub_attacker"] [data-testid="stCaptionContainer"] p { color: var(--attack); font-weight: 700; }
[class*="st-key-bub_customer"] { background: var(--accent-soft); border-bottom-left-radius: 4px; }
[class*="st-key-bub_customer"] [data-testid="stCaptionContainer"] p { color: var(--accent); font-weight: 700; }
[class*="st-key-bub_bot"] { background: var(--surface-2); border: 1px solid var(--line); border-bottom-right-radius: 4px; margin-left: auto; }
[class*="st-key-judge_"] { width: fit-content; max-width: 94%; margin-left: auto; padding: .25rem .65rem; border-radius: 6px; }
[class*="st-key-judge_"] * { margin: 0; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: .78rem; font-weight: 600; }
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
[class*="st-key-world_"] { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: .7rem 1rem; margin-top: 1rem; gap: 0; }
[class*="st-key-note_efficiency"] { border-left: 5px solid var(--accent); }
[class*="st-key-note_clean"] { border-left: 5px solid var(--good); }
.st-key-panel_report { gap: .9rem; }
"""

CSS = f"<style>{TOKENS}{PAGE}{SHELL}{HOME}{PLAY}{RESULTS}{ARENA}</style>"


def apply_theme() -> None:
    """Add the stylesheet to the page. It is the same text on every run, so the browser keeps it."""
    st.html(CSS)
