# %% --- import ---


import os
import numpy as np

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


# layout
class AreaObject:
    def __init__(self, area_w, h=GS_fsh, scale=(1, 1, 1)):
        """
        Parameters
        ---
        scale -> (int, int, int)
            [0]占幾份, [1]分幾份, [2]空格數

        """
        #
        _w = area_w - GS_sw * (scale[2] + 1)
        _w = _w / scale[1] * scale[0]

        #
        self.x = 0
        self.y = 0
        self.w = _w
        self.h = h
        self.area_w = area_w

        # mix
        self.size = (self.w, self.h)

    def set_posi(self, x=GS_sw, y=GS_sw):
        self.x = x
        self.y = y
        self.posi = (self.x, self.y)

        return self.h + GS_sw


# - initial
layout_w = symbol_w * MM.reel_num + GS_sw * (MM.reel_num + 1)
layout_h = 0

# - setting
_banner_area = AreaObject(layout_w)  # banner (main)
layout_h += _banner_area.set_posi()

round_area = AreaObject(layout_w, scale=(1, 3, 2))  # banner
round_area.set_posi(y=_banner_area.y)

payline_area = AreaObject(layout_w, scale=(2, 3, 2))  # banner
payline_area.set_posi(x=round_area.w + 2 * GS_sw, y=_banner_area.y)

symbol_area = AreaObject(area_w=layout_w, h=symbol_h * MM.window_size + GS_sw * (MM.window_size - 1))  # symbol
layout_h += symbol_area.set_posi(y=layout_h)

_btn_area = AreaObject(layout_w)  # btn (main)
layout_h += _btn_area.set_posi(y=layout_h + GS_sw)

spinscore_area = AreaObject(layout_w, scale=(2, 4, 3))  # btn
spinscore_area.set_posi(y=_btn_area.y)

autospin_area = AreaObject(layout_w, scale=(1, 4, 3))  # btn
autospin_area.set_posi(x=spinscore_area.w + 2 * GS_sw, y=_btn_area.y)

spin_area = AreaObject(layout_w, scale=(1, 4, 3))  # btn
spin_area.set_posi(x=spinscore_area.w + autospin_area.w + 3 * GS_sw, y=_btn_area.y)

info1_area = AreaObject(layout_w)  # info
layout_h += info1_area.set_posi(y=layout_h + GS_sw)

info2_area = AreaObject(layout_w)  # info
layout_h += info2_area.set_posi(y=layout_h)

info3_area = AreaObject(layout_w)  # info
layout_h += info3_area.set_posi(y=layout_h - GS_sw)

info4_area = AreaObject(layout_w)  # info
layout_h += info4_area.set_posi(y=layout_h - 2 * GS_sw)

info5_area = AreaObject(layout_w)  # info
layout_h += info5_area.set_posi(y=layout_h - 3 * GS_sw)

info6_area = AreaObject(layout_w)  # info
layout_h += info6_area.set_posi(y=layout_h - 4 * GS_sw)

layout_size = (layout_w, layout_h - 30)  # 微調(by project)


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
        self.spins = 0
        self.hits = 0
        self.spin_cum = 0
        self.max_score_one = 0
        self.max_score = 0
        self.score_cum = 0

        self.wukong3_cnt = 0

        self.respin_cnt = 0
        self.respin1_cnt = 0
        self.respin2_cnt = 0
        self.respin3_cnt = 0

        self.trigger_cum = 0
        self.trigger3_cum = 0
        self.trigger4_cum = 0
        self.trigger5_cum = 0

        # self.spin_and_calc_result = []

        # math output
        self.show_score = 0
        self.arr_result = None
        self.rng = "--"
        self.paylines = []
        self.trigger_times = 0

        # Data
        self.show_datas = []
        self.show_now = None


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
            _sw = GS_sw * (j + 1) + j * symbol_w
            _sh = GS_fsh + GS_sw * 2 + i * (symbol_h + GS_sw)
            if show_type == "base":
                s = Symbol(5, _sw, _sh - GS.symbol_move_limit, img)
            elif show_type == "payline":
                s = Symbol(5, _sw, _sh, img, shadow=show_line[i, j] == 0, limit=0)
            elif show_type == "respin":
                if respin_posi[j] == 0:  # move reel
                    s = Symbol(5, _sw, _sh - GS.symbol_move_limit, img)
                else:  # stick reel
                    s = Symbol(5, _sw, _sh, img, limit=0)
            else:
                s = Symbol(5, -999, -999, img, limit=0)

            reel.add(s)
            symbol_objs.append(s)

        reel_groups.append(reel)

    return reel_groups, symbol_objs


