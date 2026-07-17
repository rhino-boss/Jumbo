import json
import math
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import numpy as np
import pandas as pd
from numba import njit

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

# ===== User Settings =====

CONFIG_FILE = "config.js"
TOTAL_ROUNDS = 10**7
BET_MULTI = 1
BET_MODE = 0
CARD_SYSTEM_ENABLED = True
CARD_SYSTEM_IS_NEWBIE = False  # True: Newbie, False: Oldhand

# H026-style batch runner. Keep False for an ordinary single run.
RUN_ALL_COMBINATIONS = True
BATCH_RUNS = [
    {"config_file": "config.js", "bet_mode": 0, "total_rounds": 10**5, "card_system_is_newbie": False, "card_system_enabled": True},
    # {"config_file": "config.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_is_newbie": True, "card_system_enabled": True},
    # {"config_file": "config.js", "bet_mode": 2, "total_rounds": 10**7, "card_system_is_newbie": False, "card_system_enabled": True},
]

# H015's card filtering can be memory-heavy. Keep the H026-style configurable
# threading, but cap the safe default so running from an IDE does not exhaust it.
THREADS = max(1, min(8, os.cpu_count() or 1))

OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = False
SHOW_CONSOLE_DETAIL = False
RUN_SINGLE_SPIN_DEBUG = False
DEBUG_ROUNDS = 1


def _parse_env_bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true/false, got {value!r}")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.environ.get("H015_CONFIG_FILE", CONFIG_FILE)
CONFIG_PATH = os.path.join(BASE_DIR, CONFIG_FILE)
OUTPUT_DIR = os.path.join(BASE_DIR, "Record")
TOTAL_ROUNDS = int(os.environ.get("H015_TOTAL_ROUNDS", str(TOTAL_ROUNDS)))
BET_MULTI = int(os.environ.get("H015_BET_MULTI", str(BET_MULTI)))
BET_MODE = int(os.environ.get("H015_BET_MODE", str(BET_MODE)))
CARD_SYSTEM_ENABLED = _parse_env_bool("H015_CARD_SYSTEM_ENABLED", CARD_SYSTEM_ENABLED)
CARD_SYSTEM_IS_NEWBIE = _parse_env_bool("H015_CARD_SYSTEM_IS_NEWBIE", CARD_SYSTEM_IS_NEWBIE)
RUN_ALL_COMBINATIONS = _parse_env_bool("H015_RUN_ALL_COMBINATIONS", RUN_ALL_COMBINATIONS)
BATCH_COMBINATIONS = list(BATCH_RUNS)
THREADS = int(os.environ.get("H015_THREADS", str(THREADS)))
OUTPUT_REPORT = _parse_env_bool("H015_OUTPUT_REPORT", OUTPUT_REPORT)
SHOW_CONSOLE_SUMMARY = _parse_env_bool("H015_SHOW_CONSOLE_SUMMARY", SHOW_CONSOLE_SUMMARY)
SHOW_CONSOLE_DETAIL = _parse_env_bool("H015_SHOW_CONSOLE_DETAIL", SHOW_CONSOLE_DETAIL)
RUN_SINGLE_SPIN_DEBUG = _parse_env_bool("H015_RUN_SINGLE_SPIN_DEBUG", RUN_SINGLE_SPIN_DEBUG)

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


# ===== Config Load =====


def _load_config(path):
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read().strip()
    start = raw.find("{")
    end = raw.rfind("}")
    return json.loads(raw[start : end + 1])


def _combo_map_to_array(raw_tables):
    combo_names = ("combo0", "combo1", "combo2", "combo3_plus")
    table_count = len(raw_tables)
    symbol_count = len(raw_tables[0]["combo0"])
    reel_count = len(raw_tables[0]["combo0"][0])
    arr = np.zeros((table_count, len(combo_names), symbol_count, reel_count), dtype=np.int64)
    for table_idx, table in enumerate(raw_tables):
        for combo_idx, combo_name in enumerate(combo_names):
            arr[table_idx, combo_idx, :, :] = np.asarray(table[combo_name], dtype=np.int64)
    return arr


CFG = _load_config(CONFIG_PATH)

GAME_ID = CFG["game_id"]
PARSHEET_ID = CFG.get("parsheet_id", "H0151")
GAME_NAME = CFG["display_name"]
GAME_VERSION = CFG.get("excel_version") or CFG.get("game_version") or ""
MODE_NORMALBET = int(CFG["mode_normalbet"])
MODE_FEATUREBUY = int(CFG["mode_featurebuy"])
SCENE_BG = int(CFG["scene_bg"])
SCENE_FG = int(CFG["scene_fg"])
SCENE_BF = int(CFG["scene_bf"])
WINDOW_SIZE = int(CFG["window_size"])
REEL_NUM = int(CFG["reel_num"])
LAYOUT_SHAPE = tuple(int(v) for v in CFG["layout_shape"])
DEFAULT_COIN_IN = int(CFG["default_coin_in"])
NORMALBET = int(CFG["normalbet"])
FEATUREBUY = int(CFG["featurebuy"])
MAX_SPIN_FREE_GAME = int(CFG["max_spin_free_game"])
DENOM = float(CFG.get("denom", 0.002))
FREE_SPIN_AWARDS = np.asarray(CFG.get("free_spin_awards", [0, 0, 0, 10, 12, 14]), dtype=np.int64)

