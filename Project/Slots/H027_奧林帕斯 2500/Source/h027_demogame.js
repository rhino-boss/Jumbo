(() => {
  "use strict";

  const Box = data;
  const DENOM = 0.002;
  const INITIAL_BALANCE = 10000;
  const BET_OPTIONS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 30, 40, 60, 100, 200, 300, 600, 1000, 1500];
  const MODE_NORMAL = Box.mode_normalbet;
  const MODE_EXTRA = Box.mode_extrabet;
  const MODE_BUY = Box.mode_featurebuy;
  const WW = Box.symbol_codes.indexOf("WW");
  const C1 = Box.symbol_codes.indexOf("C1");
  const C2 = Box.symbol_codes.indexOf("C2");
  const PROFILE_NAMES = {
    [MODE_NORMAL]: "normal",
    [MODE_EXTRA]: "normal",
    [MODE_BUY]: "featurebuy"
  };
  const LANGUAGE_STORAGE_KEY = "slotDemoLanguage";
  const UI_TEXT = {
    en: {
      gameName: "Olympus 2500", baseGame: "Base Game", freeGame: "Free Game", buyFeature: "Buy Feature",
      superFeature: "Extra Bet", cascade: "Cascade", multiplier: "Mult", fgLeft: "FG Left", credit: "Credit",
      bet: "Bet", win: "Win", stats: "Simulation Stats", rounds: "Total Rounds", hitRate: "Hit Rate",
      maxMultiplier: "Max Multiplier", play: "Play", spin: "Spin", auto: "Auto", stop: "Stop", speed: "Speed",
      betMode: "Bet Mode", normalBet: "Normal Bet", debugMode: "Debug Mode", forceFg: "Force FG", setting: "Setting",
      language: "Language", help: "Help", reset: "Reset", reelRng: "Reel RNG", spinResult: "Spin Result",
      clusterWins: "Cluster Wins", clear: "Clear", close: "Close", loading: "Loading game rules...",
      helpTitle: "Game Help", ready: "Ready — press Spin", noWin: "No cluster win", pay: "Pay"
    },
    zh: {
      gameName: "奧林帕斯 2500", baseGame: "基礎遊戲", freeGame: "免費遊戲", buyFeature: "購買特色",
      superFeature: "額外押注", cascade: "連消", multiplier: "倍數", fgLeft: "FG 剩餘", credit: "餘額",
      bet: "押注", win: "得分", stats: "模擬統計", rounds: "總局數", hitRate: "中獎率",
      maxMultiplier: "最高倍數", play: "遊戲", spin: "Spin", auto: "自動", stop: "停止", speed: "速度",
      betMode: "押注模式", normalBet: "一般押注", debugMode: "除錯模式", forceFg: "強制 FG", setting: "設定",
      language: "語言", help: "Help", reset: "重置", reelRng: "輪帶 RNG", spinResult: "Spin 結果",
      clusterWins: "Cluster 得獎", clear: "清除", close: "關閉", loading: "正在載入遊戲規則…",
      helpTitle: "遊戲 Help", ready: "準備完成 — 請按 Spin", noWin: "沒有 Cluster 得獎", pay: "得分"
    }
  };
  function savedLanguage() {
    try { return localStorage.getItem(LANGUAGE_STORAGE_KEY) === "zh" ? "zh" : "en"; } catch (_) { return "en"; }
  }
  const state = {
    language: savedLanguage(),
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
  el.language = byId("languageSelect");
  el.helpContent = byId("helpContent");
  el.helpFrame = byId("helpFrame");

  const t = (key) => UI_TEXT[state.language][key] || UI_TEXT.en[key] || key;
  const tr = (english, chinese) => state.language === "zh" ? chinese : english;

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
      : state.selectedMode === MODE_EXTRA
        ? Box.extrabet
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
        let offset = row;
        let symbol = strip.symbols[(start + offset) % length][reel];
        while (symbol === WW && offset < length + Box.window_size) {
          offset += 1;
          symbol = strip.symbols[(start + offset) % length][reel];
        }
        board[row][reel] = symbol;
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

  function applyCascade(spin, wins, scene, c2Mode) {
    const winningSymbols = new Set(wins.map((win) => win.symbol));
    const strip = Box.strips[spin.tableId];

    for (let reel = 0; reel < Box.reel_num; reel += 1) {
      const kept = [];
      const keptWild = [];
      const keptC2Values = [];
      let hasScatter = false;
      for (let row = Box.window_size - 1; row >= 0; row -= 1) {
        const symbol = spin.board[row][reel];
        if (symbol === C1) hasScatter = true;
        if (!winningSymbols.has(symbol)) {
          kept.push(symbol);
          keptWild.push(spin.fromWild[row][reel]);
          keptC2Values.push(symbol === C2 ? spin.c2Values[row][reel] : 0);
        }
      }

      let outputRow = Box.window_size - 1;
      for (let index = 0; index < kept.length; index += 1) {
        spin.board[outputRow][reel] = kept[index];
        spin.fromWild[outputRow][reel] = keptWild[index];
        spin.c2Values[outputRow][reel] = keptC2Values[index];
        outputRow -= 1;
      }

      const length = strip.reel_lengths[reel];
      while (outputRow >= 0) {
        spin.drops[reel] += 1;
        let stripIndex = (spin.starts[reel] - spin.drops[reel] + length) % length;
        let symbol = strip.symbols[stripIndex][reel];
        while (symbol === WW) {
          spin.drops[reel] += 1;
          stripIndex = (spin.starts[reel] - spin.drops[reel] + length) % length;
          symbol = strip.symbols[stripIndex][reel];
        }
        if (symbol === C1 && hasScatter) {
          spin.drops[reel] += 1;
          stripIndex = (spin.starts[reel] - spin.drops[reel] + length) % length;
          symbol = strip.symbols[stripIndex][reel];
        }
        if (symbol === C1) hasScatter = true;
        spin.board[outputRow][reel] = symbol;
        spin.fromWild[outputRow][reel] = false;
        spin.c2Values[outputRow][reel] = symbol === C2 ? drawC2Value(scene, false, c2Mode) : 0;
        outputRow -= 1;
      }
    }

    // Every surviving C2 advances one level after each winning cascade.
    for (let row = 0; row < Box.window_size; row += 1) {
      for (let reel = 0; reel < Box.reel_num; reel += 1) {
        if (spin.board[row][reel] !== C2) continue;
        const current = spin.c2Values[row][reel];
        const level = Box.c2_multiplier_levels.indexOf(current);
        if (level >= 0 && level < Box.c2_multiplier_levels.length - 1) {
          spin.c2Values[row][reel] = Box.c2_multiplier_levels[level + 1];
        }
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

  function chooseC2Mode(scene) {
    const profile = currentProfile();
    const modeWeights = profile.c2_mode_weights[scene === "FG" ? "free" : "base"];
    return pickWeighted(modeWeights);
  }

  function initializeC2Values(spin, scene, c2Mode) {
    spin.c2Values = Array.from({ length: Box.window_size }, () => Array(Box.reel_num).fill(0));
    for (let row = 0; row < Box.window_size; row += 1) {
      for (let reel = 0; reel < Box.reel_num; reel += 1) {
        if (spin.board[row][reel] === C2) spin.c2Values[row][reel] = drawC2Value(scene, false, c2Mode);
      }
    }
  }

  function summarizeC2Values(spin, c2Mode) {
    let total = 0;
    let count = 0;
    for (let row = 0; row < Box.window_size; row += 1) {
      for (let reel = 0; reel < Box.reel_num; reel += 1) {
        if (spin.board[row][reel] !== C2) continue;
        const value = spin.c2Values[row][reel];
        total += value;
        count += 1;
      }
    }
    return { values: clone(spin.c2Values), total, count, mode: c2Mode };
  }

  function scatterPay(count) {
    if (count < 4 || count > 6) return 0;
    return (Box.pay_table[C1][count - 4] || 0) * betMultiplier();
  }

  function playSpin(tableId, scene, carriedMultiplier = 0, forcedStops = null) {
    const spin = generateBoard(tableId, forcedStops);
    const c2Mode = chooseC2Mode(scene);
    initializeC2Values(spin, scene, c2Mode);
    const initialBoard = clone(spin.board);
    const initialC2Values = clone(spin.c2Values);
    const steps = [];
    let rawPay = 0;

    for (let index = 0; index < 100; index += 1) {
      const evaluated = evaluateClusters(spin.board);
      if (!evaluated.wins.length) break;
      const before = clone(spin.board);
      const beforeC2Values = clone(spin.c2Values);
      rawPay += evaluated.pay;
      applyCascade(spin, evaluated.wins, scene, c2Mode);
      steps.push({
        cascadeIndex: index + 1,
        before,
        after: clone(spin.board),
        beforeC2Values,
        afterC2Values: clone(spin.c2Values),
        hitPositions: evaluated.hitPositions,
        wins: evaluated.wins,
        pay: evaluated.pay
      });
    }

    const c2 = summarizeC2Values(spin, c2Mode);
    const scatterCount = spin.board.flat().filter((symbol) => symbol === C1).length;
    const scatterWin = scatterPay(scatterCount);
    const effectiveMultiplier = scene === "FG" ? carriedMultiplier + c2.total : c2.total;
    const finalPay = rawPay * (effectiveMultiplier || 1) + scatterWin;
    return {
      scene,
      tableId,
      tableName: Box.strip_names[tableId],
      initialBoard,
      initialC2Values,
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
      const selectedTable = tableIndex(freeTable.names[index]);
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
    const clearedSet = new Set((options.clearedPositions || []).map(([row, reel]) => `${row}-${reel}`));
    el.board.innerHTML = "";
    board.forEach((row, rowIndex) => row.forEach((cell, reelIndex) => {
      const node = document.createElement("div");
      const dropMotion = options.dropMotion?.[`${rowIndex}-${reelIndex}`];
      const special = cell.code === "C1" ? "h019-scatter" : cell.code === "C2" ? "h019-c2" : "";
      const symbolClass = `symbol-${cell.code.toLowerCase().replace(/[^a-z0-9_-]/g, "")}`;
      node.className = `cell ${symbolClass} ${special} ${hitSet.has(`${rowIndex}-${reelIndex}`) ? "hit" : ""} ${clearedSet.has(`${rowIndex}-${reelIndex}`) ? "symbol-cleared" : ""} ${dropMotion?.type === "new" ? "symbol-drop" : dropMotion?.type === "settle" ? "symbol-settle" : ""} ${options.spinning ? "reel-spin" : ""}`;
      if (dropMotion) {
        node.style.setProperty("--drop-start", `${-dropMotion.rows * 105}%`);
        node.style.setProperty("--drop-duration", `${Math.max(320, 640 / state.speed) / 2}ms`);
        node.style.setProperty("--drop-delay", "0ms");
      }
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

  async function animateReels(spin) {
    const frames = Math.max(2, Math.round(8 / state.speed));
    for (let frame = 0; frame < frames; frame += 1) {
      const rollingBoard = Array.from({ length: Box.window_size }, (_, row) =>
        Array.from({ length: Box.reel_num }, (_, reel) => {
          const offset = (frames - frame + reel) % Box.window_size;
          const sourceRow = (row + offset) % Box.window_size;
          return symbolCell(spin.initialBoard[sourceRow][reel], spin.initialC2Values[sourceRow][reel]);
        })
      );
      renderBoard(rollingBoard, { spinning: true });
      await sleep(55);
    }
  }

  function updateFeatureBar(spin = null) {
    const inFg = spin?.scene === "FG" || Boolean(state.pendingFg);
    document.body.classList.toggle("fg-mode", inFg);
    setText(el.mode, inFg ? t("freeGame") : state.selectedMode === MODE_BUY ? t("buyFeature") : state.selectedMode === MODE_EXTRA ? t("superFeature") : t("baseGame"));
    setText(el.cascade, String(spin?.steps.length || 0));
    const multiplier = inFg ? state.pendingFg?.carry || 0 : spin?.effectiveMultiplier || 0;
    setText(el.multiplier, `x${multiplier || 1}`);
    el.fgPill.classList.toggle("hidden", !state.pendingFg);
    if (state.pendingFg) setText(el.fgLeft, `${state.pendingFg.queue.length}/${state.pendingFg.total}`);
    setText(el.featureStatus, state.pendingFg ? `${t("freeGame")} ${t("win")} ${money(state.pendingFg.win)}` : "");
  }

  function renderClusterWins(spin) {
    el.lineList.innerHTML = "";
    const allWins = spin.steps.flatMap((step) => step.wins.map((win) => ({ ...win, cascadeIndex: step.cascadeIndex })));
    if (!allWins.length) {
      el.lineList.innerHTML = `<div class="line-row"><span>${t("noWin")}</span><span>${t("pay")} 0.00</span></div>`;
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
    state.snapshots = [{ label: "Initial", board: boardCells(spin.initialBoard, spin.initialC2Values), hits: [] }];
    spin.steps.forEach((step) => {
      state.snapshots.push({ label: `Cascade ${step.cascadeIndex} win`, board: boardCells(step.before, step.beforeC2Values), hits: step.hitPositions });
      state.snapshots.push({ label: `Cascade ${step.cascadeIndex} drop`, board: boardCells(step.after, step.afterC2Values), hits: [] });
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
    setText(el.betButton, `${t("bet")} ${money(betMoney())}`);
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
    el.buy.classList.toggle("is-active", state.selectedMode === MODE_EXTRA);
    el.super.classList.toggle("is-active", state.selectedMode === MODE_BUY);
    setText(el.auto, state.auto ? t("stop") : t("auto"));
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
    await animateReels(spin);
    renderBoard(boardCells(spin.initialBoard, spin.initialC2Values));
    updateFeatureBar({ ...spin, steps: [] });
    writeMessage(tr(`${spin.scene} | ${spin.tableName} | Reel stop`, `${spin.scene} | ${spin.tableName} | 停輪`));
    await sleep(260);

    for (const step of spin.steps) {
      renderBoard(boardCells(step.before, step.beforeC2Values), { hitPositions: step.hitPositions });
      setText(el.cascade, String(step.cascadeIndex));
      writeMessage(tr(`Cascade ${step.cascadeIndex} | Pay ${money(toMoney(step.pay))}`, `連消 ${step.cascadeIndex} | 得分 ${money(toMoney(step.pay))}`), "win");
      await sleep(360);
      renderBoard(boardCells(step.before, step.beforeC2Values), { clearedPositions: step.hitPositions });
      await sleep(180);
      const dropMotion = window.slotBuildDropMotion?.(step.before.length, step.before[0].length, step.hitPositions) || {};
      renderBoard(boardCells(step.after, step.afterC2Values), { dropMotion });
      await sleep((Math.max(320, 640 / state.speed) / 2 + 180) * state.speed);
    }

    renderBoard(boardCells(spin.finalBoard, spin.c2.values));
    updateFeatureBar(spin);
    writeMessage(tr(`Final ${money(toMoney(spin.finalPay))} | C1 ${spin.scatterCount} | C2 x${spin.c2.total}`, `最終得分 ${money(toMoney(spin.finalPay))} | C1 ${spin.scatterCount} | C2 x${spin.c2.total}`), spin.finalPay > 0 ? "win" : "");
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
    appendLog(tr(`Free Game triggered | ${queue.length} spins`, `觸發免費遊戲 | ${queue.length} 次`), "result");
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
      appendLog(tr(`FG Retrigger | +${extra.length} spins`, `FG 再觸發 | +${extra.length} 次`), "result");
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
    writeMessage(tr(`Free Game complete | Total ${money(fg.win)}`, `免費遊戲完成 | 總得分 ${money(fg.win)}`), "win");
    updateStats();
  }

  function forcedTriggerSpin(forcedStops = null) {
    return playSpin(tableIndex("BF_Symbol"), "BG", 0, forcedStops);
  }

  function regularSpin(forcedStops = null) {
    if (state.selectedMode !== MODE_EXTRA) return playSpin(chooseBaseTable(), "BG", 0, forcedStops);
    const candidates = [];
    for (let attempt = 0; attempt < Box.extra_fg_probability_multiplier; attempt += 1) {
      const spin = playSpin(chooseBaseTable(), "BG", 0, attempt === 0 ? forcedStops : null);
      candidates.push(spin);
      if (spin.scatterCount >= 4) return spin;
    }
    return candidates[0];
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
      if (state.balance < wager) throw new Error(tr("Insufficient balance", "餘額不足"));
      state.balance -= wager;
      state.totalBet += wager;
      state.roundCount += 1;
      state.lastWin = 0;
      updateStats();

      const forcedStops = parseForcedStops();
      const forceFeature = el.forceFg.checked || state.selectedMode === MODE_BUY;
      const spin = forceFeature ? forcedTriggerSpin(forcedStops) : regularSpin(forcedStops);
      el.forceFg.checked = false;
      await playback(spin);

      state.lastWin = toMoney(spin.finalPay);
      state.balance += state.lastWin;
      state.totalWin += state.lastWin;
      state.maxMultiplier = Math.max(state.maxMultiplier, spin.c2.total);
      const triggered = spin.scatterCount >= 4 || state.selectedMode === MODE_BUY;
      if (triggered) {
        startFreeGame();
        writeMessage(`${state.selectedMode === MODE_BUY ? t("buyFeature") : "C1"} ${tr("entered Free Game", "進入免費遊戲")}`, "win");
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
    if (state.helpMarkdown && el.helpDialog.open) renderHelp(state.helpMarkdown);
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
    writeMessage(t("ready"), "result");
  }

  function parseHelp(markdown) {
    const sections = [];
    let section = null;
    let group = null;
    for (const rawLine of markdown.split(/\r?\n/)) {
      const line = rawLine.trim();
      if (line.startsWith("## ")) {
        section = { fallback: line.slice(3), titleZh: "", titleEn: "", groups: [] };
        sections.push(section);
        group = { titleZh: "", titleEn: "", rules: [], payouts: [] };
        section.groups.push(group);
      } else if (line.startsWith("### ") && section) {
        group = { titleZh: line.slice(4), titleEn: line.slice(4), rules: [], payouts: [] };
        section.groups.push(group);
      } else if (line.startsWith("|") && section && group) {
        const cells = line.split("|").slice(1, -1).map((cell) => cell.trim());
        if (!cells.length || cells.every((cell) => /^:?-+:?$/.test(cell))) continue;
        if (["Item", "Field", "中文欄", "符号"].includes(cells[0])) continue;
        if (cells.length === 3 && cells[0] === "主要標題") {
          section.titleZh = cells[1]; section.titleEn = cells[2];
        } else if (cells.length === 3 && cells[0] === "副標題") {
          group.titleZh = cells[1]; group.titleEn = cells[2];
        } else if (cells.length === 3 && cells[0] === "規則說明") {
          group.rules.push({ zh: cells[1], en: cells[2] });
        } else if (cells.length === 3) {
          group.payouts.push(...cells.filter(Boolean));
        }
      }
    }
    return sections.filter((item) => item.titleZh || item.titleEn || item.groups.some((itemGroup) => itemGroup.rules.length || itemGroup.payouts.length));
  }

  function renderHelp(markdown) {
    el.helpContent.innerHTML = "";
    for (const section of parseHelp(markdown)) {
      const card = document.createElement("section");
      card.className = "help-section";
      const title = document.createElement("h3");
      title.className = "help-section-title";
      title.textContent = state.language === "zh" ? (section.titleZh || section.titleEn || section.fallback) : (section.titleEn || section.titleZh || section.fallback);
      card.appendChild(title);
      if (section.fallback === "PAYTABLE") {
        const note = document.createElement("div");
        note.className = "help-rule";
        note.textContent = tr(
          `Payouts below are shown for the current bet of ${money(betMoney() / DENOM)}.`,
          `以下派彩金額依目前押注 ${money(betMoney() / DENOM)} 顯示。`
        );
        card.appendChild(note);
      }
      for (const group of section.groups) {
        if ((group.titleZh || group.titleEn) && (group.rules.length || group.payouts.length)) {
          const heading = document.createElement("h4");
          heading.className = "help-group-title";
          heading.textContent = state.language === "zh" ? (group.titleZh || group.titleEn) : (group.titleEn || group.titleZh);
          card.appendChild(heading);
        }
        for (const rule of group.rules) {
          const row = document.createElement("div");
          row.className = "help-rule";
          row.textContent = state.language === "zh" ? rule.zh : rule.en;
          card.appendChild(row);
        }
        if (group.payouts.length) {
          const grid = document.createElement("div");
          grid.className = "help-payout-grid";
          for (const payout of group.payouts) {
            const item = document.createElement("div");
            item.className = "help-payout-item";
            item.textContent = payout.replaceAll("[", "").replaceAll("]", "").replace(/(-\s*)([\d.]+)\s*$/, (_, separator, rawValue) => {
              const payoutCredits = Number(rawValue) * betMultiplier();
              return `${separator}${money(payoutCredits)}`;
            });
            grid.appendChild(item);
          }
          card.appendChild(grid);
        }
      }
      el.helpContent.appendChild(card);
    }
    if (!el.helpContent.children.length) el.helpContent.innerHTML = `<div class="help-load-error">${tr("Unable to load game rules.", "無法載入遊戲規則。")}</div>`;
  }

  async function loadHelp() {
    el.helpContent.innerHTML = `<div class="help-loading">${t("loading")}</div>`;
    let markdown = byId("embeddedGameHelpMarkdown")?.textContent?.trim() || "";
    if (!markdown) {
      try { markdown = el.helpFrame.contentDocument?.body?.innerText || ""; } catch (_) {}
    }
    if (!markdown && location.protocol !== "file:") {
      try {
        const response = await fetch("./game_help_draft.md", { cache: "no-store" });
        if (response.ok) markdown = await response.text();
      } catch (_) {}
    }
    state.helpMarkdown = markdown;
    renderHelp(markdown);
  }

  function applyLanguage(showMessage = false) {
    document.documentElement.lang = state.language === "zh" ? "zh-Hant" : "en";
    el.language.value = state.language;
    try { localStorage.setItem(LANGUAGE_STORAGE_KEY, state.language); } catch (_) {}
    setText(byId("gameName"), t("gameName"));
    const creditLabels = document.querySelectorAll("#credit-bar .i-label");
    [t("credit"), t("bet"), t("win")].forEach((value, index) => setText(creditLabels[index], value));
    setText(document.querySelector("#simulation-stats h3"), t("stats"));
    const statLabels = document.querySelectorAll("#simulation-stats .s-label");
    [t("rounds"), "RTP", t("hitRate"), "FG Trigger", t("maxMultiplier")].forEach((value, index) => setText(statLabels[index], value));
    setText(document.querySelector("#play-panel .zone-label"), t("play"));
    setText(document.querySelector("#bet-mode-panel .zone-label"), t("betMode"));
    setText(el.normal, t("normalBet"));
    setText(el.buy, `${t("superFeature")} (${Box.extrabet}x)`);
    setText(el.super, `${t("buyFeature")} (${Box.featurebuy}x)`);
    setText(document.querySelector("#settings-wrap .setting-header"), t("setting"));
    setText(document.querySelector('label[for="languageSelect"] span'), t("language"));
    setText(el.help, t("help")); setText(el.reset, t("reset")); setText(byId("helpDialogTitle"), t("helpTitle")); setText(el.closeHelp, t("close"));
    setText(document.querySelector("#rng-wrap .diagnostic-header"), t("reelRng"));
    setText(byId("log-header"), t("spinResult")); setText(document.querySelector("#log-body .log-subheader"), t("clusterWins")); setText(el.clearLog, t("clear"));
    const debugLabel = document.querySelector('label[for="debugModeInput"]');
    if (debugLabel?.lastChild) debugLabel.lastChild.textContent = ` ${t("debugMode")}`;
    const forceLabel = document.querySelector('label[for="forceFgInput"]');
    if (forceLabel?.lastChild) forceLabel.lastChild.textContent = ` ${t("forceFg")}`;
    const speedLabel = document.querySelector('label[for="speedRange"]');
    if (speedLabel?.firstChild) speedLabel.firstChild.textContent = `${t("speed")} `;
    updateFeatureBar(state.lastSpin); updateStats(); updateControls();
    if (state.helpMarkdown && el.helpDialog.open) renderHelp(state.helpMarkdown);
    if (showMessage) writeMessage(tr("Language changed to English", "語言已切換為中文"), "result");
  }

  el.spin.addEventListener("click", doSpin);
  el.auto.addEventListener("click", () => {
    state.auto = !state.auto;
    if (!state.auto) clearTimeout(state.autoTimer);
    updateControls();
    if (state.auto && !state.busy) doSpin();
  });
  el.normal.addEventListener("click", () => selectMode(MODE_NORMAL));
  el.buy.addEventListener("click", () => selectMode(MODE_EXTRA));
  el.super.addEventListener("click", () => purchaseFeature(MODE_BUY));
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
    writeMessage(tr("Reel RNG reset", "輪帶 RNG 已重置"));
  });
  el.clearLog.addEventListener("click", () => { el.liveLog.innerHTML = ""; });
  el.reset.addEventListener("click", resetSession);
  el.config.addEventListener("change", () => {
    const url = new URL(window.location.href);
    url.searchParams.set("config", el.config.value);
    window.location.href = url.href;
  });
  el.language.addEventListener("change", () => {
    state.language = el.language.value === "zh" ? "zh" : "en";
    applyLanguage(true);
  });
  el.help.addEventListener("click", () => { el.helpDialog.showModal(); loadHelp(); });
  el.closeHelp.addEventListener("click", () => el.helpDialog.close());
  el.helpDialog.addEventListener("click", (event) => {
    if (event.target === el.helpDialog) el.helpDialog.close();
  });
  el.helpFrame.addEventListener("load", () => {
    if (el.helpDialog.open && !state.helpMarkdown) loadHelp();
  });

  byId("gameId").textContent = "H027";
  byId("gameName").textContent = t("gameName");
  el.config.value = H027_ACTIVE_CONFIG;
  el.cardRange.closest("label").firstChild.textContent = "Card BG Range ";
  el.cardRange.disabled = true;
  document.title = `${Box.display_name || "Olympus 2500"} — Demo Game`;
  renderBetMenu();
  renderBoard(sampleBoard());
  updateFeatureBar();
  updateStats();
  updateControls();
  toggleDebug(false);
  applyLanguage();
  appendLog(`${Box.model} loaded | ${Box.excel_version}`, "result");
})();
