/* =====================================================================
   js/ui/components/modals.js
   Modal dialog manager plus the round report and the replay player.
   Modal content is described as { title, html(), after?, wide? } and stored in state.modal.
   Note: showReport needs the current level, so the caller passes it in (this avoids
   importing play-view.js and creating a circular dependency).
   ===================================================================== */

import { S, state } from "../../state.js";
import { $, esc, svgIcon, starsHtml, WORLD_ICON } from "../dom.js";
import { sectorOf } from "../../../data/worlds/index.js";
import { LEVELS } from "../../../data/levels.js";
import { TYPE_LABEL, DEFENSE_LABEL } from "../../../data/constants.js";
import { missingFor } from "../../engine/generator.js";
import { efficiencyLabel } from "../../engine/evaluator.js";
import { mapSvg, tallyHtml } from "./core-map.js";
import { entryHtml } from "./chat-box.js";
import { consentHtml, registerConsent } from "../../services/share.js";

// The consent box of a level report sends this round once, and only if the player ticks it.
registerConsent("level", () => S.last && ({ sent: !!S.last.sent, plays: [S.last.share], markSent: () => { S.last.sent = true; } }));
// Stop the replay timer if one is running.
export function stopReplay() { if (state.replayTimer) { clearInterval(state.replayTimer); state.replayTimer = null; } }
// Draw state.modal into #modal-root (or clear it), run its after() hook and focus the first control.
export function renderModal() {
  const root = $("#modal-root");
  if (!state.modal) { root.innerHTML = ""; return; }
  root.innerHTML = `<div class="modal-back" data-action="modalBack"><div class="modal ${state.modal.wide ? "wide" : ""}" role="dialog" aria-modal="true" aria-label="${esc(state.modal.title)}">${state.modal.html()}</div></div>`;
  if (state.modal.after) state.modal.after();
  (root.querySelector("[data-autofocus]") || root.querySelector("button"))?.focus();
}
// Open a modal (stops any running replay first).
export function openModal(m) { stopReplay(); state.modal = m; renderModal(); }
// Close the modal (stops any running replay first).
export function closeModal() { stopReplay(); state.modal = null; renderModal(); }
// True while the Endless section report is shown: it cannot be dismissed by clicking outside.
export const modalLocked = () => S.screen === "endless" && state.E && state.E.status === "report";

