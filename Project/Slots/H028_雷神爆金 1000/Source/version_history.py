#!/usr/bin/env python3
"""Archive H028 math configs, bump their version, and record math changes."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path

import model_sync


SOURCE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SOURCE_DIR.parent
VERSIONS_DIR = PROJECT_DIR / "Versions"
MANIFEST_JSON = VERSIONS_DIR / "version_manifest.json"
MANIFEST_JS = VERSIONS_DIR / "version_manifest.js"
TARGETS = {
    "92A": (SOURCE_DIR / "H028192A.xlsx", PROJECT_DIR / "config_92A.js"),
    "94A": (SOURCE_DIR / "H028194A.xlsx", PROJECT_DIR / "config_94A.js"),
}


def parse_version(value: str) -> tuple[int, int]:
    parts = value.strip().split(".")
    if len(parts) not in (2, 4) or any(not part.isdigit() for part in parts):
        raise ValueError(f"版本必須是兩碼格式，例如 2.0：{value!r}")
    return int(parts[0]), int(parts[1])


def next_version(current: str, change_type: str) -> str:
    major, minor = parse_version(current)
    if change_type == "main":
        return f"{major + 1}.0"
    return f"{major}.{minor + 1}"


def load_manifest() -> dict:
    return json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))


def version_key(value: str) -> tuple[int, int]:
    return parse_version(value)


def write_manifest(manifest: dict) -> None:
    manifest["versions"].sort(key=lambda item: version_key(item["version"]), reverse=True)
    text = json.dumps(manifest, ensure_ascii=False, indent=2)
    MANIFEST_JSON.write_text(text + "\n", encoding="utf-8")
    MANIFEST_JS.write_text(
        "window.H028_VERSION_MANIFEST = " + text + ";\n",
        encoding="utf-8",
    )


def manifest_entry(manifest: dict, version: str) -> dict | None:
    return next((item for item in manifest["versions"] if item["version"] == version), None)


def archive_config(config_code: str, config_path: Path, version: str, manifest: dict) -> None:
    destination = VERSIONS_DIR / version / config_path.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.read_bytes() != config_path.read_bytes():
        raise ValueError(f"歷史版本已存在但內容不同，拒絕覆寫：{destination}")
    if not destination.exists():
        shutil.copy2(config_path, destination)
    entry = manifest_entry(manifest, version)
    if entry is None:
        entry = {"version": version, "date": dt.date.today().isoformat(), "configs": {}, "changes": []}
        manifest["versions"].append(entry)
    entry.setdefault("configs", {})[config_code] = destination.relative_to(PROJECT_DIR).as_posix()


def config_differences(workbook_path: Path, config_path: Path) -> tuple[bool, bool]:
    generated = model_sync.build_config(workbook_path)
    current = model_sync.load_js_config(config_path)
    ignored = {"excel_version", "card_system"}
    shared_keys = (set(generated) | set(current)) - ignored
    main_changed = any(generated.get(key) != current.get(key) for key in shared_keys)
    weights_changed = generated.get("card_system") != current.get("card_system")
    return main_changed, weights_changed


def update_workbook_version(workbook_path: Path, version: str) -> None:
    updates: dict = {}
    model_sync.add_update(updates, "Overview", "B3", version, "excel_version")
    model_sync.write_patched_workbook(
        workbook_path,
        workbook_path,
        updates,
        force=True,
        preserve_formula_cache=True,
    )


def selected_targets(change_type: str, config_code: str) -> list[str]:
    if change_type == "main":
        return ["92A", "94A"]
    if config_code == "all":
        return ["92A", "94A"]
    return [config_code]


def run(change_type: str, config_code: str, message: str) -> str:
    message = message.strip()
    if not message:
        raise ValueError("數學調整必須填寫版本更動內容。")
    selected = selected_targets(change_type, config_code)
    differences = {
        code: config_differences(*TARGETS[code])
        for code in selected
    }
    if change_type == "main":
        if not any(main for main, _ in differences.values()):
            raise ValueError("沒有偵測到 H0281 共用數學參數變更，不應增加第一碼。")
    else:
        if any(main for main, _ in differences.values()):
            raise ValueError("偵測到 H0281 共用參數變更，請改選『主要參數』升第一碼。")
        selected = [code for code in selected if differences[code][1]]
        if not selected:
            raise ValueError("沒有偵測到倍率權重變更，不需建立新版本。")

    current_versions = {
        code: str(model_sync.load_js_config(TARGETS[code][1])["excel_version"])
        for code in selected
    }
    base_version = max(current_versions.values(), key=version_key)
    new_version = next_version(base_version, change_type)
    manifest = load_manifest()

    for code in selected:
        workbook_path, config_path = TARGETS[code]
        archive_config(code, config_path, current_versions[code], manifest)
        update_workbook_version(workbook_path, new_version)
        generated = model_sync.build_config(workbook_path)
        model_sync.write_js_config(config_path, generated)
        model_sync.verify_output(workbook_path, generated)

    entry = manifest_entry(manifest, new_version)
    if entry is None:
        entry = {
            "version": new_version,
            "date": dt.date.today().isoformat(),
            "configs": {},
            "changes": [],
        }
        manifest["versions"].append(entry)
    entry["date"] = dt.date.today().isoformat()
    entry.setdefault("changes", []).append(message)
    for code in selected:
        _, config_path = TARGETS[code]
        snapshot = VERSIONS_DIR / new_version / config_path.name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config_path, snapshot)
        entry.setdefault("configs", {})[code] = snapshot.relative_to(PROJECT_DIR).as_posix()
    manifest["current"] = new_version
    write_manifest(manifest)
    return new_version


def main() -> None:
    parser = argparse.ArgumentParser(description="H028 數學版本封存與升版")
    parser.add_argument("--type", choices=("main", "weights"), required=True)
    parser.add_argument("--config", choices=("92A", "94A", "all"), default="all")
    parser.add_argument("--message", help="只填數學調整內容，不填介面或錯誤修正")
    args = parser.parse_args()
    message = args.message
    if message is None:
        message = input("請輸入數學調整內容：").strip()
    version = run(args.type, args.config, message)
    print(f"新版本：{version}")
    print("版本封存、config、XLSX 與 Change Log 已完成。")


if __name__ == "__main__":
    main()
