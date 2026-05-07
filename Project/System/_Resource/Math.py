# ----- import -----

import multiprocessing
import threading
import pandas as pd
import numpy as np
import time
import math
import matplotlib.pyplot as plt
from datetime import datetime
import os
import sys

# ----- setting / get data -----


def get_resource_path(relative_path):
    """正確取得資源路徑"""
    if getattr(sys, "frozen", False):
        # 打包後
        base_path = sys._MEIPASS
    else:
        # 開發模式
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


simulation_use_path = get_resource_path("_Resource/Simulator/multiplier_range_v5.xlsx")


threshold_v1 = pd.read_excel(simulation_use_path, "v1_3000", header=None, dtype=np.float32).values[:, 0]
threshold_v2 = pd.read_excel(simulation_use_path, "v2_5000", header=None, dtype=np.float32).values[:, 0]
threshold_v3 = pd.read_excel(simulation_use_path, "v3_500", header=None, dtype=np.float32).values[:, 0]
threshold_v4 = pd.read_excel(simulation_use_path, "v4_500_median", header=None, dtype=np.float32).values[:, 0]
threshold_v5 = pd.read_excel(simulation_use_path, "v5", header=None, dtype=np.float32).values[:, 0]

threshold_show = threshold_v1
threshold_record = threshold_v5  # 31, 32, ...
threshold_record_version = "threshold_v5"


# ----- function -----


