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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)


# ===== User Settings =====

# Single-run settings. Used when RUN_ALL_COMBINATIONS = False.
CONFIG_FILE = "config_92.js"
TOTAL_ROUNDS = 10**7
BET_MULTI = 1
BET_MODE = 0  # 0 Normal, 1 Extra, 2 Feature Buy, 3 Super Feature Buy
CARD_SYSTEM_ENABLED = True  # True: use card system when config supports it; False: force it off.
CARD_SYSTEM_IS_NEWBIE = False  # True: Newbie, False: Oldhand
PARAMETER_TABLE = "AUTO"  # AUTO is official; A/B are diagnostic overrides only.

# Batch runs. Edit this list directly when you want to run a custom set once.
# A/B is selected by each Card System card, so every official run uses AUTO.
# Newbie only has Normal / Extra sections; Feature Buy / Super Feature use Oldhand.
RUN_ALL_COMBINATIONS = True
BATCH_RUNS = [
    # config_92: Newbie NB / EB
    {"config_file": "config_92.js", "parameter_table": "AUTO", "bet_mode": 0, "total_rounds": 10**6, "card_system_enabled": True, "card_system_is_newbie": False},
    # # config_92: Newbie NB / EB
    # {"config_file": "config_92.js", "parameter_table": "AUTO", "bet_mode": 0, "total_rounds": 10**9, "card_system_enabled": True, "card_system_is_newbie": True},
    # {"config_file": "config_92.js", "parameter_table": "AUTO", "bet_mode": 1, "total_rounds": 10**9, "card_system_enabled": True, "card_system_is_newbie": True},
    # # config_92: Oldhand NB / EB / BF / SF
    # {"config_file": "config_92.js", "parameter_table": "AUTO", "bet_mode": 0, "total_rounds": 10**9, "card_system_enabled": True, "card_system_is_newbie": False},
    # {"config_file": "config_92.js", "parameter_table": "AUTO", "bet_mode": 1, "total_rounds": 10**9, "card_system_enabled": True, "card_system_is_newbie": False},
    # {"config_file": "config_92.js", "parameter_table": "AUTO", "bet_mode": 2, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    # {"config_file": "config_92.js", "parameter_table": "AUTO", "bet_mode": 3, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    # # config_94: Newbie NB / EB
    # {"config_file": "config_94.js", "parameter_table": "AUTO", "bet_mode": 0, "total_rounds": 10**9, "card_system_enabled": True, "card_system_is_newbie": True},
    # {"config_file": "config_94.js", "parameter_table": "AUTO", "bet_mode": 1, "total_rounds": 10**9, "card_system_enabled": True, "card_system_is_newbie": True},
    # # config_94: Oldhand NB / EB / BF / SF
    # {"config_file": "config_94.js", "parameter_table": "AUTO", "bet_mode": 0, "total_rounds": 10**9, "card_system_enabled": True, "card_system_is_newbie": False},
    # {"config_file": "config_94.js", "parameter_table": "AUTO", "bet_mode": 1, "total_rounds": 10**9, "card_system_enabled": True, "card_system_is_newbie": False},
    # {"config_file": "config_94.js", "parameter_table": "AUTO", "bet_mode": 2, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    # {"config_file": "config_94.js", "parameter_table": "AUTO", "bet_mode": 3, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
]

OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = True
SHOW_CONSOLE_DETAIL = True
RUN_SINGLE_SPIN_DEBUG = False
DEBUG_ROUNDS = 1


def parse_env_bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    value = value.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true/false, got {value!r}")


CONFIG_FILE = os.environ.get("H998_CONFIG_FILE", CONFIG_FILE)


def resolve_base_dir():
    override = os.environ.get("H998_BASE_DIR")
    cwd = Path.cwd().resolve()
    folder_names = ("H998_糖果狂歡 2500 (未完成)", "H998_糖果狂歡 2500")
    candidates = []
    if override:
        candidates.append(Path(override).expanduser())
    candidates.append(cwd)
    for parent in (cwd, *cwd.parents):
        for folder_name in folder_names:
            candidates.append(parent / "Project_AI" / "Slots" / folder_name)
            candidates.append(parent / "Slots" / folder_name)
    file_value = globals().get("__file__")
    if file_value:
        file_dir = Path(file_value).resolve().parent
        candidates.append(file_dir)
        for parent in (file_dir, *file_dir.parents):
            for folder_name in folder_names:
                candidates.append(parent / "Project_AI" / "Slots" / folder_name)

    checked = []
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in checked:
            continue
        checked.append(candidate)
        config_path = candidate / CONFIG_FILE
        if not config_path.is_file():
            continue
        try:
            header = config_path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        if "H998_BOX_DATA" in header or '"parsheet_id": "H9981"' in header:
            return candidate
    raise FileNotFoundError(f"Cannot locate H998 base directory containing a valid {CONFIG_FILE}. " "Set H998_BASE_DIR to the H998 project folder when running outside the workspace.")


BASE_DIR = resolve_base_dir()
OUTPUT_DIR = BASE_DIR / "Record"
CONFIG_PATH = BASE_DIR / CONFIG_FILE
SIMULATOR_PATH = BASE_DIR / "Simulator.py"
TOTAL_ROUNDS = int(os.environ.get("H998_TOTAL_ROUNDS", TOTAL_ROUNDS))
BET_MULTI = int(os.environ.get("H998_BET_MULTI", BET_MULTI))
BET_MODE = int(os.environ.get("H998_BET_MODE", BET_MODE))
CARD_SYSTEM_ENABLED = parse_env_bool("H998_CARD_SYSTEM_ENABLED", CARD_SYSTEM_ENABLED)
CARD_SYSTEM_IS_NEWBIE = parse_env_bool("H998_CARD_SYSTEM_IS_NEWBIE", CARD_SYSTEM_IS_NEWBIE)
PARAMETER_TABLE = os.environ.get("H998_PARAMETER_TABLE", PARAMETER_TABLE).strip().upper()
if PARAMETER_TABLE not in {"AUTO", "A", "B"}:
    raise ValueError(f"H998_PARAMETER_TABLE must be AUTO, A, or B; got {PARAMETER_TABLE!r}")
