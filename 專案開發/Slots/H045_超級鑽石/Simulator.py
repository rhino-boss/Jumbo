"""H045 超級鑽石 (Lucky Diamond) simulator（Numba 版）.

盤面 5x4、1024 Ways、Cascade；金框中獎翻牌為小鬼／大鬼兩種，每顆翻出的 Wild
再抽倍數（x1＝無倍數），大鬼丟出的 W2 沿用本體倍數；同一連線的 WILD 倍數相加後
再乘 Cascade Multiplier（5 階）。玩法定義見 ``game_rule.md``；執行參數一律來自 Config，不在本程式
內重複維護輪帶、權重、Paytable 或 Feature 參數。

Runner、BATCH_RUNS、Console 欄位與 Excel 報表版面依 ``專案需知/開發需知/模擬程式規範.md``。

2026-11-06：遊戲核心改寫為 Numba（@njit nogil，多執行緒），規則與 6.0.1.2 純 Python 版逐行對照移植；
Config 一律以陣列參數傳入核心（不烤進編譯快取），報表版面、檔名、Console 欄位不變。
RNG 改用 Numba 的 np.random（每執行緒獨立串流），與純 Python 版逐局不同、統計上一致。
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
import time
from collections import Counter, namedtuple
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

# Numba 編譯快取放系統暫存資料夾，不在專案資料夾留 __pycache__；Config 以參數傳入，快取不會吃到舊參數
os.environ["NUMBA_CACHE_DIR"] = str(Path(tempfile.gettempdir()) / "h045_numba")

import numpy as np
import pandas as pd
from numba import njit

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

# ===== User Settings =====

CONFIG_FILE = "config.js"
CONFIG_RTP_FILE = "AUTO"   # AUTO＝依押注檔位自動選（模擬程式規範 §1.2.3）；明寫檔名即 override
# 檔位對應表（2026-10-22）：老手 小 Bet < $2 → 94A、中 Bet $2～$100 → 92A、大 Bet > $100 → 92A_Bet100；
# 小 Bet：NB／EB 用實際押注判；大 Bet：一律用基礎押注判（對齊 SPS isHighBet()，2026-10-27）；BF 皆用基礎押注。Newbie 各版共用 → 固定 92A。最大押注 $5000。
RTP_SERIES = os.environ.get("H045_RTP_SERIES", "A")   # A／B 版（2026-10-27 加 B 版）；--series 可覆寫
TIER_CONFIG = {"small_bet": "config_94{s}.js", "medium_bet": "config_92{s}.js", "big_bet": "config_92{s}_Bet100.js"}
NEWBIE_CONFIG = "config_92{s}.js"
TOTAL_ROUNDS = 100_000
BASE_BET_SETTING = 1.0
BET_MODE = 0  # 0 = Normal Bet, 2 = Buy Feature
CARD_SYSTEM_ENABLED = False
CARD_SYSTEM_IS_NEWBIE = False

RUN_ALL_COMBINATIONS = True
BATCH_RUNS = [
    # --- 階段 7：小場次 Debug ---
    {"config_file": "config.js", "config_rtp_file": "AUTO", "bet_mode": 0,
     "total_rounds": 10**5, "card_system_enabled": False, "card_system_is_newbie": False, "base_bet": 1.0},
    # --- 階段 8：自然機率正式報表（卡片權重校準用）---
    # 2026-10-06 使用者決議：純 Python 無 Numba（1e6≈76 秒），本機改跑 NB 1e8／BF 1e7（規範預設 1e9／1e8）
    # {"config_file": "config.js", "config_rtp_file": "AUTO", "bet_mode": 0,
    #  "total_rounds": 10**8, "card_system_enabled": False, "card_system_is_newbie": False, "base_bet": 1.0},
    # {"config_file": "config.js", "config_rtp_file": "AUTO", "bet_mode": 2,
    #  "total_rounds": 10**7, "card_system_enabled": False, "card_system_is_newbie": False, "base_bet": 1.0},
]
THREADS = max(1, min(12, os.cpu_count() or 1))   # 多執行緒（Numba nogil）；本機 i7-12700H 20 執行緒
OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = True
RUN_SINGLE_SPIN_DEBUG = False
DEBUG_ROUNDS = 1
CARD_RETRY_LIMIT = 10_000
RNG_SEED = 45_045

COIN_BASE = 100.0                      # Credit 基準，與 Overview!A7 一致
MODE_NORMALBET = 0
MODE_EXTRABET = 1                      # Extra Bet（2026-10-15）：押注 2 倍、FG 週期為 NB 的 1/5，卡組 eb_base_game／eb_free_game
MODE_FEATUREBUY = 2
SUPPORTED_BET_MODES = (MODE_NORMALBET, MODE_EXTRABET, MODE_FEATUREBUY)

WW = 0
W2 = 1
C1 = 2
SCORE_SYMBOLS = tuple(range(3, 11))
EMPTY = -1
NSYM = 11                      # 符號 ID 0~10

# 金框不是符號，而是套在一般符號上的旗標（v2：依 Gold Count Weight 逐輪決定顆數）
GOLD_RESULTS = ("WW", "W2")   # 小鬼 / 大鬼；倍數為翻牌後的第二段抽取
NO_WIN_BONUS_GOLD = 2          # game_rule §9.1.12（2026-10-28）：本轉沒得分 → 金框輪再加 2 顆金框（停輪即顯示，不影響得分）

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

def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def resolve_base_dir() -> Path:
    base = Path(__file__).resolve().parent
    if not (base / CONFIG_FILE).exists():
        raise FileNotFoundError(f"找不到 {CONFIG_FILE}，請在 H045 專案資料夾執行。")
    return base


BASE_DIR = resolve_base_dir()


def load_js_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    start = text.index("{")
    end = text.rindex("}") + 1
    return json.loads(text[start:end])


def _version_major(value: Any) -> str:
    return str(value).split(".")[0]


def validate_config_pair(natural: dict[str, Any], rtp: dict[str, Any] | None,
                         natural_name: str, rtp_name: str) -> None:
    if natural.get("game_id") != "H045":
        raise ValueError(f"{natural_name} 的 game_id 必須為 H045")
    version = str(natural.get("excel_version", ""))
    if not version.isdigit() or len(version) != 1:
        raise ValueError(f"{natural_name} 的 excel_version 必須為 1 碼，目前為 {version!r}")
    if rtp is None:
        return
    if rtp.get("game_id") != natural.get("game_id"):
        raise ValueError(f"{rtp_name} 與 {natural_name} 的 game_id 不一致")
    rtp_version = str(rtp.get("excel_version", ""))
    parts = rtp_version.split(".")
    if len(parts) != 4 or not all(p.isdigit() for p in parts):
        raise ValueError(f"{rtp_name} 的 excel_version 必須為 4 碼，目前為 {rtp_version!r}")
    if parts[0] != version:
        raise ValueError(
            f"{rtp_name} 的版本第 1 碼 {parts[0]} 必須等於基礎模型版本 {version}")


# ===== 遊戲核心（Numba）=====
#
# 每轉統計寫在一條 int64 向量（SI）＋ float64 向量（SF），欄位位置如下；
# FG 一場（session）與 BG 一轉共用同一套版面，後面再接「每轉衍生」欄位（E_*）。
# 卡片重骰時只重設這些暫存向量，被重骰掉的轉／場不會進統計（同純 Python 版）。

MVK = 16       # 倍數值種類上限（全域倍數值清單的索引；目前 x1/x2/x3/x5）
SPK = 8        # 分裂顆數欄位（0~7）
NKIND = 3      # mult_kind：0=WW、1=W2、2=SPLIT
KIND_NAMES = ("WW", "W2", "SPLIT")

I_CASC, I_SCAT, I_MAXLM, I_GCONV, I_MWC, I_MCELLS, I_MLEFT = 0, 1, 2, 3, 4, 5, 6
I_BIGUSED, I_BIGSCORED, I_INITGOLD, I_GOLDAPP = 7, 8, 9, 10
O_GOLDEN = 11                       # [2]   WW／W2 翻牌數
O_SPLIT = O_GOLDEN + 2              # [SPK] 分裂實際放置顆數分布
O_MWV = O_SPLIT + SPK               # [MVK] 翻牌抽到的倍數分布
O_MKIND = O_MWV + MVK               # [3*MVK] (WW/W2/SPLIT, 倍數)
O_GREEL = O_MKIND + NKIND * MVK     # [5]   初始盤面每輪金框數
O_SYMH = O_GREEL + 5                # [NSYM] 符號 ways 命中
O_LENH = O_SYMH + NSYM              # [NSYM*6] (符號, 連線長度) 命中
O_INITS = O_LENH + NSYM * 6         # [5*NSYM] 初始盤面符號
O_DROPS = O_INITS + 5 * NSYM        # [5*NSYM] 補牌符號
SPIN_I_LEN = O_DROPS + 5 * NSYM
E_HIT = SPIN_I_LEN                  # 以下為 session（場）層級：每轉衍生計數
E_FLIP = E_HIT + 1
E_MULTSP = E_HIT + 2
E_MUNUSED = E_HIT + 3
E_BIG = E_HIT + 4
E_BIGUSEDSP = E_HIT + 5
E_GSEEN = E_HIT + 6
E_GBOARDS = E_HIT + 7
E_SPECIAL = E_HIT + 8
E_COMBO = E_HIT + 9                 # [6] 0~5+
E_SPINS = E_COMBO + 6
E_RETRIG = E_SPINS + 1
E_CAPPED = E_SPINS + 2
SESS_I_LEN = E_SPINS + 3

F_PAY = 0
O_SYMPAY = 1                        # [NSYM]
O_LENPAY = O_SYMPAY + NSYM          # [NSYM*6]
SESS_F_LEN = O_LENPAY + NSYM * 6

# 全域（局層級）計數
G_ROUNDS, G_CAPPED, G_FGTRIG, G_TRIGCNT, G_RETRY, G_RLE, G_RLBGR, G_RLBGFG, G_RLFG = range(9)
GI_LEN = 9
H_COIN, H_PBG, H_PFG, H_WX, H_WX2, H_MAXWX, H_TRIGPAY = range(7)
GF_LEN = 7
# Multiplier Line 分桶
B_BGCNT, B_FGCNT, B_BFCNT, B_TRIGCNT, B_FGHIT, B_FGSPINS, B_BGMULT, B_FGMULT, B_BGGF, B_FGGF = range(10)
BI_LEN = 10
B_BGPAY, B_FGPAY, B_BFPAY, B_TRIGPAY = range(4)
BF_LEN = 4

# 卡組區段
SEC_NAMES = ("base_game", "free_game", "eb_base_game", "eb_free_game", "buy_feature")
SEC_BASE, SEC_FREE, SEC_EB_BASE, SEC_EB_FREE, SEC_BF = range(5)

GameData = namedtuple("GameData", [
    "reel_sym", "reel_cum", "reel_len", "reel_tot",
    "drop_val", "drop_cum", "drop_n", "drop_tot",
    "gres_cum", "gres_tot",
    "split_val", "split_cum", "split_n", "split_tot",
    "mult_val", "mult_gi", "mult_cum", "mult_n", "mult_tot",
    "gcnt_cum", "gcnt_n", "gcnt_tot",
    "pays", "ladder", "ladder_len", "gold_reels", "split_reels",
    "twbg_id", "twbg_cum", "twbg_tot", "twfg_id", "twfg_cum", "twfg_tot",
    "fs_init", "max_fs", "entry_table", "mv_one",
    "card_cum", "card_n", "card_tot", "card_type", "card_min", "card_max",
    "thresholds",
])

Scratch = namedtuple("Scratch", [
    "si", "sf", "snap", "sym", "mul", "gold", "pre_s", "pre_m", "pre_g",
    "gpos", "bsrc", "cand", "fresh", "nfresh", "cnt", "hit",
    "l_tg", "l_len", "l_ways", "l_raw",
    "sess_i", "sess_f", "bg_i", "bg_f",
])

# Numba 核心收「一般 tuple」（namedtuple 的型別會綁模組名，快取換個執行方式就讀不回）；欄位位置常數如下
_D_REEL_SYM = 0
_D_REEL_CUM = 1
_D_REEL_LEN = 2
_D_REEL_TOT = 3
_D_DROP_VAL = 4
_D_DROP_CUM = 5
_D_DROP_N = 6
_D_DROP_TOT = 7
_D_GRES_CUM = 8
_D_GRES_TOT = 9
_D_SPLIT_VAL = 10
_D_SPLIT_CUM = 11
_D_SPLIT_N = 12
_D_SPLIT_TOT = 13
_D_MULT_VAL = 14
_D_MULT_GI = 15
_D_MULT_CUM = 16
_D_MULT_N = 17
_D_MULT_TOT = 18
_D_GCNT_CUM = 19
_D_GCNT_N = 20
_D_GCNT_TOT = 21
_D_PAYS = 22
_D_LADDER = 23
_D_LADDER_LEN = 24
_D_GOLD_REELS = 25
_D_SPLIT_REELS = 26
_D_TWBG_ID = 27
_D_TWBG_CUM = 28
_D_TWBG_TOT = 29
_D_TWFG_ID = 30
_D_TWFG_CUM = 31
_D_TWFG_TOT = 32
_D_FS_INIT = 33
_D_MAX_FS = 34
_D_ENTRY_TABLE = 35
_D_MV_ONE = 36
_D_CARD_CUM = 37
_D_CARD_N = 38
_D_CARD_TOT = 39
_D_CARD_TYPE = 40
_D_CARD_MIN = 41
_D_CARD_MAX = 42
_D_THRESHOLDS = 43
_W_SI = 0
_W_SF = 1
_W_SNAP = 2
_W_SYM = 3
_W_MUL = 4
_W_GOLD = 5
_W_PRE_S = 6
_W_PRE_M = 7
_W_PRE_G = 8
_W_GPOS = 9
_W_BSRC = 10
_W_CAND = 11
_W_FRESH = 12
_W_NFRESH = 13
_W_CNT = 14
_W_HIT = 15
_W_L_TG = 16
_W_L_LEN = 17
_W_L_WAYS = 18
_W_L_RAW = 19
_W_SESS_I = 20
_W_SESS_F = 21
_W_BG_I = 22
_W_BG_F = 23


def _cum_array(weights) -> tuple[np.ndarray, float]:
    """累積權重（負值視為 0），同純 Python 版 _cumulative。"""
    out = np.cumsum([max(0.0, float(w)) for w in weights]).astype(np.float64)
    return out, float(out[-1]) if len(out) else 0.0


def _section_cap(rtp_config: dict[str, Any], profile: str, section: str, card_enabled: bool) -> float:
    """該 Profile 某卡組「最高有權重 range 卡」的上限；Card System Off 回傳無限大。"""
    if not card_enabled:
        return math.inf
    cards = ((rtp_config.get("card_system") or {}).get("profiles") or {}).get(profile, {}).get(section) or []
    caps = [float(c["max"]) for c in cards
            if str(c.get("type")) == "range" and float(c.get("weight", 0)) > 0 and "max" in c]
    return max(caps) if caps else math.inf


def build_game_data(config: dict[str, Any], rtp_config: dict[str, Any] | None, newbie: bool,
                    card_enabled: bool) -> tuple[GameData, list[int], list[str]]:
    """把 Config 轉成 Numba 核心用的陣列。回傳 (GameData, 全域倍數值清單, 表名清單)。"""
    rtp_config = rtp_config or {}
    names = list(config["tables"])
    T = len(names)
    tid = {n: i for i, n in enumerate(names)}
    lmax = max(len(r) for raw in config["tables"].values() for r in raw["reels"])
    reel_sym = np.zeros((T, 5, lmax), np.int64)
    reel_cum = np.zeros((T, 5, lmax), np.float64)
    reel_len = np.zeros((T, 5), np.int64)
    reel_tot = np.zeros((T, 5), np.float64)
    drop_val = np.zeros((T, 5, NSYM), np.int64)
    drop_cum = np.zeros((T, 5, NSYM), np.float64)
    drop_n = np.zeros((T, 5), np.int64)
    drop_tot = np.zeros((T, 5), np.float64)
    gres_cum = np.zeros((T, 2), np.float64)
    gres_tot = np.zeros(T, np.float64)
    split_val = np.zeros((T, 16), np.int64)
    split_cum = np.zeros((T, 16), np.float64)
    split_n = np.zeros(T, np.int64)
    split_tot = np.zeros(T, np.float64)
    mult_val = np.zeros((T, 2, MVK), np.int64)
    mult_gi = np.zeros((T, 2, MVK), np.int64)
    mult_cum = np.zeros((T, 2, MVK), np.float64)
    mult_n = np.zeros((T, 2), np.int64)
    mult_tot = np.zeros((T, 2), np.float64)
    gcnt_cum = np.zeros((T, 2, 5, 8), np.float64)
    gcnt_n = np.zeros((T, 2, 5), np.int64)
    gcnt_tot = np.zeros((T, 2, 5), np.float64)

    if len(config["symbol_names"]) != NSYM:
        raise ValueError(f"符號數必須為 {NSYM}")
    mvals = sorted({1} | {int(k) for raw in config["tables"].values()
                          for tbl in raw["multiplier_wild_weight"].values() for k in tbl})
    if len(mvals) > MVK:
        raise ValueError(f"倍數值種類 {len(mvals)} 超過上限 {MVK}")
    mgi = {v: i for i, v in enumerate(mvals)}

    for t, name in enumerate(names):
        raw = config["tables"][name]
        for r, (symbols, weights) in enumerate(zip(raw["reels"], raw["symbol_weight"])):
            cum, tot = _cum_array(weights)
            n = len(symbols)
            reel_sym[t, r, :n] = list(map(int, symbols))
            reel_cum[t, r, :n] = cum
            reel_len[t, r] = n
            reel_tot[t, r] = tot
        drop = {int(k): v for k, v in raw["drop_weight"].items()}
        for r in range(5):
            values = [sid for sid in sorted(drop) if float(drop[sid][r]) > 0]
            cum, tot = _cum_array([float(drop[sid][r]) for sid in values])
            drop_val[t, r, :len(values)] = values
            drop_cum[t, r, :len(values)] = cum
            drop_n[t, r] = len(values)
            drop_tot[t, r] = tot
        grw = raw["gold_result_weight"]
        cum, tot = _cum_array([float(grw.get(k, 0)) for k in GOLD_RESULTS])
        gres_cum[t] = cum
        gres_tot[t] = tot
        scw = {int(k): float(v) for k, v in raw["split_count_weight"].items()}
        s_values = sorted(scw)
        if max(s_values) >= SPK:
            raise ValueError(f"分裂顆數上限 {SPK - 1}")
        cum, tot = _cum_array([scw[k] for k in s_values])
        split_val[t, :len(s_values)] = s_values
        split_cum[t, :len(s_values)] = cum
        split_n[t] = len(s_values)
        split_tot[t] = tot
        for o, key in enumerate(GOLD_RESULTS):
            table = raw["multiplier_wild_weight"].get(key, {"1": 1})
            values = sorted(int(k) for k in table)
            cum, tot = _cum_array([float(table[str(v)]) for v in values])
            mult_val[t, o, :len(values)] = values
            mult_gi[t, o, :len(values)] = [mgi[v] for v in values]
            mult_cum[t, o, :len(values)] = cum
            mult_n[t, o] = len(values)
            mult_tot[t, o] = tot
        # 金框顆數：盤面表自帶 gold_count_weight 就用該表，否則用場景（bg／fg）全域值
        for scene_index, scene in enumerate(("bg", "fg")):
            per_reels = raw.get("gold_count_weight") or config["gold_count_weight"][scene]
            for r, per_reel in enumerate(per_reels):
                cum, tot = _cum_array(per_reel)
                gcnt_cum[t, scene_index, r, :len(cum)] = cum
                gcnt_n[t, scene_index, r] = len(cum)
                gcnt_tot[t, scene_index, r] = tot

    pays = np.zeros((NSYM, 6), np.float64)
    for k, v in config["pays"].items():
        for i, p in enumerate(v):
            pays[int(k), i + 3] = float(p)
    ladder = np.zeros((2, 16), np.int64)
    ladder_len = np.zeros(2, np.int64)
    for i, scene in enumerate(("bg", "fg")):
        lad = list(map(int, config["cascade_multiplier"][scene]))
        ladder[i, :len(lad)] = lad
        ladder_len[i] = len(lad)

    def table_weight(group):
        weights = config["table_weight"][group]
        ids = np.array([tid[n] for n in weights], np.int64)
        cum, tot = _cum_array([float(weights[n]) for n in weights])
        return ids, cum, tot

    twbg_id, twbg_cum, twbg_tot = table_weight("bg")
    twfg_id, twfg_cum, twfg_tot = table_weight("fg")
    fs_table = {int(k): v for k, v in config["free_spins"].items()}
    fs_init = np.zeros(32, np.int64)
    for s in range(3, 32):
        key = min(s, max(fs_table))
        fs_init[s] = int(fs_table[key]["initial"]) if key in fs_table else -1

    # 卡片
    profile = "newbie" if newbie else "oldhand"
    prof = ((rtp_config.get("card_system") or {}).get("profiles") or {}).get(profile, {})
    ncmax = max([1] + [len(prof.get(sec) or []) for sec in SEC_NAMES])
    card_cum = np.zeros((5, ncmax), np.float64)
    card_n = np.zeros(5, np.int64)
    card_tot = np.zeros(5, np.float64)
    card_type = np.zeros((5, ncmax), np.int64)
    card_min = np.zeros((5, ncmax), np.float64)
    card_max = np.zeros((5, ncmax), np.float64)
    if card_enabled:
        for i, sec in enumerate(SEC_NAMES):
            cards = prof.get(sec) or []
            if not cards:
                continue
            cum, tot = _cum_array([float(c["weight"]) for c in cards])
            card_cum[i, :len(cards)] = cum
            card_n[i] = len(cards)
            card_tot[i] = tot
            for j, c in enumerate(cards):
                card_type[i, j] = 1 if c.get("type") == "free_game" else 0
                card_min[i, j] = float(c["min"])
                card_max[i, j] = float(c["max"])

    data = GameData(
        reel_sym, reel_cum, reel_len, reel_tot,
        drop_val, drop_cum, drop_n, drop_tot,
        gres_cum, gres_tot,
        split_val, split_cum, split_n, split_tot,
        mult_val, mult_gi, mult_cum, mult_n, mult_tot,
        gcnt_cum, gcnt_n, gcnt_tot,
        pays, ladder, ladder_len,
        np.array(list(map(int, config["gold_reels"])), np.int64),
        np.array(list(map(int, config["split_target_reels"])), np.int64),
        twbg_id, twbg_cum, twbg_tot, twfg_id, twfg_cum, twfg_tot,
        fs_init, int(config["max_free_spins"]),
        int(tid[config["bet_modes"]["buy_feature"]["entry_table"]]), int(mgi[1]),
        card_cum, card_n, card_tot, card_type, card_min, card_max,
        np.array(MULTIPLIER_THRESHOLDS, np.float64),
    )
    return data, mvals, names


def mode_caps(rtp_config: dict[str, Any] | None, newbie: bool, card_enabled: bool,
              bet_mode: int) -> tuple[float, float]:
    """Max Win（單局上限）與 BG Trigger Cap（數學模型規範 §1.4.4／§2.3）；Card System Off 皆為無限大。
    BF 取 buy_feature 卡組上限；NB 取 base_game／free_game 兩者上限較大者；EB 用 eb_* 卡組。"""
    rtp_config = rtp_config or {}
    profile = "newbie" if newbie else "oldhand"
    cap = {sec: _section_cap(rtp_config, profile, sec, card_enabled) for sec in SEC_NAMES}
    # Max Win 一律用老手上限（2026-11-09 對齊 SPS）：新手不因新手卡組上限截斷，新手得分只由卡片區間控制
    old = {sec: _section_cap(rtp_config, "oldhand", sec, card_enabled) for sec in SEC_NAMES}
    if bet_mode == MODE_FEATUREBUY:
        return old["buy_feature"], cap["base_game"]
    if bet_mode == MODE_EXTRABET:
        return max(old["eb_free_game"], old["eb_base_game"]), cap["eb_base_game"]
    return max(old["free_game"], old["base_game"]), cap["base_game"]


def new_scratch() -> Scratch:
    return Scratch(
        np.zeros(SESS_I_LEN, np.int64), np.zeros(SESS_F_LEN, np.float64), np.zeros(SESS_I_LEN, np.int64),
        np.zeros((5, 4), np.int64), np.zeros((5, 4), np.int64), np.zeros((5, 4), np.int64),
        np.zeros((5, 4), np.int64), np.zeros((5, 4), np.int64), np.zeros((5, 4), np.int64),
        np.zeros((20, 2), np.int64), np.zeros((20, 4), np.int64), np.zeros(20, np.int64),
        np.zeros((5, 4), np.int64), np.zeros(5, np.int64), np.zeros((5, NSYM), np.int64),
        np.zeros((5, 4), np.int64),
        np.zeros(8, np.int64), np.zeros(8, np.int64), np.zeros(8, np.int64), np.zeros(8, np.float64),
        np.zeros(SESS_I_LEN, np.int64), np.zeros(SESS_F_LEN, np.float64),
        np.zeros(SESS_I_LEN, np.int64), np.zeros(SESS_F_LEN, np.float64),
    )


@njit(nogil=True, cache=True)
def _pick(cum, n, total):
    """同 bisect.bisect_right(cumulative, random()*total)，結果上限 n-1。"""
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
def _partial_shuffle(arr, k, m):
    """等同 rng.shuffle(arr[:k]) 後取前 m 個（Fisher-Yates 只做前 m 步）。"""
    for i in range(m):
        j = i + int(np.random.random() * (k - i))
        tmp = arr[i]
        arr[i] = arr[j]
        arr[j] = tmp


@njit(nogil=True, cache=True)
def _evaluate(D, W):
    """1024 Ways 判獎。回傳 (連線數, line_mult)；各連線寫在 W[_W_L_]*，命中格寫在 W[_W_HIT]。
    金框是旗標不是符號，判獎一律用底層符號（game_rule §3.1）。"""
    sym = W[_W_SYM]
    cnt = W[_W_CNT]
    hit = W[_W_HIT]
    cnt[:, :] = 0
    hit[:, :] = 0
    for r in range(5):
        for c in range(4):
            s = sym[r, c]
            if s >= 0:
                cnt[r, s] += 1
    nlines = 0
    for tg in range(3, NSYM):
        ways = 1
        length = 0
        for r in range(5):
            k = cnt[r, WW] + cnt[r, W2] + cnt[r, tg]
            if k == 0:
                break
            ways *= k
            length += 1
        if length < 3:
            continue
        raw = D[_D_PAYS][tg, length] * ways
        if raw <= 0:
            continue
        for r in range(length):
            for c in range(4):
                s = sym[r, c]
                if s == WW or s == W2 or s == tg:
                    hit[r, c] = 1
        W[_W_L_TG][nlines] = tg
        W[_W_L_LEN][nlines] = length
        W[_W_L_WAYS][nlines] = ways
        W[_W_L_RAW][nlines] = raw
        nlines += 1
    # game_rule §5.3：只有本次中獎被消除的帶倍 WILD 倍數相加（x1 不計入），總和為 0 視為 x1
    used = 0
    if nlines > 0:
        for r in range(5):
            for c in range(4):
                if hit[r, c] == 1 and (sym[r, c] == WW or sym[r, c] == W2) and W[_W_MUL][r, c] > 1:
                    used += W[_W_MUL][r, c]
    return nlines, (used if used > 0 else 1)


@njit(nogil=True, cache=True)
def _draw_gold(D, W, t, scene):
    """依 Gold Count Weight 逐輪抽出金框顆數，再隨機挑格子套上金框旗標。
    金框只出現在 gold_reels（R2~R4），且不套在 Scatter 上（比照競品）。"""
    sym = W[_W_SYM]
    gold = W[_W_GOLD]
    cand = W[_W_CAND]
    gold[:, :] = 0
    for gr in D[_D_GOLD_REELS]:
        tot = D[_D_GCNT_TOT][t, scene, gr]
        if tot <= 0:
            continue
        count = _pick(D[_D_GCNT_CUM][t, scene, gr], D[_D_GCNT_N][t, scene, gr], tot)
        if count <= 0:
            continue
        k = 0
        for c in range(4):
            if sym[gr, c] != C1:
                cand[k] = c
                k += 1
        if k == 0:
            continue
        m = min(count, k)
        _partial_shuffle(cand, k, m)
        for i in range(m):
            gold[gr, cand[i]] = 1


@njit(nogil=True, cache=True)
def _spin(D, W, t, scene, free_game, bet, cap):
    """單轉（含連消）。結果寫入 W[_W_SI]／W[_W_SF]；W[_W_SYM]／W[_W_MUL]／W[_W_GOLD] 為最終盤面。"""
    si = W[_W_SI]
    sf = W[_W_SF]
    sym = W[_W_SYM]
    mul = W[_W_MUL]
    gold = W[_W_GOLD]
    si[:] = 0
    sf[:] = 0.0
    si[I_MAXLM] = 1
    ladder_len = D[_D_LADDER_LEN][scene]
    # --- 停輪 ---
    for r in range(5):
        n = D[_D_REEL_LEN][t, r]
        st = _pick(D[_D_REEL_CUM][t, r], n, D[_D_REEL_TOT][t, r])
        for c in range(4):
            s = D[_D_REEL_SYM][t, r, (st + c) % n]
            sym[r, c] = s
            mul[r, c] = 0
            gold[r, c] = 0
            si[O_INITS + r * NSYM + s] += 1
    _draw_gold(D, W, t, scene)
    cand = W[_W_CAND]
    ig = 0
    for r in range(5):
        g = 0
        for c in range(4):
            g += gold[r, c]
        si[O_GREEL + r] += g
        ig += g
    si[I_INITGOLD] = ig
    si[I_GOLDAPP] = ig

    has_last = False
    last_ng = 0
    last_split = False
    while True:
        nlines, line_mult = _evaluate(D, W)
        if nlines == 0:
            # 2026-10-21 使用者定案：最後一次翻牌後沒有再連線，翻出來的一律以原位無倍數小鬼呈現（大鬼不分裂），
            # 盤面與統計都以最終畫面為準
            if has_last:
                snap = W[_W_SNAP]
                si[O_GOLDEN] = snap[O_GOLDEN]
                si[O_GOLDEN + 1] = snap[O_GOLDEN + 1]
                si[I_GCONV] = snap[I_GCONV]
                si[I_MWC] = snap[I_MWC]
                si[I_MCELLS] = snap[I_MCELLS]
                si[I_BIGUSED] = snap[I_BIGUSED]
                for i in range(SPK):
                    si[O_SPLIT + i] = snap[O_SPLIT + i]
                for i in range(MVK):
                    si[O_MWV + i] = snap[O_MWV + i]
                for i in range(NKIND * MVK):
                    si[O_MKIND + i] = snap[O_MKIND + i]
                si[O_GOLDEN] += last_ng
                si[I_GCONV] += last_ng
                si[O_MWV + D[_D_MV_ONE]] += last_ng
                si[O_MKIND + 0 * MVK + D[_D_MV_ONE]] += last_ng
                if last_split:
                    for r in range(5):
                        for c in range(4):
                            sym[r, c] = W[_W_PRE_S][r, c]
                            mul[r, c] = W[_W_PRE_M][r, c]
                            gold[r, c] = W[_W_PRE_G][r, c]
                for i in range(last_ng):
                    sym[W[_W_GPOS][i, 0], W[_W_GPOS][i, 1]] = WW
                    mul[W[_W_GPOS][i, 0], W[_W_GPOS][i, 1]] = 0
            break
        mlt = D[_D_LADDER][scene, min(si[I_CASC], ladder_len - 1)]
        raw_pay = 0.0
        for li in range(nlines):
            raw_pay += W[_W_L_RAW][li] * line_mult
        sf[F_PAY] += raw_pay * mlt * bet
        if line_mult > si[I_MAXLM]:
            si[I_MAXLM] = line_mult
        si[I_CASC] += 1
        for li in range(nlines):
            tg = W[_W_L_TG][li]
            ln = W[_W_L_LEN][li]
            p = W[_W_L_RAW][li] * line_mult * mlt * bet
            si[O_SYMH + tg] += W[_W_L_WAYS][li]
            sf[O_SYMPAY + tg] += p
            si[O_LENH + tg * 6 + ln] += 1
            sf[O_LENPAY + tg * 6 + ln] += p

        # 命中格：金框不消除（當下翻成本體），其餘清空
        ng = 0
        for r in range(5):
            for c in range(4):
                if W[_W_HIT][r, c] == 0:
                    continue
                if sym[r, c] == W2 and gold[r, c] == 0:
                    si[I_BIGSCORED] = 1
                if gold[r, c] == 1:
                    W[_W_GPOS][ng, 0] = r
                    W[_W_GPOS][ng, 1] = c
                    ng += 1
                    gold[r, c] = 0
                else:
                    sym[r, c] = EMPTY
                    mul[r, c] = 0

        # 翻牌前統計快照（連消結束時改記成「全部無倍數小鬼」）
        nbig = 0
        if ng > 0:
            W[_W_SNAP][:SPIN_I_LEN] = si[:SPIN_I_LEN]
            # game_rule §5.2～5.3：每顆中獎金框抽小鬼／大鬼，再抽倍數；補牌前寫進原格
            for i in range(ng):
                r = W[_W_GPOS][i, 0]
                c = W[_W_GPOS][i, 1]
                o = _pick(D[_D_GRES_CUM][t], 2, D[_D_GRES_TOT][t])
                # game_rule §9.1.10：BG 一把 Spin 最多成立一次大鬼，之後改以小鬼處理
                if o == 1 and not free_game and si[I_BIGUSED] == 1:
                    o = 0
                si[O_GOLDEN + o] += 1
                si[I_GCONV] += 1
                sym[r, c] = W2 if o == 1 else WW
                k = _pick(D[_D_MULT_CUM][t, o], D[_D_MULT_N][t, o], D[_D_MULT_TOT][t, o])
                v = D[_D_MULT_VAL][t, o, k]
                gi = D[_D_MULT_GI][t, o, k]
                if v > 1:
                    si[I_MWC] += 1
                    si[I_MCELLS] += 1
                si[O_MWV + gi] += 1
                si[O_MKIND + o * MVK + gi] += 1
                mul[r, c] = v if v > 1 else 0
                if o == 1:
                    si[I_BIGUSED] = 1
                    W[_W_BSRC][nbig, 0] = r
                    W[_W_BSRC][nbig, 1] = c
                    W[_W_BSRC][nbig, 2] = v
                    W[_W_BSRC][nbig, 3] = gi
                    nbig += 1

        # game_rule §5.1：原地補牌——消除的格子直接在原位補新符號，其餘符號不移動
        for r in range(5):
            W[_W_NFRESH][r] = 0
            for c in range(4):
                W[_W_FRESH][r, c] = 0
                if sym[r, c] == EMPTY:
                    s = D[_D_DROP_VAL][t, r, _pick(D[_D_DROP_CUM][t, r], D[_D_DROP_N][t, r], D[_D_DROP_TOT][t, r])]
                    sym[r, c] = s
                    mul[r, c] = 0
                    gold[r, c] = 0
                    si[O_DROPS + r * NSYM + s] += 1
                    W[_W_FRESH][r, c] = 1
                    W[_W_NFRESH][r] += 1

        # game_rule §9.1.11：補牌後重抽顆數 N，保留存活金框，不足才從新補格子補上
        added = 0
        for gr in D[_D_GOLD_REELS]:
            if W[_W_NFRESH][gr] == 0:
                continue
            tot = D[_D_GCNT_TOT][t, scene, gr]
            target = 0
            if tot > 0:
                target = _pick(D[_D_GCNT_CUM][t, scene, gr], D[_D_GCNT_N][t, scene, gr], tot)
            alive = 0
            for c in range(4):
                alive += gold[gr, c]
            short = target - alive
            if short <= 0:
                continue
            k = 0
            for c in range(4):
                if W[_W_FRESH][gr, c] == 1 and gold[gr, c] == 0 and sym[gr, c] != C1:
                    cand[k] = c
                    k += 1
            m = min(short, k)
            _partial_shuffle(cand, k, m)
            for i in range(m):
                gold[gr, cand[i]] = 1
            added += m
        si[I_GOLDAPP] += added

        # game_rule §5.4：補牌後，大鬼本體丟出 2～4 顆 W2（倍數同本體），落點依補牌後的盤面
        if nbig > 0:
            for r in range(5):
                for c in range(4):
                    W[_W_PRE_S][r, c] = sym[r, c]
                    W[_W_PRE_M][r, c] = mul[r, c]
                    W[_W_PRE_G][r, c] = gold[r, c]
            for b in range(nbig):
                r0 = W[_W_BSRC][b, 0]
                c0 = W[_W_BSRC][b, 1]
                v = W[_W_BSRC][b, 2]
                gi = W[_W_BSRC][b, 3]
                count = D[_D_SPLIT_VAL][t, _pick(D[_D_SPLIT_CUM][t], D[_D_SPLIT_N][t], D[_D_SPLIT_TOT][t])]
                k = 0
                for r in D[_D_SPLIT_REELS]:
                    for c in range(4):
                        s = sym[r, c]
                        if s != WW and s != W2 and s != C1 and not (r == r0 and c == c0):
                            cand[k] = r * 4 + c
                            k += 1
                if k == 0:
                    si[O_SPLIT + 0] += 1
                    continue
                m = min(count, k)
                _partial_shuffle(cand, k, m)
                for i in range(m):
                    r = cand[i] // 4
                    c = cand[i] % 4
                    si[O_MKIND + 2 * MVK + gi] += 1
                    if v > 1:
                        si[I_MCELLS] += 1
                    # game_rule §5.4：分裂體是 W2，倍數同本體；蓋到金框即變 W2，金框消失
                    sym[r, c] = W2
                    mul[r, c] = v if v > 1 else 0
                    gold[r, c] = 0
                si[O_SPLIT + m] += 1
        has_last = ng > 0
        last_ng = ng
        last_split = nbig > 0

        if sf[F_PAY] >= cap:
            break

    if sf[F_PAY] <= 0:
        # game_rule §9.1.12：沒得分時在金框輪隨機挑 2 格非金框、非 C1 加金框（僅顯示，不影響得分）
        k = 0
        for gr in D[_D_GOLD_REELS]:
            for c in range(4):
                if gold[gr, c] == 0 and sym[gr, c] != C1:
                    cand[k] = gr * 4 + c
                    k += 1
        m = min(NO_WIN_BONUS_GOLD, k)
        _partial_shuffle(cand, k, m)
        for i in range(m):
            gold[cand[i] // 4, cand[i] % 4] = 1
    sc = 0
    left = 0
    for r in range(5):
        for c in range(4):
            if sym[r, c] == C1:
                sc += 1
            if (sym[r, c] == WW or sym[r, c] == W2) and mul[r, c] > 1:
                left += 1
    si[I_SCAT] = sc
    si[I_MLEFT] = left


@njit(nogil=True, cache=True)
def _add_spin(dst_i, dst_f, si, sf):
    """一轉的統計加進 session（場）：數值相加、max_line_multiplier 取大，並記每轉衍生計數。"""
    for i in range(SPIN_I_LEN):
        dst_i[i] += si[i]
    dst_i[I_MAXLM] -= si[I_MAXLM]
    if si[I_MAXLM] > dst_i[I_MAXLM]:
        dst_i[I_MAXLM] = si[I_MAXLM]
    for i in range(SESS_F_LEN):
        dst_f[i] += sf[i]
    dst_i[E_HIT] += 1 if sf[F_PAY] > 0 else 0
    dst_i[E_FLIP] += 1 if si[I_GCONV] > 0 else 0
    dst_i[E_MULTSP] += 1 if si[I_MWC] > 0 else 0
    dst_i[E_MUNUSED] += 1 if (si[I_MCELLS] > 0 and si[I_MLEFT] == si[I_MCELLS]) else 0
    big = si[O_GOLDEN + 1] > 0
    dst_i[E_BIG] += 1 if big else 0
    dst_i[E_BIGUSEDSP] += 1 if (big and si[I_BIGSCORED] == 1) else 0
    dst_i[E_GSEEN] += 1 if si[I_GOLDAPP] > 0 else 0
    dst_i[E_GBOARDS] += 1 if si[I_INITGOLD] > 0 else 0
    dst_i[E_SPECIAL] += 1 if si[I_SCAT] > 0 else 0
    dst_i[E_COMBO + min(si[I_CASC], 5)] += 1
    dst_i[E_SPINS] += 1


@njit(nogil=True, cache=True)
def _free_session(D, W, initial, budget, bet, cap):
    """FG 一場：結果寫入 W[_W_SESS_I]／W[_W_SESS_F]。Retrigger 固定 +5、上限 max_free_spins（同純 Python 版）。"""
    sess_i = W[_W_SESS_I]
    sess_f = W[_W_SESS_F]
    sess_i[:] = 0
    sess_f[:] = 0.0
    remaining = initial
    played = 0
    max_fs = D[_D_MAX_FS]
    while remaining > 0 and played < max_fs:
        remaining -= 1
        played += 1
        t = D[_D_TWFG_ID][_pick(D[_D_TWFG_CUM], len(D[_D_TWFG_ID]), D[_D_TWFG_TOT])]
        _spin(D, W, t, 1, True, bet, cap)
        _add_spin(sess_i, sess_f, W[_W_SI], W[_W_SF])
        if budget + sess_f[F_PAY] >= cap:
            sess_i[E_CAPPED] = 1
            break
        if W[_W_SI][I_SCAT] >= 3 and played + remaining < max_fs:
            add = min(5, max_fs - played - remaining)
            if add > 0:
                remaining += add
                sess_i[E_RETRIG] += 1


@njit(nogil=True, cache=True)
def _pick_card(D, sec, card_draws):
    idx = _pick(D[_D_CARD_CUM][sec], D[_D_CARD_N][sec], D[_D_CARD_TOT][sec])
    card_draws[sec, idx] += 1
    return idx


@njit(nogil=True, cache=True)
def _card_feature(D, W, sec, initial, budget, bet, cap, gi, card_draws):
    """FG 卡：整場重跑直到 FG 得分落在卡片區間（min < x <= max），上限 CARD_RETRY_LIMIT。"""
    idx = _pick_card(D, sec, card_draws)
    lo = D[_D_CARD_MIN][sec, idx]
    hi = D[_D_CARD_MAX][sec, idx]
    for _ in range(CARD_RETRY_LIMIT):
        _free_session(D, W, initial, budget, bet, cap)
        ratio = W[_W_SESS_F][F_PAY] / bet
        if lo < ratio and ratio <= hi:
            return
        gi[G_RETRY] += 1
    gi[G_RLE] += 1
    gi[G_RLFG] += 1


@njit(nogil=True, cache=True)
def _natural_base_spin(D, W, bet, cap):
    t = D[_D_TWBG_ID][_pick(D[_D_TWBG_CUM], len(D[_D_TWBG_ID]), D[_D_TWBG_TOT])]
    _spin(D, W, t, 0, False, bet, cap)


@njit(nogil=True, cache=True)
def _card_spin(D, W, sec, bet, cap, trig_cap, gi, card_draws):
    """BG 卡：整把重骰直到符合。free_game 卡須同時「觸發 FG」且 BG 得分 ≤ BG Trigger Cap（數學模型規範 §2.3）。"""
    idx = _pick_card(D, sec, card_draws)
    want_fg = D[_D_CARD_TYPE][sec, idx] == 1
    lo = D[_D_CARD_MIN][sec, idx]
    hi = D[_D_CARD_MAX][sec, idx]
    for _ in range(CARD_RETRY_LIMIT):
        _natural_base_spin(D, W, bet, cap)
        ratio = W[_W_SF][F_PAY] / bet
        if want_fg:
            if W[_W_SI][I_SCAT] >= 3 and ratio <= trig_cap:
                return
        elif W[_W_SI][I_SCAT] < 3 and lo < ratio and ratio <= hi:
            return
        gi[G_RETRY] += 1
    gi[G_RLE] += 1
    if want_fg:
        gi[G_RLBGFG] += 1
    else:
        gi[G_RLBGR] += 1


@njit(nogil=True, cache=True)
def _threshold_index(thresholds, x):
    for i in range(len(thresholds)):
        if x <= thresholds[i]:
            return i
    return len(thresholds) - 1


@njit(nogil=True, cache=True)
def simulate_chunk(D, rounds, bet_mode, bet, wager, card_on, max_win, trig_cap, seed):
    """跑 rounds 局，回傳統計陣列。bet＝基礎押注（得分與卡片倍率分母），wager＝實際扣款。"""
    np.random.seed(seed)
    W = (
        np.zeros(SESS_I_LEN, np.int64), np.zeros(SESS_F_LEN, np.float64), np.zeros(SESS_I_LEN, np.int64),
        np.zeros((5, 4), np.int64), np.zeros((5, 4), np.int64), np.zeros((5, 4), np.int64),
        np.zeros((5, 4), np.int64), np.zeros((5, 4), np.int64), np.zeros((5, 4), np.int64),
        np.zeros((20, 2), np.int64), np.zeros((20, 4), np.int64), np.zeros(20, np.int64),
        np.zeros((5, 4), np.int64), np.zeros(5, np.int64), np.zeros((5, NSYM), np.int64),
        np.zeros((5, 4), np.int64),
        np.zeros(8, np.int64), np.zeros(8, np.int64), np.zeros(8, np.int64), np.zeros(8, np.float64),
        np.zeros(SESS_I_LEN, np.int64), np.zeros(SESS_F_LEN, np.float64),
        np.zeros(SESS_I_LEN, np.int64), np.zeros(SESS_F_LEN, np.float64),
    )
    nb = len(D[_D_THRESHOLDS])
    gi = np.zeros(GI_LEN, np.int64)
    gf = np.zeros(GF_LEN, np.float64)
    gs_i = np.zeros((2, SESS_I_LEN), np.int64)
    gs_f = np.zeros((2, SESS_F_LEN), np.float64)
    gs_i[0, I_MAXLM] = 1
    gs_i[1, I_MAXLM] = 1
    bi = np.zeros((BI_LEN, nb), np.int64)
    bfl = np.zeros((BF_LEN, nb), np.float64)
    bcombo = np.zeros((2, nb, 5), np.int64)
    bgold = np.zeros((2, nb, 2), np.int64)
    card_draws = np.zeros((5, D[_D_CARD_CUM].shape[1]), np.int64)
    cap = max_win * bet
    eb = bet_mode == 1
    sec_base = SEC_EB_BASE if eb else SEC_BASE
    sec_free = SEC_EB_FREE if eb else SEC_FREE
    bg_i = W[_W_BG_I]
    bg_f = W[_W_BG_F]
    sess_i = W[_W_SESS_I]
    sess_f = W[_W_SESS_F]

    for _ in range(rounds):
        pay_bg = 0.0
        pay_fg = 0.0
        fg_on = False
        trig = False
        trig_pay = 0.0
        capped = False
        if bet_mode == 2:
            # 進場盤＝用 BF_Symbol 照常轉一次 BG（含金框、照常判獎）；BF 表保證任何停點都不得分、至少 3 顆 C1
            t = D[_D_ENTRY_TABLE]
            for r in range(5):
                n = D[_D_REEL_LEN][t, r]
                st = _pick(D[_D_REEL_CUM][t, r], n, D[_D_REEL_TOT][t, r])
                for c in range(4):
                    W[_W_SYM][r, c] = D[_D_REEL_SYM][t, r, (st + c) % n]
                    W[_W_MUL][r, c] = 0
            _draw_gold(D, W, t, 0)   # 進場盤照常上金框（BF 表保證不得分，金框不影響結果）
            nl, _lm = _evaluate(D, W)
            if nl > 0:
                raise RuntimeError("BF_Symbol 權重必須保證進場盤不得分")
            scatter = 0
            for r in range(5):
                for c in range(4):
                    if W[_W_SYM][r, c] == C1:
                        scatter += 1
            if scatter < 3:
                raise RuntimeError("BF_Symbol 權重必須保證進場盤至少 3 顆 C1")
            spins = D[_D_FS_INIT][min(scatter, 31)]
            if card_on:
                _card_feature(D, W, SEC_BF, spins, 0.0, bet, cap, gi, card_draws)
            else:
                _free_session(D, W, spins, 0.0, bet, cap)
            sess_i[E_SPECIAL] += 1   # 進場盤本身含 SC
            fg_on = True
            capped = sess_i[E_CAPPED] == 1
            pay_fg = min(sess_f[F_PAY], cap)
        else:
            if card_on:
                _card_spin(D, W, sec_base, bet, cap, trig_cap, gi, card_draws)
            else:
                _natural_base_spin(D, W, bet, cap)
            bg_i[:] = 0
            bg_f[:] = 0.0
            _add_spin(bg_i, bg_f, W[_W_SI], W[_W_SF])
            pay_bg = W[_W_SF][F_PAY]
            scatter = W[_W_SI][I_SCAT]
            if scatter >= 3:
                trig = True
                trig_pay = pay_bg
                initial = D[_D_FS_INIT][min(scatter, 31)]
                if card_on:
                    _card_feature(D, W, sec_free, initial, pay_bg, bet, cap, gi, card_draws)
                else:
                    _free_session(D, W, initial, pay_bg, bet, cap)
                fg_on = True
                pay_fg = sess_f[F_PAY]
                capped = sess_i[E_CAPPED] == 1
            if pay_bg + pay_fg > cap:          # game_rule §9.10.2：達上限即截斷
                overflow = pay_bg + pay_fg - cap
                pay_fg = max(0.0, pay_fg - overflow)
                if pay_bg + pay_fg > cap:
                    pay_bg = min(pay_bg, cap)
                capped = True

        # --- 累計（同純 Python 版 _accumulate）---
        gi[G_ROUNDS] += 1
        gf[H_COIN] += wager
        gf[H_PBG] += pay_bg
        gf[H_PFG] += pay_fg
        wx = (pay_bg + pay_fg) / wager
        gf[H_WX] += wx
        gf[H_WX2] += wx * wx
        if wx > gf[H_MAXWX]:
            gf[H_MAXWX] = wx
        if capped:
            gi[G_CAPPED] += 1
        if fg_on:
            gi[G_FGTRIG] += 1
        if trig:
            gi[G_TRIGCNT] += 1
            gf[H_TRIGPAY] += trig_pay
        if bet_mode != 2:
            m = gs_i[0, I_MAXLM]
            for i in range(SESS_I_LEN):
                gs_i[0, i] += bg_i[i]
            gs_i[0, I_MAXLM] = max(m, bg_i[I_MAXLM])
            for i in range(SESS_F_LEN):
                gs_f[0, i] += bg_f[i]
        if fg_on:
            m = gs_i[1, I_MAXLM]
            for i in range(SESS_I_LEN):
                gs_i[1, i] += sess_i[i]
            gs_i[1, I_MAXLM] = max(m, sess_i[I_MAXLM])
            for i in range(SESS_F_LEN):
                gs_f[1, i] += sess_f[i]

        if bet_mode == 2:
            # 數學模型規範 §2.5：BF 的倍率判定分母是 Normal Bet 基準成本，不是購買價
            idx = _threshold_index(D[_D_THRESHOLDS], pay_fg / bet)
            bi[B_BFCNT, idx] += 1
            bfl[B_BFPAY, idx] += pay_fg
        elif trig:
            idx = _threshold_index(D[_D_THRESHOLDS], trig_pay / bet)
            bi[B_TRIGCNT, idx] += 1
            bfl[B_TRIGPAY, idx] += trig_pay
            fi = _threshold_index(D[_D_THRESHOLDS], pay_fg / bet)
            bi[B_FGCNT, fi] += 1
            bfl[B_FGPAY, fi] += pay_fg
            bi[B_FGSPINS, fi] += sess_i[E_SPINS]
            bi[B_FGHIT, fi] += sess_i[E_HIT]
            bi[B_FGMULT, fi] += sess_i[E_MULTSP]
            bi[B_FGGF, fi] += sess_i[I_INITGOLD]
            bgold[1, fi, 0] += sess_i[O_GOLDEN]
            bgold[1, fi, 1] += sess_i[O_GOLDEN + 1]
            for k in range(6):
                bcombo[1, fi, min(max(k, 1), 5) - 1] += sess_i[E_COMBO + k]
        else:
            idx = _threshold_index(D[_D_THRESHOLDS], pay_bg / bet)
            bi[B_BGCNT, idx] += 1
            bfl[B_BGPAY, idx] += pay_bg
            bi[B_BGMULT, idx] += bg_i[E_MULTSP]
            bi[B_BGGF, idx] += bg_i[I_INITGOLD]
            bgold[0, idx, 0] += bg_i[O_GOLDEN]
            bgold[0, idx, 1] += bg_i[O_GOLDEN + 1]
            bcombo[0, idx, min(max(bg_i[I_CASC], 1), 5) - 1] += 1
    return gi, gf, gs_i, gs_f, bi, bfl, bcombo, bgold, card_draws


# ===== 統計 =====

def wager_for_mode(mode: int, base_bet: float) -> float:
    if mode == MODE_NORMALBET:
        return base_bet
    if mode == MODE_EXTRABET:
        return base_bet * float(CFG["bet_modes"]["extra_bet"]["cost_multiplier"])
    return base_bet * float(CFG["bet_modes"]["buy_feature"]["cost_multiplier"])


def bet_tier_name(bet_tier_amount: float, big_amount: float | None = None) -> str:
    """數學模型規範 §1.7.1（2026-10-27）：小 Bet（< $2）看 bet_tier_amount（NB／EB 實際押注、BF／SF 基礎押注）；
    大 Bet（> $100）看基礎押注 big_amount（對齊 SPS isHighBet()）。未給 big_amount 時同 bet_tier_amount。"""
    big_amount = bet_tier_amount if big_amount is None else big_amount
    if bet_tier_amount < 2.0:
        return "small_bet"
    if big_amount <= 100.0:
        return "medium_bet"
    return "big_bet"


def threshold_index(multiplier: float) -> int:
    for index, upper in enumerate(MULTIPLIER_THRESHOLDS):
        if multiplier <= upper:
            return index
    return len(MULTIPLIER_THRESHOLDS) - 1


def _empty_stats() -> dict[str, Any]:
    buckets = len(MULTIPLIER_THRESHOLDS)
    return {
        "rounds": 0, "coin_in": 0.0, "pay_bg": 0.0, "pay_fg": 0.0,
        "win_x_sum": 0.0, "win_x_square": 0.0, "max_win_x": 0.0, "capped_rounds": 0,
        "bg_hit_spins": 0, "fg_hit_spins": 0, "fg_spins": 0, "fg_triggers": 0,
        "retriggers": 0, "cascades_bg": 0, "cascades_fg": 0,
        "special_symbol_cnt": 0, "bg_trigger_fg_cnt": 0, "bg_trigger_fg_pay": 0.0,
        "golden_converted": 0, "bg_gold_symbols": 0, "fg_gold_symbols": 0,
        "bg_gold_appeared": 0, "fg_gold_appeared": 0,
        "bg_flip_spins": 0, "fg_flip_spins": 0, "bg_mult_spins": 0, "fg_mult_spins": 0,
        "bg_big_spins": 0, "fg_big_spins": 0, "bg_big_used_spins": 0, "fg_big_used_spins": 0,
        "bg_gold_seen_spins": 0, "fg_gold_seen_spins": 0,
        "bg_mult_cells": 0, "fg_mult_cells": 0, "bg_mult_left": 0, "fg_mult_left": 0,
        "bg_mult_unused_spins": 0, "fg_mult_unused_spins": 0,
        "bg_gold_reel": Counter(), "fg_gold_reel": Counter(), "bg_gold_boards": 0, "fg_gold_boards": 0,
        "combo_bg": Counter(), "combo_fg": Counter(),
        "bg_symbol_length_pay": Counter(), "fg_symbol_length_pay": Counter(),
        "bg_mult_wild": 0, "fg_mult_wild": 0, "max_line_multiplier": 1,
        "bg_golden_results": Counter(), "fg_golden_results": Counter(),
        "bg_split_counts": Counter(), "fg_split_counts": Counter(),
        "mult_wild_values": Counter(), "bg_mult_kind": Counter(), "fg_mult_kind": Counter(),
        "symbol_hits": Counter(), "symbol_pay": Counter(),
        "bg_symbol_length_hits": Counter(), "fg_symbol_length_hits": Counter(),
        "bg_initial_symbols": Counter(), "bg_drop_symbols": Counter(),
        "fg_initial_symbols": Counter(), "fg_drop_symbols": Counter(),
        "retry_total": 0, "retry_limit_exceeded": 0, "retry_limit_bg_range": 0,
        "retry_limit_bg_freegame": 0, "retry_limit_fg": 0,
        "card_draws": Counter(),
        # Multiplier Line 分桶
        "bucket_bg_cnt": [0] * buckets, "bucket_bg_pay": [0.0] * buckets,
        "bucket_fg_cnt": [0] * buckets, "bucket_fg_pay": [0.0] * buckets,
        "bucket_bf_cnt": [0] * buckets, "bucket_bf_pay": [0.0] * buckets,
        "bucket_trigger_cnt": [0] * buckets, "bucket_trigger_pay": [0.0] * buckets,
        "bucket_fg_hit": [0] * buckets, "bucket_fg_spins": [0] * buckets,
        "bucket_bg_mult": [0] * buckets, "bucket_fg_mult": [0] * buckets,   # 2026-10-21 各區間倍數出現轉數（最終畫面口徑）
        "bucket_bg_combo": [[0] * 5 for _ in range(buckets)],
        "bucket_fg_combo": [[0] * 5 for _ in range(buckets)],
        "bucket_bg_golden": [Counter() for _ in range(buckets)],
        "bucket_fg_golden": [Counter() for _ in range(buckets)],
        "bucket_bg_gold_frames": [0] * buckets,
        "bucket_fg_gold_frames": [0] * buckets,
    }


def _counter(pairs) -> Counter:
    """只放有次數的鍵（同純 Python 版 Counter 只在 += 時產生鍵）。"""
    out = Counter()
    for key, value in pairs:
        if value:
            out[key] = value.item() if hasattr(value, "item") else value
    return out


def arrays_to_stats(arrays, mvals: list[int]) -> dict[str, Any]:
    """Numba 核心回傳的陣列 → 與純 Python 版相同結構的 stats dict（報表程式不必改）。"""
    gi, gf, gs_i, gs_f, bi, bfl, bcombo, bgold, card_draws = arrays
    s = _empty_stats()
    s["rounds"] = int(gi[G_ROUNDS])
    s["coin_in"] = float(gf[H_COIN])
    s["pay_bg"] = float(gf[H_PBG])
    s["pay_fg"] = float(gf[H_PFG])
    s["win_x_sum"] = float(gf[H_WX])
    s["win_x_square"] = float(gf[H_WX2])
    s["max_win_x"] = float(gf[H_MAXWX])
    s["capped_rounds"] = int(gi[G_CAPPED])
    s["fg_triggers"] = int(gi[G_FGTRIG])
    s["bg_trigger_fg_cnt"] = int(gi[G_TRIGCNT])
    s["bg_trigger_fg_pay"] = float(gf[H_TRIGPAY])
    s["retry_total"] = int(gi[G_RETRY])
    s["retry_limit_exceeded"] = int(gi[G_RLE])
    s["retry_limit_bg_range"] = int(gi[G_RLBGR])
    s["retry_limit_bg_freegame"] = int(gi[G_RLBGFG])
    s["retry_limit_fg"] = int(gi[G_RLFG])
    s["fg_spins"] = int(gs_i[1, E_SPINS])
    s["retriggers"] = int(gs_i[1, E_RETRIG])
    s["special_symbol_cnt"] = int(gs_i[0, E_SPECIAL] + gs_i[1, E_SPECIAL])
    s["golden_converted"] = int(gs_i[0, I_GCONV] + gs_i[1, I_GCONV])
    s["max_line_multiplier"] = int(max(1, gs_i[0, I_MAXLM], gs_i[1, I_MAXLM]))
    mwv = Counter()
    sym_hits = Counter()
    sym_pay = Counter()
    for scene, p in ((0, "bg"), (1, "fg")):
        S, F = gs_i[scene], gs_f[scene]
        s[f"cascades_{p}"] = int(S[I_CASC])
        s[f"{p}_hit_spins"] = int(S[E_HIT])
        s[f"{p}_gold_symbols"] = int(S[I_INITGOLD])
        s[f"{p}_gold_appeared"] = int(S[I_GOLDAPP])
        s[f"{p}_flip_spins"] = int(S[E_FLIP])
        s[f"{p}_mult_spins"] = int(S[E_MULTSP])
        s[f"{p}_mult_cells"] = int(S[I_MCELLS])
        s[f"{p}_mult_left"] = int(S[I_MLEFT])
        s[f"{p}_mult_unused_spins"] = int(S[E_MUNUSED])
        s[f"{p}_big_spins"] = int(S[E_BIG])
        s[f"{p}_big_used_spins"] = int(S[E_BIGUSEDSP])
        s[f"{p}_gold_seen_spins"] = int(S[E_GSEEN])
        s[f"{p}_gold_boards"] = int(S[E_GBOARDS])
        s[f"{p}_mult_wild"] = int(S[I_MWC])
        s[f"{p}_gold_reel"] = _counter((r, int(S[O_GREEL + r])) for r in range(5))
        s[f"combo_{p}"] = _counter((k, int(S[E_COMBO + k])) for k in range(6))
        s[f"{p}_golden_results"] = _counter((GOLD_RESULTS[o], int(S[O_GOLDEN + o])) for o in range(2))
        s[f"{p}_split_counts"] = _counter((k, int(S[O_SPLIT + k])) for k in range(SPK))
        s[f"{p}_mult_kind"] = _counter(((KIND_NAMES[kd], mvals[g]), int(S[O_MKIND + kd * MVK + g]))
                                       for kd in range(NKIND) for g in range(len(mvals)))
        s[f"{p}_symbol_length_hits"] = _counter(((sy, ln), int(S[O_LENH + sy * 6 + ln]))
                                                for sy in range(NSYM) for ln in range(6))
        s[f"{p}_symbol_length_pay"] = _counter(((sy, ln), float(F[O_LENPAY + sy * 6 + ln]))
                                               for sy in range(NSYM) for ln in range(6))
        s[f"{p}_initial_symbols"] = _counter(((r, sy), int(S[O_INITS + r * NSYM + sy]))
                                             for r in range(5) for sy in range(NSYM))
        s[f"{p}_drop_symbols"] = _counter(((r, sy), int(S[O_DROPS + r * NSYM + sy]))
                                          for r in range(5) for sy in range(NSYM))
        mwv.update(_counter((mvals[g], int(S[O_MWV + g])) for g in range(len(mvals))))
        sym_hits.update(_counter((sy, int(S[O_SYMH + sy])) for sy in range(NSYM)))
        sym_pay.update(_counter((sy, float(F[O_SYMPAY + sy])) for sy in range(NSYM)))
    s["mult_wild_values"] = mwv
    s["symbol_hits"] = sym_hits
    s["symbol_pay"] = sym_pay
    profile = "newbie" if CARD_PROFILE_NEWBIE else "oldhand"
    s["card_draws"] = _counter(((profile, SEC_NAMES[sec], i), int(card_draws[sec, i]))
                               for sec in range(card_draws.shape[0]) for i in range(card_draws.shape[1]))
    for key, row in (("bucket_bg_cnt", B_BGCNT), ("bucket_fg_cnt", B_FGCNT), ("bucket_bf_cnt", B_BFCNT),
                     ("bucket_trigger_cnt", B_TRIGCNT), ("bucket_fg_hit", B_FGHIT),
                     ("bucket_fg_spins", B_FGSPINS), ("bucket_bg_mult", B_BGMULT),
                     ("bucket_fg_mult", B_FGMULT), ("bucket_bg_gold_frames", B_BGGF),
                     ("bucket_fg_gold_frames", B_FGGF)):
        s[key] = [int(v) for v in bi[row]]
    for key, row in (("bucket_bg_pay", B_BGPAY), ("bucket_fg_pay", B_FGPAY),
                     ("bucket_bf_pay", B_BFPAY), ("bucket_trigger_pay", B_TRIGPAY)):
        s[key] = [float(v) for v in bfl[row]]
    for scene, p in ((0, "bg"), (1, "fg")):
        s[f"bucket_{p}_combo"] = [[int(v) for v in bcombo[scene, b]] for b in range(NBUCKET)]
        s[f"bucket_{p}_golden"] = [_counter((GOLD_RESULTS[o], int(bgold[scene, b, o])) for o in range(2))
                                   for b in range(NBUCKET)]
    return s


def merge_arrays(results):
    """多執行緒結果合併：相加；max_win_x、max_line_multiplier 取大。"""
    merged = [np.array(a, copy=True) for a in results[0]]
    for res in results[1:]:
        for i, a in enumerate(res):
            merged[i] += a
    merged[1][H_MAXWX] = max(r[1][H_MAXWX] for r in results)
    for scene in range(2):
        merged[2][scene, I_MAXLM] = max(r[2][scene, I_MAXLM] for r in results)
    return tuple(merged)


CARD_PROFILE_NEWBIE = False


def _chunk_args(bet_mode: int, base_bet: float, card_enabled: bool, newbie: bool):
    card_on = bool(card_enabled and (CFG_RTP.get("card_system") or {}).get("enabled"))
    data, mvals, _ = build_game_data(CFG, CFG_RTP or None, newbie, card_on)
    max_win, trig_cap = mode_caps(CFG_RTP or None, newbie, card_on, bet_mode)
    wager = wager_for_mode(bet_mode, base_bet)
    return tuple(data), mvals, card_on, max_win, trig_cap, wager


def run_simulation(total_rounds: int, bet_mode: int, base_bet: float, threads: int,
                   card_enabled: bool, newbie: bool) -> dict[str, Any]:
    global CARD_PROFILE_NEWBIE
    CARD_PROFILE_NEWBIE = bool(newbie)
    threads = max(1, min(threads, total_rounds))
    per_thread = [total_rounds // threads] * threads
    for index in range(total_rounds % threads):
        per_thread[index] += 1
    assert sum(per_thread) == total_rounds
    data, mvals, card_on, max_win, trig_cap, wager = _chunk_args(bet_mode, base_bet, card_enabled, newbie)

    # Warm-up（編譯／載入快取，不計時）
    simulate_chunk(data, 50, bet_mode, base_bet, wager, card_on, max_win, trig_cap, RNG_SEED - 1)

    started = time.perf_counter()
    if threads == 1:
        arrays = simulate_chunk(data, total_rounds, bet_mode, base_bet, wager, card_on, max_win, trig_cap, RNG_SEED)
    else:
        # Numba nogil：多執行緒真平行（同 H026／H027）；各執行緒的 np.random 為獨立串流
        with ThreadPoolExecutor(max_workers=threads) as pool:
            futures = [
                pool.submit(simulate_chunk, data, count, bet_mode, base_bet, wager, card_on,
                            max_win, trig_cap, RNG_SEED + index * 7919)
                for index, count in enumerate(per_thread) if count > 0
            ]
            arrays = merge_arrays([future.result() for future in futures])
    duration = time.perf_counter() - started
    return {"stats": arrays_to_stats(arrays, mvals), "duration": duration}


# ===== 報表 / Console =====

def mode_name(mode: int) -> str:
    return {MODE_NORMALBET: "Normal Bet", MODE_EXTRABET: "Extra Bet"}.get(mode, "Buy Feature")


def calculated_metrics(result: dict[str, Any]) -> dict[str, Any]:
    s = result["stats"]
    rounds = max(1, s["rounds"])
    coin_in = max(1e-12, s["coin_in"])
    pay_total = s["pay_bg"] + s["pay_fg"]
    mean = s["win_x_sum"] / rounds
    variance = max(0.0, s["win_x_square"] / rounds - mean * mean)
    fg_triggers = s["fg_triggers"]
    fg_spins = s["fg_spins"]
    special = int(s["special_symbol_cnt"])
    return {
        "rounds": s["rounds"],
        "coin_in_per_round": s["coin_in"] / rounds,
        "rtp_total": pay_total / coin_in,
        "rtp_link": 0.0,
        "rtp_bonus": 0.0,
        "rtp_game": pay_total / coin_in,
        "rtp_bg": s["pay_bg"] / coin_in,
        "rtp_fg": s["pay_fg"] / coin_in,
        "hit_rate_bg": s["bg_hit_spins"] / rounds,
        "hit_rate_fg": s["fg_hit_spins"] / max(1, fg_spins),
        "fg_trigger_rate": fg_triggers / rounds,
        "fg_trigger_cycle": rounds / fg_triggers if fg_triggers else math.inf,
        "retrigger_trigger_rate": s["retriggers"] / max(1, fg_spins),
        "retrigger_trigger_cycle": fg_spins / s["retriggers"] if s["retriggers"] else math.inf,
        "avg_fg_spins": fg_spins / fg_triggers if fg_triggers else 0.0,
        "special_symbol_cnt": special,
        "SCR": special / rounds * 10_000_000_000,
        "max_win_x": s["max_win_x"],
        "capped_rounds": s["capped_rounds"],
        "volatility_std": math.sqrt(variance),
        "standard_error": math.sqrt(variance) / math.sqrt(rounds),
    }


def _trigger_within_cap(s: dict[str, Any], profile: str, section: str) -> tuple[int, float]:
    """自然機率（Card Off）下，BG 觸發 FG 那把得分 ≤ 該 Profile BG Trigger Cap（base_game 卡組最高有權重區間上限）的次數與得分。"""
    cards = (CFG_RTP or {}).get("card_system", {}).get("profiles", {}).get(profile, {}).get(section) or []
    caps = [float(c["max"]) for c in cards if c.get("type") == "range" and float(c.get("weight", 0)) > 0]
    cap = max(caps) if caps else math.inf
    idx = [i for i, upper in enumerate(MULTIPLIER_THRESHOLDS) if upper <= cap]
    return (int(sum(s["bucket_trigger_cnt"][i] for i in idx)), float(sum(s["bucket_trigger_pay"][i] for i in idx)))


def common_summary_sections(result: dict[str, Any]) -> list[list[tuple[str, Any]]]:
    s = result["stats"]
    m = calculated_metrics(result)
    # 2026-10-21：自然機率報表的觸發 FG 那把依新老手 BG Trigger Cap 分開統計（新手上限 ≤ 老手，較多大倍數被擋）
    trigger_rows: list[tuple[str, Any]] = [("bg_trigger_fg_cnt", s["bg_trigger_fg_cnt"]),
                                           ("bg_trigger_fg_pay", s["bg_trigger_fg_pay"])]
    if not result["card_system_enabled"] and result["bet_mode"] != MODE_FEATUREBUY:
        section = "eb_base_game" if result["bet_mode"] == MODE_EXTRABET else "base_game"
        old_cnt, old_pay = _trigger_within_cap(s, "oldhand", section)
        new_cnt, new_pay = _trigger_within_cap(s, "newbie", section)
        trigger_rows = [("bg_trigger_fg_cnt", old_cnt), ("bg_trigger_fg_pay", old_pay),
                        ("bg_trigger_fg_cnt_newbie", new_cnt), ("bg_trigger_fg_pay_newbie", new_pay)]
    sections: list[list[tuple[str, Any]]] = [
        [("game_name", result["game_name"]), ("game_id", result["game_id"])],
        [("config_file", result["config_file"]),
         ("config_rtp_file", result["config_rtp_file"]),
         ("math_version", result["math_version"]),
         ("card_system", "on" if result["card_system_enabled"] else "off")],
        [("bet_mode", mode_name(result["bet_mode"])),
         ("bet_multi", result["bet_multi"]),
         ("feature_price_multiplier", result["feature_price_multiplier"]),
         ("base_bet", result["base_bet"]),
         ("bet_amount", result["bet_amount"]),
         ("bet_tier_amount", result["bet_tier_amount"]),
         ("bet_tier", result["bet_tier"]),
         ("jackpot", result["jackpot"]),
         ("coin_in", m["coin_in_per_round"]),
         ("total_rounds", s["rounds"]),
         ("duration", result["duration"])],
        [("rtp_total", m["rtp_total"]), ("rtp_link", m["rtp_link"]),
         ("rtp_bonus", m["rtp_bonus"]), ("rtp_game", m["rtp_game"]),
         ("rtp_bg", m["rtp_bg"]), ("rtp_fg", m["rtp_fg"]),
         ("hit_rate_bg", m["hit_rate_bg"]), ("hit_rate_fg", m["hit_rate_fg"]),
         ("fg_trigger_rate", (m["fg_trigger_rate"], m["fg_trigger_cycle"])),
         ("retrigger_trigger_rate", (m["retrigger_trigger_rate"], m["retrigger_trigger_cycle"])),
         ("avg_fg_spins", m["avg_fg_spins"])],
        [*trigger_rows,
         ("special_symbol_cnt", m["special_symbol_cnt"]),
         ("SCR", m["SCR"])],
        [("max_win_x", m["max_win_x"]), ("capped_rounds", m["capped_rounds"]),
         ("volatility_std", m["volatility_std"]), ("standard_error", m["standard_error"])],
    ]
    if result["card_system_enabled"]:
        sections.extend([
            [("card_system_profile", result["card_system_profile"]),
             ("card_retry_limit", CARD_RETRY_LIMIT),
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
    rounds = max(1, s["rounds"])
    fg_spins = max(1, s["fg_spins"])
    golden_total = max(1, sum(s["bg_golden_results"].values()) + sum(s["fg_golden_results"].values()))
    rows: list[tuple[str, Any]] = [
        ("avg_cascades_bg", s["cascades_bg"] / rounds),
        ("avg_cascades_fg", s["cascades_fg"] / fg_spins),
        ("mult_left_rate_bg", s["bg_mult_left"] / max(1, s["bg_mult_cells"])),
        ("mult_left_rate_fg", s["fg_mult_left"] / max(1, s["fg_mult_cells"])),
        ("mult_unused_spin_rate_bg", s["bg_mult_unused_spins"] / max(1, s["bg_mult_spins"])),
        ("mult_unused_spin_rate_fg", s["fg_mult_unused_spins"] / max(1, s["fg_mult_spins"])),
        ("avg_gold_frames_bg", s["bg_gold_symbols"] / rounds),
        ("avg_gold_frames_fg", s["fg_gold_symbols"] / fg_spins),
        ("golden_converted", s["golden_converted"]),
    ]
    # 2026-10-21 By Game 關注指標（每轉；BG＝每局 BG 轉、FG＝每 FG 轉）：出現率＝出現的轉 ÷ 總轉數；使用率＝有用到的轉 ÷ 出現的轉
    for scene, spins in (("bg", rounds), ("fg", fg_spins)):
        rows.extend([
            (f"mult_seen_rate_{scene}", s[f"{scene}_mult_spins"] / spins),
            (f"mult_used_rate_{scene}", 1 - s[f"{scene}_mult_unused_spins"] / max(1, s[f"{scene}_mult_spins"])),
            (f"big_seen_rate_{scene}", s[f"{scene}_big_spins"] / spins),
            (f"big_used_rate_{scene}", s[f"{scene}_big_used_spins"] / max(1, s[f"{scene}_big_spins"])),
            (f"gold_seen_rate_{scene}", s[f"{scene}_gold_seen_spins"] / spins),
            (f"gold_used_rate_{scene}", s[f"{scene}_flip_spins"] / max(1, s[f"{scene}_gold_seen_spins"])),
        ])
    for key in GOLD_RESULTS:
        count = s["bg_golden_results"][key] + s["fg_golden_results"][key]
        rows.append((f"golden_result_{key}_share", count / golden_total))
    rows.extend([
        ("mult_wild_bg_rate", s["bg_mult_wild"] / rounds),
        ("mult_wild_fg_rate", s["fg_mult_wild"] / fg_spins),
        ("max_line_multiplier", s["max_line_multiplier"]),
    ])
    for value in sorted(s["mult_wild_values"]):
        total = max(1, sum(s["mult_wild_values"].values()))
        rows.append((f"mult_wild_x{value}_share", s["mult_wild_values"][value] / total))
    for scene in ("bg", "fg"):
        for kind, value in sorted(s[f"{scene}_mult_kind"]):
            rows.append((f"mult_{scene}_{kind}_x{value}", s[f"{scene}_mult_kind"][(kind, value)]))
    for count in sorted(k for k in set(s["bg_split_counts"]) | set(s["fg_split_counts"]) if k):
        rows.append((f"split_{count}_bg_rate", s["bg_split_counts"][count] / rounds))
        rows.append((f"split_{count}_fg_rate", s["fg_split_counts"][count] / fg_spins))
    return rows


COUNT_KEYS = {
    "total_rounds", "bg_trigger_fg_cnt", "bg_trigger_fg_cnt_newbie", "special_symbol_cnt", "SCR", "retry_total",
    "retry_limit_exceeded", "retry_limit_bg_range", "retry_limit_bg_freegame",
    "retry_limit_fg", "golden_converted", "capped_rounds", "max_line_multiplier",
}


def _display_value(key: str, value: Any) -> str:
    if key == "duration":
        return f"{float(value):05.2f} sec"
    if key in COUNT_KEYS:
        return f"{int(value):,}"
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
    if key.startswith("rtp_") or key in {"hit_rate_bg", "hit_rate_fg"} or key.endswith("_share"):
        return f"{float(value):.4%}"
    if key.endswith("_rate"):
        return f"{float(value):.6%}"
    if key == "avg_fg_spins":
        return f"{float(value):.2f} spins"
    if key == "max_win_x":
        return f"{float(value):,.2f} x"
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
            print(f"{key:<28}{_display_value(key, value)}")
        print()
    print("<< By Game Info >>")
    for key, value in game_info_rows(result):
        print(f"{key:<28}{_display_value(key, value)}")
    print()


def multiplier_line_frame(result: dict[str, Any]) -> pd.DataFrame:
    s = result["stats"]
    rows = []
    trigger_cnt_cum = 0
    trigger_pay_cum = 0.0
    has_bf = result["bet_mode"] == MODE_FEATUREBUY
    for index, upper in enumerate(MULTIPLIER_THRESHOLDS):
        if index == 0:
            interval = "0"
        else:
            interval = f"{float(MULTIPLIER_THRESHOLDS[index - 1]):.1f} < X <= {float(upper):.1f}"
        trigger_cnt_cum += s["bucket_trigger_cnt"][index]
        trigger_pay_cum += s["bucket_trigger_pay"][index]
        row: dict[str, Any] = {
            "Interval": interval,
            "base_game_cnt": s["bucket_bg_cnt"][index],
            "base_game_pay": s["bucket_bg_pay"][index],
            "free_game_cnt": s["bucket_fg_cnt"][index],
            "free_game_pay": s["bucket_fg_pay"][index],
        }
        if has_bf:
            row["free_game_cnt_BF"] = s["bucket_bf_cnt"][index]
            row["free_game_pay_BF"] = s["bucket_bf_pay"][index]
        row["Interval_Upper"] = upper
        row["bg_trigger_fg_cnt_lte_upper"] = trigger_cnt_cum
        row["bg_trigger_fg_pay_lte_upper"] = trigger_pay_cum
        fg_spins = s["bucket_fg_spins"][index]
        row["FG_Hit_Rate"] = s["bucket_fg_hit"][index] / fg_spins if fg_spins else 0.0
        row["FG_Spin_Count"] = fg_spins
        # 各區間倍數出現率（同 Demogame：最後一次翻牌沒再連線改無倍數小鬼，看最終畫面）：BG＝該區間 BG 局數、FG＝該區間 FG 場的總轉數
        row["BG_Mult_Seen_Rate"] = s["bucket_bg_mult"][index] / s["bucket_bg_cnt"][index] if s["bucket_bg_cnt"][index] else 0.0
        row["FG_Mult_Seen_Rate"] = s["bucket_fg_mult"][index] / fg_spins if fg_spins else 0.0

        bg_combo_total = max(1, sum(s["bucket_bg_combo"][index]))
        for combo in range(5):
            label = f"BG_Combo_{combo + 1}{'+' if combo == 4 else ''}_Rate"
            row[label] = s["bucket_bg_combo"][index][combo] / bg_combo_total
        fg_combo_total = max(1, sum(s["bucket_fg_combo"][index]))
        for combo in range(5):
            label = f"FG_Combo_{combo + 1}{'+' if combo == 4 else ''}_Rate"
            row[label] = s["bucket_fg_combo"][index][combo] / fg_combo_total

        # --- By Game ---
        bg_gold = s["bucket_bg_golden"][index]
        bg_gold_total = max(1, sum(bg_gold.values()))
        for key in GOLD_RESULTS:
            row[f"BG_Golden_{key}_Rate"] = bg_gold[key] / bg_gold_total
        fg_gold = s["bucket_fg_golden"][index]
        fg_gold_total = max(1, sum(fg_gold.values()))
        for key in GOLD_RESULTS:
            row[f"FG_Golden_{key}_Rate"] = fg_gold[key] / fg_gold_total
        bg_cnt = max(1, s["bucket_bg_cnt"][index])
        row["BG_Avg_Gold_Frames"] = s["bucket_bg_gold_frames"][index] / bg_cnt
        row["FG_Avg_Gold_Frames"] = s["bucket_fg_gold_frames"][index] / max(1, fg_spins)
        rows.append(row)
    return pd.DataFrame(rows)


def symbol_frame(result: dict[str, Any]) -> pd.DataFrame:
    s = result["stats"]
    names = CFG["symbol_names"]
    total_hits = max(1, sum(s["symbol_hits"].values()))
    total_pay = max(1e-12, sum(s["symbol_pay"].values()))
    rows = []
    for symbol in SCORE_SYMBOLS:
        rows.append({
            "symbol_id": symbol,
            "symbol": names[str(symbol)],
            "ways_hits": s["symbol_hits"][symbol],
            "hit_share": s["symbol_hits"][symbol] / total_hits,
            "pay": s["symbol_pay"][symbol],
            "pay_share": s["symbol_pay"][symbol] / total_pay,
            "hits_3": s["bg_symbol_length_hits"][(symbol, 3)] + s["fg_symbol_length_hits"][(symbol, 3)],
            "hits_4": s["bg_symbol_length_hits"][(symbol, 4)] + s["fg_symbol_length_hits"][(symbol, 4)],
            "hits_5": s["bg_symbol_length_hits"][(symbol, 5)] + s["fg_symbol_length_hits"][(symbol, 5)],
        })
    return pd.DataFrame(rows)


def feature_frame(result: dict[str, Any]) -> pd.DataFrame:
    s = result["stats"]
    rounds = max(1, s["rounds"])
    fg_spins = max(1, s["fg_spins"])
    rows = [
        ("golden_converted_total", s["golden_converted"]),
        ("golden_per_round", s["golden_converted"] / rounds),
        ("flip_spins_bg", s["bg_flip_spins"]), ("flip_spins_fg", s["fg_flip_spins"]),
        ("mult_spins_bg", s["bg_mult_spins"]), ("mult_spins_fg", s["fg_mult_spins"]),
        ("mult_cells_bg", s["bg_mult_cells"]), ("mult_cells_fg", s["fg_mult_cells"]),
        ("mult_left_bg", s["bg_mult_left"]), ("mult_left_fg", s["fg_mult_left"]),
        ("mult_unused_spins_bg", s["bg_mult_unused_spins"]), ("mult_unused_spins_fg", s["fg_mult_unused_spins"]),
        ("mult_left_rate_bg", s["bg_mult_left"] / max(1, s["bg_mult_cells"])),
        ("mult_left_rate_fg", s["fg_mult_left"] / max(1, s["fg_mult_cells"])),
        ("mult_unused_spin_rate_bg", s["bg_mult_unused_spins"] / max(1, s["bg_mult_spins"])),
        ("mult_unused_spin_rate_fg", s["fg_mult_unused_spins"] / max(1, s["fg_mult_spins"])),
        ("gold_board_rate_bg", s["bg_gold_boards"] / rounds),
        ("gold_board_rate_fg", s["fg_gold_boards"] / fg_spins),
        *[(f"gold_reel_bg_R{reel + 1}", s["bg_gold_reel"][reel] / rounds / 4) for reel in range(5)],
        *[(f"gold_reel_fg_R{reel + 1}", s["fg_gold_reel"][reel] / fg_spins / 4) for reel in range(5)],
        ("gold_appeared_bg", s["bg_gold_appeared"]),
        ("gold_appeared_fg", s["fg_gold_appeared"]),
        ("gold_usage_bg", sum(s["bg_golden_results"].values()) / max(1, s["bg_gold_appeared"])),
        ("gold_usage_fg", sum(s["fg_golden_results"].values()) / max(1, s["fg_gold_appeared"])),
        ("mult_wild_created_bg", s["bg_mult_wild"]),
        ("mult_wild_created_fg", s["fg_mult_wild"]),
        ("mult_wild_per_round", (s["bg_mult_wild"] + s["fg_mult_wild"]) / rounds),
        ("max_line_multiplier", s["max_line_multiplier"]),
        ("max_win_x", s["max_win_x"]),
        ("capped_rounds", s["capped_rounds"]),
        ("avg_cascades_bg", s["cascades_bg"] / rounds),
        ("avg_cascades_fg", s["cascades_fg"] / fg_spins),
    ]
    for key in GOLD_RESULTS:
        rows.append((f"golden_{key}_bg", s["bg_golden_results"][key]))
        rows.append((f"golden_{key}_fg", s["fg_golden_results"][key]))
    for value in sorted(s["mult_wild_values"]):
        rows.append((f"mult_wild_x{value}", s["mult_wild_values"][value]))
    for count in sorted(k for k in set(s["bg_split_counts"]) | set(s["fg_split_counts"])):
        rows.append((f"split_{count}_bg", s["bg_split_counts"][count]))
        rows.append((f"split_{count}_fg", s["fg_split_counts"][count]))
    return pd.DataFrame(rows, columns=["Index", "Value"])


# ===== 報表檔名 =====

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
    stamp = (timestamp or datetime.now()).strftime("%y%m%d%H%M")
    rounds_tag = format_rounds_tag(result["stats"]["rounds"])
    bet_mode = result["bet_mode"]
    if not result["card_system_enabled"]:
        game_id = f"{CFG['parsheet_id']}"
        version_tag = format_base_version_tag(CFG["excel_version"])
        return f"{game_id}_{version_tag}_{stamp}_betmode{bet_mode}_{rounds_tag}.xlsx"
    rtp_game_id = str(CFG_RTP.get("parsheet_id") or CFG_RTP.get("game_id"))
    version_tag = format_rtp_version_tag(CFG_RTP["excel_version"])
    rtp_tag = format_rtp_tag(calculated_metrics(result)["rtp_total"])
    profile = result["card_system_profile"]
    parts = [rtp_game_id, version_tag, stamp, f"betmode{bet_mode}", rounds_tag, rtp_tag, profile]
    if profile == "oldhand":
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


def eliminate_frame(result: dict[str, Any]) -> pd.DataFrame:
    """消除次數分布（同 H016 報表 Eliminate 頁）：BG 每局、FG 每次免費轉。"""
    s = result["stats"]
    rows = [(("5+" if k == 5 else str(k)), s["combo_bg"].get(k, 0), s["combo_fg"].get(k, 0)) for k in range(6)]
    return pd.DataFrame(rows, columns=["combo", "BG", "FG"])


def symbol_length_frame(result: dict[str, Any]) -> pd.DataFrame:
    """各符號 3／4／5 連線命中數與派彩（同 H016 報表 Symbol Length 頁）。"""
    s = result["stats"]
    names = CFG["symbol_names"]
    rows = []
    for scene, hits_key, pay_key in (("BG", "bg_symbol_length_hits", "bg_symbol_length_pay"),
                                     ("FG", "fg_symbol_length_hits", "fg_symbol_length_pay")):
        for symbol in SCORE_SYMBOLS:
            for length in (3, 4, 5):
                rows.append((scene, names[str(symbol)], length,
                             s[hits_key][(symbol, length)], s[pay_key][(symbol, length)]))
    return pd.DataFrame(rows, columns=["scene", "symbol", "length", "hits", "pay"])


# ===== Runner =====

def build_result(stats_bundle: dict[str, Any], combo: dict[str, Any]) -> dict[str, Any]:
    bet_mode = int(combo["bet_mode"])
    base_bet = float(combo["base_bet"])
    bet_amount = wager_for_mode(bet_mode, base_bet)
    if bet_mode == MODE_FEATUREBUY:
        price = float(CFG["bet_modes"]["buy_feature"]["cost_multiplier"])
        bet_tier_amount = bet_amount / price
        feature_price = price
    else:
        bet_tier_amount = bet_amount
        feature_price = "n/a"
    jackpot_on = bool((CFG.get("jackpot") or {}).get("enabled"))
    return {
        "stats": stats_bundle["stats"],
        "duration": stats_bundle["duration"],
        "game_name": CFG["name_zh"],
        "game_id": CFG["online_game_id"],
        "parsheet_id": CFG["parsheet_id"],
        "config_file": combo["config_file"],
        "config_rtp_file": combo["config_rtp_file"] if CFG_RTP else f"{combo['config_rtp_file']} (not found)",
        "math_version": CFG_RTP.get("excel_version", CFG["excel_version"]),
        "card_system_enabled": bool(combo["card_system_enabled"]) and bool(CFG_RTP),
        "card_system_profile": "newbie" if combo["card_system_is_newbie"] else "oldhand",
        "bet_mode": bet_mode,
        "bet_multi": int(round(bet_amount / base_bet)),
        "feature_price_multiplier": feature_price,
        "base_bet": base_bet,
        "bet_amount": bet_amount,
        "bet_tier_amount": bet_tier_amount,
        "bet_tier": bet_tier_name(bet_tier_amount, base_bet),
        "jackpot": "on" if jackpot_on else "off",
    }


def load_batch_configs(combo: dict[str, Any]) -> None:
    global CFG, CFG_RTP
    CFG = load_js_config(BASE_DIR / combo["config_file"])
    if str(combo.get("config_rtp_file", "AUTO")).upper() == "AUTO":
        mode, base_bet = int(combo["bet_mode"]), float(combo["base_bet"])
        tier_amount = base_bet if mode == MODE_FEATUREBUY else wager_for_mode(mode, base_bet)
        tpl = NEWBIE_CONFIG if combo.get("card_system_is_newbie") else TIER_CONFIG[bet_tier_name(tier_amount, base_bet)]
        combo["config_rtp_file"] = tpl.format(s=RTP_SERIES)
        print(f"[auto] bet_mode {mode}、base_bet {base_bet:g}（檔位金額 ${tier_amount:g}）→ {combo['config_rtp_file']}")
    rtp_path = BASE_DIR / combo["config_rtp_file"]
    CFG_RTP = load_js_config(rtp_path) if rtp_path.exists() else {}
    validate_config_pair(CFG, CFG_RTP or None, combo["config_file"], combo["config_rtp_file"])
    if not CFG_RTP and combo["card_system_enabled"]:
        print(f"[warn] 找不到 {combo['config_rtp_file']}，本批改以 Card System Off 執行。")


def validate_batch_run(combo: dict[str, Any]) -> dict[str, Any]:
    required = {"config_file", "config_rtp_file", "bet_mode", "total_rounds",
                "card_system_enabled", "card_system_is_newbie", "base_bet"}
    missing = required - set(combo)
    if missing:
        raise ValueError(f"BATCH_RUNS 缺少必要欄位：{sorted(missing)}")
    if int(combo["bet_mode"]) not in SUPPORTED_BET_MODES:
        raise ValueError(f"不支援的 bet_mode {combo['bet_mode']}；本作只有 0 / 2")
    if int(combo["total_rounds"]) <= 0:
        raise ValueError("total_rounds 必須為正整數")
    if float(combo["base_bet"]) <= 0:
        raise ValueError("base_bet 必須大於 0")
    return combo


def format_board(symbols: list[list[int]], mults: list[list[int]] | None = None) -> str:
    names = CFG["symbol_names"]
    lines = []
    for row in range(4):
        cells = []
        for reel in range(5):
            text = names[str(symbols[reel][row])]
            if mults and mults[reel][row]:
                text += f"x{mults[reel][row]}"
            cells.append(f"{text:>7}")
        lines.append(" ".join(cells))
    return "\n".join(lines)


def run_single_spin_debug() -> None:
    """逐局除錯：每局以獨立種子跑 1 局並印出主要結果（Numba 版不保留盤面物件）。"""
    data, mvals, card_on, max_win, trig_cap, wager = _chunk_args(MODE_NORMALBET, 1.0, False, False)
    for index in range(DEBUG_ROUNDS):
        arrays = simulate_chunk(data, 1, MODE_NORMALBET, 1.0, wager, False, max_win, trig_cap, RNG_SEED + index)
        s = arrays_to_stats(arrays, mvals)
        print(f"--- debug round {index + 1} ---")
        print(f"pay_bg={s['pay_bg']:.4f} pay_fg={s['pay_fg']:.4f} "
              f"cascades_bg={s['cascades_bg']} fg_spins={s['fg_spins']} "
              f"golden={s['golden_converted']} mult_wild={s['bg_mult_wild'] + s['fg_mult_wild']} "
              f"max_line_mult={s['max_line_multiplier']} capped={bool(s['capped_rounds'])}")


def run_batch(combo: dict[str, Any], index: int, total: int) -> None:
    validate_batch_run(combo)
    load_batch_configs(combo)
    print(f"=== Batch {index}/{total}: {combo} ===")
    card_enabled = bool(combo["card_system_enabled"]) and bool(CFG_RTP)
    bundle = run_simulation(int(combo["total_rounds"]), int(combo["bet_mode"]),
                            float(combo["base_bet"]), THREADS,
                            card_enabled, bool(combo["card_system_is_newbie"]))
    result = build_result(bundle, combo)
    if SHOW_CONSOLE_SUMMARY:
        print_console(result)
    if OUTPUT_REPORT:
        path = output_report(result)
        print(f"report -> {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="H045 超級鑽石 simulator")
    parser.add_argument("--rounds", type=int, default=None)
    parser.add_argument("--bet-mode", type=int, default=None)
    parser.add_argument("--base-bet", type=float, default=None)
    parser.add_argument("--threads", type=int, default=None)
    parser.add_argument("--no-report", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--card-on", action="store_true", help="Card System On（需 config_rtp_file）")
    parser.add_argument("--card-off", action="store_true", help="Card System Off")
    parser.add_argument("--newbie", action="store_true", help="Profile 改為 Newbie")
    parser.add_argument("--config-rtp", default=None, help="覆寫 config_rtp_file，例如 config_92A.js")
    parser.add_argument("--config", default=None, help="覆寫 config_file（調參試驗用）")
    parser.add_argument("--seed", type=int, default=None, help="覆寫 RNG_SEED（複驗用不同種子）")
    parser.add_argument("--series", choices=["A", "B"], default=None, help="AUTO 選組用 A／B 版")
    return parser.parse_args()


def main() -> None:
    global RNG_SEED, RTP_SERIES
    global THREADS, OUTPUT_REPORT
    args = parse_args()
    if args.seed is not None:
        RNG_SEED = args.seed
    if args.series:
        RTP_SERIES = args.series
    if args.threads:
        THREADS = max(1, args.threads)
    if args.no_report:
        OUTPUT_REPORT = False

    runs = [dict(run) for run in BATCH_RUNS] if RUN_ALL_COMBINATIONS else [{
        "config_file": CONFIG_FILE, "config_rtp_file": CONFIG_RTP_FILE,
        "bet_mode": BET_MODE, "total_rounds": TOTAL_ROUNDS,
        "card_system_enabled": CARD_SYSTEM_ENABLED,
        "card_system_is_newbie": CARD_SYSTEM_IS_NEWBIE,
        "base_bet": BASE_BET_SETTING,
    }]
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
        if args.config_rtp:
            run["config_rtp_file"] = args.config_rtp
        if args.config:
            run["config_file"] = args.config

    if args.debug or RUN_SINGLE_SPIN_DEBUG:
        load_batch_configs(runs[0])
        run_single_spin_debug()
        return

    for index, run in enumerate(runs, start=1):
        run_batch(run, index, len(runs))


if __name__ == "__main__":
    main()
