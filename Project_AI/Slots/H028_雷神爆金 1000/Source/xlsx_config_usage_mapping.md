# H028 xlsx / config 使用對照

| 來源 | config key | Simulator 用途 |
| --- | --- | --- |
| `Overview!C32:F42` | `linkpoint` | 3～6 輪 Ways 賠率 |
| `Base Game Symbol` | `BaseGameSymbol*` / `BaseGameSymbolWeight*` | BG 初始輪帶與權重 |
| `Base Game Symbol` | `BaseGameMegaWay*` | BG 大符號高度組合權重 |
| `Base Game Symbol` | `BaseGameMY*` / `BaseGame*PostC1` | BG Mystery 與 Scatter 後置配置 |
| `Base Game Symbol` | `BaseGame*Drop*` | BG Cascade 補牌權重 |
| `Free Game Symbol` | `FreeGameSymbol*` / `FreeGameSymbolWeight*` | FG 初始輪帶與權重 |
| `Free Game Symbol` | `FreeGameMegaWay*` | FG 大符號高度組合權重 |
| `Free Game Symbol` | `FreeGameMY*` / `FreeGame*PostC1` | FG Mystery 與 Scatter 後置配置 |
| `Free Game Symbol` | `FreeGame*Drop*` | FG Cascade 補牌權重 |
| `Description!D5:D6` | `ReelWeight` | BG 參數組選擇權重 |
| `Description!G5:G7` | `FreeReelWeight` | FG 初始場次參數組權重 |
| `Description!D18:D20` | `FreeTriggerReel` | Retrigger 場次參數組權重 |

`config_92.js` 的 Game ID、PARsheet ID、名稱與版本 metadata 由 `xlsx_to_config.py` 固定補入；官方 ID 對應以 `../../iGaming 遊戲代號一覽.xlsx` 為準。
