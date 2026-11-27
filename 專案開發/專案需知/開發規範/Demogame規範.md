# Demogame規範

本文件屬於 `專案需知/` 專案需知文件集，總覽、共通原則與完成條件見 [_README.md](../其他/_README.md)。

**存放位置**（路徑以遊戲專案資料夾 `Slots/H0xx_遊戲名稱/` 為準，總表見[產出與紀錄規範](產出與紀錄規範.md#3-專案目錄與存放位置)）：

| 檔案 | 存放位置 |
|---|---|
| `index.html` | 專案根目錄 |
| Demo 用符號圖（WebP） | `Source/Image/` |
| 共用樣式與程式 `demogame_common.css`／`.js` | `Slots/` |

## 1. 用途與載入

Demogame 是模型邏輯、流程與 Debug 資訊的可操作驗證介面，不只是視覺展示。它必須能用單局結果證明 Config、Simulator 與遊戲規則一致。

- 主入口固定為 `index.html`，使用相對路徑，雙擊即可離線執行。
- Config 選單不列 Profile，Demogame 不提供 Newbie：**所有 Demo 一律老手期**（2026-11-27 使用者再確認），頁面原生 Profile 選單隱藏並固定 oldhand。
- 卡片系統沒有獨立的開關，由 Config 選單決定：選 `…-Base` 為自然機率（卡片系統關），選 `01-A` 這類系列代號為卡片系統開（Oldhand）。
- Config 選單只讓操作者選系列（2026-11-20）：`Base`（卡片關）、`A`、`B`（沒有 B 版就只有 A）；小／中／大 Bet 是同一份 Config（`config_<產線編號><系列>.js`）裡的層級（`94x`／`92x`／`92x_Bet100`），不放進選單，依玩家押注自動切換，規則同 Simulator 選層級：NB／EB 看實際押注、BF／SF 看底注，未滿 $2 用小 Bet、底注超過 $100 用大 Bet、其餘中 Bet。遊戲載入所選系列的 Config 後，把 `base` 疊上各 `tiers[層級]` 展開成一組（例 `window.H0xx_BOX_SET = { small, mid, big }`），換押注或換押注模式時立即換成對應層級（H026 為參考實作：`H026_BOX_SET`、`applyBoxTier()`）。
- Config 選單名稱帶產線編號（2026-11-20，所有遊戲適用）：產線編號依 `D:\SVN\Math_Release\IGaming\說明書\ID對照表.txt`（`01` 菲律賓主流遊戲、`01_2` 菲律賓 landbase 轉製遊戲、`02` 美國、`03` 墨西哥）；**發想中的遊戲（還沒有市場）一律用 `99`**（例：`99-A-Base`、`99-A`，2026-11-20 使用者）。自然機率寫 `{產線編號}-{A/B}-Base`，卡片開寫 `{產線編號}-{A/B}`；產線編號放前面（2026-11-20 使用者改為 `01-A` 格式）；依產線編號排序，同一產線內 Base 在前，例：`01-A-Base`、`01-B-Base`、`01-A`、`01-B`、`02-A-Base`、`02-A`…。Demo 用的 config（例 `120A_Demo`）寫 `{產線編號}-{A/B}-Demo`（例 `01-A-Demo`），排在最後（2026-11-20 使用者）。**A、B 共用同一份自然機率（只差卡片）時，B 的 Base 不列**，只留 `xx-A-Base`（遊戲宣告 `window.DEMOGAME_SHARED_BASE = true`）。遊戲宣告 `window.DEMOGAME_PRODUCT_LINE = "01"` 後共用 `demogame_common.js` 就照這個格式顯示；同一款有多條產線時，在原生 `#configSelect` 的 `<option>` 加 `data-line`。遊戲程式不可依選項文字判斷要載入哪份 config（用選項的 value）。
- 自然機率只依基礎數學 Variant 區分，與 RTP 家族無關（顯示名稱照上一條產線編號格式）。
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

### 1.2 名詞定義

本規範提到某款遊戲（例：「參考實作 H032」）時只是範例，規則本身以本文件文字為準；沒有其他遊戲可參考時，照本文件的定義與第 2.4～2.8 節的介面即可做出 Demogame。

| 名詞 | 定義 |
| --- | --- |
| BG／FG | Base Game（主遊戲）／Free Game（免費遊戲）。 |
| NB／EB／BF／SF | 押注模式代號：Normal Bet（一般押注）、Extra Bet（額外押注，成本為底注 × `cost_multiplier`，例 2x）、Buy Feature（購買特色，直接進 FG，價格為底注 × 購買倍數）、Super Feature（超級特色，較高價的購買）。Log、RNG 碼、倍率線型都用這四個代號。有第二種額外押注時代號為 EB2。模式值固定 `0`＝NB、`1`＝EB、`2`＝EB2、`3`＝BF、`4`＝SF（2026-11-20 使用者；沒有的模式跳過不補位）；此代號僅新遊戲適用，既有遊戲維持原代號（例 H032、H045：`2`＝BF、`3`＝SF）（2026-11-20 使用者）。 |
| 底注／實際押注 | 底注＝押注選單（Bet Stepper）上的金額；實際押注＝底注 × 該模式成本倍數。倍數一律＝得分 ÷ 實際押注，但 BF／SF 的倍率線型與 FG 看板用得分 ÷ 底注。 |
| 自然機率 | 不經卡片系統、直接依 Config 的輪帶／權重抽出的結果（Config 選單的 `Base`）。 |
| 卡片系統（Card System） | 先依目前層級 `card_system` 的卡片權重抽一張卡（一個倍率區間 `(min, max]`，或特殊類型），再以自然機率重抽整局直到倍數落在該區間；重抽上限為 `retry_limit`，超過記一次 Retry Limit Exceeded。細節以《模擬程式規範》為準，Demo 必須與 Simulator 同邏輯。 |
| Profile（Oldhand／Newbie） | 卡片組：老手／新手。Demogame 只用 Oldhand，不提供 Newbie。 |
| Config | `config_<產線編號><系列>.js`（例 `config_01A.js`）＝該產線該系列的全部數學：`base`（輪帶、賠率、自然機率）＋`tiers`（各 RTP／押注層級的卡片權重），全域變數 `window.H0xx_CONFIG_<產線編號><系列>`；以 `<script>` 載入（`file://` 開網頁不能讀 `.json`，所以不用 JSON 檔）。結構見《模擬程式規範》第 2.1 節。 |
| 系列（Variant）A／B | 同一款遊戲的兩組卡片權重版本；Config 選單只讓操作者選系列。 |
| 小／中／大 Bet | 依押注自動選的 Config 層級：小 Bet＝`94x`、中 Bet＝`92x`、大 Bet＝`92x_Bet100`（判定規則見第 1 節）。 |
| 版本（四碼） | `遊戲參數.卡片權重.SCR.其他文件`，例 `7.0.1.0`；版本清單在 `Versions/version_manifest.js`（`current`、`versions[].version`、`versions[].configs`）。 |
| Cascade（連消） | 中獎符號消除、補牌後再判獎的流程；一局內的消除次數稱 Cascade 次數。 |
| 輪帶類／掉落類遊戲 | 輪帶類＝Spin 時每輪是一條輪帶捲動停輪；掉落類＝Spin 時舊盤整欄掉出、新盤整欄掉入（通常是 Pay Anywhere 或消除掉落的遊戲）。新遊戲屬哪一類依 `game_rule.md` 的盤面表現決定，不確定時問使用者。 |
| RNG 碼 | 可重現一局的字串 `<Config-Profile>/<NB|EB|BF|SF>/<on|off>/<選項|->/<8 碼十六進位種子>`，見第 5 節。 |
| 腳本 | Set RNG 區的情境下拉（例：連消 5 次以上、有觸發 FG）；選了之後每局用自然機率重抽到符合條件。 |
| 標準 64 區間 | 倍率分布用的 64 個 `(下限, 上限]` 區間；邊界定義在 `demogame_common.js`，遊戲只要傳倍數。 |
| 產線編號 | `01` 菲律賓主流、`01_2` 菲律賓 landbase 轉製、`02` 美國、`03` 墨西哥、`99` 發想中（第 1 節）。 |
| peek 列／Jumbo／Extra Reel | 遊戲專屬盤面元素：只露出一部分的格子列、占多格的大符號、主盤面外的額外輪；有才需要處理。 |

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

- Player：Credit、Bet、Win。Player／Play／Bet Mode 三區併入遊戲區的手機直式排版（見 2.2.1，共用模組處理）。
- Stats／Simulation。Stats（標題「基本指標」）放共用項目（總局數、RTP、中獎率、FG 觸發、BG／FG 最大倍數；原「最高倍數」與其重複，不再顯示）；遊戲自訂的特殊指標（只放觀察玩法機制用的即時統計，例如金框使用率；FG 週期等遊戲數據已在報告中，不放這裡）放在下方獨立的「特殊指標」區（共用模組自動把非共用列移入，也可在列上標 `data-by-game`），沒有特殊指標就不顯示這區。
- Play：Spin、Auto、Bet Stepper、Speed。
- Bet Mode 的容器、共用互動與狀態樣式；實際支援模式及倍率由 Config 決定。按鈕字體、大小一致、字一律白色：NB／EB 為切換鈕（選取中用「自動」鈕的深綠底白字），BF／SF 為購買鈕，用 SPIN 的藍底白字（共用模組依按鈕文字判斷）。
- Debug Mode **預設開啟**（2026-11-27 使用者；共用模組載入時自動勾選，頁面可設 `window.DEMOGAME_DEBUG_DEFAULT = false` 關掉）、Set RNG、Log 與歷史紀錄（Spin Result 面板與 Force FG 已停用，由共用模組隱藏；Reel RNG 停輪面板已拿掉，改用統計區的 BG／FG 最大倍數）。
- 遊戲發想的 Demo 必須在 Set RNG 區最左邊加「腳本」下拉（`#scriptSelect`，第一個選項 value 為空字串；參考實作 H032／H045）：選項為「無」＋觸發本作特色的情境（例：連消 5 次以上、各新特色發生、有觸發 FG、FG 100x 以上），選了之後每次 Normal／Extra Spin 用自然機率重抽到符合條件（不改權重；BG 情境要求不觸發 FG；抽不到用最後一把並在 Log 註記），按 Reset 才清；腳本局不計入倍率線型；RNG 選項欄記腳本 key，照碼可重現。
- Setting：Version、Config／Profile、Language、Help、Reset。
- Language：共用區的固定英文標籤由 `demogame_common.js` 依 `#languageSelect` 統一切換中英（整段完全相同才替換）；By Game 區域與遊戲專屬文字仍由各遊戲自行翻譯，切回 English 必須還原。
- 共用彈窗、按鈕狀態、欄位樣式、響應式版面、無障礙與錯誤顯示。**任何彈窗開著時背景都不能操作**（2026-11-27 使用者）：共用模組偵測 `<dialog open>`、免費遊戲看板、新手導覽、手機區設定／押注選單，`<html>` 加 `dg-modal-lock`，頁面不能捲動、彈窗以外的區塊點不到也滾不動，**空白鍵／Enter 也不能觸發背景的 Spin**（只在彈窗裡面有作用；涵蓋購買確認框 `#m2-buy`、全畫面演出 `#m2-fx`）；各遊戲自訂彈窗請用 `<dialog>` 的 `showModal()` 開，就會自動套用。各區塊上下、左右間距一律 10px（含盤面與右欄、頁尾與設定區），頁尾文字置中、用區域標題的說明色。字體統一：所有按鈕 12px 粗體；Debug 的 Previous／Next 兩顆同款（深藍底、細框、淺色字，共用 `demogame_common.js` 套用）；設定區文字標籤 12px 一般字重、下拉選項同按鈕；有名稱的區域標題 12px 粗體、說明色、不轉大寫，標題列滿版、下方加一條分隔線（同紀錄區）；遊戲區不顯示標題。倍率線型、消除分布、紀錄、版本紀錄的標題後有「+」，點下去用彈窗顯示完整內容（倍率線型為大圖；消除分布只放大下方圖表、不帶數字表；圖表彈窗用圖表卡片同一套深色底 `#030b17`），彈窗高度貼齊內容（最高 92vh，超過在框內捲動），不留大片空白，可按 ⟳ 旋轉 90°（寬高對調後滿版）；直式手機放大倍率線型時一開就是橫的，紀錄與版本紀錄維持直式，關閉後放回原位；所有捲軸隱藏但保留上下捲動。

### 2.2.1 遊戲區（手機直式排版，2026-11-27 起所有遊戲）

由 `demogame_common.js` 的 phone-layout 段（`// ==== phone-layout ====`）自動套用，各遊戲 `index.html` 不用改；只搬節點、不改 id 與事件。參考實作：H027 宙斯 2500。

- 位置：桌機維持「手機｜右欄」兩欄（左右不置中）；**手機框＋正下方的更新資訊（頁尾 `.footer-note`：最後調性更新／唯一碼／程式最後調整／最後更新）整組在視窗上下置中**，畫面不夠高時等比縮小。手機（窄螢幕）時更新資訊放整頁最下面（2026-11-27 使用者「手機畫面上下置中就好、不用左右」「這個放手機下面，跟手機物件一起上下置中；手機版開這個網頁，這個資訊到最下面」）。
- 外框：桌機遊玩區包手機外框（黑邊、瀏海、Home 條），與上方、右欄間距同一般區塊 10px；**固定在畫面上，右欄上下捲動時不動**，視窗比手機框矮時整台等比縮小。手機（≤ 760px）不顯示外框，**遊玩區剛好一個螢幕高**，開啟時自動對齊。
- 由上而下：
  1. 標題列：**一律放右欄最上面**（手機上就是遊玩區下方、基本指標上面），不佔遊玩區（2026-11-27 使用者）。
  2. 彩金列：遊戲自帶 `#jpBar` 就用遊戲的；沒有但 Help 有 OP JACKPOT 段時放展示列（GRAND｜MAJOR｜OP 寶箱｜MINOR｜MINI，同 H032）。Demo 不模擬累積：GRAND／MAJOR 顯示起始值 1,000／200，MINOR／MINI 為底注 × 50／× 10；實際押注未滿 2.00 時 GRAND／MAJOR 變灰；數字塞不下先拿掉小數點，再塞不下用 K／M。
  3. Mult：置中膠囊、兩側細線（共用資訊條 `#demogame-info-bar`；沒有資訊時整列不顯示）。
  3a. 倍數列：原本放在盤面框裡的倍數條（`#grid-panel .multiplier-track`）**移出盤面框、放在盤面正上方**（`#m2-top`）；其他要移的元素用 `window.DEMOGAME_PHONE_TOP = ["#meter"]` 指定（例 Minted Mike）（2026-11-27 使用者「乘倍數丟出去」）。
  4. 盤面：遊戲自己的 `#grid-panel` 整塊搬進來；手機上**下方 SPIN 區（訊息列、押注列、餘額列、操作列）每款位置固定**（沒有押注模式也保留押注列高度），上方剩下的空間全部給盤面：盤面等比縮放撐滿可用寬或高（可放大，上限 1.8 倍），寬度先頂到時把盤面底框拉高填滿、內容置中；區塊間距 6～9px（2026-11-27 使用者「盤面太小」「間隔小一點，不要太多」「下方 spin 區域位置固定，空的地方縮放盤面去填」）。
     - 矮螢幕（手機寬且高度 ≤ 860px，例：手機瀏覽器扣掉網址列）：彩金列 52px、訊息列 32px、押注卡 56px、餘額列上下內距 6px、SPIN 80px，空間留給盤面（「宙斯畫面會變小」）。
  5. 訊息橫幅：原訊息列，低調緞帶樣式（中間亮、兩端淡出），中獎文字變綠。
  6. 押注模式：一列三格寬的卡片，**沒有內容的格子不放，剩下的置中**。**一般押注不放按鈕**（預設就是一般押注）。額外押注只放一顆、做成開關（小開關接在名稱後面同一行、整組置中），所有遊戲統一：只有一種額外押注時點一下開、再點一下關；有兩種以上（例：超級寶石系列 EB1 1.5x／EB2 8x）時點一下 EB1、第二下 EB2、再點一下回一般押注，按鈕顯示目前那一種的名稱與金額。按鈕下方顯示**按下去要花的金額**＝底注 × 該模式倍數（底注＝目前押注 ÷ 選取中模式倍數；額外押注開啟不影響購買特色金額；不顯示 (2x) 與括號）。
     - 卡片價格＝基礎押注 × 模式倍數，**開關 EB 不可改變 BF／SF 價格**（共用程式自動判斷押注鈕是否含 EB 倍數，2026-11-27 使用者）。
     - 得獎明細格（N 消／聚集消除遊戲**一律保留**，沒得獎時是空框，同實機）：**只有 N 消（Pay Anywhere）與聚集消除（Cluster）的遊戲**才有（依 Help 判斷，可用 `window.DEMOGAME_WIN_DETAIL = true／false` 指定），且該列還有空位時才放。固定三格、細線分隔（同 dev 環境），每格「顆數｜符號圖｜金額」；**每消除一次即時更新**（盤面中獎格 `.cell.hit` 依符號數顆數，金額＝訊息列 WIN 增加的部分；同一次消除有多種符號時金額待一局結束再補），新的一列從最下面補上，只顯示最新三列、塞不下的跳過；一局結束用除錯區 `#lineList` 的正式明細校正；按 SPIN 開新局先清空。
  7. 餘額列：原本的面板樣式（標籤在上、數值在下）。
  8. 操作列：設定｜押注｜SPIN｜自動｜加速。小鈕無外框、圖示＋文字；SPIN 大圓鈕、中間雙箭頭；押注鈕開押注選單（取代 −／＋）；自動進行中換停止圖示變綠（**所有遊戲一律**：自動中顯示綠色停止方塊＋「停止」，英文介面「STOP」；各遊戲以文字 Stop／停止／ON 或 `is-active`／`active` class 表示自動中都會被判斷到，2026-11-27 使用者「所有自動按下去都要變這樣」）；加速依序 x1 → x3 → x5 → x10（即速度滑桿，上限放寬到 10）。
- 設定：由操作列的「設定」打開，浮在遊玩區裡（不放右下角懸浮鈕）；打開時遊玩區壓暗、視窗亮藍框＋光暈；標題列＋✕，勾選做成兩格卡片（勾選中亮框），版本／Config／語言 標籤＋下拉一行一個；✕、Esc、點視窗外或壓暗處關閉。
- **購買特色確認框（所有遊戲）**：按任何購買鈕（`.demogame-buy-btn`，含 Super Feature）先跳確認框，按購買才照遊戲原本流程開局；共用模組 buy-confirm（`#m2-buy`）。構圖參考 dev：置中大標題（＝按鈕名稱）、說明「以目前花費觸發免費遊戲。點擊「購買」開始遊戲」、花費大框（按鈕金額）、押注加減（連動遊戲的押注 −／＋）、購買數量（1～10，大於 1 時每局含 FG 結束後自動再買）、取消／購買；模擬器藍色樣式。按鈕不能按或已選取（再按是取消）時不跳框。有 Dev 模式的遊戲開 Dev 模式時改用 dev 美術（見 2.2.2）（2026-11-27 使用者「所有遊戲的 BF 都要有這個功能」）。
- **所有彈窗**（設定、押注選單、說明、圖表放大、買特色確認、轉場、結算）都能**點外面（壓暗處）或按 Esc 關掉**；確認框另有標題列 ✕（2026-11-27 使用者）。
- 押注選單與設定**同一套樣式**：亮藍框＋光暈、打開時遊玩區壓暗，選項按鈕與設定的勾選卡片同底色、同框線，跟背景分得出來（2026-11-27 使用者）。
- 右欄：最上面標題列，接著統計、玩法簡介、倍率線型；除錯模式的上一步／下一步、指定 RNG、紀錄、版本紀錄、模擬都放右欄。
- 不套用：頁面設 `window.DEMOGAME_PHONE_LAYOUT = false`，或頁面自帶 `<style id="m2-layout">`。

### 2.2.2 Dev 模式（遊戲有 dev 環境釋出時才加，2026-11-27 起）

遊戲在 dev 環境釋出、使用者說「加 Dev 模式」時才做；**目標是遊玩區看起來跟 dev 一模一樣**，手機外框與 demo 功能不變。程式在 `demogame_common.js` 的 dev-skin 段（`// ==== dev-skin ====`），各遊戲只放素材與設定。參考實作：H027 宙斯 2500。

**設定開關**：設定多一個「Dev 模式」勾選，**預設開**（記在瀏覽器）；關掉回到一般 demo 畫面。

**素材**（全部放 `<遊戲>/Source/Dev/`，webp）：

1. 來源：dev 連結（Cocos Creator 版；連結過期請使用者從大廳重新登入，Claude 不代打密碼）＋ `JB 工作區/game_spec/<GameID>/07_美術素材_GameView`。下載 dev 素材前先問使用者。
2. 切圖：dev 的 `assets/<bundle>/import`（pack 合併 JSON）裡每張 SpriteFrame 有 `name`／`rect`／`rotated`，貼圖 uuid 由 deps 索引到 uuids（22 碼壓縮 uuid 用 Cocos base64 解），原圖在 `assets/<bundle>/native/<前 2 碼>/<uuid>.webp`；依 rect 裁出（rotated 要轉回）。
3. 常用：背景（BG／FG 上下兩張）、盤面底＋盤面框、彩金牌與標題字、OP JACKPOT 標誌、緞帶（左翅／中段／右翅切三張）、額外押注／購買特色／第三格面板、開關 on／off、餘額列與操作列圖示、SPIN（底＋外圈＋箭頭）、待機文字圖（BG／FG 各一組）、FG 的剩餘場次框、倍數球（球＋金框）、轉場與結算文字圖（YOU'VE WON、FREE SPINS）、買特色框（FeatureBoard、BUY／CANCEL 鈕、加減框）。
4. **白色 UI 圖示先染成 dev 的黃色存檔**（不可用 CSS mask 上色：用檔案直接開網頁時 mask 圖會被瀏覽器擋掉、整排圖示消失）。
5. **有邊框的圖一律九宮格**（border-image：邊角維持比例、只拉中間），不可整張拉伸（彩金牌、緞帶、押注按鈕、第三格、FG 框都曾因整張拉伸變形）。

**意象物（例：宙斯）**：dev 是 Spine 骨架動畫，不在 demo 裡即時播（WebGL 讀本機貼圖在直接開檔時會被擋），改成**預先逐格算好的透明動畫 webp**：

1. 用 dev 的遊戲引擎找到人物 prefab（例 `preload` bundle 的 `ZeusView`），取得骨架檔（`.bin`＝Spine 3.8 binary）、atlas 文字、貼圖；貼圖若用 SplitAlpha（主圖 RGB＋`alphaTexture`），兩張合成 RGBA（顏色為預乘 alpha）。
2. 用 spine-webgl 3.8（`EsotericSoftware/spine-runtimes@3.8` 的 `spine-ts/build/spine-webgl.js`）在本機伺服器頁面上逐格渲染（`preserveDrawingBuffer`、透明底），固定取景範圍（例 x −320～320、y 130～690 世界座標，0.75 倍）。**貼圖縮小時 atlas 的 size／xy／orig／offset 要同比縮**，否則部件會亂飛。
3. 動畫：待機（Idle，循環，32 格）＋動作（例：Show 舉手放雷電、Win 握拳，播一次 `loop=1`）；輸出 384×336、quality 約 72；動作圖左右與上緣 40px 淡出，避免光暈切成方框。暫存的骨架檔與渲染腳本放 scratchpad，做完刪掉，專案只留動畫 webp。
4. 擺放：腰帶（骨架切邊）對齊盤面上緣、藏在盤面後面；露出部分約占意象區高 72%、寬約 62%（同 dev）。

**版面規則**（Dev 模式開啟時）：

- **dev 沒有的區域不出現**（例：Mult 條隱藏）。
- 上方：彩金列（GRAND／MAJOR 上排、MINOR／MINI 下排、中間 OP JACKPOT）＋意象物，剩下的高度都給這區；盤面不拉高。
- 盤面：框整張疊在盤面上（框比例與盤面接近）、紫底只鋪在柱子內側；**盤面框貼齊手機左右邊**；格子比例同 dev（寬一點），符號放大到接近填滿格子；畫面不夠高時盤面等比縮小。
- 觸控手機：**SPIN 一定要在畫面內**（以 390×664 觸控手機尺寸驗證）。
- 緞帶：沒在報贏分時輪播 dev 的待機文字圖（BG／FG 各一組，3 秒換一張）。
- 押注模式：額外押注依序「標題 → 金額 → 開關」，第三格用 dev 面板放得獎明細。
- FG：背景換 FG 上下兩張（上圖延伸到盤面中線、下圖從中線接起，不露底色）；押注按鈕與操作列收起來，**餘額列保留**；左下剩餘場次（藍色數字）、中間倍數球、右下得獎明細；FG 自動接續，不用按 SPIN。
- 意象物動作：有贏分時播 Win；盤面有倍數球時播 Show。

**兩種模式都有的特色畫面**（Dev 模式用 dev 美術，關掉時用模擬器藍色卡片樣式）：

- 買特色：先跳確認框（說明文字、花費、押注加減、購買數量；數量 > 1 時每場結算完自動再買），按購買才開始；確認前不讓遊戲切到 BF。
- 進 FG 轉場：「恭喜獲得 N 免費遊戲」約 2.6 秒（可點掉）。
- FG 結算：本場 FG 總贏分（扣掉觸發局）約 3.5 秒（可點掉）。
- FG 自動接續：演出播放中先等。

**遊戲端設定**（放在載入 `demogame_common.js` 之前）：

```html
<script>window.DEMOGAME_DEV_SKIN = "./Source/Dev/";</script>
<script>window.DEMOGAME_DEV_HERO = { img: "Zeus_Idle.webp", x0: -320, x1: 320, y0: 130, y1: 690, yBottom: 292, yTop: 660, width: 571,
    anims: { show: ["Zeus_Show.webp", 1167], win: ["Zeus_Win.webp", 667] } };
  window.DEMOGAME_DEV_FEATURE = { idle: ["GameIdle_MSG1", "GameIdle_MSG2"], idleFg: ["GameIdle_MSG1_FG", "GameIdle_MSG2_FG", "GameIdle_MSG3_FG"], heroWin: true };</script>
```

- `DEMOGAME_DEV_HERO`：x0～y1＝動畫圖的世界座標範圍；yBottom／yTop＝要露出的範圍（腰帶到頭頂）；width＝人物寬；anims＝動作圖與毫秒數。
- `DEMOGAME_DEV_FEATURE`：idle／idleFg＝緞帶待機圖檔名（不含 .webp）；heroWin＝有贏分時播意象物動作。

**驗證**（每次改完自己截圖檢查，不交給使用者看）：手機 430×900、觸控手機 390×664、桌機 1300×900、直接開檔（file://）都要有意象物與圖示；Dev 模式開／關各走一次：一般轉、買特色確認（加減押注金額連動）、轉場、FG 全程自動跑完、結算；主控台沒有錯誤。對照 dev 截圖逐區比對（彩金、意象物、盤面框、緞帶、押注列、餘額列、操作列、FG 下半部）。

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
- **改共用檔必同時升所有遊戲 `index.html` 的 `?v=` 版號**（否則線上讀到舊快取），版號格式一律 **`日期-時分秒`**（取當下 Get-Date，例 `?v=20261127-165230`），JS 與 CSS 各自改到才升各自的；改之前先 grep 目前的版號。多個工作階段同時改共用檔時用這個格式就不會撞號、不會往回退（2026-11-27）。
- By Game 樣式與程式保留在該遊戲的 `index.html` 或遊戲專屬資源，不得放入共用檔案影響其他遊戲。
- 遊戲專屬 CSS 不得覆寫共用區域，除非本規範明確提供可覆寫的 CSS Variable 或 Hook。

### 2.3 符號顯示規則（所有遊戲）

盤面符號一律依下列規則顯示，樣式由 `demogame_common.css` 的 Symbol display standard 統一套用：

| 狀態 | 顯示 |
| --- | --- |
| 該符號有美術（或 icon） | 只顯示符號圖；**不顯示符號代號、不畫符號框**（無框線、無底色） |
| 該符號無美術，或圖片載入失敗 | 顯示**符號框＋符號代號** |

- 符號代號（`M1`、`M2`、`A`、`C1`…）一律使用一般字重，**不得使用粗體**。
- 符號框＋代號的樣式所有遊戲統一（共用 `demogame_common.js` 依格子代號自動套用，各遊戲不另設；沒有特別要求就照這套）：沒圖時一定顯示符號代號（Scatter 一律顯示 C1、Wild 一律顯示 WW），只露出一部分的格子（例如頂端 peek 列）畫成整顆符號被盤面上緣截斷（頂端不畫框線），文字上下左右置中、Consolas 19px 一般字重、文字本身不加底色；M 獎與字獎（A／K／Q／J／10）都有底版，字獎深藍底，M1～M8 用同亮度、不同色相的低彩度漸層（M1 酒紅、M2 靛紫、M3 墨綠、M4 寶藍、M5 青、M6 梅紫、M7 棕、M8 橄欖）；C1／C2／SC 橘色亮漸層；Wild 青綠漸層；金框符號保留原底色、外框一律金色，且跟著符號一直顯示（得分時也保留）。Help 賠率表的代號方格用同一套配色。H014 數字格不套用。
- 有符號美術的遊戲必須接入共用圖片介面：頁面在載入 `demogame_common.js` 前定義 `window.DEMOGAME_IMAGE_TOGGLE = { supported: true, defaultEnabled: true, setEnabled(enabled) { … } }`，`setEnabled` 內切換是否輸出符號圖並重繪目前盤面。符號圖一律開啟，Setting **不再有 Image 開關**（2026-11-20 起改為「顯示符號 ID」）；只有圖片載入失敗時共用模組才呼叫 `setEnabled(false)` 改用文字。
- **「顯示符號 ID」開關**（共用，Setting，2026-11-20；英文 Show Symbol ID）：勾選後在盤面每個符號的正中間疊上符號代號（M1、M2、A、WW、C1…），方便對照 Log／輪帶；狀態存 `localStorage`（`slotDemoSymbolId`），預設關閉。代號依序取 `window.DEMOGAME_SYMBOL_ID(cell)` → 格子內 `data-symbol-id` → `.symbol-code` 文字 → 符號圖 `alt` → `.slot-symbol-label`／`.code` 文字；顯示名稱跟代號不同的遊戲（例如 code 顯示 Wild）要在格子內補 `data-symbol-id`。
- 有輸出符號圖的格子必須加上 `has-symbol-art`；圖片載入失敗時移除此 class 並改顯示代號。
- **圖片預載（必做）**：放到網頁上時，圖片若等第一次用到才下載，盤面會先出現空白格。有符號美術的遊戲必須在 `DEMOGAME_IMAGE_TOGGLE` 加上 `images`：本遊戲會用到的**所有**圖片網址（陣列，或回傳陣列的函式），包含大符號長圖、金框等所有變體。共用模組會在開局前預載並解碼完成：
  - 預載期間擋住點擊與鍵盤；超過 120 ms 才顯示「載入圖片 n / N」遮罩，避免已有快取時畫面閃一下。
  - 解碼最多等 1.5 秒；分頁在背景時略過解碼（瀏覽器在背景分頁不會完成 `decode()`），不得因此卡住遮罩。
  - 任一張載入失敗：改用文字顯示，並提示失敗張數；不得停在載入畫面。
  - 預載邏輯只寫在 `demogame_common.js`，遊戲專屬程式只提供 `images` 清單，不得自行另寫預載。
- **圖片格式**：Demo 使用的符號圖一律用 WebP（`quality 90`、保留透明），檔名與原 PNG 相同、副檔名改 `.webp`，放在 `Source/Image/`；原始 PNG 保留作為美術原檔，Demo 不引用。
- 無美術時的代號可使用共用標籤 `<span class="slot-symbol-label">代號</span>`（置中、一般字重）。
- 沒有任何符號美術的遊戲，**預設用 icon（emoji）當符號圖**，同樣接共用圖片介面（`defaultEnabled: true`、`images: []`）；icon 依符號主題挑（例：H027 皇冠 👑、H032 糖骷髏 💀），用 `.sym-icon` 疊在格子上並加 `has-symbol-art`（2026-11-03 起）。
- 中獎、轉換等**狀態**框線（`.hit`、`.convert`、`.wild-mark`、`.fx-win`）不受此規則影響。
- 符號一體：符號的字、框、底板是一體，所有動畫（長出來、消除、補牌、掉落）都整格一起動，不能只有部分變化（例如框先出現、字才長出來）。顯示得分框時，沒得分的符號完全不變（不變暗、不換框）。
- 得分符號只把外框換成藍色框起來（金框符號得分時保留金框、外圈加藍框）（共用 `demogame_common.js` 套用），不放大、不閃、不跳；各遊戲不得另做中獎動畫。消除與掉落動畫不受影響。
- Hook：框線本身屬規則狀態、且沒有對應美術時（例如純 CSS 的金框），在該格加 `keep-symbol-frame` 保留框線。金框若已有美術（例如 Frame 圖或金框版符號圖），不得再疊加 CSS 框。

### 2.4 最小 index.html 骨架

共用模組靠固定 id 找元素，**下列 id 不可改名**；其餘區塊可依遊戲增加。共用區的固定標籤一律寫英文（Credit、Spin、Bet Mode…），中文由共用模組依語言翻譯；By Game 文字由遊戲自己翻。範例中的 `H0xx`、文字與數值都是佔位。

```html
<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>H0xx 遊戲名稱 Demo</title>
  <style>/* By Game 樣式：只寫盤面、符號、狀態膠囊等第 2.1 節範圍（FG 看板樣式由共用 CSS 提供） */</style>
  <link rel="stylesheet" href="../demogame_common.css?v=YYYYMMDDa">
</head>
<body class="slot-simulator">
  <main class="phone">
    <div id="feature-bar">                                   <!-- 標題列；共用模組把報告／說明／重置搬到右側 -->
      <span id="game-title"><span id="gameId">線上 Game ID</span> <span id="gameName">英文名稱</span></span>
    </div>
    <div id="strip-bar">                                     <!-- 狀態列（共用模組隱藏，只把 #multPill／#sumPill 鏡射到盤面上方資訊條） -->
      <div class="feature-strip" id="featureDisplay">
        <span id="modeText">Base Game</span>
        <span id="featureStatus"></span>
        <span class="feature-pill hidden" id="multPill"><span class="k">Multiplier</span><span class="v" id="multValue">x1</span></span>
        <span class="feature-pill hidden" id="fgLeftPill"><span class="k">FG Left</span><span class="v" id="fgLeftValue">0/0</span></span>
      </div>
    </div>
    <div id="app-shell">
      <section id="grid-panel">
        <div class="board-shell"><div class="board-grid" id="board"><!-- 每格 <div class="cell">…</div> --></div></div>
        <div class="message-bar" id="messageBar">Ready — press Spin</div>
      </section>
      <aside id="right-panel">                               <!-- 共用模組把下面三區搬到盤面下方 -->
        <section id="credit-bar">
          <div class="credit-cell"><span class="i-label">Credit</span><span class="i-value hi" id="balanceValue">10,000</span></div>
          <div class="credit-cell"><span class="i-label">Bet</span><span class="i-value" id="betValue">1.00</span></div>
          <div class="credit-cell"><span class="i-label">Win</span><span class="i-value hi" id="winValue">0</span></div>
        </section>
        <section id="play-panel" class="control-zone action-zone">
          <span class="zone-label">Play</span>
          <div class="zone-body play-main-controls">
            <button id="spinBtn" type="button">Spin</button>
            <button id="autoBtn" type="button">Auto</button>
            <div class="bet-stepper">
              <button id="betMinusBtn" type="button">&minus;</button>
              <button id="betBtn" type="button">Bet 1.00</button>
              <button id="betPlusBtn" type="button">+</button>
              <div class="bet-menu hidden" id="betMenu" role="listbox"></div>
            </div>
            <label class="speed-control" for="speedRange">Speed
              <input id="speedRange" type="range" min="1" max="5" step="1" value="1"><span id="speedValue">x1</span></label>
          </div>
          <div id="play-debug-controls" class="zone-body play-debug-controls debug-hidden">
            <button id="previousStepBtn" type="button" disabled>&#9664;&#9664; Previous</button>
            <button id="nextStepBtn" type="button" disabled>Next &#9654;&#9654;</button>
          </div>
        </section>
        <section id="bet-mode-panel" class="control-zone mode-zone">
          <span class="zone-label">Bet Mode</span>
          <div class="zone-body">                            <!-- 只放遊戲實際有的模式 -->
            <button class="mode-btn is-active" id="normalBetBtn" type="button">Normal Bet</button>
            <button class="mode-btn" id="extraBetBtn" type="button">Extra Bet (2x)</button>
            <button id="buyFeatureBtn" type="button">Buy Feature (50x)</button>
            <button id="superFeatureBtn" type="button">Super Feature (200x)</button>
          </div>
        </section>
        <section id="simulation-stats">
          <h3>Simulation Stats</h3>                          <!-- 共用模組改名「基本指標」 -->
          <div class="simulation-row"><span class="s-label">Total Rounds</span><span class="s-value" id="roundCountValue">0</span></div>
          <div class="simulation-row"><span class="s-label">RTP</span><span class="s-value" id="rtpValue">0.00%</span></div>
          <div class="simulation-row"><span class="s-label">Hit Rate</span><span class="s-value" id="hitRateValue">0.00%</span></div>
          <div class="simulation-row"><span class="s-label">FG Trigger</span><span class="s-value hi" id="fgTriggerValue">0</span></div>
          <div class="simulation-row"><span class="s-label">Max Multiplier</span><span class="s-value hi" id="maxMultiplierValue">x0</span></div>
          <div class="simulation-row" data-by-game><span class="s-label">特殊指標名稱</span><span class="s-value" id="xxxValue">0.00%</span></div>
        </section>
      </aside>
    </div>
    <section id="controls" class="debug-off">
      <div id="set-rng-panel" class="control-zone set-rng-zone debug-hidden">
        <span class="zone-label">Set RNG</span>
        <div class="zone-body set-rng-controls">
          <label class="debug-rng-field" for="cardRangeSelect">Card BG Range
            <select id="cardRangeSelect"><option value="">Auto</option></select></label>   <!-- 有卡片系統才放 -->
          <label class="debug-rng-field" for="scriptSelect">腳本
            <select id="scriptSelect"><option value="">無</option></select></label>       <!-- 遊戲發想必放 -->
          <label class="debug-rng-field" for="rngInput">RNG
            <input id="rngInput" type="text" autocomplete="off" spellcheck="false"></label>
          <button id="setRngResetBtn" type="button">Reset</button>
        </div>
      </div>
    </section>
    <section id="live-log-wrap" class="diagnostic-region debug-only debug-hidden">
      <div class="live-log-header diagnostic-header"><span>Log</span><button id="clearLogBtn" type="button">Clear</button></div>
      <div id="liveLogBody" role="log" aria-live="polite"></div>
    </section>
    <section id="change-log-wrap" class="diagnostic-region debug-only debug-hidden">
      <div class="diagnostic-header">版本紀錄</div>
      <div id="changeLogBody"><!-- 第 7 節：<article class="change-log-entry"><h4>v1（1.0.0.0）</h4><ol><li>…（MM/DD）</li></ol></article> --></div>
    </section>
    <section id="settings-wrap" class="diagnostic-region">
      <div class="setting-header diagnostic-header">Setting</div>
      <div class="setting-body">
        <label class="setting-toggle" for="debugModeInput"><input id="debugModeInput" type="checkbox"> Debug Mode</label>
        <label class="config-control" for="versionSelect">Version <select id="versionSelect"></select></label>
        <label class="config-control" for="configSelect">Config <select id="configSelect"></select></label>
        <label class="config-control" for="languageSelect">Language
          <select id="languageSelect"><option value="zh">繁中</option><option value="en">English</option></select></label>
        <button id="helpBtn" type="button">Help</button>
        <button id="resetBtn" type="button">Reset</button>
      </div>
    </section>
    <div class="footer-note"></div>                          <!-- 共用模組寫入最後調性更新／唯一碼 -->
  </main>
  <dialog id="helpDialog">
    <div class="help-dialog-shell">
      <div class="help-dialog-header"><h2 id="helpDialogTitle">Game Help</h2><button id="closeHelpBtn" type="button">Close</button></div>
      <div id="helpContent" class="help-content"></div>
    </div>
  </dialog>
  <script id="embeddedGameHelpMarkdown" type="text/plain">（game_help.md 全文，格式見 2.8）</script>
  <script src="./Versions/version_manifest.js?v=YYYYMMDDa"></script>
  <script>/* ① 選版本與系列、依序載入 config（見 2.5），同步填 #versionSelect／#configSelect */</script>
  <script>/* ② 遊戲主程式：Render、動畫、狀態、共用介面（見 2.6） */</script>
  <script>/* ③ window.DEMOGAME_* 宣告（見 2.6） */</script>
  <script src="../demogame_common.js?v=YYYYMMDDa"></script>
</body>
</html>
```

- 共用模組會自行建立：Config 合併選單 `#demogameConfigSelect`、隱藏的卡片開關 `#cardSystemInput`、「顯示符號 ID」`#symbolIdInput`、特殊指標區 `#by-game-stats`、玩法簡介 `#demogame-overview`、累積倍率線型 `#demogame-cumulative-chart`、Simulation 面板 `#batch-simulation`、盤面上方資訊條 `#demogame-info-bar`、標題列按鈕 `#demogameTitleActions`、導覽、圖片預載遮罩。遊戲**不要**自己做這些元素。
- 已停用、不必放的舊元素：Spin Result 面板 `#log-wrap`、Force FG `#forceFgInput`、Profile 選單 `#cardProfileSelect`（放了也會被共用模組隱藏）。
- `#messageBar` 是 By Game 區域，但樣式由共用模組統一；`.debug-hidden`、`.hidden` 由共用 CSS 定義為隱藏。

### 2.5 載入順序與生命週期

1. `<head>` 先放 By Game `<style>`，再載入 `../demogame_common.css`。
2. `<body>` 依序：骨架 HTML → Help 原文 → 版本清單 → config 載入 → 遊戲主程式 → `DEMOGAME_*` 宣告 → **最後一行**才載入 `../demogame_common.js`。共用模組載入當下就讀 DOM 與 `window.DEMOGAME_*`、`window.demogameSimulationModes` 等，所以這些都必須在它之前定義；`demogameSimulateRound`、`demogameAddCredit` 也要在它之前或同一個同步流程內定義。
3. config 載入（同步，用 `document.write('<script src=…>')` 或直接 `<script src>`）：
   - 讀 `Versions/version_manifest.js`，依網址 `?version=` 選版本（預設 `current`）；目前版本讀根目錄 config，舊版本讀 `Versions/<版本>/` 的封存 config。
   - 依 `?config=`（或 localStorage 記憶）選系列 A／B；以 `<script>` 載入該系列的 `config_<產線編號><系列>.js`，把 `base` 疊上各 `tiers[層級]` 展開成一組（例 `window.H0xx_BOX_SET = { small, mid, big }`），先用中 Bet 那層。`Base` 只用 `base`（卡片關）。
   - 檢查：`base` 的 `excel_version` 必須等於版本第 1 碼、各層級版本第 1 碼與 `base` 相同、各層級有 `card_system`，缺層級或不符就 `throw new Error(…)`（第 1 節：不得靜默使用舊值）。
   - 同一段同步填 `#versionSelect`（每個版本一個 `<option value="四碼版本">`）與 `#configSelect`（每個系列一個 `<option value="A">A</option>`；有 Demo config 再加一個，value 含 `Demo`；多產線時加 `data-line`）；兩者的 `change` 都改網址參數後重新載入頁面。
4. 遊戲主程式啟動時：檢查必要 config 欄位（缺就 `throw`）、畫初始盤面、寫第一行 Log `Config <名稱> loaded | Version <版本> | Card System On|Off`（重置時共用模組會只保留這一行）。
5. 每一局（含 FG）流程：鎖住 `#spinBtn`（`disabled = true`）→ 取 RNG 碼 → 在 `demogameRng.run()` 內一次算完整局結果 → 播動畫（時間全部取 `demogameMotion`）→ 更新 Credit／Win／統計 → 呼叫 `demogameLineChart.record()`、`demogameHistory.record()` → `await demogameRoundPause()` → 解鎖 `#spinBtn`。長按 Spin、Auto 都靠 `#spinBtn.disabled` 判斷「這局結束了沒」，所以忙碌期間一定要 disabled。

### 2.6 遊戲端必須提供的介面

**全域宣告（在載入 `demogame_common.js` 前設定）**

| 名稱 | 型別 | 必要性 | 說明 |
| --- | --- | --- | --- |
| `window.<ID>_CONFIG` | object | 必要 | 目前使用中的 config：`config_<產線編號><系列>.js` 的 `base` 疊上目前層級展開後的物件（檔案本身的變數 `window.<ID>_CONFIG_<產線編號><系列>` 不給共用模組用）；名稱以 `_CONFIG`（或 `_BOX_DATA`）結尾，共用模組從這裡找 `card_system`、`excel_version`、`rtp_label`、`reel_num`、`window_size`、`paylines`。換層級或選卡片開／關時要同步換掉這個物件。 |
| `DEMOGAME_PRODUCT_LINE` | string | 必要 | 產線編號，例 `"01"`；發想中 `"99"`。 |
| `DEMOGAME_SHARED_BASE` | boolean | A／B 共用自然機率時 | `true` 時 Config 選單只列 A 的 Base。 |
| `DEMOGAME_CARD_SYSTEM_SUPPORTED` | boolean | 選用 | `false` 時強制沒有卡片系統（只列 Base）。 |
| `DEMOGAME_VERSION_OVERRIDE` | string | 沒有 `#versionSelect` 選項時 | 版本選單顯示值；否則依序取 config 的 `excel_version`／`game_version`／`version`。 |
| `DEMOGAME_IMAGE_TOGGLE` | object | 有符號圖（含 emoji）時必要 | `{ supported: true, defaultEnabled: true, images: [網址…] 或 () => [網址…], setEnabled(enabled, { initial }) }`；`setEnabled` 切換是否輸出符號圖並重繪目前盤面（第 2.3 節）。 |
| `DEMOGAME_SYMBOL_ART` | `{ 代號: 網址 }` | 有符號美術時 | Help 賠率表、特殊符號卡片、內文 `[代號]` 小圖用。 |
| `DEMOGAME_SYMBOL_ID` | `(cell) => string \| null` | 選用 | 「顯示符號 ID」取代號的自訂函式；不設就依第 2.3 節的順序找。 |
| `DEMOGAME_HISTORY` | boolean | 必要 | `true` 時統計區出現 BG／FG 最大倍數。 |
| `DEMOGAME_REPORT_URL` | string | 有 `report.html` 時 | 例 `"./report.html"`。 |
| `DEMOGAME_LAST_TUNING`、`DEMOGAME_TUNING_CODE` | string | 必要 | 第 5 節。另可設 `DEMOGAME_LAST_CODE`（程式最後調整）、`DEMOGAME_LAST_UPDATE`（任何東西最後調整），有設才多顯示一行。 |
| `DEMOGAME_OVERVIEW` | object | 必要 | `{ competitor, expect, changes: [...], label?: "base", en?: { expect, changes } }`（第 5 節玩法簡介）。 |
| `DEMOGAME_INFO_BAR` | boolean | 選用 | 設 `false` 不用共用的盤面上方資訊條（遊戲自己有倍數條時）。 |
| `DEMOGAME_WAY_BOARD`、`DEMOGAME_WAY_SHAPE`、`DEMOGAME_PAYLINES` | 見第 4 節 | config 讀不到盤面／賠付線時 | Help 走線圖用。 |
| `demogameSimulationModes` | `[{ value, label }]` | 必要 | Simulation 面板的押注模式選單，只列實際支援的模式。 |
| `demogameSimulationBets`、`demogameSimulationBetDefault` | `[{ value, label }]`、`() => value` | 有小中大 Bet 時 | Simulation 面板的押注大小選單與預設值。 |
| `demogameSimulateRound` | `({ mode, bet }) => result \| Promise<result>` | 必要 | 第 5 節；`result` 欄位：`multiplier`、`lineMultiplier`、`fgTriggered`、`maxMultiplier`、`retryLimitExceeded`、`retryCount`、`bgCascade`、`fgCascades`（陣列）。沒有消除的遊戲不回 `bgCascade`／`fgCascades`，面板就隱藏消除分布。 |
| `demogameAddCredit` | `(n) => void` | 必要 | 餘額加 n（顯示金額，依內部單位換算）並重畫。 |

**DOM 狀態約定（遊戲要維持，共用模組靠這些判斷）**

| 狀態 | 遊戲要做的事 |
| --- | --- |
| 盤面格子 | `#board` 底下每格一個 `.cell`；有符號圖的格子加 `has-symbol-art`；得分格加 `hit`（共用模組畫藍框）；純 CSS 金框加 `gold`（或 `special-gold`）與 `keep-symbol-frame`；無圖時代號放在 `.slot-symbol-label`（或 `.symbol-code`）裡。 |
| FG 中 | 進 FG 時 `document.body.classList.add("fg-mode")`，回 BG 時移除。 |
| 忙碌中 | 一局進行中 `#spinBtn.disabled = true`，結束才解除。 |
| 押注模式 | 目前模式的按鈕加 `is-active`；不支援的模式按鈕 `disabled` 並加 `is-locked`。按鈕 id 固定：`normalBetBtn`、`extraBetBtn`（第二種 EB 用 `extraBet2Btn`）、`buyFeatureBtn`、`superFeatureBtn`（或 `buySuperFeatureBtn`）。 |
| 特色結束 | FG 結算看板關閉、回到 BG 後 `document.dispatchEvent(new Event("dg-feature-end"))`。 |
| 結算看板 | 看板元素加 `data-hold-stop` 屬性（第 5 節）。 |
| Debug Mode | `#debugModeInput` 勾選時，移除 `.debug-only`、`#set-rng-panel`、`#play-debug-controls` 的 `debug-hidden`，並把 `#controls` 的 `debug-off` 拿掉；取消勾選時加回。 |
| 倍數膠囊 | 有需要顯示在盤面上方的倍數時，放在 `#strip-bar` 裡的 `#multPill`（或 `#sumPill`）：`<span class="k">名稱</span><span class="v">值</span>`，不顯示時加 `hidden`。 |
| 特殊指標 | 統計區的非共用列加 `data-by-game`（共用列只有 `roundCountValue`、`rtpValue`、`hitRateValue`、`fgTriggerValue`、`maxMultiplierValue` 五個）。 |

**遊戲要監聽的事件**

| 來源 | 遊戲要做的事 |
| --- | --- |
| `#configSelect` 的 `change` | 共用合併選單選了系列後，會把值寫回 `#configSelect` 並發出 `change`：遊戲改網址 `?config=` 重新載入，或直接換 config。不可依選項文字判斷。 |
| `#cardSystemInput` 的 `change`／`document` 的 `demogame:card-system-change`（`detail.enabled`） | 卡片系統開關改變；也可在每局開頭讀 `window.DEMOGAME_CARD_SYSTEM_ENABLED`。 |
| `#resetBtn` 的 `click` | 遊戲清自己的統計、餘額、盤面與 FG 狀態。共用模組同時會清倍率線型、BG／FG 最大倍數、腳本、RNG 欄、Simulation 累積，並連按 `#betMinusBtn` 把押注退回第一檔。 |
| `#languageSelect` 的 `change`（值 `zh`／`en`） | 重寫 By Game 文字；共用區文字由共用模組處理。 |
| `#rngInput` 的 `input`、`#cardRangeSelect`／`#scriptSelect` 的 `change` | 同步遊戲內的指定狀態（互斥清除由共用模組處理，被清的欄位也會發事件）。 |

### 2.7 共用模組 API 一覽

`demogame_common.js` 載入後提供下列 API（遊戲在執行期呼叫，建議寫成 `window.xxx?.()` 以免單獨開檔時出錯）：

| API | 參數／回傳 | 用途與呼叫時機 |
| --- | --- | --- |
| `demogameMotion.level()` | → 1～5 | 目前 Speed（讀 `#speedRange`）。 |
| `demogameMotion.reelSpinMs()`、`stopStaggerMs()`、`dropMs()`、`growMs()` | → 毫秒 | 動畫時間（第 4 節數值）；所有轉輪、掉落、長出來的時間都從這裡取。 |
| `demogameMotion.grow(cells)` | 格子陣列 → 毫秒 | 原地補牌的新符號套「長出來」動畫。 |
| `demogameMotion.dropSpin(board, columnsOf, render)` | → Promise | 掉落類遊戲的 Spin 動畫：`columnsOf()` 回傳每欄由上到下的 `.cell` 陣列，`render()` 同步畫出結果盤面；函式先複製舊盤、呼叫 `render()`，再播舊盤掉出、新盤掉入。 |
| `slotBuildDropMotion(rows, cols, cleared)` | `rows`＝列數或每欄列數陣列，`cleared`＝`[[row, col], …]` → `{ "row-col": { type: "new", rows, groupSize } \| { type: "settle", rows } }` | 掉落補牌時算出每格是新符號（從上方掉入）還是既有符號下移幾格。 |
| `demogameRoundPause()` | → Promise | 每一轉算完分後呼叫（500 ms；長按連續 Spin 時 250 ms）。 |
| `demogameRng.takeInput()` | → `null` 或 `{ config, mode, card, opts, seed }`；格式錯誤會 `throw` | 每局開頭呼叫：有填 RNG 碼就用它的 `seed` 與 `opts`，沒有就 `demogameRng.newSeed()`。 |
| `demogameRng.run(seed, fn)` | → `fn()` 的回傳 | 執行期間 `Math.random` 換成種子序列；整局結果（BG＋全部 FG）必須在 `fn` 內同步算完，表演用亂數放在外面。 |
| `demogameRng.format({ config, mode, card, opts, seed })`、`parse(text)`、`seeded(seed)` | 字串／物件／亂數函式 | 產生 Log 的 `RNG <碼>`、解析碼、取得獨立的種子亂數。 |
| `demogameLog(text, type)` | `type`＝`info`／`mode`／`rng`／`result`／`cascade`／`error` | 寫一行 Log（新的在上、最多 500 行）；行格式見第 5 節。`RNG <碼>` 行會自動變成可點。 |
| `demogameLineChart.record(multiplier, "NB" \| "EB")`、`setMode(mode \| null)`、`reset()` | — | 每局（含 FG）結束記一次累積倍率線型；BF／SF 不記。押注模式按鈕沒有 `is-active` 時用 `setMode()` 告知目前模式。 |
| `demogameHistory.record({ bg, fg })`、`reset()` | 倍數（÷ 底注） | BG 局結束記 `bg`、FG 結束記 `fg`。 |
| `demogameWinLines.draw(container, lines)`、`clear(container)` | `lines`＝`[[cell, cell, …], …]` | 連線遊戲畫得分線（第 4 節）；盤面重畫後要重畫。 |
| `demogameFxTarget(id)` | → 元素 | 飛行動畫的目標（第 5 節）。 |
| `demogameSharedText(english)` | → 依語言的字串 | 取共用字典的翻譯（遊戲要顯示共用術語時用）。 |
| `demogameTagSymbols()` | — | 遊戲自己的動畫重畫盤面後立即套用無圖符號配色。 |
| `DemogameImagePreload.preload(urls)` | → `Promise<{ failed }>` | 額外圖片要預載時用（一般只要填 `DEMOGAME_IMAGE_TOGGLE.images`）。 |
| `demogameGuide()` | — | 手動開始新手導覽。 |
| `slotBindCommonControls(actions)` | `{ spin, toggleAuto, normalMode, extraMode, buyFeatureMode, betMinus, betPlus, toggleBetMenu, speedChange, previousStep, nextStep, debugChange, resetRng, clearLog, reset, configChange, languageChange, openHelp, closeHelp, rngChanged, documentClick }` | 選用：一次把骨架上的固定按鈕綁到遊戲函式。 |
| `slotFx` | `ensureLayer`、`popCells`、`spawnCoins`、`multiPop`、`winFloat`、`totalWin`… | 選用特效圖層；不得用來做中獎強調（第 2.3 節）。 |
| `demogameFgBanner.trigger({ spins, icon, auto })`、`end({ win, bet, format, auto })` | → Promise（看板關閉時 resolve） | FG 觸發／結算看板（第 5 節 FG 看板）。`trigger` 顯示「免費遊戲／N 場」（`icon` 預設 `C1`，取 `DEMOGAME_SYMBOL_ART`）；`end` 顯示「免費遊戲結束／總贏分／金額／倍數（`win ÷ bet`，2 位小數）」並自帶 `data-hold-stop`。`auto` 傳目前是否 Auto（布林或函式）。 |
| `demogameFgBanner.show({ icon, title, sub, count, note, html, holdStop, auto, autoMs })`、`close()`、`isOpen()` | → Promise | 自訂內容的看板（卡片依序 icon／title／sub／count／note；`html` 整段取代）；`icon` 可給代號、圖片網址或 HTML。 |
| `demogameHelp.render(md, { lang, bet, baseBet, format, config, configOptions })` | → `#helpContent` | 解析第 2.8 節格式的 md 輸出到 `#helpContent`：`lang`＝`zh`／`en`（預設讀 `#languageSelect`）、`bet`＝目前底注（數字或函式，預設讀 `#betValue`）、`baseBet`＝md 賠率數字的基準（預設 `config.base_bet`，再無則 100）、`format`＝金額格式函式。md 沒有賠率表且有給 `config` 時，自動用 `configPaytable` 補上；完全沒內容時輸出 `.help-load-error`。Help 開著時押注或語言改變會自動重畫。 |
| `demogameHelp.load({ url, embeddedId })`、`open(opts)`、`parse(md)` | `load` → `Promise<md>`；`open` → 載入＋`render`＋開 `#helpDialog` | `load` 先 fetch `./game_help.md`（`file://` 略過），讀不到用內嵌 `#embeddedGameHelpMarkdown`；`open(opts)` 一次做完，`#helpBtn` 直接綁它即可。 |
| `demogameHelp.configPaytable(cfg, { type, bet, baseBet, format, counts, reels, skip })` | → `.help-payout-table` 元素或 `null` | 由 config 產生賠率表（之後共用版式排成每個符號一張「N - 派彩」卡片）。`type` 不給時自動判斷：有 `paylines`／`line_num`／`lines` → Lines；`pays` 是物件或有 `max_ways`／`ways` → Ways；其餘 → 全盤計數。派彩讀 `pay_table` → `pays` → `paytable`（陣列依符號 index，或物件 key＝index／代號）；符號名讀 `symbol_str` → `symbol_names` → `symbol_codes`。Ways／Lines 欄位＝(`reel_num` − 欄數 + 1)～`reel_num` 連；計數型依 `counts` → `count_labels` → `min_cluster` 起算（最後一欄加「+」）。派彩 ÷ `baseBet`（預設 `base_bet` → `default_coin_in` → 1）× 目前押注；全 0 的符號與欄略過。遊戲也可設 `window.DEMOGAME_HELP_CONFIG`（＋選用 `DEMOGAME_HELP_CONFIG_OPTIONS`），`#helpContent` 出現 `.help-load-error` 時共用模組自動補上。 |

共用模組設定的唯讀狀態：`window.DEMOGAME_CARD_SYSTEM_ENABLED`（卡片系統是否開）、`window.DEMOGAME_SYMBOL_IMAGES_ENABLED`（符號圖是否在用）、`window.demogameSpaceHolding`（是否正在長按連續 Spin）、`window.__demogameImageCache`（已預載的 Image 物件）。

### 2.8 Help 資料格式

Help 原文＝`其他/game_help.md`（中間檔放 `其他/`，Demo 以 `./其他/game_help.md` 讀取）（固定檔名，舊名 `game_help_draft.md` 不再使用），整份貼進 `<script id="embeddedGameHelpMarkdown" type="text/plain">`（雙擊離線開啟時讀不到外部 .md）。格式：

```markdown
## PAYTABLE                      ← 區塊（## 開頭；名稱含 Meta 的區塊不顯示）

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 符號賠付值 | SYMBOL PAYOUT VALUES |
| 規則說明 | ▪ 所有符號必須由最左至右連續出現，方可獲獎。 | ▪ ALL WINS MUST BE ON CONSECUTIVE REELS FROM LEFTMOST TO RIGHT. |

### WILD SYMBOL                  ← 小節（### 開頭）

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 百搭符號 | WILD SYMBOL |
| 規則說明 | ▪ [WW] 可替代除 [C1] 以外的所有符號。 | ▪ [WW] SUBSTITUTES FOR ALL SYMBOLS EXCEPT [C1]. |

### 賠率表                        ← 小節名稱固定「賠率表」；副標題表之後先「繁中：」再「英文：」各一張賠率表

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 賠率表 | PAYTABLE |

繁中：

| 符號 | {5} 連 | {4} 連 | {3} 連 |
| --- | ---: | ---: | ---: |
| [M1] | {250} | {150} | {50} |

英文：

| SYMBOL | {5} OF A KIND | {4} OF A KIND | {3} OF A KIND |
| --- | ---: | ---: | ---: |
| [M1] | {250} | {150} | {50} |
```

- 每列第一欄 `Item` 只有三種：`主要標題`（區塊標題）、`副標題`（小節標題）、`規則說明`（一條規則，前面的 `▪` 會被去掉改成共用圓點）。

- `[代號]` 會換成符號小圖、`{數字}` 只是強調標記（顯示時去掉大括號）、`[走線圖-…]` 佔位列見第 4 節。賠率表數字是以 `base_bet` 為底的派彩，顯示時換算成目前押注（數字 ÷ `base_bet` × 目前底注），押注改變時重算。
- 遊戲用共用 API 輸出 Help（第 2.7 節）：`#helpBtn` 綁 `demogameHelp.open({ baseBet, bet, format, config })`，或自己載入 md 後呼叫 `demogameHelp.render(md, opts)`；不要再自寫 md 解析。API 依目前語言輸出到 `#helpContent` 的 DOM 結構固定如下（舊遊戲自寫 renderer 也必須輸出同一結構），之後的版式（置中、特殊符號卡片、兩欄符號卡片、內嵌小圖、走線圖）都由共用模組自動套用：

```html
<section class="help-section">
  <h3 class="help-section-title">區塊標題</h3>
  <div class="help-rule"><div class="help-rule-zh">規則一條</div></div>   <!-- 英文用 help-rule-en -->
  <h4 class="help-group-title">小節標題</h4>
  <div class="help-rule"><div class="help-rule-zh">…</div></div>
  <div class="help-payout-table">                                         <!-- 賠率表：第一列表頭，第一欄符號代號 -->
    <div class="help-payout-row"><div class="help-payout-cell">Symbol</div><div class="help-payout-cell">5</div>…</div>
    <div class="help-payout-row"><div class="help-payout-cell">M1</div><div class="help-payout-cell">5.00</div>…</div>
  </div>
</section>
```

- 讀不到 md 或 md 沒有賠率表時（第 4 節「Help 至少要有賠率表」），呼叫 `render`／`open` 時傳 `config`，由 `demogameHelp.configPaytable` 依目前押注產生賠率表（支援全盤計數型、Ways、Lines，依 config 的派彩結構自動判斷，必要時用 `configOptions.type`／`counts` 指定）；不用 API 的遊戲可設 `window.DEMOGAME_HELP_CONFIG`，`#helpContent` 出現 `.help-load-error` 時共用模組自動補上。

## 3. 補牌方式

每款有消除機制的遊戲，必須在 Game Rule、Config 對應說明與 Demogame 中指定唯一補牌方式。Simulator 與 Demogame 必須使用相同邏輯。

1. **消除後原地補牌**
   - 中獎符號消除後，只在原本的空格位置抽取並顯示新符號。
   - 盤面上未消除的符號維持原座標，不播放向下移動動畫。
   - 新符號在空格原位「長出來」（縮放 0→1，共用 `demogameMotion.grow()`），**不得播放掉落動畫**。
2. **消除後掉落補牌**
   - 中獎符號消除後，同一 Reel／Column 上方未消除的符號依重力向下補位。
   - 剩餘空格由新符號從盤面上方掉入。
   - 動畫必須區分既有符號的 Settle 與新符號的 Drop／Refill。
   - 掉落整段時間＝一輪從滾動到滾停的時間（共用 `demogameMotion.dropMs()`）。
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
- 轉輪滾動一律照 H020 超級寶石的滾法（做法見下一條「輪帶滾動做法」，不需參考 H020）：每輪是一條連續往下捲動的輪帶，由左到右依序停在結果上；不得用每一幀換一次符號的方式表現滾動。轉輪類遊戲停輪前要多往下滾約 18% 格高再回彈到正確位置（總時間不變，輪帶上方墊一格避免露出空白）；Speed 1～4 每輪至少滾 10 個符號，Speed 5 維持。掉落類遊戲（H013、H019、H027、H045、急速糖果 2、糖果狂歡 2500）Spin 不播輪帶滾動：舊盤面整欄往下掉出、新符號整欄從上方掉入並輕微回彈，由左到右逐欄錯開（Speed 5 同時），每欄時間＝`reelSpinMs()`，用共用 `demogameMotion.dropSpin()`；連消後的補牌方式維持各遊戲原本規則。
- 輪帶滾動做法（輪帶類遊戲，參考實作 H032 `reelStripSpin`）：結果在動畫前已算好並畫進 `#board`，動畫只是蓋在上面的表演，不得改結果。
  1. 每一輪在該輪格子上方蓋一個 `overflow:hidden` 的視窗（`position:absolute`，左右各多留 3px，避免外框光暈被切），動畫期間該輪真格 `visibility:hidden`。
  2. 視窗內放一條直的輪帶，由上到下：墊 1 格隨機符號（回彈時不露出空白）→ 結果盤面該輪各格的複本 → `extra` 格。`extra`＝max(列數＋3, round(該輪時間 ÷ 60), Speed 1～4 時 10)；`extra` 中最下面「列數」格放前一盤該輪各格的複本（下一條規則），其餘放從目前盤面隨機挑的符號複本。複本要清掉 `hit`、`fx-*` 等狀態 class。
  3. 輪帶起點 `translateY(-extra × 格距)`（此時視窗顯示的正是前一盤），用 Web Animations 往下捲：前 82% 時間捲到「超過終點」（超捲量見上一條），再回彈到 `translateY(0)`；先把起點寫進 `style.transform`，避免第一格閃出結果盤面。
  4. 第 n 輪（0 起算）時間＝`reelSpinMs() + stopStaggerMs() × n`，所以由左到右依序停；全部結束後移除視窗、恢復真格顯示。
- 前一個盤面要被捲走（2026-11-18 使用者）：下一次 Spin（含 FG 每轉、Respin）動畫的第一格必須仍是前一個盤面，由舊盤面往下捲走（輪帶類）或整欄掉出（掉落類）後，新盤面才從上方進來；**不得先把盤面換成新符號再開始滾**，也不得逐格換符號假裝滾動。輪帶類做法：滾動輪帶在動畫起點對到視窗的那幾格放前一盤每格的複本（Jumbo 大符號、Extra Reel 照實際位置與大小，清掉得分框等狀態），其餘才放隨機輪帶符號；共用 `demogameMotion.dropSpin()` 與掉落類遊戲本來就符合。新遊戲交付前以凍結動畫第一格截圖比對前一盤確認。
- 動畫時間統一由共用 `window.demogameMotion` 提供，各遊戲不得自訂：一輪滾動到滾停 `reelSpinMs()`＝700／520／380／260／180 ms（Speed 1～5），逐輪停錯開 `stopStaggerMs()`＝120／100／80／60／0 ms；掉落補牌 `dropMs()`、原地補牌長出來 `growMs()` 都等於 `reelSpinMs()`。
- 每一轉（BG 局與每一轉 FG）算完分後的停頓（不受 Speed 影響，Simulation 不停頓）：手動 Spin 固定停 0.5 秒（共用 `window.demogameRoundPause()`，長按連續 Spin 時減半）；**Auto 停 250ms，之後再 90ms 開始下一轉**（同 H032，2026-11-20 使用者），不得用更長的 Auto 間隔。
- BG、Cascade、FG、Retrigger 與 Feature 狀態按真實流程播放。
- FG 結束回到 BG 時，盤面還原成觸發 FG 那局的 BG 最終盤面（BF 為入場盤），Feature Status 回到基礎遊戲。
- Config、Version、Profile、押注層級、Card System 與 Language 只顯示實際支援的內容。
- Help 與 `game_help.md` 一致，不在 HTML 另維護一份規則。
- Help 至少要有賠率表：`game_help.md` 沒有賠率（或讀不到、只剩離線副本）時，由 Config 的 Paytable 依目前押注產生。
- Help 版式（共用 `demogame_common.js`，2026-11-18 照參考排版）：內容窄欄（最寬 600px）置中；區塊標題白色 20px 置中、副標題白色 16px 置中、區塊之間用分隔線；規則 14px 淺灰、前面圓點「•」、條與條之間留空；全大寫的英文規則自動轉成句首大寫（[代號]、{數字}、FG／RTP／C1 等縮寫與 Free Game、Wild 等功能名稱維持大寫）。賠率表顯示成兩欄符號卡片，每張是「符號＋由大到小兩欄（張數白、派彩金色）」，每張卡片都框起來（淡底色＋細框、圓角 10px、卡片間距 10px，樣式同特殊符號卡片；2026-11-20）；特殊符號（WW／W2／C1／C2…）放在賠率表這一區、一般符號格前面，跟一般符號之間不畫分隔線（分隔線只用在區和區之間），不可排進一般符號的兩欄格裡（2026-11-20 照參考排版）：每個特殊符號一張滿欄寬、有淡底色與細框的卡片，「左圖右文」，由上到下排（先 Wild 後 Scatter）：左邊符號圖（有美術 76px），右邊先是金色名稱（正式 Help 的副標題，例：百搭符號）再是該符號的說明條列；說明跟其他區完全同一種排法（靠左、圓點、同字級行高），不可置中或拿掉圓點。Help 所有內文的字級、行高、條距一律相同（14px／1.55，特殊符號說明也一樣）。內文裡的 [代號]（[WW]、[C1]、[M1]…）一律換成內嵌符號小圖，小圖不可撐高行高；彩金名稱 [GRAND]／[MAJOR]／[MINOR]／[MINI] 換成彩金列同色的粗體字（紅／紫／藍／綠），不留中括號；其餘遊戲沒有那個代號的圖就維持 [代號] 文字，不硬換；沒美術時特殊符號的圖改用代號方格。有符號美術的遊戲要定義 `window.DEMOGAME_SYMBOL_ART = { 代號: 圖片網址 }`，卡片用該圖；沒美術時，顯示與盤面同款的深色代號方格（C1／SC 金色、WW 綠色）。
- Help 走線圖（共用，2026-11-20）：正式 Help 的 `[走線圖-1,024 MAX WAYS]`、`[走線圖-3 OF A KIND PAYS 2 WAYS]`、`[走線圖-NO WIN]` 佔位列要原樣放進 Demo 的 Help 文字，共用程式會畫成盤面小圖（一格一格的盤面、金色圓點代表符號位置；NO WIN 把中斷的那一軸整軸標紅），三張排成一橫排、各自一張卡片、圖下寫說明。盤面大小讀 config 的 `reel_num`／`window_size`，讀不到的遊戲宣告 `window.DEMOGAME_WAY_BOARD = [軸數, 列數]`。
  - 三種遊戲類型的走線圖長相不同（2026-11-20 使用者提供正式 Help 的樣子），Demo 要照該類型畫，配色用 Demo 的深色樣式（淡底色卡片、金色標示、紅色標中斷軸），不照搬正式 Help 的底色：
    - **Way Game（固定路數，例 1,024 Ways）**：三張盤面圖排一橫排——`N MAX WAYS`（每格都有圓點）、`3 OF A KIND PAYS 2 WAYS`（第 1 軸 1 顆、第 2 軸 2 顆、第 3 軸 1 顆）、`NO WIN`（第 2 軸整軸標紅，其餘軸有圓點但連不起來）；圖下寫說明。共用程式已支援。
    - **Megaways（各軸高度可變）**：一樣是三張圖（`N MAX WAY`、`3 OF A KIND PAYS 2 WAYS`、`NO WIN`），但盤面要畫出實際形狀——各軸格數不同、有上方額外橫軸時（例：第 2～5 軸上方多一列）畫在盤面上方；`MAX WAY` 那張畫每軸最多格數且全部有圓點，另外兩張用高度不一的格子示範（大符號占多格仍算 1 顆）；`NO WIN` 同樣把中斷的那一軸整軸標紅。
    - **Line Game（固定賠付線）**：每條賠付線一張小盤面圖，該線經過的格子標亮（金色）、其餘格子暗色；圖下寫兩位數線號（`01`、`02`…），依線號由小到大排，一橫排 4 張；線的走法取自 config 的賠付線定義，不可手寫。
    - 三種畫法都在共用 `demogame_common.js`（2026-11-20），各遊戲不要自己畫，只要把正式 Help 的佔位列原樣放進 Help 文字並宣告必要設定：Megaways 宣告 `window.DEMOGAME_WAY_SHAPE = { reels: 6, rows: 5, top: [2, 5] }`（`rows`＝主盤面每軸最多格數；`top`＝上方額外橫軸涵蓋的軸，1 起算，沒有就省略），佔位列同 Way Game（例 `[走線圖- 32,400 MAX WAY]`）；Line Game 的佔位列是 `[走線圖 20 LINE]`／`[PAYLINE DIAGRAM 20 LINE]`，賠付線讀 config／Box 資料的 `paylines`（每條線是各軸在第幾列、0＝最上列），讀不到的遊戲宣告 `window.DEMOGAME_PAYLINES`；讀不到賠付線時維持原文字、不畫。
- 連線（Line）遊戲有得分時要在盤面畫出得分線：呼叫共用 `window.demogameWinLines.draw(盤面容器, [[格子元素…], …])`，每條得分線要依線圖（paylines）整條畫出、連過每一輪的格子中心，不能只畫中獎的那幾連，顏色依序輪替；每次重畫盤面後要重新呼叫。

## 5. Debug 與重現

Debug Mode 至少可查看：

- Config、Version、Profile、Bet Mode、Mode／Feature Price 倍數、base bet、實際模式押注、`bet_tier_amount`、押注層級、Link 資格、BG／FG Max Multiplier 與 Card System 狀態。
- Card 抽獎值、卡片區間與 Retry 次數。
- Table、Drop Mode 與盤面表（記在 Log）；停輪與整局抽樣以 RNG 碼重現（見下方「可重現 RNG」）。
- 初始盤面、每段 Cascade、Line／Ways Win、Multiplier 與最終結果。
- FG 觸發、局數、Retrigger、整包 Win 及即時 Log。
- 最後調性更新（共用，頁尾 `.footer-note`）：頁面在載入 `demogame_common.js` 前設 `window.DEMOGAME_LAST_TUNING = "YYYY-MM-DD HH:MM"`，頁尾顯示「最後調性更新：日期 時間」（24 小時制，到分鐘）。**只有數學模型或倍率（卡片）權重調整才更新**（與 `修改紀錄.md` 最新一項同日）；介面、演出、文件修改不更新。
- 唯一碼（共用，更新資訊的最後一行，2026-11-27 使用者）：同一個 `<script>` 再設 `window.DEMOGAME_TUNING_CODE = "XXXXXX"`（6 碼隨機碼，大寫英文＋數字，不用 0／O／1／I），頁尾在「最後調性更新」下一行顯示「唯一碼：XXXXXX」。**每次調性更新（換 `DEMOGAME_LAST_TUNING` 時）一定要產生新的唯一碼**；所有遊戲（正式專案、發想、克隆、其他）都要有。**每次 Demo 更新完，回報給使用者時都要寫出目前的唯一碼**，讓使用者對照線上頁尾判斷是不是最新調性。
- 數值報告按鈕（共用）：有數值報告 `report.html` 的遊戲，在載入 `demogame_common.js` 前設 `window.DEMOGAME_REPORT_URL = "./report.html"`，標題列右側出現「報告」按鈕（英文 Report），與說明、重置排在一起。
- BG／FG 最大倍數（共用，併在「統計」區，取代原「最高倍數」列）：頁面在載入 `demogame_common.js` 前設 `window.DEMOGAME_HISTORY = true`，每局呼叫 `window.demogameHistory.record({ bg, fg })`（BG 得分、該局 FG 總得分，皆 ÷ 底注）；沒有 FG 的遊戲只顯示 BG 列，重置清空。
- Log（共用 `window.demogameLog(text, type)`）：帶時間的即時紀錄，新的一行在最上面、舊的往下擠，Clear 清空，最多保留 500 行；所有遊戲行格式一致（照下列格式，參考實作 H045；`<盤面表>` 為該轉使用的 Table 名稱，沒有多張表的遊戲省略該欄），不記演出過程：
  - `Config <名稱> loaded | Version <版本> | Card System On|Off`
  - `#<局號> Normal Bet|Extra Bet|Buy Feature|Super Feature | Bet <押注>[ | Card Range set][ | Replay]`
  - `RNG <碼>`（可點，複製並填入 RNG 欄）
  - `BG|BF Entry | <盤面表> | Cascade <n> | C1 <n> | Win <得分> (<倍數>x)`
  - `Free Game triggered | <n> spins[ (Retrigger ×k)]`、`FG <i>/<n> | … | Win <得分>`、`FG complete | Total <得分> (<倍數>x)`
  - `Error | <訊息>`
- Simulation（共用，`#batch-simulation`）：N 局獨立數學模擬，Start 執行中只顯示「進行中」（English：Running），不跳局數。FG 觸發顯示「比例 (N 場)」；最高倍數為單局總得分倍數（BF ÷ 底注）；消除分布轉置為「消除次數 × BG／FG」，與倍率線型一樣各自框成一區並有標題。各遊戲提供：
  - `window.demogameSimulateRound({ mode })`：用與畫面相同的遊戲邏輯產生一局（不得另寫簡化數學），回傳 `multiplier`（總得分含 FG ÷ 實際押注）、`lineMultiplier`（BF ÷ 底注，其餘同 `multiplier`）、`fgTriggered`、`maxMultiplier`、`retryLimitExceeded`、`retryCount`、`bgCascade`、`fgCascades`；`mode` 只在該局暫時套用，不得改動畫面押注模式與統計。
  - `window.demogameSimulationModes = [{ value, label }]`：只列實際支援的押注模式，面板據此顯示押注模式選單。
  - `window.demogameSimulationBets = [{ value, label }]`（2026-11-20）：押注大小選單，放在押注模式選單右邊、樣式相同；選定值以 `demogameSimulateRound({ mode, bet })` 傳給遊戲，只用在模擬、不改玩家目前押注，並依該押注套用對應的小／中／大 Bet config；`window.demogameSimulationBetDefault()` 回傳預設值（目前押注）。
  - 模擬的累積結果依「押注模式＋押注大小」各自保存（2026-11-20）：換設定是切換到那組的累積（沒跑過就顯示空的），再按開始是接著那組繼續跑；只有按重置才把所有組合全部清空。
- 右欄區域可摺疊（共用）：右欄有標題的區域（基本指標、特殊指標、玩法簡介、倍率線型等）點標題即可收起／展開，標題左側有箭頭，收起時標題列上下置中；標題內的按鈕（放大「+」）不觸發摺疊。倍率線型預設收起，玩法簡介預設打開。玩法簡介的競品／期待／玩法各列之間用分隔線隔開（同特殊指標）。
- 下方除錯區可摺疊（共用）：版本紀錄／模擬／紀錄點標題列收起／展開；版本紀錄預設折疊，模擬、紀錄預設展開。
- 空白鍵＝Spin（共用，鎖住預設）：空白鍵只觸發 Spin（按 `#spinBtn`），擋掉瀏覽器預設的整頁往下捲與按到焦點所在的按鈕／勾選框；按住不連發。焦點在文字輸入欄、下拉選單時照常打字；說明視窗開著不 Spin；導覽開著時空白鍵關閉導覽。由共用模組在 window 捕獲階段處理，各遊戲自己的空白鍵監聽不會再收到（不會重複 Spin），新遊戲不用另外寫。
- 餘額加錢（共用）：「餘額」標籤右邊有純文字「+」（無外框），按一下餘額 +1000（顯示金額）。各遊戲在自己的作用域設 `window.demogameAddCredit = (n) => { 依內部單位換算後加進 state 餘額; 重畫; }`，沒設就不顯示「+」。
- 訊息列（盤面下方，贏分區，`#messageBar`）一律用下列文字（參考實作 H032；「」內為中文顯示，English 依序為 `Ready — press Spin`、`Spin`、`Free Spin`、`WIN`、`No Win`）：待命「準備完成 — 請按 Spin」；轉動「Spin」／「Free Spin」；每段得分「WIN x」，有倍數「WIN 原始 × 倍數 = 得分」（轉末才乘的遊戲在轉末顯示），每次閃一下（`#messageBar.fx-bar-hit`）；一轉結束「WIN 總分」或「未中獎」；FG 每轉「FG i/n · WIN x」或「FG i/n · 未中獎」，加局再接「 · +k FG」。除錯文字（Cascade／Pay／Drop／停輪等）只寫 Log，不上訊息列。
- 押注模式按鈕（共用）：一排排開，每顆 88px（放不下才縮）、高 34px、間距 6px；名稱 11px＋倍數另起一行 9px；未開放的模式 disabled＋`.is-locked`，壓黑（底 #0b111a、字 #4a5563），不寫「製作中」。
- 購買類按鈕（購買特色／超級特色等，共用）：一律藍色（底 #0077cc、白字、無外框），不可用綠色或其他顏色區分；按下去買進後壓暗（class `dg-buy-active`），到這場 FG 結束才恢復；壓暗的樣子跟買進期間另一顆被停用的購買按鈕完全相同（同藍底 #0077cc、白字、opacity .45），兩顆看起來一樣，不另用深色或綠色。樣式由 `demogame_common.js` 提供，各遊戲 index.html 不另寫顏色覆寫。特色結束時遊戲要發 `document.dispatchEvent(new Event("dg-feature-end"))`（放在 FG 結算看板關閉、回到主遊戲之後），共用程式收到就立刻恢復購買鈕；沒發的話只靠輪詢，連續 Spin 時會一直壓暗（2026-11-20）。
- FG 看板（蓋在盤面上，`#board .fg-banner`）：
  - 觸發看板：觸發 FG（含購買進場）後、第一場 FG 開始前顯示「免費遊戲／N 場」；有符號圖時帶觸發符號小圖（固定 72px，不得撐滿盤面蓋住文字）。
  - 結算看板：最後一場 FG 轉完（含加局全部轉完）後顯示「免費遊戲結束／總贏分／金額／倍數（總贏分 ÷ 底注，2 位小數）」，金額為整場 FG 的總贏分，不含觸發那一把的 BG 得分。
  - 關閉方式兩者相同：Auto 模式 1 秒後自動消失；非 Auto 要點盤面／看板或按 Spin 關閉。看板顯示期間背景不可捲動，看板消失後才進下一步（開始 FG／回到 BG）。
  - 長按 SPIN／空白鍵連續 Spin 時：結算看板不可被長按關掉，連續 Spin 到結算看板就終止，操作者要放開後重新按才繼續（看板元素加 `data-hold-stop`，共用 `demogame_common.js` 看到就停止連續 Spin）；觸發看板不受此限，連續 Spin 會照常關掉並開始 FG。
  - 用共用 API（第 2.7 節）：觸發看板 `await demogameFgBanner.trigger({ spins, icon: "C1", auto: state.auto })`，結算看板 `await demogameFgBanner.end({ win, bet: 底注, format: 金額格式, auto: state.auto })`（自帶 `data-hold-stop`）；遊戲 `await` 之後才開始 FG／回到 BG。樣式由 `demogame_common.css` 提供（外觀同 H032），遊戲不另寫看板樣式。
  - API 產生的結構：在 `#board` 內 append `<div class="fg-banner dg-fg-banner" [data-hold-stop]><div class="fg-banner-card">…</div></div>`，卡片內依序 `.fg-banner-icon`（觸發符號圖，可省略）、`.fg-banner-title`、`.fg-banner-sub`、`.fg-banner-count`；點盤面、按 `#spinBtn`（顯示期間暫時解除 disabled，關閉後還原）或 Auto 1 秒後 resolve 並移除看板；期間 `<html>` 加 `dg-modal-open` 鎖背景捲動。舊遊戲（H026、H032、H039 等）自寫的 `.fg-banner` 不受共用樣式影響，可繼續使用。
- 重置（RNG 區 `#setRngResetBtn`）與模擬區開始／重置（`#batchSimulationStartBtn`／`#batchSimulationResetBtn`）（共用）：跟 SPIN 同款藍色主按鈕（底 #0077cc、白字、高 34px、無外框光暈），disabled 壓暗（底 #102a49、字 #87a7c1）；各遊戲 index.html 不另寫顏色覆寫。
- 模擬（共用）：第一次按「開始」，之後按鈕變「繼續」，每次再跑輸入的局數並接在前面累積（統計與倍率線型都累加）；按「重置」清空回到「開始」；累積依「押注模式＋押注大小」各自保存（見上方模擬條）。
- 飛行動畫目標（共用）：狀態列 `#strip-bar` 已隱藏、改由盤面上方資訊條鏡射倍數膠囊，倍數飛到 Mult／Sum 等動畫一律用 `window.demogameFxTarget("multPill")` 取得畫面上看得到的目標，不要直接量 `#multPill` 的位置（會飛到左上角）。
- 新手導覽（共用）：每台裝置**第一次進遊戲**自動播（localStorage 記看過、所有遊戲共用，2026-11-12），標題列「導覽」可再看；導覽內容有改時把 `GUIDE_REV` 加 1，看過舊版的裝置會再自動播一次。**逐步導覽**（2026-11-12）：一次框一個區域，依序為盤面、SPIN／控制、餘額／押注／得分、押注模式、指標、玩法簡介、倍率線型、除錯模式、**設定（顯示符號 ID、版本、Config、語言，2026-11-20）**；說明框下方有「上一步／n/N／下一步」，最後一步「完成」，Esc 關閉、← → 切換。框線緊貼目標外緣、粗細一致，說明框不壓到目標。手機版（寬度 ≤760px 或觸控裝置）不顯示導覽，也不放「導覽」鈕（2026-11-11）。找不到的區域自動略過，各遊戲不用另外寫；共用 Setting 新增功能時要同步補進導覽步驟。
- 玩法簡介（共用，累積倍率線型上方，標題「玩法簡介」／Game Overview）：寫**競品**（廠商＋遊戲名）、**期待**（一句話說明這款遊戲玩家期待的過程）與**玩法**（本作相對競品的規格變化，沒有競品就寫主要玩法，3～6 點、每點一句；只寫規格上的變化，不寫權重、機率、調性等隱性設計）；詳細規則放標題列「說明」，不寫在這裡。頁面在載入 `demogame_common.js` 前設 `window.DEMOGAME_OVERVIEW = { competitor: "廠商 遊戲名", expect: "…", changes: ["…"] }`，沒設就不顯示。遊戲發想以自家前作為基底時加 `label: "base"`，標籤改顯示「前作」（competitor 填前作名稱與編號）。
- 累積倍率線型（共用，統計區下方，標題「倍率線型 (押注模式)」）：畫面實際遊玩的局，NB 記在 NB、EB 記在 EB，BF／SF 不記錄；依目前押注模式顯示對應的累積圖（標準 64 區間、Y 軸上限 1%），重置清空。右欄小圖：X 軸每 8 個區間標一次、字維持可讀大小，縱軸依 1x 以上區間的最大占比自動縮放（還沒有 1x 以上的局就依全部區間；0x、(0, 1] 超出就裁掉），從第一局就看得到點；按「+」放大才顯示完整 64 區間標籤。遊戲每局（含 FG）結束時呼叫 `window.demogameLineChart.record(總得分 ÷ 押注, "NB"|"EB")`；押注模式按鈕沒有 is-active 樣式時另呼叫 `setMode()`。
- 倍率線型（共用，併入 Simulation 面板）：該次模擬每局 `lineMultiplier` 的標準 64 區間分布，X 軸逐一標出 (下限, 上限]，Y 軸 NB／EB 1%、BF 20%，超過上限或為 0 的區間不畫點、線在該處斷開。沒有 Simulation 面板的頁面才在 Set RNG 上方顯示即時線型（NB 一局含 FG 結束時呼叫 `window.demogameLineChart?.record(該局總得分 ÷ 底注)`；批次模擬不得呼叫）。

Set RNG 的各欄位（卡片區間、遊戲專屬選單、RNG）互斥：設定其中一個時其他回到預設（共用模組處理）。所有設定都每局沿用，按重置才清空，遊戲不得在 Spin、FG、切換模式後自行清掉。指定值要檢查格式；不得因指定 RNG 進入無限重跑。

**Set RNG（共用，`#set-rng-panel`）**：欄位排成一列等寬（卡片 BG 區間、遊戲專屬選單、RNG `#rngInput`、重置 `#setRngResetBtn`）。

**可重現 RNG（共用 `window.demogameRng`）**：每局（BG＋整場 FG）以一組 32-bit 種子算出；Log 印一行 `RNG <Config-Profile>/<NB|EB|BF|SF>/<on|off>/<選項|->/<種子 8 碼>`，點一下複製並填入 RNG 欄，按 Spin 整局重跑出相同結果。遊戲在每局開始呼叫 `demogameRng.takeInput()` 取碼、用 `demogameRng.run(seed, fn)` 一次算完整局結果（表演用亂數放在外面），選項欄放重現所需的遊戲專屬設定（例：腳本名稱、`r<卡片區間>`）。

## 6. 與 Simulator 對帳

至少準備下列可重現案例：無獎 BG、一般得分、Wild／Scatter、Cascade／Multiplier、FG Trigger／Retrigger、各 Bet Mode、Oldhand 小／中／大 Bet、Link 可用／不可用、Card System range／free_game／Retry、Max Win 截斷及遊戲專屬 Feature。

逐項確認盤面、RNG、各段得分、Total Win、Coin In、倍率、Feature 狀態與 Retry 計數一致。

## 7. 交付檢查

Demogame 的「版本紀錄」（`#change-log-wrap`，Debug Mode 開啟時顯示）是專案 `個人筆記/修改紀錄.md` 的複本，只說明各版本的**調性差異**：

- 格式同 [產出與紀錄規範 第 2 節](產出與紀錄規範.md#2-修改紀錄格式)：依四碼版本分節、新到舊，列出全部版本；每個版本一個 `<article class="change-log-entry">`，標題 `<h4>v<第 1 碼>（<四碼版本>）</h4>`，內文 `<ol>` 編號清單，項目與 `修改紀錄.md` 相同（同一版本內由舊到新、句尾附 `（MM/DD）`）。設定區目前選的版本那一節由共用模組標示。
- 每次 `修改紀錄.md` 新增或修改項目，同一次修改中同步更新 `#changeLogBody`。
- 沒有任何調性紀錄時（`修改紀錄.md` 只有標題），`#changeLogBody` 留空，共用模組會把整個版本紀錄區隱藏；不得用「現行版本」「細節無紀錄」之類的佔位項目充數。
- 通則：沒有內容的區域一律不顯示（特殊指標、版本紀錄、空的 Set RNG 容器等由共用模組自動隱藏）。
- 狀態列以共用模組現況為準（2026-11-20 使用者）：`#strip-bar` 由共用模組隱藏，倍數膠囊（`#multPill`／`#sumPill`）鏡射到盤面上方資訊條；遊戲進入 FG 時仍必須在 `body` 加上 `fg-mode`。膠囊由共用模組統一配色，各遊戲不另設：場景標籤（Base Game、Free Game、Buy Feature、Super Feature 等，含特色狀態顯示的場景名稱）用深藍底、淺藍字膠囊；其他資訊（連消、倍數、FG 剩餘、Table 等）一律用黃色膠囊（淡黃底、黃字 12px）；膠囊都不加外框。
- Demogame 介面、演出、Debug、共用模組與文件的修改**不記在頁面上**（以 git commit 訊息為準），也不寫進 `修改紀錄.md`。

- [ ] 離線開啟無錯誤，Console 無未處理例外。
- [ ] 第 2.4 節骨架的固定 id 都在（沒有的模式按鈕除外）、`demogame_common.js` 在 `</body>` 前最後載入，第 2.6 節標「必要」的全域宣告與 DOM 狀態都已提供。
- [ ] 「版本紀錄」（`#changeLogBody`）與 `修改紀錄.md` 內容一致（依版本分節、新到舊、只記調性）。
- [ ] `demogame_common.css` 與 `demogame_common.js` 由 `../` 相對路徑載入，且共用功能未複製進遊戲專屬程式。
- [ ] 圖示範圍內的標題、Feature Status、盤面、動畫與 Message 屬 By Game；其餘 UI 使用共用資源。
- [ ] By Game CSS／JavaScript 未覆寫或複製共用區域的版面與控制邏輯。
- [ ] 符號顯示符合 2.3：有圖＝只顯示圖（無代號、無符號框），無圖＝符號框＋代號；代號不粗體；有美術的遊戲已接共用圖片介面，沒美術的遊戲預設用 icon；Setting 的「顯示符號 ID」開啟後每格正中間顯示正確代號。
- [ ] 有符號美術時：`DEMOGAME_IMAGE_TOGGLE.images` 列出全部圖片（含大符號、金框等變體），以本機伺服器開啟確認 `window.__demogameImageCache` 張數等於清單、全部 `naturalWidth > 0`、載入遮罩已消失；Demo 引用的圖片皆為 `.webp`，無 `.png` 引用。
- [ ] 補牌方式已選定為原地、掉落或特殊補牌，並與 Game Rule、Config、Simulator 一致。
- [ ] 原地補牌不移動保留符號；掉落補牌正確區分 Settle 與新符號 Drop。
- [ ] Config 切換後所有資料與顯示同步更新。
- [ ] 所有支援的 Bet Mode 均可完成完整流程。
- [ ] Card System Off／On、Oldhand 小／中／大 Bet 與 Link 資格行為正確（Demogame 一律老手期，不提供 Newbie）。
- [ ] Debug 資訊足以重現並與 Simulator 對帳。
- [ ] Demo 統計口徑與模擬報表一致。
- [ ] 不存在寫死的舊遊戲名稱、倍率、Table、輪帶或 Help。
- [ ] 下一次 Spin 動畫第一格仍是前一個盤面（舊盤先捲走／掉出，新盤才進來），沒有先變牌再滾。
- [ ] 有 FG 的遊戲：觸發看板（免費遊戲 N 場）與結算看板（免費遊戲結束／總贏分）都會出現，Auto 1 秒自動關、非 Auto 可點掉；觸發符號圖沒有撐滿盤面。
- [ ] 購買類按鈕都是藍色，買進後壓暗（兩顆購買按鈕壓暗後樣子相同）、FG 結束恢復；沒有綠色或各遊戲自訂顏色。
- [ ] 長按 SPIN 連續轉到 FG 結束：結算看板留在畫面上、連續 Spin 停止，重新按才繼續。
- [ ] 畫面與 Help 全為繁體中文，無簡體字（前作沿用的「簡中」內容已轉繁體、欄名改「繁中」；規則見 [產出與紀錄規範 第 1 節](產出與紀錄規範.md#1-必要產出文件)）。

## 8. Demo 版 RTP 120%

Demo 網頁（展示、試玩）用的卡片權重，RTP 120%。規則依[數學模型規範 §1.5.3](Omniplay/數學模型規範.md#153-demo-版-rtp120)，本節是操作方式。

- **來源**：只用**老手中 Bet**（92A）一套衍生；**不分大小 Bet、新老手、A／B 版**，新手直接複製老手（含倍數上限）。
- **NB／EB**：差額 `120% − 92%` 一半加在 BG `(25, 30]`、一半提高 FG 觸發卡權重（縮短 FG 週期），兩者都從 `(-1, 0]` 扣；FG 倍率區間不動。觸發把本身的 BG 得分會一起變多，要先從 BG 補足量扣掉。EB 以 NB 基準成本換算（EB 2x 時補足量 ×2）。
- **BF／SF**：平均倍數拉到 `購買價 × 120%`；購買價以上（贏錢）的區間等比例升、以下（賠錢）的區間等比例降，各段形狀不變。
- **不跑模擬驗證**：以卡片權重精算即可。
- **SCR 不跑模擬**：`OP Jackpot` 工作表的 SCR 直接複製 92A 工作簿（含來源註記）；92A 的 SCR 更新時同步改。
- **不升版號、不記修改紀錄**：屬 Demo 用參數，不是數學調性。
- **檔案**：出工作簿與 config，不做 PARsheet、報表。
  - 工作簿 `Source/<MathID>1120_Demo.xlsx`（例 `H0451120_Demo.xlsx`）：複製 92A 工作簿改 Multiplier_Weight，新手欄＝老手欄（含 Avg_Multi、Nature_Prob），Overview 型號改同檔名、Pay Back 區塊重算；區間平均用 Avg_Multi 精算。存檔後跑 `_check_xlsx_style.py`。
  - `config_120A_Demo.js` 由工作簿轉出，放遊戲根目錄；`config_code`／`rtp_label` 為 `120A_Demo`，並加 `demo_only` 註記。
  - 兩者都複製一份到 `Versions/<目前版本>/`（工作簿放 `Source/`），並加進 `Versions/version_manifest.js／.json` 目前版本的 `sources`／`configs`，Demo 選單顯示「120A Demo（RTP 120%）」；改 manifest 後要升 `index.html` 的 `?v=` 尾碼。
  - 不交 SPS、不進送驗文件。
- 例：H045 v6.0.0.3 — NB FG 週期 150 → 96.2 轉、EB 30 → 24.5 轉；BF 平均 46.25x → 60x、贏錢率 30% → 48.9%。

## 9. 彩金（OP Jackpot）

有彩金的遊戲，Demo 的實際遊玩與批次模擬都要包含彩金（2026-11-17 起，H032 首例）：

- **參數**：一律讀目前層級的 `jackpot` 區塊（由 OP Jackpot 數學模型與遊戲工作簿的 SCR 轉出，見《[數學模型規範](Omniplay/數學模型規範.md)》§1.6.3），Demo 內不寫死 RTP、Increment、起始金額、固定倍數、SCR 或籤箱；選 Base（沒有 RTP config）時彩金列隱藏、不判定彩金。
- **判定時機**：與 Simulator 相同（《[模擬程式規範](模擬程式規範.md)》§1.2.4）——每一轉出現觸發符號（BG／購買進場盤、FG 每一轉）各判一次；FG 中途中彩金也立刻進選彩金小遊戲。
- **實際遊玩（含 Auto）**：每局押注累進 GRAND／MAJOR；中獎走選彩金小遊戲，獎金計入餘額、得分與畫面 RTP；檔位與 Link 資格同 Simulator。
- **批次模擬（Simulation 面板）**：同一套判定，但用獨立彩池，不改畫面上的彩池；`demogameSimulateRound` 回傳的倍數要含彩金。
- **選彩金小遊戲**：照 config 的籤箱（`pick_lots`），依中獎彩金隨機挑一種組合、整箱洗牌後依序翻開，中獎彩金翻到第 3 張即結束，箱內剩下的籤在結束時揭露；不得用固定順序讓中獎彩金總在最後一張出現。
