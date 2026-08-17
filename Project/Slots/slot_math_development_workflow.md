# Slot 數學開發流程

本文件定義新 Slot 專案的**數學開發流程、製作順序、操作方式、階段產物與完成條件**。

實作欄位、命名、版本、Card System、Simulator、Demogame、Config 與報表格式等細節，統一依照 [Slot 開發注意事項](./slot_development_specification.md)。本文件不重複定義實作規格；兩份文件有差異時，以 `slot_development_specification.md` 為準。

適用範圍：`Project/Slots/H0xx_遊戲名稱/` 下的新遊戲數學模型、既有模型改版，以及 RTP、Card System、Feature 或 Bet Mode 參數調整。

## 1. 文件分工

| 文件 | 回答的問題 | 使用時機 |
|---|---|---|
| 本文件 `slot_math_development_workflow.md` | 先做什麼、後做什麼、如何推進、每階段要交付什麼 | 排程、開案、追蹤進度、交付驗收 |
| [`slot_development_specification.md`](./slot_development_specification.md) | 檔案怎麼命名、欄位怎麼定義、版本怎麼升、程式與報表怎麼實作 | 製作 XLSX、Config、Simulator、Demogame 與 Record 時 |
| 各遊戲 `game_rule.md` | 這款遊戲實際怎麼玩、如何判獎、Feature 如何運作 | 建模、實作與單局對帳時 |
| `Source/xlsx_config_usage_mapping.md` | XLSX 資料如何映射到 Config 與程式 | 轉檔、維護與查錯時 |

## 2. 過往專案整理後的標準做法

過往專案可看到數種演進中的做法：

- H013、H015、H019 使用 RTP Config、`xlsx_to_config.py`、`update_config.bat`、Simulator 與 Record 的基本流程。
- H016、H028 已拆分基礎 `config.js` 與 RTP／Variant Config，並保留 `Versions/`，較符合目前標準。
- H026 同時存在 92／94 與 A／B Variant，適合作為多模型組合的參考。
- H027 使用 `model_sync.py` 與 `update.bat` 自動同步 Source 與程式資料，代表轉檔工具名稱可以不同，但責任必須相同。

新專案採用以下統一原則：

1. `game_rule.md` 定義玩法，數學 XLSX／`Source/` 定義正式參數。
2. Config 必須由 Source 轉出，不直接手改自動產生的參數。
3. Simulator 與 Demogame 使用同一份 Config。
4. 先驗證 Card System Off 的自然機率，再驗證 Card System On。
5. 每次調參都依「Source → 版本 → Config → Simulator → Record → 對帳」完整重跑。
6. 舊專案若與目前命名、版本或報表格式不同，不直接複製舊格式；依現行規格建立。

## 3. 整體流程

```text
確認 Game Rule 與數學目標
        ↓
建立基礎數學模型
        ↓
建立 RTP／Variant／Card System 模型
        ↓
建立 Source、Mapping 與轉檔工具
        ↓
產生並驗證 Config
        ↓
實作 Simulator
        ↓
小場次 Debug 與單局驗證
        ↓
Card System Off 自然機率驗證
        ↓
Card System On／各 Mode／各 Profile 驗證
        ↓
調參循環與大場次正式模擬
        ↓
Max Win、Retry、分布與代表性單局驗證
        ↓
Simulator／Demogame 對帳
        ↓
凍結版本、整理 Record、完成交付
```

## 4. 製作順序與階段關卡

不得因為某個程式可以先寫就跳過前置規則。上一階段的完成條件成立後，才進入下一階段。

