"""Fill H027 config drop weights from Gates of Olympus 1000 observations.

The competitor's BG/FG drop screens are measured per reel.  Each reel is
quantized to an integer weight total of 1,000,000 using largest remainder.
Only config.js is changed; model_sync.py import writes it back to H0271.xlsx.
"""
import argparse
import importlib.util
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "Source"))
from model_sync import DEFAULT_CONFIG, load_js_config, write_js_config


DEFAULT_INPUT = PROJECT_DIR / "其他" / "參考資料" / "game_responses-gates of olympus 1000.xlsx"
ANALYZER_PATH = PROJECT_DIR / "其他" / "analyze_gates_competitor.py"
WEIGHT_TOTAL = 1_000_000


def load_analyzer():
    spec = importlib.util.spec_from_file_location("h027_competitor_analyzer", ANALYZER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def calibrate(config_path, input_path):
    analyzer = load_analyzer()
    analysis = analyzer.analyze(input_path)
    sessions = analysis["_sessions"]
    scenes = {
        "BG_Symbol": [session.bg for session in sessions],
        "FG_Symbol": [spin for session in sessions for spin in session.fg_spins],
    }
    config = load_js_config(config_path)
    strip_by_name = dict(zip(config["strip_names"], config["strips"]))
    symbol_codes = list(config["symbol_codes"])

    for strip_name, spins in scenes.items():
        probabilities = analyzer.reel_symbol_probabilities(spins, "drop")
        per_reel = [
            analyzer.largest_remainder_counts(reel_probabilities, WEIGHT_TOTAL)
            for reel_probabilities in probabilities
        ]
        matrix = [
            [int(per_reel[reel].get(code, 0)) for reel in range(6)]
            for code in symbol_codes
        ]
        if strip_name == "BG_Symbol" and "BG_Symbol (2)" in strip_by_name:
            first = strip_by_name["BG_Symbol"].get("drop_weights", matrix)
            second = strip_by_name["BG_Symbol (2)"].get("drop_weights", matrix)
            rebased_first, rebased_second = [], []
            for symbol_index, target_row in enumerate(matrix):
                first_row, second_row = [], []
                for reel, target in enumerate(target_row):
                    delta = int(round((first[symbol_index][reel] - second[symbol_index][reel]) / 2))
                    delta = max(-target, min(target, delta))
                    first_row.append(target + delta)
                    second_row.append(target - delta)
                rebased_first.append(first_row)
                rebased_second.append(second_row)
            strip_by_name["BG_Symbol"]["drop_weights"] = rebased_first
            strip_by_name["BG_Symbol (2)"]["drop_weights"] = rebased_second
        elif strip_name == "FG_Symbol" and "FG_Symbol (2)" in strip_by_name:
            first = strip_by_name["FG_Symbol"].get("drop_weights", matrix)
            second = strip_by_name["FG_Symbol (2)"].get("drop_weights", matrix)
            rebased_first, rebased_second = [], []
            for symbol_index, target_row in enumerate(matrix):
                first_row, second_row = [], []
                for reel, target in enumerate(target_row):
                    delta = int(round((first[symbol_index][reel] - second[symbol_index][reel]) / 15))
                    delta = max(-(target // 7), min(target // 8, delta))
                    first_row.append(target + 7 * delta)
                    second_row.append(target - 8 * delta)
                rebased_first.append(first_row)
                rebased_second.append(second_row)
            strip_by_name["FG_Symbol"]["drop_weights"] = rebased_first
            strip_by_name["FG_Symbol (2)"]["drop_weights"] = rebased_second
        else:
            strip_by_name[strip_name]["drop_weights"] = matrix
        totals = [sum(row[reel] for row in matrix) for reel in range(6)]
        if totals != [WEIGHT_TOTAL] * 6:
            raise ValueError(f"{strip_name} invalid drop-weight totals: {totals}")
        print(f"{strip_name}: drop-weight totals={totals}")

    write_js_config(config_path, config)
    print(f"Calibrated config written: {config_path}")


def main():
    parser = argparse.ArgumentParser(description="Calibrate H027 BG/FG drop weights from competitor responses")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    calibrate(args.config.resolve(), args.input.resolve())


if __name__ == "__main__":
    main()
