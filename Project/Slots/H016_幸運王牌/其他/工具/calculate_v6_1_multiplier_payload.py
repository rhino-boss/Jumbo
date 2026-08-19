"""Build the H016 v6.1 card multiplier payload from v6 Card-Off reports.

Natural math remains v6.  This wrapper reuses the audited v5.1 solver while
pinning the new source reports and the card-only version 6.1.0.0.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path


TOOL_DIR = Path(__file__).resolve().parent
SOURCE = TOOL_DIR / "calculate_v5_1_multiplier_payload.py"


def main() -> None:
    spec = importlib.util.spec_from_file_location("h016_v6_1_solver", SOURCE)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {SOURCE}")
    solver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(solver)

    project = TOOL_DIR.parents[1]
    solver.VERSION = "6.1.0.0"
    solver.NORMAL_REPORT = project / "Record" / "H0161_06_2608191032_betmode0_108.xlsx"
    solver.BF_REPORT = project / "Record" / "H0161_06_2608191033_betmode2_107.xlsx"
    solver.OUTPUT_PATH = project / "其他" / "診斷" / "H016_v6_1_multiplier_payload.json"
    solver.main()


if __name__ == "__main__":
    main()
