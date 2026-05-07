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
game_name = "H015_賞金列車"  # 這個要跟專案資料夾名稱相同
math_version = "0001"

# - resource data
# path_math = Red.Path.get_resource_path("Project/Slots/Source/H015_math_data" + ".xlsx")
path_math = Red.Path.get_resource_path("Project/Slots/Source/H015_math_data_送驗版" + ".xlsx")

# - output data
path_plot = "Project/Slots/Record/"
path_output_data = lambda add_info="": "Project/Slots/Record/" + game_name + "_" + datetime.now().strftime("%y%m%d%H%M") + add_info + ".xlsx"


# %% ----- setting -----


# [simulator]
mode_normalbet, mode_featurebuy = 0, 2  # 分下注模式
scence_BG, scence_FG = 0, 1  # 分場景 # refer_A
scence_num = 2  # refer_A
# spin_BG, spin_FG = 0, 1  # 分輪帶(還不知道哪裡有用到)
output_BG, output_FG, output_OA = 0, 1, 2  # output使用


# [by game setting]
# - window
window_size = 5
reel_num = 6
layout_shape = (5, 6)
score_area = np.array(
    [
        [1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1],
        [0, 1, 1, 1, 1, 0],
        [0, 0, 1, 1, 0, 0],
    ],
    np.int64,
)
special_area = np.array(
    [
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [99, 0, 0, 0, 0, 99],
        [99, 99, 0, 0, 99, 99],
    ],
    np.int64,
)

# - bet setting
normalbet = 1
featurebuy = 75

# - free game
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


def __get_strip(dir, sheet_names, reels_idx):

    int_default_value = -1
    int_sheet_counts = len(sheet_names)

    arr_max_shape = [0, 0]
    list_arr = []
    reel_num = len(reels_idx)

    for i, sheet_na in enumerate(sheet_names):
        arr_temp = pd.read_excel(dir, sheet_name=sheet_na).values[:, reels_idx]
        list_arr.append(arr_temp)
        arr_max_shape[0] = max(arr_max_shape[0], arr_temp.shape[0])

    arr_reels = np.full(shape=(int_sheet_counts, arr_max_shape[0], reel_num), fill_value=int_default_value, dtype=np.int16)
    for i in range(int_sheet_counts):
        arr_shape_sheet = list_arr[i].shape
        for row in range(arr_shape_sheet[0]):
            for column in range(arr_shape_sheet[1]):
                int_fill_value = list_arr[i][row, column]
                if np.isnan(int_fill_value):
                    continue
                arr_reels[i, row, column] = int_fill_value

    reels_len = np.zeros(shape=(int_sheet_counts, reel_num), dtype=np.int16)
    for sheet in range(int_sheet_counts):
        for reel_i in range(arr_reels[sheet].shape[1]):
            reels_len[sheet][reel_i] = np.count_nonzero(arr_reels[sheet, :, reel_i] != -1)

    return arr_reels, reels_len


def __get_value(dir, sheet, col=[], data_type="float64"):
    data = pd.read_excel(dir, sheet_name=str(sheet))[col].dropna().values.astype(data_type)
    return data


def __get_weight(dir, sheet, col=[], data_type="int64"):
    data = pd.read_excel(dir, sheet_name=str(sheet))[col].dropna().values.astype(data_type)
    data_cum = data.cumsum(axis=0).astype("int64")
    return data, data_cum


# Special
def __get_drop_weight(dir, sheet_names, symbol_num, col=[], data_type="int64"):

    int_default_value = 0
    sheet_len = len(sheet_names)

    data = np.full(shape=(sheet_len, 4, symbol_num, reel_num), fill_value=int_default_value, dtype=np.int64)
    data_cum = np.full(shape=(sheet_len, 4, symbol_num, reel_num), fill_value=int_default_value, dtype=np.int64)
    for sheet_id, sheet in enumerate(sheet_names):
        data_temp = pd.read_excel(dir, sheet_name=str(sheet))[col].dropna().values.astype(data_type)
        data_1 = data_temp[symbol_num * 0 : symbol_num * 1, :]
        data_2 = data_temp[symbol_num * 1 : symbol_num * 2, :]
        data_3 = data_temp[symbol_num * 2 : symbol_num * 3, :]
        data_4 = data_temp[symbol_num * 3 : symbol_num * 4, :]
        data_cum_1 = data_1.cumsum(axis=0).astype(data_type)
        data_cum_2 = data_2.cumsum(axis=0).astype(data_type)
        data_cum_3 = data_3.cumsum(axis=0).astype(data_type)
        data_cum_4 = data_4.cumsum(axis=0).astype(data_type)
        list_data = [data_1, data_2, data_3, data_4]
        list_data_cum = [data_cum_1, data_cum_2, data_cum_3, data_cum_4]
        for combo in range(4):
            for symbol in range(symbol_num):
                for reel in range(data_temp.shape[1]):
                    data[sheet_id, combo, symbol, reel] = list_data[combo][symbol, reel]
                    data_cum[sheet_id, combo, symbol, reel] = list_data_cum[combo][symbol, reel]

    return data, data_cum


