# %% --- import ---


import os
import numpy as np

import pygame as pg
from pygame.locals import QUIT

import Math as MM
import GameSetting as GS


#%% --- pre-setting ---


# img name list
symbol_names = os.listdir(GS.path_symbol_img)
sw = GS.layout_spacing_width

# symbol
_img = pg.image.load(GS.path_symbol_img + "/" + symbol_names[0])
symbol_w = _img.get_width() * GS.symbol_adj_size  # (w, h)
symbol_h = _img.get_height() * GS.symbol_adj_size
symbol_size = (symbol_w, symbol_h)

# layout
layout_w = symbol_w * MM.reel_num + GS.layout_spacing_width * (MM.reel_num + 1)

up_space_size = (layout_w - sw * 2, GS.function_space_height)
down_space_size = (layout_w, GS.function_space_height)

layout_h = symbol_h * MM.window_size + up_space_size[1] + down_space_size[1] + GS.layout_spacing_width * (MM.window_size + 2 + 2)

layout_size = (layout_w, layout_h)


#%% --- object---


class Symbol(pg.sprite.Sprite):

    dx = 0
    dy = 0
    x = 0  # x坐標
    y = 0  # y坐標
    speed = 0  # 移動速度
    limit = 0

    def __init__(self, sp, sx, sy, simg, limit=GS.symbol_move_limit, shadow=False):

        # intial setting
        pg.sprite.Sprite.__init__(self)
        self.speed = sp
        self.x = sx
        self.y = sy
        self.limit = limit

        # symbol setting
        self.image = simg
        if shadow == True:
            self.image.set_alpha(GS.payline_alpha)
        self.rect = self.image.get_rect()  # 取得object區域
        self.rect.topleft = (sx, sy)  # 初始位置

    # 移動
    def update(self):

        if self.dy >= self.limit:
            return False

        # 計算新坐標
        # self.x += 0
        self.y += self.speed
        self.dy += self.speed

        # 移動圖形
        # self.rect.x = self.x
        self.rect.y = self.y


class Button(pg.sprite.Sprite):

    show_text = "default"
    click_text = "default"
    position = (0, 0)
    size = [10, 10]
    color = GS.Color.black
    on = False

    def __init__(self, show_text, position, size, color, click_text=""):

        self.show_text = show_text
        self.click_text = click_text
        self.position = position
        self.size = size
        self.color = color

        # intial setting
        pg.sprite.Sprite.__init__(self)

        # img setting
        self.image = pg.Surface(self.size)  # object 'width', 'height'
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.rect.topleft = self.position  # 初始位置

        # font
        self.font = pg.font.SysFont("Arial", GS.text_size)
        self.text = self.font.render(show_text, True, GS.Color.white)
        self.text_center = self.text.get_rect(center=(self.rect.w / 2, self.rect.h / 2))
        self.image.blit(self.text, self.text_center)

    def click(self):
        if self.click_text == "":
            return

        self.on = self.on == False

        # img setting
        self.image = pg.Surface(self.size)  # object 'width', 'height'
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.rect.topleft = self.position  # 初始位置

        # font
        text = self.show_text if self.on == False else self.click_text
        self.font = pg.font.SysFont("Arial", GS.text_size)
        self.text = self.font.render(text, True, GS.Color.white)
        self.text_center = self.text.get_rect(center=(self.rect.w / 2, self.rect.h / 2))
        self.image.blit(self.text, self.text_center)

    def update_text(self, text):

        # img setting
        self.image = pg.Surface(self.size)  # object 'width', 'height'
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.rect.topleft = self.position  # 初始位置

        # font
        self.font = pg.font.SysFont("Arial", GS.text_size)
        self.text = self.font.render(text, True, GS.Color.white)
        self.text_center = self.text.get_rect(center=(self.rect.w / 2, self.rect.h / 2))
        self.image.blit(self.text, self.text_center)


class Status:
    flag_show_payline = False
    flag_rolling = True
    flag_auto_spin = False
    flag_respin = False

    def __init__(self) -> None:
        self.flag_show_payline = False
        self.flag_rolling = False
        self.flag_auto_spin = False
        self.flag_respin = False

    def update_status(self, show_payline=False, rolling=False, auto_spin=False, respin=False):
        self.flag_show_payline = show_payline
        self.flag_rolling = rolling
        self.flag_auto_spin = auto_spin
        self.flag_respin = respin


#%% --- intial ---


# game title setting
pg.init()
pg.display.set_caption(GS.domo_name)

screen_icon = pg.image.load(GS.path_icon)
pg.display.set_icon(screen_icon)


