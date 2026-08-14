"""Sync H016194 runtime data that is defined by the current H0161.xlsx."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_js(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8-sig")
    return json.loads(raw[raw.find("{") : raw.rfind("}") + 1])


def main() -> None:
    source = load_js(ROOT / "config.js")
    target_path = ROOT / "config_94A.js"
    target = load_js(target_path)
    target["excel_version"] = "2.0.0.0"

    # Physical FG gold stops and per-table Random Wild values/weights come from
    # the current XLSX. Keep H016194's other stop/drop weights intact.
    for name, table in target["tables"].items():
        if name not in source["tables"]:
            continue
        table["random_wild"] = source["tables"][name]["random_wild"]
        if name.startswith("fg_") or name == "super":
            table["reels"] = source["tables"][name]["reels"]
    target["tables"]["buy"] = source["tables"]["buy"]
    target["card_system"] = {"enabled": False, "profiles": {}}

    payload = json.dumps(target, ensure_ascii=False, separators=(",", ":"))
    target_path.write_text(
        "// H016194 runtime config; XLSX-defined reels/RW synchronized from Source/H0161.xlsx.\n"
        f"window.H016_CONFIG={payload};\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
