# H027 xlsx / config 轉換對照

## 入口

- `model_sync.py export`：`H0271.xlsx` → `config_92A.js`
- `model_sync.py import --in-place`：`config_92A.js` → `H0271.xlsx`
- `model_sync.py export --check`：檢查 config 是否與 xlsx 一致，不寫檔。
- `model_sync.py import --check`：列出 config 寫回 xlsx 時的差異，不寫檔。
- Windows 可直接執行 `update.bat`，操作方式與 H028 一致。

## 工作簿對照

| xlsx | config |
|---|---|
| `Overview!B2:B3` | `model`, `excel_version` |
| `Overview!A7`, `B11:B13`, `B17:G17` | 底注、Bet 倍數、視窗 |
| `Overview!A30:I41` | `symbol_codes`, `symbol_ids`, `pay_table` |
| `Parameter!C28:C52` | `multiplier_levels` |
| `Parameter!K4:AI4` | `parameter.super_multiplier` |
| `Parameter!B4:D13` | BG/FG 輪帶與 Free Spin 設定 |
| `Parameter!B18:H23` | `use_c3.weights_by_reel` |
| `Parameter!J9:AI14` | C2 倍數權重 |
| `Parameter!J19:AI24` | C3 倍數權重 |
| `BG_Symbol`, `BG_Symbol (2)`, `FG_Symbol` 的 `L4:Q303` | `strips[].symbols` |
| `BG_Symbol`, `BG_Symbol (2)`, `FG_Symbol` 的 `S4:X303` | Symbol ID 公式快取（寫回時保留公式） |
| `BG_Symbol`, `BG_Symbol (2)`, `FG_Symbol` 的 `Z4:AE303` | `strips[].weights` |
| `BG_Symbol`, `BG_Symbol (2)`, `FG_Symbol` 的 `AH4:AM15` | `strips[].drop_weights`（C1～TE × R1～R6） |

## 限制

- Normal Bet BG 使用 `BG_Symbol` 與 `BG_Symbol (2)`，Parameter 默認權重為 1:1；同一 Spin 的初始盤面與所有掉落固定使用同一張 Table。
- Feature Buy 維持只使用 `BG_Symbol`；FG 只使用 `FG_Symbol`。
- `BG_Symbol (3)`、`FG_Symbol (2)/(3)` 為歷史分頁，不參與轉換。
- BG 兩表合併後的初始符號 counts 與掉落 weights 由 `calibrate_bg_two_tables.py` 保持為競品 R1～R6 目標分布。
- config → xlsx 採原子取代，並設定 Excel 重新計算。Symbol ID 公式不會被改成固定值。
