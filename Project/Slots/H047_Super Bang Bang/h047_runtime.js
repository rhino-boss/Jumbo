// ─── CONSTANTS ───────────────────────────────────────────────────────────────
const COLS = 5, ROWS = 4;
const SCATTER_MIN = 3, FG_INIT = 10, FG_RETRIG = 5;
const BUY_MULT = 100, MAX_WIN_MULT = 1024;
const BET_OPTIONS = [0.5,1,2,5,10,20,50,100,200,500,1000];

// Symbol IDs
const S = { WW:0, SC:1, ACE:2, K:3, Q:4, J:5, SP:6, HT:7, DM:8, CL:9, GC:10 };
const SYMS = [
  {id:0, code:'WW', label:'WW', bg:'rgba(40,120,50,0.7)', color:'#7fff7f'},
  {id:1, code:'C1', label:'C1', bg:'rgba(120,100,0,0.7)', color:'#ffdd55'},
  {id:2, code:'M1', label:'M1', bg:'rgba(100,60,0,0.7)', color:'#ffd700'},
  {id:3, code:'M2', label:'M2', bg:'rgba(80,50,0,0.7)', color:'#ffbe76'},
  {id:4, code:'M3', label:'M3', bg:'rgba(80,20,20,0.7)', color:'#ff7675'},
  {id:5, code:'M4', label:'M4', bg:'rgba(40,20,80,0.7)', color:'#a29bfe'},
  {id:6, code:'A',  label:'A',  bg:'rgba(20,40,80,0.7)', color:'#74b9ff'},
  {id:7, code:'K',  label:'K',  bg:'rgba(80,20,50,0.7)', color:'#fd79a8'},
  {id:8, code:'Q',  label:'Q',  bg:'rgba(20,70,70,0.7)', color:'#81ecec'},
  {id:9, code:'J',  label:'J',  bg:'rgba(20,60,40,0.7)', color:'#55efc4'},
  {id:10,code:'GC', label:'GC', bg:'rgba(100,70,0,0.7)', color:'#fdcb6e'},
];
const PAY = {
  2:[0.5,1.5,2.5], 3:[0.4,1.2,2.0], 4:[0.3,0.9,1.5], 5:[0.2,0.6,1.0],
  6:[0.1,0.3,0.5], 7:[0.1,0.3,0.5], 8:[0.05,0.15,0.25], 9:[0.05,0.15,0.25],
};
const SCORE_IDS = [2,3,4,5,6,7,8,9];
const MULTI_STRIP = [
   1,  5,  2, 10,  1,  3, 25,  2,  1, 15,
   3,  5,  2,100,  1,  3, 10,  2,  5, 20,
   1, 15,  3, 50,  2, 10,  1,500,  5, 25,
   3,  2, 20,  1,  5, 10,  2,  1, 25,  3
];
// Symbol weights per column: [WW,SC,ACE,K,Q,J,SP,HT,DM,CL,GC]
const W_NORMAL = [3,2,8,8,10,10,13,13,16,16,0];
const W_GOLD   = [3,2,7,7, 9, 9,12,12,15,15,5];

// ─── STATE ───────────────────────────────────────────────────────────────────
const st = {
  balance: 100000, totalBet:0, totalWin:0,
  totalSpins:0, hitSpins:0, fgTriggers:0, roundCount:0,
  betIdx:4, autoOn:false, turboOn:false, speed:1, maxMultiplier:0, busy:false,
  pendingRound:null, pendingSpinIdx:0, displayWin:0, autoTimer:null,
};

