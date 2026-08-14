from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import re
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
SOURCE = PROJECT / "其他" / "參考資料" / "Super Ace_claude.txt"
CONFIG = PROJECT / "config_92.js"
WEIGHT_SCALE = Decimal("10000")

SYMBOL_IDS = {
    "C1": 2,
    "M1": 3,
    "M2": 4,
    "M3": 5,
    "M4": 6,
    "A": 7,
    "K": 8,
    "Q": 9,
    "J": 10,
}

SCENE_TABLE = {"BG": "bg_1", "FG": "fg_1"}
SCENE_TABLES = {
    "BG": ("bg_1", "bg_2", "bg_3", "bg_high", "bg_low", "buy"),
    "FG": (
        "fg_1", "fg_2", "fg_3", "fg_high_a", "fg_high_k", "fg_high_q",
        "fg_high_j", "fg_low", "super",
    ),
}
SCENE_MULTIPLIERS = {"BG": [1, 2, 3, 5], "FG": [2, 4, 6, 10]}
ACTIVE_SELECTION = {"base": "bg_1", "free": "fg_1", "retrigger": "fg_1"}
COMPETITOR_RANDOM_WILD_COUNTS = (1401, 235, 18)


def parse_source(path: Path = SOURCE) -> dict[str, dict[str, list[list[int]]]]:
    rows: dict[str, list[tuple[int, list[str], list[str]]]] = {"BG": [], "FG": []}
    scene: str | None = None
    reading_rows = False

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if line in ("[BG]", "[FG]"):
            scene = line[1:-1]
            reading_rows = False
            continue
        if line.startswith("["):
            scene = None
            reading_rows = False
            continue
        if scene and line.startswith("Pos"):
            reading_rows = True
            continue
        if not scene or not reading_rows or not line:
            continue

        parts = re.split(r"\s+", line)
        if len(parts) != 11:
            raise ValueError(f"{scene}: expected 11 columns, got {len(parts)}: {line}")
        position = int(parts[0])
        rows[scene].append((position, parts[1:6], parts[6:11]))

    parsed: dict[str, dict[str, list[list[int]]]] = {}
    for scene_name, scene_rows in rows.items():
        expected_positions = list(range(200))
        actual_positions = [row[0] for row in scene_rows]
        if actual_positions != expected_positions:
            raise ValueError(
                f"{scene_name}: positions must be exactly 0..199; got {actual_positions[:5]}..."
            )

        reels = [[] for _ in range(5)]
        weights = [[] for _ in range(5)]
        for _, symbol_cells, weight_cells in scene_rows:
            for reel, symbol in enumerate(symbol_cells):
                if symbol not in SYMBOL_IDS:
                    raise ValueError(f"{scene_name} R{reel + 1}: unsupported symbol {symbol!r}")
                reels[reel].append(SYMBOL_IDS[symbol])
            for reel, raw_weight in enumerate(weight_cells):
                scaled = Decimal(raw_weight) * WEIGHT_SCALE
                if scaled != scaled.to_integral_value() or scaled <= 0:
                    raise ValueError(
                        f"{scene_name} R{reel + 1}: weight {raw_weight!r} is not a positive 4dp value"
                    )
                weights[reel].append(int(scaled))

        for reel in range(5):
            if len(reels[reel]) != 200 or len(weights[reel]) != 200:
                raise ValueError(f"{scene_name} R{reel + 1}: reel/weight length must be 200")
            ratio = max(weights[reel]) / min(weights[reel])
            if ratio > 10 + 1e-12:
                raise ValueError(f"{scene_name} R{reel + 1}: positive stop ratio {ratio:.6f}x exceeds 10x")

        parsed[scene_name] = {"reels": reels, "weights": weights}
    return parsed


def load_config(path: Path = CONFIG) -> tuple[dict[str, Any], str, str]:
    text = path.read_text(encoding="utf-8-sig")
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Cannot find JSON payload in {path}")
    return json.loads(match.group(0)), text[: match.start()], text[match.end() :]


