# Slot Demo Game 共用規格

> 檔名：`slot_demogame_standards.md`
>
> 參考實作：`Project_AI/Slots/H026_彩罐熱舞 1000/index.html`
>
> 用途：建立下一款 Slot Demo Game 時，統一畫面樣式、操作方式、Debug 工具、資料顯示與驗收標準。

## 1. 規格定位

### 1.1 必須統一的項目

- 整體深色介面風格與色彩層級。
- 卡片、標題列、按鈕、欄位及間距規則。
- 主畫面資訊架構。
- Play、Bet Mode、Setting 的操作方式。
- Debug Mode 的顯示範圍與控制邏輯。
- Set RNG、Reel RNG、Spin Result、Log 的基本功能。
- 統計欄位與計算口徑。
- Help 彈窗的閱讀方式。
- 離線開啟、響應式與最低驗收標準。

### 1.2 必須依遊戲調整的項目

- 盤面尺寸、輪帶數、可見列數與 symbol 素材。
- Payline、Ways、Cluster 或其他得分方式。
- Feature 狀態列顯示的欄位。
- Bet Mode 種類、倍率與 Feature Buy 成本。
- Cascade、Multiplier、FG、Jackpot 等遊戲特色。
- Config 檔案名稱與選項。
- Card System、Set RNG 類型與可指定範圍。
- Reel RNG 需要顯示的實際抽獎階段。

不得為了外觀一致，顯示遊戲本身不存在的功能。

## 2. 建立新 Demo Game 前要整理的資料

### 2.1 遊戲基本資料

- Game ID。
- Parsheet ID。
- 中文及英文遊戲名稱。
- 預設 Config。
- 可切換的 Config 清單。
- 預設餘額。
- Denomination（DENOM）。
- Bet Level 清單。

### 2.2 數學與盤面資料

- Reel 數量與盤面列數。
- 各 Mode 使用的 Table、Reel Strip 與 Reel Weight。
- Symbol ID、Symbol Code、圖片路徑及基礎 symbol 對應。
- Paytable。
- Payline、Ways 或其他得分資料。
- Scatter、Wild、Gold、Multiplier 等 symbol 屬性。
- Drop／Cascade 使用的表與權重。
- FG 觸發、加局、最大場次與倍數規則。
- Card System 的 Card Range、權重與命中條件。
- Feature Buy 是否需要觸發盤面及其重抽條件。

### 2.3 操作模式

每個 Mode 必須先列出：

- 顯示名稱。
- Config 中的 Mode ID。
- 投注倍率。
- 使用的 BG／FG Table。
- 是否為持續開關或一次性操作。
- 是否可在 Auto 中切換。
- 是否可直接進入 FG。

例如：

| Mode | 類型 | 畫面顯示 | 投注處理 |
| --- | --- | --- | --- |
| Normal Bet | 持續模式 | `NORMAL BET` | 1 倍 Bet |
| Extra Bet | 持續模式 | `EXTRA BET (2X)` | 依 Config 倍率計算 |
| Buy Feature | 一次性操作 | `BUY FEATURE (75X)` | 單次扣除指定倍數 |

### 2.4 Feature 顯示需求

每個遊戲都要先定義 Feature 狀態列需要即時顯示什麼，例如：

- Base Game／Free Game。
- Cascade 次數。
- 本次 Spin Multiplier。
- FG 累積 Multiplier。
- FG Left。
- Mega Level、Collection、Meter 或其他遊戲專屬狀態。

只顯示對玩家或測試有意義的狀態，不在狀態列顯示 Table ID 或 RNG 細節。

### 2.5 Help 資料

- `game_help_draft.md`。
- 正式規則章節清單。
- 简中及英文規則文字。
- Paytable。
- 不應顯示的內部內容，例如 Game Meta、來源說明、待確認事項及編輯備註。

## 3. 建議檔案結構

```text
<Game Folder>/
├─ index.html
├─ game_help_draft.md
├─ config_*.js
├─ Simulator.py                 # 若專案有模擬器
├─ Assets/ 或 Image/
│  └─ symbols...
└─ Source/                      # 原始表格或轉檔來源，依專案需要
```

