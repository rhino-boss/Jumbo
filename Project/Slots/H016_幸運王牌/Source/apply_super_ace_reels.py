from __future__ import annotations

import argparse
import bisect
import json
from collections import Counter
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


HERE = Path(__file__).resolve().parent
DEFAULT_TARGET = HERE / "H0161.xlsx"
DEFAULT_SOURCE = Path(
    "C:/Users/rhinshen/Mine/個人工作區/市場資訊/H5/遊戲資源/JILI/"
    "JILI - Super Ace/遊戲資料/StripTable_SuperAce_還原.xlsx"
)
TARGETS = {"BG_Symbol": "BG_Strip", "FG_Symbol": "FG_Strip"}
EDITABLE_COLUMNS = {*range(11, 16), *range(23, 28)}  # K:O and W:AA only
REEL_LENGTH = 200
GOLD_RATES = {
    "BG_Symbol": [0.0, 0.15024, 0.11346, 0.07600, 0.0],
    "FG_Symbol": [0.0, 0.21057, 0.18177, 0.15244, 0.0],
}
GOLD_SYMBOLS = {
    "M1": "G1", "M2": "G2", "M3": "G3", "M4": "G4",
    "A": "GA", "K": "GK", "Q": "GQ", "J": "GJ",
}


def stable_value(value: Any) -> Any:
    if hasattr(value, "text"):
        return (value.text, value.ref)
    return value


def protected_values(workbook) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for worksheet in workbook.worksheets:
        cells: dict[str, Any] = {}
        for row in worksheet.iter_rows():
            for cell in row:
                if worksheet.title in TARGETS and cell.column in EDITABLE_COLUMNS:
                    continue
                if cell.value is not None:
                    cells[cell.coordinate] = stable_value(cell.value)
        result[worksheet.title] = cells
    return result


def read_reels(worksheet) -> tuple[list[list[str]], list[list[float]]]:
    reels: list[list[str]] = [[] for _ in range(5)]
    weights: list[list[float]] = [[] for _ in range(5)]
    for row in worksheet.iter_rows(min_row=3, max_col=12, values_only=True):
        for reel in range(5):
            symbol = row[1 + reel]
            stop_weight = row[7 + reel]
            if symbol in (None, ""):
                continue
            weight = float(stop_weight)
            if weight <= 0:
                raise ValueError(f"{worksheet.title} R{reel + 1}: stop weight must be positive")
            reels[reel].append(str(symbol))
            weights[reel].append(weight)
    if any(not reel for reel in reels):
        raise ValueError(f"{worksheet.title}: all five reels must be non-empty")
    return reels, weights


def resample_to_200(symbols: list[str], weights: list[float]) -> list[str]:
    cumulative: list[float] = []
    running = 0.0
    for weight in weights:
        running += weight
        cumulative.append(running)
    return [
        symbols[min(bisect.bisect_left(cumulative, running * (index + 0.5) / REEL_LENGTH), len(symbols) - 1)]
        for index in range(REEL_LENGTH)
    ]


def proportional_gold_counts(symbols: list[str], total_gold: int) -> dict[str, int]:
    counts = Counter(symbol for symbol in symbols if symbol in GOLD_SYMBOLS)
    eligible = sum(counts.values())
    if total_gold > eligible:
        raise ValueError(f"gold target {total_gold} exceeds {eligible} eligible symbols")
    exact = {symbol: total_gold * count / eligible for symbol, count in counts.items()}
    allocated = {symbol: int(value) for symbol, value in exact.items()}
    remainder = total_gold - sum(allocated.values())
    order = sorted(counts, key=lambda symbol: (exact[symbol] - allocated[symbol], counts[symbol], symbol), reverse=True)
    for symbol in order[:remainder]:
        allocated[symbol] += 1
    return allocated


def evenly_spaced(items: list[int], count: int) -> list[int]:
    if count <= 0:
        return []
    return [items[min(int((index + 0.5) * len(items) / count), len(items) - 1)] for index in range(count)]


def apply_gold(symbols: list[str], rate: float) -> tuple[list[str], int]:
    result = list(symbols)
    target = round(REEL_LENGTH * rate)
    by_symbol: dict[str, list[int]] = {
        symbol: [index for index, value in enumerate(result) if value == symbol]
        for symbol in GOLD_SYMBOLS
    }
    for symbol, count in proportional_gold_counts(result, target).items():
        for index in evenly_spaced(by_symbol[symbol], count):
            result[index] = GOLD_SYMBOLS[symbol]
    return result, target


def write_reels(worksheet, reels: list[list[str]]) -> None:
    for row in range(4, 404):
        for column in EDITABLE_COLUMNS:
            worksheet.cell(row, column).value = None
    for reel, symbols in enumerate(reels):
        for row, symbol in enumerate(symbols, start=4):
            worksheet.cell(row, 11 + reel).value = symbol
            worksheet.cell(row, 23 + reel).value = 1


def update_workbook(target_path: Path, source_path: Path) -> dict[str, Any]:
    target = load_workbook(target_path, data_only=False)
    source = load_workbook(source_path, read_only=True, data_only=True)
    before = protected_values(target)
    result: dict[str, Any] = {}
    for target_name, source_name in TARGETS.items():
        source_reels, source_weights = read_reels(source[source_name])
        reels: list[list[str]] = []
        gold_counts: list[int] = []
        for reel in range(5):
            expanded = resample_to_200(source_reels[reel], source_weights[reel])
            expanded, gold_count = apply_gold(expanded, GOLD_RATES[target_name][reel])
            reels.append(expanded)
            gold_counts.append(gold_count)
        write_reels(target[target_name], reels)
        result[target_name] = {
            "reel_lengths": [len(reel) for reel in reels],
            "integer_weight_sums": [REEL_LENGTH] * 5,
            "gold_counts": gold_counts,
            "gold_rates": [count / REEL_LENGTH for count in gold_counts],
            "r1_has_gold": any(symbol in GOLD_SYMBOLS.values() for symbol in reels[0]),
            "r5_has_gold": any(symbol in GOLD_SYMBOLS.values() for symbol in reels[4]),
            "all_weights_are_positive_integers": True,
        }
    source.close()
    target.save(target_path)

    checked = load_workbook(target_path, data_only=False)
    checked_protected = protected_values(checked)
    if checked_protected != before:
        changed = sorted(name for name in before if checked_protected[name] != before[name])
        raise RuntimeError(f"Values outside K:O/W:AA changed: {changed}")
    result["protected_values_unchanged"] = True
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    result = update_workbook(args.target.resolve(), args.source.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
