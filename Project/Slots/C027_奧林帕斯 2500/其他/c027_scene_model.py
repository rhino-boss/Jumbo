"""C027 場景表混合（Scene Mixture）數學模型.

為什麼需要這個模型
------------------
競品報告 §5.2 顯示「盤面有倍數球」時的 Hit Rate 明顯高於「沒有倍數球」
（BG 40.16% vs 21.72%、FG 50.60% vs 40.96%），但單一輪帶做不到這件事：
倍數球會佔掉一個格位，反而會**降低**該盤面的 Any-8 命中率。
競品報告自己也指出這可能同源於 `reel_set`（資料中有 0~4 共 5 種）。

H027 的結論是「需要跨輪 reel_set／場景表才能同時對齊」，但沒有實作。
C027 把它實作出來：每個場景由兩張子輪帶表混合，
每一轉（BG）或每一次免費遊戲轉（FG）**獨立**抽一張子表。

    A 表：倍數球多、聚集度 θ_A 高（好中獎）
    B 表：完全沒有倍數球、聚集度 θ_B 低

混合後就能同時控制
    P(有球)、Hit Rate、Hit Rate|有球、Hit Rate|無球
四個原本互相打死的量。

邊際分布為什麼不會被破壞
------------------------
子表 k 的 C2 格數為 `c2_k`、混合權重 `w_k`、輪帶長度 `L`。只要

    Σ_k w_k · c2_k = L · s            （s = 競品該輪的 C2 邊際占比）

並且每張子表的「非 C2 符號」按競品邊際比例分配到剩下的 `L − c2_k` 格，
那麼混合後每個非 C2 符號的占比為

    Σ_k w_k · f_c/(1−s) · (1 − c2_k/L) = f_c/(1−s) · (1−s) = f_c

也就是**與競品邊際完全相同**，不是近似。掉落表則讓同場景的子表共用一份
競品掉落邊際，因此掉落分布也精確保持。

自由度整理
----------
每個場景的自由參數是 `c2_A`（整數）、`θ_A`、`θ_B`；`w_A` 由上式決定，
`w_B = 1 − w_A`。三個自由參數對四個目標，最後一個目標（整體 Hit Rate）
是前三個的線性組合，因此是相容的，不是超定。
"""

from __future__ import annotations

import numpy as np

from strip_model import build_reel, largest_remainder, window_matrix

SYMBOL_ORDER = ["C1", "M1", "M2", "M3", "M4", "A", "K", "Q", "J", "TE", "C2"]
NORMAL_SYMBOLS = SYMBOL_ORDER[1:10]
SYMBOL_INDEX = {code: index for index, code in enumerate(SYMBOL_ORDER)}
NORMAL_INDEX = [SYMBOL_INDEX[code] for code in NORMAL_SYMBOLS]
C1_INDEX, C2_INDEX = SYMBOL_INDEX["C1"], SYMBOL_INDEX["C2"]
REELS = [f"R{index}" for index in range(1, 7)]


def sub_symbol_counts(marginal: dict[str, float], length: int, c2_count: int) -> dict[str, int]:
    """Allocate one sub-table's strip cells so the mixture keeps the pooled marginal.

    `marginal` is the competitor share for this scene and reel.  The C2 cells are
    set explicitly; every other symbol shares the remaining cells in competitor
    proportion, which is exactly what the mixture identity in the module docstring
    requires.
    """
    others = [code for code in SYMBOL_ORDER if code != "C2"]
    allocated = largest_remainder([marginal[code] for code in others], length - c2_count)
    counts = dict(zip(others, allocated))
    counts["C2"] = c2_count
    return {code: counts[code] for code in SYMBOL_ORDER}


def mixture_weight_for(c2_share: float, length: int, c2_count: int) -> float:
    """w_A that keeps the pooled C2 marginal, given a ball-free B table."""
    if c2_count <= 0:
        raise ValueError("the ball-carrying sub-table needs at least one C2 cell")
    weight = c2_share * length / c2_count
    if not 0.0 < weight <= 1.0:
        raise ValueError(f"c2_count={c2_count} implies an out-of-range mixture weight {weight:.4f}")
    return weight


def build_sub_reels(marginals: dict[str, dict[str, float]], length: int, c2_count: int,
                    theta: float, seed: int, max_run: int, iterations: int) -> list[list[str]]:
    return [
        build_reel(sub_symbol_counts(marginals[reel], length, c2_count), SYMBOL_INDEX,
                   theta, seed + index, max_run=max_run, iterations=iterations)[0]
        for index, reel in enumerate(REELS)
    ]


def _windows(reels: list[list[str]]) -> np.ndarray:
    return np.stack([window_matrix(reel, SYMBOL_ORDER) for reel in reels])


