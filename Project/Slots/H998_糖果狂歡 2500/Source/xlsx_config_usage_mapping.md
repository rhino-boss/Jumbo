# H998192 / H998194.xlsx → config JSON/JS 欄位對照

## 來源與輸出

- 唯一數學來源：`H998192.xlsx`、`H998194.xlsx`。
- `H998192.xlsx` → `config_92.js`。
- `H998194.xlsx` → `config_94.js`。
- `Overview!B2/B3` → `model`、`game_version`、`excel_version`。
- 正式識別固定為 `game_id=101001`、`parsheet_id=H9981`。
- 輸出仍使用 `window.H998_BOX_DATA = {...};`，內容為合法 JSON，供 Simulator 與 DemoGame 共用。

## Overview

- 第 6–9 列 → Normal / Extra / Feature Buy / Super Feature Buy 成本與 `rtp_targets`。
- 正式模式成本依主 `Overview`：Normal `1x`、Extra `1.25x`、Feature Buy `100x`、Super Feature Buy `500x`。
- Description / Feature Buy Overview 中殘留的 Feature Buy `75x` 為舊版文字，不覆蓋主 `Overview`。
- 第 33 列 `B:G` → 6 軸可視高度、`window_size`、`reel_num`。
- Free Spins Setting → `free_spin_awards`。
- Retrigger Setting → `retrigger_awards`。
- 第 57 列起符號表 → `symbol_str`、`symbol_codes`、`symbol_id`、`pay_table`。
- 一般符號獎級固定對應 `8–9 / 10–11 / 12+`；C1 使用 `4 / 5 / 6`。

## Parameter

- `Parameter!A4:H43` 是由 `A3` 控制的動態預覽區：
  - `A3=1` 顯示 `A44:H83`。
  - `A3=2` 顯示 `A84:H123`。
- 正式來源只有 `A44:H83` 的 `[A]` 與 `A84:H123` 的 `[B]`；輸出的 `parameter_blocks` 只保留 `A`、`B`，不產生 `A_2`。
- A/B 不是獨立遊戲版本，而是由 Card System 每張卡的「使用的表」欄位在每局動態指定：
  - Normal / Extra 選表權重 → `weight_table_normal_bet`、`weight_table_extra_bet`。
  - C2 倍率值 → `value_multiplier`。
  - FG / FB / SB 兩張表的倍率權重 → 六個 `weight_multiplier_*` 欄位。
- 權重會以最大公因數約分；抽選機率不變，可避免不必要的大整數。
- `[A]` 的 Normal / Extra 選表權重為 `[1, 0, 0]`；`[B]` 為 `[0, 1, 0]`。
- `[A]` 的 Free Game 高低表組合為初始 8 low + 2 high；`[B]` 為 2 low + 8 high。
- Retrigger 依遊戲規則固定增加 4 low + 1 high，不跟著 A/B 初始比例改變。

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
- Newbie 只適用 Normal / Extra；Feature Buy / Super Feature 固定使用 Oldhand 卡片資料。
- `A:B` → 倍率區間；`M` → 使用 A/B 表；`R` → 權重。
- 工作表頂端的模式摘要不視為卡片表；各模式使用後段同名正式區塊的 `Lower / Upper` 資料。
- 卡片的 A/B 表別會在 Simulator 與 DemoGame 套用對應 `parameter_blocks` 的 BG 選表、FG 組合及 C2 權重。
- 正式模擬使用 `parameter_table=AUTO`；強制 A/B 僅供診斷，不是正式版本組合。
- FG Trigger 會輸出成 `type=free_game`；其餘輸出成 `type=range`。
- `card_system.enabled=true`；卡片未符合時會持續重抽，不設重抽上限。

## 指令

```powershell
# 產生 config_92.js 與 config_94.js
python Source/xlsx_to_config.py --all

# 驗證兩份輸出與 Excel 是否一致，不寫檔
python Source/xlsx_to_config.py --all --check

# 單檔轉換或指定輸出
python Source/xlsx_to_config.py --source Source/H998192.xlsx
python Source/xlsx_to_config.py --source Source/H998192.xlsx --output config_92_test.js
```
