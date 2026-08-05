# %%
import json
import math
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from multiprocessing import Pool, cpu_count
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

# ===== User Settings =====

CONFIG_FILE = "config_92A.js"
TOTAL_ROUNDS = 10**7
BET_MODE = 0  # 0 for Normal Bet, 2 for Buy Feature; 101016 has no Extra Bet
BET_MULTI = 1
ENABLE_M1_MULTIPLIER = True
FG_INITIAL_MULTIPLIER = 2
CARD_SYSTEM_ENABLED = True
CARD_SYSTEM_IS_NEWBIE = False  # True for newbie, False for oldhand

RUN_ALL_COMBINATIONS = True
BATCH_RUNS = [
    {"config_file": "config_92A.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": False, "card_system_is_newbie": False},
    # {"config_file": "config_92A.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},
    # {"config_file": "config_92A.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    # {"config_file": "config_94A.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},
    # {"config_file": "config_94A.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    # {"config_file": "config_92B.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},
    # {"config_file": "config_92B.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    # {"config_file": "config_94B.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},
    # {"config_file": "config_94B.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    # {"config_file": "config_92A.js", "bet_mode": 2, "total_rounds": 10**7, "card_system_enabled": True, "card_system_is_newbie": False},
]

THREADS = max(1, max(8, os.cpu_count() - 2 or 1))
OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = False
SHOW_CONSOLE_DETAIL = False
RUN_SINGLE_SPIN_DEBUG = False

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
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on"}


CONFIG_FILE = os.environ.get("H028_CONFIG_FILE", CONFIG_FILE)


def resolve_base_dir():
    cwd = Path.cwd().resolve()
    candidates = []

    base_dir_override = os.environ.get("H028_BASE_DIR")
    if base_dir_override:
        candidates.append(Path(base_dir_override).expanduser().resolve())

    file_value = globals().get("__file__")
    if file_value:
        file_parent = Path(file_value).resolve().parent
        candidates.append(file_parent)
    else:
        file_parent = None

    candidates.append(cwd)
    anchors = [cwd, *cwd.parents]
    if file_parent is not None:
        anchors.extend([file_parent, *file_parent.parents])
    for anchor in anchors:
        candidates.extend(
            [
                anchor / "H028_雷神爆金 1000",
                anchor / "Slots" / "H028_雷神爆金 1000",
                anchor / "Project_AI" / "Slots" / "H028_雷神爆金 1000",
            ]
        )

    checked = []
    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        candidate_key = os.path.normcase(str(candidate))
        if candidate_key in seen:
            continue
        seen.add(candidate_key)
        checked.append(str(candidate / CONFIG_FILE))
        if (candidate / CONFIG_FILE).is_file():
            return candidate
    raise FileNotFoundError(f"Cannot locate {CONFIG_FILE}. Checked: " + " | ".join(checked))


BASE_DIR = resolve_base_dir()
SIMULATOR_PATH = BASE_DIR / "Simulator.py"
OUTPUT_DIR = BASE_DIR / "Record"
CONFIG_PATH = BASE_DIR / CONFIG_FILE
TOTAL_ROUNDS = int(os.environ.get("H028_TOTAL_ROUNDS", str(TOTAL_ROUNDS)))
BET_MODE = int(os.environ.get("H028_BET_MODE", str(BET_MODE)))
BET_MULTI = int(os.environ.get("H028_BET_MULTI", str(BET_MULTI)))
THREADS = int(os.environ.get("H028_THREADS", str(THREADS)))
RUN_ALL_COMBINATIONS = parse_env_bool("H028_RUN_ALL_COMBINATIONS", RUN_ALL_COMBINATIONS)
OUTPUT_REPORT = parse_env_bool("H028_OUTPUT_REPORT", OUTPUT_REPORT)
SHOW_CONSOLE_SUMMARY = parse_env_bool("H028_SHOW_CONSOLE_SUMMARY", SHOW_CONSOLE_SUMMARY)
SHOW_CONSOLE_DETAIL = parse_env_bool("H028_SHOW_CONSOLE_DETAIL", SHOW_CONSOLE_DETAIL)
RUN_SINGLE_SPIN_DEBUG = parse_env_bool("H028_RUN_SINGLE_SPIN_DEBUG", RUN_SINGLE_SPIN_DEBUG)
ENABLE_M1_MULTIPLIER = parse_env_bool("H028_ENABLE_M1_MULTIPLIER", ENABLE_M1_MULTIPLIER)
CARD_SYSTEM_ENABLED = parse_env_bool("H028_CARD_SYSTEM_ENABLED", CARD_SYSTEM_ENABLED)
CARD_SYSTEM_IS_NEWBIE = parse_env_bool("H028_CARD_SYSTEM_IS_NEWBIE", CARD_SYSTEM_IS_NEWBIE)


def load_js_config(path):
    content = path.read_text(encoding="utf-8").strip()
    match = re.match(r"^(?:const|let|var)\s+\w+\s*=\s*(.*?);?\s*$", content, re.DOTALL)
    if match:
        content = match.group(1)
    return json.loads(content)


data = load_js_config(CONFIG_PATH)
GAME_ID = str(data.get("game_id", "101016"))
PARSHEET_ID = str(data.get("parsheet_id", "H0281"))
GAME_NAME = str(data.get("display_name", "Thunder Boost 1000"))
GAME_NAME_ZH = str(data.get("game_name_zh", "雷神爆金1000"))
CONFIG_VERSION = str(data.get("excel_version", "1.0.0.1"))
DEFAULT_COIN_IN = int(data.get("default_coin_in", 100))
MODE_NORMALBET = int(data.get("mode_normalbet", 0))
MODE_EXTRABET = int(data.get("mode_extrabet", 1))
MODE_FEATUREBUY = int(data.get("mode_featurebuy", 2))
NORMALBET = int(data.get("normalbet", 1))
FEATUREBUY = int(data.get("featurebuy", 75))
SUPPORTED_BET_MODES = tuple(int(value) for value in data.get("supported_bet_modes", [MODE_NORMALBET]))

# Card system: draw one target card, then retry generated results until they
# match the selected interval.  The denominator always uses Normal Bet coin-in.
CARD_SYSTEM = data.get("card_system", {})
CARD_SYSTEM_ENABLED = CARD_SYSTEM_ENABLED and bool(CARD_SYSTEM.get("enabled", False))
CARD_RETRY_LIMIT = max(1, int(CARD_SYSTEM.get("retry_limit", 5000)))
CARD_TYPE_RANGE = 0
CARD_TYPE_FREE_GAME = 1
CARD_PROFILE_NEWBIE_BG = 0
CARD_PROFILE_NEWBIE_FG = 1
CARD_PROFILE_OLDHAND_BG = 2
CARD_PROFILE_OLDHAND_FG = 3
CARD_PROFILE_BUY_FEATURE = 4


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
        running_weight += max(0, int(card.get("weight", 0)))
        CARD_TYPES[card_profile_index, card_index] = CARD_TYPE_FREE_GAME if card.get("type") == "free_game" else CARD_TYPE_RANGE
        CARD_MIN[card_profile_index, card_index] = float(card.get("min", 0.0))
        CARD_MAX[card_profile_index, card_index] = float(card.get("max", 0.0))
        CARD_WEIGHT_CUM[card_profile_index, card_index] = running_weight
    CARD_COUNTS[card_profile_index] = len(cards)

# ========== 預處理參數為 numpy 數組 ==========
# 將所有參數轉為 numpy 數組以便 numba 使用

# ReelWeight
REEL_WEIGHT = np.array(data["ReelWeight"], dtype=np.float64)

# linkpoint: [11符號][4連線] M1-M6,A,K,Q,J,TE 的 3,4,5,6 連線得分
LINKPOINT = np.array(data["linkpoint"], dtype=np.float64)

# MegaWay 15種情況 (轉為固定大小數組，用-1填充)
MEGAWAY_PATTERNS = np.array(
    [[4, 1, -1, -1, -1], [1, 4, -1, -1, -1], [3, 2, -1, -1, -1], [2, 3, -1, -1, -1], [3, 1, 1, -1, -1], [1, 3, 1, -1, -1], [1, 1, 3, -1, -1], [2, 2, 1, -1, -1], [2, 1, 2, -1, -1], [1, 2, 2, -1, -1], [2, 1, 1, 1, -1], [1, 2, 1, 1, -1], [1, 1, 2, 1, -1], [1, 1, 1, 2, -1], [1, 1, 1, 1, 1]],
    dtype=np.int32,
)

# 盤面高度: R1-R6=5, R7=4 (與後端 "5555554" 版面一致)
TARGET_HEIGHTS = np.array([5, 5, 5, 5, 5, 5, 4], dtype=np.int32)


def prepare_param_arrays(suffix):
    """準備指定參數組的 numpy 數組 (BaseGame)"""
    # Symbol reels: 7條輪帶，每條最多121個符號
    symbol_reels_list = data[f"BaseGameSymbol{suffix}"]
    max_len = max(len(r) for r in symbol_reels_list)
    symbol_reels = np.full((7, max_len), -1, dtype=np.int32)
    reel_lengths = np.zeros(7, dtype=np.int32)
    for i, reel in enumerate(symbol_reels_list):
        symbol_reels[i, : len(reel)] = np.array(reel, dtype=np.int32)
        reel_lengths[i] = len(reel)

    # Weight reels
    weight_reels_list = data[f"BaseGameSymbolWeight{suffix}"]
    weight_reels = np.full((7, max_len), 0.0, dtype=np.float64)
    for i, reel in enumerate(weight_reels_list):
        weight_reels[i, : len(reel)] = np.array(reel, dtype=np.float64)

    # MegaWay weights: 6x15
    megaway_weights = np.array(data[f"BaseGameMegaWay{suffix}"], dtype=np.float64)

    # MY weights
    my_weights = np.array(data[f"BaseGameMY{suffix}"], dtype=np.float64)

    # PostC1 weights (取第二行的權重，第一行是值但恰好等於索引)
    post_c1_data = data[f"BaseGame{suffix}PostC1"]
    post_c1_weights = np.array(post_c1_data[1], dtype=np.float64)

    # Drop weights: 5組，每組7條輪帶x26符號
    drop_weights = np.zeros((5, 7, 26), dtype=np.float64)
    for d in range(5):
        drop_data = data[f"BaseGame{suffix}Drop{d+1}"]
        for r in range(7):
            arr = np.array(drop_data[r], dtype=np.float64)
            drop_weights[d, r, : len(arr)] = arr

    return symbol_reels, reel_lengths, weight_reels, megaway_weights, my_weights, post_c1_weights, drop_weights


def prepare_freegame_param_arrays(suffix):
    """準備指定參數組的 numpy 數組 (FreeGame)"""
    # Symbol reels: 7條輪帶
    symbol_reels_list = data[f"FreeGameSymbol{suffix}"]
    max_len = max(len(r) for r in symbol_reels_list)
    symbol_reels = np.full((7, max_len), -1, dtype=np.int32)
    reel_lengths = np.zeros(7, dtype=np.int32)
    for i, reel in enumerate(symbol_reels_list):
        symbol_reels[i, : len(reel)] = np.array(reel, dtype=np.int32)
        reel_lengths[i] = len(reel)

    # Weight reels
    weight_reels_list = data[f"FreeGameSymbolWeight{suffix}"]
    weight_reels = np.full((7, max_len), 0.0, dtype=np.float64)
    for i, reel in enumerate(weight_reels_list):
        weight_reels[i, : len(reel)] = np.array(reel, dtype=np.float64)

    # MegaWay weights: 6x15
    megaway_weights = np.array(data[f"FreeGameMegaWay{suffix}"], dtype=np.float64)

    # MY weights
    my_weights = np.array(data[f"FreeGameMY{suffix}"], dtype=np.float64)

    # PostC1 weights (處理不同格式: 1D 或 2D)
    post_c1_data = data[f"FreeGame{suffix}PostC1"]
    if isinstance(post_c1_data[0], list):
        # 2D 格式 [[values], [weights]]
        post_c1_weights = np.array(post_c1_data[1], dtype=np.float64)
    else:
        # 1D 格式 [weights]
        post_c1_weights = np.array(post_c1_data, dtype=np.float64)

    # Drop weights: 5組，每組7條輪帶x26符號
    drop_weights = np.zeros((5, 7, 26), dtype=np.float64)
    for d in range(5):
        drop_data = data[f"FreeGame{suffix}Drop{d+1}"]
        for r in range(7):
            arr = np.array(drop_data[r], dtype=np.float64)
            drop_weights[d, r, : len(arr)] = arr

    return symbol_reels, reel_lengths, weight_reels, megaway_weights, my_weights, post_c1_weights, drop_weights


# 預先準備三套參數；第 3 套僅供 Feature Buy 觸發盤面使用。
_p1 = prepare_param_arrays(1)
_p2 = prepare_param_arrays(2)
_p3 = prepare_param_arrays(3)

# 參數組1
SYMBOL_REELS_1 = _p1[0]
REEL_LENGTHS_1 = _p1[1]
WEIGHT_REELS_1 = _p1[2]
MEGAWAY_WEIGHTS_1 = _p1[3]
MY_WEIGHTS_1 = _p1[4]
POST_C1_WEIGHTS_1 = _p1[5]
DROP_WEIGHTS_1 = _p1[6]

# 參數組2
SYMBOL_REELS_2 = _p2[0]
REEL_LENGTHS_2 = _p2[1]
WEIGHT_REELS_2 = _p2[2]
MEGAWAY_WEIGHTS_2 = _p2[3]
MY_WEIGHTS_2 = _p2[4]
POST_C1_WEIGHTS_2 = _p2[5]
DROP_WEIGHTS_2 = _p2[6]

# 參數組3（BF_Symbol）
SYMBOL_REELS_3 = _p3[0]
REEL_LENGTHS_3 = _p3[1]
WEIGHT_REELS_3 = _p3[2]
MEGAWAY_WEIGHTS_3 = _p3[3]
MY_WEIGHTS_3 = _p3[4]
POST_C1_WEIGHTS_3 = _p3[5]
DROP_WEIGHTS_3 = _p3[6]

# FreeGame 參數組
_fp1 = prepare_freegame_param_arrays(1)
_fp2 = prepare_freegame_param_arrays(2)
_fp3 = prepare_freegame_param_arrays(3)

# FreeGame 參數組1
FG_SYMBOL_REELS_1 = _fp1[0]
FG_REEL_LENGTHS_1 = _fp1[1]
FG_WEIGHT_REELS_1 = _fp1[2]
FG_MEGAWAY_WEIGHTS_1 = _fp1[3]
FG_MY_WEIGHTS_1 = _fp1[4]
FG_POST_C1_WEIGHTS_1 = _fp1[5]
FG_DROP_WEIGHTS_1 = _fp1[6]

# FreeGame 參數組2
FG_SYMBOL_REELS_2 = _fp2[0]
FG_REEL_LENGTHS_2 = _fp2[1]
FG_WEIGHT_REELS_2 = _fp2[2]
FG_MEGAWAY_WEIGHTS_2 = _fp2[3]
FG_MY_WEIGHTS_2 = _fp2[4]
FG_POST_C1_WEIGHTS_2 = _fp2[5]
FG_DROP_WEIGHTS_2 = _fp2[6]

# FreeGame 參數組3
FG_SYMBOL_REELS_3 = _fp3[0]
FG_REEL_LENGTHS_3 = _fp3[1]
FG_WEIGHT_REELS_3 = _fp3[2]
FG_MEGAWAY_WEIGHTS_3 = _fp3[3]
FG_MY_WEIGHTS_3 = _fp3[4]
FG_POST_C1_WEIGHTS_3 = _fp3[5]
FG_DROP_WEIGHTS_3 = _fp3[6]

# FreeReelWeight 權重 (用於初始場次選擇參數組)
FREE_REEL_WEIGHT = np.array(data["FreeReelWeight"], dtype=np.float64)

# FreeTriggerReel 權重 (用於 retrigger 時選擇參數組)
FREE_TRIGGER_REEL = np.array(data["FreeTriggerReel"], dtype=np.float64)

# ========== Numba 加速函數 ==========


@njit(nogil=True)
def weighted_choice_numba(weights):
    """根據權重隨機選擇索引 (numba 版本)"""
    total = np.sum(weights)
    n = len(weights)
    if total == 0:
        return np.int32(np.random.randint(0, n))
    r = np.random.random() * total
    cumsum = 0.0
    for i in range(n):
        cumsum += weights[i]
        if r < cumsum:
            return np.int32(i)
    return np.int32(n - 1)


