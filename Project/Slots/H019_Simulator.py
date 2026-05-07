# %% Import


import numpy as np
import pandas as pd
from numba import jit, njit
import math

import os

os.chdir("C:\\Users\\rhinshen\\Mine\\個人工作區\\2_Program")

# my package
import Project.Slots.Source.H019_Box as Box

import Project.Slots.Source.General.Math as Mat
from Project.Slots.Source.General.Math import simulation, cplot
from Project.Slots.Source.General.RedBox import div, log_use


# %% Setting

bet_multi = 1  # bet multiplier
bet_mode = Box.mode_narmalbet
# bet_mode = Box.mode_featurebuy
bet_mode = Box.mode_superfeaturebuy

total_round = 10**8  # 測試1
# total_round = 10**3  # 測試2
# total_round = 10**0  # 測試3
# total_round = 10**9  # 標準，時間: s
# total_round = 10**7


# %% Initial

# coin in
if bet_mode == Box.mode_narmalbet:
    coin_in = bet_multi * Box.default_coin_in * Box.normalbet
elif bet_mode == Box.mode_featurebuy:
    coin_in = bet_multi * Box.default_coin_in * Box.normalbet * Box.featurebuy
elif bet_mode == Box.mode_superfeaturebuy:
    coin_in = bet_multi * Box.default_coin_in * Box.normalbet * Box.superfeaturebuy

# setting
if bet_mode == Box.mode_narmalbet:
    value_freespin_table_choose_freegame = Box.value_freespin_table_choose_freegame
    value_freespin_table_choose_retrigger = Box.value_freespin_table_choose_retrigger
    weight_cum_c2_BG = Box.weight_cum_c2_BG
    weight_cum_c2_FG = Box.weight_cum_c2_FG
    weight_cum_c2_base_direct = Box.weight_cum_c2_base_direct
    weight_cum_c2_base_wild = Box.weight_cum_c2_base_wild
    weight_cum_c2_free_direct = Box.weight_cum_c2_free_direct
    weight_cum_c2_free_wild = Box.weight_cum_c2_free_wild
    weight_cum_c2_super = Box.weight_cum_c2_super
    weight_cum_c2_ultimate = Box.weight_cum_c2_ultimate
    weigh_cumt_c2_bad = Box.weigh_cumt_c2_bad
elif bet_mode == Box.mode_featurebuy:
    value_freespin_table_choose_freegame = Box.value_freespin_table_choose_freegame_BF
    value_freespin_table_choose_retrigger = Box.value_freespin_table_choose_retrigger_BF
    weight_cum_c2_BG = Box.weight_cum_c2_BG_BF
    weight_cum_c2_FG = Box.weight_cum_c2_FG_BF
    weight_cum_c2_base_direct = Box.weight_cum_c2_base_direct_BF
    weight_cum_c2_base_wild = Box.weight_cum_c2_base_wild_BF
    weight_cum_c2_free_direct = Box.weight_cum_c2_free_direct_BF
    weight_cum_c2_free_wild = Box.weight_cum_c2_free_wild_BF
    weight_cum_c2_super = Box.weight_cum_c2_super_BF
    weight_cum_c2_ultimate = Box.weight_cum_c2_ultimate_BF
    weigh_cumt_c2_bad = Box.weigh_cumt_c2_bad_BF
elif bet_mode == Box.mode_superfeaturebuy:
    value_freespin_table_choose_freegame = Box.value_freespin_table_choose_freegame_SF
    value_freespin_table_choose_retrigger = Box.value_freespin_table_choose_retrigger_SF
    weight_cum_c2_BG = Box.weight_cum_c2_BG_SF
    weight_cum_c2_FG = Box.weight_cum_c2_FG_SF
    weight_cum_c2_base_direct = Box.weight_cum_c2_base_direct_SF
    weight_cum_c2_base_wild = Box.weight_cum_c2_base_wild_SF
    weight_cum_c2_free_direct = Box.weight_cum_c2_free_direct_SF
    weight_cum_c2_free_wild = Box.weight_cum_c2_free_wild_SF
    weight_cum_c2_super = Box.weight_cum_c2_super_SF
    weight_cum_c2_ultimate = Box.weight_cum_c2_ultimate_SF
    weigh_cumt_c2_bad = Box.weigh_cumt_c2_bad_SF


# %% Simulate


