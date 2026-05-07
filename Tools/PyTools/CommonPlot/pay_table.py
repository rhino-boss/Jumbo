# %% import


import numpy as np
import pandas as pd

# seaborn
import seaborn as sns

# plotly
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import plotly.io as pio
from plotly.graph_objects import Layout

pio.renderers.default = "browser"

# matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]


# %% matplotlib


def plot(paytable, symbol, line, coin_in=0, ylim=1000):
    """

    Example
    ---
    paytable = np.array([[50, 150, 1000], [50, 100, 400], [10, 50, 250], [10, 50, 125], [5, 50, 100], [5, 30, 100], [5, 30, 100], [5, 20, 100], [5, 20, 100], [5, 15, 100],]) # 換行\n
    symbol = ["M1", "M2", "M3", "M4", "A", "K", "Q", "J", "TE", "NI"] # 換行\n
    line = [f"line {i}" for i in range(3, 5 + 1)] # 換行\n
    coin_in = 25 # 換行\n

    >>> plot(paytable, symbol, line, 10, 1300)

    """

    # base setting
    fig_size = (15, 12)
    font_set = (30, 20, 20, 14)  # (title, ticks, legend, show_text)

    x_space = np.arange(len(line)) * 3  # 控制x軸間隔
    bar_width = 0.26
    edge_width = 3
    text_posi_adj = 0.05

    show_text_space = 60

    # palette setting
    palette = []
    palette.extend(sns.color_palette("hls", len(symbol)))

    # plot
    plt.figure(figsize=fig_size)

    # plot bar
    for i in range(len(symbol)):
        x_value = x_space + bar_width * i
        y_value = paytable[i]
        plt.bar(x_value, y_value, bar_width, label=symbol[i], color=palette[i], edgecolor="w", linewidth=edge_width)

        if coin_in != 0:
            for _x, _y in zip(x_value, y_value):
                mul = _y / coin_in
                show_text = f"{_y / coin_in:0.1f}倍 ({symbol[i]})"
                if mul > 0 and mul < 1:
                    plt.text(_x + text_posi_adj, _y + show_text_space, show_text, ha="center", fontsize=font_set[3], rotation=90, alpha=0.7)
                elif mul >= 1:
                    plt.text(_x + text_posi_adj, _y + show_text_space, show_text, ha="center", fontsize=font_set[3], rotation=90, alpha=0.7)
                else:
                    plt.text(_x + text_posi_adj, _y + show_text_space, "x", ha="center", fontsize=font_set[3], rotation=90, alpha=0.7)

    # 顯示文字設定
    plt.title("賠率", fontsize=font_set[0])

    plt.ylim(0, ylim)

    plt.xticks(x_space + bar_width * len(symbol) / 2 - bar_width, line, fontsize=20)
    plt.yticks(fontsize=font_set[1])

    plt.legend(fontsize=font_set[2], loc="upper right")
    plt.grid(alpha=0.7)
    plt.show()


paytable = np.array(
    [
        [50, 200, 2500],
        [30, 100, 300],
        [200, 50, 20],
        [20, 50, 100],
        [50, 20, 10],
        [50, 20, 10],
        [30, 20, 10],
        [30, 20, 10],
    ]
)
symbol = ["M1", "M2", "M3", "M4", "A", "K", "Q", "J"]
line = [f"line {i}" for i in range(3, 5 + 1)]
coin_in = 50

plot(paytable, symbol, line, 10, 3000)


# %% plotly


# # data prepare
# paytable = np.array([
#     [50, 150, 1000],
#     [50,100,400],
#     [10,50,250],
#     [10,50,125],
#     [5,50,100],
#     [5,30,100],
#     [5,30,100],
#     [5,20,100],
#     [5,20,100],
#     [5,15,100],
# ])
# symbol = ['M1', 'M2', 'M3', 'M4', 'A', 'K', 'Q', 'J', 'TE', 'NI']
# arr_shape = (3, 5)

# col = [f"line{i+1}" for i in range(2, arr_shape[1])]

# df = pd.DataFrame(paytable, columns=col)
# df["symbol"] = symbol
# df.set_index("symbol", inplace=True)

# df = df[col].stack().reset_index()
# df.columns = ["symbol", "line", "pay"]
# df

# # layout setting
# axis_template = dict(
#     showgrid=True,
#     # zeroline=True,
#     nticks=20,
#     showline=True,
#     linewidth=3,
#     linecolor="rgb(150,150,150,150)",  # 外框顏色
#     gridcolor="rgb(192, 192, 192, 192)",  # grid顏色
#     mirror="all",
#     # zerolinecolor="rgb(150,150,150,150)",
# )

# layout = go.Layout(
#     title="賠率",
#     xaxis=axis_template,  # 外框線格式
#     yaxis=axis_template,  # 外框線格式
#     showlegend=True,
#     plot_bgcolor="rgba(0,0,0,0)"
#     # legend=dict(x=0.9, y=1.1)
# )

# # plot
# fig = go.Figure(layout=layout)
# for s, group in df.groupby("symbol", sort=False):
#     fig.add_trace(go.Bar(x=group["line"], y=group["pay"], name=s))

# # update plot status
# fig.update_xaxes(title_text="賠率")  # 更新x-axis
# fig.update_yaxes(title=dict(text="連線", font_size=20))  # 更新y-axis
# fig.update_layout(legend=dict(title="symbol"), title=dict(font_size=50))

# fig.show()


# %% binomial

# nn = 9
# pp = 0.57376
# ss = 10 ** 5

# dd = np.random.binomial(n=nn, p=pp, size=ss)
# plt.figure(figsize=(15, 12))
# pl = plt.hist(dd - 0.5, bins=np.arange(0, 11) - 0.5, rwidth=0.5, density=True)
# plt.xticks(np.arange(0, 11))
# plt.title(f"Binomial Distribution (n={5}, p={pp}, size={ss})", fontsize=28)

# plt.ylim(0, 0.4)

# plt.xticks(fontsize=20)
# plt.yticks(fontsize=20)

# # plt.legend(fontsize=20, loc="upper right")
# plt.grid(alpha=0.7)
# plt.show()


# %%

# yy = [0, 5552618, 2141356, 397686, 54935, 7737, 951, 146, 16, 5, 0]
# xx = [i for i in range(len(yy))]


# plt.figure(figsize=(15, 12))

# pl = plt.bar(xx, yy)
# plt.xticks(xx)
# # plt.title(f"Binomial Distribution (n={5}, p={pp}, size={ss})", fontsize=28)

# # plt.ylim(0, 0.4)

# plt.xticks(fontsize=20)
# plt.yticks(fontsize=20)

# # # plt.legend(fontsize=20, loc="upper right")
# plt.grid(alpha=0.7)
# plt.show()

# %%
