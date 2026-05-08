from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

import xlsx_to_config as generator


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_XLSX = PROJECT_DIR / "Source" / "H026192.xlsx"
DEFAULT_CONFIG = PROJECT_DIR / "config.js"
DEFAULT_OUTPUT = PROJECT_DIR / "Tool" / "config_xlsx_weight_reel_check.md"

WEIGHT_SECTIONS = [
    ("weight_table_bg", "BG Table Selection Weight", "Parameter!J5:J7"),
    ("weight_table_fg", "FG Table Selection Weight", "Parameter!J12:J14"),
    ("weight_table_bf", "BF Table Selection Weight", "Parameter!J19:J21"),
    ("weight_multiple_special", "Multiple Selection Weight - Special Pool", "Parameter!O5:AA11"),
    ("weight_special_pool", "Used Special Pool Weight", "Parameter!AD5:AK11"),
    ("weight_multiple_r3_before", "Multiple Selection Weight - Reel3 Before Eliminate", "Parameter!O16:AA22"),
    ("weight_multiple_r3_after", "Multiple Selection Weight - Reel3 After Eliminate", "Parameter!O27:AA33"),
    ("weight_multiple_before", "Multiple Selection Weight - Before Eliminate", "Parameter!O38:AA44"),
    ("weight_multiple_after", "Multiple Selection Weight - After Eliminate", "Parameter!O49:AA55"),
    ("eliminate_table_weight_bg", "Eliminate Table Weight BG", "Parameter!J43:K43"),
    ("eliminate_table_weight_fg", "Eliminate Table Weight FG", "Parameter!J44:K44"),
    ("eliminate_table_weight_bf", "Eliminate Table Weight BF", "config keeps same value as FG"),
]

STRIP_SHEETS = [
    ("BG_Symbol", "B1"),
    ("BG_Symbol (2)", "B2"),
    ("BG_Symbol (3)", "B3"),
    ("FG_Symbol", "F1"),
    ("FG_Symbol (2)", "F2"),
    ("FG_Symbol (3)", "F3"),
    ("BF_Symbol", "BF"),
]


