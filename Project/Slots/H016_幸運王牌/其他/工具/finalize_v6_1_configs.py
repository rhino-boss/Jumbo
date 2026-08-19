"""Finalize v6.1 RTP configs while preserving frozen v6 SF cards exactly."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[2]
FROZEN = PROJECT / "Versions" / "6.0"
VERSION = "6.1.0.0"


def load_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    prefix = "window.H016_CONFIG="
    start = text.index(prefix) + len(prefix)
    end = text.rindex(";")
    return json.loads(text[start:end])


def write_config(path: Path, config: dict[str, Any]) -> None:
    payload = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    path.write_text(
        "// Generated from Source/H0161.xlsx by 其他/工具/xlsx_to_config.py.\n"
        f"window.H016_CONFIG={payload};\n",
        encoding="utf-8",
    )


def main() -> None:
    base = load_config(PROJECT / "config.js")
    summaries: list[dict[str, Any]] = []
    for name in ("config_92A.js", "config_94A.js"):
        target_path = PROJECT / name
        frozen_path = FROZEN / name
        target = load_config(target_path)
        frozen = load_config(frozen_path)

        for profile_name, profile in target["card_system"]["profiles"].items():
            frozen_profile = frozen["card_system"]["profiles"][profile_name]
            profile["super_feature"] = copy.deepcopy(frozen_profile["super_feature"])

        target["excel_version"] = VERSION
        target["runtime_version"] = VERSION

        if target["tables"] != base["tables"]:
            raise ValueError(f"{name}: natural tables diverge from config.js")
        if target["table_selection"] != base["table_selection"]:
            raise ValueError(f"{name}: table selection diverges from config.js")
        for profile_name, profile in target["card_system"]["profiles"].items():
            frozen_sf = frozen["card_system"]["profiles"][profile_name]["super_feature"]
            if profile["super_feature"] != frozen_sf:
                raise AssertionError(f"{name} {profile_name}: SF cards changed")

        write_config(target_path, target)
        summaries.append({
            "file": name,
            "version": VERSION,
            "profiles": {
                profile_name: {
                    section: sum(int(card["weight"]) for card in profile[section])
                    for section in ("base_game", "free_game", "buy_feature", "super_feature")
                }
                for profile_name, profile in target["card_system"]["profiles"].items()
            },
        })
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
