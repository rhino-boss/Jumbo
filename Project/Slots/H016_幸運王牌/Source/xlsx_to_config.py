from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PROJECT_DIR = HERE.parent
DEFAULT_SOURCE = HERE / "H0161.xlsx"
DEFAULT_OUTPUT = PROJECT_DIR / "config_92.js"
FRONTEND_NAMES = {
    "0": "WW1", "1": "WW2", "2": "C1",
    "3": "M1", "4": "M2", "5": "M3", "6": "M4",
    "7": "A", "8": "K", "9": "Q", "10": "J",
    "11": "M1G", "12": "M2G", "13": "M3G", "14": "M4G",
    "15": "AG", "16": "KG", "17": "QG", "18": "JG",
}


def load_simulator_module():
    os.environ.setdefault("H016_BASE_DIR", str(PROJECT_DIR))
    os.environ.setdefault("H016_RUN_ALL_COMBINATIONS", "false")
    spec = importlib.util.spec_from_file_location("h016_simulator_for_config", PROJECT_DIR / "Simulator.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load Simulator.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def frontend_config(source: Path) -> dict[str, Any]:
    simulator = load_simulator_module()
    config = simulator._load_xlsx_config(source)
    config["name_en"] = "Lucky Ace"
    config["rtp_label"] = 92
    config["reel_num"] = 5
    config["window_size"] = 4
    config["max_ways"] = 1024
    config["symbol_names"] = FRONTEND_NAMES
    config["base_table_weights"] = {"high": 1, "low": 0}
    config["card_system"] = {"enabled": False, "profiles": {}}
    for table in config["tables"].values():
        normalized = []
        for reel in table["weights"]:
            if any(float(weight) != int(weight) for weight in reel):
                raise ValueError("H0161.xlsx contains a non-integer reel weight")
            normalized.append([int(weight) for weight in reel])
        table["weights"] = normalized
        normalized_drop = []
        for reel in table["drop_weights"]:
            if any(float(weight) != int(weight) for weight in reel):
                raise ValueError("H0161.xlsx contains a non-integer Symbol Drop Weight")
            normalized_drop.append([int(weight) for weight in reel])
        table["drop_weights"] = normalized_drop
        random_weights = table["random_wild"]["weights"]
        if any(float(weight) != int(weight) for weight in random_weights):
            raise ValueError("H0161.xlsx contains a non-integer Random Wild weight")
        table["random_wild"]["weights"] = [int(weight) for weight in random_weights]
    return config


def validate(config: dict[str, Any]) -> dict[str, Any]:
    tables = config["tables"]
    bg = tables["bg_high"]
    fg = tables["fg_high_a"]
    gold_ids = set(range(11, 19))

    def gold_counts(table: dict[str, Any]) -> list[int]:
        return [sum(symbol in gold_ids for symbol in reel) for reel in table["reels"]]

    for table in tables.values():
        if [len(reel) for reel in table["reels"]] != [200] * 5:
            raise ValueError("Every frontend reel must contain exactly 200 stops")
        if any(any(type(weight) is not int or weight <= 0 for weight in reel) for reel in table["weights"]):
            raise ValueError("Every frontend initial stop weight must be a positive integer")
        if any(any(type(weight) is not int or weight < 0 for weight in reel) for reel in table["drop_weights"]):
            raise ValueError("Every frontend Symbol Drop Weight must be a non-negative integer")
        if any(sum(reel) <= 0 for reel in table["drop_weights"]):
            raise ValueError("Every frontend Symbol Drop Weight reel must have a positive total")
    result = {
        "bg_lengths": [len(reel) for reel in bg["reels"]],
        "fg_lengths": [len(reel) for reel in fg["reels"]],
        "bg_gold_counts": gold_counts(bg),
        "fg_gold_counts": gold_counts(fg),
        "bg_random_wild": bg["random_wild"],
        "fg_random_wild": fg["random_wild"],
        "bg_drop_weight_sums": [sum(reel) for reel in bg["drop_weights"]],
        "fg_drop_weight_sums": [sum(reel) for reel in fg["drop_weights"]],
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronize H0161.xlsx to the index frontend config")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    config = frontend_config(source)
    result = validate(config)
    payload = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    output.write_text(
        "// Generated from Source/H0161.xlsx by Source/xlsx_to_config.py.\n"
        f"window.H016_CONFIG={payload};\n",
        encoding="utf-8",
    )
    result.update({"source": str(source), "output": str(output)})
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
