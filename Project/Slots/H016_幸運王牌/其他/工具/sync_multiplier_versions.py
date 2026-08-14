from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


PROJECT_DIR = Path(__file__).resolve().parents[2]
SOURCE_DIR = PROJECT_DIR / "Source"
VERSIONS_DIR = PROJECT_DIR / "Versions"
VERSION = "1.13"
CONFIGS = {
    "92": (PROJECT_DIR / "config_92.js", SOURCE_DIR / "H016192A.xlsx"),
    "94": (PROJECT_DIR / "config_94.js", SOURCE_DIR / "H016194A.xlsx"),
}
CONFIG_PATTERN = re.compile(r"window\.H016_CONFIG\s*=\s*(\{.*\})\s*;", re.DOTALL)


def load_config(path: Path) -> tuple[str, dict[str, Any]]:
    source = path.read_text(encoding="utf-8")
    match = CONFIG_PATTERN.search(source)
    if match is None:
        raise ValueError(f"Cannot find window.H016_CONFIG in {path}")
    header = source[: match.start()].rstrip()
    return header, json.loads(match.group(1))


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def config_text(header: str, config: dict[str, Any]) -> str:
    payload = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    prefix = header + "\n" if header else ""
    return f"{prefix}window.H016_CONFIG={payload};\n"


def range_cards(
    sheet, start: int, table: str, override_weights: list[int] | None = None
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for row in range(start, start + 64):
        minimum = float(sheet.cell(row, 15).value)
        maximum = float(sheet.cell(row, 16).value)
        index = row - start
        weight = int(
            override_weights[index]
            if override_weights is not None
            else sheet.cell(row, 11).value or 0
        )
        if weight <= 0:
            continue
        cards.append({
            "type": "range",
            "min": minimum,
            "max": maximum,
            "table": table,
            "weight": weight,
        })
    return cards


def card_system(
    workbook_path: Path, override: dict[str, Any] | None = None
) -> dict[str, Any]:
    workbook = load_workbook(workbook_path, read_only=True, data_only=True)
    try:
        detail = workbook["Detail"]
        newbie = workbook["Detail_Newbie"]

        def base_cards(sheet, bg_weights) -> list[dict[str, Any]]:
            cards = range_cards(sheet, 15, "B", bg_weights)
            free_weight = int(
                bg_weights[64] if bg_weights is not None else sheet.cell(79, 11).value or 0
            )
            if free_weight > 0:
                cards.append({"type": "free_game", "table": "A", "weight": free_weight})
            return cards

        old_bg_weights = override["bg"]["weights"] if override is not None else None
        old_fg_weights = override["fg"]["weights"] if override is not None else None
        newbie_bg_weights = override["newbie"]["bg"]["weights"] if override is not None else None
        newbie_fg_weights = override["newbie"]["fg"]["weights"] if override is not None else None
        bf_weights = override["bf"]["weights"] if override is not None else None
        sf_weights = override["sf"]["weights"] if override is not None else None
        buy = range_cards(detail, 163, "E", bf_weights)
        super_cards = range_cards(detail, 234, "G", sf_weights)
        profiles = {
            "weight_1": {
                "base_game": base_cards(newbie, newbie_bg_weights),
                "free_game": range_cards(newbie, 86, "E", newbie_fg_weights),
                "buy_feature": deepcopy(buy),
                "super_feature": deepcopy(super_cards),
            },
            "weight_2": {
                "base_game": base_cards(detail, old_bg_weights),
                "free_game": range_cards(detail, 86, "E", old_fg_weights),
                "buy_feature": buy,
                "super_feature": super_cards,
            },
        }

        for profile_name, profile in profiles.items():
            for section in ("free_game", "buy_feature", "super_feature"):
                total = sum(card["weight"] for card in profile[section])
                if total != 1_000_000_000:
                    raise ValueError(
                        f"{workbook_path.name}: {profile_name}.{section} sums to {total:,}, expected 1,000,000,000"
                    )
            base_range_total = sum(
                card["weight"] for card in profile["base_game"] if card["type"] == "range"
            )
            if base_range_total != 1_000_000_000:
                raise ValueError(
                    f"{workbook_path.name}: {profile_name}.base_game range cards sum to "
                    f"{base_range_total:,}, expected 1,000,000,000"
                )
        return {
            "enabled": True,
            "retry_limit": 20_000,
            "default_profile": "weight_2",
            "profiles": profiles,
        }
    finally:
        workbook.close()


def update_manifest(config_paths: dict[str, str]) -> None:
    manifest_path = VERSIONS_DIR / "version_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["current"] = VERSION
    entry = {
        "version": VERSION,
        "date": date.today().isoformat(),
        "configs": config_paths,
        "changes": [
            "BF 改為獨立套用與 FG 相同的線型規則，RTP 目標恢復為 92.5%。",
            "BF 不含 (-1, 0] 零倍結果，第一個有權重結果為 (5, 6]；自然機率門檻、每區間 0.2% RTP 占比與 (50, 60] 加倍規則均與 FG 相同。",
            "BG 與 NB BG 完整保留 v1.10，不重新計算。",
            "FG 的 (-1, 0] 零倍結果與 (0, 1]～(4, 5] 全部不給權重；第一個有權重結果為 (5, 6]。",
            "FG 中 H016 自然機率低於 0.1% 的區間不給權重；達標區間至少占該 FG 總 RTP 的 0.2%。",
            "滿足上述高優先條件後，以最接近 Super Ace 各倍率相對 Hit Rate 的方式配置線型；只有 (50, 60] 額外提高 2 倍。",
            "Normal RTP 拆分校準：BG 固定 70%；H016192 FG 22%、H016194 FG 24%；兩份新手 BG 70%、FG 23%。",
            "新手倍率上限：BG 30x、FG 120x，超過上限的倍率區間權重歸零。",
            "SF 完全沿用 v1.12，不做調整。",
            "index 配牌超過 20,000 次仍未命中時使用最接近結果，避免極低機率倍率卡造成遊戲中斷。",
            "未修改輪帶、停輪權重、補牌權重、金框、Random Wild 或 Game Rule。",
        ],
    }
    versions = [item for item in manifest.get("versions", []) if item.get("version") != VERSION]
    for item in versions:
        if item.get("version") in {"1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9", "1.10", "1.11", "1.12"}:
            item["status"] = "superseded"
            item["superseded_by"] = VERSION
    versions.append(entry)
    manifest["versions"] = versions
    atomic_write(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    atomic_write(
        VERSIONS_DIR / "version_manifest.js",
        "window.H016_VERSION_MANIFEST = "
        + json.dumps(manifest, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", type=Path, help="Validated multiplier-rule payload override")
    args = parser.parse_args()
    payload = (
        json.loads(args.payload.read_text(encoding="utf-8"))
        if args.payload is not None
        else None
    )
    version_configs: dict[str, str] = {}
    for label, (config_path, workbook_path) in CONFIGS.items():
        if not workbook_path.is_file():
            raise FileNotFoundError(workbook_path)
        header, config = load_config(config_path)
        config["runtime_version"] = VERSION
        config["source_multiplier_xlsx"] = workbook_path.name
        override = payload["versions"][label] if payload is not None else None
        config["card_system"] = card_system(workbook_path, override)
        rendered = config_text(header, config)
        atomic_write(config_path, rendered)
        archived = VERSIONS_DIR / VERSION / config_path.name
        atomic_write(archived, rendered)
        version_configs[label] = archived.relative_to(PROJECT_DIR).as_posix()

    update_manifest(version_configs)
    print(json.dumps({"version": VERSION, "configs": version_configs}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
