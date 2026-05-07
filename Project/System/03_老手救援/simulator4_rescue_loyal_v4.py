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

"""
基本設定
* Bet = 1

資料儲存結構
* version: B4
* record_data: (x: player, y: total round)

待開發項目

"""


row_data = pd.read_excel("Project/System/03_老手救援/rowdata_2k_2k_模擬資料增加新手期.xlsx", header=None).to_numpy()
# row_data = pd.read_excel("Project/System/03_老手救援/rowdata_2k_2k_真實資料.xlsx", header=None).to_numpy()


# %%


player = int(row_data.shape[0] / 2)
total_round = row_data.shape[1]

# player = int(row_data.shape[0])
# total_round = 2000

record_size = (2 * player + 1, total_round)
threshold = 10**6

row_data_pay = row_data[:player, :]
row_data_fg = row_data[player:, :]

row_data_len = (np.isnan(row_data)[:player, :] == False).sum(axis=1)
total_spin = sum(row_data_len)

print("player:", player)
print("total_round:", total_round)
print("shape:", row_data.shape)
print("total_spin:", total_spin)


# %%


# rescue setting new
trigger_range = 100
observe_rtp_range_1 = 200
observe_rtp_range_2 = 500
observe_rtp_range_3 = 2000

return_percnetage = 0.8
return_rtp_threshold_11 = 0.70
return_rtp_threshold_12 = 0.6
return_rtp_threshold_2 = 0.75
return_rtp_threshold_3 = 0.9

rescue_value_ceiling = 100
rescue_value_floor = 15
rescue_value_mini = 15

no_fg_trigger = 2000  # 可以訂2x理論週期
limit_continue_trigger = 50  # 避開N把內連續救援


# record data setting
# x=0
# RA_pay_BG = 0
# RA_pay_FG = 1
# RA_pay_JP = 2
# RA_pay_rescue_BG = 3
# RA_pay_rescue_FG = 4
# RA_cnt_rescue = 5
RA_cnt_need_help = 6
RA_cnt_trigger_rescue = 7
RA_cnt_need_help_player = 8
RA_cnt_trigger_rescue_player = 9
# RA_pay = 10
RA_pay_rescue = 11

# x
R_rescue_pay = (0 * player + 1, 1 * player + 1)
R_rescue_mode = (1 * player + 1, 2 * player + 1)


@njit("int64[:, :](int64[:, :], int64)", nogil=True)
def simulator_game(record_data, total_round):  # 完整遊戲模擬

    record_data_all = record_data[0, :]
    record_data_rescue_pay = record_data[R_rescue_pay[0] : R_rescue_pay[1], :]
    record_data_rescue_mode = record_data[R_rescue_mode[0] : R_rescue_mode[1], :]

    def log_all(condition, idx, v):
        if condition:
            record_data_all[idx] += v

    def log_pay(record_data, pay, i, j):
        record_data[i, j] += pay

    def get_value(cum_weight):
        rd = math.ceil(np.random.random() * cum_weight[-1]) - 1
        for idx in range(len(cum_weight)):
            if rd < cum_weight[idx]:
                return idx

    # simulate n times
    for i in range(player):
        cnt_cum_range = observe_rtp_range_2  # 判定區間
        cnt_cum_range_trigger = -1  # 要觸發的那一場
        cnt_spin = 0  # 已經玩多少場

        TF_log_need_help = False
        TF_log_trigger_rescue = False
        for j in range(total_round):

            if j >= row_data_len[i]:
                break

            # system function: 判斷是否需要救援
            """
            救援1: RTP低+短期體驗不好
            救援2: RTP高+短期體驗不好
            救援3: 長期沒有觸發FG
            """
            mode_trigger_rescue = 0
            if cnt_spin == cnt_cum_range_trigger:
                rtp_1 = record_data_rescue_pay[i, j - observe_rtp_range_1 : j].sum() / observe_rtp_range_1 / threshold  # 往前抓"observe_rtp_range_1"場
                rtp_2 = record_data_rescue_pay[i, j - observe_rtp_range_2 : j].sum() / observe_rtp_range_2 / threshold  # 往前抓"observe_rtp_range_2"場

                observe_rtp_range = observe_rtp_range_3 if observe_rtp_range_3 < j else j
                rtp_3 = record_data_rescue_pay[i, j - observe_rtp_range : j].sum() / observe_rtp_range / threshold  # 往前抓"0~observe_rtp_range_3"場

                if (rtp_3 < return_rtp_threshold_3) and (rtp_1 < return_rtp_threshold_11) and (rtp_2 < return_rtp_threshold_2):
                    mode_trigger_rescue = 1
                if (rtp_3 >= return_rtp_threshold_3) and (rtp_1 < return_rtp_threshold_12) and (rtp_2 < return_rtp_threshold_2):
                    mode_trigger_rescue = 2

                # previous_n_rounds = cnt_spin if cnt_spin < observe_rtp_range_2 else observe_rtp_range_2
                # fg_cnt = row_data_fg[i, j - previous_n_rounds : j].sum()
                # if fg_cnt == 0 and cnt_spin >= no_fg_trigger:
                #     mode_trigger_rescue = 3

            # play game
            pay = 0
            if mode_trigger_rescue >= 1:

                # rescue
                if mode_trigger_rescue == 1:
                    pay = (return_percnetage - rtp_1) * observe_rtp_range_1 * threshold
                    if pay >= rescue_value_ceiling * threshold:  # 輸太多，只救到上限
                        pay = rescue_value_ceiling * threshold
                    elif pay < rescue_value_floor * threshold:  # 輸得太少，救不到
                        pay = row_data_pay[i, j]
                        mode_trigger_rescue = 0
                elif mode_trigger_rescue == 2:
                    pay = rescue_value_mini * threshold
                elif mode_trigger_rescue == 3:
                    pay = rescue_value_mini * threshold

                # log
                if mode_trigger_rescue > 0:
                    TF_log_trigger_rescue = True
                    log_all(True, RA_cnt_trigger_rescue, 1)
                    log_all(True, RA_pay_rescue, pay)
                # else:
                #     print("這裡", rtp_1, rtp_2, rtp_3)

                TF_log_need_help = True
                log_all(True, RA_cnt_need_help, 1)

            else:
                pay = row_data_pay[i, j]

            # record
            log_pay(record_data_rescue_pay, pay, i, j)
            log_pay(record_data_rescue_mode, mode_trigger_rescue, i, j)

            # update
            cnt_spin += 1
            if cnt_spin >= cnt_cum_range - 100 + trigger_range - 1:  # 更新判定區間/更新判定把數
                cnt_cum_range += trigger_range
                new_cnt_cum_range_trigger = cnt_cum_range - 100 + np.random.randint(0, trigger_range)
                while new_cnt_cum_range_trigger - cnt_cum_range_trigger < limit_continue_trigger:  # 避開連續救援
                    new_cnt_cum_range_trigger = cnt_cum_range - 100 + np.random.randint(0, trigger_range)
                cnt_cum_range_trigger = new_cnt_cum_range_trigger
                # print(cnt_cum_range_trigger)

        log_all(TF_log_trigger_rescue, RA_cnt_trigger_rescue_player, 1)
        log_all(TF_log_need_help, RA_cnt_need_help_player, 1)

    return record_data


