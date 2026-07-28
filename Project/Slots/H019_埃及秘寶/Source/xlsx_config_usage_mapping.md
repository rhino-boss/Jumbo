# H019 xlsx / config 使用對照

| xlsx 來源 | config key | Simulator 用途 |
| --- | --- | --- |
| `Overview!B2` | `model` | 報表的模型名稱，例如 H019192。 |
| `Overview!B3` | `excel_version` | Excel／數學版本標籤。 |
| `Overview` 模式表 | `normalbet`、`featurebuy`、`superfeaturebuy`、`rtp_targets` | 模式成本與 xlsx 目標 RTP。 |
| `Overview` 賠率表 | `pay_table`、`pay_count_bounds` | 一般符號 8–9／10–11／12+ 與 C1 賠付。 |
| `Parameter` BG 表權重 | `parameter.*.base_reel_weights_cum` | Normal Bet 的四組 BG 選表。 |
| `Parameter` FG 初始／Retrigger | `parameter.*.free_table` | 初始 15 Spins 與每次 Retrigger 5 Spins 的輪帶配置。 |
| `Parameter` Prob C2 | `parameter.*.c2_mode_weights` | 每次 Spin 的 Normal／Super／Ultimate 類型選擇。 |
| `Parameter` Weight C2 | `parameter.*.c2` | 17 個 C2 倍數值與各情境實際權重。 |
| `Multiplier_Weight` | `card_system.newbie`／`oldhand` | Normal BG／FG、Buy Feature、Super Feature 的 range／free_game 卡片與權重。 |
| `BG_Symbol*` | `strips[0:4]` | Normal Bet 的 BG 初始與 Cascade 輪帶。 |
| `FG_Symbol*` | `strips[4:8]` | Normal／Buy Feature 的 FG 輪帶。 |
| `BF_Symbol` | `strips[8]` | Buy／Super 起始觸發盤面。 |
| `SF_Symbol*` | `strips[9:13]` | Super Feature 的 FG 輪帶。 |

官方 metadata 固定為 Game ID `101006`、PARsheet ID `H0191`、中文名「埃及秘寶」、英文名 `Egypt's Treasure`。

## 轉換方式

雙擊 `update_config.bat` 後：

- 直接按 Enter：轉換預設 `H019192.xlsx`。
- 輸入單一 xlsx 檔名或完整路徑：只轉換該檔。
- 輸入 `ALL`：轉換 Source 內全部 `H0191*.xlsx`。

輸出名稱：

- `H019192.xlsx` → `../config_92.js`
- `H019194.xlsx` → `../config_94.js`

卡片表欄位對應：

- `Weight_NB_BG`／`Weight_NB_FG`：依上層標題分成 Newbie 與 Oldhand。
- `Weight_BF_FG`：Buy Feature 整包結果卡。
- `Weight_SF_FG`：Super Feature 整包結果卡。
- `Free Game`：事件卡；其餘 `(min, max]` 為倍率區間卡。

Excel 可以保持開啟，但執行前必須先儲存；轉換器只讀取磁碟上的已儲存內容。可用下列指令驗證 config 是否與 xlsx 一致：

```powershell
.\.venv\Scripts\python.exe '.\Project_AI\Slots\H019_埃及秘寶\Source\xlsx_to_config.py' --all --check
```