| 順序 | 階段 | 主要工作 | 產出 | 進入下一階段的條件 |
|---:|---|---|---|---|
| 1 | 開案與目標確認 | 確認 Game ID、盤面、判獎、Bet Mode、Feature、RTP、Hit Rate、Max Win、Profile 與 Variant | 已確認的 `game_rule.md`、數學目標表 | 核心規則與計算口徑無待確認項目 |
| 2 | 基礎數學模型 | 建立 Symbol、Paytable、Reel／Weight、Table、Feature 流程與自然機率 | `Source/H0xx1.xlsx` | 自然機率流程可計算，理論上限已確認 |
| 3 | RTP／Variant 模型 | 建立 92／94、A／B、Card System 區間與權重 | `Source/H0xx1<RTP><Variant>.xlsx` | 每個正式組合都有目標與資料；不建立空白 Variant |
| 4 | Mapping 與轉檔 | 定義 XLSX 到 Config 的來源、型別、欄位與驗證 | `xlsx_config_usage_mapping.md`、轉檔工具 | Config 可重建，錯誤資料會被擋下 |
| 5 | Config 產生 | 由 Source 產生基礎與 RTP／Variant Config，核對版本與資料 | `config.js`、`config_<RTP><Variant>.js` | Source、Config、版本逐項一致 |
| 6 | Simulator 實作 | 實作自然機率、Feature、Card System、批次、統計與報表 | `Simulator.py` | 固定 Seed 可重現，單執行緒 Debug 正確 |
| 7 | 小場次驗證 | 強制或指定 RNG 測試判獎、Feature、Retry、Max Win 與例外 | Debug Trace、測試紀錄 | 代表性案例逐項符合 Game Rule |
| 8 | 自然機率基準 | Card System Off 跑所有自然機率 Bet Mode | `Record/*card-off*.xlsx` 或規格化檔名 | RTP Breakdown、Hit Rate、Feature 與分布合理 |
| 9 | Card System 驗證 | 分 RTP、Variant、Profile、Bet Mode 跑 Card System On | `Record/*card.xlsx` | 權重占比合理、Retry Limit Exceeded 通過 |
| 10 | 調參與正式模擬 | 依差距修改 Source，重新轉檔、模擬、比較與升版 | 正式大場次 Record | 所有支援組合符合目標與統計誤差要求 |
| 11 | 極值與單局對帳 | 驗證 Max Win、封頂、理論可達路徑及代表性單局 | 極值紀錄、對帳案例 | Config、Simulator、Demogame 結果一致 |
| 12 | 版本凍結與交付 | 清理暫存、保存版本、報表、來源與變更說明 | 完整專案目錄 | 本文件第 9 節全部通過 |

各階段的實作要求請查閱：

