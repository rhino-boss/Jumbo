# H025 Excel / config 使用對照

## 來源映射

| H025 專案檔案 | 101013 原始檔名 | 用途 |
| --- | --- | --- |
| `H025192A.xlsx` | `H026(果醬罐A) 93 92.xlsx` | A 組、92 版數學來源 |
| `H025194A.xlsx` | `H026(果醬罐A) 93 94.xlsx` | A 組、94 版數學來源 |
| `H025192B.xlsx` | `H026(果醬罐B) 93 92.xlsx` | B 組、92 版數學來源 |
| `H025194B.xlsx` | `H026(果醬罐B) 93 94.xlsx` | B 組、94 版數學來源 |
| `../config.js` | `data.js` | 101013 現有模擬器使用的基準設定 |
| `../config_92A.js` | `H025192A.xlsx` | A 組、92 版可重新產生設定 |
| `../config_92B.js` | `H025192B.xlsx` | B 組、92 版可重新產生設定 |
| `../config_94A.js` | `H025194A.xlsx` | A 組、94 版可重新產生設定 |
| `../config_94B.js` | `H025194B.xlsx` | B 組、94 版可重新產生設定 |

## 目前限制

1. 101013 沒有提供 Excel 轉 `data.js` 的生成程式；H025 已依活頁簿實際區塊補上 `xlsx_to_config.py`。
2. `config.js` 保留為 101013 `data.js` 的位元相同基準檔，不直接視為某個 A/B、92/94 版本。
3. 四份活頁簿可透過 `update_config.bat` 產生對應的 `config_92A.js`、`config_92B.js`、`config_94A.js`、`config_94B.js`。
4. Excel 內原有 H026 字樣是來源舊代號；本專案不改寫原始活頁簿內容與格式。

## 產生與驗證

```powershell
py -3 '.\Project_AI\Slots\H025_多採多汁\Source\xlsx_to_config.py' --all --check
```

Simulator 可透過 `H025_CONFIG_FILE` 切換設定，例如 `config_92A.js`。

## 規則採信順序

來源內文字衝突時，依使用者於 2026-07-16 的確認，以 `Simulator.py` 實際執行邏輯為準：

- Wild 倍數上限為 `×100`。
- 3／4 顆 Scatter 分別增加 `8／10` 次 Free Game。
