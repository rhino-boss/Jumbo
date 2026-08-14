# H016 XLSX / Config 使用對照

| 數學文件 | Config | Simulator 用途 | 版本格式 |
|---|---|---|---|
| `H0161.xlsx` | `config.js` | 自然機率、輪帶、停輪權重、補牌、Paytable、Feature 與共用遊戲參數 | 1 碼；目前由 `2.0.0.0` 的第一碼產生為 `2` |
| `H016192A.xlsx` | `config_92A.js` | 92A 的 Card System 區間、倍率權重與 RTP／Variant metadata | 4 碼 |
| `H016194A.xlsx` | `config_94A.js` | 94A 的 Card System 區間、倍率權重與 RTP／Variant metadata | 4 碼 |

Simulator 先載入 `config_file`（固定為 `config.js`）作為自然機率資料，再載入
`config_rtp_file`。RTP Config 只允許提供 `card_system`、`parsheet_id`、
`excel_version`、`rtp_label`、`runtime_version` 與 `source_multiplier_xlsx`；不得覆寫
`config.js` 的輪帶、Paytable、Feature 或其他自然機率資料。

目前 `config_92A.js`／`config_94A.js` 仍保留完整共用資料；
Simulator 載入時會驗證其共用資料必須與 `config.js` 完全一致，並只採用上述 RTP 欄位。

## 已知版本待辦

`H0161.xlsx` 的 `Overview!B3` 目前為 `2.0.0.0`，但規範要求基礎文件只填 1 碼；
`H016192A.xlsx`／`H016194A.xlsx` 目前為 `1.0.0.2`，第一碼也尚未與基礎版本一致。
本次拆檔不修改 Excel，正式發版前必須先統一三份 XLSX 的版本，再重新產生三份 Config。
