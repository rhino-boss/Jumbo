# %% import

import numpy as np
import pandas as pd

# plotly
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import plotly.io as pio

pio.renderers.default = "browser"

# matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


# %% matplotlib


def plot(x, y, data, title, show_text=True, xxinfo=""):
    """
    get pay line plot.

    Parameter
    ---
    x -> list, x_ticks \n
    y -> list, y_ticks \n
    data -> np.array, n*m

    Example 1
    ---
    x = ["R1", "R2", "R3", "R4", "R5"] # 換行\n
    y = ["0", "1", "2"]   # 換行\n
    data = np.array([[4, 3, 3, 3, 4], [3, 4, 4, 4, 3], [3, 3, 3, 7, 5]]) # 換行\n

    >>> plot(x, y, data, show_text=True)

    Example 2
    ---
    paylines = ["1111", "0101", "0121"] # 換行\n
    arr_shape = (4, 4) # 換行\n

    for payline in paylines:
        arr = np.zeros(arr_shape)
        for i, p in enumerate(payline):
            arr[int(p), i] = 1

        plot([1, 1, 1, 1], [1, 1, 1, 1], arr, payline, show_text=False)

    """

    # pre-setting
    white_text = data.max()
    arr_shape = data.shape
    df = pd.DataFrame(data, columns=x, index=y)

    # plot prepare
    plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]
    plt.figure(figsize=(160, 9))

    fig, ax = plt.subplots(figsize=(10, 10))
    im = ax.imshow(df, cmap="gray_r")

    # # fill data
    # if show_text:
    #     for i in range(len(df.columns)):
    #         for j in range(len(df.index)):
    #             if data[j, i] == white_text:
    #                 text = ax.text(i, j, data[j, i], ha="center", va="center", color="white", fontdict={"size": 18})
    #             else:
    #                 text = ax.text(i, j, data[j, i], ha="center", va="center", color="black", fontdict={"size": 18})

    # else setting
    ax.set_xticks(np.arange(len(df.columns)))
    ax.set_xticklabels(df.columns)

    plt.setp(ax.get_xticklabels(), rotation=0, ha="right", rotation_mode="anchor")

    ax.set_yticks(np.arange(len(df.index)))
    ax.set_yticklabels(df.index)

    if show_text:
        ax.set_title(xxinfo, fontdict={"size": 20})
        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)
    else:
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)

    ax.get_xaxis().set_visible(False)

    #
    err = 0.5
    w_len = arr_shape[1] * 2 * err - err
    h_len = arr_shape[0] * 2 * err - err
    for i in range(1, arr_shape[0]):
        plt.hlines(i - err - 0.01, -0.5, w_len, colors="black", lw=1)
    for i in range(1, arr_shape[1]):
        plt.vlines(i - err, -0.5, h_len, colors="black", lw=1)

    plt.savefig(f"C:/Users/rhinshen/Mine/(個人工作區)/3_Tools/PyTools/CommonPlot/Pay_Line/{title}.jpg")
    # plt.show()


def plot_all(paylines, arr_shape):
    cum_arr = np.zeros(arr_shape, dtype=np.int16)
    for idx, payline in enumerate(paylines):
        arr = np.zeros(arr_shape, dtype=np.int16)
        for i, p in enumerate(payline):
            arr[int(p), i] = 1
        cum_arr += arr

        plot(
            ["R1", "R2", "R3", "R4", "R5"],
            [str(i) for i in range(arr_shape[0])],
            arr,
            f"{idx}_{payline}",
            show_text=True,
            xxinfo=idx,
        )


paylines = [
    "11111",
    "00000",
    "22222",
    "01210",
    "21012",
    "00100",
    "22122",
    "12221",
    "10001",
    "01110",
    "21112",
    "01010",
    "21212",
    "10101",
    "12121",
    "11011",
    "11211",
    "02020",
    "20202",
    "10201",
    "12021",
    "00200",
    "22022",
    "02220",
    "20002",
    "02120",
    "20102",
    "11112",
    "00122",
    "22100",
    "01112",
    "21110",
    "01212",
    "21010",
    "00001",
    "22221",
    "01012",
    "21210",
    "10121",
    "12101",
    "11000",
    "11222",
    "10012",
    "12210",
    "10122",
    "12100",
    "21001",
    "01221",
    "00121",
    "22101",
]


arr_shape = (3, 5)

plot_all(paylines, arr_shape)


# %% plotly


# import plotly.figure_factory as ff
# import numpy as np

# x = ["R1", "R2", "R3", "R4", "R5"]
# y = ["C3", "C2", "C1"]
# z = np.array(
#     [
#         [4, 3, 3, 3, 4],
#         [3, 4, 4, 4, 3],
#         [3, 3, 3, 3, 3],
#     ]
# )[::-1]

# fig = ff.create_annotated_heatmap(z, x, y, annotation_text=z, colorscale="viridis")

# # plot 內部自體大小
# for i in range(len(fig.layout.annotations)):
#     fig.layout.annotations[i].font.size = 30

# fig.update_xaxes(title=dict(font_size=30), tickfont=dict(size=30))  # 更新x-axis
# fig.update_yaxes(title=dict(font_size=30), tickfont=dict(size=30))  # 更新y-axis


# # fig.show()
