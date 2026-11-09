/* =====================================================================
   js/state.js
   Central place for all shared mutable state. Other modules import these objects
   and mutate their properties, so every module sees the same values.
   ES module imports of primitives are read-only, so primitives (speed, fast,
   playToken ...) live as properties of the single `state` object instead of
   separate variables. This file imports nothing, which avoids circular dependencies.
   It also holds the render() and go() hooks that main.js registers at startup, so
   views can re-render or navigate without importing main.js.
   ===================================================================== */

// Current screen and gameplay state: screen name, selected level/package, round messages, rule shop,
// selected card ids, running flag, last result, tutorial step, last package per level, reset confirmation.
// Only mutated (Object.assign / property writes), never reassigned.
export const S = { screen: "home", mode: null, levelIdx: 0, pkg: 0, msgs: null, shop: [], selected: [], running: false, last: null, tutStep: 0, lastPkg: {}, confirmReset: false };
// Live AI / local game server status: whether the server answers, whether live AI is ready, its model name and
// whether anonymous play storage is set up. The API key never reaches the browser.
export const AI = { server: false, ready: false, model: "", storage: false };
// Shared variables that used to be top-level `let`s. Write them as state.<name> = value.
export const state = {
  // E: the current Endless run (null when none). Its status is lobby, brief, loading, report or over.
  E: null,
  // modal: the open dialog { title, html(), after?, wide? } or null.
  modal: null,
  // replayTimer: interval id of the replay player (null when stopped).
  replayTimer: null,
  // speed: chat animation speed, normal / fast / instant (restored from localStorage by services/storage.js).
  speed: "normal",
  // fast: true after the player presses Skip, so waits are skipped for the current round.
  fast: false,
  // playToken: incremented on every navigation or new round so an old, still-running round can detect it is stale and stop.
  playToken: 0,
  // progress: saved campaign results per level (filled from localStorage by services/storage.js).
  progress: {},
  // dev: message / error / busy flags of the AI connection panel in Settings.
  dev: { msg: "", err: "", busy: false },
  // renderFn: the real render function, registered by main.js through registerRender().
  // goFn: the real navigation function, registered by main.js through registerGo().
  renderFn: null,
  goFn: null
};
// Register the app render function. Lets modules trigger a re-render without importing main.js.
export function registerRender(fn) { state.renderFn = fn; }
// Re-render the whole app through the registered function (no-op before registration).
export function render() { if (state.renderFn) state.renderFn(); }
// Register the app navigation function (go in main.js).
export function registerGo(fn) { state.goFn = fn; }
// Navigate to a screen, optionally merging extra values into S (no-op before registration).
export function go(screen, extra) { if (state.goFn) state.goFn(screen, extra); }