@njit(nogil=True)
def comb_count_numba(n, k):
    """C(n, k) 組合數 (整數)，等價後端 buildCombinations 列舉出的組合總數"""
    if k < 0 or k > n:
        return 0
    if k > n - k:
        k = n - k
    result = 1
    for i in range(k):
        result = result * (n - i) // (i + 1)
    return result


@njit(nogil=True)
def pick_combination_numba(n, k, out):
    """依字典序列舉 C(n,k) 後等機率抽一組，結果(升冪)寫入 out[0..k-1]。
    等價後端 applyPostScatter 的選輪流程：buildCombinations(字典序列舉) + pickEvenly(均權抽 index)。
    此處以組合 unranking 直接算出第 m 組，避免建整份清單(結果分布完全相同)。"""
    total = comb_count_numba(n, k)
    m = np.random.randint(0, total)  # 均勻抽 rank(0..total-1)，等同 pickEvenly 均權
    x = 0
    rem = k
    for i in range(k):
        while True:
            cnt = comb_count_numba(n - x - 1, rem - 1)  # 以 x 開頭的組合數
            if m < cnt:
                out[i] = np.int32(x)
                x += 1
                rem -= 1
                break
            else:
                m -= cnt
                x += 1


@njit(nogil=True)
def single_spin_core(symbol_reels, reel_lengths, weight_reels, megaway_weights, my_weights, post_c1_weights, drop_weights, megaway_patterns, linkpoint, target_heights, enable_m1_multiplier):
    """執行單次 spin 核心計算 (numba 版本)"""
    # 生成初始盤面
    board = np.full((7, 6), -1, dtype=np.int32)
    lengths = np.full((7, 6), 0, dtype=np.int32)

    # R1-R6
    for reel_idx in range(6):
        pattern_idx = int(weighted_choice_numba(megaway_weights[reel_idx]))
        pattern = megaway_patterns[pattern_idx]
        start_pos = int(weighted_choice_numba(weight_reels[reel_idx, : reel_lengths[reel_idx]]))

        pos = 0
        symbol_pos = start_pos
        for p in range(5):
            length = int(pattern[p])
            if length < 0:
                break
            symbol = symbol_reels[reel_idx, symbol_pos % reel_lengths[reel_idx]]
            # head 存高度，延續格存 0 (與後端 linkScreenSymbol 一致)
            for k in range(length):
                if pos < 6:
                    board[reel_idx, pos] = symbol
                    lengths[reel_idx, pos] = np.int32(length) if k == 0 else 0
                    pos += 1
            symbol_pos += length

    # R7: 4個符號
    r7_start = int(weighted_choice_numba(weight_reels[6, : reel_lengths[6]]))
    for i in range(4):
        symbol = symbol_reels[6, (r7_start + i) % reel_lengths[6]]
        board[6, i] = symbol
        lengths[6, i] = np.int32(1)

    # 模擬後端 convertToMegaWaysScreenLabel：R1-R6 符號下移一行，R7 移到 row0
    # 1. R1-R6 所有符號下移一行
    for reel_idx in range(6):
        for pos in range(5, 0, -1):  # 5,4,3,2,1
            board[reel_idx, pos] = board[reel_idx, pos - 1]
            lengths[reel_idx, pos] = lengths[reel_idx, pos - 1]
        board[reel_idx, 0] = np.int32(-1)  # row0 先清空
        lengths[reel_idx, 0] = 0

    # 2. R7 的 4 個符號移到 R2-R5 的 row0
    for i in range(4):
        board[i + 1, 0] = board[6, i]
        lengths[i + 1, 0] = 1

    # 轉換 MY 符號
    # MY 權重索引對應: 0=Wild, 1=C1, 2=M1, 3=M2, ..., 12=TE
    target_idx = int(weighted_choice_numba(my_weights))
    my_target_symbol = np.int32(target_idx)  # 索引直接就是符號 ID (用獨立變數避免被消除循環覆蓋)
    for r in range(7):
        for c in range(6):
            if board[r, c] == 24:
                board[r, c] = my_target_symbol
            elif board[r, c] == 25:
                board[r, c] = np.int32(my_target_symbol + 11)

    # C1 替換：從 C(7, N) 隨機選擇輪帶替換
    # 注意：MegaWay 符號現在在 row 1-5，row 0 是 R7
    c1_count = int(weighted_choice_numba(post_c1_weights))
    if c1_count > 0:
        # 與後端 applyPostScatter 同步：列舉 C(7, c1_count) 所有組合(字典序)後等機率抽一組
        # (等價後端 buildCombinations 字典序列舉 + pickEvenly 均權抽 index)
        chosen_reels = np.full(7, -1, dtype=np.int32)
        pick_combination_numba(7, c1_count, chosen_reels)

        # 某輪若無可替換符號則該顆 C1 不補 (與後端選定 C(7,N) 後 continue 的行為一致)
        for idx in range(c1_count):
            r = chosen_reels[idx]
            if r == 6:
                # R7：算分/觸發都以「已併入 R2~R5 row0」的盤面為準，
                # 因此 C1 必須寫進合併後的計分格 board[1..4, 0]，而非 R7 原始輪 board[6, *]，
                # 否則替換對算分與 c1_final(觸發判定) 都不生效，原符號還會照樣計分。
                # (R7 符號皆為 1x1，最短長度恆為 1；複數候選時等機率隨機抽)
                cand_reels = np.full(4, -1, dtype=np.int32)
                n_cand = 0
                for i in range(4):
                    if board[i + 1, 0] != -1:  # 有效符號即可 (與後端一致：只檢查 link>0)
                        cand_reels[n_cand] = i + 1
                        n_cand += 1
                if n_cand == 0:
                    continue  # R7 無有效符號
                target_reel = cand_reels[np.random.randint(0, n_cand)]
                board[target_reel, 0] = np.int32(1)
                continue
            # R1~R6：在 pos 1~5 的 MegaWay 符號中替換 (row 0 是 R7)
            # 找出該輪帶最短長度 (與後端一致：只檢查 link>0，不排除任何符號)
            min_len = 99
            c = 1  # 從 row 1 開始
            while c < 6:
                L = lengths[r, c]
                if L <= 0:
                    c += 1
                    continue
                if L < min_len:
                    min_len = L
                c += L
            if min_len == 99:
                continue  # 該輪帶無有效符號
            # 收集所有「最短長度」大符號 block 的起始位置 (head)
            cand_heads = np.full(6, -1, dtype=np.int32)
            n_cand = 0
            c = 1  # 從 row 1 開始 (row 0 是 R7)
            while c < 6:
                L = lengths[r, c]
                if L <= 0:
                    c += 1
                    continue
                if L == min_len:
                    cand_heads[n_cand] = c
                    n_cand += 1
                c += L
            # 複數最短長度時，等機率隨機抽一個 block (與後端一致)
            head = cand_heads[np.random.randint(0, n_cand)]
            # 將整個大符號 block 替換為 C1 (等同後端 head 變 C1、維持高度)
            for cc in range(head, head + min_len):
                if cc < 6:
                    board[r, cc] = np.int32(1)

    # 記錄初始盤面 C1 數量和長度分布 (C1 替換後、消除前)
    init_c1_count = 0
    init_c1_len_counts = np.zeros(4, dtype=np.int32)  # [len1, len2, len3, len4]
    for reel_idx in range(6):
        # 依 lengths 逐 block 走訪，每個 C1 block head 各算 1 個 (與後端 link>0 計 head 一致)
        c = 0
        while c < 6:
            sym = board[reel_idx, c]
            L = lengths[reel_idx, c]
            if sym == -1 or L <= 0:
                c += 1
                continue
            if sym == 1:  # C1
                init_c1_count += 1
                if 1 <= L <= 4:
                    init_c1_len_counts[L - 1] += 1
            c += L

    # R7 的 C1 已於上方主迴圈 (reels 1~4 的 row0) 計入，與 c1_final 計數方式一致，
    # 不再額外掃描 R7 原始輪 board[6, *] (該處在 PostScatter 後仍為原符號，不會是 C1)。

    # M1 倍數累加 (初始盤面)
    # M1=2, GM1=13, 長度1=+2, 長度2=+3, 長度3=+4, 長度4=+5
    # BG 第一顆 M1 用大小建立倍數：1x1 使 x1→x2、2x1 使 x1→x3，以此類推。
    # 後續 M1 才完整累加其標示倍數。
    multiplier = 1.0
    m1_count = 0

    if enable_m1_multiplier:
        for reel_idx in range(6):
            pos = 0
            while pos < 6:
                sym = board[reel_idx, pos]
                L = lengths[reel_idx, pos]
                if sym == -1 or L <= 0:
                    pos += 1
                    continue
                if sym == 2 or sym == 13:  # M1 或 GM1
                    bonus = L + 1  # 長度1=+2, 長度2=+3...
                    if m1_count == 0:
                        bonus -= 1
                    multiplier += bonus
                    m1_count += 1
                pos += L

    # R7 的 M1 已於上方主迴圈 (reels 1~4 的 row 0，R7 移位後位置) 計入，
    # 此處不再額外累加，避免同一顆 R7 的 M1 被重複計算兩次倍數。

    total_win = 0.0
    drop_count = 0
    max_drops = 50  # 安全上限
    cascade_scores = np.zeros(5, dtype=np.float64)

    # 消除循環
    while drop_count < max_drops:
        # 檢查消除
        score = 0.0
        wins = np.zeros((11, 3), dtype=np.int32)
        win_count = 0

        for target_symbol in range(2, 13):
            consecutive_reels = 0
            ways = 1
            gold_symbol = target_symbol + 11

            for reel_idx in range(6):
                matching = 0
                # 依 lengths 逐 MegaWay block 走訪；大型符號無論覆蓋幾格，
                # 在 Ways 計算中只視為一個符號。
                c = 0
                while c < 6:
                    sym = board[reel_idx, c]
                    L = lengths[reel_idx, c]
                    if sym == -1 or L <= 0:
                        c += 1
                        continue
                    if sym == target_symbol or sym == gold_symbol or sym == 0:
                        matching += 1
                    c += L

                if matching > 0:
                    consecutive_reels += 1
                    ways *= matching
                else:
                    break

            if consecutive_reels >= 3:
                symbol_idx = target_symbol - 2
                line_idx = consecutive_reels - 3
                base_score = linkpoint[symbol_idx, line_idx]
                score += base_score * ways
                wins[win_count, 0] = target_symbol
                wins[win_count, 1] = consecutive_reels
                wins[win_count, 2] = ways
                win_count += 1

        if win_count == 0:
            break

        # 得分乘以倍數
        cascade_round = min(drop_count, 4)
        cascade_scores[cascade_round] += score * multiplier
        total_win += score * multiplier
        drop_count += 1
        drop_idx = min(drop_count, 5) - 1

        # 移除並補充
        to_remove = np.zeros((7, 6), dtype=np.int32)
        gold_win_head = np.zeros((7, 6), dtype=np.int32)  # 兩階段修正:記錄中獎金框head
        # Pass1: 用原始盤面標記所有消除(不即時mutate board),避免中獎金框轉Wild後被後面符號誤消
        for w in range(win_count):
            target_symbol = wins[w, 0]
            reels_count = wins[w, 1]
            gold_symbol = target_symbol + 11
            for reel_idx in range(reels_count):
                pos = 0
                while pos < 6:
                    sym = board[reel_idx, pos]
                    L = lengths[reel_idx, pos]
                    if sym == -1 or L <= 0:
                        pos += 1
                        continue
                    if sym == target_symbol or sym == gold_symbol or sym == 0:
                        for k in range(L):
                            if pos + k < 6:
                                to_remove[reel_idx, pos + k] = 1
                        if sym >= 13 and sym <= 23:
                            gold_win_head[reel_idx, pos] = 1
                    pos += L
        # Pass2: 中獎金框整塊轉Wild並取消其消除(存活),對齊後端 calculateChangeWildScreen
        for reel_idx in range(6):
            pos = 0
            while pos < 6:
                L = lengths[reel_idx, pos]
                if L > 0:
                    if gold_win_head[reel_idx, pos] == 1:
                        for k in range(L):
                            if pos + k < 6:
                                board[reel_idx, pos + k] = 0
                                to_remove[reel_idx, pos + k] = 0
                    pos += L
                else:
                    pos += 1

        # 記錄補充前的位置，用於檢測新 M1
        old_fill_pos = np.zeros(7, dtype=np.int32)

        # R1-R6 主盤面垂直掉落 (row 1-5，row 0 是 R7)
        # Java 順序: 新符號在底部 (row 1-消除數量)，保留符號在頂部 (row 消除數量+1 到末尾)
        for reel_idx in range(6):
            target_height = target_heights[reel_idx]

            # 收集存活符號列表 (row 1-5)，以區塊為單位
            survive_symbols = np.full(6, -1, dtype=np.int32)
            survive_lens = np.zeros(6, dtype=np.int32)
            survive_count = 0
            pos = 1
            while pos < 6:
                sym = board[reel_idx, pos]
                L = lengths[reel_idx, pos]
                if sym == -1:
                    pos += 1
                    continue
                if L > 0:  # 是 head
                    if to_remove[reel_idx, pos] == 0:  # 未被移除
                        # 複製整個區塊
                        for k in range(L):
                            if pos + k < 6:
                                survive_symbols[survive_count] = board[reel_idx, pos + k]
                                survive_lens[survive_count] = L if k == 0 else 0
                                survive_count += 1
                    pos += L
                else:
                    pos += 1

            # 計算消除數量 (要補充的新符號數量)
            # MegaWays 填充區域是 row 1-5 (5格)，row 0 由 R7 水平掉落邏輯單獨處理
            eliminate_count = target_height - survive_count

            new_reel = np.full(6, -1, dtype=np.int32)
            new_len = np.zeros(6, dtype=np.int32)

            # 按 Java 順序填充: 先新符號 (row 1 到 eliminate_count)，再保留符號
            new_pos = 1

            # 先填充新符號
            for _ in range(eliminate_count):
                if new_pos >= 6:
                    break
                new_symbol = np.int32(weighted_choice_numba(drop_weights[drop_idx, reel_idx]))
                # cascade掉落若補到MY/G_MY，沿用本局抽到的轉換symbol(與後端 replaceMysterySymbol 一致)
                if new_symbol == 24:
                    new_symbol = my_target_symbol
                elif new_symbol == 25:
                    new_symbol = np.int32(my_target_symbol + 11)
                new_reel[new_pos] = new_symbol
                new_len[new_pos] = 1  # 補充符號皆 1x1
                # 檢查新補充的 M1 (補充符號長度都是 1)
                if enable_m1_multiplier and (new_symbol == 2 or new_symbol == 13):
                    bonus = 2  # 長度1=+2
                    if m1_count == 0:
                        bonus -= 1
                    multiplier += bonus
                    m1_count += 1
                new_pos += 1

            old_fill_pos[reel_idx] = new_pos  # 記錄補充結束位置

            # 再填充保留符號
            for si in range(survive_count):
                if new_pos >= 6:
                    break
                new_reel[new_pos] = survive_symbols[si]
                new_len[new_pos] = survive_lens[si]
                new_pos += 1

            # 保留 R7 位置的符號 (R2-R5 的 row 0)
            if reel_idx in (1, 2, 3, 4):
                new_reel[0] = board[reel_idx, 0]
                new_len[0] = lengths[reel_idx, 0]  # R7 格長度保留(=1)

            board[reel_idx] = new_reel
            lengths[reel_idx] = new_len

        # R7 水平掉落 (往左靠攏，右邊補充) - R7 在 row 0
        r7_symbols = np.full(4, -1, dtype=np.int32)
        r7_pos = 0
        for i in range(4):
            reel_idx = i + 1  # R2-R5
            sym = board[reel_idx, 0]
            if sym != -1 and to_remove[reel_idx, 0] == 0:
                r7_symbols[r7_pos] = sym
                r7_pos += 1

        r7_old_pos = r7_pos  # 記錄 R7 補充開始位置

        # 補充 R7 (從右邊補充)
        while r7_pos < 4:
            new_symbol = np.int32(weighted_choice_numba(drop_weights[drop_idx, 6]))
            # cascade掉落若補到MY/G_MY，沿用本局抽到的轉換symbol(與後端 replaceMysterySymbol 一致)
            if new_symbol == 24:
                new_symbol = my_target_symbol
            elif new_symbol == 25:
                new_symbol = np.int32(my_target_symbol + 11)
            r7_symbols[r7_pos] = new_symbol
            # 檢查新補充的 M1
            if enable_m1_multiplier and (new_symbol == 2 or new_symbol == 13):
                bonus = 2  # 長度1=+2
                if m1_count == 0:
                    bonus -= 1
                multiplier += bonus
                m1_count += 1
            r7_pos += 1

        # 更新 R7 位置 (row 0)
        for i in range(4):
            board[i + 1, 0] = r7_symbols[i]
            board[6, i] = r7_symbols[i]
            lengths[i + 1, 0] = 1  # R7 皆 1x1

    # 計算最終盤面的 C1 數量：依 lengths 逐 block head 計 (與後端 link>0 計 head 一致)
    # lengths 已在消除/掉落過程中維護(存活保留長度、補充=1)，故可信。
    c1_final_count = 0
    for reel_idx in range(6):
        c = 0
        while c < 6:
            sym = board[reel_idx, c]
            L = lengths[reel_idx, c]
            if sym == -1 or L <= 0:
                c += 1
                continue
            if sym == 1:  # C1
                c1_final_count += 1
            c += L

    return (
        total_win,
        c1_final_count,
        np.int32(multiplier),
        np.int32(init_c1_count),
        init_c1_len_counts,
        cascade_scores,
        np.int32(m1_count),
    )


