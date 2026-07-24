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

# Single-run settings. Used when RUN_ALL_COMBINATIONS = False.
CONFIG_FILE = "config_92A.js"
TOTAL_ROUNDS = 10**7
BET_MODE = 2  # 0 for normal bet, 1 for extra bet, 2 for feature buy
CARD_SYSTEM_ENABLED = True  # True to enable cards, False to run without cards
CARD_SYSTEM_IS_NEWBIE = False  # True for newbie, False for oldhand

# Batch runs. Edit this list directly when you want to run a custom set once.
RUN_ALL_COMBINATIONS = True
BATCH_RUNS = [
    # {"config_file": "config_92A.js", "bet_mode": 2, "total_rounds": 10**6, "card_system_enabled": False, "card_system_is_newbie": False},  # Test
    # {"config_file": "config_92A.js", "bet_mode": 1, "total_rounds": 10**7, "card_system_enabled": True, "card_system_is_newbie": False},  # Test
    # {"config_file": "config_92B.js", "bet_mode": 1, "total_rounds": 10**7, "card_system_enabled": True, "card_system_is_newbie": False},  # Test
    # {"config_file": "config_94A.js", "bet_mode": 1, "total_rounds": 10**7, "card_system_enabled": True, "card_system_is_newbie": False},  # Test
    # {"config_file": "config_94B.js", "bet_mode": 1, "total_rounds": 10**7, "card_system_enabled": True, "card_system_is_newbie": False},  # Test
    # {"config_file": "config_92A.js", "bet_mode": 2, "total_rounds": 10**5, "card_system_enabled": False, "card_system_is_newbie": False},  # Test
    # {"config_file": "config_92A.js", "bet_mode": 0, "total_rounds": 10**9, "card_system_enabled": False, "card_system_is_newbie": False},  # 自然機率
    {"config_file": "config_92A.js", "bet_mode": 2, "total_rounds": 10**9, "card_system_enabled": False, "card_system_is_newbie": False},  # 自然機率
    # {"config_file": "config_92A.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},  # SCR
    # {"config_file": "config_92A.js", "bet_mode": 1, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},  # SCR
    # {"config_file": "config_92A.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},  # SCR
    # {"config_file": "config_92A.js", "bet_mode": 1, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},  # SCR
    # {"config_file": "config_94A.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},
    # {"config_file": "config_94A.js", "bet_mode": 1, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},
    # {"config_file": "config_94A.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},  # SCR
    # {"config_file": "config_94A.js", "bet_mode": 1, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},  # SCR
    # {"config_file": "config_92B.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},  # SCR
    # {"config_file": "config_92B.js", "bet_mode": 1, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},  # SCR
    # {"config_file": "config_92B.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    # {"config_file": "config_92B.js", "bet_mode": 1, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    # {"config_file": "config_94B.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},
    # {"config_file": "config_94B.js", "bet_mode": 1, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},
    # {"config_file": "config_94B.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    # {"config_file": "config_94B.js", "bet_mode": 1, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    # {"config_file": "config_92A.js", "bet_mode": 2, "total_rounds": 10**7, "card_system_enabled": True, "card_system_is_newbie": False},  # SCR
]


def parse_env_bool(name, default):
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on"}


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "Record")

BET_MULTI = 1
CONFIG_FILE = os.environ.get("H026_CONFIG_FILE", CONFIG_FILE)
CONFIG_PATH = os.path.join(BASE_DIR, CONFIG_FILE)
TOTAL_ROUNDS = int(os.environ.get("H026_TOTAL_ROUNDS", str(TOTAL_ROUNDS)))
BET_MODE = int(os.environ.get("H026_BET_MODE", str(BET_MODE)))
CARD_SYSTEM_ENABLED = parse_env_bool("H026_CARD_SYSTEM_ENABLED", CARD_SYSTEM_ENABLED)
CARD_SYSTEM_IS_NEWBIE = parse_env_bool("H026_CARD_SYSTEM_IS_NEWBIE", CARD_SYSTEM_IS_NEWBIE)
RUN_ALL_COMBINATIONS = parse_env_bool("H026_RUN_ALL_COMBINATIONS", RUN_ALL_COMBINATIONS)
BATCH_COMBINATIONS = list(BATCH_RUNS)

THREADS = max(1, max(8, os.cpu_count() - 2 or 1))
FG_SPIN_CAP = 50
FG_TRIGGER_BASE_SPINS = 12
FG_EXTRA_SPINS_PER_SCATTER = 2
ALLOW_C1_DROP_WHEN_BOARD_HAS_C1 = False

OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = False
SHOW_CONSOLE_DETAIL = False
RUN_SINGLE_SPIN_DEBUG = False
TRACE_RETRY_FAILURE = False
TRACE_BF_BG_WIN = True
TRACE_BF_BG_WIN_LIMIT = 20

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


