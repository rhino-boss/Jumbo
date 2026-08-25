"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const projectRoot = path.resolve(__dirname, "..", "..", "..");

function loadWindowConfig(relativePath) {
  const context = { window: {} };
  vm.runInNewContext(fs.readFileSync(path.join(projectRoot, relativePath), "utf8"), context, {
    filename: relativePath,
  });
  return context.window.H016_CONFIG;
}

const base = loadWindowConfig("Versions/3.0/config.js");
const rtp = loadWindowConfig("Versions/3.0/config_92A.js");
const cfg = JSON.parse(JSON.stringify(base));
cfg.card_system = JSON.parse(JSON.stringify(rtp.card_system));

const WW = 0;
const W2 = 1;
const C1 = 2;
const SCORE = [3, 4, 5, 6, 7, 8, 9, 10];
const BASE_BET = 100;
const BET_MULTI = 1;
const MAX_RETRY = Math.max(1, Number(cfg.card_system?.retry_limit || 10000));
const useFixedBoundary = process.argv.includes("--fixed");
const tables = {};

for (const [name, raw] of Object.entries(cfg.tables)) {
  tables[name] = {
    ...raw,
    cumulative: raw.weights.map((weights) => {
      let sum = 0;
      return weights.map((weight) => (sum += Math.max(0, Number(weight))));
    }),
    dropCumulative: raw.drop_weights.map((weights) => {
      let sum = 0;
      return weights.map((weight) => (sum += Math.max(0, Number(weight))));
    }),
  };
}

function pick(values, weights) {
  let total = weights.reduce((sum, weight) => sum + Math.max(0, Number(weight) || 0), 0);
  if (total <= 0) return values[0];
  let target = Math.random() * total;
  for (let index = 0; index < values.length; index++) {
    target -= Math.max(0, Number(weights[index]) || 0);
    if (target < 0) return values[index];
  }
  return values.at(-1);
}

function drawIndex(tableName, reel) {
  const cumulative = tables[tableName].cumulative[reel];
  const target = Math.random() * cumulative.at(-1);
  let low = 0;
  let high = cumulative.length - 1;
  while (low < high) {
    const middle = (low + high) >> 1;
    if (target < cumulative[middle]) high = middle;
    else low = middle + 1;
  }
  return low;
}

function draw(tableName, reel) {
  const table = tables[tableName];
  const cumulative = table.dropCumulative[reel];
  const target = Math.random() * cumulative.at(-1);
  let low = 0;
  let high = cumulative.length - 1;
  while (low < high) {
    const middle = (low + high) >> 1;
    if (target < cumulative[middle]) high = middle;
    else low = middle + 1;
  }
  return Number(table.drop_values[reel][low]);
}

const canonical = (symbol) => (symbol >= 11 && symbol <= 18 ? symbol - 8 : symbol);

function makeBoard(tableName) {
  return Array.from({ length: 5 }, (_, reel) => {
    const symbols = tables[tableName].reels[reel];
    const stop = drawIndex(tableName, reel);
    return Array.from({ length: 4 }, (_, row) => Number(symbols[(stop + row) % symbols.length]));
  });
}

function evaluate(board) {
  let rawPay = 0;
  const hits = new Set();
  for (const target of SCORE) {
    const counts = [];
    const positions = [];
    for (let reel = 0; reel < 5; reel++) {
      const matched = [];
      for (let row = 0; row < 4; row++) {
        const symbol = board[reel][row];
        if (symbol === WW || symbol === W2 || canonical(symbol) === target) matched.push([reel, row]);
      }
      if (!matched.length) break;
      counts.push(matched.length);
      positions.push(matched);
    }
    if (counts.length < 3) continue;
    const ways = counts.reduce((product, count) => product * count, 1);
    const pay = Number(cfg.pays[String(target)][counts.length - 3]) * ways;
    if (pay <= 0) continue;
    rawPay += pay;
    positions.flat().forEach(([reel, row]) => hits.add(`${reel},${row}`));
  }
  return { rawPay, hits };
}

function addW2(board, tableName, gold, freeGame = false) {
  if (!gold.length) return 0;
  const randomWild = tables[tableName].random_wild;
  const count = Number(pick(randomWild.values, randomWild.weights)) || 0;
  if (count <= 0) return 0;
  const source = gold[Math.floor(Math.random() * gold.length)];
  const candidates = [];
  for (let reel = 1; reel < 5; reel++) {
    for (let row = 0; row < 4; row++) {
      if (![WW, W2, C1].includes(board[reel][row])) candidates.push([reel, row]);
    }
  }
  if (candidates.length < count) return 0;
  board[source[0]][source[1]] = W2;
  candidates.sort(() => Math.random() - 0.5);
  for (const [reel, row] of candidates.slice(0, count)) board[reel][row] = W2;
  return count;
}

