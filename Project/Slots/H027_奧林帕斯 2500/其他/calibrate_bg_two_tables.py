"""Calibrate a two-table latent BG model while preserving symbol marginals.

BG_Symbol and BG_Symbol (2) are selected 50/50. Their per-reel initial
symbol counts and drop weights are complementary, so the combined marginal
distribution is exactly the pre-calibration BG distribution. A table is held
for the full spin, creating persistence between the initial winning symbol and
all subsequent drops without a separate correlated-drop algorithm.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import itertools
import json
import os
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Source"))
import model_sync


DEFAULT_CONFIG = ROOT / "config_92A.js"
DEFAULT_INPUT = ROOT / "其他" / "參考資料" / "game_responses-gates of olympus 1000.xlsx"
ANALYZER_PATH = ROOT / "其他" / "analyze_gates_competitor.py"
BG_NAMES = ("BG_Symbol", "BG_Symbol (2)")
FG_NAMES = ("FG_Symbol", "FG_Symbol (2)")
SPECIAL_CODES = {"C1", "C2", "C3"}
TARGET_BG = np.asarray(
    [62.5247524752, 18.2673267327, 11.0891089109, 4.9009900990,
     1.9306930693, 0.8910891089, 0.3465346535, 0.0495049505, 0.0],
    dtype=np.float64,
)


def largest_remainder(total: int, weights: list[int]) -> list[int]:
    source_total = sum(weights)
    if total <= 0 or source_total <= 0:
        return [0] * len(weights)
    raw = [total * value / source_total for value in weights]
    result = [int(value) for value in raw]
    remainder = total - sum(result)
    order = sorted(range(len(weights)), key=lambda i: (raw[i] - result[i], -i), reverse=True)
    for index in order[:remainder]:
        result[index] += 1
    return result


def split_vector(base: list[int], group_a: set[int], score_indices: list[int], strength: float) -> tuple[list[int], list[int]]:
    """Return complementary A/B vectors whose arithmetic mean is base."""
    a_indices = [index for index in score_indices if index in group_a]
    b_indices = [index for index in score_indices if index not in group_a]
    a_total = sum(base[index] for index in a_indices)
    b_total = sum(base[index] for index in b_indices)
    shift = min(int(round(strength * min(a_total, b_total))), a_total, b_total)
    additions = largest_remainder(shift, [base[index] for index in a_indices])
    removals = largest_remainder(shift, [base[index] for index in b_indices])

    first = list(base)
    for index, value in zip(a_indices, additions):
        first[index] += value
    for index, value in zip(b_indices, removals):
        first[index] -= value
    second = [2 * original - value for original, value in zip(base, first)]
    if min(first) < 0 or min(second) < 0 or sum(first) != sum(base) or sum(second) != sum(base):
        raise RuntimeError("Invalid complementary split")
    return first, second


def split_combined(
    combined: list[int], group_a: set[int], score_indices: list[int], strength: float
) -> tuple[list[int], list[int]]:
    """Split a combined two-table count vector into biased 300-stop tables."""
    if sum(combined) % 2:
        raise ValueError("Combined total must be even")
    first = largest_remainder(sum(combined) // 2, combined)
    second = [total - value for total, value in zip(combined, first)]
    a_indices = [index for index in score_indices if index in group_a]
    b_indices = [index for index in score_indices if index not in group_a]
    shift = min(
        int(round(strength * min(sum(second[index] for index in a_indices),
                                 sum(first[index] for index in b_indices)))),
        sum(second[index] for index in a_indices),
        sum(first[index] for index in b_indices),
    )
    additions = largest_remainder(shift, [second[index] for index in a_indices])
    removals = largest_remainder(shift, [first[index] for index in b_indices])
    for index, value in zip(a_indices, additions):
        first[index] += value
        second[index] -= value
    for index, value in zip(b_indices, removals):
        first[index] -= value
        second[index] += value
    if min(first) < 0 or min(second) < 0 or any(a + b != total for a, b, total in zip(first, second, combined)):
        raise RuntimeError("Invalid combined split")
    return first, second


def select_partition(initial_counts: np.ndarray, drop_weights: np.ndarray, score_indices: list[int]) -> set[int]:
    """Choose the score-symbol partition that is most balanced across reels."""
    best = None
    first = score_indices[0]
    rest = score_indices[1:]
    vectors = [initial_counts[:, reel] for reel in range(initial_counts.shape[1])]
    vectors += [drop_weights[:, reel] for reel in range(drop_weights.shape[1])]
    for mask in range(1 << len(rest)):
        group = {first, *(rest[index] for index in range(len(rest)) if mask & (1 << index))}
        if len(group) == len(score_indices):
            continue
        loss = 0.0
        for vector in vectors:
            score_total = sum(int(vector[index]) for index in score_indices)
            group_total = sum(int(vector[index]) for index in group)
            loss += ((group_total / score_total) - 0.5) ** 2
        candidate = (loss, tuple(sorted(group)))
        if best is None or candidate < best:
            best = candidate
    if best is None:
        raise RuntimeError("No valid score-symbol partition")
    return set(best[1])


def build_sequence(
    length: int, target_counts: list[int], score_ids: set[int], special_ids: set[int],
    run_strength: float, seed: int
) -> list[int]:
    """Build a strip from exact counts; spread special symbols across the reel."""
    rng = random.Random(seed)
    result = [0] * length
    remaining = Counter({symbol_id: target_counts[symbol_id] for symbol_id in score_ids})
    specials = [symbol_id for symbol_id in sorted(special_ids) for _ in range(target_counts[symbol_id])]
    rng.shuffle(specials)
    special_positions = []
    used = set()
    for index in range(len(specials)):
        candidate = int(round((index + 0.5) * length / len(specials))) % length
        while candidate in used:
            candidate = (candidate + 1) % length
        used.add(candidate)
        special_positions.append(candidate)
    for position, symbol_id in zip(special_positions, specials):
        result[position] = symbol_id

    previous = None
    for position in range(length):
        if position in used:
            previous = None
            continue
        if previous is not None and remaining[previous] > 0 and rng.random() < run_strength:
            selected = previous
        else:
            symbols = [symbol for symbol in sorted(score_ids) if remaining[symbol] > 0]
            selected = rng.choices(symbols, weights=[remaining[symbol] for symbol in symbols], k=1)[0]
        result[position] = selected
        remaining[selected] -= 1
        previous = selected
    if any(remaining.values()):
        raise RuntimeError(f"Unconsumed score symbols: {remaining}")
    return result


def load_competitor_initial_counts(input_path: Path, symbol_codes: list[str]) -> np.ndarray:
    spec = importlib.util.spec_from_file_location("h027_two_table_competitor", ANALYZER_PATH)
    analyzer = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = analyzer
    spec.loader.exec_module(analyzer)
    analysis = analyzer.analyze(input_path)
    spins = [session.bg for session in analysis["_sessions"]]
    probabilities = analyzer.reel_symbol_probabilities(spins, "initial")
    per_reel = [analyzer.largest_remainder_counts(values, 600) for values in probabilities]
    matrix = np.asarray(
        [[int(per_reel[reel].get(code, 0)) for reel in range(6)] for code in symbol_codes],
        dtype=np.int64,
    )
    if matrix.sum(axis=0).tolist() != [600] * 6:
        raise RuntimeError("Competitor initial counts did not quantize to 600 per reel")
    return matrix


def ensure_table_parameter(block: dict, source_name: str, new_name: str) -> None:
    names = list(block["table_names"])
    if new_name not in names:
        insert_at = names.index(source_name) + 1
        names.insert(insert_at, new_name)
    block["table_names"] = names
    block["weights"][new_name] = list(block["weights"][source_name])
    block["weights_cum"][new_name] = list(block["weights_cum"][source_name])


def build_candidate(
    config: dict, competitor_initial: np.ndarray, initial_strength: float,
    drop_strength: float, run_strength: float, seed: int
) -> tuple[dict, set[int]]:
    result = copy.deepcopy(config)
    names = list(result["strip_names"])
    strips = copy.deepcopy(result["strips"])
    by_name = dict(zip(names, strips))
    base = copy.deepcopy(by_name[BG_NAMES[0]])
    fg = [copy.deepcopy(by_name[name]) for name in FG_NAMES]

    symbol_ids = list(result["symbol_ids"])
    code_by_id = dict(zip(result["symbol_ids"], result["symbol_codes"]))
    id_to_index = {symbol_id: index for index, symbol_id in enumerate(symbol_ids)}
    score_ids = [symbol_id for symbol_id in symbol_ids if code_by_id[symbol_id] not in SPECIAL_CODES]
    score_indices = [id_to_index[symbol_id] for symbol_id in score_ids]

    matrix = np.asarray(base["symbols"], dtype=np.int64)
    initial_counts = np.asarray(competitor_initial, dtype=np.int64)
    drop = np.asarray(base["drop_weights"], dtype=np.int64)
    group_indices = select_partition(initial_counts, drop, score_indices)

    first_matrix = matrix.copy()
    second_matrix = matrix.copy()
    first_drop = drop.copy()
    second_drop = drop.copy()
    score_set = set(score_ids)
    special_set = set(symbol_ids) - score_set
    max_id = max(symbol_ids)

    for reel in range(matrix.shape[1]):
        count_a, count_b = split_combined(
            initial_counts[:, reel].tolist(), group_indices, score_indices, initial_strength
        )
        count_by_id_a = [0] * (max_id + 1)
        count_by_id_b = [0] * (max_id + 1)
        for index, symbol_id in enumerate(symbol_ids):
            count_by_id_a[symbol_id] = count_a[index]
            count_by_id_b[symbol_id] = count_b[index]
        first_matrix[:, reel] = build_sequence(
            matrix.shape[0], count_by_id_a, score_set, special_set,
            run_strength, seed + reel * 1009
        )
        second_matrix[:, reel] = build_sequence(
            matrix.shape[0], count_by_id_b, score_set, special_set,
            run_strength, seed + 100_000 + reel * 1013
        )
        drop_a, drop_b = split_vector(drop[:, reel].tolist(), group_indices, score_indices, drop_strength)
        first_drop[:, reel] = drop_a
        second_drop[:, reel] = drop_b

    first = copy.deepcopy(base)
    second = copy.deepcopy(base)
    first["symbols"] = first_matrix.tolist()
    second["symbols"] = second_matrix.tolist()
    first["drop_weights"] = first_drop.tolist()
    second["drop_weights"] = second_drop.tolist()

    result["strip_names"] = [*BG_NAMES, *FG_NAMES]
    result["strips"] = [first, second, *fg]
    for profile_name in ("normal", "featurebuy"):
        profile = result["parameter"][profile_name]
        ensure_table_parameter(profile["c2"], BG_NAMES[0], BG_NAMES[1])
        ensure_table_parameter(profile["c3"], BG_NAMES[0], BG_NAMES[1])
        use_super = profile["use_super_multiplier"]
        if BG_NAMES[1] not in use_super["table_names"]:
            insert_at = use_super["table_names"].index(BG_NAMES[0]) + 1
            use_super["table_names"].insert(insert_at, BG_NAMES[1])
        use_super["weights_by_initial_ball_count"][BG_NAMES[1]] = list(
            use_super["weights_by_initial_ball_count"][BG_NAMES[0]]
        )
        if profile_name == "normal":
            profile["base_reel_names"] = list(BG_NAMES)
            profile["base_reel_weights"] = [1, 1]
            profile["base_reel_weights_cum"] = [1, 2]
        else:
            profile["base_reel_names"] = [BG_NAMES[0]]
            profile["base_reel_weights"] = [1]
            profile["base_reel_weights_cum"] = [1]

    # Exact marginal invariants for a 50/50 table mixture.
    for reel in range(matrix.shape[1]):
        for symbol_id in symbol_ids:
            combined = int(np.sum(first_matrix[:, reel] == symbol_id) + np.sum(second_matrix[:, reel] == symbol_id))
            expected = int(initial_counts[id_to_index[symbol_id], reel])
            if combined != expected:
                raise RuntimeError(f"Initial marginal changed: R{reel + 1} symbol {symbol_id}")
    if not np.array_equal(first_drop + second_drop, drop * 2):
        raise RuntimeError("Drop-weight marginals changed")
    return result, {symbol_ids[index] for index in group_indices}


def evaluate(config: dict, rounds: int, temp_path: Path) -> dict:
    model_sync.write_js_config(temp_path, config)
    code = (
        "import json, Simulator as s; "
        "r,d,c=s.run_simulation(); "
        "print('__RESULT__'+json.dumps({'cascade':r[s.R_CASCADE_BG,:20].tolist(),"
        "'hit':float(r[s.R_ALL,s.RA_HITS_BG]/s.TOTAL_ROUNDS)}))"
    )
    env = os.environ.copy()
    env.update({
        "H027_CONFIG_FILE": str(temp_path),
        "H027_RUN_ALL_COMBINATIONS": "false",
        "H027_TOTAL_ROUNDS": str(rounds),
        "H027_OUTPUT_REPORT": "false",
        "H027_SHOW_CONSOLE_SUMMARY": "false",
        "H027_SHOW_CONSOLE_DETAIL": "false",
        "PYTHONUTF8": "1",
    })
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, env=env,
        text=True, encoding="utf-8", errors="replace", capture_output=True, check=True,
    )
    line = next((line for line in completed.stdout.splitlines() if line.startswith("__RESULT__")), None)
    if line is None:
        raise RuntimeError(f"Simulator result missing:\n{completed.stdout}\n{completed.stderr}")
    return json.loads(line[len("__RESULT__"):])


def conditional_distribution(cascade: list[float]) -> np.ndarray:
    counts = np.asarray(cascade, dtype=np.float64)
    positive = counts[1:].sum()
    buckets = np.asarray([*counts[1:9], counts[9:].sum()], dtype=np.float64)
    return buckets / positive * 100 if positive else np.zeros(9)


def objective(distribution: np.ndarray) -> float:
    # Combo 1-6 carry nearly all competitor mass; retain 7-9+ as light tail guards.
    weights = np.asarray([1, 1, 1, 1, 1, 1, 0.25, 0.25, 0.25], dtype=np.float64)
    return float(np.sum(weights * (distribution - TARGET_BG) ** 2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--rounds", type=int, default=500_000)
    parser.add_argument("--verify-rounds", type=int, default=5_000_000)
    parser.add_argument("--run-strength", type=float, default=0.14)
    parser.add_argument("--initial-strength", type=float)
    parser.add_argument("--drop-strength", type=float)
    parser.add_argument("--seed", type=int, default=27102)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    original = model_sync.load_js_config(args.config.resolve())
    competitor_initial = load_competitor_initial_counts(
        args.input.resolve(), list(original["symbol_codes"])
    )
    temp_path = ROOT / "config_bg_two_table_calibration.tmp.js"
    strengths = [
        (0.12, 0.72), (0.12, 0.76), (0.12, 0.80),
        (0.14, 0.70), (0.14, 0.74), (0.14, 0.78),
        (0.15, 0.70), (0.15, 0.72), (0.15, 0.74), (0.15, 0.76),
        (0.16, 0.68), (0.16, 0.72), (0.16, 0.76),
        (0.18, 0.66), (0.18, 0.70),
    ]
    if (args.initial_strength is None) != (args.drop_strength is None):
        parser.error("--initial-strength and --drop-strength must be supplied together")
    if args.initial_strength is not None:
        strengths = [(args.initial_strength, args.drop_strength)]
    best = None
    try:
        for initial_strength, drop_strength in strengths:
            candidate, group_ids = build_candidate(
                original, competitor_initial, initial_strength, drop_strength,
                args.run_strength, args.seed
            )
            metrics = evaluate(candidate, args.rounds, temp_path)
            distribution = conditional_distribution(metrics["cascade"])
            result = (
                objective(distribution), initial_strength, drop_strength,
                candidate, distribution, metrics["hit"], group_ids,
            )
            if best is None or result[0] < best[0]:
                best = result
            print(
                f"initial={initial_strength:.2f} drop={drop_strength:.2f} "
                f"loss={result[0]:.4f} hit={result[5]:.4%} "
                f"combo={','.join(f'{value:.3f}' for value in distribution)}",
                flush=True,
            )
        assert best is not None
        _, initial_strength, drop_strength, candidate, _, _, group_ids = best
        if args.write:
            from calibrate_stack_arrangement import calibrate as calibrate_stacks
            candidate, _ = calibrate_stacks(candidate, args.input.resolve())
        verified = evaluate(candidate, args.verify_rounds, temp_path)
        verified_distribution = conditional_distribution(verified["cascade"])
        codes = dict(zip(original["symbol_ids"], original["symbol_codes"]))
        print(
            f"BEST initial={initial_strength:.2f} drop={drop_strength:.2f} "
            f"loss={objective(verified_distribution):.4f} "
            f"hit={verified['hit']:.4%} groupA={[codes[value] for value in sorted(group_ids)]}"
        )
        print("TARGET", ",".join(f"{value:.4f}" for value in TARGET_BG))
        print("VERIFY", ",".join(f"{value:.4f}" for value in verified_distribution))
        if args.write:
            model_sync.write_js_config(args.config.resolve(), candidate)
            print(f"Updated {args.config.resolve()}")
        else:
            print("Dry run only; pass --write to update config.")
    finally:
        if temp_path.exists():
            temp_path.unlink()


if __name__ == "__main__":
    main()