# make multi-thread
func_nb_mt = simulation.make_multi_thread(simulator_game, round=total_round, output_shape=record_size)
record_data, durning = simulation.time_func("Duration: ", func_nb_mt)


# %% Print Log


print(f"Durning: {durning:0.2f}s")
print(f"Total Round: {total_round}, Players: {player}")

record_data_rescue_mode = record_data[R_rescue_mode[0] : R_rescue_mode[1], :]
record_data_rescue_pay = record_data[R_rescue_pay[0] : R_rescue_pay[1], :]


print("\n--- overview ---")

rtp = np.nansum(row_data_pay) / total_spin / threshold
rtp_rescue = np.nansum(record_data_rescue_pay) / total_spin / threshold
rtp_rescue_1 = (np.nansum(record_data_rescue_pay[record_data_rescue_mode == 1]) - np.nansum(row_data_pay[record_data_rescue_mode == 1])) / total_spin / threshold
rtp_rescue_2 = (np.nansum(record_data_rescue_pay[record_data_rescue_mode == 2]) - np.nansum(row_data_pay[record_data_rescue_mode == 2])) / total_spin / threshold
rtp_rescue_3 = (np.nansum(record_data_rescue_pay[record_data_rescue_mode == 3]) - np.nansum(row_data_pay[record_data_rescue_mode == 3])) / total_spin / threshold

print(f"\n* rtp: {rtp*100:0.4f}%")
print(f"* rtp_rescue: {(rtp_rescue-rtp)*100:0.2f}%")
print(f"  - rtp_rescue_1: {rtp_rescue_1*100:0.2f}% ({rtp_rescue_1/(rtp_rescue-rtp)*100:5.2f}%)")
print(f"  - rtp_rescue_2: {rtp_rescue_2*100:0.2f}% ({rtp_rescue_2/(rtp_rescue-rtp)*100:5.2f}%)")
print(f"  - rtp_rescue_3: {rtp_rescue_3*100:0.2f}% ({rtp_rescue_3/(rtp_rescue-rtp)*100:5.2f}%)")


print("\n--- 關注指標 ---")
cnt_trigger_rescue_pay = record_data[0, RA_pay_rescue]
cnt_need_help = record_data[0, RA_cnt_need_help]
cnt_trigger_rescue = record_data[0, RA_cnt_trigger_rescue]
cnt_need_help_player = record_data[0, RA_cnt_need_help_player]
cnt_trigger_rescue_player = record_data[0, RA_cnt_trigger_rescue_player]
total_can_trigger = (total_round - observe_rtp_range_2) / trigger_range * player