PAY_TABLE = np.asarray(CFG["pay_table"], dtype=np.int64)
SCORE_AREA = np.asarray(CFG["score_area"], dtype=np.int64)
SPECIAL_AREA = np.asarray(CFG["special_area"], dtype=np.int64)
VALUE_MULTIPLIER_RANGE = np.asarray(CFG["value_multiplier_range"], dtype=np.int64)
ARR_REELS = np.asarray(CFG["arr_reels"], dtype=np.int64)
ARR_REELS_WEIGHT_CUM = np.asarray(CFG["arr_reels_weight_cum"], dtype=np.int64)
REELS_LEN = np.asarray(CFG["reels_len"], dtype=np.int64)
WEIGHT_CUM_TABLE_BG = np.asarray(CFG["weight_cum_table_bg"], dtype=np.int64)
WEIGHT_CUM_TABLE_FG = np.asarray(CFG["weight_cum_table_fg"], dtype=np.int64)
WEIGHT_CUM_TABLE_BF = np.asarray(CFG["weight_cum_table_bf"], dtype=np.int64)
WEIGHT_CUM_DROP_CHOOSE_BG = np.asarray(CFG["weight_cum_drop_choose_bg"], dtype=np.int64)
WEIGHT_CUM_DROP_CHOOSE_FG = np.asarray(CFG["weight_cum_drop_choose_fg"], dtype=np.int64)
WEIGHT_CUM_MUST_APPEAR_1_FG = np.asarray(CFG["weight_cum_must_appear_1_fg"], dtype=np.int64)
WEIGHT_CUM_MULTI_APPEAR_BG = np.asarray(CFG["weight_cum_multi_appear_bg"], dtype=np.int64)
WEIGHT_CUM_MULTI_APPEAR_FG = np.asarray(CFG["weight_cum_multi_appear_fg"], dtype=np.int64)
WEIGHT_CUM_DROP_SYMBOL_A = _combo_map_to_array(CFG["weight_cum_drop_symbol_a"])
WEIGHT_CUM_DROP_SYMBOL_B = _combo_map_to_array(CFG["weight_cum_drop_symbol_b"])
WEIGHT_CUM_DROP_SYMBOL_C = _combo_map_to_array(CFG["weight_cum_drop_symbol_c"])

SYMBOL_ID = np.asarray(CFG["symbol_id"], dtype=np.int64)
SYMBOL_STR = {int(k): v for k, v in CFG["symbol_str"].items()}
SYMBOLS_SCORE = np.asarray(CFG["symbols_score"], dtype=np.int64)
SYMBOLS_GOLD = np.asarray(CFG["symbols_gold"], dtype=np.int64)
SYMBOLS_ALL = np.asarray(CFG["symbols_all"], dtype=np.int64)
SYMBOL_COUNT = int(CFG["symbols_count"])

WW = int(next(k for k, v in SYMBOL_STR.items() if v == "WW"))
C1 = int(next(k for k, v in SYMBOL_STR.items() if v == "C1"))
STRIP_BF = int(CFG["strip_bf"])
SUPPORTED_BET_MODES = (MODE_NORMALBET, MODE_FEATUREBUY)

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


def _get_card_list(player, mode, segment):
    player_data = CARD_SYSTEM.get(player, {})
    mode_data = player_data.get(mode, {}) if isinstance(player_data, dict) else {}
    return list(mode_data.get(segment, [])) if isinstance(mode_data, dict) else []


CARD_PROFILE_LISTS = [
    _get_card_list("newbie", "normal_bet", "weight_bg"),
    _get_card_list("newbie", "normal_bet", "weight_fg"),
    _get_card_list("oldhand", "normal_bet", "weight_bg"),
    _get_card_list("oldhand", "normal_bet", "weight_fg"),
    _get_card_list("oldhand", "buy_feature", "weight_fg"),
]
MAX_CARDS = max(1, max((len(cards) for cards in CARD_PROFILE_LISTS), default=0))
CARD_TYPES = np.full((len(CARD_PROFILE_LISTS), MAX_CARDS), -1, dtype=np.int64)
CARD_MIN = np.zeros((len(CARD_PROFILE_LISTS), MAX_CARDS), dtype=np.float64)
CARD_MAX = np.zeros((len(CARD_PROFILE_LISTS), MAX_CARDS), dtype=np.float64)
CARD_WEIGHT_CUM = np.zeros((len(CARD_PROFILE_LISTS), MAX_CARDS), dtype=np.int64)
CARD_COUNTS = np.zeros(len(CARD_PROFILE_LISTS), dtype=np.int64)
for profile_idx, cards in enumerate(CARD_PROFILE_LISTS):
    running_weight = 0
    for card_idx, card in enumerate(cards):
        running_weight += max(0, int(card.get("weight", 0)))
        CARD_TYPES[profile_idx, card_idx] = CARD_TYPE_FREE_GAME if card.get("type") == "free_game" else CARD_TYPE_RANGE
        CARD_MIN[profile_idx, card_idx] = float(card.get("min", 0.0))
        CARD_MAX[profile_idx, card_idx] = float(card.get("max", 0.0))
        CARD_WEIGHT_CUM[profile_idx, card_idx] = running_weight
    CARD_COUNTS[profile_idx] = len(cards)

SCORE_SYMBOL_MASK = np.zeros(SYMBOL_COUNT, dtype=np.int64)
for symbol in SYMBOLS_SCORE:
    SCORE_SYMBOL_MASK[int(symbol)] = 1

GOLD_SYMBOL_MASK = np.zeros(SYMBOL_COUNT, dtype=np.int64)
for symbol in SYMBOLS_GOLD:
    GOLD_SYMBOL_MASK[int(symbol)] = 1

MULTIPLIER_LEVELS = len(VALUE_MULTIPLIER_RANGE)
SUMMARY_FIELDS = [
    "rounds",
    "coin_in_total",
    "pay_bg_total",
    "pay_fg_total",
    "hit_bg_spins",
    "fg_trigger_spins",
    "fg_spins",
    "hit_fg_spins",
    "retrigger_count",
    "bomb_used_bg",
    "bomb_used_fg",
    "max_win_multiplier",
    "max_combo_bg",
    "max_combo_fg",
    "retry_total",
    "retry_limit_exceeded",
    "retry_fail_bg_range",
    "retry_fail_bg_freegame",
    "retry_fail_fg",
    "win_x_sum",
    "win_x_square",
]
SUMMARY_IDX = {name: idx for idx, name in enumerate(SUMMARY_FIELDS)}
SUMMARY_SIZE = len(SUMMARY_FIELDS)
I_ROUNDS = 0
I_COIN_IN_TOTAL = 1
I_PAY_BG_TOTAL = 2
I_PAY_FG_TOTAL = 3
I_HIT_BG_SPINS = 4
I_FG_TRIGGER_SPINS = 5
I_FG_SPINS = 6
I_HIT_FG_SPINS = 7
I_RETRIGGER_COUNT = 8
I_BOMB_USED_BG = 9
I_BOMB_USED_FG = 10
I_MAX_WIN_MULTIPLIER = 11
I_MAX_COMBO_BG = 12
I_MAX_COMBO_FG = 13
I_RETRY_TOTAL = 14
I_RETRY_LIMIT_EXCEEDED = 15
I_RETRY_FAIL_BG_RANGE = 16
I_RETRY_FAIL_BG_FREEGAME = 17
I_RETRY_FAIL_FG = 18
I_WIN_X_SUM = 19
I_WIN_X_SQUARE = 20

