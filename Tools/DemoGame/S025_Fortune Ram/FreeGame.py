# %% --- import ---


import os

# import numpy as np
from numpy import zeros
from numpy import random as nrd

import pygame as pg
from pygame.locals import QUIT

import Math as MM
import GameSetting as GS

from GameSetting import layout_spacing_width as GS_sw
from GameSetting import function_space_height as GS_fsh


#%% --- pre-setting ---


# img name list
symbol_names = os.listdir(GS.path_symbol_img)


# symbol
_img = pg.image.load(GS.path_symbol_img + "/" + symbol_names[0])
symbol_w = _img.get_width() * GS.symbol_adj_size  # (w, h)
symbol_h = _img.get_height() * GS.symbol_adj_size
symbol_size = (symbol_w, symbol_h)


#%% --- area---


class LayoutStatus:
    def __init__(self) -> None:

        # symbol
        self.symbol_w = 0
        self.symbol_h = 0
        self.symbol_size = (0, 0)

        # layout
        self.layout_h = 0
        self.layout_w = 0
        self.layout_size = (0, 0)

        # areas
        self.areas = []  # 裡面存"ObjElement"這個

    def set_symbol(self, symbol_w, symbol_h):
        self.symbol_w = symbol_w
        self.symbol_h = symbol_h
        self.symbol_size = (symbol_w, symbol_h)

    def update_layout(self, h, sw):
        self.layout_h += h + sw
        self.layout_size = (self.layout_w, self.layout_h)

    def get_cum_y(self):
        y = 0
        for area in self.areas:
            if area.area_type == "base":
                y += area.h + GS_sw
            elif area.area_type == "no_sw":
                y += area.h
            else:
                pass
        return y

    def end_setting(self):
        self.layout_h -= 10
        self.layout_size = (self.layout_w, self.layout_h)


class ObjElement:
    def __init__(self, x, y, w, h, area_type):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.posi = (x, y)
        self.size = (w, h)

        self.area_type = area_type


def generate_obj_area(layout_status, size, div, div_type):

    w, h = size

    def get_element_posi(div_list, total_len):
        num = len(div_list)
        element_uw = (total_len - (num - 1) * GS_sw) / sum(div_list)  # element 寬的單位

        new_div_list = [0]
        new_div_list.extend(div_list)
        new_div_list.pop(-1)

        posi_list = []
        ex = 0
        for i in range(num):
            ex += element_uw * new_div_list[i] + GS_sw
            ew = div_list[i] * element_uw
            posi_list.append((ex, ew))

        return posi_list

    if div_type == "base":
        element_col_list = get_element_posi(div, w)
        element_row_list = get_element_posi([1], h)
        layout_status.update_layout(h, GS_sw)

    elif div_type == "no_sw":
        element_col_list = get_element_posi([1], w)
        element_row_list = get_element_posi(div, h)
        layout_status.update_layout(h, 0)

    #
    output_area = []
    for r in element_row_list:
        for c in element_col_list:
            if div_type == "base":
                emt = ObjElement(c[0], r[0] + layout_status.get_cum_y(), c[1], r[1], div_type)
            elif div_type == "no_sw":
                emt = ObjElement(c[0], layout_status.get_cum_y() + GS_sw, c[1], r[1], div_type)
            output_area.append(emt)

        layout_status.areas.append(emt)

    return output_area


def get_mask(layout_status, symbol_area):

    x = symbol_area.x  #
    y = 0
    w = symbol_area.w
    h = symbol_area.y
    mask1 = ObjElement(x, y, w, h, "mask")
    x = symbol_area.x  #
    y = symbol_area.y + symbol_area.h
    w = symbol_area.w
    h = layout_status.layout_h - (symbol_area.y + symbol_area.h)
    mask2 = ObjElement(x, y, w, h, "mask")

    return [mask1, mask2]


layout_status = LayoutStatus()
layout_status.layout_w = symbol_w * MM.reel_num + GS_sw * (MM.reel_num + 1)

f = lambda h, div, div_type: generate_obj_area(layout_status, (layout_status.layout_w - 20, h), div, div_type)

# area
round_area, payline_area = f(GS_fsh, [1, 2], "base")

