import multiprocessing
import threading
import pandas as pd
import numpy as np
import time
import math
import matplotlib.pyplot as plt
from datetime import datetime


threshold_v0 = np.array(
    [
        0,
        0.5,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        15,
        20,
        25,
        30,
        35,
        40,
        45,
        50,
        60,
        70,
        80,
        90,
        100,
        125,
        150,
        175,
        200,
        225,
        250,
        275,
        300,
        325,
        350,
        375,
        400,
        425,
        450,
        475,
        500,
        600,
        700,
        800,
        900,
        1000,
        2000,
        3000,
        9999999,
    ],
    np.float64,
)  # v0_自定義

threshold_v1 = np.array(
    [
        0,
        0.5,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        15,
        20,
        25,
        30,
        35,
        40,
        45,
        50,
        60,
        70,
        80,
        90,
        100,
        125,
        150,
        175,
        200,
        225,
        250,
        275,
        300,
        325,
        350,
        375,
        400,
        425,
        450,
        475,
        500,
        600,
        700,
        800,
        900,
        1000,
        2000,
        3000,
        9999999,
    ],
    np.float64,
)  # v1_原始版(3000)

threshold_v2 = np.array(
    [
        0,
        1,
        2,
        3,
        4,
        5,
        7,
        6,
        8,
        9,
        10,
        15,
        20,
        25,
        30,
        35,
        40,
        45,
        50,
        60,
        70,
        80,
        90,
        100,
        125,
        150,
        175,
        200,
        225,
        250,
        275,
        300,
        325,
        350,
        375,
        400,
        425,
        450,
        475,
        600,
        500,
        700,
        800,
        900,
        1000,
        2000,
        3000,
        5000,
        999999,
    ],
    np.float64,
)  # v2_三代機(5000)

threshold_v3 = np.array(
    [
        0,
        1,
        2,
        5,
        10,
        20,
        50,
        100,
        300,
        1000,
        10000,
        150000,
    ],
    np.float64,
)  # v3_YL

threshold_choose = 2
threshold_dict = {0: threshold_v0, 1: threshold_v1, 2: threshold_v2, 3: threshold_v3}
threshold = threshold_dict[threshold_choose]


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

    def multiplier_line(record, title="倍率線型", ylim=0.16, start=0):
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


# func
class cfunc:
    """
    常用func
    """

    def __init__(self) -> None:
        pass


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

            if round < 10**5:
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

    def output_data(datas, names, path, file_name=""):
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


# reel
class reel:
    """
    輪帶相關
    """

    def __init__(self) -> None:
        pass

    class generate_reel:
        """
        可以設定固定間隔(接近)、至少間隔多長
        """

        def __init__(self, symbol_dict, symbol_num_list, stack_rate_arr, stack_list):
            # setting
            self.symbol_dict = symbol_dict  # 所有符號種類
            self.all_stack_option = stack_list  # 所有堆疊選項
            self.symbol_num_list = symbol_num_list
            self.stack_rate_arr = stack_rate_arr

            # processing
            self.symbol_num = len(symbol_dict)
            self.stack_num = stack_rate_arr.shape[1]

            # initial value
            self.condition_list = []

        class condition_setting:
            def __init__(self, symbol, blank_num, blank_type):
                self.symbol = symbol  # [0, 1, 2]
                self.blank_num = blank_num
                self.blank_type = blank_type  # (間隔數, type) 1:固定間格, 2:至少間格

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
        def randon_value(arr):

            # func
            get_prob = lambda weight: weight / weight.sum()

            # random
            symbol_weight = arr.sum(axis=1)
            rd_symbol = np.random.choice([i for i in range(arr.shape[0])], p=get_prob(symbol_weight))

            stack_weight = arr[rd_symbol]
            rd_stack = np.random.choice([i for i in range(arr.shape[1])], p=get_prob(stack_weight))

            return rd_symbol, rd_stack

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

            stack_num_arr = np.zeros(self.stack_rate_arr.shape, dtype=np.int32)

            for i in range(self.symbol_num):
                # setting
                setting_stack_rate = self.stack_rate_arr[i]

                total_num = self.symbol_num_list[i]
                setting_stack_rate = self.stack_rate_arr[i]

                # calculate
                stack_num_arr[i] = get_symbol_stack_num_1xn(total_num, setting_stack_rate)

            return stack_num_arr

        def choose_pool_arr(self, arr, reel):

            for i, condition in enumerate(self.condition_list):
                pre_symbol_list = self.get_pre_symbol_list(condition.blank_num, reel)
                symbol_in_list_bool = self.check_list_in_list(condition.symbol, pre_symbol_list)

                bool_arr_1xn = np.ones(self.symbol_num, dtype=np.int16)

                if condition.blank_type == 1 and not symbol_in_list_bool:  # 固定間格。沒有，必定出現
                    if arr[condition.symbol].sum() == 0:
                        continue
                    bool_arr_1xn = np.zeros(self.symbol_num, dtype=np.int16)
                    bool_arr_1xn[condition.symbol] = 1
                    bool_arr_nxm = self.list_2_arr_nxm(bool_arr_1xn, self.stack_num)
                    self.update_arr(arr, arr * bool_arr_nxm)
                    break
                elif condition.blank_type == 1 and symbol_in_list_bool:  # 固定間格。有，不能出現
                    bool_arr_1xn[condition.symbol] = 0

                if condition.blank_type == 3 and not symbol_in_list_bool:  # 最多間格。n格沒出現，必定出現
                    bool_arr_1xn = np.zeros(self.symbol_num, dtype=np.int16)
                    bool_arr_1xn[condition.symbol] = 1

                if condition.blank_type == 2 and symbol_in_list_bool:  # 至少間格。相同標誌、種類不要連續出現
                    bool_arr_1xn[condition.symbol] = 0

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

            new_reel = []  # 目標

            while stack_num_arr.sum() > 0:
                # pool setting
                pool_arr = stack_num_arr.copy()
                self.choose_pool_arr(pool_arr, new_reel)

                # random "symbol" and "stack"
                symbol, stack = self.randon_value(pool_arr)

                # update "stack_num_arr" and "reel"
                stack_num_arr[symbol, stack] -= 1
                for _ in range(stack + 1):
                    new_reel.append(symbol)

            if show_type == 0:
                return new_reel
            elif show_type == 1:
                return [self.symbol_dict[i] for i in new_reel]

        def generate_reel_n(self, try_times, reel_type: reel_type = reel_type.symbol_id):
            cnt = 0
            for _ in range(try_times):
                try:
                    new_reel = self.generate_reel(reel_type)
                    print(f"run times: {cnt}")
                    break
                except ValueError as e:
                    print(f"error: {e}")

                cnt += 1

            return new_reel