@njit("int64[:, :](int64[:, :], int64)", nopython=True, nogil=True)
def simulator_game(record_data, total_round):  # 完整遊戲模擬

    # tool
    def get_value(cum_weight):
        rd = math.ceil(np.random.random() * cum_weight[-1]) - 1
        # rd = np.random.randint(0, cum_weight[-1])
        for i in range(len(cum_weight)):
            if rd < cum_weight[i]:
                return i

    def copy_array_1xn(li, li_copy):
        arr_shape = li.shape
        for i in range(arr_shape[0]):
            li_copy[i] = li[i]

    def copy_array(arr, arr_copy):
        """
        把"arr"複製到"arr_copy"上
        """
        arr_shape = arr.shape
        for i in range(arr_shape[0]):
            for j in range(arr_shape[1]):
                arr_copy[i, j] = arr[i, j]

    def get_element_num_nxn(arr, elemets):
        cnt = 0
        for i in range(arr.shape[0]):
            for j in range(arr.shape[1]):
                for e in elemets:
                    if arr[i, j] == e:
                        cnt += 1
        return cnt

    def get_interval(num, bounds):
        for i in range(len(bounds) - 1):
            if bounds[i] <= num < bounds[i + 1]:
                return i
        if num >= bounds[-1]:
            return len(bounds) - 1

        return -1  # 如果小於最低區間，可視需求回傳 None 或 -1

    def shuffle_inplace(li):
        n = li.shape[0]
        for i in range(n - 1, 0, -1):
            j = np.random.randint(0, i + 1)
            tmp = li[i]
            li[i] = li[j]
            li[j] = tmp

    def concatenate(arr1xn_A, arr1xn_B):
        len_A = arr1xn_A.shape[0]
        len_B = arr1xn_B.shape[0]

        arr1xn_new = np.zeros((len_A + len_B,), arr1xn_A.dtype)
        for i in range(len_A):
            arr1xn_new[i] = arr1xn_A[i]
        for j in range(len_B):
            arr1xn_new[j + len_A] = arr1xn_B[j]

        return arr1xn_new

    # pre-setting
    rng_BS = np.zeros(Box.reel_num[Box.scence_BG], np.int64)
    arr_result_BG = np.zeros((Box.window_size[Box.scence_BG], Box.reel_num[Box.scence_BG]), np.int64)
    arr_result_BG_pre = arr_result_BG.copy()

    rng_FS = np.zeros(Box.reel_num[Box.scence_FG], np.int64)
    arr_result_FG = np.zeros((Box.window_size[Box.scence_FG], Box.reel_num[Box.scence_FG]), np.int64)
    arr_result_FG_pre = arr_result_FG.copy()

    # log
    def log_multi_line(game_scence, score):  # 倍率線型
        """
        倍率線型紀錄
        """
        cnt_idx = 1
        pay_idx = 4
        if game_scence == 0:
            cnt_idx = Box.R_multiplier_range_cnt_BG
            pay_idx = Box.R_multiplier_range_pay_BG
            combo_idx = Box.R_multiplier_range_combo_BG
        elif game_scence == 1:
            cnt_idx = Box.R_multiplier_range_cnt_FG
            pay_idx = Box.R_multiplier_range_pay_FG
            combo_idx = Box.R_multiplier_range_combo_FG
        elif game_scence == 2:
            cnt_idx = Box.R_multiplier_range_cnt_OA
            pay_idx = Box.R_multiplier_range_pay_OA
            combo_idx = Box.R_multiplier_range_combo_OA

        multi = score / Box.default_coin_in
        for i in range(Box.threshold_record.shape[0] - 1):

            if multi <= Box.threshold_record[i]:
                record_data[cnt_idx][i] += 1
                record_data[pay_idx][i] += score
                # if combo != -1:
                #     record_data[combo_idx][i] += combo
                break

            elif Box.threshold_record[i] < multi and multi <= Box.threshold_record[i + 1]:
                record_data[cnt_idx][i + 1] += 1
                record_data[pay_idx][i + 1] += score
                # if combo != -1:
                #     record_data[combo_idx][i + 1] += combo
                break

    def log_all(condition, idx, v):
        if condition:
            record_data[Box.R_all, idx] += v

    def log_hit(symbol, line, posi_y_fix):  # 每個獎項的hit
        if symbol == Box.C1:
            idx = line - 4
        else:
            idx = get_interval(line, Box.pay_table_awards_cascading)
        if idx != -1:
            record_data[Box.R_hits[0] : Box.R_hits[1], :][idx, symbol + len(Box.symbols_all) * posi_y_fix] += 1  # posi_y_fix: 0->BG, 1->FG

    def log_pay(symbol, line, pay, posi_y_fix):  # 每個獎項的pay
        if symbol == Box.C1:
            idx = line - 4
        else:
            idx = get_interval(line, Box.pay_table_awards_cascading)

        if idx != -1:
            record_data[Box.R_pay[0] : Box.R_pay[1], :][idx, symbol + len(Box.symbols_all) * posi_y_fix] += pay

    def log_eliminate(symbol, line, posi_y_fix):  # 每個獎項的hit
        if symbol == Box.C1:
            idx = line - 4
            record_data[Box.R_eliminate[0] : Box.R_eliminate[1], :][idx, symbol + len(Box.symbols_all) * posi_y_fix] += 1  # posi_y_fix: 0->BG, 1->FG
        else:
            idx = get_interval(line, Box.pay_table_awards_cascading)
            if idx != -1:
                record_data[Box.R_eliminate[0] : Box.R_eliminate[1], :][idx, symbol + len(Box.symbols_all) * posi_y_fix] += int(line)  # posi_y_fix: 0->BG, 1->FG

    # tool - bygame
    def arr_result_generator(table_id, rng, arr_result):
        window_size, reel_num = arr_result.shape

        # generator rng
        for i in range(reel_num):
            ll = Box.reels_len[int(table_id), i]
            arr_reels_weight = Box.arr_reels_weight[int(table_id), :ll, i]
            use_reel_weight = np.cumsum(arr_reels_weight)
            rng[i] = get_value(use_reel_weight)

        # generator arr_result
        for i in range(window_size):
            for j in range(reel_num):
                use_reel = Box.arr_reels[int(table_id), :, j]
                use_reel_len = Box.reels_len[int(table_id), j]
                arr_result[i, j] = use_reel[(rng[j] + i) % use_reel_len]

    def get_pay(symbol, line):

        pay = 0
        if symbol == Box.C1 and line in Box.pay_table_C1:
            pay = Box.pay_table[Box.C1][line - 4] * bet_multi

        if symbol in Box.symbols_score and line >= Box.pay_table_awards_cascading[0]:
            idx = get_interval(line, Box.pay_table_awards_cascading)
            pay = Box.pay_table[symbol][idx + 3] * bet_multi

        return pay

    def calculate_win_c1(game_scence, arr_result):  # log

        # # bonus : 由最左至右連續出現
        # line = 0
        # for reel in arr_result.T:
        #     if Box.C1 in reel or Box.WW in reel:  # WW可以代替C1
        #         line += 1
        #         continue
        #     else:
        #         break

        # scatter : 出現在隨機位置
        line = 0
        for row in arr_result:
            for s in row:
                if s == Box.C1:
                    line += 1

        pay_c1 = get_pay(Box.C1, line)

        # record
        log_hit(Box.C1, line, game_scence)
        log_pay(Box.C1, line, pay_c1, game_scence)

        return pay_c1

    def calculate_win(game_scence, arr_result, pay_symbols, multi):  # log

        if multi == 0:
            multi = 1

        pay_sum = 0
        pay_symbols_new = np.full(len(Box.symbols_all), 99, dtype=arr_result.dtype)  # 預設最大長度

        idx = 0
        for symbol in Box.symbols_all:  # 每個symbol看
            if symbol in Box.symbols_score:
                line = get_element_num_nxn(arr_result, [Box.WW, symbol])
                pay = int(get_pay(symbol, line)) * int(multi)
                pay_sum += pay
                if pay > 0:
                    pay_symbols_new[idx] = symbol
                    idx += 1

                    log_hit(symbol, line, game_scence)
                    log_pay(symbol, line, pay, game_scence)
                    log_eliminate(symbol, line, game_scence)

                    # print("* symbol: ", symbol, "line: ", line, "multi: ", multi, "pay: ", pay)

        copy_array_1xn(pay_symbols_new, pay_symbols)

        return pay_sum

    def remove_and_fall(table_id, rng, arr_result, remove_symbol, remove_cnt):
        rows, cols = arr_result.shape

        for i in range(rows):
            for j in range(cols):
                if arr_result[i, j] == Box.WW:  # 前一把有消除掉的WW才會變C2
                    arr_result[i, j] = Box.C2  # WW轉C2

        for c in range(cols):
            # 取得要移除的符號（會往下掉）
            nonremove = []
            for i in arr_result[:, c]:
                if i not in remove_symbol:
                    nonremove.append(i)

            # 上面要補的數量
            missing = rows - len(nonremove)

            # 新欄位
            use_reel = Box.arr_reels[int(table_id), :, c]
            use_reel_clear = use_reel[use_reel != -1]  # 清除-1
            use_reel_clear_len = len(use_reel_clear)

            cnt_next = remove_cnt[c]
            while len(nonremove) < rows:
                cnt_next += 1
                append_symbol = use_reel_clear[rng[c] - int(cnt_next % use_reel_clear_len)]
                if Box.C1 in nonremove and append_symbol == Box.C1:
                    cnt_next += 1
                    append_symbol = use_reel_clear[rng[c] - int(cnt_next % use_reel_clear_len)]
                # if Box.C2 in nonremove and append_symbol == Box.C2: # 賽特的C2不會被跳過
                #     cnt_next += 1
                #     append_symbol = use_reel_clear[rng[c] - int(cnt_next % use_reel_clear_len)]

                nonremove.insert(0, append_symbol)

            remove_cnt[c] = cnt_next
            for i in range(rows):
                arr_result[:, c][i] = nonremove[i]

    def get_spin_result(arr_result, pay_symbols):
        pay_sum = 0
        pay_symbols_new = np.full(len(Box.symbols_all), 99, dtype=arr_result.dtype)  # 預設最大長度

        idx = 0
        for symbol in Box.symbols_all:  # 每個symbol看
            if symbol in Box.symbols_score:
                line = get_element_num_nxn(arr_result, [symbol, Box.WW])
                pay = int(get_pay(symbol, line))
                pay_sum += pay
                if pay > 0:
                    pay_symbols_new[idx] = symbol
                    idx += 1

        cnt_ww2c2 = 0
        if pay_sum >= 0:
            cnt_ww2c2 += get_element_num_nxn(arr_result, [Box.WW])

        copy_array_1xn(pay_symbols_new, pay_symbols)

        return cnt_ww2c2

    def table_set(weight):
        ll = sum(weight)
        free_spin_table_list = np.array([99 for i in range(ll)])
        idx = 0
        cnt = 0
        for num in weight:
            for i in range(num):
                free_spin_table_list[cnt] = idx
                cnt += 1
            idx += 1

        return free_spin_table_list

    # main
    def base_game():  # log
        """
        遊戲流程
        * spin->算分->消除->掉落->算分->...
        """
        pay_symbol_pre = np.full(len(Box.symbols_all), 99, dtype=arr_result_BG.dtype)
        pay_symbol = np.full(len(Box.symbols_all), 99, dtype=arr_result_BG.dtype)

        # spin --根據???決定使用的表
        table_id = 0
        if bet_mode == Box.mode_narmalbet:
            table_id = get_value(Box.weight_cum_table_BG)
        elif bet_mode == Box.mode_featurebuy:
            table_id = Box.strip_BF
        elif bet_mode == Box.mode_superfeaturebuy:
            table_id = Box.strip_BF
        arr_result_generator(table_id, rng_BS, arr_result_BG)
        mode_c2 = get_value(weight_cum_c2_BG)

        # print("* table_id:", table_id)
        # print("* rng:", rng_BS)
        # print("* arr_result_BG:\n", arr_result_BG)
        # print("* mode_c2:", mode_c2)

        # --------------------------------------------------- 先取得最終倍數

        copy_array(arr_result_BG, arr_result_BG_pre)  # 複製一個預先算倍數的arr

        num_ww2c2 = 0
        num_ww2c2 += get_spin_result(arr_result_BG_pre, pay_symbol_pre)

        # remove and fall
        remove_cnt_pre = np.zeros(Box.reel_num[Box.scence_BG], np.float64)
        cnt_eliminate = 0
        while True:
            if pay_symbol_pre[0] == 99:
                break
            # print("* pay_symbol_pre:", pay_symbol_pre, "\n")

            remove_and_fall(table_id, rng_BS, arr_result_BG_pre, pay_symbol_pre, remove_cnt_pre)

            num_ww2c2_temp = get_spin_result(arr_result_BG_pre, pay_symbol_pre)
            cnt_eliminate += 1

            if pay_symbol_pre[0] != 99:
                num_ww2c2 += num_ww2c2_temp

            # print(f"--- eliminate {cnt_eliminate:02.00f} ---")
            # print("* arr_result_BG_pre:\n", arr_result_BG_pre)

        # get multiplier
        multi_cum = 0
        num_C2 = get_element_num_nxn(arr_result_BG_pre, [Box.C2])
        if mode_c2 == 0:
            for i in range(num_C2 - num_ww2c2):
                idx = get_value(weight_cum_c2_base_direct)
                multi = Box.value_multiplier_range[int(idx)]
                multi_cum += multi
                # print("* multi C2 direct:", multi, multi_cum, idx)
            for i in range(num_ww2c2):
                idx = get_value(weight_cum_c2_base_wild)
                multi = Box.value_multiplier_range[int(idx)]
                multi_cum += multi
                # print("* multi WW to C2 :", multi, multi_cum, idx)
        if mode_c2 == 1:
            for i in range(num_C2):
                idx = get_value(weight_cum_c2_super)
                multi = Box.value_multiplier_range[int(idx)]
                multi_cum += multi
                # print("* multi C2 super:", multi, multi_cum, idx)
        if mode_c2 == 2:
            for i in range(num_C2):
                idx = get_value(weight_cum_c2_ultimate)
                multi = Box.value_multiplier_range[int(idx)]
                multi_cum += multi
                # print("* multi C2 ultimate:", multi, multi_cum, idx)

        # ---------------------------------------------------

        # print("\n--- calculate ---")

        # calculate
        pay_sum = 0
        pay_base = calculate_win(Box.scence_BG, arr_result_BG, pay_symbol, multi_cum)
        pay_sum += pay_base

        # remove and fall
        remove_cnt = np.zeros(Box.reel_num[Box.scence_BG], np.int64)
        cnt = 0
        while True:
            if pay_symbol[0] == 99:
                break
            remove_and_fall(table_id, rng_BS, arr_result_BG, pay_symbol, remove_cnt)
            pay_base = calculate_win(Box.scence_BG, arr_result_BG, pay_symbol, multi_cum)
            pay_sum += pay_base
            cnt += 1

        pay_c1 = calculate_win_c1(Box.scence_BG, arr_result_BG)
        num_c1 = get_element_num_nxn(arr_result_BG, [Box.C1])

        # ---------------------------------------------------

        # record
        log_all(pay_sum > 0, Box.RA_hits_BG, 1)
        log_all(cnt_eliminate >= 8, Box.RA_eliminate_BG[0] + 8, 1)
        log_all(cnt_eliminate < 8, Box.RA_eliminate_BG[0] + cnt_eliminate, 1)
        log_all(num_c1 > 0, Box.RA_have_SC_BG, 1)
        log_all(num_c1 == 0, Box.RA_no_SC_BG, 1)

        return pay_sum, pay_c1

    def free_game():  # log
        """
        遊戲流程??
        """
        pay_symbol_pre = np.full(len(Box.symbols_all), 99, dtype=arr_result_FG.dtype)
        pay_symbol = np.full(len(Box.symbols_all), 99, dtype=arr_result_FG.dtype)

        # 預先決定每一把spin抽哪張表
        free_spin_table_list = table_set(value_freespin_table_choose_freegame)
        shuffle_inplace(free_spin_table_list)

        # print("* value_freespin_table_choose_freegame:", value_freespin_table_choose_freegame)
        # print("* shuffle_inplace:", free_spin_table_list)

        pay_FG = 0
        cnt_freespin = 0
        cnt_multi_cum = 0
        while True:
            if cnt_freespin >= free_spin_table_list.shape[0]:
                break
            # print("\n====== cnt_freespin", cnt_freespin, "======\n")

            # spin 決定使用的表
            table_id = 0
            if bet_mode == Box.mode_narmalbet:
                table_id = free_spin_table_list[cnt_freespin] + 4
            elif bet_mode == Box.mode_featurebuy:
                table_id = free_spin_table_list[cnt_freespin] + 4
            elif bet_mode == Box.mode_superfeaturebuy:
                table_id = free_spin_table_list[cnt_freespin] + 9
            arr_result_generator(table_id, rng_FS, arr_result_FG)

            # print("* table_id:", table_id)
            # print("* rng:", rng_FS)
            # print("* arr_result_FG:\n", arr_result_FG)
            # print("* multi:", cnt_multi_cum, "\n")

            # --------------------------------------------------- 先取得最終倍數

            copy_array(arr_result_FG, arr_result_FG_pre)  # 複製一個預先算倍數的arr
            num_ww2c2 = 0
            num_ww2c2 += get_spin_result(arr_result_FG_pre, pay_symbol_pre)

            # remove and fall
            remove_cnt_pre = np.zeros(Box.reel_num[Box.scence_FG], np.int64)
            cnt_eliminate = 0
            while True:
                if pay_symbol_pre[0] == 99:
                    break

                remove_and_fall(table_id, rng_FS, arr_result_FG_pre, pay_symbol_pre, remove_cnt_pre)
                num_ww2c2_temp = get_spin_result(arr_result_FG_pre, pay_symbol_pre)
                cnt_eliminate += 1

                if pay_symbol_pre[0] != 99:
                    num_ww2c2 += num_ww2c2_temp

            #     print(f"\n--- eliminate {cnt_eliminate:02.00f} ---")
            #     print("* arr_result_FG_pre:\n", arr_result_FG_pre)

            # if cnt_eliminate > 0:
            #     print("")

            # re-trigger
            if free_spin_table_list.shape[0] < Box.max_spin_free_game:
                num_C1 = get_element_num_nxn(arr_result_FG_pre, [Box.C1])
                if num_C1 in Box.pay_table_C1_reteigger:
                    retrigger_table_list = table_set(value_freespin_table_choose_retrigger)
                    shuffle_inplace(retrigger_table_list)
                    free_spin_table_list = concatenate(free_spin_table_list, retrigger_table_list)
                    # print("* shuffle_inplace (retrigger):", free_spin_table_list, retrigger_table_list)
                    log_all(True, Box.RA_re_trigger, 1)

            # get multiplier
            mode_c2 = get_value(weight_cum_c2_FG)
            # print("* weight_cum_c2_FG:", weight_cum_c2_FG)
            multi_cum = 0
            num_C2 = get_element_num_nxn(arr_result_FG_pre, [Box.C2])

            # if num_C2 > 0:
            #     print("")

            if mode_c2 == 0:
                for i in range(num_C2 - num_ww2c2):
                    idx = get_value(weight_cum_c2_free_direct)
                    multi = Box.value_multiplier_range[int(idx)]
                    multi_cum += multi
                    # print("* multi C2 direct:", multi, multi_cum, num_C2, num_ww2c2)
                for i in range(num_ww2c2):
                    idx = get_value(weight_cum_c2_free_wild)
                    multi = Box.value_multiplier_range[int(idx)]
                    multi_cum += multi
                    # print("* multi WW to C2 :", multi, multi_cum, num_C2, num_ww2c2)
            if mode_c2 == 1:
                for i in range(num_C2):
                    idx = get_value(weight_cum_c2_super)
                    multi = Box.value_multiplier_range[int(idx)]
                    multi_cum += multi
                    # print("* multi C2 super:", multi, multi_cum)
            if mode_c2 == 2:
                for i in range(num_C2):
                    idx = get_value(weight_cum_c2_ultimate)
                    multi = Box.value_multiplier_range[int(idx)]
                    multi_cum += multi
                    # print("* multi C2 ultimate:", multi, multi_cum)

            # if num_C2 > 0:
            #     print("")

            # ---------------------------------------------------

            # calculate
            pay_sum = 0
            pay_base = 0
            if multi_cum == 0:  # 有C2且有得分才可以用倍數
                pay_base = calculate_win(Box.scence_FG, arr_result_FG, pay_symbol, 1)
            else:
                pay_base = calculate_win(Box.scence_FG, arr_result_FG, pay_symbol, cnt_multi_cum + multi_cum)
            pay_sum += pay_base

            # remove and fall
            remove_cnt = np.zeros(Box.reel_num[Box.scence_FG], np.int64)
            cnt = 0
            while True:
                if pay_symbol[0] == 99:
                    break
                remove_and_fall(table_id, rng_FS, arr_result_FG, pay_symbol, remove_cnt)
                if multi_cum == 0:  # 有`C2且有得分才可以用倍數
                    pay_base = calculate_win(Box.scence_FG, arr_result_FG, pay_symbol, 1)
                else:
                    pay_base = calculate_win(Box.scence_FG, arr_result_FG, pay_symbol, cnt_multi_cum + multi_cum)
                pay_sum += pay_base
                cnt += 1

            if pay_sum > 0:
                cnt_multi_cum += multi_cum

            pay_c1 = calculate_win_c1(Box.scence_FG, arr_result_FG)
            pay_sum += pay_c1
            num_c1 = get_element_num_nxn(arr_result_FG, [Box.C1])

            # ---------------------------------------------------

            # update
            pay_FG += pay_sum
            cnt_freespin += 1

            # record
            log_all(pay_sum > 0, Box.RA_hits_FG, 1)
            log_all(True, Box.RA_free_spins, 1)
            log_all(cnt_eliminate >= 5, Box.RA_eliminate_FG[0] + 5, 1)
            log_all(cnt_eliminate < 5, Box.RA_eliminate_FG[0] + cnt_eliminate, 1)

            log_all(num_c1 > 0, Box.RA_have_SC_FG, 1)
            log_all(num_c1 == 0, Box.RA_no_SC_FG, 1)

            num_c1_r3 = get_element_num_nxn(arr_result_FG[:, 2:], [Box.C1])
            if num_c1 == 3 and num_c1_r3 == 2 and table_id == 4:
                # print(arr_result_FG)
                log_all(True, Box.RA_else, 1)

            # print("\n* pay_FG:", pay_FG, "score(x):", pay_FG / coin_in)
        # record
        log_all(True, Box.RA_trigger_freegame, 1)

        return pay_FG

    # simulate n times
    for _ in range(total_round):

        total_win = 0  # 總得分

        # print(f"\n************** Spin {_+1:02.0f} **************\n")

        # base game
        pay_BG, pay_c1 = base_game()
        total_win += pay_BG
        total_win += pay_c1

        # free game
        pay_FG = 0
        if pay_c1 > 0:  # free game
            # if True:  # free game
            pay_FG = free_game()
            log_multi_line(Box.output_FG, pay_FG)
        else:
            log_multi_line(Box.output_BG, pay_BG)

        # print("\n====== final ======")
        # print("\n* pay_BG:", pay_BG, "score(x):", pay_BG / coin_in)
        # print("\n* pay_FG:", pay_FG, "score(x):", pay_FG / coin_in)

        total_win += pay_FG

        # 標準差
        log_all(True, Box.RA_x_sum, total_win / coin_in)  # x_sum
        log_all(True, Box.RA_x_square, (total_win / coin_in) ** 2)  # x_square

        # 倍率線型
        log_multi_line(Box.output_OA, total_win)
        log_all(pay_c1 > 0, Box.RA_trigger_FG_pay_BG, pay_BG)
        log_all(pay_c1 > 0, Box.RA_trigger_FG_pay_SC, pay_c1)

    return record_data