def onespin(gs, is_auto=False):

    # clear temp storage
    gs.show_datas.clear()
    slot_window_surface.fill(GS.Color.white)  # 畫面清空

    # math
    math_results = MM.freegame_spin_and_calculate()

    level = 0
    wild_position = np.array([0, 0, 0, 0, 0])
    for math_res in math_results:

        #
        gs.show_score = math_res.score
        gs.arr_result = math_res.arr_result

        gs.rng = math_res.rng
        gs.paylines = math_res.paylines
        gs.trigger_times = math_res.trigger_cnt

        gs.new_wild_posi = math_res.respin_posi
        gs.respin_show_arr = math_res.respin_show_arr

        # append "show_datas"
        if level == 0:
            show_type = "base"
            show_arr = gs.arr_result
        else:
            show_type = "respin"
            show_arr = gs.respin_show_arr

        #
        show_reels, symbol_objs = generate_objects(show_arr, show_type, respin_posi=gs.new_wild_posi)  # 建立全部物件群組
        base1_d = dict(reel=show_reels, symbols=symbol_objs, type=show_type, score=gs.show_score)
        base2_d = dict(reel=show_reels, symbols=symbol_objs, type="payline", score=gs.show_score)
        gs.show_datas.append(base1_d)

        for pl in gs.paylines:
            show_reels, symbol_objs = generate_objects(show_arr, "payline", show_line=pl)  # 建立全部物件群組
            payline_d = dict(reel=show_reels, symbols=symbol_objs, type="payline", score=gs.show_score)
            gs.show_datas.append(payline_d)

        if len(gs.paylines) > 0:
            gs.show_datas.append(base2_d)  # show use

        if is_auto:
            gs.show_datas.append(base2_d)  # show use

        level += 1
        wild_position += gs.new_wild_posi

        if (len(show_arr[show_arr == MM.wild]) + len(show_arr[show_arr == MM.wild2])) == 3:
            gs.wukong3_cnt += 1

        if len(show_arr[show_arr == MM.scatter]) >= 3:
            gs.trigger_cum += 1

        if len(show_arr[show_arr == MM.scatter]) == 3:
            gs.trigger3_cum += 1
        elif len(show_arr[show_arr == MM.scatter]) == 4:
            gs.trigger4_cum += 1
        elif len(show_arr[show_arr == MM.scatter]) == 5:
            gs.trigger5_cum += 1

    # [update] info
    gs.spins += 1
    if gs.show_score > 0:
        gs.hits += 1

    if gs.show_score > gs.max_score_one:
        gs.max_score_one = gs.show_score

    if gs.spin_cum == MM.free_spins:
        if gs.score_cum > gs.max_score:
            gs.max_score = gs.score_cum

    if gs.spin_cum < MM.free_spins:
        gs.score_cum += gs.show_score
        gs.spin_cum += 1
    else:
        gs.score_cum = gs.show_score
        gs.spin_cum = 1

    gs.trigger_cum += gs.trigger_times

    if level > 1:
        gs.respin_cnt += 1

    if level == 2:
        gs.respin1_cnt += 1
    elif level == 3:
        gs.respin2_cnt += 1
    elif level == 4:
        gs.respin3_cnt += 1

    # [update] data
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
slot_window_surface = pg.display.set_mode(layout_size)  # symbol / 1層
slot_window_surface.fill(GS.Color.white)
event_surface = pg.display.set_mode(layout_size)  # 事件 / 2層(最上層)
event_surface.fill(GS.Color.white)


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

info5_btn = Button("5", info5_area.posi, info5_area.size, GS.Color.white, text_color=GS.Color.black, is_info=True)
btns.add(info5_btn)

info6_btn = Button("6", info6_area.posi, info6_area.size, GS.Color.white, text_color=GS.Color.black, is_info=True)
btns.add(info6_btn)

btns.draw(event_surface)

#%%
# [data setting] (遊戲資料設定)
gs = GameStatus()


# [object setting] (初始盤面)
show_reels, symbol_objs = generate_objects(np.zeros(MM.arr_shape), "payline")  # 建立初始物件群組(假的盤面)
gs.show_datas = [dict(reel=show_reels, symbols=symbol_objs, type="payline", score=0)]


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
    _show_respin_period = int(gs.spins / gs.respin_cnt) if gs.respin_cnt > 0 else "inf"
    _show_wukong3_period = int(gs.spins / gs.wukong3_cnt) if gs.wukong3_cnt > 0 else "inf"

    score_btn.update_text(f"score: {gs.show_now['score']} / total: {gs.score_cum}")
    round_btn.update_text(f"free game ({gs.spin_cum}/{MM.free_spins})")
    info1_btn.update_text(f"hit rate: {_show_hit_rate:0.2f}  ( hits: {gs.hits} / spins: {gs.spins} )")
    info2_btn.update_text(f"max score: {gs.max_score_one} / {gs.max_score}")
    info3_btn.update_text(
        f"free game re-trigger: {gs.trigger_cum} ( {gs.trigger3_cum} / {gs.trigger4_cum} / {gs.trigger5_cum} ) ( period: {_show_trigger_period} )"
    )
    info4_btn.update_text(f"re-spin: {gs.respin_cnt} ( {gs.respin1_cnt} / {gs.respin2_cnt} / {gs.respin3_cnt} ) ( period: {_show_respin_period} )")
    info5_btn.update_text(f"wukong*3: {gs.wukong3_cnt} ( period: {_show_wukong3_period} )")
    info6_btn.update_text(f"rng: {gs.rng}")

    # -- reel wait (滾動間隔設定)
    if gs.show_now["type"] in ["payline", "respin"]:
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