PARAMETER_TABLE_OVERRIDE = -1 if PARAMETER_TABLE == "AUTO" else 0 if PARAMETER_TABLE == "A" else 1
RUN_ALL_COMBINATIONS = parse_env_bool("H998_RUN_ALL_COMBINATIONS", RUN_ALL_COMBINATIONS)
BATCH_COMBINATIONS = list(BATCH_RUNS)

THREADS = int(os.environ.get("H998_THREADS", max(1, min(8, os.cpu_count() or 1))))
OUTPUT_REPORT = parse_env_bool("H998_OUTPUT_REPORT", OUTPUT_REPORT)
SHOW_CONSOLE_SUMMARY = parse_env_bool("H998_SHOW_CONSOLE_SUMMARY", SHOW_CONSOLE_SUMMARY)
SHOW_CONSOLE_DETAIL = parse_env_bool("H998_SHOW_CONSOLE_DETAIL", SHOW_CONSOLE_DETAIL)
RUN_SINGLE_SPIN_DEBUG = parse_env_bool("H998_RUN_SINGLE_SPIN_DEBUG", RUN_SINGLE_SPIN_DEBUG)

THRESHOLD_RECORD = np.asarray(
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


def _load_config(path):
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    return json.loads(raw[raw.find("{") : raw.rfind("}") + 1])


CFG = _load_config(CONFIG_PATH)
GAME_ID = str(CFG["game_id"])
PARSHEET_ID = str(CFG["parsheet_id"])
GAME_NAME = str(CFG["display_name"])
GAME_VERSION = str(CFG["game_version"])
CARD_SYSTEM_RAW = CFG.get("card_system", {})
CARD_SYSTEM_ENABLED = CARD_SYSTEM_ENABLED and bool(CARD_SYSTEM_RAW.get("enabled", False))

CARD_TYPE_RANGE = 0
CARD_TYPE_FREE_GAME = 1
CARD_PROFILE_NEWBIE_NORMAL_BG = 0
CARD_PROFILE_NEWBIE_NORMAL_FG = 1
CARD_PROFILE_NEWBIE_EXTRA_BG = 2
CARD_PROFILE_NEWBIE_EXTRA_FG = 3
CARD_PROFILE_OLDHAND_NORMAL_BG = 4
CARD_PROFILE_OLDHAND_NORMAL_FG = 5
CARD_PROFILE_OLDHAND_EXTRA_BG = 6
CARD_PROFILE_OLDHAND_EXTRA_FG = 7
CARD_PROFILE_BUY_FEATURE = 8
CARD_PROFILE_SUPER_FEATURE = 9


def _card_list(player, mode, segment):
    return list(CARD_SYSTEM_RAW.get(player, {}).get(mode, {}).get(segment, []))


CARD_PROFILE_LISTS = [
    _card_list("newbie", "normal_bet", "weight_bg"),
    _card_list("newbie", "normal_bet", "weight_fg"),
    _card_list("newbie", "extra_bet", "weight_bg"),
    _card_list("newbie", "extra_bet", "weight_fg"),
    _card_list("oldhand", "normal_bet", "weight_bg"),
    _card_list("oldhand", "normal_bet", "weight_fg"),
    _card_list("oldhand", "extra_bet", "weight_bg"),
    _card_list("oldhand", "extra_bet", "weight_fg"),
    _card_list("oldhand", "buy_feature", "weight_fg"),
    _card_list("oldhand", "super_feature", "weight_fg"),
]
MAX_CARDS = max(1, max((len(cards) for cards in CARD_PROFILE_LISTS), default=0))
CARD_TYPES = np.full((len(CARD_PROFILE_LISTS), MAX_CARDS), -1, dtype=np.int64)
CARD_MIN = np.zeros((len(CARD_PROFILE_LISTS), MAX_CARDS), dtype=np.float64)
CARD_MAX = np.zeros((len(CARD_PROFILE_LISTS), MAX_CARDS), dtype=np.float64)
CARD_PARAMETER = np.zeros((len(CARD_PROFILE_LISTS), MAX_CARDS), dtype=np.int64)
CARD_WEIGHT_CUM = np.zeros((len(CARD_PROFILE_LISTS), MAX_CARDS), dtype=np.int64)
CARD_COUNTS = np.zeros(len(CARD_PROFILE_LISTS), dtype=np.int64)
for profile_idx, cards in enumerate(CARD_PROFILE_LISTS):
    running_weight = 0
    for card_idx, card in enumerate(cards):
        running_weight += max(0, int(card.get("weight", 0)))
        CARD_TYPES[profile_idx, card_idx] = CARD_TYPE_FREE_GAME if card.get("type") == "free_game" else CARD_TYPE_RANGE
        CARD_MIN[profile_idx, card_idx] = float(card.get("min", 0.0))
        CARD_MAX[profile_idx, card_idx] = float(card.get("max", 0.0))
        CARD_PARAMETER[profile_idx, card_idx] = 1 if str(card.get("table", "A")).strip().upper() == "B" else 0
        CARD_WEIGHT_CUM[profile_idx, card_idx] = running_weight
    CARD_COUNTS[profile_idx] = len(cards)

MODE_NORMALBET = int(CFG["mode_normalbet"])
MODE_EXTRABET = int(CFG["mode_extrabet"])
MODE_FEATUREBUY = int(CFG["mode_featurebuy"])
MODE_SUPERFEATUREBUY = int(CFG["mode_superfeaturebuy"])
SUPPORTED_BET_MODES = (MODE_NORMALBET, MODE_EXTRABET, MODE_FEATUREBUY, MODE_SUPERFEATUREBUY)
MODE_NAMES = {0: "Normal Bet", 1: "Extra Bet", 2: "Feature Buy", 3: "Super Feature Buy"}

WINDOW_SIZE = int(CFG["window_size"])
REEL_NUM = int(CFG["reel_num"])
DEFAULT_COIN_IN = int(CFG["default_coin_in"])
BET_FACTORS = np.asarray(
    [CFG["normalbet"], CFG["extrabet"], CFG["featurebuy"], CFG["superfeaturebuy"]],
    dtype=np.float64,
)
MAX_FREE_SPINS = int(CFG["max_spin_free_game"])
RETRIGGER_LOW = int(CFG["retrigger_free_spins_low"])
RETRIGGER_HIGH = int(CFG["retrigger_free_spins_high"])

ARR_REELS = np.asarray(CFG["arr_reels"], dtype=np.int64)
ARR_REELS_WEIGHT_CUM = np.asarray(CFG["arr_reels_weight_cum"], dtype=np.int64)
REELS_LEN = np.asarray(CFG["reels_len"], dtype=np.int64)
PAY_TABLE = np.asarray(CFG["pay_table"], dtype=np.int64)
SYMBOL_STR = {int(key): value for key, value in CFG["symbol_str"].items()}
SYMBOL_COUNT = len(SYMBOL_STR)
SYMBOLS_SCORE = np.asarray(CFG["symbols_score"], dtype=np.int64)
VALUE_MULTIPLIER = np.asarray(CFG["value_multiplier"], dtype=np.int64)
SF_GUARANTEED_MULTIPLIER = int(CFG["super_feature_guaranteed_multiplier"])

PARAMETER_NAMES = ("A", "B")
PARAMETER_BLOCKS = [CFG["parameter_blocks"][name] for name in PARAMETER_NAMES]
PARAM_WEIGHT_TABLE_NORMAL = np.asarray(
    [block["table_weights"]["normal"] for block in PARAMETER_BLOCKS],
    dtype=np.int64,
)
PARAM_WEIGHT_TABLE_EXTRA = np.asarray(
    [block["table_weights"]["extrabet"] for block in PARAMETER_BLOCKS],
    dtype=np.int64,
)


def _parameter_mix(block, mode):
    active = [item for item in block["free_spin_mix"] if int(item["weights"][mode]) > 0]
    if len(active) != 1:
        raise ValueError(f"Parameter block {block['name']}: expected one active {mode} free-spin mix")
    return int(active[0]["low"]), int(active[0]["high"])


PARAM_INITIAL_LOW = np.asarray(
    [[_parameter_mix(block, mode)[0] for mode in ("normal", "featurebuy", "superfeaturebuy")] for block in PARAMETER_BLOCKS],
    dtype=np.int64,
)
PARAM_INITIAL_HIGH = np.asarray(
    [[_parameter_mix(block, mode)[1] for mode in ("normal", "featurebuy", "superfeaturebuy")] for block in PARAMETER_BLOCKS],
    dtype=np.int64,
)
PARAM_MULTI_WEIGHTS = np.asarray(
    [[block["multiplier_weights"][source] for source in block["multiplier_sources"]] for block in PARAMETER_BLOCKS],
    dtype=np.int64,
)

C1 = next(sid for sid, code in SYMBOL_STR.items() if code == "C1")
C2 = next(sid for sid, code in SYMBOL_STR.items() if code == "C2")

S_TOTAL_WIN = 0
S_BG_PAY = 1
S_SCATTER_PAY = 2
S_FG_PAY = 3
S_BG_HITS = 4
S_FG_HITS = 5
S_FG_TRIGGER = 6
S_RETRIGGER = 7
S_FREE_SPINS = 8
S_MAX_WIN = 9
S_X_SUM = 10
S_X_SQUARE = 11
S_BG_CASCADES = 12
S_FG_CASCADES = 13
S_FG_MULTI_SUM = 14
S_FG_MULTI_MAX = 15
S_RETRY_TOTAL = 16
S_RETRY_LIMIT_EXCEEDED = 17
STAT_COUNT = 18


def _validate_settings():
    if BET_MODE not in SUPPORTED_BET_MODES:
        raise ValueError(f"Unsupported H998 bet mode {BET_MODE}; valid modes: 0, 1, 2, 3")
    if TOTAL_ROUNDS <= 0:
        raise ValueError("TOTAL_ROUNDS must be positive")
    if BET_MULTI <= 0:
        raise ValueError("BET_MULTI must be positive")
    if THREADS <= 0:
        raise ValueError("THREADS must be positive")


@njit(nogil=True)
def _weighted_index(weights):
    total = 0
    for value in weights:
        if value > 0:
            total += value
    if total <= 0:
        return 0
    pick = np.random.randint(0, total)
    running = 0
    for idx in range(weights.shape[0]):
        if weights[idx] > 0:
            running += weights[idx]
            if pick < running:
                return idx
    return weights.shape[0] - 1


@njit(nogil=True)
def _weighted_cumulative_index(cumulative):
    total = cumulative[-1]
    if total <= 0:
        return 0
    pick = np.random.randint(0, total)
    for idx in range(cumulative.shape[0]):
        if pick < cumulative[idx]:
            return idx
    return cumulative.shape[0] - 1


@njit(nogil=True)
def _pick_card(profile_idx):
    card_count = CARD_COUNTS[profile_idx]
    if card_count <= 0:
        return -1
    total = CARD_WEIGHT_CUM[profile_idx, card_count - 1]
    if total <= 0:
        return -1
    pick = np.random.randint(0, total)
    for card_idx in range(card_count):
        if pick < CARD_WEIGHT_CUM[profile_idx, card_idx]:
            return card_idx
    return card_count - 1


@njit(nogil=True)
def _is_card_match(profile_idx, card_idx, score, card_coin_in, triggered_free_game):
    if card_idx < 0:
        return True
    if CARD_TYPES[profile_idx, card_idx] == CARD_TYPE_FREE_GAME:
        return triggered_free_game == 1
    multiplier = score / card_coin_in
    return multiplier > CARD_MIN[profile_idx, card_idx] and multiplier <= CARD_MAX[profile_idx, card_idx]


@njit(nogil=True)
def _card_profiles(mode):
    if mode == MODE_FEATUREBUY:
        return -1, -1, CARD_PROFILE_BUY_FEATURE
    if mode == MODE_SUPERFEATUREBUY:
        return -1, -1, CARD_PROFILE_SUPER_FEATURE
    if CARD_SYSTEM_IS_NEWBIE:
        if mode == MODE_EXTRABET:
            return CARD_PROFILE_NEWBIE_EXTRA_BG, CARD_PROFILE_NEWBIE_EXTRA_FG, -1
        return CARD_PROFILE_NEWBIE_NORMAL_BG, CARD_PROFILE_NEWBIE_NORMAL_FG, -1
    if mode == MODE_EXTRABET:
        return CARD_PROFILE_OLDHAND_EXTRA_BG, CARD_PROFILE_OLDHAND_EXTRA_FG, -1
    return CARD_PROFILE_OLDHAND_NORMAL_BG, CARD_PROFILE_OLDHAND_NORMAL_FG, -1


@njit(nogil=True)
def _threshold_index(multiplier):
    for idx in range(THRESHOLD_RECORD.shape[0]):
        if multiplier <= THRESHOLD_RECORD[idx]:
            return idx
    return THRESHOLD_RECORD.shape[0] - 1


@njit(nogil=True)
def _generate_board(table_id):
    board = np.zeros((WINDOW_SIZE, REEL_NUM), dtype=np.int64)
    stops = np.zeros(REEL_NUM, dtype=np.int64)
    for reel in range(REEL_NUM):
        stops[reel] = _weighted_cumulative_index(ARR_REELS_WEIGHT_CUM[table_id, :, reel])
        reel_len = REELS_LEN[table_id, reel]
        for row in range(WINDOW_SIZE):
            board[row, reel] = ARR_REELS[table_id, (stops[reel] + row) % reel_len, reel]
    return board, stops


@njit(nogil=True)
def _pay_bin(count):
    if count >= 12:
        return 2
    if count >= 10:
        return 1
    if count >= 8:
        return 0
    return -1


@njit(nogil=True)
def _cascade(table_id, board, stops, multiplier, scene, collect, hits, pays, eliminates):
    total_pay = 0.0
    cascade_count = 0
    remove_counts = np.zeros(REEL_NUM, dtype=np.int64)
    while True:
        counts = np.zeros(SYMBOL_COUNT, dtype=np.int64)
        for row in range(WINDOW_SIZE):
            for reel in range(REEL_NUM):
                symbol = board[row, reel]
                if 0 <= symbol < SYMBOL_COUNT:
                    counts[symbol] += 1

        remove_symbols = np.zeros(SYMBOL_COUNT, dtype=np.int64)
        any_win = False
        for idx in range(SYMBOLS_SCORE.shape[0]):
            symbol = SYMBOLS_SCORE[idx]
            pay_bin = _pay_bin(counts[symbol])
            if pay_bin >= 0:
                pay = PAY_TABLE[symbol, pay_bin + 3] * multiplier
                if pay > 0:
                    any_win = True
                    remove_symbols[symbol] = 1
                    total_pay += pay
                    if collect:
                        hits[scene, symbol, pay_bin] += 1
                        pays[scene, symbol, pay_bin] += pay
                        eliminates[scene, symbol, pay_bin] += counts[symbol]
        if not any_win:
            break

        cascade_count += 1
        for reel in range(REEL_NUM):
            kept = np.empty(WINDOW_SIZE, dtype=np.int64)
            kept_count = 0
            for row in range(WINDOW_SIZE):
                symbol = board[row, reel]
                if remove_symbols[symbol] == 0:
                    kept[kept_count] = symbol
                    kept_count += 1
            missing = WINDOW_SIZE - kept_count
            for pos in range(kept_count - 1, -1, -1):
                board[pos + missing, reel] = kept[pos]
            for row in range(missing - 1, -1, -1):
                while True:
                    remove_counts[reel] += 1
                    reel_len = REELS_LEN[table_id, reel]
                    source = (stops[reel] - (remove_counts[reel] % reel_len)) % reel_len
                    symbol = ARR_REELS[table_id, source, reel]
                    duplicate = False
                    if symbol == C1 or symbol == C2:
                        for check_row in range(row + 1, WINDOW_SIZE):
                            if board[check_row, reel] == symbol:
                                duplicate = True
                                break
                    if not duplicate:
                        board[row, reel] = symbol
                        break
    return total_pay, cascade_count


@njit(nogil=True)
def _count_symbol(board, symbol):
    count = 0
    for row in range(WINDOW_SIZE):
        for reel in range(REEL_NUM):
            if board[row, reel] == symbol:
                count += 1
    return count


@njit(nogil=True)
def _base_table(mode, parameter_idx):
    if mode == MODE_NORMALBET:
        return _weighted_index(PARAM_WEIGHT_TABLE_NORMAL[parameter_idx])
    if mode == MODE_EXTRABET:
        return 4 + _weighted_index(PARAM_WEIGHT_TABLE_EXTRA[parameter_idx])
    return 3


@njit(nogil=True)
def _fg_tables_and_profile(mode):
    if mode == MODE_FEATUREBUY:
        return 9, 10, 2
    if mode == MODE_SUPERFEATUREBUY:
        return 11, 12, 4
    return 7, 8, 0


@njit(nogil=True)
def _draw_multiplier(parameter_idx, profile_row, count, guaranteed_multiplier):
    if count <= 0 and guaranteed_multiplier <= 0:
        return 1
    total = guaranteed_multiplier if guaranteed_multiplier > 0 else 0
    random_count = count - 1 if guaranteed_multiplier > 0 and count > 0 else count
    weights = PARAM_MULTI_WEIGHTS[parameter_idx, profile_row]
    for _ in range(random_count):
        total += VALUE_MULTIPLIER[_weighted_index(weights)]
    return total


@njit(nogil=True)
def _simulate_chunk(rounds, mode, bet_multi):
    stats = np.zeros(STAT_COUNT, dtype=np.float64)
    hits = np.zeros((2, SYMBOL_COUNT, 3), dtype=np.float64)
    pays = np.zeros((2, SYMBOL_COUNT, 3), dtype=np.float64)
    eliminates = np.zeros((2, SYMBOL_COUNT, 3), dtype=np.float64)
    multiplier_line = np.zeros((3, THRESHOLD_RECORD.shape[0]), dtype=np.float64)
    coin_in = DEFAULT_COIN_IN * BET_FACTORS[mode] * bet_multi
    card_coin_in = DEFAULT_COIN_IN * BET_FACTORS[MODE_NORMALBET] * bet_multi
    bg_profile, fg_profile, package_profile = _card_profiles(mode)
    accepted_rounds = 0
    retry_count = 0
    bg_card_idx = -1
    fg_card_idx = -1
    package_card_idx = -1
    bg_parameter_idx = 0
    fg_parameter_idx = 0

    while accepted_rounds < rounds:
        if retry_count == 0:
            bg_card_idx = -1
            fg_card_idx = -1
            package_card_idx = -1
            bg_parameter_idx = 0
            fg_parameter_idx = 0
            if CARD_SYSTEM_ENABLED:
                if package_profile >= 0:
                    package_card_idx = _pick_card(package_profile)
                    if package_card_idx >= 0:
                        fg_parameter_idx = CARD_PARAMETER[package_profile, package_card_idx]
                else:
                    bg_card_idx = _pick_card(bg_profile)
                    if bg_card_idx >= 0:
                        bg_parameter_idx = CARD_PARAMETER[bg_profile, bg_card_idx]
                    if bg_card_idx >= 0 and CARD_TYPES[bg_profile, bg_card_idx] == CARD_TYPE_FREE_GAME:
                        fg_card_idx = _pick_card(fg_profile)
                        if fg_card_idx >= 0:
                            fg_parameter_idx = CARD_PARAMETER[fg_profile, fg_card_idx]
            if PARAMETER_TABLE_OVERRIDE >= 0:
                bg_parameter_idx = PARAMETER_TABLE_OVERRIDE
                fg_parameter_idx = PARAMETER_TABLE_OVERRIDE

        round_hits = np.zeros((2, SYMBOL_COUNT, 3), dtype=np.float64)
        round_pays = np.zeros((2, SYMBOL_COUNT, 3), dtype=np.float64)
        round_eliminates = np.zeros((2, SYMBOL_COUNT, 3), dtype=np.float64)
        table_id = _base_table(mode, bg_parameter_idx)
        board, stops = _generate_board(table_id)
        bg_regular, bg_cascades = _cascade(table_id, board, stops, bet_multi, 0, True, round_hits, round_pays, round_eliminates)
        scatter_count = _count_symbol(board, C1)
        scatter_pay = 0.0
        if 4 <= scatter_count <= 6:
            scatter_pay = PAY_TABLE[C1, scatter_count - 4] * bet_multi

        bg_pay = bg_regular + scatter_pay
        fg_pay = 0.0
        fg_spins = 0
        retriggers = 0
        fg_hit_spins = 0
        fg_cascades = 0
        fg_multiplier_sum = 0
        fg_multiplier_max = 0

        if scatter_pay > 0:
            low_table, high_table, profile = _fg_tables_and_profile(mode)
            mix_mode = 1 if mode == MODE_FEATUREBUY else 2 if mode == MODE_SUPERFEATUREBUY else 0
            low_total = PARAM_INITIAL_LOW[fg_parameter_idx, mix_mode]
            high_total = PARAM_INITIAL_HIGH[fg_parameter_idx, mix_mode]
            sf_guaranteed_spin = -1
            if mode == MODE_SUPERFEATUREBUY:
                sf_guaranteed_spin = np.random.randint(0, low_total + high_total)
            sf_guaranteed_count = 0
            low_done = 0
            high_done = 0
            while high_done < high_total or low_done < low_total:
                high_remaining = high_total - high_done
                low_remaining = low_total - low_done
                remaining = high_remaining + low_remaining
                is_high = high_remaining > 0 and (low_remaining <= 0 or np.random.randint(0, remaining) < high_remaining)
                if is_high:
                    fg_table = high_table
                    high_done += 1
                else:
                    fg_table = low_table
                    low_done += 1

                fg_board, fg_stops = _generate_board(fg_table)
                preview = fg_board.copy()
                dummy_hits = np.zeros((2, SYMBOL_COUNT, 3), dtype=np.float64)
                dummy_pays = np.zeros((2, SYMBOL_COUNT, 3), dtype=np.float64)
                dummy_eliminates = np.zeros((2, SYMBOL_COUNT, 3), dtype=np.float64)
                _cascade(fg_table, preview, fg_stops, 1, 1, False, dummy_hits, dummy_pays, dummy_eliminates)

                final_scatter = _count_symbol(preview, C1)
                if low_total + high_total < MAX_FREE_SPINS and 3 <= final_scatter <= 6:
                    low_total += RETRIGGER_LOW
                    high_total += RETRIGGER_HIGH
                    retriggers += 1

                guaranteed_multiplier = SF_GUARANTEED_MULTIPLIER if fg_spins == sf_guaranteed_spin else 0
                if guaranteed_multiplier > 0:
                    sf_guaranteed_count += 1
                multiplier = _draw_multiplier(
                    fg_parameter_idx,
                    profile + (1 if is_high else 0),
                    _count_symbol(preview, C2),
                    guaranteed_multiplier,
                )
                spin_pay, cascades = _cascade(fg_table, fg_board, fg_stops, multiplier * bet_multi, 1, True, round_hits, round_pays, round_eliminates)
                fg_pay += spin_pay
                fg_spins += 1
                fg_cascades += cascades
                fg_multiplier_sum += multiplier
                if multiplier > fg_multiplier_max:
                    fg_multiplier_max = multiplier
                if spin_pay > 0:
                    fg_hit_spins += 1
            if mode == MODE_SUPERFEATUREBUY and sf_guaranteed_count != 1:
                raise RuntimeError("Super Feature must apply exactly one guaranteed 2500x multiplier")

        total_win = bg_pay + fg_pay
        triggered_free_game = 1 if scatter_pay > 0 else 0
        accepted = True
        if CARD_SYSTEM_ENABLED:
            if package_profile >= 0:
                accepted = _is_card_match(package_profile, package_card_idx, total_win, card_coin_in, triggered_free_game)
            elif bg_card_idx >= 0 and CARD_TYPES[bg_profile, bg_card_idx] == CARD_TYPE_FREE_GAME:
                accepted = triggered_free_game == 1 and _is_card_match(fg_profile, fg_card_idx, fg_pay, card_coin_in, 1)
            else:
                accepted = triggered_free_game == 0 and _is_card_match(bg_profile, bg_card_idx, bg_pay, card_coin_in, 0)

        if not accepted:
            stats[S_RETRY_TOTAL] += 1
            retry_count += 1
            continue

        hits += round_hits
        pays += round_pays
        eliminates += round_eliminates
        stats[S_TOTAL_WIN] += total_win
        stats[S_BG_PAY] += bg_regular
        stats[S_SCATTER_PAY] += scatter_pay
        stats[S_FG_PAY] += fg_pay
        if bg_pay > 0:
            stats[S_BG_HITS] += 1
        stats[S_FG_HITS] += fg_hit_spins
        if scatter_pay > 0:
            stats[S_FG_TRIGGER] += 1
        stats[S_RETRIGGER] += retriggers
        stats[S_FREE_SPINS] += fg_spins
        stats[S_BG_CASCADES] += bg_cascades
        stats[S_FG_CASCADES] += fg_cascades
        stats[S_FG_MULTI_SUM] += fg_multiplier_sum
        if fg_multiplier_max > stats[S_FG_MULTI_MAX]:
            stats[S_FG_MULTI_MAX] = fg_multiplier_max
        if total_win > stats[S_MAX_WIN]:
            stats[S_MAX_WIN] = total_win
        x = total_win / coin_in
        stats[S_X_SUM] += x
        stats[S_X_SQUARE] += x * x
        multiplier_line[0, _threshold_index(bg_pay / coin_in)] += 1
        if scatter_pay > 0:
            multiplier_line[1, _threshold_index(fg_pay / coin_in)] += 1
        multiplier_line[2, _threshold_index(x)] += 1
        accepted_rounds += 1
        retry_count = 0

    return stats, hits, pays, eliminates, multiplier_line


def _run_parallel(total_rounds, threads, mode, bet_multi):
    workers = min(threads, total_rounds)
    chunks = [total_rounds // workers] * workers
    for idx in range(total_rounds % workers):
        chunks[idx] += 1
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(lambda count: _simulate_chunk(count, mode, bet_multi), chunks))
    stats = sum((item[0] for item in results), np.zeros(STAT_COUNT))
    hits = sum((item[1] for item in results), np.zeros((2, SYMBOL_COUNT, 3)))
    pays = sum((item[2] for item in results), np.zeros((2, SYMBOL_COUNT, 3)))
    eliminates = sum((item[3] for item in results), np.zeros((2, SYMBOL_COUNT, 3)))
    multiplier_line = sum((item[4] for item in results), np.zeros((3, THRESHOLD_RECORD.shape[0])))
    return stats, hits, pays, eliminates, multiplier_line, time.perf_counter() - started


def _safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def _build_outputs(stats, hits, pays, eliminates, multiplier_line, rounds, duration, bet_mode=BET_MODE, bet_multi=BET_MULTI, threads=THREADS):
    coin_in = DEFAULT_COIN_IN * BET_FACTORS[bet_mode] * bet_multi
    total_coin_in = coin_in * rounds
    fg_spins = stats[S_FREE_SPINS]
    triggers = stats[S_FG_TRIGGER]
    mean = stats[S_X_SUM] / rounds
    variance = max(0.0, stats[S_X_SQUARE] / rounds - mean * mean)
    base_rows = [
        ("Game ID", GAME_ID, ""),
        ("PARsheet ID", PARSHEET_ID, ""),
        ("Game Version", GAME_VERSION, ""),
        ("Config File", CONFIG_FILE, ""),
        ("Parameter Table", PARAMETER_TABLE, ""),
        ("Card Profile Requested", "Newbie" if CARD_SYSTEM_IS_NEWBIE else "Oldhand", ""),
        (
            "Card Profile Applied",
            "Off" if not CARD_SYSTEM_ENABLED else "Oldhand" if bet_mode in (MODE_FEATUREBUY, MODE_SUPERFEATUREBUY) else "Newbie" if CARD_SYSTEM_IS_NEWBIE else "Oldhand",
            "",
        ),
        ("Bet Mode", bet_mode, MODE_NAMES[bet_mode]),
        ("Coin In / Round", coin_in, "credit"),
        ("Total Rounds", rounds, ""),
        ("Threads", min(threads, rounds), ""),
        ("Duration", duration, "seconds"),
        ("rtp_total", _safe_div(stats[S_TOTAL_WIN], total_coin_in), ""),
        ("rtp_bg", _safe_div(stats[S_BG_PAY] + stats[S_SCATTER_PAY], total_coin_in), ""),
        ("rtp_fg", _safe_div(stats[S_FG_PAY], total_coin_in), ""),
        ("RTP", _safe_div(stats[S_TOTAL_WIN], total_coin_in), ""),
        ("RTP - Base", _safe_div(stats[S_BG_PAY], total_coin_in), ""),
        ("RTP - Scatter", _safe_div(stats[S_SCATTER_PAY], total_coin_in), ""),
        ("RTP - Free Game", _safe_div(stats[S_FG_PAY], total_coin_in), ""),
        ("Hit Rate - Paid Round", _safe_div(stats[S_BG_HITS], rounds), ""),
        ("Hit Rate - FG Spin", _safe_div(stats[S_FG_HITS], fg_spins), ""),
        ("FG Trigger Rate", _safe_div(triggers, rounds), f"1 / {_safe_div(rounds, triggers):.2f}" if triggers else "N/A"),
        ("Average FG Spins", _safe_div(fg_spins, triggers), ""),
        ("Retrigger / Feature", _safe_div(stats[S_RETRIGGER], triggers), ""),
        ("Average FG Multiplier", _safe_div(stats[S_FG_MULTI_SUM], fg_spins), ""),
        ("Max FG Multiplier", stats[S_FG_MULTI_MAX], "x"),
        ("Average BG Cascades", _safe_div(stats[S_BG_CASCADES], rounds), ""),
        ("Average FG Cascades", _safe_div(stats[S_FG_CASCADES], fg_spins), ""),
        ("Max Win", _safe_div(stats[S_MAX_WIN], coin_in), "x Bet"),
        ("volatility_std", math.sqrt(variance), ""),
        ("card_system", "on" if CARD_SYSTEM_ENABLED else "off", ""),
        ("card_system_profile", "newbie" if CARD_SYSTEM_IS_NEWBIE and bet_mode in (MODE_NORMALBET, MODE_EXTRABET) else "oldhand", ""),
        ("retry_limit", "unlimited" if CARD_SYSTEM_ENABLED else 0, ""),
        ("retry_total", int(stats[S_RETRY_TOTAL]), ""),
        ("retry_limit_exceeded", int(stats[S_RETRY_LIMIT_EXCEEDED]), ""),
    ]
    df_base = pd.DataFrame(base_rows, columns=["Index", "Value", "Value2"])

    detail_rows = []
    bins = ["8-9", "10-11", "12+"]
    for scene, scene_name in enumerate(("BG", "FG")):
        for symbol in SYMBOLS_SCORE:
            for pay_bin, label in enumerate(bins):
                detail_rows.append(
                    {
                        "Scene": scene_name,
                        "Symbol": SYMBOL_STR[int(symbol)],
                        "Count": label,
                        "Hits": hits[scene, symbol, pay_bin],
                        "Pay": pays[scene, symbol, pay_bin],
                        "RTP": pays[scene, symbol, pay_bin] / total_coin_in,
                        "Eliminate": eliminates[scene, symbol, pay_bin],
                    }
                )
    df_detail = pd.DataFrame(detail_rows)

    labels = []
    for idx, upper in enumerate(THRESHOLD_RECORD):
        labels.append("0" if idx == 0 else f"({THRESHOLD_RECORD[idx - 1]:g}, {upper:g}]")
    df_multiplier = pd.DataFrame(
        {
            "Interval": labels,
            "Base Game": multiplier_line[0],
            "Free Game": multiplier_line[1],
            "Over All": multiplier_line[2],
        }
    )
    df_record = pd.DataFrame({"Stat Index": np.arange(STAT_COUNT), "Value": stats})
    return df_base, df_detail, df_multiplier, df_record


def _print_outputs(df_base, df_detail):
    print("\n=== H998 Fixed Result ===")
    for row in df_base.itertuples(index=False):
        if isinstance(row.Value, float):
            value = f"{row.Value:.6f}"
        else:
            value = str(row.Value)
        print(f"{row.Index:<27} {value:<14} {row.Value2}")
    if SHOW_CONSOLE_DETAIL:
        print("\n=== H998 By-Game Result ===")
        grouped = df_detail.groupby(["Scene", "Symbol"], as_index=False)[["Hits", "Pay", "Eliminate"]].sum()
        print(grouped.to_string(index=False))


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


def format_elapsed_time(seconds):
    total_seconds = max(0, int(round(float(seconds))))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}h {minutes}m {secs}s"