規則：

- 主入口固定使用 `index.html`。
- HTML、Config、Help 與素材應使用相對路徑。
- 雙擊 `index.html` 時必須可以離線操作，不依賴伺服器。
- 無圖片時可以退化顯示 Symbol Code，但不可造成程式中斷。
- Config 不可載入時，要顯示明確錯誤，不可只留下空白畫面。

## 4. 共用視覺規格

### 4.1 色彩 Token

新 Demo Game 預設沿用下列色彩：

```css
:root {
  --bg: #040e1a;
  --panel: #071528;
  --surface: #0c2240;
  --surface-2: #103052;
  --text: #b0d4f0;
  --sub: #5a88aa;
  --accent: #00ddc0;
  --red: #ff5f8a;
  --green: #33ff99;
  --blue: #33bbff;
  --mauve: #b06aff;
}
```

### 4.2 尺寸與樣式

- 頁面背景使用 `--bg`。
- 主要內容最大寬度預設為 `920px`。
- 主要卡片背景使用 `--panel`。
- 卡片圓角統一為 `10px`。
- 診斷區域邊框統一為 `1px solid rgba(38, 92, 137, 0.55)`。
- 區域標題列高度統一為 `36px`。
- 區域標題使用英文大寫、小字級與固定字距。
- 一般內容文字使用 `--text`，次要標示使用 `--sub`。
- 主要成功或即時數值使用 `--accent` 或 `--green`。
- 危險或強制操作使用 `--red`。
- 所有區域名稱、邊框、圓角及標題高度必須一致。

### 4.3 響應式

- 桌面版使用盤面與資訊欄雙欄配置。
- 建議主盤面欄寬約 `420px`，右欄使用剩餘空間。
- 螢幕寬度小於或等於 `760px` 時改為單欄。
- 小螢幕的按鈕與欄位可以換行，但不可超出卡片。
- Bet 選單、Help 彈窗及 Log 不得造成水平捲動。
- 所有控制項都必須維持可點擊的最小尺寸。

## 5. 畫面區域與固定順序

### 5.1 一般畫面

由上到下：

1. Game Title。
2. Feature Status。
3. Main Area。
   - 左側：Reel Board、Message Bar。
   - 右側：Player、Simulation Stats、Play、Bet Mode。
4. Setting。

### 5.2 Debug Mode 開啟後

Debug Mode 開啟時，額外顯示：

1. Play 內的 Debug 操作列。
2. Set RNG。
3. Reel RNG。
4. Spin Result（包含 Line Wins）。
5. Log。
6. Setting 仍固定在最下方。

Debug Mode 關閉時，上述 Debug 專用區域必須完全隱藏，不可留下空白高度。

## 6. 區域詳細規格

### 6.1 Game Title

- 顯示 Game ID 與遊戲名稱。
- 資料應來自目前載入的 Config。
- 名稱不得沿用其他遊戲的暫存文字。

### 6.2 Feature Status

- 顯示目前是 Base Game 或 Free Game。
- Feature 數值必須隨 Spin、Cascade、FG Spin 即時更新。
- 沒有作用的 Feature Pill 應隱藏。
- `FG Left` 只在 FG 期間顯示。
- `FG Left` 格式為「剩餘場次／本次 FG 總場次」。
- Retrigger 後才增加總場次。

### 6.3 Reel Board

- 使用真實 Config 的 Reel、Weight 與 Symbol 資料產生結果。
- Spin 動畫使用對應 Mode 的真實輪帶符號，不使用無關假圖替代。
- 每格至少支援 Symbol 圖片與 Symbol Code。
- 依遊戲需要支援：Scatter、Wild、Gold、Multiplier、Hit、Convert 等狀態。
- 中獎、轉換及消除必須有可辨識的視覺狀態。
- Message Bar 固定放在盤面下方。

### 6.4 Message Bar

至少需要顯示：