symbol_area = f(symbol_h * MM.window_size + GS_sw * (MM.window_size - 1), [1], "base")[0]
spinscore_area, autospin_area, spin_area = f(GS_fsh, [2, 1, 1], "base")

info1_area, info2_area, info3_area, info4_area = f(GS_fsh * 4 + GS_sw * 3, [1, 1, 1, 1], "no_sw")

# mask
mask1_area, mask2_area = get_mask(layout_status, symbol_area)

# final
layout_status.end_setting()


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

    on = False

    def __init__(self, show_text, position, size, background_color=GS.Color.gray, text_color=GS.Color.white, is_info=False, click_text=""):

        self.show_text = show_text
        self.click_text = click_text
        self.position = position
        self.size = size
        self.background_color = background_color
        self.text_color = text_color
        self.is_info = is_info

        # intial setting
        pg.sprite.Sprite.__init__(self)

        # img setting
        self.image = pg.Surface(self.size)  # object 'width', 'height'
        self.image.fill(self.background_color)
        self.rect = self.image.get_rect()
        self.rect.topleft = self.position  # 初始位置

        # font
        self.font = pg.font.SysFont(GS.text_font, GS.text_size)
        self.text = self.font.render(show_text, True, self.text_color)
        if self.is_info:
            self.text_center = self.text.get_rect(midleft=(10, self.rect.h / 2))
        else:
            self.text_center = self.text.get_rect(center=(self.rect.w / 2, self.rect.h / 2))
        self.image.blit(self.text, self.text_center)

    def click(self):
        if self.click_text == "":
            return

        self.on = self.on == False

        # img setting
        self.image = pg.Surface(self.size)  # object 'width', 'height'
        self.image.fill(self.background_color)
        self.rect = self.image.get_rect()
        self.rect.topleft = self.position  # 初始位置

        # font
        text = self.show_text if self.on == False else self.click_text
        self.font = pg.font.SysFont(GS.text_font, GS.text_size)
        self.text = self.font.render(text, True, self.text_color)
        if self.is_info:
            self.text_center = self.text.get_rect(midleft=(10, self.rect.h / 2))
        else:
            self.text_center = self.text.get_rect(center=(self.rect.w / 2, self.rect.h / 2))
        self.image.blit(self.text, self.text_center)

    def update_text(self, text):

        # img setting
        self.image = pg.Surface(self.size)  # object 'width', 'height'
        self.image.fill(self.background_color)
        self.rect = self.image.get_rect()
        self.rect.topleft = self.position  # 初始位置

        # font
        self.font = pg.font.SysFont(GS.text_font, GS.text_size)
        self.text = self.font.render(text, True, self.text_color)
        if self.is_info:
            self.text_center = self.text.get_rect(midleft=(10, self.rect.h / 2))
        else:
            self.text_center = self.text.get_rect(center=(self.rect.w / 2, self.rect.h / 2))

        self.image.blit(self.text, self.text_center)


class GameStatus:
    def __init__(self) -> None:

        # layout setting
        self.threshold_reel_roll_delay = [i * GS.reel_wait for i in range(MM.reel_num)]  # reel 間滾動延遲

        self.cnt_reel_wait = 0
        self.cnt_auto_wait = 0
        self.cnt_spin_and_spin_wait = 0

        self.flag = True  # game control (遊戲停止終止迴圈)
        self.flag_rolling = False
        self.flag_spin_btn_click = False

        # show info (text)
        self.max_score_one = 0
        self.max_score = 0
        self.trigger_cum = 0
        self.score_cum = 0
        self.spin_cum = 0
        self.hits = 0
        self.spins = 0
        # self.spin_and_calc_result = []

        self.free_spins = 5

        # math output
        self.show_score = 0
        self.arr_result = None
        self.rng = "--"
        self.paylines = []
        self.trigger_times = 0

        # Data
        self.show_datas = []
        self.show_now = None


