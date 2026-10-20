"""H020 超級寶石 (Super Gems) simulator.

盤面：R1～R3 為 3×3、5 條固定線（只有 3 連線得分）＋ R4 特色轉輪（1X～500X 倍數／重轉球）。
玩法定義見 ``game_rule.md``；執行參數一律來自 Config，不在本程式內重複維護輪帶或權重。

- ``config.js``：自然機率（R1～R3 輪帶與權重、賠率、5 線、各押注模式的 R4／重轉次數／重轉倍數權重）。
- ``config_92A.js``／``config_94A.js``／``config_96A.js``：Reskin 92／94／96 版的卡片系統（Oldhand、Newbie 各含 NB／EB1／EB2／SF）。
- 押注模式：0 Normal Bet（1x）、1 Extra Bet 1（1.5x）、2 Extra Bet 2（8x）、3 Super Feature（250x，5 次 Spin）。
- 卡片區間與 Multiplier Line 的倍率分母都是 Normal Bet 押注（贏分 ÷ base_bet），EB／SF 不除成本倍數；
  RTP、volatility_std 以實際成本計。
- Reskin 產線：不分押注層級，依版本選 Config（``CONFIG_RTP_FILE = "AUTO"`` → ``config_<RESKIN_VERSION>A.js``，
  batch 可用 ``reskin_version`` 指定 92／94／96）；Newbie、Oldhand 用同一份 Config 內各自的卡片。
  OP 轉製（Reskin 數學模型規範 §3.1.2）：卡片只負責 Game RTP ＝ 版本 − 4%（新手、老手、各模式相同）；
  Bonus（OP Jackpot Minor／Mini）與 Progressive 由系統負責，不在本程式模擬。
- OP Jackpot 不在本程式模擬；``special_symbol_cnt`` 統計 R4 停在重轉球的 Spin 數（OP Jackpot 觸發來源）。

Runner、BATCH_RUNS、Console 欄位與 Excel 報表版面依 ``專案需知/開發需知/模擬程式規範.md``。
"""

from __future__ import annotations

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

RUN_ALL_COMBINATIONS = True
CONFIG_FILE = "config.js"
CONFIG_RTP_FILE = "AUTO"  # AUTO：依 RESKIN_VERSION 選 config_<版本>A.js；也可指定 "config_96A.js"
RESKIN_VERSION = "96"  # Reskin 版本：92／94／96
TOTAL_ROUNDS = 100_000
BASE_BET_SETTING = 2
BET_MODE = 0  # 0 = Normal Bet, 1 = Extra Bet 1, 2 = Extra Bet 2, 3 = Super Feature
CARD_SYSTEM_ENABLED = True

_NB = {"config_file": "config.js", "config_rtp_file": "AUTO", "bet_mode": 0, "card_system_is_newbie": False}
_E1 = dict(_NB, bet_mode=1)
_E2 = dict(_NB, bet_mode=2)
_SF = dict(_NB, bet_mode=3)
_NEW = {"card_system_is_newbie": True}

BATCH_RUNS = [
    # --- 1. 測試：Card System On，10^5（Reskin 96 版，新手／老手）---
    *[dict(m, reskin_version="96", total_rounds=10**5, card_system_enabled=True, base_bet=2) for m in (_NB, _E1, _E2, _SF)],
    *[dict(m, **_NEW, reskin_version="96", total_rounds=10**5, card_system_enabled=True, base_bet=2) for m in (_NB, _E1, _E2, _SF)],
    # --- 2. 自然機率：Card System Off（NB／EB／SF 10^9）---
    # *[dict(m, total_rounds=10**9, card_system_enabled=False, base_bet=2) for m in (_NB, _E1, _E2, _SF)],
    # --- 3. 正式模擬：Card System On，92／94／96 × 新手／老手 × 四模式，各 10^8 ---
    # *[dict(m, **p, reskin_version=v, total_rounds=10**8, card_system_enabled=True, base_bet=2)
    #   for v in ("96", "94", "92") for p in ({}, _NEW) for m in (_NB, _E1, _E2, _SF)],
]
WORKERS = max(1, min(24, os.cpu_count() or 1))
OUTPUT_REPORT = True
CARD_RETRY_LIMIT = 10_000
RNG_SEED = 20_020

