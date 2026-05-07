# %% --- import ---
if True:
    import os

    from numpy import zeros, array, full

    import pygame as pg
    from pygame.locals import QUIT

    import GameSetting as GS
    from GameSetting import layout_spacing_width as GS_sw
    from GameSetting import function_space_height as GS_fsh
    from GameSetting import GAME_TYPE as GT

    import Math as MM


# %% --- pre-setting ---
if True:
    # img name list
    symbol_names = os.listdir(GS.path_symbol_img)
    symbol_names.sort()

    # symbol
    _img = pg.image.load(GS.path_symbol_img + "/" + symbol_names[0])
    symbol_w = _img.get_width() * GS.symbol_adj_size  # (w, h)
    symbol_h = _img.get_height() * GS.symbol_adj_size
    symbol_size = (symbol_w, symbol_h)

    # symbol pre-load
    symbol_imgs = dict()
    for symbol_name in symbol_names:
        symbol_id = int(symbol_name.split("_")[0])
        img = pg.image.load(GS.path_symbol_img + "/" + symbol_name)
        img = pg.transform.smoothscale(img, symbol_size)
        symbol_imgs[symbol_id] = img
        # img = pg.transform.scale(img, symbol_size)


# %% --- area---
if True:

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
            self.layout_h -= GS_sw
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
        x = symbol_area.x  # banner area
        y = 0
        w = symbol_area.w
        h = symbol_area.y
        mask1 = ObjElement(x, y, w, h, "mask")

        x = symbol_area.x  # btn and info area
        y = symbol_area.y + symbol_area.h
        w = symbol_area.w
        h = layout_status.layout_h - (symbol_area.y + symbol_area.h)
        mask2 = ObjElement(x, y, w, h, "mask")

        return [mask1, mask2]

    layout_status = LayoutStatus()
    layout_status.layout_w = symbol_w * MM.reel_num_bg + GS_sw * (MM.reel_num_bg + 1)

    f = lambda h, div, div_type: generate_obj_area(layout_status, (layout_status.layout_w - GS_sw * 2, h), div, div_type)

    # area
    round_area, payline_area = f(GS_fsh, [2, 3], "base")

    symbol_area = f(symbol_h * MM.arr_shape_show[0] + GS_sw * (MM.arr_shape_show[0] - 1), [1], "base")[0]
    spinscore_area, autospin_area, spin_area = f(GS_fsh, [2, 1, 1], "base")

    trigger_freegame_area, info1_area, info2_area, info3_area, info4_area, info5_area = f(GS_fsh * 6 + GS_sw * 5, [1, 1, 1, 1, 1, 1], "no_sw")

    # mask
    mask1_area, mask2_area = get_mask(layout_status, symbol_area)

    # final
    layout_status.end_setting()


