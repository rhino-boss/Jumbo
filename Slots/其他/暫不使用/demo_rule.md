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

### 2026-08-04 — H047 Cascade 播放順序、掉落動畫與 Bet 檔位修正

需求：

- 每次 Spin／Cascade 必須依序播放：滾停 → 算分線顯示 → 消除／中獎金框轉 WW → 掉落 → 下一次循環。
- 掉落與補位必須具有實際動畫。
- Bet 使用 H026 的投注檔位，最小與預設皆為 `1.00`。

修改檔案：

- `H047_Super Bang Bang/index.html`
- `H047_Super Bang Bang/h047_runtime.js`

完成內容：

- Cascade 播放拆分為 `rolling`、`stopped`、`score`、`eliminate`、`drop`、`settled`、`complete` 階段。
- 滾停後先保留中獎盤面並顯示 Ways 算分線與當次得分，再進入消除。
- 一般中獎符號播放縮小、增亮與淡出動畫。
- 參與中獎的 Golden Card 在消除盤面先轉為 `WW`，並播放翻轉／亮起動畫；Big Joker 轉換位置亦列入轉換動畫。
- 掉落依每格實際移動列數設定起始高度；既有符號下落與新符號由上方補入均播放回彈動畫。
- 每次掉落完成並顯示穩定盤面後，才開始下一次算分循環。
- Bet 改為 H026 的 20 檔：`1、2、3、4、5、6、8、10、12、16、20、30、40、60、100、200、300、600、1000、1500`。
- 預設與 Reset 後的 Bet index 均設為最小檔 `1.00`。

驗證：

- JavaScript 語法檢查通過。
- Selenium 驗證 Bet 選單共 20 檔，第一檔 `1.00`、最後一檔 `1,500.00`，預設高亮 `1.00`。
- Selenium 在第一局即捕捉到完整順序：`rolling > stopped > score > eliminate > drop > settled > complete`。
- Selenium 實際捕捉到 `symbol-cleared`、`symbol-drop`／`symbol-settle` 動畫 class。
- 指定含中獎金框的模擬局驗證通過：轉換位置資料為 `WW`，消除階段實際顯示 `WW` 與 `convert` 動畫。
- 瀏覽器錯誤數為 0。

### 2026-08-04 — H047 掉落速度提高 3 倍

需求：

- Cascade 掉落與補位動畫速度提高 3 倍。

修改檔案：

- `H047_Super Bang Bang/index.html`
- `H047_Super Bang Bang/h047_runtime.js`

完成內容：

- 掉落動畫基準時間由 `420ms` 縮短為 `140ms`。
- 掉落階段等待時間由 `480ms` 縮短為 `160ms`。
- 各 Speed 檔位仍會依倍率縮短，最短動畫與等待時間分別調整為 `30ms`、`50ms`。
- 算分線顯示與消除階段時間不變。

驗證：

- JavaScript 語法檢查通過。
## H047 使用 H016 輪帶並補齊 H026 Debug UI/UX（2026-08-04）

- `H047_Super Bang Bang/index.html` 載入 `H016_幸運王牌/config_92.js`，初始盤面與消除後補符號皆改由 H016 的 5 輪、400 格輪帶及停點權重產生。
- BG 預設使用 H016 `bg_high`；FG 使用 `fg_low` 或四組 `fg_high_*`；購買特色使用 `buy`。
- 第一輪（R1）禁止金框：H016 原輪帶的 R1 本身不含金框，runtime 另加防呆，即使收到金框 ID 也轉為同符號普通框。
- Debug Mode 補上 H026 類型操作：Force FG、輸入 5 個 Reel RNG 停點、切換 H016 BG 輪帶、RNG Reset、Previous／Next 動畫階段回看、Live Log 與 Clear。
- Reel RNG 與結果區會顯示實際使用的 H016 table 及五輪停點。
- FG 套用 H016 的 `free_spin_cap = 50`，避免 Force FG 或連續 retrigger 造成無上限運算。

## H047 動畫、WW 消除與單檔整併（2026-08-04）

- 滾輪動畫取消 `translateY` 上下位移，保留符號換幀、亮度與模糊效果，避免滾停瞬間上下晃動。
- 所有參與連線的 WW 都會和一般中獎符號一起消除；命中金框轉成的 WW 也會在顯示轉換後消除並掉落補位。
- 金框轉 WW 動畫取消縮小、放大與翻轉，只保留亮度轉換效果。
- `h047_runtime.js` 完整內嵌至 `H047_Super Bang Bang/index.html`，不再保留獨立 runtime 檔。
- 滾動期間透明度固定為 `1`，符號及框體不使用半透明淡化。
- 依畫面確認後，滾動時同步移除 `brightness`、`blur` 與 CSS keyframe；僅保留 JavaScript 符號換幀，滾動中的框體與停輪後保持相同實色清晰度。
- 主盤滾輪改為持續換幀直到 Extra Reel 完成；最後一幀直接繪製實際結果盤面，Extra Reel 滾停後不再二次變牌。
- 金框處理改為 H016 順序：第一次命中只在原位置轉成 WW，不於同次 Cascade 消除或移動；下一次 Cascade 才能作為 WW 參與 Ways，若再次命中則和既有 WW 一樣消除。
- Win 顯示改為逐次 Cascade 同步累加，並保留小數兩位；每次算分線顯示時立即更新，不再等整個 Spin 結束。
- 金框觸發大鬼時拆成兩段動畫：先顯示中獎金框轉 WW，再額外顯示隨機 1～4 個合格符號逐格轉成 WW，之後才進入消除與掉落。
- 金框轉 WW 與大鬼隨機符號轉 WW 的動畫／停留時間均延長為原本 3 倍；消除及掉落速度不變。
- 金框底板改為參考圖樣式：實心上亮下深金色漸層、頂部白金高光、底部深金陰影及白色符號字樣。
- Cascade 播放順序重排為：滾停結果 → 標記中獎符號 → 同步消除／金框轉 WW／Win 加分 → 若為大鬼則先標記隨機選區、再將選區轉 WW → 掉落補位 → 下一次判獎循環。標記階段不會提早增加 Win。
- W2 流程再次依指定順序調整：消除／金框轉一般 WW 或 W2／算分 → 先補牌 → 僅 W2 從補牌後盤面挑選隨機區域 → 標記選區 → 選區轉一般 WW → 下一次循環。W2 本體以 `W2` 顯示，一般百搭維持 `WW`。
- 補牌重力改為包含所有保留的 WW／W2；金框轉成的 WW 或 W2 不再固定原格，若下方有消除空位會隨其他符號一起向下掉落，再由頂部補牌。