def _normalize_card_profiles(card_system_raw):
    def _profile_segment_weights(segment_raw, segment_key, legacy_fallback=None):
        if not isinstance(segment_raw, dict):
            return []
        profile_raw = segment_raw.get(segment_key)
        if isinstance(profile_raw, dict):
            weights = list(profile_raw.get("weight_fg" if segment_key == "buy_feature" else "weight_bg", []))
            if weights:
                return weights
        if legacy_fallback is not None:
            return list(segment_raw.get(legacy_fallback, []))
        return []

    def _profile_segment_freegame(segment_raw, segment_key, legacy_fallback=None):
        if not isinstance(segment_raw, dict):
            return []
        profile_raw = segment_raw.get(segment_key)
        if isinstance(profile_raw, dict):
            weights = list(profile_raw.get("weight_fg", []))
            if weights:
                return weights
        if legacy_fallback is not None:
            return list(segment_raw.get(legacy_fallback, []))
        return []

    if not isinstance(card_system_raw, dict):
        return {
            "newbie_bg": [],
            "newbie_fg": [],
            "newbie_extra_bg": [],
            "newbie_extra_fg": [],
            "oldhand_bg": [],
            "oldhand_fg": [],
            "oldhand_extra_bg": [],
            "oldhand_extra_fg": [],
            "weight_bf": [],
        }

    if "profiles" in card_system_raw:
        profiles = card_system_raw.get("profiles", {})
        normal_bet = list(profiles.get("normal_bet", []))
        free_game = list(profiles.get("free_game", []))
        extra_bet = list(profiles.get("extra_bet") or normal_bet)
        extra_free_game = list(profiles.get("extra_free_game") or free_game)
        buy_feature = list(profiles.get("buy_feature", []))
        return {
            "newbie_bg": normal_bet,
            "newbie_fg": free_game,
            "oldhand_bg": list(normal_bet),
            "oldhand_fg": list(free_game),
            "newbie_extra_bg": extra_bet,
            "newbie_extra_fg": extra_free_game,
            "oldhand_extra_bg": list(extra_bet),
            "oldhand_extra_fg": list(extra_free_game),
            "weight_bf": buy_feature,
        }

    newbie = card_system_raw.get("newbie", {}) if isinstance(card_system_raw.get("newbie"), dict) else {}
    oldhand = card_system_raw.get("oldhand", {}) if isinstance(card_system_raw.get("oldhand"), dict) else {}
    legacy_extra_bet = card_system_raw.get("extra_bet", {}) if isinstance(card_system_raw.get("extra_bet"), dict) else {}
    newbie_bg = _profile_segment_weights(newbie, "normal_bet", "weight_bg")
    newbie_fg = _profile_segment_freegame(newbie, "normal_bet", "weight_fg")
    oldhand_bg = _profile_segment_weights(oldhand, "normal_bet", "weight_bg")
    oldhand_fg = _profile_segment_freegame(oldhand, "normal_bet", "weight_fg")
    fallback_bg = oldhand_bg or newbie_bg
    fallback_fg = oldhand_fg or newbie_fg
    newbie_extra_bg = _profile_segment_weights(newbie, "extra_bet")
    newbie_extra_fg = _profile_segment_freegame(newbie, "extra_bet")
    oldhand_extra_bg = _profile_segment_weights(oldhand, "extra_bet")
    oldhand_extra_fg = _profile_segment_freegame(oldhand, "extra_bet")
    if not newbie_extra_bg:
        newbie_extra_bg = list(legacy_extra_bet.get("weight_bg") or newbie_bg or fallback_bg)
    if not newbie_extra_fg:
        newbie_extra_fg = list(legacy_extra_bet.get("weight_fg") or newbie_fg or fallback_fg)
    if not oldhand_extra_bg:
        oldhand_extra_bg = list(legacy_extra_bet.get("weight_bg") or oldhand_bg or fallback_bg)
    if not oldhand_extra_fg:
        oldhand_extra_fg = list(legacy_extra_bet.get("weight_fg") or oldhand_fg or fallback_fg)
    buy_feature_fg = _profile_segment_freegame(oldhand, "buy_feature")
    if not buy_feature_fg:
        buy_feature_fg = list(card_system_raw.get("weight_bf", []))
    return {
        "newbie_bg": list(newbie_bg),
        "newbie_fg": list(newbie_fg),
        "newbie_extra_bg": list(newbie_extra_bg),
        "newbie_extra_fg": list(newbie_extra_fg),
        "oldhand_bg": list(oldhand_bg or fallback_bg),
        "oldhand_fg": list(oldhand_fg or fallback_fg),
        "oldhand_extra_bg": list(oldhand_extra_bg),
        "oldhand_extra_fg": list(oldhand_extra_fg),
        "weight_bf": list(buy_feature_fg),
    }


def _build_card_profile_tables(card_system_raw):
    profile_names = (
        "newbie_bg",
        "newbie_fg",
        "newbie_extra_bg",
        "newbie_extra_fg",
        "oldhand_bg",
        "oldhand_fg",
        "oldhand_extra_bg",
        "oldhand_extra_fg",
        "weight_bf",
    )
    card_type_map = {"range": 0, "free_game": 1}
    normalized_profiles = _normalize_card_profiles(card_system_raw)
    profile_cards = []
    for profile_name in profile_names:
        cards = list(normalized_profiles.get(profile_name, []))
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
MODE_EXTRABET = int(CFG_RAW.get("mode_extrabet", 1))
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
EXTRABET = int(CFG_RAW.get("extrabet", NORMALBET * 2))
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
CARD_SYSTEM_ENABLED = bool(CARD_SYSTEM_ENABLED and CARD_SYSTEM_RAW.get("enabled"))
CARD_RETRY_LIMIT = int(CARD_SYSTEM_RAW.get("retry_limit", 0))
CARD_TYPES, CARD_MIN, CARD_MAX, CARD_WEIGHT_CUM, CARD_COUNTS = _build_card_profile_tables(CARD_SYSTEM_RAW)
CASCADE_BLOCK_C1_WHEN_BOARD_HAS_C1 = 0 if ALLOW_C1_DROP_WHEN_BOARD_HAS_C1 else 1

SYMBOLS_COUNT = int(len(SYMBOL_ID))
LINE_NUM = int(PAYLINES.shape[0])
VALUE_MULTIPLIER_COUNT = int(len(VALUE_MULTIPLIER_RANGE))
RECORD_COLS = max(len(THRESHOLD_RECORD), SYMBOLS_COUNT * 2, VALUE_MULTIPLIER_COUNT, 140)
R_FG_FINAL_MULTI_BUCKET = 19
R_FG_SPIN_MULTI_HIT = 20
R_BG_SPIN_MULTI_HIT = 21
R_FG_INTERVAL_SPIN_CNT = 22
R_FG_INTERVAL_HIT_CNT = 23
RECORD_SIZE = (24, RECORD_COLS)

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
# Per paid Spin moments.  One triggered FG session is folded into the paid
# Spin's pay_total, so FG spins are not separate standard-deviation samples.
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
RA_FINAL_GOLD_COUNT_FG_LT10_0 = 65
RA_FINAL_GOLD_COUNT_FG_GE10_0 = 75
RA_FINAL_GOLD_COUNT_FG_GE20_0 = 85
RA_SPECIAL_TRIGGER_SPINS_BG = 95
RA_SPECIAL_TRIGGER_SPINS_FG = 96
RA_BG_TABLE0_SPINS = 97
RA_BG_TABLE0_HITS = 98
RA_BG_TABLE1_SPINS = 99
RA_BG_TABLE1_HITS = 100
RA_BG_TABLE2_SPINS = 101
RA_BG_TABLE2_HITS = 102
RA_COMBO_BG_TABLE0_1 = 103
RA_COMBO_BG_TABLE1_1 = 108
RA_COMBO_BG_TABLE2_1 = 113
RA_COMBO_FG_TABLE0_1 = 118
RA_COMBO_FG_TABLE1_1 = 123
RA_COMBO_FG_TABLE2_1 = 128

FG_FINAL_MULTI_BUCKET_LABELS = [
    "0",
    "1-10",
    "11-20",
    "21-30",
    "31-40",
    "41-50",
    "51-100",
    "100+",
]
PROFILE_NEWBIE_BG = 0
PROFILE_NEWBIE_FG = 1
PROFILE_NEWBIE_EXTRA_BG = 2
PROFILE_NEWBIE_EXTRA_FG = 3
PROFILE_OLDHAND_BG = 4
PROFILE_OLDHAND_FG = 5
PROFILE_OLDHAND_EXTRA_BG = 6
PROFILE_OLDHAND_EXTRA_FG = 7
PROFILE_WEIGHT_BF = 8
CARD_TYPE_RANGE = 0
CARD_TYPE_FREE_GAME = 1
RETRY_FAIL_NONE = 0
RETRY_FAIL_BG_RANGE = 1
RETRY_FAIL_BG_FREEGAME = 2
RETRY_FAIL_FG = 3
ACTIVE_PROFILE_BG = PROFILE_NEWBIE_BG if CARD_SYSTEM_IS_NEWBIE else PROFILE_OLDHAND_BG
ACTIVE_PROFILE_FG = PROFILE_NEWBIE_FG if CARD_SYSTEM_IS_NEWBIE else PROFILE_OLDHAND_FG


