"""產生超級寶石固定自然遊戲 Row Data（本遊戲沒有 FG）。"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
SIMULATOR_PATH = SCRIPT_DIR / "simulator_system.py"
OUTPUT_PATH = SCRIPT_DIR / "Data" / "超級寶石_基礎遊戲_1000人_1000轉.parquet"
CSV_OUTPUT_PATH = OUTPUT_PATH.with_suffix(".csv.gz")
METADATA_PATH = OUTPUT_PATH.with_suffix(".metadata.json")

PLAYERS = 1000
SPINS = 1000
TOTAL_ROWS = PLAYERS * SPINS
TARGET_RTP = 0.92
SEARCH_SEED = 20260724
CANDIDATES = 100_000
BATCH_SIZE = 5_000
SHUFFLE_SEED = 2026072401


def load_curve() -> tuple[np.ndarray, np.ndarray]:
    spec = importlib.util.spec_from_file_location("_oldhand_c_curve", SIMULATOR_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"無法載入：{SIMULATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    curve = np.asarray(module.FIXED_WEIGHT_MULTIPLIER_CURVE, dtype=np.float64)
    weights = curve[:, 2]
    multipliers = curve[:, 3]
    return weights / weights.sum(), multipliers


def find_best_counts(probabilities: np.ndarray, multipliers: np.ndarray) -> tuple[int, np.ndarray, float]:
    rng = np.random.default_rng(SEARCH_SEED)
    best_index = -1
    best_counts: np.ndarray | None = None
    best_rtp = 0.0
    best_gap = float("inf")

    processed = 0
    while processed < CANDIDATES:
        size = min(BATCH_SIZE, CANDIDATES - processed)
        counts = rng.multinomial(TOTAL_ROWS, probabilities, size=size)
        rtps = counts @ multipliers / TOTAL_ROWS
        gaps = np.abs(rtps - TARGET_RTP)
        local = int(np.argmin(gaps))
        if float(gaps[local]) < best_gap:
            best_gap = float(gaps[local])
            best_index = processed + local
            best_counts = counts[local].copy()
            best_rtp = float(rtps[local])
        processed += size

    if best_counts is None:
        raise RuntimeError("沒有產生候選資料")
    return best_index, best_counts, best_rtp


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    probabilities, multipliers = load_curve()
    candidate_index, counts, selected_rtp = find_best_counts(probabilities, multipliers)

    natural_multipliers = np.repeat(multipliers, counts)
    np.random.default_rng(SHUFFLE_SEED).shuffle(natural_multipliers)
    natural_fg = np.zeros(TOTAL_ROWS, dtype=bool)

    frame = pd.DataFrame(
        {
            "Player": np.repeat(np.arange(1, PLAYERS + 1, dtype=np.int16), SPINS),
            "Spin": np.tile(np.arange(1, SPINS + 1, dtype=np.int16), PLAYERS),
            "Bet": np.ones(TOTAL_ROWS, dtype=np.float32),
            "Natural_Multiplier": natural_multipliers.astype(np.float32),
            "Natural_Payout": natural_multipliers.astype(np.float32),
            "Natural_FG": natural_fg,
            "Natural_BG_Multiplier": natural_multipliers.astype(np.float32),
            "Natural_FG_Multiplier": np.zeros(TOTAL_ROWS, dtype=np.float32),
        }
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(OUTPUT_PATH, index=False, compression="zstd")
    frame.to_csv(CSV_OUTPUT_PATH, index=False, compression="gzip")
    actual_rtp = float(frame["Natural_Payout"].sum() / frame["Bet"].sum())
    metadata = {
        "description": "超級寶石：無救援機制固定自然遊戲 Row Data",
        "game": "超級寶石",
        "players": PLAYERS,
        "spins_per_player": SPINS,
        "rows": TOTAL_ROWS,
        "target_rtp_percent": TARGET_RTP * 100.0,
        "actual_rtp_percent": actual_rtp * 100.0,
        "candidate_rtp_percent": selected_rtp * 100.0,
        "candidate_index_zero_based": candidate_index,
        "candidate_count": CANDIDATES,
        "search_seed": SEARCH_SEED,
        "shuffle_seed": SHUFFLE_SEED,
        "natural_fg_count": int(natural_fg.sum()),
        "parquet_file": OUTPUT_PATH.name,
        "parquet_sha256": sha256(OUTPUT_PATH),
        "csv_gz_file": CSV_OUTPUT_PATH.name,
        "csv_gz_sha256": sha256(CSV_OUTPUT_PATH),
    }
    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"候選版本：{candidate_index:,} / {CANDIDATES:,}")
    print(f"固定資料 RTP：{actual_rtp * 100.0:.9f}%")
    print(f"自然 FG：{int(natural_fg.sum()):,}")
    print(f"Row Data：{OUTPUT_PATH}")
    print(f"CSV.GZ Row Data：{CSV_OUTPUT_PATH}")
    print(f"Metadata：{METADATA_PATH}")


if __name__ == "__main__":
    main()
