"""
使用流程 :

[畫面] GameSetting.py
1. icon 設定(未設定會是預設嚎野狼的圖) : 
  設定方式 -> 把這個"./Source/img/icon.png"取代掉
2. 區域參數設定(可用預設) : 
  "setting (自定義)"這區域的都可調整 

[數學] Math.py
3. 設定:

[Game] Demo
4. Game Run

"""


# %% setting (不可動)

import os


class Color:
    white = (255, 255, 255)
    gray = (153, 151, 153)
    black = (0, 0, 0)


# image
path_icon = os.path.join("Source\img", "icon.png")
path_symbol_img = os.path.join("Source/img/symbol")

# math
path_math_data = os.path.join("Source", "math.xlsx")


# %% setting (自定義)


domo_name = "Slot - Howl Wolf (S023)"


payline_alpha = 30  # 顯示走線時的透明度

function_space_height = 40  # 按鈕高度
symbol_adj_size = 0.65  # symbol 大小修正參數

text_size = 25  # 字體大小
text_font = "Microsoft JhengHei"  # 字體

symbol_move_limit = 150  # 移動距離

layout_spacing_width = 10  # symbol 間距

spin_and_spin_wait = 30  # spin 間的停頓時間(100)
# payline_show_wait = 100  # show 走線的停頓時間
# auto_wait = 30  # auto spin 的間隔時間

reel_speed = 150  # 滾輪移動速度(150)
reel_wait = 10  # reel 間的間隔(延遲時間)


# %%
