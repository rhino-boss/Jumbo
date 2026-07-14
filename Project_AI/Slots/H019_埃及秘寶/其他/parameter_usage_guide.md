# H019 Simulator 參數使用說明

## 前段設定

- `CONFIG_FILE`：預設 `config_92.js`，可切換成 `config_94.js`。
- `TOTAL_ROUNDS`：模擬局數，預設 100,000。
- `BET_MODE`：`0` Normal、`2` Buy Feature、`3` Super Feature。
- `BET_MULTI`：押注倍率。
- `CARD_SYSTEM_ENABLED`：卡片系統總開關；`True` 開啟、`False` 關閉。
- `CARD_SYSTEM_IS_NEWBIE`：Normal Bet 使用者 Profile；`True` 為 Newbie，`False` 為 Oldhand。
- `THREADS`：ThreadPool 執行緒數。
- `OUTPUT_REPORT`：是否輸出 xlsx 報表。
- `SHOW_CONSOLE_SUMMARY` / `SHOW_CONSOLE_DETAIL`：摘要與明細顯示。
- `RUN_SINGLE_SPIN_DEBUG`：單局檢查模式。
- `RUN_ALL_COMBINATIONS`：依 `BATCH_COMBINATIONS` 執行多組版本／模式。

設定可用同名 `H019_` 環境變數覆寫，適合 PowerShell 或 VS Code Interactive Window。

## PowerShell 執行範例

在 `C:\Users\rhinshen\Mine\個人工作區\2_Program` 執行：

```powershell
$env:PYTHONUTF8='1'
$env:H019_TOTAL_ROUNDS='100000'
$env:H019_CONFIG_FILE='config_92.js'
$env:H019_BET_MODE='0'
$env:H019_CARD_SYSTEM_ENABLED='true'
$env:H019_CARD_SYSTEM_IS_NEWBIE='false'
.\.venv\Scripts\python.exe '.\Project_AI\Slots\H019_埃及秘寶\Simulator.py'
```

只看 console、不輸出報表：

```powershell
$env:H019_OUTPUT_REPORT='false'
```

模式值：

- `0`：Normal Bet，單局成本 100 Credit。
- `2`：Buy Feature，單局成本 10,000 Credit。
- `3`：Super Feature，單局成本 50,000 Credit。

## 資料流

`Source/H019192.xlsx` 或 `H019194.xlsx` → `Source/xlsx_to_config.py` → `config_92.js` 或 `config_94.js` → `Simulator.py` → `Record/*.xlsx`

報表檔名以前綴 `H0191`（PARsheet ID）命名；版本移除標點，例如 `3.0.0.1` 寫成 `3001`，10 的整數次方局數以 `10+指數` 表示，例如 `10**5` 寫成 `105`。範例：`H0191_3001_2607141633_betmode0_105_oldhand_card.xlsx`。程式可從檔案、終端機或 VS Code Interactive Window 執行，會自行尋找遊戲資料夾。

## 卡片系統

- 前段 `CARD_SYSTEM_ENABLED` 是執行開關；同樣可用 `H019_CARD_SYSTEM_ENABLED=true/false` 覆寫。
- config 的 `card_system.enabled` 也必須為 `true` 才會實際啟用，權重來自 xlsx `Multiplier_Weight`。
- Normal Bet 可用 `H019_CARD_SYSTEM_IS_NEWBIE=true/false` 切換 Newbie／Oldhand。
- Buy／Super 固定使用 `Weight_BF_FG`／`Weight_SF_FG`。
- 同一張卡不符合時重跑，最多 5000 次。
- 報表顯示 retry 統計；啟用時檔名以 `_card` 結尾。
- 卡片倍率以 Normal Bet 的 100 Credit 為分母，即使實際模式是 100× 或 500× 購買功能。

批次模式每筆可獨立設定：

```python
{
    "config_file": "config_92.js",
    "bet_mode": 0,
    "total_rounds": 10**5,
    "card_system_enabled": True,
    "card_system_is_newbie": False,
}
```

## 目前刻意保留的 C2 規則

- 每次 Spin 只抽 Normal／Super／Ultimate 三種權重類型。
- 只有參與中獎消除的 Wild 轉成 C2。
- 倍數值與權重以 xlsx `Parameter` 為準。
- 不使用 Bad 權重切換與 FG 輪帶強制替換；目標結果分布改由卡片系統依 xlsx 權重篩選。
