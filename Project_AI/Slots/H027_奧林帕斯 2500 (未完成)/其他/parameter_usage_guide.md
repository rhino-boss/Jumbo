# H027 Simulator 參數使用說明

## 前段設定

- `CONFIG_FILE`：目前預設並使用 `config_92A.js`。
- `TOTAL_ROUNDS`：模擬局數，預設 100,000。
- `BET_MODE`：`0` Normal、`1` Extra Bet、`2` Buy Feature；不支援模式 `3`。
- `BET_MULTI`：押注倍率。
- `CARD_SYSTEM_ENABLED`：卡片系統總開關；`True` 開啟、`False` 關閉。
- `CARD_SYSTEM_IS_NEWBIE`：Normal Bet 使用者 Profile；`True` 為 Newbie，`False` 為 Oldhand。
- `THREADS`：ThreadPool 執行緒數。
- `OUTPUT_REPORT`：是否輸出 xlsx 報表。
- `SHOW_CONSOLE_SUMMARY` / `SHOW_CONSOLE_DETAIL`：摘要與明細顯示。
- `RUN_SINGLE_SPIN_DEBUG`：單局檢查模式。
- `RUN_ALL_COMBINATIONS`：依 `BATCH_COMBINATIONS` 執行多組版本／模式。

設定可用同名 `H027_` 環境變數覆寫，適合 PowerShell 或 VS Code Interactive Window。

## PowerShell 執行範例

在 `C:\Users\rhinshen\Mine\個人工作區\2_Program` 執行：

```powershell
$env:PYTHONUTF8='1'
$env:H027_TOTAL_ROUNDS='100000'
$env:H027_CONFIG_FILE='config_92A.js'
$env:H027_BET_MODE='0'
$env:H027_CARD_SYSTEM_ENABLED='true'
$env:H027_CARD_SYSTEM_IS_NEWBIE='false'
.\.venv\Scripts\python.exe '.\Project_AI\Slots\H027_奧林帕斯 2500\Simulator.py'
```

只看 console、不輸出報表：

```powershell
$env:H027_OUTPUT_REPORT='false'
```

模式值：

- `0`：Normal Bet，單局成本 100 Credit。
- `1`：Extra Bet，單局成本 200 Credit；使用 5 次 Normal 候選盤提升 FG 機率。
- `2`：Buy Feature，單局成本 10,000 Credit。

## 資料流

`Source/H027192A.xlsx` → `Source/xlsx_to_config.py` → `config_92A.js` → `Simulator.py` → `Record/*.xlsx`

報表檔名以前綴 `H0271`（PARsheet ID）命名；版本移除標點，例如 `3.0.0.1` 寫成 `3001`，10 的整數次方局數以 `10+指數` 表示，例如 `10**5` 寫成 `105`。範例：`H0271_3001_2607141724_betmode0_105_oldhand_card.xlsx`。程式可從檔案、終端機或 VS Code Interactive Window 執行，會自行尋找遊戲資料夾。

## 卡片系統

- 前段 `CARD_SYSTEM_ENABLED` 是執行開關；同樣可用 `H027_CARD_SYSTEM_ENABLED=true/false` 覆寫。
- config 的 `card_system.enabled` 也必須為 `true` 才會實際啟用，權重來自 xlsx `Multiplier_Weight`。
- Normal Bet 可用 `H027_CARD_SYSTEM_IS_NEWBIE=true/false` 切換 Newbie／Oldhand。
- Extra Bet 尚無專用卡片權重，因此目前不啟用卡片篩選。
- Buy Feature 固定使用 `Weight_BF_FG`。
- 同一張卡不符合時重跑，最多 5000 次。
- 報表顯示 retry 統計；啟用時檔名以 `_card` 結尾。
- 卡片倍率以 Normal Bet 的 100 Credit 為分母；Buy Feature 亦沿用此基準。

批次模式每筆可獨立設定：

```python
{
    "config_file": "config_92A.js",
    "bet_mode": 0,
    "total_rounds": 10**5,
    "card_system_enabled": True,
    "card_system_is_newbie": False,
}
```

## H027 C2 與輪帶處理

- 每次 Spin 只抽 Normal／Super／Ultimate 三種權重類型。
- 遊戲中沒有 Wild；載入 xlsx 時排除所有 WW 輪帶位置。
- C2 值池固定為 `2、3、4、5、8、10、12、15、20、25、50、100、500、1000、2500`。
- 每次中獎消除，消除前已在盤面的 C2 往後升一級，最高 2500x。
- xlsx 的 150x、200x、250x 權重不納入抽選；2500x 目前由 Cascade 升級取得。
- 不使用 Bad 權重切換與 FG 輪帶強制替換；目標結果分布改由卡片系統依 xlsx 權重篩選。
