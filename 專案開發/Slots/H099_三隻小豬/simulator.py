"""H099 三隻小豬 (Three Little Pigs) simulator.

盤面 5×3（頂端另有 1 列 peek，不判獎）、固定 20 線由左至右、Cascade（重力掉落補牌）。
R2～R4 的金色符號中獎時在原位轉 Wild，該格框升一階（茅草 → 木頭 → 磚頭，最多 3 階；框跟格子、不隨符號移動）；
連消結束且本局有得分時，每個框依階數抽倍數，Mult＝1＋所有框倍數，乘本局總得分（BG 每局框重置）。
FG：3／4／5 Scatter → 10／15／20 局，框整場保留；FG 中 3+ Scatter 加 fg_retrigger_spins 局、剩餘上限 50；
隱性控制：金色好局（fg_good_slots）、框上金色加權（frame_gold_boost.fg.by_frame_count，磚頭出現後停止）、
豪宅局（frame_gold_boost.fg.mansion，整場轉 mansion.table_id、依階數加權停輪、不停止）。
押注模式 NB（0）／EB（1，2x，數學同 NB）／BF（2，75x，進場盤表 6 重抽到 3+ Scatter）。

遊戲邏輯逐函式對照 Demo 的瀏覽器 JS 引擎（index.html：generateBoard、chooseTable、chooseEliminateMode、
evaluateBoard、applyHitAndTransform、cascadeDrop、pickDropSymbol、revealFrames、pickFrameValue、runSpin、
runFreeGameSequence、runRound）；亂數順序與 JS 不同，但機率分布相同。
玩法定義見 ``game_rule.md``；執行參數一律來自 Config（``config_99A.js``，base 疊上 tiers["92A"]，等同 JS 的
H026_BOX_DATA），不在本程式內重複維護輪帶、權重、Paytable 或 Feature 參數（JS 寫死的 FG 局數常數除外，見 User Settings）。

Runner、BATCH_RUNS、Console 欄位與 Excel 報表版面依 ``專案需知/開發規範/模擬程式規範.md``。
核心以 Numba 編譯（沒有 Numba 時自動退回純 Python，結果分布相同但很慢）；多程序 ProcessPoolExecutor 平行。

2026-11-27 初版（由 Demo JS 引擎移植；Config 變數前綴 H026 與 game_id H026192A 沿用彩罐熱舞，未改）。
"""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import os
import sys
import time
from collections import namedtuple
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

# Numba：沒有安裝或設環境變數 H099_NO_NUMBA=1 時退回純 Python（只供除錯、交叉驗證）
# 不開 Numba 編譯快取（核心參數是 namedtuple，快取每次都對不上，只會在 __pycache__ 堆檔）；每個程序各自編譯約 20～40 秒
_NO_NUMBA =os.environ.get("H099_NO_NUMBA", "").strip().lower() in {"1", "true", "yes", "on"}
try:
    if _NO_NUMBA:
        raise ImportError
    from numba import njit
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

    def njit(*args, **kwargs):   # 退回純 Python 的替身裝飾器
        if args and callable(args[0]):
            return args[0]
        return lambda func: func


# ===== User Settings =====

MATH_ID = "H099"                       # 本作 Math ID（config 的 game_id 沿用彩罐熱舞 H026192A，報表檔名改用本作代號）
GAME_NAME_FALLBACK = "三隻小豬"
CONFIG_FILE = "config_99A.js"          # 一個產線一個系列一份 config（產線 99＝發想、系列 A）
CONFIG_TIER = "AUTO"                   # AUTO＝依押注檔位選層級；明寫層級代號即 override
EXPECTED_CONFIG_NAME = "99A"           # 驗證 config_name（game_id 沿用 H026192A，不拿來驗證）
# 檔位對應表：本作發想階段只有一層 92A，小／中／大 Bet、Newbie 全用 92{s}
TIER_CONFIG = {"small_bet": "92{s}", "medium_bet": "92{s}", "big_bet": "92{s}"}
NEWBIE_TIER = "92{s}"
TOTAL_ROUNDS = 100_000
BASE_BET_SETTING = 1.0
BET_MODE = 0                           # 0 = Normal Bet, 1 = Extra Bet, 2 = Buy Feature（沿用彩罐熱舞代號，同 config mode_*）
CARD_SYSTEM_ENABLED = False
CARD_SYSTEM_IS_NEWBIE = False

RUN_ALL_COMBINATIONS = True
BATCH_RUNS = [
    # --- 區塊 1：測試（流程與報表驗證）---
    {"config_file": "config_99A.js", "tier": "AUTO", "bet_mode": 0,
     "total_rounds": 10**5, "card_system_enabled": False, "card_system_is_newbie": False, "base_bet": 1.0},
    {"config_file": "config_99A.js", "tier": "AUTO", "bet_mode": 0,
     "total_rounds": 10**5, "card_system_enabled": True, "card_system_is_newbie": False, "base_bet": 1.0},
    # --- 區塊 2：自然機率（Card Off；要跑哪些 Bet Mode 先跟使用者確認）---
    # {"config_file": "config_99A.js", "tier": "AUTO", "bet_mode": 0,
    #  "total_rounds": 10**9, "card_system_enabled": False, "card_system_is_newbie": False, "base_bet": 1.0},
    # {"config_file": "config_99A.js", "tier": "AUTO", "bet_mode": 2,
    #  "total_rounds": 10**8, "card_system_enabled": False, "card_system_is_newbie": False, "base_bet": 1.0},
    # --- 區塊 3：SCR（Card On、彩金關；權重相同的組合只跑一筆）---
    # {"config_file": "config_99A.js", "tier": "AUTO", "bet_mode": 0,
    #  "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False, "base_bet": 1.0},
    # --- 區塊 4：正式模擬（Card On；Oldhand NB／EB／BF、Newbie）---
    # {"config_file": "config_99A.js", "tier": "AUTO", "bet_mode": 0,
    #  "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False, "base_bet": 1.0},
    # {"config_file": "config_99A.js", "tier": "AUTO", "bet_mode": 1,
    #  "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False, "base_bet": 1.0},
    # {"config_file": "config_99A.js", "tier": "AUTO", "bet_mode": 2,
    #  "total_rounds": 10**7, "card_system_enabled": True, "card_system_is_newbie": False, "base_bet": 1.0},
    # {"config_file": "config_99A.js", "tier": "AUTO", "bet_mode": 0,
    #  "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True, "base_bet": 1.0},
]
THREADS = max(1, min(24, os.cpu_count() or 1))   # 多程序（模擬機 24 核）
OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = True
RUN_SINGLE_SPIN_DEBUG = False
DEBUG_ROUNDS = 5
CARD_RETRY_LIMIT = 10_000
JACKPOT_ENABLED = True                 # 本作 config 沒有 jackpot 區塊，無作用
RNG_SEED = 99_099

COIN_BASE = 100.0                      # Credit 基準：NB 押注＝default_coin_in × normalbet ＝ 100 coin（Paytable 單位）
MODE_NORMALBET = 0
MODE_EXTRABET = 1
MODE_FEATUREBUY = 2
SUPPORTED_BET_MODES = (MODE_NORMALBET, MODE_EXTRABET, MODE_FEATUREBUY)
BUY_MODES = (MODE_FEATUREBUY,)

# Demo JS 寫死、config 沒有的 FG 常數（index.html：FEATURE_TRIGGER_SCATTER_MIN、FG_TRIGGER_BASE_SPINS、
# FG_EXTRA_SPINS_PER_SCATTER、FG_SPIN_CAP）；BF 進場表 JS 寫死表 6（＝strip_name_map 的 "BF"）
FG_TRIGGER_SCATTER_MIN = 3
FG_TRIGGER_BASE_SPINS = 10
FG_EXTRA_SPINS_PER_SCATTER = 5
FG_SPIN_CAP = 50

MULTIPLIER_THRESHOLDS = (
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50,
    60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 250, 300, 350, 400, 450,
    500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000,
    2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000,
    20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000, 9999999,
)

# ----- 核心統計陣列版位（Numba 編譯期常數）-----
NSYM_MAX = 32
LV_MAX = 8
TAB_MAX = 16
# scratch：每次嘗試的明細（Retry 時清零，只有被接受的那次併入統計）
SCR_SYM = 0                            # [符號 × 連線長度 3～5 × (hits, pay)]
SCR_COMBO = SCR_SYM + NSYM_MAX * 6     # 連消次數 0～4、5+（每轉）
SCR_FRM = SCR_COMBO + 6                # [框階數 × (刷倍數次數, 倍數合計)]
SCR_TAB = SCR_FRM + LV_MAX * 2         # [表 × (轉數, 得分轉數)]
SCR_BOOST_CNT = SCR_TAB + TAB_MAX * 2  # 依框數加權（by_frame_count）成功次數
SCR_BOOST_INIT = SCR_BOOST_CNT + 1     # 停輪加權（initial，豪宅局）轉金色格數
SCR_BOOST_DROP = SCR_BOOST_INIT + 1    # 補牌加權（drop）轉金色格數
SCR_GOLDCONV = SCR_BOOST_DROP + 1      # 金色符號中獎轉 Wild（框升階）次數
SCR_MAXLV = SCR_GOLDCONV + 1           # 結束時場上最高框階數分布（BG 每局；FG 每場結束）
SCR_ENDFR = SCR_MAXLV + LV_MAX         # 結束時各階框格數
SCR_MANSION = SCR_ENDFR + LV_MAX       # 豪宅局場數
SCR_GOOD = SCR_MANSION + 1             # 金色好局轉數
SCR_SPINS = SCR_GOOD + 1               # 轉數
SCR_CASC = SCR_SPINS + 1               # 連消次數合計
SCR_SIZE = SCR_CASC + 1

S_ROUNDS, S_COIN, S_PAY_BG, S_PAY_FG, S_WX, S_WX2, S_MAXWX, S_BG_HIT = 0, 1, 2, 3, 4, 5, 6, 7
S_FG_HIT, S_FG_SPINS, S_TRIG, S_RETRIG, S_CASC_BG, S_CASC_FG, S_SPECIAL = 8, 9, 10, 11, 12, 13, 14
S_FGY, S_FGY2, S_FGN, S_RETRY, S_EXC, S_EXC_BGR, S_EXC_BGF, S_EXC_FG = 15, 16, 17, 18, 19, 20, 21, 22
S_MAXMULT, S_MAX_FG_X, S_MAX_BG_X, S_FG_PLAYED = 23, 24, 25, 26
NS = 32
S_MAX_KEYS = (S_MAXWX, S_MAXMULT, S_MAX_FG_X, S_MAX_BG_X)

B_BG_CNT, B_BG_PAY, B_FG_CNT, B_FG_PAY, B_BF_CNT, B_BF_PAY, B_TRIG_CNT, B_TRIG_PAY = 0, 1, 2, 3, 4, 5, 6, 7
B_FG_HIT, B_FG_SPINS, B_BG_COMBO, B_FG_COMBO, B_BG_FRAMES, B_FG_END_FRAMES = 8, 9, 10, 15, 20, 21
NBCOL = 22

CARD_RANGE = 0
CARD_FREE = 1

CFG: dict[str, Any] = {}               # 本批展開後的 Box（base 疊上 tiers[層級]）
CFG_SET: dict[str, Any] = {}           # 整份 config（config_name、series、base、tiers）
CORE = None                            # 本程序的 Numba 核心資料


# ===== Config =====

def resolve_base_dir() -> Path:
    base = Path(__file__).resolve().parent
    if not (base / CONFIG_FILE).exists():
        raise FileNotFoundError(f"找不到 {CONFIG_FILE}，請在 {MATH_ID} 專案資料夾執行。")
    return base


