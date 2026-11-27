<!-- 中英文合併一份（2026-11-26）：前半中文、後半 English；docx 只出英文版 -->

# Math Document Description — 101016 雷神爆金1000（Thunder Boost）

**適用範圍：Normal Bet（一般下注）**

| 項目 | 內容 |
| --- | --- |
| Game ID | 101016 |
| Math files | `H0281.xlsx`（共用自然模型）；`H028188B.xlsx`（RTP 88%）、`H028190B.xlsx`（RTP 90%）、`H028192A.xlsx`（RTP 92%）、`H028194A.xlsx`（RTP 94%）；`H028192A_Bet100.xlsx`、`H028188B_Bet100.xlsx`（單注 > $100 的獨立模型） |
| Version | 共用模型 `3`；RTP 模型 `3.5.0.3`（92A／94A／92A_Bet100）、`3.5.0.2`（88B／90B／88B_Bet100） |
| 對應程式 | `simulator.py` + `config.js`（共用模型）+ `config_88B.js` / `config_90B.js` / `config_92A.js` / `config_94A.js` / `config_92A_Bet100.js` / `config_88B_Bet100.js`（各 RTP 版本） |
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
  - [1-9 Detail](#1-9-detail)
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
   `simulator.py` 與展示頁載入 `config.js`（對應共用模型）與 `config_<RTP><版型>.js`（對應 RTP 版本檔）。xlsx 與 config 之間依固定映射轉換；本文件標示「程式使用 ✅」的欄位，指該資料會進入 config 並影響模擬。`OP Jackpot` 工作表的 SCR 是唯一由模擬器直接讀取 xlsx 的欄位（僅在啟用彩金模擬時）。

3. **金框符號在使用時被拆成兩層資訊。**
   金框符號的代號（Id 13～23）等於「基底符號 Id + 11」；判獎一律使用基底符號的賠率，金框身分只決定「中獎後該格轉為 Wild」的行為。Mystery 符號（Id 24；金框版 25）在盤面停定後整盤轉換為當局抽出的目標符號。

4. **並非所有欄位都會被程式使用。**
   各工作表左側的張數統計、佔比、平均值等欄位，以及 `Detail`、Performance Wheel 等工作表，屬於設計與檢核用途，程式不讀取。下方各節逐一標明。

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
| `Detail` | 卡片權重的推導過程（自然分布＋校準係數） | — | ❌ 設計用 |
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
| Model / Version | 模型代號與四碼版本（目前 92A／94A／92A_Bet100 為 `3.5.0.3`，其餘 `3.5.0.2`） | ✅ 版本核對、輸出檔名 |
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

> 92／94 兩版（含 92A_Bet100）的卡組已含天花板配平（3.5.0.3）：`Detail` Free Game 列的觸發局 BG 平均倍率採 70 倍上限重骰後的截斷值 `7.7609`，並由 BG `(60,70]` 權重補回，理論 Game RTP 精確至小數 6 位（0.920000／0.940000）。
>
> 送驗版數學模型（`H028192.xlsx`／`H028194.xlsx`）的 Overview 採前作送驗格式的 RTP 主列：`Base Bet｜Game RTP｜Bonus RTP｜Link RTP｜Total RTP｜Hit JP Symbol appear rate`，其中 92 版 `0.920000 + 0.02 + 0.02 = 0.96`、94 版 `0.940000 + 0.02 + 0 = 0.96`，`Hit JP Symbol appear rate` 以 Threshold 10,000,000,000 為分母。

### 1-8 Multiplier_Weight

卡片系統的輸入。版面為：

| 欄 | 標題 | 用途 |
| --- | --- | --- |
| A | `Range` | 得分倍率區間標籤 |
| B | `Weight_NB_BG` | Base Game 卡片權重 |
| C | `Weight_NB_FG` | Free Game 卡片權重 |

列由一連串「得分倍率區間」構成（得分 ÷ Coin In，**左開右閉**），最後一列 `Free Game` 是一張特殊卡：它不看金額，只要求「這一局必須觸發 Free Game」。每一欄的權重總和都校準到 1,000,000,000，因此權重值可直接理解為「該結果出現的機率 × 10⁹」。詳細機制見[第四章](#四卡片系統說明)。

**`_Bet100` 模型（單注金額 > $100 的獨立模型）**：`H028192A_Bet100.xlsx`／`H028188B_Bet100.xlsx` 的工作表結構、欄位與對應的 92A／88B 完全相同，差異只在 Free Game 卡片權重——得分上限由 3,000 倍（88B 2,000 倍）降為 **2,000 倍**：最高有權重的區間為 `(1000, 2000]`，`(2000, 3000]` 權重為 0；20～200 倍主體區間與原模型形狀相同（等比），200～2,000 倍尾端等比放大配平，**FG 派彩率、觸發週期與平均倍數與原模型完全一致**。單注金額 > $100 的模擬以對應的 `config_92A_Bet100.js`／`config_88B_Bet100.js` 執行；90B／94A 對應小額投注，無 `_Bet100` 模型。

**檔案間的差異**：`Weight_NB_BG` 與 `Weight_NB_FG` 依版本各自校準；`_Bet100` 模型除 FG 卡欄外與原模型逐格相同。

### 1-9 Detail

`Multiplier_Weight` 權重的推導工作表，程式不讀取，版面：

| 區塊 | 內容 |
| --- | --- |
| `Simulate` 側（Cnt／Pay／Hit Rate／Avg. Multi.） | 關閉卡片系統、10 億場模擬得到的每個得分區間自然機率 |
| `Calculate` 側（Fix Num／Fix Rate／Final Rate／Weight／Hit Rate） | 人工調整係數（Fix Num）→ 校準後權重的推導鏈 |

調參的實際迴路是：關閉卡片系統跑出自然機率 → 填入 `Simulate` 側 → 調整 `Fix Num` → 得到校準後的權重 → 寫入 `Multiplier_Weight` → 開啟卡片系統重跑驗證。

### 1-10 OP Jackpot

記錄 SCR（Scatter spin 率），供平台彩金模組把「每局的理論觸發率」換算成「每個含 Scatter 的 spin 的判定機率」。

| 欄位 | 內容 |
| --- | --- |
| `Threshold` | 10,000,000,000（SCR 的分母基數） |
| `NB` | SCR（依版本實測：88B 3,618,838,430／90B 3,621,199,650／92A 3,641,035,800／94A 3,641,760,160） |

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
       抽一張 Free Game 卡片（
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

卡片來自 `Multiplier_Weight`，依階段分組：

| 卡片組 | 欄位 | 何時抽 |
| --- | --- | --- |
| Base Game 卡 | `Weight_NB_BG` | 每一局開始 |
| Free Game 卡 | `Weight_NB_FG` | 觸發 FG 後 |

單注金額 > $100 時，改以 `_Bet100` 模型（`config_92A_Bet100.js`／`config_88B_Bet100.js`）執行，其 FG 卡即該模型的 `Weight_NB_FG`（上限 2,000 倍）；卡片組結構不變。

兩種卡片型別：

| 型別 | 判定方式 |
| --- | --- |
| 區間卡（`range`） | 要求該段得分 ÷ Coin In 落在指定區間內（左開右閉） |
| 免費遊戲卡（`free_game`） | 不看金額，只要求這一局必須觸發 Free Game |

Free Game 卡組沒有 `free_game` 型別的卡片，因為進到 FG 判定時「已觸發 FG」已是既定事實，只需比對金額區間。

**`_Bet100` 模型的 FG 卡組設計**：得分上限由 3,000 倍（88B 2,000 倍）降為 **2,000 倍**（`(2000, 3000]` 權重為 0，最高有權重區間 `(1000, 2000]`）。配平方式為 20～200 倍主體形狀不變、200～2,000 倍尾端等比放大，權重總和維持 10⁹、卡片加權平均 FG 倍數與原模型一致——因此 **FG 派彩率、觸發週期、平均倍數完全不變**，只有得分分布的尾端形狀不同。90B／94A 對應小額投注，無 `_Bet100` 模型。

### 4-3 單局的判定流程

```
每一局開始：抽一張 Base Game 卡

若抽到 free_game 卡：
    重複執行 BG spin，直到最終盤面達 4 顆 Scatter
    依單注金額選擇 FG 卡欄，抽一張 Free Game 卡
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
- **天花板機制**：BG 觸發 Free Game 的那一把，BG 得分必須 ≤「BG 卡組最高有權重區間」的上限（本模型 70 倍），超過上限就整把重骰（與觸發重試合併判定）。非觸發局由區間卡本身限制；因此 `Detail` 的 Free Game 列平均倍率採重骰後的截斷平均（與同列自然值不同屬正常）。
- **區間卡一旦觸發 FG 就整局作廢重抽**——因此 FG 觸發率完全由 `Free Game` 卡的權重決定，與盤面的自然 Scatter 機率無關。
- FG 的重抽是以「整段 Free Game」為單位，不是單場。

### 4-4 與 Detail 工作表的關係

`Detail` 是卡片權重的推導來源：先在關閉卡片系統的狀態下取得各得分區間的自然機率（`Simulate` 側），再乘上人工調整係數 `Fix Num`，正規化後得到寫入 `Multiplier_Weight` 的權重（`Calculate` 側）。因此工作表同時記錄「自然機率」與「目標機率」兩份數據，可用來檢視每個區間被放大或壓縮了多少。

### 4-5 注意事項

1. **卡片權重是影響 RTP 最直接的參數。** 調整盤面權重會改變自然機率，但最終落點仍由卡片決定；若只調盤面而不同步更新卡片權重，總 RTP 不會依預期改變，只會讓重抽次數上升。
2. **重抽次數是健康度指標。** 若某張卡片的區間在自然機率下極難達成，重抽次數會顯著上升，甚至觸及上限。模擬報表會輸出重抽統計，應一併檢視。
3. **BG 與 FG 的 RTP 分配由兩組卡片各自決定。** 四份 RTP 版本檔的差異只在卡片欄位。
4. **FG 觸發率由 `Free Game` 卡的權重鎖定。** 要改變 FG 週期，應調整該卡權重，而非輪帶上的 Scatter 分布。
5. **`_Bet100` 模型只改變 FG 得分分布的尾端形狀。** 派彩率與週期不變，SCR 沿用原模型值；驗證時以單注金額跨越 $100 的兩組模擬（原模型 vs `_Bet100` 模型）對照。

---

<!-- ===== English ===== -->

# Math Document Description — 101016 Thunder Boost

**Scope: Normal Bet**

| Item | Content |
| --- | --- |
| Game ID | 101016 |
| Math files | `H0281.xlsx` (shared natural-probability model); `H028188B.xlsx` (RTP 88%), `H028190B.xlsx` (RTP 90%), `H028192A.xlsx` (RTP 92%), `H028194A.xlsx` (RTP 94%); `H028192A_Bet100.xlsx`, `H028188B_Bet100.xlsx` (standalone models for single bets above $100) |
| Version | Shared model `3`; RTP models `3.5.0.3` (92A / 94A / 92A_Bet100), `3.5.0.2` (88B / 90B / 88B_Bet100) |
| Companion programs | `simulator.py` + `config.js` (shared model) + `config_88B.js` / `config_90B.js` / `config_92A.js` / `config_94A.js` / `config_92A_Bet100.js` / `config_88B_Bet100.js` (per RTP version) |
| Board | 6-reel Megaways; up to 5 rows per reel on the main board; 1 Extra Reel cell above each of reels 2–5 (effective window 5-6-6-6-6-5) |
| Win evaluation | Way Game (2,025–32,400 ways), consecutive adjacent reels from the left; cascading removal and refill after each win |
| Coin In | 100 (Base Bet 100 × Price 1) |
| Bet mode | Normal Bet |

---

## Table of Contents

- [1. Worksheet Guide](#1-worksheet-guide)
  - [1-1 How the program consumes the xlsx parameters](#1-1-how-the-program-consumes-the-xlsx-parameters)
  - [1-2 Worksheet overview](#1-2-worksheet-overview)
  - [1-3 Overview (shared model)](#1-3-overview-shared-model)
  - [1-4 Parameter](#1-4-parameter)
  - [1-5 Symbol reel sheets](#1-5-symbol-reel-sheets)
  - [1-6 Performance Wheel](#1-6-performance-wheel)
  - [1-7 Overview (RTP version files)](#1-7-overview-rtp-version-files)
  - [1-8 Multiplier_Weight](#1-8-multiplier_weight)
  - [1-9 Detail](#1-9-detail)
  - [1-10 OP Jackpot](#1-10-op-jackpot)
- [2. Game Parameters on the Parameter Worksheet](#2-game-parameters-on-the-parameter-worksheet)
  - [2-1 Table Selection Weight - Base Game](#2-1-table-selection-weight---base-game)
  - [2-2 Table Selection Weight - Free Game](#2-2-table-selection-weight---free-game)
  - [2-3 Table Selection Weight - Retrigger](#2-3-table-selection-weight---retrigger)
- [3. Game Logic](#3-game-logic)
  - [3-1 Board and coordinate system](#3-1-board-and-coordinate-system)
  - [3-2 Symbols and roles](#3-2-symbols-and-roles)
  - [3-3 Flow of a single spin](#3-3-flow-of-a-single-spin)
  - [3-4 Win evaluation rules](#3-4-win-evaluation-rules)
  - [3-5 Cascade and gold-frame-to-Wild conversion](#3-5-cascade-and-gold-frame-to-wild-conversion)
  - [3-6 M1 multiplier accumulation and application](#3-6-m1-multiplier-accumulation-and-application)
  - [3-7 Free Game](#3-7-free-game)
  - [3-8 Full flow of one paid spin](#3-8-full-flow-of-one-paid-spin)
  - [3-9 Key rules recap](#3-9-key-rules-recap)
- [4. Card System](#4-card-system)
  - [4-1 Purpose](#4-1-purpose)
  - [4-2 Card structure](#4-2-card-structure)
  - [4-3 Per-round decision flow](#4-3-per-round-decision-flow)
  - [4-4 Relation to the Detail worksheets](#4-4-relation-to-the-detail-worksheets)
  - [4-5 Notes](#4-5-notes)

---

## 1. Worksheet Guide

### 1-1 How the program consumes the xlsx parameters

The math documents are split into two kinds of workbooks: the **shared natural-probability model** (`H0281.xlsx`: reels, paytable, size patterns, drops, Free Game spin counts — shared by all RTP versions) and the **RTP version files** (`H0281<RTP><variant>.xlsx`: version number, card weights, SCR). Four points are essential for matching worksheet fields to program behavior:

1. **Weights are relative.**
   Every field labeled Weight is a relative weight; it need not be a probability and need not sum to 100%. The program draws a random value across the total of that weight group and lands on an item in proportion to its weight. **The sum of each weight group is that group's denominator**, so raising a single entry also dilutes every other entry in the same group.

2. **The program reads configs converted from the xlsx.**
   `simulator.py` and the demo page load `config.js` (shared model) and `config_<RTP><variant>.js` (RTP version file). The xlsx and configs are converted through a fixed mapping. Fields marked "Used ✅" in this document are the ones that enter the config and affect simulation. The SCR on the `OP Jackpot` worksheet is the only field the simulator reads directly from the xlsx (only when jackpot simulation is enabled).

3. **Gold-framed symbols carry two layers of information.**
   A gold-framed symbol's Id (13–23) equals its base symbol Id + 11. Win evaluation always uses the base symbol's pays; the gold-frame identity only governs the "convert to Wild after winning" behavior. The Mystery symbol (Id 24; gold-framed 25) converts board-wide into the target symbol drawn for that spin once the board settles.

4. **Not every field is consumed by the program.**
   The tally/ratio/average columns on the left of each sheet, and the `Detail` and Performance Wheel worksheets, are for design and verification; the program does not read them. Each section below states this explicitly.

### 1-2 Worksheet overview

**Shared model `H0281.xlsx`**

| Worksheet | Provides | Affects | Used |
| --- | --- | --- | --- |
| `Overview` | Basic game specs, Free Game spin table, symbol paytable | Cost, win evaluation, FG spin counts | ✅ partial |
| `Parameter` | Three reel-table selection weight groups | Table selection at the start of every spin | ✅ |
| `BG_Symbol`, `BG_Symbol (2)` | Two Base Game reel sets + pattern/conversion/drop weights | BG initial board and cascade refills | ✅ |
| `FG_Symbol`, `FG_Symbol (2)`, `FG_Symbol (3)` | Three Free Game reel sets + pattern/conversion/drop weights | FG initial board and cascade refills | ✅ |
| `BG_Performance Wheel`, `FG_Performance Wheel` | Presentation-side wheel reference | — | ❌ presentation |

**RTP version files `H0281<RTP><variant>.xlsx` (four files plus two `_Bet100` files, all sharing the same structure)**

| Worksheet | Provides | Affects | Used |
| --- | --- | --- | --- |
| `Overview` | Version number, RTP breakdown per bet type | Version check, output file names | ✅ version |
| `Multiplier_Weight` | Card weights for the card system | Accept/redraw of per-round results | ✅ |
| `Detail` | Derivation of the card weights (natural distribution + calibration factors) | — | ❌ design |
| `OP Jackpot` | SCR (scatter-spin rate) records | Jackpot probability conversion | ✅ when jackpot simulation is on |

### 1-3 Overview (shared model)

Provides the basic game specification.

| Block | Content | Used |
| --- | --- | --- |
| Model / Version | Model code `H0281` and the shared-model version (single integer) | ✅ version check |
| Base Bet / Multiway | Bet basis 100 and maximum ways 32,400 | ✅ |
| Coin in table | Cost and multiplier per bet type | ✅ Normal Bet row |
| Reel # / Visible Window Size | 6 reels; effective window 5-6-6-6-6-5 (reels 2–5 include the Extra Reel cell) | ✅ board dimensions |
| Free Spins Setting | Scatter count → free spins: 4 scatters award 10 spins, +2 per additional scatter; total cap 50 | ✅ (see 3-7) |
| Pay Table | Symbol codes, Ids, and pays for 3/4/5/6 of a kind (per 100 credit bet) | ✅ win evaluation |

**Coin In**

```
Coin In = bet multiplier × Base Bet
```

All RTP and multiplier statistics use "total round win ÷ Coin In". Pay Table values are per 100 credit bet, i.e. value ÷ 100 = pay in bet multiples per single way.

### 1-4 Parameter

The shared model's table-selection control panel — three weight groups only. See [Chapter 2](#2-game-parameters-on-the-parameter-worksheet) block by block.

### 1-5 Symbol reel sheets

Two Base Game sheets and three Free Game sheets with identical layout. Each defines "one reel set plus that table's own pattern/conversion/drop weights".

| Field group | Content | Used |
| --- | --- | --- |
| Leftmost `Symbol` / `Description` / `R1~R7` / `ID` (A4:J29) | Symbol lookup table (name ↔ Id) and per-reel tallies | ✅ lookup table; tally columns ❌ verification |
| `Symbol` (M4:S203) | Reel strips as text, 7 strips × 200 cells | ❌ human-readable |
| `Symbol ID` (U4:AA203) | Reel strips as Ids, derived from the lookup table | ✅ actual reels |
| `Symbol Weight` (AC4:AI203) | Stop-position weight for every reel cell | ✅ stop position |
| `MegaWay` (C33:H47) | Reels 1–6 × 15 large-symbol size-pattern weights | ✅ per-reel symbol size layout |
| `MY` (C51:C63) | 13 weights for the Mystery conversion target (index = symbol Id: 0 = Wild, 1 = Scatter, 2–12 = M1–M11) | ✅ one target draw per spin |
| `Post Scatter` (B67:C74) | Weights for the number of Scatters (0–7) placed after the board settles | ✅ Scatter generation |
| `Drop1`–`Drop5` (AL4:AR145) | Cascade refill symbol weights, 7 reels × 26 symbols × 5 stages | ✅ cascade refills |

**About `Symbol Weight`**: this is not a "symbol weight" but a "**stop-position** weight". The program first draws a reel position from this column, then fills the reel from that position following the MegaWay size pattern. A symbol's actual appearance rate therefore depends on how often it appears on the strip, the weights of those positions, and the size-pattern distribution.

**About `Drop1`–`Drop5`**: when cascades open up empty cells, the program **does not pull further symbols off the reel strip — it resamples from this weight table**. The five stages correspond to successive cascade steps. Scatter is not present on the initial reel strips; it enters the board only through Post Scatter and Drops.

**The two BG sheets / three FG sheets** differ only in their weight configurations (gold-frame ratio, multiplier layout, Scatter refill rates); layout and field meanings are identical.

### 1-6 Performance Wheel

Wheel reference for the presentation layer. Not read by the program; affects no probabilities.

### 1-7 Overview (RTP version files)

| Block | Content | Used |
| --- | --- | --- |
| Model / Version | Model code and the four-part version (currently `3.5.0.3` for 92A / 94A / 92A_Bet100, `3.5.0.2` for the rest) | ✅ version check, output file names |
| Coin in / Total RTP table | Total RTP per bet type | target values |
| Pay Back breakdown | Normal Bet Base Game / Free Game pay back, Hit%, Pulls/Hit | target values |

**Normal Bet breakdown of the four RTP version files (target values)**

| File | Base Game | Free Game | Game RTP | FG cycle |
| --- | --- | --- | --- | --- |
| `H028188B.xlsx` | 72% | 16% | 88% | 1/375.00 |
| `H028190B.xlsx` | 72% | 18% | 90% | 1/366.67 |
| `H028192A.xlsx` | 72% | 20% | 92% | 1/300.00 |
| `H028194A.xlsx` | 72% | 22% | 94% | 1/300.00 |

The total pay back including platform jackpots is `Game RTP + Bonus RTP + Link RTP`; the Bonus/Link parameters live in the platform OP Jackpot module, not in this model. This model only supplies the SCR used for the conversion (see [1-10](#1-10-op-jackpot)).

> The 92 / 94 versions (including 92A_Bet100) carry the oldhand payout-ceiling calibration (3.5.0.3): the trigger-spin BG average on the `Detail` Free Game row uses the truncated mean `7.7609` (re-roll above the 70x cap), rebalanced through the oldhand BG `(60,70]` weight, so the theoretical Game RTP is exact to 6 decimal places (0.920000 / 0.940000).
>
> The submission math models (`H028192.xlsx` / `H028194.xlsx`) use the previous title's submission Overview layout — the RTP main row `Base Bet | Game RTP | Bonus RTP | Link RTP | Total RTP | Hit JP Symbol appear rate`, where the 92 version reads `0.920000 + 0.02 + 0.02 = 0.96` and the 94 version `0.940000 + 0.02 + 0 = 0.96`; `Hit JP Symbol appear rate` is expressed against a threshold of 10,000,000,000.

### 1-8 Multiplier_Weight

Input of the card system. Layout:

| Column | Header | Purpose |
| --- | --- | --- |
| A | `Range` | Win-multiple interval labels |
| B | `Weight_NB_BG` | Base Game card weights |
| C | `Weight_NB_FG` | Free Game card weights |

The rows are a sequence of win-multiple intervals (win ÷ Coin In, **open on the left, closed on the right**); the final `Free Game` row is a special card that ignores the amount and only requires "this round must trigger Free Game". Every column's weights are calibrated to a total of 1,000,000,000, so a weight can be read directly as "probability of that outcome × 10⁹". Full mechanics in [Chapter 4](#4-card-system).

**The `_Bet100` models (standalone models for single bets above $100)**: `H028192A_Bet100.xlsx` / `H028188B_Bet100.xlsx` share the exact worksheet structure and columns of 92A / 88B; they differ only in the Free Game card weights — the win cap drops from 3,000× (2,000× for 88B) to **2,000×**: the highest weighted interval is `(1000, 2000]`, with `(2000, 3000]` at weight 0; the 20×–200× body keeps the original shape (uniform scale) and the 200×–2,000× tail is scaled up uniformly to rebalance, so the **FG pay back, trigger cycle and average multiple are identical to the original models**. Simulations with single bets above $100 run with the matching `config_92A_Bet100.js` / `config_88B_Bet100.js`; 90B / 94A serve small bets and have no `_Bet100` model.

**Differences across the files**: `Weight_NB_BG` and `Weight_NB_FG` are calibrated per version; a `_Bet100` model is cell-identical to its base model except for the FG card column.

### 1-9 Detail

Derivation worksheet for the `Multiplier_Weight` columns; not read by the program. Layout:

| Block | Content |
| --- | --- |
| `Simulate` side (Cnt / Pay / Hit Rate / Avg. Multi.) | Natural probability of every win interval, measured over 1 billion rounds with the card system off |
| `Calculate` side (Fix Num / Fix Rate / Final Rate / Weight / Hit Rate) | Manual calibration factors (Fix Num) → derivation chain to the calibrated weights |

The tuning loop is: run natural probability with the card system off → fill the `Simulate` side → adjust `Fix Num` → obtain calibrated weights → write into `Multiplier_Weight` → re-run with the card system on to verify.

### 1-10 OP Jackpot

Records the SCR (scatter-spin rate), letting the platform jackpot module convert "theoretical trigger probability per round" into "decision probability per scatter-bearing spin".

| Field | Content |
| --- | --- |
| `Threshold` | 10,000,000,000 (denominator base of the SCR) |
| `NB` | SCR (measured per version: 88B 3,618,838,430 / 90B 3,621,199,650 / 92A 3,641,035,800 / 94A 3,641,760,160) |

SCR definition: **number of spins containing at least one Scatter ÷ paid rounds × 10,000,000,000** (the Base Game spin and every Free Spin each count as one spin), measured over simulations of 10⁸ rounds or more.

**Jackpot probability conversion**

```
Pscatter = SCR ÷ 10,000,000,000
           (probability that any given spin shows at least one Scatter)

Ptheory  = theoretical trigger probability of a jackpot award per round
           (back-derived from the award's fixed pay back rate and prize;
            parameters live in the platform jackpot module)

Phit     = Ptheory ÷ Pscatter
           (conditional probability of running one jackpot decision on each
            scatter-bearing spin)
```

Jackpot decisions happen only on scatter-bearing spins, so running them at `Phit` (amplified by `Pscatter`) makes the long-run trigger rate equal `Ptheory`. The `_Bet100` models' FG card difference changes the scatter-spin rate by less than 0.5%, so their `OP Jackpot` worksheets carry the base models' SCR values.

---

## 2. Game Parameters on the Parameter Worksheet

Parameter holds three weight groups that control "which reel table each spin uses". This is the most upstream lever on game feel and FG content: the table choice fixes that spin's reels, size patterns, Mystery, Scatter and refill settings as a whole.

### 2-1 Table Selection Weight - Base Game

| Worksheet | Weight |
| --- | --- |
| `BG_Symbol` | 6000 |
| `BG_Symbol (2)` | 4000 |

**The first action of every BG spin** is drawing the reel table from this group (60% / 40%).

### 2-2 Table Selection Weight - Free Game

| Worksheet | Weight |
| --- | --- |
| `FG_Symbol` | 6000 |
| `FG_Symbol (2)` | 4500 |
| `FG_Symbol (3)` | 4500 |

During the Free Game's **initial spins** (those awarded at the trigger), the table is drawn from this group at the start of every spin (40% / 30% / 30%).

### 2-3 Table Selection Weight - Retrigger

| Worksheet | Weight |
| --- | --- |
| `FG_Symbol` | 6000 |
| `FG_Symbol (2)` | 4500 |
| `FG_Symbol (3)` | 4500 |

Spins added by retriggers draw their table from this group instead. The two groups currently hold the same values; keeping them separate preserves the ability to tune them independently.

---

## 3. Game Logic

### 3-1 Board and coordinate system

| Item | Value |
| --- | --- |
| Main board reels | 6 (R1–R6), Megaways variable height, up to 5 rows per reel |
| Extra Reel | one strip of 4 cells, fixed above R2–R5 (one cell each) |
| Effective window | 5-6-6-6-6-5 (the 6th cell of R2–R5 is the Extra Reel cell) |

Internally the program generates the Extra Reel's 4 symbols from a 7th strip and merges them into the top cells of R2–R5; win evaluation and Scatter counting both use the merged board.

### 3-2 Symbols and roles

| Symbol | Id | Description | Role |
| --- | --- | --- | --- |
| `WW` | 0 | Wild | Substitutes for all symbols except Scatter; appears only on R2–R5; carries no pays |
| `C1` | 1 | Scatter | Counted only; carries no pays; cannot be substituted by Wild |
| `M1` | 2 | Top symbol, doubles as the multiplier symbol | Pays; provides multipliers by size on the main board and a fixed multiplier on the Extra Reel |
| `M2`–`M6` | 3–7 | High symbols | Pay |
| `M7`–`M11` (A, K, Q, J, 10) | 8–12 | Low symbols | Pay |
| Gold-framed symbols | 13–23 | Gold-framed versions of the paying symbols (Id = base + 11) | Evaluated as the base symbol; convert to Wild in place after taking part in a win |
| `MY` | 24 (gold-framed 25) | Mystery | Converts board-wide into the target symbol drawn for the spin once the board settles |

Three derived attributes drive the program: **base-symbol mapping** (gold frame −11), **gold-frame flag** (governs Wild conversion), and **payable flag** (`WW` substitutes, `C1` interrupts during evaluation).

### 3-3 Flow of a single spin

BG and FG share the same flow; they differ only in which tables are used and the multiplier's starting value.

```
1. Choose the reel table for this spin
      BG: draw by Table Selection Weight - Base Game
      FG: initial spins draw by the Free Game group,
          retrigger spins by the Retrigger group
2. For R1–R6: draw a size pattern (1x1–1x4 blocks) from that reel's MegaWay
   weights, draw a stop position from Symbol Weight, then fill the reel from
   the strip following the pattern
3. Extra Reel: draw 4 symbols from the 7th strip and merge them into the top
   cells of R2–R5
4. Mystery conversion: draw one target symbol from the MY weights; every MY
   on the board (including gold-framed MY) converts to it (gold-framed MY
   converts to the gold-framed version)
5. Post Scatter: draw a count N (0–7); pick a combination of N of the 7
   strips uniformly; on each chosen strip replace the shortest symbol block
   with a Scatter
6. Cascade loop:
   6-1 Evaluate wins by the Way Game rules (see 3-4)
   6-2 No wins → exit the loop
   6-3 Add this step's win (multiplied by the current accumulated multiplier)
   6-4 Handle winning positions: gold-framed → convert to Wild in place;
       regular symbols → clear
   6-5 Symbols fall; empty cells refill from the Drop weights (Scatter and
       Mystery may drop in; Mystery reuses this spin's conversion target)
   6-6 Back to 6-1
7. Count Scatters on the final board (main board and Extra Reel both count;
   oversized Scatters count by the cells they occupy)
8. Decide Free Game trigger / retrigger
```

### 3-4 Win evaluation rules

```
Way Game evaluation:
    From R1, compare the same base symbol reel by reel to the right
    (Wild substitutes); 3+ consecutive reels required for a pay
    Ways = product of that symbol's symbol count on each consecutive reel
        an oversized symbol (1x2/1x3/1x4) counts as ONE symbol regardless
        of the cells it covers
    Single-symbol win = Pay Table value ÷ 100 × Ways × Coin In
    Scatter never joins a way; hitting one interrupts that reel's match
```

Key points:

- Ways must **start from R1** (leftmost); no skipping reels.
- Gold-framed symbols are evaluated as their base symbols, so they are fully equivalent for way matching.
- The sum of all symbols' way wins is this step's win, then multiplied by the current accumulated multiplier.

### 3-5 Cascade and gold-frame-to-Wild conversion

1. Winning regular symbols are removed.
2. Winning gold-framed symbols are **not removed**: the cell converts to `WW` and stays on the board for the next evaluation; the Wild lasts one cascade step only.
3. Remaining symbols fall; empty cells refill from this table's Drop weights.
4. Refilled Mystery symbols reuse this spin's conversion target; refills may bring in Scatters.
5. Evaluation repeats until the board forms no new wins.

### 3-6 M1 multiplier accumulation and application

**Sources**:

| Position | Multiplier |
| --- | --- |
| Main-board M1 (1x1) | x2 |
| Main-board M1 (1x2) | x3 |
| Main-board M1 (1x3) | x4 |
| Main-board M1 (1x4) | x5 |
| M1 on the Extra Reel | fixed x2 (size mapping does not apply) |

**Accumulation**: multiple M1s in the same step **add up** (never multiply).

**Application**: every cascade step's win is multiplied by the current accumulated total. Base Game restarts the accumulation on every new spin; Free Game starts at x2 and **carries it across spins** until the whole Free Game session ends (see 3-7).

M1 also keeps its line pays on the Pay Table; the multiplier role and the paying role coexist.

### 3-7 Free Game

**Trigger**: after the whole cascade sequence ends, **4 Scatters** on the final board (main board + Extra Reel) trigger the Free Game.

| Scatters | Free spins |
| --- | --- |
| 4 | 10 |
| 5 | 12 |
| 6 | 14 |
| 7 | 16 |
| 8+ | +2 per additional Scatter |

After entering the Free Game, **the total number of spins, retriggers included, is capped at 50**.

**Reel-table selection**: a table is drawn at the start of every FG spin — initial spins from `Table Selection Weight - Free Game`, retrigger-added spins from `Table Selection Weight - Retrigger`.

**Accumulated multiplier**: starts at **x2** on entering the FG, carries across spins without reset until the whole session ends; the next FG session starts again from x2.

**Retrigger**: reaching 4 Scatters again during the FG adds spins by the same award table (capped by the 50-spin limit). Retriggers only add spins; they never clear the accumulated multiplier.

### 3-8 Full flow of one paid spin

```
1. Cost of the round: Coin In = bet multiplier × Base Bet
2. Draw a Base Game card (see Chapter 4)
3. Run one BG spin (flow in 3-3)
4. If the final board reaches 4 Scatters:
       determine free spins by the award table (cap 50)
       draw a Free Game card (simulations with a
           single bet above $100 run on the _Bet100 model's config)
       run the Free Game:
           multiplier starts at x2
           each spin: draw reel table → run the spin → add win, carry the
                      multiplier → 4+ Scatters add spins (cap 50)
5. Round total = BG win + whole FG session win
6. Accept the round, or redraw it, by the card's condition (see 4-3)
```

### 3-9 Key rules recap

1. **Each cascade step's win is multiplied immediately by the current accumulated multiplier**; the multiplier itself accumulates by addition, never multiplication.
2. **A gold-framed symbol converts to Wild only after taking part in a win**; the Wild lasts one cascade step.
3. **The FG multiplier carries across spins**, starting at x2; retriggers add spins without clearing it.
4. **Scatters are counted only on the final board after all cascades end**; main board and Extra Reel both count, and oversized Scatters count by the cells they occupy.
5. **Scatter is absent from the initial reel strips**; it enters only via Post Scatter and cascade Drops.
6. **Oversized symbols count as one symbol in the Ways product**, but Scatter counting goes by occupied cells.
7. **Wild never stops in naturally**; the only source of Wilds is the conversion of winning gold-framed symbols.
8. **Cascade refills resample from the dedicated Drop weights**, not from the reel strip.
9. **Mystery draws its conversion target once per spin**; initial and refilled Mysteries all convert to the same symbol.
10. **M1 on the Extra Reel is fixed at x2**; the main board's size mapping does not apply there.

---

## 4. Card System

### 4-1 Purpose

The card system **does not alter the board probabilities**. It performs accept/redraw (rejection sampling) at the level of the whole round result, reshaping the natural probability into a target distribution.

It makes the following two things directly specifiable instead of being approximated through board parameters:

- **the distribution of per-round wins** (how much probability each win interval carries)
- **the FG trigger rate**

### 4-2 Card structure

Cards come from `Multiplier_Weight`, grouped by stage:

| Card group | Column | Drawn when |
| --- | --- | --- |
| Base Game cards | `Weight_NB_BG` | At the start of every round |
| Free Game cards | `Weight_NB_FG` | After an FG trigger |

For single bets above $100 the simulation runs on the `_Bet100` model (`config_92A_Bet100.js` / `config_88B_Bet100.js`), whose FG cards are that model's `Weight_NB_FG` (2,000× cap); the card-group structure is unchanged.

Two card types:

| Type | Condition |
| --- | --- |
| Interval card (`range`) | The segment's win ÷ Coin In must fall inside the interval (open left, closed right) |
| Free Game card (`free_game`) | Ignores the amount; requires only that this round triggers the Free Game |

Free Game card groups contain no `free_game`-type card, because by the time the FG decision runs, "FG triggered" is already a fact — only the amount interval is checked.

**Design of the `_Bet100` FG card group**: the win cap drops from 3,000× (2,000× for 88B) to **2,000×** (`(2000, 3000]` at weight 0; highest weighted interval `(1000, 2000]`). Rebalancing keeps the 20×–200× body shape unchanged and scales the 200×–2,000× tail up uniformly; the weight total stays at 10⁹ and the card-weighted average FG multiple matches the base model — so **FG pay back, trigger cycle and average multiple are unchanged**; only the tail shape of the win distribution differs. 90B / 94A serve small bets and have no `_Bet100` model.

### 4-3 Per-round decision flow

```
At the start of every round: draw a Base Game card

If a free_game card is drawn:
    rerun BG spins until the final board reaches 4 Scatters
    choose the FG card column by single-bet amount, draw an FG card
    rerun the WHOLE Free Game session until its total win falls inside
    the card's interval

If a range card is drawn:
    run one BG spin
        if it triggered the Free Game          → reject, redraw the round
        if the BG win is outside the interval  → reject, redraw the round
        otherwise                              → accept

Every stage is protected by a redraw cap of 10,000; on reaching the cap the
last result is kept and recorded, so cards that are practically undrawable
can be detected.
```

Key points:

- The card system decides "**what this round should look like**", then uses redraws to realize it.
- Decisions use fractional multiples (win ÷ Coin In) with open-left / closed-right intervals; the denominator is always the Normal Bet Coin In.
- **Payout ceiling**: the Base Game win of the spin that triggers the Free Game must not exceed the upper bound of the highest weighted Base Game card interval (70× in this model); a trigger spin above the bound is redrawn entirely (combined with the trigger-retry loop). Non-trigger rounds are bounded by their interval cards; the Free Game row's average multiple in `Detail` therefore uses the truncated conditional mean after redraws (differing from the natural value in the same row is expected).
- **A range card rejects the whole round as soon as the FG triggers** — the FG trigger rate is therefore fixed entirely by the `Free Game` card's weight, independent of the board's natural Scatter probability.
- FG redraws operate on the **whole Free Game session**, not on single spins.

### 4-4 Relation to the Detail worksheets

`Detail` is the derivation source of the card weights: natural probabilities per win interval are measured with the card system off (`Simulate` side), multiplied by the manual calibration factor `Fix Num`, and normalized into the weights written to `Multiplier_Weight` (`Calculate` side). The worksheets therefore hold both the "natural" and the "target" distributions, showing how much each interval was amplified or compressed.

### 4-5 Notes

1. **Card weights are the most direct lever on RTP.** Changing board weights changes the natural probability, but the final outcome is still fixed by the cards; changing the board without recalibrating the cards will not move total RTP as expected — it only raises redraw counts.
2. **Redraw counts are a health indicator.** A card whose interval is very hard to reach naturally shows sharply higher redraw counts, possibly hitting the cap. Simulation reports output redraw statistics; review them together.
3. **The BG/FG RTP split is set by the two card groups independently.** The four RTP version files differ only in the card columns.
4. **The FG trigger rate is locked by the `Free Game` card weight.** To change the FG cycle, adjust that card's weight, not the Scatter distribution on the reels.
5. **A `_Bet100` model changes only the tail shape of the FG win distribution.** Pay back and cycle are unchanged, and its SCR carries the base model's value; verification compares paired simulations with single bets on both sides of $100 (base model vs `_Bet100` model).
