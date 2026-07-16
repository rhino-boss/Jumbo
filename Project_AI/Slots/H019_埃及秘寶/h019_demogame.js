(() => {
  "use strict";

  const Box = data;
  const DENOM = 0.002;
  const INITIAL_BALANCE = 10000;
  const BET_OPTIONS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 30, 40, 60, 100, 200, 300, 600, 1000, 1500];
  const MODE_NORMAL = Box.mode_normalbet;
  const MODE_BUY = Box.mode_featurebuy;
  const MODE_SUPER = Box.mode_superfeaturebuy;
  const WW = Box.symbol_codes.indexOf("WW");
  const C1 = Box.symbol_codes.indexOf("C1");
  const C2 = Box.symbol_codes.indexOf("C2");
  const PROFILE_NAMES = {
    [MODE_NORMAL]: "normal",
    [MODE_BUY]: "featurebuy",
    [MODE_SUPER]: "superfeaturebuy"
  };
  const state = {
    balance: INITIAL_BALANCE,
    totalBet: 0,
    totalWin: 0,
    roundCount: 0,
    hitCount: 0,
    fgTriggerCount: 0,
    maxMultiplier: 0,
    betIndex: 0,
    selectedMode: MODE_NORMAL,
    speed: 1,
    busy: false,
    auto: false,
    autoTimer: null,
    lastWin: 0,
    pendingFg: null,
    snapshots: [],
    snapshotIndex: -1,
    lastSpin: null
  };

  const byId = (id) => document.getElementById(id);
  const el = {
    board: byId("board"),
    message: byId("messageBar"),
    mode: byId("modeText"),
    featureStatus: byId("featureStatus"),
    cascade: byId("carryMultiValue"),
    multiplier: byId("spinMultiValue"),
    fgPill: byId("fgLeftPill"),
    fgLeft: byId("fgLeftValue"),
    balance: byId("balanceValue"),
    bet: byId("betValue"),
    win: byId("winValue"),
    rounds: byId("roundCountValue"),
    rtp: byId("rtpValue"),
    hitRate: byId("hitRateValue"),
    fgTriggers: byId("fgTriggerValue"),
    maxMultiplier: byId("maxMultiplierValue"),
    spin: byId("spinBtn"),
    auto: byId("autoBtn"),
    normal: byId("normalBetBtn"),
    buy: byId("extraBetBtn"),
    super: byId("buyFeatureBtn"),
    betButton: byId("betBtn"),
    betMinus: byId("betMinusBtn"),
    betPlus: byId("betPlusBtn"),
    betMenu: byId("betMenu"),
    speed: byId("speedRange"),
    speedValue: byId("speedValue"),
    config: byId("configSelect"),
    debug: byId("debugModeInput"),
    forceFg: byId("forceFgInput"),
    previous: byId("previousStepBtn"),
    next: byId("nextStepBtn"),
    rngInput: byId("reelRngInput"),
    cardRange: byId("cardRangeSelect"),
    rngReset: byId("setRngResetBtn"),
    rngList: byId("rngList"),
    lineList: byId("lineList"),
    resultList: byId("spinResultList"),
    liveLog: byId("liveLogBody"),
    clearLog: byId("clearLogBtn"),
    reset: byId("resetBtn"),
    help: byId("helpBtn"),
    helpDialog: byId("helpDialog"),
    closeHelp: byId("closeHelpBtn")
  };

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, Math.max(18, ms / state.speed)));
  const clone = (value) => JSON.parse(JSON.stringify(value));
  const randomIndex = (length) => Math.floor(Math.random() * length);
  const money = (value) => Number(value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const toMoney = (credit) => Number(credit) * DENOM;

  function setText(node, value) {
    if (node) node.textContent = value;
  }

  function pickWeighted(weights) {
    const safe = weights.map((value) => Math.max(0, Number(value) || 0));
    const total = safe.reduce((sum, value) => sum + value, 0);
    if (total <= 0) return 0;
    let target = Math.random() * total;
    for (let index = 0; index < safe.length; index += 1) {
      target -= safe[index];
      if (target < 0) return index;
    }
    return safe.length - 1;
  }

  function writeMessage(text, type = "") {
    setText(el.message, text);
    el.message.className = `message-bar ${type}`;
    appendLog(text, type === "error" ? "error" : type === "win" ? "result" : "info");
  }

  function appendLog(text, type = "info") {
    if (!el.liveLog) return;
    const line = document.createElement("div");
    line.className = `live-log-line ${type}`;
    const time = new Date().toLocaleTimeString("en-GB", { hour12: false });
    line.textContent = `[${time}] ${text}`;
    el.liveLog.appendChild(line);
    while (el.liveLog.children.length > 500) el.liveLog.firstElementChild.remove();
    el.liveLog.scrollTop = el.liveLog.scrollHeight;
  }

  function currentProfile() {
    return Box.parameter[PROFILE_NAMES[state.selectedMode]];
  }

  function betMoney() {
    return BET_OPTIONS[state.betIndex];
  }

  function betMultiplier() {
    return betMoney() / (Box.default_coin_in * DENOM * Box.normalbet);
  }

  function wagerMoney() {
    const modeCost = state.selectedMode === MODE_BUY
      ? Box.featurebuy
      : state.selectedMode === MODE_SUPER
        ? Box.superfeaturebuy
        : Box.normalbet;
    return betMoney() * modeCost;
  }

  function tableIndex(name) {
    return Box.strip_names.indexOf(name);
  }

  function chooseBaseTable() {
    const profile = currentProfile();
    const selected = pickWeighted(profile.base_reel_weights);
    return tableIndex(profile.base_reel_names[selected]);
  }

  function parseForcedStops() {
    const raw = el.rngInput.value.trim();
    if (!raw) return null;
    const values = raw.split(/\s+/).map(Number);
    if (values.length !== Box.reel_num || values.some((value) => !Number.isInteger(value) || value < 0)) {
      throw new Error(`Reel RNG 請輸入 ${Box.reel_num} 個非負整數，並以空格分隔`);
    }
    return values;
  }

  function generateBoard(tableId, forcedStops = null) {
    const strip = Box.strips[tableId];
    const board = Array.from({ length: Box.window_size }, () => Array(Box.reel_num).fill(0));
    const fromWild = Array.from({ length: Box.window_size }, () => Array(Box.reel_num).fill(false));
    const starts = [];
    const drops = Array(Box.reel_num).fill(0);

    for (let reel = 0; reel < Box.reel_num; reel += 1) {
      const length = strip.reel_lengths[reel];
      const weights = strip.weights.slice(0, length).map((row) => row[reel]);
      const start = forcedStops ? forcedStops[reel] % length : pickWeighted(weights);
      starts.push(start);
      for (let row = 0; row < Box.window_size; row += 1) {
        board[row][reel] = strip.symbols[(start + row) % length][reel];
      }
    }
    return { tableId, board, fromWild, starts, drops };
  }

  function evaluateClusters(board) {
    const flat = board.flat();
    const wildCount = flat.filter((symbol) => symbol === WW).length;
    const wins = [];
    const hitPositions = [];
    let pay = 0;

    for (let symbol = 0; symbol < Box.symbol_codes.length; symbol += 1) {
      if (symbol === WW || symbol === C1 || symbol === C2) continue;
      const count = flat.filter((item) => item === symbol).length + wildCount;
      const payIndex = count >= 12 ? 5 : count >= 10 ? 4 : count >= 8 ? 3 : -1;
      if (payIndex < 0) continue;
      const symbolPay = (Box.pay_table[symbol][payIndex] || 0) * betMultiplier();
      wins.push({ symbol, count, pay: symbolPay });
      pay += symbolPay;
      for (let row = 0; row < Box.window_size; row += 1) {
        for (let reel = 0; reel < Box.reel_num; reel += 1) {
          if (board[row][reel] === symbol || board[row][reel] === WW) hitPositions.push([row, reel]);
        }
      }
    }
    return { wins, hitPositions, pay };
  }

  function applyCascade(spin, wins) {
    const winningSymbols = new Set(wins.map((win) => win.symbol));
    const strip = Box.strips[spin.tableId];

    for (let reel = 0; reel < Box.reel_num; reel += 1) {
      const kept = [];
      const keptWild = [];
      let hasScatter = false;
      for (let row = Box.window_size - 1; row >= 0; row -= 1) {
        const symbol = spin.board[row][reel];
        if (symbol === C1) hasScatter = true;
        if (symbol === WW) {
          kept.push(C2);
          keptWild.push(true);
        } else if (!winningSymbols.has(symbol)) {
          kept.push(symbol);
          keptWild.push(spin.fromWild[row][reel]);
        }
      }

      let outputRow = Box.window_size - 1;
      for (let index = 0; index < kept.length; index += 1) {
        spin.board[outputRow][reel] = kept[index];
        spin.fromWild[outputRow][reel] = keptWild[index];
        outputRow -= 1;
      }

      const length = strip.reel_lengths[reel];
      while (outputRow >= 0) {
        spin.drops[reel] += 1;
        let stripIndex = (spin.starts[reel] - spin.drops[reel] + length) % length;
        let symbol = strip.symbols[stripIndex][reel];
        if (symbol === C1 && hasScatter) {
          spin.drops[reel] += 1;
          stripIndex = (spin.starts[reel] - spin.drops[reel] + length) % length;
          symbol = strip.symbols[stripIndex][reel];
        }
        if (symbol === C1) hasScatter = true;
        spin.board[outputRow][reel] = symbol;
        spin.fromWild[outputRow][reel] = false;
        outputRow -= 1;
      }
    }
  }

  function drawC2Value(scene, cameFromWild, c2Mode) {
    const c2 = currentProfile().c2;
    const key = c2Mode === 1
      ? "super"
      : c2Mode === 2
        ? "ultimate"
        : scene === "FG"
          ? cameFromWild ? "free_wild" : "free_direct"
          : cameFromWild ? "base_wild" : "base_direct";
    return c2.multipliers[pickWeighted(c2.weights[key])] || 0;
  }

  function assignC2Values(spin, scene) {
    const profile = currentProfile();
    const modeWeights = profile.c2_mode_weights[scene === "FG" ? "free" : "base"];
    const c2Mode = pickWeighted(modeWeights);
    const values = Array.from({ length: Box.window_size }, () => Array(Box.reel_num).fill(0));
    let total = 0;
    let count = 0;
    for (let row = 0; row < Box.window_size; row += 1) {
      for (let reel = 0; reel < Box.reel_num; reel += 1) {
        if (spin.board[row][reel] !== C2) continue;
        const value = drawC2Value(scene, spin.fromWild[row][reel], c2Mode);
        values[row][reel] = value;
        total += value;
        count += 1;
      }
    }
    return { values, total, count, mode: c2Mode };
  }

  function scatterPay(count) {
    if (count < 4 || count > 6) return 0;
    return (Box.pay_table[C1][count - 4] || 0) * betMultiplier();
  }

  function playSpin(tableId, scene, carriedMultiplier = 0, forcedStops = null) {
    const spin = generateBoard(tableId, forcedStops);
    const initialBoard = clone(spin.board);
    const steps = [];
    let rawPay = 0;

    for (let index = 0; index < 100; index += 1) {
      const evaluated = evaluateClusters(spin.board);
      if (!evaluated.wins.length) break;
      const before = clone(spin.board);
      rawPay += evaluated.pay;
      applyCascade(spin, evaluated.wins);
      steps.push({
        cascadeIndex: index + 1,
        before,
        after: clone(spin.board),
        hitPositions: evaluated.hitPositions,
        wins: evaluated.wins,
        pay: evaluated.pay
      });
    }

    const c2 = assignC2Values(spin, scene);
    const scatterCount = spin.board.flat().filter((symbol) => symbol === C1).length;
    const scatterWin = scatterPay(scatterCount);
    const effectiveMultiplier = scene === "FG" ? carriedMultiplier + c2.total : c2.total;
    const finalPay = rawPay * (effectiveMultiplier || 1) + scatterWin;
    return {
      scene,
      tableId,
      tableName: Box.strip_names[tableId],
      initialBoard,
      finalBoard: clone(spin.board),
      starts: spin.starts,
      steps,
      c2,
      scatterCount,
      scatterWin,
      rawPay,
      effectiveMultiplier,
      finalPay
    };
  }

  function buildFreeSchedule(kind) {
    const freeTable = currentProfile().free_table;
    const schedule = [];
    freeTable[kind].forEach((count, index) => {
      const selectedTable = state.selectedMode === MODE_SUPER ? 9 + index : tableIndex(freeTable.names[index]);
      for (let repeat = 0; repeat < count; repeat += 1) schedule.push(selectedTable);
    });
    for (let index = schedule.length - 1; index > 0; index -= 1) {
      const selected = randomIndex(index + 1);
      [schedule[index], schedule[selected]] = [schedule[selected], schedule[index]];
    }
    return schedule;
  }

  function symbolCell(symbol, value = 0) {
    const code = Box.symbol_codes[symbol] || "?";
    return { symbol, code, glyph: code, value };
  }

  function boardCells(board, values = null) {
    return board.map((row, rowIndex) => row.map((symbol, reelIndex) => symbolCell(symbol, values?.[rowIndex]?.[reelIndex] || 0)));
  }

  function renderBoard(board, options = {}) {
    const hitSet = new Set((options.hitPositions || []).map(([row, reel]) => `${row}-${reel}`));
    el.board.innerHTML = "";
    board.forEach((row, rowIndex) => row.forEach((cell, reelIndex) => {
      const node = document.createElement("div");
      const special = cell.code === "C1" ? "h019-scatter" : cell.code === "C2" ? "h019-c2" : "";
      const symbolClass = `symbol-${cell.code.toLowerCase().replace(/[^a-z0-9_-]/g, "")}`;
      node.className = `cell ${symbolClass} ${special} ${hitSet.has(`${rowIndex}-${reelIndex}`) ? "hit" : ""} ${options.spinning ? "reel-spin" : ""}`;
      const wrap = document.createElement("div");
      wrap.className = "symbol-wrap";
      const glyph = document.createElement("span");
      glyph.className = "h019-glyph";
      glyph.textContent = cell.glyph;
      wrap.appendChild(glyph);
      node.appendChild(wrap);
      const code = document.createElement("div");
      code.className = "symbol-code";
      code.textContent = cell.code;
      node.appendChild(code);
      if (cell.value > 0) {
        const multiplier = document.createElement("div");
        multiplier.className = "multiplier-badge";
        multiplier.textContent = `x${cell.value}`;
        node.appendChild(multiplier);
      }
      el.board.appendChild(node);
    }));
  }

  function sampleBoard() {
    return Array.from({ length: Box.window_size }, () =>
      Array.from({ length: Box.reel_num }, () => symbolCell(randomIndex(Box.symbol_codes.length)))
    );
  }

  async function animateReels() {
    const frames = Math.max(2, Math.round(8 / state.speed));
    for (let frame = 0; frame < frames; frame += 1) {
      renderBoard(sampleBoard(), { spinning: true });
      await sleep(55);
    }
  }

  function updateFeatureBar(spin = null) {
    const inFg = spin?.scene === "FG" || Boolean(state.pendingFg);
    document.body.classList.toggle("fg-mode", inFg);
    setText(el.mode, inFg ? "Free Game" : state.selectedMode === MODE_BUY ? "Buy Feature" : state.selectedMode === MODE_SUPER ? "Super Feature" : "Base Game");
    setText(el.cascade, String(spin?.steps.length || 0));
    const multiplier = inFg ? state.pendingFg?.carry || 0 : spin?.effectiveMultiplier || 0;
    setText(el.multiplier, `x${multiplier || 1}`);
    el.fgPill.classList.toggle("hidden", !state.pendingFg);
    if (state.pendingFg) setText(el.fgLeft, `${state.pendingFg.queue.length}/${state.pendingFg.total}`);
    setText(el.featureStatus, state.pendingFg ? `FG Win ${money(state.pendingFg.win)}` : "");
  }

  function renderClusterWins(spin) {
    el.lineList.innerHTML = "";
    const allWins = spin.steps.flatMap((step) => step.wins.map((win) => ({ ...win, cascadeIndex: step.cascadeIndex })));
    if (!allWins.length) {
      el.lineList.innerHTML = '<div class="line-row"><span>No cluster win</span><span>Pay 0.00</span></div>';
      return;
    }
    allWins.forEach((win) => {
      const row = document.createElement("div");
      row.className = "line-row";
      row.innerHTML = `<span>C${win.cascadeIndex} | ${Box.symbol_codes[win.symbol]} × ${win.count}</span><span>${money(toMoney(win.pay))}</span>`;
      el.lineList.appendChild(row);
    });
  }

  function renderRng(spin) {
    el.rngList.innerHTML = "";
    const rows = [
      [`Table`, `${spin.tableName} (#${spin.tableId})`],
      [`C2`, `count ${spin.c2.count} | x${spin.c2.total} | mode ${spin.c2.mode}`]
    ];
    spin.starts.forEach((start, index) => rows.push([`R${index + 1}`, `stop ${start}`]));
    rows.forEach(([left, right]) => {
      const row = document.createElement("div");
      row.className = "rng-row";
      row.innerHTML = `<span>${left}</span><span>${right}</span>`;
      el.rngList.appendChild(row);
    });
  }

  function boardText(board) {
    return board.map((row) => row.map((symbol) => Box.symbol_codes[symbol].padStart(2, " ")).join(" ")).join("\n");
  }

  function renderResultStages(spin) {
    el.resultList.innerHTML = "";
    const stages = [{ label: "Initial", board: spin.initialBoard, meta: `${spin.scene} | ${spin.tableName}` }];
    spin.steps.forEach((step) => stages.push({ label: `Cascade ${step.cascadeIndex}`, board: step.after, meta: `Pay ${money(toMoney(step.pay))}` }));
    stages.push({ label: "Final", board: spin.finalBoard, meta: `C1 ${spin.scatterCount} | C2 x${spin.c2.total} | Win ${money(toMoney(spin.finalPay))}` });
    stages.forEach((stage) => {
      const row = document.createElement("div");
      row.className = "spin-result-row";
      row.innerHTML = `<div><strong>${stage.label}</strong><span>${stage.meta}</span></div><pre>${boardText(stage.board)}</pre>`;
      el.resultList.appendChild(row);
    });
  }

  function captureSnapshots(spin) {
    state.snapshots = [{ label: "Initial", board: boardCells(spin.initialBoard), hits: [] }];
    spin.steps.forEach((step) => {
      state.snapshots.push({ label: `Cascade ${step.cascadeIndex} win`, board: boardCells(step.before), hits: step.hitPositions });
      state.snapshots.push({ label: `Cascade ${step.cascadeIndex} drop`, board: boardCells(step.after), hits: [] });
    });
    state.snapshots.push({ label: "Final", board: boardCells(spin.finalBoard, spin.c2.values), hits: [] });
    state.snapshotIndex = state.snapshots.length - 1;
    updateDebugButtons();
  }

  function showSnapshot(index) {
    if (!state.snapshots.length) return;
    state.snapshotIndex = Math.max(0, Math.min(index, state.snapshots.length - 1));
    const snapshot = state.snapshots[state.snapshotIndex];
    renderBoard(snapshot.board, { hitPositions: snapshot.hits });
    writeMessage(`${snapshot.label} | Step ${state.snapshotIndex + 1}/${state.snapshots.length}`);
    updateDebugButtons();
  }

  function updateDebugButtons() {
    const enabled = el.debug.checked && !state.busy && state.snapshots.length > 0;
    el.previous.disabled = !enabled || state.snapshotIndex <= 0;
    el.next.disabled = !enabled || state.snapshotIndex >= state.snapshots.length - 1;
  }

  function updateStats() {
    setText(el.balance, money(state.balance));
    setText(el.bet, money(wagerMoney()));
    setText(el.win, money(state.lastWin));
    setText(el.rounds, String(state.roundCount));
    setText(el.rtp, state.totalBet > 0 ? `${(state.totalWin / state.totalBet * 100).toFixed(2)}%` : "0.00%");
    setText(el.hitRate, state.roundCount > 0 ? `${(state.hitCount / state.roundCount * 100).toFixed(2)}%` : "0.00%");
    setText(el.fgTriggers, String(state.fgTriggerCount));
    setText(el.maxMultiplier, `x${state.maxMultiplier}`);
    setText(el.betButton, `Bet ${money(betMoney())}`);
  }

  function updateControls() {
    const wagerLocked = state.busy || Boolean(state.pendingFg);
    el.normal.disabled = wagerLocked;
    el.buy.disabled = wagerLocked;
    el.super.disabled = wagerLocked;
    el.betMinus.disabled = wagerLocked;
    el.betPlus.disabled = wagerLocked;
    el.betButton.disabled = wagerLocked;
    el.rngInput.disabled = state.busy;
    el.rngReset.disabled = state.busy || !el.rngInput.value.trim();
    el.spin.disabled = state.busy;
    el.normal.classList.toggle("is-active", state.selectedMode === MODE_NORMAL);
    el.buy.classList.remove("is-active");
    el.super.classList.remove("is-active");
    setText(el.auto, state.auto ? "Stop" : "Auto");
    updateDebugButtons();
  }

  function renderBetMenu() {
    el.betMenu.innerHTML = "";
    BET_OPTIONS.forEach((value, index) => {
      const option = document.createElement("button");
      option.type = "button";
      option.textContent = money(value);
      option.className = index === state.betIndex ? "is-active" : "";
      option.addEventListener("click", (event) => {
        event.stopPropagation();
        state.betIndex = index;
        el.betMenu.classList.add("hidden");
        updateStats();
        renderBetMenu();
      });
      el.betMenu.appendChild(option);
    });
  }

  async function playback(spin) {
    await animateReels();
    renderBoard(boardCells(spin.initialBoard));
    updateFeatureBar({ ...spin, steps: [] });
    writeMessage(`${spin.scene} | ${spin.tableName} | Reel stop`);
    await sleep(260);

    for (const step of spin.steps) {
      renderBoard(boardCells(step.before), { hitPositions: step.hitPositions });
      setText(el.cascade, String(step.cascadeIndex));
      writeMessage(`Cascade ${step.cascadeIndex} | Pay ${money(toMoney(step.pay))}`, "win");
      await sleep(360);
      renderBoard(boardCells(step.after));
      await sleep(260);
    }

    renderBoard(boardCells(spin.finalBoard, spin.c2.values));
    updateFeatureBar(spin);
    writeMessage(`Final ${money(toMoney(spin.finalPay))} | C1 ${spin.scatterCount} | C2 x${spin.c2.total}`, spin.finalPay > 0 ? "win" : "");
    renderClusterWins(spin);
    renderRng(spin);
    renderResultStages(spin);
    captureSnapshots(spin);
    state.lastSpin = spin;
  }

  function startFreeGame() {
    const queue = buildFreeSchedule("initial");
    state.pendingFg = { queue, total: queue.length, played: 0, carry: 0, win: 0 };
    state.fgTriggerCount += 1;
    appendLog(`Free Game triggered | ${queue.length} spins`, "result");
    updateFeatureBar();
  }

  async function playFreeSpin() {
    const fg = state.pendingFg;
    if (!fg || !fg.queue.length) return finishFreeGame();
    const tableId = fg.queue.shift();
    const spin = playSpin(tableId, "FG", fg.carry);
    fg.played += 1;
    fg.carry += spin.c2.total;
    fg.win += toMoney(spin.finalPay);
    state.maxMultiplier = Math.max(state.maxMultiplier, fg.carry);

    if (spin.scatterCount >= 3 && fg.total < Box.max_free_spins) {
      const extra = buildFreeSchedule("retrigger").slice(0, Box.max_free_spins - fg.total);
      fg.queue.push(...extra);
      fg.total += extra.length;
      appendLog(`FG Retrigger | +${extra.length} spins`, "result");
    }
    await playback(spin);
    updateStats();
    if (!fg.queue.length) finishFreeGame();
  }

  function finishFreeGame() {
    const fg = state.pendingFg;
    if (!fg) return;
    state.pendingFg = null;
    state.lastWin += fg.win;
    state.balance += fg.win;
    state.totalWin += fg.win;
    if (state.lastWin > 0) state.hitCount += 1;
    state.selectedMode = MODE_NORMAL;
    document.body.classList.remove("fg-mode");
    updateFeatureBar();
    writeMessage(`Free Game complete | Total ${money(fg.win)}`, "win");
    updateStats();
  }

  function forcedTriggerSpin(forcedStops = null) {
    return playSpin(tableIndex("BF_Symbol"), "BG", 0, forcedStops);
  }

  async function doSpin() {
    if (state.busy) return;
    state.busy = true;
    updateControls();
    try {
      if (state.pendingFg) {
        await playFreeSpin();
        return;
      }

      const wager = wagerMoney();
      if (state.balance < wager) throw new Error("Insufficient balance");
      state.balance -= wager;
      state.totalBet += wager;
      state.roundCount += 1;
      state.lastWin = 0;
      updateStats();

      const forcedStops = parseForcedStops();
      const forceFeature = el.forceFg.checked || state.selectedMode !== MODE_NORMAL;
      const tableId = forceFeature ? tableIndex("BF_Symbol") : chooseBaseTable();
      const spin = forceFeature ? forcedTriggerSpin(forcedStops) : playSpin(tableId, "BG", 0, forcedStops);
      el.forceFg.checked = false;
      await playback(spin);

      state.lastWin = toMoney(spin.finalPay);
      state.balance += state.lastWin;
      state.totalWin += state.lastWin;
      state.maxMultiplier = Math.max(state.maxMultiplier, spin.c2.total);
      const triggered = spin.scatterCount >= 4 || state.selectedMode !== MODE_NORMAL;
      if (triggered) {
        startFreeGame();
        writeMessage(`${state.selectedMode === MODE_BUY ? "Buy Feature" : state.selectedMode === MODE_SUPER ? "Super Feature" : "C1"} entered Free Game`, "win");
      } else if (state.lastWin > 0) {
        state.hitCount += 1;
      }
      updateStats();
    } catch (error) {
      state.auto = false;
      if (!state.pendingFg) state.selectedMode = MODE_NORMAL;
      writeMessage(error.message, "error");
    } finally {
      state.busy = false;
      updateControls();
      if (state.auto) state.autoTimer = setTimeout(doSpin, Math.max(80, 650 / state.speed));
    }
  }

  function selectMode(mode) {
    if (state.busy || state.pendingFg) return;
    state.selectedMode = mode;
    updateControls();
    updateStats();
    updateFeatureBar();
    appendLog(`${PROFILE_NAMES[mode]} selected`, "mode");
  }

  function purchaseFeature(mode) {
    if (state.busy || state.pendingFg) return;
    state.selectedMode = mode;
    updateControls();
    updateStats();
    updateFeatureBar();
    appendLog(`${PROFILE_NAMES[mode]} purchased | Spin starts immediately`, "mode");
    doSpin();
  }

  function setBetIndex(index) {
    if (state.busy || state.pendingFg) return;
    state.betIndex = Math.max(0, Math.min(index, BET_OPTIONS.length - 1));
    updateStats();
    renderBetMenu();
  }

  function toggleDebug(enabled) {
    ["play-debug-controls", "set-rng-panel", "rng-wrap", "log-wrap", "live-log-wrap"].forEach((id) => {
      byId(id).classList.toggle("debug-hidden", !enabled);
    });
    byId("controls").classList.toggle("debug-off", !enabled);
    updateDebugButtons();
  }

  function resetSession() {
    if (state.busy) return;
    clearTimeout(state.autoTimer);
    Object.assign(state, {
      balance: INITIAL_BALANCE,
      totalBet: 0,
      totalWin: 0,
      roundCount: 0,
      hitCount: 0,
      fgTriggerCount: 0,
      maxMultiplier: 0,
      lastWin: 0,
      selectedMode: MODE_NORMAL,
      auto: false,
      pendingFg: null,
      snapshots: [],
      snapshotIndex: -1,
      lastSpin: null
    });
    document.body.classList.remove("fg-mode");
    renderBoard(sampleBoard());
    updateFeatureBar();
    updateStats();
    updateControls();
    writeMessage("Ready — press Spin", "result");
  }

  el.spin.addEventListener("click", doSpin);
  el.auto.addEventListener("click", () => {
    state.auto = !state.auto;
    if (!state.auto) clearTimeout(state.autoTimer);
    updateControls();
    if (state.auto && !state.busy) doSpin();
  });
  el.normal.addEventListener("click", () => selectMode(MODE_NORMAL));
  el.buy.addEventListener("click", () => purchaseFeature(MODE_BUY));
  el.super.addEventListener("click", () => purchaseFeature(MODE_SUPER));
  el.betMinus.addEventListener("click", () => setBetIndex(state.betIndex - 1));
  el.betPlus.addEventListener("click", () => setBetIndex(state.betIndex + 1));
  el.betButton.addEventListener("click", (event) => {
    event.stopPropagation();
    el.betMenu.classList.toggle("hidden");
  });
  document.addEventListener("click", (event) => {
    if (!el.betMenu.contains(event.target) && event.target !== el.betButton) el.betMenu.classList.add("hidden");
  });
  document.addEventListener("keydown", (event) => {
    if (event.code === "Space" && !["INPUT", "SELECT", "BUTTON"].includes(event.target.tagName)) {
      event.preventDefault();
      doSpin();
    }
  });
  el.speed.addEventListener("input", () => {
    state.speed = Number(el.speed.value);
    setText(el.speedValue, `x${state.speed}`);
  });
  el.previous.addEventListener("click", () => showSnapshot(state.snapshotIndex - 1));
  el.next.addEventListener("click", () => showSnapshot(state.snapshotIndex + 1));
  el.debug.addEventListener("change", () => toggleDebug(el.debug.checked));
  el.rngInput.addEventListener("input", updateControls);
  el.rngReset.addEventListener("click", () => {
    el.rngInput.value = "";
    updateControls();
    writeMessage("Reel RNG reset");
  });
  el.clearLog.addEventListener("click", () => { el.liveLog.innerHTML = ""; });
  el.reset.addEventListener("click", resetSession);
  el.config.addEventListener("change", () => {
    const url = new URL(window.location.href);
    url.searchParams.set("config", el.config.value);
    window.location.href = url.href;
  });
  el.help.addEventListener("click", () => el.helpDialog.showModal());
  el.closeHelp.addEventListener("click", () => el.helpDialog.close());
  el.helpDialog.addEventListener("click", (event) => {
    if (event.target === el.helpDialog) el.helpDialog.close();
  });

  byId("gameId").textContent = "H019";
  byId("gameName").textContent = Box.game_name_zh;
  el.buy.textContent = `Buy Feature (${Box.featurebuy}x)`;
  el.super.textContent = `Super Feature (${Box.superfeaturebuy}x)`;
  el.config.value = H019_ACTIVE_CONFIG;
  el.cardRange.closest("label").firstChild.textContent = "Card BG Range ";
  el.cardRange.disabled = true;
  document.title = `H019 ${Box.game_name_zh} — Demo`;
  renderBetMenu();
  renderBoard(sampleBoard());
  updateFeatureBar();
  updateStats();
  updateControls();
  toggleDebug(false);
  appendLog(`${Box.model} loaded | ${Box.excel_version}`, "result");
})();
