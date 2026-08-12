"""Compare initial-window vertical symbol stacks between competitor and H027.

A stack is a maximal contiguous run of the same symbol within one five-cell
reel column. The distribution is cell-weighted: A,A,A,K,J contributes three
Stack-3 cells and two Stack-1 cells. Initial screens only are used because
this metric is intended to validate reel-strip ordering rather than cascade
drop behavior.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config_92A.js"
DEFAULT_INPUT = ROOT / "其他" / "參考資料" / "game_responses-gates of olympus 1000.xlsx"
DEFAULT_OUTPUT = ROOT / "其他" / "參考資料" / "stack_distribution_metrics.json"
ANALYZER_PATH = ROOT / "其他" / "analyze_gates_competitor.py"
SCENE_TABLES = {
    "BG": (("BG_Symbol", 1), ("BG_Symbol (2)", 1)),
    "FG": (("FG_Symbol", 8), ("FG_Symbol (2)", 7)),
}


def load_analyzer():
    spec = importlib.util.spec_from_file_location("h027_stack_competitor", ANALYZER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_config(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    match = re.fullmatch(r"\s*const\s+data\s*=\s*(\{.*\})\s*;?\s*", text, re.DOTALL)
    if not match:
        raise ValueError(f"Unsupported config format: {path}")
    return json.loads(match.group(1))


def add_column(column: list[int], weight: int, reel: int, totals, by_symbol, by_reel_symbol) -> None:
    start = 0
    while start < len(column):
        end = start + 1
        while end < len(column) and column[end] == column[start]:
            end += 1
        length = end - start
        cells = length * weight
        totals[reel][length] += cells
        by_symbol[column[start]][length] += cells
        by_reel_symbol[reel][column[start]][length] += cells
        start = end


def finalize(totals, by_symbol, by_reel_symbol, id_to_code: dict[int, str]) -> dict:
    by_reel = {}
    for reel, counts in enumerate(totals):
        denominator = sum(counts.values())
        by_reel[f"R{reel + 1}"] = {
            f"stack_{length}": counts[length] / denominator if denominator else 0.0
            for length in range(1, 6)
        }
    symbol_rows = {}
    for symbol_id, counts in sorted(by_symbol.items()):
        denominator = sum(counts.values())
        symbol_rows[id_to_code.get(symbol_id, str(symbol_id))] = {
            f"stack_{length}": counts[length] / denominator if denominator else 0.0
            for length in range(1, 6)
        }
    reel_symbol_rows = {}
    for reel, symbols in enumerate(by_reel_symbol):
        reel_symbol_rows[f"R{reel + 1}"] = {}
        for symbol_id, counts in sorted(symbols.items()):
            denominator = sum(counts.values())
            reel_symbol_rows[f"R{reel + 1}"][id_to_code.get(symbol_id, str(symbol_id))] = {
                f"stack_{length}": counts[length] / denominator if denominator else 0.0
                for length in range(1, 6)
            }
    return {"by_reel": by_reel, "by_symbol": symbol_rows, "by_reel_symbol": reel_symbol_rows}


def competitor_scene(spins, id_to_code: dict[int, str]) -> dict:
    totals = [Counter() for _ in range(6)]
    by_symbol = defaultdict(Counter)
    by_reel_symbol = [defaultdict(Counter) for _ in range(6)]
    screens = 0
    for spin in spins:
        if not spin.screens or len(spin.screens[0]) != 30:
            continue
        screen = spin.screens[0]
        screens += 1
        for reel in range(6):
            add_column(
                [screen[row * 6 + reel] for row in range(5)], 1, reel,
                totals, by_symbol, by_reel_symbol,
            )
    result = finalize(totals, by_symbol, by_reel_symbol, id_to_code)
    result["screen_count"] = screens
    result["cell_count"] = screens * 30
    return result


def h027_scene(config: dict, scene: str) -> dict:
    by_name = dict(zip(config["strip_names"], config["strips"]))
    id_to_code = dict(zip(config["symbol_ids"], config["symbol_codes"]))
    totals = [Counter() for _ in range(6)]
    by_symbol = defaultdict(Counter)
    by_reel_symbol = [defaultdict(Counter) for _ in range(6)]
    weighted_screens = 0
    for table_name, weight in SCENE_TABLES[scene]:
        strip = by_name[table_name]
        matrix = strip["symbols"]
        lengths = strip["reel_lengths"]
        for reel in range(6):
            length = int(lengths[reel])
            for start in range(length):
                column = [int(matrix[(start + row) % length][reel]) for row in range(5)]
                add_column(column, weight, reel, totals, by_symbol, by_reel_symbol)
        weighted_screens += weight * int(lengths[0])
    result = finalize(totals, by_symbol, by_reel_symbol, id_to_code)
    result["weighted_screen_count"] = weighted_screens
    result["weighted_cell_count"] = weighted_screens * 30
    return result


def analyze(config_path: Path, input_path: Path) -> dict:
    analyzer = load_analyzer()
    analysis = analyzer.analyze(input_path)
    sessions = analysis["_sessions"]
    bg_spins = [session.bg for session in sessions]
    fg_spins = [spin for session in sessions for spin in session.fg_spins]
    config = load_config(config_path)
    return {
        "definition": {
            "scope": "initial screen only",
            "grain": "cell-weighted maximal contiguous run within each five-cell reel column",
            "example": "A,A,A,K,J -> three Stack-3 cells and two Stack-1 cells",
        },
        "source": {"competitor": input_path.name, "h027": config_path.name},
        "competitor": {
            "BG": competitor_scene(bg_spins, analyzer.SYMBOL_ID_TO_CODE),
            "FG": competitor_scene(fg_spins, analyzer.SYMBOL_ID_TO_CODE),
        },
        "h027": {scene: h027_scene(config, scene) for scene in ("BG", "FG")},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    result = analyze(args.config.resolve(), args.input.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not args.no_write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Written: {args.output.resolve()}", file=sys.stderr)


if __name__ == "__main__":
    main()
