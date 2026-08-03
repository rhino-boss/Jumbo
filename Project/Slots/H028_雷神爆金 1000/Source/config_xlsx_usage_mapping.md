# H028 config / xlsx 回填對照

本文件說明 `config_to_xlsx.py` 如何將 `config_92A.js` 的資料回填至 H028 數學工作簿。

預設來源：

- config：`../config_92A.js`
- xlsx：`H028192A.xlsx`
- 輸出：`H028192A_from_config_92A.xlsx`

預設採用另存副本，不會修改原始 xlsx。

## config key / xlsx 對照

| config key | 回填位置 | 回填內容 |
| --- | --- | --- |
| `excel_version` | `Overview!B3` | Excel／數學版本 |
| `linkpoint` | `Overview` 內由 `M1` 起算的 `C:F`、共 11 列 | M1～M6、A、K、Q、J、10 的 3～6 輪 Ways 賠率 |
| `BaseGameSymbol1` | `BG_Symbol!T4:Z124` | BG 參數組 1 輪帶 |
| `BaseGameSymbolWeight1` | `BG_Symbol!AB4:AH124` | BG 參數組 1 輪帶權重 |
| `BaseGameMegaWay1` | `BG_Symbol!B33:G47` | BG 參數組 1 MegaWay 權重 |
| `BaseGameMY1` | `BG_Symbol!B50:B62` | BG 參數組 1 Mystery 權重 |
| `BaseGame1PostC1` | `BG_Symbol!A65:B72` | BG 參數組 1 Scatter 後置配置 |
| `BaseGameSymbol2` | `BG_Symbol!BM4:BS124` | BG 參數組 2 輪帶 |
| `BaseGameSymbolWeight2` | `BG_Symbol!BU4:CA124` | BG 參數組 2 輪帶權重 |
| `BaseGameMegaWay2` | `BG_Symbol!AU33:AZ47` | BG 參數組 2 MegaWay 權重 |
| `BaseGameMY2` | `BG_Symbol!AU50:AU62` | BG 參數組 2 Mystery 權重 |
| `BaseGame2PostC1` | `BG_Symbol!AT65:AU72` | BG 參數組 2 Scatter 後置配置 |
| `BaseGame1Drop1`～`BaseGame1Drop5` | `BG_Symbol!AK:AQ`，起始列為 5、34、63、92、121，各 26 列 | BG 參數組 1 Cascade 補牌權重 |
| `BaseGame2Drop1`～`BaseGame2Drop5` | `BG_Symbol!CD:CJ`，起始列為 5、34、63、92、121，各 26 列 | BG 參數組 2 Cascade 補牌權重 |
| `ReelWeight` | `Description!D5:D6` | BG 參數組選擇權重 |
| `FreeReelWeight` | `Description!G5:G7` | FG 初始場次參數組權重 |
| `FreeTriggerReel` | `Description!D18:D20` | FG Retrigger 參數組權重 |
| `FreeGameSymbol1` | `FG_Symbol!T4:Z124` | FG 參數組 1 輪帶 |
| `FreeGameSymbolWeight1` | `FG_Symbol!AB4:AH124` | FG 參數組 1 輪帶權重 |
| `FreeGameMegaWay1` | `FG_Symbol!B33:G47` | FG 參數組 1 MegaWay 權重 |
| `FreeGameMY1` | `FG_Symbol!B50:B62` | FG 參數組 1 Mystery 權重 |
| `FreeGame1PostC1` | `FG_Symbol!A65:B72` | FG 參數組 1 Scatter 後置配置 |
| `FreeGameSymbol2` | `FG_Symbol!BM4:BS124` | FG 參數組 2 輪帶 |
| `FreeGameSymbolWeight2` | `FG_Symbol!BU4:CA124` | FG 參數組 2 輪帶權重 |
| `FreeGameMegaWay2` | `FG_Symbol!AU33:AZ47` | FG 參數組 2 MegaWay 權重 |
| `FreeGameMY2` | `FG_Symbol!AU50:AU62` | FG 參數組 2 Mystery 權重 |
| `FreeGame2PostC1` | `FG_Symbol!AU65:AU72` | FG 參數組 2 Scatter 後置配置 |
| `FreeGameSymbol3` | `FG_Symbol!DF4:DL124` | FG 參數組 3 輪帶 |
| `FreeGameSymbolWeight3` | `FG_Symbol!DN4:DT124` | FG 參數組 3 輪帶權重 |
| `FreeGameMegaWay3` | `FG_Symbol!CN33:CS47` | FG 參數組 3 MegaWay 權重 |
| `FreeGameMY3` | `FG_Symbol!CN50:CN62` | FG 參數組 3 Mystery 權重 |
| `FreeGame3PostC1` | `FG_Symbol!CM65:CN72` | FG 參數組 3 Scatter 後置配置 |
| `FreeGame1Drop1`～`FreeGame1Drop5` | `FG_Symbol!AK:AQ`，起始列為 5、34、63、92、121，各 26 列 | FG 參數組 1 Cascade 補牌權重 |
| `FreeGame2Drop1`～`FreeGame2Drop5` | `FG_Symbol!CD:CJ`，起始列為 5、34、63、92、121，各 26 列 | FG 參數組 2 Cascade 補牌權重 |
| `FreeGame3Drop1`～`FreeGame3Drop5` | `FG_Symbol!DW:EC`，起始列為 5、34、63、92、121，各 26 列 | FG 參數組 3 Cascade 補牌權重 |
| `card_system.newbie.normal_bet.weight_bg` | `Multiplier_Weight` 的 Newbie／`Weight_NB_BG` 欄 | 新手 Normal Bet BG 卡片權重 |
| `card_system.newbie.normal_bet.weight_fg` | `Multiplier_Weight` 的 Newbie／`Weight_NB_FG` 欄 | 新手 Normal Bet FG 卡片權重 |
| `card_system.oldhand.normal_bet.weight_bg` | `Multiplier_Weight` 的 Oldhand／`Weight_NB_BG` 欄 | 老手 Normal Bet BG 卡片權重 |
| `card_system.oldhand.normal_bet.weight_fg` | `Multiplier_Weight` 的 Oldhand／`Weight_NB_FG` 欄 | 老手 Normal Bet FG 卡片權重 |
| `card_system.oldhand.buy_feature.weight_fg` | `Multiplier_Weight` 的 Oldhand／`Weight_BF_FG` 欄 | 老手 Buy Feature FG 卡片權重 |

