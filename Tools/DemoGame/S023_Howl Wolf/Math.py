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


def __get_paylines(dir, sheet):
    data = pd.read_excel(dir, sheet_name=str(sheet), dtype=str).pay_line

    def line_str_to_arr(line):
        """
        Examples
        --------
        >>> '01210'
        np.array([
            [1, 0, 0, 0, 0],
            [1, 0, 0, 0, 0],
            [1, 0, 0, 0, 0]
            ])
        """
        lines_arr = np.zeros(arr_shape, np.int64)

        # line[col_idx] = row_idx
        for col_idx in range(len(line)):
            lines_arr[line[col_idx], col_idx] = 1

        return lines_arr

    lines_set = []
    for line in data:
        lines_set.append([int(i) for i in line])

    line_arrs = []
    for line in lines_set:
        line_arrs.append(line_str_to_arr(line))

    return np.array(line_arrs, dtype=np.int64)


def __get_spins_weight(dir, sheet):  # for free game
    data = pd.read_excel(dir, sheet_name=str(sheet))

    return data["weight"].values, np.cumsum(data["weight"].values)


# %% ----- Setting -----


# [configure]

model_id = "S026"
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
all_symbols = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])


# [strip]

# - base strip
BR1, BR2, BR3, BR4, BR5, *_length = __get_strip(GS.path_math_data, "basegame_strip", True)
BR1_len, BR2_len, BR3_len, BR4_len, BR5_len = _length

# - free strip
FR1, FR2, FR3, FR4, FR5, *_length = __get_strip(GS.path_math_data, "freegame_strip", True)
FR1_len, FR2_len, FR3_len, FR4_len, FR5_len = _length


# [pay table]

paytable, symbol_str, symbol_id = __get_paytable(GS.path_math_data, "pay_table")
trigger_freegame_unique_score_list = np.unique(paytable[3:, 2:])


# [pay line]

pay_lines = __get_paylines(GS.path_math_data, "pay_lines")


# [random spins weight]

spins_weight, spins_weight_cum = __get_spins_weight(GS.path_math_data, "free_spins")
spins_prob = spins_weight / sum(spins_weight)


# [else]

c1_score_in = data = pd.read_excel(GS.path_math_data, sheet_name=str("setting"), header=None)[1][0]  # 進freegame的分數(pay)
free_spins = data = pd.read_excel(GS.path_math_data, sheet_name=str("setting"), header=None)[1][1]  # free spin

pay_lines_cnt = len(pay_lines)  # 幾線

bet = 1 * 5 / 10  # $
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
            for i in range(GS.show_arr_len):
                arr[i, 0] = FR1[(rng[0] + i) % FR1_len]
                arr[i, 1] = FR2[(rng[1] + i) % FR2_len]
                arr[i, 2] = FR3[(rng[2] + i) % FR3_len]
                arr[i, 3] = FR4[(rng[3] + i) % FR4_len]
                arr[i, 4] = FR5[(rng[4] + i) % FR5_len]

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
    def __init__(self, rng=np.zeros(reel_num), arr_result=np.zeros(shape=arr_shape), pay_line=list(), score=0, trigger_score_stack=[]) -> None:
        self.rng = rng
        self.arr_result = arr_result
        self.paylines = pay_line
        self.score = score

        # special
        self.trigger_score_stack = trigger_score_stack


def basegame_spin_and_calculate(print_log=False, set_seed=-1):
    print("base game.")

    # --- set seed ---
    if set_seed != -1:
        np.random.seed(set_seed)
    # ---

    rng = np.zeros(reel_num, dtype=np.int64)
    arr_result = np.zeros((window_size, reel_num), dtype=np.int64)

    def rng_generator():
        rng[0] = np.random.randint(BR1_len)
        rng[1] = np.random.randint(BR2_len)
        rng[2] = np.random.randint(BR3_len)
        rng[3] = np.random.randint(BR4_len)
        rng[4] = np.random.randint(BR5_len)

        # # lock rng (test)(0分盤面)
        # lock_rng = [10, 11, 35, 40, 25]
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
        # lock_arr_result = np.array([
        #     [8, 8, 7, 1, 5],
        #     [8, 8, 7, 9, 5],
        #     [8, 8, 7, 2, 2]], dtype=np.int64)

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
        # have_wild_cnt = 0
        have_wild_score_stack = []

        # - scatter part
        line = __get_scatter_line(array)
        pay_idx = line - 1 if line > 0 else 0
        score = paytable[scatter1, pay_idx] * coin_in
        pay += score

        if score > 0:
            show_arr = arr_result.copy()
            show_arr[show_arr == scatter1] = 1
            show_arr[show_arr != scatter1] = 0
            show_arr[:, line:] = 0

            show_text = GS.format_bg_payline_btn_scatterpay.format(line=line + 1, symbol=symbol_str[scatter1], pay=score)
            payline_list.append((show_arr, show_text))

            if print_log:
                RB.log_use.print_result("line", line, "score", score, tag="[c1]")
                RB.log_use.print_result("score line", show_arr, next_line=True)
                print("")

        # - symbol part
        for i, pay_line in enumerate(pay_lines):
            result = (array.T)[pay_line.T == 1]
            score_symbol, line, have_wild = __get_lines(result)
            score = paytable[score_symbol, line - 1] * bet
            pay += score
            if score > 0:
                show_text = GS.format_payline_btn_payline.format(line_id=i, line=line + 1, symbol=symbol_str[score_symbol], pay=score)
                payline_list.append((pay_line, show_text))

            if have_wild:
                have_wild_score_stack.append(score)

            if print_log:
                if score > 0:
                    RB.log_use.print_result("symbol", score_symbol, "line", line, "have wild", have_wild, "score", score, tag=f"[line {i}]")
                    RB.log_use.print_result("score line", pay_line, next_line=True)
                    print("")

        return pay, payline_list, have_wild_score_stack

    rng_generator()
    arr_result_generator()

    if print_log:
        RB.log_use.print_result("rng", rng, next_line=True)
        print("")

    score, paylines, trigger_score_stack = calculate(arr_result)

    return MathOutput(
        rng,
        ExpandingArr.add_base_array(rng, "base"),
        ExpandingArr.add_payline_array(paylines),
        score,
        trigger_score_stack=trigger_score_stack,
        # trigger_score_stack=[10, 20],
    )