BASE_DIR = resolve_base_dir()


def load_js_config(path: Path) -> dict[str, Any]:
    """取第一個 { 到最後一個 } 之間的文字，以 JSON 解析（模擬程式規範 §2.2.1）。"""
    text = path.read_text(encoding="utf-8")
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


def load_config_set(path: Path) -> dict[str, Any]:
    data = load_js_config(path)
    if "base" not in data or "tiers" not in data:
        raise ValueError(f"{path.name} 不是 base＋tiers 格式（模擬程式規範 §2.1）")
    if str(data.get("config_name")) != EXPECTED_CONFIG_NAME:
        raise ValueError(f"{path.name} 的 config_name 必須為 {EXPECTED_CONFIG_NAME}，目前為 {data.get('config_name')!r}")
    return data


def expand_tier(data: dict[str, Any], tier: str) -> dict[str, Any]:
    """base 疊上 tiers[層級]（淺層覆蓋，source 不疊入）＝ JS 的 H026_BOX_DATA。"""
    if tier not in data["tiers"]:
        raise ValueError(f"層級 {tier} 不存在；可用層級：{', '.join(data['tiers'])}")
    box = {**data["base"], **{k: v for k, v in data["tiers"][tier].items() if k != "source"}}
    version = str(box.get("excel_version", ""))
    parts = version.split(".")
    if len(parts) != 4 or not all(p.isdigit() for p in parts):
        raise ValueError(f"層級 {tier} 的 excel_version 必須為四段數字，目前為 {version!r}")
    base_version = data["base"].get("excel_version")
    if base_version is not None and str(base_version) != parts[0]:
        raise ValueError(f"層級 {tier} 版本第 1 碼 {parts[0]} 必須等於 base 版本 {base_version}")
    return box


def cost_multiplier(mode: int, box: dict[str, Any] | None = None) -> float:
    """模式成本倍數（JS coinIn：NB normalbet、EB extrabet、BF normalbet × featurebuy；皆以 normalbet 為 1）。"""
    box = box or CFG
    normal = float(box.get("normalbet", 1) or 1)
    if mode == MODE_EXTRABET:
        return float(box.get("extrabet", normal)) / normal
    if mode == MODE_FEATUREBUY:
        return float(box.get("featurebuy", 1))
    return 1.0


def wager_for_mode(mode: int, base_bet: float) -> float:
    """實際押注 ＝ base_bet × 模式成本倍數。"""
    return base_bet * cost_multiplier(mode)


def bet_tier_name(bet_tier_amount: float, base_bet: float) -> str:
    """模擬程式規範 §1.2.3：small < $2 ≤ medium ≤ $100 < big（$2 看 bet_tier_amount、$100 看基礎押注）。"""
    if bet_tier_amount < 2.0:
        return "small_bet"
    if base_bet <= 100.0:
        return "medium_bet"
    return "big_bet"


def load_batch_configs(combo: dict[str, Any]) -> None:
    global CFG, CFG_SET
    data = load_config_set(BASE_DIR / combo["config_file"])
    CFG_SET = data
    if str(combo.get("tier", "AUTO")).upper() == "AUTO":
        mode, base_bet = int(combo["bet_mode"]), float(combo["base_bet"])
        amount = base_bet if mode in BUY_MODES else base_bet * cost_multiplier(mode, data["base"])
        tpl = NEWBIE_TIER if combo.get("card_system_is_newbie") else TIER_CONFIG[bet_tier_name(amount, base_bet)]
        combo["tier"] = tpl.format(s=data["series"])
        print(f"[auto] bet_mode {mode}、base_bet {base_bet:g}（檔位金額 ${amount:g}）→ {combo['config_file']} 層級 {combo['tier']}")
    CFG = expand_tier(data, combo["tier"])
    if combo["card_system_enabled"] and not (CFG.get("card_system") or {}).get("enabled", False):
        print(f"[warn] 層級 {combo['tier']} 的 card_system 未啟用，本批改以 Card System Off 執行。")
        combo["card_system_enabled"] = False
    limit = (CFG.get("card_system") or {}).get("retry_limit")
    if limit is not None and int(limit) != CARD_RETRY_LIMIT:
        print(f"[warn] config retry_limit {limit} 與 CARD_RETRY_LIMIT {CARD_RETRY_LIMIT} 不同，以 CARD_RETRY_LIMIT 為準。")


def validate_batch_run(combo: dict[str, Any]) -> dict[str, Any]:
    required = {"config_file", "tier", "bet_mode", "total_rounds",
                "card_system_enabled", "card_system_is_newbie", "base_bet"}
    missing = required - set(combo)
    if missing:
        raise ValueError(f"BATCH_RUNS 缺少必要欄位：{sorted(missing)}")
    if int(combo["bet_mode"]) not in SUPPORTED_BET_MODES:
        raise ValueError(f"不支援的 bet_mode {combo['bet_mode']}；本作只有 0 / 1 / 2")
    if int(combo["total_rounds"]) <= 0:
        raise ValueError("total_rounds 必須為正整數")
    if float(combo["base_bet"]) <= 0:
        raise ValueError("base_bet 必須大於 0")
    return combo


def profile_cards(box: dict[str, Any], profile: str, bet_mode: int, deck: str) -> list[dict[str, Any]]:
    """JS getCardSystemProfileCards：Profile → 押注（normal_bet／extra_bet／buy_feature）→ weight_bg／weight_fg；本 Profile 沒有時用另一個 Profile。"""
    cs = box.get("card_system") or {}
    other = "oldhand" if profile == "newbie" else "newbie"
    if deck == "bf":
        for key in (profile, other):
            cards = ((cs.get(key) or {}).get("buy_feature") or {}).get("weight_fg") or []
            if cards:
                return cards
        return []
    bet_key = "extra_bet" if bet_mode == MODE_EXTRABET else "normal_bet"
    field = "weight_bg" if deck == "bg" else "weight_fg"
    for key in (profile, other):
        cards = ((cs.get(key) or {}).get(bet_key) or {}).get(field) or []
        if cards:
            return cards
    return []


def bg_trigger_cap(box: dict[str, Any], profile: str, bet_mode: int) -> float | None:
    """BG Trigger Cap：同卡組正權重 range 卡的最大 max（JS bgTriggerCap）。"""
    caps = [float(c["max"]) for c in profile_cards(box, profile, bet_mode, "bg")
            if (c.get("type") or "range") == "range" and float(c.get("weight", 0)) > 0]
    return max(caps) if caps else None


def _levels(values: Any) -> list[float] | None:
    """JS boostLevels：有任一 > 0 才算有設定。"""
    if isinstance(values, list) and any(float(v) > 0 for v in values):
        return [float(v) for v in values]
    return None


Core = namedtuple("Core", [
    "rows", "nreel", "off", "wild", "scatter", "nsym",
    "reels", "reel_len", "reel_cum", "sc_win", "grp_cum", "grp_idx", "grp_n", "cond_k", "cond_cum", "cond_n", "base_of", "is_gold", "gold_of_base", "is_score",
    "drop_cum", "elim_cum", "bg_table_cum", "paylines", "pay", "score_syms",
    "frame_vals", "frame_cum", "frame_n", "frame_max", "gold_col", "drops_scatter",
    "boost_init", "boost_drop", "boost_count", "boost_count_len", "boost_flags",
    "fg_default_table", "fg_pre_brick_table", "bf_table", "good_table", "good_slots", "n_good_slots",
    "mansion_prob", "mansion_table", "retrigger_spins", "fg_cap", "trig_min", "trig_base", "trig_extra",
    "card_type", "card_min", "card_max", "card_cum", "card_n", "bg_cap", "retry_limit", "thresholds",
])