工作表名稱同時相容：

- `BG_Symbol` 或 `Base Game Symbol`
- `FG_Symbol` 或 `Free Game Symbol`

## 不回填的 metadata

下列欄位由程式或專案規格固定管理，不會寫入 xlsx：

- `game_id`
- `parsheet_id`
- `display_name`
- `game_name_zh`
- `default_coin_in`
- `mode_normalbet`
- `mode_extrabet`
- `mode_featurebuy`
- `normalbet`
- `featurebuy`
- `supported_bet_modes`
- `card_system.enabled`
- `card_system.retry_limit`

## 公式儲存格處理

部分映射範圍在原始 xlsx 中是公式輸出格，例如輪帶表中的 `VLOOKUP`。

config 只保存公式計算後的資料，無法由 config 還原原始公式。因此：

- 預設另存副本時，映射範圍內的公式會轉成 config 中的固定值。
- 原始 `H028192A.xlsx` 不會被修改。
- 使用 `--in-place` 覆寫原檔時，必須同時指定 `--overwrite-formulas`。
- 建議保留原始數學工作簿，將回填檔用於資料核對、重建或交付。

工具直接更新 xlsx 內指定儲存格的 OOXML，不使用 openpyxl 重存整本工作簿，以保留未映射的工作表內容、格式與 Excel 擴充資料。

## 使用方式

### 雙擊 update_xlsx.bat

直接執行：

```text
update_xlsx.bat
```

批次工具會依序詢問 config 與來源 xlsx；直接按 Enter 使用 `config_92A.js` 和 `H028192A.xlsx`。輸出採另存副本並自動執行 round-trip 驗證，不會覆寫來源 xlsx。

也可以從命令列直接指定：

```powershell
& "Project\Slots\H028_雷神爆金 1000\Source\update_xlsx.bat" `
  "config_92A.js" `
  "H028192A.xlsx"
```

### 預設另存副本

```powershell
.\.venv\Scripts\python.exe "Project\Slots\H028_雷神爆金 1000\Source\config_to_xlsx.py"
```

輸出：

```text
Project\Slots\H028_雷神爆金 1000\Source\H028192A_from_config_92A.xlsx
```

### 只檢查差異

```powershell
.\.venv\Scripts\python.exe "Project\Slots\H028_雷神爆金 1000\Source\config_to_xlsx.py" --check
```

只列出映射格與差異格，不寫入 xlsx。

### 指定 config、來源與輸出

```powershell
.\.venv\Scripts\python.exe "Project\Slots\H028_雷神爆金 1000\Source\config_to_xlsx.py" `
  --config "Project\Slots\H028_雷神爆金 1000\config_92A.js" `
  --source "Project\Slots\H028_雷神爆金 1000\Source\H028192A.xlsx" `
  --output "Project\Slots\H028_雷神爆金 1000\Source\H028192A_backfilled.xlsx"
```

如果輸出檔已存在，必須加上 `--force` 才會取代。

### 覆寫原始 xlsx

```powershell
.\.venv\Scripts\python.exe "Project\Slots\H028_雷神爆金 1000\Source\config_to_xlsx.py" `
  --in-place `
  --overwrite-formulas
```

覆寫採用暫存檔加原子置換；若驗證失敗，工具會中止並回報錯誤。

## 驗證流程

每次成功輸出後，工具會立即執行 round-trip 驗證：

1. 將 config 資料回填至 xlsx。
2. 使用既有 `xlsx_to_config.py` 的解析邏輯讀回。
3. 比較所有產生的 config key。
4. 任一欄位不一致即視為失敗。

目前 `config_92A.js`／`H028192A.xlsx` 的映射總數為 13,985 格，已完成完整 round-trip 驗證。
