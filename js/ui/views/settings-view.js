/* =====================================================================
   js/ui/views/settings-view.js
   Settings screen: chat speed, progress reset and the AI connection panel (live AI status and a
   connection test). There is no field for an API key: the key lives in .env on the computer that runs server.py.
   ===================================================================== */

import { S, AI, state, render } from "../../state.js";
import { esc, svgIcon } from "../dom.js";
import { updateAiTag } from "../../services/api.js";

// Return the HTML of the settings page. The AI panel only reports the state of the local game server and live AI.
export function viewSettings() {
  const segs = ["normal", "fast", "instant"].map(s => `<button data-action="speed" data-s="${s}" aria-pressed="${state.speed === s}">${s[0].toUpperCase() + s.slice(1)}</button>`).join("");
  const help = !AI.server
    ? `<b>The live AI needs the local game server</b>
      <span class="muted" style="font-size:14px">Run <span class="mono">python server.py</span> and open <span class="mono">http://localhost:8000</span>. Without it the game uses built-in attack scripts.</span>`
    : AI.ready
      ? `<b>Live AI is on</b>
      <span class="muted" style="font-size:14px">The attacker and the chatbot are ${esc(AI.model)}. The key is read from the .env file on this computer and never reaches the browser.</span>`
      : `<b>Live AI is off</b>
      <span class="muted" style="font-size:14px">The key is never typed into the game. To switch it on, copy .env.example to .env, set <span class="mono">USE_FAKE_AI=false</span>, add your own <span class="mono">GEMINI_API_KEY</span> and restart the server.</span>`;
  const test = AI.server && AI.ready
    ? `<div class="row"><button class="btn" data-action="aiTest" ${state.dev.busy ? "disabled" : ""}>Test connection</button></div>` : "";
  return `<div class="settings">
    <div class="section-head"><p class="eyebrow">Settings</p><h2>Game settings</h2></div>
    <section class="panel"><h3>Chat speed</h3><p class="muted" style="font-size:14px">How fast attacks and replies appear during a round.</p><div class="seg" role="group" aria-label="Chat speed">${segs}</div></section>
    <section class="panel"><h3>Progress</h3><p class="muted" style="font-size:14px">Level stars and best scores are saved in this browser.</p>
      <div class="row">${S.confirmReset ? `<span>Erase all level progress? This can't be undone.</span><button class="btn danger small" data-action="resetProgress">Erase progress</button><button class="btn small" data-action="cancelReset">Cancel</button>` : `<button class="btn small" data-action="askReset">Reset level progress</button>`}</div></section>
    <section class="panel"><div class="row" style="justify-content:space-between"><h3>AI connection</h3><span class="chip ${AI.ready ? "good" : ""}">${AI.server ? (AI.ready ? "Live AI ready · " + esc(AI.model) : "Server running · live AI off") : "No local server"}</span></div>
      <div class="lockbox">${svgIcon("lock")}<div class="stack" style="gap:8px">${help}</div></div>${test}
      ${state.dev.msg ? `<p class="okmsg" role="status">${esc(state.dev.msg)}</p>` : ""}${state.dev.err ? `<p class="err" role="alert">${esc(state.dev.err)}</p>` : ""}
      ${AI.server ? `<p class="muted" style="font-size:13px">${AI.storage ? "Anonymous result storage is set up. It is only used when you tick the box on a report." : "Anonymous result storage is not set up (SUPABASE_URL and SUPABASE_KEY in .env)."}</p>` : ""}</section>
  </div>`;
}
// Run an async action fn from the AI panel: set the busy flag, catch errors into state.dev.err, then re-render.
export async function devCall(fn) {
  state.dev = { msg: "", err: "", busy: true }; render();
  try { await fn(); } catch (e) { state.dev.err = e.message; }
  state.dev.busy = false; updateAiTag(); render();
}
