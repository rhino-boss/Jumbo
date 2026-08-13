from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
import os
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
CONFIG = PROJECT / "config_92.js"
BASELINE = PROJECT / "Versions" / "1.0" / "config_92.js"
SIMULATOR = PROJECT / "Simulator.py"
BUILDER = HERE / "build_competitor_comparison.py"
XLSX = PROJECT / "Source" / "H0161.xlsx"

SCORE_IDS = tuple(range(3, 11))
FOCUS_IDS = {6, 7, 9, 10}  # M4, A, Q, J
OTHER_IDS = set(SCORE_IDS) - FOCUS_IDS
W2_CONDITIONAL = (1401, 235, 18)
ALIASES = {
    "bg_high": "bg_1", "bg_low": "bg_2", "buy": "bg_3",
    "fg_high_a": "fg_1", "fg_high_k": "fg_2", "fg_high_q": "fg_3",
    "fg_high_j": "fg_1", "fg_low": "fg_1", "super": "fg_2",
}


def load_js(path: Path) -> tuple[dict[str, Any], str, str]:
    text = path.read_text(encoding="utf-8-sig")
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Cannot find JSON payload in {path}")
    return json.loads(match.group(0)), text[:match.start()], text[match.end():]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(name, None)


def canonical(symbol: int) -> int:
    return symbol - 8 if 11 <= symbol <= 18 else symbol


def has_sc(reel: list[int], stop: int) -> bool:
    return any(canonical(reel[(stop + row) % len(reel)]) == 2 for row in range(4))


def sc_exposure(reel: list[int], weights: list[int]) -> float:
    total = sum(max(0, weight) for weight in weights)
    return sum(weight for stop, weight in enumerate(weights) if weight > 0 and has_sc(reel, stop)) / max(1, total)


def redistribute_without_c1(values: list[int], weights: list[int]) -> list[int]:
    total = sum(weights)
    keep = [index for index, value in enumerate(values) if canonical(value) != 2]
    denominator = sum(weights[index] for index in keep)
    if denominator <= 0:
        raise ValueError("Cannot redistribute C1 drop weight")
    raw = [0.0] * len(weights)
    for index in keep:
        raw[index] = total * weights[index] / denominator
    result = [math.floor(value) for value in raw]
    remainder = total - sum(result)
    order = sorted(keep, key=lambda index: raw[index] - result[index], reverse=True)
    for index in order[:remainder]:
        result[index] += 1
    return result


def block_fg_trigger(table: dict[str, Any], requested: set[int]) -> set[int]:
    candidates = [reel for reel in range(5) if reel not in requested]
    extra = min(candidates, key=lambda reel: sc_exposure(table["reels"][reel], table["weights"][reel]))
    blocked = set(requested) | {extra}
    for reel in blocked:
        table["weights"][reel] = [
            0 if has_sc(table["reels"][reel], stop) else int(weight)
            for stop, weight in enumerate(table["weights"][reel])
        ]
    # C1 does not participate in a win and can accumulate through refills.
    # Removing it from every drop reel is necessary to make the no-FG result hard,
    # rather than merely likely, when only config may change.
    table["drop_weights"] = [
        redistribute_without_c1(values, weights)
        for values, weights in zip(table["drop_values"], table["drop_weights"])
    ]
    return blocked


def bounded_weights(raw: list[float], zero_mask: list[bool] | None = None) -> list[int]:
    zero_mask = zero_mask or [False] * len(raw)
    positives = [value for value, disabled in zip(raw, zero_mask) if not disabled and value > 0]
    if not positives:
        raise ValueError("A reel cannot have all stop weights disabled")
    floor = max(positives) / 10.0
    clipped = [0.0 if disabled else max(floor, value) for value, disabled in zip(raw, zero_mask)]
    scale = 2_000_000 / sum(clipped)
    result = [0 if disabled else max(1, round(value * scale)) for value, disabled in zip(clipped, zero_mask)]
    positive = [value for value in result if value > 0]
    minimum = math.ceil(max(positive) / 10)
    return [0 if value == 0 else max(minimum, value) for value in result]


def rescale_drop(
    values: list[int], weights: list[int], boost_strength: float, suppress_strength: float,
) -> list[int]:
    factors = []
    for value in values:
        symbol = canonical(value)
        factors.append(
            2.0 ** boost_strength if symbol in FOCUS_IDS
            else 0.5 ** suppress_strength if symbol in OTHER_IDS
            else 1.0
        )
    raw = [weight * factor for weight, factor in zip(weights, factors)]
    total = sum(weights)
    denominator = sum(raw)
    scaled = [total * value / denominator for value in raw]
    result = [math.floor(value) for value in scaled]
    order = sorted(range(len(result)), key=lambda index: scaled[index] - result[index], reverse=True)
    for index in order[:total - sum(result)]:
        result[index] += 1
    return result