print("\n* 救援比例")
print("  - 該被救的玩家比例 (該被救玩家數/總玩家數):", f"{cnt_need_help_player/player*100:0.02f}%")
print("  - 該被救且有被救的玩家:", f"{cnt_trigger_rescue_player/cnt_need_help_player*100:0.02f}%")
print("  - 實際救援玩家比例:", f"{cnt_need_help_player/player*cnt_trigger_rescue_player/cnt_need_help_player*100:0.02f}%")
# print("  - 該被救的比例 (該被救總次數/總共可觸發):", f"{cnt_need_help/total_can_trigger*100:0.02f}%")
# print("  - 該被救且有被救的比例 (該被救且有被救/該被救總次數):", f"{cnt_trigger_rescue/cnt_need_help*100:0.02f}%")
print("  - 平均救援次數:", f"{cnt_trigger_rescue/cnt_trigger_rescue_player:0.02f} 次/人")
print("  - 平均救援強度:", f"{cnt_trigger_rescue_pay/cnt_trigger_rescue/threshold:0.00f}x")
print("  - 救援次數:", f"{cnt_trigger_rescue:0.00f} 次")


print("\n* 救援次數:", cnt_trigger_rescue)
print(f"  - 救援次數-救援1: {record_data_rescue_mode[record_data_rescue_mode==1].shape[0]}")
print(f"  - 救援次數-救援2: {record_data_rescue_mode[record_data_rescue_mode==2].shape[0]}")
print(f"  - 救援次數-救援3: {record_data_rescue_mode[record_data_rescue_mode==3].shape[0]}")


# %%


print("\n--- RTP 觀察 ---")
threshold_rtp = 0.80

f = lambda row_data_pay_filter: np.nansum(row_data_pay_filter, axis=1) / np.sum(~np.isnan(row_data_pay_filter), axis=1) / threshold

# row_data_rtp_200 = row_data_pay[:, :200].sum(axis=1) / 200 / threshold
# row_data_rtp_500 = row_data_pay[:, :500].sum(axis=1) / 500 / threshold
# row_data_rtp_1000 = row_data_pay[:, :1000].sum(axis=1) / 1000 / threshold
# row_data_rtp_2000 = row_data_pay[:, :2000].sum(axis=1) / 2000 / threshold

# data_rescue_rtp_200 = record_data_rescue_pay[:, :200].sum(axis=1) / 200 / threshold
# data_rescue_rtp_500 = record_data_rescue_pay[:, :500].sum(axis=1) / 500 / threshold
# data_rescue_rtp_1000 = record_data_rescue_pay[:, :1000].sum(axis=1) / 1000 / threshold
# data_rescue_rtp_2000 = record_data_rescue_pay[:, :2000].sum(axis=1) / 2000 / threshold

row_data_rtp_200 = row_data_pay[:, :200].sum(axis=1) / 200 / threshold
row_data_rtp_500 = row_data_pay[:, :500].sum(axis=1) / 500 / threshold
row_data_rtp_1000 = row_data_pay[:, :1000].sum(axis=1) / 1000 / threshold
row_data_rtp_2000 = row_data_pay[:, :2000].sum(axis=1) / 2000 / threshold

data_rescue_rtp_200 = record_data_rescue_pay[:, :200].sum(axis=1) / 200 / threshold
data_rescue_rtp_500 = record_data_rescue_pay[:, :500].sum(axis=1) / 500 / threshold
data_rescue_rtp_1000 = record_data_rescue_pay[:, :1000].sum(axis=1) / 1000 / threshold
data_rescue_rtp_2000 = record_data_rescue_pay[:, :2000].sum(axis=1) / 2000 / threshold

before_200 = row_data_rtp_200[row_data_rtp_200 < threshold_rtp].shape[0] / player
before_500 = row_data_rtp_500[row_data_rtp_500 < threshold_rtp].shape[0] / player
before_1000 = row_data_rtp_1000[row_data_rtp_1000 < threshold_rtp].shape[0] / player
before_2000 = row_data_rtp_2000[row_data_rtp_2000 < threshold_rtp].shape[0] / player

after_200 = data_rescue_rtp_200[data_rescue_rtp_200 < threshold_rtp].shape[0] / player
after_500 = data_rescue_rtp_500[data_rescue_rtp_500 < threshold_rtp].shape[0] / player
after_1000 = data_rescue_rtp_1000[data_rescue_rtp_1000 < threshold_rtp].shape[0] / player
after_2000 = data_rescue_rtp_2000[data_rescue_rtp_2000 < threshold_rtp].shape[0] / player

print(f"\n* 200轉:  {before_200*100:5.02f}% -> {after_200*100:5.02f}%")
print(f"* 500轉:  {before_500*100:5.02f}% -> {after_500*100:5.02f}%")
print(f"* 1000轉: {before_1000*100:5.02f}% -> {after_1000*100:5.02f}%")
print(f"* 2000轉: {before_2000*100:5.02f}% -> {after_2000*100:5.02f}%")


# %% Output to Excel


# now = datetime.now().strftime("%y%m%d%H%M%S")
# df = pd.DataFrame(record_data[1:, :])
# # file_name = "output_rescue_data_" + now + ".xlsx"
# # df.to_csv(file_name, index=False, header=False)
# file_name = "output_rescue_data.xlsx"
# df.to_excel(file_name, index=False, header=False)

# print(file_name + " saved.")


# %%