# make multi-thread
func_nb_mt = simulation.make_multi_thread(simulator_game, round=total_round, output_shape=Box.record_size)
record_data, durning = simulation.time_func("Duration: ", func_nb_mt)


# %% simulater Result


def simulater_result(show_result=False, show_detail=False, show_multi_line=False, output_data=False):

    def write_data(df, add_data_index="", add_data_value="", add_data_value2=""):
        idx = df.shape[0]
        df.loc[idx] = [add_data_index, add_data_value, add_data_value2]

    def get_multiplier_data(multiplier_data, threshold=Mat.threshold_record):

        df = pd.DataFrame()

        # interval
        threshold_str = []
        for i in range(0, len(threshold)):
            if i == 0:
                threshold_str.append("0")
            else:
                threshold_str.append(str(threshold[i - 1]) + " < X <= " + str(threshold[i]))

        df["Interval"] = threshold_str

        # data
        value_idx = [Box.R_multiplier_range_cnt_BG, Box.R_multiplier_range_pay_BG, Box.R_multiplier_range_cnt_FG, Box.R_multiplier_range_pay_FG]
        value_name = ["base_game_cnt", "base_game_pay", "free_game_cnt", "free_game_pay"]

        for i, idx in enumerate(value_idx):
            df[value_name[i]] = multiplier_data[idx, :].T

        return df

    if True:  # 資料準備
        # [show_result]
        rtp_BG_BS = record_data[Box.R_pay[0] : Box.R_pay[1], Box.symbols_score].sum() / coin_in / total_round
        rtp_BG_SC = record_data[Box.R_pay[0] : Box.R_pay[1], Box.C1].sum() / coin_in / total_round  # BG scatter pay
        rtp_FG_FS = record_data[Box.R_pay[0] : Box.R_pay[1], Box.symbols_score + len(Box.symbols_all)].sum() / coin_in / total_round
        hit_rate_BG = record_data[Box.R_all, Box.RA_hits_BG] / total_round
        hit_rate_FG = record_data[Box.R_all, Box.RA_hits_FG] / record_data[Box.R_all, Box.RA_free_spins]
        p_avg_spin_FG = record_data[Box.R_all, Box.RA_free_spins] / record_data[Box.R_all, Box.RA_trigger_freegame]
        p_trigger_FG = record_data[Box.R_all, Box.RA_trigger_freegame] / total_round
        p_retrigger = record_data[Box.R_all, Box.RA_re_trigger] / record_data[Box.R_all, Box.RA_trigger_freegame]
        avg_multi_FG = (rtp_FG_FS + rtp_BG_SC) / p_trigger_FG
        std = ((record_data[Box.R_all, Box.RA_x_square] - ((record_data[Box.R_all, Box.RA_x_sum]) ** 2 / total_round)) / total_round) ** 0.5
        median = Mat.threshold_record[Mat.cfunc.get_median_idx_from_multiplier_line(record_data[Box.R_multiplier_range_cnt_FG])]
        pay_trigger_FG_pay_BG = record_data[Box.R_all, Box.RA_trigger_FG_pay_BG]
        pay_trigger_FG_pay_SC = record_data[Box.R_all, Box.RA_trigger_FG_pay_SC]

        eliminate_BG = record_data[Box.R_all, Box.RA_eliminate_BG[0] : Box.RA_eliminate_BG[1]] / total_round
        eliminate_FG = record_data[Box.R_all, Box.RA_eliminate_FG[0] : Box.RA_eliminate_FG[1]] / record_data[Box.R_all, Box.RA_free_spins]

        have_SC_BG = record_data[Box.R_all, Box.RA_have_SC_BG]
        no_SC_BG = record_data[Box.R_all, Box.RA_no_SC_BG]
        have_SC_FG = record_data[Box.R_all, Box.RA_have_SC_FG]
        no_SC_FG = record_data[Box.R_all, Box.RA_no_SC_FG]

        # [show_detail]
        data_hits = record_data[Box.R_hits[0] : Box.R_hits[1], :].copy() / total_round
        data_rtp = record_data[Box.R_pay[0] : Box.R_pay[1], :].copy() / coin_in / total_round
        data_eliminate = record_data[Box.R_eliminate[0] : Box.R_eliminate[1], :].copy() / total_round
        data_eliminate[:, Box.symbols_count :] = data_eliminate[:, Box.symbols_count :] / record_data[Box.R_all, Box.RA_free_spins] * total_round

        # # [show_multi_line]
        data_multiplier_cnt_BG = Mat.cplot.map_multiplier_big2small_v2(Mat.threshold_v7, Mat.threshold_v7, record_data[Box.R_multiplier_range_cnt_BG])
        data_multiplier_cnt_FG = Mat.cplot.map_multiplier_big2small_v2(Mat.threshold_v7, Mat.threshold_v7, record_data[Box.R_multiplier_range_cnt_FG])
        data_multiplier_cnt_OA = Mat.cplot.map_multiplier_big2small_v2(Mat.threshold_v7, Mat.threshold_v7, record_data[Box.R_multiplier_range_cnt_OA])

    if True:  # 結果格式設定
        # [output_data]
        df_base = pd.DataFrame([], columns=["Index", "Value", "Value2"])
        f_write_data = lambda idx, v1, v2="": write_data(df_base, idx, v1, v2)

        print("coin_in: ", coin_in, "bet_mode: ", bet_mode, "total_round: ", format(total_round, ","))

        f_write_data("total round", format(total_round, ","))
        f_write_data("durning", "{0:0.2f}s".format(durning))
        f_write_data("RTP", "{0:0.5f}".format(rtp_BG_BS + rtp_BG_SC + rtp_FG_FS))
        f_write_data("RTP - base spin", "{0:0.5f}".format(rtp_BG_BS))
        f_write_data("RTP - scatter pay", "{0:0.5f}".format(rtp_BG_SC))
        f_write_data("RTP - free spin", "{0:0.5f}".format(rtp_FG_FS))
        f_write_data("hit rate - base spin", "{0:0.5f}".format(hit_rate_BG))
        f_write_data("hit rate - free spin", "{0:0.5f}".format(hit_rate_FG))
        f_write_data("免費遊戲觸發機率", "{0:0.5f}".format(p_trigger_FG), "{:0.2f}場".format(1 / p_trigger_FG))
        f_write_data("retrigger機率", "{0:0.5f}".format(p_retrigger), "{:0.2f}場".format(1 / p_retrigger))
        f_write_data("平均轉數", "{0:0.5f}".format(p_avg_spin_FG))
        f_write_data("平均倍數", "{0:0.2f}".format(avg_multi_FG))
        f_write_data("expected value", "{0:0.6f}".format(rtp_BG_BS + rtp_FG_FS))
        f_write_data("standard deviation", "{0:0.6f}".format(std))
        f_write_data("median", "{0:0.2f}".format(median))
        f_write_data("positive index", "{0:0.2f}".format(median / avg_multi_FG))
        f_write_data("觸發FG時BG的盤面得分", "{0}".format(pay_trigger_FG_pay_BG))
        f_write_data("觸發FG時BG的盤面SC得分", "{0}".format(pay_trigger_FG_pay_SC))
        f_write_data("SC Appear BG", "{0}".format(have_SC_BG))
        f_write_data("SC no Appear BG", "{0}".format(no_SC_BG))
        f_write_data("SC Appear FG", "{0}".format(have_SC_FG))
        f_write_data("SC no Appear FG", "{0}".format(no_SC_FG))
        # for i, x in enumerate(eliminate_BG):
        #     f_write_data(f"BG消除{i}次", "{0:0.2f}%".format(x * 100))
        # for i, x in enumerate(eliminate_FG):
        #     f_write_data(f"FG消除{i}次", "{0:0.2f}%".format(x * 100))
        f_write_data("else", "{0}".format(record_data[Box.R_all, Box.RA_else] / total_round))

        # [output_data] - detail (line game-hit rate, way game-combo)
        symbols_id = np.concatenate([Box.symbols_all, Box.symbols_all + Box.symbols_count])
        symbols_str = [Box.symbol_str[i] for i in Box.symbols_all] * 2

        df_hits = pd.DataFrame(data_hits[:, symbols_id], columns=symbols_str, index=[f"line * {i+1} - hits" for i in range(5)])
        df_rtp = pd.DataFrame(data_rtp[:, symbols_id], columns=symbols_str, index=[f"line * {i+1} - rtp" for i in range(5)])
        df_eliminate = pd.DataFrame(data_eliminate[:, symbols_id], columns=symbols_str, index=[f"line * {i+1} - eliminate" for i in range(5)])

    # show
    if show_result:  # 顯示結果

        div.div_center("simulate result - base info", lower=True)
        for i, data in enumerate(df_base.values):
            log_use.print_result2(data[0], data[1], data[2])

    if show_detail:  # 顯示細項

        div.div_center("simulate result - hits", upper=True, lower=True)
        print(df_hits)

        div.div_center("simulate result - rtp", upper=True, lower=True)
        print(df_rtp)

        # div.div_center("simulate result - combo", upper=True, lower=True)
        # print(df_combo)

    if show_multi_line:  # 顯示倍率線型

        div.div_center("simulate result - plot", upper=True, lower=True)

        name = Box.plot_name
        cplot.multiplier_line(data_multiplier_cnt_BG, threshold=Mat.threshold_show, title=name + "BG", ylim=0.05)
        cplot.multiplier_line(data_multiplier_cnt_FG, Mat.threshold_show, name + "FG", ylim=0.25)
        cplot.multiplier_line(data_multiplier_cnt_OA, Mat.threshold_show, name + "OA", ylim=0.15)

    if output_data:  # 輸出資料

        df_detail = pd.concat([df_hits, df_rtp, df_eliminate], axis=0)
        df_detail.reset_index(inplace=True)
        df_output = pd.concat([df_base, df_detail], axis=1)

        df_multiplier = get_multiplier_data(record_data, Mat.threshold_record)
        df_record_data = pd.DataFrame(record_data)

        with pd.ExcelWriter(Box.path_output_data(f"_betmode{bet_mode}")) as writer:
            df_output.to_excel(writer, sheet_name="Base Info", index=False)
            df_multiplier.to_excel(writer, sheet_name="Multiplier Line", index=False)
            df_record_data.to_excel(writer, sheet_name="Record Data", index=False)


record_data = record_data.astype(np.float64)
simulater_result(True, False, False, True)
# simulater_result(False, False, False, False)

# %%
