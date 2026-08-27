from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
os.environ["H027_RUN_ALL_COMBINATIONS"] = "false"
os.environ["H027_OUTPUT_REPORT"] = "false"
os.environ["H027_CARD_SYSTEM_ENABLED"] = "false"
sys.path.insert(0, str(ROOT))
import Simulator as sim  # noqa: E402


def load_config(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    return json.loads(text[text.find("{") : text.rfind("}") + 1])


def assert_config(path: Path) -> None:
    config = load_config(path)
    for profile_name in ("normal", "featurebuy"):
        block = config["parameter"][profile_name]["c2_to_c3"]
        assert "super_multiplier" not in config["parameter"]
        assert "multiplier" in config["parameter"][profile_name]
        assert block["drop_combo_buckets"] == ["1", "2", "3", "4", "5+"]
        for name in block["table_names"]:
            assert len(block["weights_by_initial_ball_count"][name]) == 6
            assert len(block["weights_by_drop_combo"][name]) == 5


def assert_runtime_buckets() -> None:
    profile = 0
    table = sim.TABLE_BY_NAME["BG_Symbol"]
    original_initial = sim.USE_SUPER_WEIGHT[profile, table].copy()
    original_drop = sim.DROP_SUPER_WEIGHT[profile, table].copy()
    original_denominator = int(sim.USE_SUPER_DENOMINATOR[profile])
    try:
        sim.USE_SUPER_DENOMINATOR[profile] = 10000
        sim.USE_SUPER_WEIGHT[profile, table] = np.asarray([0, 10000, 0, 0, 0, 10000])
        sim.DROP_SUPER_WEIGHT[profile, table] = np.asarray([0, 10000, 0, 0, 10000])

        assert sim.prepare_initial_multiplier_symbol(sim.C2, profile, table, 1)[0] == sim.C2
        assert sim.prepare_initial_multiplier_symbol(sim.C2, profile, table, 2)[0] == sim.C3
        assert sim.prepare_initial_multiplier_symbol(sim.C2, profile, table, 6)[0] == sim.C3
        assert sim.prepare_initial_multiplier_symbol(sim.C2, profile, table, 99)[0] == sim.C3

        assert sim.prepare_drop_multiplier_symbol(sim.C2, profile, table, 1)[0] == sim.C2
        assert sim.prepare_drop_multiplier_symbol(sim.C2, profile, table, 2)[0] == sim.C3
        assert sim.prepare_drop_multiplier_symbol(sim.C2, profile, table, 3)[0] == sim.C2
        assert sim.prepare_drop_multiplier_symbol(sim.C2, profile, table, 5)[0] == sim.C3
        assert sim.prepare_drop_multiplier_symbol(sim.C2, profile, table, 99)[0] == sim.C3
        assert sim.prepare_drop_multiplier_symbol(sim.C1, profile, table, 2)[0] == sim.C1
    finally:
        sim.USE_SUPER_WEIGHT[profile, table] = original_initial
        sim.DROP_SUPER_WEIGHT[profile, table] = original_drop
        sim.USE_SUPER_DENOMINATOR[profile] = original_denominator


def main() -> None:
    for base in (ROOT, ROOT / "Versions" / "1.0"):
        for name in ("config.js", "config_92A.js", "config_94A.js"):
            assert_config(base / name)
    assert_runtime_buckets()
    print("C3 spawn-rule config and runtime bucket tests passed.")


if __name__ == "__main__":
    main()
