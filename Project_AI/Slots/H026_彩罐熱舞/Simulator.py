import json
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import numpy as np
import pandas as pd
from numba import njit

# ===== User Settings =====

BASE_DIR = r"C:\Users\rhinshen\Mine\個人工作區\2_Program\Project_AI\Slots\H026_彩罐熱舞"
CONFIG_PATH = os.path.join(BASE_DIR, "config.js")
OUTPUT_DIR = os.path.join(BASE_DIR, "Record")

TOTAL_ROUNDS = 10**8
BET_MULTI = 1
BET_MODE = 0
THREADS = max(1, max(8, os.cpu_count() or 1))
FG_SPIN_CAP = 50
ALLOW_C1_DROP_WHEN_BOARD_HAS_C1 = False

OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = True
SHOW_CONSOLE_DETAIL = False
RUN_SINGLE_SPIN_DEBUG = False
TRACE_RETRY_FAILURE = False

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
    if start < 0 or end < 0 or end <= start:
        raise ValueError(f"Invalid config.js format: {path}")
    return json.loads(raw[start : end + 1])


def _pad_nested_tables(raw_tables, fill_value):
    table_count = len(raw_tables)
    max_len = max(len(table) for table in raw_tables)
    reel_count = len(raw_tables[0][0])
    arr = np.full((table_count, max_len, reel_count), fill_value, dtype=np.int64)
    for table_idx, table in enumerate(raw_tables):
        for row_idx, row in enumerate(table):
            arr[table_idx, row_idx, :] = np.asarray(row, dtype=np.int64)
    return arr


def _build_card_profile_tables(card_system_raw):
    profile_names = ("normal_bet", "free_game", "buy_feature")
    card_type_map = {"range": 0, "free_game": 1}
    profile_cards = []
    for profile_name in profile_names:
        cards = list(card_system_raw.get("profiles", {}).get(profile_name, []))
        profile_cards.append(cards)

    max_cards = max((len(cards) for cards in profile_cards), default=0)
    if max_cards <= 0:
        max_cards = 1

    card_types = np.full((len(profile_names), max_cards), -1, dtype=np.int64)
    card_min = np.zeros((len(profile_names), max_cards), dtype=np.float64)
    card_max = np.zeros((len(profile_names), max_cards), dtype=np.float64)
    card_weight_cum = np.zeros((len(profile_names), max_cards), dtype=np.int64)
    card_counts = np.zeros(len(profile_names), dtype=np.int64)

    for profile_idx, cards in enumerate(profile_cards):
        running = 0
        for card_idx, card in enumerate(cards):
            weight = int(card.get("weight", 0))
            running += weight
            card_types[profile_idx, card_idx] = card_type_map.get(str(card.get("type", "range")), 0)
            card_min[profile_idx, card_idx] = float(card.get("min", 0.0))
            card_max[profile_idx, card_idx] = float(card.get("max", 0.0))
            card_weight_cum[profile_idx, card_idx] = running
        card_counts[profile_idx] = len(cards)

    return card_types, card_min, card_max, card_weight_cum, card_counts


CFG_RAW = _load_config(CONFIG_PATH)

GAME_ID = CFG_RAW["game_id"]
GAME_NAME = CFG_RAW.get("display_name") or CFG_RAW.get("game_name") or GAME_ID
CONFIG_VERSION = CFG_RAW.get("excel_version") or CFG_RAW.get("game_version") or CFG_RAW.get("version") or ""
MODE_NORMALBET = int(CFG_RAW["mode_normalbet"])
MODE_FEATUREBUY = int(CFG_RAW["mode_featurebuy"])
SCENE_BG = int(CFG_RAW["scene_bg"])
SCENE_FG = int(CFG_RAW["scene_fg"])
SCENE_BF = int(CFG_RAW["scene_bf"])
OUTPUT_BG = 0
OUTPUT_FG = 1
OUTPUT_OA = 2

WINDOW_SIZE = int(CFG_RAW["window_size"])
DISPLAY_WINDOW_SIZE = WINDOW_SIZE + 1
SCORE_ROW_OFFSET = DISPLAY_WINDOW_SIZE - WINDOW_SIZE
REEL_NUM = int(CFG_RAW["reel_num"])
LAYOUT_SHAPE = (DISPLAY_WINDOW_SIZE, REEL_NUM)
REEL3_SPECIAL_TABLE_IDS = np.asarray([1, 3, 4, 5], dtype=np.int64)
DEFAULT_COIN_IN = int(CFG_RAW["default_coin_in"])
NORMALBET = int(CFG_RAW["normalbet"])
FEATUREBUY = int(CFG_RAW["featurebuy"])
SPECIAL_POOL_WEIGHT_BASE = int(CFG_RAW["special_pool_weight_base"])
MAX_WIN_MULTIPLIER = 5000

PAYLINES = np.asarray(CFG_RAW["paylines"], dtype=np.int64)
PAY_TABLE = np.asarray(CFG_RAW["pay_table"], dtype=np.int64)
SYMBOL_ID = np.asarray(CFG_RAW["symbol_id"], dtype=np.int64)
SYMBOL_STR = {int(k): v for k, v in CFG_RAW["symbol_str"].items()}
BASE_SYMBOL_OF = np.asarray(CFG_RAW["base_symbol_of"], dtype=np.int64)
IS_GOLD_SYMBOL = np.asarray(CFG_RAW["is_gold_symbol"], dtype=np.int64)
IS_SCORE_SYMBOL = np.asarray(CFG_RAW["is_score_symbol"], dtype=np.int64)
SYMBOLS_SCORE = np.asarray(CFG_RAW["symbols_score"], dtype=np.int64)
VALUE_MULTIPLIER_RANGE = np.asarray(CFG_RAW["value_multiplier_range"], dtype=np.int64)

WEIGHT_CUM_TABLE_BG = np.asarray(CFG_RAW["weight_cum_table_bg"], dtype=np.int64)

WEIGHT_SPECIAL_POOL = np.asarray(CFG_RAW["weight_special_pool"], dtype=np.int64)
WEIGHT_CUM_MULTIPLE_SPECIAL = np.asarray(CFG_RAW["weight_cum_multiple_special"], dtype=np.int64)
WEIGHT_CUM_MULTIPLE_R3_BEFORE = np.asarray(CFG_RAW["weight_cum_multiple_r3_before"], dtype=np.int64)
WEIGHT_CUM_MULTIPLE_R3_AFTER = np.asarray(CFG_RAW["weight_cum_multiple_r3_after"], dtype=np.int64)
WEIGHT_CUM_MULTIPLE_BEFORE = np.asarray(CFG_RAW["weight_cum_multiple_before"], dtype=np.int64)
WEIGHT_CUM_MULTIPLE_AFTER = np.asarray(CFG_RAW["weight_cum_multiple_after"], dtype=np.int64)

ARR_REELS = _pad_nested_tables(CFG_RAW["arr_reels"], -1)
ARR_REELS_WEIGHT_CUM = _pad_nested_tables(CFG_RAW["arr_reels_weight_cum"], 0)
DROP_WEIGHT_A_CUM = np.asarray(CFG_RAW["drop_weight_a_cum"], dtype=np.int64)
DROP_WEIGHT_B_CUM = np.asarray(CFG_RAW["drop_weight_b_cum"], dtype=np.int64)
REELS_LEN = np.asarray(CFG_RAW["reels_len"], dtype=np.int64)
STRIP_NAME_MAP = list(CFG_RAW["strip_name_map"])

ELIMINATE_TABLE_WEIGHT_CUM_BG = np.asarray(CFG_RAW["eliminate_table_weight_cum_bg"], dtype=np.int64)
ELIMINATE_TABLE_WEIGHT_CUM_FG = np.asarray(CFG_RAW["eliminate_table_weight_cum_fg"], dtype=np.int64)
ELIMINATE_TABLE_WEIGHT_CUM_BF = np.asarray(CFG_RAW["eliminate_table_weight_cum_bf"], dtype=np.int64)

CARD_SYSTEM_RAW = CFG_RAW.get("card_system", {})
CARD_SYSTEM_ENABLED = bool(CARD_SYSTEM_RAW.get("enabled"))
CARD_RETRY_LIMIT = int(CARD_SYSTEM_RAW.get("retry_limit", 0))
CARD_TYPES, CARD_MIN, CARD_MAX, CARD_WEIGHT_CUM, CARD_COUNTS = _build_card_profile_tables(CARD_SYSTEM_RAW)
CASCADE_BLOCK_C1_WHEN_BOARD_HAS_C1 = 0 if ALLOW_C1_DROP_WHEN_BOARD_HAS_C1 else 1

SYMBOLS_COUNT = int(len(SYMBOL_ID))
LINE_NUM = int(PAYLINES.shape[0])
RECORD_COLS = max(len(THRESHOLD_RECORD), SYMBOLS_COUNT * 2, 100)
RECORD_SIZE = (20, RECORD_COLS)

WW = int(next(key for key, value in SYMBOL_STR.items() if value == "WW"))
C1 = int(next(key for key, value in SYMBOL_STR.items() if value == "C1"))