def generate_objects(show_arr, show_type, show_line=zeros(MM.arr_shape)):

    # output
    reel_groups = []
    symbol_objs = []

    #
    symbol_names = os.listdir(GS.path_symbol_img)
    symbol_names.sort()

    # symbol_area
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
            _sw = symbol_area.x + j * (GS_sw + symbol_w)
            _sh = symbol_area.y + i * (GS_sw + symbol_h)

            if show_type == "base":
                s = Symbol(GS.move_unit, _sw, _sh - GS.symbol_move_limit, img)
            elif show_type == "payline":
                s = Symbol(GS.move_unit, _sw, _sh, img, shadow=show_line[i, j] == 0, limit=0)
            else:
                s = Symbol(GS.move_unit, -999, -999, img, limit=0)

            reel.add(s)
            symbol_objs.append(s)

        reel_groups.append(reel)

    return reel_groups, symbol_objs


def onespin(gs, is_auto=False):

    # clear temp storage
    gs.show_datas.clear()
    slot_window_surface.fill(GS.Color.white)  # 畫面清空

    # math
    math_res = MM.freegame_spin_and_calculate()

    gs.show_score = math_res.score
    gs.arr_result = math_res.arr_result

    gs.rng = math_res.rng
    gs.paylines = math_res.paylines
    gs.trigger_times = math_res.trigger_cnt

    # append "show_datas"
    show_reels, symbol_objs = generate_objects(gs.arr_result, "base")  # 建立全部物件群組
    ori = dict(reel=show_reels, symbols=symbol_objs, type="base", score=gs.show_score, payline_text="")
    gs.show_datas.append(ori)

    for pl, txt in gs.paylines:
        show_reels, symbol_objs = generate_objects(gs.arr_result, "payline", show_line=pl)  # 建立全部物件群組
        gs.show_datas.append(dict(reel=show_reels, symbols=symbol_objs, type="payline", score=gs.show_score, payline_text=txt))

    if len(gs.paylines) > 0:
        ori = ori.copy()
        ori["type"] = "payline"
        gs.show_datas.append(ori)  # show use

    if is_auto:
        gs.show_datas.append(ori)  # show use

    gs.spins += 1
    if gs.show_score > 0:
        gs.hits += 1

    if gs.show_score > gs.max_score_one:
        gs.max_score_one = gs.show_score

    if gs.spin_cum == gs.free_spins:
        if gs.score_cum > gs.max_score:
            gs.max_score = gs.score_cum

    if gs.spin_cum < gs.free_spins:
        gs.score_cum += gs.show_score
        gs.spin_cum += 1
    else:
        gs.score_cum = gs.show_score
        gs.spin_cum = 1
        gs.free_spins = nrd.choice([5, 6, 7, 8, 9], p=MM.spins_prob)

    gs.trigger_cum += gs.trigger_times

    gs.cnt_reel_wait = 0
    gs.show_now = gs.show_datas.pop(0)

    return None


#%% --- intial ---


# [layout] (畫面相關定)
# - game title setting
pg.init()
pg.display.set_caption(GS.domo_name + " (Free Game)")

screen_icon = pg.image.load(GS.path_icon)
pg.display.set_icon(screen_icon)


# - surface setting
slot_window_surface = pg.display.set_mode(layout_status.layout_size)  # symbol / 1層
slot_window_surface.fill(GS.Color.white)
event_surface = pg.display.set_mode(layout_status.layout_size)  # 事件 / 2層(最上層)
event_surface.fill(GS.Color.white)


# - mask setting

masks = pg.sprite.Group()

mask1 = Button("", mask1_area.posi, mask1_area.size, GS.Color.white, is_info=True)
masks.add(mask1)

mask2 = Button("", mask2_area.posi, mask2_area.size, GS.Color.white, is_info=True)
masks.add(mask2)

masks.draw(event_surface)


# - button setting
btns = pg.sprite.Group()

round_btn = Button("", round_area.posi, round_area.size, GS.Color.gray)
btns.add(round_btn)

payline_btn = Button("", payline_area.posi, payline_area.size, GS.Color.gray)
btns.add(payline_btn)

score_btn = Button("score: 0", spinscore_area.posi, spinscore_area.size, GS.Color.gray)
btns.add(score_btn)

autospin_btn = Button("auto spin", autospin_area.posi, autospin_area.size, GS.Color.gray, click_text="inf")
btns.add(autospin_btn)

spin_btn = Button("spin", spin_area.posi, spin_area.size, GS.Color.gray)
btns.add(spin_btn)

info1_btn = Button("1", info1_area.posi, info1_area.size, GS.Color.white, text_color=GS.Color.black, is_info=True)
btns.add(info1_btn)

