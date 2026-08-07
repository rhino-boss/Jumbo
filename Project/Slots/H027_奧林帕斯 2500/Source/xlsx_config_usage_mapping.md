# H027 xlsx / config 使用對照

| xlsx 來源 | config key | Simulator 用途 |
| --- | --- | --- |
| xlsx 檔名 | `model` | 目前預設為 `H0271`；原始 `Overview!B2` 另存於 `source_model`。 |
| `Overview!B3` | `excel_version` | Excel／數學版本標籤。 |
| `Overview` 模式表 + H027 規則 | `normalbet`、`extrabet`、`featurebuy`、`rtp_targets` | Normal 1x、Extra 2x、Buy 100x；Super Feature 不使用。 |
| `Overview` 賠率表 | `pay_table`、`pay_count_bounds` | 一般符號 8–9／10–11／12+ 與 C1 賠付。 |
| `Parameter` BG 表權重 | `parameter.*.base_reel_weights_cum` | Normal Bet 的三組 BG 選表。 |
| `Parameter` FG 初始／Retrigger | `parameter.*.free_table` | 初始 15 Spins 與每次 Retrigger 5 Spins 的輪帶配置。 |
| `Parameter` Use C3 | `parameter.*.use_c3` | 各輪帶選用 C3 的機率；目前全部為 0。 |
| `Parameter` Weight C2／C3 | `parameter.*.c2`／`c3` | 讀取 25 個倍率級距與各 BG／FG 表權重，最高 2500×。 |
| `Multiplier_Weight` | `card_system.newbie`／`oldhand` | Normal BG／FG 與 Buy Feature 的 range／free_game 卡片；Extra 暫不套卡。 |
| `BG_Symbol*` | `strips[0:3]` | Normal Bet 的 BG 初始與 Cascade 輪帶。 |
| `FG_Symbol*` | `strips[3:6]` | Normal／Buy Feature 的 FG 輪帶。 |
| `BF_Symbol` | `strips[6]` | Buy Feature 起始觸發盤面。 |

官方 metadata 固定為 Game ID `101027`、PARsheet ID `H0271`、中文名「奧林帕斯 2500」、英文名 `Olympus 2500`。

目前預設數學檔為 `H0271.xlsx`。其本身沒有 `Multiplier_Weight`，所以轉換器會由 `H027194A.xlsx` 讀取既有卡片權重；其餘 Parameter、賠率與輪帶均以 `H0271.xlsx` 為準。

## 轉換方式

雙擊 `update_config.bat` 後：

- 直接按 Enter：轉換預設 `H0271.xlsx`。
- 輸入單一 xlsx 檔名或完整路徑：只轉換該檔。
- 輸入 `ALL`：只轉換 `Source` 內具備完整 Parameter 與輪帶頁的 `H0271*.xlsx`。

輸出名稱：

- `H0271.xlsx` → `config_92A.js`

卡片表欄位對應：

- `Weight_NB_BG`／`Weight_NB_FG`：依上層標題分成 Newbie 與 Oldhand。
- `Weight_BF_FG`：Buy Feature 整包結果卡。
- `Free Game`：事件卡；其餘 `(min, max]` 為倍率區間卡。

Excel 可以保持開啟，但執行前必須先儲存；轉換器只讀取磁碟上的已儲存內容。可用下列指令驗證 config 是否與 xlsx 一致：

```powershell
.\.venv\Scripts\python.exe '.\Project\Slots\H027_奧林帕斯 2500\Source\xlsx_to_config.py' --all --check
```

## Config 回填 xlsx

雙擊 `update_xlsx.bat` 會把 `config_92A.js` 回填至 `H0271.xlsx`，並把卡片權重回填至 `H027194A.xlsx`。完成後會再次執行 xlsx→config，比對整份 config；任何可映射欄位不同都會報錯。

只檢查、不寫檔：

```powershell
.\.venv\Scripts\python.exe '.\Project\Slots\H027_奧林帕斯 2500\Source\config_to_xlsx.py' --check
```

另存 round-trip 測試檔時，請同時指定主模型與卡片模型輸出路徑；測試檔建議放在 `其他` 或系統暫存目錄。
