# H026 xlsx 參數在程式中的使用說明

## 範圍

本文件說明：

- `H026192.xlsx` 的主要參數來源
- `Tool/xlsx_to_config.py` 如何把 xlsx 轉成 `config.js`
- `Simulator.py` 與 `index.html` 如何實際使用這些參數

如果你要看更細的欄位對欄位對照，請搭配：

- [xlsx_config_usage_mapping.md](./Tool/xlsx_config_usage_mapping.md)

---

## 1. 整體流程

目前這個專案的參數流向是：

1. 企劃或數學把資料填在 `H026192.xlsx`
2. `Tool/xlsx_to_config.py` 讀 xlsx，整理成 `config.js`
3. `Simulator.py` 讀 `config.js` 跑大量模擬
4. `index.html` 讀同一份 `config.js` 跑 demo / 單局展示

也就是說：

- xlsx 不是直接被 simulator 使用
- xlsx 會先被轉成 `config.js`
- runtime 真正依賴的是 `config.js`

---

## 2. 轉檔程式做了什麼

`Tool/xlsx_to_config.py` 主要分成三件事：

1. 讀取 xlsx 中各工作表的原始參數
2. 把 raw weight、strip、paytable 整理成程式較好用的結構
3. 產出 `config.js`

它不只是單純搬欄位，還會做一些衍生資料，例如：

- `weight_*` 轉成 `weight_cum_*`
- `G1/G2/...` 轉成 `base_symbol_of`
- 依符號型態產出 `is_gold_symbol`
- 依賠表產出 `is_score_symbol`
- 統計各 reel 的有效長度 `reels_len`

所以很多 runtime 直接用到的欄位，其實不是 xlsx 裡原樣存在，而是轉檔程式加工後的結果。

---

## 3. xlsx 主要工作表怎麼用

### 3.1 `Overview`

這張表主要提供遊戲的基礎靜態資料：

- `game_id`
- `pay_table`
- `symbol_id`
- `symbol_str`
- 一般符號 / 金框符號的對應關係

這些資料會影響：

- 哪些 symbol 能得分
- 3 / 4 / 5 連各給多少分
- 金框符號在 board 上要還原成哪個 base symbol

程式中的實際用途：

- `Simulator.py` 用它來做 line win 計算
- `index.html` 用它來做同樣的單局判獎與符號顯示

### 3.2 `Parameter`

這張表主要提供數學機制參數：

- paylines
- BG table weight
- multiplier range
- before / after multiplier weight
- special pool weight
- eliminate table weight

這些資料會影響：

- BG 要抽哪張 table
- 金框初始倍數怎麼抽
- Cascade 後補進來的金框倍數怎麼抽
- 消除階段要用哪套 drop table

### 3.3 `BG_Symbol* / FG_Symbol* / BF_Symbol`

這些表主要提供各場景的 strip 與 drop 權重：

- `Symbol_ID_R1~R5`
- `Strip_Weight_R1~R5`
- `Drop_Weight_A_R1~R5`
- `Drop_Weight_B_R1~R5`

這些資料會影響：

- 初始 3x5 停輪畫面怎麼生成
- Cascade 後第 2、3 顆補牌怎麼抽
- FG / BF 使用哪套 strip

補充：

- 目前專案已經改成「每個 reel 在 cascade 補牌時，第 1 顆優先承接可見畫面上方那顆隱藏輪帶符號」
- 所以 `Drop_Weight_A/B` 不再控制每一顆補牌，而是主要控制同一個 reel 該次 cascade 的第 2 顆之後的補牌

---

## 4. `config.js` 生成後，程式怎麼使用

### 4.1 基本常數

這類欄位通常在程式初始化時就讀進來：

- `reel_num`
- `window_size`
- `mode_normalbet`
- `mode_featurebuy`
- `scene_bg`
- `scene_fg`
- `scene_bf`
- `default_coin_in`
- `normalbet`
- `featurebuy`

用途：

- 定義盤面大小
- 區分 Normal Bet / Feature Buy
- 區分 BG / FG / BF 場景
- 計算 `coin_in`

### 4.2 賠率與符號判定

這類欄位主要被 `evaluate_board()` 類型邏輯使用：

- `paylines`
- `pay_table`
- `symbol_id`
- `symbol_str`
- `base_symbol_of`
- `is_gold_symbol`
- `is_score_symbol`
- `symbols_score`

用途：

- 判斷每條線怎麼走
- 判斷哪些 symbol 可算分
- 把金框 strip symbol 還原成 base symbol 參與判獎
- 顯示符號代碼與名稱

### 4.3 初始盤面生成

這類欄位控制一局開始時的停輪結果：

- `weight_cum_table_bg`
- `arr_reels`
- `arr_reels_weight_cum`
- `reels_len`
- `strip_name_map`

用途：

- BG 先決定要用哪張 table
- 每個 reel 再依 strip weight 抽 stop index
- 用 stop index 展開成可見 3x5 畫面

### 4.4 倍數分配

這類欄位控制金框 symbol 的 multiplier：

