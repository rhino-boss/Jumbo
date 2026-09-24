# -*- coding: utf-8 -*-
"""老手救援 C-2 套利檢查模擬（主救援 40–400 轉）。

以 rowdata 的 10,000 名玩家自然結果，把每一列視為一個「玩家日」。
救援判定只看過去，與玩家何時停手無關，所以先算出整天（400 轉）
套用機制後的每轉得分，再依各套利策略決定每人停在第幾轉。

策略 RTP = Σ 停手前總得分 ÷ Σ 停手前總押注。
因為每天歸零重來，天天照同一策略玩的長期 RTP 就是這個值；
> 100% 代表可穩定套利。

門檻與倍數直接沿用 simulator_system_oldhand_c2.CHECKPOINT_RULES。
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from simulator_system_oldhand_c2 import (  # noqa: E402
    CHECKPOINT_RULES, CHECKPOINTS, MAIN_SHORT_THRESHOLD, MAIN_SHORT_WINDOW,
    SYSTEM_VERSION, load_rowdata,
)

GAME = "彩罐熱舞"
DAY_SPINS = 400          # 主救援最後一個觸發點
BIG_WIN = 50.0           # 「開出大獎就閃」的門檻倍數


def apply_mechanism(nat: np.ndarray, bet: np.ndarray):
    """回傳 (adj, reward_at)：adj 為套機制後每轉得分；reward_at[p, i] 為該轉救援倍數（0=未救）。"""
    adj = nat.copy()
    reward_at = np.zeros_like(nat)
    n = nat.shape[0]
    cum_adj = np.zeros(n)
    cum_bet = np.zeros(n)
    prev = 0
    for cp in CHECKPOINTS:
        seg = slice(prev, cp - 1)
        cum_adj += adj[:, seg].sum(axis=1)
        cum_bet += bet[:, seg].sum(axis=1)
        th, rw = CHECKPOINT_RULES[cp]
        i = cp - 1
        ss = max(0, i - MAIN_SHORT_WINDOW)
        short = adj[:, ss:i].sum(axis=1) / bet[:, ss:i].sum(axis=1)
        hit = (cum_adj / cum_bet < th) & (short < MAIN_SHORT_THRESHOLD)
        adj[:, i] = np.where(hit, np.maximum(nat[:, i], rw * bet[:, i]), nat[:, i])
        reward_at[hit, i] = rw
        cum_adj += adj[:, i]
        cum_bet += bet[:, i]
        prev = cp
    return adj, reward_at


def first_true(mask: np.ndarray, default: int) -> np.ndarray:
    """每列第一個 True 的轉數（1-based）；整列沒有則回 default。"""
    has = mask.any(axis=1)
    idx = mask.argmax(axis=1) + 1
    return np.where(has, idx, default)


def strategy_rtp(pay: np.ndarray, bet: np.ndarray, stop: np.ndarray):
    cols = np.arange(pay.shape[1])[None, :]
    keep = cols < stop[:, None]
    tp = (pay * keep).sum()
    tb = (bet * keep).sum()
    return tp / tb, (tp - tb) / pay.shape[0]


def main() -> None:
    nat, bet = load_rowdata(GAME)
    nat = nat[:, :DAY_SPINS]
    bet = bet[:, :DAY_SPINS]
    adj, reward_at = apply_mechanism(nat, bet)
    n = nat.shape[0]

    cum_rtp = np.cumsum(adj, axis=1) / np.cumsum(bet, axis=1)
    mult = adj / bet
    rescued = reward_at > 0

    scenarios: list[tuple[str, np.ndarray]] = []
    for cp in CHECKPOINTS:
        scenarios.append((f"固定玩 {cp} 轉就閃", np.full(n, cp)))
    scenarios += [
        ("拿到任何救援就閃（否則玩到 400）", first_true(rescued, DAY_SPINS)),
        ("只等 100× 救援才閃（否則玩到 400）", first_true(reward_at >= 100, DAY_SPINS)),
        (f"開出 ≥{BIG_WIN:g}× 單局就閃（自然或救援）", first_true(mult >= BIG_WIN, DAY_SPINS)),
        ("當日 RTP > 100% 就閃（贏就走）", first_true(cum_rtp > 1.0, DAY_SPINS)),
        ("贏就走 ＋ 拿到救援就閃", first_true((cum_rtp > 1.0) | rescued, DAY_SPINS)),
    ]

    print(f"=== 套利檢查（{GAME}，{SYSTEM_VERSION}，{n:,} 人，主救援 40–400 轉）===")
    print(f"{'策略':<30}{'平均停在':>8}{'RTP無機制':>11}{'RTP有機制':>11}{'EV/日(bet)':>12}")
    for name, stop in scenarios:
        rtp_mech, ev = strategy_rtp(adj, bet, stop)
        rtp_base, _ = strategy_rtp(nat, bet, stop)
        flag = "  ← 超過 100%" if rtp_mech > 1.0 else ""
        print(f"{name:<30}{stop.mean():>7.0f}轉{rtp_base * 100:>10.2f}%{rtp_mech * 100:>10.2f}%{ev:>+12.2f}{flag}")


if __name__ == "__main__":
    main()
