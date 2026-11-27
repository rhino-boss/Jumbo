<!-- 中英文合併一份（2026-11-26）：前半中文、後半 English；docx 只出英文版 -->

# Math Document Description — 101027 宙斯 2500（Zeus 2500）

**適用範圍：Normal Bet（一般下注）**

| 項目 | 內容 |
| --- | --- |
| Game ID | 101027 |
| Math files | `H0271.xlsx`（共用自然模型）；`H027192.xlsx`（RTP 92%）、`H027194.xlsx`（RTP 94%） |
| Version | 共用模型 `7`；RTP 模型 `7.4.0.0` |
| 對應程式 | `simulator.py` + `config.js`（共用模型）+ `config_92.js` / `config_94.js`（各 RTP 版本） |
| 盤面 | 6 輪 × 5 列固定盤面，共 30 格 |
| 得分方式 | Pay Anywhere：同一個一般符號在整個盤面合計達 8 個以上即得獎；中獎後 Cascade 消除補牌 |
| Coin In | 100（Base Bet 100 × Price 1） |
| 押注模式 | Normal Bet |

---

## 目錄

- [一、工作表說明](#一工作表說明)
  - [1-1 程式如何使用 xlsx 的參數](#1-1-程式如何使用-xlsx-的參數)
  - [1-2 各工作表用途一覽](#1-2-各工作表用途一覽)
  - [1-3 Overview（共用模型）](#1-3-overview共用模型)
  - [1-4 Parameter](#1-4-parameter)
  - [1-5 Symbol 輪帶表](#1-5-symbol-輪帶表)
  - [1-6 Overview（RTP 版本檔）](#1-6-overviewrtp-版本檔)
  - [1-7 Multiplier_Weight](#1-7-multiplier_weight)
  - [1-8 OP Jackpot](#1-8-op-jackpot)
- [二、Parameter 工作表的遊戲參數說明](#二parameter-工作表的遊戲參數說明)
  - [2-1 weight_base_game_table](#2-1-weight_base_game_table)
  - [2-2 free_game_table_setting](#2-2-free_game_table_setting)
  - [2-3 multiplier_level_C2_C3](#2-3-multiplier_level_c2_c3)
  - [2-4 weight_multiplier（C2 倍數）](#2-4-weight_multiplierc2-倍數)
  - [2-5 weight_multiplier_C3（C3 倍數）](#2-5-weight_multiplier_c3c3-倍數)
  - [2-6 weight_C2_to_C3_by_initial_count](#2-6-weight_c2_to_c3_by_initial_count)
  - [2-7 weight_C2_to_C3_by_drop_combo](#2-7-weight_c2_to_c3_by_drop_combo)
- [三、遊戲邏輯](#三遊戲邏輯)
  - [3-1 盤面與座標系統](#3-1-盤面與座標系統)
  - [3-2 符號與角色](#3-2-符號與角色)
  - [3-3 單次 spin 的流程](#3-3-單次-spin-的流程)
  - [3-4 判獎規則](#3-4-判獎規則)
  - [3-5 Cascade 與 C3 升級](#3-5-cascade-與-c3-升級)
  - [3-6 倍數的計算與作用](#3-6-倍數的計算與作用)
  - [3-7 Free Game](#3-7-free-game)
  - [3-8 一局（一次付費 spin）的完整流程](#3-8-一局一次付費-spin的完整流程)
  - [3-9 重要規則整理](#3-9-重要規則整理)
- [四、卡片系統說明](#四卡片系統說明)
  - [4-1 用途](#4-1-用途)
  - [4-2 卡片的結構](#4-2-卡片的結構)
  - [4-3 單局的判定流程](#4-3-單局的判定流程)
  - [4-4 重抽上限與權重校準](#4-4-重抽上限與權重校準)
  - [4-5 注意事項](#4-5-注意事項)

---

## 一、工作表說明

### 1-1 程式如何使用 xlsx 的參數

本遊戲的數學文件拆成兩類工作簿：**共用自然模型**（`H0271.xlsx`：輪帶、停輪權重、賠率、選表、倍數球設定、FG 場次，兩個 RTP 版本共用）與 **RTP 版本檔**（`H027192.xlsx`／`H027194.xlsx`：版本號、卡片權重、區間平均倍率與自然機率、SCR）。理解以下三點，才能正確對照工作表欄位與程式行為：

1. **權重只看相對大小。**
   所有標示為 Weight 的欄位都是相對權重，不需要是機率、也不需要湊成 100%。程式抽樣時是在「該組權重的總和」範圍內取一個隨機值，再依權重比例落到對應項目。**每一組權重的總和就是該組的分母**，因此在同一組內單獨調高某一項，會同時稀釋其他項的機率。例外是 2-6、2-7 的 C2→C3 轉換權重，分母固定為 10,000。

2. **程式讀取的是由 xlsx 轉出的 config。**
   `simulator.py` 載入 `config.js`（對應共用模型）與 `config_92.js`／`config_94.js`（對應 RTP 版本檔）；`config_92.js`／`config_94.js` 以 `base_config` 欄位指向 `config.js`。本文件標示「程式使用 ✅」的欄位，指該資料會進入 config 並影響模擬。

3. **並非所有欄位都會被程式使用。**
   各輪帶表左側的張數統計、`Symbol` 文字欄位等屬於檢核用途，程式不讀取。下方各節逐一標明。

### 1-2 各工作表用途一覽

**共用自然模型 `H0271.xlsx`**

| 工作表 | 提供什麼 | 影響哪一段玩法 | 程式使用 |
| --- | --- | --- | --- |
| `Overview` | 遊戲基本規格、FG 場次設定、符號賠率表 | 成本計算、判獎、Scatter 給獎、FG 場次 | ✅ 部分 |
| `Parameter` | BG 選表權重、FG 場次的輪帶表配置、倍數等級、C2／C3 倍數權重、C2→C3 轉換權重 | 選表、倍數球 | ✅ |
| `BG_Symbol`、`BG_Symbol (2)`、`BG_Symbol (3)` | Base Game 的三組輪帶與停輪權重 | BG 的開局盤面與 Cascade 補牌 | ✅ |
| `FG_Symbol`、`FG_Symbol (2)`、`FG_Symbol (3)` | Free Game 的三組輪帶與停輪權重 | FG 的開局盤面與 Cascade 補牌 | ✅（`FG_Symbol (3)` 場次配置為 0，不會被使用） |

**RTP 版本檔 `H027192.xlsx`／`H027194.xlsx`（結構完全相同）**

| 工作表 | 提供什麼 | 影響哪一段玩法 | 程式使用 |
| --- | --- | --- | --- |
| `Overview` | 版本號、RTP 拆解 | 版本核對、輸出檔名 | ✅ 版本 |
| `Multiplier_Weight` | 卡片系統的 BG／FG 卡片權重 | 單局結果的接受／重抽 | ✅ |
| `Avg_Multi` | 各得分倍率區間的自然平均倍率 | 權重 × 平均倍率 = 各區間的派彩貢獻 | ❌（核對用） |
| `Nature_Prob` | 各得分倍率區間的自然發生機率 | 卡片權重配置的合格性檢核 | ❌（核對用） |
| `OP Jackpot` | SCR（Scatter spin 率） | 彩金模組的機率換算 | ❌（由平台彩金模組使用） |

### 1-3 Overview（共用模型）

| 區塊 | 內容 | 程式使用 |
| --- | --- | --- |
| Model / Version | 模型代號 `H0271` 與共用模型版本 `7` | ✅ 版本核對 |
| Base Bet | 押注基準 100 | ✅ |
| Coin in 表 | Normal Bet 的成本（100 × Price 1） | ✅ |
| Reel # / Visible Window Size | 6 輪，每輪 5 格 | ✅ 建立盤面尺寸 |
| Free Spins Setting | Scatter（C1）數量對應免費場次與 Retrigger 場次；總場次上限 50 | ✅（見 3-7） |
| Pay Table | 各符號的代號、Id，C1 的 4／5／6 顆賠率，一般符號的 8~9／10~11／12+ 顆賠率（以 100 credit 投注為單位） | ✅ 判獎 |

**Pay Table（以 100 credit 投注為單位；÷100 即為倍數）**

| Symbol | Id | 4 | 5 | 6 | 8~9 | 10~11 | 12+ |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C1（Scatter） | 1 | 300 | 500 | 10000 | — | — | — |
| C2（Multiplier） | 2 | — | — | — | — | — | — |
| C3（Super Multiplier） | 3 | — | — | — | — | — | — |
| M1 | 4 | — | — | — | 1000 | 2500 | 5000 |
| M2 | 5 | — | — | — | 250 | 1000 | 2500 |
| M3 | 6 | — | — | — | 200 | 500 | 1500 |
| M4 | 7 | — | — | — | 150 | 200 | 1200 |
| A | 8 | — | — | — | 100 | 150 | 1000 |
| K | 9 | — | — | — | 80 | 120 | 800 |
| Q | 10 | — | — | — | 50 | 100 | 500 |
| J | 11 | — | — | — | 40 | 90 | 400 |
| TE | 12 | — | — | — | 25 | 75 | 200 |

**Coin In 的計算**

```
Coin In = 下注倍數 × Base Bet
```

所有 RTP 與倍率統計都以「該局總得分 ÷ Coin In」為單位。

### 1-4 Parameter

共用模型的控制面板，逐區塊說明見[第二章](#二parameter-工作表的遊戲參數說明)。

### 1-5 Symbol 輪帶表

Base Game 三張、Free Game 三張，版面完全相同。每張表定義一組 6 輪的循環輪帶與停輪權重。

| 欄位群 | 內容 | 程式使用 |
| --- | --- | --- |
| 最左側 `Symbol` / `Description` / `R1~R6` / `ID` | 各符號在每輪輪帶上的張數統計與符號 Id 對照 | ❌ 檢核用 |
| `Symbol`（`L:Q`） | 輪帶內容（文字），每輪 63 或 64 格 | ❌ 給人閱讀 |
| `Symbol ID`（`S:X`） | 輪帶內容（代號） | ✅ 實際輪帶 |
| `Symbol Weight`（`Z:AE`） | 每個輪帶位置的停輪權重 | ✅ 決定停輪位置 |

**關於 `Symbol Weight`**：這一欄不是「符號的權重」，而是「**停輪位置**的權重」。程式先依此欄抽出一個輪帶位置，再從該位置起取連續 5 格填滿該輪。因此某符號的實際出現率，同時取決於它在輪帶上出現幾次、以及那些位置的權重。

**Cascade 補牌**：消除後的空位**沿同一條輪帶**從該輪可視窗頂端之前的位置依序補入（輪帶首尾相接），不使用獨立的補牌權重表。

**六張表的角色分工**

| 表 | C1（Scatter） | C2（倍數球） | 角色 |
| --- | --- | --- | --- |
| `BG_Symbol` | 每輪 1～2 張 | 無 | 一般局；可觸發 FG |
| `BG_Symbol (2)` | 每輪 1～2 張 | 無 | 一般局；可觸發 FG |
| `BG_Symbol (3)` | 無 | 每輪 1 張 | 倍數球局；不會觸發 FG |
| `FG_Symbol` | 每輪 1 張 | 每輪 1～2 張 | FG 場次；可 Retrigger |
| `FG_Symbol (2)` | 無 | 每輪 1～2 張 | FG 場次；不會 Retrigger |
| `FG_Symbol (3)` | 每輪 1 張 | 每輪 1～2 張 | 未使用（場次配置為 0） |

> 由此可知，**Base Game 的倍數球只出現在抽到 `BG_Symbol (3)` 的局**，而 FG 只能由抽到 `BG_Symbol` 或 `BG_Symbol (2)` 的局觸發。
>
> 同一張輪帶的同一輪中，任兩張 C1 的位置距離至少 6 格（含首尾循環），且輪帶前 5 格與最後 5 格不放 C1，因此**同一輪的可視窗最多只會出現 1 顆 C1**；Cascade 補牌時若同一輪已有 C1，不會再補入第二顆。

### 1-6 Overview（RTP 版本檔）

| 區塊 | 內容 | 程式使用 |
| --- | --- | --- |
| Model / Version | 模型代號 `H027192`／`H027194` 與四碼版本 `7.4.0.0` | ✅ 版本核對、輸出檔名 |
| Coin in 表 | Normal Bet 的成本與 Game RTP | 目標值 |
| 彩金列 | `Bonus RTP`、`Link RTP`、`Total RTP`、`Hit JP Symbol appear rate` | 目標值 |
| Total Pay Back 表 | Base Game／Free Game 派彩率、FG 觸發率（Hit%）與週期（Pulls/Hit） | 目標值 |

**兩份 RTP 版本檔的目標值**

| 檔案 | Base Game | Free Game | Game RTP | Bonus RTP | Link RTP | Total RTP | FG 週期 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `H027192.xlsx` | 72% | 20% | 92% | 2% | 2% | 96% | 1/450.83 |
| `H027194.xlsx` | 72% | 22% | 94% | 2% | 0% | 96% | 1/450.83 |

- `Total RTP = Game RTP + Bonus RTP + Link RTP`；Bonus／Link 的參數由平台 OP Jackpot 模組提供，不在本模型內，本模型只提供換算用的 SCR（見 [1-8](#1-8-op-jackpot)）。
- `Hit JP Symbol appear rate` 即 `OP Jackpot` 工作表的 NB SCR，以 Threshold 10,000,000,000 為分母。

### 1-7 Multiplier_Weight

卡片系統的輸入。版面為：

| 欄 | 標題 | 用途 |
| --- | --- | --- |
| A | `Range` | 得分倍率區間標籤 |
| B | `Weight_NB_BG` | Base Game 卡片權重 |
| C | `Weight_NB_FG` | Free Game 卡片權重 |

列由 64 個「得分倍率區間」構成（得分 ÷ Coin In，**左開右閉**），最後一列 `Free Game` 是一張特殊卡：它不看金額，只要求「這一局必須觸發 Free Game」。每一欄的權重總和都是 1,000,000,000，因此權重值可直接理解為「該結果被指定的機率 × 10⁹」。詳細機制見[第四章](#四卡片系統說明)。

| 項目 | 92 版 | 94 版 |
| --- | --- | --- |
| `Weight_NB_BG` | 有權重的區間至 `(1000, 2000]`；`Free Game` 卡 2,218,131 | 與 92 版逐格相同 |
| `Weight_NB_FG` | 有權重的區間 `(20, 25]`～`(10000, 20000]`（FG 平均 90.17 倍） | 同範圍，FG 平均 99.18 倍 |

**兩份 RTP 版本檔的差異只在 `Weight_NB_FG` 一欄**——也就是 FG 的派彩配置。`Weight_NB_BG`、整份共用模型在兩個版本中完全相同。

**`Avg_Multi` 工作表**（與 `Multiplier_Weight` 同列對應，兩個版本內容相同）：

| 欄 | 標題 | 內容 |
| --- | --- | --- |
| A | `Range` | 得分倍率區間標籤 |
| B | `Avg_Multi_NB_BG` | 卡片系統關閉的自然模擬中，落在該區間的 BG 局平均倍率（得分 ÷ Coin In，不含觸發 FG 的局）；`Free Game` 列為觸發局的 BG 平均倍率（只計 BG 得分不超過 2,000 倍的觸發局） |
| C | `Avg_Multi_NB_FG` | 落在該區間的整段 Free Game 平均倍率 |

核對方式：`Σ（Weight_NB_BG × Avg_Multi_NB_BG）÷ 10⁹` = 72.41%（未計重抽上限的理想值，見 [4-4](#4-4-重抽上限與權重校準)）；`Σ（Weight_NB_FG × Avg_Multi_NB_FG）÷ 10⁹` = FG 平均倍數（92 版 90.17、94 版 99.18），乘上 FG 觸發率 1/450.83 即為 Free Game 派彩率。

**`Nature_Prob` 工作表**（同列對應，兩個版本內容相同）：卡片系統關閉時各區間的自然發生機率。`Nature_Prob_NB_BG` 為不含觸發局的每一局落在該區間的機率（各區間合計 100%），`Free Game` 列為自然的 FG 觸發率（每局 0.1682%）；`Nature_Prob_NB_FG` 為整段 Free Game 落在該區間的機率（合計 100%）。自然發生率低於 0.05% 的區間不配置卡片權重。

### 1-8 OP Jackpot

記錄 SCR（Scatter spin 率），供平台彩金模組把「每局的理論觸發率」換算成「每個含 Scatter 的 spin 的判定機率」。

| 欄位 | 內容 |
| --- | --- |
| `Threshold` | 10,000,000,000（SCR 的分母基數） |
| `NB` | SCR = 3,929,397,500（92 版與 94 版相同） |

SCR 的口徑：**含至少 1 顆 C1 的 spin 數 ÷ 付費局數 × 10,000,000,000**（Base Game 與每一場 Free Game 都各算一次 spin），由 10⁸ 局的卡片系統開啟模擬實測。

**彩金機率的換算公式**

```
Pscatter = SCR ÷ 10,000,000,000
           （每一局平均出現「含至少 1 顆 C1 的 spin」的次數）

Ptheory  = 該彩金獎項每一局的理論觸發機率
           （由獎項的固定派彩率與獎額反推；參數在平台彩金模組內）

Phit     = Ptheory ÷ Pscatter
           （每個含 C1 的 spin 實際進行一次彩金判定的條件機率）
```

彩金判定只發生在含 C1 的 spin 上，因此以 `Pscatter` 放大後的 `Phit` 進行判定，長期觸發率即等於 `Ptheory`。

---

## 二、Parameter 工作表的遊戲參數說明

### 2-1 weight_base_game_table

| 工作表 | 權重 |
| --- | ---: |
| `BG_Symbol` | 162,386 |
| `BG_Symbol (2)` | 619,916 |
| `BG_Symbol (3)` | 380,100 |

**每一次 BG spin 的第一個動作**就是用這組權重抽出本局使用的輪帶表。這一步同時決定本局是「可觸發 FG 的一般局」（前兩張）或「倍數球局」（`BG_Symbol (3)`），是影響手感與 FG 觸發率最上游的參數。

### 2-2 free_game_table_setting

| 工作表 | free game（初始場次） | retrigger（追加場次） |
| --- | ---: | ---: |
| `FG_Symbol` | 6 | 2 |
| `FG_Symbol (2)` | 9 | 3 |
| `FG_Symbol (3)` | 0 | 0 |

這不是權重，而是**場次的組成**：

- 觸發 FG 時配發 15 場，由 6 場 `FG_Symbol` 與 9 場 `FG_Symbol (2)` 組成，**打亂順序**後依序執行。
- 每次 Retrigger 追加 5 場，由 2 場 `FG_Symbol` 與 3 場 `FG_Symbol (2)` 組成，打亂後接在現有場次之後。
- 總場次上限 50 場；追加超過上限的部分不配發。

### 2-3 multiplier_level_C2_C3

倍數等級表，共 25 級：

| Level | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17～25 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 倍數 | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 15 | 20 | 25 | 50 | 100 | 250 | 500 | 1000 | 2500 |

**這是一張索引表**——2-4、2-5 的欄位順序都對應此表；C3 升級時也依此表往下一級移動（見 [3-5](#3-5-cascade-與-c3-升級)）。第 17～25 級皆為 2500，因此 C3 升到 2500 後維持 2500。

### 2-4 weight_multiplier（C2 倍數）

每顆 C2 生成時，依**所在輪帶表**的這一列權重抽出倍數（欄位對應 2-3 的等級）。

| 輪帶表 | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 15 | 20 | 25 | 50 | 100 | 250 | 500 | 1000 | 2500 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `BG_Symbol`～`(3)` | 1143 | 961 | 1031 | 1430 | 1822 | 1544 | 935 | 478 | 152 | 205 | 100 | 100 | 75 | 25 | 75 | 75 | 75 |
| `FG_Symbol`、`(2)` | 4340 | 2375 | 1393 | 1151 | 290 | 185 | 128 | 32 | 24 | 16 | 8 | 8 | 20 | 20 | 20 | 20 | 20 |

第 18～25 級（皆為 2500）的權重為 0。

### 2-5 weight_multiplier_C3（C3 倍數）

C2 轉為 C3 時（見 2-6、2-7），改依這一列權重重新抽出 C3 的起始倍數。

| 輪帶表 | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 15 | 20 | 25 | 50 | 100 | 250 以上 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `BG_Symbol`～`(3)` | 1143 | 961 | 1031 | 1430 | 1822 | 1544 | 935 | 239 | 76 | 102 | 50 | 50 | 37 | 0 |
| `FG_Symbol`、`(2)` | 4340 | 2375 | 1393 | 1151 | 290 | 185 | 128 | 16 | 12 | 8 | 4 | 4 | 10 | 250／500／1000 各 10，2500 為 0 |

C3 的起始倍數上限較低，但每次中獎消除都會升一級，可逐級升到 2500。

### 2-6 weight_C2_to_C3_by_initial_count

**開局盤面**上每顆 C2 生成時，依「開局盤面的 C2 總數」選欄，**各自獨立**以「權重 ÷ 10,000」的機率轉為 C3。

| 輪帶表 | 1 顆 | 2 顆 | 3 顆 | 4 顆 | 5 顆 | 6 顆以上 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BG_Symbol`、`BG_Symbol (3)`、`FG_Symbol`、`FG_Symbol (2)` | 4000 | 2600 | 1900 | 1500 | 1300 | 1100 |
| `BG_Symbol (2)` | 800 | 520 | 380 | 300 | 260 | 220 |

### 2-7 weight_C2_to_C3_by_drop_combo

**Cascade 補牌**補入的每顆 C2，依「目前是第幾次連消」選欄，以「權重 ÷ 10,000」的機率轉為 C3。

| 輪帶表 | Combo 1 | 2 | 3 | 4 | 5+ |
| --- | ---: | ---: | ---: | ---: | ---: |
| `BG_Symbol`、`BG_Symbol (3)`、`FG_Symbol`、`FG_Symbol (2)` | 2000 | 1300 | 950 | 750 | 650 |
| `BG_Symbol (2)` | 400 | 260 | 190 | 150 | 130 |

C2 只在**生成當下**判定一次是否轉為 C3；已在盤面上的 C2 不會在後續 Cascade 重新判定，已轉成 C3 也不會再轉回。

---

## 三、遊戲邏輯

### 3-1 盤面與座標系統

| 項目 | 值 |
| --- | --- |
| 輪數 | 6（R1～R6） |
| 每輪格數 | 5（固定） |
| 盤面總格數 | 30 |

停輪時取輪帶上連續 5 格填入該輪；判獎與 C1 計數都以整個 6 × 5 盤面為準。

### 3-2 符號與角色

| Symbol | Id | 說明 | 角色 |
| --- | --- | --- | --- |
| `C1` | 1 | Scatter | 只計數量；最終盤面 4 顆以上觸發 FG、支付 Scatter 獎；不參與 Pay Anywhere、不會被消除 |
| `C2` | 2 | Multiplier（倍數球） | 帶一個固定倍數；不參與 Pay Anywhere、不會被消除 |
| `C3` | 3 | Super Multiplier（升級倍數球） | 帶一個倍數，每次中獎消除後升一級；不參與 Pay Anywhere、不會被消除 |
| `M1`～`M4` | 4～7 | 高分符號 | 可計分 |
| `A`、`K`、`Q`、`J`、`TE` | 8～12 | 低分符號 | 可計分 |

**本作沒有 Wild。** 一般符號只統計自身數量，沒有任何替代符號。

**C3 不在輪帶上。** 輪帶只放 C2；每顆 C2 生成時依 2-6／2-7 判定是否轉為 C3。

### 3-3 單次 spin 的流程

BG 與 FG 共用同一套流程，差別只在使用哪一張輪帶表。

```
1. 決定本 spin 使用哪一張輪帶表
      BG：依 weight_base_game_table 抽選
      FG：依 free_game_table_setting 配置好的場次順序取用（見 3-7）
2. R1～R6 逐輪：依 Symbol Weight 抽出停輪位置，從輪帶取連續 5 格填滿該輪
3. 開局盤面上的每顆 C2：
      依本表的 weight_multiplier 抽出倍數
      依開局 C2 總數查 weight_C2_to_C3_by_initial_count，獨立判定是否轉為 C3；
      轉為 C3 者改依 weight_multiplier_C3 抽出起始倍數
4. 連消迴圈：
   4-1 依 Pay Anywhere 判獎（見 3-4）
   4-2 沒有任何獎 → 結束迴圈
   4-3 累加本回合一般符號得分（尚未乘倍數）
   4-4 盤面上「消除前已存在」的每顆 C3 升一級（見 3-5）
   4-5 中獎的一般符號移除；C1、C2、C3 留在原位
   4-6 各輪符號往下墜，空位沿同一條輪帶依序補入
          補入的 C2 依連消次數查 weight_C2_to_C3_by_drop_combo 判定是否轉為 C3
          同一輪已有 C1 時不再補入第二顆 C1
   4-7 回到 4-1
5. 統計最終盤面的 C1 數量，計算 Scatter 獎
6. 加總最終盤面所有 C2、C3 的倍數，依 3-6 計算本 spin 得分
7. 判定是否觸發／Retrigger Free Game
```

### 3-4 判獎規則

```
對每一種一般符號（M1～M4、A、K、Q、J、TE）：
    統計它在整個 6 × 5 盤面上的數量 N
    N ≥ 8 才有賠率：
        8～9   → 取 Pay Table 的 8~9 欄
        10～11 → 取 10~11 欄
        12+    → 取 12+ 欄
    單一符號得分 = Pay Table 賠率 ÷ 100 × Coin In
本回合得分 = 所有中獎符號的得分相加
```

要點：

- 位置不限、不需相鄰，**只看全盤數量**。
- 同一盤面可同時有多種符號中獎，各自計分後相加。
- C1、C2、C3 不屬於一般符號，不參與判獎。

**Scatter 獎**：所有 Cascade 結束後，依最終盤面 C1 數量支付：4 顆 3 倍、5 顆 5 倍、6 顆 100 倍（以 Coin In 為單位）；3 顆以下不給獎。Scatter 獎**不乘** C2／C3 倍數。

### 3-5 Cascade 與 C3 升級

1. 中獎的一般符號移除；C1、C2、C3 不移除，留在原位。
2. **每發生一次中獎消除，消除前已在盤面上的每顆 C3 往 2-3 等級表的下一級移動**（例如 5 → 6、50 → 100）；同一次消除即使多種符號同時中獎，也只升一級。
3. 該次消除後新補入的 C3 不追溯升級，要等下一次中獎消除才升級。
4. C3 升到 2500 後維持 2500。C2 的倍數不會改變。
5. 各輪剩餘符號往下墜，空位沿同一條輪帶補入。
6. 補牌後重新判獎，直到盤面沒有任何一般符號達 8 個以上。

### 3-6 倍數的計算與作用

設：

- `R` = 本 spin 所有 Cascade 的一般符號得分總和（未乘倍數）
- `M_now` = 本 spin **最終盤面**所有 C2、C3 倍數的**加總**（多顆加總、不相乘）
- `S` = 本 spin 的 Scatter 獎

**Base Game**

```
最終盤面有 C2／C3（M_now > 0）：BG 得分 = R × M_now + S
最終盤面沒有 C2／C3：           BG 得分 = R + S
```

BG 的倍數只作用於當次 spin，不會帶到下一局。

**Free Game（累積倍數）**

設 `M_acc` 為 FG 進場時歸零的累積倍數：

```
若 R > 0 且 M_now > 0：M_acc = M_acc + M_now        （有一般符號得分的 spin 才累積）
若 M_now > 0 且 M_acc > 0：本場得分 = R × M_acc + S  （本場最終盤面有球才套用累積倍數）
否則：                    本場得分 = R + S           （以 1 倍計算；M_acc 保留不歸零）
```

- 倍數在所有 Cascade 結束後，對該 spin 的一般符號得分總和一次套用，不逐回合套用。
- 只有 Scatter 得分（`R = 0`）的 spin，即使最終盤面有球也不累積。
- 有得分但最終盤面沒有任何 C2／C3 的 spin，不論 `M_acc` 已經多少，都以 1 倍計算。
- `M_acc` 跨場保留，直到整段 FG 結束才清除。

### 3-7 Free Game

**觸發**：BG 整局 Cascade 結束後，最終盤面 C1 達 **4 顆以上**即觸發，配發 **15 場**（4、5、6 顆皆同），並另依 3-4 支付 Scatter 獎。

**場次組成**：15 場由 6 場 `FG_Symbol` 與 9 場 `FG_Symbol (2)` 打亂順序組成（見 [2-2](#2-2-free_game_table_setting)）；每一場使用配置好的那張輪帶表。

**Retrigger**：FG 中某一場最終盤面 C1 達 **3 顆以上**，追加 **5 場**（2 場 `FG_Symbol` + 3 場 `FG_Symbol (2)`，打亂後接在現有場次之後）；4 顆以上同時支付 Scatter 獎。最後一場也可 Retrigger。

**場次上限**：含 Retrigger 在內，單次 FG 總場次上限 **50 場**。

**累積倍數**：進入 FG 時歸零，依 3-6 跨場累積，直到整段 FG 結束；Retrigger 只增加場次，不清除累積倍數。

> `FG_Symbol (2)` 不含 C1，因此只有 `FG_Symbol` 的場次可能 Retrigger。

### 3-8 一局（一次付費 spin）的完整流程

```
1. 計算本局成本：Coin In = 下注倍數 × Base Bet
2. 抽一張 Base Game 卡片（見第四章）
3. 執行一次 BG spin（流程見 3-3），得 BG 得分
4. 若最終盤面 C1 達 4 顆：
       配發 15 場（6 場 FG_Symbol + 9 場 FG_Symbol (2)，打亂順序）
       抽一張 Free Game 卡片
       進入 Free Game：
           累積倍數歸零
           每一場：依配置的輪帶表執行 spin → 依 3-6 累積倍數並計算本場得分
                   → 達 3 顆 C1 則追加 5 場（受 50 場上限）
5. 本局總得分 = BG 得分 + FG 整段得分
6. 依卡片條件決定接受本局，或重抽（見 4-3）
```

### 3-9 重要規則整理

1. **Pay Anywhere 只看全盤數量**，同一符號 8 個以上即中獎，不需相鄰、沒有 Wild。
2. **C1、C2、C3 都不會被消除**，留在盤面到該 spin 結束。
3. **倍數加總、不相乘**，並在所有 Cascade 結束後一次套用於一般符號得分；Scatter 獎不乘倍數。
4. **C3 每次中獎消除升一級**，C2 不升級；新補入的 C3 不追溯升級。
5. **C2→C3 只在生成當下判定一次**：開局依 C2 總數、補牌依連消次數。
6. **BG 倍數只作用於當次 spin**；FG 倍數跨場累積，但只在「本場最終盤面有球」時套用。
7. **BG 只有 `BG_Symbol (3)` 會出現倍數球**，且這張表不會觸發 FG。
8. **FG 的 15 場由兩張輪帶表依固定比例組成並打亂順序**，不是逐場抽表。
9. **同一輪最多 1 顆 C1**；Cascade 補牌不會在同一輪補入第二顆。

---

## 四、卡片系統說明

### 4-1 用途

卡片系統**不改變盤面的機率設定**，而是在「整局結果」的層級做接受／重抽（rejection sampling），把自然機率重新塑形成目標分布。它使下列兩件事可以被直接指定：

- **單局得分的分布**（各得分區間各佔多少比例）
- **FG 觸發率**

### 4-2 卡片的結構

卡片來自 `Multiplier_Weight`，分兩組：

| 卡片組 | 何時抽 | 卡片內容 |
| --- | --- | --- |
| Base Game 卡 | 每一局開始 | 64 個得分倍率區間，外加一張 `Free Game` 卡 |
| Free Game 卡 | 觸發 FG 後 | 64 個得分倍率區間（判定整段 FG 的總得分） |

| 型別 | 判定方式 |
| --- | --- |
| 區間卡（`range`） | 要求該段得分 ÷ Coin In 落在指定區間內（左開右閉） |
| 免費遊戲卡（`free_game`） | 不看金額，只要求這一局觸發 Free Game；同時要求觸發局的 BG 得分不超過 Base Game 卡組最高有權重區間的上限（2,000 倍） |

### 4-3 單局的判定流程

```
每一局開始：抽一張 Base Game 卡（同一局重抽期間卡片固定不變）

若抽到 free_game 卡：
    重複執行 BG spin，直到「最終盤面 C1 ≥ 4」且「BG 得分 ≤ 2,000 倍」
    再抽一張 Free Game 卡
    重複執行「整段 Free Game」，直到 FG 總得分落在該卡的區間內

若抽到 range 卡：
    執行一次 BG spin
        若觸發了 Free Game        → 不接受，整局重抽
        若 BG 得分不在該卡區間內  → 不接受，整局重抽
        否則                      → 接受

每次重抽都依自然選表規則重新產生完整結果；重抽上限 10,000 次（見 4-4）。
```

要點：

- 判定用的是含小數的倍率（得分 ÷ Coin In），區間為**左開右閉**。
- **區間卡一旦觸發 FG 就整局作廢重抽**——因此 FG 觸發率由 `Free Game` 卡的權重決定（1/450.83）。
- FG 的重抽以「整段 Free Game」為單位，不是單場。

### 4-4 重抽上限與權重校準

- 每張卡最多重抽 **10,000 次**；達上限時停止，保留最後一次結果並計入統計。
- 卡片抽到區間 `i` 後，每次嘗試命中的機率為該區間的自然機率 `p_i`；10,000 次內命中的機率為 `s_i = 1 − (1 − p_i)^10000`。自然機率較低的高倍 BG 區間 `s_i` 明顯小於 1，未命中時保留的最後一次結果是一次自然結果。
- 因此 `Weight_NB_BG` 的校準已計入此效應：求解時每個區間的平均倍率以「`s_i × 區間平均倍率 + (1 − s_i) × 自然一轉平均倍率`」計算，使**含重抽上限後**的 Base Game 派彩率等於 72%。直接以「權重 × 區間平均倍率」相乘得到的 BG 派彩率會略高於 72%（約 72.41%），差額即為重抽上限造成的落差。
- Free Game 卡各區間的自然機率足夠高（`s_i ≈ 1`），不受此效應影響。
- 卡片系統開啟的模擬驗證（各 10⁸ 局）：92 版 BG 72.08%、94 版 BG 71.99%，皆在統計誤差內。

### 4-5 注意事項

1. **卡片權重是影響 RTP 最直接的參數。** 調整輪帶或選表權重會改變自然機率，但最終落點仍由卡片決定；只調盤面而不同步更新卡片權重，總 RTP 不會依預期改變，只會讓重抽次數上升。
2. **重抽次數是健康度指標。** 模擬報表輸出重抽統計與 `Retry Limit Exceeded` 次數，應一併檢視。
3. **兩個 RTP 版本只差 `Weight_NB_FG`。** 92 版與 94 版的 BG 卡組、FG 觸發率與共用模型完全相同。
4. **FG 觸發率由 `Free Game` 卡的權重鎖定。** 若要改變 FG 週期，應調整該卡權重，而非調整輪帶上的 C1 分布。

---

<!-- ===== English ===== -->

# Math Document Description — 101027 Zeus 2500

**Scope: Normal Bet**

| Item | Content |
| --- | --- |
| Game ID | 101027 |
| Math files | `H0271.xlsx` (shared natural model); `H027192.xlsx` (RTP 92%), `H027194.xlsx` (RTP 94%) |
| Version | Shared model `7`; RTP models `7.4.0.0` |
| Programs | `simulator.py` + `config.js` (shared model) + `config_92.js` / `config_94.js` (RTP versions) |
| Reels | 6 reels × 5 rows, fixed window, 30 positions |
| Win evaluation | Pay Anywhere: a regular symbol pays when it appears 8 or more times anywhere on the screen; winning symbols are removed and refilled (Cascade) |
| Coin In | 100 (Base Bet 100 × Price 1) |
| Bet mode | Normal Bet |

---

## Contents

- [1. Worksheets](#1-worksheets)
  - [1-1 How the program uses the xlsx parameters](#1-1-how-the-program-uses-the-xlsx-parameters)
  - [1-2 Worksheet overview](#1-2-worksheet-overview)
  - [1-3 Overview (shared model)](#1-3-overview-shared-model)
  - [1-4 Parameter](#1-4-parameter)
  - [1-5 Symbol reel sheets](#1-5-symbol-reel-sheets)
  - [1-6 Overview (RTP version files)](#1-6-overview-rtp-version-files)
  - [1-7 Multiplier_Weight](#1-7-multiplier_weight)
  - [1-8 OP Jackpot](#1-8-op-jackpot)
- [2. Game Parameters in the Parameter Sheet](#2-game-parameters-in-the-parameter-sheet)
  - [2-1 weight_base_game_table](#2-1-weight_base_game_table)
  - [2-2 free_game_table_setting](#2-2-free_game_table_setting)
  - [2-3 multiplier_level_C2_C3](#2-3-multiplier_level_c2_c3)
  - [2-4 weight_multiplier (C2 values)](#2-4-weight_multiplier-c2-values)
  - [2-5 weight_multiplier_C3 (C3 values)](#2-5-weight_multiplier_c3-c3-values)
  - [2-6 weight_C2_to_C3_by_initial_count](#2-6-weight_c2_to_c3_by_initial_count)
  - [2-7 weight_C2_to_C3_by_drop_combo](#2-7-weight_c2_to_c3_by_drop_combo)
- [3. Game Logic](#3-game-logic)
  - [3-1 Screen layout](#3-1-screen-layout)
  - [3-2 Symbols and roles](#3-2-symbols-and-roles)
  - [3-3 Flow of a single spin](#3-3-flow-of-a-single-spin)
  - [3-4 Win evaluation](#3-4-win-evaluation)
  - [3-5 Cascade and C3 upgrade](#3-5-cascade-and-c3-upgrade)
  - [3-6 Multiplier calculation](#3-6-multiplier-calculation)
  - [3-7 Free Game](#3-7-free-game)
  - [3-8 Complete flow of one paid game](#3-8-complete-flow-of-one-paid-game)
  - [3-9 Key rules](#3-9-key-rules)
- [4. Card System](#4-card-system)
  - [4-1 Purpose](#4-1-purpose)
  - [4-2 Card structure](#4-2-card-structure)
  - [4-3 Acceptance flow of one game](#4-3-acceptance-flow-of-one-game)
  - [4-4 Retry limit and weight calibration](#4-4-retry-limit-and-weight-calibration)
  - [4-5 Notes](#4-5-notes)

---

## 1. Worksheets

### 1-1 How the program uses the xlsx parameters

The math documents are split into two kinds of workbooks: the **shared natural model** (`H0271.xlsx`: reels, stop weights, paytable, table selection, multiplier symbol settings and Free Game spin counts, shared by both RTP versions) and the **RTP version files** (`H027192.xlsx` / `H027194.xlsx`: version, card weights, range mean multiples and natural probabilities, SCR). Three points are needed to map worksheet fields to program behaviour:

1. **Only relative weight matters.**
   Every field labelled Weight is a relative weight; it need not be a probability or sum to 100%. The program draws a random value within the sum of the group and maps it to an item in proportion to its weight. **The sum of each group is its denominator**, so raising one item also dilutes the others. The exception is the C2→C3 conversion weights in 2-6 and 2-7, whose denominator is fixed at 10,000.

2. **The program reads configs converted from the xlsx.**
   `simulator.py` loads `config.js` (shared model) and `config_92.js` / `config_94.js` (RTP version files); the RTP configs point to `config.js` through their `base_config` field. Fields marked "used ✅" in this document are carried into the configs and affect the simulation.

3. **Not every field is used by the program.**
   The symbol count statistics on the left of each reel sheet and the text `Symbol` columns are for checking only and are not read. Each section below states which fields are used.

### 1-2 Worksheet overview

**Shared natural model `H0271.xlsx`**

| Worksheet | Provides | Affects | Used |
| --- | --- | --- | --- |
| `Overview` | Basic specification, Free Game spin settings, paytable | Cost, win evaluation, Scatter pay, Free Game spins | ✅ partly |
| `Parameter` | Base Game table selection weights, Free Game reel table allocation, multiplier levels, C2/C3 value weights, C2→C3 conversion weights | Table selection, multiplier symbols | ✅ |
| `BG_Symbol`, `BG_Symbol (2)`, `BG_Symbol (3)` | Three Base Game reel sets with stop weights | Base Game initial screen and cascade refill | ✅ |
| `FG_Symbol`, `FG_Symbol (2)`, `FG_Symbol (3)` | Three Free Game reel sets with stop weights | Free Game initial screen and cascade refill | ✅ (`FG_Symbol (3)` is allocated 0 spins and never used) |

**RTP version files `H027192.xlsx` / `H027194.xlsx` (identical structure)**

| Worksheet | Provides | Affects | Used |
| --- | --- | --- | --- |
| `Overview` | Version, RTP breakdown | Version check, output file name | ✅ version |
| `Multiplier_Weight` | Base Game / Free Game card weights | Acceptance / retry of each game result | ✅ |
| `Avg_Multi` | Natural mean multiple of each win-multiple range | Weight × mean multiple = pay contribution of each range | ❌ (for verification) |
| `Nature_Prob` | Natural probability of each win-multiple range | Eligibility check of the card weights | ❌ (for verification) |
| `OP Jackpot` | SCR (Scatter spin rate) | Probability conversion in the jackpot module | ❌ (used by the platform jackpot module) |

### 1-3 Overview (shared model)

| Block | Content | Used |
| --- | --- | --- |
| Model / Version | Model `H0271`, shared model version `7` | ✅ version check |
| Base Bet | Bet base 100 | ✅ |
| Coin in table | Normal Bet cost (100 × Price 1) | ✅ |
| Reel # / Visible Window Size | 6 reels, 5 positions each | ✅ screen size |
| Free Spins Setting | Free spins and retrigger spins by number of Scatters (C1); total limit 50 | ✅ (see 3-7) |
| Pay Table | Symbol code, Id, C1 pays for 4 / 5 / 6, regular symbol pays for 8~9 / 10~11 / 12+ (per 100-credit bet) | ✅ win evaluation |

**Pay Table (per 100-credit bet; divide by 100 for the multiple)**

| Symbol | Id | 4 | 5 | 6 | 8~9 | 10~11 | 12+ |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C1 (Scatter) | 1 | 300 | 500 | 10000 | — | — | — |
| C2 (Multiplier) | 2 | — | — | — | — | — | — |
| C3 (Super Multiplier) | 3 | — | — | — | — | — | — |
| M1 | 4 | — | — | — | 1000 | 2500 | 5000 |
| M2 | 5 | — | — | — | 250 | 1000 | 2500 |
| M3 | 6 | — | — | — | 200 | 500 | 1500 |
| M4 | 7 | — | — | — | 150 | 200 | 1200 |
| A | 8 | — | — | — | 100 | 150 | 1000 |
| K | 9 | — | — | — | 80 | 120 | 800 |
| Q | 10 | — | — | — | 50 | 100 | 500 |
| J | 11 | — | — | — | 40 | 90 | 400 |
| TE | 12 | — | — | — | 25 | 75 | 200 |

**Coin In**

```
Coin In = bet multiplier × Base Bet
```

All RTP and multiple statistics are expressed as "total win of the game ÷ Coin In".

### 1-4 Parameter

The control panel of the shared model; see [Section 2](#2-game-parameters-in-the-parameter-sheet).

### 1-5 Symbol reel sheets

Three Base Game and three Free Game sheets with identical layout. Each sheet defines one set of six circular reel strips with stop weights.

| Field group | Content | Used |
| --- | --- | --- |
| Left `Symbol` / `Description` / `R1~R6` / `ID` | Symbol counts per reel and the symbol Id map | ❌ check only |
| `Symbol` (`L:Q`) | Reel strips (text), 63 or 64 positions per reel | ❌ for reading |
| `Symbol ID` (`S:X`) | Reel strips (codes) | ✅ actual strips |
| `Symbol Weight` (`Z:AE`) | Stop weight of each reel position | ✅ stop position |

**About `Symbol Weight`**: this is the weight of a **stop position**, not of a symbol. The program draws a reel position by this column and fills the reel with the 5 consecutive positions from there. A symbol's actual frequency therefore depends on how often it appears on the strip and on the weights of those positions.

**Cascade refill**: empty positions are refilled **from the same reel strip**, continuing from the positions above the visible window (the strip is circular). No separate refill weight table is used.

**Roles of the six sheets**

| Sheet | C1 (Scatter) | C2 (multiplier symbol) | Role |
| --- | --- | --- | --- |
| `BG_Symbol` | 1–2 per reel | none | Regular game; can trigger Free Game |
| `BG_Symbol (2)` | 1–2 per reel | none | Regular game; can trigger Free Game |
| `BG_Symbol (3)` | none | 1 per reel | Multiplier game; cannot trigger Free Game |
| `FG_Symbol` | 1 per reel | 1–2 per reel | Free Game spins; can retrigger |
| `FG_Symbol (2)` | none | 1–2 per reel | Free Game spins; cannot retrigger |
| `FG_Symbol (3)` | 1 per reel | 1–2 per reel | Not used (allocated 0 spins) |

> Multiplier symbols in the Base Game therefore appear only in games that select `BG_Symbol (3)`, and the Free Game can only be triggered from games that select `BG_Symbol` or `BG_Symbol (2)`.
>
> On any reel of any strip, two C1 are at least 6 positions apart (including wrap-around), and the first and last 5 positions hold no C1, so **at most one C1 can be visible on a reel**; a cascade refill never adds a second C1 to a reel that already shows one.

### 1-6 Overview (RTP version files)

| Block | Content | Used |
| --- | --- | --- |
| Model / Version | Model `H027192` / `H027194`, four-part version `7.4.0.0` | ✅ version check, output file name |
| Coin in table | Normal Bet cost and Game RTP | Target |
| Jackpot row | `Bonus RTP`, `Link RTP`, `Total RTP`, `Hit JP Symbol appear rate` | Target |
| Total Pay Back table | Base Game / Free Game pay back, Free Game trigger rate (Hit%) and cycle (Pulls/Hit) | Target |

**Targets of the two RTP versions**

| File | Base Game | Free Game | Game RTP | Bonus RTP | Link RTP | Total RTP | FG cycle |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `H027192.xlsx` | 72% | 20% | 92% | 2% | 2% | 96% | 1/450.83 |
| `H027194.xlsx` | 72% | 22% | 94% | 2% | 0% | 96% | 1/450.83 |

- `Total RTP = Game RTP + Bonus RTP + Link RTP`. Bonus / Link parameters belong to the platform OP Jackpot module and are not part of this model; this model only provides the SCR for conversion (see [1-8](#1-8-op-jackpot)).
- `Hit JP Symbol appear rate` is the NB SCR of the `OP Jackpot` sheet, expressed over the Threshold 10,000,000,000.

### 1-7 Multiplier_Weight

The input of the card system. Layout:

| Column | Header | Use |
| --- | --- | --- |
| A | `Range` | Win multiple range label |
| B | `Weight_NB_BG` | Base Game card weights |
| C | `Weight_NB_FG` | Free Game card weights |

The rows are 64 win multiple ranges (win ÷ Coin In, **left-open, right-closed**). The last row, `Free Game`, is a special card that ignores the amount and only requires the game to trigger the Free Game. Each column sums to 1,000,000,000, so a weight can be read as "the assigned probability of that result × 10⁹". See [Section 4](#4-card-system).

| Item | 92 version | 94 version |
| --- | --- | --- |
| `Weight_NB_BG` | Weighted ranges up to `(1000, 2000]`; `Free Game` card 2,218,131 | Identical to the 92 version |
| `Weight_NB_FG` | Weighted ranges `(20, 25]` to `(10000, 20000]` (Free Game mean 90.17×) | Same span, Free Game mean 99.18× |

**The two RTP versions differ only in the `Weight_NB_FG` column**, i.e. the Free Game pay distribution. `Weight_NB_BG` and the entire shared model are identical in both versions.

**`Avg_Multi` sheet** (rows correspond to `Multiplier_Weight`; identical in both versions):

| Column | Header | Content |
| --- | --- | --- |
| A | `Range` | Win-multiple range label |
| B | `Avg_Multi_NB_BG` | Mean multiple (win ÷ Coin In) of Base Game games falling in the range in the natural simulation with the card system off, excluding games that trigger the Free Game; the `Free Game` row is the mean Base Game multiple of triggering games whose Base Game win does not exceed 2,000× |
| C | `Avg_Multi_NB_FG` | Mean multiple of the whole Free Game falling in the range |

Check: `Σ(Weight_NB_BG × Avg_Multi_NB_BG) ÷ 10⁹` = 72.41% (the ideal value before the retry limit, see [4-4](#4-4-retry-limit-and-weight-calibration)); `Σ(Weight_NB_FG × Avg_Multi_NB_FG) ÷ 10⁹` = Free Game mean multiple (90.17 for the 92 version, 99.18 for the 94 version); multiplied by the Free Game trigger rate 1/450.83 it gives the Free Game pay back.

**`Nature_Prob` sheet** (rows correspond; identical in both versions): the natural probability of each range with the card system off. `Nature_Prob_NB_BG` is the probability that a game, excluding triggering games, falls in the range (the ranges sum to 100%); the `Free Game` row is the natural Free Game trigger rate (0.1682% per game). `Nature_Prob_NB_FG` is the probability that a whole Free Game falls in the range (sums to 100%). Ranges with a natural probability below 0.05% receive no card weight.

### 1-8 OP Jackpot

Jackpot System Reference: Math Document Description_JP. The OP Jackpot prize levels, start-up pools and contribution rates are shared across all OP Jackpot games; refer to BMM's Certification Test Report "JUMBO.1038.A.02" dated on 4th August 2026 for details of the OP Jackpot Feature RTP % calculations.

Records the SCR (Scatter spin rate) used by the platform jackpot module to convert "the theoretical trigger rate per game" into "the hit probability per spin that contains a Scatter".

| Field | Content |
| --- | --- |
| `Threshold` | 10,000,000,000 (SCR denominator) |
| `NB` | SCR = 3,929,397,500 (same for the 92 and 94 versions) |

SCR definition: **number of spins containing at least one C1 ÷ number of paid games × 10,000,000,000** (the Base Game spin and every Free Game spin each count as one spin), measured from 10⁸ games with the card system on.

**Jackpot probability conversion**

```
Pscatter = SCR ÷ 10,000,000,000
           (average number of spins with at least one C1 per game)

Ptheory  = theoretical trigger probability of a jackpot prize per game
           (derived from the prize's fixed pay back and amount; parameters are in the platform jackpot module)

Phit     = Ptheory ÷ Pscatter
           (conditional probability of a jackpot check on each spin containing C1)
```

Jackpot checks only happen on spins containing C1, so checking with `Phit` (scaled by `Pscatter`) gives a long-run trigger rate equal to `Ptheory`.

---

## 2. Game Parameters in the Parameter Sheet

### 2-1 weight_base_game_table

| Sheet | Weight |
| --- | ---: |
| `BG_Symbol` | 162,386 |
| `BG_Symbol (2)` | 619,916 |
| `BG_Symbol (3)` | 380,100 |

**The first action of every Base Game spin** is to select the reel table with these weights. This decides whether the game is a regular game that can trigger the Free Game (first two tables) or a multiplier game (`BG_Symbol (3)`); it is the most upstream parameter for game feel and Free Game frequency.

### 2-2 free_game_table_setting

| Sheet | free game (initial spins) | retrigger (added spins) |
| --- | ---: | ---: |
| `FG_Symbol` | 6 | 2 |
| `FG_Symbol (2)` | 9 | 3 |
| `FG_Symbol (3)` | 0 | 0 |

These are **spin allocations**, not weights:

- When the Free Game is triggered, 15 spins are awarded: 6 spins on `FG_Symbol` and 9 on `FG_Symbol (2)`, **shuffled** and played in that order.
- Each retrigger adds 5 spins: 2 on `FG_Symbol` and 3 on `FG_Symbol (2)`, shuffled and appended to the remaining spins.
- The total number of spins is limited to 50; spins beyond the limit are not awarded.

### 2-3 multiplier_level_C2_C3

Multiplier level table with 25 levels:

| Level | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17–25 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Multiplier | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 15 | 20 | 25 | 50 | 100 | 250 | 500 | 1000 | 2500 |

**This is an index table**: the columns of 2-4 and 2-5 follow these levels, and a C3 upgrade moves to the next level of this table (see [3-5](#3-5-cascade-and-c3-upgrade)). Levels 17–25 are all 2500, so a C3 that reaches 2500 stays at 2500.

### 2-4 weight_multiplier (C2 values)

When a C2 is generated, its value is drawn with the row of **its reel table** (columns follow the levels of 2-3).

| Reel table | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 15 | 20 | 25 | 50 | 100 | 250 | 500 | 1000 | 2500 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `BG_Symbol` to `(3)` | 1143 | 961 | 1031 | 1430 | 1822 | 1544 | 935 | 478 | 152 | 205 | 100 | 100 | 75 | 25 | 75 | 75 | 75 |
| `FG_Symbol`, `(2)` | 4340 | 2375 | 1393 | 1151 | 290 | 185 | 128 | 32 | 24 | 16 | 8 | 8 | 20 | 20 | 20 | 20 | 20 |

Levels 18–25 (all 2500) have weight 0.

### 2-5 weight_multiplier_C3 (C3 values)

When a C2 converts to a C3 (see 2-6 and 2-7), the C3 starting value is drawn again with this row.

| Reel table | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 15 | 20 | 25 | 50 | 100 | 250 and above |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `BG_Symbol` to `(3)` | 1143 | 961 | 1031 | 1430 | 1822 | 1544 | 935 | 239 | 76 | 102 | 50 | 50 | 37 | 0 |
| `FG_Symbol`, `(2)` | 4340 | 2375 | 1393 | 1151 | 290 | 185 | 128 | 16 | 12 | 8 | 4 | 4 | 10 | 250 / 500 / 1000: 10 each; 2500: 0 |

C3 starting values are capped lower, but each winning cascade upgrades a C3 by one level, up to 2500.

### 2-6 weight_C2_to_C3_by_initial_count

For each C2 on the **initial screen**, the column is selected by the total number of C2 on the initial screen, and each C2 **independently** converts to C3 with probability "weight ÷ 10,000".

| Reel table | 1 | 2 | 3 | 4 | 5 | 6 or more |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BG_Symbol`, `BG_Symbol (3)`, `FG_Symbol`, `FG_Symbol (2)` | 4000 | 2600 | 1900 | 1500 | 1300 | 1100 |
| `BG_Symbol (2)` | 800 | 520 | 380 | 300 | 260 | 220 |

### 2-7 weight_C2_to_C3_by_drop_combo

For each C2 added by a **cascade refill**, the column is selected by the current cascade count, and the C2 converts to C3 with probability "weight ÷ 10,000".

| Reel table | Combo 1 | 2 | 3 | 4 | 5+ |
| --- | ---: | ---: | ---: | ---: | ---: |
| `BG_Symbol`, `BG_Symbol (3)`, `FG_Symbol`, `FG_Symbol (2)` | 2000 | 1300 | 950 | 750 | 650 |
| `BG_Symbol (2)` | 400 | 260 | 190 | 150 | 130 |

A C2 is checked for conversion only **once, when it is generated**. A C2 already on the screen is not checked again in later cascades, and a C3 never converts back.

---

## 3. Game Logic

### 3-1 Screen layout

| Item | Value |
| --- | --- |
| Reels | 6 (R1–R6) |
| Positions per reel | 5 (fixed) |
| Total positions | 30 |

Each reel takes 5 consecutive strip positions from its stop; win evaluation and C1 counting use the whole 6 × 5 screen.

### 3-2 Symbols and roles

| Symbol | Id | Description | Role |
| --- | --- | --- | --- |
| `C1` | 1 | Scatter | Counted only; 4 or more on the final screen trigger the Free Game and pay a Scatter award; not part of Pay Anywhere and never removed |
| `C2` | 2 | Multiplier | Carries a fixed multiplier; not part of Pay Anywhere and never removed |
| `C3` | 3 | Super Multiplier | Carries a multiplier that is upgraded one level after each winning cascade; not part of Pay Anywhere and never removed |
| `M1`–`M4` | 4–7 | High symbols | Pay |
| `A`, `K`, `Q`, `J`, `TE` | 8–12 | Low symbols | Pay |

**There is no Wild.** A regular symbol is counted on its own; no symbol substitutes for it.

**C3 is not on the reels.** The strips only hold C2; each generated C2 is checked for conversion to C3 by 2-6 / 2-7.

### 3-3 Flow of a single spin

Base Game and Free Game share the same flow; only the reel table differs.

```
1. Decide the reel table of this spin
      Base Game: drawn by weight_base_game_table
      Free Game: taken from the spin order allocated by free_game_table_setting (see 3-7)
2. For R1–R6: draw a stop position by Symbol Weight and fill the reel with 5 consecutive positions
3. For each C2 on the initial screen:
      draw its value by the table's weight_multiplier
      look up weight_C2_to_C3_by_initial_count by the initial C2 total and check conversion independently;
      a converted C3 draws its starting value by weight_multiplier_C3
4. Cascade loop:
   4-1 Evaluate Pay Anywhere wins (see 3-4)
   4-2 No win → exit the loop
   4-3 Add this round's regular symbol win (before multiplier)
   4-4 Upgrade every C3 that was on the screen before this removal by one level (see 3-5)
   4-5 Remove winning regular symbols; C1, C2 and C3 stay in place
   4-6 Symbols fall; empty positions are refilled from the same strip
          a refilled C2 is checked by weight_C2_to_C3_by_drop_combo using the cascade count
          no second C1 is refilled into a reel that already shows one
   4-7 Back to 4-1
5. Count C1 on the final screen and calculate the Scatter award
6. Sum the multipliers of all C2 and C3 on the final screen and calculate the spin win by 3-6
7. Check Free Game trigger / retrigger
```

### 3-4 Win evaluation

```
For each regular symbol (M1–M4, A, K, Q, J, TE):
    count its number N on the whole 6 × 5 screen
    pays only when N ≥ 8:
        8–9   → column 8~9 of the Pay Table
        10–11 → column 10~11
        12+   → column 12+
    symbol win = Pay Table value ÷ 100 × Coin In
Round win = sum of all winning symbols
```

Key points:

- Position does not matter and symbols need not be adjacent; **only the screen-wide count matters**.
- Several symbols can win on the same screen; each is paid and the wins are added.
- C1, C2 and C3 are not regular symbols and do not take part in win evaluation.

**Scatter award**: after all cascades, the final number of C1 pays 3× (4 C1), 5× (5 C1) or 100× (6 C1) Coin In; 3 or fewer pay nothing. The Scatter award is **not multiplied** by C2 / C3.

### 3-5 Cascade and C3 upgrade

1. Winning regular symbols are removed; C1, C2 and C3 are not removed and stay in place.
2. **On each winning removal, every C3 already on the screen before the removal moves to the next level of the 2-3 table** (e.g. 5 → 6, 50 → 100); a removal with several winning symbols still counts as one upgrade.
3. A C3 that drops in after a removal is not upgraded retroactively; it waits for the next winning removal.
4. A C3 that reaches 2500 stays at 2500. C2 values never change.
5. The remaining symbols fall and the empty positions are refilled from the same strip.
6. Wins are evaluated again after the refill until no regular symbol reaches 8.

### 3-6 Multiplier calculation

Let:

- `R` = total regular symbol win of all cascades in the spin (before multiplier)
- `M_now` = **sum** of all C2 and C3 values on the **final screen** of the spin (added, not multiplied)
- `S` = Scatter award of the spin

**Base Game**

```
C2 / C3 on the final screen (M_now > 0): Base Game win = R × M_now + S
No C2 / C3 on the final screen:          Base Game win = R + S
```

The Base Game multiplier applies to that spin only and is not carried to the next game.

**Free Game (accumulated multiplier)**

Let `M_acc` be the accumulated multiplier, reset to 0 when the Free Game starts:

```
If R > 0 and M_now > 0:     M_acc = M_acc + M_now       (accumulates only on spins with a regular win)
If M_now > 0 and M_acc > 0: spin win = R × M_acc + S    (applies only when this spin ends with a multiplier symbol)
Otherwise:                  spin win = R + S            (paid at 1×; M_acc is kept, not reset)
```

- The multiplier is applied once to the spin's total regular win after all cascades, not round by round.
- A spin with only a Scatter award (`R = 0`) does not accumulate, even if its final screen shows multiplier symbols.
- A winning spin whose final screen has no C2 / C3 is paid at 1× regardless of `M_acc`.
- `M_acc` carries over between spins and is cleared only when the whole Free Game ends.

### 3-7 Free Game

**Trigger**: after all Base Game cascades, **4 or more** C1 on the final screen trigger the Free Game with **15 spins** (same for 4, 5 and 6 C1), plus the Scatter award of 3-4.

**Spin allocation**: the 15 spins consist of 6 `FG_Symbol` spins and 9 `FG_Symbol (2)` spins in shuffled order (see [2-2](#2-2-free_game_table_setting)); each spin uses its allocated reel table.

**Retrigger**: when a Free Game spin ends with **3 or more** C1, **5 spins** are added (2 `FG_Symbol` + 3 `FG_Symbol (2)`, shuffled and appended); 4 or more C1 also pay the Scatter award. The last spin can retrigger.

**Spin limit**: at most **50 spins** per Free Game, including retriggers.

**Accumulated multiplier**: reset to 0 when the Free Game starts and accumulated by 3-6 until the Free Game ends; a retrigger only adds spins and does not clear the multiplier.

> `FG_Symbol (2)` holds no C1, so only `FG_Symbol` spins can retrigger.

### 3-8 Complete flow of one paid game

```
1. Cost: Coin In = bet multiplier × Base Bet
2. Draw a Base Game card (see Section 4)
3. Play one Base Game spin (flow in 3-3) and get the Base Game win
4. If the final screen has 4 or more C1:
       award 15 spins (6 FG_Symbol + 9 FG_Symbol (2), shuffled)
       draw a Free Game card
       play the Free Game:
           accumulated multiplier = 0
           each spin: play on its allocated table → accumulate and pay by 3-6
                      → 3 or more C1 add 5 spins (limited to 50)
5. Total game win = Base Game win + total Free Game win
6. Accept the game or retry according to the card (see 4-3)
```

### 3-9 Key rules

1. **Pay Anywhere only counts screen-wide**; 8 or more of a symbol pay, with no adjacency and no Wild.
2. **C1, C2 and C3 are never removed** and stay until the spin ends.
3. **Multipliers are added, not multiplied**, and applied once to the regular win after all cascades; the Scatter award is not multiplied.
4. **A C3 is upgraded one level per winning removal**; C2 is never upgraded; a newly dropped C3 is not upgraded retroactively.
5. **C2→C3 conversion is checked once at generation**: by the initial C2 total on the initial screen, by the cascade count on refill.
6. **The Base Game multiplier applies to that spin only**; the Free Game multiplier accumulates but applies only when the spin's final screen shows a multiplier symbol.
7. **In the Base Game only `BG_Symbol (3)` shows multiplier symbols**, and that table cannot trigger the Free Game.
8. **The 15 Free Game spins use two reel tables in a fixed proportion, shuffled**, instead of a per-spin table draw.
9. **At most one C1 per reel**; a cascade refill never adds a second one.

---

## 4. Card System

### 4-1 Purpose

The card system **does not change the reel probabilities**. It accepts or retries (rejection sampling) at the level of the whole game result, reshaping the natural distribution into the target distribution. It allows two things to be set directly:

- **the distribution of the game win** (the share of each win range)
- **the Free Game trigger rate**

### 4-2 Card structure

Cards come from `Multiplier_Weight` in two groups:

| Card group | Drawn when | Content |
| --- | --- | --- |
| Base Game cards | At the start of every game | 64 win multiple ranges plus one `Free Game` card |
| Free Game cards | After the Free Game is triggered | 64 win multiple ranges (applied to the total Free Game win) |

| Type | Condition |
| --- | --- |
| Range card (`range`) | The win ÷ Coin In must fall in the range (left-open, right-closed) |
| Free Game card (`free_game`) | Ignores the amount and requires the game to trigger the Free Game; the Base Game win of the triggering spin must also not exceed the upper bound of the highest weighted Base Game range (2,000×) |

### 4-3 Acceptance flow of one game

```
Start of each game: draw one Base Game card (the card stays fixed during retries)

If a free_game card is drawn:
    repeat the Base Game spin until "final C1 ≥ 4" and "Base Game win ≤ 2,000×"
    draw one Free Game card
    repeat the whole Free Game until its total win falls in the card's range

If a range card is drawn:
    play one Base Game spin
        Free Game triggered             → reject and retry the whole game
        Base Game win outside the range → reject and retry the whole game
        otherwise                       → accept

Every retry regenerates a complete result with the natural table selection; the retry limit is 10,000 (see 4-4).
```

Key points:

- The check uses the exact multiple (win ÷ Coin In); ranges are **left-open, right-closed**.
- **A range card that triggers the Free Game is always rejected**, so the Free Game trigger rate is set by the weight of the `Free Game` card (1/450.83).
- Free Game retries are done for the whole Free Game, not per spin.

### 4-4 Retry limit and weight calibration

- Each card is retried at most **10,000 times**; at the limit, the last result is kept and counted in the statistics.
- For a card on range `i`, each attempt hits with the range's natural probability `p_i`, so the chance of hitting within 10,000 attempts is `s_i = 1 − (1 − p_i)^10000`. For high-multiple Base Game ranges with low natural probability, `s_i` is clearly below 1, and the result kept on a miss is a natural result.
- The calibration of `Weight_NB_BG` therefore includes this effect: the mean multiple of each range is taken as "`s_i` × range mean multiple + (1 − `s_i`) × natural mean multiple of one spin", so that the Base Game pay back **including the retry limit** equals 72%. Multiplying weights by range mean multiples directly gives a Base Game pay back slightly above 72% (about 72.41%); the difference is the effect of the retry limit.
- The Free Game card ranges have sufficiently high natural probabilities (`s_i ≈ 1`) and are not affected.
- Simulation with the card system on (10⁸ games each): Base Game 72.08% (92 version) and 71.99% (94 version), both within statistical error.

### 4-5 Notes

1. **Card weights are the most direct RTP control.** Changing reels or table selection changes the natural probabilities, but the final distribution is still decided by the cards; changing the screen settings without updating the card weights does not move the total RTP as expected and only raises the retry count.
2. **The retry count is a health indicator.** The simulation report outputs retry statistics and the `Retry Limit Exceeded` count; review them together.
3. **The two RTP versions differ only in `Weight_NB_FG`.** The Base Game cards, the Free Game trigger rate and the shared model are identical for 92 and 94.
4. **The Free Game trigger rate is fixed by the weight of the `Free Game` card.** To change the Free Game cycle, adjust that weight rather than the C1 distribution on the reels.
