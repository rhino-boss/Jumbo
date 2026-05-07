# %% Import


import os
import sys

import numpy as np
import pandas as pd
from numba import njit

os.chdir("C:\\Users\\rhinshen\\Mine\\個人工作區\\2_Program")
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

import Project.Slots.Source.H026_Box as Box
import Project.Slots.Source.General.Math as Mat
from Project.Slots.Source.General.Math import cplot, simulation
from Project.Slots.Source.General.RedBox import div, log_use

# %% Setting


bet_multi = 1
bet_mode = Box.mode_normalbet
# bet_mode = Box.mode_featurebuy

# total_round = 10**6
total_round = 10**7

debug_spin_trace = False
debug_trace_limit = 20
debug_show_cascade = True
fg_spin_cap = 50


# %% Initial


if bet_mode == Box.mode_normalbet:
    coin_in = bet_multi * Box.default_coin_in * Box.normalbet
elif bet_mode == Box.mode_featurebuy:
    coin_in = bet_multi * Box.default_coin_in * Box.normalbet * Box.featurebuy
else:
    raise ValueError(f"Unsupported bet_mode: {bet_mode}")

threshold_record = Mat.threshold_record.astype(np.float64)


# %% Numba helpers


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
def clear_2d(arr):
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            arr[i, j] = 0


@njit(nogil=True)
def choose_table(scene_mode, fg_multiplier_sum):
    if scene_mode == 0:
        return pick_by_cum(Box.weight_cum_table_BG)
    if scene_mode == 1:
        if fg_multiplier_sum < 10:
            return 3
        if fg_multiplier_sum < 20:
            return 4
        return 5
    return 6 + pick_by_cum(Box.weight_cum_table_BF)


@njit(nogil=True)
def pick_multiplier(cum_matrix, strip_idx):
    return Box.value_multiplier_range[pick_by_cum(cum_matrix[:, strip_idx])]


@njit(nogil=True)
def pick_initial_multiplier_by_col(table_id, col):
    if col == 2:
        return pick_multiplier(Box.weight_cum_multiple_r3_before, table_id)
    return pick_multiplier(Box.weight_cum_multiple_before, table_id)


@njit(nogil=True)
def pick_drop_multiplier_by_col(table_id, col):
    if col == 2:
        return pick_multiplier(Box.weight_cum_multiple_r3_after, table_id)
    return pick_multiplier(Box.weight_cum_multiple_after, table_id)


@njit(nogil=True)
def choose_eliminate_table(scene_mode):
    if scene_mode == Box.scence_BG:
        choice = pick_by_cum(Box.eliminate_table_weight_cum_BG)
        return 1 if choice == 0 else 0
    if scene_mode == Box.scence_FG:
        choice = pick_by_cum(Box.eliminate_table_weight_cum_FG)
        return 1 if choice == 0 else 0
    return np.random.randint(0, 2)


@njit(nogil=True)
def generate_board(table_id, board, gold_mask, multi_mask):
    for col in range(Box.reel_num):
        reel_length = Box.reels_len[table_id, col]
        stop_idx = pick_by_cum(Box.arr_reels_weight_cum[table_id, :reel_length, col])
        for row in range(Box.window_size):
            symbol = Box.arr_reels[table_id, (stop_idx + row) % reel_length, col]
            board[row, col] = Box.base_symbol_of[symbol]
            gold_mask[row, col] = Box.is_gold_symbol[symbol]
            multi_mask[row, col] = 0


@njit(nogil=True)
def count_scatter(board):
    total = 0
    for row in range(Box.window_size):
        for col in range(Box.reel_num):
            if board[row, col] == Box.C1:
                total += 1
    return total


@njit(nogil=True)
def collect_gold_positions(gold_mask, gold_pos):
    gold_count = 0
    for row in range(Box.window_size):
        for col in range(Box.reel_num):
            if gold_mask[row, col] == 1:
                gold_pos[gold_count, 0] = row
                gold_pos[gold_count, 1] = col
                gold_count += 1
    return gold_count


@njit(nogil=True)
def count_gold_mask(gold_mask):
    gold_count = 0
    for row in range(Box.window_size):
        for col in range(Box.reel_num):
            gold_count += gold_mask[row, col]
    return gold_count


@njit(nogil=True)
def assign_initial_multiplier(table_id, gold_mask, multi_mask, gold_pos):
    gold_count = collect_gold_positions(gold_mask, gold_pos)
    if gold_count == 0:
        return

    special_idx = -1
    if table_id < 3:
        special_weight = Box.weight_special_pool[min(gold_count, 9), table_id]
        if special_weight > 0 and np.random.randint(0, Box.special_pool_weight_base) < special_weight:
            special_idx = np.random.randint(0, gold_count)

    for idx in range(gold_count):
        row = gold_pos[idx, 0]
        col = gold_pos[idx, 1]
        if idx == special_idx:
            multi_mask[row, col] = pick_multiplier(Box.weight_cum_multiple_special, table_id)
        else:
            multi_mask[row, col] = pick_initial_multiplier_by_col(table_id, col)


@njit(nogil=True)
def get_pay(symbol, line_len):
    if symbol < 0 or Box.is_score_symbol[symbol] == 0 or line_len < 3:
        return 0
    return Box.pay_table[symbol, line_len - 3] * bet_multi


@njit(nogil=True)
def evaluate_board(board, hit_mask, spin_hits, spin_pay):
    clear_2d(hit_mask)

    total_pay = 0
    total_hits = 0

    for line_idx in range(Box.paylines.shape[0]):
        best_symbol = -1
        best_len = 0
        best_pay = 0

        first_row = Box.paylines[line_idx, 0]
        first_symbol = board[first_row, 0]
        if first_symbol == Box.C1:
            continue

        if first_symbol == Box.WW:
            for sym_idx in range(Box.symbols_score.shape[0]):
                symbol = Box.symbols_score[sym_idx]
                line_len = 0
                for reel in range(Box.reel_num):
                    row = Box.paylines[line_idx, reel]
                    symbol_on_line = board[row, reel]
                    if symbol_on_line == symbol or symbol_on_line == Box.WW:
                        line_len += 1
                    else:
                        break
                pay = get_pay(symbol, line_len)
                if pay > best_pay:
                    best_symbol = symbol
                    best_len = line_len
                    best_pay = pay
        else:
            line_len = 0
            for reel in range(Box.reel_num):
                row = Box.paylines[line_idx, reel]
                symbol_on_line = board[row, reel]
                if symbol_on_line == first_symbol or symbol_on_line == Box.WW:
                    line_len += 1
                else:
                    break
            best_symbol = first_symbol
            best_len = line_len
            best_pay = get_pay(best_symbol, best_len)

        if best_pay <= 0:
            continue

        total_pay += best_pay
        total_hits += 1
        spin_hits[best_len - 3, best_symbol] += 1
        spin_pay[best_len - 3, best_symbol] += best_pay

        for reel in range(best_len):
            row = Box.paylines[line_idx, reel]
            hit_mask[row, reel] = 1

    return total_pay, total_hits


@njit(nogil=True)
def assign_drop_multiplier(table_id, row, col, multi_mask):
    multi_mask[row, col] = pick_drop_multiplier_by_col(table_id, col)


