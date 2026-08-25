"""H027 競品對齊 — 數學模型擬合與版本挑選.

用途
----
1. 依競品分析報告的每一項可對齊指標，合成 H027 的四張輪帶（`--strips`）。
2. 依「總 RTP = 版本標籤、BG RTP = 競品整數值」重新校準 Card System（`--cards`）。
3. 掃過候選參數組合、對每個候選評分，挑出綜合偏差最小的版本（`--search`）。

只改 config.js / config_92A.js / config_94A.js，不改 Source/*.xlsx，也不改 Simulator.py。

數學模型見 `strip_model.py` 的模組說明；卡片投影見本檔 `project_shape`。
"""

from __future__ import annotations

import argparse
import copy
import itertools
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from competitor_targets import NORMAL_SYMBOLS, REELS, SCENES, SYMBOL_ORDER, Targets
from strip_model import build_reel, largest_remainder, window_matrix

ROOT = Path(__file__).resolve().parent.parent
OTHER = ROOT / "其他"
RECORD = ROOT / "Record"
CONFIG_BASE = ROOT / "config.js"
CONFIG_VARIANTS = [ROOT / "config_92A.js", ROOT / "config_94A.js"]

# 輪帶名稱 -> 競品場景（沿用既有 config 的表格角色）
STRIP_SCENE = {
    "BG_Symbol": "BF",          # Buy Feature 進場盤面
    "BG_Symbol (2)": "BG",      # Normal Bet 一般遊戲
    "FG_Symbol": "FG",          # 自然觸發免費遊戲
    "FG_Symbol (2)": "BF",      # Buy Feature 免費遊戲
}
SCENE_FOR_MULTIPLIER = {"BG_Symbol": "BF", "BG_Symbol (2)": "BG", "FG_Symbol": "FG", "FG_Symbol (2)": "BF"}
SYMBOL_INDEX = {code: index for index, code in enumerate(SYMBOL_ORDER)}
NORMAL_INDEX = [SYMBOL_INDEX[code] for code in NORMAL_SYMBOLS]
C1_INDEX, C2_INDEX = SYMBOL_INDEX["C1"], SYMBOL_INDEX["C2"]

TARGETS = Targets()


# --------------------------------------------------------------------------- io