SUPPORTED_BET_MODES = (0, 1, 2, 3)
PAY_SCALE = 10  # 賠率含 2.4／1.6／0.4，核心以 ×10 整數計算

MULTIPLIER_THRESHOLDS = (
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50,
    60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 250, 300, 350, 400, 450,
    500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000,
    2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000,
    20000, 30000, 100000, 999999,
)

BASE_DIR = Path(__file__).resolve().parent

# ===== Config =====


def load_js_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    return json.loads(text[text.index("{"):text.rindex("}") + 1])


def validate_config_pair(base: dict[str, Any], rtp: dict[str, Any]) -> None:
    if base.get("game_id") != "H020" or rtp.get("game_id") != "H020":
        raise ValueError("config 的 game_id 必須為 H020")
    bv = str(base.get("excel_version", ""))
    if not bv.isdigit() or len(bv) != 1:
        raise ValueError(f"config.js 的 excel_version 必須為 1 碼，目前為 {bv!r}")
    rv = str(rtp.get("excel_version", ""))
    if len(rv.split(".")) != 4 or rv.split(".")[0] != bv:
        raise ValueError(f"RTP 版本 {rv!r} 必須為四段且第 1 碼等於基礎版本 {bv}")


def bet_tier_of(amount: float) -> str:
    cents = round(amount * 100)
    if cents < 200:
        return "small_bet"
    if cents <= 10_000:
        return "medium_bet"
    return "big_bet"


def resolve_rtp_file(combo: dict[str, Any], tier: str) -> str:
    name = combo["config_rtp_file"]
    if name != "AUTO":
        return name
    return f"config_{combo.get('reskin_version', RESKIN_VERSION)}A.js"  # Reskin 不分押注層級


def _cum(weights: list[int]) -> np.ndarray:
    if any(w < 0 for w in weights):
        raise ValueError("權重不得為負")
    return np.cumsum(np.array(weights, np.int64))


def pack_tables(base: dict[str, Any], rtp: dict[str, Any], bet_mode: int, newbie: bool) -> dict[str, Any]:
    """把 Config 轉成 Numba 核心使用的固定型別陣列。"""
    mode = base["bet_modes"][str(bet_mode)]
    L = max(len(r) for r in base["reels"])
    reel_sym = np.full((3, L), -1, np.int64)
    reel_len = np.zeros(3, np.int64)
    reel_cum = np.zeros((3, L), np.int64)
    for r in range(3):
        reel_len[r] = len(base["reels"][r])
        reel_sym[r, :reel_len[r]] = base["reels"][r]
        c = _cum(mode["reel_weights"][r])
        reel_cum[r, :len(c)] = c
        reel_cum[r, len(c):] = c[-1]
    lines = np.array(base["paylines"], np.int64)
    pay10 = np.array([round(p * PAY_SCALE) for p in base["paytable_3"]], np.int64)
    r4_mult = np.array(base["r4_multipliers"] + [0], np.int64)  # 最後一格 = 重轉球
    r4_cum = _cum(mode["r4_weights"])
    rs_cnt = np.array(base["respin_counts"], np.int64)
    rs_cnt_cum = _cum(mode["respin_count_weights"])
    rs_mul_cum = np.zeros((len(base["respin_counts"]), len(base["r4_multipliers"])), np.int64)
    for j, w in enumerate(mode["respin_multiplier_weights"]):
        if sum(w) > 0:
            rs_mul_cum[j] = _cum(w)
    profile = "newbie" if newbie and str(bet_mode) in rtp["card"]["newbie"] else "oldhand"
    card = rtp["card"][profile][str(bet_mode)]
    card_iv = np.array(card["intervals"], np.int64)
    card_cum = _cum(card["weights"])
    return {
        "arrays": (reel_sym, reel_len, reel_cum, lines, pay10, r4_mult, r4_cum, rs_cnt, rs_cnt_cum,
                   rs_mul_cum, card_iv, card_cum),
        "spins": int(mode["spins"]),
        "card": card,
        "card_profile": profile,
    }


