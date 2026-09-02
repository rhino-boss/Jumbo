"""Recalculate v6.2 BG/FG/BF cards; preserve SF until its 10^9 report exists."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


TOOL_DIR = Path(__file__).resolve().parent
SOURCE = TOOL_DIR / "calculate_v5_1_multiplier_payload.py"


def main() -> None:
    spec = importlib.util.spec_from_file_location("h016_v6_2_partial_solver", SOURCE)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {SOURCE}")
    solver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(solver)

    project = TOOL_DIR.parents[1]
    solver.VERSION = "6.2.0.1"
    solver.NORMAL_REPORT = project / "Record" / "H0161_06_2608191134_betmode0_109.xlsx"
    # The original v6 BF xlsx was removed from Record after v6.1 was finalized.
    # Reuse its exact extracted count/pay arrays from the hash-verified v6.1
    # archive.  This is valid because the current natural change touches SF only.
    archived_payload_path = (
        project / "Versions" / "6.1" / "其他" / "H016_v6_1_multiplier_payload.json"
    )
    archived_payload = json.loads(archived_payload_path.read_text(encoding="utf-8"))
    archived_bf = archived_payload["bf_source_report"]
    bf_report = {
        "path": f"{archived_payload_path.resolve()}#bf_source_report",
        "rounds": int(archived_bf["rounds"]),
        "base_bet": float(archived_bf["base_bet"]),
        "bf_count": [int(value) for value in archived_bf["bf_count"]],
        "bf_pay": [float(value) for value in archived_bf["bf_pay"]],
    }
    if sum(bf_report["bf_count"]) != bf_report["rounds"]:
        raise ValueError("Archived v6.1 BF counts do not match rounds")
    solver.load_bf_report = lambda _path: bf_report
    solver.BF_REPORT = archived_payload_path
    solver.OUTPUT_PATH = project / "其他" / "診斷" / "H016_v6_2_partial_payload.json"
    solver.main()


if __name__ == "__main__":
    main()
