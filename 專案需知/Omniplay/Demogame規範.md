# Demogame規範

本文件屬於 `專案需知/` 專案需知文件集，總覽、共通原則與完成條件見 [_README.md](../其他/_README.md)。

**存放位置**（路徑以遊戲專案資料夾 `Slots/H0xx_遊戲名稱/` 為準，總表見[總覽](../其他/_README.md#3-文件存放位置)）：

| 檔案 | 存放位置 |
|---|---|
| `index.html` | 專案根目錄 |
| Demo 用符號圖（WebP） | `Source/Image/` |
| 共用樣式與程式 `demogame_common.css`／`.js` | `Slots/` |

## 1. 用途與載入

Demogame 是模型邏輯、流程與 Debug 資訊的可操作驗證介面，不只是視覺展示。它必須能用單局結果證明 Config、Simulator 與遊戲規則一致。

- 主入口固定為 `index.html`，使用相對路徑，雙擊即可離線執行。
- Config 選單只列 Config 代號，不列 Profile，Demogame 不提供 Newbie：例如 `BaseA`、`BaseB`、`92A`、`94A`、`92A_BET100`、`92B`。
- 卡片系統沒有獨立的開關，由 Config 選單決定：選 `Base` 為自然機率（卡片系統關），選 `92A` 等 Config 代號為卡片系統開（Oldhand）。
- 自然機率只依基礎數學 Variant 區分，與 RTP 家族無關：只有一套時顯示 `Base`；有 A／B 兩套時顯示 `BaseA`、`BaseB`。
- 標題列右側固定放「數值報告」（有報告時）、「說明」、「重置」三個文字按鈕（無底色、無外框，滑過才顯示底色），字型與標題相同，標題列高 44px；數值報告在同一分頁開啟。
- 標題列樣式各遊戲一致：代號＋名稱 15px 粗體、上下置中（由共用 CSS 統一），不得另寫遊戲專屬的標題樣式。
- 盤面不得裁掉格子的特效：中獎放大、百搭彈出與外發光在最外側一欄／一列也要完整顯示（共用 CSS 對 `#board.board-grid` 保留 14px 外圍可見範圍）。
- 遊戲名稱、盤面、輪帶、權重、Paytable、Bet Mode 與 Feature 參數從 Config 取得。
- 不得為演出方便另寫一套簡化數學邏輯。
- Config 無法載入或欄位不完整時要顯示明確錯誤，不得靜默使用舊值。

### 1.1 遊戲類型命名規則

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

## 2. 共用區域與 By Game 區域

圖示中的遊戲顯示區域屬於 By Game 設計；除此之外的 Demogame 區域均為所有遊戲共用。

### 2.1 By Game 區域

下列區域依各遊戲盤面、Feature 與美術需求自行設計：

- Game Title：遊戲 ID、遊戲名稱及遊戲專屬標題樣式。
- Feature Status：Cascade／Combo、FG Left、Multiplier 與其他遊戲狀態（不顯示 Base Game／Free Game 模式標題；沒有要顯示的特色時整列隱藏，由共用模組處理）。
- Reel／Board：盤面尺寸、Reel、Symbol、框體、特殊符號及遊戲專屬資訊。
- Board Animation：Spin、中獎、消除、補牌、掉落、轉換、Multiplier 與 Feature 動畫。
- Board Message：盤面下方的局數、FG 進度、得分、No Win 與遊戲流程訊息。

對應元素通常為 `#feature-bar`、`#strip-bar`、`#grid-panel`／`#board` 及盤面 Message Bar。實際 ID 可以依遊戲調整，但範圍與責任不得擴張到共用區域。

By Game 區域必須：

- 從 Config 取得名稱、盤面、Symbol、倍率與 Feature 資料，不得寫死其他遊戲的內容。
- 只維護遊戲專屬 HTML、CSS、Render、動畫與狀態轉換。
- 將共用操作需要的狀態與結果透過固定介面交給共用模組，不得複製整套共用控制邏輯。

### 2.2 共用區域

除第 2.1 節外，其餘區域與行為均由所有遊戲共用，包括：

- Player：Credit、Bet、Win。Player／Play／Bet Mode 三區一律放在盤面下方（左欄），右欄只留統計；手機版（單欄）依序為盤面、這三區、統計（共用模組處理）。
- Stats／Simulation。Stats（標題「基本指標」）放共用項目（總局數、RTP、中獎率、FG 觸發、BG／FG 最大倍數；原「最高倍數」與其重複，不再顯示）；遊戲自訂的特殊指標（只放觀察玩法機制用的即時統計，例如金框使用率；FG 週期等遊戲數據已在報告中，不放這裡）放在下方獨立的「特殊指標」區（共用模組自動把非共用列移入，也可在列上標 `data-by-game`），沒有特殊指標就不顯示這區。
- Play：Spin、Auto、Bet Stepper、Speed。
- Bet Mode 的容器、共用互動與狀態樣式；實際支援模式及倍率由 Config 決定。按鈕字體、大小一致、字一律白色：NB／EB 為切換鈕（選取中用「自動」鈕的深綠底白字），BF／SF 為購買鈕，用 SPIN 的藍底白字（共用模組依按鈕文字判斷）。
- Debug Mode、Set RNG、Log 與歷史紀錄（Spin Result 面板與 Force FG 已停用，由共用模組隱藏；Reel RNG 停輪面板已拿掉，改用統計區的 BG／FG 最大倍數）。
- Setting：Version、Config／Profile、Language、Help、Reset。
- Language：共用區的固定英文標籤由 `demogame_common.js` 依 `#languageSelect` 統一切換中英（整段完全相同才替換）；By Game 區域與遊戲專屬文字仍由各遊戲自行翻譯，切回 English 必須還原。
- 共用彈窗、按鈕狀態、欄位樣式、響應式版面、無障礙與錯誤顯示。各區塊上下、左右間距一律 10px（含盤面與右欄、頁尾與設定區），頁尾文字置中、用區域標題的說明色。字體統一：所有按鈕 12px 粗體；Debug 的 Previous／Next 兩顆同款（深藍底、細框、淺色字，共用 `demogame_common.js` 套用）；設定區文字標籤 12px 一般字重、下拉選項同按鈕；有名稱的區域標題 12px 粗體、說明色、不轉大寫，標題列滿版、下方加一條分隔線（同紀錄區）；遊戲區不顯示標題。倍率線型、紀錄、版本紀錄的標題後有「+」，點下去用彈窗顯示完整內容（倍率線型為大圖），彈窗一開就是最大尺寸（不隨內容長高，沒資料的地方維持深色底），可按 ⟳ 旋轉 90°（寬高對調後滿版）；直式手機放大倍率線型時一開就是橫的，紀錄與版本紀錄維持直式，關閉後放回原位；所有捲軸隱藏但保留上下捲動。

共用資源固定放在 `Slots/`：

```text
Slots/
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

### 2.3 符號顯示規則（所有遊戲）

盤面符號一律依下列規則顯示，樣式由 `demogame_common.css` 的 Symbol display standard 統一套用：

| 狀態 | 顯示 |
| --- | --- |
| Image 開啟，且該符號有美術 | 只顯示符號圖；**不顯示符號代號、不畫符號框**（無框線、無底色） |
| Image 關閉，或該符號無美術 | 顯示**符號框＋符號代號** |

- 符號代號（`M1`、`M2`、`A`、`C1`…）一律使用一般字重，**不得使用粗體**。
- 符號框＋代號的樣式所有遊戲統一（共用 `demogame_common.js` 依格子代號自動套用，各遊戲不另設；沒有特別要求就照這套）：M 獎與字獎（A／K／Q／J／10）都有底版，字獎深藍底，M1～M8 用同亮度、不同色相的低彩度漸層（M1 酒紅、M2 靛紫、M3 墨綠、M4 寶藍、M5 青、M6 梅紫、M7 棕、M8 橄欖）；C1／C2／SC 與金框同一種亮色漸層呈現但用紫色；Wild 青綠漸層；金框格一律用亮金漸層（淡金→深金、金框、淺色代號）並覆蓋原本底色；Consolas 21px 一般字重；Help 賠率表的代號方格用同一套配色（18px）。中獎、轉換等狀態格維持各自的狀態樣式；H014 數字格不套用。
- 有符號美術的遊戲必須接入共用 Image 開關：頁面在載入 `demogame_common.js` 前定義 `window.DEMOGAME_IMAGE_TOGGLE = { supported: true, defaultEnabled: true, setEnabled(enabled) { … } }`，`setEnabled` 內切換是否輸出符號圖並重繪目前盤面；不得自行另做圖片開關。共用模組會在 Setting 產生 `Image` 開關，選擇存於 `localStorage`（`slotDemoSymbolImages`）。
- 有輸出符號圖的格子必須加上 `has-symbol-art`；圖片載入失敗時移除此 class 並改顯示代號。
- **圖片預載（必做）**：放到網頁上時，圖片若等第一次用到才下載，盤面會先出現空白格。有符號美術的遊戲必須在 `DEMOGAME_IMAGE_TOGGLE` 加上 `images`：本遊戲會用到的**所有**圖片網址（陣列，或回傳陣列的函式），包含大符號長圖、金框等所有變體。共用模組會在開局前預載並解碼完成：
  - 預載期間擋住點擊與鍵盤；超過 120 ms 才顯示「載入圖片 n / N」遮罩，避免已有快取時畫面閃一下。
  - 解碼最多等 1.5 秒；分頁在背景時略過解碼（瀏覽器在背景分頁不會完成 `decode()`），不得因此卡住遮罩。
  - 任一張載入失敗：關閉 Image 開關、改用文字顯示，並提示失敗張數；不得停在載入畫面。
  - 預載邏輯只寫在 `demogame_common.js`，遊戲專屬程式只提供 `images` 清單，不得自行另寫預載。
- **圖片格式**：Demo 使用的符號圖一律用 WebP（`quality 90`、保留透明），檔名與原 PNG 相同、副檔名改 `.webp`，放在 `Source/Image/`；原始 PNG 保留作為美術原檔，Demo 不引用。
- 無美術時的代號可使用共用標籤 `<span class="slot-symbol-label">代號</span>`（置中、一般字重）。
- 沒有任何符號美術的遊戲不接 Image 開關，固定顯示符號框＋代號。
- 中獎、轉換等**狀態**框線（`.hit`、`.convert`、`.wild-mark`、`.fx-win`）不受此規則影響。
- Hook：框線本身屬規則狀態、且沒有對應美術時（例如純 CSS 的金框），在該格加 `keep-symbol-frame` 保留框線。金框若已有美術（例如 Frame 圖或金框版符號圖），不得再疊加 CSS 框。

## 3. 補牌方式

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
   - 必須在該遊戲的 `game_rule.md` 與數學模型的 `Game Description` 工作表中明確定義抽取來源、移動方向、補牌順序、保留位置及動畫。
   - 不得把單一遊戲的特殊補牌邏輯寫成所有遊戲共用的預設行為。

- 補牌資料必須來自 Config 定義的 Reel／Drop Table／Weight，不得只為動畫另外抽一組結果。
- 補牌後重新判獎的次數、盤面與得分必須可由 Debug 結果重現，並與 Simulator 對帳。
- Symbol 轉 Wild、鎖定位置或不補牌的位置，必須先依遊戲規則處理，再執行選定的補牌方式。

## 4. 必要行為

- 支援 Normal Spin，以及遊戲實際存在的 Extra Bet、Buy Feature、Super Feature。
- 押注選項依 Bet Currency：1～1500 加上最大押注 2000／3000／5000；押注層級由數學定義的遊戲（例如 H014 依押注各有自然表）以 Config 為準。
- Bet 顯示與 Credit 扣款使用實際模式成本；Win 依流程即時更新：每次消除得分就加上去（BG 局與每轉 FG），局末數值與結算相同；觸發 FG 那局（含 BF 入場盤）的 BG 得分要累積進 FG，FG 期間 Win＝觸發局 BG 得分＋FG 累計，FG 結束時等於整局總得分；Debug 的 Previous／Next 逐步檢視時，Win 同步顯示該步的累計得分。
- Auto、Speed、Reset 不得改變 RNG、得分或統計結果。
- Speed 為 1～5 五階：1～4 階轉輪由左到右逐輪停；第 5 階不逐輪停，Spin 後所有轉輪同時到位（BG、FG、Respin 皆同）。
- 每一轉（BG 局與每一轉 FG）算完分後固定停 0.5 秒（共用 `window.demogameRoundPause()`），才放行下一轉或 Auto；這段停頓不受 Speed 影響，Simulation 不停頓。
- BG、Cascade、FG、Retrigger 與 Feature 狀態按真實流程播放。
- FG 結束回到 BG 時，盤面還原成觸發 FG 那局的 BG 最終盤面（BF 為入場盤），Feature Status 回到基礎遊戲。
- Config、Version、Profile、押注層級、Card System 與 Language 只顯示實際支援的內容。
- Help 與 `game_help_draft.md` 一致，不在 HTML 另維護一份規則。
- Help 至少要有賠率表：`game_help_draft.md` 沒有賠率（或讀不到、只剩離線副本）時，由 Config 的 Paytable 依目前押注產生。
- Help 版式（共用 `demogame_common.js`）：標題由大到小（區塊標題 20px 置中 → 副標題 15px 置中 → 規則 13px），區塊之間用分隔線、規則前加方塊符號；賠率表顯示成兩欄符號卡片，每張是「符號＋由大到小的 `N - 派彩`」。有符號美術的遊戲要定義 `window.DEMOGAME_SYMBOL_ART = { 代號: 圖片網址 }`，卡片用該圖；沒美術或 Image 關閉時，顯示與盤面同款的深色代號方格（C1／SC 金色、WW 綠色）。
- 連線（Line）遊戲有得分時要在盤面畫出得分線：呼叫共用 `window.demogameWinLines.draw(盤面容器, [[格子元素…], …])`，每條得分線要依線圖（paylines）整條畫出、連過每一輪的格子中心，不能只畫中獎的那幾連，顏色依序輪替；每次重畫盤面後要重新呼叫。

## 5. Debug 與重現

Debug Mode 至少可查看：

- Config、Version、Profile、Bet Mode、Mode／Feature Price 倍數、base bet、實際模式押注、`bet_tier_amount`、押注層級、Link 資格、BG／FG Max Multiplier 與 Card System 狀態。
- Card 抽獎值、卡片區間與 Retry 次數。
- Table、Drop Mode 與盤面表（記在 Log）；停輪與整局抽樣以 RNG 碼重現（見下方「可重現 RNG」）。
- 初始盤面、每段 Cascade、Line／Ways Win、Multiplier 與最終結果。
- FG 觸發、局數、Retrigger、整包 Win 及即時 Log。
- 最後調性更新（共用，頁尾 `.footer-note`）：頁面在載入 `demogame_common.js` 前設 `window.DEMOGAME_LAST_TUNING = "YYYY-MM-DD HH:MM"`，頁尾顯示「最後調性更新：日期 時間」（24 小時制，到分鐘）。**只有數學模型或倍率（卡片）權重調整才更新**（與 `修改紀錄.md` 最新一項同日）；介面、演出、文件修改不更新。
- 數值報告按鈕（共用）：有 `其他/數值報告_<遊戲中文名>.html` 的遊戲，在載入 `demogame_common.js` 前設 `window.DEMOGAME_REPORT_URL`，標題列右側出現「報告」按鈕（英文 Report），與說明、重置排在一起。
- BG／FG 最大倍數（共用，併在「統計」區，取代原「最高倍數」列）：頁面在載入 `demogame_common.js` 前設 `window.DEMOGAME_HISTORY = true`，每局呼叫 `window.demogameHistory.record({ bg, fg })`（BG 得分、該局 FG 總得分，皆 ÷ 底注）；沒有 FG 的遊戲只顯示 BG 列，重置清空。
- Log（共用 `window.demogameLog(text, type)`）：帶時間的即時紀錄，Clear 清空，最多保留 500 行；所有遊戲行格式一致（照 H045），不記演出過程：
  - `Config <名稱> loaded | Version <版本> | Card System On|Off`
  - `#<局號> Normal Bet|Extra Bet|Buy Feature|Super Feature | Bet <押注>[ | Card Range set][ | Replay]`
  - `RNG <碼>`（可點，複製並填入 RNG 欄）
  - `BG|BF Entry | <盤面表> | Cascade <n> | C1 <n> | Win <得分> (<倍數>x)`
  - `Free Game triggered | <n> spins[ (Retrigger ×k)]`、`FG <i>/<n> | … | Win <得分>`、`FG complete | Total <得分> (<倍數>x)`
  - `Error | <訊息>`
- Simulation（共用，`#batch-simulation`）：N 局獨立數學模擬，Start 執行中只顯示「進行中」（English：Running），不跳局數。FG 觸發顯示「比例 (N 場)」；最高倍數為單局總得分倍數（BF ÷ 底注）；消除分布轉置為「消除次數 × BG／FG」，與倍率線型一樣各自框成一區並有標題。各遊戲提供：
  - `window.demogameSimulateRound({ mode })`：用與畫面相同的遊戲邏輯產生一局（不得另寫簡化數學），回傳 `multiplier`（總得分含 FG ÷ 實際押注）、`lineMultiplier`（BF ÷ 底注，其餘同 `multiplier`）、`fgTriggered`、`maxMultiplier`、`retryLimitExceeded`、`retryCount`、`bgCascade`、`fgCascades`；`mode` 只在該局暫時套用，不得改動畫面押注模式與統計。
  - `window.demogameSimulationModes = [{ value, label }]`：只列實際支援的押注模式，面板據此顯示押注模式選單。
- 累積倍率線型（共用，統計區下方，標題「倍率線型 (押注模式)」）：畫面實際遊玩的局，NB 記在 NB、EB 記在 EB，BF／SF 不記錄；依目前押注模式顯示對應的累積圖（標準 64 區間、Y 軸 1%），重置清空。遊戲每局（含 FG）結束時呼叫 `window.demogameLineChart.record(總得分 ÷ 押注, "NB"|"EB")`；押注模式按鈕沒有 is-active 樣式時另呼叫 `setMode()`。
- 倍率線型（共用，併入 Simulation 面板）：該次模擬每局 `lineMultiplier` 的標準 64 區間分布，X 軸逐一標出 (下限, 上限]，Y 軸 NB／EB 1%、BF 20%，超過上限或為 0 的區間不畫點、線在該處斷開。沒有 Simulation 面板的頁面才在 Set RNG 上方顯示即時線型（NB 一局含 FG 結束時呼叫 `window.demogameLineChart?.record(該局總得分 ÷ 底注)`；批次模擬不得呼叫）。

Set RNG 的各欄位（卡片區間、遊戲專屬選單、RNG）互斥：設定其中一個時其他回到預設（共用模組處理）。所有設定都每局沿用，按重置才清空，遊戲不得在 Spin、FG、切換模式後自行清掉。指定值要檢查格式；不得因指定 RNG 進入無限重跑。

**Set RNG（共用，`#set-rng-panel`）**：欄位排成一列等寬（卡片 BG 區間、遊戲專屬選單、RNG `#rngInput`、重置 `#setRngResetBtn`）。

**可重現 RNG（共用 `window.demogameRng`）**：每局（BG＋整場 FG）以一組 32-bit 種子算出；Log 印一行 `RNG <Config-Profile>/<NB|EB|BF|SF>/<on|off>/<選項|->/<種子 8 碼>`，點一下複製並填入 RNG 欄，按 Spin 整局重跑出相同結果。遊戲在每局開始呼叫 `demogameRng.takeInput()` 取碼、用 `demogameRng.run(seed, fn)` 一次算完整局結果（表演用亂數放在外面），選項欄放重現所需的遊戲專屬設定（例：腳本名稱、`r<卡片區間>`）。

## 6. 與 Simulator 對帳

至少準備下列可重現案例：無獎 BG、一般得分、Wild／Scatter、Cascade／Multiplier、FG Trigger／Retrigger、各 Bet Mode、Newbie、Oldhand 小／中／大 Bet、Link 可用／不可用、Card System range／free_game／Retry、Max Win 截斷及遊戲專屬 Feature。

逐項確認盤面、RNG、各段得分、Total Win、Coin In、倍率、Feature 狀態與 Retry 計數一致。

## 7. 交付檢查

Demogame 的「版本紀錄」（`#change-log-wrap`，Debug Mode 開啟時顯示）是專案根目錄 `修改紀錄.md` 的複本，只說明各版本的**調性差異**：

- 格式同 [開發流程 2.1](開發流程.md#21-修改紀錄格式)：依四碼版本分節、新到舊，列出全部版本；每個版本一個 `<article class="change-log-entry">`，標題 `<h4>v<第 1 碼>（<四碼版本>）</h4>`，內文 `<ol>` 編號清單，項目與 `修改紀錄.md` 相同（同一版本內由舊到新、句尾附 `（MM/DD）`）。設定區目前選的版本那一節由共用模組標示。
- 每次 `修改紀錄.md` 新增或修改項目，同一次修改中同步更新 `#changeLogBody`。
- 沒有任何調性紀錄時（`修改紀錄.md` 只有標題），`#changeLogBody` 留空，共用模組會把整個版本紀錄區隱藏；不得用「現行版本」「細節無紀錄」之類的佔位項目充數。
- 通則：沒有內容的區域一律不顯示（特殊指標、版本紀錄、空的 Set RNG 容器等由共用模組自動隱藏）。
- 盤面上方狀態列最前面固定顯示 Base Game／Free Game 標籤（中文：基礎遊戲／免費遊戲），由共用模組依 `body.fg-mode` 切換，所以狀態列一律顯示；遊戲進入 FG 時必須在 `body` 加上 `fg-mode`。狀態列由共用模組統一配色，各遊戲不另設：場景標籤（Base Game、Free Game、Buy Feature、Super Feature 等，含特色狀態顯示的場景名稱）用深藍底、淺藍字膠囊；其他資訊（連消、倍數、FG 剩餘、Table 等）一律用黃色膠囊（淡黃底、黃字 12px）；膠囊都不加外框。
- Demogame 介面、演出、Debug、共用模組與文件的修改**不記在頁面上**（以 git commit 訊息為準），也不寫進 `修改紀錄.md`。

- [ ] 離線開啟無錯誤，Console 無未處理例外。
- [ ] 「版本紀錄」（`#changeLogBody`）與 `修改紀錄.md` 內容一致（依版本分節、新到舊、只記調性）。
- [ ] `demogame_common.css` 與 `demogame_common.js` 由 `../` 相對路徑載入，且共用功能未複製進遊戲專屬程式。
- [ ] 圖示範圍內的標題、Feature Status、盤面、動畫與 Message 屬 By Game；其餘 UI 使用共用資源。
- [ ] By Game CSS／JavaScript 未覆寫或複製共用區域的版面與控制邏輯。
- [ ] 符號顯示符合 2.3：Image 開＝只顯示圖（無代號、無符號框），Image 關或無美術＝符號框＋代號；代號不粗體；有美術的遊戲已接共用 Image 開關。
- [ ] 有符號美術時：`DEMOGAME_IMAGE_TOGGLE.images` 列出全部圖片（含大符號、金框等變體），以本機伺服器開啟確認 `window.__demogameImageCache` 張數等於清單、全部 `naturalWidth > 0`、載入遮罩已消失；Demo 引用的圖片皆為 `.webp`，無 `.png` 引用。
- [ ] 補牌方式已選定為原地、掉落或特殊補牌，並與 Game Rule、Config、Simulator 一致。
- [ ] 原地補牌不移動保留符號；掉落補牌正確區分 Settle 與新符號 Drop。
- [ ] Config 切換後所有資料與顯示同步更新。
- [ ] 所有支援的 Bet Mode 均可完成完整流程。
- [ ] Card System Off／On、Newbie、Oldhand 小／中／大 Bet 與 Link 資格行為正確。
- [ ] Debug 資訊足以重現並與 Simulator 對帳。
- [ ] Demo 統計口徑與模擬報表一致。
- [ ] 不存在寫死的舊遊戲名稱、倍率、Table、輪帶或 Help。
