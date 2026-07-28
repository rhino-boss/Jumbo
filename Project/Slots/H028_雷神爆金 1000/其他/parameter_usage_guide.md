# H028 Simulator 參數使用說明

## 前段設定

* `CONFIG_FILE`：數學 config，預設 `config_92A.js`。
* `TOTAL_ROUNDS`：模擬局數。
* `BET_MODE`：`0` 為 Normal Bet、`2` 為 Buy Feature；本版 101016 邏輯不提供 Extra Bet。
* `THREADS`：ThreadPool 執行緒數。
* `OUTPUT_REPORT`：是否輸出 xlsx 報表。
* `SHOW_CONSOLE_SUMMARY` / `SHOW_CONSOLE_DETAIL`：固定摘要與遊戲專屬明細。
* `RUN_SINGLE_SPIN_DEBUG`：單局 BG trace。
* `CARD_SYSTEM_ENABLED`：是否啟用卡片結果篩選／重試。
* `CARD_SYSTEM_IS_NEWBIE`：Normal Bet 使用新手卡權重 (`True`) 或老手卡權重 (`False`)。

以上設定亦可用 `H028_` 前綴環境變數覆寫；卡片設定對應 `H028_CARD_SYSTEM_ENABLED` 與 `H028_CARD_SYSTEM_IS_NEWBIE`。`BATCH_RUNS` 每列也可個別加入 `card_system_enabled`、`card_system_is_newbie`。批次子程序沿用 H026 Simulator 的執行方式。

卡片不是額外派彩機制，而是先抽目標卡，再重試遊戲結果：區間採 `(min, max]`；Free Game 卡先篩選會觸發 FG 的 BG，再用同身分 FG 權重篩選整場 FG 派彩。Buy Feature 使用 `Weight_BF_FG`。倍率分母一律採 Normal Bet coin-in，重試上限由 config 的 `card_system.retry_limit` 控制。

## 資料流

`../Source/H028192A.xlsx` → `../Source/xlsx_to_config.py` → `../config_92A.js` → `../Simulator.py` → `../Record/*.xlsx`

玩法核心以 `../../其他遊戲/101016/101016 simulation.py` 為準；執行、彙總與報表架構以 `../../H026_彩罐熱舞 1000/Simulator.py` 為準。
