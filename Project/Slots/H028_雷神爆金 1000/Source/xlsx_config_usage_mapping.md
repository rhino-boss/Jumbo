# H028 XLSX ↔ config 雙向使用與映射對照

本文件合併原本的 `xlsx_config_usage_mapping.md` 與 `config_xlsx_usage_mapping.md`，以目前唯一入口 `model_sync.py`／`update.bat` 為準。

## 1. 檔案架構與資料所有權

H028 數學模型拆成「共用模型」與「RTP 版本」兩類工作簿。

| 檔案 | 資料所有權 | 用途 |
| --- | --- | --- |
| `H0281.xlsx` | 賠率、六張 Symbol 表、輪帶、Symbol Weight、MegaWay、MY、Post Scatter、Drop1～5、Parameter | 所有 RTP 版本共用的基礎模型 |
| `H0281<RTP><版型>.xlsx` | `Overview!B3` 版本、`Detail`／`Detail_Newbie` 與 `Multiplier_Weight` 卡片權重 | 例如 `H028192A.xlsx`、`H028192B.xlsx`、`H028194A.xlsx` |
| `config_<RTP><版型>.js` | Simulator 與 index 的執行參數 | 例如 `config_92A.js`、`config_92B.js`、`config_94A.js` |

檔名不是寫死的白名單：`model_sync.py` 依 `H0281<RTP><版型>.xlsx` 與 `config_<RTP><版型>.js` 自動配對。因此工具已支援 H028 共用模型、H028192A、H028192B；目前正式目錄實際存在 92A、94A，尚未建立正式 92B 工作簿。

## 2. 轉換方向

| 指令 | 方向 | 寫入內容 | 不寫入內容 |
| --- | --- | --- | --- |
| `model_sync.py export` | XLSX → config | 共用模型全部映射欄位、版本、卡片權重 | 固定 metadata 由工具提供 |
| `model_sync.py import`（共用模型） | config → `H0281.xlsx` | 共用模型映射欄位 | RTP 版本卡片資料、固定 metadata |
| `model_sync.py import`（RTP 工作簿） | config → `H0281<RTP><版型>.xlsx` | 版本、Detail 卡片輸入／快取、Multiplier Weight 公式快取 | 共用 Symbol 模型、固定 metadata |

`Multiplier_Weight` 由 `Detail!K`／`Detail_Newbie!K` 公式推導。config → RTP XLSX 會回填 `Fix Num`、自然分布快取、Weight／RTP 快取，並保留原公式；不會把公式改成固定值。

## 3. 參數組與工作表

| config 參數組 | XLSX 工作表 | 初始輪帶／權重範圍 |
| --- | --- | --- |
| `BaseGame*1` | `BG_Symbol` | `M4:S203`／`AC4:AI203` |
| `BaseGame*2` | `BG_Symbol (2)` | `M4:S203`／`AC4:AI203` |
| `BaseGame*3` | `BF_Symbol` | `M4:S203`／`AC4:AI203` |
| `FreeGame*1` | `FG_Symbol` | `M4:S203`／`AC4:AI203` |
| `FreeGame*2` | `FG_Symbol (2)` | `M4:S203`／`AC4:AI203` |
| `FreeGame*3` | `FG_Symbol (3)` | `M4:S203`／`AC4:AI203` |

六張 Symbol 表的 R1～R7 都固定為 200 格。

## 4. Symbol 表共用映射

| XLSX 範圍 | config 欄位 | 形狀／說明 |
| --- | --- | --- |
| `M4:S203` | `*Symbol*` | 7 輪 × 200 格；真正的 Symbol 輪帶 |
| `AC4:AI203` | `*SymbolWeight*` | 7 輪 × 200 個停輪權重 |
| `C33:H47` | `*MegaWay*` | R1～R6 × 15 種大型符號版型 |
| `C51:C63` | `*MY*` | 13 個 Mystery 轉換權重 |
| `B67:C74` | `*PostC1` | Scatter 顆數 0～7 與權重 |
| `AL4:AR29` | `*Drop1` | 7 輪 × 26 個符號權重 |
| `AL33:AR58` | `*Drop2` | 7 輪 × 26 個符號權重 |
| `AL62:AR87` | `*Drop3` | 7 輪 × 26 個符號權重 |
| `AL91:AR116` | `*Drop4` | 7 輪 × 26 個符號權重 |
| `AL120:AR145` | `*Drop5` | 7 輪 × 26 個符號權重 |

### Symbol 與 Symbol ID

- XLSX → config：依各 Symbol 表 `A4:J29` 的 Symbol／ID 對照，將 `M:S` 的符號名稱轉成數字 ID。
- config → XLSX：依同一份 ID 對照將數字 ID 轉回符號名稱，寫入 `M:S`。
- `U:AA` 是 Excel 的 Symbol ID 公式區，不是 export 的讀取來源。import 後會恢復公式、移除失效的 `calcChain.xml` 關聯，並要求 Excel 完整重算。
- config 中只要出現 Symbol，就必須能在工作表 `A4:J29` 找到對應 ID，否則轉換會直接失敗。

### Scatter 與特殊表

- SC（ID 1）不放在 BG／FG 初始輪帶，由各表 `B67:C74` 的 Post Scatter 產生。
- Drop1～Drop5 可以依設定掉落 SC。
- `BF_Symbol` 對應 `BaseGame*3`，只供 Feature Buy 觸發畫面使用；其有效停輪權重必須維持零 Ways 得分。

