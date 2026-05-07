# %%

import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from numba import jit, njit
import math
import os

os.chdir("C:\\Users\\rhinshen\\Mine\\個人工作區\\2_Program")


import Project.Slots.Source.H015_Box as Box
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
                [2, "M1", 3, 3, 0, 0, 0],
                [3, "M2", 3, 3, 0, 0, 0],
                [4, "M3", 7, 7, 0, 0, 0],
                [5, "M4", 43, 43, 0, 0, 0],
                [6, "M5", 42, 42, 0, 0, 0],
                [7, "A", 43, 43, 0, 0, 0],
                [8, "K", 43, 43, 0, 0, 0],
                [9, "Q", 7, 7, 0, 0, 0],
                [10, "J", 7, 7, 0, 0, 0],
                [11, "G1", 0, 0, 0, 0, 0],
                [12, "G2", 0, 0, 0, 0, 0],
                [13, "G3", 0, 0, 0, 0, 0],
                [14, "G4", 0, 0, 0, 0, 0],
                [15, "G5", 0, 0, 0, 0, 0],
                [16, "GA", 0, 0, 0, 0, 0],
                [17, "GK", 0, 0, 0, 0, 0],
                [18, "GQ", 0, 0, 0, 0, 0],
                [19, "GJ", 0, 0, 0, 0, 0],
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
                [2, "M1", 10, 10, 0, 0, 0],
                [3, "M2", 12, 12, 0, 0, 0],
                [4, "M3", 13, 13, 0, 0, 0],
                [5, "M4", 22, 22, 0, 0, 0],
                [6, "M5", 22, 22, 0, 0, 0],
                [7, "A", 27, 27, 0, 0, 0],
                [8, "K", 24, 24, 0, 0, 0],
                [9, "Q", 12, 12, 0, 0, 0],
                [10, "J", 8, 8, 0, 0, 0],
                [11, "G1", 2, 2, 0, 0, 0],
                [12, "G2", 3, 3, 0, 0, 0],
                [13, "G3", 3, 3, 0, 0, 0],
                [14, "G4", 8, 8, 0, 0, 0],
                [15, "G5", 8, 8, 0, 0, 0],
                [16, "GA", 10, 10, 0, 0, 0],
                [17, "GK", 9, 9, 0, 0, 0],
                [18, "GQ", 3, 3, 0, 0, 0],
                [19, "GJ", 2, 2, 0, 0, 0],
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
                [2, "M1", 0, 0, 0, 0, 0],
                [3, "M2", 0, 0, 0, 0, 0],
                [4, "M3", 0, 0, 0, 0, 0],
                [5, "M4", 0, 0, 0, 0, 0],
                [6, "M5", 0, 0, 0, 0, 0],
                [7, "A", 0, 0, 0, 0, 0],
                [8, "K", 0, 0, 0, 0, 0],
                [9, "Q", 0, 0, 0, 0, 0],
                [10, "J", 0, 0, 0, 0, 0],
                [11, "G1", 3, 3, 0, 0, 0],
                [12, "G2", 1, 1, 0, 0, 0],
                [13, "G3", 8, 8, 0, 0, 0],
                [14, "G4", 43, 43, 0, 0, 0],
                [15, "G5", 42, 42, 0, 0, 0],
                [16, "GA", 42, 42, 0, 0, 0],
                [17, "GK", 44, 44, 0, 0, 0],
                [18, "GQ", 6, 6, 0, 0, 0],
                [19, "GJ", 9, 9, 0, 0, 0],
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
                [1, "C1", 3, 3, 0, 0, 0],
                [2, "M1", 3, 3, 0, 0, 0],
                [3, "M2", 3, 3, 0, 0, 0],
                [4, "M3", 7, 7, 0, 0, 0],
                [5, "M4", 31, 31, 0, 0, 0],
                [6, "M5", 27, 27, 0, 0, 0],
                [7, "A", 31, 31, 0, 0, 0],
                [8, "K", 32, 32, 0, 0, 0],
                [9, "Q", 6, 6, 0, 0, 0],
                [10, "J", 7, 7, 0, 0, 0],
                [11, "G1", 1, 1, 0, 0, 0],
                [12, "G2", 1, 1, 0, 0, 0],
                [13, "G3", 2, 2, 0, 0, 0],
                [14, "G4", 11, 11, 0, 0, 0],
                [15, "G5", 12, 12, 0, 0, 0],
                [16, "GA", 10, 10, 0, 0, 0],
                [17, "GK", 10, 10, 0, 0, 0],
                [18, "GQ", 1, 1, 0, 0, 0],
                [19, "GJ", 2, 2, 0, 0, 0],
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
                [1, "C1", 3, 3, 0, 0, 0],
                [2, "M1", 9, 9, 0, 0, 0],
                [3, "M2", 8, 8, 0, 0, 0],
                [4, "M3", 14, 14, 0, 0, 0],
                [5, "M4", 36, 36, 0, 0, 0],
                [6, "M5", 34, 34, 0, 0, 0],
                [7, "A", 35, 35, 0, 0, 0],
                [8, "K", 34, 34, 0, 0, 0],
                [9, "Q", 13, 13, 0, 0, 0],
                [10, "J", 14, 14, 0, 0, 0],
                [11, "G1", 0, 0, 0, 0, 0],
                [12, "G2", 0, 0, 0, 0, 0],
                [13, "G3", 0, 0, 0, 0, 0],
                [14, "G4", 0, 0, 0, 0, 0],
                [15, "G5", 0, 0, 0, 0, 0],
                [16, "GA", 0, 0, 0, 0, 0],
                [17, "GK", 0, 0, 0, 0, 0],
                [18, "GQ", 0, 0, 0, 0, 0],
                [19, "GJ", 0, 0, 0, 0, 0],
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
    for col in _temp:
        df[col] = df[col].astype(int)

    GR = Mat.reel_v2.generate_reel(df[columns_name_setting], df[columns_name_stake])
    GR.new_condition(symbol=[1], blank_num=6, blank_type=2)
    GR.new_condition(symbol=[2], blank_num=1, blank_type=2)
    GR.new_condition(symbol=[3], blank_num=1, blank_type=2)
    GR.new_condition(symbol=[4], blank_num=1, blank_type=2)
    GR.new_condition(symbol=[5], blank_num=1, blank_type=2)
    GR.new_condition(symbol=[6], blank_num=1, blank_type=2)
    GR.new_condition(symbol=[7], blank_num=1, blank_type=2)
    GR.new_condition(symbol=[8], blank_num=1, blank_type=2)
    GR.new_condition(symbol=[9], blank_num=1, blank_type=2)
    GR.new_condition(symbol=[10], blank_num=1, blank_type=2)

    GR.new_condition(symbol=[11], blank_num=1, blank_type=2)
    GR.new_condition(symbol=[12], blank_num=1, blank_type=2)
    GR.new_condition(symbol=[13], blank_num=1, blank_type=2)
    GR.new_condition(symbol=[14], blank_num=1, blank_type=2)
    GR.new_condition(symbol=[15], blank_num=1, blank_type=2)
    GR.new_condition(symbol=[16], blank_num=1, blank_type=2)
    GR.new_condition(symbol=[17], blank_num=1, blank_type=2)
    GR.new_condition(symbol=[18], blank_num=1, blank_type=2)
    GR.new_condition(symbol=[19], blank_num=1, blank_type=2)

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
