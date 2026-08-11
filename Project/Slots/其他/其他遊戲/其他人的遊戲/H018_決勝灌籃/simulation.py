#%%
"""
Slam Dunk Simulation Program v3
Uses data.json parameters, supports Numba JIT + multi-threading acceleration
Supports Free Game ticket bucket mechanism (special/high/mid/low 4 table draw)
"""

import json
import numpy as np
from numba import jit
import multiprocessing
import threading
import time
import math
from pathlib import Path


# ============================================================
# Ticket Bucket Settings
# ============================================================
# 
# ✅ Modify the values here, they will be automatically passed to simulation functions
# No need to manually sync other locations

# Initial trigger ticket bucket [special, high, mid, low]
INITIAL_TICKETS_3 = np.array([2, 30, 50, 295], dtype=np.int64)   # 3 C1: 10 spins
INITIAL_TICKETS_4 = np.array([2, 40, 70, 300], dtype=np.int64)   # 4 C1: 15 spins
INITIAL_TICKETS_5 = np.array([2, 50, 90, 300], dtype=np.int64)   # 5 C1: 20 spins

# Retrigger ticket bucket [special, high, mid, low]
RETRIGGER_TICKETS_3 = np.array([1, 20, 30, 200], dtype=np.int64)    # 3 C1: +10 spins
RETRIGGER_TICKETS_4 = np.array([1, 20, 50, 200], dtype=np.int64)    # 4 C1: +15 spins
RETRIGGER_TICKETS_5 = np.array([1, 30, 70, 200], dtype=np.int64)    # 5 C1: +20 spins

# Initial spins
INITIAL_SPINS = {3: 10, 4: 15, 5: 20}
RETRIGGER_SPINS = {3: 10, 4: 15, 5: 20}


# ============================================================
# Data Loading
# ============================================================

