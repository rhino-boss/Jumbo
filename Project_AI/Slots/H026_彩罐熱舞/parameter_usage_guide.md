# H026 xlsx 參數在程式中的使用說明

## 範圍

本文件重點是回答三件事：

- `H026192.xlsx` 的資料最後怎麼進入 runtime
- `config.js` 裡的主要參數各自控制哪一段玩法
- 一局遊戲從開局到結束時，這些參數是怎麼被依序用掉的

如果你要看更細的欄位對欄位對照，請搭配：

- [xlsx_config_usage_mapping.md](./Tool/xlsx_config_usage_mapping.md)

---

## 1. 先看整體流程

這個專案的參數流向很單純：

1. 企劃或數學先把資料填在 `H026192.xlsx`
2. `Tool/xlsx_to_config.py` 讀 xlsx，整理後輸出成 `config.js`
3. `Simulator.py` 讀 `config.js` 跑大量模擬
4. `index.html` 讀同一份 `config.js` 跑單局展示

先記住一個核心觀念：

- xlsx 不是 runtime 直接使用的資料
- runtime 真正吃的是 `config.js`
- 如果你想知道某個參數如何影響遊戲結果，最後一定要回到單局流程看它在什麼時點被用到

---

## 2. xlsx 轉成 `config.js` 之後，資料被分成哪幾類

`Tool/xlsx_to_config.py` 不只是把欄位原封不動搬過去，而是會先整理成比較好用的 runtime 結構。

最常見的轉換有這幾種：

- 原始權重會整理成累積權重，方便 runtime 抽樣
- 金框符號會整理成「基底符號 + 是否金框」兩層資訊
- 會先整理出哪些符號可得分、哪些符號是特殊符號
- 各輪帶的有效長度會先算好

可以把 `config.js` 內的資料粗分成 5 類：

### 2.1 基本模式與場景

代表欄位：

- `mode_normalbet`
- `mode_featurebuy`
- `scene_bg`
- `scene_fg`
- `scene_bf`
- `default_coin_in`
- `normalbet`
- `featurebuy`

主要用途：

- 決定這局是一般下注還是買入免費遊戲
- 決定現在是在 BG、FG 還是 BF 場景
- 決定這局成本怎麼算

### 2.2 判獎相關

代表欄位：

- `paylines`
- `pay_table`
- `symbol_id`
- `symbol_str`
- `base_symbol_of`
- `is_score_symbol`

主要用途：

- 決定 20 條線怎麼判
- 決定每個一般符號 3 / 4 / 5 連給多少分
- 決定金框符號在判獎前要先還原成哪個一般符號

### 2.3 初始盤面生成

代表欄位：

- `weight_cum_table_bg`
- `arr_reels`
- `arr_reels_weight_cum`
- `reels_len`
- `strip_name_map`

主要用途：

- 先決定這局抽到哪張 table
- 再決定每個 reel 的停輪位置
- 最後展開成可見盤面

補充：

- 初始盤面是 4x5
- 真正記分的是底部 3x5

### 2.4 金框與倍數

代表欄位：

- `is_gold_symbol`
- `value_multiplier_range`
- `weight_special_pool`
- `weight_cum_multiple_special`
- `weight_cum_multiple_before`
- `weight_cum_multiple_after`
- `weight_cum_multiple_r3_before`
- `weight_cum_multiple_r3_after`

主要用途：

- 判斷某個符號是不是金框
- 決定金框在初始盤面拿到什麼倍數
- 決定掉落補進來的金框拿到什麼倍數
- 決定特殊格是否啟用，以及特殊格吃哪套倍數權重

### 2.5 Cascade 與補牌

代表欄位：

- `drop_weight_a_cum`
- `drop_weight_b_cum`
- `eliminate_table_weight_cum_bg`
- `eliminate_table_weight_cum_fg`
- `eliminate_table_weight_cum_bf`

主要用途：

- 決定這局 Cascade 用 A 還是 B 補牌模式
- 決定每個 reel 補進哪些新符號
- 讓 BG / FG / BF 在掉落行為上可以分開配置

---

## 3. xlsx 哪些工作表主要對應到哪一類資料

### 3.1 `Overview`

主要提供：

- 遊戲基本資訊
- 符號代號
- 賠率表
- 一般符號與金框符號的對應關係

它主要影響的是：

- 判獎規則
- 符號顯示
- 金框在判獎時要還原成哪個一般符號

### 3.2 `Parameter`

主要提供：

- BG table weight
- multiplier range
- before / after multiplier weight
- special pool weight
- eliminate table weight

它主要影響的是：

- 開局抽哪張 table
- 金框倍數怎麼分配
- Special Pool 什麼情況會啟動
- Cascade 用哪套補牌模式

### 3.3 `BG_Symbol* / FG_Symbol* / BF_Symbol`

主要提供：

- 各場景的 reel strip
- 各場景的初始停輪權重
- 各場景的 `Drop A / Drop B` 權重

