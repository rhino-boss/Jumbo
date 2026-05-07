# %%

import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from numba import jit, njit
import math
import os

os.chdir("C:\\Users\\rhinshen\\Mine\\個人工作區\\2_Program")

import Project.Slots.Source.H013_Box as Box
import Project.Slots.Source.General.Math as Mat


# %%

columns_name = ["symbol_id", "symbol_str", "symbol_count", 1, 2, 3, 5]
columns_name_setting = columns_name[:3]
columns_name_stake = columns_name[3:]

df_list = []


# -----------------
df_list.append(
    pd.DataFrame(
        np.array(
            [
                [0, "WW", 0, 0, 0, 0, 0],
                [1, "C1", 2, 2, 0, 0, 0],
                [2, "C2", 4, 4, 0, 0, 0],
                [3, "M1", 6, 0, 3, 0, 0],
                [4, "M2", 14, 0, 7, 0, 0],
                [5, "M3", 12, 0, 6, 0, 0],
                [6, "M4", 18, 0, 9, 0, 0],
                [7, "A", 12, 0, 6, 0, 0],
                [8, "K", 30, 0, 15, 0, 0],
                [9, "Q", 26, 0, 13, 0, 0],
                [10, "J", 36, 0, 18, 0, 0],
                [11, "TE", 40, 0, 20, 0, 0],
            ]
        ),
        columns=columns_name,
    )
)


df_list.append(
    pd.DataFrame(
        np.array(
            [
                [0, "WW", 0, 0, 0, 0, 0],
                [1, "C1", 4, 4, 0, 0, 0],
                [2, "C2", 8, 8, 0, 0, 0],
                [3, "M1", 8, 0, 4, 0, 0],
                [4, "M2", 16, 0, 8, 0, 0],
                [5, "M3", 14, 0, 7, 0, 0],
                [6, "M4", 18, 0, 9, 0, 0],
                [7, "A", 10, 0, 5, 0, 0],
                [8, "K", 26, 0, 13, 0, 0],
                [9, "Q", 32, 0, 16, 0, 0],
                [10, "J", 34, 0, 17, 0, 0],
                [11, "TE", 30, 0, 15, 0, 0],
            ]
        ),
        columns=columns_name,
    )
)


df_list.append(
    pd.DataFrame(
        np.array(
            [
                [0, "WW", 0, 0, 0, 0, 0],
                [1, "C1", 2, 2, 0, 0, 0],
                [2, "C2", 4, 4, 0, 0, 0],
                [3, "M1", 14, 0, 7, 0, 0],
                [4, "M2", 20, 0, 10, 0, 0],
                [5, "M3", 14, 0, 7, 0, 0],
                [6, "M4", 20, 0, 10, 0, 0],
                [7, "A", 26, 0, 13, 0, 0],
                [8, "K", 30, 0, 15, 0, 0],
                [9, "Q", 20, 0, 10, 0, 0],
                [10, "J", 26, 0, 13, 0, 0],
                [11, "TE", 24, 0, 12, 0, 0],
            ]
        ),
        columns=columns_name,
    )
)


df_list.append(
    pd.DataFrame(
        np.array(
            [
                [0, "WW", 0, 0, 0, 0, 0],
                [1, "C1", 4, 4, 0, 0, 0],
                [2, "C2", 2, 2, 0, 0, 0],
                [3, "M1", 12, 0, 6, 0, 0],
                [4, "M2", 14, 0, 7, 0, 0],
                [5, "M3", 18, 0, 9, 0, 0],
                [6, "M4", 22, 0, 11, 0, 0],
                [7, "A", 12, 0, 6, 0, 0],
                [8, "K", 12, 0, 6, 0, 0],
                [9, "Q", 26, 0, 13, 0, 0],
                [10, "J", 36, 0, 18, 0, 0],
                [11, "TE", 42, 0, 21, 0, 0],
            ]
        ),
        columns=columns_name,
    )
)


df_list.append(
    pd.DataFrame(
        np.array(
            [
                [0, "WW", 0, 0, 0, 0, 0],
                [1, "C1", 2, 2, 0, 0, 0],
                [2, "C2", 4, 4, 0, 0, 0],
                [3, "M1", 6, 0, 3, 0, 0],
                [4, "M2", 14, 0, 7, 0, 0],
                [5, "M3", 14, 0, 7, 0, 0],
                [6, "M4", 22, 0, 11, 0, 0],
                [7, "A", 16, 0, 8, 0, 0],
                [8, "K", 26, 0, 13, 0, 0],
                [9, "Q", 38, 0, 19, 0, 0],
                [10, "J", 26, 0, 13, 0, 0],
                [11, "TE", 32, 0, 16, 0, 0],
            ]
        ),
        columns=columns_name,
    )
)


