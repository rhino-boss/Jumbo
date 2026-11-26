# H026 彩罐熱舞 1000（Pinata Beat 1000, 101014）Game Description

> 文件目的：說明遊戲模型參數的使用方式與各參數對應的實際遊戲功能（依《數學文件規範》§2.1）。
> 版本：`4.0.0.9`（`Source/01/version.txt`；模型與 Config 各層級 `excel_version` 同此版本）
> 一致性來源：`game_rule.md`、`Source/01/H026192A.xlsx`／`H026194A.xlsx`／`H026192A_Bet100.xlsx`、`config_01A.js`、`對外文件/101014_Math Document Description.md`
> 參數或選表邏輯更新時，本文件必須同步更新。

---

## §1. 模型檔案與資料所有權

| 檔案 | 押注層級 | 資料所有權 | Config |
| --- | --- | --- | --- |
| `Source/01/H026194A.xlsx` | 小 Bet | 盤面參數（`Parameter`、六張 BG／FG 輪帶表、`BF_Symbol`）＋卡片權重（`Multiplier_Weight`）＋ SCR（`OP Jackpot`） | `config_01A.js` → `tiers.94A` |
| `Source/01/H026192A.xlsx` | 中 Bet | 同上 | `config_01A.js` → `tiers.92A`（`default_tier`） |
| `Source/01/H026192A_Bet100.xlsx` | 大 Bet | 同上；與 92A 只差老手 FG 卡與 BF 卡的上限 | `config_01A.js` → `tiers.92A_Bet100` |
| `Source/01/H026192B.xlsx`／`H026194B.xlsx`／`H026192B_Bet100.xlsx` | — | B 版，凍結不再動 | 無（不載入） |

- 本作沒有獨立的基礎數學檔（`H0261.xlsx`），每份 RTP 工作簿都含完整盤面參數。
- **一個市場一份 Config**：`config_01A.js` 的 `base` 放三層共用欄位，`tiers[層級]` 只放該層不同的欄位（`card_system`、版本資訊；94A 另含 `BF_Symbol` 的輪帶與補牌權重）。Simulator 與 Demogame 一律以 `base` 疊上 `tiers[層級]` 展開（淺層覆蓋、`source` 不疊入）；Simulator 以 `CONFIG_TIER`（或環境變數 `H026_CONFIG_TIER`）指定層級。
- 層級規則（`config_01A.js` → `tier_rule`）：小 Bet 94A（NB／EB 實際押注未滿 $2；BF 看底注）、大 Bet 92A_Bet100（底注超過 $100）、其餘中 Bet 92A。

---

## §2. 盤面參數（RTP 工作簿 → `config_01A.js` 的 `base`）

三份 A 版工作簿的盤面參數相同（94A 的 `BF_Symbol` 例外，見 §2.3）。

### 2.1 Overview

| 參數 | 用途 | 使用模式 | 選表條件 | 限制 | 模型／Config 欄位 |
| --- | --- | --- | --- | --- | --- |
| Base Bet／Coin In | 押注基準 | 所有統計以「得分 ÷ Coin In」計 | NB 1x、EB 2x、BF 75x | 卡片判定的 Coin In 一律用 NB 基準（EB、BF 亦同） | `Overview!A7`、`A10:D13` → `default_coin_in`、`normalbet`、`extrabet`、`featurebuy` |
| 盤面尺寸 | 輪數與記分列數 | 每次 Spin | — | 5 輪 × 3 列記分；程式另持有 1 列不記分的預覽列 | `Overview!A30:F31` → `reel_num`、`window_size` |
| Free Spins Setting | FG 觸發與加局場次 | 連消結束後最終盤面記分區 C1 數 | 3／4／5 個 C1 → 12／14／16 場（BG 觸發與 FG 加局相同） | 單次 FG 含加局最多 50 場 | `Overview!A35:C39` → Simulator `FG_TRIGGER_BASE_SPINS`、`FG_EXTRA_SPINS_PER_SCATTER`、`FG_SPIN_CAP` |
| Pay Table | 線獎賠率（100 credit 押注） | 每次判獎 | 3／4／5 連 | 與 `game_rule.md` §4 一致（line pay × 100）；`WW`、`C1` 無賠率；`G1`～`GJ` 與基底符號相同，程式判獎只用基底符號 | `Overview!A42:F62` → `pay_table`、`symbol_str`、`base_symbol_of`、`is_gold_symbol`、`is_score_symbol` |

