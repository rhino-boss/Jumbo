"""H027 competitor target extraction.

Single source of truth for every metric the competitor analysis report
(`遊戲數據_Gates_of_Olympus_1000.md` / `.html`) actually states, so the model
fitter and the scorer read identical numbers.

Symbol mapping (推定, same as 競品比較_H027.md §2.2):
    S1 -> C1, S3..S11 -> M1 M2 M3 M4 A K Q J TE, 倍數球 -> C2(+C3)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OTHER = ROOT / "其他"
HTML = OTHER / "遊戲數據_Gates_of_Olympus_1000.html"

REELS = [f"R{i}" for i in range(1, 7)]
SCENES = ("BG", "FG", "BF")
# report row order inside every symbol table
SOURCE_ORDER = ["S1", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11", "倍數球"]
SYMBOL_ORDER = ["C1", "M1", "M2", "M3", "M4", "A", "K", "Q", "J", "TE", "C2"]
NORMAL_SYMBOLS = SYMBOL_ORDER[1:10]
SOURCE_TO_CODE = dict(zip(SOURCE_ORDER, SYMBOL_ORDER))

INITIAL_TABLE = {"BG": 6, "FG": 7, "BF": 8}
DROP_TABLE = {"BG": 9, "FG": 10, "BF": 11}
STACK_OVERALL_TABLE = 12
STACK_BY_SYMBOL_TABLE = {"BG": 13, "FG": 14}
CLUSTER_TABLE = 15

# --- values quoted directly from the report body (no machine-readable table) ---
BASIC = {
    "bg_rtp": 0.59763,
    "fg_rtp": 0.24868,
    "total_rtp": 0.84631,
    "bg_hit_rate": 0.22225,
    "fg_hit_rate": 0.45783,
    "fg_cycle": 433.2,
    "fg_avg_multiplier": 107.74,
    "fg_median_multiplier": 85.05,
    "bf_rtp": 0.86094,
    "bf_hit_rate": 0.38832,
    "bf_avg_multiplier": 86.094,
    "bf_price": 100.0,
}

# §3.5.1 全部轉數（含未中獎）; index 0..5 == combo 0..5+
COMBO = {
    "BG": [0.77775, 0.13882, 0.04078, 0.02462, 0.01088, 0.00714],
    "FG": [0.57831, 0.20181, 0.12349, 0.04518, 0.03313, 0.01807],
    "BF": [0.66895, 0.18047, 0.07210, 0.04266, 0.01757, 0.01825],
}

# §3.3.1 window-level longest-stack classification (mutually exclusive)
STACK_OVERALL = {
    "BG": [0.60868, 0.34952, 0.03772, 0.00363, 0.00045],
    "FG": [0.62149, 0.33735, 0.03966, 0.00151, 0.00000],
    "BF": [0.61704, 0.34560, 0.03417, 0.00299, 0.00020],
}

# §5.1.1 倍數球出現率 / 每盤球數分布
BALL_SPIN_RATE = {"BG": 0.02737, "FG": 0.50000, "BF": 0.41433}
BALL_COUNT_DIST = {
    "BG": [0.733, 0.248, 0.018, 0.000],
    "FG": [0.779, 0.186, 0.035, 0.000],
    "BF": [0.775, 0.192, 0.030, 0.003],
}

# §5.1.2 倍數值分布
MULTIPLIER_VALUES = [2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 50, 100, 250, 500]
MULTIPLIER_DIST = {
    "BG": [9.20, 8.96, 7.78, 20.28, 20.99, 14.39, 8.49, 3.30, 1.89, 2.36, 0.24, 0.47, 1.18, 0.24, 0.24],
    "FG": [45.42, 22.18, 13.38, 9.86, 4.58, 3.17, 0.35, 0.35, 0.70, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    "BF": [46.31, 24.86, 11.66, 10.17, 3.20, 1.43, 0.70, 0.52, 0.42, 0.21, 0.17, 0.28, 0.07, 0.00, 0.00],
}

# §3.6 高倍門檻（自然 21 場 + 購買 251 場合併）
THRESHOLD_SHARE = {10: 0.9191, 20: 0.8235, 50: 0.5515, 100: 0.2904, 200: 0.0993, 500: 0.0074, 1000: 0.0000}
MAX_MULTIPLIER = {"rule": 15000.0, "natural_fg": 316.40, "bf_fg": 591.10}


def _percent(value) -> float:
    return float(str(value).replace("%", "").strip()) / 100.0


def _ordered_rows(table: pd.DataFrame, columns: list[str]) -> list[list[float]]:
    return [[_percent(row[column]) for column in columns] for _, row in table.iterrows()]


class Targets:
    """Every competitor target, keyed the way the fitter needs it."""

    def __init__(self) -> None:
        tables = pd.read_html(HTML, encoding="utf-8")
        self.initial: dict[str, dict[str, dict[str, float]]] = {}
        self.drop: dict[str, dict[str, dict[str, float]]] = {}
        for scene in SCENES:
            for store, index in ((self.initial, INITIAL_TABLE[scene]), (self.drop, DROP_TABLE[scene])):
                rows = _ordered_rows(tables[index], REELS)
                store[scene] = {
                    reel: {SYMBOL_ORDER[i]: rows[i][r] for i in range(len(SYMBOL_ORDER))}
                    for r, reel in enumerate(REELS)
                }
        self.stack_by_symbol: dict[str, dict[str, dict[str, dict[int, float]]]] = {}
        for scene, index in STACK_BY_SYMBOL_TABLE.items():
            table = tables[index]
            first, second = table.columns[0], table.columns[1]
            store: dict[str, dict[str, dict[int, float]]] = {reel: {} for reel in REELS}
            for _, row in table.iterrows():
                code = SOURCE_TO_CODE.get(str(row[first]).strip())
                if code is None:
                    continue
                size = int(str(row[second]).strip()[0])
                for reel in REELS:
                    store[reel].setdefault(code, {})[size] = _percent(row[reel])
            self.stack_by_symbol[scene] = store
        # BF has no per-symbol stack table in the report; reuse BF's overall shape via FG layout
        self.stack_by_symbol["BF"] = self.stack_by_symbol["FG"]
        self.cluster: dict[str, dict[str, float]] = {}
        table = tables[CLUSTER_TABLE]
        scene_names = list(table.columns)
        current = None
        label_map = {"BG": "BG", "FG": "FG", "BF": "BF"}
        for _, row in table.iterrows():
            raw = str(row[scene_names[0]])
            for key in label_map:
                if key in raw:
                    current = key
            if current is None:
                continue
            bucket = str(row[scene_names[1]]).strip()
            self.cluster.setdefault(current, {})[bucket] = _percent(row[scene_names[2]])
        self.basic = dict(BASIC)
        self.combo = {k: list(v) for k, v in COMBO.items()}
        self.stack_overall = {k: list(v) for k, v in STACK_OVERALL.items()}
        self.ball_spin_rate = dict(BALL_SPIN_RATE)
        self.ball_count_dist = {k: list(v) for k, v in BALL_COUNT_DIST.items()}
        self.multiplier_dist = {k: [v / 100.0 for v in vals] for k, vals in MULTIPLIER_DIST.items()}

    # cluster buckets collapsed to the three H027 pay tiers
    def cluster_tiers(self, scene: str) -> dict[str, float]:
        raw = self.cluster[scene]
        return {
            "8-9": raw.get("8", 0.0) + raw.get("9", 0.0),
            "10-11": raw.get("10", 0.0) + raw.get("11", 0.0),
            "12+": raw.get("12+", 0.0),
        }

    def initial_hit_target(self, scene: str) -> float:
        """P(initial board produces a symbol win) = 1 - combo0."""
        return 1.0 - self.combo[scene][0]

    def interval_shape(self) -> dict[str, list[float]]:
        """64-interval competitor line shape, taken from 競品比較_H027.md appendix A."""
        rows = []
        for line in (OTHER / "競品比較_H027.md").read_text(encoding="utf-8").splitlines():
            if not line.startswith("| `(") or "→" not in line:
                continue
            cells = [part.strip() for part in line.split("|")[1:-1]]
            if len(cells) != 4:
                continue
            rows.append([float(cell.split("→", 1)[0].strip()) / 100.0 for cell in cells[1:]])
        if len(rows) != 64:
            raise ValueError(f"expected 64 interval rows, found {len(rows)}")
        return {"BG": [r[0] for r in rows], "FG": [r[1] for r in rows], "BF": [r[2] for r in rows]}


if __name__ == "__main__":
    t = Targets()
    for scene in SCENES:
        print(scene, "initial R1 sum", round(sum(t.initial[scene]["R1"].values()), 5),
              "drop R1 sum", round(sum(t.drop[scene]["R1"].values()), 5),
              "initial hit target", f"{t.initial_hit_target(scene):.4%}",
              "cluster", {k: f"{v:.2%}" for k, v in t.cluster_tiers(scene).items()})
    print("stack_by_symbol BG R1 TE", t.stack_by_symbol["BG"]["R1"]["TE"])
    print("interval BG head", t.interval_shape()["BG"][:4])
