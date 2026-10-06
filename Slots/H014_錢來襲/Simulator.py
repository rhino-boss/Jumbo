"""H014 錢來襲 (Money Boost) simulator.

盤面：R1～R3 數字轉輪（中線串接成數字分，單位 Coin）＋ R4 特色轉輪（2X／5X／10X／
RESPIN／綠 BONUS／紅 BONUS／空白）。玩法定義見 ``game_rule.md``；執行參數一律來自 Config，
不在本程式內重複維護輪帶、權重或轉盤獎項。

- ``config.js``：自然機率（各押注 bet{n}p_{A,B,C} 頁的權重輪帶、R4 分組權重、Respin、轉盤）。
- ``config_92A.js``：卡片系統（Card_Bet{n} 頁的倍率區間、使用表、Hit%_Weight_Final）。
- 本作沒有 Newbie／Oldhand 與小／中／大 Bet，卡片權重依押注（1／5／10／50／100）分組；
  報表檔名在 Profile 位置改寫押注，例如 ``_bet100``。
- 0換E、假表演、初始盤面只影響演出，不影響派彩，不在本程式模擬。

Runner、BATCH_RUNS、Console 欄位與 Excel 報表版面依 ``專案需知/模擬程式規範.md``。
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
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
CONFIG_RTP_FILE = "config_92A.js"
TOTAL_ROUNDS = 100_000
BASE_BET_SETTING = 1
BET_MODE = 0  # 0 = Normal Bet, 1 = Extra Bet
CARD_SYSTEM_ENABLED = True
NATURAL_SHEET = "A"  # Card System Off 時使用的表（A／B／C）

_NB = {"config_file": "config.js", "config_rtp_file": "config_92A.js", "bet_mode": 0,
       "card_system_is_newbie": False}
_EB = dict(_NB, bet_mode=1)

BATCH_RUNS = [
    # --- 1. 測試：Card System On，各押注 10^5 ---
    *[dict(_NB, total_rounds=10**5, card_system_enabled=True, base_bet=b) for b in (1, 5, 10, 50, 100)],
    *[dict(_EB, total_rounds=10**5, card_system_enabled=True, base_bet=b) for b in (1, 5, 10, 50, 100)],
    # --- 2. 自然機率：Card System Off（natural_sheet 指定 A／B／C 表）---
    # *[dict(_NB, total_rounds=10**9, card_system_enabled=False, base_bet=b, natural_sheet="A") for b in (1, 5, 10, 50, 100)],
    # *[dict(_EB, total_rounds=10**9, card_system_enabled=False, base_bet=b, natural_sheet="A") for b in (1, 5, 10, 50, 100)],
    # --- 3. SCR：Card System On，彩金關 ---
    # *[dict(_NB, total_rounds=10**8, card_system_enabled=True, base_bet=b) for b in (1, 5, 10, 50, 100)],
    # *[dict(_EB, total_rounds=10**8, card_system_enabled=True, base_bet=b) for b in (1, 5, 10, 50, 100)],
    # --- 4. 正式模擬：Card System On ---
    # *[dict(_NB, total_rounds=10**8, card_system_enabled=True, base_bet=b) for b in (1, 5, 10, 50, 100)],
    # *[dict(_EB, total_rounds=10**8, card_system_enabled=True, base_bet=b) for b in (1, 5, 10, 50, 100)],
]
THREADS = max(1, min(16, os.cpu_count() or 1))
OUTPUT_REPORT = True
CARD_RETRY_LIMIT = 10_000
RESPIN_MAX_REROLL = 10  # Description 6：重轉超過 10 次改用固定組合
RNG_SEED = 14_014

SUPPORTED_BET_MODES = (0, 1)
SUPPORTED_BETS = (1, 5, 10, 50, 100)

# Symbol ID（與 config.js 的 symbols 順序一致）
S_E, S_X2, S_X5, S_X10, S_RESPIN, S_SC_G, S_SC_R = 0, 6, 7, 8, 9, 10, 11
R4_KINDS = ("E", "2x", "5x", "10x", "respin", "scatter_g", "scatter_r")
R4_KIND_OF_SYMBOL = {S_E: 0, S_X2: 1, S_X5: 2, S_X10: 3, S_RESPIN: 4, S_SC_G: 5, S_SC_R: 6}

MULTIPLIER_THRESHOLDS = (
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50,
    60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 250, 300, 350, 400, 450,
    500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000,
    2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000,
    20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000, 9999999,
)

BASE_DIR = Path(__file__).resolve().parent

# ===== Config =====


def load_js_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    return json.loads(text[text.index("{"):text.rindex("}") + 1])


def validate_config_pair(base: dict[str, Any], rtp: dict[str, Any]) -> None:
    if base.get("game_id") != "H014" or rtp.get("game_id") != "H014":
        raise ValueError("config 的 game_id 必須為 H014")
    bv = str(base.get("excel_version", ""))
    if not bv.isdigit() or len(bv) != 1:
        raise ValueError(f"config.js 的 excel_version 必須為 1 碼，目前為 {bv!r}")
    rv = str(rtp.get("excel_version", ""))
    if len(rv.split(".")) != 4 or rv.split(".")[0] != bv:
        raise ValueError(f"RTP 版本 {rv!r} 必須為四段且第 1 碼等於基礎版本 {bv}")


def _cum(weights: list[int], size: int) -> np.ndarray:
    out = np.zeros(size, dtype=np.int64)
    acc = 0
    for i, w in enumerate(weights):
        if w < 0:
            raise ValueError("權重不得為負")
        acc += int(w)
        out[i] = acc
    for i in range(len(weights), size):
        out[i] = acc
    return out


def pack_tables(base: dict[str, Any], rtp: dict[str, Any], bet_mode: int, bet: int,
                card_on: bool, natural_sheet: str) -> dict[str, Any]:
    """把 Config 轉成 Numba 核心使用的固定型別陣列。"""
    nat = base["natural"][str(bet_mode)][str(bet)]
    sheet_names = sorted(nat["sheets"])
    ns = len(sheet_names)
    L = 64
    reel_sym = np.full((ns, 3, L), -1, np.int64)
    reel_len = np.zeros((ns, 3), np.int64)
    reel_cum = np.zeros((ns, 3, 3, L), np.int64)
    table_cum = np.zeros((ns, 3), np.int64)
    r4_sym = np.full((ns, L), -1, np.int64)
    r4_len = np.zeros(ns, np.int64)
    r4_cum = np.zeros((ns, 12, L), np.int64)
    rs_sym = np.full((ns, 3, L), -1, np.int64)
    rs_len = np.zeros((ns, 3), np.int64)
    rs_cum = np.zeros((ns, 3, L), np.int64)
    wheel_val = np.zeros((ns, 16), np.int64)
    wheel_cum = np.zeros((ns, 16), np.int64)
    fallback = np.zeros((ns, 3), np.int64)
    switch_cum = np.zeros((ns, 2), np.int64)
    for s, name in enumerate(sheet_names):
        sh = nat["sheets"][name]
        table_cum[s] = _cum(sh["table_weight"], 3)
        for r in range(3):
            reel_len[s, r] = len(sh["reels"][r])
            reel_sym[s, r, :reel_len[s, r]] = sh["reels"][r]
            for t, tn in enumerate("ABC"):
                reel_cum[s, t, r] = _cum(sh["reel_weights"][tn][r], L)
            rs_len[s, r] = len(sh["respin_reels"][r])
            rs_sym[s, r, :rs_len[s, r]] = sh["respin_reels"][r]
            rs_cum[s, r] = _cum(sh["respin_weights"][r], L)
        r4_len[s] = len(sh["r4"])
        r4_sym[s, :r4_len[s]] = sh["r4"]
        for b in range(12):  # 該押注不可能出現的分數分組允許總權重為 0
            r4_cum[s, b] = _cum(sh["r4_weights"][b], L)
        wheel_val[s, :len(sh["wheel"])] = sh["wheel"]
        wheel_cum[s] = _cum(sh["wheel_weights"], 16)
        fallback[s] = sh["respin_fallback_rng"]
        switch_cum[s] = _cum(sh["respin_switch_weight"], 2)
    digit_val = np.zeros(len(base["symbols"]), np.int64)
    digit_pow = np.ones(len(base["symbols"]), np.int64)
    is_digit = np.zeros(len(base["symbols"]), np.int64)
    for sid, (val, length) in base["digit_value"].items():
        digit_val[int(sid)] = val
        digit_pow[int(sid)] = 10 ** length
        is_digit[int(sid)] = 1

    card = rtp["card"][str(bet_mode)][str(bet)]
    card_iv = np.array(card["intervals"], np.int64)
    card_sheet = np.array([sheet_names.index(x) for x in card["sheets"]], np.int64)
    card_cum = _cum(card["weights"], len(card["weights"]))
    natural_idx = sheet_names.index(natural_sheet) if natural_sheet in sheet_names else -1
    if not card_on and natural_idx < 0:
        raise ValueError(f"bet{bet} 沒有 {natural_sheet} 表，可用：{sheet_names}")
    return {
        "sheet_names": sheet_names,
        "arrays": (reel_sym, reel_len, reel_cum, table_cum, r4_sym, r4_len, r4_cum,
                   rs_sym, rs_len, rs_cum, wheel_val, wheel_cum, fallback, switch_cum,
                   digit_val, digit_pow, is_digit, card_iv, card_sheet, card_cum),
        "cap": int(nat["base_cap"]),
        "natural_idx": natural_idx,
        "card": card,
    }


# ===== Numba Core =====

@njit(nogil=True)
def _draw(cum, n):
    total = cum[n - 1]
    x = np.random.randint(0, total)
    for i in range(n):
        if x < cum[i]:
            return i
    return n - 1


@njit(nogil=True)
def _number(a, b, c, digit_val, digit_pow, is_digit):
    n = 0
    if is_digit[a]:
        n = n * digit_pow[a] + digit_val[a]
    if is_digit[b]:
        n = n * digit_pow[b] + digit_val[b]
    if is_digit[c]:
        n = n * digit_pow[c] + digit_val[c]
    return n


@njit(nogil=True)
def _bucket(score):
    if score == 0:
        return 0
    if score == 1:
        return 1
    if score == 5:
        return 2
    if score == 10:
        return 3
    if score == 11:
        return 4
    if score == 15:
        return 5
    if score == 50:
        return 6
    if score == 51:
        return 7
    if score == 55:
        return 8
    if score <= 3000:
        return 9
    if score <= 6000:
        return 10
    return 11


@njit(nogil=True)
def _spin(s, bet, cap, reel_sym, reel_len, reel_cum, table_cum, r4_sym, r4_len, r4_cum,
          rs_sym, rs_len, rs_cum, wheel_val, wheel_cum, fallback, switch_cum,
          digit_val, digit_pow, is_digit, out):
    """單局。out = [win, s1, r4_symbol, respin_add, wheel_index, cap_reroll, respin_reroll, fallback]."""
    t = _draw(table_cum[s], 3)
    cap_reroll = 0
    while True:
        i = _draw(reel_cum[s, t, 0], reel_len[s, 0])
        j = _draw(reel_cum[s, t, 1], reel_len[s, 1])
        k = _draw(reel_cum[s, t, 2], reel_len[s, 2])
        s1 = _number(reel_sym[s, 0, i], reel_sym[s, 1, j], reel_sym[s, 2, k], digit_val, digit_pow, is_digit)
        if cap == 0 or s1 <= cap:
            break
        cap_reroll += 1
    b = _bucket(s1)
    pos = _draw(r4_cum[s, b], r4_len[s])
    sym = r4_sym[s, pos]
    win = s1
    respin_add = 0
    wheel_idx = -1
    respin_reroll = 0
    used_fallback = 0
    if sym == 6:
        win = s1 * 2
    elif sym == 7:
        win = s1 * 5
    elif sym == 8:
        win = s1 * 10
    elif sym == 9:
        ok = False
        for _ in range(RESPIN_MAX_REROLL + 1):
            a = rs_sym[s, 0, _draw(rs_cum[s, 0], rs_len[s, 0])]
            b2 = rs_sym[s, 1, _draw(rs_cum[s, 1], rs_len[s, 1])]
            c = rs_sym[s, 2, _draw(rs_cum[s, 2], rs_len[s, 2])]
            if cap > 0 and (c == 4 or c == 5) and switch_cum[s, 1] > 0:
                if _draw(switch_cum[s], 2) == 0:
                    tmp = b2
                    b2 = c
                    c = tmp
            s2 = _number(a, b2, c, digit_val, digit_pow, is_digit)
            if s2 > 0 and s1 + s2 >= bet and (cap == 0 or s2 <= cap):
                respin_add = s2
                ok = True
                break
            respin_reroll += 1
        if not ok:
            used_fallback = 1
            respin_add = _number(rs_sym[s, 0, fallback[s, 0]], rs_sym[s, 1, fallback[s, 1]],
                                 rs_sym[s, 2, fallback[s, 2]], digit_val, digit_pow, is_digit)
        win = s1 + respin_add
    elif sym == 10 or sym == 11:
        wheel_idx = _draw(wheel_cum[s], 16)
        win = s1 + wheel_val[s, wheel_idx] * bet
    out[0] = win
    out[1] = s1
    out[2] = sym
    out[3] = respin_add
    out[4] = wheel_idx
    out[5] = cap_reroll
    out[6] = respin_reroll
    out[7] = used_fallback


@njit(nogil=True)
def _in_interval(win, bet, card_iv, idx):
    lo = card_iv[idx]
    if lo == -1:
        return win == 0
    if win <= lo * bet:
        return False
    if idx + 1 < card_iv.shape[0]:
        return win <= card_iv[idx + 1] * bet
    return True


@njit(nogil=True)
def run_worker(seed, rounds, bet, cap, card_on, natural_idx, retry_limit, thresholds,
               reel_sym, reel_len, reel_cum, table_cum, r4_sym, r4_len, r4_cum,
               rs_sym, rs_len, rs_cum, wheel_val, wheel_cum, fallback, switch_cum,
               digit_val, digit_pow, is_digit, card_iv, card_sheet, card_cum):
    np.random.seed(seed)
    n_iv = card_iv.shape[0]
    n_th = thresholds.shape[0]
    # scalar stats
    sc = np.zeros(16, np.int64)   # 0 win,1 hits,2 max_win,3 s1_pay,4 respin_add,5 wheel_pay,6 special_cnt,
                                  # 7 cap_reroll,8 respin_reroll,9 fallback,10 retry_total,11 retry_exceeded,
                                  # 12 respin_cnt,13 wheel_cnt
    sumsq = np.zeros(1, np.float64)
    r4_cnt = np.zeros(12, np.int64)
    r4_pay = np.zeros(12, np.int64)
    wheel_hits = np.zeros(16, np.int64)
    bucket_cnt = np.zeros(n_th, np.int64)
    bucket_pay = np.zeros(n_th, np.int64)
    card_draw = np.zeros(n_iv, np.int64)
    card_retry = np.zeros(n_iv, np.int64)
    out = np.zeros(8, np.int64)
    for _ in range(rounds):
        if card_on:
            iv = _draw(card_cum, n_iv)
            card_draw[iv] += 1
            s = card_sheet[iv]
            tries = 0
            while True:
                _spin(s, bet, cap, reel_sym, reel_len, reel_cum, table_cum, r4_sym, r4_len, r4_cum,
                      rs_sym, rs_len, rs_cum, wheel_val, wheel_cum, fallback, switch_cum,
                      digit_val, digit_pow, is_digit, out)
                if _in_interval(out[0], bet, card_iv, iv):
                    break
                tries += 1
                if tries >= retry_limit:
                    sc[11] += 1
                    break
            sc[10] += tries
            card_retry[iv] += tries
        else:
            _spin(natural_idx, bet, cap, reel_sym, reel_len, reel_cum, table_cum, r4_sym, r4_len, r4_cum,
                  rs_sym, rs_len, rs_cum, wheel_val, wheel_cum, fallback, switch_cum,
                  digit_val, digit_pow, is_digit, out)
        win = out[0]
        sym = out[2]
        sc[0] += win
        if win > 0:
            sc[1] += 1
        if win > sc[2]:
            sc[2] = win
        sc[3] += out[1]
        sc[4] += out[3]
        if out[4] >= 0:
            wheel_hits[out[4]] += 1
            sc[5] += win - out[1]
            sc[13] += 1
        if sym == 9:
            sc[12] += 1
        if sym == 9 or sym == 10 or sym == 11:
            sc[6] += 1
        sc[7] += out[5]
        sc[8] += out[6]
        sc[9] += out[7]
        r4_cnt[sym] += 1
        r4_pay[sym] += win
        m = win / bet
        sumsq[0] += m * m
        for h in range(n_th):
            if win <= thresholds[h] * bet:
                bucket_cnt[h] += 1
                bucket_pay[h] += win
                break
    return sc, sumsq, r4_cnt, r4_pay, wheel_hits, bucket_cnt, bucket_pay, card_draw, card_retry


# ===== Runner =====

def simulate(packed: dict[str, Any], bet: int, rounds: int, card_on: bool, seed: int) -> tuple[dict[str, Any], float]:
    thresholds = np.array(MULTIPLIER_THRESHOLDS, np.int64)
    args = (bet, packed["cap"], card_on, max(packed["natural_idx"], 0), CARD_RETRY_LIMIT, thresholds,
            *packed["arrays"])
    run_worker(seed, 10, *args)  # Warm-up（Numba 編譯不計入 duration）
    threads = max(1, min(THREADS, rounds))
    per, rem = divmod(rounds, threads)
    parts = [per + (1 if i < rem else 0) for i in range(threads)]
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=threads) as pool:
        futures = [pool.submit(run_worker, seed + 1000 * (i + 1), n, *args) for i, n in enumerate(parts) if n]
        results = [f.result() for f in futures]
    duration = time.perf_counter() - start
    keys = ("sc", "sumsq", "r4_cnt", "r4_pay", "wheel_hits", "bucket_cnt", "bucket_pay", "card_draw", "card_retry")
    merged = {k: sum(r[i] for r in results) for i, k in enumerate(keys)}
    merged["sc"][2] = max(int(r[0][2]) for r in results)
    merged["rounds"] = sum(parts)
    assert merged["rounds"] == rounds
    return merged, duration


def build_result(combo: dict[str, Any], base: dict[str, Any], rtp: dict[str, Any], packed: dict[str, Any],
                 stats: dict[str, Any], duration: float) -> dict[str, Any]:
    bet_mode = int(combo["bet_mode"])
    bet = int(combo["base_bet"])
    cost = float(base["bet_modes"][str(bet_mode)]["cost_multiplier"])
    rounds = stats["rounds"]
    sc = stats["sc"]
    coin_in = rounds * bet * cost
    rtp_total = sc[0] / coin_in
    mean_m = sc[0] / rounds / (bet * cost)
    var = stats["sumsq"][0] / rounds / (cost * cost) - mean_m * mean_m
    std = math.sqrt(max(var, 0.0))
    card = packed["card"]
    max_iv = max(i for i, w in enumerate(card["weights"]) if w > 0)
    max_upper = card["intervals"][max_iv + 1] if max_iv + 1 < len(card["intervals"]) else "inf"
    return {
        "combo": combo, "stats": stats, "duration": duration, "bet_mode": bet_mode, "bet": bet, "cost": cost,
        "card_on": bool(combo["card_system_enabled"]),
        "natural_sheet": combo.get("natural_sheet", NATURAL_SHEET),
        "sheet_names": packed["sheet_names"], "card": card,
        "game_name": base["name_zh"], "game_id": base["online_game_id"], "parsheet_id": base["parsheet_id"],
        "base_version": base["excel_version"], "math_version": rtp["excel_version"],
        "bet_mode_name": base["bet_modes"][str(bet_mode)]["name"],
        "coin_in": coin_in, "rtp_total": rtp_total, "std": std,
        "max_multiplier_bg": max_upper if combo["card_system_enabled"] else "natural",
    }


def _pct(x: float) -> str:
    return f"{x * 100:.4f}%"


def _int(x: Any) -> str:
    return f"{int(x):,}"


def common_rows(res: dict[str, Any]) -> list[list[tuple[str, str]]]:
    st = res["stats"]
    sc = st["sc"]
    rounds = st["rounds"]
    bet = res["bet"]
    cost = res["cost"]
    sections = [
        [("game_name", res["game_name"]), ("game_id", res["game_id"])],
        [("config_file", res["combo"]["config_file"]), ("config_rtp_file", res["combo"]["config_rtp_file"]),
         ("math_version", res["math_version"]), ("card_system", "on" if res["card_on"] else "off")],
        [("bet_mode", res["bet_mode_name"]), ("bet_multi", f"{cost:g}"), ("feature_price_multiplier", "n/a"),
         ("base_bet", f"{float(bet):.1f}"), ("bet_amount", f"{bet * cost:.1f}"),
         ("bet_tier_amount", f"{bet * cost:.1f}"), ("bet_tier", f"bet{bet}"), ("link_enabled", "false"),
         ("max_multiplier_bg", str(res["max_multiplier_bg"])), ("max_multiplier_fg", "n/a"),
         ("coin_in", f"{res['coin_in']:,.1f}"), ("total_rounds", _int(rounds)),
         ("duration", f"{res['duration']:05.2f} sec")],
        [("rtp_total", _pct(res["rtp_total"])), ("rtp_link", _pct(0.0)), ("rtp_bonus", _pct(0.0)),
         ("rtp_game", _pct(res["rtp_total"])), ("rtp_bg", _pct(res["rtp_total"])),
         ("hit_rate_bg", _pct(sc[1] / rounds))],
        [("special_symbol_cnt", _int(sc[6])), ("SCR", _int(round(sc[6] / rounds * 10_000_000_000)) if rounds else "0")],
        [("volatility_std", f"{res['std']:05.2f}"), ("standard_error", f"{res['std'] / math.sqrt(rounds):.6f}")],
    ]
    if res["card_on"]:
        sections.append([
            ("card_system_profile", f"bet{bet}"), ("card_retry_limit", _int(CARD_RETRY_LIMIT)),
            ("retry_total", _int(sc[10])), ("avg_retry", f"{sc[10] / rounds:.2f}"),
            ("retry_limit_exceeded", _int(sc[11])),
        ])
    return sections


def game_info_rows(res: dict[str, Any]) -> list[tuple[str, str]]:
    st = res["stats"]
    sc = st["sc"]
    rounds = st["rounds"]
    coin_in = res["coin_in"]
    rows = [("natural_sheet", "card" if res["card_on"] else res["natural_sheet"]),
            ("number_rtp", _pct(sc[3] / coin_in))]
    for sym, name in ((6, "2x"), (7, "5x"), (8, "10x"), (9, "respin"), (10, "scatter_g"), (11, "scatter_r"), (0, "E")):
        rows.append((f"r4_{name}_rate", _pct(st["r4_cnt"][sym] / rounds)))
        rows.append((f"r4_{name}_rtp", _pct(st["r4_pay"][sym] / coin_in)))
    rows += [
        ("respin_add_rtp", _pct(sc[4] / coin_in)),
        ("respin_avg_reroll", f"{sc[8] / max(1, sc[12]):.4f}"),
        ("respin_fallback_cnt", _int(sc[9])),
        ("wheel_rtp", _pct(sc[5] / coin_in)),
        ("base_cap_reroll_cnt", _int(sc[7])),
        ("max_win_x", f"{sc[2] / res['bet']:,.2f} x"),
    ]
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
    bet = res["bet"]
    rows = []
    for i, upper in enumerate(MULTIPLIER_THRESHOLDS):
        interval = "0" if i == 0 else f"{float(MULTIPLIER_THRESHOLDS[i - 1]):.1f} < X <= {float(upper):.1f}"
        rows.append({"Interval": interval, "base_game_cnt": int(st["bucket_cnt"][i]),
                     "base_game_pay": st["bucket_pay"][i] / bet, "Interval_Upper": upper})
    return pd.DataFrame(rows)


def feature_frame(res: dict[str, Any]) -> pd.DataFrame:
    st = res["stats"]
    rows = []
    sheet = res["sheet_names"]
    for i in range(16):
        if st["wheel_hits"][i]:
            rows.append((f"wheel_index_{i}", int(st["wheel_hits"][i])))
    for sym, name in ((0, "E"), (6, "2x"), (7, "5x"), (8, "10x"), (9, "respin"), (10, "scatter_g"), (11, "scatter_r")):
        rows.append((f"r4_{name}_cnt", int(st["r4_cnt"][sym])))
        rows.append((f"r4_{name}_pay_x", st["r4_pay"][sym] / res["bet"]))
    rows.append(("sheets", "/".join(sheet)))
    return pd.DataFrame(rows, columns=["Index", "Value"])


def card_frame(res: dict[str, Any]) -> pd.DataFrame:
    st = res["stats"]
    card = res["card"]
    rounds = st["rounds"]
    total_w = sum(card["weights"])
    rows = []
    for i, iv in enumerate(card["intervals"]):
        draws = int(st["card_draw"][i])
        rows.append({"Interval": iv, "Sheet": card["sheets"][i], "Weight": card["weights"][i],
                     "Setting_Rate": card["weights"][i] / total_w, "Actual_Rate": draws / rounds,
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
    head = res["parsheet_id"]
    if not res["card_on"]:
        return (f"{head}_{str(res['base_version']).zfill(2)}_{stamp}_betmode{res['bet_mode']}_{rounds_tag}"
                f"_bet{res['bet']}_{res['natural_sheet']}.xlsx")
    rtp_tag = f"{res['rtp_total'] * 100:.4f}".replace(".", "")[:4]
    return (f"{head}_{format_rtp_version_tag(res['math_version'])}_{stamp}_betmode{res['bet_mode']}"
            f"_{rounds_tag}_{rtp_tag}_bet{res['bet']}.xlsx")


def output_report(res: dict[str, Any]) -> Path:
    directory = BASE_DIR / "Record"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / report_filename(res)
    flat = [row for section in common_rows(res) for row in section] + game_info_rows(res)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(flat, columns=["Index", "Value"]).to_excel(writer, sheet_name="Overview", index=False)
        multiplier_line_frame(res).to_excel(writer, sheet_name="Multiplier Line", index=False)
        feature_frame(res).to_excel(writer, sheet_name="Feature", index=False)
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
        raise ValueError(f"不支援的 bet_mode {combo['bet_mode']}；本作只有 0 / 1")
    if int(combo["total_rounds"]) <= 0:
        raise ValueError("total_rounds 必須為正整數")
    if combo["base_bet"] not in SUPPORTED_BETS:
        raise ValueError(f"base_bet 只能是 {SUPPORTED_BETS}，不可加壓")


def run_batch(combo: dict[str, Any], index: int, total: int) -> dict[str, Any]:
    validate_batch_run(combo)
    print(f"=== Batch {index}/{total}: {combo} ===")
    print()
    base = load_js_config(BASE_DIR / combo["config_file"])
    rtp = load_js_config(BASE_DIR / combo["config_rtp_file"])
    validate_config_pair(base, rtp)
    card_on = bool(combo["card_system_enabled"])
    natural_sheet = combo.get("natural_sheet", NATURAL_SHEET)
    packed = pack_tables(base, rtp, int(combo["bet_mode"]), int(combo["base_bet"]), card_on, natural_sheet)
    stats, duration = simulate(packed, int(combo["base_bet"]), int(combo["total_rounds"]), card_on,
                               RNG_SEED + index)
    res = build_result(combo, base, rtp, packed, stats, duration)
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
                 "card_system_is_newbie": False, "base_bet": BASE_BET_SETTING, "natural_sheet": NATURAL_SHEET}]
    for i, combo in enumerate(runs, 1):
        run_batch(combo, i, len(runs))


if __name__ == "__main__":
    main()
