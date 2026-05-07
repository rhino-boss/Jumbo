# %% ----- Import -----


import pandas as pd
import numpy as np

import GameSetting as GS
import Tool.RedBox as RB


# %% ----- [Function] Get Data -----


def __get_strip(dir, sheet, get_length=False):
    data = pd.read_excel(dir, sheet_name=str(sheet))

    R1 = data.R1.dropna().values
    R2 = data.R2.dropna().values
    R3 = data.R3.dropna().values
    R4 = data.R4.dropna().values
    R5 = data.R5.dropna().values

    if get_length:
        R1_len = R1.shape[0]
        R2_len = R2.shape[0]
        R3_len = R3.shape[0]
        R4_len = R4.shape[0]
        R5_len = R5.shape[0]

        print("log: already get strip.")
        return R1, R2, R3, R4, R5, R1_len, R2_len, R3_len, R4_len, R5_len

    print("log: already get strip.")
    return R1, R2, R3, R4, R5, None


def __get_paytable(dir, sheet):
    data = pd.read_excel(dir, sheet_name=str(sheet))

    paytable = data[["line1", "line2", "line3", "line4", "line5"]].values
    symbol_str = data.symbol.to_list()
    symbol_id = np.array(data.id.to_list(), dtype=np.int64)

    print("log: already get pay table.")
    return paytable, symbol_str, symbol_id


def __get_paylines(dir, sheet):
    def line_str_to_arr(line):
        """
        input:
            01210
        output:
            [[1, 0, 0, 0, 0],
            [1, 0, 0, 0, 0],
            [1, 0, 0, 0, 0]]
        """
        lines_arr = np.zeros(arr_shape, np.int64)

        # line[col_idx] = row_idx
        for col_idx in range(len(line)):
            lines_arr[line[col_idx], col_idx] = 1

        return lines_arr

    data = pd.read_excel(dir, sheet_name=str(sheet), dtype=str).line

    lines_set = []
    for line in data:
        lines_set.append([int(i) for i in line])

    line_arrs = []
    for line in lines_set:
        line_arrs.append(line_str_to_arr(line))

    print("log: already get score lines.")
    return np.array(line_arrs, dtype=np.int64)


# %% ----- Setting -----


# [configure]

model_id = "S026"
version = "0.0.0.1"

window_size = 3
reel_num = 5
arr_shape = (window_size, reel_num)


# [free game]

free_spins_3in = 8  # 3顆Scatter進
free_spins_4in = 12
free_spins_5in = 20
max_free_spin_times_add = 999  # 最大re-spin次數

respin_prob = 1  # set
# respin_prob = 0.5  # set


# [symbol]

wild = 0
wild2 = 12  # 表演用
scatter = 1
m_symbols = np.array([2, 3, 4, 5], dtype=np.int64)
number_symbols = np.array([6, 7, 8, 9, 10, 11], dtype=np.int64)

symbol_expanding_wild = 99


# [strip]

# -- base strip
BR1, BR2, BR3, BR4, BR5, *_length = __get_strip(GS.path_math_data, "basegame_strip", True)
BR1_len, BR2_len, BR3_len, BR4_len, BR5_len = _length

# -- free strip
FR11, FR12, FR13, FR14, FR15, *_length = __get_strip(GS.path_math_data, "freespin_strip", True)
FR11_len, FR12_len, FR13_len, FR14_len, FR15_len = _length

FR21, FR22, FR23, FR24, FR25, *_length = __get_strip(GS.path_math_data, "respin_strip", True)
FR21_len, FR22_len, FR23_len, FR24_len, FR25_len = _length


# [pay table / pay line]

paytable, symbol_str, symbol_id = __get_paytable(GS.path_math_data, "pay_table")
pay_lines = __get_paylines(GS.path_math_data, "pay_lines")


# [else]

free_spins = data = pd.read_excel(GS.path_math_data, sheet_name=str("setting"), header=None)[1][0]  # 進freegame的分數(pay)

pay_lines_cnt = len(pay_lines)  # 幾線

bet = 1
add_rate = 1.4  # set
coin_in = pay_lines_cnt * bet * add_rate

