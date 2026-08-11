# H045 xlsx -> config.js -> Simulator / index 對照表

## 範圍

本文件對照目前專案中的：

- `Source/H045192.xlsx`、`Source/H045194.xlsx`
- `config_92.js`、`config_94.js`
- `Simulator.py`
- `index.html`（即 demogame）

目的：

1. 說明 `xlsx` 哪些 sheet / 欄位會進到 `config_*.js`
2. 說明 `config_*.js` 每個欄位在哪裡被 `Simulator.py` / `index.html` 使用
3. 標示哪些欄位是「直接來自 xlsx」、哪些是「由 xlsx 衍生」、哪些是「程式常數」

## 流程

1. 在 Excel 調整 `Multiplier_Weight_Newbie` / `_Oldhand` 的 `Fix Num`（唯一的調校輸入）
2. 存檔 —— Excel 會把整條公式鏈重算到 `Weight`，並連動 `Overview` 的 RTP
3. 執行 `update_config.bat`（或 `py xlsx_to_config.py <xlsx> <config.js>`）
4. `Simulator.py` 讀 `config_*.js`
5. `index.html` 也讀同一份 `config_*.js`

> **注意**：`xlsx_to_config.py` 讀的是公式的**快取值**。若活頁簿是被 openpyxl 之類的程式改過（openpyxl 存檔會清掉快取），必須先用 `其他/recalc.ps1` 讓 Excel 重算並存檔，否則卡片系統會讀成空的。

## 說明約定

- `直接`：可直接對應到 `xlsx` 可見欄位
- `衍生`：由 `xlsx` 原始欄位轉換或重新編碼得到
- `靜態/程式`：`xlsx` 沒有來源，是程式常數
- `未使用`：欄位存在於 config，但 runtime 沒有真正讀它

---

## A. config.js 整體欄位對照

| config 欄位 | xlsx 來源 | 類型 | Simulator.py | index.html | 備註 |
| --- | --- | --- | --- | --- | --- |
| `game_id` | 無（程式常數 `"H045"`） | 靜態/程式 | `GAME_ID` | 標題列 | |
| `parsheet_id` | 由 xlsx 檔名取得 | 衍生 | `PARSHEET_ID` | 未使用 | `H045192` / `H045194` |
| `name_zh` / `name_en` | 無 | 靜態/程式 | 報表標題 | 標題列 | |
| `rtp_label` | 由檔名 `192` / `194` 判定 | 衍生 | 未使用 | 未使用 | 92 或 94 |
| `reel_num` | `Parameter` → Feature Setting → `Reel Num` | 直接 | 盤面尺寸 | 盤面尺寸 | 5 |
| `window_size` | `Parameter` → Feature Setting → `Visible Window Size` | 直接 | 盤面尺寸 | 盤面尺寸 | 4 |
| `max_ways` | `Parameter` → Feature Setting → `Max Ways` | 直接 | 未使用 | 資訊顯示 | 1024 |
| `symbol_names` | 無（程式對照表） | 靜態/程式 | 報表欄名 | 圖片對應 | id -> `WW1`/`C1`/`M1`… |
| `pays` | `Overview` → Pay Table 的 `3` / `4` / `5` 欄 | 直接 | `evaluate()` | `evaluate()` | 除以 100 存成 bet 倍數 |
| `tables.*.reels` | 各 `*_Symbol` 工作頁 K:O 欄的 400 格輪帶 | 直接 | `Reel.symbols` | `makeBoard()` | 符號名轉 id |
| `tables.*.weights` | 各 `*_Symbol` 工作頁 W:AA 欄的 Symbol Weight | 直接 | `Reel.cumulative` | `draw()` | 逐格權重 |
| `tables.*.random_wild` | `Parameter` → Random Wild Weight | 直接 | `add_w2()` | `selectW2Targets()` | 0 / 2 / 3 / 4 的權重 |
| `tables.*.multipliers` | `Parameter` → Win Multiplier Ladder | 直接 | `spin()` | `spin()` | BG `1,2,3,5,10`；FG `2,4,6,10,20` |
| `base_table_weights` | 無 | 靜態/程式 | 未使用 | 未使用 | 關閉卡片系統時才有意義 |
| `card_system.profiles.weight_1` | `Multiplier_Weight_Newbie` 的 Lower / Upper / Table / Weight | 直接 | `pick_card()` | `pickCard()` | 新手 |
| `card_system.profiles.weight_2` | `Multiplier_Weight_Oldhand` 同上 | 直接 | `pick_card()` | `pickCard()` | 老手 |
| `free_game_mix.groups` | `Parameter` → Free Game Table Mix Weight | 直接 | `free_queue()` | `freeQueue()` | 依卡片的 Table 代碼（D / E）選組 |
| `free_game_mix.high_variant_weights` | `Parameter` → Free Game High Table Weight | 直接 | `high_table()` | `highTable()` | A / K / Q / J |
| `free_spins` | `Parameter` → Feature Setting → `Free Spins` | 直接 | `free_session()` | `freeSession()` | 10 |
| `retrigger_spins` | `Parameter` → `Retrigger Spins` | 直接 | `free_session()` | `freeSession()` | 5 |
| `retrigger_high` | `Parameter` → `Retrigger High Spins` | 直接 | `free_session()` | `freeSession()` | 加局中的高表場數 |
| `free_spin_cap` | `Parameter` → `Free Spin Cap` | 直接 | `free_session()` | `freeSession()` | 50 |
| `scatter_trigger` | `Parameter` → `Scatter Trigger Count` | 直接 | `round()` / `free_session()` | `play()` / `freeSession()` | 3 |
| `buy_price` | `Parameter` → `Buy Feature Price (x Bet)` | 直接 | `wager_for_mode()` | `play()` | 40.5 |
| `source_xlsx` | 由 xlsx 檔名取得 | 衍生 | 未使用 | 未使用 | 追溯用 |