def build_core(box: dict[str, Any], profile: str, bet_mode: int) -> Core:
    """把 Box 正規化成 Numba 核心用的固定型別陣列（符號 ID 由 symbol_str 綁定，不寫死）。"""
    sym_str = {int(k): v for k, v in box["symbol_str"].items()}
    wild = next(k for k, v in sym_str.items() if v == "WW")
    scatter = next(k for k, v in sym_str.items() if v == "C1")
    symbol_id = [int(s) for s in box["symbol_id"]]
    nsym = len(symbol_id)
    if nsym > NSYM_MAX or symbol_id != list(range(nsym)):
        raise ValueError("symbol_id 必須為 0..n-1 且 n ≤ NSYM_MAX")
    nreel = int(box["reel_num"])
    rows = int(box["window_size"]) + 1
    off = rows - int(box["window_size"])
    nt = len(box["arr_reels"])
    if nt > TAB_MAX:
        raise ValueError("表數超過 TAB_MAX")
    reels_len = np.array(box["reels_len"], dtype=np.int64)
    lmax = int(reels_len.max())
    reels = np.zeros((nt, lmax, nreel), dtype=np.int64)
    reel_cum = np.zeros((nt, nreel, lmax), dtype=np.int64)
    for t in range(nt):
        for col in range(nreel):
            length = int(reels_len[t, col])
            for i in range(length):
                reels[t, i, col] = int(box["arr_reels"][t][i][col])
                reel_cum[t, col, i] = int(box["arr_reels_weight_cum"][t][i][col])
            reel_cum[t, col, length:] = reel_cum[t, col, length - 1]
    # 每個停輪位置顯示的 rows 格（含 peek 列）裡的 Scatter 數，供 min_scatter 加速判斷
    sc_win = np.zeros((nt, nreel, lmax), dtype=np.int64)
    for t in range(nt):
        for col in range(nreel):
            length = int(reels_len[t, col])
            for i in range(length):
                start = (i - off + length) % length
                sc_win[t, col, i] = sum(1 for r in range(rows)
                                        if int(box["base_symbol_of"][reels[t, (start + r) % length, col]]) == scatter)
    # BF 進場盤條件抽樣（只用在「補牌不會補 Scatter」的表）：先依各軸 Scatter 數 k 的聯合機率抽出
    # 「窗內 Scatter 合計 ≥ 觸發數」的組合，再在各軸該 k 的停輪位置中依權重抽停輪；
    # 與 JS「整盤重抽到 Scatter 夠」的分布完全相同（JS 的 BF 進場重抽不計入卡片 Retry）。
    kmax = rows + 1
    grp_cum = np.zeros((nt, nreel, kmax, lmax), dtype=np.int64)
    grp_idx = np.zeros((nt, nreel, kmax, lmax), dtype=np.int64)
    grp_n = np.zeros((nt, nreel, kmax), dtype=np.int64)
    weights = np.zeros((nt, nreel, kmax), dtype=np.float64)
    for t in range(nt):
        for col in range(nreel):
            length = int(reels_len[t, col])
            prev = 0
            for i in range(length):
                w = int(reel_cum[t, col, i]) - prev
                prev = int(reel_cum[t, col, i])
                if w <= 0:
                    continue
                k = int(sc_win[t, col, i])
                n = grp_n[t, col, k]
                grp_idx[t, col, k, n] = i
                grp_cum[t, col, k, n] = (grp_cum[t, col, k, n - 1] if n else 0) + w
                grp_n[t, col, k] = n + 1
                weights[t, col, k] += w
    combos = [c for c in np.ndindex(*([kmax] * nreel)) if sum(c) >= FG_TRIGGER_SCATTER_MIN]
    cond_k = np.zeros((nt, max(1, len(combos)), nreel), dtype=np.int64)
    cond_cum = np.zeros((nt, max(1, len(combos))), dtype=np.float64)
    cond_n = np.zeros(nt, dtype=np.int64)
    for t in range(nt):
        n = 0
        running = 0.0
        for c in combos:
            p = 1.0
            for col, k in enumerate(c):
                p *= weights[t, col, k] / float(reel_cum[t, col, int(reels_len[t, col]) - 1])
            if p <= 0.0:
                continue
            running += p
            cond_k[t, n] = c
            cond_cum[t, n] = running
            n += 1
        cond_n[t] = n
    base_of = np.array(box["base_symbol_of"], dtype=np.int64)
    is_gold = np.array(box["is_gold_symbol"], dtype=np.int64)
    is_score = np.array(box["is_score_symbol"], dtype=np.int64)
    gold_of_base = np.full(nsym, -1, dtype=np.int64)   # JS GOLD_OF_BASE：一般符號 → 金色版本
    for sid in symbol_id:
        if is_gold[sid]:
            gold_of_base[base_of[sid]] = sid
    drop_cum = np.zeros((2, nt, nreel, nsym), dtype=np.int64)
    for m, key in enumerate(("drop_weight_a_cum", "drop_weight_b_cum")):
        for t in range(nt):
            for s in range(nsym):
                for col in range(nreel):
                    drop_cum[m, t, col, s] = int(box[key][t][s][col])
    drops_scatter = np.zeros(nt, dtype=np.int64)   # JS TABLE_DROPS_SCATTER：補牌會不會補出 Scatter
    for t in range(nt):
        for key in ("drop_weight_a", "drop_weight_b"):
            if any(float(w) > 0 for w in box[key][t][scatter]):
                drops_scatter[t] = 1
    elim_cum = np.zeros((3, 2), dtype=np.int64)
    bg = box.get("eliminate_table_weight_cum_bg") or [1, 2]
    fg = box.get("eliminate_table_weight_cum_fg") or [1, 2]
    bf = box.get("eliminate_table_weight_cum_bf") or fg
    for i, cum in enumerate((bg, fg, bf)):
        elim_cum[i] = [int(cum[0]), int(cum[-1])]
    bg_table_cum = np.array(box["weight_cum_table_bg"], dtype=np.int64)
    paylines = np.array(box["paylines"], dtype=np.int64)
    pay = np.array(box["pay_table"], dtype=np.float64)
    score_syms = np.array(box["symbols_score"], dtype=np.int64)

    # 框倍數表：set 0＝BG（frame_multiplier_bg 有該階才用，否則同 FG）、set 1＝FG／BF
    fm = box["frame_multiplier"]
    keys = fm.get("levels") or ["plain", "straw", "wood", "brick"]
    frame_max = len(keys)
    if frame_max >= LV_MAX:
        raise ValueError("框階數超過 LV_MAX")
    fm_bg = box.get("frame_multiplier_bg") or {}
    vmax = 1
    tables: dict[tuple[int, int], dict[str, Any] | None] = {}
    for lv, key in enumerate(keys, start=1):
        main = None if key == "plain" else fm[key]
        tables[(1, lv)] = main
        tables[(0, lv)] = fm_bg.get(key) or main
        for tb in (tables[(0, lv)], tables[(1, lv)]):
            if tb:
                vmax = max(vmax, len(tb["values"]))
    frame_vals = np.zeros((2, LV_MAX, vmax), dtype=np.float64)
    frame_cum = np.zeros((2, LV_MAX, vmax), dtype=np.int64)
    frame_n = np.zeros((2, LV_MAX), dtype=np.int64)
    for (fs, lv), tb in tables.items():
        if not tb:
            continue
        n = len(tb["values"])
        frame_n[fs, lv] = n
        frame_vals[fs, lv, :n] = [float(v) for v in tb["values"]]
        frame_cum[fs, lv, :n] = np.cumsum([int(w) for w in tb["weights"]])
    gold_col = np.zeros(nreel, dtype=np.int64)   # JS GOLD_COLS：輪帶上出現過金色符號的輪
    for t in range(nt):
        for row in box["arr_reels"][t]:
            for col, s in enumerate(row):
                if is_gold[int(s)]:
                    gold_col[col] = 1

    # 框上金色加權（JS frameGoldBoostFor）：set 0 bg、1 fg、2 bf、3 fg.mansion
    gb = box.get("frame_gold_boost") or {}
    boost_init = np.zeros((4, LV_MAX), dtype=np.float64)
    boost_drop = np.zeros((4, LV_MAX), dtype=np.float64)
    boost_count = np.zeros((4, 16), dtype=np.float64)
    boost_count_len = np.ones(4, dtype=np.int64)
    boost_flags = np.zeros((4, 5), dtype=np.int64)   # has_init, has_drop, has_count, stop_on_brick, target_top
    sources = [(gb.get("bg"), False), (gb.get("fg"), False), (gb.get("bf"), False),
               ((gb.get("fg") or {}).get("mansion"), True)]
    for i, (src, mansion) in enumerate(sources):
        if not src:
            continue
        init, drop, count = _levels(src.get("initial")), _levels(src.get("drop")), _levels(src.get("by_frame_count"))
        if not init and not drop and not count:
            continue
        if init:
            boost_init[i, :min(len(init), LV_MAX)] = init[:LV_MAX]
            boost_flags[i, 0] = 1
        if drop:
            boost_drop[i, :min(len(drop), LV_MAX)] = drop[:LV_MAX]
            boost_flags[i, 1] = 1
        if count:
            boost_count[i, :min(len(count), 16)] = count[:16]
            boost_count_len[i] = min(len(count), 16)
            boost_flags[i, 2] = 1
        boost_flags[i, 3] = 1 if (not mansion and bool(src.get("stop_on_brick"))) else 0
        boost_flags[i, 4] = 1 if (not mansion and (src.get("target") or "all") == "top_frame") else 0

    # FG 選表：fg_table_rule 依累積倍數（本作 FG 累積一律 0）→ 預設表；沒有對到規則用表 3（同 JS）
    fg_default = 3
    for rule in (box.get("fg_table_rule") or {}).get("rules") or []:
        lo = float(rule.get("min_multiplier") or 0)
        hi = rule.get("max_exclusive")
        if 0 < lo or (hi is not None and 0 >= float(hi)):
            continue
        fg_default = int(rule["table_id"])
        break
    pre_brick = box.get("fg_pre_brick_table_id")
    good = box.get("fg_good_slots") or None
    slots = (good or {}).get("slots") or []
    good_slots = np.zeros((max(1, len(slots)), 4), dtype=np.int64)
    for i, slot in enumerate(slots):
        good_slots[i] = [1 if slot.get("anchor") == "end" else 0, int(slot["from"]), int(slot["to"]), int(slot["count"])]
    mansion = (gb.get("fg") or {}).get("mansion") or None
    names = list(box.get("strip_name_map") or [])
    bf_table = names.index("BF") if "BF" in names else 6

    # Card System 卡組：deck 0＝BG、1＝FG、2＝BF
    decks = [profile_cards(box, profile, bet_mode, d) for d in ("bg", "fg", "bf")]
    nc = max(1, max(len(d) for d in decks))
    card_type = np.zeros((3, nc), dtype=np.int64)
    card_min = np.zeros((3, nc), dtype=np.float64)
    card_max = np.zeros((3, nc), dtype=np.float64)
    card_cum = np.zeros((3, nc), dtype=np.int64)
    card_n = np.zeros(3, dtype=np.int64)
    for d, cards in enumerate(decks):
        running = 0
        for i, card in enumerate(cards):
            card_type[d, i] = CARD_FREE if card.get("type") == "free_game" else CARD_RANGE
            card_min[d, i] = float(card.get("min") or 0)
            card_max[d, i] = float(card.get("max") or 0)
            running += int(card.get("weight") or 0)
            card_cum[d, i] = running
        card_n[d] = len(cards)
    cap = bg_trigger_cap(box, profile, bet_mode)

    return Core(
        rows=rows, nreel=nreel, off=off, wild=wild, scatter=scatter, nsym=nsym,
        reels=reels, reel_len=reels_len, reel_cum=reel_cum, sc_win=sc_win,
        grp_cum=grp_cum, grp_idx=grp_idx, grp_n=grp_n, cond_k=cond_k, cond_cum=cond_cum, cond_n=cond_n, base_of=base_of, is_gold=is_gold,
        gold_of_base=gold_of_base, is_score=is_score, drop_cum=drop_cum, elim_cum=elim_cum,
        bg_table_cum=bg_table_cum, paylines=paylines, pay=pay, score_syms=score_syms,
        frame_vals=frame_vals, frame_cum=frame_cum, frame_n=frame_n, frame_max=frame_max,
        gold_col=gold_col, drops_scatter=drops_scatter,
        boost_init=boost_init, boost_drop=boost_drop, boost_count=boost_count,
        boost_count_len=boost_count_len, boost_flags=boost_flags,
        fg_default_table=int(fg_default),
        fg_pre_brick_table=int(pre_brick) if pre_brick is not None else -1,
        bf_table=int(bf_table),
        good_table=int(good["table_id"]) if good and slots else -1,
        good_slots=good_slots, n_good_slots=len(slots),
        mansion_prob=float(mansion.get("prob") or 0) if mansion else 0.0,
        mansion_table=int(mansion["table_id"]) if mansion and mansion.get("table_id") is not None else -1,
        retrigger_spins=int(box["fg_retrigger_spins"]) if box.get("fg_retrigger_spins") is not None else -1,
        fg_cap=FG_SPIN_CAP, trig_min=FG_TRIGGER_SCATTER_MIN, trig_base=FG_TRIGGER_BASE_SPINS,
        trig_extra=FG_EXTRA_SPINS_PER_SCATTER,
        card_type=card_type, card_min=card_min, card_max=card_max, card_cum=card_cum, card_n=card_n,
        bg_cap=float(cap) if cap is not None else -1.0, retry_limit=int(CARD_RETRY_LIMIT),
        thresholds=np.array(MULTIPLIER_THRESHOLDS, dtype=np.float64),
    )


# ===== 遊戲核心 =====
# 內部場景代號：0＝BG、1＝FG、2＝BF（BF 進場盤）；得分單位 coin（NB 押注 100 coin）

@njit(cache=False)
def _pick_cum(cum, n, r):
    """第一個 r < cum[i] 的 i（JS pickByCum）。"""
    lo = 0
    hi = n - 1
    while lo < hi:
        mid = (lo + hi) >> 1
        if r < cum[mid]:
            hi = mid
        else:
            lo = mid + 1
    return lo


@njit(cache=False)
def _has_brick(C, frames):
    """JS framesHaveBrick：場上有沒有到頂階（磚頭）的框。"""
    for r in range(C.rows):
        for c in range(C.nreel):
            if frames[r, c] >= C.frame_max:
                return True
    return False


@njit(cache=False)
def _pick_frame_value(C, fs, lv):
    """JS pickFrameValue：依該階權重抽一個框倍數（plain 階沒有表＝0）。"""
    n = C.frame_n[fs, lv]
    if n <= 0:
        return 0.0
    tot = C.frame_cum[fs, lv, n - 1]
    if tot <= 0:
        return C.frame_vals[fs, lv, n - 1]
    return C.frame_vals[fs, lv, _pick_cum(C.frame_cum[fs, lv], n, np.random.randint(0, tot))]


@njit(cache=False)
def _boost_prob(C, levels, frames, row, col, target_top, top_r, top_c):
    """JS boostProbAt：只在可出金色的輪；target＝top_frame 時只加權階數最高那格；機率＝levels[該格框階數]。"""
    if C.gold_col[col] == 0:
        return 0.0
    if target_top == 1 and top_r >= 0 and not (top_r == row and top_c == col):
        return 0.0
    return levels[frames[row, col]]


