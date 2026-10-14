# H027 宙斯 2500（Zeus 2500, 101027）Game Description

> 文件目的：說明遊戲模型參數的使用方式與各參數對應的實際遊戲功能。
> 版本：基礎數學 `7`／RTP 模型 `7.4.0.0`（2026-10-14）
> 一致性來源：`game_rule.md`、`Source/H0271A.xlsx`／`H0271B.xlsx`、`Source/H02719xX(_Bet100).xlsx`
> 參數或選表邏輯更新時，本文件必須同步更新。

---

## §1. 模型檔案與資料所有權

| 檔案 | 資料所有權 | 執行檔 |
| --- | --- | --- |
| `Source/H0271A.xlsx`／`H0271B.xlsx` | 自然機率（A／B 兩套基礎數學）：輪帶、停輪權重、賠率、BG 選表、FG 場次配置、C2／C3 倍數權重、C2→C3 轉換權重 | `config_A.js`／`config_B.js`（版本 `7`） |
| `Source/H027194A.xlsx`／`H027194B.xlsx` | 小 Bet（`< $2`）：卡片權重、OP Jackpot SCR | `config_94A.js`／`config_94B.js`（`7.4.0.0`） |
| `Source/H027192A.xlsx`／`H027192B.xlsx` | 中 Bet（`$2～$100`）：同上 | `config_92A.js`／`config_92B.js` |
| `Source/H027192A_Bet100.xlsx`／`H027192B_Bet100.xlsx` | 大 Bet（`> $100`，含 `> $1,500` 超大 Bet）：BG／FG 上限 1000x，BG 實際上限 200x（天花板） | `config_92A_Bet100.js`／`config_92B_Bet100.js` |

RTP Config 以 `base_config` 指向同 Variant 的基礎 Config；Simulator 與 index 先載基礎 Config 再疊 RTP Config。送驗只送 A 版 92／94（`文件/101027/`）。

---

## §2. 基礎數學參數（`H0271X.xlsx` → `config_X.js`）

| 參數 | 用途 | 使用模式 | 選表條件 | 限制 | 模型／Config 欄位 |
| --- | --- | --- | --- | --- | --- |
| BG 選表權重 | 每局 BG 輪帶表 | NB／EB 每局一次 | `BG_Symbol` 9,698／`(2)` 19,298／`(3)` 6,110（A 版） | `(3)` 才有倍數球、不含 C1；EB 另乘 FG 機率倍數 | `Parameter!C4:C6` |
| FG 場次配置 | FG 每場輪帶表 | 觸發 15 場、Retrigger 5 場 | `FG_Symbol` 6＋`(2)` 9（加局 2＋3），打亂順序 | 總場次上限 50；`FG_Symbol (3)` 為 0 | `Parameter!C11:D13` |
| 輪帶／停輪權重 | 盤面符號 | 每次 Spin | 依所選表 | 每輪 63／64 格；同輪 C1 間距 ≥ 6 | 各 Symbol 表 `S:X`／`Z:AE` |
| Cascade 補牌 | 消除後補位 | 每次消除 | 沿同一條輪帶往上取 | 同輪不補第二顆 C1 | 程式規則 |
| 倍數等級 | C2／C3 倍數清單、C3 升級順序 | — | 25 級（2～1000、17 級以上 2500） | C3 最高 2500 | `Parameter!B18:C42` |
| C2 倍數權重 | C2 生成時的倍數 | 每顆 C2 | 依所在輪帶表 | BG 最高 1000x、FG 最高 2500x | `Parameter!K4:AI8` |
| C3 倍數權重 | C2 轉 C3 時的起始倍數 | 每顆轉換的 C3 | 依所在輪帶表 | A 版 BG 最高 100x、FG 最高 1000x | `Parameter!K14:AI18` |
| C2→C3（開局） | 開局 C2 轉 C3 機率 | 開局盤面 | 依開局 C2 總數 1～6+ | 分母 10,000 | `Parameter!K24:P28` |
| C2→C3（補牌） | 補牌 C2 轉 C3 機率 | Cascade 補牌 | 依 Combo 1～5+ | 分母 10,000 | `Parameter!K34:O38` |
| 賠率表 | Pay Anywhere 8~9／10~11／12+；C1 4／5／6 | 每次判獎 | — | 與 game_rule §4 一致 | `Overview!A30:I41` |
| FG 觸發／加局 | C1 數量 | BG 4+ 觸發 15 場；FG 3+ 加 5 場 | — | 上限 50 場 | `Overview!A22:C25` |
| Bet 模式 | NB 1x、EB 2x（FG 機率 5 倍）、BF 100x | — | — | BF 入場盤固定 4 顆 C1、給 3x | 基礎 Config metadata |

---

## §3. 卡片（倍率權重）系統（RTP 工作簿 `Multiplier_Weight` → `card_system`）

| 參數 | 用途 | 使用模式 | 選表條件 | 限制 | 模型／Config 欄位 |
| --- | --- | --- | --- | --- | --- |
| Newbie BG／FG 卡 | 新手結果分布 | NB／EB | `card_system_is_newbie = true` | BG 上限 30x、FG 30～120x | `Weight_*_BG/FG_Newbie` → `newbie.*` |
| 老手 BG 卡 | 老手 BG 結果分布（含 `free_game` 卡決定 FG 週期） | NB／EB | 依押注層級選 94／92／Bet100 | 小／中 Bet A 最高 (200,250]、B 最高 (1000,2000]；大 Bet A (120,140]、B (180,200] | `Weight_NB_BG`／`Weight_EB_BG` |
| 老手 FG 卡 | 老手 FG Session 分布 | NB／EB 觸發後 | 同上 | 小／中 Bet 20～20,000x；大 Bet 20～1,000x | `Weight_NB_FG`／`Weight_EB_FG` |
| BF 卡 | BF FG 分布 | BF | 依基礎押注層級 | 目標 FG 89.5%＋入場 3%、贏錢率 30% | `Weight_BF` |
| Retry Limit | 重抽上限 | 每張卡 | — | 10,000 次；超限保留最後一次結果 | `card_system.retry_limit` |

- 區間 `(min, max]`，倍率分母一律為 Normal Bet 基準成本；每欄總和 1,000,000,000。
- 觸發局 BG 上限：`free_game` 卡要求觸發局 BG ≤ 該卡組最高有權重區間上限，超過重抽。
- **老手 BG 權重計入重抽上限失敗**（7.4.0.0 起）：以有效均倍 `s_i·e_i + (1 − s_i)·F` 求解，使含重抽失敗後的 BG 命中 72%（EB 42%／94 版 39%）；`Multiplier_Weight × Avg_Multi` 的理想值因此略高於目標（見 `注意事項.md` 第 5 項、數學模型規範 2.4）。
- 目標 RTP：Oldhand NB 72:20（92）／72:22（94）、EB 42:50／39:55；Newbie 72:21（NB）、40.5:52.5（EB）；BF 92.5%。FG 週期 NB 1/450.83、EB 1/90.17。
- SCR：A／B 分版、NB／EB／BF 分群；Oldhand 小／中／大 Bet 共用中 Bet 代表值，Newbie 獨立（`OP Jackpot` 頁）。
