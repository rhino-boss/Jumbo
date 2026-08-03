# Math Document Description — H026192A（彩罐熱舞 1000 / Pinata Beat 1000）

**適用範圍：Normal Bet（一般下注）**

| 項目 | 值 |
| --- | --- |
| Model | H026192A |
| Version | 4.0.0.8（`Overview!B3`） |
| Game ID | 101014 |
| 資料來源 | `Source/H026192A.xlsx` |
| 對應程式 | `Simulator.py`、`index.html`（皆讀 `config_92A.js`） |
| 盤面 | 5 輪 × 3 列記分（程式內部為 4 列，最上列不記分） |
| 線數 | 20 條固定線，左→右 |
| Normal Bet Coin In | 100（Base Bet 100 × Price 1） |
| Normal Bet Total RTP | 91.99998%（BG 68.00% + FG 24.00%） |

> 本文件只說明 Normal Bet 會用到的參數。Extra Bet（Price ×2）、Buy Feature（Price ×75）與 `BF_Symbol` 工作表僅在需要對照時提及，不展開。

---

## 0. 名詞與代號

| 代號 | 意義 |
| --- | --- |
| BG | Base Game，付費轉動的主遊戲場景 |
| FG | Free Game，免費遊戲場景 |
| Gold / 彩虹框 / 金框 | `G1~GJ` 這一類帶倍數框的符號 |
| Table / Strip | 一組輪帶設定（一個 `*_Symbol` 工作表 = 一張 table） |
| Combo | 同一次 spin 內第幾次連消（消除→掉落→再判獎算一次） |
| Cascade | 中獎符號消失、上方符號下墜、空位補新符號的整個過程 |

Table 編號（程式內 `table_id`，順序固定）：

| table_id | 工作表 | 程式代號 | 場景 | Normal Bet 是否使用 |
| --- | --- | --- | --- | --- |
| 0 | `BG_Symbol` | B1 | BG | ✅ 主要表 |
| 1 | `BG_Symbol (2)` | B2 | BG | ✅ 全金框表 |
| 2 | `BG_Symbol (3)` | B3 | BG | ✅ 觸發 FG 專用表 |
| 3 | `FG_Symbol` | F1 | FG | ✅ 累積倍率 < 10 |
| 4 | `FG_Symbol (2)` | F2 | FG | ✅ 累積倍率 < 20 |
| 5 | `FG_Symbol (3)` | F3 | FG | ✅ 累積倍率 ≥ 20 |
| 6 | `BF_Symbol` | BF | Buy Feature | ❌（Normal Bet 不會抽到） |

---

## 1. 參數如何進入程式（資料流）

```
H026192A.xlsx
   │  Source/xlsx_to_config.py
   ▼
config_92A.js          ← 唯一的 runtime 設定檔
   ├──► Simulator.py   （大量模擬 / 出報表）
   └──► index.html     （demo game）
```

三個必須先理解的轉換規則，否則會誤判「改了 xlsx 卻沒生效」：

1. **所有權重在轉檔時都會被轉成「累積權重」**（`*_cum`）。runtime 抽樣時是「取 `[0, total)` 的整數隨機值，找第一個累積值大於它的索引」。所以 xlsx 上的權重值不需要是機率、也不需要湊成 100%，只要相對大小正確即可；但每一組權重的**總和就是該組的分母**。
2. **金框符號在轉檔時被拆成兩層**：盤面只存「基底符號」（`base_symbol_of`，例如 `G1 → M1`），另外用 `gold_mask` 記「這格是不是金框」、`multi_mask` 記「這格的倍數是多少」。
   - 因此 `Overview` 的 Pay Table 裡 `G1~GJ` 那 9 列賠率**程式永遠不會讀到**（轉檔時 `is_score_symbol` 被設為 0）。判獎一律用基底符號的賠率。這 9 列只是給人看的對照。
3. **`Description` 工作表與各表左側的統計欄位都不進 config**，純文件/檢核用。程式只讀本文件標示為「程式讀取」的欄位。

---

## 2. 盤面座標系統（讀參數前必須先懂）

| 程式變數 | 值 | 說明 |
| --- | --- | --- |
| `reel_num` | 5 | 輪數 |
| `window_size` | 3 | `Overview!B31`，**記分**列數 |
| `DISPLAY_WINDOW_SIZE` | 4 | = `window_size + 1`，程式實際持有的列數 |
| `SCORE_ROW_OFFSET` | 1 | 記分區從第 1 列開始 |

```
row 0  ← 預覽列（不判獎、不算 Scatter，但金框會先被分配倍數）
row 1  ┐
row 2  ├ 記分區 3×5（判線、算 Scatter 都只看這裡）
row 3  ┘
```

停輪時取輪帶上連續 4 格填入 row 0~3；`Parameter` 的 Line 表寫的 0/1/2 會自動 +1 對應到 row 1~3。

**這個 offset 造成一個很容易誤解的行為**：預覽列（row 0）的金框在開局分配倍數時，走的是 **After Eliminate** 那一組權重，不是 Before。詳見 §4.5。

---

## 3. `Overview` 工作表

### 3.1 基本欄位（程式讀取）

| 儲存格 | 內容 | config 欄位 | 程式用途 |
| --- | --- | --- | --- |
| `B2` | `H026192A` | `game_id` | 報表標題、輸出檔名 |
| `B3` | `4.0.0.8` | `excel_version` | 版本標記，寫進輸出檔名 |
| `A7` | `100` | `default_coin_in` | 押注基準 |
| `B11` | `1` | `normalbet` | Normal Bet 倍率 |
| `B31` | `3` | `window_size` | 記分列數（見 §2） |
| `A43:F62` | Pay Table | `pay_table` / `symbol_id` / `symbol_str` | 判獎 |

**Coin In 計算（Normal Bet）**

```python
coin_in = bet_multi * default_coin_in * normalbet
        = bet_multi * 100 * 1
```

`bet_multi` 是玩家選的下注倍數（模擬時固定 1）。所有 RTP、倍率統計都用 `pay_total / coin_in`。

### 3.2 RTP 區塊（程式**不**讀取，是驗證用）