# ========== FreeGame Spin 核心函數 ==========


@njit(nogil=True)
def freegame_spin_core(symbol_reels, reel_lengths, weight_reels, megaway_weights, my_weights, post_c1_weights, drop_weights, megaway_patterns, linkpoint, target_heights, current_multiplier, current_m1_count, enable_m1_multiplier):
    """執行 FreeGame 單次 spin 核心計算 (numba 版本)

    參數:
    - current_multiplier: 當前累計倍數
    - current_m1_count: 當前已累計的 M1 數量
    - enable_m1_multiplier: 是否開啟 M1 倍數特色

    返回:
    - total_win: 本次 spin 得分
    - c1_final_count: 結束時 C1 數量
    - new_multiplier: 更新後的倍數
    - new_m1_count: 更新後的 M1 數量
    """
    # 生成初始盤面
    board = np.full((7, 6), -1, dtype=np.int32)
    lengths = np.full((7, 6), 0, dtype=np.int32)

    # R1-R6
    for reel_idx in range(6):
        pattern_idx = int(weighted_choice_numba(megaway_weights[reel_idx]))
        pattern = megaway_patterns[pattern_idx]
        start_pos = int(weighted_choice_numba(weight_reels[reel_idx, : reel_lengths[reel_idx]]))

        pos = 0
        symbol_pos = start_pos
        for p in range(5):
            length = int(pattern[p])
            if length < 0:
                break
            symbol = symbol_reels[reel_idx, symbol_pos % reel_lengths[reel_idx]]
            # head 存高度，延續格存 0 (與後端 linkScreenSymbol 一致)
            for k in range(length):
                if pos < 6:
                    board[reel_idx, pos] = symbol
                    lengths[reel_idx, pos] = np.int32(length) if k == 0 else 0
                    pos += 1
            symbol_pos += length

    # R7: 4個符號
    r7_start = int(weighted_choice_numba(weight_reels[6, : reel_lengths[6]]))
    for i in range(4):
        symbol = symbol_reels[6, (r7_start + i) % reel_lengths[6]]
        board[6, i] = symbol
        lengths[6, i] = np.int32(1)

    # 模擬後端 convertToMegaWaysScreenLabel：R1-R6 符號下移一行，R7 移到 row0
    # 1. R1-R6 所有符號下移一行
    for reel_idx in range(6):
        for pos in range(5, 0, -1):  # 5,4,3,2,1
            board[reel_idx, pos] = board[reel_idx, pos - 1]
            lengths[reel_idx, pos] = lengths[reel_idx, pos - 1]
        board[reel_idx, 0] = np.int32(-1)  # row0 先清空
        lengths[reel_idx, 0] = 0

    # 2. R7 的 4 個符號移到 R2-R5 的 row0
    for i in range(4):
        board[i + 1, 0] = board[6, i]
        lengths[i + 1, 0] = 1

    # 轉換 MY 符號
    # MY 權重索引對應: 0=Wild, 1=C1, 2=M1, 3=M2, ..., 12=TE
    target_idx = int(weighted_choice_numba(my_weights))
    my_target_symbol = np.int32(target_idx)  # 索引直接就是符號 ID (用獨立變數避免被消除循環覆蓋)
    for r in range(7):
        for c in range(6):
            if board[r, c] == 24:
                board[r, c] = my_target_symbol
            elif board[r, c] == 25:
                board[r, c] = np.int32(my_target_symbol + 11)

    # C1 替換：從 C(7, N) 隨機選擇輪帶替換
    # 注意：MegaWay 符號現在在 row 1-5，row 0 是 R7
    c1_count = int(weighted_choice_numba(post_c1_weights))
    if c1_count > 0:
        # 與後端 applyPostScatter 同步：列舉 C(7, c1_count) 所有組合(字典序)後等機率抽一組
        # (等價後端 buildCombinations 字典序列舉 + pickEvenly 均權抽 index)
        chosen_reels = np.full(7, -1, dtype=np.int32)
        pick_combination_numba(7, c1_count, chosen_reels)

        # 某輪若無可替換符號則該顆 C1 不補 (與後端選定 C(7,N) 後 continue 的行為一致)
        for idx in range(c1_count):
            r = chosen_reels[idx]
            if r == 6:
                # R7：算分/觸發都以「已併入 R2~R5 row0」的盤面為準，
                # 因此 C1 必須寫進合併後的計分格 board[1..4, 0]，而非 R7 原始輪 board[6, *]，
                # 否則替換對算分與 c1_final(觸發判定) 都不生效，原符號還會照樣計分。
                # (R7 符號皆為 1x1，最短長度恆為 1；複數候選時等機率隨機抽)
                cand_reels = np.full(4, -1, dtype=np.int32)
                n_cand = 0
                for i in range(4):
                    if board[i + 1, 0] != -1:  # 有效符號即可 (與後端一致：只檢查 link>0)
                        cand_reels[n_cand] = i + 1
                        n_cand += 1
                if n_cand == 0:
                    continue  # R7 無有效符號
                target_reel = cand_reels[np.random.randint(0, n_cand)]
                board[target_reel, 0] = np.int32(1)
                continue
            # R1~R6：在 pos 1~5 的 MegaWay 符號中替換 (row 0 是 R7)
            # 找出該輪帶最短長度 (與後端一致：只檢查 link>0，不排除任何符號)
            min_len = 99
            c = 1  # 從 row 1 開始
            while c < 6:
                L = lengths[r, c]
                if L <= 0:
                    c += 1
                    continue
                if L < min_len:
                    min_len = L
                c += L
            if min_len == 99:
                continue  # 該輪帶無有效符號
            # 收集所有「最短長度」大符號 block 的起始位置 (head)
            cand_heads = np.full(6, -1, dtype=np.int32)
            n_cand = 0
            c = 1  # 從 row 1 開始 (row 0 是 R7)
            while c < 6:
                L = lengths[r, c]
                if L <= 0:
                    c += 1
                    continue
                if L == min_len:
                    cand_heads[n_cand] = c
                    n_cand += 1
                c += L
            # 複數最短長度時，等機率隨機抽一個 block (與後端一致)
            head = cand_heads[np.random.randint(0, n_cand)]
            # 將整個大符號 block 替換為 C1 (等同後端 head 變 C1、維持高度)
            for cc in range(head, head + min_len):
                if cc < 6:
                    board[r, cc] = np.int32(1)

    # M1 倍數累加 (使用傳入的倍數)
    multiplier = float(current_multiplier)
    m1_count = int(current_m1_count)

    if enable_m1_multiplier:
        for reel_idx in range(6):
            pos = 0
            while pos < 6:
                sym = board[reel_idx, pos]
                L = lengths[reel_idx, pos]
                if sym == -1 or L <= 0:
                    pos += 1
                    continue
                if sym == 2 or sym == 13:  # M1 或 GM1
                    # FG 固定由 x2 開始，每顆 M1 都完整累加其標示倍數。
                    bonus = L + 1
                    multiplier += bonus
                    m1_count += 1
                pos += L

    # R7 的 M1 已於上方主迴圈 (reels 1~4 的 row 0，R7 移位後位置) 計入，
    # 此處不再額外累加，避免同一顆 R7 的 M1 被重複計算兩次倍數。

    total_win = 0.0
    drop_count = 0
    max_drops = 50
    cascade_scores = np.zeros(5, dtype=np.float64)

    # 消除循環
    while drop_count < max_drops:
        score = 0.0
        wins = np.zeros((11, 3), dtype=np.int32)
        win_count = 0

        for target_symbol in range(2, 13):
            consecutive_reels = 0
            ways = 1
            gold_symbol = target_symbol + 11

            for reel_idx in range(6):
                matching = 0
                # 依 lengths 逐 MegaWay block 走訪；大型符號無論覆蓋幾格，
                # 在 Ways 計算中只視為一個符號。
                c = 0
                while c < 6:
                    sym = board[reel_idx, c]
                    L = lengths[reel_idx, c]
                    if sym == -1 or L <= 0:
                        c += 1
                        continue
                    if sym == target_symbol or sym == gold_symbol or sym == 0:
                        matching += 1
                    c += L

                if matching > 0:
                    consecutive_reels += 1
                    ways *= matching
                else:
                    break

            if consecutive_reels >= 3:
                symbol_idx = target_symbol - 2
                line_idx = consecutive_reels - 3
                base_score = linkpoint[symbol_idx, line_idx]
                score += base_score * ways
                wins[win_count, 0] = target_symbol
                wins[win_count, 1] = consecutive_reels
                wins[win_count, 2] = ways
                win_count += 1

        if win_count == 0:
            break

        # 得分乘以倍數
        cascade_round = min(drop_count, 4)
        cascade_scores[cascade_round] += score * multiplier
        total_win += score * multiplier
        drop_count += 1
        drop_idx = min(drop_count, 5) - 1

        # 移除並補充
        to_remove = np.zeros((7, 6), dtype=np.int32)
        gold_win_head = np.zeros((7, 6), dtype=np.int32)  # 兩階段修正:記錄中獎金框head
        # Pass1: 用原始盤面標記所有消除(不即時mutate board),避免中獎金框轉Wild後被後面符號誤消
        for w in range(win_count):
            target_symbol = wins[w, 0]
            reels_count = wins[w, 1]
            gold_symbol = target_symbol + 11
            for reel_idx in range(reels_count):
                pos = 0
                while pos < 6:
                    sym = board[reel_idx, pos]
                    L = lengths[reel_idx, pos]
                    if sym == -1 or L <= 0:
                        pos += 1
                        continue
                    if sym == target_symbol or sym == gold_symbol or sym == 0:
                        for k in range(L):
                            if pos + k < 6:
                                to_remove[reel_idx, pos + k] = 1
                        if sym >= 13 and sym <= 23:
                            gold_win_head[reel_idx, pos] = 1
                    pos += L
        # Pass2: 中獎金框整塊轉Wild並取消其消除(存活),對齊後端 calculateChangeWildScreen
        for reel_idx in range(6):
            pos = 0
            while pos < 6:
                L = lengths[reel_idx, pos]
                if L > 0:
                    if gold_win_head[reel_idx, pos] == 1:
                        for k in range(L):
                            if pos + k < 6:
                                board[reel_idx, pos + k] = 0
                                to_remove[reel_idx, pos + k] = 0
                    pos += L
                else:
                    pos += 1

        # R1-R6 垂直掉落
        # Java 順序: 新符號在底部 (row 1-消除數量)，保留符號在頂部 (row 消除數量+1 到末尾)
        for reel_idx in range(6):
            target_height = target_heights[reel_idx]

            # 收集存活符號列表 (row 1-5)，以區塊為單位
            survive_symbols = np.full(6, -1, dtype=np.int32)
            survive_lens = np.zeros(6, dtype=np.int32)
            survive_count = 0
            pos = 1
            while pos < 6:
                sym = board[reel_idx, pos]
                L = lengths[reel_idx, pos]
                if sym == -1:
                    pos += 1
                    continue
                if L > 0:  # 是 head
                    if to_remove[reel_idx, pos] == 0:  # 未被移除
                        # 複製整個區塊
                        for k in range(L):
                            if pos + k < 6:
                                survive_symbols[survive_count] = board[reel_idx, pos + k]
                                survive_lens[survive_count] = L if k == 0 else 0
                                survive_count += 1
                    pos += L
                else:
                    pos += 1

            # 計算消除數量 (要補充的新符號數量)
            eliminate_count = target_height - survive_count

            new_reel = np.full(6, -1, dtype=np.int32)
            new_len = np.zeros(6, dtype=np.int32)

            # 按 Java 順序填充: 先新符號 (row 1 到 eliminate_count)，再保留符號
            new_pos = 1

            # 先填充新符號
            for _ in range(eliminate_count):
                if new_pos >= 6:
                    break
                new_symbol = np.int32(weighted_choice_numba(drop_weights[drop_idx, reel_idx]))
                # cascade掉落若補到MY/G_MY，沿用本局抽到的轉換symbol(與後端 replaceMysterySymbol 一致)
                if new_symbol == 24:
                    new_symbol = my_target_symbol
                elif new_symbol == 25:
                    new_symbol = np.int32(my_target_symbol + 11)
                new_reel[new_pos] = new_symbol
                new_len[new_pos] = 1  # 補充符號皆 1x1
                if enable_m1_multiplier and (new_symbol == 2 or new_symbol == 13):
                    bonus = 2
                    multiplier += bonus
                    m1_count += 1
                new_pos += 1

            # 再填充保留符號
            for si in range(survive_count):
                if new_pos >= 6:
                    break
                new_reel[new_pos] = survive_symbols[si]
                new_len[new_pos] = survive_lens[si]
                new_pos += 1

            # 保留 R7 位置的符號 (R2-R5 的 row 0)
            if reel_idx in (1, 2, 3, 4):
                new_reel[0] = board[reel_idx, 0]
                new_len[0] = lengths[reel_idx, 0]  # R7 格長度保留(=1)

            board[reel_idx] = new_reel
            lengths[reel_idx] = new_len

        # R7 水平掉落 - R7 在 row 0
        r7_symbols = np.full(4, -1, dtype=np.int32)
        r7_pos = 0
        for i in range(4):
            reel_idx = i + 1
            sym = board[reel_idx, 0]
            if sym != -1 and to_remove[reel_idx, 0] == 0:
                r7_symbols[r7_pos] = sym
                r7_pos += 1

        while r7_pos < 4:
            new_symbol = np.int32(weighted_choice_numba(drop_weights[drop_idx, 6]))
            # cascade掉落若補到MY/G_MY，沿用本局抽到的轉換symbol(與後端 replaceMysterySymbol 一致)
            if new_symbol == 24:
                new_symbol = my_target_symbol
            elif new_symbol == 25:
                new_symbol = np.int32(my_target_symbol + 11)
            r7_symbols[r7_pos] = new_symbol
            if enable_m1_multiplier and (new_symbol == 2 or new_symbol == 13):
                bonus = 2
                multiplier += bonus
                m1_count += 1
            r7_pos += 1

        # 更新 R7 位置 (row 0)
        for i in range(4):
            board[i + 1, 0] = r7_symbols[i]
            board[6, i] = r7_symbols[i]
            lengths[i + 1, 0] = 1  # R7 皆 1x1

    # 計算最終 C1 數量：依 lengths 逐 block head 計 (與後端 link>0 計 head 一致)
    c1_final_count = 0
    for reel_idx in range(6):
        c = 0
        while c < 6:
            sym = board[reel_idx, c]
            L = lengths[reel_idx, c]
            if sym == -1 or L <= 0:
                c += 1
                continue
            if sym == 1:  # C1
                c1_final_count += 1
            c += L

    return total_win, c1_final_count, np.int32(multiplier), np.int32(m1_count), cascade_scores


# ========== 多進程支持 ==========


