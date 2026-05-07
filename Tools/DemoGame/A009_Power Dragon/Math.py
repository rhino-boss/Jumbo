# %% ----- Import -----


import pandas as pd
import numpy as np

import GameSetting as GS
from GameSetting import GAME_TYPE as GT

# my package
from Tool.RedBox import log_use
import Tool.Math as mat


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


# [configure]
if True:
    # simulate setting
    model_id = "A009"
    slot_name = "包你發 龍門天下"
    version = "0001"

    window_size_bg = 3  # base game
    reel_num_bg = 5
    arr_shape_bg = (window_size_bg, reel_num_bg)

    window_size_fg = 4  # free game
    reel_num_fg = 5
    arr_shape_fg = (window_size_fg, reel_num_fg)

    free_spins = 8
    max_freegame = 5  # 最大free game場數
    max_freespins = free_spins * max_freegame  # 最大free spin次數

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

    symbols_special = np.array([WW, C1], dtype=np.int64)  # WW, C1
    symbols_m = np.array([M1, M2, M3, M4, M5], dtype=np.int64)  # M1, M2, M3, M4, M5
    symbols_number = np.array([A, K, Q, J], dtype=np.int64)  # A, K, Q, J

    symbols_score = np.concatenate([symbols_m, symbols_number])
    symbols = np.concatenate([symbols_special, symbols_m, symbols_number])

    # demo game setting
    game_scene = {
        GS.GAME_TYPE.BaseGame: [0],
        GS.GAME_TYPE.FreeGame: [1],
    }

    arr_shape_show = (4, reel_num_bg)
    rng_freegame = np.array([23, 79, 21, 0, 0], np.int16)
    # rng_feature = np.array([3,6,14,14,10], np.int16)


# [strip]
if True:
    BGR1, BGR2, BGR3, BGR4, BGR5, *_length = __get_strip(GS.path_math_data, "strip_BG", 0)
    BGR1_len, BGR2_len, BGR3_len, BGR4_len, BGR5_len = _length

    FGR1, FGR2, FGR3, FGR4, FGR5, *_length = __get_strip(GS.path_math_data, "strip_FG", 0)
    FGR1_len, FGR2_len, FGR3_len, FGR4_len, FGR5_len = _length


# [pay table]
pay_table, symbol_str, symbol_id, symbols_powerup = __get_paytable(GS.path_math_data, "pay_table")

# [feature]
if True:
    power_up_value = __get_power_up(GS.path_math_data, "power_value")


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
        rng=np.zeros(reel_num_bg),
        arr_result=np.zeros(shape=arr_shape_bg),
        arr_result_2=np.zeros(shape=arr_shape_bg),
        pay_lines=list(),
        show_score=0,
        trigger_freespins=0,
        # arr_sticky_symbol=np.zeros(shape=arr_shape_bg),
        # arr_sticky_posi=np.zeros(shape=arr_shape_bg),
        # trigger_feature=0,
    ) -> None:
        # basic
        self.game_type = game_type

        self.rng = rng

        self.arr_result = arr_result  # 滾動的盤面(滾多長輪高就多長。ex: 3x5，滾10，需要送10x5的array)
        self.arr_result_2 = arr_result_2  # 顯示的第二盤面(MY要接露用的)

        self.pay_lines = pay_lines  # ex: 3x5。3x5的111...array

        self.show_score = show_score
        self.trigger_freespins = trigger_freespins

        # # by game
        # self.arr_sticky_symbol = arr_sticky_symbol
        # self.arr_sticky_posi = arr_sticky_posi
        # self.trigger_feature = trigger_feature


