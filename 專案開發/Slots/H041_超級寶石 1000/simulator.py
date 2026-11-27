"""H041 超級寶石 1000 (Super Gems 1000) simulator.

盤面：R1～R3 為 3×3、5 條固定線（只有 3 連線得分，WW 可替代）＋ R4 特色轉輪（只看中線）。
每把 R4 依押注模式權重抽出一個結果（有線獎用 Normal use、沒線獎用 No win use 權重）：
- 倍數 1X～1000X：線獎合計 × 倍數。
- 重轉（Re-spin）：抽重轉次數 N（2～50），依 N 那一欄的權重抽 N 次倍數相加；抽到 Upgrade（BOOST）不扣次數，
  之後改用 Upgrade-respin 倍數表（同一欄 N）。
- Upgrade-multi（BOOST 倍數）：再依 Upgrade use 權重抽一次 5X～1000X。
- Upgrade-respin（BOOST 重轉）：依 Upgrade-respin 次數與倍數表重轉（不會再抽到 Upgrade）。
本把派彩 ＝ 線獎合計 × 本把倍數（以 Normal Bet 底注計）；沒有線獎時不派彩、不觸發重轉。
押注模式：0 Normal Bet（1x）、1 Extra Bet 1（1.5x）、2 Extra Bet 2（8x）、4 Super Feature（250x，5 次 Spin，
倍數累積：有線獎的 Spin 把本把倍數加進累積倍數，該 Spin 派彩＝線獎 × 累積倍數）。代號依《模擬程式規範》新遊戲規則（SF＝4）。

玩法定義見 ``game_rule.md``；執行參數一律來自 Config，不在本程式內重複維護輪帶、權重、Paytable 或 Feature 參數。
- ``config_01A.js``：產線 01（菲律賓），層級 97A_Bet1（小 Bet <= $1）／97A_Bet2（其餘；本作無大 Bet 檔，> $300 也用 97A_Bet2）；
  Newbie 固定 97A_Bet2；Oldhand Extra Bet 2 底注 > $1500 改用 ``eb2_base_game_over1500`` 卡組；Newbie 無 SF 卡組，SF 用 oldhand。
- 卡片區間與 Multiplier Line 的倍率分母都是 Normal Bet 底注（贏分 ÷ base_bet）；RTP、volatility_std 以實際押注計。
- OP Jackpot 不在本程式模擬（Config 無彩金參數）；``special_symbol_cnt`` 統計 R4 中線出現重轉球（Re-spin／Upgrade-respin）的 Spin 數。

Runner、BATCH_RUNS、Console 欄位與 Excel 報表版面依 ``專案需知/開發規範/模擬程式規範.md``。
2026-11-27 建立（範本 H020／H024；新增 BOOST 與 1000X）。
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numba import njit

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

# ===== User Settings =====

CONFIG_FILE = "config_01A.js"   # 一個產線的一個系列一份 config：config_<產線><系列>.js
CONFIG_TIER = "AUTO"            # AUTO：依押注檔位選層級；也可直接寫層級代號
# 01 檔位對應（2026-11-26 新分級）：小 Bet <= $1 → 97A_Bet1；其餘 → 97A_Bet2（大 Bet > $300 無專屬檔，同 97A_Bet2）
TIER_CODE = {"small_bet": "97{s}_Bet1", "medium_bet": "97{s}_Bet2", "big_bet": "97{s}_Bet2"}
NEWBIE_TIER = "97{s}_Bet2"
EB2_OVER_BET = 1500.0           # Oldhand Extra Bet 2 底注 > 此值改用 eb2_base_game_over1500
TOTAL_ROUNDS = 100_000
BASE_BET_SETTING = 2.0
BET_MODE = 0                    # 0 = Normal Bet, 1 = Extra Bet 1, 2 = Extra Bet 2, 4 = Super Feature
CARD_SYSTEM_ENABLED = True
CARD_SYSTEM_IS_NEWBIE = False
RUN_ALL_COMBINATIONS = True

MODE_NORMALBET = 0
MODE_EXTRABET = 1
MODE_EXTRABET2 = 2
MODE_SUPERFEATURE = 4
SUPPORTED_BET_MODES = (MODE_NORMALBET, MODE_EXTRABET, MODE_EXTRABET2, MODE_SUPERFEATURE)
BUY_MODES = (MODE_SUPERFEATURE,)
MODE_KEY = {0: "normal", 1: "extra_bet", 2: "extra_bet_2", 4: "super_feature"}
CARD_KEY = {0: "base_game", 1: "eb_base_game", 2: "eb2_base_game", 4: "super_feature"}

_NB = {"config_file": "config_01A.js", "tier": "AUTO", "bet_mode": 0, "card_system_enabled": True,
       "card_system_is_newbie": False, "base_bet": 2}
_E1 = dict(_NB, bet_mode=1)
_E2 = dict(_NB, bet_mode=2)
_SF = dict(_NB, bet_mode=4)
_NEW = {"card_system_is_newbie": True}

PRESETS: dict[str, list[dict[str, Any]]] = {
    # --- 1. 測試：Card System On，10^5 ---
    "test": [dict(m, total_rounds=10**5) for m in (_NB, _E1, _E2, _SF)],
    # --- 2. 自然機率：Card System Off（原作工作簿自然分布為 10^8 局）---
    "natural": [dict(m, total_rounds=10**8, card_system_enabled=False) for m in (_NB, _E1, _E2, _SF)],
    # --- 3. 原作卡片驗證（10^6 快速）：97A_Bet1／97A_Bet2 老手四模式＋EB2 底注 > $1500；新手 NB／EB1／EB2 ---
    "card01_quick": [dict(m, tier=t, base_bet=b, total_rounds=10**6) for t, b in (("97A_Bet1", 0.5), ("97A_Bet2", 2))
                     for m in (_NB, _E1, _E2, _SF)]
                    + [dict(_E2, tier="97A_Bet2", base_bet=2000, total_rounds=10**6)]
                    + [dict(m, **_NEW, tier="97A_Bet2", total_rounds=10**6) for m in (_NB, _E1, _E2)],
    # --- 4. 原作卡片驗證（10^7）---
    "card01": [dict(m, tier=t, base_bet=b, total_rounds=10**7) for t, b in (("97A_Bet1", 0.5), ("97A_Bet2", 2))
               for m in (_NB, _E1, _E2, _SF)]
              + [dict(_E2, tier="97A_Bet2", base_bet=2000, total_rounds=10**7)]
              + [dict(m, **_NEW, tier="97A_Bet2", total_rounds=10**7) for m in (_NB, _E1, _E2)],
    # --- 5. 補跑（10^7）：card01 中 2026-11-27 只用本機 10^5 驗的 9 組（97A_Bet1 SF；97A_Bet2 四模式＋EB2 > $1500；新手 NB／EB1／EB2）---
    "card01_rerun": [dict(_SF, tier="97A_Bet1", base_bet=0.5, total_rounds=10**7)]
                    + [dict(m, tier="97A_Bet2", base_bet=2, total_rounds=10**7) for m in (_NB, _E1, _E2, _SF)]
                    + [dict(_E2, tier="97A_Bet2", base_bet=2000, total_rounds=10**7)]
                    + [dict(m, **_NEW, tier="97A_Bet2", total_rounds=10**7) for m in (_NB, _E1, _E2)],
}
BATCH_RUNS = PRESETS["test"]

THREADS = max(1, min(22, os.cpu_count() or 1))   # 模擬機規則：threads ≤ 22（模擬程式規範 §1.5）
OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = True
DEBUG_ROUNDS = 5
CARD_RETRY_LIMIT = 10_000
JACKPOT_ENABLED = False         # Config 無彩金參數，無作用
RNG_SEED = 41_041
COIN_BASE = 100.0
PAY_SCALE = 10                  # 賠率含 2.4／1.6／0.4，核心以 ×10 整數計算

MULTIPLIER_THRESHOLDS = (
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50,
    60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 250, 300, 350, 400, 450,
    500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000,
    2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000,
    20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000, 9999999,
)

N_MULT = 16                     # R4 倍數種類（1X～1000X）
R4_RESPIN, R4_UP_MULTI, R4_UP_RESPIN = N_MULT, N_MULT + 1, N_MULT + 2
BASE_DIR = Path(__file__).resolve().parent

# ===== Config =====


def load_js_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"找不到 {path.name}，請在 H041 專案資料夾執行")
    text = path.read_text(encoding="utf-8")
    return json.loads(text[text.index("{"):text.rindex("}") + 1])


def expand_tier(data: dict[str, Any], tier: str) -> dict[str, Any]:
    """base 疊上 tiers[tier]（淺層覆蓋，source 不疊入），並檢查版本。"""
    if tier not in data["tiers"]:
        raise ValueError(f"{data['config_name']} 沒有層級 {tier}（可用：{', '.join(data['tiers'])}）")
    base = data["base"]
    cfg = {**base, **{k: v for k, v in data["tiers"][tier].items() if k != "source"}}
    bv = str(base.get("excel_version", ""))
    rv = str(cfg.get("excel_version", "")).split(".")
    if not (bv.isdigit() and len(bv) == 1):
        raise ValueError(f"base 的 excel_version 必須為 1 碼，目前為 {bv!r}")
    if len(rv) != 4 or rv[0] != bv:
        raise ValueError(f"層級 {tier} 版本 {cfg.get('excel_version')!r} 必須為四段且第 1 碼等於 {bv}")
    if data.get("game_id") != "H041" or base.get("game_id") != "H041":
        raise ValueError("config 的 game_id 必須為 H041")
    return cfg


def cost_of(base: dict[str, Any], mode: int) -> float:
    return float(base["bet_modes"][MODE_KEY[mode]]["cost_multiplier"])


def tier_amount_of(base: dict[str, Any], mode: int, base_bet: float) -> float:
    """小 Bet 判定金額：NB／EB 為實際押注、SF 為購買價 ÷ 價格倍數（＝底注）。"""
    return base_bet if mode in BUY_MODES else base_bet * cost_of(base, mode)


def bet_tier_name(tier_amount: float, base_bet: float) -> str:
    if round(tier_amount * 100) <= 100:
        return "small_bet"
    if round(base_bet * 100) > 30_000:
        return "big_bet"
    return "medium_bet"


def load_batch_configs(combo: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    data = load_js_config(BASE_DIR / combo["config_file"])
    base = data["base"]
    mode = int(combo["bet_mode"])
    bet = float(combo["base_bet"])
    amount = tier_amount_of(base, mode, bet)
    bt = bet_tier_name(amount, bet)
    tier = combo["tier"]
    if tier == "AUTO":
        tier = (NEWBIE_TIER if combo["card_system_is_newbie"] else TIER_CODE[bt]).format(s=data["series"])
        print(f"[auto] bet_mode {mode}、base_bet {bet:g}（檔位金額 ${amount:g}）→ {tier}")
    return data, expand_tier(data, tier), tier, bt


def _cum(weights: list[int]) -> np.ndarray:
    if any(int(w) < 0 for w in weights):
        raise ValueError("權重不得為負")
    c = np.cumsum(np.array(weights, np.int64))
    return c


def deck_key(mode: int, profile: str, base_bet: float) -> str:
    key = CARD_KEY[mode]
    if mode == MODE_EXTRABET2 and profile == "oldhand" and base_bet > EB2_OVER_BET:
        key = "eb2_base_game_over1500"
    return key


def pack_tables(cfg: dict[str, Any], mode: int, newbie: bool, base_bet: float) -> dict[str, Any]:
    """把 Config 轉成 Numba 核心使用的固定型別陣列。"""
    tbl = cfg["tables"]["bg_1"]
    L = max(len(r) for r in tbl["reels"])
    reel_sym = np.full((3, L), -1, np.int64)
    reel_len = np.zeros(3, np.int64)
    reel_cum = np.zeros((3, L), np.int64)
    for r in range(3):
        reel_len[r] = len(tbl["reels"][r])
        reel_sym[r, :reel_len[r]] = tbl["reels"][r]
        if len(tbl["symbol_weight"][r]) != reel_len[r]:
            raise ValueError(f"symbol_weight[{r}] 長度與輪帶不符")
        c = _cum(tbl["symbol_weight"][r])
        reel_cum[r, :len(c)] = c
        reel_cum[r, len(c):] = c[-1]
    wild = int(cfg["wild_ids"][0])
    lines = np.array(cfg["paylines"], np.int64)
    n_sym = max(int(k) for k in cfg["pays"]) + 1
    pay10 = np.zeros(n_sym, np.int64)
    for k, v in cfg["pays"].items():
        pay10[int(k)] = round(float(v[0]) * PAY_SCALE)
    fr = cfg["feature_reel"][MODE_KEY[mode]]
    r4_mult = np.array(cfg["r4_multipliers"], np.int64)
    if len(r4_mult) != N_MULT:
        raise ValueError(f"r4_multipliers 必須為 {N_MULT} 種")
    for k in ("r4_weights", "r4_no_win_weights"):
        if len(fr[k]) != N_MULT + 3:
            raise ValueError(f"{k} 長度必須為倍數數量 + 3（重轉、BOOST 倍數、BOOST 重轉）")
    if len(fr["r4_upgrade_weights"]) != N_MULT:
        raise ValueError("r4_upgrade_weights 長度必須為倍數數量")
    r4_cum = _cum(fr["r4_weights"])
    nowin_cum = _cum(fr["r4_no_win_weights"])
    upg_cum = _cum(fr["r4_upgrade_weights"])
    rs_cnt = np.array(cfg["respin_counts"], np.int64)
    n_rs = len(rs_cnt)
    rs_cnt_cum = _cum(fr["respin_count_weights"])
    urs_cnt_cum = _cum(fr["upgrade_respin_count_weights"])
    rs_mul_cum = np.zeros((n_rs, N_MULT + 1), np.int64)
    urs_mul_cum = np.zeros((n_rs, N_MULT), np.int64)
    for j in range(n_rs):
        w = fr["respin_multiplier_weights"][j]
        u = fr["upgrade_respin_multiplier_weights"][j]
        if len(w) != N_MULT + 1 or len(u) != N_MULT:
            raise ValueError("重轉倍數權重形狀錯誤")
        if fr["respin_count_weights"][j] > 0 and sum(w) <= 0:
            raise ValueError(f"重轉 N={rs_cnt[j]} 有權重但倍數權重全為 0")
        if sum(w) > 0:
            rs_mul_cum[j] = _cum(w)
        if sum(u) > 0:
            urs_mul_cum[j] = _cum(u)
    profile = "newbie" if newbie else "oldhand"
    profiles = cfg["card_system"]["profiles"]
    if CARD_KEY[mode] not in profiles[profile]:
        profile = "oldhand"   # Newbie 無 SF 卡組 → 用 oldhand（Config newbie_fallback）
    key = deck_key(mode, profile, base_bet)
    deck = profiles[profile][key]
    card_lo = np.array([c["min"] for c in deck], np.int64)
    card_hi = np.array([c["max"] for c in deck], np.int64)
    card_cum = _cum([c["weight"] for c in deck])
    spins = int(cfg["bet_modes"][MODE_KEY[mode]].get("spins", 1))
    return {"arrays": (reel_sym, reel_len, reel_cum, lines, pay10, wild, r4_mult, r4_cum, nowin_cum, upg_cum,
                       rs_cnt, rs_cnt_cum, urs_cnt_cum, rs_mul_cum, urs_mul_cum, card_lo, card_hi, card_cum),
            "deck": deck, "deck_key": key, "card_profile": profile, "spins": spins}


# ===== 遊戲核心 =====

@njit(nogil=True)
def _draw(cum):
    n = cum.shape[0]
    x = np.random.randint(0, cum[n - 1])
    for i in range(n):
        if x < cum[i]:
            return i
    return n - 1


@njit(nogil=True)
def _respin(j, upgraded, r4_mult, rs_cnt, rs_mul_cum, urs_mul_cum, out):
    """重轉 N＝rs_cnt[j] 次，回傳倍數加總；out[0]＝是否中途 Upgrade。"""
    rem = rs_cnt[j]
    total = 0
    up = upgraded
    while rem > 0:
        if up:
            k = _draw(urs_mul_cum[j])
        else:
            k = _draw(rs_mul_cum[j])
            if k == r4_mult.shape[0]:   # Upgrade：不扣次數，之後改用 Upgrade-respin 倍數表
                up = True
                out[0] = 1
                continue
        total += r4_mult[k]
        rem -= 1
    return total


@njit(nogil=True)
def _spin(reel_sym, reel_len, reel_cum, lines, pay10, wild, r4_mult, r4_cum, nowin_cum, upg_cum,
          rs_cnt, rs_cnt_cum, urs_cnt_cum, rs_mul_cum, urs_mul_cum, out, sym_hit, sym_pay, tmp):
    """單次 Spin。out = [line10, r4_idx, mult, respin_n_idx, mid_upgrade, line_hits]。"""
    grid = np.empty((3, 3), np.int64)
    for r in range(3):
        stop = _draw(reel_cum[r, :reel_len[r]])
        for row in range(3):
            grid[row, r] = reel_sym[r, (stop + row) % reel_len[r]]
    for s in range(sym_hit.shape[0]):
        sym_hit[s] = 0
        sym_pay[s] = 0
    line10 = 0
    hits = 0
    for li in range(lines.shape[0]):
        a = grid[lines[li, 0], 0]
        b = grid[lines[li, 1], 1]
        c = grid[lines[li, 2], 2]
        best = 0
        bsym = -1
        if a == wild and b == wild and c == wild:
            best = pay10[wild]
            bsym = wild
        target = -1
        if a != wild:
            target = a
        elif b != wild:
            target = b
        elif c != wild:
            target = c
        if target >= 0 and (a == target or a == wild) and (b == target or b == wild) and (c == target or c == wild):
            if pay10[target] > best:
                best = pay10[target]
                bsym = target
        if best > 0:
            hits += 1
            sym_hit[bsym] += 1
            sym_pay[bsym] += best
        line10 += best
    nm = r4_mult.shape[0]
    mult = 0
    j = -1
    tmp[0] = 0
    if line10 > 0:
        r4 = _draw(r4_cum)
        if r4 < nm:
            mult = r4_mult[r4]
        elif r4 == nm:                 # 重轉
            j = _draw(rs_cnt_cum)
            mult = _respin(j, False, r4_mult, rs_cnt, rs_mul_cum, urs_mul_cum, tmp)
        elif r4 == nm + 1:             # BOOST 倍數
            mult = r4_mult[_draw(upg_cum)]
        else:                          # BOOST 重轉
            j = _draw(urs_cnt_cum)
            mult = _respin(j, True, r4_mult, rs_cnt, rs_mul_cum, urs_mul_cum, tmp)
    else:
        r4 = _draw(nowin_cum)          # 沒有線獎：只決定演出，不派彩、不重轉
    out[0] = line10
    out[1] = r4
    out[2] = mult
    out[3] = j
    out[4] = tmp[0]
    out[5] = hits


@njit(nogil=True)
def _in_card(win10, lo, hi):
    if lo == -1:
        return win10 == 0
    return lo * 10 < win10 <= hi * 10


@njit(nogil=True)
def run_worker(seed, rounds, spins, card_on, retry_limit, thresholds,
               reel_sym, reel_len, reel_cum, lines, pay10, wild, r4_mult, r4_cum, nowin_cum, upg_cum,
               rs_cnt, rs_cnt_cum, urs_cnt_cum, rs_mul_cum, urs_mul_cum, card_lo, card_hi, card_cum, cost):
    np.random.seed(seed)
    n_th = thresholds.shape[0]
    nm = r4_mult.shape[0]
    n_r4 = nm + 3
    n_rs = rs_cnt.shape[0]
    n_card = card_cum.shape[0]
    n_sym = pay10.shape[0]
    # 0 win10, 1 hit_rounds, 2 max_win10, 3 line10_sum, 4 line_hit_spins, 5 special_cnt, 6 retry_total,
    # 7 retry_exceeded, 8 total_spins, 9 mid_upgrade_cnt, 10 mult_sum_respin, 11 mult_sum_up_multi, 12 mult_sum_up_respin
    sc = np.zeros(13, np.int64)
    sumsq = np.zeros(1, np.float64)
    r4_cnt = np.zeros(n_r4, np.int64)          # 中線結果（所有 Spin）
    r4_win_cnt = np.zeros(n_r4, np.int64)      # 有線獎的 Spin
    r4_win_pay = np.zeros(n_r4, np.int64)
    rs_n_cnt = np.zeros(n_rs, np.int64)
    urs_n_cnt = np.zeros(n_rs, np.int64)
    bucket_cnt = np.zeros(n_th, np.int64)
    bucket_pay = np.zeros(n_th, np.int64)
    band_spins = np.zeros(n_th, np.int64)
    band_hits = np.zeros(n_th, np.int64)
    card_draw = np.zeros(n_card, np.int64)
    card_retry = np.zeros(n_card, np.int64)
    sym_hits = np.zeros(n_sym, np.int64)
    sym_pays = np.zeros(n_sym, np.int64)
    sh = np.zeros(n_sym, np.int64)
    sp = np.zeros(n_sym, np.int64)
    s_sh = np.zeros((spins, n_sym), np.int64)
    s_sp = np.zeros((spins, n_sym), np.int64)
    out = np.zeros(6, np.int64)
    tmp = np.zeros(1, np.int64)
    s_line = np.zeros(spins, np.int64)
    s_r4 = np.zeros(spins, np.int64)
    s_mult = np.zeros(spins, np.int64)
    s_j = np.zeros(spins, np.int64)
    s_up = np.zeros(spins, np.int64)
    s_pay = np.zeros(spins, np.int64)
    for _ in range(rounds):
        iv = -1
        if card_on:
            iv = _draw(card_cum)
            card_draw[iv] += 1
        tries = 0
        while True:
            total = 0
            acc = 0
            for k in range(spins):
                _spin(reel_sym, reel_len, reel_cum, lines, pay10, wild, r4_mult, r4_cum, nowin_cum, upg_cum,
                      rs_cnt, rs_cnt_cum, urs_cnt_cum, rs_mul_cum, urs_mul_cum, out, sh, sp, tmp)
                s_line[k] = out[0]
                s_r4[k] = out[1]
                s_mult[k] = out[2]
                s_j[k] = out[3]
                s_up[k] = out[4]
                for s in range(n_sym):
                    s_sh[k, s] = sh[s]
                    s_sp[k, s] = sp[s]
                if out[0] > 0:
                    if spins > 1:      # Super Feature：倍數累積
                        acc += out[2]
                        s_pay[k] = out[0] * acc
                    else:
                        s_pay[k] = out[0] * out[2]
                else:
                    s_pay[k] = 0
                total += s_pay[k]
            if not card_on or _in_card(total, card_lo[iv], card_hi[iv]):
                break
            tries += 1
            if tries >= retry_limit:
                sc[7] += 1
                break
        if card_on:
            sc[6] += tries
            card_retry[iv] += tries
        sc[0] += total
        if total > 0:
            sc[1] += 1
        if total > sc[2]:
            sc[2] = total
        for k in range(spins):
            sc[8] += 1
            sc[3] += s_line[k]
            r4 = s_r4[k]
            r4_cnt[r4] += 1
            if r4 == nm or r4 == nm + 2:
                sc[5] += 1
            if s_line[k] > 0:
                sc[4] += 1
                r4_win_cnt[r4] += 1
                r4_win_pay[r4] += s_pay[k]
                for s in range(n_sym):
                    sym_hits[s] += s_sh[k, s]
                    sym_pays[s] += s_sp[k, s]
                if r4 == nm:
                    rs_n_cnt[s_j[k]] += 1
                    sc[10] += s_mult[k]
                    sc[9] += s_up[k]
                elif r4 == nm + 1:
                    sc[11] += s_mult[k]
                elif r4 == nm + 2:
                    urs_n_cnt[s_j[k]] += 1
                    sc[12] += s_mult[k]
        x = total / 10.0 / cost
        sumsq[0] += x * x
        for h in range(n_th):
            if total <= thresholds[h] * 10:
                bucket_cnt[h] += 1
                bucket_pay[h] += total
                for k in range(spins):
                    band_spins[h] += 1
                    if s_line[k] > 0:
                        band_hits[h] += 1
                break
    return (sc, sumsq, r4_cnt, r4_win_cnt, r4_win_pay, rs_n_cnt, urs_n_cnt, bucket_cnt, bucket_pay,
            band_spins, band_hits, card_draw, card_retry, sym_hits, sym_pays)


RESULT_KEYS = ("sc", "sumsq", "r4_cnt", "r4_win_cnt", "r4_win_pay", "rs_n_cnt", "urs_n_cnt", "bucket_cnt",
               "bucket_pay", "band_spins", "band_hits", "card_draw", "card_retry", "sym_hits", "sym_pays")


def _worker_entry(args):
    return run_worker(*args)


def run_simulation(packed: dict[str, Any], rounds: int, card_on: bool, seed: int, cost: float,
                   threads: int) -> tuple[dict[str, Any], float]:
    thresholds = np.array(MULTIPLIER_THRESHOLDS, np.int64)
    common = (packed["spins"], card_on, CARD_RETRY_LIMIT, thresholds, *packed["arrays"], cost)
    workers = max(1, min(threads, rounds))
    per, rem = divmod(rounds, workers)
    parts = [per + (1 if i < rem else 0) for i in range(workers)]
    jobs = [(seed + 7919 * i, n, *common) for i, n in enumerate(parts) if n]
    with ProcessPoolExecutor(max_workers=len(jobs)) as pool:
        list(pool.map(_worker_entry, [(seed - 1, 1, *common)] * len(jobs)))  # Warm-up（不計入 duration、不併入統計）
        start = time.perf_counter()
        results = list(pool.map(_worker_entry, jobs))
        duration = time.perf_counter() - start
    merged = {k: sum(r[i] for r in results) for i, k in enumerate(RESULT_KEYS)}
    merged["sc"][2] = max(int(r[0][2]) for r in results)
    merged["rounds"] = sum(parts)
    assert merged["rounds"] == rounds
    return merged, duration


# ===== 報表 / Console =====

def calculated_metrics(res: dict[str, Any]) -> dict[str, Any]:
    st = res["stats"]
    sc = st["sc"]
    rounds = st["rounds"]
    cost, bet = res["cost"], res["bet"]
    coin_in = rounds * bet * cost
    win = sc[0] / PAY_SCALE * bet
    mean_x = sc[0] / PAY_SCALE / rounds / cost
    var = st["sumsq"][0] / rounds - mean_x * mean_x
    std = math.sqrt(max(var, 0.0))
    return {"coin_in_total": coin_in, "rtp_game": win / coin_in, "std": std, "se": std / math.sqrt(rounds)}


def _pct(x: float, nd: int = 4) -> str:
    return f"{x * 100:.{nd}f}%"


def _int(x: Any) -> str:
    return f"{int(x):,}"


def common_summary_sections(res: dict[str, Any]) -> list[list[tuple[str, str]]]:
    st = res["stats"]
    sc = st["sc"]
    rounds = st["rounds"]
    m = res["metrics"]
    bet, cost = res["bet"], res["cost"]
    is_sf = res["bet_mode"] in BUY_MODES
    tier_amount = bet if is_sf else bet * cost
    rtp = _pct(m["rtp_game"])
    sections = [
        [("game_name", res["cfg"]["name_zh"]), ("game_id", res["cfg"]["online_game_id"])],
        [("config_file", res["combo"]["config_file"]), ("tier", res["tier"]),
         ("math_version", res["cfg"]["excel_version"] if res["card_on"] else res["cfg_base_version"]),
         ("card_system", "on" if res["card_on"] else "off")],
        [("bet_mode", res["mode_name"]), ("bet_multi", "1" if is_sf else f"{cost:g}"),
         ("feature_price_multiplier", f"{cost:g}" if is_sf else "n/a"),
         ("base_bet", f"{bet:.2f}"), ("bet_amount", f"{bet * cost:.2f}"), ("bet_tier_amount", f"{tier_amount:.2f}"),
         ("bet_tier", res["bet_tier"]), ("jackpot", "off"), ("coin_in", f"{bet * cost:.2f}"),
         ("total_rounds", _int(rounds)), ("duration", f"{res['duration']:05.2f} sec")],
        [("rtp_total", rtp), ("rtp_link", "n/a"), ("rtp_bonus", "n/a"), ("rtp_game", rtp),
         ("rtp_bg", "n/a" if is_sf else rtp), ("rtp_fg", rtp if is_sf else "n/a"),
         ("hit_rate_bg", "n/a" if is_sf else _pct(sc[1] / rounds)),
         ("hit_rate_fg", _pct(sc[4] / max(1, sc[8])) if is_sf else "n/a"),
         ("fg_trigger_rate", "n/a"), ("retrigger_trigger_rate", "n/a"),
         ("avg_fg_spins", f"{sc[8] / rounds:.2f} spins" if is_sf else "n/a")],
        [("bg_trigger_fg_cnt", "n/a"), ("bg_trigger_fg_pay", "n/a"), ("special_symbol_cnt", _int(sc[5])),
         ("SCR", _int(round(sc[5] / rounds * 10_000_000_000)) if rounds else "0")],
        [("max_win_x", f"{sc[2] / PAY_SCALE / cost:,.2f} x"), ("capped_rounds", "0"),
         ("volatility_std", f"{m['std']:05.2f}"), ("volatility_std_fg", f"{m['std']:05.2f}" if is_sf else "n/a"),
         ("standard_error", f"{m['se']:05.2f}")],
    ]
    if res["card_on"]:
        sections.append([("card_system_profile", res["card_profile"]), ("card_deck", res["deck_key"]),
                         ("card_retry_limit", str(CARD_RETRY_LIMIT)),
                         ("retry_total", _int(sc[6])), ("avg_retry", f"{sc[6] / rounds:05.2f}")])
        sections.append([("retry_limit_exceeded", _int(sc[7])),
                         ("retry_limit_bg_range", "0" if is_sf else _int(sc[7])),
                         ("retry_limit_bg_freegame", "0"), ("retry_limit_fg", _int(sc[7]) if is_sf else "0")])
    return sections


def game_info_rows(res: dict[str, Any]) -> list[tuple[str, str]]:
    st = res["stats"]
    sc = st["sc"]
    spins = max(1, sc[8])
    coin = res["metrics"]["coin_in_total"]
    bet = res["bet"]
    cfg = res["cfg"]
    hit = max(1, sc[4])
    nm = N_MULT
    rows = [("line_hit_rate", _pct(sc[4] / spins, 6)),
            ("line_rtp_no_multiplier", _pct(sc[3] / PAY_SCALE * bet / coin, 6))]
    names = [f"{v}x" for v in cfg["r4_multipliers"]] + ["respin", "boost_multi", "boost_respin"]
    for i, n in enumerate(names):
        rows.append((f"r4_{n}_on_win_rate", _pct(st["r4_win_cnt"][i] / hit, 6)))
    for i, n in enumerate(names):
        rows.append((f"r4_{n}_rtp", _pct(st["r4_win_pay"][i] / PAY_SCALE * bet / coin, 6)))
    rows += [
        ("respin_trigger_rate", _pct(st["r4_win_cnt"][nm] / spins, 6)),
        ("respin_avg_multiplier", f"{sc[10] / max(1, st['r4_win_cnt'][nm]):.4f}"),
        ("respin_mid_boost_rate", _pct(sc[9] / max(1, st["r4_win_cnt"][nm]), 6)),
        ("boost_multi_trigger_rate", _pct(st["r4_win_cnt"][nm + 1] / spins, 6)),
        ("boost_multi_avg_multiplier", f"{sc[11] / max(1, st['r4_win_cnt'][nm + 1]):.4f}"),
        ("boost_respin_trigger_rate", _pct(st["r4_win_cnt"][nm + 2] / spins, 6)),
        ("boost_respin_avg_multiplier", f"{sc[12] / max(1, st['r4_win_cnt'][nm + 2]):.4f}"),
    ]
    for j, n in enumerate(cfg["respin_counts"]):
        rows.append((f"respin_n{n}_rate", _pct(st["rs_n_cnt"][j] / max(1, st["r4_win_cnt"][nm]), 6)))
    for j, n in enumerate(cfg["respin_counts"]):
        rows.append((f"boost_respin_n{n}_rate", _pct(st["urs_n_cnt"][j] / max(1, st["r4_win_cnt"][nm + 2]), 6)))
    return rows


def print_console(res: dict[str, Any]) -> None:
    for section in common_summary_sections(res):
        for k, v in section:
            print(f"{k:<28}{v}")
        print()
    print("<< By Game Info >>")
    print()
    for k, v in game_info_rows(res):
        print(f"{k:<28}{v}")
    print()


def overview_rows(res: dict[str, Any]) -> list[tuple[str, str]]:
    return [r for s in common_summary_sections(res) for r in s] + game_info_rows(res)


def multiplier_line_frame(res: dict[str, Any]) -> pd.DataFrame:
    st = res["stats"]
    is_sf = res["bet_mode"] in BUY_MODES
    key_cnt, key_pay = ("free_game_cnt_SF", "free_game_pay_SF") if is_sf else ("base_game_cnt", "base_game_pay")
    rows = []
    for i, upper in enumerate(MULTIPLIER_THRESHOLDS):
        interval = "0" if i == 0 else f"{float(MULTIPLIER_THRESHOLDS[i - 1]):.1f} < X <= {float(upper):.1f}"
        row = {"Interval": interval, key_cnt: int(st["bucket_cnt"][i]),
               key_pay: st["bucket_pay"][i] / PAY_SCALE * res["bet"], "Interval_Upper": upper}
        if is_sf:   # SF：該區間（一局 5 轉總得分）內每一轉的中獎率與轉數
            s, h = int(st["band_spins"][i]), int(st["band_hits"][i])
            row["FG_Hit_Rate"] = h / s if s else 0.0
            row["FG_Spin_Count"] = s
        rows.append(row)
    return pd.DataFrame(rows)


def feature_frame(res: dict[str, Any]) -> pd.DataFrame:
    st = res["stats"]
    cfg = res["cfg"]
    names = [f"{v}x" for v in cfg["r4_multipliers"]] + ["respin", "boost_multi", "boost_respin"]
    rows = [(f"r4_{n}_cnt", int(st["r4_cnt"][i])) for i, n in enumerate(names)]
    rows += [(f"r4_{n}_on_line_win_cnt", int(st["r4_win_cnt"][i])) for i, n in enumerate(names)]
    rows += [(f"respin_n{n}_cnt", int(st["rs_n_cnt"][j])) for j, n in enumerate(cfg["respin_counts"])]
    rows += [(f"boost_respin_n{n}_cnt", int(st["urs_n_cnt"][j])) for j, n in enumerate(cfg["respin_counts"])]
    rows.append(("respin_mid_boost_cnt", int(st["sc"][9])))
    return pd.DataFrame(rows, columns=["Index", "Value"])


def symbol_frame(res: dict[str, Any]) -> pd.DataFrame:
    st = res["stats"]
    names = res["cfg"]["symbol_names"]
    hits = st["sym_hits"]
    pays = st["sym_pays"]
    th, tp = max(1, int(hits.sum())), max(1, int(pays.sum()))
    rows = []
    for s in range(len(hits)):
        rows.append({"symbol_id": s, "symbol": names[str(s)], "ways_hits": int(hits[s]), "hit_share": hits[s] / th,
                     "pay": pays[s] / PAY_SCALE * res["bet"], "pay_share": pays[s] / tp, "hits_3": int(hits[s])})
    return pd.DataFrame(rows)


def symbol_length_frame(res: dict[str, Any]) -> pd.DataFrame:
    st = res["stats"]
    names = res["cfg"]["symbol_names"]
    scene = "FG" if res["bet_mode"] in BUY_MODES else "BG"
    return pd.DataFrame([{"scene": scene, "symbol": names[str(s)], "length": 3, "hits": int(st["sym_hits"][s]),
                          "pay": st["sym_pays"][s] / PAY_SCALE * res["bet"]} for s in range(len(st["sym_hits"]))])


def card_frame(res: dict[str, Any]) -> pd.DataFrame:
    st = res["stats"]
    deck = res["deck"]
    rounds = st["rounds"]
    tw = sum(c["weight"] for c in deck)
    rows = []
    for i, c in enumerate(deck):
        d = int(st["card_draw"][i])
        rows.append({"Lower": c["min"], "Upper": c["max"], "Weight": c["weight"], "Setting_Rate": c["weight"] / tw,
                     "Actual_Rate": d / rounds, "Draws": d, "Avg_Retry": st["card_retry"][i] / d if d else 0.0})
    return pd.DataFrame(rows)


# ===== 報表檔名 =====

def format_rounds_tag(total_rounds: int) -> str:
    e = round(math.log10(total_rounds)) if total_rounds > 0 else 0
    return f"10{e}" if 10 ** e == total_rounds else str(total_rounds)


def format_rtp_version_tag(version: str) -> str:
    out = ""
    for part in str(version).split("."):
        if not part.isdigit() or len(part) > 2:
            raise ValueError(f"版本段位 {part!r} 超過 2 位數，請修正版本後再輸出報表")
        out += part.zfill(2)
    return out


def format_rtp_tag(rtp: float) -> str:
    return f"{rtp * 100:.4f}".replace(".", "")[:4]


def report_filename(res: dict[str, Any]) -> str:
    stamp = datetime.now().strftime("%y%m%d%H%M")
    rt = format_rounds_tag(res["stats"]["rounds"])
    if not res["card_on"]:
        return f"{res['base_parsheet_id']}_{str(res['cfg_base_version']).zfill(2)}_{stamp}_betmode{res['bet_mode']}_{rt}.xlsx"
    gid = res["cfg"]["game_id"] + res["tier"][3:] if res["tier"].startswith("97") else res["cfg"]["game_id"]
    tail = res["card_profile"] if res["card_profile"] == "newbie" else f"oldhand_{res['bet_tier']}"
    return (f"{gid}_{format_rtp_version_tag(res['cfg']['excel_version'])}_{stamp}_betmode{res['bet_mode']}_{rt}_"
            f"{format_rtp_tag(res['metrics']['rtp_game'])}_{tail}_card.xlsx")


def output_report(res: dict[str, Any]) -> Path:
    directory = BASE_DIR / "Record"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / report_filename(res)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(overview_rows(res), columns=["Index", "Value"]).to_excel(writer, sheet_name="Overview", index=False)
        multiplier_line_frame(res).to_excel(writer, sheet_name="Multiplier Line", index=False)
        feature_frame(res).to_excel(writer, sheet_name="Feature", index=False)
        symbol_frame(res).to_excel(writer, sheet_name="Symbol", index=False)
        symbol_length_frame(res).to_excel(writer, sheet_name="Symbol Length", index=False)
        if res["card_on"]:
            card_frame(res).to_excel(writer, sheet_name="Card", index=False)
    return path


# ===== Runner =====

def validate_batch_run(combo: dict[str, Any]) -> None:
    required = {"config_file", "tier", "bet_mode", "total_rounds", "card_system_enabled", "card_system_is_newbie", "base_bet"}
    missing = required - set(combo)
    if missing:
        raise ValueError(f"BATCH_RUNS 缺少必要欄位：{sorted(missing)}")
    if int(combo["bet_mode"]) not in SUPPORTED_BET_MODES:
        raise ValueError(f"不支援的 bet_mode {combo['bet_mode']}；本作只有 0／1／2／4")
    if int(combo["total_rounds"]) <= 0:
        raise ValueError("total_rounds 必須為正整數")
    if float(combo["base_bet"]) <= 0:
        raise ValueError("base_bet 必須大於 0")


def run_batch(combo: dict[str, Any], index: int, total: int, threads: int, seed: int) -> dict[str, Any]:
    validate_batch_run(combo)
    print(f"=== Batch {index}/{total}: {combo} ===")
    print()
    data, cfg, tier, bt = load_batch_configs(combo)
    mode = int(combo["bet_mode"])
    bet = float(combo["base_bet"])
    cost = cost_of(cfg, mode)
    card_on = bool(combo["card_system_enabled"])
    newbie = bool(combo["card_system_is_newbie"]) and card_on
    packed = pack_tables(cfg, mode, newbie, bet)
    stats, duration = run_simulation(packed, int(combo["total_rounds"]), card_on, seed + index, cost, threads)
    res = {"combo": combo, "cfg": cfg, "cfg_base_version": data["base"]["excel_version"],
           "base_parsheet_id": data["base"]["parsheet_id"], "tier": tier if card_on else "base",
           "bet_tier": bt, "bet_mode": mode, "bet": bet, "cost": cost, "card_on": card_on,
           "card_profile": packed["card_profile"], "deck": packed["deck"], "deck_key": packed["deck_key"],
           "mode_name": cfg["bet_modes"][MODE_KEY[mode]]["name"], "stats": stats, "duration": duration}
    res["metrics"] = calculated_metrics(res)
    if SHOW_CONSOLE_SUMMARY:
        print_console(res)
    if OUTPUT_REPORT:
        print(f"report -> {output_report(res)}")
        print()
    return res


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="H041 超級寶石 1000 simulator")
    p.add_argument("--preset", choices=sorted(PRESETS), default=None, help="改跑指定的批次組（預設 BATCH_RUNS）")
    p.add_argument("--rounds", type=int, default=None)
    p.add_argument("--bet-mode", type=int, default=None)
    p.add_argument("--base-bet", type=float, default=None)
    p.add_argument("--threads", type=int, default=None)
    p.add_argument("--no-report", action="store_true")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--card-on", action="store_true")
    p.add_argument("--card-off", action="store_true")
    p.add_argument("--newbie", action="store_true")
    p.add_argument("--tier", default=None, help="覆寫層級，例如 97A_Bet1／97A_Bet2")
    p.add_argument("--config", default=None, help="覆寫 config_file")
    p.add_argument("--seed", type=int, default=None)
    return p.parse_args()


def debug_round(combo: dict[str, Any]) -> None:
    """單執行緒逐局除錯：印出每局得分與 R4 結果。"""
    data, cfg, tier, bt = load_batch_configs(combo)
    mode = int(combo["bet_mode"])
    packed = pack_tables(cfg, mode, bool(combo["card_system_is_newbie"]), float(combo["base_bet"]))
    th = np.array(MULTIPLIER_THRESHOLDS, np.int64)
    cost = cost_of(cfg, mode)
    for k in range(DEBUG_ROUNDS):
        r = run_worker(RNG_SEED + k, 1, packed["spins"], bool(combo["card_system_enabled"]), CARD_RETRY_LIMIT, th,
                       *packed["arrays"], cost)
        print(f"round {k + 1}: win {r[0][0] / PAY_SCALE:g}x base bet, line {r[0][3] / PAY_SCALE:g}x, "
              f"special {int(r[0][5])}, retry {int(r[0][6])}")


def main() -> None:
    global OUTPUT_REPORT
    args = parse_args()
    runs = [dict(r) for r in (PRESETS[args.preset] if args.preset else BATCH_RUNS)] if RUN_ALL_COMBINATIONS else [
        {"config_file": CONFIG_FILE, "tier": CONFIG_TIER, "bet_mode": BET_MODE, "total_rounds": TOTAL_ROUNDS,
         "card_system_enabled": CARD_SYSTEM_ENABLED, "card_system_is_newbie": CARD_SYSTEM_IS_NEWBIE,
         "base_bet": BASE_BET_SETTING}]
    for r in runs:
        if args.rounds:
            r["total_rounds"] = args.rounds
        if args.bet_mode is not None:
            r["bet_mode"] = args.bet_mode
        if args.base_bet:
            r["base_bet"] = args.base_bet
        if args.card_on:
            r["card_system_enabled"] = True
        if args.card_off:
            r["card_system_enabled"] = False
        if args.newbie:
            r["card_system_is_newbie"] = True
        if args.tier:
            r["tier"] = args.tier
        if args.config:
            r["config_file"] = args.config
    if args.no_report:
        OUTPUT_REPORT = False
    if args.debug:
        debug_round(runs[0])
        return
    threads = args.threads or THREADS
    seed = args.seed if args.seed is not None else RNG_SEED
    for i, combo in enumerate(runs, 1):
        run_batch(combo, i, len(runs), threads, seed)


if __name__ == "__main__":
    main()