@njit(nogil=True)
def cascade_drop(table_id, use_drop_a, board, gold_mask, multi_mask, hit_mask, keep_symbol, keep_gold, keep_multi):
    for col in range(Box.reel_num):
        keep_count = 0
        for row in range(Box.window_size - 1, -1, -1):
            if hit_mask[row, col] == 0:
                keep_symbol[keep_count] = board[row, col]
                keep_gold[keep_count] = gold_mask[row, col]
                keep_multi[keep_count] = multi_mask[row, col]
                keep_count += 1

        keep_idx = 0
        for row in range(Box.window_size - 1, -1, -1):
            if hit_mask[row, col] == 2:
                board[row, col] = Box.WW
                gold_mask[row, col] = 0
                multi_mask[row, col] = 0
            elif keep_idx < keep_count:
                board[row, col] = keep_symbol[keep_idx]
                gold_mask[row, col] = keep_gold[keep_idx]
                multi_mask[row, col] = keep_multi[keep_idx]
                keep_idx += 1
            else:
                if use_drop_a == 1:
                    drop_idx = pick_by_cum(Box.drop_weight_a_cum[table_id, :, col])
                else:
                    drop_idx = pick_by_cum(Box.drop_weight_b_cum[table_id, :, col])
                drop_symbol = Box.symbol_id[drop_idx]

                board[row, col] = Box.base_symbol_of[drop_symbol]
                gold_mask[row, col] = Box.is_gold_symbol[drop_symbol]
                if gold_mask[row, col] == 1:
                    assign_drop_multiplier(table_id, row, col, multi_mask)
                else:
                    multi_mask[row, col] = 0


@njit(nogil=True)
def update_spin_flags(gold_mask, multi_mask, gold_seen, multi_seen):
    for row in range(Box.window_size):
        for col in range(Box.reel_num):
            if gold_mask[row, col] == 1:
                gold_seen = 1
                if multi_mask[row, col] > 0:
                    multi_seen = 1
    return gold_seen, multi_seen