# ===== Numba Core =====

@njit(nogil=True)
def _draw(cum):
    n = cum.shape[0]
    x = np.random.randint(0, cum[n - 1])
    for i in range(n):
        if x < cum[i]:
            return i
    return n - 1


@njit(nogil=True)
def _spin(reel_sym, reel_len, reel_cum, lines, pay10, r4_mult, r4_cum, rs_cnt, rs_cnt_cum, rs_mul_cum, out):
    """單次 Spin。out = [line_pay10, r4_index, respin_n, respin_mult, mult, line_hits]."""
    grid = np.empty((3, 3), np.int64)
    for r in range(3):
        stop = _draw(reel_cum[r, :reel_len[r]])
        for row in range(3):
            grid[row, r] = reel_sym[r, (stop + row) % reel_len[r]]
    line_pay = 0
    hits = 0
    for li in range(lines.shape[0]):
        a = grid[lines[li, 0], 0]
        b = grid[lines[li, 1], 1]
        c = grid[lines[li, 2], 2]
        best = 0
        if a == 0 and b == 0 and c == 0:
            best = pay10[0]
        target = -1
        for s in (a, b, c):
            if s != 0:
                target = s
                break
        if target > 0 and (a == target or a == 0) and (b == target or b == 0) and (c == target or c == 0):
            if pay10[target] > best:
                best = pay10[target]
        if best > 0:
            hits += 1
        line_pay += best
    r4 = _draw(r4_cum)
    mult = r4_mult[r4]
    n = 0
    if r4 == r4_mult.shape[0] - 1:  # 重轉球
        mult = 0
        if line_pay > 0:
            j = _draw(rs_cnt_cum)
            n = rs_cnt[j]
            for _ in range(n):
                mult += r4_mult[_draw(rs_mul_cum[j])]
    out[0] = line_pay
    out[1] = r4
    out[2] = n
    out[3] = mult if n > 0 else 0
    out[4] = mult
    out[5] = hits


@njit(nogil=True)
def _in_interval(win10, card_iv, idx):
    lo = card_iv[idx]
    if lo == -1:
        return win10 == 0
    return lo * 10 < win10 <= card_iv[idx + 1] * 10


