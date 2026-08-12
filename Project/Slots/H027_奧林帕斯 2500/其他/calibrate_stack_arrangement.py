"""Reorder H027 strips to match competitor initial vertical stack lengths.

Symbol counts and all drop weights remain unchanged. Each reel strip is rebuilt
from runs of length 1, 2, or 3, targeting the competitor's per-symbol stack
distribution (mostly Stack 2 with fewer Stack 3 cells). The cyclic arranger
then maximizes spacing between separate runs of the same symbol; Stack 4/5 is
never allowed.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "Source"))
import model_sync
from analyze_stack_distribution import DEFAULT_INPUT, SCENE_TABLES, analyze


DEFAULT_CONFIG = ROOT / "config_92A.js"
SPECIAL_CODES = {"C1", "C2", "C3"}


def make_runs(count: int, probabilities: tuple[float, float, float], rng: random.Random) -> list[int]:
    runs = []
    remaining = count
    while remaining:
        lengths = [length for length in (1, 2, 3) if length <= remaining]
        weights = [probabilities[length - 1] for length in lengths]
        if not any(weights):
            selected = 1
        else:
            selected = rng.choices(lengths, weights=weights, k=1)[0]
        runs.append(selected)
        remaining -= selected
    return runs


def cyclic_run_gaps(sequence: list[int]) -> list[tuple[int, int, int]]:
    """Return (symbol, run length, following gap) for every cyclic run."""
    if not sequence:
        return []
    runs = []
    start = 0
    for index in range(1, len(sequence) + 1):
        if index == len(sequence) or sequence[index] != sequence[start]:
            runs.append([sequence[start], index - start, 0])
            start = index
    if len(runs) > 1 and runs[0][0] == runs[-1][0]:
        runs[0][1] += runs[-1][1]
        runs.pop()
    for index, run in enumerate(runs):
        next_same = next(
            offset
            for offset in range(1, len(runs) + 1)
            if runs[(index + offset) % len(runs)][0] == run[0]
        )
        run[2] = sum(runs[(index + offset) % len(runs)][1] for offset in range(1, next_same))
    return [tuple(run) for run in runs]


def validate_sequence(
    sequence: list[int], min_separate_gap: int = 4,
    symbol_min_gaps: dict[int, int] | None = None,
) -> None:
    symbol_min_gaps = symbol_min_gaps or {}
    violations = [
        (symbol, run_length, gap)
        for symbol, run_length, gap in cyclic_run_gaps(sequence)
        if run_length > 3 or gap < symbol_min_gaps.get(symbol, min_separate_gap)
    ]
    if violations:
        raise ValueError(f"Invalid cyclic run arrangement: {violations[:5]}")


def arrange_runs(
    runs_by_symbol: dict[int, list[int]], seed: int, min_separate_gap: int = 4,
    symbol_min_gaps: dict[int, int] | None = None,
) -> list[int]:
    """Keep equal runs five positions apart (at least four cells between them)."""
    symbol_min_gaps = symbol_min_gaps or {}
    source_chunks = [
        (symbol, length)
        for symbol, lengths in runs_by_symbol.items()
        for length in lengths
    ]

    def penalty(chunks: list[tuple[int, int]]) -> int:
        prefix = [0]
        for _, length in chunks:
            prefix.append(prefix[-1] + length)
        total_length = prefix[-1]
        positions = defaultdict(list)
        for index, (symbol, _) in enumerate(chunks):
            positions[symbol].append(index)
        score = 0
        for symbol, indexes in positions.items():
            required_gap = symbol_min_gaps.get(symbol, min_separate_gap)
            for offset, left in enumerate(indexes):
                right = indexes[(offset + 1) % len(indexes)]
                if right > left:
                    gap = prefix[right] - prefix[left + 1]
                else:
                    gap = total_length - (prefix[left + 1] - prefix[right])
                if gap < required_gap:
                    score += 10_000 if gap == 0 else (required_gap - gap) ** 2
        return score

    best = None
    for attempt in range(8):
        rng = random.Random(seed + attempt * 7919)
        # Place every symbol's groups at near-even angles around the cyclic
        # strip before local swaps. This avoids concentrating the most frequent
        # symbol near the boundary, which a plain random shuffle often does.
        keyed_chunks = []
        for symbol, lengths in runs_by_symbol.items():
            shuffled = list(lengths)
            rng.shuffle(shuffled)
            phase = rng.random()
            group_count = len(shuffled)
            for index, length in enumerate(shuffled):
                angle = ((index + phase) / group_count) % 1.0
                keyed_chunks.append((angle, rng.random(), symbol, length))
        keyed_chunks.sort()
        chunks = [(symbol, length) for _, _, symbol, length in keyed_chunks]
        score = penalty(chunks)
        for iteration in range(25_000):
            if score == 0:
                sequence = [symbol for symbol, length in chunks for _ in range(length)]
                validate_sequence(sequence, min_separate_gap, symbol_min_gaps)
                return sequence
            if best is None or score < best[0]:
                best = (score, list(chunks))
            left, right = rng.sample(range(len(chunks)), 2)
            chunks[left], chunks[right] = chunks[right], chunks[left]
            candidate = penalty(chunks)
            temperature = max(0.05, 2.5 * (1 - iteration / 25_000))
            if candidate <= score or rng.random() < math.exp((score - candidate) / temperature):
                score = candidate
            else:
                chunks[left], chunks[right] = chunks[right], chunks[left]
    if best is None:
        raise RuntimeError("No arrangement candidate")
    sequence = [symbol for symbol, length in best[1] for _ in range(length)]
    if any(run_length > 3 for _, run_length, _ in cyclic_run_gaps(sequence)):
        raise RuntimeError("Best arrangement still contains a run longer than 3")
    return sequence


def run_exposure(runs: list[int]) -> np.ndarray:
    """Return cell exposures by visible Stack 1-5 for isolated source runs."""
    counts = np.zeros(5, dtype=np.float64)
    for run_length in runs:
        for window_start in range(-4, run_length):
            overlap = max(0, min(run_length, window_start + 5) - max(0, window_start))
            if overlap:
                counts[overlap - 1] += overlap
    return counts


def search_symbol_runs(
    counts: list[int], table_weights: list[int], target: np.ndarray, seed: int,
) -> tuple[list[list[int]], tuple[float, float, float], np.ndarray]:
    best = None
    for pair_probability in np.arange(0.05, 0.96, 0.05):
        for triple_probability in np.arange(0.00, 0.51, 0.05):
            single_probability = 1.0 - pair_probability - triple_probability
            if single_probability < 0.01:
                continue
            probabilities = (single_probability, pair_probability, triple_probability)
            for variant in range(8):
                runs_by_table = []
                exposure = np.zeros(5, dtype=np.float64)
                for table_index, (count, weight) in enumerate(zip(counts, table_weights)):
                    rng = random.Random(seed + variant * 1_000_003 + table_index * 100_003)
                    runs = make_runs(count, probabilities, rng)
                    runs_by_table.append(runs)
                    exposure += weight * run_exposure(runs)
                achieved = exposure / exposure.sum()
                weights = np.asarray([1, 1, 1, 8, 8], dtype=np.float64)
                loss = float(np.sum(weights * (achieved - target) ** 2))
                candidate = (loss, probabilities, variant, runs_by_table, achieved)
                if best is None or candidate[:3] < best[:3]:
                    best = candidate
    if best is None:
        raise RuntimeError("No per-symbol run candidate")
    _, probabilities, _, runs_by_table, achieved = best
    return runs_by_table, probabilities, achieved


def stack_distribution(sequence: list[int]) -> np.ndarray:
    counts = Counter()
    length = len(sequence)
    for start in range(length):
        column = [sequence[(start + row) % length] for row in range(5)]
        index = 0
        while index < 5:
            end = index + 1
            while end < 5 and column[end] == column[index]:
                end += 1
            run_length = end - index
            counts[run_length] += run_length
            index = end
    return np.asarray([counts[length] / (5 * len(sequence)) for length in range(1, 6)])


def target_vector(metrics: dict, scene: str, reel: int) -> np.ndarray:
    row = metrics["competitor"][scene]["by_reel"][f"R{reel + 1}"]
    return np.asarray([row[f"stack_{length}"] for length in range(1, 6)], dtype=np.float64)


def search_reel(
    counts_by_table: list[Counter], table_weights: list[int], target: np.ndarray,
    symbol_targets: dict, code_by_id: dict[int, str], seed: int,
) -> tuple[list[list[int]], dict[str, list[float]], np.ndarray, float]:
    runs_by_table = [defaultdict(list) for _ in counts_by_table]
    parameters = {}
    for symbol_id in sorted(set().union(*[set(counts) for counts in counts_by_table])):
        code = code_by_id[symbol_id]
        counts = [table_counts[symbol_id] for table_counts in counts_by_table]
        target_row = symbol_targets.get(code)
        if code in SPECIAL_CODES or target_row is None:
            selected_runs = [[[1] * count][0] for count in counts]
            probabilities = (1.0, 0.0, 0.0)
        else:
            symbol_target = np.asarray(
                [target_row[f"stack_{length}"] for length in range(1, 6)], dtype=np.float64
            )
            selected_runs, probabilities, _ = search_symbol_runs(
                counts, table_weights, symbol_target, seed + symbol_id * 10_000
            )
        parameters[code] = [round(float(value), 4) for value in probabilities]
        for table_index, runs in enumerate(selected_runs):
            runs_by_table[table_index][symbol_id] = runs

    sequences = [
        arrange_runs(
            runs,
            seed + table_index * 100_003,
            symbol_min_gaps={
                symbol_id: 6
                for symbol_id, code in code_by_id.items()
                if code == "C1"
            },
        )
        for table_index, runs in enumerate(runs_by_table)
    ]
    aggregate = np.zeros(5, dtype=np.float64)
    for sequence, weight in zip(sequences, table_weights):
        aggregate += weight * stack_distribution(sequence)
    aggregate /= sum(table_weights)
    weights = np.asarray([1, 1, 1, 8, 8], dtype=np.float64)
    loss = float(np.sum(weights * (aggregate - target) ** 2))
    return sequences, parameters, aggregate, loss


def calibrate(config: dict, competitor_path: Path) -> tuple[dict, list[dict]]:
    result = copy.deepcopy(config)
    metrics = analyze(DEFAULT_CONFIG, competitor_path)
    by_name = dict(zip(result["strip_names"], result["strips"]))
    code_by_id = dict(zip(result["symbol_ids"], result["symbol_codes"]))
    diagnostics = []
    for scene_index, scene in enumerate(("BG", "FG")):
        tables = SCENE_TABLES[scene]
        for reel in range(6):
            counts_by_table = [Counter(int(row[reel]) for row in by_name[name]["symbols"]) for name, _ in tables]
            table_weights = [weight for _, weight in tables]
            target = target_vector(metrics, scene, reel)
            symbol_targets = metrics["competitor"][scene]["by_reel_symbol"][f"R{reel + 1}"]
            sequences, parameters, achieved, loss = search_reel(
                counts_by_table, table_weights, target, symbol_targets, code_by_id,
                seed=2710400 + scene_index * 1_000_000 + reel * 10_000,
            )
            for (table_name, _), sequence in zip(tables, sequences):
                strip = by_name[table_name]
                for row, symbol_id in enumerate(sequence):
                    strip["symbols"][row][reel] = symbol_id
            diagnostics.append({
                "scene": scene,
                "reel": reel + 1,
                "run_probabilities_by_symbol": parameters,
                "target": target.tolist(),
                "achieved": achieved.tolist(),
                "loss": loss,
            })
    return result, diagnostics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    config = model_sync.load_js_config(args.config.resolve())
    candidate, diagnostics = calibrate(config, args.input.resolve())
    for row in diagnostics:
        print(
            f"{row['scene']} R{row['reel']} "
            f"target={','.join(f'{100*v:.3f}' for v in row['target'])} "
            f"achieved={','.join(f'{100*v:.3f}' for v in row['achieved'])} "
            f"loss={row['loss']:.8f}"
        )
    if args.write:
        model_sync.write_js_config(args.config.resolve(), candidate)
        print(f"Updated {args.config.resolve()}")
    else:
        print("Dry run only; pass --write to update config.")


if __name__ == "__main__":
    main()