@njit(nogil=True)
def single_spin(param_set, enable_m1_multiplier=True):
    """執行單次 spin，返回 (win, c1_count, multiplier, init_c1_count, c1_len_stats, cascade_scores)

    參數:
    - param_set: 參數組 (1、2 或 BF 專用的 3)
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)
    """
    if param_set == 1:
        return single_spin_core(SYMBOL_REELS_1, REEL_LENGTHS_1, WEIGHT_REELS_1, MEGAWAY_WEIGHTS_1, MY_WEIGHTS_1, POST_C1_WEIGHTS_1, DROP_WEIGHTS_1, MEGAWAY_PATTERNS, LINKPOINT, TARGET_HEIGHTS, enable_m1_multiplier)
    if param_set == 2:
        return single_spin_core(SYMBOL_REELS_2, REEL_LENGTHS_2, WEIGHT_REELS_2, MEGAWAY_WEIGHTS_2, MY_WEIGHTS_2, POST_C1_WEIGHTS_2, DROP_WEIGHTS_2, MEGAWAY_PATTERNS, LINKPOINT, TARGET_HEIGHTS, enable_m1_multiplier)
    return single_spin_core(SYMBOL_REELS_3, REEL_LENGTHS_3, WEIGHT_REELS_3, MEGAWAY_WEIGHTS_3, MY_WEIGHTS_3, POST_C1_WEIGHTS_3, DROP_WEIGHTS_3, MEGAWAY_PATTERNS, LINKPOINT, TARGET_HEIGHTS, enable_m1_multiplier)


# 全域變數，用於 worker 傳遞參數
ENABLE_M1_MULTIPLIER_GLOBAL = True


def run_simulations(n_sims, enable_m1_multiplier=True):
    """執行多次模擬 (Python 版本)，返回 (results, c1_counts, multipliers, init_c1_counts, c1_len_stats)

    參數:
    - n_sims: 模擬次數
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)
    """
    results = np.zeros(n_sims, dtype=np.float64)
    c1_counts = np.zeros(n_sims, dtype=np.int32)
    multipliers = np.zeros(n_sims, dtype=np.int32)
    init_c1_counts = np.zeros(n_sims, dtype=np.int32)
    c1_len_stats = np.zeros(4, dtype=np.int64)  # [len1_total, len2_total, len3_total, len4_total]
    cascade_score_stats = np.zeros(5, dtype=np.float64)
    reel_weight_sum = np.sum(REEL_WEIGHT)

    for i in range(n_sims):
        # 選擇參數組
        r = np.random.random() * reel_weight_sum
        param_set = 1 if r < REEL_WEIGHT[0] else 2
        win, c1, mult, init_c1, c1_lens, cascade_scores, _ = single_spin(param_set, enable_m1_multiplier)
        results[i] = win
        c1_counts[i] = c1
        multipliers[i] = mult
        init_c1_counts[i] = init_c1
        c1_len_stats += c1_lens
        cascade_score_stats += cascade_scores

    return results, c1_counts, multipliers, init_c1_counts, c1_len_stats, cascade_score_stats


def worker_simulate(args):
    """單個 worker 執行的模擬任務"""
    n_sims, seed, enable_m1 = args
    np.random.seed(seed)
    return run_simulations(n_sims, enable_m1)


def basegame(n_simulations, n_cores=None, enable_m1_multiplier=True):
    """
    執行 Base Game 模擬

    參數:
    - n_simulations: 總模擬次數
    - n_cores: 使用的 CPU 核心數，預設為全部核心
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)

    返回:
    - avg_score: 平均得分
    - std_score: 標準差
    - total_time: 執行時間
    """
    global ENABLE_M1_MULTIPLIER_GLOBAL
    ENABLE_M1_MULTIPLIER_GLOBAL = enable_m1_multiplier

    if n_cores is None:
        n_cores = cpu_count()

    n_cores = min(n_cores, cpu_count())

    print(f"開始模擬...")
    print(f"總模擬次數: {n_simulations:,}")
    print(f"使用核心數: {n_cores}")
    print(f"M1 倍數特色: {'開啟' if enable_m1_multiplier else '關閉'}")

    start_time = time.time()

    # JIT 編譯預熱
    print("JIT 編譯中...")
    _ = run_simulations(10, enable_m1_multiplier)
    compile_time = time.time() - start_time
    print(f"JIT 編譯完成，耗時: {compile_time:.2f}秒")

    start_time = time.time()

    if n_cores == 1:
        # 單進程模式
        results, c1_counts, multipliers, init_c1_counts, c1_len_stats, cascade_score_stats = run_simulations(n_simulations, enable_m1_multiplier)
    else:
        # 多進程模式
        sims_per_core = n_simulations // n_cores
        remainder = n_simulations % n_cores

        tasks = []
        for i in range(n_cores):
            n = sims_per_core + (1 if i < remainder else 0)
            seed = np.random.randint(0, 2**31) + i
            tasks.append((n, seed, enable_m1_multiplier))

        with Pool(n_cores) as pool:
            all_results = pool.map(worker_simulate, tasks)

        results = np.concatenate([r[0] for r in all_results])
        c1_counts = np.concatenate([r[1] for r in all_results])
        multipliers = np.concatenate([r[2] for r in all_results])
        init_c1_counts = np.concatenate([r[3] for r in all_results])
        c1_len_stats = np.sum([r[4] for r in all_results], axis=0)
        cascade_score_stats = np.sum([r[5] for r in all_results], axis=0)

    total_time = time.time() - start_time

    # 計算統計
    avg_score = np.mean(results)
    std_score = np.std(results)
    total_score = np.sum(results)
    non_zero = np.sum(results > 0)
    hit_rate = non_zero / n_simulations * 100

    # 初始 C1 統計 (0, 1, 2, 3, 4, 5, 6, 7+)
    init_c1_stats = np.zeros(8, dtype=np.int64)
    for i in range(8):
        if i < 7:
            init_c1_stats[i] = np.sum(init_c1_counts == i)
        else:
            init_c1_stats[i] = np.sum(init_c1_counts >= 7)

    # 結束 C1 統計 (0, 1, 2, 3, 4, 5, 6, 7+)
    c1_stats = np.zeros(8, dtype=np.int64)
    for i in range(8):
        if i < 7:
            c1_stats[i] = np.sum(c1_counts == i)
        else:
            c1_stats[i] = np.sum(c1_counts >= 7)

    # 倍數統計 (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15+)
    mult_stats = np.zeros(15, dtype=np.int64)
    for i in range(15):
        if i < 14:
            mult_stats[i] = np.sum(multipliers == (i + 1))
        else:
            mult_stats[i] = np.sum(multipliers >= 15)

    # 得分分布統計 (以 100 為基底)
    # 區間邊界 (乘以 100 得到實際分數邊界)
    score_boundaries = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 2000, 3000]
    score_labels = [
        "[0]",
        "(0~1]",
        "(1~2]",
        "(2~3]",
        "(3~4]",
        "(4~5]",
        "(5~6]",
        "(6~7]",
        "(7~8]",
        "(8~9]",
        "(9~10]",
        "(10~15]",
        "(15~20]",
        "(20~25]",
        "(25~30]",
        "(30~35]",
        "(35~40]",
        "(40~45]",
        "(45~50]",
        "(50~60]",
        "(60~70]",
        "(70~80]",
        "(80~90]",
        "(90~100]",
        "(100~120]",
        "(120~140]",
        "(140~160]",
        "(160~180]",
        "(180~200]",
        "(200~250]",
        "(250~300]",
        "(300~350]",
        "(350~400]",
        "(400~450]",
        "(450~500]",
        "(500~550]",
        "(550~600]",
        "(600~650]",
        "(650~700]",
        "(700~750]",
        "(750~800]",
        "(800~850]",
        "(850~900]",
        "(900~950]",
        "(950~1000]",
        "(1000~2000]",
        "(2000~3000]",
        "[3000+]",
    ]

    score_stats = np.zeros(len(score_labels), dtype=np.int64)
    normalized_results = results / 100.0  # 以 100 為基底

    # [0]
    score_stats[0] = np.sum(normalized_results == 0)
    # (0~1], (1~2], ... (2000~3000]
    for i in range(1, len(score_boundaries)):
        lower = score_boundaries[i - 1]
        upper = score_boundaries[i]
        score_stats[i] = np.sum((normalized_results > lower) & (normalized_results <= upper))
    # [3000+]
    score_stats[-1] = np.sum(normalized_results > 3000)

    print(f"\n---------- Cascade 消除平均得分 (BaseGame) ----------")
    cascade_avgs = cascade_score_stats / n_simulations if n_simulations > 0 else np.zeros(5)
    labels = ["第1次", "第2次", "第3次", "第4次", "第5次+"]
    for i in range(5):
        print(f"  {labels[i]}消除平均得分: {cascade_avgs[i]:.4f}")
    print(f"  總和(應等於平均總得分): {np.sum(cascade_avgs):.4f}")
    print(f"\n========== 模擬結果 ==========")
    print(f"模擬次數: {n_simulations:,}")
    print(f"總得分: {total_score:,.0f}")
    print(f"平均得分: {avg_score:.4f}")
    print(f"標準差: {std_score:.4f}")
    print(f"中獎率: {hit_rate:.2f}%")
    print(f"RTP: {avg_score:.4f} ({avg_score*100:.2f}%)")
    print(f"執行時間: {total_time:.2f}秒")
    print(f"速度: {n_simulations/total_time:,.0f} spins/秒")
    print(f"\n---------- 初始C1(Scatter) 統計 ----------")
    for i in range(8):
        label = f"{i}" if i < 7 else "7+"
        count = init_c1_stats[i]
        pct = count / n_simulations * 100
        print(f"  初始C1={label}: {count:,} 次 ({pct:.4f}%)")
    print(f"\n---------- 初始C1 長度分布 ----------")
    total_c1 = np.sum(c1_len_stats)
    for i in range(4):
        count = c1_len_stats[i]
        pct = count / total_c1 * 100 if total_c1 > 0 else 0
        print(f"  長度={i+1}: {count:,} 個 ({pct:.4f}%)")
    print(f"  C1 總數: {total_c1:,} 個")
    print(f"\n---------- 結束C1(Scatter) 統計 ----------")
    for i in range(8):
        label = f"{i}" if i < 7 else "7+"
        count = c1_stats[i]
        pct = count / n_simulations * 100
        print(f"  結束C1={label}: {count:,} 次 ({pct:.4f}%)")
    print(f"\n---------- 倍數統計 ----------")
    for i in range(15):
        label = f"{i + 1}" if i < 14 else "15+"
        count = mult_stats[i]
        pct = count / n_simulations * 100
        print(f"  倍數={label}: {count:,} 次 ({pct:.4f}%)")
    print(f"\n---------- 得分分布 (基底=100) ----------")
    for i, label in enumerate(score_labels):
        count = score_stats[i]
        pct = count / n_simulations * 100
        print(f"  {label}: {count:,} 次 ({pct:.4f}%)")
    print(f"===============================")

    return avg_score, std_score, total_time, init_c1_stats, c1_stats, mult_stats, score_stats, c1_len_stats


# ========== FreeGame 函數 ==========


@njit(nogil=True)
def freegame_single_spin(param_set, current_multiplier, current_m1_count, enable_m1_multiplier=True):
    """執行 FreeGame 單次 spin，返回 (win, c1_count, new_multiplier, new_m1_count, cascade_scores)

    參數:
    - param_set: 參數組 (1, 2, 或 3)
    - current_multiplier: 當前累計倍數
    - current_m1_count: 當前已累計的 M1 數量
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)
    """
    if param_set == 1:
        return freegame_spin_core(FG_SYMBOL_REELS_1, FG_REEL_LENGTHS_1, FG_WEIGHT_REELS_1, FG_MEGAWAY_WEIGHTS_1, FG_MY_WEIGHTS_1, FG_POST_C1_WEIGHTS_1, FG_DROP_WEIGHTS_1, MEGAWAY_PATTERNS, LINKPOINT, TARGET_HEIGHTS, current_multiplier, current_m1_count, enable_m1_multiplier)
    elif param_set == 2:
        return freegame_spin_core(FG_SYMBOL_REELS_2, FG_REEL_LENGTHS_2, FG_WEIGHT_REELS_2, FG_MEGAWAY_WEIGHTS_2, FG_MY_WEIGHTS_2, FG_POST_C1_WEIGHTS_2, FG_DROP_WEIGHTS_2, MEGAWAY_PATTERNS, LINKPOINT, TARGET_HEIGHTS, current_multiplier, current_m1_count, enable_m1_multiplier)
    else:
        return freegame_spin_core(FG_SYMBOL_REELS_3, FG_REEL_LENGTHS_3, FG_WEIGHT_REELS_3, FG_MEGAWAY_WEIGHTS_3, FG_MY_WEIGHTS_3, FG_POST_C1_WEIGHTS_3, FG_DROP_WEIGHTS_3, MEGAWAY_PATTERNS, LINKPOINT, TARGET_HEIGHTS, current_multiplier, current_m1_count, enable_m1_multiplier)


def freegame(trigger_c1_count, verbose=False, enable_m1_multiplier=True):
    """
    執行 FreeGame 模擬

    參數:
    - trigger_c1_count: 觸發時的 C1 數量 (4, 5, 6, ...)
    - verbose: 是否輸出詳細信息
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)

    返回:
    - total_win: 總得分
    - final_multiplier: 結束時倍數
    - total_spins: 總 spin 數 (含 retrigger)
    - retrigger_count: retrigger 次數
    """
    # 計算初始場次: 4→10, 5→12, 每多1加2
    initial_spins = 10 + (trigger_c1_count - 4) * 2
    remaining_spins = initial_spins
    initial_remaining = initial_spins  # 追蹤初始場次剩餘
    total_rounds = initial_spins  # 追蹤總場次 (用於最大場次限制)
    max_rounds = 50  # 後端 maxRound 設定

    # 初始化
    total_win = 0.0
    multiplier = FG_INITIAL_MULTIPLIER
    m1_count = 0
    total_spins_done = 0
    retrigger_count = 0
    cascade_score_stats = np.zeros(5, dtype=np.float64)

    # 權重
    reel_weight_sum = np.sum(FREE_REEL_WEIGHT)
    trigger_weight_sum = np.sum(FREE_TRIGGER_REEL)

    while remaining_spins > 0:
        # 選擇參數組：初始場次用 FreeReelWeight，retrigger 用 FreeTriggerReel
        if initial_remaining > 0:
            # 初始場次
            r = np.random.random() * reel_weight_sum
            cumsum = 0.0
            param_set = 1
            for i in range(len(FREE_REEL_WEIGHT)):
                cumsum += FREE_REEL_WEIGHT[i]
                if r < cumsum:
                    param_set = i + 1
                    break
            initial_remaining -= 1
        else:
            # Retrigger 場次
            r = np.random.random() * trigger_weight_sum
            cumsum = 0.0
            param_set = 1
            for i in range(len(FREE_TRIGGER_REEL)):
                cumsum += FREE_TRIGGER_REEL[i]
                if r < cumsum:
                    param_set = i + 1
                    break

        # 執行 spin
        win, c1_final, new_mult, new_m1_count, cascade_scores = freegame_single_spin(param_set, multiplier, m1_count, enable_m1_multiplier)

        total_win += win
        multiplier = new_mult
        m1_count = new_m1_count
        total_spins_done += 1
        remaining_spins -= 1
        cascade_score_stats += cascade_scores

        if verbose:
            print(f"  Spin {total_spins_done}: win={win:.0f}, C1={c1_final}, mult={multiplier}, param={param_set}")

        # 檢查 retrigger
        if c1_final >= 4:
            retrigger_spins = 10 + (c1_final - 4) * 2
            # 後端 maxRound 限制：不超過 50 場
            available_rounds = max_rounds - total_rounds
            if available_rounds > 0:
                add_rounds = min(retrigger_spins, available_rounds)
                remaining_spins += add_rounds
                total_rounds += add_rounds
                retrigger_count += 1
                if verbose:
                    print(f"  *** Retrigger! C1={c1_final}, +{add_rounds} spins (total={total_rounds}) ***")

    return total_win, multiplier, total_spins_done, retrigger_count, cascade_score_stats


def run_freegame_simulations(n_sims, trigger_c1_count=4, enable_m1_multiplier=True):
    """執行多次 FreeGame 模擬，返回統計數據

    參數:
    - n_sims: 模擬次數
    - trigger_c1_count: 觸發時的 C1 數量
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)
    """
    results = np.zeros(n_sims, dtype=np.float64)
    final_multipliers = np.zeros(n_sims, dtype=np.int32)
    total_spins_list = np.zeros(n_sims, dtype=np.int32)
    retrigger_counts = np.zeros(n_sims, dtype=np.int32)
    cascade_score_stats = np.zeros(5, dtype=np.float64)
    total_spins_total = 0

    for i in range(n_sims):
        win, mult, spins, retrigs, cascade_scores = freegame(trigger_c1_count, False, enable_m1_multiplier)
        results[i] = win
        final_multipliers[i] = mult
        total_spins_list[i] = spins
        retrigger_counts[i] = retrigs
        cascade_score_stats += cascade_scores
        total_spins_total += spins

    return results, final_multipliers, total_spins_list, retrigger_counts, cascade_score_stats, total_spins_total


