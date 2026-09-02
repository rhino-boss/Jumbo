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
