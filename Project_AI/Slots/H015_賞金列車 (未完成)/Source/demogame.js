(() => {
  "use strict";

  const Box = window.H015_BOX_DATA;
  if (!Box) throw new Error("H015 config.js was not loaded.");

  const $ = (id) => document.getElementById(id);
  const SCORE = new Set(Box.symbols_score || []);
  const GOLD = new Set(Box.symbols_gold || []);
  const CODE = Object.fromEntries(Object.entries(Box.symbol_str).map(([id, code]) => [Number(id), code]));
  const ID = Object.fromEntries(Object.entries(CODE).map(([id, code]) => [code, Number(id)]));
  const WW = ID.WW;
  const C1 = ID.C1;
  const REELS = Box.reel_num;
  const ROWS = Box.window_size;
  const MODE_NORMAL = Box.mode_normalbet;
  const MODE_BUY = Box.mode_featurebuy;
  const MULTIPLIERS = Box.value_multiplier_range;
  const HELP_PATH = "./game_help_draft.md";
  const STORAGE_KEY = "slotDemoLanguage";
  const BET_LEVELS = Box.bet_options?.length ? Box.bet_options : [1, 2, 5, 10];

  const T = {
    en: {
      game: "Wild Train", base: "Base Game", free: "Free Game", ready: "Ready — press Spin",
      cascade: "Cascade", mult: "Mult", fgLeft: "FG Left", credit: "Credit", bet: "Bet", win: "Win",
      stats: "Simulation Stats", rounds: "Total Rounds", hit: "Hit Rate", maxMult: "Max Multiplier",
      play: "Play", spin: "Spin", nextFg: "Next FG", auto: "Auto", stop: "Stop", speed: "Speed",
      betMode: "Bet Mode", normal: "Normal Bet", buy: "Buy Feature (75x)", setting: "Setting",
      debug: "Debug Mode", language: "Language", help: "Help", reset: "Reset", clear: "Clear",
      reelRng: "Reel RNG", result: "Spin Result", wins: "Way Wins", setRng: "Set RNG",
      rngPlaceholder: "6 stop indexes, e.g. 1 2 3 4 5 6", previous: "◀◀ Previous", next: "Next ▶▶",
      forceFg: "Force FG", buyStart: "Buy Feature paid — guaranteed FG trigger spin",
      insufficient: "Insufficient credit", invalidRng: "RNG needs exactly 6 valid stop indexes",
      noWin: "No win", complete: "complete", triggered: "Free Game triggered", retrigger: "Free Game retriggered",
      helpTitle: "Game Help", close: "Close", loading: "Loading game rules...", loadFail: "Unable to load game_help_draft.md.",
      footer: "Double-click to play offline. No server needed.", configFixed: "H015192 (xlsx)",
      languageChanged: "Language changed to English", resetDone: "Game and statistics reset"
    },
    zh: {
      game: "賞金列車", base: "基礎遊戲", free: "免費遊戲", ready: "準備完成 — 請按 Spin",
      cascade: "連消", mult: "倍數", fgLeft: "FG 剩餘", credit: "餘額", bet: "押注", win: "得分",
      stats: "模擬統計", rounds: "總局數", hit: "中獎率", maxMult: "最高倍數",
      play: "遊戲", spin: "Spin", nextFg: "下一次 FG", auto: "自動", stop: "停止", speed: "速度",
      betMode: "押注模式", normal: "一般押注", buy: "購買特色 (75x)", setting: "設定",
      debug: "除錯模式", language: "語言", help: "Help", reset: "重置", clear: "清除",
      reelRng: "輪帶 RNG", result: "Spin 結果", wins: "Ways 得獎", setRng: "指定 RNG",
      rngPlaceholder: "輸入 6 個停輪位置，例如 1 2 3 4 5 6", previous: "◀◀ 上一步", next: "下一步 ▶▶",
      forceFg: "強制 FG", buyStart: "已支付購買特色費用 — 本局保證觸發 FG",
      insufficient: "餘額不足", invalidRng: "RNG 必須是 6 個有效停輪位置",
      noWin: "未得獎", complete: "完成", triggered: "已觸發免費遊戲", retrigger: "免費遊戲再觸發",
      helpTitle: "遊戲 Help", close: "關閉", loading: "正在載入遊戲規則…", loadFail: "無法載入 game_help_draft.md。",
      footer: "可直接雙擊離線遊玩，不需要伺服器。", configFixed: "H015192（xlsx）",
      languageChanged: "語言已切換為中文", resetDone: "遊戲與統計已重置"
    }
  };

  const initialLanguage = (() => {
    try { return localStorage.getItem(STORAGE_KEY) === "zh" ? "zh" : "en"; } catch (_) { return "en"; }
  })();

  const state = {
    language: initialLanguage, balance: 10000, betIndex: 0, busy: false, auto: false, debug: false,
    fg: { remaining: 0, total: 0, played: 0 }, rounds: 0, normalRounds: 0, totalBet: 0, totalWin: 0,
    hitRounds: 0, naturalFg: 0, maxMultiplier: 1, lastWin: 0, lastSpin: null, snapshots: [], snapshotIndex: -1,
    log: [], helpMarkdown: ""
  };

  const el = Object.fromEntries([
    "board", "messageBar", "balanceValue", "betValue", "winValue", "roundCountValue", "rtpValue", "hitRateValue",
    "fgTriggerValue", "maxMultiplierValue", "spinBtn", "autoBtn", "betMinusBtn", "betPlusBtn", "betBtn", "betMenu",
    "speedRange", "speedValue", "normalBetBtn", "buyFeatureBtn", "debugModeInput", "languageSelect", "configSelect",
    "helpBtn", "resetBtn", "helpDialog", "closeHelpBtn", "helpContent", "helpSourceFrame", "rngList", "lineList",
    "spinResultList", "liveLogBody", "clearLogBtn", "reelRngInput", "setRngResetBtn", "previousStepBtn", "nextStepBtn",
    "forceFgInput", "modeText", "featureStatus", "carryMultiValue", "fgLeftPill", "fgLeftValue",
    "cardRangeSelect", "gameId", "gameName", "multiplierWindow"
  ].map((id) => [id, $(id)]));

  let displayedMultiplierIndex = 0;

  function text(key) { return T[state.language][key] || T.en[key] || key; }
  function format(value, digits = 0) { return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: digits }); }
  function formatBet(value) { return Number(value || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function cumulativeChoice(cum) {
    const max = cum[cum.length - 1];
    if (!(max > 0)) return 0;
    const roll = Math.floor(Math.random() * max) + 1;
    return cum.findIndex((value) => roll <= value);
  }
  function clone(value) { return JSON.parse(JSON.stringify(value)); }
  function delay() { return new Promise((resolve) => setTimeout(resolve, Math.max(25, 260 / Number(el.speedRange.value || 1)))); }
  function activeBet() { return BET_LEVELS[state.betIndex]; }
  function coinIn(mode = MODE_NORMAL) { return Box.default_coin_in * Box.normalbet * activeBet() * (mode === MODE_BUY ? Box.featurebuy : 1); }
  function payAmount(raw, multiplier) { return raw * multiplier * activeBet(); }

  function multiplierIndex(value) {
    const index = MULTIPLIERS.indexOf(Number(value));
    return index < 0 ? 0 : index;
  }

  function renderMultiplierTrack(index = displayedMultiplierIndex, animate = false) {
    displayedMultiplierIndex = Math.max(0, Math.min(index, MULTIPLIERS.length - 1));
    const values = [-2, -1, 0, 1, 2].map((offset) => {
      const target = displayedMultiplierIndex + offset;
      if (target < 0) return MULTIPLIERS[MULTIPLIERS.length + target];
      return MULTIPLIERS[target] ?? null;
    });
    el.multiplierWindow.classList.remove("roll-one");
    el.multiplierWindow.innerHTML = values.map((value, slot) => {
      const classes = ["multiplier-step", slot < 2 ? "is-previous" : "", slot === 2 ? "is-active" : ""].filter(Boolean).join(" ");
      return `<span class="${classes}">${value == null ? "" : `x${value}`}</span>`;
    }).join("");
    if (animate) {
      void el.multiplierWindow.offsetWidth;
      el.multiplierWindow.classList.add("roll-one");
    }
  }

  async function rollMultiplierTo(value) {
    const target = Math.max(displayedMultiplierIndex, multiplierIndex(value));
    while (displayedMultiplierIndex < target) {
      renderMultiplierTrack(displayedMultiplierIndex + 1, true);
      await new Promise((resolve) => setTimeout(resolve, Math.max(45, 150 / Number(el.speedRange.value || 1))));
    }
  }

  function generateBoard(tableId, forcedStops = null) {
    const board = Array.from({ length: ROWS }, () => Array(REELS).fill(99));
    const stops = [];
    for (let reel = 0; reel < REELS; reel++) {
      const length = Box.reels_len[tableId][reel];
      const stop = forcedStops ? forcedStops[reel] % length : cumulativeChoice(Box.arr_reels_weight_cum[tableId].slice(0, length).map((row) => row[reel]));
      stops.push(stop);
      for (let row = 0; row < ROWS; row++) {
        if (Box.score_area[row][reel]) board[row][reel] = Box.arr_reels[tableId][(stop + row) % length][reel];
      }
    }
    return { board, stops };
  }

  function normalizeGold(board) {
    const gold = Array.from({ length: ROWS }, () => Array(REELS).fill(false));
    for (let row = 0; row < ROWS; row++) for (let reel = 0; reel < REELS; reel++) {
      if (GOLD.has(board[row][reel])) { board[row][reel] -= 8; gold[row][reel] = true; }
    }
    return gold;
  }

  function evaluate(board, gold) {
    const symbols = [...new Set(board.map((row) => row[0]).filter((symbol) => SCORE.has(symbol)))];
    const wins = []; const hit = Array.from({ length: ROWS }, () => Array(REELS).fill(0)); let raw = 0;
    for (const symbol of symbols) {
      let length = 0; let ways = 1;
      for (let reel = 0; reel < REELS; reel++) {
        let count = 0;
        for (let row = 0; row < ROWS; row++) if (board[row][reel] === symbol || board[row][reel] === WW) count++;
        if (!count) break;
        length++; ways *= count;
      }
      const unit = length >= 3 ? Number(Box.pay_table[symbol][length - 3] || 0) : 0;
      if (!unit) continue;
      raw += unit * ways; wins.push({ symbol, length, ways, unit });
      for (let reel = 0; reel < length; reel++) for (let row = 0; row < ROWS; row++) {
        if (board[row][reel] === symbol || board[row][reel] === WW) hit[row][reel] = gold[row][reel] ? 2 : 1;
      }
    }
    return { raw, wins, hit };
  }

  function comboTable(raw, tableId, combo, reel) {
    const key = combo < 3 ? `combo${combo}` : "combo3_plus";
    return raw[tableId][key].map((row) => row[reel]);
  }

  function drop(board, gold, hit, tableId, combo, dropIndex) {
    const source = dropIndex === 1 ? Box.weight_cum_drop_symbol_b : dropIndex === 2 ? Box.weight_cum_drop_symbol_c : Box.weight_cum_drop_symbol_a;
    for (let row = 0; row < ROWS; row++) for (let reel = 0; reel < REELS; reel++) {
      if (hit[row][reel] === 1) board[row][reel] = cumulativeChoice(comboTable(source, tableId, combo, reel));
      if (hit[row][reel] === 2) { board[row][reel] = WW; gold[row][reel] = false; }
    }
    for (let row = 0; row < ROWS; row++) for (let reel = 0; reel < REELS; reel++) {
      if (GOLD.has(board[row][reel])) { board[row][reel] -= 8; gold[row][reel] = true; }
    }
  }

  function chooseTable(scene, mode) {
    if (scene === "BG" && mode === MODE_BUY) return Box.strip_bf;
    if (scene === "BG") return cumulativeChoice(Box.weight_cum_table_bg);
    return cumulativeChoice(mode === MODE_BUY ? Box.weight_cum_table_bf : Box.weight_cum_table_fg) + 2;
  }

  function forcedStops() {
    const value = el.reelRngInput.value.trim();
    if (!value) return null;
    const stops = value.split(/[\s,]+/).map(Number);
    if (stops.length !== REELS || stops.some((n) => !Number.isInteger(n) || n < 0)) throw new Error(text("invalidRng"));
    return stops;
  }

  function simulateScene(scene, mode, forceTrigger = false) {
    const tableId = chooseTable(scene, mode);
    let first = generateBoard(tableId, forcedStops());
    if (forceTrigger && scene === "BG") {
      const active = [];
      for (let reel = 0; reel < REELS; reel++) for (let row = 0; row < ROWS; row++) if (Box.score_area[row][reel]) active.push([row, reel]);
      const present = first.board.flat().filter((symbol) => symbol === C1).length;
      const candidates = active.filter(([row, reel]) => first.board[row][reel] !== C1);
      for (let i = 0; i < Math.max(0, 3 - present); i++) {
        const [row, reel] = candidates[candidates.length - 1 - i * 3];
        first.board[row][reel] = C1;
      }
    }
    const board = first.board; const gold = normalizeGold(board); const dropIndex = cumulativeChoice(scene === "BG" ? Box.weight_cum_drop_choose_bg : Box.weight_cum_drop_choose_fg);
    const multiProfile = scene === "BG" ? Box.weight_cum_multi_appear_bg : Box.weight_cum_multi_appear_fg;
    const multiBase = scene === "BG" ? (mode === MODE_BUY ? dropIndex : tableId * 3 + dropIndex) : (tableId - 2) * 3 + dropIndex;
    let level = scene === "BG" ? 0 : 3; let combo = 0; let total = 0; const steps = [];
    while (combo < 200) {
      const before = clone(board); const result = evaluate(board, gold);
      const profileLevel = Math.max(0, Math.min(4, scene === "BG" ? level : level - 3));
      const bombCum = multiProfile[profileLevel].map((row) => row[multiBase]);
      const lightning = cumulativeChoice(bombCum);
      level = Math.min(MULTIPLIERS.length - 1, level + lightning);
      const multiplier = MULTIPLIERS[level];
      level = Math.min(MULTIPLIERS.length - 1, level + 1);
      const win = payAmount(result.raw, multiplier); total += win;
      const snapshot = { board: before, gold: clone(gold), hit: result.hit, wins: result.wins, combo: combo + 1, lightning, multiplier, win, total, stops: first.stops, scene };
      steps.push(snapshot);
      if (!result.raw) break;
      drop(board, gold, result.hit, tableId, combo, dropIndex); combo++;
    }
    const scatter = board.flat().filter((symbol) => symbol === C1).length;
    return { scene, board: clone(board), gold: clone(gold), stops: first.stops, steps, total, scatter, maxMultiplier: Math.max(...steps.map((step) => step.multiplier)) };
  }

  function freeAward(scatter) { return Number(Box.free_spin_awards?.[scatter] || (scatter >= 3 ? 10 + (scatter - 3) * 2 : 0)); }

  function symbolMarkup(symbol, isGold) {
    if (symbol === 99) return "";
    const code = CODE[symbol] || `S${symbol}`;
    return `<div class="symbol-wrap"><span class="h015-glyph">${code}</span></div>`;
  }

  function renderBoard(board, gold = [], hit = [], options = {}) {
    el.board.style.gridTemplateColumns = `repeat(${REELS}, var(--cell-size, 74px))`;
    el.board.innerHTML = "";
    for (let row = 0; row < ROWS; row++) for (let reel = 0; reel < REELS; reel++) {
      const cell = document.createElement("div"); const active = Box.score_area[row][reel];
      const code = CODE[board[row][reel]] || `S${board[row][reel]}`;
      const symbolClass = `symbol-${code.toLowerCase().replace(/[^a-z0-9_-]/g, "")}`;
      cell.className = `cell ${symbolClass}${gold[row]?.[reel] ? " gold" : ""}${hit[row]?.[reel] ? " hit" : ""}${options.spinning ? " reel-spin" : ""}${active ? "" : " peek-row"}`;
      if (!active) cell.style.visibility = "hidden";
      cell.innerHTML = symbolMarkup(board[row][reel], gold[row]?.[reel]); el.board.appendChild(cell);
    }
  }

  function renderRng(stops = []) { el.rngList.innerHTML = stops.map((stop, i) => `<span class="rng-chip">R${i + 1}: ${stop}</span>`).join(""); }
  function renderWins(step) {
    el.lineList.innerHTML = step.wins.length ? step.wins.map((win) => `<div>${CODE[win.symbol]} · ${win.length} reels · ${win.ways} ways · ${format(win.unit * win.ways)}</div>`).join("") : `<div>${text("noWin")}</div>`;
    el.spinResultList.innerHTML = `<div>${text("cascade")} ${step.combo} · +${step.lightning} · x${step.multiplier} · ${format(step.win)}</div>`;
  }
  function showSnapshot(index, syncMultiplier = true) {
    if (!state.snapshots.length) return;
    state.snapshotIndex = Math.max(0, Math.min(index, state.snapshots.length - 1)); const step = state.snapshots[state.snapshotIndex];
    renderBoard(step.board, step.gold, step.hit); renderRng(step.stops); renderWins(step);
    el.carryMultiValue.textContent = step.combo;
    if (syncMultiplier) renderMultiplierTrack(multiplierIndex(step.multiplier));
    el.previousStepBtn.disabled = state.snapshotIndex <= 0; el.nextStepBtn.disabled = state.snapshotIndex >= state.snapshots.length - 1;
  }
  function addLog(message) {
    state.log.unshift(`${new Date().toLocaleTimeString()}  ${message}`); state.log = state.log.slice(0, 80);
    el.liveLogBody.innerHTML = state.log.map((item) => `<div>${item}</div>`).join("");
  }

  function updateStats() {
    el.balanceValue.textContent = format(state.balance); el.betValue.textContent = formatBet(activeBet()); el.winValue.textContent = format(state.lastWin);
    el.roundCountValue.textContent = format(state.rounds); el.rtpValue.textContent = state.totalBet ? `${(state.totalWin / state.totalBet * 100).toFixed(2)}%` : "0.00%";
    el.hitRateValue.textContent = state.rounds ? `${(state.hitRounds / state.rounds * 100).toFixed(2)}%` : "0.00%";
    el.fgTriggerValue.textContent = state.normalRounds ? `${(state.naturalFg / state.normalRounds * 100).toFixed(3)}% (${state.naturalFg})` : "0.000% (0)";
    el.maxMultiplierValue.textContent = `x${state.maxMultiplier}`; el.betBtn.textContent = `${text("bet")} ${formatBet(activeBet())}`;
    el.fgLeftPill.classList.toggle("hidden", state.fg.remaining <= 0); el.fgLeftValue.textContent = `${state.fg.remaining}/${state.fg.total}`;
    el.modeText.textContent = state.fg.remaining ? text("free") : text("base"); el.spinBtn.textContent = state.fg.remaining ? text("nextFg") : text("spin");
  }

  async function animateReels(spin) {
    const initial = spin.steps[0];
    if (!initial) return;
    const frames = Math.max(2, Math.round(8 / Number(el.speedRange.value || 1)));
    for (let frame = 0; frame < frames; frame++) {
      const rollingBoard = clone(initial.board);
      const rollingGold = clone(initial.gold);
      for (let reel = 0; reel < REELS; reel++) {
        const activeRows = [];
        for (let row = 0; row < ROWS; row++) if (Box.score_area[row][reel]) activeRows.push(row);
        const offset = (frames - frame + reel) % activeRows.length;
        for (let position = 0; position < activeRows.length; position++) {
          const targetRow = activeRows[position];
          const sourceRow = activeRows[(position + offset) % activeRows.length];
          rollingBoard[targetRow][reel] = initial.board[sourceRow][reel];
          rollingGold[targetRow][reel] = initial.gold[sourceRow][reel];
        }
      }
      renderBoard(rollingBoard, rollingGold, [], { spinning: true });
      await new Promise((resolve) => setTimeout(resolve, 55));
    }
  }

  async function animateSpin(spin) {
    state.snapshots = spin.steps; state.snapshotIndex = -1;
    const startIndex = spin.scene === "FG" ? Math.min(3, MULTIPLIERS.length - 1) : 0;
    renderMultiplierTrack(startIndex);
    el.carryMultiValue.textContent = "0";
    await animateReels(spin);
    if (spin.steps[0]) {
      renderBoard(spin.steps[0].board, spin.steps[0].gold);
      await delay();
    }
    for (let i = 0; i < spin.steps.length; i++) {
      showSnapshot(i, false);
      await rollMultiplierTo(spin.steps[i].multiplier);
      await delay();
    }
    renderBoard(spin.board, spin.gold); renderRng(spin.stops);
  }

  async function playFreeSpin() {
    const spin = simulateScene("FG", MODE_NORMAL); await animateSpin(spin);
    state.fg.remaining--; state.fg.played++; state.lastWin = spin.total; state.totalWin += spin.total;
    if (spin.scatter >= 3 && state.fg.played < Box.max_spin_free_game) {
      const award = Math.min(freeAward(spin.scatter), Box.max_spin_free_game - state.fg.played - state.fg.remaining);
      state.fg.remaining += award; state.fg.total += award; addLog(`${text("retrigger")} +${award}`);
    }
    state.maxMultiplier = Math.max(state.maxMultiplier, spin.maxMultiplier); addLog(`FG ${state.fg.played} · ${format(spin.total)}`);
    el.messageBar.textContent = `FG ${state.fg.played}/${state.fg.total} · ${format(spin.total)}`;
  }

  async function playPaid(mode) {
    const cost = coinIn(mode);
    if (state.balance < cost) throw new Error(text("insufficient"));
    state.balance -= cost; state.totalBet += cost; state.rounds++; if (mode === MODE_NORMAL) state.normalRounds++;
    const force = mode === MODE_BUY || el.forceFgInput.checked;
    if (mode === MODE_BUY) el.messageBar.textContent = text("buyStart");
    const spin = simulateScene("BG", mode, force); await animateSpin(spin);
    state.lastWin = spin.total; state.totalWin += spin.total; state.balance += spin.total;
    if (spin.total > 0) state.hitRounds++;
    state.maxMultiplier = Math.max(state.maxMultiplier, spin.maxMultiplier);
    if (spin.scatter >= 3) {
      const award = Math.min(freeAward(spin.scatter), Box.max_spin_free_game);
      state.fg = { remaining: award, total: award, played: 0 };
      if (mode === MODE_NORMAL) state.naturalFg++;
      addLog(`${text("triggered")} · ${spin.scatter} C1 · ${award} FG`);
    }
    addLog(`${mode === MODE_BUY ? "Buy Feature" : "BG"} · ${format(spin.total)}`);
    el.messageBar.textContent = `${spin.scene} ${text("complete")} · ${format(spin.total)}${state.fg.remaining ? ` · ${text("triggered")}` : ""}`;
  }

  async function play(mode = MODE_NORMAL) {
    if (state.busy) return; state.busy = true; updateControls();
    try { if (state.fg.remaining) await playFreeSpin(); else await playPaid(mode); }
    catch (error) { el.messageBar.textContent = error.message; addLog(`Error · ${error.message}`); }
    finally { state.busy = false; updateStats(); updateControls(); }
  }

  async function autoLoop() {
    state.auto = !state.auto; updateControls();
    while (state.auto) { await play(MODE_NORMAL); if (state.balance < coinIn()) state.auto = false; }
    updateControls();
  }

  function updateControls() {
    el.spinBtn.disabled = state.busy; el.buyFeatureBtn.disabled = state.busy || state.fg.remaining > 0;
    el.autoBtn.textContent = state.auto ? text("stop") : text("auto"); el.betMinusBtn.disabled = state.busy || state.betIndex === 0;
    el.betPlusBtn.disabled = state.busy || state.betIndex === BET_LEVELS.length - 1;
  }

  function applyLanguage(logChange = false) {
    document.documentElement.lang = state.language === "zh" ? "zh-Hant" : "en"; el.languageSelect.value = state.language;
    try { localStorage.setItem(STORAGE_KEY, state.language); } catch (_) {}
    el.gameName.textContent = text("game"); el.modeText.textContent = state.fg.remaining ? text("free") : text("base");
    document.querySelector("#simulation-stats h3").textContent = text("stats");
    const statLabels = document.querySelectorAll("#simulation-stats .s-label"); [text("rounds"), "RTP", text("hit"), "FG Trigger", text("maxMult")].forEach((v, i) => { if (statLabels[i]) statLabels[i].textContent = v; });
    const creditLabels = document.querySelectorAll("#credit-bar .i-label"); [text("credit"), text("bet"), text("win")].forEach((v, i) => { if (creditLabels[i]) creditLabels[i].textContent = v; });
    document.querySelector("#play-panel .zone-label").textContent = text("play"); document.querySelector("#bet-mode-panel .zone-label").textContent = text("betMode");
    el.normalBetBtn.textContent = text("normal"); el.buyFeatureBtn.textContent = text("buy");
    document.querySelector("#settings-wrap .setting-header").textContent = text("setting");
    el.debugModeInput.parentElement.lastChild.textContent = ` ${text("debug")}`; el.helpBtn.textContent = text("help"); el.resetBtn.textContent = text("reset");
    el.clearLogBtn.textContent = text("clear"); el.previousStepBtn.textContent = text("previous"); el.nextStepBtn.textContent = text("next");
    el.reelRngInput.placeholder = text("rngPlaceholder"); el.closeHelpBtn.textContent = text("close"); $("helpDialogTitle").textContent = text("helpTitle");
    document.querySelector(".footer-note").textContent = text("footer");
    document.querySelector('label[for="languageSelect"] span').textContent = text("language");
    document.querySelector('label[for="reelRngInput"]').childNodes[0].textContent = `${text("reelRng")} `;
    document.querySelector("#set-rng-panel .zone-label").textContent = text("setRng");
    el.cardRangeSelect.closest("label").style.display = "none";
    if (!state.lastSpin && !logChange) el.messageBar.textContent = text("ready");
    if (logChange) { el.messageBar.textContent = text("languageChanged"); addLog(text("languageChanged")); }
    updateStats(); updateControls(); if (el.helpDialog.open && state.helpMarkdown) renderHelp(state.helpMarkdown);
  }

  function renderHelp(markdown) {
    const lines = markdown.split(/\r?\n/); let html = ""; let inTable = false; let sectionOpen = false;
    const closeTable = () => { if (inTable) { html += "</div>"; inTable = false; } };
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (/^## /.test(line)) { closeTable(); if (sectionOpen) html += "</section>"; html += `<section class="help-section"><h3 class="help-section-title">${line.slice(3)}</h3>`; sectionOpen = true; }
      else if (/^### /.test(line)) { closeTable(); html += `<h4 class="help-group-title">${line.slice(4)}</h4>`; }
      else if (line.startsWith("|")) {
        const cells = line.split("|").slice(1, -1).map((v) => v.trim());
        if (cells.every((v) => /^:?-+:?$/.test(v))) continue;
        if (!inTable) { html += '<div class="help-payout-grid">'; inTable = true; }
        if (cells[0] === "Item" || cells[0] === "符号") continue;
        const value = cells.length === 3 ? (state.language === "zh" ? cells[1] : cells[2]) : cells.join(" · ");
        if (value) html += `<div class="help-payout-item">${value.replace(/\[([^\]]+)\]/g, "<b>$1</b>")}</div>`;
      } else if (line === "---") closeTable();
    }
    closeTable(); if (sectionOpen) html += "</section>"; el.helpContent.innerHTML = html || `<div class="help-load-error">${text("loadFail")}</div>`;
  }

  async function loadHelp() {
    el.helpContent.innerHTML = `<div class="help-loading">${text("loading")}</div>`; let markdown = "";
    try { const response = await fetch(HELP_PATH, { cache: "no-store" }); if (response.ok) markdown = await response.text(); } catch (_) {}
    if (!markdown) {
      try { markdown = el.helpSourceFrame.contentDocument?.body?.innerText || ""; } catch (_) {}
    }
    if (!markdown) markdown = document.getElementById("embeddedH015GameHelpMarkdown")?.textContent?.trim() || "";
    state.helpMarkdown = markdown; renderHelp(markdown);
  }

  function setDebug(enabled) {
    state.debug = enabled; document.querySelectorAll(".debug-hidden").forEach((node) => node.classList.toggle("debug-hidden", !enabled));
    document.querySelectorAll(".debug-only").forEach((node) => node.style.display = enabled ? "" : "none");
    document.querySelector("#controls").classList.toggle("debug-off", !enabled);
  }

  function reset() {
    state.balance = 10000; state.busy = false; state.auto = false; state.fg = { remaining: 0, total: 0, played: 0 };
    state.rounds = state.normalRounds = state.totalBet = state.totalWin = state.hitRounds = state.naturalFg = state.lastWin = 0;
    state.maxMultiplier = 1; state.snapshots = []; state.snapshotIndex = -1; state.log = [];
    el.liveLogBody.innerHTML = el.lineList.innerHTML = el.spinResultList.innerHTML = el.rngList.innerHTML = "";
    const initial = generateBoard(0); renderBoard(initial.board, normalizeGold(initial.board)); renderMultiplierTrack(0); el.messageBar.textContent = text("resetDone"); updateStats(); updateControls();
  }

  function buildBetMenu() {
    el.betMenu.innerHTML = BET_LEVELS.map((v, i) => `<button type="button" data-index="${i}">${formatBet(v)}</button>`).join("");
    el.betMenu.querySelectorAll("button").forEach((button) => button.addEventListener("click", () => { state.betIndex = Number(button.dataset.index); el.betMenu.classList.add("hidden"); updateStats(); }));
  }

  el.spinBtn.addEventListener("click", () => play(MODE_NORMAL)); el.buyFeatureBtn.addEventListener("click", () => play(MODE_BUY)); el.autoBtn.addEventListener("click", autoLoop);
  el.betMinusBtn.addEventListener("click", () => { state.betIndex = Math.max(0, state.betIndex - 1); updateStats(); });
  el.betPlusBtn.addEventListener("click", () => { state.betIndex = Math.min(BET_LEVELS.length - 1, state.betIndex + 1); updateStats(); });
  el.betBtn.addEventListener("click", () => el.betMenu.classList.toggle("hidden")); el.speedRange.addEventListener("input", () => { el.speedValue.textContent = `x${el.speedRange.value}`; });
  el.debugModeInput.addEventListener("change", () => setDebug(el.debugModeInput.checked));
  el.languageSelect.addEventListener("change", () => { state.language = el.languageSelect.value === "zh" ? "zh" : "en"; applyLanguage(true); });
  el.helpBtn.addEventListener("click", () => { el.helpDialog.showModal(); loadHelp(); }); el.closeHelpBtn.addEventListener("click", () => el.helpDialog.close());
  el.helpDialog.addEventListener("click", (event) => { if (event.target === el.helpDialog) el.helpDialog.close(); });
  el.helpSourceFrame.addEventListener("load", () => { if (el.helpDialog.open && !state.helpMarkdown) loadHelp(); });
  el.resetBtn.addEventListener("click", reset); el.clearLogBtn.addEventListener("click", () => { state.log = []; el.liveLogBody.innerHTML = ""; });
  el.setRngResetBtn.addEventListener("click", () => { el.reelRngInput.value = ""; el.forceFgInput.checked = false; });
  el.previousStepBtn.addEventListener("click", () => showSnapshot(state.snapshotIndex - 1)); el.nextStepBtn.addEventListener("click", () => showSnapshot(state.snapshotIndex + 1));

  document.title = `${Box.game_id} ${Box.english_name} — Demo`; el.gameId.textContent = Box.game_id; el.configSelect.disabled = true; el.configSelect.title = text("configFixed");
  buildBetMenu(); setDebug(false); const initial = generateBoard(0); const initialGold = normalizeGold(initial.board); renderBoard(initial.board, initialGold); renderMultiplierTrack(0); renderRng(initial.stops); applyLanguage();
})();
