# H015192.xlsx → config.js 欄位對照

## Overview

- `B2` → `game_id`
- `B3` → `game_version`
- `A7` → `default_coin_in`
- `B11` → `normalbet`
- `B12` → `featurebuy`
- 第 26 列 `B:G` → `layout_visible`、`window_size`、`score_area`
- 第 69 列起 Scatter 場次表 → `free_spin_awards`
- 第 77 列起符號表 → `pay_table`、`symbol_id`、`symbol_str`

正式識別資料固定為 `parsheet_id=H0151`、中文名 `賞金列車`、英文名 `Wild Train`。

## Parameter

- 第 5 列 `C:M` → `value_multiplier_range`
- 第 10–11 列 → BG table 權重
- 第 16–17 列 → FG table 權重
- 第 22–23 列 → Buy Feature table 權重
- 第 28–29 列 → BG／FG 掉落表 A、B、C 選擇權重
- 第 34–45 列及其右側五個區塊 → BG／FG 各乘數階級的 Lightning 數量權重
- 第 50 列 `C:M` → FG 保底 Lightning 場次權重

## BG／FG／BF Symbol 工作表

適用工作表：`BG_Symbol`、`BG_Symbol (2)`、`FG_Symbol`、`FG_Symbol (2)`、`BF_Symbol`。

- `L:Q`：六輪輪帶符號
- `S:X`：符號 ID（核對用途，不是輪帶權重）
- `Z:AE`：六輪 stop 權重
- 掉落表 A：`AG` 符號、`AH:AM` 權重
- 掉落表 B：`AO` 符號、`AP:AU` 權重
- 掉落表 C：`AW` 符號、`AX:BC` 權重
- 四段 Cascade 資料起始列為 `6 / 29 / 52 / 75`，分別對應第 1、2、3、4+ 次補牌。

每段掉落表固定依 symbol ID 順序讀取 19 列；顯示標籤不可拿來當陣列索引，因為部分金框列會顯示其基礎符號名稱。

## 卡片系統

- `Multiplier_Weight_Newbie`：Normal Bet Newbie BG／FG 權重
- `Multiplier_Weight_Oldhand`：Normal Bet Oldhand BG／FG 與 Buy Feature 權重
- BG Range：第 15–78 列 `A:B` 區間、`L` 權重
- BG Free Game 卡：第 79 列 `L` 權重
- FG Range：第 87–150 列 `A:B` 區間、`L` 權重
- Buy Feature Range：Oldhand 第 157–220 列 `A:B` 區間、`L` 權重

轉換器會輸出 `card_system`、啟用狀態與 `retry_limit=5000`，供 Simulator 以結果篩選／重抽方式套用。

