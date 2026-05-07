# Slot Demogame 設計規範

> 檔名：`slot_demogame_standards.md`
> 用途：作為未來所有新遊戲建立 Demogame 時的共用設計標準。

## 1. 文件目的與適用範圍

1. 建立一套可直接複用的 Demogame 共用設計標準。
2. 本文件適用於未來所有新遊戲的 Demogame，不是只給單一遊戲使用。
3. 本文件規範的重點包括：
   - 檔案結構
   - UI 區塊定義
   - 互動方式
   - 狀態切換
   - 資料綁定
   - debug 資訊
   - 響應式與錯誤處理
   - 最低驗收標準

## 2. 技術形式規範

1. Demogame 必須使用 `HTML` 作為主介面載體。
2. 建議技術分工如下：
   - `HTML`：負責 UI 結構與區塊容器
   - `CSS`：負責樣式、版型、響應式與狀態視覺
   - `JavaScript`：負責資料綁定、互動事件、狀態切換與盤面 render
3. 必須能直接開啟 HTML 進行操作。

## 3. 檔案結構規範

Demogame 資料夾至少應包含：

1. `Demogame.html`
2. `config.js`
3. `Image` 素材資料夾，若無素材則至少可退化為文字顯示

## 4. 畫面結構規範

Demogame 應採單頁式結構，至少包含以下 UI 區塊：

1. Header / Hero 區
2. Feature 狀態列
3. Reel Board / 主盤面區
4. Message Bar / 訊息列
5. 特殊押注按鈕區
6. Player Info / 玩家資訊區
7. 主控制列
8. Session 統計區
9. Line Wins 區
10. RNG 區
11. Spin Result 區

## 5. UI 區塊定義

### 5.1 Header / Hero 區

最少應顯示：

1. `DEMOGAME`
2. 遊戲名稱

補充：

1. 若專案要求顯示 PARsheet ID，應明確定義格式。
2. 若專案要求固定中文名，則不應直接沿用 config 中的舊英文名或臨時測試名。

### 5.2 Feature 狀態列

最少應顯示：

1. 與該遊戲玩法直接相關的 Feature 狀態
2. 若玩法有累積值，必須顯示累積過程，而不是只顯示最終結果
3. 若玩法在 cascade 中會變化，必須每次 cascade 即時刷新
4. 若玩法在 FG 中會變化，必須每次 FG spin / cascade 即時刷新
5. 若該遊戲的單次 spin 有消除次數概念，應顯示本次 spin 的消除次數
6. 若該遊戲有 Free Game，應支援在 FG 期間顯示 `剩餘場次 / 總場次`

規則：

1. 顯示內容應依遊戲玩法客製，不要求所有遊戲完全相同。
2. 使用哪張表不放在這一區，應顯示在 `RNG 區`。
3. `FG Left` 顯示規範：
   - BG 期間不顯示
   - FG 期間顯示 `剩餘場次 / 總場次`
   - 總場次在進入 FG 時應固定
   - 只有在發生 retrigger 後，總場次才可增加

### 5.3 Reel Board / 主盤面區

最少應支援：

1. 固定盤面顯示
2. symbol 圖示顯示
3. symbol code 顯示
4. scatter 標記
5. gold / special / multiplier 標記
6. hit 高亮
7. convert 高亮
8. reel spin 動畫或等效播放效果

規則：

1. 畫面滾動時，應優先使用真實輪帶資料做動畫。
2. BG 用 BG 輪帶，BF 用 BF 輪帶，FG 用 FG 輪帶。
3. 不應只用隨機假符號做純裝飾滾動。

### 5.4 Message Bar / 訊息列

最少應顯示：

1. loading 狀態
2. spin 中狀態
3. cascade 中狀態
4. FG 觸發狀態
5. spin 完成狀態
6. error 狀態

### 5.5 特殊押注按鈕區

可能玩法：

1. `Extra Bet`
2. `Buy Feature`
3. `Super Feature`

規則：

1. `Extra Bet` 應為開關式控制。
2. `Extra Bet` 開啟後，每次按 `Spin` 都應使用 Extra Bet 對應的輪帶或表。
3. `Buy Feature` 與 `Super Feature` 為一次性購買按鈕。
4. 若規則要求 `Buy Feature` 或 `Super Feature` 進場盤面必須滿足條件，例如 `3+ Scatter`，則 Demogame 必須在背景重抽直到達標。
5. 背景重抽過程：
   - 不可重複扣錢
   - 不可計算中間得分
   - 不可進統計
6. 若遊戲沒有 `Extra Bet` 或 `Super Feature`，則不應顯示對應按鈕。
7. 不應為了版面一致而硬保留不存在的按鈕。

