# 目前金框倍數是怎麼決定的

目前 `Simulator.py` / `demogame` 的金框倍數決定方式，可以直接整理成這張表。

## 先講總規則

金框本身是從初始輪帶或 `drop_weight` 出來的。  
但金框上顯示的倍率，不是跟著輪帶帶出來，而是另外依情境抽權重。

可用的倍率權重有這幾組：

- `weight_cum_multiple_special`
- `weight_cum_multiple_r3_before`
- `weight_cum_multiple_r3_after`
- `weight_cum_multiple_before`
- `weight_cum_multiple_after`

倍率值本體來自：

- `value_multiplier_range`

## 現在實際使用情境

### 1. 被選成特殊格的金框

使用權重：`weight_cum_multiple_special`

條件：

- 先通過 `weight_special_pool`
- 只從記分區 `3x5` 的金框裡選 1 顆
- 被選中的那顆就用 `special`

### 2. 初始滾停時，在指定輪帶表的 `R3`，而且位於記分區 `3x5`

使用權重：`weight_cum_multiple_r3_before`

條件：

- 不是特殊格
- table 是 `BG_Symbol (2)`、`FG_Symbol`、`FG_Symbol (2)`、`FG_Symbol (3)`
- 欄位是 `R3`
- row 在記分區 `3x5`

### 3. 初始滾停時，在指定輪帶表的 `R3`，但位於最上排非記分區

使用權重：`weight_cum_multiple_r3_after`

條件：

- 不是特殊格
- table 是那 4 張特例表
- 欄位是 `R3`
- 但不在記分區 `3x5`

### 4. 初始滾停時，不屬於上面那種 `R3` 特例，而且位於記分區 `3x5`

使用權重：`weight_cum_multiple_before`

條件：

- 不是特殊格
- 不是指定輪帶表的 `R3`
- 在記分區 `3x5`

### 5. 初始滾停時，不屬於上面那種 `R3` 特例，而且位於最上排非記分區

使用權重：`weight_cum_multiple_after`

條件：

- 不是特殊格
- 不是指定輪帶表的 `R3`
- 在最上排非記分區

### 6. Cascade 後掉落補進來的金框，在指定輪帶表的 `R3`

使用權重：`weight_cum_multiple_r3_after`

條件：

- 這顆金框是掉落補進來的
- table 是那 4 張特例表
- 欄位是 `R3`

### 7. Cascade 後掉落補進來的金框，不屬於上面那種 `R3` 特例

使用權重：`weight_cum_multiple_after`

條件：

- 這顆金框是掉落補進來的
- 不是指定輪帶表的 `R3`

## Special Pool 的選取範圍

只從**記分區 `3x5` 的金框**中選。  
最上排非記分區金框不會被選成特殊格。

## R3 特例表

目前程式寫死的 table id 是：

- `1` = `B2` = `BG_Symbol (2)`
- `3` = `F1` = `FG_Symbol`
- `4` = `F2` = `FG_Symbol (2)`
- `5` = `F3` = `FG_Symbol (3)`
