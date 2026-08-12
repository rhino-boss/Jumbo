"""Calibrate two persistent FG tables while preserving competitor marginals.

Each 15-spin FG schedules 8 spins from FG_Symbol and 7 from FG_Symbol (2).
The two tables use complementary symbol counts and drop weights whose 8:7
weighted average equals the competitor FG distribution. Retriggers schedule
3:2 because the game adds five spins.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Source"))
import model_sync
from calibrate_bg_two_tables import (
    SPECIAL_CODES,
    build_sequence,
    conditional_distribution,
    ensure_table_parameter,
    select_partition,
)


DEFAULT_CONFIG = ROOT / "config_92A.js"
DEFAULT_INPUT = ROOT / "其他" / "參考資料" / "game_responses-gates of olympus 1000.xlsx"
ANALYZER_PATH = ROOT / "其他" / "analyze_gates_competitor.py"
BG_NAMES = ("BG_Symbol", "BG_Symbol (2)")
FG_NAMES = ("FG_Symbol", "FG_Symbol (2)")
INITIAL_COUNTS = (8, 7)
RETRIGGER_COUNTS = (3, 2)
TARGET_FG = np.asarray(
    [47.1014492754, 29.7101449275, 10.8695652174, 7.9710144928,
     2.1739130435, 2.1739130435, 0.0, 0.0, 0.0],
    dtype=np.float64,
)


def capped_allocate(total: int, weights: list[int], capacities: list[int]) -> list[int]:
    """Allocate integer units proportionally without exceeding capacities."""
    result = [0] * len(weights)
    remaining = total
    while remaining:
        active = [i for i, cap in enumerate(capacities) if result[i] < cap]
        if not active:
            raise RuntimeError("Insufficient split capacity")
        weight_total = sum(max(weights[i], 1) for i in active)
        raw = {i: remaining * max(weights[i], 1) / weight_total for i in active}
        order = sorted(active, key=lambda i: (raw[i] - int(raw[i]), weights[i], -i), reverse=True)
        progress = 0
        for index in active:
            value = min(int(raw[index]), capacities[index] - result[index])
            result[index] += value
            progress += value
        remaining -= progress
        for index in order:
            if not remaining:
                break
            if result[index] < capacities[index]:
                result[index] += 1
                remaining -= 1
        if progress == 0 and remaining and not any(result[i] < capacities[i] for i in active):
            raise RuntimeError("Unable to complete capped allocation")
    return result


def weighted_split(
    base: list[int], group_a: set[int], score_indices: list[int], strength: float,
    weight_a: int = INITIAL_COUNTS[0], weight_b: int = INITIAL_COUNTS[1],
) -> tuple[list[int], list[int]]:
    """Return A/B vectors whose weight_a:weight_b average is exactly base."""
    a_indices = [index for index in score_indices if index in group_a]
    b_indices = [index for index in score_indices if index not in group_a]
    positive_caps = [base[index] // weight_a for index in a_indices]
    negative_caps = [base[index] // weight_b for index in b_indices]
    units = int(round(strength * min(sum(positive_caps), sum(negative_caps))))
    positive = capped_allocate(units, [base[index] for index in a_indices], positive_caps)
    negative = capped_allocate(units, [base[index] for index in b_indices], negative_caps)
    delta = [0] * len(base)
    for index, value in zip(a_indices, positive):
        delta[index] = value
    for index, value in zip(b_indices, negative):
        delta[index] = -value
    first = [value + weight_b * delta[index] for index, value in enumerate(base)]
    second = [value - weight_a * delta[index] for index, value in enumerate(base)]
    if min(first) < 0 or min(second) < 0 or sum(first) != sum(base) or sum(second) != sum(base):
        raise RuntimeError("Invalid weighted complementary split")
    if any(weight_a * a + weight_b * b != (weight_a + weight_b) * value
           for a, b, value in zip(first, second, base)):
        raise RuntimeError("Weighted marginal changed")
    return first, second


def load_competitor_initial_counts(input_path: Path, symbol_codes: list[str]) -> np.ndarray:
    spec = importlib.util.spec_from_file_location("h027_fg_two_table_competitor", ANALYZER_PATH)
    analyzer = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = analyzer
    spec.loader.exec_module(analyzer)
    analysis = analyzer.analyze(input_path)
    spins = [spin for session in analysis["_sessions"] for spin in session.fg_spins]
    probabilities = analyzer.reel_symbol_probabilities(spins, "initial")
    per_reel = [analyzer.largest_remainder_counts(values, 300) for values in probabilities]
    matrix = np.asarray(
        [[int(per_reel[reel].get(code, 0)) for reel in range(6)] for code in symbol_codes],
        dtype=np.int64,
    )
    if matrix.sum(axis=0).tolist() != [300] * 6:
        raise RuntimeError("Competitor FG initial counts did not quantize to 300 per reel")
    return matrix


def build_candidate(
    config: dict, competitor_initial: np.ndarray, initial_strength: float,
    drop_strength: float, run_strength: float, seed: int,
) -> tuple[dict, set[int]]:
    result = copy.deepcopy(config)
    by_name = dict(zip(result["strip_names"], result["strips"]))
    bg = [copy.deepcopy(by_name[name]) for name in BG_NAMES]
    base = copy.deepcopy(by_name[FG_NAMES[0]])
    second_base = copy.deepcopy(by_name[FG_NAMES[1]])

    symbol_ids = list(result["symbol_ids"])
    code_by_id = dict(zip(result["symbol_ids"], result["symbol_codes"]))
    id_to_index = {symbol_id: index for index, symbol_id in enumerate(symbol_ids)}
    score_ids = [symbol_id for symbol_id in symbol_ids if code_by_id[symbol_id] not in SPECIAL_CODES]
    score_indices = [id_to_index[symbol_id] for symbol_id in score_ids]
    first_existing_drop = np.asarray(base["drop_weights"], dtype=np.int64)
    second_existing_drop = np.asarray(second_base["drop_weights"], dtype=np.int64)
    drop_numerator = INITIAL_COUNTS[0] * first_existing_drop + INITIAL_COUNTS[1] * second_existing_drop
    if np.any(drop_numerator % sum(INITIAL_COUNTS)):
        raise RuntimeError("Existing FG drop-weight tables do not have an integral 8:7 aggregate")
    drop = drop_numerator // sum(INITIAL_COUNTS)
    group_indices = select_partition(competitor_initial, drop, score_indices)

    first_matrix = np.asarray(base["symbols"], dtype=np.int64).copy()
    second_matrix = first_matrix.copy()
    first_drop = drop.copy()
    second_drop = drop.copy()
    score_set = set(score_ids)
    special_set = set(symbol_ids) - score_set
    max_id = max(symbol_ids)

    for reel in range(6):
        count_a, count_b = weighted_split(
            competitor_initial[:, reel].tolist(), group_indices, score_indices, initial_strength
        )
        by_id_a = [0] * (max_id + 1)
        by_id_b = [0] * (max_id + 1)
        for index, symbol_id in enumerate(symbol_ids):
            by_id_a[symbol_id] = count_a[index]
            by_id_b[symbol_id] = count_b[index]
        first_matrix[:, reel] = build_sequence(
            300, by_id_a, score_set, special_set, run_strength, seed + reel * 1019
        )
        second_matrix[:, reel] = build_sequence(
            300, by_id_b, score_set, special_set, run_strength, seed + 100_000 + reel * 1021
        )
        drop_a, drop_b = weighted_split(
            drop[:, reel].tolist(), group_indices, score_indices, drop_strength
        )
        first_drop[:, reel] = drop_a
        second_drop[:, reel] = drop_b

    first = copy.deepcopy(base)
    second = copy.deepcopy(base)
    first["symbols"] = first_matrix.tolist()
    second["symbols"] = second_matrix.tolist()
    first["drop_weights"] = first_drop.tolist()
    second["drop_weights"] = second_drop.tolist()
    result["strip_names"] = [*BG_NAMES, *FG_NAMES]
    result["strips"] = [*bg, first, second]

    for profile_name in ("normal", "featurebuy"):
        profile = result["parameter"][profile_name]
        ensure_table_parameter(profile["c2"], FG_NAMES[0], FG_NAMES[1])
        ensure_table_parameter(profile["c3"], FG_NAMES[0], FG_NAMES[1])
        use_super = profile["use_super_multiplier"]
        if FG_NAMES[1] not in use_super["table_names"]:
            insert_at = use_super["table_names"].index(FG_NAMES[0]) + 1
            use_super["table_names"].insert(insert_at, FG_NAMES[1])
        use_super["weights_by_initial_ball_count"][FG_NAMES[1]] = list(
            use_super["weights_by_initial_ball_count"][FG_NAMES[0]]
        )
        profile["free_table"] = {
            "names": list(FG_NAMES),
            "initial": list(INITIAL_COUNTS),
            "retrigger": list(RETRIGGER_COUNTS),
        }

    for reel in range(6):
        for symbol_id in symbol_ids:
            index = id_to_index[symbol_id]
            count_a = int(np.sum(first_matrix[:, reel] == symbol_id))
            count_b = int(np.sum(second_matrix[:, reel] == symbol_id))
            expected = int(competitor_initial[index, reel])
            if INITIAL_COUNTS[0] * count_a + INITIAL_COUNTS[1] * count_b != sum(INITIAL_COUNTS) * expected:
                raise RuntimeError(f"FG initial marginal changed: R{reel + 1} symbol {symbol_id}")
    if not np.array_equal(INITIAL_COUNTS[0] * first_drop + INITIAL_COUNTS[1] * second_drop,
                          sum(INITIAL_COUNTS) * drop):
        raise RuntimeError("FG drop-weight marginal changed")
    return result, {symbol_ids[index] for index in group_indices}


def evaluate(config: dict, rounds: int, temp_path: Path) -> dict:
    model_sync.write_js_config(temp_path, config)
    code = (
        "import json, Simulator as s; "
        "r,d,c=s.run_simulation(); "
        "print('__RESULT__'+json.dumps({'cascade':r[s.R_CASCADE_FG,:20].tolist(),"
        "'hit':float(r[s.R_ALL,s.RA_HITS_FG]/r[s.R_ALL,s.RA_FG_SPINS]),"
        "'spins':int(r[s.R_ALL,s.RA_FG_SPINS])}))"
    )
    env = os.environ.copy()
    env.update({
        "H027_CONFIG_FILE": str(temp_path),
        "H027_RUN_ALL_COMBINATIONS": "false",
        "H027_TOTAL_ROUNDS": str(rounds),
        "H027_BET_MODE": "2",
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


def objective(distribution: np.ndarray) -> float:
    weights = np.asarray([2, 2, 1, 1, 0.5, 0.5, 0.05, 0.05, 0.05], dtype=np.float64)
    return float(np.sum(weights * (distribution - TARGET_FG) ** 2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--rounds", type=int, default=25_000)
    parser.add_argument("--verify-rounds", type=int, default=100_000)
    parser.add_argument("--run-strength", type=float, default=0.14)
    parser.add_argument("--initial-strength", type=float)
    parser.add_argument("--drop-strength", type=float)
    parser.add_argument("--refine", action="store_true")
    parser.add_argument("--seed", type=int, default=27103)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    original = model_sync.load_js_config(args.config.resolve())
    competitor_initial = load_competitor_initial_counts(args.input.resolve(), list(original["symbol_codes"]))
    temp_path = ROOT / "config_fg_two_table_calibration.tmp.js"
    strengths = [
        (0.30, 0.60), (0.30, 0.75), (0.30, 0.90),
        (0.50, 0.60), (0.50, 0.75), (0.50, 0.90),
        (0.70, 0.60), (0.70, 0.75), (0.70, 0.90),
        (0.90, 0.60), (0.90, 0.75), (0.90, 0.90),
    ]
    if args.refine:
        strengths = [
            (0.48, 0.68), (0.48, 0.72), (0.48, 0.76),
            (0.52, 0.68), (0.52, 0.72), (0.52, 0.76),
            (0.56, 0.68), (0.56, 0.72), (0.56, 0.76),
        ]
    if (args.initial_strength is None) != (args.drop_strength is None):
        parser.error("--initial-strength and --drop-strength must be supplied together")
    if args.initial_strength is not None:
        strengths = [(args.initial_strength, args.drop_strength)]
    best = None
    try:
        for initial_strength, drop_strength in strengths:
            candidate, group_ids = build_candidate(
                original, competitor_initial, initial_strength, drop_strength, args.run_strength, args.seed
            )
            metrics = evaluate(candidate, args.rounds, temp_path)
            distribution = conditional_distribution(metrics["cascade"])
            result = (objective(distribution), initial_strength, drop_strength, candidate,
                      distribution, metrics["hit"], metrics["spins"], group_ids)
            if best is None or result[0] < best[0]:
                best = result
            print(
                f"initial={initial_strength:.2f} drop={drop_strength:.2f} loss={result[0]:.4f} "
                f"hit={result[5]:.4%} fg_spins={result[6]} "
                f"combo={','.join(f'{value:.3f}' for value in distribution)}",
                flush=True,
            )
        assert best is not None
        _, initial_strength, drop_strength, candidate, _, _, _, group_ids = best
        if args.write:
            from calibrate_stack_arrangement import calibrate as calibrate_stacks
            candidate, _ = calibrate_stacks(candidate, args.input.resolve())
        verified = evaluate(candidate, args.verify_rounds, temp_path)
        distribution = conditional_distribution(verified["cascade"])
        codes = dict(zip(original["symbol_ids"], original["symbol_codes"]))
        print(
            f"BEST initial={initial_strength:.2f} drop={drop_strength:.2f} "
            f"loss={objective(distribution):.4f} hit={verified['hit']:.4%} "
            f"fg_spins={verified['spins']} groupA={[codes[value] for value in sorted(group_ids)]}"
        )
        print("TARGET", ",".join(f"{value:.4f}" for value in TARGET_FG))
        print("VERIFY", ",".join(f"{value:.4f}" for value in distribution))
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