# %% --- object---
if True:

    class Symbol(pg.sprite.Sprite):
        dx = 0
        dy = 0
        x = 0  # x坐標
        y = 0  # y坐標
        speed = 0  # 移動速度
        limit = 0

        def __init__(self, sp, sx, sy, simg, limit=GS.symbol_move_limit, shadow_value=GS.alpha_max):
            # intial setting
            pg.sprite.Sprite.__init__(self)
            self.speed = sp
            self.x = sx
            self.y = sy
            self.limit = limit

            # symbol setting
            self.image = simg.copy()
            self.image.set_alpha(shadow_value)
            self.rect = self.image.get_rect()  # 取得object區域
            self.rect.topleft = (sx, sy)  # 初始位置

        # 移動
        def update(self, event_type=1):
            if self.dy >= self.limit:
                return False

            if event_type == 0:
                # 計算新坐標
                self.y += self.speed
                self.dy += self.speed

                # 移動圖形
                # self.rect.x = self.x
                self.rect.y = self.y

            elif event_type == 1:
                self.dy = self.limit

    class Button(pg.sprite.Sprite):
        on = False
        lock_ = False

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
            self._color_set(self.background_color)

            # font
            self._font_set(self.show_text)

        def _color_set(self, color):
            self.image = pg.Surface(self.size)  # object 'width', 'height'
            self.image.fill(color)
            self.rect = self.image.get_rect()
            self.rect.topleft = self.position  # 初始位置

        def _font_set(self, text):
            self.font = pg.font.SysFont(GS.text_font, GS.text_size)
            self.text = self.font.render(text, True, self.text_color)
            if self.is_info:
                self.text_center = self.text.get_rect(midleft=(10, self.rect.h / 2))
            else:
                self.text_center = self.text.get_rect(center=(self.rect.w / 2, self.rect.h / 2))

            self.image.blit(self.text, self.text_center)

        def click(self):
            if self.click_text == "":
                return

            if self.lock_:
                return

            self.on = self.on == False

            # img setting
            self._color_set(self.background_color)

            # font
            text = self.show_text if self.on == False else self.click_text
            self._font_set(text)

        def update_btn(self, text, color=GS.Color.gray):
            if self.is_info == True:
                self._color_set(self.background_color)
            else:
                self._color_set(color)

            self._font_set(text)

        def lock_btn(self):

            # img setting
            self._color_set(self.background_color)

            # font
            self._font_set("-")

            #
            self.on = False
            self.lock_ = True

    class GameStatus:
        def __init__(self) -> None:
            # [畫面]
            # - layout setting
            self.threshold_reel_roll_delay = [i * GS.wait_reel for i in range(MM.reel_num_bg)]  # reel 間滾動延遲

            self.cnt_reel_wait = 0
            self.cnt_auto_wait = 0
            self.cnt_spin_and_spin_wait = 0

            self.flag = True  # game control (遊戲停止終止迴圈)
            self.flag_rolling = False
            self.flag_spin_btn_click = False

            self.game_cnt = 0

            # [遊戲]

            # - math (暫存)
            self.math_sts = MM.MathStatus()  # 部分變數每呼叫一次"Math"刷新一次

            # - game data
            self.show_datas = []  # type: ignore # type: [ShowData]
            self.show_now = None  # type: ShowData
            self.show_forever = None  # type: ShowData

            self.no_credit = False  # 還有沒有錢
            self.lock_spin = False  # spin間的間格時間

    class ShowData:
        def __init__(self, reel, symbols, type, score, payline_text="") -> None:
            self.reel = reel
            self.symbols = symbols
            self.type = type
            self.score = score
            self.payline_text = payline_text

    def generate_objects(show_arr, show_type, show_posi=zeros(MM.arr_shape_show)):
        # output
        reel_groups = []
        symbol_objs = []

        # symbol_area
        arr_shape = show_arr.shape
        for j in range(arr_shape[1]):  # 5 (reel num)
            reel = pg.sprite.Group()
            for i in range(arr_shape[0]):  # 3 (window size)
                symbol_id = int(abs(show_arr[i, j]))

                # get img object
                img = symbol_imgs[symbol_id]
                # create symbol objectS
                _sw = symbol_area.x + j * (GS_sw + symbol_w)
                _sh = symbol_area.y + i * (GS_sw + symbol_h)

                if show_type == "base":
                    s = Symbol(GS.move_unit, _sw, _sh - GS.symbol_move_limit, img, limit=GS.symbol_move_limit)
                elif show_type in ("payline", "last"):
                    shadow_value = GS.alpha_payline if show_posi[i, j] == 0 else GS.alpha_max
                    s = Symbol(GS.move_unit, _sw, _sh, img, shadow_value=shadow_value, limit=0)
                elif show_type == "sticky":
                    shadow_value = GS.alpha_0 if show_posi[i, j] == 0 else GS.alpha_100
                    s = Symbol(GS.move_unit, _sw, _sh, img, shadow_value=shadow_value, limit=0)
                else:
                    s = Symbol(GS.move_unit, -999, -999, img, limit=0)

                reel.add(s)
                symbol_objs.append(s)

            reel_groups.append(reel)

        return reel_groups, symbol_objs

    def one_spin(gs, is_auto=False, is_freegame=False):
        """
        更新"GameStatus"(gs)的資料。
        註解: 這邊的資料是遊戲表演會用到的資料。
        """

        # [清除暫存]
        gs.show_datas.clear()
        reel_surface.fill(GS.Color.white)  # 畫面清空

        # [one spin] 數學資料
        gs.math_sts.one_spin(is_freegame)

        # [append] append "show_datas"
        # # - 設定sticky在reel上的物件
        # show_reels, symbol_objs = generate_objects(gs.math_sts.arr_sticky_symbol, "sticky", show_posi=gs.math_sts.arr_sticky_posi)  # 建立全部物件群組
        # stk = ShowData(show_reels, symbol_objs, "sticky", gs.math_sts.math_res.show_score)
        # gs.show_datas.append(stk)

        # - 設定reel上的物件
        show_reels, symbol_objs = generate_objects(gs.math_sts.math_res.arr_result, "base")
        ori = ShowData(show_reels, symbol_objs, "base", gs.math_sts.math_res.show_score)
        ori_last = ShowData(show_reels, symbol_objs, "last", gs.math_sts.math_res.show_score)
        gs.show_datas.append(ori)

        # - 設定閃爍
        # --- 設定mystery
        show_reels, symbol_objs = generate_objects(gs.math_sts.math_res.arr_result_2, "payline", show_posi=full(gs.math_sts.math_res.arr_result_2.shape, 1))
        ori = ShowData(show_reels, symbol_objs, "payline", gs.math_sts.math_res.show_score)
        ori_last = ShowData(show_reels, symbol_objs, "last", gs.math_sts.math_res.show_score)
        gs.show_datas.append(ori)

        # --- 設定payline
        for pl, txt in gs.math_sts.math_res.pay_lines:
            show_reels, symbol_objs = generate_objects(gs.math_sts.math_res.arr_result_2, "payline", show_posi=pl)
            gs.show_datas.append(ShowData(show_reels, symbol_objs, "payline", gs.math_sts.math_res.show_score, payline_text=txt))

        if len(gs.math_sts.math_res.pay_lines) > 0 or is_auto:
            gs.show_datas.append(ori_last)  # show use

        # [pop] pop "show_datas"
        gs.cnt_reel_wait = 0
        show_data = gs.show_datas.pop(0)
        if show_data.type == "sticky":
            gs.show_forever = show_data
            gs.show_now = gs.show_datas.pop(0)
        else:
            gs.show_now = show_data


