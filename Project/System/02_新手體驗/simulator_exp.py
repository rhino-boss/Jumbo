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


# row_data_pay = pd.read_excel("Project/System/02_新手體驗/output_row_data_260224141654_糖果新手_RTP 92+315.xlsx", sheet_name="pay", header=None).to_numpy()
# row_data_mode = pd.read_excel("Project/System/02_新手體驗/output_row_data_260224141654_糖果新手_RTP 92+315.xlsx", sheet_name="mode", header=None).to_numpy()
row_data_pay = pd.read_excel("Project/System/02_新手體驗/output_row_data_260224142455_糖果新手_RTP 92+315_2000.xlsx", sheet_name="pay", header=None).to_numpy()
row_data_mode = pd.read_excel("Project/System/02_新手體驗/output_row_data_260224142455_糖果新手_RTP 92+315_2000.xlsx", sheet_name="mode", header=None).to_numpy()


# %% Base Setting


player = 2000
total_round = 200

record_size = (3 * player + 1, total_round)
threshold = 10**6

score_bg = 5  # multi
score_mg = 10
score_fg_50 = 15
score_fg_150_1 = 15
score_fg_150_2 = 30

threshold_1 = 1
threshold_2 = 0.70 - 0.05
threshold_3 = 0.50 - 0.05
threshold_4 = 0.75
threshold_5 = 0.55


print("player:", player)
print("total_round:", total_round)
print("shape:", row_data_pay.shape)


# %% 從這邊開始執行 (Simulator)


# record data setting
# x=0
RA_pay_BG = 0
RA_pay_FG = 1
RA_pay_JP = 2
RA_cnt_push = 3
RA_cnt_push_1 = 4
RA_cnt_push_2 = 5
RA_cnt_push_3 = 6
RA_cnt_push_4 = 7

# x
R_exp_pay = (0 * player + 1, 1 * player + 1)
R_exp_mode = (1 * player + 1, 2 * player + 1)
R_exp_push = (2 * player + 1, 3 * player + 1)


@njit("int64[:, :](int64[:, :], int64)", nogil=True)
def simulator_game(record_data, total_round):  # 完整遊戲模擬

    record_data_all = record_data[0, :]
    record_data_exp_pay = record_data[R_exp_pay[0] : R_exp_pay[1], :]
    record_data_exp_mode = record_data[R_exp_mode[0] : R_exp_mode[1], :]
    record_data_exp_push = record_data[R_exp_push[0] : R_exp_push[1], :]

    def log_all(condition, idx, v):
        if condition:
            record_data_all[idx] += v

    def log_pay(record_data, pay, i, j):
        record_data[i, j] += pay

    def log_mode(record_data, mode, i, j):
        record_data[i, j] = mode

    def log_push(record_data, i, j):
        record_data[i, j] = 1

    # def get_value(cum_weight):
    #     rd = math.ceil(np.random.random() * cum_weight[-1]) - 1
    #     for idx in range(len(cum_weight)):
    #         if rd < cum_weight[idx]:
    #             return idx

    # simulate n times
    for i in range(player):
        n_first = np.random.randint(41, 60)
        n_second = np.random.randint(141, 160)

        trigger_fg = False
        trigger_mg = False

        cnt_spin = 0  # 已經玩多少場
        cnt_push_time = 0  # 打平次數
        for n_spin in range(total_round):

            pay = 0
            mode = 0  # 0: NB, 1: FG, 2: MG, 3: exp BG, 4: exp MG, 5: exp 50 FG, 6: exp 150 FG 1, 7: exp 150 FG 2
            cum_rtp = record_data_exp_pay[i, :n_spin].sum() / threshold / (n_spin + 1) if n_spin > 0 else 0

            # 加新手體驗
            if n_spin == n_first and not trigger_fg and not trigger_mg:
                trigger_fg = True
                # if threshold_2 < cum_rtp and cum_rtp <= threshold_1:
                #     pay = score_bg * threshold
                #     mode = 3
                if threshold_3 < cum_rtp and cum_rtp <= threshold_2:
                    pay = score_mg * threshold
                    mode = 4
                if cum_rtp <= threshold_3:
                    pay = score_fg_50 * threshold
                    mode = 5
            elif n_spin == n_second:
                trigger_mg = True
                if threshold_5 < cum_rtp and cum_rtp <= threshold_4:
                    pay = score_fg_150_1 * threshold
                    mode = 6
                if cum_rtp <= threshold_5:
                    pay = score_fg_150_2 * threshold
                    mode = 7
            else:
                pay = row_data_pay[i, n_spin]
                if row_data_mode[i, n_spin] == 1:
                    trigger_fg = True
                    mode = 1
                elif row_data_mode[i, n_spin] == 2:
                    trigger_mg = True
                    mode = 2

            # # 正常遊戲
            # pay = row_data_pay[i, n_spin]
            # if row_data_mode[i, n_spin] == 1:
            #     mode = 1
            # elif row_data_mode[i, n_spin] == 2:
            #     mode = 2

            new_cum_rtp = (row_data_pay[i, :n_spin].sum() + pay) / threshold / (n_spin + 2) if (n_spin + 2) > 0 else 0
            if n_spin >= 14 and new_cum_rtp >= 1 and cum_rtp < 1:
                log_push(record_data_exp_push, i, n_spin)
                log_all(True, RA_cnt_push, 1)

            # record
            log_pay(record_data_exp_pay, pay, i, n_spin)
            log_mode(record_data_exp_mode, mode, i, n_spin)

            # update
            cnt_spin += 1

    return record_data


