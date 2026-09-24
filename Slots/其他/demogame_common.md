# Demo Game 共用模組

所有遊戲的 `index.html` 共用：

- `demogame_common.css`：遊戲資訊、盤面、Credit、Play、Bet Mode、Stats、Debug、Setting 與 Help 的 UI/UX，所有主要區塊使用一致的淡色外框。
- `demogame_common.js`：共用初始化、Setting 結構正規化、Config／Player 合併、Version 顯示、Bet Mode 無障礙狀態、Help 樣式與 Markdown／賠率表標準化。原本的 `help_ui_standardizer.js` 已完整併入此檔案。

Setting 會統一整理成左側開關群組與右側設定／操作群組。Config 與 Player 合併成單一選單（例如 `92A-Oldhand`），並在旁邊顯示目前數學模型的 Version；舊模型未提供版本欄位時顯示 `Current`。

Debug 面板以 10px 間距排列，不讓相鄰外框黏在一起。若頁面同時存在 `#change-log-wrap` 與 `#batch-simulation`，共用模組會自動將 Simulation 放到 Change Log 後面；沒有 Change Log 的遊戲則保留原位置。

共用區塊標題統一使用與 `LOG` 相同的 12px 字級、字重與字距，英文以大寫顯示。Simulation 不顯示 Config／Version／Card System／Bet 的說明行，並固定與前一個區塊保留 10px 間距。

Settings 的數學模型欄位順序統一為 `Version → Config → Language`。

Reel RNG 與 Spin Result 的內容列共用相同的 12px 字級、左右欄、間距與底色；空白 RNG 區顯示等待狀態。使用逐格加權抽取、沒有 reel stop 的模型會顯示實際數學表來源與 `weighted draw`，不產生虛構 stop 值。

H015 的 Cascade 動畫使用共用 drop motion：中獎符號先消除、既有符號向下移動，新符號再由盤面上方掉入補牌。

`demogame_common.js` 另提供 opt-in 的 `window.slotFx` 動畫模組（首次呼叫時注入樣式，不呼叫的頁面完全不受影響），介面皆以 cell DOM 元素為單位，任何盤面規格可用：

- `ensureLayer(container)`：在盤面外框內建立/取得 `.slot-fx-layer`（粒子與浮字的容器）；頁面也可自行放 `<div class="slot-fx-layer">`。
- `winGlow(winCells, dimCells)`：中獎格金光爆閃、未中獎格壓暗（`fx-win` / `fx-dim`）。
- `popCells(cells)`：消除縮爆。`spawnCoins(layer, [{el, count}])`：以各格中心噴散金幣粒子。
- `wildPop(cells)`：轉換符號彈跳登場。`mark(cell, "fx-wild-stay")` / `mark(cell, "fx-scatter")`：Wild 常駐光暈、Scatter 呼吸發光。
- `multiPop(layer, "X8", { jump, tag })`：盤面中央大字（跳階時 `jump: true` 為綠金配色、`tag` 顯示上標）。
- `winFloat(layer, "+200")`：每段贏分浮字。`totalWin(layer, "總贏分", "3.85")`：回合結束閃光橫幅。
- `reelRoll(cells)`：滾動中輪帶的模糊滾動效果。

使用範例：`其他/遊戲發想/賞金列車 2/index.html`（含逐輪停輪、中獎→消除→轉 Wild→倍數彈出→總贏分的完整編排）。

符號顯示規則（Demogame規範 4.2.3）由共用模組統一處理：

- `demogame_common.js` 偵測到頁面定義 `window.DEMOGAME_IMAGE_TOGGLE` 時，在 Setting 產生 `Image` 開關並呼叫其 `setEnabled(enabled)`；狀態存 `localStorage` 的 `slotDemoSymbolImages`。
- `demogame_common.css` 的 Symbol display standard：格子有 `has-symbol-art` 時只顯示符號圖，隱藏符號代號並移除符號框線與底色；狀態框線（`.hit`、`.convert`、`.wild-mark`、`.fx-win`）與加了 `keep-symbol-frame` 的格子不受影響。
- 所有盤面符號代號（`.symbol-code`、`.h019-glyph`、`.slot-symbol-label` 等）一律一般字重；無美術時可用 `.slot-symbol-label` 作為置中代號標籤。
- 目前接入 Image 開關的遊戲：H013、H015、H016、H019、H028，以及發想的糖果狂歡 2500、賞金列車 2；H026、H027、急速糖果 2 無符號美術，固定顯示框＋代號。

H015 Card System 的 Normal Bet 採兩階段 retry：BG `free_game` 卡先固定並重抽至觸發，之後在同一 BG 上獨立重抽整包 FG，直到符合 `weight_fg` 或達到設定的 retry limit；不可把 BG 與 FG 綁成同一次重抽。

所有 Demo Game 都會顯示 Simulation；只有遊戲邏輯已實作卡片模型時才顯示 `Card System` 開關。統計區標題統一為 `Stats`。H026、H028 沿用遊戲原生的獨立批次模擬器；其餘遊戲各自提供 `window.demogameSimulateRound`，直接重用該頁 Demo Game 的 BG、Cascade、FG、Retrigger、倍率與 Card System JavaScript 數學函式。共用模組不再用卡片區間權重近似結果，也不呼叫 Python。以上批次路徑都不播放動畫、不觸發畫面 Spin，且不更動盤面、餘額或主 Stats。

Simulation 預設為 10,000 場。共用執行器採約 40ms 的自適應時間切片；H026、H028 每 250 場才更新一次畫面，以降低 DOM 更新成本並保持頁面可操作。

共用模組會檢查目前數學設定是否有權重大於 0 的有效 `card_system` 資料；沒有時會隱藏整個 `Card System` 欄位。遊戲若尚未實作卡片數學分支，頁面需設定 `window.DEMOGAME_CARD_SYSTEM_SUPPORTED = false`，即使載入的共用設定物件含卡片資料也不會誤顯示；原遊戲已有 Card System 控制時則保留原生判定。

每款遊戲只需自行維護：

- `#feature-bar`：遊戲名稱。
- `#strip-bar`：該遊戲的狀態資訊。
- `#grid-panel` / `#board`：盤面結構、符號與動畫。
- `#bet-mode-panel .zone-body` 內的押注模式按鈕與倍率；容器與互動樣式共用。

新遊戲的 `index.html` 在 `</head>` 前載入：

```html
<link rel="stylesheet" href="../demogame_common.css?v=1">
```

並在 `</body>` 前載入：

```html
<script src="../demogame_common.js?v=1"></script>
```

遊戲資料夾皆位於 `Project/Slots` 下一層，因此路徑固定使用 `../`。
