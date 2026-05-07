# %% ----- Import -----


import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import random as rd
from numba import jit
from datetime import datetime

# my package
import Project.Slots.Source.General.RedBox as Red
from Project.Slots.Source.General.RedBox import log_use
from Project.Slots.Source.General.Math import threshold_record


# %% ----- base info -----


# [data]
game_name = "H013_爆破糖果"  # 這個要跟專案資料夾名稱相同
math_version = "0001"

# - resource data
path_math = Red.Path.get_resource_path("Project/Slots/Source/H013_math_data" + ".xlsx")

# - output data
path_plot = "Project/Slots/Record/"
path_output_data = lambda add_info="": "Project/Slots/Record/" + game_name + "_" + math_version + "_" + datetime.now().strftime("%y%m%d%H%M") + add_info + ".xlsx"


# %% ----- setting -----


# [simulator]
mode_narmalbet, mode_extrabet, mode_featurebuy, mode_superfeaturebuy = 0, 1, 2, 3  # 分下注模式
scence_BG, scence_FG = 0, 1  # 分場景 # refer_A
scence_num = 2  # refer_A
# spin_BG, spin_FG = 0, 1  # 分輪帶(還不知道哪裡有用到)
output_BG, output_FG, output_OA = 0, 1, 2  # output使用


# [by game setting]
# - window
window_size = np.array([5, 5], np.int8)  # refer_A
reel_num = np.array([6, 6], np.int8)

# - bet setting
normalbet = 1
extrabet = 1.25
featurebuy = 75
superfeaturebuy = 500

# - free game
# initial_free_spins = 10
extra_spin_high = 1
extra_spin_low = 4
max_spin_free_game = 50

# - special symbols (沒有就空著)


# %% ----- Get Data -----


def __get_overview(dir, sheet):
    data = pd.read_excel(dir, sheet_name=str(sheet), header=None, index_col=0).T
    return data


def __get_paytable(dir, sheet, awards):
    data = pd.read_excel(dir, sheet_name=str(sheet))
    paytable = data[awards].values
    symbol_str = {id: data.Symbol[i] for i, id in enumerate(data.Id)}
    symbol_id = np.array(data.Id.to_list(), dtype=np.int64)
    return paytable, symbol_str, symbol_id


def __get_strip(dir, sheet_names):

    int_default_value = -1
    int_sheet_counts = len(sheet_names)

    arr_max_shape = [0, 0]
    list_dataframe = []

    for i, sheet_na in enumerate(sheet_names):
        arr_temp_dataframe = pd.read_excel(dir, sheet_name=sheet_na)
        list_dataframe.append(arr_temp_dataframe)

        arr_max_shape[0] = max(arr_max_shape[0], arr_temp_dataframe.shape[0])
        arr_max_shape[1] = max(arr_max_shape[1], arr_temp_dataframe.shape[1])

    arr_reels = np.full(shape=(int_sheet_counts, arr_max_shape[0], arr_max_shape[1]), fill_value=int_default_value, dtype=np.int16)
    for i in range(int_sheet_counts):
        arr_shape_sheet = list_dataframe[i].shape
        for row in range(arr_shape_sheet[0]):
            for column in range(arr_shape_sheet[1]):
                int_fill_value = list_dataframe[i].values[row, column]
                if np.isnan(int_fill_value):
                    continue
                arr_reels[i, row, column] = int_fill_value

    reels_len = np.zeros(shape=(int_sheet_counts, reel_num[0]), dtype=np.int16)
    for sheet in range(int_sheet_counts):
        for reel_i in range(arr_reels[sheet].shape[1]):
            reels_len[sheet][reel_i] = np.count_nonzero(arr_reels[sheet, :, reel_i] != -1)

    return arr_reels, reels_len


