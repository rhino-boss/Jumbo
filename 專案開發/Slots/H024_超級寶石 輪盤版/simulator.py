"""H024 超級寶石 輪盤版 (Super Gems - Wheel) simulator.

盤面：R1～R3 為 3×3、5 條固定線（只有 3 連線得分，WW 可替代）＋ R4 特色轉輪（只看中線）。
R4 依押注模式權重抽出 1X／2X／3X／5X／10X／15X 或輪盤（C2：Normal Bet、C3：Extra Bet）：
- 倍數：線獎合計 × 倍數。
- 輪盤：抽外圈基礎倍數（1～1000）與內圈加乘倍數（依外圈結果的權重欄抽），
  本局派彩 ＝ 線獎合計 × 加乘倍數 ＋ 基礎倍數 × 加乘倍數（以 Normal Bet 底注計；盤面沒得分也會派輪盤獎）。
押注模式：0 Normal Bet（1x）、1 Extra Bet（1.5x）。原作 Overview 列的 Super Feature Buy（250x）沒有任何參數，本程式不支援。

玩法定義見 ``game_rule.md``；執行參數一律來自 Config，不在本程式內重複維護輪帶、權重、Paytable 或 Feature 參數。
- ``config_01A.js``：產線 01（菲律賓），層級 97A_Bet1（小 Bet）／97A_Bet2（中 Bet；本作無大 Bet 檔，> $300 也用 97A_Bet2）。
- ``config_02A.js``：產線 02（美國 Reskin），層級 92A／94A／96A，不分押注層級，由 ``reskin_version`` 指定。
- 卡片區間與 Multiplier Line 的倍率分母都是 Normal Bet 底注（贏分 ÷ base_bet）；RTP、volatility_std 以實際押注計。
- OP Jackpot 觸發符號＝特色轉輪上的輪盤（C2／C3，2026-11-27 使用者：比照 H020 由特色轉輪特殊符號觸發）；
  ``special_symbol_cnt`` 統計 R4 可視 3 格（演出停點同 Demo：在輪帶上隨機挑一個中線符號相同的位置）出現輪盤的局數，SCR＝其 ÷ 局數 × 10^10。
  彩金派彩本身不在本程式模擬（jackpot off）。

Runner、BATCH_RUNS、Console 欄位與 Excel 報表版面依 ``專案需知/開發規範/模擬程式規範.md``。
2026-11-26 建立（範本 H020；R4 改輪盤）。
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
CONFIG_TIER = "AUTO"            # AUTO：01 依押注檔位選層級、02 依 reskin_version；也可直接寫層級代號
# 01 檔位對應（2026-11-26 新分級）：小 Bet <= $1（NB／EB 實際押注）→ 97A_Bet1；其餘 → 97A_Bet2（大 Bet > $300 無專屬檔，同 97A_Bet2）
TIER_CODE = {"small_bet": "97{s}_Bet1", "medium_bet": "97{s}_Bet2", "big_bet": "97{s}_Bet2"}
NEWBIE_TIER = "97{s}_Bet2"
RESKIN_VERSION = "92"           # config_02A.js 用：92／94／96
TOTAL_ROUNDS = 100_000
BASE_BET_SETTING = 1.0
BET_MODE = 0                    # 0 = Normal Bet, 1 = Extra Bet
CARD_SYSTEM_ENABLED = True
CARD_SYSTEM_IS_NEWBIE = False
RUN_ALL_COMBINATIONS = True

MODE_NORMALBET = 0
MODE_EXTRABET = 1
SUPPORTED_BET_MODES = (MODE_NORMALBET, MODE_EXTRABET)
BUY_MODES: tuple[int, ...] = ()
MODE_KEY = {MODE_NORMALBET: "normal", MODE_EXTRABET: "extra_bet"}
CARD_KEY = {MODE_NORMALBET: "base_game", MODE_EXTRABET: "eb_base_game"}

_NB = {"config_file": "config_01A.js", "tier": "AUTO", "bet_mode": 0, "card_system_enabled": True,
       "card_system_is_newbie": False, "base_bet": 2}
_EB = dict(_NB, bet_mode=1)
_NEW = {"card_system_is_newbie": True}
_R = {"config_file": "config_02A.js"}

PRESETS: dict[str, list[dict[str, Any]]] = {
    # --- 1. 測試：Card System On，10^5 ---
    "test": [dict(m, total_rounds=10**5) for m in (_NB, _EB)],
    # --- 2. 自然機率：Card System Off（NB／EB；原作工作簿自然分布為 10^8 局）---
    "natural": [dict(m, total_rounds=10**8, card_system_enabled=False) for m in (_NB, _EB)],
    # --- 01 原作卡片驗證：97A_Bet1／97A_Bet2 × 老手，新手固定 97A_Bet2 ---
    "card01": [dict(m, tier=t, base_bet=b, total_rounds=10**7) for t, b in (("97A_Bet1", 0.6), ("97A_Bet2", 2)) for m in (_NB, _EB)]
              + [dict(m, **_NEW, tier="97A_Bet2", total_rounds=10**7) for m in (_NB, _EB)],
    # --- 02 Reskin 快速驗證：92／94／96 × 老手／新手 × NB／EB，10^6 ---
    "reskin02": [dict(m, **_R, **p, reskin_version=v, total_rounds=10**6)
                 for v in ("92", "94", "96") for p in ({}, _NEW) for m in (_NB, _EB)],
    # --- 01 新手（PARsheet 權重，93%）快速驗證 ---
    "newbie01": [dict(m, **_NEW, tier="97A_Bet2", total_rounds=10**6) for m in (_NB, _EB)],
    # --- 3. SCR：Card On、彩金關，10^8；老手各 config 共用一個代表（01 用 97A_Bet2、02 用 92A），新手獨立 ---
    "scr": [dict(m, **p, tier="97A_Bet2", total_rounds=10**8) for p in ({}, _NEW) for m in (_NB, _EB)]
           + [dict(m, **_R, **p, reskin_version="92", total_rounds=10**8) for p in ({}, _NEW) for m in (_NB, _EB)],
    # --- 4. 正式模擬（02，10^8；需要時再跑）---
    "reskin02_formal": [dict(m, **_R, **p, reskin_version=v, total_rounds=10**8)
                        for v in ("92", "94", "96") for p in ({}, _NEW) for m in (_NB, _EB)],
}
BATCH_RUNS = PRESETS["test"]

THREADS = max(1, min(24, os.cpu_count() or 1))
OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = True
RUN_SINGLE_SPIN_DEBUG = False
DEBUG_ROUNDS = 1
CARD_RETRY_LIMIT = 10_000
JACKPOT_ENABLED = False         # Config 無彩金參數，無作用
RNG_SEED = 24_024
COIN_BASE = 100.0
PAY_SCALE = 10                  # 賠率含 2.4／1.6／0.4，核心以 ×10 整數計算

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
    if not path.exists():
        raise FileNotFoundError(f"找不到 {path.name}，請在 H024 專案資料夾執行")
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
    if data.get("game_id") != "H024" or base.get("game_id") != "H024":
        raise ValueError("config 的 game_id 必須為 H024")
    return cfg


def wager_for_mode(base: dict[str, Any], mode: int, base_bet: float) -> float:
    return base_bet * float(base["bet_modes"][MODE_KEY[mode]]["cost_multiplier"])


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
    amount = wager_for_mode(base, mode, bet)
    bt = bet_tier_name(amount, bet)
    tier = combo["tier"]
    if tier == "AUTO":
        if data.get("product_line") == "02":
            tier = f"{combo.get('reskin_version', RESKIN_VERSION)}{data['series']}"
        elif combo["card_system_is_newbie"]:
            tier = NEWBIE_TIER.format(s=data["series"])
        else:
            tier = TIER_CODE[bt].format(s=data["series"])
        print(f"[auto] bet_mode {mode}、base_bet {bet:g}（檔位金額 ${amount:g}）→ {tier}")
    return data, expand_tier(data, tier), tier, bt


def _cum(weights: list[int]) -> np.ndarray:
    if any(int(w) < 0 for w in weights):
        raise ValueError("權重不得為負")
    return np.cumsum(np.array(weights, np.int64))


def pack_tables(cfg: dict[str, Any], mode: int, newbie: bool) -> dict[str, Any]:
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
    if len(fr["r4_weights"]) != len(r4_mult) + 1:
        raise ValueError("r4_weights 長度必須為倍數數量 + 1（最後一格＝輪盤）")
    r4_cum = _cum(fr["r4_weights"])
    base_vals = np.array(cfg["wheel_base_values"], np.int64)
    extra_vals = np.array(cfg["wheel_extra_values"], np.int64)
    base_cum = _cum(fr["wheel_base_weights"])
    ext = fr["wheel_extra_weights"]
    if len(ext) != len(base_vals) or any(len(e) != len(extra_vals) for e in ext):
        raise ValueError("wheel_extra_weights 形狀必須為 [外圈數][內圈數]")
    extra_cum = np.zeros((len(base_vals), len(extra_vals)), np.int64)
    for b, w in enumerate(ext):
        if fr["wheel_base_weights"][b] > 0 and sum(w) <= 0:
            raise ValueError(f"外圈 {base_vals[b]}x 有權重但內圈權重全為 0")
        if sum(w) > 0:
            extra_cum[b] = _cum(w)
    profile = "newbie" if newbie else "oldhand"
    deck = cfg["card_system"]["profiles"][profile][CARD_KEY[mode]]
    card_lo = np.array([c["min"] for c in deck], np.int64)
    card_hi = np.array([c["max"] for c in deck], np.int64)
    card_cum = _cum([c["weight"] for c in deck])
    # R4 演出停點：每個結果在輪帶上可停的位置，以及該位置的可視 3 格是否出現輪盤（OP Jackpot 觸發符號）
    strip = [int(x) for x in fr["r4_strip"]]
    wid = int(fr["wheel_symbol_id"])
    ids = [int(x) for x in cfg["r4_symbol_ids"]] + [wid]
    n = len(strip)
    vis_cnt = np.zeros(len(ids), np.int64)
    vis_flag = np.zeros((len(ids), n), np.int64)
    for o, sid in enumerate(ids):
        pos = [i for i, s in enumerate(strip) if s == sid] or list(range(n))   # 輪帶上沒有該符號時中線覆蓋為結果
        vis_cnt[o] = len(pos)
        for j, i in enumerate(pos):
            vis_flag[o, j] = int(sid == wid or strip[(i - 1) % n] == wid or strip[(i + 1) % n] == wid)
    return {"arrays": (reel_sym, reel_len, reel_cum, lines, pay10, wild, r4_mult, r4_cum, base_vals, base_cum,
                       extra_vals, extra_cum, card_lo, card_hi, card_cum, vis_cnt, vis_flag),
            "deck": deck, "card_profile": profile}


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
def _spin(reel_sym, reel_len, reel_cum, lines, pay10, wild, r4_mult, r4_cum, base_vals, base_cum, extra_vals,
          extra_cum, out, sym_hit, sym_pay):
    """單次 Spin。out = [win10, line10, r4_idx, base_idx, extra_idx, line_hits]；sym_hit／sym_pay 為本把各符號線數與線獎。"""
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
    r4 = _draw(r4_cum)
    bi = -1
    ei = -1
    if r4 < r4_mult.shape[0]:
        win10 = line10 * r4_mult[r4]
    else:  # 輪盤：線獎 × 內圈 ＋ 外圈 × 內圈
        bi = _draw(base_cum)
        ei = _draw(extra_cum[bi])
        win10 = line10 * extra_vals[ei] + base_vals[bi] * extra_vals[ei] * 10
    out[0] = win10
    out[1] = line10
    out[2] = r4
    out[3] = bi
    out[4] = ei
    out[5] = hits


@njit(nogil=True)
def _in_card(win10, lo, hi):
    if lo == -1:
        return win10 == 0
    return lo * 10 < win10 <= hi * 10


@njit(nogil=True)
def run_worker(seed, rounds, card_on, retry_limit, thresholds,
               reel_sym, reel_len, reel_cum, lines, pay10, wild, r4_mult, r4_cum, base_vals, base_cum,
               extra_vals, extra_cum, card_lo, card_hi, card_cum, vis_cnt, vis_flag, cost):
    np.random.seed(seed)
    n_th = thresholds.shape[0]
    n_r4 = r4_mult.shape[0] + 1
    n_b = base_vals.shape[0]
    n_e = extra_vals.shape[0]
    n_card = card_cum.shape[0]
    n_sym = pay10.shape[0]
    # 0 win10, 1 hit_rounds, 2 max_win10, 3 line10_sum, 4 line_hit_rounds, 5 wheel_cnt, 6 retry_total,
    # 7 retry_exceeded, 8 wheel_prize10, 9 wheel_line10(×extra), 10 wheel_with_line, 11 r4_mult_pay10
    sc = np.zeros(13, np.int64)   # 12 special_symbol_cnt（R4 可視 3 格出現輪盤）
    sumsq = np.zeros(1, np.float64)
    r4_cnt = np.zeros(n_r4, np.int64)
    r4_win_cnt = np.zeros(n_r4, np.int64)
    b_cnt = np.zeros(n_b, np.int64)
    e_cnt = np.zeros(n_e, np.int64)
    bucket_cnt = np.zeros(n_th, np.int64)
    bucket_pay = np.zeros(n_th, np.int64)
    card_draw = np.zeros(n_card, np.int64)
    card_retry = np.zeros(n_card, np.int64)
    sym_hits = np.zeros(n_sym, np.int64)
    sym_pays = np.zeros(n_sym, np.int64)
    sh = np.zeros(n_sym, np.int64)
    sp = np.zeros(n_sym, np.int64)
    out = np.zeros(6, np.int64)
    for _ in range(rounds):
        iv = -1
        if card_on:
            iv = _draw(card_cum)
            card_draw[iv] += 1
        tries = 0
        while True:
            _spin(reel_sym, reel_len, reel_cum, lines, pay10, wild, r4_mult, r4_cum, base_vals, base_cum,
                  extra_vals, extra_cum, out, sh, sp)
            if not card_on or _in_card(out[0], card_lo[iv], card_hi[iv]):
                break
            tries += 1
            if tries >= retry_limit:
                sc[7] += 1
                break
        if card_on:
            sc[6] += tries
            card_retry[iv] += tries
        win10 = out[0]
        line10 = out[1]
        r4 = out[2]
        sc[0] += win10
        if win10 > 0:
            sc[1] += 1
        if win10 > sc[2]:
            sc[2] = win10
        sc[3] += line10
        r4_cnt[r4] += 1
        if line10 > 0:
            sc[4] += 1
            r4_win_cnt[r4] += 1
            for s in range(n_sym):
                sym_hits[s] += sh[s]
                sym_pays[s] += sp[s]
        if r4 == n_r4 - 1:
            sc[5] += 1
            b_cnt[out[3]] += 1
            e_cnt[out[4]] += 1
            prize = base_vals[out[3]] * extra_vals[out[4]] * 10
            sc[8] += prize
            sc[9] += win10 - prize
            if line10 > 0:
                sc[10] += 1
        else:
            sc[11] += win10
        if vis_flag[r4, np.random.randint(0, vis_cnt[r4])] == 1:
            sc[12] += 1
        x = win10 / 10.0 / cost
        sumsq[0] += x * x
        for h in range(n_th):
            if win10 <= thresholds[h] * 10:
                bucket_cnt[h] += 1
                bucket_pay[h] += win10
                break
    return (sc, sumsq, r4_cnt, r4_win_cnt, b_cnt, e_cnt, bucket_cnt, bucket_pay, card_draw, card_retry,
            sym_hits, sym_pays)


def _worker_entry(args):
    return run_worker(*args)


def run_simulation(packed: dict[str, Any], rounds: int, card_on: bool, seed: int, cost: float,
                   threads: int) -> tuple[dict[str, Any], float]:
    thresholds = np.array(MULTIPLIER_THRESHOLDS, np.int64)
    common = (card_on, CARD_RETRY_LIMIT, thresholds, *packed["arrays"], cost)
    workers = max(1, min(threads, rounds))
    per, rem = divmod(rounds, workers)
    parts = [per + (1 if i < rem else 0) for i in range(workers)]
    jobs = [(seed + 7919 * i, n, *common) for i, n in enumerate(parts) if n]
    with ProcessPoolExecutor(max_workers=len(jobs)) as pool:
        list(pool.map(_worker_entry, [(seed - 1, 1, *common)] * len(jobs)))  # Warm-up（不計入 duration、不併入統計）
        start = time.perf_counter()
        results = list(pool.map(_worker_entry, jobs))
        duration = time.perf_counter() - start
    keys = ("sc", "sumsq", "r4_cnt", "r4_win_cnt", "b_cnt", "e_cnt", "bucket_cnt", "bucket_pay",
            "card_draw", "card_retry", "sym_hits", "sym_pays")
    merged = {k: sum(r[i] for r in results) for i, k in enumerate(keys)}
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
    sections = [
        [("game_name", res["cfg"]["name_zh"]), ("game_id", res["cfg"]["online_game_id"])],
        [("config_file", res["combo"]["config_file"]), ("tier", res["tier"]),
         ("math_version", res["cfg"]["excel_version"] if res["card_on"] else res["cfg_base_version"]),
         ("card_system", "on" if res["card_on"] else "off")],
        [("bet_mode", res["mode_name"]), ("bet_multi", f"{cost:g}"), ("feature_price_multiplier", "n/a"),
         ("base_bet", f"{bet:.2f}"), ("bet_amount", f"{bet * cost:.2f}"), ("bet_tier_amount", f"{bet * cost:.2f}"),
         ("bet_tier", res["bet_tier"]), ("jackpot", "off"), ("coin_in", f"{bet * cost:.2f}"),
         ("total_rounds", _int(rounds)), ("duration", f"{res['duration']:05.2f} sec")],
        [("rtp_total", _pct(m["rtp_game"])), ("rtp_link", "n/a"), ("rtp_bonus", "n/a"),
         ("rtp_game", _pct(m["rtp_game"])), ("rtp_bg", _pct(m["rtp_game"])), ("rtp_fg", "n/a"),
         ("hit_rate_bg", _pct(sc[1] / rounds)), ("hit_rate_fg", "n/a"), ("fg_trigger_rate", "n/a"),
         ("retrigger_trigger_rate", "n/a"), ("avg_fg_spins", "n/a")],
        [("bg_trigger_fg_cnt", "n/a"), ("bg_trigger_fg_pay", "n/a"), ("special_symbol_cnt", _int(sc[12])),
         ("SCR", _int(round(sc[12] / rounds * 10_000_000_000)) if rounds else "0")],
        [("max_win_x", f"{sc[2] / PAY_SCALE / cost:,.2f} x"), ("capped_rounds", "0"),
         ("volatility_std", f"{m['std']:05.2f}"), ("volatility_std_fg", "n/a"), ("standard_error", f"{m['se']:05.2f}")],
    ]
    if res["card_on"]:
        sections.append([("card_system_profile", res["card_profile"]), ("card_retry_limit", str(CARD_RETRY_LIMIT)),
                         ("retry_total", _int(sc[6])), ("avg_retry", f"{sc[6] / rounds:05.2f}")])
        sections.append([("retry_limit_exceeded", _int(sc[7])), ("retry_limit_bg_range", _int(sc[7])),
                         ("retry_limit_bg_freegame", "0"), ("retry_limit_fg", "0")])
    return sections


def game_info_rows(res: dict[str, Any]) -> list[tuple[str, str]]:
    st = res["stats"]
    sc = st["sc"]
    rounds = st["rounds"]
    coin = res["metrics"]["coin_in_total"]
    bet = res["bet"]
    cfg = res["cfg"]
    rows = [("line_hit_rate", _pct(sc[4] / rounds, 6)),
            ("line_rtp_no_multiplier", _pct(sc[3] / PAY_SCALE * bet / coin, 6)),
            ("multiplier_rtp", _pct(sc[11] / PAY_SCALE * bet / coin, 6)),
            ("wheel_rate", _pct(sc[5] / rounds, 6)),
            ("wheel_rtp", _pct((sc[8] + sc[9]) / PAY_SCALE * bet / coin, 6)),
            ("wheel_prize_rtp", _pct(sc[8] / PAY_SCALE * bet / coin, 6)),
            ("wheel_line_rtp", _pct(sc[9] / PAY_SCALE * bet / coin, 6)),
            ("wheel_with_line_rate", _pct(sc[10] / max(1, sc[5]), 6)),
            ("avg_wheel_prize_x", f"{sc[8] / PAY_SCALE / max(1, sc[5]):.4f}")]
    names = [f"{v}x" for v in cfg["r4_multipliers"]] + ["wheel"]
    for i, n in enumerate(names):
        rows.append((f"r4_{n}_rate", _pct(st["r4_cnt"][i] / rounds, 6)))
    for i, v in enumerate(cfg["wheel_base_values"]):
        rows.append((f"wheel_base_{v}x_share", _pct(st["b_cnt"][i] / max(1, sc[5]))))
    for i, v in enumerate(cfg["wheel_extra_values"]):
        rows.append((f"wheel_extra_{v}x_share", _pct(st["e_cnt"][i] / max(1, sc[5]))))
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
    rows = []
    for i, upper in enumerate(MULTIPLIER_THRESHOLDS):
        interval = "0" if i == 0 else f"{float(MULTIPLIER_THRESHOLDS[i - 1]):.1f} < X <= {float(upper):.1f}"
        rows.append({"Interval": interval, "base_game_cnt": int(st["bucket_cnt"][i]),
                     "base_game_pay": st["bucket_pay"][i] / PAY_SCALE * res["bet"], "Interval_Upper": upper})
    return pd.DataFrame(rows)


def feature_frame(res: dict[str, Any]) -> pd.DataFrame:
    st = res["stats"]
    cfg = res["cfg"]
    rows = [("wheel_cnt", int(st["sc"][5])), ("wheel_with_line_cnt", int(st["sc"][10]))]
    names = [f"{v}x" for v in cfg["r4_multipliers"]] + ["wheel"]
    rows += [(f"r4_{n}_cnt", int(st["r4_cnt"][i])) for i, n in enumerate(names)]
    rows += [(f"r4_{n}_on_line_win_cnt", int(st["r4_win_cnt"][i])) for i, n in enumerate(names)]
    rows += [(f"wheel_base_{v}x_cnt", int(st["b_cnt"][i])) for i, v in enumerate(cfg["wheel_base_values"])]
    rows += [(f"wheel_extra_{v}x_cnt", int(st["e_cnt"][i])) for i, v in enumerate(cfg["wheel_extra_values"])]
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
    return pd.DataFrame([{"scene": "BG", "symbol": names[str(s)], "length": 3, "hits": int(st["sym_hits"][s]),
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


def format_base_version_tag(version: str) -> str:
    return str(version).zfill(2)


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
        return f"{res['base_parsheet_id']}_{format_base_version_tag(res['cfg_base_version'])}_{stamp}_betmode{res['bet_mode']}_{rt}.xlsx"
    gid = res["cfg"]["game_id"]  # H024197A／H024192A（含 Variant）
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
        raise ValueError(f"不支援的 bet_mode {combo['bet_mode']}；本作只有 0（NB）／1（EB）")
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
    cost = float(cfg["bet_modes"][MODE_KEY[mode]]["cost_multiplier"])
    card_on = bool(combo["card_system_enabled"])
    newbie = bool(combo["card_system_is_newbie"]) and card_on
    packed = pack_tables(cfg, mode, newbie)
    stats, duration = run_simulation(packed, int(combo["total_rounds"]), card_on, seed + index, cost, threads)
    res = {"combo": combo, "cfg": cfg, "cfg_base_version": data["base"]["excel_version"], "base_parsheet_id": data["base"]["parsheet_id"], "tier": tier if card_on else "base",
           "bet_tier": bt, "bet_mode": mode, "bet": bet, "cost": cost, "card_on": card_on, "card_profile": packed["card_profile"],
           "deck": packed["deck"], "mode_name": cfg["bet_modes"][MODE_KEY[mode]]["name"], "stats": stats, "duration": duration}
    res["metrics"] = calculated_metrics(res)
    if SHOW_CONSOLE_SUMMARY:
        print_console(res)
    if OUTPUT_REPORT:
        print(f"report -> {output_report(res)}")
        print()
    return res


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="H024 超級寶石 輪盤版 simulator")
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
    p.add_argument("--tier", default=None, help="覆寫層級，例如 97A_Bet1／97A_Bet2／92A／94A／96A")
    p.add_argument("--config", default=None, help="覆寫 config_file")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--series", choices=["A"], default=None)
    return p.parse_args()


def debug_round(combo: dict[str, Any]) -> None:
    """單執行緒逐局除錯：印出每局 R4 結果與得分。"""
    data, cfg, tier, bt = load_batch_configs(combo)
    mode = int(combo["bet_mode"])
    packed = pack_tables(cfg, mode, bool(combo["card_system_is_newbie"]))
    th = np.array(MULTIPLIER_THRESHOLDS, np.int64)
    cost = float(cfg["bet_modes"][MODE_KEY[mode]]["cost_multiplier"])
    for k in range(DEBUG_ROUNDS):
        r = run_worker(RNG_SEED + k, 1, bool(combo["card_system_enabled"]), CARD_RETRY_LIMIT, th, *packed["arrays"], cost)
        print(f"round {k + 1}: win {r[0][0] / PAY_SCALE:g}x base bet, line {r[0][3] / PAY_SCALE:g}x, wheel {int(r[0][5])}, retry {int(r[0][6])}")


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
        if args.series:
            r["config_file"] = r["config_file"][:-5] + args.series + ".js"
    if args.no_report:
        OUTPUT_REPORT = False
    if args.debug or RUN_SINGLE_SPIN_DEBUG:
        debug_round(runs[0])
        return
    threads = args.threads or THREADS
    seed = args.seed if args.seed is not None else RNG_SEED
    for i, combo in enumerate(runs, 1):
        run_batch(combo, i, len(runs), threads, seed)


if __name__ == "__main__":
    main()
