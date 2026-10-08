# -*- coding: utf-8 -*-
"""救援池（共同池）模擬。

老手救援 C-2 的救援全部由同一個共同池支付：
* 每轉提撥該轉押注的 5% 進池。
* 判定成功時，救援成本（救援後得分 − 自然得分）從池扣款；
  池餘額不足以支付該筆成本 → 這次不救援（硬性上限）。
* 池跨日累積，判定與觸發仍以天為循環。

模擬設定：
* 每天 10,000 名玩家，每人當日固定玩 N 轉；每天從 rowdata（10,000 人 × 1,000 轉）
  有放回抽 10,000 列當作當天的自然結果。
* 同一天所有玩家同步轉動：每個判定區間開始前先把提撥入池，
  再以隨機順序逐筆處理該區間的救援（主救援觸發點前後 5 轉隨機判定）。
* 救援規則直接沿用 simulator_system_oldhand_c2（主救援 40–400、延伸救援 440–1,000）。
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from simulator_system_oldhand_c2 import (  # noqa: E402
    CHECKPOINT_RULES, CHECKPOINTS, EXT_CHECKPOINTS, EXT_MID_THRESHOLD, EXT_MID_WINDOW,
    EXT_SHORT_THRESHOLD, EXT_SHORT_WINDOW, MAIN_SHORT_THRESHOLD,
    MAIN_SHORT_WINDOW, SYSTEM_VERSION, CHECKPOINT_JITTER, ext_rewards, judge_spins, load_rowdata,
)

GAME = "彩罐熱舞"
LEVY = 0.05
PLAYERS_PER_DAY = 10_000
DAYS = 30
SPIN_SCENARIOS = [400, 800, 1000]
SEED = 20261005


def run(nat_all: np.ndarray, bet_all: np.ndarray, n_spins: int, rng: np.random.Generator) -> dict:
    balance = 0.0
    tot = dict(bet=0.0, nat=0.0, paid=0.0, want=0.0, hits=0, denied=0)
    day1_denied_rate = None
    n = PLAYERS_PER_DAY
    idx = np.arange(n)
    events = [(cp, "main") for cp in CHECKPOINTS] + [(cp, "ext") for cp in EXT_CHECKPOINTS]

    for day in range(DAYS):
        rows = rng.integers(0, nat_all.shape[0], n)
        nat = nat_all[rows, :n_spins]
        bet = bet_all[rows, :n_spins]
        adj = nat.copy()
        spins = judge_spins(n, rng)
        levied = 0                                       # 已入池的轉數（0-based，不含）
        day_hits = day_denied = 0
        for cp, kind in events:
            # 判定區間開始前的提撥先入池；主救援區間為觸發點前後 5 轉
            start = cp - CHECKPOINT_JITTER - 1 if kind == "main" else cp - 1
            end = cp + CHECKPOINT_JITTER if kind == "main" else cp
            if start >= n_spins:
                break
            balance += LEVY * bet[:, levied:start].sum()
            levied = start

            zeros = np.zeros((n, 1))
            cs_a = np.concatenate([zeros, np.cumsum(adj, axis=1)], axis=1)
            cs_b = np.concatenate([zeros, np.cumsum(bet, axis=1)], axis=1)
            if kind == "main":
                th, reward = CHECKPOINT_RULES[cp]
                s = spins[cp]
                played = s <= n_spins
                k = np.minimum(s, n_spins) - 1
                lo = np.maximum(0, k - MAIN_SHORT_WINDOW)
                cum = cs_a[idx, k] / cs_b[idx, k]
                short = (cs_a[idx, k] - cs_a[idx, lo]) / (cs_b[idx, k] - cs_b[idx, lo])
                hit = played & (cum < th) & (short < MAIN_SHORT_THRESHOLD)
                rw = np.full(n, reward)
            else:
                k = np.full(n, cp - 1)
                i = cp - 1
                mid = (cs_a[:, i] - cs_a[:, i - EXT_MID_WINDOW]) / (cs_b[:, i] - cs_b[:, i - EXT_MID_WINDOW])
                short = (cs_a[:, i] - cs_a[:, i - EXT_SHORT_WINDOW]) / (cs_b[:, i] - cs_b[:, i - EXT_SHORT_WINDOW])
                hit = (mid < EXT_MID_THRESHOLD) & (short < EXT_SHORT_THRESHOLD)
                rw = ext_rewards(hit, rng)

            natural = nat[idx, k]
            inc = np.where(hit, np.maximum(natural, rw * bet[idx, k]) - natural, 0.0)
            tot["want"] += inc.sum()
            for p in rng.permutation(np.flatnonzero(inc > 0)):
                if balance >= inc[p]:
                    balance -= inc[p]
                    adj[p, k[p]] = natural[p] + inc[p]
                    tot["paid"] += inc[p]
                else:
                    day_denied += 1
            day_hits += int(hit.sum())

            end = min(end, n_spins)                      # 判定區間內的提撥
            balance += LEVY * bet[:, levied:end].sum()
            levied = end
        balance += LEVY * bet[:, levied:].sum()          # 最後一個判定之後的提撥

        tot["bet"] += bet.sum()
        tot["nat"] += nat.sum()
        tot["hits"] += day_hits
        tot["denied"] += day_denied
        if day == 0:
            day1_denied_rate = day_denied / max(day_hits, 1)

    return dict(
        base=tot["nat"] / tot["bet"],
        want=tot["want"] / tot["bet"],
        paid=tot["paid"] / tot["bet"],
        denied=tot["denied"] / max(tot["hits"], 1),
        day1_denied=day1_denied_rate,
        end_balance=balance / PLAYERS_PER_DAY,
    )


def main() -> None:
    nat_all, bet_all = load_rowdata(GAME)
    print(f"=== 救援池模擬（{GAME}，{SYSTEM_VERSION}，每天 {PLAYERS_PER_DAY:,} 人 × {DAYS} 天，提撥 {LEVY:.0%}，起始餘額 0）===")
    print(f"{'當日轉數':>6}{'無機制RTP':>11}{'不設上限增量':>12}{'實際發放增量':>12}{'實際總RTP':>11}"
          f"{'首日不救率':>10}{'30天不救率':>11}{'期末餘額/人':>12}")
    for n_spins in SPIN_SCENARIOS:
        r = run(nat_all, bet_all, n_spins, np.random.default_rng(SEED))
        print(f"{n_spins:>6}轉{r['base'] * 100:>10.2f}%{r['want'] * 100:>+11.2f}%{r['paid'] * 100:>+11.2f}%"
              f"{(r['base'] + r['paid']) * 100:>10.2f}%{r['day1_denied'] * 100:>9.2f}%{r['denied'] * 100:>10.2f}%"
              f"{r['end_balance']:>10.1f} bet")


if __name__ == "__main__":
    main()
