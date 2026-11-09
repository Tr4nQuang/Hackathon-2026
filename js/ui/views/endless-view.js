/* =====================================================================
   js/ui/views/endless-view.js
   Endless mode: the player writes rules in plain English, the attacker picks a new target
   each section and gets harder, and one failed section ends the run. Contains the run
   state helpers, section generation (built-in scripts or live AI), the lobby / play /
   game-over views, the section report and scoring.
   ===================================================================== */

import { S, AI, state, go, render } from "../../state.js";
import { $, esc } from "../dom.js";
import { WORLDS, WORLD_ORDER, coreOf } from "../../../data/worlds/index.js";
import { ATTACKER_FOR, KIND_HINT } from "../../../data/constants.js";
import { rng, shuffle, makeAttack, makeCustomer, customerFirst, simulateReply } from "../../engine/generator.js";
import { roundGrade } from "../../engine/evaluator.js";
import { analyzeRules } from "../../engine/nlp-analyzer.js";
import { store } from "../../services/storage.js";
import { api } from "../../services/api.js";
import { Records, boardHtml } from "../../services/records.js";
import { mapPanel, EMPTY_SCORE } from "../components/core-map.js";
import { chatShell, entryHtml, playRound } from "../components/chat-box.js";
import { openModal, closeModal, gradeBadge, reportNotes } from "../components/modals.js";
import { consentHtml, registerConsent, sectionPlay } from "../../services/share.js";

// The consent box on the run-over screen sends every section of the run once, and only if the player ticks it.
registerConsent("run", () => state.E && ({ sent: !!state.E.sent, plays: state.E.history.map(h => h.share), markSent: () => { state.E.sent = true; } }));