def __get_multi_appear_weight(dir, sheet, col=[], data_type="int64"):
    int_default_value = 0
    data_shape = (7, len(col))

    data = pd.read_excel(dir, sheet_name=str(sheet))[col].dropna().values.astype(data_type)
    data_1 = data[0:7, :]
    data_2 = data[7:14, :]
    data_3 = data[14:21, :]
    data_4 = data[21:28, :]
    data_5 = data[28:35, :]
    data_cum_1 = data[0:7, :].cumsum(axis=0).astype(data_type)
    data_cum_2 = data[7:14, :].cumsum(axis=0).astype(data_type)
    data_cum_3 = data[14:21, :].cumsum(axis=0).astype(data_type)
    data_cum_4 = data[21:28, :].cumsum(axis=0).astype(data_type)
    data_cum_5 = data[28:35, :].cumsum(axis=0).astype(data_type)

    list_data = [data_1, data_2, data_3, data_4, data_5]
    list_data_cum = [data_cum_1, data_cum_2, data_cum_3, data_cum_4, data_cum_5]
    new_data = np.full(shape=(5, data_shape[0], data_shape[1]), fill_value=int_default_value, dtype=np.int64)
    new_data_cum = np.full(shape=(5, data_shape[0], data_shape[1]), fill_value=int_default_value, dtype=np.int64)
    for i in range(5):
        for j in range(data_shape[0]):
            for k in range(data_shape[1]):
                new_data[i][j, k] = list_data[i][j, k]
                new_data_cum[i][j, k] = list_data_cum[i][j, k]

    return new_data, new_data_cum


# %%


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
pay_table_awards = np.array([3, 4, 5, 6])
pay_table, symbol_str, symbol_id = __get_paytable(path_math, "pay_table", pay_table_awards)
default_coin_in = 100  # paytable的基礎下注的金額

WW, C1, C2, M1, M2, M3, M4, A, K, Q, J, G1, G2, G3, G4, GA, GK, GQ, GJ = range(19)  # 這是宣告，可以亂填
for i, symbol in enumerate(symbol_str.values()):  # 這邊才是真的填上去
    globals()[symbol] = symbol_id[i]

symbols_special = np.array([WW, C1, C2], dtype=np.int64)
symbols_main = np.array([M1, M2, M3, M4], dtype=np.int64)
symbols_number = np.array([A, K, Q, J], dtype=np.int64)
symbols_main_gold = np.array([G1, G2, G3, G4], dtype=np.int64)
symbols_number_gold = np.array([GA, GK, GQ, GJ], dtype=np.int64)

symbols_score = np.concatenate([symbols_main, symbols_number])  # 盤面算分
symbols_gold = np.concatenate([symbols_main_gold, symbols_number_gold])  # 盤面算分
symbols_all = np.concatenate([symbols_special, symbols_main, symbols_number, symbols_main_gold, symbols_number_gold])

symbols_count = len(symbol_str)


# [strip]
strip_BG, strip_BG2, strip_FG, strip_FG2, strip_BF = range(0, 5)  # 輪帶編號
sheet_names_BG = ["BG_strip", "BG_strip (2)"]
sheet_names_FG = ["FG_strip", "FG_strip (2)"]
sheet_names_BF = ["BF_strip"]
arr_reels, reels_len = __get_strip(path_math, sheet_names_BG + sheet_names_FG + sheet_names_BF, [0, 1, 2, 3, 4, 5])
arr_reels_weight, __ = __get_strip(path_math, sheet_names_BG + sheet_names_FG + sheet_names_BF, [6, 7, 8, 9, 10, 11])

# [value]
# value_xxx = __get_value(path_math, "value", "xxx") # 範例
value_multiplier_range = __get_value(path_math, "value", "Multiplier_Range")