- Ready。
- Reels spinning。
- Spin 完成。
- Cascade 階段。
- FG 觸發與剩餘場次。
- 無法投注或餘額不足。
- RNG 指定錯誤。
- 其他執行錯誤。

### 6.5 Player

固定顯示：

- `Credit`。
- `Bet`。
- `Win`。

規則：

- 所有金額必須使用同一套 DENOM 換算。
- Bet 顯示實際扣款金額，不顯示內部 Bet Multi。
- Extra Bet 開啟後，Bet 必須立即顯示加倍後金額。
- Win 隨播放進度更新，不可在 FG 開始時直接顯示整段最終結果。
- Credit 先扣款，再依播放進度逐步加入 Win。

### 6.6 Simulation Stats

固定顯示：

- `Total Rounds`。
- `RTP`。
- `Hit Rate`。
- `FG Trigger`。
- `Max Multiplier`。

計算口徑：

- `Total Rounds`：完成並列入統計的付費 Round 數。
- `RTP`：累積 Total Win ÷ 累積有效投注。
- `Hit Rate`：有得分的 Round 數 ÷ Total Rounds。
- `FG Trigger`：自然觸發次數 ÷ 可自然觸發的 Round 數。
- `FG Trigger` 同時顯示觸發率與平均週期，例如 `2.00% (50場)`。
- Buy Feature 與 Force FG 不計入自然 FG Trigger。
- `Max Multiplier`：Session 內實際出現的最大倍數。

### 6.7 Play

主要操作列固定包含：

1. `SPIN`。
2. `AUTO`。
3. Bet Stepper。
4. Speed Slider。

Bet Stepper：

- 左側為 `−`。
- 中間顯示目前 Bet。
- 右側為 `+`。
- 點擊中間 Bet 按鈕，顯示所有可選 Bet Level。
- Bet Level 預設為：`1、2、3、4、5、6、8、10、12、16、20、30、40、60、100、200、300、600、1000、1500`。
- 新遊戲若使用不同 Bet Level，必須由 Config 或明確常數提供。

Speed：

- 使用拉條，不使用 Turbo 開關。
- 範圍固定為 `x1～x5`。
- Speed 只影響動畫與播放等待時間，不改變 RNG 結果。

### 6.8 Auto

- Auto 是隨時可切換的模式開關。
- Auto 開啟後立即開始自動 Spin。
- Auto 關閉後，不再啟動下一次 Spin。
- Auto 開啟時，SPIN 不可按。
- Auto 開啟時，Bet `−／選單／+` 不可操作。
- Auto 開啟時，Bet Mode 不可切換。
- SPIN 按鈕不可用閃爍方式表示 Auto 狀態。
- AUTO 按鈕本身必須清楚顯示啟用狀態。

### 6.9 Bet Mode

- Bet Mode 是獨立區域，放在 Play 下一個區域。
- Normal Bet 與 Extra Bet 是模式開關，點擊後保持啟用狀態。
- 啟用中的模式按鈕必須亮起。
- Extra Bet 名稱必須顯示倍率，例如 `EXTRA BET (2X)`。
- Extra Bet 開啟時，Player 的 Bet 與實際扣款同步變更。
- Buy Feature 是一次性操作，不是持續模式。
- Buy Feature 按鈕顯示成本倍率，例如 `BUY FEATURE (75X)`。
- 點擊 Buy Feature 後直接執行該遊戲定義的 FG 進場流程。
- 不存在的 Mode 不顯示。

### 6.10 Play 的 Debug 操作列

只在 Debug Mode 開啟時顯示，並與 Play 的主要操作列上下分隔。

包含：

- `◀◀ PREVIOUS`。
- `NEXT ▶▶`。
- `Force FG`（遊戲支援時）。

歷史控制規則：

- 每次 Spin 播放都要保存可回看的畫面 Snapshot。
- Spin 完成後，只要存在較早 Snapshot，即可按 Previous。
- 目前位於最早 Snapshot 時，Previous 不可按。
- 只有回到較早 Snapshot 且存在向前歷史時，Next 才可按。
- 目前已是最新 Snapshot 時，Next 不可按。
- Spin 播放進行中，Previous 與 Next 不可按。
- Debug Mode 下，即使正在播放，也可以按 SPIN 排入下一次遊戲；目前播放應安全快轉完成，再開始已排入的 Spin。

