# %% ----- Import -----


import pandas as pd
import numpy as np
import numba as nb

import GameSetting as GS
import Tool.RedBox as RB


# %% ----- [Function] Get Data -----


def __get_strip(dir, sheet, get_length=False):
    data = pd.read_excel(dir, sheet_name=str(sheet))

    R1 = data.r1.dropna().values
    R2 = data.r2.dropna().values
    R3 = data.r3.dropna().values
    R4 = data.r4.dropna().values
    R5 = data.r5.dropna().values

    if get_length:
        R1_len = R1.shape[0]
        R2_len = R2.shape[0]
        R3_len = R3.shape[0]
        R4_len = R4.shape[0]
        R5_len = R5.shape[0]

        return R1, R2, R3, R4, R5, R1_len, R2_len, R3_len, R4_len, R5_len

    return R1, R2, R3, R4, R5, None


def __get_paytable(dir, sheet):
    data = pd.read_excel(dir, sheet_name=str(sheet))

    paytable = data[["line1", "line2", "line3", "line4", "line5"]].values
    symbol_str = data.symbol.to_list()
    symbol_id = np.array(data.id.to_list(), dtype=np.int64)

    return paytable, symbol_str, symbol_id


# %% ----- Setting -----


# [configure]

model_id = "S025"
version = "0.0.0.1"

window_size = 3
reel_num = 5
arr_shape = (window_size, reel_num)


# [symbol]

wild = 0
scatter1 = 1
scatter2 = 2
special_symbols = np.array([0, 1, 2], dtype=np.int64)
m_symbols = np.array([3, 4, 5, 6], dtype=np.int64)
number_symbols = np.array([7, 8, 9, 10, 11], dtype=np.int64)


# [strip]

# - base strip
BR1, BR2, BR3, BR4, BR5, *_length = __get_strip(GS.path_math_data, "basegame_strip", True)
BR1_len, BR2_len, BR3_len, BR4_len, BR5_len = _length

# - free strip
# FR1, FR2, FR3, FR4, FR5, *_length = __get_strip(GS.path_math_data, "freegame_strip", True)
# FR1_len, FR2_len, FR3_len, FR4_len, FR5_len = _length


# [pay table]

paytable, symbol_str, symbol_id = __get_paytable(GS.path_math_data, "pay_table")


# [else]

pay_lines_cnt = 88  # 幾線

bet = 1
add_rate = 1
coin_in = pay_lines_cnt * bet * add_rate


# %% ----- [Function] Demo Game Use -----


class ExpandingArr:
    def add_base_array(rng, game_type):
        new_shape = (GS.show_arr_len, reel_num)
        arr = np.zeros(new_shape)

        if game_type == "base":
            for i in range(GS.show_arr_len):
                arr[i, 0] = BR1[(rng[0] + i) % BR1_len]
                arr[i, 1] = BR2[(rng[1] + i) % BR2_len]
                arr[i, 2] = BR3[(rng[2] + i) % BR3_len]
                arr[i, 3] = BR4[(rng[3] + i) % BR4_len]
                arr[i, 4] = BR5[(rng[4] + i) % BR5_len]
        elif game_type == "free":
            # for i in range(GS.show_arr_len):
            #     arr[i, 0] = FR1[(rng[0] + i) % FR1_len]
            #     arr[i, 1] = FR2[(rng[1] + i) % FR2_len]
            #     arr[i, 2] = FR3[(rng[2] + i) % FR3_len]
            #     arr[i, 3] = FR4[(rng[3] + i) % FR4_len]
            #     arr[i, 4] = FR5[(rng[4] + i) % FR5_len]
            pass

        return arr

    def add_payline_array(arr_list):
        new_shape = (GS.show_arr_len, reel_num)
        new_arr_list = []
        for arr_t in arr_list:
            arr, text = arr_t
            add = np.zeros(new_shape)
            new_arr_list.append((np.row_stack([arr, add]), text))

        return new_arr_list


class MathOutput:
    def __init__(self, rng=np.zeros(reel_num), arr_result=np.zeros(shape=arr_shape), pay_line=list(), score=0, trigger_score=0, have_wild_cnt=0) -> None:
        self.rng = rng
        self.arr_result = arr_result
        self.paylines = pay_line
        self.score = score
        self.trigger_cnt = have_wild_cnt

        # special
        self.trigger_score = trigger_score


