# %% Import


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
player = 200
total_round = 2000

record_size = (player * 3 + 1, total_round)
threshold = 10**6

# rescue setting
return_percnetage = 0.75
trigger_range = 100

return_rtp_threshold_1 = 0.70
observe_rtp_range_1 = 200

return_rtp_threshold_2 = 0.75
observe_rtp_range_2 = 500

return_rtp_threshold_3 = 0.9
observe_rtp_range_3 = 2000

max_rescue = 30
min_rescue = 15

limit_continue_trigger = 10  # 避開連續救援

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
        569575066,
        229582950,
        85959579,
        38750450,
        32026186,
        14985120,
        8603128,
        5229215,
        3424839,
        1936256,
        1804585,
        5063385,
        491890,
        291507,
        275902,
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
        97024192,
        84645118,
        74900907,
        62557894,
        55683215,
        50434655,
        41191236,
        40815263,
        68752714,
        57707400,
        49145875,
        41176434,
        34909232,
        53835175,
        39859048,
        29263717,
        21525188,
        16859572,
        27428185,
        14829244,
        8584393,
        8942411,
        5901886,
        3852034,
        2302789,
        1828530,
        1000100,
        653208,
        660638,
        621396,
        0,
        0,
        0,
        0,
        3108351,
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
    [130, 500, 1600000, 12000000],
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
            12.55334413,
            17.5366351,
            22.5270944,
            27.50446408,
            32.5156953,
            37.49118649,
            42.51813282,
            47.50903591,
            54.91713314,
            64.89915611,
            74.86836938,
            84.87142857,
            94.90823864,
            109.443129,
            129.5268197,
            149.5408447,
            169.4623779,
            189.6576471,
            222.4180717,
            272.4480663,
            322.8842524,
            373.2968474,
            423.6770536,
            473.0814637,
            523.2455378,
            573.9682997,
            625.0822857,
            673.1862205,
            724.716436,
            774.5420601,
            0,
            0,
            0,
            0,
            1237.537258,
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

p_JP = 0.001360013


# record data 格式
# x
R_pay_original = (0 * player + 1, 1 * player + 1)
R_pay_rescue = (1 * player + 1, 2 * player + 1)
R_10_rescue = (2 * player + 1, 3 * player + 1)

# x=0
RA_pay_BG = 0
RA_pay_FG = 1
RA_pay_JP = 2
RA_pay_rescue_BG = 3
RA_pay_rescue_FG = 4
RA_cnt_rescue = 5
RA_cnt_need_help = 6
RA_cnt_trigger_rescue = 7
RA_cnt_need_help_player = 8
RA_cnt_trigger_rescue_player = 9


# %% Simulator


@njit("int64[:, :](int64[:, :], int64)", nopython=True, nogil=True)
def simulator_game(record_data, total_round):  # 完整遊戲模擬

    record_data_all = record_data[0, :]
    record_data_pay_original = record_data[R_pay_original[0] : R_pay_original[1], :]
    record_data_pay_rescue = record_data[R_pay_rescue[0] : R_pay_rescue[1], :]
    record_data_10_rescue = record_data[R_10_rescue[0] : R_10_rescue[1], :]

    def log_all(condition, idx, v):
        if condition:
            record_data_all[idx] += v

    def log_pay(record_data, pay, i, j):
        record_data[i, j] += pay

    def log_hit(record_data, hit, i, j):
        record_data[i, j] += hit

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
        cnt_cum_range = observe_rtp_range_2  # 判定區間
        cnt_cum_range_trigger = -1  # 要觸發的那一場
        cnt_spin = 0  # 已經玩多少場
        TF_need_help = False
        TF_trigger_rescue = False
        # print("================ Player", i, "================")
        for j in range(total_round):

            # system function
            trigger_rescue = False
            if cnt_spin == cnt_cum_range_trigger:
                rtp_1 = record_data_pay_rescue[i, j - observe_rtp_range_1 : j].sum() / observe_rtp_range_1 / threshold  # 往前抓"observe_rtp_range_1"場
                rtp_2 = record_data_pay_rescue[i, j - observe_rtp_range_2 : j].sum() / observe_rtp_range_2 / threshold  # 往前抓"observe_rtp_range_2"場

                observe_rtp_range = observe_rtp_range_3
                if observe_rtp_range >= j:
                    observe_rtp_range = j
                rtp_3 = record_data_pay_rescue[i, j - observe_rtp_range : j].sum() / observe_rtp_range / threshold  # 往前抓"0~observe_rtp_range_3"場

                trigger_rescue = (rtp_1 < return_rtp_threshold_1) and (rtp_2 < return_rtp_threshold_2) and (rtp_3 < return_rtp_threshold_3)  # 短期、長期 玩家都體驗不好才會觸發

            # play game
            pay_BG, pay_FG = 0, 0
            if trigger_rescue:
                TF_need_help = True
                log_all(True, RA_cnt_need_help, 1)

                # free game (fix value)
                pay_FG = (return_percnetage - rtp_1) * observe_rtp_range_1 * threshold
                if pay_FG >= max_rescue * threshold:
                    pay_FG = max_rescue * threshold
                if pay_FG < min_rescue * threshold:
                    pay_FG = 0
                    trigger_rescue = False

                if pay_FG > 0:
                    TF_trigger_rescue = True
                    log_all(True, RA_cnt_trigger_rescue, 1)
                # print("rescue multiplier:", pay_FG, "RTP1:", rtp_1, "RTP2:", rtp_2)
            else:
                # base game
                pay_BG, trigger_FG = base_game()

                # free game
                pay_FG = 0
                if trigger_FG:
                    pay_FG = free_game()

                # jackpot game
                rd_JP = np.random.random()
                pay_JP = 0
                if rd_JP < p_JP:
                    pay_JP = jackpot_game()

            # record
            if trigger_rescue:
                log_all(True, RA_cnt_rescue, 1)
                log_all(True, RA_pay_rescue_BG, pay_BG)
                log_all(True, RA_pay_rescue_FG, pay_FG)
                log_pay(record_data_pay_rescue, pay_BG + pay_FG, i, j)
                log_pay(record_data_10_rescue, 1, i, j)
            else:
                log_all(True, RA_pay_BG, pay_BG)
                log_all(True, RA_pay_FG, pay_FG)
                log_all(True, RA_pay_JP, pay_JP)
                log_all(True, RA_pay_rescue_BG, pay_BG)
                log_all(True, RA_pay_rescue_FG, pay_FG)
                log_pay(record_data_pay_original, pay_BG + pay_FG, i, j)
                log_pay(record_data_pay_rescue, pay_BG + pay_FG, i, j)

            # update
            cnt_spin += 1
            if cnt_spin >= cnt_cum_range - 100 + trigger_range - 1:  # 更新判定區間/更新判定把數
                cnt_cum_range += trigger_range
                new_cnt_cum_range_trigger = cnt_cum_range - 100 + np.random.randint(0, trigger_range)
                while new_cnt_cum_range_trigger - cnt_cum_range_trigger < limit_continue_trigger:  # 避開連續救援
                    new_cnt_cum_range_trigger = cnt_cum_range - 100 + np.random.randint(0, trigger_range)
                cnt_cum_range_trigger = new_cnt_cum_range_trigger

        log_all(TF_need_help, RA_cnt_need_help_player, 1)
        log_all(TF_trigger_rescue, RA_cnt_trigger_rescue_player, 1)

    return record_data