@njit(nogil=True)
def run_worker(seed, rounds, spins, card_on, retry_limit, thresholds,
               reel_sym, reel_len, reel_cum, lines, pay10, r4_mult, r4_cum, rs_cnt, rs_cnt_cum, rs_mul_cum,
               card_iv, card_cum):
    np.random.seed(seed)
    n_iv = card_iv.shape[0] - 1
    n_th = thresholds.shape[0]
    n_r4 = r4_mult.shape[0]
    n_rs = rs_cnt.shape[0]
    # 0 win10, 1 hit_rounds, 2 max_win10, 3 line_pay10(未乘倍), 4 hit_spins, 5 special_cnt,
    # 6 retry_total, 7 retry_exceeded, 8 respin_win_spins, 9 respin_mult_sum, 10 total_spins, 11 respin_pay10
    sc = np.zeros(12, np.int64)
    sumsq = np.zeros(1, np.float64)
    r4_win_cnt = np.zeros(n_r4, np.int64)
    r4_win_pay = np.zeros(n_r4, np.int64)
    rs_n_cnt = np.zeros(n_rs, np.int64)
    bucket_cnt = np.zeros(n_th, np.int64)
    bucket_pay = np.zeros(n_th, np.int64)
    card_draw = np.zeros(n_iv, np.int64)
    card_retry = np.zeros(n_iv, np.int64)
    # 依一局總得分的區間：該區間內的轉數、中獎轉數、重轉轉數（SF 一局 5 轉；Multiplier Line 的 FG_Hit_Rate／FG_Spin_Count）
    band_spins = np.zeros(n_th, np.int64)
    band_hits = np.zeros(n_th, np.int64)
    band_respins = np.zeros(n_th, np.int64)
    out = np.zeros(6, np.int64)
    s_r4 = np.zeros(spins, np.int64)
    s_pay = np.zeros(spins, np.int64)
    s_n = np.zeros(spins, np.int64)
    s_mult = np.zeros(spins, np.int64)
    s_line = np.zeros(spins, np.int64)
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
                _spin(reel_sym, reel_len, reel_cum, lines, pay10, r4_mult, r4_cum, rs_cnt, rs_cnt_cum,
                      rs_mul_cum, out)
                s_line[k] = out[0]
                s_r4[k] = out[1]
                s_n[k] = out[2]
                s_mult[k] = out[3]
                if out[0] > 0:
                    if spins > 1:
                        acc += out[4]
                        s_pay[k] = out[0] * acc
                    else:
                        s_pay[k] = out[0] * out[4]
                else:
                    s_pay[k] = 0
                total += s_pay[k]
            if not card_on or _in_interval(total, card_iv, iv):
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
            sc[10] += 1
            sc[3] += s_line[k]
            if s_r4[k] == n_r4 - 1:
                sc[5] += 1
            if s_line[k] > 0:
                sc[4] += 1
                r4_win_cnt[s_r4[k]] += 1
                r4_win_pay[s_r4[k]] += s_pay[k]
                if s_n[k] > 0:
                    sc[8] += 1
                    sc[9] += s_mult[k]
                    sc[11] += s_pay[k]
                    for j in range(n_rs):
                        if rs_cnt[j] == s_n[k]:
                            rs_n_cnt[j] += 1
        m = total / 10.0
        sumsq[0] += m * m
        for h in range(n_th):
            if total <= thresholds[h] * 10:
                bucket_cnt[h] += 1
                bucket_pay[h] += total
                for k in range(spins):
                    band_spins[h] += 1
                    if s_line[k] > 0:
                        band_hits[h] += 1
                        if s_n[k] > 0:
                            band_respins[h] += 1
                break
    return (sc, sumsq, r4_win_cnt, r4_win_pay, rs_n_cnt, bucket_cnt, bucket_pay, card_draw, card_retry,
            band_spins, band_hits, band_respins)


def _worker_entry(args):
    return run_worker(*args)


# ===== Runner =====

def simulate(packed: dict[str, Any], rounds: int, card_on: bool, seed: int) -> tuple[dict[str, Any], float]:
    thresholds = np.array(MULTIPLIER_THRESHOLDS, np.int64)
    common = (packed["spins"], card_on, CARD_RETRY_LIMIT, thresholds, *packed["arrays"])
    workers = max(1, min(WORKERS, rounds))
    per, rem = divmod(rounds, workers)
    parts = [per + (1 if i < rem else 0) for i in range(workers)]
    jobs = [(seed + 1000 * (i + 1), n, *common) for i, n in enumerate(parts) if n]
    with ProcessPoolExecutor(max_workers=len(jobs)) as pool:
        list(pool.map(_worker_entry, [(j[0], 1, *j[2:]) for j in jobs]))  # Warm-up（Numba 編譯不計入 duration）
        start = time.perf_counter()
        results = list(pool.map(_worker_entry, jobs))
        duration = time.perf_counter() - start
    keys = ("sc", "sumsq", "r4_win_cnt", "r4_win_pay", "rs_n_cnt", "bucket_cnt", "bucket_pay",
            "card_draw", "card_retry", "band_spins", "band_hits", "band_respins")
    merged = {k: sum(r[i] for r in results) for i, k in enumerate(keys)}
    merged["sc"][2] = max(int(r[0][2]) for r in results)
    merged["rounds"] = sum(parts)
    assert merged["rounds"] == rounds
    return merged, duration


