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
* 同一天所有玩家同步轉動：每個觸發點先把到此為止的提撥入池，
  再以隨機順序逐筆處理該觸發點的救援。
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
    MAIN_SHORT_WINDOW, SYSTEM_VERSION, ext_rewards, load_rowdata,
)

GAME = "彩罐熱舞"
LEVY = 0.05
PLAYERS_PER_DAY = 10_000
DAYS = 30
SPIN_SCENARIOS = [400, 800, 1000]
SEED = 20261005


def judge(cp: int, adj: np.ndarray, bet: np.ndarray, cum_adj: np.ndarray, cum_bet: np.ndarray,
          rng: np.random.Generator):
    """回傳 (是否觸發, 救援倍數)；只看第 cp 轉之前的狀態。"""
    i = cp - 1
    if cp in CHECKPOINT_RULES:
        th, rw = CHECKPOINT_RULES[cp]
        ss = max(0, i - MAIN_SHORT_WINDOW)
        short = adj[:, ss:i].sum(axis=1) / bet[:, ss:i].sum(axis=1)
        return (cum_adj / cum_bet < th) & (short < MAIN_SHORT_THRESHOLD), rw
    mid = adj[:, i - EXT_MID_WINDOW:i].sum(axis=1) / bet[:, i - EXT_MID_WINDOW:i].sum(axis=1)
    short = adj[:, i - EXT_SHORT_WINDOW:i].sum(axis=1) / bet[:, i - EXT_SHORT_WINDOW:i].sum(axis=1)
    hit = (mid < EXT_MID_THRESHOLD) & (short < EXT_SHORT_THRESHOLD)
    return hit, ext_rewards(hit, rng)


def run(nat_all: np.ndarray, bet_all: np.ndarray, n_spins: int, rng: np.random.Generator) -> dict:
    cps = [c for c in CHECKPOINTS + EXT_CHECKPOINTS if c <= n_spins]
    balance = 0.0
    tot = dict(bet=0.0, nat=0.0, paid=0.0, want=0.0, hits=0, denied=0)
    day1_denied_rate = None

    for day in range(DAYS):
        rows = rng.integers(0, nat_all.shape[0], PLAYERS_PER_DAY)
        nat = nat_all[rows, :n_spins]
        bet = bet_all[rows, :n_spins]
        adj = nat.copy()
        cum_adj = np.zeros(PLAYERS_PER_DAY)
        cum_bet = np.zeros(PLAYERS_PER_DAY)
        prev = 0
        day_hits = day_denied = 0
        for cp in cps:
            seg = slice(prev, cp - 1)
            balance += LEVY * bet[:, seg].sum()          # 判定轉之前的提撥先入池
            cum_adj += adj[:, seg].sum(axis=1)
            cum_bet += bet[:, seg].sum(axis=1)

            hit, rw = judge(cp, adj, bet, cum_adj, cum_bet, rng)
            i = cp - 1
            inc = np.where(hit, np.maximum(nat[:, i], rw * bet[:, i]) - nat[:, i], 0.0)
            tot["want"] += inc.sum()
            for p in rng.permutation(np.flatnonzero(inc > 0)):
                if balance >= inc[p]:
                    balance -= inc[p]
                    adj[p, i] = nat[p, i] + inc[p]
                    tot["paid"] += inc[p]
                else:
                    day_denied += 1
            day_hits += int(hit.sum())

            balance += LEVY * bet[:, i].sum()            # 判定轉本身的提撥
            cum_adj += adj[:, i]
            cum_bet += bet[:, i]
            prev = cp
        balance += LEVY * bet[:, prev:].sum()            # 最後一個觸發點之後的提撥

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