def simulate_freegame(n_simulations, trigger_c1_count=4, enable_m1_multiplier=True):
    """
    執行 FreeGame 模擬並輸出統計

    參數:
    - n_simulations: 模擬次數
    - trigger_c1_count: 觸發時的 C1 數量
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)
    """
    print(f"開始 FreeGame 模擬...")
    print(f"觸發 C1 數量: {trigger_c1_count}")
    print(f"初始場次: {10 + (trigger_c1_count - 4) * 2}")
    print(f"模擬次數: {n_simulations:,}")
    print(f"M1 倍數特色: {'開啟' if enable_m1_multiplier else '關閉'}")

    start_time = time.time()

    # JIT 預熱
    print("JIT 編譯中...")
    _ = freegame(4, False, enable_m1_multiplier)
    compile_time = time.time() - start_time
    print(f"JIT 編譯完成，耗時: {compile_time:.2f}秒")

    start_time = time.time()
    results, final_mults, total_spins, retrig_counts, cascade_score_stats, total_spins_total = run_freegame_simulations(n_simulations, trigger_c1_count, enable_m1_multiplier)
    total_time = time.time() - start_time

    # 統計
    avg_win = np.mean(results)
    std_win = np.std(results)
    avg_mult = np.mean(final_mults)
    avg_spins = np.mean(total_spins)
    avg_retrigs = np.mean(retrig_counts)
    retrig_rate = np.sum(retrig_counts > 0) / n_simulations * 100

    # 倍數分布
    mult_stats = np.zeros(15, dtype=np.int64)
    for i in range(15):
        if i < 14:
            mult_stats[i] = np.sum(final_mults == (i + 1))
        else:
            mult_stats[i] = np.sum(final_mults >= 15)

    print(f"\n---------- FreeGame Cascade 消除平均得分 ----------")
    if total_spins_total > 0:
        cascade_avgs = cascade_score_stats / total_spins_total
    else:
        cascade_avgs = np.zeros(5, dtype=np.float64)
    labels = ["第1次", "第2次", "第3次", "第4次", "第5次+"]
    for i in range(5):
        print(f"  {labels[i]}消除平均得分: {cascade_avgs[i]:.4f}")
    print(f"  總和(應等於 FreeGame 平均每 spin 得分): {np.sum(cascade_avgs):.4f}")
    print(f"\n========== FreeGame 模擬結果 ==========")
    print(f"模擬次數: {n_simulations:,}")
    print(f"平均得分: {avg_win:.4f}")
    print(f"標準差: {std_win:.4f}")
    print(f"平均結束倍數: {avg_mult:.2f}")
    print(f"平均 spin 數: {avg_spins:.2f}")
    print(f"平均 retrigger 次數: {avg_retrigs:.4f}")
    print(f"Retrigger 機率: {retrig_rate:.4f}%")
    print(f"執行時間: {total_time:.2f}秒")
    print(f"速度: {n_simulations/total_time:,.0f} FG/秒")
    print(f"\n---------- 結束倍數統計 ----------")
    for i in range(15):
        label = f"{i + 1}" if i < 14 else "15+"
        count = mult_stats[i]
        pct = count / n_simulations * 100
        print(f"  倍數={label}: {count:,} 次 ({pct:.4f}%)")
    print(f"=======================================")

    return avg_win, std_win, avg_mult, avg_spins, mult_stats


# ========== Full Game 函數 ==========


def single_full_game(enable_m1_multiplier=True):
    """
    執行單次完整遊戲 (BaseGame + 可能的 FreeGame)

    參數:
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)

    返回:
    - total_win: 總得分
    - bg_win: BaseGame 得分
    - fg_win: FreeGame 得分
    - fg_triggered: 是否觸發 FreeGame (0/1)
    - fg_retrigger: FreeGame 中是否有 retrigger (0/1)
    - c1_count: 結束時 C1 數量
    """
    # 執行 BaseGame
    reel_weight_sum = np.sum(REEL_WEIGHT)
    r = np.random.random() * reel_weight_sum
    param_set = 1 if r < REEL_WEIGHT[0] else 2

    bg_win, c1_count, mult, init_c1, _, bg_cascade_scores, _ = single_spin(param_set, enable_m1_multiplier)

    fg_win = 0.0
    fg_triggered = 0
    fg_retrigger = 0
    fg_cascade_scores = np.zeros(5, dtype=np.float64)

    # 檢查是否觸發 FreeGame
    if c1_count >= 4:
        fg_triggered = 1
        fg_total_win, fg_mult, fg_spins, retrig_count, fg_cascade_scores = freegame(c1_count, False, enable_m1_multiplier)
        fg_win = fg_total_win
        if retrig_count > 0:
            fg_retrigger = 1

    total_win = bg_win + fg_win
    return total_win, bg_win, fg_win, fg_triggered, fg_retrigger, c1_count, bg_cascade_scores, fg_cascade_scores


def run_full_game_simulations(n_sims, enable_m1_multiplier=True):
    """執行多次完整遊戲模擬

    參數:
    - n_sims: 模擬次數
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)
    """
    total_wins = np.zeros(n_sims, dtype=np.float64)
    bg_wins = np.zeros(n_sims, dtype=np.float64)
    fg_wins = np.zeros(n_sims, dtype=np.float64)
    fg_triggered = np.zeros(n_sims, dtype=np.int32)
    fg_retriggered = np.zeros(n_sims, dtype=np.int32)
    c1_counts = np.zeros(n_sims, dtype=np.int32)
    bg_cascade_stats = np.zeros(5, dtype=np.float64)
    fg_cascade_stats = np.zeros(5, dtype=np.float64)

    for i in range(n_sims):
        total, bg, fg, trig, retrig, c1, bg_cascade_scores, fg_cascade_scores = single_full_game(enable_m1_multiplier)
        total_wins[i] = total
        bg_wins[i] = bg
        fg_wins[i] = fg
        fg_triggered[i] = trig
        fg_retriggered[i] = retrig
        c1_counts[i] = c1
        bg_cascade_stats += bg_cascade_scores
        fg_cascade_stats += fg_cascade_scores

    return total_wins, bg_wins, fg_wins, fg_triggered, fg_retriggered, c1_counts, bg_cascade_stats, fg_cascade_stats


def worker_full_game(args):
    """單個 worker 執行的完整遊戲模擬任務"""
    n_sims, seed, enable_m1 = args
    np.random.seed(seed)
    return run_full_game_simulations(n_sims, enable_m1)


def full_game(n_simulations, n_cores=None, enable_m1_multiplier=True):
    """
    執行完整遊戲模擬 (BaseGame + FreeGame)

    參數:
    - n_simulations: 總模擬次數
    - n_cores: 使用的 CPU 核心數，預設為全部核心
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)

    返回:
    - avg_total: 總平均得分
    - avg_bg: BaseGame 平均得分
    - avg_fg: FreeGame 平均得分
    - fg_trigger_rate: FreeGame 觸發機率
    - fg_retrigger_rate: FreeGame 中 retrigger 比例
    """
    global ENABLE_M1_MULTIPLIER_GLOBAL
    ENABLE_M1_MULTIPLIER_GLOBAL = enable_m1_multiplier

    if n_cores is None:
        n_cores = cpu_count()

    n_cores = min(n_cores, cpu_count())

    print(f"開始完整遊戲模擬...")
    print(f"總模擬次數: {n_simulations:,}")
    print(f"使用核心數: {n_cores}")
    print(f"M1 倍數特色: {'開啟' if enable_m1_multiplier else '關閉'}")

    start_time = time.time()

    # JIT 編譯預熱
    print("JIT 編譯中...")
    _ = run_full_game_simulations(10, enable_m1_multiplier)
    compile_time = time.time() - start_time
    print(f"JIT 編譯完成，耗時: {compile_time:.2f}秒")

    start_time = time.time()

    if n_cores == 1:
        # 單進程模式
        total_wins, bg_wins, fg_wins, fg_triggered, fg_retriggered, c1_counts, bg_cascade_stats, fg_cascade_stats = run_full_game_simulations(n_simulations, enable_m1_multiplier)
    else:
        # 多進程模式
        sims_per_core = n_simulations // n_cores
        remainder = n_simulations % n_cores

        tasks = []
        for i in range(n_cores):
            n = sims_per_core + (1 if i < remainder else 0)
            seed = np.random.randint(0, 2**31) + i
            tasks.append((n, seed, enable_m1_multiplier))

        with Pool(n_cores) as pool:
            all_results = pool.map(worker_full_game, tasks)

        total_wins = np.concatenate([r[0] for r in all_results])
        bg_wins = np.concatenate([r[1] for r in all_results])
        fg_wins = np.concatenate([r[2] for r in all_results])
        fg_triggered = np.concatenate([r[3] for r in all_results])
        fg_retriggered = np.concatenate([r[4] for r in all_results])
        c1_counts = np.concatenate([r[5] for r in all_results])
        bg_cascade_stats = np.sum([r[6] for r in all_results], axis=0)
        fg_cascade_stats = np.sum([r[7] for r in all_results], axis=0)

    total_time = time.time() - start_time

    # 統計
    avg_total = np.mean(total_wins)
    avg_bg = np.mean(bg_wins)
    avg_fg = np.mean(fg_wins)
    std_total = np.std(total_wins)

    fg_trigger_count = np.sum(fg_triggered)
    fg_trigger_rate = fg_trigger_count / n_simulations * 100

    fg_retrig_count = np.sum(fg_retriggered)
    fg_retrig_rate = fg_retrig_count / fg_trigger_count * 100 if fg_trigger_count > 0 else 0

    # C1 統計
    c1_stats = np.zeros(8, dtype=np.int64)
    for i in range(8):
        if i < 7:
            c1_stats[i] = np.sum(c1_counts == i)
        else:
            c1_stats[i] = np.sum(c1_counts >= 7)

    print(f"\n---------- BaseGame Cascade 消除平均得分 ----------")
    bg_cascade_avgs = bg_cascade_stats / n_simulations if n_simulations > 0 else np.zeros(5)
    labels = ["第1次", "第2次", "第3次", "第4次", "第5次+"]
    for i in range(5):
        print(f"  {labels[i]}消除平均得分: {bg_cascade_avgs[i]:.4f}")
    print(f"  總和(應等於 BaseGame 平均總得分): {np.sum(bg_cascade_avgs):.4f}")

    print(f"\n---------- FreeGame Cascade 消除平均得分 ----------")
    fg_cascade_avgs = fg_cascade_stats / n_simulations if n_simulations > 0 else np.zeros(5)
    for i in range(5):
        print(f"  {labels[i]}消除平均得分: {fg_cascade_avgs[i]:.4f}")
    print(f"  總和(應等於 FreeGame 平均總得分): {np.sum(fg_cascade_avgs):.4f}")
    print(f"\n========== 完整遊戲模擬結果 ==========")
    print(f"模擬次數: {n_simulations:,}")
    print(f"")
    print(f"---------- 得分統計 ----------")
    print(f"總平均得分: {avg_total:.4f}")
    print(f"  BaseGame: {avg_bg:.4f} ({avg_bg/avg_total*100:.2f}%)")
    print(f"  FreeGame: {avg_fg:.4f} ({avg_fg/avg_total*100:.2f}%)")
    print(f"標準差: {std_total:.4f}")
    print(f"")
    print(f"---------- FreeGame 統計 ----------")
    print(f"FreeGame 觸發次數: {fg_trigger_count:,}")
    print(f"FreeGame 觸發機率: {fg_trigger_rate:.4f}%")
    print(f"有 Retrigger 的 FreeGame: {fg_retrig_count:,} / {fg_trigger_count:,}")
    print(f"Retrigger 比例: {fg_retrig_rate:.4f}%")
    print(f"")
    print(f"---------- C1(Scatter) 統計 ----------")
    for i in range(8):
        label = f"{i}" if i < 7 else "7+"
        count = c1_stats[i]
        pct = count / n_simulations * 100
        print(f"  C1={label}: {count:,} 次 ({pct:.4f}%)")
    print(f"")
    print(f"執行時間: {total_time:.2f}秒")
    print(f"速度: {n_simulations/total_time:,.0f} games/秒")
    print(f"==========================================")

    return avg_total, avg_bg, avg_fg, fg_trigger_rate, fg_retrig_rate


# ========== 符號名稱對照 (用於除錯顯示) ==========
SYMBOL_NAMES = {0: "WD", 1: "SP", 2: "M1", 3: "M2", 4: "M3", 5: "M4", 6: "M5", 7: "M6", 8: "A", 9: "K", 10: "Q", 11: "J", 12: "TE", 13: "GM1", 14: "GM2", 15: "GM3", 16: "GM4", 17: "GM5", 18: "GM6", 19: "GA", 20: "GK", 21: "GQ", 22: "GJ", 23: "GTE", 24: "MY", 25: "GMY"}

# ===== H026-style runner / aggregation / reporting =====

R_ALL = 0
R_MULTIPLIER_COUNT_BG = 1
R_MULTIPLIER_COUNT_FG = 2
R_MULTIPLIER_COUNT_OA = 3
R_MULTIPLIER_PAY_BG = 4
R_MULTIPLIER_PAY_FG = 5
R_MULTIPLIER_PAY_OA = 6
R_BG_CASCADE_PAY = 7
R_FG_CASCADE_PAY = 8
R_SCATTER_COUNT = 9
R_FG_FINAL_MULTIPLIER = 10
R_SCENE = 11
R_BG_CASCADE_DIST = 12
R_FG_CASCADE_DIST = 13

# Multiplier Line interval metrics. BG rows use one paid BG spin as the
# denominator. FG rows group complete FG sessions by session pay interval;
# spin-level rates use the FG spins inside those sessions as denominator.
R_BG_INTERVAL_HITS = 14
R_BG_INTERVAL_M1 = 15
R_BG_INTERVAL_BIG_M1 = 16
R_BG_INTERVAL_CASCADE_1 = 17
R_BG_INTERVAL_CASCADE_2 = 18
R_BG_INTERVAL_CASCADE_3 = 19
R_BG_INTERVAL_CASCADE_4 = 20
R_BG_INTERVAL_CASCADE_5P = 21
R_BG_INTERVAL_MULT_SUM = 22
R_BG_INTERVAL_MULT_MAX = 23
R_FG_INTERVAL_SPINS = 24
R_FG_INTERVAL_HIT_SPINS = 25
R_FG_INTERVAL_M1_SPINS = 26
R_FG_INTERVAL_BIG_M1_SPINS = 27
R_FG_INTERVAL_CASCADE_1 = 28
R_FG_INTERVAL_CASCADE_2 = 29
R_FG_INTERVAL_CASCADE_3 = 30
R_FG_INTERVAL_CASCADE_4 = 31
R_FG_INTERVAL_CASCADE_5P = 32
R_FG_INTERVAL_RETRIGGER_SESSIONS = 33
R_FG_INTERVAL_FINAL_MULT_SUM = 34
R_FG_INTERVAL_FINAL_MULT_MAX = 35

RECORD_COLS = max(64, len(THRESHOLD_RECORD))
RECORD_SIZE = (36, RECORD_COLS)

RA_TOTAL_ROUNDS = 0
RA_COIN_IN_SUM = 1
RA_PAY_TOTAL = 2
RA_PAY_BG = 3
RA_PAY_FG = 4
RA_HITS_TOTAL = 5
RA_HITS_BG = 6
RA_HITS_FG_SPIN = 7
RA_FG_TRIGGER = 8
RA_FG_RETRIGGER = 9
RA_FG_SPINS = 10
RA_X_SUM = 11
RA_X_SQUARE = 12
RA_MAX_SINGLE_WIN = 13
RA_MAX_WIN_HITS = 14
RA_FG_SESSIONS = 15
RA_BG_CASCADES = 16
RA_FG_CASCADES = 17
RA_MAX_FG_MULTIPLIER = 18
RA_RETRY_TOTAL = 19
RA_RETRY_LIMIT_EXCEEDED = 20
RA_RETRY_FAIL_BG_RANGE = 21
RA_RETRY_FAIL_BG_FREEGAME = 22
RA_RETRY_FAIL_FG = 23
RA_TRIGGER_FG_PAY_BG = 24
RA_TRIGGER_FG_BG_MAX_PAY = 25

