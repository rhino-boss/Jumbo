# H027 XLSX / Config 使用對照

## 正式入口

- `xlsx_to_config.py [--check]`：`H0271.xlsx` → `../config.js`。
- `model_sync.py import --in-place`：`../config.js` → `H0271.xlsx`。
- `update.bat`：提供上述轉換與雙向檢查入口。

## 共用執行來源

- Simulator 的 `config_file` 提供輪帶、盤面、Table、Drop Weight 與自然機率。
- Simulator 的 `config_rtp_file` 提供 C2／C3 倍率權重與 Card System；目前來源結構尚未拆出 `H027192A.xlsx`，Card System Off 批次暫時以 `config.js` 同時完成相容性驗證，此項列為 Card System On 的交付阻塞。
- Demogame 只從所選 Config 取得遊戲名稱、盤面、Symbol、Paytable、Bet Mode、補牌模式及 Feature 參數。

## 工作簿對照

| XLSX | Config |
|---|---|
| `Overview!B2:B3` | `model`, `excel_version` |
| `Overview!A7`, `B11:B13`, `B17:G17` | 底注、Bet 倍數、視窗 |
| `Overview!A30:I41` | `symbol_codes`, `symbol_ids`, `pay_table` |
| `Parameter!C28:C52` | `multiplier_levels` |
| `Parameter!K4:AI4` | `parameter.super_multiplier` |
| `Parameter!B4:D13` | BG／FG 選表與 Free Spin 設定 |
| `Parameter!B18:H23` | `use_super_multiplier.weights_by_initial_ball_count` |
| `Parameter!J9:AI14` | C2 倍率權重 |
| `Parameter!J19:AI24` | C3 倍率權重 |
| 四張 `*_Symbol` 工作頁 `L4:Q303` | `strips[].symbols` |
| 四張 `*_Symbol` 工作頁 `Z4:AE303` | `strips[].weights` |
| 四張 `*_Symbol` 工作頁 `AH4:AM15` | `strips[].drop_weights` |

`BG_Symbol (3)`、`FG_Symbol (3)` 與 Parameter 中對應的歷史列不屬於正式 Runtime；雙向轉換必須保留其原值，不得清空或匯入 Config。

## Demogame / Runtime Metadata

下列欄位由轉檔工具的固定 Metadata 產生，禁止在 `index.html` 另寫一份：

- `denom`
- `bet_options`
- `initial_balance`
- `drop_mode = cascade_drop`
- `fg_trigger_count`, `fg_retrigger_count`, `cascade_limit`
- `supported_bet_modes`

`cascade_drop` 表示中獎符號消除後，同輪上方保留符號向下補位，空格由該 Spin 選定 Table 的 `drop_weights` 從上方補入；Simulator 與 Demogame 使用相同順序。