| 儲存格 | 值 | 意義 |
| --- | --- | --- |
| `C11` | 0.9199998 | Normal Bet 總 RTP，公式 `=SUM(B18:B19)` |
| `B18` | 0.6799998 | BG 貢獻，來自 `Multiplier_Weight_Oldhand!C7` |
| `B19` | 0.2400001 | FG 貢獻，來自 `Multiplier_Weight_Oldhand!D7` |
| `D18` | 238.34 | **FG 週期**（來自 `Multiplier_Weight_Oldhand!G7`） |
| `C18` | 0.0041956 | `=1/D18`，即 **FG 觸發率** |

> ⚠️ `C17` 標題寫 `Hit%`，但這一格填的是 **FG 觸發率**，不是連線中獎率。可以反推驗證：`Multiplier_Weight!G68`（Oldhand Normal Bet 的 Free Game 卡權重）= 4,195,668，該欄總權重約 1,000,000,000，4,195,668 / 1e9 = 0.0041956，完全吻合。也就是說 **Normal Bet 的 FG 觸發率是被卡片系統直接指定的**（見 §6）。
>
> ⚠️ `C11`（92%）取的是 **Oldhand** 的數字。`Multiplier_Weight_Newbie` 的 Normal Bet 總 RTP 是 **93%**。同一份數學模型，兩種玩家 profile 的 RTP 不同，Overview 只呈現 Oldhand。

### 3.3 Free Spins Setting（`A35:C38`）

| 記分區 C1 數 | 免費次數 |
| --- | --- |
| 3 | 12 |
| 4 | 14 |
| 5 | 16 |

程式用的是公式而非查表：

```python
FG_TRIGGER_BASE_SPINS      = 12
FG_EXTRA_SPINS_PER_SCATTER = 2
free_spins = 12 + (scatter_count - 3) * 2   # scatter_count >= 3
FG_SPIN_CAP = 50                           # Overview!A39「maximum of free spins is 50」
```

> ⚠️ `Description` 工作表 B31 寫 `FG 次數 = 15 + (scatter_count - 3) * 2`（15/17/19），與 `Overview` 和程式常數（12/14/16）**不一致**。`Description` 是舊版殘留，以 `Overview` + 程式常數為準。

### 3.4 Pay Table（`A42:F62`）

賠率以 100 credit 下注為基準，數值直接乘 `bet_multi`。

| Symbol | Id | 3 | 4 | 5 | 程式定位 |
| --- | --- | --- | --- | --- | --- |
| WW | 0 | 0 | 0 | 0 | Wild：只替代、不自帶賠率 |
| C1 | 1 | 0 | 0 | 0 | Scatter：只算數量、會截斷連線 |
| M1 | 2 | 250 | 1250 | 5000 | 可計分 |
| M2 | 3 | 100 | 500 | 2000 | 可計分 |
| M3 | 4 | 75 | 250 | 1000 | 可計分 |
| M4 | 5 | 50 | 200 | 750 | 可計分 |
| M5 | 6 | 25 | 100 | 500 | 可計分 |
| A | 7 | 10 | 50 | 250 | 可計分 |
| K | 8 | 10 | 50 | 250 | 可計分 |
| Q | 9 | 10 | 50 | 250 | 可計分 |
| J | 10 | 10 | 50 | 250 | 可計分 |
| G1~GJ | 11~19 | （同基底） | | | **程式不讀**，判獎時已還原成 M1~J |

程式衍生出的三張旗標表：

| config 欄位 | 內容 | 用在哪 |
| --- | --- | --- |
| `base_symbol_of` | `G1→M1 … GJ→J`，其餘指向自己 | 停輪、補牌時把 strip 上的符號寫進盤面 |
| `is_gold_symbol` | `G1~GJ` 為 1 | 決定該格是否進入倍數分配 |
| `is_score_symbol` | `WW`、`C1`、`G*` 為 0，其餘為 1 | `get_pay()` 的前置檢查 |
| `symbols_score` | `[2..10]`（M1~J） | Wild 開頭的線要逐一試算哪個符號賠最多 |

---

## 4. `Parameter` 工作表

這是整份模型的核心控制面板。以下逐區塊說明，並標明程式在單局中「什麼時候」用它。

### 4.1 `Line`（`B4:G24`，20 列）→ `paylines`

每列 5 個數字 = 該線在 R1~R5 各取記分區第幾列（0=上、1=中、2=下）。

| ID | R1 | R2 | R3 | R4 | R5 |  | ID | R1 | R2 | R3 | R4 | R5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | 1 | 1 | 1 |  | 10 | 2 | 1 | 1 | 1 | 2 |
| 1 | 0 | 0 | 0 | 0 | 0 |  | 11 | 1 | 1 | 0 | 1 | 1 |
| 2 | 2 | 2 | 2 | 2 | 2 |  | 12 | 1 | 1 | 2 | 1 | 1 |
| 3 | 0 | 1 | 2 | 1 | 0 |  | 13 | 1 | 0 | 1 | 0 | 1 |
| 4 | 2 | 1 | 0 | 1 | 2 |  | 14 | 1 | 2 | 1 | 2 | 1 |
| 5 | 0 | 0 | 1 | 0 | 0 |  | 15 | 0 | 1 | 0 | 1 | 0 |
| 6 | 2 | 2 | 1 | 2 | 2 |  | 16 | 2 | 1 | 2 | 1 | 2 |
| 7 | 1 | 2 | 2 | 2 | 1 |  | 17 | 0 | 0 | 1 | 2 | 2 |
| 8 | 1 | 0 | 0 | 0 | 1 |  | 18 | 2 | 2 | 1 | 0 | 0 |
| 9 | 0 | 1 | 1 | 1 | 0 |  | 19 | 0 | 2 | 0 | 2 | 0 |

**判獎邏輯（`evaluate_board`）**

```
對每一條線 line：
    取 R1 上該線位置的符號 s1
    若 s1 == C1        → 這條線不算（Scatter 不參與連線）
    若 s1 == WW        → 對 symbols_score 裡每個符號各試算一次，取賠率最高者
    否則               → 以 s1 的基底符號為目標
    從 R1 往右數，符號的基底 == 目標 或 該格是 WW → 連線長度 +1；否則中斷
    遇到 C1 立即中斷
    連線長度 >= 3 才有賠率：pay = pay_table[目標符號][長度-3] * bet_multi
    每條線只取最高的一種算法，不重複計分
```

要點：
- 一定要從 **R1** 起算（左起）。
- 金框在判獎階段已經是基底符號，所以 `GA` 和 `A` 對判線完全等價。
- 每條線只給一個獎，20 條線的獎相加。