@njit(cache=False)
def _eval_board(C, board, hit, scr):
    """JS evaluateBoard：20 線由左至右；Wild 開頭時取得分最高的符號（同分取 symbols_score 順序在前者）。"""
    total = 0.0
    nl = C.paylines.shape[0]
    ns = C.score_syms.shape[0]
    for line in range(nl):
        s0 = board[C.paylines[line, 0] + C.off, 0]
        if s0 == C.scatter:
            continue
        best_sym = -1
        best_len = 0
        best_pay = 0.0
        if s0 == C.wild:
            for k in range(ns):
                sym = C.score_syms[k]
                ln = 0
                for reel in range(C.nreel):
                    s = board[C.paylines[line, reel] + C.off, reel]
                    if s == C.scatter:
                        break
                    if C.base_of[s] == sym or s == C.wild:
                        ln += 1
                    else:
                        break
                p = 0.0
                if ln >= 3 and C.is_score[sym] == 1:
                    p = C.pay[sym, ln - 3]
                if p > best_pay:
                    best_sym = sym
                    best_len = ln
                    best_pay = p
        else:
            first = C.base_of[s0]
            ln = 0
            for reel in range(C.nreel):
                s = board[C.paylines[line, reel] + C.off, reel]
                if s == C.scatter:
                    break
                if C.base_of[s] == first or s == C.wild:
                    ln += 1
                else:
                    break
            best_sym = first
            best_len = ln
            if ln >= 3 and C.is_score[first] == 1:
                best_pay = C.pay[first, ln - 3]
        if best_pay <= 0.0:
            continue
        for reel in range(best_len):
            hit[C.paylines[line, reel] + C.off, reel] = 1
        total += best_pay
        base = SCR_SYM + best_sym * 6 + (best_len - 3) * 2
        scr[base] += 1.0
        scr[base + 1] += best_pay
    return total


@njit(cache=False)
def _run_spin(C, scene, table_override, frames, has_frames_in, boost_set, min_scatter, scr, cond_sample):
    """JS runSpin：選表 → 補牌模式 → 停輪 → 框上金色加權 → 連消（判獎、金色轉 Wild 升框、重力掉落補牌）→ 刷框倍數。

    frames 為進出參數（FG 跨局保留；BG／BF 傳入全 0）。回傳
    (ok, final_pay, raw_pay, cascades, scatter_count, frame_total, max_level, frame_cells, table_id)；
    ok＝False 表示 min_scatter 加速略過（停輪盤面含 peek 列 Scatter 不夠、且該表補牌不會補 Scatter，必定重抽）。
    cond_sample＝True（BF 進場盤）時直接條件抽樣窗內 Scatter ≥ 觸發數的停輪，分布同重抽（已與重抽版 3×10^5 局對照一致）。"""
    R = C.rows
    NR = C.nreel
    OFF = C.off
    # chooseTable
    if scene == 1 and table_override >= 0:
        t = table_override
    elif scene == 0:
        nb = C.bg_table_cum.shape[0]
        t = _pick_cum(C.bg_table_cum, nb, np.random.randint(0, C.bg_table_cum[nb - 1]))
    elif scene == 1:
        t = C.fg_default_table
    else:
        t = C.bf_table
    # generateBoard 的停輪：停輪位置是第一列判獎列，頂端 peek 列在它上面
    stops = np.empty(NR, dtype=np.int64)
    n_sc = 0
    if cond_sample and min_scatter == C.trig_min and C.drops_scatter[t] == 0 and C.cond_n[t] > 0:
        # BF 進場盤條件抽樣（見 build_core）：直接抽「窗內 Scatter ≥ 觸發數」的停輪
        nn = C.cond_n[t]
        ci = _pick_cum(C.cond_cum[t], nn, np.random.random() * C.cond_cum[t, nn - 1])
        for col in range(NR):
            k = C.cond_k[t, ci, col]
            gn = C.grp_n[t, col, k]
            j = _pick_cum(C.grp_cum[t, col, k], gn, np.random.randint(0, C.grp_cum[t, col, k, gn - 1]))
            stops[col] = C.grp_idx[t, col, k, j]
            n_sc += k
    else:
        for col in range(NR):
            L = C.reel_len[t, col]
            idx = _pick_cum(C.reel_cum[t, col], L, np.random.randint(0, C.reel_cum[t, col, L - 1]))
            stops[col] = idx
            n_sc += C.sc_win[t, col, idx]
    # 加速（JS minScatter）：停輪盤面（含 peek 列）Scatter 不夠、且補牌不會補出 Scatter → 必定被重抽，不跑連消
    # （此處比 JS 更早判斷：連補牌模式都還沒抽；被略過的盤面本來就丟棄，分布不變）
    if min_scatter > 0 and C.drops_scatter[t] == 0 and n_sc < min_scatter:
        return False, 0.0, 0.0, 0, 0, 0.0, 0, 0, t
    # chooseEliminateMode（補牌 A／B）
    mode = 0
    etot = C.elim_cum[scene, 1]
    if etot > 0:
        mode = 0 if np.random.randint(0, etot) < C.elim_cum[scene, 0] else 1
    board = np.empty((R, NR), dtype=np.int64)
    gold = np.zeros((R, NR), dtype=np.int64)
    for col in range(NR):
        L = C.reel_len[t, col]
        start = (stops[col] - OFF + L) % L
        for row in range(R):
            s = C.reels[t, (start + row) % L, col]
            board[row, col] = C.base_of[s]
            gold[row, col] = C.is_gold[s]

    flags = C.boost_flags[boost_set]
    brick = _has_brick(C, frames)
    # 依框數加權（FG 第 2 轉起）：依場上框數 n 取機率，中了就在「還沒到磚頭、停到一般符號」的框隨機挑一格改金色
    if flags[2] == 1 and has_frames_in and not (flags[3] == 1 and brick):
        frame_count = 0
        cand_r = np.empty(R * NR, dtype=np.int64)
        cand_c = np.empty(R * NR, dtype=np.int64)
        ncand = 0
        for row in range(OFF, R):
            for col in range(NR):
                lv = frames[row, col]
                if lv <= 0:
                    continue
                frame_count += 1
                if lv < C.frame_max and C.gold_col[col] == 1 and gold[row, col] == 0 and C.gold_of_base[board[row, col]] >= 0:
                    cand_r[ncand] = row
                    cand_c[ncand] = col
                    ncand += 1
        prob = 0.0
        if frame_count > 0:
            prob = C.boost_count[boost_set, min(frame_count, C.boost_count_len[boost_set] - 1)]
        if prob > 0.0 and ncand > 0 and np.random.random() < prob:
            k = np.random.randint(0, ncand)
            gold[cand_r[k], cand_c[k]] = 1
            scr[SCR_BOOST_CNT] += 1.0
    # 停輪金色加權（依框階數；本作只有豪宅局用：沒框／茅草／木頭 100%、磚頭 0）
    top_r = -1
    top_c = -1
    if flags[4] == 1:
        best = 0
        for row in range(OFF, R):
            for col in range(NR):
                if frames[row, col] > best:
                    best = frames[row, col]
                    top_r = row
                    top_c = col
    if flags[0] == 1 and not (flags[3] == 1 and brick):
        for row in range(OFF, R):
            for col in range(NR):
                prob = _boost_prob(C, C.boost_init[boost_set], frames, row, col, flags[4], top_r, top_c)
                if prob > 0.0 and gold[row, col] == 0 and C.gold_of_base[board[row, col]] >= 0 and np.random.random() < prob:
                    gold[row, col] = 1
                    scr[SCR_BOOST_INIT] += 1.0

    hit = np.zeros((R, NR), dtype=np.int64)
    keep_s = np.empty(R, dtype=np.int64)
    keep_g = np.empty(R, dtype=np.int64)
    raw = 0.0
    nc = 0
    while True:
        hit[:, :] = 0
        total = _eval_board(C, board, hit, scr)
        if total <= 0.0:
            break
        nc += 1
        raw += total
        # applyHitAndTransform：中獎的金色符號原位轉 Wild、該格框升一階（最多 frame_max）；其他中獎符號消除
        for row in range(R):
            for col in range(NR):
                if hit[row, col] != 1:
                    continue
                if gold[row, col] == 1:
                    lv = frames[row, col] + 1
                    frames[row, col] = lv if lv < C.frame_max else C.frame_max
                    hit[row, col] = 2
                    scr[SCR_GOLDCONV] += 1.0
                else:
                    board[row, col] = -1
                    gold[row, col] = 0
        # cascadeDrop：留下的符號（含轉出的 Wild）往下掉，空格由下往上補（同軸已有 C1 不再補 C1）
        drop_active = flags[1] == 1 and not (flags[3] == 1 and _has_brick(C, frames))
        for col in range(NR):
            nk = 0
            for row in range(R - 1, -1, -1):
                h = hit[row, col]
                if h == 0:
                    keep_s[nk] = board[row, col]
                    keep_g[nk] = gold[row, col]
                    nk += 1
                elif h == 2:
                    keep_s[nk] = C.wild
                    keep_g[nk] = 0
                    nk += 1
            k = 0
            for row in range(R - 1, -1, -1):
                if k < nk:
                    board[row, col] = keep_s[k]
                    gold[row, col] = keep_g[k]
                    k += 1
                else:
                    board[row, col] = -1
                    gold[row, col] = 0
            has_c1 = False
            for row in range(R):
                if board[row, col] == C.scatter:
                    has_c1 = True
            for row in range(R - 1, -1, -1):
                if board[row, col] >= 0:
                    continue
                dcum = C.drop_cum[mode, t, col]
                dtot = dcum[C.nsym - 1]
                while True:   # JS pickDropSymbol：同軸已有 C1 抽到 C1 就重抽
                    ds = _pick_cum(dcum, C.nsym, np.random.randint(0, dtot))
                    bs = C.base_of[ds]
                    if has_c1 and bs == C.scatter:
                        continue
                    break
                if drop_active:
                    prob = _boost_prob(C, C.boost_drop[boost_set], frames, row, col, flags[4], top_r, top_c)
                    if prob > 0.0 and C.is_gold[ds] == 0 and C.gold_of_base[bs] >= 0 and np.random.random() < prob:
                        ds = C.gold_of_base[bs]
                        scr[SCR_BOOST_DROP] += 1.0
                board[row, col] = bs
                gold[row, col] = C.is_gold[ds]
                if bs == C.scatter and row >= OFF:
                    has_c1 = True

    sc = 0
    for row in range(OFF, R):
        for col in range(NR):
            if board[row, col] == C.scatter:
                sc += 1
    # revealFrames：本局有得分才刷框倍數；Mult＝1＋所有框倍數（BG 用 frame_multiplier_bg，若有）
    ftotal = 0.0
    maxlv = 0
    nfr = 0
    fs = 0 if scene == 0 else 1
    for row in range(R):
        for col in range(NR):
            lv = frames[row, col]
            if lv <= 0:
                continue
            nfr += 1
            if lv > maxlv:
                maxlv = lv
            if raw > 0.0:
                v = _pick_frame_value(C, fs, lv)
                ftotal += v
                scr[SCR_FRM + lv * 2] += 1.0
                scr[SCR_FRM + lv * 2 + 1] += v
    final = raw * (1.0 + ftotal)
    scr[SCR_COMBO + min(nc, 5)] += 1.0
    scr[SCR_CASC] += nc
    scr[SCR_SPINS] += 1.0
    scr[SCR_TAB + t * 2] += 1.0
    if raw > 0.0:
        scr[SCR_TAB + t * 2 + 1] += 1.0
    return True, final, raw, nc, sc, ftotal, maxlv, nfr, t


