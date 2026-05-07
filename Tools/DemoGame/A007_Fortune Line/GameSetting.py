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
    white = (255, 255, 255, 100)
    gray = (153, 151, 153, 100)
    black = (0, 0, 0, 100)
    red = (255, 0, 0, 100)


# image
path_icon = os.path.join("Source\img", "icon.png")
path_symbol_img = os.path.join("Source/img/symbol")

# math
path_math_data = os.path.join("Source", "math.xlsx")
path_script_data = os.path.join("Source", "script.csv")


# %% setting (自定義)

# game info
domo_name = "A007-Power Line"

# 畫面
# - window
alpha_payline = 30  # 顯示走線時的透明度
alpha_0 = 0
alpha_30 = 30
alpha_100 = 100
alpha_max = 1000
alpha_none = -1

function_space_height = 25  # 按鈕高度
layout_spacing_width = 5  # 物件間距

text_size = 16  # 字體大小
text_font = "Microsoft JhengHei"  # 字體

symbol_adj_size = 0.15  # 標誌大小修正參數
symbol_move_limit = 1500  # [移動距離]，標誌從哪裡開始出滾動
show_arr_len = 14  # [滾動長度]，和移動距離要搭配調整

# - delay
wait_update = 5  # 刷新間隔(30)
wait_spin_and_spin = 5  # spin 間的停頓時間(50)
wait_payline_show = 5  # show 走線的停頓時間(500)
wait_auto = 5  # auto spin 的間隔時間(100)
wait_reel = 30  # reel 間的間隔(延遲時間)(30)

# - speed
speed_reel = 10000  # 滾輪移動速度
move_unit = 10  # 移動單位(10)

# - window
window_add_show = 5  # 向上多接露多少輪

# - text format
format_bg_round_btn = "base game"
format_fg_round_btn = "free game ({spin_cum} / {free_spins})"

format_payline_btn_payline = "line {line_id}, {symbol}*{line}, win {pay}"
format_bg_payline_btn_scatterpay = "{symbol}*{line}, win {pay}"
format_fg_payline_btn_scatterpay = "{symbol}*{line}, win {pay}"

format_score_btn = 0

format_info1_btn = "hit rate: {_show_hit_rate:0.2f}  ( hits: {hits} / spins: {spins} )"
format_bg_info2_btn = "max score: {max_score_one}"
format_fg_info2_btn = "max score: {max_score_one} / {max_score}"
format_info3_btn = "free game trigger: {trigger_cum} ( period: {trigger_period} )"
format_info4_btn = "rng: {rng}"


# %%