R_ALL = 0
R_MULTIPLIER_RANGE_CNT_BG = 1
R_MULTIPLIER_RANGE_CNT_FG = 2
R_MULTIPLIER_RANGE_CNT_OA = 3
R_MULTIPLIER_RANGE_PAY_BG = 4
R_MULTIPLIER_RANGE_PAY_FG = 5
R_MULTIPLIER_RANGE_PAY_OA = 6
R_HITS = (10, 13)
R_PAY = (13, 16)
R_ELIMINATE = (16, 19)

RA_HITS_BG = 0
RA_HITS_FG = 1
RA_TRIGGER_FREEGAME = 2
RA_RE_TRIGGER = 3
RA_FREE_SPINS = 4
RA_X_SUM = 5
RA_X_SQUARE = 6
RA_TRIGGER_FG_PAY_BG = 7
RA_MAX_WIN_HITS = 8
RA_MAX_SINGLE_WIN = 9
RA_MAX_MULTIPLIER = 10
RA_ELIMINATE_0 = 11
RA_ELIMINATE_1 = 12
RA_ELIMINATE_2 = 13
RA_ELIMINATE_3 = 14
RA_ELIMINATE_4 = 15
RA_ELIMINATE_5 = 16
RA_RETRY_TOTAL = 17
RA_RETRY_LIMIT_EXCEEDED = 18
RA_RETRY_LIMIT_BG_RANGE = 19
RA_RETRY_LIMIT_BG_FREEGAME = 20
RA_GOLD_APPEAR_SPINS = 21
RA_GOLD_USED_SPINS = 22
RA_MULTI_APPEAR_SPINS = 23
RA_MULTI_USED_SPINS = 24
RA_RETRY_LIMIT_FG = 25
RA_RETRY_LIMIT_BG_FREEGAME_NEVER_TRIGGER = 26
RA_GOLD_APPEAR_SPINS_BG = 27
RA_GOLD_USED_SPINS_BG = 28
RA_GOLD_APPEAR_SPINS_FG = 29
RA_GOLD_USED_SPINS_FG = 30
RA_ELIMINATE_0_FG = 31
RA_ELIMINATE_1_FG = 32
RA_ELIMINATE_2_FG = 33
RA_ELIMINATE_3_FG = 34
RA_ELIMINATE_4_FG = 35
RA_ELIMINATE_5_FG = 36
RA_MULTI_APPEAR_SPINS_BG = 37
RA_MULTI_USED_SPINS_BG = 38
RA_MULTI_APPEAR_SPINS_FG = 39
RA_FINAL_GOLD_COUNT_BG_0 = 40
RA_FINAL_GOLD_COUNT_FG_0 = 50
RA_MULTI_USED_SPINS_FG = 60
RA_MAX_MULTIPLIER_BG = 61
RA_MAX_MULTIPLIER_FG = 62
RA_FINAL_C1_PRESENT_BG = 63
RA_FINAL_C1_PRESENT_FG = 64
PROFILE_NORMAL_BET = 0
PROFILE_FREE_GAME = 1
PROFILE_BUY_FEATURE = 2
CARD_TYPE_RANGE = 0
CARD_TYPE_FREE_GAME = 1
RETRY_FAIL_NONE = 0
RETRY_FAIL_BG_RANGE = 1
RETRY_FAIL_BG_FREEGAME = 2
RETRY_FAIL_FG = 3


# ===== Numba Core =====


@njit(nogil=True)
def pick_by_cum(cum_weight):
    total = int(cum_weight[cum_weight.shape[0] - 1])
    if total <= 0:
        return 0
    rd = np.random.randint(0, total)
    for idx in range(cum_weight.shape[0]):
        if rd < cum_weight[idx]:
            return idx
    return cum_weight.shape[0] - 1


@njit(nogil=True)
def pick_card(profile_idx):
    card_count = CARD_COUNTS[profile_idx]
    if card_count <= 0:
        return -1

    total = CARD_WEIGHT_CUM[profile_idx, card_count - 1]
    if total <= 0:
        return -1

    rd = np.random.randint(0, total)
    for idx in range(card_count):
        if rd < CARD_WEIGHT_CUM[profile_idx, idx]:
            return idx
    return card_count - 1


@njit(nogil=True)
def is_range_match(min_value, max_value, score, coin_in):
    if coin_in <= 0:
        return False
    multiplier = score / coin_in
    return multiplier > min_value and multiplier <= max_value


@njit(nogil=True)
def is_card_match(profile_idx, card_idx, score, coin_in, triggered_free_game):
    if card_idx < 0:
        return True
    card_type = CARD_TYPES[profile_idx, card_idx]
    if card_type == CARD_TYPE_FREE_GAME:
        return triggered_free_game == 1
    return is_range_match(CARD_MIN[profile_idx, card_idx], CARD_MAX[profile_idx, card_idx], score, coin_in)


@njit(nogil=True)
def calc_free_spins(scatter_count, force_trigger):
    if scatter_count >= 3:
        return 15 + (scatter_count - 3) * 2
    if force_trigger == 1:
        return 15
    return 0


@njit(nogil=True)
def merge_round_record(record_data, round_record):
    current_max_single = record_data[R_ALL, RA_MAX_SINGLE_WIN]
    current_max_multi = record_data[R_ALL, RA_MAX_MULTIPLIER]
    current_max_multi_bg = record_data[R_ALL, RA_MAX_MULTIPLIER_BG]
    current_max_multi_fg = record_data[R_ALL, RA_MAX_MULTIPLIER_FG]
    round_max_single = round_record[R_ALL, RA_MAX_SINGLE_WIN]
    round_max_multi = round_record[R_ALL, RA_MAX_MULTIPLIER]
    round_max_multi_bg = round_record[R_ALL, RA_MAX_MULTIPLIER_BG]
    round_max_multi_fg = round_record[R_ALL, RA_MAX_MULTIPLIER_FG]

    for i in range(record_data.shape[0]):
        for j in range(record_data.shape[1]):
            record_data[i, j] += round_record[i, j]

    record_data[R_ALL, RA_MAX_SINGLE_WIN] = current_max_single if current_max_single > round_max_single else round_max_single
    record_data[R_ALL, RA_MAX_MULTIPLIER] = current_max_multi if current_max_multi > round_max_multi else round_max_multi
    record_data[R_ALL, RA_MAX_MULTIPLIER_BG] = current_max_multi_bg if current_max_multi_bg > round_max_multi_bg else round_max_multi_bg
    record_data[R_ALL, RA_MAX_MULTIPLIER_FG] = current_max_multi_fg if current_max_multi_fg > round_max_multi_fg else round_max_multi_fg


@njit(nogil=True)
def clear_2d(arr):
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            arr[i, j] = 0


@njit(nogil=True)
def choose_table(scene_mode, fg_multiplier_sum):
    if scene_mode == SCENE_BG:
        return pick_by_cum(WEIGHT_CUM_TABLE_BG)
    if scene_mode == SCENE_FG:
        if fg_multiplier_sum < 10:
            return 3
        if fg_multiplier_sum < 20:
            return 4
        return 5
    return 6


@njit(nogil=True)
def pick_multiplier(cum_matrix, strip_idx):
    return VALUE_MULTIPLIER_RANGE[pick_by_cum(cum_matrix[:, strip_idx])]


@njit(nogil=True)
def is_scoring_row(row):
    return 1 if row >= SCORE_ROW_OFFSET else 0


@njit(nogil=True)
def uses_reel3_multiplier_table(table_id, col):
    if col != 2:
        return 0
    for idx in range(REEL3_SPECIAL_TABLE_IDS.shape[0]):
        if table_id == REEL3_SPECIAL_TABLE_IDS[idx]:
            return 1
    return 0


@njit(nogil=True)
def pick_initial_multiplier_by_pos(table_id, row, col):
    if uses_reel3_multiplier_table(table_id, col) == 1:
        if is_scoring_row(row) == 1:
            return pick_multiplier(WEIGHT_CUM_MULTIPLE_R3_BEFORE, table_id)
        return pick_multiplier(WEIGHT_CUM_MULTIPLE_R3_AFTER, table_id)
    if is_scoring_row(row) == 1:
        return pick_multiplier(WEIGHT_CUM_MULTIPLE_BEFORE, table_id)
    return pick_multiplier(WEIGHT_CUM_MULTIPLE_AFTER, table_id)


@njit(nogil=True)
def pick_drop_multiplier_by_col(table_id, col):
    if uses_reel3_multiplier_table(table_id, col) == 1:
        return pick_multiplier(WEIGHT_CUM_MULTIPLE_R3_AFTER, table_id)
    return pick_multiplier(WEIGHT_CUM_MULTIPLE_AFTER, table_id)


@njit(nogil=True)
def choose_eliminate_table(scene_mode):
    if scene_mode == SCENE_BG:
        choice = pick_by_cum(ELIMINATE_TABLE_WEIGHT_CUM_BG)
        return 1 if choice == 0 else 0
    if scene_mode == SCENE_FG:
        choice = pick_by_cum(ELIMINATE_TABLE_WEIGHT_CUM_FG)
        return 1 if choice == 0 else 0
    choice = pick_by_cum(ELIMINATE_TABLE_WEIGHT_CUM_BF)
    return 1 if choice == 0 else 0


