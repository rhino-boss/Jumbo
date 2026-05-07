# %% ----- Import -----


import pandas as pd
import numpy as np

import GameSetting as GS

from Tool.RedBox import log_use


# %% ----- [Function] Get Data -----


if True:

    def __get_strip(dir, sheet, idx):
        data = pd.read_excel(dir, sheet_name=str(sheet))

        R1 = data.iloc[:, 0 + idx * 5].dropna().values.astype("int64")
        R2 = data.iloc[:, 1 + idx * 5].dropna().values.astype("int64")
        R3 = data.iloc[:, 2 + idx * 5].dropna().values.astype("int64")
        R4 = data.iloc[:, 3 + idx * 5].dropna().values.astype("int64")
        R5 = data.iloc[:, 4 + idx * 5].dropna().values.astype("int64")

        R1_len = R1.shape[0]
        R2_len = R2.shape[0]
        R3_len = R3.shape[0]
        R4_len = R4.shape[0]
        R5_len = R5.shape[0]

        log_use.print_run_log(f"already get [strip] [{sheet}].")
        return R1, R2, R3, R4, R5, R1_len, R2_len, R3_len, R4_len, R5_len

    def __get_paytable(dir, sheet):
        data = pd.read_excel(dir, sheet_name=str(sheet))
        paytable = data[["line1", "line2", "line3", "line4", "line5"]].values
        symbol_str = data.symbol.to_list()
        symbol_id = np.array(data.id.to_list(), dtype=np.int64)

        power_symbols = np.array(data.power_up.values, dtype=np.int64)
        power_symbols = np.array([i for i, v in enumerate(power_symbols) if v == 1], dtype=np.int64)

        log_use.print_run_log(f"already get [{sheet}].")
        return paytable, symbol_str, symbol_id, power_symbols

    def __get_power_up(dir, sheet):
        data = pd.read_excel(dir, sheet_name=str(sheet))
        power_up = data.power_up.values

        log_use.print_run_log(f"already get [{sheet}].")
        return power_up

    def __get_weight(dir, sheet, col):
        data = pd.read_excel(dir, sheet_name=str(sheet))[col].dropna().values
        data_cum = data.cumsum(axis=0).astype("int64")

        log_use.print_run_log(f"already get [{sheet}].")
        return data, data_cum

    def __get_uup_weight(dir, sheet, id):
        data = pd.read_excel(dir, sheet_name=str(sheet)).iloc[id * 4 : id * 4 + 4, :].values
        data_cum = data.cumsum(axis=0)

        log_use.print_run_log(f"already get [{sheet}].")
        return data, data_cum

    def __get_multi(dir, sheet):
        data = pd.read_excel(dir, sheet_name=str(sheet))

        log_use.print_run_log(f"already get [{sheet}].")
        return data.multi.values, data.weight.cumsum().values


# [configure]
if True:
    model_id = "A007"
    slot_name = "包你發至尊版 富貴連線"
    version = "0001"

    window_size = 3  # base game, free game
    reel_num = 5
    arr_shape = (window_size, reel_num)

    arr_shape_show = (window_size + GS.window_add_show, reel_num)

    uup_vaild_reel = np.array([0, 1, 1, 1, 0], dtype=np.int32)

    free_spins = 6
    max_freegame = 5  # 最大free game場數
    max_freespins = 30  # 最大free spin次數

    # [symbol]
    WW = 0
    C1 = 1
    M1 = 2
    M2 = 3
    M3 = 4
    M4 = 5
    M5 = 6
    A = 7
    K = 8
    Q = 9
    J = 10
    MY = 11
    FE = 12

    symbols_special = np.array([WW, C1], dtype=np.int64)  # WW, C1
    symbols_m = np.array([M1, M2, M3, M4, M5], dtype=np.int64)  # M1, M2, M3, M4, M5
    symbols_number = np.array([A, K, Q, J], dtype=np.int64)  # A, K, Q, J
    symbols_else = np.array([MY, FE], dtype=np.int64)  # MY, FE

    symbols_score = np.concatenate([symbols_m, symbols_number])
    symbols = np.concatenate([symbols_special, symbols_m, symbols_number])

# [strip]
if True:
    B1R1, B1R2, B1R3, B1R4, B1R5, *_length = __get_strip(GS.path_math_data, "strip_BG", 0)
    B1R1_len, B1R2_len, B1R3_len, B1R4_len, B1R5_len = _length

    B2R1, B2R2, B2R3, B2R4, B2R5, *_length = __get_strip(GS.path_math_data, "strip_BG", 1)
    B2R1_len, B2R2_len, B2R3_len, B2R4_len, B2R5_len = _length

    B3R1, B3R2, B3R3, B3R4, B3R5, *_length = __get_strip(GS.path_math_data, "strip_BG", 2)
    B3R1_len, B3R2_len, B3R3_len, B3R4_len, B3R5_len = _length

    F1R1, F1R2, F1R3, F1R4, F1R5, *_length = __get_strip(GS.path_math_data, "strip_FG", 0)
    F1R1_len, F1R2_len, F1R3_len, F1R4_len, F1R5_len = _length

    F2R1, F2R2, F2R3, F2R4, F2R5, *_length = __get_strip(GS.path_math_data, "strip_FG", 1)
    F2R1_len, F2R2_len, F2R3_len, F2R4_len, F2R5_len = _length

    F3R1, F3R2, F3R3, F3R4, F3R5, *_length = __get_strip(GS.path_math_data, "strip_FG", 2)
    F3R1_len, F3R2_len, F3R3_len, F3R4_len, F3R5_len = _length

    F4R1, F4R2, F4R3, F4R4, F4R5, *_length = __get_strip(GS.path_math_data, "strip_FG", 3)
    F4R1_len, F4R2_len, F4R3_len, F4R4_len, F4R5_len = _length

    F5R1, F5R2, F5R3, F5R4, F5R5, *_length = __get_strip(GS.path_math_data, "strip_FG", 4)
    F5R1_len, F5R2_len, F5R3_len, F5R4_len, F5R5_len = _length

