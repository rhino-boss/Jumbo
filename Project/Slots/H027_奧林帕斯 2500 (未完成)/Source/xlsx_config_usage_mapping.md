# H027 xlsx / config 使用對照

| xlsx 來源 | config key | Simulator 用途 |
| --- | --- | --- |
| xlsx 檔名 | `model` | 報表模型名稱，例如 `H027192A`；原始 `Overview!B2` 另存於 `source_model`。 |
| `Overview!B3` | `excel_version` | Excel／數學版本標籤。 |
| `Overview` 模式表 + H027 規則 | `normalbet`、`extrabet`、`featurebuy`、`rtp_targets` | Normal 1x、Extra 2x、Buy 100x；Super Feature 不使用。 |
| `Overview` 賠率表 | `pay_table`、`pay_count_bounds` | 一般符號 8–9／10–11／12+ 與 C1 賠付。 |
| `Parameter` BG 表權重 | `parameter.*.base_reel_weights_cum` | Normal Bet 的四組 BG 選表。 |
| `Parameter` FG 初始／Retrigger | `parameter.*.free_table` | 初始 15 Spins 與每次 Retrigger 5 Spins 的輪帶配置。 |
| `Parameter` Prob C2 | `parameter.*.c2_mode_weights` | 每次 Spin 的 Normal／Super／Ultimate 類型選擇。 |
| `Parameter` Weight C2 + H027 規則 | `parameter.*.c2` | 過濾為 15 個正式倍數級距；150／200／250 不使用，2500 初始權重為 0。 |
| `Multiplier_Weight` | `card_system.newbie`／`oldhand` | Normal BG／FG 與 Buy Feature 的 range／free_game 卡片；Extra 暫不套卡。 |
| `BG_Symbol*` | `strips[0:4]` | Normal Bet 的 BG 初始與 Cascade 輪帶。 |
| `FG_Symbol*` | `strips[4:8]` | Normal／Buy Feature 的 FG 輪帶。 |
| `BF_Symbol` | `strips[8]` | Buy Feature 起始觸發盤面。 |

官方 metadata 固定為 Game ID `101027`、PARsheet ID `H0271`、中文名「奧林帕斯 2500」、英文名 `Olympus 2500`。

目前 `H027192A.xlsx` 是以 H019 92% 數學底稿建立的初版。轉換器會依 H027 已確認規則停用 WW、Super Feature 與 Jackpot，建立 Extra Bet 模式並過濾 C2 值池。尚待新版 PAR sheet 的項目記錄在 `pending_math_items`。

## 轉換方式

雙擊 `update_config.bat` 後：

- 直接按 Enter：轉換預設 `H027192A.xlsx`。
- 輸入單一 xlsx 檔名或完整路徑：只轉換該檔。
- 輸入 `ALL`：轉換 `Source` 內全部 `H0271*.xlsx`。

輸出名稱：

- `H027192A.xlsx` → `config_92A.js`

卡片表欄位對應：

- `Weight_NB_BG`／`Weight_NB_FG`：依上層標題分成 Newbie 與 Oldhand。
- `Weight_BF_FG`：Buy Feature 整包結果卡。
- `Free Game`：事件卡；其餘 `(min, max]` 為倍率區間卡。

Excel 可以保持開啟，但執行前必須先儲存；轉換器只讀取磁碟上的已儲存內容。可用下列指令驗證 config 是否與 xlsx 一致：

```powershell
.\.venv\Scripts\python.exe '.\Project_AI\Slots\H027_奧林帕斯 2500\Source\xlsx_to_config.py' --all --check
```