@njit(nogil=True)
def run_spin(
    scene_mode,
    fg_multiplier_sum,
    board,
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
    generate_board(table_id, board, gold_mask, multi_mask)
    scatter_count = count_scatter(board)
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
            pay_cascade, _ = evaluate_board(board, hit_mask, spin_hits, spin_pay)
        else:
            pay_cascade, _ = evaluate_board(board, hit_mask, spin_eliminate, spin_pay)

        if pay_cascade <= 0:
            break

        raw_pay += pay_cascade
        hit_any = 1

        for row in range(Box.window_size):
            for col in range(Box.reel_num):
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

        cascade_drop(table_id, use_drop_a, board, gold_mask, multi_mask, hit_mask, keep_symbol, keep_gold, keep_multi)
        gold_appear, multi_appear = update_spin_flags(gold_mask, multi_mask, gold_appear, multi_appear)
        combo_idx += 1

    final_multiplier = multiplier_sum if multiplier_sum > 0 else 1
    final_pay = raw_pay * final_multiplier
    return final_pay, scatter_count, hit_any, multiplier_sum, final_multiplier, combo_idx, gold_appear, gold_used, multi_appear, multi_used, pre_eliminate_gold_count


@njit(nogil=True)
def add_line_record(record_data, row_start, data, factor, scene_idx):
    offset = scene_idx * Box.symbols_count
    for line_idx in range(3):
        for symbol in range(Box.symbols_count):
            value = data[line_idx, symbol]
            if value > 0:
                record_data[row_start + line_idx, offset + symbol] += value * factor


@njit(nogil=True)
def log_multi_line(record_data, scene_idx, score):
    if scene_idx == Box.output_BG:
        cnt_idx = Box.R_multiplier_range_cnt_BG
        pay_idx = Box.R_multiplier_range_pay_BG
    elif scene_idx == Box.output_FG:
        cnt_idx = Box.R_multiplier_range_cnt_FG
        pay_idx = Box.R_multiplier_range_pay_FG
    else:
        cnt_idx = Box.R_multiplier_range_cnt_OA
        pay_idx = Box.R_multiplier_range_pay_OA

    multi = score / coin_in
    target = threshold_record.shape[0] - 1
    for idx in range(threshold_record.shape[0]):
        if multi <= threshold_record[idx]:
            target = idx
            break

    record_data[cnt_idx, target] += 1
    record_data[pay_idx, target] += score


@njit(nogil=True)
def apply_spin_log(record_data, scene_idx, spin_pay_total, hit_any, final_multiplier, spin_hits, spin_pay, spin_eliminate, eliminate_count, gold_appear, gold_used, multi_appear, multi_used, final_gold_count):
    if scene_idx == Box.scence_BG:
        if hit_any == 1:
            record_data[Box.R_all, Box.RA_hits_BG] += 1
    else:
        if hit_any == 1:
            record_data[Box.R_all, Box.RA_hits_FG] += 1

    add_line_record(record_data, Box.R_hits[0], spin_hits, 1, scene_idx)
    add_line_record(record_data, Box.R_pay[0], spin_pay, final_multiplier, scene_idx)
    add_line_record(record_data, Box.R_eliminate[0], spin_eliminate, 1, scene_idx)

    if scene_idx == Box.scence_BG:
        if eliminate_count == 0:
            record_data[Box.R_all, Box.RA_eliminate_0] += 1
        elif eliminate_count == 1:
            record_data[Box.R_all, Box.RA_eliminate_1] += 1
        elif eliminate_count == 2:
            record_data[Box.R_all, Box.RA_eliminate_2] += 1
        elif eliminate_count == 3:
            record_data[Box.R_all, Box.RA_eliminate_3] += 1
        elif eliminate_count == 4:
            record_data[Box.R_all, Box.RA_eliminate_4] += 1
        elif eliminate_count >= 5:
            record_data[Box.R_all, Box.RA_eliminate_5] += 1
    else:
        if eliminate_count == 0:
            record_data[Box.R_all, Box.RA_eliminate_0_FG] += 1
        elif eliminate_count == 1:
            record_data[Box.R_all, Box.RA_eliminate_1_FG] += 1
        elif eliminate_count == 2:
            record_data[Box.R_all, Box.RA_eliminate_2_FG] += 1
        elif eliminate_count == 3:
            record_data[Box.R_all, Box.RA_eliminate_3_FG] += 1
        elif eliminate_count == 4:
            record_data[Box.R_all, Box.RA_eliminate_4_FG] += 1
        elif eliminate_count >= 5:
            record_data[Box.R_all, Box.RA_eliminate_5_FG] += 1

    record_data[Box.R_all, Box.RA_gold_appear_spins] += gold_appear
    record_data[Box.R_all, Box.RA_gold_used_spins] += gold_used
    record_data[Box.R_all, Box.RA_multi_appear_spins] += multi_appear
    record_data[Box.R_all, Box.RA_multi_used_spins] += multi_used
    if scene_idx == Box.scence_BG:
        record_data[Box.R_all, Box.RA_final_gold_count_BG_0 + min(final_gold_count, 9)] += 1
    else:
        record_data[Box.R_all, Box.RA_final_gold_count_FG_0 + min(final_gold_count, 9)] += 1

    if spin_pay_total >= Box.max_win_multiplier * Box.default_coin_in * Box.normalbet:
        record_data[Box.R_all, Box.RA_max_win_hits] += 1
    if spin_pay_total > record_data[Box.R_all, Box.RA_max_single_win]:
        record_data[Box.R_all, Box.RA_max_single_win] = spin_pay_total
    if final_multiplier > record_data[Box.R_all, Box.RA_max_multiplier]:
        record_data[Box.R_all, Box.RA_max_multiplier] = final_multiplier


# %% Simulate


@njit("int64[:, :](int64[:, :], int64)", nogil=True)
def simulator_game(record_data, total_round):
    board = np.zeros(Box.layout_shape, np.int64)
    gold_mask = np.zeros(Box.layout_shape, np.int64)
    multi_mask = np.zeros(Box.layout_shape, np.int64)
    hit_mask = np.zeros(Box.layout_shape, np.int64)
    spin_hits = np.zeros((3, Box.symbols_count), np.int64)
    spin_pay = np.zeros((3, Box.symbols_count), np.int64)
    spin_eliminate = np.zeros((3, Box.symbols_count), np.int64)
    gold_pos = np.zeros((Box.window_size * Box.reel_num, 2), np.int64)
    keep_symbol = np.zeros(Box.window_size, np.int64)
    keep_gold = np.zeros(Box.window_size, np.int64)
    keep_multi = np.zeros(Box.window_size, np.int64)

    for _ in range(total_round):
        pay_bg = 0
        pay_fg = 0

        if bet_mode == Box.mode_normalbet:
            spin_pay_total, scatter_count, hit_any, _, final_multiplier, eliminate_count, gold_appear, gold_used, multi_appear, multi_used, final_gold_count = run_spin(0, 0, board, gold_mask, multi_mask, hit_mask, spin_hits, spin_pay, spin_eliminate, gold_pos, keep_symbol, keep_gold, keep_multi)
            pay_bg = spin_pay_total
            apply_spin_log(record_data, Box.scence_BG, spin_pay_total, hit_any, final_multiplier, spin_hits, spin_pay, spin_eliminate, eliminate_count, gold_appear, gold_used, multi_appear, multi_used, final_gold_count)

            free_spins = 0
            if scatter_count >= 3:
                free_spins = 15 + (scatter_count - 3) * 2
                record_data[Box.R_all, Box.RA_trigger_freegame] += 1
                record_data[Box.R_all, Box.RA_trigger_FG_pay_BG] += pay_bg
        else:
            spin_pay_total, scatter_count, hit_any, _, final_multiplier, eliminate_count, gold_appear, gold_used, multi_appear, multi_used, final_gold_count = run_spin(2, 0, board, gold_mask, multi_mask, hit_mask, spin_hits, spin_pay, spin_eliminate, gold_pos, keep_symbol, keep_gold, keep_multi)
            pay_bg = spin_pay_total
            apply_spin_log(record_data, Box.scence_BG, spin_pay_total, hit_any, final_multiplier, spin_hits, spin_pay, spin_eliminate, eliminate_count, gold_appear, gold_used, multi_appear, multi_used, final_gold_count)
            free_spins = 15 if scatter_count < 3 else 15 + (scatter_count - 3) * 2
            record_data[Box.R_all, Box.RA_trigger_freegame] += 1
            record_data[Box.R_all, Box.RA_trigger_FG_pay_BG] += pay_bg

        fg_multiplier_sum = 0
        remaining_freespin = min(free_spins, fg_spin_cap)
        while remaining_freespin > 0:
            spin_pay_total, scatter_count, hit_any, fg_multiplier_sum, final_multiplier, eliminate_count, gold_appear, gold_used, multi_appear, multi_used, final_gold_count = run_spin(
                1, fg_multiplier_sum, board, gold_mask, multi_mask, hit_mask, spin_hits, spin_pay, spin_eliminate, gold_pos, keep_symbol, keep_gold, keep_multi
            )
            pay_fg += spin_pay_total
            apply_spin_log(record_data, Box.scence_FG, spin_pay_total, hit_any, final_multiplier, spin_hits, spin_pay, spin_eliminate, eliminate_count, gold_appear, gold_used, multi_appear, multi_used, final_gold_count)

            record_data[Box.R_all, Box.RA_free_spins] += 1
            remaining_freespin -= 1

            if scatter_count >= 3:
                remaining_freespin = min(remaining_freespin + 15 + (scatter_count - 3) * 2, fg_spin_cap)
                record_data[Box.R_all, Box.RA_re_trigger] += 1

        pay_total = pay_bg + pay_fg
        record_data[Box.R_all, Box.RA_x_sum] += int(pay_total / coin_in * 1000000)
        record_data[Box.R_all, Box.RA_x_square] += int((pay_total / coin_in) ** 2 * 1000000)

        log_multi_line(record_data, Box.output_BG, pay_bg)
        if pay_fg > 0:
            log_multi_line(record_data, Box.output_FG, pay_fg)
        log_multi_line(record_data, Box.output_OA, pay_total)

    return record_data


record_data = np.zeros(Box.record_size, np.int64)
durning = 0.0


def _pick_by_cum_trace(cum_weight):
    total = int(cum_weight[-1])
    if total <= 0:
        return 0, 0, total
    rd = np.random.randint(0, total)
    for idx, value in enumerate(cum_weight):
        if rd < value:
            return idx, rd, total
    return len(cum_weight) - 1, rd, total


def _format_board(board, gold_mask=None, multi_mask=None):
    rows = []
    for row in range(board.shape[0]):
        row_items = []
        for col in range(board.shape[1]):
            symbol = int(board[row, col])
            name = Box.symbol_str.get(symbol, str(symbol))
            if gold_mask is not None and gold_mask[row, col] == 1:
                name = f"{name}*"
            if multi_mask is not None and multi_mask[row, col] > 0:
                name = f"{name}x{int(multi_mask[row, col])}"
            row_items.append(f"{name:>8}")
        rows.append(" ".join(row_items))
    return "\n".join(rows)


def _print_weight_info(title, values):
    print(f"{title}: [{', '.join(str(int(v)) for v in values)}]")


def _weight_text(values):
    return f"[{', '.join(str(int(v)) for v in values)}]"


def _choose_table_trace(scene_mode, fg_multiplier_sum):
    if scene_mode == 0:
        weights = Box.weight_table_BG
        offset = 0
        table_group = "BG"
        choice, rng_value, rng_total = _pick_by_cum_trace(np.cumsum(weights))
        table_id = offset + choice
    elif scene_mode == 1:
        weights = None
        rng_value = -1
        rng_total = 0
        if fg_multiplier_sum < 10:
            table_id = 3
            table_group = "FG<10"
        elif fg_multiplier_sum < 20:
            table_id = 4
            table_group = "FG10-20"
        else:
            table_id = 5
            table_group = "FG20+"
    else:
        weights = Box.weight_table_BF
        offset = 6
        table_group = "BF"
        choice, rng_value, rng_total = _pick_by_cum_trace(np.cumsum(weights))
        table_id = offset + choice
    return table_id, {
        "table_group": table_group,
        "rng_value": rng_value,
        "rng_total": rng_total,
        "weights": None if weights is None else weights.copy(),
    }


def _choose_eliminate_table_trace(scene_mode):
    if scene_mode == Box.scence_BG:
        weights = Box.eliminate_table_weight_BG
        table_group = "BG"
        choice, rng_value, rng_total = _pick_by_cum_trace(Box.eliminate_table_weight_cum_BG)
        use_drop_a = 1 if choice == 0 else 0
    elif scene_mode == Box.scence_FG:
        weights = Box.eliminate_table_weight_FG
        table_group = "FG"
        choice, rng_value, rng_total = _pick_by_cum_trace(Box.eliminate_table_weight_cum_FG)
        use_drop_a = 1 if choice == 0 else 0
    else:
        weights = np.array([1, 1], dtype=np.int64)
        table_group = "BF"
        rng_total = 2
        rng_value = np.random.randint(0, rng_total)
        use_drop_a = rng_value

    return use_drop_a, {
        "table_group": table_group,
        "rng_value": rng_value,
        "rng_total": rng_total,
        "weights": weights.copy(),
    }


def _generate_board_trace(table_id, board, gold_mask, multi_mask, trace_logs):
    reel_rng_info = []
    for col in range(Box.reel_num):
        reel_length = int(Box.reels_len[table_id, col])
        cum_weight = Box.arr_reels_weight_cum[table_id, :reel_length, col]
        stop_idx, rng_value, rng_total = _pick_by_cum_trace(cum_weight)
        strip_weights = Box.arr_reels_weight[table_id, :reel_length, col].copy()
        reel_rng_info.append((col + 1, rng_value, rng_total, stop_idx))
        trace_logs.append(f"Reel {col + 1} Strip Weights: {_weight_text(strip_weights)}")
        for row in range(Box.window_size):
            symbol = int(Box.arr_reels[table_id, (stop_idx + row) % reel_length, col])
            board[row, col] = Box.base_symbol_of[symbol]
            gold_mask[row, col] = Box.is_gold_symbol[symbol]
            multi_mask[row, col] = 0
    return reel_rng_info


def _assign_initial_multiplier_trace(table_id, gold_mask, multi_mask, trace_logs):
    gold_positions = [(row, col) for row in range(Box.window_size) for col in range(Box.reel_num) if gold_mask[row, col] == 1]
    gold_count = len(gold_positions)
    if gold_count == 0:
        trace_logs.append("Initial Multiplier: no gold symbols on initial board")
        return

    special_idx = -1
    if table_id < 3:
        special_weight = int(Box.weight_special_pool[min(gold_count, 9), table_id])
        trace_logs.append(f"Special Pool Weight: gold_count={gold_count}, weight={special_weight}")
        if special_weight > 0 and np.random.randint(0, Box.special_pool_weight_base) < special_weight:
            special_idx = np.random.randint(0, gold_count)
            trace_logs.append(f"Special Pool Multiplier Weights: {_weight_text(Box.weight_multiple_special[:, table_id])}")
    for idx, (row, col) in enumerate(gold_positions):
        if idx == special_idx:
            multi_idx, rng_value, rng_total = _pick_by_cum_trace(Box.weight_cum_multiple_special[:, table_id])
            multi = Box.value_multiplier_range[multi_idx]
            trace_logs.append(f"Gold ({row},{col}) Special Pool RNG={rng_value}/{rng_total} -> x{int(multi)}")
        else:
            if col == 2:
                weights = Box.weight_multiple_r3_before[:, table_id]
                cum_weights = Box.weight_cum_multiple_r3_before[:, table_id]
                source = "R3 Before"
            else:
                weights = Box.weight_multiple_before[:, table_id]
                cum_weights = Box.weight_cum_multiple_before[:, table_id]
                source = "Before"
            trace_logs.append(f"{source} Multiplier Weights: {_weight_text(weights)}")
            multi_idx, rng_value, rng_total = _pick_by_cum_trace(cum_weights)
            multi = Box.value_multiplier_range[multi_idx]
            trace_logs.append(f"Gold ({row},{col}) {source} RNG={rng_value}/{rng_total} -> x{int(multi)}")
        multi_mask[row, col] = multi


def _get_pay_trace(symbol, line_len):
    if symbol < 0 or Box.is_score_symbol[symbol] == 0 or line_len < 3:
        return 0
    return int(Box.pay_table[symbol, line_len - 3] * bet_multi)


def _evaluate_board_trace(board, hit_mask, hit_accum, pay_accum):
    hit_mask.fill(0)
    total_pay = 0
    line_logs = []

    for line_idx in range(Box.paylines.shape[0]):
        best_symbol = -1
        best_len = 0
        best_pay = 0

        first_row = Box.paylines[line_idx, 0]
        first_symbol = int(board[first_row, 0])
        if first_symbol == Box.C1:
            continue

        if first_symbol == Box.WW:
            for symbol in Box.symbols_score:
                line_len = 0
                for reel in range(Box.reel_num):
                    row = Box.paylines[line_idx, reel]
                    symbol_on_line = int(board[row, reel])
                    if symbol_on_line == symbol or symbol_on_line == Box.WW:
                        line_len += 1
                    else:
                        break
                pay = _get_pay_trace(int(symbol), line_len)
                if pay > best_pay:
                    best_symbol = int(symbol)
                    best_len = line_len
                    best_pay = pay
        else:
            line_len = 0
            for reel in range(Box.reel_num):
                row = Box.paylines[line_idx, reel]
                symbol_on_line = int(board[row, reel])
                if symbol_on_line == first_symbol or symbol_on_line == Box.WW:
                    line_len += 1
                else:
                    break
            best_symbol = first_symbol
            best_len = line_len
            best_pay = _get_pay_trace(best_symbol, best_len)

        if best_pay <= 0:
            continue

        total_pay += best_pay
        hit_accum[best_len - 3, best_symbol] += 1
        pay_accum[best_len - 3, best_symbol] += best_pay
        line_logs.append((line_idx, best_symbol, best_len, best_pay))
        for reel in range(best_len):
            row = Box.paylines[line_idx, reel]
            hit_mask[row, reel] = 1

    return total_pay, line_logs


def _cascade_drop_trace(table_id, use_drop_a, board, gold_mask, multi_mask, hit_mask, trace_logs):
    for col in range(Box.reel_num):
        keep = []
        for row in range(Box.window_size - 1, -1, -1):
            if hit_mask[row, col] == 0:
                keep.append((int(board[row, col]), int(gold_mask[row, col]), int(multi_mask[row, col])))

        keep_idx = 0
        for row in range(Box.window_size - 1, -1, -1):
            if hit_mask[row, col] == 2:
                board[row, col] = Box.WW
                gold_mask[row, col] = 0
                multi_mask[row, col] = 0
            elif keep_idx < len(keep):
                board[row, col], gold_mask[row, col], multi_mask[row, col] = keep[keep_idx]
                keep_idx += 1
            else:
                weights = Box.drop_weight_a[table_id, :, col] if use_drop_a == 1 else Box.drop_weight_b[table_id, :, col]
                cum = Box.drop_weight_a_cum[table_id, :, col] if use_drop_a == 1 else Box.drop_weight_b_cum[table_id, :, col]
                drop_idx, rng_value, rng_total = _pick_by_cum_trace(cum)
                drop_symbol = int(Box.symbol_id[drop_idx])
                trace_logs.append(f"Drop Weights {'A' if use_drop_a == 1 else 'B'} Reel {col + 1}: {_weight_text(weights)}")
                trace_logs.append(f"Drop Reel {col + 1} Row {row} RNG={rng_value}/{rng_total} -> wheel_idx={drop_idx}, symbol={Box.symbol_str[int(drop_symbol)]}")
                board[row, col] = Box.base_symbol_of[drop_symbol]
                gold_mask[row, col] = Box.is_gold_symbol[drop_symbol]
                if gold_mask[row, col] == 1:
                    if col == 2:
                        weights = Box.weight_multiple_r3_after[:, table_id]
                        cum_weights = Box.weight_cum_multiple_r3_after[:, table_id]
                        source = "R3 After"
                    else:
                        weights = Box.weight_multiple_after[:, table_id]
                        cum_weights = Box.weight_cum_multiple_after[:, table_id]
                        source = "After"
                    trace_logs.append(f"{source} Multiplier Weights: {_weight_text(weights)}")
                    multi_idx, multi_rng, multi_total = _pick_by_cum_trace(cum_weights)
                    multi_mask[row, col] = Box.value_multiplier_range[multi_idx]
                    trace_logs.append(f"New Gold ({row},{col}) {source} RNG={multi_rng}/{multi_total} -> x{int(multi_mask[row, col])}")
                else:
                    multi_mask[row, col] = 0


def _run_spin_trace(scene_mode, fg_multiplier_sum, spin_no, spin_label):
    board = np.zeros(Box.layout_shape, np.int64)
    gold_mask = np.zeros(Box.layout_shape, np.int64)
    multi_mask = np.zeros(Box.layout_shape, np.int64)
    hit_mask = np.zeros(Box.layout_shape, np.int64)
    spin_hits = np.zeros((3, Box.symbols_count), np.int64)
    spin_pay = np.zeros((3, Box.symbols_count), np.int64)
    spin_eliminate = np.zeros((3, Box.symbols_count), np.int64)
    trace_logs = []
    combo_line_logs = []
    board_snapshots = []

    table_id, table_trace = _choose_table_trace(scene_mode, fg_multiplier_sum)
    use_drop_a, drop_table_trace = _choose_eliminate_table_trace(scene_mode)
    reel_rng_info = _generate_board_trace(table_id, board, gold_mask, multi_mask, trace_logs)
    scatter_count = int(np.sum(board == Box.C1))
    _assign_initial_multiplier_trace(table_id, gold_mask, multi_mask, trace_logs)
    pre_eliminate_gold_count = count_gold_mask(gold_mask)
    board_snapshots.append(("Initial Stop Board", _format_board(board, gold_mask, multi_mask)))

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
        pay_cascade, line_logs = _evaluate_board_trace(board, hit_mask, spin_hits if combo_idx == 0 else spin_eliminate, spin_pay)
        if pay_cascade <= 0:
            break

        combo_line_logs.append((combo_idx + 1, line_logs, int(pay_cascade)))
        raw_pay += pay_cascade
        hit_any = 1

        for row in range(Box.window_size):
            for col in range(Box.reel_num):
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
        board_snapshots.append((f"After Eliminate {combo_idx + 1}", _format_board(board, gold_mask, multi_mask)))

        if debug_show_cascade:
            trace_logs.append(f"Combo {combo_idx + 1} Board Before Cascade:\n{_format_board(board, gold_mask, multi_mask)}")
        _cascade_drop_trace(table_id, use_drop_a, board, gold_mask, multi_mask, hit_mask, trace_logs)
        gold_appear, multi_appear = update_spin_flags(gold_mask, multi_mask, gold_appear, multi_appear)
        board_snapshots.append((f"After Cascade {combo_idx + 1}", _format_board(board, gold_mask, multi_mask)))
        if debug_show_cascade:
            trace_logs.append(f"Combo {combo_idx + 1} Board After Cascade:\n{_format_board(board, gold_mask, multi_mask)}")
        combo_idx += 1

    final_multiplier = multiplier_sum if multiplier_sum > 0 else 1
    final_pay = raw_pay * final_multiplier
    print(f"\n========== Trace Spin {spin_no} ({spin_label}) ==========")
    print(f"Table RNG: {table_trace['rng_value']}/{table_trace['rng_total']} -> " f"{table_trace['table_group']} table_id={table_id} strip={Box.strip_name_map[table_id]}")
    if table_trace["weights"] is None:
        print(f"Table Rule: fg_multiplier_sum={fg_multiplier_sum} -> {table_trace['table_group']}")
    else:
        print(f"Table Weights: {_weight_text(table_trace['weights'])}")
    print(f"Eliminate Table Weights ({drop_table_trace['table_group']}): {_weight_text(drop_table_trace['weights'])}")
    print(f"Eliminate Table RNG: {drop_table_trace['rng_value']}/{drop_table_trace['rng_total']} -> {'A' if use_drop_a == 1 else 'B'}")
    for reel_no, rng_value, rng_total, stop_idx in reel_rng_info:
        print(f"Reel {reel_no} RNG: {rng_value}/{rng_total} -> stop_idx={stop_idx}")
    print(f"Scatter Count: {scatter_count}")
    print("Winning Lines:")
    if combo_line_logs:
        for combo_no, line_logs, combo_pay in combo_line_logs:
            print(f"- Combo {combo_no}: pay={combo_pay}")
            for line_idx, sym, line_len, pay in line_logs:
                print(f"  Line {line_idx + 1}: symbol={Box.symbol_str[sym]}, ways={line_len}, pay={pay}")
    else:
        print("- No winning lines")
    print("Board Progress:")
    for title, board_text in board_snapshots:
        print(f"- {title}:")
        print(board_text)
    print("Final Board:")
    print(_format_board(board, gold_mask, multi_mask))
    print("Used Weights:")
    for log in trace_logs:
        print(f"- {log}")
    print(f"Spin Result: raw_pay={raw_pay}, final_multiplier={final_multiplier}, final_pay={final_pay}, 消除前金框數={pre_eliminate_gold_count}")
    return final_pay, scatter_count, hit_any, multiplier_sum, final_multiplier, combo_idx, gold_appear, gold_used, multi_appear, multi_used, pre_eliminate_gold_count, spin_hits, spin_pay, spin_eliminate


def _apply_spin_log_py(record_data, scene_idx, spin_pay_total, hit_any, final_multiplier, spin_hits, spin_pay, spin_eliminate, eliminate_count, gold_appear, gold_used, multi_appear, multi_used, final_gold_count):
    if scene_idx == Box.scence_BG:
        if hit_any >= 1:
            record_data[Box.R_all, Box.RA_hits_BG] += 1
    else:
        if hit_any >= 1:
            record_data[Box.R_all, Box.RA_hits_FG] += 1

    offset = scene_idx * Box.symbols_count
    for line_idx in range(3):
        for symbol in range(Box.symbols_count):
            if spin_hits[line_idx, symbol] > 0:
                record_data[Box.R_hits[0] + line_idx, offset + symbol] += spin_hits[line_idx, symbol]
            if spin_pay[line_idx, symbol] > 0:
                record_data[Box.R_pay[0] + line_idx, offset + symbol] += spin_pay[line_idx, symbol] * final_multiplier
            if spin_eliminate[line_idx, symbol] > 0:
                record_data[Box.R_eliminate[0] + line_idx, offset + symbol] += spin_eliminate[line_idx, symbol]

    if scene_idx == Box.scence_BG:
        if eliminate_count == 0:
            record_data[Box.R_all, Box.RA_eliminate_0] += 1
        elif eliminate_count == 1:
            record_data[Box.R_all, Box.RA_eliminate_1] += 1
        elif eliminate_count == 2:
            record_data[Box.R_all, Box.RA_eliminate_2] += 1
        elif eliminate_count == 3:
            record_data[Box.R_all, Box.RA_eliminate_3] += 1
        elif eliminate_count == 4:
            record_data[Box.R_all, Box.RA_eliminate_4] += 1
        elif eliminate_count >= 5:
            record_data[Box.R_all, Box.RA_eliminate_5] += 1
    else:
        if eliminate_count == 0:
            record_data[Box.R_all, Box.RA_eliminate_0_FG] += 1
        elif eliminate_count == 1:
            record_data[Box.R_all, Box.RA_eliminate_1_FG] += 1
        elif eliminate_count == 2:
            record_data[Box.R_all, Box.RA_eliminate_2_FG] += 1
        elif eliminate_count == 3:
            record_data[Box.R_all, Box.RA_eliminate_3_FG] += 1
        elif eliminate_count == 4:
            record_data[Box.R_all, Box.RA_eliminate_4_FG] += 1
        elif eliminate_count >= 5:
            record_data[Box.R_all, Box.RA_eliminate_5_FG] += 1

    record_data[Box.R_all, Box.RA_gold_appear_spins] += gold_appear
    record_data[Box.R_all, Box.RA_gold_used_spins] += gold_used
    record_data[Box.R_all, Box.RA_multi_appear_spins] += multi_appear
    record_data[Box.R_all, Box.RA_multi_used_spins] += multi_used
    if scene_idx == Box.scence_BG:
        record_data[Box.R_all, Box.RA_final_gold_count_BG_0 + min(final_gold_count, 9)] += 1
    else:
        record_data[Box.R_all, Box.RA_final_gold_count_FG_0 + min(final_gold_count, 9)] += 1

    if spin_pay_total >= Box.max_win_multiplier * Box.default_coin_in * Box.normalbet:
        record_data[Box.R_all, Box.RA_max_win_hits] += 1
    if spin_pay_total > record_data[Box.R_all, Box.RA_max_single_win]:
        record_data[Box.R_all, Box.RA_max_single_win] = spin_pay_total
    if final_multiplier > record_data[Box.R_all, Box.RA_max_multiplier]:
        record_data[Box.R_all, Box.RA_max_multiplier] = final_multiplier


def _log_multi_line_py(record_data, scene_idx, score):
    if scene_idx == Box.output_BG:
        cnt_idx = Box.R_multiplier_range_cnt_BG
        pay_idx = Box.R_multiplier_range_pay_BG
    elif scene_idx == Box.output_FG:
        cnt_idx = Box.R_multiplier_range_cnt_FG
        pay_idx = Box.R_multiplier_range_pay_FG
    else:
        cnt_idx = Box.R_multiplier_range_cnt_OA
        pay_idx = Box.R_multiplier_range_pay_OA

    multi = score / coin_in
    target = threshold_record.shape[0] - 1
    for idx in range(threshold_record.shape[0]):
        if multi <= threshold_record[idx]:
            target = idx
            break
    record_data[cnt_idx, target] += 1
    record_data[pay_idx, target] += score


def simulator_game_trace(record_data, total_round):
    trace_rounds = min(int(total_round), int(debug_trace_limit))
    for round_idx in range(trace_rounds):
        pay_bg = 0
        pay_fg = 0

        if bet_mode == Box.mode_normalbet:
            spin_pay_total, scatter_count, hit_any, _, final_multiplier, eliminate_count, gold_appear, gold_used, multi_appear, multi_used, final_gold_count, spin_hits, spin_pay, spin_eliminate = _run_spin_trace(0, 0, round_idx + 1, "BG")
            pay_bg = spin_pay_total
            _apply_spin_log_py(record_data, Box.scence_BG, spin_pay_total, hit_any, final_multiplier, spin_hits, spin_pay, spin_eliminate, eliminate_count, gold_appear, gold_used, multi_appear, multi_used, final_gold_count)
            free_spins = 0
            if scatter_count >= 3:
                free_spins = 15 + (scatter_count - 3) * 2
                record_data[Box.R_all, Box.RA_trigger_freegame] += 1
                record_data[Box.R_all, Box.RA_trigger_FG_pay_BG] += pay_bg
        else:
            spin_pay_total, scatter_count, hit_any, _, final_multiplier, eliminate_count, gold_appear, gold_used, multi_appear, multi_used, final_gold_count, spin_hits, spin_pay, spin_eliminate = _run_spin_trace(2, 0, round_idx + 1, "BF")
            pay_bg = spin_pay_total
            _apply_spin_log_py(record_data, Box.scence_BG, spin_pay_total, hit_any, final_multiplier, spin_hits, spin_pay, spin_eliminate, eliminate_count, gold_appear, gold_used, multi_appear, multi_used, final_gold_count)
            free_spins = 15 if scatter_count < 3 else 15 + (scatter_count - 3) * 2
            record_data[Box.R_all, Box.RA_trigger_freegame] += 1
            record_data[Box.R_all, Box.RA_trigger_FG_pay_BG] += pay_bg

        fg_multiplier_sum = 0
        remaining_freespin = min(free_spins, fg_spin_cap)
        fg_spin_idx = 0
        while remaining_freespin > 0:
            fg_spin_idx += 1
            spin_pay_total, scatter_count, hit_any, fg_multiplier_sum, final_multiplier, eliminate_count, gold_appear, gold_used, multi_appear, multi_used, final_gold_count, spin_hits, spin_pay, spin_eliminate = _run_spin_trace(1, fg_multiplier_sum, round_idx + 1, f"FG-{fg_spin_idx}")
            pay_fg += spin_pay_total
            _apply_spin_log_py(record_data, Box.scence_FG, spin_pay_total, hit_any, final_multiplier, spin_hits, spin_pay, spin_eliminate, eliminate_count, gold_appear, gold_used, multi_appear, multi_used, final_gold_count)
            record_data[Box.R_all, Box.RA_free_spins] += 1
            remaining_freespin -= 1
            if scatter_count >= 3:
                remaining_freespin = min(remaining_freespin + 15 + (scatter_count - 3) * 2, fg_spin_cap)
                record_data[Box.R_all, Box.RA_re_trigger] += 1

        pay_total = pay_bg + pay_fg
        record_data[Box.R_all, Box.RA_x_sum] += int(pay_total / coin_in * 1000000)
        record_data[Box.R_all, Box.RA_x_square] += int((pay_total / coin_in) ** 2 * 1000000)
        _log_multi_line_py(record_data, Box.output_BG, pay_bg)
        if pay_fg > 0:
            _log_multi_line_py(record_data, Box.output_FG, pay_fg)
        _log_multi_line_py(record_data, Box.output_OA, pay_total)

    return record_data


def run_simulation(rounds=total_round):
    global record_data, durning, total_round

    total_round = int(rounds)
    if debug_spin_trace:
        print(f"[Trace] Spin trace enabled -> rounds={min(total_round, debug_trace_limit)}")
        record_data, durning = simulation.time_func("Duration: ", simulator_game_trace, np.zeros(Box.record_size, np.int64), min(total_round, debug_trace_limit))
    else:
        # 先在主執行緒完成 Numba compile，避免多執行緒同時 compile。
        simulator_game(np.zeros(Box.record_size, np.int64), 1)
        func_nb_mt = simulation.make_multi_thread(simulator_game, round=total_round, output_shape=Box.record_size)
        record_data, durning = simulation.time_func("Duration: ", func_nb_mt)
    return record_data, durning


# %% simulater Result


def simulater_result(show_result=False, show_detail=False, show_multi_line=False, output_data=False, return_dict=True):
    def write_data(df, add_data_index="", add_data_value="", add_data_value2=""):
        df.loc[df.shape[0]] = [add_data_index, add_data_value, add_data_value2]

    def get_multiplier_data(multiplier_data, threshold=Mat.threshold_record):
        threshold_str = []
        for idx in range(len(threshold)):
            if idx == 0:
                threshold_str.append("0")
            else:
                threshold_str.append(str(threshold[idx - 1]) + " < X <= " + str(threshold[idx]))

        threshold_len = len(threshold)
        df = pd.DataFrame({"Interval": threshold_str})
        df["base_game_cnt"] = multiplier_data[Box.R_multiplier_range_cnt_BG, :threshold_len]
        df["base_game_pay"] = multiplier_data[Box.R_multiplier_range_pay_BG, :threshold_len]
        df["free_game_cnt"] = multiplier_data[Box.R_multiplier_range_cnt_FG, :threshold_len]
        df["free_game_pay"] = multiplier_data[Box.R_multiplier_range_pay_FG, :threshold_len]
        df["overall_cnt"] = multiplier_data[Box.R_multiplier_range_cnt_OA, :threshold_len]
        df["overall_pay"] = multiplier_data[Box.R_multiplier_range_pay_OA, :threshold_len]
        return df

    record_data_float = record_data.astype(np.float64)
    x_sum = record_data_float[Box.R_all, Box.RA_x_sum] / 1000000
    x_square = record_data_float[Box.R_all, Box.RA_x_square] / 1000000

    rtp_bg = record_data_float[Box.R_pay[0] : Box.R_pay[1], : Box.symbols_count].sum() / coin_in / total_round
    rtp_fg = record_data_float[Box.R_pay[0] : Box.R_pay[1], Box.symbols_count : Box.symbols_count * 2].sum() / coin_in / total_round
    rtp_total = rtp_bg + rtp_fg

    hit_rate_bg = record_data_float[Box.R_all, Box.RA_hits_BG] / total_round
    fg_spins = record_data_float[Box.R_all, Box.RA_free_spins]
    total_spins = total_round + fg_spins
    hit_rate_fg = record_data_float[Box.R_all, Box.RA_hits_FG] / fg_spins if fg_spins > 0 else 0
    hit_rate_total = (record_data_float[Box.R_all, Box.RA_hits_BG] + record_data_float[Box.R_all, Box.RA_hits_FG]) / total_spins if total_spins > 0 else 0
    trigger_rate_fg = record_data_float[Box.R_all, Box.RA_trigger_freegame] / total_round
    retrigger_rate = record_data_float[Box.R_all, Box.RA_re_trigger] / fg_spins if fg_spins > 0 else 0

    eliminate_0_rate = record_data_float[Box.R_all, Box.RA_eliminate_0] / total_spins if total_spins > 0 else 0
    eliminate_1_rate = record_data_float[Box.R_all, Box.RA_eliminate_1] / total_spins if total_spins > 0 else 0
    eliminate_2_rate = record_data_float[Box.R_all, Box.RA_eliminate_2] / total_spins if total_spins > 0 else 0
    eliminate_3_rate = record_data_float[Box.R_all, Box.RA_eliminate_3] / total_spins if total_spins > 0 else 0
    eliminate_4_rate = record_data_float[Box.R_all, Box.RA_eliminate_4] / total_spins if total_spins > 0 else 0
    eliminate_5_rate = record_data_float[Box.R_all, Box.RA_eliminate_5] / total_spins if total_spins > 0 else 0

    eliminate_0_FG_rate = record_data_float[Box.R_all, Box.RA_eliminate_0_FG] / total_spins if total_spins > 0 else 0
    eliminate_1_FG_rate = record_data_float[Box.R_all, Box.RA_eliminate_1_FG] / total_spins if total_spins > 0 else 0
    eliminate_2_FG_rate = record_data_float[Box.R_all, Box.RA_eliminate_2_FG] / total_spins if total_spins > 0 else 0
    eliminate_3_FG_rate = record_data_float[Box.R_all, Box.RA_eliminate_3_FG] / total_spins if total_spins > 0 else 0
    eliminate_4_FG_rate = record_data_float[Box.R_all, Box.RA_eliminate_4_FG] / total_spins if total_spins > 0 else 0
    eliminate_5_FG_rate = record_data_float[Box.R_all, Box.RA_eliminate_5_FG] / total_spins if total_spins > 0 else 0

    gold_line_rate = record_data_float[Box.R_all, Box.RA_gold_used_spins] / total_spins if total_spins > 0 else 0
    gold_usage_rate = record_data_float[Box.R_all, Box.RA_gold_used_spins] / record_data_float[Box.R_all, Box.RA_gold_appear_spins] if record_data_float[Box.R_all, Box.RA_gold_appear_spins] > 0 else 0
    multi_usage_rate = record_data_float[Box.R_all, Box.RA_multi_used_spins] / record_data_float[Box.R_all, Box.RA_multi_appear_spins] if record_data_float[Box.R_all, Box.RA_multi_appear_spins] > 0 else 0
    final_gold_count_stats_bg = []
    final_gold_count_stats_fg = []
    for gold_count in range(10):
        count_bg = int(record_data[Box.R_all, Box.RA_final_gold_count_BG_0 + gold_count])
        rate_bg = count_bg / total_round if total_round > 0 else 0
        final_gold_count_stats_bg.append((gold_count, count_bg, rate_bg))
        count_fg = int(record_data[Box.R_all, Box.RA_final_gold_count_FG_0 + gold_count])
        rate_fg = count_fg / fg_spins if fg_spins > 0 else 0
        final_gold_count_stats_fg.append((gold_count, count_fg, rate_fg))
    std = max(0.0, x_square / total_round - (x_sum / total_round) ** 2) ** 0.5

    df_base = pd.DataFrame([], columns=["Index", "Value", "Value2"])
    write_data(df_base, "total round", format(total_round, ","))
    write_data(df_base, "durning", f"{durning:0.2f}s")
    write_data(df_base, "RTP", f"{rtp_total:0.6f}")
    write_data(df_base, "RTP - BG", f"{rtp_bg:0.6f}")
    write_data(df_base, "RTP - FG", f"{rtp_fg:0.6f}")
    write_data(df_base, "Hit Rate - BG", f"{hit_rate_bg:0.6f}")
    write_data(df_base, "Hit Rate - FG", f"{hit_rate_fg:0.6f}")
    write_data(df_base, "Hit Rate - Overall", f"{hit_rate_total:0.6f}")
    write_data(df_base, "FG Trigger Rate", f"{trigger_rate_fg:0.6f}")
    write_data(df_base, "Retrigger Rate", f"{retrigger_rate:0.6f}")

    write_data(df_base, "Eliminate 0 Rate", f"{eliminate_0_rate:0.6f}", int(record_data[Box.R_all, Box.RA_eliminate_0]))
    write_data(df_base, "Eliminate 1 Rate", f"{eliminate_1_rate:0.6f}", int(record_data[Box.R_all, Box.RA_eliminate_1]))
    write_data(df_base, "Eliminate 2 Rate", f"{eliminate_2_rate:0.6f}", int(record_data[Box.R_all, Box.RA_eliminate_2]))
    write_data(df_base, "Eliminate 3 Rate", f"{eliminate_3_rate:0.6f}", int(record_data[Box.R_all, Box.RA_eliminate_3]))
    write_data(df_base, "Eliminate 4 Rate", f"{eliminate_4_rate:0.6f}", int(record_data[Box.R_all, Box.RA_eliminate_4]))
    write_data(df_base, "Eliminate 5 Rate", f"{eliminate_5_rate:0.6f}", int(record_data[Box.R_all, Box.RA_eliminate_5]))

    write_data(df_base, "Eliminate 0 FG Rate", f"{eliminate_0_FG_rate:0.6f}", int(record_data[Box.R_all, Box.RA_eliminate_0_FG]))
    write_data(df_base, "Eliminate 1 FG Rate", f"{eliminate_1_FG_rate:0.6f}", int(record_data[Box.R_all, Box.RA_eliminate_1_FG]))
    write_data(df_base, "Eliminate 2 FG Rate", f"{eliminate_2_FG_rate:0.6f}", int(record_data[Box.R_all, Box.RA_eliminate_2_FG]))
    write_data(df_base, "Eliminate 3 FG Rate", f"{eliminate_3_FG_rate:0.6f}", int(record_data[Box.R_all, Box.RA_eliminate_3_FG]))
    write_data(df_base, "Eliminate 4 FG Rate", f"{eliminate_4_FG_rate:0.6f}", int(record_data[Box.R_all, Box.RA_eliminate_4_FG]))
    write_data(df_base, "Eliminate 5 FG Rate", f"{eliminate_5_FG_rate:0.6f}", int(record_data[Box.R_all, Box.RA_eliminate_5_FG]))

    write_data(df_base, "Gold Line Rate", f"{gold_line_rate:0.6f}")
    write_data(df_base, "Gold Usage Rate", f"{gold_usage_rate:0.6f}")
    write_data(df_base, "Multiplier Usage Rate", f"{multi_usage_rate:0.6f}")
    for gold_count, count, rate in final_gold_count_stats_bg:
        write_data(df_base, f"消除前金框 BG {gold_count} 個", f"{count}/{int(total_round)} ({rate:.2%})")
    for gold_count, count, rate in final_gold_count_stats_fg:
        write_data(df_base, f"消除前金框 FG {gold_count} 個", f"{count}/{int(fg_spins)} ({rate:.2%})")
    write_data(df_base, "standard deviation", f"{std:0.6f}")
    write_data(df_base, "Max Win Hits", int(record_data[Box.R_all, Box.RA_max_win_hits]))
    write_data(df_base, "Max Win (x)", f"{record_data[Box.R_all, Box.RA_max_single_win] / coin_in:0.2f}")
    write_data(df_base, "Max Multiplier", int(record_data[Box.R_all, Box.RA_max_multiplier]))

    column_labels = [Box.symbol_str[sym] for sym in Box.symbol_id] + [Box.symbol_str[sym] for sym in Box.symbol_id]
    index_labels = ["3", "4", "5"]
    df_hits = pd.DataFrame(record_data_float[Box.R_hits[0] : Box.R_hits[1], : Box.symbols_count * 2], columns=column_labels, index=index_labels)
    df_pay = pd.DataFrame(record_data_float[Box.R_pay[0] : Box.R_pay[1], : Box.symbols_count * 2] / coin_in / total_round, columns=column_labels, index=index_labels)
    df_eliminate = pd.DataFrame(record_data_float[Box.R_eliminate[0] : Box.R_eliminate[1], : Box.symbols_count * 2], columns=column_labels, index=index_labels)

    result_dict = {
        "rtp_bg": rtp_bg,
        "rtp_fg": rtp_fg,
        "rtp_overall": rtp_total,
        "hit_rate_bg": hit_rate_bg,
        "hit_rate_fg": hit_rate_fg,
        "hit_rate_overall": hit_rate_total,
        "fg_trigger_rate": trigger_rate_fg,
        "retrigger_rate": retrigger_rate,
        "eliminate_0_rate": eliminate_0_rate,
        "eliminate_1_rate": eliminate_1_rate,
        "eliminate_2_rate": eliminate_2_rate,
        "eliminate_3_rate": eliminate_3_rate,
        "eliminate_4_rate": eliminate_4_rate,
        "eliminate_5_rate": eliminate_5_rate,
        "eliminate_0_count": int(record_data[Box.R_all, Box.RA_eliminate_0]),
        "eliminate_1_count": int(record_data[Box.R_all, Box.RA_eliminate_1]),
        "eliminate_2_count": int(record_data[Box.R_all, Box.RA_eliminate_2]),
        "eliminate_3_count": int(record_data[Box.R_all, Box.RA_eliminate_3]),
        "eliminate_4_count": int(record_data[Box.R_all, Box.RA_eliminate_4]),
        "eliminate_5_count": int(record_data[Box.R_all, Box.RA_eliminate_5]),
        "eliminate_0_FG_rate": eliminate_0_FG_rate,
        "eliminate_1_FG_rate": eliminate_1_FG_rate,
        "eliminate_2_FG_rate": eliminate_2_FG_rate,
        "eliminate_3_FG_rate": eliminate_3_FG_rate,
        "eliminate_4_FG_rate": eliminate_4_FG_rate,
        "eliminate_5_FG_rate": eliminate_5_FG_rate,
        "eliminate_0_FG_count": int(record_data[Box.R_all, Box.RA_eliminate_0_FG]),
        "eliminate_1_FG_count": int(record_data[Box.R_all, Box.RA_eliminate_1_FG]),
        "eliminate_2_FG_count": int(record_data[Box.R_all, Box.RA_eliminate_2_FG]),
        "eliminate_3_FG_count": int(record_data[Box.R_all, Box.RA_eliminate_3_FG]),
        "eliminate_4_FG_count": int(record_data[Box.R_all, Box.RA_eliminate_4_FG]),
        "eliminate_5_FG_count": int(record_data[Box.R_all, Box.RA_eliminate_5_FG]),
        "gold_line_rate": gold_line_rate,
        "gold_usage_rate": gold_usage_rate,
        "multiplier_usage_rate": multi_usage_rate,
        "final_gold_count_stats_bg": {gold_count: {"count": count, "rate": rate} for gold_count, count, rate in final_gold_count_stats_bg},
        "final_gold_count_stats_fg": {gold_count: {"count": count, "rate": rate} for gold_count, count, rate in final_gold_count_stats_fg},
        "volatility_std": std,
        "max_win_hits": int(record_data[Box.R_all, Box.RA_max_win_hits]),
        "max_win_x": record_data[Box.R_all, Box.RA_max_single_win] / coin_in,
        "max_multiplier": int(record_data[Box.R_all, Box.RA_max_multiplier]),
    }

    if show_result:
        div.div_center("simulate result - base info", lower=True)
        for data in df_base.values:
            log_use.print_result2(data[0], data[1], data[2])

    if show_detail:
        div.div_center("simulate result - hits", upper=True, lower=True)
        print(df_hits)
        div.div_center("simulate result - rtp", upper=True, lower=True)
        print(df_pay)
        div.div_center("simulate result - eliminate", upper=True, lower=True)
        print(df_eliminate)

    if show_multi_line:
        div.div_center("simulate result - plot", upper=True, lower=True)
        data_multiplier_cnt_bg = cplot.map_multiplier_big2small_v2(Mat.threshold_v7, Mat.threshold_v7, record_data[Box.R_multiplier_range_cnt_BG])
        data_multiplier_cnt_fg = cplot.map_multiplier_big2small_v2(Mat.threshold_v7, Mat.threshold_v7, record_data[Box.R_multiplier_range_cnt_FG])
        data_multiplier_cnt_oa = cplot.map_multiplier_big2small_v2(Mat.threshold_v7, Mat.threshold_v7, record_data[Box.R_multiplier_range_cnt_OA])
        cplot.multiplier_line(data_multiplier_cnt_bg, threshold=Mat.threshold_show, title=Box.plot_name + "BG", ylim=0.05)
        cplot.multiplier_line(data_multiplier_cnt_fg, threshold=Mat.threshold_show, title=Box.plot_name + "FG", ylim=0.25)
        cplot.multiplier_line(data_multiplier_cnt_oa, threshold=Mat.threshold_show, title=Box.plot_name + "OA", ylim=0.15)

    if output_data:
        df_multiplier = get_multiplier_data(record_data_float)
        with pd.ExcelWriter(Box.path_output_data(f"_betmode{bet_mode}")) as writer:
            df_base.to_excel(writer, sheet_name="Base Info", index=False)
            df_multiplier.to_excel(writer, sheet_name="Multiplier Line", index=False)
            df_hits.to_excel(writer, sheet_name="Hits")
            df_pay.to_excel(writer, sheet_name="Pay")
            df_eliminate.to_excel(writer, sheet_name="Eliminate")
            pd.DataFrame(record_data).to_excel(writer, sheet_name="Record Data", index=False)

    if return_dict:
        return df_base, {"summary": result_dict, "hits": df_hits, "pay": df_pay, "eliminate": df_eliminate}
    return df_base


if __name__ == "__main__":
    run_simulation(total_round)
    record_data = record_data.astype(np.float64)
    simulater_result(True, False, False, False)
