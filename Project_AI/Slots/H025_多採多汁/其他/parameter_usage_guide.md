# H025 Simulator 參數使用說明

## 設定檔

- 預設：`config.js`（101013 原始基準）
- 環境變數覆寫：`H025_CONFIG_FILE`
- 設定檔路徑以 `Simulator.py` 所在資料夾為基準。
- 可選設定：`config_92A.js`、`config_92B.js`、`config_94A.js`、`config_94B.js`。

例如：

```powershell
$env:H025_CONFIG_FILE='config_92A.js'
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe '.\Project_AI\Slots\H025_多採多汁\Simulator.py' -r 10000 -w 1 --seed 25025
```

## CLI 參數

| 參數 | 預設值 | 說明 |
| --- | ---: | --- |
| `-r`, `--rounds` | `100000` | Base Game 模擬局數 |
| `-w`, `--workers` | `8` | 多進程數量；驗證時可先用 `1` |
| `--no-multiplier` | 關閉旗標 | 指定後停用 Wild 倍數 |
| `--seed` | 隨機 | 固定亂數種子以便重現 |
| `-q`, `--quiet` | 關閉 | 減少過程輸出 |

查看說明：

```powershell
.\.venv\Scripts\python.exe '.\Project_AI\Slots\H025_多採多汁\Simulator.py' --help
```

## 執行範圍

- CLI 目前只串接 Base Game 模擬與 console 統計。
- 程式內保留 `freegame(initial_spins, rounds)` 與 `freegame_parallel(...)`，但尚未接入 CLI。
- `Record/` 目前只是標準專案預留資料夾；101013 原程式沒有 xlsx 報表輸出。
- `Source/*.xlsx` 尚未直接連接 Simulator。實際執行值以 `config.js` 為準。
