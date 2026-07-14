# H028 Simulator 參數使用說明

## 前段設定

* `CONFIG_FILE`：數學 config，預設 `config_92.js`。
* `TOTAL_ROUNDS`：模擬局數。
* `BET_MODE`：`0` 為 Normal Bet、`2` 為 Buy Feature；本版 101016 邏輯不提供 Extra Bet。
* `THREADS`：ThreadPool 執行緒數。
* `OUTPUT_REPORT`：是否輸出 xlsx 報表。
* `SHOW_CONSOLE_SUMMARY` / `SHOW_CONSOLE_DETAIL`：固定摘要與遊戲專屬明細。
* `RUN_SINGLE_SPIN_DEBUG`：單局 BG trace。

以上設定亦可用 `H028_` 前綴環境變數覆寫；批次子程序沿用 H026 Simulator 的執行方式。

## 資料流

`../Source/H028192A.xlsx` → `../Source/xlsx_to_config.py` → `../config_92.js` → `../Simulator.py` → `../Record/*.xlsx`

玩法核心以 `../../其他遊戲/101016/101016 simulation.py` 為準；執行、彙總與報表架構以 `../../H026_彩罐熱舞 1000/Simulator.py` 為準。
