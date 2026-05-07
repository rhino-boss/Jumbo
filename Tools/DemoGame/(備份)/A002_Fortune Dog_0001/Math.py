# %% ----- Import -----


import pandas as pd
import numpy as np

import GameSetting as GS
import Tool.RedBox as RB


# %% ----- [Function] Get Data -----


if True:

    def get_strip(dir, sheet, get_length=False):
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

    def get_paytable(dir, sheet):
        data = pd.read_excel(dir, sheet_name=str(sheet))

        paytable = data[["line1", "line2", "line3", "line4", "line5"]].values
        symbol_str = data.symbol.to_list()
        symbol_id = np.array(data.id.to_list(), dtype=np.int64)

        return paytable, symbol_str, symbol_id

    def get_paylines(dir, sheet):
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

    def get_spins_weight(dir, sheet):  # for free game
        data = pd.read_excel(dir, sheet_name=str(sheet))

        return data["spins"].values, data["weight"].values, np.cumsum(data["weight"].values)


# %% ----- Setting -----


if True:
    # [configure]

    model_id = "A002"
    version = "0.0.0.1"

    window_size = 3
    reel_num = 5
    arr_shape = (window_size, reel_num)

    max_freespins = 10

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
    BR1, BR2, BR3, BR4, BR5, *_length = get_strip(GS.path_math_data, "basegame_strip", True)
    BR1_len, BR2_len, BR3_len, BR4_len, BR5_len = _length

    # - free strip
    FR1, FR2, FR3, FR4, FR5, *_length = get_strip(GS.path_math_data, "freegame_strip", True)
    FR1_len, FR2_len, FR3_len, FR4_len, FR5_len = _length

    # [pay table]
    paytable, symbol_str, symbol_id = get_paytable(GS.path_math_data, "pay_table")
    trigger_freegame_unique_score_list = np.unique(paytable[3:, 2:])

    # [pay line]
    pay_lines = get_paylines(GS.path_math_data, "pay_lines")

    # [random spins weight]
    spins, spins_weight, spins_weight_cum = get_spins_weight(GS.path_math_data, "free_spins")
    spins_prob = spins_weight / sum(spins_weight)

    # [else]

    pay_lines_cnt = len(pay_lines)  # 幾線

    bet = 1
    add_rate = 1
    coin_in = pay_lines_cnt * bet * add_rate


# %% ----- [Data] Demo Game Use -----


class MathOutput:
    def __init__(
        self,
        game_type=0,
        rng=np.zeros(reel_num),
        arr_result=np.zeros(shape=arr_shape),
        pay_lines=list(),
        show_score=0,
        trigger_freespins=0,
        arr_sticky_symbol=np.zeros(shape=arr_shape),
        arr_sticky_posi=np.zeros(shape=arr_shape),
    ) -> None:
        # basic
        self.game_type = game_type

        self.rng = rng
        self.arr_result = arr_result
        self.pay_lines = pay_lines
        self.show_score = show_score
        self.trigger_freespins = trigger_freespins

        # by game
        self.arr_sticky_symbol = arr_sticky_symbol
        self.arr_sticky_posi = arr_sticky_posi

        self.arr_sticky_symbol_init = np.zeros(shape=arr_shape)
        self.arr_sticky_posi_init = np.zeros(shape=arr_shape)


class MathStatus:
    def __init__(self) -> None:
        # basic
        self.credit = 2000

        self.cnt_spins = 0  # base game累積轉數
        self.cnt_hits = 0  # base game有得分次數(不包含free game)

        self.freegame_coin = 0
        self.have_free_spins = 0  # 有多少次free game
        self.cnt_free_spins = 0  # 該場free game進行了幾次spin
        self.cnt_trigger_freegame_times = 0  #  free game進行次數

        self.max_score_basegame = 0  # 單把最大分數(base game)
        self.max_score_freegame = 0  # 單把最大分數(free game)

        # by game
        self.arr_sticky_symbol = np.zeros(arr_shape)
        self.arr_sticky_posi = np.zeros(arr_shape)


# %% ----- [Function] Demo Game Use -----


# tools
def get_value(cum_weight):
    """
    丟累積的Weight, Output第幾個
    """
    rd = np.random.randint(0, cum_weight[-1])
    for i in range(len(cum_weight)):
        if rd < cum_weight[i]:
            return i

    return get_value(cum_weight)