wild_combo_0 = np.array([[0, 0, 0, 0, 0]], dtype=np.int64)
wild_combo_1 = np.array([[0, 0, 0, 0, 0], [0, 1, 0, 0, 0]], dtype=np.int64)
wild_combo_2 = np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 0]], dtype=np.int64)
wild_combo_3 = np.array([[0, 0, 0, 0, 0], [0, 0, 0, 1, 0]], dtype=np.int64)
wild_combo_4 = np.array([[0, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 1, 1, 0, 0]], dtype=np.int64)
wild_combo_5 = np.array([[0, 0, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 0], [0, 0, 1, 1, 0]], dtype=np.int64)
wild_combo_6 = np.array([[0, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 0, 1, 0], [0, 1, 0, 1, 0]], dtype=np.int64)
wild_combo_7 = np.array(
    [[0, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 1, 1, 0, 0], [0, 0, 0, 1, 0], [0, 1, 0, 1, 0], [0, 0, 1, 1, 0], [0, 1, 1, 1, 0]], dtype=np.int64
)


# %% ----- [Function] Demo Game Use -----


class MathOutput:
    def __init__(
        self,
        rng=np.zeros(reel_num),
        arr_result=np.zeros(shape=arr_shape),
        pay_line=list(),
        score=0,
        respin_posi=np.zeros(shape=reel_num),
        respin_show_arr=np.zeros(arr_shape),
    ):
        self.rng = rng
        self.arr_result = arr_result
        self.paylines = pay_line
        self.score = score
        self.trigger_cnt = 0  # !!!

        # special
        self.respin_posi = respin_posi
        self.respin_show_arr = respin_show_arr


def basegame_spin_and_calculate(print_log=False):
    """
    Feature
    --- 
    wild 延展(wild*2)

    """

    rng = np.zeros(reel_num, dtype=np.int8)
    arr_result = np.zeros((window_size, reel_num), dtype=np.int8)

    def rng_generator():
        rng[0] = np.random.randint(BR1_len)
        rng[1] = np.random.randint(BR2_len)
        rng[2] = np.random.randint(BR3_len)
        rng[3] = np.random.randint(BR4_len)
        rng[4] = np.random.randint(BR5_len)

        # # lock rng (test)
        # lock_rng = [25, 43, 35, 40, 36]
        # for i in range(len(lock_rng)):
        #     rng[i] = lock_rng[i]

        if print_log:
            print("rng: ", rng, "\n")

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
        #     [1, 1, 0, 1, 5],
        #     [9, 1, 1, 9, 5],
        #     [2, 2, 2, 2, 2]], dtype=np.int8)

        # for i in range(len(lock_arr_result)):
        #     arr_result[i] = lock_arr_result[i]

        if print_log:
            print("arr_result: \n", arr_result, "\n")

        return None

    def __calculate_lines(result):
        line = 0

        score_symbol = -1
        for i in result:
            if score_symbol != -1 and score_symbol != i and i != wild:
                break

            if i != wild:
                score_symbol = i

            line += 1

        # 開頭是Scatter不在這個function算分
        if score_symbol == scatter:
            line = 1

        return score_symbol, line

    def __get_wild_appear_reel(arr):
        arr = arr.copy()
        arr_T = arr.T
        wild_appear_r = np.zeros(reel_num, np.int64)
        for j in range(len(arr_T)):
            have_ww = False
            for s in arr_T[j]:
                if s == wild:
                    have_ww = True
                    break
            if have_ww:
                wild_appear_r[j] = 1

        return wild_appear_r

    def __get_wild_combo(wild_combo):

        """
        取得有無wild的組合

        Examples
        --------
        >>> __get_wild_combo([0, 0, 1, 2, 0])
        [[0 0 0 0 0]
        [0 0 1 0 0]
        [0 0 0 1 0]
        [0 0 1 1 0]]
        
        """

        # 基本版面設定
        c0 = [0]
        c1 = [0, 1]
        c2 = [0, 0, 1, 1]
        c3 = [0, 0, 0, 0, 1, 1, 1, 1]
        cc = [c0, c1, c2, c3]

        # 總組合數
        wild_combo = wild_combo.copy()
        total_combo = 2 ** sum(wild_combo)

        # [0,0,1,1,0]->[0,0,1,2,0]
        cnt = 0
        for i, d in enumerate(wild_combo):
            if d > 0:
                wild_combo[i] += cnt
                cnt += 1

        wild_combos = []
        for c in wild_combo:
            wild_combos.extend(cc[c] * int(total_combo / len(cc[c])))

        # 轉置
        shape = (total_combo, reel_num)
        arr = np.zeros(shape, dtype=np.int64)
        cnt = 0
        for j in range(shape[1]):
            for i in range(shape[0]):
                arr[i, j] = wild_combos[cnt]
                cnt += 1

        return arr

    def calculate_win(arr):

        # output
        total_pay = 0  # 這把的總得分
        payline_list = []

        #
        arr = arr.copy()
        ww_appear_reels = __get_wild_appear_reel(arr)
        wild_combo = __get_wild_combo(ww_appear_reels)

        for _idx, pay_line in enumerate(pay_lines):

            # get 要算分的線
            result = np.zeros(reel_num, np.int8)
            for i in range(window_size):
                for j in range(reel_num):
                    if pay_line[i, j] == 1:
                        result[j] = arr[i, j]

            # wild 算分組合
            catch_scores = []
            catch_lines = []
            for i, combo in enumerate(wild_combo):
                r = result.copy()
                for j in range(len(result)):
                    if combo[j] == 1:
                        r[j] = wild

                score_symbol, line = __calculate_lines(r)
                score = paytable[score_symbol, line - 1] * bet

                # catch
                catch_scores.append(score)
                catch_lines.append(line)

            if len(catch_scores) != 0 and len(catch_lines) != 0:
                max_line = max(catch_lines)
                sum_score = 0
                for i, c_line in enumerate(catch_lines):
                    if c_line == max_line:
                        sum_score += catch_scores[i]

                total_pay += sum_score
                if sum_score > 0:
                    payline_list.append(pay_line)

        return total_pay, payline_list

    rng_generator()
    arr_result_generator()

    if print_log:
        RB.log_use.print_result("rng", rng, next_line=True)

    score, paylines = calculate_win(arr_result)

    return MathOutput(rng, arr_result, paylines, score)