def sub_board_sample(reels: list[list[str]], rounds: int, seed: int) -> dict[str, np.ndarray]:
    """Sample initial boards from one sub-table and return the per-board statistics."""
    rng = np.random.default_rng(seed)
    length = len(reels[0])
    windows = _windows(reels)
    stops = rng.integers(0, length, size=(rounds, 6))
    board = np.empty((rounds, 30), dtype=np.int8)
    stack = np.empty((rounds, 6), dtype=np.int8)
    for reel_index in range(6):
        view = windows[reel_index][stops[:, reel_index]]
        board[:, reel_index * 5:(reel_index + 1) * 5] = view
        current = np.ones(rounds, dtype=np.int8)
        longest = np.ones(rounds, dtype=np.int8)
        for column in range(1, 5):
            current = np.where(view[:, column] == view[:, column - 1], current + 1, 1)
            longest = np.maximum(longest, current)
        stack[:, reel_index] = longest
    counts = np.empty((rounds, len(SYMBOL_ORDER)), dtype=np.int8)
    for index in range(len(SYMBOL_ORDER)):
        counts[:, index] = (board == index).sum(axis=1)
    normal = counts[:, NORMAL_INDEX]
    return {
        "hit": (normal >= 8).any(axis=1),
        "balls": counts[:, C2_INDEX],
        "scatter": counts[:, C1_INDEX],
        "stack": stack.reshape(-1),
        "tier_8_9": ((normal >= 8) & (normal <= 9)).sum(axis=1),
        "tier_10_11": ((normal >= 10) & (normal <= 11)).sum(axis=1),
        "tier_12": (normal >= 12).sum(axis=1),
    }


def mixture_metrics(samples: list[dict[str, np.ndarray]], weights: list[float]) -> dict:
    """Joint initial-board metrics of the weighted sub-table mixture."""
    weights = np.asarray(weights, dtype=float)
    weights = weights / weights.sum()
    hit = 0.0
    ball_present = 0.0
    hit_and_ball = 0.0
    ball_counts = np.zeros(5)
    stack = np.zeros(5)
    tiers = np.zeros(3)
    scatter_ge4 = 0.0
    for weight, sample in zip(weights, samples):
        has_ball = sample["balls"] >= 1
        hit += weight * float(sample["hit"].mean())
        ball_present += weight * float(has_ball.mean())
        hit_and_ball += weight * float((sample["hit"] & has_ball).mean())
        for index in range(1, 5):
            ball_counts[index] += weight * float((sample["balls"] == index).mean())
        for index in range(1, 6):
            stack[index - 1] += weight * float((sample["stack"] == index).mean())
        tiers += weight * np.array([
            float(sample["tier_8_9"].sum()), float(sample["tier_10_11"].sum()), float(sample["tier_12"].sum())
        ]) / len(sample["hit"])
        scatter_ge4 += weight * float((sample["scatter"] >= 4).mean())
    no_ball = 1.0 - ball_present
    return {
        "hit": hit,
        "ball_present": ball_present,
        "hit_given_ball": hit_and_ball / ball_present if ball_present > 0 else 0.0,
        "hit_given_no_ball": (hit - hit_and_ball) / no_ball if no_ball > 0 else 0.0,
        "ball_counts": (ball_counts[1:] / ball_present).tolist() if ball_present > 0 else [0.0] * 4,
        "stack": stack.tolist(),
        "cluster_tiers": (tiers / tiers.sum()).tolist() if tiers.sum() else [0.0, 0.0, 0.0],
        "scatter_ge4": scatter_ge4,
    }


def sample_hit(sample: dict[str, np.ndarray], condition: str = "all") -> float:
    """`all`, `ball` (hit rate on boards holding a ball) or `no_ball`."""
    if condition == "all":
        return float(sample["hit"].mean())
    mask = sample["balls"] >= 1 if condition == "ball" else sample["balls"] == 0
    return float(sample["hit"][mask].mean()) if mask.any() else 0.0


def solve_theta_for_hit(marginals, length, c2_count, target_hit, seed, max_run, iterations,
                        bounds=(0.05, 6.0), steps=11, rounds=150_000, tolerance=0.0008,
                        condition="all"):
    """Bisect the clustering parameter so one sub-table's hit rate hits target.

    `condition` selects which hit rate is matched, so the ball-carrying table can be
    solved directly on its `hit | ball` value — the number the competitor's §5.2
    table states, which is not the table's unconditional hit rate because a ball
    occupies one of the 30 cells.
    """
    low, high = bounds
    best = None
    for _ in range(steps):
        mid = (low + high) / 2.0
        reels = build_sub_reels(marginals, length, c2_count, mid, seed, max_run, iterations)
        sample = sub_board_sample(reels, rounds, seed ^ 0x5F5F)
        hit = sample_hit(sample, condition)
        if best is None or abs(hit - target_hit) < abs(best["hit"] - target_hit):
            best = {"theta": mid, "reels": reels, "hit": hit, "sample": sample}
        if hit < target_hit:
            low = mid
        else:
            high = mid
        if abs(hit - target_hit) < tolerance:
            break
    return best