SCENE_LABELS = ("BG", "FG")


# ===== Numba Core =====


@njit
def _rand_cum_index(cum_arr):
    total = int(cum_arr[-1])
    if total <= 0:
        return 0
    pick = np.random.randint(total)
    for idx in range(cum_arr.shape[0]):
        if pick < cum_arr[idx]:
            return idx
    return cum_arr.shape[0] - 1


@njit
def _pick_card(profile_idx):
    card_count = CARD_COUNTS[profile_idx]
    if card_count <= 0:
        return -1
    return _rand_cum_index(CARD_WEIGHT_CUM[profile_idx, :card_count])


@njit
def _is_card_match(profile_idx, card_idx, score, card_coin_in, triggered_free_game):
    if card_idx < 0:
        return True
    if CARD_TYPES[profile_idx, card_idx] == CARD_TYPE_FREE_GAME:
        return triggered_free_game == 1
    multiplier = score / card_coin_in
    return multiplier > CARD_MIN[profile_idx, card_idx] and multiplier <= CARD_MAX[profile_idx, card_idx]


@njit
def _copy_special_area():
    arr = np.empty_like(SPECIAL_AREA)
    for r in range(SPECIAL_AREA.shape[0]):
        for c in range(SPECIAL_AREA.shape[1]):
            arr[r, c] = SPECIAL_AREA[r, c]
    return arr


@njit
def _generate_board(table_id, board, rng):
    for reel_idx in range(REEL_NUM):
        stop = _rand_cum_index(ARR_REELS_WEIGHT_CUM[table_id, : REELS_LEN[table_id, reel_idx], reel_idx])
        rng[reel_idx] = stop
        for row_idx in range(WINDOW_SIZE):
            board[row_idx, reel_idx] = ARR_REELS[table_id, (stop + row_idx) % REELS_LEN[table_id, reel_idx], reel_idx]


@njit
def _apply_score_area(board):
    for row_idx in range(WINDOW_SIZE):
        for reel_idx in range(REEL_NUM):
            if SCORE_AREA[row_idx, reel_idx] == 0:
                board[row_idx, reel_idx] = 99


@njit
def _restore_gold_symbols(board, gold_mask):
    for row_idx in range(WINDOW_SIZE):
        for reel_idx in range(REEL_NUM):
            symbol = board[row_idx, reel_idx]
            if symbol >= 0 and symbol < SYMBOL_COUNT and GOLD_SYMBOL_MASK[symbol] == 1:
                board[row_idx, reel_idx] = symbol - 8
                gold_mask[row_idx, reel_idx] = 1


@njit
def _get_pay(symbol, line_length):
    if symbol >= 0 and symbol < SYMBOL_COUNT and SCORE_SYMBOL_MASK[symbol] == 1 and line_length >= 3:
        return PAY_TABLE[symbol, line_length - 3]
    return 0


@njit
def _evaluate_board(board, special_pos, gold_mask, pay_symbol, pay_way, pay_line, pay_unit):
    for idx in range(pay_symbol.shape[0]):
        pay_symbol[idx] = 99
        pay_way[idx] = 0
        pay_line[idx] = 0
        pay_unit[idx] = 0

    special_copy = np.empty_like(special_pos)
    for r in range(special_pos.shape[0]):
        for c in range(special_pos.shape[1]):
            special_copy[r, c] = special_pos[r, c]

    unique_symbols = np.full(REEL_NUM, 99, dtype=np.int64)
    unique_count = 0
    for row_idx in range(WINDOW_SIZE):
        symbol = board[row_idx, 0]
        if symbol == 99:
            continue
        exists = False
        for idx in range(unique_count):
            if unique_symbols[idx] == symbol:
                exists = True
                break
        if not exists:
            unique_symbols[unique_count] = symbol
            unique_count += 1

    total_pay = 0
    hit_count = 0
    for sym_idx in range(unique_count):
        symbol = unique_symbols[sym_idx]
        line_length = 0
        ways = 1
        for reel_idx in range(REEL_NUM):
            matched = 0
            for row_idx in range(WINDOW_SIZE):
                cell = board[row_idx, reel_idx]
                if cell == symbol or cell == WW:
                    matched += 1
            if matched == 0:
                break
            line_length += 1
            ways *= matched

        pay_unit_value = _get_pay(symbol, line_length)
        if pay_unit_value <= 0:
            continue

        total_pay += pay_unit_value * ways
        if hit_count < pay_symbol.shape[0]:
            pay_symbol[hit_count] = symbol
            pay_way[hit_count] = ways
            pay_line[hit_count] = line_length
            pay_unit[hit_count] = pay_unit_value
            hit_count += 1

        for reel_idx in range(line_length):
            for row_idx in range(WINDOW_SIZE):
                cell = board[row_idx, reel_idx]
                if special_copy[row_idx, reel_idx] == 99:
                    continue
                if cell == symbol or cell == WW:
                    special_copy[row_idx, reel_idx] = 2 if gold_mask[row_idx, reel_idx] == 1 else 1

    for r in range(special_pos.shape[0]):
        for c in range(special_pos.shape[1]):
            special_pos[r, c] = special_copy[r, c]

    return total_pay, hit_count


@njit
def _apply_cascade(table_id, combo_idx, board, special_pos, gold_mask, drop_table):
    drop_combo_idx = combo_idx if combo_idx < 3 else 3
    for row_idx in range(WINDOW_SIZE):
        for reel_idx in range(REEL_NUM):
            flag = special_pos[row_idx, reel_idx]
            if flag == 1:
                board[row_idx, reel_idx] = _rand_cum_index(drop_table[table_id, drop_combo_idx, :, reel_idx])
            elif flag == 2:
                board[row_idx, reel_idx] = WW
                gold_mask[row_idx, reel_idx] = 0


@njit
def _count_symbol(board, target):
    count = 0
    for row_idx in range(WINDOW_SIZE):
        for reel_idx in range(REEL_NUM):
            if board[row_idx, reel_idx] == target:
                count += 1
    return count


@njit
def _increment_bucket(buckets, value):
    idx = value
    if idx >= buckets.shape[0] - 1:
        idx = buckets.shape[0] - 1
    buckets[idx] += 1


@njit
def _get_free_spins_award(scatter_count):
    if scatter_count >= 0 and scatter_count < FREE_SPIN_AWARDS.shape[0]:
        award = int(FREE_SPIN_AWARDS[scatter_count])
        if award > 0:
            return award
    if scatter_count >= 3:
        return 10 + (scatter_count - 3) * 2
    return 0