### 2.2 Parameter

| 參數 | 用途 | 使用模式 | 選表條件 | 限制 | 模型／Config 欄位 |
| --- | --- | --- | --- | --- | --- |
| Line | 20 條固定線 | 每次判獎 | 每列 5 個數字＝R1～R5 取記分區第幾列（0 上、1 中、2 下） | 由 R1 起連續；每線只取最高獎 | `Parameter!B4:G24` → `paylines` |
| Table Selection Weight - Base Game | BG 每局輪帶表 | 每次 BG Spin 第一步抽一次 | `BG_Symbol` 7,000／`BG_Symbol (2)` 1,000／`BG_Symbol (3)` 2,000 | 只有 `BG_Symbol (3)` 可湊出 FG 觸發 | `Parameter!I4:J7` → `weight_table_bg` |
| FG 輪帶表切換 | FG 每場輪帶表 | 每場 FG 依當前累積倍數 | < 10 → `FG_Symbol`；< 20 → `FG_Symbol (2)`；≥ 20 → `FG_Symbol (3)` | FG 無選表權重 | 程式規則（`Description` 8.1）→ `fg_table_rule` |
| Multiplier Range | 金框倍數清單（索引表） | 抽倍數時先抽索引再換值 | 0、2、3、5、8、10、15、20、25、50、100、500、1000 | `0`＝金框不帶倍數 | `Parameter!I25:I38` → `value_multiplier_range` |
| Used Special Pool Weight | 特殊倍數池是否啟用 | 開局分配倍數時判定一次 | 依記分區金框數（1～9，9 個以上用第 9 欄）與本局輪帶表查權重 | 分母 10,000；一局最多 1 顆金框吃特殊池；預覽列與補牌金框不參與 | `Parameter!AC4:AL11` → `weight_special_pool`、`special_pool_weight_base` |
| Multiple Selection Weight - Special Pool | 命中特殊池那顆金框的倍數 | 同上 | 依本局輪帶表 | 欄位對應 Multiplier Range | `Parameter!N4:AA11` → `weight_multiple_special` |
| Multiple Selection Weight - Before Eliminate | 開局記分區金框的倍數 | 開局 | 非 R3，或該表不走 R3 專用組 | 同上 | `Parameter!N37:AA44` → `weight_multiple_before` |
| Multiple Selection Weight - After Eliminate | 開局預覽列金框、Cascade 補入金框的倍數 | 開局（預覽列）／每次補牌 | 同上 | 同上 | `Parameter!N48:AA55` → `weight_multiple_after` |
| Multiple Selection Weight - Reel3 Before Eliminate | R3 整輪金框表的 R3 開局記分區倍數 | 開局 | 只限 `BG_Symbol (2)` 與三張 FG 表的 R3 | 同上 | `Parameter!N15:AA22` → `weight_multiple_r3_before` |
| Multiple Selection Weight - Reel3 After Eliminate | 同上表的 R3 預覽列、R3 補入金框倍數 | 開局（預覽列）／每次補牌 | 同上 | 同上 | `Parameter!N26:AA33` → `weight_multiple_r3_after` |
| Eliminate Table Weight | 本局補牌用 A 或 B 組 | 每次 Spin 開局抽一次，整個連消過程不換 | BG／FG 各一組權重 | 目前 BG、FG 皆為 A 10：B 0（只用 A 組） | `Parameter!I41:K44` → `eliminate_table_weight_bg`／`_fg`（`eliminate_table_weight_bf` 同為 A 10：B 0，模型無對應列） |

