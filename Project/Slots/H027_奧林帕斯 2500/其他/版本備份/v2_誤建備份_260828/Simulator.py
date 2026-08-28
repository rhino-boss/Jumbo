import json
import hashlib
import math
import os
import re
import subprocess
import sys
import time
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# Numba captures module-level config arrays in compiled code.  Put cached
# kernels in a config-content-specific directory so changing config.js cannot
# silently reuse a kernel compiled with older math parameters.
_cache_base_dir = Path(os.environ.get("H027_BASE_DIR", Path(__file__).resolve().parent))
_cache_digest = hashlib.sha256()
for _cache_name in (
    os.environ.get("H027_CONFIG_FILE", "config.js"),
    os.environ.get("H027_CONFIG_RTP_FILE", "config.js"),
):
    _cache_path = _cache_base_dir / _cache_name
    _cache_digest.update(str(_cache_path.resolve()).encode("utf-8"))
    if _cache_path.is_file():
        _cache_digest.update(_cache_path.read_bytes())
os.environ.setdefault("NUMBA_CACHE_DIR", str(Path(os.environ.get("TEMP", ".")) / "h027_numba" / _cache_digest.hexdigest()[:16]))

from numba import njit

# ===== User settings =====

CONFIG_FILE = "config.js"
CONFIG_RTP_FILE = "config.js"
TOTAL_ROUNDS = 10**5
BET_MODE = 0
BET_MULTI = 1
BASE_BET = 1.0
CARD_SYSTEM_ENABLED = False
CARD_SYSTEM_IS_NEWBIE = False
THREADS = max(1, max(8, (os.cpu_count() or 2) - 2))
RANDOM_SEED = None

RUN_ALL_COMBINATIONS = True
OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = True
SHOW_CONSOLE_DETAIL = False

