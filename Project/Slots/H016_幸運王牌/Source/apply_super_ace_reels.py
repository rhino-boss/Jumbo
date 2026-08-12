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
BASE_SYMBOLS = {gold: symbol for symbol, gold in GOLD_SYMBOLS.items()}
MIN_SC_GAP = 4
MAX_SYMBOL_STACK = 4


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


def base_symbol(symbol: str) -> str:
    return BASE_SYMBOLS.get(symbol, symbol)


def cyclic_runs(symbols: list[str]) -> list[list[int]]:
    """Return canonical-symbol runs, treating the reel as a closed loop."""
    size = len(symbols)
    canonical = [base_symbol(symbol) for symbol in symbols]
    if len(set(canonical)) == 1:
        return [list(range(size))]
    start = next(index for index in range(size) if canonical[index] != canonical[index - 1])
    runs: list[list[int]] = []
    current: list[int] = []
    current_symbol: str | None = None
    for offset in range(size):
        index = (start + offset) % size
        if canonical[index] != current_symbol:
            if current:
                runs.append(current)
            current = [index]
            current_symbol = canonical[index]
        else:
            current.append(index)
    if current:
        runs.append(current)
    return runs


def reel_constraint_state(symbols: list[str]) -> tuple[tuple[int, int, int], list[int]]:
    """Return a sortable penalty and positions that directly violate constraints."""
    size = len(symbols)
    scatter_positions = [index for index, symbol in enumerate(symbols) if symbol == "C1"]
    sc_penalty = 0
    violating: set[int] = set()
    if scatter_positions:
        for offset, left in enumerate(scatter_positions):
            right = scatter_positions[(offset + 1) % len(scatter_positions)]
            gap = (right - left - 1) % size
            if gap < MIN_SC_GAP:
                sc_penalty += MIN_SC_GAP - gap
                violating.add(right)

    stack_penalty = 0
    for run in cyclic_runs(symbols):
        if len(run) > MAX_SYMBOL_STACK:
            stack_penalty += len(run) - MAX_SYMBOL_STACK
            violating.update(run[MAX_SYMBOL_STACK:])

    return (sc_penalty + stack_penalty, sc_penalty, stack_penalty), sorted(violating)


def repair_reel_constraints(symbols: list[str]) -> tuple[list[str], list[tuple[int, int]]]:
    """Repair constraints with deterministic, minimum-penalty swaps within one reel."""
    result = list(symbols)
    swaps: list[tuple[int, int]] = []
    for _ in range(len(result) * 2):
        penalty, violating = reel_constraint_state(result)
        if penalty[0] == 0:
            return result, swaps

        best: tuple[tuple[int, int, int], int, int, int] | None = None
        for left in violating:
            for right in range(len(result)):
                if left == right or result[left] == result[right]:
                    continue
                result[left], result[right] = result[right], result[left]
                candidate_penalty, _ = reel_constraint_state(result)
                result[left], result[right] = result[right], result[left]
                if candidate_penalty >= penalty:
                    continue
                distance = min((right - left) % len(result), (left - right) % len(result))
                candidate = (candidate_penalty, distance, left, right)
                if best is None or candidate < best:
                    best = candidate

        if best is None:
            raise RuntimeError(f"Unable to repair reel constraints; remaining penalty={penalty}")
        _, _, left, right = best
        result[left], result[right] = result[right], result[left]
        swaps.append((left, right))

    raise RuntimeError("Reel constraint repair exceeded iteration limit")


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
        reel_swaps: list[int] = []
        for reel in range(5):
            expanded = resample_to_200(source_reels[reel], source_weights[reel])
            expanded, gold_count = apply_gold(expanded, GOLD_RATES[target_name][reel])
            expanded, swaps = repair_reel_constraints(expanded)
            reels.append(expanded)
            gold_counts.append(gold_count)
            reel_swaps.append(len(swaps))
        write_reels(target[target_name], reels)
        result[target_name] = {
            "reel_lengths": [len(reel) for reel in reels],
            "integer_weight_sums": [REEL_LENGTH] * 5,
            "gold_counts": gold_counts,
            "gold_rates": [count / REEL_LENGTH for count in gold_counts],
            "constraint_repair_swaps": reel_swaps,
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
