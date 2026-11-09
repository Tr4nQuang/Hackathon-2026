/* =====================================================================
   js/ui/views/play-view.js
   Play screen shared by the tutorial and the 12 levels: rule shop, System Core map and
   chat side by side. Also starts a try (new script package and shop) and runs a round,
   grades it and saves the result.
   ===================================================================== */

import { S, state, go, render } from "../../state.js";
import { $, esc } from "../dom.js";
import { LEVELS, TUTORIAL, TUT_STEPS } from "../../../data/levels.js";
import { WORLDS } from "../../../data/worlds/index.js";
import { getCard, cardsCoverage, cardsBans } from "../../../data/cards.js";
import { buildRound, shopFor, simulateReply } from "../../engine/generator.js";
import { efficiencyLabel, minCostFor, roundGrade } from "../../engine/evaluator.js";
import { mapPanel, EMPTY_SCORE } from "../components/core-map.js";
import { chatShell, entryHtml, playRound } from "../components/chat-box.js";
import { showReport } from "../components/modals.js";
import { saveProgress } from "../../services/storage.js";
import { levelPlay } from "../../services/share.js";

// The level being played: the tutorial or LEVELS[S.levelIdx].
export const currentLevel = () => S.mode === "tutorial" ? TUTORIAL : LEVELS[S.levelIdx];
// Pick a random script package index, never the same one twice in a row for the same level key.
export function pickPackage(key, count) {
  if (count <= 1) return 0;
  let p = Math.floor(Math.random() * count);
  if (p === S.lastPkg[key]) p = (p + 1 + Math.floor(Math.random() * (count - 1))) % count;
  S.lastPkg[key] = p;
  return p;
}
/* Every try draws a new package of scripts and builds a new shop for it. */
// Start a new try: merge extra into S, draw a package, build the round messages and the shop, reset
// the selection and open the play screen.
export function beginTry(extra = {}) {
  Object.assign(S, extra);
  const L = currentLevel();
  S.pkg = pickPackage(L.tutorial ? "tutorial" : S.levelIdx, L.packs.length);
  S.msgs = buildRound(L, S.pkg); S.shop = shopFor(L, S.pkg, S.msgs);
  S.selected = []; S.running = false; S.last = null;
  go("play");
}
// Return the HTML of the play screen. Before a round it shows the rule shop and a Run button;
// after a round it shows the chosen rules, compute used and retry / report buttons.
// In the tutorial it also shows the coach box for the current step.
export function viewPlay() {
  const L = currentLevel(), w = WORLDS[L.world], done = !!S.last;
  const title = L.tutorial ? "Tutorial" : `Level ${S.levelIdx + 1} · ${L.title}`;
  const usedNow = ids => ids.reduce((a, id) => a + getCard(id, w).cost, 0);
  let tut = "";
  if (L.tutorial) {
    const k = Math.min(S.tutStep, TUT_STEPS.length - 1), st = TUT_STEPS[k];
    tut = `<div class="coach" style="margin-bottom:16px"><div class="av">C</div><div><b class="k">Step ${k + 1} of 5 · ${esc(st.title)}</b>${esc(st.body)}
      ${k < 2 ? `<div class="row" style="margin-top:8px"><button class="btn small primary" data-action="tutNext">Next</button></div>` : ""}</div></div>`;
  }
  let rules;
  if (!done) {
    const cards = S.shop.map(id => { const c = getCard(id, w);
      return `<button class="rcard ${S.selected.includes(id) ? "on" : ""}" data-action="toggleCard" data-id="${id}" aria-pressed="${S.selected.includes(id)}" ${S.running ? "disabled" : ""}>
      <span class="box"></span><span><span class="lbl">${esc(c.label)}</span><br><span class="txt">${esc(typeof c.text === "function" ? c.text(w) : c.text)}</span></span><span class="cost">${c.cost}⚡</span></button>`; }).join("");
    const used = usedNow(S.selected);
    rules = `<div class="row" style="justify-content:space-between"><h3>Rule shop</h3><span class="chip">${S.shop.length} rules</span></div>
      <p class="muted" style="font-size:13px">Each rule costs compute (⚡). Rules that do no work lower your grade, and you won't be told which ones afterwards.</p>
      <div class="rcards">${cards}</div>
      <div class="budget"><span>Compute used</span><span class="big">${used}<span class="bolt">⚡</span></span><span class="muted">${S.selected.length} rule${S.selected.length === 1 ? "" : "s"} chosen</span></div>
      <div class="row"><button class="btn primary" data-action="runLevel" ${S.running ? "disabled" : ""}>${S.running ? "Round running…" : "Run round"}</button></div>`;
  } else {
    rules = `<h3>Your rules this round</h3>
      <ul class="notes">${S.last.sel.length ? S.last.sel.map(id => `<li><span class="chip">${getCard(id, w).cost}⚡</span><span>${esc(getCard(id, w).label)}</span></li>`).join("") : `<li><span class="chip">0⚡</span><span>No rules chosen</span></li>`}</ul>
      <div class="budget"><span>Compute used</span><span class="big">${S.last.used}<span class="bolt">⚡</span></span><span class="muted">${esc(efficiencyLabel(S.last.excess))}</span></div>
      <div class="row"><button class="btn primary" data-action="retryLevel">Try again with new scripts</button><button class="btn" data-action="showReport">Report</button></div>
      ${L.tutorial ? `<button class="btn" data-action="nav" data-to="levels">Go to Level mode</button>` : `<button class="btn" data-action="nav" data-to="levels">Level map</button>`}`;
  }
  return `
  <div class="play-head">
    <div class="stack" style="gap:8px"><p class="eyebrow">${esc(w.name)} · ${L.tutorial ? "1 script package" : `1 of ${L.packs.length} script packages, drawn at random`}</p><h2>${esc(title)}</h2></div>
    <div class="goal"><div><b>Attacker's goal</b>${esc(L.goal)}</div><div><b>Their style</b>${esc(L.style)}</div></div>
  </div>
  ${tut}
  <div class="play-grid">
    <section class="panel a-rules" aria-label="Your rules">${rules}</section>
    <section class="panel a-map" aria-label="System Core">${mapPanel(w, done ? S.last.log[S.last.log.length - 1].map : {}, done ? S.last.score : EMPTY_SCORE)}</section>
    <section class="a-chat">${chatShell(w, done ? "Round over" : "Waiting for your rules")}</section>
  </div>`;
}
// After the screen is drawn, fill the chat with the last round log or the waiting message.
export function initPlayChat() {
  const body = $("#chat");
  if (S.last) { body.innerHTML = S.last.log.map(entryHtml).join(""); body.scrollTop = body.scrollHeight; }
  else body.innerHTML = `<div class="waiting">Choose your rules, then press Run round. Visitors and attackers show up here, one chat at a time.</div>`;
}
// Run the selected rules through the round: play it, grade it against the cheapest possible rule set
// (par), save progress, then re-render and show the report.
export async function runLevel() {
  const L = currentLevel(), w = WORLDS[L.world], msgs = S.msgs, sel = [...S.selected];
  const cov = cardsCoverage(sel, w), bans = cardsBans(sel, w);
  S.running = true; if (L.tutorial) S.tutStep = 3;
  render();
  const res = await playRound({ world: w, msgs, getReply: async m => ({ text: simulateReply(w, m, cov, bans) }) });
  if (!res) { S.running = false; return; }
  const used = sel.reduce((a, id) => a + getCard(id, w).cost, 0), sc = res.score;
  const par = minCostFor(w, msgs, S.shop, { kept: sc.kept, served: sc.served, coreBreached: res.tally.coreBreached });
  const excess = Math.max(0, used - par);
  const grade = roundGrade({ ...sc, coreBreached: res.tally.coreBreached }, excess);
  const sec = grade.sec, help = grade.help;
  const points = grade.pass ? Math.max(0, sc.kept + sc.served - grade.penalty) : 0;
  S.running = false;
  S.last = { ...res, msgs, sel, cov, used, excess, sec, help, grade, points, pkg: S.pkg, world: w };
  S.last.share = levelPlay(L, S.levelIdx, S.last);
  if (L.tutorial) { S.tutStep = 4; if (grade.pass) { state.progress.tutorial = true; saveProgress(); } }
  else {
    const p = state.progress[S.levelIdx] || { stars: 0, best: 0, perfect: false };
    state.progress[S.levelIdx] = { stars: Math.max(p.stars, grade.pass ? grade.stars : 0), best: Math.max(p.best, points), perfect: p.perfect || grade.key === "perfect" };
    saveProgress();
  }
  render();
  showReport(L);
}