## 5. 其他共用欄位

| XLSX 位置 | config key | 用途 |
| --- | --- | --- |
| `H0281.xlsx` Overview 的 M1 起始 `C:F` 11 列 | `linkpoint` | 3～6 輪 Ways 賠率 |
| `Parameter!C5:C6` | `ReelWeight` | BG Table 1／2 選擇權重 |
| `Parameter!C11:C13` | `FreeReelWeight` | FG 初始 Table 1／2／3 權重 |
| `Parameter!C18:C20` | `FreeTriggerReel` | FG Retrigger Table 1／2／3 權重 |

固定的 `game_id`、名稱、coin-in、bet mode 與 Feature Buy 倍率由 `model_sync.py` 的 `METADATA` 提供，不回填 XLSX。

## 6. RTP 版本與卡片權重

| RTP 工作簿位置／欄名 | config 位置 |
| --- | --- |
| `Overview!B3` | `excel_version` |
| `Weight_NB_BG_Newbie` | `card_system.newbie.normal_bet.weight_bg` |
| `Weight_NB_FG_Newbie` | `card_system.newbie.normal_bet.weight_fg` |
| `Weight_NB_BG` | `card_system.oldhand.normal_bet.weight_bg` |
| `Weight_NB_FG` | `card_system.oldhand.normal_bet.weight_fg` |
| `Weight_BF` | `card_system.oldhand.buy_feature.weight_fg` |

倍率區間採 `(min, max]`。Normal Bet 先抽 `weight_bg`；若抽到 `free_game`，觸發 FG 後再抽同 Profile 的 `weight_fg`，並以完整 FG Session 得分比對區間。

FG 模型週期直接由 BG 卡片權重計算：`sum(weight_bg) ÷ Free Game card weight`。Simulator 的 `fg_cycle_model`／`fg_trigger_rate_model` 是設定值；`fg_cycle_observed`／`fg_trigger_rate_observed` 是有限模擬樣本值，兩者不可混用。卡片關閉時沒有可由卡片權重推導的模型週期，因此模型欄位為 0／介面顯示 `--`。

目前卡片限制：自然發生率低於 0.1% 或區間上限超過 20,000x 時權重為 0。Oldhand Normal Bet 的 BG／FG 目標分別為 72%／20%（92A）或 72%／22%（94A）；Newbie 為 72%／21%；Buy Feature 僅計 FG，目標 92.5%。

## 7. 目前模型重點

| 項目 | 目前設定 |
| --- | --- |
| `ReelWeight` | BG Table 1／2 |
| `FreeReelWeight`／`FreeTriggerReel` | `[6000,4500,4500]`，FG1／FG2／FG3 = 40%／30%／30% |
| FG Table 定位 | FG1 競品表、FG2 連消表、FG3 累積倍數表 |
| Golden M1 | 所有初始輪帶與 Drop1～5 都為 0；M1 只使用普通 ID 2 |
| 初始金框 | FG1 15%、FG2 20%；各輪 200 格 |
| 掉落金框 | FG1、FG2 Drop1～5 為 10% |
| FG3 M1 R1～R7 | `[3,20,20,12,12,4,4]` |

## 8. 使用方式

### 互動工具

```bat
update.bat
```

可選：

1. `config`：全部 RTP 工作簿 → 對應 `config_*.js`
2. `xlsx`：config → 原地更新 `H0281.xlsx`，並將所有已存在的 `config_<RTP><版型>.js` 回填至對應 RTP 工作簿
3. `check`：只核對，不寫檔

也可以直接執行：

```powershell
# XLSX → config，並核對所有 RTP 版本
.\.venv\Scripts\python.exe .\Source\model_sync.py export --all --sync-default --check

# config → XLSX，只檢查映射差異
.\.venv\Scripts\python.exe .\Source\model_sync.py import `
  --config .\config_92A.js `
  --source .\Source\H028192A.xlsx `
  --check

# config → 所有已存在的 RTP 工作簿
.\.venv\Scripts\python.exe .\Source\model_sync.py import --all-variants

# 依最新無卡片報表重新校正所有卡片倍率權重
.\.venv\Scripts\python.exe .\Source\tune_multiplier_weights.py `
  --normal-report <Normal-Bet-無卡片報表.xlsx> `
  --bf-report <Buy-Feature-無卡片報表.xlsx>
```

## 9. 操作限制與驗證

- 執行寫入前必須儲存並關閉 Excel；存在 `~$*.xlsx` 時 `update.bat` 會警告。
- `import --in-place` 必須明確加入 `--overwrite-formulas`，工具使用暫存檔進行原子置換。
- export 的 `--check` 會逐 key 比對生成結果與既有 config。
- import 寫出後會立即執行 config → XLSX → config round-trip；任何共用映射 key 不一致即失敗。
- RTP 工作簿回填時保留 Detail／Multiplier Weight 公式，只更新輸入與公式快取；另會移除失效的 `calcChain.xml` 關聯並要求 Excel 完整重算。
- `--all-variants` 只處理同時存在 config 與工作簿的版本；例如正式建立 `H028192B.xlsx` 與 `config_92B.js` 後會自動納入。
- round-trip 驗證會逐一確認共用模型與卡片資料；公式保留與快取值也需通過檢查。