@njit(nogil=True)
def is_base_bet_mode(bet_mode):
    return bet_mode == MODE_NORMALBET or bet_mode == MODE_EXTRABET


@njit(nogil=True)
def get_bg_profile_idx(bet_mode):
    if bet_mode == MODE_EXTRABET:
        return PROFILE_NEWBIE_EXTRA_BG if CARD_SYSTEM_IS_NEWBIE else PROFILE_OLDHAND_EXTRA_BG
    return PROFILE_NEWBIE_BG if CARD_SYSTEM_IS_NEWBIE else PROFILE_OLDHAND_BG


@njit(nogil=True)
def get_fg_profile_idx(bet_mode):
    if bet_mode == MODE_EXTRABET:
        return PROFILE_NEWBIE_EXTRA_FG if CARD_SYSTEM_IS_NEWBIE else PROFILE_OLDHAND_EXTRA_FG
    return PROFILE_NEWBIE_FG if CARD_SYSTEM_IS_NEWBIE else PROFILE_OLDHAND_FG


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
        return FG_TRIGGER_BASE_SPINS + (scatter_count - 3) * FG_EXTRA_SPINS_PER_SCATTER
    if force_trigger == 1:
        return FG_TRIGGER_BASE_SPINS
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
def clear_1d(arr):
    for i in range(arr.shape[0]):
        arr[i] = 0


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
def get_fg_gold_count_bucket(fg_multiplier_sum):
    if fg_multiplier_sum < 10:
        return 0
    if fg_multiplier_sum < 20:
        return 1
    return 2


@njit(nogil=True)
def get_fg_final_multiplier_bucket(fg_multiplier_sum):
    if fg_multiplier_sum <= 0:
        return 0
    if fg_multiplier_sum <= 10:
        return 1
    if fg_multiplier_sum <= 20:
        return 2
    if fg_multiplier_sum <= 30:
        return 3
    if fg_multiplier_sum <= 40:
        return 4
    if fg_multiplier_sum <= 50:
        return 5
    if fg_multiplier_sum <= 100:
        return 6
    return 7


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
        visible_start_idx = stop_idx % reel_length
        next_above_idx[col] = (visible_start_idx - 1 + reel_length) % reel_length
        for row in range(DISPLAY_WINDOW_SIZE):
            symbol = ARR_REELS[table_id, (visible_start_idx + row) % reel_length, col]
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
def count_scoring_gold_mask(gold_mask):
    gold_count = 0
    for row in range(SCORE_ROW_OFFSET, DISPLAY_WINDOW_SIZE):
        for col in range(REEL_NUM):
            gold_count += gold_mask[row, col]
    return gold_count


@njit(nogil=True)
def assign_initial_multiplier(table_id, gold_mask, multi_mask, gold_pos):
    gold_count = collect_gold_positions(gold_mask, gold_pos)
    if gold_count == 0:
        return 0

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
    return 1 if special_idx >= 0 else 0


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
def mark_spin_multiplier_hits(gold_mask, multi_mask, spin_multiplier_seen):
    for row in range(DISPLAY_WINDOW_SIZE):
        for col in range(REEL_NUM):
            if gold_mask[row, col] != 1:
                continue
            multiplier_value = multi_mask[row, col]
            if multiplier_value <= 0:
                continue
            for idx in range(VALUE_MULTIPLIER_COUNT):
                if VALUE_MULTIPLIER_RANGE[idx] == multiplier_value:
                    spin_multiplier_seen[idx] = 1
                    break


