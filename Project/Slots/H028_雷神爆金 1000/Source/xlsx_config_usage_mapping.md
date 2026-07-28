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
| `Multiplier_Weight` 新手 `Weight_NB_BG` / `Weight_NB_FG` | `card_system.newbie.normal_bet` | 新手 Normal Bet 的 BG 卡與 FG 卡權重 |
| `Multiplier_Weight` 老手 `Weight_NB_BG` / `Weight_NB_FG` | `card_system.oldhand.normal_bet` | 老手 Normal Bet 的 BG 卡與 FG 卡權重 |
| `Multiplier_Weight` 老手 `Weight_BF_FG` | `card_system.oldhand.buy_feature.weight_fg` | Buy Feature 整場 FG 結果權重 |

`config_92A.js` 的 Game ID、PARsheet ID、名稱與版本 metadata 由 `xlsx_to_config.py` 固定補入；官方 ID 對應以 `../../iGaming 遊戲代號一覽.xlsx` 為準。卡片倍率區間依 `Multiplier_Weight` B 欄解析，邊界為 `(min, max]`，並保留 `Free Game` 類型。

## `update_config.bat` 使用方式

雙擊後可輸入單一 xlsx 檔名或完整路徑；直接按 Enter 使用 `H028192A.xlsx`，輸入 `ALL` 則一次轉換 Source 內全部 `H0281*.xlsx`。

輸出名稱由 xlsx 檔名自動產生：

* `H028192A.xlsx` → `config_92A.js`
* `H028192B.xlsx` → `config_92B.js`
* `H028194A.xlsx` → `config_94A.js`

Simulator 預設直接使用 `config_92A.js`；`update_config.bat` 仍會同步一份相容舊流程的 `config_92.js`。Excel 可以保持開啟，但執行前必須先儲存，轉換器只會讀到磁碟上的已儲存內容。