class MathStatus:
    """
    Game使用的主要資料，遊戲中會變動的資料
    """

    def __init__(self) -> None:
        # basic
        """
        0 : base game
        1 : free game
        """
        self.game_type = 0

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

        # # by game
        # self.arr_sticky_symbol = np.zeros(arr_shape_bg)
        # self.arr_sticky_posi = np.zeros(arr_shape_bg)

    def one_spin(self, trigger_freegame=False):
        # [check game type]
        # - free game
        if (self.game_type == 0 and self.math_res.trigger_freespins > 0) or (self.have_free_spins > self.cnt_free_spins):  # 在BG有freespins或在FG還有freespins
            self.game_type = 1

        # - base game
        else:
            self.game_type = 0
            # clear free game data
            self.credit += self.freegame_coin
            self.freegame_coin = 0
            self.have_free_spins = 0
            self.cnt_free_spins = 0

        # - spin
        if self.game_type == 0:
            if trigger_freegame:
                self.math_res = basegame_spin_and_calculate(rng_freegame=rng_freegame)
            else:
                self.math_res = basegame_spin_and_calculate()
            # self.init_sticky()
        elif self.game_type == 1:
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
        if self.game_type == 0:
            self.credit -= coin_in
            self.credit += self.math_res.show_score
            if self.math_res.show_score > 0:
                self.cnt_hits += 1
            if self.math_res.show_score > self.max_score_basegame:
                self.math_res.max_score_basegame = self.math_res.show_score
            self.cnt_spins += 1
        elif self.game_type == 1:
            self.freegame_coin += self.math_res.show_score
            if self.math_res.show_score > self.max_score_freegame:
                self.math_res.max_score_freegame = self.math_res.show_score
            self.cnt_free_spins += 1

        # [print]
        print("* credit: ", self.credit)

    # def init_sticky(self):
    #     self.arr_sticky_symbol = np.zeros(arr_shape_bg)
    #     self.arr_sticky_posi = np.zeros(arr_shape_bg)

    # def update_sticky(self):
    #     self.arr_sticky_symbol = self.math_res.arr_sticky_symbol
    #     self.arr_sticky_posi = self.math_res.arr_sticky_posi


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

    def print_result(game_type, arr, rng, score):
        if show_log:
            print("\n====================\n")

            print("* game type: ", game_type)
            print("* score: ", score)
            print("* rng: ")
            print("    [", end="")
            for i in rng:
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
        new_shape = (GS.show_arr_len, reel_num_bg)
        arr = np.zeros(new_shape)

        if game_type == 0:  # base
            for i in range(GS.show_arr_len):
                arr[i, 0] = BGR1[(rng[0] + i) % BGR1_len]
                arr[i, 1] = BGR2[(rng[1] + i) % BGR2_len]
                arr[i, 2] = BGR3[(rng[2] + i) % BGR3_len]
                arr[i, 3] = BGR4[(rng[3] + i) % BGR4_len]
                arr[i, 4] = BGR5[(rng[4] + i) % BGR5_len]

        elif game_type == 1:  # free
            for i in range(GS.show_arr_len):
                arr[i, 0] = FGR1[(rng[0] + i) % FGR1_len]
                arr[i, 1] = FGR2[(rng[1] + i) % FGR2_len]
                arr[i, 2] = FGR3[(rng[2] + i) % FGR3_len]
                arr[i, 3] = FGR4[(rng[3] + i) % FGR4_len]
                arr[i, 4] = FGR5[(rng[4] + i) % FGR5_len]
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
        show_window_shape = (GS.show_arr_len, reel_num_bg)

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
            pay_line = generate_payline(arr_shape_bg)
            pay_line_extend = extend_arr_num(pay_line, show_window_shape)
            pay_lines.append((pay_line_extend, show_text))

        trigger_freespins = 2

        #
        math_res = MathResult(game_type, rng, arr_result, pay_lines, score, trigger_freespins)
        return math_res

    def generate_fake_math_res_freegame(symbol=0):
        #
        show_window_shape = (GS.show_arr_len, reel_num_bg)

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

        # score = multi[get_value(multi_weight_cum)] * coin_in
        score = 0

        pay_lines = []
        # for i in range(3):
        #     show_text = "no setting."
        #     pay_line = generate_payline(arr_shape)
        #     pay_line_extend = extend_arr_num(pay_line, show_window_shape)
        #     pay_lines.append((pay_line_extend, show_text))

        trigger_freespins = 0

        arr_result_sticky = np.zeros(arr_shape_fg)
        pay_lines_sticky = generate_arr(arr_shape_fg, (0, 2))

        #
        math_res = MathResult(game_type, rng, arr_result, arr_result_2, pay_lines, score, trigger_freespins, arr_result_sticky, pay_lines_sticky)

        return math_res