### 6.11 Set RNG

- Set RNG 是獨立區域，只在 Debug Mode 開啟時顯示。
- Card Range 與 Reel RNG 必須互斥。
- 有指定 Card Range 時，Reel RNG 不可輸入。
- 有指定 Reel RNG 時，Card Range 不可選擇。
- Reel RNG 使用單一輸入框，以空格分隔，例如：`1 2 3 4 5`。
- Reel RNG 數量必須等於 Reel 數量。
- 每個輸入值都要驗證是否落在該 Reel 的有效 RNG 範圍。
- `Auto` 代表不指定，由正常 RNG 決定。
- 必須提供清楚可見的 `RESET`，只重置 Set RNG 輸入。
- Spin、Auto 或待處理 FG 期間，Set RNG 不可修改。
- 指定 RNG 只作用於下一個適用的 Spin，實際作用範圍需依遊戲定義。

### 6.12 Reel RNG

只在 Debug Mode 開啟時顯示，至少包含：

- Scene／Mode。
- Card System 抽獎值及總範圍（若有）。
- Table 抽獎值及總範圍。
- Drop Mode 抽獎值及總範圍。
- 每一 Reel 的 RNG 值、總範圍、Stop Index 與 Reel Length。
- 是否為指定 RNG。

所有 RNG 建議統一顯示為：

```text
抽中值 / RNG總值 | range 0-(RNG總值-1)
```

### 6.13 Spin Result

只在 Debug Mode 開啟時顯示，內容依播放順序即時更新：

- 初始盤面。
- 每一次 Cascade 的盤面。
- 每次 Cascade Pay。
- 當下 Multiplier。
- 最終 Spin 結果。
- Line Wins。

Line Wins 至少包含：

- Line Index。
- Symbol。
- 命中長度。
- Cascade Index。
- Pay。

### 6.14 Log

- 只在 Debug Mode 開啟時顯示。
- 必須即時更新。
- 最多保留並顯示 500 行。
- 標題只顯示 `LOG`，不可顯示 `?? / 500` 或目前行數。
- 提供 `CLEAR` 按鈕。
- 新訊息加入後自動捲動到底部。
- 建議用顏色區分一般資訊、Mode 變更、Cascade、結果與錯誤。

### 6.15 Setting

Setting 永遠顯示，並固定在所有下方區域的最後。

至少包含：

- `Debug Mode` 開關。
- `Config` 選單。
- `Help` 按鈕。
- `Reset` 按鈕。

規則：

- Debug Mode 開啟後才顯示 Debug 專用區域。
- Config 切換方式需明確；重新載入後應套用選定 Config。
- Reset 重置 Credit、統計、Auto、Bet Mode、FG、Debug 暫存、指定 RNG 與畫面狀態。
- Reset 後回到預設 Config 或保留目前 Config，必須在專案開始前決定並保持一致。

### 6.16 Help

- Help 按鈕放在 Setting。
- 點擊後使用彈窗顯示 `game_help_draft.md` 的規則內容。
- 規則文字必須與 `game_help_draft.md` 完全相同，不可在 HTML 中另外改寫。
- 只顯示正式規則與 Paytable。
- 不顯示文件前言、Game Meta、來源說明、待確認事項或編輯備註。
- 简中與英文並排顯示；小螢幕可改為上下排列。
- 規則以區域卡片整理，不直接顯示原始 Markdown 表格。
- 必須支援 Close 按鈕、`Esc` 與點擊背景關閉。
- 必須提供離線備援內容，確保雙擊 `index.html` 時仍可閱讀。
- 若 Help 內容採內嵌備援，更新 `game_help_draft.md` 時必須同步更新內嵌內容並做文字一致性檢查。

## 7. 操作鎖定矩陣

