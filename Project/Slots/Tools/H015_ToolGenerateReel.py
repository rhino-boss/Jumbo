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
                [1, "C1", 3, 3, 0, 0, 0],
                [2, "C2", 0, 0, 0, 0, 0],
                [3, "M1", 23, 23, 0, 0, 0],
                [4, "M2", 49, 45, 2, 0, 0],
                [5, "M3", 7, 7, 0, 0, 0],
                [6, "M4", 49, 45, 2, 0, 0],
                [7, "A", 4, 4, 0, 0, 0],
                [8, "K", 4, 4, 0, 0, 0],
                [9, "Q", 57, 53, 2, 0, 0],
                [10, "J", 4, 0, 2, 0, 0],
                [11, "G1", 0, 0, 0, 0, 0],
                [12, "G2", 0, 0, 0, 0, 0],
                [13, "G3", 0, 0, 0, 0, 0],
                [14, "G4", 0, 0, 0, 0, 0],
                [15, "GA", 0, 0, 0, 0, 0],
                [16, "GK", 0, 0, 0, 0, 0],
                [17, "GQ", 0, 0, 0, 0, 0],
                [18, "GJ", 0, 0, 0, 0, 0],
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
                [2, "C2", 0, 0, 0, 0, 0],
                [3, "M1", 2, -2, 2, 0, 0],
                [4, "M2", 3, 3, 0, 0, 0],
                [5, "M3", 22, 18, 2, 0, 0],
                [6, "M4", 4, 4, 0, 0, 0],
                [7, "A", 41, 37, 2, 0, 0],
                [8, "K", 59, 55, 2, 0, 0],
                [9, "Q", 4, 4, 0, 0, 0],
                [10, "J", 62, 62, 0, 0, 0],
                [11, "G1", 0, 0, 0, 0, 0],
                [12, "G2", 0, 0, 0, 0, 0],
                [13, "G3", 0, 0, 0, 0, 0],
                [14, "G4", 0, 0, 0, 0, 0],
                [15, "GA", 0, 0, 0, 0, 0],
                [16, "GK", 0, 0, 0, 0, 0],
                [17, "GQ", 0, 0, 0, 0, 0],
                [18, "GJ", 0, 0, 0, 0, 0],
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
                [2, "C2", 0, 0, 0, 0, 0],
                [3, "M1", 37, 37, 0, 0, 0],
                [4, "M2", 32, 28, 2, 0, 0],
                [5, "M3", 6, 6, 0, 0, 0],
                [6, "M4", 43, 39, 2, 0, 0],
                [7, "A", 8, 8, 0, 0, 0],
                [8, "K", 10, 10, 0, 0, 0],
                [9, "Q", 39, 35, 2, 0, 0],
                [10, "J", 7, 3, 2, 0, 0],
                [11, "G1", 2, 2, 0, 0, 0],
                [12, "G2", 2, 2, 0, 0, 0],
                [13, "G3", 2, 2, 0, 0, 0],
                [14, "G4", 2, 2, 0, 0, 0],
                [15, "GA", 2, 2, 0, 0, 0],
                [16, "GK", 2, 2, 0, 0, 0],
                [17, "GQ", 2, 2, 0, 0, 0],
                [18, "GJ", 2, 2, 0, 0, 0],
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
                [2, "C2", 0, 0, 0, 0, 0],
                [3, "M1", 12, 8, 2, 0, 0],
                [4, "M2", 15, 15, 0, 0, 0],
                [5, "M3", 26, 22, 2, 0, 0],
                [6, "M4", 16, 16, 0, 0, 0],
                [7, "A", 30, 26, 2, 0, 0],
                [8, "K", 31, 27, 2, 0, 0],
                [9, "Q", 18, 18, 0, 0, 0],
                [10, "J", 34, 34, 0, 0, 0],
                [11, "G1", 2, 2, 0, 0, 0],
                [12, "G2", 2, 2, 0, 0, 0],
                [13, "G3", 2, 2, 0, 0, 0],
                [14, "G4", 2, 2, 0, 0, 0],
                [15, "GA", 2, 2, 0, 0, 0],
                [16, "GK", 2, 2, 0, 0, 0],
                [17, "GQ", 2, 2, 0, 0, 0],
                [18, "GJ", 2, 2, 0, 0, 0],
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
                [1, "C1", 1, 1, 0, 0, 0],
                [2, "C2", 0, 0, 0, 0, 0],
                [3, "M1", 14, 10, 2, 0, 0],
                [4, "M2", 17, 17, 0, 0, 0],
                [5, "M3", 25, 21, 2, 0, 0],
                [6, "M4", 23, 23, 0, 0, 0],
                [7, "A", 30, 26, 2, 0, 0],
                [8, "K", 33, 29, 2, 0, 0],
                [9, "Q", 24, 24, 0, 0, 0],
                [10, "J", 33, 33, 0, 0, 0],
                [11, "G1", 0, 0, 0, 0, 0],
                [12, "G2", 0, 0, 0, 0, 0],
                [13, "G3", 0, 0, 0, 0, 0],
                [14, "G4", 0, 0, 0, 0, 0],
                [15, "GA", 0, 0, 0, 0, 0],
                [16, "GK", 0, 0, 0, 0, 0],
                [17, "GQ", 0, 0, 0, 0, 0],
                [18, "GJ", 0, 0, 0, 0, 0],
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
                [1, "C1", 1, 1, 0, 0, 0],
                [2, "C2", 0, 0, 0, 0, 0],
                [3, "M1", 12, 12, 0, 0, 0],
                [4, "M2", 27, 23, 2, 0, 0],
                [5, "M3", 13, 13, 0, 0, 0],
                [6, "M4", 32, 28, 2, 0, 0],
                [7, "A", 25, 25, 0, 0, 0],
                [8, "K", 29, 29, 0, 0, 0],
                [9, "Q", 37, 33, 2, 0, 0],
                [10, "J", 24, 20, 2, 0, 0],
                [11, "G1", 0, 0, 0, 0, 0],
                [12, "G2", 0, 0, 0, 0, 0],
                [13, "G3", 0, 0, 0, 0, 0],
                [14, "G4", 0, 0, 0, 0, 0],
                [15, "GA", 0, 0, 0, 0, 0],
                [16, "GK", 0, 0, 0, 0, 0],
                [17, "GQ", 0, 0, 0, 0, 0],
                [18, "GJ", 0, 0, 0, 0, 0],
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