def format_bet_mode_label(bet_mode):
    return MODE_NAMES.get(int(bet_mode), f"Bet Mode {bet_mode}")


def run_simulation(total_round=TOTAL_ROUNDS, bet_mode=BET_MODE, bet_multi=BET_MULTI, threads=THREADS):
    if bet_mode not in SUPPORTED_BET_MODES:
        raise ValueError(f"Unsupported H998 bet mode {bet_mode}; valid modes: {SUPPORTED_BET_MODES}")
    if total_round <= 0 or bet_multi <= 0 or threads <= 0:
        raise ValueError("total_round, bet_multi, and threads must be positive")
    print(
        f"Starting H998 simulation | config={CONFIG_FILE} | mode={format_bet_mode_label(bet_mode)} | " f"rounds={total_round} | threads={threads} | card={'on' if CARD_SYSTEM_ENABLED else 'off'}",
        flush=True,
    )
    print("Compiling Numba core...", flush=True)
    _simulate_chunk(1, bet_mode, bet_multi)
    print("Numba ready. Simulation running...", flush=True)
    stats, hits, pays, eliminates, multiplier_line, duration = _run_parallel(total_round, threads, bet_mode, bet_multi)
    coin_in = DEFAULT_COIN_IN * BET_FACTORS[bet_mode] * bet_multi
    return stats, hits, pays, eliminates, multiplier_line, duration, coin_in