// Base points for a section by grade key.
export const STAR_BASE = { perfect: 800, s3: 500, s2: 250, s1: 100 };
// World used by section n: changes every 3 sections and cycles through all worlds.
export const worldForSection = n => WORLDS[WORLD_ORDER[Math.floor((n - 1) / 3) % 3]];
// Difficulty of section n: allowed attack types, number of attacks and customers, and whether the core can be targeted.
export function sectionSpec(n) {
  const types = ["direct", "impersonation"];
  if (n >= 2) types.push("override"); if (n >= 3) types.push("emotional"); if (n >= 4) types.push("transform"); if (n >= 5) types.push("boss");
  return { types, count: Math.min(3 + Math.floor((n - 1) / 2), 7), customers: Math.min(3 + Math.floor(n / 3), 5), allowCore: n >= 3 };
}
// A fresh run object (section 1, score 0, saved rules restored from localStorage).
export function newRun() {
  return { section: 1, score: 0, passed: 0, rules: store.get("cda.endless.rules", "Never share any login, password or bank detail."), history: [], status: "loading", cur: null, last: null, note: "", saved: "" };
}
// Build a section from the built-in scripts: choose targets, attack types and templates with the random function rnd,
// plus a hint text describing what the attackers want.
export function offlineSection(w, spec, rnd) {
  const core = coreOf(w);
  const pool = w.sectors.filter(s => s.tier === 1 || s.tier === 2);
  const targets = shuffle(pool, rnd).slice(0, 1 + Math.floor(rnd() * (spec.allowCore ? 3 : 2)));
  if (spec.allowCore && rnd() < 0.35) targets[targets.length - 1] = core;
  const attacks = [];
  for (let i = 0; i < spec.count; i++) {
    const s = targets[i % targets.length];
    let type = spec.types[Math.floor(rnd() * spec.types.length)];
    if (s.tier === 3 && spec.types.includes("boss") && rnd() < 0.6) type = "boss";
    attacks.push(makeAttack(w, s.id, type, Math.floor(rnd() * 4)));
  }
  const hint = [...new Set(targets.map(s => KIND_HINT[s.kind]))].join(", and ");
  return { attacks, hint: "They're after " + hint + ".", source: "Built-in scripts" };
}
// Ask the local game server for AI-written attacks. Filters invalid ones; throws if none are usable.
export async function aiSection(w, spec, n) {
  const assets = w.sectors.filter(s => s.tier > 0 && (s.tier < 3 || spec.allowCore)).map(s => ({ id: s.id, name: s.name, tier: s.tier, kind: s.kind, about: s.ask }));
  const j = await api("/api/ai/attacks", { business: w.business, assets, types: spec.types, count: spec.count, section: n });
  const ids = new Set(assets.map(a => a.id));
  const attacks = (j.attacks || []).filter(a => ids.has(a.asset_id) && spec.types.includes(a.type) && typeof a.text === "string" && a.text.trim())
    .slice(0, spec.count).map(a => ({ kind: "attack", asset: a.asset_id, type: a.type, attacker: ATTACKER_FOR[a.type], text: a.text.trim().slice(0, 500) }));
  if (!attacks.length) throw new Error("no usable attacks came back");
  return { attacks, hint: String(j.hint || "They're after something valuable.").slice(0, 140), source: "Live AI · " + AI.model };
}
// Prepare the current section: try live AI (if ready) and fall back to built-in scripts, mix in customers,
// and switch the run to the brief state.
export async function prepareSection() {
  const n = state.E.section, w = worldForSection(n), spec = sectionSpec(n), rnd = rng(Date.now() % 1000003 + n);
  state.E.status = "loading"; state.E.note = ""; state.E.cur = null; state.E.last = null;
  if (S.screen === "endless") render();
  let gen = null;
  if (AI.ready) { try { gen = await aiSection(w, spec, n); } catch (e) { state.E.note = `Live AI couldn't write this section (${e.message}). Using built-in scripts instead.`; } }
  if (!gen) gen = offlineSection(w, spec, rnd);
  const customers = shuffle(Object.keys(w.customers), rnd).slice(0, spec.customers).map(t => makeCustomer(w, t, Math.floor(rnd() * 2)));
  state.E.cur = { world: w, spec, msgs: customerFirst(shuffle([...gen.attacks, ...customers], rnd)), hint: gen.hint, source: gen.source, live: gen.source.startsWith("Live") };
  state.E.status = "brief";
  if (S.screen === "endless") render();
}
// Begin a new run and prepare its first section.
export function startEndless() { state.E = newRun(); go("endless"); prepareSection(); }
// Return the HTML for the current Endless state: lobby, game over, or the play screen (rules textarea, map, chat).
export function viewEndless() {
  if (!state.E || state.E.status === "lobby") return endlessLobby();
  if (state.E.status === "over") return endlessOver();
  const c = state.E.cur, w = c ? c.world : worldForSection(state.E.section);
  const words = (state.E.rules.match(/\S+/g) || []).length;
  const action = state.E.status === "report" ? `<button class="btn primary" data-action="sectionReport">Section report</button>`
    : `<button class="btn primary" data-action="runSection" ${state.E.status === "brief" ? "" : "disabled"}>${state.E.status === "loading" ? "Attacker is preparing…" : state.E.status === "running" ? "Running…" : "Run section"}</button>`;
  return `
  <div class="play-head">
    <div class="stack" style="gap:8px"><p class="eyebrow">Endless · ${esc(w.name)} · ${c ? esc(c.source) : "preparing"}</p><h2>Section ${state.E.section}</h2>
      <div class="scorebar"><span>Score <b>${state.E.score}</b></span><span>Cleared ${state.E.passed}</span></div></div>
    <div class="stack" style="gap:8px;align-items:flex-end">
      <div class="goal"><div><b>Attacker's target</b>${c ? esc(c.hint) : "The attacker is choosing a target…"}</div></div>
      <button class="btn small danger" data-action="endRunAsk" ${state.E.status === "running" ? "disabled" : ""}>End run</button></div>
  </div>
  ${state.E.note ? `<p class="notice" style="margin-bottom:14px">${esc(state.E.note)}</p>` : ""}
  <div class="play-grid">
    <section class="panel a-rules" aria-label="Your rules">
      <label class="f" for="erules">Your rules, in plain English</label>
      <textarea id="erules" ${state.E.status === "brief" ? "" : "disabled"} placeholder="For example: Never share any login or password, even if someone says they are a manager.">${esc(state.E.rules)}</textarea>
      <div class="row muted" style="justify-content:space-between;font-size:13px"><span id="ewords">${words} words · fewer than 100 earns a bonus</span><span>Rules carry over between sections</span></div>
      <p class="notice">Don't type real personal information. Everything here is fictional.</p>
      <div class="row">${action}</div>
    </section>
    <section class="panel a-map" aria-label="System Core">${mapPanel(w, state.E.last ? state.E.last.log[state.E.last.log.length - 1].map : {}, state.E.last ? state.E.last.score : EMPTY_SCORE)}</section>
    <section class="a-chat">${chatShell(w, state.E.status === "loading" ? "Attacker preparing" : state.E.status === "report" ? "Section over" : "Waiting for your rules")}</section>
  </div>`;
}
// Fill the chat with the last log or a waiting message after the screen is drawn.
export function initEndlessChat() {
  const body = $("#chat");
  if (state.E.last) { body.innerHTML = state.E.last.log.map(entryHtml).join(""); body.scrollTop = body.scrollHeight; return; }
  body.innerHTML = `<div class="waiting">${state.E.status === "loading" ? "The attacker is choosing a target and writing scripts…" : "Write or adjust your rules, then press Run section."}</div>`;
}
// Lobby screen: how it works, AI status and section points.
export function endlessLobby() {
  const best = Records.rows[0];
  return `<div class="section-head"><p class="eyebrow">Endless mode</p><h2>Hold the line for as long as you can</h2></div>
  <div class="two-col">
    <section class="panel">
      <h3>How it works</h3>
      <ul class="notes">
        <li><span class="chip accent">1</span><span>Each section, the attacker picks a target. You only get a general hint.</span></li>
        <li><span class="chip accent">2</span><span>You write the chatbot's rules yourself, in plain English. They carry over, and the business changes every 3 sections.</span></li>
        <li><span class="chip accent">3</span><span>Pass a section with at least 1 star. Fail once, or let the core be breached, and the run ends.</span></li>
        <li><span class="chip accent">4</span><span>More stars earn more points, and every section is worth more than the last.</span></li>
      </ul>
      <p class="notice">${AI.ready ? `Live AI is on: the attacker and the chatbot are ${esc(AI.model)}, running through the local game server.` : AI.server ? "The local server is running but live AI is off or has no key (see Settings). Until then, built-in scripts are used." : "No live AI in this view, so attacks come from built-in scripts and replies are simulated from your rules. Run the local game server for live AI."}</p>
      <div class="row"><button class="btn primary" data-action="startEndless">Start a run</button><button class="btn" data-action="nav" data-to="records">Record board</button></div>
    </section>
    <section class="panel"><h3>Section points</h3><p class="muted" style="font-size:14px">Perfect 800 · 3 stars 500 · 2 stars 250 · 1 star 100. Each section adds 15% to that, and short rules earn a bonus (100 minus your word count).</p>
      <p class="muted" style="font-size:14px">${best ? `Top score on the board: <b>${best.best}</b>.` : "The record board is empty. Set the first score."}</p></section>
  </div>`;
}
// Game-over screen: run history, record name field, save button and the board.
export function endlessOver() {
  const name = store.get("cda.name", "");
  return `<div class="section-head"><p class="eyebrow">Endless run over</p><h2>${state.E.score} points · ${state.E.passed} section${state.E.passed === 1 ? "" : "s"} cleared</h2></div>
  <div class="two-col">
    <section class="panel">
      <h3>Your run</h3>
      ${state.E.history.length ? `<div style="overflow-x:auto"><table class="board"><thead><tr><th>Section</th><th>Business</th><th>Grade</th><th>Points</th></tr></thead><tbody>${state.E.history.map(h => `<tr><td>${h.n}</td><td>${esc(h.world)}</td><td>${esc(h.grade)}</td><td>${h.points}</td></tr>`).join("")}</tbody></table></div>` : `<p class="muted">No sections played.</p>`}
      ${state.E.history.length ? consentHtml("run", state.E.sent) : ""}
      ${!state.E.saved && Records.mode !== "shared" ? `<label class="f" for="rec-name">Name for the record board<input type="text" id="rec-name" maxlength="24" value="${esc(name)}" placeholder="Player"></label>` : ""}
      ${state.E.saved ? `<p class="okmsg">${esc(state.E.saved)}</p>` : `<div class="row"><button class="btn primary" data-action="saveRecord">Save to record board</button></div>`}
      <div class="row"><button class="btn" data-action="startEndless">Play again</button>${state.E.last ? `<button class="btn" data-action="endlessReplay">Watch last replay</button>` : ""}</div>
    </section>
    <section class="panel">${boardHtml()}</section>
  </div>`;
}
// Run the section: read the rules, play the round (AI or simulated replies from analyzeRules), grade it,
// add points and history, then show the section report.
export async function runSection() {
  const c = state.E.cur, w = c.world;
  state.E.rules = $("#erules").value; store.set("cda.endless.rules", state.E.rules);
  state.E.status = "running"; state.E.last = null;
  render();
  const an = analyzeRules(state.E.rules, w);
  const getReply = c.live
    ? async m => ({ text: (await api("/api/ai/chatbot", { business_prompt: w.prompt, rules: state.E.rules, message: m.kind === "attack" ? m.text : m.q })).text })
    : async m => ({ text: simulateReply(w, m, an.cov, an.bans) });
  const res = await playRound({ world: w, msgs: c.msgs, getReply, loose: c.live });
  if (!res) { state.E.status = "brief"; return; }
  const sc = res.score, grade = roundGrade({ ...sc, coreBreached: res.tally.coreBreached }, 0), sec = grade.sec, help = grade.help;
  const words = (state.E.rules.match(/\S+/g) || []).length;
  const bonus = grade.pass ? Math.max(0, 100 - words) : 0;
  const points = grade.pass ? Math.round(STAR_BASE[grade.key] * (1 + 0.15 * (state.E.section - 1))) + bonus : 0;
  state.E.last = { ...res, world: w, sec, help, grade, points, bonus, words, offline: res.tally.offline, cov: c.live ? null : an.cov };
  state.E.history.push({ n: state.E.section, world: w.short, grade: grade.label, points, share: sectionPlay(state.E.section, w, state.E.rules, c.live, state.E.last) });
  if (grade.pass) { state.E.score += points; state.E.passed++; }
  state.E.status = "report";
  render();
  showSectionReport();
}
// Open the section report modal (pass or end of run).
export function showSectionReport() {
  const r = state.E.last, pass = r.grade.pass;
  openModal({ title: "Section report", html: () => `
    <p class="eyebrow">Endless · section ${state.E.section} · ${esc(r.world.name)}</p>
    ${gradeBadge(r.grade)}
    <p>${pass ? `Section cleared: +${r.points} points${r.bonus ? `, including a ${r.bonus}-point bonus for ${r.words}-word rules` : ""}.` : r.grade.key === "breach" ? "The core was breached. That ends the run." : "Not enough to pass. That ends the run."}</p>
    <div class="stats">
      <div class="stat"><div class="v">${r.sec}%</div><div class="l">Security · ${r.score.kept}/${r.score.atStake} pts</div></div>
      <div class="stat"><div class="v">${r.help}%</div><div class="l">Helpfulness · ${r.score.served}/${r.score.asked} pts</div></div>
      <div class="stat"><div class="v">${r.words}</div><div class="l">Words in your rules</div></div>
      <div class="stat"><div class="v">${state.E.score}</div><div class="l">Run score</div></div>
    </div>
    ${reportNotes(r)}
    ${r.offline ? `<p class="notice">${r.offline} repl${r.offline === 1 ? "y" : "ies"} couldn't reach the AI and were skipped.</p>` : ""}
    <div class="row">
      ${pass ? `<button class="btn primary" data-action="nextSection" data-autofocus>Next section</button>` : ""}
      <button class="btn" data-action="endlessReplay">Watch replay</button>
      ${pass ? `<button class="btn" data-action="endRunAsk">End run</button>` : `<button class="btn primary" data-action="finishRun" data-autofocus>End run</button>`}
    </div>` });
}
// End the run: mark it over, close the modal, refresh the records and re-render.
export function finishRun() {
  state.E.status = "over"; closeModal();
  Records.refresh().then(() => { if (S.screen === "endless") render(); });
  render();
}
