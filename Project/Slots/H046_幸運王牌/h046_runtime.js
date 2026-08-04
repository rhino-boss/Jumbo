(() => {
  "use strict";

  const cfg = window.H046_CONFIG;
  if (!cfg) throw new Error("H046 config was not loaded.");
  const $ = id => document.getElementById(id);
  const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
  const WW = 0, W2 = 1, C1 = 2;
  const SCORE = [3, 4, 5, 6, 7, 8, 9, 10];
  const CODE = Object.fromEntries(Object.entries(cfg.symbol_names).map(([id, code]) => [Number(id), code]));
  const DISPLAY = {WW:"WILD",WW1:"WILD",WW2:"W2",C1:"C1",M1:"A♠",M2:"K♥",M3:"Q♦",M4:"J♣",A:"A",K:"K",Q:"Q",J:"J",M1G:"A♠",M2G:"K♥",M3G:"Q♦",M4G:"J♣",AG:"A",KG:"K",QG:"Q",JG:"J"};
  const H046_IMAGE_ROOT = "./Source/Image/";
  const SYMBOL_ASSET = {
    WW1:"W1_Symbol.png", WW2:"W2_Symbol.png", C1:"C1_Symbol.png", C2:"C2_Symbol.png",
    M1:"M1_Symbol.png", M2:"M2_Symbol.png", M3:"M3_Symbol.png", M4:"M4_Symbol.png",
    A:"M5_Symbol.png", K:"M6_Symbol.png", Q:"M7_Symbol.png", J:"M8_Symbol.png",
    M1G:"G1_Symbol.png", M2G:"G2_Symbol.png", M3G:"G3_Symbol.png", M4G:"G4_Symbol.png",
    AG:"G5_Symbol.png", KG:"G6_Symbol.png", QG:"G7_Symbol.png", JG:"G8_Symbol.png"
  };
  const BET_LEVELS = [0.20, 0.50, 1, 2, 5, 10];
  const MAX_RETRY = 20000;
  const DROP_SPEED_MULTIPLIER = 3;
  const tables = {};
  const state = {
    balance: 10000, betIndex: 2, busy: false, auto: false, language: "zh",
    rounds: 0, totalBet: 0, totalWin: 0, hitRounds: 0, fgTriggers: 0,
    maxMultiplier: 1, snapshots: [], snapshotIndex: -1, log: [], mode: 0,
    fg: {spins: [], index: 0, total: 0, mode: 0}
  };

  document.head.insertAdjacentHTML("beforeend", `<style>
    #multiplierWindow{grid-template-columns:repeat(4,minmax(0,1fr))!important;transform:none!important}
    #board .h046-face{font:900 clamp(1rem,2.4vw,1.7rem)/1 Georgia,serif;color:#fff6cc;text-shadow:0 2px 5px #000;text-align:center}
    #board .symbol-ww,#board .symbol-ww2{background:radial-gradient(circle,#d43c4a,#5b0713)!important}
    #board .symbol-c1{background:radial-gradient(circle,#ffd75c,#8c3d08)!important}
    #board .symbol-code{display:none!important}
    #board .cell.gold .h015-symbol-img{width:94%;height:94%;max-width:94%;max-height:94%}
  </style>`);

  for (const [name, raw] of Object.entries(cfg.tables)) {
    tables[name] = {...raw, cumulative: raw.weights.map(weights => {
      let sum = 0;
      return weights.map(weight => sum += Math.max(0, Number(weight)));
    })};
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

  function draw(tableName, reel) {
    const table = tables[tableName], cumulative = table.cumulative[reel];
    const target = Math.random() * cumulative.at(-1);
    let low = 0, high = cumulative.length - 1;
    while (low < high) {
      const middle = (low + high) >> 1;
      if (target < cumulative[middle]) high = middle;
      else low = middle + 1;
    }
    return Number(table.reels[reel][low]);
  }

  const cloneBoard = board => board.map(reel => reel.slice());
  const canonical = symbol => symbol >= 11 && symbol <= 18 ? symbol - 8 : symbol;
  const makeBoard = table => Array.from({length: 5}, (_, reel) => Array.from({length: 4}, () => draw(table, reel)));
  const scatterCount = board => board.flat().filter(symbol => symbol === C1).length;
  const format = value => Number(value).toLocaleString("en-US", {minimumFractionDigits: 2, maximumFractionDigits: 2});

  function evaluate(board) {
    let rawPay = 0;
    const hits = new Set(), details = [];
    for (const target of SCORE) {
      const counts = [], positions = [];
      for (let reel = 0; reel < 5; reel++) {
        const matched = [];
        for (let row = 0; row < 4; row++) {
          const symbol = board[reel][row];
          if (symbol === WW || symbol === W2 || canonical(symbol) === target) matched.push([reel, row]);
        }
        if (!matched.length) break;
        counts.push(matched.length); positions.push(matched);
      }
      if (counts.length < 3) continue;
      const ways = counts.reduce((product, count) => product * count, 1);
      const pay = Number(cfg.pays[String(target)][counts.length - 3]) * ways;
      if (pay <= 0) continue;
      rawPay += pay;
      positions.flat().forEach(([reel, row]) => hits.add(`${reel},${row}`));
      details.push({symbol: CODE[target], length: counts.length, ways, pay});
    }
    return {rawPay, hits, details};
  }

  function addW2(board, tableName, gold) {
    if (!gold.length) return 0;
    const randomWild = tables[tableName].random_wild;
    const count = Number(pick(randomWild.values, randomWild.weights)) || 0;
    if (count <= 0) return 0;
    const source = gold[Math.floor(Math.random() * gold.length)];
    board[source[0]][source[1]] = W2;
    const candidates = [];
    for (let reel = 1; reel < 5; reel++) for (let row = 0; row < 4; row++) {
      if (![WW, W2, C1].includes(board[reel][row])) candidates.push([reel, row]);
    }
    candidates.sort(() => Math.random() - 0.5).slice(0, count).forEach(([reel, row]) => board[reel][row] = W2);
    return Math.min(count, candidates.length);
  }

  function spin(tableName, freeGame = false) {
    const table = tables[tableName];
    const multipliers = table.multipliers?.length ? table.multipliers : (freeGame ? [2,4,6,10] : [1,2,3,5]);
    const board = makeBoard(tableName), snapshots = [];
    let pay = 0, combo = 0, pendingGold = [], bgW2Used = false, golden = 0, w2Events = 0;
    snapshots.push({type:"initial", board: cloneBoard(board), hits: [], combo: 0, multiplier: multipliers[0], message: "Spin"});
    while (true) {
      if (pendingGold.length && (freeGame || !bgW2Used)) {
        const made = addW2(board, tableName, pendingGold);
        if (made) { w2Events++; bgW2Used = true; snapshots.push({type:"convert", board: cloneBoard(board), hits: [], converted: pendingGold.map(([reel,row])=>`${reel},${row}`), combo, multiplier: multipliers[Math.min(combo,3)], message: `W2 × ${made}`}); }
      }
      pendingGold = [];
      const win = evaluate(board);
      if (!win.rawPay) break;
      const multiplier = multipliers[Math.min(combo, multipliers.length - 1)];
      const cascadePay = win.rawPay * multiplier * BET_LEVELS[state.betIndex];
      pay += cascadePay;
      snapshots.push({type:"win", board: cloneBoard(board), hits: [...win.hits], combo, multiplier, message: `WIN ${format(cascadePay)}`, details: win.details});
      const transitionBoard = cloneBoard(board), cleared = [], converted = [];
      combo++;
      for (const key of win.hits) {
        const [reel, row] = key.split(",").map(Number), symbol = board[reel][row];
        if (symbol >= 11 && symbol <= 18) {
          board[reel][row] = WW;
          transitionBoard[reel][row] = WW;
          pendingGold.push([reel, row]);
          converted.push(key);
          golden++;
        } else {
          board[reel][row] = -1;
          cleared.push(key);
        }
      }
      snapshots.push({type:"eliminate", board: transitionBoard, hits: [], cleared, converted, combo, multiplier: multipliers[Math.min(combo,3)], message: "Eliminate + WW"});
      const drop = [];
      for (let reel = 0; reel < 5; reel++) {
        const survivors = board[reel].map((symbol, oldRow) => ({symbol, oldRow})).filter(item => item.symbol !== -1);
        const nextReel = survivors.map(item => item.symbol);
        survivors.forEach((item, finalRow) => {
          const rows = item.oldRow - finalRow;
          if (rows > 0) drop.push({key:`${reel},${finalRow}`, rows, isNew:false, delay:reel * 24});
        });
        while (nextReel.length < 4) {
          const finalRow = nextReel.length;
          nextReel.push(draw(tableName, reel));
          drop.push({key:`${reel},${finalRow}`, rows:4 - finalRow, isNew:true, delay:reel * 24 + (3 - finalRow) * 18});
        }
        board[reel] = nextReel;
      }
      snapshots.push({type:"cascade", board: cloneBoard(board), hits: [], drop, combo, multiplier: multipliers[Math.min(combo,3)], message: "Drop"});
    }
    return {pay, combo, scatter: scatterCount(board), golden, w2Events, board, snapshots, maxMultiplier: multipliers[Math.min(Math.max(combo - 1, 0), multipliers.length - 1)]};
  }

  function freeQueue() {
    const choices = cfg.free_game_mix.choices;
    const choice = pick(choices, choices.map(item => item.weight)), queue = [];
    for (let i = 0; i < choice.high; i++) queue.push("high");
    for (let i = 0; i < choice.low; i++) queue.push("low");
    return queue.sort(() => Math.random() - 0.5);
  }

  function highTable() {
    return pick(["fg_high_a","fg_high_k","fg_high_q","fg_high_j"], cfg.free_game_mix.high_variant_weights);
  }

  function freeSession(superMode = false) {
    let remaining = Number(cfg.free_spins), played = 0, pay = 0, retriggers = 0;
    const queue = freeQueue(), spins = [], snapshots = [];
    while (remaining > 0 && played < Number(cfg.free_spin_cap)) {
      remaining--; played++;
      const surface = queue.shift() || "low";
      const table = superMode ? "super" : surface === "high" ? highTable() : "fg_low";
      const result = spin(table, true);
      pay += result.pay; spins.push(result); snapshots.push(...result.snapshots);
      if (result.scatter >= 3 && played + remaining < Number(cfg.free_spin_cap)) {
        const add = Math.min(Number(cfg.retrigger_spins), Number(cfg.free_spin_cap) - played - remaining);
        remaining += add; retriggers += add > 0 ? 1 : 0;
        queue.push("high", ...Array(Math.max(0, add - 1)).fill("low"));
      }
    }
    return {pay, played, retriggers, spins, snapshots, maxMultiplier: Math.max(1, ...spins.map(item => item.maxMultiplier))};
  }

  function cardProfile() { return "weight_2"; }
  function pickCard(section, profile = cardProfile()) {
    const cards = cfg.card_system?.profiles?.[profile]?.[section];
    if (!cards?.length) return null;
    return pick(cards, cards.map(card => card.weight));
  }
  function cardMatches(card, pay) {
    const ratio = pay / BET_LEVELS[state.betIndex];
    return Number(card.min) < ratio && ratio <= Number(card.max);
  }
  function cardSpin(card) {
    if (!card) return spin("bg_high");
    if (card.type === "free_game") {
      for (let retry = 0; retry < MAX_RETRY; retry++) { const result = spin("bg_low"); if (result.scatter >= 3) return result; }
    } else {
      const table = card.table === "A" ? "bg_low" : "bg_high";
      for (let retry = 0; retry < MAX_RETRY; retry++) { const result = spin(table); if (result.scatter < 3 && cardMatches(card, result.pay)) return result; }
    }
    throw new Error("Card retry limit exceeded");
  }
  function cardFeature(section, superMode) {
    const card = pickCard(section, section === "super_feature" ? "weight_1" : cardProfile());
    if (!card) return freeSession(superMode);
    for (let retry = 0; retry < MAX_RETRY; retry++) { const result = freeSession(superMode); if (cardMatches(card, result.pay)) return result; }
    throw new Error(`${section} retry limit exceeded`);
  }

  function renderMultiplier(freeGame, index = 0) {
    const values = freeGame ? [2,4,6,10] : [1,2,3,5];
    $("multiplierWindow").classList.remove("roll-one");
    $("multiplierWindow").innerHTML = values.map((value, step) => `<span class="multiplier-step ${step < index ? "is-previous" : ""} ${step === Math.min(index,3) ? "is-active" : ""}">×${value}</span>`).join("");
  }

  function renderBoard(board, hitList = [], options = {}) {
    const hits = new Set(hitList), cleared = new Set(options.cleared || []), converted = new Set(options.converted || []), root = $("board");
    const drop = new Map((options.drop || []).map(item => [item.key, item]));
    root.innerHTML = "";
    for (let row = 3; row >= 0; row--) for (let reel = 0; reel < 5; reel++) {
      const symbol = board[reel][row], code = CODE[symbol], cell = document.createElement("div");
      const key = `${reel},${row}`;
      const motion = drop.get(key), speed = Number($("speedRange").value || 1);
      cell.className = `cell symbol-${code.toLowerCase()}${symbol >= 11 ? " gold" : ""}${hits.has(key) ? " hit" : ""}${cleared.has(key) ? " symbol-cleared" : ""}${motion ? (motion.isNew ? " symbol-drop symbol-refill" : " symbol-settle") : ""}${converted.has(key) ? " convert" : ""}${options.spinning ? " reel-spin" : ""}`;
      if (motion) {
        cell.style.setProperty("--drop-start", `${-Math.max(1, motion.rows) * 112}%`);
        const dropDuration = Math.max(85, 520 / speed / DROP_SPEED_MULTIPLIER);
        cell.style.setProperty("--drop-duration", `${dropDuration}ms`);
        cell.style.setProperty("--drop-delay", `${(motion.delay || 0) / DROP_SPEED_MULTIPLIER}ms`);
        if (motion.isNew) cell.style.setProperty("--refill-duration", `${dropDuration}ms`);
      }
      const asset = SYMBOL_ASSET[code];
      cell.innerHTML = asset ? `<div class="symbol-wrap"><img class="symbol-img h015-symbol-img" src="${H046_IMAGE_ROOT}${asset}" alt="${code}" draggable="false"></div>` : `<div class="symbol-wrap"><span class="h046-face">${DISPLAY[code] || code}</span><span class="symbol-code">${code}</span></div>`;
      root.append(cell);
    }
  }

  function delay() { return Math.max(45, 360 / Number($("speedRange").value || 1)); }
  async function animateReels(initialBoard) {
    const frames = Math.max(2, Math.round(8 / Number($("speedRange").value || 1)));
    for (let frame = 0; frame < frames; frame++) {
      const rolling = cloneBoard(initialBoard);
      for (let reel = 0; reel < 5; reel++) {
        const offset = (frames - frame + reel) % 4;
        for (let row = 0; row < 4; row++) rolling[reel][row] = initialBoard[reel][(row + offset) % 4];
      }
      renderBoard(rolling, [], {spinning:true});
      await wait(55);
    }
  }

  function renderWinDetails(snapshot) {
    $("lineList").innerHTML = snapshot.details?.length ? snapshot.details.map(win => `<div>${win.symbol} · ${win.length} reels · ${win.ways} ways · ${format(win.pay)}</div>`).join("") : "<div>No Win</div>";
    $("spinResultList").innerHTML = `<div>Run ${snapshot.combo + 1} · ×${snapshot.multiplier} · ${snapshot.message}</div>`;
    $("carryMultiValue").textContent = snapshot.combo;
  }

  async function animateSnapshots(snapshots, freeGame = false) {
    state.snapshots = snapshots; state.snapshotIndex = -1;
    renderMultiplier(freeGame, 0); $("carryMultiValue").textContent = "0";
    if (snapshots[0]) { await animateReels(snapshots[0].board); renderBoard(snapshots[0].board); await wait(delay()); }
    for (let index = 1; index < snapshots.length; index++) {
      const snapshot = snapshots[index]; state.snapshotIndex = index; renderMultiplier(freeGame, snapshot.combo);
      $("messageBar").textContent = snapshot.message || "Cascade";
      if (snapshot.type === "win") {
        renderWinDetails(snapshot);
        renderBoard(snapshot.board, snapshot.hits); await wait(delay());
      } else if (snapshot.type === "eliminate") {
        renderBoard(snapshot.board, [], {cleared:snapshot.cleared || [], converted:snapshot.converted || []});
        await wait(Math.max(180, 320 / Number($("speedRange").value || 1)));
      } else if (snapshot.type === "cascade") {
        const duration = Math.max(85, 520 / Number($("speedRange").value || 1) / DROP_SPEED_MULTIPLIER);
        renderBoard(snapshot.board, [], {drop:snapshot.drop || []}); await wait(duration + 90);
      } else {
        renderBoard(snapshot.board, [], {converted:snapshot.converted || []}); await wait(delay());
      }
    }
    const finalSnapshot = snapshots.at(-1); if (finalSnapshot) renderBoard(finalSnapshot.board);
    updateDebugButtons();
  }

  function showSnapshot(index) {
    if (!state.snapshots.length) return;
    state.snapshotIndex = Math.max(0, Math.min(index, state.snapshots.length - 1));
    const snapshot = state.snapshots[state.snapshotIndex]; renderBoard(snapshot.board, snapshot.hits, {cleared:snapshot.cleared || [], drop:snapshot.drop || [], converted:snapshot.converted || []}); renderMultiplier(document.body.classList.contains("fg-mode"), snapshot.combo); if (snapshot.type === "win") renderWinDetails(snapshot); updateDebugButtons();
  }
  function updateDebugButtons() {
    $("previousStepBtn").disabled = state.snapshotIndex <= 0;
    $("nextStepBtn").disabled = state.snapshotIndex < 0 || state.snapshotIndex >= state.snapshots.length - 1;
  }

  function updateStats() {
    const bet = BET_LEVELS[state.betIndex];
    $("balanceValue").textContent = format(state.balance); $("betValue").textContent = format(bet); $("betBtn").textContent = `Bet ${format(bet)}`; $("winValue").textContent = format(state.lastWin || 0);
    $("roundCountValue").textContent = state.rounds.toLocaleString();
    $("rtpValue").textContent = state.totalBet ? `${(state.totalWin / state.totalBet * 100).toFixed(2)}%` : "0.00%";
    $("hitRateValue").textContent = state.rounds ? `${(state.hitRounds / state.rounds * 100).toFixed(2)}%` : "0.00%";
    $("fgTriggerValue").textContent = state.rounds ? `${(state.fgTriggers/state.rounds*100).toFixed(3)}% (${state.fgTriggers})` : "0.000% (0)"; $("maxMultiplierValue").textContent = `x${state.maxMultiplier}`;
    const remaining = Math.max(0, state.fg.spins.length - state.fg.index);
    document.body.classList.toggle("fg-mode", remaining > 0); $("fgLeftPill").classList.toggle("hidden", remaining <= 0);
    $("fgLeftValue").textContent = `${remaining}/${state.fg.total}`; $("modeText").textContent = remaining ? (state.fg.mode === 3 ? "Super Free Game" : "Free Game") : "Base Game";
    $("spinBtn").textContent = remaining ? "Next FG" : "Spin";
  }
  function setBusy(value) {
    state.busy = value;
    const inFeature = state.fg.index < state.fg.spins.length;
    $("spinBtn").disabled = value; $("buyFeatureBtn").disabled = value || inFeature; $("buySuperFeatureBtn").disabled = value || inFeature;
    $("betMinusBtn").disabled = value || inFeature || state.betIndex === 0; $("betPlusBtn").disabled = value || inFeature || state.betIndex === BET_LEVELS.length - 1;
  }

  function activateFeature(feature, mode) {
    state.fg = {spins:feature.spins, index:0, total:feature.spins.length, mode}; state.fgTriggers++;
    $("featureStatus").textContent = mode === 3 ? "Super Feature" : "Free Game Triggered"; updateStats();
  }

  function buyEntry() {
    for (let retry = 0; retry < MAX_RETRY; retry++) { const result = spin("buy", false); if (result.scatter >= 3) return result; }
    throw new Error("Buy entry retry limit exceeded");
  }

  async function playFeatureSpin() {
    const item = state.fg.spins[state.fg.index]; if (!item) return;
    await animateSnapshots(item.snapshots, true); state.fg.index++;
    state.lastWin = item.pay; state.totalWin += item.pay; state.balance += item.pay; state.maxMultiplier = Math.max(state.maxMultiplier, item.maxMultiplier);
    $("messageBar").textContent = `FG ${state.fg.index}/${state.fg.total} · ${item.pay > 0 ? `WIN ${format(item.pay)}` : "No Win"}`;
    if (state.fg.index >= state.fg.spins.length) { $("featureStatus").textContent = "Feature complete"; state.fg = {spins:[],index:0,total:0,mode:0}; }
  }

  async function play(mode = 0) {
    if (state.busy) return; setBusy(true); state.lastWin = 0;
    try {
      if (state.fg.index < state.fg.spins.length) {
        await playFeatureSpin();
      } else {
        state.mode = mode; const bet = BET_LEVELS[state.betIndex], cost = bet * (mode === 2 ? Number(cfg.buy_price) : mode === 3 ? Number(cfg.super_buy_price) : 1);
        if (state.balance < cost) throw new Error("Insufficient balance");
        state.balance -= cost; state.totalBet += cost; state.rounds++; updateStats();
        let base;
        if (mode === 0) base = $("forceFgInput").checked ? cardSpin({type:"free_game"}) : cardSpin(pickCard("base_game"));
        else base = buyEntry();
        await animateSnapshots(base.snapshots, false); state.lastWin = base.pay; state.totalWin += base.pay; state.balance += base.pay; state.hitRounds += base.pay > 0 ? 1 : 0; state.maxMultiplier = Math.max(state.maxMultiplier, base.maxMultiplier);
        $("messageBar").textContent = base.pay > 0 ? `WIN ${format(base.pay)}` : "No Win";
        if (base.scatter >= 3 || mode !== 0) {
          const superMode = mode === 3, section = mode === 0 ? "free_game" : superMode ? "super_feature" : "buy_feature";
          activateFeature(cardFeature(section, superMode), mode);
        }
      }
    } catch (error) { console.error(error); $("messageBar").textContent = error.message; }
    updateStats(); setBusy(false); if (state.auto) setTimeout(() => play(0), 180);
  }

  function helpHtml() {
    const payRows = SCORE.map(symbol => `<div class="help-payout-item">[${CODE[symbol]}] 3-${cfg.pays[String(symbol)][0]*100} / 4-${cfg.pays[String(symbol)][1]*100} / 5-${cfg.pays[String(symbol)][2]*100}</div>`).join("");
    return `<section class="help-section"><h3 class="help-section-title">符號賠付值 <span class="help-en">SYMBOL PAYOUT VALUES</span></h3><p class="help-rule">所有符號必須由最左至右連續出現，方可獲獎。<br><span class="help-rule-en">ALL WINS ARE FROM LEFTMOST TO RIGHT ONLY.</span></p><div class="help-payout-grid">${payRows}</div></section>
    <section class="help-section"><h3 class="help-section-title">消除掉落特色 <span class="help-en">CASCADING FEATURE</span></h3><p class="help-rule">中獎後，金框以外的中獎符號消除並由上方補入新符號，直到沒有新中獎組合。</p></section>
    <section class="help-section"><h3 class="help-section-title">黃金符號特色 <span class="help-en">GOLDEN SYMBOL FEATURE</span></h3><p class="help-rule">黃金符號出現在第 2、3、4 輪。參與中獎後會在原位置轉為 [WW]，或轉為 [W2] 並隨機複製 2～4 個 [W2]。</p></section>
    <section class="help-section"><h3 class="help-section-title">賠付倍數特色 <span class="help-en">WIN MULTIPLIER FEATURE</span></h3><p class="help-rule">主遊戲連消倍率固定為 ×1、×2、×3、×5；免費遊戲固定為 ×2、×4、×6、×10。</p></section>
    <section class="help-section"><h3 class="help-section-title">免費遊戲特色 <span class="help-en">FREE GAME FEATURE</span></h3><p class="help-rule">3 個以上 [C1] 觸發 10 場免費遊戲。免費遊戲中 3 個以上 [C1] 增加 5 場，最多 50 場。</p></section>
    <section class="help-section"><h3 class="help-section-title">購買特色 <span class="help-en">BUY FEATURE</span></h3><p class="help-rule">一般購買特色價格為投注的 40.5 倍；購買超級特色價格為投注的 250 倍。超級特色中，每次消除黃金符號都會產生 [W2]。</p></section>
    <section class="help-section"><h3 class="help-section-title">最多路數 <span class="help-en">MAXIMUM WAYS</span></h3><p class="help-rule">5 輪 4 列，最多 1024 Ways。百搭符號可替代除 [C1] 外的所有符號。</p></section>`;
  }

  function applyLanguage() {
    $("gameId").textContent = cfg.game_id; $("gameName").textContent = state.language === "zh" ? cfg.name_zh : cfg.name_en;
    $("buyFeatureBtn").textContent = state.language === "zh" ? "購買特色 (40.5x)" : "Buy Feature (40.5x)";
    $("buySuperFeatureBtn").textContent = state.language === "zh" ? "購買超級特色 (250x)" : "Buy Super Feature (250x)";
  }
  function setDebug(enabled) { $("controls").classList.toggle("debug-off", !enabled); document.querySelectorAll(".debug-only, #set-rng-panel, #play-debug-controls").forEach(node => node.classList.toggle("debug-hidden", !enabled)); }
  function reset() {
    Object.assign(state, {balance:10000, rounds:0, totalBet:0, totalWin:0, hitRounds:0, fgTriggers:0, maxMultiplier:1, lastWin:0, auto:false, snapshots:[], snapshotIndex:-1, fg:{spins:[],index:0,total:0,mode:0}});
    $("autoBtn").textContent = "Auto"; renderBoard(makeBoard("bg_low")); renderMultiplier(false); $("messageBar").textContent = "Ready — press Spin"; updateStats();
  }
  function buildBetMenu() {
    $("betMenu").innerHTML = BET_LEVELS.map((value,index) => `<button type="button" data-index="${index}">${format(value)}</button>`).join("");
    $("betMenu").querySelectorAll("button").forEach(button => button.onclick = () => {state.betIndex=Number(button.dataset.index);$("betMenu").classList.add("hidden");updateStats();});
  }

  $("spinBtn").onclick = () => play(0); $("buyFeatureBtn").onclick = () => play(2); $("buySuperFeatureBtn").onclick = () => play(3);
  $("autoBtn").onclick = () => {state.auto=!state.auto;$("autoBtn").textContent=state.auto?"Stop":"Auto";if(state.auto&&!state.busy)play(0);};
  $("betMinusBtn").onclick = () => {state.betIndex=Math.max(0,state.betIndex-1);updateStats();}; $("betPlusBtn").onclick = () => {state.betIndex=Math.min(BET_LEVELS.length-1,state.betIndex+1);updateStats();};
  $("betBtn").onclick = () => $("betMenu").classList.toggle("hidden"); $("speedRange").oninput = () => $("speedValue").textContent=`x${$("speedRange").value}`;
  $("debugModeInput").onchange = () => setDebug($("debugModeInput").checked); $("previousStepBtn").onclick=()=>showSnapshot(state.snapshotIndex-1); $("nextStepBtn").onclick=()=>showSnapshot(state.snapshotIndex+1);
  $("languageSelect").onchange = () => {state.language=$("languageSelect").value;applyLanguage();};
  $("helpBtn").onclick = () => {$("helpContent").innerHTML=helpHtml();$("helpDialog").showModal();}; $("closeHelpBtn").onclick=()=>$("helpDialog").close();
  $("resetBtn").onclick=reset; $("clearLogBtn").onclick=()=>$("liveLogBody").innerHTML=""; $("setRngResetBtn").onclick=()=>{$("reelRngInput").value="";$("forceFgInput").checked=false;};
  $("configSelect").value=window.H046_ACTIVE_CONFIG; $("configSelect").onchange=()=>{const url=new URL(location.href);url.searchParams.set("config",$("configSelect").value);location.href=url.href;};
  document.title=`${cfg.name_en || "Lucky Ace"} — Demo Game`; buildBetMenu(); applyLanguage(); setDebug(false); reset();
})();