def build_result_frames(stats, hits, pays, eliminates, multiplier_line, total_round, duration, bet_mode=BET_MODE, bet_multi=BET_MULTI, threads=THREADS):
    frames = _build_outputs(
        stats,
        hits,
        pays,
        eliminates,
        multiplier_line,
        total_round,
        duration,
        bet_mode,
        bet_multi,
        threads,
    )
    coin_in = DEFAULT_COIN_IN * BET_FACTORS[bet_mode] * bet_multi
    total_coin_in = coin_in * total_round
    fg_spins = stats[S_FREE_SPINS]
    triggers = stats[S_FG_TRIGGER]
    summary = {
        "rtp_total": _safe_div(stats[S_TOTAL_WIN], total_coin_in),
        "rtp_bg": _safe_div(stats[S_BG_PAY] + stats[S_SCATTER_PAY], total_coin_in),
        "rtp_scatter": _safe_div(stats[S_SCATTER_PAY], total_coin_in),
        "rtp_fg": _safe_div(stats[S_FG_PAY], total_coin_in),
        "hit_rate_bg": _safe_div(stats[S_BG_HITS], total_round),
        "hit_rate_fg": _safe_div(stats[S_FG_HITS], fg_spins),
        "fg_trigger_count": triggers,
        "fg_trigger_rate": _safe_div(triggers, total_round),
        "retrigger_rate": _safe_div(stats[S_RETRIGGER], triggers),
        "avg_fg_multiplier": _safe_div(stats[S_FG_MULTI_SUM], fg_spins),
        "avg_fg_spins": _safe_div(fg_spins, triggers),
        "max_win_multiplier": _safe_div(stats[S_MAX_WIN], coin_in),
        "volatility_std": math.sqrt(max(0.0, stats[S_X_SQUARE] / total_round - (stats[S_X_SUM] / total_round) ** 2)),
    }
    return (*frames, summary)


