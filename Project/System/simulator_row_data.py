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
player = 10**5
# player = 200
total_round = 200

record_size = (2 * player + 1, total_round)
threshold = 10**6


# %% Box


# 倍率線型設定
multiplier_range = np.array(
    [
        0,
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
        120,
        140,
        160,
        180,
        200,
        250,
        300,
        350,
        400,
        450,
        500,
        550,
        600,
        650,
        700,
        750,
        800,
        850,
        900,
        950,
        1000,
        2000,
        3000,
        4000,
        5000,
        6000,
        7000,
        8000,
        8000,
        10000,
        20000,
        30000,
        40000,
        -1,
    ]
)
weight_cum_BG = np.array(
    [
        605554736,
        215658208,
        59615199,
        38944836,
        28200472,
        16087129,
        9235803,
        5613772,
        4893692,
        2766681,
        2967028,
        8462502,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1999942,
    ],
    np.int64,
).cumsum()
weight_cum_FG = np.array(
    [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        273942792,
        239132889,
        172899884,
        154298840,
        159725596,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ],
    np.int64,
).cumsum()
weight_cum_JP = np.array(
    [130, 500, 1600000, 23500000],  # 新手 $1
    # [130, 500, 1600000, 12000000], # 老手 $1
    np.int64,
).cumsum()
average_multiplier_BG = (
    np.array(
        [
            0.0000,
            0.4522,
            1.6649,
            2.5711,
            3.5115,
            4.5624,
            5.4327,
            6.5135,
            7.4870,
            8.4601,
            9.9241,
            11.7569,
            16.6371,
            23.3803,
            26.7408,
            31.6693,
            37.4886,
            41.8856,
            47.6619,
            53.5955,
            63.8586,
            74.2467,
            81.7250,
            0.0000,
            106.7000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            5.0039,
        ],
        np.float64,
    )
    * threshold
).astype(np.int64)
average_multiplier_FG = (
    np.array(
        [
            0.0000,
            0.5803,
            1.5968,
            2.6230,
            3.6198,
            4.6262,
            5.6285,
            6.5758,
            7.6020,
            8.6169,
            9.5984,
            12.5882,
            17.5938,
            22.5713,
            27.5754,
            32.5464,
            37.5373,
            42.5531,
            47.5676,
            54.9458,
            64.9682,
            74.9337,
            84.9442,
            94.9073,
            109.5666,
            129.6503,
            149.7352,
            169.6464,
            189.6580,
            222.7745,
            273.2649,
            323.3945,
            373.4419,
            423.4785,
            473.4852,
            523.4316,
            573.6501,
            625.0823,
            673.1862,
            724.7164,
            774.5421,
            824.9694,
            874.3236,
            923.5996,
            975.4664,
            1237.5373,
            2251.1450,
            3311.2125,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
            0.0000,
        ],
        np.float64,
    )
    * threshold
).astype(np.int64)
average_multiplier_JP = (
    np.array(
        [769231, 200000, 50, 10],
        np.float64,
    )
    * threshold
).astype(np.int64)

p_JP = 0.0025100000000  # 新手 $1
# p_JP = 0.001360013  # 老手 $1


# record data 格式
# x
R_rescue_pay = (0 * player + 1, 1 * player + 1)
R_rescue_fg = (1 * player + 1, 2 * player + 1)

# x=0
RA_pay_BG = 0
RA_pay_FG = 1
RA_pay_JP = 2


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

    def base_game():
        idx = int(get_value(weight_cum_BG))
        pay = average_multiplier_BG[idx]
        return pay, idx == weight_cum_BG.shape[0] - 1

    def free_game():
        idx = int(get_value(weight_cum_FG))
        pay = average_multiplier_FG[idx]
        return pay

    def jackpot_game():
        idx = int(get_value(weight_cum_JP))
        pay = average_multiplier_JP[idx]
        return pay

    # simulate n times
    for i in range(player):
        cnt_spin = 0  # 已經玩多少場
        for j in range(total_round):

            # base game
            pay_BG, trigger_FG = base_game()

            # free game
            pay_FG = 0
            if trigger_FG:
                pay_FG = free_game()
                log_fg(record_data_fg_jp, i, j)

            # jackpot game
            rd_JP = np.random.random()
            pay_JP = 0
            if rd_JP < p_JP:
                pay_JP = jackpot_game()
                log_jp(record_data_fg_jp, i, j)

            # record
            log_all(True, RA_pay_BG, pay_BG)
            log_all(True, RA_pay_FG, pay_FG)
            log_all(True, RA_pay_JP, pay_JP)
            log_pay(record_data_pay, pay_BG + pay_FG + pay_JP, i, j)

            # update
            cnt_spin += 1

    return record_data


# make multi-thread
func_nb_mt = simulation.make_multi_thread(simulator_game, round=total_round, output_shape=record_size)
record_data, durning = simulation.time_func("Duration: ", func_nb_mt)


# %% Print


rtp_BG = record_data[0, RA_pay_BG] / total_round / player / threshold
rtp_FG = record_data[0, RA_pay_FG] / total_round / player / threshold
rtp_JP = record_data[0, RA_pay_JP] / total_round / player / threshold


print(f"Durning: {durning:0.2f}s")
print(f"Total Round: {total_round}, Players: {player}")

print("\n--- overview ---")
print(f"* RTP: {(rtp_BG+rtp_FG+rtp_JP)*100:0.2f}%")
print(f"* RTP BG: {rtp_BG*100:03.2f}%")
print(f"* RTP FG: {rtp_FG*100:03.2f}%")
print(f"* RTP JP: {rtp_JP*100:03.2f}%")


# %%


now = datetime.now().strftime("%y%m%d%H%M%S")
df = pd.DataFrame(record_data[1:, :])
file_name = "output_row_data_" + now + ".csv"
df.to_csv(file_name, index=False, header=False)
print(file_name + " saved.")


# %%