def load_js(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8-sig")
    start, end = text.index("{"), text.rindex("}")
    return json.loads(text[start:end + 1]), text[:start]


def write_js(path: Path, data: dict, prefix: str) -> None:
    path.write_text(prefix + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


# ------------------------------------------------------------------ strip build

def symbol_counts(scene: str, reel: str, length: int, c2_count: int) -> dict[str, int]:
    """Allocate strip cells; C2 count is set explicitly because the report's ball
    marginal and its ball-per-spin rate are on different denominators."""
    marginal = TARGETS.initial[scene][reel]
    others = [code for code in SYMBOL_ORDER if code != "C2"]
    allocated = largest_remainder([marginal[code] for code in others], length - c2_count)
    counts = dict(zip(others, allocated))
    counts["C2"] = c2_count
    return {code: counts[code] for code in SYMBOL_ORDER}


def build_scene_strip(scene: str, theta: float, c2_count: int, length: int,
                      seed: int, max_run: int, iterations: int, n1_weight: float = 1.0) -> list[list[str]]:
    reels = []
    for index, reel in enumerate(REELS):
        sequence, _ = build_reel(
            symbol_counts(scene, reel, length, c2_count), SYMBOL_INDEX, theta,
            seed + index, max_run=max_run, iterations=iterations, n1_weight=n1_weight,
        )
        reels.append(sequence)
    return reels


def board_metrics(reels: list[list[str]], rounds: int = 400_000, seed: int = 7) -> dict:
    """Initial-board metrics by Monte Carlo over independent reel stops."""
    rng = np.random.default_rng(seed)
    length = len(reels[0])
    windows = np.stack([window_matrix(reel, SYMBOL_ORDER) for reel in reels])
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
    tiers = np.array([
        ((normal >= 8) & (normal <= 9)).sum(),
        ((normal >= 10) & (normal <= 11)).sum(),
        (normal >= 12).sum(),
    ], dtype=float)
    flat = stack.reshape(-1)
    ball = counts[:, C2_INDEX]
    present = float((ball >= 1).mean())
    return {
        "initial_hit": float((normal >= 8).any(axis=1).mean()),
        "stack": [float((flat == size).mean()) for size in range(1, 6)],
        "cluster_tiers": (tiers / tiers.sum()).tolist(),
        "ball_present": present,
        "ball_counts": [float((ball == k).mean() / present) if present else 0.0 for k in (1, 2, 3, 4)],
        "scatter_ge4": float((counts[:, C1_INDEX] >= 4).mean()),
    }


def solve_theta(scene: str, c2_count: int, length: int, seed: int, max_run: int,
                iterations: int, target_hit: float, bounds=(0.0, 9.0), steps: int = 12) -> tuple[float, dict]:
    """Bisect the clustering parameter so the initial-board hit rate hits target."""
    low, high = bounds
    best = None
    for _ in range(steps):
        mid = (low + high) / 2.0
        reels = build_scene_strip(scene, mid, c2_count, length, seed, max_run, iterations)
        metrics = board_metrics(reels, rounds=200_000)
        if best is None or abs(metrics["initial_hit"] - target_hit) < abs(best[1]["initial_hit"] - target_hit):
            best = (mid, metrics, reels)
        if metrics["initial_hit"] < target_hit:
            low = mid
        else:
            high = mid
        if abs(metrics["initial_hit"] - target_hit) < 0.0008:
            break
    return best[0], {"metrics": best[1], "reels": best[2]}


# -------------------------------------------------------------- config assembly

def cumulative(values) -> list[int]:
    total = 0
    out = []
    for value in values:
        total += int(value)
        out.append(total)
    return out


def apply_strips(config: dict, scene_reels: dict[str, list[list[str]]]) -> None:
    code_to_id = dict(zip(config["symbol_codes"], config["symbol_ids"]))
    by_name = dict(zip(config["strip_names"], config["strips"]))
    for name, scene in STRIP_SCENE.items():
        reels = scene_reels[name]
        length = len(reels[0])
        strip = by_name[name]
        strip["symbols"] = [[code_to_id[reels[reel][row]] for reel in range(6)] for row in range(length)]
        strip["weights"] = [[1] * 6 for _ in range(length)]
        strip["reel_lengths"] = [length] * 6
        drop = [[0] * 6 for _ in range(len(config["symbol_ids"]))]
        for reel_index, reel in enumerate(REELS):
            probabilities = [TARGETS.drop[scene][reel].get(code, 0.0) for code in SYMBOL_ORDER]
            weights = largest_remainder(probabilities, 1_000_000)
            for code, weight in zip(SYMBOL_ORDER, weights):
                drop[code_to_id[code] - 1][reel_index] = weight
        strip["drop_weights"] = drop


def apply_multiplier_weights(config: dict) -> None:
    """C2 倍率權重 = 競品倍數值分布；C3 / Super Multiplier 關閉（競品無此機制）。"""
    levels = list(config["multiplier_levels"])
    for profile_name in ("normal", "featurebuy"):
        profile = config["parameter"][profile_name]
        profile["use_super_multiplier"]["weights_by_initial_ball_count"] = {
            table: [0, 0, 0, 0, 0, 0] for table in profile["use_super_multiplier"]["table_names"]
        }
        profile["c2"]["multipliers"] = levels
        for table in profile["c2"]["table_names"]:
            scene = SCENE_FOR_MULTIPLIER[table]
            share = dict(zip([2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 50, 100, 250, 500],
                             TARGETS.multiplier_dist[scene]))
            # a level value can repeat in multiplier_levels; only the first slot carries weight
            weights = [0] * len(levels)
            used = set()
            probabilities = []
            slots = []
            for index, value in enumerate(levels):
                if value in share and value not in used:
                    used.add(value)
                    slots.append(index)
                    probabilities.append(share[value])
            allocated = largest_remainder(probabilities, 10_000)
            for index, weight in zip(slots, allocated):
                weights[index] = weight
            profile["c2"]["weights"][table] = weights
            profile["c2"]["weights_cum"][table] = cumulative(weights)


def apply_table_roles(config: dict) -> None:
    normal = config["parameter"]["normal"]
    feature = config["parameter"]["featurebuy"]
    normal["base_reel_weights"] = [0, 1]
    normal["base_reel_weights_cum"] = [0, 1]
    feature["base_reel_weights"] = [1, 0]
    feature["base_reel_weights_cum"] = [1, 1]
    normal["free_table"]["initial"] = [15, 0]
    normal["free_table"]["retrigger"] = [5, 0]
    feature["free_table"]["initial"] = [0, 15]
    feature["free_table"]["retrigger"] = [0, 5]


def sync_physical(base: dict, target: dict) -> None:
    for key in ("strip_names", "strips", "multiplier_levels"):
        target[key] = copy.deepcopy(base[key])
    target["parameter"]["super_multiplier"] = copy.deepcopy(base["parameter"]["super_multiplier"])
    for profile_name in ("normal", "featurebuy"):
        for key in ("base_reel_names", "base_reel_weights", "base_reel_weights_cum",
                    "free_table", "use_super_multiplier", "c2", "c3"):
            target["parameter"][profile_name][key] = copy.deepcopy(base["parameter"][profile_name][key])


def validate_strips(config: dict, c2_counts: dict[str, int]) -> None:
    id_to_code = {int(v): k for k, v in zip(config["symbol_codes"], config["symbol_ids"])}
    code_to_id = dict(zip(config["symbol_codes"], config["symbol_ids"]))
    for name, strip in zip(config["strip_names"], config["strips"]):
        scene = STRIP_SCENE[name]
        length = len(strip["symbols"])
        if any(len(row) != 6 for row in strip["symbols"]):
            raise ValueError(f"{name}: symbol rows must have 6 reels")
        if any(value != 1 for row in strip["weights"] for value in row):
            raise ValueError(f"{name}: Symbol Weight must stay 1")
        if strip["reel_lengths"] != [length] * 6:
            raise ValueError(f"{name}: reel_lengths mismatch")
        for reel_index, reel in enumerate(REELS):
            sequence = [id_to_code[row[reel_index]] for row in strip["symbols"]]
            expected = symbol_counts(scene, reel, length, c2_counts[scene])
            for code in SYMBOL_ORDER:
                if sequence.count(code) != expected[code]:
                    raise ValueError(f"{name} {reel} {code}: count {sequence.count(code)} != {expected[code]}")
        for reel_index in range(6):
            if sum(row[reel_index] for row in strip["drop_weights"]) != 1_000_000:
                raise ValueError(f"{name} R{reel_index + 1}: drop weights must sum to 1,000,000")
        scatter = code_to_id["C1"]
        for reel_index in range(6):
            positions = [row for row, values in enumerate(strip["symbols"]) if values[reel_index] == scatter]
            if len(positions) > 1:
                gaps = [(positions[(i + 1) % len(positions)] - positions[i]) % length for i in range(len(positions))]
                if min(gaps) < 6:
                    raise ValueError(f"{name} R{reel_index + 1}: C1 circular gap below 6")


# ------------------------------------------------------------------- simulation

def run_simulator(config_file: str, config_rtp_file: str, bet_mode: int, rounds: int,
                  card_system: bool, newbie: bool, seed: int, base_bet: float = 1.0) -> Path:
    env = dict(os.environ)
    env.update({
        "H027_CONFIG_FILE": config_file,
        "H027_CONFIG_RTP_FILE": config_rtp_file,
        "H027_BET_MODE": str(bet_mode),
        "H027_TOTAL_ROUNDS": str(rounds),
        "H027_CARD_SYSTEM_ENABLED": "true" if card_system else "false",
        "H027_CARD_SYSTEM_IS_NEWBIE": "true" if newbie else "false",
        "H027_BASE_BET": str(base_bet),
        "H027_RUN_ALL_COMBINATIONS": "false",
        "H027_OUTPUT_REPORT": "true",
        "H027_SHOW_CONSOLE_SUMMARY": "false",
        "H027_RANDOM_SEED": str(seed),
    })
    before = set(RECORD.glob("*.xlsx"))
    result = subprocess.run([sys.executable, str(ROOT / "Simulator.py")], cwd=str(ROOT),
                            env=env, capture_output=True, text=True, errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"Simulator failed:\n{result.stdout[-4000:]}\n{result.stderr[-4000:]}")
    after = set(RECORD.glob("*.xlsx")) - before
    if not after:
        raise RuntimeError("Simulator produced no report")
    return max(after, key=lambda path: path.stat().st_mtime)


def probe_natural_fg(rounds: int, seed: int = 27301) -> Path:
    """Sample the natural-FG (FG_Symbol) session distribution at full sample size.

    A Normal Bet run only produces ~1/625 FG sessions, far too few to calibrate the
    64-interval FG card weights.  This writes a throw-away config whose Buy Feature
    profile draws the *natural* FG table, runs Buy Feature once per round, and then
    deletes the probe config again.  Physics is untouched: FG_Symbol, its drop table
    and its C2 weights are the same objects a natural trigger would use.
    """
    probe_path = ROOT / "config_probe_natural_fg.js"
    config, prefix = load_js(CONFIG_BASE)
    config["parameter"]["featurebuy"]["free_table"]["initial"] = [15, 0]
    config["parameter"]["featurebuy"]["free_table"]["retrigger"] = [5, 0]
    config["config_code"] = "probe_natural_fg"
    write_js(probe_path, config, prefix)
    try:
        return run_simulator(probe_path.name, probe_path.name, 2, rounds, False, False, seed)
    finally:
        probe_path.unlink(missing_ok=True)


def interval_table(path: Path) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name="Multiplier Line")


def interval_stats(frame: pd.DataFrame, count_col: str, pay_col: str, denominator: float):
    counts = frame[count_col].to_numpy(dtype=float)
    pays = frame[pay_col].to_numpy(dtype=float)
    total = counts.sum()
    natural = counts / total if total else np.zeros_like(counts)
    averages = np.where(counts > 0, pays / np.maximum(counts, 1) / denominator, 0.0)
    return natural, averages


# ------------------------------------------------------------- card calibration

def project_shape(shape, averages, total_mass, target_mean, allowed):
    """Closest distribution (L2) to `shape` on the allowed intervals with the given
    total mass and mean.  Active-set: drop negative components and re-solve."""
    active = [index for index, ok in enumerate(allowed) if ok]
    result = np.zeros(len(shape))
    while True:
        if len(active) < 2:
            raise ValueError("not enough eligible intervals for the mean constraint")
        base_total = sum(shape[index] for index in active)
        if base_total <= 0:
            raise ValueError("eligible intervals carry no reference mass")
        q = np.array([shape[index] / base_total * total_mass for index in active])
        a = np.array([averages[index] for index in active])
        n = len(active)
        m00, m01, m11 = float(n), float(a.sum()), float((a * a).sum())
        r0 = total_mass - q.sum()
        r1 = target_mean - float((a * q).sum())
        determinant = m00 * m11 - m01 * m01
        if abs(determinant) < 1e-12:
            raise ValueError("degenerate interval averages")
        lam0 = (r0 * m11 - r1 * m01) / determinant
        lam1 = (m00 * r1 - m01 * r0) / determinant
        candidate = q + lam0 + lam1 * a
        negative = [(value, position) for position, value in enumerate(candidate) if value < -1e-12]
        if not negative:
            for index, value in zip(active, candidate):
                result[index] = max(0.0, value)
            return result
        active.pop(min(negative)[1])


def remap_shape(shape, allowed, uppers):
    mapped = np.zeros(len(shape))
    valid = [index for index, ok in enumerate(allowed) if ok]
    if not valid:
        raise ValueError("no eligible intervals")
    for index, mass in enumerate(shape):
        if mass <= 0:
            continue
        nearest = min(valid, key=lambda candidate: abs(uppers[candidate] - uppers[index]))
        mapped[nearest] += mass
    return mapped / mapped.sum()


def update_card_list(cards: list[dict], weights, free_game_weight: int | None = None) -> None:
    ranges = [card for card in cards if card.get("type", "range") == "range"]
    if len(ranges) != len(weights):
        raise ValueError(f"card range count {len(ranges)} != weight count {len(weights)}")
    for card, weight in zip(ranges, weights):
        card["weight"] = int(weight)
    if free_game_weight is not None:
        free_cards = [card for card in cards if card.get("type") == "free_game"]
        if len(free_cards) != 1:
            raise ValueError("normal BG card list must hold exactly one free_game card")
        free_cards[0]["weight"] = int(free_game_weight)


def iter_card_modes(card_system: dict):
    for player in ("newbie", "oldhand"):
        player_data = card_system[player]
        for mode in ("normal_bet", "buy_feature"):
            mode_data = player_data[mode]
            if player == "newbie":
                yield mode, mode_data
            else:
                for tier_data in mode_data.values():
                    yield mode, tier_data


def calibrate_cards(natural_normal: Path, natural_bf: Path, natural_fg: Path, cycle: float,
                    bg_rtp_target: float, threshold: float = 0.0004,
                    variants: list[Path] | None = None, verbose: bool = True,
                    bg_rtp_offset: float = 0.0) -> dict:
    """Set every card weight so that, for each RTP variant:
        BG RTP   = bg_rtp_target (competitor value truncated to an integer percent)
        total RTP= rtp_label
        FG cycle = the requested cycle
    while keeping the 64-interval shapes as close to the competitor as the natural
    model allows (minimum-L2 projection).
    """
    variants = variants or CONFIG_VARIANTS
    targets = TARGETS.interval_shape()
    normal_frame = interval_table(natural_normal)
    bf_frame = interval_table(natural_bf)
    fg_frame = interval_table(natural_fg)
    uppers = normal_frame["Interval_Upper"].to_numpy(dtype=float)

    bg_natural, bg_avg = interval_stats(normal_frame, "base_game_cnt", "base_game_pay", 500.0)
    fg_natural, fg_avg = interval_stats(fg_frame, "free_game_cnt_BF", "free_game_pay_BF", 500.0)
    bf_natural, bf_avg = interval_stats(bf_frame, "free_game_cnt_BF", "free_game_pay_BF", 500.0)

    bg_allowed = bg_natural >= threshold
    fg_allowed = fg_natural >= threshold
    bf_allowed = bf_natural >= threshold
    bg_shape = remap_shape(targets["BG"], bg_allowed, uppers)
    fg_shape = remap_shape(targets["FG"], fg_allowed, uppers)
    bf_shape = remap_shape(targets["BF"], bf_allowed, uppers)

    trigger_probability = 1.0 / cycle
    free_game_weight = round(trigger_probability / (1.0 - trigger_probability) * 1_000_000_000)

    bg_hit_target = TARGETS.basic["bg_hit_rate"]
    positive_mass = (bg_hit_target - trigger_probability) / (1.0 - trigger_probability)
    positive_allowed = bg_allowed.copy()
    positive_allowed[0] = False
    positive_shape = bg_shape.copy()
    positive_shape[0] = 0.0

    trigger_counts = normal_frame["bg_trigger_fg_cnt_lte_upper"].to_numpy(dtype=float)
    trigger_pays = normal_frame["bg_trigger_fg_pay_lte_upper"].to_numpy(dtype=float)
    cap_index = max(index for index, ok in enumerate(positive_allowed) if ok)
    trigger_mean = trigger_pays[cap_index] / trigger_counts[cap_index] / 500.0 if trigger_counts[cap_index] else 0.0

    summary = {}
    for path in variants:
        config, prefix = load_js(path)
        label = float(config.get("rtp_label", 92))
        label = label / 100.0 if label > 1.5 else label
        # BG RTP is fixed; the FG contribution is whatever the total needs.
        fg_contribution = label - bg_rtp_target
        if fg_contribution <= 0:
            raise ValueError(f"{path.name}: BG RTP target leaves no room for FG")
        fg_mean_target = fg_contribution / trigger_probability
        # One Newton step: the BG range means a_i are measured on the natural run,
        # which still contains the FG-triggering rounds that a range card rejects,
        # so the solved BG RTP lands slightly low.  The offset is the measured gap
        # (see 其他/數值版本挑選_H027.md §5.1) fed back into the solve.
        range_mean = ((bg_rtp_target + bg_rtp_offset - trigger_probability * trigger_mean)
                      / (1.0 - trigger_probability))
        bg_probabilities = project_shape(positive_shape, bg_avg, positive_mass, range_mean, positive_allowed)
        bg_probabilities[0] = 1.0 - positive_mass
        fg_probabilities = project_shape(fg_shape, fg_avg, 1.0, fg_mean_target, fg_allowed)
        bf_probabilities = project_shape(bf_shape, bf_avg, 1.0, label * TARGETS.basic["bf_price"], bf_allowed)

        bg_weights = largest_remainder(bg_probabilities, 1_000_000_000)
        fg_weights = largest_remainder(fg_probabilities, 1_000_000_000)
        bf_weights = largest_remainder(bf_probabilities, 1_000_000_000)
        config["card_system"]["fg_entry_cycle_target"] = cycle
        config["card_system"]["bg_rtp_target"] = bg_rtp_target
        config["card_system"]["bg_rtp_solve_offset"] = bg_rtp_offset
        config["card_system"]["calibration"] = {
            "rtp_family": int(round(label * 100)),
            "method": "L2 projection onto the competitor 64-interval line",
            "bg_rtp_target": bg_rtp_target,
            "bg_rtp_solve_offset": bg_rtp_offset,
            "total_rtp_target": label,
            "fg_entry_probability": trigger_probability,
            "fg_package_mean": fg_mean_target,
            "buy_package_mean": label * TARGETS.basic["bf_price"],
            "bg_hit_rate_target": bg_hit_target,
            # newbie and oldhand share one solve in the competitor baseline; the
            # per-player RTP split of the original XLSX model is not reinstated here
            "newbie_oldhand_split": "identical",
            "normal_report": natural_normal.name,
            "buy_report": natural_bf.name,
            "natural_fg_probe": natural_fg.name,
        }
        for mode, mode_data in iter_card_modes(config["card_system"]):
            if mode == "normal_bet":
                update_card_list(mode_data["weight_bg"], bg_weights, free_game_weight)
                update_card_list(mode_data["weight_fg"], fg_weights)
            else:
                update_card_list(mode_data["weight_fg"], bf_weights)
        write_js(path, config, prefix)
        expected_total = ((1.0 - trigger_probability) * float((bg_probabilities * bg_avg).sum())
                          + trigger_probability * (trigger_mean + fg_mean_target))
        summary[path.name] = {
            "label": label,
            "cycle": cycle,
            "fg_mean_target": fg_mean_target,
            "expected_bg_rtp": bg_rtp_target,
            "expected_total_rtp": expected_total,
            "expected_bg_hit": trigger_probability + (1 - trigger_probability) * float(bg_probabilities[1:].sum()),
            "eligible": [int(bg_allowed.sum()), int(fg_allowed.sum()), int(bf_allowed.sum())],
            # the card weights *are* the 64-interval line by construction, so expose
            # them for noise-free candidate comparison
            "interval_line": {"BG": bg_probabilities.tolist(),
                              "FG": fg_probabilities.tolist(),
                              "BF": bf_probabilities.tolist()},
        }
        if verbose:
            info = summary[path.name]
            print(f"  {path.name}: BG RTP={bg_rtp_target:.2%} total={info['expected_total_rtp']:.4%} "
                  f"cycle=1/{cycle:.1f} FG avg={fg_mean_target:.2f}x BG hit={info['expected_bg_hit']:.4%} "
                  f"eligible={info['eligible']}")
    return summary


# ------------------------------------------------------------------ strip stage

# max_run / theta per scene come from the local screening documented in
# 其他/數值版本挑選_H027.md §3 (each scene scored on its own hit rate, stack
# distribution, cluster tier share and ball rate).
DEFAULT_PLAN = {
    "length": 1080,
    "max_run": {"BG": 4, "FG": 4, "BF": 3},
    "iterations": 60_000,
    "seed": 27_000,
    "c2_counts": {"BG": 1, "FG": 24, "BF": 19},
    # theta is re-bisected on every build: the annealer's solution quality is
    # seed-dependent, so a pinned value does not reproduce the same hit rate.
    "theta": None,
    "theta_bounds": {"BG": (0.2, 1.3), "FG": (1.4, 3.4), "BF": (1.2, 4.6)},
}


def build_all_strips(plan: dict, verbose: bool = True) -> dict:
    reels_by_scene: dict[str, list[list[str]]] = {}
    diagnostics = {}
    for offset, scene in enumerate(SCENES):
        c2 = plan["c2_counts"][scene]
        seed = plan["seed"] + offset * 100
        max_run = plan["max_run"][scene]
        if plan.get("theta") is not None and plan["theta"].get(scene) is not None:
            theta = float(plan["theta"][scene])
            reels = build_scene_strip(scene, theta, c2, plan["length"], seed, max_run, plan["iterations"])
            metrics = board_metrics(reels)
        else:
            theta, info = solve_theta(scene, c2, plan["length"], seed, max_run,
                                      plan["iterations"], TARGETS.initial_hit_target(scene),
                                      bounds=plan.get("theta_bounds", {}).get(scene, (0.0, 9.0)),
                                      steps=10)
            reels, metrics = info["reels"], info["metrics"]
        reels_by_scene[scene] = reels
        diagnostics[scene] = {"theta": theta, "max_run": max_run,
                              "c2_count": c2, "length": plan["length"], **metrics}
        if verbose:
            print(f"  {scene}: theta={theta:.3f} initial hit={metrics['initial_hit']:.4%} "
                  f"(target {TARGETS.initial_hit_target(scene):.4%}) "
                  f"stack={[f'{v:.3%}' for v in metrics['stack']]} "
                  f"ball={metrics['ball_present']:.3%} (target {TARGETS.ball_spin_rate[scene]:.3%})")
    scene_reels = {name: reels_by_scene[scene] for name, scene in STRIP_SCENE.items()}
    return {"scene_reels": scene_reels, "diagnostics": diagnostics}


def apply_strip_stage(plan: dict, verbose: bool = True) -> dict:
    built = build_all_strips(plan, verbose=verbose)
    base, prefix = load_js(CONFIG_BASE)
    variants = [load_js(path) for path in CONFIG_VARIANTS]
    apply_strips(base, built["scene_reels"])
    apply_table_roles(base)
    apply_multiplier_weights(base)
    base["strip_length"] = plan["length"]
    base["competitor_fit"] = {
        "model": "pair-distance clustering (see 其他/strip_model.py)",
        "strip_length": plan["length"],
        "max_run": plan["max_run"],
        "theta": {scene: round(built["diagnostics"][scene]["theta"], 4) for scene in SCENES},
        "c2_counts": plan["c2_counts"],
    }
    validate_strips(base, plan["c2_counts"])
    write_js(CONFIG_BASE, base, prefix)
    for path, (config, variant_prefix) in zip(CONFIG_VARIANTS, variants):
        sync_physical(base, config)
        config["competitor_fit"] = copy.deepcopy(base["competitor_fit"])
        validate_strips(config, plan["c2_counts"])
        write_js(path, config, variant_prefix)
    return built["diagnostics"]


# ------------------------------------------------------------------------- main

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strips", action="store_true", help="synthesize and write the four reel strips")
    parser.add_argument("--cards", action="store_true", help="re-calibrate Card System weights")
    parser.add_argument("--cycle", type=float, default=TARGETS.basic["fg_cycle"])
    parser.add_argument("--bg-rtp", type=float, default=0.59)
    parser.add_argument("--bg-rtp-offset", type=float, default=0.0039)
    parser.add_argument("--length", type=int, default=DEFAULT_PLAN["length"])
    parser.add_argument("--resolve-theta", action="store_true",
                        help="re-bisect theta instead of using the pinned values")
    parser.add_argument("--iterations", type=int, default=DEFAULT_PLAN["iterations"])
    parser.add_argument("--seed", type=int, default=DEFAULT_PLAN["seed"])
    parser.add_argument("--natural-rounds", type=int, default=10 ** 6)
    args = parser.parse_args()

    if args.strips:
        plan = dict(DEFAULT_PLAN)
        plan.update({"length": args.length, "iterations": args.iterations, "seed": args.seed})
        if args.resolve_theta:
            plan["theta"] = None
        print("[strips] synthesizing")
        diagnostics = apply_strip_stage(plan)
        (OTHER / "fit_strip_diagnostics.json").write_text(
            json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.cards:
        print("[cards] natural reference runs")
        normal = run_simulator("config.js", "config.js", 0, args.natural_rounds, False, False, 27001)
        bf = run_simulator("config.js", "config.js", 2, args.natural_rounds, False, False, 27201)
        fg = probe_natural_fg(args.natural_rounds)
        print(f"  normal={normal.name}\n  bf={bf.name}\n  natural-fg probe={fg.name}")
        print("[cards] calibrating")
        summary = calibrate_cards(normal, bf, fg, args.cycle, args.bg_rtp,
                                  bg_rtp_offset=args.bg_rtp_offset)
        (OTHER / "fit_card_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
