"""Synchronize H016 SF physical reels, stop weights, and selections from FG."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[2]
CONFIG = PROJECT / "config.js"


def load_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8-sig")
    prefix = "window.H016_CONFIG="
    start = text.index(prefix) + len(prefix)
    return json.loads(text[start:text.rindex(";")])


def write_config(path: Path, config: dict[str, Any]) -> None:
    payload = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    path.write_text(
        "// Generated from Source/H0161.xlsx by 其他/工具/xlsx_to_config.py.\n"
        f"window.H016_CONFIG={payload};\n",
        encoding="utf-8",
    )


def selection_weights(config: dict[str, Any], group: str) -> list[int]:
    return [int(item["weight"]) for item in config["table_selection"][group]]


def main() -> None:
    before = load_config(CONFIG)
    after = copy.deepcopy(before)

    for index in range(1, 4):
        after["tables"][f"sf_{index}"]["reels"] = copy.deepcopy(
            before["tables"][f"fg_{index}"]["reels"]
        )
        after["tables"][f"sf_{index}"]["weights"] = copy.deepcopy(
            before["tables"][f"fg_{index}"]["weights"]
        )
    # Legacy Super alias follows SF_Symbol (sf_1), but all non-reel parameters
    # stay untouched as requested.
    after["tables"]["super"]["reels"] = copy.deepcopy(
        after["tables"]["sf_1"]["reels"]
    )
    after["tables"]["super"]["weights"] = copy.deepcopy(
        after["tables"]["sf_1"]["weights"]
    )

    for source_group, target_group in (
        ("free", "super_free"),
        ("retrigger", "super_retrigger"),
    ):
        source = before["table_selection"][source_group]
        target = after["table_selection"][target_group]
        if len(source) != 3 or len(target) != 3:
            raise ValueError("FG/SF table selections must contain exactly three tables")
        for source_item, target_item in zip(source, target):
            target_item["weight"] = int(source_item["weight"])

    after["excel_version"] = "6"

    # Enforce the requested scope: SF reels, Super alias reels, SF selection,
    # and the unchanged base-version marker are the only permitted differences.
    expected = copy.deepcopy(before)
    for index in range(1, 4):
        expected["tables"][f"sf_{index}"]["reels"] = copy.deepcopy(
            before["tables"][f"fg_{index}"]["reels"]
        )
        expected["tables"][f"sf_{index}"]["weights"] = copy.deepcopy(
            before["tables"][f"fg_{index}"]["weights"]
        )
    expected["tables"]["super"]["reels"] = copy.deepcopy(
        expected["tables"]["sf_1"]["reels"]
    )
    expected["tables"]["super"]["weights"] = copy.deepcopy(
        expected["tables"]["sf_1"]["weights"]
    )
    expected["table_selection"]["super_free"] = copy.deepcopy(
        after["table_selection"]["super_free"]
    )
    expected["table_selection"]["super_retrigger"] = copy.deepcopy(
        after["table_selection"]["super_retrigger"]
    )
    expected["excel_version"] = "6"
    if after != expected:
        raise AssertionError("Unexpected config changes outside the approved SF scope")

    write_config(CONFIG, after)
    print(json.dumps({
        "config": str(CONFIG),
        "version": after["excel_version"],
        "sf_reels_match_fg": {
            f"sf_{index}": after["tables"][f"sf_{index}"]["reels"]
            == after["tables"][f"fg_{index}"]["reels"]
            for index in range(1, 4)
        },
        "super_free": selection_weights(after, "super_free"),
        "super_retrigger": selection_weights(after, "super_retrigger"),
        "sf_stop_weights_match_fg": all(
            after["tables"][f"sf_{index}"]["weights"]
            == after["tables"][f"fg_{index}"]["weights"]
            for index in range(1, 4)
        ),
        "sf_drop_weights_unchanged": all(
            after["tables"][f"sf_{index}"]["drop_weights"]
            == before["tables"][f"sf_{index}"]["drop_weights"]
            for index in range(1, 4)
        ),
        "sf_random_wild_unchanged": all(
            after["tables"][f"sf_{index}"]["random_wild"]
            == before["tables"][f"sf_{index}"]["random_wild"]
            for index in range(1, 4)
        ),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