def print_batch_summary(duration, summary, bet_mode):
    fg_trigger_count = int(round(float(summary.get("fg_trigger_count", 0))))
    print(f"* game_id: {GAME_ID}", flush=True)
    print(f"* version: {GAME_VERSION}", flush=True)
    print(f"* config: {CONFIG_FILE}", flush=True)
    print(f"* parameter_table: {PARAMETER_TABLE}", flush=True)
    print(f"* card_profile_requested: {'newbie' if CARD_SYSTEM_IS_NEWBIE else 'oldhand'}", flush=True)
    print(f"* bet_mode: {format_bet_mode_label(bet_mode)}", flush=True)
    print(f"* duration: {format_elapsed_time(duration)}", flush=True)
    print(f"* rtp_total: {summary['rtp_total'] * 100:.2f}%", flush=True)
    print(f"* rtp_bg: {summary['rtp_bg'] * 100:.2f}%", flush=True)
    print(f"* rtp_scatter: {summary['rtp_scatter'] * 100:.2f}%", flush=True)
    print(f"* rtp_fg: {summary['rtp_fg'] * 100:.2f}%", flush=True)
    print(f"* volatility_std: {summary['volatility_std']:.6f}", flush=True)
    print(f"* hit_rate_bg: {summary['hit_rate_bg']:.4f}", flush=True)
    print(f"* hit_rate_fg: {summary['hit_rate_fg']:.4f}", flush=True)
    print(f"* fg_trigger_rate: {summary['fg_trigger_rate']:.4f} ({fg_trigger_count} spins)", flush=True)
    print(f"* retrigger_rate: {summary['retrigger_rate']:.4f}", flush=True)
    print(f"* avg_fg_multiplier: {summary['avg_fg_multiplier']:.2f} x", flush=True)
    print(f"* avg_fg_spins: {summary['avg_fg_spins']:.2f} spins", flush=True)
    print(f"* max_win_multiplier: {summary['max_win_multiplier']:.2f} x", flush=True)
    print(f"* card_system: {'on' if CARD_SYSTEM_ENABLED else 'off'}", flush=True)


