# H013197.xlsx → config.js 欄位對照

## 識別資料

- 正式 Game ID：`101001`。
- 正式 PARsheet ID：`H0131`。
- 中文／英文名：`糖果狂歡 1000`／`Sugar Bonanza 1000`。
- `overview!B1`：舊數學識別碼 `H013197-0.0.0.4`，保留為 `source_game_id`。
- `overview!B2`：數學版本 `0004`。

## 盤面與賠率

- 固定盤面：6 輪 × 5 列。
- `pay_table`：`Symbol`、`4/5/6/8/10/12` 與 `Id` 轉成 `symbol_str`、`symbol_id`、`pay_awards`、`pay_table`。
- 一般符號 `M1~M4/A/K/Q/J/TE` 以全盤面顆數 `8-9/10-11/12+` 判獎。
- `C1` 以 4／5／6 顆支付並觸發 FG；`C2` 為 FG 倍數符號。

## Reel Strip 與 Stop Weight

以下 13 組輪帶與同名 `_weight` 工作表依序映射：

1. `BG_strip`、`BG_strip (2)`、`BG_strip (3)`、`BG_strip (4)`
2. `EB_strip`、`EB_strip (2)`、`EB_strip (3)`
3. `FG_strip`、`FG_strip (2)`
4. `FB_strip`、`FB_strip (2)`
5. `SB_strip`、`SB_strip (2)`

每張表 `R1:R6` 轉為 `arr_reels`；stop weight 轉為逐輪累積的 `arr_reels_weight_cum`。空白輪帶補 `-1`，空白權重補 `0`，不會形成可抽選 stop。

## Table 與倍數權重

- `weight.table_normal_bet`：Normal Bet 的 BG A/B/C 表選擇權重。
- `weight.table_extra_bet`：Extra Bet 的 EB A/B/C 表選擇權重。
- `value.multiplier_range`：C2 可抽倍率值。
- `weight.multiplier_range_FG_low/high`：自然 FG 低／高表倍率權重。
- `weight.multiplier_range_FB_low/high`：Feature Buy 低／高表倍率權重。
- `weight.multiplier_range_SB_low/high`：Super Feature Buy 低／高表倍率權重。

## 固定流程參數

- 初始 FG：8 場低表 + 2 場高表。
- Retrigger：4 場低表 + 1 場高表。
- 單次 FG 上限：50 場。
- 模式：0 Normal、1 Extra、2 Feature Buy、3 Super Feature Buy。
- 成本：1x、1.25x、75x、500x。

## 已知來源差異

官方遊戲清單的 BF 欄是 100x，舊數學檔與舊 Simulator 是 75x。本專案為可重現舊數學採 75x，並在 `config.js` 的 `source_conflicts` 保留差異。
