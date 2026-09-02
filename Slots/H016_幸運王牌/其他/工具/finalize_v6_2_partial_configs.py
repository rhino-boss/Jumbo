"""Finalize v6.2 BG/FG/BF configs while preserving v6.1 SF cards exactly."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[2]
FROZEN = PROJECT / "Versions" / "6.1"
VERSION = "6.2.0.1"


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


def main() -> None:
    natural = load_config(PROJECT / "config.js")
    summary: list[dict[str, Any]] = []
    for name in ("config_92A.js", "config_94A.js"):
        target_path = PROJECT / name
        target = load_config(target_path)
        frozen = load_config(FROZEN / name)
        for profile_name, profile in target["card_system"]["profiles"].items():
            profile["super_feature"] = copy.deepcopy(
                frozen["card_system"]["profiles"][profile_name]["super_feature"]
            )
        target["excel_version"] = VERSION
        target["runtime_version"] = VERSION

        if target["tables"] != natural["tables"]:
            raise ValueError(f"{name}: natural tables diverge from config.js")
        if target["table_selection"] != natural["table_selection"]:
            raise ValueError(f"{name}: table selection diverges from config.js")
        for profile_name, profile in target["card_system"]["profiles"].items():
            expected = frozen["card_system"]["profiles"][profile_name]["super_feature"]
            if profile["super_feature"] != expected:
                raise AssertionError(f"{name}/{profile_name}: SF cards changed")

        write_config(target_path, target)
        summary.append({"file": name, "version": VERSION, "sf": "v6.1 exact"})
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