# plot
class cplot:
    """
    畫圖工具
    """

    plot_size = (14, 8)
    font_set = (28, 24, 14, 20)

    def __init__(self) -> None:
        pass

    def multiplier_line_mul(data_tuple, plot_title, output_filename="", ylim=0.16, start_x_idx=0, line_color=("red", "orange", "green", "blue", "purple")):
        """
        input xlsx, plot

        Parameters
        ---
        data_tuple -> (str, str)
            data path, game name.

        start_idx -> int, default 0
            data start index.

        line_color -> turple, list, default ('red', 'orange', 'green', 'blue', 'purple')
            line color.

        Example
        ---

        dirr = "c:\\Users\\rhinshen\\Mine\\Employee_0419\\3_Tools\\PyTools\\CommonPlot\\Multiplier_Line\\RowData\\"

        dirr_datas = []\n
        dirr_datas.append((dirr + "倍率線型_包你發至尊版 富貴連線_v7_bet88_FG.xlsx", "富貴連線_v7"))\n
        dirr_datas.append((dirr + "倍率線型_包你發至尊版 富貴連線_v6_bet88_FG.xlsx", "富貴連線_v6"))\n

        >>> plot_multiplier_line(dirr_datas, "倍率線型", ylim=0.16, filename="倍率線型", line_color=("black", "red"))
        <plot>

        """
        # get data
        plot_datas = []
        for dirr, game_name in data_tuple:
            data = pd.read_excel(dirr, index_col=0)
            plot_datas.append((data, game_name))

        x_lable = data.index.tolist()

        # setting
        plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]  # 中文設定
        plt.rcParams["axes.unicode_minus"] = False

        x_lable = x_lable[start_x_idx:]

        # split datas, names and converted to percentage
        datas = []
        names = []
        for pds in plot_datas:
            ori_data = pds[0].copy()[start_x_idx:].values
            datas.append(ori_data / sum(ori_data))
            names.append(pds[1])

        # plot
        plt.figure(figsize=cplot.plot_size)

        for idx, pds in enumerate(datas):
            plt.plot([i for i in range(len(pds))], pds, marker="o", label=names[idx], color=line_color[idx])

        plt.title(plot_title, fontsize=cplot.font_set[0])

        # plt.xlabel("Multiple", fontsize=cplot.font_set[1])
        plt.xticks([i for i in range(len(datas[0]))], x_lable, rotation=90, fontsize=cplot.font_set[2])
        plt.yticks(fontsize=cplot.font_set[1])

        # plt.ylabel("Freq(%)", fontsize=cplot.font_set[1])
        plt.ylim(0, ylim)

        plt.legend(fontsize=cplot.font_set[3])
        plt.grid()

        # save fig
        if output_filename != "":
            plt.savefig(f"{output_filename}.jpg", bbox_inches="tight", dpi=300, transparent=True)

    def multiplier_line(record, threshold, title="倍率線型", ylim=0.16, start=0):
        """
        input data (array), plot
        """

        # converted to percentage
        ori_data = record.copy()[start:]
        data = ori_data / sum(ori_data)

        # xlabel prepare
        threshold_str = []
        for i in range(start, len(threshold)):
            if i == 0:
                threshold_str.append("0")
            else:
                threshold_str.append(str(threshold[i - 1]) + " < X <= " + str(threshold[i]))

        # plot
        plt.figure(figsize=cplot.plot_size)
        plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]

        plt.plot([i for i in range(len(data))], data, marker="o")

        plt.title(title, fontsize=cplot.font_set[0])

        # plt.xlabel("Multiple", cplot.font_set[1])
        plt.xticks([i for i in range(len(data))], threshold_str, rotation=90)

        # plt.ylabel("Freq(%)", cplot.font_set[1])
        plt.ylim(0, ylim)

        plt.grid()
        # plt.show()

    def map_multiplier_big2small(range_small, range_big, data_big):
        """
        記中位數會用到
        """
        arr_cum = np.zeros(len(range_big), dtype=np.int64)
        for i, v in enumerate(range_big):
            if v in range_small:
                arr_cum[i] = v
            else:
                arr_cum[i] = 0

        arr_cum = arr_cum[::-1]
        temp_value = arr_cum[-1]
        for i, v in enumerate(arr_cum):
            if v == 0 and i != len(arr_cum) - 1:
                arr_cum[i] = temp_value
            else:
                temp_value = arr_cum[i]

        df_cum = pd.DataFrame({"range": arr_cum[::-1], "value": data_big})
        new_data = df_cum.groupby("range").sum().values.T[0]

        return new_data

    def map_multiplier_big2small_v2(range_small, range_big, data_big):

        def fill_values(li):
            new_arr = np.array(li, dtype=np.float32)
            for i, v in enumerate(li):
                if v != 0:
                    new_arr[i] = li[i]
                elif v == 0:
                    for num in li[i:]:
                        if num != 0:
                            new_arr[i] = num
                            break
            return new_arr

        arr_cum = np.zeros(len(range_big), dtype=np.float32)

        for i, rr in enumerate(range_big):
            if rr in range_small:
                arr_cum[i] = rr

        arr_cum = fill_values(arr_cum)
        arr_cum = fill_values(arr_cum[::-1])[::-1]

        new_data = np.zeros(len(range_small), dtype=np.float32)
        for i, rr in enumerate(arr_cum):
            new_data[list(range_small).index(rr)] += data_big[i]

        new_data2 = np.zeros(len(range_small), dtype=np.float32)
        for i in range(len(new_data2)):
            if i + 1 != len(new_data2):
                new_data2[i + 1] = new_data[i]

        return new_data2


# func
class cfunc:
    """
    常用func
    """

    def __init__(self) -> None:
        pass

    def get_median_idx_from_multiplier_line(data):

        data = data.copy().cumsum()
        median_num = data[-1] / 2

        idx = 0
        for i, v in enumerate(data):
            if v > median_num:
                idx = i
                break

        v1 = abs(data[idx - 1] - median_num)
        v2 = abs(data[idx] - median_num)

        if v1 > v2:
            return idx
        else:
            return idx - 1


