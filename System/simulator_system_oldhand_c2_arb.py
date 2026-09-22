# -*- coding: utf-8 -*-
"""老手救援 C-2 套利檢查模擬。

以 rowdata 的 10,000 名玩家 × 1,000 轉自然結果，把每一列視為一個「玩家日」，
量測兩種套利策略的期望值（EV，以 bet 為單位）：

* 日切刷量：每天只玩到第 40 轉（第一個觸發點）就停，天天領第一點救援。
* 押注放大：第 1–39 轉用 1 單位押注做低當日 RTP，第 40 轉（判定轉）改押 B 倍
  吃救援。分別計算「無防線」與「計價防線 = min(當下押注, 當日押注中位數)」兩種。

門檻與倍數直接沿用 simulator_system_oldhand_c2.CHECKPOINT_RULES。
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from simulator_system_oldhand_c2 import CHECKPOINT_RULES, GAMES, load_rowdata  # noqa: E402

RAMP_BET = 10.0  # 押注放大倍率 B


def analyse(game: str) -> None:
    nat, bet = load_rowdata(game)
    assert np.allclose(bet, 1.0), "套利模擬假設 rowdata 押注固定為 1"
    threshold, reward = CHECKPOINT_RULES[40]

    first39 = nat[:, :39]
    mult40 = nat[:, 39]                       # 第 40 轉自然倍數（bet=1）
    trigger = first39.sum(axis=1) / 39.0 < threshold
    trig_rate = trigger.mean()

    # ---- 策略一：日切刷量（固定押注 1，玩到第 40 轉就停） ----
    natural_profit = first39.sum(axis=1) + mult40 - 40.0
    inc = np.where(trigger, np.maximum(mult40, reward) - mult40, 0.0)
    ev_farm = (natural_profit + inc).mean()

    # ---- 策略二：押注放大（第 40 轉押 B 倍） ----
    ramp_natural = first39.sum(axis=1) - 39.0 + RAMP_BET * (mult40 - 1.0)
    pay40 = RAMP_BET * mult40
    # 無防線：救援以當下押注計價 → reward × B
    inc_no_def = np.where(trigger, np.maximum(pay40, reward * RAMP_BET) - pay40, 0.0)
    ev_ramp = (ramp_natural + inc_no_def).mean()
    # 計價防線：救援以 min(當下押注, 當日押注中位數=1) 計價 → reward × 1
    inc_def = np.where(trigger, np.maximum(pay40, reward) - pay40, 0.0)
    ev_ramp_def = (ramp_natural + inc_def).mean()

    print(f"=== 套利檢查（{game}）第 40 轉觸發點：門檻 <{threshold * 100:.0f}%、救 {reward:g}× ===")
    print(f"trigger_rate_cp40       : {trig_rate * 100:.2f}%")
    print(f"日切刷量 EV/日           : {ev_farm:+.3f} bet（40 轉停手，天天重來）")
    print(f"押注放大 EV/日（無防線）  : {ev_ramp:+.3f} bet（第 40 轉押 {RAMP_BET:g} 倍）")
    print(f"押注放大 EV/日（計價防線）: {ev_ramp_def:+.3f} bet")
    print()


def main() -> None:
    for game in GAMES:
        analyse(game)


if __name__ == "__main__":
    main()