@njit(nogil=True)
def add_spin_multiplier_hit_record(record_data, row_idx, spin_multiplier_seen):
    for idx in range(VALUE_MULTIPLIER_COUNT):
        record_data[row_idx, idx] += spin_multiplier_seen[idx]


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
    spin_multiplier_seen,
    reel_stop_idx,
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
    for col in range(REEL_NUM):
        reel_length = REELS_LEN[table_id, col]
        reel_stop_idx[col] = (next_above_idx[col] + 1) % reel_length
    copy_layout(board_initial, board)
    special_triggered = assign_initial_multiplier(table_id, gold_mask, multi_mask, gold_pos)
    pre_eliminate_gold_count = count_scoring_gold_mask(gold_mask)

    raw_pay = 0
    combo_idx = 0
    hit_any = 0
    multiplier_sum = fg_multiplier_sum
    gold_appear = 0
    gold_used = 0
    multi_appear = 0
    multi_used = 0

    clear_1d(spin_multiplier_seen)
    gold_appear, multi_appear = update_spin_flags(gold_mask, multi_mask, gold_appear, multi_appear)
    mark_spin_multiplier_hits(gold_mask, multi_mask, spin_multiplier_seen)

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
        mark_spin_multiplier_hits(gold_mask, multi_mask, spin_multiplier_seen)
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
        special_triggered,
        table_id,
        use_drop_a,
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
def print_bf_bg_win_trace(trace_idx, pay_bg, scatter_count, final_multiplier, combo_idx, board_initial, board_final, reel_stop_idx, table_id, use_drop_a):
    print("")
    print("=== BF BG Win Trace ===")
    print("trace_idx =", trace_idx)
    print("table_id =", table_id)
    print("use_drop_a =", use_drop_a)
    print("reel_stop_idx =", reel_stop_idx[0], reel_stop_idx[1], reel_stop_idx[2], reel_stop_idx[3], reel_stop_idx[4])
    print("pay_bg =", pay_bg)
    print("scatter_count =", scatter_count)
    print("final_multiplier =", final_multiplier)
    print("combo_idx =", combo_idx)
    print("initial_board")
    for row in range(DISPLAY_WINDOW_SIZE):
        print(
            board_initial[row, 0],
            board_initial[row, 1],
            board_initial[row, 2],
            board_initial[row, 3],
            board_initial[row, 4],
        )
    print("final_board")
    for row in range(DISPLAY_WINDOW_SIZE):
        print(
            board_final[row, 0],
            board_final[row, 1],
            board_final[row, 2],
            board_final[row, 3],
            board_final[row, 4],
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
def get_multiplier_range_bucket(score, coin_in):
    multi = score / coin_in
    target = THRESHOLD_RECORD.shape[0] - 1
    for idx in range(THRESHOLD_RECORD.shape[0]):
        if multi <= THRESHOLD_RECORD[idx]:
            target = idx
            break
    return target


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

    target = get_multiplier_range_bucket(score, coin_in)

    record_data[cnt_idx, target] += 1
    record_data[pay_idx, target] += score


@njit(nogil=True)
def log_round_multiplier_lines(record_data, pay_bg, pay_fg, pay_total, triggered_bg_fg, multiplier_line_coin_in):
    if triggered_bg_fg == 1:
        if pay_fg > 0:
            log_multi_line(record_data, OUTPUT_FG, pay_fg, multiplier_line_coin_in)
            log_multi_line(record_data, OUTPUT_OA, pay_fg, multiplier_line_coin_in)
        return

    log_multi_line(record_data, OUTPUT_BG, pay_bg, multiplier_line_coin_in)
    if pay_fg > 0:
        log_multi_line(record_data, OUTPUT_FG, pay_fg, multiplier_line_coin_in)
    log_multi_line(record_data, OUTPUT_OA, pay_total, multiplier_line_coin_in)


@njit(nogil=True)
def log_bg_table_hit(record_data, table_id, hit_any):
    if table_id == 0:
        record_data[R_ALL, RA_BG_TABLE0_SPINS] += 1
        if hit_any == 1:
            record_data[R_ALL, RA_BG_TABLE0_HITS] += 1
    elif table_id == 1:
        record_data[R_ALL, RA_BG_TABLE1_SPINS] += 1
        if hit_any == 1:
            record_data[R_ALL, RA_BG_TABLE1_HITS] += 1
    elif table_id == 2:
        record_data[R_ALL, RA_BG_TABLE2_SPINS] += 1
        if hit_any == 1:
            record_data[R_ALL, RA_BG_TABLE2_HITS] += 1


@njit(nogil=True)
def log_combo_table_count(record_data, scene_idx, table_id, combo_idx):
    if combo_idx <= 0:
        return
    bucket = combo_idx
    if bucket > 5:
        bucket = 5
    offset = bucket - 1

    if scene_idx == SCENE_BG:
        if table_id == 0:
            record_data[R_ALL, RA_COMBO_BG_TABLE0_1 + offset] += 1
        elif table_id == 1:
            record_data[R_ALL, RA_COMBO_BG_TABLE1_1 + offset] += 1
        elif table_id == 2:
            record_data[R_ALL, RA_COMBO_BG_TABLE2_1 + offset] += 1
    elif scene_idx == SCENE_FG:
        if table_id == 3:
            record_data[R_ALL, RA_COMBO_FG_TABLE0_1 + offset] += 1
        elif table_id == 4:
            record_data[R_ALL, RA_COMBO_FG_TABLE1_1 + offset] += 1
        elif table_id == 5:
            record_data[R_ALL, RA_COMBO_FG_TABLE2_1 + offset] += 1


@njit(nogil=True)
def apply_spin_log(
    record_data,
    scene_idx,
    fg_gold_count_bucket,
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
    special_triggered,
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
        if special_triggered == 1:
            record_data[R_ALL, RA_SPECIAL_TRIGGER_SPINS_BG] += 1
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
        if fg_gold_count_bucket == 0:
            record_data[R_ALL, RA_FINAL_GOLD_COUNT_FG_LT10_0 + min(final_gold_count, 9)] += 1
        elif fg_gold_count_bucket == 1:
            record_data[R_ALL, RA_FINAL_GOLD_COUNT_FG_GE10_0 + min(final_gold_count, 9)] += 1
        else:
            record_data[R_ALL, RA_FINAL_GOLD_COUNT_FG_GE20_0 + min(final_gold_count, 9)] += 1
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
        if special_triggered == 1:
            record_data[R_ALL, RA_SPECIAL_TRIGGER_SPINS_FG] += 1
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
    multiplier_line_coin_in,
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
    spin_multiplier_seen,
):
    pay_fg = 0
    fg_multiplier_sum = 0
    fg_spin_count = 0
    fg_hit_count = 0
    remaining_freespin = free_spins if free_spins < FG_SPIN_CAP else FG_SPIN_CAP
    reel_stop_idx = np.zeros(REEL_NUM, np.int64)

    while remaining_freespin > 0:
        fg_gold_count_bucket = get_fg_gold_count_bucket(fg_multiplier_sum)
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
            spin_multiplier_seen,
            reel_stop_idx,
        )
        pay_fg += fg_result[0]
        fg_spin_count += 1
        if fg_result[0] > 0:
            fg_hit_count += 1
        fg_multiplier_sum = fg_result[3]
        log_combo_table_count(record_data, SCENE_FG, fg_result[12], fg_result[5])
        apply_spin_log(
            record_data,
            SCENE_FG,
            fg_gold_count_bucket,
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
            fg_result[11],
            coin_in,
        )

        record_data[R_ALL, RA_FREE_SPINS] += 1
        add_spin_multiplier_hit_record(record_data, R_FG_SPIN_MULTI_HIT, spin_multiplier_seen)
        remaining_freespin -= 1

        if fg_result[1] >= 3:
            extra_spins = FG_TRIGGER_BASE_SPINS + (fg_result[1] - 3) * FG_EXTRA_SPINS_PER_SCATTER
            remaining_freespin = min(remaining_freespin + extra_spins, FG_SPIN_CAP)
            record_data[R_ALL, RA_RE_TRIGGER] += 1

    interval_idx = get_multiplier_range_bucket(pay_fg, multiplier_line_coin_in)
    record_data[R_FG_INTERVAL_SPIN_CNT, interval_idx] += fg_spin_count
    record_data[R_FG_INTERVAL_HIT_CNT, interval_idx] += fg_hit_count
    record_data[R_FG_FINAL_MULTI_BUCKET, get_fg_final_multiplier_bucket(fg_multiplier_sum)] += 1
    return pay_fg


