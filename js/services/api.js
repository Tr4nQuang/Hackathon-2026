/* =====================================================================
   js/services/api.js
   Communication with the optional local game server (/api/*) and the AI status tag
   in the top bar. Without the server the game runs in demo mode.
   ===================================================================== */

import { AI } from "../state.js";
import { $ } from "../ui/dom.js";

// POST a JSON body to path and return the parsed JSON. Throws an Error (with .status) on a non-OK response.
export async function api(path, body) {
  const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) { const e = new Error(j.error || `Request failed (${r.status})`); e.status = r.status; throw e; }
  return j;
}
// When served from localhost, ask /api/status whether the game server and live AI are available and update AI.
export async function detectServer() {
  if (["localhost", "127.0.0.1"].includes(location.hostname) && location.protocol.startsWith("http")) {
    try {
      const r = await fetch("/api/status", { cache: "no-store" });
      if (r.ok) { const j = await r.json(); if (j.server) Object.assign(AI, { server: true, ready: j.ai_ready, model: j.model, storage: !!j.storage }); }
    } catch (_) {}
  }
  updateAiTag();
}
// Show the mode in the top bar: Live AI on / Local server / Demo build.
export function updateAiTag() { $("#ai-tag").textContent = AI.server ? (AI.ready ? "Live AI on" : "Local server") : "Demo build"; }