---

## B. 依工作頁分組的來源對照

### B1. `Overview`

| xlsx 位置 | config 欄位 | 備註 |
| --- | --- | --- |
| Pay Table 的 `Symbol` / `3` / `4` / `5` | `pays` | 只取 M1~J 八個計分符號；金框列與 base 同賠率，不另存 |

其餘欄位（Model / Version / Total RTP / Pay Back / Hit% / Pulls-Hit / Free Spins Setting / Feature）皆為**顯示與送驗用**，不進 config。其中 Total RTP 與 Pay Back 是公式，連動 `Multiplier_Weight_*` 的彙總列。

### B2. `Parameter`

| 區塊 | config 欄位 |
| --- | --- |
| Table Selection - Base Game | 不進 config（實際選表由卡片的 Table 欄決定） |
| Random Wild Weight (Weight/Total) | `tables.*.random_wild` |
| Win Multiplier Ladder | `tables.*.multipliers` |
| Free Game Table Mix Weight | `free_game_mix.groups` |
| Free Game High Table Weight | `free_game_mix.high_variant_weights` |
| Feature Setting | `free_spins` / `retrigger_spins` / `retrigger_high` / `free_spin_cap` / `scatter_trigger` / `buy_price` / `reel_num` / `window_size` / `max_ways` |

### B3. `Multiplier_Weight_Newbie` / `Multiplier_Weight_Oldhand`

每個區段（Base Game / Free Game / Buy Feature）的公式鏈：

```
Simulator Rate = Cnt / SUM(Cnt)
Simulator RTP  = Pay / Cnt / Coin in / 5
Rate           = 依 Table 欄 INDEX/MATCH 取對應變體的 Simulator Rate
Fix Rate       = Rate x Fix Num           <- Fix Num 是唯一調校輸入
Final Rate     = Fix Rate / SUM(Fix Rate)
Weight         = INT(Final Rate x Threshold)
RTP            = 對應變體的 Simulator RTP x Weight / Threshold
```

只有 `Lower` / `Upper` / `Table` / `Weight` 四欄會進 config。

兩個例外：

- Base Game 最後一列是 FG Trigger 卡，`Rate` 是手動輸入的實測觸發率（不查表），`Final Rate` 直接取 `Fix Rate` 而非佔比
- Base Game 第一列的 `Weight` 是餘數（`Threshold - 其餘列總和`），讓總和剛好等於 Threshold

### B4. `Multiplier_Weight`

新手／老手並列的檢視頁，每一格都是連到上述兩張工作頁的參照，不進 config。

### B5. `BG_Symbol` / `BG_Symbol (2)` / `FG_Symbol` ~ `FG_Symbol (4)` / `FG_Symbol (5)` / `BF_Symbol`

| xlsx 欄位群 | config 欄位 | 備註 |
| --- | --- | --- |
| C:G 欄 符號數量 | 不進 config | 由 K:O 欄輪帶統計而來的檢核用資訊 |
| K:O 欄 Symbol | `tables.*.reels` | 400 格輪帶 |
| Q:U 欄 Symbol ID | 不進 config | K:O 的 id 版，供人閱讀 |
| W:AA 欄 Symbol Weight | `tables.*.weights` | 逐格權重；`BF_Symbol` 用 0/1 遮罩保證進場必有 3 顆以上 C1 |

工作頁與遊戲模式的對應：

| 工作頁 | 用途 | config table key |
| --- | --- | --- |
| `BG_Symbol` | BG 高表 | `bg_high` |
| `BG_Symbol (2)` | BG 低表 | `bg_low` |
| `FG_Symbol` | FG 高表 A | `fg_high_a` |
| `FG_Symbol (2)` | FG 高表 K | `fg_high_k` |
| `FG_Symbol (3)` | FG 高表 Q | `fg_high_q` |
| `FG_Symbol (4)` | FG 高表 J | `fg_high_j` |
| `FG_Symbol (5)` | FG 低表 | `fg_low` |
| `BF_Symbol` | Buy Feature 進場表 | `buy` |

### B6. 不進 config 的工作頁

- `Description`：玩法流程說明
- `OP Jackpot`：C1 出現次數統計

---

## C. 目前值得注意的欄位

| 欄位 | 現況 |
| --- | --- |
| `base_table_weights` | 卡片系統啟用時不會用到；關閉卡片系統時 `Simulator.py` 也只會固定用 `bg_high`，此欄實際未被讀取 |
| `max_ways` / `rtp_label` / `source_xlsx` | 僅供顯示與追溯 |
| `tables.buy` | `index.html` 的 `buyEntry()` 會用它產生進場盤面；`Simulator.py` 的 Buy 模式直接進 FG，**沒有用到這張表**（見下） |

### C1. 已知的規則書 / 數學模型落差

`game_rule.md` §8.1 與 §9.5.2 寫「Buy 進場局的 Ways / Cascade 得分正常計入」，但卡片系統的 `Buy Feature` 區間是對 **Free Game 得分**做匹配，`Simulator.py` 的 Buy 模式因此不跑進場局、`pay_bg` 恆為 0。若改成計入進場局得分，Buy Feature 的 RTP 會超出卡片權重的目標值。此處待企劃確認要調整哪一邊。

---

## D. 結論

- `xlsx` 提供數學、輪帶與卡片權重
- `config_*.js` 是統一執行格式
- `Simulator.py` 與 `index.html` 吃同一份 config，邏輯一一對應

唯一的調校入口是 `Multiplier_Weight_*` 的 `Fix Num`；改完存檔，`Overview` 的 RTP 會自動重算，再跑 `update_config.bat` 即可同步到模擬器與 demogame。
