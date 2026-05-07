# Standalone Slot 模擬器建置規範

## 1. 必要檔案

每一款 standalone slot 模擬器資料夾，至少應包含以下四個檔案：

* `simulator.py`
* `demogame.html`
* `config.js`
* `slot_simulator_standards.md`

這四個檔案必須放在同一層目錄，並能直接互相配合使用。

## 2. 建置目標

這份規範只定義 standalone 模擬器的建置方式。

目標是讓新遊戲在提供下列資料後，可以快速建立出同型的 standalone 套件：

* 遊戲玩法規則文件
* 數學資料來源
* 上一款 standalone 模擬器作為範本
* 本規範文件

這份規範不要求其他外部專案固定檔名，也不應提到不相關的正式專案結構。

## 3. 各檔案責任

### `config.js`

`config.js` 是 `simulator.py` 和 `demogame.html` 共用的主要參數來源。

內容至少應包含：

* 遊戲代號與名稱
* 盤面大小
* 押注選項
* Buy Feature 價格
* Free Game 場數規則
* 符號定義
* 賠率表
* 線型定義
* 輪帶或權重資料
* 金框與倍數設定
* DemoGame 會使用到的圖片路徑

規則：

* `config.js` 可以是純 JSON 內容，也可以是 `window.xxx = {...};` 形式。
* 若專案仍需要保留 `config.json`，它只能作為相容或中間產物，不應作為主要讀取檔。
* 如果數學資料原始來源是 xlsx，應先轉成 `config.js` 再提供模擬程式與 HTML 使用。

### `simulator.py`

`simulator.py` 是 standalone 模擬程式入口。

至少應提供：

* 單局 `spin` 除錯模式
* 批次 `simulate` 模擬模式
* xlsx 報表輸出
* console summary 快速檢查資訊

`simulator.py` 必須直接讀取同資料夾內的 `config.js`。

模擬核心規則：

* `simulate` 必須使用 `Numba` 加速路徑，不可只用純 Python 迴圈跑大量 round。
* 若已有既有正式 simulator 可重用，`simulate` 可直接串接既有 Numba 路徑。
* `spin` 可保留 standalone 的 Python trace/debug 邏輯，方便閱讀單局結果。

互動執行規則：

* 沒帶參數時，要能用預設值直接執行
* 預設路徑必須以 `simulator.py` 自己所在位置為基準
* 啟動時應顯示實際使用的 config 路徑
* `Rounds`
* `Bet Mode`
* `Bet`
* `Output XLSX`

上述預設值應集中放在檔案前段，讓使用者一打開就能直接修改。

報表輸出規則：

* 直接執行時，若未另外指定，應自動輸出 xlsx。
* 預設輸出位置應為 standalone 資料夾內的 `Record`。
* 檔名格式應固定，例如：`遊戲名_YYMMDDHHMM_betmode0.xlsx`
* `betmode0` 代表 normal bet，`betmode2` 代表 feature buy。

### `demogame.html`

`demogame.html` 是本地試玩的 HTML。

至少應提供：

* 讀取 `config.js`
* 使用本地 `Source/Image` 的圖片
* 一般 Spin
* Buy Feature
* 顯示目前 Bet、Win、模式、FG 狀態
* 被消除的格子保持空白，不顯示 `EMPTY`

若直接雙擊 HTML 開啟時，應優先支援 `config.js` 這種不依賴 `fetch json` 的方式。

### `slot_simulator_standards.md`

這份文件只用來描述 standalone 模擬器規範。

內容不應依賴其他專案的固定架構，也不應把不相干的檔名或路徑寫進來。

## 4. 共用邏輯一致性

`simulator.py` 與 `demogame.html` 必須對齊以下內容：

* 符號代碼
* 賠率表
* 線型
* FG 觸發邏輯
* Buy Feature 價格
* 倍數清單
* 金框行為

若兩者有差異，應以 `config.js` 為準。

## 5. 輸出規範

### Console Summary

`simulator.py` 至少應輸出：

* 遊戲代號
* Bet
* Rounds
* Bet Mode
* Duration
* RTP
* Hit Rate
* FG Trigger Rate
* Max Win
* Output XLSX

### XLSX 報表

若需要輸出 xlsx，至少應包含：

* `Base Info`
* `Multiplier Line`
* `Hits`
* `Pay`
* `Eliminate`
* `Record Data`

## 6. 建置限制

* 所有預設路徑應以 standalone 資料夾內的相對位置為主
* 圖片路徑盡量收進 `config.js`
* `simulator.py` 的預設參數應集中在檔案前段，方便修改
* `simulate` 不可退化成沒有 `Numba` 的大量模擬版本
* 若重用既有正式 simulator，只能把它當作 `simulate` 的 NumPy / Numba engine，standalone 對外介面仍應維持本規範定義
* 如果瀏覽器本地 `fetch` 被擋住，`demogame.html` 應明確顯示錯誤，不可靜默失敗

## 7. 新遊戲最小輸入包

如果下次要做新遊戲，最少建議提供：

* 遊戲玩法規則文件
* 數學資料檔
* 上一款 standalone 模擬器整包
* 本規範文件

如果只有玩法文件，沒有數學資料，最多只能做出骨架版：

* 可以做出 `simulator.py`
* 可以做出 `demogame.html`
* 可以做出 `config.js` 欄位模板

但不能保證：

* RTP 正確
* Feature 觸發率正確
* 報表統計正確
* 與正式數學結果一致