function spin(tableName, freeGame = false) {
  const table = tables[tableName];
  const multipliers = table.multipliers?.length ? table.multipliers : freeGame ? [2, 4, 6, 10] : [1, 2, 3, 5];
  const board = makeBoard(tableName);
  let pay = 0;
  let combo = 0;
  let pendingGold = [];
  let w2Used = false;
  while (true) {
    if (pendingGold.length && (freeGame || !w2Used)) {
      if (addW2(board, tableName, pendingGold, freeGame)) w2Used = true;
    }
    pendingGold = [];
    const win = evaluate(board);
    if (!win.rawPay) break;
    pay += win.rawPay * multipliers[Math.min(combo, multipliers.length - 1)] * BASE_BET * BET_MULTI;
    combo++;
    for (const key of win.hits) {
      const [reel, row] = key.split(",").map(Number);
      const symbol = board[reel][row];
      if (symbol >= 11 && symbol <= 18) {
        board[reel][row] = WW;
        pendingGold.push([reel, row]);
      } else {
        board[reel][row] = -1;
      }
    }
    for (let reel = 0; reel < 5; reel++) {
      for (let row = 0; row < 4; row++) {
        if (board[reel][row] === -1) board[reel][row] = draw(tableName, reel);
      }
    }
  }
  return {
    pay,
    combo,
    scatter: board.flat().filter((symbol) => symbol === C1).length,
  };
}

function naturalBaseSpin() {
  const selection = cfg.table_selection?.base;
  if (selection?.length) {
    return spin(pick(selection.map((item) => item.table), selection.map((item) => item.weight)));
  }
  return spin("bg_high");
}

function pickCard() {
  const cards = cfg.card_system.profiles.weight_2.base_game;
  return pick(cards, cards.map((card) => card.weight));
}

function cardMatches(card, pay) {
  const ratio = pay / (BASE_BET * BET_MULTI);
  return Number(card.min) < ratio && ratio <= Number(card.max);
}

function cardDistance(card, pay) {
  const ratio = pay / (BASE_BET * BET_MULTI);
  if (cardMatches(card, pay)) return 0;
  if (ratio <= Number(card.min)) return Number(card.min) - ratio;
  return ratio - Number(card.max);
}

function cardSpin(card, diagnostics) {
  if (card.type === "free_game") {
    for (let retry = 0; retry < MAX_RETRY; retry++) {
      const result = naturalBaseSpin();
      diagnostics.retries += retry > 0 ? 1 : 0;
      if (result.scatter >= 3) return result;
    }
    diagnostics.fallbacks++;
    return naturalBaseSpin();
  }
  const table = card.table === "A" ? "bg_low" : "bg_high";
  let nearest = null;
  let nearestDistance = Infinity;
  for (let retry = 0; retry < MAX_RETRY; retry++) {
    const result = spin(table);
    if (result.scatter >= 3) continue;
    if (useFixedBoundary && cardMatches(card, result.pay)) return result;
    const distance = cardDistance(card, result.pay);
    if (!useFixedBoundary && distance === 0) return result;
    if (distance < nearestDistance) {
      nearest = result;
      nearestDistance = distance;
    }
  }
  diagnostics.fallbacks++;
  if (nearestDistance > 0) diagnostics.unmatchedFallbacks++;
  return nearest || naturalBaseSpin();
}

const rounds = Number(process.argv[2] || 10000);
const diagnostics = { retries: 0, fallbacks: 0, unmatchedFallbacks: 0 };
const cardCounts = { zero: 0, paying: 0, freeGame: 0 };
const intervalStats = new Map();
let hits = 0;
let cascades = 0;

for (let index = 0; index < rounds; index++) {
  const card = pickCard();
  if (card.type === "free_game") cardCounts.freeGame++;
  else if (Number(card.max) <= 0) cardCounts.zero++;
  else cardCounts.paying++;
  const result = cardSpin(card, diagnostics);
  const interval = card.type === "free_game" ? "Free Game" : `(${card.min}, ${card.max}]`;
  const intervalRow = intervalStats.get(interval) || { selected: 0, positive: 0, matched: 0, zeroPay: 0 };
  intervalRow.selected++;
  intervalRow.positive += result.pay > 0 ? 1 : 0;
  intervalRow.matched += card.type === "free_game" ? Number(result.scatter >= 3) : Number(cardMatches(card, result.pay));
  intervalRow.zeroPay += result.pay === 0 ? 1 : 0;
  intervalStats.set(interval, intervalRow);
  if (result.pay > 0) hits++;
  cascades += result.combo;
}

console.log(JSON.stringify({
  rounds,
  useFixedBoundary,
  hits,
  hitRate: hits / rounds,
  cardCounts,
  cardRates: Object.fromEntries(Object.entries(cardCounts).map(([key, value]) => [key, value / rounds])),
  avgCascades: cascades / rounds,
  fallbacks: diagnostics.fallbacks,
  unmatchedFallbacks: diagnostics.unmatchedFallbacks,
  intervalStats: Object.fromEntries(intervalStats),
}, null, 2));