- 各 Multiple Selection Weight 區塊最右欄（`AB`）為設計參考的平均倍數，程式不讀取。
- 倍數選用順序：命中特殊池 → Special Pool；否則 R3 且該表走 R3 專用組 → Reel3 Before（記分區）／Reel3 After（預覽列）；其他 → Before（記分區）／After（預覽列）。Cascade 補入的金框一律走 After（R3 專用表的 R3 走 Reel3 After）。

### 2.3 輪帶表（`BG_Symbol`、`BG_Symbol (2)`、`BG_Symbol (3)`、`FG_Symbol`、`FG_Symbol (2)`、`FG_Symbol (3)`、`BF_Symbol`）

| 參數 | 用途 | 使用模式 | 選表條件 | 限制 | 模型／Config 欄位 |
| --- | --- | --- | --- | --- | --- |
| `Symbol ID R1~R5` | 輪帶內容（代號 0～19） | 每次 Spin 停輪 | 依本局輪帶表 | 每輪 200 格；不含 `WW` | 各表 `Q4:U203` → `arr_reels`、`reels_len` |
| `Symbol Weight R1~R5` | 停輪位置權重 | 每次 Spin 停輪 | 同上 | 權重屬「位置」而非符號；停輪後取連續 4 格（含預覽列） | 各表 `W4:AA203` → `arr_reels_weight` |
| `Eliminate Wheel Weight A／B` | Cascade 補牌權重（符號 × 輪） | 每次消除後補空位 | 依 Eliminate Table Weight 選 A／B | 與輪帶無關、重新抽樣；同輪已有 C1 時抽到 C1 重抽；版面分 1 Combo／2 Combo／3+ Combo 三區，程式取 2 Combo 區（三區目前數值相同） | 各表 `AC` 起／`AJ` 起 → `drop_weight_a`／`drop_weight_b` |

| 輪帶表 | 角色 | Config 索引 |
| --- | --- | --- |
| `BG_Symbol` | 一般局；金框只在 R2～R4 | 0（`B1`） |
| `BG_Symbol (2)` | 全金框局；R3 整輪金框且走 R3 專用倍數組 | 1（`B2`） |
| `BG_Symbol (3)` | 觸發 FG 局；C1 分布在 5 輪；特殊池權重為 0，Before／After 倍數組只有 x2～x8 | 2（`B3`） |
| `FG_Symbol`／`(2)`／`(3)` | FG 三張表，依累積倍數切換；R3 整輪金框且帶倍數、不含 C1 | 3／4／5（`F1`～`F3`） |
| `BF_Symbol` | Buy Feature 進場 Spin（`scene_bf`）；重抽到最終盤面 ≥ 3 個 C1 | 6（`BF`）；94A 的輪帶與補牌權重與 92A 不同，存在 `tiers.94A` |

---

## §3. 遊戲流程與參數使用時點

1. **選表**：BG 依 Table Selection Weight 抽表；FG 依累積倍數切表；BF 進場用 `BF_Symbol`。
2. **選補牌組**：依 Eliminate Table Weight 抽 A／B（本 Spin 固定）。
3. **停輪**：各輪依 `Symbol Weight` 抽停輪位置，取連續 4 格展開成 4 × 5 盤面（最上列為預覽列）。
4. **分配倍數**：先判定特殊池，再依位置與時機選倍數組（§2.2）。
5. **連消迴圈**：判 20 線 → 無獎即結束 → 累加線獎 → 中獎金框收集倍數並在原位轉成 `WW`，其他中獎符號清除 → 剩餘符號下墜、空位依補牌權重補入（新金框依位置抽倍數；同輪已有 C1 不再補 C1）→ 重新判獎。
6. **結算倍數**：本 Spin 有收集到大於 0 的倍數時，累積倍數一次乘上本 Spin 線獎總和；否則不乘。
7. **FG 判定**：最終盤面記分區 C1 ≥ 3 觸發（或加局），場次見 §2.1。FG 累積倍數跨場保留、整段 FG 結束才清除，並決定下一場用哪張表；加局不清除累積倍數。

