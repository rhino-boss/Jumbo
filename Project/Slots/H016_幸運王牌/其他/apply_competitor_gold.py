from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
CONFIG = PROJECT / "config_92.js"
BUILDER = HERE / "build_competitor_comparison.py"

BASE_IDS = tuple(range(3, 11))
GOLD_OFFSET = 8
SCENE_MASTER = {"BG": "bg_1", "FG": "fg_1"}
SCENE_TABLES = {
    "BG": ("bg_1", "bg_2", "bg_3", "bg_high", "bg_low", "buy"),
    "FG": (
        "fg_1", "fg_2", "fg_3", "fg_high_a", "fg_high_k", "fg_high_q",
        "fg_high_j", "fg_low", "super",
    ),
}


def load_builder():
    name = "h016_competitor_builder_for_gold"
    spec = importlib.util.spec_from_file_location(name, BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {BUILDER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(name, None)


def load_config(path: Path = CONFIG) -> tuple[dict[str, Any], str, str]:
    text = path.read_text(encoding="utf-8-sig")
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Cannot find JSON payload in {path}")
    return json.loads(match.group(0)), text[: match.start()], text[match.end() :]


def competitor_targets(builder) -> dict[str, dict[str, dict[str, list[float]]]]:
    competitor = builder.raw_competitor()
    result: dict[str, dict[str, dict[str, list[float]]]] = {}
    for scene in ("BG", "FG"):
        counts = competitor["counts"][scene]
        result[scene] = {}
        for stage in ("initial", "drop"):
            totals = counts[f"{stage}_total"]
            result[scene][stage] = {}
            for symbol_id in BASE_IDS:
                symbol = builder.symbol_name(builder.load_model_config(), symbol_id)
                result[scene][stage][symbol] = [
                    counts[f"gold_symbol_{stage}"][reel][symbol] / max(1, totals[reel])
                    for reel in range(5)
                ]
    return result


def canonical(symbol_id: int) -> int:
    return symbol_id - GOLD_OFFSET if 11 <= symbol_id <= 18 else symbol_id


def visible_contribution(weights: list[int], position: int) -> int:
    length = len(weights)
    return sum(weights[(position - row) % length] for row in range(4))


def closest_subset(contributions: list[int], target: float) -> set[int]:
    """Subset-sum with compact bitsets, followed by exact one/two move refinement."""
    if target <= 0 or not contributions:
        return set()

    scale = 10
    scaled = [max(1, round(value / scale)) for value in contributions]
    scaled_target = round(target / scale)
    cap = scaled_target + max(scaled)
    mask = (1 << (cap + 1)) - 1
    history = [1]
    bits = 1
    for value in scaled:
        bits |= (bits << value) & mask
        history.append(bits)

    below_bits = bits & ((1 << (min(scaled_target, cap) + 1)) - 1)
    below = below_bits.bit_length() - 1 if below_bits else 0
    above_bits = bits >> min(scaled_target, cap)
    above = scaled_target + ((above_bits & -above_bits).bit_length() - 1) if above_bits else below
    best_sum = min((below, above), key=lambda value: abs(value - scaled_target))

    selected: set[int] = set()
    remaining = best_sum
    for index in range(len(scaled), 0, -1):
        previous = history[index - 1]
        if remaining <= cap and ((previous >> remaining) & 1):
            continue
        selected.add(index - 1)
        remaining -= scaled[index - 1]
    if remaining != 0:
        raise RuntimeError("Could not reconstruct gold-position subset")

    def total(selection: set[int]) -> int:
        return sum(contributions[index] for index in selection)

    current = total(selected)
    while True:
        best_error = abs(current - target)
        best_action: tuple[str, int, int | None, int] | None = None
        for index, value in enumerate(contributions):
            candidate = current - value if index in selected else current + value
            error = abs(candidate - target)
            if error + 1e-9 < best_error:
                best_error = error
                best_action = ("remove" if index in selected else "add", index, None, candidate)
        selected_list = list(selected)
        unselected_list = [index for index in range(len(contributions)) if index not in selected]
        for old in selected_list:
            for new in unselected_list:
                candidate = current - contributions[old] + contributions[new]
                error = abs(candidate - target)
                if error + 1e-9 < best_error:
                    best_error = error
                    best_action = ("swap", old, new, candidate)
        if best_action is None:
            break
        action, first, second, current = best_action
        if action == "add":
            selected.add(first)
        elif action == "remove":
            selected.remove(first)
        else:
            selected.remove(first)
            selected.add(int(second))
    return selected


def apply_initial_gold(
    config: dict[str, Any], targets: dict[str, dict[str, dict[str, list[float]]]]
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for scene, table_name in SCENE_MASTER.items():
        table = config["tables"][table_name]
        for reel_index in range(5):
            reel = [canonical(int(symbol)) for symbol in table["reels"][reel_index]]
            weights = [int(weight) for weight in table["weights"][reel_index]]
            denominator = 4 * sum(weights)
            for symbol_id in BASE_IDS:
                symbol = config["symbol_names"][str(symbol_id)]
                positions = [index for index, value in enumerate(reel) if value == symbol_id]
                contributions = [visible_contribution(weights, position) for position in positions]
                target_ratio = float(targets[scene]["initial"][symbol][reel_index])
                selected_local = closest_subset(contributions, target_ratio * denominator)
                for local_index in selected_local:
                    reel[positions[local_index]] = symbol_id + GOLD_OFFSET
                actual_ratio = sum(contributions[index] for index in selected_local) / denominator
                result.append({
                    "scene": scene,
                    "stage": "initial",
                    "symbol": symbol,
                    "reel": reel_index + 1,
                    "target": target_ratio,
                    "actual": actual_ratio,
                    "difference_pp": (actual_ratio - target_ratio) * 100,
                    "gold_positions": len(selected_local),
                })
            table["reels"][reel_index] = reel
    return result


def apply_drop_gold(
    config: dict[str, Any], targets: dict[str, dict[str, dict[str, list[float]]]]
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for scene, table_name in SCENE_MASTER.items():
        table = config["tables"][table_name]
        for reel_index in range(5):
            values = [int(value) for value in table["drop_values"][reel_index]]
            weights = [int(weight) for weight in table["drop_weights"][reel_index]]
            denominator = sum(weights)
            for symbol_id in BASE_IDS:
                symbol = config["symbol_names"][str(symbol_id)]
                base_index = values.index(symbol_id)
                gold_index = values.index(symbol_id + GOLD_OFFSET)
                combined = weights[base_index] + weights[gold_index]
                target_ratio = float(targets[scene]["drop"][symbol][reel_index])
                desired_gold = min(combined, max(0, round(target_ratio * denominator)))
                weights[gold_index] = desired_gold
                weights[base_index] = combined - desired_gold
                actual_ratio = desired_gold / denominator if denominator else 0.0
                result.append({
                    "scene": scene,
                    "stage": "drop",
                    "symbol": symbol,
                    "reel": reel_index + 1,
                    "target": target_ratio,
                    "actual": actual_ratio,
                    "difference_pp": (actual_ratio - target_ratio) * 100,
                    "gold_weight": desired_gold,
                })
            table["drop_weights"][reel_index] = weights
    return result


def synchronize(config: dict[str, Any]) -> None:
    for scene, master in SCENE_MASTER.items():
        for table_name in SCENE_TABLES[scene]:
            if table_name not in config["tables"]:
                raise ValueError(f"Missing table {table_name}")
            config["tables"][table_name] = copy.deepcopy(config["tables"][master])


def validate(config: dict[str, Any], metrics: list[dict[str, Any]]) -> None:
    for scene, master in SCENE_MASTER.items():
        table = config["tables"][master]
        for table_name in SCENE_TABLES[scene]:
            if config["tables"][table_name] != table:
                raise ValueError(f"{table_name} is not identical to {master}")
        for reel, weights in zip(table["reels"], table["weights"]):
            if len(reel) != 200 or len(weights) != 200:
                raise ValueError(f"{master}: reel and weight lengths must remain 200")
            if not all(type(weight) is int and weight > 0 for weight in weights):
                raise ValueError(f"{master}: stop weights must remain positive integers")
            if max(weights) / min(weights) > 10 + 1e-12:
                raise ValueError(f"{master}: stop weight ratio exceeds 10x")
        for drop_weights in table["drop_weights"]:
            if not all(type(weight) is int and weight >= 0 for weight in drop_weights):
                raise ValueError(f"{master}: drop weights must be non-negative integers")

    for metric in metrics:
        if metric["reel"] in (1, 5) and not math.isclose(metric["actual"], 0.0, abs_tol=1e-15):
            raise ValueError(f"Gold must remain zero on R{metric['reel']}: {metric}")


def write_config(config: dict[str, Any], prefix: str, suffix: str) -> None:
    payload = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    temporary = CONFIG.with_name(CONFIG.name + ".tmp")
    temporary.write_text(prefix + payload + suffix, encoding="utf-8")
    temporary.replace(CONFIG)


def main() -> None:
    parser = argparse.ArgumentParser(description="Match H016 per-symbol/per-reel gold ratios to Super Ace")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--bg-zero-weight", type=int, help="Optional BG Random Wild zero weight")
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()

    builder = load_builder()
    config, prefix, suffix = load_config()
    targets = competitor_targets(builder)
    metrics = apply_initial_gold(config, targets)
    metrics.extend(apply_drop_gold(config, targets))
    if args.bg_zero_weight is not None:
        if args.bg_zero_weight < 0:
            parser.error("--bg-zero-weight must be non-negative")
        config["tables"]["bg_1"]["random_wild"] = {
            "values": [0, 2, 3, 4],
            "weights": [args.bg_zero_weight, 1401, 235, 18],
        }
    synchronize(config)
    validate(config, metrics)
    if args.write:
        write_config(config, prefix, suffix)

    initial = [item for item in metrics if item["stage"] == "initial"]
    drop = [item for item in metrics if item["stage"] == "drop"]
    result = {
        "written": bool(args.write),
        "bg_random_wild_weights": config["tables"]["bg_1"]["random_wild"]["weights"],
        "initial_max_abs_difference_pp": max(abs(item["difference_pp"]) for item in initial),
        "initial_mean_abs_difference_pp": sum(abs(item["difference_pp"]) for item in initial) / len(initial),
        "drop_max_abs_difference_pp": max(abs(item["difference_pp"]) for item in drop),
        "drop_mean_abs_difference_pp": sum(abs(item["difference_pp"]) for item in drop) / len(drop),
    }
    if not args.summary_only:
        result["metrics"] = metrics
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