@njit
def _record_hits_pay(hit_counts, pay_amounts, scene_idx, pay_symbol, pay_way, pay_line, pay_unit, hit_count, applied_multiplier, bet_multi):
    for idx in range(hit_count):
        symbol = pay_symbol[idx]
        hit_counts[scene_idx, symbol] += pay_way[idx]
        pay_amounts[scene_idx, symbol] += pay_unit[idx] * pay_way[idx] * applied_multiplier * bet_multi


@njit
def _record_threshold(threshold_count, threshold_pay, scene_idx, value, pay_value):
    bucket = threshold_count.shape[1] - 1
    for idx in range(threshold_count.shape[1]):
        if value <= THRESHOLD_RECORD[idx]:
            bucket = idx
            break
    threshold_count[scene_idx, bucket] += 1
    threshold_pay[scene_idx, bucket] += pay_value


@njit
def _run_spin(scene_mode, bet_mode, bet_multi, force_first_light, summary, hit_counts, pay_amounts, combo_counts):
    rng = np.zeros(REEL_NUM, dtype=np.int64)
    board = np.zeros((WINDOW_SIZE, REEL_NUM), dtype=np.int64)
    gold_mask = np.zeros((WINDOW_SIZE, REEL_NUM), dtype=np.int64)
    pay_symbol = np.full(8, 99, dtype=np.int64)
    pay_way = np.zeros(8, dtype=np.int64)
    pay_line = np.zeros(8, dtype=np.int64)
    pay_unit = np.zeros(8, dtype=np.int64)

    if scene_mode == SCENE_BG:
        table_id = _rand_cum_index(WEIGHT_CUM_TABLE_BG)
        drop_idx = _rand_cum_index(WEIGHT_CUM_DROP_CHOOSE_BG)
        multi_idx_base = table_id * 3 + drop_idx
        if bet_mode == MODE_FEATUREBUY:
            table_id = STRIP_BF
            multi_idx_base = drop_idx
    else:
        if bet_mode == MODE_FEATUREBUY:
            table_id = _rand_cum_index(WEIGHT_CUM_TABLE_BF) + 2
        else:
            table_id = _rand_cum_index(WEIGHT_CUM_TABLE_FG) + 2
        drop_idx = _rand_cum_index(WEIGHT_CUM_DROP_CHOOSE_FG)
        multi_idx_base = (table_id - 2) * 3 + drop_idx

    drop_table = WEIGHT_CUM_DROP_SYMBOL_A
    if drop_idx == 1:
        drop_table = WEIGHT_CUM_DROP_SYMBOL_B
    elif drop_idx == 2:
        drop_table = WEIGHT_CUM_DROP_SYMBOL_C

    _generate_board(table_id, board, rng)
    _apply_score_area(board)
    _restore_gold_symbols(board, gold_mask)

    combo_idx = 0
    multiplier_level = 0 if scene_mode == SCENE_BG else 3
    total_pay = 0
    winning_cascades = 0
    used_bomb = 0
    while True:
        special_pos = _copy_special_area()

        if scene_mode == SCENE_BG:
            weight_idx = multiplier_level if multiplier_level <= 4 else 4
            bomb_count = _rand_cum_index(WEIGHT_CUM_MULTI_APPEAR_BG[weight_idx, :, multi_idx_base])
        else:
            weight_idx = multiplier_level - 3
            if weight_idx < 0:
                weight_idx = 0
            if weight_idx > 4:
                weight_idx = 4
            bomb_count = _rand_cum_index(WEIGHT_CUM_MULTI_APPEAR_FG[weight_idx, :, multi_idx_base])

        cascade_pay_raw, hit_count = _evaluate_board(board, special_pos, gold_mask, pay_symbol, pay_way, pay_line, pay_unit)
        _apply_cascade(table_id, combo_idx, board, special_pos, gold_mask, drop_table)
        _restore_gold_symbols(board, gold_mask)

        if scene_mode == SCENE_FG and combo_idx == 0 and force_first_light == 1 and bomb_count == 0:
            multiplier_level = min(multiplier_level + 1, MULTIPLIER_LEVELS - 1)
        else:
            multiplier_level = min(multiplier_level + bomb_count, MULTIPLIER_LEVELS - 1)

        multiplier_value = VALUE_MULTIPLIER_RANGE[multiplier_level]
        multiplier_level = min(multiplier_level + 1, MULTIPLIER_LEVELS - 1)
        combo_idx += 1

        if cascade_pay_raw <= 0:
            break

        winning_cascades += 1
        cascade_pay = cascade_pay_raw * multiplier_value * bet_multi
        total_pay += cascade_pay
        _record_hits_pay(
            hit_counts,
            pay_amounts,
            0 if scene_mode == SCENE_BG else 1,
            pay_symbol,
            pay_way,
            pay_line,
            pay_unit,
            hit_count,
            multiplier_value,
            bet_multi,
        )
        if bomb_count > 0 and cascade_pay > 0:
            used_bomb = 1

    _increment_bucket(combo_counts[0 if scene_mode == SCENE_BG else 1], winning_cascades)
    if scene_mode == SCENE_BG:
        if winning_cascades > summary[I_MAX_COMBO_BG]:
            summary[I_MAX_COMBO_BG] = winning_cascades
    else:
        if winning_cascades > summary[I_MAX_COMBO_FG]:
            summary[I_MAX_COMBO_FG] = winning_cascades

    scatter_count = _count_symbol(board, C1)
    return total_pay, scatter_count, winning_cascades > 0, used_bomb


@njit
def _run_free_game_session(scatter_bg, bet_mode, bet_multi, summary, hit_counts, pay_amounts, combo_counts):
    pay_fg = 0.0
    summary[I_FG_TRIGGER_SPINS] += 1
    free_spins = _get_free_spins_award(scatter_bg)
    guaranteed_light_spin = _rand_cum_index(WEIGHT_CUM_MUST_APPEAR_1_FG)
    fg_spin_idx = 0
    while fg_spin_idx < free_spins and fg_spin_idx < MAX_SPIN_FREE_GAME:
        force_first_light = 1 if guaranteed_light_spin == fg_spin_idx + 1 else 0
        spin_pay, spin_scatter, hit_fg, bomb_fg = _run_spin(
            SCENE_FG,
            bet_mode,
            bet_multi,
            force_first_light,
            summary,
            hit_counts,
            pay_amounts,
            combo_counts,
        )
        pay_fg += spin_pay
        summary[I_FG_SPINS] += 1
        if hit_fg:
            summary[I_HIT_FG_SPINS] += 1
        if bomb_fg:
            summary[I_BOMB_USED_FG] += 1
        if spin_scatter >= 3:
            free_spins += _get_free_spins_award(spin_scatter)
            summary[I_RETRIGGER_COUNT] += 1
        fg_spin_idx += 1
    return pay_fg