# [2] main
def basegame_spin_and_calculate(show_log=True, rng_freegame=np.zeros(0)):

    rng = np.zeros(reel_num_bg, dtype=np.int64)
    arr_result = np.zeros((window_size_bg, reel_num_bg), dtype=np.int64)

    # ------------ "MathResult" data ------------

    # ------------ "MathResult" data ------------

    def rng_generator(game_type):
        """
        生成RNG
        """
        if game_type == 0:  # BG base
            rng[0] = np.random.randint(BGR1_len)
            rng[1] = np.random.randint(BGR2_len)
            rng[2] = np.random.randint(BGR3_len)
            rng[3] = np.random.randint(BGR4_len)
            rng[4] = np.random.randint(BGR5_len)

        elif game_type == 1:  # FG base
            rng[0] = np.random.randint(FGR1_len)
            rng[1] = np.random.randint(FGR2_len)
            rng[2] = np.random.randint(FGR3_len)
            rng[3] = np.random.randint(FGR4_len)
            rng[4] = np.random.randint(FGR5_len)

    def arr_result_generator(game_type):
        """
        生成盤面
        """

        if game_type == 0:  # base
            for i in range(window_size_bg):
                arr_result[i, 0] = BGR1[(rng[0] + i) % BGR1_len]
                arr_result[i, 1] = BGR2[(rng[1] + i) % BGR2_len]
                arr_result[i, 2] = BGR3[(rng[2] + i) % BGR3_len]
                arr_result[i, 3] = BGR4[(rng[3] + i) % BGR4_len]
                arr_result[i, 4] = BGR5[(rng[4] + i) % BGR5_len]

        elif game_type == 1:  # free
            for i in range(window_size_fg):
                arr_result[i, 0] = FGR1[(rng[0] + i) % FGR1_len]
                arr_result[i, 1] = FGR2[(rng[1] + i) % FGR2_len]
                arr_result[i, 2] = FGR3[(rng[2] + i) % FGR3_len]
                arr_result[i, 3] = FGR4[(rng[3] + i) % FGR4_len]
                arr_result[i, 4] = FGR5[(rng[4] + i) % FGR5_len]

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

    def calculate_win_bg():
        """
        盤面算分(power up)
        """
        pay_sum = 0
        for symbol in symbols_score:
            # 計算連線(line)
            line = 0
            for i in range(reel_num_bg):
                check_list = arr_result[:, i]
                if symbol in check_list or WW in check_list:
                    line += 1
                else:
                    break

            # 計算倍數(combo)
            mul_cum = 1
            for i in range(reel_num_bg):
                check_list = arr_result[:, i]
                if symbol in check_list or WW in check_list:
                    # game type (0: way game, 1: power up and up)
                    if (symbol in symbols_m) and (symbol in symbols_powerup):  # 1
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

    def one_spin_bg():
        # spin
        rng_generator(0)
        if len(rng_freegame) > 0:
            rng[0] = rng_freegame[0]
            rng[1] = rng_freegame[1]
            rng[2] = rng_freegame[2]
            rng[3] = rng_freegame[3]
            rng[4] = rng_freegame[4]

        arr_result_generator(0)

        # calculate
        score = 0
        trigger_freegame = False

        score_c1, trigger_freegame = calculate_win_c1_bg()
        score_base = calculate_win_bg()
        score = score_c1 + score_base
        game_type = 0
        if show_log:
            print_result(f"[{game_type}] base game", arr_result, rng, score)

        return score, trigger_freegame, game_type

    # spin
    score, trigger, game_type = one_spin_bg()

    # ------------ "MathResult" data ------------

    # 正常版
    arr_result = add_base_array(rng, game_type)
    arr_result[3, :] = 99

    arr_result_2 = arr_result.copy()[: arr_shape_show[0]]

    pay_lines = []

    trigger_freespins = free_spins if trigger else 0

    math_res = MathResult(game_type, rng, arr_result, arr_result_2, pay_lines, score, trigger_freespins)

    # ------------ "MathResult" data ------------

    return math_res


