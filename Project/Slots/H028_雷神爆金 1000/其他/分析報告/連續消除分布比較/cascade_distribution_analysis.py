"""Reproduce the H028 vs Lucky Neko cascade-distribution comparison.

Run from the workspace root with the project virtual environment. The script
prints counts, rates, percentage-point differences, and chi-square statistics.
It does not modify config, xlsx, or simulator files.
"""

from __future__ import annotations

import importlib.util
from math import sqrt
from pathlib import Path

import numpy as np
from numba import njit


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SIMULATOR_PATH = PROJECT_ROOT / "Simulator.py"
ROUNDS = 1_000_000
SEED = 20260804


def load_simulator():
    spec = importlib.util.spec_from_file_location("h028_combo_analysis", SIMULATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def build_sampler(module):
    choose = module.choose_parameter_set
    bg_spin = module.single_spin
    fg_spin = module.freegame_single_spin
    reel_weight = module.REEL_WEIGHT
    free_weight = module.FREE_REEL_WEIGHT
    trigger_weight = module.FREE_TRIGGER_REEL
    fg_initial = module.FG_INITIAL_MULTIPLIER
    enable_m1 = module.ENABLE_M1_MULTIPLIER

    @njit(nogil=True)
    def sample(rounds: int, seed: int):
        np.random.seed(seed)
        bg = np.zeros(6, np.int64)
        fg = np.zeros(6, np.int64)
        fg_sessions = 0

        for _ in range(rounds):
            param_set = choose(reel_weight)
            _, scatter, _, _, _, cascade_pay = bg_spin(param_set, enable_m1)
            bg[min(np.count_nonzero(cascade_pay), 5)] += 1
            if scatter < 4:
                continue

            fg_sessions += 1
            initial = 10 + max(0, scatter - 4) * 2
            remaining = initial
            initial_remaining = initial
            scheduled = initial
            multiplier = fg_initial
            m1_count = 0

            while remaining > 0:
                weights = free_weight if initial_remaining > 0 else trigger_weight
                param_set = choose(weights)
                if initial_remaining > 0:
                    initial_remaining -= 1
                _, fg_scatter, multiplier, m1_count, cascade_pay = fg_spin(
                    param_set, multiplier, m1_count, enable_m1
                )
                fg[min(np.count_nonzero(cascade_pay), 5)] += 1
                remaining -= 1
                if fg_scatter >= 4:
                    requested = 10 + (fg_scatter - 4) * 2
                    available = 50 - scheduled
                    if available > 0:
                        added = min(requested, available)
                        remaining += added
                        scheduled += added

        return bg, fg, fg_sessions

    return sample


def compare(label: str, current: np.ndarray, reference: np.ndarray) -> None:
    current_rate = current / current.sum()
    reference_rate = reference / reference.sum()
    observed = np.vstack([current, reference])
    expected = observed.sum(axis=1)[:, None] * observed.sum(axis=0)[None, :] / observed.sum()
    chi_square = float(np.sum((observed - expected) ** 2 / expected))

    print(f"\n{label}: current n={current.sum():,}, reference n={reference.sum():,}")
    print("bin,current,reference,diff_pp,95ci_low_pp,95ci_high_pp")
    labels = ["0", "1", "2", "3", "4", "5+"]
    for name, current_value, reference_value in zip(labels, current_rate, reference_rate):
        standard_error = sqrt(
            current_value * (1 - current_value) / current.sum()
            + reference_value * (1 - reference_value) / reference.sum()
        )
        difference = current_value - reference_value
        print(
            f"{name},{current_value:.8f},{reference_value:.8f},"
            f"{difference * 100:.6f},{(difference - 1.96 * standard_error) * 100:.6f},"
            f"{(difference + 1.96 * standard_error) * 100:.6f}"
        )
    print(f"chi_square={chi_square:.6f}, df=5")
    print(f"total_variation={0.5 * np.abs(current_rate - reference_rate).sum():.8f}")


def main() -> None:
    module = load_simulator()
    sample = build_sampler(module)
    sample(1, SEED)  # Compile before the measured sample.
    bg, fg, fg_sessions = sample(ROUNDS, SEED)

    # Lucky Neko ComboRate normalized to 0,1,2,3,4,5+ eliminations.
    lucky_bg = np.array([34101, 9076, 2206, 932, 406, 218 + 97 + 35 + 17 + 19])
    lucky_fg_known = np.array([326, 110, 68, 28, 12 + 6 + 2 + 1 + 1])
    lucky_fg = np.concatenate(([1519 - lucky_fg_known.sum()], lucky_fg_known))

    print(f"seed={SEED}, bg_rounds={ROUNDS:,}, fg_sessions={fg_sessions:,}, fg_spins={fg.sum():,}")
    compare("BG", bg, lucky_bg)
    compare("FG", fg, lucky_fg)


if __name__ == "__main__":
    main()