def output_report(df_base, df_detail, df_multiplier, df_record, bet_mode, total_round):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%y%m%d%H%M")
    parts = [GAME_ID]
    version_tag = format_version_tag(GAME_VERSION)
    if version_tag:
        parts.append(version_tag)
    config_tag = Path(CONFIG_FILE).stem.replace("config_", "cfg")
    parameter_tag = f"param{PARAMETER_TABLE.lower()}"
    profile_tag = "newbie" if CARD_SYSTEM_IS_NEWBIE else "oldhand"
    card_tag = "cardon" if CARD_SYSTEM_ENABLED else "cardoff"
    parts.extend(
        [
            config_tag,
            parameter_tag,
            profile_tag,
            card_tag,
            stamp,
            f"betmode{bet_mode}",
            format_rounds_tag(total_round),
        ]
    )
    path = os.path.join(OUTPUT_DIR, f"{'_'.join(parts)}.xlsx")
    with pd.ExcelWriter(path) as writer:
        df_base.to_excel(writer, sheet_name="Base Info", index=False)
        df_detail[["Scene", "Symbol", "Count", "Hits"]].to_excel(writer, sheet_name="Hits", index=False)
        df_detail[["Scene", "Symbol", "Count", "Pay", "RTP"]].to_excel(writer, sheet_name="Pay", index=False)
        df_detail[["Scene", "Symbol", "Count", "Eliminate"]].to_excel(writer, sheet_name="Eliminate", index=False)
        df_multiplier.to_excel(writer, sheet_name="Multiplier Line", index=False)
        df_record.to_excel(writer, sheet_name="Record Data", index=False)
    return path


