# H045 超級鑽石 — XLSX → Config Mapping

本文件定義 `Source/H0451.xlsx` 與 `config.js` 之間的欄位對應、型別與驗證規則。
轉換由 AI 依本文件執行；依 `專案需知/開發流程.md` 第 1 節，專案內**不建立、不保留任何轉檔腳本**。

- 基礎數學：`Source/H0451.xlsx`（1 碼版本）→ `config.js`（`excel_version` 1 碼）
- RTP／Variant：`Source/H045192A.xlsx`（4 碼版本）→ `config_92A.js`（`excel_version` 4 碼，第 1 碼須等於基礎版本）

---

## 1. Overview

| XLSX 位置 | Config 欄位 | 型別 | 說明 |
|---|---|---|---|
| `B2` | `parsheet_id` | str | 固定 `H0451` |
| `B3` | `excel_version` | str | 基礎模型 1 碼版本 |
| `A7` | `base_bet` | int | Credit 基準，100 |
| `B11` / `C11` | `bet_modes.normal.cost_multiplier` | int | Normal Bet = 1 |
| `B12` / `C12` | `bet_modes.buy_feature.cost_multiplier` | int | Buy Feature = 250 |
| `B16:F17` | `reel_num` / `window_size` | int | 5 輪 × 4 列 |
| `A21:C24` | `free_spins` | dict | `C1 Num` → `{initial, retrigger}` |
| `A25` | `max_free_spins` | int | 以 `Parameter!C31` 為準，此列為文字敘述 |
| Pay Table 區 `A:H` | `symbol_names` / `pays` / `wild_ids` / `scatter_id` / `golden_ids` | dict | 見 §1.1 |

### 1.1 Pay Table 區

- 標題列以 `A 欄 = "Symbol"` 且 `H 欄 = "Id"` **動態定位**，不寫死列號。
- `A` 欄符號名、`H` 欄 Symbol ID → `symbol_names`（`{id: name}`）。
- `E`／`F`／`G` 欄為 3／4／5 連賠付（Credit）→ `pays[id] = [E/base_bet, F/base_bet, G/base_bet]`；三者皆 0 的符號不寫入 `pays`。
- 金框符號 `G1`~`G4`、`GA`、`GK`、`GQ`、`GJ`（ID 11~18）的賠付與其基礎符號相同，另以 `golden_ids`（`{金框 id: 基礎 id}`）記錄對應關係。
- 前端規格書把金框寫作 `M1_G`~`M4_G` / `A_G` 等；**以本模型的 `G1`~`GJ` 為準**。

---

## 2. Parameter

| XLSX 位置 | Config 欄位 | 說明 |
|---|---|---|
| `B2:C6` | `table_weight.bg` | Base Game 三張輪帶表的選表權重 |
| `B9:C13` | `table_weight.fg` | Free Game 選表權重 |
| `B16:C20` | `table_weight.retrigger` | Retrigger 選表權重 |
| `C25:G25` | `cascade_multiplier.bg` | `[1, 2, 3, 5, 10]` |
| `C26:G26` | `cascade_multiplier.fg` | `[2, 4, 6, 10, 20]` |
| `C30` | `max_win_multiplier` | `20000` |
| `C31` | `max_free_spins` | `50` |
| `B36:C38` | `jackpot.trigger_weight` | `No Trigger` / `Trigger`；`Trigger > 0` 時 `jackpot.enabled = true` |

- 工作表名稱 → Config key：`BG_Symbol`→`bg_1`、`BG_Symbol (2)`→`bg_2`、`BG_Symbol (3)`→`bg_3`、
  `FG_Symbol`→`fg_1`、`FG_Symbol (2)`→`fg_2`、`FG_Symbol (3)`→`fg_3`、`BF_Symbol`→`bf_1`。
- 選表區塊以 B 欄標題文字定位（`Base Game` / `- Free Game` / `Retrigger`），不寫死列號。

---

## 3. 各輪帶工作表（`*_Symbol`）

| XLSX 區域 | Config 欄位 | 型別 / 長度 | 說明 |
|---|---|---|---|
| `K4:O203` | `tables.<key>.reels` | `int[5][200]` | **物理輪帶，讀符號名再轉 ID** |
| `Q4:U203` | —（不讀） | — | VLOOKUP 公式欄，僅供 Excel 內檢視 |
| `W4:AA203` | `tables.<key>.symbol_weight` | `int[5][200]` | 初始停輪：各輪每個停點的權重 |
| `AF4:AK22` | `tables.<key>.drop_weight` | `{id: int[5]}` | Cascade 補牌：各符號在各輪的掉落權重 |
| `AC4:AD7` | `tables.<key>.golden_result_weight` | `{str: int}` | `WW` / `WW_M` / `W2` / `W2_M` |
| `AC11:AD13` | `tables.<key>.split_count_weight` | `{int: int}` | 大鬼分裂顆數 2／3／4 |
| `AC17:AD19` | `tables.<key>.multiplier_wild_weight` | `{int: int}` | WILD 倍數 ×2／×3／×5 |

> **重要**：`Q:U` 與 `Overview!A11:A12`、`*_Symbol!C7:G22` 是公式欄。openpyxl 存檔後公式快取值會消失，
> 因此轉檔一律只讀**字面值欄位**（`K:O`、`W:AA`、`AF:AK`、`AC:AD`），不依賴任何公式快取。

### 3.1 BF_Symbol 例外

Buy Feature 進場盤不判獎、不 Cascade、金框不翻牌，因此 `bf_1` 的
`golden_result_weight`／`split_count_weight`／`multiplier_wild_weight` 三張表權重全為 `0`，程式不得使用。

---

## 4. Config 專屬欄位（非直接對應儲存格）

| Config 欄位 | 值 | 來源 |
|---|---|---|
| `game_id` | `H045` | 資料夾代號 |
| `online_game_id` | `101015` | `其他/iGaming 遊戲代號一覽.xlsx` |
| `golden_reels` | `[1, 2, 3]` | game_rule §5.1：金框只在 R2~R4（0-indexed） |
| `split_target_reels` | `[1, 2, 3, 4]` | game_rule §5.4：分裂只落 R2~R5，R1 永不落 Wild |
| `bet_modes.buy_feature.entry_table` | `bf_1` | game_rule §8.2 |
| `bet_modes.buy_feature.min_scatter` | `3` | game_rule §8.2 |
| `card_system.enabled` | `false` | 基礎 Config 不含卡片系統，由 `config_92A.js` 提供 |

---

## 5. 轉檔後驗證

- [x] `excel_version` 為 1 碼且等於 `Overview!B3`
- [x] 每張表 `reels` 與 `symbol_weight` 皆為 5 × 200
- [x] 每輪 `symbol_weight` 總和 > 0
- [x] 所有權重非負
- [x] `reels` 內的 ID 皆存在於 `symbol_names`
- [x] `pays` 的 key 皆存在於 `symbol_names`
- [ ] Simulator 與 Demogame 載入同一份 config 後逐局對帳（待 Simulator 完成）

---

## 6. 版本同步

| 異動 | 動作 |
|---|---|
| `H0451.xlsx` 內容變更 | `Overview!B3` 遞增 → 重新轉出 `config.js` → 所有 `H0451<RTP><Variant>.xlsx` 第 1 碼同步、第 2~4 碼歸零 |
| `H045192A.xlsx` 卡片權重變更 | 該檔第 2 碼遞增、第 3~4 碼歸零 → 重新轉出 `config_92A.js` |
| 任一 Config 重新轉出 | `Versions/version_manifest.json` 與 `.js` 同步更新 |
