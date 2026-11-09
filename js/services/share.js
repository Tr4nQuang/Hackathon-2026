/* =====================================================================
   js/services/share.js
   Anonymous result sharing. Nothing is sent unless the player ticks the box on a report (it is never ticked
   for them). A play holds the level, the rule cards (or the written rules in Endless mode), the grade and the
   zones that leaked or turned a customer away. It never holds a name or any chat text. The local game server
   stores it only if Supabase is set up in .env.
   ===================================================================== */

import { AI } from "../state.js";
import { $, esc } from "../ui/dom.js";
import { api } from "./api.js";

export const CONSENT_TEXT = "Share my anonymous results to help research. No name or personal data is saved.";
const attempts = {};

// A random id (run ids and the per-tab session id).
const uuid = () => crypto.randomUUID();
// The id of this browser tab's session (kept in sessionStorage, never linked to a person).
export function sessionId() {
  try { let id = sessionStorage.getItem("cda.session"); if (!id) { id = uuid(); sessionStorage.setItem("cda.session", id); } return id; } catch (_) { return uuid(); }
}
// Grade fields the server needs.
const gradeFields = g => ({ key: g.key, stars: g.stars, overall: g.overall, sec: g.sec, help: g.help });
// The zones that leaked or turned a customer away in a round.
const eventsOf = t => [...[...t.breached].map(zone => ({ zone, outcome: "leaked" })), ...[...t.refusedTopics].map(zone => ({ zone, outcome: "refused" }))];

// The play of a finished tutorial or level round r.
export function levelPlay(L, levelIdx, r) {
  const key = L.tutorial ? "tutorial" : `level_${levelIdx + 1}`;
  attempts[key] = (attempts[key] || 0) + 1;
  return { mode: L.tutorial ? "tutorial" : "level", level_id: key, run_id: uuid(), attempt_number: attempts[key], package_index: r.pkg,
    chosen_rules: r.sel, rules_used: r.sel.length, core_hacked: r.tally.coreBreached, grade: gradeFields(r.grade), events: eventsOf(r.tally),
    guide_skipped: false };
}
// The play of one finished Endless section.
export function sectionPlay(section, world, rules, live, r) {
  return { mode: "endless", level_id: `endless_${world.id}`, run_id: uuid(), attempt_number: section, package_index: 0, player_rules: rules, live,
    core_hacked: r.tally.coreBreached, grade: gradeFields(r.grade), events: eventsOf(r.tally) };
}
// The tick box and its message line (only when the local game server is there to take the result).
export function consentHtml(scope, sent) {
  if (!AI.server) return "";
  return `<div class="consent"><label><input type="checkbox" data-action="consent" data-scope="${esc(scope)}" ${sent ? "checked disabled" : ""}> ${esc(CONSENT_TEXT)}</label><p class="muted" id="consent-msg" style="font-size:13px" role="status"></p></div>`;
}
// Send plays to the server; returns the message to show.
export async function sendPlays(plays) {
  try {
    const j = await api("/api/play", { session_id: sessionId(), plays });
    return j.saved ? "Thank you, your anonymous result was saved." : "Storage is not set up here, so nothing was saved.";
  } catch (e) { return "Couldn't reach the game server: " + e.message; }
}
// Handle a click on a consent box: send the plays of its scope once. The scopes are registered by the views.
const sources = {};
export const registerConsent = (scope, getter) => { sources[scope] = getter; };
export async function shareFromCheckbox(el) {
  if (!el.checked) return;
  const src = sources[el.dataset.scope]; if (!src) return;
  const got = src(); if (!got || got.sent) return;
  got.markSent(); el.disabled = true;
  const msg = await sendPlays(got.plays);
  const line = $("#consent-msg"); if (line) line.textContent = msg;
}