@njit(cache=False)
def _draw_good(C, good, k, total, after):
    """JS drawGoodSlot：在 [lo, hi]（end 錨點從最後一局往前算）且 > after 的局中，均勻抽 count 局標為金色好局。"""
    anchor = C.good_slots[k, 0]
    lo = C.good_slots[k, 1]
    hi = C.good_slots[k, 2]
    cnt = C.good_slots[k, 3]
    if anchor == 1:
        lo, hi = total - hi + 1, total - lo + 1
    a = max(1, max(lo, after + 1))
    b = min(total, hi)
    n = b - a + 1
    if n <= 0:
        return good
    if b >= good.shape[0]:
        bigger = np.zeros(b + 64, dtype=np.int64)
        bigger[:good.shape[0]] = good
        good = bigger
    cand = np.arange(a, b + 1)
    for i in range(min(cnt, n)):
        j = i + np.random.randint(0, n - i)
        tmp = cand[i]
        cand[i] = cand[j]
        cand[j] = tmp
        good[cand[i]] = 1
    return good


@njit(cache=False)
def _run_fg(C, awarded, scr):
    """JS runFreeGameSequence：框整場保留；金色好局；豪宅局；3+ Scatter 加局（剩餘上限 fg_cap），加局後尾段好局重抽（舊的保留）。

    回傳 (total_pay, played, hit_spins, retriggers, special_spins, max_mult, end_frame_cells)。"""
    cap = C.fg_cap
    remaining = min(awarded, cap)
    frames = np.zeros((C.rows, C.nreel), dtype=np.int64)
    good = np.zeros(remaining + 64, dtype=np.int64)
    if C.good_table >= 0:
        for k in range(C.n_good_slots):
            good = _draw_good(C, good, k, remaining, 0)
    is_m = False
    if C.mansion_prob > 0.0:
        is_m = np.random.random() < C.mansion_prob
    total = 0.0
    played = 0
    hits = 0
    retrig = 0
    special = 0
    maxmult = 1.0
    has_in = False
    while remaining > 0:
        idx = played + 1
        is_good = idx < good.shape[0] and good[idx] == 1
        # 選表優先順序：豪宅局 → 金色好局 → 還沒出磚頭（fg_pre_brick_table_id，若有）→ 預設表
        if is_m and C.mansion_table >= 0:
            tov = C.mansion_table
        elif is_good:
            tov = C.good_table
        elif C.fg_pre_brick_table >= 0 and not _has_brick(C, frames):
            tov = C.fg_pre_brick_table
        else:
            tov = -1
        bset = 3 if is_m else 1
        ok, fp, raw, nc, sc, ft, mlv, nfr, t = _run_spin(C, 1, tov, frames, has_in, bset, 0, scr, False)
        has_in = True
        remaining -= 1
        if sc >= C.trig_min:
            add = C.retrigger_spins if C.retrigger_spins >= 0 else C.trig_base + (sc - C.trig_min) * C.trig_extra
            remaining = min(remaining + add, cap)
            if add > 0:
                retrig += 1
            if C.good_table >= 0:
                for k in range(C.n_good_slots):
                    if C.good_slots[k, 0] == 1:
                        good = _draw_good(C, good, k, idx + remaining, idx)
        played += 1
        total += fp
        if raw > 0.0:
            hits += 1
            if 1.0 + ft > maxmult:
                maxmult = 1.0 + ft
        if sc > 0:
            special += 1
        if is_good:
            scr[SCR_GOOD] += 1.0
    end_cells = 0
    maxlv = 0
    for r in range(C.rows):
        for c in range(C.nreel):
            lv = frames[r, c]
            if lv > 0:
                end_cells += 1
                scr[SCR_ENDFR + lv] += 1.0
                if lv > maxlv:
                    maxlv = lv
    scr[SCR_MAXLV + maxlv] += 1.0
    if is_m:
        scr[SCR_MANSION] += 1.0
    return total, played, hits, retrig, special, maxmult, end_cells


@njit(cache=False)
def _pick_card(C, deck):
    """JS pickCardSystemEntry：依權重抽卡；卡組空或總權重 0 回傳 -1（不套卡片）。"""
    n = C.card_n[deck]
    if n <= 0:
        return -1
    tot = C.card_cum[deck, n - 1]
    if tot <= 0:
        return -1
    return _pick_cum(C.card_cum[deck], n, np.random.randint(0, tot))


@njit(cache=False)
def _range_match(C, deck, card, x):
    """JS isCardSystemMatch（已觸發 FG 的情境）：沒卡或 free_game 卡＝符合；range 卡 min < x <= max。"""
    if card < 0 or C.card_type[deck, card] == CARD_FREE:
        return True
    return x > C.card_min[deck, card] and x <= C.card_max[deck, card]


@njit(cache=False)
def _bucket(C, x):
    th = C.thresholds
    for i in range(th.shape[0]):
        if x <= th[i]:
            return i
    return th.shape[0] - 1


@njit(cache=False)
def _simulate_chunk(C, n_rounds, mode_kind, card_on, cost, seed, S, B, G):
    """跑 n_rounds 個付費局並累加統計（JS runRound，含 Card System）。mode_kind：0＝NB／EB、1＝BF。

    得分在核心內是 coin（NB 押注 100 coin）；寫入統計時換成「NB 底注倍數」x。"""
    np.random.seed(seed)
    R = C.rows
    NR = C.nreel
    scr_bg = np.zeros(SCR_SIZE)
    scr_fg = np.zeros(SCR_SIZE)
    frames0 = np.zeros((R, NR), dtype=np.int64)
    limit = C.retry_limit
    tmin = C.trig_min
    coin = COIN_BASE
    for _ in range(n_rounds):
        scr_fg[:] = 0.0
        retry = 0
        trig = False
        fg_played = False
        fres = (0.0, 0, 0, 0, 0, 1.0, 0)
        ok, fp, raw, nc, sc, ft, mlv, nfr, t = False, 0.0, 0.0, 0, 0, 0.0, 0, 0, 0
        pay_bg = 0.0
        pay_fg = 0.0
        if mode_kind == 0:
            card = _pick_card(C, 0) if card_on else -1
            if card >= 0 and C.card_type[0, card] == CARD_FREE:
                # free_game 卡：重抽到觸發 FG 且 BG 倍數 ≤ BG Trigger Cap；Scatter 不夠的停輪盤面略過連消（最後一次照常跑完）
                reroll = 0
                while True:
                    scr_bg[:] = 0.0
                    frames0[:, :] = 0
                    minsc = 0 if reroll + 1 >= limit else tmin
                    ok, fp, raw, nc, sc, ft, mlv, nfr, t = _run_spin(C, 0, -1, frames0, False, 0, minsc, scr_bg, False)
                    if not ok:
                        reroll += 1
                        continue
                    if sc < tmin or (C.bg_cap >= 0.0 and fp / coin > C.bg_cap):
                        reroll += 1
                        if reroll >= limit:
                            S[S_EXC] += 1.0
                            S[S_EXC_BGF] += 1.0
                            break
                        continue
                    break
                retry += reroll
                if sc >= tmin:
                    trig = True
                    awarded = C.trig_base + (sc - tmin) * C.trig_extra
                    fcard = _pick_card(C, 1)
                    fr = 0
                    while True:   # FG 卡：重跑整包 FG（BG 盤面與得分不變）到落在區間
                        scr_fg[:] = 0.0
                        fres = _run_fg(C, awarded, scr_fg)
                        if _range_match(C, 1, fcard, fres[0] / coin):
                            break
                        fr += 1
                        if fr >= limit:
                            S[S_EXC] += 1.0
                            S[S_EXC_FG] += 1.0
                            break
                    retry += fr
                    fg_played = True
            else:
                # range 卡（或 Card Off）：重抽到「未觸發 FG 且 min < BG 倍數 <= max」
                reroll = 0
                exc_range = False
                while True:
                    scr_bg[:] = 0.0
                    frames0[:, :] = 0
                    ok, fp, raw, nc, sc, ft, mlv, nfr, t = _run_spin(C, 0, -1, frames0, False, 0, 0, scr_bg, False)
                    if card >= 0:
                        x = fp / coin
                        if sc >= tmin or not (x > C.card_min[0, card] and x <= C.card_max[0, card]):
                            reroll += 1
                            if reroll >= limit:
                                exc_range = True
                                S[S_EXC] += 1.0
                                S[S_EXC_BGR] += 1.0
                            else:
                                continue
                    break
                retry += reroll
                if sc >= tmin:
                    trig = True
                    if not exc_range:   # JS：BG range 卡 Retry 上限被迫接受的觸發盤不進 FG
                        awarded = C.trig_base + (sc - tmin) * C.trig_extra
                        fres = _run_fg(C, awarded, scr_fg)
                        fg_played = True
            pay_bg = fp
            if fg_played:
                pay_fg = fres[0]
        else:
            # BF：進場盤（表 6）重抽到 3+ Scatter，跑整包 FG；卡片判定用「進場盤＋FG」總得分 ÷ NB 底注
            card = _pick_card(C, 2) if card_on else -1
            rr = 0
            while True:
                while True:
                    scr_bg[:] = 0.0
                    frames0[:, :] = 0
                    ok, fp, raw, nc, sc, ft, mlv, nfr, t = _run_spin(C, 2, -1, frames0, False, 2, tmin, scr_bg, True)
                    if ok and sc >= tmin:
                        break
                awarded = C.trig_base + (sc - tmin) * C.trig_extra
                scr_fg[:] = 0.0
                fres = _run_fg(C, awarded, scr_fg)
                if not _range_match(C, 2, card, (fp + fres[0]) / coin):
                    rr += 1
                    if rr >= limit:
                        S[S_EXC] += 1.0
                        S[S_EXC_FG] += 1.0
                    else:
                        continue
                break
            retry += rr
            trig = True
            fg_played = True
            pay_bg = 0.0
            pay_fg = fp + fres[0]   # 規範 §1.1.6：BF 得分全部計入 pay_fg

        # ---- 累加（只有被接受的結果）----
        bg_x = pay_bg / coin
        fg_x = pay_fg / coin
        S[S_ROUNDS] += 1.0
        S[S_COIN] += cost
        S[S_PAY_BG] += bg_x
        S[S_PAY_FG] += fg_x
        wx = (bg_x + fg_x) / cost
        S[S_WX] += wx
        S[S_WX2] += wx * wx
        if wx > S[S_MAXWX]:
            S[S_MAXWX] = wx
        if bg_x > S[S_MAX_BG_X]:
            S[S_MAX_BG_X] = bg_x
        if raw > 0.0:
            S[S_BG_HIT] += 1.0
            if 1.0 + ft > S[S_MAXMULT]:
                S[S_MAXMULT] = 1.0 + ft
        S[S_CASC_BG] += nc
        special = 1 if sc > 0 else 0
        S[S_RETRY] += retry
        # 本局 base 轉（BG 或 BF 進場盤）結束時的框
        scr_bg[SCR_MAXLV + mlv] += 1.0
        for r in range(R):
            for c in range(NR):
                if frames0[r, c] > 0:
                    scr_bg[SCR_ENDFR + frames0[r, c]] += 1.0
        for i in range(SCR_SIZE):
            G[0, i] += scr_bg[i]
        if trig:
            S[S_TRIG] += 1.0
        if fg_played:
            S[S_FG_PLAYED] += 1.0
            S[S_FG_SPINS] += fres[1]
            S[S_FG_HIT] += fres[2]
            S[S_RETRIG] += fres[3]
            special += fres[4]
            if fres[5] > S[S_MAXMULT]:
                S[S_MAXMULT] = fres[5]
            S[S_CASC_FG] += scr_fg[SCR_CASC]
            fy = fg_x / cost
            S[S_FGY] += fy
            S[S_FGY2] += fy * fy
            S[S_FGN] += 1.0
            if fg_x > S[S_MAX_FG_X]:
                S[S_MAX_FG_X] = fg_x
            for i in range(SCR_SIZE):
                G[1, i] += scr_fg[i]
        S[S_SPECIAL] += special
        # Multiplier Line 分桶（X 以 NB 底注為分母）
        if mode_kind == 1:
            bi = _bucket(C, fg_x)
            B[bi, B_BF_CNT] += 1.0
            B[bi, B_BF_PAY] += fg_x
            B[bi, B_FG_HIT] += fres[2]
            B[bi, B_FG_SPINS] += fres[1]
            for k in range(6):
                B[bi, B_FG_COMBO + min(max(k, 1), 5) - 1] += scr_fg[SCR_COMBO + k]
            B[bi, B_FG_END_FRAMES] += fres[6]
        elif trig:
            ti = _bucket(C, bg_x)
            B[ti, B_TRIG_CNT] += 1.0
            B[ti, B_TRIG_PAY] += bg_x
            fi = _bucket(C, fg_x)
            B[fi, B_FG_CNT] += 1.0
            B[fi, B_FG_PAY] += fg_x
            B[fi, B_FG_HIT] += fres[2]
            B[fi, B_FG_SPINS] += fres[1]
            for k in range(6):
                B[fi, B_FG_COMBO + min(max(k, 1), 5) - 1] += scr_fg[SCR_COMBO + k]
            B[fi, B_FG_END_FRAMES] += fres[6]
        else:
            bi = _bucket(C, bg_x)
            B[bi, B_BG_CNT] += 1.0
            B[bi, B_BG_PAY] += bg_x
            B[bi, B_BG_COMBO + min(max(nc, 1), 5) - 1] += 1.0
            B[bi, B_BG_FRAMES] += nfr