# %% --- intial ---
if True:
    # [layout] (畫面相關定)
    # - game title setting
    pg.init()
    pg.display.set_caption(GS.domo_name + "")

    screen_icon = pg.image.load(GS.path_icon)
    pg.display.set_icon(screen_icon)

    # - surface setting
    reel_surface = pg.display.set_mode(layout_status.layout_size)  # symbol / 1層
    reel_surface.fill(GS.Color.white)

    event_surface = pg.display.set_mode(layout_status.layout_size)  # 事件 / 3層(最上層)
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

    autospin_btn = Button("auto", autospin_area.posi, autospin_area.size, GS.Color.gray, click_text="inf")
    btns.add(autospin_btn)

    spin_btn = Button("spin", spin_area.posi, spin_area.size, GS.Color.gray, click_text="stop")
    btns.add(spin_btn)

    trigger_freegame_btn = Button("free game", trigger_freegame_area.posi, trigger_freegame_area.size, GS.Color.gray, text_color=GS.Color.white, click_text="click")
    btns.add(trigger_freegame_btn)

    info1_btn = Button("--", info1_area.posi, info1_area.size, GS.Color.white, text_color=GS.Color.black, is_info=True)
    btns.add(info1_btn)

    info2_btn = Button("--", info2_area.posi, info2_area.size, GS.Color.white, text_color=GS.Color.black, is_info=True)
    btns.add(info2_btn)

    info3_btn = Button("--", info3_area.posi, info3_area.size, GS.Color.white, text_color=GS.Color.black, is_info=True)
    btns.add(info3_btn)

    info4_btn = Button("--", info4_area.posi, info4_area.size, GS.Color.white, text_color=GS.Color.black, is_info=True)
    btns.add(info4_btn)

    info5_btn = Button("--", info5_area.posi, info5_area.size, GS.Color.white, text_color=GS.Color.black, is_info=True)
    btns.add(info5_btn)

    btns.draw(event_surface)

    # [data setting] (遊戲資料設定)
    gs = GameStatus()

    # [物件設定] (初始盤面)
    show_reels, symbol_objs = generate_objects(zeros(MM.arr_shape_show), "payline")  # 建立初始物件群組(假的盤面)
    gs.show_datas = [ShowData(show_reels, symbol_objs, "payline", 0, payline_text="game start")]

    pg.display.update()  # 初始畫面刷新


