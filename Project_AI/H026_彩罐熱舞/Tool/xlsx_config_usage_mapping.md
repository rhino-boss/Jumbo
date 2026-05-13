# H026 xlsx -> config.js -> simulator/index 對照表

## 範圍

本文件對照目前專案中的：

- `H026192.xlsx`
- `config.js`
- `simulator.py`
- `index.html`（即 demogame）

目的：

1. 說明 `xlsx` 哪些 sheet / 欄位會進到 `config.js`
2. 說明 `config.js` 每個欄位在哪裡被 `simulator.py` / `index.html` 使用
3. 標示哪些欄位是「直接來自 xlsx」、哪些是「由 xlsx 衍生」、哪些是「generator / 靜態資料」

## 流程確認

目前正確流程是：

1. 提供 `xlsx`
2. 由轉換程序把 `xlsx` 轉成 `config.js`
3. `simulator.py` 讀 `config.js`
4. `index.html` 也讀同一份 `config.js`
5. 兩者用相同資料結構與近乎相同邏輯執行模擬 / demogame

## 說明約定

- `直接`：可直接對應到目前 `xlsx` 可見欄位
- `衍生`：由 `xlsx` 原始欄位轉換、展開、累積或重新編碼得到
- `靜態/外部`：目前 `xlsx` 看不到明確欄位來源，通常是 generator、圖片設定或程式常數
- `未使用`：目前欄位存在於 `config.js`，但 runtime 沒有真正讀它

---

## A. config.js 整體欄位對照

