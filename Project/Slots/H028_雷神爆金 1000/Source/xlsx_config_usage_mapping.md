# H028 xlsx → config 使用對照

`xlsx_to_config.py` 以目前 `H028192A.xlsx` 的分頁配置為準。每一組數學參數使用獨立的 Symbol 工作表，不再使用同一張表右側的舊版橫向區塊；五張 Symbol 表的 R1～R7 均固定讀取 200 格。

## 參數組與工作表

| config 參數組 | xlsx 工作表 | 輪帶範圍／長度 |
| --- | --- | --- |
| `BaseGame*1` | `BG_Symbol` | `M4:S203`、200 格 |
| `BaseGame*2` | `BG_Symbol (2)` | `M4:S124`、121 格 |
| `FreeGame*1` | `FG_Symbol` | `M4:S203`、200 格 |
| `FreeGame*2` | `FG_Symbol (2)` | `M4:S124`、121 格 |
| `FreeGame*3` | `FG_Symbol (3)` | `M4:S124`、121 格 |

## 每張 Symbol 工作表的共用位置

| xlsx 範圍 | config 欄位 | 資料形狀 |
| --- | --- | --- |
| `BG_Symbol!M4:S203`／`AC4:AI203` | `BaseGameSymbol1`／`BaseGameSymbolWeight1` | 7 輪 × 200 格 |
| `FG_Symbol!M4:S203`／`AC4:AI203` | `FreeGameSymbol1`／`FreeGameSymbolWeight1` | 7 輪 × 200 格 |
| `M4:S124`／`AC4:AI124` | 其他未啟用的 `*Symbol*`／`*SymbolWeight*` | 7 輪 × 121 格 |
| `C33:H47` | `*MegaWay*` | 6 輪 × 15 種大符號組合權重 |
| `C51:C63` | `*MY*` | 13 個 Mystery 權重 |
| `B67:C74` | `*PostC1` | 8 個 Scatter 數量與對應權重 |
| `AL4:AR29` | `*Drop1` | 7 輪 × 26 個符號權重 |
| `AL33:AR58` | `*Drop2` | 7 輪 × 26 個符號權重 |
| `AL62:AR87` | `*Drop3` | 7 輪 × 26 個符號權重 |
| `AL91:AR116` | `*Drop4` | 7 輪 × 26 個符號權重 |
| `AL120:AR145` | `*Drop5` | 7 輪 × 26 個符號權重 |

`M:S` 是真正的輪帶 Symbol。xlsx → config 會依每張工作表 `A4:J29` 的 Symbol／ID 對照表，把 `M:S` 的符號名稱轉成 Simulator 使用的數字 ID；`U:AA` 保留為 Excel 公式區，不作為回填來源。

SC（ID 1）不配置於任何 BG／FG 初始輪帶；初始停輪後的顆數由各參數組 `B67:C74` 的 `*PostC1` 權重產生，`Drop1～Drop5` 則保留 `analysis_lucky_neko_final.xlsx` 的 `SymbolOcc_Drop`／`Extra Reel_Drop` SC 比例。初始非 SC 符號移除 SC 後重新正規化。

## 其他位置

| 來源 | config key | Simulator 用途 |
| --- | --- | --- |
| `Overview!B3` | `excel_version` | Excel／數學版本 |
| `Overview` 的 M1 起始賠付表 | `linkpoint` | 3～6 輪 Ways 賠率 |
| `Parameter!C5:C6` | `ReelWeight` | BG 參數組選擇權重 |
| `Parameter!C11:C13` | `FreeReelWeight` | FG 初始場次參數組權重 |
| `Parameter!C18:C20` | `FreeTriggerReel` | FG Retrigger 參數組權重 |
| `Multiplier_Weight` Newbie／`Weight_NB_BG`、`Weight_NB_FG` | `card_system.newbie.normal_bet` | 新手卡片權重 |
| `Multiplier_Weight` Oldhand／`Weight_NB_BG`、`Weight_NB_FG` | `card_system.oldhand.normal_bet` | 老手 Normal Bet 卡片權重 |
| `Multiplier_Weight` Oldhand／`Weight_BF_FG` | `card_system.oldhand.buy_feature.weight_fg` | 老手 Buy Feature FG 卡片權重 |

## `update_config.bat`

雙擊後可輸入單一 xlsx 檔名或完整路徑；直接按 Enter 使用 `H028192A.xlsx`，輸入 `ALL` 則轉換 Source 內全部 `H0281*.xlsx`。

檔名會自動對應 config，例如 `H028192A.xlsx` → `config_92A.js`。Excel 可以保持開啟，但執行前必須先儲存，工具只會讀到磁碟上的內容。
