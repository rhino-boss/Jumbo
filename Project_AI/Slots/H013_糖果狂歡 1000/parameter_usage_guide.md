# H013 數學模型參數使用說明

## 範圍

本文件說明：

* `H013` 數學模型參數目前如何被 `H013_Box.py` 載入
* `H013_Simulator.py` 如何實際使用這些參數
* 如果你要另外建立一支新程式，應該怎麼直接重用現有參數，而不是重抄一份

本文件以目前可執行的程式行為為主，優先順序如下：

1. `H013_Simulator.py`
2. `Source\\H013_Box.py`
3. `H013_糖果狂歡` 資料夾中的歷史 xlsx / Help

---

## 1. 整體流程

目前 H013 的參數流向是：

1. `H013_Box.py` 內定義 `path_math`，並從數學 xlsx 讀取各工作表
2. `H013_Box.py` 把這些資料整理成程式可直接使用的常數、陣列、累積權重
3. `H013_Simulator.py` import `Project.Slots.Source.H013_Box as Box`
4. simulator 只透過 `Box.xxx` 取值，不再自己解析 xlsx

也就是說：

* runtime 的參數入口是 `H013_Box.py`
* 新程式若要和 simulator 保持一致，**應直接 import `H013_Box.py`**
* 不建議在新程式再手刻一次 xlsx 讀取邏輯，否則很容易和現行模型脫鉤

---

## 2. `H013_Box.py` 做了什麼

`H013_Box.py` 主要分成五類工作。

### 2.1 基本模式與場景常數

這一層提供：

* 下注模式：`mode_narmalbet`、`mode_extrabet`、`mode_featurebuy`、`mode_superfeaturebuy`
* 場景：`scence_BG`、`scence_FG`
* 盤面大小：`window_size`、`reel_num`
* 下注倍率：`normalbet`、`extrabet`、`featurebuy`、`superfeaturebuy`
* FG 控制：`extra_spin_low`、`extra_spin_high`、`max_spin_free_game`

這些常數通常會決定新程式的流程骨架。

### 2.2 符號與賠率資料

這一層提供：

* `pay_table`
* `symbol_str`
* `symbol_id`
* `symbols_special`
* `symbols_main`
* `symbols_number`
* `symbols_score`
* `symbols_all`
* `pay_table_C1`
* `pay_table_C1_reteigger`
* `pay_table_awards_cascading`

這些資料會影響：

* 哪些符號可算一般獎
* Scatter 在幾顆時有獎
* 一般符號在 `8-9 / 10-11 / 12+` 時給多少分

### 2.3 輪帶資料

這一層提供：

* `arr_reels`
* `reels_len`
* 各模式對應的 strip index：
  * `strip_BG ~ strip_BG4`
  * `strip_EB ~ strip_EB3`
  * `strip_FG / strip_FG2`
  * `strip_FB / strip_FB2`
  * `strip_SB / strip_SB2`

這些資料會影響：

* 初始盤面怎麼生成
* 各下注模式要用哪組 reel
* FG 高表 / 低表要切哪一張 strip

### 2.4 Reel Weight / Table Weight

這一層提供：

* `arr_reels_weight`
* `weight_table_normal_bet`
* `weight_cum_table_normal_bet`
* `weight_table_extra_bet`
* `weight_cum_table_extra_bet`

這些資料會影響：

* BG / EB 一開始選哪張表
* 各 reel stop index 的抽樣權重

### 2.5 倍數相關資料

這一層提供：

* `value_multiplier`
* `weight_table_multiplier_range_FG_low`
* `weight_cum_table_multiplier_range_FG_low`
* `weight_table_multiplier_range_FG_high`
* `weight_cum_table_multiplier_range_FG_high`
* `weight_table_multiplier_range_FB_low`
* `weight_cum_table_multiplier_range_FB_low`
* `weight_table_multiplier_range_FB_high`
* `weight_cum_table_multiplier_range_FB_high`
* `weight_table_multiplier_range_SB_low`
* `weight_cum_table_multiplier_range_SB_low`
* `weight_table_multiplier_range_SB_high`
* `weight_cum_table_multiplier_range_SB_high`

這些資料會影響：

* `C2 / Multiplier` 能抽到哪些倍數
* 不同 FG / Buy 場景應採用哪組倍率權重

---

## 3. `H013_Simulator.py` 怎麼使用這些參數

### 3.1 下注模式與 `coin_in`

`H013_Simulator.py` 一開始先依 `bet_mode` 決定 `coin_in`：

* `Normal Bet`：`default_coin_in * normalbet`
* `Extra Bet`：`default_coin_in * extrabet`
* `Feature Buy`：`default_coin_in * normalbet * featurebuy`
* `Super Feature Buy`：`default_coin_in * normalbet * superfeaturebuy`

如果你的新程式要輸出 RTP、倍率、成本比較，必須沿用同樣的 `coin_in` 算法，否則結果會錯。