### 4.2 `Table Selection Weight - Base Game`（`I4:J7`）→ `weight_table_bg`

| 工作表 | Weight | 佔比 |
| --- | --- | --- |
| `BG_Symbol` (B1) | 7000 | 70% |
| `BG_Symbol (2)` (B2) | 1000 | 10% |
| `BG_Symbol (3)` (B3) | 2000 | 20% |
| 合計 | 10000 | |

**每一次 BG spin 的第一個動作**就是用這組權重抽 `table_id`。這一步決定了本局後面所有的輪帶、補牌、倍數權重都走哪一欄。

三張表的角色（由各表的實際數值反推，可自行驗證）：

| 表 | 設計意圖 | 關鍵特徵 |
| --- | --- | --- |
| B1 | 一般局 | 金框只出現在 R2/R3/R4；C1 只在 R2、R4 → **記分區最多 2 個 Scatter，不可能觸發 FG** |
| B2 | 金框局 | **R3 輪帶 100% 是金框**；C1 同樣只在 R2、R4 → **也不可能觸發 FG** |
| B3 | 觸發 FG 局 | C1 分布在全部 5 輪（最多 5 個）；所有倍數權重都是 `0 → 10000`，即**金框一律 ×0**，避免進 FG 前吃到大倍數 |

> 這推出一個關鍵結論：**Normal Bet 只有抽到 B3 才可能進 FG**。所以 FG 觸發率 = P(抽到 B3) × P(B3 開出 3+ Scatter)，而卡片系統會再對這個結果做重抽校正（§6）。

`FG_Symbol` / `BF_Symbol` 在 `I12` 起、`I19` 起也有 table weight 區塊，但**轉檔沒有輸出、程式不使用**：FG 的 table 是用累積倍率硬切（§7.1），BF 固定用 table 6。

### 4.3 `Multiplier Range`（`I25:I38`）→ `value_multiplier_range`

13 個倍數值，**這是索引表**，下面所有 multiplier weight 區塊的欄位順序都對應它：

```
索引  0   1   2   3   4   5    6    7    8    9    10   11   12
值    0   2   3   5   8   10   15   20   25   50   100  500  1000
```

抽倍數的流程固定是：用某一組權重抽出「索引」→ 再用 `value_multiplier_range[索引]` 換成倍數值。**索引 0 的值是 0，代表「這顆金框沒有倍數」**（框還在，但收集不到倍率）。

### 4.4 `Used Special Pool Weight`（`AC4:AL11`）→ `weight_special_pool`

- 分母固定 **10000**（`special_pool_weight_base`）。
- 欄位 `1~9` = **記分區內的金框數量**。
- 每一列 = 一張 table。

Normal Bet 相關數值：

| Table | 1 顆 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | 300 | 600 | 1080 | 1440 | 2250 | 2700 | 3150 | 3600 | 4050 |
| B2 | 0 | 0 | 525 | 700 | 1750 | 2100 | 3675 | 4200 | 4725 |
| B3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| F1 / F2 / F3 | 0 | 0 | 450 | 500 | 1400 | 1800 | 3200 | 4000 | 4200 |

**使用邏輯（`assign_initial_multiplier`）**

```python
n = 記分區(row 1~3)的金框數量
if n > 0:
    row = min(n, 9) - 1                       # 查表列
    w   = weight_special_pool[row][table_id]
    if w > 0 and randint(0, 10000) < w:       # 命中特殊池
        special_idx = randint(0, n)           # 在 n 顆記分區金框中「等機率」挑 1 顆
```

要點：
- 特殊池**只在開局分配倍數時判定一次**，Cascade 補進來的金框不會再有特殊池。
- 一局最多**只有 1 顆**金框吃到特殊池倍數。
- 只有記分區的金框有資格；預覽列的金框不算入 `n`，也不會被選中。
- B3 全 0 → 觸發 FG 那張表永遠不會出特殊池。

### 4.5 五組 `Multiple Selection Weight`（`N3:AA55`）

五個區塊，欄位皆為 O~AA（對應 §4.3 的 13 個倍數），列皆為 7 張 table。分母都是 10000。

| xlsx 區塊 | config 欄位 | 何時使用 |
| --- | --- | --- |
| `Multiple Selection Weight - Special Pool`（列 5~11） | `weight_cum_multiple_special` | 開局命中特殊池的那 1 顆金框 |
| `Multiple Selection Weight - Reel3 Before Eliminate`（列 16~22） | `weight_cum_multiple_r3_before` | 開局、**R3**、**記分區**的金框（限特定 table） |
| `Multiple Selection Weight - Reel3 After Eliminate`（列 27~33） | `weight_cum_multiple_r3_after` | 開局的 R3 預覽列金框 + Cascade 補進 R3 的金框（限特定 table） |
| `Multiple Selection Weight - Before Eliminate`（列 38~44） | `weight_cum_multiple_before` | 開局、非 R3、記分區的金框 |
| `Multiple Selection Weight - After Eliminate`（列 49~55） | `weight_cum_multiple_after` | 開局的非 R3 預覽列金框 + Cascade 補進的非 R3 金框 |

**「R3 專用表」的啟用條件**（`uses_reel3_multiplier_table`）：

```python
REEL3_SPECIAL_TABLE_IDS = [1, 3, 4, 5]      # 即 B2, F1, F2, F3
用 R3 專用權重  ⟺  col == 2 且 table_id ∈ {1, 3, 4, 5}
```

也就是 **B1（table 0）和 B3（table 2）的第 3 輪並不走 R3 專用表**，仍走一般的 Before/After。這一點常被誤解。

**完整的倍數選擇決策樹**

```python
# 開局：對盤面上「所有」金框（含預覽列）逐格分配
def pick_initial_multiplier_by_pos(table_id, row, col):
    if col == 2 and table_id in (1, 3, 4, 5):
        return R3_BEFORE if row >= 1 else R3_AFTER     # row 0 = 預覽列 → AFTER
    return BEFORE      if row >= 1 else AFTER          # row 0 = 預覽列 → AFTER

# Cascade 補牌：新補進來的金框
def pick_drop_multiplier_by_col(table_id, col):
    if col == 2 and table_id in (1, 3, 4, 5):
        return R3_AFTER
    return AFTER
```

