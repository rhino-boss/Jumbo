# H028 xlsx / config 使用對照

| 來源 | config key | Simulator 用途 |
| --- | --- | --- |
| `Overview!B3` | `excel_version` | Excel／數學版本與報表版本標籤 |
| `Overview` 的 M1 起始賠付表 | `linkpoint` | 3～6 輪 Ways 賠率 |
| `BG_Symbol`（相容舊名 `Base Game Symbol`） | `BaseGameSymbol*` / `BaseGameSymbolWeight*` | BG 初始輪帶與權重 |
| `BG_Symbol`（相容舊名 `Base Game Symbol`） | `BaseGameMegaWay*` | BG 大符號高度組合權重 |
| `BG_Symbol`（相容舊名 `Base Game Symbol`） | `BaseGameMY*` / `BaseGame*PostC1` | BG Mystery 與 Scatter 後置配置 |
| `BG_Symbol`（相容舊名 `Base Game Symbol`） | `BaseGame*Drop*` | BG Cascade 補牌權重 |
| `FG_Symbol`（相容舊名 `Free Game Symbol`） | `FreeGameSymbol*` / `FreeGameSymbolWeight*` | FG 初始輪帶與權重 |
| `FG_Symbol`（相容舊名 `Free Game Symbol`） | `FreeGameMegaWay*` | FG 大符號高度組合權重 |
| `FG_Symbol`（相容舊名 `Free Game Symbol`） | `FreeGameMY*` / `FreeGame*PostC1` | FG Mystery 與 Scatter 後置配置 |
| `FG_Symbol`（相容舊名 `Free Game Symbol`） | `FreeGame*Drop*` | FG Cascade 補牌權重 |
| `Description!D5:D6` | `ReelWeight` | BG 參數組選擇權重 |
| `Description!G5:G7` | `FreeReelWeight` | FG 初始場次參數組權重 |
| `Description!D18:D20` | `FreeTriggerReel` | Retrigger 場次參數組權重 |

`config_92.js` 的 Game ID、PARsheet ID、名稱與版本 metadata 由 `xlsx_to_config.py` 固定補入；官方 ID 對應以 `../../iGaming 遊戲代號一覽.xlsx` 為準。

## `update_config.bat` 使用方式

雙擊後可輸入單一 xlsx 檔名或完整路徑；直接按 Enter 使用 `H028192A.xlsx`，輸入 `ALL` 則一次轉換 Source 內全部 `H0281*.xlsx`。

輸出名稱由 xlsx 檔名自動產生：

* `H028192A.xlsx` → `config_92A.js`
* `H028192B.xlsx` → `config_92B.js`
* `H028194A.xlsx` → `config_94A.js`

為相容目前 Simulator，轉換預設來源 `H028192A.xlsx` 時也會同步更新 `config_92.js`。Excel 可以保持開啟，但執行前必須先儲存，轉換器只會讀到磁碟上的已儲存內容。