### 3.2 模式切表

simulator 會先依 `bet_mode` 決定要用哪組 strip：

* BG：`strip_BG / BG2 / BG3`
* EB：`strip_EB / EB2 / EB3`
* FG：`strip_FG / strip_FG2`
* FB：`strip_FB / strip_FB2`
* SB：`strip_SB / strip_SB2`

另外：

* `Normal Bet` / `Feature Buy` / `Super Feature Buy` 的 BG 選表權重目前都吃 `weight_table_normal_bet`
* `Extra Bet` 另外吃 `weight_table_extra_bet`

### 3.3 盤面生成

`arr_result_generator()` 的核心流程是：

1. 先用 `arr_reels_weight` 抽每個 reel 的 stop index
2. 再用 `arr_reels` + `reels_len` 把 stop index 展開成可見盤面

也就是說：

* `arr_reels` 決定 reel 內容與順序
* `arr_reels_weight` 決定每個 stop 被抽中的機率

如果你要做「單局展示器」、「盤面分析器」或「hit case 搜尋器」，這組函式邏輯必須照搬。

### 3.4 判獎

`calculate_win()` 的實際做法不是線型判獎，而是：

* 對 `Box.symbols_score` 中每種一般符號分開計數
* 直接統計該符號在整個盤面出現幾顆
* 依 `pay_table_awards_cascading` 決定落在 `8-9 / 10-11 / 12+` 哪個區間
* 去 `pay_table` 取分

`calculate_win_c1()` 則單獨處理 `C1 / Scatter`：

* Scatter 不看一般得分流程
* 要等整個 tumble 完成後，才統計最終盤面的 `C1` 數量

### 3.5 掉落與補牌

`remove_and_fall()` 的核心重點有兩個：

1. 得分符號會被整批移除
2. 補牌是沿用同一 reel 的後續順序往上補，不是另外抽獨立掉落池

另外目前程式有兩個限制：

* 某一 reel 若已經有 `C1`，補牌遇到下一顆 `C1` 會跳過
* 某一 reel 若已經有 `C2`，補牌遇到下一顆 `C2` 也會跳過

如果你做的是 replay / debug 工具，這一點要和 simulator 完全一致。

### 3.6 FG 與倍數

`free_game()` 裡的關鍵點如下：

* 初始 FG 場次目前在程式裡是硬寫為 `N_high = 2`、`N_low = 8`
* 高表 spins 會先跑完，再跑低表 spins
* 每一局 FG 都會先複製盤面到 `arr_result_FG_pre`
* 對 `arr_result_FG_pre` 先完整模擬一次 tumble，取最終盤面的 `C1 / C2`
* 用最終 `C1` 判斷是否 retrigger
* 用最終 `C2` 顆數逐顆抽倍數，最後加總成 `multi_cum`
* 再把這個 `multi_cum` 套用到該局實際計分流程

這代表：

* 倍數不是每次消除單獨算
* 倍數是該局 tumble 全部結束後，一次決定並套用到該局總得分

---

## 4. 新程式怎麼用這套參數

如果你要建立一個新程式，建議分三層。

### 4.1 第一層：直接 import `H013_Box.py`

最基本寫法是：

```python
import Project.Slots.Source.H013_Box as Box
```

然後只透過 `Box.xxx` 取值，例如：

```python
reel_num = Box.reel_num[Box.scence_BG]
window_size = Box.window_size[Box.scence_BG]
pay_table = Box.pay_table
symbols_score = Box.symbols_score
```

這樣做的好處是：

* 新程式自動沿用現有數學模型
* `H013_Box.py` 之後若有更新，新程式也能同步吃到

### 4.2 第二層：先決定你的程式用途

常見用途和建議直接使用的參數如下。

如果你要做「單局盤面展示」：

* `arr_reels`
* `arr_reels_weight`
* `reels_len`
* `symbol_str`

如果你要做「判獎工具」：

* `symbols_score`
* `pay_table`
* `pay_table_C1`
* `pay_table_awards_cascading`

如果你要做「FG 倍數分析」：

* `value_multiplier`
* `weight_cum_table_multiplier_range_FG_low`
* `weight_cum_table_multiplier_range_FG_high`
* `weight_cum_table_multiplier_range_FB_low`
* `weight_cum_table_multiplier_range_FB_high`
* `weight_cum_table_multiplier_range_SB_low`
* `weight_cum_table_multiplier_range_SB_high`

如果你要做「下注模式比較」：

* `normalbet`
* `extrabet`
* `featurebuy`
* `superfeaturebuy`
* `weight_cum_table_normal_bet`
* `weight_cum_table_extra_bet`

### 4.3 第三層：直接重用 simulator 的流程概念

新程式若要和目前模擬結果一致，建議沿用這個順序：

