# -*- coding: utf-8 -*-
"""老手救援 C-2 現行規則模擬（40 轉一桶、觸發點後 1～5 轉判定、強制換成救援結果）。

規則（老手救援 C-2版 規格）：
* 觸發點 t：主救援 40, 80, …, 400；延伸救援 440 起每 40 轉、不設上限。
* 判定轉在 t+1～t+5 均勻隨機；只看完成的桶：
  條件 1 = 最近 1 桶 RTP < 50%；條件 2 = 最近 10 桶（不足全拿）RTP < 門檻
  （主救援依觸發點，延伸救援 < 65%）。
* 押注檢查：判定轉押注 > 判定用桶平均押注 → 取消。
* 命中就強制換成救援結果（不取較高者）；救援得分 = 救援倍數 × 押注，倍數取卡片區間上限（保守）。
* 救援池（選用）：每轉提撥押注 × pool_rate；救援成本 = 整筆救援得分；餘額不足不救；每天歸零、起始 0。

自然結果：彩罐熱舞 rowdata（10,000 人 × 1,000 轉，押注固定 1）每轉獨立，
本程式把全部 1,000 萬轉當母體有放回抽樣，可組成任意轉數。每次模擬最多 100 萬轉。

用法：python3 simulator_system_oldhand_c2_bucket.py main|ext|long|pool|arb
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROWDATA = HERE / "rowdata" / "彩罐熱舞_基礎遊戲_10000人_1000轉.csv.gz"
RECORD = HERE / "record"
MAX_SPINS = 1_000_000
SEED = 20261105

BUCKET = 40
COND1 = 0.50
MAIN_TH = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.55, 0.60, 0.65]
MAIN_RW = [25, 50, 70, 80, 90, 100, 100, 100, 100, 100]
EXT_TH = 0.65
EXT_RW = 100
NEWBIE_SPINS = 200


def load_population() -> np.ndarray:
    with gzip.open(ROWDATA, "rt", encoding="utf-8") as fh:
        frame = pd.read_csv(fh, usecols=["Bet", "Natural_Payout"])
    return (frame["Natural_Payout"] / frame["Bet"]).to_numpy(dtype=np.float64)


def triggers(n_spins: int) -> list[tuple[int, float, float]]:
    """(觸發點, 條件 2 門檻, 救援倍數)，只列判定區間開始於當日轉數內的。"""
    out = [(40 * (i + 1), MAIN_TH[i], MAIN_RW[i]) for i in range(10)]
    t = 440
    while t + 1 <= n_spins:
        out.append((t, EXT_TH, EXT_RW))
        t += 40
    return [x for x in out if x[0] + 1 <= n_spins]


def run_day(mult, bet, rng, *, pool_rate=None, newbie=False, bet_check=True, raise_to=None):
    """一天：所有玩家同步轉動。回傳 dict（final 為套機制後每轉得分）。
    raise_to：加注套利玩家——觸發點後 5 轉，看已完成的桶條件都成立就把押注加到 raise_to。"""
    n, n_spins = mult.shape
    assert n * n_spins <= MAX_SPINS, "每次模擬最多 100 萬轉"
    bet = bet.copy()
    nat = mult * bet
    final = nat.copy()
    trig = triggers(n_spins)
    by_t = {t: i for i, (t, _, _) in enumerate(trig)}
    offset = rng.integers(1, 6, size=(n, len(trig)))
    bpay = np.zeros((n, n_spins // BUCKET + 2))
    bbet = np.zeros_like(bpay)
    stats = {k: np.zeros(len(trig)) for k in ("judged", "hit", "cancel", "denied", "paid_n", "paid", "cost_want")}
    rescued_at = np.zeros((n, n_spins), dtype=bool)
    balance = 0.0
    rows = np.arange(n)
    for s in range(1, n_spins + 1):
        col = s - 1
        j, k = divmod(col, BUCKET)
        if pool_rate is not None:
            balance += pool_rate * bet[:, col].sum()
        t = BUCKET * j
        if k < 5 and t in by_t and not (newbie and t < NEWBIE_SPINS + BUCKET):
            ti = by_t[t]
            _, th, rw = trig[ti]
            judge = offset[:, ti] == k + 1
            lo = max(0, j - 10)
            cond1 = bpay[:, j - 1] / bbet[:, j - 1] < COND1
            cond2 = bpay[:, lo:j].sum(axis=1) / bbet[:, lo:j].sum(axis=1) < th
            if raise_to is not None:
                up = cond1 & cond2
                bet[up, col] = raise_to
                nat[:, col] = mult[:, col] * bet[:, col]
                final[:, col] = nat[:, col]
            hit = judge & cond1 & cond2
            avg_bet = bbet[:, lo:j].sum(axis=1) / (BUCKET * (j - lo))
            cancel = hit & (bet[:, col] > avg_bet + 1e-12) if bet_check else np.zeros(n, bool)
            go = hit & ~cancel
            cost = rw * bet[:, col]
            stats["judged"][ti] += judge.sum()
            stats["hit"][ti] += hit.sum()
            stats["cancel"][ti] += cancel.sum()
            stats["cost_want"][ti] += cost[go].sum()
            if pool_rate is None:
                paid = go
            else:
                paid = np.zeros(n, bool)
                for p in rng.permutation(rows[go]):
                    if balance >= cost[p]:
                        balance -= cost[p]
                        paid[p] = True
                stats["denied"][ti] += (go & ~paid).sum()
            final[paid, col] = cost[paid]
            rescued_at[paid, col] = True
            stats["paid_n"][ti] += paid.sum()
            stats["paid"][ti] += (final[paid, col] - nat[paid, col]).sum()
        bpay[:, j] += final[:, col]
        bbet[:, j] += bet[:, col]
    return dict(nat=nat, final=final, bet=bet, trig=trig, stats=stats, rescued_at=rescued_at, end_balance=balance)


def draw(pop, n, n_spins, rng):
    return pop[rng.integers(0, len(pop), size=(n, n_spins))]


def pct(x):
    return round(float(x) * 100, 4)


def item_main(pop, rng):
    """1-a 主救援：2,400 人 × 405 轉；另跑新玩家第一天（前 200 轉新手期）。"""
    n, n_spins = 2_400, 405
    mult = draw(pop, n, n_spins, rng)
    bet = np.ones_like(mult)
    out = {}
    for label, newbie in (("oldhand", False), ("first_day", True)):
        r = run_day(mult, bet, np.random.default_rng(SEED + 1), newbie=newbie)
        tb = r["bet"].sum()
        st = r["stats"]
        out[label] = {
            "natural_rtp": pct(r["nat"].sum() / tb),
            "increment": pct((r["final"] - r["nat"]).sum() / tb),
            "total_rtp": pct(r["final"].sum() / tb),
            "rescued_players": pct(r["rescued_at"].any(axis=1).mean()),
            "trigger_rate": pct(st["paid_n"].sum() / max(st["judged"].sum(), 1)),
            "rescues": int(st["paid_n"].sum()), "judged": int(st["judged"].sum()),
            "windows": [{"t": t, "rate": pct(st["paid_n"][i] / max(st["judged"][i], 1)),
                         "usage": pct(st["paid"][i] / tb), "count": int(st["paid_n"][i])}
                        for i, (t, _, _) in enumerate(r["trig"])],
        }
    return out


def item_ext(pop, rng):
    """1-b 延伸救援：1,000 人 × 1,000 轉（前段套主救援），並以截斷算全員固定玩 N 轉。"""
    n, n_spins = 1_000, 1_000
    mult = draw(pop, n, n_spins, rng)
    r = run_day(mult, np.ones_like(mult), np.random.default_rng(SEED + 2))
    return summarize_long(r, [500, 600, 700, 800, 900, 1000])


def item_long(pop, rng):
    """2 超過 1,000 轉：500 人 × 2,000 轉。"""
    n, n_spins = 500, 2_000
    mult = draw(pop, n, n_spins, rng)
    r = run_day(mult, np.ones_like(mult), np.random.default_rng(SEED + 3))
    return summarize_long(r, [1000, 1200, 1400, 1600, 1800, 2000])


def summarize_long(r, cut_points):
    nat, final, bet, st = r["nat"], r["final"], r["bet"], r["stats"]
    ext_idx = [i for i, (t, _, _) in enumerate(r["trig"]) if t >= 440]
    seg = slice(400, None)
    out = {
        "segment_natural_rtp": pct(nat[:, seg].sum() / bet[:, seg].sum()),
        "ext_increment": pct((final[:, seg] - nat[:, seg]).sum() / bet[:, seg].sum()),
        "ext_rescued_players": pct(r["rescued_at"][:, 400:].any(axis=1).mean()),
        "ext_trigger_rate": pct(st["paid_n"][ext_idx].sum() / max(st["judged"][ext_idx].sum(), 1)),
        "ext_rescues": int(st["paid_n"][ext_idx].sum()), "ext_judged": int(st["judged"][ext_idx].sum()),
        "day_total_rtp": pct(final.sum() / bet.sum()),
        "windows": [{"t": r["trig"][i][0], "rate": pct(st["paid_n"][i] / max(st["judged"][i], 1))} for i in ext_idx],
        "fixed_n": [],
    }
    for n_cut in cut_points:
        s = slice(400, n_cut)
        out["fixed_n"].append({
            "n": n_cut,
            "ext_increment": pct((final[:, s] - nat[:, s]).sum() / bet[:, s].sum()),
            "total_rtp": pct(final[:, :n_cut].sum() / bet[:, :n_cut].sum()),
        })
    return out


def item_pool(pop, rng):
    """3 救援池 1%：每天同步轉動，依當日轉數調整人數讓每次 ≤ 100 萬轉。"""
    out = []
    for n_spins, n in ((405, 2_400), (800, 1_250), (1_000, 1_000), (2_000, 500)):
        mult = draw(pop, n, n_spins, rng)
        bet = np.ones_like(mult)
        free = run_day(mult, bet, np.random.default_rng(SEED + 4))
        capped = run_day(mult, bet, np.random.default_rng(SEED + 4), pool_rate=0.01)
        tb = bet.sum()
        st = capped["stats"]
        out.append({
            "spins": n_spins, "players": n,
            "natural_rtp": pct(free["nat"].sum() / tb),
            "uncapped_increment": pct((free["final"] - free["nat"]).sum() / tb),
            "paid_increment": pct((capped["final"] - capped["nat"]).sum() / tb),
            "total_rtp": pct(capped["final"].sum() / tb),
            "deny_rate": pct(st["denied"].sum() / max(st["hit"].sum() - st["cancel"].sum(), 1)),
            "pool_usage": pct(capped["final"][capped["rescued_at"]].sum() / (0.01 * tb)),
            "end_balance_per_player": round(capped["end_balance"] / n, 3),
        })
    return out


def strategy_rtp(final, bet, stop):
    keep = np.arange(final.shape[1])[None, :] < stop[:, None]
    tp, tb = (final * keep).sum(), (bet * keep).sum()
    return pct(tp / tb), round(float((tp - tb) / final.shape[0]), 3)


def item_arb(pop, rng):
    """4 套利：主救援 2,400 人 × 405 轉；延伸救援 1,000 人 × 1,000 轉；加注套利。"""
    out = {"main": [], "ext": [], "bet_up": {}}
    n, n_spins = 2_400, 405
    mult = draw(pop, n, n_spins, rng)
    bet = np.ones_like(mult)
    r = run_day(mult, bet, np.random.default_rng(SEED + 5))

    def first_rescue(rescued, default):
        has = rescued.any(axis=1)
        return np.where(has, rescued.argmax(axis=1) + 1, default)

    for stop_n in list(range(45, 406, 40)):
        stop = np.full(n, stop_n)
        rtp, ev = strategy_rtp(r["final"], bet, stop)
        out["main"].append({"strategy": f"固定玩 {stop_n} 轉就閃", "avg_stop": stop_n, "rtp": rtp,
                            "rtp_none": strategy_rtp(r["nat"], bet, stop)[0], "ev": ev})
    stop = first_rescue(r["rescued_at"], n_spins)
    rtp, ev = strategy_rtp(r["final"], bet, stop)
    out["main"].append({"strategy": f"拿到任何救援就閃（否則玩到 {n_spins}）", "avg_stop": round(float(stop.mean()), 1),
                        "rtp": rtp, "rtp_none": strategy_rtp(r["nat"], bet, np.full(n, n_spins))[0], "ev": ev})

    # 延伸救援
    n2, s2 = 1_000, 1_000
    mult2 = draw(pop, n2, s2, rng)
    bet2 = np.ones_like(mult2)
    r2 = run_day(mult2, bet2, np.random.default_rng(SEED + 6))
    for stop_n in (445, 605, 805, 1000):
        stop = np.full(n2, stop_n)
        rtp, ev = strategy_rtp(r2["final"], bet2, stop)
        out["ext"].append({"strategy": f"固定玩 {stop_n} 轉就閃", "avg_stop": stop_n, "rtp": rtp,
                           "rtp_none": strategy_rtp(r2["nat"], bet2, stop)[0], "ev": ev})
    stop = first_rescue(r2["rescued_at"][:, 400:], s2 - 400) + 400
    rtp, ev = strategy_rtp(r2["final"], bet2, stop)
    out["ext"].append({"strategy": "400 轉後拿到救援就閃（否則玩到 1,000）", "avg_stop": round(float(stop.mean()), 1),
                       "rtp": rtp, "rtp_none": strategy_rtp(r2["nat"], bet2, np.full(n2, s2))[0], "ev": ev})

    # 加注套利：平常押 1；觸發點後 5 轉若條件都成立（玩家看得到自己的輸贏）就押 10
    raise_to = 10.0
    for label, check in (("有押注檢查", True), ("沒有押注檢查", False)):
        rr = run_day(mult, bet, np.random.default_rng(SEED + 5), bet_check=check, raise_to=raise_to)
        tb = rr["bet"].sum()
        out["bet_up"][label] = {"rtp": pct(rr["final"].sum() / tb), "rtp_none": pct(rr["nat"].sum() / tb),
                                "canceled": int(rr["stats"]["cancel"].sum()), "rescues": int(rr["stats"]["paid_n"].sum())}
    return out


ITEMS = {"main": item_main, "ext": item_ext, "long": item_long, "pool": item_pool, "arb": item_arb}


def main():
    names = sys.argv[1:] or list(ITEMS)
    pop = load_population()
    for name in names:
        result = ITEMS[name](pop, np.random.default_rng(SEED))
        RECORD.mkdir(exist_ok=True)
        (RECORD / f"bucket_{name}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"=== {name} ===")
        print(json.dumps(result, ensure_ascii=False)[:3000], flush=True)


if __name__ == "__main__":
    main()
