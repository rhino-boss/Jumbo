# H025 Simulator 參數使用說明

## 架構與邏輯來源

- `Simulator.py` 是重新建立的 H026-style 外層，負責 User Settings、Config、Record、模擬切片、Console、Excel、Batch 與 `main()`。
- `H025_game_logic.py` 保存六角盤面、Cluster 消除、Wild 倍數、Mega Eliminate、Scatter 與 Free Game 的 101013 程式邏輯。
- H026 的 5 軸連線、Gold、Multiplier Symbol、Bet Mode 與卡片系統不適用於 H025，因此不會帶入。
- 正式執行入口只有 `Simulator.py`；`H025_game_logic.py` 不需要單獨執行。

## 預設值

| 項目 | 預設值 |
| --- | ---: |
| Config | `config_92B.js` |
| Paid rounds | `100,000` |
| Threads | 最多 `8`，不超過電腦 CPU 數；使用 `ThreadPoolExecutor` |
| Coin in | `100` |
| Report | 開啟，輸出到 `Record/` |
| Run all combinations | 關閉 |

Simulator 會先執行 1 局 Numba 預熱，再開始計算正式模擬時間，與 H026 的計時流程一致。

## 一般執行

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe '.\Project_AI\Slots\H025_多採多汁\Simulator.py' -r 10000 -w 1 --seed 25025
```

指定 Config：

```powershell
.\.venv\Scripts\python.exe '.\Project_AI\Slots\H025_多採多汁\Simulator.py' --config config_92A.js -r 10000 -w 1
```

一次執行四個版本：

```powershell
.\.venv\Scripts\python.exe '.\Project_AI\Slots\H025_多採多汁\Simulator.py' --all -r 10000 -w 1
```

## CLI 參數

| 參數 | 說明 |
| --- | --- |
| `-r`, `--rounds` | Paid round 數；每局會由 BG 自動銜接觸發的 FG |
| `-w`, `--workers` | 多程序數量；小量驗證建議使用 `1` |
| `--seed` | 固定亂數種子 |
| `--config` | `config_92A.js`、`config_92B.js`、`config_94A.js` 或 `config_94B.js` |
| `--all` | 依序執行上述四個 Config |
| `--no-report` | 不產生 Excel 報表 |
| `--no-multiplier` | 關閉 Wild 倍數 |
| `--detail` | 在主控台顯示各項分布 |

在 VS Code Interactive Window／Jupyter 中執行時，程式會忽略 kernel 自動加入的 `--f=...` 參數；`--workers`／`H025_THREADS` 仍會套用，並透過多執行緒切分模擬局數。

多執行緒共用 Python／NumPy 全域亂數狀態，因此固定 seed 時，`1` worker 可穩定重現；多 worker 的整體分布可比較，但不保證每次逐局結果完全相同。

## 環境變數

| 變數 | 說明 |
| --- | --- |
| `H025_CONFIG_FILE` | 設定檔 |
| `H025_BASE_DIR` | Interactive Window 無法自動定位時，手動指定 H025 專案目錄 |
| `H025_TOTAL_ROUNDS` | Paid round 數 |
| `H025_THREADS` | 多程序數 |
| `H025_SEED` | 亂數種子 |
| `H025_RUN_ALL_COMBINATIONS` | 是否批次執行四個 Config |
| `H025_OUTPUT_REPORT` | 是否輸出報表 |
| `H025_SHOW_CONSOLE_DETAIL` | 是否顯示詳細分布 |
| `H025_ENABLE_MULTIPLIER` | 是否啟用 Wild 倍數 |
| `H025_MAX_FG_SPINS` | 單場 FG 安全上限，預設 `10000` |

環境變數可使用 `true/false`、`1/0`、`yes/no` 或 `on/off`。

## 報表內容

Excel 會輸出：`Base Info`、`RTP Hit Rate`、`Win Distribution`、`Scatter Distribution`、`Cascade Distribution`、`Wild Multiplier`、`Mega Feature` 與 `Record Data`。

`RTP Hit Rate` 會分別列出 Total Paid Round、Base Game 與 Free Game Spin 的 Sample Count、Hit Count、Hit Rate、Hit Frequency、Pay、RTP Contribution 與 Average Pay per Hit。

RTP 使用 `總派彩 / (Paid rounds × 100)`；BG 觸發的完整 FG 派彩會計入同一 Paid round 的 Total RTP。
