# H013192 / H013194.xlsx → config JSON/JS 欄位對照

## 來源與輸出

- 唯一數學來源：`H013192.xlsx`、`H013194.xlsx`。
- `H013192.xlsx` → `config_92.js`。
- `H013194.xlsx` → `config_94.js`。
- `Overview!B2/B3` → `model`、`game_version`、`excel_version`。
- 正式識別固定為 `game_id=101001`、`parsheet_id=H0131`。
- 輸出仍使用 `window.H013_BOX_DATA = {...};`，內容為合法 JSON，供 Simulator 與 DemoGame 共用。

## Overview

- 第 6–9 列 → Normal / Extra / Feature Buy / Super Feature Buy 成本與 `rtp_targets`。
- 第 33 列 `B:G` → 6 軸可視高度、`window_size`、`reel_num`。
- Free Spins Setting → `free_spin_awards`。
- Retrigger Setting → `retrigger_awards`。
- 第 57 列起符號表 → `symbol_str`、`symbol_codes`、`symbol_id`、`pay_table`。
- 一般符號獎級固定對應 `8–9 / 10–11 / 12+`；C1 使用 `4 / 5 / 6`。

## Parameter

- `[A]`、第二組 `[A]` 與 `[B]` 全部保留在 `parameter_blocks`。
- 第一組 `[A]` 是舊 Simulator 的預設相容組：
  - Normal / Extra 選表權重 → `weight_table_normal_bet`、`weight_table_extra_bet`。
  - C2 倍率值 → `value_multiplier`。
  - FG / FB / SB 兩張表的倍率權重 → 六個 `weight_multiplier_*` 欄位。
- 權重會以最大公因數約分；抽選機率不變，可避免不必要的大整數。
- Free Game 高低表組合 → 初始 8 low + 2 high；Retrigger 依 5 場等比例轉為 4 low + 1 high。

## 13 張 Symbol 工作表

工作表順序：

1. `Base Game Symbol (1..4)`
2. `Extra Bet Symbol (1..3)`
3. `Free Game Symbol (1..2)`
4. `Feature Buy Symbol (1..2)`
5. `Super Feature Buy Symbol (1..2)`

- `L:Q` → 六軸輪帶符號。
- `AG:AL` → 六軸 stop weight。
- stop weight 轉為 `arr_reels_weight_cum`；原始資料另保留在 `strips[].weights`。
- `AN:AO` → 該 FG / FB / SB 工作表上的 C2 倍率與權重。
- `arr_reels`、`reels_len` 與舊 `strip_name_map` 會同步輸出，維持現有 Simulator / DemoGame 相容。

## Card System

- `Multiplier_Weight_Newbie`：Normal、Extra、Free Game。
- `Multiplier_Weight_Oldhand`：Normal、Extra、Free Game、Buy Feature、Super Feature。
- `A:B` → 倍率區間；`M` → 使用 A/B 表；`R` → 權重。
- FG Trigger 會輸出成 `type=free_game`；其餘輸出成 `type=range`。
- `card_system.enabled=true`、`retry_limit=5000`。

## 指令

```powershell
# 產生 config_92.js 與 config_94.js
python Tool/xlsx_to_config.py --all

# 驗證兩份輸出與 Excel 是否一致，不寫檔
python Tool/xlsx_to_config.py --all --check

# 單檔轉換或指定輸出
python Tool/xlsx_to_config.py --source Source/H013192.xlsx
python Tool/xlsx_to_config.py --source Source/H013192.xlsx --output config.js
```
