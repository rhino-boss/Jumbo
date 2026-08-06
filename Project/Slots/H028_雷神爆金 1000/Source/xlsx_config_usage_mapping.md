# H028 xlsx → config 使用對照

`xlsx_to_config.py` 以目前 `H028192A.xlsx` 的分頁配置為準。每一組數學參數使用獨立的 Symbol 工作表，不再使用同一張表右側的舊版橫向區塊；六張 Symbol 表的 R1～R7 均固定讀取 200 格。

## 參數組與工作表

| config 參數組 | xlsx 工作表 | 輪帶範圍／長度 |
| --- | --- | --- |
| `BaseGame*1` | `BG_Symbol` | `M4:S203`、200 格 |
| `BaseGame*2` | `BG_Symbol (2)` | `M4:S203`、200 格 |
| `BaseGame*3` | `BF_Symbol` | `M4:S203`、200 格 |
| `FreeGame*1` | `FG_Symbol` | `M4:S203`、200 格 |
| `FreeGame*2` | `FG_Symbol (2)` | `M4:S203`、200 格 |
| `FreeGame*3` | `FG_Symbol (3)` | `M4:S203`、200 格 |

## 每張 Symbol 工作表的共用位置

| xlsx 範圍 | config 欄位 | 資料形狀 |
| --- | --- | --- |
| `BG_Symbol!M4:S203`／`AC4:AI203` | `BaseGameSymbol1`／`BaseGameSymbolWeight1` | 7 輪 × 200 格 |
| `FG_Symbol!M4:S203`／`AC4:AI203` | `FreeGameSymbol1`／`FreeGameSymbolWeight1` | 7 輪 × 200 格 |
| `M4:S203`／`AC4:AI203` | 其他 `*Symbol*`／`*SymbolWeight*` | 7 輪 × 200 格 |
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

`BF_Symbol` 讀入 `BaseGame*3`。除 Symbol Weight 外均與 `BaseGame*1` 相同；BF 權重保留多組不形成 Ways 的 RNG，只將可能得分的停輪位置設為 0，並只在 Feature Buy 觸發畫面使用。

BG1、BG2 的 R1～R7 初始金框比例分別為 `[0%,33.5%,31.5%,25%,22%,17.5%,0%]`、`[0%,33%,31%,24.5%,21.5%,17%,0%]`。兩表 Drop1～Drop5 以 2.0.0.31 為基準，只將 Golden M2～Golden TE 權重乘以 5；BG1 的 R1～R7 實際金框機率為 `[0%,10.0841%,10.7387%,10.7003%,5.072%,2.6429%,0%]`，BG2 為 `[0%,10.3398%,11.0109%,11.0425%,5.226%,2.7516%,0%]`。Golden M1 權重維持 0。

BG1 R1 的 M4／M5／A／Q 數量為 `[12,12,17,17]`，R2 的 M4／M6／K／J 為 `[19,16,16,14]`；BG2 對應數量分別為 `[12,12,16,16]`、`[19,16,16,14]`。數量均合併普通／金框 ID 計算，兩表 R1、R2 仍各為 200 格。

FG1 為競品表、FG2 為連消表、FG3 為累積倍數表。`Parameter!C11:C13`、`C18:C20` 均為 `[6000,4500,4500]`，因此初始 FG 與 Retrigger 都以 40%／30%／30% 使用 FG1／FG2／FG3。FG1、FG2 的 R1～R7 初始金框分別為 30/200（15%）、40/200（20%），兩表 Drop1～Drop5 的 R1～R7 金框權重均為 10%。BG、BF、FG 全部 Table 的初始輪帶及 Drop1～Drop5 均禁止 Golden M1（ID 13）；M1 只使用普通 ID 2，金框總量由其他非 M1 符號承接。FG3 的 R1～R7 M1 合計為 `[3,20,20,12,12,4,4]`，每輪維持 200 格。

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