@njit(nogil=True)
def generate_board(table_id, board, gold_mask, multi_mask, next_above_idx):
    for col in range(REEL_NUM):
        reel_length = REELS_LEN[table_id, col]
        stop_idx = pick_by_cum(ARR_REELS_WEIGHT_CUM[table_id, :reel_length, col])
        next_above_idx[col] = (stop_idx - 1 + reel_length) % reel_length
        for row in range(DISPLAY_WINDOW_SIZE):
            symbol = ARR_REELS[table_id, (stop_idx + row) % reel_length, col]
            board[row, col] = BASE_SYMBOL_OF[symbol]
            gold_mask[row, col] = IS_GOLD_SYMBOL[symbol]
            multi_mask[row, col] = 0


@njit(nogil=True)
def count_scatter(board):
    total = 0
    for row in range(SCORE_ROW_OFFSET, DISPLAY_WINDOW_SIZE):
        for col in range(REEL_NUM):
            if board[row, col] == C1:
                total += 1
    return total


@njit(nogil=True)
def column_has_scatter(board, col):
    for row in range(DISPLAY_WINDOW_SIZE):
        if board[row, col] == C1:
            return 1
    return 0


@njit(nogil=True)
def pick_drop_symbol(table_id, use_drop_a, col, column_has_c1):
    while True:
        if use_drop_a == 1:
            drop_idx = pick_by_cum(DROP_WEIGHT_A_CUM[table_id, :, col])
        else:
            drop_idx = pick_by_cum(DROP_WEIGHT_B_CUM[table_id, :, col])
        drop_symbol = SYMBOL_ID[drop_idx]
        base_symbol = BASE_SYMBOL_OF[drop_symbol]
        if CASCADE_BLOCK_C1_WHEN_BOARD_HAS_C1 == 1 and column_has_c1 == 1 and base_symbol == C1:
            continue
        return drop_symbol, base_symbol


@njit(nogil=True)
def take_reel_above_symbol(table_id, col, next_above_idx, column_has_c1):
    reel_length = REELS_LEN[table_id, col]
    while True:
        strip_idx = next_above_idx[col]
        symbol = ARR_REELS[table_id, strip_idx, col]
        next_above_idx[col] = (strip_idx - 1 + reel_length) % reel_length
        base_symbol = BASE_SYMBOL_OF[symbol]
        if CASCADE_BLOCK_C1_WHEN_BOARD_HAS_C1 == 1 and column_has_c1 == 1 and base_symbol == C1:
            continue
        return symbol, base_symbol


@njit(nogil=True)
def collect_gold_positions(gold_mask, gold_pos):
    gold_count = 0
    for row in range(DISPLAY_WINDOW_SIZE):
        for col in range(REEL_NUM):
            if gold_mask[row, col] == 1:
                gold_pos[gold_count, 0] = row
                gold_pos[gold_count, 1] = col
                gold_count += 1
    return gold_count


@njit(nogil=True)
def collect_scoring_gold_positions(gold_mask, gold_pos):
    gold_count = 0
    for row in range(SCORE_ROW_OFFSET, DISPLAY_WINDOW_SIZE):
        for col in range(REEL_NUM):
            if gold_mask[row, col] == 1:
                gold_pos[gold_count, 0] = row
                gold_pos[gold_count, 1] = col
                gold_count += 1
    return gold_count


@njit(nogil=True)
def count_gold_mask(gold_mask):
    gold_count = 0
    for row in range(DISPLAY_WINDOW_SIZE):
        for col in range(REEL_NUM):
            gold_count += gold_mask[row, col]
    return gold_count


@njit(nogil=True)
def assign_initial_multiplier(table_id, gold_mask, multi_mask, gold_pos):
    gold_count = collect_gold_positions(gold_mask, gold_pos)
    if gold_count == 0:
        return

    scoring_gold_pos = np.zeros((DISPLAY_WINDOW_SIZE * REEL_NUM, 2), np.int64)
    scoring_gold_count = collect_scoring_gold_positions(gold_mask, scoring_gold_pos)
    special_idx = -1
    if scoring_gold_count > 0:
        pool_row = scoring_gold_count - 1
        if scoring_gold_count == 0:
            pool_row = 0
        if pool_row >= WEIGHT_SPECIAL_POOL.shape[0]:
            pool_row = WEIGHT_SPECIAL_POOL.shape[0] - 1
        special_weight = WEIGHT_SPECIAL_POOL[pool_row, table_id]
        if special_weight > 0 and np.random.randint(0, SPECIAL_POOL_WEIGHT_BASE) < special_weight:
            special_idx = np.random.randint(0, scoring_gold_count)

    for idx in range(gold_count):
        row = gold_pos[idx, 0]
        col = gold_pos[idx, 1]
        scoring_match_idx = -1
        for scoring_idx in range(scoring_gold_count):
            if scoring_gold_pos[scoring_idx, 0] == row and scoring_gold_pos[scoring_idx, 1] == col:
                scoring_match_idx = scoring_idx
                break
        if scoring_match_idx >= 0 and scoring_match_idx == special_idx:
            multi_mask[row, col] = pick_multiplier(WEIGHT_CUM_MULTIPLE_SPECIAL, table_id)
        else:
            multi_mask[row, col] = pick_initial_multiplier_by_pos(table_id, row, col)


@njit(nogil=True)
def get_pay(symbol, line_len, bet_multi):
    if symbol < 0 or IS_SCORE_SYMBOL[symbol] == 0 or line_len < 3:
        return 0
    return PAY_TABLE[symbol, line_len - 3] * bet_multi


@njit(nogil=True)
def evaluate_board(board, hit_mask, spin_hits, spin_pay, bet_multi):
    clear_2d(hit_mask)

    total_pay = 0
    total_hits = 0

    for line_idx in range(PAYLINES.shape[0]):
        best_symbol = -1
        best_len = 0
        best_pay = 0

        # Line wins must start from the leftmost reel on the payline.
        first_row = PAYLINES[line_idx, 0] + SCORE_ROW_OFFSET
        first_symbol_raw = board[first_row, 0]
        if first_symbol_raw == C1:
            continue
        first_symbol = BASE_SYMBOL_OF[first_symbol_raw]

        if first_symbol_raw == WW:
            for sym_idx in range(SYMBOLS_SCORE.shape[0]):
                symbol = SYMBOLS_SCORE[sym_idx]
                line_len = 0
                for reel in range(REEL_NUM):
                    row = PAYLINES[line_idx, reel] + SCORE_ROW_OFFSET
                    symbol_on_line = board[row, reel]
                    if symbol_on_line == C1:
                        break
                    if BASE_SYMBOL_OF[symbol_on_line] == symbol or symbol_on_line == WW:
                        line_len += 1
                    else:
                        break
                pay = get_pay(symbol, line_len, bet_multi)
                if pay > best_pay:
                    best_symbol = symbol
                    best_len = line_len
                    best_pay = pay
        else:
            line_len = 0
            for reel in range(REEL_NUM):
                row = PAYLINES[line_idx, reel] + SCORE_ROW_OFFSET
                symbol_on_line = board[row, reel]
                if symbol_on_line == C1:
                    break
                if BASE_SYMBOL_OF[symbol_on_line] == first_symbol or symbol_on_line == WW:
                    line_len += 1
                else:
                    break
            best_symbol = first_symbol
            best_len = line_len
            best_pay = get_pay(best_symbol, best_len, bet_multi)

        if best_pay <= 0:
            continue

        total_pay += best_pay
        total_hits += 1
        spin_hits[best_len - 3, best_symbol] += 1
        spin_pay[best_len - 3, best_symbol] += best_pay

        for reel in range(best_len):
            row = PAYLINES[line_idx, reel] + SCORE_ROW_OFFSET
            hit_mask[row, reel] = 1

    return total_pay, total_hits


@njit(nogil=True)
def cascade_drop(table_id, use_drop_a, board, gold_mask, multi_mask, hit_mask, keep_symbol, keep_gold, keep_multi, next_above_idx):
    for col in range(REEL_NUM):
        keep_count = 0
        for row in range(DISPLAY_WINDOW_SIZE - 1, -1, -1):
            if hit_mask[row, col] == 0:
                keep_symbol[keep_count] = board[row, col]
                keep_gold[keep_count] = gold_mask[row, col]
                keep_multi[keep_count] = multi_mask[row, col]
                keep_count += 1
            elif hit_mask[row, col] == 2:
                keep_symbol[keep_count] = WW
                keep_gold[keep_count] = 0
                keep_multi[keep_count] = 0
                keep_count += 1

        keep_idx = 0
        for row in range(DISPLAY_WINDOW_SIZE - 1, -1, -1):
            if keep_idx < keep_count:
                board[row, col] = keep_symbol[keep_idx]
                gold_mask[row, col] = keep_gold[keep_idx]
                multi_mask[row, col] = keep_multi[keep_idx]
                keep_idx += 1
            else:
                board[row, col] = -1
                gold_mask[row, col] = 0
                multi_mask[row, col] = 0

        has_c1_in_col = column_has_scatter(board, col)
        for row in range(DISPLAY_WINDOW_SIZE - 1, -1, -1):
            if board[row, col] >= 0:
                continue
            drop_symbol, base_symbol = pick_drop_symbol(table_id, use_drop_a, col, has_c1_in_col)
            board[row, col] = base_symbol
            gold_mask[row, col] = IS_GOLD_SYMBOL[drop_symbol]
            if gold_mask[row, col] == 1:
                multi_mask[row, col] = pick_drop_multiplier_by_col(table_id, col)
            else:
                multi_mask[row, col] = 0
            if row >= SCORE_ROW_OFFSET and base_symbol == C1:
                has_c1_in_col = 1