@njit
def _simulate_chunk(total_rounds, bet_mode, bet_multi, seed):
    np.random.seed(seed)

    summary = np.zeros(SUMMARY_SIZE, dtype=np.float64)
    hit_counts = np.zeros((2, SYMBOL_COUNT), dtype=np.float64)
    pay_amounts = np.zeros((2, SYMBOL_COUNT), dtype=np.float64)
    combo_counts = np.zeros((2, 6), dtype=np.float64)
    threshold_count = np.zeros((3, len(THRESHOLD_RECORD)), dtype=np.float64)
    threshold_pay = np.zeros((3, len(THRESHOLD_RECORD)), dtype=np.float64)

    coin_in = bet_multi * DEFAULT_COIN_IN * NORMALBET
    if bet_mode == MODE_FEATUREBUY:
        coin_in *= FEATUREBUY

    card_coin_in = bet_multi * DEFAULT_COIN_IN * NORMALBET
    bg_profile = CARD_PROFILE_NEWBIE_BG if CARD_SYSTEM_IS_NEWBIE else CARD_PROFILE_OLDHAND_BG
    fg_profile = CARD_PROFILE_NEWBIE_FG if CARD_SYSTEM_IS_NEWBIE else CARD_PROFILE_OLDHAND_FG
    accepted_rounds = 0
    retry_count = 0
    retry_total = 0
    retry_limit_exceeded = 0
    retry_fail_bg_range = 0
    retry_fail_bg_freegame = 0
    retry_fail_fg = 0
    bg_card_idx = -1
    fg_card_idx = -1
    package_card_idx = -1

    while accepted_rounds < total_rounds:
        if retry_count == 0:
            bg_card_idx = -1
            fg_card_idx = -1
            package_card_idx = -1
            if CARD_SYSTEM_ENABLED:
                if bet_mode == MODE_NORMALBET:
                    bg_card_idx = _pick_card(bg_profile)
                    if bg_card_idx >= 0 and CARD_TYPES[bg_profile, bg_card_idx] == CARD_TYPE_FREE_GAME:
                        fg_card_idx = _pick_card(fg_profile)
                else:
                    package_card_idx = _pick_card(CARD_PROFILE_BUY_FEATURE)

        summary_before = summary.copy()
        hit_counts_before = hit_counts.copy()
        pay_amounts_before = pay_amounts.copy()
        combo_counts_before = combo_counts.copy()
        threshold_count_before = threshold_count.copy()
        threshold_pay_before = threshold_pay.copy()

        summary[I_ROUNDS] += 1
        summary[I_COIN_IN_TOTAL] += coin_in

        pay_bg, scatter_bg, hit_bg, bomb_bg = _run_spin(SCENE_BG, bet_mode, bet_multi, 0, summary, hit_counts, pay_amounts, combo_counts)
        summary[I_PAY_BG_TOTAL] += pay_bg
        if hit_bg:
            summary[I_HIT_BG_SPINS] += 1
        if bomb_bg:
            summary[I_BOMB_USED_BG] += 1

        pay_fg = 0.0
        if scatter_bg >= 3:
            summary_after_bg = summary.copy()
            hit_counts_after_bg = hit_counts.copy()
            pay_amounts_after_bg = pay_amounts.copy()
            combo_counts_after_bg = combo_counts.copy()
            fg_retry_count = 0
            while True:
                if fg_retry_count > 0:
                    summary = summary_after_bg.copy()
                    hit_counts = hit_counts_after_bg.copy()
                    pay_amounts = pay_amounts_after_bg.copy()
                    combo_counts = combo_counts_after_bg.copy()
                pay_fg = _run_free_game_session(scatter_bg, bet_mode, bet_multi, summary, hit_counts, pay_amounts, combo_counts)
                needs_fg_match = CARD_SYSTEM_ENABLED and bet_mode == MODE_NORMALBET and bg_card_idx >= 0 and CARD_TYPES[bg_profile, bg_card_idx] == CARD_TYPE_FREE_GAME
                if not needs_fg_match or _is_card_match(fg_profile, fg_card_idx, pay_fg, card_coin_in, 1):
                    break
                retry_total += 1
                retry_fail_fg += 1
                fg_retry_count += 1
                if fg_retry_count >= CARD_RETRY_LIMIT:
                    retry_limit_exceeded += 1
                    break

        summary[I_PAY_FG_TOTAL] += pay_fg
        _record_threshold(threshold_count, threshold_pay, 0, pay_bg / coin_in, pay_bg)
        if scatter_bg >= 3:
            _record_threshold(threshold_count, threshold_pay, 1, pay_fg / coin_in, pay_fg)
        _record_threshold(threshold_count, threshold_pay, 2, (pay_bg + pay_fg) / coin_in, pay_bg + pay_fg)
        win_mult = (pay_bg + pay_fg) / coin_in if coin_in > 0 else 0.0
        summary[I_WIN_X_SUM] += win_mult
        summary[I_WIN_X_SQUARE] += win_mult * win_mult
        if win_mult > summary[I_MAX_WIN_MULTIPLIER]:
            summary[I_MAX_WIN_MULTIPLIER] = win_mult

        accepted = True
        fail_reason = 0
        triggered_free_game = 1 if scatter_bg >= 3 else 0
        if CARD_SYSTEM_ENABLED:
            if bet_mode == MODE_NORMALBET:
                if bg_card_idx >= 0 and CARD_TYPES[bg_profile, bg_card_idx] == CARD_TYPE_FREE_GAME:
                    if triggered_free_game == 0:
                        accepted = False
                        fail_reason = 2
                elif triggered_free_game == 1 or not _is_card_match(bg_profile, bg_card_idx, pay_bg, card_coin_in, 0):
                    accepted = False
                    fail_reason = 1
            elif not _is_card_match(CARD_PROFILE_BUY_FEATURE, package_card_idx, pay_bg + pay_fg, card_coin_in, triggered_free_game):
                accepted = False
                fail_reason = 3

        if not accepted:
            retry_total += 1
            if fail_reason == 1:
                retry_fail_bg_range += 1
            elif fail_reason == 2:
                retry_fail_bg_freegame += 1
            else:
                retry_fail_fg += 1
            retry_count += 1
            if retry_count < CARD_RETRY_LIMIT:
                summary = summary_before
                hit_counts = hit_counts_before
                pay_amounts = pay_amounts_before
                combo_counts = combo_counts_before
                threshold_count = threshold_count_before
                threshold_pay = threshold_pay_before
                continue
            retry_limit_exceeded += 1

        accepted_rounds += 1
        retry_count = 0

    summary[I_RETRY_TOTAL] += retry_total
    summary[I_RETRY_LIMIT_EXCEEDED] += retry_limit_exceeded
    summary[I_RETRY_FAIL_BG_RANGE] += retry_fail_bg_range
    summary[I_RETRY_FAIL_BG_FREEGAME] += retry_fail_bg_freegame
    summary[I_RETRY_FAIL_FG] += retry_fail_fg

    return summary, hit_counts, pay_amounts, combo_counts, threshold_count, threshold_pay