def freegame_spin_and_calculate(trigger_score, print_log=False):
    print(f"free game. {trigger_score}")

    rng = np.zeros(reel_num, dtype=np.int64)
    arr_result = np.zeros((window_size, reel_num), dtype=np.int64)

    def rng_generator():
        rng[0] = np.random.randint(FR1_len)
        rng[1] = np.random.randint(FR2_len)
        rng[2] = np.random.randint(FR3_len)
        rng[3] = np.random.randint(FR4_len)
        rng[4] = np.random.randint(FR5_len)

        # # lock rng (test)
        # lock_rng = [0,0,0,0,9]
        # for i in range(len(lock_rng)):
        #     rng[i] = lock_rng[i]

        return None

    def arr_result_generator():
        for i in range(window_size):
            arr_result[i, 0] = FR1[(rng[0] + i) % FR1_len]
            arr_result[i, 1] = FR2[(rng[1] + i) % FR2_len]
            arr_result[i, 2] = FR3[(rng[2] + i) % FR3_len]
            arr_result[i, 3] = FR4[(rng[3] + i) % FR4_len]
            arr_result[i, 4] = FR5[(rng[4] + i) % FR5_len]

        # # lock arr_result (test)
        # lock_arr_result = np.array([
        #     [8, 8, 0, 8, 5],
        #     [9, 8, 1, 9, 5],
        #     [2, 2, 2, 2, 2]], dtype=np.int64)

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
        have_wild_score_stack = []

        # - scatter part
        c1_num = len(array[array == scatter1])
        score = c1_num * trigger_score
        pay += score

        if score > 0:
            show_arr = arr_result.copy()
            show_arr[show_arr == scatter1] = 1
            show_arr[show_arr != scatter1] = 0
            show_text = GS.format_bg_payline_btn_scatterpay.format(line=c1_num, symbol=symbol_str[scatter1], pay=score)
            payline_list.append((show_arr, show_text))

            if print_log:
                RB.log_use.print_result("c1_num", c1_num, "score", score, tag="[c1]")
                RB.log_use.print_result("score line", show_arr, next_line=True)
                print("")

        # - symbol part
        for i, pay_line in enumerate(pay_lines):
            result = (array.T)[pay_line.T == 1]
            score_symbol, line, have_wild = __get_lines(result)
            score = paytable[score_symbol, line - 1] * bet
            pay += score

            if score > 0:
                show_text = GS.format_payline_btn_payline.format(line_id=i, line=line + 1, symbol=symbol_str[score_symbol], pay=score)
                payline_list.append((pay_line, show_text))

            if have_wild:
                have_wild_score_stack.append(score)

            if print_log:
                if score > 0:
                    RB.log_use.print_result("symbol", score_symbol, "line", line, "have wild", have_wild, "score", score, tag=f"[line {i}]")
                    RB.log_use.print_result("score line", pay_line, next_line=True)
                    print("")

        return pay, payline_list, have_wild_score_stack

    rng_generator()
    arr_result_generator()

    if print_log:
        RB.log_use.print_result("rng", rng, next_line=True)
        print("")

    score, paylines, have_wild_score_stack = calculate(arr_result)

    return MathOutput(
        rng,
        ExpandingArr.add_base_array(rng, "free"),
        ExpandingArr.add_payline_array(paylines),
        score,
        trigger_score_stack=have_wild_score_stack,
    )


def random_spins():
    def get_value(cum_weight):
        """
        丟累積的Weight, Output第幾個
        """
        rd = np.random.randint(0, cum_weight[-1])
        for i in range(len(cum_weight)):
            if rd < cum_weight[i]:
                return i

    return get_value(spins_weight_cum) + 5


# %%
