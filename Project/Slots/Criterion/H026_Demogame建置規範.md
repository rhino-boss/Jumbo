# H026 Demogame 建置規範

## 1. 目的
本文件用於定義 H026 的 Demogame 建置方式。Demogame 的用途是「試玩」，不是模擬統計，因此需要保留 `H026_Simulator.py` 的單局遊戲邏輯與 `H026_Box.py` 的參數設定，同時補齊前端展示、逐步結果輸出與可重播的狀態資料。

## 2. 建置目標
1. 建立一份 H026 專用 Demogame 主程式。
2. Demogame 的核心盤面流程必須與 `Project/Slots/H026_Simulator.py` 一致。
3. Demogame 使用的參數、symbol 定義、權重表、paytable、paylines、multiplier 規格，必須直接沿用 `Project/Slots/Source/H026_Box.py`。
4. Demogame 可以為了試玩目的新增狀態輸出、逐步紀錄、UI 顯示資料整理，但不得自行發明另一套數學邏輯。
5. 第一優先交付型態需支援離線開啟，使用者在不連接網路、不啟動本機 server 的情況下，直接打開 Demogame 檔案即可遊玩。

## 3. 參考來源
1. 遊戲流程唯一依據：
   - `Project/Slots/H026_Simulator.py`
2. 參數與資料唯一依據：
   - `Project/Slots/Source/H026_Box.py`
3. 數學資料來源：
   - `Project/Slots/Source/H026_math_data.xlsx`

## 4. 強制相容規範
1. Demogame 不可複製一份新的 paytable / strip / weight 常數到本地硬編。
2. Demogame 必須 `import Project.Slots.Source.H026_Box as Box`，並直接使用 Box 內既有變數。
3. 下列參數名稱與意義必須完全一致：
   - `mode_normalbet`
   - `mode_featurebuy`
   - `normalbet`
   - `featurebuy`
   - `default_coin_in`
   - `window_size`
   - `reel_num`
   - `layout_shape`
   - `paylines`
   - `pay_table`
   - `symbol_id`
   - `symbol_str`
   - `base_symbol_of`
   - `is_gold_symbol`
   - `is_score_symbol`
   - `weight_table_BG`
   - `weight_table_FG`
   - `weight_table_BF`
   - `weight_multiple_special`
   - `weight_multiple_before`
   - `weight_multiple_after`
   - `weight_special_pool`
   - `value_multiplier_range`
   - `drop_weight_a`
   - `drop_weight_b`
   - `arr_reels`
   - `arr_reels_weight`
   - `reels_len`
4. 若 `H026_Box.py` 後續有修正，Demogame 必須自動吃到同一份修正結果，不可出現雙份維護。
5. 若為離線版本，可透過建置步驟將 `H026_Box.py` 資料匯出為前端可讀檔案，但該匯出檔必須視為 `H026_Box.py` 的衍生物，不可改成人工維護常數。

## 5. Bet 與模式規範
1. Demogame 必須支援：
   - `bet_multi`
   - `bet_mode`
2. `coin_in` 計算方式必須與 `H026_Simulator.py` 相同：
   - Normal Bet: `bet_multi * Box.default_coin_in * Box.normalbet`
   - Feature Buy: `bet_multi * Box.default_coin_in * Box.normalbet * Box.featurebuy`
3. 不可新增 Simulator 目前不存在的第三種下注模式。
4. Bet 調整選項必須包含從 `1` 開始的 Bet，第一個可選 Bet 不可大於 `1`。

## 6. 單局流程規範
Demogame 的單局主流程必須對齊 `H026_Simulator.py` 的 `run_spin` 與 `simulator_game` 邏輯。

### 6.1 Base / Feature Buy 入口
1. 若 `bet_mode == Box.mode_normalbet`：
   - 先進行 1 次 BG spin。
   - 若 Scatter 數量 `>= 3`，進入 FG。
2. 若 `bet_mode == Box.mode_featurebuy`：
   - 以 BF 場景起手。
   - 不論 Scatter 是否達 3，都至少給 15 次 FG。
   - 若 Scatter `>= 3`，FG 次數為 `15 + (scatter_count - 3) * 2`。

