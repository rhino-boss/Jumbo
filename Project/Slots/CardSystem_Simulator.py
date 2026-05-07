# %% Import


from datetime import datetime
import numpy as np
import pandas as pd
from numba import jit, njit
import math
import os

os.chdir("C:\\Users\\rhinshen\\Mine\\個人工作區\\2_Program")

import Project.Slots.Source.General.Math as Mat
from Project.Slots.Source.General.Math import simulation, cplot
from Project.Slots.Source.General.RedBox import div, log_use

# my package
import Project.Slots.Source.General.RedBox as Red

# path_math = Red.Path.get_resource_path("Project/Slots/Source/CardSystem_math_data.xlsx")
path_math = Red.Path.get_resource_path("Project/Slots/Source/CardSystem_math_data_BF.xlsx")


# %% Setting


"""
基本設定
* Bet = 1

資料儲存結構
* version: B2
* record_data: (x: player, y: total round)

待開發項目

"""

# simulator setting
player = 1
total_round = 10**7
record_size = (2 * player + 1, total_round)
value_scale = 10**6
boundary_newbie_oldhand = 200

# Game Setting
bet_level = 0  # 0~29
denom = pd.read_excel(path_math, sheet_name="BetSetting")["denom"][0]
mini_bet = pd.read_excel(path_math, sheet_name="BetSetting")["mini_bet"][0]
bet = pd.read_excel(path_math, sheet_name="BetSetting")["bet"][bet_level]
bet_multiplier = pd.read_excel(path_math, sheet_name="BetSetting")["bet_multiplier"][bet_level]

coin_in = bet * denom
threshold = 10**10


multiplier_range = pd.read_excel(path_math, sheet_name="Newbie")["multiplier_range"].dropna().values.astype(np.int64)

weight_cum_BG_newbie = pd.read_excel(path_math, sheet_name="Newbie")["weight_BG"].dropna().values.astype(np.int64).cumsum()
average_multiplier_BG_newbie = pd.read_excel(path_math, sheet_name="Newbie")["average_multiplier_BG"].dropna().values * value_scale * coin_in
weight_cum_FG_newbie = pd.read_excel(path_math, sheet_name="Newbie")["weight_FG"].dropna().values.astype(np.int64).cumsum()
average_multiplier_FG_newbie = pd.read_excel(path_math, sheet_name="Newbie")["average_multiplier_FG"].dropna().values * value_scale * coin_in

weight_cum_BG_oldhand = pd.read_excel(path_math, sheet_name="Oldhand")["weight_BG"].dropna().values.astype(np.int64).cumsum()
average_multiplier_BG_oldhand = pd.read_excel(path_math, sheet_name="Oldhand")["average_multiplier_BG"].dropna().values * value_scale * coin_in
weight_cum_FG_oldhand = pd.read_excel(path_math, sheet_name="Oldhand")["weight_FG"].dropna().values.astype(np.int64).cumsum()
average_multiplier_FG_oldhand = pd.read_excel(path_math, sheet_name="Oldhand")["average_multiplier_FG"].dropna().values * value_scale * coin_in

weight_cum_JP_newbie = pd.read_excel(path_math, sheet_name="Newbie")[["weight_JP1", "weight_JP2", "weight_JP3", "weight_JP4"]].dropna().values.astype(np.int64)[bet_level].cumsum()
average_multiplier_JP_newbie = pd.read_excel(path_math, sheet_name="Newbie")[["average_multiplier_JP1", "average_multiplier_JP2", "average_multiplier_JP3", "average_multiplier_JP4"]].dropna().values[bet_level] * value_scale

weight_cum_JP_oldhand = pd.read_excel(path_math, sheet_name="Oldhand")[["weight_JP1", "weight_JP2", "weight_JP3", "weight_JP4"]].dropna().values.astype(np.int64)[bet_level].cumsum()
average_multiplier_JP_oldhand = pd.read_excel(path_math, sheet_name="Oldhand")[["average_multiplier_JP1", "average_multiplier_JP2", "average_multiplier_JP3", "average_multiplier_JP4"]].dropna().values[bet_level] * value_scale

p_JP_newbie = weight_cum_JP_newbie[-1] / threshold
p_JP_oldhand = weight_cum_JP_oldhand[-1] / threshold

# record data 格式
# x
R_rescue_pay = (0 * player + 1, 1 * player + 1)
R_rescue_fg = (1 * player + 1, 2 * player + 1)

# x=0
RA_pay_BG = 0
RA_pay_FG = 1
RA_pay_JP_link = 2
RA_pay_JP_bonus = 3
RA_period_JP = 4
RA_x_sum_game = 11
RA_x_square_game = 12
RA_x_sum_bonus = 13
RA_x_square_bonus = 14


# %% Simulator