def shape_focus(
    table: dict[str, Any], boost_strength: float, suppress_strength: float,
    blocked: set[int] | None = None,
) -> None:
    blocked = blocked or set()
    for reel in range(5):
        base = table["weights"][reel]
        raw: list[float] = []
        mask: list[bool] = []
        for stop, weight in enumerate(base):
            disabled = weight <= 0 or (reel in blocked and has_sc(table["reels"][reel], stop))
            factor = 1.0
            for row in range(4):
                symbol = canonical(table["reels"][reel][(stop + row) % 200])
                factor *= (
                    2.0 ** boost_strength if symbol in FOCUS_IDS
                    else 0.5 ** suppress_strength if symbol in OTHER_IDS
                    else 1.0
                )
            raw.append(max(1, weight) * factor)
            mask.append(disabled)
        table["weights"][reel] = bounded_weights(raw, mask)
        table["drop_weights"][reel] = rescale_drop(
            table["drop_values"][reel], table["drop_weights"][reel],
            boost_strength, suppress_strength,
        )


def shape_sc(table: dict[str, Any], bias: float) -> None:
    for reel in range(5):
        # BG3 is a dedicated trigger table.  Use a direct SC/non-SC ratio so
        # the source strip remains fixed and the <=10x stop-weight constraint
        # has a predictable, monotonic control surface.
        raw = [bias if has_sc(table["reels"][reel], stop) else 1.0 for stop in range(200)]
        table["weights"][reel] = bounded_weights(raw)


def table_metrics(simulator, config: dict[str, Any], table_name: str, scene: str, spins: int, seed: int) -> dict[str, Any]:
    game = simulator.LuckyAce(config, seed, False, False)
    hits: Counter[int] = Counter()
    w2_events = triggers = 0
    for _ in range(spins):
        spin = game.spin(table_name, free_game=scene == "FG")
        w2_events += spin.w2_events
        triggers += int(spin.scatter_count >= 3)
        for (symbol, _length), count in spin.symbol_length_hits.items():
            hits[int(symbol)] += count
    return {
        "spins": spins,
        "w2_rate": w2_events / spins,
        "trigger_rate": triggers / spins,
        "symbol_hit_rate": {symbol: hits[symbol] / spins for symbol in SCORE_IDS},
    }


def hit_objective(actual: dict[int, float], target: dict[int, float]) -> float:
    return sum(math.log(max(actual[symbol], 1e-6) / max(target[symbol], 1e-6)) ** 2 for symbol in SCORE_IDS)


def choose_focus_strength(
    simulator, config: dict[str, Any], table_name: str, scene: str,
    master: dict[str, Any], blocked: set[int], target: dict[int, float], samples: int,
) -> tuple[tuple[float, float], dict[str, Any]]:
    best: tuple[float, float, float, dict[str, Any], dict[str, Any]] | None = None
    for boost_strength in (0.0, 0.5, 1.0, 1.5):
        for suppress_strength in (0.5, 1.0, 1.5, 2.0, 3.0):
            table = copy.deepcopy(master)
            if scene == "BG":
                # master already contains the hard masks and no-C1 drops.
                shape_focus(table, boost_strength, suppress_strength, blocked)
            else:
                shape_focus(table, boost_strength, suppress_strength)
            config["tables"][table_name] = table
            seed = 72000 + round(boost_strength * 100) + round(suppress_strength * 1000)
            metrics = table_metrics(simulator, config, table_name, scene, samples, seed)
            objective = hit_objective(metrics["symbol_hit_rate"], target)
            if best is None or objective < best[0]:
                best = (
                    objective, boost_strength, suppress_strength,
                    copy.deepcopy(table), metrics,
                )
    assert best is not None
    config["tables"][table_name] = best[3]
    return (best[1], best[2]), best[4]


