# C027 Game Description — 模型參數使用說明

> 對應數學模型：`Source/C0271.xlsx`（基礎，版本 `0`）、`Source/C027192A.xlsx`／`Source/C027194A.xlsx`（版本 `0.0.0.0`）
> 對應 Config：`config.js`、`config_92A.js`、`config_94A.js`
> 規則來源：`game_rule.md`
> 撰寫日期：2026-08-25

本文件說明 C027 的模型參數怎麼用、選表條件是什麼、以及每個欄位對應到遊戲的哪個功能。內容必須與數學模型的 `Gaem Description` 工作表、`game_rule.md` 及 Config 一致。

---

## 1. Config 分工

| 檔案 | 對應 XLSX | 版本格式 | 內容 |
|---|---|---|---|
| `config.js` | `Source/C0271.xlsx` | 1 碼（`0`） | 輪帶、掉落表、Paytable、Feature 參數、場景混合權重 |
| `config_92A.js` | `Source/C027192A.xlsx` | 4 碼（`0.0.0.0`） | 倍率權重與 Card System；Game RTP 92% 家族 |
| `config_94A.js` | `Source/C027194A.xlsx` | 4 碼（`0.0.0.0`） | 倍率權重與 Card System；Game RTP 94% 家族 |

Runtime 由 `Simulator.py` 的 `merge_runtime_config()` 合併：**自然機率（輪帶、掉落、選表）一律取 `config.js`**，只有 `c2`、`c3`、`use_super_multiplier` 與 `card_system` 取自 RTP／Variant Config。RTP Config 不得改變 `config.js` 定義的盤面與自然機率邏輯。

---

## 2. 輪帶表（`strip_names` / `strips`）

| 表名 | 使用模式 | 選表條件 | 限制 |
|---|---|---|---|
| `BF_Symbol` | Buy Feature 入口 | `parameter.featurebuy.base_reel_names` 唯一項 | R2～R5 強制停在含 C1 的視窗；每 5 格視窗內同一般符號不重複；不配置 C2 |
| `BG_Symbol` | Normal／Extra Bet | 依 `parameter.normal.base_reel_weights` 逐轉抽選 | 場景 A：有 C2、聚集度高 |
| `BG_Symbol (2)` | Normal／Extra Bet | 同上 | 場景 B：無 C2、聚集度低 |
| `FG_Symbol` | 自然觸發 FG | 依 `parameter.normal.free_table.weights` 逐免費轉抽選 | 場景 A：有 C2 |
| `FG_Symbol (2)` | 自然觸發 FG | 同上 | 場景 B：無 C2 |
| `FG_Symbol (3)` | Buy Feature FG | 依 `parameter.featurebuy.free_table.weights` 逐免費轉抽選 | 場景 A：有 C2 |
| `FG_Symbol (4)` | Buy Feature FG | 同上 | 場景 B：無 C2 |

每張表的欄位：

| 欄位 | 說明 |
|---|---|
| `symbols` | 輪帶格位，`[row][reel]` 的符號 ID；長度 = `reel_lengths[0]` |
| `weights` | 停輪點權重，C027 固定為 1（均勻停輪） |
| `drop_weights` | 掉落補牌權重，`[symbol_index][reel]`；每輪合計 1,000,000 |
| `reel_lengths` | 各輪帶長度，六輪等長 |
| `linked_stop_weight` / `linked_stop_denominator` / `linked_stop_offsets` | 連動停輪；C027 未使用，權重為 0 |

同一場景的兩張子表**共用同一份掉落邊際**，因此掉落分布與混合權重無關。

---

## 3. 場景表混合（Scene Mixture）

| 參數 | 位置 | 說明 |
|---|---|---|
| `base_reel_names` / `base_reel_weights` / `base_reel_weights_cum` | `parameter.<profile>` | BG 每一付費轉的抽表權重 |
| `free_table.names` | `parameter.<profile>` | 該 Profile 的 FG 場景子表清單 |
| `free_table.weights` | `parameter.<profile>` | **有正權重時啟用逐轉抽表**；每一次免費 Spin 獨立抽一張子表 |
| `free_table.initial_spins` / `retrigger_spins` | `parameter.<profile>` | 逐轉抽表模式下的初始／加局場次（15／5） |
| `free_table.initial` / `retrigger` | `parameter.<profile>` | 舊的「每張表固定場次」排程；只有在 `weights` 全為 0 時才生效 |
| `scene_mixture` | Config 根層 | 求解紀錄：各場景的子表名稱、混合權重、A 表 C2 格數、聚集度 θ |

Runtime 對應：`Simulator.schedule_free_spins()` 與 `index.html` 的 `buildFreeSchedule()`。兩邊必須同時支援兩種模式，並以 `weights` 是否有正值決定走哪一條。

---

## 4. 倍數符號參數