- 數學文件、模型命名、版本與 RTP：[規格第 1 節](./slot_development_specification.md#1-數學文件-math-document)
- Card System：[規格第 2 節](./slot_development_specification.md#2-卡片系統-card-system)
- Simulator、BATCH_RUNS、Console 與 Record：[規格第 3 節](./slot_development_specification.md#3-模擬程式-simulator)
- Demogame 與單局對帳：[規格第 4 節](./slot_development_specification.md#4-demogame)
- Config、轉檔與版本歷史：[規格第 5 節](./slot_development_specification.md#5-config)

## 5. 各階段操作方式

### 5.1 開案與數學目標確認

1. 建立 `H0xx_遊戲名稱/` 專案資料夾。
2. 讀取並確認 `game_rule.md`。
3. 列出所有正式支援組合：RTP、Variant、Profile、Bet Mode、Card System Off／On。
4. 為每個組合定義 RTP、Hit Rate、Feature Frequency、Max Win 與其他遊戲專屬指標。
5. 將未決定的判獎順序、倍率分母、Feature 上限與例外退回確認；未確認前不製作正式模型。

### 5.2 建立基礎數學模型

1. 先完成 Base Game，再依狀態順序完成 Feature。
2. 建立 Symbol、Paytable、Reel Strip／Weight、Table 與 Bet Mode。
3. 建立 BG、FG、Cascade、Multiplier、Retrigger、Jackpot 等流程。
4. 計算 RTP Breakdown 與理論 Max Win，不只計算 Total RTP。
5. 建立基礎數學 XLSX，版本依規格使用 1 碼。

### 5.3 建立 RTP／Variant 與 Card System

1. 只建立產品實際需要的 92／94、A／B 組合。
2. A／B 表示數學 Variant，不表示 Newbie／Oldhand。
3. 依 Profile 與 Bet Mode 建立 BG／FG 卡片區間及權重。
4. 確認每張正權重卡片的區間可達，並定義 Retry 行為。
5. 建立 RTP／Variant XLSX，版本依規格使用四段格式。

### 5.4 轉檔與 Config 驗證

1. 在 `xlsx_config_usage_mapping.md` 記錄每項 Config 資料的來源。
2. 使用 `xlsx_to_config.py`、`model_sync.py` 或專案的更新腳本產生 Config。
3. 執行欄位、型別、陣列長度、ID、Weight、Min／Max、版本與模式驗證。
4. 比較轉檔前後資料，確認 Config 可由 Source 重建且沒有非預期差異。
5. 轉檔錯誤時修正 Source、Mapping 或轉檔工具，不直接修改 Config 大型陣列。

### 5.5 Simulator 開發與 Debug

1. 先完成自然機率核心，再加入 Card System 篩選與 Retry。
2. 讓 Simulator 直接讀取正式 Config，不另寫一份參數。
3. 建立固定 Seed、單執行緒與逐局 Trace 模式。
4. 建立強制／指定案例，驗證無獎、一般獎、Wild、Scatter、Feature、Retrigger、倍率與封頂。
5. 小場次確認正確後，再加入 Numba、多執行緒、BATCH_RUNS 與 Excel 報表。

### 5.6 模擬順序

模擬必須依下列順序執行：

1. 小場次、Card System Off：驗證流程與報表。
2. 中場次、Card System Off：確認自然機率 RTP 與分布。
3. 小場次、Card System On：確認抽卡、Profile、Mode 與 Retry。
4. 中場次、Card System On：調整區間、權重與目標 RTP。
5. 所有正式組合的大場次模擬。
6. Max Win、低機率 Feature 與 Retry 邊界的專項驗證。

最低批次矩陣：

| 類型 | RTP／Variant | Profile | Bet Mode | Card System |
|---|---|---|---|---|
| 自然機率基準 | 基礎 Config | 不適用 | 每個支援 Mode | Off |
| Newbie | 每個正式 RTP／Variant | Newbie | Normal／Extra 等支援 Mode | On |
| Oldhand | 每個正式 RTP／Variant | Oldhand | Normal／Extra 等支援 Mode | On |
| Buy Feature | 每個支援組合 | 依遊戲定義 | Buy Feature | On；若需自然基準則另跑 Off |
| Super Feature | 每個支援組合 | 依遊戲定義 | Super Feature | On；若需自然基準則另跑 Off |

不存在的 Mode、Profile 或 Variant 不建立空批次，也不以全零結果冒充驗證完成。

### 5.7 調參循環

每一次調參都執行完整循環：

```text
確認差距與原因
    ↓
修改對應 Source XLSX
    ↓
依異動內容更新版本
    ↓
重新產生 Config
    ↓
執行轉檔與資料驗證
    ↓
先跑小場次確認流程
    ↓
再跑中／大場次確認統計
    ↓
保存新 Record 並與前版比較
```

調參時依序判斷：

1. 先確認程式與統計口徑是否錯誤。
2. 再檢查自然機率的 Paytable、Reel、Table、Feature。
3. 最後才調整 Card System 區間與權重。
4. 不得只為讓 Total RTP 接近目標而忽略 RTP Breakdown、Hit Rate、Feature Frequency、分布或 Retry。

### 5.8 對帳與交付

1. 選定可重現的代表性 RNG／Seed。
2. 逐項核對 Config、Simulator 與 Demogame 的盤面、判獎、Feature、倍率、Total Win、Coin In 與 Retry。
3. 完成所有正式組合的最新 Record。
4. 將正式 Config 與歷史版本關係寫入 `Versions/` 與 manifest。
5. 清除暫存檔、舊測試輸出及不屬於正式交付的檔案。
6. 依第 9 節完成最終驗收。

## 6. 新專案建議目錄

```text
Project/Slots/H0xx_遊戲名稱/
├─ game_rule.md
├─ Simulator.py
├─ index.html
├─ config.js
├─ config_92A.js
├─ config_94A.js
├─ Source/
│  ├─ H0xx1.xlsx
│  ├─ H0xx192A.xlsx
│  ├─ H0xx194A.xlsx
│  ├─ xlsx_config_usage_mapping.md
│  ├─ xlsx_to_config.py 或 model_sync.py
│  └─ update_config.bat 或 update.bat
├─ Record/
└─ Versions/
   ├─ version_manifest.js
   └─ version_manifest.json
```

- A／B、92／94、Buy／Super Feature 只依產品實際需求增減。
- 目錄中的檔名、版本及報表命名必須符合現行規格，不以舊遊戲的歷史命名為準。

## 7. 異動時的重跑範圍

| 異動 | 必做流程 |
|---|---|
| Paytable、Reel、Table、Feature、Bet Mode、判獎 | 更新基礎 XLSX與版本 → 同步受影響 RTP／Variant → 轉 Config → 全部受影響批次重跑 → Demogame 對帳 |
| Card System 區間或權重 | 更新受影響 RTP／Variant XLSX 第 2 碼 → 轉 Config → Card System On 批次重跑 → 檢查占比與 Retry |
| SCR | 更新受影響 RTP／Variant XLSX 第 3 碼 → 轉 Config → 重跑 SCR 相關批次 |
| 文件、說明或排版 | 依規格更新第 4 碼；若不影響執行結果，不沿用舊版號產生新正式報表 |
| Simulator 數學邏輯 | 修正程式 → 固定 Seed 回歸 → 小場次 → 所有受影響正式批次 → Demogame 對帳 |
| 報表或顯示邏輯 | 驗證統計來源未變 → 核對 Console 與 Excel → 依影響範圍重產報表 |

## 8. 禁止事項

- 未確認 Game Rule 就自行補猜核心數學規則。
- 直接修改由 XLSX 產生的 Config 參數來避開轉檔。
- Simulator、Demogame 與 Config 各維護一套參數。
- 只跑 Card System On，不保留自然機率基準。
- 只驗證 Total RTP，不驗證 RTP Breakdown、分布、Feature 與 Retry。
- Card System Retry 時重抽目標卡、重複扣款或污染場次統計。
- 未升版就覆寫正式 XLSX、Config 或 Record。
- 建立產品未使用的空白 B Variant、Mode 或 Profile。
- 直接複製舊專案的不相容命名、版本、報表欄位或遊戲專屬統計。
- 用全零欄位表示不存在或尚未驗證的功能。

## 9. 數學完成條件

以下條件全部成立，數學開發才算完成：

- [ ] Game Rule 的核心流程、判獎、倍率、Feature 與例外均已確認。
- [ ] 每個正式 RTP、Variant、Profile 與 Bet Mode 都有明確目標。
- [ ] 基礎與 RTP／Variant XLSX 的命名及版本正確。
- [ ] Config 可由 Source 完整重建，Mapping 可追溯。
- [ ] Source、Config、Simulator、Demogame 與 Record 使用同一正式版本。
- [ ] 固定 Seed 可重現相同結果。
- [ ] Card System Off 的自然機率基準已完成。
- [ ] Card System On 的所有正式組合已完成。
- [ ] RTP、RTP Breakdown、Hit Rate、Feature Frequency 與分布符合目標。
- [ ] Card 權重占比合理，Retry Limit Exceeded 為零或已有核准處理方式。
- [ ] Max Win、封頂及理論可達路徑已驗證。
- [ ] Console 與 Record 報表內容及統計口徑一致。
- [ ] 代表性單局已完成 Config、Simulator、Demogame 三方對帳。
- [ ] 最新正式 Record 已保存，歷史版本未被覆寫。
- [ ] 暫存檔、快取與測試輸出未列入正式交付。

完成上述清單後，再依 [`slot_development_specification.md` 第 5.6 節](./slot_development_specification.md#56-完成條件)進行最終確認。