@njit(nogil=True)
def update_spin_flags(gold_mask, multi_mask, gold_seen, multi_seen):
    for row in range(DISPLAY_WINDOW_SIZE):
        for col in range(REEL_NUM):
            if gold_mask[row, col] == 1:
                gold_seen = 1
                if multi_mask[row, col] > 0:
                    multi_seen = 1
    return gold_seen, multi_seen


@njit(nogil=True)
def copy_layout(target, source):
    for row in range(DISPLAY_WINDOW_SIZE):
        for col in range(REEL_NUM):
            target[row, col] = source[row, col]


@njit(nogil=True)
def run_spin(
    scene_mode,
    fg_multiplier_sum,
    bet_multi,
    board,
    board_initial,
    gold_mask,
    multi_mask,
    hit_mask,
    spin_hits,
    spin_pay,
    spin_eliminate,
    gold_pos,
    keep_symbol,
    keep_gold,
    keep_multi,
    next_above_idx,
):
    clear_2d(board)
    clear_2d(gold_mask)
    clear_2d(multi_mask)
    clear_2d(hit_mask)
    clear_2d(spin_hits)
    clear_2d(spin_pay)
    clear_2d(spin_eliminate)

    table_id = choose_table(scene_mode, fg_multiplier_sum)
    use_drop_a = choose_eliminate_table(scene_mode)
    generate_board(table_id, board, gold_mask, multi_mask, next_above_idx)
    copy_layout(board_initial, board)
    assign_initial_multiplier(table_id, gold_mask, multi_mask, gold_pos)
    pre_eliminate_gold_count = count_gold_mask(gold_mask)

    raw_pay = 0
    combo_idx = 0
    hit_any = 0
    multiplier_sum = fg_multiplier_sum
    gold_appear = 0
    gold_used = 0
    multi_appear = 0
    multi_used = 0

    gold_appear, multi_appear = update_spin_flags(gold_mask, multi_mask, gold_appear, multi_appear)

    while True:
        if combo_idx == 0:
            pay_cascade, _ = evaluate_board(board, hit_mask, spin_hits, spin_pay, bet_multi)
        else:
            pay_cascade, _ = evaluate_board(board, hit_mask, spin_eliminate, spin_pay, bet_multi)

        if pay_cascade <= 0:
            break

        raw_pay += pay_cascade
        hit_any = 1

        for row in range(DISPLAY_WINDOW_SIZE):
            for col in range(REEL_NUM):
                if hit_mask[row, col] == 1:
                    if gold_mask[row, col] == 1:
                        gold_used = 1
                        if multi_mask[row, col] > 0:
                            multi_used = 1
                        multiplier_sum += multi_mask[row, col]
                        hit_mask[row, col] = 2
                    else:
                        board[row, col] = -1
                        gold_mask[row, col] = 0
                        multi_mask[row, col] = 0

        cascade_drop(table_id, use_drop_a, board, gold_mask, multi_mask, hit_mask, keep_symbol, keep_gold, keep_multi, next_above_idx)
        gold_appear, multi_appear = update_spin_flags(gold_mask, multi_mask, gold_appear, multi_appear)
        combo_idx += 1

    scatter_count = count_scatter(board)
    final_multiplier = multiplier_sum if multi_used == 1 and multiplier_sum > 0 else 1
    final_pay = raw_pay * final_multiplier
    return (
        final_pay,
        scatter_count,
        hit_any,
        multiplier_sum,
        final_multiplier,
        combo_idx,
        gold_appear,
        gold_used,
        multi_appear,
        multi_used,
        pre_eliminate_gold_count,
    )


@njit(nogil=True)
def copy_board_snapshot(history, attempt_idx, board):
    for row in range(DISPLAY_WINDOW_SIZE):
        for col in range(REEL_NUM):
            history[attempt_idx, row, col] = board[row, col]


@njit(nogil=True)
def print_retry_failure_trace(attempt_count, scatter_history, board_history, retry_fail_reason):
    print("")
    print("=== Retry Failure Trace ===")
    print("retry_fail_reason =", retry_fail_reason)
    print("attempt_count =", attempt_count)
    for attempt_idx in range(attempt_count):
        print("attempt", attempt_idx + 1, "scatter_count =", scatter_history[attempt_idx])
        for row in range(DISPLAY_WINDOW_SIZE):
            print(
                board_history[attempt_idx, row, 0],
                board_history[attempt_idx, row, 1],
                board_history[attempt_idx, row, 2],
                board_history[attempt_idx, row, 3],
                board_history[attempt_idx, row, 4],
            )
        print("")


@njit(nogil=True)
def add_line_record(record_data, row_start, data, factor, scene_idx):
    offset = scene_idx * SYMBOLS_COUNT
    for line_idx in range(3):
        for symbol in range(SYMBOLS_COUNT):
            value = data[line_idx, symbol]
            if value > 0:
                record_data[row_start + line_idx, offset + symbol] += value * factor


@njit(nogil=True)
def log_multi_line(record_data, scene_idx, score, coin_in):
    if scene_idx == OUTPUT_BG:
        cnt_idx = R_MULTIPLIER_RANGE_CNT_BG
        pay_idx = R_MULTIPLIER_RANGE_PAY_BG
    elif scene_idx == OUTPUT_FG:
        cnt_idx = R_MULTIPLIER_RANGE_CNT_FG
        pay_idx = R_MULTIPLIER_RANGE_PAY_FG
    else:
        cnt_idx = R_MULTIPLIER_RANGE_CNT_OA
        pay_idx = R_MULTIPLIER_RANGE_PAY_OA

    multi = score / coin_in
    target = THRESHOLD_RECORD.shape[0] - 1
    for idx in range(THRESHOLD_RECORD.shape[0]):
        if multi <= THRESHOLD_RECORD[idx]:
            target = idx
            break

    record_data[cnt_idx, target] += 1
    record_data[pay_idx, target] += score


@njit(nogil=True)
def log_round_multiplier_lines(record_data, pay_bg, pay_fg, pay_total, triggered_bg_fg, coin_in):
    if triggered_bg_fg == 1:
        if pay_fg > 0:
            log_multi_line(record_data, OUTPUT_FG, pay_fg, coin_in)
            log_multi_line(record_data, OUTPUT_OA, pay_fg, coin_in)
        return

    log_multi_line(record_data, OUTPUT_BG, pay_bg, coin_in)
    if pay_fg > 0:
        log_multi_line(record_data, OUTPUT_FG, pay_fg, coin_in)
    log_multi_line(record_data, OUTPUT_OA, pay_total, coin_in)


@njit(nogil=True)
def apply_spin_log(
    record_data,
    scene_idx,
    spin_pay_total,
    hit_any,
    final_multiplier,
    spin_hits,
    spin_pay,
    spin_eliminate,
    eliminate_count,
    gold_appear,
    gold_used,
    multi_appear,
    multi_used,
    final_gold_count,
    final_scatter_count,
    coin_in,
):
    if scene_idx == SCENE_BG:
        if hit_any == 1:
            record_data[R_ALL, RA_HITS_BG] += 1
    else:
        if hit_any == 1:
            record_data[R_ALL, RA_HITS_FG] += 1

    add_line_record(record_data, R_HITS[0], spin_hits, 1, scene_idx)
    add_line_record(record_data, R_PAY[0], spin_pay, final_multiplier, scene_idx)
    add_line_record(record_data, R_ELIMINATE[0], spin_eliminate, 1, scene_idx)

    if scene_idx == SCENE_BG:
        if eliminate_count == 0:
            record_data[R_ALL, RA_ELIMINATE_0] += 1
        elif eliminate_count == 1:
            record_data[R_ALL, RA_ELIMINATE_1] += 1
        elif eliminate_count == 2:
            record_data[R_ALL, RA_ELIMINATE_2] += 1
        elif eliminate_count == 3:
            record_data[R_ALL, RA_ELIMINATE_3] += 1
        elif eliminate_count == 4:
            record_data[R_ALL, RA_ELIMINATE_4] += 1
        else:
            record_data[R_ALL, RA_ELIMINATE_5] += 1
        record_data[R_ALL, RA_FINAL_GOLD_COUNT_BG_0 + min(final_gold_count, 9)] += 1
        if gold_appear == 1:
            record_data[R_ALL, RA_GOLD_APPEAR_SPINS_BG] += 1
        if gold_used == 1:
            record_data[R_ALL, RA_GOLD_USED_SPINS_BG] += 1
        if multi_appear == 1:
            record_data[R_ALL, RA_MULTI_APPEAR_SPINS_BG] += 1
        if multi_used == 1:
            record_data[R_ALL, RA_MULTI_USED_SPINS_BG] += 1
        if final_scatter_count > 0:
            record_data[R_ALL, RA_FINAL_C1_PRESENT_BG] += 1
        if final_multiplier > record_data[R_ALL, RA_MAX_MULTIPLIER_BG]:
            record_data[R_ALL, RA_MAX_MULTIPLIER_BG] = final_multiplier
    else:
        if eliminate_count == 0:
            record_data[R_ALL, RA_ELIMINATE_0_FG] += 1
        elif eliminate_count == 1:
            record_data[R_ALL, RA_ELIMINATE_1_FG] += 1
        elif eliminate_count == 2:
            record_data[R_ALL, RA_ELIMINATE_2_FG] += 1
        elif eliminate_count == 3:
            record_data[R_ALL, RA_ELIMINATE_3_FG] += 1
        elif eliminate_count == 4:
            record_data[R_ALL, RA_ELIMINATE_4_FG] += 1
        else:
            record_data[R_ALL, RA_ELIMINATE_5_FG] += 1
        record_data[R_ALL, RA_FINAL_GOLD_COUNT_FG_0 + min(final_gold_count, 9)] += 1
        if gold_appear == 1:
            record_data[R_ALL, RA_GOLD_APPEAR_SPINS_FG] += 1
        if gold_used == 1:
            record_data[R_ALL, RA_GOLD_USED_SPINS_FG] += 1
        if multi_appear == 1:
            record_data[R_ALL, RA_MULTI_APPEAR_SPINS_FG] += 1
        if multi_used == 1:
            record_data[R_ALL, RA_MULTI_USED_SPINS_FG] += 1
        if final_scatter_count > 0:
            record_data[R_ALL, RA_FINAL_C1_PRESENT_FG] += 1
        if final_multiplier > record_data[R_ALL, RA_MAX_MULTIPLIER_FG]:
            record_data[R_ALL, RA_MAX_MULTIPLIER_FG] = final_multiplier

    record_data[R_ALL, RA_GOLD_APPEAR_SPINS] += gold_appear
    record_data[R_ALL, RA_GOLD_USED_SPINS] += gold_used
    record_data[R_ALL, RA_MULTI_APPEAR_SPINS] += multi_appear
    record_data[R_ALL, RA_MULTI_USED_SPINS] += multi_used

    if spin_pay_total >= MAX_WIN_MULTIPLIER * coin_in:
        record_data[R_ALL, RA_MAX_WIN_HITS] += 1
    if spin_pay_total > record_data[R_ALL, RA_MAX_SINGLE_WIN]:
        record_data[R_ALL, RA_MAX_SINGLE_WIN] = spin_pay_total
    if final_multiplier > record_data[R_ALL, RA_MAX_MULTIPLIER]:
        record_data[R_ALL, RA_MAX_MULTIPLIER] = final_multiplier


