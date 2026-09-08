# Math Document Description — 101016 雷神爆金1000（Thunder Boost 1000）

**適用範圍：Normal Bet（一般下注）**

| 項目 | 內容 |
| --- | --- |
| Game ID | 101016 |
| Math files | `H0281.xlsx`（共用自然模型）；`H028188B.xlsx`（RTP 88%）、`H028190B.xlsx`（RTP 90%）、`H028192A.xlsx`（RTP 92%）、`H028194A.xlsx`（RTP 94%）；`H028192A_Bet100.xlsx`、`H028188B_Bet100.xlsx`（單注 > $100 的獨立模型） |
| Version | 共用模型 `3`；RTP 模型 `3.5.0.0`（含 Bet100） |
| 對應程式 | `Simulator.py` + `config.js`（共用模型）+ `config_88B.js` / `config_90B.js` / `config_92A.js` / `config_94A.js` / `config_92A_Bet100.js` / `config_88B_Bet100.js`（各 RTP 版本） |
| 盤面 | 6 輪 Megaways；主盤面每輪最高 5 列；第 2～5 輪上方各 1 格 Extra Reel（有效視窗 5-6-6-6-6-5） |
| 得分方式 | Way Game（2,025–32,400 Ways），左起連續相鄰輪；中獎後 Cascade 消除補牌 |
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
  - [1-6 Performance Wheel](#1-6-performance-wheel)
  - [1-7 Overview（RTP 版本檔）](#1-7-overviewrtp-版本檔)
  - [1-8 Multiplier_Weight](#1-8-multiplier_weight)
  - [1-9 Detail 與 Detail_Newbie](#1-9-detail-與-detail_newbie)
  - [1-10 OP Jackpot](#1-10-op-jackpot)
- [二、Parameter 工作表的遊戲參數說明](#二parameter-工作表的遊戲參數說明)
  - [2-1 Table Selection Weight - Base Game](#2-1-table-selection-weight---base-game)
  - [2-2 Table Selection Weight - Free Game](#2-2-table-selection-weight---free-game)
  - [2-3 Table Selection Weight - Retrigger](#2-3-table-selection-weight---retrigger)
- [三、遊戲邏輯](#三遊戲邏輯)
  - [3-1 盤面與座標系統](#3-1-盤面與座標系統)
  - [3-2 符號與角色](#3-2-符號與角色)
  - [3-3 單次 spin 的流程](#3-3-單次-spin-的流程)
  - [3-4 判獎規則](#3-4-判獎規則)
  - [3-5 Cascade 與金框轉 Wild](#3-5-cascade-與金框轉-wild)
  - [3-6 M1 倍數的累積與作用](#3-6-m1-倍數的累積與作用)
  - [3-7 Free Game](#3-7-free-game)
  - [3-8 一局（一次付費 spin）的完整流程](#3-8-一局一次付費-spin的完整流程)
  - [3-9 重要規則整理](#3-9-重要規則整理)
- [四、卡片系統說明](#四卡片系統說明)
  - [4-1 用途](#4-1-用途)
  - [4-2 卡片的結構](#4-2-卡片的結構)
  - [4-3 單局的判定流程](#4-3-單局的判定流程)
  - [4-4 與 Detail 工作表的關係](#4-4-與-detail-工作表的關係)
  - [4-5 注意事項](#4-5-注意事項)

---

## 一、工作表說明

### 1-1 程式如何使用 xlsx 的參數

本遊戲的數學文件拆成兩類工作簿：**共用自然模型**（`H0281.xlsx`：輪帶、賠率、版型、掉落、FG 場次等，所有 RTP 版本共用）與 **RTP 版本檔**（`H0281<RTP><版型>.xlsx`：版本號、卡片權重、SCR）。理解以下四點，才能正確對照工作表欄位與程式行為：

1. **權重只看相對大小。**
   所有標示為 Weight 的欄位都是相對權重，不需要是機率、也不需要湊成 100%。程式抽樣時是在「該組權重的總和」範圍內取一個隨機值，再依權重比例落到對應項目。**每一組權重的總和就是該組的分母**，因此在同一組內單獨調高某一項，會同時稀釋其他項的機率。

2. **程式讀取的是由 xlsx 轉出的 config。**
   `Simulator.py` 與展示頁載入 `config.js`（對應共用模型）與 `config_<RTP><版型>.js`（對應 RTP 版本檔）。xlsx 與 config 之間依固定映射轉換（映射見專案 `Source/xlsx_config_usage_mapping.md`）；本文件標示「程式使用 ✅」的欄位，指該資料會進入 config 並影響模擬。`OP Jackpot` 工作表的 SCR 是唯一由模擬器直接讀取 xlsx 的欄位（僅在啟用彩金模擬時）。

3. **金框符號在使用時被拆成兩層資訊。**
   金框符號的代號（Id 13～23）等於「基底符號 Id + 11」；判獎一律使用基底符號的賠率，金框身分只決定「中獎後該格轉為 Wild」的行為。Mystery 符號（Id 24；金框版 25）在盤面停定後整盤轉換為當局抽出的目標符號。

4. **並非所有欄位都會被程式使用。**
   各工作表左側的張數統計、佔比、平均值等欄位，以及 `Detail`／`Detail_Newbie`、Performance Wheel 等工作表，屬於設計與檢核用途，程式不讀取。下方各節逐一標明。

### 1-2 各工作表用途一覽

**共用自然模型 `H0281.xlsx`**

| 工作表 | 提供什麼 | 影響哪一段玩法 | 程式使用 |
| --- | --- | --- | --- |
| `Overview` | 遊戲基本規格、FG 場次設定、符號賠率表 | 成本計算、判獎、進入 FG 的場次 | ✅ 部分 |
| `Parameter` | 三組輪帶表選擇權重 | 每次 spin 的開局選表 | ✅ |
| `BG_Symbol`、`BG_Symbol (2)` | Base Game 的兩組輪帶＋版型／轉換／掉落權重 | BG 的開局盤面與 Cascade 補牌 | ✅ |
| `FG_Symbol`、`FG_Symbol (2)`、`FG_Symbol (3)` | Free Game 的三組輪帶＋版型／轉換／掉落權重 | FG 的開局盤面與 Cascade 補牌 | ✅ |
| `BG_Performance Wheel`、`FG_Performance Wheel` | 表演用轉輪參考 | — | ❌ 表演參考 |

**RTP 版本檔 `H0281<RTP><版型>.xlsx`（四份＋兩份 `_Bet100`，結構完全相同）**

| 工作表 | 提供什麼 | 影響哪一段玩法 | 程式使用 |
| --- | --- | --- | --- |
| `Overview` | 版本號、各押注型態的 RTP 拆解 | 版本核對、輸出檔名 | ✅ 版本 |
| `Multiplier_Weight` | 卡片系統的各組卡片權重 | 單局結果的接受／重抽 | ✅ |
| `Detail`、`Detail_Newbie` | 卡片權重的推導過程（自然分布＋校準係數） | — | ❌ 設計用 |
| `OP Jackpot` | SCR（Scatter spin 率）紀錄 | 彩金模組的機率換算 | ✅ 彩金模擬時 |

### 1-3 Overview（共用模型）

提供遊戲的基本規格。

| 區塊 | 內容 | 程式使用 |
| --- | --- | --- |
| Model / Version | 模型代號 `H0281` 與共用模型版本（單一整數） | ✅ 版本核對 |
| Base Bet / Multiway | 押注基準 100 與最大 Ways 數 32,400 | ✅ |
| Coin in 表 | 各押注型態的成本與倍數 | ✅ Normal Bet 列 |
| Reel # / Visible Window Size | 6 輪；有效視窗 5-6-6-6-6-5（第 2～5 輪含 Extra Reel 的 1 格） | ✅ 建立盤面尺寸 |
| Free Spins Setting | Scatter 數量對應免費場次：4 顆 10 場，之後每多 1 顆 +2 場；總場次上限 50 | ✅（見 3-7） |
| Pay Table | 各符號的代號、Id 與 3／4／5／6 連的賠率（以 100 credit 投注為單位） | ✅ 判獎 |

**Coin In 的計算**

```
Coin In = 下注倍數 × Base Bet
```

所有 RTP 與倍率統計都以「該局總得分 ÷ Coin In」為單位。Pay Table 的值以 100 credit 投注為單位，即「值 ÷ 100 = 每 1 Way 的下注倍數賠率」。

### 1-4 Parameter

共用模型的選表控制面板，只有三組權重，逐區塊說明見[第二章](#二parameter-工作表的遊戲參數說明)。

### 1-5 Symbol 輪帶表

Base Game 兩張、Free Game 三張，版面完全相同。每張表各自定義「一組輪帶＋該表專屬的版型／轉換／掉落權重」。

| 欄位群 | 內容 | 程式使用 |
| --- | --- | --- |
| 最左側 `Symbol` / `Description` / `R1~R7` / `ID`（A4:J29） | 符號對照表（名稱 ↔ Id）與各輪張數統計 | ✅ 對照表；統計欄 ❌ 檢核用 |
| `Symbol`（M4:S203） | 輪帶內容（文字），7 輪 × 200 格 | ❌ 給人閱讀 |
| `Symbol ID`（U4:AA203） | 輪帶內容（代號），由符號對照表換算 | ✅ 實際輪帶 |
| `Symbol Weight`（AC4:AI203） | 每個輪帶位置的停輪權重 | ✅ 決定停輪位置 |
| `MegaWay`（C33:H47） | 第 1～6 輪 × 15 種大型符號版型權重 | ✅ 每輪的符號尺寸組合 |
| `MY`（C51:C63） | Mystery 轉換目標的 13 個權重（索引即符號 Id：0=Wild、1=Scatter、2～12=M1～M11） | ✅ 每局抽一次轉換目標 |
| `Post Scatter`（B67:C74） | 盤面停定後補入的 Scatter 顆數（0～7）權重 | ✅ Scatter 產生 |
| `Drop1`～`Drop5`（AL4:AR145） | Cascade 補牌的符號權重，7 輪 × 26 符號 × 5 段 | ✅ Cascade 補牌 |

**關於 `Symbol Weight`**：這一欄不是「符號的權重」，而是「**停輪位置**的權重」。程式先依此欄抽出一個輪帶位置，再從該位置起依 MegaWay 版型往下取連續數格填滿該輪。因此某符號的實際出現率同時取決於它在輪帶上出現幾次、那些位置的權重、以及版型的尺寸分配。

**關於 `Drop1`～`Drop5`**：Cascade 產生空位時，**不是從輪帶接著往上取符號，而是用這張權重表重新抽樣**；五段對應不同的連消段數。Scatter 不放在初始輪帶上，只能由 Post Scatter 與 Drop 補入。

**兩張 BG 表／三張 FG 表的差異**只在權重配置（金框比例、倍數配置、Scatter 補入率），版面與欄位意義完全相同。

### 1-6 Performance Wheel

表演端參考用的轉輪整理，程式不讀取，不影響任何機率。

### 1-7 Overview（RTP 版本檔）

| 區塊 | 內容 | 程式使用 |
| --- | --- | --- |
| Model / Version | 模型代號與四碼版本（目前 `3.5.0.0`） | ✅ 版本核對、輸出檔名 |
| Coin in / Total RTP 表 | 各押注型態的總 RTP | 目標值 |
| Pay Back 拆解表 | Normal Bet 的 Base Game／Free Game 派彩率、Hit%、Pulls/Hit | 目標值 |

**四份 RTP 版本檔的 Normal Bet 拆解（目標值）**

| 檔案 | Base Game | Free Game | Game RTP | FG 週期 |
| --- | --- | --- | --- | --- |
| `H028188B.xlsx` | 72% | 16% | 88% | 1/375.00 |
| `H028190B.xlsx` | 72% | 18% | 90% | 1/366.67 |
| `H028192A.xlsx` | 72% | 20% | 92% | 1/300.00 |
| `H028194A.xlsx` | 72% | 22% | 94% | 1/300.00 |

含平台彩金的總派彩率為 `Game RTP + Bonus RTP + Link RTP`；Bonus／Link 的參數由平台 OP Jackpot 模組提供，不在本模型內，本模型僅提供換算用的 SCR（見 [1-10](#1-10-op-jackpot)）。

### 1-8 Multiplier_Weight

卡片系統的輸入。版面為：

| 欄 | 標題 | 用途 |
| --- | --- | --- |
| A | `Range` | 得分倍率區間標籤 |
| B | `Weight_NB_BG_Newbie` | 新手（Newbie）Profile 的 Base Game 卡片權重 |
| C | `Weight_NB_FG_Newbie` | 新手 Profile 的 Free Game 卡片權重 |
| D | `Weight_NB_BG` | 一般（Oldhand）Profile 的 Base Game 卡片權重 |
| E | `Weight_NB_FG` | 一般 Profile 的 Free Game 卡片權重 |

列由一連串「得分倍率區間」構成（得分 ÷ Coin In，**左開右閉**），最後一列 `Free Game` 是一張特殊卡：它不看金額，只要求「這一局必須觸發 Free Game」。每一欄的權重總和都校準到 1,000,000,000，因此權重值可直接理解為「該結果出現的機率 × 10⁹」。詳細機制見[第四章](#四卡片系統說明)。

**`_Bet100` 模型（單注金額 > $100 的獨立模型）**：`H028192A_Bet100.xlsx`／`H028188B_Bet100.xlsx` 的工作表結構、欄位與對應的 92A／88B 完全相同，差異只在一般 Profile 的 Free Game 卡片權重——得分上限由 10,000 倍降為 **2,000 倍**：最高有權重的區間為 `(1000, 2000]`，`(2000, 3000]` 與 `(9000, 10000]` 權重為 0；20～200 倍主體區間與原模型形狀相同（等比），200～2,000 倍尾端等比放大配平，**FG 派彩率、觸發週期與平均倍數與原模型完全一致**。單注金額 > $100 的模擬以對應的 `config_92A_Bet100.js`／`config_88B_Bet100.js` 執行；90B／94A 對應小額投注，無 `_Bet100` 模型。

**檔案間的差異**：`Weight_NB_BG` 與 `Weight_NB_FG` 依版本各自校準；**新手兩欄（B、C）在所有檔案中完全相同**；`_Bet100` 模型除一般 Profile 的 FG 卡外與原模型逐格相同。

### 1-9 Detail 與 Detail_Newbie

`Multiplier_Weight` 各欄權重的推導工作表，程式不讀取。`Detail` 對應一般 Profile、`Detail_Newbie` 對應新手 Profile，版面相同：

| 區塊 | 內容 |
| --- | --- |
| `Simulate` 側（Cnt／Pay／Hit Rate／Avg. Multi.） | 關閉卡片系統、10 億場模擬得到的每個得分區間自然機率 |
| `Calculate` 側（Fix Num／Fix Rate／Final Rate／Weight／Hit Rate） | 人工調整係數（Fix Num）→ 校準後權重的推導鏈 |

調參的實際迴路是：關閉卡片系統跑出自然機率 → 填入 `Simulate` 側 → 調整 `Fix Num` → 得到校準後的權重 → 寫入 `Multiplier_Weight` → 開啟卡片系統重跑驗證。

### 1-10 OP Jackpot

記錄各 Profile 的 SCR（Scatter spin 率），供平台彩金模組把「每局的理論觸發率」換算成「每個含 Scatter 的 spin 的判定機率」。

| 欄位 | 內容 |
| --- | --- |
| `Threshold` | 10,000,000,000（SCR 的分母基數） |
| `NB_Newbie` | 新手 Profile 的 SCR（四份檔案統一採 92% 檔實測值 3,647,149,360） |
| `NB` | 一般 Profile 的 SCR（依版本實測：88B 3,618,838,430／90B 3,621,199,650／92A 3,641,035,800／94A 3,641,760,160） |

SCR 的口徑：**含至少 1 顆 Scatter 的 spin 數 ÷ 付費局數 × 10,000,000,000**（Base Game 與每一場 Free Spin 都各算一次 spin），由 10⁸ 場以上的大樣本模擬實測。

**彩金機率的換算公式**

```
Pscatter = SCR ÷ 10,000,000,000
           （任一 spin 至少出現 1 顆 Scatter 的機率）

Ptheory  = 該彩金獎項每一局的理論觸發機率
           （由獎項的固定派彩率與獎額反推；參數在平台彩金模組內）

Phit     = Ptheory ÷ Pscatter
           （每個含 Scatter 的 spin 實際進行一次彩金判定的條件機率）
```

彩金判定只發生在含 Scatter 的 spin 上，因此以 `Pscatter` 放大後的 `Phit` 進行判定，長期觸發率即等於 `Ptheory`。`_Bet100` 模型的 FG 卡組差異對 Scatter spin 率的影響小於 0.5%，其 `OP Jackpot` 工作表沿用原模型的 SCR 值。

---

## 二、Parameter 工作表的遊戲參數說明

Parameter 只有三組權重，控制「每一次 spin 用哪一張輪帶表」。這是影響手感與 FG 內容最上游的參數：選表同時決定該 spin 的輪帶、版型、Mystery、Scatter 與補牌設定整組走哪一張表。

### 2-1 Table Selection Weight - Base Game

| 工作表 | 權重 |
| --- | --- |
| `BG_Symbol` | 6000 |
| `BG_Symbol (2)` | 4000 |

**每一次 BG spin 的第一個動作**就是用這組權重抽出本局使用的輪帶表（60%／40%）。

### 2-2 Table Selection Weight - Free Game

| 工作表 | 權重 |
| --- | --- |
| `FG_Symbol` | 6000 |
| `FG_Symbol (2)` | 4500 |
| `FG_Symbol (3)` | 4500 |

Free Game 的**初始場次**（觸發當下配發的場次）中，每一場開始時依這組權重抽表（40%／30%／30%）。

### 2-3 Table Selection Weight - Retrigger

| 工作表 | 權重 |
| --- | --- |
| `FG_Symbol` | 6000 |
| `FG_Symbol (2)` | 4500 |
| `FG_Symbol (3)` | 4500 |

Retrigger 追加的場次中，每一場開始時改依這組權重抽表。目前兩組數值相同，保留分開設定的能力。

---

## 三、遊戲邏輯

### 3-1 盤面與座標系統

| 項目 | 值 |
| --- | --- |
| 主盤面輪數 | 6（R1～R6），Megaways 可變高度，每輪最高 5 列 |
| Extra Reel | 1 條、4 格，固定對應 R2～R5 上方各 1 格 |
| 有效視窗 | 5-6-6-6-6-5（R2～R5 的第 6 格即 Extra Reel） |

程式內部以第 7 條輪帶產生 Extra Reel 的 4 個符號，再併入 R2～R5 的最上格；判獎與 Scatter 計數都以合併後的盤面為準。

### 3-2 符號與角色

| Symbol | Id | 說明 | 角色 |
| --- | --- | --- | --- |
| `WW` | 0 | Wild | 替代除 Scatter 外的所有符號，只出現在 R2～R5，本身不帶賠率 |
| `C1` | 1 | Scatter | 只計數量，本身不帶賠率，不可被 Wild 替代 |
| `M1` | 2 | 高分符號，兼倍數符號 | 可計分；主盤面依尺寸提供倍數、Extra Reel 上固定提供倍數 |
| `M2`～`M6` | 3～7 | 高分符號 | 可計分 |
| `M7`～`M11`（A、K、Q、J、10） | 8～12 | 低分符號 | 可計分 |
| 金框符號 | 13～23 | 上列可計分符號的金框版本（Id = 基底 + 11） | 判獎視為基底符號；參與中獎後原位轉為 Wild |
| `MY` | 24（金框 25） | Mystery | 盤面停定後整盤轉換為當局抽出的目標符號 |

三項程式衍生的判斷依據：**基底符號對照**（金框 −11）、**是否金框**（決定轉 Wild 行為）、**是否可計分**（`WW`、`C1` 判獎時分別為替代／截斷）。

### 3-3 單次 spin 的流程

BG 與 FG 共用同一套流程，差別只在使用哪一張表與倍數的起算值。

```
1. 決定本 spin 使用哪一張輪帶表
      BG：依 Table Selection Weight - Base Game 抽選
      FG：初始場次依 Free Game 權重、retrigger 場次依 Retrigger 權重抽選
2. R1～R6 逐輪：依該輪的 MegaWay 版型權重抽出符號尺寸組合（1x1～1x4），
   依 Symbol Weight 抽出停輪位置，從輪帶取符號依版型填滿該輪
3. Extra Reel：依第 7 條輪帶抽 4 個符號，併入 R2～R5 的最上格
4. Mystery 轉換：依 MY 權重抽一個目標符號，
   盤面上所有 MY（含金框 MY）轉換為該符號（金框 MY 轉為金框版）
5. Post Scatter：依權重抽出補入顆數 N（0～7），在 7 條輪帶中等機率
   選 N 條組合，各輪以最短尺寸的符號區塊替換為 Scatter
6. 連消迴圈：
   6-1 依 Way Game 規則判獎（見 3-4）
   6-2 沒有任何獎 → 結束迴圈
   6-3 累計本回合得分（乘上當前累積倍數）
   6-4 處理中獎位置：金框 → 原位轉為 Wild；一般符號 → 清空
   6-5 符號下墜，空位依 Drop 權重補入新符號（可補入 Scatter 與 Mystery；
       Mystery 沿用本局的轉換目標）
   6-6 回到 6-1
7. 統計最終盤面的 Scatter 數量（主盤面與 Extra Reel 皆計入；
   大尺寸 Scatter 依實際占用格數計數）
8. 判定是否觸發／retrigger Free Game
```

### 3-4 判獎規則

```
以 Way Game 判定：
    自 R1 起，往右逐輪比對相同基底符號（Wild 可替代）
    連續達 3 輪以上才有賠率
    Ways 數 = 各連續輪上該符號的「符號個數」乘積
        大型符號（1x2／1x3／1x4）無論覆蓋幾格都只計 1 個符號
    單一符號得分 = Pay Table 賠率 ÷ 100 × Ways × Coin In
    Scatter 不參與連線；遇到即中斷該輪的比對
```

要點：

- 連線必須**從 R1 起算**（左起），中間不得跳輪。
- 金框在判獎階段視為基底符號，因此金框與基底符號對判線完全等價。
- 所有符號的 Way 獎相加即為本回合得分，再乘上當前累積倍數。

### 3-5 Cascade 與金框轉 Wild

1. 中獎的一般符號移除。
2. 中獎的金框符號**不移除**：該位置轉為 `WW` 留在盤面，供下一回合判獎使用；Wild 只保留一個 Cascade 回合。
3. 各輪剩餘符號往下墜，空位依本表的 Drop 權重補入新符號。
4. 補入的 Mystery 沿用本局的轉換目標符號；補牌可補入 Scatter。
5. 補牌後重新判獎，直到盤面不再形成新的中獎組合。

### 3-6 M1 倍數的累積與作用

**來源**：

| 位置 | 倍數 |
| --- | --- |
| 主盤面 M1（1x1） | x2 |
| 主盤面 M1（1x2） | x3 |
| 主盤面 M1（1x3） | x4 |
| 主盤面 M1（1x4） | x5 |
| Extra Reel 上的 M1 | 固定 x2（不套用尺寸映射） |

**累積**：同一回合出現多個 M1 時倍數**加總**（不相乘）。

**作用**：每一回合的得分都乘上「當前累積總倍數」。Base Game 每次新 spin 重新起算；Free Game 自 x2 起算且**跨場保留**，直到整段 Free Game 結束（見 3-7）。

M1 同時保有 Pay Table 上的連線賠率，倍數功能與連線計分並存。

### 3-7 Free Game

**觸發**：整局 Cascade 結束後，最終盤面（主盤面＋Extra Reel）的 Scatter 達 **4 顆**即觸發。

| Scatter 數 | 免費場次 |
| --- | --- |
| 4 | 10 |
| 5 | 12 |
| 6 | 14 |
| 7 | 16 |
| 8 以上 | 每多 1 顆再 +2 |

單次進入 Free Game 後，**含 retrigger 在內總場次上限 50 場**。

**輪帶表選擇**：每一場 FG 開始時抽一次表——初始場次依 `Table Selection Weight - Free Game`、retrigger 追加的場次依 `Table Selection Weight - Retrigger`。

**累積倍數**：進入 FG 時自 **x2** 起算，跨場保留、不重置，直到整段 FG 結束；下一次重新進入 FG 時重新自 x2 起算。

**Retrigger**：FG 之中再次達到 4 顆 Scatter，依同一張場次表追加場次（受 50 場上限封頂）。retrigger 只增加場次，不清除已累積的倍數。

### 3-8 一局（一次付費 spin）的完整流程

```
1. 計算本局成本：Coin In = 下注倍數 × Base Bet
2. 抽一張 Base Game 卡片（見第四章）
3. 執行一次 BG spin（流程見 3-3）
4. 若最終盤面 Scatter 達 4 顆：
       依場次表決定免費場次（上限 50）
       抽一張 Free Game 卡片（該 Profile 的 FG 卡欄；
           單注金額 > $100 的模擬使用 _Bet100 模型的 config）
       進入 Free Game：
           累積倍數自 x2 起算
           每一場：抽輪帶表 → 執行 spin → 累加得分與倍數（跨場保留）
                   → 達 4 顆 Scatter 則追加場次（受 50 場上限）
5. 本局總得分 = BG 得分 + FG 整段得分
6. 依卡片條件決定接受本局，或重抽（見 4-3）
```

### 3-9 重要規則整理

1. **每回合得分即時乘上當前累積倍數**；倍數本身以加總累積，不相乘。
2. **金框必須參與中獎才會轉為 Wild**；轉出的 Wild 只保留一個 Cascade 回合。
3. **FG 累積倍數跨場保留**，起算值 x2；retrigger 只加場次，不清除倍數。
4. **Scatter 只看整局 Cascade 結束後的最終盤面**；主盤面與 Extra Reel 皆計入，大尺寸 Scatter 依實際占用格數計數。
5. **Scatter 不放在初始輪帶上**，只由 Post Scatter 與 Cascade Drop 產生。
6. **大型符號在 Ways 計算中只計 1 個符號**，但 Scatter 計數依占用格數。
7. **Wild 不會自然停出**，盤面上的 Wild 只來自中獎金框的轉換。
8. **Cascade 補牌用獨立的 Drop 權重重新抽樣**，不是從輪帶接著往上取符號。
9. **Mystery 一局只抽一次轉換目標**，開局與補牌補入的 Mystery 都轉成同一個符號。
10. **Extra Reel 的 M1 固定 x2**，不套用主盤面的尺寸倍數映射。

---

## 四、卡片系統說明

### 4-1 用途

卡片系統**不改變盤面的機率設定**，而是在「整局結果」的層級做接受／重抽（rejection sampling），把自然機率重新塑形成目標分布。

它的存在使得下列兩件事可以被直接指定，而不必依賴盤面參數去逼近：

- **單局得分的分布**（哪些得分區間各佔多少比例）
- **FG 觸發率**

### 4-2 卡片的結構

卡片來自 `Multiplier_Weight`，依玩家 Profile 與階段分組：

| 卡片組 | 欄位 | 何時抽 |
| --- | --- | --- |
| 新手 Base Game 卡 | `Weight_NB_BG_Newbie` | 新手 Profile 每一局開始 |
| 新手 Free Game 卡 | `Weight_NB_FG_Newbie` | 新手 Profile 觸發 FG 後 |
| 一般 Base Game 卡 | `Weight_NB_BG` | 一般 Profile 每一局開始 |
| 一般 Free Game 卡 | `Weight_NB_FG` | 一般 Profile 觸發 FG 後 |

單注金額 > $100 時，改以 `_Bet100` 模型（`config_92A_Bet100.js`／`config_88B_Bet100.js`）執行，其一般 Profile 的 FG 卡即該模型的 `Weight_NB_FG`（上限 2,000 倍）；卡片組結構不變。

兩種卡片型別：

| 型別 | 判定方式 |
| --- | --- |
| 區間卡（`range`） | 要求該段得分 ÷ Coin In 落在指定區間內（左開右閉） |
| 免費遊戲卡（`free_game`） | 不看金額，只要求這一局必須觸發 Free Game |

Free Game 卡組沒有 `free_game` 型別的卡片，因為進到 FG 判定時「已觸發 FG」已是既定事實，只需比對金額區間。

**`_Bet100` 模型的 FG 卡組設計**：得分上限由 10,000 倍降為 **2,000 倍**（`(2000, 3000]` 與 `(9000, 10000]` 權重為 0，最高有權重區間 `(1000, 2000]`）。配平方式為 20～200 倍主體形狀不變、200～2,000 倍尾端等比放大，權重總和維持 10⁹、卡片加權平均 FG 倍數與原模型一致——因此 **FG 派彩率、觸發週期、平均倍數完全不變**，只有得分分布的尾端形狀不同。90B／94A 對應小額投注，無 `_Bet100` 模型。

### 4-3 單局的判定流程

```
每一局開始：依 Profile 抽一張 Base Game 卡

若抽到 free_game 卡：
    重複執行 BG spin，直到最終盤面達 4 顆 Scatter
    依 Profile 與單注金額選擇 FG 卡欄，抽一張 Free Game 卡
    重複執行「整段 Free Game」，直到 FG 總得分落在該卡的區間內

若抽到 range 卡：
    執行一次 BG spin
        若觸發了 Free Game        → 不接受，重抽該局
        若 BG 得分不在該卡區間內  → 不接受，重抽該局
        否則                      → 接受

每個階段的重抽上限為 10,000 次；達上限時保留最後一次結果並計入統計，
以便檢查是否有某張卡片實際上抽不出來。
```

要點：

- 卡片系統決定的是「**這一局要長成什麼樣**」，再用重抽把它湊出來。
- 判定用的是含小數的倍率（得分 ÷ Coin In），區間為**左開右閉**；分母一律使用 Normal Bet 的 Coin In。
- **區間卡一旦觸發 FG 就整局作廢重抽**——因此 FG 觸發率完全由 `Free Game` 卡的權重決定，與盤面的自然 Scatter 機率無關。
- FG 的重抽是以「整段 Free Game」為單位，不是單場。

### 4-4 與 Detail 工作表的關係

`Detail`（一般 Profile）與 `Detail_Newbie`（新手 Profile）是卡片權重的推導來源：先在關閉卡片系統的狀態下取得各得分區間的自然機率（`Simulate` 側），再乘上人工調整係數 `Fix Num`，正規化後得到寫入 `Multiplier_Weight` 的權重（`Calculate` 側）。因此工作表同時記錄「自然機率」與「目標機率」兩份數據，可用來檢視每個區間被放大或壓縮了多少。

### 4-5 注意事項

1. **卡片權重是影響 RTP 最直接的參數。** 調整盤面權重會改變自然機率，但最終落點仍由卡片決定；若只調盤面而不同步更新卡片權重，總 RTP 不會依預期改變，只會讓重抽次數上升。
2. **重抽次數是健康度指標。** 若某張卡片的區間在自然機率下極難達成，重抽次數會顯著上升，甚至觸及上限。模擬報表會輸出重抽統計，應一併檢視。
3. **BG 與 FG 的 RTP 分配由兩組卡片各自決定。** 四份 RTP 版本檔的差異只在一般 Profile 的卡片欄位；新手兩欄四份完全相同。
4. **FG 觸發率由 `Free Game` 卡的權重鎖定。** 要改變 FG 週期，應調整該卡權重，而非輪帶上的 Scatter 分布。
5. **`_Bet100` 模型只改變 FG 得分分布的尾端形狀。** 派彩率與週期不變，SCR 沿用原模型值；驗證時以單注金額跨越 $100 的兩組模擬（原模型 vs `_Bet100` 模型）對照。
