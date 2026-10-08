# -*- coding: utf-8 -*-
"""新手體驗 D 版模擬（彩罐熱舞 rowdata），輸出 record/newbie_numbers.json。

規則（專案需知/機制說明.md 第 1 節）：
* 第一次：第 41–60 轉隨機一轉判定，RTP（第 1 轉～判定回合前一轉）< 50% → 15×、50%～< 70% → 10×、≥ 70% 不處理。
* 第二次：第 140–160 轉隨機一轉判定，RTP < 65% → 30×、65%～< 85% → 15×、≥ 85% 不處理。
* 設定得分「取代」判定回合的原始得分（不是取較高值）；第二次判定使用已套用第一次的結果。
* 新手期以 200 轉為基準。rowdata 為 92% 基礎（老手配置），新手配置若基礎 RTP 不同需另跑。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from simulator_system_oldhand_c2 import load_rowdata  # noqa: E402
from simulator_system_oldhand_c2_arb import first_true, strategy_rtp  # noqa: E402

GAME = "彩罐熱舞"
NEWBIE_SPINS = 200
SEED = 20261008
# (判定區間, [(RTP 上限, 設定倍數), ...])；超過最後一個上限不處理
JUDGES = [
    ((41, 60), [(0.50, 15.0), (0.70, 10.0)]),
    ((140, 160), [(0.65, 30.0), (0.85, 15.0)]),
]


def apply_newbie(nat: np.ndarray, bet: np.ndarray, rng: np.random.Generator):
    """回傳 (adj, set_at, spins)：set_at[p, i] 為該轉設定倍數（0 = 未處理）。"""
    n, length = nat.shape
    rows = np.arange(n)
    adj = nat.copy()
    set_at = np.zeros_like(nat)
    spins = []
    for (lo, hi), bands in JUDGES:
        s = rng.integers(lo, hi + 1, n)
        spins.append(s)
        played = s <= length
        k = np.minimum(s, length) - 1
        cs_a = np.concatenate([np.zeros((n, 1)), np.cumsum(adj, axis=1)], axis=1)
        cs_b = np.concatenate([np.zeros((n, 1)), np.cumsum(bet, axis=1)], axis=1)
        rtp = cs_a[rows, k] / cs_b[rows, k]
        mult = np.zeros(n)
        for upper, m in reversed(bands):
            mult = np.where(rtp < upper, m, mult)
        hit = played & (mult > 0)
        adj[rows[hit], k[hit]] = mult[hit] * bet[rows[hit], k[hit]]
        set_at[rows[hit], k[hit]] = mult[hit]
    return adj, set_at, spins


def main() -> None:
    nat_all, bet_all = load_rowdata(GAME)
    n = nat_all.shape[0]
    nat, bet = nat_all[:, :NEWBIE_SPINS], bet_all[:, :NEWBIE_SPINS]
    adj, set_at, spins = apply_newbie(nat, bet, np.random.default_rng(SEED))
    rows = np.arange(n)
    tb = bet.sum()
    out: dict = {"basis": f"10,000 人 × {NEWBIE_SPINS} 轉"}

    judges = []
    for j, ((lo, hi), bands) in enumerate(JUDGES):
        k = spins[j] - 1
        m = set_at[rows, k]
        band_rates = {f"{b[1]:g}x": float((m == b[1]).mean()) for b in bands}
        inc = (adj[rows, k] - nat[rows, k])
        judges.append(dict(
            window=[lo, hi], bands=band_rates, trigger_rate=float((m > 0).mean()),
            usage=float((inc * (m > 0)).sum() / tb),
            negative_share=float(((inc < 0) & (m > 0)).sum() / max((m > 0).sum(), 1)),
        ))
    out["judges"] = judges
    out["metrics"] = dict(
        base=float(nat.sum() / tb), uplift=float((adj - nat).sum() / tb), total=float(adj.sum() / tb),
        used_ratio=float((set_at > 0).any(1).mean()),
        hits=int((set_at > 0).sum()), judged=n * len(JUDGES),
    )
    dist = {}
    for v in set_at[set_at > 0]:
        dist[f"{v:g}x"] = dist.get(f"{v:g}x", 0) + 1
    out["distribution"] = dist

    # 敏感度：新手期內固定玩 N 轉
    sens = {}
    for N in (60, 100, 160, 200):
        a, _, _ = apply_newbie(nat_all[:, :N], bet_all[:, :N], np.random.default_rng(SEED))
        b = bet_all[:, :N].sum()
        sens[N] = dict(uplift=float((a - nat_all[:, :N]).sum() / b), total=float(a.sum() / b))
    out["sensitivity"] = sens

    # 套利：固定玩 N 轉就閃、拿到體驗就閃（否則玩到 200）
    arb = {}
    for N in (60, 100, 160, 200):
        stop = np.full(n, N)
        rm, ev = strategy_rtp(adj, bet, stop)
        rb, _ = strategy_rtp(nat, bet, stop)
        arb[f"fixed_{N}"] = dict(stop=float(stop.mean()), rtp=float(rm), base=float(rb), ev=float(ev))
    stop = first_true(set_at > 0, NEWBIE_SPINS)
    rm, ev = strategy_rtp(adj, bet, stop)
    rb, _ = strategy_rtp(nat, bet, np.full(n, NEWBIE_SPINS))
    arb["any_set"] = dict(stop=float(stop.mean()), rtp=float(rm), base=float(rb), ev=float(ev))
    out["arb"] = arb

    dest = Path(__file__).resolve().parent / "record" / "newbie_numbers.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
