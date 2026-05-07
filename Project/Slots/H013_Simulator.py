# %% Import

import numpy as np
import pandas as pd
from numba import jit, njit
import math
import os

os.chdir("C:\\Users\\rhinshen\\Mine\\個人工作區\\2_Program")

# my package
import Project.Slots.Source.H013_Box as Box

import Project.Slots.Source.General.Math as Mat
from Project.Slots.Source.General.Math import simulation, cplot
from Project.Slots.Source.General.RedBox import div, log_use


# %% Setting

bet_multi = 1  # bet multiplier
bet_mode = Box.mode_narmalbet
# bet_mode = Box.mode_extrabet
# bet_mode = Box.mode_featurebuy
# bet_mode = Box.mode_superfeaturebuy

total_round = 10**6  # 測試
total_round = 10**2  # 測試
# total_round = 10**9  # 標準，時間: s
# total_round = 10**10  # 大場次，時間: s


# %% Initial

# coin in
if bet_mode == Box.mode_narmalbet:
    coin_in = bet_multi * Box.default_coin_in * Box.normalbet
elif bet_mode == Box.mode_extrabet:
    coin_in = bet_multi * Box.default_coin_in * Box.extrabet
elif bet_mode == Box.mode_featurebuy:
    coin_in = bet_multi * Box.default_coin_in * Box.normalbet * Box.featurebuy
elif bet_mode == Box.mode_superfeaturebuy:
    coin_in = bet_multi * Box.default_coin_in * Box.normalbet * Box.superfeaturebuy

# strip
if bet_mode == Box.mode_narmalbet:
    strip_B1, strip_B2, strip_B3 = Box.strip_BG, Box.strip_BG2, Box.strip_BG3
    strip_F1, strip_F2 = Box.strip_FG, Box.strip_FG2
elif bet_mode == Box.mode_extrabet:
    strip_B1, strip_B2, strip_B3 = Box.strip_EB, Box.strip_EB2, Box.strip_EB3
    strip_F1, strip_F2 = Box.strip_FG, Box.strip_FG2
elif bet_mode == Box.mode_featurebuy:
    strip_B1, strip_B2, strip_B3 = Box.strip_BG, Box.strip_BG2, Box.strip_BG3
    strip_F1, strip_F2 = Box.strip_FB, Box.strip_FB2
elif bet_mode == Box.mode_superfeaturebuy:
    strip_B1, strip_B2, strip_B3 = Box.strip_BG, Box.strip_BG2, Box.strip_BG3
    strip_F1, strip_F2 = Box.strip_SB, Box.strip_SB2

# table
if bet_mode == Box.mode_narmalbet or bet_mode == Box.mode_featurebuy or bet_mode == Box.mode_superfeaturebuy:
    weight_table, weigh_table_cum = Box.weight_table_normal_bet, Box.weight_cum_table_normal_bet
elif bet_mode == Box.mode_extrabet:
    weight_table, weigh_table_cum = Box.weight_table_extra_bet, Box.weight_cum_table_extra_bet

# multiplier range
if bet_mode == Box.mode_narmalbet or bet_mode == Box.mode_extrabet:
    weight_multiplier_range_low, weigh_multiplier_range_low_cum = Box.weight_table_multiplier_range_FG_low, Box.weight_cum_table_multiplier_range_FG_low
    weight_multiplier_range_high, weigh_multiplier_range_high_cum = Box.weight_table_multiplier_range_FG_high, Box.weight_cum_table_multiplier_range_FG_high
elif bet_mode == Box.mode_featurebuy:
    weight_multiplier_range_low, weigh_multiplier_range_low_cum = Box.weight_table_multiplier_range_FB_low, Box.weight_cum_table_multiplier_range_FB_low
    weight_multiplier_range_high, weigh_multiplier_range_high_cum = Box.weight_table_multiplier_range_FB_high, Box.weight_cum_table_multiplier_range_FB_high
elif bet_mode == Box.mode_superfeaturebuy:
    weight_multiplier_range_low, weigh_multiplier_range_low_cum = Box.weight_table_multiplier_range_SB_low, Box.weight_cum_table_multiplier_range_SB_low
    weight_multiplier_range_high, weigh_multiplier_range_high_cum = Box.weight_table_multiplier_range_SB_high, Box.weight_cum_table_multiplier_range_SB_high


# low, high
if bet_mode == Box.mode_narmalbet or bet_mode == Box.mode_extrabet:
    N_low = 8
    N_high = 2