def basegame_spin_and_calculate(print_log=False):
    rng = np.zeros(reel_num, dtype=np.int64)
    arr_result = np.zeros((window_size, reel_num), dtype=np.int64)

    def rng_generator():
        rng[0] = np.random.randint(BR1_len)
        rng[1] = np.random.randint(BR2_len)
        rng[2] = np.random.randint(BR3_len)
        rng[3] = np.random.randint(BR4_len)
        rng[4] = np.random.randint(BR5_len)

        # # lock rng (test)
        # lock_rng = [1, 11, 35, 40, 25]
        # for i in range(len(lock_rng)):
        #     rng[i] = lock_rng[i]

        return None

    def arr_result_generator():
        for i in range(window_size):
            arr_result[i, 0] = BR1[(rng[0] + i) % BR1_len]
            arr_result[i, 1] = BR2[(rng[1] + i) % BR2_len]
            arr_result[i, 2] = BR3[(rng[2] + i) % BR3_len]
            arr_result[i, 3] = BR4[(rng[3] + i) % BR4_len]
            arr_result[i, 4] = BR5[(rng[4] + i) % BR5_len]

        # # lock arr_result (test)
        # lock_arr_result = np.array(
        #     [
        #         [2, 2, 2, 2, 2],
        #         [1, 0, 2, 1, 1],
        #         [3, 3, 3, 1, 1],
        #     ],
        #     dtype=np.int64,
        # )

        # for i in range(len(lock_arr_result)):
        #     arr_result[i] = lock_arr_result[i]

        return None

    def __get_lines(result):
        # 計算symbol的連線得分(不包含c1)
        line = 0
        have_wild = False

        score_symbol = -1
        for i in result:
            if score_symbol != -1 and score_symbol != i and i != wild:
                break

            if i != wild:
                score_symbol = i

            line += 1
            have_wild |= i == wild

        if score_symbol == scatter1:
            line, have_wild = 1, False

        return score_symbol, line, have_wild

    def __get_scatter_line(array):
        # 計算c1在base game的連線得分
        result = (array == 1).sum(axis=0)
        for i in range(len(result)):
            if result[i] >= 1:
                result[i] = 1

        line = 0
        for i in range(len(result)):
            if result[i] >= 1:
                line += 1
            else:
                break

        return line

    def calculate(array):
        # output
        pay = 0
        payline_list = []
        have_wild_cnt = 0

        col_first = np.unique(array[:, 0])

        for symbol in col_first:
            if symbol != 1:
                mul_ = 1
                line = 0
                for i in range(reel_num):
                    check_list = array[:, i]
                    if symbol in check_list or 0 in check_list:
                        mul = (check_list == symbol).sum() + (check_list == 0).sum()
                        line += 1
                        mul_ *= mul
                    else:
                        break
                if line >= 3:
                    score = paytable[symbol][line - 1] * mul_
                    pay += score

                    payline_arr = np.full(arr_result.shape, -1, np.int64)
                    payline_arr[arr_result == symbol] = 1
                    payline_arr[arr_result == 0] = 1
                    payline_arr[payline_arr == -1] = 0

                    # print(payline_arr)

                    show_text = GS.format_payline_btn_payline.format(line=line, way=mul_, symbol=symbol_str[symbol], pay=score)
                    # print(show_text)
                    payline_list.append((payline_arr, show_text))
            else:
                pass

        return pay, payline_list, have_wild_cnt

    rng_generator()
    arr_result_generator()

    if print_log:
        RB.log_use.print_result("rng", rng, next_line=True)
        print("")

    score, paylines, have_wild_cnt = calculate(arr_result)

    # return MathOutput(rng, arr_result, paylines, score, have_wild_cnt=have_wild_cnt)
    return MathOutput(rng, ExpandingArr.add_base_array(rng, "base"), ExpandingArr.add_payline_array(paylines), score, have_wild_cnt=have_wild_cnt)


basegame_spin_and_calculate()

# %%