def __get_strip_weight(dir, sheet_names):  # 權重RNG

    int_default_value = -1  # 填0沒有資料的地方就不會被random到
    int_sheet_counts = len(sheet_names)

    arr_max_shape = [0, 0]
    list_dataframe = []

    for i, sheet_na in enumerate(sheet_names):
        arr_temp_dataframe = pd.read_excel(dir, sheet_name=sheet_na)
        list_dataframe.append(arr_temp_dataframe)

        arr_max_shape[0] = max(arr_max_shape[0], arr_temp_dataframe.shape[0])
        arr_max_shape[1] = max(arr_max_shape[1], arr_temp_dataframe.shape[1])

    arr_reels_weight = np.full(shape=(int_sheet_counts, arr_max_shape[0], arr_max_shape[1]), fill_value=int_default_value, dtype=np.int16)
    for i in range(int_sheet_counts):
        arr_shape_sheet = list_dataframe[i].shape
        for row in range(arr_shape_sheet[0]):
            for column in range(arr_shape_sheet[1]):
                int_fill_value = list_dataframe[i].values[row, column]
                if np.isnan(int_fill_value):
                    continue
                arr_reels_weight[i, row, column] = int_fill_value

    return arr_reels_weight


def __get_value(dir, sheet, col=[], data_type="float64"):
    data = pd.read_excel(dir, sheet_name=str(sheet))[col].dropna().values.astype(data_type)
    return data


def __get_weight(dir, sheet, col=[], data_type="float64"):
    data = pd.read_excel(dir, sheet_name=str(sheet))[col].dropna().values.astype(data_type)
    data_cum = data.cumsum(axis=0).astype("int64")
    return data, data_cum


# [overview]
overview = __get_overview(path_math, "overview")

game_ID = overview.game_ID[1]
game_version = overview.game_version[1]
game_RTP = overview.game_RTP[1]


# [pay table]
"""
限制: 所有Symbol Id必須按造順序排，
* ex: 0,1,2,... 可以
* ex: 0,5,6,... 不行
"""
pay_table_C1 = np.array([4, 5, 6])
pay_table_C1_reteigger = np.array([3, 4, 5, 6])
pay_table_awards_cascading = np.array([8, 10, 12])
pay_table, symbol_str, symbol_id = __get_paytable(path_math, "pay_table", np.concatenate([pay_table_C1, pay_table_awards_cascading]))
default_coin_in = 100  # paytable的基礎下注的金額

WW, C1, C2, M1, M2, M3, M4, A, K, Q, J, TE = range(12)  # 這是宣告，可以亂填
for i, symbol in enumerate(symbol_str.values()):  # 這邊才是真的填上去
    globals()[symbol] = symbol_id[i]

symbols_special = np.array([WW, C1, C2], dtype=np.int64)
symbols_main = np.array([M1, M2, M3, M4], dtype=np.int64)
symbols_number = np.array([A, K, Q, J, TE], dtype=np.int64)

symbols_score = np.concatenate([symbols_main, symbols_number])  # 盤面算分
symbols_all = np.concatenate([symbols_special, symbols_main, symbols_number])

symbols_count = len(symbol_str)


# %%

# [strip]
strip_BG, strip_BG2, strip_BG3, strip_BG4 = range(0, 4)  # 輪帶編號, (A, B, C)。strip_BG4是Feature Buy用的BG輪帶
strip_EB, strip_EB2, strip_EB3 = range(4, 7)
strip_FG, strip_FG2 = range(7, 9)  # (Low, High)
strip_FB, strip_FB2 = range(9, 11)
strip_SB, strip_SB2 = range(11, 13)

sheet_names_BG = ["BG_strip", "BG_strip (2)", "BG_strip (3)", "BG_strip (4)"]
sheet_names_EB = ["EB_strip", "EB_strip (2)", "EB_strip (3)"]
sheet_names_FG = ["FG_strip", "FG_strip (2)"]
sheet_names_FB = ["FB_strip", "FB_strip (2)"]
sheet_names_SB = ["SB_strip", "SB_strip (2)"]
arr_reels, reels_len = __get_strip(path_math, sheet_names_BG + sheet_names_EB + sheet_names_FG + sheet_names_FB + sheet_names_SB)

