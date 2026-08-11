"""H016 幸運王牌 simulator.

The runner, environment settings, batch workflow and Excel report layout follow
H015.  The game engine follows 101003 and reads H0161.xlsx directly (legacy JS
configs remain supported):
5x4 Ways, cascades, golden-symbol retention, WW/W2 conversion and fixed combo
multipliers.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
import os
import random
import re
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import load_workbook

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

# ===== User Settings (H015-compatible runner) =====

CONFIG_FILE = "Source/H0161.xlsx"
TOTAL_ROUNDS = 100_000
BET_MULTI = 1
BET_MODE = 0  # 0=Normal Bet, 2=Buy Feature, 3=Buy Super Feature
CARD_SYSTEM_ENABLED = True
CARD_SYSTEM_IS_NEWBIE = False

RUN_ALL_COMBINATIONS = True
BATCH_RUNS = [
    # {"config_file": "config_92.js", "bet_mode": 0, "total_rounds": 10**4, "card_system_enabled": False, "card_system_is_newbie": False},
    {"config_file": "config_92.js", "bet_mode": 0, "total_rounds": 10**5, "card_system_enabled": True, "card_system_is_newbie": False},
]
THREADS = max(1, min(8, os.cpu_count() or 1))
OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = True
SHOW_CONSOLE_DETAIL = False
RUN_SINGLE_SPIN_DEBUG = False
DEBUG_ROUNDS = 1
CARD_RETRY_LIMIT = 200_000

BASE_BET = 100.0
MODE_NORMALBET = 0
MODE_FEATUREBUY = 2
MODE_SUPERBUY = 3
SUPPORTED_BET_MODES = (MODE_NORMALBET, MODE_FEATUREBUY, MODE_SUPERBUY)
WW = 0
W2 = 1
C1 = 2
SCORE_SYMBOLS = tuple(range(3, 11))
GOLD_MIN = 11
GOLD_MAX = 18


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    value = value.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true/false, got {value!r}")


CONFIG_FILE = os.environ.get("H016_CONFIG_FILE", CONFIG_FILE)


def _load_config(path: Path) -> dict[str, Any]:
    if path.suffix.lower() in {".xlsx", ".xlsm"}:
        return _load_xlsx_config(path)
    raw = path.read_text(encoding="utf-8-sig")
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        raise ValueError(f"Config does not contain a JSON object: {path}")
    return json.loads(raw[start : end + 1])


def _xlsx_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric, got {value!r}")
    return float(value)


def _xlsx_table(ws, name_to_id: dict[str, int], multipliers: list[int]) -> dict[str, Any]:
    reels: list[list[int]] = [[] for _ in range(5)]
    weights: list[list[float]] = [[] for _ in range(5)]
    for row_number, row_values in enumerate(ws.iter_rows(min_row=4, max_row=403, max_col=27, values_only=True), start=4):
        for reel in range(5):
            symbol_name = row_values[10 + reel]
            if symbol_name in (None, ""):
                continue
            if symbol_name not in name_to_id:
                raise ValueError(f"{ws.title} R{reel + 1} row {row_number}: unknown symbol {symbol_name!r}")
            reels[reel].append(name_to_id[str(symbol_name)])
            weights[reel].append(_xlsx_number(row_values[22 + reel], f"{ws.title} R{reel + 1} weight row {row_number}"))
    if any(not reel for reel in reels):
        raise ValueError(f"{ws.title}: five non-empty reels are required")
    if any(sum(reel_weights) <= 0 for reel_weights in weights):
        raise ValueError(f"{ws.title}: each reel must have positive total weight")

    random_values = [int(_xlsx_number(ws.cell(row, 29).value, f"{ws.title} Random Wild value")) for row in range(4, 8)]
    random_weights = [_xlsx_number(ws.cell(row, 30).value, f"{ws.title} Random Wild weight") for row in range(4, 8)]
    if random_values != [0, 2, 3, 4] or len(random_values) != len(random_weights):
        raise ValueError(f"{ws.title}: Random Wild must define 0/2/3/4 and matching weights")

    fill_symbols: list[list[int]] = [[] for _ in range(5)]
    fill_weights: list[list[float]] = [[] for _ in range(5)]
    for row in range(4, 13):
        symbol_name = ws.cell(row, 32).value
        if symbol_name in (None, ""):
            continue
        if str(symbol_name) not in name_to_id:
            raise ValueError(f"{ws.title} AF{row}: unknown fill symbol {symbol_name!r}")
        symbol_id = name_to_id[str(symbol_name)]
        for reel in range(5):
            fill_symbols[reel].append(symbol_id)
            fill_weights[reel].append(_xlsx_number(ws.cell(row, 33 + reel).value, f"{ws.title} fill R{reel + 1}"))
    if any(not symbols for symbols in fill_symbols):
        fill_symbols = [reel[:] for reel in reels]
        fill_weights = [[1.0] * len(reel) for reel in reels]

    gold_overlay = [
        _xlsx_number(ws.cell(4, 40 + reel).value or 0, f"{ws.title} gold overlay R{reel + 1}")
        for reel in range(5)
    ]
    scatter_suppression = _xlsx_number(ws["AU3"].value or 0, f"{ws.title} scatter suppression")
    return {
        "reels": reels,
        "weights": weights,
        "fill_symbols": fill_symbols,
        "fill_weights": fill_weights,
        "random_wild": {"values": random_values, "weights": random_weights},
        "gold_overlay": gold_overlay,
        "scatter_suppression": scatter_suppression,
        "multipliers": multipliers,
    }


def _load_xlsx_config(path: Path) -> dict[str, Any]:
    workbook = load_workbook(path, read_only=True, data_only=False)
    required_sheets = {"Overview", "Parameter", "BG_Symbol", "FG_Symbol"}
    missing = required_sheets.difference(workbook.sheetnames)
    if missing:
        raise ValueError(f"{path.name}: missing sheets {sorted(missing)}")
    overview = workbook["Overview"]
    parameter = workbook["Parameter"]

    base_bet = _xlsx_number(overview["A7"].value, "Overview!A7 Base Bet")
    symbol_names: dict[str, str] = {}
    name_to_id: dict[str, int] = {}
    for row in range(29, 48):
        name = overview.cell(row, 1).value
        symbol_id = overview.cell(row, 8).value
        if name in (None, "") or symbol_id in (None, ""):
            continue
        numeric_id = int(_xlsx_number(symbol_id, f"Overview!H{row}"))
        symbol_names[str(numeric_id)] = str(name)
        name_to_id[str(name)] = numeric_id
    expected_ids = set(range(19))
    if set(map(int, symbol_names)) != expected_ids:
        raise ValueError(f"{path.name}: Overview symbol ids must be 0..18")

    pays: dict[str, list[float]] = {}
    for row in range(32, 40):
        symbol_id = int(_xlsx_number(overview.cell(row, 8).value, f"Overview!H{row}"))
        pays[str(symbol_id)] = [
            _xlsx_number(overview.cell(row, col).value, f"Overview pay row {row}") / base_bet
            for col in (5, 6, 7)
        ]

    bg_multipliers = [1, 2, 3, 5]
    fg_multipliers = [2, 4, 6, 10]
    bg_table = _xlsx_table(workbook["BG_Symbol"], name_to_id, bg_multipliers)
    fg_table = _xlsx_table(workbook["FG_Symbol"], name_to_id, fg_multipliers)
    # Parameter selects BG_Symbol/FG_Symbol at weight 1.  Aliases keep the
    # existing engine paths usable without touching the zero-weight sheets.
    tables = {
        "bg_high": bg_table,
        "bg_low": bg_table,
        "buy": bg_table,
        "fg_high_a": fg_table,
        "fg_high_k": fg_table,
        "fg_high_q": fg_table,
        "fg_high_j": fg_table,
        "fg_low": fg_table,
        "super": fg_table,
    }

    return {
        "game_id": "H016",
        "parsheet_id": str(overview["B2"].value or path.stem),
        "name_zh": "幸運王牌",
        "rtp_label": None,
        "reel_num": 5,
        "window_size": 4,
        "max_ways": 1024,
        "symbol_names": symbol_names,
        "pays": pays,
        "tables": tables,
        "free_game_mix": {
            "choices": [{"high": int(_xlsx_number(overview["B21"].value, "Overview!B21")), "low": 0, "weight": 1}],
            "high_variant_weights": [1, 0, 0, 0],
        },
        "free_spins": int(_xlsx_number(overview["B21"].value, "Overview!B21")),
        "retrigger_spins": int(_xlsx_number(overview["C21"].value, "Overview!C21")),
        "free_spin_cap": 50,
        "buy_price": _xlsx_number(overview["B12"].value, "Overview!B12"),
        "super_buy_price": 250.0,
        "card_system": {"enabled": False, "profiles": {}},
        "source_xlsx": path.name,
    }


def _is_h016_config(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        data = _load_config(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    required = {"tables", "symbol_names", "pays", "free_game_mix"}
    return str(data.get("game_id")) == "H016" and required.issubset(data)


def resolve_base_dir() -> Path:
    """Locate H016 safely when run as a file, `%run`, or a Notebook cell."""
    cwd = Path.cwd().resolve()
    candidates: list[Path] = []
    override = os.environ.get("H016_BASE_DIR")
    if override:
        candidates.append(Path(override).expanduser())

    file_value = globals().get("__file__")
    if file_value and not str(file_value).startswith("<"):
        candidates.append(Path(file_value).resolve().parent)
    candidates.append(cwd)

    for parent in (cwd, *cwd.parents):
        candidates.extend(
            [
                parent / "Project" / "Slots" / "H016_幸運王牌",
                parent / "Project_AI" / "Slots" / "H016_幸運王牌",
                parent / "Slots" / "H016_幸運王牌",
            ]
        )

    checked: list[Path] = []
    for candidate in candidates:
        try:
            candidate = candidate.resolve()
        except OSError:
            continue
        if candidate in checked:
            continue
        checked.append(candidate)
        if _is_h016_config(candidate / CONFIG_FILE):
            return candidate

    locations = "\n  - ".join(str(path / CONFIG_FILE) for path in checked)
    raise FileNotFoundError(f"Cannot locate a valid H016 {CONFIG_FILE}. Checked:\n  - {locations}\n" "Set H016_BASE_DIR to the H016_幸運王牌 folder when running from another workspace.")


BASE_DIR = resolve_base_dir()
OUTPUT_DIR = BASE_DIR / "Record"
SIMULATOR_PATH = BASE_DIR / "Simulator.py"
TOTAL_ROUNDS = int(os.environ.get("H016_TOTAL_ROUNDS", TOTAL_ROUNDS))
BET_MULTI = int(os.environ.get("H016_BET_MULTI", BET_MULTI))
BET_MODE = int(os.environ.get("H016_BET_MODE", BET_MODE))
CARD_SYSTEM_ENABLED = _env_bool("H016_CARD_SYSTEM_ENABLED", CARD_SYSTEM_ENABLED)
CARD_SYSTEM_IS_NEWBIE = _env_bool("H016_CARD_SYSTEM_IS_NEWBIE", CARD_SYSTEM_IS_NEWBIE)
RUN_ALL_COMBINATIONS = _env_bool("H016_RUN_ALL_COMBINATIONS", RUN_ALL_COMBINATIONS)
OUTPUT_REPORT = _env_bool("H016_OUTPUT_REPORT", OUTPUT_REPORT)
SHOW_CONSOLE_SUMMARY = _env_bool("H016_SHOW_CONSOLE_SUMMARY", SHOW_CONSOLE_SUMMARY)
SHOW_CONSOLE_DETAIL = _env_bool("H016_SHOW_CONSOLE_DETAIL", SHOW_CONSOLE_DETAIL)
RUN_SINGLE_SPIN_DEBUG = _env_bool("H016_RUN_SINGLE_SPIN_DEBUG", RUN_SINGLE_SPIN_DEBUG)
THREADS = max(1, int(os.environ.get("H016_THREADS", THREADS)))
CFG = _load_config(BASE_DIR / CONFIG_FILE)
CARD_SYSTEM_ENABLED = CARD_SYSTEM_ENABLED and bool(CFG.get("card_system", {}).get("enabled"))
GAME_ID = str(CFG.get("game_id", "H016"))
PARSHEET_ID = str(CFG.get("parsheet_id", "H016192"))
GAME_NAME = str(CFG.get("name_zh", "幸運王牌"))
SYMBOL_STR = {int(k): v for k, v in CFG["symbol_names"].items()}


def canonical(symbol: int) -> int:
    return symbol - 8 if GOLD_MIN <= symbol <= GOLD_MAX else symbol


def weighted_pick(rng: random.Random, values: list[Any], weights: list[float]) -> Any:
    total = sum(max(0.0, float(w)) for w in weights)
    if not values:
        raise ValueError("No values available for weighted selection")
    if total <= 0:
        return values[0]
    target = rng.random() * total
    for value, weight in zip(values, weights):
        target -= max(0.0, float(weight))
        if target < 0:
            return value
    return values[-1]


@dataclass
class Reel:
    symbols: list[int]
    stop_cumulative: list[float]
    stop_total: float
    fill_symbols: list[int]
    fill_cumulative: list[float]
    fill_total: float

    @staticmethod
    def _index(rng: random.Random, cumulative: list[float], total: float) -> int:
        position = rng.random() * total
        return min(bisect.bisect_left(cumulative, position), len(cumulative) - 1)

    def window(self, rng: random.Random, size: int) -> list[int]:
        stop = self._index(rng, self.stop_cumulative, self.stop_total)
        return [self.symbols[(stop + offset) % len(self.symbols)] for offset in range(size)]

    def pick_fill(self, rng: random.Random) -> int:
        return self.fill_symbols[self._index(rng, self.fill_cumulative, self.fill_total)]


@dataclass
class Table:
    reels: list[Reel]
    random_wild_values: list[int]
    random_wild_weights: list[float]
    gold_overlay: list[float]
    scatter_suppression: float
    multipliers: list[int]


@dataclass
class SpinResult:
    pay: float = 0.0
    scatter_count: int = 0
    cascades: int = 0
    max_multiplier: int = 1
    golden_converted: int = 0
    w2_events: int = 0
    m1_present: bool = False
    symbol_hits: Counter = field(default_factory=Counter)
    symbol_pay: Counter = field(default_factory=Counter)
    initial_symbols: Counter = field(default_factory=Counter)
    drop_symbols: Counter = field(default_factory=Counter)
    initial_board: list[list[int]] = field(default_factory=list)
    final_board: list[list[int]] = field(default_factory=list)


@dataclass
class RoundResult:
    pay_bg: float = 0.0
    pay_fg: float = 0.0
    fg_triggered: bool = False
    fg_spins: int = 0
    retriggers: int = 0
    cascades_bg: int = 0
    cascades_fg: int = 0
    max_multiplier: int = 1
    golden_converted: int = 0
    w2_events: int = 0
    bg_w2_events: int = 0
    fg_w2_events: int = 0
    bg_m1_spins: int = 0
    fg_m1_spins: int = 0
    combo_fg: Counter = field(default_factory=Counter)
    symbol_hits: Counter = field(default_factory=Counter)
    symbol_pay: Counter = field(default_factory=Counter)
    bg_initial_symbols: Counter = field(default_factory=Counter)
    bg_drop_symbols: Counter = field(default_factory=Counter)
    fg_initial_symbols: Counter = field(default_factory=Counter)
    fg_drop_symbols: Counter = field(default_factory=Counter)

    @property
    def pay(self) -> float:
        return self.pay_bg + self.pay_fg


class LuckyAce:
    def __init__(self, config: dict[str, Any], seed: int, card_enabled: bool, newbie: bool):
        self.config = config
        self.rng = random.Random(seed)
        self.card_enabled = card_enabled and bool(config.get("card_system", {}).get("enabled"))
        self.profile = "weight_1" if newbie else "weight_2"
        self.tables = {name: self._prepare(raw) for name, raw in config["tables"].items()}

    @staticmethod
    def _prepare(raw: dict[str, Any]) -> Table:
        reels = []
        fill_symbols = raw.get("fill_symbols") or raw["reels"]
        fill_weights = raw.get("fill_weights") or [[1.0] * len(reel) for reel in raw["reels"]]
        for symbols, weights, refill_symbols, refill_weights in zip(raw["reels"], raw["weights"], fill_symbols, fill_weights):
            stop_cumulative, running = [], 0.0
            for weight in weights:
                running += max(0.0, float(weight))
                stop_cumulative.append(running)
            fill_cumulative, fill_running = [], 0.0
            for weight in refill_weights:
                fill_running += max(0.0, float(weight))
                fill_cumulative.append(fill_running)
            reels.append(
                Reel(
                    list(map(int, symbols)),
                    stop_cumulative,
                    running,
                    list(map(int, refill_symbols)),
                    fill_cumulative,
                    fill_running,
                )
            )
        random_wild = raw["random_wild"]
        return Table(
            reels,
            list(map(int, random_wild["values"])),
            list(map(float, random_wild["weights"])),
            list(map(float, raw.get("gold_overlay") or [0.0] * 5)),
            float(raw.get("scatter_suppression", 0.0)),
            list(map(int, raw.get("multipliers") or [])),
        )

    def overlay_gold(self, table: Table, reel: int, symbol: int) -> int:
        if symbol not in SCORE_SYMBOLS or not (0.0 < table.gold_overlay[reel]):
            return symbol
        return symbol + 8 if self.rng.random() < table.gold_overlay[reel] else symbol

    def suppress_second_scatter(self, table: Table, board: list[list[int]]) -> None:
        scatter_positions = [(reel, row) for reel, symbols in enumerate(board) for row, symbol in enumerate(symbols) if symbol == C1]
        candidates = [(reel, row) for reel, row in scatter_positions if reel > 0]
        if len(scatter_positions) != 2 or not candidates or self.rng.random() >= table.scatter_suppression:
            return
        reel, row = self.rng.choice(candidates)
        replacement = C1
        while replacement == C1:
            replacement = table.reels[reel].pick_fill(self.rng)
        board[reel][row] = replacement

    def board(self, table_name: str) -> list[list[int]]:
        table = self.tables[table_name]
        board = [table.reels[reel].window(self.rng, 4) for reel in range(5)]
        self.suppress_second_scatter(table, board)
        return [[self.overlay_gold(table, reel, symbol) for symbol in symbols] for reel, symbols in enumerate(board)]

    def evaluate(self, board: list[list[int]]) -> tuple[float, set[tuple[int, int]], list[tuple[int, int, float]]]:
        total, hits, details = 0.0, set(), []
        for target in SCORE_SYMBOLS:
            counts, positions = [], []
            for reel in range(5):
                matched = [(reel, row) for row, symbol in enumerate(board[reel]) if symbol in (WW, W2) or canonical(symbol) == target]
                if not matched:
                    break
                counts.append(len(matched))
                positions.append(matched)
            length = len(counts)
            if length < 3:
                continue
            ways = math.prod(counts)
            raw_pay = float(self.config["pays"][str(target)][length - 3]) * ways
            if raw_pay <= 0:
                continue
            total += raw_pay
            for group in positions:
                hits.update(group)
            details.append((target, ways, raw_pay))
        return total, hits, details

    def add_w2(self, board: list[list[int]], table: Table, gold: list[tuple[int, int]]) -> int:
        if not gold:
            return 0
        count = int(weighted_pick(self.rng, table.random_wild_values, table.random_wild_weights))
        if count <= 0:
            return 0
        source = self.rng.choice(gold)
        board[source[0]][source[1]] = W2
        candidates = [(reel, row) for reel in range(1, 5) for row, symbol in enumerate(board[reel]) if symbol not in (WW, W2, C1)]
        self.rng.shuffle(candidates)
        for reel, row in candidates[:count]:
            board[reel][row] = W2
        return min(count, len(candidates))

    def spin(self, table_name: str, free_game: bool = False) -> SpinResult:
        table = self.tables[table_name]
        multipliers = table.multipliers or ([2, 4, 6, 10] if free_game else [1, 2, 3, 5])
        board = self.board(table_name)
        result = SpinResult(initial_board=[reel[:] for reel in board])
        result.initial_symbols.update((reel, symbol) for reel, symbols in enumerate(board) for symbol in symbols)
        result.m1_present = any(canonical(symbol) == 3 for symbols in board for symbol in symbols)
        pending_gold: list[tuple[int, int]] = []
        bg_w2_used = False
        while True:
            if pending_gold and (free_game or not bg_w2_used):
                made = self.add_w2(board, table, pending_gold)
                if made:
                    result.w2_events += 1
                    bg_w2_used = True
            pending_gold = []
            raw_pay, hit_positions, details = self.evaluate(board)
            if raw_pay <= 0:
                break
            multiplier = multipliers[min(result.cascades, len(multipliers) - 1)]
            result.pay += raw_pay * multiplier * BASE_BET * BET_MULTI
            result.max_multiplier = max(result.max_multiplier, multiplier)
            result.cascades += 1
            for symbol, ways, symbol_raw_pay in details:
                result.symbol_hits[symbol] += ways
                result.symbol_pay[symbol] += symbol_raw_pay * multiplier * BASE_BET * BET_MULTI
            for reel, row in hit_positions:
                symbol = board[reel][row]
                if GOLD_MIN <= symbol <= GOLD_MAX:
                    board[reel][row] = WW
                    pending_gold.append((reel, row))
                    result.golden_converted += 1
                else:
                    board[reel][row] = -1
            for reel in range(5):
                remaining = [symbol for symbol in board[reel] if symbol != -1]
                dropped = [
                    self.overlay_gold(table, reel, table.reels[reel].pick_fill(self.rng))
                    for _ in range(4 - len(remaining))
                ]
                result.drop_symbols.update((reel, symbol) for symbol in dropped)
                result.m1_present |= any(canonical(symbol) == 3 for symbol in dropped)
                board[reel] = remaining + dropped
        result.scatter_count = sum(symbol == C1 for reel in board for symbol in reel)
        result.final_board = [reel[:] for reel in board]
        return result

    def pick_card(self, section: str, profile: str | None = None) -> dict[str, Any]:
        profile = profile or self.profile
        cards = self.config["card_system"]["profiles"][profile][section]
        return dict(weighted_pick(self.rng, cards, [float(card["weight"]) for card in cards]))

    @staticmethod
    def card_matches(card: dict[str, Any], pay: float) -> bool:
        ratio = pay / (BASE_BET * BET_MULTI)
        return float(card["min"]) < ratio <= float(card["max"])

    def card_spin(self, card: dict[str, Any]) -> SpinResult:
        if card.get("type") == "free_game":
            for _ in range(CARD_RETRY_LIMIT):
                spin = self.spin("bg_low")
                if spin.scatter_count >= 3:
                    return spin
            raise RuntimeError("FG trigger card retry limit exceeded")
        table_name = "bg_low" if card.get("table") == "A" else "bg_high"
        for _ in range(CARD_RETRY_LIMIT):
            spin = self.spin(table_name)
            if spin.scatter_count < 3 and self.card_matches(card, spin.pay):
                return spin
        raise RuntimeError(f"BG card range retry limit exceeded: ({card['min']}, {card['max']}]")

    def free_queue(self) -> list[str]:
        mix = self.config["free_game_mix"]
        choices = mix.get("choices") or mix.get("groups", {}).get("E")
        if not choices:
            raise ValueError("free_game_mix must provide choices or group E")
        choice = weighted_pick(self.rng, choices, [float(item["weight"]) for item in choices])
        queue = ["high"] * int(choice["high"]) + ["low"] * int(choice["low"])
        self.rng.shuffle(queue)
        return queue

    def high_table(self) -> str:
        return str(weighted_pick(self.rng, ["fg_high_a", "fg_high_k", "fg_high_q", "fg_high_j"], self.config["free_game_mix"]["high_variant_weights"]))

    def free_session(self, super_mode: bool = False) -> RoundResult:
        result = RoundResult(fg_triggered=True)
        remaining, played = int(self.config["free_spins"]), 0
        queue = self.free_queue()
        while remaining > 0 and played < int(self.config["free_spin_cap"]):
            remaining -= 1
            played += 1
            surface = queue.pop(0) if queue else "low"
            table_name = "super" if super_mode else self.high_table() if surface == "high" else "fg_low"
            spin = self.spin(table_name, free_game=True)
            result.pay_fg += spin.pay
            result.fg_spins += 1
            result.cascades_fg += spin.cascades
            result.max_multiplier = max(result.max_multiplier, spin.max_multiplier)
            result.golden_converted += spin.golden_converted
            result.w2_events += spin.w2_events
            result.fg_w2_events += spin.w2_events
            result.fg_m1_spins += int(spin.m1_present)
            result.combo_fg[min(spin.cascades, 5)] += 1
            result.symbol_hits.update(spin.symbol_hits)
            result.symbol_pay.update(spin.symbol_pay)
            result.fg_initial_symbols.update(spin.initial_symbols)
            result.fg_drop_symbols.update(spin.drop_symbols)
            if spin.scatter_count >= 3 and played + remaining < int(self.config["free_spin_cap"]):
                add = min(int(self.config["retrigger_spins"]), int(self.config["free_spin_cap"]) - played - remaining)
                remaining += add
                result.retriggers += int(add > 0)
                queue.extend(["high"] + ["low"] * max(0, add - 1))
        return result

    def card_feature(self, section: str, super_mode: bool = False) -> RoundResult:
        profile = "weight_1" if section == "super_feature" else self.profile
        card = self.pick_card(section, profile)
        for _ in range(CARD_RETRY_LIMIT):
            result = self.free_session(super_mode)
            if self.card_matches(card, result.pay_fg):
                return result
        raise RuntimeError(f"{section} card range retry limit exceeded: ({card['min']}, {card['max']}]")

    @staticmethod
    def merge(target: RoundResult, source: RoundResult) -> None:
        target.pay_bg += source.pay_bg
        target.pay_fg += source.pay_fg
        target.fg_triggered |= source.fg_triggered
        target.fg_spins += source.fg_spins
        target.retriggers += source.retriggers
        target.cascades_bg += source.cascades_bg
        target.cascades_fg += source.cascades_fg
        target.max_multiplier = max(target.max_multiplier, source.max_multiplier)
        target.golden_converted += source.golden_converted
        target.w2_events += source.w2_events
        target.bg_w2_events += source.bg_w2_events
        target.fg_w2_events += source.fg_w2_events
        target.bg_m1_spins += source.bg_m1_spins
        target.fg_m1_spins += source.fg_m1_spins
        target.combo_fg.update(source.combo_fg)
        target.symbol_hits.update(source.symbol_hits)
        target.symbol_pay.update(source.symbol_pay)
        target.bg_initial_symbols.update(source.bg_initial_symbols)
        target.bg_drop_symbols.update(source.bg_drop_symbols)
        target.fg_initial_symbols.update(source.fg_initial_symbols)
        target.fg_drop_symbols.update(source.fg_drop_symbols)

    def round(self, bet_mode: int) -> RoundResult:
        if bet_mode in (MODE_FEATUREBUY, MODE_SUPERBUY):
            super_mode = bet_mode == MODE_SUPERBUY
            return self.card_feature("super_feature" if super_mode else "buy_feature", super_mode) if self.card_enabled else self.free_session(super_mode)
        result = RoundResult()
        if self.card_enabled:
            spin = self.card_spin(self.pick_card("base_game"))
        else:
            spin = self.spin("bg_high")
        result.pay_bg = spin.pay
        result.cascades_bg = spin.cascades
        result.max_multiplier = spin.max_multiplier
        result.golden_converted = spin.golden_converted
        result.w2_events = spin.w2_events
        result.bg_w2_events = spin.w2_events
        result.bg_m1_spins = int(spin.m1_present)
        result.symbol_hits.update(spin.symbol_hits)
        result.symbol_pay.update(spin.symbol_pay)
        result.bg_initial_symbols.update(spin.initial_symbols)
        result.bg_drop_symbols.update(spin.drop_symbols)
        if spin.scatter_count >= 3:
            feature = self.card_feature("free_game") if self.card_enabled else self.free_session()
            self.merge(result, feature)
        return result


def wager_for_mode(mode: int, config: dict[str, Any] | None = None) -> float:
    active = config or CFG
    factor = 1.0 if mode == MODE_NORMALBET else float(active["buy_price"] if mode == MODE_FEATUREBUY else active["super_buy_price"])
    return BASE_BET * BET_MULTI * factor


def _empty_stats() -> dict[str, Any]:
    return {
        "rounds": 0,
        "coin_in": 0.0,
        "pay_bg": 0.0,
        "pay_fg": 0.0,
        "hit_rounds": 0,
        "fg_triggers": 0,
        "fg_spins": 0,
        "retriggers": 0,
        "cascades_bg": 0,
        "cascades_fg": 0,
        "golden_converted": 0,
        "w2_events": 0,
        "bg_w2_events": 0,
        "fg_w2_events": 0,
        "bg_m1_spins": 0,
        "fg_m1_spins": 0,
        "max_multiplier": 1,
        "win_x_sum": 0.0,
        "win_x_square": 0.0,
        "combo_bg": Counter(),
        "combo_fg": Counter(),
        "buckets": Counter(),
        "symbol_hits": Counter(),
        "symbol_pay": Counter(),
        "bg_initial_symbols": Counter(),
        "bg_drop_symbols": Counter(),
        "fg_initial_symbols": Counter(),
        "fg_drop_symbols": Counter(),
    }


def _simulate_chunk(rounds: int, bet_mode: int, seed: int, config: dict[str, Any] | None = None) -> dict[str, Any]:
    active = config or CFG
    game = LuckyAce(active, seed, CARD_SYSTEM_ENABLED, CARD_SYSTEM_IS_NEWBIE)
    stats = _empty_stats()
    wager = wager_for_mode(bet_mode, active)
    for _ in range(rounds):
        result = game.round(bet_mode)
        ratio = result.pay / wager if wager else 0.0
        stats["rounds"] += 1
        stats["coin_in"] += wager
        stats["pay_bg"] += result.pay_bg
        stats["pay_fg"] += result.pay_fg
        stats["hit_rounds"] += int(result.pay > 0)
        stats["fg_triggers"] += int(result.fg_triggered)
        stats["fg_spins"] += result.fg_spins
        stats["retriggers"] += result.retriggers
        stats["cascades_bg"] += result.cascades_bg
        stats["cascades_fg"] += result.cascades_fg
        stats["golden_converted"] += result.golden_converted
        stats["w2_events"] += result.w2_events
        stats["bg_w2_events"] += result.bg_w2_events
        stats["fg_w2_events"] += result.fg_w2_events
        stats["bg_m1_spins"] += result.bg_m1_spins
        stats["fg_m1_spins"] += result.fg_m1_spins
        stats["max_multiplier"] = max(stats["max_multiplier"], result.max_multiplier)
        stats["win_x_sum"] += ratio
        stats["win_x_square"] += ratio * ratio
        stats["combo_bg"][min(result.cascades_bg, 5)] += 1
        stats["combo_fg"].update(result.combo_fg)
        label = "0" if ratio == 0 else "(0,1)" if ratio < 1 else "[1,10)" if ratio < 10 else "[10,100)" if ratio < 100 else "100+"
        stats["buckets"][label] += 1
        stats["symbol_hits"].update(result.symbol_hits)
        stats["symbol_pay"].update(result.symbol_pay)
        stats["bg_initial_symbols"].update(result.bg_initial_symbols)
        stats["bg_drop_symbols"].update(result.bg_drop_symbols)
        stats["fg_initial_symbols"].update(result.fg_initial_symbols)
        stats["fg_drop_symbols"].update(result.fg_drop_symbols)
    return stats


def _merge_stats(target: dict[str, Any], source: dict[str, Any]) -> None:
    counter_fields = {
        "combo_bg", "combo_fg", "buckets", "symbol_hits", "symbol_pay",
        "bg_initial_symbols", "bg_drop_symbols", "fg_initial_symbols", "fg_drop_symbols",
    }
    for key, value in source.items():
        if key in counter_fields:
            target[key].update(value)
        elif key == "max_multiplier":
            target[key] = max(target[key], value)
        else:
            target[key] += value


def run_simulation(
    total_rounds: int = TOTAL_ROUNDS,
    bet_mode: int = BET_MODE,
    bet_multi: int = BET_MULTI,
    threads: int = THREADS,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    global BET_MULTI
    if bet_mode not in SUPPORTED_BET_MODES:
        raise ValueError(f"Unsupported bet mode: {bet_mode}")
    BET_MULTI = int(bet_multi)
    threads = max(1, min(int(threads), int(total_rounds)))
    base, extra = divmod(int(total_rounds), threads)
    chunks = [base + (1 if i < extra else 0) for i in range(threads)]
    started = time.perf_counter()
    merged = _empty_stats()
    active = config or CFG
    if threads == 1:
        _merge_stats(merged, _simulate_chunk(chunks[0], bet_mode, 46046, active))
    else:
        with ThreadPoolExecutor(max_workers=threads) as pool:
            futures = [pool.submit(_simulate_chunk, count, bet_mode, 46046 + i * 100003, active) for i, count in enumerate(chunks) if count]
            for future in futures:
                _merge_stats(merged, future.result())
    return {"stats": merged, "duration": time.perf_counter() - started, "bet_mode": bet_mode, "bet_multi": bet_multi}


simulate = run_simulation


def mode_name(mode: int) -> str:
    return {0: "Normal Bet", 2: "Buy Feature", 3: "Buy Super Feature"}.get(mode, f"Mode {mode}")


def summary_rows(result: dict[str, Any]) -> list[tuple[str, Any]]:
    s = result["stats"]
    rounds, coin_in = max(1, s["rounds"]), max(1.0, s["coin_in"])
    pay_total = s["pay_bg"] + s["pay_fg"]
    mean = s["win_x_sum"] / rounds
    variance = max(0.0, s["win_x_square"] / rounds - mean * mean)
    profile = "off" if not CARD_SYSTEM_ENABLED else "newbie" if CARD_SYSTEM_IS_NEWBIE else "oldhand"
    if result["bet_mode"] == MODE_SUPERBUY and CARD_SYSTEM_ENABLED:
        profile += " / super weight_1"
    return [
        ("parsheet_id", PARSHEET_ID),
        ("game_id", GAME_ID),
        ("game_name", GAME_NAME),
        ("config_file", CONFIG_FILE),
        ("card_system", "on" if CARD_SYSTEM_ENABLED else "off"),
        ("card_system_profile", profile),
        ("bet_mode", mode_name(result["bet_mode"])),
        ("bet_multi", result["bet_multi"]),
        ("coin_in", wager_for_mode(result["bet_mode"])),
        ("total_rounds", s["rounds"]),
        ("duration_sec", round(result["duration"], 3)),
        ("rtp_total", pay_total / coin_in),
        ("rtp_bg", s["pay_bg"] / coin_in),
        ("rtp_fg", s["pay_fg"] / coin_in),
        ("volatility_std", math.sqrt(variance)),
        ("standard_error", math.sqrt(variance) / math.sqrt(rounds)),
        ("hit_rate", s["hit_rounds"] / rounds),
        ("fg_trigger_rate", s["fg_triggers"] / rounds),
        ("fg_trigger_cycle", rounds / s["fg_triggers"] if s["fg_triggers"] else math.inf),
        ("avg_fg_spins", s["fg_spins"] / s["fg_triggers"] if s["fg_triggers"] else 0),
        ("retriggers", s["retriggers"]),
        ("avg_cascades_bg", s["cascades_bg"] / rounds),
        ("avg_cascades_fg", s["cascades_fg"] / max(1, s["fg_spins"])),
        ("golden_converted", s["golden_converted"]),
        ("w2_events", s["w2_events"]),
        ("w2_bg_event_rate", s["bg_w2_events"] / rounds),
        ("w2_fg_event_rate", s["fg_w2_events"] / max(1, s["fg_spins"])),
        ("m1_bg_spin_rate", s["bg_m1_spins"] / rounds),
        ("m1_fg_spin_rate", s["fg_m1_spins"] / max(1, s["fg_spins"])),
        ("max_win_multiplier", s["max_multiplier"]),
        ("rounds_per_second", rounds / max(result["duration"], 1e-9)),
    ]


def symbol_ratio_df(counter: Counter) -> pd.DataFrame:
    reel_totals = [sum(counter[(reel, symbol)] for symbol in SYMBOL_STR) for reel in range(5)]
    symbols = [symbol for symbol in sorted(SYMBOL_STR) if any(counter[(reel, symbol)] for reel in range(5))]
    rows = []
    for symbol in symbols:
        row: dict[str, Any] = {"Symbol": SYMBOL_STR[symbol]}
        for reel in range(5):
            total = reel_totals[reel]
            row[f"R{reel + 1}"] = counter[(reel, symbol)] / total if total else 0.0
        rows.append(row)
    return pd.DataFrame(rows, columns=["Symbol", "R1", "R2", "R3", "R4", "R5"])


def symbol_ratio_tables(result: dict[str, Any]) -> list[tuple[str, pd.DataFrame]]:
    s = result["stats"]
    return [
        ("BG 初始 R1-R5", symbol_ratio_df(s["bg_initial_symbols"])),
        ("BG 掉落 R1-R5", symbol_ratio_df(s["bg_drop_symbols"])),
        ("FG 初始 R1-R5", symbol_ratio_df(s["fg_initial_symbols"])),
        ("FG 掉落 R1-R5", symbol_ratio_df(s["fg_drop_symbols"])),
    ]


def print_symbol_ratio_tables(result: dict[str, Any]) -> None:
    formatters = {f"R{reel}": (lambda value: f"{value:.4%}") for reel in range(1, 6)}
    for title, frame in symbol_ratio_tables(result):
        print(f"\n=== {title} ===")
        print("No samples" if frame.empty else frame.to_string(index=False, formatters=formatters))


def print_console(result: dict[str, Any]) -> None:
    if SHOW_CONSOLE_SUMMARY:
        print("\n=== H016 幸運王牌 Simulation ===")
        for key, value in summary_rows(result):
            if key.startswith("rtp_") or key.endswith("_rate"):
                print(f"{key:22s}: {float(value) * 100:.6f}%")
            else:
                print(f"{key:22s}: {value}")
        print_symbol_ratio_tables(result)
    if SHOW_CONSOLE_DETAIL:
        print("\nPay buckets:", dict(result["stats"]["buckets"]))


def output_report(result: dict[str, Any]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    s = result["stats"]
    summary = dict(summary_rows(result))
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    rounds_tag = str(s["rounds"])
    rtp_tag = f"{float(summary['rtp_total']):.4f}".split(".", 1)[1]
    parts = [PARSHEET_ID, timestamp, f"betmode{result['bet_mode']}", rounds_tag, rtp_tag]
    if CARD_SYSTEM_ENABLED:
        parts.extend(["newbie" if CARD_SYSTEM_IS_NEWBIE else "oldhand", "card"])
    path = OUTPUT_DIR / ("_".join(re.sub(r"[^0-9A-Za-z_]+", "", part) for part in parts) + ".xlsx")
    base_df = pd.DataFrame(summary_rows(result), columns=["field", "value"])
    symbols = SCORE_SYMBOLS
    hits_df = pd.DataFrame({"symbol": [SYMBOL_STR[symbol] for symbol in symbols], "hits": [s["symbol_hits"][symbol] for symbol in symbols], "pay": [s["symbol_pay"][symbol] for symbol in symbols]})
    combo_df = pd.DataFrame({"combo": ["0", "1", "2", "3", "4", "5+"], "BG": [s["combo_bg"][i] for i in range(6)], "FG": [s["combo_fg"][i] for i in range(6)]})
    bucket_df = pd.DataFrame({"bucket": ["0", "(0,1)", "[1,10)", "[10,100)", "100+"], "count": [s["buckets"][key] for key in ["0", "(0,1)", "[1,10)", "[10,100)", "100+"]]})
    record_df = pd.DataFrame({"field": list(s.keys()), "value": [dict(v) if isinstance(v, Counter) else v for v in s.values()]})
    ratio_sheets = [
        ("BG Initial Symbol", symbol_ratio_df(s["bg_initial_symbols"])),
        ("BG Drop Symbol", symbol_ratio_df(s["bg_drop_symbols"])),
        ("FG Initial Symbol", symbol_ratio_df(s["fg_initial_symbols"])),
        ("FG Drop Symbol", symbol_ratio_df(s["fg_drop_symbols"])),
    ]
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        base_df.to_excel(writer, sheet_name="Base Info", index=False)
        hits_df.to_excel(writer, sheet_name="Hits", index=False)
        combo_df.to_excel(writer, sheet_name="Eliminate", index=False)
        bucket_df.to_excel(writer, sheet_name="Multiplier Line", index=False)
        record_df.to_excel(writer, sheet_name="Record Data", index=False)
        for sheet_name, frame in ratio_sheets:
            frame.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.sheets[sheet_name]
            worksheet.freeze_panes = "B2"
            worksheet.column_dimensions["A"].width = 14
            for column in "BCDEF":
                worksheet.column_dimensions[column].width = 13
                for row in range(2, len(frame) + 2):
                    worksheet[f"{column}{row}"].number_format = "0.0000%"
    return path


def format_board(board: list[list[int]]) -> str:
    return "\n".join(" | ".join(f"{SYMBOL_STR[board[reel][row]]:>3}" for reel in range(5)) for row in range(3, -1, -1))


def run_single_spin_debug() -> None:
    game = LuckyAce(CFG, 46046, False, CARD_SYSTEM_IS_NEWBIE)
    spin = game.spin("bg_high")
    print("\nInitial board:\n" + format_board(spin.initial_board))
    print("\nFinal board:\n" + format_board(spin.final_board))
    print(f"pay={spin.pay}, cascades={spin.cascades}, scatter={spin.scatter_count}, max=x{spin.max_multiplier}")


def run_all_combinations() -> None:
    for index, combo in enumerate(BATCH_RUNS, 1):
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env.update(
            {
                "H016_CONFIG_FILE": str(combo.get("config_file", CONFIG_FILE)),
                "H016_BET_MODE": str(combo.get("bet_mode", 0)),
                "H016_TOTAL_ROUNDS": str(combo.get("total_rounds", TOTAL_ROUNDS)),
                "H016_CARD_SYSTEM_IS_NEWBIE": str(bool(combo.get("card_system_is_newbie", False))).lower(),
                "H016_CARD_SYSTEM_ENABLED": str(bool(combo.get("card_system_enabled", True))).lower(),
                "H016_RUN_ALL_COMBINATIONS": "false",
                "H016_BATCH_CHILD": "1",
            }
        )
        print(f"\n=== Batch {index}/{len(BATCH_RUNS)}: {combo} ===", flush=True)
        result = subprocess.run(
            [sys.executable, str(SIMULATOR_PATH)],
            check=True,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.stdout:
            print(result.stdout.rstrip(), flush=True)
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr, flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="H016 幸運王牌 simulator (H015 runner structure)")
    parser.add_argument("rounds", nargs="?", type=int)
    parser.add_argument("bet_mode", nargs="?", type=int, choices=SUPPORTED_BET_MODES)
    parser.add_argument("--bet-multi", type=int, default=BET_MULTI)
    parser.add_argument("--threads", type=int, default=THREADS)
    parser.add_argument("--no-report", action="store_true")
    parser.add_argument("--debug-spin", action="store_true")
    # Notebook kernels append their own command-line flags. H015-style IDE and
    # Notebook execution should ignore those unrelated arguments.
    return parser.parse_known_args()[0]


def main() -> None:
    args = parse_args()
    explicit_single_run = args.rounds is not None or args.bet_mode is not None or args.debug_spin
    if RUN_ALL_COMBINATIONS and not explicit_single_run and os.environ.get("H016_BATCH_CHILD") != "1":
        run_all_combinations()
        return
    if RUN_SINGLE_SPIN_DEBUG or args.debug_spin:
        run_single_spin_debug()
        return
    result = run_simulation(args.rounds or TOTAL_ROUNDS, BET_MODE if args.bet_mode is None else args.bet_mode, args.bet_multi, args.threads)
    print_console(result)
    if OUTPUT_REPORT and not args.no_report:
        print(f"\nReport: {output_report(result)}")


if __name__ == "__main__":
    main()