def build_result(combo: dict[str, Any], base: dict[str, Any], rtp: dict[str, Any], packed: dict[str, Any],
                 stats: dict[str, Any], duration: float, rtp_file: str, tier: str) -> dict[str, Any]:
    bet_mode = int(combo["bet_mode"])
    bet = float(combo["base_bet"])
    cost = float(base["bet_modes"][str(bet_mode)]["cost_multiplier"])
    rounds = stats["rounds"]
    coin_in = rounds * bet * cost
    win = stats["sc"][0] / PAY_SCALE * bet
    mean_m = stats["sc"][0] / PAY_SCALE / rounds / cost
    var = stats["sumsq"][0] / rounds / (cost * cost) - mean_m * mean_m
    card = packed["card"]
    max_iv = max(i for i, w in enumerate(card["weights"]) if w > 0)
    return {
        "combo": combo, "stats": stats, "duration": duration, "bet_mode": bet_mode, "bet": bet, "cost": cost,
        "card_on": bool(combo["card_system_enabled"]), "card_profile": packed["card_profile"],
        "rtp_file": rtp_file, "tier": tier, "card": card, "spins": packed["spins"],
        "game_name": base["name_zh"], "rtp_game_id": rtp["parsheet_id"],
        "base_version": base["excel_version"], "math_version": rtp["excel_version"],
        "bet_mode_name": base["bet_modes"][str(bet_mode)]["name"], "r4_mult": base["r4_multipliers"],
        "respin_counts": base["respin_counts"],
        "coin_in": coin_in, "rtp_total": win / coin_in, "std": math.sqrt(max(var, 0.0)),
        "max_upper": card["intervals"][max_iv + 1],
    }


def _pct(x: float) -> str:
    return f"{x * 100:.4f}%"


def _int(x: Any) -> str:
    return f"{int(x):,}"


def common_rows(res: dict[str, Any]) -> list[list[tuple[str, str]]]:
    st = res["stats"]
    sc = st["sc"]
    rounds = st["rounds"]
    bet, cost = res["bet"], res["cost"]
    is_sf = res["bet_mode"] == 3
    tier_amount = bet if is_sf else bet * cost
    max_bg = f"{res['max_upper'] / cost:g}" if res["card_on"] else "natural"
    sections = [
        [("game_name", res["game_name"]), ("game_id", "H020")],
        [("config_file", res["combo"]["config_file"]), ("config_rtp_file", res["rtp_file"]),
         ("math_version", res["math_version"]), ("card_system", "on" if res["card_on"] else "off")],
        [("bet_mode", res["bet_mode_name"]), ("bet_multi", f"{1 if is_sf else cost:g}"),
         ("feature_price_multiplier", f"{cost:g}" if is_sf else "n/a"),
         ("base_bet", f"{bet:.2f}"), ("bet_amount", f"{bet * cost:.2f}"),
         ("bet_tier_amount", f"{tier_amount:.2f}"), ("bet_tier", res["tier"]),
         ("link_enabled", "false" if res["card_profile"] == "newbie" else "true"),
         ("max_multiplier_bg", "n/a" if is_sf else max_bg), ("max_multiplier_fg", max_bg if is_sf else "n/a"),
         ("coin_in", f"{res['coin_in']:,.2f}"), ("total_rounds", _int(rounds)),
         ("duration", f"{res['duration']:05.2f} sec")],
        [("rtp_total", _pct(res["rtp_total"])), ("rtp_link", "n/a"), ("rtp_bonus", "n/a"),
         ("rtp_game", _pct(res["rtp_total"])),
         ("rtp_bg", "n/a" if is_sf else _pct(res["rtp_total"])), ("rtp_fg", _pct(res["rtp_total"]) if is_sf else "n/a"),
         ("hit_rate_bg", "n/a" if is_sf else _pct(sc[1] / rounds)),
         ("hit_rate_fg", _pct(sc[4] / sc[10]) if is_sf else "n/a")],
        [("special_symbol_cnt", _int(sc[5])), ("SCR", _int(round(sc[5] / rounds * 10_000_000_000)) if rounds else "0")],
        [("volatility_std", f"{res['std']:05.2f}"), ("standard_error", f"{res['std'] / math.sqrt(rounds):.6f}")],
    ]
    if res["card_on"]:
        sections.append([
            ("card_system_profile", res["card_profile"]), ("card_retry_limit", _int(CARD_RETRY_LIMIT)),
            ("retry_total", _int(sc[6])), ("avg_retry", f"{sc[6] / rounds:.2f}"),
            ("retry_limit_exceeded", _int(sc[7])),
        ])
    return sections