| config.js 欄位 | xlsx 來源 | 類型 | simulator.py 使用位置 | index.html 使用位置 | 備註 |
| --- | --- | --- | --- | --- | --- |
| `generated_at` | 無 | 靜態/外部 | 未使用 | 未使用 | 產檔時間戳 |
| `source_box` | 無 | 靜態/外部 | 未使用 | 未使用 | 來源模組資訊 |
| `game_id` | `Overview.B2` | 直接 | `370`, `979`, `1006` | `1558` | 顯示與摘要 |
| `game_name` | 推定來自 generator / 外部命名 | 靜態/外部 | `371`, `372` | `1559` | `xlsx` 目前只看得到 `game_ID`，看不到中文名欄位 |
| `display_name` | 推定來自 generator / 外部命名 | 靜態/外部 | `372` | 未使用 | UI 目前沒用到 |
| `bet_options` | 無明確欄位 | 靜態/外部 | `375`, `376` | 未使用 | HTML 下注選項目前寫死在 `BET_OPTIONS_MONEY` |
| `mode_normalbet` | 無 | 靜態/外部 | `423`, `887`, `908` | `681`, `1275`, `1555` | 模式常數 |
| `mode_featurebuy` | 無 | 靜態/外部 | `424`, `877`, `887`, `889`, `891`, `908`, `910` | `686`, `1140`, `1142`, `1160`, `1203`, `1315`, `1556` | 模式常數 |
| `scene_bg` | 無 | 靜態/外部 | `425`, `462`, `846`, `889` | `773`, `1100`, `1140` | 場景常數 |
| `scene_fg` | 無 | 靜態/外部 | `426`, `466`, `848`, `921` | `777`, `1100`, `1175` | 場景常數 |
| `scene_bf` | 無 | 靜態/外部 | `427`, `889` | `1140` | Buy Feature 場景常數 |
| `reel_num` | 由 strip / paylines 結構可得 | 衍生 | `287`, `292`, `374`, `422` | `796`, `797`, `798`, `801`, `822`, `878`, `895`, `916`, `962`, `983`, `1049`, `1406` | 目前值為 5 |
| `window_size` | 由 strip 視窗高度可得 | 衍生 | `373`, `421` | `796`, `797`, `798`, `805`, `821`, `878`, `961`, `985`, `992`, `1049`, `1404` | 目前值為 3 |
| `default_coin_in` | 無明確欄位 | 靜態/外部 | `351`, `876` | `643`, `685` | bet 換算基準 |
| `normalbet` | 無明確欄位 | 靜態/外部 | `876` | `643`, `685` | 一般下注倍率常數 |
| `featurebuy` | 無明確欄位 | 靜態/外部 | `67`, `78`, `377`, `878`, `887`, `1009`, `1115` | `648`, `686`, `1163`, `1523` | Buy Feature 成本，當前值 75 |
| `special_pool_weight_base` | 無明確欄位 | 靜態/外部 | `528`, `542` | `830`, `842` | special pool RNG base，當前值 10000 |
| `paylines` | `Parameter` 工作表第 5 列起的盤線表 | 直接 | `392`, `429`, `575`, `590`, `609` | `882`, `887`, `896`, `917`, `936` | 20 條線的列索引陣列 |
| `pay_table` | `Overview` 工作表 `Pay Table：` 區塊中的 `3 / 4 / 5 / Id / Symbol` | 直接 | `350`, `432`, `569`, `578` | `874` | 依 symbol id 存 3/4/5 連線獎金 |
| `symbol_id` | `Overview` 工作表 `Pay Table：` 區塊的 `Id` | 直接 | `595`, `664`, `759`, `769`, `772`, `793` | `1009`, `1402` | drop fill 時依索引取實際 symbol id |
| `symbol_str` | `Overview` 工作表 `Pay Table：` 區塊的 `Symbol` | 直接 | `279`, `596`, `665`, `794` | `709`, `754`, `944`, `1031`, `1409` | id -> symbol code |
| `base_symbol_of` | 由 `Overview` 工作表 `Pay Table：` 區塊中的 `Symbol` base / gold 對應關係產生 | 衍生 | `276`, `502`, `773` | `807`, `1010`, `1408` | 例如 `G1 -> M1` |
| `is_gold_symbol` | 由 `Overview` 工作表 `Pay Table：` 區塊中的 symbol code 是否為 gold 版產生 | 衍生 | `277`, `504`, `775` | `809`, `1012` | `G1~GJ` 為 1 |
| `is_score_symbol` | 由 `Overview` 工作表 `Pay Table：` 區塊可否得分產生 | 衍生 | `278`, `431`, `567`, `577` | `873` | Wild/Scatter 為 0，一般符號為 1 |
| `symbols_score` | 由 `Overview` 工作表 `Pay Table：` 區塊可得分符號 id 清單產生 | 衍生 | `430`, `576`, `619` | `892` | 盤面評獎迴圈使用 |
| `value_multiplier_range` | `Parameter` 工作表 `Multiplier` 區塊 | 直接 | `341`, `381`, `447` | `730` | 倍數值清單 |
| `weight_table_bg` | `Parameter` 工作表 BG table weight 區塊 | 直接 | `272`, `384`, `465` | `776` | BG 選 table 權重 |
| `weight_cum_table_bg` | 由 `Parameter` 工作表 BG table weight 區塊累加 | 衍生 | `387`, `463` | `774` | BG 選 table 用 cumulative weight |
| `fg_table_rule` | 推定來自 generator / 規則設定 | 靜態/外部 | `390` | 未使用 | 目前 runtime 沒拿它做 FG table 選擇 |
| `weight_multiple_special` | `Parameter` 工作表 special multiplier weight 區塊 | 直接 | `338` | 未直接取 raw weight | special gold 倍數 raw weight |
| `weight_multiple_r3_before` | `Parameter` 工作表 R3 before multiplier weight 區塊 | 直接 | `336` | 未直接取 raw weight | R3 初始 gold 倍數 raw weight |
| `weight_multiple_r3_after` | `Parameter` 工作表 R3 after multiplier weight 區塊 | 直接 | `337` | 未直接取 raw weight | R3 drop 後 gold 倍數 raw weight |
| `weight_multiple_before` | `Parameter` 工作表 before multiplier weight 區塊 | 直接 | `334` | 未直接取 raw weight | 非 R3 初始 gold 倍數 raw weight |
| `weight_multiple_after` | `Parameter` 工作表 after multiplier weight 區塊 | 直接 | `335` | 未直接取 raw weight | 非 R3 drop 後 gold 倍數 raw weight |
| `weight_cum_multiple_special` | 由 `weight_multiple_special` 累加 | 衍生 | `550` | `854` | special gold 倍數抽選 |
| `weight_cum_multiple_r3_before` | 由 `weight_multiple_r3_before` 累加 | 衍生 | `454` | `739` | R3 初始 gold 倍數抽選 |
| `weight_cum_multiple_r3_after` | 由 `weight_multiple_r3_after` 累加 | 衍生 | `458` | `745` | R3 drop 後 gold 倍數抽選 |
| `weight_cum_multiple_before` | 由 `weight_multiple_before` 累加 | 衍生 | `454` | `740` | 非 R3 初始 gold 倍數抽選 |
| `weight_cum_multiple_after` | 由 `weight_multiple_after` 累加 | 衍生 | `458` | `746` | 非 R3 drop 後 gold 倍數抽選 |
| `weight_special_pool` | `Parameter` 工作表 special pool weight 區塊 | 直接 | `539` | `839` | Base 特殊金框池觸發率 |
| `arr_reels` | `BG_Symbol* / FG_Symbol* / BF_Symbol` 工作表的 symbol 區塊 | 直接 | `280`, `501` | `803`, `806` | 各 table reel strip 符號表 |
| `arr_reels_weight` | `BG_Symbol* / FG_Symbol* / BF_Symbol` 工作表的 strip weight 區塊 | 直接 | `281` | 未使用 | raw reel weight，HTML/Simulator 都實際用 cum 版 |
| `arr_reels_weight_cum` | 由 `arr_reels_weight` 累加 | 衍生 | `489` | `803` | 停輪抽樣用 cumulative weight |
| `drop_weight_a` | `BG_Symbol* / FG_Symbol* / BF_Symbol` 工作表的 `Drop_Weight_A` 區塊 | 直接 | 未使用 | `1007` | HTML 只被關鍵字命中；runtime 實際用 cum 版 |
| `drop_weight_b` | `BG_Symbol* / FG_Symbol* / BF_Symbol` 工作表的 `Drop_Weight_B` 區塊 | 直接 | 未使用 | `1007` | 同上 |
| `drop_weight_a_cum` | 由 `drop_weight_a` 累加 | 衍生 | `768` | `1007` | Cascade 補符號抽樣用 |
| `drop_weight_b_cum` | 由 `drop_weight_b` 累加 | 衍生 | `768` | `1007` | Cascade 補符號抽樣用 |
| `reels_len` | 由各 strip 有效列數產生 | 衍生 | `282`, `488` | `802` | 各 table / reel 的有效長度 |
| `strip_name_map` | 由 sheet/table 命名產生 | 衍生 | `383`, `476` | `788` | `B1/B2/B3/F1/F2/F3/BF` |
| `frame_bg` | 無 | 靜態/外部 | 未使用 | `1236` | 金框底圖 |
| `frame_top` | 無 | 靜態/外部 | 未使用 | `1249` | 金框上層圖 |
| `asset_map` | 無 | 靜態/外部 | `352` | `705` | symbol code -> 圖片路徑 |