info2_btn = Button("2", info2_area.posi, info2_area.size, GS.Color.white, text_color=GS.Color.black, is_info=True)
btns.add(info2_btn)

info3_btn = Button("3", info3_area.posi, info3_area.size, GS.Color.white, text_color=GS.Color.black, is_info=True)
btns.add(info3_btn)

info4_btn = Button("4", info4_area.posi, info4_area.size, GS.Color.white, text_color=GS.Color.black, is_info=True)
btns.add(info4_btn)

btns.draw(event_surface)


# [data setting] (遊戲資料設定)
gs = GameStatus()


# [object setting] (初始盤面)
show_reels, symbol_objs = generate_objects(zeros(MM.arr_shape), "payline")  # 建立初始物件群組(假的盤面)
gs.show_datas = [dict(reel=show_reels, symbols=symbol_objs, type="payline", score=0, payline_text="game start")]


pg.display.update()  # 初始畫面刷新


# [main]
gs.show_now = gs.show_datas.pop(0)
while gs.flag:

    # [preset 預設]
    pg.time.Clock().tick(GS.reel_speed)  # 數字越大，動越快

    # [status 狀態紀錄] :
    gs.flag_rolling = False
    for i in gs.show_now["symbols"]:
        if i.limit != i.dy:
            gs.flag_rolling = True
            break

    # [update 資料刷新]
    if gs.flag_rolling == False and len(gs.show_datas) > 0:
        if gs.cnt_spin_and_spin_wait < GS.spin_and_spin_wait:
            gs.cnt_spin_and_spin_wait += 1
        else:
            gs.cnt_spin_and_spin_wait = 0
            gs.cnt_reel_wait = 0
            gs.show_now = gs.show_datas.pop(0)

    # [layout 畫面相關]

    # -- game info
    _show_hit_rate = gs.hits / gs.spins if gs.spins > 0 else 0
    _show_trigger_period = int(gs.spins / gs.trigger_cum) if gs.trigger_cum > 0 else "inf"

    score_btn.update_text(f"score: {gs.show_now['score']} / total: {gs.score_cum}")
    payline_btn.update_text(gs.show_now["payline_text"])
    round_btn.update_text(f"free game ({gs.spin_cum}/{gs.free_spins})")
    info1_btn.update_text(f"hit rate: {_show_hit_rate:0.2f}  ( hits: {gs.hits} / spins: {gs.spins} )")
    info2_btn.update_text(f"max score: {gs.max_score_one} / {gs.max_score}")
    info3_btn.update_text(f"free game trigger: {gs.trigger_cum} ( period: {_show_trigger_period} )")
    info4_btn.update_text(f"rng: {gs.rng}")

    # -- reel wait (滾動間隔設定)
    if gs.show_now["type"] == "payline":
        gs.threshold_reel_roll_delay = [0 for i in range(MM.reel_num)]  # reel 間滾動延遲
    else:
        gs.threshold_reel_roll_delay = [i * GS.reel_wait for i in range(MM.reel_num)]  # reel 間滾動延遲

    # -- update move (滾動)
    slot_window_surface.fill(GS.Color.white)  # 畫面清空
    for i in range(len(gs.show_now["reel"])):
        if gs.cnt_reel_wait < gs.threshold_reel_roll_delay[i]:
            reel.draw(slot_window_surface)
        else:
            reel = gs.show_now["reel"][i]
            reel.draw(slot_window_surface)
            reel.update()

    # -- auto spin (自動)
    if autospin_btn.on and len(gs.show_datas) == 0:
        onespin(gs, True)

    # -- update layout
    masks.draw(event_surface)
    btns.draw(event_surface)
    pg.display.update()

    # -- update
    gs.cnt_reel_wait += 1

    # [event 事件]
    for event in pg.event.get():
        if event.type == QUIT:  # 當使用者結束視窗，程式也結束
            gs.flag = False
            pg.quit()

        if event.type == pg.MOUSEBUTTONDOWN:
            if spin_btn.rect.collidepoint(event.pos):
                onespin(gs)

            if autospin_btn.rect.collidepoint(event.pos):

                # update slot window
                autospin_btn.click()


print("game close.")