# [weight]
# weight_xxx, weight_cum_xxx = __get_weight(path_math, "weight", col="xxx") # 範例
weight_table_BG, weight_cum_table_BG = __get_weight(path_math, "weight", col="Table_BG")
weight_table_FG, weight_cum_table_FG = __get_weight(path_math, "weight", col="Table_FG")
weight_table_BF, weight_cum_table_BF = __get_weight(path_math, "weight", col="Table_BF")
weight_drop_choose_bg, weight_cum_drop_choose_bg = __get_weight(path_math, "weight", col="Drop_Symbol_BG")
weight_drop_choose_fg, weight_cum_drop_choose_fg = __get_weight(path_math, "weight", col="Drop_Symbol_FG")
weight_must_appear_1_fg, weight_cum_must_appear_1_fg = __get_weight(path_math, "weight", col="Must_Appear_1")
# weight_multi_appear_bg, weight_cum_multi_appear_bg = __get_weight(path_math, "weight", col=["Multi_Appear_B1A", "Multi_Appear_B1B", "Multi_Appear_B1C", "Multi_Appear_B2A", "Multi_Appear_B2B", "Multi_Appear_B2C"])
# weight_multi_appear_fg, weight_cum_multi_appear_fg = __get_weight(path_math, "weight", col=["Multi_Appear_F1A", "Multi_Appear_F1B", "Multi_Appear_F1C", "Multi_Appear_F2A", "Multi_Appear_F2B", "Multi_Appear_F2C"])

weight_multi_appear_bg, weight_cum_multi_appear_bg = __get_multi_appear_weight(path_math, "weight", col=["Multi_Appear_B1A", "Multi_Appear_B1B", "Multi_Appear_B1C", "Multi_Appear_B2A", "Multi_Appear_B2B", "Multi_Appear_B2C"])
weight_multi_appear_fg, weight_cum_multi_appear_fg = __get_multi_appear_weight(path_math, "weight", col=["Multi_Appear_F1A", "Multi_Appear_F1B", "Multi_Appear_F1C", "Multi_Appear_F2A", "Multi_Appear_F2B", "Multi_Appear_F2C"])


weight_drop_symbol_A, weight_cum_drop_symbol_A = __get_drop_weight(path_math, sheet_names_BG + sheet_names_FG + sheet_names_BF, symbols_count, col=["Drop_Weight_A_R1", "Drop_Weight_A_R2", "Drop_Weight_A_R3", "Drop_Weight_A_R4", "Drop_Weight_A_R5", "Drop_Weight_A_R6"])
weight_drop_symbol_B, weight_cum_drop_symbol_B = __get_drop_weight(path_math, sheet_names_BG + sheet_names_FG + sheet_names_BF, symbols_count, col=["Drop_Weight_B_R1", "Drop_Weight_B_R2", "Drop_Weight_B_R3", "Drop_Weight_B_R4", "Drop_Weight_B_R5", "Drop_Weight_B_R6"])
weight_drop_symbol_C, weight_cum_drop_symbol_C = __get_drop_weight(path_math, sheet_names_BG + sheet_names_FG + sheet_names_BF, symbols_count, col=["Drop_Weight_C_R1", "Drop_Weight_C_R2", "Drop_Weight_C_R3", "Drop_Weight_C_R4", "Drop_Weight_C_R5", "Drop_Weight_C_R6"])


# %% ----- Record -----

record_cols = max(len(threshold_record), len(symbols_all) * scence_num)
record_size = (40, record_cols)


# x
R_all = 0
R_multiplier_range_cnt_BG = 1
R_multiplier_range_cnt_FG = 2
R_multiplier_range_cnt_OA = 3
R_multiplier_range_pay_BG = 4
R_multiplier_range_pay_FG = 5
R_multiplier_range_pay_OA = 6
R_hits = (10, 16)
R_pay = (16, 22)
R_combo = (22, 28)
R_eliminate = (28, 34)

# x=0
RA_hits_BG = 0  # BG 的 Hit Rate
RA_hits_FG = 1  # FG 的 Hit Rate
RA_trigger_freegame = 2  # FG 的觸發次數
RA_re_trigger = 3  # FG re-trigger 的觸發次數
RA_free_spins = 4  # FG spin 的次數
RA_x_sum = 5  # 標準差
RA_x_square = 6  # 標準差

# x=0, Special (by game)
RA_trigger_FG_pay_BG = 7
RA_eliminate_BG = (8, 17)
RA_eliminate_FG = (17, 26)
RA_trigger_FG_pay_SC = 26
RA_lighting_used_BG = 27
RA_lighting_used_FG = 28
RA_have_SC_BG = 30
RA_no_SC_BG = 31
RA_have_SC_FG = 32
RA_no_SC_FG = 33


# %% ----- Format -----

plot_name = "倍率線型_" + game_name + "_"
# f_multi_line_xlsx_name = lambda x: f"倍率線型_{Mat.threshold_record_version}_" + slot_name + f"_BET{int(pay_line)}" + "_"  # + game_type[x]


# %%