# ===== 平行執行 =====

def _new_stats() -> dict[str, np.ndarray]:
    return {"S": np.zeros(NS), "B": np.zeros((len(MULTIPLIER_THRESHOLDS), NBCOL)), "G": np.zeros((2, SCR_SIZE))}


def _merge_stats(target: dict[str, np.ndarray], source: dict[str, np.ndarray]) -> None:
    for i in range(NS):
        if i in S_MAX_KEYS:
            target["S"][i] = max(target["S"][i], source["S"][i])
        else:
            target["S"][i] += source["S"][i]
    target["B"] += source["B"]
    target["G"] += source["G"]


def _run_chunk_local(n: int, mode_kind: int, card_on: bool, cost: float, seed: int) -> dict[str, np.ndarray]:
    stats = _new_stats()
    _simulate_chunk(CORE, n, mode_kind, card_on, cost, seed, stats["S"], stats["B"], stats["G"])
    return stats


def _init_worker(box: dict[str, Any], profile: str, bet_mode: int, mode_kind: int, card_on: bool, cost: float) -> None:
    """Worker 初始化：spawn 啟動不會繼承全域變數，要把主程序的 Box 傳進來；建核心並先跑 Warm-up（Numba 編譯不計時）。"""
    global CFG, CORE
    CFG = box
    CORE = build_core(box, profile, bet_mode)
    _run_chunk_local(20, mode_kind, card_on, cost, RNG_SEED - 1)   # Warm-up：統計丟棄


def _worker_ready() -> int:
    time.sleep(0.05)   # 讓已就緒的 Worker 不會一口氣吃掉所有確認工作
    return os.getpid()


def _worker_chunk(n: int, mode_kind: int, card_on: bool, cost: float, seed: int) -> dict[str, np.ndarray]:
    return _run_chunk_local(n, mode_kind, card_on, cost, seed)


def run_simulation(total_rounds: int, bet_mode: int, base_bet: float, threads: int,
                   card_enabled: bool, newbie: bool) -> dict[str, Any]:
    """場次平均分給各 Worker（餘數給前幾個），Worker 種子 RNG_SEED + i × 7919；Warm-up 完成後才計時。"""
    profile = "newbie" if newbie else "oldhand"
    mode_kind = 1 if bet_mode in BUY_MODES else 0
    cost = cost_multiplier(bet_mode)
    threads = max(1, min(threads, total_rounds))
    per = [total_rounds // threads] * threads
    for i in range(total_rounds % threads):
        per[i] += 1
    assert sum(per) == total_rounds
    merged = _new_stats()
    if threads == 1:
        _init_worker(CFG, profile, bet_mode, mode_kind, card_enabled, cost)   # 編譯＋Warm-up（不計時）
        started = time.perf_counter()
        _merge_stats(merged, _run_chunk_local(total_rounds, mode_kind, card_enabled, cost, RNG_SEED))
        return {"stats": merged, "duration": time.perf_counter() - started}
    with ProcessPoolExecutor(max_workers=threads, mp_context=mp.get_context("spawn"), initializer=_init_worker,
                             initargs=(CFG, profile, bet_mode, mode_kind, card_enabled, cost)) as pool:
        # 等所有 Worker 編譯＋Warm-up 完（initializer 跑完才會接工作；收齊 threads 個不同 pid 才算全部就緒）
        ready: set[int] = set()
        while len(ready) < threads:
            ready.update(f.result() for f in [pool.submit(_worker_ready) for _ in range(threads)])
        started = time.perf_counter()
        futures = [pool.submit(_worker_chunk, n, mode_kind, card_enabled, cost, RNG_SEED + i * 7919)
                   for i, n in enumerate(per) if n > 0]
        for f in futures:
            _merge_stats(merged, f.result())
        duration = time.perf_counter() - started
    return {"stats": merged, "duration": duration}


# ===== 報表 / Console =====

def mode_name(mode: int) -> str:
    return {MODE_NORMALBET: "Normal Bet", MODE_EXTRABET: "Extra Bet", MODE_FEATUREBUY: "Buy Feature"}[mode]


def frame_keys() -> list[str]:
    return list(CFG["frame_multiplier"].get("levels") or ["plain", "straw", "wood", "brick"])


def calculated_metrics(result: dict[str, Any]) -> dict[str, Any]:
    S = result["stats"]["S"]
    rounds = max(1.0, S[S_ROUNDS])
    coin = max(1e-12, S[S_COIN])
    mean = S[S_WX] / rounds
    var = max(0.0, S[S_WX2] / rounds - mean * mean)
    fgn = S[S_FGN]
    fg_mean = S[S_FGY] / fgn if fgn else 0.0
    fg_var = max(0.0, S[S_FGY2] / fgn - fg_mean * fg_mean) if fgn else 0.0
    trig = S[S_TRIG]
    fg_spins = S[S_FG_SPINS]
    return {
        "rounds": int(S[S_ROUNDS]),
        "coin_in_per_round": S[S_COIN] / rounds * result["base_bet"],
        "rtp_total": (S[S_PAY_BG] + S[S_PAY_FG]) / coin,
        "rtp_link": 0.0,                         # 本作沒有彩金
        "rtp_bonus": 0.0,
        "rtp_game": (S[S_PAY_BG] + S[S_PAY_FG]) / coin,
        "rtp_bg": S[S_PAY_BG] / coin,
        "rtp_fg": S[S_PAY_FG] / coin,
        "hit_rate_bg": S[S_BG_HIT] / rounds,
        "hit_rate_fg": S[S_FG_HIT] / max(1.0, fg_spins),
        "fg_trigger_rate": trig / rounds,
        "fg_trigger_cycle": rounds / trig if trig else math.inf,
        "retrigger_trigger_rate": S[S_RETRIG] / max(1.0, fg_spins),
        "retrigger_trigger_cycle": fg_spins / S[S_RETRIG] if S[S_RETRIG] else math.inf,
        "avg_fg_spins": fg_spins / trig if trig else 0.0,
        "special_symbol_cnt": int(S[S_SPECIAL]),
        "SCR": S[S_SPECIAL] / rounds * 10_000_000_000,
        "max_win_x": S[S_MAXWX],
        "capped_rounds": 0,                      # 本作 Max Win 未定（game_rule ⏳），不截斷
        "volatility_std": math.sqrt(var),
        "volatility_std_fg": math.sqrt(fg_var),
        "standard_error": math.sqrt(var) / math.sqrt(rounds),
    }


def _trigger_within_cap(result: dict[str, Any], cap: float | None) -> tuple[int, float]:
    """BG 觸發 FG 那把 ≤ cap 的次數與得分（取 Multiplier Line 同一上限那列的累計；找不到完全相同上限即停止）。"""
    B = result["stats"]["B"]
    if cap is None:
        return int(B[:, B_TRIG_CNT].sum()), float(B[:, B_TRIG_PAY].sum()) * result["base_bet"]
    if cap not in MULTIPLIER_THRESHOLDS:
        raise ValueError(f"BG Trigger Cap {cap:g} 不在倍率區間上限中，請補齊倍率區間")
    upto = MULTIPLIER_THRESHOLDS.index(cap) + 1
    return int(B[:upto, B_TRIG_CNT].sum()), float(B[:upto, B_TRIG_PAY].sum()) * result["base_bet"]


def common_summary_sections(result: dict[str, Any]) -> list[list[tuple[str, Any]]]:
    m = calculated_metrics(result)
    S = result["stats"]["S"]
    mode = result["bet_mode"]
    if result["card_system_enabled"]:
        cnt, pay = _trigger_within_cap(result, bg_trigger_cap(CFG, result["card_system_profile"], mode))
        trigger_rows = [("bg_trigger_fg_cnt", cnt), ("bg_trigger_fg_pay", pay)]
    elif mode in BUY_MODES:
        trigger_rows = [("bg_trigger_fg_cnt", 0), ("bg_trigger_fg_pay", 0.0)]
    else:
        old_cnt, old_pay = _trigger_within_cap(result, bg_trigger_cap(CFG, "oldhand", mode))
        new_cnt, new_pay = _trigger_within_cap(result, bg_trigger_cap(CFG, "newbie", mode))
        trigger_rows = [("bg_trigger_fg_cnt", old_cnt), ("bg_trigger_fg_pay", old_pay),
                        ("bg_trigger_fg_cnt_newbie", new_cnt), ("bg_trigger_fg_pay_newbie", new_pay)]
    sections: list[list[tuple[str, Any]]] = [
        [("game_name", result["game_name"]), ("game_id", result["game_id"])],
        [("config_file", result["config_file"]), ("tier", result["tier"]),
         ("math_version", result["math_version"]),
         ("card_system", "on" if result["card_system_enabled"] else "off")],
        [("bet_mode", mode_name(mode)), ("bet_multi", result["bet_multi"]),
         ("feature_price_multiplier", result["feature_price_multiplier"]),
         ("base_bet", result["base_bet"]), ("bet_amount", result["bet_amount"]),
         ("bet_tier_amount", result["bet_tier_amount"]), ("bet_tier", result["bet_tier"]),
         ("jackpot", result["jackpot"]), ("coin_in", m["coin_in_per_round"]),
         ("total_rounds", m["rounds"]), ("duration", result["duration"])],
        [("rtp_total", m["rtp_total"]), ("rtp_link", m["rtp_link"]), ("rtp_bonus", m["rtp_bonus"]),
         ("rtp_game", m["rtp_game"]), ("rtp_bg", m["rtp_bg"]), ("rtp_fg", m["rtp_fg"]),
         ("hit_rate_bg", m["hit_rate_bg"]), ("hit_rate_fg", m["hit_rate_fg"]),
         ("fg_trigger_rate", (m["fg_trigger_rate"], m["fg_trigger_cycle"])),
         ("retrigger_trigger_rate", (m["retrigger_trigger_rate"], m["retrigger_trigger_cycle"])),
         ("avg_fg_spins", m["avg_fg_spins"])],
        [*trigger_rows, ("special_symbol_cnt", m["special_symbol_cnt"]), ("SCR", m["SCR"])],
        [("max_win_x", m["max_win_x"]), ("capped_rounds", m["capped_rounds"]),
         ("volatility_std", m["volatility_std"]), ("volatility_std_fg", m["volatility_std_fg"]),
         ("standard_error", m["standard_error"])],
    ]
    if result["card_system_enabled"]:
        sections.extend([
            [("card_system_profile", result["card_system_profile"]),
             ("card_retry_limit", CARD_RETRY_LIMIT),
             ("retry_total", S[S_RETRY]),
             ("avg_retry", S[S_RETRY] / max(1.0, S[S_ROUNDS]))],
            [("retry_limit_exceeded", S[S_EXC]), ("retry_limit_bg_range", S[S_EXC_BGR]),
             ("retry_limit_bg_freegame", S[S_EXC_BGF]), ("retry_limit_fg", S[S_EXC_FG])],
        ])
    return sections


def game_info_rows(result: dict[str, Any]) -> list[tuple[str, Any]]:
    """By Game Info：欄位清單與順序只在這裡定義，Console 與 Overview 共用。"""
    S, G = result["stats"]["S"], result["stats"]["G"]
    rounds = max(1.0, S[S_ROUNDS])
    fg_spins = max(1.0, S[S_FG_SPINS])
    fg_played = max(1.0, S[S_FG_PLAYED])
    keys = frame_keys()
    nlv = len(keys)
    bg, fg = G[0], G[1]
    rows: list[tuple[str, Any]] = [
        ("avg_cascades_bg", S[S_CASC_BG] / rounds),
        ("avg_cascades_fg", S[S_CASC_FG] / fg_spins),
    ]
    for k in range(6):
        rows.append((f"bg_combo_{'5+' if k == 5 else k}_share", bg[SCR_COMBO + k] / rounds))
    for k in range(6):
        rows.append((f"fg_combo_{'5+' if k == 5 else k}_share", fg[SCR_COMBO + k] / fg_spins))
    # BG（BF 為進場盤）結束時有某階以上框的局：比率與週期
    for lv in range(1, nlv + 1):
        n = bg[SCR_MAXLV + lv: SCR_MAXLV + nlv + 1].sum()
        suffix = "" if lv == nlv else "_plus"
        rows.append((f"bg_{keys[lv - 1]}{suffix}_rate", n / rounds))
        rows.append((f"bg_{keys[lv - 1]}{suffix}_cycle", rounds / n if n else math.inf))
    rows.append(("avg_frames_bg", bg[SCR_ENDFR: SCR_ENDFR + nlv + 1].sum() / rounds))
    for lv in range(1, nlv + 1):
        cnt = bg[SCR_FRM + lv * 2]
        rows.append((f"avg_frame_value_{keys[lv - 1]}_bg", bg[SCR_FRM + lv * 2 + 1] / cnt if cnt else 0.0))
    rows.append(("fg_avg_win_x", S[S_PAY_FG] / max(1.0, S[S_TRIG])))   # 每場 FG 平均倍數（÷ NB 底注；BF 含進場盤）
    rows.append(("max_fg_win_x", S[S_MAX_FG_X]))
    for lv in range(1, nlv + 1):
        n = fg[SCR_MAXLV + lv: SCR_MAXLV + nlv + 1].sum()
        suffix = "" if lv == nlv else "_plus"
        rows.append((f"fg_end_{keys[lv - 1]}{suffix}_rate", n / fg_played))
    rows.append(("avg_end_frames_fg", fg[SCR_ENDFR: SCR_ENDFR + nlv + 1].sum() / fg_played))
    for lv in range(1, nlv + 1):
        cnt = fg[SCR_FRM + lv * 2]
        rows.append((f"avg_frame_value_{keys[lv - 1]}_fg", fg[SCR_FRM + lv * 2 + 1] / cnt if cnt else 0.0))
    rows.append(("fg_mansion_rate", fg[SCR_MANSION] / fg_played))
    rows.append(("fg_good_spin_share", fg[SCR_GOOD] / fg_spins))
    rows.append(("fg_frame_boost_share", fg[SCR_BOOST_CNT] / fg_spins))
    names = CFG.get("strip_name_map") or []
    for t in range(TAB_MAX):
        spins = fg[SCR_TAB + t * 2]
        if spins:
            name = names[t] if t < len(names) else str(t)
            rows.append((f"fg_table_{t}_{name}_share", spins / fg_spins))
            rows.append((f"fg_table_{t}_{name}_hit_rate", fg[SCR_TAB + t * 2 + 1] / spins))
    rows.append(("max_final_multiplier", S[S_MAXMULT]))
    return rows


COUNT_KEYS = {
    "total_rounds", "bg_trigger_fg_cnt", "bg_trigger_fg_cnt_newbie", "special_symbol_cnt", "SCR", "retry_total",
    "retry_limit_exceeded", "retry_limit_bg_range", "retry_limit_bg_freegame", "retry_limit_fg", "capped_rounds",
    "max_final_multiplier",
}


def _display_value(key: str, value: Any) -> str:
    if key == "duration":
        return f"{float(value):05.2f} sec"
    if key in COUNT_KEYS:
        return f"{int(round(float(value))):,}"
    if key == "card_retry_limit":
        return str(int(value))
    if key in {"bg_trigger_fg_pay", "bg_trigger_fg_pay_newbie"}:
        return f"{float(value):,.0f}"
    if key in {"coin_in", "base_bet", "bet_amount", "bet_tier_amount"}:
        return f"{float(value):.2f}"
    if key in {"fg_trigger_rate", "retrigger_trigger_rate"}:
        rate, cycle = value
        unit = "spins" if key == "fg_trigger_rate" else "free spins"
        cycle_text = "N/A" if not math.isfinite(float(cycle)) else f"{float(cycle):.2f} {unit}"
        return f"{float(rate):.4%} (cycle {cycle_text})"
    if key.endswith("_cycle"):
        return "N/A" if not math.isfinite(float(value)) else f"{float(value):,.2f} spins"
    if key.startswith("rtp_") or key in {"hit_rate_bg", "hit_rate_fg"} or key.endswith("_share"):
        return f"{float(value):.4%}"
    if key.endswith("_rate"):
        return f"{float(value):.6%}"
    if key == "avg_fg_spins":
        return f"{float(value):.2f} spins"
    if key in {"max_win_x", "max_fg_win_x"}:
        return f"{float(value):,.2f} x"
    if key in {"avg_retry", "volatility_std", "volatility_std_fg", "standard_error"} \
            or key.endswith("_win_x") or key.startswith("avg_"):
        return f"{float(value):05.2f}"
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.6f}"
    return str(value)


