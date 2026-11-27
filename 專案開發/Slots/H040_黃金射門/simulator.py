"""H040 黃金射門 (Goal Rush) simulator.

盤面：3×3、5 條固定線（只有 3 連線得分；WW 只出現在第 3 輪，可替代所有一般符號，本身不得分）。
足球特色（Football Feature）：得分線含 WW 時觸發，以本局盤面總贏分為底，踢 5 球：
- 依權重抽一組腳本，腳本預先決定 5 球各自的結果類型（0 失敗、1／2／3 成功）。
- 每球先從 20 組倍數表等機率抽一組 6 個倍數擺在球門上；成功時依結果類型的權重組（ID 1～3）抽中其中一格。
- 每次成功把累積倍數乘上抽中的倍數（起始 1），5 球後派彩 ＝ 盤面總贏分 × 累積倍數（不另派盤面贏分）。
押注模式：0 Normal Bet（1x）、3 Buy Feature（50x，用 bf_1 停輪權重、重轉到觸發足球特色為止）。

玩法定義見 ``game_rule.md``；執行參數一律來自 Config，不在本程式內重複維護輪帶、權重、Paytable 或 Feature 參數。
- ``config_01A.js``：產線 01（菲律賓），層級 97A_Bet1（小 Bet）／97A_Bet2（中 Bet；本作無大 Bet 檔，> $300 也用 97A_Bet2）。
- 卡片為整局贏分卡（含足球特色），區間與 Multiplier Line 的倍率分母都是 Normal Bet 底注（贏分 ÷ base_bet）；RTP、volatility_std 以實際押注計。
- OP Jackpot 不在本程式模擬（Config 無彩金參數）；``special_symbol_cnt`` 統計盤面出現 WW 的局（SCR 口徑同原作 Parameter-卡片A 的 Scatter Combo Rate）。

Runner、BATCH_RUNS、Console 欄位與 Excel 報表版面依 ``專案需知/開發規範/模擬程式規範.md``。
2026-11-27 建立（範本 H024）。
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
TOTAL_ROUNDS = 100_000
BASE_BET_SETTING = 1.0
BET_MODE = 0                    # 0 = Normal Bet, 3 = Buy Feature
CARD_SYSTEM_ENABLED = True
CARD_SYSTEM_IS_NEWBIE = False
RUN_ALL_COMBINATIONS = True

MODE_NORMALBET = 0
MODE_FEATUREBUY = 3
SUPPORTED_BET_MODES = (MODE_NORMALBET, MODE_FEATUREBUY)
BUY_MODES: tuple[int, ...] = (MODE_FEATUREBUY,)
MODE_KEY = {MODE_NORMALBET: "normal", MODE_FEATUREBUY: "buy_feature"}
CARD_KEY = {MODE_NORMALBET: "base_game", MODE_FEATUREBUY: "buy_feature"}

_NB = {"config_file": "config_01A.js", "tier": "AUTO", "bet_mode": 0, "card_system_enabled": True,
       "card_system_is_newbie": False, "base_bet": 2}
_BF = dict(_NB, bet_mode=3)
_NEW = {"card_system_is_newbie": True}

PRESETS: dict[str, list[dict[str, Any]]] = {
    # --- 1. 測試：Card System On，10^5 ---
    "test": [dict(m, total_rounds=10**5) for m in (_NB, _BF)],
    # --- 2. 自然機率：Card System Off（原作工作簿 NB 10^8、FB 5.01×10^7）---
    "natural": [dict(_NB, total_rounds=10**8, card_system_enabled=False),
                dict(_BF, total_rounds=10**7, card_system_enabled=False)],
    # --- 3. 01 原作卡片驗證：97A_Bet1（$1）／97A_Bet2（$2）× 老手 NB／BF，新手固定 97A_Bet2 ---
    "card01_quick": [dict(m, tier=t, base_bet=b, total_rounds=10**6) for t, b in (("97A_Bet1", 1), ("97A_Bet2", 2)) for m in (_NB, _BF)]
                    + [dict(m, **_NEW, tier="97A_Bet2", total_rounds=10**6) for m in (_NB, _BF)],
    "card01": [dict(m, tier=t, base_bet=b, total_rounds=10**7) for t, b in (("97A_Bet1", 1), ("97A_Bet2", 2)) for m in (_NB, _BF)]
              + [dict(m, **_NEW, tier="97A_Bet2", total_rounds=10**7) for m in (_NB, _BF)],
}
BATCH_RUNS = PRESETS["test"]

THREADS = max(1, min(24, os.cpu_count() or 1))
OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = True
RUN_SINGLE_SPIN_DEBUG = False
DEBUG_ROUNDS = 1
CARD_RETRY_LIMIT = 10_000
JACKPOT_ENABLED = False         # Config 無彩金參數，無作用
RNG_SEED = 40_040
COIN_BASE = 100.0
PAY_SCALE = 10                  # 賠率含 0.4，核心以 ×10 整數計算

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
        raise FileNotFoundError(f"找不到 {path.name}，請在 H040 專案資料夾執行")
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
    if data.get("game_id") != "H040" or base.get("game_id") != "H040":
        raise ValueError("config 的 game_id 必須為 H040")
    return cfg


def wager_for_mode(base: dict[str, Any], mode: int, base_bet: float) -> float:
    return base_bet * float(base["bet_modes"][MODE_KEY[mode]]["cost_multiplier"])


def bet_tier_name(tier_amount: float, base_bet: float) -> str:
    if round(tier_amount * 100) <= 100:
        return "small_bet"
    if round(base_bet * 100) > 30_000:
        return "big_bet"
    return "medium_bet"


def tier_amount_for_mode(mode: int, base_bet: float, amount: float) -> float:
    """NB：實際押注；BF：購買價 ÷ Feature Price 倍數＝基礎押注（數學模型規範 1.7.1）。"""
    return base_bet if mode in BUY_MODES else amount


def load_batch_configs(combo: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    data = load_js_config(BASE_DIR / combo["config_file"])
    base = data["base"]
    mode = int(combo["bet_mode"])
    bet = float(combo["base_bet"])
    amount = wager_for_mode(base, mode, bet)
    tier_amount = tier_amount_for_mode(mode, bet, amount)
    bt = bet_tier_name(tier_amount, bet)
    tier = combo["tier"]
    if tier == "AUTO":
        if combo["card_system_is_newbie"]:
            tier = NEWBIE_TIER.format(s=data["series"])
        else:
            tier = TIER_CODE[bt].format(s=data["series"])
        print(f"[auto] bet_mode {mode}、base_bet {bet:g}（檔位金額 ${tier_amount:g}）→ {tier}")
    return data, expand_tier(data, tier), tier, bt


def _cum(weights: list[int]) -> np.ndarray:
    if any(int(w) < 0 for w in weights):
        raise ValueError("權重不得為負")
    return np.cumsum(np.array(weights, np.int64))


def pack_tables(cfg: dict[str, Any], mode: int, newbie: bool) -> dict[str, Any]:
    """把 Config 轉成 Numba 核心使用的固定型別陣列。"""
    tkey = cfg["bet_modes"][MODE_KEY[mode]].get("entry_table", "bg_1")
    tbl = cfg["tables"][tkey]
    L = max(len(r) for r in tbl["reels"])
    reel_sym = np.full((3, L), -1, np.int64)
    reel_len = np.zeros(3, np.int64)
    reel_cum = np.zeros((3, L), np.int64)
    for r in range(3):
        reel_len[r] = len(tbl["reels"][r])
        reel_sym[r, :reel_len[r]] = tbl["reels"][r]
        if len(tbl["symbol_weight"][r]) != reel_len[r]:
            raise ValueError(f"{tkey}.symbol_weight[{r}] 長度與輪帶不符")
        c = _cum(tbl["symbol_weight"][r])
        if c[-1] <= 0:
            raise ValueError(f"{tkey}.symbol_weight[{r}] 權重總和為 0")
        reel_cum[r, :len(c)] = c
        reel_cum[r, len(c):] = c[-1]
    wild = int(cfg["wild_ids"][0])
    lines = np.array(cfg["paylines"], np.int64)
    n_sym = max(int(k) for k in cfg["symbol_names"]) + 1
    pay10 = np.zeros(n_sym, np.int64)
    for k, v in cfg["pays"].items():
        pay10[int(k)] = round(float(v[0]) * PAY_SCALE)
    ff = cfg["football_feature"]
    fp = ff[MODE_KEY[mode]]
    scripts = np.array(ff["scripts"], np.int64)
    if scripts.shape[1] != int(ff["rounds"]):
        raise ValueError("football_feature.scripts 每列長度必須等於 rounds")
    if len(fp["script_weights"]) != scripts.shape[0]:
        raise ValueError("script_weights 長度必須等於 scripts 數量")
    script_cum = _cum(fp["script_weights"])
    for s, w in zip(ff["scripts"], fp["script_weights"]):
        if w > 0 and not any(x > 0 for x in s):
            raise ValueError("有權重的腳本至少要有一球成功")
    sets = fp["multiplier_sets"]
    if any(len(s) != int(ff["goal_slots"]) for s in sets):
        raise ValueError("multiplier_sets 每組長度必須等於 goal_slots")
    if any(float(x) != int(x) for s in sets for x in s):
        raise ValueError("multiplier_sets 必須為整數倍數（本程式以整數計算）")
    mult_sets = np.array(sets, np.int64)
    pick = fp["pick_weights"]
    if len(pick) != int(scripts.max()):
        raise ValueError("pick_weights 組數必須等於腳本最大結果類型")
    pick_cum = np.array([_cum(w) for w in pick], np.int64)
    profile = "newbie" if newbie else "oldhand"
    deck = cfg["card_system"]["profiles"][profile][CARD_KEY[mode]]
    card_lo = np.array([c["min"] for c in deck], np.int64)
    card_hi = np.array([c["max"] for c in deck], np.int64)
    card_cum = _cum([c["weight"] for c in deck])
    buy = 1 if mode in BUY_MODES else 0
    return {"arrays": (reel_sym, reel_len, reel_cum, lines, pay10, wild, scripts, script_cum, mult_sets, pick_cum,
                       buy, card_lo, card_hi, card_cum),
            "deck": deck, "card_profile": profile, "table": tkey}


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
def _spin(reel_sym, reel_len, reel_cum, lines, pay10, wild, out, sym_hit, sym_pay):
    """單次盤面。out = [line10, trigger, line_hits, ww_visible]；sym_hit／sym_pay 為本把各符號線數與線獎。"""
    grid = np.empty((3, 3), np.int64)
    ww = 0
    for r in range(3):
        stop = _draw(reel_cum[r, :reel_len[r]])
        for row in range(3):
            s = reel_sym[r, (stop + row) % reel_len[r]]
            grid[row, r] = s
            if s == wild:
                ww = 1
    for s in range(sym_hit.shape[0]):
        sym_hit[s] = 0
        sym_pay[s] = 0
    line10 = 0
    hits = 0
    trig = 0
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
            if a == wild or b == wild or c == wild:
                trig = 1
        line10 += best
    out[0] = line10
    out[1] = trig
    out[2] = hits
    out[3] = ww


@njit(nogil=True)
def _feature(scripts, script_cum, mult_sets, pick_cum, fres):
    """足球特色：回傳累積倍數；fres[0]＝腳本索引，fres[1..5]＝每球倍數（0＝失敗），fres[6..10]＝每球抽到的倍數組。"""
    si = _draw(script_cum)
    fres[0] = si
    m = 1
    n_set = mult_sets.shape[0]
    for k in range(scripts.shape[1]):
        t = scripts[si, k]
        st = np.random.randint(0, n_set)
        fres[6 + k] = st
        if t > 0:
            v = mult_sets[st, _draw(pick_cum[t - 1])]
            fres[1 + k] = v
            m *= v
        else:
            fres[1 + k] = 0
    return m


@njit(nogil=True)
def _play(reel_sym, reel_len, reel_cum, lines, pay10, wild, scripts, script_cum, mult_sets, pick_cum, buy,
          out, so, sym_hit, sym_pay, fres):
    """一次完整結果（Card 每次 Retry 重跑這個）。out = [win10, line10, trigger, line_hits, ww_visible, mult, entry_spins]。
    BF：用 bf_1 停輪權重重轉到觸發足球特色為止（保險上限 10^6 次）。"""
    entry = 0
    while True:
        _spin(reel_sym, reel_len, reel_cum, lines, pay10, wild, so, sym_hit, sym_pay)
        entry += 1
        if buy == 0 or so[1] == 1 or entry >= 1_000_000:
            break
    m = 1
    if so[1] == 1:
        m = _feature(scripts, script_cum, mult_sets, pick_cum, fres)
        win10 = so[0] * m
    else:
        win10 = so[0]
    out[0] = win10
    out[1] = so[0]
    out[2] = so[1]
    out[3] = so[2]
    out[4] = so[3]
    out[5] = m
    out[6] = entry


@njit(nogil=True)
def _in_card(win10, lo, hi):
    if lo == -1:
        return win10 == 0
    return lo * 10 < win10 <= hi * 10


@njit(nogil=True)
def run_worker(seed, rounds, card_on, retry_limit, thresholds,
               reel_sym, reel_len, reel_cum, lines, pay10, wild, scripts, script_cum, mult_sets, pick_cum, buy,
               card_lo, card_hi, card_cum, cost):
    np.random.seed(seed)
    n_th = thresholds.shape[0]
    n_card = card_cum.shape[0]
    n_sym = pay10.shape[0]
    n_round = scripts.shape[1]
    # 0 win10, 1 hit_rounds, 2 max_win10, 3 bg_pay10(未觸發), 4 feature_cnt, 5 feature_pay10, 6 retry_total,
    # 7 retry_exceeded, 8 feature_base10(觸發局盤面贏分), 9 ww_visible_cnt, 10 entry_spins, 11 line_hit_rounds,
    # 12 max_mult, 13 line10_sum
    sc = np.zeros(14, np.int64)
    fsum = np.zeros(2, np.float64)      # 0 sumsq（÷ cost）, 1 累積倍數合計
    round_type = np.zeros((n_round, 4), np.int64)
    succ_cnt = np.zeros(n_round + 1, np.int64)
    bucket_cnt = np.zeros(n_th, np.int64)
    bucket_pay = np.zeros(n_th, np.int64)
    mult_bucket = np.zeros(n_th, np.int64)
    card_draw = np.zeros(n_card, np.int64)
    card_retry = np.zeros(n_card, np.int64)
    sym_hits = np.zeros(n_sym, np.int64)
    sym_pays = np.zeros(n_sym, np.int64)
    sh = np.zeros(n_sym, np.int64)
    sp = np.zeros(n_sym, np.int64)
    out = np.zeros(7, np.int64)
    so = np.zeros(4, np.int64)
    fres = np.zeros(11, np.int64)
    for _ in range(rounds):
        iv = -1
        if card_on:
            iv = _draw(card_cum)
            card_draw[iv] += 1
        tries = 0
        while True:
            _play(reel_sym, reel_len, reel_cum, lines, pay10, wild, scripts, script_cum, mult_sets, pick_cum, buy,
                  out, so, sh, sp, fres)
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
        sc[0] += win10
        if win10 > 0:
            sc[1] += 1
        if win10 > sc[2]:
            sc[2] = win10
        sc[9] += out[4]
        sc[10] += out[6]
        sc[13] += line10
        if line10 > 0:
            sc[11] += 1
            for s in range(n_sym):
                sym_hits[s] += sh[s]
                sym_pays[s] += sp[s]
        if out[2] == 1:
            sc[4] += 1
            sc[5] += win10
            sc[8] += line10
            m = out[5]
            fsum[1] += m
            if m > sc[12]:
                sc[12] = m
            ns = 0
            si = fres[0]
            for k in range(n_round):
                t = scripts[si, k]
                round_type[k, t] += 1
                if t > 0:
                    ns += 1
            succ_cnt[ns] += 1
            for h in range(n_th):
                if m <= thresholds[h]:
                    mult_bucket[h] += 1
                    break
        else:
            sc[3] += win10
        x = win10 / 10.0 / cost
        fsum[0] += x * x
        for h in range(n_th):
            if win10 <= thresholds[h] * 10:
                bucket_cnt[h] += 1
                bucket_pay[h] += win10
                break
    return (sc, fsum, round_type, succ_cnt, bucket_cnt, bucket_pay, mult_bucket, card_draw, card_retry,
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
    keys = ("sc", "fsum", "round_type", "succ_cnt", "bucket_cnt", "bucket_pay", "mult_bucket", "card_draw",
            "card_retry", "sym_hits", "sym_pays")
    merged = {k: sum(r[i] for r in results) for i, k in enumerate(keys)}
    merged["sc"][2] = max(int(r[0][2]) for r in results)
    merged["sc"][12] = max(int(r[0][12]) for r in results)
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
    var = st["fsum"][0] / rounds - mean_x * mean_x
    std = math.sqrt(max(var, 0.0))
    return {"coin_in_total": coin_in, "rtp_game": win / coin_in, "rtp_bg": sc[3] / PAY_SCALE * bet / coin_in,
            "rtp_fg": sc[5] / PAY_SCALE * bet / coin_in, "std": std, "se": std / math.sqrt(rounds)}


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
    buy = res["bet_mode"] in BUY_MODES
    sections = [
        [("game_name", res["cfg"]["name_zh"]), ("game_id", res["cfg"]["online_game_id"])],
        [("config_file", res["combo"]["config_file"]), ("tier", res["tier"]),
         ("math_version", res["cfg"]["excel_version"] if res["card_on"] else res["cfg_base_version"]),
         ("card_system", "on" if res["card_on"] else "off")],
        [("bet_mode", res["mode_name"]), ("bet_multi", f"{cost:g}" if not buy else "1"),
         ("feature_price_multiplier", f"{cost:g}" if buy else "n/a"),
         ("base_bet", f"{bet:.2f}"), ("bet_amount", f"{bet * cost:.2f}"), ("bet_tier_amount", f"{res['tier_amount']:.2f}"),
         ("bet_tier", res["bet_tier"]), ("jackpot", "off"), ("coin_in", f"{bet * cost:.2f}"),
         ("total_rounds", _int(rounds)), ("duration", f"{res['duration']:05.2f} sec")],
        [("rtp_total", _pct(m["rtp_game"])), ("rtp_link", "n/a"), ("rtp_bonus", "n/a"),
         ("rtp_game", _pct(m["rtp_game"])), ("rtp_bg", _pct(m["rtp_bg"])), ("rtp_fg", _pct(m["rtp_fg"])),
         ("hit_rate_bg", _pct(sc[1] / rounds)), ("hit_rate_fg", "n/a"), ("fg_trigger_rate", _pct(sc[4] / rounds)),
         ("retrigger_trigger_rate", "n/a"), ("avg_fg_spins", "5.00" if sc[4] else "n/a")],
        [("bg_trigger_fg_cnt", _int(sc[4])), ("bg_trigger_fg_pay", f"{sc[8] / PAY_SCALE * bet:,.2f}"),
         ("special_symbol_cnt", _int(sc[9])),
         ("SCR", _int(round(sc[9] / rounds * 10_000_000_000)) if rounds else "0")],
        [("max_win_x", f"{sc[2] / PAY_SCALE / cost:,.2f} x"), ("capped_rounds", "0"),
         ("volatility_std", f"{m['std']:05.2f}"), ("volatility_std_fg", "n/a"), ("standard_error", f"{m['se']:05.2f}")],
    ]
    if res["card_on"]:
        sections.append([("card_system_profile", res["card_profile"]), ("card_retry_limit", str(CARD_RETRY_LIMIT)),
                         ("retry_total", _int(sc[6])), ("avg_retry", f"{sc[6] / rounds:05.2f}")])
        sections.append([("retry_limit_exceeded", _int(sc[7])), ("retry_limit_bg_range", _int(sc[7]) if not buy else "0"),
                         ("retry_limit_bg_freegame", "0"), ("retry_limit_fg", _int(sc[7]) if buy else "0")])
    return sections


def game_info_rows(res: dict[str, Any]) -> list[tuple[str, str]]:
    st = res["stats"]
    sc = st["sc"]
    rounds = st["rounds"]
    coin = res["metrics"]["coin_in_total"]
    bet = res["bet"]
    fc = max(1, int(sc[4]))
    rows = [("line_hit_rate", _pct(sc[11] / rounds, 6)),
            ("line_rtp_no_multiplier", _pct(sc[13] / PAY_SCALE * bet / coin, 6)),
            ("feature_rate", _pct(sc[4] / rounds, 6)),
            ("feature_cycle", f"{rounds / sc[4]:.2f}" if sc[4] else "n/a"),
            ("feature_rtp", _pct(sc[5] / PAY_SCALE * bet / coin, 6)),
            ("feature_base_rtp", _pct(sc[8] / PAY_SCALE * bet / coin, 6)),
            ("avg_feature_base_x", f"{sc[8] / PAY_SCALE / fc:.4f}"),
            ("avg_feature_multiplier", f"{st['fsum'][1] / fc:.4f}"),
            ("avg_feature_win_x", f"{sc[5] / PAY_SCALE / fc:.4f}"),
            ("max_feature_multiplier", f"{int(sc[12]):,}"),
            ("ww_visible_rate", _pct(sc[9] / rounds, 6)),
            ("avg_entry_spins", f"{sc[10] / rounds:.4f}")]
    for n in range(len(st["succ_cnt"])):
        rows.append((f"feature_success_{n}_share", _pct(st["succ_cnt"][n] / fc)))
    for k in range(st["round_type"].shape[0]):
        rows.append((f"round{k + 1}_success_rate", _pct(1 - st["round_type"][k, 0] / fc)))
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
    buy = res["bet_mode"] in BUY_MODES
    cnt_key, pay_key = ("buy_feature_cnt", "buy_feature_pay") if buy else ("base_game_cnt", "base_game_pay")
    rows = []
    for i, upper in enumerate(MULTIPLIER_THRESHOLDS):
        interval = "0" if i == 0 else f"{float(MULTIPLIER_THRESHOLDS[i - 1]):.1f} < X <= {float(upper):.1f}"
        rows.append({"Interval": interval, cnt_key: int(st["bucket_cnt"][i]),
                     pay_key: st["bucket_pay"][i] / PAY_SCALE * res["bet"], "Interval_Upper": upper})
    return pd.DataFrame(rows)


def feature_frame(res: dict[str, Any]) -> pd.DataFrame:
    st = res["stats"]
    sc = st["sc"]
    rows = [("feature_cnt", int(sc[4])), ("feature_base_pay_x", sc[8] / PAY_SCALE), ("feature_pay_x", sc[5] / PAY_SCALE),
            ("ww_visible_cnt", int(sc[9])), ("entry_spins", int(sc[10]))]
    for n, v in enumerate(st["succ_cnt"]):
        rows.append((f"success_{n}_cnt", int(v)))
    for k in range(st["round_type"].shape[0]):
        for t in range(st["round_type"].shape[1]):
            rows.append((f"round{k + 1}_type{t}_cnt", int(st["round_type"][k, t])))
    prev = 0
    for i, upper in enumerate(MULTIPLIER_THRESHOLDS):
        if i == 0:
            continue
        rows.append((f"final_multiplier_{prev}_{upper}_cnt", int(st["mult_bucket"][i])))
        prev = upper
    return pd.DataFrame(rows, columns=["Index", "Value"])


def symbol_frame(res: dict[str, Any]) -> pd.DataFrame:
    st = res["stats"]
    names = res["cfg"]["symbol_names"]
    hits = st["sym_hits"]
    pays = st["sym_pays"]
    th, tp = max(1, int(hits.sum())), max(1, int(pays.sum()))
    rows = []
    for s in range(len(hits)):
        rows.append({"symbol_id": s, "symbol": names[str(s)], "line_hits": int(hits[s]), "hit_share": hits[s] / th,
                     "pay_no_multiplier": pays[s] / PAY_SCALE * res["bet"], "pay_share": pays[s] / tp, "hits_3": int(hits[s])})
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
    gid = res["cfg"]["game_id"]  # H040197A（含 Variant）
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
        raise ValueError(f"不支援的 bet_mode {combo['bet_mode']}；本作只有 0（NB）／3（BF）")
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
    res = {"combo": combo, "cfg": cfg, "cfg_base_version": data["base"]["excel_version"], "base_parsheet_id": data["base"]["parsheet_id"],
           "tier": tier if card_on else "base", "bet_tier": bt, "bet_mode": mode, "bet": bet, "cost": cost,
           "tier_amount": tier_amount_for_mode(mode, bet, bet * cost), "card_on": card_on, "card_profile": packed["card_profile"],
           "deck": packed["deck"], "mode_name": cfg["bet_modes"][MODE_KEY[mode]]["name"], "stats": stats, "duration": duration}
    res["metrics"] = calculated_metrics(res)
    if SHOW_CONSOLE_SUMMARY:
        print_console(res)
    if OUTPUT_REPORT:
        print(f"report -> {output_report(res)}")
        print()
    return res


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="H040 黃金射門 simulator")
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
    p.add_argument("--series", choices=["A"], default=None)
    return p.parse_args()


def debug_round(combo: dict[str, Any]) -> None:
    """單執行緒逐局除錯：印出每局得分與足球特色倍數。"""
    data, cfg, tier, bt = load_batch_configs(combo)
    mode = int(combo["bet_mode"])
    packed = pack_tables(cfg, mode, bool(combo["card_system_is_newbie"]))
    th = np.array(MULTIPLIER_THRESHOLDS, np.int64)
    cost = float(cfg["bet_modes"][MODE_KEY[mode]]["cost_multiplier"])
    for k in range(DEBUG_ROUNDS):
        r = run_worker(RNG_SEED + k, 1, bool(combo["card_system_enabled"]), CARD_RETRY_LIMIT, th, *packed["arrays"], cost)
        sc = r[0]
        print(f"round {k + 1}: win {sc[0] / PAY_SCALE:g}x base bet, line {sc[13] / PAY_SCALE:g}x, feature {int(sc[4])}, "
              f"multiplier {int(sc[12])}, retry {int(sc[6])}")


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