def game_info_rows(res: dict[str, Any]) -> list[tuple[str, str]]:
    st = res["stats"]
    sc = st["sc"]
    spins = sc[10]
    coin_in = res["coin_in"]
    hit = max(1, sc[4])
    rows = [("spin_hit_rate", _pct(sc[4] / spins)),
            ("line_rtp_no_multiplier", _pct(sc[3] / PAY_SCALE * res["bet"] / coin_in))]
    names = [f"{m}x" for m in res["r4_mult"]] + ["respin"]
    for i, name in enumerate(names):
        rows.append((f"r4_{name}_on_win_rate", _pct(st["r4_win_cnt"][i] / hit)))
    for i, name in enumerate(names):
        rows.append((f"r4_{name}_rtp", _pct(st["r4_win_pay"][i] / PAY_SCALE * res["bet"] / coin_in)))
    rows += [
        ("respin_trigger_rate", _pct(sc[8] / spins)),
        ("respin_avg_multiplier", f"{sc[9] / max(1, sc[8]):.4f}"),
        ("respin_rtp", _pct(sc[11] / PAY_SCALE * res["bet"] / coin_in)),
    ]
    for j, n in enumerate(res["respin_counts"]):
        rows.append((f"respin_n{n}_rate", _pct(st["rs_n_cnt"][j] / max(1, sc[8]))))
    rows.append(("max_win_x", f"{sc[2] / PAY_SCALE / res['cost']:,.2f} x"))
    return rows


def print_console(res: dict[str, Any]) -> None:
    for section in common_rows(res):
        for k, v in section:
            print(f"{k:<24}: {v}")
        print()
    print("<< By Game Info >>")
    print()
    for k, v in game_info_rows(res):
        print(f"{k:<24}: {v}")
    print()


def multiplier_line_frame(res: dict[str, Any]) -> pd.DataFrame:
    st = res["stats"]
    rows = []
    key_cnt = "free_game_cnt_SF" if res["bet_mode"] == 3 else "base_game_cnt"
    key_pay = "free_game_pay_SF" if res["bet_mode"] == 3 else "base_game_pay"
    for i, upper in enumerate(MULTIPLIER_THRESHOLDS):
        interval = "0" if i == 0 else f"{float(MULTIPLIER_THRESHOLDS[i - 1]):.1f} < X <= {float(upper):.1f}"
        row = {"Interval": interval, key_cnt: int(st["bucket_cnt"][i]),
               key_pay: st["bucket_pay"][i] / PAY_SCALE, "Interval_Upper": upper}
        if res["bet_mode"] == 3:   # SF：該區間（一局 5 轉總得分）內每一轉的中獎率與轉數；By Game：重轉率（每轉）
            spins, hits = int(st["band_spins"][i]), int(st["band_hits"][i])
            row["FG_Hit_Rate"] = hits / spins if spins else 0.0
            row["FG_Spin_Count"] = spins
            row["FG_Respin_Rate"] = int(st["band_respins"][i]) / spins if spins else 0.0
        rows.append(row)
    return pd.DataFrame(rows)


def card_frame(res: dict[str, Any]) -> pd.DataFrame:
    st = res["stats"]
    card = res["card"]
    rounds = st["rounds"]
    total_w = sum(card["weights"])
    rows = []
    for i, w in enumerate(card["weights"]):
        draws = int(st["card_draw"][i])
        rows.append({"Lower": card["intervals"][i], "Upper": card["intervals"][i + 1], "Weight": w,
                     "Setting_Rate": w / total_w, "Actual_Rate": draws / rounds,
                     "Draws": draws, "Avg_Retry": st["card_retry"][i] / draws if draws else 0.0})
    return pd.DataFrame(rows)


def format_rounds_tag(total_rounds: int) -> str:
    exponent = round(math.log10(total_rounds)) if total_rounds > 0 else 0
    return f"10{exponent}" if 10 ** exponent == total_rounds else str(total_rounds)