@njit(nogil=True)
def run_free_game_session(
    record_data,
    free_spins,
    bet_multi,
    coin_in,
    board,
    board_initial,
    gold_mask,
    multi_mask,
    hit_mask,
    spin_hits,
    spin_pay,
    spin_eliminate,
    gold_pos,
    keep_symbol,
    keep_gold,
    keep_multi,
    next_above_idx,
):
    pay_fg = 0
    fg_multiplier_sum = 0
    remaining_freespin = free_spins if free_spins < FG_SPIN_CAP else FG_SPIN_CAP

    while remaining_freespin > 0:
        fg_result = run_spin(
            SCENE_FG,
            fg_multiplier_sum,
            bet_multi,
            board,
            board_initial,
            gold_mask,
            multi_mask,
            hit_mask,
            spin_hits,
            spin_pay,
            spin_eliminate,
            gold_pos,
            keep_symbol,
            keep_gold,
            keep_multi,
            next_above_idx,
        )
        pay_fg += fg_result[0]
        fg_multiplier_sum = fg_result[3]
        apply_spin_log(
            record_data,
            SCENE_FG,
            fg_result[0],
            fg_result[2],
            fg_result[4],
            spin_hits,
            spin_pay,
            spin_eliminate,
            fg_result[5],
            fg_result[6],
            fg_result[7],
            fg_result[8],
            fg_result[9],
            fg_result[10],
            fg_result[1],
            coin_in,
        )

        record_data[R_ALL, RA_FREE_SPINS] += 1
        remaining_freespin -= 1

        if fg_result[1] >= 3:
            extra_spins = 15 + (fg_result[1] - 3) * 2
            remaining_freespin = min(remaining_freespin + extra_spins, FG_SPIN_CAP)
            record_data[R_ALL, RA_RE_TRIGGER] += 1

    return pay_fg