@njit("int64[:, :](int64[:, :], int64)", nopython=True, nogil=True)
def simulator_game(record_data, total_round):  # 完整遊戲模擬

    record_data_all = record_data[0, :]
    record_data_pay = record_data[R_rescue_pay[0] : R_rescue_pay[1], :]
    record_data_fg_jp = record_data[R_rescue_fg[0] : R_rescue_fg[1], :]

    def log_all(condition, idx, v):
        if condition:
            record_data_all[idx] += v

    def log_pay(record_data, pay, i, j):
        record_data[i, j] += pay

    def log_fg(record_data, i, j):
        record_data[i, j] = 1

    def log_jp(record_data, i, j):
        record_data[i, j] = 2

    def get_value(cum_weight):
        rd = math.ceil(np.random.random() * cum_weight[-1]) - 1
        for idx in range(len(cum_weight)):
            if rd < cum_weight[idx]:
                return idx

    def base_game(spin):
        idx = 0
        pay = 0
        if spin < boundary_newbie_oldhand:
            idx = int(get_value(weight_cum_BG_newbie))
            pay = average_multiplier_BG_newbie[idx]
        else:
            idx = int(get_value(weight_cum_BG_oldhand))
            pay = average_multiplier_BG_oldhand[idx]
        return pay, idx == multiplier_range.shape[0]

    def free_game(spin):
        idx = 0
        pay = 0
        if spin < boundary_newbie_oldhand:
            idx = int(get_value(weight_cum_FG_newbie))
            pay = average_multiplier_FG_newbie[idx]
        else:
            idx = int(get_value(weight_cum_FG_oldhand))
            pay = average_multiplier_FG_oldhand[idx]
        return pay

    def jackpot_game(spin):
        idx = 0
        pay = 0
        if spin < boundary_newbie_oldhand:
            idx = int(get_value(weight_cum_JP_newbie))
            pay = average_multiplier_JP_newbie[idx]
        else:
            idx = int(get_value(weight_cum_JP_oldhand))
            pay = average_multiplier_JP_oldhand[idx]

        if idx == 0 or idx == 1:
            log_all(True, RA_pay_JP_link, pay)
        else:
            log_all(True, RA_pay_JP_bonus, pay)

            log_all(True, RA_x_sum_bonus, pay / coin_in / value_scale)
            log_all(True, RA_x_square_bonus, (pay / coin_in / value_scale) ** 2)

        return pay

    # simulate n times
    for i in range(player):
        cnt_spin = 0  # 已經玩多少場
        for round in range(200, total_round + 200):

            # base game
            pay_BG, trigger_FG = base_game(round)

            # free game
            pay_FG = 0
            if trigger_FG:
                pay_FG = free_game(round)
                log_fg(record_data_fg_jp, i, round)

            # jackpot game
            rd_JP = np.random.random()
            pay_JP = 0
            if round < boundary_newbie_oldhand:
                if rd_JP < p_JP_newbie:
                    pay_JP = jackpot_game(round)
                    log_all(True, RA_period_JP, 1)
            else:
                if rd_JP < p_JP_oldhand:
                    pay_JP = jackpot_game(round)
                    log_all(True, RA_period_JP, 1)
            # log_jp(record_data_fg_jp, i, round)

            # record
            log_all(True, RA_pay_BG, pay_BG)
            log_all(True, RA_pay_FG, pay_FG)

            log_all(True, RA_x_sum_game, (pay_BG + pay_FG) / coin_in / value_scale)
            log_all(True, RA_x_square_game, ((pay_BG + pay_FG) / coin_in / value_scale) ** 2)

            log_pay(record_data_pay, pay_BG + pay_FG + pay_JP, i, round)

            # update
            cnt_spin += 1

    return record_data


# make multi-thread
func_nb_mt = simulation.make_multi_thread(simulator_game, round=total_round, output_shape=record_size)
record_data, durning = simulation.time_func("Duration: ", func_nb_mt)


# %% Print


rtp_BG = record_data[0, RA_pay_BG] / total_round / player / value_scale / coin_in / 75
rtp_FG = record_data[0, RA_pay_FG] / total_round / player / value_scale / coin_in / 75
rtp_JP_link = record_data[0, RA_pay_JP_link] / total_round / player / value_scale / coin_in / 75
rtp_JP_bonus = record_data[0, RA_pay_JP_bonus] / total_round / player / value_scale / coin_in / 75


print(f"Durning: {durning:0.2f}s")
print(f"Total Round: {total_round}, Players: {player}")


print("\n--- Game Setting ---")
print("* bet_level:", bet_level)
print("* denom:", denom)
print("* mini_bet:", mini_bet)
print("* bet:", bet)
print("* bet_multiplier:", bet_multiplier)
print("* coin in:", coin_in)


print("\n--- overview ---")
print(f"* RTP: {(rtp_BG+rtp_FG+rtp_JP_link+rtp_JP_bonus)*100:0.2f}%")
print(f"* RTP BG: {rtp_BG*100:03.2f}%")
print(f"* RTP FG: {rtp_FG*100:03.2f}%")
print(f"* RTP JP-link: {rtp_JP_link*100:03.2f}%")
print(f"* RTP JP-bonus: {rtp_JP_bonus*100:03.2f}%")

n = total_round / player
std_game = ((record_data[0, RA_x_square_game] - ((record_data[0, RA_x_sum_game]) ** 2 / n)) / n) ** 0.5
std_bonus = ((record_data[0, RA_x_square_bonus] - ((record_data[0, RA_x_sum_bonus]) ** 2 / n)) / n) ** 0.5
print(std_game)
print(std_bonus)
print(record_data[0, RA_period_JP] / total_round / player)


# %%


# now = datetime.now().strftime("%y%m%d%H%M%S")
# df = pd.DataFrame(record_data[1:, :])
# file_name = "output_row_data_" + now + ".csv"
# df.to_csv(file_name, index=False, header=False)
# print(file_name + " saved.")


# %%
