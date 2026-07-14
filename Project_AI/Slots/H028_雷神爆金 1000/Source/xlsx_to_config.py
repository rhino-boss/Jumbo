import argparse
import json
from pathlib import Path

from openpyxl import load_workbook


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE = BASE_DIR / "H028192A.xlsx"
DEFAULT_OUTPUT = BASE_DIR.parent / "config_92.js"

METADATA = {
    "game_id": "101016",
    "parsheet_id": "H0281",
    "display_name": "Thunder Boost 1000",
    "game_name_zh": "雷神爆金1000",
    "excel_version": "1.0.0.1",
    "default_coin_in": 100,
    "mode_normalbet": 0,
    "mode_extrabet": 1,
    "mode_featurebuy": 2,
    "normalbet": 1,
    "featurebuy": 75,
    "supported_bet_modes": [0, 2],
}


def extract_transposed(sheet, range_text):
    rows = [[cell.value for cell in row] for row in sheet[range_text]]
    columns = [list(column) for column in zip(*rows)]
    if len(columns) == 1:
        return columns[0]
    return columns


def extract_no_transpose(sheet, range_text):
    return [[cell.value for cell in row] for row in sheet[range_text]]


def get_sheet(workbook, *names):
    for name in names:
        if name in workbook.sheetnames:
            return workbook[name]
    raise KeyError(f"Worksheet not found; tried {names}. Available: {workbook.sheetnames}")


def build_config(source_path):
    workbook = load_workbook(source_path, read_only=True, data_only=True)
    output = dict(METADATA)

    overview = workbook["Overview"]
    output["linkpoint"] = extract_no_transpose(overview, "C32:F42")

    base = get_sheet(workbook, "Base Game Symbol", "BG_Symbol")
    base_ranges = {
        "BaseGameSymbol1": "T4:Z124",
        "BaseGameSymbolWeight1": "AB4:AH124",
        "BaseGameMegaWay1": "B33:G47",
        "BaseGameMY1": "B50:B62",
        "BaseGame1PostC1": "A65:B72",
        "BaseGameSymbol2": "BM4:BS124",
        "BaseGameSymbolWeight2": "BU4:CA124",
        "BaseGameMegaWay2": "AU33:AZ47",
        "BaseGameMY2": "AU50:AU62",
        "BaseGame2PostC1": "AT65:AU72",
    }
    for drop_index, first_row in enumerate((5, 34, 63, 92, 121), start=1):
        base_ranges[f"BaseGame1Drop{drop_index}"] = f"AK{first_row}:AQ{first_row + 25}"
        base_ranges[f"BaseGame2Drop{drop_index}"] = f"CD{first_row}:CJ{first_row + 25}"
    for key, range_text in base_ranges.items():
        output[key] = extract_transposed(base, range_text)

    description = workbook["Description"]
    output["ReelWeight"] = extract_transposed(description, "D5:D6")
    output["FreeReelWeight"] = extract_transposed(description, "G5:G7")
    output["FreeTriggerReel"] = extract_transposed(description, "D18:D20")

    free = get_sheet(workbook, "Free Game Symbol", "FG_Symbol")
    free_ranges = {
        "FreeGameSymbol1": "T4:Z124",
        "FreeGameSymbolWeight1": "AB4:AH124",
        "FreeGameMegaWay1": "B33:G47",
        "FreeGameMY1": "B50:B62",
        "FreeGame1PostC1": "A65:B72",
        "FreeGameSymbol2": "BM4:BS124",
        "FreeGameSymbolWeight2": "BU4:CA124",
        "FreeGameMegaWay2": "AU33:AZ47",
        "FreeGameMY2": "AU50:AU62",
        "FreeGame2PostC1": "AU65:AU72",
        "FreeGameSymbol3": "DF4:DL124",
        "FreeGameSymbolWeight3": "DN4:DT124",
        "FreeGameMegaWay3": "CN33:CS47",
        "FreeGameMY3": "CN50:CN62",
        "FreeGame3PostC1": "CM65:CN72",
    }
    for drop_index, first_row in enumerate((5, 34, 63, 92, 121), start=1):
        free_ranges[f"FreeGame1Drop{drop_index}"] = f"AK{first_row}:AQ{first_row + 25}"
        free_ranges[f"FreeGame2Drop{drop_index}"] = f"CD{first_row}:CJ{first_row + 25}"
        free_ranges[f"FreeGame3Drop{drop_index}"] = f"DW{first_row}:EC{first_row + 25}"
    for key, range_text in free_ranges.items():
        output[key] = extract_transposed(free, range_text)

    workbook.close()
    return output


def load_js_config(path):
    text = path.read_text(encoding="utf-8").strip()
    if not text.startswith("const data = "):
        raise ValueError(f"Unsupported config header: {path}")
    return json.loads(text[len("const data = ") :].rstrip(";"))


def write_js_config(path, data):
    path.write_text(
        "const data = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description="Build H028 config_92.js from H028192A.xlsx")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="Compare generated data with the existing output")
    args = parser.parse_args()

    generated = build_config(args.source)
    if args.check:
        current = load_js_config(args.output)
        changed_keys = [key for key in generated if generated[key] != current.get(key)]
        extra_keys = [key for key in current if key not in generated]
        if changed_keys or extra_keys:
            print(f"Config mismatch. Changed keys: {changed_keys}; extra keys: {extra_keys}")
            raise SystemExit(1)
        print(f"Config is current: {args.output}")
        return

    write_js_config(args.output, generated)
    print(f"Config written: {args.output}")


if __name__ == "__main__":
    main()
