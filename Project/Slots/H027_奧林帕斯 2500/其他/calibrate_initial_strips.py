"""Reorder H027 score symbols to calibrate the initial-board win rate.

The script preserves, for every reel:
* the exact count of every symbol;
* the exact positions of C1/C2/C3;
* strip weights and drop weights.

Only the order of M1..TE in ``strips[].symbols`` is changed.
"""

from __future__ import annotations

import argparse
import copy
import random
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "Source"))
import model_sync


DEFAULT_CONFIG = ROOT / "config_92A.js"
SPECIAL_CODES = {"C1", "C2", "C3"}


def reorder_reel(original: list[int], score_ids: set[int], strength: float, seed: int) -> list[int]:
    """Build score-symbol runs while leaving special-symbol positions fixed."""
    rng = random.Random(seed)
    result = list(original)
    remaining = Counter(value for value in original if value in score_ids)
    previous = None

    for position, value in enumerate(original):
        if value not in score_ids:
            previous = None
            continue

        if previous is not None and remaining[previous] > 0 and rng.random() < strength:
            selected = previous
        else:
            symbols = [symbol for symbol, count in remaining.items() if count > 0]
            weights = [remaining[symbol] for symbol in symbols]
            selected = rng.choices(symbols, weights=weights, k=1)[0]

        result[position] = selected
        remaining[selected] -= 1
        previous = selected

    if any(remaining.values()):
        raise RuntimeError(f"Unconsumed symbols: {remaining}")
    return result


def build_candidate(symbols: list[list[int]], score_ids: set[int], strength: float, seed: int) -> list[list[int]]:
    matrix = np.asarray(symbols, dtype=np.int64)
    candidate = matrix.copy()
    for reel in range(matrix.shape[1]):
        candidate[:, reel] = reorder_reel(
            matrix[:, reel].tolist(), score_ids, strength, seed + reel * 1009
        )
    return candidate.tolist()


def initial_win_rate(symbols: list[list[int]], score_ids: list[int], samples: int, seed: int) -> float:
    """Estimate P(any score symbol appears at least eight times in 6x5)."""
    matrix = np.asarray(symbols, dtype=np.int16)
    rows, reels = matrix.shape
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, rows, size=(samples, reels), dtype=np.int32)
    counts = np.zeros((samples, len(score_ids)), dtype=np.uint8)

    sample_index = np.arange(samples)[:, None]
    reel_index = np.arange(reels)[None, :]
    for visible_row in range(5):
        board_row = matrix[(starts + visible_row) % rows, reel_index]
        for symbol_index, symbol_id in enumerate(score_ids):
            counts[:, symbol_index] += np.sum(board_row == symbol_id, axis=1).astype(np.uint8)
    return float(np.mean(np.any(counts >= 8, axis=1)))


def symbol_counts(symbols: list[list[int]]) -> list[Counter]:
    matrix = np.asarray(symbols, dtype=np.int64)
    return [Counter(matrix[:, reel].tolist()) for reel in range(matrix.shape[1])]


def search(strip: dict, score_ids: list[int], target: float, samples: int, seed: int) -> tuple[list[list[int]], float, float, int]:
    original = strip["symbols"]
    expected_counts = symbol_counts(original)
    score_set = set(score_ids)
    best = None

    # Broad search followed by two local refinements. Multiple seeds are tested
    # because count-preserving construction is discrete at a 300-stop length.
    strengths = [index / 100 for index in range(0, 96, 4)]
    for stage in range(3):
        stage_results = []
        for strength in strengths:
            for variant in range(4):
                candidate_seed = seed + stage * 100_000 + int(strength * 10_000) + variant * 10_007
                candidate = build_candidate(original, score_set, strength, candidate_seed)
                if symbol_counts(candidate) != expected_counts:
                    raise RuntimeError("Symbol counts changed during candidate construction")
                rate = initial_win_rate(candidate, score_ids, samples, candidate_seed + 77)
                result = (abs(rate - target), candidate, rate, strength, candidate_seed)
                stage_results.append(result)
                if best is None or result[0] < best[0]:
                    best = result

        stage_best = min(stage_results, key=lambda item: item[0])
        center = stage_best[3]
        step = 0.01 if stage == 0 else 0.0025
        strengths = sorted({max(0.0, min(0.99, center + offset * step)) for offset in range(-5, 6)})

    assert best is not None
    _, candidate, rate, strength, candidate_seed = best
    return candidate, rate, strength, candidate_seed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--bg-target", type=float, default=0.285512)
    parser.add_argument("--fg-target", type=float, default=0.438095)
    parser.add_argument("--samples", type=int, default=300_000)
    parser.add_argument("--verify-samples", type=int, default=3_000_000)
    parser.add_argument("--seed", type=int, default=2701)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    config = model_sync.load_js_config(args.config)
    if "BG_Symbol (2)" in config["parameter"]["normal"]["base_reel_names"]:
        raise RuntimeError(
            "BG two-table mode is active; use calibrate_bg_two_tables.py so the complementary marginals remain intact."
        )
    original_config = copy.deepcopy(config)
    code_to_id = dict(zip(config["symbol_codes"], config["symbol_ids"]))
    score_ids = [symbol_id for code, symbol_id in code_to_id.items() if code not in SPECIAL_CODES]
    targets = {"BG_Symbol": args.bg_target, "FG_Symbol": args.fg_target}

    for strip_index, strip_name in enumerate(config["strip_names"]):
        strip = config["strips"][strip_index]
        original_rate = initial_win_rate(
            strip["symbols"], score_ids, args.verify_samples, args.seed + strip_index * 1_000_000
        )
        candidate, search_rate, strength, candidate_seed = search(
            strip,
            score_ids,
            targets[strip_name],
            args.samples,
            args.seed + strip_index * 10_000_000,
        )
        verified_rate = initial_win_rate(
            candidate, score_ids, args.verify_samples, args.seed + strip_index * 1_000_000 + 991
        )
        strip["symbols"] = candidate
        print(
            f"{strip_name}: original={original_rate:.6%}, target={targets[strip_name]:.6%}, "
            f"search={search_rate:.6%}, verified={verified_rate:.6%}, "
            f"strength={strength:.4f}, seed={candidate_seed}"
        )

    for before, after, strip_name in zip(
        original_config["strips"], config["strips"], config["strip_names"]
    ):
        if symbol_counts(before["symbols"]) != symbol_counts(after["symbols"]):
            raise RuntimeError(f"{strip_name}: symbol distribution changed")
        if before["weights"] != after["weights"]:
            raise RuntimeError(f"{strip_name}: strip weights changed")
        if before.get("drop_weights") != after.get("drop_weights"):
            raise RuntimeError(f"{strip_name}: drop weights changed")
        before_matrix = np.asarray(before["symbols"])
        after_matrix = np.asarray(after["symbols"])
        for special_id in (code_to_id["C1"], code_to_id["C2"], code_to_id["C3"]):
            if not np.array_equal(before_matrix == special_id, after_matrix == special_id):
                raise RuntimeError(f"{strip_name}: special symbol positions changed")

    if args.write:
        model_sync.write_js_config(args.config, config)
        print(f"Updated {args.config}")
    else:
        print("Dry run only; pass --write to update config.")


if __name__ == "__main__":
    main()
