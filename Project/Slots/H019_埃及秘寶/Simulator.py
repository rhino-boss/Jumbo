import json
import math
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

# ===== User settings =====

CONFIG_FILE = "config_92.js"
TOTAL_ROUNDS = 10**5
BET_MODE = 0
BET_MULTI = 1
CARD_SYSTEM_ENABLED = True
CARD_SYSTEM_IS_NEWBIE = False
THREADS = max(1, max(8, (os.cpu_count() or 2) - 2))

RUN_ALL_COMBINATIONS = True
OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = True
SHOW_CONSOLE_DETAIL = False
RUN_SINGLE_SPIN_DEBUG = False

BATCH_COMBINATIONS = [
    # {"config_file": "config_92.js", "bet_mode": 0, "total_rounds": 10**9, "card_system_enabled": False, "card_system_is_newbie": False},
    # {"config_file": "config_92.js", "bet_mode": 3, "total_rounds": 10**8, "card_system_enabled": False, "card_system_is_newbie": False},
    {"config_file": "config_92.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},
    {"config_file": "config_92.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    {"config_file": "config_92.js", "bet_mode": 2, "total_rounds": 10**7, "card_system_enabled": True, "card_system_is_newbie": False},
    {"config_file": "config_92.js", "bet_mode": 3, "total_rounds": 10**7, "card_system_enabled": True, "card_system_is_newbie": False},
]

THRESHOLD_RECORD = np.array(
    [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        15,
        20,
        25,
        30,
        35,
        40,
        45,
        50,
        60,
        70,
        80,
        90,
        100,
        120,
        140,
        160,
        180,
        200,
        250,
        300,
        350,
        400,
        450,
        500,
        550,
        600,
        650,
        700,
        750,
        800,
        850,
        900,
        950,
        1000,
        2000,
        3000,
        4000,
        5000,
        6000,
        7000,
        8000,
        9000,
        10000,
        20000,
        30000,
        40000,
        50000,
        60000,
        70000,
        80000,
        90000,
        100000,
        9999999,
    ],
    dtype=np.float64,
)


def parse_env_bool(name, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


CONFIG_FILE = os.environ.get("H019_CONFIG_FILE", CONFIG_FILE)
TOTAL_ROUNDS = int(os.environ.get("H019_TOTAL_ROUNDS", TOTAL_ROUNDS))
BET_MODE = int(os.environ.get("H019_BET_MODE", BET_MODE))
BET_MULTI = int(os.environ.get("H019_BET_MULTI", BET_MULTI))
CARD_SYSTEM_ENABLED = parse_env_bool("H019_CARD_SYSTEM_ENABLED", CARD_SYSTEM_ENABLED)
CARD_SYSTEM_IS_NEWBIE = parse_env_bool("H019_CARD_SYSTEM_IS_NEWBIE", CARD_SYSTEM_IS_NEWBIE)
THREADS = int(os.environ.get("H019_THREADS", THREADS))
RUN_ALL_COMBINATIONS = parse_env_bool("H019_RUN_ALL_COMBINATIONS", RUN_ALL_COMBINATIONS)
OUTPUT_REPORT = parse_env_bool("H019_OUTPUT_REPORT", OUTPUT_REPORT)
SHOW_CONSOLE_SUMMARY = parse_env_bool("H019_SHOW_CONSOLE_SUMMARY", SHOW_CONSOLE_SUMMARY)
SHOW_CONSOLE_DETAIL = parse_env_bool("H019_SHOW_CONSOLE_DETAIL", SHOW_CONSOLE_DETAIL)
RUN_SINGLE_SPIN_DEBUG = parse_env_bool("H019_RUN_SINGLE_SPIN_DEBUG", RUN_SINGLE_SPIN_DEBUG)


def resolve_base_dir():
    override = os.environ.get("H019_BASE_DIR")
    candidates = []
    if override:
        candidates.append(Path(override).expanduser())
    file_value = globals().get("__file__")
    if file_value:
        candidates.append(Path(file_value).resolve().parent)
    cwd = Path.cwd().resolve()
    candidates.extend([cwd, cwd / "Project_AI" / "Slots" / "H019_埃及秘寶"])
    for parent in [cwd, *cwd.parents]:
        candidates.append(parent / "Project_AI" / "Slots" / "H019_埃及秘寶")
        candidates.append(parent / "Slots" / "H019_埃及秘寶")
    for candidate in candidates:
        candidate = candidate.resolve()
        if (candidate / CONFIG_FILE).is_file():
            return candidate
    raise FileNotFoundError(f"Cannot locate H019 base directory containing {CONFIG_FILE}")


BASE_DIR = resolve_base_dir()
CONFIG_PATH = BASE_DIR / CONFIG_FILE
OUTPUT_DIR = BASE_DIR / "Record"
SIMULATOR_PATH = BASE_DIR / "Simulator.py"


def load_js_config(path):
    text = path.read_text(encoding="utf-8-sig").strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError(f"Invalid config format: {path}")
    return json.loads(text[start : end + 1])


CFG = load_js_config(CONFIG_PATH)

GAME_ID = str(CFG["game_id"])
PARSHEET_ID = str(CFG["parsheet_id"])
GAME_NAME = str(CFG["display_name"])
GAME_NAME_ZH = str(CFG["game_name_zh"])
CONFIG_VERSION = str(CFG["excel_version"])

MODE_NORMALBET = int(CFG["mode_normalbet"])
MODE_FEATUREBUY = int(CFG["mode_featurebuy"])
MODE_SUPERFEATUREBUY = int(CFG["mode_superfeaturebuy"])
DEFAULT_COIN_IN = int(CFG["default_coin_in"])
NORMALBET = int(CFG["normalbet"])
FEATUREBUY = int(CFG["featurebuy"])
SUPERFEATUREBUY = int(CFG["superfeaturebuy"])
WINDOW_SIZE = int(CFG["window_size"])
REEL_NUM = int(CFG["reel_num"])
MAX_FREE_SPINS = int(CFG["max_free_spins"])

SYMBOL_CODES = list(CFG["symbol_codes"])
SYMBOL_IDS = np.asarray(CFG["symbol_ids"], dtype=np.int64)
PAY_TABLE = np.asarray(CFG["pay_table"], dtype=np.int64)
SYMBOL_COUNT = len(SYMBOL_CODES)
CODE_TO_ID = {code: int(symbol_id) for code, symbol_id in zip(SYMBOL_CODES, SYMBOL_IDS)}
WW = CODE_TO_ID["WW"]
C1 = CODE_TO_ID["C1"]
C2 = CODE_TO_ID["C2"]
SCORE_SYMBOLS = np.asarray([CODE_TO_ID[code] for code in SYMBOL_CODES if code not in {"WW", "C1", "C2"}], dtype=np.int64)

REEL_LENGTHS = np.asarray([item["reel_lengths"] for item in CFG["strips"]], dtype=np.int64)
MAX_STRIP_ROWS = max(len(item["symbols"]) for item in CFG["strips"])
STRIPS = np.zeros((len(CFG["strips"]), MAX_STRIP_ROWS, REEL_NUM), dtype=np.int64)
STRIP_WEIGHTS = np.zeros_like(STRIPS)
for table_index, item in enumerate(CFG["strips"]):
    row_count = len(item["symbols"])
    STRIPS[table_index, :row_count] = np.asarray(item["symbols"], dtype=np.int64)
    STRIP_WEIGHTS[table_index, :row_count] = np.asarray(item["weights"], dtype=np.int64)

PROFILE_NAMES = ["normal", "featurebuy", "superfeaturebuy"]
PROFILE_BY_MODE = {MODE_NORMALBET: 0, MODE_FEATUREBUY: 1, MODE_SUPERFEATUREBUY: 2}
PARAMETER = CFG["parameter"]

BASE_REEL_WEIGHT_CUM = np.zeros((3, 4), dtype=np.int64)
FREE_INITIAL_COUNTS = np.zeros((3, 4), dtype=np.int64)
FREE_RETRIGGER_COUNTS = np.zeros((3, 4), dtype=np.int64)
C2_MODE_WEIGHT_CUM = np.zeros((3, 2, 3), dtype=np.int64)
C2_MULTIPLIERS = np.zeros((3, 17), dtype=np.int64)
C2_WEIGHT_CUM = np.zeros((3, 7, 17), dtype=np.int64)

C2_WEIGHT_NAMES = ["base_direct", "base_wild", "free_direct", "free_wild", "super", "ultimate", "bad"]
for profile_index, profile_name in enumerate(PROFILE_NAMES):
    profile = PARAMETER[profile_name]
    base_cum = profile["base_reel_weights_cum"]
    BASE_REEL_WEIGHT_CUM[profile_index, : len(base_cum)] = base_cum
    FREE_INITIAL_COUNTS[profile_index] = np.asarray(profile["free_table"]["initial"], dtype=np.int64)
    FREE_RETRIGGER_COUNTS[profile_index] = np.asarray(profile["free_table"]["retrigger"], dtype=np.int64)
    C2_MODE_WEIGHT_CUM[profile_index, 0] = np.cumsum(np.asarray(profile["c2_mode_weights"]["base"], dtype=np.int64))
    C2_MODE_WEIGHT_CUM[profile_index, 1] = np.cumsum(np.asarray(profile["c2_mode_weights"]["free"], dtype=np.int64))
    multipliers = profile["c2"]["multipliers"]
    C2_MULTIPLIERS[profile_index, : len(multipliers)] = multipliers
    for weight_index, name in enumerate(C2_WEIGHT_NAMES):
        values = profile["c2"]["weights_cum"][name]
        C2_WEIGHT_CUM[profile_index, weight_index, : len(values)] = values

CARD_SYSTEM = CFG.get("card_system", {})
CARD_SYSTEM_ENABLED = CARD_SYSTEM_ENABLED and bool(CARD_SYSTEM.get("enabled", False))
CARD_RETRY_LIMIT = max(1, int(CARD_SYSTEM.get("retry_limit", 5000)))
CARD_TYPE_RANGE = 0
CARD_TYPE_FREE_GAME = 1
CARD_PROFILE_NEWBIE_BG = 0
CARD_PROFILE_NEWBIE_FG = 1
CARD_PROFILE_OLDHAND_BG = 2
CARD_PROFILE_OLDHAND_FG = 3
CARD_PROFILE_BUY_FEATURE = 4
CARD_PROFILE_SUPER_FEATURE = 5


def get_card_profile_cards(player, mode, segment):
    player_data = CARD_SYSTEM.get(player, {})
    mode_data = player_data.get(mode, {}) if isinstance(player_data, dict) else {}
    return list(mode_data.get(segment, [])) if isinstance(mode_data, dict) else []


CARD_PROFILE_LISTS = [
    get_card_profile_cards("newbie", "normal_bet", "weight_bg"),
    get_card_profile_cards("newbie", "normal_bet", "weight_fg"),
    get_card_profile_cards("oldhand", "normal_bet", "weight_bg"),
    get_card_profile_cards("oldhand", "normal_bet", "weight_fg"),
    get_card_profile_cards("oldhand", "buy_feature", "weight_fg"),
    get_card_profile_cards("oldhand", "super_feature", "weight_fg"),
]
MAX_CARDS = max(1, max((len(cards) for cards in CARD_PROFILE_LISTS), default=0))
CARD_TYPES = np.full((len(CARD_PROFILE_LISTS), MAX_CARDS), -1, dtype=np.int64)
CARD_MIN = np.zeros((len(CARD_PROFILE_LISTS), MAX_CARDS), dtype=np.float64)
CARD_MAX = np.zeros((len(CARD_PROFILE_LISTS), MAX_CARDS), dtype=np.float64)
CARD_WEIGHT_CUM = np.zeros((len(CARD_PROFILE_LISTS), MAX_CARDS), dtype=np.int64)
CARD_COUNTS = np.zeros(len(CARD_PROFILE_LISTS), dtype=np.int64)
for card_profile_index, cards in enumerate(CARD_PROFILE_LISTS):
    running_weight = 0
    for card_index, card in enumerate(cards):
        weight = max(0, int(card.get("weight", 0)))
        running_weight += weight
        CARD_TYPES[card_profile_index, card_index] = CARD_TYPE_FREE_GAME if card.get("type") == "free_game" else CARD_TYPE_RANGE
        CARD_MIN[card_profile_index, card_index] = float(card.get("min", 0.0))
        CARD_MAX[card_profile_index, card_index] = float(card.get("max", 0.0))
        CARD_WEIGHT_CUM[card_profile_index, card_index] = running_weight
    CARD_COUNTS[card_profile_index] = len(cards)


def calc_coin_in(bet_mode, bet_multi):
    if bet_mode == MODE_NORMALBET:
        return DEFAULT_COIN_IN * NORMALBET * bet_multi
    if bet_mode == MODE_FEATUREBUY:
        return DEFAULT_COIN_IN * FEATUREBUY * bet_multi
    if bet_mode == MODE_SUPERFEATUREBUY:
        return DEFAULT_COIN_IN * SUPERFEATUREBUY * bet_multi
    raise ValueError(f"Unsupported bet mode: {bet_mode}")


def format_bet_mode_label(bet_mode):
    if bet_mode == MODE_FEATUREBUY:
        return "Buy Feature"
    if bet_mode == MODE_SUPERFEATUREBUY:
        return "Super Feature"
    return "Normal Bet"


# ===== Record layout =====

R_ALL = 0
R_MULTI_CNT_BG = 1
R_MULTI_PAY_BG = 2
R_MULTI_CNT_FG = 3
R_MULTI_PAY_FG = 4
R_MULTI_CNT_OA = 5
R_MULTI_PAY_OA = 6
R_SYMBOL_HIT_BG = 7
R_SYMBOL_PAY_BG = 8
R_SYMBOL_HIT_FG = 9
R_SYMBOL_PAY_FG = 10
R_CASCADE_BG = 11
R_CASCADE_FG = 12
R_C2_VALUE_BG = 13
R_C2_VALUE_FG = 14
R_SCATTER_BG = 15
R_SCATTER_FG = 16

RECORD_COLS = max(128, len(THRESHOLD_RECORD), SYMBOL_COUNT, C2_MULTIPLIERS.shape[1])
RECORD_SIZE = (17, RECORD_COLS)

RA_TOTAL_ROUNDS = 0
RA_COIN_IN_SUM = 1
RA_PAY_TOTAL = 2
RA_PAY_BG_CLUSTER = 3
RA_PAY_BG_SCATTER = 4
RA_PAY_FG = 5
RA_HITS_BG = 6
RA_HITS_FG = 7
RA_FG_TRIGGER = 8
RA_RETRIGGER = 9
RA_FG_SPINS = 10
RA_X_SUM = 11
RA_X_SQUARE = 12
RA_MAX_SINGLE_WIN = 13
RA_MAX_WIN_HITS = 14
RA_MAX_C2_MULTIPLIER = 15
RA_BG_CASCADES = 16
RA_FG_CASCADES = 17
RA_C2_COUNT_BG = 18
RA_C2_COUNT_FG = 19
RA_RETRY_TOTAL = 20
RA_RETRY_LIMIT_EXCEEDED = 21
RA_RETRY_FAIL_BG_RANGE = 22
RA_RETRY_FAIL_BG_FREEGAME = 23
RA_RETRY_FAIL_FG = 24


@njit(nogil=True)
def pick_cumulative(cumulative):
    total = cumulative[-1]
    if total <= 0:
        return 0
    pick = np.random.randint(0, total)
    for index in range(cumulative.shape[0]):
        if pick < cumulative[index]:
            return index
    return cumulative.shape[0] - 1


@njit(nogil=True)
def pick_card(card_profile_index):
    card_count = CARD_COUNTS[card_profile_index]
    if card_count <= 0:
        return -1
    return pick_cumulative(CARD_WEIGHT_CUM[card_profile_index, :card_count])


@njit(nogil=True)
def is_card_match(card_profile_index, card_index, score, card_coin_in, triggered_free_game):
    if card_index < 0:
        return True
    if CARD_TYPES[card_profile_index, card_index] == CARD_TYPE_FREE_GAME:
        return triggered_free_game == 1
    multiplier = score / card_coin_in
    return multiplier > CARD_MIN[card_profile_index, card_index] and multiplier <= CARD_MAX[card_profile_index, card_index]


@njit(nogil=True)
def choose_base_table(profile_index):
    if profile_index != 0:
        return 8
    cumulative = BASE_REEL_WEIGHT_CUM[profile_index]
    return pick_cumulative(cumulative)


@njit(nogil=True)
def generate_board(table_id):
    board = np.empty((WINDOW_SIZE, REEL_NUM), dtype=np.int64)
    wild_c2 = np.zeros((WINDOW_SIZE, REEL_NUM), dtype=np.int64)
    starts = np.zeros(REEL_NUM, dtype=np.int64)
    drop_counts = np.zeros(REEL_NUM, dtype=np.int64)
    for reel in range(REEL_NUM):
        length = REEL_LENGTHS[table_id, reel]
        total = 0
        for row in range(length):
            total += STRIP_WEIGHTS[table_id, row, reel]
        pick = np.random.randint(0, total) if total > 0 else 0
        running = 0
        start = 0
        for row in range(length):
            running += STRIP_WEIGHTS[table_id, row, reel]
            if pick < running:
                start = row
                break
        starts[reel] = start
        for visible_row in range(WINDOW_SIZE):
            board[visible_row, reel] = STRIPS[table_id, (start + visible_row) % length, reel]
    return board, wild_c2, starts, drop_counts


@njit(nogil=True)
def pay_index_for_count(count):
    if count >= 12:
        return 5
    if count >= 10:
        return 4
    if count >= 8:
        return 3
    return -1


@njit(nogil=True)
def evaluate_clusters(board, bet_multi):
    winning = np.zeros(SYMBOL_COUNT, dtype=np.int64)
    symbol_hits = np.zeros(SYMBOL_COUNT, dtype=np.int64)
    symbol_raw_pay = np.zeros(SYMBOL_COUNT, dtype=np.int64)
    wild_count = 0
    for row in range(WINDOW_SIZE):
        for reel in range(REEL_NUM):
            if board[row, reel] == WW:
                wild_count += 1

    raw_pay = 0
    any_win = 0
    for symbol_index in range(SCORE_SYMBOLS.shape[0]):
        symbol = SCORE_SYMBOLS[symbol_index]
        count = wild_count
        for row in range(WINDOW_SIZE):
            for reel in range(REEL_NUM):
                if board[row, reel] == symbol:
                    count += 1
        pay_index = pay_index_for_count(count)
        if pay_index >= 0:
            pay = PAY_TABLE[symbol, pay_index] * bet_multi
            winning[symbol] = 1
            symbol_hits[symbol] += 1
            symbol_raw_pay[symbol] += pay
            raw_pay += pay
            any_win = 1
    return raw_pay, winning, symbol_hits, symbol_raw_pay, any_win


@njit(nogil=True)
def cascade_board(board, wild_c2, table_id, starts, drop_counts, winning, any_win):
    if any_win == 0:
        return
    for reel in range(REEL_NUM):
        kept_symbols = np.empty(WINDOW_SIZE, dtype=np.int64)
        kept_wild_flags = np.zeros(WINDOW_SIZE, dtype=np.int64)
        kept_count = 0
        has_scatter = 0
        for row in range(WINDOW_SIZE - 1, -1, -1):
            symbol = board[row, reel]
            if symbol == C1:
                has_scatter = 1
            if symbol == WW:
                kept_symbols[kept_count] = C2
                kept_wild_flags[kept_count] = 1
                kept_count += 1
            elif symbol < winning.shape[0] and winning[symbol] == 1:
                continue
            else:
                kept_symbols[kept_count] = symbol
                kept_wild_flags[kept_count] = wild_c2[row, reel]
                kept_count += 1

        output_row = WINDOW_SIZE - 1
        for index in range(kept_count):
            board[output_row, reel] = kept_symbols[index]
            wild_c2[output_row, reel] = kept_wild_flags[index]
            output_row -= 1

        length = REEL_LENGTHS[table_id, reel]
        while output_row >= 0:
            drop_counts[reel] += 1
            strip_index = (starts[reel] - drop_counts[reel]) % length
            symbol = STRIPS[table_id, strip_index, reel]
            if symbol == C1 and has_scatter == 1:
                drop_counts[reel] += 1
                strip_index = (starts[reel] - drop_counts[reel]) % length
                symbol = STRIPS[table_id, strip_index, reel]
            if symbol == C1:
                has_scatter = 1
            board[output_row, reel] = symbol
            wild_c2[output_row, reel] = 0
            output_row -= 1


@njit(nogil=True)
def draw_c2_value(profile_index, scene, came_from_wild, c2_mode):
    if c2_mode == 1:
        weight_index = 4
    elif c2_mode == 2:
        weight_index = 5
    elif scene == 0:
        weight_index = 1 if came_from_wild else 0
    else:
        weight_index = 3 if came_from_wild else 2
    cumulative = C2_WEIGHT_CUM[profile_index, weight_index]
    valid_length = 0
    for index in range(cumulative.shape[0]):
        if cumulative[index] > 0:
            valid_length = index + 1
    if valid_length == 0:
        return 0, -1
    selected = pick_cumulative(cumulative[:valid_length])
    return C2_MULTIPLIERS[profile_index, selected], selected


@njit(nogil=True)
def count_scatter(board):
    count = 0
    for row in range(WINDOW_SIZE):
        for reel in range(REEL_NUM):
            if board[row, reel] == C1:
                count += 1
    return count


@njit(nogil=True)
def play_cluster_spin(table_id, profile_index, scene, bet_multi):
    board, wild_c2, starts, drop_counts = generate_board(table_id)
    total_raw_pay = 0
    total_hits = np.zeros(SYMBOL_COUNT, dtype=np.int64)
    total_raw_symbol_pay = np.zeros(SYMBOL_COUNT, dtype=np.int64)
    cascades = 0

    for _ in range(100):
        raw_pay, winning, hits, raw_symbol_pay, any_win = evaluate_clusters(board, bet_multi)
        total_raw_pay += raw_pay
        total_hits += hits
        total_raw_symbol_pay += raw_symbol_pay
        if any_win == 0:
            break
        cascades += 1
        cascade_board(board, wild_c2, table_id, starts, drop_counts, winning, any_win)

    c2_mode = pick_cumulative(C2_MODE_WEIGHT_CUM[profile_index, scene])
    c2_total = 0
    c2_count = 0
    c2_value_hits = np.zeros(C2_MULTIPLIERS.shape[1], dtype=np.int64)
    for row in range(WINDOW_SIZE):
        for reel in range(REEL_NUM):
            if board[row, reel] == C2:
                value, value_index = draw_c2_value(profile_index, scene, wild_c2[row, reel] == 1, c2_mode)
                c2_total += value
                c2_count += 1
                if value_index >= 0:
                    c2_value_hits[value_index] += 1

    scatter_count = count_scatter(board)
    scatter_pay = 0
    if scatter_count >= 4 and scatter_count <= 6:
        scatter_pay = PAY_TABLE[C1, scatter_count - 4] * bet_multi
    return (
        total_raw_pay,
        scatter_pay,
        scatter_count,
        c2_total,
        c2_count,
        cascades,
        total_hits,
        total_raw_symbol_pay,
        c2_value_hits,
    )


@njit(nogil=True)
def shuffle_segment(values, start, end):
    for index in range(end - 1, start, -1):
        selected = np.random.randint(start, index + 1)
        temp = values[index]
        values[index] = values[selected]
        values[selected] = temp


@njit(nogil=True)
def append_free_tables(target, current_length, counts, table_offset):
    start = current_length
    for table_index in range(counts.shape[0]):
        for _ in range(counts[table_index]):
            if current_length >= target.shape[0]:
                return current_length
            target[current_length] = table_offset + table_index
            current_length += 1
    shuffle_segment(target, start, current_length)
    return current_length


@njit(nogil=True)
def get_bucket(win, coin_in):
    multiplier = win / coin_in
    for index in range(THRESHOLD_RECORD.shape[0]):
        if multiplier <= THRESHOLD_RECORD[index]:
            return index
    return THRESHOLD_RECORD.shape[0] - 1


@njit(nogil=True)
def run_free_game_session(record, profile_index, bet_mode, bet_multi, coin_in):
    free_tables = np.full(MAX_FREE_SPINS, -1, dtype=np.int64)
    table_offset = 9 if bet_mode == MODE_SUPERFEATUREBUY else 4
    scheduled = append_free_tables(free_tables, 0, FREE_INITIAL_COUNTS[profile_index], table_offset)
    spin_index = 0
    cumulative_multiplier = 0
    fg_session_pay = 0

    while spin_index < scheduled and spin_index < MAX_FREE_SPINS:
        fg_table_id = free_tables[spin_index]
        raw_fg, fg_scatter_pay, fg_scatter_count, fg_c2, fg_c2_count, fg_cascades, fg_hits, fg_raw_symbol_pay, fg_c2_hits = play_cluster_spin(fg_table_id, profile_index, 1, bet_multi)
        cumulative_multiplier += fg_c2
        effective_multiplier = cumulative_multiplier if cumulative_multiplier > 0 else 1
        fg_spin_pay = raw_fg * effective_multiplier + fg_scatter_pay
        fg_session_pay += fg_spin_pay
        record[R_ALL, RA_FG_SPINS] += 1
        record[R_ALL, RA_HITS_FG] += 1 if fg_spin_pay > 0 else 0
        record[R_ALL, RA_FG_CASCADES] += fg_cascades
        record[R_ALL, RA_C2_COUNT_FG] += fg_c2_count
        if cumulative_multiplier > record[R_ALL, RA_MAX_C2_MULTIPLIER]:
            record[R_ALL, RA_MAX_C2_MULTIPLIER] = cumulative_multiplier

        record[R_CASCADE_FG, min(fg_cascades, RECORD_COLS - 1)] += 1
        record[R_SCATTER_FG, min(fg_scatter_count, 7)] += 1
        for symbol in range(SYMBOL_COUNT):
            record[R_SYMBOL_HIT_FG, symbol] += fg_hits[symbol]
            record[R_SYMBOL_PAY_FG, symbol] += fg_raw_symbol_pay[symbol] * effective_multiplier
        record[R_SYMBOL_PAY_FG, C1] += fg_scatter_pay
        for index in range(fg_c2_hits.shape[0]):
            record[R_C2_VALUE_FG, index] += fg_c2_hits[index]

        if fg_scatter_count >= 3 and scheduled < MAX_FREE_SPINS:
            previous = scheduled
            scheduled = append_free_tables(free_tables, scheduled, FREE_RETRIGGER_COUNTS[profile_index], table_offset)
            if scheduled > previous:
                record[R_ALL, RA_RETRIGGER] += 1
        spin_index += 1

    record[R_ALL, RA_PAY_FG] += fg_session_pay
    fg_bucket = get_bucket(fg_session_pay, coin_in)
    record[R_MULTI_CNT_FG, fg_bucket] += 1
    record[R_MULTI_PAY_FG, fg_bucket] += fg_session_pay
    return fg_session_pay


@njit(nogil=True)
def simulator_chunk(total_round, bet_mode, bet_multi):
    record = np.zeros(RECORD_SIZE, dtype=np.float64)
    profile_index = 0
    if bet_mode == MODE_FEATUREBUY:
        profile_index = 1
    elif bet_mode == MODE_SUPERFEATUREBUY:
        profile_index = 2

    coin_in = DEFAULT_COIN_IN * NORMALBET * bet_multi
    if bet_mode == MODE_FEATUREBUY:
        coin_in = DEFAULT_COIN_IN * FEATUREBUY * bet_multi
    elif bet_mode == MODE_SUPERFEATUREBUY:
        coin_in = DEFAULT_COIN_IN * SUPERFEATUREBUY * bet_multi
    card_coin_in = DEFAULT_COIN_IN * NORMALBET * bet_multi
    bg_card_profile = CARD_PROFILE_NEWBIE_BG if CARD_SYSTEM_IS_NEWBIE else CARD_PROFILE_OLDHAND_BG
    fg_card_profile = CARD_PROFILE_NEWBIE_FG if CARD_SYSTEM_IS_NEWBIE else CARD_PROFILE_OLDHAND_FG
    package_card_profile = CARD_PROFILE_BUY_FEATURE if bet_mode == MODE_FEATUREBUY else CARD_PROFILE_SUPER_FEATURE
    accepted_rounds = 0
    retry_count = 0
    retry_total = 0
    retry_limit_exceeded = 0
    retry_fail_bg_range = 0
    retry_fail_bg_freegame = 0
    retry_fail_fg = 0
    bg_card_index = -1
    fg_card_index = -1
    package_card_index = -1

    while accepted_rounds < total_round:
        if retry_count == 0:
            fg_card_index = -1
            if CARD_SYSTEM_ENABLED:
                if bet_mode == MODE_NORMALBET:
                    bg_card_index = pick_card(bg_card_profile)
                    package_card_index = -1
                else:
                    bg_card_index = -1
                    package_card_index = pick_card(package_card_profile)
            else:
                bg_card_index = -1
                package_card_index = -1
        record_before_attempt = record.copy()
        table_id = choose_base_table(profile_index)
        raw_bg, scatter_pay, scatter_count, bg_c2, bg_c2_count, bg_cascades, bg_hits, bg_raw_symbol_pay, bg_c2_hits = play_cluster_spin(table_id, profile_index, 0, bet_multi)
        bg_multiplier = bg_c2 if bg_c2 > 0 else 1
        bg_cluster_pay = raw_bg * bg_multiplier
        bg_pay = bg_cluster_pay + scatter_pay
        total_pay = bg_pay

        record[R_ALL, RA_TOTAL_ROUNDS] += 1
        record[R_ALL, RA_COIN_IN_SUM] += coin_in
        record[R_ALL, RA_PAY_BG_CLUSTER] += bg_cluster_pay
        record[R_ALL, RA_PAY_BG_SCATTER] += scatter_pay
        record[R_ALL, RA_HITS_BG] += 1 if bg_pay > 0 else 0
        record[R_ALL, RA_BG_CASCADES] += bg_cascades
        record[R_ALL, RA_C2_COUNT_BG] += bg_c2_count
        if bg_c2 > record[R_ALL, RA_MAX_C2_MULTIPLIER]:
            record[R_ALL, RA_MAX_C2_MULTIPLIER] = bg_c2

        record[R_CASCADE_BG, min(bg_cascades, RECORD_COLS - 1)] += 1
        record[R_SCATTER_BG, min(scatter_count, 7)] += 1
        for symbol in range(SYMBOL_COUNT):
            record[R_SYMBOL_HIT_BG, symbol] += bg_hits[symbol]
            record[R_SYMBOL_PAY_BG, symbol] += bg_raw_symbol_pay[symbol] * bg_multiplier
        record[R_SYMBOL_PAY_BG, C1] += scatter_pay
        for index in range(bg_c2_hits.shape[0]):
            record[R_C2_VALUE_BG, index] += bg_c2_hits[index]

        bg_bucket = get_bucket(bg_pay, coin_in)
        record[R_MULTI_CNT_BG, bg_bucket] += 1
        record[R_MULTI_PAY_BG, bg_bucket] += bg_pay

        record_after_bg = record.copy()
        fg_session_pay = 0
        if scatter_count >= 4:
            if CARD_SYSTEM_ENABLED and bet_mode == MODE_NORMALBET and bg_card_index >= 0 and CARD_TYPES[bg_card_profile, bg_card_index] == CARD_TYPE_FREE_GAME and fg_card_index < 0:
                fg_card_index = pick_card(fg_card_profile)
            fg_retry_count = 0
            while True:
                record = record_after_bg.copy()
                record[R_ALL, RA_FG_TRIGGER] += 1
                fg_session_pay = run_free_game_session(record, profile_index, bet_mode, bet_multi, coin_in)
                total_pay = bg_pay + fg_session_pay
                needs_fg_match = CARD_SYSTEM_ENABLED and bet_mode == MODE_NORMALBET and bg_card_index >= 0 and CARD_TYPES[bg_card_profile, bg_card_index] == CARD_TYPE_FREE_GAME
                if not needs_fg_match or is_card_match(fg_card_profile, fg_card_index, fg_session_pay, card_coin_in, 1):
                    break
                retry_total += 1
                retry_fail_fg += 1
                fg_retry_count += 1
                if fg_retry_count >= CARD_RETRY_LIMIT:
                    retry_limit_exceeded += 1
                    break

        record[R_ALL, RA_PAY_TOTAL] += total_pay
        multiplier_x = total_pay / coin_in
        record[R_ALL, RA_X_SUM] += multiplier_x
        record[R_ALL, RA_X_SQUARE] += multiplier_x * multiplier_x
        if total_pay > record[R_ALL, RA_MAX_SINGLE_WIN]:
            record[R_ALL, RA_MAX_SINGLE_WIN] = total_pay
            record[R_ALL, RA_MAX_WIN_HITS] = 1
        elif total_pay == record[R_ALL, RA_MAX_SINGLE_WIN]:
            record[R_ALL, RA_MAX_WIN_HITS] += 1
        overall_bucket = get_bucket(total_pay, coin_in)
        record[R_MULTI_CNT_OA, overall_bucket] += 1
        record[R_MULTI_PAY_OA, overall_bucket] += total_pay
        accepted = 1
        fail_reason = 0
        triggered_free_game = 1 if scatter_count >= 4 else 0
        if CARD_SYSTEM_ENABLED:
            if bet_mode == MODE_NORMALBET:
                if bg_card_index >= 0 and CARD_TYPES[bg_card_profile, bg_card_index] == CARD_TYPE_FREE_GAME:
                    if triggered_free_game == 0:
                        accepted = 0
                        fail_reason = 2
                elif triggered_free_game == 1 or not is_card_match(bg_card_profile, bg_card_index, bg_pay, card_coin_in, 0):
                    accepted = 0
                    fail_reason = 1
            elif not is_card_match(package_card_profile, package_card_index, total_pay, card_coin_in, triggered_free_game):
                accepted = 0
                fail_reason = 3

        if accepted == 0:
            retry_total += 1
            if fail_reason == 1:
                retry_fail_bg_range += 1
            elif fail_reason == 2:
                retry_fail_bg_freegame += 1
            else:
                retry_fail_fg += 1
            retry_count += 1
            if retry_count < CARD_RETRY_LIMIT:
                record = record_before_attempt
                continue
            retry_limit_exceeded += 1

        accepted_rounds += 1
        retry_count = 0

    record[R_ALL, RA_RETRY_TOTAL] += retry_total
    record[R_ALL, RA_RETRY_LIMIT_EXCEEDED] += retry_limit_exceeded
    record[R_ALL, RA_RETRY_FAIL_BG_RANGE] += retry_fail_bg_range
    record[R_ALL, RA_RETRY_FAIL_BG_FREEGAME] += retry_fail_bg_freegame
    record[R_ALL, RA_RETRY_FAIL_FG] += retry_fail_fg
    return record


def split_rounds(total_round, threads):
    workers = max(1, min(int(threads), int(total_round)))
    base, remainder = divmod(int(total_round), workers)
    return [base + (1 if index < remainder else 0) for index in range(workers)]


def merge_records(records):
    merged = np.sum(np.stack(records), axis=0)
    merged[R_ALL, RA_MAX_SINGLE_WIN] = max(item[R_ALL, RA_MAX_SINGLE_WIN] for item in records)
    merged[R_ALL, RA_MAX_WIN_HITS] = sum(item[R_ALL, RA_MAX_WIN_HITS] for item in records if item[R_ALL, RA_MAX_SINGLE_WIN] == merged[R_ALL, RA_MAX_SINGLE_WIN])
    merged[R_ALL, RA_MAX_C2_MULTIPLIER] = max(item[R_ALL, RA_MAX_C2_MULTIPLIER] for item in records)
    return merged


def run_simulation(total_round=TOTAL_ROUNDS, bet_mode=BET_MODE, bet_multi=BET_MULTI, threads=THREADS):
    if bet_mode not in PROFILE_BY_MODE:
        raise ValueError(f"Unsupported bet mode: {bet_mode}")
    simulator_chunk(1, bet_mode, bet_multi)
    chunks = split_rounds(total_round, threads)
    start = time.perf_counter()
    if len(chunks) == 1:
        record = simulator_chunk(chunks[0], bet_mode, bet_multi)
    else:
        with ThreadPoolExecutor(max_workers=len(chunks)) as executor:
            futures = [executor.submit(simulator_chunk, rounds, bet_mode, bet_multi) for rounds in chunks]
            record = merge_records([future.result() for future in futures])
    return record, time.perf_counter() - start, calc_coin_in(bet_mode, bet_multi)


def format_threshold_labels(thresholds):
    labels = []
    for index, current in enumerate(thresholds):
        labels.append("0" if index == 0 else f"{thresholds[index - 1]:g} < X <= {current:g}")
    return labels


def build_result_frames(record, total_round, duration, coin_in, bet_mode, bet_multi):
    values = record.astype(np.float64)
    coin_in_sum = values[R_ALL, RA_COIN_IN_SUM]
    pay_total = values[R_ALL, RA_PAY_TOTAL]
    pay_bg_cluster = values[R_ALL, RA_PAY_BG_CLUSTER]
    pay_bg_scatter = values[R_ALL, RA_PAY_BG_SCATTER]
    pay_fg = values[R_ALL, RA_PAY_FG]
    fg_sessions = values[R_ALL, RA_FG_TRIGGER]
    fg_spins = values[R_ALL, RA_FG_SPINS]
    variance = values[R_ALL, RA_X_SQUARE] / total_round - (values[R_ALL, RA_X_SUM] / total_round) ** 2

    summary = {
        "game_id": GAME_ID,
        "parsheet_id": PARSHEET_ID,
        "version": CONFIG_VERSION,
        "config_file": CONFIG_FILE,
        "bet_mode": format_bet_mode_label(bet_mode),
        "total_rounds": total_round,
        "threads": THREADS,
        "duration_seconds": duration,
        "games_per_second": total_round / duration if duration else 0,
        "coin_in": coin_in,
        "rtp_total": pay_total / coin_in_sum if coin_in_sum else 0,
        "rtp_bg_cluster": pay_bg_cluster / coin_in_sum if coin_in_sum else 0,
        "rtp_bg_scatter": pay_bg_scatter / coin_in_sum if coin_in_sum else 0,
        "rtp_bg": (pay_bg_cluster + pay_bg_scatter) / coin_in_sum if coin_in_sum else 0,
        "rtp_fg": pay_fg / coin_in_sum if coin_in_sum else 0,
        "hit_rate_bg": values[R_ALL, RA_HITS_BG] / total_round,
        "hit_rate_fg": values[R_ALL, RA_HITS_FG] / fg_spins if fg_spins else 0,
        "fg_trigger_rate": fg_sessions / total_round,
        "fg_trigger_count": int(fg_sessions),
        "retrigger_per_fg": values[R_ALL, RA_RETRIGGER] / fg_sessions if fg_sessions else 0,
        "retrigger_rate": values[R_ALL, RA_RETRIGGER] / fg_sessions if fg_sessions else 0,
        "avg_fg_multiplier": (pay_fg / coin_in_sum) / (fg_sessions / total_round) if coin_in_sum and fg_sessions else 0,
        "avg_fg_spins": fg_spins / fg_sessions if fg_sessions else 0,
        "volatility_std": math.sqrt(max(0.0, variance)),
        "max_win_x": values[R_ALL, RA_MAX_SINGLE_WIN] / coin_in if coin_in else 0,
        "max_c2_multiplier": int(values[R_ALL, RA_MAX_C2_MULTIPLIER]),
        "avg_bg_cascades": values[R_ALL, RA_BG_CASCADES] / total_round,
        "avg_fg_cascades": values[R_ALL, RA_FG_CASCADES] / fg_spins if fg_spins else 0,
        "card_system": "on" if CARD_SYSTEM_ENABLED else "off",
        "card_system_profile": "off" if not CARD_SYSTEM_ENABLED else ("newbie" if CARD_SYSTEM_IS_NEWBIE and bet_mode == MODE_NORMALBET else ("oldhand" if bet_mode == MODE_NORMALBET else format_bet_mode_label(bet_mode))),
        "retry_limit": CARD_RETRY_LIMIT if CARD_SYSTEM_ENABLED else 0,
        "retry_total": int(values[R_ALL, RA_RETRY_TOTAL]),
        "avg_retry": values[R_ALL, RA_RETRY_TOTAL] / total_round,
        "retry_limit_exceeded": int(values[R_ALL, RA_RETRY_LIMIT_EXCEEDED]),
        "retry_fail_bg_range": int(values[R_ALL, RA_RETRY_FAIL_BG_RANGE]),
        "retry_fail_bg_freegame": int(values[R_ALL, RA_RETRY_FAIL_BG_FREEGAME]),
        "retry_fail_fg": int(values[R_ALL, RA_RETRY_FAIL_FG]),
    }

    base_frame = pd.DataFrame({"Index": list(summary.keys()), "Value": list(summary.values())})
    multiplier_frame = pd.DataFrame(
        {
            "Interval": format_threshold_labels(THRESHOLD_RECORD),
            "base_game_cnt": values[R_MULTI_CNT_BG, : len(THRESHOLD_RECORD)],
            "base_game_pay": values[R_MULTI_PAY_BG, : len(THRESHOLD_RECORD)],
            "free_game_cnt": values[R_MULTI_CNT_FG, : len(THRESHOLD_RECORD)],
            "free_game_pay": values[R_MULTI_PAY_FG, : len(THRESHOLD_RECORD)],
            "overall_cnt": values[R_MULTI_CNT_OA, : len(THRESHOLD_RECORD)],
            "overall_pay": values[R_MULTI_PAY_OA, : len(THRESHOLD_RECORD)],
        }
    )
    symbol_frame = pd.DataFrame(
        {
            "Symbol": SYMBOL_CODES,
            "BG_Hit": values[R_SYMBOL_HIT_BG, :SYMBOL_COUNT],
            "BG_Pay": values[R_SYMBOL_PAY_BG, :SYMBOL_COUNT],
            "FG_Hit": values[R_SYMBOL_HIT_FG, :SYMBOL_COUNT],
            "FG_Pay": values[R_SYMBOL_PAY_FG, :SYMBOL_COUNT],
        }
    )
    cascade_frame = pd.DataFrame(
        {
            "Cascade_Count": np.arange(20),
            "BG_Count": values[R_CASCADE_BG, :20],
            "FG_Count": values[R_CASCADE_FG, :20],
        }
    )
    profile_index = PROFILE_BY_MODE[bet_mode]
    c2_values = C2_MULTIPLIERS[profile_index]
    valid = c2_values > 0
    c2_frame = pd.DataFrame(
        {
            "Multiplier": c2_values[valid],
            "BG_Count": values[R_C2_VALUE_BG, : C2_MULTIPLIERS.shape[1]][valid],
            "FG_Count": values[R_C2_VALUE_FG, : C2_MULTIPLIERS.shape[1]][valid],
        }
    )
    scatter_frame = pd.DataFrame(
        {
            "Scatter_Count": ["0", "1", "2", "3", "4", "5", "6", "7+"],
            "BG_Count": values[R_SCATTER_BG, :8],
            "FG_Count": values[R_SCATTER_FG, :8],
        }
    )
    return summary, base_frame, multiplier_frame, symbol_frame, cascade_frame, c2_frame, scatter_frame


def format_elapsed_time(seconds):
    total_seconds = max(0, int(round(float(seconds))))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}h {minutes}m {secs}s"


def show_console(summary):
    fg_trigger_count = int(summary["fg_trigger_count"])
    print(f"* game_id: {summary['game_id']}", flush=True)
    print(f"* version: {summary['version']}", flush=True)
    print(f"* bet_mode: {summary['bet_mode']}", flush=True)
    print(f"* duration: {format_elapsed_time(summary['duration_seconds'])}", flush=True)
    print(f"* rtp_total: {summary['rtp_total'] * 100:.2f}%", flush=True)
    print(f"* rtp_bg: {summary['rtp_bg'] * 100:.2f}%", flush=True)
    print(f"* rtp_fg: {summary['rtp_fg'] * 100:.2f}%", flush=True)
    print(f"* volatility_std: {summary['volatility_std']:.6f}", flush=True)
    print(f"* hit_rate_bg: {summary['hit_rate_bg']:.2f}", flush=True)
    print(f"* hit_rate_fg: {summary['hit_rate_fg']:.2f}", flush=True)
    print(f"* fg_trigger_rate: {summary['fg_trigger_rate']:.2f} ({fg_trigger_count} spins)", flush=True)
    print(f"* retrigger_rate: {summary['retrigger_rate']:.2f}", flush=True)
    print(f"* avg_fg_multiplier: {summary['avg_fg_multiplier']:.2f} x", flush=True)
    print(f"* avg_fg_spins: {summary['avg_fg_spins']:.2f} spins", flush=True)
    print(f"* card_system: {summary['card_system']}", flush=True)


def format_rounds_tag(rounds):
    rounds = int(rounds)
    if rounds > 0:
        exponent = 0
        value = rounds
        while value % 10 == 0:
            value //= 10
            exponent += 1
        if value == 1 and exponent > 0:
            return f"10{exponent}"
    return str(rounds)


def format_version_tag(version):
    return re.sub(r"[^0-9A-Za-z]+", "", str(version or "").strip())


def output_report(frames, record, bet_mode, total_round):
    _, base_frame, multiplier_frame, symbol_frame, cascade_frame, c2_frame, scatter_frame = frames
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    profile_suffix = ""
    if CARD_SYSTEM_ENABLED and bet_mode == MODE_NORMALBET:
        profile_suffix = "_newbie" if CARD_SYSTEM_IS_NEWBIE else "_oldhand"
    card_suffix = "_card" if CARD_SYSTEM_ENABLED else ""
    filename = f"{PARSHEET_ID}_{format_version_tag(CONFIG_VERSION)}_{timestamp}_" f"betmode{bet_mode}_{format_rounds_tag(total_round)}{profile_suffix}{card_suffix}.xlsx"
    path = OUTPUT_DIR / filename
    with pd.ExcelWriter(path) as writer:
        base_frame.to_excel(writer, sheet_name="Base Info", index=False)
        multiplier_frame.to_excel(writer, sheet_name="Multiplier Line", index=False)
        symbol_frame.to_excel(writer, sheet_name="Symbol Summary", index=False)
        cascade_frame.to_excel(writer, sheet_name="Cascade", index=False)
        c2_frame.to_excel(writer, sheet_name="C2 Multiplier", index=False)
        scatter_frame.to_excel(writer, sheet_name="Scatter Dist", index=False)
        pd.DataFrame(record).to_excel(writer, sheet_name="Record Data", index=False)
    return path


def run_single_spin_debug():
    profile = PROFILE_BY_MODE[BET_MODE]
    table_id = 8 if BET_MODE != MODE_NORMALBET else 0
    result = play_cluster_spin(table_id, profile, 0, BET_MULTI)
    print("Single spin result:")
    print(f"raw_cluster_pay={result[0]}, scatter_pay={result[1]}, scatter_count={result[2]}")
    print(f"c2_multiplier={result[3]}, c2_count={result[4]}, cascades={result[5]}")


def run_batch_combinations():
    total_jobs = len(BATCH_COMBINATIONS)
    for index, combo in enumerate(BATCH_COMBINATIONS, start=1):
        print(
            f"\n=== Batch {index}/{total_jobs}: " f"config={combo['config_file']}, bet_mode={combo['bet_mode']}, " f"rounds={combo['total_rounds']}, card={combo.get('card_system_enabled', CARD_SYSTEM_ENABLED)}, " f"newbie={combo.get('card_system_is_newbie', CARD_SYSTEM_IS_NEWBIE)} ===",
            flush=True,
        )
        env = os.environ.copy()
        env["H019_CONFIG_FILE"] = combo["config_file"]
        env["H019_BET_MODE"] = str(combo["bet_mode"])
        env["H019_TOTAL_ROUNDS"] = str(combo["total_rounds"])
        env["H019_CARD_SYSTEM_ENABLED"] = "true" if combo.get("card_system_enabled", CARD_SYSTEM_ENABLED) else "false"
        env["H019_CARD_SYSTEM_IS_NEWBIE"] = "true" if combo.get("card_system_is_newbie", CARD_SYSTEM_IS_NEWBIE) else "false"
        env["H019_RUN_ALL_COMBINATIONS"] = "false"
        env["H019_BATCH_CHILD"] = "1"
        env["PYTHONUTF8"] = "1"
        env["PYTHONUNBUFFERED"] = "1"
        process = subprocess.Popen(
            [sys.executable, str(SIMULATOR_PATH)],
            cwd=str(BASE_DIR),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        if process.stdout is not None:
            for line in process.stdout:
                print(line, end="", flush=True)
        return_code = process.wait()
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, process.args)


def main():
    if RUN_ALL_COMBINATIONS and os.environ.get("H019_BATCH_CHILD") != "1":
        run_batch_combinations()
        return
    if RUN_SINGLE_SPIN_DEBUG:
        run_single_spin_debug()
        return

    record, duration, coin_in = run_simulation()
    frames = build_result_frames(record, TOTAL_ROUNDS, duration, coin_in, BET_MODE, BET_MULTI)
    summary = frames[0]
    if SHOW_CONSOLE_SUMMARY:
        show_console(summary)
    if SHOW_CONSOLE_DETAIL:
        print(frames[3].to_string(index=False))
    if OUTPUT_REPORT:
        report = output_report(frames, record, BET_MODE, TOTAL_ROUNDS)
        print(f"Report: {report}")


if __name__ == "__main__":
    main()