> ⚠️ 預覽列（row 0）雖然是「開局」產生的，但因為 `is_scoring_row(0) == False`，它吃的是 **After Eliminate**。設計上合理（它要等掉下來才會參與判獎），但看表時很容易看錯。

**Normal Bet 會用到的實際權重值**

`Before Eliminate`（B1 / B2 / B3 三張表數值相同）：

| 倍數 | 0 | 2 | 3 | 5 | 8 |
| --- | --- | --- | --- | --- | --- |
| Weight | 8500 | 500 | 400 | 300 | 300 |

→ 85% 的開局記分區金框是 ×0（有框無倍數），有倍數的平均 4.07 倍。

`After Eliminate`：

| Table | 0 | 2 | 3 | 5 | 8 | 10 | 15 | 20 | 25 | 50 | 100 | 500 | 1000 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B1 / B2 | 8400 | 500 | 400 | 300 | 300 | 20 | 20 | 5 | 5 | 5 | 20 | 5 | 20 |
| B3 | 8500 | 500 | 400 | 300 | 300 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

→ B1/B2 的掉落金框帶有長尾（含 ×1000，權重 20/10000），有倍數者平均 19.73 倍；B3 沒有長尾。

`Reel3 Before / After Eliminate`（只有 B2 會用到）：

| 區塊 | 0 | 2 | 3 | 5 | 8 | 10 | 15 | 20 | 25 | 50 | 100 | 500 | 1000 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B2 R3 Before | 0 | 3600 | 3400 | 1500 | 1500 | — | — | — | — | — | — | — | — |
| B2 R3 After | 0 | 3500 | 3400 | 1500 | 1500 | 20 | 20 | 5 | 5 | 5 | 20 | 5 | 20 |
| B1 / B3 R3 | 10000 | — | — | — | — | — | — | — | — | — | — | — | — |

→ B2 的 R3 是「整輪金框且**保證有倍數**」（權重 0 的欄位是 0），所以 B2 是這個模型製造連續倍數的主力。

`Special Pool`：

| Table | 10 | 15 | 20 | 25 | 50 | 100 | 500 | 1000 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B1 / B2 | 2680 | 3000 | 2000 | 500 | 100 | 1200 | 20 | 500 |
| B3 | （0 → 10000，即不出倍數） | | | | | | | |
| F1 | 3855 | 3000 | 1500 | 150 | 25 | 800 | 70 | 600 |
| F2 | 4385 | 3000 | 1500 | 150 | 25 | 500 | 40 | 400 |
| F3 | 5145 | 3000 | 1500 | 150 | 25 | 100 | 10 | 70 |

→ 特殊池**最小值是 10 倍**，且 B1/B2 有 5% 機率直接給 ×1000。這是單局大獎的主要來源。

**`AB` 欄的意義**：`AB` 是「排除 ×0 之後的平均倍率」（`Σ(權重×倍數) ÷ Σ(倍數>0 的權重)`）。程式不讀這一欄，且是**手動填入的常數（沒有公式連動）**。目前 BG 各列都對得上，但下列 FG 列已與現行權重脫節，看表時請以權重反算為準：

| 位置 | AB 欄填的值 | 依現行權重實算 |
| --- | --- | --- |
| Special Pool / F1、F2、F3 | 126.225 / 93.43 / 36.98 | 83.36 / 59.39 / 21.65 |
| R3 Before / F1、F2、F3 | 2.73 | 2.57 |
| R3 After / F1、F2、F3 | 10.7375 / 6.3535 / 5.2575 | 2.582 |
| After / F1、F2、F3 | 25.76 / 13.32 / 10.11 | 2.517 |

### 4.6 `Eliminate Table Weight`（`I41:K44`）→ `eliminate_table_weight_*`

| 場景 | A | B |
| --- | --- | --- |
| Base Game | 10 | 0 |
| Free Game | 10 | 0 |

**使用邏輯（`choose_eliminate_table`）**：每次 spin 開局抽一次，決定**本局整個 Cascade 過程**要用 `Eliminate Wheel Weight A` 還是 `B` 來補牌，中途不會換。

目前設定 A=10、B=0 → **100% 使用 A 表**，B 表形同備用。`BF` 的權重是直接複製 Free Game 的那一列（轉檔行為，xlsx 沒有獨立的 BF 列）。

---

## 5. `BG_Symbol` / `BG_Symbol (2)` / `BG_Symbol (3)` / `FG_Symbol*` 工作表

七張表版面完全相同。每一張表定義「一組輪帶 + 一組補牌轉盤」。

### 5.1 版面對照

| xlsx 欄位 | 列範圍 | config 欄位 | 程式讀取 |
| --- | --- | --- | --- |
| `A3:H23` Symbol / Description / R1~R5 / ID | 4~23 | — | ❌ 檢核用（= 該表輪帶上各符號的**張數統計**，每輪合計 200，見 `C24:G24`） |
| `C26:G27` Normal / Golden Symbol 佔比 | 26~27 | — | ❌ 檢核用 |
| `B30:G38` 合併統計（基底+金框） | 30~38 | — | ❌ 檢核用（例：B1 的 R2 `M1=38` = 一般 M1 22 + 金框 G1 16） |
| `J:O` **Symbol**（文字） | 4~203 | — | ❌ 給人讀的輪帶 |
| `Q:U` **Symbol ID R1~R5** | 4~203 | `arr_reels` | ✅ 實際輪帶 |
| `W:AA` **Symbol Weight R1~R5** | 4~203 | `arr_reels_weight` → `arr_reels_weight_cum` | ✅ 停輪權重 |
| `AC:AH` **Eliminate Wheel Weight A** | 30~49 | `drop_weight_a` → `drop_weight_a_cum` | ✅ 補牌權重 A |
| `AJ:AO` **Eliminate Wheel Weight B** | 30~49 | `drop_weight_b` → `drop_weight_b_cum` | ✅ 補牌權重 B |

輪帶長度：七張表都是 **200 格**（`reels_len` 全為 200）。

### 5.2 停輪邏輯（`generate_board`）

```python
for col in 0..4:
    L         = reels_len[table_id][col]                      # 200
    stop_idx  = pick_by_cum(arr_reels_weight_cum[table_id][:L][col])   # 依權重抽停輪位置
    for row in 0..3:
        symbol           = arr_reels[table_id][(stop_idx + row) % L][col]
        board[row][col]  = base_symbol_of[symbol]             # 只存基底符號
        gold_mask[row][col] = is_gold_symbol[symbol]
```