它主要影響的是：

- 初始盤面怎麼長出來
- Cascade 補進來哪些符號
- BG、FG、BF 的盤面手感差異

---

## 4. 一局遊戲實際怎麼跑

這一段是整份文件最重要的部分。前面那些參數，最後都會在這個流程裡被消耗掉。

### 4.1 Base Game 單局流程

1. 先依下注模式計算本局成本。
   - `Normal Bet` 用一般倍率
   - `Feature Buy` 用買入倍率
2. 依目前場景決定這局要用哪一類 table。
   - BG 用 BG 的 table
   - FG 用 FG 的 table
   - BF 用 BF 的 table
3. 如果是在 FG，還會再看目前已累積的倍數，切到對應強度的機率區段。
4. 系統再抽出這局要使用 `Drop A` 還是 `Drop B`。
5. 根據該局採用的 reel strip 與停輪權重，產生初始 4x5 畫面。
6. 初始盤面上的金框符號先被分配倍數。
   - 記分區內的金框主要吃初始進場用的倍數規則
   - 頂部預覽列或特殊位置的金框可能吃不同規則
   - 若特殊格啟動，會有 1 顆記分區金框改吃特殊倍數規則
7. 盤面依固定 20 線，由左到右進行判獎。
8. 若有中獎，先累加這一輪的 line win。
9. 若中獎位置裡有金框，該格不直接消失，而是留在原位轉成 Wild，並把該顆金框的倍數收集起來。
10. 其他中獎位置清空後，現有符號先往下掉。
11. 還空著的位置再依這局採用的補牌模式補進新符號。
12. 若新補進來的是金框，會依掉落用的倍數規則再分配倍數。
13. 若補牌後又形成新中獎，就重複判獎、消除、掉落、補牌。
14. 直到盤面不再形成新中獎，才統計最終盤面上的 Scatter 數量。
15. 若這一整局曾實際收集到倍數，才在整局結束後把累積倍數一次乘上整局總得分。
16. 若最終盤面 Scatter 達門檻，就進入免費遊戲。

### 4.2 這個流程中最重要的 4 個規則

#### A. 倍數不是每次中獎就立刻乘

- 單次連消過程中，倍數先收集起來
- 要等整局不能再消除後，才一次乘到整局總分

#### B. 金框要先中獎，倍數才算真的拿到

- 金框先當一般符號參與判獎
- 只有該顆金框真的在該次消除中被打掉，才會收集它的倍數
- 被打掉後，該位置會轉成 Wild 留在盤面

#### C. Scatter 要看整局最後結果

- 不是中途看到 Scatter 就立刻進 FG
- 必須等整局 Cascade 全部結束後，看最終盤面 Scatter 數量

#### D. 同一欄 Cascade 補牌不會補出第二顆 Scatter

- 某一欄只要已經有 Scatter
- 該欄後續補牌若再次抽到 Scatter，會重抽

---

## 5. Free Game 和 Base Game 的差別

FG 不是另一套完全不同的玩法，而是在同一條主流程上切換機率配置並保留累積倍數。

主要差異如下：

- 場景切到 `scene_fg`
- 使用 FG 專用的 table、reel strip、補牌權重
- FG 的 table 選擇會受到目前已累積倍數影響
- 單局 FG 結束後若最終盤面再出現 `3+ Scatter`，會 retrigger `15 / 17 / 19`
- 單次進入 FG 後，包含 retrigger 在內，總場數上限是 50

最重要的一點：

- BG 的倍數只影響那一局
- FG 的倍數會跨局保留，到整段 FG 結束才清掉

---

## 6. 用範例把流程串起來

### 6.1 範例 A：一般 Base Game 單局

假設某次 `Normal Bet` 單局流程如下。

符號說明：

- `GA` = 金框 A
- `GJ` = 金框 J
- `WW` = Wild
- `C1` = Scatter

初始 4x5 畫面如下：

| 列位 | R1 | R2 | R3 | R4 | R5 |
| --- | --- | --- | --- | --- | --- |
| 預覽列 | K | M2 | GQ | J | M1 |
| 第 1 列 | Q | J | M3 | A | C1 |
| 第 2 列 | A | GA(x10) | A | A | M5 |
| 第 3 列 | M3 | K | Q | J | M4 |

這一局可以這樣理解：

1. 本局先依一般下注倍率算出成本。
2. 系統先抽到某張 BG table。
3. 這局再抽到 `Drop B` 補牌模式。
4. 初始盤面長出後，第 2 列形成 `A - GA - A - A`，等於 4 個 A 連線。
5. 因為 `GA` 參與這次中獎，所以這顆金框不會直接消失，而是會先收集 `x10`，再在原位轉成 `WW`。

第一輪中獎處理後，盤面會變成：