def format_rtp_version_tag(version: str) -> str:
    out = ""
    for part in str(version).split("."):
        if not part.isdigit() or len(part) > 2:
            raise ValueError(f"版本段位 {part!r} 超過 2 位數，請修正版本後再輸出報表")
        out += part.zfill(2)
    return out


def report_filename(res: dict[str, Any]) -> str:
    stamp = datetime.now().strftime("%y%m%d%H%M")
    rounds_tag = format_rounds_tag(res["stats"]["rounds"])
    if not res["card_on"]:
        return f"H0201_{str(res['base_version']).zfill(2)}_{stamp}_betmode{res['bet_mode']}_{rounds_tag}.xlsx"
    rtp_tag = f"{res['rtp_total'] * 100:.4f}".replace(".", "")[:4]
    tail = res["card_profile"]  # Reskin 不分押注層級
    return (f"{res['rtp_game_id']}_{format_rtp_version_tag(res['math_version'])}_{stamp}_betmode{res['bet_mode']}"
            f"_{rounds_tag}_{rtp_tag}_{tail}.xlsx")


def output_report(res: dict[str, Any]) -> Path:
    directory = BASE_DIR / "Record"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / report_filename(res)
    flat = [row for section in common_rows(res) for row in section] + game_info_rows(res)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(flat, columns=["Index", "Value"]).to_excel(writer, sheet_name="Overview", index=False)
        multiplier_line_frame(res).to_excel(writer, sheet_name="Multiplier Line", index=False)
        if res["card_on"]:
            card_frame(res).to_excel(writer, sheet_name="Card", index=False)
    return path


def validate_batch_run(combo: dict[str, Any]) -> None:
    required = {"config_file", "config_rtp_file", "bet_mode", "total_rounds",
                "card_system_enabled", "card_system_is_newbie", "base_bet"}
    missing = required - set(combo)
    if missing:
        raise ValueError(f"BATCH_RUNS 缺少必要欄位：{sorted(missing)}")
    if int(combo["bet_mode"]) not in SUPPORTED_BET_MODES:
        raise ValueError(f"不支援的 bet_mode {combo['bet_mode']}；本作只有 0／1／2／3")
    if int(combo["total_rounds"]) <= 0:
        raise ValueError("total_rounds 必須為正整數")
    if float(combo["base_bet"]) <= 0:
        raise ValueError("base_bet 必須大於 0")


def run_batch(combo: dict[str, Any], index: int, total: int) -> dict[str, Any]:
    validate_batch_run(combo)
    print(f"=== Batch {index}/{total}: {combo} ===")
    print()
    base = load_js_config(BASE_DIR / combo["config_file"])
    bet_mode = int(combo["bet_mode"])
    cost = float(base["bet_modes"][str(bet_mode)]["cost_multiplier"])
    bet = float(combo["base_bet"])
    tier = bet_tier_of(bet if bet_mode == 3 else bet * cost)
    rtp_file = resolve_rtp_file(combo, tier)
    rtp = load_js_config(BASE_DIR / rtp_file)
    validate_config_pair(base, rtp)
    card_on = bool(combo["card_system_enabled"])
    packed = pack_tables(base, rtp, bet_mode, bool(combo["card_system_is_newbie"]))
    stats, duration = simulate(packed, int(combo["total_rounds"]), card_on, RNG_SEED + index)
    res = build_result(combo, base, rtp, packed, stats, duration, rtp_file, tier)
    print_console(res)
    if OUTPUT_REPORT:
        print(f"report: {output_report(res)}")
        print()
    return res


def main() -> None:
    if RUN_ALL_COMBINATIONS:
        runs = [dict(r) for r in BATCH_RUNS]
    else:
        runs = [{"config_file": CONFIG_FILE, "config_rtp_file": CONFIG_RTP_FILE, "bet_mode": BET_MODE,
                 "total_rounds": TOTAL_ROUNDS, "card_system_enabled": CARD_SYSTEM_ENABLED,
                 "card_system_is_newbie": False, "base_bet": BASE_BET_SETTING}]
    for i, combo in enumerate(runs, 1):
        run_batch(combo, i, len(runs))


if __name__ == "__main__":
    main()