def generate_payline(shape):
    """
    隨機生成走線
    """
    row, column = shape
    arr = np.zeros(shape)
    for j in range(column):
        rd_i = np.random.randint(0, row)
        arr[rd_i, j] = 1

    return arr


def extend_arr_zero(arr, new_shape):
    """
    arr : 要擴大的array \n
    new_shape : 要轉換的新的大小
    """
    new_arr = np.zeros(new_shape)

    shape = arr.shape
    row, column = shape

    for i in range(row):
        for j in range(column):
            new_arr[i, j] = arr[i, j]

    return new_arr


def generate_arr(shape, ele_range):
    row, column = shape

    ele_min, ele_max = ele_range
    np.random.randint(ele_min, ele_max)

    li = [np.random.randint(ele_min, ele_max) for i in range(row * column)]
    return np.array(li).reshape(shape)


#
def add_base_array(rng, game_type):
    new_shape = (GS.show_arr_len, reel_num)
    arr = np.zeros(new_shape)

    if game_type == 0:
        for i in range(GS.show_arr_len):
            arr[i, 0] = BR1[(rng[0] + i) % BR1_len]
            arr[i, 1] = BR2[(rng[1] + i) % BR2_len]
            arr[i, 2] = BR3[(rng[2] + i) % BR3_len]
            arr[i, 3] = BR4[(rng[3] + i) % BR4_len]
            arr[i, 4] = BR5[(rng[4] + i) % BR5_len]
    elif game_type == 1:
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


# fake data
def generate_fake_math_res_basegame():
    #
    show_window_shape = (GS.show_arr_len, reel_num)

    #
    game_type = 0
    rng = np.array([0, 0, 0, 0, 0])
    # arr_result = np.zeros(show_window_shape)

    row, column = show_window_shape
    li = [np.random.randint(0, len(all_symbols)) for i in range(row * column)]
    arr_result = np.array(li).reshape(show_window_shape)

    score = 404

    pay_lines = []
    for i in range(3):
        show_text = "no setting."
        pay_line = generate_payline(arr_shape)
        pay_line_extend = extend_arr_zero(pay_line, show_window_shape)
        pay_lines.append((pay_line_extend, show_text))

    trigger_freespins = 5

    #
    math_res = MathOutput(game_type, rng, arr_result, pay_lines, score, trigger_freespins)

    return math_res


def generate_fake_math_res_freegame():
    #
    show_window_shape = (GS.show_arr_len, reel_num)

    #
    game_type = 1
    rng = np.array([0, 0, 0, 0, 0])
    # arr_result = np.zeros(show_window_shape)

    row, column = show_window_shape
    li = [np.random.randint(0, len(all_symbols)) for i in range(row * column)]
    arr_result = np.array(li).reshape(show_window_shape)

    score = 404

    pay_lines = []
    for i in range(3):
        show_text = "no setting."
        pay_line = generate_payline(arr_shape)
        pay_line_extend = extend_arr_zero(pay_line, show_window_shape)
        pay_lines.append((pay_line_extend, show_text))

    trigger_freespins = 0

    arr_result_sticky = np.zeros(arr_shape)
    pay_lines_sticky = generate_arr(arr_shape, (0, 2))

    #
    math_res = MathOutput(game_type, rng, arr_result, pay_lines, score, trigger_freespins, arr_result_sticky, pay_lines_sticky)

    return math_res


# main
def basegame_spin_and_calculate(show_info=""):
    print(f"base game. {show_info}")

    rng = np.zeros(reel_num, dtype=np.int64)
    arr_result = np.zeros((window_size, reel_num), dtype=np.int64)

    def rng_generator():
        rng[0] = np.random.randint(BR1_len)
        rng[1] = np.random.randint(BR2_len)
        rng[2] = np.random.randint(BR3_len)
        rng[3] = np.random.randint(BR4_len)
        rng[4] = np.random.randint(BR5_len)

        # # lock rng (test)(0分盤面)
        # lock_rng = [0, 0, 0, 0, 0]
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

    rng_generator()
    arr_result_generator()

    math_res = generate_fake_math_res_basegame()

    return math_res


def freegame_spin_and_calculate(show_info=""):
    """
    spin
    """
    print(f"free game. {show_info}")

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

    rng_generator()
    arr_result_generator()

    math_res = generate_fake_math_res_freegame()
    return math_res


# %%