# surface setting
slot_window_surface = pg.display.set_mode(layout_size)  # symbol / 1層
slot_window_surface.fill(GS.Color.white)
event_surface = pg.display.set_mode(layout_size)  # 事件 / 2層(最上層)
event_surface.fill(GS.Color.white)


# button setting
btns = pg.sprite.Group()

announcement_area = Button("", (sw, sw), up_space_size, GS.Color.gray)
btns.add(announcement_area)

btn_w = (down_space_size[0] - 4 * sw) / 4
btn_h = GS.function_space_height
btn_size = (btn_w, btn_h)

score_btn = Button("score: 0", (sw, layout_h - sw * 2 - btn_h), (btn_w * 2, btn_h), GS.Color.gray)
btns.add(score_btn)

autospin_btn = Button("auto spin", (sw * 2 + btn_w * 2, layout_h - sw * 2 - btn_h), (btn_w, btn_h), GS.Color.gray, click_text="inf")
btns.add(autospin_btn)

spin_btn = Button("spin", (sw * 3 + btn_w * 3, layout_h - sw * 2 - btn_h), (btn_w, btn_h), GS.Color.gray)
btns.add(spin_btn)

btns.draw(event_surface)


def generate_objects(show_arr, show_type, show_line=np.zeros(MM.arr_shape), respin_posi=[0, 0, 0, 1, 0]):

    # output
    reel_groups = []
    symbol_objs = []

    #
    symbol_names = os.listdir(GS.path_symbol_img)
    symbol_names.sort()

    #
    arr_shape = show_arr.shape
    for j in range(arr_shape[1]):  # 5 (reel num)
        reel = pg.sprite.Group()
        for i in range(arr_shape[0]):  # 3 (window size)

            symbol_id = int(abs(show_arr[i, j]))
            symbol_name = symbol_names[symbol_id]

            # load img
            img = pg.image.load(GS.path_symbol_img + "/" + symbol_name)
            img = pg.transform.scale(img, symbol_size)

            # create symbol object
            _sw = GS.layout_spacing_width * (j + 1) + j * symbol_w
            _sh = GS.function_space_height + sw * 2 + i * (symbol_h + sw)
            if show_type == "base":
                s = Symbol(5, _sw, _sh - GS.symbol_move_limit, img)
            elif show_type == "payline":
                s = Symbol(5, _sw, _sh, img, shadow=show_line[i, j] == 0, limit=0)
            elif show_type == "respin":
                if respin_posi[j] == 0:  # move reel
                    s = Symbol(5, _sw, _sh - GS.symbol_move_limit, img)
                else:  # stick reel
                    s = Symbol(5, _sw, _sh, img, limit=0)

            reel.add(s)
            symbol_objs.append(s)

        reel_groups.append(reel)

    return reel_groups, symbol_objs


# 初始盤面
show_reels, symbol_objs = generate_objects(np.zeros(MM.arr_shape), "payline")  # 建立初始物件群組(假的盤面)
show_datas = [dict(reel=show_reels, symbols=symbol_objs, type="payline", score=20)]


# 初始畫面刷新
pg.display.update()


#%% --- start ---


# -  cnt (temp)
cnt_reel_wait = 0  # reel 間的延遲 (搭配"threshold_reel_roll_delay"使用)
cnt_auto_wait = 0  # auto spin 延遲
cnt_spin_and_spin_wait = 0  # 每把間的延遲時間

# - ?? (temp)
flag = True  # 關閉遊戲後停止迴圈
flags = Status()
spin_btn_click = False

hits = 0
spins = 0
score = 0
spin_and_calc_result = []  # (score, arr_result, rng, show_lines, respin_posi)

# - else
threshold_reel_roll_delay = [i * GS.reel_wait for i in range(MM.reel_num)]  # reel 間滾動延遲


