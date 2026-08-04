"""依 BG／FG 卡片權重產生彩罐熱舞固定自然遊戲 Row Data。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = SCRIPT_DIR / "Data" / "彩罐熱舞_基礎遊戲_1000人_1000轉.parquet"
CSV_OUTPUT_PATH = OUTPUT_PATH.with_suffix(".csv.gz")
METADATA_PATH = OUTPUT_PATH.with_suffix(".metadata.json")

PLAYERS = 1000
SPINS = 1000
TOTAL_ROWS = PLAYERS * SPINS
SEARCH_SEED = 20260727
CANDIDATES = 100_000
SHUFFLE_SEED = 2026072701

# 一般 BG 結果：（Lower, Upper, Hit Rate, Avg. Multi. BG）
BG_CARDS = (
    (-1.0, 0.0, 0.717055857, 0.0),
    (0.0, 1.0, 0.160623081, 0.435830536),
    (1.0, 2.0, 0.045422828, 1.497261215),
    (2.0, 3.0, 0.021536404, 2.517836201),
    (3.0, 4.0, 0.011596655, 3.567446926),
    (4.0, 5.0, 0.009134802, 4.596430086),
    (5.0, 6.0, 0.007190182, 5.585349256),
    (6.0, 7.0, 0.003320467, 6.560064648),
    (7.0, 8.0, 0.002829485, 7.621365942),
    (8.0, 9.0, 0.002562420, 8.598610603),
    (9.0, 10.0, 0.002284070, 9.646311048),
    (10.0, 15.0, 0.003122478, 12.44756245),
    (15.0, 20.0, 0.004943303, 17.48587772),
    (20.0, 25.0, 0.001632498, 22.53922896),
    (25.0, 30.0, 0.000484312, 27.54456725),
    (30.0, 35.0, 0.000399241, 32.53199743),
    (35.0, 40.0, 0.000516966, 37.54492462),
    (40.0, 45.0, 0.000206614, 42.62596653),
    (45.0, 50.0, 0.000218292, 47.66623757),
    (50.0, 60.0, 0.000362447, 54.90126537),
    (60.0, 70.0, 0.000145447, 65.0050481),
    (70.0, 80.0, 0.000128331, 75.00017852),
    (100.0, 120.0, 0.0000882, 109.6407485),
)

# BG Free Game 事件。
FG_EVENT_HIT_RATE = 0.00419562
FG_TRIGGER_BG_AVG = 0.269426957

# FG 整包區間卡：（Lower, Upper, Weight FG, Avg. Multi. FG）
FG_CARDS = (
    (10.0, 15.0, 11909520, 12.61258346),
    (15.0, 20.0, 41860452, 17.60205983),
    (20.0, 25.0, 111004404, 22.58106278),
    (25.0, 30.0, 111361643, 27.56985414),
    (30.0, 35.0, 80581250, 32.56898403),
    (35.0, 40.0, 79361966, 37.55240754),
    (40.0, 45.0, 80316879, 42.5508611),
    (45.0, 50.0, 81174018, 47.5523717),
    (50.0, 60.0, 53738887, 55.10919966),
    (60.0, 70.0, 76816777, 65.07531252),
    (70.0, 80.0, 68984893, 75.06862859),
    (80.0, 90.0, 31483369, 85.06147512),
    (90.0, 100.0, 32286981, 95.04644019),
    (100.0, 120.0, 65980191, 110.055556),
    (120.0, 140.0, 40193279, 130.0147558),
    (140.0, 160.0, 15877065, 149.9971996),
    (160.0, 180.0, 2922854, 169.9694654),
    (180.0, 200.0, 2440185, 189.9567504),
    (200.0, 250.0, 8742609, 224.5537577),
    (250.0, 300.0, 1386106, 274.4559046),
    (300.0, 350.0, 1068747, 324.4192298),
    (350.0, 400.0, 95641, 374.4242555),
    (400.0, 450.0, 54626, 424.362997),
    (450.0, 500.0, 46689, 474.3555049),
    (500.0, 550.0, 39868, 524.371771),
    (550.0, 600.0, 34094, 574.4073168),
    (600.0, 650.0, 29074, 624.3619089),
    (650.0, 700.0, 24921, 674.3624508),
    (700.0, 750.0, 21428, 724.345345),
    (750.0, 800.0, 18467, 774.3709209),
    (800.0, 850.0, 15860, 824.3931112),
    (850.0, 900.0, 13769, 874.3993791),
    (900.0, 950.0, 11894, 924.4675793),
    (950.0, 1000.0, 10334, 974.457827),
    (1000.0, 2000.0, 70885, 1321.338229),
    (2000.0, 3000.0, 9944, 2380.071703),
    (3000.0, 4000.0, 2925, 3427.00531),
    (4000.0, 5000.0, 1462, 4462.17459),
    (10000.0, 20000.0, 6023, 14078.94009),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_best_counts() -> tuple[int, np.ndarray, np.ndarray, float, float]:
    bg_weights = np.asarray(
        [card[2] for card in BG_CARDS] + [FG_EVENT_HIT_RATE],
        dtype=np.float64,
    )
    bg_values = np.asarray(
        [card[3] for card in BG_CARDS] + [FG_TRIGGER_BG_AVG],
        dtype=np.float64,
    )
    fg_weights = np.asarray([card[2] for card in FG_CARDS], dtype=np.float64)
    fg_values = np.asarray([card[3] for card in FG_CARDS], dtype=np.float64)

    if bg_weights.sum() <= 0:
        raise ValueError("Weight BG＋Free Game 必須至少有一個正權重")
    if fg_weights.sum() <= 0:
        raise ValueError("Weight FG 必須至少有一個正權重")

    bg_prob = bg_weights / bg_weights.sum()
    fg_prob = fg_weights / fg_weights.sum()
    expected_fg = float(np.sum(fg_prob * fg_values))
    theoretical_rtp = float(
        np.sum(bg_prob * bg_values)
        + bg_prob[-1] * expected_fg
    )

    rng = np.random.default_rng(SEARCH_SEED)
    best_index = -1
    best_bg_counts: np.ndarray | None = None
    best_fg_counts: np.ndarray | None = None
    best_rtp = 0.0
    best_gap = float("inf")

    for candidate in range(CANDIDATES):
        bg_counts = rng.multinomial(TOTAL_ROWS, bg_prob)
        fg_count = int(bg_counts[-1])
        fg_counts = rng.multinomial(fg_count, fg_prob)
        rtp = float(
            (
                np.sum(bg_counts * bg_values)
                + np.sum(fg_counts * fg_values)
            )
            / TOTAL_ROWS
        )
        gap = abs(rtp - theoretical_rtp)
        if gap < best_gap:
            best_gap = gap
            best_index = candidate
            best_bg_counts = bg_counts.copy()
            best_fg_counts = fg_counts.copy()
            best_rtp = rtp

    if best_bg_counts is None or best_fg_counts is None:
        raise RuntimeError("沒有產生候選資料")
    return (
        best_index,
        best_bg_counts,
        best_fg_counts,
        best_rtp,
        theoretical_rtp,
    )


def main() -> None:
    candidate, bg_counts, fg_counts, candidate_rtp, theoretical_rtp = (
        find_best_counts()
    )

    regular_bg = np.repeat(
        np.asarray([card[3] for card in BG_CARDS], dtype=np.float64),
        bg_counts[:-1],
    )
    fg_results = np.repeat(
        np.asarray([card[3] for card in FG_CARDS], dtype=np.float64),
        fg_counts,
    )
    fg_count = len(fg_results)

    bg_multiplier = np.concatenate(
        [regular_bg, np.full(fg_count, FG_TRIGGER_BG_AVG, dtype=np.float64)]
    )
    fg_multiplier = np.concatenate(
        [np.zeros(len(regular_bg), dtype=np.float64), fg_results]
    )
    natural_fg = np.concatenate(
        [np.zeros(len(regular_bg), dtype=bool), np.ones(fg_count, dtype=bool)]
    )
    natural_multiplier = bg_multiplier + fg_multiplier

    permutation = np.random.default_rng(SHUFFLE_SEED).permutation(TOTAL_ROWS)
    bg_multiplier = bg_multiplier[permutation]
    fg_multiplier = fg_multiplier[permutation]
    natural_fg = natural_fg[permutation]
    natural_multiplier = natural_multiplier[permutation]

    frame = pd.DataFrame(
        {
            "Player": np.repeat(
                np.arange(1, PLAYERS + 1, dtype=np.int16), SPINS
            ),
            "Spin": np.tile(
                np.arange(1, SPINS + 1, dtype=np.int16), PLAYERS
            ),
            "Bet": np.ones(TOTAL_ROWS, dtype=np.float32),
            "Natural_Multiplier": natural_multiplier.astype(np.float32),
            "Natural_Payout": natural_multiplier.astype(np.float32),
            "Natural_FG": natural_fg,
            "Natural_BG_Multiplier": bg_multiplier.astype(np.float32),
            "Natural_FG_Multiplier": fg_multiplier.astype(np.float32),
        }
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(OUTPUT_PATH, index=False, compression="zstd")
    frame.to_csv(CSV_OUTPUT_PATH, index=False, compression="gzip")

    actual_rtp = float(frame["Natural_Payout"].sum() / frame["Bet"].sum())
    metadata = {
        "description": "彩罐熱舞：BG Free Game 事件後另抽 FG 卡片的固定自然遊戲 Row Data",
        "game": "彩罐熱舞",
        "players": PLAYERS,
        "spins_per_player": SPINS,
        "rows": TOTAL_ROWS,
        "theoretical_rtp_percent": theoretical_rtp * 100.0,
        "actual_rtp_percent": actual_rtp * 100.0,
        "candidate_rtp_percent": candidate_rtp * 100.0,
        "candidate_index_zero_based": candidate,
        "candidate_count": CANDIDATES,
        "search_seed": SEARCH_SEED,
        "shuffle_seed": SHUFFLE_SEED,
        "natural_fg_count": int(natural_fg.sum()),
        "natural_fg_rate_percent": float(natural_fg.mean() * 100.0),
        "bg_hit_rate_total": float(
            sum(card[2] for card in BG_CARDS) + FG_EVENT_HIT_RATE
        ),
        "fg_weight_total": int(sum(card[2] for card in FG_CARDS)),
        "fg_trigger_bg_avg_multiplier": FG_TRIGGER_BG_AVG,
        "parquet_file": OUTPUT_PATH.name,
        "parquet_sha256": sha256(OUTPUT_PATH),
        "csv_gz_file": CSV_OUTPUT_PATH.name,
        "csv_gz_sha256": sha256(CSV_OUTPUT_PATH),
    }
    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"理論 RTP：{theoretical_rtp * 100.0:.9f}%")
    print(f"固定資料 RTP：{actual_rtp * 100.0:.9f}%")
    print(
        f"自然 FG：{int(natural_fg.sum()):,}"
        f"（{natural_fg.mean() * 100.0:.6f}%）"
    )
    print(f"候選版本：{candidate:,} / {CANDIDATES:,}")
    print(f"CSV.GZ Row Data：{CSV_OUTPUT_PATH}")
    print(f"Metadata：{METADATA_PATH}")


if __name__ == "__main__":
    main()