| 狀態 | Spin | Auto | Bet | Bet Mode | Speed | Previous／Next | Set RNG |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Idle | 可用 | 可切換 | 可用 | 可用 | 可用 | 依歷史狀態 | 可用（Debug） |
| Spinning | 一般模式不可用；Debug 可排入 Next Spin | 可關閉 | 鎖定 | 鎖定 | 可用 | 鎖定 | 鎖定 |
| Auto | 不可用 | 可關閉 | 鎖定 | 鎖定 | 可用 | 鎖定 | 鎖定 |
| Pending FG | 顯示下一場 FG 操作 | 依設計 | 鎖定 | 鎖定 | 可用 | 依播放狀態 | 鎖定 |
| History View | 可開始下一次 Spin | 可切換 | 依 Idle | 依 Idle | 可用 | 依前後歷史 | 可用（Debug） |

## 8. 遊戲流程與帳務規格

### 8.1 Spin

1. 驗證目前狀態與餘額。
2. 取得 Bet Mode 與實際 Bet。
3. 扣除 Credit。
4. 產生完整 Round Result。
5. 依序播放 Reel、Win、Cascade、Multiplier、FG。
6. 依播放進度更新 Credit、Win、Feature、RNG、Spin Result 與 Log。
7. Round 完成後更新統計。

### 8.2 Cascade

- 每次 Cascade 都要個別播放與記錄。
- Feature 狀態、Win、盤面及 Log 必須同步更新。
- 不可直接跳到 Final Board，除非使用 Debug 快轉。

### 8.3 Free Game

- FG 觸發後依遊戲定義逐場播放。
- 顯示剩餘與總場次。
- Retrigger 必須即時更新場次。
- FG 最大場次限制需與 Game Rule 及 Simulator 一致。
- 斷線或中斷處理方式至少要在 Help 中說明；Demo 可提供可重現的完整結果。

### 8.4 Feature Buy／Force FG

- 若需重抽觸發盤面，重抽期間不可重複扣款、計分或進統計。
- 必須有最大重抽次數，超過時顯示錯誤。
- 指定 Reel RNG 與 Force FG 衝突時，不可無限重抽，應直接提示無法觸發。
- Force FG 不計入自然 FG Trigger。

## 9. 建議資料介面

### 9.1 Config 最低欄位

- `game_id`、`game_name`。
- `reel_num`、`window_size`。
- `symbol_id`、`symbol_str`、Symbol 屬性。
- Reel、Reel Length、Reel Weight。
- Table 與 Table Weight。
- Paytable 與 Payline／Ways 資料。
- Normal、Extra、Feature Buy 等 Mode ID 與倍率。
- BG／FG／Drop 使用資料。
- Card System 資料（若有）。

### 9.2 Round Result 最低欄位

- Bet Mode、Coin In、Total Win。
- Scene、Table、Drop Mode。
- Scatter Count。
- Initial Board、Final Board。
- Cascade Steps。
- Line Wins。
- Reel RNG 與其他抽獎資訊。
- FG Trigger、Awarded Spins、Remaining Spins、Retrigger。
- Feature 專屬狀態。

資料欄位可以依遊戲命名，但 Render 層取得的資訊必須完整。

## 10. 實作原則

- RNG／數學邏輯與 UI Render 分離。
- 先產生可重現的 Round Result，再依結果播放動畫。
- Debug 畫面只讀取已產生的結果，不另外改算結果。
- 所有 UI 狀態集中由單一 State 管理。
- 顯示金額、倍數、百分比與 RNG 範圍使用共用格式化函式。
- 所有按鈕狀態由統一更新函式處理，避免只在個別事件內修改。
- 即時 Log 最多保留 500 筆，資料與 DOM 都要裁切。
- 不可因動畫速度改變 RNG、得分或統計結果。
- 不可使用與 Config 不一致的寫死遊戲名稱、倍率、Table 或規則。

## 11. 新遊戲實作順序