# simulate
class simulation:

    def __init__(self) -> None:
        pass

    def time_func(s, func, *args, **kwargs):
        """
        Benchmark *func* and print out its runtime.
        """
        print("\n--- start at --- %s\n" % (time.ctime()))
        time1 = time.time()
        res = func(*args, **kwargs)
        time2 = time.time()
        minutes, seconds = divmod(time2 - time1, 60)
        hours, minutes = divmod(minutes, 60)
        print(s + "%s hours, %s minutes, %s seconds \n" % (math.floor(hours), math.floor(minutes), math.floor(seconds)))

        return res, time2 - time1

    def make_multi_thread(func, round, output_shape):
        """
        Run the given function inside *numthreads* threads, splitting its
        arguments into equal-sized chunks.
        """

        def func_mt():
            num_threads = multiprocessing.cpu_count()

            if round < 10**4:
                num_threads = 1

            print("Multi-Thread Mode: On (%d Thread)" % (num_threads))

            thread_spins = round // num_threads
            result = np.zeros((num_threads, *output_shape), np.int64)  # array for return
            chunks = []

            for int_thread in range(num_threads):
                chunks.append((result[int_thread], thread_spins))

            threads = [threading.Thread(target=func, args=chunks[t]) for t in range(len(chunks))]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            result__ = np.zeros(output_shape, np.int64)  # array for return
            for i in range(num_threads):
                result__ += result[i]

            return result__

        return func_mt

    def output_data(datas, names, path, file_name="", threshold=threshold_record):
        # check
        if len(datas) != len(names):
            print(f"data's lengths are different {len(datas)}/{len(names)}")
            return None

        # dataframe initial
        threshold_str = []
        for i in range(0, len(threshold)):
            if i == 0:
                threshold_str.append("0")
            else:
                threshold_str.append(str(threshold[i - 1]) + " < X <= " + str(threshold[i]))

        data_df = pd.DataFrame(threshold_str, columns=["Interval"])

        # input data
        for i, d in enumerate(datas):
            col_name = names[i]
            data_df[col_name] = d

        # output
        if file_name == "":
            now = datetime.strftime(datetime.now(), "%y%m%d%H%M%S")  # 年月日時分秒
            file_name = f"{'倍率線型'}_{now}"

        data_df.to_excel(path + file_name + ".xlsx", index=False)


# analysis
class analysis:

    def __init__(self) -> None:
        pass

    def get_stack_rate_overall(reels):
        """
        堆疊率_All。單個符號、兩個符號、...比例，不分種類

        Examples
        --------
        reels = [1, 1, 1, 2, 3, 2, 2, 1, 1, 5, 5] #\n
        reels = ["a", "a", "d", "b", "a", "a", "c", "c", "c", "c", "c", "c", "k", "a"] #\n
        reels_symbol_sort = np.unique(reels) #\n
        get_stack_rate_overall(reels)
        >>> 1:  15.38%
            2:  7.69%
            3:  7.69%
            4:  15.38%
            5:  46.15%
            6:  7.69%
            7:  7.69%
        """

        reels = reels.copy()

        list_stack = []
        before_symbol = reels.pop(0)
        cnt = 1
        for s in reels:
            if before_symbol == s:
                cnt += 1
            else:
                list_stack.append(cnt)
                before_symbol = s
                cnt = 1
        list_stack.append(cnt)

        # show result
        reel_len = len(reels)
        for i, stack in enumerate(list_stack):
            print(f"{i+1}: {stack/reel_len*100: 0.2f}%")

        return list_stack

    def get_stack_rate_by_symbol(reels, col_label):
        """
        堆疊率。符號1單個出現、兩堆疊出現、...比例

        Examples
        --------
        reels = [1, 1, 1, 2, 3, 2, 2, 1, 1, 5, 5] #\n
        reels = ["a", "a", "d", "b", "a", "a", "c", "c", "c", "c", "c", "c", "k", "a"] #\n
        reels_symbol_sort = np.unique(reels) #\n
        get_stack_rate_by_symbol(reels, reels_symbol_sort) #\n
        >>>       1     2     3     4     5     6
            a  0.33  0.67  0.00  0.00  0.00  0.00
            b  1.00  0.00  0.00  0.00  0.00  0.00
            c  0.00  0.00  0.00  0.00  0.00  1.00
            d  1.00  0.00  0.00  0.00  0.00  0.00
            k  1.00  0.00  0.00  0.00  0.00  0.00

        """

        reels = reels.copy()

        # 切成N堆疊的片段
        list_symbol = []
        list_stack = []
        before_symbol = reels.pop(0)
        cnt = 1
        for s in reels:
            if before_symbol == s:
                cnt += 1
            else:
                list_symbol.append(before_symbol)
                list_stack.append(cnt)
                before_symbol = s
                cnt = 1

        list_symbol.append(before_symbol)
        list_stack.append(cnt)

        # 整合
        arr = np.zeros((len(col_label), max(list_stack)), dtype=np.float16)
        for i in range(len(list_symbol)):
            x = col_label.tolist().index(list_symbol[i])
            arr[x, list_stack[i] - 1] += 1

        # show result
        for i in range(arr.shape[0]):
            arr[i] = arr[i] / sum(arr[i])

        result_table = pd.DataFrame(arr)
        result_table.index = col_label
        result_table.columns = result_table.columns + 1
        print(result_table)

        return arr