def run_single_spin_debug(bet_mode=BET_MODE, bet_multi=BET_MULTI):
    stats, hits, pays, eliminates, multiplier_line, duration, coin_in = run_simulation(
        total_round=DEBUG_ROUNDS,
        bet_mode=bet_mode,
        bet_multi=bet_multi,
        threads=1,
    )
    print(
        f"Single spin result: coin_in={coin_in}, total_win={stats[S_TOTAL_WIN]}, " f"scatter_triggers={int(stats[S_FG_TRIGGER])}, duration={duration:.4f}s",
        flush=True,
    )


def run_all_combinations():
    total_jobs = len(BATCH_COMBINATIONS)
    for index, combo in enumerate(BATCH_COMBINATIONS, start=1):
        combo_env = os.environ.copy()
        combo_env["PYTHONUNBUFFERED"] = "1"
        combo_env["H998_CONFIG_FILE"] = str(combo["config_file"])
        combo_env["H998_PARAMETER_TABLE"] = str(combo.get("parameter_table", "AUTO"))
        combo_env["H998_BET_MODE"] = str(combo["bet_mode"])
        combo_env["H998_TOTAL_ROUNDS"] = str(combo["total_rounds"])
        combo_env["H998_CARD_SYSTEM_ENABLED"] = "true" if combo.get("card_system_enabled", True) else "false"
        combo_env["H998_CARD_SYSTEM_IS_NEWBIE"] = "true" if combo.get("card_system_is_newbie", False) else "false"
        combo_env["H998_RUN_ALL_COMBINATIONS"] = "false"
        combo_env["H998_BATCH_CHILD"] = "1"
        print(
            f"\n=== Batch {index}/{total_jobs}: config={combo['config_file']}, "
            f"parameter_table={combo.get('parameter_table', 'AUTO')}, "
            f"bet_mode={combo['bet_mode']}, total_rounds={combo['total_rounds']}, "
            f"card_system_enabled={combo.get('card_system_enabled', True)}, "
            f"card_system_is_newbie={combo.get('card_system_is_newbie', False)} ===",
            flush=True,
        )
        result = subprocess.run(
            [sys.executable, str(SIMULATOR_PATH)],
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
    if RUN_ALL_COMBINATIONS and os.environ.get("H998_BATCH_CHILD") != "1":
        run_all_combinations()
        return
    if RUN_SINGLE_SPIN_DEBUG:
        run_single_spin_debug()
        return

    _validate_settings()
    stats, hits, pays, eliminates, multiplier_line, duration, _coin_in = run_simulation()
    df_base, df_detail, df_multiplier, df_record, summary = build_result_frames(
        stats,
        hits,
        pays,
        eliminates,
        multiplier_line,
        TOTAL_ROUNDS,
        duration,
        BET_MODE,
        BET_MULTI,
        THREADS,
    )
    if SHOW_CONSOLE_SUMMARY:
        _print_outputs(df_base, df_detail)
    print_batch_summary(duration, summary, BET_MODE)
    if OUTPUT_REPORT:
        report_path = output_report(
            df_base,
            df_detail,
            df_multiplier,
            df_record,
            BET_MODE,
            TOTAL_ROUNDS,
        )
        print(f"\nReport: {report_path}")


if __name__ == "__main__":
    main()