1. 先決定 `bet_mode`
2. 算 `coin_in`
3. 依 `bet_mode` 決定 strip 與 table weight
4. 生成初始盤面
5. 判斷一般得分
6. 移除得分符號並補牌
7. 沒有新得分後，再判 Scatter
8. 若進 FG，再依目前程式的高低表與倍數規則處理

不要反過來先用規格文件硬寫規則，再去猜參數在哪裡。這樣很容易和 runtime 脫節。

---

## 5. 範例：最小可用的新程式骨架

下面是一個適合新工具起步的最小骨架。

```python
import math
import numpy as np
import Project.Slots.Source.H013_Box as Box


def get_value(cum_weight):
    rd = math.ceil(np.random.random() * cum_weight[-1]) - 1
    for i, v in enumerate(cum_weight):
        if rd < v:
            return i
    return len(cum_weight) - 1


def build_board(table_id):
    rows = Box.window_size[Box.scence_BG]
    cols = Box.reel_num[Box.scence_BG]
    rng = np.zeros(cols, np.int64)
    board = np.zeros((rows, cols), np.int64)

    for reel_idx in range(cols):
        reel_len = Box.reels_len[table_id, reel_idx]
        reel_weight = Box.arr_reels_weight[table_id, :reel_len, reel_idx]
        stop = get_value(np.cumsum(reel_weight))
        rng[reel_idx] = stop

        reel = Box.arr_reels[table_id, :, reel_idx]
        for row_idx in range(rows):
            board[row_idx, reel_idx] = reel[(stop + row_idx) % reel_len]

    return board, rng
```

這個骨架只做兩件事：

* 從 `Box` 讀參數
* 生成和 simulator 同型態的盤面

之後你可以再往上加：

* 判獎
* tumble
* FG
* 統計輸出

---

## 6. 實務上最容易踩錯的點

### 6.1 不要把歷史 xlsx 當唯一真相

`H013_糖果狂歡` 資料夾內的歷史 xlsx 很有價值，但它不是目前 runtime 的唯一來源。

已知最典型差異：

* 歷史 xlsx 提過「FG 高低表場次由權重決定」
* 目前 `H013_Simulator.py` 實際是固定 `2 高表 + 8 低表`

如果你的新程式目標是「對齊現在 simulator」，請以程式為準。

### 6.2 `window_size` 和 `reel_num` 不要看反

本作是：

* `window_size = 5`
* `reel_num = 6`

也就是 **6 輪盤、5 列**，不是 5 輪盤、6 列。

### 6.3 Scatter 與一般得分的判定時點不同

一般符號：

* 每次 tumble 都要判斷

Scatter：

* 要等整局 Base Game / 單局 FG tumble 全部結束後才統計

### 6.4 倍數不是盤面上看到就立刻乘

目前程式不是「消一串就乘一次」，而是：

1. 先看該局最終盤面有幾顆 `C2`
2. 再逐顆抽倍數
3. 加總成一個 `multi_cum`
4. 把這個 `multi_cum` 套到該局所有得分

### 6.5 `coin_in` 算錯，所有 RTP 都會錯

尤其是：

* `Extra Bet = 1.25x`
* `Feature Buy = 75x`
* `Super Feature Buy = 500x`

新程式如果要做統計，一定要先確認自己使用的 `coin_in` 和 simulator 一致。

---

## 7. 建議優先查看的欄位 / 常數

如果你只想快速做出一支可用的新工具，先看這幾組：

* `Box.window_size`
* `Box.reel_num`
* `Box.arr_reels`
* `Box.arr_reels_weight`
* `Box.reels_len`
* `Box.symbols_score`
* `Box.pay_table`
* `Box.pay_table_C1`
* `Box.pay_table_awards_cascading`
* `Box.value_multiplier`
* `Box.weight_cum_table_multiplier_range_FG_low`
* `Box.weight_cum_table_multiplier_range_FG_high`

這一組就足夠做出：

* 初始盤面生成
* 一般判獎
* Scatter 判斷
* FG 倍數分析原型

---

## 8. 文件來源 / 參考

* `C:\Users\rhinshen\Mine\個人工作區\2_Program\Project\Slots\H013_Simulator.py`
* `C:\Users\rhinshen\Mine\個人工作區\2_Program\Project\Slots\Source\H013_Box.py`
* `C:\Users\rhinshen\Mine\個人工作區\2_Program\Project\Slots\Source\General\Math.py`
* `C:\Users\rhinshen\Mine\個人工作區\2_Program\Project\Slots\Source\General\RedBox.py`
* `C:\Users\rhinshen\Mine\個人工作區\0_Project (專案相關)\IGaming\1_專案\遊戲開發\所有遊戲\H013_糖果狂歡\歷史紀錄\v1\H013197-0.0.0.1.xlsx`
* `C:\Users\rhinshen\Mine\個人工作區\0_Project (專案相關)\IGaming\1_專案\遊戲開發\所有遊戲\H013_糖果狂歡\遊戲畫面_Help\*.png`
