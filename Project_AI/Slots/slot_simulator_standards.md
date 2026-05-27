# Slot Simulator 建置規範

## 1. 用途

這份文件用來規範新遊戲 `simulator.py` 的建置方式，目標是讓每款新遊戲的模擬程式都具備一致的：

* 設定區結構
* `Numba` 模擬核心
* console 結果顯示格式
* xlsx 報表輸出格式

若有可參考的既有 simulator，可在實作時附上作為參考；H015 只是可參考案例之一，不是必要依據。

## 2. 必要輸入

新建模擬程式時，至少應具備：

* 遊戲玩法規則文件
* 數學資料來源
* 本規範文件

若有前一款相近玩法的 simulator，可作為實作參考，但新遊戲仍需依自己的玩法、數學與輸出需求整理程式，不可直接複製後缺少必要調整。

## 3. 程式結構要求

`simulator.py` 至少應包含：

* 匯入區
* 使用者可直接修改的前段設定區
* 數學資料載入區
* `Numba` 模擬核心
* 結果整理區
* console 顯示區
* xlsx 報表輸出區

參數資料應統一由 `config` 載入，建議集中管理下列內容：

* 遊戲名稱與版本
* 盤面大小
* 符號定義
* paytable
* 輪帶或權重資料
* 下注模式常數
* 統計欄位定義
* 報表輸出路徑與檔名規則

## 4. 前段可調整設定區

以下項目必須集中放在程式前面，使用者打開檔案後能直接修改，不可分散在程式中段或函式內：

* 是否輸出報表開關
* 執行多少次模擬
* 押注模式設定
* 平行計算線程數

建議一併放在同區的設定：

* 是否顯示 console 固定結果
* 是否顯示 console by-game 結果
* 是否顯示倍率線型或其他圖表
* bet multiplier / bet amount
* debug spin 開關

下注模式至少要能在前段直接切換以下模式：

* `Normal Bet`
* `Extra Bet`
* `Buy Feature`
* `Super Feature`

線程數必須可以在前段直接指定，例如：

* `THREADS = 8`

模擬次數必須可以在前段直接指定，例如：

* `TOTAL_ROUNDS = 10**8`

報表輸出開關必須可以在前段直接指定，例如：

* `OUTPUT_REPORT = True`

## 5. 模擬核心要求

### 5.1 必須使用 Numba

大量模擬的核心路徑必須使用 `Numba` 加速，不可退化成只用純 Python 迴圈跑大量 round。

要求如下：

* 核心模擬函式必須使用 `@njit`、`@jit(nopython=True)` 或等價 `Numba` 路徑
* 若有平行化需求，應搭配既有多線程封裝或等價實作
* 若有單局 trace / debug 模式，可保留純 Python 可讀版本，但大量模擬不可走這條路徑

### 5.2 平行計算

若 simulator 支援平行計算：

* 線程數必須可在程式前段直接修改
* 大量模擬時應明確走平行化入口
* 最終彙總結果必須回收到同一份 `record_data` 或等價統計資料結構

### 5.3 單局與批次模式

至少應提供：

* 單局 `spin` / debug 模式
* 批次 `simulate` 模式

`spin` 用來驗證盤面、流程、符號行為與 feature 邏輯；`simulate` 用來跑大量模擬並輸出統計結果。

## 6. 執行完成後的顯示要求

執行完成後，必須直接顯示結果；若有可參考的既有 simulator，可在實作時附上作為顯示格式參考。

console 顯示至少要拆成兩個區塊：

* 固定結果區塊
* by game 特定結果區塊

### 6.1 固定結果區塊

固定結果區塊用來放每款遊戲都應有的摘要資訊，至少包含：

* 遊戲名稱或代號
* bet / coin in
* bet mode
* total rounds
* duration
* RTP
* 各主要 RTP 拆分
* hit rate
* feature trigger rate
* max win

若遊戲有 free game、bonus game、respin 或其他主要場景，建議同步列出：

* 各場景 RTP
* 各場景 hit rate
* 平均 feature 次數
* retrigger 機率
* standard deviation
* median / positive index

### 6.2 by game 特定結果區塊

這個區塊用來放該遊戲特有、只有這款遊戲才需要觀察的結果；若有可參考的既有 simulator，可在實作時附上作為分區格式參考。

依遊戲需求可包含：

* hits 表
* rtp 表
* eliminate / combo / cascade 表
* multiplier line
* 特殊符號出現次數
* feature 專屬統計
* 盤面特有機制的命中率或使用率

要求如下：

* 固定結果與 by game 結果不可混在同一區塊隨意輸出
* 區塊標題需明確
* 欄位命名需可讀，不可只留內部縮寫而無法判讀

## 7. 報表輸出要求

執行完成後，必須具備輸出報表功能；若有可參考的既有 simulator，可在實作時附上作為報表格式參考。

### 7.1 報表開關

是否輸出報表必須由程式前段開關控制，使用者不需要改函式呼叫處或程式尾端。

### 7.2 輸出格式

報表格式以 xlsx 為主，建議至少包含：

* `Base Info`
* `Multiplier Line`
* `Record Data`

若遊戲有類似的明細表需求，建議一併輸出：

* `Hits`
* `Pay`
* `Eliminate`

若實作上採既有 simulator 的合併方式，也可將 base 與 detail 整理後輸出到同一主工作表，但至少要保留：

* 固定摘要資訊
* by game 明細資訊
* 原始統計資料

### 7.3 報表內容

`Base Info` 至少應對齊 console 固定結果區塊的主要欄位。

by game 報表至少應對齊 console by-game 區塊的主要欄位，例如：

* 各 symbol hit rate
* 各 symbol pay / RTP
* 各 combo / eliminate 統計
* feature 專屬統計

`Record Data` 或等價工作表應保留原始統計資料，方便後續追查與二次分析。

### 7.4 檔名與輸出位置

輸出檔名建議包含：

* 遊戲名
* 時間戳
* bet mode

例如：

* `GameName_YYMMDDHHMM_betmode0.xlsx`

輸出路徑應集中定義，不可散落在多處硬編碼。

## 8. 統計資料設計要求

模擬統計建議維持固定結構，例如：

* base info 需要的累加欄位
* multiplier line 欄位
* hits 欄位
* pay 欄位
* eliminate 欄位
* 各 feature 專屬欄位

若採 `record_data` 二維陣列或等價結構：

* index 定義必須集中管理
* 各區段用途必須可讀
* 不可把 magic number 散落在 simulator 內文

## 9. 建置限制

* 不可省略 `Numba` 大量模擬加速路徑
* 不可把報表輸出開關藏在程式尾端
* 不可把模擬次數藏在函式內
* 不可把 bet mode 寫死在模擬核心內
* 不可把線程數寫死在平行計算封裝內而無法前段修改
* 不可在執行完成後只有 raw data 而沒有整理後的顯示結果
* 不可只有固定摘要而沒有 by game 特定結果區塊
* 不可只有 console 顯示而沒有報表輸出能力

## 10. 新遊戲最低交付標準

新遊戲 simulator 至少必須做到：

* 可直接在程式前段修改模擬次數
* 可直接在程式前段修改 bet mode
* 可直接在程式前段修改報表輸出開關
* 可直接在程式前段修改平行計算線程數
* 大量模擬走 `Numba` 加速
* 執行後顯示固定結果區塊
* 執行後顯示 by game 特定結果區塊
* 執行後可輸出 xlsx 報表

若缺少以上任一項，視為未符合新遊戲 simulator 建置規範。
