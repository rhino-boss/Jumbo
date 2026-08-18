from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
import os
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
DEFAULT_BASE = PROJECT / "config.js"
DEFAULT_RTP = PROJECT / "config_94A.js"
QJ_SYMBOLS = frozenset({9, 10, 17, 18})
WILD_PROFILES = {
    "current": [0, 700, 500, 200],
    "moderate_2": [0, 1000, 300, 100],
    "strong_2": [0, 1300, 90, 10],
    "only_2": [0, 1, 0, 0],
}


def load_simulator(base_config: Path, rtp_config: Path):
    os.environ["H016_BASE_DIR"] = str(PROJECT)
    os.environ["H016_RUN_ALL_COMBINATIONS"] = "false"
    os.environ["H016_CONFIG_FILE"] = base_config.name
    os.environ["H016_CONFIG_RTP_FILE"] = rtp_config.name
    os.environ["H016_CARD_SYSTEM_ENABLED"] = "true"
    os.environ["H016_CARD_SYSTEM_IS_NEWBIE"] = "false"
    os.environ["H016_OUTPUT_REPORT"] = "false"
    os.environ["H016_SHOW_CONSOLE_SUMMARY"] = "false"
    os.environ["H016_SHOW_CONSOLE_DETAIL"] = "false"
    spec = importlib.util.spec_from_file_location("h016_sf_math_tuner", PROJECT / "Simulator.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load Simulator.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def normalize(raw: list[float], total: int) -> list[int]:
    raw_total = sum(raw)
    if raw_total <= 0:
        raise ValueError("Cannot normalize an empty weight vector")
    exact = [value * total / raw_total for value in raw]
    result = [int(math.floor(value)) for value in exact]
    remainder = total - sum(result)
    order = sorted(range(len(raw)), key=lambda index: exact[index] - result[index], reverse=True)
    for index in order[:remainder]:
        result[index] += 1
    return result


def bounded_stop_weights(raw: list[float], total: int) -> list[int]:
    positive = [value for value in raw if value > 0]
    if not positive:
        raise ValueError("Every reel needs at least one positive stop weight")
    ceiling = min(positive) * 9.8
    limited = [min(value, ceiling) if value > 0 else 0.0 for value in raw]
    result = normalize(limited, total)
    enabled = [value for value in result if value > 0]
    if max(enabled) / min(enabled) > 10:
        raise ValueError("Generated stop weights exceed the 10x limit")
    return result


def tune_table(
    source: dict[str, Any],
    head_target: float,
    tail_target: float,
    duplicate_penalty: float,
    wild_profile: str,
) -> dict[str, Any]:
    table = copy.deepcopy(source)
    for reel_index, (symbols, weights) in enumerate(zip(table["reels"], table["weights"])):
        target = head_target if reel_index < 3 else tail_target
        q_counts: list[int] = []
        j_counts: list[int] = []
        for stop in range(len(symbols)):
            visible = [symbols[(stop + offset) % len(symbols)] for offset in range(4)]
            q_counts.append(sum(symbol in (9, 17) for symbol in visible))
            j_counts.append(sum(symbol in (10, 18) for symbol in visible))
        raw = [
            float(weight)
            * duplicate_penalty ** (max(0, q_count - 1) + max(0, j_count - 1))
            for weight, q_count, j_count in zip(weights, q_counts, j_counts)
        ]
        for _ in range(16):
            total = sum(raw) * 4
            q_rate = sum(value * count for value, count in zip(raw, q_counts)) / total
            j_rate = sum(value * count for value, count in zip(raw, j_counts)) / total
            q_scale = target / max(q_rate, 1e-12)
            j_scale = target / max(j_rate, 1e-12)
            raw = [
                value * q_scale ** (q_count / 4) * j_scale ** (j_count / 4)
                for value, q_count, j_count in zip(raw, q_counts, j_counts)
            ]
        table["weights"][reel_index] = bounded_stop_weights(raw, sum(weights))

    for reel_index, (values, weights) in enumerate(zip(table["drop_values"], table["drop_weights"])):
        target = head_target if reel_index < 3 else tail_target
        total = sum(weights)
        q_indexes = [index for index, value in enumerate(values) if value in (9, 17)]
        j_indexes = [index for index, value in enumerate(values) if value in (10, 18)]
        other_indexes = [index for index in range(len(values)) if index not in q_indexes + j_indexes]
        result = [0] * len(values)
        for indexes in (q_indexes, j_indexes):
            group = [float(weights[index]) for index in indexes]
            allocated = normalize(group, round(total * target))
            for index, value in zip(indexes, allocated):
                result[index] = value
        remaining = total - sum(result)
        allocated = normalize([float(weights[index]) for index in other_indexes], remaining)
        for index, value in zip(other_indexes, allocated):
            result[index] = value
        table["drop_weights"][reel_index] = result
    table["random_wild"]["weights"] = list(WILD_PROFILES[wild_profile])
    return table


def candidate_base(
    source: dict[str, Any],
    head_target: float,
    tail_target: float,
    duplicate_penalty: float,
    wild_profile: str,
) -> dict[str, Any]:
    result = copy.deepcopy(source)
    tuned = tune_table(
        result["tables"]["sf_1"], head_target, tail_target,
        duplicate_penalty, wild_profile,
    )
    result["tables"]["sf_1"] = tuned
    result["tables"]["super"] = copy.deepcopy(tuned)
    result["excel_version"] = "4"
    return result


def evaluate(simulator, base: dict[str, Any], rounds: int, threads: int, seed: int) -> dict[str, float | int]:
    active = simulator.compose_runtime_config(base, simulator.CFG_RTP)
    packed = simulator.fast_simulator.prepare_config(active)
    simulator.fast_simulator.warm(
        packed, 3, 1, seed=seed, card_enabled=False, card_newbie=False,
    )
    packed_result = simulator.fast_simulator.run_prepared(
        packed, rounds, 3, 1, threads, seed=seed,
        card_enabled=False, card_newbie=False,
    )
    stats = simulator.fast_simulator.to_stats(packed_result)
    cards = active["card_system"]["profiles"]["weight_2"]["super_feature"]
    total_weight = sum(int(card["weight"]) for card in cards)
    thresholds = [float(value) for value in simulator.MULTIPLIER_THRESHOLDS]
    expected_spins = 0.0
    expected_hits = 0.0
    expected_pay = 0.0
    expected_retry = 0.0
    limit_probability = 0.0
    missing_weight = 0
    for card in cards:
        weight = int(card["weight"])
        if weight <= 0:
            continue
        probability = weight / total_weight
        bucket = thresholds.index(float(card["max"]))
        count = int(stats["multiplier_fg_count"][bucket])
        if count <= 0:
            missing_weight += weight
            continue
        natural_probability = count / rounds
        expected_spins += probability * int(stats["interval_fg_spins"][bucket]) / count
        expected_hits += probability * int(stats["interval_fg_hits"][bucket]) / count
        expected_pay += probability * float(stats["multiplier_fg_pay"][bucket]) / count
        expected_retry += probability * (1.0 / natural_probability - 1.0)
        limit_probability += probability * (1.0 - natural_probability) ** 10_000
    if missing_weight:
        raise ValueError(
            f"Card-weight mass {missing_weight:,} has no natural SF sample; increase rounds"
        )
    natural_spins = max(1, int(stats["fg_spins"]))
    return {
        "hit_rate": expected_hits / expected_spins,
        "rtp": expected_pay / 25_000.0,
        "avg_fg_spins": expected_spins,
        "avg_retry": expected_retry,
        "retry_limit_probability": limit_probability,
        "natural_hit_rate": int(stats["fg_hit_spins"]) / natural_spins,
        "natural_rtp": float(stats["pay_fg"]) / max(1.0, float(stats["coin_in"])),
    }


def score(result: dict[str, float | int], target_hit_rate: float, baseline_retry: float) -> float:
    hit_error = abs(float(result["hit_rate"]) - target_hit_rate)
    rtp_error = abs(float(result["rtp"]) - 0.925)
    retry_ratio = float(result["avg_retry"]) / max(1e-12, baseline_retry)
    retry_penalty = max(0.0, retry_ratio - 1.5)
    limit_penalty = float(result["retry_limit_probability"])
    return hit_error * 1_000 + rtp_error * 30 + retry_penalty * 5 + limit_penalty * 10_000


def write_config(path: Path, config: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    path.write_text(
        "// SF math candidate generated by 其他/工具/tune_sf_math.py.\n"
        f"window.H016_CONFIG={payload};\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Tune H016 SF per-spin hit rate without changing reels or card weights")
    parser.add_argument("--base-config", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--rtp-config", type=Path, default=DEFAULT_RTP)
    parser.add_argument("--target-hit-rate", type=float, default=0.35)
    parser.add_argument("--coarse-rounds", type=int, default=20_000)
    parser.add_argument("--final-rounds", type=int, default=200_000)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--seed", type=int, default=46046)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    base_path = args.base_config.resolve()
    rtp_path = args.rtp_config.resolve()
    simulator = load_simulator(base_path, rtp_path)
    baseline = evaluate(simulator, simulator.CFG_NATURAL, args.final_rounds, args.threads, args.seed)
    baseline_retry = float(baseline["avg_retry"])

    coarse: list[dict[str, Any]] = []
    for head_target in (0.24, 0.26):
        for tail_target in (0.01, 0.02):
            for duplicate_penalty in (0.4, 0.6):
                for wild_profile in WILD_PROFILES:
                    try:
                        base = candidate_base(
                            simulator.CFG_NATURAL, head_target, tail_target,
                            duplicate_penalty, wild_profile,
                        )
                        result = evaluate(simulator, base, args.coarse_rounds, args.threads, args.seed)
                    except ValueError:
                        continue
                    row = {
                        "head_target": head_target,
                        "tail_target": tail_target,
                        "duplicate_penalty": duplicate_penalty,
                        "wild_profile": wild_profile,
                        **result,
                    }
                    row["score"] = score(row, args.target_hit_rate, baseline_retry)
                    coarse.append(row)

    finalists = sorted(coarse, key=lambda row: float(row["score"]))[:4]
    final: list[dict[str, Any]] = []
    for row in finalists:
        base = candidate_base(
            simulator.CFG_NATURAL,
            float(row["head_target"]),
            float(row["tail_target"]),
            float(row["duplicate_penalty"]),
            str(row["wild_profile"]),
        )
        result = evaluate(simulator, base, args.final_rounds, args.threads, args.seed)
        verified = {
            key: row[key]
            for key in ("head_target", "tail_target", "duplicate_penalty", "wild_profile")
        }
        verified.update(result)
        verified["score"] = score(verified, args.target_hit_rate, baseline_retry)
        final.append(verified)

    final.sort(key=lambda row: float(row["score"]))
    best = final[0]
    if args.output:
        output = args.output.resolve()
        write_config(
            output,
            candidate_base(
                simulator.CFG_NATURAL,
                float(best["head_target"]),
                float(best["tail_target"]),
                float(best["duplicate_penalty"]),
                str(best["wild_profile"]),
            ),
        )
    print(json.dumps({
        "base_config": str(base_path),
        "rtp_config": str(rtp_path),
        "target_hit_rate": args.target_hit_rate,
        "baseline": baseline,
        "best": best,
        "finalists": final,
        "output": str(args.output.resolve()) if args.output else None,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
