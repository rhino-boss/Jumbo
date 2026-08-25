# Slot 開發注意事項

本文件整理 Slot Game 數學模型從設計、實作、驗證到交付時必須注意的事項。重點是確保數學文件、Card System、模擬程式、Demogame 與 Config 使用同一套規則與參數，避免各端各自解讀或寫死例外。

適用範圍：`Project/Slots/H0xx_遊戲名稱/` 下的新遊戲模型、既有模型改版，以及 RTP、Card System 或 Feature 參數調整。

## 目錄

- [共通原則](#共通原則)
- [數學文件](#數學文件)
  - [數學模型](#數學模型)
  - [PAR Sheet](#par-sheet)
  - [Game Rule](#game-rule)
- [程式相關](#程式相關)
  - [模擬程式](#模擬程式)
  - [Demogame](#demogame)
  - [Config](#config)
- [其他文件](#其他文件)
  - [Help](#help)
  - [Game Description](#game-description)
  - [Game List](#game-list)
- [附錄](#附錄)
  - [Card System](#card-system)

## 共通原則

```text
數學文件／XLSX
      ↓ 轉檔與驗證
    Config
     ├─→ 模擬程式 → Record 報表
     └─→ Demogame  → 操作與逐局對帳
```

- 數學文件與 `Source/*.xlsx` 是規格來源，Config 是程式執行時的共同參數來源。
- 模擬程式與 Demogame 必須讀取同一份 Config，不得各自維護另一套輪帶、權重、Paytable 或 Feature 參數。
- `game_rule.md` 必須說明玩法、判獎順序、倍率口徑、Feature 流程與例外；程式不可補猜未定義的規則。
- Game Rule 是遊戲規則的正式說明來源；數學模型、程式與 Help 必須與其一致。
- Help 必須依 Game Rule 編寫，並同時維護 `Help.xlsx` 與對應的 Markdown 文件；兩者內容不得不一致。
- 同一項資料若在多個檔案出現，修改時必須同步更新並完成對帳。
- 未支援的 RTP、Variant、Bet Mode、Profile 或 Feature，不得出現在 Config、Simulator 批次或 Demogame 選單。
- 會影響結果分布、RTP、觸發率、最大獎或 Retry 的修改，都必須更新版本並重新模擬。

---

## 數學文件

### 數學模型

數學模型是包含公式、計算過程、輪帶、權重、參數與驗證依據的完整文件，也是產出 PAR Sheet 與 Config 的數學來源。

#### 1.1 必要內容

模型開始實作前，數學文件至少要定義：

- Game ID、遊戲名稱、盤面尺寸與 Lines／Ways／Cluster 等得分方式。
- Symbol、Paytable、Wild／Scatter 規則與判獎順序。
- BG、FG、Cascade、Multiplier、Retrigger、Jackpot 等流程。
- Normal Bet、Extra Bet、Buy Feature、Super Feature 的成本與差異。
- 各 RTP 家族、Variant、Player Profile 與押注層級的 Link／Bonus Game／Game RTP 拆分及 Total RTP。
- Oldhand 必須依小 Bet／中 Bet／大 Bet 分別定義倍率權重。
- Feature Trigger Rate、Hit Rate、Max Win／Max Multiplier 與上限。
- Card System 的區間、權重、倍率分母、Retry 與失敗處理。
- 同局同時符合多項條件時的處理優先順序。

計算口徑必須明確區分：

```text
RTP = Total Win ÷ 實際 Total Bet
卡片判定倍率 = 指定結果得分 ÷ card_system_coin_in
Max Multiplier = Round Total Win ÷ 該模式定義的基準成本
```

#### 1.2 模型命名

| 項目 | 格式 | 範例 |
|---|---|---|
| 遊戲 ID | `H<三位數字>` | `H028` |
| 基礎數學 XLSX | `H<遊戲編號>1.xlsx` | `H0161.xlsx` |
| RTP／Variant 數學 XLSX | `H<遊戲編號>1<RTP><Variant>.xlsx` | `H016192A.xlsx` |

- `92`／`94` 表示 RTP 家族。
- `A`／`B` 表示同一 RTP 家族下的數學 Variant，不代表 Newbie／Oldhand。
- 沒有 B 版時只建立 A 版，不得建立內容相同的空白 B 版。

##### 1.2.1 數學模型工作表命名與規則

數學模型 XLSX 的共用工作表使用下列名稱與用途：

| 工作表名稱 | 用途與規則 |
|---|---|
| `Overview` | 遊戲的基礎設定。 |
| `Gaem Description` | 說明遊戲模型參數的使用方法。工作表名稱固定使用此拼法，不得自行改為其他名稱。 |
| `Parameter` | 遊戲參數。 |
| `BG_Symbol` | Base Game 使用的第一張輪帶表。 |
| `BG_Symbol (2)` | Base Game 使用的第二張輪帶表；只有一張 BG 輪帶表時不得建立。 |
| `BG_Symbol (3)` | Base Game 使用的第三張輪帶表；只有一或兩張 BG 輪帶表時不得建立。 |
| `BF_Symbol` | Buy Feature 入口使用的觸發輪帶，只能用來觸發 FG；該入口盤面不得產生任何 BG 得分。 |

- BG 有多張輪帶表時，第一張固定命名為 `BG_Symbol`，第二張起依序在名稱後加上空格與括號編號，例如 `BG_Symbol (2)`、`BG_Symbol (3)`；不得使用 `BG_Symbol2`、`BG_Symbol_2` 或其他格式。
- `BF_Symbol` 必須與一般 BG 輪帶分開定義。其符號配置與停輪結果必須確保 Buy Feature 入口可觸發 FG，且觸發盤面不成立任何 Line／Ways／Cluster／Pay Anywhere 或其他 BG 派彩。
- 若遊戲沒有 Buy Feature，則不得建立空白或未使用的 `BF_Symbol` 工作表。
- 新增其他用途的輪帶工作表時，必須在 `Gaem Description` 說明選表條件、使用模式與限制，並同步更新 XLSX 轉 Config mapping。

#### 1.3 版本規則

基礎數學文件與 RTP／Variant 數學文件使用不同的版本格式：

| 文件 | 版本格式 | 範例 |
|---|---|---|
| `H<遊戲編號>1.xlsx` | 1 碼數字版本 | 競品模型初始為 `0`；非競品模型初始為 `1` |
| `H<遊戲編號>1<RTP><Variant>.xlsx` | 4 碼數字版本 | `H016192A.xlsx`：`1.0.0.0` |

RTP／Variant 數學文件的四碼版本格式為：

```text
遊戲參數.卡片權重.SCR.其他文件
```

例如：`H016192A.xlsx` 的版本為 `1.0.0.0` 時，第 1 碼 `1` 必須與 `H0161.xlsx` 的版本 `1` 相同。

| 段位 | 變更時機 |
|---|---|
| 第 1 碼：基礎數學版本 | 必須對應 `H<遊戲編號>1.xlsx` 的 1 碼版本；基礎輪帶、Paytable、Feature、Bet Mode、判獎等內容變更時更新。 |
| 第 2 碼：卡片權重 | Newbie／Oldhand、BG／FG／Buy／Super Feature 的卡片區間或權重。 |
| 第 3 碼：SCR | SCR 設定、內容或結果。 |
| 第 4 碼：其他文件 | 不影響前三類的規則、Help、說明或排版。 |

- `H<遊戲編號>1.xlsx` 的版本只能填 1 碼，不得填成四碼。
- 以競品遊戲資料、競品 Response、競品輪帶或競品數學模型為主要初始來源的模型，基礎數學初始版本固定為 `0`。
- 非競品衍生、由公司自行設計或沒有以競品模型作為主要初始來源的模型，基礎數學初始版本固定為 `1`。
- 是否屬於競品模型必須記錄於數學文件、Config mapping 或其他可追溯文件，不得只依檔名或人員記憶判斷。
- 初始版本確立後，後續正式異動依本節規則遞增；不得因為參考來源分類改變而把既有正式版本重設為 `0` 或 `1`。
- 所有 `H<遊戲編號>1<RTP><Variant>.xlsx` 的第 1 碼，都必須與同一遊戲的 `H<遊戲編號>1.xlsx` 版本相同。
- 基礎數學版本遞增時，所有受影響的 RTP／Variant 文件同步更新第 1 碼，並將第 2～4 碼歸零。
- 第 2 碼遞增後，第 3～4 碼歸零；第 3 碼遞增後，第 4 碼歸零。
- 同一次修改涉及多種類型時，只遞增順位最高的一碼，並將後續碼歸零。
- 依實際異動內容判斷版本，不得只依檔名判斷。
- `config.js` 的 `excel_version` 必須與基礎數學 XLSX 的 1 碼版本完全一致。
- `config_<RTP><Variant>.js` 的 `excel_version` 必須與對應 RTP／Variant XLSX 的 4 碼版本完全一致。
- 92／94 或 A／B 中所有受影響的模型都要更新，不得只改其中一份。
- 已封存版本不得覆寫；需要修正時建立新版本。

##### 1.3.1 XLSX 異動與版本同步

只要 XLSX 的正式內容有更新，就必須在同一次修改中更新對應版本；不得先改內容、之後才補版本。

| 異動內容 | 必須更新的版本 |
|---|---|
| 基礎數學 XLSX，例如 `H0161.xlsx` | 遞增該檔案的 1 碼版本；所有引用此次基礎異動的 RTP／Variant XLSX 同步更新第 1 碼，並將第 2～4 碼歸零。 |
| RTP／Variant 的遊戲參數需要更新第 1 碼 | 先遞增基礎數學 XLSX 的 1 碼版本，再同步更新所有受影響 RTP／Variant XLSX 的第 1 碼，並將第 2～4 碼歸零。 |
| Card System 區間或權重 | 更新實際異動之 RTP／Variant XLSX 的第 2 碼。 |
| SCR | 更新實際異動之 RTP／Variant XLSX 的第 3 碼。 |
| 只影響文件、說明或排版 | 更新實際異動之 RTP／Variant XLSX 的第 4 碼。 |

- 修改哪一份 XLSX，就更新哪一份 XLSX 的版本；未受影響的 XLSX 不得為了統一數字而無條件升版。
- 同一項異動同時影響 92／94 或 A／B 時，每一份受影響的 XLSX 都要依相同規則更新。
- 同一次異動涉及多個版本段位時，依順位最高的段位遞增，後續段位依第 1.3 節規則歸零。
- XLSX 版本更新後，必須重新產生其對應 Config，並同步更新 Config 的 `excel_version`。
- Simulator 與 Demogame 必須載入更新後的 Config；新產生的報表必須使用更新後的版本，不得沿用舊版號。

#### 1.4 RTP 與 Bet Mode

RTP 配置使用 `Link + Bonus Game + Game = Total RTP`。NB／EB 與 BF／SF 必須分開設定。

##### 1.4.1 NB／EB RTP 配置

| Player Profile | 押注層級 | 押注層級判定金額 | Link RTP | Bonus Game RTP | Game RTP | Total RTP | Config 家族 |
|---|---|---:|---:|---:|---:|---:|---|
| Newbie | 不分層級 | 全部 | 0.00% | 2.00% | 93.00% | 95.00% | Newbie 共用 |
| Oldhand | 小 Bet | `< $2` | 0.00% | 2.00% | 94.00% | 96.00% | `94x` |
| Oldhand | 中 Bet | `>= $2` 且 `<= $100` | 2.00% | 2.00% | 92.00% | 96.00% | `92x` |
| Oldhand | 大 Bet | `> $100` | 2.00% | 2.00% | 92.00% | 96.00% | `92x` |

- `$2` 屬於中 Bet；`$100` 屬於中 Bet；只有大於 `$100` 才屬於大 Bet。
- `92`／`94` 表示 Game RTP 配置家族，不等於加總 Link 與 Bonus Game 後的 Total RTP。
- `x` 代表 A、B 等 Variant；Variant 不改變 Profile 或押注層級定義。
- 每個遊戲的數學文件必須定義哪些派彩歸入 Link、Bonus Game、Game，三者不可重複計算。
- 產品顯示值可以四捨五入，模型計算與驗證必須使用完整精度。
- 各 Bet Mode 的 RTP 分母使用玩家在該模式的實際成本。
- Scatter Pay、購買進場盤、FG、Retrigger、Jackpot 是否計入 Total Win，必須與遊戲規則及 XLSX 公式一致。
- Card System Off／On、Newbie、Oldhand 小／中／大 Bet 及所有支援的 Bet Mode 必須分開驗證。

##### 1.4.2 BF／SF RTP 配置

| Player Profile | 押注層級 | 押注層級判定金額 | Link RTP | Bonus Game RTP | Game RTP | Total RTP |
|---|---|---:|---:|---:|---:|---:|
| Newbie | 不分層級 | 全部 | 0.00% | 4.00% | 92.50% | 96.50% |
| Oldhand | 小 Bet | `< $2` | 0.00% | 4.00% | 92.50% | 96.50% |
| Oldhand | 中 Bet | `>= $2` 且 `<= $100` | 2.00% | 2.00% | 92.50% | 96.50% |
| Oldhand | 大 Bet | `> $100` | 2.00% | 2.00% | 92.50% | 96.50% |

- BF／SF 的 92.50% 是 Game RTP 分項，不是 Total RTP；Total RTP 固定為 96.50%。
- Newbie 與 Oldhand 小 Bet 使用相同 RTP 拆分，但仍是不同 Player Profile，必須保留各自權重及模擬結果。
- Oldhand 中 Bet 與大 Bet 的 RTP 拆分相同，但倍率上限與倍率權重仍分開設定。

##### 1.4.3 押注模式分類與層級判定

押注模式分成兩大類，先計算 `bet_tier_amount`，再依 `< $2`、`>= $2 且 <= $100`、`> $100` 判斷 Oldhand 的小／中／大 Bet：

| 模式類別 | Bet Mode | `bet_tier_amount` 判定基準 | 計算方式 |
|---|---|---|---|
| 一般押注類 | Normal Bet／Extra Bet（NB／EB） | 該模式實際押注金額 | `base_bet × mode_cost_multiplier` |
| Feature Buy 類 | Buy Feature／Super Feature（BF／SF） | Feature 的基礎押注 | `feature_purchase_amount ÷ feature_price_multiplier` |

- NB／EB 使用實際扣款的模式押注金額判斷，不使用未乘 Mode 倍數的原始 base bet。
- BF／SF 使用購買價格反推的基礎押注判斷，不直接用 Feature 購買總價判斷。
- H026 EB 為 2x：基礎押注 `$1` 時，實際押注為 `$2`，所以屬於中 Bet 並可拉 Link。
- H026 BF 為 75x：購買 `$75` 時，基礎押注為 `$1`，所以屬於小 Bet 且不可拉 Link；購買 `$150` 時，基礎押注為 `$2`，所以屬於中 Bet 並可拉 Link。
- `bet_tier_amount` 必須由 Config 的模式成本／Feature 價格倍率計算，不得在 Runtime 寫死 2x、75x 或其他個別遊戲數值。

##### 1.4.4 玩家階段與倍率上限

| Player Profile | 押注層級 | BG Max Multiplier | FG Max Multiplier |
|---|---|---:|---:|
| Newbie | 不分層級 | `30x` | `120x` |
| Oldhand | 小 Bet | 依遊戲規格 | `20000x` |
| Oldhand | 中 Bet | 依遊戲規格 | `20000x` |
| Oldhand | 大 Bet | 依遊戲規格 | `2000x` |

- 上表為所有遊戲的預設硬上限；個別遊戲若產品上限更低，使用較低值並在數學文件明記。
- Max Multiplier 的分母依第 1.1 節定義；等於上限時可接受，超過上限時依遊戲的 Max Win 流程截斷或重跑，且 XLSX、Config、Simulator 與 Demogame 必須一致。
- Oldhand 小／中／大 Bet 必須使用三套獨立倍率權重，不得在 Runtime 對另一套權重臨時縮放、截斷或 fallback。
- 此分層適用於所有支援的 NB／EB／BF／SF；Oldhand 的每個模式都必須依第 1.4.3 節選擇小／中／大 Bet 權重。

#### 1.5 卡片倍率區間

數學文件使用下列卡片倍率區間：

```text
(-1, 0]
(0, 1]
(1, 2]
(2, 3]
(3, 4]
(4, 5]
(5, 6]
(6, 7]
(7, 8]
(8, 9]
(9, 10]
(10, 15]
(15, 20]
(20, 25]
(25, 30]
(30, 35]
(35, 40]
(40, 45]
(45, 50]
(50, 60]
(60, 70]
(70, 80]
(80, 90]
(90, 100]
(100, 120]
(120, 140]
(140, 160]
(160, 180]
(180, 200]
(200, 250]
(250, 300]
(300, 350]
(350, 400]
(400, 450]
(450, 500]
(500, 550]
(550, 600]
(600, 650]
(650, 700]
(700, 750]
(750, 800]
(800, 850]
(850, 900]
(900, 950]
(950, 1000]
(1000, 2000]
(2000, 3000]
(3000, 4000]
(4000, 5000]
(5000, 6000]
(6000, 7000]
(7000, 8000]
(8000, 9000]
(9000, 10000]
(10000, 20000]
(20000, 30000]
(30000, 40000]
(40000, 50000]
(50000, 60000]
(60000, 70000]
(70000, 80000]
(80000, 90000]
(90000, 100000]
(100000, 9999999]
```

#### 1.6 開發前檢查

- [ ] 遊戲規則沒有待確認的判獎順序或倍率口徑。
- [ ] 每個支援的 Config、Bet Mode 與 Profile 都有明確目標。
- [ ] 基礎數學 XLSX 為 1 碼版本，且所有 RTP／Variant XLSX 的第 1 碼均與其一致。
- [ ] 新模型已記錄競品／非競品來源；競品初始版本為 `0`，非競品初始版本為 `1`。
- [ ] XLSX 公式、命名、版本與工作頁用途可追溯。
- [ ] 共用工作表名稱符合第 1.2.1 節；多張 BG 輪帶依序使用 `BG_Symbol`、`BG_Symbol (2)`、`BG_Symbol (3)`。
- [ ] `BF_Symbol` 只用於 Buy Feature 觸發 FG，且所有入口盤面均不產生 BG 得分。
- [ ] 最大獎與理論上限已計算，且未超出產品限制。
- [ ] 所有 Feature 的 Trigger、Retrigger、結束條件與上限已定義。
- [ ] Card System 是否啟用、使用哪些卡片及如何 Retry 已定義。

---

### PAR Sheet

PAR Sheet 是提供企劃、程式、測試、美術、營運或其他職能查閱的精簡規格文件，不是完整數學模型的副本。

- PAR Sheet 必須移除數學模型中的計算公式、中間推導、內部權重計算與不需要對外提供的工作資料。
- 只保留其他職能完成工作所需的必要資訊，例如遊戲基礎設定、盤面、得分方式、Paytable、Symbol、Bet Mode、Feature 條件、局數、倍率、Max Win、Jackpot 與產品限制。
- 所有輸出數值與規則必須和完整數學模型、Game Rule 及 Config 一致，不得為了簡化而改變定義或精度口徑。
- 完整数學模型更新時，必須同步確認 PAR Sheet 是否需要更新；PAR Sheet 不得保留已失效的規格。

### Game Rule

Game Rule 是遊戲規則說明文件。

#### 用途

Game Rule 用於設定遊戲玩法規則，是數學模型、Config、Simulator、Demogame、Help 與測試案例共同遵循的規則來源。

#### 必要規則

- 每款遊戲必須提供 `game_rule.md`，並明確定義遊戲基礎設定、得分方式、Symbol 功能、判獎順序、Bet Mode、BG／FG 流程、Feature、Retrigger、Multiplier、Max Win、Jackpot 與例外處理。
- Game Rule 必須沿用本節定義的固定章節骨架、標題層級、表格形式及規則表達方式。
- 數學模型、Config、Simulator、Demogame 與 Help 不得自行補充或改寫 `game_rule.md` 未定義的玩法。
- 規則變更時，必須同步檢查並更新數學文件、Config、Simulator、Demogame、`Help.xlsx`、`game_help_draft.md` 與測試案例。
- Game Rule 與其他來源內容衝突時，必須先確認正式規則，不得由開發端自行選擇其中一種實作。

Game Rule 必須保留下列基本結構：

| 順序 | 章節 | 格式要求 |
|---:|---|---|
| 1 | `§1. 遊戲基本資訊` | 使用「項目／說明」表格記錄本節規定的基礎資料。 |
| 2 | `§2. 盤面結構` | 包含盤面示意圖與 Reel／Row、得分方向及補牌流程的文字說明。 |
| 3 | `§3. 符號類別` | 分開定義一般符號與特殊符號，說明出現位置、替代關係及功能。 |
| 4 | `§4. 賠率表（Pay Table）` | 使用表格列出符號、得分數量及倍率口徑。 |
| 5 | `§5. 核心特色` | 依遊戲機制建立子章節，完整說明特色符號、轉換、Multiplier 或其他核心玩法。 |
| 6 | `§6. 免費遊戲（Free Spins / Free Game, FG）` | 分別定義觸發、FG 玩法及 Retrigger。 |
| 7 | `§7. 核心遊戲流程（Base Game）` | 依實際執行順序編號描述 Spin、判獎、消除／補牌、結算與 Feature Trigger。 |
| 8 | `§8. 押注模式` | 依遊戲實際支援內容分別說明 Extra Bet 與 Buy Feature。 |
| 9 | `§9. 邊界 / 例外情境（Edge Cases）` | 依機制分類列出可直接驗證的邊界條件及例外處理。 |

`§1. 遊戲基本資訊` 必須包含下列欄位：

- `Game ID`
- `PARsheet ID`
- `遊戲中文名稱`
- `遊戲英文名`
- `遊戲類型`：依實際遊戲機制列出完整類型，例如 `2,025–32,400 Ways / Megaways / Cascade`。
- `盤面規格`
- `中獎方式`：使用 `Line Game`、`Way Game`、`Pay Anywhere` 或 `Cluster Pay`；只能選擇符合實際判獎邏輯的類型。
- `押注模式`

`§8. 押注模式` 依遊戲實際支援內容包含：

- `Extra Bet`：遊戲有 Extra Bet 時，說明價格、流程與 Normal Bet 的差異；沒有時可省略此子章節。
- `Buy Feature（購買特色）`：遊戲有 Buy Feature 時，說明購買價格、入口 Spin、FG 觸發方式與得分計算；沒有時可省略此子章節。

- §1～§9 的章節名稱與順序不得任意更動；遊戲沒有 FG 時，仍須保留 §6 並明確寫「不適用」或「不提供」。
- 可依各遊戲機制在固定章節下新增子章節，但不得改變核心章節順序。
- 規則必須以開發與測試可直接實作、驗證的方式描述，不得只使用宣傳文案或未定義的概念性敘述。

#### 交付檢查

- [ ] `game_rule.md` 已涵蓋所有實際支援的玩法、模式與 Feature。
- [ ] Game Rule 已依本節規定的 §1～§9 基本格式建立，固定章節、順序與表格形式完整。
- [ ] §1 已包含 Game ID、PARsheet ID、中英文名稱、遊戲類型、盤面規格、中獎方式與押注模式。
- [ ] §8 已依實際支援內容完整說明 Extra Bet 與 Buy Feature。
- [ ] 判獎順序、倍率分母、觸發條件、結束條件與上限均可直接實作及測試。
- [ ] Game Rule 與數學模型、Config、Simulator、Demogame 及 Help 的規則一致。

---

## 程式相關

### 模擬程式

`Simulator.py` 是數學模型的主要驗證工具。數學邏輯、批次設定、Console 輸出與 Excel 報表必須使用相同的統計口徑。

#### 3.1 程式架構

##### 3.1.1 加速：Numba、多執行緒

- 高頻數學核心使用 Numba 編譯；適用的核心函式使用 `@njit(nogil=True)`。
- 使用多執行緒平行執行模擬，例如 `ThreadPoolExecutor`；每個 Worker 必須持有獨立的 RNG 狀態。
- 正式計時前先執行 Warm-up，Numba 首次編譯時間不得計入 `duration`。
- Numba Core 只處理數值及固定型別 Array／Tuple；Config 解析、字串、DataFrame 與 Excel 留在 Python 層。
- 預先配置統計陣列與暫存 Buffer，模擬迴圈內不得反覆建立大型物件。
- 場次平均分配給各 Worker，餘數由前幾個 Worker 各多執行一場；合併後必須等於 `total_rounds`。
- Worker 回傳相同 shape／dtype；Count 與 Pay 欄位相加，Max 欄位取最大值。
- 固定 RNG、逐局 Trace 與 Debug 重現模式使用單執行緒。

##### 3.1.2 程式邏輯

程式依下列順序執行：

1. 讀取 `BATCH_RUNS` 的本批參數。
2. 載入 `config_file` 的自然機率參數。
3. 載入 `config_rtp_file` 的倍率權重參數。
4. 驗證兩份 Config 的 `game_id`、版本與資料相容性。
5. 將 Config 正規化為模擬核心使用的固定型別資料。
6. 依 `bet_mode`、Card System 開關、Profile 與基礎押注額建立本批設定，並選出押注層級、Link 資格及倍率上限。
7. 執行 Warm-up，再開始正式計時與多執行緒模擬。
8. 合併 Worker 統計，計算 RTP、Hit Rate、Feature、Retry 與遊戲專屬指標。
9. 依固定格式印出執行結果。
10. 需要輸出時，將相同結果寫入 `Record/*.xlsx`。

數學核心與報表／顯示邏輯必須分離。Card System 關閉時，不得執行抽卡或 Retry；`config_rtp_file` 不得改變 `config_file` 所定義的原始盤面與自然機率邏輯。

##### 3.1.3 執行結束後印出的內容

每個 Batch 結束後必須依第 3.3 節的順序與格式輸出，不得只印 RTP。欄位名稱固定使用英文，數值格式由共用格式化函式處理。

##### 3.1.4 輸出報表

- 報表固定輸出至該遊戲的 `Record/`，格式為 `.xlsx`。
- 報表與 Console 必須來自同一份統計結果，不得重新計算成不同口徑。
- 報表檔名固定沿用 H026 的命名順序，不得由個別遊戲任意調換欄位。

報表檔名格式：

```text
Card System Off：
<base_game_id>_<base_version_tag>_<timestamp>_betmode<bet_mode>_<rounds_tag>.xlsx

Card System On（Newbie／Oldhand）：
<rtp_game_id>_<rtp_version_tag>_<timestamp>_betmode<bet_mode>_<rounds_tag>_<rtp_tag>_<profile>[_<bet_tier>]_card.xlsx
```

各段規則：

| 段落 | 規則 | 範例 |
|---|---|---|
| `base_game_id` | Card System Off 時，使用基礎 Config／基礎 XLSX 的完整 Game ID。 | `H0161` |
| `base_version_tag` | Card System Off 時，使用基礎數學的 1 碼版本並補滿 2 位數。 | `2` → `02` |
| `rtp_game_id` | Card System On 時，使用 RTP／Variant Config 內的完整 Game ID。 | `H016192A` |
| `rtp_version_tag` | Card System On 時，四段版本各補滿 2 位數，再移除分隔點後依序串接。 | `2.1.3.13` → `02010313` |
| `timestamp` | 報表產生時間，格式為 `YYMMDDHHmm`。 | `2608141530` |
| `bet_mode` | 使用整數 Bet Mode。 | `0` |
| `rounds_tag` | `10^N` 場寫成 `10N`；非 10 的整次方則使用完整場次。 | `10^8` → `108` |
| `rtp_tag` | Card System On 時，取實際 RTP 小數點後 4 位，不含小數點與 `%`。 | `92.01%` → `9201` |
| `profile` | Card System On 時使用 `newbie` 或 `oldhand`；NB／EB／BF／SF 均不得省略。 | `oldhand` |
| `bet_tier` | Oldhand 使用 `small_bet`、`medium_bet` 或 `big_bet`；Newbie 省略。 | `medium_bet` |
| `card` | Card System On 時固定加在檔名最後。 | `card` |

範例：

```text
Card System Off：
H0161_02_2608141342_betmode0_105.xlsx

Card System On（Oldhand 中 Bet）：
H016192A_02000000_2608141341_betmode0_105_9600_oldhand_medium_bet_card.xlsx

Card System On（Feature Buy，Oldhand 小 Bet）：
H026194A_02010313_2608141530_betmode2_108_9650_oldhand_small_bet_card.xlsx
```

- Card System Off 的檔名只能使用 `config_file` 所對應的基礎 `game_id` 與 1 碼版本，不得使用 `config_rtp_file` 的 RTP／Variant Game ID 或四段版本。
- Card System On 的檔名使用 `config_rtp_file` 所對應的 RTP／Variant `game_id` 與四段版本。
- `base_version_tag` 固定為 2 位數；例如基礎版本 `2` 輸出為 `02`。
- `rtp_version_tag` 每一段都必須補滿 2 位數，不是只移除 `.`；`2.1.3.13` 必須轉成 `02010313`，不得輸出成 `21313`。
- 四段中的單段若超過 2 位數，視為版本格式錯誤，停止輸出報表並提示修正版本。
- 檔名不得包含空白、冒號、百分比符號或版本分隔點。

`Overview` 工作頁：

- 內容、欄位順序、欄位名稱、數值與格式必須和第 3.3 節的 Console 輸出一致，不得重新排序。
- 不寫入 Batch 標題，例如 `=== Batch 1/1: {...} ===`。
- 不寫入 `<< By Game Info >>` 標題；Game Info 欄位依 Console 的既定順序接在共用輸出的最後一個欄位之後。Card System On 時接在 `retry_limit_fg` 後，Off 時接在 `standard_error` 後。
- Card System 開啟時才顯示 `card_system_profile` 至 `retry_limit_fg`；關閉時整段不顯示，與 Console 規則一致。
- `Overview` 與 Console 必須使用同一份已計算結果，不得分別計算或套用不同格式。

`Multiplier Line` 工作頁：

- 每一列對應報表定義的一個倍率區間，欄位名稱必須維持下列英文格式。
- 共用欄位依下列順序輸出：

```text
base_game_cnt
base_game_pay
free_game_cnt
free_game_pay
free_game_cnt_BF
free_game_pay_BF
free_game_cnt_SF
free_game_pay_SF

Interval_Upper
bg_trigger_fg_cnt_lte_upper
bg_trigger_fg_pay_lte_upper

FG_Hit_Rate
FG_Spin_Count

BG_Combo_1_Rate
BG_Combo_2_Rate
BG_Combo_3_Rate
BG_Combo_4_Rate
BG_Combo_5+_Rate

FG_Combo_1_Rate
FG_Combo_2_Rate
FG_Combo_3_Rate
FG_Combo_4_Rate
FG_Combo_5+_Rate
```

- `free_game_cnt_BF`、`free_game_pay_BF` 只在遊戲有 Buy Feature 時顯示。
- `free_game_cnt_SF`、`free_game_pay_SF` 只在遊戲有 Super Feature 時顯示。
- 不支援 BF／SF 時不得保留空白欄位或以 `0` 代替未支援功能。
- `Interval_Upper` 為該列倍率區間的數值上限；`bg_trigger_fg_cnt_lte_upper` 與 `bg_trigger_fg_pay_lte_upper` 分別累計所有「BG 成功觸發 FG，且該把 BG 倍數小於等於該列上限」的次數與 BG 得分。兩欄必須由未套 Profile cap 的原始觸發 BG 分桶累加，不得先過濾成單一 Profile。
- Card System／倍率權重工具必須先從該 Profile／押注層級的正權重 BG `range` 卡取得最大區間上限，再以相同 `Interval_Upper` 讀取累計 count/pay；不得在程式內寫死 30x、70x 或其他上限。找不到完全相同的區間上限時必須停止並提示補齊倍率區間，不得取較接近的列。
- `cnt` 欄位使用整數；`pay` 欄位使用報表統一的得分精度；`Rate` 欄位使用一致的百分比格式。

共用欄位之後可接遊戲專屬的 By Game 欄位。H016 的 `Multiplier Line` 必須包含：

```text
BG_Big_Ghost_2_Rate
BG_Big_Ghost_3_Rate
BG_Big_Ghost_4_Rate

FG_Big_Ghost_2_Rate
FG_Big_Ghost_3_Rate
FG_Big_Ghost_4_Rate

BG_Avg_Gold_Frames
FG_Avg_Gold_Frames
```

- `--- 以下是 By Game 資訊 ---` 只用於規格分組說明，不是 Excel 的實際欄位。
- 其他遊戲依自身玩法定義 By Game 欄位，不得沿用 H016 不適用的欄位。
- 報表另需保留 Feature、Symbol、Pay Range、卡片抽取占比等驗證所需工作頁。

#### 3.2 必要功能

##### 3.2.1 `BATCH_RUNS`

`BATCH_RUNS` 用於定義要依序執行的模擬組合。每一筆至少包含：

| 欄位 | 必要 | 說明 |
|---|---:|---|
| `config_file` | 是 | 自然機率參數檔；提供輪帶、Table、盤面與原始遊戲機率。 |
| `config_rtp_file` | 是 | 倍率權重參數檔；提供 RTP／Variant 與 Card System 使用的倍率權重。 |
| `bet_mode` | 是 | 押注模式，例如 `0` 為 Normal Bet；其他值依遊戲規格定義。 |
| `total_rounds` | 是 | 本批正式模擬的付費 Round 數，必須為正整數。 |
| `card_system_enabled` | 是 | 是否啟用 Card System，型別為 Boolean。 |
| `card_system_is_newbie` | 是 | `true` 為 Newbie、`false` 為 Oldhand；Card System 關閉時不套用 Profile。 |
| `base_bet` | 是 | 玩家選擇的基礎押注；Simulator 依 Bet Mode 與 Config 倍數計算實際押注及 `bet_tier_amount`，必須大於 0。 |

範例：

```python
BATCH_RUNS = [
    {
        "config_file": "config.js",
        "config_rtp_file": "config_92A.js",
        "bet_mode": 1,
        "total_rounds": 1_000_000,
        "card_system_enabled": True,
        "card_system_is_newbie": False,
        "base_bet": 1,
    },
]
```

- 每批開始時印出 `=== Batch n/total: {...} ===`，內容為該批完整設定。
- 每批重新載入兩份 Config，不得沿用上一批的全域狀態。
- Config 的 `game_id` 不一致時立即停止，不得繼續模擬或輸出報表。
- Card System Off 必須另跑自然機率基準；正式大場次前先以小場次檢查流程與報表。
- NB／EB 必須用實際模式押注金額驗證 `$1.99`、`$2`、`$100`、`$100.01` 邊界；BF／SF 必須用反推後的 Feature 基礎押注驗證相同邊界。
- 至少包含 H026 類型案例：EB 2x、base bet `$1` 應判為中 Bet；BF 75x、購買 `$75` 應判為小 Bet，購買 `$150` 應判為中 Bet。
- Newbie 與 Oldhand 小／中／大 Bet 必須分批驗證 Link／Bonus Game／Game RTP 拆分及 Total RTP。

#### 3.3 執行結束後印出的內容

##### 3.3.1 固定順序與共用格式

Console 輸出順序是固定規範，不得依 dict、DataFrame 或統計完成時間任意排序。每個 Batch 必須依下列順序輸出：

1. Batch 標題：`=== Batch n/total: {...} ===`。
2. 遊戲資訊：`game_name`、`game_id`。
3. Config 與版本：`config_file`、`config_rtp_file`、`math_version`、`card_system`。
4. 執行設定：`bet_mode`、`bet_multi`、`feature_price_multiplier`、`base_bet`、`bet_amount`、`bet_tier_amount`、`bet_tier`、`link_enabled`、`max_multiplier_bg`、`max_multiplier_fg`、`coin_in`、`total_rounds`、`duration`。
5. RTP 與 Feature 統計：從 `rtp_total` 到 `avg_fg_spins`。
6. FG／特殊符號統計：`bg_trigger_fg_cnt`、`bg_trigger_fg_pay`、`special_symbol_cnt`、`SCR`。
7. 波動資訊：`volatility_std`、`standard_error`。
8. Card System 資訊：從 `card_system_profile` 到 `retry_limit_fg`；只在 Card System 開啟時整段顯示。
9. 遊戲專屬資訊：`<< By Game Info >>` 及該遊戲規定的 By Game 欄位。

- 欄位必須依下方範例逐項排列，不得交換前後順序。
- 空白行只用於區塊分隔，不影響欄位順序；不得在同一區塊中插入其他欄位。
- 新增共用欄位時必須先更新本規範並指定位置，不得由個別遊戲自行插入。
- Card System 關閉時只省略第 8 項；其他欄位順序不得改變。

```text
=== Batch 1/1: {'config_file': 'config.js', 'config_rtp_file': 'config_92A.js', 'bet_mode': 1, 'total_rounds': 1000000, 'card_system_enabled': True, 'card_system_is_newbie': False, 'base_bet': 1} ===

game_name               : 幸運王牌
game_id                 : H016
config_file             : config.js
config_rtp_file         : config_92A.js
math_version            : 0.0.0.0
card_system             : on

bet_mode                : Extra Bet
bet_multi               : 2
feature_price_multiplier: n/a
base_bet                : 1.0
bet_amount              : 2.0
bet_tier_amount         : 2.0
bet_tier                : medium_bet
link_enabled            : true
max_multiplier_bg       : by_game
max_multiplier_fg       : 20000
coin_in                 : 100.0
total_rounds            : 1,000,000
duration                : 00.00 sec

rtp_total               : 00.0000%
rtp_link                : 00.0000%
rtp_bonus_game          : 00.0000%
rtp_game                : 00.0000%
rtp_bg                  : 00.0000%
rtp_fg                  : 00.0000%
hit_rate_bg             : 00.0000%
hit_rate_fg             : 00.0000%
fg_trigger_rate         : 00.0000% (cycle 00.00 spins)
retrigger_trigger_rate  : 00.0000% (cycle 00.00 free spins)
avg_fg_spins            : 10.03 spins

bg_trigger_fg_cnt       : 1,000,000
bg_trigger_fg_pay       : 1,000,000
special_symbol_cnt      : 1,000,000
SCR                     : 1,000,000

volatility_std          : 00.00
standard_error          : 00.00

card_system_profile     : oldhand
card_retry_limit        : 10000
retry_total             : 1,000,000
avg_retry               : 00.00

retry_limit_exceeded    : 0
retry_limit_bg_range    : 0
retry_limit_bg_freegame : 0
retry_limit_fg          : 0
```

- `math_version` 顯示 RTP／Variant 模型的完整四段版本號，例如 `2.1.3.13`；Console 依數學文件原格式輸出，不得自行省略或改寫。只有報表檔名依第 3.1.4 節轉為 `02010313`。
- `duration` 顯示正式模擬耗時，不包含 Numba Warm-up，固定顯示到小數點後 2 位並加上 `sec`。
- `rtp_total = rtp_link + rtp_bonus_game + rtp_game`；三個分項的歸類必須依數學文件，且不得重複計算。
- `rtp_bg`／`rtp_fg` 是依場景的交叉檢視，不取代 Link／Bonus Game／Game 的產品 RTP 拆分。
- `bg_trigger_fg_cnt` 為 BG 成功觸發 FG 的累計次數。
- `bg_trigger_fg_pay` 為 BG 成功觸發 FG 且符合目前 Profile BG Trigger Cap 之 Spin 的 BG 累計得分；超過 cap 的觸發 BG 得分不得計入。Card System 關閉的自然機率報表也必須載入指定 RTP Config／Profile 的 cap 套用此過濾。
- `bg_trigger_fg_cnt` 保留所有自然成功觸發 FG 的次數；BG Trigger Cap 只過濾 `bg_trigger_fg_pay`，不得改寫自然 FG 觸發率。
- `Multiplier Line` 的 `bg_trigger_fg_cnt_lte_upper`／`bg_trigger_fg_pay_lte_upper` 保留所有上限的累計結果；它們不受目前執行 Profile 影響，同一份 Card System Off 自然報表必須可供不同 Profile cap 共用。
- Card System 關閉時，從 `card_system_profile` 到 `retry_limit_fg` 的整個區塊不顯示。
- `card_retry_limit` 正式設定為 `10000`。
- `avg_retry` 固定顯示到小數點後 2 位。
- 次數及累計值使用千分位逗號，例如 `1,000,000`。
- 百分比欄位固定顯示 `%`；Cycle 必須同時顯示平均間隔與正確單位。
- `special_symbol_cnt` 統計出現特殊符號 `SC` 的 Spin 次數，Base Spin 與每一次 Free Spin 都要納入。
- 單次 Base Spin／Free Spin 只要盤面出現至少一個 `SC` 就加 `1`；同一 Spin 出現多個 `SC` 仍只加 `1`。
- Cascade 過程若同屬同一次 Spin，不得因不同盤面重複累加；該 Spin 最終最多計數 `1`。
- `special_symbol_rate = special_symbol_cnt / total_rounds`，只作為 SCR 的中間計算值；分母只使用付費場數，不加 Free Spin 數。
- `SCR = special_symbol_rate × 10,000,000,000`。
- Console 與 `Overview` 不輸出 `special_symbol_rate`，只輸出換算後的 `SCR`。
- `total_rounds = 0` 時，`SCR` 輸出 `0`，不得除以零。
- 不適用的 Feature 欄位可不顯示，但不得以錯誤的 `0` 冒充已驗證結果。

##### 3.3.2 Game Info

`<< By Game Info >>` 固定放在共用輸出的最後：Card System On 時接在 `retry_limit_fg` 之後，Off 時接在 `standard_error` 之後。此區用來顯示遊戲專屬統計；欄位依玩法增減，不適用的欄位不得沿用其他遊戲。

H016 範例：

```text
<< By Game Info >>

avg_cascades_bg        : 0.410662
avg_cascades_fg        : 0.6329912625344514
golden_converted       : 182505
w2_events              : 4427
w2_bg_event_rate       : 0.330700%
w2_fg_event_rate       : 1.313552%
w2_bg_count_2          : 2917
w2_bg_count_3          : 373
w2_bg_count_4          : 17
w2_fg_count_2          : 1069
w2_fg_count_3          : 48
w2_fg_count_4          : 3
m1_bg_spin_rate        : 79.9233
```

- H016 的 By Game 欄位必須依上方順序輸出，不得依字母排序或統計產生順序重排。
- H016 若新增其他 By Game 欄位，新增欄位接在既有欄位之後，並同步更新本規範。

#### 3.4 驗證清單

- [ ] `BATCH_RUNS` 每筆均包含七個必要欄位。
- [ ] 自然機率與倍率權重分別從 `config_file`、`config_rtp_file` 載入。
- [ ] 固定 RNG／種子可重現相同結果。
- [ ] Worker 合併後的總場次等於 `total_rounds`。
- [ ] Console 與 Excel 報表的共用欄位及數值一致。
- [ ] `bg_trigger_fg_cnt` 與 `bg_trigger_fg_pay` 位於 `avg_fg_spins` 後，且次數與 BG 得分口徑正確。
- [ ] `free_game` 卡接受的觸發 BG 均未超過同 Profile 正權重 BG `range` 卡的最大上限；超過上限的結果已重跑。
- [ ] Card System Off 的自然機率報表只將符合指定 Profile BG Trigger Cap 的觸發 BG 得分計入 `bg_trigger_fg_pay`，且 `bg_trigger_fg_cnt` 未被 cap 過濾。
- [ ] `Multiplier Line` 每一列均有 `Interval_Upper` 與累計至該上限的 BG Trigger count/pay；累計值單調不減，最後一列 count 等於 `bg_trigger_fg_cnt`。
- [ ] 倍率權重工具從 Profile 的最大正權重 BG range 自動選取完全相同上限的累計 count/pay，未寫死個別 Profile 或遊戲 cap。
- [ ] `special_symbol_cnt` 同時統計 Base Spin 與 Free Spin，且同一 Spin 即使出現多個 `SC` 也只累加一次。
- [ ] `SCR` 等於 `(special_symbol_cnt / total_rounds) × 10,000,000,000`，且 Console 與 `Overview` 的數值一致。
- [ ] Card System 區塊位於 `standard_error` 後；Card System Off 時整段移除且其他欄位不重排。
- [ ] `Overview` 與 Console 的內容及順序一致，且未包含 Batch 與 `<< By Game Info >>` 標題。
- [ ] `Multiplier Line` 包含所有共用欄位，並依遊戲功能正確顯示或移除 BF／SF 與 By Game 欄位。
- [ ] 報表檔名依 H026 規則排列，時間、Bet Mode、場次及 Card System 後綴均正確。
- [ ] Card System Off 使用基礎 `game_id` 與 2 位數基礎版本，例如 `H0161_02`。
- [ ] Card System On 使用 RTP／Variant `game_id` 與補零後的四段版本，例如 `H016192A_02000000`。
- [ ] Oldhand 的 Card System On 報表檔名包含 `small_bet`、`medium_bet` 或 `big_bet`，且與 `bet_amount` 判定結果一致。
- [ ] 四段版本已逐段補滿 2 位數，例如 `2.1.3.13` 正確輸出為 `02010313`。
- [ ] RTP 與 Feature Trigger 接近目標，偏差有統計解釋。
- [ ] Newbie 的 BG／FG Max Multiplier 分別不超過 30x／120x，且 Link RTP 為 0%。
- [ ] Oldhand 小 Bet 的 FG Max Multiplier 不超過 20000x，且 Link RTP 為 0%。
- [ ] Oldhand 中 Bet 的 FG Max Multiplier 不超過 20000x，且 Link RTP 為 2%。
- [ ] Oldhand 大 Bet 的 FG Max Multiplier 不超過 2000x，且 Link RTP 為 2%。
- [ ] 各批次皆滿足 `rtp_total = rtp_link + rtp_bonus_game + rtp_game`，並符合第 1.4 節目標。
- [ ] BF／SF Newbie 為 `0% + 4% + 92.5% = 96.5%`。
- [ ] BF／SF Oldhand 小 Bet 為 `0% + 4% + 92.5% = 96.5%`。
- [ ] BF／SF Oldhand 中／大 Bet 為 `2% + 2% + 92.5% = 96.5%`。
- [ ] Card System 設定占比與實際占比一致。
- [ ] Retry Limit Exceeded 為零，或已有明確原因與核准處理方式。
- [ ] 最大獎未超出限制，理論可達結果有相應測試。
- [ ] 所有正式 Config／Mode／Profile 均有最新版本報表。

---

### Demogame

#### 4.1 用途與載入

Demogame 是模型邏輯、流程與 Debug 資訊的可操作驗證介面，不只是視覺展示。它必須能用單局結果證明 Config、Simulator 與遊戲規則一致。

- 主入口固定為 `index.html`，使用相對路徑，雙擊即可離線執行。
- Demogame 的模型顯示格式為 `<Config>-<Profile>`，例如 `92A-Oldhand`。
- 遊戲名稱、盤面、輪帶、權重、Paytable、Bet Mode 與 Feature 參數從 Config 取得。
- 不得為演出方便另寫一套簡化數學邏輯。
- Config 無法載入或欄位不完整時要顯示明確錯誤，不得靜默使用舊值。

##### 4.1.1 遊戲類型命名規則

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
| H027 奧林帕斯 2500 | `Video Slot - Pay Anywhere / Cascade` |
| H028 雷神爆金 1000 | `Video Slot - 2,025–32,400 Ways / Megaways / Cascade` |

目前正式遊戲沒有使用 `Cluster Pay`；日後只有實際採相鄰群集判獎的遊戲才能列入此類。

#### 4.2 共用區域與 By Game 區域

圖示中的遊戲顯示區域屬於 By Game 設計；除此之外的 Demogame 區域均為所有遊戲共用。

##### 4.2.1 By Game 區域

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

##### 4.2.2 共用區域

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

#### 4.3 補牌方式

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

#### 4.4 必要行為

- 支援 Normal Spin，以及遊戲實際存在的 Extra Bet、Buy Feature、Super Feature。
- Bet 顯示與 Credit 扣款使用實際模式成本；Win 依流程加入。
- Auto、Speed、Reset 不得改變 RNG、得分或統計結果。
- BG、Cascade、FG、Retrigger 與 Feature 狀態按真實流程播放。
- Config、Version、Profile、押注層級、Card System 與 Language 只顯示實際支援的內容。
- Help 與 `game_help_draft.md` 一致，不在 HTML 另維護一份規則。

#### 4.5 Debug 與重現

Debug Mode 至少可查看：

- Config、Version、Profile、Bet Mode、Mode／Feature Price 倍數、base bet、實際模式押注、`bet_tier_amount`、押注層級、Link 資格、BG／FG Max Multiplier 與 Card System 狀態。
- Card 抽獎值、卡片區間與 Retry 次數。
- Table、Drop Mode、Reel RNG、總範圍、Stop Index 與 Reel Length。
- 初始盤面、每段 Cascade、Line／Ways Win、Multiplier 與最終結果。
- FG 觸發、局數、Retrigger、整包 Win 及即時 Log。

指定 Card Range 與 Reel RNG 必須互斥。指定值要檢查數量與範圍，且只作用於規格定義的下一個 Spin；不得因指定 RNG 或 Force FG 進入無限重跑。

#### 4.6 與 Simulator 對帳

至少準備下列可重現案例：無獎 BG、一般得分、Wild／Scatter、Cascade／Multiplier、FG Trigger／Retrigger、各 Bet Mode、Newbie、Oldhand 小／中／大 Bet、Link 可用／不可用、Card System range／free_game／Retry、Max Win 截斷及遊戲專屬 Feature。

逐項確認盤面、RNG、各段得分、Total Win、Coin In、倍率、Feature 狀態與 Retry 計數一致。

#### 4.7 交付檢查

- [ ] 離線開啟無錯誤，Console 無未處理例外。
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

---

### Config

#### 5.1 定位與轉檔

Config 分為基礎 Config 與 RTP／Variant Config：

| Config | 對應數學文件 | 版本格式 |
|---|---|---|
| `config.js` | `H<遊戲編號>1.xlsx`，例如 `H0161.xlsx` | `excel_version` 為 1 碼 |
| `config_<RTP><Variant>.js` | `H<遊戲編號>1<RTP><Variant>.xlsx`，例如 `config_92A.js` 對應 `H016192A.xlsx` | `excel_version` 為 4 碼，且第 1 碼對應基礎版本 |

- `Newbie`／`Oldhand` 是 Card System 的 Player Profile，不寫入 Config 檔名。
- RTP／Variant 模型的 XLSX、Config、Simulator、Demogame 與報表必須使用相同 Config 代號。

兩種 Config 都是 Simulator 與 Demogame 的執行參數，不是人工獨立維護的第二份數學文件。正式參數必須由各自對應的 `Source/*.xlsx` 透過 `Source/xlsx_to_config.py` 產生。

```text
修改基礎或 RTP／Variant Source XLSX
      ↓
依文件類型更新 1 碼或 4 碼版本
      ↓
執行 update_config.bat 或 xlsx_to_config.py
      ↓
檢查欄位、型別、長度、權重與版本
      ↓
完成 XLSX → Config → 程式讀取對帳
      ↓
執行 Simulator 與 Demogame 驗證
```

禁止直接修改 Config 中由 XLSX 產生的大型陣列來規避轉檔；結果錯誤時應修正 XLSX、mapping 或轉檔程式。

#### 5.2 最低資料

Config 至少應提供遊戲實際需要的：

- `game_id`、`game_name`、`excel_version` 與 Config 類型／代號。
- Reel 數、盤面尺寸、Symbol ID／名稱／屬性。
- Reel Strip／Weight／Length、Paytable、Payline／Ways／Cluster。
- Table、Table Weight、Drop Mode 與各 Scene 資料。
- Bet Mode ID、成本倍率、Bet Level／DENOM。
- BG、FG、Cascade、Multiplier、Retrigger 與 Feature 參數。
- Card System 開關、Retry Limit、Profile、NB／EB 與 BF／SF 的押注層級判定方式、Oldhand 小／中／大 Bet 門檻、卡片區間與各模式／層級權重。
- Link 資格、Link／Bonus Game／Game RTP 目標與 Total RTP。
- Newbie BG／FG、Oldhand 小／中／大 Bet 的 Max Win／Max Multiplier 與其他產品限制。

同一概念在不同 Config 間必須保持一致，並記錄於 `Source/xlsx_config_usage_mapping.md`。

#### 5.3 資料驗證

- `game_id` 與所在遊戲資料夾一致。
- `config.js` 的 `excel_version` 與基礎 XLSX 完全一致，且只能是 1 碼。
- 初次建立時，競品模型的基礎 XLSX／Config 版本為 `0`，非競品模型為 `1`；來源分類必須可追溯。
- `config_<RTP><Variant>.js` 的 `excel_version` 與對應 RTP／Variant XLSX 完全一致，且必須是 4 碼。
- RTP／Variant Config 的版本第 1 碼，必須與 `config.js` 及基礎 XLSX 的版本相同。
- Config 檔名、類型、內部 RTP／Variant 與來源 XLSX 相符。
- 所有 Weight 非負，啟用選項的總權重大於 0。
- Newbie 與 Oldhand 小／中／大 Bet 的權重、Link 資格、RTP 拆分及倍率上限齊全且互相一致。
- 押注層級邊界必須精確符合 `< $2`、`>= $2 且 <= $100`、`> $100`，不得因浮點誤差選錯層級。
- NB／EB 必須以實際模式押注判斷；BF／SF 必須以購買價格除以 Feature Price 倍數後的基礎押注判斷。
- Reel、Weight、Paytable、Symbol 與 Mode 陣列長度相容。
- 所有 ID／索引在有效範圍，無重複或遺漏。
- Min／Max、倍率、局數與 Max Win 限制合法。
- 未支援的 Mode／Profile／Feature 不存在或明確停用。
- 浮點精度足以還原來源數值，不因格式化造成 RTP 偏差。

#### 5.4 版本與歷史檔

- 正式 Config 放在遊戲資料夾根層，包括基礎 `config.js` 與實際支援的 `config_92A.js` 等 RTP／Variant Config。
- 歷史 Config 放在對應的 `Versions/` 版本目錄；基礎 Config 與 RTP／Variant Config 都必須保留來源及版本關係。
- `Versions/version_manifest.js` 記錄完整版本、可用 Config、路徑與變更說明。
- Runtime、Simulator 與 Demogame 不得自行覆寫 Config 版本。
- Index 載入 `config.js` 時顯示 1 碼基礎版本；載入 RTP／Variant Config 時顯示完整 4 碼版本。
- RTP／Variant 版本若第 1、2 碼相同，Index 只顯示第 3、4 碼最新的版本。
- Version 與 Config 選單只列出 manifest 中實際存在且相容的組合。

#### 5.5 最終交付檢查

- [ ] `config.js` 對應基礎 XLSX；每個 `config_<RTP><Variant>.js` 對應相同 RTP／Variant 的 XLSX。
- [ ] 基礎 XLSX／Config 使用 1 碼版本，RTP／Variant XLSX／Config 使用 4 碼版本，且第 1 碼一致。
- [ ] XLSX、Config、Simulator、Demogame 與文件版本一致。
- [ ] Config 可由 Source 工具重新產生，且不會產生非預期差異。
- [ ] 每個 Config 都有來源 XLSX 與 mapping 說明。
- [ ] Simulator 與 Demogame 沒有重複或覆寫 Config 參數。
- [ ] 所有可選 Config／Version／Profile／Mode 均真實存在且已驗證。
- [ ] 最新模擬報表已保存於 `Record/`，結果符合目標與限制。
- [ ] 代表性單局已完成 Config、Simulator、Demogame 三方對帳。
- [ ] `~$*.xlsx`、`__pycache__/`、臨時檔與測試輸出未列入正式交付。

#### 5.6 完成條件

模型只有在下列條件全部成立後才可視為完成：

1. 數學規則與計算口徑明確，無未決定的核心邏輯。
2. Config 可由數學來源重建，版本與參數可追溯。
3. Simulator 已完成所有支援組合的統計驗證。
4. Card System 的權重、區間、Retry 與失敗監控通過。
5. Demogame 的代表性單局可與 Simulator 對帳。
6. 數學模型、PAR Sheet、Game Rule、Config、報表、Demogame、Help、Game Description 與 Game List 均為同一正式版本，且必要的 Markdown 文件皆已同步更新。

---

## 其他文件

### Help

#### 必要交付檔案

每款遊戲必須同時提供下列兩份 Help 文件：

- `Help.xlsx`
- `game_help_draft.md`

其中 `game_help_draft.md` 為必要的 Markdown 版本，不得只交付 XLSX。

兩份文件的文字、規則、數值、表格內容、章節順序與語言版本必須完全一致；檔案格式造成的版面呈現差異不得改變或省略任何內容。任一份文件更新時，另一份必須在同一次修改中同步更新。

#### 內容規則

- Help 必須依 `game_rule.md` 編寫，只整理玩家需要理解的玩法，不得新增、刪除或改變正式遊戲規則。
- Help 內的遊戲名稱、遊戲類型、Bet Mode、Paytable、Symbol、Feature、倍率、局數、觸發條件、Max Win 與 Jackpot 說明，必須與 Game Rule、數學模型及 Config 一致。
- OP Jackpot 的內容與格式必須參考 `H5企劃書_101014_Pinata Beat 1000_彩罐熱舞.xlsx`，不得自行省略 OP Jackpot 的必要規則或改用未核准的格式。
- OP Jackpot 參考檔位於 `Project/Slots/H026_彩罐熱舞 1000/其他/H5企劃書_101014_Pinata Beat 1000_彩罐熱舞.xlsx`；若檔案移動，必須同步更新本規範中的參考路徑。
- `Help.xlsx` 與 `game_help_draft.md` 若有任何內容差異，該遊戲不得視為完成交付。

#### 交付檢查

- [ ] `Help.xlsx` 與 `game_help_draft.md` 均存在。
- [ ] 兩份 Help 的文字、規則、數值、表格、章節順序與語言版本完全一致。
- [ ] Help 與 `game_rule.md`、數學模型及 Config 的內容一致。
- [ ] OP Jackpot 已參考 `H5企劃書_101014_Pinata Beat 1000_彩罐熱舞.xlsx` 編寫並完成核對。

### Game Description

Game Description 用於說明遊戲模型參數的使用方式，以及各項參數如何對應實際遊戲功能。

- 每款遊戲必須提供 `game_description.md`，不得只保留 DOCX、XLSX、簡報或口頭說明。
- 內容至少包含參數名稱、用途、使用模式、選表條件、限制與對應的數學模型／Config 欄位。
- 內容必須與數學模型中的 `Gaem Description` 工作表、Game Rule 及 Config mapping 一致。
- 參數或選表邏輯更新時，必須同步更新 `game_description.md`。

### Game List

Game List 用於彙整所有遊戲提供給企劃、開發、測試及其他職能查閱的共用資訊。

- 必須提供 Markdown 版本 `Project/Slots/game_list.md`，不得只保留 XLSX 或其他格式。
- 每款正式遊戲至少記錄 Game ID、中英文名稱、遊戲類型、盤面／得分方式、支援的 Bet Mode、RTP／版本來源與必要 Feature 資訊。
- Game List 只放跨遊戲比較與識別所需資訊，不重複完整數學公式或整份 Game Rule。
- 遊戲新增、改名、玩法分類、Bet Mode、版本或重要 Feature 異動時，必須同步更新 `game_list.md`。

---

## 附錄

### Card System

#### 2.1 定位與限制

Card System 是結果篩選與分流機制，不是獨立玩法。遊戲先依原始輪帶、盤面、判獎與 Feature 流程產生結果，再依預先抽出的卡片條件決定接受或重跑。

Card System 可控制倍率區間、要求觸發 Free Game、依 Newbie／Oldhand 與 Oldhand 小／中／大 Bet 改變結果分布，並依 Bet Mode 拆分 BG、FG、Buy Feature 與 Super Feature 的目標。

Card System 不得直接修改輪帶、Paytable、判獎公式、符號功能、FG 局數或演出流程。重跑會改變最終結果分布與 RTP，因此必須以實際流程模擬，不能只用權重推算。

#### 2.2 設定結構

```text
card_system
├─ enabled
├─ retry_limit
├─ newbie
│  ├─ normal_bet    → weight_bg／weight_fg
│  ├─ extra_bet     → weight_bg／weight_fg
│  ├─ buy_feature   → weight_fg
│  └─ super_feature → weight_fg
└─ oldhand
   ├─ normal_bet
   │  ├─ small_bet  → weight_bg／weight_fg
   │  ├─ medium_bet → weight_bg／weight_fg
   │  └─ big_bet    → weight_bg／weight_fg
   ├─ extra_bet
   │  ├─ small_bet  → weight_bg／weight_fg
   │  ├─ medium_bet → weight_bg／weight_fg
   │  └─ big_bet    → weight_bg／weight_fg
   ├─ buy_feature
   │  ├─ small_bet  → weight_fg
   │  ├─ medium_bet → weight_fg
   │  └─ big_bet    → weight_fg
   └─ super_feature
      ├─ small_bet  → weight_fg
      ├─ medium_bet → weight_fg
      └─ big_bet    → weight_fg
```

- `retry_limit` 正式預設為 `10000`。
- `weight > 0` 才可抽中；`weight = 0` 只保留設定；權重不得小於 0。
- 每個啟用的 Profile／Mode 至少要有一張正權重卡片。
- 抽中率為該卡權重除以同組所有正權重總和。
- Oldhand 依第 1.4.3 節算出的 `bet_tier_amount` 選擇 `small_bet`、`medium_bet` 或 `big_bet`；NB／EB 分別持有 BG／FG 權重，BF／SF 分別持有 Feature FG 權重。
- 啟用 Oldhand 的 Profile／Mode 必須同時提供小／中／大 Bet 三套權重，不得缺少其中一套或互相 fallback。
- Profile 缺少某個 Mode 時，必須明定不套用或指定唯一 fallback，程式不得自行猜測。

#### 2.3 卡片判定

`range` 卡使用 `(min, max]`：

```text
結果倍率 > min 且 結果倍率 <= max
```

- `(15, 20]` 不包含 15x、包含 20x；需要包含 0x 時可用 `(-1, 0]`。
- Newbie BG 的最高可用區間為 `(25, 30]`，FG 的最高可用區間為 `(100, 120]`；超過各自上限的區間權重必須為 0。
- Oldhand 小／中 Bet FG 的最高可用區間為 `(10000, 20000]`；Oldhand 大 Bet FG 的最高可用區間為 `(1000, 2000]`。
- 任一區間超過目前 Profile／押注層級的 Max Multiplier 時，其權重必須為 0。
- BG 已觸發 FG 時，即使 `pay_bg` 落入區間，也不得當作一般 BG `range` 結果。
- `free_game` 卡未觸發 FG 時必須重跑 BG。
- `free_game` 卡必須同時驗證 BG 倍率上限（BG Trigger Cap）：除觸發 FG 外，觸發該次 BG 的倍率不得超過同一 Profile／押注層級／Mode 之 `base_game` 內所有正權重 `range` 卡的最大 `max`。
- BG Trigger Cap 使用 Normal Bet 基準成本計算，判定式為 `pay_bg / card_system_coin_in <= cap`；等於上限時可接受，超過上限時整把 BG 重跑。
- `weight = 0` 的 `range` 卡不得用來放大 cap；啟用 `free_game` 卡的 Profile／Mode 必須至少有一張正權重 `range` 卡可提供 cap。
- 事件卡只定義接受條件，不得直接放置 Scatter 或直接呼叫 FG。

##### 2.3.1 Link 資格

- Link 資格一律依第 1.4.3 節算出的 `bet_tier_amount` 判斷；NB／EB／BF／SF 都使用同一組 `< $2`、`$2～$100`、`> $100` 邊界。
- Newbie 不得觸發或獲得 Link 彩金，Link RTP 必須為 0%。
- Oldhand 小 Bet 不得觸發或獲得 Link 彩金，Link RTP 必須為 0%。
- Oldhand 中 Bet 與大 Bet 可以觸發 Link 彩金，Link RTP 目標為 2%。
- `link_enabled = false` 時不得只把 Link 派彩改成 0；結果中不得出現已觸發但不派彩的 Link 事件或演出。
- Link 資格、觸發流程與 RTP 統計必須由 XLSX、Config、Simulator 與 Demogame 使用同一套設定。

#### 2.4 Retry 流程

```text
取得 Profile、Bet Mode、base bet、Mode 倍數與 Feature Price 倍數
        ↓
NB／EB 以實際模式押注、BF／SF 以 Feature 基礎押注計算 bet_tier_amount
        ↓
Oldhand 依 `< $2`、`$2～$100`、`> $100` 選擇小／中／大 Bet 權重與 Link 資格
        ↓
固定抽出目標卡片
        ↓
依原始規則產生結果
        ↓
符合 → 接受並記錄
不符 → retry + 1 → 重跑
                    ↓
             達上限後保留最後結果並記錄失敗
```

- 同一局 Retry 期間固定原本抽到的卡片，不得每次重抽。
- `range` 卡每次 Retry 也必須依該 Bet Mode 的自然 Table Selection 重新抽表並產生完整結果，再判斷倍率區間；卡片內的 Table／代號欄位只可作報表分類，不得直接指定或覆蓋數學 Table。
- BG 與 FG 為兩階段條件時，先完成 BG；觸發 FG 後再獨立抽 FG 卡，驗證整包 FG。
- 抽中 `free_game` 卡時，同一張卡固定不變，持續依自然 BG 選表重骰，直到同一把同時滿足「觸發 FG」與 BG Trigger Cap；不得使用 Buy Feature 入口盤面替代。
- Buy／Super Feature 必須先成功進入 Feature，再判定整包結果。
- Retry 不得重複扣款、重複計入場次或污染統計。
- 達上限時停止，保留最後結果並記錄 `Retry Limit Exceeded` 與失敗分類。
- 某張卡經常達到上限時，先檢查區間可達性、權重、倍率分母、Profile 與押注層級，不得只提高上限。

#### 2.5 倍率分母

| 模式 | RTP 實際成本 | Card System 倍率判定成本 | 押注層級判定金額 |
|---|---|---|---|
| Normal Bet | Normal Bet 實際成本 | Normal Bet 基準成本 | Normal Bet 實際押注金額 |
| Extra Bet | Extra Bet 加價後成本 | Normal Bet 基準成本 | Extra Bet 實際押注金額 |
| Buy／Super Feature | Feature 購買成本 | Normal Bet 基準成本 | Feature 購買價格除以 Feature Price 倍數後的基礎押注 |

Card System 的倍率分母與押注層級判定金額是兩個不同概念，不得混用。個別遊戲若採不同定義，必須在數學文件註明，並同步修改 XLSX、Config、Runtime、Simulator 與 Demogame。

#### 2.6 必要監控

報表至少記錄 Config、Version、Profile、Bet Mode 類別、base bet、實際模式押注、Feature Price 倍數、`bet_tier_amount`、押注層級、Link 資格、倍率上限、各卡抽取占比、Total／平均 Retry、Retry Limit Exceeded 比率與失敗分類。Card System 關閉時不得抽卡或 Retry；實際占比應在合理誤差內接近設定權重。