@njit("int64[:, :](int64[:, :], int64, int64, int64, int64)", nogil=True)
def simulator_chunk(record_data, total_round, bet_mode, bet_multi, coin_in):
    board = np.zeros(LAYOUT_SHAPE, np.int64)
    board_initial = np.zeros(LAYOUT_SHAPE, np.int64)
    gold_mask = np.zeros(LAYOUT_SHAPE, np.int64)
    multi_mask = np.zeros(LAYOUT_SHAPE, np.int64)
    hit_mask = np.zeros(LAYOUT_SHAPE, np.int64)
    spin_hits = np.zeros((3, SYMBOLS_COUNT), np.int64)
    spin_pay = np.zeros((3, SYMBOLS_COUNT), np.int64)
    spin_eliminate = np.zeros((3, SYMBOLS_COUNT), np.int64)
    gold_pos = np.zeros((DISPLAY_WINDOW_SIZE * REEL_NUM, 2), np.int64)
    keep_symbol = np.zeros(DISPLAY_WINDOW_SIZE, np.int64)
    keep_gold = np.zeros(DISPLAY_WINDOW_SIZE, np.int64)
    keep_multi = np.zeros(DISPLAY_WINDOW_SIZE, np.int64)
    next_above_idx = np.zeros(REEL_NUM, np.int64)
    round_record = np.zeros(RECORD_SIZE, np.int64)
    bg_round_record = np.zeros(RECORD_SIZE, np.int64)
    fg_round_record = np.zeros(RECORD_SIZE, np.int64)
    scatter_history = np.zeros(CARD_RETRY_LIMIT, np.int64)
    board_history = np.zeros((CARD_RETRY_LIMIT, DISPLAY_WINDOW_SIZE, REEL_NUM), np.int64)

    for _ in range(total_round):
        retry_count = 0
        normal_card_idx = -1
        fg_card_idx = -2
        buy_feature_card_idx = -1
        bg_freegame_triggered_once = 0

        if bet_mode == MODE_NORMALBET:
            normal_card_idx = pick_card(PROFILE_NORMAL_BET) if CARD_SYSTEM_ENABLED else -1
        else:
            buy_feature_card_idx = pick_card(PROFILE_BUY_FEATURE) if CARD_SYSTEM_ENABLED else -1

        if bet_mode == MODE_NORMALBET and CARD_SYSTEM_ENABLED and normal_card_idx >= 0 and CARD_TYPES[PROFILE_NORMAL_BET, normal_card_idx] == CARD_TYPE_FREE_GAME:
            clear_2d(round_record)
            clear_2d(bg_round_record)
            clear_2d(fg_round_record)

            pay_bg = 0
            pay_fg = 0
            pay_total = 0
            free_spins = 0
            triggered_bg_fg = 0
            retry_fail_reason = RETRY_FAIL_NONE

            while True:
                clear_2d(bg_round_record)

                bg_result = run_spin(
                    SCENE_BG,
                    0,
                    bet_multi,
                    board,
                    board_initial,
                    gold_mask,
                    multi_mask,
                    hit_mask,
                    spin_hits,
                    spin_pay,
                    spin_eliminate,
                    gold_pos,
                    keep_symbol,
                    keep_gold,
                    keep_multi,
                    next_above_idx,
                )
                pay_bg = bg_result[0]
                triggered_bg_fg = 1 if bg_result[1] >= 3 else 0
                free_spins = calc_free_spins(bg_result[1], 0)

                apply_spin_log(
                    bg_round_record,
                    SCENE_BG,
                    bg_result[0],
                    bg_result[2],
                    bg_result[4],
                    spin_hits,
                    spin_pay,
                    spin_eliminate,
                    bg_result[5],
                    bg_result[6],
                    bg_result[7],
                    bg_result[8],
                    bg_result[9],
                    bg_result[10],
                    bg_result[1],
                    coin_in,
                )

                if TRACE_RETRY_FAILURE and retry_count < CARD_RETRY_LIMIT:
                    scatter_history[retry_count] = bg_result[1]
                    copy_board_snapshot(board_history, retry_count, board_initial)

                if triggered_bg_fg == 1:
                    bg_freegame_triggered_once = 1
                    bg_round_record[R_ALL, RA_TRIGGER_FREEGAME] += 1
                    bg_round_record[R_ALL, RA_TRIGGER_FG_PAY_BG] += pay_bg
                    break

                retry_count += 1
                retry_fail_reason = RETRY_FAIL_BG_FREEGAME
                if retry_count >= CARD_RETRY_LIMIT:
                    if TRACE_RETRY_FAILURE:
                        print_retry_failure_trace(retry_count, scatter_history, board_history, retry_fail_reason)
                    bg_round_record[R_ALL, RA_RETRY_LIMIT_EXCEEDED] += 1
                    bg_round_record[R_ALL, RA_RETRY_LIMIT_BG_FREEGAME] += 1
                    bg_round_record[R_ALL, RA_RETRY_LIMIT_BG_FREEGAME_NEVER_TRIGGER] += 1
                    break

            merge_round_record(round_record, bg_round_record)

            if triggered_bg_fg == 1:
                if fg_card_idx == -2:
                    fg_card_idx = pick_card(PROFILE_FREE_GAME)

                fg_retry_count = 0
                while True:
                    clear_2d(fg_round_record)
                    pay_fg = run_free_game_session(
                        fg_round_record,
                        free_spins,
                        bet_multi,
                        coin_in,
                        board,
                        board_initial,
                        gold_mask,
                        multi_mask,
                        hit_mask,
                        spin_hits,
                        spin_pay,
                        spin_eliminate,
                        gold_pos,
                        keep_symbol,
                        keep_gold,
                        keep_multi,
                        next_above_idx,
                    )
                    if is_card_match(PROFILE_FREE_GAME, fg_card_idx, pay_fg, coin_in, 1):
                        break

                    fg_retry_count += 1
                    retry_fail_reason = RETRY_FAIL_FG
                    if fg_retry_count >= CARD_RETRY_LIMIT:
                        fg_round_record[R_ALL, RA_RETRY_LIMIT_EXCEEDED] += 1
                        fg_round_record[R_ALL, RA_RETRY_LIMIT_FG] += 1
                        break

                retry_count += fg_retry_count
                merge_round_record(round_record, fg_round_record)

            pay_total = pay_bg + pay_fg
            round_record[R_ALL, RA_RETRY_TOTAL] += retry_count

            pay_x = pay_total / coin_in
            round_record[R_ALL, RA_X_SUM] += int(pay_x * 1000000)
            round_record[R_ALL, RA_X_SQUARE] += int((pay_x * pay_x) * 1000000)

            log_round_multiplier_lines(round_record, pay_bg, pay_fg, pay_total, triggered_bg_fg, coin_in)

            merge_round_record(record_data, round_record)
            continue

        while True:
            clear_2d(round_record)

            pay_bg = 0
            pay_fg = 0
            pay_total = 0
            free_spins = 0
            triggered_bg_fg = 0
            accepted = 1
            retry_fail_reason = RETRY_FAIL_NONE

            if bet_mode == MODE_NORMALBET:
                bg_result = run_spin(
                    SCENE_BG,
                    0,
                    bet_multi,
                    board,
                    board_initial,
                    gold_mask,
                    multi_mask,
                    hit_mask,
                    spin_hits,
                    spin_pay,
                    spin_eliminate,
                    gold_pos,
                    keep_symbol,
                    keep_gold,
                    keep_multi,
                    next_above_idx,
                )
                pay_bg = bg_result[0]
                triggered_bg_fg = 1 if bg_result[1] >= 3 else 0
                free_spins = calc_free_spins(bg_result[1], 0)

                apply_spin_log(
                    round_record,
                    SCENE_BG,
                    bg_result[0],
                    bg_result[2],
                    bg_result[4],
                    spin_hits,
                    spin_pay,
                    spin_eliminate,
                    bg_result[5],
                    bg_result[6],
                    bg_result[7],
                    bg_result[8],
                    bg_result[9],
                    bg_result[10],
                    bg_result[1],
                    coin_in,
                )

                if TRACE_RETRY_FAILURE and retry_count < CARD_RETRY_LIMIT:
                    scatter_history[retry_count] = bg_result[1]
                    copy_board_snapshot(board_history, retry_count, board_initial)

                if triggered_bg_fg == 1:
                    round_record[R_ALL, RA_TRIGGER_FREEGAME] += 1
                    round_record[R_ALL, RA_TRIGGER_FG_PAY_BG] += pay_bg

                if CARD_SYSTEM_ENABLED and normal_card_idx >= 0:
                    if CARD_TYPES[PROFILE_NORMAL_BET, normal_card_idx] == CARD_TYPE_FREE_GAME:
                        if triggered_bg_fg == 0:
                            accepted = 0
                            retry_fail_reason = RETRY_FAIL_BG_FREEGAME
                        else:
                            bg_freegame_triggered_once = 1
                            if fg_card_idx == -2:
                                fg_card_idx = pick_card(PROFILE_FREE_GAME)
                            pay_fg = run_free_game_session(
                                round_record,
                                free_spins,
                                bet_multi,
                                coin_in,
                                board,
                                board_initial,
                                gold_mask,
                                multi_mask,
                                hit_mask,
                                spin_hits,
                                spin_pay,
                                spin_eliminate,
                                gold_pos,
                                keep_symbol,
                                keep_gold,
                                keep_multi,
                                next_above_idx,
                            )
                            if is_card_match(PROFILE_FREE_GAME, fg_card_idx, pay_fg, coin_in, 1) is False:
                                accepted = 0
                                retry_fail_reason = RETRY_FAIL_FG
                    else:
                        if triggered_bg_fg == 1 or is_card_match(PROFILE_NORMAL_BET, normal_card_idx, pay_bg, coin_in, 0) is False:
                            accepted = 0
                            retry_fail_reason = RETRY_FAIL_BG_RANGE
                else:
                    if triggered_bg_fg == 1:
                        pay_fg = run_free_game_session(
                            round_record,
                            free_spins,
                            bet_multi,
                            coin_in,
                            board,
                            board_initial,
                            gold_mask,
                            multi_mask,
                            hit_mask,
                            spin_hits,
                            spin_pay,
                            spin_eliminate,
                            gold_pos,
                            keep_symbol,
                            keep_gold,
                            keep_multi,
                            next_above_idx,
                        )
            else:
                bf_retry_count = 0
                while True:
                    bf_result = run_spin(
                        SCENE_BF,
                        0,
                        bet_multi,
                        board,
                        board_initial,
                        gold_mask,
                        multi_mask,
                        hit_mask,
                        spin_hits,
                        spin_pay,
                        spin_eliminate,
                        gold_pos,
                        keep_symbol,
                        keep_gold,
                        keep_multi,
                        next_above_idx,
                    )
                    if bf_result[1] >= 3:
                        break
                    bf_retry_count += 1
                    if bf_retry_count > 5000:
                        raise ValueError("Buy Feature reroll exceeded 5000 attempts; check BF trigger condition.")
                pay_bg = bf_result[0]
                free_spins = calc_free_spins(bf_result[1], 0)

                apply_spin_log(
                    round_record,
                    SCENE_BG,
                    bf_result[0],
                    bf_result[2],
                    bf_result[4],
                    spin_hits,
                    spin_pay,
                    spin_eliminate,
                    bf_result[5],
                    bf_result[6],
                    bf_result[7],
                    bf_result[8],
                    bf_result[9],
                    bf_result[10],
                    bf_result[1],
                    coin_in,
                )

                round_record[R_ALL, RA_TRIGGER_FREEGAME] += 1
                round_record[R_ALL, RA_TRIGGER_FG_PAY_BG] += pay_bg
                pay_fg = run_free_game_session(
                    round_record,
                    free_spins,
                    bet_multi,
                    coin_in,
                    board,
                    board_initial,
                    gold_mask,
                    multi_mask,
                    hit_mask,
                    spin_hits,
                    spin_pay,
                    spin_eliminate,
                    gold_pos,
                    keep_symbol,
                    keep_gold,
                    keep_multi,
                    next_above_idx,
                )

                if CARD_SYSTEM_ENABLED and buy_feature_card_idx >= 0:
                    pay_total = pay_bg + pay_fg
                    if is_card_match(PROFILE_BUY_FEATURE, buy_feature_card_idx, pay_total, coin_in, 1) is False:
                        accepted = 0
                        retry_fail_reason = RETRY_FAIL_FG

            if pay_total <= 0:
                pay_total = pay_bg + pay_fg

            if accepted == 1:
                break

            retry_count += 1
            if retry_count >= CARD_RETRY_LIMIT:
                if TRACE_RETRY_FAILURE:
                    print_retry_failure_trace(retry_count, scatter_history, board_history, retry_fail_reason)
                round_record[R_ALL, RA_RETRY_LIMIT_EXCEEDED] += 1
                if retry_fail_reason == RETRY_FAIL_BG_RANGE:
                    round_record[R_ALL, RA_RETRY_LIMIT_BG_RANGE] += 1
                elif retry_fail_reason == RETRY_FAIL_BG_FREEGAME:
                    round_record[R_ALL, RA_RETRY_LIMIT_BG_FREEGAME] += 1
                    if bg_freegame_triggered_once == 0:
                        round_record[R_ALL, RA_RETRY_LIMIT_BG_FREEGAME_NEVER_TRIGGER] += 1
                elif retry_fail_reason == RETRY_FAIL_FG:
                    round_record[R_ALL, RA_RETRY_LIMIT_FG] += 1
                break

        round_record[R_ALL, RA_RETRY_TOTAL] += retry_count

        pay_x = pay_total / coin_in
        round_record[R_ALL, RA_X_SUM] += int(pay_x * 1000000)
        round_record[R_ALL, RA_X_SQUARE] += int((pay_x * pay_x) * 1000000)

        log_round_multiplier_lines(round_record, pay_bg, pay_fg, pay_total, triggered_bg_fg, coin_in)

        merge_round_record(record_data, round_record)

    return record_data


# ===== Runtime Helpers =====


def calc_coin_in(bet_mode, bet_multi):
    if bet_mode == MODE_NORMALBET:
        return bet_multi * DEFAULT_COIN_IN * NORMALBET
    if bet_mode == MODE_FEATUREBUY:
        return bet_multi * DEFAULT_COIN_IN * NORMALBET * FEATUREBUY
    raise ValueError(f"Unsupported bet mode: {bet_mode}")