# [pay table]
pay_table, symbol_str, symbol_id, symbols_powerup = __get_paytable(GS.path_math_data, "pay_table")

# [feature]
if True:
    power_up_value = __get_power_up(GS.path_math_data, "power_value")

    weight_uup_b31, weight_cum_uup_b31 = __get_uup_weight(GS.path_math_data, "weight_uup", 0)
    weight_uup_b32, weight_cum_uup_b32 = __get_uup_weight(GS.path_math_data, "weight_uup", 1)

    weight_uup_f11_level1, weight_cum_uup_f11_level1 = __get_uup_weight(GS.path_math_data, "weight_uup", 2)
    weight_uup_f11_level2, weight_cum_uup_f11_level2 = __get_uup_weight(GS.path_math_data, "weight_uup", 3)

    weight_uup_f21_level1, weight_cum_uup_f21_level1 = __get_uup_weight(GS.path_math_data, "weight_uup", 4)
    weight_uup_f21_level2, weight_cum_uup_f21_level2 = __get_uup_weight(GS.path_math_data, "weight_uup", 5)

    weight_uup_f31_level1, weight_cum_uup_f31_level1 = __get_uup_weight(GS.path_math_data, "weight_uup", 6)
    weight_uup_f31_level2, weight_cum_uup_f31_level2 = __get_uup_weight(GS.path_math_data, "weight_uup", 7)

    weight_uup_f32_level1, weight_cum_uup_f32_level1 = __get_uup_weight(GS.path_math_data, "weight_uup", 8)
    weight_uup_f32_level2, weight_cum_uup_f32_level2 = __get_uup_weight(GS.path_math_data, "weight_uup", 9)

    weight_my, weight_cum_my = __get_weight(GS.path_math_data, "weight", "MY")
    weight_table_BG, weight_cum_table_BG = __get_weight(GS.path_math_data, "weight", "table_BG")
    weight_table_FG, weight_cum_table_FG = __get_weight(GS.path_math_data, "weight", "table_FG")

# [multiplier]
if True:
    multi, multi_weight_cum = __get_multi(GS.path_math_data, "multiplier")

# [else]
if True:
    # pay_lines_cnt = len(pay_lines)  # line
    pay_line = 88  # way
    bet = 1
    add_rate = 1
    coin_in = pay_line * bet * add_rate
    symbol_num = len(symbols_special) + len(symbols_m) + len(symbols_number)  # total symbol num


# %% ----- [Data] Demo Game Use -----


class MathResult:
    """
    輸出給Game的數學結果(每次spin送一個)
    """

    def __init__(
        self,
        game_type=0,
        rng=np.zeros(reel_num),
        arr_result=np.zeros(shape=arr_shape),
        arr_result_2=np.zeros(shape=arr_shape),
        pay_lines=list(),
        show_score=0,
        trigger_freespins=0,
        arr_sticky_symbol=np.zeros(shape=arr_shape),
        arr_sticky_posi=np.zeros(shape=arr_shape),
        trigger_feature=0,
    ) -> None:
        # basic
        self.game_type = game_type

        self.rng = rng

        self.arr_result = arr_result  # 滾動的盤面(滾多長輪高就多長。ex: 3x5，滾10，需要送10x5的array)
        self.arr_result_2 = arr_result_2  # 顯示的第二盤面(MY要接露用的)
        self.pay_lines = pay_lines  # ex: 3x5。3x5的111...array

        self.show_score = show_score
        self.trigger_freespins = trigger_freespins

        # by game
        self.arr_sticky_symbol = arr_sticky_symbol
        self.arr_sticky_posi = arr_sticky_posi
        self.trigger_feature = trigger_feature


class MathStatus:
    """
    Game使用的主要資料，遊戲中會變動的資料
    """

    def __init__(self) -> None:
        # basic
        """
        0 : base game
        1 : base game feature
        2 : free game
        3 : free game feature 1
        4 : free game feature 2
        5 : free game feature 3
        """
        self.game_type = 0
        """
        0 : base 
        1 : feature 1, stack 1
        2 : feature 2, stack 2
        3 : feature 3, stack 3
        """
        self.game_type_feature = 0

        self.credit = 20000  # 表底

        self.cnt_spins = 0  # BG累積轉數
        self.cnt_hits = 0  # BG hit times(不包含FG)

        self.math_res = MathResult()

        # free game
        self.freegame_coin = 0
        self.have_free_spins = 0  # 這場FG有幾次spins
        self.cnt_free_spins = 0  # 該場FG進行了幾次spin
        self.cnt_trigger_freegame_times = 0  # 玩了幾場FG

        # max
        self.max_score_basegame = 0  # 單把最大分數(BG)
        self.max_score_freegame = 0  # 單把最大分數(FG)

        # by game
        self.arr_sticky_symbol = np.zeros(arr_shape)
        self.arr_sticky_posi = np.zeros(arr_shape)

    def one_spin(self):
        # [判斷遊戲模式]

        # free game
        if (self.game_type == 0 and self.math_res.trigger_freespins > 0) or (self.have_free_spins > self.cnt_free_spins):  # 在BG有freespins或在FG還有freespins
            if self.math_res.trigger_feature == 0:
                self.game_type = 2
            elif self.math_res.trigger_feature == 1:
                self.game_type = 3
            elif self.math_res.trigger_feature == 2:
                self.game_type = 4
            elif self.math_res.trigger_feature == 3:
                self.game_type = 5

        # base game
        else:
            if self.math_res.trigger_feature == 0:
                self.game_type = 0
            elif self.math_res.trigger_feature == 3:
                self.game_type = 1
            else:
                self.game_type = 0
                print("ERROR: " + "game_type")

            # clear free game data
            self.credit += self.freegame_coin
            self.freegame_coin = 0
            self.have_free_spins = 0
            self.cnt_free_spins = 0

        # spin
        if self.game_type in [0, 1]:
            self.math_res = basegame_spin_and_calculate()
            # self.init_sticky()
        elif self.game_type in [2, 3, 4, 5]:
            self.math_res = freegame_spin_and_calculate()
            # self.update_sticky()
        else:
            print("no spin")

        # [update]
        # - free spin
        if self.math_res.trigger_freespins > 0:
            self.cnt_trigger_freegame_times += 1
            self.have_free_spins += self.math_res.trigger_freespins
            if self.have_free_spins >= max_freespins:
                self.have_free_spins = max_freespins

        # - 改變顯示的分數
        if self.game_type in [0, 1]:
            self.credit -= coin_in
            self.credit += self.math_res.show_score
            if self.math_res.show_score > 0:
                self.cnt_hits += 1
            if self.math_res.show_score > self.max_score_basegame:
                self.math_res.max_score_basegame = self.math_res.show_score
            self.cnt_spins += 1
        elif self.game_type in [2, 3, 4]:
            self.freegame_coin += self.math_res.show_score
            if self.math_res.show_score > self.max_score_freegame:
                self.math_res.max_score_freegame = self.math_res.show_score
            self.cnt_free_spins += 1

    def init_sticky(self):
        self.arr_sticky_symbol = np.zeros(arr_shape)
        self.arr_sticky_posi = np.zeros(arr_shape)

    def update_sticky(self):
        self.arr_sticky_symbol = self.math_res.arr_sticky_symbol
        self.arr_sticky_posi = self.math_res.arr_sticky_posi


