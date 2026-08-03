# H028 config → xlsx 回填對照

`config_to_xlsx.py` 將 `config_92A.js` 回填至目前的 H028 工作簿配置。`update_xlsx.bat` 會直接覆寫所選 xlsx，不再建立另一份 xlsx。

`update_xlsx.bat` 預設來源：

- config：`../config_92A.js`
- xlsx：`H028192A.xlsx`
- 輸出：直接覆寫上述 xlsx

## 參數組與工作表

| config 參數組 | xlsx 工作表 | 輪帶範圍／長度 |
| --- | --- | --- |
| `BaseGame*1` | `BG_Symbol` | `M4:S153`、150 格 |
| `BaseGame*2` | `BG_Symbol (2)` | `M4:S124`、121 格 |
| `FreeGame*1` | `FG_Symbol` | `M4:S124`、121 格 |
| `FreeGame*2` | `FG_Symbol (2)` | `M4:S124`、121 格 |
| `FreeGame*3` | `FG_Symbol (3)` | `M4:S124`、121 格 |

## 每張 Symbol 工作表的共用回填位置

| config 欄位 | xlsx 範圍 | 資料形狀 |
| --- | --- | --- |
| `BaseGameSymbol1`／`BaseGameSymbolWeight1` | `BG_Symbol!M4:S153`／`AC4:AI153` | 7 輪 × 150 格 |
| 其他 `*Symbol*`／`*SymbolWeight*` | 各自工作表的 `M4:S124`／`AC4:AI124` | 7 輪 × 121 格 |
| `*MegaWay*` | `C33:H47` | 6 輪 × 15 種大符號組合權重 |
| `*MY*` | `C51:C63` | 13 個 Mystery 權重 |
| `*PostC1` | `B67:C74` | 8 個 Scatter 數量與對應權重 |
| `*Drop1` | `AL4:AR29` | 7 輪 × 26 個符號權重 |
| `*Drop2` | `AL33:AR58` | 7 輪 × 26 個符號權重 |
| `*Drop3` | `AL62:AR87` | 7 輪 × 26 個符號權重 |
| `*Drop4` | `AL91:AR116` | 7 輪 × 26 個符號權重 |
| `*Drop5` | `AL120:AR145` | 7 輪 × 26 個符號權重 |

啟用中的 `BaseGameSymbol1` 會先依工作表 `A4:J29` 的 ID 對照轉成符號名稱，再回填到真正的輪帶區 `BG_Symbol!M4:S153`。`U:AA` 的 Symbol ID／公式區不再寫入固定值；工具會恢復該區公式、移除失效的 `calcChain.xml` 關聯，並要求 Excel 開啟時完整重算。工具使用暫存檔完成原子置換，但不另外保留備份，因此執行前必須關閉 Excel，並確認所選檔案正確。

## 其他回填位置

| config key | xlsx 位置 |
| --- | --- |
| `excel_version` | `Overview!B3` |
| `linkpoint` | `Overview` 內由 `M1` 起算的 `C:F`，共 11 列 |
| `ReelWeight` | `Parameter!C5:C6` |
| `FreeReelWeight` | `Parameter!C11:C13` |
| `FreeTriggerReel` | `Parameter!C18:C20` |
| `card_system.*` 權重 | `Multiplier_Weight` 對應 Newbie／Oldhand 欄位 |

遊戲 ID、名稱、bet mode 等固定 metadata 不回填 xlsx。

## 使用方式

雙擊：

```text
update_xlsx.bat
```

直接按 Enter 使用預設 config 與 xlsx，完成後原 xlsx 會被取代。也可以指定：

```powershell
& "Project\Slots\H028_雷神爆金 1000\Source\update_xlsx.bat" `
  "config_92A.js" `
  "H028192A.xlsx"
```

只檢查映射差異、不寫檔：

```powershell
.\.venv\Scripts\python.exe "Project\Slots\H028_雷神爆金 1000\Source\config_to_xlsx.py" --check
```

成功輸出後，工具會立即執行 config → xlsx → config round-trip 比對；任一 config key 不一致即失敗。

若直接執行 `config_to_xlsx.py` 且未加 `--in-place`，Python 工具本身仍維持另存副本的預設行為；只有 `update_xlsx.bat` 固定使用原地覆寫模式。