- `value_multiplier_range`
- `weight_special_pool`
- `weight_cum_multiple_special`
- `weight_cum_multiple_r3_before`
- `weight_cum_multiple_before`
- `weight_cum_multiple_r3_after`
- `weight_cum_multiple_after`

用途：

- 初始盤面上的金框抽 `before` 倍數
- Cascade 補進來的金框抽 `after` 倍數
- 特殊池觸發時改抽 `special` 倍數

目前專案中的實際規則是：

- 金框符號本身可以來自輪帶或 drop weight
- 但它上面的 multiplier 不是從輪帶直接讀，而是另外依對應權重抽出來

### 4.5 Cascade 補牌

這類欄位控制消除後如何補牌：

- `drop_weight_a_cum`
- `drop_weight_b_cum`
- `eliminate_table_weight_cum_bg`
- `eliminate_table_weight_cum_fg`

用途：

- 先決定這次消除用 A 還是 B 的 drop 模式
- 再決定每個 reel 第 2 顆之後的補牌內容

目前專案中的補牌邏輯是：

1. 初始盤面仍然由 reel strip 停輪決定
2. 每個 reel 在某次 cascade 補牌時，第 1 顆優先吃可見畫面上方那顆隱藏輪帶符號
3. 如果同一個 reel 同次 cascade 還要補第 2 顆、第 3 顆，才改用 `drop_weight_a/b`
4. 若補進來的是金框，倍數用 `after multiplier weight` 抽

---

## 5. `Simulator.py` 和 `index.html` 的分工

### 5.1 `Simulator.py`

用途是大量模擬，重點在統計：

- RTP
- hit rate
- FG trigger rate
- retrigger rate
- multiplier distribution
- eliminate distribution

所以它會大量使用：

- board 生成參數
- payline / paytable
- multiplier weight
- drop weight
- FG / BF 場景切換參數

### 5.2 `index.html`

用途是展示單局流程，重點在可視化：

- 初始盤面
- line win
- 金框轉 Wild
- Cascade 前後盤面
- 每次補牌事件
- 單局 multiplier 累積

它和 simulator 用同一份 `config.js`，所以理論上：

- 規則應該一致
- 差別只在一個拿來做批量統計，一個拿來做單局展示

---

## 6. 哪些 xlsx 參數最常影響結果

如果你是要調數學結果，最常動到的是：

- `pay_table`
- `weight_table_bg`
- `weight_multiple_before`
- `weight_multiple_after`
- `weight_multiple_r3_before`
- `weight_multiple_r3_after`
- `weight_special_pool`
- `drop_weight_a`
- `drop_weight_b`
- 各場景 strip

如果你是要調玩法表現，最容易看出差異的是：

- `arr_reels`
- `arr_reels_weight`
- `drop_weight_a/b`
- `value_multiplier_range`

如果你是要查規則為什麼和模擬結果不同，優先檢查：

1. xlsx 原值
2. `xlsx_to_config.py` 是否有轉換邏輯
3. `config.js` 產出的最終值
4. `Simulator.py` / `index.html` 有沒有真的讀到那個欄位

---

## 7. 實務上怎麼查一個參數有沒有生效

建議順序：

1. 先在 xlsx 找到原始欄位
2. 到 `Tool/xlsx_to_config.py` 找它被轉成哪個 `config.js` 欄位
3. 到 `config.js` 確認產出的值是不是你預期的
4. 在 `Simulator.py` / `index.html` 搜尋這個欄位名
5. 確認程式是直接使用它，還是只使用它的 cumulative / 衍生版本

最常見的誤解是：

- 改了 raw weight，但 runtime 實際吃的是 `*_cum`
- 以為 multiplier 跟著輪帶走，但實際上 multiplier 是另外抽的
- 以為所有補牌都吃 drop weight，但目前第 1 顆補牌先吃 reel 上方隱藏符號

---

## 8. 目前這個專案要特別注意的點

### 8.1 reel strip 與 drop weight 是兩套來源

初始盤面與 cascade 補牌不是完全同一套來源：

- 初始盤面：看 `arr_reels` + `arr_reels_weight_cum`
- cascade 第 1 顆：看目前可見畫面上方的隱藏輪帶符號
- cascade 第 2 顆之後：看 `drop_weight_a/b`

### 8.2 金框符號與倍數不是同一個來源

金框符號可能來自：

- 初始輪帶
- reel 上方隱藏符號
- drop weight

但它的 multiplier 來源是：

- `before multiplier weight`
- `after multiplier weight`
- `special multiplier weight`

不是直接跟著 strip 綁死。

### 8.3 xlsx 改完不代表 simulator 自動更新

你改的是 `xlsx`，但 simulator / demo 讀的是 `config.js`。

所以只改 xlsx 還不夠，必須重新跑：

- `Tool/xlsx_to_config.py`

把最新設定重新轉成 `config.js`，程式才會吃到。

---

## 9. 建議搭配查看的檔案

- [xlsx_to_config.py](./Tool/xlsx_to_config.py)
- [xlsx_config_usage_mapping.md](./Tool/xlsx_config_usage_mapping.md)
- [config.js](./config.js)
- [Simulator.py](./Simulator.py)
- [index.html](./index.html)

