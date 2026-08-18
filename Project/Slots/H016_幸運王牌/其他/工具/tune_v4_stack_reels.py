from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
import random
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[2]
CONFIG = PROJECT / "config.js"
RTP_CONFIGS = (PROJECT / "config_92A.js", PROJECT / "config_94A.js")
BUILDER = PROJECT / "其他" / "工具" / "build_competitor_comparison.py"
STYLE_TUNER = PROJECT / "其他" / "工具" / "tune_v4_natural_style.py"
VERSION3_CONFIG = PROJECT / "Versions" / "3.0" / "config.js"
CONFIG_PATTERN = re.compile(r"window\.H016_CONFIG\s*=\s*(\{.*\})\s*;", re.DOTALL)
TABLES = {"BG": ("bg_1", "bg_2", "bg_3"), "FG": ("fg_1", "fg_2", "fg_3")}
GROUPS = {"BG": "base", "FG": "free"}
ALIASES = {
    "bg_high": "bg_1", "bg_low": "bg_2",
    "fg_high_a": "fg_1", "fg_high_k": "fg_2", "fg_high_q": "fg_3",
    "fg_high_j": "fg_1", "fg_low": "fg_1",
}
RTP_METADATA_KEYS = (
    "parsheet_id", "excel_version", "rtp_label", "runtime_version",
    "source_multiplier_xlsx",
)


def load_module(name: str, path: Path):
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