show_log = True


# %% ----- [Function] Demo Game Use -----

if True:

    # [1] tools
    def get_value(cum_weight):
        """
        丟累積的weight, output第幾個
        """
        rd = np.random.randint(0, cum_weight[-1])
        for i in range(len(cum_weight)):
            if rd < cum_weight[i]:
                return i

        return get_value(cum_weight)

    def generate_payline(shape):
        """
        設定array大小，隨機生成走線
        """
        row, column = shape
        arr = np.zeros(shape)
        for j in range(column):
            rd_i = np.random.randint(0, row)
            arr[rd_i, j] = 1

        return arr

    def extend_arr_num(arr, new_shape, fill_num=0):
        """
        將輪帶擴展，補任意數字，預設0
        -
        arr : 要擴大的array \n
        new_shape : 要轉換的新的大小
        fill_num : 要補的數字
        """
        new_arr = np.full(new_shape, fill_num)
        # new_arr = np.zeros(new_shape)

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

    def generate_num_and_blank(new_shape, fill_list, fill_num, blank_num=0):
        """
        將輪帶擴展，補任意數字，預設0
        -
        arr : 要擴大的array \n
        new_shape : 要轉換的新的大小
        fill_num : 要補的數字
        """
        new_arr = np.full(new_shape, blank_num)
        # new_arr = np.zeros(new_shape)

        row, column = new_arr.shape
        for j in range(column):
            for i in range(fill_list[j]):
                new_arr[-(i + 1), j] = fill_num

        return new_arr

    def print_result(game_type, arr, rng, score, uup):
        if show_log:
            print("\n====================\n")
            print("* game type: \n   ", game_type)
            print("* rng: ")
            print("    [", end="")
            for i in rng:
                print("{:3.0f}".format(i), end=" ")
            print("]")

            print("* score: ", score)
            print("* uup:")
            print("    [", end="")
            for i in uup:
                print("{:3.0f}".format(i), end=" ")
            print("]")

            print("* arr_result:")
            for i in arr:
                print("    [", end="")
                for j in i:
                    print("{:3.0f}".format(j), end=" ")
                print("]")

    # -- by game
    def add_base_array(rng, game_type):
        new_shape = (GS.show_arr_len, reel_num)
        arr = np.zeros(new_shape)

        if game_type == 0:
            for i in range(GS.show_arr_len):
                arr[i, 0] = B1R1[(rng[0] + i) % B1R1_len]
                arr[i, 1] = B1R2[(rng[1] + i) % B1R2_len]
                arr[i, 2] = B1R3[(rng[2] + i) % B1R3_len]
                arr[i, 3] = B1R4[(rng[3] + i) % B1R4_len]
                arr[i, 4] = B1R5[(rng[4] + i) % B1R5_len]
        elif game_type == 1:
            for i in range(GS.show_arr_len):
                arr[i, 0] = B2R1[(rng[0] + i) % B2R1_len]
                arr[i, 1] = B2R2[(rng[1] + i) % B2R2_len]
                arr[i, 2] = B2R3[(rng[2] + i) % B2R3_len]
                arr[i, 3] = B2R4[(rng[3] + i) % B2R4_len]
                arr[i, 4] = B2R5[(rng[4] + i) % B2R5_len]
        elif game_type == 2:
            for i in range(GS.show_arr_len):
                arr[i, 0] = F1R1[(rng[0] + i) % F1R1_len]
                arr[i, 1] = F1R2[(rng[1] + i) % F1R2_len]
                arr[i, 2] = F1R3[(rng[2] + i) % F1R3_len]
                arr[i, 3] = F1R4[(rng[3] + i) % F1R4_len]
                arr[i, 4] = F1R5[(rng[4] + i) % F1R5_len]
        elif game_type == 3:
            for i in range(GS.show_arr_len):
                arr[i, 0] = F2R1[(rng[0] + i) % F2R1_len]
                arr[i, 1] = F2R2[(rng[1] + i) % F2R2_len]
                arr[i, 2] = F2R3[(rng[2] + i) % F2R3_len]
                arr[i, 3] = F2R4[(rng[3] + i) % F2R4_len]
                arr[i, 4] = F2R5[(rng[4] + i) % F2R5_len]
        elif game_type == 4:
            for i in range(GS.show_arr_len):
                arr[i, 0] = F3R1[(rng[0] + i) % F3R1_len]
                arr[i, 1] = F3R2[(rng[1] + i) % F3R2_len]
                arr[i, 2] = F3R3[(rng[2] + i) % F3R3_len]
                arr[i, 3] = F3R4[(rng[3] + i) % F3R4_len]
                arr[i, 4] = F3R5[(rng[4] + i) % F3R5_len]
        elif game_type == 5:
            for i in range(GS.show_arr_len):
                arr[i, 0] = F4R1[(rng[0] + i) % F4R1_len]
                arr[i, 1] = F4R2[(rng[1] + i) % F4R2_len]
                arr[i, 2] = F4R3[(rng[2] + i) % F4R3_len]
                arr[i, 3] = F4R4[(rng[3] + i) % F4R4_len]
                arr[i, 4] = F4R5[(rng[4] + i) % F4R5_len]

        return arr

    def symbol_trans(arr, symbol_before, symbol_after):
        shape = arr.shape

        for i in range(shape[0]):
            for j in range(shape[1]):
                if arr[i, j] == symbol_before:
                    arr[i, j] = symbol_after

    # -- fake data (不一定要有)
    def generate_fake_math_res_basegame(symbol=0):
        #
        show_window_shape = (GS.show_arr_len, reel_num)

        #
        game_type = 0
        rng = np.array([0, 0, 0, 0, 0])
        # arr_result = np.zeros(show_window_shape)

        row, column = show_window_shape
        li = [symbol for i in range(row * column)]
        # li = [np.random.randint(0, len(symbols)) for i in range(row * column)]

        arr_result = np.array(li).reshape(show_window_shape)

        score = 404

        pay_lines = []
        for i in range(3):
            show_text = "no setting."
            pay_line = generate_payline(arr_shape)
            pay_line_extend = extend_arr_num(pay_line, show_window_shape)
            pay_lines.append((pay_line_extend, show_text))

        trigger_freespins = 2

        #
        math_res = MathResult(game_type, rng, arr_result, pay_lines, score, trigger_freespins)
        return math_res

    def generate_fake_math_res_freegame(symbol=0):
        #
        show_window_shape = (GS.show_arr_len, reel_num)

        #
        game_type = 1
        rng = np.array([0, 0, 0, 0, 0])
        # arr_result = np.zeros(show_window_shape)

        row, column = show_window_shape
        li = [symbol for i in range(row * column)]
        # li = [np.random.randint(0, len(symbols)) for i in range(row * column)]
        arr_result = np.array(li).reshape(show_window_shape)

        arr_result_2 = arr_result.copy()[: arr_shape_show[0]]

        print("---------------")
        print(arr_result)

        score = multi[get_value(multi_weight_cum)] * coin_in

        pay_lines = []
        # for i in range(3):
        #     show_text = "no setting."
        #     pay_line = generate_payline(arr_shape)
        #     pay_line_extend = extend_arr_num(pay_line, show_window_shape)
        #     pay_lines.append((pay_line_extend, show_text))

        trigger_freespins = 0

        arr_result_sticky = np.zeros(arr_shape)
        pay_lines_sticky = generate_arr(arr_shape, (0, 2))

        #
        math_res = MathResult(game_type, rng, arr_result, arr_result_2, pay_lines, score, trigger_freespins, arr_result_sticky, pay_lines_sticky)

        return math_res


