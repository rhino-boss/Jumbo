# -*- coding: utf-8 -*-
"""老手救援 C-2 換模式套利檢查（NB／EB 參數不同時）。

資料：宙斯 2500（H027）92A v7.4.0.0 Oldhand 中 Bet（$2）NB／EB 每轉倍數分布
（rowdata/宙斯_92A_中Bet_NB_EB_分布.json，取自 1 億轉 Record 報表）。
NB 與 EB 在同一押注層級的總押注相同（$2），所以切換模式不會觸發押注檢查。

判定規則（現行規格）：
* 主救援觸發點 t = 40, 80, …, 400；判定轉在 t+1～t+5 均勻隨機。
* 40 轉一桶：條件 1 看最近 1 桶 RTP < 50%；條件 2 看所有完成的桶（≤ 10 桶）RTP < 門檻。
* 命中後最終得分 = max(自然得分, 救援倍數)；救援倍數取卡片區間上限（保守估計）。
* 一天 405 轉（含最後一個判定區間），不套救援池上限。

各模式先各自調到救援 RTP（救援成本 ÷ 總押注）= 1.00% ± 0.02%，參數取實際可設定的值：
* 門檻調法：救援倍數不變，條件 2 的 10 段門檻乘同一個係數後取整數 %，再逐段 ±1% 微調。
* 強度調法：門檻不變，10 段救援倍數乘同一個係數後對齊卡片區間上限，再逐段移一格微調。
每次模擬最多 100 萬轉（預設 2,400 人 × 405 轉 = 972,000 轉），到模擬機執行。

換模式玩家：平常玩 base 模式；每個觸發點後的 5 轉，先看已完成的桶，
哪個模式的條件成立且救援倍數較大就玩那個模式（都不成立就照玩 base）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DIST_FILE = HERE / "rowdata" / "宙斯_92A_中Bet_NB_EB_分布.json"

PLAYERS = int(sys.argv[1]) if len(sys.argv) > 1 else 2_400
DAY_SPINS = 405
assert PLAYERS * DAY_SPINS <= 1_000_000, "每次模擬最多 100 萬轉"
TOLERANCE = 0.0002
# 卡片倍率區間上限（數學模型規範第 1.8 節）
CARD_UPPERS = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100], dtype=float)
BUCKET = 40
TRIGGERS = list(range(40, 401, 40))
COND1 = 0.50
BASE_TH = np.array([0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.55, 0.60, 0.65])
BASE_REWARD = np.array([25, 50, 70, 80, 90, 100, 100, 100, 100, 100], dtype=float)
TARGET = 0.01
SEED = 20261105


def load_modes():
    data = json.loads(DIST_FILE.read_text(encoding="utf-8"))
    return {m: (np.array(v["values"]), np.array(v["probs"]) / sum(v["probs"]), v["rtp"]) for m, v in data["modes"].items()}


def draw(values, probs, shape, rng):
    idx = np.searchsorted(np.cumsum(probs), rng.random(shape), side="right")
    return values[np.minimum(idx, len(values) - 1)].astype(np.float32)


def play(nat, judge, params, base, switch):
    """nat[mode] = (players, DAY_SPINS) 自然倍數；params[mode] = (th[10], reward[10])。
    回傳 (總自然得分, 總救援成本)，押注每轉 1。"""
    n = judge.shape[0]
    rows = np.arange(n)
    bucket_sum = np.zeros((n, DAY_SPINS // BUCKET + 1))
    nat_total = 0.0
    cost_total = 0.0
    mode = np.full(n, base)
    modes = list(nat)
    for s in range(1, DAY_SPINS + 1):
        j = (s - 1) // BUCKET  # 目前這轉所屬的桶（0-based）
        k = (s - 1) % BUCKET   # 桶內第幾轉（0-based）；k = 0..4 是觸發點後的 5 轉
        tidx = j - 1           # 對應的觸發點序號（觸發點 = 40 * j）
        in_window = 0 <= tidx < len(TRIGGERS) and k < 5
        if in_window and k == 0:
            last = bucket_sum[:, j - 1] / BUCKET
            done = bucket_sum[:, max(0, j - 10):j].sum(axis=1) / (BUCKET * min(j, 10))
            best = np.full(n, -1.0)
            choice = np.full(n, base)
            cand = modes if switch else [base]
            for m in cand:
                th, rw = params[m]
                ok = (last < COND1) & (done < th[tidx])
                better = ok & (rw[tidx] > best)
                best = np.where(better, rw[tidx], best)
                choice = np.where(better, m, choice)
            mode = choice
        cur = mode if in_window else np.full(n, base)
        pay = np.zeros(n)
        for m in modes:
            sel = cur == m
            pay[sel] = nat[m][sel, s - 1]
        nat_total += pay.sum()
        if in_window:
            hit_spin = judge[:, tidx] == k
            reward = np.zeros(n)
            last = bucket_sum[:, j - 1] / BUCKET
            done = bucket_sum[:, max(0, j - 10):j].sum(axis=1) / (BUCKET * min(j, 10))
            for m in modes:
                th, rw = params[m]
                ok = hit_spin & (cur == m) & (last < COND1) & (done < th[tidx])
                reward = np.where(ok, rw[tidx], reward)
            final = np.maximum(pay, reward)
            cost_total += (final - pay).sum()
            pay = final
        bucket_sum[:, j] += pay
    return nat_total, cost_total


def rescue_rtp(nat, judge, params, base, switch=False):
    nt, ct = play(nat, judge, params, base, switch)
    spins = judge.shape[0] * DAY_SPINS
    return ct / spins, nt / spins


def snap_reward(values):
    """對齊最接近的卡片區間上限。"""
    return CARD_UPPERS[np.abs(CARD_UPPERS[None, :] - np.asarray(values)[:, None]).argmin(axis=1)]


def tune(nat, judge, mode, how):
    """回傳 (門檻, 救援倍數, 救援 RTP)：先掃係數取最接近 1% 的實際值，再逐段微調到 ±0.02% 內。"""
    def rtp(th, rw):
        return rescue_rtp({mode: nat[mode]}, judge, {mode: (th, rw)}, mode)[0]

    if how == "門檻":
        grid = [(np.round(BASE_TH * f * 100) / 100, BASE_REWARD.copy()) for f in np.arange(0.20, 1.0001, 0.01)]
    else:
        grid = [(BASE_TH.copy(), snap_reward(BASE_REWARD * f)) for f in np.arange(0.01, 0.30001, 0.002)]
    th, rw = min(grid, key=lambda p: abs(rtp(*p) - TARGET))
    r = rtp(th, rw)

    def moved(t, w, i, step):
        """第 i 段移一格（門檻 ±1%、倍數 ±1 個卡片區間）；超出範圍回 None。"""
        t2, w2 = t.copy(), w.copy()
        if how == "門檻":
            t2[i] = round(t2[i] + step / 100, 2)
            return (t2, w2) if t2[i] > 0 else None
        pos = int(np.where(CARD_UPPERS == w2[i])[0][0]) + step
        if not 0 <= pos < len(CARD_UPPERS):
            return None
        w2[i] = CARD_UPPERS[pos]
        return t2, w2

    for _ in range(40):
        if abs(r - TARGET) <= TOLERANCE:
            break
        # 先試單段移一格，沒有改善再試兩段一起移（一升一降可做更細的調整）
        singles = [moved(th, rw, i, s) for i in range(len(th)) for s in (-1, 1)]
        best = min(((abs(rtp(*c) - TARGET), c) for c in singles if c), key=lambda x: x[0])
        if best[0] >= abs(r - TARGET):
            pairs = []
            for i in range(len(th)):
                for s1 in (-1, 1):
                    a = moved(th, rw, i, s1)
                    for j in range(i + 1, len(th)):
                        for s2 in (-1, 1):
                            c = a and moved(a[0], a[1], j, s2)
                            if c:
                                pairs.append(c)
            best = min(((abs(rtp(*c) - TARGET), c) for c in pairs), key=lambda x: x[0])
        if best[0] >= abs(r - TARGET):
            break
        th, rw = best[1]
        r = rtp(th, rw)
    return th, rw, r


def main():
    modes = load_modes()
    rng = np.random.default_rng(SEED)
    nat = {m: draw(v, p, (PLAYERS, DAY_SPINS), rng) for m, (v, p, _) in modes.items()}
    judge = rng.integers(0, 5, size=(PLAYERS, len(TRIGGERS)))

    base_rtp = {m: rescue_rtp({m: nat[m]}, judge, {m: (BASE_TH, BASE_REWARD)}, m) for m in nat}
    tuned = {(m, how): tune(nat, judge, m, how) for m in nat for how in ("門檻", "強度")}

    scenarios = [("NB 門檻／EB 門檻", "門檻", "門檻"), ("NB 強度／EB 強度", "強度", "強度"),
                 ("NB 門檻／EB 強度", "門檻", "強度"), ("NB 強度／EB 門檻", "強度", "門檻")]
    result = {"players": PLAYERS, "day_spins": DAY_SPINS, "target": TARGET,
              "natural_rtp": {m: modes[m][2] for m in modes},
              "current_params_rescue_rtp": {m: base_rtp[m][0] for m in base_rtp},
              "tuned": {f"{m}_{how}": {"th": tuned[(m, how)][0].tolist(), "reward": tuned[(m, how)][1].tolist(), "rescue_rtp": tuned[(m, how)][2]} for (m, how) in tuned},
              "scenarios": []}
    for name, nb_how, eb_how in scenarios:
        params = {"NB": tuned[("NB", nb_how)][:2], "EB": tuned[("EB", eb_how)][:2]}
        row = {"name": name}
        for base in ("NB", "EB"):
            only, only_nat = rescue_rtp({base: nat[base]}, judge, {base: params[base]}, base)
            sw, sw_nat = rescue_rtp(nat, judge, params, base, switch=True)
            row[base] = {"only_rescue": only, "only_natural": only_nat, "switch_rescue": sw, "switch_natural": sw_nat}
        result["scenarios"].append(row)
        print(name, json.dumps(row, ensure_ascii=False), flush=True)
    out = HERE / "record" / "mode_arb_宙斯.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print("current params rescue RTP:", result["current_params_rescue_rtp"])
    for k, v in result["tuned"].items():
        print(k, f"{v['rescue_rtp']:.4%}", "門檻", [round(x * 100) for x in v["th"]], "倍數", [int(x) for x in v["reward"]])


if __name__ == "__main__":
    main()
