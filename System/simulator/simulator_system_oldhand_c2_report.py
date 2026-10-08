# -*- coding: utf-8 -*-
"""產出「機制說明_老手救援」C3 文件用的全部數字（彩罐熱舞），輸出 report_numbers.json。

階段一（主救援）以 10,000 人 × 400 轉為基準；觸發點在前後 5 轉內隨機判定，
玩家當天沒玩到的判定轉（例如 400 轉基準下第 401–405 轉）不判定。
階段二（延伸救援）以 401–1,000 轉區段押注為分母。
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import simulator_system_oldhand_c2 as sim  # noqa: E402
from simulator_system_oldhand_c2_arb import first_true, strategy_rtp  # noqa: E402

GAME = "彩罐熱舞"
DAY = 400
NEWBIE_SKIP = (40, 80, 120, 160, 200)
EXT_PROBS = [0.0, 0.01, 0.02, 0.03, 0.05, 0.08, 0.10]
EXT_SEEDS = range(5)


def main_stats(nat, bet, spins, skip=()):
    adj, reward_at = sim.apply_main(nat, bet, spins, skip)
    n, length = nat.shape
    rows = np.arange(n)
    tb = bet.sum()
    per_cp = {}
    for cp in sim.CHECKPOINTS:
        played = spins[cp] <= length
        k = np.minimum(spins[cp], length) - 1
        hit = played & (reward_at[rows, k] > 0)
        per_cp[cp] = dict(
            judged=int(played.sum()), hits=int(hit.sum()),
            trigger_rate=float(hit.sum() / n),
            usage=float(((adj[rows, k] - nat[rows, k]) * hit).sum() / tb),
        )
    return adj, reward_at, per_cp


def run_extension(base, nat, bet, p, seed):
    rng = np.random.default_rng(seed)
    adj = base.copy()
    n = nat.shape[0]
    hits_total, used = 0, np.zeros(n, bool)
    rates = {}
    for cp in sim.EXT_CHECKPOINTS:
        i = cp - 1
        w, sw = sim.EXT_MID_WINDOW, sim.EXT_SHORT_WINDOW
        mid = adj[:, i - w:i].sum(1) / bet[:, i - w:i].sum(1)
        short = adj[:, i - sw:i].sum(1) / bet[:, i - sw:i].sum(1)
        hit = (mid < sim.EXT_MID_THRESHOLD) & (short < sim.EXT_SHORT_THRESHOLD)
        big = hit & (rng.random(n) < p)
        rw = np.where(big, sim.EXT_BIG_REWARD, sim.EXT_REWARD)
        adj[:, i] = np.where(hit, np.maximum(nat[:, i], rw * bet[:, i]), nat[:, i])
        rates[cp] = float(hit.mean())
        hits_total += int(hit.sum())
        used |= hit
    seg = slice(DAY, 1000)
    inc = (adj[:, seg] - base[:, seg]).sum() / bet[:, seg].sum()
    return float(inc), hits_total, float(used.mean()), rates


def main() -> None:
    nat_all, bet_all = sim.load_rowdata(GAME)
    n = nat_all.shape[0]
    spins = sim.judge_spins(n, np.random.default_rng(sim.MAIN_SEED))
    out: dict = {"version": sim.SYSTEM_VERSION}

    # ---- 階段一：400 轉基準 ----
    nat, bet = nat_all[:, :DAY], bet_all[:, :DAY]
    adj, reward_at, per_cp = main_stats(nat, bet, spins)
    _, _, per_cp_nb = main_stats(nat, bet, spins, NEWBIE_SKIP)
    out["per_cp"] = per_cp
    out["newbie_usage"] = {cp: v["usage"] for cp, v in per_cp_nb.items()}
    tb = bet.sum()
    hits = int((reward_at > 0).sum())
    judged = sum(v["judged"] for v in per_cp.values())
    out["metrics"] = dict(
        base=float(nat.sum() / tb), uplift=float((adj - nat).sum() / tb), total=float(adj.sum() / tb),
        used_ratio=float((reward_at > 0).any(1).mean()), hits=hits, judged=judged,
    )
    rows = np.arange(n)
    dist = {}
    for cp in sim.CHECKPOINTS:
        k = np.minimum(spins[cp], DAY) - 1
        c = int(((spins[cp] <= DAY) & (reward_at[rows, k] > 0)).sum())
        rw = sim.CHECKPOINT_RULES[cp][1]
        key = f"{rw:g}x@{cp}" if rw == 100 else f"{rw:g}x"
        dist[key] = dist.get(key, 0) + c
    out["distribution"] = dist

    # 觸發點表（靜態）：RTP 增量、極限 RTP 依判定轉落點變動
    J = sim.CHECKPOINT_JITTER
    out["static"] = {
        cp: dict(th=th, rw=rw, inc_min=rw / (cp + J), inc_max=rw / (cp - J),
                 cap_min=th + rw / (cp + J), cap_max=th + rw / (cp - J))
        for cp, (th, rw) in sim.CHECKPOINT_RULES.items()
    }

    # 極限 RTP 頂到 < 100%（整數門檻，以區間最早一轉計）
    orig = dict(sim.CHECKPOINT_RULES)
    pushed = {cp: ((math.ceil(100 - rw / (cp - J) * 100) - 1) / 100, rw) for cp, (th, rw) in orig.items()}
    sim.CHECKPOINT_RULES.clear(); sim.CHECKPOINT_RULES.update(pushed)
    adj_p, _, _ = main_stats(nat, bet, spins)
    sim.CHECKPOINT_RULES.clear(); sim.CHECKPOINT_RULES.update(orig)
    out["pushed"] = dict(uplift=float((adj_p - nat).sum() / tb),
                         thresholds={cp: v[0] for cp, v in pushed.items()},
                         cap_max=max(v[0] + v[1] / (cp - J) for cp, v in pushed.items()))

    # 敏感度：全員固定玩 N 轉（只計主救援）
    sens = {}
    for N in range(100, 1001, 100):
        a, _, _ = main_stats(nat_all[:, :N], bet_all[:, :N], spins)
        b = bet_all[:, :N].sum()
        sens[N] = dict(uplift=float((a - nat_all[:, :N]).sum() / b), total=float(a.sum() / b))
    out["sensitivity"] = sens

    # 套利：固定玩 N 轉就閃、拿到任何救援就閃（否則玩到 400）
    arb = {}
    rescued = reward_at > 0
    for cp in sim.CHECKPOINTS:
        stop = np.full(n, cp)
        rm, ev = strategy_rtp(adj, bet, stop)
        rb, _ = strategy_rtp(nat, bet, stop)
        arb[f"fixed_{cp}"] = dict(stop=float(stop.mean()), rtp=float(rm), base=float(rb), ev=float(ev))
    stop = first_true(rescued, DAY)
    rm, ev = strategy_rtp(adj, bet, stop)
    rb, _ = strategy_rtp(nat, bet, np.full(n, DAY))
    arb["any_rescue"] = dict(stop=float(stop.mean()), rtp=float(rm), base=float(rb), ev=float(ev))
    out["arb"] = arb

    # ---- 階段二：401–1,000 轉區段 ----
    base_full, _, _ = main_stats(nat_all, bet_all, spins)
    inc0, hits0, used0, rates0 = run_extension(base_full, nat_all, bet_all, 0.0, 0)
    out["ext"] = dict(inc_p0=inc0, hits=hits0, judged=n * len(sim.EXT_CHECKPOINTS), used=used0, rates=rates0,
                      seg_base=float(nat_all[:, DAY:].sum() / bet_all[:, DAY:].sum()))
    ptab = {}
    for p in EXT_PROBS:
        ptab[p] = float(np.mean([run_extension(base_full, nat_all, bet_all, p, s)[0] for s in EXT_SEEDS]))
    out["ext"]["p_table"] = ptab
    lo, hi = 0.0, 0.2
    for _ in range(20):
        mid = (lo + hi) / 2
        v = np.mean([run_extension(base_full, nat_all, bet_all, mid, s)[0] for s in EXT_SEEDS])
        lo, hi = (mid, hi) if v < 0.05 else (lo, mid)
    out["ext"]["p_for_5pct"] = lo

    dest = Path(__file__).resolve().parent / "record" / "report_numbers.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, default=str)[:3000])
    print("saved", dest)


if __name__ == "__main__":
    main()