### 6.2 Spin 內部流程
每個 spin 都必須依以下順序執行：
1. 選 table。
2. 產生初始盤面。
3. 計算 Scatter 數量。
4. 對初始金框派發 multiplier。
5. 判定 paylines。
6. 消除中獎符號。
7. 命中的金框轉 Wild，並把 multiplier 累加到當前 multiplier_sum。
8. cascade 掉落補牌。
9. 重複第 5 到第 8 步，直到盤面無連線。
10. 用 `raw_pay * final_multiplier` 得出該 spin 最終贏分。

### 6.3 Table 選取規則
1. BG 使用 `weight_table_BG`。
2. FG 使用 `weight_table_FG`。
3. BF 使用 `weight_table_BF`。
4. Demogame 顯示用資料必須能知道本次選到哪一組 strip，例如 `B1/B2/B3/F1/F2/F3/BF`。

### 6.4 盤面生成規則
1. 每一軸 reel 都必須依 `arr_reels_weight` 權重決定 stop index。
2. 盤面可視區固定為 `3 x 5`。
3. symbol 顯示值可用 base symbol 呈現，但必須保留 gold flag 與 multiplier 資訊供前端顯示。

### 6.5 連線判定規則
1. 使用 `Box.paylines` 的 20 條線。
2. 由左到右判定。
3. 每條線只取最高獎。
4. Wild 可替代 score symbol，不可替代 Scatter。
5. Scatter 不參與 paylines 賠分。
6. 全 Wild 的情況，規則需與 `H026_Simulator.py` 的 `evaluate_board` 一致，也就是依最高可得 pay 的 score symbol 解讀。

### 6.6 金框與倍率規則
1. 金框 symbol 顯示上屬於 base symbol 的金框版本。
2. 初始盤面的金框 multiplier 指派規則必須與 `assign_initial_multiplier` 一致。
3. Cascade 掉落新增的金框 multiplier 指派規則必須與 `assign_drop_multiplier` 一致。
4. 金框只有在該格被命中消除時，才會：
   - 轉成 Wild
   - 將其 multiplier 加入累積倍率
5. 沒有被命中的金框，不可提前進帳倍率。

### 6.7 Special Pool 規則
1. 只在 `table_id < 3` 的 BG strip 生效。
2. 是否啟動取決於：
   - 盤面金框數量
   - `weight_special_pool[min(gold_count, 9), table_id]`
3. 若啟動：
   - 只隨機挑 1 個金框走 `weight_multiple_special`
   - 其他金框走 `weight_multiple_before`
4. 若未啟動：
   - 所有初始金框都走 `weight_multiple_before`
5. FG 與 BF 不可啟動 Special Pool。

### 6.8 Cascade 掉落規則
1. 每個 spin 開始時，先 50/50 決定本次使用 `Drop A` 或 `Drop B`。
2. 同一個 spin 的所有 cascade 必須共用同一套 drop table。
3. 命中金框的格子在消除階段標記為保留轉 Wild，不直接清空。
4. 非金框命中格才真正移除並由上方掉落補牌。
5. 新補入的金框 multiplier 使用 `weight_multiple_after`。

### 6.9 FG 累積倍率規則
1. BG 的 `multiplier_sum` 每個 spin 都從 0 開始。
2. FG 的 `multiplier_sum` 必須跨 spin 延續。
3. Retrigger 後延長的 FG spin 也要延續同一個 `multiplier_sum`。
4. 整段 FG 結束後才歸零。
5. 畫面上必須持續顯示目前累積倍率，且 FG 每次進入下一場時需延續上一場結束時的累積倍率。

## 7. Demogame 狀態輸出規範
Demogame 不是只回傳最終分數，還必須能輸出試玩用的過程資料。

### 7.1 單次遊戲回傳資料
至少需包含：
1. `bet_mode`
2. `bet_multi`
3. `coin_in`
4. `base_spin`
5. `free_spins_awarded`
6. `free_spins_played`
7. `total_win`
8. `base_total_win`
9. `free_total_win`
10. `final_fg_multiplier_sum`
11. `spins`
12. `rtp_overall`
13. `hit_rate_overall`
14. `freegame_trigger_count`

### 7.2 單個 spin 回傳資料
每個 spin 至少需包含：
1. `scene_mode`
2. `scene_name`
3. `table_id`
4. `table_name`
5. `drop_mode`
6. `rng_info`
7. `scatter_count`
8. `raw_pay`
9. `final_multiplier`
10. `final_pay`
11. `multiplier_sum_before_spin`
12. `multiplier_sum_after_spin`
13. `board_init`
14. `board_steps`
15. `line_wins`
16. `line_win_total`

