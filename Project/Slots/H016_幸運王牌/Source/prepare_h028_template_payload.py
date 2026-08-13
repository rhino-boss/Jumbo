"""Build the data payload used to update the copied H028 multiplier templates.

This module deliberately does not write an xlsx file.  Excel itself applies the
payload so the source workbook's formulas, styles, drawings and conditional
formatting remain intact.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
GENERATOR = PROJECT / "其他" / "generate_multiplier_models.py"
H028_SYNC = PROJECT.parent / "H028_雷神爆金 1000" / "Source" / "model_sync.py"
THRESHOLD = 1_000_000_000
COIN_IN = 100


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves the defining module through sys.modules.
    import sys

    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def fix_numbers(weights: list[int], natural_rates: list[float]) -> list[float]:
    values: list[float] = []
    for weight, natural_rate in zip(weights, natural_rates):
        values.append((weight / THRESHOLD / natural_rate) if natural_rate > 0 else 0.0)
    return values


def main() -> None:
    generator = load_module("h016_multiplier_generator", GENERATOR)
    sync = load_module("h028_model_sync_for_h016", H028_SYNC)
    buckets = generator.h028_ranges()
    stats = generator.collect_competitor(buckets)

    bg_counts = [int(bucket.count) for bucket in stats["bg"]]
    fg_counts = [int(bucket.count) for bucket in stats["fg"]]
    bg_pay = [float(bucket.pay) * COIN_IN for bucket in stats["bg"]]
    fg_pay = [float(bucket.pay) * COIN_IN for bucket in stats["fg"]]
    non_fg_total = sum(bg_counts)
    bg_natural = [count / non_fg_total if non_fg_total else 0.0 for count in bg_counts]
    bg_natural.append(stats["trigger_count"] / stats["rounds"])
    fg_natural = [count / stats["trigger_count"] for count in fg_counts]

    base = generator.base_weights(stats)
    base_excel = sync.bg_excel_weights(base, THRESHOLD)
    variants = []
    for target, filename in (
        (0.92, "H028192A.xlsx"),
        (0.94, "H028194A.xlsx"),
    ):
        bg_rtp, trigger_rate = generator.base_model_metrics(stats, base)
        free_target_mean = (target - bg_rtp) / trigger_rate
        free_weights = generator.tilted_weights(stats["fg"], free_target_mean)
        buy_weights = generator.tilted_weights(
            stats["fg"], target * generator.BUY_PRICE
        )
        variants.append(
            {
                "path": str((HERE / filename).resolve()),
                "target": target,
                "excel_version": "1.0.0.2",
                "base_weights": base,
                "free_weights": free_weights,
                "buy_weights": buy_weights,
                "base_fix": fix_numbers(base_excel, bg_natural),
                "free_fix": fix_numbers(free_weights, fg_natural),
                "buy_fix": fix_numbers(buy_weights, fg_natural),
            }
        )

    print(
        json.dumps(
            {
                "coin_in": COIN_IN,
                "threshold": THRESHOLD,
                "rounds": stats["rounds"],
                "trigger_count": stats["trigger_count"],
                "trigger_bg_pay": stats["trigger_bg_pay"] * COIN_IN,
                "bg_counts": bg_counts,
                "bg_pay": bg_pay,
                "fg_counts": fg_counts,
                "fg_pay": fg_pay,
                "reference_directory": stats["directory"],
                "reference_total_rtp": stats["total_rtp"],
                "variants": variants,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