# make multi-thread
func_nb_mt = simulation.make_multi_thread(simulator_game, round=total_round, output_shape=record_size)
record_data, durning = simulation.time_func("Duration: ", func_nb_mt)


# %% Print


rtp_BG = record_data[0, RA_pay_BG] / total_round / player / threshold
rtp_FG = record_data[0, RA_pay_FG] / total_round / player / threshold
rtp_JP = record_data[0, RA_pay_JP] / total_round / player / threshold
rtp_rescue_BG = record_data[0, RA_pay_rescue_BG] / total_round / player / threshold
rtp_rescue_FG = record_data[0, RA_pay_rescue_FG] / total_round / player / threshold

cnt_rescue = record_data[0, RA_cnt_rescue]  # 觸發幾次
average_rescue = cnt_rescue / player  # 平均每個人可以觸發幾次
average_rescue_adj = average_rescue / ((total_round - observe_rtp_range_2) / trigger_range)  # ??


print(f"Durning: {durning:0.2f}s")
print(f"Total Round: {total_round}, Players: {player}")

print("\n--- overview ---")
print("* return_percnetage:", return_percnetage)
print("* trigger_range:", trigger_range)
print("* return_rtp_threshold_1:", return_rtp_threshold_1)
print("* observe_rtp_range_1:", observe_rtp_range_1)
print("* return_rtp_threshold_2:", return_rtp_threshold_2)
print("* observe_rtp_range_2:", observe_rtp_range_2)
print("* max_rescue:", max_rescue)
print("* min_rescue:", min_rescue)

print("\n--- detail ---")
print(f"* RTP: {(rtp_BG+rtp_FG+rtp_JP)*100:0.2f}% -> {(rtp_rescue_BG+rtp_rescue_FG+rtp_JP)*100:0.2f}%")
print(f"* RTP BG: {rtp_BG*100:03.2f}% -> {rtp_rescue_BG*100:03.2f}%")
print(f"* RTP FG: {rtp_FG*100:03.2f}% -> {rtp_rescue_FG*100:03.2f}%")
print(f"* RTP JP: {rtp_JP*100:03.2f}%")

print("\n--- overview ---")
rtp_add = rtp_rescue_BG + rtp_rescue_FG - rtp_BG - rtp_FG
print("* 救援次數(每人):", f"{average_rescue:03.2f} ({cnt_rescue}次/{average_rescue_adj*100:03.2f}%)")
print("* 多送的 RTP:", f"{rtp_add*100:03.2f}%")

cnt_need_help = record_data[0, RA_cnt_need_help]
cnt_trigger_rescue = record_data[0, RA_cnt_trigger_rescue]
cnt_need_help_player = record_data[0, RA_cnt_need_help_player]
cnt_trigger_rescue_player = record_data[0, RA_cnt_trigger_rescue_player]
total_can_trigger = (total_round - observe_rtp_range_2) / trigger_range * player
cnt_trigger_rescue_time = record_data[R_10_rescue[0] : R_10_rescue[1], :].sum()

print("* 該被救的玩家比例 (該被救玩家數/總玩家數):", f"{cnt_need_help_player/player*100:0.02f}%")
print("* 該被救且有被救的玩家:", f"{cnt_trigger_rescue_player/cnt_trigger_rescue*100:0.02f}%")
print("* 該被救的比例 (該被救總次數/總共可觸發):", f"{cnt_need_help/total_can_trigger*100:0.02f}%")
print("* 該被救且有被救的比例 (該被救且有被救/該被救總次數):", f"{cnt_trigger_rescue/cnt_need_help*100:0.02f}%")

print(cnt_trigger_rescue_time)


# %%


# df = pd.DataFrame(record_data)
# df.to_excel("output.xlsx", index=False)


# %%