RUN_SINGLE_SPIN_DEBUG = False
BATCH_RUNS = [
    {"config_file": "config.js", "config_rtp_file": "config.js", "bet_mode": 0, "total_rounds": 10**6, "card_system_enabled": False, "card_system_is_newbie": True, "base_bet": 1.0},
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


CONFIG_FILE = os.environ.get("H027_CONFIG_FILE", CONFIG_FILE)
CONFIG_RTP_FILE = os.environ.get("H027_CONFIG_RTP_FILE", CONFIG_RTP_FILE)
TOTAL_ROUNDS = int(os.environ.get("H027_TOTAL_ROUNDS", TOTAL_ROUNDS))
BET_MODE = int(os.environ.get("H027_BET_MODE", BET_MODE))
BET_MULTI = float(os.environ.get("H027_BET_MULTI", BET_MULTI))
BASE_BET = float(os.environ.get("H027_BASE_BET", BASE_BET))
CARD_SYSTEM_ENABLED = parse_env_bool("H027_CARD_SYSTEM_ENABLED", CARD_SYSTEM_ENABLED)
CARD_SYSTEM_IS_NEWBIE = parse_env_bool("H027_CARD_SYSTEM_IS_NEWBIE", CARD_SYSTEM_IS_NEWBIE)
THREADS = int(os.environ.get("H027_THREADS", THREADS))
RANDOM_SEED = int(os.environ["H027_RANDOM_SEED"]) if os.environ.get("H027_RANDOM_SEED") else RANDOM_SEED
RUN_ALL_COMBINATIONS = parse_env_bool("H027_RUN_ALL_COMBINATIONS", RUN_ALL_COMBINATIONS)
OUTPUT_REPORT = parse_env_bool("H027_OUTPUT_REPORT", OUTPUT_REPORT)
SHOW_CONSOLE_SUMMARY = parse_env_bool("H027_SHOW_CONSOLE_SUMMARY", SHOW_CONSOLE_SUMMARY)
SHOW_CONSOLE_DETAIL = parse_env_bool("H027_SHOW_CONSOLE_DETAIL", SHOW_CONSOLE_DETAIL)
RUN_SINGLE_SPIN_DEBUG = parse_env_bool("H027_RUN_SINGLE_SPIN_DEBUG", RUN_SINGLE_SPIN_DEBUG)


def resolve_base_dir():
    override = os.environ.get("H027_BASE_DIR")
    candidates = []
    if override:
        candidates.append(Path(override).expanduser())
    file_value = globals().get("__file__")
    if file_value:
        candidates.append(Path(file_value).resolve().parent)
    cwd = Path.cwd().resolve()
    candidates.extend([cwd, cwd / "Project_AI" / "Slots" / "H027_奧林帕斯 2500"])
    for parent in [cwd, *cwd.parents]:
        candidates.append(parent / "Project_AI" / "Slots" / "H027_奧林帕斯 2500")
        candidates.append(parent / "Slots" / "H027_奧林帕斯 2500")
    for candidate in candidates:
        candidate = candidate.resolve()
        if (candidate / CONFIG_FILE).is_file() and (candidate / CONFIG_RTP_FILE).is_file():
            return candidate
    raise FileNotFoundError(f"Cannot locate H027 base directory containing {CONFIG_FILE} and {CONFIG_RTP_FILE}")


BASE_DIR = resolve_base_dir()
CONFIG_PATH = BASE_DIR / CONFIG_FILE
CONFIG_RTP_PATH = BASE_DIR / CONFIG_RTP_FILE
OUTPUT_DIR = BASE_DIR / "Record"
SIMULATOR_PATH = BASE_DIR / "Simulator.py"


def load_js_config(path):
    text = path.read_text(encoding="utf-8-sig").strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError(f"Invalid config format: {path}")
    return json.loads(text[start : end + 1])


CFG_NATURAL = load_js_config(CONFIG_PATH)
CFG_RTP = load_js_config(CONFIG_RTP_PATH)


def validate_config_pair(natural, rtp):
    natural_game_id = str(natural.get("game_id", ""))
    rtp_game_id = str(rtp.get("game_id", ""))
    if not natural_game_id or natural_game_id != rtp_game_id:
        raise ValueError(f"Config game_id mismatch: {CONFIG_FILE}={natural_game_id!r}, " f"{CONFIG_RTP_FILE}={rtp_game_id!r}")
    natural_version = str(natural.get("excel_version", "")).strip()
    rtp_version = str(rtp.get("excel_version", "")).strip()
    if not re.fullmatch(r"\d", natural_version):
        raise ValueError(f"Base config excel_version must be exactly one digit: {natural_version!r}")
    if CONFIG_PATH.resolve() != CONFIG_RTP_PATH.resolve():
        rtp_parts = rtp_version.split(".")
        if len(rtp_parts) != 4 or any(not part.isdigit() for part in rtp_parts):
            raise ValueError(f"RTP config excel_version must have four numeric parts: {rtp_version!r}")
        if rtp_parts[0] != natural_version:
            raise ValueError(f"Config version mismatch: base {natural_version!r}, RTP {rtp_version!r}")


def merge_runtime_config(natural, rtp):
    """Use natural strips/tables and only RTP-owned multiplier/card parameters."""
    merged = deepcopy(natural)
    natural_parameter = deepcopy(natural.get("parameter", {}))
    rtp_parameter = rtp.get("parameter", {})
    for profile_name in ("normal", "featurebuy"):
        if profile_name not in natural_parameter or profile_name not in rtp_parameter:
            continue
        for key in ("multiplier", "c2_to_c3"):
            if key in rtp_parameter[profile_name]:
                natural_parameter[profile_name][key] = deepcopy(rtp_parameter[profile_name][key])
    merged["parameter"] = natural_parameter
    merged["card_system"] = deepcopy(rtp.get("card_system", {}))
    for key in (
        "model",
        "parsheet_id",
        "rtp_label",
        "runtime_version",
        "config_type",
        "config_code",
        "source_multiplier_xlsx",
    ):
        if key in rtp:
            merged[key] = deepcopy(rtp[key])
    return merged


validate_config_pair(CFG_NATURAL, CFG_RTP)
CFG = merge_runtime_config(CFG_NATURAL, CFG_RTP)

GAME_ID = str(CFG["game_id"])
PARSHEET_ID = str(CFG["parsheet_id"])
GAME_NAME = str(CFG["display_name"])
GAME_NAME_ZH = str(CFG["game_name_zh"])
CONFIG_VERSION = str(CFG_RTP["excel_version"])
BASE_CONFIG_VERSION = str(CFG_NATURAL["excel_version"])
RULE_DOCUMENT = str(CFG.get("rule_document", "game_rule_H027.md"))
MODEL_STATUS = str(CFG.get("model_status", "unknown"))
PENDING_MATH_ITEMS = tuple(str(item) for item in CFG.get("pending_math_items", []))

MODE_NORMALBET = int(CFG["mode_normalbet"])
MODE_EXTRABET = int(CFG["mode_extrabet"])
MODE_FEATUREBUY = int(CFG["mode_featurebuy"])
SUPPORTED_BET_MODES = tuple(int(value) for value in CFG["supported_bet_modes"])
DEFAULT_COIN_IN = int(CFG["default_coin_in"])
NORMALBET = int(CFG["normalbet"])
EXTRABET = int(CFG["extrabet"])
FEATUREBUY = int(CFG["featurebuy"])
DENOM = float(CFG["denom"])
BET_TIER_THRESHOLDS = CFG.get("bet_tier_thresholds", {"small_bet_lt": 2, "medium_bet_lte": 100})
SMALL_BET_LT = float(BET_TIER_THRESHOLDS["small_bet_lt"])
MEDIUM_BET_LTE = float(BET_TIER_THRESHOLDS["medium_bet_lte"])
LINK_ENABLED_BY_CONFIG = bool(CFG.get("link", {}).get("enabled", False))
if BASE_BET <= 0:
    raise ValueError(f"base_bet must be greater than zero, got {BASE_BET}")
BET_MULTI = BASE_BET / (DEFAULT_COIN_IN * NORMALBET * DENOM)
EXTRA_FG_PROBABILITY_MULTIPLIER = float(CFG["extra_fg_probability_multiplier"])
WINDOW_SIZE = int(CFG["window_size"])
REEL_NUM = int(CFG["reel_num"])
MAX_FREE_SPINS = int(CFG["max_free_spins"])
FG_TRIGGER_COUNT = int(CFG["fg_trigger_count"])
FG_RETRIGGER_COUNT = int(CFG["fg_retrigger_count"])
CASCADE_LIMIT = int(CFG["cascade_limit"])

SYMBOL_CODES = list(CFG["symbol_codes"])
SYMBOL_IDS = np.asarray(CFG["symbol_ids"], dtype=np.int64)
CODE_TO_ID = {code: int(symbol_id) for code, symbol_id in zip(SYMBOL_CODES, SYMBOL_IDS)}
ID_TO_CODE = {int(symbol_id): code for code, symbol_id in zip(SYMBOL_CODES, SYMBOL_IDS)}
SYMBOL_COUNT = int(SYMBOL_IDS.max()) + 1
PAY_TABLE = np.zeros((SYMBOL_COUNT, 6), dtype=np.int64)
for symbol_id, values in zip(SYMBOL_IDS, CFG["pay_table"]):
    PAY_TABLE[int(symbol_id)] = np.asarray(values, dtype=np.int64)
C1 = CODE_TO_ID["C1"]
C2 = CODE_TO_ID["C2"]
C3 = CODE_TO_ID["C3"]
SCORE_SYMBOLS = np.asarray([CODE_TO_ID[code] for code in SYMBOL_CODES if code not in {"C1", "C2", "C3"}], dtype=np.int64)

ORIGINAL_REEL_LENGTHS = np.asarray([item["reel_lengths"] for item in CFG["strips"]], dtype=np.int64)
MAX_STRIP_ROWS = max(len(item["symbols"]) for item in CFG["strips"])
STRIPS = np.zeros((len(CFG["strips"]), MAX_STRIP_ROWS, REEL_NUM), dtype=np.int64)
STRIP_WEIGHTS = np.zeros_like(STRIPS)
LINKED_STOP_WEIGHTS = np.zeros(len(CFG["strips"]), dtype=np.int64)
LINKED_STOP_DENOMINATORS = np.full(len(CFG["strips"]), 10000, dtype=np.int64)
LINKED_STOP_OFFSETS = np.zeros((len(CFG["strips"]), REEL_NUM), dtype=np.int64)
for table_index, item in enumerate(CFG["strips"]):
    row_count = len(item["symbols"])
    STRIPS[table_index, :row_count] = np.asarray(item["symbols"], dtype=np.int64)
    STRIP_WEIGHTS[table_index, :row_count] = np.asarray(item["weights"], dtype=np.int64)
    LINKED_STOP_WEIGHTS[table_index] = int(item.get("linked_stop_weight", 0))
    LINKED_STOP_DENOMINATORS[table_index] = int(item.get("linked_stop_denominator", 10000))
    offsets = item.get("linked_stop_offsets", [0] * REEL_NUM)
    LINKED_STOP_OFFSETS[table_index, : len(offsets)] = np.asarray(offsets, dtype=np.int64)

REEL_LENGTHS = ORIGINAL_REEL_LENGTHS.copy()
STRIP_NAMES = list(CFG["strip_names"])
TABLE_BY_NAME = {name: index for index, name in enumerate(STRIP_NAMES)}

PROFILE_NAMES = ["normal", "featurebuy"]
PROFILE_BY_MODE = {MODE_NORMALBET: 0, MODE_EXTRABET: 0, MODE_FEATUREBUY: 1}
FEATUREBUY_PROFILE_INDEX = 1
PARAMETER = CFG["parameter"]

PROFILE_COUNT = len(PROFILE_NAMES)
TABLE_COUNT = len(STRIP_NAMES)
MAX_BASE_TABLES = max(len(PARAMETER[name]["base_reel_names"]) for name in PROFILE_NAMES)
MAX_FREE_TABLES = max(len(PARAMETER[name]["free_table"]["names"]) for name in PROFILE_NAMES)
MULTIPLIER_LEVELS = np.asarray(CFG["multiplier_levels"], dtype=np.int64)
MULTIPLIER_LEVEL_COUNT = len(MULTIPLIER_LEVELS)
CFG_MULTIPLIER_MAX = int(CFG.get("multiplier_max_value", 2500))
INITIAL_MULTIPLIER_COUNT = max(len(PARAMETER[name]["multiplier"]["multipliers"]) for name in PROFILE_NAMES)
BASE_REEL_WEIGHT_CUM = np.zeros((PROFILE_COUNT, MAX_BASE_TABLES), dtype=np.int64)
BASE_REEL_TABLE_IDS = np.full((PROFILE_COUNT, MAX_BASE_TABLES), -1, dtype=np.int64)
FREE_INITIAL_COUNTS = np.zeros((PROFILE_COUNT, MAX_FREE_TABLES), dtype=np.int64)
FREE_RETRIGGER_COUNTS = np.zeros((PROFILE_COUNT, MAX_FREE_TABLES), dtype=np.int64)
FREE_TABLE_IDS = np.full((PROFILE_COUNT, MAX_FREE_TABLES), -1, dtype=np.int64)
USE_SUPER_WEIGHT = np.zeros((PROFILE_COUNT, TABLE_COUNT, 6), dtype=np.int64)
DROP_SUPER_WEIGHT = np.zeros((PROFILE_COUNT, TABLE_COUNT, 5), dtype=np.int64)
USE_SUPER_DENOMINATOR = np.full(PROFILE_COUNT, 10000, dtype=np.int64)
BALL_MULTIPLIERS = np.zeros((PROFILE_COUNT, INITIAL_MULTIPLIER_COUNT), dtype=np.int64)
BALL_C2_WEIGHT_CUM = np.zeros((PROFILE_COUNT, TABLE_COUNT, INITIAL_MULTIPLIER_COUNT), dtype=np.int64)
BALL_C3_WEIGHT_CUM = np.zeros((PROFILE_COUNT, TABLE_COUNT, INITIAL_MULTIPLIER_COUNT), dtype=np.int64)

for profile_index, profile_name in enumerate(PROFILE_NAMES):
    profile = PARAMETER[profile_name]
    base_cum = profile["base_reel_weights_cum"]
    BASE_REEL_WEIGHT_CUM[profile_index, : len(base_cum)] = base_cum
    for index, name in enumerate(profile["base_reel_names"]):
        BASE_REEL_TABLE_IDS[profile_index, index] = TABLE_BY_NAME[name]
    free_table = profile["free_table"]
    FREE_INITIAL_COUNTS[profile_index, : len(free_table["initial"])] = np.asarray(free_table["initial"], dtype=np.int64)
    FREE_RETRIGGER_COUNTS[profile_index, : len(free_table["retrigger"])] = np.asarray(free_table["retrigger"], dtype=np.int64)
    for index, name in enumerate(free_table["names"]):
        FREE_TABLE_IDS[profile_index, index] = TABLE_BY_NAME[name]
    use_super = profile["c2_to_c3"]
    USE_SUPER_DENOMINATOR[profile_index] = int(use_super.get("denominator", 10000))
    for name in use_super["table_names"]:
        weights = use_super["weights_by_initial_ball_count"][name]
        USE_SUPER_WEIGHT[profile_index, TABLE_BY_NAME[name], : len(weights)] = np.asarray(weights, dtype=np.int64)
        drop_weights = use_super.get("weights_by_drop_combo", {}).get(name, weights[:5])
        DROP_SUPER_WEIGHT[profile_index, TABLE_BY_NAME[name], : len(drop_weights)] = np.asarray(drop_weights, dtype=np.int64)
    multiplier = profile["multiplier"]
    BALL_MULTIPLIERS[profile_index, : len(multiplier["multipliers"])] = np.asarray(multiplier["multipliers"], dtype=np.int64)
    for table_name in multiplier["table_names"]:
        table_id = TABLE_BY_NAME[table_name]
        c2_values = multiplier["weights_c2_cum"][table_name]
        c3_values = multiplier["weights_c3_cum"][table_name]
        BALL_C2_WEIGHT_CUM[profile_index, table_id, : len(c2_values)] = np.asarray(c2_values, dtype=np.int64)
        BALL_C3_WEIGHT_CUM[profile_index, table_id, : len(c3_values)] = np.asarray(c3_values, dtype=np.int64)
    fallback_table_id = BASE_REEL_TABLE_IDS[0, 0]
    for table_id in range(TABLE_COUNT):
        if BALL_C2_WEIGHT_CUM[profile_index, table_id].sum() == 0:
            BALL_C2_WEIGHT_CUM[profile_index, table_id] = BALL_C2_WEIGHT_CUM[profile_index, fallback_table_id]
            BALL_C3_WEIGHT_CUM[profile_index, table_id] = BALL_C3_WEIGHT_CUM[profile_index, fallback_table_id]
            USE_SUPER_WEIGHT[profile_index, table_id] = USE_SUPER_WEIGHT[profile_index, fallback_table_id]
            DROP_SUPER_WEIGHT[profile_index, table_id] = DROP_SUPER_WEIGHT[profile_index, fallback_table_id]

FEATUREBUY_TABLE_ID = BASE_REEL_TABLE_IDS[FEATUREBUY_PROFILE_INDEX, 0]

CARD_SYSTEM = CFG.get("card_system", {})
CARD_SYSTEM_ENABLED = CARD_SYSTEM_ENABLED and bool(CARD_SYSTEM.get("enabled", False))
CARD_RETRY_LIMIT = int(CARD_SYSTEM.get("retry_limit", 10000) or 10000)
if CARD_SYSTEM_ENABLED and CARD_RETRY_LIMIT != 10000:
    raise ValueError(f"Enabled card_system.retry_limit must be 10000, got {CARD_RETRY_LIMIT}")
CARD_TYPE_RANGE = 0
CARD_TYPE_FREE_GAME = 1
CARD_PROFILE_NEWBIE_BG = 0
CARD_PROFILE_NEWBIE_FG = 1
CARD_PROFILE_NEWBIE_BUY_FEATURE = 2
CARD_PROFILE_OLDHAND_BG = 3
CARD_PROFILE_OLDHAND_FG = 4
CARD_PROFILE_OLDHAND_BUY_FEATURE = 5

if BASE_BET < SMALL_BET_LT:
    ACTIVE_CARD_BET_TIER = "small_bet"
elif BASE_BET <= MEDIUM_BET_LTE:
    ACTIVE_CARD_BET_TIER = "medium_bet"
else:
    ACTIVE_CARD_BET_TIER = "big_bet"


def get_card_profile_cards(player, mode, segment, bet_tier=None):
    player_data = CARD_SYSTEM.get(player, {})
    mode_data = player_data.get(mode, {}) if isinstance(player_data, dict) else {}
    if player == "oldhand" and isinstance(mode_data, dict):
        tier = bet_tier or ACTIVE_CARD_BET_TIER
        mode_data = mode_data.get(tier, {})
    return list(mode_data.get(segment, [])) if isinstance(mode_data, dict) else []


def get_bg_trigger_cap(player, mode, bet_tier):
    player_data = CFG_RTP.get("card_system", {}).get(player, {})
    mode_data = player_data.get(mode, {}) if isinstance(player_data, dict) else {}
    if player == "oldhand" and isinstance(mode_data, dict) and bet_tier in mode_data:
        mode_data = mode_data[bet_tier]
    cards = mode_data.get("weight_bg", []) if isinstance(mode_data, dict) else []
    caps = [float(card["max"]) for card in cards if card.get("type", "range") == "range" and float(card.get("weight", 0)) > 0]
    return max(caps) if caps else None


CARD_PROFILE_LISTS = [
    get_card_profile_cards("newbie", "normal_bet", "weight_bg"),
    get_card_profile_cards("newbie", "normal_bet", "weight_fg"),
    get_card_profile_cards("newbie", "buy_feature", "weight_fg"),
    get_card_profile_cards("oldhand", "normal_bet", "weight_bg", ACTIVE_CARD_BET_TIER),
    get_card_profile_cards("oldhand", "normal_bet", "weight_fg", ACTIVE_CARD_BET_TIER),
    get_card_profile_cards("oldhand", "buy_feature", "weight_fg", ACTIVE_CARD_BET_TIER),
]
MAX_CARDS = max(1, max((len(cards) for cards in CARD_PROFILE_LISTS), default=0))
CARD_TYPES = np.full((len(CARD_PROFILE_LISTS), MAX_CARDS), -1, dtype=np.int64)
CARD_MIN = np.zeros((len(CARD_PROFILE_LISTS), MAX_CARDS), dtype=np.float64)
CARD_MAX = np.zeros((len(CARD_PROFILE_LISTS), MAX_CARDS), dtype=np.float64)
CARD_WEIGHT_CUM = np.zeros((len(CARD_PROFILE_LISTS), MAX_CARDS), dtype=np.int64)
CARD_COUNTS = np.zeros(len(CARD_PROFILE_LISTS), dtype=np.int64)
CARD_BG_TRIGGER_CAP = np.full(len(CARD_PROFILE_LISTS), -1.0, dtype=np.float64)
for card_profile_index, cards in enumerate(CARD_PROFILE_LISTS):
    running_weight = 0
    for card_index, card in enumerate(cards):
        weight = max(0, int(card.get("weight", 0)))
        running_weight += weight
        CARD_TYPES[card_profile_index, card_index] = CARD_TYPE_FREE_GAME if card.get("type") == "free_game" else CARD_TYPE_RANGE
        CARD_MIN[card_profile_index, card_index] = float(card.get("min", 0.0))
        CARD_MAX[card_profile_index, card_index] = float(card.get("max", 0.0))
        CARD_WEIGHT_CUM[card_profile_index, card_index] = running_weight
        if CARD_TYPES[card_profile_index, card_index] == CARD_TYPE_RANGE and weight > 0:
            CARD_BG_TRIGGER_CAP[card_profile_index] = max(CARD_BG_TRIGGER_CAP[card_profile_index], CARD_MAX[card_profile_index, card_index])
    CARD_COUNTS[card_profile_index] = len(cards)
if CARD_SYSTEM_ENABLED:
    for profile_index in (CARD_PROFILE_NEWBIE_BG, CARD_PROFILE_OLDHAND_BG):
        has_free_game = any(CARD_TYPES[profile_index, index] == CARD_TYPE_FREE_GAME and CARD_WEIGHT_CUM[profile_index, index] > (CARD_WEIGHT_CUM[profile_index, index - 1] if index else 0) for index in range(CARD_COUNTS[profile_index]))
        if has_free_game and CARD_BG_TRIGGER_CAP[profile_index] < 0:
            raise ValueError("Enabled free_game card requires a positive-weight BG range card for BG Trigger Cap")


def calc_coin_in(bet_mode, bet_multi):
    if bet_mode == MODE_NORMALBET:
        return DEFAULT_COIN_IN * NORMALBET * bet_multi
    if bet_mode == MODE_EXTRABET:
        return DEFAULT_COIN_IN * EXTRABET * bet_multi
    if bet_mode == MODE_FEATUREBUY:
        return DEFAULT_COIN_IN * FEATUREBUY * bet_multi
    raise ValueError(f"Unsupported bet mode: {bet_mode}")


def build_bet_context(bet_mode, bet_multi):
    coin_in = float(calc_coin_in(bet_mode, bet_multi))
    bet_amount = coin_in * DENOM
    feature_price_multiplier = FEATUREBUY if bet_mode == MODE_FEATUREBUY else None
    bet_tier_amount = bet_amount / feature_price_multiplier if feature_price_multiplier else bet_amount
    if bet_tier_amount < SMALL_BET_LT:
        bet_tier = "small_bet"
    elif bet_tier_amount <= MEDIUM_BET_LTE:
        bet_tier = "medium_bet"
    else:
        bet_tier = "big_bet"
    return {
        "bet_multi": float(bet_multi),
        "feature_price_multiplier": feature_price_multiplier,
        "base_bet": float(DEFAULT_COIN_IN * NORMALBET * bet_multi * DENOM),
        "bet_amount": bet_amount,
        "bet_tier_amount": bet_tier_amount,
        "bet_tier": bet_tier,
        "link_enabled": LINK_ENABLED_BY_CONFIG and bet_tier != "small_bet",
        # H027 has no product Max Win cap. The 2500 value limits one C2/C3
        # ball, not the sum of a round, so the runtime cap is game-defined.
        "max_multiplier_bg": "by_game",
        "max_multiplier_fg": "by_game",
        "coin_in": coin_in,
    }


def format_bet_mode_label(bet_mode):
    if bet_mode == MODE_EXTRABET:
        return "Extra Bet"
    if bet_mode == MODE_FEATUREBUY:
        return "Buy Feature"
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
R_SYMBOL_BUCKET_BG_8_9 = 17
R_SYMBOL_BUCKET_BG_10_11 = 18
R_SYMBOL_BUCKET_BG_12_PLUS = 19
R_SYMBOL_BUCKET_FG_8_9 = 20
R_SYMBOL_BUCKET_FG_10_11 = 21
R_SYMBOL_BUCKET_FG_12_PLUS = 22
R_BG_TRIGGER_FG_CNT = 23
R_BG_TRIGGER_FG_PAY = 24
R_CASCADE_BG_WITH_BALL = 25
R_CASCADE_BG_WITHOUT_BALL = 26
R_CASCADE_FG_WITH_BALL = 27
R_CASCADE_FG_WITHOUT_BALL = 28
R_SYMBOL_BUCKET_PAY_BG_8_9 = 29
R_SYMBOL_BUCKET_PAY_BG_10_11 = 30
R_SYMBOL_BUCKET_PAY_BG_12_PLUS = 31
R_SYMBOL_BUCKET_PAY_FG_8_9 = 32
R_SYMBOL_BUCKET_PAY_FG_10_11 = 33
R_SYMBOL_BUCKET_PAY_FG_12_PLUS = 34
R_BG_INTERVAL_CASCADE_1 = 35
R_BG_INTERVAL_CASCADE_2 = 36
R_BG_INTERVAL_CASCADE_3 = 37
R_BG_INTERVAL_CASCADE_4 = 38
R_BG_INTERVAL_CASCADE_5P = 39
R_FG_INTERVAL_SPINS = 40
R_FG_INTERVAL_HIT_SPINS = 41
R_FG_INTERVAL_CASCADE_1 = 42
R_FG_INTERVAL_CASCADE_2 = 43
R_FG_INTERVAL_CASCADE_3 = 44
R_FG_INTERVAL_CASCADE_4 = 45
R_FG_INTERVAL_CASCADE_5P = 46

RECORD_COLS = max(128, len(THRESHOLD_RECORD), SYMBOL_COUNT, MULTIPLIER_LEVEL_COUNT)
RECORD_SIZE = (47, RECORD_COLS)

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
RA_C2_SPINS_BG = 25
RA_C2_SPINS_FG = 26
RA_BG_TRIGGER_FG_PAY = 27
RA_SPECIAL_SYMBOL_SPINS = 28
RA_FG_SESSION_MULTIPLIER_SUM = 29
RA_FG_SESSION_COUNT = 30


@njit(nogil=True, cache=True)
def pick_cumulative(cumulative):
    total = cumulative[-1]
    if total <= 0:
        return 0
    pick = np.random.randint(0, total)
    for index in range(cumulative.shape[0]):
        if pick < cumulative[index]:
            return index
    return cumulative.shape[0] - 1


@njit(nogil=True, cache=True)
def pick_cumulative_unit(cumulative, unit_pick, unit_total):
    total = cumulative[-1]
    if total <= 0 or unit_total <= 0:
        return 0
    pick = (unit_pick * total) // unit_total
    if pick >= total:
        pick = total - 1
    for index in range(cumulative.shape[0]):
        if pick < cumulative[index]:
            return index
    return cumulative.shape[0] - 1


@njit(nogil=True, cache=True)
def pick_card(card_profile_index):
    card_count = CARD_COUNTS[card_profile_index]
    if card_count <= 0:
        return -1
    return pick_cumulative(CARD_WEIGHT_CUM[card_profile_index, :card_count])


@njit(nogil=True, cache=True)
def is_card_match(card_profile_index, card_index, score, card_coin_in, triggered_free_game):
    if card_index < 0:
        return True
    if CARD_TYPES[card_profile_index, card_index] == CARD_TYPE_FREE_GAME:
        return triggered_free_game == 1
    multiplier = score / card_coin_in
    return multiplier > CARD_MIN[card_profile_index, card_index] and multiplier <= CARD_MAX[card_profile_index, card_index]


@njit(nogil=True, cache=True)
def choose_base_table(profile_index):
    cumulative = BASE_REEL_WEIGHT_CUM[profile_index]
    selected = pick_cumulative(cumulative)
    return BASE_REEL_TABLE_IDS[profile_index, selected]


@njit(nogil=True, cache=True)
def draw_initial_multiplier(profile_index, table_id, symbol):
    cumulative = BALL_C3_WEIGHT_CUM[profile_index, table_id] if symbol == C3 else BALL_C2_WEIGHT_CUM[profile_index, table_id]
    values = BALL_MULTIPLIERS[profile_index]
    valid_length = 0
    for index in range(cumulative.shape[0]):
        if cumulative[index] > 0:
            valid_length = index + 1
    if valid_length == 0:
        return 0
    selected = pick_cumulative(cumulative[:valid_length])
    return values[selected]


@njit(nogil=True, cache=True)
def prepare_multiplier_symbol(symbol, profile_index, table_id, use_c3_weight):
    if symbol != C2:
        return symbol, 0
    denominator = USE_SUPER_DENOMINATOR[profile_index]
    use_c3 = 1 if denominator > 0 and np.random.randint(0, denominator) < use_c3_weight else 0
    final_symbol = C3 if use_c3 == 1 else C2
    return final_symbol, draw_initial_multiplier(profile_index, table_id, final_symbol)


@njit(nogil=True, cache=True)
def prepare_initial_multiplier_symbol(symbol, profile_index, table_id, initial_ball_count):
    bucket = min(6, max(1, initial_ball_count)) - 1
    return prepare_multiplier_symbol(symbol, profile_index, table_id, USE_SUPER_WEIGHT[profile_index, table_id, bucket])


@njit(nogil=True, cache=True)
def prepare_drop_multiplier_symbol(symbol, profile_index, table_id, combo_count):
    bucket = min(5, max(1, combo_count)) - 1
    return prepare_multiplier_symbol(symbol, profile_index, table_id, DROP_SUPER_WEIGHT[profile_index, table_id, bucket])


@njit(nogil=True, cache=True)
def upgrade_c3_value(value):
    for index in range(MULTIPLIER_LEVELS.shape[0]):
        if MULTIPLIER_LEVELS[index] == value:
            if index < MULTIPLIER_LEVELS.shape[0] - 1:
                return MULTIPLIER_LEVELS[index + 1]
            return MULTIPLIER_LEVELS[index]
    return min(value, int(CFG_MULTIPLIER_MAX))


@njit(nogil=True, cache=True)
def generate_board(table_id, profile_index):
    board = np.empty((WINDOW_SIZE, REEL_NUM), dtype=np.int64)
    multiplier_values = np.zeros((WINDOW_SIZE, REEL_NUM), dtype=np.int64)
    starts = np.zeros(REEL_NUM, dtype=np.int64)
    drop_counts = np.zeros(REEL_NUM, dtype=np.int64)
    linked_stop = -1
    linked_total = LINKED_STOP_DENOMINATORS[table_id]
    if linked_total > 0 and np.random.randint(0, linked_total) < LINKED_STOP_WEIGHTS[table_id]:
        # One shared weighted percentile preserves every reel's marginal stop
        # distribution while reproducing the cross-reel dependence visible in
        # competitor response screens.
        linked_stop = np.random.randint(0, 1000000)
    for reel in range(REEL_NUM):
        length = REEL_LENGTHS[table_id, reel]
        total = 0
        for row in range(length):
            total += STRIP_WEIGHTS[table_id, row, reel]
        linked_unit = (linked_stop + LINKED_STOP_OFFSETS[table_id, reel]) % 1000000
        pick = (linked_unit * total // 1000000) if linked_stop >= 0 and total > 0 else (np.random.randint(0, total) if total > 0 else 0)
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
    # Competitor Buy Feature entry is not a reel-set screen: it contains
    # exactly one C1 on each of R2-R5 and the remaining 26 cells are uniform
    # over the nine regular paying symbols.  Starts are still retained as the
    # circular-strip source if the entry screen creates a cascade.
    if profile_index == FEATUREBUY_PROFILE_INDEX and table_id == FEATUREBUY_TABLE_ID:
        for row in range(WINDOW_SIZE):
            for reel in range(REEL_NUM):
                board[row, reel] = SCORE_SYMBOLS[np.random.randint(0, SCORE_SYMBOLS.shape[0])]
        for reel in range(1, 5):
            board[np.random.randint(0, WINDOW_SIZE), reel] = C1
    initial_ball_count = 0
    for row in range(WINDOW_SIZE):
        for reel in range(REEL_NUM):
            if board[row, reel] == C2:
                initial_ball_count += 1
    for row in range(WINDOW_SIZE):
        for reel in range(REEL_NUM):
            symbol, value = prepare_initial_multiplier_symbol(board[row, reel], profile_index, table_id, initial_ball_count)
            board[row, reel] = symbol
            multiplier_values[row, reel] = value
    return board, multiplier_values, starts, drop_counts, initial_ball_count


@njit(nogil=True, cache=True)
def pay_index_for_count(count):
    if count >= 12:
        return 5
    if count >= 10:
        return 4
    if count >= 8:
        return 3
    return -1


@njit(nogil=True, cache=True)
def evaluate_clusters(board, bet_multi):
    winning = np.zeros(SYMBOL_COUNT, dtype=np.int64)
    symbol_hits = np.zeros(SYMBOL_COUNT, dtype=np.int64)
    symbol_bucket_hits = np.zeros((3, SYMBOL_COUNT), dtype=np.int64)
    symbol_bucket_pay = np.zeros((3, SYMBOL_COUNT), dtype=np.int64)
    symbol_raw_pay = np.zeros(SYMBOL_COUNT, dtype=np.int64)
    raw_pay = 0
    any_win = 0
    for symbol_index in range(SCORE_SYMBOLS.shape[0]):
        symbol = SCORE_SYMBOLS[symbol_index]
        count = 0
        for row in range(WINDOW_SIZE):
            for reel in range(REEL_NUM):
                if board[row, reel] == symbol:
                    count += 1
        pay_index = pay_index_for_count(count)
        if pay_index >= 0:
            pay = PAY_TABLE[symbol, pay_index] * bet_multi
            winning[symbol] = 1
            symbol_hits[symbol] += 1
            symbol_bucket_hits[pay_index - 3, symbol] += 1
            symbol_bucket_pay[pay_index - 3, symbol] += pay
            symbol_raw_pay[symbol] += pay
            raw_pay += pay
            any_win = 1
    return raw_pay, winning, symbol_hits, symbol_bucket_hits, symbol_bucket_pay, symbol_raw_pay, any_win


@njit(nogil=True, cache=True)
def cascade_board(board, multiplier_values, table_id, profile_index, starts, drop_counts, winning, any_win, combo_count):
    if any_win == 0:
        return
    for reel in range(REEL_NUM):
        kept_symbols = np.empty(WINDOW_SIZE, dtype=np.int64)
        kept_multiplier_values = np.zeros(WINDOW_SIZE, dtype=np.int64)
        kept_count = 0
        has_scatter = 0
        for row in range(WINDOW_SIZE - 1, -1, -1):
            symbol = board[row, reel]
            if symbol == C1:
                has_scatter = 1
            if symbol < winning.shape[0] and winning[symbol] == 1:
                continue
            else:
                kept_symbols[kept_count] = symbol
                value = multiplier_values[row, reel]
                kept_multiplier_values[kept_count] = upgrade_c3_value(value) if symbol == C3 else value
                kept_count += 1

        output_row = WINDOW_SIZE - 1
        for index in range(kept_count):
            board[output_row, reel] = kept_symbols[index]
            multiplier_values[output_row, reel] = kept_multiplier_values[index]
            output_row -= 1

        while output_row >= 0:
            drop_counts[reel] += 1
            length = REEL_LENGTHS[table_id, reel]
            source_index = (starts[reel] - drop_counts[reel]) % length
            symbol = STRIPS[table_id, source_index, reel]
            symbol, value = prepare_drop_multiplier_symbol(symbol, profile_index, table_id, combo_count)
            if symbol == C1:
                has_scatter = 1
            board[output_row, reel] = symbol
            multiplier_values[output_row, reel] = value
            output_row -= 1


@njit(nogil=True, cache=True)
def count_scatter(board):
    count = 0
    for row in range(WINDOW_SIZE):
        for reel in range(REEL_NUM):
            if board[row, reel] == C1:
                count += 1
    return count


@njit(nogil=True, cache=True)
def play_cluster_spin(table_id, profile_index, scene, bet_multi):
    board, multiplier_values, starts, drop_counts, initial_ball_count = generate_board(table_id, profile_index)
    total_raw_pay = 0
    total_hits = np.zeros(SYMBOL_COUNT, dtype=np.int64)
    total_bucket_hits = np.zeros((3, SYMBOL_COUNT), dtype=np.int64)
    total_bucket_pay = np.zeros((3, SYMBOL_COUNT), dtype=np.int64)
    total_raw_symbol_pay = np.zeros(SYMBOL_COUNT, dtype=np.int64)
    cascades = 0

    for _ in range(CASCADE_LIMIT):
        raw_pay, winning, hits, bucket_hits, bucket_pay, raw_symbol_pay, any_win = evaluate_clusters(board, bet_multi)
        total_raw_pay += raw_pay
        total_hits += hits
        total_bucket_hits += bucket_hits
        total_bucket_pay += bucket_pay
        total_raw_symbol_pay += raw_symbol_pay
        if any_win == 0:
            break
        cascades += 1
        cascade_board(board, multiplier_values, table_id, profile_index, starts, drop_counts, winning, any_win, cascades)

    multiplier_total = 0
    multiplier_count = 0
    multiplier_value_hits = np.zeros(MULTIPLIER_LEVEL_COUNT, dtype=np.int64)
    for row in range(WINDOW_SIZE):
        for reel in range(REEL_NUM):
            if board[row, reel] == C2 or board[row, reel] == C3:
                value = multiplier_values[row, reel]
                multiplier_total += value
                multiplier_count += 1
                for value_index in range(MULTIPLIER_LEVEL_COUNT):
                    if MULTIPLIER_LEVELS[value_index] == value:
                        multiplier_value_hits[value_index] += 1
                        break

    scatter_count = count_scatter(board)
    scatter_pay = 0
    if scatter_count >= FG_TRIGGER_COUNT and scatter_count <= 6:
        scatter_pay = PAY_TABLE[C1, scatter_count - FG_TRIGGER_COUNT] * bet_multi
    return (
        total_raw_pay,
        scatter_pay,
        scatter_count,
        multiplier_total,
        multiplier_count,
        cascades,
        total_hits,
        total_raw_symbol_pay,
        total_bucket_hits,
        total_bucket_pay,
        multiplier_value_hits,
    )


@njit(nogil=True, cache=True)
def play_base_spin_for_mode(table_id, profile_index, bet_mode, bet_multi):
    result = play_cluster_spin(table_id, profile_index, 0, bet_multi)
    if bet_mode != MODE_EXTRABET or result[2] >= FG_TRIGGER_COUNT:
        return result

    # Extra Bet gets five Normal-distribution trigger opportunities.  The first
    # trigger screen is used; if none trigger, the original first result is kept.
    # This stays tied to the current reel distribution while dedicated Extra
    # Bet strips are still pending.
    for _ in range(1, int(EXTRA_FG_PROBABILITY_MULTIPLIER)):
        candidate_table_id = choose_base_table(profile_index)
        candidate = play_cluster_spin(candidate_table_id, profile_index, 0, bet_multi)
        if candidate[2] >= FG_TRIGGER_COUNT:
            return candidate
    return result


@njit(nogil=True, cache=True)
def shuffle_segment(values, start, end):
    for index in range(end - 1, start, -1):
        selected = np.random.randint(start, index + 1)
        temp = values[index]
        values[index] = values[selected]
        values[selected] = temp


@njit(nogil=True, cache=True)
def append_free_tables(target, current_length, counts, table_ids):
    start = current_length
    for table_index in range(counts.shape[0]):
        for _ in range(counts[table_index]):
            if current_length >= target.shape[0]:
                return current_length
            target[current_length] = table_ids[table_index]
            current_length += 1
    shuffle_segment(target, start, current_length)
    return current_length


@njit(nogil=True, cache=True)
def get_bucket(win, coin_in):
    multiplier = win / coin_in
    for index in range(THRESHOLD_RECORD.shape[0]):
        if multiplier <= THRESHOLD_RECORD[index]:
            return index
    return THRESHOLD_RECORD.shape[0] - 1


@njit(nogil=True, cache=True)
def run_free_game_session(record, profile_index, bet_mode, bet_multi, coin_in):
    free_tables = np.full(MAX_FREE_SPINS, -1, dtype=np.int64)
    scheduled = append_free_tables(free_tables, 0, FREE_INITIAL_COUNTS[profile_index], FREE_TABLE_IDS[profile_index])
    spin_index = 0
    cumulative_multiplier = 0
    fg_session_pay = 0
    fg_hit_spins = 0
    fg_cascade_dist = np.zeros(6, dtype=np.int64)

    while spin_index < scheduled and spin_index < MAX_FREE_SPINS:
        fg_table_id = free_tables[spin_index]
        raw_fg, fg_scatter_pay, fg_scatter_count, fg_c2, fg_c2_count, fg_cascades, fg_hits, fg_raw_symbol_pay, fg_bucket_hits, fg_bucket_pay, fg_c2_hits = play_cluster_spin(fg_table_id, profile_index, 1, bet_multi)
        # A multiplier ball is collected only when this spin has a scoring
        # elimination.  Balls shown on a no-win FG screen are not accumulated.
        if raw_fg > 0:
            cumulative_multiplier += fg_c2
        effective_multiplier = cumulative_multiplier if cumulative_multiplier > 0 else 1
        fg_spin_pay = raw_fg * effective_multiplier + fg_scatter_pay
        fg_session_pay += fg_spin_pay
        if fg_spin_pay > 0:
            fg_hit_spins += 1
        fg_cascade_dist[min(fg_cascades, 5)] += 1
        record[R_ALL, RA_FG_SPINS] += 1
        record[R_ALL, RA_HITS_FG] += 1 if fg_spin_pay > 0 else 0
        record[R_ALL, RA_FG_CASCADES] += fg_cascades
        record[R_ALL, RA_C2_COUNT_FG] += fg_c2_count
        record[R_ALL, RA_C2_SPINS_FG] += 1 if fg_c2_count > 0 else 0
        record[R_ALL, RA_SPECIAL_SYMBOL_SPINS] += 1 if fg_scatter_count > 0 else 0
        if cumulative_multiplier > record[R_ALL, RA_MAX_C2_MULTIPLIER]:
            record[R_ALL, RA_MAX_C2_MULTIPLIER] = cumulative_multiplier

        record[R_CASCADE_FG, min(fg_cascades, RECORD_COLS - 1)] += 1
        if fg_c2_count > 0:
            record[R_CASCADE_FG_WITH_BALL, min(fg_cascades, RECORD_COLS - 1)] += 1
        else:
            record[R_CASCADE_FG_WITHOUT_BALL, min(fg_cascades, RECORD_COLS - 1)] += 1
        record[R_SCATTER_FG, min(fg_scatter_count, 7)] += 1
        for symbol in range(SYMBOL_COUNT):
            record[R_SYMBOL_HIT_FG, symbol] += fg_hits[symbol]
            record[R_SYMBOL_PAY_FG, symbol] += fg_raw_symbol_pay[symbol] * effective_multiplier
            for bucket in range(3):
                record[R_SYMBOL_BUCKET_FG_8_9 + bucket, symbol] += fg_bucket_hits[bucket, symbol]
                record[R_SYMBOL_BUCKET_PAY_FG_8_9 + bucket, symbol] += fg_bucket_pay[bucket, symbol] * effective_multiplier
        record[R_SYMBOL_PAY_FG, C1] += fg_scatter_pay
        for index in range(fg_c2_hits.shape[0]):
            record[R_C2_VALUE_FG, index] += fg_c2_hits[index]

        if fg_scatter_count >= FG_RETRIGGER_COUNT and scheduled < MAX_FREE_SPINS:
            previous = scheduled
            scheduled = append_free_tables(free_tables, scheduled, FREE_RETRIGGER_COUNTS[profile_index], FREE_TABLE_IDS[profile_index])
            if scheduled > previous:
                record[R_ALL, RA_RETRIGGER] += 1
        spin_index += 1

    record[R_ALL, RA_PAY_FG] += fg_session_pay
    record[R_ALL, RA_FG_SESSION_MULTIPLIER_SUM] += cumulative_multiplier
    record[R_ALL, RA_FG_SESSION_COUNT] += 1
    # Card System evaluates Buy Feature packages against the Normal Bet base
    # cost, not the 100x purchase price. Keep BF Multiplier Line buckets on
    # that same denominator so the XLSX range model and runtime can round-trip.
    fg_bucket_coin_in = DEFAULT_COIN_IN * NORMALBET * bet_multi if bet_mode == MODE_FEATUREBUY else coin_in
    fg_bucket = get_bucket(fg_session_pay, fg_bucket_coin_in)
    record[R_MULTI_CNT_FG, fg_bucket] += 1
    record[R_MULTI_PAY_FG, fg_bucket] += fg_session_pay
    record[R_FG_INTERVAL_SPINS, fg_bucket] += spin_index
    record[R_FG_INTERVAL_HIT_SPINS, fg_bucket] += fg_hit_spins
    for cascade_index in range(1, 6):
        record[R_FG_INTERVAL_CASCADE_1 + cascade_index - 1, fg_bucket] += fg_cascade_dist[cascade_index]
    return fg_session_pay


@njit(nogil=True, cache=True)
def simulator_chunk(total_round, bet_mode, bet_multi, random_seed):
    np.random.seed(random_seed)
    record = np.zeros(RECORD_SIZE, dtype=np.float64)
    card_system_active = CARD_SYSTEM_ENABLED and bet_mode != MODE_EXTRABET
    profile_index = 0
    if bet_mode == MODE_FEATUREBUY:
        profile_index = 1

    coin_in = DEFAULT_COIN_IN * NORMALBET * bet_multi
    if bet_mode == MODE_EXTRABET:
        coin_in = DEFAULT_COIN_IN * EXTRABET * bet_multi
    elif bet_mode == MODE_FEATUREBUY:
        coin_in = DEFAULT_COIN_IN * FEATUREBUY * bet_multi
    card_coin_in = DEFAULT_COIN_IN * NORMALBET * bet_multi
    bg_card_profile = CARD_PROFILE_NEWBIE_BG if CARD_SYSTEM_IS_NEWBIE else CARD_PROFILE_OLDHAND_BG
    fg_card_profile = CARD_PROFILE_NEWBIE_FG if CARD_SYSTEM_IS_NEWBIE else CARD_PROFILE_OLDHAND_FG
    package_card_profile = CARD_PROFILE_NEWBIE_BUY_FEATURE if CARD_SYSTEM_IS_NEWBIE else CARD_PROFILE_OLDHAND_BUY_FEATURE
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
            if card_system_active:
                if bet_mode == MODE_NORMALBET or bet_mode == MODE_EXTRABET:
                    bg_card_index = pick_card(bg_card_profile)
                    package_card_index = -1
                else:
                    bg_card_index = -1
                    package_card_index = pick_card(package_card_profile)
            else:
                bg_card_index = -1
                package_card_index = -1
        # Card-Off never rejects an attempted round, so copying the full
        # statistics matrix here only burns memory bandwidth.  Keep the
        # snapshot exclusively for Card System retry rollback.
        record_before_attempt = record.copy() if card_system_active else record
        table_id = choose_base_table(profile_index)
        raw_bg, scatter_pay, scatter_count, bg_c2, bg_c2_count, bg_cascades, bg_hits, bg_raw_symbol_pay, bg_bucket_hits, bg_bucket_pay, bg_c2_hits = play_base_spin_for_mode(table_id, profile_index, bet_mode, bet_multi)
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
        record[R_ALL, RA_C2_SPINS_BG] += 1 if bg_c2_count > 0 else 0
        record[R_ALL, RA_SPECIAL_SYMBOL_SPINS] += 1 if scatter_count > 0 else 0
        record[R_ALL, RA_BG_TRIGGER_FG_PAY] += bg_pay if scatter_count >= FG_TRIGGER_COUNT else 0
        if bg_c2 > record[R_ALL, RA_MAX_C2_MULTIPLIER]:
            record[R_ALL, RA_MAX_C2_MULTIPLIER] = bg_c2

        record[R_CASCADE_BG, min(bg_cascades, RECORD_COLS - 1)] += 1
        if bg_c2_count > 0:
            record[R_CASCADE_BG_WITH_BALL, min(bg_cascades, RECORD_COLS - 1)] += 1
        else:
            record[R_CASCADE_BG_WITHOUT_BALL, min(bg_cascades, RECORD_COLS - 1)] += 1
        record[R_SCATTER_BG, min(scatter_count, 7)] += 1
        for symbol in range(SYMBOL_COUNT):
            record[R_SYMBOL_HIT_BG, symbol] += bg_hits[symbol]
            record[R_SYMBOL_PAY_BG, symbol] += bg_raw_symbol_pay[symbol] * bg_multiplier
            for bucket in range(3):
                record[R_SYMBOL_BUCKET_BG_8_9 + bucket, symbol] += bg_bucket_hits[bucket, symbol]
                record[R_SYMBOL_BUCKET_PAY_BG_8_9 + bucket, symbol] += bg_bucket_pay[bucket, symbol] * bg_multiplier
        record[R_SYMBOL_PAY_BG, C1] += scatter_pay
        for index in range(bg_c2_hits.shape[0]):
            record[R_C2_VALUE_BG, index] += bg_c2_hits[index]

        bg_bucket = get_bucket(bg_pay, coin_in)
        record[R_MULTI_CNT_BG, bg_bucket] += 1
        record[R_MULTI_PAY_BG, bg_bucket] += bg_pay
        if bg_cascades > 0:
            record[R_BG_INTERVAL_CASCADE_1 + min(bg_cascades, 5) - 1, bg_bucket] += 1
        if scatter_count >= FG_TRIGGER_COUNT:
            record[R_BG_TRIGGER_FG_CNT, bg_bucket] += 1
            record[R_BG_TRIGGER_FG_PAY, bg_bucket] += bg_pay

        fg_session_pay = 0
        if scatter_count >= FG_TRIGGER_COUNT:
            needs_fg_match = card_system_active and (bet_mode == MODE_NORMALBET or bet_mode == MODE_EXTRABET) and bg_card_index >= 0 and CARD_TYPES[bg_card_profile, bg_card_index] == CARD_TYPE_FREE_GAME
            if needs_fg_match and fg_card_index < 0:
                fg_card_index = pick_card(fg_card_profile)
            record_after_bg = record.copy() if needs_fg_match else record
            fg_retry_count = 0
            while True:
                if needs_fg_match and fg_retry_count > 0:
                    record = record_after_bg.copy()
                record[R_ALL, RA_FG_TRIGGER] += 1
                fg_session_pay = run_free_game_session(record, profile_index, bet_mode, bet_multi, coin_in)
                total_pay = bg_pay + fg_session_pay
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
        overall_bucket = get_bucket(total_pay, card_coin_in if bet_mode == MODE_FEATUREBUY else coin_in)
        record[R_MULTI_CNT_OA, overall_bucket] += 1
        record[R_MULTI_PAY_OA, overall_bucket] += total_pay
        accepted = 1
        fail_reason = 0
        triggered_free_game = 1 if scatter_count >= FG_TRIGGER_COUNT else 0
        if card_system_active:
            if bet_mode == MODE_NORMALBET or bet_mode == MODE_EXTRABET:
                if bg_card_index >= 0 and CARD_TYPES[bg_card_profile, bg_card_index] == CARD_TYPE_FREE_GAME:
                    trigger_cap = CARD_BG_TRIGGER_CAP[bg_card_profile]
                    if triggered_free_game == 0 or trigger_cap < 0 or bg_pay / card_coin_in > trigger_cap:
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
    simulator_chunk(1, bet_mode, bet_multi, 0)
    chunks = split_rounds(total_round, threads)
    if RANDOM_SEED is None:
        root_seed = int.from_bytes(os.urandom(4), "little")
    else:
        root_seed = int(RANDOM_SEED) & 0xFFFFFFFF
    worker_seeds = [int(sequence.generate_state(1, dtype=np.uint32)[0]) for sequence in np.random.SeedSequence(root_seed).spawn(len(chunks))]
    start = time.perf_counter()
    if len(chunks) == 1:
        record = simulator_chunk(chunks[0], bet_mode, bet_multi, worker_seeds[0])
    else:
        with ThreadPoolExecutor(max_workers=len(chunks)) as executor:
            futures = [executor.submit(simulator_chunk, rounds, bet_mode, bet_multi, seed) for rounds, seed in zip(chunks, worker_seeds)]
            record = merge_records([future.result() for future in futures])
    return record, time.perf_counter() - start, calc_coin_in(bet_mode, bet_multi)


def format_threshold_labels(thresholds):
    labels = []
    for index, current in enumerate(thresholds):
        labels.append("0" if index == 0 else f"{thresholds[index - 1]:g} < X <= {current:g}")
    return labels


def combo_rates(counts):
    counts = np.asarray(counts, dtype=np.float64)
    denominator = counts[1:].sum()
    if denominator <= 0:
        return (0.0, 0.0, 0.0, 0.0, 0.0)
    return (
        counts[1] / denominator,
        counts[2] / denominator,
        counts[3] / denominator,
        counts[4] / denominator,
        counts[5:].sum() / denominator,
    )


def build_overview_rows(summary, card_system_active):
    fg_count = int(summary["bg_trigger_fg_cnt"])
    total_rounds = int(summary["total_rounds"])
    fg_cycle = total_rounds / fg_count if fg_count else 0.0
    retrigger_count = int(summary["retrigger_count"])
    fg_spins = float(summary["avg_fg_spins"]) * fg_count
    retrigger_cycle = fg_spins / retrigger_count if retrigger_count else 0.0
    rows = [
        ("game_name", summary["game_name"]),
        ("game_id", summary["game_id"]),
        ("config_file", summary["config_file"]),
        ("config_rtp_file", summary["config_rtp_file"]),
        ("math_version", summary["math_version"]),
        ("card_system", summary["card_system"]),
        ("", ""),
        ("bet_mode", summary["bet_mode"]),
        ("bet_multi", summary["bet_multi"]),
        ("feature_price_multiplier", summary["feature_price_multiplier"]),
        ("base_bet", f"{float(summary['base_bet']):.2f}"),
        ("bet_amount", f"{float(summary['bet_amount']):.2f}"),
        ("bet_tier_amount", f"{float(summary['bet_tier_amount']):.2f}"),
        ("bet_tier", summary["bet_tier"]),
        ("link_enabled", str(bool(summary["link_enabled"])).lower()),
        ("max_multiplier_bg", summary["max_multiplier_bg"]),
        ("max_multiplier_fg", summary["max_multiplier_fg"]),
        ("coin_in", f"{float(summary['coin_in']):.1f}"),
        ("total_rounds", f"{total_rounds:,}"),
        ("duration", f"{float(summary['duration_seconds']):.2f} sec"),
        ("", ""),
        ("rtp_total", f"{float(summary['rtp_total']) * 100:.4f}%"),
        ("rtp_link", f"{float(summary['rtp_link']) * 100:.4f}%"),
        ("rtp_bonus_game", f"{float(summary['rtp_bonus_game']) * 100:.4f}%"),
        ("rtp_game", f"{float(summary['rtp_game']) * 100:.4f}%"),
        ("rtp_bg", f"{float(summary['rtp_bg']) * 100:.4f}%"),
        ("rtp_fg", f"{float(summary['rtp_fg']) * 100:.4f}%"),
        ("hit_rate_bg", f"{float(summary['hit_rate_bg']) * 100:.4f}%"),
        ("hit_rate_fg", f"{float(summary['hit_rate_fg']) * 100:.4f}%"),
        ("fg_trigger_rate", f"{float(summary['fg_trigger_rate']) * 100:.4f}% (cycle {fg_cycle:.2f} spins)"),
        ("retrigger_trigger_rate", f"{float(summary['retrigger_rate']) * 100:.4f}% (cycle {retrigger_cycle:.2f} free spins)"),
        ("avg_fg_spins", f"{float(summary['avg_fg_spins']):.2f} spins"),
        ("", ""),
        ("bg_trigger_fg_cnt", f"{fg_count:,}"),
        ("bg_trigger_fg_pay", f"{float(summary['bg_trigger_fg_pay']):,.0f}"),
        ("special_symbol_cnt", f"{int(summary['special_symbol_cnt']):,}"),
        ("SCR", f"{float(summary['SCR']):,.0f}"),
        ("", ""),
        ("volatility_std", f"{float(summary['volatility_std']):.2f}"),
        ("standard_error", f"{float(summary['standard_error']):.2f}"),
    ]
    if card_system_active:
        rows.extend(
            [
                ("", ""),
                ("card_system_profile", summary["card_system_profile"]),
                ("card_retry_limit", int(summary["card_retry_limit"])),
                ("retry_total", f"{int(summary['retry_total']):,}"),
                ("avg_retry", f"{float(summary['avg_retry']):.2f}"),
                ("", ""),
                ("retry_limit_exceeded", f"{int(summary['retry_limit_exceeded']):,}"),
                ("retry_limit_bg_range", f"{int(summary['retry_limit_bg_range']):,}"),
                ("retry_limit_bg_freegame", f"{int(summary['retry_limit_bg_freegame']):,}"),
                ("retry_limit_fg", f"{int(summary['retry_limit_fg']):,}"),
            ]
        )
    rows.extend(
        [
            ("", ""),
            ("avg_cascades_bg", f"{float(summary['avg_bg_cascades']):.6f}"),
            ("avg_cascades_fg", f"{float(summary['avg_fg_cascades']):.6f}"),
            ("multiplier_ball_rate_bg", f"{float(summary['multiplier_ball_rate_bg']) * 100:.4f}%"),
            ("multiplier_ball_rate_fg", f"{float(summary['multiplier_ball_rate_fg']) * 100:.4f}%"),
            ("avg_multiplier_balls_bg", f"{float(summary['avg_multiplier_balls_bg']):.6f}"),
            ("avg_multiplier_balls_fg", f"{float(summary['avg_multiplier_balls_fg']):.6f}"),
            ("avg_fg_end_multiplier", f"{float(summary['avg_fg_end_multiplier']):.6f}"),
            ("max_win_x", f"{float(summary['max_win_x']):.2f}"),
            ("max_multiplier", int(summary["max_multiplier"])),
        ]
    )
    return rows


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
    card_system_active = CARD_SYSTEM_ENABLED and bet_mode != MODE_EXTRABET
    volatility_std = math.sqrt(max(0.0, variance))
    standard_error = volatility_std / math.sqrt(total_round) if total_round else 0.0
    retrigger_count = values[R_ALL, RA_RETRIGGER]
    special_symbol_cnt = values[R_ALL, RA_SPECIAL_SYMBOL_SPINS]
    scr = special_symbol_cnt / total_round * 10_000_000_000 if total_round else 0.0
    bet_context = build_bet_context(bet_mode, bet_multi)
    player = "newbie" if CARD_SYSTEM_IS_NEWBIE else "oldhand"
    mode_key = "normal_bet" if bet_mode == MODE_NORMALBET else "extra_bet" if bet_mode == MODE_EXTRABET else "buy_feature"
    bg_trigger_cap = get_bg_trigger_cap(player, mode_key, bet_context["bet_tier"])
    bg_trigger_fg_pay = values[R_ALL, RA_BG_TRIGGER_FG_PAY]
    if bg_trigger_cap is not None:
        matching = np.flatnonzero(np.isclose(THRESHOLD_RECORD, bg_trigger_cap, rtol=0.0, atol=1e-12))
        if matching.size != 1:
            raise ValueError(f"BG Trigger Cap {bg_trigger_cap:g} is missing from THRESHOLD_RECORD")
        bg_trigger_fg_pay = np.cumsum(values[R_BG_TRIGGER_FG_PAY, : len(THRESHOLD_RECORD)])[int(matching[0])]
        bet_context["max_multiplier_bg"] = bg_trigger_cap

    summary = {
        "game_id": GAME_ID,
        "parsheet_id": PARSHEET_ID,
        "game_name": GAME_NAME,
        "version": CONFIG_VERSION,
        "math_version": CONFIG_VERSION,
        "config_file": CONFIG_FILE,
        "config_rtp_file": CONFIG_RTP_FILE,
        "rule_document": RULE_DOCUMENT,
        "model_status": MODEL_STATUS,
        "wild_enabled": False,
        "jackpot_enabled": bool(CFG.get("has_jackpot", False)),
        "extra_fg_probability_multiplier": EXTRA_FG_PROBABILITY_MULTIPLIER if bet_mode == MODE_EXTRABET else 1,
        "multiplier_levels": ",".join(str(int(value)) for value in MULTIPLIER_LEVELS),
        "bet_mode": format_bet_mode_label(bet_mode),
        "bet_mode_id": bet_mode,
        "bet_multi": bet_context["bet_multi"],
        "feature_price_multiplier": bet_context["feature_price_multiplier"] if bet_context["feature_price_multiplier"] is not None else "n/a",
        "base_bet": bet_context["base_bet"],
        "bet_amount": bet_context["bet_amount"],
        "bet_tier_amount": bet_context["bet_tier_amount"],
        "bet_tier": bet_context["bet_tier"],
        "link_enabled": bet_context["link_enabled"],
        "max_multiplier_bg": bet_context["max_multiplier_bg"],
        "max_multiplier_fg": bet_context["max_multiplier_fg"],
        "total_rounds": total_round,
        "threads": THREADS,
        "duration_seconds": duration,
        "games_per_second": total_round / duration if duration else 0,
        "coin_in": coin_in,
        "rtp_total": pay_total / coin_in_sum if coin_in_sum else 0,
        "rtp_link": 0.0,
        "rtp_bonus_game": pay_fg / coin_in_sum if coin_in_sum else 0,
        "rtp_game": (pay_bg_cluster + pay_bg_scatter) / coin_in_sum if coin_in_sum else 0,
        "rtp_bg_cluster": pay_bg_cluster / coin_in_sum if coin_in_sum else 0,
        "rtp_bg_scatter": pay_bg_scatter / coin_in_sum if coin_in_sum else 0,
        "rtp_bg": (pay_bg_cluster + pay_bg_scatter) / coin_in_sum if coin_in_sum else 0,
        "rtp_fg": pay_fg / coin_in_sum if coin_in_sum else 0,
        "hit_rate_bg": values[R_ALL, RA_HITS_BG] / total_round,
        "hit_rate_fg": values[R_ALL, RA_HITS_FG] / fg_spins if fg_spins else 0,
        "fg_trigger_rate": fg_sessions / total_round,
        "fg_trigger_count": int(fg_sessions),
        "retrigger_per_fg": retrigger_count / fg_sessions if fg_sessions else 0,
        "retrigger_rate": retrigger_count / fg_spins if fg_spins else 0,
        "retrigger_count": int(retrigger_count),
        "avg_fg_multiplier": (pay_fg / coin_in_sum) / (fg_sessions / total_round) if coin_in_sum and fg_sessions else 0,
        "avg_fg_spins": fg_spins / fg_sessions if fg_sessions else 0,
        "bg_trigger_fg_cnt": int(fg_sessions),
        "bg_trigger_fg_pay": bg_trigger_fg_pay,
        "special_symbol_cnt": int(special_symbol_cnt),
        "SCR": scr,
        "volatility_std": volatility_std,
        "standard_error": standard_error,
        "stddev_x": volatility_std,
        "max_win_x": values[R_ALL, RA_MAX_SINGLE_WIN] / coin_in if coin_in else 0,
        "max_multiplier": int(values[R_ALL, RA_MAX_C2_MULTIPLIER]),
        "avg_bg_cascades": values[R_ALL, RA_BG_CASCADES] / total_round,
        "avg_fg_cascades": values[R_ALL, RA_FG_CASCADES] / fg_spins if fg_spins else 0,
        "multiplier_ball_rate_bg": values[R_ALL, RA_C2_SPINS_BG] / total_round,
        "multiplier_ball_rate_fg": values[R_ALL, RA_C2_SPINS_FG] / fg_spins if fg_spins else 0,
        "avg_multiplier_balls_bg": values[R_ALL, RA_C2_COUNT_BG] / total_round,
        "avg_multiplier_balls_fg": values[R_ALL, RA_C2_COUNT_FG] / fg_spins if fg_spins else 0,
        "avg_fg_end_multiplier": values[R_ALL, RA_FG_SESSION_MULTIPLIER_SUM] / values[R_ALL, RA_FG_SESSION_COUNT] if values[R_ALL, RA_FG_SESSION_COUNT] else 0,
        "card_system": "on" if card_system_active else "off",
        "pending_math_items": " | ".join(PENDING_MATH_ITEMS) if PENDING_MATH_ITEMS else "none",
        "card_system_profile": "off" if not card_system_active else ("newbie" if CARD_SYSTEM_IS_NEWBIE else "oldhand"),
        "card_retry_limit": CARD_RETRY_LIMIT if card_system_active else 0,
        "retry_total": int(values[R_ALL, RA_RETRY_TOTAL]),
        "avg_retry": values[R_ALL, RA_RETRY_TOTAL] / total_round,
        "retry_limit_exceeded": int(values[R_ALL, RA_RETRY_LIMIT_EXCEEDED]),
        "retry_limit_bg_range": int(values[R_ALL, RA_RETRY_FAIL_BG_RANGE]),
        "retry_limit_bg_freegame": int(values[R_ALL, RA_RETRY_FAIL_BG_FREEGAME]),
        "retry_limit_fg": int(values[R_ALL, RA_RETRY_FAIL_FG]),
    }

    overview_rows = build_overview_rows(summary, card_system_active)
    base_frame = pd.DataFrame(overview_rows, columns=["Index", "Value"])
    base_cnt = values[R_MULTI_CNT_BG, : len(THRESHOLD_RECORD)].astype(np.int64)
    free_cnt = values[R_MULTI_CNT_FG, : len(THRESHOLD_RECORD)].astype(np.int64)
    free_pay = values[R_MULTI_PAY_FG, : len(THRESHOLD_RECORD)]
    fg_interval_spins = values[R_FG_INTERVAL_SPINS, : len(THRESHOLD_RECORD)]

    def divide(numerator, denominator):
        numerator = np.asarray(numerator, dtype=np.float64)
        denominator = np.asarray(denominator, dtype=np.float64)
        return np.divide(
            numerator,
            denominator,
            out=np.zeros_like(numerator, dtype=np.float64),
            where=denominator > 0,
        )
    trigger_cnt_lte = np.cumsum(values[R_BG_TRIGGER_FG_CNT, : len(THRESHOLD_RECORD)]).astype(np.int64)
    trigger_pay_lte = np.cumsum(values[R_BG_TRIGGER_FG_PAY, : len(THRESHOLD_RECORD)])
    is_feature_buy = bet_mode == MODE_FEATUREBUY
    package_cnt = values[R_MULTI_CNT_OA, : len(THRESHOLD_RECORD)].astype(np.int64)
    package_pay = values[R_MULTI_PAY_OA, : len(THRESHOLD_RECORD)]
    multiplier_frame = pd.DataFrame(
        {
            "base_game_cnt": base_cnt,
            "base_game_pay": values[R_MULTI_PAY_BG, : len(THRESHOLD_RECORD)],
            "free_game_cnt": np.zeros_like(free_cnt) if is_feature_buy else free_cnt,
            "free_game_pay": np.zeros_like(free_pay) if is_feature_buy else free_pay,
            "free_game_cnt_BF": package_cnt if is_feature_buy else np.zeros_like(package_cnt),
            "free_game_pay_BF": package_pay if is_feature_buy else np.zeros_like(package_pay),
            "Interval_Upper": THRESHOLD_RECORD,
            "bg_trigger_fg_cnt_lte_upper": trigger_cnt_lte,
            "bg_trigger_fg_pay_lte_upper": trigger_pay_lte,
            "FG_Hit_Rate": divide(values[R_FG_INTERVAL_HIT_SPINS, : len(THRESHOLD_RECORD)], fg_interval_spins),
            "FG_Spin_Count": fg_interval_spins.astype(np.int64),
            "BG_Combo_1_Rate": divide(values[R_BG_INTERVAL_CASCADE_1, : len(THRESHOLD_RECORD)], base_cnt),
            "BG_Combo_2_Rate": divide(values[R_BG_INTERVAL_CASCADE_2, : len(THRESHOLD_RECORD)], base_cnt),
            "BG_Combo_3_Rate": divide(values[R_BG_INTERVAL_CASCADE_3, : len(THRESHOLD_RECORD)], base_cnt),
            "BG_Combo_4_Rate": divide(values[R_BG_INTERVAL_CASCADE_4, : len(THRESHOLD_RECORD)], base_cnt),
            "BG_Combo_5+_Rate": divide(values[R_BG_INTERVAL_CASCADE_5P, : len(THRESHOLD_RECORD)], base_cnt),
            "FG_Combo_1_Rate": divide(values[R_FG_INTERVAL_CASCADE_1, : len(THRESHOLD_RECORD)], fg_interval_spins),
            "FG_Combo_2_Rate": divide(values[R_FG_INTERVAL_CASCADE_2, : len(THRESHOLD_RECORD)], fg_interval_spins),
            "FG_Combo_3_Rate": divide(values[R_FG_INTERVAL_CASCADE_3, : len(THRESHOLD_RECORD)], fg_interval_spins),
            "FG_Combo_4_Rate": divide(values[R_FG_INTERVAL_CASCADE_4, : len(THRESHOLD_RECORD)], fg_interval_spins),
            "FG_Combo_5+_Rate": divide(values[R_FG_INTERVAL_CASCADE_5P, : len(THRESHOLD_RECORD)], fg_interval_spins),
        }
    )
    visible_symbol_ids = [int(value) for value in SYMBOL_IDS]
    symbol_frame = pd.DataFrame(
        {
            "Symbol": [ID_TO_CODE[index] for index in visible_symbol_ids],
            "BG_Hit": values[R_SYMBOL_HIT_BG, visible_symbol_ids],
            "BG_Pay": values[R_SYMBOL_PAY_BG, visible_symbol_ids],
            "FG_Hit": values[R_SYMBOL_HIT_FG, visible_symbol_ids],
            "FG_Pay": values[R_SYMBOL_PAY_FG, visible_symbol_ids],
        }
    )
    symbol_bucket_frame = pd.DataFrame(
        {
            "Symbol": [ID_TO_CODE[index] for index in visible_symbol_ids],
            "BG_8_9_Hit": values[R_SYMBOL_BUCKET_BG_8_9, visible_symbol_ids],
            "BG_8_9_Hit_Rate": values[R_SYMBOL_BUCKET_BG_8_9, visible_symbol_ids] / total_round,
            "BG_8_9_Pay": values[R_SYMBOL_BUCKET_PAY_BG_8_9, visible_symbol_ids],
            "BG_10_11_Hit": values[R_SYMBOL_BUCKET_BG_10_11, visible_symbol_ids],
            "BG_10_11_Hit_Rate": values[R_SYMBOL_BUCKET_BG_10_11, visible_symbol_ids] / total_round,
            "BG_10_11_Pay": values[R_SYMBOL_BUCKET_PAY_BG_10_11, visible_symbol_ids],
            "BG_12_Plus_Hit": values[R_SYMBOL_BUCKET_BG_12_PLUS, visible_symbol_ids],
            "BG_12_Plus_Hit_Rate": values[R_SYMBOL_BUCKET_BG_12_PLUS, visible_symbol_ids] / total_round,
            "BG_12_Plus_Pay": values[R_SYMBOL_BUCKET_PAY_BG_12_PLUS, visible_symbol_ids],
            "FG_8_9_Hit": values[R_SYMBOL_BUCKET_FG_8_9, visible_symbol_ids],
            "FG_8_9_Hit_Rate": values[R_SYMBOL_BUCKET_FG_8_9, visible_symbol_ids] / fg_spins if fg_spins else 0,
            "FG_8_9_Pay": values[R_SYMBOL_BUCKET_PAY_FG_8_9, visible_symbol_ids],
            "FG_10_11_Hit": values[R_SYMBOL_BUCKET_FG_10_11, visible_symbol_ids],
            "FG_10_11_Hit_Rate": values[R_SYMBOL_BUCKET_FG_10_11, visible_symbol_ids] / fg_spins if fg_spins else 0,
            "FG_10_11_Pay": values[R_SYMBOL_BUCKET_PAY_FG_10_11, visible_symbol_ids],
            "FG_12_Plus_Hit": values[R_SYMBOL_BUCKET_FG_12_PLUS, visible_symbol_ids],
            "FG_12_Plus_Hit_Rate": values[R_SYMBOL_BUCKET_FG_12_PLUS, visible_symbol_ids] / fg_spins if fg_spins else 0,
            "FG_12_Plus_Pay": values[R_SYMBOL_BUCKET_PAY_FG_12_PLUS, visible_symbol_ids],
        }
    )
    cascade_frame = pd.DataFrame(
        {
            "Cascade_Count": np.arange(20),
            "BG_Count": values[R_CASCADE_BG, :20],
            "FG_Count": values[R_CASCADE_FG, :20],
        }
    )
    multiplier_values = MULTIPLIER_LEVELS
    _, unique_indices = np.unique(multiplier_values, return_index=True)
    valid_indices = np.sort(unique_indices[multiplier_values[unique_indices] > 0])
    c2_frame = pd.DataFrame(
        {
            "Multiplier": multiplier_values[valid_indices],
            "BG_Count": values[R_C2_VALUE_BG, :MULTIPLIER_LEVEL_COUNT][valid_indices],
            "FG_Count": values[R_C2_VALUE_FG, :MULTIPLIER_LEVEL_COUNT][valid_indices],
        }
    )
    scatter_frame = pd.DataFrame(
        {
            "Scatter_Count": ["0", "1", "2", "3", "4", "5", "6", "7+"],
            "BG_Count": values[R_SCATTER_BG, :8],
            "FG_Count": values[R_SCATTER_FG, :8],
        }
    )
    ball_cascade_frame = pd.DataFrame(
        {
            "Cascade_Count": np.arange(20),
            "BG_With_Ball": values[R_CASCADE_BG_WITH_BALL, :20],
            "BG_Without_Ball": values[R_CASCADE_BG_WITHOUT_BALL, :20],
            "FG_With_Ball": values[R_CASCADE_FG_WITH_BALL, :20],
            "FG_Without_Ball": values[R_CASCADE_FG_WITHOUT_BALL, :20],
        }
    )
    return summary, base_frame, multiplier_frame, symbol_frame, cascade_frame, c2_frame, scatter_frame, symbol_bucket_frame, ball_cascade_frame


def format_elapsed_time(seconds):
    total_seconds = max(0, int(round(float(seconds))))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}h {minutes}m {secs}s"


def show_console(summary):
    rows = build_overview_rows(summary, summary["card_system"] == "on")
    labels = [label for label, _ in rows if label]
    width = max(len(label) for label in labels)
    by_game_started = False
    for label, value in rows:
        if label == "avg_cascades_bg" and not by_game_started:
            print("\n<< By Game Info >>\n", flush=True)
            by_game_started = True
        if not label:
            print("", flush=True)
        else:
            print(f"{label:<{width}} : {value}", flush=True)


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


def format_base_version_tag(version):
    text = str(version or "").strip()
    if re.fullmatch(r"\d", text):
        return f"{int(text):02d}"
    raise ValueError(f"Invalid base excel_version: {version!r}")


def format_rtp_version_tag(version):
    parts = str(version or "").strip().split(".")
    if len(parts) != 4 or any(not part.isdigit() or int(part) > 99 for part in parts):
        raise ValueError(f"Invalid RTP excel_version: {version!r}")
    return "".join(f"{int(part):02d}" for part in parts)


def format_rtp_tag(rtp_value):
    return f"{float(rtp_value) * 100:.2f}".replace(".", "")


def output_report(frames, record, bet_mode, total_round):
    summary, base_frame, multiplier_frame, symbol_frame, cascade_frame, c2_frame, scatter_frame, symbol_bucket_frame, ball_cascade_frame = frames
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    card_system_active = CARD_SYSTEM_ENABLED and bet_mode != MODE_EXTRABET
    rounds_tag = format_rounds_tag(total_round)
    if card_system_active:
        report_game_id = str(CFG_RTP.get("model") or CFG_RTP.get("parsheet_id") or GAME_ID)
        version_tag = format_rtp_version_tag(CONFIG_VERSION)
        parts = [report_game_id, version_tag, timestamp, f"betmode{bet_mode}", rounds_tag, format_rtp_tag(summary["rtp_total"])]
        parts.append("newbie" if CARD_SYSTEM_IS_NEWBIE else "oldhand")
        if not CARD_SYSTEM_IS_NEWBIE:
            parts.append(str(summary["bet_tier"]))
        parts.append("card")
    else:
        report_game_id = str(CFG_NATURAL.get("model") or CFG_NATURAL.get("parsheet_id") or GAME_ID)
        parts = [report_game_id, format_base_version_tag(BASE_CONFIG_VERSION), timestamp, f"betmode{bet_mode}", rounds_tag]
    filename = "_".join(parts) + ".xlsx"
    path = OUTPUT_DIR / filename
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        base_frame.to_excel(writer, sheet_name="Overview", index=False)
        multiplier_frame.to_excel(writer, sheet_name="Multiplier Line", index=False)
        symbol_frame.to_excel(writer, sheet_name="Symbol Summary", index=False)
        cascade_frame.to_excel(writer, sheet_name="Cascade", index=False)
        c2_frame.to_excel(writer, sheet_name="C2-C3 Multiplier", index=False)
        scatter_frame.to_excel(writer, sheet_name="Scatter Dist", index=False)
        symbol_bucket_frame.to_excel(writer, sheet_name="Symbol Hit Rate", index=False)
        ball_cascade_frame.to_excel(writer, sheet_name="Ball Cascade", index=False)
        pd.DataFrame(record).to_excel(writer, sheet_name="Record Data", index=False)
        multiplier_sheet = writer.sheets["Multiplier Line"]
        percent_columns = [index + 1 for index, name in enumerate(multiplier_frame.columns) if name.endswith("_Rate")]
        for column in percent_columns:
            for row in range(2, len(multiplier_frame) + 2):
                multiplier_sheet.cell(row=row, column=column).number_format = "0.0000%"
    return path


def run_single_spin_debug():
    profile = PROFILE_BY_MODE[BET_MODE]
    table_id = FEATUREBUY_TABLE_ID if BET_MODE == MODE_FEATUREBUY else BASE_REEL_TABLE_IDS[profile, 0]
    result = play_cluster_spin(table_id, profile, 0, BET_MULTI)
    print("Single spin result:")
    print(f"raw_cluster_pay={result[0]}, scatter_pay={result[1]}, scatter_count={result[2]}")
    print(f"multiplier={result[3]}, multiplier_count={result[4]}, cascades={result[5]}")


def validate_batch_run(combo):
    required = {
        "config_file",
        "config_rtp_file",
        "bet_mode",
        "total_rounds",
        "card_system_enabled",
        "card_system_is_newbie",
        "base_bet",
    }
    missing = sorted(required.difference(combo))
    if missing:
        raise ValueError(f"BATCH_RUNS entry missing fields: {', '.join(missing)}")
    if not isinstance(combo["card_system_enabled"], bool) or not isinstance(combo["card_system_is_newbie"], bool):
        raise TypeError("BATCH_RUNS card system fields must be Boolean")
    if int(combo["total_rounds"]) <= 0:
        raise ValueError("BATCH_RUNS total_rounds must be a positive integer")
    if float(combo["base_bet"]) <= 0:
        raise ValueError("BATCH_RUNS base_bet must be greater than zero")


def run_batch_runs():
    total_jobs = len(BATCH_RUNS)
    for index, combo in enumerate(BATCH_RUNS, start=1):
        validate_batch_run(combo)
        print(f"\n=== Batch {index}/{total_jobs}: {combo} ===", flush=True)
        env = os.environ.copy()
        env["H027_CONFIG_FILE"] = combo["config_file"]
        env["H027_CONFIG_RTP_FILE"] = combo["config_rtp_file"]
        env["H027_BET_MODE"] = str(combo["bet_mode"])
        env["H027_TOTAL_ROUNDS"] = str(combo["total_rounds"])
        env["H027_CARD_SYSTEM_ENABLED"] = "true" if combo.get("card_system_enabled", CARD_SYSTEM_ENABLED) else "false"
        env["H027_CARD_SYSTEM_IS_NEWBIE"] = "true" if combo.get("card_system_is_newbie", CARD_SYSTEM_IS_NEWBIE) else "false"
        env["H027_BASE_BET"] = str(combo["base_bet"])
        env["H027_RUN_ALL_COMBINATIONS"] = "false"
        env["H027_BATCH_CHILD"] = "1"
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
    if RUN_ALL_COMBINATIONS and os.environ.get("H027_BATCH_CHILD") != "1":
        run_batch_runs()
        return
    if RUN_SINGLE_SPIN_DEBUG:
        run_single_spin_debug()
        return

    if os.environ.get("H027_BATCH_CHILD") != "1":
        current_batch = {
            "config_file": CONFIG_FILE,
            "config_rtp_file": CONFIG_RTP_FILE,
            "bet_mode": BET_MODE,
            "total_rounds": TOTAL_ROUNDS,
            "card_system_enabled": CARD_SYSTEM_ENABLED,
            "card_system_is_newbie": CARD_SYSTEM_IS_NEWBIE,
            "base_bet": BASE_BET,
        }
        print(f"=== Batch 1/1: {current_batch} ===\n", flush=True)
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