**關鍵：`Symbol Weight` 不是「符號權重」，是「停輪位置權重」。** 每一格輪帶位置有自己的權重（本模型多為 1 或 2），抽中哪一格就從那一格往下取 4 格。所以同一個符號在輪帶上出現幾次、每次的位置權重多少，一起決定它的實際出現率。

各表停輪權重總和（= 該輪的分母，注意不是 200）：

| 表 | R1 | R2 | R3 | R4 | R5 |
| --- | --- | --- | --- | --- | --- |
| B1 | 225 | 285 | 238 | 318 | 289 |
| B2 | 540 | 480 | 556 | 200 | 200 |
| B3 | 236 | 236 | 236 | 254 | 254 |
| F1 | 562 | 536 | 560 | 368 | 365 |
| F2 | 562 | 536 | 556 | 432 | 435 |
| F3 | 562 | 536 | 552 | 264 | 270 |

由此算出的實際出現率（記分區 + 預覽列，開局盤面）：

| 表 | 金框出現率 R1 / R2 / R3 / R4 / R5 | C1 出現率 R1 / R2 / R3 / R4 / R5 |
| --- | --- | --- |
| B1 | 0 / 0.404 / 0.059 / 0.157 / 0 | 0 / 0.039 / 0 / 0.044 / 0 |
| B2 | 0 / 0.408 / **1.000** / 0.175 / 0 | 0 / 0.021 / 0 / 0.045 / 0 |
| B3 | 0 / 0.390 / 0.051 / 0.142 / 0 | 0.076 / 0.076 / 0.076 / 0.106 / 0.106 |
| F1 | 0 / 0.235 / **1.000** / 0.236 / 0 | 0.011 / 0.009 / 0 / 0.014 / 0.014 |
| F2 | 0 / 0.201 / **1.000** / 0.238 / 0 | 0.011 / 0.009 / 0 / 0.016 / 0.016 |
| F3 | 0 / 0.183 / **1.000** / 0.269 / 0 | 0.011 / 0.009 / 0 / 0.019 / 0.019 |

由此可直接看出：
- **金框永遠不會出現在 R1 和 R5**（所有表皆如此）。
- **`WW` 從來不會自然停出**（所有表的 `WW` 張數與補牌權重都是 0）。盤面上的 Wild 只有一個來源：中獎的金框轉成 Wild（§7.2 步驟 5）。
- FG 三張表的 R3 都是 100% 金框，且 R3 沒有 C1 → **FG 內最多只能開出 4 個 Scatter**，所以 FG 內 retrigger 只可能加 12 或 14 場，不會加 16 場。

### 5.3 補牌邏輯（`pick_drop_symbol`）

`Eliminate Wheel Weight A/B` 是一張 **20 列（符號）× 5 欄（輪）** 的權重表，和輪帶完全獨立。

```python
def pick_drop_symbol(table_id, use_drop_a, col, column_has_c1):
    while True:
        idx    = pick_by_cum((drop_weight_a_cum if use_drop_a else drop_weight_b_cum)[table_id][:, col])
        symbol = symbol_id[idx]
        if column_has_c1 and base_symbol_of[symbol] == C1:
            continue                        # 該欄已有 Scatter → 重抽
        return symbol
```

**要點：補牌不是「從輪帶往上繼續取」，而是用這張獨立的權重表重抽。** （程式裡雖有 `take_reel_above_symbol()` 這個「往輪帶上方取」的函式，但目前流程完全沒有呼叫它。）

同一欄禁止補出第二個 Scatter：`ALLOW_C1_DROP_WHEN_BOARD_HAS_C1 = False`，判斷範圍含預覽列。

本檔案的三個實作細節：

1. 每張表的 `AC/AJ` 區其實有 **三個區塊**：`1 Combo`（列 6~25）、`2 Combo`（列 30~49）、`3+ Combo`（列 54~73），設計上可讓不同連消次數用不同補牌率。
   **但 `xlsx_to_config.py` 只讀列 30~49，也就是 `2 Combo` 區塊。** 目前三個區塊的數值完全相同，所以結果沒有差異；一旦只改 `1 Combo` 或 `3+ Combo`，**改動不會生效**。
2. `A` 表與 `B` 表目前數值也完全相同，再加上 `Eliminate Table Weight` 是 A=10/B=0，所以實際只有一組補牌權重在跑。
3. 補牌權重與輪帶張數的關係（B1 為例）：一般符號的權重 = 輪帶張數（完全相同），金框的權重 = 輪帶張數 **×3**。

格式為「一般符號合計（輪帶張數 → 補牌權重）／金框合計（輪帶張數 → 補牌權重）」：

| 表 | R2 | R3 | R4 |
| --- | --- | --- | --- |
| B1 | 120 → 120 ／ 80 → 240（×3） | 188 → 188 ／ 12 → 36（×3） | 168 → 168 ／ 32 → 96（×3） |
| B2 | 120 → 140 ／ 80 → 103 | 0 → 0 ／ 200 → 298 | 165 → 165 ／ 35 → 65 |
| B3 | 120 → 120 ／ 80 → 118 | 188 → 182（C1 由 6 降為 0）／ 12 → 16 | 168 → 168 ／ 32 → 46 |

> B3 的補牌表把 **R1 / R3 / R5 的 C1 權重設為 0**（輪帶上有，補牌時沒有）。所以 B3 局的 Scatter 主要來自開局盤面，Cascade 只能在 R2/R4 再補出 Scatter。

---

## 6. `Multiplier_Weight` 工作表 → 卡片系統（Card System）

這是 Normal Bet 最容易被忽略、但對結果影響最大的一組參數。它**不改變盤面機率，而是對「整局結果」做接受／重抽（rejection sampling）**，把自然機率重塑成目標分布。

### 6.1 版面與對應