def apply_source(
    config: dict[str, Any],
    parsed: dict[str, dict[str, list[list[int]]]],
    bg_zero_weight: int,
) -> None:
    if bg_zero_weight < 0:
        raise ValueError("BG Random Wild zero weight must be non-negative")

    for scene, table_name in SCENE_TABLE.items():
        table = config["tables"][table_name]
        table["reels"] = copy.deepcopy(parsed[scene]["reels"])
        table["weights"] = copy.deepcopy(parsed[scene]["weights"])
        table["multipliers"] = copy.deepcopy(SCENE_MULTIPLIERS[scene])

    config["tables"]["bg_1"]["random_wild"] = {
        "values": [0, 2, 3, 4],
        "weights": [bg_zero_weight, *COMPETITOR_RANDOM_WILD_COUNTS],
    }
    config["tables"]["fg_1"]["random_wild"] = {
        "values": [0, 2, 3, 4],
        "weights": [1, 0, 0, 0],
    }
    for scene, source_table in SCENE_TABLE.items():
        for table_name in SCENE_TABLES[scene]:
            if table_name not in config["tables"]:
                raise ValueError(f"Missing config table {table_name}")
            config["tables"][table_name] = copy.deepcopy(config["tables"][source_table])

    for group, active_table in ACTIVE_SELECTION.items():
        selections = config.get("table_selection", {}).get(group)
        if not selections:
            raise ValueError(f"Missing table_selection.{group}")
        found = False
        for item in selections:
            active = str(item.get("table")) == active_table
            item["weight"] = 1 if active else 0
            found |= active
        if not found:
            raise ValueError(f"table_selection.{group} has no {active_table}")


def validate_applied(
    config: dict[str, Any], parsed: dict[str, dict[str, list[list[int]]]]
) -> None:
    for scene, table_name in SCENE_TABLE.items():
        table = config["tables"][table_name]
        if table["reels"] != parsed[scene]["reels"]:
            raise ValueError(f"{table_name}: reels do not exactly match {SOURCE.name}")
        if table["weights"] != parsed[scene]["weights"]:
            raise ValueError(f"{table_name}: stop weights do not exactly match scaled source")
        for reel, weights in enumerate(table["weights"], start=1):
            if not all(type(value) is int and value > 0 for value in weights):
                raise ValueError(f"{table_name} R{reel}: stop weights must be positive integers")
            if max(weights) / min(weights) > 10 + 1e-12:
                raise ValueError(f"{table_name} R{reel}: positive stop ratio exceeds 10x")

    for scene, source_table in SCENE_TABLE.items():
        expected = config["tables"][source_table]
        for table_name in SCENE_TABLES[scene]:
            if config["tables"][table_name] != expected:
                raise ValueError(f"{table_name}: must exactly match {source_table}")
            if config["tables"][table_name]["multipliers"] != SCENE_MULTIPLIERS[scene]:
                raise ValueError(f"{table_name}: multiplier sequence is incorrect")
    for group, active_table in ACTIVE_SELECTION.items():
        active = [
            str(item["table"])
            for item in config["table_selection"][group]
            if float(item["weight"]) > 0
        ]
        if active != [active_table]:
            raise ValueError(f"table_selection.{group}: expected only {active_table}, got {active}")


def summary(
    config: dict[str, Any], parsed: dict[str, dict[str, list[list[int]]]]
) -> dict[str, Any]:
    scenes: dict[str, Any] = {}
    for scene, table_name in SCENE_TABLE.items():
        table = config["tables"][table_name]
        scenes[scene] = {
            "table": table_name,
            "reel_lengths": [len(reel) for reel in table["reels"]],
            "weight_sums": [sum(weights) for weights in table["weights"]],
            "weight_ranges": [
                {
                    "min": min(weight for weight in weights if weight > 0),
                    "max": max(weights),
                    "ratio": round(
                        max(weights) / min(weight for weight in weights if weight > 0), 6
                    ),
                }
                for weights in table["weights"]
            ],
            "random_wild": table["random_wild"],
            "exact_source_match": table["reels"] == parsed[scene]["reels"]
            and table["weights"] == parsed[scene]["weights"],
        }
    return {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "weight_scale": int(WEIGHT_SCALE),
        "table_selection": config.get("table_selection", {}),
        "uniform_tables": {
            scene: list(table_names) for scene, table_names in SCENE_TABLES.items()
        },
        "scenes": scenes,
    }


