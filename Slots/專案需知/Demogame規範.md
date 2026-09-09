# Demogame規範

本文件屬於 `Slots/專案需知/` 專案需知文件集，總覽、共通原則與完成條件見 [_README.md](_README.md)。

## 4.1 用途與載入

Demogame 是模型邏輯、流程與 Debug 資訊的可操作驗證介面，不只是視覺展示。它必須能用單局結果證明 Config、Simulator 與遊戲規則一致。

- 主入口固定為 `index.html`，使用相對路徑，雙擊即可離線執行。
- Demogame 的模型顯示格式為 `<Config>-<Profile>`，例如 `92A-Oldhand`。
- 遊戲名稱、盤面、輪帶、權重、Paytable、Bet Mode 與 Feature 參數從 Config 取得。
- 不得為演出方便另寫一套簡化數學邏輯。
- Config 無法載入或欄位不完整時要顯示明確錯誤，不得靜默使用舊值。

### 4.1.1 遊戲類型命名規則

Game Rule、Demogame 與 Help 的遊戲類型統一使用以下格式：

`Video Slot - <主要派彩類型> / <附加機制>`

主要派彩類型只能依實際判獎邏輯選擇一種：

| 類型 | 統一英文 | 判定規則 |
| --- | --- | --- |
| 群集派彩 | `Cluster Pay` | 相同符號必須在盤面上依規定方向相鄰連接，且連接數量達門檻才得獎。 |
| 全盤計數 | `Pay Anywhere` | 相同符號在整個盤面的總數達門檻即得獎，不要求相鄰、連線或由最左輪開始。 |
| 路數派彩 | `N Ways` | 相同符號由最左輪起，在連續相鄰輪出現即得獎；文件中的 `N` 必須換成實際固定 Ways 或最小～最大 Ways。 |
| 線數派彩 | `N Lines` | 依固定 Payline 判獎；文件中的 `N` 必須換成實際線數。 |

- `Cascade`、`Megaways`、Multiplier 與 Feature 屬附加機制，不得代替主要派彩類型。
- 不要求相鄰的全盤計數玩法不得標示為 `Cluster Pay` 或 `Cluster Pays`。
- 連消流程使用的得分倍數統一稱為 `Cascade Multiplier`，不得再使用 `Progressive Multiplier`、`Progressive Cascade Multiplier` 或 `Progressive Win Multiplier`。
- 相同術語必須同步出現在 Game Rule、Index Help 與遊戲清單，不得各自使用不同名稱。

目前正式遊戲類型如下：

| 遊戲 | 統一遊戲類型 |
| --- | --- |
| H013 糖果狂歡 1000 | `Video Slot - Pay Anywhere / Cascade` |
| H015 賞金列車 | `Video Slot - 3,600 Ways / Cascade / Cascade Multiplier` |
| H016 幸運王牌 | `Video Slot - 1,024 Ways / Cascade / Cascade Multiplier` |
| H019 埃及秘寶 | `Video Slot - Pay Anywhere / Cascade` |
| H026 彩罐熱舞 1000 | `Video Slot - 20 Lines / Cascade` |
| H027 宙斯 2500 | `Video Slot - Pay Anywhere / Cascade` |
| H028 雷神爆金 | `Video Slot - 2,025–32,400 Ways / Megaways / Cascade` |

目前正式遊戲沒有使用 `Cluster Pay`；日後只有實際採相鄰群集判獎的遊戲才能列入此類。

## 4.2 共用區域與 By Game 區域

圖示中的遊戲顯示區域屬於 By Game 設計；除此之外的 Demogame 區域均為所有遊戲共用。

### 4.2.1 By Game 區域

下列區域依各遊戲盤面、Feature 與美術需求自行設計：

- Game Title：遊戲 ID、遊戲名稱及遊戲專屬標題樣式。
- Feature Status：Base Game／Free Game、Cascade／Combo、FG Left、Multiplier 與其他遊戲狀態。
- Reel／Board：盤面尺寸、Reel、Symbol、框體、特殊符號及遊戲專屬資訊。
- Board Animation：Spin、中獎、消除、補牌、掉落、轉換、Multiplier 與 Feature 動畫。
- Board Message：盤面下方的局數、FG 進度、得分、No Win 與遊戲流程訊息。