def overview_rows(result: dict[str, Any]) -> list[tuple[str, str]]:
    flat = [row for section in common_summary_sections(result) for row in section]
    return [(key, _display_value(key, value)) for key, value in flat + game_info_rows(result)]


def print_console(result: dict[str, Any]) -> None:
    for section in common_summary_sections(result):
        for key, value in section:
            print(f"{key:<28}{_display_value(key, value)}")
        print()
    print("<< By Game Info >>")
    for key, value in game_info_rows(result):
        print(f"{key:<28}{_display_value(key, value)}")
    print()


def multiplier_line_frame(result: dict[str, Any]) -> pd.DataFrame:
    B = result["stats"]["B"]
    money = result["base_bet"]
    has_bf = result["bet_mode"] in BUY_MODES
    rows = []
    trig_cnt = 0
    trig_pay = 0.0
    for i, upper in enumerate(MULTIPLIER_THRESHOLDS):
        interval = "0" if i == 0 else f"{float(MULTIPLIER_THRESHOLDS[i - 1]):.1f} < X <= {float(upper):.1f}"
        trig_cnt += int(B[i, B_TRIG_CNT])
        trig_pay += float(B[i, B_TRIG_PAY]) * money
        row: dict[str, Any] = {
            "Interval": interval,
            "base_game_cnt": int(B[i, B_BG_CNT]), "base_game_pay": float(B[i, B_BG_PAY]) * money,
            "free_game_cnt": int(B[i, B_FG_CNT]), "free_game_pay": float(B[i, B_FG_PAY]) * money,
        }
        if has_bf:
            row["free_game_cnt_BF"] = int(B[i, B_BF_CNT])
            row["free_game_pay_BF"] = float(B[i, B_BF_PAY]) * money
        row["Interval_Upper"] = upper
        row["bg_trigger_fg_cnt_lte_upper"] = trig_cnt
        row["bg_trigger_fg_pay_lte_upper"] = trig_pay
        spins = B[i, B_FG_SPINS]
        row["FG_Hit_Rate"] = B[i, B_FG_HIT] / spins if spins else 0.0
        row["FG_Spin_Count"] = int(spins)
        bg_total = max(1.0, B[i, B_BG_COMBO:B_BG_COMBO + 5].sum())
        for k in range(5):
            row[f"BG_Combo_{k + 1}{'+' if k == 4 else ''}_Rate"] = B[i, B_BG_COMBO + k] / bg_total
        fg_total = max(1.0, B[i, B_FG_COMBO:B_FG_COMBO + 5].sum())
        for k in range(5):
            row[f"FG_Combo_{k + 1}{'+' if k == 4 else ''}_Rate"] = B[i, B_FG_COMBO + k] / fg_total
        # By Game：BG 局結束時框格數平均、FG 結束時框格數平均
        row["BG_Avg_Frames"] = B[i, B_BG_FRAMES] / B[i, B_BG_CNT] if B[i, B_BG_CNT] else 0.0
        fg_cnt = B[i, B_BF_CNT] if has_bf else B[i, B_FG_CNT]
        row["FG_Avg_End_Frames"] = B[i, B_FG_END_FRAMES] / fg_cnt if fg_cnt else 0.0
        rows.append(row)
    return pd.DataFrame(rows)


def feature_frame(result: dict[str, Any]) -> pd.DataFrame:
    S, G = result["stats"]["S"], result["stats"]["G"]
    keys = frame_keys()
    rows: list[tuple[str, Any]] = [
        ("gold_converted_bg", G[0, SCR_GOLDCONV]), ("gold_converted_fg", G[1, SCR_GOLDCONV]),
        ("frame_boost_by_count_fg", G[1, SCR_BOOST_CNT]), ("frame_boost_initial_fg", G[1, SCR_BOOST_INIT]),
        ("frame_boost_drop_fg", G[1, SCR_BOOST_DROP]),
        ("mansion_fg", G[1, SCR_MANSION]), ("good_spins_fg", G[1, SCR_GOOD]),
        ("fg_played", S[S_FG_PLAYED]), ("fg_spins", S[S_FG_SPINS]),
        ("max_win_x", S[S_MAXWX]), ("max_bg_win_x", S[S_MAX_BG_X]), ("max_fg_win_x", S[S_MAX_FG_X]),
        ("max_final_multiplier", S[S_MAXMULT]),
    ]
    for scene, g in (("bg", G[0]), ("fg", G[1])):
        for lv in range(1, len(keys) + 1):
            cnt = g[SCR_FRM + lv * 2]
            rows.append((f"frame_reveal_{keys[lv - 1]}_{scene}", cnt))
            rows.append((f"frame_value_avg_{keys[lv - 1]}_{scene}", g[SCR_FRM + lv * 2 + 1] / cnt if cnt else 0.0))
        for lv in range(len(keys) + 1):
            label = "none" if lv == 0 else keys[lv - 1]
            rows.append((f"end_max_level_{label}_{scene}", g[SCR_MAXLV + lv]))
    names = CFG.get("strip_name_map") or []
    for scene, g in (("base", G[0]), ("fg", G[1])):
        for t in range(TAB_MAX):
            if g[SCR_TAB + t * 2]:
                name = names[t] if t < len(names) else str(t)
                rows.append((f"table_{t}_{name}_spins_{scene}", g[SCR_TAB + t * 2]))
                rows.append((f"table_{t}_{name}_hit_spins_{scene}", g[SCR_TAB + t * 2 + 1]))
    return pd.DataFrame(rows, columns=["Index", "Value"])