def load_game_data(json_path: str = 'data.json') -> dict:
    """Load game parameters"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def prepare_numba_data(data: dict, mode: str = 'base_game', fg_mode: str = None, weight_type: str = 'variable'):
    """
    Convert JSON data to numpy arrays for Numba

    mode: 'base_game' | 'free_game'
    fg_mode: 'special' | 'high' | 'mid' | 'low' (only needed for free_game)
    weight_type: 'uniform' | 'variable' (Base Game drop weight table type)
    """
    config = data['config']

    # Convert paytable to numpy array
    symbols = ['WW', 'C1', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9']
    paytable = np.array([data['paytable'][s] for s in symbols], dtype=np.int64)

    # Select mode data
    if mode == 'base_game':
        mode_data = data['base_game']
        window_size = config['window_size']
    else:
        mode_data = data['free_game'][fg_mode]
        window_size = config['window_size_fg']

    # Convert reel strips to numpy array
    reel_strips = {
        'R1': np.array(mode_data['reel_strips']['R1'], dtype=np.int64),
        'R2': np.array(mode_data['reel_strips']['R2'], dtype=np.int64),
        'R3': np.array(mode_data['reel_strips']['R3'], dtype=np.int64),
        'R4': np.array(mode_data['reel_strips']['R4'], dtype=np.int64),
        'R5': np.array(mode_data['reel_strips']['R5'], dtype=np.int64),
    }

    # Select Combo weight table type (only base_game has two types)
    if mode == 'base_game':
        weight_key = f'combo_weights_{weight_type}'
        if weight_key in mode_data:
            combo_weights = mode_data[weight_key]
        else:
            combo_weights = mode_data.get('combo_weights', mode_data.get('combo_weights_variable', {}))
    else:
        combo_weights = mode_data.get('combo_weights', {})

    combo_probs = {}

    for combo_name, weights in combo_weights.items():
        weights_arr = np.array(weights, dtype=np.float64)
        probs = np.zeros_like(weights_arr)

        for reel in range(5):
            col_sum = weights_arr[:, reel].sum()
            if col_sum > 0:
                cumsum = 0.0
                for sym in range(14):  # 14 個符號 (含 W2, W3, W4)
                    cumsum += weights_arr[sym, reel] / col_sum
                    probs[sym, reel] = cumsum

        combo_probs[combo_name] = probs

    return {
        'paytable': paytable,
        'reel_strips': reel_strips,
        'combo_probs': combo_probs,
        'window_size': window_size,
        'reel_num': config['reel_num'],
        'payline': config['payline'],
    }


def prepare_all_fg_data(data: dict):
    """Prepare data for all 4 FG modes"""
    fg_modes = ['special', 'high', 'mid', 'low']
    all_fg_data = {}

    for mode in fg_modes:
        if mode in data.get('free_game', {}):
            all_fg_data[mode] = prepare_numba_data(data, mode='free_game', fg_mode=mode)

    return all_fg_data


# ============================================================
# Numba JIT Accelerated Core Simulation Functions
# ============================================================

@jit(nopython=True, nogil=True)
def draw_ticket(tickets: np.ndarray) -> int:
    """Draw a ticket from bucket, return mode index (0=special, 1=high, 2=mid, 3=low)"""
    total = tickets[0] + tickets[1] + tickets[2] + tickets[3]
    if total <= 0:
        return 3  # 預設 low

    r = np.random.randint(0, total)
    cumsum = 0
    for i in range(4):
        cumsum += tickets[i]
        if r < cumsum:
            return i
    return 3


@jit(nopython=True, nogil=True)
def simulate_base_game(
    arr_output: np.ndarray,
    thread_id: int,
    num_spins: int,
    R1: np.ndarray, R2: np.ndarray, R3: np.ndarray, R4: np.ndarray, R5: np.ndarray,
    paytable: np.ndarray,
    combo1_prob: np.ndarray,
    combo2_prob: np.ndarray,
    combo5_prob: np.ndarray,
    combo10_prob: np.ndarray,
    combo26_prob: np.ndarray,
    window_size: int,
    reel_num: int,
    payline: int,
    num_threads: int,
    # Free Game 4種模式的輪帶 (special, high, mid, low)
    FG_S_R1: np.ndarray, FG_S_R2: np.ndarray, FG_S_R3: np.ndarray, FG_S_R4: np.ndarray, FG_S_R5: np.ndarray,
    FG_H_R1: np.ndarray, FG_H_R2: np.ndarray, FG_H_R3: np.ndarray, FG_H_R4: np.ndarray, FG_H_R5: np.ndarray,
    FG_M_R1: np.ndarray, FG_M_R2: np.ndarray, FG_M_R3: np.ndarray, FG_M_R4: np.ndarray, FG_M_R5: np.ndarray,
    FG_L_R1: np.ndarray, FG_L_R2: np.ndarray, FG_L_R3: np.ndarray, FG_L_R4: np.ndarray, FG_L_R5: np.ndarray,
    # Free Game 4種模式的 combo 權重
    fg_s_combo1: np.ndarray, fg_s_combo2: np.ndarray, fg_s_combo5: np.ndarray, fg_s_combo10: np.ndarray, fg_s_combo26: np.ndarray,
    fg_h_combo1: np.ndarray, fg_h_combo2: np.ndarray, fg_h_combo5: np.ndarray, fg_h_combo10: np.ndarray, fg_h_combo26: np.ndarray,
    fg_m_combo1: np.ndarray, fg_m_combo2: np.ndarray, fg_m_combo5: np.ndarray, fg_m_combo10: np.ndarray, fg_m_combo26: np.ndarray,
    fg_l_combo1: np.ndarray, fg_l_combo2: np.ndarray, fg_l_combo5: np.ndarray, fg_l_combo10: np.ndarray, fg_l_combo26: np.ndarray,
    fg_window_size: int,
    # 籤桶配置（從第26-34行讀取）
    initial_tickets_3: np.ndarray,
    initial_tickets_4: np.ndarray,
    initial_tickets_5: np.ndarray,
    retrigger_tickets_3: np.ndarray,
    retrigger_tickets_4: np.ndarray,
    retrigger_tickets_5: np.ndarray
):
    """
    Base Game + Free Game simulation core function (Numba JIT accelerated)
    Supports ticket bucket draw mechanism for 4 FG modes
    Ticket bucket config passed as parameters, modify lines 26-34 to change
    """
    # Reel strip lengths
    R1_len = R1.shape[0]
    R2_len = R2.shape[0]
    R3_len = R3.shape[0]
    R4_len = R4.shape[0]
    R5_len = R5.shape[0]

    # Working arrays
    rng = np.zeros(reel_num, np.int64)
    arr_result = np.zeros((window_size, reel_num), np.int64)
    hit_array = np.zeros((window_size, reel_num), np.int64)

    # Statistics arrays
    base_game_win = 0.0
    free_game_trigger_win = 0.0
    free_game_win = 0.0
    free_game_triggers = 0
    scatter_combo = 0
    combo_counts = np.zeros(5, np.int64)
    
    # M1~M9 symbol win statistics (9x2 matrix: [:,0]=initial elimination, [:,1]=combo elimination)
    bg_symbol_wins = np.zeros((9, 2), np.float64)  # Base Game symbol wins
    fg_symbol_wins = np.zeros((9, 2), np.float64)  # Free Game symbol wins
    temp_symbol_wins = np.zeros((9, 2), np.float64)  # Single spin temporary statistics

    # Progress display interval
    checkpoint = num_spins // 10 if num_spins >= 10 else 1

    for spin in range(num_spins):
        if thread_id == num_threads - 1 and spin % checkpoint == 0:
            progress = (spin // checkpoint) * 10
            print(progress, '%')

        # 1. Generate random stop positions
        rng[0] = np.random.randint(0, R1_len)
        rng[1] = np.random.randint(0, R2_len)
        rng[2] = np.random.randint(0, R3_len)
        rng[3] = np.random.randint(0, R4_len)
        rng[4] = np.random.randint(0, R5_len)

        # 2. Generate window contents
        for i in range(window_size):
            arr_result[i, 0] = R1[(rng[0] + i) % R1_len]
            arr_result[i, 1] = R2[(rng[1] + i) % R2_len]
            arr_result[i, 2] = R3[(rng[2] + i) % R3_len]
            arr_result[i, 3] = R4[(rng[3] + i) % R4_len]
            arr_result[i, 4] = R5[(rng[4] + i) % R5_len]

        # 3. Calculate win
        temp_symbol_wins[:, :] = 0.0  # Reset temporary statistics
        win, combo_flag = calculate_win_numba(arr_result, hit_array, paytable, window_size, reel_num, temp_symbol_wins, True)

        # 4. Combo chain
        combo_count = 0
        while combo_flag:
            combo_count += 1

            if combo_count >= 26:
                combo_prob = combo26_prob
            elif combo_count >= 10:
                combo_prob = combo10_prob
            elif combo_count >= 5:
                combo_prob = combo5_prob
            elif combo_count >= 2:
                combo_prob = combo2_prob
            else:
                combo_prob = combo1_prob

            feature_change_numba(arr_result, combo_count, window_size, reel_num)
            combo_change_numba(arr_result, hit_array, combo_prob, window_size, reel_num)
            combo_win, combo_flag = calculate_win_numba(arr_result, hit_array, paytable, window_size, reel_num, temp_symbol_wins, False)
            win += combo_win

        # 5. Count Combo occurrences
        if combo_count >= 1:
            combo_counts[0] += 1
        if combo_count >= 2:
            combo_counts[1] += 1
        if combo_count >= 5:
            combo_counts[2] += 1
        if combo_count >= 10:
            combo_counts[3] += 1
        if combo_count >= 26:
            combo_counts[4] += 1

        # 6. Check Free Game trigger (C1 >= 3)
        c1_count = 0
        has_c1_in_spin = False
        for i in range(window_size):
            for j in range(reel_num):
                if arr_result[i, j] == 1:
                    c1_count += 1
                    has_c1_in_spin = True
        
        # Count scatter_combo (this spin has C1)
        if has_c1_in_spin:
            scatter_combo += 1

        if c1_count >= 3:
            free_game_triggers += 1
            free_game_trigger_win += win
            
            # Add FG-triggering spin's BG symbol wins to BG statistics
            for i in range(9):
                bg_symbol_wins[i, 0] += temp_symbol_wins[i, 0]  # Initial elimination
                bg_symbol_wins[i, 1] += temp_symbol_wins[i, 1]  # Combo elimination

            # Determine initial spins and ticket bucket (using config)
            if c1_count >= 5:
                fg_spins = 20
                tickets = initial_tickets_5.copy()
            elif c1_count >= 4:
                fg_spins = 15
                tickets = initial_tickets_4.copy()
            else:
                fg_spins = 10
                tickets = initial_tickets_3.copy()

            # Execute Free Game (ticket bucket mechanism)
            fg_output = np.zeros(20, dtype=np.float64)  # Extended: [0]=win, [1]=scatter, [2-10]=M1~M9 initial, [11-19]=M1~M9 combo
            simulate_free_game_with_tickets(
                fg_spins, tickets,
                FG_S_R1, FG_S_R2, FG_S_R3, FG_S_R4, FG_S_R5,
                FG_H_R1, FG_H_R2, FG_H_R3, FG_H_R4, FG_H_R5,
                FG_M_R1, FG_M_R2, FG_M_R3, FG_M_R4, FG_M_R5,
                FG_L_R1, FG_L_R2, FG_L_R3, FG_L_R4, FG_L_R5,
                paytable,
                fg_s_combo1, fg_s_combo2, fg_s_combo5, fg_s_combo10, fg_s_combo26,
                fg_h_combo1, fg_h_combo2, fg_h_combo5, fg_h_combo10, fg_h_combo26,
                fg_m_combo1, fg_m_combo2, fg_m_combo5, fg_m_combo10, fg_m_combo26,
                fg_l_combo1, fg_l_combo2, fg_l_combo5, fg_l_combo10, fg_l_combo26,
                fg_window_size, reel_num, fg_output,
                retrigger_tickets_3, retrigger_tickets_4, retrigger_tickets_5
            )
            free_game_win += fg_output[0]
            scatter_combo += fg_output[1]
            # Accumulate FG symbol wins
            for i in range(9):
                fg_symbol_wins[i, 0] += fg_output[2 + i]      # Initial elimination
                fg_symbol_wins[i, 1] += fg_output[11 + i]     # Combo elimination
        else:
            base_game_win += win
            # Accumulate BG symbol wins
            for i in range(9):
                bg_symbol_wins[i, 0] += temp_symbol_wins[i, 0]  # Initial elimination
                bg_symbol_wins[i, 1] += temp_symbol_wins[i, 1]  # Combo elimination

    # Save results
    arr_output[0, 0] = base_game_win
    arr_output[0, 1] = free_game_trigger_win
    arr_output[0, 2] = free_game_win
    arr_output[0, 3] = base_game_win + free_game_trigger_win  # Full Base Game Win
    arr_output[1, 0] = free_game_triggers
    arr_output[1, 1] = scatter_combo
    for i in range(5):
        arr_output[2, i] = combo_counts[i]
    # M1~M9 symbol wins - initial elimination
    for i in range(9):
        arr_output[3, i] = bg_symbol_wins[i, 0]  # BG initial elimination
        arr_output[4, i] = fg_symbol_wins[i, 0]  # FG initial elimination
    # M1~M9 symbol wins - combo elimination
    for i in range(9):
        arr_output[5, i] = bg_symbol_wins[i, 1]  # BG combo elimination
        arr_output[6, i] = fg_symbol_wins[i, 1]  # FG combo elimination


@jit(nopython=True, nogil=True)
def calculate_win_numba(
    arr_result: np.ndarray,
    hit_array: np.ndarray,
    paytable: np.ndarray,
    window_size: int,
    reel_num: int,
    symbol_wins: np.ndarray = None,
    is_initial: bool = True
) -> tuple:
    """Calculate win (Numba version), optionally record each symbol's win
    
    symbol_wins: if provided, should be 9x2 array, [:,0]=initial elimination, [:,1]=combo elimination
    is_initial: True=initial board elimination, False=combo elimination
    """
    pay = 0
    combo_flag = False

    # Clear hit_array
    for i in range(window_size):
        for j in range(reel_num):
            hit_array[i, j] = 0

    # Find unique symbols in first column
    col_first = np.zeros(window_size, np.int64)
    col_first_count = 0

    for i in range(window_size):
        sym = arr_result[i, 0]
        found = False
        for j in range(col_first_count):
            if col_first[j] == sym:
                found = True
                break
        if not found:
            col_first[col_first_count] = sym
            col_first_count += 1

    # Calculate lines for each starting symbol
    for idx in range(col_first_count):
        symbol = col_first[idx]

        # Skip C1 (Scatter)
        if symbol == 1:
            continue

        mul_ = 1
        line = 0

        for reel in range(reel_num):
            has_symbol = False
            has_wild = False
            count = 0

            for row in range(window_size):
                if arr_result[row, reel] == symbol:
                    has_symbol = True
                    count += 1
                elif arr_result[row, reel] == 0:  # Wild
                    has_wild = True
                    count += 1

            if has_symbol or has_wild:
                line += 1
                mul_ *= count
            else:
                break

        # Score only for 3+ lines
        if line >= 3:
            combo_flag = True
            symbol_pay = paytable[symbol, line - 1] * mul_
            pay += symbol_pay
            
            # Record symbol wins (M1~M9 corresponds to symbol 2~10)
            if symbol_wins is not None and 2 <= symbol <= 10:
                symbol_idx = symbol - 2
                if is_initial:
                    symbol_wins[symbol_idx, 0] += symbol_pay  # Initial elimination
                else:
                    symbol_wins[symbol_idx, 1] += symbol_pay  # Combo elimination

            # Mark winning positions
            for reel in range(line):
                for row in range(window_size):
                    if arr_result[row, reel] == symbol or arr_result[row, reel] == 0:
                        if arr_result[row, reel] != 1:
                            hit_array[row, reel] = 1

    return pay, combo_flag


@jit(nopython=True, nogil=True)
def feature_change_numba(arr_result: np.ndarray, combo_count: int, window_size: int, reel_num: int):
    """Feature change: specific symbols become Wild"""
    if combo_count < 2:
        return

    for reel in range(1, reel_num):
        for row in range(window_size):
            sym = arr_result[row, reel]

            if combo_count >= 10 and sym in (2, 3, 4):
                arr_result[row, reel] = 0
            elif combo_count >= 5 and sym in (3, 4):
                arr_result[row, reel] = 0
            elif combo_count >= 2 and sym == 4:
                arr_result[row, reel] = 0


@jit(nopython=True, nogil=True)
def combo_change_numba(
    arr_result: np.ndarray,
    hit_array: np.ndarray,
    combo_prob: np.ndarray,
    window_size: int,
    reel_num: int
):
    """Combo replacement: replace winning symbols"""
    for reel in range(reel_num):
        c1_count = 0
        for row in range(window_size):
            if arr_result[row, reel] == 1:
                c1_count += 1

        for row in range(window_size):
            if hit_array[row, reel] == 1:
                p = np.random.rand()
                new_symbol = 10

                for sym in range(14):  # 14 個符號
                    if p <= combo_prob[sym, reel]:
                        new_symbol = sym
                        break

                while c1_count >= 1 and new_symbol == 1:
                    p = np.random.rand()
                    for sym in range(14):
                        if p <= combo_prob[sym, reel]:
                            new_symbol = sym
                            break

                # ID 11, 12, 13 轉換為 Wild (0)
                if new_symbol >= 11:
                    new_symbol = 0

                arr_result[row, reel] = new_symbol

                if new_symbol == 1:
                    c1_count += 1


@jit(nopython=True, nogil=True)
def simulate_free_game_with_tickets(
    initial_spins: int,
    tickets: np.ndarray,
    # Special 輪帶
    FG_S_R1: np.ndarray, FG_S_R2: np.ndarray, FG_S_R3: np.ndarray, FG_S_R4: np.ndarray, FG_S_R5: np.ndarray,
    # High 輪帶
    FG_H_R1: np.ndarray, FG_H_R2: np.ndarray, FG_H_R3: np.ndarray, FG_H_R4: np.ndarray, FG_H_R5: np.ndarray,
    # Mid 輪帶
    FG_M_R1: np.ndarray, FG_M_R2: np.ndarray, FG_M_R3: np.ndarray, FG_M_R4: np.ndarray, FG_M_R5: np.ndarray,
    # Low 輪帶
    FG_L_R1: np.ndarray, FG_L_R2: np.ndarray, FG_L_R3: np.ndarray, FG_L_R4: np.ndarray, FG_L_R5: np.ndarray,
    paytable: np.ndarray,
    # Special combo
    fg_s_combo1: np.ndarray, fg_s_combo2: np.ndarray, fg_s_combo5: np.ndarray, fg_s_combo10: np.ndarray, fg_s_combo26: np.ndarray,
    # High combo
    fg_h_combo1: np.ndarray, fg_h_combo2: np.ndarray, fg_h_combo5: np.ndarray, fg_h_combo10: np.ndarray, fg_h_combo26: np.ndarray,
    # Mid combo
    fg_m_combo1: np.ndarray, fg_m_combo2: np.ndarray, fg_m_combo5: np.ndarray, fg_m_combo10: np.ndarray, fg_m_combo26: np.ndarray,
    # Low combo
    fg_l_combo1: np.ndarray, fg_l_combo2: np.ndarray, fg_l_combo5: np.ndarray, fg_l_combo10: np.ndarray, fg_l_combo26: np.ndarray,
    fg_window_size: int,
    reel_num: int,
    fg_output: np.ndarray,
    # Retrigger 籤桶配置（從第32-34行讀取）
    retrigger_tickets_3: np.ndarray,
    retrigger_tickets_4: np.ndarray,
    retrigger_tickets_5: np.ndarray
):
    """
    Free Game ticket bucket mechanism simulation
    Each spin draws a ticket from bucket to determine which table to use, no replacement after draw
    Retrigger ticket bucket config passed as parameters, modify lines 32-34 to change
    """
    # Reel strip lengths
    S_lens = np.array([FG_S_R1.shape[0], FG_S_R2.shape[0], FG_S_R3.shape[0], FG_S_R4.shape[0], FG_S_R5.shape[0]], dtype=np.int64)
    H_lens = np.array([FG_H_R1.shape[0], FG_H_R2.shape[0], FG_H_R3.shape[0], FG_H_R4.shape[0], FG_H_R5.shape[0]], dtype=np.int64)
    M_lens = np.array([FG_M_R1.shape[0], FG_M_R2.shape[0], FG_M_R3.shape[0], FG_M_R4.shape[0], FG_M_R5.shape[0]], dtype=np.int64)
    L_lens = np.array([FG_L_R1.shape[0], FG_L_R2.shape[0], FG_L_R3.shape[0], FG_L_R4.shape[0], FG_L_R5.shape[0]], dtype=np.int64)

    rng = np.zeros(reel_num, np.int64)
    arr_result = np.zeros((fg_window_size, reel_num), np.int64)
    hit_array = np.zeros((fg_window_size, reel_num), np.int64)

    total_fg_win = 0.0
    scatter_combo_count = 0
    remaining_spins = initial_spins
    
    # M1~M9 symbol win statistics (9x2 matrix)
    symbol_wins = np.zeros((9, 2), np.float64)
    temp_symbol_wins = np.zeros((9, 2), np.float64)

    while remaining_spins > 0:
        remaining_spins -= 1

        # Draw a ticket from bucket to determine which table to use
        mode = draw_ticket(tickets)
        if tickets[mode] > 0:
            tickets[mode] -= 1

        # Select reel strips and lengths based on drawn mode
        if mode == 0:  # special
            lens = S_lens
        elif mode == 1:  # high
            lens = H_lens
        elif mode == 2:  # mid
            lens = M_lens
        else:  # low
            lens = L_lens

        # Generate random stop positions
        for r in range(reel_num):
            rng[r] = np.random.randint(0, lens[r])

        # Generate window contents (select reel strips based on mode)
        for i in range(fg_window_size):
            if mode == 0:  # special
                arr_result[i, 0] = FG_S_R1[(rng[0] + i) % S_lens[0]]
                arr_result[i, 1] = FG_S_R2[(rng[1] + i) % S_lens[1]]
                arr_result[i, 2] = FG_S_R3[(rng[2] + i) % S_lens[2]]
                arr_result[i, 3] = FG_S_R4[(rng[3] + i) % S_lens[3]]
                arr_result[i, 4] = FG_S_R5[(rng[4] + i) % S_lens[4]]
            elif mode == 1:  # high
                arr_result[i, 0] = FG_H_R1[(rng[0] + i) % H_lens[0]]
                arr_result[i, 1] = FG_H_R2[(rng[1] + i) % H_lens[1]]
                arr_result[i, 2] = FG_H_R3[(rng[2] + i) % H_lens[2]]
                arr_result[i, 3] = FG_H_R4[(rng[3] + i) % H_lens[3]]
                arr_result[i, 4] = FG_H_R5[(rng[4] + i) % H_lens[4]]
            elif mode == 2:  # mid
                arr_result[i, 0] = FG_M_R1[(rng[0] + i) % M_lens[0]]
                arr_result[i, 1] = FG_M_R2[(rng[1] + i) % M_lens[1]]
                arr_result[i, 2] = FG_M_R3[(rng[2] + i) % M_lens[2]]
                arr_result[i, 3] = FG_M_R4[(rng[3] + i) % M_lens[3]]
                arr_result[i, 4] = FG_M_R5[(rng[4] + i) % M_lens[4]]
            else:  # low
                arr_result[i, 0] = FG_L_R1[(rng[0] + i) % L_lens[0]]
                arr_result[i, 1] = FG_L_R2[(rng[1] + i) % L_lens[1]]
                arr_result[i, 2] = FG_L_R3[(rng[2] + i) % L_lens[2]]
                arr_result[i, 3] = FG_L_R4[(rng[3] + i) % L_lens[3]]
                arr_result[i, 4] = FG_L_R5[(rng[4] + i) % L_lens[4]]

        # Calculate win
        temp_symbol_wins[:, :] = 0.0
        win, combo_flag = calculate_win_numba(arr_result, hit_array, paytable, fg_window_size, reel_num, temp_symbol_wins, True)

        # Combo chain (use corresponding mode's combo weights)
        combo_count = 0
        while combo_flag:
            combo_count += 1

            # 選擇對應模式的 combo 權重
            if mode == 0:  # special
                if combo_count >= 26:
                    combo_prob = fg_s_combo26
                elif combo_count >= 10:
                    combo_prob = fg_s_combo10
                elif combo_count >= 5:
                    combo_prob = fg_s_combo5
                elif combo_count >= 2:
                    combo_prob = fg_s_combo2
                else:
                    combo_prob = fg_s_combo1
            elif mode == 1:  # high
                if combo_count >= 26:
                    combo_prob = fg_h_combo26
                elif combo_count >= 10:
                    combo_prob = fg_h_combo10
                elif combo_count >= 5:
                    combo_prob = fg_h_combo5
                elif combo_count >= 2:
                    combo_prob = fg_h_combo2
                else:
                    combo_prob = fg_h_combo1
            elif mode == 2:  # mid
                if combo_count >= 26:
                    combo_prob = fg_m_combo26
                elif combo_count >= 10:
                    combo_prob = fg_m_combo10
                elif combo_count >= 5:
                    combo_prob = fg_m_combo5
                elif combo_count >= 2:
                    combo_prob = fg_m_combo2
                else:
                    combo_prob = fg_m_combo1
            else:  # low
                if combo_count >= 26:
                    combo_prob = fg_l_combo26
                elif combo_count >= 10:
                    combo_prob = fg_l_combo10
                elif combo_count >= 5:
                    combo_prob = fg_l_combo5
                elif combo_count >= 2:
                    combo_prob = fg_l_combo2
                else:
                    combo_prob = fg_l_combo1

            feature_change_numba(arr_result, combo_count, fg_window_size, reel_num)
            combo_change_numba(arr_result, hit_array, combo_prob, fg_window_size, reel_num)
            combo_win, combo_flag = calculate_win_numba(arr_result, hit_array, paytable, fg_window_size, reel_num, temp_symbol_wins, False)
            win += combo_win

        # Check Retrigger (C1 >= 3)
        c1_count = 0
        for i in range(fg_window_size):
            for j in range(reel_num):
                if arr_result[i, j] == 1:
                    c1_count += 1

        if c1_count >= 5:
            remaining_spins += 20
            tickets[0] += retrigger_tickets_5[0]  # special
            tickets[1] += retrigger_tickets_5[1]  # high
            tickets[2] += retrigger_tickets_5[2]  # mid
            tickets[3] += retrigger_tickets_5[3]  # low
        elif c1_count >= 4:
            remaining_spins += 15
            tickets[0] += retrigger_tickets_4[0]  # special
            tickets[1] += retrigger_tickets_4[1]  # high
            tickets[2] += retrigger_tickets_4[2]  # mid
            tickets[3] += retrigger_tickets_4[3]  # low
        elif c1_count >= 3:
            remaining_spins += 10
            tickets[0] += retrigger_tickets_3[0]  # special
            tickets[1] += retrigger_tickets_3[1]  # high
            tickets[2] += retrigger_tickets_3[2]  # mid
            tickets[3] += retrigger_tickets_3[3]  # low

        total_fg_win += win
        # Accumulate symbol wins
        for i in range(9):
            symbol_wins[i, 0] += temp_symbol_wins[i, 0]  # Initial elimination
            symbol_wins[i, 1] += temp_symbol_wins[i, 1]  # Combo elimination
        
        # Check if this spin has C1
        has_c1 = False
        for i in range(fg_window_size):
            for j in range(reel_num):
                if arr_result[i, j] == 1:
                    has_c1 = True
                    break
            if has_c1:
                break
        if has_c1:
            scatter_combo_count += 1

    # Save results to output array
    fg_output[0] = total_fg_win
    fg_output[1] = scatter_combo_count
    # M1~M9 symbol wins - initial elimination
    for i in range(9):
        fg_output[2 + i] = symbol_wins[i, 0]
    # M1~M9 symbol wins - combo elimination
    for i in range(9):
        fg_output[11 + i] = symbol_wins[i, 1]


# ============================================================
# Multi-threading Wrapper
# ============================================================

def make_multithread_runner(simulate_func, total_rounds: int, game_data: dict, all_fg_data: dict):
    """Create multi-threaded simulator"""
    num_threads = multiprocessing.cpu_count()

    # 準備 Base Game 資料
    R1 = game_data['reel_strips']['R1']
    R2 = game_data['reel_strips']['R2']
    R3 = game_data['reel_strips']['R3']
    R4 = game_data['reel_strips']['R4']
    R5 = game_data['reel_strips']['R5']

    paytable = game_data['paytable']

    combo1_prob = game_data['combo_probs']['combo_1']
    combo2_prob = game_data['combo_probs']['combo_2_4']
    combo5_prob = game_data['combo_probs']['combo_5_9']
    combo10_prob = game_data['combo_probs']['combo_10_25']
    combo26_prob = game_data['combo_probs']['combo_26_plus']

    window_size = game_data['window_size']
    reel_num = game_data['reel_num']
    payline = game_data['payline']

    # 準備 4 種 FG 模式的資料
    fg_modes = ['special', 'high', 'mid', 'low']
    fg_data = {}

    for mode in fg_modes:
        if mode in all_fg_data:
            fg_data[mode] = all_fg_data[mode]
        else:
            # 如果缺少某個模式，用 low 代替
            fg_data[mode] = all_fg_data.get('low', game_data)

    # 提取各模式資料
    FG_S = fg_data['special']
    FG_H = fg_data['high']
    FG_M = fg_data['mid']
    FG_L = fg_data['low']

    fg_window_size = FG_S['window_size']

    # Read ticket bucket config (from lines 26-34)
    init_tickets_3 = INITIAL_TICKETS_3
    init_tickets_4 = INITIAL_TICKETS_4
    init_tickets_5 = INITIAL_TICKETS_5
    retrig_tickets_3 = RETRIGGER_TICKETS_3
    retrig_tickets_4 = RETRIGGER_TICKETS_4
    retrig_tickets_5 = RETRIGGER_TICKETS_5

    def run():
        print(f'Multi-Thread Mode: On ({num_threads} Threads)')

        results = [np.zeros((10, 10), np.float64) for _ in range(num_threads)]

        spins_per_thread = total_rounds // num_threads
        remainder = total_rounds - spins_per_thread * (num_threads - 1)

        threads = []
        for t in range(num_threads):
            spins = remainder if t == num_threads - 1 else spins_per_thread

            thread = threading.Thread(
                target=simulate_func,
                args=(
                    results[t], t, spins,
                    R1, R2, R3, R4, R5,
                    paytable,
                    combo1_prob, combo2_prob, combo5_prob, combo10_prob, combo26_prob,
                    window_size, reel_num, payline, num_threads,
                    # Special
                    FG_S['reel_strips']['R1'], FG_S['reel_strips']['R2'], FG_S['reel_strips']['R3'], FG_S['reel_strips']['R4'], FG_S['reel_strips']['R5'],
                    # High
                    FG_H['reel_strips']['R1'], FG_H['reel_strips']['R2'], FG_H['reel_strips']['R3'], FG_H['reel_strips']['R4'], FG_H['reel_strips']['R5'],
                    # Mid
                    FG_M['reel_strips']['R1'], FG_M['reel_strips']['R2'], FG_M['reel_strips']['R3'], FG_M['reel_strips']['R4'], FG_M['reel_strips']['R5'],
                    # Low
                    FG_L['reel_strips']['R1'], FG_L['reel_strips']['R2'], FG_L['reel_strips']['R3'], FG_L['reel_strips']['R4'], FG_L['reel_strips']['R5'],
                    # Special combo
                    FG_S['combo_probs']['combo_1'], FG_S['combo_probs']['combo_2_4'], FG_S['combo_probs']['combo_5_9'], FG_S['combo_probs']['combo_10_25'], FG_S['combo_probs']['combo_26_plus'],
                    # High combo
                    FG_H['combo_probs']['combo_1'], FG_H['combo_probs']['combo_2_4'], FG_H['combo_probs']['combo_5_9'], FG_H['combo_probs']['combo_10_25'], FG_H['combo_probs']['combo_26_plus'],
                    # Mid combo
                    FG_M['combo_probs']['combo_1'], FG_M['combo_probs']['combo_2_4'], FG_M['combo_probs']['combo_5_9'], FG_M['combo_probs']['combo_10_25'], FG_M['combo_probs']['combo_26_plus'],
                    # Low combo
                    FG_L['combo_probs']['combo_1'], FG_L['combo_probs']['combo_2_4'], FG_L['combo_probs']['combo_5_9'], FG_L['combo_probs']['combo_10_25'], FG_L['combo_probs']['combo_26_plus'],
                    fg_window_size,
                    # 籤桶配置
                    init_tickets_3, init_tickets_4, init_tickets_5,
                    retrig_tickets_3, retrig_tickets_4, retrig_tickets_5
                )
            )
            threads.append(thread)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Merge results
        base_game_win = sum(r[0, 0] for r in results)
        free_game_trigger_win = sum(r[0, 1] for r in results)
        free_game_win = sum(r[0, 2] for r in results)
        full_base_game_win = sum(r[0, 3] for r in results)
        free_game_triggers = sum(r[1, 0] for r in results)
        scatter_combo = sum(r[1, 1] for r in results)
        combo_counts = np.array([sum(r[2, i] for r in results) for i in range(5)])
        
        # M1~M9 symbol wins - initial elimination
        bg_symbol_wins_initial = np.array([sum(r[3, i] for r in results) for i in range(9)])
        fg_symbol_wins_initial = np.array([sum(r[4, i] for r in results) for i in range(9)])
        # M1~M9 symbol wins - combo elimination
        bg_symbol_wins_combo = np.array([sum(r[5, i] for r in results) for i in range(9)])
        fg_symbol_wins_combo = np.array([sum(r[6, i] for r in results) for i in range(9)])

        return {
            'base_game_win': base_game_win,
            'free_game_trigger_win': free_game_trigger_win,
            'free_game_win': free_game_win,
            'full_base_game_win': full_base_game_win,
            'total_win': base_game_win + free_game_trigger_win + free_game_win,
            'free_game_triggers': int(free_game_triggers),
            'scatter_combo': int(scatter_combo),
            'combo_counts': combo_counts,
            'bg_symbol_wins_initial': bg_symbol_wins_initial,
            'bg_symbol_wins_combo': bg_symbol_wins_combo,
            'fg_symbol_wins_initial': fg_symbol_wins_initial,
            'fg_symbol_wins_combo': fg_symbol_wins_combo,
        }

    return run


# ============================================================
# Main Program
# ============================================================

def run_base_game_simulation(total_rounds: int = 100_000_000, data_path: str = 'data.json', weight_type: str = 'variable'):
    """
    Execute Base Game + Free Game simulation (ticket bucket mechanism)

    weight_type: 'uniform' | 'variable'
        - uniform: unified weights for all reels (AE:AI)
        - variable: independent weights for each reel (AM:AQ)
    """
    print("=" * 60)
    print("Slam Dunk Base Game + Free Game Simulation (Ticket Bucket Mechanism)")
    print("=" * 60)

    # Load data
    print("\n[1] Loading game data...")
    data = load_game_data(data_path)
    game_data = prepare_numba_data(data, mode='base_game', weight_type=weight_type)

    # Load all Free Game modes
    all_fg_data = prepare_all_fg_data(data)

    print(f"  - BG reel strip length: R1={len(game_data['reel_strips']['R1'])}, R5={len(game_data['reel_strips']['R5'])}")
    print(f"  - BG window size: {game_data['window_size']}x{game_data['reel_num']}")
    print(f"  - Bet amount: {game_data['payline']}")
    print(f"  - Weight type: {weight_type}")
    print(f"  - FG modes: {list(all_fg_data.keys())}")

    if all_fg_data:
        fg_sample = list(all_fg_data.values())[0]
        print(f"  - FG window size: {fg_sample['window_size']}x{fg_sample['reel_num']}")

    print("\nTicket bucket settings:")
    print("  Initial trigger: 3C1=[2,30,50,400], 4C1=[2,40,70,400], 5C1=[2,50,90,400]")
    print("  Retrigger: 3C1=[1,20,30,200], 4C1=[1,20,50,200], 5C1=[1,30,70,200]")

    # Create simulator
    print(f"\n[2] Starting simulation ({total_rounds:,} rounds)...")
    start_time = time.time()

    runner = make_multithread_runner(simulate_base_game, total_rounds, game_data, all_fg_data)
    result = runner()

    elapsed = time.time() - start_time
    hours, remainder = divmod(elapsed, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Output results
    print("\n" + "=" * 60)
    print("Simulation Results")
    print("=" * 60)

    payline = game_data['payline']
    total_rtp = result['total_win'] / total_rounds / payline
    bg_rtp = result['base_game_win'] / total_rounds / payline
    fg_trigger_rtp = result['free_game_trigger_win'] / total_rounds / payline
    full_bg_rtp = result['full_base_game_win'] / total_rounds / payline
    fg_rtp = result['free_game_win'] / total_rounds / payline
    fg_rate = result['free_game_triggers'] / total_rounds

    print(f"Execution time: {int(hours)}h {int(minutes)}m {int(seconds)}s")
    print(f"Total spins: {total_rounds:,}")
    print(f"")
    print(f"RTP Statistics:")
    print(f"  - Base Game RTP (without FG trigger): {bg_rtp:.4%}")
    print(f"  - Base Game RTP (with FG trigger): {fg_trigger_rtp:.4%}")
    print(f"  - Full Base Game RTP (BG total): {full_bg_rtp:.4%}")
    print(f"  - Free Game RTP: {fg_rtp:.4%}")
    print(f"  - Total RTP: {total_rtp:.4%}")
    print(f"")
    print(f"Free Game trigger rate: {fg_rate:.4%} (1/{1/fg_rate:.1f})")
    print(f"")
    print(f"Scatter Statistics:")
    print(f"  - Scatter occurrences (count 1 per spin): {result['scatter_combo']:,}")
    print(f"  - Average Scatter per 100 spins: {result['scatter_combo'] / total_rounds * 100:.2f}")
    print(f"")
    print(f"Combo Statistics:")
    print(f"  - Combo 1+  trigger rate: {result['combo_counts'][0]/total_rounds:.2%}")
    print(f"  - Combo 2+  trigger rate: {result['combo_counts'][1]/total_rounds:.2%}")
    print(f"  - Combo 5+  trigger rate: {result['combo_counts'][2]/total_rounds:.2%}")
    print(f"  - Combo 10+ trigger rate: {result['combo_counts'][3]/total_rounds:.2%}")
    print(f"  - Combo 26+ trigger rate: {result['combo_counts'][4]/total_rounds:.2%}")
    print(f"")
    print(f"Symbol Win Statistics (M1~M9):")
    print(f"  Base Game - Initial Board Elimination:")
    for i in range(9):
        symbol_name = f"M{i+1}"
        symbol_win = result['bg_symbol_wins_initial'][i]
        symbol_rtp = symbol_win / total_rounds / payline
        print(f"    {symbol_name}: {symbol_win:,.0f} ({symbol_rtp:.4%})")
    print(f"  Base Game - Combo Elimination:")
    for i in range(9):
        symbol_name = f"M{i+1}"
        symbol_win = result['bg_symbol_wins_combo'][i]
        symbol_rtp = symbol_win / total_rounds / payline
        print(f"    {symbol_name}: {symbol_win:,.0f} ({symbol_rtp:.4%})")
    print(f"  Free Game - Initial Board Elimination:")
    for i in range(9):
        symbol_name = f"M{i+1}"
        symbol_win = result['fg_symbol_wins_initial'][i]
        symbol_rtp = symbol_win / total_rounds / payline
        print(f"    {symbol_name}: {symbol_win:,.0f} ({symbol_rtp:.4%})")
    print(f"  Free Game - Combo Elimination:")
    for i in range(9):
        symbol_name = f"M{i+1}"
        symbol_win = result['fg_symbol_wins_combo'][i]
        symbol_rtp = symbol_win / total_rounds / payline
        print(f"    {symbol_name}: {symbol_win:,.0f} ({symbol_rtp:.4%})")

    return result


#%%
if __name__ == '__main__':
    import sys

    rounds = 100_000_000
    weight_type = 'uniform'

    for arg in sys.argv[1:]:
        if arg.startswith('--rounds='):
            rounds = int(arg.split('=')[1].replace('_', ''))
        elif arg.startswith('--weight='):
            weight_type = arg.split('=')[1]
        elif arg in ('uniform', 'variable'):
            weight_type = arg

    run_base_game_simulation(total_rounds=rounds, weight_type=weight_type)

# %%