def merge_record_data(chunks):
    merged = np.zeros(RECORD_SIZE, dtype=np.int64)
    for chunk in chunks:
        merged += chunk
    merged[R_ALL, RA_MAX_SINGLE_WIN] = max(int(chunk[R_ALL, RA_MAX_SINGLE_WIN]) for chunk in chunks)
    merged[R_ALL, RA_MAX_MULTIPLIER] = max(int(chunk[R_ALL, RA_MAX_MULTIPLIER]) for chunk in chunks)
    merged[R_ALL, RA_MAX_MULTIPLIER_BG] = max(int(chunk[R_ALL, RA_MAX_MULTIPLIER_BG]) for chunk in chunks)
    merged[R_ALL, RA_MAX_MULTIPLIER_FG] = max(int(chunk[R_ALL, RA_MAX_MULTIPLIER_FG]) for chunk in chunks)
    return merged


def build_chunk_rounds(total_round, threads):
    threads = max(1, min(int(threads), int(total_round) if total_round > 0 else 1))
    base = total_round // threads
    extra = total_round % threads
    rounds = []
    for idx in range(threads):
        rounds.append(base + (1 if idx < extra else 0))
    return [value for value in rounds if value > 0]


def run_simulation(total_round=TOTAL_ROUNDS, bet_mode=BET_MODE, bet_multi=BET_MULTI, threads=THREADS):
    total_round = int(total_round)
    bet_mode = int(bet_mode)
    bet_multi = int(bet_multi)
    if TRACE_RETRY_FAILURE:
        threads = 1
    coin_in = int(calc_coin_in(bet_mode, bet_multi))

    simulator_chunk(np.zeros(RECORD_SIZE, dtype=np.int64), 1, bet_mode, bet_multi, coin_in)

    chunk_rounds = build_chunk_rounds(total_round, threads)
    start = time.perf_counter()
    if len(chunk_rounds) == 1:
        record_data = simulator_chunk(np.zeros(RECORD_SIZE, dtype=np.int64), chunk_rounds[0], bet_mode, bet_multi, coin_in)
    else:
        with ThreadPoolExecutor(max_workers=len(chunk_rounds)) as executor:
            futures = [executor.submit(simulator_chunk, np.zeros(RECORD_SIZE, dtype=np.int64), rounds, bet_mode, bet_multi, coin_in) for rounds in chunk_rounds]
            record_data = merge_record_data([future.result() for future in futures])
    duration = time.perf_counter() - start
    return record_data, duration, coin_in


def format_threshold_labels(thresholds):
    labels = []
    for idx, current in enumerate(thresholds):
        if idx == 0:
            labels.append("0")
        else:
            labels.append(f"{thresholds[idx - 1]} < X <= {current}")
    return labels


def build_result_frames(record_data, total_round, duration, coin_in, bet_mode, bet_multi, threads=THREADS):
    record_data_float = record_data.astype(np.float64)
    x_sum = record_data_float[R_ALL, RA_X_SUM] / 1000000
    x_square = record_data_float[R_ALL, RA_X_SQUARE] / 1000000

    rtp_bg = record_data_float[R_PAY[0] : R_PAY[1], :SYMBOLS_COUNT].sum() / coin_in / total_round
    rtp_fg = record_data_float[R_PAY[0] : R_PAY[1], SYMBOLS_COUNT : SYMBOLS_COUNT * 2].sum() / coin_in / total_round
    rtp_total = rtp_bg + rtp_fg

    fg_spins = record_data_float[R_ALL, RA_FREE_SPINS]
    total_spins = total_round + fg_spins
    hit_rate_bg = record_data_float[R_ALL, RA_HITS_BG] / total_round if total_round > 0 else 0.0
    hit_rate_fg = record_data_float[R_ALL, RA_HITS_FG] / fg_spins if fg_spins > 0 else 0.0
    hit_rate_total = (record_data_float[R_ALL, RA_HITS_BG] + record_data_float[R_ALL, RA_HITS_FG]) / total_spins if total_spins > 0 else 0.0
    fg_trigger_count = record_data_float[R_ALL, RA_TRIGGER_FREEGAME]
    trigger_rate_fg = fg_trigger_count / total_round if total_round > 0 else 0.0
    retrigger_rate = record_data_float[R_ALL, RA_RE_TRIGGER] / fg_spins if fg_spins > 0 else 0.0
    avg_fg_spins = fg_spins / fg_trigger_count if fg_trigger_count > 0 else 0.0
    avg_fg_multiplier = rtp_fg / trigger_rate_fg if trigger_rate_fg > 0 else 0.0
    trigger_fg_bg_pay = record_data_float[R_ALL, RA_TRIGGER_FG_PAY_BG]
    trigger_fg_bg_count = int(record_data[R_ALL, RA_TRIGGER_FREEGAME])
    retry_total = record_data_float[R_ALL, RA_RETRY_TOTAL]
    retry_limit_exceeded = record_data_float[R_ALL, RA_RETRY_LIMIT_EXCEEDED]
    retry_limit_bg_range = record_data_float[R_ALL, RA_RETRY_LIMIT_BG_RANGE]
    retry_limit_bg_freegame = record_data_float[R_ALL, RA_RETRY_LIMIT_BG_FREEGAME]
    retry_limit_fg = record_data_float[R_ALL, RA_RETRY_LIMIT_FG]
    retry_limit_bg_freegame_never_trigger = record_data_float[R_ALL, RA_RETRY_LIMIT_BG_FREEGAME_NEVER_TRIGGER]
    avg_retry = retry_total / total_round if total_round > 0 else 0.0

    std = math.sqrt(max(0.0, x_square / total_round - (x_sum / total_round) ** 2)) if total_round > 0 else 0.0
    gold_usage_rate_bg = record_data_float[R_ALL, RA_GOLD_USED_SPINS_BG] / record_data_float[R_ALL, RA_GOLD_APPEAR_SPINS_BG] if record_data_float[R_ALL, RA_GOLD_APPEAR_SPINS_BG] > 0 else 0.0
    gold_usage_rate_fg = record_data_float[R_ALL, RA_GOLD_USED_SPINS_FG] / record_data_float[R_ALL, RA_GOLD_APPEAR_SPINS_FG] if record_data_float[R_ALL, RA_GOLD_APPEAR_SPINS_FG] > 0 else 0.0
    multi_usage_rate_bg = record_data_float[R_ALL, RA_MULTI_USED_SPINS_BG] / record_data_float[R_ALL, RA_MULTI_APPEAR_SPINS_BG] if record_data_float[R_ALL, RA_MULTI_APPEAR_SPINS_BG] > 0 else 0.0
    multi_usage_rate_fg = record_data_float[R_ALL, RA_MULTI_USED_SPINS_FG] / record_data_float[R_ALL, RA_MULTI_APPEAR_SPINS_FG] if record_data_float[R_ALL, RA_MULTI_APPEAR_SPINS_FG] > 0 else 0.0
    max_multiplier_bg = int(record_data[R_ALL, RA_MAX_MULTIPLIER_BG])
    max_multiplier_fg = int(record_data[R_ALL, RA_MAX_MULTIPLIER_FG])
    final_c1_present_bg = int(record_data[R_ALL, RA_FINAL_C1_PRESENT_BG])
    final_c1_present_fg = int(record_data[R_ALL, RA_FINAL_C1_PRESENT_FG])
    bet_mode_label = "Normal Bet"
    if bet_mode == MODE_FEATUREBUY:
        bet_mode_label = "Feature Buy"

    base_rows = [
        ("game_id", GAME_ID, ""),
        ("version", CONFIG_VERSION, ""),
        ("bet_mode", bet_mode_label, ""),
        ("bet_multi", bet_multi, ""),
        ("coin_in", coin_in, ""),
        ("total_rounds", f"{total_round:,}", ""),
        ("threads", threads, ""),
        ("duration_sec", f"{duration:.2f}s", ""),
        ("", "", ""),
        ("rtp_total", f"{rtp_total:.6f}", ""),
        ("rtp_bg", f"{rtp_bg:.6f}", ""),
        ("rtp_fg", f"{rtp_fg:.6f}", ""),
        ("", "", ""),
        ("hit_rate_bg", f"{hit_rate_bg:.6f}", ""),
        ("hit_rate_fg", f"{hit_rate_fg:.6f}", ""),
        ("hit_rate_total", f"{hit_rate_total:.6f}", ""),
        ("", "", ""),
        ("fg_trigger_rate", f"{trigger_rate_fg:.6f}", ""),
        ("retrigger_rate", f"{retrigger_rate:.6f}", ""),
        ("avg_fg_multiplier", f"{avg_fg_multiplier:.6f}", ""),
        ("avg_fg_spins", f"{avg_fg_spins:.6f}", ""),
        ("trigger_fg_bg_pay", int(trigger_fg_bg_pay), ""),
        ("trigger_fg_bg_count", trigger_fg_bg_count, ""),
        ("", "", ""),
        ("card_system", "on" if CARD_SYSTEM_ENABLED else "off", ""),
        ("retry_limit", CARD_RETRY_LIMIT if CARD_SYSTEM_ENABLED else 0, ""),
        ("retry_total", int(retry_total), ""),
        ("avg_retry", f"{avg_retry:.6f}", ""),
        ("retry_limit_exceeded", int(retry_limit_exceeded), ""),
        ("retry_limit_bg_range", int(retry_limit_bg_range), ""),
        ("retry_limit_bg_freegame", int(retry_limit_bg_freegame), ""),
        ("retry_limit_bg_freegame_never_trigger", int(retry_limit_bg_freegame_never_trigger), ""),
        ("retry_limit_fg", int(retry_limit_fg), ""),
        ("", "", ""),
        ("volatility_std", f"{std:.6f}", ""),
        ("max_win_hits", int(record_data[R_ALL, RA_MAX_WIN_HITS]), ""),
        ("max_win_x", f"{record_data[R_ALL, RA_MAX_SINGLE_WIN] / coin_in:.2f}", ""),
        ("", "", ""),
        ("gold_usage_rate_bg", f"{gold_usage_rate_bg:.6f}", ""),
        ("gold_usage_rate_fg", f"{gold_usage_rate_fg:.6f}", ""),
        ("multiplier_usage_rate_bg", f"{multi_usage_rate_bg:.6f}", ""),
        ("multiplier_usage_rate_fg", f"{multi_usage_rate_fg:.6f}", ""),
        ("max_multiplier_bg", max_multiplier_bg, ""),
        ("max_multiplier_fg", max_multiplier_fg, ""),
        ("", "", ""),
        ("final_c1_present_bg", final_c1_present_bg, ""),
        ("final_c1_present_fg", final_c1_present_fg, ""),
    ]
    df_base = pd.DataFrame(base_rows, columns=["Index", "Value", "Value2"])

    column_labels = [SYMBOL_STR[sym] for sym in SYMBOL_ID] + [SYMBOL_STR[sym] for sym in SYMBOL_ID]
    df_hits = pd.DataFrame(record_data_float[R_HITS[0] : R_HITS[1], : SYMBOLS_COUNT * 2], columns=column_labels, index=["3", "4", "5"])
    df_pay = pd.DataFrame(record_data_float[R_PAY[0] : R_PAY[1], : SYMBOLS_COUNT * 2] / coin_in / total_round, columns=column_labels, index=["3", "4", "5"])
    df_eliminate = pd.DataFrame(record_data_float[R_ELIMINATE[0] : R_ELIMINATE[1], : SYMBOLS_COUNT * 2], columns=column_labels, index=["3", "4", "5"])
    df_multiplier = pd.DataFrame(
        {
            "Interval": format_threshold_labels(THRESHOLD_RECORD),
            "base_game_cnt": record_data_float[R_MULTIPLIER_RANGE_CNT_BG, : len(THRESHOLD_RECORD)],
            "base_game_pay": record_data_float[R_MULTIPLIER_RANGE_PAY_BG, : len(THRESHOLD_RECORD)],
            "free_game_cnt": record_data_float[R_MULTIPLIER_RANGE_CNT_FG, : len(THRESHOLD_RECORD)],
            "free_game_pay": record_data_float[R_MULTIPLIER_RANGE_PAY_FG, : len(THRESHOLD_RECORD)],
            "overall_cnt": record_data_float[R_MULTIPLIER_RANGE_CNT_OA, : len(THRESHOLD_RECORD)],
            "overall_pay": record_data_float[R_MULTIPLIER_RANGE_PAY_OA, : len(THRESHOLD_RECORD)],
        }
    )

    summary = {
        "rtp_total": rtp_total,
        "rtp_bg": rtp_bg,
        "rtp_fg": rtp_fg,
        "hit_rate_bg": hit_rate_bg,
        "hit_rate_fg": hit_rate_fg,
        "hit_rate_total": hit_rate_total,
        "fg_trigger_rate": trigger_rate_fg,
        "retrigger_rate": retrigger_rate,
        "avg_fg_multiplier": avg_fg_multiplier,
        "avg_fg_spins": avg_fg_spins,
        "trigger_fg_bg_pay": trigger_fg_bg_pay,
        "trigger_fg_bg_count": trigger_fg_bg_count,
        "retry_total": retry_total,
        "avg_retry": avg_retry,
        "retry_limit_exceeded": retry_limit_exceeded,
        "retry_limit_bg_range": retry_limit_bg_range,
        "retry_limit_bg_freegame": retry_limit_bg_freegame,
        "retry_limit_bg_freegame_never_trigger": retry_limit_bg_freegame_never_trigger,
        "retry_limit_fg": retry_limit_fg,
        "max_win_x": record_data[R_ALL, RA_MAX_SINGLE_WIN] / coin_in,
        "gold_usage_rate_bg": gold_usage_rate_bg,
        "gold_usage_rate_fg": gold_usage_rate_fg,
        "multi_usage_rate_bg": multi_usage_rate_bg,
        "multi_usage_rate_fg": multi_usage_rate_fg,
        "max_multiplier_bg": max_multiplier_bg,
        "max_multiplier_fg": max_multiplier_fg,
        "final_c1_present_bg": final_c1_present_bg,
        "final_c1_present_fg": final_c1_present_fg,
        "volatility_std": std,
    }
    return df_base, df_hits, df_pay, df_eliminate, df_multiplier, summary


