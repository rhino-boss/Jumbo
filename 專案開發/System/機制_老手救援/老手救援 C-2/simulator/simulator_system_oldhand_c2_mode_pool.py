# -*- coding: utf-8 -*-
"""老手救援 C-2 換模式套利（主救援＋延伸救援、可套救援池）。

資料：宙斯 2500（H027）92A v7.4.0.0 Oldhand 中 Bet NB／EB 每轉倍數分布
（rowdata/宙斯_92A_中Bet_NB_EB_分布.json）。NB 與 EB 總押注相同（押注每轉 1）。

規則同 simulator_system_oldhand_c2_bucket：40 轉一桶、觸發點後 1～5 轉判定、
條件 1 最近 1 桶 < 50%、條件 2 最近 10 桶 < 門檻、命中就強制換成救援結果（倍數取卡片區間上限）。
一天 1,000 轉（主救援 10 段＋延伸救援 440～960 共 14 段），每次模擬 1,000 人 × 1,000 轉 = 100 萬轉。

調參（門檻調法）：救援倍數不變；主救援 10 段與延伸救援門檻乘同一係數取整數 %，
再逐段 ±1% 微調，讓「只玩該模式」的玩家不套救援池時救援 RTP = 1.00% ± 0.02%。

玩家類型：
* only：只玩 NB 或只玩 EB。
* window：平常玩 EB，每個觸發點後 5 轉切到條件成立且倍數較大的模式。
* bucket：另外在每桶開始時，若 RTP 已低於門檻最鬆模式的下一段門檻，整桶改玩那個模式。
換模式防法 B：判定用的參數看「判定用 10 桶押注最多的模式」。
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DIST_FILE = HERE / "rowdata" / "宙斯_92A_中Bet_NB_EB_分布.json"
OUT = HERE / "record" / "mode_pool_宙斯.json"

PLAYERS = 1_000
DAY_SPINS = 1_000
assert PLAYERS * DAY_SPINS <= 1_000_000, "每次模擬最多 100 萬轉"
BUCKET = 40
COND1 = 0.50
BASE_MAIN_TH = [25, 30, 35, 40, 45, 50, 55, 55, 60, 65]
BASE_EXT_TH = 65
MAIN_RW = [25, 50, 70, 80, 90, 100, 100, 100, 100, 100]
EXT_RW = 100
TRIGGERS = list(range(40, 401, 40)) + list(range(440, DAY_SPINS, 40))
REWARD = np.array(MAIN_RW + [EXT_RW] * (len(TRIGGERS) - 10), dtype=float)
TARGET, TOL = 0.01, 0.0002
POOL_RATE = 0.01
SEED = 20261106
MODES = ("NB", "EB")


def expand(th11):
    """11 個門檻（主救援 10 段＋延伸 1 段，整數 %）→ 每個觸發點的門檻。"""
    return np.array(list(th11[:10]) + [th11[10]] * (len(TRIGGERS) - 10), dtype=float) / 100


def load_nat(rng):
    data = json.loads(DIST_FILE.read_text(encoding="utf-8"))["modes"]
    out = {}
    for m in MODES:
        v, p = np.array(data[m]["values"]), np.array(data[m]["probs"])
        idx = np.searchsorted(np.cumsum(p / p.sum()), rng.random((PLAYERS, DAY_SPINS)), side="right")
        out[m] = v[np.minimum(idx, len(v) - 1)].astype(np.float32)
    return out


def play(nat, th, kind, judge, *, defense=None, pool=False, order_rng=None):
    """kind[p] ∈ {"NB","EB","window","bucket"}；th[m] = 每觸發點門檻陣列。
    回傳每位玩家的 (自然得分, 救援增量)，以及 (判定成立數, 拒發數)。"""
    n = PLAYERS
    nb_bucket = DAY_SPINS // BUCKET + 1
    bsum = np.zeros((n, nb_bucket))
    bcnt = {m: np.zeros((n, nb_bucket)) for m in MODES}
    base = np.where(kind == "NB", "NB", "EB")
    switcher = (kind == "window") | (kind == "bucket")
    smart = kind == "bucket"
    mixer = kind == "mixer"          # 一般混玩：每桶隨機玩 NB 或 EB
    mix_rng = np.random.default_rng(SEED + 99)
    mixer_mode = base.copy()
    loose_mode = max(MODES, key=lambda m: th[m].mean())
    prev = base.copy()
    last_loose_switch = np.full(n, -10**9)   # 最近一次「嚴 → 鬆」切換發生在第幾轉
    nat_p = np.zeros(n)
    inc_p = np.zeros(n)
    window_mode = base.copy()
    bucket_mode = base.copy()
    balance, hits, denied = 0.0, 0, 0
    tindex = {t: i for i, t in enumerate(TRIGGERS)}
    for s in range(1, DAY_SPINS + 1):
        j, k = divmod(s - 1, BUCKET)
        t = BUCKET * j
        ti = tindex.get(t) if k < 5 else None
        if j >= 1:
            lo = max(0, j - 10)
            last = bsum[:, j - 1] / BUCKET
            done = bsum[:, lo:j].sum(axis=1) / (BUCKET * (j - lo))
        if k == 5:
            # 整桶切換：看下一個觸發點，門檻最鬆的模式若已高於目前 RTP 就整桶玩它
            bucket_mode = base.copy()
            nxt = tindex.get(BUCKET * (j + 1))
            if j >= 1 and nxt is not None:
                loose = max(MODES, key=lambda m: th[m][nxt])
                bucket_mode = np.where(smart & (done < th[loose][nxt]), loose, base)
        if ti is not None and k == 0:
            best = np.full(n, -1.0)
            window_mode = base.copy()
            for m in MODES:
                ok = switcher & (last < COND1) & (done < th[m][ti])
                better = ok & (REWARD[ti] > best)
                best = np.where(better, REWARD[ti], best)
                window_mode = np.where(better, m, window_mode)
        if k == 0:
            mixer_mode = np.where(mix_rng.random(n) < 0.5, "NB", "EB")
        cur = window_mode if ti is not None else bucket_mode
        cur = np.where(mixer, mixer_mode, cur)
        last_loose_switch = np.where((prev != loose_mode) & (cur == loose_mode), s, last_loose_switch)
        prev = cur
        pay = np.where(cur == "NB", nat["NB"][:, s - 1], nat["EB"][:, s - 1]).astype(np.float64)
        for m in MODES:
            bcnt[m][cur == m, j] += 1
        nat_p += pay
        if pool:
            balance += POOL_RATE * n
        if ti is not None:
            judged = judge[:, ti] == k + 1
            if defense == "B":
                cnt_nb = bcnt["NB"][:, lo:j].sum(axis=1)
                cnt_eb = bcnt["EB"][:, lo:j].sum(axis=1)
                rule = np.where(cnt_nb > cnt_eb, "NB", "EB")
            else:
                rule = cur
            rule_th = np.where(rule == "NB", th["NB"][ti], th["EB"][ti])
            go = judged & (last < COND1) & (done < rule_th)
            # 防法 D：判定前由嚴的模式切到鬆的模式就取消。D1 看最近 1 桶開始到判定轉；D10 看判定用 10 桶開始到判定轉
            if defense in ("D1", "D10"):
                since = BUCKET * (j - 1) + 1 if defense == "D1" else BUCKET * lo + 1
                go &= last_loose_switch < since
            hits += int(go.sum())
            paid = go.copy()
            if pool:
                paid[:] = False
                for p in order_rng.permutation(np.flatnonzero(go)):
                    if balance >= REWARD[ti]:
                        balance -= REWARD[ti]
                        paid[p] = True
                denied += int((go & ~paid).sum())
            inc_p += np.where(paid, REWARD[ti] - pay, 0.0)
            pay = np.where(paid, REWARD[ti], pay)
        bsum[:, j] += pay
    return nat_p, inc_p, hits, denied


def rescue_rtp(nat, th, kind, judge, **kw):
    _, inc, _, _ = play(nat, th, kind, judge, **kw)
    return inc.sum() / (PLAYERS * DAY_SPINS)


def tune(nat, judge, mode):
    kind = np.full(PLAYERS, mode)

    def rtp(th11):
        return rescue_rtp(nat, {m: expand(th11) for m in MODES}, kind, judge)

    grid = []
    for f in np.arange(0.20, 1.0001, 0.02):
        th11 = [round(x * f) for x in BASE_MAIN_TH] + [round(BASE_EXT_TH * f)]
        grid.append((abs(rtp(th11) - TARGET), th11))
    th11 = min(grid)[1]
    r = rtp(th11)
    for _ in range(30):
        if abs(r - TARGET) <= TOL:
            break
        cands = []
        for i in range(11):
            for d in (-1, 1):
                c = list(th11)
                c[i] += d
                if c[i] > 0:
                    cands.append((abs(rtp(c) - TARGET), c))
        best = min(cands)
        if best[0] >= abs(r - TARGET):
            break
        th11 = best[1]
        r = rtp(th11)
    return th11, r


def shared():
    """NB、EB 共用同一套門檻：以一半只玩 NB、一半只玩 EB 的玩家合計調到 1%，再看各群與切換玩家。"""
    rng = np.random.default_rng(SEED)
    nat = load_nat(rng)
    judge = rng.integers(1, 6, size=(PLAYERS, len(TRIGGERS)))
    mix = np.array(["NB"] * (PLAYERS // 2) + ["EB"] * (PLAYERS - PLAYERS // 2))

    def rtp(th11, kind=mix):
        return rescue_rtp(nat, {m: expand(th11) for m in MODES}, kind, judge)

    grid = [(abs(rtp([round(x * f) for x in BASE_MAIN_TH] + [round(BASE_EXT_TH * f)]) - TARGET),
             [round(x * f) for x in BASE_MAIN_TH] + [round(BASE_EXT_TH * f)]) for f in np.arange(0.20, 1.0001, 0.02)]
    th11 = min(grid)[1]
    r = rtp(th11)
    for _ in range(30):
        if abs(r - TARGET) <= TOL:
            break
        cands = [(abs(rtp(c) - TARGET), c) for i in range(11) for d in (-1, 1)
                 for c in [th11[:i] + [th11[i] + d] + th11[i + 1:]] if c[i] > 0]
        best = min(cands)
        if best[0] >= abs(r - TARGET):
            break
        th11, r = best[1], rtp(best[1])
    th = {m: expand(th11) for m in MODES}
    out = {"main_th": th11[:10], "ext_th": th11[10], "mix_rescue_rtp": r,
           "NB_only": rtp(th11, np.full(PLAYERS, "NB")), "EB_only": rtp(th11, np.full(PLAYERS, "EB")),
           "window": rtp(th11, np.full(PLAYERS, "window")), "bucket": rtp(th11, np.full(PLAYERS, "bucket"))}
    kind = np.array(["NB"] * 450 + ["EB"] * 450 + ["window"] * 50 + ["bucket"] * 50)
    nat_p, inc_p, hits, denied = play(nat, th, kind, judge, pool=True, order_rng=np.random.default_rng(SEED + 1))
    out["pool"] = {g: inc_p[kind == g].sum() / ((kind == g).sum() * DAY_SPINS) for g in ("NB", "EB", "window", "bucket")}
    out["pool"]["all"] = inc_p.sum() / (PLAYERS * DAY_SPINS)
    out["pool"]["deny_rate"] = denied / max(hits, 1)
    (HERE / "record" / "mode_shared_宙斯.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))


def defense_d():
    """防法 D（判定前由嚴切到鬆就取消）：各玩家群救援 RTP，含一般混玩玩家。"""
    rng = np.random.default_rng(SEED)
    nat = load_nat(rng)
    judge = rng.integers(1, 6, size=(PLAYERS, len(TRIGGERS)))
    tuned = json.loads(OUT.read_text(encoding="utf-8"))["tuned"]
    th = {m: expand(list(tuned[m]["main_th"]) + [tuned[m]["ext_th"]]) for m in MODES}
    out = {}
    for k in ("NB", "EB", "window", "bucket", "mixer"):
        out[k] = {d or "none": rescue_rtp(nat, th, np.full(PLAYERS, k), judge, defense=d) for d in (None, "B", "D1", "D10")}
    (HERE / "record" / "mode_defense_d_宙斯.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))


def main():
    rng = np.random.default_rng(SEED)
    nat = load_nat(rng)
    judge = rng.integers(1, 6, size=(PLAYERS, len(TRIGGERS)))
    tuned = {m: tune(nat, judge, m) for m in MODES}
    th = {m: expand(tuned[m][0]) for m in MODES}
    result = {"players": PLAYERS, "day_spins": DAY_SPINS,
              "tuned": {m: {"main_th": tuned[m][0][:10], "ext_th": tuned[m][0][10], "rescue_rtp": tuned[m][1]} for m in MODES},
              "no_pool": {}, "pool": {}}
    print("tuned", json.dumps(result["tuned"], ensure_ascii=False), flush=True)

    # 不套救援池：全體同一類型
    for k in ("NB", "EB", "window", "bucket"):
        for d in (None, "B"):
            key = f"{k}_{d or 'none'}"
            result["no_pool"][key] = rescue_rtp(nat, th, np.full(PLAYERS, k), judge, defense=d)
    print("no_pool", json.dumps(result["no_pool"]), flush=True)

    # 套 1% 救援池：45% 只玩 NB、45% 只玩 EB、5% 判定時切換、5% 整桶切換，共用同一個池
    kind = np.array(["NB"] * 450 + ["EB"] * 450 + ["window"] * 50 + ["bucket"] * 50)
    for d in (None, "B"):
        nat_p, inc_p, hits, denied = play(nat, th, kind, judge, defense=d, pool=True,
                                          order_rng=np.random.default_rng(SEED + 1))
        groups = {}
        for g in ("NB", "EB", "window", "bucket"):
            sel = kind == g
            groups[g] = {"rescue_rtp": inc_p[sel].sum() / (sel.sum() * DAY_SPINS),
                         "total_rtp": (nat_p[sel] + inc_p[sel]).sum() / (sel.sum() * DAY_SPINS)}
        result["pool"][d or "none"] = {"groups": groups, "deny_rate": denied / max(hits, 1),
                                       "all_rescue_rtp": inc_p.sum() / (PLAYERS * DAY_SPINS)}
    print("pool", json.dumps(result["pool"]), flush=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    import sys
    {"shared": shared, "defense_d": defense_d}.get((sys.argv[1:] or [""])[0], main)()