def load_config(path: Path) -> tuple[str, dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig")
    match = CONFIG_PATTERN.search(text)
    if match is None:
        raise ValueError(f"Cannot find config payload in {path}")
    return text[:match.start()].rstrip(), json.loads(match.group(1))


def render(header: str, config: dict[str, Any]) -> str:
    prefix = f"{header}\n" if header else ""
    payload = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    return f"{prefix}window.H016_CONFIG={payload};\n"


def atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def canonical(symbol: int) -> int:
    return symbol - 8 if 11 <= symbol <= 18 else symbol


def rebuild_pre_stack_config(current: dict[str, Any], tuner) -> dict[str, Any]:
    baseline = tuner.load_config(VERSION3_CONFIG)
    result = copy.deepcopy(current)
    for table_name in (*tuner.PRIMARY_BG, *tuner.PRIMARY_FG):
        result["tables"][table_name] = copy.deepcopy(baseline["tables"][table_name])
        tuner.suppress_stack_weights(result["tables"][table_name], 1.2)
    result["tables"]["buy"] = copy.deepcopy(baseline["tables"]["buy"])
    result["tables"]["bg_1"]["random_wild"]["weights"] = tuner.random_wild(
        result["tables"]["bg_1"]["random_wild"]["weights"], 21860
    )
    result["tables"]["bg_2"]["random_wild"]["weights"] = tuner.random_wild(
        result["tables"]["bg_2"]["random_wild"]["weights"], 12792
    )
    result["tables"]["bg_3"]["random_wild"]["weights"] = [1, 0, 0, 0]
    result["tables"]["fg_3"] = copy.deepcopy(result["tables"]["fg_1"])
    result["tables"]["fg_3"]["random_wild"] = copy.deepcopy(
        baseline["tables"]["fg_3"]["random_wild"]
    )
    tuner.halve_initial_gold(result["tables"]["fg_3"])
    tuner.halve_drop_gold(result["tables"]["fg_3"])
    for group in ("free", "retrigger"):
        result["table_selection"][group] = [
            {"table": "fg_1", "weight": 4000},
            {"table": "fg_2", "weight": 3000},
            {"table": "fg_3", "weight": 3000},
        ]
    for alias, primary in tuner.ALIASES.items():
        result["tables"][alias] = copy.deepcopy(result["tables"][primary])
    return result


def table_probabilities(config: dict[str, Any], scene: str) -> dict[str, float]:
    selected = {
        str(item["table"]): float(item["weight"])
        for item in config["table_selection"][GROUPS[scene]]
        if float(item["weight"]) > 0
    }
    total = sum(selected.values())
    return {table: selected.get(table, 0.0) / total for table in TABLES[scene]}


def effective_stop_weights(config: dict[str, Any], scene: str, reel: int) -> list[float]:
    result = [0.0] * 200
    probabilities = table_probabilities(config, scene)
    for table in TABLES[scene]:
        weights = list(map(float, config["tables"][table]["weights"][reel]))
        total = sum(weights)
        for stop, weight in enumerate(weights):
            result[stop] += probabilities[table] * weight / total
    return result


def position_coefficients(weights: list[int]) -> list[float]:
    total = float(sum(weights))
    length = len(weights)
    return [
        sum(weights[(position - row) % length] for row in range(4)) / (4 * total)
        for position in range(length)
    ]


def window_counts(builder, config: dict[str, Any], reel: list[int], stop: int):
    names = [
        builder.symbol_name(config, reel[(stop + row) % len(reel)], merge_gold=True)
        for row in range(4)
    ]
    return builder.visible_stack_counts(names)


def competitor_targets(builder, competitor: dict[str, Any], scene: str, reel: int):
    data = competitor["counts"][scene]
    denominator = max(1, data["stack_total"][reel])
    return {
        (symbol, length): data["stack"][reel][(symbol, length)] / denominator
        for symbol in builder.SYMBOLS for length in (2, 3, 4)
    }


def exact_rates(builder, config: dict[str, Any], scene: str, reel: int):
    data = builder.mixed_rng_stack_data(config, GROUPS[scene])
    return {
        (symbol, length): float(data["counts"][reel][(symbol, length)])
        for symbol in builder.SYMBOLS for length in (2, 3, 4)
    }


def max_cyclic_run(values: list[int]) -> int:
    if not values:
        return 0
    best = run = 1
    doubled = values + values
    for index in range(1, len(doubled)):
        run = run + 1 if doubled[index] == doubled[index - 1] else 1
        best = max(best, min(run, len(values)))
    return best


def optimize_reel(
    builder, config: dict[str, Any], competitor: dict[str, Any], scene: str,
    reel_index: int, iterations: int, seed: int, exposure_limit_pp: float,
    retention: float,
) -> dict[str, Any]:
    tables = TABLES[scene]
    originals = [list(map(int, config["tables"][table]["reels"][reel_index])) for table in tables]
    canonical_originals = [[canonical(value) for value in reel] for reel in originals]
    if any(values != canonical_originals[0] for values in canonical_originals[1:]):
        raise ValueError(f"{scene} R{reel_index + 1}: primary canonical reels differ")
    arrangement = canonical_originals[0].copy()
    permutation = list(range(len(arrangement)))
    allowed = [
        position for position in range(len(arrangement))
        if all(3 <= canonical(originals[index][position]) <= 10 for index in range(len(tables)))
    ]
    effective = effective_stop_weights(config, scene, reel_index)
    targets = competitor_targets(builder, competitor, scene, reel_index)
    before = exact_rates(builder, config, scene, reel_index)
    current: Counter[tuple[str, int]] = Counter()
    for stop, weight in enumerate(effective):
        for key, occurrences in window_counts(builder, config, arrangement, stop).items():
            current[key] += weight * occurrences

    coefficients = {
        table: position_coefficients(list(map(int, config["tables"][table]["weights"][reel_index])))
        for table in tables
    }
    exposure_reference: dict[str, Counter[int]] = {table: Counter() for table in tables}
    for table_index, table in enumerate(tables):
        for position, symbol in enumerate(originals[table_index]):
            exposure_reference[table][symbol] += coefficients[table][position]
    exposure_current = copy.deepcopy(exposure_reference)
    initial_run = max_cyclic_run(arrangement)

    def drift() -> float:
        return max(
            abs(exposure_current[table][symbol] - exposure_reference[table][symbol])
            for table in tables for symbol in range(3, 19)
        )

    def violations(rates):
        return {key for key, target in targets.items() if rates[key] > target + 5e-8}

    def retention_ok(rates) -> bool:
        return all(
            rates[key] + 5e-8 >= retention * min(before[key], target)
            for key, target in targets.items()
        )

    def score(rates) -> float:
        value = 0.0
        for key, target in targets.items():
            actual = rates[key]
            scale = max(target, 0.0025)
            desired = target * 0.985 if before[key] > target else before[key]
            value += ((actual - desired) / scale) ** 2
            if actual > target:
                value += 50_000.0 * ((actual - target) / scale) ** 2
            floor = retention * min(before[key], target)
            if floor > 0 and actual < floor:
                value += 5_000.0 * ((floor - actual) / scale) ** 2
        limit = exposure_limit_pp / 100.0
        if drift() > limit:
            value += 50_000.0 * ((drift() - limit) / max(limit, 1e-8)) ** 2
        return value

    original_violations = len(violations(current))
    if not original_violations:
        return {"scene": scene, "reel": reel_index + 1, "changed_positions": 0,
                "max_exposure_drift_pp": 0.0, "violations_before": 0, "violations_after": 0}

    rng = random.Random(seed)
    current_score = score(current)
    best_score = math.inf
    best_state = None
    for iteration in range(iterations):
        violated = violations(current)
        bad_positions: list[int] = []
        if violated:
            for stop in range(len(arrangement)):
                counts = window_counts(builder, config, arrangement, stop)
                if any(key in violated for key in counts):
                    bad_positions.extend(
                        position for row in range(4)
                        if (position := (stop + row) % len(arrangement)) in allowed
                    )
        first = rng.choice(bad_positions if bad_positions and rng.random() < 0.8 else allowed)
        different = [p for p in allowed if p != first and arrangement[p] != arrangement[first]]
        if not different:
            continue
        if rng.random() < 0.9:
            candidates = rng.sample(different, min(40, len(different)))
            second = min(candidates, key=lambda p: max(
                abs(coefficients[table][first] - coefficients[table][p]) for table in tables
            ))
        else:
            second = rng.choice(different)
        affected = {
            (position - row) % len(arrangement)
            for position in (first, second) for row in range(4)
        }
        old_local: Counter[tuple[str, int]] = Counter()
        for stop in affected:
            for key, occurrences in window_counts(builder, config, arrangement, stop).items():
                old_local[key] += effective[stop] * occurrences

        symbol_first, symbol_second = arrangement[first], arrangement[second]
        actual_pairs = {
            table: (originals[index][permutation[first]], originals[index][permutation[second]])
            for index, table in enumerate(tables)
        }
        arrangement[first], arrangement[second] = symbol_second, symbol_first
        permutation[first], permutation[second] = permutation[second], permutation[first]
        for table in tables:
            delta = coefficients[table][second] - coefficients[table][first]
            actual_first, actual_second = actual_pairs[table]
            exposure_current[table][actual_first] += delta
            exposure_current[table][actual_second] -= delta
        new_local: Counter[tuple[str, int]] = Counter()
        for stop in affected:
            for key, occurrences in window_counts(builder, config, arrangement, stop).items():
                new_local[key] += effective[stop] * occurrences
        for key in set(old_local) | set(new_local):
            current[key] += new_local[key] - old_local[key]

        proposed = score(current)
        progress = iteration / max(1, iterations - 1)
        temperature = 1.5 * (0.001 / 1.5) ** progress
        accept = proposed <= current_score or rng.random() < math.exp(
            min(0.0, (current_score - proposed) / max(temperature, 1e-12))
        )
        if accept:
            current_score = proposed
            hard_ok = (
                not violations(current) and retention_ok(current)
                and drift() <= exposure_limit_pp / 100.0 + 1e-12
                and max_cyclic_run(arrangement) <= initial_run
            )
            if hard_ok and proposed < best_score:
                best_score = proposed
                best_state = (arrangement.copy(), permutation.copy(), copy.deepcopy(exposure_current))
        else:
            for key in set(old_local) | set(new_local):
                current[key] += old_local[key] - new_local[key]
            for table in tables:
                delta = coefficients[table][second] - coefficients[table][first]
                actual_first, actual_second = actual_pairs[table]
                exposure_current[table][actual_first] -= delta
                exposure_current[table][actual_second] += delta
            arrangement[first], arrangement[second] = symbol_first, symbol_second
            permutation[first], permutation[second] = permutation[second], permutation[first]

    if best_state is None:
        raise RuntimeError(f"{scene} R{reel_index + 1}: no hard-constraint solution")
    _, permutation, exposure_current = best_state
    for table_index, table in enumerate(tables):
        updated = [originals[table_index][source] for source in permutation]
        if Counter(updated) != Counter(originals[table_index]):
            raise AssertionError(f"{table} R{reel_index + 1}: token multiset changed")
        if any(
            updated[position] != originals[table_index][position]
            for position in range(200) if originals[table_index][position] == 2
        ):
            raise AssertionError(f"{table} R{reel_index + 1}: SC position changed")
        config["tables"][table]["reels"][reel_index] = updated
    after = exact_rates(builder, config, scene, reel_index)
    if any(after[key] > targets[key] + 5e-8 for key in targets):
        raise AssertionError(f"{scene} R{reel_index + 1}: stack cap failed")
    if any(after[key] + 5e-8 < retention * min(before[key], targets[key]) for key in targets):
        raise AssertionError(f"{scene} R{reel_index + 1}: retention failed")
    return {
        "scene": scene, "reel": reel_index + 1,
        "changed_positions": sum(index != source for index, source in enumerate(permutation)),
        "max_exposure_drift_pp": max(
            abs(exposure_current[table][symbol] - exposure_reference[table][symbol]) * 100
            for table in tables for symbol in range(3, 19)
        ),
        "violations_before": original_violations, "violations_after": 0,
    }


def sync_aliases(config: dict[str, Any]) -> None:
    for alias, primary in ALIASES.items():
        config["tables"][alias] = copy.deepcopy(config["tables"][primary])


def sync_rtp_configs(base: dict[str, Any]) -> dict[str, Any]:
    audit = {}
    for path in RTP_CONFIGS:
        header, previous = load_config(path)
        updated = copy.deepcopy(base)
        for key in RTP_METADATA_KEYS:
            if key in previous:
                updated[key] = copy.deepcopy(previous[key])
        updated["card_system"] = copy.deepcopy(previous["card_system"])
        atomic_write(path, render(header, updated))
        audit[path.name] = {"card_system_preserved": updated["card_system"] == previous["card_system"]}
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description="Cap H016 stack rates at Super Ace")
    parser.add_argument("--iterations", type=int, default=400_000)
    parser.add_argument("--seed", type=int, default=20260818)
    parser.add_argument("--max-exposure-drift-pp", type=float, default=1.0)
    parser.add_argument("--stack-retention", type=float, default=0.90)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--validate-current", action="store_true")
    args = parser.parse_args()
    builder = load_module("h016_stack_builder", BUILDER)
    tuner = load_module("h016_style_tuner", STYLE_TUNER)
    _, current = load_config(CONFIG)
    baseline = rebuild_pre_stack_config(current, tuner)
    config = copy.deepcopy(current if args.validate_current else baseline)
    competitor = builder.raw_competitor()
    audit = []
    if not args.validate_current:
        for scene_index, scene in enumerate(("BG", "FG")):
            for reel in range(5):
                audit.append(optimize_reel(
                    builder, config, competitor, scene, reel, args.iterations,
                    args.seed + scene_index * 100 + reel,
                    args.max_exposure_drift_pp, args.stack_retention,
                ))
        sync_aliases(config)
    cap_failures = retention_failures = 0
    adjusted_cells = []
    for scene in ("BG", "FG"):
        for reel in range(5):
            targets = competitor_targets(builder, competitor, scene, reel)
            before = exact_rates(builder, baseline, scene, reel)
            after = exact_rates(builder, config, scene, reel)
            cap_failures += sum(after[key] > targets[key] + 5e-8 for key in targets)
            retention_failures += sum(
                after[key] + 5e-8 < args.stack_retention * min(before[key], targets[key])
                for key in targets
            )
            adjusted_cells.extend(
                {
                    "scene": scene, "reel": reel + 1, "symbol": key[0],
                    "stack": key[1], "before": before[key], "after": after[key],
                    "competitor": targets[key],
                }
                for key in targets if before[key] > targets[key] + 5e-8
            )
    if cap_failures or retention_failures:
        raise AssertionError({"cap_failures": cap_failures, "retention_failures": retention_failures})
    rtp_audit = None
    if args.write and not args.validate_current:
        atomic_write(CONFIG, render(
            "// H016 active 4.0 natural math; stack reels tuned by "
            "其他/工具/tune_v4_stack_reels.py.", config
        ))
        rtp_audit = sync_rtp_configs(config)
    print(json.dumps({
        "written": args.write, "final_violations": cap_failures,
        "retention_failures": retention_failures, "audit": audit,
        "adjusted_cells": adjusted_cells,
        "rtp_configs": rtp_audit,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
