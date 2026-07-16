# H015 Simulator 參數使用說明

## 前段設定

- `CONFIG_FILE`：數學設定檔，預設 `config.js`。
- `TOTAL_ROUNDS`：接受結果的模擬局數，預設 `10**7`。
- `BET_MODE`：`0` Normal Bet、`2` Buy Feature；其他值會明確拒絕。
- `BET_MULTI`：押注倍率。
- `CARD_SYSTEM_ENABLED`：卡片系統總開關。正式 RTP 驗證應保持開啟。
- `CARD_SYSTEM_IS_NEWBIE`：Normal Bet Profile；`True` 為 Newbie，`False` 為 Oldhand。
- `THREADS`：平行執行緒數。
- `OUTPUT_REPORT`：是否輸出 xlsx 報表。
- `SHOW_CONSOLE_SUMMARY` / `SHOW_CONSOLE_DETAIL`：固定摘要與遊戲明細顯示開關。
- `RUN_SINGLE_SPIN_DEBUG`：以 `DEBUG_ROUNDS` 執行最小流程檢查。

以上設定可用同名 `H015_` 環境變數覆寫。

## PowerShell 執行範例

在工作區根目錄執行 Oldhand Normal Bet 10 萬局：

```powershell
$env:PYTHONUTF8='1'
$env:H015_TOTAL_ROUNDS='100000'
$env:H015_BET_MODE='0'
$env:H015_CARD_SYSTEM_ENABLED='true'
$env:H015_CARD_SYSTEM_IS_NEWBIE='false'
py -3 '.\Project_AI\Slots\H015_賞金列車\Simulator.py'
```

只看 console、不輸出報表：

```powershell
$env:H015_OUTPUT_REPORT='false'
```

Buy Feature：

```powershell
$env:H015_BET_MODE='2'
```

## 卡片系統

- 權重來自 `Source/H015192.xlsx` 的 `Multiplier_Weight_Newbie` 與 `Multiplier_Weight_Oldhand`。
- Normal Bet 先抽 BG 卡；Range 卡要求 BG 不觸發 FG 且得分落在指定區間，Free Game 卡要求 BG 觸發 FG。
- 抽到 Free Game 卡後，FG 場次會依同一 Profile 的 FG Range 卡獨立重抽，BG 觸發盤不會跟著重抽。
- Buy Feature 使用 Oldhand 工作表的 Buy Feature Range 權重。
- 所有 Range 倍率皆以 Normal Bet 的 100 Credit 為分母；單一卡片最多重試 5000 次。
- 關閉卡片系統時顯示的是原始數學分布，不是 xlsx 卡片權重調整後的正式 RTP。
- 報表會列出 retry 總數、達上限次數與 BG Range／BG Free Game／FG 失敗分類；啟用卡片系統時檔名加 `_card`。

## 資料流與報表

`Source/H015192.xlsx` → `Tool/xlsx_to_config.py` → `config.js` → `Simulator.py` → `Record/*.xlsx`

報表至少包含 `Base Info`、`Hits`、`Pay`、`Eliminate`、`Multiplier Line`、`Record Data`。檔名以正式 PARsheet ID `H0151` 起頭，並包含版本、時間、模式、局數與卡片 Profile。