---

## B. 依 sheet 分組的來源對照

### B1. `Overview`

| xlsx 欄位 | config.js 欄位 | 備註 |
| --- | --- | --- |
| `B2` | `game_id` | 直接對應 |
| `A7` | `default_coin_in` | 直接對應 |
| `B11` | `normalbet` | 直接對應 |
| `B12` | `featurebuy` | 直接對應 |
| `B26` | `window_size` | 直接對應 |
| `Pay Table：` 區塊的 `Symbol` | `symbol_str` | id -> code 對照 |
| `Pay Table：` 區塊的 `Id` | `symbol_id` | symbol id 清單 |
| `Pay Table：` 區塊的 `3`, `4`, `5` | `pay_table` | 每個 symbol 的 3/4/5 連線獎金 |
| `Pay Table：` 區塊的 `Symbol + Id` | `symbols_score` | 過濾可得分的 symbol id |
| `Pay Table：` 區塊的 `Symbol` | `base_symbol_of` | 由 `G*` 對應回 base symbol |
| `Pay Table：` 區塊的 `Symbol` | `is_gold_symbol` | `G*` 類型標記 |
| `Pay Table：` 區塊的 `3/4/5` 是否全為 0 | `is_score_symbol` | 無獎金的 symbol 視為不可計分 |

### B2. `Parameter`