def print_console_result(df_base, df_hits, df_pay, df_eliminate):
    if SHOW_CONSOLE_SUMMARY:
        print("\n=== Fixed Result ===")
        summary_rows = list(df_base.itertuples(index=False))
        key_width = max(len(str(row.Index)) for row in summary_rows if str(row.Index))
        for row in summary_rows:
            label = str(row.Index)
            value = str(row.Value)
            if not label:
                print("")
                continue
            print(f"{label:<{key_width}} : {value}")
    if SHOW_CONSOLE_DETAIL:
        print("\n=== By Game Result: Hits ===")
        print(df_hits.to_string())
        print("\n=== By Game Result: RTP ===")
        print(df_pay.to_string())
        print("\n=== By Game Result: Eliminate ===")
        print(df_eliminate.to_string())


def output_report(df_base, df_hits, df_pay, df_eliminate, df_multiplier, record_data, bet_mode):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    path = os.path.join(OUTPUT_DIR, f"{GAME_ID}_{timestamp}_betmode{bet_mode}.xlsx")
    with pd.ExcelWriter(path) as writer:
        df_base.to_excel(writer, sheet_name="Base Info", index=False)
        df_multiplier.to_excel(writer, sheet_name="Multiplier Line", index=False)
        df_hits.to_excel(writer, sheet_name="Hits")
        df_pay.to_excel(writer, sheet_name="Pay")
        df_eliminate.to_excel(writer, sheet_name="Eliminate")
        pd.DataFrame(record_data).to_excel(writer, sheet_name="Record Data", index=False)
    return path


def run_single_spin_debug(bet_mode=BET_MODE, bet_multi=BET_MULTI):
    coin_in = calc_coin_in(bet_mode, bet_multi)
    board = np.zeros(LAYOUT_SHAPE, np.int64)
    board_initial = np.zeros(LAYOUT_SHAPE, np.int64)
    gold_mask = np.zeros(LAYOUT_SHAPE, np.int64)
    multi_mask = np.zeros(LAYOUT_SHAPE, np.int64)
    hit_mask = np.zeros(LAYOUT_SHAPE, np.int64)
    spin_hits = np.zeros((3, SYMBOLS_COUNT), np.int64)
    spin_pay = np.zeros((3, SYMBOLS_COUNT), np.int64)
    spin_eliminate = np.zeros((3, SYMBOLS_COUNT), np.int64)
    gold_pos = np.zeros((DISPLAY_WINDOW_SIZE * REEL_NUM, 2), np.int64)
    keep_symbol = np.zeros(DISPLAY_WINDOW_SIZE, np.int64)
    keep_gold = np.zeros(DISPLAY_WINDOW_SIZE, np.int64)
    keep_multi = np.zeros(DISPLAY_WINDOW_SIZE, np.int64)
    next_above_idx = np.zeros(REEL_NUM, np.int64)
    result = run_spin(
        SCENE_BG if bet_mode == MODE_NORMALBET else SCENE_BF,
        0,
        bet_multi,
        board,
        board_initial,
        gold_mask,
        multi_mask,
        hit_mask,
        spin_hits,
        spin_pay,
        spin_eliminate,
        gold_pos,
        keep_symbol,
        keep_gold,
        keep_multi,
        next_above_idx,
    )
    print("Single spin result:")
    print(f"coin_in={coin_in}, pay={result[0]}, scatter={result[1]}, final_multiplier={result[4]}, cascades={result[5]}")


def main():
    if RUN_SINGLE_SPIN_DEBUG:
        run_single_spin_debug()
        return

    if TRACE_RETRY_FAILURE:
        print("TRACE_RETRY_FAILURE is on; simulation will run with a single thread.")

    record_data, duration, coin_in = run_simulation()
    df_base, df_hits, df_pay, df_eliminate, df_multiplier, _ = build_result_frames(
        record_data=record_data,
        total_round=TOTAL_ROUNDS,
        duration=duration,
        coin_in=coin_in,
        bet_mode=BET_MODE,
        bet_multi=BET_MULTI,
        threads=THREADS,
    )
    print_console_result(df_base, df_hits, df_pay, df_eliminate)

    if OUTPUT_REPORT:
        report_path = output_report(df_base, df_hits, df_pay, df_eliminate, df_multiplier, record_data, BET_MODE)
        print(f"\nReport: {report_path}")


if __name__ == "__main__":
    main()
