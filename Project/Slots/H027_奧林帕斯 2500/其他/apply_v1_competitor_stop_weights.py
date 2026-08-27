from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "其他" / "competitor_stop_weights.json"
CONFIG_PATHS = (ROOT / "config.js", ROOT / "config_92A.js", ROOT / "config_94A.js")
TABLE_SET = {
    "BG_Symbol": 0,
    "BG_Symbol (2)": 1,
    "BG_Symbol (3)": 2,
    "FG_Symbol": 3,
    "FG_Symbol (2)": 4,
}
LINKED_MODEL = {
    "BG_Symbol": (350, [0, 250000, 656250, 765625, 234375, 984375]),
    "BG_Symbol (2)": (350, [0, 921875, 625000, 421875, 312500, 31250]),
    "BG_Symbol (3)": (350, [0, 484375, 250000, 328125, 15625, 671875]),
    "FG_Symbol": (2350, [0, 703125, 734375, 781250, 250000, 656250]),
    "FG_Symbol (2)": (2350, [0, 484375, 234375, 343750, 343750, 250000]),
}


def load_js(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    return json.loads(text[text.index("{") : text.rindex("}") + 1])


def write_js(path: Path, value: dict) -> None:
    path.write_text("const data = " + json.dumps(value, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


def integer_weights(values: list[float]) -> list[int]:
    # Candidate-sharing can produce .5 counts.  A 1000 scale keeps every
    # observed stop and the measured ratio without introducing zeros.
    return [max(1, int(round(float(value) * 1000))) for value in values]


def stop_weights(evidence: dict, scene: str, reel_set: int, reel: int) -> list[int]:
    return integer_weights(evidence["stop_counts"][scene][str(reel_set)][f"R{reel + 1}"])


def combined_free_weights(evidence: dict, reel_set: int, reel: int) -> list[int]:
    fg = evidence["stop_counts"]["FG"][str(reel_set)][f"R{reel + 1}"]
    bf = evidence["stop_counts"]["BF"][str(reel_set)][f"R{reel + 1}"]
    return integer_weights([float(left) + float(right) for left, right in zip(fg, bf)])


def apply_strip_weights(config: dict, evidence: dict) -> None:
    by_name = dict(zip(config["strip_names"], config["strips"]))
    for name, reel_set in TABLE_SET.items():
        strip = by_name[name]
        lengths = strip["reel_lengths"]
        per_reel = []
        for reel, length in enumerate(lengths):
            weights = (
                stop_weights(evidence, "BG", reel_set, reel)
                if reel_set <= 2
                else combined_free_weights(evidence, reel_set, reel)
            )
            if len(weights) != int(length):
                raise ValueError(f"{name} R{reel + 1}: {len(weights)} weights != length {length}")
            if reel_set <= 2:
                symbols = [strip["symbols"][row][reel] for row in range(int(length))]
                weights = [
                    int(round(weight * 1.04))
                    if any(symbols[(stop + offset) % int(length)] == 1 for offset in range(5))
                    else weight
                    for stop, weight in enumerate(weights)
                ]
            per_reel.append(weights)
        for row in range(len(strip["weights"])):
            for reel, length in enumerate(lengths):
                strip["weights"][row][reel] = per_reel[reel][row] if row < length else 0
        strip.pop("stop_weight_source", None)
        strip.pop("stop_weight_scene", None)
        linked_weight, linked_offsets = LINKED_MODEL[name]
        strip["linked_stop_denominator"] = 10000
        strip["linked_stop_weight"] = linked_weight
        strip["linked_stop_offsets"] = linked_offsets

    # BF entry is generated directly by runtime; this table is retained only
    # for schema compatibility and is never used as the entry screen source.
    by_name["BF_Symbol"].pop("stop_weight_source", None)
    by_name["BF_Symbol"].pop("stop_weight_scene", None)
    by_name["BF_Symbol"]["linked_stop_denominator"] = 10000
    by_name["BF_Symbol"]["linked_stop_weight"] = 0
    by_name["BF_Symbol"]["linked_stop_offsets"] = [0, 0, 0, 0, 0, 0]


def update_profile(config: dict) -> None:
    normal = config["parameter"]["normal"]
    base_weights = [9698, 19298, 2344]
    normal["base_reel_weights"] = base_weights
    normal["base_reel_weights_cum"] = [base_weights[0], sum(base_weights[:2]), sum(base_weights)]
    normal["free_table"]["initial"] = [6, 9]
    normal["free_table"]["retrigger"] = [2, 3]
    feature = config["parameter"]["featurebuy"]
    feature["free_table"]["initial"] = [5, 10]
    feature["free_table"]["retrigger"] = [2, 3]


def update_config(path: Path, evidence: dict) -> None:
    config = load_js(path)
    config["excel_version"] = "1" if path.name == "config.js" else "1.0.0.0"
    config.pop("physical_model_version", None)
    config.pop("reel_stop_weight_model", None)
    config["cascade_symbol_source"] = "reel_strip"
    config.pop("drop_weights", None)
    config.pop("linked_drop", None)
    apply_strip_weights(config, evidence)
    update_profile(config)
    config["reel_set_usage"] = {
        "BG": {"sets": [0, 1, 2], "weights": [9698, 19298, 2344]},
        "FG": {"sets": [3, 4], "spin_counts": [6, 9]},
        "BF_FG": {"sets": [3, 4], "spin_counts": [5, 10]},
        "BF_ENTRY": {
            "source": "direct_generator",
            "rule": "exactly four C1 on R2-R5; remaining 26 cells uniformly use nine regular symbols",
        },
    }
    write_js(path, config)


def set_workbook_version(path: Path, version: str) -> None:
    workbook = load_workbook(path)
    workbook["Overview"]["B3"] = version
    workbook.save(path)


def main() -> None:
    evidence = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for path in CONFIG_PATHS:
        update_config(path, evidence)
        print(f"updated {path.name}")
    set_workbook_version(ROOT / "Source" / "H0271.xlsx", "1")
    set_workbook_version(ROOT / "Source" / "H027192A.xlsx", "1.0.0.0")
    set_workbook_version(ROOT / "Source" / "H027194A.xlsx", "1.0.0.0")


if __name__ == "__main__":
    main()