def correct_symbol_profile(
    simulator, config: dict[str, Any], table_name: str, scene: str,
    target: dict[int, float], samples: int, iterations: int = 3,
) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for iteration in range(iterations):
        metrics = table_metrics(
            simulator, config, table_name, scene, samples, 76000 + iteration,
        )
        correction = {
            symbol: min(1.5, max(0.67, (target[symbol] / max(metrics["symbol_hit_rate"][symbol], 1e-6)) ** 0.7))
            for symbol in SCORE_IDS
        }
        table = config["tables"][table_name]
        for reel in range(5):
            zero_mask = [weight <= 0 for weight in table["weights"][reel]]
            raw = []
            for stop, weight in enumerate(table["weights"][reel]):
                factor = 1.0
                for row in range(4):
                    symbol = canonical(table["reels"][reel][(stop + row) % 200])
                    if symbol in correction:
                        factor *= correction[symbol] ** 0.25
                raw.append(max(1, weight) * factor)
            table["weights"][reel] = bounded_weights(raw, zero_mask)

            values, weights = table["drop_values"][reel], table["drop_weights"][reel]
            drop_raw = [
                weight * correction.get(canonical(value), 1.0) ** 0.8
                for value, weight in zip(values, weights)
            ]
            total = sum(weights)
            denominator = sum(drop_raw)
            scaled = [total * value / denominator for value in drop_raw]
            result = [math.floor(value) for value in scaled]
            order = sorted(range(len(result)), key=lambda index: scaled[index] - result[index], reverse=True)
            for index in order[:total - sum(result)]:
                result[index] += 1
            table["drop_weights"][reel] = result
    return table_metrics(simulator, config, table_name, scene, samples, 76999)


def set_wild(table: dict[str, Any], zero: int, nonzero: tuple[int, int, int]) -> None:
    table["random_wild"] = {"values": [0, 2, 3, 4], "weights": [int(zero), *map(int, nonzero)]}