# ===== Python Wrappers =====


def _merge_arrays(target, source):
    target += source


def build_chunk_rounds(total_rounds, threads):
    threads = max(1, min(int(threads), int(total_rounds) if total_rounds > 0 else 1))
    base = total_rounds // threads
    extra = total_rounds % threads
    return [base + (1 if idx < extra else 0) for idx in range(threads) if base + (1 if idx < extra else 0) > 0]


def run_simulation(total_rounds=TOTAL_ROUNDS, bet_mode=BET_MODE, bet_multi=BET_MULTI, threads=THREADS):
    if bet_mode not in SUPPORTED_BET_MODES:
        supported = ", ".join(str(mode) for mode in SUPPORTED_BET_MODES)
        raise ValueError(f"Unsupported BET_MODE={bet_mode}; H015 supports: {supported}")
    if total_rounds <= 0:
        raise ValueError("TOTAL_ROUNDS must be greater than 0")
    if bet_multi <= 0:
        raise ValueError("BET_MULTI must be greater than 0")
    if threads <= 0:
        raise ValueError("THREADS must be greater than 0")
    print(
        f"Starting H015 simulation | config={CONFIG_FILE} | mode={_mode_name(bet_mode)} | "
        f"rounds={total_rounds:,} | threads={min(threads, total_rounds)} | "
        f"card={'on' if CARD_SYSTEM_ENABLED else 'off'}",
        flush=True,
    )
    print("Compiling Numba core...", flush=True)
    # Compile the active Numba path before timing, matching H026 behavior.
    _simulate_chunk(1, bet_mode, bet_multi, 20260529)
    print("Numba ready. Simulation running...", flush=True)

    chunk_rounds = build_chunk_rounds(total_rounds, threads)
    jobs = [(rounds, 20260529 + idx * 97) for idx, rounds in enumerate(chunk_rounds)]

    results = []
    start = time.perf_counter()
    if len(jobs) == 1:
        results.append(_simulate_chunk(jobs[0][0], bet_mode, bet_multi, jobs[0][1]))
    else:
        with ThreadPoolExecutor(max_workers=len(jobs)) as executor:
            futures = [executor.submit(_simulate_chunk, rounds, bet_mode, bet_multi, seed) for rounds, seed in jobs]
            for future in futures:
                results.append(future.result())
    duration = time.perf_counter() - start

    summary = np.zeros(len(SUMMARY_FIELDS), dtype=np.float64)
    hit_counts = np.zeros((2, SYMBOL_COUNT), dtype=np.float64)
    pay_amounts = np.zeros((2, SYMBOL_COUNT), dtype=np.float64)
    combo_counts = np.zeros((2, 6), dtype=np.float64)
    threshold_count = np.zeros((3, len(THRESHOLD_RECORD)), dtype=np.float64)
    threshold_pay = np.zeros((3, len(THRESHOLD_RECORD)), dtype=np.float64)
    for item in results:
        _merge_arrays(summary, item[0])
        _merge_arrays(hit_counts, item[1])
        _merge_arrays(pay_amounts, item[2])
        _merge_arrays(combo_counts, item[3])
        _merge_arrays(threshold_count, item[4])
        _merge_arrays(threshold_pay, item[5])

    summary[I_MAX_WIN_MULTIPLIER] = max(item[0][I_MAX_WIN_MULTIPLIER] for item in results)
    summary[I_MAX_COMBO_BG] = max(item[0][I_MAX_COMBO_BG] for item in results)
    summary[I_MAX_COMBO_FG] = max(item[0][I_MAX_COMBO_FG] for item in results)

    return {
        "duration": duration,
        "summary": summary,
        "hit_counts": hit_counts,
        "pay_amounts": pay_amounts,
        "combo_counts": combo_counts,
        "threshold_count": threshold_count,
        "threshold_pay": threshold_pay,
    }


def simulate(total_rounds, bet_mode, bet_multi, threads):
    """Backward-compatible alias for callers that used the old H015 API."""
    return run_simulation(total_rounds, bet_mode, bet_multi, threads)


def _mode_name(mode):
    if mode == MODE_NORMALBET:
        return "Normal Bet"
    if mode == MODE_FEATUREBUY:
        return "Buy Feature"
    return f"Mode {mode}"


def format_rounds_tag(total_round):
    total_round = int(total_round)
    if total_round > 0:
        exponent = 0
        value = total_round
        while value % 10 == 0:
            value //= 10
            exponent += 1
        if value == 1 and exponent > 0:
            return f"10{exponent}"
    return str(total_round)


def format_version_tag(version):
    return re.sub(r"[^0-9A-Za-z]+", "", str(version or "").strip())


def format_rtp_tag(rtp_value):
    try:
        return f"{float(rtp_value):.4f}".split(".", 1)[1]
    except (TypeError, ValueError):
        return "0000"


def format_elapsed_time(seconds):
    total_seconds = max(0, int(round(float(seconds))))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}h {minutes}m {secs}s"