| 列位 | R1 | R2 | R3 | R4 | R5 |
| --- | --- | --- | --- | --- | --- |
| 預覽列 | K | M2 | GQ | J | M1 |
| 第 1 列 | 空 | J | M3 | 空 | C1 |
| 第 2 列 | 空 | WW | 空 | 空 | M5 |
| 第 3 列 | M3 | K | Q | J | M4 |

接著現有符號先往下掉，再依 `Drop B` 補牌，示意結果如下：

| 列位 | R1 | R2 | R3 | R4 | R5 |
| --- | --- | --- | --- | --- | --- |
| 預覽列 | Q | M2 | K | M3 | M1 |
| 第 1 列 | J | J | A | A | C1 |
| 第 2 列 | J | WW | GJ(x5) | J | M5 |
| 第 3 列 | M3 | K | Q | J | M4 |

6. 補牌後，第 2 列形成 `J - WW - GJ - J`，可視為 4 個 J 連線。
7. 這次 `GJ` 也參與中獎，所以再收集 `x5`，該位置之後也會轉成 `WW`。
8. 若後面不再形成新中獎，則這局總共收集到 `x10 + x5 = x15`。
9. 最後才把整局所有 line win 加總後，再一次乘上 `x15`。
10. 若最終盤面還有 3 顆以上 `C1`，才在整局結束後進 FG。

這個例子對應到的參數順序是：

- 開局 table：`weight_cum_table_bg`
- 初始盤面：`arr_reels_weight_cum` + `arr_reels`
- 初始金框倍數：`weight_special_pool` / `weight_cum_multiple_before` / `weight_cum_multiple_r3_before`
- 掉落補牌：`eliminate_table_weight_cum_bg` + `drop_weight_b_cum`
- 掉落後金框倍數：`weight_cum_multiple_after` / `weight_cum_multiple_r3_after`
- 派彩：`paylines` + `pay_table`

### 6.2 範例 B：FG 累積倍數如何跨局保留

假設玩家在 BG 最終盤面拿到 4 Scatter，進入 17 場 FG：

1. 第 1 局 FG 開始前，累積倍數為 0。
2. 第 1 局 FG 消到兩顆金框，收集 `x8 + x20`，所以本局結束後累積倍數變成 `x28`。
3. 第 2 局 FG 開始前，系統會依目前的 `x28` 切到對應的 FG 機率區段。
4. 第 2 局若沒有再收新倍數，本局仍會帶著既有累積值結算。
5. 第 3 局若又新增 `x10`，則後續累積倍數變成 `x38`。
6. 若某局最後又出現 5 Scatter，則 retrigger 再加 19 場，但整段 FG 仍受 50 場上限限制。

最容易誤解的地方：

- FG 不會每局把倍數重置回 0
- FG 的機率配置會受目前累積倍數影響
- retrigger 只增加剩餘局數，不會清掉已累積倍數

### 6.3 範例 C：為什麼改了 xlsx 權重卻覺得沒生效

常見原因如下：

1. 你改的是 xlsx 裡的某組原始權重。
2. 但沒有重新產生 `config.js`。
3. runtime 其實還在讀舊資料。
4. 或者你改的是原始權重，但 runtime 實際使用的是轉換後的累積權重。
5. 或者你改的是某張 table，但實際測試的場景根本抽不到那張 table。

排查順序建議固定：

1. 先確認 xlsx 原值是否改對
2. 再確認 `config.js` 是否重新生成
3. 再確認 `Simulator.py` / `index.html` 是否真的讀到那個欄位
4. 最後確認該欄位是在 BG、FG 還是 BF 場景被使用

---

## 7. 實務上最常影響結果的參數

### 7.1 最常影響數學結果

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

### 7.2 最常影響玩法表現

- `arr_reels`
- `arr_reels_weight`
- `drop_weight_a/b`
- `value_multiplier_range`

### 7.3 最容易誤判的地方

- 改了 raw weight，但 runtime 實際吃的是 `*_cum`
- 以為 multiplier 跟著輪帶固定綁死，但實際上是另外抽的
- 以為所有初始金框都吃同一套 `before` 規則，但最上排非記分區金框其實吃 `after`
- 以為所有 R3 金框都吃 `Reel3 Before/After`，但目前只有指定輪帶表的 R3 會用到

---

## 8. 查一個參數有沒有生效，最短路徑怎麼走

建議順序：

1. 先在 xlsx 找到原始欄位
2. 到 `Tool/xlsx_to_config.py` 找它被轉成哪個 `config.js` 欄位
3. 到 `config.js` 確認產出的值是不是你預期的
4. 在 `Simulator.py` / `index.html` 搜尋這個欄位名
5. 確認程式是直接使用它，還是只使用它的 cumulative / 衍生版本

---

## 9. 建議搭配查看的檔案

- [xlsx_to_config.py](./Tool/xlsx_to_config.py)
- [xlsx_config_usage_mapping.md](./Tool/xlsx_config_usage_mapping.md)
- [config.js](./config.js)
- [Simulator.py](./Simulator.py)
- [index.html](./index.html)