其中 `rng_info` 至少需包含：
1. table 選取 RNG
2. 每軸 reel 的 stop RNG
3. 本次 spin 使用的 drop mode RNG
4. 若有新補牌，需能追到該次補牌的 RNG 紀錄

### 7.3 board_steps 規範
每一次 cascade 過程至少需保留：
1. 判定前盤面
2. 命中位置
3. 命中線資料
4. 消除後盤面
5. 掉落後盤面
6. 本輪增加的 multiplier
7. 本輪 cascade pay

### 7.4 line_wins 規範
每個 spin 的 `line_wins` 至少需保留每條已命中線的以下資訊：
1. `line_index`
2. `symbol_id`
3. `symbol_name`
4. `line_length`
5. `line_pay`
6. `positions`
7. `cascade_index`
8. `is_triggered_by_wild`

### 7.5 統計欄位定義
1. `rtp_overall`
   - 定義為累計 `total_win / total_bet`
   - 若 Demogame 支援單局試玩，至少需能顯示目前 session 累積 RTP
2. `hit_rate_overall`
   - 定義為累計「有任一命中之 spin 次數 / 總 spin 次數」
   - Base 與 FG spin 都需納入 overall 計算
3. `freegame_trigger_count`
   - 定義為 session 內觸發免費遊戲的總次數
   - Normal Bet 的自然觸發與 Feature Buy 入口需分開標記來源，至少內部資料要可區分

## 8. 顯示層規範
1. Demogame UI 或輸出層不得自行重算得分。
2. UI 只能讀取核心邏輯輸出的結果資料。
3. 盤面顯示需能區分：
   - 一般 symbol
   - Gold symbol
   - Wild
   - Scatter
   - 金框對應倍率
4. 資訊欄位必須顯示當次 spin 的輪帶 RNG 資訊，至少可看到 table、各 reel stop 與 drop mode。
5. 每個 symbol 格上需顯示對應的代號文字，例如 `M1`、`M2`、`M3`、`M4`、`M5`、`A`、`K`、`Q`、`J`、`WW`、`C1`。
6. FG 狀態需明確顯示：
   - 剩餘 free spins
   - 目前累積 multiplier_sum
   - 是否 retrigger
7. 第一版可玩版本不得依賴網路連線；使用者直接開啟 Demogame 檔案後即可進行遊戲。
8. 若採離線版 HTML 實作，不可依賴遠端 API、遠端資源或本機 web server 才能進行基本遊玩流程。

## 9. 畫面風格參考規範
本 Demogame 的畫面風格以使用者提供的參考圖為基準，定位為「手機直式、糖果科幻、強霓虹外框、亮面玩具質感」。

### 9.1 畫面構圖
1. 採直式手機版面，主視覺比例以 9:16 為基準。
2. 畫面自上而下分為：
   - 遊戲 ID + 名稱
   - 遊戲特色區
   - 盤面
   - 特殊押住按鈕
   - 玩家資訊
   - 基本按鈕
   - 詳細遊戲數據
3. 主盤面區必須是整個畫面的視覺核心，占最大面積。
4. 上述區塊名稱是「版面定義名稱」，只作為設計與開發溝通用途，不直接顯示在遊戲畫面上。

### 9.2 視覺語言
1. 背景風格採太空 / 星空 / 發光粒子，不使用純色平面背景。
2. 主色系以藍紫、桃紅、螢光橘、亮青為主。
3. 外框與面板需要明顯霓虹描邊、發光暈染與高對比漸層。
4. 按鈕與盤面卡片需有糖果感、果凍感或塑膠亮面質感。
5. 字體表現以粗體、外光、描邊、醒目數字為主，不能做成過於樸素的企業後台風格。
6. FG 場景的整體主色、背景或主要面板配色必須與 BG 有明顯區隔，不能只改一小段文案或數字顏色。

### 9.3 遊戲 ID + 名稱區
1. 畫面最上方只保留一個主標題區塊。
2. 此區顯示內容固定為：
   - 遊戲 ID，例如 `GAME ID H026`
   - 遊戲名稱，例如 `H026 DEMOGAME`
   - 可保留一行副標題文案
