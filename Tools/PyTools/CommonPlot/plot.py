# %% import

import os

os.chdir("C:\\Users\\rhinshen\\Mine\\個人工作區\\2_Program")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# %%


row_data = pd.read_excel("rowdata_2k_2k_真實資料_包含新手期.xlsx", sheet_name="data", header=None).to_numpy()
row_data_rescue = pd.read_excel("rowdata_2k_2k_真實資料_包含新手期.xlsx", sheet_name="data_rescue", header=None).to_numpy()


# %%

x_axis = np.tile(np.arange(1, 2001), (2000, 1))
data_ori = row_data[:2000, :].cumsum(axis=1) / x_axis / 1000000
data_rescue = row_data_rescue[:2000, :].cumsum(axis=1) / x_axis / 1000000

# 顯示資料設定
data_ori_show = data_ori[:, 200:]
data_rescue_ori_show = data_rescue[50:100, 200:]
x_data_ori_show = np.arange(201, data_ori_show.shape[1] + 201)
show_players = data_ori_show.shape[0]

# 統計量
data_ori_show_mean = data_ori_show.mean(axis=0)
data_ori_show_min = data_ori_show.min(axis=0)
data_rescue_ori_show_mean = data_rescue_ori_show.mean(axis=0)
data_rescue_ori_show_min = data_rescue_ori_show.min(axis=0)

# 回歸線
coef = np.polyfit(x_data_ori_show, data_ori_show_mean, 1)
trend = np.polyval(coef, x_data_ori_show)
coef_rescue = np.polyfit(x_data_ori_show, data_rescue_ori_show_mean, 1)
trend_rescue = np.polyval(coef_rescue, x_data_ori_show)

# # 信賴區間
# z = 1.96  # 95% 信賴區間
# z = 2.576  # 99% 信賴區間
# ci_lower = data_ori_show_mean - z * data_ori_show_std / np.sqrt(show_players)
# ci_upper = data_ori_show_mean + z * data_ori_show_std / np.sqrt(show_players)


# 平滑處理
def smooth(y, window):
    return np.convolve(y, np.ones(window) / window, mode="valid")


window = 30

data_ori_show_min = smooth(data_ori_show_min, window)
data_rescue_ori_show_min = smooth(data_rescue_ori_show_min, window)

x_data_ori_show = x_data_ori_show[window - 1 :]
data_ori_show = data_ori_show[:, window - 1 :]
data_rescue_ori_show = data_rescue_ori_show[:, window - 1 :]


# 畫圖
plt.figure(figsize=(6, 4))

# for i in range(data_ori_show.shape[0]):
#     plt.scatter(x_data_ori_show, data_ori_show[i], s=5, alpha=0.01, label=f"row {i}")  # 透明度

plt.plot(x_data_ori_show, data_ori_show_min, linewidth=1.5, label="min", color="black")
plt.plot(x_data_ori_show, data_rescue_ori_show_min, linewidth=1.5, label="min_rescue", color="red")

# plt.plot(x_data_ori_show, trend, linestyle="--", linewidth=1.5, label="Linear regression", color="blue")
# plt.plot(x_data_ori_show, trend_rescue, linestyle="--", linewidth=1.5, label="Linear regression", color="Green")


plt.xlabel("spin")
plt.ylabel("RTP%")
plt.ylim(0.3, 2)
plt.legend()

plt.grid()
plt.tight_layout()
plt.show()


# %%