| 欄 | 標題（第 2/3 列） | config 路徑 | Normal Bet 是否使用 |
| --- | --- | --- | --- |
| B | `Range` | 卡片的區間標籤 | — |
| C | Newbie / `Weight_NB_BG` | `card_system.newbie.normal_bet.weight_bg` | ✅（Newbie） |
| D | Newbie / `Weight_NB_FG` | `card_system.newbie.normal_bet.weight_fg` | ✅（Newbie） |
| E | Newbie / `Weight_EB_BG` | `…newbie.extra_bet.weight_bg` | ❌ Extra Bet |
| F | Newbie / `Weight_EB_FG` | `…newbie.extra_bet.weight_fg` | ❌ Extra Bet |
| G | Oldhand / `Weight_NB_BG` | `card_system.oldhand.normal_bet.weight_bg` | ✅（Oldhand） |
| H | Oldhand / `Weight_NB_FG` | `card_system.oldhand.normal_bet.weight_fg` | ✅（Oldhand） |
| I | Oldhand / `Weight_EB_BG` | `…oldhand.extra_bet.weight_bg` | ❌ Extra Bet |
| J | Oldhand / `Weight_EB_FG` | `…oldhand.extra_bet.weight_fg` | ❌ Extra Bet |
| K | Oldhand / `Weight_BF_FG` | `…oldhand.buy_feature.weight_fg` | ❌ Buy Feature |

列的部分：

- `B4:B67` 是 `(-1, 0]`、`(0, 1]`、…、`(100000, 9999999]` 這種**得分倍率區間**（得分 ÷ coin_in），轉成 `type: "range"` 的卡，帶 `min` / `max`。
- `B68` = `Free Game`，轉成 `type: "free_game"` 的卡（不看金額，只看「這局有沒有觸發 FG」）。

每一欄的權重總和都被校準到約 **1,000,000,000**（`Multiplier_Weight_Newbie!B2` 的 Threshold = 1e9），所以權重值可以直接讀成「十億分之幾」的機率。

Normal Bet 的四欄摘要：

| 欄 | 用途 | 總權重 | `Free Game` 卡 | 換算 FG 觸發率 | 有效 `range` 卡數 | 區間範圍 |
| --- | --- | --- | --- | --- | --- | --- |
| C | Newbie BG | 1,000,040,817 | 4,195,668 | 0.0041955（1/238.35） | 15 | `(-1, 0]` ~ `(25, 30]` |
| D | Newbie FG | 999,999,995 | 無 | — | 9 | `(30, 35]` ~ `(90, 100]` |
| G | Oldhand BG | 1,000,011,437 | 4,195,668 | 0.0041956（1/238.34） | 23 | `(-1, 0]` ~ `(100, 120]` |
| H | Oldhand FG | 999,999,979 | 無 | — | 39 | `(10, 15]` ~ `(10000, 20000]` |

差異解讀：
- **BG 端**：Newbie 只鋪到 `(25, 30]`，Oldhand 鋪到 `(100, 120]` — 新手的單局 BG 得分被壓在較窄範圍。
- **FG 端**：Newbie 只鋪 `(30, 100]` 共 9 個區間，Oldhand 鋪 `(10, 20000]` 共 39 個區間 — 老手保留了 FG 的長尾大獎，新手則被限制在「穩定拿 30~100 倍」。
- 兩者的 `Free Game` 卡權重完全相同 → **FG 觸發率一致（1/238）**，差別只在觸發後的**金額分布**（也因此 Newbie 總 RTP 93% vs Oldhand 92%）。
- FG profile 沒有 `Free Game` 卡（權重 0），因為進到 FG 判定時「已觸發 FG」是既定事實，只需比對金額區間。

### 6.2 Normal Bet 的判定流程（`simulator_chunk`）

```python
retry_limit = 5000          # config.card_system.retry_limit
profile     = newbie.normal_bet if 是新手 else oldhand.normal_bet

# ── 每一局開始：先抽一張 BG 卡 ──
card = pick_by_weight(profile.weight_bg)

if card.type == "free_game":
    # 情況 A：這局「一定要」觸發 FG
    重複跑 BG spin，直到最終盤面 Scatter >= 3（或達 retry_limit）
    再抽一張 FG 卡 = pick_by_weight(profile.weight_fg)
    重複跑「整段 FG」，直到 pay_fg / coin_in ∈ (card_fg.min, card_fg.max]（或達 retry_limit）

else:
    # 情況 B：這局「不可以」觸發 FG，且 BG 得分必須落在指定區間
    while True:
        跑一次 BG spin
        if Scatter >= 3:                       # 觸發了 FG → 直接不接受
            重抽
        elif not (min < pay_bg / coin_in <= max):
            重抽
        else:
            接受
        超過 retry_limit 就放棄並記錄

pay_total = pay_bg + pay_fg                    # 一次付費 spin 的完整結果
```

要點：
- **卡片系統決定的是「這一局要長成什麼樣」，然後用重抽去湊出來。**
- 判定用的是 `pay / coin_in`（含小數的倍率），區間是**左開右閉** `(min, max]`。
- `range` 卡一旦觸發 FG 就整局作廢重抽 → 保證 FG 觸發率完全由 `Free Game` 卡的權重決定，與盤面自然機率無關。
- `Extra Bet` / `Buy Feature` 在比對區間時，分母會換成 Normal Bet 的 coin_in（`calc_card_system_coin_in`），Normal Bet 則就是自己的 coin_in。
- `retry_limit = 5000`；達上限時模擬器會記錄 `RETRY_LIMIT_EXCEEDED` 等計數，方便檢查某張卡是否根本抽不出來。

### 6.3 `Multiplier_Weight_Newbie` / `Multiplier_Weight_Oldhand`

這兩張表是**產生上面那些權重的推導工作表，程式完全不讀**。版面（以 Newbie 為例）：

| 區塊 | 內容 |
| --- | --- |
| `B2` Threshold | 1e9，權重的正規化基數 |
| `B3` Coin in | 100 |
| `B6:J8` | 各下注模式的目標 RTP / Hit Rate / FG Period / Avg Multi（`Overview` 的 RTP 就是引用這裡） |
| `A15:N…` | `Lower`/`Upper`（區間）、`Cnt`/`Pay`/`Hit Rate`/`Avg. Multi.`（**自然機率**模擬結果）、`Fix Num`（人工調整係數）、`Fix Rate`／`Final Rate`／`Weight`（校準後、寫回 `Multiplier_Weight` 的值）、`Simulator RTP` |
| `P:S` | 目前值 / 競品值 / 差異，調整時的對照 |

調參的實際迴路是：先用 `card_system_enabled = False` 跑自然機率 → 填進 `Cnt`/`Pay` → 調 `Fix Num` → 算出 `Weight` → 貼到 `Multiplier_Weight` → 重新轉檔 → 開卡片系統再跑驗證。

---

## 7. 一局 Normal Bet 的完整參數消耗順序