| 參數 | 位置 | 說明 |
|---|---|---|
| `multiplier_levels` | Config 根層 | C3 的升級階梯，也是 C2／C3 抽取權重的欄位順序。重複值（2500x 平台）只有第一個欄位可帶權重 |
| `multiplier_max_value` | Config 根層 | 單顆倍數符號上限 2500 |
| `c2.multipliers` / `c2.weights[表名]` | `parameter.<profile>` | C2 一般倍率池；**只允許 8x 以下的值帶權重** |
| `c3.multipliers` / `c3.weights[表名]` | `parameter.<profile>` | 每場景的 Super Multiplier 池；**只允許 10x 以上的值帶權重** |
| `super_multiplier.weights["Super Ball"]` | `parameter` | 全域 C3 權重；只有在該場景的 `c3` 權重全為 0 時才作為 fallback |
| `use_super_multiplier.weights_by_initial_ball_count[表名]` | `parameter.<profile>` | 萬分比。欄位為「該次 Spin 初始盤面倍數球顆數 1～6」，決定候選 C2 轉為 C3 的機率；依規則必須隨顆數遞增 |
| `use_super_multiplier.denominator` | `parameter.<profile>` | 上述權重的分母，固定 10,000 |

抽取流程（`Simulator.prepare_multiplier_symbol()`）：輪帶／掉落表只產生候選符號 C2 → 依 `use_super_multiplier` 該表該顆數欄位決定是否轉為 C3 → 從對應的池抽初始倍率。初始盤面 0 顆但 Cascade 後掉入時使用「1 顆」欄位。

升級流程（`Simulator.upgrade_c3_value()`）：每次中獎消除，消除前已在盤面的 C3 各沿 `multiplier_levels` 往後一格；到 2500x 後維持。

---

## 5. Card System 參數

| 參數 | 說明 |
|---|---|
| `card_system.enabled` | 是否啟用；Off 時不抽卡、不重跑 |
| `card_system.retry_limit` | 固定 10000 |
| `card_system.<profile>.<mode>[.<tier>].weight_bg` | BG 卡片清單（`range` ＋ 一張 `free_game`） |
| `card_system.<profile>.<mode>[.<tier>].weight_fg` | FG／Feature 整包卡片清單 |
| 卡片 `min` / `max` | 倍率區間 `(min, max]`，分母為 Normal Bet 基準成本 |
| 卡片 `type` | `range` 或 `free_game`；`free_game` 要求該把必須觸發 FG 且 BG 倍率不超過 BG Trigger Cap |
| 卡片 `ball` | **C027 新增**：`any`（預設）／`with`（最終盤面必須有 C2 或 C3）／`without`（必須沒有） |
| 卡片 `combo_min` / `combo_max` | **C027 新增**：接受結果的 Cascade 次數下／上限；`-1` 表示不限制。本版保留欄位但未啟用 |
| `card_system.calibration` | 校準紀錄：RTP 拆分規則、目標值、`ball_share`、`ball_split_max`、FG 線型來源、使用的自然基準報表 |

`ball` 與 `combo_*` 只是接受條件，不會修改輪帶、Paytable 或 Feature 流程。Runtime 對應 `Simulator.is_card_shape_match()` 與 `index.html` 的 `cardShapeMatches()`。

`ball_split_max` 說明：只有得分 ≤ 該倍率的區間卡才拆成 with／without 一對。超過該倍率的獎金在本模型幾乎必然伴隨倍數球，若對高區間要求「不可有球」會打到 Retry Limit 並破壞 RTP。

---

## 6. RTP 與押注參數

| 參數 | 說明 |
|---|---|
| `normalbet` / `extrabet` / `featurebuy` | 各模式的成本倍率（1／2／100） |
| `default_coin_in` / `denom` | Coin In 基準與面額，用於換算 `bet_multi` |
| `bet_tier_thresholds` | 小／中／大 Bet 門檻（`< $2`、`<= $100`） |
| `link.enabled` | Link 資格；Oldhand 小 Bet 與 Newbie 為 false |
| `rtp_accounting` | Link／Bonus Game／Game 三段的歸類：Bonus Game = Free Game、Game = Base Game、Link = none |
| `rtp_label`（RTP Config） | 該家族的 Game RTP 標籤（92／94） |
| `extra_fg_probability_multiplier` | Extra Bet 的 FG 觸發倍率目標（5）。⚠️ 目前以「最多五次觸發機會」近似，尚未配置專用輪帶與卡片 |

RTP 拆分規則：總 RTP = 版本標籤；BG:FG 依競品實測比例 `70.616% : 29.384%` 縮放。此規則寫在 `card_system.calibration.rtp_split_rule`。

---

## 7. 重建流程

```text
Source/*.xlsx  ──(既有轉檔工具)──▶ config.js / config_92A.js / config_94A.js
                                        │
其他/fit_c027_model.py --strips ────────┤ 解場景混合，重寫七張輪帶表與倍率權重
其他/fit_c027_model.py --cards  ────────┤ 跑自然基準並校準 Card System
其他/tune_c027.py               ────────┤ 用 Card-On 樣本解 ball_share 與 BG RTP 補償量
其他/verify_c027.py             ────────┤ 產出正式六份 Record 報表
其他/build_c027_report.py       ────────┘ 產出 遊戲數據_C027_奧林帕斯 2500.md／.html
其他/reconcile_demogame.mjs     ───────── Demogame 與 Simulator headless 對帳
其他/score_competitor_match.py  ───────── 逐指標與競品評分
```

`fit_c027_model.validate_config()` 會在寫入前擋下下列違規：輪帶表名稱或數量不符、`Symbol Weight` 不為 1、掉落權重不等於 1,000,000、C1 循環間距小於 6、`BF_Symbol` 的視窗重複一般符號或帶有 C2、C2 池出現 ≥10x、C3 池出現 <10x。
