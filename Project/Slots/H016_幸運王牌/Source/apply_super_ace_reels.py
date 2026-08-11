from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


HERE = Path(__file__).resolve().parent
DEFAULT_TARGET = HERE / "H0161.xlsx"
DEFAULT_SOURCE = Path(
    "C:/Users/rhinshen/Mine/個人工作區/市場資訊/H5/遊戲資源/JILI/"
    "JILI - Super Ace/遊戲資料/StripTable_SuperAce_還原.xlsx"
)
EDITABLE_SHEETS = {"BG_Symbol", "FG_Symbol"}
SYMBOL_ORDER = ["C1", "M1", "M2", "M3", "M4", "A", "K", "Q", "J"]


def cell_value(value: Any) -> Any:
    if hasattr(value, "text"):
        return {"array_formula": value.text, "ref": value.ref}
    return value


def sheet_fingerprint(worksheet) -> str:
    payload_object = {
        "populated_cells": [
            (cell.coordinate, cell_value(cell.value), cell.number_format)
            for row in worksheet.iter_rows()
            for cell in row
            if cell.value is not None
        ],
        "merged": sorted(str(item) for item in worksheet.merged_cells.ranges),
    }
    payload = json.dumps(payload_object, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def read_strip(source, sheet_name: str) -> tuple[list[list[str]], list[list[float]]]:
    worksheet = source[sheet_name]
    reels: list[list[str]] = [[] for _ in range(5)]
    stop_weights: list[list[float]] = [[] for _ in range(5)]
    for row in worksheet.iter_rows(min_row=3, max_col=12, values_only=True):
        for reel in range(5):
            symbol = row[1 + reel]
            weight = row[7 + reel]
            if symbol not in (None, ""):
                reels[reel].append(str(symbol))
                stop_weights[reel].append(float(weight))
    if any(not reel for reel in reels):
        raise ValueError(f"{sheet_name}: all five reels must be non-empty")
    if any(len(reels[i]) != len(stop_weights[i]) for i in range(5)):
        raise ValueError(f"{sheet_name}: symbol/stop-weight lengths differ")
    return reels, stop_weights


def read_fill_weights(source, scene: str) -> dict[str, list[float]]:
    worksheet = source["FillWeight"]
    result: dict[str, list[float]] = {}
    for row in worksheet.iter_rows(min_row=3, values_only=True):
        if row[0] != scene:
            continue
        result[str(row[1])] = [float(row[index]) for index in (4, 6, 8, 10, 12)]
    missing = set(SYMBOL_ORDER).difference(result)
    if missing:
        raise ValueError(f"FillWeight {scene}: missing {sorted(missing)}")
    return result


def read_gold_overlay(source, scene: str) -> tuple[list[float], list[float]]:
    worksheet = source["GoldOverlay"]
    total = [0.0] * 5
    big = [0.0] * 5
    for row in worksheet.iter_rows(min_row=3, max_row=12, values_only=True):
        if row[0] != scene:
            continue
        reel = int(str(row[1])[1:]) - 1
        total[reel] = float(row[2]) / 100.0
        big[reel] = float(row[4]) / 100.0
    return total, big


def write_sheet(
    worksheet,
    reels: list[list[str]],
    stop_weights: list[list[float]],
    fill_weights: dict[str, list[float]],
    gold_total: list[float],
    gold_big: list[float],
    scene: str,
) -> None:
    # Existing reel-strip area: K:O; aligned stop weights: W:AA.
    for row in range(4, 404):
        for column in (*range(11, 16), *range(23, 28)):
            worksheet.cell(row, column).value = None
    for reel in range(5):
        for offset, (symbol, weight) in enumerate(zip(reels[reel], stop_weights[reel]), start=4):
            worksheet.cell(offset, 11 + reel).value = symbol
            worksheet.cell(offset, 23 + reel).value = weight

    # Big Joker output: source Joker + 2/3/4 copies = observed totals 3/4/5.
    random_values = [0, 2, 3, 4]
    random_weights = [37_731, 1_401, 235, 18] if scene == "BG" else [1, 0, 0, 0]
    for row in range(4, 8):
        worksheet.cell(row, 29).value = random_values[row - 4]
        worksheet.cell(row, 30).value = random_weights[row - 4]

    # Additional evidence stays inside the only user-authorized worksheet.
    worksheet["AF2"] = "Cascade Fill Symbol Weight (%)"
    worksheet["AF3"] = "Symbol"
    for reel in range(5):
        worksheet.cell(3, 33 + reel).value = f"R{reel + 1}"
    for offset, symbol in enumerate(SYMBOL_ORDER, start=4):
        worksheet.cell(offset, 32).value = symbol
        for reel, weight in enumerate(fill_weights[symbol]):
            worksheet.cell(offset, 33 + reel).value = weight

    worksheet["AM2"] = "Golden Card Overlay Probability"
    worksheet["AM3"] = "Type"
    for reel in range(5):
        worksheet.cell(3, 40 + reel).value = f"R{reel + 1}"
    worksheet["AM4"] = "All Gold"
    worksheet["AM5"] = "Big Gold"
    for reel in range(5):
        worksheet.cell(4, 40 + reel).value = gold_total[reel]
        worksheet.cell(5, 40 + reel).value = gold_big[reel]

    worksheet["AT2"] = "Two-Scatter Suppression"
    worksheet["AT3"] = "Probability"
    worksheet["AU3"] = 0.371 if scene == "BG" else 0.0
    worksheet["AT5"] = "Source"
    worksheet["AU5"] = "StripTable_SuperAce_還原.xlsx"
    worksheet.column_dimensions["AF"].width = 28
    worksheet.column_dimensions["AM"].width = 32
    worksheet.column_dimensions["AT"].width = 28
    worksheet.column_dimensions["AU"].width = 34


def update_workbook(target_path: Path, source_path: Path) -> dict[str, Any]:
    target = load_workbook(target_path)
    source = load_workbook(source_path, read_only=True, data_only=True)
    protected_before = {
        name: sheet_fingerprint(target[name]) for name in target.sheetnames if name not in EDITABLE_SHEETS
    }
    results: dict[str, Any] = {}
    for scene, target_sheet, source_sheet in (
        ("BG", "BG_Symbol", "BG_Strip"),
        ("FG", "FG_Symbol", "FG_Strip"),
    ):
        reels, stop_weights = read_strip(source, source_sheet)
        fill_weights = read_fill_weights(source, scene)
        gold_total, gold_big = read_gold_overlay(source, scene)
        write_sheet(target[target_sheet], reels, stop_weights, fill_weights, gold_total, gold_big, scene)
        results[scene] = {
            "reel_lengths": [len(reel) for reel in reels],
            "stop_weight_sums": [sum(weights) for weights in stop_weights],
            "gold_total": gold_total,
            "gold_big": gold_big,
        }
    target.calculation.fullCalcOnLoad = True
    target.calculation.forceFullCalc = True
    target.calculation.calcMode = "auto"
    target.save(target_path)

    checked = load_workbook(target_path, data_only=False)
    protected_after = {
        name: sheet_fingerprint(checked[name]) for name in checked.sheetnames if name not in EDITABLE_SHEETS
    }
    if protected_before != protected_after:
        changed = sorted(name for name in protected_before if protected_before[name] != protected_after.get(name))
        raise RuntimeError(f"Unauthorized worksheet changes detected: {changed}")
    results["protected_sheets_unchanged"] = True
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    result = update_workbook(args.target.resolve(), args.source.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
