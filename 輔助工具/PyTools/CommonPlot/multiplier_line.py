# %% import

import os

os.chdir(r"C:\Users\rhinshen\Mine\(個人工作區)\3_Tools\PyTools")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# my package
import Source.Box as Box
import Source.Math as Mat


# %%


def plot(
    plot_datas,
    title,
    x_lable,
    plot_type=0,
    filename="",
    ylim=0.16,
    start_idx=0,
    line_color=("red", "orange", "green", "blue", "purple"),
):
    """
    Parameters
    ---
    plot_datas -> (np.array, str)
        input lot data.

    start_idx -> int, default 0
        data start index.

    line_color -> turple, list, default ('red', 'orange', 'green', 'blue', 'purple')
        line color.

    plot_type -> int, default 0
        0: normal
        1: cumsum

    Example
    ---
    plt.show()

    plot_datas = []

    data_bear = pd.read_excel("./Multiplier_Line/RowData/台灣黑熊.xlsx", index_col=0)
    plot_datas.append((data_bear.values, "台灣黑熊"))

    data_nepoleon = pd.read_excel("./Multiplier_Line/RowData/拿破崙.xlsx", index_col=0)
    plot_datas.append((data_nepoleon.values, "拿破崙"))

    >>> plot(plot_datas, "倍率線型", data_bear.index.tolist(), filename="倍率線型")

    """

    # setting
    plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]  # 中文設定
    plt.rcParams["axes.unicode_minus"] = False

    plot_size = (14, 8)
    font_set = (28, 24, 14, 20)

    x_lable = x_lable[start_idx:]

    # split datas, names and converted to percentage
    datas = []
    names = []

    if plot_type == 0:
        for pds in plot_datas:
            ori_data = pds[0].copy()[start_idx:]
            names.append(pds[1])
            # datas.append(ori_data / sum(ori_data))
            datas.append(ori_data.cumsum() / sum(ori_data))
    elif plot_type == 1:
        for pds in plot_datas:
            ori_data = pds[0].copy().cumsum()[start_idx:]
            names.append(pds[1])
            datas.append(ori_data / ori_data[-1])
    else:
        print("error")
        return

    # plot
    plt.figure(figsize=plot_size)

    for idx, pds in enumerate(datas):
        plt.plot(
            [i for i in range(len(pds))],
            pds,
            marker="o",
            label=names[idx],
            color=line_color[idx],
        )

    plt.title(title, fontsize=font_set[0])

    # plt.xlabel("Multiple", fontsize=font_set[1])
    # plt.ylabel("Freq(%)", fontsize=font_set[1])

    plt.xticks([i for i in range(len(datas[0]))], x_lable, rotation=90, fontsize=font_set[2])
    plt.yticks(fontsize=font_set[1])

    plt.ylim(0, ylim)

    plt.legend(fontsize=font_set[3])
    plt.grid()

    # save fig
    if filename != "":
        plt.savefig(
            f"./CommonPlot/Multiplier_Line/Plot/{filename}.jpg",
            bbox_inches="tight",
            dpi=300,
            transparent=True,
        )


dirr = "./CommonPlot/Multiplier_Line/RowData/"
scence_BG, scence_FG, scence_RD, scence_OA = 0, 1, 2, 2

plot_datas = []

data = pd.read_excel(dirr + "output_power_dragon_online.xlsx", sheet_name="Multiplier Line", index_col=0)
data = Mat.cplot.map_multiplier_big2small(Mat.threshold_v3, Mat.threshold_v4, data.values[:, scence_FG])
plot_datas.append((data, "online"))

data = pd.read_excel(
    dirr + "output_power_dragon_landbase.xlsx",
    sheet_name="Multiplier Line",
    index_col=0,
)
data = Mat.cplot.map_multiplier_big2small(Mat.threshold_v3, Mat.threshold_v4, data.values[:, scence_FG])
plot_datas.append((data, "landbase"))

co = ("Red", "Green")
plot(
    plot_datas,
    "Power Dragon Free Game",
    Mat.threshold_v3,
    ylim=1,
    filename="倍率線型",
    start_idx=0,
    line_color=co,
)
# plot(plot_datas, "Power Dragon Overall", Mat.threshold_v3, ylim=0.4, filename="倍率線型", start_idx=0, line_color=co)


# %%