# make multi-thread
func_nb_mt = simulation.make_multi_thread(simulator_game, round=total_round, output_shape=record_size)
record_data, durning = simulation.time_func("Duration: ", func_nb_mt)


# %% Print Log


print(f"Durning: {durning:0.2f}s")
print(f"Total Round: {total_round}, Players: {player}")

record_data_exp_mode = record_data[R_exp_mode[0] : R_exp_mode[1], :]
record_data_exp_pay = record_data[R_exp_pay[0] : R_exp_pay[1], :]
record_data_exp_push = record_data[R_exp_push[0] : R_exp_push[1], :]


print("\n--- overview ---")

rtp = np.nansum(row_data_pay) / player / total_round / threshold
rtp_exp = np.nansum(record_data_exp_pay) / player / total_round / threshold

print(f"rtp: {rtp* 100:0.2f}%")
print(f"rtp_exp: {rtp_exp* 100:0.2f} ({(rtp_exp-rtp)*100:0.2f})%")

cnt_push = record_data[0, RA_cnt_push] / player
print(f"打平次數: {cnt_push}")

# cnt_mode_0 = np.coun(record_data_exp_mode[record_data_exp_mode == 0])

aa = record_data_exp_pay[:, :60].sum() / player / 60 / threshold
print(f"rtp 60轉: {aa* 100:0.2f}%")

bb = record_data_exp_pay[:, :160].sum() / player / 160 / threshold
print(f"rtp 160轉: {bb* 100:0.2f}%")

c1 = record_data_exp_mode[record_data_exp_mode == 4].shape[0]
c2 = record_data_exp_mode[record_data_exp_mode == 5].shape[0]
c3 = record_data_exp_mode[record_data_exp_mode == 6].shape[0]
c4 = record_data_exp_mode[record_data_exp_mode == 7].shape[0]
print(c1, c2, c3, c4)

# %% Output to Excel


# now = datetime.now().strftime("%y%m%d%H%M%S")
# df = pd.DataFrame(record_data[1:, :])
# file_name = "output_rescue_data_" + now + ".xlsx"
# df.to_excel(file_name, index=False, header=False)

# print(file_name + " saved.")


# %%