| xlsx 欄位 | config.js 欄位 | 備註 |
| --- | --- | --- |
| 第 5 列起第 B~G 欄盤線表 | `paylines` | 例如 `11111` 轉為 `[1,1,1,1,1]` |
| 第 5 列起第 J/K 欄 BG table weights | `weight_table_bg` / `weight_cum_table_bg` | BG 選 table 權重 |
| 第 12 列起第 J/K 欄 FG table weights | 未輸出 | FG 目前直接由 `fg_table_rule` 決定 table |
| 第 19 列起第 J/K 欄 BF table weights | 未輸出 | BF 目前固定使用 `BF` table |
| 第 I 欄 `Multiplier` 區塊 | `value_multiplier_range` | 倍數值清單 |
| 第 O~AA 欄 multiplier weight 各區塊 | `weight_multiple_*` / `weight_cum_multiple_*` | 各情境 gold multiplier 權重 |
| 第 AD~AK 欄 special pool 區塊 | `weight_special_pool` | 特殊池觸發權重 |
| 第 J/K 欄 `Eliminate Table Weight` 區塊 | `eliminate_table_weight_*` / `eliminate_table_weight_cum_*` | 消除階段 table 權重 |

### B3. `BG_Symbol`, `BG_Symbol (2)`, `BG_Symbol (3)`, `FG_Symbol`, `FG_Symbol (2)`, `FG_Symbol (3)`, `BF_Symbol`

共通欄位頭：

- `Symbol_ID_R1~R5`
- `Strip_Weight_R1~R5`
- `Drop_Weight_A_R1~R5`
- `Drop_Weight_B_R1~R5`

對應如下：

| xlsx 欄位群 | config.js 欄位 | 備註 |
| --- | --- | --- |
| 第 Q~U 欄 symbol 區塊 | `arr_reels` | 各 table 各 reel 的符號 strip |
| 第 W~AA 欄 strip weight 區塊 | `arr_reels_weight` | raw strip weight |
| 第 W~AA 欄 strip weight 區塊 | `arr_reels_weight_cum` | 對 raw weight 做 cumulative sum |
| 第 AD~AH 欄 drop weight A 區塊 | `drop_weight_a` | raw drop weight A |
| 第 AD~AH 欄 drop weight A 區塊 | `drop_weight_a_cum` | cumulative 版 |
| 第 AK~AO 欄 drop weight B 區塊 | `drop_weight_b` | raw drop weight B |
| 第 AK~AO 欄 drop weight B 區塊 | `drop_weight_b_cum` | cumulative 版 |
| 各 strip 實際有效列數 | `reels_len` | 各 table / reel 長度 |
| sheet 名稱 | `strip_name_map` | 對應成 `B1/B2/B3/F1/F2/F3/BF` |

### B4. 其他存在於 `H026192.xlsx` 但目前未進 `config.js` 的工作頁

- `Description`
- `工作表2`
- `Multiplier_Weight_Newbie`
- `Multiplier_Weight_Oldhand`
- `工作表1`
- `OP Jackpot`

---

## C. simulator.py 主要使用點

### C1. 啟動 / 基本設定

- `game_id`：摘要輸出與 `Base Info`
- `window_size`, `reel_num`：建立盤面尺寸
- `mode_normalbet`, `mode_featurebuy`, `scene_bg`, `scene_fg`, `scene_bf`：控制 base / FG / BF 流程
- `default_coin_in`, `normalbet`, `featurebuy`：計算 `coin_in`

### C2. 盤面生成

- `weight_cum_table_bg/fg/bf`、`weight_table_bg/fg/bf`：決定此次 spin 用哪張 table
- `strip_name_map`：把 table id 顯示成 `B1/F1/BF` 等名稱
- `arr_reels_weight_cum`、`reels_len`：決定每輪停輪 stop index
- `arr_reels`：取出 reel stop 後的可見符號
- `base_symbol_of`、`is_gold_symbol`：把 strip symbol 轉成 base board + gold mask

### C3. 倍數分配

- `weight_special_pool`
- `special_pool_weight_base`
- `weight_cum_multiple_special`
- `weight_cum_multiple_r3_before`
- `weight_cum_multiple_before`
- `value_multiplier_range`

這些欄位決定：

1. 是否進 special gold pool
2. 該 gold symbol 抽到哪個 multiplier

### C4. 中獎判定

- `paylines`
- `symbols_score`
- `is_score_symbol`
- `pay_table`
- `symbol_str`

這些欄位決定：

1. 哪些 line 要判
2. Wild 可替代哪些符號
3. 3/4/5 連線支付多少

### C5. Cascade / 補牌