@njit("int64[:, :](int64[:, :], int64, int64, int64, int64, int64)", nogil=True)
def simulator_chunk(record_data, total_round, bet_mode, bet_multi, coin_in, card_system_coin_in):
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
    spin_multiplier_seen = np.zeros(VALUE_MULTIPLIER_COUNT, np.int64)
    reel_stop_idx = np.zeros(REEL_NUM, np.int64)
    round_record = np.zeros(RECORD_SIZE, np.int64)
    bg_round_record = np.zeros(RECORD_SIZE, np.int64)
    fg_round_record = np.zeros(RECORD_SIZE, np.int64)
    scatter_history = np.zeros(CARD_RETRY_LIMIT, np.int64)
    board_history = np.zeros((CARD_RETRY_LIMIT, DISPLAY_WINDOW_SIZE, REEL_NUM), np.int64)
    bf_bg_win_trace_count = 0

    for _ in range(total_round):
        retry_count = 0
        normal_card_idx = -1
        fg_card_idx = -2
        buy_feature_card_idx = -1
        bg_freegame_triggered_once = 0

        bg_profile_idx = get_bg_profile_idx(bet_mode)
        fg_profile_idx = get_fg_profile_idx(bet_mode)

        if is_base_bet_mode(bet_mode):
            normal_card_idx = pick_card(bg_profile_idx) if CARD_SYSTEM_ENABLED else -1
        else:
            buy_feature_card_idx = pick_card(PROFILE_WEIGHT_BF) if CARD_SYSTEM_ENABLED else -1

        if is_base_bet_mode(bet_mode) and CARD_SYSTEM_ENABLED and normal_card_idx >= 0 and CARD_TYPES[bg_profile_idx, normal_card_idx] == CARD_TYPE_FREE_GAME:
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
                    spin_multiplier_seen,
                    reel_stop_idx,
                )
                pay_bg = bg_result[0]
                triggered_bg_fg = 1 if bg_result[1] >= 3 else 0
                free_spins = calc_free_spins(bg_result[1], 0)
                log_bg_table_hit(bg_round_record, bg_result[12], bg_result[2])
                log_combo_table_count(bg_round_record, SCENE_BG, bg_result[12], bg_result[5])

                apply_spin_log(
                    bg_round_record,
                    SCENE_BG,
                    -1,
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
                    bg_result[11],
                    coin_in,
                )
                add_spin_multiplier_hit_record(bg_round_record, R_BG_SPIN_MULTI_HIT, spin_multiplier_seen)

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
                    fg_card_idx = pick_card(fg_profile_idx)

                fg_retry_count = 0
                while True:
                    clear_2d(fg_round_record)
                    pay_fg = run_free_game_session(
                        fg_round_record,
                        free_spins,
                        bet_multi,
                        coin_in,
                        card_system_coin_in,
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
                        spin_multiplier_seen,
                    )
                    if is_card_match(fg_profile_idx, fg_card_idx, pay_fg, card_system_coin_in, 1):
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

            # One paid Spin is one sample.  If it triggers FG, pay_total is
            # BG + the complete FG session before the multiplier is recorded.
            pay_x = pay_total / coin_in
            round_record[R_ALL, RA_X_SUM] += int(pay_x * 1000000)
            round_record[R_ALL, RA_X_SQUARE] += int((pay_x * pay_x) * 1000000)

            log_round_multiplier_lines(round_record, pay_bg, pay_fg, pay_total, triggered_bg_fg, card_system_coin_in)

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

            if is_base_bet_mode(bet_mode):
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
                    spin_multiplier_seen,
                    reel_stop_idx,
                )
                pay_bg = bg_result[0]
                triggered_bg_fg = 1 if bg_result[1] >= 3 else 0
                free_spins = calc_free_spins(bg_result[1], 0)
                log_bg_table_hit(round_record, bg_result[12], bg_result[2])
                log_combo_table_count(round_record, SCENE_BG, bg_result[12], bg_result[5])

                apply_spin_log(
                    round_record,
                    SCENE_BG,
                    -1,
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
                    bg_result[11],
                    coin_in,
                )
                add_spin_multiplier_hit_record(round_record, R_BG_SPIN_MULTI_HIT, spin_multiplier_seen)

                if TRACE_RETRY_FAILURE and retry_count < CARD_RETRY_LIMIT:
                    scatter_history[retry_count] = bg_result[1]
                    copy_board_snapshot(board_history, retry_count, board_initial)

                if triggered_bg_fg == 1:
                    round_record[R_ALL, RA_TRIGGER_FREEGAME] += 1
                    round_record[R_ALL, RA_TRIGGER_FG_PAY_BG] += pay_bg

                if CARD_SYSTEM_ENABLED and normal_card_idx >= 0:
                    if CARD_TYPES[bg_profile_idx, normal_card_idx] == CARD_TYPE_FREE_GAME:
                        if triggered_bg_fg == 0:
                            accepted = 0
                            retry_fail_reason = RETRY_FAIL_BG_FREEGAME
                        else:
                            bg_freegame_triggered_once = 1
                            if fg_card_idx == -2:
                                fg_card_idx = pick_card(fg_profile_idx)
                            pay_fg = run_free_game_session(
                                round_record,
                                free_spins,
                                bet_multi,
                                coin_in,
                                card_system_coin_in,
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
                                spin_multiplier_seen,
                            )
                            if is_card_match(fg_profile_idx, fg_card_idx, pay_fg, card_system_coin_in, 1) is False:
                                accepted = 0
                                retry_fail_reason = RETRY_FAIL_FG
                    else:
                        if triggered_bg_fg == 1 or is_card_match(bg_profile_idx, normal_card_idx, pay_bg, card_system_coin_in, 0) is False:
                            accepted = 0
                            retry_fail_reason = RETRY_FAIL_BG_RANGE
                else:
                    if triggered_bg_fg == 1:
                        pay_fg = run_free_game_session(
                            round_record,
                            free_spins,
                            bet_multi,
                            coin_in,
                            card_system_coin_in,
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
                            spin_multiplier_seen,
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
                        spin_multiplier_seen,
                        reel_stop_idx,
                    )
                    if bf_result[1] >= 3:
                        break
                    bf_retry_count += 1
                    if bf_retry_count > 5000:
                        raise ValueError("Buy Feature reroll exceeded 5000 attempts; check BF trigger condition.")
                pay_bg = bf_result[0]
                free_spins = calc_free_spins(bf_result[1], 0)
                if TRACE_BF_BG_WIN and pay_bg > 0 and bf_bg_win_trace_count < TRACE_BF_BG_WIN_LIMIT:
                    bf_bg_win_trace_count += 1
                    print_bf_bg_win_trace(
                        bf_bg_win_trace_count,
                        pay_bg,
                        bf_result[1],
                        bf_result[4],
                        bf_result[5],
                        board_initial,
                        board,
                        reel_stop_idx,
                        bf_result[12],
                        bf_result[13],
                    )

                apply_spin_log(
                    round_record,
                    SCENE_BG,
                    -1,
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
                    bf_result[11],
                    coin_in,
                )
                add_spin_multiplier_hit_record(round_record, R_BG_SPIN_MULTI_HIT, spin_multiplier_seen)

                round_record[R_ALL, RA_TRIGGER_FREEGAME] += 1
                round_record[R_ALL, RA_TRIGGER_FG_PAY_BG] += pay_bg
                pay_fg = run_free_game_session(
                    round_record,
                    free_spins,
                    bet_multi,
                    coin_in,
                    card_system_coin_in,
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
                    spin_multiplier_seen,
                )

                if CARD_SYSTEM_ENABLED and buy_feature_card_idx >= 0:
                    pay_total = pay_bg + pay_fg
                    if is_card_match(PROFILE_WEIGHT_BF, buy_feature_card_idx, pay_total, card_system_coin_in, 1) is False:
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

        # One paid Spin is one sample.  If it triggers FG, pay_total is
        # BG + the complete FG session before the multiplier is recorded.
        pay_x = pay_total / coin_in
        round_record[R_ALL, RA_X_SUM] += int(pay_x * 1000000)
        round_record[R_ALL, RA_X_SQUARE] += int((pay_x * pay_x) * 1000000)

        log_round_multiplier_lines(round_record, pay_bg, pay_fg, pay_total, triggered_bg_fg, card_system_coin_in)

        merge_round_record(record_data, round_record)

    return record_data


# ===== Runtime Helpers =====


def calc_coin_in(bet_mode, bet_multi):
    if bet_mode == MODE_NORMALBET:
        return bet_multi * DEFAULT_COIN_IN * NORMALBET
    if bet_mode == MODE_EXTRABET:
        return bet_multi * DEFAULT_COIN_IN * EXTRABET
    if bet_mode == MODE_FEATUREBUY:
        return bet_multi * DEFAULT_COIN_IN * NORMALBET * FEATUREBUY
    raise ValueError(f"Unsupported bet mode: {bet_mode}")