def _build_summary_rows(result, bet_mode, bet_multi):
    summary = result["summary"]
    rounds = max(1.0, summary[SUMMARY_IDX["rounds"]])
    coin_in_total = max(1.0, summary[SUMMARY_IDX["coin_in_total"]])
    pay_bg = summary[SUMMARY_IDX["pay_bg_total"]]
    pay_fg = summary[SUMMARY_IDX["pay_fg_total"]]
    pay_total = pay_bg + pay_fg
    fg_triggers = summary[SUMMARY_IDX["fg_trigger_spins"]]
    fg_spins = summary[SUMMARY_IDX["fg_spins"]]
    expected_value = summary[SUMMARY_IDX["win_x_sum"]] / rounds
    variance = max(0.0, summary[SUMMARY_IDX["win_x_square"]] / rounds - expected_value * expected_value)
    standard_deviation = math.sqrt(variance)
    rows = [
        ("parsheet_id", PARSHEET_ID),
        ("game_id", GAME_ID),
        ("game_name", GAME_NAME),
        ("game_version", GAME_VERSION),
        ("config_file", CONFIG_FILE),
        ("card_system", "on" if CARD_SYSTEM_ENABLED else "off"),
        (
            "card_system_profile",
            "off" if not CARD_SYSTEM_ENABLED else ("buy_feature" if bet_mode == MODE_FEATUREBUY else ("newbie" if CARD_SYSTEM_IS_NEWBIE else "oldhand")),
        ),
        ("bet_mode", _mode_name(bet_mode)),
        ("bet_multi", int(bet_multi)),
        ("coin_in", int(bet_multi * DEFAULT_COIN_IN * NORMALBET * (FEATUREBUY if bet_mode == MODE_FEATUREBUY else 1))),
        ("total_rounds", int(rounds)),
        ("duration_sec", round(result["duration"], 3)),
        ("rtp_total", pay_total / coin_in_total),
        ("rtp_bg", pay_bg / coin_in_total),
        ("rtp_fg", pay_fg / coin_in_total),
        ("standard_deviation", standard_deviation),
        ("standard_error", standard_deviation / math.sqrt(rounds)),
        ("hit_rate_bg", summary[SUMMARY_IDX["hit_bg_spins"]] / rounds),
        ("fg_trigger_rate", fg_triggers / rounds),
        ("fg_trigger_cycle", (rounds / fg_triggers) if fg_triggers > 0 else math.inf),
        ("avg_fg_spins", (fg_spins / fg_triggers) if fg_triggers > 0 else 0.0),
        ("hit_rate_fg", (summary[SUMMARY_IDX["hit_fg_spins"]] / fg_spins) if fg_spins > 0 else 0.0),
        ("retrigger_rate", (summary[SUMMARY_IDX["retrigger_count"]] / fg_triggers) if fg_triggers > 0 else 0.0),
        ("bomb_used_rate_bg", summary[SUMMARY_IDX["bomb_used_bg"]] / rounds),
        ("bomb_used_rate_fg", (summary[SUMMARY_IDX["bomb_used_fg"]] / fg_spins) if fg_spins > 0 else 0.0),
        ("max_win_multiplier", summary[SUMMARY_IDX["max_win_multiplier"]]),
        ("max_combo_bg", int(summary[SUMMARY_IDX["max_combo_bg"]])),
        ("max_combo_fg", int(summary[SUMMARY_IDX["max_combo_fg"]])),
        ("retry_total", int(summary[SUMMARY_IDX["retry_total"]])),
        ("retry_limit_exceeded", int(summary[SUMMARY_IDX["retry_limit_exceeded"]])),
        ("retry_fail_bg_range", int(summary[SUMMARY_IDX["retry_fail_bg_range"]])),
        ("retry_fail_bg_freegame", int(summary[SUMMARY_IDX["retry_fail_bg_freegame"]])),
        ("retry_fail_fg", int(summary[SUMMARY_IDX["retry_fail_fg"]])),
    ]
    return rows


def _build_detail_frames(result):
    rounds = max(1.0, result["summary"][SUMMARY_IDX["rounds"]])
    fg_spins = max(1.0, result["summary"][SUMMARY_IDX["fg_spins"]])
    coin_in_total = max(1.0, result["summary"][SUMMARY_IDX["coin_in_total"]])

    symbol_names = [SYMBOL_STR[idx] for idx in range(SYMBOL_COUNT) if SCORE_SYMBOL_MASK[idx] == 1]
    symbol_ids = [idx for idx in range(SYMBOL_COUNT) if SCORE_SYMBOL_MASK[idx] == 1]

    hits_data = np.vstack(
        [
            result["hit_counts"][0, symbol_ids] / rounds,
            result["hit_counts"][1, symbol_ids] / fg_spins,
        ]
    )
    pay_data = np.vstack(
        [
            result["pay_amounts"][0, symbol_ids] / coin_in_total,
            result["pay_amounts"][1, symbol_ids] / coin_in_total,
        ]
    )

    combo_index = ["0", "1", "2", "3", "4", "5+"]
    combo_df = pd.DataFrame(result["combo_counts"].T, index=combo_index, columns=["BG", "FG"])
    combo_df["BG"] = combo_df["BG"] / rounds
    combo_df["FG"] = combo_df["FG"] / fg_spins

    threshold_labels = []
    for idx, upper in enumerate(THRESHOLD_RECORD):
        if idx == 0:
            threshold_labels.append("0")
        else:
            lower = int(THRESHOLD_RECORD[idx - 1])
            upper_label = "+∞" if upper == 9999999 else str(int(upper))
            threshold_labels.append(f"({lower}, {upper_label}]")
    multiplier_df = pd.DataFrame(
        {
            "bucket": threshold_labels,
            "bg_cnt": result["threshold_count"][0],
            "bg_pay": result["threshold_pay"][0],
            "fg_cnt": result["threshold_count"][1],
            "fg_pay": result["threshold_pay"][1],
            "oa_cnt": result["threshold_count"][2],
            "oa_pay": result["threshold_pay"][2],
        }
    )

    hits_df = pd.DataFrame(hits_data, columns=symbol_names, index=["BG hit", "FG hit"])
    pay_df = pd.DataFrame(pay_data, columns=symbol_names, index=["BG rtp", "FG rtp"])
    record_df = pd.DataFrame({"field": SUMMARY_FIELDS, "value": result["summary"]})
    return hits_df, pay_df, combo_df, multiplier_df, record_df