def freegame_spin_and_calculate(show_log=""):

    # ------------ "MathResult" data ------------

    # ------------ "MathResult" data ------------

    rng = np.zeros(reel_num_bg, np.int64)
    arr_result = np.zeros(arr_shape_fg, np.int64)

    if True:

        # pre-setting
        rng = np.zeros(reel_num_bg, np.int64)
        arr_result = np.zeros(arr_shape_fg, np.int64)

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
        if game_type == 0:  # BG
            rng[0] = np.random.randint(BGR1_len)
            rng[1] = np.random.randint(BGR2_len)
            rng[2] = np.random.randint(BGR3_len)
            rng[3] = np.random.randint(BGR4_len)
            rng[4] = np.random.randint(BGR5_len)

        elif game_type == 1:  # FG
            rng[0] = np.random.randint(FGR1_len)
            rng[1] = np.random.randint(FGR2_len)
            rng[2] = np.random.randint(FGR3_len)
            rng[3] = np.random.randint(FGR4_len)
            rng[4] = np.random.randint(FGR5_len)

    def arr_result_generator(game_type):
        """
        生成盤面
        """

        if game_type == 0:  # base
            for i in range(window_size_bg):
                arr_result[i, 0] = BGR1[(rng[0] + i) % BGR1_len]
                arr_result[i, 1] = BGR2[(rng[1] + i) % BGR2_len]
                arr_result[i, 2] = BGR3[(rng[2] + i) % BGR3_len]
                arr_result[i, 3] = BGR4[(rng[3] + i) % BGR4_len]
                arr_result[i, 4] = BGR5[(rng[4] + i) % BGR5_len]

        elif game_type == 1:  # free
            for i in range(window_size_fg):
                arr_result[i, 0] = FGR1[(rng[0] + i) % FGR1_len]
                arr_result[i, 1] = FGR2[(rng[1] + i) % FGR2_len]
                arr_result[i, 2] = FGR3[(rng[2] + i) % FGR3_len]
                arr_result[i, 3] = FGR4[(rng[3] + i) % FGR4_len]
                arr_result[i, 4] = FGR5[(rng[4] + i) % FGR5_len]

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

    def calculate_win_fg():
        """
        盤面算分(power up)
        """
        pay_sum = 0
        for symbol in symbols_score:
            # 計算連線
            line = 0
            for i in range(reel_num_bg):
                check_list = arr_result[:, i]
                if symbol in check_list or WW in check_list:
                    line += 1
                else:
                    break

            # 計算倍數
            mul_cum = 1
            for i in range(reel_num_bg):
                check_list = arr_result[:, i]
                if symbol in check_list or WW in check_list:
                    # game type (0: way game, 1: power up and up)
                    if (symbol in symbols_m) and (symbol in symbols_powerup):  # 1
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

    def one_spin_fg():
        # spin
        rng_generator(1)
        arr_result_generator(1)

        # calculate
        score = 0
        trigger_freegame = False

        score_c1, trigger_freegame = calculate_win_c1_fg()
        score_base = calculate_win_fg()
        score = score_c1 + score_base

        # MathResult
        game_type = 1
        if show_log:
            print_result(f"[{game_type}] free game", arr_result, rng, score)

        return score, trigger_freegame, game_type

    # spin
    score, trigger, game_type = one_spin_fg()

    # ------------ "MathResult" data ------------

    arr_result = add_base_array(rng, game_type)
    arr_result_2 = arr_result.copy()[: arr_shape_show[0]]

    pay_lines = []

    trigger_freespins = free_spins if trigger else 0

    math_res = MathResult(game_type, rng, arr_result, arr_result_2, pay_lines, score, trigger_freespins)

    # ------------ "MathResult" data ------------

    return math_res


# [3] chaeck


def check_func(total_round):

    total_score = 0
    for i in range(total_round):

        # base game
        math_res = basegame_spin_and_calculate(show_log=False)
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
                math_res = freegame_spin_and_calculate(show_log=False)
                total_score += math_res.show_score
                total_trigger_time += math_res.trigger_freespins / free_spins

            freegame_time += 1

    print("RTP: ", total_score / total_round / coin_in)


# total_round = 10**5
# check_func(total_round)


# %%
