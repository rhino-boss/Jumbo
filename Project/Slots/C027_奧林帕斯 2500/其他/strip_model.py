"""H027 輪帶合成數學模型.

競品輪帶結構的關鍵觀察：

1. 競品 3.3.1 節的視窗堆疊分布（BG 60.868 / 34.952 / 3.772 / 0.363 / 0.045）
   與「每格獨立同分布」的理論值（60.43 / 35.31 / 3.85 / 0.38 / 0.03）幾乎相同，
   代表競品輪帶的「相鄰重複」就是純隨機水準。
2. 但 i.i.d. 盤面的 Any-8 命中率為 BG 27.17% / FG 25.49% / BF 22.42%，
   競品實際是 22.225% / 42.169% / 33.105%。
   代表競品 BG 輪帶比隨機更分散、FG 輪帶比隨機更聚集。

只靠相鄰重複無法同時滿足 1 與 2，因為相鄰重複已被 1 鎖死。
剩下的自由度是「同輪帶同符號、距離 2~4 的非相鄰重複」，它會改變 5 格視窗內
同符號個數的變異數（進而改變 Any-8 命中率與獎項大小分布），卻幾乎不影響堆疊分布。

因此本模型用兩個統計量描述一條輪帶（環狀、長度 L、符號 c 出現 n_c 次、f_c = n_c/L）：

    N1(c)  = 距離 1 的同符號配對數     目標 L * f_c^2            相當於 i.i.d. 水準，鎖定堆疊分布
    NAR(c) = 3*N2 + 2*N3 + 1*N4       目標 theta * L * 6 f_c^2   theta 為聚集度，唯一自由參數

係數 (4,3,2,1) 是「距離 d 的配對會落在幾個 5 格視窗內」，所以
E[視窗內相鄰配對數] = 4*N1/L、E[視窗內非相鄰配對數] = NAR/L；theta=1 即 i.i.d.。

theta 對每個場景（BG／FG／BF）各一個，用二分法讓盤面 Any-8 命中率打中競品值。
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit


def largest_remainder(weights, total: int) -> list[int]:
    weights = [max(0.0, float(w)) for w in weights]
    scale = sum(weights)
    if scale <= 0:
        raise ValueError("weights must not be all zero")
    exact = [w / scale * total for w in weights]
    base = [math.floor(v) for v in exact]
    order = sorted(range(len(exact)), key=lambda i: exact[i] - base[i], reverse=True)
    for i in order[: total - sum(base)]:
        base[i] += 1
    return base


@njit(cache=True)
def _pair_counts(seq, symbol_count):
    length = seq.shape[0]
    counts = np.zeros((symbol_count, 5), dtype=np.int64)
    for i in range(length):
        s = seq[i]
        for d in range(1, 5):
            if seq[(i + d) % length] == s:
                counts[s, d] += 1
    return counts


@njit(cache=True)
def _max_run(seq):
    length = seq.shape[0]
    best = 1
    run = 1
    for i in range(1, 2 * length):
        if seq[i % length] == seq[(i - 1) % length]:
            run += 1
            if run > best:
                best = run
        else:
            run = 1
    return min(best, length)


@njit(cache=True)
def _local_counts(seq, symbol_count, i, j):
    length = seq.shape[0]
    counts = np.zeros((symbol_count, 5), dtype=np.int64)
    for k in range(2):
        p = i if k == 0 else j
        for d in range(1, 5):
            q = (p + d) % length
            if seq[p] == seq[q]:
                counts[seq[p], d] += 1
            q = (p - d) % length
            if seq[p] == seq[q]:
                counts[seq[p], d] += 1
    return counts


@njit(cache=True)
def _score(counts, n1_target, nar_target, n1_weight, nar_weight):
    total = 0.0
    for s in range(counts.shape[0]):
        n1 = counts[s, 1]
        nar = 3.0 * counts[s, 2] + 2.0 * counts[s, 3] + 1.0 * counts[s, 4]
        d1 = n1 - n1_target[s]
        d2 = nar - nar_target[s]
        total += n1_weight * d1 * d1 + nar_weight * d2 * d2
    return total


@njit(cache=True)
def _scatter_ok(seq, scatter_id, gap):
    length = seq.shape[0]
    previous = -1
    first = -1
    for i in range(length):
        if seq[i] == scatter_id:
            if previous < 0:
                first = i
            elif i - previous < gap:
                return False
            previous = i
    if first >= 0 and previous != first and (first + length - previous) < gap:
        return False
    return True


@njit(cache=True)
def _anneal(seq, symbol_count, n1_target, nar_target, n1_weight, nar_weight,
            iterations, seed, scatter_id, scatter_gap, max_run):
    np.random.seed(seed)
    length = seq.shape[0]
    counts = _pair_counts(seq, symbol_count)
    current = _score(counts, n1_target, nar_target, n1_weight, nar_weight)
    best_seq = seq.copy()
    best = current
    temperature0 = max(1.0, current / max(1.0, float(length)))
    for step in range(iterations):
        i = np.random.randint(0, length)
        j = np.random.randint(0, length)
        if seq[i] == seq[j]:
            continue
        # A pair whose two endpoints are both being swapped would be counted twice
        # by _local_counts, so the incremental delta is only exact when the two
        # positions are farther apart than the longest tracked distance.
        gap = j - i if j > i else i - j
        if min(gap, length - gap) <= 4:
            continue
        before = _local_counts(seq, symbol_count, i, j)
        seq[i], seq[j] = seq[j], seq[i]
        after = _local_counts(seq, symbol_count, i, j)
        trial_counts = counts + (after - before)
        trial = _score(trial_counts, n1_target, nar_target, n1_weight, nar_weight)
        ok = True
        if scatter_id >= 0 and (seq[i] == scatter_id or seq[j] == scatter_id):
            ok = _scatter_ok(seq, scatter_id, scatter_gap)
        if ok and max_run > 0 and _max_run(seq) > max_run:
            ok = False
        accept = False
        if ok:
            if trial <= current:
                accept = True
            else:
                temperature = temperature0 * (1.0 - step / iterations) + 1e-9
                if np.random.random() < np.exp(-(trial - current) / temperature):
                    accept = True
        if accept:
            counts = trial_counts
            current = trial
            if current < best:
                best = current
                best_seq = seq.copy()
        else:
            seq[i], seq[j] = seq[j], seq[i]
    return best_seq, best


def build_reel(counts, symbol_index, theta, seed, scatter_code="C1",
               scatter_gap=6, max_run=3, iterations=120_000, n1_weight=1.0):
    """Synthesize one circular reel strip that hits the N1 / NAR targets."""
    symbol_count = len(symbol_index)
    length = sum(counts.values())
    seq = np.empty(length, dtype=np.int64)
    cursor = 0
    for code, count in counts.items():
        seq[cursor:cursor + count] = symbol_index[code]
        cursor += count
    rng = np.random.default_rng(seed)
    rng.shuffle(seq)
    n1_target = np.zeros(symbol_count)
    nar_target = np.zeros(symbol_count)
    for code, count in counts.items():
        f = count / length
        n1_target[symbol_index[code]] = length * f * f
        nar_target[symbol_index[code]] = theta * length * 6.0 * f * f
    scatter_id = symbol_index[scatter_code] if scatter_code else -1
    for _ in range(20_000):
        if scatter_id < 0 or _scatter_ok(seq, scatter_id, scatter_gap):
            break
        rng.shuffle(seq)
    else:
        raise ValueError("cannot find a scatter-legal starting arrangement")
    seq, score = _anneal(seq, symbol_count, n1_target, nar_target, float(n1_weight), 1.0,
                         int(iterations), seed & 0x7FFFFFFF, scatter_id, scatter_gap, max_run)
    inverse = {value: key for key, value in symbol_index.items()}
    return [inverse[int(value)] for value in seq], float(score)


def window_matrix(sequence, symbols):
    values = np.array([symbols.index(code) for code in sequence])
    return np.stack([np.roll(values, -offset) for offset in range(5)], axis=1)


def window_stats(sequence, symbols):
    """Exact 5-window statistics over all L circular stop positions."""
    length = len(sequence)
    windows = window_matrix(sequence, symbols)
    out = {}
    overall = np.zeros(length, dtype=np.int64)
    for index, code in enumerate(symbols):
        mask = windows == index
        count = mask.sum(axis=1)
        run = np.zeros(length, dtype=np.int64)
        current = np.zeros(length, dtype=np.int64)
        for column in range(5):
            current = np.where(mask[:, column], current + 1, 0)
            run = np.maximum(run, current)
        overall = np.maximum(overall, run)
        out[code] = {
            "count_dist": np.bincount(count, minlength=6) / length,
            "run_dist": np.bincount(run, minlength=6)[1:6] / length,
            "mean": float(count.mean()),
            "var": float(count.var()),
        }
    out["__window_longest__"] = np.bincount(overall, minlength=6)[1:6] / length
    return out
