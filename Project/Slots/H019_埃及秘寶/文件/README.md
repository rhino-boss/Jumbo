# H019 埃及秘寶

## 主要檔案

- `../Simulator.py`：H026 架構風格的獨立 Numba Simulator。
- `../config_92.js`、`../config_94.js`：由兩份 xlsx 產生的執行 config。
- `../game_rule.md`：開發／測試規則文件。
- `../game_help_draft.md`：後續 Help xlsx 的雙語草稿。
- `../Source/`：原始 xlsx、轉換器、批次檔與欄位對照。
- `../其他/parameter_usage_guide.md`：執行參數與指令。
- `../Record/`：模擬報表輸出位置。

數學資料修改流程固定為「修改並儲存 xlsx → 執行 `Source/update_config.bat` → 執行 Simulator」，不要直接手改 config 內的權重。

Simulator 支援 xlsx 驅動的卡片系統；前段 `CARD_SYSTEM_ENABLED` 可開關，Normal Bet 可切換 Newbie／Oldhand，Buy／Super 使用各自的功能購買卡表。
