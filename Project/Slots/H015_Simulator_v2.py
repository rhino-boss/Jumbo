# %% Import


import numpy as np
import pandas as pd
from numba import jit, njit
import math
import os

os.chdir("C:\\Users\\rhinshen\\Mine\\個人工作區\\2_Program")

# my package
import Project.Slots.Source.H015_Box as Box

import Project.Slots.Source.General.Math as Mat
from Project.Slots.Source.General.Math import simulation, cplot
from Project.Slots.Source.General.RedBox import div, log_use

# %% Setting


bet_multi = 1  # bet multiplier
bet_mode = Box.mode_normalbet
# bet_mode = Box.mode_featurebuy
# bet_mode = Box.mode_superfeaturebuy

total_round = 10**9  # 測試1
# total_round = 10**4  # 測試2
# total_round = 10**0  # 測試3
# total_round = 10**9  # 標準，時間: s


# %% Initial


# coin in
if bet_mode == Box.mode_normalbet:
    coin_in = bet_multi * Box.default_coin_in * Box.normalbet
elif bet_mode == Box.mode_featurebuy:
    coin_in = bet_multi * Box.default_coin_in * Box.normalbet * Box.featurebuy

# setting


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

    def check_appear(arr, check_item):
        """
        檢查"check_item"內的元素有沒有在"arr"中出現過
        """
        arr_shape = arr.shape
        for i in range(arr_shape[0]):
            for j in range(arr_shape[1]):
                if arr[i, j] == check_item:
                    return True, (i, j)
        return False, (-1, -1)

    def get_element_num_nxn(arr, elemets):
        cnt = 0
        for i in range(arr.shape[0]):
            for j in range(arr.shape[1]):
                for e in elemets:
                    if arr[i, j] == e:
                        cnt += 1
        return cnt

    def check_appear_reel(arr, check_item):
        arr_shape = arr.shape
        list_appear_posi = []
        for i in range(arr_shape[0]):
            for j in range(arr_shape[1]):
                if arr[i, j] == check_item:
                    list_appear_posi.append((i, j))
        return list_appear_posi

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

    # initial setting
    rng = np.zeros(Box.reel_num, np.int64)
    arr_result = np.zeros(Box.layout_shape, np.int64)

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
        elif game_scence == 1:
            cnt_idx = Box.R_multiplier_range_cnt_FG
            pay_idx = Box.R_multiplier_range_pay_FG
        elif game_scence == 2:
            cnt_idx = Box.R_multiplier_range_cnt_OA
            pay_idx = Box.R_multiplier_range_pay_OA

        multi = score / Box.default_coin_in
        for i in range(Box.threshold_record.shape[0] - 1):

            if multi <= Box.threshold_record[i]:
                record_data[cnt_idx][i] += 1
                record_data[pay_idx][i] += score
                break

            elif Box.threshold_record[i] < multi and multi <= Box.threshold_record[i + 1]:
                record_data[cnt_idx][i + 1] += 1
                record_data[pay_idx][i + 1] += score
                break

    def log_all(condition, idx, v):
        if condition:
            record_data[Box.R_all, idx] += v

    def log_hit_way(symbol, line, way, posi_y_fix):  # 每個獎項的hit
        idx = line - 1
        record_data[Box.R_hits[0] : Box.R_hits[1], :][idx, symbol + len(Box.symbols_all) * posi_y_fix] += way  # posi_y_fix: 0->BG, 1->FG

    def log_pay(symbol, line, pay, posi_y_fix):  # 每個獎項的pay
        idx = line - 1
        record_data[Box.R_pay[0] : Box.R_pay[1], :][idx, symbol + len(Box.symbols_all) * posi_y_fix] += pay  # posi_y_fix: 0->BG, 1->FG

    def log_eliminate_way(symbol, line, way, posi_y_fix):  # 每個獎項的hit
        idx = line - 1
        record_data[Box.R_eliminate[0] : Box.R_eliminate[1], :][idx, symbol + len(Box.symbols_all) * posi_y_fix] += way  # posi_y_fix: 0->BG, 1->FG

    # tool - bygame
    # H015 v2 沒有獨立的「炸彈 symbol / 爆炸函式」。
    # 特殊演出實際由兩段機制組成：
    # 1. 金框符號在參與得分消除後，不會直接重抽，而是轉成 Wild。
    # 2. 每次 cascade 另外抽選「閃電數量」，用來推進整局乘數等級。
    def arr_result_generator_C(table_id, rng_C, arr_result_C):
        window_size, reel_num = arr_result_C.shape

        # generator rng
        for i in range(reel_num):
            ll = Box.reels_len[int(table_id), i]
            arr_reels_weight = Box.arr_reels_weight[int(table_id), :ll, i]
            use_reel_weight = np.cumsum(arr_reels_weight)
            rng_C[i] = get_value(use_reel_weight)

        # generator arr_result
        for i in range(window_size):
            for j in range(reel_num):
                use_reel = Box.arr_reels[int(table_id), :, j]
                use_reel_len = Box.reels_len[int(table_id), j]
                arr_result_C[i, j] = use_reel[(rng_C[j] + i) % use_reel_len]

    def set_calculate_area_C(arr_result_C):
        for i in range(arr_result_C.shape[0]):
            for j in range(arr_result_C.shape[1]):
                if Box.score_area[i, j] == 0:
                    arr_result_C[i, j] = 99  # 0:不消除, 1:消除, 2:轉WW, 99:不計算區域

    def set_golden_flame_area_C(arr_result_C, arr_golden_symbol_posi_C):
        # 金框符號先轉回一般 symbol 參與 ways 計算，位置另外用 mask 記錄。
        # 後續若該格被命中，remove_and_fall_C 會把它轉成 Wild，而不是直接消失補牌。
        for i in range(arr_result_C.shape[0]):
            for j in range(arr_result_C.shape[1]):
                if arr_result_C[i, j] in Box.symbols_gold:
                    arr_result_C[i, j] -= 8  # 轉成一般符號
                    arr_golden_symbol_posi_C[i, j] = 1

    def get_pay(symbol, line):

        pay = 0
        # if symbol == Box.C1 and line in Box.pay_table:
        #     pay = Box.pay_table[Box.C1][line - 4] * bet_multi

        if symbol in Box.symbols_score and line >= 3:
            pay = Box.pay_table[symbol][line - 3] * bet_multi

        return pay

    def get_spin_result(arr_result, arr_special_posi, arr_golden_symbol_posi):
        # arr_special_posi:
        # 0  -> 一般可計算位置，這輪未命中
        # 1  -> 一般命中格，本輪消除後會依掉落表補新 symbol
        # 2  -> 金框命中格，本輪不重抽，落下後改成 Wild
        # 99 -> 不在有效盤面內

        # initial setting
        arr_pay_symbol = np.full(3, 99, np.int64)
        arr_pay_way_cnt = np.full(3, 99, np.int64)
        arr_pay_line = np.full(3, 99, np.int64)
        arr_pay_symbol_pay = np.full(3, 99, np.int64)

        arr_special_posi_copy = arr_special_posi.copy()
        calculate_symbols = []
        for symbol in arr_result[:, 0]:
            if symbol != 99 and symbol not in calculate_symbols:
                calculate_symbols.append(symbol)

        pay_symbol_sum = 0
        for idx, symbol in enumerate(calculate_symbols):
            if symbol == 99:
                continue

            line = 0
            way_multi = 1
            for reel in range(Box.reel_num):
                cnt_target_symbol = 0
                for window in range(Box.window_size):
                    if arr_result[window, reel] == symbol or arr_result[window, reel] == Box.WW:
                        cnt_target_symbol += 1

                if cnt_target_symbol == 0:
                    break

                line += 1
                way_multi *= cnt_target_symbol

            pay_symbol = int(get_pay(symbol, line))
            pay_symbol_sum += pay_symbol * way_multi
            # print("* symbol: ", symbol, "line_idx: ", line, "pay: ", pay_symbol, "way_multi: ", way_multi, "win", pay_symbol * way_multi)

            # update
            arr_pay_symbol[idx] = symbol
            arr_pay_way_cnt[idx] = way_multi
            arr_pay_line[idx] = line
            arr_pay_symbol_pay[idx] = pay_symbol

            if pay_symbol > 0:
                # arr_cascade_posi_copy 標記消除位置
                for reel in range(line):
                    for window in range(Box.window_size):
                        if arr_special_posi_copy[window, reel] != 99 and (symbol == arr_result[window, reel] or arr_result[window, reel] == Box.WW):
                            if arr_golden_symbol_posi[window, reel] == 1:
                                arr_special_posi_copy[window, reel] = 2  # 標記黃金符號
                            else:
                                arr_special_posi_copy[window, reel] = 1  # 標記消除

        # update
        copy_array(arr_special_posi_copy, arr_special_posi)

        # return pay_symbol_sum
        return pay_symbol_sum, arr_pay_symbol, arr_pay_way_cnt, arr_pay_line, arr_pay_symbol_pay

    def remove_and_fall_C(table_id, combo_id, arr_result, arr_special_posi, arr_golden_symbol_posi, weight_drop_choose):
        # 一般命中格直接依 combo 掉落表補牌；
        # 金框命中格則保留為特效格，結算後轉成 Wild，形成下一段 cascade 的延續價值。
        for window in range(arr_result.shape[0]):
            for reel in range(arr_result.shape[1]):
                if arr_special_posi[window, reel] == 1:
                    arr_result[window, reel] = get_value(weight_drop_choose[int(table_id), combo_id, :, reel])
                elif arr_special_posi[window, reel] == 2:
                    arr_result[window, reel] = Box.WW  # 黃金符號掉落後變一般符號
                    arr_golden_symbol_posi[window, reel] = 0  # 黃金符號掉落後清除標記

    def get_multi_idx(multi_lv_idx, add):
        multi_lv_idx += add
        if multi_lv_idx >= 10:
            multi_lv_idx = 10

        return multi_lv_idx

    # main
    def base_game(log):  # log
        """
        遊戲流程
        1. 產生RNG、初始畫面
        2. 轉換金框符號Idx
        3. 決定掉落表與閃電出現表
        --- 進入circle ---
        4. 抽選幾個閃電（不是炸彈位置，而是本段 cascade 增加幾階乘數）
        5. 計算得分
        6. 消除並掉落新符號
        7. 轉換金框符號
        """

        # print("\n======== Base Game ========")

        # initial setting
        arr_golden_symbol_posi = np.array(
            [
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [99, 0, 0, 0, 0, 99],
                [99, 99, 0, 0, 99, 99],
            ],
            np.int64,
        )

        # spin
        table_id = 0
        if bet_mode == Box.mode_normalbet:
            table_id = get_value(Box.weight_cum_table_BG)
        elif bet_mode == Box.mode_featurebuy:
            table_id = Box.strip_BF

        arr_result_generator_C(table_id, rng, arr_result)
        set_calculate_area_C(arr_result)
        set_golden_flame_area_C(arr_result, arr_golden_symbol_posi)

        # print("\narr_result:\n", arr_result)
        # print("\narr_golden_symbol_posi:\n", arr_golden_symbol_posi)

        # 決定使用的掉落表
        drop_idx = get_value(Box.weight_cum_drop_choose_bg)
        weight_drop_choose = Box.weight_cum_drop_symbol_A
        if drop_idx == 1:
            weight_drop_choose = Box.weight_cum_drop_symbol_B
        elif drop_idx == 2:
            weight_drop_choose = Box.weight_cum_drop_symbol_C

        # 決定出現幾個閃電的表
        multi_appear_idx = table_id * 3 + drop_idx
        if bet_mode == Box.mode_featurebuy:
            multi_appear_idx = 0 + int(drop_idx)

        combo_idx = 0
        multi_lv_idx = 0
        pay_BS = 0
        pay_cascade = 99
        TF_lighting_hit_and_use = False
        while pay_cascade > 0:

            # initial setting
            arr_special_posi = np.array(
                [
                    [0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0],
                    [99, 0, 0, 0, 0, 99],
                    [99, 99, 0, 0, 99, 99],
                ],
                np.int64,
            )

            # 抽選這次要出現幾個閃電
            weight_multi_appear = 0
            if multi_lv_idx <= 4:
                weight_multi_appear = Box.weight_cum_multi_appear_bg[multi_lv_idx, :, multi_appear_idx]
            else:
                weight_multi_appear = Box.weight_cum_multi_appear_bg[4, :, multi_appear_idx]
            num_multi_appear = get_value(weight_multi_appear)  # 決定本次出現幾個閃電

            # cascade
            pay_cascade, arr_pay_symbol, arr_pay_way_cnt, arr_pay_line, arr_pay_symbol_pay = get_spin_result(arr_result, arr_special_posi, arr_golden_symbol_posi)
            if combo_idx < 3:
                remove_and_fall_C(table_id, combo_idx, arr_result, arr_special_posi, arr_golden_symbol_posi, weight_drop_choose)
            else:
                remove_and_fall_C(table_id, 3, arr_result, arr_special_posi, arr_golden_symbol_posi, weight_drop_choose)
            set_golden_flame_area_C(arr_result, arr_golden_symbol_posi)

            # update
            multi_lv_idx = get_multi_idx(multi_lv_idx, num_multi_appear)  # 更新閃電
            multi_value = Box.value_multiplier_range[multi_lv_idx]
            multi_lv_idx = get_multi_idx(multi_lv_idx, 1)  # 更新消除累積倍數
            combo_idx += 1
            # 本段實際乘數 =「閃電推進後的等級」對應到的 multiplier value。

            pay_BS += pay_cascade * multi_value
            if num_multi_appear > 0 and pay_cascade * multi_value > 0:
                TF_lighting_hit_and_use = True

            # record
            if log:
                for idx, symbol in enumerate(arr_pay_symbol):
                    if symbol != 99 and arr_pay_symbol_pay[idx] > 0:
                        log_pay(symbol, arr_pay_line[idx], arr_pay_symbol_pay[idx] * arr_pay_way_cnt[idx] * multi_value, 0)
                        if combo_idx == 1:
                            log_hit_way(symbol, arr_pay_line[idx], arr_pay_way_cnt[idx], 0)  # posi_y_fix: 0:BG, 1:FG
                        else:
                            log_eliminate_way(symbol, arr_pay_line[idx], arr_pay_way_cnt[idx], 0)

        num_c1 = get_element_num_nxn(arr_result, [Box.C1])

        # record
        if log:
            log_all(pay_BS > 0, Box.RA_hits_BG, 1)
            log_all(combo_idx - 1 >= 8, Box.RA_eliminate_BG[0] + 3, 1)
            log_all(combo_idx - 1 < 8, Box.RA_eliminate_BG[0] + combo_idx - 1, 1)
            log_all(TF_lighting_hit_and_use, Box.RA_lighting_used_BG, 1)

        return pay_BS, num_c1

    def free_game(num_c1_bg):  # log
        """
        遊戲流程
        """
        must_hit_lighting = get_value(Box.weight_must_appear_1_fg)
        pay_FG = 0
        free_spins = 10 + (num_c1_bg - 3) * 2
        cnt_freespin = 0
        while True:
            if cnt_freespin >= free_spins or cnt_freespin >= Box.max_spin_free_game:
                # print(cnt_freespin, free_spins)
                break

            # print("\n--------- Free Spin:", cnt_freespin + 1, " / ", free_spins, " ---------")
            # initial setting
            arr_golden_symbol_posi = np.array(
                [
                    [0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0],
                    [99, 0, 0, 0, 0, 99],
                    [99, 99, 0, 0, 99, 99],
                ],
                np.int64,
            )

            # free spin
            table_id = 0
            if bet_mode == Box.mode_normalbet:
                table_id = get_value(Box.weight_cum_table_FG) + 2
            elif bet_mode == Box.mode_featurebuy:
                table_id = get_value(Box.weight_cum_table_BF) + 2

            arr_result_generator_C(table_id, rng, arr_result)
            set_calculate_area_C(arr_result)
            set_golden_flame_area_C(arr_result, arr_golden_symbol_posi)

            # print("\narr_result:\n", arr_result)

            # 決定使用的掉落表
            drop_idx = get_value(Box.weight_cum_drop_choose_fg)
            weight_drop_choose = Box.weight_cum_drop_symbol_A
            if drop_idx == 1:
                weight_drop_choose = Box.weight_cum_drop_symbol_B
            elif drop_idx == 2:
                weight_drop_choose = Box.weight_cum_drop_symbol_C
            # print(drop_idx)

            # 決定出現幾個閃電的表
            multi_appear_idx = (table_id - 2) * 3 + drop_idx

            combo_idx = 0
            multi_lv_idx = 3  # free game固定從combo 3開始
            pay_FS = 0
            pay_cascade = 99
            TF_lighting_hit = False
            TF_lighting_hit_and_use = False
            while pay_cascade > 0:

                # print("\n--- combo:", combo_idx, "---")
                # initial setting
                arr_special_posi = np.array(
                    [
                        [0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0],
                        [99, 0, 0, 0, 0, 99],
                        [99, 99, 0, 0, 99, 99],
                    ],
                    np.int64,
                )

                # 抽選這次要出現幾個閃電
                weight_multi_appear = 0
                if multi_lv_idx - 3 <= 4:
                    weight_multi_appear = Box.weight_cum_multi_appear_fg[multi_lv_idx - 3, :, multi_appear_idx]
                else:
                    weight_multi_appear = Box.weight_cum_multi_appear_fg[4, :, multi_appear_idx]

                num_multi_appear = get_value(weight_multi_appear)  # 決定本次出現幾個閃電
                if num_multi_appear > 0:
                    TF_lighting_hit = True

                # cascade
                pay_cascade, arr_pay_symbol, arr_pay_way_cnt, arr_pay_line, arr_pay_symbol_pay = get_spin_result(arr_result, arr_special_posi, arr_golden_symbol_posi)
                if combo_idx < 3:
                    remove_and_fall_C(table_id, combo_idx, arr_result, arr_special_posi, arr_golden_symbol_posi, weight_drop_choose)
                else:
                    remove_and_fall_C(table_id, 3, arr_result, arr_special_posi, arr_golden_symbol_posi, weight_drop_choose)
                set_golden_flame_area_C(arr_result, arr_golden_symbol_posi)

                # update
                if combo_idx == 0 and must_hit_lighting == cnt_freespin + 1 and TF_lighting_hit == False:  # 第一消且沒有出現過閃電，強制出現1個
                    multi_lv_idx = get_multi_idx(multi_lv_idx, 1)  # 更新閃電
                else:
                    multi_lv_idx = get_multi_idx(multi_lv_idx, num_multi_appear)  # 更新閃電

                multi_value = Box.value_multiplier_range[multi_lv_idx]
                multi_lv_idx = get_multi_idx(multi_lv_idx, 1)  # 更新消除累積倍數
                combo_idx += 1

                pay_FS += pay_cascade * multi_value
                if num_multi_appear > 0 and pay_cascade * multi_value > 0:
                    TF_lighting_hit_and_use = True

                # log
                for idx, symbol in enumerate(arr_pay_symbol):
                    if symbol != 99 and arr_pay_symbol_pay[idx] > 0:
                        log_pay(symbol, arr_pay_line[idx], arr_pay_symbol_pay[idx] * arr_pay_way_cnt[idx] * multi_value, 1)
                        if combo_idx == 1:
                            log_hit_way(symbol, arr_pay_line[idx], arr_pay_way_cnt[idx], 1)  # posi_y_fix: 0:BG, 1:FG
                        else:
                            log_eliminate_way(symbol, arr_pay_line[idx], arr_pay_way_cnt[idx], 1)

                # print("\narr_pay_symbol:", arr_pay_symbol)
                # print("arr_pay_line:", arr_pay_line)
                # print("arr_pay_way_cnt:", arr_pay_way_cnt)
                # print("arr_pay_symbol_pay:", arr_pay_symbol_pay)
                # print("\narr_result:\n", arr_result)
                # print("\npay_cascade", pay_cascade, "multi_lv_idx:", multi_lv_idx, "num_multi_appear:", num_multi_appear)

            # re-trigger
            num_c1_fg = get_element_num_nxn(arr_result, [Box.C1])
            if num_c1_fg >= 3:
                free_spins += 10 + (num_c1_fg - 3) * 2
                log_all(1, Box.RA_re_trigger, 1)

            # update
            # print("+++ pay_FS: ", pay_FS)
            pay_FG += pay_FS
            cnt_freespin += 1

            # record
            log_all(pay_FS > 0, Box.RA_hits_FG, 1)
            log_all(True, Box.RA_free_spins, 1)
            log_all(combo_idx - 1 >= 3, Box.RA_eliminate_FG[0] + 3, 1)
            log_all(combo_idx - 1 < 3, Box.RA_eliminate_FG[0] + combo_idx - 1, 1)
            log_all(TF_lighting_hit_and_use, Box.RA_lighting_used_FG, 1)

        # record
        log_all(True, Box.RA_trigger_freegame, 1)

        # return 0
        return pay_FG

    # simulate n times
    for _ in range(total_round):

        pay_total = 0  # 總得分

        # base game
        pay_BS, num_c1 = base_game(True)
        if num_c1 >= 3:
            TF_FG = True
            while TF_FG or (pay_BS / coin_in > 5000):
                pay_BS, num_c1 = base_game(False)
                TF_FG = num_c1 < 3

        # free game
        pay_FG = 0
        if num_c1 >= 3:  # free game
            pay_FG = free_game(num_c1)
            log_all(True, Box.RA_trigger_FG_pay_BG, pay_BS)
            log_multi_line(Box.output_FG, pay_FG)
            # else:
            log_multi_line(Box.output_BG, pay_BS)

        pay_total += pay_BS + pay_FG

        # 標準差
        log_all(True, Box.RA_x_sum, pay_total / coin_in)  # x_sum
        log_all(True, Box.RA_x_square, (pay_total / coin_in) ** 2)  # x_square

        # 倍率線型
        log_multi_line(Box.output_OA, pay_total)

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
        rtp_FG_FS = record_data[Box.R_pay[0] : Box.R_pay[1], Box.symbols_score + len(Box.symbols_all)].sum() / coin_in / total_round
        hit_rate_BG = record_data[Box.R_all, Box.RA_hits_BG] / total_round
        hit_rate_FG = record_data[Box.R_all, Box.RA_hits_FG] / record_data[Box.R_all, Box.RA_free_spins]
        p_avg_spin_FG = record_data[Box.R_all, Box.RA_free_spins] / record_data[Box.R_all, Box.RA_trigger_freegame]
        p_trigger_FG = record_data[Box.R_all, Box.RA_trigger_freegame] / total_round
        p_retrigger = record_data[Box.R_all, Box.RA_re_trigger] / record_data[Box.R_all, Box.RA_trigger_freegame]
        avg_multi_FG = rtp_FG_FS / p_trigger_FG
        avg_multi_per_free_spin = rtp_FG_FS / (record_data[Box.R_all, Box.RA_free_spins] / total_round)
        std = ((record_data[Box.R_all, Box.RA_x_square] - ((record_data[Box.R_all, Box.RA_x_sum]) ** 2 / total_round)) / total_round) ** 0.5
        median = Mat.threshold_record[Mat.cfunc.get_median_idx_from_multiplier_line(record_data[Box.R_multiplier_range_cnt_FG])]
        pay_trigger_FG_pay_BG = record_data[Box.R_all, Box.RA_trigger_FG_pay_BG]

        eliminate_BG = record_data[Box.R_all, Box.RA_eliminate_BG[0] : Box.RA_eliminate_BG[1]] / total_round
        eliminate_FG = record_data[Box.R_all, Box.RA_eliminate_FG[0] : Box.RA_eliminate_FG[1]] / record_data[Box.R_all, Box.RA_free_spins]
        lighting_hit_rate_BG = record_data[Box.R_all, Box.RA_lighting_used_BG] / total_round
        lighting_hit_rate_FG = record_data[Box.R_all, Box.RA_lighting_used_FG] / record_data[Box.R_all, Box.RA_free_spins]

        # [show_detail]
        data_hits = record_data[Box.R_hits[0] : Box.R_hits[1], :].copy() / total_round
        data_hits[:, Box.symbols_count :] = data_hits[:, Box.symbols_count :] / record_data[Box.R_all, Box.RA_free_spins] * total_round
        data_rtp = record_data[Box.R_pay[0] : Box.R_pay[1], :].copy() / coin_in / total_round
        data_eliminate = record_data[Box.R_eliminate[0] : Box.R_eliminate[1], :].copy() / total_round
        data_eliminate[:, Box.symbols_count :] = data_eliminate[:, Box.symbols_count :] / record_data[Box.R_all, Box.RA_free_spins] * total_round

        # [show_multi_line]
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
        f_write_data("RTP", "{0:0.5f}".format(rtp_BG_BS + rtp_FG_FS))
        f_write_data("RTP - base spin", "{0:0.5f}".format(rtp_BG_BS))
        f_write_data("RTP - free spin", "{0:0.5f}".format(rtp_FG_FS))
        f_write_data("hit rate - base spin", "{0:0.5f}".format(hit_rate_BG))
        f_write_data("hit rate - free spin", "{0:0.5f}".format(hit_rate_FG))
        f_write_data("免費遊戲觸發機率", "{0:0.5f}".format(p_trigger_FG), "{:0.2f}場".format(1 / p_trigger_FG))
        f_write_data("免費遊戲再觸發機率", "{0:0.5f}".format(p_retrigger), "{:0.2f}場".format(1 / p_retrigger))
        f_write_data("FG平均轉數", "{0:0.5f}".format(p_avg_spin_FG))
        f_write_data("FG平均倍數", "{0:0.2f}".format(avg_multi_FG))
        f_write_data("每把FG平均倍數", "{0:0.2f}".format(avg_multi_per_free_spin))
        f_write_data("expected value", "{0:0.6f}".format(rtp_BG_BS + rtp_FG_FS))
        f_write_data("standard deviation", "{0:0.6f}".format(std))
        f_write_data("median", "{0:0.2f}".format(median))
        f_write_data("positive index", "{0:0.2f}".format(median / avg_multi_FG))
        f_write_data("觸發FG時BG的盤面得分", "{0}".format(pay_trigger_FG_pay_BG), pay_trigger_FG_pay_BG / total_round / 100 / p_trigger_FG)
        f_write_data("Lighting使用率 - base spin", "{0:0.2f}%".format(lighting_hit_rate_BG * 100))
        f_write_data("Lighting使用率 - free spin", "{0:0.2f}%".format(lighting_hit_rate_FG * 100))

        for i, x in enumerate(eliminate_BG):
            f_write_data(f"BG消除{i}次", "{0:0.2f}%".format(x * 100))
        for i, x in enumerate(eliminate_FG):
            f_write_data(f"FG消除{i}次", "{0:0.2f}%".format(x * 100))

        # [output_data] - detail (line game-hit rate, way game-combo)
        symbols_id = np.concatenate([Box.symbols_score, Box.symbols_score + Box.symbols_count])
        symbols_str = [Box.symbol_str[i] for i in Box.symbols_score] * 2

        df_hits = pd.DataFrame(data_hits[:, symbols_id], columns=symbols_str, index=[f"line * {i+1} - hits" for i in range(6)])
        df_rtp = pd.DataFrame(data_rtp[:, symbols_id], columns=symbols_str, index=[f"line * {i+1} - rtp" for i in range(6)])
        df_eliminate = pd.DataFrame(data_eliminate[:, symbols_id], columns=symbols_str, index=[f"line * {i+1} - eliminate" for i in range(6)])

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

        div.div_center("simulate result - eliminate", upper=True, lower=True)
        print(df_eliminate)

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
# simulater_result(True, True, False, False)
simulater_result(True, False, False, True)


# %%