SCENE_BG_SPINS = 0
SCENE_FG_SESSIONS = 1
SCENE_FG_SPINS = 2

CASCADE_LABELS = ["Cascade 1", "Cascade 2", "Cascade 3", "Cascade 4", "Cascade 5+"]
CASCADE_DIST_LABELS = ["0", "1", "2", "3", "4", "5+"]
FG_MULTIPLIER_LABELS = [str(value) for value in range(1, 15)] + ["15+"]


@njit(nogil=True)
def calc_coin_in(bet_mode, bet_multi):
    if bet_mode == MODE_NORMALBET:
        return DEFAULT_COIN_IN * NORMALBET * bet_multi
    if bet_mode == MODE_FEATUREBUY:
        return DEFAULT_COIN_IN * NORMALBET * FEATUREBUY * bet_multi
    if bet_mode == MODE_EXTRABET:
        raise ValueError("101016 / H0281 does not provide Extra Bet")
    raise ValueError(f"Unsupported bet mode: {bet_mode}")


def format_bet_mode_label(bet_mode):
    if bet_mode == MODE_FEATUREBUY:
        return "Feature Buy"
    if bet_mode == MODE_EXTRABET:
        return "Extra Bet"
    return "Normal Bet"


@njit(nogil=True)
def choose_parameter_set(weights):
    total = float(np.sum(weights))
    if total <= 0:
        return 1
    pick = np.random.random() * total
    cumulative = 0.0
    for index, weight in enumerate(weights):
        cumulative += float(weight)
        if pick < cumulative:
            return index + 1
    return len(weights)


@njit(nogil=True)
def pick_card(card_profile_index):
    card_count = int(CARD_COUNTS[card_profile_index])
    if card_count <= 0:
        return -1
    total = int(CARD_WEIGHT_CUM[card_profile_index, card_count - 1])
    if total <= 0:
        return -1
    pick = np.random.randint(0, total)
    return int(np.searchsorted(CARD_WEIGHT_CUM[card_profile_index, :card_count], pick, side="right"))


@njit(nogil=True)
def is_card_match(card_profile_index, card_index, score, card_coin_in, triggered_free_game):
    if card_index < 0:
        return True
    if CARD_TYPES[card_profile_index, card_index] == CARD_TYPE_FREE_GAME:
        return bool(triggered_free_game)
    multiplier = score / card_coin_in if card_coin_in else 0.0
    return multiplier > CARD_MIN[card_profile_index, card_index] and multiplier <= CARD_MAX[card_profile_index, card_index]


@njit(nogil=True)
def run_freegame_session_stats(trigger_c1_count, enable_m1_multiplier=True):
    initial_spins = 10 + max(0, trigger_c1_count - 4) * 2
    remaining_spins = initial_spins
    initial_remaining = initial_spins
    total_scheduled_spins = initial_spins
    max_rounds = 50

    total_win = 0.0
    multiplier = FG_INITIAL_MULTIPLIER
    m1_count = 0
    total_spins = 0
    hit_spins = 0
    retrigger_count = 0
    m1_spin_count = 0
    big_m1_spin_count = 0
    cascade_pay = np.zeros(5, dtype=np.float64)
    cascade_dist = np.zeros(6, dtype=np.int64)

    while remaining_spins > 0:
        if initial_remaining > 0:
            param_set = choose_parameter_set(FREE_REEL_WEIGHT)
            initial_remaining -= 1
        else:
            param_set = choose_parameter_set(FREE_TRIGGER_REEL)

        previous_multiplier = multiplier
        previous_m1_count = m1_count
        win, c1_final, multiplier, m1_count, spin_cascade_pay = freegame_single_spin(
            param_set,
            multiplier,
            m1_count,
            enable_m1_multiplier,
        )
        spin_m1_count = m1_count - previous_m1_count
        if spin_m1_count > 0:
            m1_spin_count += 1
            if multiplier - previous_multiplier > 2 * spin_m1_count:
                big_m1_spin_count += 1
        total_win += win
        total_spins += 1
        remaining_spins -= 1
        cascade_pay += spin_cascade_pay
        cascade_dist[min(int(np.count_nonzero(spin_cascade_pay)), 5)] += 1
        if win > 0:
            hit_spins += 1

        if c1_final >= 4:
            requested_spins = 10 + (c1_final - 4) * 2
            available_spins = max_rounds - total_scheduled_spins
            if available_spins > 0:
                add_spins = min(requested_spins, available_spins)
                remaining_spins += add_spins
                total_scheduled_spins += add_spins
                retrigger_count += 1

    return (
        total_win,
        int(multiplier),
        total_spins,
        hit_spins,
        retrigger_count,
        cascade_pay,
        cascade_dist,
        m1_spin_count,
        big_m1_spin_count,
    )


@njit(nogil=True)
def threshold_index(win_multiplier):
    for index, upper_bound in enumerate(THRESHOLD_RECORD):
        if win_multiplier <= upper_bound:
            return index
    return len(THRESHOLD_RECORD) - 1


@njit(nogil=True)
def simulator_chunk(total_round, bet_mode, bet_multi, enable_m1_multiplier):
    record_data = np.zeros(RECORD_SIZE, dtype=np.int64)
    coin_in = calc_coin_in(bet_mode, bet_multi)
    card_coin_in = DEFAULT_COIN_IN * NORMALBET * bet_multi
    bg_card_profile = CARD_PROFILE_NEWBIE_BG if CARD_SYSTEM_IS_NEWBIE else CARD_PROFILE_OLDHAND_BG
    fg_card_profile = CARD_PROFILE_NEWBIE_FG if CARD_SYSTEM_IS_NEWBIE else CARD_PROFILE_OLDHAND_FG
    retry_total = 0
    retry_limit_exceeded = 0
    retry_fail_bg_range = 0
    retry_fail_bg_freegame = 0
    retry_fail_fg = 0

    for _ in range(int(total_round)):
        bg_win = 0.0
        fg_win = 0.0
        bg_cascade_pay = np.zeros(5, dtype=np.float64)
        fg_cascade_pay = np.zeros(5, dtype=np.float64)
        fg_cascade_dist = np.zeros(6, dtype=np.int64)
        scatter_count = 4 if bet_mode == MODE_FEATUREBUY else 0
        fg_spins = 0
        fg_hit_spins = 0
        fg_retriggers = 0
        fg_final_multiplier = 1
        fg_m1_spins = 0
        fg_big_m1_spins = 0
        fg_triggered = 0
        bg_final_multiplier = 1
        bg_m1_count = 0

        if bet_mode == MODE_NORMALBET:
            bg_card_index = pick_card(bg_card_profile) if CARD_SYSTEM_ENABLED else -1
            bg_retry_count = 0
            while True:
                param_set = choose_parameter_set(REEL_WEIGHT)
                (
                    bg_win,
                    scatter_count,
                    bg_final_multiplier,
                    _,
                    _,
                    bg_cascade_pay,
                    bg_m1_count,
                ) = single_spin(
                    param_set,
                    enable_m1_multiplier,
                )
                triggered_free_game = scatter_count >= 4
                if not CARD_SYSTEM_ENABLED or bg_card_index < 0:
                    break
                if CARD_TYPES[bg_card_profile, bg_card_index] == CARD_TYPE_FREE_GAME:
                    bg_matches = triggered_free_game
                    fail_is_free_game = True
                else:
                    bg_matches = not triggered_free_game and is_card_match(
                        bg_card_profile,
                        bg_card_index,
                        bg_win * bet_multi,
                        card_coin_in,
                        False,
                    )
                    fail_is_free_game = False
                if bg_matches:
                    break
                retry_total += 1
                bg_retry_count += 1
                if fail_is_free_game:
                    retry_fail_bg_freegame += 1
                else:
                    retry_fail_bg_range += 1
                if bg_retry_count >= CARD_RETRY_LIMIT:
                    retry_limit_exceeded += 1
                    break

            if scatter_count >= 4:
                fg_triggered = 1
                needs_fg_card = CARD_SYSTEM_ENABLED and bg_card_index >= 0 and CARD_TYPES[bg_card_profile, bg_card_index] == CARD_TYPE_FREE_GAME
                fg_card_index = pick_card(fg_card_profile) if needs_fg_card else -1
                fg_retry_count = 0
                while True:
                    (
                        fg_win,
                        fg_final_multiplier,
                        fg_spins,
                        fg_hit_spins,
                        fg_retriggers,
                        fg_cascade_pay,
                        fg_cascade_dist,
                        fg_m1_spins,
                        fg_big_m1_spins,
                    ) = run_freegame_session_stats(scatter_count, enable_m1_multiplier)
                    if not needs_fg_card or is_card_match(
                        fg_card_profile,
                        fg_card_index,
                        fg_win * bet_multi,
                        card_coin_in,
                        True,
                    ):
                        break
                    retry_total += 1
                    retry_fail_fg += 1
                    fg_retry_count += 1
                    if fg_retry_count >= CARD_RETRY_LIMIT:
                        retry_limit_exceeded += 1
                        break
        elif bet_mode == MODE_FEATUREBUY:
            # BF_Symbol only builds the trigger screen. Its restricted stop
            # weights must never produce a Ways payout; four SC are supplied
            # by the Feature Buy flow rather than the reel strip.
            bf_win, _, _, _, _, _, _ = single_spin(3, enable_m1_multiplier)
            if bf_win != 0.0:
                raise RuntimeError("BF_Symbol produced an unexpected payout")
            bg_win = 0.0
            scatter_count = 4
            fg_triggered = 1
            package_card_index = pick_card(CARD_PROFILE_BUY_FEATURE) if CARD_SYSTEM_ENABLED else -1
            fg_retry_count = 0
            while True:
                (
                    fg_win,
                    fg_final_multiplier,
                    fg_spins,
                    fg_hit_spins,
                    fg_retriggers,
                    fg_cascade_pay,
                    fg_cascade_dist,
                    fg_m1_spins,
                    fg_big_m1_spins,
                ) = run_freegame_session_stats(4, enable_m1_multiplier)
                if not CARD_SYSTEM_ENABLED or is_card_match(
                    CARD_PROFILE_BUY_FEATURE,
                    package_card_index,
                    fg_win * bet_multi,
                    card_coin_in,
                    True,
                ):
                    break
                retry_total += 1
                retry_fail_fg += 1
                fg_retry_count += 1
                if fg_retry_count >= CARD_RETRY_LIMIT:
                    retry_limit_exceeded += 1
                    break
        else:
            calc_coin_in(bet_mode, bet_multi)

        bg_win *= bet_multi
        fg_win *= bet_multi
        bg_cascade_pay *= bet_multi
        fg_cascade_pay *= bet_multi
        total_win = bg_win + fg_win
        win_multiplier = total_win / coin_in if coin_in else 0.0
        x_scaled = int(round(win_multiplier * 1_000_000))

        record_data[R_ALL, RA_TOTAL_ROUNDS] += 1
        record_data[R_ALL, RA_COIN_IN_SUM] += coin_in
        record_data[R_ALL, RA_PAY_TOTAL] += int(round(total_win))
        record_data[R_ALL, RA_PAY_BG] += int(round(bg_win))
        record_data[R_ALL, RA_PAY_FG] += int(round(fg_win))
        if fg_triggered:
            record_data[R_ALL, RA_TRIGGER_FG_PAY_BG] += int(round(bg_win))
            record_data[R_ALL, RA_TRIGGER_FG_BG_MAX_PAY] = max(
                record_data[R_ALL, RA_TRIGGER_FG_BG_MAX_PAY],
                int(round(bg_win)),
            )
        record_data[R_ALL, RA_HITS_TOTAL] += int(total_win > 0)
        record_data[R_ALL, RA_HITS_BG] += int(bg_win > 0)
        record_data[R_ALL, RA_HITS_FG_SPIN] += fg_hit_spins
        record_data[R_ALL, RA_FG_TRIGGER] += fg_triggered
        record_data[R_ALL, RA_FG_RETRIGGER] += fg_retriggers
        record_data[R_ALL, RA_FG_SPINS] += fg_spins
        record_data[R_ALL, RA_X_SUM] += x_scaled
        record_data[R_ALL, RA_X_SQUARE] += int(round(win_multiplier * win_multiplier * 1_000_000))
        record_data[R_ALL, RA_FG_SESSIONS] += fg_triggered
        record_data[R_ALL, RA_BG_CASCADES] += int(np.count_nonzero(bg_cascade_pay))
        record_data[R_ALL, RA_FG_CASCADES] += int(np.count_nonzero(fg_cascade_pay))
        record_data[R_ALL, RA_MAX_FG_MULTIPLIER] = max(record_data[R_ALL, RA_MAX_FG_MULTIPLIER], fg_final_multiplier)

        rounded_total_win = int(round(total_win))
        if rounded_total_win > record_data[R_ALL, RA_MAX_SINGLE_WIN]:
            record_data[R_ALL, RA_MAX_SINGLE_WIN] = rounded_total_win
            record_data[R_ALL, RA_MAX_WIN_HITS] = 1
        elif rounded_total_win == record_data[R_ALL, RA_MAX_SINGLE_WIN]:
            record_data[R_ALL, RA_MAX_WIN_HITS] += 1

        multiplier_line_coin_in = card_coin_in
        bg_line_index = threshold_index(bg_win / multiplier_line_coin_in if multiplier_line_coin_in else 0.0)
        fg_line_index = threshold_index(fg_win / multiplier_line_coin_in if multiplier_line_coin_in else 0.0)
        overall_line_index = threshold_index(total_win / multiplier_line_coin_in if multiplier_line_coin_in else 0.0)

        record_data[R_MULTIPLIER_COUNT_BG, bg_line_index] += 1
        record_data[R_MULTIPLIER_PAY_BG, bg_line_index] += int(round(bg_win))
        record_data[R_MULTIPLIER_COUNT_OA, overall_line_index] += 1
        record_data[R_MULTIPLIER_PAY_OA, overall_line_index] += rounded_total_win

        bg_cascade_count = min(int(np.count_nonzero(bg_cascade_pay)), 5)
        record_data[R_BG_INTERVAL_HITS, bg_line_index] += int(bg_win > 0)
        record_data[R_BG_INTERVAL_M1, bg_line_index] += int(bg_m1_count > 0)
        record_data[R_BG_INTERVAL_BIG_M1, bg_line_index] += int(
            bg_m1_count > 0 and bg_final_multiplier > 2 * bg_m1_count
        )
        if bg_cascade_count > 0:
            record_data[R_BG_INTERVAL_CASCADE_1 + bg_cascade_count - 1, bg_line_index] += 1
        record_data[R_BG_INTERVAL_MULT_SUM, bg_line_index] += int(bg_final_multiplier)
        record_data[R_BG_INTERVAL_MULT_MAX, bg_line_index] = max(
            record_data[R_BG_INTERVAL_MULT_MAX, bg_line_index],
            int(bg_final_multiplier),
        )

        if fg_triggered:
            record_data[R_MULTIPLIER_COUNT_FG, fg_line_index] += 1
            record_data[R_MULTIPLIER_PAY_FG, fg_line_index] += int(round(fg_win))
            record_data[R_FG_INTERVAL_SPINS, fg_line_index] += fg_spins
            record_data[R_FG_INTERVAL_HIT_SPINS, fg_line_index] += fg_hit_spins
            record_data[R_FG_INTERVAL_M1_SPINS, fg_line_index] += fg_m1_spins
            record_data[R_FG_INTERVAL_BIG_M1_SPINS, fg_line_index] += fg_big_m1_spins
            for cascade_index in range(1, 6):
                record_data[R_FG_INTERVAL_CASCADE_1 + cascade_index - 1, fg_line_index] += fg_cascade_dist[cascade_index]
            record_data[R_FG_INTERVAL_RETRIGGER_SESSIONS, fg_line_index] += int(fg_retriggers > 0)
            record_data[R_FG_INTERVAL_FINAL_MULT_SUM, fg_line_index] += int(fg_final_multiplier)
            record_data[R_FG_INTERVAL_FINAL_MULT_MAX, fg_line_index] = max(
                record_data[R_FG_INTERVAL_FINAL_MULT_MAX, fg_line_index],
                int(fg_final_multiplier),
            )
        for index in range(5):
            record_data[R_BG_CASCADE_PAY, index] += int(round(bg_cascade_pay[index]))
            record_data[R_FG_CASCADE_PAY, index] += int(round(fg_cascade_pay[index]))
        if bet_mode == MODE_NORMALBET:
            bg_cascade_index = min(int(np.count_nonzero(bg_cascade_pay)), 5)
            record_data[R_BG_CASCADE_DIST, bg_cascade_index] += 1
        for index in range(6):
            record_data[R_FG_CASCADE_DIST, index] += fg_cascade_dist[index]
        scatter_index = min(max(int(scatter_count), 0), 7)
        record_data[R_SCATTER_COUNT, scatter_index] += 1
        if fg_triggered:
            multiplier_index = min(max(int(fg_final_multiplier) - 1, 0), 14)
            record_data[R_FG_FINAL_MULTIPLIER, multiplier_index] += 1
        record_data[R_SCENE, SCENE_BG_SPINS] += int(bet_mode == MODE_NORMALBET)
        record_data[R_SCENE, SCENE_FG_SESSIONS] += fg_triggered
        record_data[R_SCENE, SCENE_FG_SPINS] += fg_spins

    record_data[R_ALL, RA_RETRY_TOTAL] += retry_total
    record_data[R_ALL, RA_RETRY_LIMIT_EXCEEDED] += retry_limit_exceeded
    record_data[R_ALL, RA_RETRY_FAIL_BG_RANGE] += retry_fail_bg_range
    record_data[R_ALL, RA_RETRY_FAIL_BG_FREEGAME] += retry_fail_bg_freegame
    record_data[R_ALL, RA_RETRY_FAIL_FG] += retry_fail_fg
    return record_data