def print_console(result, bet_mode, bet_multi):
    if SHOW_CONSOLE_SUMMARY:
        print("=== Fixed Summary ===")
        for key, value in _build_summary_rows(result, bet_mode, bet_multi):
            print(f"{key:20s}: {value}")

    if SHOW_CONSOLE_DETAIL:
        print("\n=== By Game Detail ===")
        hits_df, pay_df, combo_df, multiplier_df, _ = _build_detail_frames(result)
        print("\n[Hits]")
        print(hits_df.to_string())
        print("\n[Pay / RTP]")
        print(pay_df.to_string())
        print("\n[Combo / Cascade]")
        print(combo_df.to_string())
        print("\n[Multiplier Line]")
        print(multiplier_df.to_string(index=False))


def print_batch_summary(result, bet_mode, bet_multi):
    summary = dict(_build_summary_rows(result, bet_mode, bet_multi))
    fg_triggers = int(round(float(result["summary"][SUMMARY_IDX["fg_trigger_spins"]])))
    print(f"* game_id: {GAME_ID}", flush=True)
    print(f"* parsheet_id: {PARSHEET_ID}", flush=True)
    print(f"* version: {GAME_VERSION}", flush=True)
    print(f"* bet_mode: {_mode_name(bet_mode)}", flush=True)
    print(f"* duration: {format_elapsed_time(result['duration'])}", flush=True)
    print(f"* rtp_total: {float(summary.get('rtp_total', 0.0)) * 100:.2f}%", flush=True)
    print(f"* rtp_bg: {float(summary.get('rtp_bg', 0.0)) * 100:.2f}%", flush=True)
    print(f"* rtp_fg: {float(summary.get('rtp_fg', 0.0)) * 100:.2f}%", flush=True)
    print(f"* hit_rate_bg: {float(summary.get('hit_rate_bg', 0.0)):.4f}", flush=True)
    print(f"* hit_rate_fg: {float(summary.get('hit_rate_fg', 0.0)):.4f}", flush=True)
    print(f"* fg_trigger_rate: {float(summary.get('fg_trigger_rate', 0.0)):.4f} ({fg_triggers} spins)", flush=True)
    print(f"* retrigger_rate: {float(summary.get('retrigger_rate', 0.0)):.4f}", flush=True)
    print(f"* avg_fg_spins: {float(summary.get('avg_fg_spins', 0.0)):.2f} spins", flush=True)
    print(f"* max_win_multiplier: {float(summary.get('max_win_multiplier', 0.0)):.2f} x", flush=True)
    print(f"* card_system: {'on' if CARD_SYSTEM_ENABLED else 'off'}", flush=True)


def output_report(result, bet_mode, bet_multi):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    version_tag = format_version_tag(GAME_VERSION)
    rounds = int(result["summary"][SUMMARY_IDX["rounds"]])
    rounds_tag = format_rounds_tag(rounds)
    summary_rows = _build_summary_rows(result, bet_mode, bet_multi)
    summary_map = dict(summary_rows)
    rtp_tag = format_rtp_tag(summary_map.get("rtp_total"))
    filename_parts = [PARSHEET_ID]
    if version_tag:
        filename_parts.append(version_tag)
    filename_parts.extend([timestamp, f"betmode{bet_mode}", rounds_tag])
    if CARD_SYSTEM_ENABLED:
        filename_parts.append(rtp_tag)
        if bet_mode == MODE_NORMALBET:
            filename_parts.append("newbie" if CARD_SYSTEM_IS_NEWBIE else "oldhand")
        filename_parts.append("card")
    path = os.path.join(OUTPUT_DIR, f"{'_'.join(filename_parts)}.xlsx")
    hits_df, pay_df, combo_df, multiplier_df, record_df = _build_detail_frames(result)
    base_info_df = pd.DataFrame(summary_rows, columns=["field", "value"])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        base_info_df.to_excel(writer, sheet_name="Base Info", index=False)
        hits_df.to_excel(writer, sheet_name="Hits")
        pay_df.to_excel(writer, sheet_name="Pay")
        combo_df.to_excel(writer, sheet_name="Eliminate")
        multiplier_df.to_excel(writer, sheet_name="Multiplier Line", index=False)
        record_df.to_excel(writer, sheet_name="Record Data", index=False)
    return path


def run_single_spin_debug():
    result = run_simulation(DEBUG_ROUNDS, BET_MODE, BET_MULTI, 1)
    print_console(result, BET_MODE, BET_MULTI)
    print_batch_summary(result, BET_MODE, BET_MULTI)


def run_all_combinations():
    if not BATCH_COMBINATIONS:
        raise ValueError("RUN_ALL_COMBINATIONS is enabled, but BATCH_RUNS is empty")
    total_jobs = len(BATCH_COMBINATIONS)
    for index, combo in enumerate(BATCH_COMBINATIONS, start=1):
        combo_env = os.environ.copy()
        combo_env["PYTHONUNBUFFERED"] = "1"
        combo_env["H015_CONFIG_FILE"] = str(combo.get("config_file", CONFIG_FILE))
        combo_env["H015_BET_MODE"] = str(combo["bet_mode"])
        combo_env["H015_TOTAL_ROUNDS"] = str(combo["total_rounds"])
        combo_env["H015_CARD_SYSTEM_IS_NEWBIE"] = "true" if combo.get("card_system_is_newbie", False) else "false"
        combo_env["H015_CARD_SYSTEM_ENABLED"] = "true" if combo.get("card_system_enabled", True) else "false"
        combo_env["H015_RUN_ALL_COMBINATIONS"] = "false"
        combo_env["H015_BATCH_CHILD"] = "1"
        print(
            f"\n=== Batch {index}/{total_jobs}: " f"config={combo_env['H015_CONFIG_FILE']}, " f"bet_mode={combo_env['H015_BET_MODE']}, " f"total_rounds={combo_env['H015_TOTAL_ROUNDS']}, " f"card_system_is_newbie={combo_env['H015_CARD_SYSTEM_IS_NEWBIE']} ===",
            flush=True,
        )
        subprocess.run(
            [sys.executable, os.path.abspath(__file__)],
            check=True,
            env=combo_env,
        )


def main():
    if RUN_ALL_COMBINATIONS and os.environ.get("H015_BATCH_CHILD") != "1":
        run_all_combinations()
        return

    if RUN_SINGLE_SPIN_DEBUG:
        run_single_spin_debug()
        return

    result = run_simulation()
    print_console(result, BET_MODE, BET_MULTI)
    print_batch_summary(result, BET_MODE, BET_MULTI)
    if OUTPUT_REPORT:
        report_path = output_report(result, BET_MODE, BET_MULTI)
        print(f"\nReport: {report_path}")


if __name__ == "__main__":
    main()