// Grade label with stars (stars only when the round passed).
export function gradeBadge(g) {
  return `<div class="grade-badge ${g.key === "perfect" ? "perfect" : g.pass ? "" : g.key}"><span class="big">${esc(g.label)}</span>${g.pass ? starsHtml(g.stars) : ""}</div>`;
}
/* Notes say what got through and who was turned away. They never say which rules were unnecessary. */
// List of notes for the report: which attacks got through and what was missing, who was turned away,
// efficiency feedback, or a "clean" note.
export function reportNotes(r) {
  const w = r.world, notes = [];
  r.tally.leaks.forEach(({ m, leaked }) => {
    const miss = r.cov ? missingFor(w, m, r.cov) : [], act = sectorOf(w, m.asset).kind === "action";
    notes.push(`<li><span class="chip bad">${act ? "Action" : "Leak"}</span><span><b>${esc(m.attacker)}</b> ${act ? "got the bot to do" : "got"} <b>${esc(leaked.map(id => sectorOf(w, id).name.toLowerCase()).join(" and "))}</b> with ${esc(TYPE_LABEL[m.type].toLowerCase())}.${miss.length ? ` Nothing in your rules covered ${esc(miss.map(k => DEFENSE_LABEL[k]).join(", "))}.` : ""}</span></li>`);
  });
  r.tally.refused.forEach(m => notes.push(`<li><span class="chip warn">Turned away</span><span>A customer asking about <b>${esc(sectorOf(w, m.topic).name.toLowerCase())}</b> got no answer.</span></li>`));
  if (r.excess > 0) notes.push(`<li><span class="chip">Efficiency</span><span>${r.excess >= 5 ? "Far more compute than this job needed." : "Some compute did no work."} It cost you ${r.grade.penalty} points. Think about which of your rules this attack team really needed.</span></li>`);
  if (!notes.length) notes.push(`<li><span class="chip good">Clean</span><span>No leaks, no turned-away customers${r.excess === 0 ? ", and no wasted compute" : ""}.</span></li>`);
  return `<ul class="notes">${notes.join("")}</ul>`;
}
// Open the round report for the last result (S.last) of level L: grade, stats, notes and action buttons.
export function showReport(L) {
  const r = S.last; if (!r) return;
  const isLast = !L.tutorial && S.levelIdx === LEVELS.length - 1;
  openModal({ title: "Round report", html: () => `
    <p class="eyebrow">${L.tutorial ? "Tutorial" : `Level ${S.levelIdx + 1} · ${esc(L.title)}`} · script package ${"ABCD"[r.pkg]}</p>
    ${gradeBadge(r.grade)}
    <p>${r.grade.key === "breach" ? "The core was breached, so the round ended on the spot. Protect the centre first." : r.grade.pass ? (isLast ? "Final level cleared. All three businesses are defended." : "Level passed.") : (r.sec >= 50 && r.help >= 30) ? "Failed on compute: too many rules that did no work." : "Not enough to pass. Check the notes and the replay, then try again."}</p>
    <div class="stats">
      <div class="stat"><div class="v">${r.sec}%</div><div class="l">Security · ${r.score.kept}/${r.score.atStake} pts kept</div></div>
      <div class="stat"><div class="v">${r.help}%</div><div class="l">Helpfulness · ${r.score.served}/${r.score.asked} pts</div></div>
      <div class="stat"><div class="v">${r.used}⚡</div><div class="l">Compute · ${esc(efficiencyLabel(r.excess))}</div></div>
      <div class="stat"><div class="v">${r.grade.overall}%</div><div class="l">Overall · ${r.points} points</div></div>
    </div>
    ${reportNotes(r)}
    ${consentHtml("level", r.sent)}
    <div class="row">
      <button class="btn primary" data-action="openReplay" data-autofocus>Watch replay</button>
      <button class="btn" data-action="retryLevel">Try again</button>
      ${L.tutorial ? `<button class="btn" data-action="nav" data-to="levels">Go to Level mode</button>` : r.grade.pass && !isLast ? `<button class="btn" data-action="startLevel" data-i="${S.levelIdx + 1}">Next level</button>` : ""}
      ${!L.tutorial ? `<button class="btn" data-action="nav" data-to="levels">Level map</button>` : ""}
      <button class="btn" data-action="closeModal">Close</button>
    </div>` });
}
// Open the replay player for result r: map and chat redraw to any step, with play / pause, step buttons,
// scrubber, speed selector and a timeline of verdict ticks.
export function openReplay(r) {
  let i = 0;
  const log = r.log, w = r.world;
  const marks = log.map((e, k) => e.type === "judge" ? `<i style="left:${(100 * k / Math.max(1, log.length - 1)).toFixed(2)}%;background:var(--${e.cls})"></i>` : "").join("");
  // Draw step i: map and tally on the left, chat history up to step i on the right.
  const draw = () => {
    $("#rp-map").innerHTML = mapSvg(w, log[i].map) + tallyHtml(log[i].score);
    const body = $("#rp-chat"); body.innerHTML = log.slice(0, i + 1).map(entryHtml).join(""); body.scrollTop = body.scrollHeight;
    $("#rp-range").value = i; $("#rp-pos").textContent = `${i + 1}/${log.length}`;
  };
  // Stop automatic playback and reset the button label.
  const halt = () => { stopReplay(); const b = $("#rp-play"); if (b) b.textContent = "Play"; };
  // Toggle automatic playback (restarts from the beginning if it is at the end).
  const play = () => {
    if (state.replayTimer) { halt(); return; }
    if (i >= log.length - 1) i = 0;
    $("#rp-play").textContent = "Pause";
    state.replayTimer = setInterval(() => { if (i >= log.length - 1) { halt(); return; } i++; draw(); }, 900 / Number($("#rp-speed").value));
  };
  openModal({ title: "Round replay", wide: true, html: () => `
    <div class="row" style="justify-content:space-between"><div><p class="eyebrow">Replay · ${esc(w.name)}</p><h2 style="font-size:24px">Watch the core change, message by message</h2></div><button class="btn small" data-action="closeReplay">Back to report</button></div>
    <div class="replay-grid">
      <div class="mapbox" id="rp-map"></div>
      <div class="chat"><div class="chat-head"><div class="logo">${svgIcon(WORLD_ICON[w.id])}</div><div><b>${esc(w.bot)}</b><div class="status">Recorded conversation</div></div></div><div class="chat-body" id="rp-chat"></div></div>
    </div>
    <div>
      <div class="player">
        <button class="btn small primary" id="rp-play" data-autofocus>Play</button>
        <button class="btn small" id="rp-prev" aria-label="Previous step">◀</button>
        <button class="btn small" id="rp-next" aria-label="Next step">▶</button>
        <input type="range" id="rp-range" min="0" max="${log.length - 1}" value="0" aria-label="Replay position">
        <span class="mono" id="rp-pos" style="font-size:13px"></span>
        <select id="rp-speed" aria-label="Replay speed"><option value="1">1×</option><option value="2" selected>2×</option><option value="4">4×</option></select>
      </div>
      <div class="timeline" aria-hidden="true">${marks}</div>
      <p class="muted" style="font-size:13px;margin-top:6px">Timeline ticks: red for leaks, amber for refused customers, green for blocked attacks and answered questions.</p>
    </div>`,
    after: () => {
      draw();
      $("#rp-play").onclick = play;
      $("#rp-prev").onclick = () => { halt(); i = Math.max(0, i - 1); draw(); };
      $("#rp-next").onclick = () => { halt(); i = Math.min(log.length - 1, i + 1); draw(); };
      $("#rp-range").oninput = e => { halt(); i = Number(e.target.value); draw(); };
      $("#rp-speed").onchange = () => { if (state.replayTimer) { halt(); play(); } };
    } });
}
