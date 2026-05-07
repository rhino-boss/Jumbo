# %% ----- Import -----

import os
from datetime import datetime

import numpy as np
import pandas as pd

import Project.Slots.Source.General.RedBox as Red
from Project.Slots.Source.General.Math import threshold_record

# %% ----- base info -----


game_name = "H026_彩罐熱舞"
math_version = "0003"

path_math = Red.Path.get_resource_path("Project/Slots/Source/H026_math_data.xlsx")
path_plot = "Project/Slots/Record/"
path_output_data = lambda add_info="": "Project/Slots/Record/" + game_name + "_" + datetime.now().strftime("%y%m%d%H%M") + add_info + ".xlsx"


# %% ----- setting -----


mode_normalbet, mode_featurebuy = 0, 2
scence_BG, scence_FG = 0, 1
scence_num = 2
output_BG, output_FG, output_OA = 0, 1, 2

window_size = 3
reel_num = 5
layout_shape = (window_size, reel_num)

normalbet = 1
featurebuy = 75
default_coin_in = 100

multiplier_base_weight = 10000
special_pool_weight_base = 10000
max_win_multiplier = 5000


# %% ----- load helpers -----


def _read_sheet(sheet_name, dtype=None):
    try:
        return pd.read_excel(path_math, sheet_name=sheet_name, dtype=dtype)
    except ValueError as exc:
        raise ValueError(f"Missing sheet: {sheet_name}") from exc


def _require_columns(df, sheet_name, columns):
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Sheet '{sheet_name}' missing columns: {missing}")


def _to_numpy(values, dtype, sheet_name, field_name):
    try:
        return np.asarray(values, dtype=dtype)
    except Exception as exc:
        raise ValueError(f"Sheet '{sheet_name}' field '{field_name}' dtype invalid") from exc


def _get_overview():
    df = pd.read_excel(path_math, sheet_name="overview", header=None, index_col=0).T
    required = ["game_ID", "game_version", "game_RTP"]
    _require_columns(df, "overview", required)
    return df


def _get_paytable():
    df = _read_sheet("pay_table")
    _require_columns(df, "pay_table", ["Symbol", 3, 4, 5, "Id"])
    symbol_id_local = _to_numpy(df["Id"].values, np.int64, "pay_table", "Id")
    symbol_str_local = {int(symbol_id_local[i]): str(df["Symbol"].iloc[i]) for i in range(df.shape[0])}
    pay_table_local = _to_numpy(df[[3, 4, 5]].values, np.int64, "pay_table", "[3,4,5]")
    return df, pay_table_local, symbol_id_local, symbol_str_local


def _parse_paylines():
    df = _read_sheet("paylines", dtype={"Line": str})
    _require_columns(df, "paylines", ["Line"])
    lines = np.zeros((df.shape[0], reel_num), dtype=np.int64)
    for idx, raw in enumerate(df["Line"].fillna("").tolist()):
        value = str(raw).strip()
        if len(value) != reel_num or not value.isdigit():
            raise ValueError(f"Sheet 'paylines' invalid Line at row {idx}: {raw}")
        for reel in range(reel_num):
            lines[idx, reel] = int(value[reel])
    return lines