def freegame_spin_and_calculate(print_log=False):
    # rng_temp_list = [[39,  9,  6 ,34 ,28]]
    """
    Feature
    --- 
    1. wild 延展(wild*2)
    2. re-spin 機率觸發

    """
    rng = np.zeros(reel_num, dtype=np.int8)
    arr_result = np.zeros((window_size, reel_num), dtype=np.int8)

    def rng_generator(strip_type):
        if strip_type == 0:
            rng[0] = np.random.randint(BR1_len)
            rng[1] = np.random.randint(BR2_len)
            rng[2] = np.random.randint(BR3_len)
            rng[3] = np.random.randint(BR4_len)
            rng[4] = np.random.randint(BR5_len)
        elif strip_type == 1:
            rng[0] = np.random.randint(FR11_len)
            rng[1] = np.random.randint(FR12_len)
            rng[2] = np.random.randint(FR13_len)
            rng[3] = np.random.randint(FR14_len)
            rng[4] = np.random.randint(FR15_len)

        elif strip_type == 2:
            rng[0] = np.random.randint(FR21_len)
            rng[1] = np.random.randint(FR22_len)
            rng[2] = np.random.randint(FR23_len)
            rng[3] = np.random.randint(FR24_len)
            rng[4] = np.random.randint(FR25_len)

        # # # lock rng (test)
        # if len(rng_temp_list)>0:
        #     lock_rng = rng_temp_list.pop()
        #     for i in range(len(lock_rng)):
        #         rng[i] = lock_rng[i]

        return None

    def arr_result_generator(strip_type):
        if strip_type == 0:
            for i in range(window_size):
                arr_result[i, 0] = BR1[(rng[0] + i) % BR1_len]
                arr_result[i, 1] = BR2[(rng[1] + i) % BR2_len]
                arr_result[i, 2] = BR3[(rng[2] + i) % BR3_len]
                arr_result[i, 3] = BR4[(rng[3] + i) % BR4_len]
                arr_result[i, 4] = BR5[(rng[4] + i) % BR5_len]
        elif strip_type == 1:
            for i in range(window_size):
                arr_result[i, 0] = FR11[(rng[0] + i) % FR11_len]
                arr_result[i, 1] = FR12[(rng[1] + i) % FR12_len]
                arr_result[i, 2] = FR13[(rng[2] + i) % FR13_len]
                arr_result[i, 3] = FR14[(rng[3] + i) % FR14_len]
                arr_result[i, 4] = FR15[(rng[4] + i) % FR15_len]
        elif strip_type == 2:
            for i in range(window_size):
                arr_result[i, 0] = FR21[(rng[0] + i) % FR21_len]
                arr_result[i, 1] = FR22[(rng[1] + i) % FR22_len]
                arr_result[i, 2] = FR23[(rng[2] + i) % FR23_len]
                arr_result[i, 3] = FR24[(rng[3] + i) % FR24_len]
                arr_result[i, 4] = FR25[(rng[4] + i) % FR25_len]

        # # lock arr_result (test)
        # lock_arr_result = np.array([
        #     [10, 0, 1, 6, 1],
        #     [6, 10, 3, 3, 3],
        #     [4, 5, 10, 5, 3]], dtype=np.int8)

        # for i in range(len(lock_arr_result)):
        #     arr_result[i] = lock_arr_result[i]

        return None

    def __calculate_lines(result):
        line = 0

        score_symbol = -1
        for i in result:
            if score_symbol != -1 and score_symbol != i and i != wild:
                break

            if i != wild:
                score_symbol = i

            line += 1

        # 開頭是Scatter不算分
        if score_symbol == scatter:
            line = 1

        return score_symbol, line

    def __get_wild_appear_reel(arr):
        arr = arr.copy()
        arr_W = arr.copy()
        arr_T = arr.T
        wild_appear_r = np.zeros(reel_num, np.int64)
        for j in range(len(arr_T)):
            have_ww = False
            for s in arr_T[j]:
                if s == wild:
                    have_ww = True
                    break
            if have_ww:
                wild_appear_r[j] = 1
                arr.T[j] = np.full(shape=window_size, fill_value=wild, dtype=np.int64)

        for i in range(window_size):
            for j in range(reel_num):
                if arr_W[i, j] == wild:
                    arr[i, j] = wild

        return arr, wild_appear_r

    def __calculate_mul(result, wild_combo, is_inv):
        catch_scores = []
        catch_lines = []

        if is_inv:
            result = result[::-1]

        for i, combo in enumerate(wild_combo):
            r = result.copy()
            for j in range(len(result)):
                if is_inv:
                    if combo[::-1][j] == 1:
                        r[j] = wild
                else:
                    if combo[j] == 1:
                        r[j] = wild

            score_symbol, line = __calculate_lines(r)
            score = paytable[score_symbol, line - 1] * bet

            # catch
            catch_scores.append(score)
            catch_lines.append(line)

        sum_score = 0
        if len(catch_scores) != 0 and len(catch_lines) != 0:
            max_line = max(catch_lines)
            for i, c_line in enumerate(catch_lines):
                if c_line == max_line:
                    sum_score += catch_scores[i]

        return sum_score, score_symbol

    def __get_wild_combo(ww_appear_reels):
        wild_combo = wild_combo_0
        if (ww_appear_reels == np.array([0, 0, 0, 0, 0], dtype=np.int64)).all():  # 0
            wild_combo = wild_combo_0
        elif (ww_appear_reels == np.array([0, 1, 0, 0, 0], dtype=np.int64)).all():  # 1
            wild_combo = wild_combo_1
        elif (ww_appear_reels == np.array([0, 0, 1, 0, 0], dtype=np.int64)).all():  # 2
            wild_combo = wild_combo_2
        elif (ww_appear_reels == np.array([0, 0, 0, 1, 0], dtype=np.int64)).all():  # 3
            wild_combo = wild_combo_3
        elif (ww_appear_reels == np.array([0, 1, 1, 0, 0], dtype=np.int64)).all():  # 4
            wild_combo = wild_combo_4
        elif (ww_appear_reels == np.array([0, 0, 1, 1, 0], dtype=np.int64)).all():  # 5
            wild_combo = wild_combo_5
        elif (ww_appear_reels == np.array([0, 1, 0, 1, 0], dtype=np.int64)).all():  # 6
            wild_combo = wild_combo_6
        elif (ww_appear_reels == np.array([0, 1, 1, 1, 0], dtype=np.int64)).all():  # 7
            wild_combo = wild_combo_7

        return wild_combo

    def calculate_win_freegame(arr, before_wild_lock_reel, lock_arr):

        # 2 - [initial]
        arr = arr.copy()
        after_wild_lock_reel = before_wild_lock_reel.copy()
        after_lock_arr = lock_arr.copy()
        pay = 0  # 這把free spin的得分
        paylines = []

        # 3 - [scatter]

        # 4 - [symbol]
        # - keep lock
        for i in range(window_size):
            for j in range(reel_num):
                if after_lock_arr[i, j] != -1:
                    arr[i, j] = after_lock_arr[i, j]

        _, ww_appear_reels = __get_wild_appear_reel(arr)
        wild_combo = __get_wild_combo(ww_appear_reels)

        for idx, j in enumerate(ww_appear_reels):
            if j > 0:
                after_wild_lock_reel[idx] = 1
                for i in range(window_size):
                    after_lock_arr[i, idx] = arr[i, idx]
            else:
                for i in range(window_size):
                    after_lock_arr[i, idx] = -1

        # 5 - [calculate / score]
        for pay_line in pay_lines:

            # get 要算分的線
            result = np.zeros(reel_num, np.int8)
            for jj in range(window_size):
                for i in range(reel_num):
                    if pay_line[jj, i] == 1:
                        result[i] = arr[jj, i]

            # wild 算分組合
            s1, ss1 = __calculate_mul(result, wild_combo, False)
            s2, ss2 = __calculate_mul(result, wild_combo, True)
            if ss1 == ss2:
                score = max(s1, s2)
            else:
                score = s1 + s2

            if score > 0:
                pay += score
                paylines.append(pay_line)

        return pay, after_wild_lock_reel, after_lock_arr, paylines, arr

    def one_free_spin():

        # [output]
        output_data = []

        # [initial] setting
        before_wild_lock_position = np.zeros(reel_num, dtype=np.int64)

        # 2 - [initial]
        wild_lock_reel = np.zeros(reel_num, dtype=np.int64)  # 鎖定住的reel
        lock_arr = np.full(arr_shape, fill_value=-1, dtype=np.int64)  # 鎖定住的元素array

        wild_lock_num = 0
        cnt_spin = 1  # 還可以轉幾次
        cnt_spin_level = 0  # spin的階段 (first spin -> re-spin1 -> re-spin2 -> re-spin3)

        # [start spin]
        respin_list = np.zeros(reel_num)
        while cnt_spin > 0:

            # [calculate / score]
            _strip_idx = 1 if cnt_spin_level == 0 else 2
            rng_generator(_strip_idx)
            arr_result_generator(_strip_idx)

            score, _after_wild_lock_reel, _after_lock_arr, paylines, _show_arr = calculate_win_freegame(arr_result, wild_lock_reel, lock_arr)
            show_arr = _show_arr.copy()

            # [update] re-spin
            # - 機率re-spin (version 1 >> 每顆wild判定，過了才lock)
            is_spin = False
            for j in range(reel_num):
                if _after_wild_lock_reel[j] == 1 and wild_lock_reel[j] != 1:
                    rd = np.random.rand()
                    if rd <= respin_prob:  # re-spin
                        is_spin |= True
                        respin_list[j] = 1

                        # - [update] "wild_lock_reel"
                        wild_lock_reel[j] = 1

                        # - [update] "lock_element"
                        for i in range(window_size):
                            lock_arr[i, j] = _after_lock_arr[i, j]
            if is_spin:
                cnt_spin += 1

            # [update] status
            cnt_spin -= 1
            cnt_spin_level += 1

            for r in range(reel_num):
                for w in range(window_size):
                    if respin_list[r] == 1 and arr_result[w, r] == wild:
                        arr_result[w, r] = wild2
                    if respin_list[r] == 1 and show_arr[w, r] == wild:
                        show_arr[w, r] = wild2

            for i in paylines:
                for r in range(reel_num):
                    for w in range(window_size):
                        if respin_list[r] == 1 and arr_result[w, r] == wild:
                            i[w, r] = wild2

            if cnt_spin_level == 0:
                output_data.append(MathOutput(rng.copy(), arr_result.copy(), paylines.copy(), score))
            else:
                output_data.append(MathOutput(rng.copy(), arr_result.copy(), paylines.copy(), score, before_wild_lock_position, show_arr))

            before_wild_lock_position = wild_lock_reel.copy()

        return output_data

    return one_free_spin()


# %%
