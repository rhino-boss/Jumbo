<!-- 中英文合併一份（2026-11-26）：前半中文、後半 English；docx 只出英文版 -->

# Math Document Description — 101014 彩罐熱舞 1000（Pinata Beat 1000）

**適用範圍：Normal Bet（一般下注）**

| 項目 | 內容 |
| --- | --- |
| Game ID | 101014 |
| Math files | `H026197A_Bet2.xlsx`（RTP 92%）、`H026197A_Bet1.xlsx`（RTP 94%）、`H026197A_Bet300.xlsx`（大 Bet，RTP 92%） |
| Version | 4.0.0.8 |
| 對應程式 | `simulator.py` + `config_92.js` / `config_94.js` |
| 盤面 | 5 輪 × 3 列記分（程式內部持有 4 列，最上列不記分） |
| 線數 | 20 條固定線，左 → 右 |
| Coin In | 100（Base Bet 100 × Price 1） |
| 押注模式 | 僅 Normal Bet |

---

## 目錄

- [一、工作表說明](#一工作表說明)
  - [1-1 程式如何使用 xlsx 的參數](#1-1-程式如何使用-xlsx-的參數)
  - [1-2 各工作表用途一覽](#1-2-各工作表用途一覽)
  - [1-3 Overview](#1-3-overview)
  - [1-4 Description](#1-4-description)
  - [1-5 Parameter](#1-5-parameter)
  - [1-6 Multiplier_Weight](#1-6-multiplier_weight)
  - [1-7 Multiplier_Weight_Detail](#1-7-multiplier_weight_detail)
  - [1-8 OP Jackpot](#1-8-op-jackpot)
  - [1-9 Base Game 輪帶表](#1-9-base-game-輪帶表)
  - [1-10 Free Game 輪帶表](#1-10-free-game-輪帶表)
- [二、Parameter 工作表的遊戲參數說明](#二parameter-工作表的遊戲參數說明)
  - [2-1 Line](#2-1-line)
  - [2-2 Table Selection Weight - Base Game](#2-2-table-selection-weight---base-game)
  - [2-3 Multiplier Range](#2-3-multiplier-range)
  - [2-4 Used Special Pool Weight](#2-4-used-special-pool-weight)
  - [2-5 Multiple Selection Weight（五組）](#2-5-multiple-selection-weight五組)
  - [2-6 Eliminate Table Weight](#2-6-eliminate-table-weight)
- [三、遊戲邏輯](#三遊戲邏輯)
  - [3-1 盤面與座標系統](#3-1-盤面與座標系統)
  - [3-2 符號與角色](#3-2-符號與角色)
  - [3-3 單次 spin 的流程](#3-3-單次-spin-的流程)
  - [3-4 判獎規則](#3-4-判獎規則)
  - [3-5 Cascade 與金框轉 Wild](#3-5-cascade-與金框轉-wild)
  - [3-6 倍數的分配、收集與作用](#3-6-倍數的分配收集與作用)
  - [3-7 Free Game](#3-7-free-game)
  - [3-8 一局（一次付費 spin）的完整流程](#3-8-一局一次付費-spin的完整流程)
  - [3-9 重要規則整理](#3-9-重要規則整理)
- [四、卡片系統說明](#四卡片系統說明)
  - [4-1 用途](#4-1-用途)
  - [4-2 卡片的結構](#4-2-卡片的結構)
  - [4-3 單局的判定流程](#4-3-單局的判定流程)
  - [4-4 與 Multiplier_Weight_Detail 的關係](#4-4-與-multiplier_weight_detail-的關係)
  - [4-5 注意事項](#4-5-注意事項)

---

## 一、工作表說明

### 1-1 程式如何使用 xlsx 的參數

`simulator.py` 使用 xlsx 的參數執行模擬。理解以下三點，才能正確對照工作表上的欄位與程式行為：

1. **權重只看相對大小。**
   所有標示為 Weight 的欄位都是相對權重，不需要是機率、也不需要湊成 100%。程式抽樣時，是在「該組權重的總和」範圍內取一個隨機值，再依權重比例落到對應項目。**每一組權重的總和就是該組的分母**，因此在同一組內單獨調高某一項，會同時稀釋其他項的機率。

2. **金框符號在使用時被拆成兩層資訊。**
   盤面上實際存放的是「基底符號」（例如金框 `G1` 在盤面上就是 `M1`），另外用兩個遮罩分別記錄「這一格是不是金框」與「這一格的倍數是多少」。
   因此 `Overview` 的 Pay Table 中 `G1~GJ` 那 9 列的賠率，程式並不會讀取 —— 判獎一律使用基底符號的賠率。那 9 列僅供對照，用來確認金框與基底符號的賠率一致。

3. **並非所有欄位都會被程式使用。**
   各工作表左側的張數統計、佔比、平均值等欄位，以及 `Description`、`Multiplier_Weight_Detail`、`OP Jackpot` 三張工作表，都屬於設計與檢核用途，程式不會讀取。下方各節會逐一標明。

### 1-2 各工作表用途一覽

| 工作表 | 提供什麼 | 影響哪一段玩法 | 程式使用 |
| --- | --- | --- | --- |
| `Overview` | 遊戲基本規格、RTP 拆解、免費遊戲場次設定、符號賠率表 | 成本計算、判獎、進入 FG 的場次 | ✅ 部分 |
| `Description` | 參數流程的文字說明 | — | ❌ 文件用 |
| `Parameter` | 盤線、各類權重、倍數清單 | 開局選表、倍數分配、補牌模式 | ✅ |
| `Multiplier_Weight` | 卡片系統的兩組卡片權重 | 單局結果的接受／重抽 | ✅ |
| `Multiplier_Weight_Detail` | 上表權重的推導過程與目標值 | — | ❌ 設計用 |
| `OP Jackpot` | 模擬紀錄的統計（spin 數、C1 數） | — | ❌ 驗證紀錄 |
| `BG_Symbol`<br>`BG_Symbol (2)`<br>`BG_Symbol (3)` | Base Game 的三組輪帶與補牌轉盤 | BG 的開局盤面與 Cascade 補牌 | ✅ |
| `FG_Symbol`<br>`FG_Symbol (2)`<br>`FG_Symbol (3)` | Free Game 的三組輪帶與補牌轉盤 | FG 的開局盤面與 Cascade 補牌 | ✅ |

兩份 math file 的工作表結構完全相同。

### 1-3 Overview

提供遊戲的基本規格與數學目標值。

| 區塊 | 內容 | 程式使用 |
| --- | --- | --- |
| Model / Version | 模型代號與版本 | ✅ 寫入輸出檔名 |
| RTP 主列 | 押注基準與各項派彩率（見下表） | 僅 `Base Bet` ✅，其餘為目標值 |
| Reel # / Visible Window Size | 輪數與記分列數 | ✅ 建立盤面尺寸 |
| Free Spins Setting | 記分區 Scatter 數量對應的免費場次，以及總場次上限 | ✅（見 3-7） |
| Pay Table | 各符號的代號、Id 與 3／4／5 連線賠率 | ✅ 判獎 |

**RTP 主列的欄位**

| 欄位 | 意義 |
| --- | --- |
| `Base Bet` | 押注基準 |
| `Game RTP` | 遊戲本身的派彩率，等於 Base Game 與 Free Game 兩段之和 |
| `Bonus RTP` | 固定彩金池的派彩率（OP Jackpot 的 MINOR + MINI） |
| `Link RTP` | 連線累積彩金的派彩率（OP Jackpot 的 GRAND + MAJOR） |
| `Total RTP` | `Game RTP + Bonus RTP + Link RTP`，即含彩金的總派彩率 |
| `Hit JP Symbol appear rate` | 每次 spin 畫面上至少出現一顆 Hit JP Symbol（本遊戲為 Scatter）的機率，以 Threshold 10,000,000,000 為分母表示；供彩金模組換算實際判定機率使用 |

**Coin In 的計算**

```
Coin In = 下注倍數 × Base Bet
```

所有 RTP 與倍率統計都以「該局總得分 ÷ Coin In」為單位。

> 兩份 math file 的 `Game RTP` 分別為 92% 與 94%，但 `Link RTP` 分別為 2% 與 0%，因此 **`Total RTP` 兩版一致（96%）**。
>
> 這對應 OP Jackpot 的兩組設定：`JP0100B` 募集 GRAND 1% + MAJOR 1%（Link 2%），`JP0100A` 則將兩者設為 0%（Link 0%）；MINOR 0.8% + MINI 1.2% 在兩組設定中都存在，因此 `Bonus RTP` 固定為 2%。
>
> `Game RTP` 的 Base Game 與 Free Game 拆解值記錄在 `Multiplier_Weight_Detail`（見 [1-7](#1-7-multiplier_weight_detail)），FG 的觸發率與週期亦同。
>
> `Hit JP Symbol appear rate` 的數值取自 `OP Jackpot` 工作表的 `SCR` 欄位，該欄與 `C1 cnt`／`Spin` 為同一次模擬的紀錄。各組 `SCR` 數值如下（分母 Threshold = 10,000,000,000）：
>
> | Status | Bet Type | SCR（92 版） | SCR（94 版） |
> | --- | --- | --- | --- |
> | Newbie | Normal Bet | 3,368,441,800 | 3,368,441,800 |
> | Newbie | Extra Bet | 3,830,983,800 | 3,830,983,800 |
> | Oldhand | Normal Bet | 3,370,654,300 | 3,371,218,200 |
> | Oldhand | Extra Bet | 3,829,976,500 | 3,830,025,700 |
>
> Newbie 兩版共用同一組模擬紀錄，數值相同；Oldhand 兩版各自模擬，數值略有差異。

### 1-4 Description

以文字條列各參數在 BG／FG 流程中的使用順序，內容與本文件第三章一致。純文件用途，程式不讀取。

### 1-5 Parameter

整個模型的核心控制面板，逐區塊說明見[第二章](#二parameter-工作表的遊戲參數說明)。

### 1-6 Multiplier_Weight

卡片系統的輸入。版面為：

| 欄 | 標題 | 用途 |
| --- | --- | --- |
| `Range` | 得分倍率區間標籤 | 決定每張卡片的上下界 |
| `Weight_NB_BG` | Base Game 卡片權重 | 每一局開始時抽一張 |
| `Weight_NB_FG` | Free Game 卡片權重 | 觸發 FG 後抽一張 |

列的部分由一連串「得分倍率區間」構成（得分 ÷ Coin In，左開右閉），最後一列 `Free Game` 是一張特殊卡：它不看金額，只要求「這一局必須觸發 Free Game」。

兩欄的權重總和各自被校準到同一個基數，因此權重值可以直接理解為「該結果出現的機率」。詳細機制見[第四章](#四卡片系統說明)。

**兩份 math file 的差異只在 `Weight_NB_FG` 一欄** —— 也就是 FG 的派彩配置。`Weight_NB_BG`、整張 `Parameter`、以及全部六張輪帶表在兩份檔案中完全相同。

### 1-7 Multiplier_Weight_Detail

`Multiplier_Weight` 那兩欄權重的推導工作表，程式不讀取。

| 區塊 | 內容 |
| --- | --- |
| Threshold | 權重的正規化基數 |
| Coin in | 引用 `Overview` 的押注基準 |
| 目標值列 | Normal Bet 的目標 RTP、Hit Rate、FG 週期、平均倍率（`Overview` 的 RTP 拆解即引用此處） |
| `Base Game (Normal Bet)` 區塊 | 每個得分區間的自然機率模擬結果（次數／派彩／命中率／平均倍率）、人工調整係數，以及校準後的權重 |
| `Free Game (Normal Bet)` 區塊 | 同上，針對 FG 的整段得分 |
| 對照欄 | 目前值與競品值的差異，供調整時參考 |

調參的實際迴路是：先關閉卡片系統跑出自然機率 → 填入模擬結果 → 調整係數 → 得到校準後的權重 → 寫入 `Multiplier_Weight` → 開啟卡片系統重跑驗證。

> `Multiplier_Weight` 的兩欄權重原本是以動態陣列公式從本工作表溢出（spill）取得；本送驗版本已將其轉為靜態數值，因此兩張工作表的數值一致但不再互相連動。

### 1-8 OP Jackpot

記錄各次模擬的 spin 數、記分區 Scatter 數與 Scatter 累計數，供驗證比對。程式不讀取，也不含任何 Jackpot 的機率或派彩參數。

### 1-9 Base Game 輪帶表

Base Game 的三組輪帶設定。三張表版面完全相同，各自定義「一組輪帶 + 一組補牌轉盤」。

| 欄位群 | 內容 | 程式使用 |
| --- | --- | --- |
| 最左側 Symbol / Description / R1~R5 / ID | 該表輪帶上各符號的張數統計與每輪合計 | ❌ 檢核用 |
| Normal / Golden Symbol 佔比 | 一般符號與金框符號的比例 | ❌ 檢核用 |
| 合併統計 | 基底符號與其金框版本的張數合計 | ❌ 檢核用 |
| `Symbol` | 輪帶內容（文字） | ❌ 給人閱讀 |
| `Symbol ID R1~R5` | 輪帶內容（代號） | ✅ 實際輪帶 |
| `Symbol Weight R1~R5` | 每個輪帶位置的停輪權重 | ✅ 決定停輪位置 |
| `Eliminate Wheel Weight A` | 補牌轉盤權重（A 組） | ✅ Cascade 補牌 |
| `Eliminate Wheel Weight B` | 補牌轉盤權重（B 組） | ✅ Cascade 補牌 |

**三張表的角色分工**

| 表 | 角色 | 特徵 |
| --- | --- | --- |
| `BG_Symbol` | 一般局 | 金框只出現在第 2、3、4 輪；Scatter 分布不足以湊出觸發門檻 |
| `BG_Symbol (2)` | 全金框局 | 第 3 輪整輪為金框且保證帶倍數；Scatter 分布同上 |
| `BG_Symbol (3)` | 觸發 FG 局 | Scatter 分布在全部 5 輪；金框的倍數配置為零，避免進入 FG 前先吃到大倍數 |

> 由此可知，**Normal Bet 只有在抽到 `BG_Symbol (3)` 的局才可能觸發 Free Game**。

**關於 `Symbol Weight`**

這一欄不是「符號的權重」，而是「**停輪位置**的權重」。程式先依此欄抽出一個輪帶位置，再從該位置往下取連續數格填滿盤面。因此某個符號的實際出現率，同時取決於它在輪帶上出現幾次、以及那些位置各自的權重。

**關於 `Eliminate Wheel Weight`**

這是一張「符號 × 輪」的權重表，與輪帶完全獨立。Cascade 產生空位時，**不是從輪帶接著往上取符號，而是用這張表重新抽樣**。表中同時提供 A、B 兩組，由 `Eliminate Table Weight` 決定該局使用哪一組（見 [2-6](#2-6-eliminate-table-weight)）。

此欄位群在版面上分為 `1 Combo`、`2 Combo`、`3+ Combo` 三個區塊，設計上可讓不同連消次數使用不同的補牌率。

> 目前程式取用的是 `2 Combo` 區塊的設定，三個區塊的數值目前一致。若要區分連消次數，需一併調整程式的取用方式。

### 1-10 Free Game 輪帶表

Free Game 的三組輪帶設定，版面與欄位意義同 [1-9](#1-9-base-game-輪帶表)。

三張表依「當前累積倍率」切換（見 [3-7](#3-7-free-game)），共同特徵是：

- 第 3 輪保證為金框且保證帶倍數
- 第 3 輪不含 Scatter，因此 **FG 內能開出的 Scatter 數量上限比 BG 少一輪**
- 三張表的差異在倍數配置的期望值，用來讓累積倍率越高時、成長速度趨緩

---

## 二、Parameter 工作表的遊戲參數說明

以下逐區塊說明每一組參數控制什麼、以及程式在一局之中「什麼時候」使用它。

### 2-1 Line

定義 20 條固定線。每一列代表一條線，5 個數字依序表示該線在第 1~5 輪各取記分區的第幾列（0 = 上、1 = 中、2 = 下）。

例如 `1, 1, 1, 1, 1` 代表整條中線，`0, 1, 2, 1, 0` 代表一條 V 字線。

程式在每一次判獎時依序檢查這 20 條線，每條線只給一個獎，最後相加。詳見 [3-4](#3-4-判獎規則)。

### 2-2 Table Selection Weight - Base Game

列出 Base Game 的三張輪帶表及其權重。

**每一次 BG spin 的第一個動作**就是用這組權重抽出本局要使用的輪帶表。這一步同時決定了本局後續的輪帶、補牌轉盤與倍數權重都走哪一組設定，是影響手感與 FG 觸發率最上游的參數。

Free Game 沒有對應的區塊，因為 FG 的輪帶表不是抽的，而是依累積倍率切換。

### 2-3 Multiplier Range

金框可能帶有的倍數清單。**這是一張索引表** —— 下方所有 `Multiple Selection Weight` 區塊的欄位順序都對應此清單。

抽倍數的流程固定為：用某一組權重抽出「索引」→ 再用此清單換成實際倍數值。清單的第一項為 `0`，代表「這顆金框沒有倍數」（框存在，但收集不到倍率）。

清單中的非零倍數依序為：`x2`、`x3`、`x5`、`x8`、`x10`、`x15`、`x20`、`x25`、`x50`、`x100`、`x500`、`x1000`。

### 2-4 Used Special Pool Weight

決定「特殊倍數池」是否啟用。

- 欄位為 **記分區內的金框數量**（金框越多，啟用機率越高）
- 每一列對應一張輪帶表
- 分母固定為 10000

**使用邏輯**

1. 開局分配倍數前，先數出記分區的金框數量。
2. 依該數量與本局的輪帶表查出權重，判定本局是否啟用特殊池。
3. 若啟用，在記分區的金框中**等機率挑選 1 顆**，該顆改用 `Multiple Selection Weight - Special Pool` 抽倍數。

要點：

- 特殊池**只在開局分配倍數時判定一次**；Cascade 補進來的金框不會再有機會。
- 一局最多只有 **1 顆**金框吃到特殊池倍數。
- 只有記分區的金框有資格；最上方的預覽列不算入數量，也不會被選中。

### 2-5 Multiple Selection Weight（五組）

五個區塊的欄位皆對應 [2-3](#2-3-multiplier-range) 的倍數清單，列皆對應各張輪帶表。它們的差別只在**什麼位置、什麼時機**的金框會使用哪一組。

| 區塊 | 使用時機 |
| --- | --- |
| `Special Pool` | 開局時命中特殊池的那 1 顆金框 |
| `Before Eliminate` | 開局時、**記分區**、非第 3 輪的金框 |
| `After Eliminate` | 開局時位於**預覽列**的非第 3 輪金框，以及 Cascade 補進來的非第 3 輪金框 |
| `Reel3 Before Eliminate` | 開局時、記分區、**第 3 輪**的金框（限特定輪帶表） |
| `Reel3 After Eliminate` | 開局時位於預覽列的第 3 輪金框，以及 Cascade 補進第 3 輪的金框（限特定輪帶表） |

**「第 3 輪專用」的啟用條件**

只有「第 3 輪整輪為金框」的那些輪帶表（BG 的全金框表，以及三張 FG 表），其第 3 輪才會走 Reel3 專用的兩組權重；其餘輪帶表的第 3 輪仍走一般的 Before／After。

**完整的選擇順序**

```
開局分配（盤面上所有金框，含預覽列，逐格處理）
    ├─ 命中特殊池的那 1 顆 ──────────────► Special Pool
    ├─ 第 3 輪 且 該表為 Reel3 專用表
    │      ├─ 位於記分區 ────────────────► Reel3 Before Eliminate
    │      └─ 位於預覽列 ────────────────► Reel3 After  Eliminate
    └─ 其他
           ├─ 位於記分區 ────────────────► Before Eliminate
           └─ 位於預覽列 ────────────────► After  Eliminate

Cascade 補牌（新補進來的金框）
    ├─ 第 3 輪 且 該表為 Reel3 專用表 ───► Reel3 After Eliminate
    └─ 其他 ─────────────────────────────► After Eliminate
```

> 預覽列（最上方不記分的那一列）雖然是開局產生的，但它必須等掉落後才會參與判獎，因此吃的是 **After Eliminate**，不是 Before。這是看表時最容易誤解的一點。

各區塊最右側另有一個平均倍率欄位，定義為「排除倍數 0 之後的平均倍率」，供設計時參考，程式不讀取。

### 2-6 Eliminate Table Weight

決定該局的 Cascade 使用 `Eliminate Wheel Weight A` 或 `B`，Base Game 與 Free Game 可分開設定。

**每次 spin 開局抽一次，決定本局整個 Cascade 過程使用哪一組，中途不會更換。**

---

## 三、遊戲邏輯

### 3-1 盤面與座標系統

| 項目 | 值 |
| --- | --- |
| 輪數 | 5 |
| 記分列數 | 3 |
| 程式持有列數 | 4（記分 3 列 + 最上方 1 列預覽列） |

```
預覽列   ← 不判獎、不算 Scatter，但金框會先被分配倍數
記分列 1 ┐
記分列 2 ├ 3 × 5：判線與計算 Scatter 都只看這裡
記分列 3 ┘
```

停輪時取輪帶上連續 4 格填入這 4 列；`Line` 表寫的 0／1／2 對應記分列 1～3。

### 3-2 符號與角色

| Symbol | 說明 | 角色 |
| --- | --- | --- |
| `WW` | Wild | 可替代所有可計分符號，本身不帶賠率 |
| `C1` | Scatter | 只計數量、會截斷連線，本身不帶賠率 |
| `M1`~`M5` | 高賠符號 | 可計分 |
| `A`、`K`、`Q`、`J` | 低賠符號 | 可計分 |
| `G1`~`G5`、`GA`、`GK`、`GQ`、`GJ` | 上列可計分符號的金框版本 | 判獎時視為對應的基底符號，額外可帶倍數 |

三項程式衍生的判斷依據：

- **基底符號對照**：金框符號對應回哪一個一般符號（停輪與補牌時寫入盤面用）
- **是否金框**：決定該格是否進入倍數分配
- **是否可計分**：`WW`、`C1` 與所有金框代號皆為否，判獎時據此過濾

**`WW` 不會自然停出。** 六張輪帶表的輪帶與補牌轉盤都不含 `WW`；盤面上的 Wild 只有一個來源 —— 中獎的金框在原位轉成 Wild（見 [3-5](#3-5-cascade-與金框轉-wild)）。

### 3-3 單次 spin 的流程

BG 與 FG 共用同一套流程，差別只在使用哪一組參數。

```
1. 決定本局使用哪一張輪帶表
      BG：依 Table Selection Weight - Base Game 抽選
      FG：依當前累積倍率切換（見 3-7）
2. 依 Eliminate Table Weight 抽出本局使用 A 或 B 組補牌轉盤（本局固定）
3. 依各輪的 Symbol Weight 抽出停輪位置，再依 Symbol ID 展開成 4 × 5 盤面
4. 對盤面上所有金框（含預覽列）分配倍數
      先判定特殊池是否啟用，再依位置與時機選用對應的權重組（見 2-4、2-5）
5. 連消迴圈：
   5-1 依 20 條線判獎
   5-2 若沒有任何獎 → 結束迴圈
   5-3 累加本輪的線獎
   5-4 處理中獎位置：
          金框 → 收集其倍數，該格不消失，改為轉成 Wild
          非金框 → 清空
   5-5 該輪現有符號往下墜，空位依本局的補牌轉盤補入新符號
          新補進來的金框依其位置選用對應權重組抽倍數
          該輪若已有 Scatter，補到 Scatter 會重抽
   5-6 回到 5-1
6. 統計最終盤面記分區的 Scatter 數量
7. 若本次 spin 實際收集到倍數，將累積倍數一次乘上本次 spin 的線獎總和
```

### 3-4 判獎規則

```
對每一條線：
    取第 1 輪在該線位置的符號
        若為 Scatter        → 這條線不算
        若為 Wild           → 對所有可計分符號各試算一次，取賠率最高者
        否則                → 以其基底符號為比對目標
    從第 1 輪往右逐輪比對：
        基底符號相同 或 該格是 Wild → 連線長度 +1
        遇到 Scatter                → 立即中斷
        其他                        → 中斷
    連線長度達 3 以上才有賠率，依 Pay Table 取值後乘上下注倍數
    每條線只取最高的一種算法，不重複計分
```

要點：

- 連線必須**從第 1 輪起算**（左起）。
- 金框在判獎階段已還原為基底符號，因此金框與其基底符號對判線完全等價。
- 20 條線的獎相加即為本輪的線獎總和。

### 3-5 Cascade 與金框轉 Wild

1. 中獎的一般符號移除。
2. 中獎的金框**不移除**：先把它的倍數收集起來，該位置改為 `WW` 留在盤面上，因此不會被視為空位。
3. 該輪剩餘符號往下墜。
4. 仍為空的位置，依本局選定的補牌轉盤重新抽樣補入。
5. 若補進來的是金框，依其所在輪別選用對應的權重組抽倍數。
6. **同一輪不會補出第二顆 Scatter**：該輪若已有 Scatter，補牌抽到 Scatter 會重抽。
7. 補牌後重新判獎，直到不再形成新的中獎組合。

### 3-6 倍數的分配、收集與作用

**分配（開局）**：盤面上每一顆金框都會先被指派一個倍數，可能為 0。指派時依「是否命中特殊池」、「是否在第 3 輪且該表為 Reel3 專用表」、「位於記分區或預覽列」三個條件選用對應的權重組（見 [2-4](#2-4-used-special-pool-weight)、[2-5](#2-5-multiple-selection-weight五組)）。

**收集**：金框先當作基底符號參與判線。**只有該顆金框真的在某次消除中被打中，它的倍數才會被收集**；沒有中獎的金框，倍數不算。

**作用**：單次 spin 內，倍數只是先累加起來，**不會即時乘上獎金**。等到盤面不再形成新的中獎組合之後，才把累積倍數一次乘上本次 spin 的線獎總和。

若本次 spin 完全沒有收集到大於 0 的倍數，則不套用倍數。

### 3-7 Free Game

**觸發**：整局 Cascade 全部結束後，看最終盤面**記分區**的 Scatter 數量。達 3 顆以上即觸發。

| 記分區 Scatter 數 | 免費場次 |
| --- | --- |
| 3 | 12 |
| 4 | 14 |
| 5 | 16 |

單次進入 Free Game 後，**含 retrigger 在內總場次上限為 50 場**。

**輪帶表的切換**：FG 不再抽輪帶表，而是依「當前累積倍率」直接切換。

| 當前累積倍率 | 使用的輪帶表 |
| --- | --- |
| < 10 | `FG_Symbol` |
| < 20 | `FG_Symbol (2)` |
| ≥ 20 | `FG_Symbol (3)` |

**累積倍率的保留**：FG 的累積倍率**跨場保留**，直到整段 Free Game 結束才清除，並且會反過來決定下一場使用哪一張輪帶表。

**Retrigger**：FG 之中若再次達到 Scatter 門檻，依同一張場次表追加場次，但總剩餘場次仍受 50 場上限封頂。retrigger 只增加場次，不會清除已累積的倍率。

> 由於 FG 的三張輪帶表第 3 輪不含 Scatter，FG 內能開出的 Scatter 數量上限比 BG 少一輪。

### 3-8 一局（一次付費 spin）的完整流程

```
1. 計算本局成本：Coin In = 下注倍數 × Base Bet
2. 抽一張 Base Game 卡片（見第四章）
3. 執行一次 BG spin（流程見 3-3）
4. 若最終盤面記分區的 Scatter 達門檻：
       依場次表決定免費場次（上限 50）
       抽一張 Free Game 卡片
       進入 Free Game：
           累積倍率歸零
           每一場：
               依當前累積倍率選擇輪帶表
               執行一次 spin（流程同 3-3，倍數自當前累積值起算）
               累加本場得分，更新累積倍率（跨場保留）
               若本場達 Scatter 門檻 → 追加場次（受 50 場上限）
5. 本局總得分 = BG 得分 + FG 整段得分
6. 依卡片條件決定接受本局，或整局重抽（見 4-3）
```

### 3-9 重要規則整理

1. **倍數不是即時乘的。** 單次 spin 內先累加，等到不能再連消才一次乘上該 spin 的線獎總和。
2. **金框必須中獎才收得到倍數。** 被打中後該格轉成 Wild 留在盤面，不消失、不掉落。
3. **FG 的累積倍率不是每場都會生效。** 只有「本場實際收集到大於 0 的倍數」的那些場次才會套用累積值。
4. **FG 累積倍率跨場保留，且會決定下一場使用哪一張輪帶表。** retrigger 只加場次，不清除累積值。
5. **Scatter 只看整局 Cascade 結束後的最終盤面**，中途出現不算，預覽列不算。
6. **Normal Bet 只有抽到 `BG_Symbol (3)` 的局才可能觸發 Free Game。**
7. **預覽列的金框吃 `After Eliminate`，不是 `Before Eliminate`。**
8. **只有「第 3 輪整輪金框」的那些輪帶表，第 3 輪才走 Reel3 專用的倍數權重。**
9. **Cascade 補牌是用獨立的補牌轉盤重新抽樣**，不是從輪帶接著往上取符號。
10. **`WW` 不會自然停出**，盤面上的 Wild 只來自中獎金框的轉換。

---

## 四、卡片系統說明

### 4-1 用途

卡片系統**不改變盤面的機率設定**，而是在「整局結果」的層級做接受／重抽（rejection sampling），把自然機率重新塑形成目標分布。

它的存在使得下列兩件事可以被直接指定，而不必依賴盤面參數去逼近：

- **單局得分的分布**（哪些得分區間各佔多少比例）
- **FG 觸發率**

### 4-2 卡片的結構

卡片來自 `Multiplier_Weight`，分兩組：

| 卡片組 | 何時抽 | 卡片內容 |
| --- | --- | --- |
| Base Game 卡 | 每一局開始 | 一連串「得分倍率區間」，外加一張 `Free Game` 卡 |
| Free Game 卡 | 觸發 FG 後 | 一連串「得分倍率區間」 |

兩種卡片型別：

| 型別 | 判定方式 |
| --- | --- |
| 區間卡（`range`） | 要求該段得分 ÷ Coin In 落在指定區間內（左開右閉） |
| 免費遊戲卡（`free_game`） | 不看金額，只要求這一局必須觸發 Free Game |

Free Game 卡組沒有 `free_game` 型別的卡片，因為進到 FG 判定時「已觸發 FG」已是既定事實，只需比對金額區間。

### 4-3 單局的判定流程

```
每一局開始：抽一張 Base Game 卡

若抽到 free_game 卡：
    重複執行 BG spin，直到最終盤面達 Scatter 門檻
    再抽一張 Free Game 卡
    重複執行「整段 Free Game」，直到 FG 總得分落在該卡的區間內

若抽到 range 卡：
    執行一次 BG spin
        若觸發了 Free Game        → 不接受，整局重抽
        若 BG 得分不在該卡區間內  → 不接受，整局重抽
        否則                      → 接受

兩種情況都受重抽上限保護；達上限時放棄該局並計入統計，
以便檢查是否有某張卡片實際上抽不出來。
```

要點：

- 卡片系統決定的是「**這一局要長成什麼樣**」，再用重抽把它湊出來。
- 判定用的是含小數的倍率（得分 ÷ Coin In），區間為**左開右閉**。
- **區間卡一旦觸發 FG 就整局作廢重抽** —— 因此 FG 觸發率完全由 `Free Game` 卡的權重決定，與盤面的自然 Scatter 機率無關。
- FG 的重抽是以「整段 Free Game」為單位，不是單場。

### 4-4 與 Multiplier_Weight_Detail 的關係

`Multiplier_Weight_Detail` 是卡片權重的推導來源：先在關閉卡片系統的狀態下取得各得分區間的自然機率，再乘上人工調整係數，正規化後得到寫入 `Multiplier_Weight` 的權重。因此該工作表同時記錄了「自然機率」與「目標機率」兩份數據，可用來檢視每個區間被放大或壓縮了多少。

### 4-5 注意事項

1. **卡片權重是影響 RTP 最直接的參數。** 調整盤面權重會改變自然機率，但最終落點仍由卡片決定；若只調盤面而不同步更新卡片權重，總 RTP 不會依預期改變，只會讓重抽次數上升。
2. **重抽次數是健康度指標。** 若某張卡片的區間在自然機率下極難達成，重抽次數會顯著上升，甚至觸及上限。模擬報表會輸出重抽統計，應一併檢視。
3. **BG 與 FG 的 RTP 分配由兩組卡片各自決定。** 兩份 math file 之所以只差 `Weight_NB_FG`，就是只調整了 FG 卡組的派彩分布。
4. **FG 觸發率由 `Free Game` 卡的權重鎖定。** 若要改變 FG 週期，應調整該卡權重，而非調整輪帶上的 Scatter 分布。

---

<!-- ===== English ===== -->

# Math Document Description — 101014 Pinata Beat 1000

**Scope: Normal Bet only**

| Item | Content |
| --- | --- |
| Game ID | 101014 |
| Math files | `H026197A_Bet2.xlsx` (RTP 92%), `H026197A_Bet1.xlsx` (RTP 94%), `H026197A_Bet300.xlsx` (big bet, RTP 92%) |
| Version | 4.0.0.8 |
| Programs | `simulator.py` + `config_92.js` / `config_94.js` |
| Layout | 5 reels × 3 scoring rows (the program holds 4 rows; the top row does not score) |
| Paylines | 20 fixed lines, left to right |
| Coin In | 100 (Base Bet 100 × Price 1) |
| Bet mode | Normal Bet only |

---

## Table of Contents

- [1. Worksheet Function Introduction](#1-worksheet-function-introduction)
  - [1-1 How the program uses the xlsx parameters](#1-1-how-the-program-uses-the-xlsx-parameters)
  - [1-2 Worksheet overview](#1-2-worksheet-overview)
  - [1-3 Overview](#1-3-overview)
  - [1-4 Description](#1-4-description)
  - [1-5 Parameter](#1-5-parameter)
  - [1-6 Multiplier_Weight](#1-6-multiplier_weight)
  - [1-7 Multiplier_Weight_Detail](#1-7-multiplier_weight_detail)
  - [1-8 OP Jackpot](#1-8-op-jackpot)
  - [1-9 Base Game reel tables](#1-9-base-game-reel-tables)
  - [1-10 Free Game reel tables](#1-10-free-game-reel-tables)
- [2. Game Parameters on the Parameter Worksheet](#2-game-parameters-on-the-parameter-worksheet)
  - [2-1 Line](#2-1-line)
  - [2-2 Table Selection Weight - Base Game](#2-2-table-selection-weight---base-game)
  - [2-3 Multiplier Range](#2-3-multiplier-range)
  - [2-4 Used Special Pool Weight](#2-4-used-special-pool-weight)
  - [2-5 Multiple Selection Weight (five blocks)](#2-5-multiple-selection-weight-five-blocks)
  - [2-6 Eliminate Table Weight](#2-6-eliminate-table-weight)
- [3. Game Logic](#3-game-logic)
  - [3-1 Layout and coordinate system](#3-1-layout-and-coordinate-system)
  - [3-2 Symbols and roles](#3-2-symbols-and-roles)
  - [3-3 Flow of a single spin](#3-3-flow-of-a-single-spin)
  - [3-4 Win evaluation](#3-4-win-evaluation)
  - [3-5 Cascading and golden-framed symbols turning into Wild](#3-5-cascading-and-golden-framed-symbols-turning-into-wild)
  - [3-6 Multiplier assignment, collection and application](#3-6-multiplier-assignment-collection-and-application)
  - [3-7 Free Game](#3-7-free-game)
  - [3-8 Flow of one round (one paid spin)](#3-8-flow-of-one-round-one-paid-spin)
  - [3-9 Key rules summary](#3-9-key-rules-summary)
- [4. Card System](#4-card-system)
  - [4-1 Purpose](#4-1-purpose)
  - [4-2 Card structure](#4-2-card-structure)
  - [4-3 Per-round evaluation flow](#4-3-per-round-evaluation-flow)
  - [4-4 Relationship with Multiplier_Weight_Detail](#4-4-relationship-with-multiplier_weight_detail)
  - [4-5 Notes](#4-5-notes)

---

## 1. Worksheet Function Introduction

### 1-1 How the program uses the xlsx parameters

`simulator.py` uses the parameters in the xlsx to run the simulation. Three points must be understood before mapping worksheet fields to program behaviour:

1. **Weights are relative values only.**
   Every field labelled Weight is a relative weight. It does not need to be a probability and does not need to sum to 100%. When drawing, the program takes a random value within the total of that weight group, then maps it to the corresponding entry in proportion to the weights. **The total of each weight group is that group's denominator**, so raising one entry within a group simultaneously dilutes the others.

2. **A golden-framed symbol is held as two layers of information.**
   The board stores the *base symbol* (for example, the golden-framed `G1` is stored on the board as `M1`). Two separate masks record whether each cell is golden-framed and what multiplier that cell carries.
   Consequently the program never reads the pay values of the `G1`–`GJ` rows in the `Overview` Pay Table; win evaluation always uses the base symbol's pay values. Those 9 rows exist for reference, to confirm that a golden-framed symbol pays the same as its base symbol.

3. **Not every field is used by the program.**
   The symbol-count statistics, ratios and averages on the left side of each worksheet, together with the `Description`, `Multiplier_Weight_Detail` and `OP Jackpot` worksheets, are for design and verification purposes only. Each section below states which fields the program uses.

### 1-2 Worksheet overview

| Worksheet | Provides | Affects | Used by program |
| --- | --- | --- | --- |
| `Overview` | Game specification, RTP breakdown, free-spin settings, symbol pay table | Cost calculation, win evaluation, free-spin count | Yes (partly) |
| `Description` | Text description of the parameter flow | — | No (document only) |
| `Parameter` | Paylines, all weight groups, multiplier list | Table selection, multiplier assignment, cascade fill mode | Yes |
| `Multiplier_Weight` | The two card-weight columns of the card system | Accept / re-draw of a round result | Yes |
| `Multiplier_Weight_Detail` | Derivation of the above weights and the target values | — | No (design only) |
| `OP Jackpot` | Simulation record statistics (spin count, Scatter count) | — | No (verification record) |
| `BG_Symbol`<br>`BG_Symbol (2)`<br>`BG_Symbol (3)` | Three Base Game reel strips and cascade-fill wheels | Base Game initial board and cascade fill | Yes |
| `FG_Symbol`<br>`FG_Symbol (2)`<br>`FG_Symbol (3)` | Three Free Game reel strips and cascade-fill wheels | Free Game initial board and cascade fill | Yes |

Both math files have an identical worksheet structure.

### 1-3 Overview

Provides the game specification and the mathematical target values.

| Block | Content | Used by program |
| --- | --- | --- |
| Model / Version | Model code and version | Yes (written into the output file name) |
| RTP row | Bet basis and the pay-back rates (see below) | `Base Bet` only; the rest are target values |
| Reel # / Visible Window Size | Reel count and scoring row count | Yes (board dimensions) |
| Free Spins Setting | Free-spin count per Scatter count, and the overall cap | Yes (see 3-7) |
| Pay Table | Symbol code, Id and 3 / 4 / 5-of-a-kind pay values | Yes (win evaluation) |

**Fields of the RTP row**

| Field | Meaning |
| --- | --- |
| `Base Bet` | Bet basis |
| `Game RTP` | Pay-back rate of the game itself, the sum of the Base Game and Free Game contributions |
| `Bonus RTP` | Pay-back rate of the fixed jackpot pools (OP Jackpot MINOR + MINI) |
| `Link RTP` | Pay-back rate of the linked progressive jackpots (OP Jackpot GRAND + MAJOR) |
| `Total RTP` | `Game RTP + Bonus RTP + Link RTP`, i.e. the total pay-back including the jackpot |
| `Hit JP Symbol appear rate` | Probability that at least one Hit JP Symbol (the Scatter in this game) appears on the screen per spin, expressed as a weight out of Threshold 10,000,000,000; used by the jackpot module to derive its actual hit probability |

**Coin In calculation**

```
Coin In = bet multiplier x Base Bet
```

All RTP and multiplier statistics are expressed as "total win of the round ÷ Coin In".

> The `Game RTP` of the two math files is 92% and 94% respectively, but their `Link RTP` is 2% and 0% respectively, so **`Total RTP` is identical in both (96%)**.
>
> This mirrors the two OP Jackpot configurations: `JP0100B` funds GRAND 1% + MAJOR 1% (Link 2%), while `JP0100A` sets both to 0% (Link 0%). MINOR 0.8% + MINI 1.2% exist in both configurations, so `Bonus RTP` is fixed at 2%.
>
> The Base Game / Free Game breakdown behind `Game RTP` is recorded on `Multiplier_Weight_Detail` (see [1-7](#1-7-multiplier_weight_detail)), together with the Free Game trigger rate and cycle.
>
> The `Hit JP Symbol appear rate` value is taken from the `SCR` field of the `OP Jackpot` worksheet, which is recorded together with `C1 cnt` and `Spin` from the same simulation run. The recorded `SCR` values are listed below (denominator Threshold = 10,000,000,000):
>
> | Status | Bet Type | SCR (92 version) | SCR (94 version) |
> | --- | --- | --- | --- |
> | Newbie | Normal Bet | 3,368,441,800 | 3,368,441,800 |
> | Newbie | Extra Bet | 3,830,983,800 | 3,830,983,800 |
> | Oldhand | Normal Bet | 3,370,654,300 | 3,371,218,200 |
> | Oldhand | Extra Bet | 3,829,976,500 | 3,830,025,700 |
>
> Both versions share the same simulation record for Newbie, so those values are identical; the Oldhand values come from separate simulations per version and differ slightly.

### 1-4 Description

Lists, in text form, the order in which the parameters are used during the Base Game and Free Game flows. The content matches Section 3 of this document. Document only; not read by the program.

### 1-5 Parameter

The central control panel of the model. Each block is described in [Section 2](#2-game-parameters-on-the-parameter-worksheet).

### 1-6 Multiplier_Weight

The input to the card system. Layout:

| Column | Header | Purpose |
| --- | --- | --- |
| `Range` | Win-multiple range label | Defines the bounds of each card |
| `Weight_NB_BG` | Base Game card weights | One card is drawn at the start of every round |
| `Weight_NB_FG` | Free Game card weights | One card is drawn after Free Game is triggered |

The rows are a series of win-multiple ranges (total win ÷ Coin In, left-open and right-closed). The last row, `Free Game`, is a special card: it does not check an amount, it only requires that the round must trigger Free Game.

The totals of the two columns are each calibrated to the same base value, so a weight can be read directly as the probability of that outcome. The mechanism is described in [Section 4](#4-card-system).

**The only parameter difference between the two math files is the `Weight_NB_FG` column** — that is, the Free Game pay distribution. `Weight_NB_BG`, the entire `Parameter` worksheet and all six reel tables are identical in both files.

### 1-7 Multiplier_Weight_Detail

The worksheet from which the two weight columns of `Multiplier_Weight` are derived. Not read by the program.

| Block | Content |
| --- | --- |
| Threshold | Normalisation base of the weights |
| Coin in | References the Base Bet on `Overview` |
| Target rows | Target RTP, hit rate, Free Game cycle and average multiplier for Normal Bet (the RTP breakdown on `Overview` references these) |
| `Base Game (Normal Bet)` block | Natural-probability simulation results per win range (count, pay, hit rate, average multiplier), the manual adjustment factor, and the calibrated weights |
| `Free Game (Normal Bet)` block | The same, applied to the total win of a Free Game session |
| Comparison columns | Current versus benchmark values, for reference while tuning |

The tuning loop is: run with the card system disabled to obtain the natural probabilities, enter the simulation results, adjust the factors, obtain the calibrated weights, write them into `Multiplier_Weight`, then re-run with the card system enabled to verify.

> The two weight columns of `Multiplier_Weight` were originally spilled from this worksheet by dynamic-array formulas. In this submission version they have been converted to static values, so the two worksheets hold identical values but are no longer linked.

### 1-8 OP Jackpot

Records the spin count, the scoring-area Scatter count and the cumulative Scatter count of each simulation run, for verification. Not read by the program, and contains no jackpot probability or pay parameters.

### 1-9 Base Game reel tables

`BG_Symbol`, `BG_Symbol (2)` and `BG_Symbol (3)` are the three Base Game reel settings. The three worksheets share an identical layout; each defines one reel strip plus one cascade-fill wheel.

| Field group | Content | Used by program |
| --- | --- | --- |
| Leftmost Symbol / Description / R1–R5 / ID | Symbol counts on that table's reel strip and the per-reel totals | No (verification) |
| Normal / Golden Symbol ratio | Ratio of normal to golden-framed symbols | No (verification) |
| Combined statistics | Combined count of a base symbol and its golden-framed version | No (verification) |
| `Symbol` | Reel strip content (text) | No (human readable) |
| `Symbol ID R1~R5` | Reel strip content (codes) | Yes (the actual reel strip) |
| `Symbol Weight R1~R5` | Weight of each reel-strip position | Yes (determines the stop position) |
| `Eliminate Wheel Weight A` | Cascade-fill wheel weights, group A | Yes (cascade fill) |
| `Eliminate Wheel Weight B` | Cascade-fill wheel weights, group B | Yes (cascade fill) |

**Roles of the three tables**

| Table | Role | Characteristics |
| --- | --- | --- |
| `BG_Symbol` | Ordinary round | Golden frames appear on reels 2, 3 and 4 only; the Scatter distribution cannot reach the trigger threshold |
| `BG_Symbol (2)` | Full golden-frame round | Reel 3 is entirely golden-framed and always carries a multiplier; Scatter distribution as above |
| `BG_Symbol (3)` | Free Game trigger round | Scatters are distributed across all five reels; the golden-frame multiplier configuration is zero, so no large multiplier is collected before entering Free Game |

> It follows that in Normal Bet, **Free Game can only be triggered in a round that draws `BG_Symbol (3)`**.

**About `Symbol Weight`**

This column is not the weight of a symbol; it is the weight of a **reel-strip position**. The program first draws a strip position according to this column, then takes the consecutive cells from that position to fill the board. The effective appearance rate of a symbol therefore depends both on how many times it occurs on the strip and on the weights of those positions.

**About `Eliminate Wheel Weight`**

This is a symbol × reel weight table, entirely independent of the reel strip. When cascading creates empty positions, **the program does not continue taking symbols from the reel strip; it draws again from this table**. Groups A and B are both provided, and `Eliminate Table Weight` decides which group the round uses (see [2-6](#2-6-eliminate-table-weight)).

The field group is laid out as three blocks, `1 Combo`, `2 Combo` and `3+ Combo`, so that different cascade counts can use different fill rates.

> The program currently uses the `2 Combo` block; the values of the three blocks are currently identical. Distinguishing by cascade count would also require changing which block the program reads.

### 1-10 Free Game reel tables

`FG_Symbol`, `FG_Symbol (2)` and `FG_Symbol (3)` are the three Free Game reel settings. The layout and field meanings are the same as [1-9](#1-9-base-game-reel-tables).

The three tables are switched according to the current accumulated multiplier (see [3-7](#3-7-free-game)). Their common characteristics are:

- Reel 3 is always golden-framed and always carries a multiplier
- Reel 3 contains no Scatter, so **the maximum number of Scatters obtainable inside Free Game is one reel fewer than in the Base Game**
- The tables differ in the expected value of their multiplier configuration, so that growth slows down as the accumulated multiplier rises

---

## 2. Game Parameters on the Parameter Worksheet

Each block below states what the parameter group controls and at which point in a round the program uses it.

### 2-1 Line

Defines the 20 fixed paylines. Each row is one line; the five numbers state, for reels 1 to 5, which scoring row that line uses (0 = top, 1 = middle, 2 = bottom).

For example, `1, 1, 1, 1, 1` is the straight centre line, and `0, 1, 2, 1, 0` is a V-shaped line.

At each win evaluation the program checks these 20 lines in order. Each line pays only one award, and the awards are then summed. See [3-4](#3-4-win-evaluation).

### 2-2 Table Selection Weight - Base Game

Lists the three Base Game reel tables and their weights.

**The first action of every Base Game spin** is to draw the reel table for that round from this weight group. That single step also determines which reel strip, cascade-fill wheel and multiplier weights the rest of the round will use, which makes it the most upstream parameter affecting both game feel and the Free Game trigger rate.

Free Game has no corresponding block, because Free Game reel tables are not drawn; they are switched by the accumulated multiplier.

### 2-3 Multiplier Range

The list of multipliers a golden-framed symbol may carry. **This is an index table** — the column order of every `Multiple Selection Weight` block below corresponds to this list.

Drawing a multiplier always follows the same sequence: draw an *index* from a weight group, then convert it to the actual multiplier through this list. The first entry of the list is `0`, meaning "this golden-framed symbol carries no multiplier" (the frame exists, but no multiplier can be collected).

The non-zero multipliers of the list, in order, are: `x2`, `x3`, `x5`, `x8`, `x10`, `x15`, `x20`, `x25`, `x50`, `x100`, `x500`, `x1000`.

### 2-4 Used Special Pool Weight

Decides whether the special multiplier pool is activated.

- The columns are the **number of golden-framed symbols in the scoring area** (the more golden frames, the higher the activation chance)
- Each row corresponds to one reel table
- The denominator is fixed at 10000

**Logic**

1. Before multipliers are assigned at the start of a spin, count the golden-framed symbols in the scoring area.
2. Look up the weight by that count and the reel table of the round, and decide whether the special pool activates.
3. If it activates, **one** golden-framed symbol in the scoring area is chosen with equal probability, and that symbol draws its multiplier from `Multiple Selection Weight - Special Pool` instead.

Notes:

- The special pool is evaluated **only once, at the initial multiplier assignment**. Golden-framed symbols added by cascading never get this chance.
- At most **one** golden-framed symbol per round receives a special-pool multiplier.
- Only golden-framed symbols in the scoring area are eligible. Those in the top preview row are neither counted nor selected.

### 2-5 Multiple Selection Weight (five blocks)

The columns of all five blocks correspond to the multiplier list in [2-3](#2-3-multiplier-range), and the rows correspond to the reel tables. They differ only in **which position and which moment** uses which block.

| Block | When it is used |
| --- | --- |
| `Special Pool` | The single golden-framed symbol that hits the special pool at the start of a spin |
| `Before Eliminate` | Golden-framed symbols at the start of a spin, in the **scoring area**, not on reel 3 |
| `After Eliminate` | Golden-framed symbols at the start of a spin located in the **preview row** (not reel 3), and golden-framed symbols added by cascading (not reel 3) |
| `Reel3 Before Eliminate` | Golden-framed symbols at the start of a spin, in the scoring area, on **reel 3** (specific reel tables only) |
| `Reel3 After Eliminate` | Reel-3 golden-framed symbols at the start of a spin located in the preview row, and reel-3 golden-framed symbols added by cascading (specific reel tables only) |

**When the reel-3 blocks apply**

Only reel tables whose third reel is entirely golden-framed (the Base Game full golden-frame table and the three Free Game tables) use the two reel-3 blocks for their third reel. On all other reel tables, reel 3 still uses the ordinary Before / After blocks.

**Full selection order**

```
Initial assignment (every golden-framed symbol on the board, preview row included)
    |- the single symbol that hit the special pool ------> Special Pool
    |- reel 3 AND the table uses the reel-3 blocks
    |      |- in the scoring area --------------------> Reel3 Before Eliminate
    |      +- in the preview row ---------------------> Reel3 After  Eliminate
    +- otherwise
           |- in the scoring area --------------------> Before Eliminate
           +- in the preview row ---------------------> After  Eliminate

Cascade fill (newly added golden-framed symbols)
    |- reel 3 AND the table uses the reel-3 blocks ---> Reel3 After Eliminate
    +- otherwise -------------------------------------> After Eliminate
```

> Although the preview row (the non-scoring top row) is produced at the start of a spin, it can only take part in a win after it has dropped down. It therefore uses **After Eliminate**, not Before Eliminate. This is the single easiest point to misread on these worksheets.

### 2-6 Eliminate Table Weight

Decides whether the cascading of the round uses `Eliminate Wheel Weight A` or `B`. The Base Game and Free Game can be configured separately.

**One draw is made at the start of each spin, and the chosen group is used for the whole cascade sequence of that spin; it is never switched mid-spin.**

---

## 3. Game Logic

### 3-1 Layout and coordinate system

| Item | Value |
| --- | --- |
| Reels | 5 |
| Scoring rows | 3 |
| Rows held by the program | 4 (3 scoring rows plus 1 preview row at the top) |

```
preview row   <- does not pay, is not counted for Scatters,
                 but its golden-framed symbols do receive a multiplier
scoring row 1 -+
scoring row 2  |- 3 x 5: line evaluation and Scatter counting use only this area
scoring row 3 -+
```

At each stop, four consecutive cells of the reel strip fill these four rows. The values 0 / 1 / 2 on the `Line` worksheet refer to scoring rows 1 to 3.

### 3-2 Symbols and roles

| Symbol | Description | Role |
| --- | --- | --- |
| `WW` | Wild | Substitutes for all paying symbols; carries no pay value of its own |
| `C1` | Scatter | Counted only; breaks a line; carries no pay value of its own |
| `M1`–`M5` | High-pay symbols | Paying |
| `A`, `K`, `Q`, `J` | Low-pay symbols | Paying |
| `G1`–`G5`, `GA`, `GK`, `GQ`, `GJ` | Golden-framed versions of the paying symbols above | Treated as the corresponding base symbol for win evaluation; may additionally carry a multiplier |

Three derived lookups are used by the program:

- **Base symbol mapping**: which ordinary symbol a golden-framed symbol maps back to (used when writing the board at stop and at cascade fill)
- **Is golden-framed**: decides whether a cell enters multiplier assignment
- **Is paying**: `WW`, `C1` and every golden-framed code are false; win evaluation filters on this

**`WW` never lands from a reel stop.** Neither the reel strips nor the cascade-fill wheels of the six reel tables contain `WW`. A Wild on the board has exactly one source: a winning golden-framed symbol turning into a Wild in place (see [3-5](#3-5-cascading-and-golden-framed-symbols-turning-into-wild)).

### 3-3 Flow of a single spin

The Base Game and Free Game share the same flow; only the parameter groups differ.

```
1. Determine the reel table for this spin
      Base Game: draw from Table Selection Weight - Base Game
      Free Game: switch by the current accumulated multiplier (see 3-7)
2. Draw cascade-fill group A or B from Eliminate Table Weight (fixed for this spin)
3. Draw a stop position per reel from Symbol Weight, then expand Symbol ID into the 4 x 5 board
4. Assign a multiplier to every golden-framed symbol on the board, preview row included
      First evaluate the special pool, then select the weight block by position and
      timing (see 2-4 and 2-5)
5. Cascade loop:
   5-1 Evaluate the 20 paylines
   5-2 If no award at all -> exit the loop
   5-3 Add this pass's line awards to the running total
   5-4 Process the winning positions:
          golden-framed -> collect its multiplier; the cell does not disappear but
                         turns into a Wild
          otherwise   -> clear the cell
   5-5 Remaining symbols in the reel drop down; empty positions are filled from the
       cascade-fill wheel of this spin
          a newly added golden-framed symbol draws its multiplier from the block
          matching its position
          if the reel already holds a Scatter, drawing a Scatter is re-drawn
   5-6 Return to 5-1
6. Count the Scatters in the scoring area of the final board
7. If any multiplier was actually collected in this spin, apply the accumulated
   multiplier once to the total line award of this spin
```

### 3-4 Win evaluation

```
For each payline:
    Take the symbol on reel 1 at that line's position
        if Scatter  -> the line does not pay
        if Wild     -> evaluate once for every paying symbol and keep the highest pay
        otherwise   -> use its base symbol as the target
    Compare from reel 1 rightwards, reel by reel:
        same base symbol OR the cell is a Wild -> line length + 1
        Scatter                                -> break immediately
        anything else                          -> break
    A line length of 3 or more pays; take the value from the Pay Table and multiply
    by the bet multiplier
    Each line keeps only its single highest-paying interpretation; no double counting
```

Notes:

- A line must start from **reel 1** (leftmost).
- A golden-framed symbol has already been reduced to its base symbol at evaluation time, so it is exactly equivalent to that base symbol for line purposes.
- The sum of the 20 lines is the total line award of that evaluation pass.

### 3-5 Cascading and golden-framed symbols turning into Wild

1. Winning ordinary symbols are removed.
2. A winning golden-framed symbol is **not** removed: its multiplier is collected first, and the position becomes `WW` and stays on the board, so it is not treated as an empty position.
3. Remaining symbols in that reel drop down.
4. Positions that are still empty are filled by drawing again from the cascade-fill wheel selected for this spin.
5. If a newly added symbol is golden-framed, its multiplier is drawn from the block matching its reel.
6. **A second Scatter is never added to the same reel**: if the reel already holds a Scatter, a drawn Scatter is re-drawn.
7. After filling, win evaluation runs again, until no new winning combination is formed.

### 3-6 Multiplier assignment, collection and application

**Assignment (start of a spin)**: every golden-framed symbol on the board is assigned a multiplier, which may be 0. The weight block is selected by three conditions: whether the special pool was hit, whether the symbol is on reel 3 of a table that uses the reel-3 blocks, and whether it sits in the scoring area or the preview row (see [2-4](#2-4-used-special-pool-weight) and [2-5](#2-5-multiple-selection-weight-five-blocks)).

**Collection**: a golden-framed symbol first takes part in line evaluation as its base symbol. **Its multiplier is collected only if that symbol is actually cleared by a win.** A golden-framed symbol that does not win contributes no multiplier.

**Application**: within a single spin the multipliers are only accumulated; they are **not applied immediately**. Once the board forms no further winning combination, the accumulated multiplier is applied once to the total line award of that spin.

If no multiplier greater than 0 was collected during the spin, no multiplier is applied.

### 3-7 Free Game

**Trigger**: after the entire cascade sequence has finished, count the Scatters in the **scoring area** of the final board. Three or more triggers the feature.

| Scatters in the scoring area | Free spins |
| --- | --- |
| 3 | 12 |
| 4 | 14 |
| 5 | 16 |

Once Free Game is entered, the total number of free spins, **including retriggers, is capped at 50**.

**Reel table switching**: Free Game does not draw a reel table; it switches directly by the current accumulated multiplier.

| Current accumulated multiplier | Reel table used |
| --- | --- |
| < 10 | `FG_Symbol` |
| < 20 | `FG_Symbol (2)` |
| >= 20 | `FG_Symbol (3)` |

**Carrying the accumulated multiplier**: the accumulated multiplier is **carried across spins** and is cleared only when the whole Free Game session ends. It also determines which reel table the next spin uses.

**Retrigger**: reaching the Scatter threshold again during Free Game adds spins according to the same table, but the total remaining spins are still capped at 50. A retrigger only adds spins; it never clears the accumulated multiplier.

> Because reel 3 of the three Free Game tables contains no Scatter, the maximum number of Scatters obtainable inside Free Game is one reel fewer than in the Base Game.

### 3-8 Flow of one round (one paid spin)

```
1. Compute the cost: Coin In = bet multiplier x Base Bet
2. Draw one Base Game card (see Section 4)
3. Run one Base Game spin (flow as in 3-3)
4. If the scoring area of the final board reaches the Scatter threshold:
       determine the free-spin count from the table (capped at 50)
       draw one Free Game card
       enter Free Game:
           reset the accumulated multiplier to zero
           for each spin:
               select the reel table by the current accumulated multiplier
               run one spin (flow as in 3-3, multipliers starting from the current
               accumulated value)
               add this spin's win, update the accumulated multiplier (carried over)
               if this spin reaches the Scatter threshold -> add spins (cap 50)
5. Total win of the round = Base Game win + total Free Game win
6. Accept the round, or re-draw the whole round, according to the card condition
   (see 4-3)
```

### 3-9 Key rules summary

1. **Multipliers are not applied immediately.** They accumulate within a spin and are applied once, to that spin's total line award, when no further cascade is possible.
2. **A golden-framed symbol must win before its multiplier is collected.** After being cleared it turns into a Wild and stays on the board; it neither disappears nor drops.
3. **The accumulated multiplier of Free Game does not apply on every spin.** It applies only on those spins that actually collected a multiplier greater than 0.
4. **The accumulated multiplier is carried across Free Game spins and determines the reel table of the next spin.** A retrigger only adds spins; it does not clear the accumulated value.
5. **Scatters are counted only on the final board after the whole cascade sequence has finished** — not while cascading, and never in the preview row.
6. **In Normal Bet, Free Game can only be triggered in a round that draws `BG_Symbol (3)`.**
7. **Golden-framed symbols in the preview row use `After Eliminate`, not `Before Eliminate`.**
8. **Only reel tables whose third reel is entirely golden-framed use the reel-3 multiplier blocks for reel 3.**
9. **Cascade fill draws again from an independent cascade-fill wheel**; it does not continue taking symbols from the reel strip.
10. **`WW` never lands from a reel stop**; every Wild on the board comes from a winning golden-framed symbol.

---

## 4. Card System

### 4-1 Purpose

The card system **does not change the probability settings of the board**. It performs accept / re-draw (rejection sampling) at the level of the whole round result, reshaping the natural probabilities into a target distribution.

Because of it, the following two properties can be specified directly instead of being approached by tuning board parameters:

- **The distribution of the win of a round** (what share each win range takes)
- **The Free Game trigger rate**

### 4-2 Card structure

The cards come from `Multiplier_Weight` and form two groups:

| Card group | When drawn | Contents |
| --- | --- | --- |
| Base Game cards | At the start of every round | A series of win-multiple ranges, plus one `Free Game` card |
| Free Game cards | After Free Game is triggered | A series of win-multiple ranges |

Two card types:

| Type | Condition |
| --- | --- |
| Range card (`range`) | Requires that segment's win ÷ Coin In to fall inside the given range (left-open, right-closed) |
| Free-game card (`free_game`) | Does not check an amount; requires only that the round triggers Free Game |

The Free Game card group contains no `free_game` type card, because by the time the Free Game condition is evaluated the feature has already been triggered; only the amount range needs to be matched.

### 4-3 Per-round evaluation flow

```
At the start of every round: draw one Base Game card

If a free_game card is drawn:
    repeat Base Game spins until the final board reaches the Scatter threshold
    then draw one Free Game card
    repeat the whole Free Game session until its total win falls inside that
    card's range

If a range card is drawn:
    run one Base Game spin
        if Free Game was triggered      -> reject, re-draw the whole round
        if the Base Game win is outside
        the card's range                -> reject, re-draw the whole round
        otherwise                       -> accept

Both cases are protected by a re-draw limit. On reaching the limit the round is
abandoned and counted, so that a card which cannot in practice be satisfied can
be identified.
```

Notes:

- The card system decides **what the round must look like**, and re-drawing is used to produce it.
- Evaluation uses the fractional multiple (win ÷ Coin In); ranges are **left-open and right-closed**.
- **A range card rejects the whole round as soon as Free Game is triggered.** The Free Game trigger rate is therefore determined entirely by the weight of the `Free Game` card, independently of the natural Scatter probability of the board.
- Free Game re-draws operate on the **whole Free Game session**, not on a single free spin.

### 4-4 Relationship with Multiplier_Weight_Detail

`Multiplier_Weight_Detail` is the source from which the card weights are derived: the natural probability of each win range is first obtained with the card system disabled, then multiplied by a manual adjustment factor and normalised to produce the weights written into `Multiplier_Weight`. The worksheet therefore holds both the natural and the target probabilities, which makes it possible to see how much each range has been amplified or compressed.

### 4-5 Notes

1. **The card weights are the most direct parameters affecting RTP.** Adjusting board weights changes the natural probabilities, but the final outcome is still decided by the cards. Changing the board without updating the card weights will not move the total RTP as intended; it will only increase the number of re-draws.
2. **Re-draw counts are a health indicator.** If the range of a card is very hard to reach under the natural probabilities, the re-draw count rises noticeably and may reach the limit. The simulation report outputs re-draw statistics, which should be reviewed together with the RTP.
3. **The RTP split between the Base Game and Free Game is decided by the two card groups separately.** This is why the two math files differ only in `Weight_NB_FG`: only the Free Game pay distribution was adjusted.
4. **The Free Game trigger rate is locked by the weight of the `Free Game` card.** To change the Free Game cycle, adjust that weight rather than the Scatter distribution on the reel strips.