# [2] main
def basegame_spin_and_calculate(show_info=""):

    rng = np.zeros(reel_num, dtype=np.int64)
    arr_result = np.zeros((window_size, reel_num), dtype=np.int64)

    # ------------ "MathResult" data ------------

    trans_symbols = [99, 99]  # MY, FE
    arr_result_uup = np.array([0, 0, 0, 0, 0])

    # ------------ "MathResult" data ------------

    if True:

        # tool
        def get_value(cum_weight):
            """
            get random index of value by cumulative weight.

            input cum Weight, output random index(position).

            Examples
            --------
            >>> get_value([1,3,5])
            2

            Test
            --------
            aa = [0, 0, 0, 0, 0]
            bb = np.array([60, 30, 10, 1, 1]).cumsum()
            # bb = np.array([1, 2, 3, 4, 5]).cumsum()

            tt = 10**5
            for i in range(tt):
                cc = get_value(bb)
                # print(cc)
                aa[cc] += 1

            np.array(aa)/tt
            """
            rd = np.random.randint(0, cum_weight[-1])
            for i in range(len(cum_weight)):
                if rd < cum_weight[i]:
                    return i

        def check_unique(arr, check_range):
            check_list = arr[:, 0]
            unique_symbol = 99  # 99=沒有
            cnt = 0

            for s in check_list:
                if unique_symbol == 99 and s in check_range:
                    unique_symbol = s
                    cnt = 1
                elif s in check_range:
                    if unique_symbol == s:
                        cnt += 1
                    else:
                        unique_symbol = 99
                        cnt = 0
                        break

            return unique_symbol, cnt

        # game
        def rng_generator(game_type):
            """
            生成RNG
            """
            if game_type == 0:
                rng[0] = np.random.randint(B1R1_len)
                rng[1] = np.random.randint(B1R2_len)
                rng[2] = np.random.randint(B1R3_len)
                rng[3] = np.random.randint(B1R4_len)
                rng[4] = np.random.randint(B1R5_len)
            elif game_type == 1:
                rng[0] = np.random.randint(B2R1_len)
                rng[1] = np.random.randint(B2R2_len)
                rng[2] = np.random.randint(B2R3_len)
                rng[3] = np.random.randint(B2R4_len)
                rng[4] = np.random.randint(B2R5_len)
            elif game_type == 2:
                rng[0] = np.random.randint(B3R1_len)
                rng[1] = np.random.randint(B3R2_len)
                rng[2] = np.random.randint(B3R3_len)
                rng[3] = np.random.randint(B3R4_len)
                rng[4] = np.random.randint(B3R5_len)
            elif game_type == 98:  # feature
                rng[0] = 20
                rng[1] = 3
                rng[2] = 13
                rng[3] = 0
                rng[4] = 0
            elif game_type == 99:  # feature
                rng[0] = 6
                rng[1] = 0
                rng[2] = 0
                rng[3] = 0
                rng[4] = 0

        def arr_result_generator(game_type):
            """
            生成盤面
            """
            if game_type == 0:
                for i in range(window_size):
                    arr_result[i, 0] = B1R1[(rng[0] + i) % B1R1_len]
                    arr_result[i, 1] = B1R2[(rng[1] + i) % B1R2_len]
                    arr_result[i, 2] = B1R3[(rng[2] + i) % B1R3_len]
                    arr_result[i, 3] = B1R4[(rng[3] + i) % B1R4_len]
                    arr_result[i, 4] = B1R5[(rng[4] + i) % B1R5_len]
            elif game_type == 1:
                for i in range(window_size):
                    arr_result[i, 0] = B2R1[(rng[0] + i) % B2R1_len]
                    arr_result[i, 1] = B2R2[(rng[1] + i) % B2R2_len]
                    arr_result[i, 2] = B2R3[(rng[2] + i) % B2R3_len]
                    arr_result[i, 3] = B2R4[(rng[3] + i) % B2R4_len]
                    arr_result[i, 4] = B2R5[(rng[4] + i) % B2R5_len]
            elif game_type == 2:
                for i in range(window_size):
                    arr_result[i, 0] = B3R1[(rng[0] + i) % B3R1_len]
                    arr_result[i, 1] = B3R2[(rng[1] + i) % B3R2_len]
                    arr_result[i, 2] = B3R3[(rng[2] + i) % B3R3_len]
                    arr_result[i, 3] = B3R4[(rng[3] + i) % B3R4_len]
                    arr_result[i, 4] = B3R5[(rng[4] + i) % B3R5_len]

        def get_waygame_multi(symbol, row_list):
            """
            取得單一輪"way game"倍數
            """
            if symbol == WW or symbol == C1:
                return 0

            mul = 0
            for s in row_list:
                if s == symbol or s == WW:
                    mul += 1

            if mul == 0:
                mul = 1

            return mul

        def get_power_up_multi(symbol, row_list):
            """
            取得單一輪"power up"倍數
            """
            if symbol == WW or symbol == C1:
                return 0

            mul = 0
            cnt = 0
            for s in row_list:
                if symbol == s:
                    cnt += 1
                else:
                    if s == WW:
                        mul += 1
                    if cnt != 0:
                        mul += power_up_value[cnt - 1]
                        cnt = 0

            if cnt != 0:
                mul += power_up_value[cnt - 1]

            return mul

        def get_uup_multi(symbol, row_list, add_num):
            """
            取得單一輪"power up"倍數
            """
            if symbol == WW or symbol == C1:
                return 0

            mul = 0
            cnt = 0
            add = 0
            for s in row_list:
                if symbol == s:
                    cnt += 1
                else:
                    if s == WW:
                        mul += 1
                    if cnt != 0:
                        mul += power_up_value[cnt + add_num - 1]
                        cnt = 0
                        add = add_num

            if cnt != 0:
                mul += power_up_value[cnt + add_num - 1]
                add = add_num

            return mul, add

        # base game & record
        def calculate_win_c1_bg():
            # bonus : 由最左至右連續出現
            line = 0
            for reel in arr_result.T:
                if C1 in reel or WW in reel:  # WW可以代替C1
                    line += 1
                    continue
                else:
                    break

            # # scatter : 出現在隨機位置
            # line = 0
            # for row in arr_result:
            #     for s in row:
            #         if s == C1:
            #             line += 1

            if line >= 3:
                pay_c1 = pay_table[C1][line - 1] * coin_in
                return pay_c1, True
            else:
                return 0, False

        def calculate_win_bg(is_uup, table):
            """
            盤面算分(power up)
            """
            pay_sum = 0
            for symbol in symbols_score:
                # 計算連線(line)
                line = 0
                for i in range(reel_num):
                    check_list = arr_result[:, i]
                    if symbol in check_list or WW in check_list:
                        line += 1
                    else:
                        break

                # 計算倍數(combo)
                mul_cum = 1
                for i in range(reel_num):
                    check_list = arr_result[:, i]
                    if symbol in check_list or WW in check_list:
                        # game type (0: way game, 1: power up, 2: power up and up)
                        if is_uup and uup_vaild_reel[i] == 1:  # 2
                            add = 0
                            if table == 0:
                                add = get_value(weight_cum_uup_b31[:, i])
                            elif table == 1:
                                add = get_value(weight_cum_uup_b32[:, i])
                            mul, add_num = get_uup_multi(symbol, check_list, add)
                            arr_result_uup[i] = add_num

                        elif (symbol in symbols_m) and (symbol in symbols_powerup):  # 1
                            mul = get_power_up_multi(symbol, check_list)

                        else:  # 0
                            mul = get_waygame_multi(symbol, check_list)

                        mul_cum *= mul
                    else:
                        break

                # 算分+紀錄output
                if line >= 1:
                    pay_symbol = pay_table[symbol][line - 1] * mul_cum
                    pay_sum += pay_symbol

            return pay_sum

        def one_spin_feature_bg(trigger_symbol):
            table = get_value(weight_cum_table_BG)

            # spin
            rng_generator(1 + table)
            arr_result_generator(1 + table)

            # transfer
            for i in range(window_size):
                for j in range(reel_num):
                    if arr_result[i, j] == FE:
                        arr_result[i, j] = trigger_symbol

            for i in range(window_size):
                arr_result[i, 0] = 99

            for i in range(3):
                arr_result[i, 0] = trigger_symbol

            # calculate
            score_base = calculate_win_bg(True, table)
            score = score_base

            print_result("base game - feature", arr_result, rng, score, arr_result_uup)
            return score

        def one_spin_bg():
            # spin
            rng_generator(0)
            arr_result_generator(0)

            # transfer
            rd_my = get_value(weight_cum_my) + 2
            for i in range(window_size):
                for j in range(reel_num):
                    if arr_result[i, j] == MY:
                        arr_result[i, j] = rd_my

            trans_symbols[0] = rd_my

            # check trigger feature (full reel)
            feature_data = check_unique(arr_result, symbols_m)
            trans_symbols[1] = feature_data[0]

            # calculate
            score = 0
            trigger_freegame = False
            if feature_data[1] == 3 and (feature_data[0] in symbols_powerup):  # trigger feature
                score = one_spin_feature_bg(feature_data[0])
                game_type = 1
            else:
                score_c1, trigger_freegame = calculate_win_c1_bg()
                score_base = calculate_win_bg(False, 0)
                score = score_c1 + score_base
                game_type = 0
                print_result("base game", arr_result, rng, score, arr_result_uup)

            return score, trigger_freegame, game_type

    # spin
    score, trigger, game_type = one_spin_bg()

    # ------------ "MathResult" data ------------

    # 正常版
    arr_result = add_base_array(rng, game_type)
    arr_result = np.concatenate([generate_num_and_blank((5, 5), arr_result_uup, trans_symbols[1], 99), arr_result])
    symbol_trans(arr_result, FE, trans_symbols[1])
    symbol_trans(arr_result, MY, trans_symbols[0])

    arr_result_2 = arr_result.copy()[: arr_shape_show[0]]

    # # MY
    # arr_result = add_base_array(rng, game_type)
    # arr_result = np.concatenate([generate_num_and_blank((5, 5), arr_result_uup, trans_symbols[1], 99), arr_result])
    # symbol_trans(arr_result, FE, trans_symbols[1])

    # arr_result_2 = arr_result.copy()[: arr_shape_show[0]]
    # symbol_trans(arr_result_2, MY, trans_symbols[0])

    pay_lines = []

    trigger_freespins = free_spins if trigger else 0
    # trigger_freespins = 2 if trigger else 0  # 從倍率線型拉分數

    math_res = MathResult(game_type, rng, arr_result, arr_result_2, pay_lines, score, trigger_freespins)
    # math_res = generate_fake_math_res_basegame(0)

    # ------------ "MathResult" data ------------

    return math_res