---

## §4. 卡片（倍率權重）系統（RTP 工作簿 `Multiplier_Weight` → `tiers[層級].card_system`）

卡片系統先抽卡決定這一局的目標得分區間，再重抽整局直到符合；不改變盤面機率與判獎、派彩公式。

| 參數 | 用途 | 使用模式 | 選表條件 | 限制 | 模型／Config 欄位 |
| --- | --- | --- | --- | --- | --- |
| Newbie NB BG／FG 卡 | 新手 NB 結果分布 | NB | `card_system_is_newbie = true` | BG 最高有權重區間 (25, 30]；FG (90, 100] | `Multiplier_Weight!C:D`（`Weight_NB_BG`／`Weight_NB_FG`，Newbie）→ `newbie.normal_bet.weight_bg`／`weight_fg` |
| Newbie EB BG／FG 卡 | 新手 EB 結果分布 | EB | 同上 | BG (40, 45]；FG (90, 100] | `Multiplier_Weight!E:F` → `newbie.extra_bet.*` |
| 老手 NB BG／FG 卡 | 老手 NB 結果分布 | NB | 老手；依押注層級選 94A／92A／92A_Bet100 | BG (100, 120]；FG 94A／92A (10000, 20000]、92A_Bet100 (950, 1000] | `Multiplier_Weight!G:H` → `oldhand.normal_bet.*` |
| 老手 EB BG／FG 卡 | 老手 EB 結果分布 | EB | 同上 | 同老手 NB | `Multiplier_Weight!I:J` → `oldhand.extra_bet.*` |
| BF 卡 | BF 結果分布 | BF | 同上 | 94A／92A (10000, 20000]、92A_Bet100 (950, 1000]；判定 BF 進場 Spin＋FG 的合計得分 | `Multiplier_Weight!K`（`Weight_BF_FG`）→ `oldhand.buy_feature.weight_fg` |
| Retry Limit | 重抽上限 | 每局 | — | 5,000 次；超限時 `Simulator.py` 保留最後一次結果並計入 `retry_limit_exceeded` | `card_system.retry_limit` |

- 區間 `(min, max]`，左開右閉，倍率＝得分 ÷ NB Coin In；`Multiplier_Weight` 列 4～67 為 64 個得分區間，列 68 為 `Free Game` 卡。
- **BG 卡組含 `free_game` 卡**：抽到時重複 BG Spin 直到最終盤面 C1 ≥ 3，再抽一張 FG 卡、重抽整段 FG 直到總得分落在該卡區間。抽到區間卡時，觸發 FG 或得分不在區間內都整局重抽，因此 **FG 週期完全由 `Free Game` 卡權重決定**：NB 4,195,668／1,000,011,437（週期 238.34）、EB 20,978,340／1,000,361,591（週期 47.69），三層相同。
- FG 卡組沒有 `free_game` 卡；FG 重抽以整段 FG 為單位。
- 推導工作表：`Multiplier_Weight_Oldhand`、`Multiplier_Weight_Newbie`（自然機率、調整係數、目標值；程式不讀取）。
- 目標 RTP（`Overview`／`Multiplier_Weight_*` 第 7～8 列）：

| 層級 | Profile | NB BG | NB FG | NB Total | EB BG | EB FG | EB Total | BF |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 94A | 老手 | 68.00% | 26.00% | 94.00% | 32.02% | 61.98% | 94.00% | 92.50% |
| 92A | 老手 | 68.00% | 24.00% | 92.00% | 32.02% | 59.98% | 92.00% | 92.50% |
| 92A_Bet100 | 老手 | 68.00% | 24.00% | 92.00% | 32.02% | 59.98% | 92.00% | 92.50% |
| 三層共用 | Newbie | 68.00% | 25.00% | 93.00% | 30.52% | 62.48% | 93.00% | — |

---

## §5. OP Jackpot 參數（RTP 工作簿 `OP Jackpot` 頁）