def _build_strip_arrays(sheet_names):
    symbol_cols = [f"Symbol_ID_R{i}" for i in range(1, reel_num + 1)]
    strip_weight_cols = [f"Strip_Weight_R{i}" for i in range(1, reel_num + 1)]
    drop_a_cols = [f"Drop_Weight_A_R{i}" for i in range(1, reel_num + 1)]
    drop_b_cols = [f"Drop_Weight_B_R{i}" for i in range(1, reel_num + 1)]

    strip_frames = []
    max_len = 0
    for sheet in sheet_names:
        df = _read_sheet(sheet)
        _require_columns(df, sheet, symbol_cols + strip_weight_cols + drop_a_cols + drop_b_cols)
        strip_frames.append(df)
        max_len = max(max_len, df.shape[0])

    sheet_count = len(sheet_names)
    arr_symbols = np.full((sheet_count, max_len, reel_num), -1, dtype=np.int64)
    arr_strip_weight = np.zeros((sheet_count, max_len, reel_num), dtype=np.int64)
    arr_drop_a = np.zeros((sheet_count, symbols_count, reel_num), dtype=np.int64)
    arr_drop_b = np.zeros((sheet_count, symbols_count, reel_num), dtype=np.int64)
    reels_len_local = np.zeros((sheet_count, reel_num), dtype=np.int64)

    for sheet_idx, df in enumerate(strip_frames):
        if df.shape[0] < symbols_count:
            raise ValueError(f"Sheet '{sheet_names[sheet_idx]}' rows less than symbols_count: {df.shape[0]} < {symbols_count}")
        for reel in range(reel_num):
            symbol_col = symbol_cols[reel]
            weight_col = strip_weight_cols[reel]
            drop_a_col = drop_a_cols[reel]
            drop_b_col = drop_b_cols[reel]

            symbol_values = df[symbol_col].values
            weight_values = df[weight_col].values
            drop_a_values = df[drop_a_col].fillna(0).values
            drop_b_values = df[drop_b_col].fillna(0).values
            arr_drop_a[sheet_idx, :, reel] = _to_numpy(drop_a_values[:symbols_count], np.int64, sheet_names[sheet_idx], drop_a_col)
            arr_drop_b[sheet_idx, :, reel] = _to_numpy(drop_b_values[:symbols_count], np.int64, sheet_names[sheet_idx], drop_b_col)

            valid_rows = 0
            for row in range(df.shape[0]):
                symbol_raw = symbol_values[row]
                if pd.isna(symbol_raw):
                    continue
                symbol = int(symbol_raw)
                arr_symbols[sheet_idx, valid_rows, reel] = symbol
                arr_strip_weight[sheet_idx, valid_rows, reel] = int(weight_values[row])
                valid_rows += 1
            reels_len_local[sheet_idx, reel] = valid_rows

    return arr_symbols, arr_strip_weight, arr_drop_a, arr_drop_b, reels_len_local


def _get_weight_matrix(df, columns, field_name, fillna_zero=False):
    _require_columns(df, "weight", columns)
    subset = df[columns].copy()
    if fillna_zero:
        subset = subset.fillna(0)
    elif subset.isna().any().any():
        raise ValueError(f"Sheet 'weight' field '{field_name}' contains NaN")
    return _to_numpy(subset.values, np.int64, "weight", field_name)


def _get_weight_vector(df, column, field_name, size, fillna_zero=False):
    values = _get_weight_matrix(df, [column], field_name, fillna_zero=fillna_zero)[:size, 0]
    if values.shape[0] < size:
        raise ValueError(f"Sheet 'weight' field '{field_name}' rows less than {size}: {values.shape[0]} < {size}")
    return values.astype(np.int64)


def _cum_last_axis(arr):
    return np.cumsum(arr, axis=0).astype(np.int64)


# %% ----- overview / paytable -----


overview = _get_overview()

game_ID = overview["game_ID"].iloc[0]
game_version = overview["game_version"].iloc[0]
game_RTP = overview["game_RTP"].iloc[0]

pay_table_df, pay_table, symbol_id, symbol_str = _get_paytable()
symbols_count = int(symbol_id.shape[0])

WW, C1, C2, M1, M2, M3, M4, M5, A, K, Q, J, TE, G1, G2, G3, G4, G5, GA, GK, GQ, GJ = range(22)  # 這是宣告，可以亂填
for idx, symbol_name in enumerate(pay_table_df["Symbol"].tolist()):
    globals()[str(symbol_name)] = int(symbol_id[idx])

symbols_special = np.array([WW, C1], dtype=np.int64)
symbols_main = np.array([M1, M2, M3, M4, M5], dtype=np.int64)
symbols_number = np.array([A, K, Q, J], dtype=np.int64)
symbols_main_gold = np.array([G1, G2, G3, G4, G5], dtype=np.int64)
symbols_number_gold = np.array([GA, GK, GQ, GJ], dtype=np.int64)
symbols_gold = np.concatenate([symbols_main_gold, symbols_number_gold]).astype(np.int64)
symbols_score = np.concatenate([symbols_main, symbols_number]).astype(np.int64)
symbols_all = np.concatenate([symbols_special, symbols_main, symbols_number, symbols_main_gold, symbols_number_gold]).astype(np.int64)

