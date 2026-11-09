/* =====================================================================
   js/main.js
   Entry point: navigation (go), the render function that draws the current screen, global
   event handlers (click, submit, input, keydown) and the startup code.
   go and render are registered in state.js so other modules can call them without
   importing this file.
   ===================================================================== */

import { S, state, registerRender, registerGo } from "./state.js";
import { $ } from "./ui/dom.js";
import { store, saveProgress } from "./services/storage.js";
import { api, detectServer } from "./services/api.js";
import { Records, fillNames } from "./services/records.js";
import { renderModal, openModal, closeModal, modalLocked, stopReplay, showReport, openReplay } from "./ui/components/modals.js";
import { viewHome } from "./ui/views/home-view.js";
import { viewLevels } from "./ui/views/levels-view.js";
import { currentLevel, beginTry, viewPlay, initPlayChat, runLevel } from "./ui/views/play-view.js";
import { viewEndless, initEndlessChat, prepareSection, startEndless, runSection, showSectionReport, finishRun } from "./ui/views/endless-view.js";
import { viewRecords } from "./ui/views/records-view.js";
import { viewSettings, devCall } from "./ui/views/settings-view.js";
import { shareFromCheckbox } from "./services/share.js";

// Navigate to a screen: cancel any running round (new playToken), clear the modal and replay, merge extra values
// into S, re-render and scroll to the top.
function go(screen, extra = {}) {
  state.playToken++; state.fast = false; state.modal = null; stopReplay();
  Object.assign(S, extra, { screen });
  render();
  window.scrollTo({ top: 0, behavior: "auto" });
}
// Draw the current screen into #app: update the active nav button, call the view function, redraw the modal
// and run the per-screen initialisation (chat contents, shared-board names).
function render() {
  document.querySelectorAll(".nav button").forEach(b => b.removeAttribute("aria-current"));
  const navKey = { home: "home", levels: "levels", play: "levels", endless: "endless", records: "records", settings: "settings" }[S.screen];
  document.querySelector(`.nav button[data-to="${navKey}"]`)?.setAttribute("aria-current", "page");
  const views = { home: viewHome, levels: viewLevels, play: viewPlay, endless: viewEndless, records: viewRecords, settings: viewSettings };
  $("#app").innerHTML = views[S.screen]();
  renderModal();
  if (S.screen === "play") initPlayChat();
  if (S.screen === "endless" && state.E && ["brief", "loading", "report"].includes(state.E.status)) initEndlessChat();
  if (Records.mode === "shared") fillNames();
}

// Click handler: every button carries a data-action attribute that is dispatched here.
document.addEventListener("click", e => {
  const el = e.target.closest("[data-action]"); if (!el || el.disabled) return;
  const a = el.dataset.action, i = Number(el.dataset.i);
  if (a === "modalBack") { if (e.target === el && !modalLocked()) closeModal(); return; }
  switch (a) {
    case "home": go("home"); break;
    case "nav": {
      const to = el.dataset.to;
      if (to === "endless" && (!state.E || state.E.status === "over")) state.E = { status: "lobby" };
      go(to);
      break;
    }
    case "startTutorial": beginTry({ mode: "tutorial", tutStep: 0 }); break;
    case "startLevel": beginTry({ mode: "level", levelIdx: i }); break;
    case "retryLevel": beginTry({ tutStep: 2 }); break;
    case "toggleCard":
      if (!S.running && !S.last) { const id = el.dataset.id; S.selected = S.selected.includes(id) ? S.selected.filter(x => x !== id) : [...S.selected, id]; if (S.mode === "tutorial" && S.tutStep < 2) S.tutStep = 2; render(); }
      break;
    case "tutNext": S.tutStep++; render(); break;
    case "runLevel": runLevel(); break;
    case "skip": state.fast = true; break;
    case "showReport": showReport(currentLevel()); break;
    case "closeModal": closeModal(); break;
    case "openReplay": openReplay(S.last); break;
    case "closeReplay":
      if (S.screen === "endless" && state.E && state.E.status === "report") showSectionReport();
      else if (S.screen === "play" && S.last) showReport(currentLevel());
      else closeModal();
      break;
    case "startEndless": startEndless(); break;
    case "runSection": runSection(); break;
    case "sectionReport": showSectionReport(); break;
    case "nextSection": closeModal(); state.E.section++; prepareSection(); break;
    case "endlessReplay": openReplay(state.E.last); break;
    case "endRunAsk":
      openModal({ title: "End run", html: () => `<h2 style="font-size:24px">End this run?</h2><p>Your score of ${state.E.score} can then go on the record board.</p><div class="row"><button class="btn primary danger" data-action="finishRun" data-autofocus>End run</button><button class="btn" data-action="${state.E.status === "report" ? "sectionReport" : "closeModal"}">Keep playing</button></div>` });
      break;
    case "finishRun": finishRun(); break;
    case "saveRecord": {
      const nm = $("#rec-name") ? $("#rec-name").value : "";
      el.disabled = true;
      Records.submit(state.E.score, state.E.passed, nm).then(msg => { state.E.saved = msg; render(); });
      break;
    }
    case "speed": state.speed = el.dataset.s; store.set("cda.speed", state.speed); render(); break;
    case "askReset": S.confirmReset = true; render(); break;
    case "cancelReset": S.confirmReset = false; render(); break;
    case "resetProgress": state.progress = {}; saveProgress(); S.confirmReset = false; render(); break;
    case "aiTest": devCall(async () => { const j = await api("/api/ai/test", {}); state.dev.msg = `Connected. ${j.model} replied: "${j.reply}"`; }); break;
    case "consent": shareFromCheckbox(el); break;
  }
});
// Keep the Endless rules text and its word counter in sync while typing.
document.addEventListener("input", e => {
  if (e.target.id === "erules" && state.E) { state.E.rules = e.target.value; const n = (state.E.rules.match(/\S+/g) || []).length; const el = $("#ewords"); if (el) el.textContent = `${n} words · fewer than 100 earns a bonus`; }
});
// Escape closes the modal unless it is locked.
document.addEventListener("keydown", e => { if (e.key === "Escape" && state.modal && !modalLocked()) closeModal(); });

// Expose render and go to the other modules.
registerRender(render);
registerGo(go);

// Startup: show the first screen, then detect the game server and load the records.
/* Boot */
function start(data) {
  if (data && ["home", "levels", "records", "settings"].includes(data.screen)) S.screen = data.screen;
  render();
  detectServer().then(() => Records.init()).then(() => {
    const busy = S.running || (state.E && ["running", "loading"].includes(state.E.status));
    if (!busy && ["home", "records", "settings"].includes(S.screen)) render();
  });
}
try { window.claude?.hot?.snapshot?.(() => ({ screen: ["play", "endless"].includes(S.screen) ? "home" : S.screen })); } catch (_) {}
window.claude?.hot?.ready ? window.claude.hot.ready(start) : start(window.claude?.hot?.data ?? {});
