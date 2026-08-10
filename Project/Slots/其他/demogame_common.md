# Demo Game 共用模組

所有遊戲的 `index.html` 共用：

- `demogame_common.css`：遊戲資訊、盤面、Credit、Play、Bet Mode、Stats、Debug、Setting 與 Help 的 UI/UX，所有主要區塊使用一致的淡色外框。
- `demogame_common.js`：共用初始化、Setting 結構正規化、Config／Player 合併、Version 顯示、Bet Mode 無障礙狀態、Help 樣式與 Markdown／賠率表標準化。原本的 `help_ui_standardizer.js` 已完整併入此檔案。

Setting 會統一整理成左側開關群組與右側設定／操作群組。Config 與 Player 合併成單一選單（例如 `92A-Oldhand`），並在旁邊顯示目前數學模型的 Version；舊模型未提供版本欄位時顯示 `Current`。

Debug 面板以 10px 間距排列，不讓相鄰外框黏在一起。若頁面同時存在 `#change-log-wrap` 與 `#batch-simulation`，共用模組會自動將 Simulation 放到 Change Log 後面；沒有 Change Log 的遊戲則保留原位置。

共用區塊標題統一使用與 `LOG` 相同的 12px 字級、字重與字距，英文以大寫顯示。Simulation 不顯示 Config／Version／Card System／Bet 的說明行，並固定與前一個區塊保留 10px 間距。

所有 Demo Game 都會顯示 `Card System` 開關與 Simulation，統計區標題統一為 `Stats`。H026、H028 沿用遊戲原生的獨立批次模擬器；H027 透過純數學 adapter 執行完整 Cascade／FG；其餘遊戲由共用模組直接依目前 Card System 數學權重模擬 N 場並累計結果。以上批次路徑都不觸發畫面 Spin，也不更動盤面、餘額或主 Stats。

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