| 參數 | 用途 | 使用模式 | 選表條件 | 限制 | 來源欄位 |
| --- | --- | --- | --- | --- | --- |
| Threshold | SCR 分母 | — | — | 10,000,000,000 | `OP Jackpot!C2` |
| SCR | 含 ≥ 1 個 C1 的 Spin 率，供彩金模組換算判定機率 | 彩金模擬 | Newbie NB／EB、Oldhand NB／EB／BF 分列 | 口徑＝C1 cnt ÷ 付費局數 × Threshold（BG Spin 與每場 FG Spin 各算一次）；Newbie 三層同值；92A_Bet100 與 92A 同值 | `OP Jackpot!B4:G15` |

| Status | Bet Type | 94A | 92A | 92A_Bet100 |
| --- | --- | --- | --- | --- |
| Newbie | Normal Bet | 3,368,441,800 | 3,368,441,800 | 3,368,441,800 |
| Newbie | Extra Bet | 3,830,983,800 | 3,830,983,800 | 3,830,983,800 |
| Oldhand | Normal Bet | 3,371,218,200 | 3,370,654,300 | 3,370,654,300 |
| Oldhand | Extra Bet | 3,830,025,700 | 3,829,976,500 | 3,829,976,500 |
| Oldhand | Buy Feature | 30,000,858,400 | 30,000,858,400 | 30,000,858,400 |

- 彩金的獎項、池底與貢獻率屬平台 OP Jackpot 模組，不在本模型內；送驗版 Bonus／Link RTP 依《送驗文件規範》§2.1.1 取自 `Slots/OP Jackpot/JP0100B`（92 版）／`JP0100C`（94 版）。

---

## §6. 押注參數

| 參數 | 用途 | 使用模式 | 選表條件 | 限制 | Config 欄位 |
| --- | --- | --- | --- | --- | --- |
| `bet_mode` | 押注模式 | 每批次 | 0＝Normal Bet、1＝Extra Bet、2＝Buy Feature | EB 與 NB 共用同一套盤面參數，只換卡片組 | `mode_normalbet`、`mode_extrabet`、`mode_featurebuy` |
| 押注倍數 | NB 1x、EB 2x、BF 75x | 計算成本 | — | 卡片判定一律以 NB Coin In 為分母 | `normalbet`、`extrabet`、`featurebuy` |
| 場景 | BG／FG／BF 進場 Spin | 選表與補牌組 | 0＝BG、1＝FG、2＝BF | — | `scene_bg`、`scene_fg`、`scene_bf` |
| 押注層級 | 選 94A／92A／92A_Bet100 | 每批次 | 見 §1 層級規則 | — | `default_tier`、`tier_rule`、Simulator `CONFIG_TIER` |

---

## §7. 待確認事項（文件與模型不一致，未自行決定）

1. 模型 `Description` 工作表 7.3、8.4 寫 FG 次數「15 + (scatter_count − 3) × 2」（15／17／19 場）；`Overview`、`game_rule.md`、`Simulator.py` 皆為 12／14／16 場。
2. `game_rule.md` §5A、§9.2.4 寫「Extra Bet 下金框倍數套用調整後的配置」；模型與 `config_01A.js` 沒有 EB 專用的倍數權重，`Simulator.py` 的 EB 只換卡片組。
3. `H026192A_Bet100.xlsx` 的 `Multiplier_Weight_Oldhand` 目標列寫 FG 上限 20000；該檔 `Multiplier_Weight` 與 `tiers.92A_Bet100` 實際最高有權重區間為 (950, 1000]。
4. `config_01A.js` 的 `description` 與各層 `source` 寫 `Source/01/H026xxx.xlsx`；模型實際放在 `Source/`。
5. `101014_Math Document Description` 1-9 寫 `BG_Symbol (3)`「金框倍數配置為零」；`Parameter` 中該表只有特殊池（與 R3 專用組，該表不使用）為 0，Before／After 組仍有 x2～x8。
6. 同文件 4-3 寫重抽達上限時「放棄該局」；`Simulator.py` 實作為保留最後一次結果並計數。
