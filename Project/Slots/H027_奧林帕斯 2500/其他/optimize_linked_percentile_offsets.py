from __future__ import annotations

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config.js"
SAMPLES = 20000
GRID = 64


def load_js(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    return json.loads(text[text.index("{") : text.rindex("}") + 1])


def starts_for(strip: dict, reel: int, units: np.ndarray) -> np.ndarray:
    length = int(strip["reel_lengths"][reel])
    weights = np.asarray([row[reel] for row in strip["weights"][:length]], dtype=np.int64)
    cumulative = np.cumsum(weights)
    picks = units * int(cumulative[-1]) // 1_000_000
    return np.searchsorted(cumulative, picks, side="right")


PAY_TABLE: dict[int, tuple[int, int, int]] = {}


def metrics(strip: dict, offsets: list[int]) -> tuple[float, float, float]:
    base = (np.arange(SAMPLES, dtype=np.int64) * 1_000_000 // SAMPLES + 17) % 1_000_000
    board = np.empty((SAMPLES, 5, 6), dtype=np.int16)
    symbols = np.asarray(strip["symbols"], dtype=np.int16)
    for reel in range(6):
        units = (base + int(offsets[reel])) % 1_000_000
        starts = starts_for(strip, reel, units)
        length = int(strip["reel_lengths"][reel])
        for row in range(5):
            board[:, row, reel] = symbols[(starts + row) % length, reel]
    flat = board.reshape(SAMPLES, 30)
    hit = np.zeros(SAMPLES, dtype=bool)
    pay = np.zeros(SAMPLES, dtype=np.float64)
    for symbol in range(3, 12):
        counts = np.sum(flat == symbol, axis=1)
        hit |= counts >= 8
        values = PAY_TABLE[symbol]
        pay += np.where(counts >= 12, values[2], np.where(counts >= 10, values[1], np.where(counts >= 8, values[0], 0)))
    retrigger = np.sum(flat == 1, axis=1) >= 3
    return float(np.mean(hit)), float(np.mean(retrigger)), float(np.mean(pay) / 100.0)


def objective(value: tuple[float, float, float]) -> float:
    hit, retrigger, pay_x = value
    return 3.0 * hit - pay_x - 8.0 * max(0.0, retrigger - 0.007)


def optimize(strip: dict) -> tuple[list[int], tuple[float, float, float]]:
    offsets = [0, 0, 0, 0, 0, 0]
    phases = [index * 1_000_000 // GRID for index in range(GRID)]
    best_metrics = metrics(strip, offsets)
    for _ in range(4):
        changed = False
        for reel in range(1, 6):
            current = offsets[reel]
            best_offset = current
            best_score = objective(best_metrics)
            for phase in phases:
                offsets[reel] = phase
                candidate_metrics = metrics(strip, offsets)
                score = objective(candidate_metrics)
                if score > best_score:
                    best_score = score
                    best_offset = phase
                    best_metrics = candidate_metrics
            offsets[reel] = best_offset
            changed |= best_offset != current
        if not changed:
            break
    return offsets, best_metrics


def main() -> None:
    config = load_js(CONFIG)
    global PAY_TABLE
    PAY_TABLE = {
        int(symbol): tuple(int(config["pay_table"][index][bucket]) for bucket in (3, 4, 5))
        for index, symbol in enumerate(config["symbol_ids"])
        if 3 <= int(symbol) <= 11
    }
    for name, strip in zip(config["strip_names"], config["strips"]):
        if name == "BF_Symbol":
            continue
        offsets, result = optimize(strip)
        print(f"{name}: offsets={offsets} linked_hit={result[0]:.6%} linked_retrigger={result[1]:.6%} initial_pay_x={result[2]:.6f}")


if __name__ == "__main__":
    main()