### 5.6 Player Info / 玩家資訊區

最少應顯示：

1. `Balance`
2. `Bet`
3. `Win`

規則：

1. 若內部以 point / credit 計算，畫面以錢顯示，必須明確提供 `DENOM` 或固定換算規則。
2. 所有玩家可見金額顯示必須套用同一套換算規則，包括：
   - Balance
   - Bet
   - Win
   - Line Wins
   - Buy Feature 成本
3. `Win` 不可在進入 FG 後直接顯示整段 FG 最終結果。
4. `Win` 至少要在每顆 spin 播放完成後即時更新。
5. 若遊戲有 cascade，建議 `Win` 在每次消除時即時更新。
6. `Balance` 不可在進入 FG 後直接顯示整段 FG 結算後的最終值。
7. `Balance` 必須先扣款，再隨播放進度逐步補回贏分。

### 5.7 主控制列

最少應包含：

1. `Reset`
2. `Bet`
3. `Spin`
4. `Auto`
5. `Turbo`

規則：

1. `Reset` 必須可重置 session 統計與狀態。
2. `Bet` 必須能切換 bet 檔位。
3. 若玩家看到的是金額 bet，畫面應直接顯示金額，不是內部 bet multi。
4. 若內部仍需轉回 bet multi，必須有明確公式。
5. `Auto` 必須為開關式控制，開啟後自動旋轉。
6. `Turbo` 必須為開關式控制，開啟後以兩倍速進行遊戲流程播放。
7. 若進入 FG 流程，`Spin` 必須切換為 `Next FG` 或其他等效文字。

### 5.8 Session 統計區

最少應顯示：

1. `RTP`
2. `Hit Rate`
3. `FG Trigger`

規則：

1. `FG Trigger` 必須同時顯示觸發率與觸發週期。
2. 顯示格式建議為：`0.01% (1000場)`。
3. `FG Trigger` 不應計入 `Buy Feature / Super Feature` 直接進場。
4. `FG Trigger` 應只計自然觸發，除非專案另有定義。

### 5.9 Line Wins 區

最少應顯示：

1. line index
2. symbol
3. line length
4. cascade index
5. line pay

補充：

1. 若顯示 `C1 / C2 / C3`，必須在文件中定義其意義為 cascade 次數。

### 5.10 RNG 區

最少應顯示：

1. 使用哪張表
2. drop mode RNG
3. 各 reel 的 stop index
4. 各 reel 的 RNG 值與範圍

### 5.11 Spin Result 區

最少應顯示：

1. 本次 `spin` 的初始盤面結果
2. 每個 `cascade n` 的盤面結果
3. 若有更多階段，可依序列出

## 6. 狀態切換規範

### 6.1 Cascade

1. `Feature 狀態列` 若有累積值或階段性變化，必須在每次 cascade 即時更新。
2. `Spin Result 區` 必須追加對應的 cascade 盤面結果。
3. 若有 `Win` 遞增展示需求，應在每次 cascade 同步更新。

### 6.2 FG

1. `FG Left` 若該遊戲有此資訊，必須更新。
2. `Win` 與 `Balance` 若為玩家可見資訊，必須依播放進度逐步更新，不可一進 FG 就先結清整段結果。

## 7. 資料綁定規範

### 7.1 config 建議綁定欄位

至少應可從 `config` 取得：

1. `game_id`
2. `game_name`
3. `bet_options`
4. `mode_normalbet`
5. `mode_featurebuy`
6. 與特殊押注相關的 mode / table / flag 欄位
7. `reel_num`
8. `window_size`
9. `paylines`
10. `symbol_id`
11. `symbol_str` 或等效欄位
12. `denom` 或等效換算規則

### 7.2 spin result 建議綁定欄位

至少應可從 `spin result` 或 `round result` 取得：

1. `bet_mode`
2. `coin_in`
3. `total_win`
4. `spin_index`
5. `scene_name`
6. `table_name`
7. `drop_mode`
8. `scatter_count`
9. `feature_values` 或等效欄位
10. `remaining_free_spins_before`
11. `remaining_free_spins_after`
12. `board_init`
13. `board_final`
14. `board_steps`
15. `line_wins`
16. `rng_info`
17. `retrigger_awarded`

## 8. 最低驗收標準

一個合格的新 Demogame 至少必須做到：

1. 開啟 HTML 即可操作
2. 可進行 normal spin
3. 可進行特殊押注玩法
4. 可展示 free game 流程
5. 可顯示 line win 結果
6. 可顯示 session 基本統計
7. 可顯示基本 RNG / trace 資訊
8. 可顯示每次 spin 與 cascade 的結果盤面
9. 可依播放進度更新 Feature / Win / Balance