對應元素通常為 `#feature-bar`、`#strip-bar`、`#grid-panel`／`#board` 及盤面 Message Bar。實際 ID 可以依遊戲調整，但範圍與責任不得擴張到共用區域。

By Game 區域必須：

- 從 Config 取得名稱、盤面、Symbol、倍率與 Feature 資料，不得寫死其他遊戲的內容。
- 只維護遊戲專屬 HTML、CSS、Render、動畫與狀態轉換。
- 將共用操作需要的狀態與結果透過固定介面交給共用模組，不得複製整套共用控制邏輯。

### 4.2.2 共用區域

除第 4.2.1 節外，其餘區域與行為均由所有遊戲共用，包括：

- Player：Credit、Bet、Win。
- Stats／Simulation。
- Play：Spin、Auto、Bet Stepper、Speed。
- Bet Mode 的容器、共用互動與狀態樣式；實際支援模式及倍率由 Config 決定。
- Debug Mode、Set RNG、Reel RNG、Spin Result、Log 與 History 控制。
- Setting：Version、Config／Profile、Language、Help、Reset。
- 共用彈窗、按鈕狀態、欄位樣式、響應式版面、無障礙與錯誤顯示。

共用資源固定放在 `Project/Slots/`：

```text
Project/Slots/
├─ demogame_common.css
├─ demogame_common.js
└─ H0xx_遊戲名稱/
   └─ index.html
```

每款遊戲的 `index.html` 必須使用相對路徑載入：

```html
<link rel="stylesheet" href="../demogame_common.css?v=1">
<script src="../demogame_common.js?v=1"></script>
```

- `demogame_common.css` 維護所有共用區域的版面、色彩、間距、元件狀態與響應式規則。
- `demogame_common.js` 維護共用初始化、操作控制、Setting、Config／Profile、Version、Language、Help、Debug 與共用狀態同步。
- 共用功能或樣式有異動時，修改 `demogame_common.css`／`demogame_common.js`，不得在每款遊戲的 `index.html` 複製一份再各自修改。
- By Game 樣式與程式保留在該遊戲的 `index.html` 或遊戲專屬資源，不得放入共用檔案影響其他遊戲。
- 遊戲專屬 CSS 不得覆寫共用區域，除非本規範明確提供可覆寫的 CSS Variable 或 Hook。

## 4.3 補牌方式

每款有消除機制的遊戲，必須在 Game Rule、Config 對應說明與 Demogame 中指定唯一補牌方式。Simulator 與 Demogame 必須使用相同邏輯。

1. **消除後原地補牌**
   - 中獎符號消除後，只在原本的空格位置抽取並顯示新符號。
   - 盤面上未消除的符號維持原座標，不播放向下移動動畫。
   - 新符號在空格原位播放 Refill 動畫。
2. **消除後掉落補牌**
   - 中獎符號消除後，同一 Reel／Column 上方未消除的符號依重力向下補位。
   - 剩餘空格由新符號從盤面上方掉入。
   - 動畫必須區分既有符號的 Settle 與新符號的 Drop／Refill。
3. **特殊補牌（By Game）**
   - 不符合前兩類的 Random、Parallel、跨欄移動、整盤替換或其他特殊補牌皆歸此類。
   - 必須在該遊戲的 `game_rule.md` 與 Config mapping 中明確定義抽取來源、移動方向、補牌順序、保留位置及動畫。
   - 不得把單一遊戲的特殊補牌邏輯寫成所有遊戲共用的預設行為。

- 補牌資料必須來自 Config 定義的 Reel／Drop Table／Weight，不得只為動畫另外抽一組結果。
- 補牌後重新判獎的次數、盤面與得分必須可由 Debug 結果重現，並與 Simulator 對帳。
- Symbol 轉 Wild、鎖定位置或不補牌的位置，必須先依遊戲規則處理，再執行選定的補牌方式。

## 4.4 必要行為

