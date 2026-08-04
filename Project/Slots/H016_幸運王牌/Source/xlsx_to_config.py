"""Build H016 runtime data from the H016 PARsheet layout.

The source xlsx files remain authoritative.  This module is shared by
Simulator.py and the browser-config exporter so Python and index.html use the
same symbol tables and weights.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


SYMBOL_TO_ID = {
    "WW1": 0,
    "WW2": 1,
    "C1": 2,
    "M1": 3,
    "M2": 4,
    "M3": 5,
    "M4": 6,
    "A": 7,
    "K": 8,
    "Q": 9,
    "J": 10,
    "M1G": 11,
    "M2G": 12,
    "M3G": 13,
    "M4G": 14,
    "AG": 15,
    "KG": 16,
    "QG": 17,
    "JG": 18,
}
ID_TO_SYMBOL = {value: key for key, value in SYMBOL_TO_ID.items()}

TABLE_LAYOUT = {
    "bg_high": ("Base Game Symbol - High", 2),
    "bg_low": ("Base Game Symbol - Low", 9),
    "fg_high_a": ("Free Game Symbol - High - A", 16),
    "fg_high_k": ("Free Game Symbol - High - K", 16),
    "fg_high_q": ("Free Game Symbol - High - Q", 16),
    "fg_high_j": ("Free Game Symbol - High - J", 16),
    "fg_low": ("Free Game Symbol - Low", 23),
    "buy": ("Buy Feature Symbol", 30),
    "super": ("Super Free Game Symbol", 37),
}

CARD_SECTIONS = {
    "base_game": (5, 57),
    "free_game": (64, 115),
    "buy_feature": (129, 180),
    "super_feature": (194, 245),
}


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_multiplier(value: Any) -> int:
    text = str(value or "").strip().upper().replace("×", "X")
    if text.startswith("X"):
        text = text[1:]
    return int(float(text))


def _read_table(workbook, weight_sheet, sheet_name: str, weight_start_col: int) -> dict[str, Any]:
    sheet = workbook[sheet_name]
    reels: list[list[int]] = [[] for _ in range(5)]
    weights: list[list[float]] = [[] for _ in range(5)]

    # Symbol-table row 4 is line 0. Symbol Weight row 5 is the matching line 0.
    for offset in range(400):
        symbol_row = 4 + offset
        weight_row = 5 + offset
        for reel in range(5):
            raw_symbol = sheet.cell(symbol_row, 11 + reel).value
            symbol_name = str(raw_symbol or "").strip()
            if symbol_name not in SYMBOL_TO_ID:
                raise ValueError(
                    f"{sheet_name}!{sheet.cell(symbol_row, 11 + reel).coordinate}: "
                    f"unknown symbol {raw_symbol!r}"
                )
            reels[reel].append(SYMBOL_TO_ID[symbol_name])
            weights[reel].append(
                max(0.0, _number(weight_sheet.cell(weight_row, weight_start_col + reel).value))
            )

    random_wild_values: list[int] = []
    random_wild_weights: list[float] = []
    for row in range(3, 7):
        value = sheet.cell(row, 29).value  # AC
        weight = sheet.cell(row, 30).value  # AD
        if value is not None:
            random_wild_values.append(int(_number(value)))
            random_wild_weights.append(max(0.0, _number(weight)))

    multipliers = []
    for row in range(9, 13):
        value = sheet.cell(row, 29).value
        if value not in (None, ""):
            multipliers.append(_parse_multiplier(value))

    return {
        "reels": reels,
        "weights": weights,
        "random_wild": {
            "values": random_wild_values,
            "weights": random_wild_weights,
        },
        "multipliers": multipliers,
    }


def _read_free_game_mix(workbook) -> dict[str, Any]:
    sheet = workbook["Description"]
    choices: list[dict[str, Any]] = []
    for high_col, low_col, weight_col in ((3, 4, 5), (7, 8, 9)):
        for row in range(23, 29):
            weight = max(0.0, _number(sheet.cell(row, weight_col).value))
            if weight:
                choices.append(
                    {
                        "high": int(_number(sheet.cell(row, high_col).value)),
                        "low": int(_number(sheet.cell(row, low_col).value)),
                        "weight": weight,
                    }
                )

    high_variant_weights = [
        max(0.0, _number(sheet.cell(row, 5).value, 1.0)) for row in range(31, 35)
    ]
    if not any(high_variant_weights):
        high_variant_weights = [1.0, 1.0, 1.0, 1.0]

    return {
        "choices": choices or [{"high": 0, "low": 10, "weight": 1.0}],
        "high_variant_weights": high_variant_weights,
    }


def _read_paytable(workbook) -> dict[str, list[float]]:
    sheet = workbook["Overview"]
    pays: dict[str, list[float]] = {}
    # Rows 41..48 are M1, M2, M3, M4, A, K, Q, J. D/E/F are 3/4/5.
    for row in range(41, 49):
        name = str(sheet.cell(row, 1).value).strip()
        pays[str(SYMBOL_TO_ID[name])] = [
            _number(sheet.cell(row, 4).value) / 100.0,
            _number(sheet.cell(row, 5).value) / 100.0,
            _number(sheet.cell(row, 6).value) / 100.0,
        ]
    return pays


def _read_card_system(workbook) -> dict[str, Any]:
    sheet = workbook["Card"]
    profiles = {"weight_1": {}, "weight_2": {}, "weight_3": {}}
    for section, (first_row, last_row) in CARD_SECTIONS.items():
        for profile_index, weight_col in enumerate((28, 29, 30), start=1):
            cards = []
            for row in range(first_row, last_row + 1):
                lower = sheet.cell(row, 1).value
                upper = sheet.cell(row, 2).value
                table_code = str(sheet.cell(row, 17).value or "").strip()
                weight = max(0.0, _number(sheet.cell(row, weight_col).value))
                if not weight:
                    continue
                if str(lower).strip() == "FG Trigger":
                    cards.append(
                        {
                            "type": "free_game",
                            "table": table_code,
                            "weight": weight,
                        }
                    )
                else:
                    cards.append(
                        {
                            "type": "range",
                            "min": _number(lower, -1.0),
                            "max": _number(upper),
                            "table": table_code,
                            "weight": weight,
                        }
                    )
            profiles[f"weight_{profile_index}"][section] = cards
    return {
        "enabled": True,
        "default_profile": "weight_2",
        "profiles": profiles,
    }


def load_game_config(xlsx_path: str | Path) -> dict[str, Any]:
    path = Path(xlsx_path).resolve()
    # Normal mode is intentionally used here. The parser performs many indexed
    # cell lookups across nine sheets; read-only mode reparses rows repeatedly
    # and is dramatically slower for this access pattern.
    workbook = load_workbook(path, read_only=False, data_only=False)
    value_workbook = load_workbook(path, read_only=False, data_only=True)
    weight_sheet = workbook["Symbol Weight"]

    tables = {
        key: _read_table(workbook, weight_sheet, sheet_name, weight_col)
        for key, (sheet_name, weight_col) in TABLE_LAYOUT.items()
    }

    parsheet = path.stem
    rtp = 92 if "192" in parsheet else 94 if "194" in parsheet else None
    return {
        "game_id": "H016",
        "parsheet_id": parsheet,
        "name_zh": "幸運王牌",
        "name_en": "Lucky Ace",
        "rtp_label": rtp,
        "reel_num": 5,
        "window_size": 4,
        "max_ways": 1024,
        "symbol_names": {str(key): value for key, value in ID_TO_SYMBOL.items()},
        "pays": _read_paytable(workbook),
        "tables": tables,
        "base_table_weights": {"high": 1.0, "low": 0.0},
        # Weight 2/3 cells on Card are formulas, so use Excel's cached values.
        "card_system": _read_card_system(value_workbook),
        "free_game_mix": _read_free_game_mix(workbook),
        "free_spins": 10,
        "retrigger_spins": 5,
        "free_spin_cap": 50,
        "buy_price": 40.5,
        "super_buy_price": 250.0,
        "source_xlsx": path.name,
    }


def write_js(config: dict[str, Any], output_path: str | Path) -> Path:
    output = Path(output_path)
    payload = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    output.write_text(
        "/* Generated from the H016 source xlsx. Do not edit by hand. */\n"
        f"window.H016_CONFIG={payload};\n",
        encoding="utf-8",
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate H016 browser config from H016 xlsx")
    parser.add_argument("xlsx", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    config = load_game_config(args.xlsx)
    output = write_js(config, args.output)
    print(f"Generated {output} from {args.xlsx}")


if __name__ == "__main__":
    main()