### 7.1 場景與 table 的選擇

| 場景 | 如何決定 table | 用到的參數 |
| --- | --- | --- |
| BG | 依權重抽 | `weight_table_bg`（B1 70% / B2 10% / B3 20%） |
| FG | **不抽**，依「當前累積倍率和」硬切 | 累積倍率 < 10 → F1；< 20 → F2；≥ 20 → F3 |

FG 的切換是程式常數（`choose_table`），不是 xlsx 參數。`config.fg_table_rule` 雖然記錄了這組門檻，但 runtime 並沒有讀它。

### 7.2 單次 spin（`run_spin`），BG 與 FG 共用同一套流程

```
 1. table_id  = 依場景決定（§7.1）                        ← weight_table_bg
 2. use_drop_a = 抽 A/B 補牌表（本局固定）                 ← eliminate_table_weight
 3. 停輪產生 4×5 盤面                                     ← arr_reels_weight_cum, arr_reels
    → 盤面存基底符號，另外記 gold_mask
 4. 開局金框分配倍數（含預覽列，逐格）                      ← weight_special_pool
    a. 先算記分區金框數 n，判定是否命中特殊池，命中則隨機挑 1 顆
    b. 被挑中的那顆     → Special Pool 權重              ← weight_cum_multiple_special
    c. 其餘金框：
         R3 且 table ∈ {B2,F1,F2,F3}：
              記分區 → R3 Before                        ← weight_cum_multiple_r3_before
              預覽列 → R3 After                         ← weight_cum_multiple_r3_after
         其他：
              記分區 → Before                           ← weight_cum_multiple_before
              預覽列 → After                            ← weight_cum_multiple_after
 5. 連消迴圈（combo = 0, 1, 2 …）:
    5.1 判 20 條線                                        ← paylines, pay_table, symbols_score
    5.2 沒有任何獎 → 跳出迴圈
    5.3 raw_pay += 本輪 line win 總和
    5.4 對每個中獎位置：
          是金框 → multiplier_sum += 該格倍數
                   該格「不消失」，改標記為「轉 Wild」
          非金框 → 清空
    5.5 該欄現有符號往下墜，空位補新符號                    ← drop_weight_a_cum / b_cum
          若補進金框 → 依 R3 判定取 R3 After 或 After 抽倍數
          該欄已有 C1 時，補到 C1 會重抽
    5.6 combo += 1，回 5.1
 6. scatter_count = 最終盤面「記分區」的 C1 數量
 7. final_multiplier = multiplier_sum  （若本次 spin 有實際吃到 >0 的倍數）
                     = 1              （否則）
 8. final_pay = raw_pay * final_multiplier
```

### 7.3 一局（一次付費 spin）的外層流程

```
1. coin_in = bet_multi * 100 * 1
2. 抽 BG 卡（§6.2）
3. 跑 BG spin → pay_bg, scatter_count
4. scatter_count >= 3：
     free_spins = 12 + (scatter_count - 3) * 2      # 12 / 14 / 16
     進 FG：
       fg_multiplier_sum = 0
       remaining = min(free_spins, 50)
       while remaining > 0:
           依 fg_multiplier_sum 選 F1/F2/F3
           跑一次 spin（流程同 §7.2，multiplier_sum 從 fg_multiplier_sum 起算）
           pay_fg += 本場得分
           fg_multiplier_sum = 本場結束後的累積值        # 跨場保留
           remaining -= 1
           若本場記分區 C1 >= 3：
               remaining = min(remaining + 12 + (C1-3)*2, 50)   # retrigger
5. pay_total = pay_bg + pay_fg
6. 依卡片條件決定接受或整局重抽（§6.2）
```

---

## 8. 最容易誤解的 10 個點

1. **倍數不是即時乘的。** 單次 spin 內先把倍數加總，等到不能再連消了才一次乘上該 spin 的 `raw_pay`。
2. **金框要「中獎」才收得到倍數。** 金框先當基底符號參與判線；只有它真的被打中，才把倍數加進 `multiplier_sum`，並在原位轉成 Wild 留在盤面（不消失、不掉落）。
3. **FG 的累積倍率不是每場都會生效。** `final_multiplier` 只有在「本場有吃到 >0 的倍數」時才等於累積值，否則是 1。所以某場中獎但沒消到金框，那場就只拿原始得分。
4. **FG 累積倍率跨場保留，且會反過來決定下一場用哪張表**（<10→F1、<20→F2、≥20→F3）。retrigger 只加場數，不清空累積值。
5. **Scatter 只看整局 Cascade 結束後的最終盤面**，中途出現不算，預覽列不算。
6. **B1 和 B2 永遠不可能觸發 FG**（C1 只分布在 R2/R4，記分區最多 2 個）。Normal Bet 的 FG 只能從 B3 來，而觸發率最終由卡片系統的 `Free Game` 卡權重鎖定。
7. **預覽列（row 0）的金框吃 After Eliminate，不是 Before。**
8. **只有 B2 / F1 / F2 / F3 的第 3 輪走 R3 專用倍數表**；B1、B3 的第 3 輪走一般的 Before/After。
9. **改 raw weight 之後一定要重新轉檔。** runtime 只吃 `*_cum`；`Simulator.py` 的 `CONFIG_FILE` 也要確認指到對的那份 `config_*.js`。
10. **補牌權重只有「2 Combo」那一塊會生效**（列 30~49）。改 `1 Combo` / `3+ Combo` 不會有任何效果。

---

## 9. 參數 → 結果的影響對照（調參用）

| 想調的目標 | 主要參數 | 次要參數 |
| --- | --- | --- |
| 總 RTP | `Multiplier_Weight` 的 `Weight_NB_BG` / `Weight_NB_FG`（卡片系統直接定義結果分布） | `pay_table` |
| BG / FG 的 RTP 分配 | `Multiplier_Weight` 兩欄的權重配置 | `weight_table_bg` 中 B3 的比重 |
| FG 觸發率與週期 | `Multiplier_Weight!G68`（`Free Game` 卡權重） | B3 的 C1 分布、`weight_table_bg` 的 B3 權重 |
| 連線中獎率 | 各表 `Symbol ID` + `Symbol Weight`（輪帶組成） | `paylines` |
| 大獎（單局高倍）機率 | `Used Special Pool Weight` + `Multiple Selection Weight - Special Pool` | `After Eliminate` 的長尾（×500 / ×1000） |
| 金框出現頻率 | 各表輪帶的金框張數與位置權重 | `Eliminate Wheel Weight` 的金框權重（B1 為輪帶張數 ×3） |
| 連消長度 | `Eliminate Wheel Weight`（補牌組成） | 輪帶組成 |
| FG 節奏（倍率成長速度） | `Multiple Selection Weight - Reel3 Before/After`（F1/F2/F3） | F1/F2/F3 的 R3 金框率、`Special Pool` 權重 |
| 新手 / 老手體驗差異 | `Multiplier_Weight` C/D 欄 vs G/H 欄 | — |

