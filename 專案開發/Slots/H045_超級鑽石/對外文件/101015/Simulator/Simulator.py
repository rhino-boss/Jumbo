"""H045 Lucky Diamond simulator.

5x4 board, 1024 Ways, Cascade. A winning golden frame flips into a Wild (WW) or a Split Wild (W2); every flipped Wild
then draws a multiplier (x1 = no multiplier), and the W2 copies thrown out by a Split Wild reuse its multiplier. Wild multipliers on one pay line are summed
and then multiplied by the Cascade Multiplier (5 steps). All parameters come from the Config files (config.js: shared model;
config_92.js / config_94.js: card weights); reels, weights, paytable and feature parameters are not duplicated in this program.

Normal Bet only.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
import os
import random
import re
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

# ===== User Settings =====

CONFIG_FILE = "config.js"
CONFIG_RTP_FILE = "config_92.js"
TOTAL_ROUNDS = 100_000
BASE_BET_SETTING = 1.0
BET_MODE = 0  # 0 = Normal Bet
CARD_SYSTEM_ENABLED = True

RUN_ALL_COMBINATIONS = True
BATCH_RUNS = [
    # Normal Bet, card system on
    {"config_file": "config.js", "config_rtp_file": "config_92.js", "bet_mode": 0,
     "total_rounds": 10**8, "card_system_enabled": True, "base_bet": 1.0},
    {"config_file": "config.js", "config_rtp_file": "config_94.js", "bet_mode": 0,
     "total_rounds": 10**8, "card_system_enabled": True, "base_bet": 1.0},
]
THREADS = max(1, os.cpu_count() or 1)   # number of processes
OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = True
RUN_SINGLE_SPIN_DEBUG = False
DEBUG_ROUNDS = 1
CARD_RETRY_LIMIT = 10_000
RNG_SEED = 45_045

COIN_BASE = 100.0                      # credit base, same as Overview!A7
MODE_NORMALBET = 0
SUPPORTED_BET_MODES = (MODE_NORMALBET,)

WW = 0
W2 = 1
C1 = 2
SCORE_SYMBOLS = tuple(range(3, 11))
EMPTY = -1

# A golden frame is a flag on a regular symbol, not a symbol; the count per reel follows Gold Count Weight
GOLD_RESULTS = ("WW", "W2")   # Wild / Split Wild; the multiplier is drawn after the flip
NO_WIN_BONUS_GOLD = 2          # no win this spin -> add 2 golden frames on the gold reels (display only, no effect on pay)

MULTIPLIER_THRESHOLDS = (
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50,
    60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 250, 300, 350, 400, 450,
    500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000,
    2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000,
    20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000, 9999999,
)

CFG: dict[str, Any] = {}
CFG_RTP: dict[str, Any] = {}


# ===== Config =====

def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def resolve_base_dir() -> Path:
    base = Path(__file__).resolve().parent
    if not (base / CONFIG_FILE).exists():
        raise FileNotFoundError(f"{CONFIG_FILE} not found; run in the same folder as the config files.")
    return base


BASE_DIR = resolve_base_dir()


def load_js_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    start = text.index("{")
    end = text.rindex("}") + 1
    return json.loads(text[start:end])


def _version_major(value: Any) -> str:
    return str(value).split(".")[0]


def validate_config_pair(natural: dict[str, Any], rtp: dict[str, Any] | None,
                         natural_name: str, rtp_name: str) -> None:
    if natural.get("game_id") != "H045":
        raise ValueError(f"game_id of {natural_name} must be H045")
    version = str(natural.get("excel_version", ""))
    if not version.isdigit() or len(version) != 1:
        raise ValueError(f"excel_version of {natural_name} must have 1 part, got {version!r}")
    if rtp is None:
        return
    if rtp.get("game_id") != natural.get("game_id"):
        raise ValueError(f"game_id of {rtp_name} does not match {natural_name}")
    rtp_version = str(rtp.get("excel_version", ""))
    parts = rtp_version.split(".")
    if len(parts) != 4 or not all(p.isdigit() for p in parts):
        raise ValueError(f"excel_version of {rtp_name} must have 4 parts, got {rtp_version!r}")
    if parts[0] != version:
        raise ValueError(
            f"first part {parts[0]} of the {rtp_name} version must equal the shared model version {version}")


def card_section(rtp_config: dict[str, Any] | None, section: str) -> list[dict[str, Any]]:
    """Card list of the Normal Bet card groups (base_game / free_game)."""
    return ((rtp_config or {}).get("card_system", {}).get("normal_bet", {}).get(section)) or []


# ===== Game core =====

@dataclass
class Reel:
    symbols: list[int]
    cumulative: list[float]
    total: float

    def stop(self, rng: random.Random) -> int:
        position = rng.random() * self.total
        return min(bisect.bisect_right(self.cumulative, position), len(self.cumulative) - 1)

    def window(self, rng: random.Random, size: int) -> list[int]:
        start = self.stop(rng)
        length = len(self.symbols)
        return [self.symbols[(start + offset) % length] for offset in range(size)]


@dataclass
class Table:
    reels: list[Reel]
    drop_values: list[list[int]]
    drop_cumulative: list[list[float]]
    drop_total: list[float]
    gold_results: list[str]
    gold_cumulative: list[float]
    gold_total: float
    split_values: list[int]
    split_cumulative: list[float]
    split_total: float
    # Separate multiplier tables by result: WW_M and W2_M
    mult: dict[str, tuple[list[int], list[float], float]]


def _cumulative(weights: list[float]) -> tuple[list[float], float]:
    out, running = [], 0.0
    for weight in weights:
        running += max(0.0, float(weight))
        out.append(running)
    return out, running


def _pick(rng: random.Random, values: list[Any], cumulative: list[float], total: float) -> Any:
    if total <= 0:
        raise ValueError("total weight must be greater than 0")
    position = rng.random() * total
    return values[min(bisect.bisect_right(cumulative, position), len(values) - 1)]


def prepare_table(raw: dict[str, Any]) -> Table:
    reels = []
    for symbols, weights in zip(raw["reels"], raw["symbol_weight"]):
        cumulative, total = _cumulative(weights)
        reels.append(Reel(list(map(int, symbols)), cumulative, total))

    drop_values, drop_cumulative, drop_total = [], [], []
    drop = {int(k): v for k, v in raw["drop_weight"].items()}
    for reel in range(5):
        values = [sid for sid in sorted(drop) if float(drop[sid][reel]) > 0]
        cumulative, total = _cumulative([float(drop[sid][reel]) for sid in values])
        drop_values.append(values)
        drop_cumulative.append(cumulative)
        drop_total.append(total)

    grw = raw["gold_result_weight"]
    g_values = [k for k in GOLD_RESULTS if k in grw]
    g_cumulative, g_total = _cumulative([float(grw[k]) for k in g_values])

    scw = {int(k): float(v) for k, v in raw["split_count_weight"].items()}
    s_values = sorted(scw)
    s_cumulative, s_total = _cumulative([scw[k] for k in s_values])

    mult: dict[str, tuple[list[int], list[float], float]] = {}
    for key, table in raw["multiplier_wild_weight"].items():
        values = sorted(int(k) for k in table)
        cumulative, total = _cumulative([float(table[str(v)]) for v in values])
        mult[key] = (values, cumulative, total)

    return Table(reels, drop_values, drop_cumulative, drop_total,
                 g_values, g_cumulative, g_total,
                 s_values, s_cumulative, s_total, mult)


@dataclass
class SpinResult:
    pay: float = 0.0
    scatter_count: int = 0
    cascades: int = 0
    max_cascade_multiplier: int = 1
    golden_converted: int = 0
    golden_results: Counter = field(default_factory=Counter)
    split_counts: Counter = field(default_factory=Counter)
    mult_wild_created: int = 0
    mult_wild_values: Counter = field(default_factory=Counter)
    mult_kind: Counter = field(default_factory=Counter)   # count of (WW/W2/SPLIT, multiplier)
    max_line_multiplier: int = 1
    big_ghost_used: bool = False
    big_ghost_scored: bool = False               # Split Wild body or a thrown W2 was removed (part of a win)
    mult_cells: int = 0                          # number of Wilds with a multiplier (x2 or more, incl. thrown W2)
    mult_left: int = 0                           # Wilds with a multiplier still on the board (not removed) at settlement
    initial_gold_count: int = 0
    gold_appeared: int = 0                       # golden frames on the initial screen and after refills (usage denominator)
    initial_gold_reel: Counter = field(default_factory=Counter)   # golden frames per reel on the initial screen
    symbol_hits: Counter = field(default_factory=Counter)
    symbol_pay: Counter = field(default_factory=Counter)
    symbol_length_hits: Counter = field(default_factory=Counter)
    symbol_length_pay: Counter = field(default_factory=Counter)
    initial_symbols: Counter = field(default_factory=Counter)
    drop_symbols: Counter = field(default_factory=Counter)
    initial_board: list[list[int]] = field(default_factory=list)
    final_board: list[list[int]] = field(default_factory=list)
    final_gold: list[list[bool]] = field(default_factory=list)
    bonus_gold_cells: list[tuple[int, int]] = field(default_factory=list)   # positions of golden frames added on no-win spins


@dataclass
class RoundResult:
    pay_bg: float = 0.0
    pay_fg: float = 0.0
    fg_triggered: bool = False
    fg_spins: int = 0
    retriggers: int = 0
    cascades_bg: int = 0
    cascades_fg: int = 0
    capped: bool = False
    golden_converted: int = 0
    bg_golden_results: Counter = field(default_factory=Counter)
    fg_golden_results: Counter = field(default_factory=Counter)
    bg_split_counts: Counter = field(default_factory=Counter)
    fg_split_counts: Counter = field(default_factory=Counter)
    bg_mult_wild: int = 0
    fg_mult_wild: int = 0
    mult_wild_values: Counter = field(default_factory=Counter)
    bg_mult_kind: Counter = field(default_factory=Counter)
    fg_mult_kind: Counter = field(default_factory=Counter)
    max_line_multiplier: int = 1
    bg_hit_spins: int = 0
    fg_hit_spins: int = 0
    bg_gold_symbols: int = 0
    fg_gold_symbols: int = 0
    bg_gold_appeared: int = 0
    fg_gold_appeared: int = 0
    bg_flip_spins: int = 0      # spins with a golden frame removed and flipped
    fg_flip_spins: int = 0
    bg_mult_spins: int = 0      # spins showing a Wild with a multiplier (x2 or more) after a flip
    fg_mult_spins: int = 0
    bg_mult_cells: int = 0      # Wilds with a multiplier: shown / not removed at settlement / spins with a multiplier but none removed
    fg_mult_cells: int = 0
    bg_mult_left: int = 0
    fg_mult_left: int = 0
    bg_mult_unused_spins: int = 0
    fg_mult_unused_spins: int = 0
    # By-game indicators: spins where a Split Wild appears / appears and is used, spins with golden frames (incl. refills)
    bg_big_spins: int = 0
    fg_big_spins: int = 0
    bg_big_used_spins: int = 0
    fg_big_used_spins: int = 0
    bg_gold_seen_spins: int = 0
    fg_gold_seen_spins: int = 0
    bg_gold_reel: Counter = field(default_factory=Counter)
    fg_gold_reel: Counter = field(default_factory=Counter)
    bg_gold_boards: int = 0
    fg_gold_boards: int = 0
    special_symbol_cnt: int = 0
    bg_trigger_fg_cnt: int = 0
    bg_trigger_fg_pay: float = 0.0
    bg_cascade_count: int = 0
    combo_fg: Counter = field(default_factory=Counter)
    fg_pay_per_spin: list[float] = field(default_factory=list)
    symbol_hits: Counter = field(default_factory=Counter)
    symbol_pay: Counter = field(default_factory=Counter)
    bg_symbol_length_hits: Counter = field(default_factory=Counter)
    fg_symbol_length_hits: Counter = field(default_factory=Counter)
    bg_symbol_length_pay: Counter = field(default_factory=Counter)
    fg_symbol_length_pay: Counter = field(default_factory=Counter)
    bg_initial_symbols: Counter = field(default_factory=Counter)
    bg_drop_symbols: Counter = field(default_factory=Counter)
    fg_initial_symbols: Counter = field(default_factory=Counter)
    fg_drop_symbols: Counter = field(default_factory=Counter)

    @property
    def pay(self) -> float:
        return self.pay_bg + self.pay_fg


class SuperDiamond:
    """H045 game core. Each instance owns its RNG and is used by a single worker."""

    def __init__(self, config: dict[str, Any], rtp_config: dict[str, Any] | None,
                 seed: int, bet_amount: float, card_enabled: bool):
        self.config = config
        self.rtp_config = rtp_config or {}
        self.rng = random.Random(seed)
        self.bet = bet_amount
        self.card_enabled = bool(card_enabled and (self.rtp_config.get("card_system") or {}).get("enabled"))
        self.tables = {name: prepare_table(raw) for name, raw in config["tables"].items()}
        self.ladder_bg = list(map(int, config["cascade_multiplier"]["bg"]))
        self.ladder_fg = list(map(int, config["cascade_multiplier"]["fg"]))
        self.pays = {int(k): v for k, v in config["pays"].items()}
        self.max_fs = int(config["max_free_spins"])
        self.split_reels = list(map(int, config["split_target_reels"]))
        self.gold_reels = list(map(int, config["gold_reels"]))
        # Golden frame count distribution: {scene: [(values, cumulative, total) per reel]}
        self.gold_count = {
            scene: [_cumulative([float(w) for w in per_reel])
                    for per_reel in config["gold_count_weight"][scene]]
            for scene in ("bg", "fg")
        }
        # A table may carry its own gold_count_weight (e.g. bg_3 / fg_3), which overrides the scene default
        for name, raw in config["tables"].items():
            if raw.get("gold_count_weight"):
                self.gold_count[name] = [_cumulative([float(w) for w in per_reel])
                                         for per_reel in raw["gold_count_weight"]]
        # Max Win is set by the card system multiplier cap; no cap when the card system is off
        self.max_win = self._card_multiplier_cap()
        self.fs_table = {int(k): v for k, v in config["free_spins"].items()}
        self.retry_total = 0
        self.retry_limit_exceeded = 0
        self.retry_limit_bg_range = 0
        self.retry_limit_bg_freegame = 0
        self.retry_limit_fg = 0
        self.card_draws: Counter = Counter()

    def _card_section_cap(self, section: str) -> float:
        """Upper bound of the highest weighted range card of a Normal Bet card group; infinity when the card system is off."""
        if not self.card_enabled:
            return math.inf
        cards = card_section(self.rtp_config, section)
        caps = [float(c["max"]) for c in cards
                if str(c.get("type")) == "range" and float(c.get("weight", 0)) > 0 and "max" in c]
        return max(caps) if caps else math.inf

    def _card_multiplier_cap(self) -> float:
        """Max Win (per game) is the larger upper bound of the highest weighted range of the base_game / free_game card groups;
        the BG Trigger Cap is set by the base_game card group and stored in self.bg_trigger_cap."""
        self.bg_trigger_cap = self._card_section_cap("base_game")
        self.fg_cap = self._card_section_cap("free_game")
        self.trigger_cap = self.bg_trigger_cap
        return max(self.fg_cap, self.bg_trigger_cap)

    # --- Board ---

    def gold_key(self, table_name: str, scene: str) -> str:
        """Source of the golden frame count weights: the own weights of the table if present, otherwise the scene (bg / fg) default."""
        return table_name if table_name in self.gold_count else scene

    def gold_target(self, scene: str, reel: int) -> int:
        """Draw how many golden frames this reel has this time (0-4)."""
        cumulative, total = self.gold_count[scene][reel]
        if total <= 0:
            return 0
        return min(bisect.bisect_right(cumulative, self.rng.random() * total), len(cumulative) - 1)

    def topup_gold(self, scene: str, symbols: list[list[int]],
                   gold: list[list[bool]], fresh_rows: dict[int, list[int]]) -> int:
        """After a refill, redraw the count N, keep surviving golden frames and add new ones only on refilled cells. Returns the number added.
        fresh_rows: rows refilled in place on each reel."""
        added = 0
        for reel in self.gold_reels:
            rows = fresh_rows.get(reel, [])
            if not rows:
                continue
            target = self.gold_target(scene, reel)
            alive = sum(gold[reel])
            short = target - alive
            if short <= 0:
                continue
            spots = [row for row in rows
                     if not gold[reel][row] and symbols[reel][row] != C1]
            self.rng.shuffle(spots)
            for row in spots[:short]:
                gold[reel][row] = True
                added += 1
        return added

    def add_no_win_gold(self, symbols: list[list[int]], gold: list[list[bool]]) -> list[tuple[int, int]]:
        """On a no-win spin, add golden frames on NO_WIN_BONUS_GOLD random distinct cells of the gold reels that are not golden and not C1;
        if fewer cells are available, add as many as possible. A no-win board has no pay line and golden frames do not change evaluation, so pay / RTP are unchanged."""
        spots = [(reel, row) for reel in self.gold_reels for row in range(4)
                 if not gold[reel][row] and symbols[reel][row] != C1]
        self.rng.shuffle(spots)
        for reel, row in spots[:NO_WIN_BONUS_GOLD]:
            gold[reel][row] = True
        return spots[:NO_WIN_BONUS_GOLD]

    def draw_gold(self, scene: str, symbols: list[list[int]]) -> list[list[bool]]:
        """Draw the golden frame count of each reel from Gold Count Weight, then pick random cells to flag.

        Golden frames appear only on gold_reels (R2-R4) and never on a Scatter.
        """
        gold = [[False] * 4 for _ in range(5)]
        for reel in self.gold_reels:
            cumulative, total = self.gold_count[scene][reel]
            if total <= 0:
                continue
            count = min(bisect.bisect_right(cumulative, self.rng.random() * total), len(cumulative) - 1)
            if count <= 0:
                continue
            spots = [row for row in range(4) if symbols[reel][row] != C1]
            if not spots:
                continue
            self.rng.shuffle(spots)
            for row in spots[:count]:
                gold[reel][row] = True
        return gold

    def board(self, table_name: str, scene: str = "bg"):
        table = self.tables[table_name]
        symbols = [table.reels[reel].window(self.rng, 4) for reel in range(5)]
        mults = [[0] * 4 for _ in range(5)]
        return symbols, mults, self.draw_gold(self.gold_key(table_name, scene), symbols)

    def evaluate(self, symbols: list[list[int]], mults: list[list[int]]):
        """Return (raw_pay, hit_positions, details, max_line_mult).

        raw_pay includes the sum of Wild multipliers on the board but not the Cascade Multiplier.
        """
        total = 0.0
        hits: set[tuple[int, int]] = set()
        details: list[tuple[int, int, int, float, int]] = []
        best_line_mult = 1
        lines: list[tuple[int, int, int, float]] = []
        for target in SCORE_SYMBOLS:
            counts: list[int] = []
            positions: list[list[tuple[int, int]]] = []
            for reel in range(5):
                # A golden frame is a flag, not a symbol; evaluate with the underlying symbol
                matched = [
                    (reel, row)
                    for row, symbol in enumerate(symbols[reel])
                    if symbol in (WW, W2) or symbol == target
                ]
                if not matched:
                    break
                counts.append(len(matched))
                positions.append(matched)
            length = len(counts)
            if length < 3:
                continue
            ways = 1
            for count in counts:
                ways *= count
            raw = float(self.pays[target][length - 3]) * ways
            if raw <= 0:
                continue
            for group in positions:
                hits.update(group)
            lines.append((target, length, ways, raw))
        # Only multipliers of Wilds removed in this win are summed (x1 not counted),
        # applied to all pay lines of this cascade; unused Wilds stay on the board; a sum of 0 counts as x1
        used_sum = sum(mults[reel][row] for reel, row in hits
                       if symbols[reel][row] in (WW, W2) and mults[reel][row] > 1)
        line_mult = used_sum if used_sum > 0 else 1
        for target, length, ways, raw in lines:
            total += raw * line_mult
            details.append((target, length, ways, raw * line_mult, line_mult))
        if lines:
            best_line_mult = line_mult
        return total, hits, details, best_line_mult

    def _draw_multiplier(self, table: Table, outcome: str, result: SpinResult) -> int:
        """Draw once from the multiplier table of the result; 1 means no multiplier."""
        values, cumulative, total = table.mult[outcome]
        value = int(_pick(self.rng, values, cumulative, total))
        if value > 1:
            result.mult_wild_created += 1
            result.mult_cells += 1
        result.mult_wild_values[value] += 1
        result.mult_kind[(outcome, value)] += 1
        return value

    def flip_golden_body(self, table: Table, symbols: list[list[int]], mults: list[list[int]],
                         gold_positions: list[tuple[int, int]], result: SpinResult,
                         free_game: bool) -> list[tuple[tuple[int, int], int]]:
        """Each winning golden frame draws Wild / Split Wild, then a multiplier.
        The body is written into its cell at removal, before the refill. Returns the Split Wild bodies to split after the refill."""
        big_sources: list[tuple[tuple[int, int], int]] = []
        for reel, row in gold_positions:
            outcome = _pick(self.rng, table.gold_results, table.gold_cumulative, table.gold_total)
            # At most one Split Wild per Base Game spin; later flips become Wild
            if outcome == "W2" and not free_game and result.big_ghost_used:
                outcome = "WW"
            result.golden_results[outcome] += 1
            result.golden_converted += 1
            symbols[reel][row] = W2 if outcome == "W2" else WW
            value = self._draw_multiplier(table, outcome, result)   # x1 means no multiplier
            mults[reel][row] = value if value > 1 else 0
            if outcome == "W2":
                result.big_ghost_used = True
                big_sources.append(((reel, row), value))
        return big_sources

    @staticmethod
    def _flip_stats_mark(result: SpinResult) -> dict[str, Any]:
        """Stats snapshot before a flip (used to re-record as Wilds without multiplier when the cascade ends)."""
        return {"golden_results": Counter(result.golden_results), "golden_converted": result.golden_converted,
                "mult_wild_created": result.mult_wild_created, "mult_cells": result.mult_cells,
                "mult_wild_values": Counter(result.mult_wild_values), "mult_kind": Counter(result.mult_kind),
                "split_counts": Counter(result.split_counts), "big_ghost_used": result.big_ghost_used}

    @staticmethod
    def _collapse_last_flip(result: SpinResult, symbols, mults, gold, mark, positions, pre_split) -> None:
        """No further win after the last flip: restore the board before splitting, set flipped cells to WW without multiplier, and re-record n Wilds without multiplier."""
        for key, value in mark.items():
            setattr(result, key, value)
        n = len(positions)
        result.golden_results["WW"] += n
        result.golden_converted += n
        result.mult_wild_values[1] += n
        result.mult_kind[("WW", 1)] += n
        if pre_split:
            for r in range(5):
                symbols[r][:], mults[r][:], gold[r][:] = pre_split[0][r], pre_split[1][r], pre_split[2][r]
        for r, c in positions:
            symbols[r][c], mults[r][c] = WW, 0

    def split_big_ghosts(self, table: Table, symbols: list[list[int]], mults: list[list[int]], gold: list[list[bool]],
                         big_sources: list[tuple[tuple[int, int], int]], result: SpinResult) -> None:
        """After the refill, a Split Wild body throws out 2-4 W2 (same multiplier), placed on the refilled board."""
        for source, value in big_sources:
            count = int(_pick(self.rng, table.split_values, table.split_cumulative, table.split_total))
            candidates = [
                (reel, row)
                for reel in self.split_reels
                for row in range(4)
                if symbols[reel][row] not in (WW, W2, C1) and (reel, row) != source
            ]
            if not candidates:
                result.split_counts[0] += 1
                continue
            self.rng.shuffle(candidates)
            placed = candidates[:count]
            for reel, row in placed:
                result.mult_kind[("SPLIT", value)] += 1
                result.mult_cells += int(value > 1)
                # A thrown copy is W2, identical to the body; no new multiplier is drawn
                symbols[reel][row] = W2
                mults[reel][row] = value if value > 1 else 0
                gold[reel][row] = False   # a covered golden frame becomes W2 and is no longer flipped
            result.split_counts[len(placed)] += 1

    def spin(self, table_name: str, free_game: bool = False) -> SpinResult:
        table = self.tables[table_name]
        scene = "fg" if free_game else "bg"
        ladder = self.ladder_fg if free_game else self.ladder_bg
        symbols, mults, gold = self.board(table_name, scene)
        result = SpinResult(initial_board=[reel[:] for reel in symbols])
        result.initial_symbols.update(
            (reel, symbol) for reel, column in enumerate(symbols) for symbol in column)
        result.initial_gold_count = sum(sum(column) for column in gold)
        result.gold_appeared = result.initial_gold_count
        result.initial_gold_reel.update({reel: sum(column) for reel, column in enumerate(gold) if sum(column)})

        cap = self.max_win * self.bet
        last_flip = None   # last flip: (stats before flip, golden frame positions, board before split)
        while True:
            raw_pay, hits, details, line_mult = self.evaluate(symbols, mults)
            if raw_pay <= 0:
                # No further win after the last flip (cascade ends): flipped cells are shown as Wilds without multiplier in place (no split);
                # board and stats follow the final screen. Removing the thrown Wilds cannot create a win and the multipliers are unused, so pay is unchanged.
                if last_flip:
                    self._collapse_last_flip(result, symbols, mults, gold, *last_flip)
                break
            multiplier = ladder[min(result.cascades, len(ladder) - 1)]
            gained = raw_pay * multiplier * self.bet
            result.pay += gained
            result.max_cascade_multiplier = max(result.max_cascade_multiplier, multiplier)
            result.max_line_multiplier = max(result.max_line_multiplier, line_mult)
            result.cascades += 1
            for symbol, length, ways, symbol_raw, _ in details:
                result.symbol_hits[symbol] += ways
                result.symbol_pay[symbol] += symbol_raw * multiplier * self.bet
                result.symbol_length_hits[(symbol, length)] += 1
                result.symbol_length_pay[(symbol, length)] += symbol_raw * multiplier * self.bet

            gold_positions: list[tuple[int, int]] = []
            for reel, row in hits:
                if symbols[reel][row] == W2 and not gold[reel][row]:
                    result.big_ghost_scored = True
                if gold[reel][row]:
                    gold_positions.append((reel, row))   # golden frames are not removed; they flip into the body in place
                    gold[reel][row] = False
                else:
                    symbols[reel][row] = EMPTY
                    mults[reel][row] = 0

            # Golden frames flip in place; a Split Wild splits after the refill
            mark = self._flip_stats_mark(result) if gold_positions else None
            big_sources = (self.flip_golden_body(table, symbols, mults, gold_positions, result, free_game)
                           if gold_positions else [])

            # In-place refill: removed cells get new symbols in place; other symbols do not move
            fresh_rows: dict[int, list[int]] = {}
            for reel in range(5):
                rows = [row for row in range(4) if symbols[reel][row] == EMPTY]
                for row in rows:
                    symbol = int(_pick(self.rng, table.drop_values[reel],
                                       table.drop_cumulative[reel], table.drop_total[reel]))
                    symbols[reel][row], mults[reel][row], gold[reel][row] = symbol, 0, False
                    result.drop_symbols[(reel, symbol)] += 1
                fresh_rows[reel] = rows

            # Redraw golden frame counts after the refill
            result.gold_appeared += self.topup_gold(self.gold_key(table_name, scene), symbols, gold, fresh_rows)

            pre_split = ([c[:] for c in symbols], [c[:] for c in mults], [c[:] for c in gold]) if big_sources else None
            if big_sources:
                self.split_big_ghosts(table, symbols, mults, gold, big_sources, result)
            last_flip = (mark, list(gold_positions), pre_split) if gold_positions else None

            if result.pay >= cap:
                break

        if result.pay <= 0:
            result.bonus_gold_cells = self.add_no_win_gold(symbols, gold)
        result.scatter_count = sum(symbol == C1 for column in symbols for symbol in column)
        result.final_board = [reel[:] for reel in symbols]
        result.final_gold = [reel[:] for reel in gold]
        result.mult_left = sum(1 for reel in range(5) for row in range(4)
                               if symbols[reel][row] in (WW, W2) and mults[reel][row] > 1)
        return result

    # --- Card System ---

    def pick_card(self, section: str) -> dict[str, Any]:
        cards = card_section(self.rtp_config, section)
        weights = [float(card["weight"]) for card in cards]
        cumulative, total = _cumulative(weights)
        index = min(bisect.bisect_right(cumulative, self.rng.random() * total), len(cards) - 1)
        self.card_draws[(section, index)] += 1
        return dict(cards[index])

    def card_matches(self, card: dict[str, Any], pay: float) -> bool:
        ratio = pay / self.bet
        return float(card["min"]) < ratio <= float(card["max"])

    # --- Round ---

    def natural_base_spin(self) -> SpinResult:
        weights = self.config["table_weight"]["bg"]
        names = list(weights)
        cumulative, total = _cumulative([float(weights[n]) for n in names])
        return self.spin(str(_pick(self.rng, names, cumulative, total)))

    def card_spin(self, card: dict[str, Any]) -> SpinResult:
        want_fg = card.get("type") == "free_game"
        spin = None
        for _ in range(CARD_RETRY_LIMIT):
            spin = self.natural_base_spin()
            if want_fg:
                # A free_game card needs both a Free Game trigger and a BG win <= BG Trigger Cap; otherwise the whole game is redrawn
                if spin.scatter_count >= 3 and spin.pay / self.bet <= self.trigger_cap:
                    return spin
            elif spin.scatter_count < 3 and self.card_matches(card, spin.pay):
                return spin
            self.retry_total += 1
        self.retry_limit_exceeded += 1
        if want_fg:
            self.retry_limit_bg_freegame += 1
        else:
            self.retry_limit_bg_range += 1
        return spin

    def _fg_table(self, group: str) -> str:
        weights = self.config["table_weight"][group]
        names = list(weights)
        cumulative, total = _cumulative([float(weights[n]) for n in names])
        return str(_pick(self.rng, names, cumulative, total))

    def free_session(self, initial_spins: int, budget: float) -> RoundResult:
        result = RoundResult(fg_triggered=True)
        remaining, played = int(initial_spins), 0
        cap = self.max_win * self.bet
        while remaining > 0 and played < self.max_fs:
            remaining -= 1
            played += 1
            spin = self.spin(self._fg_table("fg"), free_game=True)
            result.pay_fg += spin.pay
            result.fg_pay_per_spin.append(spin.pay)
            result.fg_spins += 1
            result.cascades_fg += spin.cascades
            result.golden_converted += spin.golden_converted
            result.fg_golden_results.update(spin.golden_results)
            result.fg_split_counts.update(spin.split_counts)
            result.fg_mult_wild += spin.mult_wild_created
            result.mult_wild_values.update(spin.mult_wild_values)
            result.fg_mult_kind.update(spin.mult_kind)
            result.max_line_multiplier = max(result.max_line_multiplier, spin.max_line_multiplier)
            result.fg_hit_spins += int(spin.pay > 0)
            result.fg_gold_symbols += spin.initial_gold_count
            result.fg_gold_appeared += spin.gold_appeared
            result.fg_flip_spins += int(spin.golden_converted > 0)
            result.fg_mult_spins += int(spin.mult_wild_created > 0)
            result.fg_mult_cells += spin.mult_cells
            result.fg_mult_left += spin.mult_left
            result.fg_mult_unused_spins += int(spin.mult_cells > 0 and spin.mult_left == spin.mult_cells)
            result.fg_big_spins += int(spin.golden_results["W2"] > 0)
            result.fg_big_used_spins += int(spin.golden_results["W2"] > 0 and spin.big_ghost_scored)
            result.fg_gold_seen_spins += int(spin.gold_appeared > 0)
            result.fg_gold_reel.update(spin.initial_gold_reel)
            result.fg_gold_boards += int(spin.initial_gold_count > 0)
            result.special_symbol_cnt += int(spin.scatter_count > 0)
            result.combo_fg[min(spin.cascades, 5)] += 1
            result.symbol_hits.update(spin.symbol_hits)
            result.symbol_pay.update(spin.symbol_pay)
            result.fg_symbol_length_hits.update(spin.symbol_length_hits)
            result.fg_symbol_length_pay.update(spin.symbol_length_pay)
            result.fg_initial_symbols.update(spin.initial_symbols)
            result.fg_drop_symbols.update(spin.drop_symbols)
            if budget + result.pay_fg >= cap:
                result.capped = True
                break
            if spin.scatter_count >= 3 and played + remaining < self.max_fs:
                add = min(5, self.max_fs - played - remaining)
                if add > 0:
                    remaining += add
                    result.retriggers += 1
        return result

    def card_feature(self, section: str, initial_spins: int, budget: float) -> RoundResult:
        card = self.pick_card(section)
        result = None
        for _ in range(CARD_RETRY_LIMIT):
            result = self.free_session(initial_spins, budget)
            if self.card_matches(card, result.pay_fg):
                return result
            self.retry_total += 1
        self.retry_limit_exceeded += 1
        self.retry_limit_fg += 1
        return result

    @staticmethod
    def merge(target: RoundResult, source: RoundResult) -> None:
        target.pay_fg += source.pay_fg
        target.fg_triggered |= source.fg_triggered
        target.fg_spins += source.fg_spins
        target.retriggers += source.retriggers
        target.cascades_fg += source.cascades_fg
        target.capped |= source.capped
        target.golden_converted += source.golden_converted
        target.fg_golden_results.update(source.fg_golden_results)
        target.fg_split_counts.update(source.fg_split_counts)
        target.fg_mult_wild += source.fg_mult_wild
        target.mult_wild_values.update(source.mult_wild_values)
        target.fg_mult_kind.update(source.fg_mult_kind)
        target.max_line_multiplier = max(target.max_line_multiplier, source.max_line_multiplier)
        target.fg_hit_spins += source.fg_hit_spins
        target.fg_gold_symbols += source.fg_gold_symbols
        target.fg_gold_appeared += source.fg_gold_appeared
        target.fg_flip_spins += source.fg_flip_spins
        target.fg_mult_spins += source.fg_mult_spins
        target.fg_mult_cells += source.fg_mult_cells
        target.fg_mult_left += source.fg_mult_left
        target.fg_mult_unused_spins += source.fg_mult_unused_spins
        target.fg_big_spins += source.fg_big_spins
        target.fg_big_used_spins += source.fg_big_used_spins
        target.fg_gold_seen_spins += source.fg_gold_seen_spins
        target.fg_gold_reel.update(source.fg_gold_reel)
        target.fg_gold_boards += source.fg_gold_boards
        target.special_symbol_cnt += source.special_symbol_cnt
        target.combo_fg.update(source.combo_fg)
        target.fg_pay_per_spin.extend(source.fg_pay_per_spin)
        target.symbol_hits.update(source.symbol_hits)
        target.symbol_pay.update(source.symbol_pay)
        target.fg_symbol_length_hits.update(source.fg_symbol_length_hits)
        target.fg_symbol_length_pay.update(source.fg_symbol_length_pay)
        target.fg_initial_symbols.update(source.fg_initial_symbols)
        target.fg_drop_symbols.update(source.fg_drop_symbols)

    def round(self) -> RoundResult:
        """One Normal Bet game."""
        result = RoundResult()
        spin = self.card_spin(self.pick_card("base_game")) if self.card_enabled else self.natural_base_spin()
        result.pay_bg = spin.pay
        result.cascades_bg = spin.cascades
        result.bg_cascade_count = spin.cascades
        result.golden_converted = spin.golden_converted
        result.bg_golden_results.update(spin.golden_results)
        result.bg_split_counts.update(spin.split_counts)
        result.bg_mult_wild = spin.mult_wild_created
        result.mult_wild_values.update(spin.mult_wild_values)
        result.bg_mult_kind.update(spin.mult_kind)
        result.max_line_multiplier = spin.max_line_multiplier
        result.bg_hit_spins = int(spin.pay > 0)
        result.bg_gold_symbols = spin.initial_gold_count
        result.bg_gold_appeared = spin.gold_appeared
        result.bg_flip_spins = int(spin.golden_converted > 0)
        result.bg_mult_spins = int(spin.mult_wild_created > 0)
        result.bg_mult_cells = spin.mult_cells
        result.bg_mult_left = spin.mult_left
        result.bg_mult_unused_spins = int(spin.mult_cells > 0 and spin.mult_left == spin.mult_cells)
        result.bg_big_spins = int(spin.golden_results["W2"] > 0)
        result.bg_big_used_spins = int(spin.golden_results["W2"] > 0 and spin.big_ghost_scored)
        result.bg_gold_seen_spins = int(spin.gold_appeared > 0)
        result.bg_gold_reel.update(spin.initial_gold_reel)
        result.bg_gold_boards = int(spin.initial_gold_count > 0)
        result.special_symbol_cnt = int(spin.scatter_count > 0)
        result.symbol_hits.update(spin.symbol_hits)
        result.symbol_pay.update(spin.symbol_pay)
        result.bg_symbol_length_hits.update(spin.symbol_length_hits)
        result.bg_symbol_length_pay.update(spin.symbol_length_pay)
        result.bg_initial_symbols.update(spin.initial_symbols)
        result.bg_drop_symbols.update(spin.drop_symbols)

        if spin.scatter_count >= 3:
            result.bg_trigger_fg_cnt = 1
            result.bg_trigger_fg_pay = spin.pay
            initial = self.fs_table[min(spin.scatter_count, max(self.fs_table))]["initial"]
            feature = (self.card_feature("free_game", initial, result.pay_bg)
                       if self.card_enabled else self.free_session(initial, result.pay_bg))
            self.merge(result, feature)

        cap = self.max_win * self.bet
        if result.pay > cap:                      # truncate at the cap
            overflow = result.pay - cap
            result.pay_fg = max(0.0, result.pay_fg - overflow)
            if result.pay > cap:
                result.pay_bg = min(result.pay_bg, cap)
            result.capped = True
        return result


# ===== Statistics =====

def wager_for_mode(mode: int, base_bet: float) -> float:
    """Normal Bet bet = base bet x cost_multiplier (1)."""
    return base_bet * float(CFG["bet_modes"]["normal"]["cost_multiplier"])


def threshold_index(multiplier: float) -> int:
    for index, upper in enumerate(MULTIPLIER_THRESHOLDS):
        if multiplier <= upper:
            return index
    return len(MULTIPLIER_THRESHOLDS) - 1


def _empty_stats() -> dict[str, Any]:
    buckets = len(MULTIPLIER_THRESHOLDS)
    return {
        "rounds": 0, "coin_in": 0.0, "pay_bg": 0.0, "pay_fg": 0.0,
        "win_x_sum": 0.0, "win_x_square": 0.0, "max_win_x": 0.0, "capped_rounds": 0,
        "bg_hit_spins": 0, "fg_hit_spins": 0, "fg_spins": 0, "fg_triggers": 0,
        "retriggers": 0, "cascades_bg": 0, "cascades_fg": 0,
        "special_symbol_cnt": 0, "bg_trigger_fg_cnt": 0, "bg_trigger_fg_pay": 0.0,
        "golden_converted": 0, "bg_gold_symbols": 0, "fg_gold_symbols": 0,
        "bg_gold_appeared": 0, "fg_gold_appeared": 0,
        "bg_flip_spins": 0, "fg_flip_spins": 0, "bg_mult_spins": 0, "fg_mult_spins": 0,
        "bg_big_spins": 0, "fg_big_spins": 0, "bg_big_used_spins": 0, "fg_big_used_spins": 0,
        "bg_gold_seen_spins": 0, "fg_gold_seen_spins": 0,
        "bg_mult_cells": 0, "fg_mult_cells": 0, "bg_mult_left": 0, "fg_mult_left": 0,
        "bg_mult_unused_spins": 0, "fg_mult_unused_spins": 0,
        "bg_gold_reel": Counter(), "fg_gold_reel": Counter(), "bg_gold_boards": 0, "fg_gold_boards": 0,
        "combo_bg": Counter(), "combo_fg": Counter(),
        "bg_symbol_length_pay": Counter(), "fg_symbol_length_pay": Counter(),
        "bg_mult_wild": 0, "fg_mult_wild": 0, "max_line_multiplier": 1,
        "bg_golden_results": Counter(), "fg_golden_results": Counter(),
        "bg_split_counts": Counter(), "fg_split_counts": Counter(),
        "mult_wild_values": Counter(), "bg_mult_kind": Counter(), "fg_mult_kind": Counter(),
        "symbol_hits": Counter(), "symbol_pay": Counter(),
        "bg_symbol_length_hits": Counter(), "fg_symbol_length_hits": Counter(),
        "bg_initial_symbols": Counter(), "bg_drop_symbols": Counter(),
        "fg_initial_symbols": Counter(), "fg_drop_symbols": Counter(),
        "retry_total": 0, "retry_limit_exceeded": 0, "retry_limit_bg_range": 0,
        "retry_limit_bg_freegame": 0, "retry_limit_fg": 0,
        "card_draws": Counter(),
        # Multiplier Line buckets
        "bucket_bg_cnt": [0] * buckets, "bucket_bg_pay": [0.0] * buckets,
        "bucket_fg_cnt": [0] * buckets, "bucket_fg_pay": [0.0] * buckets,
        "bucket_trigger_cnt": [0] * buckets, "bucket_trigger_pay": [0.0] * buckets,
        "bucket_fg_hit": [0] * buckets, "bucket_fg_spins": [0] * buckets,
        "bucket_bg_mult": [0] * buckets, "bucket_fg_mult": [0] * buckets,   # spins showing multipliers per range (final screen)
        "bucket_bg_combo": [[0] * 5 for _ in range(buckets)],
        "bucket_fg_combo": [[0] * 5 for _ in range(buckets)],
        "bucket_bg_golden": [Counter() for _ in range(buckets)],
        "bucket_fg_golden": [Counter() for _ in range(buckets)],
        "bucket_bg_gold_frames": [0] * buckets,
        "bucket_fg_gold_frames": [0] * buckets,
    }


def _accumulate(stats: dict[str, Any], result: RoundResult, wager: float,
                base_bet: float) -> None:
    stats["rounds"] += 1
    stats["coin_in"] += wager
    stats["pay_bg"] += result.pay_bg
    stats["pay_fg"] += result.pay_fg
    win_x = result.pay / wager
    stats["win_x_sum"] += win_x
    stats["win_x_square"] += win_x * win_x
    stats["max_win_x"] = max(stats["max_win_x"], win_x)
    stats["capped_rounds"] += int(result.capped)
    stats["bg_hit_spins"] += result.bg_hit_spins
    stats["fg_hit_spins"] += result.fg_hit_spins
    stats["fg_spins"] += result.fg_spins
    stats["fg_triggers"] += int(result.fg_triggered)
    stats["retriggers"] += result.retriggers
    stats["cascades_bg"] += result.cascades_bg
    stats["cascades_fg"] += result.cascades_fg
    stats["special_symbol_cnt"] += result.special_symbol_cnt
    stats["bg_trigger_fg_cnt"] += result.bg_trigger_fg_cnt
    stats["bg_trigger_fg_pay"] += result.bg_trigger_fg_pay
    stats["golden_converted"] += result.golden_converted
    stats["bg_gold_symbols"] += result.bg_gold_symbols
    stats["fg_gold_symbols"] += result.fg_gold_symbols
    stats["bg_gold_appeared"] += result.bg_gold_appeared
    stats["fg_gold_appeared"] += result.fg_gold_appeared
    for key in ("bg_flip_spins", "fg_flip_spins", "bg_mult_spins", "fg_mult_spins",
                "bg_mult_cells", "fg_mult_cells", "bg_mult_left", "fg_mult_left",
                "bg_mult_unused_spins", "fg_mult_unused_spins", "bg_big_spins", "fg_big_spins",
                "bg_big_used_spins", "fg_big_used_spins", "bg_gold_seen_spins", "fg_gold_seen_spins"):
        stats[key] += getattr(result, key)
    stats["bg_gold_boards"] += result.bg_gold_boards
    stats["fg_gold_boards"] += result.fg_gold_boards
    stats["combo_bg"][min(result.bg_cascade_count, 5)] += 1
    stats["combo_fg"].update(result.combo_fg)
    stats["bg_mult_wild"] += result.bg_mult_wild
    stats["fg_mult_wild"] += result.fg_mult_wild
    stats["max_line_multiplier"] = max(stats["max_line_multiplier"], result.max_line_multiplier)
    for key in ("bg_golden_results", "fg_golden_results", "bg_split_counts",
                "fg_split_counts", "mult_wild_values", "bg_mult_kind", "fg_mult_kind", "symbol_hits", "symbol_pay",
                "bg_symbol_length_hits", "fg_symbol_length_hits",
                "bg_symbol_length_pay", "fg_symbol_length_pay", "bg_gold_reel", "fg_gold_reel",
                "bg_initial_symbols", "bg_drop_symbols",
                "fg_initial_symbols", "fg_drop_symbols"):
        stats[key].update(getattr(result, key))

    if result.fg_triggered:
        # Games that trigger the Free Game belong to the Free Game card; their BG win only goes into bg_trigger_fg_*_lte_upper
        index = threshold_index(result.bg_trigger_fg_pay / base_bet)
        stats["bucket_trigger_cnt"][index] += 1
        stats["bucket_trigger_pay"][index] += result.bg_trigger_fg_pay
        fg_index = threshold_index(result.pay_fg / base_bet)
        stats["bucket_fg_cnt"][fg_index] += 1
        stats["bucket_fg_pay"][fg_index] += result.pay_fg
        stats["bucket_fg_spins"][fg_index] += result.fg_spins
        stats["bucket_fg_hit"][fg_index] += result.fg_hit_spins
        stats["bucket_fg_mult"][fg_index] += result.fg_mult_spins
        stats["bucket_fg_gold_frames"][fg_index] += result.fg_gold_symbols
        stats["bucket_fg_golden"][fg_index].update(result.fg_golden_results)
        for combo, count in result.combo_fg.items():
            stats["bucket_fg_combo"][fg_index][min(max(combo, 1), 5) - 1] += count
    else:
        index = threshold_index(result.pay_bg / base_bet)
        stats["bucket_bg_cnt"][index] += 1
        stats["bucket_bg_pay"][index] += result.pay_bg
        stats["bucket_bg_mult"][index] += result.bg_mult_spins
        stats["bucket_bg_gold_frames"][index] += result.bg_gold_symbols
        stats["bucket_bg_golden"][index].update(result.bg_golden_results)
        stats["bucket_bg_combo"][index][min(max(result.bg_cascade_count, 1), 5) - 1] += 1


def _merge_stats(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if isinstance(value, Counter):
            target[key].update(value)
        elif key == "max_win_x" or key == "max_line_multiplier":
            target[key] = max(target[key], value)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, Counter):
                    target[key][index].update(item)
                elif isinstance(item, list):
                    for sub, subvalue in enumerate(item):
                        target[key][index][sub] += subvalue
                else:
                    target[key][index] += item
        else:
            target[key] += value


def _simulate_chunk(rounds: int, bet_mode: int, base_bet: float, seed: int,
                    card_enabled: bool) -> dict[str, Any]:
    wager = wager_for_mode(bet_mode, base_bet)
    engine = SuperDiamond(CFG, CFG_RTP or None, seed, base_bet, card_enabled)
    stats = _empty_stats()
    for _ in range(rounds):
        _accumulate(stats, engine.round(), wager, base_bet)
    stats["retry_total"] = engine.retry_total
    stats["retry_limit_exceeded"] = engine.retry_limit_exceeded
    stats["retry_limit_bg_range"] = engine.retry_limit_bg_range
    stats["retry_limit_bg_freegame"] = engine.retry_limit_bg_freegame
    stats["retry_limit_fg"] = engine.retry_limit_fg
    stats["card_draws"].update(engine.card_draws)
    return stats


def _init_worker(cfg: dict[str, Any], cfg_rtp: dict[str, Any]) -> None:
    """Worker initializer: Windows starts workers with spawn, so the loaded config is passed in."""
    global CFG, CFG_RTP
    CFG, CFG_RTP = cfg, cfg_rtp


def run_simulation(total_rounds: int, bet_mode: int, base_bet: float, threads: int,
                   card_enabled: bool) -> dict[str, Any]:
    per_thread = [total_rounds // threads] * threads
    for index in range(total_rounds % threads):
        per_thread[index] += 1
    assert sum(per_thread) == total_rounds

    # Warm-up (not timed)
    _simulate_chunk(min(200, max(1, total_rounds)), bet_mode, base_bet,
                    RNG_SEED - 1, card_enabled)

    started = time.perf_counter()
    merged = _empty_stats()
    if threads == 1:
        merged = _simulate_chunk(total_rounds, bet_mode, base_bet, RNG_SEED, card_enabled)
    else:
        # Multiprocessing (a ThreadPool uses only one core because of the GIL); workers receive the config via initializer
        with ProcessPoolExecutor(max_workers=threads, initializer=_init_worker, initargs=(CFG, CFG_RTP)) as pool:
            futures = [
                pool.submit(_simulate_chunk, count, bet_mode, base_bet,
                            RNG_SEED + index * 7919, card_enabled)
                for index, count in enumerate(per_thread) if count > 0
            ]
            for future in futures:
                _merge_stats(merged, future.result())
    duration = time.perf_counter() - started
    return {"stats": merged, "duration": duration}


# ===== Report / Console =====

def mode_name(mode: int) -> str:
    return "Normal Bet"


def calculated_metrics(result: dict[str, Any]) -> dict[str, Any]:
    s = result["stats"]
    rounds = max(1, s["rounds"])
    coin_in = max(1e-12, s["coin_in"])
    pay_total = s["pay_bg"] + s["pay_fg"]
    mean = s["win_x_sum"] / rounds
    variance = max(0.0, s["win_x_square"] / rounds - mean * mean)
    fg_triggers = s["fg_triggers"]
    fg_spins = s["fg_spins"]
    special = int(s["special_symbol_cnt"])
    return {
        "rounds": s["rounds"],
        "coin_in_per_round": s["coin_in"] / rounds,
        "rtp_total": pay_total / coin_in,
        "rtp_link": 0.0,
        "rtp_bonus": 0.0,
        "rtp_game": pay_total / coin_in,
        "rtp_bg": s["pay_bg"] / coin_in,
        "rtp_fg": s["pay_fg"] / coin_in,
        "hit_rate_bg": s["bg_hit_spins"] / rounds,
        "hit_rate_fg": s["fg_hit_spins"] / max(1, fg_spins),
        "fg_trigger_rate": fg_triggers / rounds,
        "fg_trigger_cycle": rounds / fg_triggers if fg_triggers else math.inf,
        "retrigger_trigger_rate": s["retriggers"] / max(1, fg_spins),
        "retrigger_trigger_cycle": fg_spins / s["retriggers"] if s["retriggers"] else math.inf,
        "avg_fg_spins": fg_spins / fg_triggers if fg_triggers else 0.0,
        "special_symbol_cnt": special,
        "SCR": special / rounds * 10_000_000_000,
        "max_win_x": s["max_win_x"],
        "capped_rounds": s["capped_rounds"],
        "volatility_std": math.sqrt(variance),
        "standard_error": math.sqrt(variance) / math.sqrt(rounds),
    }


def _trigger_within_cap(s: dict[str, Any], section: str) -> tuple[int, float]:
    """Natural probability (card off): count and pay of Free Game triggering games whose BG win <= BG Trigger Cap (upper bound of the highest weighted base_game range)."""
    cards = card_section(CFG_RTP, section)
    caps = [float(c["max"]) for c in cards if c.get("type") == "range" and float(c.get("weight", 0)) > 0]
    cap = max(caps) if caps else math.inf
    idx = [i for i, upper in enumerate(MULTIPLIER_THRESHOLDS) if upper <= cap]
    return (int(sum(s["bucket_trigger_cnt"][i] for i in idx)), float(sum(s["bucket_trigger_pay"][i] for i in idx)))


def common_summary_sections(result: dict[str, Any]) -> list[list[tuple[str, Any]]]:
    s = result["stats"]
    m = calculated_metrics(result)
    # In the natural report, Free Game triggering games count only if their BG win <= BG Trigger Cap
    trigger_rows: list[tuple[str, Any]] = [("bg_trigger_fg_cnt", s["bg_trigger_fg_cnt"]),
                                           ("bg_trigger_fg_pay", s["bg_trigger_fg_pay"])]
    if not result["card_system_enabled"]:
        cnt, pay = _trigger_within_cap(s, "base_game")
        trigger_rows = [("bg_trigger_fg_cnt", cnt), ("bg_trigger_fg_pay", pay)]
    sections: list[list[tuple[str, Any]]] = [
        [("game_name", result["game_name"]), ("game_id", result["game_id"])],
        [("config_file", result["config_file"]),
         ("config_rtp_file", result["config_rtp_file"]),
         ("math_version", result["math_version"]),
         ("card_system", "on" if result["card_system_enabled"] else "off")],
        [("bet_mode", mode_name(result["bet_mode"])),
         ("bet_multi", result["bet_multi"]),
         ("base_bet", result["base_bet"]),
         ("bet_amount", result["bet_amount"]),
         ("coin_in", m["coin_in_per_round"]),
         ("total_rounds", s["rounds"]),
         ("duration", result["duration"])],
        [("rtp_total", m["rtp_total"]), ("rtp_link", m["rtp_link"]),
         ("rtp_bonus", m["rtp_bonus"]), ("rtp_game", m["rtp_game"]),
         ("rtp_bg", m["rtp_bg"]), ("rtp_fg", m["rtp_fg"]),
         ("hit_rate_bg", m["hit_rate_bg"]), ("hit_rate_fg", m["hit_rate_fg"]),
         ("fg_trigger_rate", (m["fg_trigger_rate"], m["fg_trigger_cycle"])),
         ("retrigger_trigger_rate", (m["retrigger_trigger_rate"], m["retrigger_trigger_cycle"])),
         ("avg_fg_spins", m["avg_fg_spins"])],
        [*trigger_rows,
         ("special_symbol_cnt", m["special_symbol_cnt"]),
         ("SCR", m["SCR"])],
        [("max_win_x", m["max_win_x"]), ("capped_rounds", m["capped_rounds"]),
         ("volatility_std", m["volatility_std"]), ("standard_error", m["standard_error"])],
    ]
    if result["card_system_enabled"]:
        sections.extend([
            [("card_retry_limit", CARD_RETRY_LIMIT),
             ("retry_total", s["retry_total"]),
             ("avg_retry", s["retry_total"] / max(1, s["rounds"]))],
            [("retry_limit_exceeded", s["retry_limit_exceeded"]),
             ("retry_limit_bg_range", s["retry_limit_bg_range"]),
             ("retry_limit_bg_freegame", s["retry_limit_bg_freegame"]),
             ("retry_limit_fg", s["retry_limit_fg"])],
        ])
    return sections


def game_info_rows(result: dict[str, Any]) -> list[tuple[str, Any]]:
    s = result["stats"]
    rounds = max(1, s["rounds"])
    fg_spins = max(1, s["fg_spins"])
    golden_total = max(1, sum(s["bg_golden_results"].values()) + sum(s["fg_golden_results"].values()))
    rows: list[tuple[str, Any]] = [
        ("avg_cascades_bg", s["cascades_bg"] / rounds),
        ("avg_cascades_fg", s["cascades_fg"] / fg_spins),
        ("mult_left_rate_bg", s["bg_mult_left"] / max(1, s["bg_mult_cells"])),
        ("mult_left_rate_fg", s["fg_mult_left"] / max(1, s["fg_mult_cells"])),
        ("mult_unused_spin_rate_bg", s["bg_mult_unused_spins"] / max(1, s["bg_mult_spins"])),
        ("mult_unused_spin_rate_fg", s["fg_mult_unused_spins"] / max(1, s["fg_mult_spins"])),
        ("avg_gold_frames_bg", s["bg_gold_symbols"] / rounds),
        ("avg_gold_frames_fg", s["fg_gold_symbols"] / fg_spins),
        ("golden_converted", s["golden_converted"]),
    ]
    # By-game indicators (per spin; BG = BG spins, FG = Free Game spins): appear rate = spins shown / total spins; use rate = spins used / spins shown
    for scene, spins in (("bg", rounds), ("fg", fg_spins)):
        rows.extend([
            (f"mult_seen_rate_{scene}", s[f"{scene}_mult_spins"] / spins),
            (f"mult_used_rate_{scene}", 1 - s[f"{scene}_mult_unused_spins"] / max(1, s[f"{scene}_mult_spins"])),
            (f"big_seen_rate_{scene}", s[f"{scene}_big_spins"] / spins),
            (f"big_used_rate_{scene}", s[f"{scene}_big_used_spins"] / max(1, s[f"{scene}_big_spins"])),
            (f"gold_seen_rate_{scene}", s[f"{scene}_gold_seen_spins"] / spins),
            (f"gold_used_rate_{scene}", s[f"{scene}_flip_spins"] / max(1, s[f"{scene}_gold_seen_spins"])),
        ])
    for key in GOLD_RESULTS:
        count = s["bg_golden_results"][key] + s["fg_golden_results"][key]
        rows.append((f"golden_result_{key}_share", count / golden_total))
    rows.extend([
        ("mult_wild_bg_rate", s["bg_mult_wild"] / rounds),
        ("mult_wild_fg_rate", s["fg_mult_wild"] / fg_spins),
        ("max_line_multiplier", s["max_line_multiplier"]),
    ])
    for value in sorted(s["mult_wild_values"]):
        total = max(1, sum(s["mult_wild_values"].values()))
        rows.append((f"mult_wild_x{value}_share", s["mult_wild_values"][value] / total))
    for scene in ("bg", "fg"):
        for kind, value in sorted(s[f"{scene}_mult_kind"]):
            rows.append((f"mult_{scene}_{kind}_x{value}", s[f"{scene}_mult_kind"][(kind, value)]))
    for count in sorted(k for k in set(s["bg_split_counts"]) | set(s["fg_split_counts"]) if k):
        rows.append((f"split_{count}_bg_rate", s["bg_split_counts"][count] / rounds))
        rows.append((f"split_{count}_fg_rate", s["fg_split_counts"][count] / fg_spins))
    return rows


COUNT_KEYS = {
    "total_rounds", "bg_trigger_fg_cnt", "special_symbol_cnt", "SCR", "retry_total",
    "retry_limit_exceeded", "retry_limit_bg_range", "retry_limit_bg_freegame",
    "retry_limit_fg", "golden_converted", "capped_rounds", "max_line_multiplier",
}


def _display_value(key: str, value: Any) -> str:
    if key == "duration":
        return f"{float(value):05.2f} sec"
    if key in COUNT_KEYS:
        return f"{int(value):,}"
    if key == "card_retry_limit":
        return str(int(value))
    if key == "bg_trigger_fg_pay":
        return f"{float(value):,.0f}"
    if key in {"coin_in", "base_bet", "bet_amount"}:
        return f"{float(value):.2f}"
    if key in {"fg_trigger_rate", "retrigger_trigger_rate"}:
        rate, cycle = value
        unit = "spins" if key == "fg_trigger_rate" else "free spins"
        cycle_text = "N/A" if not math.isfinite(float(cycle)) else f"{float(cycle):.2f} {unit}"
        return f"{float(rate):.4%} (cycle {cycle_text})"
    if key.startswith("rtp_") or key in {"hit_rate_bg", "hit_rate_fg"} or key.endswith("_share"):
        return f"{float(value):.4%}"
    if key.endswith("_rate"):
        return f"{float(value):.6%}"
    if key == "avg_fg_spins":
        return f"{float(value):.2f} spins"
    if key == "max_win_x":
        return f"{float(value):,.2f} x"
    if key in {"avg_retry", "volatility_std", "standard_error"}:
        return f"{float(value):05.2f}"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def overview_rows(result: dict[str, Any]) -> list[tuple[str, str]]:
    flat = [row for section in common_summary_sections(result) for row in section]
    return [(key, _display_value(key, value)) for key, value in flat + game_info_rows(result)]


def print_console(result: dict[str, Any]) -> None:
    for section in common_summary_sections(result):
        for key, value in section:
            print(f"{key:<28}{_display_value(key, value)}")
        print()
    print("<< By Game Info >>")
    for key, value in game_info_rows(result):
        print(f"{key:<28}{_display_value(key, value)}")
    print()


def multiplier_line_frame(result: dict[str, Any]) -> pd.DataFrame:
    s = result["stats"]
    rows = []
    trigger_cnt_cum = 0
    trigger_pay_cum = 0.0
    for index, upper in enumerate(MULTIPLIER_THRESHOLDS):
        if index == 0:
            interval = "0"
        else:
            interval = f"{float(MULTIPLIER_THRESHOLDS[index - 1]):.1f} < X <= {float(upper):.1f}"
        trigger_cnt_cum += s["bucket_trigger_cnt"][index]
        trigger_pay_cum += s["bucket_trigger_pay"][index]
        row: dict[str, Any] = {
            "Interval": interval,
            "base_game_cnt": s["bucket_bg_cnt"][index],
            "base_game_pay": s["bucket_bg_pay"][index],
            "free_game_cnt": s["bucket_fg_cnt"][index],
            "free_game_pay": s["bucket_fg_pay"][index],
        }
        row["Interval_Upper"] = upper
        row["bg_trigger_fg_cnt_lte_upper"] = trigger_cnt_cum
        row["bg_trigger_fg_pay_lte_upper"] = trigger_pay_cum
        fg_spins = s["bucket_fg_spins"][index]
        row["FG_Hit_Rate"] = s["bucket_fg_hit"][index] / fg_spins if fg_spins else 0.0
        row["FG_Spin_Count"] = fg_spins
        # Multiplier appear rate per range (final screen): BG = BG games in the range, FG = total spins of Free Games in the range
        row["BG_Mult_Seen_Rate"] = s["bucket_bg_mult"][index] / s["bucket_bg_cnt"][index] if s["bucket_bg_cnt"][index] else 0.0
        row["FG_Mult_Seen_Rate"] = s["bucket_fg_mult"][index] / fg_spins if fg_spins else 0.0

        bg_combo_total = max(1, sum(s["bucket_bg_combo"][index]))
        for combo in range(5):
            label = f"BG_Combo_{combo + 1}{'+' if combo == 4 else ''}_Rate"
            row[label] = s["bucket_bg_combo"][index][combo] / bg_combo_total
        fg_combo_total = max(1, sum(s["bucket_fg_combo"][index]))
        for combo in range(5):
            label = f"FG_Combo_{combo + 1}{'+' if combo == 4 else ''}_Rate"
            row[label] = s["bucket_fg_combo"][index][combo] / fg_combo_total

        # --- By Game ---
        bg_gold = s["bucket_bg_golden"][index]
        bg_gold_total = max(1, sum(bg_gold.values()))
        for key in GOLD_RESULTS:
            row[f"BG_Golden_{key}_Rate"] = bg_gold[key] / bg_gold_total
        fg_gold = s["bucket_fg_golden"][index]
        fg_gold_total = max(1, sum(fg_gold.values()))
        for key in GOLD_RESULTS:
            row[f"FG_Golden_{key}_Rate"] = fg_gold[key] / fg_gold_total
        bg_cnt = max(1, s["bucket_bg_cnt"][index])
        row["BG_Avg_Gold_Frames"] = s["bucket_bg_gold_frames"][index] / bg_cnt
        row["FG_Avg_Gold_Frames"] = s["bucket_fg_gold_frames"][index] / max(1, fg_spins)
        rows.append(row)
    return pd.DataFrame(rows)


def symbol_frame(result: dict[str, Any]) -> pd.DataFrame:
    s = result["stats"]
    names = CFG["symbol_names"]
    total_hits = max(1, sum(s["symbol_hits"].values()))
    total_pay = max(1e-12, sum(s["symbol_pay"].values()))
    rows = []
    for symbol in SCORE_SYMBOLS:
        rows.append({
            "symbol_id": symbol,
            "symbol": names[str(symbol)],
            "ways_hits": s["symbol_hits"][symbol],
            "hit_share": s["symbol_hits"][symbol] / total_hits,
            "pay": s["symbol_pay"][symbol],
            "pay_share": s["symbol_pay"][symbol] / total_pay,
            "hits_3": s["bg_symbol_length_hits"][(symbol, 3)] + s["fg_symbol_length_hits"][(symbol, 3)],
            "hits_4": s["bg_symbol_length_hits"][(symbol, 4)] + s["fg_symbol_length_hits"][(symbol, 4)],
            "hits_5": s["bg_symbol_length_hits"][(symbol, 5)] + s["fg_symbol_length_hits"][(symbol, 5)],
        })
    return pd.DataFrame(rows)


def feature_frame(result: dict[str, Any]) -> pd.DataFrame:
    s = result["stats"]
    rounds = max(1, s["rounds"])
    fg_spins = max(1, s["fg_spins"])
    rows = [
        ("golden_converted_total", s["golden_converted"]),
        ("golden_per_round", s["golden_converted"] / rounds),
        ("flip_spins_bg", s["bg_flip_spins"]), ("flip_spins_fg", s["fg_flip_spins"]),
        ("mult_spins_bg", s["bg_mult_spins"]), ("mult_spins_fg", s["fg_mult_spins"]),
        ("mult_cells_bg", s["bg_mult_cells"]), ("mult_cells_fg", s["fg_mult_cells"]),
        ("mult_left_bg", s["bg_mult_left"]), ("mult_left_fg", s["fg_mult_left"]),
        ("mult_unused_spins_bg", s["bg_mult_unused_spins"]), ("mult_unused_spins_fg", s["fg_mult_unused_spins"]),
        ("mult_left_rate_bg", s["bg_mult_left"] / max(1, s["bg_mult_cells"])),
        ("mult_left_rate_fg", s["fg_mult_left"] / max(1, s["fg_mult_cells"])),
        ("mult_unused_spin_rate_bg", s["bg_mult_unused_spins"] / max(1, s["bg_mult_spins"])),
        ("mult_unused_spin_rate_fg", s["fg_mult_unused_spins"] / max(1, s["fg_mult_spins"])),
        ("gold_board_rate_bg", s["bg_gold_boards"] / rounds),
        ("gold_board_rate_fg", s["fg_gold_boards"] / fg_spins),
        *[(f"gold_reel_bg_R{reel + 1}", s["bg_gold_reel"][reel] / rounds / 4) for reel in range(5)],
        *[(f"gold_reel_fg_R{reel + 1}", s["fg_gold_reel"][reel] / fg_spins / 4) for reel in range(5)],
        ("gold_appeared_bg", s["bg_gold_appeared"]),
        ("gold_appeared_fg", s["fg_gold_appeared"]),
        ("gold_usage_bg", sum(s["bg_golden_results"].values()) / max(1, s["bg_gold_appeared"])),
        ("gold_usage_fg", sum(s["fg_golden_results"].values()) / max(1, s["fg_gold_appeared"])),
        ("mult_wild_created_bg", s["bg_mult_wild"]),
        ("mult_wild_created_fg", s["fg_mult_wild"]),
        ("mult_wild_per_round", (s["bg_mult_wild"] + s["fg_mult_wild"]) / rounds),
        ("max_line_multiplier", s["max_line_multiplier"]),
        ("max_win_x", s["max_win_x"]),
        ("capped_rounds", s["capped_rounds"]),
        ("avg_cascades_bg", s["cascades_bg"] / rounds),
        ("avg_cascades_fg", s["cascades_fg"] / fg_spins),
    ]
    for key in GOLD_RESULTS:
        rows.append((f"golden_{key}_bg", s["bg_golden_results"][key]))
        rows.append((f"golden_{key}_fg", s["fg_golden_results"][key]))
    for value in sorted(s["mult_wild_values"]):
        rows.append((f"mult_wild_x{value}", s["mult_wild_values"][value]))
    for count in sorted(k for k in set(s["bg_split_counts"]) | set(s["fg_split_counts"])):
        rows.append((f"split_{count}_bg", s["bg_split_counts"][count]))
        rows.append((f"split_{count}_fg", s["fg_split_counts"][count]))
    return pd.DataFrame(rows, columns=["Index", "Value"])


# ===== Report file name =====

def format_rounds_tag(total_rounds: int) -> str:
    exponent = round(math.log10(total_rounds)) if total_rounds > 0 else 0
    if 10 ** exponent == total_rounds:
        return f"10{exponent}"
    return str(total_rounds)


def format_base_version_tag(version: Any) -> str:
    text = str(version)
    if not text.isdigit() or len(text) != 1:
        raise ValueError(f"shared model version must have 1 part, got {version!r}")
    return text.zfill(2)


def format_rtp_version_tag(version: Any) -> str:
    parts = str(version).split(".")
    if len(parts) != 4:
        raise ValueError(f"RTP version must have 4 parts, got {version!r}")
    out = ""
    for part in parts:
        if not part.isdigit() or len(part) > 2:
            raise ValueError(f"version part {part!r} has more than 2 digits; fix the version before writing the report")
        out += part.zfill(2)
    return out


def format_rtp_tag(rtp_ratio: float) -> str:
    return f"{rtp_ratio * 100:.4f}".replace(".", "")[:4]


def report_filename(result: dict[str, Any], timestamp: datetime | None = None) -> str:
    stamp = (timestamp or datetime.now()).strftime("%y%m%d%H%M")
    rounds_tag = format_rounds_tag(result["stats"]["rounds"])
    bet_mode = result["bet_mode"]
    if not result["card_system_enabled"]:
        game_id = f"{CFG['parsheet_id']}"
        version_tag = format_base_version_tag(CFG["excel_version"])
        return f"{game_id}_{version_tag}_{stamp}_betmode{bet_mode}_{rounds_tag}.xlsx"
    rtp_game_id = str(CFG_RTP.get("parsheet_id") or CFG_RTP.get("game_id"))
    version_tag = format_rtp_version_tag(CFG_RTP["excel_version"])
    rtp_tag = format_rtp_tag(calculated_metrics(result)["rtp_total"])
    parts = [rtp_game_id, version_tag, stamp, f"betmode{bet_mode}", rounds_tag, rtp_tag, "card"]
    return "_".join(parts) + ".xlsx"


def output_report(result: dict[str, Any], output_dir: Path | None = None) -> Path:
    directory = output_dir or (BASE_DIR / "Record")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / report_filename(result)
    overview = pd.DataFrame(overview_rows(result), columns=["Index", "Value"])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        overview.to_excel(writer, sheet_name="Overview", index=False)
        multiplier_line_frame(result).to_excel(writer, sheet_name="Multiplier Line", index=False)
        feature_frame(result).to_excel(writer, sheet_name="Feature", index=False)
        symbol_frame(result).to_excel(writer, sheet_name="Symbol", index=False)
        eliminate_frame(result).to_excel(writer, sheet_name="Eliminate", index=False)
        symbol_length_frame(result).to_excel(writer, sheet_name="Symbol Length", index=False)
    return path


def eliminate_frame(result: dict[str, Any]) -> pd.DataFrame:
    """Cascade count distribution: per BG game and per Free Game spin."""
    s = result["stats"]
    rows = [(("5+" if k == 5 else str(k)), s["combo_bg"].get(k, 0), s["combo_fg"].get(k, 0)) for k in range(6)]
    return pd.DataFrame(rows, columns=["combo", "BG", "FG"])


def symbol_length_frame(result: dict[str, Any]) -> pd.DataFrame:
    """Hits and pay of 3 / 4 / 5 of a kind per symbol."""
    s = result["stats"]
    names = CFG["symbol_names"]
    rows = []
    for scene, hits_key, pay_key in (("BG", "bg_symbol_length_hits", "bg_symbol_length_pay"),
                                     ("FG", "fg_symbol_length_hits", "fg_symbol_length_pay")):
        for symbol in SCORE_SYMBOLS:
            for length in (3, 4, 5):
                rows.append((scene, names[str(symbol)], length,
                             s[hits_key][(symbol, length)], s[pay_key][(symbol, length)]))
    return pd.DataFrame(rows, columns=["scene", "symbol", "length", "hits", "pay"])


# ===== Runner =====

def build_result(stats_bundle: dict[str, Any], combo: dict[str, Any]) -> dict[str, Any]:
    bet_mode = int(combo["bet_mode"])
    base_bet = float(combo["base_bet"])
    bet_amount = wager_for_mode(bet_mode, base_bet)
    return {
        "stats": stats_bundle["stats"],
        "duration": stats_bundle["duration"],
        "game_name": CFG["name_en"],
        "game_id": CFG["online_game_id"],
        "parsheet_id": CFG["parsheet_id"],
        "config_file": combo["config_file"],
        "config_rtp_file": combo["config_rtp_file"] if CFG_RTP else f"{combo['config_rtp_file']} (not found)",
        "math_version": CFG_RTP.get("excel_version", CFG["excel_version"]),
        "card_system_enabled": bool(combo["card_system_enabled"]) and bool(CFG_RTP),
        "bet_mode": bet_mode,
        "bet_multi": int(round(bet_amount / base_bet)),
        "base_bet": base_bet,
        "bet_amount": bet_amount,
    }


def load_batch_configs(combo: dict[str, Any]) -> None:
    global CFG, CFG_RTP
    CFG = load_js_config(BASE_DIR / combo["config_file"])
    rtp_path = BASE_DIR / combo["config_rtp_file"]
    CFG_RTP = load_js_config(rtp_path) if rtp_path.exists() else {}
    validate_config_pair(CFG, CFG_RTP or None, combo["config_file"], combo["config_rtp_file"])
    if not CFG_RTP and combo["card_system_enabled"]:
        print(f"[warn] {combo['config_rtp_file']} not found; this batch runs with the card system off.")


def validate_batch_run(combo: dict[str, Any]) -> dict[str, Any]:
    required = {"config_file", "config_rtp_file", "bet_mode", "total_rounds",
                "card_system_enabled", "base_bet"}
    missing = required - set(combo)
    if missing:
        raise ValueError(f"BATCH_RUNS is missing fields: {sorted(missing)}")
    if int(combo["bet_mode"]) not in SUPPORTED_BET_MODES:
        raise ValueError(f"unsupported bet_mode {combo['bet_mode']}; only 0 (Normal Bet) is supported")
    if int(combo["total_rounds"]) <= 0:
        raise ValueError("total_rounds must be a positive integer")
    if float(combo["base_bet"]) <= 0:
        raise ValueError("base_bet must be greater than 0")
    return combo


def format_board(symbols: list[list[int]], mults: list[list[int]] | None = None) -> str:
    names = CFG["symbol_names"]
    lines = []
    for row in range(4):
        cells = []
        for reel in range(5):
            text = names[str(symbols[reel][row])]
            if mults and mults[reel][row]:
                text += f"x{mults[reel][row]}"
            cells.append(f"{text:>7}")
        lines.append(" ".join(cells))
    return "\n".join(lines)


def run_single_spin_debug() -> None:
    engine = SuperDiamond(CFG, CFG_RTP or None, RNG_SEED, 1.0, False)
    for index in range(DEBUG_ROUNDS):
        result = engine.round()
        print(f"--- debug round {index + 1} ---")
        print(f"pay_bg={result.pay_bg:.4f} pay_fg={result.pay_fg:.4f} "
              f"cascades_bg={result.cascades_bg} fg_spins={result.fg_spins} "
              f"golden={result.golden_converted} mult_wild={result.bg_mult_wild + result.fg_mult_wild} "
              f"max_line_mult={result.max_line_multiplier} capped={result.capped}")


def run_batch(combo: dict[str, Any], index: int, total: int) -> None:
    validate_batch_run(combo)
    load_batch_configs(combo)
    print(f"=== Batch {index}/{total}: {combo} ===")
    card_enabled = bool(combo["card_system_enabled"]) and bool(CFG_RTP)
    bundle = run_simulation(int(combo["total_rounds"]), int(combo["bet_mode"]),
                            float(combo["base_bet"]), THREADS,
                            card_enabled)
    result = build_result(bundle, combo)
    if SHOW_CONSOLE_SUMMARY:
        print_console(result)
    if OUTPUT_REPORT:
        path = output_report(result)
        print(f"report -> {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="H045 Lucky Diamond simulator")
    parser.add_argument("--rounds", type=int, default=None)
    parser.add_argument("--bet-mode", type=int, default=None)
    parser.add_argument("--base-bet", type=float, default=None)
    parser.add_argument("--threads", type=int, default=None)
    parser.add_argument("--no-report", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--card-on", action="store_true", help="Card System On (needs config_rtp_file)")
    parser.add_argument("--card-off", action="store_true", help="Card System Off")
    parser.add_argument("--config-rtp", default=None, help="override config_rtp_file, e.g. config_94.js")
    parser.add_argument("--config", default=None, help="override config_file")
    parser.add_argument("--seed", type=int, default=None, help="override RNG_SEED (use a different seed for re-checks)")
    return parser.parse_args()


def main() -> None:
    global RNG_SEED
    global THREADS, OUTPUT_REPORT
    args = parse_args()
    if args.seed is not None:
        RNG_SEED = args.seed
    if args.threads:
        THREADS = max(1, args.threads)
    if args.no_report:
        OUTPUT_REPORT = False

    runs = [dict(run) for run in BATCH_RUNS] if RUN_ALL_COMBINATIONS else [{
        "config_file": CONFIG_FILE, "config_rtp_file": CONFIG_RTP_FILE,
        "bet_mode": BET_MODE, "total_rounds": TOTAL_ROUNDS,
        "card_system_enabled": CARD_SYSTEM_ENABLED,
        "base_bet": BASE_BET_SETTING,
    }]
    for run in runs:
        if args.rounds:
            run["total_rounds"] = args.rounds
        if args.bet_mode is not None:
            run["bet_mode"] = args.bet_mode
        if args.base_bet:
            run["base_bet"] = args.base_bet
        if args.card_on:
            run["card_system_enabled"] = True
        if args.card_off:
            run["card_system_enabled"] = False
        if args.config_rtp:
            run["config_rtp_file"] = args.config_rtp
        if args.config:
            run["config_file"] = args.config

    if args.debug or RUN_SINGLE_SPIN_DEBUG:
        load_batch_configs(runs[0])
        run_single_spin_debug()
        return

    for index, run in enumerate(runs, start=1):
        run_batch(run, index, len(runs))


if __name__ == "__main__":
    main()