def load_config(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8").strip()
    if raw.startswith("window.") and "=" in raw:
        raw = raw.split("=", 1)[1].strip()
    if raw.endswith(";"):
        raw = raw[:-1].strip()
    return json.loads(raw)


def format_status(ok: bool) -> str:
    return "OK" if ok else "DIFF"


def matrix_to_md(matrix: list[list[int]], row_labels: list[str], col_labels: list[str]) -> str:
    lines = ["| Name | " + " | ".join(col_labels) + " |", "| --- | " + " | ".join(["---"] * len(col_labels)) + " |"]
    for label, row in zip(row_labels, matrix):
        lines.append("| " + label + " | " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def list_to_md(values: list[int], labels: list[str]) -> str:
    lines = ["| Name | Value |", "| --- | --- |"]
    for label, value in zip(labels, values):
        lines.append(f"| {label} | {value} |")
    return "\n".join(lines)


def block_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def serialize_rows(rows: list[list[int]], headers: list[str]) -> str:
    lines = [", ".join(headers)]
    for idx, row in enumerate(rows, start=1):
        lines.append(f"{idx}, " + ", ".join(str(item) for item in row))
    return "\n".join(lines)


def build_weight_section(config: dict[str, Any], generated: dict[str, Any]) -> str:
    parts: list[str] = ["## 權重設定對照", ""]
    multiplier_labels = [str(item) for item in config["value_multiplier_range"]]
    strip_labels = config["strip_name_map"]
    table_labels = ["B1", "B2", "B3"]
    fg_bf_labels = ["F1", "F2", "F3"]

    for key, title, source in WEIGHT_SECTIONS:
        cfg_value = config[key]
        gen_value = generated[key]
        ok = cfg_value == gen_value
        parts.append(f"### {title}")
        parts.append("")
        parts.append(f"- xlsx 來源：`{source}`")
        parts.append(f"- config 欄位：`{key}`")
        parts.append(f"- 比對結果：`{format_status(ok)}`")
        parts.append("")

        if key.startswith("weight_table_"):
            labels = table_labels if key == "weight_table_bg" else fg_bf_labels
            parts.append("**config.js**")
            parts.append("")
            parts.append(list_to_md(cfg_value, labels))
            parts.append("")
            parts.append("**xlsx 轉出結果**")
            parts.append("")
            parts.append(list_to_md(gen_value, labels))
            parts.append("")
            continue

        if key.startswith("eliminate_table_weight_"):
            labels = ["A", "B"]
            parts.append("**config.js**")
            parts.append("")
            parts.append(list_to_md(cfg_value, labels))
            parts.append("")
            parts.append("**xlsx 轉出結果**")
            parts.append("")
            parts.append(list_to_md(gen_value, labels))
            parts.append("")
            continue

        if key == "weight_special_pool":
            row_labels = [str(item) for item in range(1, len(cfg_value) + 1)]
            parts.append("**config.js**")
            parts.append("")
            parts.append(matrix_to_md(cfg_value, row_labels, strip_labels))
            parts.append("")
            parts.append("**xlsx 轉出結果**")
            parts.append("")
            parts.append(matrix_to_md(gen_value, row_labels, strip_labels))
            parts.append("")
            continue

        parts.append("**config.js**")
        parts.append("")
        parts.append(matrix_to_md(cfg_value, multiplier_labels, strip_labels))
        parts.append("")
        parts.append("**xlsx 轉出結果**")
        parts.append("")
        parts.append(matrix_to_md(gen_value, multiplier_labels, strip_labels))
        parts.append("")

    return "\n".join(parts)


def build_reel_section(config: dict[str, Any], generated: dict[str, Any]) -> str:
    parts: list[str] = ["## 輪帶與補牌設定對照", ""]
    for table_idx, (sheet_name, table_name) in enumerate(STRIP_SHEETS):
        parts.append(f"### {table_name} / {sheet_name}")
        parts.append("")
        parts.append("- `arr_reels` 來源：`Q:U`，從第 4 列開始讀到資料結束")
        parts.append("- `arr_reels_weight` 來源：`W:AA`，從第 4 列開始讀到資料結束")
        parts.append("- `drop_weight_a` 來源：`AD:AH`，固定讀 `30:49`")
        parts.append("- `drop_weight_b` 來源：`AK:AO`，固定讀 `30:49`")
        parts.append("")

        compare_rows = [
            ["arr_reels", format_status(config["arr_reels"][table_idx] == generated["arr_reels"][table_idx]), len(config["arr_reels"][table_idx])],
            ["arr_reels_weight", format_status(config["arr_reels_weight"][table_idx] == generated["arr_reels_weight"][table_idx]), len(config["arr_reels_weight"][table_idx])],
            ["drop_weight_a", format_status(config["drop_weight_a"][table_idx] == generated["drop_weight_a"][table_idx]), len(config["drop_weight_a"][table_idx])],
            ["drop_weight_b", format_status(config["drop_weight_b"][table_idx] == generated["drop_weight_b"][table_idx]), len(config["drop_weight_b"][table_idx])],
        ]
        parts.append(block_table(["Block", "Compare", "Row Count"], compare_rows))
        parts.append("")

        parts.append("**config.js / arr_reels**")
        parts.append("")
        parts.append("```text")
        parts.append(serialize_rows(config["arr_reels"][table_idx], ["idx", "R1", "R2", "R3", "R4", "R5"]))
        parts.append("```")
        parts.append("")

        parts.append("**config.js / arr_reels_weight**")
        parts.append("")
        parts.append("```text")
        parts.append(serialize_rows(config["arr_reels_weight"][table_idx], ["idx", "R1", "R2", "R3", "R4", "R5"]))
        parts.append("```")
        parts.append("")

        parts.append("**config.js / drop_weight_a**")
        parts.append("")
        parts.append("```text")
        parts.append(serialize_rows(config["drop_weight_a"][table_idx], ["idx", "R1", "R2", "R3", "R4", "R5"]))
        parts.append("```")
        parts.append("")

        parts.append("**config.js / drop_weight_b**")
        parts.append("")
        parts.append("```text")
        parts.append(serialize_rows(config["drop_weight_b"][table_idx], ["idx", "R1", "R2", "R3", "R4", "R5"]))
        parts.append("```")
        parts.append("")

    return "\n".join(parts)


def build_markdown(xlsx_path: Path, config_path: Path) -> str:
    config = load_config(config_path)
    template = generator.load_template(config_path)
    generated = generator.generate_config(xlsx_path, template)
    wb = load_workbook(xlsx_path, data_only=True, read_only=True)

    sections = [
        "# H026 權重與輪帶設定對照",
        "",
        f"- xlsx：`{xlsx_path.name}`",
        f"- config：`{config_path.name}`",
        f"- game_id：`{config['game_id']}`",
        f"- strip_name_map：`{', '.join(config['strip_name_map'])}`",
        f"- multiplier_range：`{config['value_multiplier_range']}`",
        "",
        "## 總結",
        "",
        f"- 權重區塊比對：`{format_status(all(config[key] == generated[key] for key, _title, _src in WEIGHT_SECTIONS))}`",
        f"- 輪帶 / 補牌區塊比對：`{format_status(all(config['arr_reels'][idx] == generated['arr_reels'][idx] and config['arr_reels_weight'][idx] == generated['arr_reels_weight'][idx] and config['drop_weight_a'][idx] == generated['drop_weight_a'][idx] and config['drop_weight_b'][idx] == generated['drop_weight_b'][idx] for idx in range(len(config['strip_name_map']))))}`",
        "",
        build_weight_section(config, generated),
        "",
        build_reel_section(config, generated),
        "",
        "## xlsx 主要來源提示",
        "",
        "- `Overview`：`game_id`、`default_coin_in`、`featurebuy`、`pay_table`",
        "- `Parameter`：`paylines`、所有 table selection weight、所有 multiplier weight、eliminate table weight",
        "- `BG_Symbol* / FG_Symbol* / BF_Symbol`：`arr_reels`、`arr_reels_weight`、`drop_weight_a`、`drop_weight_b`",
        "",
    ]
    _ = wb
    return "\n".join(sections)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export config.js and xlsx weight/reel mapping to markdown")
    parser.add_argument("--xlsx", default=str(DEFAULT_XLSX))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    xlsx_path = Path(args.xlsx).resolve()
    config_path = Path(args.config).resolve()
    output_path = Path(args.output).resolve()
    markdown = build_markdown(xlsx_path, config_path)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Exported {output_path.name}")


if __name__ == "__main__":
    main()