3. 不顯示 Jackpot 區塊，不預留 GRAND / MAJOR / MINOR / MINI 的版位。
4. 遊戲區塊名稱本身不顯示在畫面上。

### 9.4 遊戲特色區
1. 遊戲 ID + 名稱區下方需有一條獨立資訊帶，作為遊戲特色展示區。
2. 目前此區的主要用途是顯示：
   - 當前遊戲模式
   - 當前累積 multiplier
   - 當次 spin 的累積 multiplier
   - 剩餘 free spins
   - 目前累積倍率
3. 若遊戲處於 FG，這一區必須高亮顯示目前 `multiplier_sum` 與剩餘 `free spins`。
4. 若有 retrigger，需在這區或主盤面上方做一次明確提示。
5. `RTP / Hit Rate / Free Game Trigger Count` 不放在這一區，統一移到最下方的詳細遊戲數據區。
6. 累積倍率顯示不可只在命中當下短暫出現，需在平時待機畫面也能看見目前值。

### 9.5 主盤面區
1. 主盤面維持 H026 實際數學規格的 `3 x 5` 顯示。
2. 每格 symbol 容器需有獨立底板，風格參考圖片中的發光玻璃卡槽。
3. 盤面 symbol 圖片必須優先使用：
   - `Project/Slots/Source/Image/P026_Symbol`
4. 必須使用的圖片至少包含：
   - `pinata-wins_symbol_h1_chilli.png`
   - `pinata-wins_symbol_h2_taco.png`
   - `pinata-wins_symbol_h3_maracas.png`
   - `pinata-wins_symbol_h4_sombrero.png`
   - `pinata-wins_symbol_h5_skull.png`
   - `pinata-wins_symbol_l1_j.png`
   - `pinata-wins_symbol_l2_q.png`
   - `pinata-wins_symbol_l3_k.png`
   - `pinata-wins_symbol_l4_a.png`
   - `pinata-wins_symbol_s_scatter.png`
   - `pinata-wins_symbol_s_wild.png`
   - `pinata-wins_symbol_s_frame_bg.png`
   - `pinata-wins_symbol_s_frame.png`
5. Scatter 需要有明顯特殊標記，不能只用一般字串顯示。
6. Wild、Gold symbol、命中中的 symbol，三者視覺上必須能快速區分。
7. Gold symbol 需以 `frame_bg + symbol + frame` 的方式疊出金框效果，必要時可搭配倍率徽章。
8. 命中後必須能看出「是什麼獎項得分已連線」，不可只顯示總贏分。
9. Symbol 圖上需額外覆蓋對應代號文字，不能只靠圖像辨識。

### 9.6 特殊押住按鈕
1. 主盤面下方需保留一個顯眼的大型特殊按鈕區。
2. 此區預設用於放置 `BUY FEATURE`。
3. 視覺上需明顯強於一般控制按鈕。
4. 此區不顯示區塊名稱文字。

### 9.7 玩家資訊
1. 盤面下方需顯示至少三個欄位：
   - Balance
   - Bet
   - Win
2. 數字區需使用大字體，方便試玩時快速確認結果。
3. 欄位需對應 Demogame 真實狀態，不可只顯示假文案。

### 9.8 基本按鈕
1. 底部需保留常見 slot 控制項：
   - Setting
   - Bet 調整
   - Spin
   - Auto
   - Turbo
2. `Spin` 必須是底部視覺中心。
3. `Auto` 與 `Turbo` 可以先做 UI 預留；若第一版未實作功能，需明確標註 disabled 狀態。
4. 若遊戲進入 FG，必須支援由玩家每按一次 `Spin` 才執行下一場 FG spin，不可強制自動連播整段 FG。
5. 若 FG 採手動逐場模式，需避免玩家在 FG 中途誤開新局；必要時可暫時鎖住 `Bet` 與 `Buy Feature`。

### 9.9 詳細遊戲數據
1. 所有詳細數據統一放在最下方。
2. 此區至少包含兩組資訊：
   - session 統計摘要
   - 當前或最近一次命中的詳細資料
3. session 統計摘要至少顯示：
   - `RTP`
   - `Hit Rate`
   - `Free Game Trigger Count`
4. 命中詳細資料至少顯示：
   - 命中 symbol 名稱
   - 連線長度
   - `line pay`
   - `total win`
   - retrigger 或 FG 狀態提示
