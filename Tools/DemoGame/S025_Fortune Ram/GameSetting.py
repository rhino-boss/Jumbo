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


domo_name = "Howl Wolf(S023)"

payline_alpha = 30  # 顯示走線時的透明度

function_space_height = 40  # 按鈕高度
symbol_adj_size = 0.3  # symbol 大小修正參數

text_size = 22  # 字體大小
text_font = "Microsoft JhengHei"  # 字體

symbol_move_limit = 1300  # 移動距離
# symbol_move_limit = 300  # 移動距離

layout_spacing_width = 10  # symbol 間距

spin_and_spin_wait = 50  # spin 間的停頓時間
payline_show_wait = 500  # show 走線的停頓時間
auto_wait = 100  # auto spin 的間隔時間

reel_speed = 700  # 滾輪移動速度(150)
reel_wait = 30  # reel 間的間隔(延遲時間)
move_unit = 5  # 移動單位

show_arr_len = 10  # 滾動長度


# %% show text format


format_bg_round_btn = "base game"
format_fg_round_btn = "free game ({spin_cum} / {free_spins})"

format_payline_btn_payline = "{symbol}*{line}*{way}, win {pay}"
format_bg_payline_btn_scatterpay = "{symbol}*{line}, win {pay}"
format_fg_payline_btn_scatterpay = "{symbol}*{line}, win {pay}"

format_score_btn = 0

format_info1_btn = "hit rate: {_show_hit_rate:0.2f}  ( hits: {hits} / spins: {spins} )"
format_bg_info2_btn = "max score: {max_score_one}"
format_fg_info2_btn = "max score: {max_score_one} / {max_score}"
format_info3_btn = "free game trigger: {trigger_cum} ( period: {trigger_period} )"
format_info4_btn = "rng: {rng}"


# %%