is_gold_symbol = np.zeros(symbols_count, dtype=np.int64)
is_score_symbol = np.zeros(symbols_count, dtype=np.int64)
base_symbol_of = np.full(symbols_count, -1, dtype=np.int64)

for sym in symbols_all:
    base_symbol_of[sym] = sym
for base_sym, gold_sym in zip(np.concatenate([symbols_main, symbols_number]), symbols_gold):
    base_symbol_of[gold_sym] = int(base_sym)
    is_gold_symbol[gold_sym] = 1
for sym in symbols_score:
    is_score_symbol[sym] = 1


# %% ----- xlsx data -----


paylines = _parse_paylines()
line_num = int(paylines.shape[0])

strip_names = ["BG_strip", "BG_strip (2)", "BG_strip (3)", "FG_strip", "FG_strip (2)", "FG_strip (3)", "BF_strip"]
strip_name_map = np.array(["B1", "B2", "B3", "F1", "F2", "F3", "BF"])
arr_reels, arr_reels_weight, drop_weight_a, drop_weight_b, reels_len = _build_strip_arrays(strip_names)
arr_reels_weight_cum = np.cumsum(arr_reels_weight, axis=1).astype(np.int64)

# # Scatter 與 Wild 不能自然掉落。
# for sheet_idx in range(drop_weight_a.shape[0]):
#     for reel in range(reel_num):
#         drop_weight_a[sheet_idx, WW, reel] = 0
#         drop_weight_a[sheet_idx, C1, reel] = 0
#         drop_weight_b[sheet_idx, WW, reel] = 0
#         drop_weight_b[sheet_idx, C1, reel] = 0

drop_weight_a_cum = np.cumsum(drop_weight_a, axis=1).astype(np.int64)
drop_weight_b_cum = np.cumsum(drop_weight_b, axis=1).astype(np.int64)

value_df = _read_sheet("value")
_require_columns(value_df, "value", ["Multiplier_Range"])
value_multiplier_range = _to_numpy(value_df["Multiplier_Range"].values, np.int64, "value", "Multiplier_Range")
expected_multiplier_range = np.array([0, 2, 3, 5, 8, 10, 15, 20, 25, 35, 50, 80, 100], dtype=np.int64)
if value_multiplier_range.shape[0] != expected_multiplier_range.shape[0] or not np.array_equal(value_multiplier_range, expected_multiplier_range):
    raise ValueError("Sheet 'value' invalid Multiplier_Range")

weight_df = _read_sheet("weight")

weight_table_BG = _get_weight_vector(weight_df, "Table_BG", "Table_BG", 3, fillna_zero=True)
weight_table_FG = _get_weight_vector(weight_df, "Table_FG", "Table_FG", 3, fillna_zero=True)
weight_table_BF = _get_weight_vector(weight_df, "Table_BF", "Table_BF", 3, fillna_zero=True)
weight_cum_table_BG = np.cumsum(weight_table_BG).astype(np.int64)
weight_cum_table_FG = np.cumsum(weight_table_FG).astype(np.int64)
weight_cum_table_BF = np.cumsum(weight_table_BF).astype(np.int64)
eliminate_table_weight_BG = _get_weight_vector(weight_df, "Eliminate_Table_Weight_BG", "Eliminate_Table_Weight_BG", 2, fillna_zero=True)
eliminate_table_weight_FG = _get_weight_vector(weight_df, "Eliminate_Table_Weight_FG", "Eliminate_Table_Weight_FG", 2, fillna_zero=True)
eliminate_table_weight_cum_BG = np.cumsum(eliminate_table_weight_BG).astype(np.int64)
eliminate_table_weight_cum_FG = np.cumsum(eliminate_table_weight_FG).astype(np.int64)

multiple_special_cols = [f"Multiple_Selection_Weight_Special_{name}" for name in strip_name_map]
multiple_r3_before_cols = [f"Multiple_Selection_Weight_R3_Before_{name}" for name in strip_name_map]
multiple_r3_after_cols = [f"Multiple_Selection_Weight_R3_After_{name}" for name in strip_name_map]
multiple_before_cols = [f"Multiple_Selection_Weight_Before_{name}" for name in strip_name_map]
multiple_after_cols = [f"Multiple_Selection_Weight_After_{name}" for name in strip_name_map]
special_pool_cols = [f"Used_Special_Pool_Weight_{name}" for name in strip_name_map]