def write_config(config: dict[str, Any], prefix: str, suffix: str, path: Path = CONFIG) -> None:
    payload = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(prefix + payload + suffix, encoding="utf-8")
    temporary.replace(path)


def simulate(config: dict[str, Any], rounds: int, threads: int) -> dict[str, Any]:
    module_name = "h016_simulator_for_claude_reels"
    environment = {
        "H016_BASE_DIR": str(PROJECT),
        "H016_CONFIG_FILE": CONFIG.name,
        "H016_RUN_ALL_COMBINATIONS": "false",
        "H016_CARD_SYSTEM_ENABLED": "false",
        "H016_OUTPUT_REPORT": "false",
        "H016_SHOW_CONSOLE_SUMMARY": "false",
        "H016_SHOW_CONSOLE_DETAIL": "false",
    }
    previous = {name: os.environ.get(name) for name in environment}
    previous_dont_write = sys.dont_write_bytecode
    os.environ.update(environment)
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location(module_name, PROJECT / "Simulator.py")
        if spec is None or spec.loader is None:
            raise RuntimeError("Cannot load Simulator.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        result = module.run_simulation(
            total_rounds=rounds,
            bet_mode=module.MODE_NORMALBET,
            bet_multi=1,
            threads=max(1, threads),
            config=config,
        )
        stats = result["stats"]
        bg_total = max(1, int(stats["rounds"]))
        fg_total = int(stats["fg_spins"])
        wager = float(stats["coin_in"])
        return {
            "rounds": int(stats["rounds"]),
            "fg_spins": fg_total,
            "fg_triggers": int(stats["fg_triggers"]),
            "fg_trigger_rate": int(stats["fg_triggers"]) / bg_total,
            "bg_w2_events": int(stats["bg_w2_events"]),
            "bg_w2_event_rate": int(stats["bg_w2_events"]) / bg_total,
            "bg_w2_counts": {
                str(count): int(stats["bg_w2_counts"][count]) for count in (2, 3, 4)
            },
            "fg_w2_events": int(stats["fg_w2_events"]),
            "fg_w2_event_rate": int(stats["fg_w2_events"]) / fg_total if fg_total else 0.0,
            "fg_w2_counts": {
                str(count): int(stats["fg_w2_counts"][count]) for count in (2, 3, 4)
            },
            "rtp_bg": float(stats["pay_bg"]) / wager if wager else 0.0,
            "rtp_fg": float(stats["pay_fg"]) / wager if wager else 0.0,
            "rtp_total": (float(stats["pay_bg"]) + float(stats["pay_fg"])) / wager if wager else 0.0,
            "duration_seconds": round(float(result["duration"]), 3),
        }
    finally:
        sys.modules.pop(module_name, None)
        sys.dont_write_bytecode = previous_dont_write
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply Super Ace_claude.txt BG/FG reels and integer stop weights to config_92.js"
    )
    parser.add_argument("--write", action="store_true", help="Atomically update config_92.js")
    parser.add_argument(
        "--bg-zero-weight",
        type=int,
        default=5600,
        help="Random Wild 0 weight; non-zero weights stay at competitor 1401/235/18",
    )
    parser.add_argument("--simulate-rounds", type=int, default=0)
    parser.add_argument("--threads", type=int, default=8)
    args = parser.parse_args()

    parsed = parse_source()
    config, prefix, suffix = load_config()
    apply_source(config, parsed, args.bg_zero_weight)
    validate_applied(config, parsed)
    if args.write:
        write_config(config, prefix, suffix)
    result = summary(config, parsed)
    if args.simulate_rounds > 0:
        result["simulation"] = simulate(config, args.simulate_rounds, args.threads)
    result["written"] = bool(args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