- 支援 Normal Spin，以及遊戲實際存在的 Extra Bet、Buy Feature、Super Feature。
- Bet 顯示與 Credit 扣款使用實際模式成本；Win 依流程加入。
- Auto、Speed、Reset 不得改變 RNG、得分或統計結果。
- BG、Cascade、FG、Retrigger 與 Feature 狀態按真實流程播放。
- Config、Version、Profile、押注層級、Card System 與 Language 只顯示實際支援的內容。
- Help 與 `game_help_draft.md` 一致，不在 HTML 另維護一份規則。

## 4.5 Debug 與重現

Debug Mode 至少可查看：

- Config、Version、Profile、Bet Mode、Mode／Feature Price 倍數、base bet、實際模式押注、`bet_tier_amount`、押注層級、Link 資格、BG／FG Max Multiplier 與 Card System 狀態。
- Card 抽獎值、卡片區間與 Retry 次數。
- Table、Drop Mode、Reel RNG、總範圍、Stop Index 與 Reel Length。
- 初始盤面、每段 Cascade、Line／Ways Win、Multiplier 與最終結果。
- FG 觸發、局數、Retrigger、整包 Win 及即時 Log。

指定 Card Range 與 Reel RNG 必須互斥。指定值要檢查數量與範圍，且只作用於規格定義的下一個 Spin；不得因指定 RNG 或 Force FG 進入無限重跑。

## 4.6 與 Simulator 對帳

至少準備下列可重現案例：無獎 BG、一般得分、Wild／Scatter、Cascade／Multiplier、FG Trigger／Retrigger、各 Bet Mode、Newbie、Oldhand 小／中／大 Bet、Link 可用／不可用、Card System range／free_game／Retry、Max Win 截斷及遊戲專屬 Feature。

逐項確認盤面、RNG、各段得分、Total Win、Coin In、倍率、Feature 狀態與 Retry 計數一致。

## 4.7 交付檢查

每次修改 Demogame 的 `index.html`、共用 `demogame_common.css`／`demogame_common.js`，或任何會改變操作、顯示、動畫、Debug、Config／Version／Profile 選擇方式的程式時，必須在同一次修改中同步更新 Demogame 的「修改紀錄」。

- 修改紀錄統一放在 `#change-log-wrap`，並於 Debug Mode 開啟時顯示。
- 每筆紀錄至少包含日期、修改目的、實際變更內容與驗證結果。
- 若變更會影響數學、XLSX、Config、RTP、Hit Rate 或 Feature 行為，必須明確列出受影響檔案與數值；若未影響，也必須註明「未修改 XLSX／Config 數學參數」。
- 修改紀錄必須描述目前實際完成的內容，不得只寫「調整」、「修正」或尚未執行的計畫。
- 純介面或程式修正不需要因此提升數學版本，但仍必須留下修改紀錄。

- [ ] 離線開啟無錯誤，Console 無未處理例外。
- [ ] 本次 Demogame 修改已同步更新 `#change-log-wrap`，內容包含日期、變更與驗證結果。
- [ ] `demogame_common.css` 與 `demogame_common.js` 由 `../` 相對路徑載入，且共用功能未複製進遊戲專屬程式。
- [ ] 圖示範圍內的標題、Feature Status、盤面、動畫與 Message 屬 By Game；其餘 UI 使用共用資源。
- [ ] By Game CSS／JavaScript 未覆寫或複製共用區域的版面與控制邏輯。
- [ ] 補牌方式已選定為原地、掉落或特殊補牌，並與 Game Rule、Config、Simulator 一致。
- [ ] 原地補牌不移動保留符號；掉落補牌正確區分 Settle 與新符號 Drop。
- [ ] Config 切換後所有資料與顯示同步更新。
- [ ] 所有支援的 Bet Mode 均可完成完整流程。
- [ ] Card System Off／On、Newbie、Oldhand 小／中／大 Bet 與 Link 資格行為正確。
- [ ] Debug 資訊足以重現並與 Simulator 對帳。
- [ ] Demo 統計口徑與模擬報表一致。
- [ ] 不存在寫死的舊遊戲名稱、倍率、Table、輪帶或 Help。