def freegame_spin_and_calculate(show_info=""):

    # ------------ "MathResult" data ------------

    trans_symbols = [99, 99]  # MY, FE
    arr_result_uup = np.array([0, 0, 0, 0, 0])

    # ------------ "MathResult" data ------------

    rng = np.zeros(reel_num, np.int64)
    arr_result = np.zeros(arr_shape, np.int64)

    if True:

        # pre-setting
        rng = np.zeros(reel_num, np.int64)
        arr_result = np.zeros(arr_shape, np.int64)

        # tool
        def get_value(cum_weight):
            """
            get random index of value by cumulative weight.

            input cum Weight, output random index(position).

            Examples
            --------
            >>> get_value([1,3,5])
            2

            Test
            --------
            aa = [0, 0, 0, 0, 0]
            bb = np.array([60, 30, 10, 1, 1]).cumsum()
            # bb = np.array([1, 2, 3, 4, 5]).cumsum()

            tt = 10**5
            for i in range(tt):
                cc = get_value(bb)
                # print(cc)
                aa[cc] += 1

            np.array(aa)/tt
            """
            rd = np.random.randint(0, cum_weight[-1])
            for i in range(len(cum_weight)):
                if rd < cum_weight[i]:
                    return i

        def check_unique(arr, check_range):
            check_list = arr[:, 0]
            unique_symbol = 99  # 99=沒有
            cnt = 0

            for s in check_list:
                if unique_symbol == 99 and s in check_range:
                    unique_symbol = s
                    cnt = 1
                elif s in check_range:
                    if unique_symbol == s:
                        cnt += 1
                    else:
                        unique_symbol = 99
                        cnt = 0
                        break

            return unique_symbol, cnt

        # game
        def rng_generator(game_type):
            """
            生成RNG
            """
            if game_type == 0:
                rng[0] = np.random.randint(B1R1_len)
                rng[1] = np.random.randint(B1R2_len)
                rng[2] = np.random.randint(B1R3_len)
                rng[3] = np.random.randint(B1R4_len)
                rng[4] = np.random.randint(B1R5_len)
            elif game_type == 1:
                rng[0] = np.random.randint(B2R1_len)
                rng[1] = np.random.randint(B2R2_len)
                rng[2] = np.random.randint(B2R3_len)
                rng[3] = np.random.randint(B2R4_len)
                rng[4] = np.random.randint(B2R5_len)
            elif game_type == 2:
                rng[0] = np.random.randint(B3R1_len)
                rng[1] = np.random.randint(B3R2_len)
                rng[2] = np.random.randint(B3R3_len)
                rng[3] = np.random.randint(B3R4_len)
                rng[4] = np.random.randint(B3R5_len)
            elif game_type == 3:
                rng[0] = np.random.randint(F1R1_len)
                rng[1] = np.random.randint(F1R2_len)
                rng[2] = np.random.randint(F1R3_len)
                rng[3] = np.random.randint(F1R4_len)
                rng[4] = np.random.randint(F1R5_len)
            elif game_type == 4:
                rng[0] = np.random.randint(F2R1_len)
                rng[1] = np.random.randint(F2R2_len)
                rng[2] = np.random.randint(F2R3_len)
                rng[3] = np.random.randint(F2R4_len)
                rng[4] = np.random.randint(F2R5_len)
            elif game_type == 5:
                rng[0] = np.random.randint(F3R1_len)
                rng[1] = np.random.randint(F3R2_len)
                rng[2] = np.random.randint(F3R3_len)
                rng[3] = np.random.randint(F3R4_len)
                rng[4] = np.random.randint(F3R5_len)
            elif game_type == 6:
                rng[0] = np.random.randint(F4R1_len)
                rng[1] = np.random.randint(F4R2_len)
                rng[2] = np.random.randint(F4R3_len)
                rng[3] = np.random.randint(F4R4_len)
                rng[4] = np.random.randint(F4R5_len)
            elif game_type == 7:
                rng[0] = np.random.randint(F5R1_len)
                rng[1] = np.random.randint(F5R2_len)
                rng[2] = np.random.randint(F5R3_len)
                rng[3] = np.random.randint(F5R4_len)
                rng[4] = np.random.randint(F5R5_len)

        def arr_result_generator(game_type):
            """
            生成盤面
            """
            if game_type == 0:
                for i in range(window_size):
                    arr_result[i, 0] = B1R1[(rng[0] + i) % B1R1_len]
                    arr_result[i, 1] = B1R2[(rng[1] + i) % B1R2_len]
                    arr_result[i, 2] = B1R3[(rng[2] + i) % B1R3_len]
                    arr_result[i, 3] = B1R4[(rng[3] + i) % B1R4_len]
                    arr_result[i, 4] = B1R5[(rng[4] + i) % B1R5_len]
            elif game_type == 1:
                for i in range(window_size):
                    arr_result[i, 0] = B2R1[(rng[0] + i) % B2R1_len]
                    arr_result[i, 1] = B2R2[(rng[1] + i) % B2R2_len]
                    arr_result[i, 2] = B2R3[(rng[2] + i) % B2R3_len]
                    arr_result[i, 3] = B2R4[(rng[3] + i) % B2R4_len]
                    arr_result[i, 4] = B2R5[(rng[4] + i) % B2R5_len]
            elif game_type == 2:
                for i in range(window_size):
                    arr_result[i, 0] = B3R1[(rng[0] + i) % B3R1_len]
                    arr_result[i, 1] = B3R2[(rng[1] + i) % B3R2_len]
                    arr_result[i, 2] = B3R3[(rng[2] + i) % B3R3_len]
                    arr_result[i, 3] = B3R4[(rng[3] + i) % B3R4_len]
                    arr_result[i, 4] = B3R5[(rng[4] + i) % B3R5_len]
            elif game_type == 3:
                for i in range(window_size):
                    arr_result[i, 0] = F1R1[(rng[0] + i) % F1R1_len]
                    arr_result[i, 1] = F1R2[(rng[1] + i) % F1R2_len]
                    arr_result[i, 2] = F1R3[(rng[2] + i) % F1R3_len]
                    arr_result[i, 3] = F1R4[(rng[3] + i) % F1R4_len]
                    arr_result[i, 4] = F1R5[(rng[4] + i) % F1R5_len]
            elif game_type == 4:
                for i in range(window_size):
                    arr_result[i, 0] = F2R1[(rng[0] + i) % F2R1_len]
                    arr_result[i, 1] = F2R2[(rng[1] + i) % F2R2_len]
                    arr_result[i, 2] = F2R3[(rng[2] + i) % F2R3_len]
                    arr_result[i, 3] = F2R4[(rng[3] + i) % F2R4_len]
                    arr_result[i, 4] = F2R5[(rng[4] + i) % F2R5_len]
            elif game_type == 5:
                for i in range(window_size):
                    arr_result[i, 0] = F3R1[(rng[0] + i) % F3R1_len]
                    arr_result[i, 1] = F3R2[(rng[1] + i) % F3R2_len]
                    arr_result[i, 2] = F3R3[(rng[2] + i) % F3R3_len]
                    arr_result[i, 3] = F3R4[(rng[3] + i) % F3R4_len]
                    arr_result[i, 4] = F3R5[(rng[4] + i) % F3R5_len]
            elif game_type == 6:
                for i in range(window_size):
                    arr_result[i, 0] = F4R1[(rng[0] + i) % F4R1_len]
                    arr_result[i, 1] = F4R2[(rng[1] + i) % F4R2_len]
                    arr_result[i, 2] = F4R3[(rng[2] + i) % F4R3_len]
                    arr_result[i, 3] = F4R4[(rng[3] + i) % F4R4_len]
                    arr_result[i, 4] = F4R5[(rng[4] + i) % F4R5_len]
            elif game_type == 7:
                for i in range(window_size):
                    arr_result[i, 0] = F5R1[(rng[0] + i) % F5R1_len]
                    arr_result[i, 1] = F5R2[(rng[1] + i) % F5R2_len]
                    arr_result[i, 2] = F5R3[(rng[2] + i) % F5R3_len]
                    arr_result[i, 3] = F5R4[(rng[3] + i) % F5R4_len]
                    arr_result[i, 4] = F5R5[(rng[4] + i) % F5R5_len]

        def get_waygame_multi(symbol, row_list):
            """
            取得單一輪"way game"倍數
            """
            if symbol == WW or symbol == C1:
                return 0

            mul = 0
            for s in row_list:
                if s == symbol or s == WW:
                    mul += 1

            if mul == 0:
                mul = 1

            return mul

        def get_power_up_multi(symbol, row_list):
            """
            取得單一輪"power up"倍數
            """
            if symbol == WW or symbol == C1:
                return 0

            mul = 0
            cnt = 0
            for s in row_list:
                if symbol == s:
                    cnt += 1
                else:
                    if s == WW:
                        mul += 1
                    if cnt != 0:
                        mul += power_up_value[cnt - 1]
                        cnt = 0

            if cnt != 0:
                mul += power_up_value[cnt - 1]

            return mul

        def get_uup_multi(symbol, row_list, add_num):
            """
            取得單一輪"power up"倍數
            """
            if symbol == WW or symbol == C1:
                return 0

            mul = 0
            cnt = 0
            add = 0
            for s in row_list:
                if symbol == s:
                    cnt += 1
                else:
                    if s == WW:
                        mul += 1
                    if cnt != 0:
                        mul += power_up_value[cnt + add_num - 1]
                        cnt = 0
                        add = add_num

            if cnt != 0:
                mul += power_up_value[cnt + add_num - 1]
                add = add_num

            return mul, add

        # free game & record
        def calculate_win_c1_fg():
            # bonus : 由最左至右連續出現
            line = 0
            for reel in arr_result.T:
                if C1 in reel or WW in reel:  # WW可以代替C1
                    line += 1
                    continue
                else:
                    break

            # # scatter : 出現在隨機位置
            # line = 0
            # for row in arr_result:
            #     for s in row:
            #         if s == C1:
            #             line += 1

            if line >= 3:
                pay_c1 = pay_table[C1][line - 1] * coin_in

                return pay_c1, True
            else:
                return 0, False

        def calculate_win_fg(trigger_stack, table):
            """
            盤面算分(power up)
            """
            pay_sum = 0
            for symbol in symbols_score:
                # 計算連線
                line = 0
                for i in range(reel_num):
                    check_list = arr_result[:, i]
                    if symbol in check_list or WW in check_list:
                        line += 1
                    else:
                        break

                # 計算倍數
                mul_cum = 1
                for i in range(reel_num):
                    check_list = arr_result[:, i]
                    if symbol in check_list or WW in check_list:
                        # game type (0: way game, 1: power up, 2: power up and up)
                        if trigger_stack != 0 and uup_vaild_reel[i] == 1:  # 2
                            add = 0

                            # level 1
                            if trigger_stack == 1:
                                add = get_value(weight_cum_uup_f11_level1[:, i])
                            elif trigger_stack == 2:
                                add = get_value(weight_cum_uup_f21_level1[:, i])
                            elif trigger_stack == 3 and table == 0:
                                add = get_value(weight_cum_uup_f31_level1[:, i])
                            elif trigger_stack == 3 and table == 1:
                                add = get_value(weight_cum_uup_f32_level1[:, i])

                            # level 2
                            if line >= 5:
                                if trigger_stack == 1:
                                    add += get_value(weight_cum_uup_f11_level2[:, i])
                                elif trigger_stack == 2:
                                    add += get_value(weight_cum_uup_f21_level2[:, i])
                                elif trigger_stack == 3 and table == 0:
                                    add += get_value(weight_cum_uup_f31_level2[:, i])
                                elif trigger_stack == 3 and table == 1:
                                    add += get_value(weight_cum_uup_f32_level2[:, i])

                            mul, uup_add = get_uup_multi(symbol, check_list, add)
                            arr_result_uup[i] = uup_add

                        elif (symbol in symbols_m) and (symbol in symbols_powerup):  # 1
                            mul = get_power_up_multi(symbol, check_list)

                        else:  # 0
                            mul = get_waygame_multi(symbol, check_list)

                        mul_cum *= mul
                    else:
                        break

                if line >= 1:
                    pay_symbol = pay_table[symbol][line - 1] * mul_cum
                    pay_sum += pay_symbol

            return pay_sum

        def one_spin_feature_fg(feature_data):
            table = get_value(weight_cum_table_FG)
            trigger_symbol, trigger_stack = feature_data

            reel_id = 3 + trigger_stack
            if trigger_stack == 3:
                reel_id += table

            rng_generator(reel_id)
            arr_result_generator(reel_id)

            # transfer
            for i in range(window_size):
                for j in range(reel_num):
                    if arr_result[i, j] == FE:
                        arr_result[i, j] = trigger_symbol

            for i in range(window_size):
                arr_result[i, 0] = 99

            for i in range(trigger_stack):
                arr_result[i, 0] = trigger_symbol

            # calculate
            score_base = calculate_win_fg(trigger_stack, table)
            score = score_base

            print(arr_result)
            print_result(f"[{feature_data[1]+2}]free game - feature", arr_result, rng, score, arr_result_uup)

            return score

        def one_spin_fg():
            # spin
            rng_generator(3)
            arr_result_generator(3)

            feature_data = check_unique(arr_result, symbols_m)
            trans_symbols[1] = feature_data[0]

            # calculate
            score = 0
            trigger_freegame = False
            if feature_data[1] == 0 or (feature_data[0] not in symbols_powerup):
                score_c1, trigger_freegame = calculate_win_c1_fg()
                score_base = calculate_win_fg(0, 0)
                score = score_c1 + score_base

                # MathResult
                game_type = 2
                print_result(f"[{game_type}] free game", arr_result, rng, score, arr_result_uup)
            else:
                # trigger feature
                score = one_spin_feature_fg(feature_data)

                # MathResult
                game_type = feature_data[1] + 2

            return score, trigger_freegame, game_type

    # spin
    score, trigger, game_type = one_spin_fg()

    # ------------ "MathResult" data ------------

    arr_result = add_base_array(rng, game_type)

    if game_type == 3:
        for i in range(2):
            arr_result[i, 0] = 7
    elif game_type == 4:
        for i in range(1):
            arr_result[i, 0] = 7

    arr_result = np.concatenate([generate_num_and_blank((5, 5), arr_result_uup, trans_symbols[1], 99), arr_result])
    symbol_trans(arr_result, FE, trans_symbols[1])

    arr_result_2 = arr_result.copy()[: arr_shape_show[0]]

    pay_lines = []

    trigger_freespins = free_spins if trigger else 0
    # trigger_freespins = 2 if trigger else 0  # 從倍率線型拉分數

    math_res = MathResult(game_type, rng, arr_result, arr_result_2, pay_lines, score, trigger_freespins)
    # math_res = generate_fake_math_res_basegame(0)

    # ------------ "MathResult" data ------------

    return math_res


# [3] chaeck
def check_func(total_round):

    total_score = 0
    for i in range(total_round):

        # base game
        math_res = basegame_spin_and_calculate()
        total_score += math_res.show_score

        # free game
        if math_res.trigger_freespins / free_spins == 1:
            total_trigger_time = 1
            freegame_time = 0

            # 判斷最大場次
            if freegame_time >= max_freegame:
                break

            # 判斷有幾場
            if total_trigger_time <= freegame_time:
                break

            # 開始免費遊戲
            for j in range(free_spins):
                math_res = freegame_spin_and_calculate()
                total_score += math_res.show_score
                total_trigger_time += math_res.trigger_freespins / free_spins

            freegame_time += 1

    print("RTP: ", total_score / total_round / coin_in)


# total_round = 10**4
# check_func(total_round)


# %%