weight_multiple_special = _get_weight_matrix(weight_df, multiple_special_cols, "Multiple_Selection_Weight_Special")
weight_multiple_r3_before = _get_weight_matrix(weight_df, multiple_r3_before_cols, "Multiple_Selection_Weight_R3_Before")
weight_multiple_r3_after = _get_weight_matrix(weight_df, multiple_r3_after_cols, "Multiple_Selection_Weight_R3_After")
weight_multiple_before = _get_weight_matrix(weight_df, multiple_before_cols, "Multiple_Selection_Weight_Before")
weight_multiple_after = _get_weight_matrix(weight_df, multiple_after_cols, "Multiple_Selection_Weight_After")

# `Used_Special_Pool_Weight` 以金框數 0-9 為索引，最後一行 NaN 視為該金框數配置為 0。
weight_special_pool = _get_weight_matrix(weight_df, special_pool_cols, "Used_Special_Pool_Weight", fillna_zero=True)

weight_cum_multiple_special = _cum_last_axis(weight_multiple_special)
weight_cum_multiple_r3_before = _cum_last_axis(weight_multiple_r3_before)
weight_cum_multiple_r3_after = _cum_last_axis(weight_multiple_r3_after)
weight_cum_multiple_before = _cum_last_axis(weight_multiple_before)
weight_cum_multiple_after = _cum_last_axis(weight_multiple_after)


# %% ----- record -----


record_cols = max(len(threshold_record), symbols_count * scence_num, 100)
record_size = (20, record_cols)

R_all = 0
R_multiplier_range_cnt_BG = 1
R_multiplier_range_cnt_FG = 2
R_multiplier_range_cnt_OA = 3
R_multiplier_range_pay_BG = 4
R_multiplier_range_pay_FG = 5
R_multiplier_range_pay_OA = 6
R_hits = (10, 13)
R_pay = (13, 16)
R_eliminate = (16, 19)

RA_hits_BG = 0
RA_hits_FG = 1
RA_trigger_freegame = 2
RA_re_trigger = 3
RA_free_spins = 4
RA_x_sum = 5
RA_x_square = 6
RA_trigger_FG_pay_BG = 7
RA_max_win_hits = 8
RA_max_single_win = 9
RA_max_multiplier = 10
RA_eliminate_0 = 11
RA_eliminate_1 = 12
RA_eliminate_2 = 13
RA_eliminate_3 = 14
RA_eliminate_4 = 15
RA_eliminate_5 = 16
RA_gold_appear_spins = 21
RA_gold_used_spins = 22
RA_multi_appear_spins = 23
RA_multi_used_spins = 24
RA_eliminate_0_FG = 31
RA_eliminate_1_FG = 32
RA_eliminate_2_FG = 33
RA_eliminate_3_FG = 34
RA_eliminate_4_FG = 35
RA_eliminate_5_FG = 36
RA_final_gold_count_BG_0 = 40
RA_final_gold_count_BG_1 = 41
RA_final_gold_count_BG_2 = 42
RA_final_gold_count_BG_3 = 43
RA_final_gold_count_BG_4 = 44
RA_final_gold_count_BG_5 = 45
RA_final_gold_count_BG_6 = 46
RA_final_gold_count_BG_7 = 47
RA_final_gold_count_BG_8 = 48
RA_final_gold_count_BG_9 = 49
RA_final_gold_count_FG_0 = 50
RA_final_gold_count_FG_1 = 51
RA_final_gold_count_FG_2 = 52
RA_final_gold_count_FG_3 = 53
RA_final_gold_count_FG_4 = 54
RA_final_gold_count_FG_5 = 55
RA_final_gold_count_FG_6 = 56
RA_final_gold_count_FG_7 = 57
RA_final_gold_count_FG_8 = 58
RA_final_gold_count_FG_9 = 59

# %% ----- format -----


plot_name = "倍率線型_" + game_name + "_"

# %%
