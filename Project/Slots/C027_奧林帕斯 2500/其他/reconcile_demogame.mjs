/**
 * Demogame 與 Simulator 對帳（headless）.
 *
 * 開發規範 §4.6 要求 Demogame 與 Simulator 使用同一套數學邏輯並可逐項對帳。
 * 這支腳本把 `index.html` 的主程式在 Node 裡跑起來（用最小 DOM stub 取代瀏覽器），
 * 直接呼叫它自己的 `playSpin` / `generateFreeSession`，統計出下列指標再與
 * Simulator 的 Card-Off 自然報表比較：
 *
 *   BG Hit Rate / BG 倍數球出現率 / BG 平均 Cascade 次數
 *   FG Hit Rate / FG 倍數球出現率
 *   FG 場景抽表占比（驗證場景表混合真的逐轉抽表）
 *
 * 用法：
 *   node reconcile_demogame.mjs [轉數]
 */

import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const ROUNDS = Number(process.argv[2] || 200000);

// --------------------------------------------------------------- DOM stub

function makeElement(id) {
  const element = {
    id,
    value: "",
    textContent: "",
    innerHTML: "",
    className: "",
    hidden: false,
    disabled: false,
    checked: false,
    dataset: {},
    style: {},
    children: [],
    firstChild: { textContent: "" },
    classList: { add() {}, remove() {}, toggle() {}, contains: () => false },
    appendChild(child) { this.children.push(child); return child; },
    removeChild() {},
    replaceChildren() { this.children = []; },
    insertAdjacentElement() {},
    setAttribute() {},
    removeAttribute() {},
    getAttribute: () => null,
    addEventListener() {},
    removeEventListener() {},
    closest: () => element,
    querySelector: () => makeElement(`${id}-q`),
    querySelectorAll: () => [],
    focus() {},
    click() {},
    showModal() {},
    close() {},
    scrollTo() {},
    remove() {},
    getBoundingClientRect: () => ({ width: 600, height: 400, top: 0, left: 0 }),
  };
  return element;
}

const elements = new Map();
function byId(id) {
  if (!elements.has(id)) elements.set(id, makeElement(id));
  return elements.get(id);
}

const documentStub = {
  title: "",
  documentElement: makeElement("html"),
  body: makeElement("body"),
  head: makeElement("head"),
  getElementById: byId,
  querySelector: (selector) => byId(`sel:${selector}`),
  querySelectorAll: () => [],
  createElement: (tag) => makeElement(`new:${tag}`),
  createDocumentFragment: () => makeElement("fragment"),
  createTextNode: (text) => ({ textContent: text }),
  addEventListener() {},
  removeEventListener() {},
  write() {},
  readyState: "complete",
};

const sandbox = {
  console,
  Math,
  JSON,
  Number,
  String,
  Boolean,
  Array,
  Object,
  Map,
  Set,
  Date,
  Intl,
  isNaN,
  parseInt,
  parseFloat,
  URLSearchParams,
  document: documentStub,
  setTimeout: () => 0,
  clearTimeout() {},
  setInterval: () => 0,
  clearInterval() {},
  requestAnimationFrame: () => 0,
  performance: { now: () => 0 },
  navigator: { language: "zh-TW", userAgent: "node" },
  fetch: () => Promise.reject(new Error("offline")),
  location: { search: "", href: "http://localhost/index.html" },
  matchMedia: () => ({ matches: false, addEventListener() {} }),
  alert() {},
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.self = sandbox;

// --------------------------------------------------------------- load pieces

const html = readFileSync(join(ROOT, "index.html"), "utf8");
const configText = readFileSync(join(ROOT, "config.js"), "utf8");

// the last <script> block without src is the game program; the block before it is
// the config-field guard, which we skip because the stub has no message bar
const blocks = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
const program = blocks.filter((code) => code.includes("function playSpin")).at(-1);
if (!program) throw new Error("找不到 index.html 的主程式區塊");

const context = vm.createContext(sandbox);
vm.runInContext(configText, context, { filename: "config.js" });
// the browser gets these from the config-bootstrap block, which needs document.write
vm.runInContext(
  'var C027_ACTIVE_CONFIG = "config.js"; var C027_CONFIG_FILES = ["config.js", "config_92A.js", "config_94A.js"];'
  + ' var C027_CONFIG_VERSION = "headless"; window.c027ConfigLoadFailed = () => {};',
  context,
  { filename: "bootstrap" },
);
// expose the math entry points the harness needs
vm.runInContext(
  program.replace(/\}\)\(\);\s*$/, "  window.__harness = { playSpin, generateFreeSession, chooseBaseTable, buildFreeSchedule, state, Box };\n})();"),
  context,
  { filename: "index.html" },
);