def build_chunk_rounds(total_round, threads):
    threads = max(1, min(int(threads), int(total_round) if total_round > 0 else 1))
    base = total_round // threads
    extra = total_round % threads
    return [base + (1 if index < extra else 0) for index in range(threads) if base + (1 if index < extra else 0) > 0]


def merge_record_data(chunks):
    merged = np.zeros(RECORD_SIZE, dtype=np.int64)
    global_max = max(int(chunk[R_ALL, RA_MAX_SINGLE_WIN]) for chunk in chunks)
    global_max_multiplier = max(int(chunk[R_ALL, RA_MAX_FG_MULTIPLIER]) for chunk in chunks)
    bg_interval_max = np.max(
        np.stack([chunk[R_BG_INTERVAL_MULT_MAX] for chunk in chunks]), axis=0
    )
    fg_interval_max = np.max(
        np.stack([chunk[R_FG_INTERVAL_FINAL_MULT_MAX] for chunk in chunks]), axis=0
    )
    for chunk in chunks:
        merged += chunk
    merged[R_ALL, RA_MAX_SINGLE_WIN] = global_max
    merged[R_ALL, RA_MAX_WIN_HITS] = sum(int(chunk[R_ALL, RA_MAX_WIN_HITS]) for chunk in chunks if int(chunk[R_ALL, RA_MAX_SINGLE_WIN]) == global_max)
    merged[R_ALL, RA_MAX_FG_MULTIPLIER] = global_max_multiplier
    merged[R_BG_INTERVAL_MULT_MAX] = bg_interval_max
    merged[R_FG_INTERVAL_FINAL_MULT_MAX] = fg_interval_max
    return merged


def run_simulation(total_round=TOTAL_ROUNDS, bet_mode=BET_MODE, bet_multi=BET_MULTI, threads=THREADS):
    total_round = int(total_round)
    bet_mode = int(bet_mode)
    bet_multi = int(bet_multi)
    if total_round <= 0:
        raise ValueError("TOTAL_ROUNDS must be positive")
    if bet_mode not in SUPPORTED_BET_MODES:
        calc_coin_in(bet_mode, bet_multi)

    # Compile the BG/FG paths and the complete chunk loop before timing.
    single_spin(1, ENABLE_M1_MULTIPLIER)
    single_spin(3, ENABLE_M1_MULTIPLIER)
    freegame_single_spin(1, 1, 0, ENABLE_M1_MULTIPLIER)
    simulator_chunk(1, bet_mode, bet_multi, ENABLE_M1_MULTIPLIER)

    chunk_rounds = build_chunk_rounds(total_round, threads)
    start = time.perf_counter()
    if len(chunk_rounds) == 1:
        record_data = simulator_chunk(chunk_rounds[0], bet_mode, bet_multi, ENABLE_M1_MULTIPLIER)
    else:
        with ThreadPoolExecutor(max_workers=len(chunk_rounds)) as executor:
            futures = [
                executor.submit(
                    simulator_chunk,
                    rounds,
                    bet_mode,
                    bet_multi,
                    ENABLE_M1_MULTIPLIER,
                )
                for rounds in chunk_rounds
            ]
            record_data = merge_record_data([future.result() for future in futures])
    duration = time.perf_counter() - start
    return record_data, duration, calc_coin_in(bet_mode, bet_multi)


def format_threshold_labels(thresholds):
    labels = []
    for index, current in enumerate(thresholds):
        if index == 0:
            labels.append("0")
        else:
            labels.append(f"{thresholds[index - 1]} < X <= {current}")
    return labels


def build_result_frames(record_data, total_round, duration, coin_in, bet_mode, bet_multi, threads=THREADS):
    values = record_data.astype(np.float64)
    pay_total = values[R_ALL, RA_PAY_TOTAL]
    pay_bg = values[R_ALL, RA_PAY_BG]
    pay_fg = values[R_ALL, RA_PAY_FG]
    fg_sessions = values[R_ALL, RA_FG_SESSIONS]
    fg_spins = values[R_ALL, RA_FG_SPINS]
    coin_in_sum = values[R_ALL, RA_COIN_IN_SUM]

    rtp_total = pay_total / coin_in_sum if coin_in_sum else 0.0
    rtp_bg = pay_bg / coin_in_sum if coin_in_sum else 0.0
    rtp_fg = pay_fg / coin_in_sum if coin_in_sum else 0.0
    hit_rate_total = values[R_ALL, RA_HITS_TOTAL] / total_round if total_round else 0.0
    bg_spins = values[R_SCENE, SCENE_BG_SPINS]
    hit_rate_bg = values[R_ALL, RA_HITS_BG] / bg_spins if bg_spins else 0.0
    hit_rate_fg = values[R_ALL, RA_HITS_FG_SPIN] / fg_spins if fg_spins else 0.0
    fg_trigger_rate = values[R_ALL, RA_FG_TRIGGER] / total_round if total_round else 0.0
    retrigger_rate = values[R_ALL, RA_FG_RETRIGGER] / fg_sessions if fg_sessions else 0.0
    avg_fg_spins = fg_spins / fg_sessions if fg_sessions else 0.0
    trigger_fg_bg_pay = values[R_ALL, RA_TRIGGER_FG_PAY_BG]
    trigger_fg_bg_count = int(values[R_ALL, RA_FG_TRIGGER])
    trigger_fg_bg_max_pay = int(values[R_ALL, RA_TRIGGER_FG_BG_MAX_PAY])
    x_sum = values[R_ALL, RA_X_SUM] / 1_000_000
    x_square = values[R_ALL, RA_X_SQUARE] / 1_000_000
    volatility_std = math.sqrt(max(0.0, x_square / total_round - (x_sum / total_round) ** 2))
    max_win_x = values[R_ALL, RA_MAX_SINGLE_WIN] / coin_in if coin_in else 0.0
    retry_total = int(values[R_ALL, RA_RETRY_TOTAL])
    card_profile = "off"
    if CARD_SYSTEM_ENABLED:
        card_profile = ("newbie" if CARD_SYSTEM_IS_NEWBIE else "oldhand") if bet_mode == MODE_NORMALBET else "buy_feature"

    bg_interval_count = values[R_MULTIPLIER_COUNT_BG, : len(THRESHOLD_RECORD)]
    fg_interval_count = values[R_MULTIPLIER_COUNT_FG, : len(THRESHOLD_RECORD)]
    overall_interval_count = values[R_MULTIPLIER_COUNT_OA, : len(THRESHOLD_RECORD)]
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

    bg_m1_rate = (
        values[R_BG_INTERVAL_M1, : len(THRESHOLD_RECORD)].sum() / bg_interval_count.sum()
        if bg_interval_count.sum()
        else 0.0
    )
    bg_big_m1_rate = (
        values[R_BG_INTERVAL_BIG_M1, : len(THRESHOLD_RECORD)].sum() / bg_interval_count.sum()
        if bg_interval_count.sum()
        else 0.0
    )
    fg_m1_rate = (
        values[R_FG_INTERVAL_M1_SPINS, : len(THRESHOLD_RECORD)].sum() / fg_interval_spins.sum()
        if fg_interval_spins.sum()
        else 0.0
    )
    fg_big_m1_rate = (
        values[R_FG_INTERVAL_BIG_M1_SPINS, : len(THRESHOLD_RECORD)].sum() / fg_interval_spins.sum()
        if fg_interval_spins.sum()
        else 0.0
    )
    fg_retrigger_session_rate = (
        values[R_FG_INTERVAL_RETRIGGER_SESSIONS, : len(THRESHOLD_RECORD)].sum() / fg_interval_count.sum()
        if fg_interval_count.sum()
        else 0.0
    )
    avg_bg_final_multiplier = (
        values[R_BG_INTERVAL_MULT_SUM, : len(THRESHOLD_RECORD)].sum() / bg_interval_count.sum()
        if bg_interval_count.sum()
        else 0.0
    )
    avg_fg_final_multiplier = (
        values[R_FG_INTERVAL_FINAL_MULT_SUM, : len(THRESHOLD_RECORD)].sum() / fg_interval_count.sum()
        if fg_interval_count.sum()
        else 0.0
    )
    max_bg_final_multiplier = int(values[R_BG_INTERVAL_MULT_MAX, : len(THRESHOLD_RECORD)].max())
    max_fg_final_multiplier = int(values[R_FG_INTERVAL_FINAL_MULT_MAX, : len(THRESHOLD_RECORD)].max())
    multiplier_line_coin_in = DEFAULT_COIN_IN * NORMALBET * bet_multi

    base_rows = [
        ("game_id", GAME_ID, ""),
        ("parsheet_id", PARSHEET_ID, ""),
        ("game_name", GAME_NAME, ""),
        ("game_name_zh", GAME_NAME_ZH, ""),
        ("version", CONFIG_VERSION, ""),
        ("config", CONFIG_FILE, ""),
        ("bet_mode", format_bet_mode_label(bet_mode), ""),
        ("bet_multi", bet_multi, ""),
        ("coin_in", coin_in, ""),
        ("multiplier_line_basis", "normal_bet", "all intervals use Normal Bet coin-in"),
        ("multiplier_line_coin_in", multiplier_line_coin_in, "interval divisor"),
        ("multiplier_line_bg_basis", "BG spin", "BG rates use paid BG spins in each BG-pay interval"),
        ("multiplier_line_fg_basis", "FG session", "FG sessions are grouped by total session pay; spin rates use spins in those sessions"),
        ("total_rounds", int(total_round), ""),
        ("threads", int(threads), ""),
        ("duration_sec", round(duration, 6), ""),
        ("", "", ""),
        ("rtp_total", rtp_total, ""),
        ("rtp_bg", rtp_bg, ""),
        ("rtp_fg", rtp_fg, ""),
        ("", "", ""),
        ("hit_rate_total", hit_rate_total, ""),
        ("hit_rate_bg", hit_rate_bg, ""),
        ("hit_rate_fg", hit_rate_fg, ""),
        ("m1_appear_rate_bg", bg_m1_rate, "BG spins containing at least one M1 / BG spins"),
        ("m1_appear_rate_fg", fg_m1_rate, "FG spins containing at least one M1 / FG spins"),
        ("m1_2x1_plus_rate_bg", bg_big_m1_rate, "BG spins containing at least one M1 of size 2x1 or larger / BG spins"),
        ("m1_2x1_plus_rate_fg", fg_big_m1_rate, "FG spins containing at least one M1 of size 2x1 or larger / FG spins"),
        ("", "", ""),
        ("fg_trigger_rate", fg_trigger_rate, ""),
        ("retrigger_per_fg", retrigger_rate, "events / FG session"),
        ("retrigger_rate", fg_retrigger_session_rate, "sessions with retrigger / FG sessions"),
        ("avg_fg_spins", avg_fg_spins, ""),
        ("cascade_rate_basis", "exact", "Cascade 1/2/3/4 are exact counts; Cascade 5+ is capped into one group"),
        ("avg_final_multiplier_bg", avg_bg_final_multiplier, "average final accumulated multiplier per BG spin"),
        ("max_final_multiplier_bg", max_bg_final_multiplier, "maximum final accumulated multiplier among BG spins"),
        ("avg_final_multiplier_fg", avg_fg_final_multiplier, "average final accumulated multiplier per FG session"),
        ("max_final_multiplier_fg", max_fg_final_multiplier, "maximum final accumulated multiplier among FG sessions"),
        ("trigger_fg_bg_pay", int(trigger_fg_bg_pay), ""),
        ("trigger_fg_bg_count", trigger_fg_bg_count, ""),
        ("trigger_fg_bg_max_pay", trigger_fg_bg_max_pay, ""),
        ("", "", ""),
        ("volatility_std", volatility_std, ""),
        ("max_win_x", max_win_x, ""),
        ("max_win_hits", int(values[R_ALL, RA_MAX_WIN_HITS]), ""),
        ("", "", ""),
        ("card_system", "on" if CARD_SYSTEM_ENABLED else "off", ""),
        ("card_system_profile", card_profile, ""),
        ("retry_limit", CARD_RETRY_LIMIT if CARD_SYSTEM_ENABLED else 0, ""),
        ("retry_total", retry_total, ""),
        ("avg_retry", retry_total / total_round if total_round else 0.0, ""),
        ("retry_limit_exceeded", int(values[R_ALL, RA_RETRY_LIMIT_EXCEEDED]), ""),
        ("retry_fail_bg_range", int(values[R_ALL, RA_RETRY_FAIL_BG_RANGE]), ""),
        ("retry_fail_bg_freegame", int(values[R_ALL, RA_RETRY_FAIL_BG_FREEGAME]), ""),
        ("retry_fail_fg", int(values[R_ALL, RA_RETRY_FAIL_FG]), ""),
    ]
    df_base = pd.DataFrame(base_rows, columns=["Index", "Value", "Value2"])

    scene_rows = [
        {
            "Scene": "Base Game",
            "Spins_or_Sessions": int(bg_spins),
            "Hits": int(values[R_ALL, RA_HITS_BG]),
            "Pay": int(pay_bg),
            "RTP": rtp_bg,
        },
        {
            "Scene": "Free Game",
            "Spins_or_Sessions": int(fg_spins),
            "Hits": int(values[R_ALL, RA_HITS_FG_SPIN]),
            "Pay": int(pay_fg),
            "RTP": rtp_fg,
        },
    ]
    df_scene = pd.DataFrame(scene_rows)

    cascade_rows = []
    for scene, row_index, denominator in (
        ("BG", R_BG_CASCADE_PAY, bg_spins),
        ("FG", R_FG_CASCADE_PAY, fg_spins),
    ):
        for index, label in enumerate(CASCADE_LABELS):
            pay = int(record_data[row_index, index])
            cascade_rows.append(
                {
                    "Scene": scene,
                    "Cascade": label,
                    "Pay": pay,
                    "Average_Pay": pay / denominator if denominator else 0.0,
                }
            )
    df_cascade = pd.DataFrame(cascade_rows)

    cascade_dist_rows = []
    for scene, row_index, denominator in (
        ("BG", R_BG_CASCADE_DIST, bg_spins),
        ("FG", R_FG_CASCADE_DIST, fg_spins),
    ):
        for index, label in enumerate(CASCADE_DIST_LABELS):
            count = int(record_data[row_index, index])
            cascade_dist_rows.append(
                {
                    "Scene": scene,
                    "Cascade_Count": label,
                    "Count": count,
                    "Rate": count / denominator if denominator else 0.0,
                }
            )
    df_cascade_dist = pd.DataFrame(cascade_dist_rows)

    scatter_total = values[R_SCATTER_COUNT, :8].sum()
    df_scatter = pd.DataFrame(
        {
            "Scatter": [str(value) for value in range(7)] + ["7+"],
            "Count": record_data[R_SCATTER_COUNT, :8],
            "Rate": record_data[R_SCATTER_COUNT, :8] / scatter_total if scatter_total else np.zeros(8),
        }
    )
    multiplier_total = values[R_FG_FINAL_MULTIPLIER, :15].sum()
    df_fg_multiplier = pd.DataFrame(
        {
            "FG_Final_Multiplier": FG_MULTIPLIER_LABELS,
            "Count": record_data[R_FG_FINAL_MULTIPLIER, :15],
            "Rate": record_data[R_FG_FINAL_MULTIPLIER, :15] / multiplier_total if multiplier_total else np.zeros(15),
        }
    )
    df_multiplier_line = pd.DataFrame(
        {
            "Interval": format_threshold_labels(THRESHOLD_RECORD),
            "BG_Count": record_data[R_MULTIPLIER_COUNT_BG, : len(THRESHOLD_RECORD)],
            "BG_Pay": record_data[R_MULTIPLIER_PAY_BG, : len(THRESHOLD_RECORD)],
            "BG_Hit_Rate": divide(values[R_BG_INTERVAL_HITS, : len(THRESHOLD_RECORD)], bg_interval_count),
            "BG_M1_Appear_Rate": divide(values[R_BG_INTERVAL_M1, : len(THRESHOLD_RECORD)], bg_interval_count),
            "BG_M1_2x1Plus_Rate": divide(values[R_BG_INTERVAL_BIG_M1, : len(THRESHOLD_RECORD)], bg_interval_count),
            "BG_Cascade_1_Rate": divide(values[R_BG_INTERVAL_CASCADE_1, : len(THRESHOLD_RECORD)], bg_interval_count),
            "BG_Cascade_2_Rate": divide(values[R_BG_INTERVAL_CASCADE_2, : len(THRESHOLD_RECORD)], bg_interval_count),
            "BG_Cascade_3_Rate": divide(values[R_BG_INTERVAL_CASCADE_3, : len(THRESHOLD_RECORD)], bg_interval_count),
            "BG_Cascade_4_Rate": divide(values[R_BG_INTERVAL_CASCADE_4, : len(THRESHOLD_RECORD)], bg_interval_count),
            "BG_Cascade_5Plus_Rate": divide(values[R_BG_INTERVAL_CASCADE_5P, : len(THRESHOLD_RECORD)], bg_interval_count),
            "BG_Final_Avg_Multiplier": divide(values[R_BG_INTERVAL_MULT_SUM, : len(THRESHOLD_RECORD)], bg_interval_count),
            "BG_Final_Max_Multiplier": record_data[R_BG_INTERVAL_MULT_MAX, : len(THRESHOLD_RECORD)],
            "FG_Session_Count": record_data[R_MULTIPLIER_COUNT_FG, : len(THRESHOLD_RECORD)],
            "FG_Pay": record_data[R_MULTIPLIER_PAY_FG, : len(THRESHOLD_RECORD)],
            "FG_Spin_Count": record_data[R_FG_INTERVAL_SPINS, : len(THRESHOLD_RECORD)],
            "FG_Hit_Rate": divide(values[R_FG_INTERVAL_HIT_SPINS, : len(THRESHOLD_RECORD)], fg_interval_spins),
            "FG_M1_Appear_Rate": divide(values[R_FG_INTERVAL_M1_SPINS, : len(THRESHOLD_RECORD)], fg_interval_spins),
            "FG_M1_2x1Plus_Rate": divide(values[R_FG_INTERVAL_BIG_M1_SPINS, : len(THRESHOLD_RECORD)], fg_interval_spins),
            "FG_Cascade_1_Rate": divide(values[R_FG_INTERVAL_CASCADE_1, : len(THRESHOLD_RECORD)], fg_interval_spins),
            "FG_Cascade_2_Rate": divide(values[R_FG_INTERVAL_CASCADE_2, : len(THRESHOLD_RECORD)], fg_interval_spins),
            "FG_Cascade_3_Rate": divide(values[R_FG_INTERVAL_CASCADE_3, : len(THRESHOLD_RECORD)], fg_interval_spins),
            "FG_Cascade_4_Rate": divide(values[R_FG_INTERVAL_CASCADE_4, : len(THRESHOLD_RECORD)], fg_interval_spins),
            "FG_Cascade_5Plus_Rate": divide(values[R_FG_INTERVAL_CASCADE_5P, : len(THRESHOLD_RECORD)], fg_interval_spins),
            "FG_Retrigger_Rate": divide(values[R_FG_INTERVAL_RETRIGGER_SESSIONS, : len(THRESHOLD_RECORD)], fg_interval_count),
            "FG_Final_Avg_Multiplier": divide(values[R_FG_INTERVAL_FINAL_MULT_SUM, : len(THRESHOLD_RECORD)], fg_interval_count),
            "FG_Final_Max_Multiplier": record_data[R_FG_INTERVAL_FINAL_MULT_MAX, : len(THRESHOLD_RECORD)],
            "Overall_Count": record_data[R_MULTIPLIER_COUNT_OA, : len(THRESHOLD_RECORD)],
            "Overall_Pay": record_data[R_MULTIPLIER_PAY_OA, : len(THRESHOLD_RECORD)],
        }
    )
    df_record = pd.DataFrame(record_data)
    summary = {
        "rtp_total": rtp_total,
        "rtp_bg": rtp_bg,
        "rtp_fg": rtp_fg,
        "hit_rate_total": hit_rate_total,
        "hit_rate_bg": hit_rate_bg,
        "hit_rate_fg": hit_rate_fg,
        "m1_appear_rate_bg": bg_m1_rate,
        "m1_appear_rate_fg": fg_m1_rate,
        "m1_2x1_plus_rate_bg": bg_big_m1_rate,
        "m1_2x1_plus_rate_fg": fg_big_m1_rate,
        "fg_trigger_rate": fg_trigger_rate,
        "fg_trigger_count": int(values[R_ALL, RA_FG_TRIGGER]),
        "trigger_fg_bg_pay": int(trigger_fg_bg_pay),
        "trigger_fg_bg_count": trigger_fg_bg_count,
        "trigger_fg_bg_max_pay": trigger_fg_bg_max_pay,
        "retrigger_rate": retrigger_rate,
        "retrigger_session_rate": fg_retrigger_session_rate,
        "avg_fg_spins": avg_fg_spins,
        "avg_final_multiplier_bg": avg_bg_final_multiplier,
        "max_final_multiplier_bg": max_bg_final_multiplier,
        "avg_final_multiplier_fg": avg_fg_final_multiplier,
        "max_final_multiplier_fg": max_fg_final_multiplier,
        "volatility_std": volatility_std,
        "max_win_x": max_win_x,
        "card_system": "on" if CARD_SYSTEM_ENABLED else "off",
        "card_system_profile": card_profile,
        "retry_total": retry_total,
        "avg_retry": retry_total / total_round if total_round else 0.0,
        "retry_limit_exceeded": int(values[R_ALL, RA_RETRY_LIMIT_EXCEEDED]),
        "retry_fail_bg_range": int(values[R_ALL, RA_RETRY_FAIL_BG_RANGE]),
        "retry_fail_bg_freegame": int(values[R_ALL, RA_RETRY_FAIL_BG_FREEGAME]),
        "retry_fail_fg": int(values[R_ALL, RA_RETRY_FAIL_FG]),
    }
    return df_base, df_scene, df_cascade, df_cascade_dist, df_scatter, df_fg_multiplier, df_multiplier_line, df_record, summary