elif bet_mode == Box.mode_featurebuy:
    N_low = 8
    N_high = 2
elif bet_mode == Box.mode_superfeaturebuy:
    N_low = 8
    N_high = 2

print("coin_in: ", coin_in, "bet_mode: ", bet_mode, "total_round: ", format(total_round, ","))
print("weight_table: ", weight_table)
print("weight_multiplier_range_low: ", weight_multiplier_range_low)
print("weight_multiplier_range_high: ", weight_multiplier_range_high)
print(N_low, N_high)


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

    def get_element_num_nxn(arr, elemet):
        cnt = 0
        for i in range(arr.shape[0]):
            for j in range(arr.shape[1]):
                if elemet == arr[i, j]:
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

    # pre-setting
    rng_BS = np.zeros(Box.reel_num[Box.scence_BG], np.int64)
    arr_result_BG = np.zeros((Box.window_size[Box.scence_BG], Box.reel_num[Box.scence_BG]), np.int64)

    rng_FS = np.zeros(Box.reel_num[Box.scence_FG], np.int64)
    arr_result_FG = np.zeros((Box.window_size[Box.scence_FG], Box.reel_num[Box.scence_FG]), np.int64)
    arr_result_FG_pre = arr_result_FG.copy()

    # log
    def log_multi_line(game_scence, score):  # 倍率線型
        """
        倍率線型紀錄
        """
        idx = 1
        if game_scence == 0:
            idx = Box.R_multiplier_range_cnt_BG
        elif game_scence == 1:
            idx = Box.R_multiplier_range_cnt_FG
        elif game_scence == 2:
            idx = Box.R_multiplier_range_cnt_OA

        multi = score / coin_in
        for i in range(Box.threshold_record.shape[0] - 1):

            if multi <= Box.threshold_record[i]:
                record_data[idx][i] += 1
                break

            elif Box.threshold_record[i] < multi and multi <= Box.threshold_record[i + 1]:
                record_data[idx][i + 1] += 1
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
                # print("line: ", line, "symbol: ", symbol)

    # tool - bygame
    def arr_result_generator(table_id, rng, arr_result, n):

        window_size, reel_num = arr_result.shape

        # generator rng
        for i in range(reel_num):
            ll = Box.reels_len[int(table_id), i]
            arr_reels_weight = Box.arr_reels_weight[int(table_id), :ll, i]
            use_reel_weight = np.cumsum(arr_reels_weight)
            rng[i] = get_value(use_reel_weight)
            # rng[i] = np.random.randint(Box.reels_len[int(table_id), i])
            # if table_id in [7, 8, 9, 10]:
            #     print(ll)
            # print()

        # if n != -1:
        #     if table_id in [9, 10]:
        #         script = np.array(
        #             [
        #                 [29, 27, 72, 62, 8, 75],
        #                 [89, 103, 16, 104, 20, 78],
        #                 [89, 10, 90, 89, 10, 76],
        #                 [59, 79, 47, 92, 36, 16],
        #                 [15, 61, 5, 10, 89, 4],
        #                 [1, 100, 75, 87, 84, 95],
        #                 [105, 82, 51, 14, 23, 69],
        #                 [18, 31, 75, 90, 80, 25],
        #                 [48, 11, 61, 56, 8, 51],
        #                 [32, 55, 68, 106, 97, 70],
        #             ]
        #         )
        #         rng[0] = script[n][0]
        #         rng[1] = script[n][1]
        #         rng[2] = script[n][2]
        #         rng[3] = script[n][3]
        #         rng[4] = script[n][4]
        #         rng[5] = script[n][5]

        # if table_id in [9, 10]:
        #     rng[0] = 107
        #     rng[1] = 87
        #     rng[2] = 88
        #     rng[3] = 81
        #     rng[4] = 9
        #     rng[5] = 94

        # generator arr_result
        for i in range(window_size):
            for j in range(reel_num):
                use_reel = Box.arr_reels[int(table_id), :, j]
                use_reel_len = Box.reels_len[int(table_id), j]
                arr_result[i, j] = use_reel[(rng[j] + i) % use_reel_len]

        # if table_id in [7, 8, 9, 10]:
        #     print(table_id, rng)
        #     # print(arr_result, table_id)

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

    def calculate_win(game_scence, arr_result, pay_symbols, log, multi):  # log
        pay_sum = 0
        pay_symbols_new = np.full(len(Box.symbols_all), 99, dtype=arr_result.dtype)  # 預設最大長度

        idx = 0
        for symbol in Box.symbols_all:  # 每個symbol看
            if symbol in Box.symbols_score:
                line = get_element_num_nxn(arr_result, symbol)
                pay = int(get_pay(symbol, line)) * int(multi)
                pay_sum += pay
                if pay > 0:
                    pay_symbols_new[idx] = symbol
                    idx += 1

                    if log:
                        # print(game_scence, arr_result, pay_symbols, log, multi)
                        log_hit(symbol, line, game_scence)
                        log_pay(symbol, line, pay, game_scence)
                        log_eliminate(symbol, line, game_scence)
                        # print("   symbol: ", symbol, "line: ", line, "pay: ", pay)

        copy_array_1xn(pay_symbols_new, pay_symbols)

        return pay_sum

    def remove_and_fall(table_id, rng, arr_result, remove_symbol, remove_cnt):
        rows, cols = arr_result.shape

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

            use_reel_weight = Box.arr_reels_weight[int(table_id), :, c]
            use_reel_weight_clear = use_reel_weight[use_reel_weight != -1]  # 清除-1

            cnt_next = remove_cnt[c]
            while len(nonremove) < rows:
                cnt_next += 1
                append_symbol = use_reel_clear[rng[c] - cnt_next % use_reel_clear_len]
                if Box.C1 in nonremove and append_symbol == Box.C1:
                    cnt_next += 1
                    append_symbol = use_reel_clear[rng[c] - cnt_next % use_reel_clear_len]
                if Box.C2 in nonremove and append_symbol == Box.C2:
                    cnt_next += 1
                    append_symbol = use_reel_clear[rng[c] - cnt_next % use_reel_clear_len]
                # while use_reel_weight_clear[rng[c] - cnt_next % use_reel_clear_len] == 0:
                #     cnt_next += 1
                #     append_symbol = use_reel_clear[rng[c] - cnt_next % use_reel_clear_len]

                nonremove.insert(0, append_symbol)

            remove_cnt[c] = cnt_next
            for i in range(rows):
                arr_result[:, c][i] = nonremove[i]

    # main
    def base_game():  # log
        """
        遊戲流程
        * spin->算分->消除->掉落->算分->...
        """
        pay_symbol = np.full(len(Box.symbols_all), 99, dtype=arr_result_BG.dtype)

        # spin --根據???決定使用的表
        table_id = 0
        if bet_mode == Box.mode_featurebuy or bet_mode == Box.mode_superfeaturebuy:
            table_id = Box.strip_BG4
        else:
            table_id = get_value(weigh_table_cum)
        arr_result_generator(table_id, rng_BS, arr_result_BG, -1)

        # calculate
        pay_sum = 0
        pay_base = calculate_win(Box.scence_BG, arr_result_BG, pay_symbol, True, 1)
        pay_sum += pay_base

        # remove and fall
        remove_cnt = np.zeros(Box.reel_num[Box.scence_BG], np.int64)
        cnt = 0
        while True:
            if pay_symbol[0] == 99:
                break
            remove_and_fall(table_id, rng_BS, arr_result_BG, pay_symbol, remove_cnt)
            pay_base = calculate_win(Box.scence_BG, arr_result_BG, pay_symbol, True, 1)
            pay_sum += pay_base
            cnt += 1

        pay_c1 = calculate_win_c1(Box.scence_BG, arr_result_BG)
        pay_sum += pay_c1

        # record
        log_all(pay_sum > 0, Box.RA_hits_BG, 1)

        return pay_sum, pay_c1

    def free_game():  # log
        # print("================================================")
        # print(rng_BS)
        # print(arr_result_BG)
        # print(rng_FS)
        # print(arr_result_FG)

        free_spins_low = N_low
        free_spins_high = N_high
        cnt_free_spins_low = 0
        cnt_free_spins_high = 0
        pay_FG = 0
        pay_symbol_pre = np.full(len(Box.symbols_all), 99, dtype=arr_result_FG.dtype)
        pay_symbol = np.full(len(Box.symbols_all), 99, dtype=arr_result_FG.dtype)

        cnt_ = 0
        # script = [3, 7]
        while True:
            table_id = 0
            if cnt_free_spins_high < free_spins_high:
                table_id = strip_F2
                cnt_free_spins_high += 1
            elif cnt_free_spins_low < free_spins_low:
                table_id = strip_F1
                cnt_free_spins_low += 1
            else:
                break

            # cnt_ += 1
            # if cnt_ in script:
            #     table_id = 10
            # else:
            #     table_id = 9

            # spin --根據???決定使用的表
            arr_result_generator(table_id, rng_FS, arr_result_FG, cnt_ - 1)
            # print(f"\n\n\n--- 第{cnt_free_spins_low + cnt_free_spins_high}次spin --------------------------")
            # print(table_id, rng_FS)
            # print("* arr_result_FG:")
            # print(arr_result_FG)

            # --------------------------------------------------- 先取得最終倍數

            copy_array(arr_result_FG, arr_result_FG_pre)  # 複製一個預先算倍數的arr
            calculate_win(Box.scence_FG, arr_result_FG_pre, pay_symbol_pre, False, 1)

            # remove and fall
            remove_cnt_pre = np.zeros(Box.reel_num[Box.scence_FG], np.int64)
            cnt_eliminate = 0
            while True:
                if pay_symbol_pre[0] == 99:
                    break
                remove_and_fall(table_id, rng_FS, arr_result_FG_pre, pay_symbol_pre, remove_cnt_pre)
                calculate_win(Box.scence_FG, arr_result_FG_pre, pay_symbol_pre, False, 1)
                cnt_eliminate += 1
                # print()
            # print("* cnt_eliminate: ", cnt_eliminate)

            # re-trigger
            if free_spins_low + free_spins_high < Box.max_spin_free_game:
                num_C1 = get_element_num_nxn(arr_result_FG_pre, Box.C1)
                if num_C1 in Box.pay_table_C1_reteigger:
                    free_spins_low += Box.extra_spin_low
                    free_spins_high += Box.extra_spin_high

            # get multiplier
            num_C2 = get_element_num_nxn(arr_result_FG_pre, Box.C2)
            multi_cum = 0
            for i in range(num_C2):
                if table_id in [8, 10]:
                    idx = get_value(weigh_multiplier_range_high_cum)
                else:
                    idx = get_value(weigh_multiplier_range_low_cum)

                multi = Box.value_multiplier[int(idx)]
                multi_cum += multi
                # print("multi: ", int(multi), "num_C2: ", num_C2, "idx: ", idx)

            # print("\n", end="")

            if multi_cum == 0:
                multi_cum = 1

            # ---------------------------------------------------

            # calculate
            pay_sum = 0
            pay_base = calculate_win(Box.scence_FG, arr_result_FG, pay_symbol, True, multi_cum)
            pay_sum += pay_base

            # print("----- ", -1, "* arr_result_FG:")
            # print(arr_result_FG)
            # print("*0 pay_base: ", pay_base, "pay_symbol: ", pay_symbol, "multi_cum: ", multi_cum)

            # remove and fall
            remove_cnt = np.zeros(Box.reel_num[Box.scence_FG], np.int64)
            cnt = 0

            while True:
                if pay_symbol[0] == 99:
                    break

                remove_and_fall(table_id, rng_FS, arr_result_FG, pay_symbol, remove_cnt)
                pay_base = calculate_win(Box.scence_FG, arr_result_FG, pay_symbol, True, multi_cum)
                pay_sum += pay_base
                cnt += 1

            #     print("----- ", cnt, "* arr_result_FG:")
            #     print(arr_result_FG)
            #     print("*1 pay_base: ", pay_base, "pay_symbol: ", pay_symbol, "multi_cum: ", multi_cum)

            # print("* pay_sum: ", pay_sum)

            # ---------------------------------------------------

            # update
            pay_FG += pay_sum

            # record
            log_all(pay_sum > 0, Box.RA_hits_FG, 1)
            log_all(True, Box.RA_free_spins, 1)

        # record
        log_all(True, Box.RA_trigger_freegame, 1)

        return pay_FG

    # simulate n times
    for _ in range(total_round):

        total_win = 0  # 總得分

        # base game
        pay_BG, pay_c1 = base_game()
        total_win += pay_BG

        # free game
        pay_FG = 0
        if pay_c1 > 0:  # free game
            pay_FG = free_game()
            log_multi_line(Box.output_FG, pay_FG)

        total_win += pay_FG

        # 標準差
        log_all(True, Box.RA_x_sum, total_win / coin_in)  # x_sum
        log_all(True, Box.RA_x_square, (total_win / coin_in) ** 2)  # x_square

        # 倍率線型
        log_multi_line(Box.output_BG, pay_BG)
        log_multi_line(Box.output_OA, total_win)

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
        value_idx = [Box.R_multiplier_range_cnt_BG, Box.R_multiplier_range_cnt_FG, Box.R_multiplier_range_cnt_OA]
        value_name = ["Base Game", "Free Game", "Over All"]

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

        avg_multi_FG = (rtp_FG_FS + rtp_BG_SC) / p_trigger_FG

        std = ((record_data[Box.R_all, Box.RA_x_square] - ((record_data[Box.R_all, Box.RA_x_sum]) ** 2 / total_round)) / total_round) ** 0.5
        median = Mat.threshold_record[Mat.cfunc.get_median_idx_from_multiplier_line(record_data[Box.R_multiplier_range_cnt_FG])]

        # [show_detail]
        data_hits = record_data[Box.R_hits[0] : Box.R_hits[1], :].copy() / total_round
        data_rtp = record_data[Box.R_pay[0] : Box.R_pay[1], :].copy() / coin_in / total_round
        data_eliminate = record_data[Box.R_eliminate[0] : Box.R_eliminate[1], :].copy() / total_round

        # data_complete_rate_FG = record_data[Box.R_all, Box.RA_hits_complete_FG] / record_data[Box.R_all, Box.RA_trigger_freegame]

        # [show_multi_line]
        data_multiplier_cnt_BG = Mat.cplot.map_multiplier_big2small_v2(Mat.threshold_v7, Mat.threshold_v7, record_data[Box.R_multiplier_range_cnt_BG])
        data_multiplier_cnt_FG = Mat.cplot.map_multiplier_big2small_v2(Mat.threshold_v7, Mat.threshold_v7, record_data[Box.R_multiplier_range_cnt_FG])
        data_multiplier_cnt_OA = Mat.cplot.map_multiplier_big2small_v2(Mat.threshold_v7, Mat.threshold_v7, record_data[Box.R_multiplier_range_cnt_OA])

    if True:  # 結果格式設定
        # [output_data]
        df_base = pd.DataFrame([], columns=["Index", "Value", "Value2"])
        f_write_data = lambda idx, v1, v2="": write_data(df_base, idx, v1, v2)

        f_write_data("total round", format(total_round, ","))
        f_write_data("durning", "{:0.2f}s".format(durning))

        f_write_data("RTP", "{0:0.5f}".format(rtp_BG_BS + rtp_BG_SC + rtp_FG_FS))
        f_write_data("RTP - base spin", "{0:0.5f}".format(rtp_BG_BS))
        f_write_data("RTP - scatter pay", "{0:0.5f}".format(rtp_BG_SC))
        f_write_data("RTP - free spin", "{0:0.5f}".format(rtp_FG_FS))

        f_write_data("hit rate - base spin", "{0:0.5f}".format(hit_rate_BG))
        f_write_data("hit rate - free spin", "{0:0.5f}".format(hit_rate_FG))

        f_write_data("觸發機率 (FG)", "{:0.5f}".format(p_trigger_FG), "{:0.2f}場".format(1 / p_trigger_FG))

        f_write_data("平均Spin (FG)", "{:0.5f}".format(p_avg_spin_FG))
        f_write_data("平均倍數", "{:0.2f}".format(avg_multi_FG))

        f_write_data("expected value (EX)", "{:0.6f}".format(rtp_BG_BS + rtp_FG_FS))
        f_write_data("standard deviation (SD)", "{:0.6f}".format(std))
        f_write_data("median", "{:0.2f}".format(median))
        f_write_data("positive index", "{:0.2f}".format(median / avg_multi_FG))

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
        # cplot.multiplier_line(data_multiplier_OA, Mat.threshold_show, name + "OA", ylim=0.15)

    if output_data:  # 輸出資料

        df_detail = pd.concat([df_hits, df_rtp, df_eliminate], axis=0)
        df_detail.reset_index(inplace=True)
        df_output = pd.concat([df_base, df_detail], axis=1)

        df_multiplier_line = get_multiplier_data(record_data, Mat.threshold_record)
        df_record_data = pd.DataFrame(record_data)

        with pd.ExcelWriter(Box.path_output_data(f"_betmode{bet_mode}")) as writer:
            df_output.to_excel(writer, sheet_name="Base Info", index=False)
            df_multiplier_line.to_excel(writer, sheet_name="Multiplier Line", index=False)
            df_record_data.to_excel(writer, sheet_name="Record Data", index=False)


record_data = record_data.astype(np.float64)
simulater_result(True, False, False, False)


# %% --- Test ---


# %%