1. 整理第 2 節所需資料。
2. 複製 H026 的版面骨架與共用 CSS Token。
3. 替換 Game ID、名稱、Config 清單與素材。
4. 建立 Config Adapter，統一遊戲資料介面。
5. 完成 Normal Spin 與盤面 Render。
6. 完成 Bet、Auto、Speed 與 Bet Mode。
7. 完成遊戲 Feature 與 FG 流程。
8. 完成統計與帳務更新。
9. 完成 Debug Mode、Set RNG、RNG、Spin Result、Log 與歷史控制。
10. 接上 Help 並建立離線備援。
11. 依第 12 節完成驗收。

## 12. 最低驗收清單

### 12.1 基本功能

- [ ] 雙擊 `index.html` 可離線開啟。
- [ ] Normal Spin 可完成。
- [ ] 所有 Bet Level 可選擇。
- [ ] Extra Bet 金額、Mode 與輪帶同步切換。
- [ ] Buy Feature 可正確進入指定流程。
- [ ] Auto 可隨時關閉，關閉後不再自動 Spin。
- [ ] Speed x1～x5 只改變播放速度。
- [ ] Reset 可完整恢復預設狀態。

### 12.2 顯示與統計

- [ ] Credit、Bet、Win 的 DENOM 換算一致。
- [ ] Feature Status 隨播放即時更新。
- [ ] RTP、Hit Rate、FG Trigger、Max Multiplier 計算正確。
- [ ] Feature Buy 與 Force FG 不計入自然 FG Trigger。
- [ ] 桌面與小螢幕均無水平溢出。
- [ ] 所有區域標題、邊框、圓角與間距一致。

### 12.3 Debug

- [ ] Debug 關閉時不顯示任何 Debug 專用區域或空白。
- [ ] Debug 開啟時顯示 Play Debug 列、Set RNG、Reel RNG、Spin Result、Log。
- [ ] Previous／Next 的可用條件正確。
- [ ] Debug 播放中可排入下一次 Spin。
- [ ] Card Range 與 Reel RNG 互斥。
- [ ] Reel RNG 輸入數量及範圍驗證正確。
- [ ] Set RNG Reset 清楚可見且功能正確。
- [ ] RNG 顯示值、總值、Range 與 Stop Index 正確。
- [ ] Spin Result 依播放階段即時更新。
- [ ] Log 即時更新、最多 500 行且可 Clear。

### 12.4 Help

- [ ] Setting 中有 Help 按鈕。
- [ ] Help 只顯示正式規則與 Paytable。
- [ ] Help 文字與 `game_help_draft.md` 完全一致。
- [ ] Help 可用 Close、Esc 及背景點擊關閉。
- [ ] 離線開啟時 Help 仍可閱讀。

### 12.5 技術檢查

- [ ] HTML 內嵌 JavaScript 語法檢查通過。
- [ ] HTML ID 無重複。
- [ ] 瀏覽器 Console 無未處理錯誤。
- [ ] Normal、Extra、Feature Buy、FG、Auto、Debug 至少各完成一次實際操作測試。
- [ ] 指定 RNG 可重現預期盤面或抽獎區間。
- [ ] Help、Bet 選單與所有彈窗沒有版面溢出。

## 13. 每款新遊戲必須留下的規格紀錄

建議在遊戲資料夾另外建立 `demogame_spec.md`，只記錄該遊戲與共用規格不同的部分：

```markdown
# <Game ID> Demo Game Spec

## Config
- 預設 Config：
- 可切換 Config：
- DENOM：
- Bet Levels：

## Board
- Reel x Row：
- 得分方式：
- Symbol Assets：

## Bet Modes
- Normal：
- Extra：
- Feature Buy：

## Feature Status
- 欄位 1：
- 欄位 2：

## Debug RNG
- Card Range：
- Table RNG：
- Reel RNG：
- 互斥條件：

## Statistics
- Hit 定義：
- FG Trigger 分母：
- Max Multiplier 定義：

## Help
- 規則來源：
- 排除章節：

## Special Cases
- 該遊戲額外限制或例外：
```

共用行為不必在每款遊戲重寫；只記錄差異與遊戲專屬規則。