def print_console_result(df_base, df_scene, df_cascade, df_cascade_dist, df_scatter, df_fg_multiplier):
    if SHOW_CONSOLE_SUMMARY:
        print("\n=== Fixed Result ===")
        for row in df_base.itertuples(index=False):
            print(f"{row.Index:<24} : {row.Value}")
    if SHOW_CONSOLE_DETAIL:
        print("\n=== By Game Result: Scene Summary ===")
        print(df_scene.to_string(index=False))
        print("\n=== By Game Result: Cascade ===")
        print(df_cascade.to_string(index=False))
        print("\n=== By Game Result: Cascade Distribution ===")
        print(df_cascade_dist.to_string(index=False))
        print("\n=== By Game Result: Scatter ===")
        print(df_scatter.to_string(index=False))
        print("\n=== By Game Result: FG Final Multiplier ===")
        print(df_fg_multiplier.to_string(index=False))


def format_rounds_tag(total_round):
    total_round = int(total_round)
    value = total_round
    exponent = 0
    while value > 0 and value % 10 == 0:
        value //= 10
        exponent += 1
    if value == 1 and exponent > 0:
        return f"10{exponent}"
    return str(total_round)


def format_version_tag(version):
    return re.sub(r"[^0-9A-Za-z]+", "", str(version or ""))


def format_elapsed_time(seconds):
    total_seconds = max(0, int(round(float(seconds))))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}h {minutes}m {secs}s"


def print_batch_summary(duration, summary, bet_mode):
    print(f"* game_id: {GAME_ID}", flush=True)
    print(f"* parsheet_id: {PARSHEET_ID}", flush=True)
    print(f"* version: {CONFIG_VERSION}", flush=True)
    print(f"* bet_mode: {format_bet_mode_label(bet_mode)}", flush=True)
    print(f"* duration: {format_elapsed_time(duration)}", flush=True)
    print(f"* rtp_total: {summary['rtp_total'] * 100:.2f}%", flush=True)
    print(f"* rtp_bg: {summary['rtp_bg'] * 100:.2f}%", flush=True)
    print(f"* rtp_fg: {summary['rtp_fg'] * 100:.2f}%", flush=True)
    print(f"* hit_rate_bg: {summary['hit_rate_bg']:.4f}", flush=True)
    print(f"* hit_rate_fg: {summary['hit_rate_fg']:.4f}", flush=True)
    print(
        f"* fg_trigger_rate: {summary['fg_trigger_rate']:.4f} " f"({summary['fg_trigger_count']} sessions)",
        flush=True,
    )
    print(f"* retrigger_per_fg: {summary['retrigger_rate']:.4f}", flush=True)
    print(f"* avg_fg_spins: {summary['avg_fg_spins']:.2f} spins", flush=True)
    print(f"* max_win: {summary['max_win_x']:.2f} x", flush=True)
    profile_text = f" ({summary['card_system_profile']})" if summary["card_system"] == "on" else ""
    print(f"* card_system: {summary['card_system']}{profile_text}", flush=True)
    print(f"* retry_total: {summary['retry_total']}", flush=True)
    print(f"* avg_retry: {summary['avg_retry']:.4f}", flush=True)
    print(f"* retry_limit_exceeded: {summary['retry_limit_exceeded']}", flush=True)
    print(f"* retry_fail_bg_range: {summary['retry_fail_bg_range']}", flush=True)
    print(f"* retry_fail_bg_freegame: {summary['retry_fail_bg_freegame']}", flush=True)
    print(f"* retry_fail_fg: {summary['retry_fail_fg']}", flush=True)


def output_report(
    df_base,
    df_scene,
    df_cascade,
    df_cascade_dist,
    df_scatter,
    df_fg_multiplier,
    df_multiplier_line,
    df_record,
    bet_mode,
    total_round,
):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    profile_suffix = ""
    if CARD_SYSTEM_ENABLED and bet_mode == MODE_NORMALBET:
        profile_suffix = "_newbie" if CARD_SYSTEM_IS_NEWBIE else "_oldhand"
    card_suffix = "_card" if CARD_SYSTEM_ENABLED else ""
    filename = f"{PARSHEET_ID}_{format_version_tag(CONFIG_VERSION)}_{timestamp}_" f"betmode{bet_mode}_{format_rounds_tag(total_round)}{profile_suffix}{card_suffix}.xlsx"
    path = OUTPUT_DIR / filename
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df_base.to_excel(writer, sheet_name="Base Info", index=False)
        df_scene.to_excel(writer, sheet_name="Scene Summary", index=False)
        df_cascade.to_excel(writer, sheet_name="Cascade", index=False)
        df_cascade_dist.to_excel(writer, sheet_name="Cascade Dist", index=False)
        df_scatter.to_excel(writer, sheet_name="Scatter Dist", index=False)
        df_fg_multiplier.to_excel(writer, sheet_name="FG Final Multi", index=False)
        df_multiplier_line.to_excel(writer, sheet_name="Multiplier Line", index=False)
        df_record.to_excel(writer, sheet_name="Record Data", index=False)

        base_sheet = writer.sheets["Base Info"]
        base_sheet.freeze_panes = "A2"
        base_sheet.auto_filter.ref = base_sheet.dimensions
        base_sheet.column_dimensions["A"].width = 34
        base_sheet.column_dimensions["B"].width = 22
        base_sheet.column_dimensions["C"].width = 42
        for row_index in range(2, len(df_base) + 2):
            metric_name = str(base_sheet.cell(row=row_index, column=1).value or "")
            if metric_name.startswith("rtp_") or "rate" in metric_name:
                base_sheet.cell(row=row_index, column=2).number_format = "0.0000%"
            elif "multiplier" in metric_name or metric_name in ("avg_fg_spins", "avg_retry"):
                base_sheet.cell(row=row_index, column=2).number_format = "0.0000"

        multiplier_sheet = writer.sheets["Multiplier Line"]
        multiplier_sheet.freeze_panes = "B2"
        multiplier_sheet.auto_filter.ref = multiplier_sheet.dimensions
        multiplier_sheet.column_dimensions["A"].width = 22
        for column_index, column_name in enumerate(df_multiplier_line.columns, start=1):
            column_letter = multiplier_sheet.cell(row=1, column=column_index).column_letter
            multiplier_sheet.column_dimensions[column_letter].width = max(
                14, min(28, len(str(column_name)) + 3)
            )
            if column_name.endswith("_Rate"):
                number_format = "0.0000%"
            elif column_name.endswith("_Count") or column_name.endswith("_Pay"):
                number_format = "#,##0"
            elif "Multiplier" in column_name:
                number_format = "0.0000"
            else:
                continue
            for row_index in range(2, len(df_multiplier_line) + 2):
                multiplier_sheet.cell(row=row_index, column=column_index).number_format = number_format
    return path


def run_single_spin_debug():
    param_set = choose_parameter_set(REEL_WEIGHT)
    result = single_spin(param_set, ENABLE_M1_MULTIPLIER)
    print("Single spin result:")
    print(f"param_set={param_set}, pay={result[0]}, scatter={result[1]}, " f"multiplier={result[2]}, initial_scatter={result[3]}, cascade_pay={result[5]}")


def run_all_combinations():
    total_jobs = len(BATCH_RUNS)
    for index, combo in enumerate(BATCH_RUNS, start=1):
        combo_env = os.environ.copy()
        combo_env["PYTHONUNBUFFERED"] = "1"
        combo_env["H028_CONFIG_FILE"] = combo["config_file"]
        combo_env["H028_BET_MODE"] = str(combo["bet_mode"])
        combo_env["H028_TOTAL_ROUNDS"] = str(combo["total_rounds"])
        combo_env["H028_CARD_SYSTEM_ENABLED"] = "true" if combo.get("card_system_enabled", CARD_SYSTEM_ENABLED) else "false"
        combo_env["H028_CARD_SYSTEM_IS_NEWBIE"] = "true" if combo.get("card_system_is_newbie", CARD_SYSTEM_IS_NEWBIE) else "false"
        combo_env["H028_RUN_ALL_COMBINATIONS"] = "false"
        combo_env["H028_BATCH_CHILD"] = "1"
        print(
            f"\n=== Batch {index}/{total_jobs}: config={combo['config_file']}, " f"bet_mode={combo['bet_mode']}, total_rounds={combo['total_rounds']}, " f"card={combo.get('card_system_enabled', CARD_SYSTEM_ENABLED)}, " f"newbie={combo.get('card_system_is_newbie', CARD_SYSTEM_IS_NEWBIE)} ===",
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
    if RUN_ALL_COMBINATIONS and os.environ.get("H028_BATCH_CHILD") != "1":
        run_all_combinations()
        return
    if RUN_SINGLE_SPIN_DEBUG:
        run_single_spin_debug()
        return

    record_data, duration, coin_in = run_simulation()
    frames = build_result_frames(
        record_data,
        TOTAL_ROUNDS,
        duration,
        coin_in,
        BET_MODE,
        BET_MULTI,
        THREADS,
    )
    df_base, df_scene, df_cascade, df_cascade_dist, df_scatter, df_fg_multiplier, df_multiplier_line, df_record, summary = frames
    print_console_result(df_base, df_scene, df_cascade, df_cascade_dist, df_scatter, df_fg_multiplier)
    print_batch_summary(duration, summary, BET_MODE)

    if OUTPUT_REPORT:
        report_path = output_report(
            df_base,
            df_scene,
            df_cascade,
            df_cascade_dist,
            df_scatter,
            df_fg_multiplier,
            df_multiplier_line,
            df_record,
            BET_MODE,
            TOTAL_ROUNDS,
        )
        print(f"\nReport: {report_path}")


if __name__ == "__main__":
    main()
