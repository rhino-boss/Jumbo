"""H039 急速糖果 2 (Candy Rush 2) simulator（Numba 版）.

盤面 5x5、Cluster Pay（上下左右相連 >= 4）、Cascade、位置倍數（每次消除 +1，計分乘全盤倍數總和）。
玩法定義見 ``game_rule.md``，正式實作以 Demo ``index.html`` 的 JS 為準，本程式逐條對照移植：
  boardFromStops／reelBoard → _resolve 開頭的盤面生成、_spin 的停點抽取
  buyEntryBoard             → _buy_entry
  findClusters              → _scan_clusters
  cascade                   → _resolve 內的掉落補牌
  runSpin                   → _spin ＋ _resolve
  runFreeGames              → _free_session
  computeRound／drawCard／cardsFor／inRange → simulate_chunk、_card_spin、_card_feature

執行參數一律來自 Config（config_01a.js：base＝基礎數學、tiers.<層級>＝卡片權重），本程式不重複維護
輪帶、賠率、底板權重、FG 場數或卡片權重。Runner、BATCH_RUNS、Console 欄位與 Excel 報表版面依
``專案需知/開發規範/模擬程式規範.md``；Card System 依 ``Omniplay/數學模型規範.md`` 第 2 章。

本作目前只有 Oldhand、只有 92A：沒有 Newbie、沒有押注分層、沒有 OP Jackpot，規範中這些欄位
（bet_tier、link_enabled、rtp_link、rtp_bonus、*_newbie、檔名的 bet_tier 段）一律不輸出，不捏造參數。

執行：py -B simulator.py（不留 __pycache__；Numba 編譯快取放系統暫存資料夾）。
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

# Numba 編譯快取放系統暫存資料夾，不在專案資料夾留 __pycache__；Config 以陣列參數傳入，快取不會吃到舊參數
os.environ["NUMBA_CACHE_DIR"] = str(Path(tempfile.gettempdir()) / "h039_numba")
sys.dont_write_bytecode = True

import numpy as np
from numba import njit

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

# ===== User Settings =====

CONFIG_FILE = "config_01a.js"   # 一個產線的一個系列一份 config：config_<產線><系列>.js（產線 01、系列 A）
CONFIG_TIER = "92A"   # 目前只有 92A（Oldhand），沒有押注分層，不做 AUTO 選組（模擬程式規範 §1.2.3 不適用）
TOTAL_ROUNDS = 100_000
BASE_BET_SETTING = 1.0
BET_MODE = 0  # 0 = Normal Bet, 1 = Extra Bet, 2 = Buy Feature
CARD_SYSTEM_ENABLED = False
CARD_SYSTEM_IS_NEWBIE = False

RUN_ALL_COMBINATIONS = True
BATCH_RUNS = [
    # --- 區塊 1：測試（流程與報表驗證，Card On，NB／EB／BF 各 10^5）---
    {"config_file": "config_01a.js", "tier": "92A", "bet_mode": 0,
     "total_rounds": 10**5, "card_system_enabled": True, "card_system_is_newbie": False, "base_bet": 1.0},
    {"config_file": "config_01a.js", "tier": "92A", "bet_mode": 1,
     "total_rounds": 10**5, "card_system_enabled": True, "card_system_is_newbie": False, "base_bet": 1.0},
    {"config_file": "config_01a.js", "tier": "92A", "bet_mode": 2,
     "total_rounds": 10**5, "card_system_enabled": True, "card_system_is_newbie": False, "base_bet": 1.0},
    # --- 區塊 2：自然機率（Card Off；規範場次 NB／EB 10^9、BF 10^8，≥10^6 一律丟模擬機 ssh sim 跑）---
    # 要跑哪些 Bet Mode 需先與使用者確認（規範 §1.2.2）；BF 權重若共用 NB FG 分布則不必另跑 BF。
    # {"config_file": "config_01a.js", "tier": "92A", "bet_mode": 0,
    #  "total_rounds": 10**9, "card_system_enabled": False, "card_system_is_newbie": False, "base_bet": 1.0},
    # {"config_file": "config_01a.js", "tier": "92A", "bet_mode": 1,
    #  "total_rounds": 10**9, "card_system_enabled": False, "card_system_is_newbie": False, "base_bet": 1.0},
    # {"config_file": "config_01a.js", "tier": "92A", "bet_mode": 2,
    #  "total_rounds": 10**8, "card_system_enabled": False, "card_system_is_newbie": False, "base_bet": 1.0},
    # --- 區塊 3：SCR（Card On、彩金關；NB／EB 10^8、BF 10^7）---
    # 本作目前沒有 OP Jackpot，SCR 只照規範量測輸出，暫無使用處；之後接彩金時再啟用。
    # {"config_file": "config_01a.js", "tier": "92A", "bet_mode": 0,
    #  "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False, "base_bet": 1.0},
    # --- 區塊 4：正式模擬（Card On；NB／EB 10^8、BF 10^7）---
    # 目前卡片權重是舊盤面（逐格抽）解的，尚未依輪帶版自然機率重解，重解後再啟用。
    # {"config_file": "config_01a.js", "tier": "92A", "bet_mode": 0,
    #  "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False, "base_bet": 1.0},
    # {"config_file": "config_01a.js", "tier": "92A", "bet_mode": 1,
    #  "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False, "base_bet": 1.0},
    # {"config_file": "config_01a.js", "tier": "92A", "bet_mode": 2,
    #  "total_rounds": 10**7, "card_system_enabled": True, "card_system_is_newbie": False, "base_bet": 1.0},
]
WORKERS = max(1, min(24, os.cpu_count() or 1))   # ProcessPoolExecutor 行程數（每個行程獨立 RNG）
OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = True
RUN_SINGLE_SPIN_DEBUG = False     # True＝固定 Seed、單執行緒、逐局 Trace（同 --trace N）
DEBUG_ROUNDS = 3
RNG_SEED = 39_039

MODE_NORMALBET = 0
MODE_EXTRABET = 1
MODE_FEATUREBUY = 2
MODE_KEY = {MODE_NORMALBET: "normal_bet", MODE_EXTRABET: "extra_bet", MODE_FEATUREBUY: "buy_feature"}

# Buy Feature 入場盤的 C1 顆數：index.html buyEntryBoard（cols.slice(0, 3)）與 computeRound（fgAward(3)）寫死為 3，Config 無此欄位
BUY_ENTRY_SCATTER = 3

# 報表倍率區間（Multiplier Line／Pay Range 用；與卡片區間上限一致，載入時會檢查）
MULTIPLIER_THRESHOLDS = (
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50,
    60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 250, 300, 350, 400, 450,
    500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000,
    2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000,
    20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000, 9999999,
)
NBUCKET = len(MULTIPLIER_THRESHOLDS)

CFG: dict[str, Any] = {}
CFG_RTP: dict[str, Any] = {}


# ===== Config =====

def resolve_base_dir() -> Path:
    base = Path(__file__).resolve().parent
    if not (base / CONFIG_FILE).exists():
        raise FileNotFoundError(f"找不到 {CONFIG_FILE}，請在 H039 專案資料夾執行。")
    return base


BASE_DIR = resolve_base_dir()


def load_js_config(path: Path) -> dict[str, Any]:
    """config_01a.js：`window.H039_CONFIG_01A = {純 JSON};`（註解不含大括號）。取第一個 { 到最後一個 } 直接解析。"""
    text = path.read_text(encoding="utf-8")
    return json.loads(text[text.index("{"):text.rindex("}") + 1])


def load_config(path: Path, tier: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """回傳 (base, base 疊上 tiers[tier])；source 只作說明不疊入。檔內沒有該層級時第二個值為 {}。"""
    data = load_js_config(path)
    if data.get("game_id") != "H039" or "base" not in data or "tiers" not in data:
        raise ValueError(f"{path.name} 不是 H039 的 config_<產線><系列>.js 格式")
    base = data["base"]
    if tier not in data["tiers"]:
        return base, {}
    return base, {**base, **{k: v for k, v in data["tiers"][tier].items() if k != "source"}}


def read_version_txt() -> str | None:
    path = BASE_DIR / "Source" / "version.txt"
    return path.read_text(encoding="utf-8").strip() if path.exists() else None


def validate_config_pair(natural: dict[str, Any], rtp: dict[str, Any] | None,
                         natural_name: str, rtp_name: str) -> None:
    if natural.get("game_id") != "H039":
        raise ValueError(f"{natural_name} 的 game_id 必須為 H039")
    version = str(natural.get("excel_version", ""))
    if not version.isdigit() or len(version) != 1:
        raise ValueError(f"{natural_name} 的 excel_version 必須為 1 碼，目前為 {version!r}")
    # 本程式實作的玩法前提；Config 改了這些就必須先改程式，不得靜默照舊算
    if natural.get("refill_mode") != "drop":
        raise ValueError(f"refill_mode 只支援 drop，目前為 {natural.get('refill_mode')!r}")
    pm = natural.get("position_multiplier") or {}
    if pm.get("score_scope") != "board_sum" or pm.get("bg_reset") != "per_spin" or pm.get("fg_reset") != "per_session":
        raise ValueError("position_multiplier 的 score_scope／bg_reset／fg_reset 與本程式實作不符")
    size = int(natural["board_size"])
    nsym = len(natural["symbol_codes"])
    sc = int(natural["scatter_index"])
    if nsym > MAX_SYM or len(natural["pay_table"][0]) > MAX_PAY:
        raise ValueError("符號數或賠率欄數超過本程式統計陣列上限")
    if len(natural["pay_table"]) != nsym - 1 or sc != nsym - 1:
        raise ValueError("pay_table 列數必須等於一般符號數，且 Scatter 必須是最後一個符號索引")
    for scene in ("bg", "fg"):
        strips = natural["reels"][scene]
        if len(strips) != size:
            raise ValueError(f"reels.{scene} 必須有 {size} 條輪帶")
        for i, strip in enumerate(strips):
            if len(strip) < size or any((not isinstance(v, int)) or v < 0 or v >= nsym for v in strip):
                raise ValueError(f"reels.{scene}[{i}] 內容不合法")
            if "reel_length" in natural and len(strip) != int(natural["reel_length"]):
                raise ValueError(f"reels.{scene}[{i}] 長度 {len(strip)} ≠ reel_length {natural['reel_length']}")
    # buyEntryBoard 用 indexOf(SC) 取單一位置，並假設視窗內最多 1 顆 C1：BG 輪帶每條必須剛好 1 顆 C1
    for i, strip in enumerate(natural["reels"]["bg"]):
        if strip.count(sc) != 1:
            raise ValueError(f"reels.bg[{i}] 的 C1 顆數必須為 1（Buy Feature 入場盤的前提），目前 {strip.count(sc)}")
    plates = natural["extra_bet_plates"]
    if len(plates["values"]) != len(plates["value_weights"]) or len(plates["count_values"]) != len(plates["count_weights"]):
        raise ValueError("extra_bet_plates 的值與權重長度不一致")
    if max(plates["count_values"]) > size * size or min(plates["value_weights"] + plates["count_weights"]) < 0:
        raise ValueError("extra_bet_plates 內容不合法")
    if rtp is None:
        return
    if rtp.get("game_id") != natural.get("game_id"):
        raise ValueError(f"{rtp_name} 與 {natural_name} 的 game_id 不一致")
    rtp_version = str(rtp.get("excel_version", ""))
    parts = rtp_version.split(".")
    if len(parts) != 4 or not all(p.isdigit() for p in parts):
        raise ValueError(f"{rtp_name} 的 excel_version 必須為 4 碼，目前為 {rtp_version!r}")
    if parts[0] != version:
        raise ValueError(f"{rtp_name} 的版本第 1 碼 {parts[0]} 必須等於基礎模型版本 {version}")
    txt = read_version_txt()
    if txt is not None and txt != rtp_version:
        print(f"[warn] Source/version.txt（{txt}）與 {rtp_name} 的 excel_version（{rtp_version}）不一致，請確認版本。")


# ===== 遊戲核心（Numba）=====
#
# 每個「嘗試」（BG 一轉、或 FG 一整場）的統計寫在一條 int64 向量（acc_i）＋ float64 向量（acc_f）；
# 卡片重骰時整條歸零重來，被重骰掉的轉／場不會進統計。

MAX_SYM = 8        # 符號種類上限（統計陣列版面；目前 7：M1~M6＋C1）
MAX_PAY = 8        # 賠率欄數上限（目前 7：4/5/6/7/8/9/10+）
COMBO_K = 12       # 連消次數統計 0~11+

A_SPINS, A_HIT, A_CASC, A_SPECIAL, A_RETRIG, A_REMOVED, A_MAXSUM, A_SUMEND, A_PLATESUM, A_MAXCASC = range(10)
A_COMBO = 10                              # [COMBO_K] 每轉連消次數分布
A_INIT = A_COMBO + COMBO_K                # [MAX_SYM] 開場盤面符號數
A_DROP = A_INIT + MAX_SYM                 # [MAX_SYM] 掉落補入符號數
A_SYMHIT = A_DROP + MAX_SYM               # [MAX_SYM*MAX_PAY] (符號, 賠率欄) Cluster 命中數
ACC_I_LEN = A_SYMHIT + MAX_SYM * MAX_PAY
F_PAY = 0
F_SYMPAY = 1                              # [MAX_SYM*MAX_PAY] (符號, 賠率欄) 派彩
ACC_F_LEN = F_SYMPAY + MAX_SYM * MAX_PAY

# 全域（局層級）計數
(G_ROUNDS, G_FGTRIG, G_TRIGCNT, G_RETRY, G_RLE, G_RLBGR, G_RLBGFG, G_RLFG,
 G_ENTRY, G_ENTRYTRY, G_BGHIT_NOTRIG) = range(11)
GI_LEN = 11
H_COIN, H_PBG, H_PFG, H_WX, H_WX2, H_MAXWX, H_TRIGPAY, H_FGSUMEND, H_MAXBGX, H_MAXFGX = range(10)
GF_LEN = 10
# Multiplier Line 分桶
(B_BGCNT, B_FGCNT, B_BFCNT, B_TRIGCNT, B_FGHIT, B_FGSPINS, B_BGSUM, B_FGSUM, B_PRCNT) = range(9)
BI_LEN = 9
B_BGPAY, B_FGPAY, B_BFPAY, B_TRIGPAY, B_PRPAY = range(5)
BF_LEN = 5

# 卡組：0＝該模式的 weight_bg、1＝該模式的 weight_fg（BF 只有 weight_fg）
SEC_BG, SEC_FG = 0, 1
CARD_RANGE, CARD_FREE = 0, 1

# Numba 核心收一般 tuple；欄位位置常數如下
(_D_STRIPS, _D_SLEN, _D_PAY, _D_PARAM, _D_FGAWARD, _D_PCV, _D_PCC, _D_PV, _D_PVC,
 _D_CARD_CUM, _D_CARD_N, _D_CARD_TOT, _D_CARD_TYPE, _D_CARD_MIN, _D_CARD_MAX,
 _D_THRESHOLDS, _D_SCPOS) = range(17)
P_SIZE, P_MINC, P_SC, P_STEP, P_FGCAP, P_ENTRYSC, P_SAMECLEAR = range(7)
(_W_BOARD, _W_MULT, _W_REM, _W_VIS, _W_STACK, _W_CELLS, _W_PTR, _W_STOPS,
 _W_CLSYM, _W_CLSIZE, _W_CLPAY, _W_BG_I, _W_BG_F, _W_SESS_I, _W_SESS_F, _W_PLATES, _W_COLS) = range(17)

# Trace 紀錄碼（float64 流水帳，只有 Trace 模式才配置）
T_SPIN, T_STEP, T_END, T_CARD, T_ACCEPT, T_FGSTART, T_RETRIG, T_ENTRY, T_PLATES, T_ROUND = range(1, 11)


def _cum_array(weights) -> tuple[np.ndarray, float]:
    out = np.cumsum([max(0.0, float(w)) for w in weights]).astype(np.float64)
    return out, float(out[-1]) if len(out) else 0.0


def card_sections(rtp_config: dict[str, Any] | None, bet_mode: int) -> tuple[list[dict], list[dict]]:
    """同 index.html cardsFor：card_system.oldhand.{normal_bet,extra_bet,buy_feature}.{weight_bg,weight_fg}。"""
    seg = (((rtp_config or {}).get("card_system") or {}).get("oldhand") or {}).get(MODE_KEY[bet_mode]) or {}
    bg = [] if bet_mode == MODE_FEATUREBUY else list(seg.get("weight_bg") or [])
    return bg, list(seg.get("weight_fg") or [])


def section_cap(cards: list[dict]) -> float:
    """卡組「最高有權重 range 卡」的上限；沒有則無限大。"""
    caps = [float(c["max"]) for c in cards if c.get("type") == "range" and float(c.get("weight", 0)) > 0]
    return max(caps) if caps else math.inf


def build_game_data(config: dict[str, Any], rtp_config: dict[str, Any] | None, bet_mode: int):
    """把 Config 正規化成核心用的固定型別陣列。"""
    size = int(config["board_size"])
    sc = int(config["scatter_index"])
    lmax = max(len(s) for scene in ("bg", "fg") for s in config["reels"][scene])
    strips = np.zeros((2, size, lmax), np.int64)
    slen = np.zeros((2, size), np.int64)
    for si, scene in enumerate(("bg", "fg")):
        for c, strip in enumerate(config["reels"][scene]):
            strips[si, c, :len(strip)] = strip
            slen[si, c] = len(strip)
    pay = np.array(config["pay_table"], np.float64)
    awards = {int(k): int(v) for k, v in config["fg_awards"].items()}
    maxkey = max(awards)
    # fgAward(n) = FG_AWARD[min(n, FG_MAXKEY)] || 0；索引 0..size（一軸最多 1 顆 C1）
    fg_award = np.array([awards.get(min(n, maxkey), 0) for n in range(size * size + 1)], np.int64)
    plates = config["extra_bet_plates"]
    pcc, _ = _cum_array(plates["count_weights"])
    pvc, _ = _cum_array(plates["value_weights"])
    param = np.array([size, int(config["min_cluster"]), sc, int(config["position_multiplier"]["step"]),
                      int(config["fg_cap"]), BUY_ENTRY_SCATTER,
                      1 if config.get("same_symbol_clear") is True else 0], np.int64)
    scpos = np.array([list(s).index(sc) for s in config["reels"]["bg"]], np.int64)

    sections = card_sections(rtp_config, bet_mode)
    ncard = max(1, max(len(s) for s in sections))
    card_cum = np.zeros((2, ncard), np.float64)
    card_n = np.zeros(2, np.int64)
    card_tot = np.zeros(2, np.float64)
    card_type = np.zeros((2, ncard), np.int64)
    card_min = np.zeros((2, ncard), np.float64)
    card_max = np.zeros((2, ncard), np.float64)
    for si, cards in enumerate(sections):
        if not cards:
            continue
        if any(float(c.get("weight", 0)) < 0 for c in cards):
            raise ValueError("卡片權重不得小於 0")
        cum, tot = _cum_array([c.get("weight", 0) for c in cards])
        card_cum[si, :len(cards)] = cum
        card_cum[si, len(cards):] = tot
        card_n[si] = len(cards)
        card_tot[si] = tot
        for i, c in enumerate(cards):
            if c.get("type") == "free_game":
                card_type[si, i] = CARD_FREE
            elif c.get("type") == "range":
                card_min[si, i] = float(c["min"])
                card_max[si, i] = float(c["max"])
                if float(c.get("weight", 0)) > 0 and float(c["max"]) not in MULTIPLIER_THRESHOLDS:
                    raise ValueError(f"卡片區間上限 {c['max']} 不在報表倍率區間內，請補齊倍率區間")
            else:
                raise ValueError(f"不支援的卡片類型 {c.get('type')!r}")
    return (
        strips, slen, pay, param, fg_award,
        np.array(plates["count_values"], np.int64), pcc, np.array(plates["values"], np.int64), pvc,
        card_cum, card_n, card_tot, card_type, card_min, card_max,
        np.array(MULTIPLIER_THRESHOLDS, np.float64), scpos,
    )


@njit(nogil=True, cache=True)
def _pick(cum, n, total):
    """依累積權重抽一個索引（等同 index.html rngW／drawCard 的逐項相減）。"""
    pos = np.random.random() * total
    lo = 0
    hi = n
    while lo < hi:
        mid = (lo + hi) >> 1
        if cum[mid] <= pos:
            lo = mid + 1
        else:
            hi = mid
    return lo if lo < n - 1 else n - 1


@njit(nogil=True, cache=True)
def _lg(log, lp, v):
    p = lp[0]
    if p < log.shape[0]:
        log[p] = v
    lp[0] = p + 1


@njit(nogil=True, cache=True)
def _lg_grid(log, lp, g):
    for r in range(g.shape[0]):
        for c in range(g.shape[1]):
            _lg(log, lp, g[r, c])


@njit(nogil=True, cache=True)
def _scan_clusters(board, n, minc, sc, vis, rem, stack, cells, cl_sym, cl_size):
    """同 findClusters：依 r、c 順序掃描，上下左右相連同符號 >= minc 為一組；C1 不參與。
    回傳組數；rem 標出所有成立 Cluster 的格子。"""
    for r in range(n):
        for c in range(n):
            vis[r, c] = 0
            rem[r, c] = 0
    ncl = 0
    for r in range(n):
        for c in range(n):
            if vis[r, c] != 0:
                continue
            sym = board[r, c]
            if sym == sc:
                continue
            top = 0
            stack[0] = r * n + c
            vis[r, c] = 1
            cnt = 0
            while top >= 0:
                k = stack[top]
                top -= 1
                cells[cnt] = k
                cnt += 1
                cr = k // n
                cc = k % n
                if cr > 0 and vis[cr - 1, cc] == 0 and board[cr - 1, cc] == sym:
                    vis[cr - 1, cc] = 1
                    top += 1
                    stack[top] = k - n
                if cr < n - 1 and vis[cr + 1, cc] == 0 and board[cr + 1, cc] == sym:
                    vis[cr + 1, cc] = 1
                    top += 1
                    stack[top] = k + n
                if cc > 0 and vis[cr, cc - 1] == 0 and board[cr, cc - 1] == sym:
                    vis[cr, cc - 1] = 1
                    top += 1
                    stack[top] = k - 1
                if cc < n - 1 and vis[cr, cc + 1] == 0 and board[cr, cc + 1] == sym:
                    vis[cr, cc + 1] = 1
                    top += 1
                    stack[top] = k + 1
            if cnt >= minc:
                cl_sym[ncl] = sym
                cl_size[ncl] = cnt
                ncl += 1
                for i in range(cnt):
                    rem[cells[i] // n, cells[i] % n] = 1
    return ncl


@njit(nogil=True, cache=True)
def _resolve(D, W, scene, bet, acc_i, acc_f, log, lp):
    """一次 Spin 的完整計算（停點已放在 W[_W_STOPS]，位置倍數 W[_W_MULT] 由呼叫端準備）。
    同 boardFromStops ＋ runSpin 的 while 迴圈 ＋ cascade。回傳 (得分, 連消次數, 最終 C1 數, 最終全盤倍數和)。"""
    P = D[_D_PARAM]
    n = P[P_SIZE]
    minc = P[P_MINC]
    sc = P[P_SC]
    step = P[P_STEP]
    strips = D[_D_STRIPS]
    slen = D[_D_SLEN]
    pay = D[_D_PAY]
    npay = pay.shape[1]
    board = W[_W_BOARD]
    mult = W[_W_MULT]
    rem = W[_W_REM]
    ptr = W[_W_PTR]
    stops = W[_W_STOPS]
    cl_sym = W[_W_CLSYM]
    cl_size = W[_W_CLSIZE]
    cl_pay = W[_W_CLPAY]
    tr = log.shape[0] > 1

    # 盤面：視窗第 r 列（0 最上）＝ strip[(s + r) % L]；下一顆要掉的輪帶位置 ptr = s - 1
    msum = 0
    for c in range(n):
        L = slen[scene, c]
        s = stops[c]
        for r in range(n):
            v = strips[scene, c, (s + r) % L]
            board[r, c] = v
            acc_i[A_INIT + v] += 1
            msum += mult[r, c]
        ptr[c] = s - 1 if s > 0 else L - 1
    if tr:
        _lg(log, lp, T_SPIN)
        _lg(log, lp, scene)
        for c in range(n):
            _lg(log, lp, stops[c])
        _lg_grid(log, lp, board)
        _lg_grid(log, lp, mult)

    total = 0.0
    casc = 0
    while True:
        ncl = _scan_clusters(board, n, minc, sc, W[_W_VIS], rem, W[_W_STACK], W[_W_CELLS], cl_sym, cl_size)
        if ncl == 0:
            break
        # 每組各自計分，都乘「本段消除前」的全盤倍數和（0 視為 1）
        eff = msum if msum > 0 else 1
        step_pay = 0.0
        for i in range(ncl):
            sym = cl_sym[i]
            idx = cl_size[i] - minc
            if idx > npay - 1:
                idx = npay - 1
            p = pay[sym, idx] * bet * eff
            cl_pay[i] = p
            step_pay += p
            acc_i[A_SYMHIT + sym * MAX_PAY + idx] += 1
            acc_f[F_SYMPAY + sym * MAX_PAY + idx] += p
        total += step_pay
        casc += 1
        # 同符號連帶消除（same_symbol_clear）：盤面上與得分 Cluster 同符號的其餘格子一併消除（rem=2），不計分、位置倍數不 +1
        if P[P_SAMECLEAR] != 0:
            for r in range(n):
                for c in range(n):
                    if rem[r, c] == 0:
                        v = board[r, c]
                        for i in range(ncl):
                            if cl_sym[i] == v:
                                rem[r, c] = 2
                                break
        if tr:
            _lg(log, lp, T_STEP)
            _lg(log, lp, msum)
            _lg(log, lp, eff)
            _lg(log, lp, step_pay)
            _lg(log, lp, ncl)
            for i in range(ncl):
                _lg(log, lp, cl_sym[i])
                _lg(log, lp, cl_size[i])
                _lg(log, lp, cl_pay[i])
            _lg_grid(log, lp, rem)
        # 計分後，Cluster 本身的每一格位置倍數 +step（連帶消除的格子不加）
        for r in range(n):
            for c in range(n):
                if rem[r, c] != 0:
                    acc_i[A_REMOVED] += 1
                    if rem[r, c] == 1:
                        mult[r, c] += step
                        msum += step
        # 掉落補牌：存活符號依重力下移（C1 不消除）；空位由輪帶往上接著掉，最下面的空位先補。
        # 輪帶讀到 C1 時該軸已有 C1 就跳過這顆。
        for c in range(n):
            L = slen[scene, c]
            w = n - 1
            has_sc = False
            for r in range(n - 1, -1, -1):
                if rem[r, c] == 0:
                    v = board[r, c]
                    board[w, c] = v
                    if v == sc:
                        has_sc = True
                    w -= 1
            p = ptr[c]
            while w >= 0:
                while True:
                    sym = strips[scene, c, p]
                    p = p - 1 if p > 0 else L - 1
                    if sym != sc:
                        break
                    if not has_sc:
                        has_sc = True
                        break
                board[w, c] = sym
                acc_i[A_DROP + sym] += 1
                w -= 1
            ptr[c] = p
        if tr:
            _lg_grid(log, lp, board)
            _lg_grid(log, lp, mult)

    scatter = 0
    for r in range(n):
        for c in range(n):
            if board[r, c] == sc:
                scatter += 1
    acc_i[A_SPINS] += 1
    acc_i[A_CASC] += casc
    acc_i[A_COMBO + (casc if casc < COMBO_K - 1 else COMBO_K - 1)] += 1
    if casc > 0:
        acc_i[A_HIT] += 1
    if scatter > 0:
        acc_i[A_SPECIAL] += 1      # C1 不消除，最終盤面有 C1 ⇔ 這一轉盤面出現過 C1
    if msum > acc_i[A_MAXSUM]:
        acc_i[A_MAXSUM] = msum
    if casc > acc_i[A_MAXCASC]:
        acc_i[A_MAXCASC] = casc
    acc_i[A_SUMEND] += msum
    acc_f[F_PAY] += total
    if tr:
        _lg(log, lp, T_END)
        _lg(log, lp, total)
        _lg(log, lp, casc)
        _lg(log, lp, scatter)
        _lg(log, lp, msum)
    return total, casc, scatter, msum


@njit(nogil=True, cache=True)
def _spin(D, W, scene, plates_on, bet, acc_i, acc_f, log, lp):
    """同 runSpin：抽停點（reelBoard）；Extra Bet 開場隨機不重複位置放倍數底板，直接加到該格位置倍數。"""
    P = D[_D_PARAM]
    n = P[P_SIZE]
    slen = D[_D_SLEN]
    stops = W[_W_STOPS]
    for c in range(n):
        stops[c] = int(np.random.random() * slen[scene, c])
    if plates_on:
        mult = W[_W_MULT]
        plates = W[_W_PLATES]
        count = D[_D_PCV][_pick(D[_D_PCC], len(D[_D_PCV]), D[_D_PCC][-1])]
        placed = 0
        while placed < count:
            key = int(np.random.random() * n * n)
            dup = False
            for i in range(placed):
                if plates[i, 0] == key:
                    dup = True
                    break
            if dup:
                continue
            value = D[_D_PV][_pick(D[_D_PVC], len(D[_D_PV]), D[_D_PVC][-1])]
            mult[key // n, key % n] += value
            plates[placed, 0] = key
            plates[placed, 1] = value
            placed += 1
            acc_i[A_PLATESUM] += value
        if log.shape[0] > 1:
            _lg(log, lp, T_PLATES)
            _lg(log, lp, count)
            for i in range(count):
                _lg(log, lp, plates[i, 0])
                _lg(log, lp, plates[i, 1])
    return _resolve(D, W, scene, bet, acc_i, acc_f, log, lp)


@njit(nogil=True, cache=True)
def _base_spin(D, W, plates_on, bet, log, lp):
    """BG 一轉：位置倍數歸零後轉一次，統計寫入 W[_W_BG_I]／W[_W_BG_F]。"""
    W[_W_BG_I][:] = 0
    W[_W_BG_F][:] = 0.0
    W[_W_MULT][:, :] = 0
    return _spin(D, W, 0, plates_on, bet, W[_W_BG_I], W[_W_BG_F], log, lp)


@njit(nogil=True, cache=True)
def _free_session(D, W, award, bet, log, lp):
    """同 runFreeGames：一段完整 FG（含 Retrigger），位置倍數整場保留；用 FG 輪帶。
    結果寫入 W[_W_SESS_I]／W[_W_SESS_F]，回傳最後的全盤倍數和。"""
    P = D[_D_PARAM]
    cap = P[P_FGCAP]
    fg_award = D[_D_FGAWARD]
    sess_i = W[_W_SESS_I]
    sess_f = W[_W_SESS_F]
    sess_i[:] = 0
    sess_f[:] = 0.0
    W[_W_MULT][:, :] = 0
    tr = log.shape[0] > 1
    if tr:
        _lg(log, lp, T_FGSTART)
        _lg(log, lp, award)
    left = award
    played = 0
    msum = 0
    while left > 0 and played < cap:
        _t, _c, scatter, msum = _spin(D, W, 1, False, bet, sess_i, sess_f, log, lp)
        left -= 1
        played += 1
        if scatter >= 3 and played + left < cap:
            add = fg_award[scatter]
            if add > cap - played - left:
                add = cap - played - left
            left += add
            if add > 0:
                sess_i[A_RETRIG] += 1
            if tr:
                _lg(log, lp, T_RETRIG)
                _lg(log, lp, scatter)
                _lg(log, lp, add)
    return msum


@njit(nogil=True, cache=True)
def _buy_entry(D, W, log, lp):
    """同 buyEntryBoard：BG 輪帶，隨機 3 軸停在看得到 C1 的位置、其餘軸停在沒有 C1 的位置；有 Cluster 就整盤重抽。
    只供畫面（不計分、不連消），這裡照做以驗證前提並回傳重抽次數。"""
    P = D[_D_PARAM]
    n = P[P_SIZE]
    sc = P[P_SC]
    k = P[P_ENTRYSC]
    strips = D[_D_STRIPS]
    slen = D[_D_SLEN]
    scpos = D[_D_SCPOS]
    board = W[_W_BOARD]
    cols = W[_W_COLS]
    stops = W[_W_STOPS]
    tries = 0
    while True:
        tries += 1
        for i in range(n):
            cols[i] = i
        for i in range(n - 1, 0, -1):
            j = int(np.random.random() * (i + 1))
            t = cols[i]
            cols[i] = cols[j]
            cols[j] = t
        for c in range(n):
            L = slen[0, c]
            is_sc = False
            for i in range(k):
                if cols[i] == c:
                    is_sc = True
            if is_sc:
                stops[c] = (scpos[c] - int(np.random.random() * n) + L) % L
            else:
                while True:
                    st = int(np.random.random() * L)
                    d = (scpos[c] - st + L) % L
                    if d >= n:
                        stops[c] = st
                        break
        for c in range(n):
            L = slen[0, c]
            for r in range(n):
                board[r, c] = strips[0, c, (stops[c] + r) % L]
        ncl = _scan_clusters(board, n, P[P_MINC], sc, W[_W_VIS], W[_W_REM], W[_W_STACK], W[_W_CELLS],
                             W[_W_CLSYM], W[_W_CLSIZE])
        if ncl == 0:
            break
    scatter = 0
    for r in range(n):
        for c in range(n):
            if board[r, c] == sc:
                scatter += 1
    if log.shape[0] > 1:
        _lg(log, lp, T_ENTRY)
        _lg(log, lp, tries)
        for c in range(n):
            _lg(log, lp, stops[c])
        _lg_grid(log, lp, board)
    return tries, scatter


@njit(nogil=True, cache=True)
def _pick_card(D, sec, card_draws, log, lp):
    idx = _pick(D[_D_CARD_CUM][sec], D[_D_CARD_N][sec], D[_D_CARD_TOT][sec])
    card_draws[sec, idx] += 1
    if log.shape[0] > 1:
        _lg(log, lp, T_CARD)
        _lg(log, lp, sec)
        _lg(log, lp, idx)
    return idx


@njit(nogil=True, cache=True)
def _card_feature(D, W, award, bet, retry_limit, gi, card_draws, log, lp):
    """FG 卡（BF 為整局）：固定一張卡，整場重跑直到 FG 得分 ÷ 基礎押注落在 (min, max]；最多 retry_limit 次，
    超過就保留最後一場並記錄失敗。卡組總權重為 0 時不套卡（同 drawCard 回傳 null）。"""
    if D[_D_CARD_TOT][SEC_FG] <= 0.0:
        return _free_session(D, W, award, bet, log, lp)
    idx = _pick_card(D, SEC_FG, card_draws, log, lp)
    lo = D[_D_CARD_MIN][SEC_FG, idx]
    hi = D[_D_CARD_MAX][SEC_FG, idx]
    lp0 = lp[0]
    msum = 0
    tries = 0
    for _ in range(retry_limit):
        lp[0] = lp0
        msum = _free_session(D, W, award, bet, log, lp)
        ratio = W[_W_SESS_F][F_PAY] / bet
        if lo < ratio and ratio <= hi:
            if log.shape[0] > 1:
                _lg(log, lp, T_ACCEPT)
                _lg(log, lp, tries)
                _lg(log, lp, 1)
            return msum
        gi[G_RETRY] += 1
        tries += 1
    gi[G_RLE] += 1
    gi[G_RLFG] += 1
    if log.shape[0] > 1:
        _lg(log, lp, T_ACCEPT)
        _lg(log, lp, tries)
        _lg(log, lp, 0)
    return msum


@njit(nogil=True, cache=True)
def _card_spin(D, W, plates_on, bet, trig_cap, retry_limit, gi, card_draws, log, lp):
    """BG 卡：固定一張卡，整把重骰直到符合。
    range 卡：不觸發 FG 且 BG 得分 ÷ 基礎押注落在 (min, max]。
    free_game 卡：觸發 FG 且 BG 得分 ≤ BG Trigger Cap（數學模型規範 §2.3 天花板）。"""
    idx = _pick_card(D, SEC_BG, card_draws, log, lp)
    want_fg = D[_D_CARD_TYPE][SEC_BG, idx] == 1
    lo = D[_D_CARD_MIN][SEC_BG, idx]
    hi = D[_D_CARD_MAX][SEC_BG, idx]
    lp0 = lp[0]
    res = (0.0, 0, 0, 0)
    tries = 0
    ok = 0
    for _ in range(retry_limit):
        lp[0] = lp0
        res = _base_spin(D, W, plates_on, bet, log, lp)
        ratio = res[0] / bet
        if want_fg:
            if res[2] >= 3 and ratio <= trig_cap:
                ok = 1
                break
        elif res[2] < 3 and lo < ratio and ratio <= hi:
            ok = 1
            break
        gi[G_RETRY] += 1
        tries += 1
    if ok == 0:
        gi[G_RLE] += 1
        if want_fg:
            gi[G_RLBGFG] += 1
        else:
            gi[G_RLBGR] += 1
    if log.shape[0] > 1:
        _lg(log, lp, T_ACCEPT)
        _lg(log, lp, tries)
        _lg(log, lp, ok)
    return res


@njit(nogil=True, cache=True)
def _threshold_index(thresholds, x):
    for i in range(len(thresholds)):
        if x <= thresholds[i]:
            return i
    return len(thresholds) - 1


@njit(nogil=True, cache=True)
def simulate_chunk(D, rounds, bet_mode, bet, wager, card_on, trig_cap, retry_limit, seed, log):
    """跑 rounds 局，回傳統計陣列。bet＝基礎押注（得分與卡片倍率分母），wager＝實際扣款。
    log 長度 > 1 時為 Trace 模式（單執行緒），把每一步寫進流水帳。"""
    np.random.seed(seed)
    P = D[_D_PARAM]
    n = P[P_SIZE]
    W = (
        np.zeros((n, n), np.int64), np.zeros((n, n), np.int64), np.zeros((n, n), np.int64),
        np.zeros((n, n), np.int64), np.zeros(n * n, np.int64), np.zeros(n * n, np.int64),
        np.zeros(n, np.int64), np.zeros(n, np.int64),
        np.zeros(n * n, np.int64), np.zeros(n * n, np.int64), np.zeros(n * n, np.float64),
        np.zeros(ACC_I_LEN, np.int64), np.zeros(ACC_F_LEN, np.float64),
        np.zeros(ACC_I_LEN, np.int64), np.zeros(ACC_F_LEN, np.float64),
        np.zeros((n * n, 2), np.int64), np.zeros(n, np.int64),
    )
    thresholds = D[_D_THRESHOLDS]
    nb = len(thresholds)
    lp = np.zeros(1, np.int64)
    gi = np.zeros(GI_LEN, np.int64)
    gf = np.zeros(GF_LEN, np.float64)
    gs_i = np.zeros((2, ACC_I_LEN), np.int64)
    gs_f = np.zeros((2, ACC_F_LEN), np.float64)
    bi = np.zeros((BI_LEN, nb), np.int64)
    bfl = np.zeros((BF_LEN, nb), np.float64)
    bcombo = np.zeros((2, nb, 5), np.int64)
    card_draws = np.zeros((2, D[_D_CARD_CUM].shape[1]), np.int64)
    hist_sc = np.zeros(n * n + 1, np.int64)          # 觸發 FG 時的 C1 顆數
    hist_spins = np.zeros(P[P_FGCAP] + 1, np.int64)  # FG 一場的實際轉數
    eb = bet_mode == 1
    bg_i = W[_W_BG_I]
    bg_f = W[_W_BG_F]
    sess_i = W[_W_SESS_I]
    sess_f = W[_W_SESS_F]
    fg_award = D[_D_FGAWARD]
    tr = log.shape[0] > 1

    for _ in range(rounds):
        pay_bg = 0.0
        pay_fg = 0.0
        fg_on = False
        fg_sum_end = 0
        res = (0.0, 0, 0, 0)
        if tr:
            _lg(log, lp, T_ROUND)
        if bet_mode == 2:
            # Buy Feature：入場盤（BG 輪帶、剛好 3 顆 C1、沒有 Cluster，不計分）→ 直接給 fgAward(3) 場 FG
            tries, scatter = _buy_entry(D, W, log, lp)
            if scatter != P[P_ENTRYSC]:
                raise RuntimeError("Buy Feature 入場盤的 C1 顆數不符")
            gi[G_ENTRY] += 1
            gi[G_ENTRYTRY] += tries
            award = fg_award[P[P_ENTRYSC]]
            if card_on:
                fg_sum_end = _card_feature(D, W, award, bet, retry_limit, gi, card_draws, log, lp)
            else:
                fg_sum_end = _free_session(D, W, award, bet, log, lp)
            fg_on = True
            pay_fg = sess_f[F_PAY]
            hist_sc[scatter] += 1
        else:
            if card_on:
                res = _card_spin(D, W, eb, bet, trig_cap, retry_limit, gi, card_draws, log, lp)
            else:
                res = _base_spin(D, W, eb, bet, log, lp)
            pay_bg = res[0]
            scatter = res[2]
            if scatter >= 3:
                award = fg_award[scatter]
                if card_on:
                    fg_sum_end = _card_feature(D, W, award, bet, retry_limit, gi, card_draws, log, lp)
                else:
                    fg_sum_end = _free_session(D, W, award, bet, log, lp)
                fg_on = True
                pay_fg = sess_f[F_PAY]
                hist_sc[scatter] += 1

        # --- 累計 ---
        gi[G_ROUNDS] += 1
        gf[H_COIN] += wager
        gf[H_PBG] += pay_bg
        gf[H_PFG] += pay_fg
        wx = (pay_bg + pay_fg) / wager
        gf[H_WX] += wx
        gf[H_WX2] += wx * wx
        if wx > gf[H_MAXWX]:
            gf[H_MAXWX] = wx
        if pay_bg / bet > gf[H_MAXBGX]:
            gf[H_MAXBGX] = pay_bg / bet
        if pay_fg / bet > gf[H_MAXFGX]:
            gf[H_MAXFGX] = pay_fg / bet
        pri = _threshold_index(thresholds, wx)
        bi[B_PRCNT, pri] += 1
        bfl[B_PRPAY, pri] += pay_bg + pay_fg
        if bet_mode != 2:
            m1 = gs_i[0, A_MAXSUM]
            m2 = gs_i[0, A_MAXCASC]
            for i in range(ACC_I_LEN):
                gs_i[0, i] += bg_i[i]
            gs_i[0, A_MAXSUM] = max(m1, bg_i[A_MAXSUM])
            gs_i[0, A_MAXCASC] = max(m2, bg_i[A_MAXCASC])
            for i in range(ACC_F_LEN):
                gs_f[0, i] += bg_f[i]
        if fg_on:
            gi[G_FGTRIG] += 1
            gf[H_FGSUMEND] += fg_sum_end
            hist_spins[sess_i[A_SPINS]] += 1
            m1 = gs_i[1, A_MAXSUM]
            m2 = gs_i[1, A_MAXCASC]
            for i in range(ACC_I_LEN):
                gs_i[1, i] += sess_i[i]
            gs_i[1, A_MAXSUM] = max(m1, sess_i[A_MAXSUM])
            gs_i[1, A_MAXCASC] = max(m2, sess_i[A_MAXCASC])
            for i in range(ACC_F_LEN):
                gs_f[1, i] += sess_f[i]

        # 倍率分桶：分母一律為基礎押注（數學模型規範 §2.5）
        if fg_on:
            fi = _threshold_index(thresholds, pay_fg / bet)
            if bet_mode == 2:
                bi[B_BFCNT, fi] += 1
                bfl[B_BFPAY, fi] += pay_fg
            else:
                gi[G_TRIGCNT] += 1
                gf[H_TRIGPAY] += pay_bg
                ti = _threshold_index(thresholds, pay_bg / bet)
                bi[B_TRIGCNT, ti] += 1
                bfl[B_TRIGPAY, ti] += pay_bg
                bi[B_FGCNT, fi] += 1
                bfl[B_FGPAY, fi] += pay_fg
            bi[B_FGSPINS, fi] += sess_i[A_SPINS]
            bi[B_FGHIT, fi] += sess_i[A_HIT]
            bi[B_FGSUM, fi] += fg_sum_end
            for k in range(1, COMBO_K):
                bcombo[1, fi, (k if k < 5 else 5) - 1] += sess_i[A_COMBO + k]
        else:
            # BG Multiplier Line 只計「未觸發 FG」的局
            idx = _threshold_index(thresholds, pay_bg / bet)
            bi[B_BGCNT, idx] += 1
            bfl[B_BGPAY, idx] += pay_bg
            bi[B_BGSUM, idx] += bg_i[A_SUMEND]
            casc = res[1]
            if casc > 0:
                gi[G_BGHIT_NOTRIG] += 1
                bcombo[0, idx, (casc if casc < 5 else 5) - 1] += 1
    return gi, gf, gs_i, gs_f, bi, bfl, bcombo, card_draws, hist_sc, hist_spins, lp


@njit(nogil=True, cache=True)
def resolve_stops_chunk(D, scene, stops_seq, mult0, bet, log):
    """對帳／重現用：依給定停點序列逐轉計算（位置倍數由 mult0 起算並跨轉保留，等同一段 FG 或單一 BG）。"""
    P = D[_D_PARAM]
    n = P[P_SIZE]
    W = (
        np.zeros((n, n), np.int64), np.zeros((n, n), np.int64), np.zeros((n, n), np.int64),
        np.zeros((n, n), np.int64), np.zeros(n * n, np.int64), np.zeros(n * n, np.int64),
        np.zeros(n, np.int64), np.zeros(n, np.int64),
        np.zeros(n * n, np.int64), np.zeros(n * n, np.int64), np.zeros(n * n, np.float64),
        np.zeros(ACC_I_LEN, np.int64), np.zeros(ACC_F_LEN, np.float64),
        np.zeros(ACC_I_LEN, np.int64), np.zeros(ACC_F_LEN, np.float64),
        np.zeros((n * n, 2), np.int64), np.zeros(n, np.int64),
    )
    lp = np.zeros(1, np.int64)
    W[_W_MULT][:, :] = mult0
    for i in range(stops_seq.shape[0]):
        for c in range(n):
            W[_W_STOPS][c] = stops_seq[i, c]
        _resolve(D, W, scene, bet, W[_W_BG_I], W[_W_BG_F], log, lp)
    return lp


# ===== Trace 解析 =====

def parse_log(log: np.ndarray, end: int, size: int) -> list[dict[str, Any]]:
    """把核心寫出的流水帳轉成事件清單（Trace 列印與對帳共用）。"""
    if end > len(log):
        raise RuntimeError(f"Trace 緩衝區不足（需要 {end}，配置 {len(log)}）")
    cells = size * size
    pos = 0
    events: list[dict[str, Any]] = []

    def take(k: int) -> list[float]:
        nonlocal pos
        out = log[pos:pos + k].tolist()
        pos += k
        return out

    def grid() -> list[list[int]]:
        flat = [int(v) for v in take(cells)]
        return [flat[r * size:(r + 1) * size] for r in range(size)]

    while pos < end:
        code = int(take(1)[0])
        if code == T_ROUND:
            events.append({"type": "round"})
        elif code == T_SPIN:
            scene = int(take(1)[0])
            stops = [int(v) for v in take(size)]
            events.append({"type": "spin", "scene": "bg" if scene == 0 else "fg", "stops": stops,
                           "board": grid(), "mult": grid(), "steps": []})
        elif code == T_STEP:
            msum, eff, pay, ncl = take(4)
            wins = []
            for _ in range(int(ncl)):
                sym, sz, p = take(3)
                wins.append({"sym": int(sym), "size": int(sz), "pay": p})
            step = {"boardSum": int(msum), "effSum": int(eff), "pay": pay, "wins": wins,
                    "remove": grid(), "boardAfter": grid(), "multAfter": grid()}
            events[-1]["steps"].append(step)
        elif code == T_END:
            total, casc, scatter, msum = take(4)
            events[-1].update({"total": total, "cascadeCount": int(casc), "scatterCount": int(scatter),
                               "finalSum": int(msum)})
        elif code == T_CARD:
            sec, idx = take(2)
            events.append({"type": "card", "section": int(sec), "index": int(idx)})
        elif code == T_ACCEPT:
            tries, ok = take(2)
            events.append({"type": "accept", "retries": int(tries), "ok": bool(ok)})
        elif code == T_FGSTART:
            events.append({"type": "fg_start", "award": int(take(1)[0])})
        elif code == T_RETRIG:
            sc, add = take(2)
            events.append({"type": "retrigger", "scatter": int(sc), "add": int(add)})
        elif code == T_ENTRY:
            tries = int(take(1)[0])
            stops = [int(v) for v in take(size)]
            events.append({"type": "entry", "tries": tries, "stops": stops, "board": grid()})
        elif code == T_PLATES:
            count = int(take(1)[0])
            plates = []
            for _ in range(count):
                key, value = take(2)
                plates.append({"key": int(key), "value": int(value)})
            events.append({"type": "plates", "plates": plates})
        else:
            raise RuntimeError(f"未知的 Trace 紀錄碼 {code}（位置 {pos - 1}）")
    return events


def resolve_from_stops(scene: str, stops_seq: list[list[int]], mult0: list[list[int]] | None = None,
                       bet: float = 1.0, config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """給定停點（可多轉，位置倍數跨轉保留）回傳每一轉的完整步驟；供與 index.html 對帳。"""
    cfg = config or CFG or load_config(BASE_DIR / CONFIG_FILE, CONFIG_TIER)[0]
    validate_config_pair(cfg, None, CONFIG_FILE, "")
    data = build_game_data(cfg, None, MODE_NORMALBET)
    size = int(cfg["board_size"])
    m0 = np.array(mult0 if mult0 is not None else [[0] * size] * size, np.int64)
    seq = np.array(stops_seq, np.int64).reshape(-1, size)
    log = np.zeros(max(4096, len(seq) * 20000), np.float64)
    lp = resolve_stops_chunk(data, 0 if scene == "bg" else 1, seq, m0, float(bet), log)
    return [e for e in parse_log(log, int(lp[0]), size) if e["type"] == "spin"]


def format_grid(board: list[list[int]], mult: list[list[int]] | None = None,
                remove: list[list[int]] | None = None) -> str:
    codes = CFG["symbol_codes"]
    lines = []
    for r, row in enumerate(board):
        cells = []
        for c, v in enumerate(row):
            text = codes[v]
            if remove and remove[r][c]:
                text = f"[{text}]"
            if mult and mult[r][c]:
                text += f"x{mult[r][c]}"
            cells.append(f"{text:>8}")
        lines.append("  " + " ".join(cells))
    return "\n".join(lines)


def print_events(events: list[dict[str, Any]], bet_mode: int) -> None:
    codes = CFG["symbol_codes"]
    sections = card_sections(CFG_RTP or None, bet_mode)
    fg_no = 0
    for e in events:
        kind = e["type"]
        if kind == "card":
            card = sections[e["section"]][e["index"]]
            desc = "free_game" if card["type"] == "free_game" else f"({card['min']}, {card['max']}]"
            print(f"[card] {'weight_bg' if e['section'] == SEC_BG else 'weight_fg'} 抽到 {desc}")
        elif kind == "accept":
            print(f"[card] 重骰 {e['retries']} 次，{'符合' if e['ok'] else '達 Retry 上限，保留最後結果'}\n")
        elif kind == "entry":
            print(f"[BF 入場盤] 停點 {e['stops']}（整盤重抽 {e['tries'] - 1} 次；不計分）")
            print(format_grid(e["board"]))
        elif kind == "fg_start":
            fg_no = 0
            print(f"[FG] 開始，{e['award']} 場")
        elif kind == "retrigger":
            print(f"[FG] Retrigger：{e['scatter']} 顆 C1 → +{e['add']} 場\n")
        elif kind == "plates":
            size = int(CFG["board_size"])
            text = "、".join(f"列{p['key'] // size}欄{p['key'] % size} x{p['value']}" for p in e["plates"])
            print(f"[Extra Bet 底板] {text}")
        elif kind == "spin":
            if e["scene"] == "fg":
                fg_no += 1
            head = "BG" if e["scene"] == "bg" else f"FG 第 {fg_no} 轉"
            print(f"[{head}] 停點 {e['stops']}")
            print(format_grid(e["board"], e["mult"]))
            for i, st in enumerate(e["steps"], start=1):
                wins = "、".join(f"{codes[w['sym']]}×{w['size']}＝{w['pay']:.4f}" for w in st["wins"])
                print(f"  連消 {i}：全盤和 {st['boardSum']}（乘 {st['effSum']}）→ {wins}；本段 {st['pay']:.4f}")
                print(format_grid(st["boardAfter"], st["multAfter"]))
            print(f"  → 得分 {e['total']:.4f}、連消 {e['cascadeCount']} 次、C1 {e['scatterCount']} 顆、"
                  f"全盤和 {e['finalSum']}\n")


# ===== 統計 =====

def wager_for_mode(mode: int, base_bet: float) -> float:
    if mode == MODE_EXTRABET:
        return base_bet * float(CFG["extrabet"])
    if mode == MODE_FEATUREBUY:
        return base_bet * float(CFG["featurebuy"])
    return base_bet


def merge_arrays(results):
    """Worker 結果合併：Count／Pay 相加；Max 欄位取最大值。"""
    merged = [np.array(a, copy=True) for a in results[0]]
    for res in results[1:]:
        for i, a in enumerate(res):
            merged[i] += a
    for key in (H_MAXWX, H_MAXBGX, H_MAXFGX):
        merged[1][key] = max(r[1][key] for r in results)
    for scene in range(2):
        for key in (A_MAXSUM, A_MAXCASC):
            merged[2][scene, key] = max(r[2][scene, key] for r in results)
    return tuple(merged)


def arrays_to_stats(arrays) -> dict[str, Any]:
    gi, gf, gs_i, gs_f, bi, bfl, bcombo, card_draws, hist_sc, hist_spins = arrays[:10]
    return {
        "rounds": int(gi[G_ROUNDS]), "coin_in": float(gf[H_COIN]),
        "pay_bg": float(gf[H_PBG]), "pay_fg": float(gf[H_PFG]),
        "win_x_sum": float(gf[H_WX]), "win_x_square": float(gf[H_WX2]),
        "max_win_x": float(gf[H_MAXWX]), "max_bg_x": float(gf[H_MAXBGX]), "max_fg_x": float(gf[H_MAXFGX]),
        "fg_triggers": int(gi[G_FGTRIG]), "bg_triggers": int(gi[G_TRIGCNT]), "trig_pay": float(gf[H_TRIGPAY]),
        "retry_total": int(gi[G_RETRY]), "retry_limit_exceeded": int(gi[G_RLE]),
        "retry_limit_bg_range": int(gi[G_RLBGR]), "retry_limit_bg_freegame": int(gi[G_RLBGFG]),
        "retry_limit_fg": int(gi[G_RLFG]),
        "entry_cnt": int(gi[G_ENTRY]), "entry_tries": int(gi[G_ENTRYTRY]),
        "fg_sum_end": float(gf[H_FGSUMEND]),
        "acc_i": gs_i, "acc_f": gs_f, "bi": bi, "bfl": bfl, "bcombo": bcombo,
        "card_draws": card_draws, "hist_sc": hist_sc, "hist_spins": hist_spins,
    }


def _chunk_args(bet_mode: int, base_bet: float, card_enabled: bool):
    card_cfg = (CFG_RTP or {}).get("card_system") or {}
    card_on = bool(card_enabled and card_cfg.get("enabled"))
    data = build_game_data(CFG, CFG_RTP or None, bet_mode)
    bg_cards, fg_cards = card_sections(CFG_RTP or None, bet_mode)
    trig_cap = section_cap(bg_cards) if card_on else math.inf
    retry_limit = int(card_cfg.get("retry_limit", 0)) if card_on else 1
    if card_on:
        if retry_limit <= 0:
            raise ValueError("card_system.retry_limit 必須為正整數")
        need_bg = bet_mode != MODE_FEATUREBUY
        if (need_bg and data[_D_CARD_TOT][SEC_BG] <= 0) or data[_D_CARD_TOT][SEC_FG] <= 0:
            raise ValueError(f"{MODE_KEY[bet_mode]} 的卡組沒有任何正權重卡片")
        has_free = any(c.get("type") == "free_game" and float(c.get("weight", 0)) > 0 for c in bg_cards)
        if has_free and not math.isfinite(trig_cap):
            raise ValueError("啟用 free_game 卡的卡組必須至少有一張正權重 range 卡提供 BG Trigger Cap")
    return data, card_on, trig_cap, retry_limit, wager_for_mode(bet_mode, base_bet)


_NO_LOG = np.zeros(1, np.float64)


def _worker(args):
    """ProcessPoolExecutor 的工作函式：先 Warm-up（載入／編譯 Numba，不計時），再正式計時。"""
    data, rounds, bet_mode, bet, wager, card_on, trig_cap, retry_limit, seed = args
    simulate_chunk(data, 20, bet_mode, bet, wager, card_on, trig_cap, retry_limit, seed ^ 0x5F5F, _NO_LOG)
    started = time.perf_counter()
    arrays = simulate_chunk(data, rounds, bet_mode, bet, wager, card_on, trig_cap, retry_limit, seed, _NO_LOG)
    return arrays[:10], time.perf_counter() - started


def run_simulation(total_rounds: int, bet_mode: int, base_bet: float, workers: int,
                   card_enabled: bool) -> dict[str, Any]:
    workers = max(1, min(workers, total_rounds))
    per_worker = [total_rounds // workers] * workers
    for index in range(total_rounds % workers):
        per_worker[index] += 1
    assert sum(per_worker) == total_rounds
    data, card_on, trig_cap, retry_limit, wager = _chunk_args(bet_mode, base_bet, card_enabled)
    jobs = [(data, count, bet_mode, base_bet, wager, card_on, trig_cap, retry_limit, RNG_SEED + index * 7919)
            for index, count in enumerate(per_worker) if count > 0]

    # Warm-up（主行程先編譯並寫入快取，Worker 直接讀快取；皆不計入 duration）
    simulate_chunk(data, 20, bet_mode, base_bet, wager, card_on, trig_cap, retry_limit, RNG_SEED - 1, _NO_LOG)
    wall = time.perf_counter()
    if len(jobs) == 1:
        results = [_worker(jobs[0])]
    else:
        with ProcessPoolExecutor(max_workers=len(jobs)) as pool:
            results = list(pool.map(_worker, jobs))
    wall = time.perf_counter() - wall
    arrays = merge_arrays([r[0] for r in results])
    stats = arrays_to_stats(arrays)
    assert stats["rounds"] == total_rounds, "Worker 合併後的總場次不等於 total_rounds"
    # duration＝各 Worker 正式模擬耗時的最大值（不含行程啟動與 Numba 載入）；wall 另列供參考
    return {"stats": stats, "duration": max(r[1] for r in results), "wall": wall, "workers": len(jobs),
            "trig_cap": trig_cap, "retry_limit": retry_limit, "card_on": card_on}


# ===== 報表 / Console =====

def mode_name(mode: int) -> str:
    return {MODE_NORMALBET: "Normal Bet", MODE_EXTRABET: "Extra Bet"}.get(mode, "Buy Feature")


def _cap_index(cap: float) -> int | None:
    """卡組上限對應的倍率區間列；找不到完全相同的上限就停止（規範 §1.1.4）。"""
    if not math.isfinite(cap):
        return None
    if cap not in MULTIPLIER_THRESHOLDS:
        raise ValueError(f"卡組上限 {cap} 找不到完全相同的倍率區間上限，請補齊倍率區間")
    return MULTIPLIER_THRESHOLDS.index(cap)


def calculated_metrics(result: dict[str, Any]) -> dict[str, Any]:
    s = result["stats"]
    rounds = max(1, s["rounds"])
    coin_in = max(1e-12, s["coin_in"])
    pay_total = s["pay_bg"] + s["pay_fg"]
    mean = s["win_x_sum"] / rounds
    variance = max(0.0, s["win_x_square"] / rounds - mean * mean)
    bg, fg = s["acc_i"][0], s["acc_i"][1]
    fg_triggers = s["fg_triggers"]
    fg_spins = int(fg[A_SPINS])
    retrig = int(fg[A_RETRIG])
    special = int(bg[A_SPECIAL]) + int(fg[A_SPECIAL]) + s["entry_cnt"]   # BF 入場盤本身含 C1，也算一轉
    # bg_trigger_fg_*：BG 觸發 FG 且該把 BG 倍數 ≤ BG Trigger Cap（Oldhand 卡組最高正權重 range 上限）
    cap = result["bg_trigger_cap"]
    idx = _cap_index(cap)
    trig_cnt = s["bi"][B_TRIGCNT]
    trig_pay = s["bfl"][B_TRIGPAY]
    upto = NBUCKET if idx is None else idx + 1
    return {
        "coin_in_per_round": s["coin_in"] / rounds,
        "rtp_total": pay_total / coin_in,
        "rtp_game": pay_total / coin_in,
        "rtp_bg": s["pay_bg"] / coin_in,
        "rtp_fg": s["pay_fg"] / coin_in,
        "hit_rate_bg": int(bg[A_HIT]) / rounds,
        "hit_rate_fg": int(fg[A_HIT]) / max(1, fg_spins),
        "fg_trigger_rate": fg_triggers / rounds,
        "fg_trigger_cycle": rounds / fg_triggers if fg_triggers else math.inf,
        "retrigger_trigger_rate": retrig / max(1, fg_spins),
        "retrigger_trigger_cycle": fg_spins / retrig if retrig else math.inf,
        "avg_fg_spins": fg_spins / fg_triggers if fg_triggers else 0.0,
        "bg_trigger_fg_cnt": int(trig_cnt[:upto].sum()),
        "bg_trigger_fg_pay": float(trig_pay[:upto].sum()),
        "special_symbol_cnt": special,
        "SCR": special / rounds * 10_000_000_000 if s["rounds"] else 0,
        "volatility_std": math.sqrt(variance),
        "standard_error": math.sqrt(variance) / math.sqrt(rounds),
    }


def common_summary_sections(result: dict[str, Any]) -> list[list[tuple[str, Any]]]:
    """Console 與 Overview 共用的欄位（順序依模擬程式規範 §1.3.1）。
    本作不支援的欄位不輸出：bet_tier、link_enabled（無押注分層／Link）、rtp_link、rtp_bonus（無 OP Jackpot）、
    bg_trigger_fg_*_newbie（無 Newbie）；Buy Feature 沒有 BG，不輸出 rtp_bg／hit_rate_bg／bg_trigger_fg_*。"""
    s = result["stats"]
    m = calculated_metrics(result)
    is_bf = result["bet_mode"] == MODE_FEATUREBUY
    rtp_rows: list[tuple[str, Any]] = [("rtp_total", m["rtp_total"]), ("rtp_game", m["rtp_game"])]
    if not is_bf:
        rtp_rows.append(("rtp_bg", m["rtp_bg"]))
    rtp_rows.append(("rtp_fg", m["rtp_fg"]))
    if not is_bf:
        rtp_rows.append(("hit_rate_bg", m["hit_rate_bg"]))
    rtp_rows += [("hit_rate_fg", m["hit_rate_fg"]),
                 ("fg_trigger_rate", (m["fg_trigger_rate"], m["fg_trigger_cycle"])),
                 ("retrigger_trigger_rate", (m["retrigger_trigger_rate"], m["retrigger_trigger_cycle"])),
                 ("avg_fg_spins", m["avg_fg_spins"])]
    trigger_rows: list[tuple[str, Any]] = []
    if not is_bf:
        trigger_rows = [("bg_trigger_fg_cnt", m["bg_trigger_fg_cnt"]), ("bg_trigger_fg_pay", m["bg_trigger_fg_pay"])]
    sections: list[list[tuple[str, Any]]] = [
        [("game_name", result["game_name"]), ("game_id", result["game_id"])],
        [("config_file", result["config_file"]),
         ("config_tier", result["config_tier"]),
         ("math_version", result["math_version"]),
         ("card_system", "on" if result["card_system_enabled"] else "off")],
        [("bet_mode", mode_name(result["bet_mode"])),
         ("bet_multi", result["bet_multi"]),
         ("feature_price_multiplier", result["feature_price_multiplier"]),
         ("base_bet", result["base_bet"]),
         ("bet_amount", result["bet_amount"]),
         ("bet_tier_amount", result["bet_tier_amount"]),
         ("max_multiplier_bg", result["max_multiplier_bg"]),
         ("max_multiplier_fg", result["max_multiplier_fg"]),
         ("coin_in", m["coin_in_per_round"]),
         ("total_rounds", s["rounds"]),
         ("duration", result["duration"])],
        rtp_rows,
        [*trigger_rows,
         ("special_symbol_cnt", m["special_symbol_cnt"]),
         ("SCR", m["SCR"])],
        [("volatility_std", m["volatility_std"]), ("standard_error", m["standard_error"])],
    ]
    if result["card_system_enabled"]:
        sections.extend([
            [("card_system_profile", result["card_system_profile"]),
             ("card_retry_limit", result["card_retry_limit"]),
             ("retry_total", s["retry_total"]),
             ("avg_retry", s["retry_total"] / max(1, s["rounds"]))],
            [("retry_limit_exceeded", s["retry_limit_exceeded"]),
             ("retry_limit_bg_range", s["retry_limit_bg_range"]),
             ("retry_limit_bg_freegame", s["retry_limit_bg_freegame"]),
             ("retry_limit_fg", s["retry_limit_fg"])],
        ])
    return sections


def game_info_rows(result: dict[str, Any]) -> list[tuple[str, Any]]:
    s = result["stats"]
    mode = result["bet_mode"]
    rounds = max(1, s["rounds"])
    bg, fg = s["acc_i"][0], s["acc_i"][1]
    fg_spins = max(1, int(fg[A_SPINS]))
    fg_hits = max(1, int(fg[A_HIT]))
    rows: list[tuple[str, Any]] = [("rounds_per_sec", s["rounds"] / max(1e-9, result["duration"])),
                                   ("workers", result["workers"]),
                                   ("max_win_x", s["max_win_x"])]
    if mode != MODE_FEATUREBUY:
        bg_hits = max(1, int(bg[A_HIT]))
        combo = [int(bg[A_COMBO + k]) for k in range(COMBO_K)]
        rows += [
            ("max_bg_x", s["max_bg_x"]),
            ("avg_cascades_bg", int(bg[A_CASC]) / rounds),
            ("avg_cascades_bg_hit", int(bg[A_CASC]) / bg_hits),
            ("bg_combo_1_share", combo[1] / bg_hits),
            ("bg_combo_2_share", combo[2] / bg_hits),
            ("bg_combo_3_share", combo[3] / bg_hits),
            ("bg_combo_4plus_share", sum(combo[4:]) / bg_hits),
            ("max_cascades_bg", int(bg[A_MAXCASC])),
            ("avg_board_sum_bg_hit", int(bg[A_SUMEND]) / bg_hits),
            ("max_board_sum_bg", int(bg[A_MAXSUM])),
        ]
    if mode == MODE_EXTRABET:
        rows.append(("avg_plate_sum", int(bg[A_PLATESUM]) / rounds))
    rows += [
        ("max_fg_x", s["max_fg_x"]),
        ("avg_fg_x", s["pay_fg"] / result["base_bet"] / max(1, s["fg_triggers"])),
        ("avg_cascades_fg", int(fg[A_CASC]) / fg_spins),
        ("avg_cascades_fg_hit", int(fg[A_CASC]) / fg_hits),
        ("max_cascades_fg", int(fg[A_MAXCASC])),
        ("avg_board_sum_fg_end", s["fg_sum_end"] / max(1, s["fg_triggers"])),
        ("max_board_sum_fg", int(fg[A_MAXSUM])),
    ]
    if mode != MODE_FEATUREBUY:
        for k in sorted(int(x) for x in CFG["fg_awards"]):
            rows.append((f"fg_trigger_c1_{k}_cnt", int(s["hist_sc"][k])))
    else:
        rows.append(("buy_entry_avg_redraw", s["entry_tries"] / max(1, s["entry_cnt"]) - 1))
    return rows


COUNT_KEYS = {
    "total_rounds", "bg_trigger_fg_cnt", "special_symbol_cnt", "SCR", "retry_total",
    "retry_limit_exceeded", "retry_limit_bg_range", "retry_limit_bg_freegame", "retry_limit_fg",
    "max_cascades_bg", "max_cascades_fg", "max_board_sum_bg", "max_board_sum_fg", "rounds_per_sec",
}


def _display_value(key: str, value: Any) -> str:
    if isinstance(value, str):
        return value
    if key == "duration":
        return f"{float(value):05.2f} sec"
    if key in COUNT_KEYS or key.endswith("_cnt"):
        return f"{int(value):,}"
    if key in {"card_retry_limit", "workers", "bet_multi"}:
        return str(int(value))
    if key == "bg_trigger_fg_pay":
        return f"{float(value):,.2f}"
    if key in {"coin_in", "base_bet", "bet_amount", "bet_tier_amount"}:
        return f"{float(value):.2f}"
    if key in {"fg_trigger_rate", "retrigger_trigger_rate"}:
        rate, cycle = value
        unit = "spins" if key == "fg_trigger_rate" else "free spins"
        cycle_text = "N/A" if not math.isfinite(float(cycle)) else f"{float(cycle):.2f} {unit}"
        return f"{float(rate):.4%} (cycle {cycle_text})"
    if key.startswith("rtp_") or key in {"hit_rate_bg", "hit_rate_fg"} or key.endswith("_share"):
        return f"{float(value):.4%}"
    if key == "avg_fg_spins":
        return f"{float(value):.2f} spins"
    if key in {"max_win_x", "max_bg_x", "max_fg_x", "avg_fg_x"}:
        return f"{float(value):,.2f} x"
    if key in {"max_multiplier_bg", "max_multiplier_fg"}:
        return f"{float(value):g}"
    if key in {"avg_retry", "volatility_std", "standard_error"}:
        return f"{float(value):05.2f}"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def overview_rows(result: dict[str, Any]) -> list[tuple[str, str]]:
    flat = [row for section in common_summary_sections(result) for row in section]
    return [(key, _display_value(key, value)) for key, value in flat + game_info_rows(result)]


def print_console(result: dict[str, Any]) -> None:
    for section in common_summary_sections(result):
        for key, value in section:
            print(f"{key:<26}: {_display_value(key, value)}")
        print()
    print("<< By Game Info >>")
    print()
    for key, value in game_info_rows(result):
        print(f"{key:<26}: {_display_value(key, value)}")
    print()


def _interval_text(index: int) -> str:
    if index == 0:
        return "0"
    return f"{float(MULTIPLIER_THRESHOLDS[index - 1]):.1f} < X <= {float(MULTIPLIER_THRESHOLDS[index]):.1f}"


def multiplier_line_frame(result: dict[str, Any]):
    import pandas as pd
    s = result["stats"]
    bi, bfl, bcombo = s["bi"], s["bfl"], s["bcombo"]
    is_bf = result["bet_mode"] == MODE_FEATUREBUY
    rows = []
    trigger_cnt_cum = 0
    trigger_pay_cum = 0.0
    for index, upper in enumerate(MULTIPLIER_THRESHOLDS):
        trigger_cnt_cum += int(bi[B_TRIGCNT, index])
        trigger_pay_cum += float(bfl[B_TRIGPAY, index])
        row: dict[str, Any] = {
            "Interval": _interval_text(index),
            "base_game_cnt": int(bi[B_BGCNT, index]),
            "base_game_pay": float(bfl[B_BGPAY, index]),
            "free_game_cnt": int(bi[B_FGCNT, index]),
            "free_game_pay": float(bfl[B_FGPAY, index]),
        }
        if is_bf:   # BF 欄只在 Buy Feature 批次輸出，其他模式不以 0 冒充
            row["free_game_cnt_BF"] = int(bi[B_BFCNT, index])
            row["free_game_pay_BF"] = float(bfl[B_BFPAY, index])
        row["Interval_Upper"] = upper
        row["bg_trigger_fg_cnt_lte_upper"] = trigger_cnt_cum
        row["bg_trigger_fg_pay_lte_upper"] = trigger_pay_cum
        fg_spins = int(bi[B_FGSPINS, index])
        row["FG_Hit_Rate"] = int(bi[B_FGHIT, index]) / fg_spins if fg_spins else 0.0
        row["FG_Spin_Count"] = fg_spins
        # Combo 占比：該區間內「有連消」的轉，連消 1／2／3／4／5+ 次各占多少
        bg_total = max(1, int(bcombo[0, index].sum()))
        for k in range(5):
            row[f"BG_Combo_{k + 1}{'+' if k == 4 else ''}_Rate"] = int(bcombo[0, index, k]) / bg_total
        fg_total = max(1, int(bcombo[1, index].sum()))
        for k in range(5):
            row[f"FG_Combo_{k + 1}{'+' if k == 4 else ''}_Rate"] = int(bcombo[1, index, k]) / fg_total
        # --- By Game：全盤倍數和 ---
        fg_cnt = int(bi[B_BFCNT if is_bf else B_FGCNT, index])
        row["BG_Avg_Board_Sum"] = int(bi[B_BGSUM, index]) / max(1, int(bi[B_BGCNT, index]))
        row["FG_Avg_Board_Sum_End"] = int(bi[B_FGSUM, index]) / max(1, fg_cnt)
        rows.append(row)
    return pd.DataFrame(rows)


def pay_range_frame(result: dict[str, Any]):
    """整局得分 ÷ 實際押注的分布（含 BG＋FG）。"""
    import pandas as pd
    s = result["stats"]
    rounds = max(1, s["rounds"])
    coin_in = max(1e-12, s["coin_in"])
    rows = []
    for index, upper in enumerate(MULTIPLIER_THRESHOLDS):
        cnt = int(s["bi"][B_PRCNT, index])
        pay = float(s["bfl"][B_PRPAY, index])
        rows.append((_interval_text(index), upper, cnt, cnt / rounds, pay, pay / coin_in))
    return pd.DataFrame(rows, columns=["Interval", "Interval_Upper", "round_cnt", "round_rate", "pay", "rtp"])


def feature_frame(result: dict[str, Any]):
    import pandas as pd
    s = result["stats"]
    fg_triggers = max(1, s["fg_triggers"])
    fg = s["acc_i"][1]
    rows: list[tuple[str, Any, Any, Any]] = []
    for k in range(len(s["hist_sc"])):
        if s["hist_sc"][k]:
            rows.append(("fg_trigger_c1", k, int(s["hist_sc"][k]), int(s["hist_sc"][k]) / fg_triggers))
    for k in range(len(s["hist_spins"])):
        if s["hist_spins"][k]:
            rows.append(("fg_session_spins", k, int(s["hist_spins"][k]), int(s["hist_spins"][k]) / fg_triggers))
    rows.append(("fg_retrigger", "count", int(fg[A_RETRIG]), int(fg[A_RETRIG]) / max(1, int(fg[A_SPINS]))))
    return pd.DataFrame(rows, columns=["feature", "key", "count", "rate"])


def symbol_frame(result: dict[str, Any]):
    """各符號各 Cluster 大小的命中數與派彩。"""
    import pandas as pd
    s = result["stats"]
    codes = CFG["symbol_codes"]
    npay = len(CFG["pay_table"][0])
    minc = int(CFG["min_cluster"])
    coin_in = max(1e-12, s["coin_in"])
    rows = []
    for si, scene in enumerate(("BG", "FG")):
        for sym in range(len(CFG["pay_table"])):
            for idx in range(npay):
                size = f"{minc + idx}{'+' if idx == npay - 1 else ''}"
                hits = int(s["acc_i"][si][A_SYMHIT + sym * MAX_PAY + idx])
                pay = float(s["acc_f"][si][F_SYMPAY + sym * MAX_PAY + idx])
                rows.append((scene, codes[sym], size, CFG["pay_table"][sym][idx], hits, pay, pay / coin_in))
    return pd.DataFrame(rows, columns=["scene", "symbol", "cluster_size", "pay_table", "hits", "pay", "rtp"])


def symbol_count_frame(result: dict[str, Any]):
    """開場盤面與掉落補入的符號數。"""
    import pandas as pd
    s = result["stats"]
    codes = CFG["symbol_codes"]
    rows = []
    for si, scene in enumerate(("BG", "FG")):
        acc = s["acc_i"][si]
        init_total = max(1, int(acc[A_INIT:A_INIT + MAX_SYM].sum()))
        drop_total = max(1, int(acc[A_DROP:A_DROP + MAX_SYM].sum()))
        for sym, code in enumerate(codes):
            init, drop = int(acc[A_INIT + sym]), int(acc[A_DROP + sym])
            rows.append((scene, code, init, init / init_total, drop, drop / drop_total))
    return pd.DataFrame(rows, columns=["scene", "symbol", "initial_cnt", "initial_rate", "drop_cnt", "drop_rate"])


def eliminate_frame(result: dict[str, Any]):
    """連消次數分布：BG 每局、FG 每次免費轉。"""
    import pandas as pd
    s = result["stats"]
    bg, fg = s["acc_i"][0], s["acc_i"][1]
    bg_total, fg_total = max(1, int(bg[A_SPINS])), max(1, int(fg[A_SPINS]))
    rows = []
    for k in range(COMBO_K):
        b, f = int(bg[A_COMBO + k]), int(fg[A_COMBO + k])
        rows.append((f"{k}+" if k == COMBO_K - 1 else str(k), b, b / bg_total, f, f / fg_total))
    return pd.DataFrame(rows, columns=["combo", "BG", "BG_rate", "FG", "FG_rate"])


def card_frame(result: dict[str, Any]):
    """卡片抽取占比：設定占比 vs 實際占比。"""
    import pandas as pd
    s = result["stats"]
    rows = []
    for si, (name, cards) in enumerate(zip(("weight_bg", "weight_fg"), card_sections(CFG_RTP, result["bet_mode"]))):
        total_w = sum(float(c.get("weight", 0)) for c in cards)
        total_d = int(s["card_draws"][si].sum())
        for i, c in enumerate(cards):
            w = float(c.get("weight", 0))
            d = int(s["card_draws"][si][i])
            rows.append((name, c["type"], c.get("min", ""), c.get("max", ""), w,
                         w / total_w if total_w else 0.0, d, d / total_d if total_d else 0.0))
    return pd.DataFrame(rows, columns=["section", "type", "min", "max", "weight", "set_share", "draws", "actual_share"])


def format_rounds_tag(total_rounds: int) -> str:
    exponent = round(math.log10(total_rounds)) if total_rounds > 0 else 0
    if 10 ** exponent == total_rounds:
        return f"10{exponent}"
    return str(total_rounds)


def format_base_version_tag(version: Any) -> str:
    text = str(version)
    if not text.isdigit() or len(text) != 1:
        raise ValueError(f"基礎版本必須為 1 碼，目前為 {version!r}")
    return text.zfill(2)


def format_rtp_version_tag(version: Any) -> str:
    parts = str(version).split(".")
    if len(parts) != 4:
        raise ValueError(f"RTP／Variant 版本必須為四段，目前為 {version!r}")
    out = ""
    for part in parts:
        if not part.isdigit() or len(part) > 2:
            raise ValueError(f"版本段位 {part!r} 超過 2 位數，請修正版本後再輸出報表")
        out += part.zfill(2)
    return out


def format_rtp_tag(rtp_ratio: float) -> str:
    return f"{rtp_ratio * 100:.4f}".replace(".", "")[:4]


def report_filename(result: dict[str, Any], timestamp: datetime | None = None) -> str:
    """Off：<base_game_id>_<版本2碼>_<時間>_betmode<n>_<場次>.xlsx
    On ：<rtp_game_id>_<版本8碼>_<時間>_betmode<n>_<場次>_<rtp>_<profile>.xlsx（本作無押注分層，不帶 bet_tier 段）"""
    stamp = (timestamp or datetime.now()).strftime("%y%m%d%H%M")
    rounds_tag = format_rounds_tag(result["stats"]["rounds"])
    bet_mode = result["bet_mode"]
    if not result["card_system_enabled"]:
        return (f"{CFG['parsheet_id']}_{format_base_version_tag(CFG['excel_version'])}_{stamp}"
                f"_betmode{bet_mode}_{rounds_tag}.xlsx")
    rtp_game_id = f"{CFG_RTP['parsheet_id']}{CFG_RTP['config_code']}"
    parts = [rtp_game_id, format_rtp_version_tag(CFG_RTP["excel_version"]), stamp, f"betmode{bet_mode}",
             rounds_tag, format_rtp_tag(calculated_metrics(result)["rtp_total"]), result["card_system_profile"]]
    return "_".join(parts) + ".xlsx"


def output_report(result: dict[str, Any], output_dir: Path | None = None) -> Path:
    import pandas as pd
    directory = output_dir or (BASE_DIR / "Record")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / report_filename(result)
    overview = pd.DataFrame(overview_rows(result), columns=["Index", "Value"])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        overview.to_excel(writer, sheet_name="Overview", index=False)
        multiplier_line_frame(result).to_excel(writer, sheet_name="Multiplier Line", index=False)
        pay_range_frame(result).to_excel(writer, sheet_name="Pay Range", index=False)
        feature_frame(result).to_excel(writer, sheet_name="Feature", index=False)
        symbol_frame(result).to_excel(writer, sheet_name="Symbol", index=False)
        symbol_count_frame(result).to_excel(writer, sheet_name="Symbol Count", index=False)
        eliminate_frame(result).to_excel(writer, sheet_name="Eliminate", index=False)
        if result["card_system_enabled"]:
            card_frame(result).to_excel(writer, sheet_name="Card", index=False)
    return path


# ===== Runner =====

def build_result(bundle: dict[str, Any], combo: dict[str, Any]) -> dict[str, Any]:
    bet_mode = int(combo["bet_mode"])
    base_bet = float(combo["base_bet"])
    bet_amount = wager_for_mode(bet_mode, base_bet)
    card_on = bundle["card_on"]
    bg_cards, fg_cards = card_sections(CFG_RTP or None, bet_mode)
    # BG Trigger Cap：Card On 用於重骰；Card Off 只用於 bg_trigger_fg_* 統計（Oldhand 卡組最高正權重 range 上限）
    bg_cap = section_cap(bg_cards)
    return {
        "stats": bundle["stats"],
        "duration": bundle["duration"],
        "workers": bundle["workers"],
        "game_name": CFG["game_name_zh"],
        "game_id": CFG["online_game_id"],
        "config_file": combo["config_file"],
        "config_tier": combo["tier"] if CFG_RTP else f"{combo['tier']} (not found)",
        "math_version": CFG_RTP.get("excel_version", CFG["excel_version"]),
        "card_system_enabled": card_on,
        "card_system_profile": "oldhand",
        "card_retry_limit": bundle["retry_limit"],
        "bet_mode": bet_mode,
        "bet_multi": int(CFG["extrabet"]) if bet_mode == MODE_EXTRABET else 1,
        "feature_price_multiplier": float(CFG["featurebuy"]) if bet_mode == MODE_FEATUREBUY else "n/a",
        "base_bet": base_bet,
        "bet_amount": bet_amount,
        "bet_tier_amount": base_bet if bet_mode == MODE_FEATUREBUY else bet_amount,
        "bg_trigger_cap": bg_cap,
        "max_multiplier_bg": bg_cap if (card_on and bet_mode != MODE_FEATUREBUY) else "n/a",
        "max_multiplier_fg": section_cap(fg_cards) if card_on else "n/a",
    }


def load_batch_configs(combo: dict[str, Any]) -> None:
    """每批重新載入 Config 並重新展開層級（base＝CFG、base 疊上 tiers[tier]＝CFG_RTP），不沿用上一批的全域狀態。"""
    global CFG, CFG_RTP
    CFG, CFG_RTP = load_config(BASE_DIR / combo["config_file"], combo["tier"])
    rtp_name = f"{combo['config_file']}:{combo['tier']}"
    validate_config_pair(CFG, CFG_RTP or None, f"{combo['config_file']}:base", rtp_name)
    if not CFG_RTP and combo["card_system_enabled"]:
        raise FileNotFoundError(f"{combo['config_file']} 沒有層級 {combo['tier']}，無法以 Card System On 執行。")


def validate_batch_run(combo: dict[str, Any]) -> dict[str, Any]:
    required = {"config_file", "tier", "bet_mode", "total_rounds",
                "card_system_enabled", "card_system_is_newbie", "base_bet"}
    missing = required - set(combo)
    if missing:
        raise ValueError(f"BATCH_RUNS 缺少必要欄位：{sorted(missing)}")
    if int(combo["bet_mode"]) not in MODE_KEY:
        raise ValueError(f"不支援的 bet_mode {combo['bet_mode']}；本作為 0（Normal）／1（Extra Bet）／2（Buy Feature）")
    if int(combo["total_rounds"]) <= 0:
        raise ValueError("total_rounds 必須為正整數")
    if float(combo["base_bet"]) <= 0:
        raise ValueError("base_bet 必須大於 0")
    if combo["card_system_enabled"] and combo["card_system_is_newbie"]:
        raise ValueError("本作目前沒有 Newbie 卡組（config 只有 card_system.oldhand），不支援 card_system_is_newbie=True")
    return combo


def run_trace(combo: dict[str, Any], rounds: int) -> None:
    """固定 Seed、單執行緒、逐局 Trace：第 i 局用種子 RNG_SEED + i，可單獨重現。"""
    validate_batch_run(combo)
    load_batch_configs(combo)
    bet_mode, base_bet = int(combo["bet_mode"]), float(combo["base_bet"])
    data, card_on, trig_cap, retry_limit, wager = _chunk_args(bet_mode, base_bet, bool(combo["card_system_enabled"]))
    size = int(CFG["board_size"])
    print(f"=== Trace: {mode_name(bet_mode)}、base_bet {base_bet:g}、Card System {'on' if card_on else 'off'}、"
          f"RNG_SEED {RNG_SEED} ===\n")
    for index in range(rounds):
        log = np.zeros(4_000_000, np.float64)
        seed = RNG_SEED + index
        arrays = simulate_chunk(data, 1, bet_mode, base_bet, wager, card_on, trig_cap, retry_limit, seed, log)
        s = arrays_to_stats(arrays)
        print(f"--- 第 {index + 1} 局（seed {seed}）---")
        print_events(parse_log(log, int(arrays[10][0]), size), bet_mode)
        print(f"本局：押注 {wager:g}、BG 得分 {s['pay_bg']:.4f}、FG 得分 {s['pay_fg']:.4f}、"
              f"總倍數 {(s['pay_bg'] + s['pay_fg']) / wager:.4f}x、FG 轉數 {int(s['acc_i'][1][A_SPINS])}、"
              f"重骰 {s['retry_total']} 次\n")


def run_batch(combo: dict[str, Any], index: int, total: int) -> dict[str, Any]:
    validate_batch_run(combo)
    load_batch_configs(combo)
    print(f"=== Batch {index}/{total}: {combo} ===")
    print()
    bundle = run_simulation(int(combo["total_rounds"]), int(combo["bet_mode"]), float(combo["base_bet"]),
                            WORKERS, bool(combo["card_system_enabled"]))
    result = build_result(bundle, combo)
    if SHOW_CONSOLE_SUMMARY:
        print_console(result)
    if OUTPUT_REPORT:
        path = output_report(result)
        print(f"report -> {path}")
        print()
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="H039 急速糖果 2 simulator")
    parser.add_argument("--rounds", type=int, default=None)
    parser.add_argument("--bet-mode", type=int, default=None, help="0 Normal／1 Extra Bet／2 Buy Feature")
    parser.add_argument("--base-bet", type=float, default=None)
    parser.add_argument("--workers", "--threads", type=int, default=None, dest="workers", help="行程數；1＝單執行緒")
    parser.add_argument("--no-report", action="store_true")
    parser.add_argument("--trace", type=int, nargs="?", const=DEBUG_ROUNDS, default=None,
                        help="固定 Seed、單執行緒、逐局 Trace（預設 3 局）")
    parser.add_argument("--card-on", action="store_true", help="Card System On（需 config 內有該層級）")
    parser.add_argument("--card-off", action="store_true", help="Card System Off")
    parser.add_argument("--tier", default=None, help="覆寫層級 tier，例如 92A")
    parser.add_argument("--config", default=None, help="覆寫 config_file（調參試驗用）")
    parser.add_argument("--seed", type=int, default=None, help="覆寫 RNG_SEED（複驗用不同種子）")
    parser.add_argument("--single", action="store_true",
                        help="不跑 BATCH_RUNS，只跑一批（預設值見 User Settings，可再用其他參數覆寫）")
    return parser.parse_args()


def main() -> None:
    global RNG_SEED, WORKERS, OUTPUT_REPORT
    args = parse_args()
    if args.seed is not None:
        RNG_SEED = args.seed
    if args.workers:
        WORKERS = max(1, args.workers)
    if args.no_report:
        OUTPUT_REPORT = False

    single = {
        "config_file": CONFIG_FILE, "tier": CONFIG_TIER,
        "bet_mode": BET_MODE, "total_rounds": TOTAL_ROUNDS,
        "card_system_enabled": CARD_SYSTEM_ENABLED,
        "card_system_is_newbie": CARD_SYSTEM_IS_NEWBIE,
        "base_bet": BASE_BET_SETTING,
    }
    tracing = args.trace is not None or RUN_SINGLE_SPIN_DEBUG
    use_single = args.single or tracing or not RUN_ALL_COMBINATIONS
    runs = [single] if use_single else [dict(run) for run in BATCH_RUNS]
    for run in runs:
        if args.rounds:
            run["total_rounds"] = args.rounds
        if args.bet_mode is not None:
            run["bet_mode"] = args.bet_mode
        if args.base_bet:
            run["base_bet"] = args.base_bet
        if args.card_on:
            run["card_system_enabled"] = True
        if args.card_off:
            run["card_system_enabled"] = False
        if args.tier:
            run["tier"] = args.tier
        if args.config:
            run["config_file"] = args.config

    if tracing:
        run_trace(runs[0], args.trace if args.trace is not None else DEBUG_ROUNDS)
        return
    for index, run in enumerate(runs, start=1):
        run_batch(run, index, len(runs))


if __name__ == "__main__":
    main()