def refined_zero(zero: int, nonzero_total: int, observed: float, target: float) -> int:
    if observed <= 0:
        return max(0, zero // 2)
    probability = nonzero_total / (zero + nonzero_total)
    desired = min(0.999999, max(1e-8, probability * target / observed))
    return max(0, round(nonzero_total * (1 - desired) / desired))


def tune_wild(
    simulator, config: dict[str, Any], table_name: str, scene: str,
    target: float, nonzero: tuple[int, int, int], samples: int,
) -> tuple[int, dict[str, Any]]:
    nonzero_total = sum(nonzero)
    zero = 36_450 if scene == "BG" else 80_000
    metrics: dict[str, Any] = {}
    for iteration in range(4):
        set_wild(config["tables"][table_name], zero, nonzero)
        metrics = table_metrics(simulator, config, table_name, scene, samples, 81000 + iteration)
        observed = metrics["w2_rate"]
        if observed <= 0:
            zero = max(0, zero // 2)
            continue
        probability = nonzero_total / (zero + nonzero_total)
        desired_probability = min(0.999999, max(1e-8, probability * target / observed))
        proposed = round(nonzero_total * (1 - desired_probability) / desired_probability)
        if abs(proposed - zero) <= 5:
            break
        zero = max(0, proposed)
    set_wild(config["tables"][table_name], zero, nonzero)
    return zero, metrics


def sync_aliases(config: dict[str, Any]) -> None:
    for alias, primary in ALIASES.items():
        config["tables"][alias] = copy.deepcopy(config["tables"][primary])


def validate(config: dict[str, Any], original: dict[str, Any], blocked: dict[str, set[int]]) -> None:
    for name in ("bg_1", "bg_2", "bg_3", "fg_1", "fg_2", "fg_3"):
        table = config["tables"][name]
        if table["reels"] != original["tables"][name]["reels"]:
            raise ValueError(f"{name}: physical reel changed")
        for reel, weights in enumerate(table["weights"]):
            if len(weights) != 200 or any(type(weight) is not int or weight < 0 for weight in weights):
                raise ValueError(f"{name}.R{reel + 1}: invalid stop weights")
            positive = [weight for weight in weights if weight > 0]
            if not positive or max(positive) > 10 * min(positive):
                raise ValueError(f"{name}.R{reel + 1}: positive stop max/min exceeds 10x")
        for weights in table["drop_weights"]:
            if any(type(weight) is not int or weight < 0 for weight in weights) or sum(weights) <= 0:
                raise ValueError(f"{name}: invalid drop weights")
    for name, reels in blocked.items():
        table = config["tables"][name]
        for reel in reels:
            if any(weight > 0 and has_sc(table["reels"][reel], stop) for stop, weight in enumerate(table["weights"][reel])):
                raise ValueError(f"{name}.R{reel + 1}: SC remains reachable")
        for values, weights in zip(table["drop_values"], table["drop_weights"]):
            if any(weight > 0 and canonical(value) == 2 for value, weight in zip(values, weights)):
                raise ValueError(f"{name}: C1 remains in drop weights")
    if config["tables"]["bg_3"]["random_wild"]["weights"][1:] != [0, 0, 0]:
        raise ValueError("bg_3 Random Wild must be 0%")
    fg_wild = config["tables"]["fg_2"]["random_wild"]
    if fg_wild["weights"][2:] != [0, 0] or config["tables"]["fg_1"]["random_wild"] != fg_wild:
        raise ValueError("FG1/FG2 Random Wild must match and allow only 2")
    for alias, primary in ALIASES.items():
        if config["tables"][alias] != config["tables"][primary]:
            raise ValueError(f"{alias} differs from {primary}")


def atomic_write(path: Path, prefix: str, suffix: str, config: dict[str, Any]) -> None:
    fd, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(prefix + json.dumps(config, ensure_ascii=False, separators=(",", ":")) + suffix)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply H016 table roles using config only")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--calibration-samples", type=int, default=15_000)
    parser.add_argument("--final-samples", type=int, default=100_000)
    args = parser.parse_args()

    original, prefix, suffix = load_js(CONFIG)
    baseline, _, _ = load_js(BASELINE)
    config = copy.deepcopy(original)
    simulator = load_module(SIMULATOR, "h016_simulator_table_roles")
    builder = load_module(BUILDER, "h016_builder_table_roles")
    competitor = builder.raw_competitor()
    competitor_w2 = float(competitor["w2_bg_event_rate"])
    competitor_trigger = float(competitor["fg_trigger_rate"])

    bg_master = copy.deepcopy(baseline["tables"]["bg_1"])
    fg_master = copy.deepcopy(baseline["tables"]["fg_1"])
    config["tables"]["bg_1"] = copy.deepcopy(bg_master)
    config["tables"]["bg_2"] = copy.deepcopy(bg_master)
    config["tables"]["bg_3"] = copy.deepcopy(bg_master)
    config["tables"]["fg_1"] = copy.deepcopy(fg_master)
    config["tables"]["fg_2"] = copy.deepcopy(fg_master)
    config["tables"]["fg_3"] = copy.deepcopy(fg_master)

    requested = {"bg_1": {2, 4}, "bg_2": {0, 3}}
    blocked: dict[str, set[int]] = {}
    for name in ("bg_1", "bg_2"):
        table = config["tables"][name]
        candidates = [reel for reel in range(5) if reel not in requested[name]]
        extra = min(candidates, key=lambda reel: sc_exposure(table["reels"][reel], table["weights"][reel]))
        blocked[name] = requested[name] | {extra}
        block_fg_trigger(table, requested[name])

    reference_samples = max(10_000, args.calibration_samples)
    reference_hits = {
        "BG": table_metrics(
            simulator, config, "bg_1", "BG", reference_samples, 70001,
        )["symbol_hit_rate"],
        "FG": table_metrics(
            simulator, config, "fg_1", "FG", reference_samples, 70002,
        )["symbol_hit_rate"],
    }
    targets = {
        scene: {
            symbol: rate * (2.0 if symbol in FOCUS_IDS else 0.5)
            for symbol, rate in reference_hits[scene].items()
        }
        for scene in ("BG", "FG")
    }

    bg2_strength, _ = choose_focus_strength(
        simulator, config, "bg_2", "BG", copy.deepcopy(config["tables"]["bg_2"]),
        blocked["bg_2"], targets["BG"], args.calibration_samples,
    )
    fg2_strength, _ = choose_focus_strength(
        simulator, config, "fg_2", "FG", copy.deepcopy(config["tables"]["fg_2"]),
        set(), targets["FG"], args.calibration_samples,
    )
    correct_symbol_profile(
        simulator, config, "bg_2", "BG", targets["BG"], args.calibration_samples,
    )
    correct_symbol_profile(
        simulator, config, "fg_2", "FG", targets["FG"], args.calibration_samples,
    )

    best_sc: tuple[float, float, dict[str, Any], dict[str, Any]] | None = None
    trigger_target = competitor_trigger * 2
    # 1.32 was selected by the fixed-seed 100k fine grid (1.6930% versus the
    # Super Ace x2 target 1.6874%). Keep it explicit so reruns are reproducible.
    for bias in (1.32,):
        table = copy.deepcopy(bg_master)
        shape_sc(table, bias)
        table["random_wild"] = {"values": [0, 2, 3, 4], "weights": [1, 0, 0, 0]}
        config["tables"]["bg_3"] = table
        metrics = table_metrics(simulator, config, "bg_3", "BG", args.calibration_samples, 91000 + round(bias * 10))
        difference = abs(metrics["trigger_rate"] - trigger_target)
        if best_sc is None or difference < best_sc[0]:
            best_sc = (difference, bias, copy.deepcopy(table), metrics)
    assert best_sc is not None
    config["tables"]["bg_3"] = best_sc[2]

    bg1_zero, _ = tune_wild(
        simulator, config, "bg_1", "BG", competitor_w2, W2_CONDITIONAL, args.calibration_samples,
    )
    bg2_zero, _ = tune_wild(
        simulator, config, "bg_2", "BG", competitor_w2 * 2, W2_CONDITIONAL, args.calibration_samples,
    )
    config["tables"]["bg_3"]["random_wild"] = {"values": [0, 2, 3, 4], "weights": [1, 0, 0, 0]}
    fg2_zero, _ = tune_wild(
        simulator, config, "fg_2", "FG", competitor_w2 * 2, (sum(W2_CONDITIONAL), 0, 0), args.calibration_samples,
    )
    config["tables"]["fg_1"]["random_wild"] = copy.deepcopy(config["tables"]["fg_2"]["random_wild"])
    config["tables"]["fg_3"]["random_wild"] = {"values": [0, 2, 3, 4], "weights": [1, 0, 0, 0]}

    config["table_selection"] = {
        "base": [
            {"table": "bg_1", "weight": 450_000},
            {"table": "bg_2", "weight": 50_000},
            {"table": "bg_3", "weight": 500_000},
        ],
        "free": [
            {"table": "fg_1", "weight": 1},
            {"table": "fg_2", "weight": 1},
            {"table": "fg_3", "weight": 0},
        ],
        "retrigger": [
            {"table": "fg_1", "weight": 1},
            {"table": "fg_2", "weight": 1},
            {"table": "fg_3", "weight": 0},
        ],
    }
    sync_aliases(config)
    validate(config, original, blocked)

    final = {
        name: table_metrics(
            simulator, config, name, "BG" if name.startswith("bg") else "FG",
            args.final_samples, 101000 + index,
        )
        for index, name in enumerate(("bg_1", "bg_2", "bg_3", "fg_1", "fg_2"))
    }
    # One high-sample residual correction is more reliable than extending the
    # low-sample search. FG1 must copy FG2's final weights by requirement.
    bg1_zero = refined_zero(bg1_zero, sum(W2_CONDITIONAL), final["bg_1"]["w2_rate"], competitor_w2)
    bg2_zero = refined_zero(bg2_zero, sum(W2_CONDITIONAL), final["bg_2"]["w2_rate"], competitor_w2 * 2)
    fg2_zero = refined_zero(fg2_zero, sum(W2_CONDITIONAL), final["fg_2"]["w2_rate"], competitor_w2 * 2)
    set_wild(config["tables"]["bg_1"], bg1_zero, W2_CONDITIONAL)
    set_wild(config["tables"]["bg_2"], bg2_zero, W2_CONDITIONAL)
    set_wild(config["tables"]["fg_2"], fg2_zero, (sum(W2_CONDITIONAL), 0, 0))
    config["tables"]["fg_1"]["random_wild"] = copy.deepcopy(config["tables"]["fg_2"]["random_wild"])
    sync_aliases(config)
    validate(config, original, blocked)
    final = {
        name: table_metrics(
            simulator, config, name, "BG" if name.startswith("bg") else "FG",
            args.final_samples, 111000 + index,
        )
        for index, name in enumerate(("bg_1", "bg_2", "bg_3", "fg_1", "fg_2"))
    }
    if final["bg_1"]["trigger_rate"] or final["bg_2"]["trigger_rate"]:
        raise ValueError("BG1/BG2 still triggered FG in final validation")

    if args.write:
        atomic_write(CONFIG, prefix, suffix, config)

    print(json.dumps({
        "written": bool(args.write),
        "xlsx_touched": False,
        "targets": {
            "competitor_w2": competitor_w2,
            "competitor_w2_x2": competitor_w2 * 2,
            "competitor_fg_trigger_x2": trigger_target,
            "focus_hit_profile": "M4/A/Q/J = Scene table 1 x2; M1/M2/M3/K = Scene table 1 x0.5",
            "reference_symbol_hit_rate": reference_hits,
            "target_symbol_hit_rate": targets,
        },
        "blocked_reels": {name: [reel + 1 for reel in sorted(reels)] for name, reels in blocked.items()},
        "selected_strength": {"bg_2": bg2_strength, "fg_2": fg2_strength, "bg_3_sc_bias": best_sc[1]},
        "random_wild_zero": {"bg_1": bg1_zero, "bg_2": bg2_zero, "fg_1_fg_2": fg2_zero},
        "final": final,
        "table_selection": config["table_selection"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