# %% --- main ---
if True:

    def game_info_setting(game_setting):
        gs = game_setting

        _show_hit_rate = gs.math_sts.cnt_hits / gs.math_sts.cnt_spins if gs.math_sts.cnt_spins > 0 else 0
        _show_trigger_rate = int(gs.math_sts.cnt_spins / gs.math_sts.cnt_trigger_freegame_times) if gs.math_sts.cnt_trigger_freegame_times > 0 else "inf"

        if gs.math_sts.game_type in MM.game_scene[GT.BaseGame]:
            round_btn.update_btn(GS.format_bg_round_btn)
        else:
            round_btn.update_btn(f"free game ({gs.math_sts.cnt_free_spins}/{gs.math_sts.have_free_spins})", color=GS.Color.red)

        score_btn.update_btn(f"score: {gs.show_now.score} ( {gs.show_now.score/MM.pay_line:0.2f}X )")
        payline_btn.update_btn(gs.show_now.payline_text)

        info1_btn.update_btn(f"coin: {gs.math_sts.credit} ( +{gs.math_sts.freegame_coin} )")
        info2_btn.update_btn(f"hit rate: {_show_hit_rate:0.2f}  ( hits: {gs.math_sts.cnt_hits} / spins: {gs.math_sts.cnt_spins} )")
        info3_btn.update_btn(f"max score: {gs.math_sts.max_score_basegame} / {gs.math_sts.max_score_freegame}")
        info4_btn.update_btn(f"free game trigger: {gs.math_sts.cnt_trigger_freegame_times} ( period: {_show_trigger_rate} )")
        info5_btn.update_btn(f"rng: {gs.math_sts.math_res.rng} {gs.math_sts.game_type}")

    def init_cnt(game_setting):
        game_setting.game_cnt = 0
        return game_setting.game_cnt <= 10

    gs.show_now = gs.show_datas.pop(0)
    while gs.flag:
        # [預設/初始狀態]
        pg.time.Clock().tick(GS.speed_reel)  # 數字越大，動越快

        gs.lock_spin = gs.game_cnt <= GS.wait_update  # 設定把把間延遲的時間間隔
        gs.no_credit = gs.math_sts.credit <= MM.coin_in  # 表底還有沒有錢

        # [狀態紀錄]
        gs.flag_rolling = False
        for i in gs.show_now.symbols:
            if i.limit != i.dy:
                gs.flag_rolling = True
                break

        # [update]
        if gs.flag_rolling == False and len(gs.show_datas) > 0:
            if gs.cnt_spin_and_spin_wait < GS.wait_spin_and_spin:
                gs.cnt_spin_and_spin_wait += 1
            else:
                gs.cnt_spin_and_spin_wait = 0
                gs.cnt_reel_wait = 0
                gs.show_now = gs.show_datas.pop(0)

        # [遊戲資訊]
        game_info_setting(gs)

        # [畫面相關]
        masks.draw(event_surface)
        btns.draw(event_surface)

        # - reel wait (滾動間隔設定)
        if gs.show_now.type in ("payline", "last"):
            gs.threshold_reel_roll_delay = [0 for i in range(MM.reel_num_bg)]  # reel 間滾動延遲
        else:
            gs.threshold_reel_roll_delay = [i * GS.wait_reel for i in range(MM.reel_num_bg)]  # reel 間滾動延遲
            # gs.threshold_reel_roll_delay = [i * GS.wait_reel for i in [0, 0, 1, 2, 2]]  # reel 間滾動延遲

        # - update reel move (滾動)
        reel_surface.fill(GS.Color.white)  # 畫面清空
        for i in range(len(gs.show_now.reel)):
            if gs.cnt_reel_wait < gs.threshold_reel_roll_delay[i]:
                reel.draw(reel_surface)
            else:
                reel = gs.show_now.reel[i]
                reel.update(0)
            reel.draw(reel_surface)

        # - update sticky object
        if gs.show_forever != None:
            for i in range(len(gs.show_forever.reel)):
                reel = gs.show_forever.reel[i]
            reel.draw(reel_surface)

        # - auto spin (自動)
        if autospin_btn.on and len(gs.show_datas) == 0 and gs.lock_spin == False:
            one_spin(gs, is_auto=True)

        # - trigger free game (免費遊戲)
        if trigger_freegame_btn.on and len(gs.show_datas) == 0 and gs.math_sts.math_res.trigger_freespins == 0:
            one_spin(gs, is_freegame=True)

        # - spin結束後還原spin_btn狀態
        if spin_btn.on and gs.flag_rolling == False:
            spin_btn.on = False
            spin_btn.update_btn(spin_btn.show_text)

        # - 還原trigger_freegame_btn狀態
        if trigger_freegame_btn.on and gs.math_sts.game_type != 0:
            trigger_freegame_btn.on = False
            trigger_freegame_btn.update_btn(trigger_freegame_btn.show_text)

        # - update
        gs.cnt_reel_wait += 1
        gs.game_cnt += 1
        if gs.game_cnt >= 999:
            gs.game_cnt = 0

        # - update button (更新按鈕如果沒錢)
        if gs.no_credit:
            autospin_btn.lock_btn()
            spin_btn.lock_btn()
            trigger_freegame_btn.lock_btn()

        # - update layout (更新畫面)
        masks.draw(event_surface)
        btns.draw(event_surface)
        pg.display.update()

        # [事件]
        for event in pg.event.get():
            if event.type == QUIT:  # 當使用者結束視窗，程式也結束
                gs.flag = False

            keys = pg.key.get_pressed()
            mouse_type = event.type == pg.MOUSEBUTTONDOWN

            # escape
            if keys[pg.K_ESCAPE]:
                gs.flag = False

            # spin
            is_spin_click = mouse_type and spin_btn.rect.collidepoint(event.pos)
            is_space_click = keys[pg.K_SPACE]
            if (is_spin_click or is_space_click) and gs.lock_spin == False and autospin_btn.on == False and not gs.no_credit:
                gs.lock_spin = init_cnt(gs)
                spin_btn.click()
                if spin_btn.on:
                    one_spin(gs)
                else:
                    for i in range(len(gs.show_now.reel)):
                        reel = gs.show_now.reel[i]
                        reel.update(1)
                    reel.draw(reel_surface)

            if gs.no_credit and autospin_btn.on:
                autospin_btn.click()

            # auto spin
            is_auto_spin_click = mouse_type and autospin_btn.rect.collidepoint(event.pos)
            is_a_click = keys[pg.K_a]
            if (is_auto_spin_click or is_a_click) and gs.lock_spin == False and not gs.no_credit:
                gs.lock_spin = init_cnt(gs)
                autospin_btn.click()

            # trigger free game
            is_trigger_freegame_click = mouse_type and trigger_freegame_btn.rect.collidepoint(event.pos)
            if is_trigger_freegame_click and gs.lock_spin == False and gs.math_sts.game_type in MM.game_scene[GT.BaseGame] and trigger_freegame_btn.on == False:
                gs.lock_spin = init_cnt(gs)
                trigger_freegame_btn.click()

    pg.quit()

    print("game close.")