// ─── HELPERS ─────────────────────────────────────────────────────────────────
const ri = n => Math.floor(Math.random() * n);
const cloneBoard = b => b.map(row => row.map(c => ({...c})));
const fmt = n => Number(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
const fmtI = n => Math.round(n).toLocaleString('en-US');
const fmtBet = n => Number(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
const getBet = () => BET_OPTIONS[st.betIdx];
const delay = ms => new Promise(r => setTimeout(r, Math.max(16,Math.round(ms/st.speed))));

function pickW(weights) {
  const total = weights.reduce((a,b)=>a+b,0);
  let r = Math.random()*total;
  for(let i=0;i<weights.length;i++){ r-=weights[i]; if(r<=0) return i; }
  return weights.length-1;
}
function randSymbol(col) {
  const w = (col>=1&&col<=3) ? W_GOLD : W_NORMAL;
  const symOrder = [S.WW,S.SC,S.ACE,S.K,S.Q,S.J,S.SP,S.HT,S.DM,S.CL,S.GC];
  return symOrder[pickW(w)];
}
function makeCell(sym, base=null) {
  const b = base !== null ? base : (sym===S.GC ? SCORE_IDS[ri(SCORE_IDS.length)] : sym);
  return { sym, base:b, isGold:sym===S.GC, isWild:sym===S.WW, isScat:sym===S.SC, isEmpty:false };
}
function genBoard() {
  return Array.from({length:ROWS}, (_,row) =>
    Array.from({length:COLS}, (_,col) => makeCell(randSymbol(col)))
  );
}
function randStripIdx() { return Math.floor(Math.random()*MULTI_STRIP.length); }

// ─── 1024 WAYS EVALUATION ─────────────────────────────────────────────────────
function evalWays(board) {
  const wins = [];
  for(const sym of SCORE_IDS) {
    // Count per reel: positions matching sym OR Wild
    const counts = Array.from({length:COLS}, (_,col) => {
      let n=0;
      for(let row=0;row<ROWS;row++) {
        const c=board[row][col];
        if(!c.isEmpty && (c.base===sym || c.sym===S.WW)) n++;
      }
      return n;
    });
    let ways=1, len=0;
    for(let col=0;col<COLS;col++) {
      if(counts[col]===0) break;
      ways*=counts[col]; len++;
    }
    if(len>=3) {
      const base=PAY[sym][len-3];
      wins.push({sym, len, ways, base, raw:base*ways});
    }
  }
  return wins;
}

// Build hit mask: mark all cells contributing to at least one win
function buildHitMask(board, wins) {
  const hit = Array.from({length:ROWS},()=>Array(COLS).fill(false));
  for(const w of wins) {
    for(let col=0;col<w.len;col++) {
      for(let row=0;row<ROWS;row++) {
        const c=board[row][col];
        if(!c.isEmpty && (c.base===w.sym || c.sym===S.WW)) hit[row][col]=true;
      }
    }
  }
  return hit;
}

// Count scatters on board
function countScatter(board) {
  let n=0;
  for(let r=0;r<ROWS;r++) for(let c=0;c<COLS;c++) if(!board[r][c].isEmpty&&board[r][c].isScat) n++;
  return n;
}

// ─── CASCADE LOGIC ────────────────────────────────────────────────────────────
// Process one cascade step: convert GC→Wild, eliminate hits, apply Joker, drop, fill
function cascade(board, hit) {
  const converts = []; // {row,col} GC→Wild positions
  // 1. Convert hit Golden Cards to Wild
  for(let r=0;r<ROWS;r++) for(let c=0;c<COLS;c++) {
    if(hit[r][c] && board[r][c].isGold) {
      board[r][c] = makeCell(S.WW);
      converts.push({row:r,col:c});
    }
  }
  // 2. Joker effect: if any GC converted, decide Big/Little Joker
  if(converts.length>0) {
    const bigJoker = Math.random()<0.5;
    if(bigJoker) {
      // Big Joker: randomly replace 1-4 non-SC/non-WW in cols 1-4 (R2-R5)
      const candidates=[];
      for(let r=0;r<ROWS;r++) for(let c=1;c<COLS;c++) {
        const cell=board[r][c];
        if(!cell.isEmpty&&!cell.isWild&&!cell.isScat&&!hit[r][c]) candidates.push({r,c});
      }
      const count=1+ri(Math.min(4,candidates.length));
      for(let i=0;i<count&&candidates.length;i++) {
        const pick=ri(candidates.length);
        const {r,c}=candidates.splice(pick,1)[0];
        board[r][c]=makeCell(S.WW);
        hit[r][c]=true; // mark as hit so they get removed next? 
        // Actually Big Joker Wilds stay - they converted, not eliminated
        hit[r][c]=false; // they stay on board as Wilds
        board[r][c].isNewJoker=true;
      }
    }
    // Little Joker: only the converted positions become Wild (already done)
  }
  // 3. Eliminate non-Wild hit cells (set isEmpty)
  for(let r=0;r<ROWS;r++) for(let c=0;c<COLS;c++) {
    if(hit[r][c] && !board[r][c].isWild) board[r][c].isEmpty=true;
  }
  // 4. Drop: per column, compact non-empty to bottom, fill top with new
  for(let c=0;c<COLS;c++) {
    const keep=[];
    for(let r=ROWS-1;r>=0;r--) { if(!board[r][c].isEmpty) keep.push(board[r][c]); }
    for(let r=ROWS-1;r>=0;r--) {
      if(keep.length>0) board[r][c]=keep.shift();
      else board[r][c]=makeCell(randSymbol(c));
    }
  }
  return converts;
}

// ─── SPIN ─────────────────────────────────────────────────────────────────────
function runSpin(mode, stripStartIdx=0) {
  // mode: 'BG' | 'FG'
  const board = genBoard();
  let cumulSum = 0;  // accumulates strip values as cascades happen

  let totalRaw = 0;
  let cascadeCount = 0;
  const steps = [];
  const allWins = [];
  let scatterCount = countScatter(board);
  const initBoard = cloneBoard(board);

  while(true) {
    const wins = evalWays(board);
    if(!wins.length) break;
    const rawSum = wins.reduce((s,w)=>s+w.raw, 0);
    const stripVal = MULTI_STRIP[(stripStartIdx + cascadeCount) % MULTI_STRIP.length];
    cumulSum += stripVal;
    st.maxMultiplier = Math.max(st.maxMultiplier, Math.min(cumulSum, MAX_WIN_MULT));
    const pay = rawSum * cumulSum;
    totalRaw += pay;
    allWins.push(...wins.map(w=>({...w, mult:cumulSum, stripVal, pay:w.raw*cumulSum, cascade:cascadeCount+1})));

    const hit = buildHitMask(board, wins);
    const boardBefore = cloneBoard(board);
    const converts = cascade(board, hit);
    cascadeCount++;

    // Check scatter after drop (for retrigger in FG)
    const newScat = countScatter(board);
    if(newScat>scatterCount) scatterCount=newScat;

    steps.push({
      cascadeIdx: cascadeCount,
      boardBefore,
      boardAfter: cloneBoard(board),
      wins, rawSum, mult:cumulSum, stripVal, pay, converts
    });

    if(totalRaw >= getBet()*MAX_WIN_MULT) break;
  }

  return { mode, board:cloneBoard(board), initBoard, steps, allWins, totalRaw, cascadeCount, scatterCount, stripStartIdx };
}

// ─── ROUND ────────────────────────────────────────────────────────────────────
function runRound(isBuy=false) {
  const bet = getBet();
  const coinIn = isBuy ? bet*BUY_MULT : bet;
  if(st.balance<coinIn) throw new Error('Balance insufficient');

  st.balance -= coinIn;
  st.totalBet += coinIn;

  const spins=[];
  const base = runSpin('BG', randStripIdx());
  base.spinIdx=1; base.isTrigger=false;
  spins.push(base);
  st.totalSpins++;
  if(base.totalRaw>0) st.hitSpins++;

  let fgRemain = (base.scatterCount>=SCATTER_MIN||isBuy) ? FG_INIT : 0;
  if(fgRemain>0) st.fgTriggers++;

  while(fgRemain>0) {
    const fg = runSpin('FG', randStripIdx());
    fg.spinIdx = spins.length+1;
    fg.remainBefore = fgRemain;
    fgRemain--;
    if(fg.scatterCount>=SCATTER_MIN) { fgRemain+=FG_RETRIG; fg.retrigger=FG_RETRIG; }
    fg.remainAfter = fgRemain;
    spins.push(fg);
    st.totalSpins++;
    if(fg.totalRaw>0) st.hitSpins++;
  }

  const totalWin = spins.reduce((s,sp)=>s+sp.totalRaw,0);
  st.balance += totalWin;
  st.totalWin += totalWin;
  st.roundCount++;

  return { bet, coinIn, spins, totalWin, isBuy };
}

// ─── RENDERING ───────────────────────────────────────────────────────────────
const boardEl = document.getElementById('board');
const msgEl   = document.getElementById('msgBar');
const modeLbl = document.getElementById('modeLabel');
const featSt  = document.getElementById('featureStatus');
const cascEl     = document.getElementById('cascadeValue');
const cumulMultEl= document.getElementById('cumulMultValue');
const fgPill  = document.getElementById('fgPill');
const fgLeftEl= document.getElementById('fgLeftValue');
const balEl   = document.getElementById('balVal');
const betEl   = document.getElementById('betVal');
const winEl   = document.getElementById('winVal');
const rtpEl   = document.getElementById('rtpVal');
const hitEl   = document.getElementById('hitVal');
const fgTrigEl= document.getElementById('fgTrigVal');
const roundEl = document.getElementById('roundVal');
const maxMultEl = document.getElementById('maxMultVal');
const lineEl  = document.getElementById('lineList');
const rngEl   = document.getElementById('rngList');
const resEl   = document.getElementById('resultList');
const spinBtn = document.getElementById('spinBtn');
const betBtn  = document.getElementById('betBtn');
const betMinusBtn = document.getElementById('betMinusBtn');
const betPlusBtn = document.getElementById('betPlusBtn');
const betMenuEl = document.getElementById('betMenu');
const buyBtn  = document.getElementById('buyBtn');
const autoBtn = document.getElementById('autoBtn');
const normalBetBtn = document.getElementById('normalBetBtn');
const speedRange = document.getElementById('speedRange');
const speedValue = document.getElementById('speedValue');
const resetBtn= document.getElementById('resetBtn');
const debugModeInput = document.getElementById('debugModeInput');
const languageSelect = document.getElementById('languageSelect');
const helpBtn = document.getElementById('helpBtn');
const helpDialog = document.getElementById('helpDialog');
const closeHelpBtn = document.getElementById('closeHelpBtn');

function renderCell(cell, opts={}) {
  const info = SYMS[cell.sym] || SYMS[0];
  const displayInfo = cell.isGold ? (SYMS[cell.base] || info) : info;
  const el = document.createElement('div');
  const symbolClass = `symbol-${displayInfo.code.toLowerCase().replace(/[^a-z0-9_-]/g,'')}`;
  const cls = ['cell', symbolClass];
  if(cell.isGold) cls.push('gold');
  if(cell.isWild) cls.push('wild');
  if(cell.isScat) cls.push('scatter');
  if(cell.isEmpty) cls.push('empty');
  if(opts.hit) cls.push('hit');
  if(opts.convert) cls.push('convert');
  if(opts.spin) cls.push('reel-spin');
  el.className = cls.join(' ');
  const wrap = document.createElement('div');
  wrap.className = 'symbol-wrap';
  const glyph = document.createElement('span');
  glyph.className = 'h027-glyph';
  glyph.textContent = cell.isEmpty ? '' : displayInfo.code;
  wrap.appendChild(glyph);
  el.appendChild(wrap);
  return el;
}

function renderBoard(board, hitMask=null, convertSet=null, spinning=false, slideIn=false) {
  boardEl.innerHTML='';
  for(let r=0;r<ROWS;r++) for(let c=0;c<COLS;c++) {
    const cell=board[r][c];
    const isHit = hitMask&&hitMask[r][c];
    const isCvt = convertSet&&convertSet.some(x=>x.row===r&&x.col===c);
    const el=renderCell(cell,{hit:isHit,convert:isCvt,spin:spinning});
    if(slideIn) {
      const dur=st.turboOn?150:360;
      const stagger=st.turboOn?35:90;
      el.style.animation=`reelDrop ${dur}ms cubic-bezier(0.22,0.85,0.30,1.05) ${c*stagger}ms both`;
    }
    boardEl.appendChild(el);
  }
}

function randomBoard() {
  return Array.from({length:ROWS},()=>Array.from({length:COLS},(_,c)=>makeCell(randSymbol(c))));
}

function updateCards(win=null) {
  balEl.textContent = fmtI(st.balance);
  betEl.textContent = fmtBet(getBet());
  betBtn.textContent = `Bet ${fmtBet(getBet())}`;
  winEl.textContent = win!==null ? fmtI(win) : fmtI(st.displayWin);
  if(st.totalBet>0) rtpEl.textContent=(st.totalWin/st.totalBet*100).toFixed(1)+'%';
  if(st.totalSpins>0) hitEl.textContent=(st.hitSpins/st.totalSpins*100).toFixed(1)+'%';
  roundEl.textContent = fmtI(st.roundCount);
  fgTrigEl.textContent = `${st.roundCount ? (st.fgTriggers/st.roundCount*100).toFixed(3) : '0.000'}% (${st.fgTriggers})`;
  maxMultEl.textContent = `×${st.maxMultiplier}`;
}

function closeBetMenu() {
  betMenuEl.classList.add('hidden');
  betBtn.setAttribute('aria-expanded','false');
}

function toggleBetMenu() {
  const willOpen = betMenuEl.classList.contains('hidden');
  betMenuEl.classList.toggle('hidden',!willOpen);
  betBtn.setAttribute('aria-expanded',String(willOpen));
}

function updateBetMenuSelection() {
  Array.from(betMenuEl.children).forEach((option,index)=>{
    const active=index===st.betIdx;
    option.classList.toggle('is-active',active);
    option.setAttribute('aria-selected',String(active));
  });
}

function updateBetControls() {
  const locked=st.busy||st.autoOn||Boolean(st.pendingRound);
  betBtn.disabled=locked;
  betMinusBtn.disabled=locked||st.betIdx===0;
  betPlusBtn.disabled=locked||st.betIdx===BET_OPTIONS.length-1;
  if(locked) closeBetMenu();
}

function setBetIndex(nextIndex) {
  if(st.busy||st.autoOn||st.pendingRound) return;
  st.betIdx=Math.min(BET_OPTIONS.length-1,Math.max(0,nextIndex));
  updateCards();
  updateBetMenuSelection();
  updateBetControls();
  msgEl.textContent=`Bet ${fmtBet(getBet())}`;
}

function renderBetMenu() {
  betMenuEl.innerHTML='';
  BET_OPTIONS.forEach((amount,index)=>{
    const option=document.createElement('button');
    option.type='button';
    option.className='bet-option';
    option.setAttribute('role','option');
    option.textContent=fmtBet(amount);
    option.addEventListener('click',event=>{
      event.stopPropagation();
      setBetIndex(index);
      closeBetMenu();
    });
    betMenuEl.appendChild(option);
  });
  updateBetMenuSelection();
}

function updateFeatureBar(spin=null, fgLeft=null) {
  if(!spin) {
    modeLbl.textContent='Base Game'; featSt.textContent='';
    cascEl.textContent='0'; cumulMultEl.textContent='x1';
    fgPill.classList.add('hidden');
    document.body.classList.remove('fg-mode');
    return;
  }
  const isFG = spin.mode==='FG';
  modeLbl.textContent = isFG ? 'Free Game' : 'Base Game';
  cascEl.textContent = spin.cascadeCount;
  if(isFG&&fgLeft!=null) {
    fgPill.classList.remove('hidden');
    fgLeftEl.textContent = fgLeft;
  } else {
    fgPill.classList.add('hidden');
  }
  document.body.classList.toggle('fg-mode', isFG);
}

function renderWaysList(wins) {
  lineEl.innerHTML='';
  if(!wins||!wins.length) {
    lineEl.innerHTML='<div class="line-row"><span>No win</span><span>0</span></div>'; return;
  }
  wins.slice(0,10).forEach(w=>{
    const info=SYMS[w.sym]||SYMS[0];
    const row=document.createElement('div'); row.className='line-row';
    row.innerHTML=`<span style="color:${info.color}">${info.label} × ${w.len}R × ${w.ways}W | C${w.cascade} ×${w.mult}</span><span>${fmt(w.pay)}</span>`;
    lineEl.appendChild(row);
  });
}

function renderRngList(spin) {
  rngEl.innerHTML='';
  if(!spin) return;
  const rows=[
    {l:'Mode', r:spin.mode},
    {l:'Strip Start', r:'pos '+spin.stripStartIdx+' (×'+MULTI_STRIP[spin.stripStartIdx]+')'},
    {l:'Cascades', r:spin.cascadeCount},
    {l:'Scatter', r:spin.scatterCount},
    {l:'Total Win', r:fmt(spin.totalRaw)},
  ];
  rows.forEach(({l,r})=>{
    const el=document.createElement('div'); el.className='rng-row';
    el.innerHTML=`<span>${l}</span><span>${r}</span>`; rngEl.appendChild(el);
  });
}

function boardToText(board) {
  return board.map(row=>row.map(c=>(c.isEmpty?'--':SYMS[c.sym].code).padEnd(3)).join(' ')).join('\n');
}

function renderResultList(spin) {
  resEl.innerHTML='';
  if(!spin) { resEl.innerHTML='<div class="spin-result-row"><div class="spin-result-head"><span>—</span></div></div>'; return; }
  const stages=[{label:'Init', board:spin.initBoard, meta:spin.mode+' | strip ×'+MULTI_STRIP[spin.stripStartIdx]}];
  spin.steps.forEach(s=>stages.push({
    label:`Cascade ${s.cascadeIdx}`,
    board:s.boardAfter,
    meta:`Raw ${fmt(s.rawSum)} × ${s.mult} = ${fmt(s.pay)}`
  }));
  stages.forEach(st=>{
    const row=document.createElement('div'); row.className='spin-result-row';
    row.innerHTML=`<div class="spin-result-head"><span>${st.label}</span><span>${st.meta}</span></div><pre class="spin-result-board">${boardToText(st.board)}</pre>`;
    resEl.appendChild(row);
  });
}

// ─── PLAYBACK ────────────────────────────────────────────────────────────────
async function animateReels(initialBoard) {
  const frames = Math.max(2, Math.round(8 / st.speed));
  for(let frame=0;frame<frames;frame++) {
    const rolling = cloneBoard(initialBoard);
    for(let reel=0;reel<COLS;reel++) {
      const offset = (frames - frame + reel) % ROWS;
      for(let row=0;row<ROWS;row++) {
        rolling[row][reel] = {...initialBoard[(row + offset) % ROWS][reel]};
      }
    }
    renderBoard(rolling, null, null, true);
    await new Promise(resolve=>setTimeout(resolve,55));
  }
}

async function playSpin(spin, fgLeft=null) {
  updateFeatureBar(spin, fgLeft);
  cascEl.textContent='0'; cumulMultEl.textContent='x1';
  msgEl.textContent=`${spin.mode} Spin ${spin.spinIdx} | Rolling reels...`;
  await Promise.all([
    spinTrackAnim(spin.stripStartIdx),
    animateReels(spin.initBoard)
  ]);
  renderBoard(spin.initBoard);
  await delay(360);
  renderResultList(spin);
  renderWaysList([]);
  renderRngList(spin);
  msgEl.textContent=`${spin.mode} Spin ${spin.spinIdx} | Strip start: ×${MULTI_STRIP[spin.stripStartIdx]}`;
  await delay(300);

  for(const step of spin.steps) {
    const hit=buildHitMask(step.boardBefore, step.wins);
    const cvtSet=step.converts.map(c=>({row:c.row,col:c.col}));
    renderBoard(step.boardBefore, hit, cvtSet);
    renderWaysList(spin.allWins.filter(w=>w.cascade===step.cascadeIdx));
    cascEl.textContent = step.cascadeIdx;
    cumulMultEl.textContent = 'x'+step.mult;
    msgEl.textContent=`Cascade ${step.cascadeIdx} | ×${step.stripVal}→Σ×${step.mult} | +${fmt(step.pay)}`;
    await stepTrackForward();
    await delay(200);
    renderBoard(step.boardAfter);
    await delay(240);
  }
  renderBoard(spin.board);
  renderResultList(spin);
  renderRngList(spin);
  renderWaysList(spin.allWins);
  msgEl.textContent=`${spin.mode} Spin ${spin.spinIdx} done | Win ${fmt(spin.totalRaw)}`;
  st.displayWin = spin.totalRaw;
  updateCards();
}

// ─── MAIN SPIN HANDLER ───────────────────────────────────────────────────────
async function doSpin(isBuy=false) {
  if(st.busy) return;
  st.busy=true;
  spinBtn.disabled=true; buyBtn.disabled=true; updateBetControls();

  try {
    if(st.pendingRound && st.pendingSpinIdx<st.pendingRound.spins.length) {
      const round=st.pendingRound;
      const spin=round.spins[st.pendingSpinIdx];
      const fgLeft=spin.remainAfter!=null?spin.remainAfter:0;
      msgEl.textContent=`FG Spin ${spin.spinIdx} rolling...`;
      await playSpin(spin, fgLeft);
      st.pendingSpinIdx++;
      if(st.pendingSpinIdx>=round.spins.length) {
        st.pendingRound=null;
        msgEl.textContent=`Round done | Total Win ${fmt(round.totalWin)}`;
        st.displayWin=round.totalWin;
        updateCards();
        updateFeatureBar(null);
        document.body.classList.remove('fg-mode');
      } else {
        const next=round.spins[st.pendingSpinIdx];
        msgEl.textContent=`FG ready | ${next.remainBefore} spins left — press Spin`;
      }
    } else {
      msgEl.textContent='Spinning...';
      const round=runRound(isBuy);
      st.displayWin=0;
      updateCards(0);
      await playSpin(round.spins[0]);
      updateCards(round.spins[0].totalRaw);
      if(round.spins.length>1) {
        st.pendingRound=round; st.pendingSpinIdx=1;
        msgEl.textContent=`${isBuy?'Buy Feature':'Scatter'} → FG x${FG_INIT} | press Spin`;
      } else {
        st.pendingRound=null; st.pendingSpinIdx=0;
        st.displayWin=round.totalWin;
        updateCards(round.totalWin);
      }
    }
  } catch(e) {
    st.autoOn=false; clearTimeout(st.autoTimer);
    msgEl.textContent=e.message;
  } finally {
    st.busy=false;
    spinBtn.disabled=false; buyBtn.disabled=false;
    updateBetControls();
    spinBtn.textContent=st.pendingRound?'Next FG':'Spin';
    autoBtn.classList.toggle('is-active',st.autoOn);
    if(st.autoOn&&!st.pendingRound) {
      clearTimeout(st.autoTimer);
      st.autoTimer=setTimeout(()=>doSpin(false), st.turboOn?120:600);
    }
  }
}


// ─── MULTI STRIP TRACK ───────────────────────────────────────────────────────
let trackCenter = 0;
const mOuter  = document.getElementById('multiOuter');
const mTrack  = document.getElementById('multiTrack');
const mCells  = [0,1,2,3,4,5,6].map(i=>document.getElementById('mc'+i));
// 7 cells total; show 5 at once (mc1–mc5 visible, mc0/mc6 are buffer)
// active cell = mc3 (center of visible 5)

function initTrack() {
  const cw = mOuter.offsetWidth / 5;
  mCells.forEach(c=>{ c.style.width=cw+'px'; });
  mTrack.style.width=(cw*7)+'px';
  mTrack.style.transition='none';
  mTrack.style.left=(-cw)+'px';
  setTrackContent(0);
}

function setTrackContent(ci) {
  const n=MULTI_STRIP.length;
  ci=((ci%n)+n)%n; trackCenter=ci;
  // offset: mc0=ci-3, mc1=ci-2, mc2=ci-1, mc3=ci, mc4=ci+1, mc5=ci+2, mc6=ci+3
  const ids=[-3,-2,-1,0,1,2,3].map(o=>((ci+o)%n+n)%n);
  mCells.forEach((c,i)=>{ c.textContent='×'+MULTI_STRIP[ids[i]]; c.classList.toggle('active',i===3); });
}

async function spinTrackAnim(targetIdx) {
  const n=MULTI_STRIP.length;
  const frames=st.turboOn?4:16; const ms=st.turboOn?30:48;
  for(let i=0;i<frames;i++){ setTrackContent(Math.floor(Math.random()*n)); await delay(ms); }
  setTrackContent(targetIdx);
}

async function stepTrackForward() {
  const cw=mOuter.offsetWidth/5;
  const n=MULTI_STRIP.length;
  const newIdx=(trackCenter+1)%n;
  const ids=[-2,-1,0,1,2,3,4].map(o=>((trackCenter+o)%n+n)%n);
  mCells.forEach((c,i)=>{ c.textContent='×'+MULTI_STRIP[ids[i]]; c.classList.toggle('active',i===2); });
  mTrack.style.transition='none';
  mTrack.style.left=(-cw)+'px';
  await new Promise(r=>{
    requestAnimationFrame(()=>{
      mTrack.style.transition='left 170ms ease-out';
      mTrack.style.left=(-2*cw)+'px';
      setTimeout(()=>{ mTrack.style.transition='none'; mTrack.style.left=(-cw)+'px'; setTrackContent(newIdx); r(); },185);
    });
  });
}

// ─── EVENTS ──────────────────────────────────────────────────────────────────
spinBtn.addEventListener('click',()=>doSpin(false));
buyBtn.addEventListener('click',()=>doSpin(true));
normalBetBtn.addEventListener('click',()=>{ msgEl.textContent='Normal Bet selected'; });
betBtn.addEventListener('click',()=>{
  if(st.busy||st.autoOn||st.pendingRound) return;
  toggleBetMenu();
});
betMinusBtn.addEventListener('click',()=>setBetIndex(st.betIdx-1));
betPlusBtn.addEventListener('click',()=>setBetIndex(st.betIdx+1));
document.addEventListener('click',event=>{
  if(!event.target.closest('.bet-stepper')) closeBetMenu();
});
document.addEventListener('keydown',event=>{
  if(event.key==='Escape') closeBetMenu();
});
autoBtn.addEventListener('click',()=>{
  st.autoOn=!st.autoOn;
  autoBtn.classList.toggle('is-active',st.autoOn);
  updateBetControls();
  if(st.autoOn&&!st.busy&&!st.pendingRound) { clearTimeout(st.autoTimer); st.autoTimer=setTimeout(()=>doSpin(false),200); }
  else if(!st.autoOn) clearTimeout(st.autoTimer);
});
speedRange.addEventListener('input',()=>{
  st.speed=Number(speedRange.value)||1;
  st.turboOn=st.speed>1;
  speedValue.textContent=`x${st.speed}`;
});
resetBtn.addEventListener('click',()=>{
  clearTimeout(st.autoTimer);
  Object.assign(st,{balance:100000,totalBet:0,totalWin:0,totalSpins:0,hitSpins:0,fgTriggers:0,
    roundCount:0,betIdx:4,autoOn:false,turboOn:false,speed:1,maxMultiplier:0,busy:false,pendingRound:null,pendingSpinIdx:0,displayWin:0});
  spinBtn.disabled=false; buyBtn.disabled=false; betBtn.disabled=false;
  spinBtn.textContent='Spin';
  autoBtn.classList.remove('is-active'); speedRange.value='1'; speedValue.textContent='x1';
  updateFeatureBar(null); updateCards(0);
  updateBetMenuSelection(); closeBetMenu(); updateBetControls();
  renderBoard(randomBoard()); renderWaysList([]); renderRngList(null); renderResultList(null);
setTimeout(initTrack,80);
  msgEl.textContent='Reset — press Spin';
});
debugModeInput.addEventListener('change',()=>{
  document.querySelectorAll('.debug-only, #controls').forEach(node=>node.classList.toggle('debug-hidden',!debugModeInput.checked));
});
languageSelect.addEventListener('change',()=>{
  const zh=languageSelect.value==='zh';
  normalBetBtn.textContent=zh?'一般投注':'Normal Bet';
  buyBtn.textContent=zh?'購買特色 (100X)':'Buy Feature (100X)';
  helpBtn.textContent='HELP';
});
helpBtn.addEventListener('click',()=>helpDialog.showModal());
closeHelpBtn.addEventListener('click',()=>helpDialog.close());
helpDialog.addEventListener('click',event=>{if(event.target===helpDialog) helpDialog.close();});

// ─── INIT ────────────────────────────────────────────────────────────────────
renderBetMenu();
updateFeatureBar(null); updateCards(0);
updateBetControls();
renderBoard(randomBoard()); renderWaysList([]); renderRngList(null); renderResultList(null);
setTimeout(initTrack,80);
