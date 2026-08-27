# H027 XLSX / Config 使用對照

H027 的初始模型主要依據競品遊戲資料建立，依 `slot_development_specification.md` 的版本規則，基礎數學初始版本使用 `0`。

## 正式入口

- `model_sync.py export [--check]`：`H0271.xlsx` → `../config.js`。
- `model_sync.py import --in-place`：`../config.js` → `H0271.xlsx`。
- `update.bat`：提供上述轉換與雙向檢查入口。

## 共用執行來源

- Simulator 的 `config_file` 提供輪帶、盤面、Table 與自然機率；消除補牌也沿同一條輪帶，不使用 Symbol Drop Weight。
- C2／C3 倍率權重及 C2→C3 自然機率以 `H0271.xlsx` 為唯一來源，並同步進 Base、92A、94A Config。
- Simulator 的 `config_rtp_file` 提供 Card System 倍率區間權重；`H027192A.xlsx`／`H027194A.xlsx` 只管理卡片區間，不重複存放自然 C3 參數。
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
| `Parameter!B55:G63` | `use_super_multiplier.drop_combo_buckets`、`weights_by_drop_combo`；Combo 5 以上使用 `5+` |
| `Parameter!J9:AI14` | C2 倍率權重 |
| `Parameter!J19:AI24` | C3 倍率權重 |
| 六張正式 `*_Symbol` 工作頁 `L4:Q303` | `strips[].symbols`；實際輪帶長度由正 Weight 的最後一列決定 |
| 六張正式 `*_Symbol` 工作頁 `Z4:AE303` | `strips[].weights`；競品還原輪帶有效位置皆為 1，其餘為 0 |
| 六張正式 `*_Symbol` 工作頁 `AH4:AM15` | 保留版面相容但全部為 0，不是 Runtime 輸入 |

六張正式 Runtime 表為 `BG_Symbol`、`BG_Symbol (2)`、`BG_Symbol (3)`、`FG_Symbol`、`FG_Symbol (2)`、`BF_Symbol`。`FG_Symbol (3)` 仍為歷史保留頁，不匯入 Config。

## Demogame / Runtime Metadata

下列欄位由轉檔工具的固定 Metadata 產生，禁止在 `index.html` 另寫一份：

- `denom`
- `bet_options`
- `initial_balance`
- `drop_mode = cascade_drop`
- `fg_trigger_count`, `fg_retrigger_count`, `cascade_limit`
- `supported_bet_modes`
- `config_type = base`, `config_code = base`
- `is_competitor_model = true` 與 `initial_version_rule = competitor_model_starts_at_0`
- `bet_tier_thresholds`：小 Bet `< 2`、中 Bet `<= 100`、大 Bet `> 100`
- `link.enabled = false`
- `rtp_accounting`：H027 目前將 FG 派彩列入 Bonus Game、BG 派彩列入 Game，Link 不適用；正式 RTP 目標仍為 pending
- `card_system.enabled = false`：尚無 RTP／Variant 來源時不建立空白 Profile／Mode；以 `reason` 明確說明停用原因

`cascade_drop` 表示中獎符號消除後，同輪上方保留符號向下補位；空格從初始可視窗頂端之前的位置沿同一條首尾相接輪帶依序補入。Simulator 與 Demogame 使用相同方向與索引規則。

Base／Card System Off 且 `config_rtp_file` 尚無正權重 BG range 卡時，代表尚未指定 Profile cap；`bg_trigger_fg_pay` 暫以未設上限的自然觸發 BG 得分輸出。`Multiplier Line` 仍完整保留各 `Interval_Upper` 的累計 count/pay；未來載入正式 RTP／Variant Config 後，Simulator 必須從該 Profile 的最大正權重 BG range 取得完全相同的上限並套用，不得寫死。