- `drop_weight_a_cum`
- `drop_weight_b_cum`
- `symbol_id`
- `base_symbol_of`
- `is_gold_symbol`
- `weight_cum_multiple_r3_after`
- `weight_cum_multiple_after`

這些欄位決定：

1. 補進來的是哪個 symbol
2. 補進來若是 gold，抽到哪個 multiplier

### C6. 輸出

`simulator.py` 匯出 `Record Data / Multiplier Line / Hits / Pay / Eliminate / Base Info`，但這些輸出欄位不是 `config.js` 輸入來源，而是用上面欄位跑完後的模擬結果。

---

## D. index.html（demogame）主要使用點

### D1. 啟動 / UI

- `game_id`, `game_name`：標題顯示
- `asset_map`, `frame_bg`, `frame_top`：symbol 與金框素材

### D2. 下注與成本

- `default_coin_in`
- `normalbet`
- `featurebuy`
- `mode_normalbet`
- `mode_featurebuy`

注意：

- HTML 的下注選項目前不是讀 `bet_options`
- HTML 用自己寫死的 `BET_OPTIONS_MONEY`
- 再用 `default_coin_in * DENOM * normalbet` 回推 `bet_multi`

所以 `bet_options` 雖然存在於 `config.js`，目前 `index.html` 沒有真正使用。

### D3. 遊戲邏輯

`index.html` 和 `simulator.py` 的邏輯幾乎一一對應，使用到的欄位也幾乎相同：

- `weight_cum_table_bg/fg/bf`
- `weight_table_bg/fg/bf`
- `strip_name_map`
- `arr_reels`
- `arr_reels_weight_cum`
- `reels_len`
- `base_symbol_of`
- `is_gold_symbol`
- `weight_special_pool`
- `special_pool_weight_base`
- `weight_cum_multiple_special`
- `weight_cum_multiple_r3_before`
- `weight_cum_multiple_before`
- `weight_cum_multiple_r3_after`
- `weight_cum_multiple_after`
- `value_multiplier_range`
- `paylines`
- `symbols_score`
- `is_score_symbol`
- `pay_table`
- `drop_weight_a_cum`
- `drop_weight_b_cum`
- `symbol_id`
- `symbol_str`

---

## E. 目前值得注意的欄位

### E1. 存在但目前 runtime 未實際使用

| 欄位 | 現況 |
| --- | --- |
| `generated_at` | metadata only |
| `source_box` | metadata only |
| `display_name` | 目前 UI 未使用 |
| `bet_options` | HTML 未使用，下注清單寫死在 `BET_OPTIONS_MONEY` |
| `fg_table_rule` | 目前 simulator / HTML 都沒有依此規則切 FG table |
| `arr_reels_weight` | runtime 實際用 `arr_reels_weight_cum` |
| `drop_weight_a` | runtime 實際用 `drop_weight_a_cum` |
| `drop_weight_b` | runtime 實際用 `drop_weight_b_cum` |
| `frame_bg` | simulator 未使用，只有 HTML 用 |
| `frame_top` | simulator 未使用，只有 HTML 用 |

### E2. 目前 `xlsx` 看不到直接來源的欄位

下列欄位在目前 `H026192.xlsx` 的工作頁 / 對應儲存格中沒有直接看到明確來源，應視為 generator 或外部規則輸入：

- `game_name`
- `display_name`
- `bet_options`
- `mode_normalbet`
- `mode_featurebuy`
- `scene_bg`
- `scene_fg`
- `scene_bf`
- `default_coin_in`
- `normalbet`
- `featurebuy`
- `special_pool_weight_base`
- `fg_table_rule`
- `asset_map`
- `frame_bg`
- `frame_top`

---

## F. 結論

目前專案的核心架構是正確的：

- `xlsx` 提供數學與 strip 資料
- `config.js` 是統一執行格式
- `simulator.py` 與 `index.html` 都吃同一份 `config.js`

但如果要把流程完全收斂成「同一份 config，完全同一邏輯」的標準版，接下來最值得處理的是：

1. 讓 `index.html` 改讀 `config.bet_options`，不要再寫死 `BET_OPTIONS_MONEY`
2. 確認 `fg_table_rule` 是否應該真的參與 FG table 選擇
3. 明確定義那些目前屬於 generator/static 的欄位，到底是來自 xlsx、企劃規格，還是程式預設
