"""H999 幸運王牌2 simulator.

The runner, environment settings, batch workflow and Excel report layout follow
H015.  The game engine follows 101003 and reads the H999-derived H999 configs:
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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

# ===== User Settings (H015-compatible runner) =====

CONFIG_FILE = "config_92.js"
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


CONFIG_FILE = os.environ.get("H999_CONFIG_FILE", CONFIG_FILE)


def _load_config(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8-sig")
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        raise ValueError(f"Config does not contain a JSON object: {path}")
    return json.loads(raw[start : end + 1])


def _is_h999_config(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        data = _load_config(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    required = {"tables", "symbol_names", "pays", "free_game_mix"}
    return str(data.get("game_id")) == "H999" and required.issubset(data)


def resolve_base_dir() -> Path:
    """Locate H999 safely when run as a file, `%run`, or a Notebook cell."""
    cwd = Path.cwd().resolve()
    candidates: list[Path] = []
    override = os.environ.get("H999_BASE_DIR")
    if override:
        candidates.append(Path(override).expanduser())

    file_value = globals().get("__file__")
    if file_value and not str(file_value).startswith("<"):
        candidates.append(Path(file_value).resolve().parent)
    candidates.append(cwd)

    for parent in (cwd, *cwd.parents):
        candidates.extend(
            [
                parent / "Project" / "Slots" / "H999_幸運王牌 2",
                parent / "Project_AI" / "Slots" / "H999_幸運王牌 2",
                parent / "Slots" / "H999_幸運王牌 2",
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
        if _is_h999_config(candidate / CONFIG_FILE):
            return candidate

    locations = "\n  - ".join(str(path / CONFIG_FILE) for path in checked)
    raise FileNotFoundError(f"Cannot locate a valid H999 {CONFIG_FILE}. Checked:\n  - {locations}\n" "Set H999_BASE_DIR to the H999_幸運王牌 2 folder when running from another workspace.")


BASE_DIR = resolve_base_dir()
OUTPUT_DIR = BASE_DIR / "Record"
SIMULATOR_PATH = BASE_DIR / "Simulator.py"
TOTAL_ROUNDS = int(os.environ.get("H999_TOTAL_ROUNDS", TOTAL_ROUNDS))
BET_MULTI = int(os.environ.get("H999_BET_MULTI", BET_MULTI))
BET_MODE = int(os.environ.get("H999_BET_MODE", BET_MODE))
CARD_SYSTEM_ENABLED = _env_bool("H999_CARD_SYSTEM_ENABLED", CARD_SYSTEM_ENABLED)
CARD_SYSTEM_IS_NEWBIE = _env_bool("H999_CARD_SYSTEM_IS_NEWBIE", CARD_SYSTEM_IS_NEWBIE)
RUN_ALL_COMBINATIONS = _env_bool("H999_RUN_ALL_COMBINATIONS", RUN_ALL_COMBINATIONS)
OUTPUT_REPORT = _env_bool("H999_OUTPUT_REPORT", OUTPUT_REPORT)
SHOW_CONSOLE_SUMMARY = _env_bool("H999_SHOW_CONSOLE_SUMMARY", SHOW_CONSOLE_SUMMARY)
SHOW_CONSOLE_DETAIL = _env_bool("H999_SHOW_CONSOLE_DETAIL", SHOW_CONSOLE_DETAIL)
RUN_SINGLE_SPIN_DEBUG = _env_bool("H999_RUN_SINGLE_SPIN_DEBUG", RUN_SINGLE_SPIN_DEBUG)
THREADS = max(1, int(os.environ.get("H999_THREADS", THREADS)))
CFG = _load_config(BASE_DIR / CONFIG_FILE)
GAME_ID = str(CFG.get("game_id", "H999"))
PARSHEET_ID = str(CFG.get("parsheet_id", "H999192"))
GAME_NAME = str(CFG.get("name_zh", "幸運王牌2"))
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
    cumulative: list[float]
    total: float

    def pick(self, rng: random.Random) -> int:
        position = rng.random() * self.total
        index = bisect.bisect_left(self.cumulative, position)
        return self.symbols[min(index, len(self.symbols) - 1)]


@dataclass
class Table:
    reels: list[Reel]
    random_wild_values: list[int]
    random_wild_weights: list[float]
    multipliers: list[int]


@dataclass
class SpinResult:
    pay: float = 0.0
    scatter_count: int = 0
    cascades: int = 0
    max_multiplier: int = 1
    golden_converted: int = 0
    w2_events: int = 0
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
        for symbols, weights in zip(raw["reels"], raw["weights"]):
            cumulative, running = [], 0.0
            for weight in weights:
                running += max(0.0, float(weight))
                cumulative.append(running)
            reels.append(Reel(list(map(int, symbols)), cumulative, running))
        random_wild = raw["random_wild"]
        return Table(
            reels,
            list(map(int, random_wild["values"])),
            list(map(float, random_wild["weights"])),
            list(map(int, raw.get("multipliers") or [])),
        )

    def board(self, table_name: str) -> list[list[int]]:
        table = self.tables[table_name]
        return [[table.reels[reel].pick(self.rng) for _ in range(4)] for reel in range(5)]

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
        multipliers = table.multipliers or ([2, 4, 6, 10, 20] if free_game else [1, 2, 3, 5, 10])
        board = self.board(table_name)
        result = SpinResult(
            initial_board=[reel[:] for reel in board],
            max_multiplier=multipliers[0],
        )
        result.initial_symbols.update((reel, symbol) for reel, symbols in enumerate(board) for symbol in symbols)
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
            multiplier_index = min(result.cascades, len(multipliers) - 1)
            multiplier = multipliers[multiplier_index]
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
                dropped = [table.reels[reel].pick(self.rng) for _ in range(4 - len(remaining))]
                result.drop_symbols.update((reel, symbol) for symbol in dropped)
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
        choices = self.config["free_game_mix"]["choices"]
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
        result.symbol_hits.update(spin.symbol_hits)
        result.symbol_pay.update(spin.symbol_pay)
        result.bg_initial_symbols.update(spin.initial_symbols)
        result.bg_drop_symbols.update(spin.drop_symbols)
        if spin.scatter_count >= 3:
            feature = self.card_feature("free_game") if self.card_enabled else self.free_session()
            self.merge(result, feature)
        return result


def wager_for_mode(mode: int) -> float:
    factor = 1.0 if mode == MODE_NORMALBET else float(CFG["buy_price"] if mode == MODE_FEATUREBUY else CFG["super_buy_price"])
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


def _simulate_chunk(rounds: int, bet_mode: int, seed: int) -> dict[str, Any]:
    game = LuckyAce(CFG, seed, CARD_SYSTEM_ENABLED, CARD_SYSTEM_IS_NEWBIE)
    stats = _empty_stats()
    wager = wager_for_mode(bet_mode)
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
        stats["max_multiplier"] = max(stats["max_multiplier"], result.max_multiplier)
        stats["win_x_sum"] += ratio
        stats["win_x_square"] += ratio * ratio
        stats["combo_bg"][min(result.cascades_bg, 5)] += 1
        stats["combo_fg"][min(result.cascades_fg, 5)] += 1
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


def run_simulation(total_rounds: int = TOTAL_ROUNDS, bet_mode: int = BET_MODE, bet_multi: int = BET_MULTI, threads: int = THREADS) -> dict[str, Any]:
    global BET_MULTI
    if bet_mode not in SUPPORTED_BET_MODES:
        raise ValueError(f"Unsupported bet mode: {bet_mode}")
    BET_MULTI = int(bet_multi)
    threads = max(1, min(int(threads), int(total_rounds)))
    base, extra = divmod(int(total_rounds), threads)
    chunks = [base + (1 if i < extra else 0) for i in range(threads)]
    started = time.perf_counter()
    merged = _empty_stats()
    if threads == 1:
        _merge_stats(merged, _simulate_chunk(chunks[0], bet_mode, 46046))
    else:
        with ThreadPoolExecutor(max_workers=threads) as pool:
            futures = [pool.submit(_simulate_chunk, count, bet_mode, 46046 + i * 100003) for i, count in enumerate(chunks) if count]
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
        print("\n=== H999 幸運王牌2 Simulation ===")
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
                "H999_CONFIG_FILE": str(combo.get("config_file", CONFIG_FILE)),
                "H999_BET_MODE": str(combo.get("bet_mode", 0)),
                "H999_TOTAL_ROUNDS": str(combo.get("total_rounds", TOTAL_ROUNDS)),
                "H999_CARD_SYSTEM_IS_NEWBIE": str(bool(combo.get("card_system_is_newbie", False))).lower(),
                "H999_CARD_SYSTEM_ENABLED": str(bool(combo.get("card_system_enabled", True))).lower(),
                "H999_RUN_ALL_COMBINATIONS": "false",
                "H999_BATCH_CHILD": "1",
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
    parser = argparse.ArgumentParser(description="H999 幸運王牌2 simulator (H015 runner structure)")
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
    if RUN_ALL_COMBINATIONS and not explicit_single_run and os.environ.get("H999_BATCH_CHILD") != "1":
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