def calc_card_system_coin_in(bet_mode, bet_multi):
    if bet_mode == MODE_EXTRABET or bet_mode == MODE_FEATUREBUY:
        return bet_multi * DEFAULT_COIN_IN * NORMALBET
    return calc_coin_in(bet_mode, bet_multi)


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
    card_system_coin_in = int(calc_card_system_coin_in(bet_mode, bet_multi))

    simulator_chunk(np.zeros(RECORD_SIZE, dtype=np.int64), 1, bet_mode, bet_multi, coin_in, card_system_coin_in)

    chunk_rounds = build_chunk_rounds(total_round, threads)
    start = time.perf_counter()
    if len(chunk_rounds) == 1:
        record_data = simulator_chunk(np.zeros(RECORD_SIZE, dtype=np.int64), chunk_rounds[0], bet_mode, bet_multi, coin_in, card_system_coin_in)
    else:
        with ThreadPoolExecutor(max_workers=len(chunk_rounds)) as executor:
            futures = [
                executor.submit(
                    simulator_chunk,
                    np.zeros(RECORD_SIZE, dtype=np.int64),
                    rounds,
                    bet_mode,
                    bet_multi,
                    coin_in,
                    card_system_coin_in,
                )
                for rounds in chunk_rounds
            ]
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


def build_gold_count_distribution_frame(record_data):
    def extract_distribution(start_idx):
        counts = np.asarray(record_data[R_ALL, start_idx : start_idx + 10], dtype=np.float64)
        total = counts.sum()
        ratio = counts / total if total > 0 else np.zeros(10, dtype=np.float64)
        average = float(np.dot(np.arange(10, dtype=np.float64), counts) / total) if total > 0 else 0.0
        return ratio, average

    bg_ratio, bg_average = extract_distribution(RA_FINAL_GOLD_COUNT_BG_0)
    fg_ratio, fg_average = extract_distribution(RA_FINAL_GOLD_COUNT_FG_LT10_0)
    fg10_ratio, fg10_average = extract_distribution(RA_FINAL_GOLD_COUNT_FG_GE10_0)
    fg20_ratio, fg20_average = extract_distribution(RA_FINAL_GOLD_COUNT_FG_GE20_0)

    rows = []
    for gold_count in range(10):
        rows.append(
            {
                "金框分布": gold_count,
                "BG": bg_ratio[gold_count],
                "FG": fg_ratio[gold_count],
                "FG10": fg10_ratio[gold_count],
                "FG20": fg20_ratio[gold_count],
            }
        )
    rows.append(
        {
            "金框分布": "平均數量",
            "BG": bg_average,
            "FG": fg_average,
            "FG10": fg10_average,
            "FG20": fg20_average,
        }
    )
    return pd.DataFrame(rows, columns=["金框分布", "BG", "FG", "FG10", "FG20"])


def build_combo_distribution_frame(record_data, total_round, fg_spins):
    table_specs = [
        ("BG_Symbol", RA_COMBO_BG_TABLE0_1),
        ("BG_Symbol (2)", RA_COMBO_BG_TABLE1_1),
        ("BG_Symbol (3)", RA_COMBO_BG_TABLE2_1),
        ("FG_Symbol", RA_COMBO_FG_TABLE0_1),
        ("FG_Symbol (2)", RA_COMBO_FG_TABLE1_1),
        ("FG_Symbol (3)", RA_COMBO_FG_TABLE2_1),
    ]
    combo_labels = ["Combo 1", "Combo 2", "Combo 3", "Combo 4", "Combo 5+"]
    rows = []
    bg_total_counts = [0, 0, 0, 0, 0]
    fg_total_counts = [0, 0, 0, 0, 0]
    for table_label, start_idx in table_specs:
        counts = [int(record_data[R_ALL, start_idx + offset]) for offset in range(5)]
        total_count = sum(counts)
        if table_label.startswith("BG_"):
            for idx, count in enumerate(counts):
                bg_total_counts[idx] += count
        else:
            for idx, count in enumerate(counts):
                fg_total_counts[idx] += count
        for combo_label, count in zip(combo_labels, counts):
            rows.append(
                {
                    "Table": table_label,
                    "Combo": combo_label,
                    "Count": count,
                    "Rate": (count / total_count) if total_count > 0 else 0.0,
                }
            )
    bg_total = sum(bg_total_counts)
    fg_total = sum(fg_total_counts)
    for combo_label, count in zip(combo_labels, bg_total_counts):
        rows.append(
            {
                "Table": "BG",
                "Combo": combo_label,
                "Count": count,
                "Rate": (count / bg_total) if bg_total > 0 else 0.0,
            }
        )
    for combo_label, count in zip(combo_labels, fg_total_counts):
        rows.append(
            {
                "Table": "FG",
                "Combo": combo_label,
                "Count": count,
                "Rate": (count / fg_total) if fg_total > 0 else 0.0,
            }
        )
    return pd.DataFrame(rows, columns=["Table", "Combo", "Count", "Rate"])


def build_bg_symbol_hit_frame(record_data):
    rows = []
    labels = ["BG_Symbol", "BG_Symbol (2)", "BG_Symbol (3)"]
    spin_indices = [RA_BG_TABLE0_SPINS, RA_BG_TABLE1_SPINS, RA_BG_TABLE2_SPINS]
    hit_indices = [RA_BG_TABLE0_HITS, RA_BG_TABLE1_HITS, RA_BG_TABLE2_HITS]
    for label, spin_idx, hit_idx in zip(labels, spin_indices, hit_indices):
        spin_count = int(record_data[R_ALL, spin_idx])
        hit_count = int(record_data[R_ALL, hit_idx])
        rows.append(
            {
                "BG_Symbol": label,
                "Spin_Count": spin_count,
                "Hit_Count": hit_count,
                "Hit_Rate": (hit_count / spin_count) if spin_count > 0 else 0.0,
            }
        )
    return pd.DataFrame(rows, columns=["BG_Symbol", "Spin_Count", "Hit_Count", "Hit_Rate"])


def build_fg_final_multiplier_bucket_frame(record_data):
    counts = np.asarray(record_data[R_FG_FINAL_MULTI_BUCKET, : len(FG_FINAL_MULTI_BUCKET_LABELS)], dtype=np.float64)
    total = counts.sum()
    rows = []
    for idx, label in enumerate(FG_FINAL_MULTI_BUCKET_LABELS):
        count = int(counts[idx])
        rows.append(
            {
                "FG_Final_Multiplier_Range": label,
                "Count": count,
                "Rate": (count / total) if total > 0 else 0.0,
            }
        )
    return pd.DataFrame(rows, columns=["FG_Final_Multiplier_Range", "Count", "Rate"])


def build_fg_spin_multiplier_hit_frame(record_data):
    fg_spins = int(record_data[R_ALL, RA_FREE_SPINS])
    rows = []
    for idx, multiplier_value in enumerate(VALUE_MULTIPLIER_RANGE):
        hit_count = int(record_data[R_FG_SPIN_MULTI_HIT, idx])
        rows.append(
            {
                "Multiplier": f"{int(multiplier_value)}x",
                "FG_Spin_Count": fg_spins,
                "Hit_Count": hit_count,
                "Hit_Rate": (hit_count / fg_spins) if fg_spins > 0 else 0.0,
            }
        )
    return pd.DataFrame(rows, columns=["Multiplier", "FG_Spin_Count", "Hit_Count", "Hit_Rate"])