---

## 10. 版本與一致性檢查清單

| 項目 | 目前狀態 | 建議 |
| --- | --- | --- |
| `Overview!B3` 版本 | 4.0.0.8 | — |
| `config_92A.js` 的 `excel_version` | **4.0.0.6** | xlsx 已更新但 config 未重新產生，送驗前務必重跑 `xlsx_to_config.py` 並確認版本一致 |
| FG 場數公式 | `Overview` + 程式 = 12/14/16；`Description!B31` = 15/17/19 | `Description` 為舊版殘留，應更新或刪除 |
| `AB` 欄平均倍率 | BG 各列正確；FG 的 Special Pool / R3 Before / R3 After / After 四處與現行權重不符 | 手動欄位，重算後更新 |
| `Eliminate Wheel Weight` 三個 Combo 區塊 | 數值相同，但只有 `2 Combo` 會被讀取 | 若不打算分 Combo，建議移除多餘區塊避免誤改 |
| `Eliminate Wheel Weight A` vs `B` | 數值相同，且權重 A=10 / B=0 | 若無雙表需求可簡化 |
| `Parameter!I12` / `I19` 的 FG / BF table weight | 有填值但轉檔不輸出、程式不使用 | 標註為未使用或移除 |
| `Overview` 的 `G1~GJ` 賠率列 | 有填值但程式不讀 | 保留作對照即可，須確認與基底符號一致（目前一致） |
| `OP Jackpot` 工作表 | Threshold 1e10 與各次模擬的 spin / C1 / SCR 統計；程式不讀 | 驗證紀錄用 |

---

## 附錄 A. xlsx → config 欄位對照速查

| xlsx 位置 | config 欄位 | 轉換 |
| --- | --- | --- |
| `Overview!B2` | `game_id` | 直接 |
| `Overview!B3` | `excel_version` | 直接 |
| `Overview!A7` | `default_coin_in` | 直接 |
| `Overview!B11` | `normalbet` | 直接 |
| `Overview!B31` | `window_size` | 直接（程式再 +1 得顯示列數） |
| `Overview!A43:E62` | `pay_table` | 3/4/5 連賠率 |
| `Overview!F43:F62` | `symbol_id` | 直接 |
| `Overview!A43:A62` | `symbol_str` / `base_symbol_of` / `is_gold_symbol` / `is_score_symbol` / `symbols_score` | 由 symbol code 衍生 |
| `Parameter!C5:G24` | `paylines` | 直接 |
| `Parameter!J5:J7` | `weight_table_bg` → `weight_cum_table_bg` | 累加 |
| `Parameter!I26:I38` | `value_multiplier_range` | 直接 |
| `Parameter!O5:AA11` | `weight_multiple_special` → `weight_cum_multiple_special` | 轉置 + 累加 |
| `Parameter!O16:AA22` | `weight_multiple_r3_before` → `_cum` | 轉置 + 累加 |
| `Parameter!O27:AA33` | `weight_multiple_r3_after` → `_cum` | 轉置 + 累加 |
| `Parameter!O38:AA44` | `weight_multiple_before` → `_cum` | 轉置 + 累加 |
| `Parameter!O49:AA55` | `weight_multiple_after` → `_cum` | 轉置 + 累加 |
| `Parameter!AD5:AL11` | `weight_special_pool` | 轉置（不累加，用 `randint(0,10000) < w` 判定） |
| `Parameter!J43:K44` | `eliminate_table_weight_bg` / `_fg`（`_bf` 複製 `_fg`） | 累加 |
| `*_Symbol!Q4:U203` | `arr_reels` | 直接 |
| `*_Symbol!W4:AA203` | `arr_reels_weight` → `arr_reels_weight_cum` | 逐輪累加 |
| `*_Symbol!AD30:AH49` | `drop_weight_a` → `drop_weight_a_cum` | 逐輪累加（**只讀 2 Combo 區塊**） |
| `*_Symbol!AK30:AO49` | `drop_weight_b` → `drop_weight_b_cum` | 同上 |
| `*_Symbol` 輪帶列數 | `reels_len` | 全為 200 |
| `Multiplier_Weight!B4:B68` + C/D 或 G/H 欄 | `card_system.{newbie,oldhand}.normal_bet.{weight_bg,weight_fg}` | 區間標籤解析成 `min`/`max`；`Free Game` 列轉成 `type:"free_game"` |

## 附錄 B. 程式常數（不在 xlsx 內，改動須改程式）

| 常數 | 值 | 位置 | 說明 |
| --- | --- | --- | --- |
| `FG_TRIGGER_BASE_SPINS` | 12 | `Simulator.py` | 3 Scatter 的基礎場數 |
| `FG_EXTRA_SPINS_PER_SCATTER` | 2 | `Simulator.py` | 每多 1 個 Scatter 加的場數 |
| `FG_SPIN_CAP` | 50 | `Simulator.py` | FG 總場數上限（含 retrigger） |
| `REEL3_SPECIAL_TABLE_IDS` | `[1,3,4,5]` | `Simulator.py` | 哪些 table 的 R3 用專用倍數表 |
| `ALLOW_C1_DROP_WHEN_BOARD_HAS_C1` | `False` | `Simulator.py` | 同欄禁止補出第二個 Scatter |
| FG table 門檻 | `<10 / <20 / ≥20` | `choose_table()` | FG 依累積倍率切表 |
| `special_pool_weight_base` | 10000 | `config` 靜態值 | 特殊池分母 |
| `MAX_WIN_MULTIPLIER` | 5000 | `Simulator.py` | **僅供統計**「達 5000× 的次數」，不是封頂機制 |
| `CARD_RETRY_LIMIT` | 5000 | `config.card_system.retry_limit` | 卡片重抽上限 |
