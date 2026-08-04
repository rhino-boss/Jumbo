# Demo Index 修改紀錄

本文件用於記錄 `Project/Slots` 下各遊戲 Demo `index.html` 及其直接相依 runtime 的修改。

## 維護規則

- 後續凡修改任何遊戲的 `index.html`，都必須在本文件追加一筆紀錄。
- 若玩法程式拆分在 `*_runtime.js`，與該次 index 修改相關的 runtime 變更須記在同一筆。
- 每筆紀錄至少包含：日期、遊戲、需求、修改檔案、完成內容與驗證結果。
- 不覆寫舊紀錄；新紀錄依日期追加。

## 修改紀錄

### 2026-08-04 — H047 Super Bang Bang

需求：

- 直接使用 H046「幸運王牌」的 `index.html` 作為版型基底，再替換為 Super Bang Bang 玩法。
- 符號不使用圖片，採 101027 的純文字符號框。
- 符號代碼使用 `M1`、`M2`、`M3`、`M4`、`A`、`K`、`Q`、`J`、`WW`、`C1`。
- `Mult` 初始值、無連消狀態及 Reset 後皆顯示 `x1`。
- 網頁頁籤名稱使用 `Super Bang Bang — Demo Game`；畫面標題使用 `H047 Super Bang Bang`。
- Spin 必須具有與 H046 相同的轉輪滾動動畫。

修改檔案：

- `H047_Super Bang Bang/index.html`
- `H047_Super Bang Bang/h047_runtime.js`

完成內容：

- 保留 H046 的雙欄版型、Play、Bet Mode、Simulation Stats、Setting、Debug 與 Help 結構。
- 接入 Super Bang Bang 的 5 輪 × 4 列、1024 Ways、Cascade、Golden Card、Multiplier Strip、Free Game 與 Buy Feature 邏輯。
- 移除 H046 圖片符號依賴，改用純文字代碼與 101027 符號框配色。
- Spin 時依 H046 節奏產生多幀轉輪位移，各輪使用不同 offset，並與 Multiplier Strip 同步滾動後停下。
- 清除舊的空白 `animateSpin()` 前置呼叫，統一由 `animateReels()` 執行實際轉輪動畫，避免 Spin 因未定義函式中止。

驗證：

- JavaScript 語法檢查通過。
- Runtime 所需 DOM ID 全數存在，無重複 ID。
- 無 `<img>`、H046 config loader 或 `h046_runtime.js` 殘留引用。
- Headless Edge 已成功載入並完成初始畫面渲染。
- Selenium 實際點擊 Spin 驗證通過：偵測到 `reel-spin`、`Rolling reels...`、盤面更新與完整回合結束，瀏覽器錯誤數為 0。

### 2026-08-04 — H047 Bet 功能比照 H026

需求：

- H047 的 Bet 功能與 H026 相同。

修改檔案：

- `H047_Super Bang Bang/h047_runtime.js`

完成內容：

- Bet 中央按鈕由循環切換改為開啟 H026 式雙欄 Bet 選單。
- 選單顯示全部投注檔位，並以 `is-active` 標示目前檔位。
- 點擊選項後立即套用並關閉選單；點擊選單外或按 `Escape` 亦會關閉。
- `−`／`+` 按鈕依投注檔位逐級調整，位於最小／最大檔時停用。
- Spin、Auto 或待進行 FG 期間鎖定 Bet、`−`、`+`，並自動關閉選單。
- Bet 檔位補齊 `0.50`，完整範圍為 `0.50–1,000.00`；顯示格式統一為兩位小數。

驗證：

- JavaScript 語法檢查通過。
- Selenium 驗證選單共 11 檔，預設 `10.00` 正確高亮。
- Selenium 驗證選取 `20.00`、`−` 回到 `10.00`、`+` 回到 `20.00` 均正常。
- Selenium 驗證 Spin 期間 Bet 控制鎖定、選單關閉、回合完成，瀏覽器錯誤數為 0。
