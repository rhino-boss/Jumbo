"""Search at most ten H016 v6 FG stop/table-weight candidates.

Only FG initial stop weights, FG free/retrigger table-selection weights, their
legacy alias stop weights, and version metadata may change.  Reels, drops,
gold, Random Wild, multipliers, BG, BF, SF, and Card System weights are frozen.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[2]
BASE_PATH = PROJECT / "config.js"
RTP_PATHS = (PROJECT / "config_92A.js", PROJECT / "config_94A.js")
SIMULATOR = PROJECT / "Simulator.py"
VERSION = "6.0.0.0"
PATTERN = re.compile(r"window\.H016_CONFIG\s*=\s*(\{.*\})\s*;", re.DOTALL)
PRIMARY = ("fg_1", "fg_2", "fg_3")
ALIASES = {
    "fg_high_a": "fg_1", "fg_high_j": "fg_1", "fg_low": "fg_1",
    "fg_high_k": "fg_2", "fg_high_q": "fg_3",
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_config(path: Path) -> tuple[str, dict[str, Any]]:
    source = path.read_text(encoding="utf-8-sig")
    match = PATTERN.search(source)
    if match is None:
        raise ValueError(f"Cannot parse {path}")
    return source[:match.start()].rstrip(), json.loads(match.group(1))


def atomic_config(path: Path, header: str, config: dict[str, Any]) -> None:
    payload = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    prefix = header + "\n" if header else ""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(f"{prefix}window.H016_CONFIG={payload};\n", encoding="utf-8")
    temporary.replace(path)


def modules():
    os.environ["H016_CONFIG_FILE"] = "config.js"
    os.environ["H016_CONFIG_RTP_FILE"] = "config_92A.js"
    os.environ["H016_CARD_SYSTEM_ENABLED"] = "true"
    os.environ["H016_CARD_SYSTEM_IS_NEWBIE"] = "false"
    os.environ["H016_RUN_ALL_COMBINATIONS"] = "false"
    os.environ["H016_OUTPUT_REPORT"] = "false"
    simulator = load_module("h016_v6_simulator", SIMULATOR)
    weight_tools = load_module(
        "h016_v6_weight_tools", Path(__file__).with_name("tune_v4_natural_style.py")
    )
    stack_tools = load_module(
        "h016_v6_stack_tools", Path(__file__).with_name("build_competitor_comparison.py")
    )
    return simulator, weight_tools, stack_tools


def boost_stack_weights(table: dict[str, Any], factor: float, weight_tools) -> None:
    for reel_index, (reel, weights) in enumerate(zip(table["reels"], table["weights"])):
        flags = weight_tools.stack_stop_flags(list(map(int, reel)))
        original = list(map(int, weights))
        adjusted = [
            float(weight) * factor if flag else float(weight)
            for weight, flag in zip(original, flags)
        ]
        table["weights"][reel_index] = weight_tools.largest_remainder(
            adjusted, sum(original), [weight > 0 for weight in original]
        )


def candidate(
    baseline: dict[str, Any], factor2: float, factor3: float,
    selection: tuple[int, int, int], weight_tools,
) -> dict[str, Any]:
    config = copy.deepcopy(baseline)
    boost_stack_weights(config["tables"]["fg_2"], factor2, weight_tools)
    boost_stack_weights(config["tables"]["fg_3"], factor3, weight_tools)
    for alias, primary in ALIASES.items():
        config["tables"][alias]["weights"] = copy.deepcopy(
            config["tables"][primary]["weights"]
        )
    rows = [
        {"table": table, "weight": int(weight)}
        for table, weight in zip(PRIMARY, selection)
    ]
    config["table_selection"]["free"] = copy.deepcopy(rows)
    config["table_selection"]["retrigger"] = copy.deepcopy(rows)
    return config


def stack_rate(config: dict[str, Any], stack_tools) -> float:
    data = stack_tools.mixed_rng_stack_data(config, "free")
    return sum(sum(data["counts"][reel].values()) for reel in range(5)) / sum(data["totals"])


def competitor_stack_rate(stack_tools) -> tuple[float, int]:
    competitor = stack_tools.raw_competitor()
    fg = competitor["counts"]["FG"]
    events = sum(sum(fg["stack"][reel].values()) for reel in range(5))
    rng = sum(int(fg["stack_total"][reel]) for reel in range(5))
    return events / rng, int(fg["spins"])


def run_card(simulator, config: dict[str, Any], rounds: int, seed: int) -> dict[str, float]:
    simulator.CARD_SYSTEM_ENABLED = True
    simulator.CARD_SYSTEM_IS_NEWBIE = False
    result = simulator.run_simulation(
        total_rounds=rounds, bet_mode=0, bet_multi=1,
        threads=8, config=config, seed=seed,
    )
    stats = result["stats"]
    fg_spins = max(1, int(stats["fg_spins"]))
    coin_in = max(1.0, float(stats["coin_in"]))
    return {
        "card_hit_rate": float(stats["fg_hit_spins"]) / fg_spins,
        "card_rtp": (float(stats["pay_bg"]) + float(stats["pay_fg"])) / coin_in,
        "fg_spins": fg_spins,
        "fg_triggers": int(stats["fg_triggers"]),
        "retry_avg": float(stats.get("retry_total", 0)) / max(1, int(stats["rounds"])),
        "retry_limit_exceeded": int(stats.get("retry_limit_exceeded", 0)),
    }


def unchanged_guard(before: dict[str, Any], after: dict[str, Any]) -> None:
    allowed = {
        *(f"tables.{name}.weights" for name in (*PRIMARY, *ALIASES)),
        "table_selection.free", "table_selection.retrigger", "excel_version",
    }

    def walk(left: Any, right: Any, path: str = "") -> list[str]:
        if type(left) is not type(right):
            return [path]
        if isinstance(left, dict):
            result = []
            for key in sorted(set(left) | set(right)):
                child = f"{path}.{key}" if path else key
                if key not in left or key not in right:
                    result.append(child)
                else:
                    result.extend(walk(left[key], right[key], child))
            return result
        if isinstance(left, list):
            return [] if left == right else [path]
        return [] if left == right else [path]

    illegal = [path for path in walk(before, after) if path not in allowed]
    if illegal:
        raise ValueError(f"v6 changed forbidden paths: {illegal}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--search-rounds", type=int, default=100_000)
    parser.add_argument("--confirm-rounds", type=int, default=500_000)
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--output", type=Path,
        default=PROJECT / "其他" / "診斷" / "H016_v6_fg_candidates.json",
    )
    args = parser.parse_args()
    simulator, weight_tools, stack_tools = modules()
    base_header, baseline = load_config(BASE_PATH)
    _rtp_header, rtp_92 = load_config(RTP_PATHS[0])
    competitor_rate, competitor_spins = competitor_stack_rate(stack_tools)
    baseline_rate = stack_rate(baseline, stack_tools)

    # Exactly ten bounded candidates.  Factors multiply only stops whose
    # four-cell visible window contains a canonical 2+ stack.
    definitions = [
        (4.0, 4.0, (0, 6500, 3500)),
        (6.0, 6.0, (0, 6500, 3500)),
        (8.0, 8.0, (0, 6500, 3500)),
        (10.0, 10.0, (0, 6500, 3500)),
        (12.0, 12.0, (0, 6500, 3500)),
        (8.0, 8.0, (0, 5000, 5000)),
        (8.0, 8.0, (0, 8000, 2000)),
        (4.0, 4.0, (2000, 5000, 3000)),
        (2.0, 2.0, (4000, 4000, 2000)),
        (1.0, 1.0, (6000, 2500, 1500)),
    ]
    rows = []
    for index, (factor2, factor3, selection) in enumerate(definitions, start=1):
        natural = candidate(baseline, factor2, factor3, selection, weight_tools)
        runtime = simulator.compose_runtime_config(natural, rtp_92)
        card = run_card(simulator, runtime, args.search_rounds, 6_100_000 + index)
        rate = stack_rate(natural, stack_tools)
        rows.append({
            "candidate": index,
            "factor_fg2": factor2,
            "factor_fg3": factor3,
            "selection_fg1_fg2_fg3": list(selection),
            "stack_rate": rate,
            "stack_vs_competitor": rate / competitor_rate,
            **card,
        })

    eligible = [
        row for row in rows
        if 0.38 <= row["card_hit_rate"] <= 0.45
        and row["retry_limit_exceeded"] == 0
    ]
    target = [row for row in eligible if row["stack_vs_competitor"] >= 0.5]
    if target:
        best = min(
            target,
            key=lambda row: (
                row["stack_vs_competitor"] - 0.5,
                abs(row["card_hit_rate"] - 0.415),
                row["candidate"],
            ),
        )
        selection_reason = "met >=50% competitor stack rate and 38-45% Card-On FG Hit Rate"
    elif eligible:
        best = max(eligible, key=lambda row: (row["stack_rate"], -abs(row["card_hit_rate"] - 0.415)))
        selection_reason = "best stack improvement among candidates within 38-45% Card-On FG Hit Rate"
    else:
        raise ValueError("None of the ten candidates met the 38-45% Card-On FG Hit Rate bound")

    definition = definitions[int(best["candidate"]) - 1]
    final_natural = candidate(baseline, *definition, weight_tools)
    final_runtime = simulator.compose_runtime_config(final_natural, rtp_92)
    confirmation = run_card(simulator, final_runtime, args.confirm_rounds, 6_200_000)
    best["confirmation"] = confirmation
    if not 0.38 <= confirmation["card_hit_rate"] <= 0.45:
        raise ValueError(
            f"Selected candidate failed confirmation Hit Rate: {confirmation['card_hit_rate']:.4%}"
        )
    if confirmation["retry_limit_exceeded"] != 0:
        raise ValueError("Selected candidate exceeded Card Retry Limit")

    output = {
        "version": VERSION,
        "scope": "FG stop weights and free/retrigger table-selection weights only",
        "search_rounds_per_candidate": args.search_rounds,
        "confirm_rounds": args.confirm_rounds,
        "competitor_fg_spins": competitor_spins,
        "competitor_stack_rate": competitor_rate,
        "baseline_stack_rate": baseline_rate,
        "baseline_vs_competitor": baseline_rate / competitor_rate,
        "candidates": rows,
        "selected": best,
        "selection_reason": selection_reason,
        "written": bool(args.write),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.write:
        final_natural["excel_version"] = "6"
        unchanged_guard(baseline, final_natural)
        atomic_config(
            BASE_PATH,
            "// H016 v6 FG stop/table weights; generated by 其他/工具/tune_v6_fg.py.",
            final_natural,
        )
        for path in RTP_PATHS:
            header, previous = load_config(path)
            runtime = simulator.compose_runtime_config(final_natural, previous)
            if runtime["card_system"] != previous["card_system"]:
                raise ValueError(f"{path.name}: Card System weights changed")
            runtime["excel_version"] = VERSION
            runtime["runtime_version"] = VERSION
            atomic_config(path, header, runtime)

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