df_list.append(
    pd.DataFrame(
        np.array(
            [
                [0, "WW", 0, 0, 0, 0, 0],
                [1, "C1", 4, 4, 0, 0, 0],
                [2, "C2", 6, 6, 0, 0, 0],
                [3, "M1", 8, 0, 4, 0, 0],
                [4, "M2", 14, 0, 7, 0, 0],
                [5, "M3", 12, 0, 6, 0, 0],
                [6, "M4", 20, 0, 10, 0, 0],
                [7, "A", 12, 0, 6, 0, 0],
                [8, "K", 26, 0, 13, 0, 0],
                [9, "Q", 38, 0, 19, 0, 0],
                [10, "J", 26, 0, 13, 0, 0],
                [11, "TE", 34, 0, 17, 0, 0],
            ]
        ),
        columns=columns_name,
    )
)


# -----------------


new_reel_list = []
for i, df in enumerate(df_list):

    _temp = columns_name.copy()
    _temp.remove("symbol_str")
    df.loc[:, _temp] = df.loc[:, _temp].astype(int)

    GR = Mat.reel_v2.generate_reel(df[columns_name_setting], df[columns_name_stake])
    GR.new_condition(symbol=[0, 1, 2], blank_num=2, blank_type=2)
    # GR.new_condition(symbol=[0, 20, 21, 22, 23, 24], blank_num=2, blank_type=2)
    GR.new_condition(symbol=[0, 3], blank_num=2, blank_type=2)
    GR.new_condition(symbol=[0, 4], blank_num=2, blank_type=2)
    GR.new_condition(symbol=[0, 5], blank_num=2, blank_type=2)
    GR.new_condition(symbol=[0, 6], blank_num=2, blank_type=2)
    GR.new_condition(symbol=[7], blank_num=2, blank_type=2)
    GR.new_condition(symbol=[8], blank_num=2, blank_type=2)
    GR.new_condition(symbol=[9], blank_num=2, blank_type=2)
    GR.new_condition(symbol=[10], blank_num=2, blank_type=2)
    GR.new_condition(symbol=[11], blank_num=2, blank_type=2)

    new_reel = GR.generate_reel_n(try_times=200, reel_type=GR.reel_type.symbol_str)
    new_reel_list.append(new_reel)


# %%


# 找出最長的 List 長度
max_length = max(len(li) for li in new_reel_list)
# print(max_length)

# 補齊每個 List 的長度（用空字串補）
for i in range(5):
    new_reel_list[i] += [""] * (max_length - len(new_reel_list[i]))


# 印出來，每一列是每個 List 相同 index 的元素
for i in range(max_length):
    row = [new_reel_list[col][i] for col in range(len(new_reel_list))]
    print("\t".join(row))


# %%


# def map_multiplier_big2small(range_small, range_big, data_big):
#     """
#     記中位數會用到
#     """
#     arr_cum = np.zeros(len(range_big), dtype=np.int64)
#     for i, v in enumerate(range_big):
#         if v in range_small:
#             arr_cum[i] = v
#         else:
#             arr_cum[i] = 0

#     arr_cum = arr_cum[::-1]
#     temp_value = arr_cum[-1]
#     for i, v in enumerate(arr_cum):
#         if v == 0 and i != len(arr_cum) - 1:
#             arr_cum[i] = temp_value
#         else:
#             temp_value = arr_cum[i]

#     df_cum = pd.DataFrame({"range": arr_cum[::-1], "value": data_big})
#     new_data = df_cum.groupby("range").sum().values.T[0]

#     return new_data


# def map_multiplier_big2small_v2(range_small, range_big, data_big):
#     arr_cum = np.zeros(len(range_big), dtype=np.int64)

#     for i, rr in enumerate(range_big):
#         if rr in range_small:
#             arr_cum[i] = rr

#     for i, rr in enumerate(arr_cum):
#         if rr == 0:
#             arr_cum[i] = arr_cum[i + 1]

#     new_data = np.zeros(len(range_big), dtype=np.int64)
#     for i, rr in enumerate(arr_cum):
#         new_data[range_small.index(rr)] += data_big[i]

#     return new_data


# range_small = [10, 20, 30]
# range_big = [5, 10, 15, 20, 25, 30]
# data_big = [1, 2, 3, 4, 5, 6]

# map_multiplier_big2small_v2(range_small, range_big, data_big)


# %%


# range_small = [1, 5, 10, 20, 99]
# range_big = [1, 2, 5, 9, 10, 20, 30, 999]
# data_big = [1, 2, 3, 4, 5, 6, 7, 10, 100]
# print(range_small)
# print(range_big)
# print("data_big")
# print(data_big)


# ------------

# arr_cum = np.zeros(len(range_big), dtype=np.int64)

# for i, rr in enumerate(range_big):
#     if rr in range_small:
#         arr_cum[i] = rr

# for i, rr in enumerate(arr_cum):
#     if rr == 0:
#         arr_cum[i] = arr_cum[i + 1]

# new_data = np.zeros(len(range_big), dtype=np.int64)
# for i, rr in enumerate(arr_cum):
#     new_data[range_small.index(rr)] += data_big[i]

# print(arr_cum)
# print(new_data)

# %%