def build_bg_spin_multiplier_hit_frame(record_data, total_round):
    bg_spins = int(total_round)
    rows = []
    for idx, multiplier_value in enumerate(VALUE_MULTIPLIER_RANGE):
        hit_count = int(record_data[R_BG_SPIN_MULTI_HIT, idx])
        rows.append(
            {
                "Multiplier": f"{int(multiplier_value)}x",
                "BG_Spin_Count": bg_spins,
                "Hit_Count": hit_count,
                "Hit_Rate": (hit_count / bg_spins) if bg_spins > 0 else 0.0,
            }
        )
    return pd.DataFrame(rows, columns=["Multiplier", "BG_Spin_Count", "Hit_Count", "Hit_Rate"])


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
    special_trigger_rate_bg = record_data_float[R_ALL, RA_SPECIAL_TRIGGER_SPINS_BG] / total_round if total_round > 0 else 0.0
    special_trigger_rate_fg = record_data_float[R_ALL, RA_SPECIAL_TRIGGER_SPINS_FG] / fg_spins if fg_spins > 0 else 0.0
    max_multiplier_bg = int(record_data[R_ALL, RA_MAX_MULTIPLIER_BG])
    max_multiplier_fg = int(record_data[R_ALL, RA_MAX_MULTIPLIER_FG])
    final_c1_present_bg = int(record_data[R_ALL, RA_FINAL_C1_PRESENT_BG])
    final_c1_present_fg = int(record_data[R_ALL, RA_FINAL_C1_PRESENT_FG])
    bet_mode_label = "Normal Bet"
    if bet_mode == MODE_EXTRABET:
        bet_mode_label = "Extra Bet"
    elif bet_mode == MODE_FEATUREBUY:
        bet_mode_label = "Feature Buy"
    multiplier_line_coin_in = int(calc_card_system_coin_in(bet_mode, bet_multi))

    base_rows = [
        ("game_id", GAME_ID, ""),
        ("version", CONFIG_VERSION, ""),
        ("bet_mode", bet_mode_label, ""),
        ("bet_multi", bet_multi, ""),
        ("coin_in", coin_in, ""),
        ("multiplier_line_basis", "normal_bet", ""),
        ("multiplier_line_coin_in", multiplier_line_coin_in, ""),
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
        ("card_system_profile", "extra_bet" if bet_mode == MODE_EXTRABET else ("newbie" if CARD_SYSTEM_IS_NEWBIE else "oldhand"), ""),
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
        ("special_trigger_rate_bg", f"{special_trigger_rate_bg:.6f}", ""),
        ("special_trigger_rate_fg", f"{special_trigger_rate_fg:.6f}", ""),
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
    df_gold_count = build_gold_count_distribution_frame(record_data)
    df_combo = build_combo_distribution_frame(record_data, total_round, fg_spins)
    df_bg_symbol_hit = build_bg_symbol_hit_frame(record_data)
    df_bg_spin_multiplier_hit = build_bg_spin_multiplier_hit_frame(record_data, total_round)
    df_fg_final_multiplier_bucket = build_fg_final_multiplier_bucket_frame(record_data)
    df_fg_spin_multiplier_hit = build_fg_spin_multiplier_hit_frame(record_data)
    fg_interval_spin_cnt = record_data_float[R_FG_INTERVAL_SPIN_CNT, : len(THRESHOLD_RECORD)]
    fg_interval_hit_cnt = record_data_float[R_FG_INTERVAL_HIT_CNT, : len(THRESHOLD_RECORD)]
    fg_interval_hit_rate = np.divide(
        fg_interval_hit_cnt,
        fg_interval_spin_cnt,
        out=np.zeros_like(fg_interval_hit_cnt),
        where=fg_interval_spin_cnt > 0,
    )
    df_multiplier = pd.DataFrame(
        {
            "Interval": format_threshold_labels(THRESHOLD_RECORD),
            "base_game_cnt": record_data_float[R_MULTIPLIER_RANGE_CNT_BG, : len(THRESHOLD_RECORD)],
            "base_game_pay": record_data_float[R_MULTIPLIER_RANGE_PAY_BG, : len(THRESHOLD_RECORD)],
            "free_game_cnt": record_data_float[R_MULTIPLIER_RANGE_CNT_FG, : len(THRESHOLD_RECORD)],
            "free_game_pay": record_data_float[R_MULTIPLIER_RANGE_PAY_FG, : len(THRESHOLD_RECORD)],
            "free_game_hit_rate": fg_interval_hit_rate,
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
        "fg_trigger_count": fg_trigger_count,
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
        "special_trigger_rate_bg": special_trigger_rate_bg,
        "special_trigger_rate_fg": special_trigger_rate_fg,
        "max_multiplier_bg": max_multiplier_bg,
        "max_multiplier_fg": max_multiplier_fg,
        "final_c1_present_bg": final_c1_present_bg,
        "final_c1_present_fg": final_c1_present_fg,
        "volatility_std": std,
    }
    return (
        df_base,
        df_hits,
        df_pay,
        df_eliminate,
        df_gold_count,
        df_combo,
        df_bg_symbol_hit,
        df_bg_spin_multiplier_hit,
        df_fg_final_multiplier_bucket,
        df_fg_spin_multiplier_hit,
        df_multiplier,
        summary,
    )


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
    version_text = str(version or "").strip()
    if not version_text:
        return ""
    return re.sub(r"[^0-9A-Za-z]+", "", version_text)


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


def format_bet_mode_label(bet_mode):
    if bet_mode == MODE_EXTRABET:
        return "Extra Bet"
    if bet_mode == MODE_FEATUREBUY:
        return "Feature Buy"
    return "Normal Bet"


def print_batch_summary(duration, summary, bet_mode):
    fg_trigger_count = int(round(float(summary.get("fg_trigger_count", 0))))
    print(f"* game_id: {GAME_ID}", flush=True)
    print(f"* version: {CONFIG_VERSION}", flush=True)
    print(f"* bet_mode: {format_bet_mode_label(bet_mode)}", flush=True)
    print(f"* duration: {format_elapsed_time(duration)}", flush=True)
    print(f"* rtp_total: {float(summary.get('rtp_total', 0.0)) * 100:.2f}%", flush=True)
    print(f"* rtp_bg: {float(summary.get('rtp_bg', 0.0)) * 100:.2f}%", flush=True)
    print(f"* rtp_fg: {float(summary.get('rtp_fg', 0.0)) * 100:.2f}%", flush=True)
    print(f"* hit_rate_bg: {float(summary.get('hit_rate_bg', 0.0)):.2f}", flush=True)
    print(f"* hit_rate_fg: {float(summary.get('hit_rate_fg', 0.0)):.2f}", flush=True)
    print(f"* fg_trigger_rate: {float(summary.get('fg_trigger_rate', 0.0)):.2f} ({fg_trigger_count} spins)", flush=True)
    print(f"* retrigger_rate: {float(summary.get('retrigger_rate', 0.0)):.2f}", flush=True)
    print(f"* avg_fg_multiplier: {float(summary.get('avg_fg_multiplier', 0.0)):.2f} x", flush=True)
    print(f"* avg_fg_spins: {float(summary.get('avg_fg_spins', 0.0)):.2f} spins", flush=True)
    print(f"* card_system: {'on' if CARD_SYSTEM_ENABLED else 'off'}", flush=True)


def output_report(
    df_base,
    df_hits,
    df_pay,
    df_eliminate,
    df_gold_count,
    df_combo,
    df_bg_symbol_hit,
    df_bg_spin_multiplier_hit,
    df_fg_final_multiplier_bucket,
    df_fg_spin_multiplier_hit,
    df_multiplier,
    summary,
    record_data,
    bet_mode,
    total_round,
):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    rounds_tag = format_rounds_tag(total_round)
    version_tag = format_version_tag(CONFIG_VERSION)
    rtp_tag = format_rtp_tag(summary.get("rtp_total"))
    show_profile_suffix = CARD_SYSTEM_ENABLED and bet_mode != MODE_FEATUREBUY
    profile_suffix = "_newbie" if show_profile_suffix and CARD_SYSTEM_IS_NEWBIE else ("_oldhand" if show_profile_suffix else "")
    card_suffix = "_card" if CARD_SYSTEM_ENABLED else ""
    filename_parts = [GAME_ID]
    if version_tag:
        filename_parts.append(version_tag)
    filename_parts.extend([timestamp, f"betmode{bet_mode}", rounds_tag])
    if CARD_SYSTEM_ENABLED:
        filename_parts.append(f"{rtp_tag}{profile_suffix}{card_suffix}")
    path = os.path.join(OUTPUT_DIR, f"{'_'.join(filename_parts)}.xlsx")
    # 下方欄寬、凍結窗格與儲存格格式使用 openpyxl API，固定引擎以避免
    # pandas 選到 xlsxwriter 時產生 Worksheet API 不相容。
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df_base.to_excel(writer, sheet_name="Base Info", index=False)
        df_gold_count.to_excel(writer, sheet_name="Gold Count", index=False)
        df_combo.to_excel(writer, sheet_name="Combo Dist", index=False)
        df_bg_symbol_hit.to_excel(writer, sheet_name="BG Symbol Hit", index=False)
        df_bg_spin_multiplier_hit.to_excel(writer, sheet_name="BG Spin Multi", index=False)
        df_fg_final_multiplier_bucket.to_excel(writer, sheet_name="FG Final Multi", index=False)
        df_fg_spin_multiplier_hit.to_excel(writer, sheet_name="FG Spin Multi", index=False)
        df_multiplier.to_excel(writer, sheet_name="Multiplier Line", index=False)
        df_hits.to_excel(writer, sheet_name="Hits")
        df_pay.to_excel(writer, sheet_name="Pay")
        df_eliminate.to_excel(writer, sheet_name="Eliminate")
        pd.DataFrame(record_data).to_excel(writer, sheet_name="Record Data", index=False)
        worksheet = writer.sheets["Gold Count"]
        worksheet.freeze_panes = "A2"
        worksheet.column_dimensions["A"].width = 12
        for col in ("B", "C", "D", "E"):
            worksheet.column_dimensions[col].width = 12
            for row in range(2, 12):
                worksheet[f"{col}{row}"].number_format = "0.00%"
            worksheet[f"{col}12"].number_format = "0.00"
        worksheet = writer.sheets["Multiplier Line"]
        hit_rate_col = df_multiplier.columns.get_loc("free_game_hit_rate") + 1
        for row in range(2, len(df_multiplier) + 2):
            worksheet.cell(row=row, column=hit_rate_col).number_format = "0.00%"
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
    spin_multiplier_seen = np.zeros(VALUE_MULTIPLIER_COUNT, np.int64)
    reel_stop_idx = np.zeros(REEL_NUM, np.int64)
    result = run_spin(
        SCENE_BG if is_base_bet_mode(bet_mode) else SCENE_BF,
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
        spin_multiplier_seen,
        reel_stop_idx,
    )
    print("Single spin result:")
    print(f"coin_in={coin_in}, pay={result[0]}, scatter={result[1]}, final_multiplier={result[4]}, cascades={result[5]}")


def run_all_combinations():
    total_jobs = len(BATCH_COMBINATIONS)
    for index, combo in enumerate(BATCH_COMBINATIONS, start=1):
        combo_env = os.environ.copy()
        combo_env["PYTHONUNBUFFERED"] = "1"
        combo_env["H026_CONFIG_FILE"] = combo["config_file"]
        combo_env["H026_BET_MODE"] = str(combo["bet_mode"])
        combo_env["H026_TOTAL_ROUNDS"] = str(combo["total_rounds"])
        combo_env["H026_CARD_SYSTEM_ENABLED"] = "true" if combo.get("card_system_enabled", True) else "false"
        combo_env["H026_CARD_SYSTEM_IS_NEWBIE"] = "true" if combo["card_system_is_newbie"] else "false"
        combo_env["H026_RUN_ALL_COMBINATIONS"] = "false"
        combo_env["H026_BATCH_CHILD"] = "1"

        print(
            f"\n=== Batch {index}/{total_jobs}: " f"config={combo['config_file']}, " f"bet_mode={combo['bet_mode']}, " f"total_rounds={combo['total_rounds']}, " f"card_system_enabled={combo.get('card_system_enabled', True)}, " f"card_system_is_newbie={combo['card_system_is_newbie']} ===",
            flush=True,
        )
        result = subprocess.run(
            [sys.executable, os.path.abspath(__file__)],
            check=True,
            env=combo_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.stdout:
            print(result.stdout.rstrip(), flush=True)
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr, flush=True)


def main():
    if RUN_ALL_COMBINATIONS and os.environ.get("H026_BATCH_CHILD") != "1":
        run_all_combinations()
        return

    if RUN_SINGLE_SPIN_DEBUG:
        run_single_spin_debug()
        return

    if TRACE_RETRY_FAILURE:
        print("TRACE_RETRY_FAILURE is on; simulation will run with a single thread.")

    record_data, duration, coin_in = run_simulation()
    (
        df_base,
        df_hits,
        df_pay,
        df_eliminate,
        df_gold_count,
        df_combo,
        df_bg_symbol_hit,
        df_bg_spin_multiplier_hit,
        df_fg_final_multiplier_bucket,
        df_fg_spin_multiplier_hit,
        df_multiplier,
        summary,
    ) = build_result_frames(
        record_data=record_data,
        total_round=TOTAL_ROUNDS,
        duration=duration,
        coin_in=coin_in,
        bet_mode=BET_MODE,
        bet_multi=BET_MULTI,
        threads=THREADS,
    )
    print_console_result(df_base, df_hits, df_pay, df_eliminate)
    print_batch_summary(duration, summary, BET_MODE)

    if OUTPUT_REPORT:
        report_path = output_report(
            df_base,
            df_hits,
            df_pay,
            df_eliminate,
            df_gold_count,
            df_combo,
            df_bg_symbol_hit,
            df_bg_spin_multiplier_hit,
            df_fg_final_multiplier_bucket,
            df_fg_spin_multiplier_hit,
            df_multiplier,
            summary,
            record_data,
            BET_MODE,
            TOTAL_ROUNDS,
        )
        print(f"\nReport: {report_path}")


if __name__ == "__main__":
    main()
