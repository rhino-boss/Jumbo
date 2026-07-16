# H013 Simulator 參數使用說明

## 前段設定

- `CONFIG_FILE`：數學設定檔，預設 `config.js`。
- `TOTAL_ROUNDS`：付費 Round 數，預設 `10**7`。
- `BET_MODE`：0 Normal、1 Extra、2 Feature Buy、3 Super Feature Buy；其他值會拒絕。
- `BET_MULTI`：賠付與下注倍率。
- `THREADS`：平行執行緒數。
- `OUTPUT_REPORT`：是否輸出 xlsx。
- `SHOW_CONSOLE_SUMMARY`／`SHOW_CONSOLE_DETAIL`：固定摘要／本作明細顯示開關。
- `RUN_SINGLE_SPIN_DEBUG`：用單執行緒跑 `DEBUG_ROUNDS` 局做流程檢查。

設定均可由同名 `H013_` 環境變數覆寫。

## PowerShell 範例

```powershell
$env:PYTHONUTF8='1'
$env:H013_TOTAL_ROUNDS='100000'
$env:H013_BET_MODE='0'
$env:H013_THREADS='8'
.\.venv\Scripts\python.exe '.\Project_AI\Slots\H013_糖果狂歡 1000\Simulator.py'
```

只看 console、不輸出報表：

```powershell
$env:H013_OUTPUT_REPORT='false'
```

模式切換：

```powershell
$env:H013_BET_MODE='1'  # Extra Bet
$env:H013_BET_MODE='2'  # Feature Buy
$env:H013_BET_MODE='3'  # Super Feature Buy
```

## 資料流與報表

`Source/H013197.xlsx` → `Tool/xlsx_to_config.py` → `config.js` → `Simulator.py` → `Record/*.xlsx`

報表包含 `Base Info`、`Hits`、`Pay`、`Eliminate`、`Multiplier Line`、`Record Data`。檔名第一段固定使用 PARsheet ID `H0131`。

## 舊版修正點

- 移除硬編碼 `os.chdir` 與舊共用套件依賴，從專案相對路徑載入 config。
- 模擬次數、模式、執行緒與輸出開關集中在檔案前段。
- 模式輸入會明確驗證。
- 四種模式均使用對應 BG／FG 輪帶和倍率權重；Super Feature 高表不再誤判為低表。
- 倍率報表區間與共用 Simulator 規範一致。
- 大量模擬核心使用 Numba，外層以可調執行緒分塊彙總。