# - main
show_now = show_datas.pop(0)
while flag:

    # [preset 預設]
    pg.time.Clock().tick(GS.reel_speed)  # 數字越大，動越快

    # [status 狀態紀錄] :
    flags.flag_rolling = False
    for i in show_now["symbols"]:
        if i.limit != i.dy:
            flags.flag_rolling = True
            break

    # [update 資料刷新]
    if flags.flag_rolling == False and len(show_datas) > 0:
        if spin_btn_click:
            cnt_spin_and_spin_wait = 0
            cnt_reel_wait = 0
            spin_btn_click = False
        else:
            if cnt_spin_and_spin_wait < GS.spin_and_spin_wait:
                cnt_spin_and_spin_wait += 1
            else:
                cnt_spin_and_spin_wait = 0
                cnt_reel_wait = 0
                show_now = show_datas.pop(0)

    # [layout 畫面相關]

    # -- game info
    score_btn.update_text(f"score: {show_now['score']}")

    # -- reel wait (滾動間隔設定)
    show_hit_rate = hits / spins if spins > 0 else 0
    if show_now["type"] == "payline":
        announcement_area.update_text(f"hits: {hits}, spins: {spins}, hit rate: {show_hit_rate:0.2f}")
        threshold_reel_roll_delay = [0 for i in range(MM.reel_num)]  # reel 間滾動延遲
    elif show_now["type"] in ["payline", "respin"]:
        announcement_area.update_text(f"re-spin: {show_now.get('level')}")
        threshold_reel_roll_delay = [0 for i in range(MM.reel_num)]  # reel 間滾動延遲
    else:
        announcement_area.update_text(f"hits: {hits}, spins: {spins}, hit rate: {show_hit_rate:0.2f}")
        threshold_reel_roll_delay = [i * GS.reel_wait for i in range(MM.reel_num)]  # reel 間滾動延遲

    # -- update move (滾動)
    slot_window_surface.fill(GS.Color.white)  # 畫面清空
    for i in range(len(show_now["reel"])):
        if cnt_reel_wait < threshold_reel_roll_delay[i]:
            reel.draw(slot_window_surface)
        else:
            reel = show_now["reel"][i]
            reel.draw(slot_window_surface)
            reel.update()

    # -- auto spin (自動)
    if autospin_btn.on and len(show_datas) == 0:

        # clear temp storage
        show_datas.clear()
        slot_window_surface.fill(GS.Color.white)  # 畫面清空

        # math
        math_results = MM.freegame_spin_and_calculate()

        level = 0
        for math_res in math_results:

            score = math_res.score
            arr_result = math_res.arr_result

            rng = math_res.rng
            paylines = math_res.paylines

            new_wild_posi = math_res.respin_posi
            respin_show_arr = math_res.respin_show_arr

            if level == 0:
                _show_type = "base"
                _show_arr = arr_result
            else:
                _show_type = "respin"
                _show_arr = respin_show_arr

            show_reels, symbol_objs = generate_objects(_show_arr, _show_type, respin_posi=new_wild_posi)  # 建立全部物件群組
            ori = dict(reel=show_reels, symbols=symbol_objs, type=_show_type, score=score, level=level)
            show_datas.append(ori)

            for pl in paylines:
                show_reels, symbol_objs = generate_objects(_show_arr, "payline", show_line=pl)  # 建立全部物件群組
                show_datas.append(dict(reel=show_reels, symbols=symbol_objs, type="payline", score=score, level=level))

            ori = ori.copy()
            ori["type"] = "payline"
            show_datas.append(ori)
            show_datas.append(ori)

            level += 1

        spins += 1
        if score > 0:
            hits += 1

        cnt_reel_wait = 0
        show_now = show_datas.pop(0)

    # -- update layout
    btns.draw(event_surface)
    pg.display.update()

    # -- update
    cnt_reel_wait += 1

    # [event 事件]
    for event in pg.event.get():
        if event.type == QUIT:  # 當使用者結束視窗，程式也結束
            flag = False
            pg.quit()

        if event.type == pg.MOUSEBUTTONDOWN:
            if spin_btn.rect.collidepoint(event.pos):

                # clear temp storage
                show_datas.clear()
                slot_window_surface.fill(GS.Color.white)  # 畫面清空

                # math
                math_results = MM.freegame_spin_and_calculate()

                level = 0
                for math_res in math_results:

                    score = math_res.score
                    arr_result = math_res.arr_result

                    rng = math_res.rng
                    paylines = math_res.paylines

                    new_wild_posi = math_res.respin_posi
                    respin_show_arr = math_res.respin_show_arr

                    if level == 0:
                        _show_type = "base"
                        _show_arr = arr_result
                    else:
                        _show_type = "respin"
                        _show_arr = respin_show_arr

                    show_reels, symbol_objs = generate_objects(_show_arr, _show_type, respin_posi=new_wild_posi)  # 建立全部物件群組
                    ori = dict(reel=show_reels, symbols=symbol_objs, type=_show_type, score=score, level=level)
                    show_datas.append(ori)

                    for pl in paylines:
                        show_reels, symbol_objs = generate_objects(_show_arr, "payline", show_line=pl)  # 建立全部物件群組
                        show_datas.append(dict(reel=show_reels, symbols=symbol_objs, type="payline", score=score, level=level))

                    ori = ori.copy()
                    ori["type"] = "payline"
                    show_datas.append(ori)
                    show_datas.append(ori)

                    level += 1

                spins += 1
                if score > 0:
                    hits += 1

                cnt_reel_wait = 0
                show_now = show_datas.pop(0)

            if autospin_btn.rect.collidepoint(event.pos):

                # update slot window
                autospin_btn.click()


print("game close.")