sheet_names_BG_weight = ["BG_strip_weight", "BG_strip_weight (2)", "BG_strip_weight (3)", "BG_strip_weight (4)"]
sheet_names_EB_weight = ["EB_strip_weight", "EB_strip_weight (2)", "EB_strip_weight (3)"]
sheet_names_FG_weight = ["FG_strip_weight", "FG_strip_weight (2)"]
sheet_names_FB_weight = ["FB_strip_weight", "FB_strip_weight (2)"]
sheet_names_SB_weight = ["SB_strip_weight", "SB_strip_weight (2)"]
arr_reels_weight = __get_strip_weight(path_math, sheet_names_BG_weight + sheet_names_EB_weight + sheet_names_FG_weight + sheet_names_FB_weight + sheet_names_SB_weight)

# [value]
# value_xxx = __get_value(path_math, "value", "xxx") # 範例
value_multiplier = __get_value(path_math, "value", "multiplier_range", data_type=np.int64)  # 範例

# [weight]
# weight_xxx, weight_cum_xxx = __get_weight(path_math, "weight", col="xxx") # 範例
weight_table_normal_bet, weight_cum_table_normal_bet = __get_weight(path_math, "weight", col="table_normal_bet", data_type=np.int64)
weight_table_extra_bet, weight_cum_table_extra_bet = __get_weight(path_math, "weight", col="table_extra_bet", data_type=np.int64)
weight_table_multiplier_range_FG_low, weight_cum_table_multiplier_range_FG_low = __get_weight(path_math, "weight", col="multiplier_range_FG_low", data_type=np.int64)
weight_table_multiplier_range_FG_high, weight_cum_table_multiplier_range_FG_high = __get_weight(path_math, "weight", col="multiplier_range_FG_high", data_type=np.int64)
weight_table_multiplier_range_FB_low, weight_cum_table_multiplier_range_FB_low = __get_weight(path_math, "weight", col="multiplier_range_FB_low", data_type=np.int64)
weight_table_multiplier_range_FB_high, weight_cum_table_multiplier_range_FB_high = __get_weight(path_math, "weight", col="multiplier_range_FB_high", data_type=np.int64)
weight_table_multiplier_range_SB_low, weight_cum_table_multiplier_range_SB_low = __get_weight(path_math, "weight", col="multiplier_range_SB_low", data_type=np.int64)
weight_table_multiplier_range_SB_high, weight_cum_table_multiplier_range_SB_high = __get_weight(path_math, "weight", col="multiplier_range_SB_high", data_type=np.int64)

# * [special]


# %% ----- Record -----

record_cols = max(len(threshold_record), len(symbols_all) * scence_num)
record_size = (40, record_cols)


# x
R_all = 0
R_multiplier_range_cnt_BG = 1
R_multiplier_range_cnt_FG = 2
R_multiplier_range_cnt_OA = 3
R_hits = (5, 10)
R_pay = (10, 15)
R_combo = (15, 20)
R_eliminate = (20, 25)

# x=0
RA_hits_BG = 0  # BG 的 Hit Rate
RA_hits_FG = 1  # FG 的 Hit Rate
RA_trigger_freegame = 2  # FG 的觸發次數
RA_re_trigger = 3  # FG re-trigger 的觸發次數
RA_free_spins = 4  # FG spin 的次數
RA_x_sum = 5  # 標準差
RA_x_square = 6  # 標準差

# x=0, Special (by game)


# %% ----- Format -----

plot_name = "倍率線型_" + game_name + "_"
# f_multi_line_xlsx_name = lambda x: f"倍率線型_{Mat.threshold_record_version}_" + slot_name + f"_BET{int(pay_line)}" + "_"  # + game_type[x]


# %%