# reel
class reel_v2:
    """
    輪帶相關
    """

    class generate_reel:
        """
        可以設定固定間隔(接近)、至少間隔多長
        """

        def __init__(self, symbol_df, stack_df):
            # setting
            self.symbol_df = symbol_df  # 所有符號設定
            self.stack_df = stack_df.values  # 所有符號堆疊組數

            self.symbol_id = symbol_df["symbol_id"]
            self.symbol_str = symbol_df["symbol_str"]
            self.symbol_count = symbol_df["symbol_count"]
            # self.mini_gap = symbol_df["mini_gap"]
            self.all_stack_option = stack_df.columns  # 所有堆疊選項

            # processing
            self.symbol_num = len(self.symbol_id)
            self.stack_num = self.stack_df.shape[1]

            # initial value
            self.condition_list = []

        class condition_setting:
            def __init__(self, symbol, blank_num, blank_type):
                self.symbol = symbol
                self.blank_num = blank_num
                self.blank_type = blank_type

            def print_value(self):
                print((self.symbol, self.blank_num, self.blank_type))

        class reel_type:
            symbol_id = 0
            symbol_str = 1

        class blank_type:
            fix_posi = 1  # 固定間格: n格沒出現，必定出現。n格有出現，必定不出現
            at_least = 2  # 至少間格: n格有出現，必定不出現
            most_posi = 3  # 最多間格: n格沒出現，必定出現

        @staticmethod
        def check_list_in_list(check_values, pool):
            for v in check_values:
                if v in pool:
                    return True

            return False

        @staticmethod
        def get_pre_symbol_list(n, symbol_list):
            if n >= len(symbol_list):
                return symbol_list
            return symbol_list[-n:]

        @staticmethod
        def list_2_arr_nxm(bool_list, m):
            n = len(bool_list)
            bool_arr_nxm = np.array([i for i in bool_list for _ in range(m)]).reshape((n, m))

            return bool_arr_nxm

        @staticmethod
        def update_arr(arr, new_arr):
            for i in range(arr.shape[0]):
                for j in range(arr.shape[1]):
                    arr[i, j] = new_arr[i, j]

        @staticmethod
        def random_value(arr):

            # func
            get_prob = lambda weight: weight / weight.sum()

            # random
            symbol_weight = arr.sum(axis=1)
            rd_symbol = np.random.choice([i for i in range(arr.shape[0])], p=get_prob(symbol_weight))

            stack_weight = arr[rd_symbol]
            rd_stack_id = np.random.choice([i for i in range(arr.shape[1])], p=get_prob(stack_weight))

            return rd_symbol, rd_stack_id

        @staticmethod
        def output_reel():
            pass

        # tool func
        def get_symbol_stack_num_nxn(self):

            def get_symbol_stack_num_1xn(total_num, rate):
                """
                決定二堆疊以上的數量，剩下的都是一堆疊的
                """

                num = np.zeros(rate.shape)
                sp = math.sumprod(self.all_stack_option, rate)

                for i in range(1, len(rate)):
                    num[i] = math.floor(total_num / sp * rate[i])

                num[0] = total_num - math.sumprod(num[1:], self.all_stack_option[1:])

                return num

            stack_num_arr = np.zeros(self.stack_df.shape, dtype=np.int32)

            for i in range(self.symbol_num):
                # setting
                total_num = self.symbol_count[i]
                if total_num == 0:
                    continue

                setting_stack_rate = self.stack_df[i]

                # calculate
                stack_num_arr[i] = get_symbol_stack_num_1xn(total_num, setting_stack_rate)

            return stack_num_arr

        def choose_pool_arr(self, arr, reel):

            for i, condition in enumerate(self.condition_list):
                pre_symbol_list = self.get_pre_symbol_list(condition.blank_num, reel)
                symbol_in_list_bool = self.check_list_in_list(condition.symbol, pre_symbol_list)

                bool_arr_1xn = np.ones(self.symbol_num, dtype=np.int16)
                symbol_posi = []
                for symbol in condition.symbol:
                    symbol_posi.append(self.symbol_id.tolist().index(symbol))

                if condition.blank_type == 1 and not symbol_in_list_bool:  # 固定間格。沒有，必定出現
                    if arr[symbol_posi].sum() == 0:
                        continue
                    bool_arr_1xn = np.zeros(self.symbol_num, dtype=np.int16)
                    bool_arr_1xn[symbol_posi] = 1
                    bool_arr_nxm = self.list_2_arr_nxm(bool_arr_1xn, self.stack_num)
                    self.update_arr(arr, arr * bool_arr_nxm)
                    break
                elif condition.blank_type == 1 and symbol_in_list_bool:  # 固定間格。有，不能出現
                    bool_arr_1xn[symbol_posi] = 0

                if condition.blank_type == 3 and not symbol_in_list_bool:  # 最多間格。n格沒出現，必定出現
                    bool_arr_1xn = np.zeros(self.symbol_num, dtype=np.int16)
                    bool_arr_1xn[symbol_posi] = 1

                if condition.blank_type == 2 and symbol_in_list_bool:  # 至少間格。相同標誌、種類不要連續出現
                    bool_arr_1xn[symbol_posi] = 0

                bool_arr_nxm = self.list_2_arr_nxm(bool_arr_1xn, self.stack_num)
                self.update_arr(arr, arr * bool_arr_nxm)

        # main
        def new_condition(self, symbol: list, blank_num: int, blank_type: int):
            self.condition_list.append(self.condition_setting(symbol, blank_num, blank_type))

        def generate_reel(self, show_type=reel_type.symbol_id):
            # 計算各組符號的不同堆疊的數量
            stack_num_arr = self.get_symbol_stack_num_nxn()

            # 生成輪帶
            pool_arr = stack_num_arr.copy()
            pool_arr.sum(axis=0)

            new_reel_id = []
            new_reel_str = []
            while stack_num_arr.sum() > 0:
                # pool setting
                pool_arr = stack_num_arr.copy()
                self.choose_pool_arr(pool_arr, new_reel_id)

                # print(stack_num_arr.copy(), "ori")
                # print(pool_arr, "adj")

                # random "symbol" and "stack"
                symbol_id, stack_id = self.random_value(pool_arr)

                # update "stack_num_arr" and "reel"
                stack_num = self.all_stack_option[stack_id]
                stack_num_arr[symbol_id, stack_id] -= 1

                for _ in range(stack_num):
                    new_reel_id.append(self.symbol_id[symbol_id])
                    new_reel_str.append(self.symbol_str[symbol_id])

            if show_type == 0:
                return new_reel_id
            elif show_type == 1:
                return new_reel_str

        def generate_reel_n(self, try_times, reel_type: reel_type = reel_type.symbol_id):
            cnt = 0
            for _ in range(try_times):
                try:
                    new_reel = self.generate_reel(reel_type)
                    # print(f"run times: {cnt}")
                    break
                except ValueError as e:
                    # print(f"error: {e}")
                    continue

                cnt += 1

            print(f"run times: {cnt}")
            return new_reel