5. 這一區可視為原本參考圖中的第 2、3 組資訊區，需放在介面最下方，不可提前放到頂部。

### 9.10 動畫規範
1. Spin 開始時，輪帶需有滾動感或 reel spin 動畫，不能只瞬間切換成最終結果。
2. 命中連線後，命中格需有高亮、放大、閃爍或發光效果。
3. 金框命中轉 Wild 時，需有明確的轉換演出。
4. Cascade 掉落時，需有由上而下補位動畫。
5. Multiplier 增加時，需跳出對應的 `xN` 演出。
6. FG 觸發與 retrigger 必須有獨立大提示動畫。
7. FG 場景的每一次手動 spin 仍必須有輪帶滾動演出，不可因為是免費遊戲就省略 reel spin 動畫。
8. BG 場景若該次 spin 最終已無後續消除，收尾畫面不可額外保留贏分線高亮作為最終停格；最終停格應回到正常盤面顯示。

### 9.11 響應式規範
1. 第一優先版型為手機直式。
2. 若在桌面端開啟，需保持直式主舞台置中，不可任意拉寬盤面比例。
3. 寬螢幕可在左右兩側保留背景延伸或裝飾區，但主盤面比例不可被破壞。

## 10. 程式結構建議
Demogame 建議拆成以下責任：
1. `Box`：
   - 只負責讀資料與提供常數、權重、符號定義。
2. `Game Logic`：
   - 以 `H026_Simulator.py` 的 spin 邏輯為主體，抽成可重用的單局遊戲流程。
3. `Presenter / Serializer`：
   - 將盤面、倍率、命中線、FG 狀態整理成前端好接的結構。
4. `UI / Demo Entry`：
   - 接下注參數，呼叫單局遊戲，顯示結果。

## 11. 禁止事項
1. 不可把 `Simulator` 的統計 record 機制直接當作 Demogame 必要輸出。
2. 不可為了 UI 方便而改寫數學結果。
3. 不可讓前端自己抽權重、自己算連線、自己算 multiplier。
4. 不可在 Demogame 中硬編任何 H026 專屬 paytable 或 strip 資料。
5. 不可把 Feature Buy 保底 15 FG 的規則遺漏。
6. 不可做成過於簡陋的 debug 盤面風格，例如純 HTML table、純文字按鈕、無狀態層級的測試頁。
7. 不可直接照抄參考圖的遊戲名稱、symbol 美術或品牌元素；只能借用畫面結構與視覺方向。
8. 不可把「離線可玩」做成名義上的功能，但實際仍要求使用者啟動本機 server、安裝外掛或連接網路後才能遊玩。

## 12. 驗收條件
1. 同一組隨機種子下，Demogame 的單 spin 結果必須可與 `H026_Simulator.py` 對齊。
2. 對齊項目至少包含：
   - table 選擇
   - 初始盤面
   - scatter_count
   - 每輪 cascade pay
   - multiplier 累積
   - spin 最終贏分
3. Normal Bet 與 Feature Buy 都必須能完成整局流程。
4. FG retrigger 後的剩餘轉數與倍率累積必須正確延續。
5. 畫面需符合本文件第 9 節的直式 slot 版位要求。
6. UI 必須能在單次 spin 後看出：
   - 初始盤面
   - 命中結果
   - cascade 後盤面
   - 當前 Win
   - FG 狀態
   - multiplier 狀態
   - 輪帶 RNG
   - symbol 代號標示
   - reel 滾動演出
   - 目前累積倍率
   - FG 剩餘場次
   - BG 與 FG 的場景配色差異
7. UI 或資料層必須能明確查到：
   - 什麼獎項得分已連線
   - 總 RTP
   - 總 Hit Rate
   - 免費遊戲觸發次數
8. 直接雙擊 Demogame 主檔或使用同級啟動檔時，必須能在離線狀態完成遊玩流程。
9. 進入 FG 後，玩家必須可以用逐次按 `Spin` 的方式完成每一場 FG spin。

## 13. 建置結論
H026 Demogame 應視為 `H026_Simulator.py` 的「單局可視化版本」，不是另一套數學模型。所有盤面邏輯與參數來源必須回到 `H026_Simulator.py` 與 `H026_Box.py`，其中 `H026_Box.py` 是參數唯一來源，`H026_Simulator.py` 是流程唯一來源。任何後續實作若與這兩份檔案不一致，應視為規格違反。