const harness = sandbox.__harness;
if (!harness) throw new Error("主程式沒有掛上 __harness");
const box = harness.Box;

// --------------------------------------------------------------- statistics

const stripNames = box.strip_names;
const bgTables = box.parameter.normal.base_reel_names.map((name) => stripNames.indexOf(name));
const fgTables = box.parameter.normal.free_table.names.map((name) => stripNames.indexOf(name));

let bgHits = 0;
let bgBallSpins = 0;
let bgCascades = 0;
let fgSpins = 0;
let fgHits = 0;
let fgBallSpins = 0;
const bgTableUse = new Map(bgTables.map((id) => [id, 0]));
const fgTableUse = new Map(fgTables.map((id) => [id, 0]));

for (let round = 0; round < ROUNDS; round += 1) {
  const tableId = harness.chooseBaseTable();
  bgTableUse.set(tableId, (bgTableUse.get(tableId) || 0) + 1);
  const spin = harness.playSpin(tableId, "BG", 0);
  if (spin.finalPay > 0) bgHits += 1;
  if (spin.multiplier.count > 0) bgBallSpins += 1;
  bgCascades += spin.steps.length;
  if (spin.scatterCount >= box.fg_trigger_count) {
    const session = harness.generateFreeSession();
    for (const free of session.spins) {
      fgSpins += 1;
      if (free.finalPay > 0) fgHits += 1;
      if (free.multiplier.count > 0) fgBallSpins += 1;
      fgTableUse.set(free.tableId, (fgTableUse.get(free.tableId) || 0) + 1);
    }
  }
}

const pct = (value) => `${(value * 100).toFixed(4)}%`;
const configured = (weights) => {
  const total = weights.reduce((sum, value) => sum + Number(value || 0), 0);
  return weights.map((value) => Number(value || 0) / total);
};

console.log(`Demogame headless 對帳　rounds=${ROUNDS.toLocaleString()}　config=${box.model} v${box.excel_version}`);
console.log("");
console.log(`BG Hit Rate            ${pct(bgHits / ROUNDS)}`);
console.log(`BG 倍數球出現率        ${pct(bgBallSpins / ROUNDS)}`);
console.log(`BG 平均 Cascade 次數   ${(bgCascades / ROUNDS).toFixed(6)}`);
console.log(`FG 轉數                ${fgSpins.toLocaleString()}`);
console.log(`FG Hit Rate            ${fgSpins ? pct(fgHits / fgSpins) : "n/a"}`);
console.log(`FG 倍數球出現率        ${fgSpins ? pct(fgBallSpins / fgSpins) : "n/a"}`);
console.log("");
console.log("場景抽表占比（實測 vs Config 設定）");
const bgConfigured = configured(box.parameter.normal.base_reel_weights);
bgTables.forEach((id, index) => {
  const used = (bgTableUse.get(id) || 0) / ROUNDS;
  console.log(`  BG ${stripNames[id].padEnd(16)} ${pct(used)}  設定 ${pct(bgConfigured[index])}`);
});
const fgConfigured = configured(box.parameter.normal.free_table.weights || []);
fgTables.forEach((id, index) => {
  const used = fgSpins ? (fgTableUse.get(id) || 0) / fgSpins : 0;
  console.log(`  FG ${stripNames[id].padEnd(16)} ${pct(used)}  設定 ${pct(fgConfigured[index] ?? 0)}`);
});

// the report reads this file so its reconciliation table cannot drift from the run
writeFileSync(join(HERE, "reconcile_demogame.json"), JSON.stringify({
  rounds: ROUNDS,
  model: box.model,
  excel_version: box.excel_version,
  bg_hit_rate: bgHits / ROUNDS,
  bg_ball_rate: bgBallSpins / ROUNDS,
  bg_avg_cascades: bgCascades / ROUNDS,
  fg_spins: fgSpins,
  fg_hit_rate: fgSpins ? fgHits / fgSpins : 0,
  fg_ball_rate: fgSpins ? fgBallSpins / fgSpins : 0,
  bg_table_share: bgTables.map((id, index) => ({
    name: stripNames[id], measured: (bgTableUse.get(id) || 0) / ROUNDS, configured: bgConfigured[index],
  })),
  fg_table_share: fgTables.map((id, index) => ({
    name: stripNames[id],
    measured: fgSpins ? (fgTableUse.get(id) || 0) / fgSpins : 0,
    configured: fgConfigured[index] ?? 0,
  })),
}, null, 2) + "\n", "utf8");