def _score_symbols() -> list[int]:
    return [int(s) for s in CFG["symbols_score"]]


def symbol_frame(result: dict[str, Any]) -> pd.DataFrame:
    G = result["stats"]["G"]
    money = result["base_bet"] / COIN_BASE
    names = CFG["symbol_str"]
    sym = G[0] + G[1]
    hits = {s: sum(sym[SCR_SYM + s * 6 + k * 2] for k in range(3)) for s in _score_symbols()}
    pays = {s: sum(sym[SCR_SYM + s * 6 + k * 2 + 1] for k in range(3)) * money for s in _score_symbols()}
    total_hits = max(1.0, sum(hits.values()))
    total_pay = max(1e-12, sum(pays.values()))
    rows = []
    for s in _score_symbols():
        rows.append({
            "symbol_id": s, "symbol": names[str(s)],
            "line_hits": int(hits[s]), "hit_share": hits[s] / total_hits,
            "pay": pays[s], "pay_share": pays[s] / total_pay,
            "hits_3": int(sym[SCR_SYM + s * 6]), "hits_4": int(sym[SCR_SYM + s * 6 + 2]),
            "hits_5": int(sym[SCR_SYM + s * 6 + 4]),
        })
    return pd.DataFrame(rows)


def eliminate_frame(result: dict[str, Any]) -> pd.DataFrame:
    """連消次數分布：BG 以局計（BF 為進場盤）、FG 以 Free Spin 計。"""
    G = result["stats"]["G"]
    rows = [("5+" if k == 5 else str(k), int(G[0, SCR_COMBO + k]), int(G[1, SCR_COMBO + k])) for k in range(6)]
    return pd.DataFrame(rows, columns=["combo", "BG", "FG"])


def symbol_length_frame(result: dict[str, Any]) -> pd.DataFrame:
    """線得分（未乘框倍數）的符號 × 連線長度命中數與派彩。"""
    G = result["stats"]["G"]
    money = result["base_bet"] / COIN_BASE
    names = CFG["symbol_str"]
    rows = []
    for scene, g in (("BG", G[0]), ("FG", G[1])):
        for s in _score_symbols():
            for k, length in enumerate((3, 4, 5)):
                rows.append((scene, names[str(s)], length, int(g[SCR_SYM + s * 6 + k * 2]),
                             g[SCR_SYM + s * 6 + k * 2 + 1] * money))
    return pd.DataFrame(rows, columns=["scene", "symbol", "length", "hits", "pay"])


# ===== 報表檔名 =====

def format_rounds_tag(total_rounds: int) -> str:
    exponent = round(math.log10(total_rounds)) if total_rounds > 0 else 0
    return f"10{exponent}" if 10 ** exponent == total_rounds else str(total_rounds)


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
    """Card Off：H0991_<基礎版本 2 碼>_…；Card On：H0991<RTP><Variant>_<四段版本>_…_card。
    config 的 game_id 沿用彩罐熱舞（H026192A），檔名改用本作 MATH_ID；base 沒有 excel_version 時取層級版本第 1 碼。"""
    stamp = (timestamp or datetime.now()).strftime("%y%m%d%H%M")
    rounds_tag = format_rounds_tag(result["stats_rounds"])
    bet_mode = result["bet_mode"]
    version = str(CFG["excel_version"])
    if not result["card_system_enabled"]:
        base_version = str(CFG_SET["base"].get("excel_version") or version.split(".")[0])
        return f"{MATH_ID}1_{format_base_version_tag(base_version)}_{stamp}_betmode{bet_mode}_{rounds_tag}.xlsx"
    tier_code = result["tier"].split("_")[0]   # 例 92A（_Bet100 不進 ID）
    parts = [f"{MATH_ID}1{tier_code}", format_rtp_version_tag(version), stamp, f"betmode{bet_mode}", rounds_tag,
             format_rtp_tag(calculated_metrics(result)["rtp_total"]), result["card_system_profile"]]
    if result["card_system_profile"] == "oldhand":
        parts.append(result["bet_tier"])
    parts.append("card")
    return "_".join(parts) + ".xlsx"


def output_report(result: dict[str, Any], output_dir: Path | None = None) -> Path:
    directory = output_dir or (BASE_DIR / "Record")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / report_filename(result)
    overview = pd.DataFrame(overview_rows(result), columns=["Index", "Value"])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        overview.to_excel(writer, sheet_name="Overview", index=False)
        multiplier_line_frame(result).to_excel(writer, sheet_name="Multiplier Line", index=False)
        feature_frame(result).to_excel(writer, sheet_name="Feature", index=False)
        symbol_frame(result).to_excel(writer, sheet_name="Symbol", index=False)
        eliminate_frame(result).to_excel(writer, sheet_name="Eliminate", index=False)
        symbol_length_frame(result).to_excel(writer, sheet_name="Symbol Length", index=False)
    return path


# ===== Runner =====

def build_result(bundle: dict[str, Any], combo: dict[str, Any]) -> dict[str, Any]:
    bet_mode = int(combo["bet_mode"])
    base_bet = float(combo["base_bet"])
    bet_amount = wager_for_mode(bet_mode, base_bet)
    if bet_mode in BUY_MODES:
        price = cost_multiplier(bet_mode)
        bet_tier_amount = bet_amount / price
        feature_price: Any = int(price) if float(price).is_integer() else price
    else:
        bet_tier_amount = bet_amount
        feature_price = "n/a"
    multi = bet_amount / base_bet
    return {
        "stats": bundle["stats"],
        "stats_rounds": int(bundle["stats"]["S"][S_ROUNDS]),
        "duration": bundle["duration"],
        "game_name": CFG.get("game_name_zh") or GAME_NAME_FALLBACK,
        "game_id": CFG.get("online_game_id") or "N/A（發想，未指定）",
        "config_file": combo["config_file"],
        "tier": combo["tier"],
        "math_version": CFG.get("excel_version"),
        "card_system_enabled": bool(combo["card_system_enabled"]),
        "card_system_profile": "newbie" if combo["card_system_is_newbie"] else "oldhand",
        "bet_mode": bet_mode,
        "bet_multi": int(multi) if float(multi).is_integer() else multi,
        "feature_price_multiplier": feature_price,
        "base_bet": base_bet,
        "bet_amount": bet_amount,
        "bet_tier_amount": bet_tier_amount,
        "bet_tier": bet_tier_name(bet_tier_amount, base_bet),
        "jackpot": "on" if (JACKPOT_ENABLED and (CFG.get("jackpot") or {}).get("enabled")) else "off",
    }


def run_single_spin_debug(combo: dict[str, Any]) -> None:
    """單執行緒逐局除錯：印每局 BG／FG 得分（倍數＝÷ NB 底注）。"""
    mode = int(combo["bet_mode"])
    card = bool(combo["card_system_enabled"])
    profile = "newbie" if combo["card_system_is_newbie"] else "oldhand"
    mode_kind = 1 if mode in BUY_MODES else 0
    cost = cost_multiplier(mode)
    _init_worker(CFG, profile, mode, mode_kind, card, cost)
    for i in range(DEBUG_ROUNDS):
        S = _run_chunk_local(1, mode_kind, card, cost, RNG_SEED + i)["S"]
        print(f"--- debug round {i + 1}（seed {RNG_SEED + i}）--- bg_x={S[S_PAY_BG]:.2f} fg_x={S[S_PAY_FG]:.2f} "
              f"bg_cascades={int(S[S_CASC_BG])} fg_triggered={int(S[S_TRIG])} fg_spins={int(S[S_FG_SPINS])} "
              f"retry={int(S[S_RETRY])} max_mult={S[S_MAXMULT]:g}")


def run_batch(combo: dict[str, Any], index: int, total: int) -> None:
    validate_batch_run(combo)
    load_batch_configs(combo)
    print(f"=== Batch {index}/{total}: {combo} ===")
    print()
    if not HAS_NUMBA:
        print("[warn] 未使用 Numba（純 Python），速度很慢，只適合除錯。")
    bundle = run_simulation(int(combo["total_rounds"]), int(combo["bet_mode"]), float(combo["base_bet"]),
                            THREADS, bool(combo["card_system_enabled"]), bool(combo["card_system_is_newbie"]))
    result = build_result(bundle, combo)
    if SHOW_CONSOLE_SUMMARY:
        print_console(result)
    if OUTPUT_REPORT:
        print(f"report -> {output_report(result)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"{MATH_ID} 三隻小豬 simulator")
    parser.add_argument("--rounds", type=int, default=None)
    parser.add_argument("--bet-mode", type=int, default=None)
    parser.add_argument("--base-bet", type=float, default=None)
    parser.add_argument("--threads", type=int, default=None)
    parser.add_argument("--no-report", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--card-on", action="store_true", help="Card System On")
    parser.add_argument("--card-off", action="store_true", help="Card System Off")
    parser.add_argument("--newbie", action="store_true", help="Profile 改為 Newbie")
    parser.add_argument("--tier", default=None, help="覆寫層級（本作只有 92A）")
    parser.add_argument("--config", default=None, help="覆寫 config_file（調參試驗用）")
    parser.add_argument("--seed", type=int, default=None, help="覆寫 RNG_SEED（複驗用不同種子）")
    parser.add_argument("--series", choices=["A"], default=None, help="AUTO 選組使用的系列（本作只有 A）")
    parser.add_argument("--only", type=int, default=None, help="只跑 BATCH_RUNS 第 N 筆（1 起算）")
    return parser.parse_args()


def main() -> None:
    global RNG_SEED, THREADS, OUTPUT_REPORT
    args = parse_args()
    if args.seed is not None:
        RNG_SEED = args.seed
    if args.threads:
        THREADS = max(1, args.threads)
    if args.no_report:
        OUTPUT_REPORT = False
    runs = [dict(run) for run in BATCH_RUNS] if RUN_ALL_COMBINATIONS else [{
        "config_file": CONFIG_FILE, "tier": CONFIG_TIER, "bet_mode": BET_MODE, "total_rounds": TOTAL_ROUNDS,
        "card_system_enabled": CARD_SYSTEM_ENABLED, "card_system_is_newbie": CARD_SYSTEM_IS_NEWBIE,
        "base_bet": BASE_BET_SETTING,
    }]
    if args.only:
        runs = [runs[args.only - 1]]
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
        if args.newbie:
            run["card_system_is_newbie"] = True
        if args.series:
            run["config_file"] = f"config_99{args.series}.js"
        if args.tier:
            run["tier"] = args.tier
        if args.config:
            run["config_file"] = args.config
    if args.debug or RUN_SINGLE_SPIN_DEBUG:
        validate_batch_run(runs[0])
        load_batch_configs(runs[0])
        run_single_spin_debug(runs[0])
        return
    for index, run in enumerate(runs, start=1):
        run_batch(run, index, len(runs))


if __name__ == "__main__":
    main()
