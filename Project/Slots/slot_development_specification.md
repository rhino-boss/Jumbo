# Slot Game 模型開發注意事項

本文件整理 Slot Game 數學模型從設計、實作、驗證到交付時必須注意的事項。重點是確保數學文件、Card System、模擬程式、Demogame 與 Config 使用同一套規則與參數，避免各端各自解讀或寫死例外。

適用範圍：`Project/Slots/H0xx_遊戲名稱/` 下的新遊戲模型、既有模型改版，以及 RTP、Card System 或 Feature 參數調整。

## 目錄

- [1. 數學文件 Math Document](#1-數學文件-math-document)
- [2. 卡片系統 Card System](#2-卡片系統-card-system)
- [3. 模擬程式 Simulator](#3-模擬程式-simulator)
- [4. Demogame](#4-demogame)
- [5. Config](#5-config)

**共通原則**

```text
數學文件／XLSX
      ↓ 轉檔與驗證
    Config
     ├─→ 模擬程式 → Record 報表
     └─→ Demogame  → 操作與逐局對帳
```

- 數學文件與 `Source/*.xlsx` 是規格來源，Config 是程式執行時的共同參數來源。
- 模擬程式與 Demogame 必須讀取同一份 Config，不得各自維護另一套輪帶、權重、Paytable 或 Feature 參數。
- `game_rule.md` 必須說明玩法、判獎順序、倍率口徑、Feature 流程與例外；程式不可補猜未定義的規則。
- 同一項資料若在多個檔案出現，修改時必須同步更新並完成對帳。
- 未支援的 RTP、Variant、Bet Mode、Profile 或 Feature，不得出現在 Config、Simulator 批次或 Demogame 選單。
- 會影響結果分布、RTP、觸發率、最大獎或 Retry 的修改，都必須更新版本並重新模擬。

---

## 1. 數學文件 Math Document

### 1.1 必要內容

模型開始實作前，數學文件至少要定義：

- Game ID、遊戲名稱、盤面尺寸與 Lines／Ways／Cluster 等得分方式。
- Symbol、Paytable、Wild／Scatter 規則與判獎順序。
- BG、FG、Cascade、Multiplier、Retrigger、Jackpot 等流程。
- Normal Bet、Extra Bet、Buy Feature、Super Feature 的成本與差異。
- 各 RTP 家族、Variant 與 Player Profile 的目標 RTP。
- Feature Trigger Rate、Hit Rate、Max Win／Max Multiplier 與上限。
- Card System 的區間、權重、倍率分母、Retry 與失敗處理。
- 同局同時符合多項條件時的處理優先順序。

計算口徑必須明確區分：

```text
RTP = Total Win ÷ 實際 Total Bet
卡片判定倍率 = 指定結果得分 ÷ card_system_coin_in
Max Multiplier = Round Total Win ÷ 該模式定義的基準成本
```

### 1.2 模型命名

| 項目 | 格式 | 範例 |
|---|---|---|
| 遊戲 ID | `H<三位數字>` | `H028` |
| 基礎數學 XLSX | `H<遊戲編號>1.xlsx` | `H0161.xlsx` |
| RTP／Variant 數學 XLSX | `H<遊戲編號>1<RTP><Variant>.xlsx` | `H016192A.xlsx` |

- `92`／`94` 表示 RTP 家族。
- `A`／`B` 表示同一 RTP 家族下的數學 Variant，不代表 Newbie／Oldhand。
- 沒有 B 版時只建立 A 版，不得建立內容相同的空白 B 版。

### 1.3 版本規則

基礎數學文件與 RTP／Variant 數學文件使用不同的版本格式：

| 文件 | 版本格式 | 範例 |
|---|---|---|
| `H<遊戲編號>1.xlsx` | 1 碼數字版本 | `H0161.xlsx`：`1` |
| `H<遊戲編號>1<RTP><Variant>.xlsx` | 4 碼數字版本 | `H016192A.xlsx`：`1.0.0.0` |

RTP／Variant 數學文件的四碼版本格式為：

```text
遊戲參數.卡片權重.SCR.其他文件
```

例如：`H016192A.xlsx` 的版本為 `1.0.0.0` 時，第 1 碼 `1` 必須與 `H0161.xlsx` 的版本 `1` 相同。

| 段位 | 變更時機 |
|---|---|
| 第 1 碼：基礎數學版本 | 必須對應 `H<遊戲編號>1.xlsx` 的 1 碼版本；基礎輪帶、Paytable、Feature、Bet Mode、判獎等內容變更時更新。 |
| 第 2 碼：卡片權重 | Newbie／Oldhand、BG／FG／Buy／Super Feature 的卡片區間或權重。 |
| 第 3 碼：SCR | SCR 設定、內容或結果。 |
| 第 4 碼：其他文件 | 不影響前三類的規則、Help、說明或排版。 |

- `H<遊戲編號>1.xlsx` 的版本只能填 1 碼，不得填成四碼。
- 所有 `H<遊戲編號>1<RTP><Variant>.xlsx` 的第 1 碼，都必須與同一遊戲的 `H<遊戲編號>1.xlsx` 版本相同。
- 基礎數學版本遞增時，所有受影響的 RTP／Variant 文件同步更新第 1 碼，並將第 2～4 碼歸零。
- 第 2 碼遞增後，第 3～4 碼歸零；第 3 碼遞增後，第 4 碼歸零。
- 同一次修改涉及多種類型時，只遞增順位最高的一碼，並將後續碼歸零。
- 依實際異動內容判斷版本，不得只依檔名判斷。
- `config.js` 的 `excel_version` 必須與基礎數學 XLSX 的 1 碼版本完全一致。
- `config_<RTP><Variant>.js` 的 `excel_version` 必須與對應 RTP／Variant XLSX 的 4 碼版本完全一致。
- 92／94 或 A／B 中所有受影響的模型都要更新，不得只改其中一份。
- 已封存版本不得覆寫；需要修正時建立新版本。

#### 1.3.1 XLSX 異動與版本同步

只要 XLSX 的正式內容有更新，就必須在同一次修改中更新對應版本；不得先改內容、之後才補版本。

| 異動內容 | 必須更新的版本 |
|---|---|
| 基礎數學 XLSX，例如 `H0161.xlsx` | 遞增該檔案的 1 碼版本；所有引用此次基礎異動的 RTP／Variant XLSX 同步更新第 1 碼，並將第 2～4 碼歸零。 |
| RTP／Variant 的遊戲參數需要更新第 1 碼 | 先遞增基礎數學 XLSX 的 1 碼版本，再同步更新所有受影響 RTP／Variant XLSX 的第 1 碼，並將第 2～4 碼歸零。 |
| Card System 區間或權重 | 更新實際異動之 RTP／Variant XLSX 的第 2 碼。 |
| SCR | 更新實際異動之 RTP／Variant XLSX 的第 3 碼。 |
| 只影響文件、說明或排版 | 更新實際異動之 RTP／Variant XLSX 的第 4 碼。 |

- 修改哪一份 XLSX，就更新哪一份 XLSX 的版本；未受影響的 XLSX 不得為了統一數字而無條件升版。
- 同一項異動同時影響 92／94 或 A／B 時，每一份受影響的 XLSX 都要依相同規則更新。
- 同一次異動涉及多個版本段位時，依順位最高的段位遞增，後續段位依第 1.3 節規則歸零。
- XLSX 版本更新後，必須重新產生其對應 Config，並同步更新 Config 的 `excel_version`。
- Simulator 與 Demogame 必須載入更新後的 Config；新產生的報表必須使用更新後的版本，不得沿用舊版號。

### 1.4 RTP 與 Bet Mode

下表為共用 target。實際專案若不同，必須在遊戲規格中註記，並同步修改 XLSX、Config、Simulator 與 Demogame。

| Config 家族 | Player Profile | Normal Bet | Extra Bet | Buy Feature | Super Feature |
|---|---|---:|---:|---:|---:|
| `92x` | Newbie | 93.00% | 93.00% | 92.50%（共用） | 92.50%（共用） |
| `92x` | Oldhand | 92.00% | 92.00% | 92.50%（共用） | 92.50%（共用） |
| `94x` | Newbie | 93.00% | 93.00% | 92.50%（共用） | 92.50%（共用） |
| `94x` | Oldhand | 94.00% | 94.00% | 92.50%（共用） | 92.50%（共用） |

- `x` 代表 A、B 等 Variant；Variant 不改變 Profile 定義。
- 產品顯示值可以四捨五入，模型計算與驗證必須使用完整精度。
- 各 Bet Mode 的 RTP 分母使用玩家在該模式的實際成本。
- Scatter Pay、購買進場盤、FG、Retrigger、Jackpot 是否計入 Total Win，必須與遊戲規則及 XLSX 公式一致。
- Card System Off／On、Newbie／Oldhand 及所有支援的 Bet Mode 必須分開驗證。

### 1.5 開發前檢查

- [ ] 遊戲規則沒有待確認的判獎順序或倍率口徑。
- [ ] 每個支援的 Config、Bet Mode 與 Profile 都有明確目標。
- [ ] 基礎數學 XLSX 為 1 碼版本，且所有 RTP／Variant XLSX 的第 1 碼均與其一致。
- [ ] XLSX 公式、命名、版本與工作頁用途可追溯。
- [ ] 最大獎與理論上限已計算，且未超出產品限制。
- [ ] 所有 Feature 的 Trigger、Retrigger、結束條件與上限已定義。
- [ ] Card System 是否啟用、使用哪些卡片及如何 Retry 已定義。

---

## 2. 卡片系統 Card System

### 2.1 定位與限制

Card System 是結果篩選與分流機制，不是獨立玩法。遊戲先依原始輪帶、盤面、判獎與 Feature 流程產生結果，再依預先抽出的卡片條件決定接受或重跑。

Card System 可控制倍率區間、要求觸發 Free Game、依 Newbie／Oldhand 改變結果分布，並依 Bet Mode 拆分 BG、FG、Buy Feature 與 Super Feature 的目標。

Card System 不得直接修改輪帶、Paytable、判獎公式、符號功能、FG 局數或演出流程。重跑會改變最終結果分布與 RTP，因此必須以實際流程模擬，不能只用權重推算。

### 2.2 設定結構

```text
card_system
├─ enabled
├─ retry_limit
├─ newbie
│  ├─ normal_bet → weight_bg／weight_fg
│  └─ extra_bet  → weight_bg／weight_fg
└─ oldhand
   ├─ normal_bet    → weight_bg／weight_fg
   ├─ extra_bet     → weight_bg／weight_fg
   ├─ buy_feature   → weight_fg
   └─ super_feature → weight_fg
```

- `retry_limit` 正式預設為 `10000`。
- `weight > 0` 才可抽中；`weight = 0` 只保留設定；權重不得小於 0。
- 每個啟用的 Profile／Mode 至少要有一張正權重卡片。
- 抽中率為該卡權重除以同組所有正權重總和。
- Profile 缺少某個 Mode 時，必須明定不套用或指定唯一 fallback，程式不得自行猜測。

### 2.3 卡片判定

`range` 卡使用 `(min, max]`：

```text
結果倍率 > min 且 結果倍率 <= max
```

- `(15, 20]` 不包含 15x、包含 20x；需要包含 0x 時可用 `(-1, 0]`。
- BG 已觸發 FG 時，即使 `pay_bg` 落入區間，也不得當作一般 BG `range` 結果。
- `free_game` 卡未觸發 FG 時必須重跑 BG。
- FG 卡 BG 倍率上限開啟時，除觸發 FG 外，BG 倍率也不得超過同一 BG Profile 內有效 `range` 卡的最大上限。
- 事件卡只定義接受條件，不得直接放置 Scatter 或直接呼叫 FG。

### 2.4 Retry 流程

```text
取得 Profile 與 Bet Mode
        ↓
固定抽出目標卡片
        ↓
依原始規則產生結果
        ↓
符合 → 接受並記錄
不符 → retry + 1 → 重跑
                    ↓
             達上限後保留最後結果並記錄失敗
```

- 同一局 Retry 期間固定原本抽到的卡片，不得每次重抽。
- BG 與 FG 為兩階段條件時，先完成 BG；觸發 FG 後再獨立抽 FG 卡，驗證整包 FG。
- Buy／Super Feature 必須先成功進入 Feature，再判定整包結果。
- Retry 不得重複扣款、重複計入場次或污染統計。
- 達上限時停止，保留最後結果並記錄 `Retry Limit Exceeded` 與失敗分類。
- 某張卡經常達到上限時，先檢查區間可達性、權重、倍率分母與 Profile，不得只提高上限。

### 2.5 倍率分母

| 模式 | RTP 實際成本 | Card System 判定成本 |
|---|---|---|
| Normal Bet | Normal Bet 實際成本 | Normal Bet 基準成本 |
| Extra Bet | Extra Bet 加價後成本 | Normal Bet 基準成本 |
| Buy／Super Feature | Feature 購買成本 | Normal Bet 基準成本 |

個別遊戲若採不同定義，必須在數學文件註明，並同步修改 XLSX、Config、Runtime、Simulator 與 Demogame。

### 2.6 必要監控

報表至少記錄 Config、Version、Profile、Bet Mode、開關、各卡抽取占比、Total／平均 Retry、Retry Limit Exceeded 比率與失敗分類。Card System 關閉時不得抽卡或 Retry；實際占比應在合理誤差內接近設定權重。

---

## 3. 模擬程式 Simulator

`Simulator.py` 是數學模型的主要驗證工具。數學邏輯、批次設定、Console 輸出與 Excel 報表必須使用相同的統計口徑。

### 3.1 程式架構

#### 3.1.1 加速：Numba、多執行緒

- 高頻數學核心使用 Numba 編譯；適用的核心函式使用 `@njit(nogil=True)`。
- 使用多執行緒平行執行模擬，例如 `ThreadPoolExecutor`；每個 Worker 必須持有獨立的 RNG 狀態。
- 正式計時前先執行 Warm-up，Numba 首次編譯時間不得計入 `duration`。
- Numba Core 只處理數值及固定型別 Array／Tuple；Config 解析、字串、DataFrame 與 Excel 留在 Python 層。
- 預先配置統計陣列與暫存 Buffer，模擬迴圈內不得反覆建立大型物件。
- 場次平均分配給各 Worker，餘數由前幾個 Worker 各多執行一場；合併後必須等於 `total_rounds`。
- Worker 回傳相同 shape／dtype；Count 與 Pay 欄位相加，Max 欄位取最大值。
- 固定 RNG、逐局 Trace 與 Debug 重現模式使用單執行緒。

#### 3.1.2 程式邏輯

程式依下列順序執行：

1. 讀取 `BATCH_RUNS` 的本批參數。
2. 載入 `config_file` 的自然機率參數。
3. 載入 `config_rtp_file` 的倍率權重參數。
4. 驗證兩份 Config 的 `game_id`、版本與資料相容性。
5. 將 Config 正規化為模擬核心使用的固定型別資料。
6. 依 `bet_mode`、Card System 開關與 Profile 建立本批設定。
7. 執行 Warm-up，再開始正式計時與多執行緒模擬。
8. 合併 Worker 統計，計算 RTP、Hit Rate、Feature、Retry 與遊戲專屬指標。
9. 依固定格式印出執行結果。
10. 需要輸出時，將相同結果寫入 `Record/*.xlsx`。

數學核心與報表／顯示邏輯必須分離。Card System 關閉時，不得執行抽卡或 Retry；`config_rtp_file` 不得改變 `config_file` 所定義的原始盤面與自然機率邏輯。

#### 3.1.3 執行結束後印出的內容

每個 Batch 結束後必須依第 3.3 節的順序與格式輸出，不得只印 RTP。欄位名稱固定使用英文，數值格式由共用格式化函式處理。

#### 3.1.4 輸出報表

- 報表固定輸出至該遊戲的 `Record/`，格式為 `.xlsx`。
- 報表與 Console 必須來自同一份統計結果，不得重新計算成不同口徑。
- 報表檔名固定沿用 H026 的命名順序，不得由個別遊戲任意調換欄位。

報表檔名格式：

```text
Card System Off：
<base_game_id>_<base_version_tag>_<timestamp>_betmode<bet_mode>_<rounds_tag>.xlsx

Card System On（Newbie／Oldhand）：
<rtp_game_id>_<rtp_version_tag>_<timestamp>_betmode<bet_mode>_<rounds_tag>_<rtp_tag>_<profile>_card.xlsx

Card System On（不分 Profile 的 Buy／Super Feature）：
<rtp_game_id>_<rtp_version_tag>_<timestamp>_betmode<bet_mode>_<rounds_tag>_<rtp_tag>_card.xlsx
```

各段規則：

| 段落 | 規則 | 範例 |
|---|---|---|
| `base_game_id` | Card System Off 時，使用基礎 Config／基礎 XLSX 的完整 Game ID。 | `H0161` |
| `base_version_tag` | Card System Off 時，使用基礎數學的 1 碼版本並補滿 2 位數。 | `2` → `02` |
| `rtp_game_id` | Card System On 時，使用 RTP／Variant Config 內的完整 Game ID。 | `H016192A` |
| `rtp_version_tag` | Card System On 時，四段版本各補滿 2 位數，再移除分隔點後依序串接。 | `2.1.3.13` → `02010313` |
| `timestamp` | 報表產生時間，格式為 `YYMMDDHHmm`。 | `2608141530` |
| `bet_mode` | 使用整數 Bet Mode。 | `0` |
| `rounds_tag` | `10^N` 場寫成 `10N`；非 10 的整次方則使用完整場次。 | `10^8` → `108` |
| `rtp_tag` | Card System On 時，取實際 RTP 小數點後 4 位，不含小數點與 `%`。 | `92.01%` → `9201` |
| `profile` | 分 Profile 時使用 `newbie` 或 `oldhand`；不分 Profile 時省略。 | `oldhand` |
| `card` | Card System On 時固定加在檔名最後。 | `card` |

範例：

```text
Card System Off：
H0161_02_2608141342_betmode0_105.xlsx

Card System On（Oldhand）：
H016192A_02000000_2608141341_betmode0_105_9129_oldhand_card.xlsx

Card System On（Feature Buy，不分 Profile）：
H026192A_02010313_2608141530_betmode2_108_9245_card.xlsx
```

- Card System Off 的檔名只能使用 `config_file` 所對應的基礎 `game_id` 與 1 碼版本，不得使用 `config_rtp_file` 的 RTP／Variant Game ID 或四段版本。
- Card System On 的檔名使用 `config_rtp_file` 所對應的 RTP／Variant `game_id` 與四段版本。
- `base_version_tag` 固定為 2 位數；例如基礎版本 `2` 輸出為 `02`。
- `rtp_version_tag` 每一段都必須補滿 2 位數，不是只移除 `.`；`2.1.3.13` 必須轉成 `02010313`，不得輸出成 `21313`。
- 四段中的單段若超過 2 位數，視為版本格式錯誤，停止輸出報表並提示修正版本。
- 檔名不得包含空白、冒號、百分比符號或版本分隔點。

`Overview` 工作頁：

- 內容、欄位順序、欄位名稱、數值與格式必須和第 3.3 節的 Console 輸出一致，不得重新排序。
- 不寫入 Batch 標題，例如 `=== Batch 1/1: {...} ===`。
- 不寫入 `<< By Game Info >>` 標題；Game Info 欄位依 Console 的既定順序直接接在 `standard_error` 之後。
- Card System 開啟時才顯示 `card_system_profile` 至 `retry_limit_fg`；關閉時整段不顯示，與 Console 規則一致。
- `Overview` 與 Console 必須使用同一份已計算結果，不得分別計算或套用不同格式。

`Multiplier Line` 工作頁：

- 每一列對應報表定義的一個倍率區間，欄位名稱必須維持下列英文格式。
- 共用欄位依下列順序輸出：

```text
base_game_cnt
base_game_pay
free_game_cnt
free_game_pay
free_game_cnt_BF
free_game_pay_BF
free_game_cnt_SF
free_game_pay_SF

FG_Hit_Rate
FG_Spin_Count

BG_Combo_1_Rate
BG_Combo_2_Rate
BG_Combo_3_Rate
BG_Combo_4_Rate
BG_Combo_5+_Rate

FG_Combo_1_Rate
FG_Combo_2_Rate
FG_Combo_3_Rate
FG_Combo_4_Rate
FG_Combo_5+_Rate
```

- `free_game_cnt_BF`、`free_game_pay_BF` 只在遊戲有 Buy Feature 時顯示。
- `free_game_cnt_SF`、`free_game_pay_SF` 只在遊戲有 Super Feature 時顯示。
- 不支援 BF／SF 時不得保留空白欄位或以 `0` 代替未支援功能。
- `cnt` 欄位使用整數；`pay` 欄位使用報表統一的得分精度；`Rate` 欄位使用一致的百分比格式。

共用欄位之後可接遊戲專屬的 By Game 欄位。H016 的 `Multiplier Line` 必須包含：

```text
BG_Big_Ghost_2_Rate
BG_Big_Ghost_3_Rate
BG_Big_Ghost_4_Rate

FG_Big_Ghost_2_Rate
FG_Big_Ghost_3_Rate
FG_Big_Ghost_4_Rate

BG_Avg_Gold_Frames
FG_Avg_Gold_Frames
```

- `--- 以下是 By Game 資訊 ---` 只用於規格分組說明，不是 Excel 的實際欄位。
- 其他遊戲依自身玩法定義 By Game 欄位，不得沿用 H016 不適用的欄位。
- 報表另需保留 Feature、Symbol、Pay Range、卡片抽取占比等驗證所需工作頁。

### 3.2 必要功能

#### 3.2.1 `BATCH_RUNS`

`BATCH_RUNS` 用於定義要依序執行的模擬組合。每一筆至少包含：

| 欄位 | 必要 | 說明 |
|---|---:|---|
| `config_file` | 是 | 自然機率參數檔；提供輪帶、Table、盤面與原始遊戲機率。 |
| `config_rtp_file` | 是 | 倍率權重參數檔；提供 RTP／Variant 與 Card System 使用的倍率權重。 |
| `bet_mode` | 是 | 押注模式，例如 `0` 為 Normal Bet；其他值依遊戲規格定義。 |
| `total_rounds` | 是 | 本批正式模擬的付費 Round 數，必須為正整數。 |
| `card_system_enabled` | 是 | 是否啟用 Card System，型別為 Boolean。 |
| `card_system_is_newbie` | 是 | `true` 為 Newbie、`false` 為 Oldhand；Card System 關閉時不套用 Profile。 |

範例：

```python
BATCH_RUNS = [
    {
        "config_file": "config.js",
        "config_rtp_file": "config_92A.js",
        "bet_mode": 0,
        "total_rounds": 1_000_000,
        "card_system_enabled": True,
        "card_system_is_newbie": False,
    },
]
```

- 每批開始時印出 `=== Batch n/total: {...} ===`，內容為該批完整設定。
- 每批重新載入兩份 Config，不得沿用上一批的全域狀態。
- Config 的 `game_id` 不一致時立即停止，不得繼續模擬或輸出報表。
- Card System Off 必須另跑自然機率基準；正式大場次前先以小場次檢查流程與報表。

### 3.3 執行結束後印出的內容

#### 3.3.1 固定順序與共用格式

Console 輸出順序是固定規範，不得依 dict、DataFrame 或統計完成時間任意排序。每個 Batch 必須依下列順序輸出：

1. Batch 標題：`=== Batch n/total: {...} ===`。
2. 遊戲資訊：`game_name`、`game_id`。
3. Config 與版本：`config_file`、`config_rtp_file`、`math_version`、`card_system`。
4. 執行設定：`bet_mode`、`bet_multi`、`coin_in`、`total_rounds`、`duration`。
5. Card System 資訊：從 `card_system_profile` 到 `retry_limit_fg`；只在 Card System 開啟時整段顯示。
6. 共用統計：從 `rtp_total` 到 `SCR`。
7. 波動資訊：`volatility_std`、`standard_error`。
8. 遊戲專屬資訊：`<< By Game Info >>` 及該遊戲規定的 By Game 欄位。

- 欄位必須依下方範例逐項排列，不得交換前後順序。
- 空白行只用於區塊分隔，不影響欄位順序；不得在同一區塊中插入其他欄位。
- 新增共用欄位時必須先更新本規範並指定位置，不得由個別遊戲自行插入。
- Card System 關閉時只省略第 5 項，`rtp_total` 必須直接接在 `duration` 之後。

```text
=== Batch 1/1: {'config_file': 'config.js', 'config_rtp_file': 'config_92A.js', 'bet_mode': 0, 'total_rounds': 1000000, 'card_system_enabled': True, 'card_system_is_newbie': False} ===

game_name              : 幸運王牌
game_id                : H016

config_file            : config.js
config_rtp_file        : config_92A.js
math_version           : 2.1.3.13
card_system            : on

bet_mode               : Normal Bet
bet_multi              : 1
coin_in                : 100.0
total_rounds           : 1,000,000
duration               : 00.000 sec

card_system_profile    : oldhand
card_retry_limit       : 20000
retry_total            : 8808086
avg_retry              : 8.808086
retry_limit_exceeded   : 0
retry_limit_bg_range   : 0
retry_limit_bg_freegame: 0
retry_limit_fg         : 0

rtp_total              : 00.0000%
rtp_bg                 : 00.0000%
rtp_fg                 : 00.0000%
hit_rate_bg            : 00.0000%
hit_rate_fg            : 00.0000%
fg_trigger_rate        : 00.0000% (cycle 00.00 spins)
retrigger_trigger_rate : 00.0000% (cycle 00.00 free spins)
avg_fg_spins           : 10.03 spins
special_symbol_cnt     : xxx
SCR                    : xxx

volatility_std         : 00.00
standard_error         : 00.00
```

- `math_version` 顯示 RTP／Variant 模型的完整四段版本號，例如 `2.1.3.13`；Console 依數學文件原格式輸出，不得自行省略或改寫。只有報表檔名依第 3.1.4 節轉為 `02010313`。
- `duration` 顯示正式模擬耗時，不包含 Numba Warm-up。
- Card System 關閉時，從 `card_system_profile` 到 `retry_limit_fg` 的整個區塊不顯示。
- 百分比欄位固定顯示 `%`；Cycle 必須同時顯示平均間隔與正確單位。
- `special_symbol_cnt` 統計出現特殊符號 `SC` 的 Spin 次數，Base Spin 與每一次 Free Spin 都要納入。
- 單次 Base Spin／Free Spin 只要盤面出現至少一個 `SC` 就加 `1`；同一 Spin 出現多個 `SC` 仍只加 `1`。
- Cascade 過程若同屬同一次 Spin，不得因不同盤面重複累加；該 Spin 最終最多計數 `1`。
- `total_spin = Base Spin 總數 + Free Spin 總數`。
- `special_symbol_rate = special_symbol_cnt / total_spin`，只作為 SCR 的中間計算值。
- `SCR = special_symbol_rate × 10,000,000,000`。
- Console 與 `Overview` 不輸出 `special_symbol_rate`，只輸出換算後的 `SCR`。
- `total_spin = 0` 時，`SCR` 輸出 `0`，不得除以零。
- 不適用的 Feature 欄位可不顯示，但不得以錯誤的 `0` 冒充已驗證結果。

#### 3.3.2 Game Info

`<< By Game Info >>` 固定放在 `standard_error` 之後，用來顯示遊戲專屬統計。欄位依玩法增減，不適用的欄位不得沿用其他遊戲。

H016 範例：

```text
<< By Game Info >>

avg_cascades_bg        : 0.410662
avg_cascades_fg        : 0.6329912625344514
golden_converted       : 182505
w2_events              : 4427
w2_bg_event_rate       : 0.330700%
w2_fg_event_rate       : 1.313552%
w2_bg_count_2          : 2917
w2_bg_count_3          : 373
w2_bg_count_4          : 17
w2_fg_count_2          : 1069
w2_fg_count_3          : 48
w2_fg_count_4          : 3
m1_bg_spin_rate        : 79.9233
```

- H016 的 By Game 欄位必須依上方順序輸出，不得依字母排序或統計產生順序重排。
- H016 若新增其他 By Game 欄位，新增欄位接在既有欄位之後，並同步更新本規範。

### 3.4 驗證清單

- [ ] `BATCH_RUNS` 每筆均包含六個必要欄位。
- [ ] 自然機率與倍率權重分別從 `config_file`、`config_rtp_file` 載入。
- [ ] 固定 RNG／種子可重現相同結果。
- [ ] Worker 合併後的總場次等於 `total_rounds`。
- [ ] Console 與 Excel 報表的共用欄位及數值一致。
- [ ] `special_symbol_cnt` 同時統計 Base Spin 與 Free Spin，且同一 Spin 即使出現多個 `SC` 也只累加一次。
- [ ] `SCR` 等於 `(special_symbol_cnt / total_spin) × 10,000,000,000`，且 Console 與 `Overview` 的數值一致。
- [ ] `Overview` 與 Console 的內容及順序一致，且未包含 Batch 與 `<< By Game Info >>` 標題。
- [ ] `Multiplier Line` 包含所有共用欄位，並依遊戲功能正確顯示或移除 BF／SF 與 By Game 欄位。
- [ ] 報表檔名依 H026 規則排列，時間、Bet Mode、場次及 Card System 後綴均正確。
- [ ] Card System Off 使用基礎 `game_id` 與 2 位數基礎版本，例如 `H0161_02`。
- [ ] Card System On 使用 RTP／Variant `game_id` 與補零後的四段版本，例如 `H016192A_02000000`。
- [ ] 四段版本已逐段補滿 2 位數，例如 `2.1.3.13` 正確輸出為 `02010313`。
- [ ] RTP 與 Feature Trigger 接近目標，偏差有統計解釋。
- [ ] Card System 設定占比與實際占比一致。
- [ ] Retry Limit Exceeded 為零，或已有明確原因與核准處理方式。
- [ ] 最大獎未超出限制，理論可達結果有相應測試。
- [ ] 所有正式 Config／Mode／Profile 均有最新版本報表。

---

## 4. Demogame

### 4.1 用途與載入

Demogame 是模型邏輯、流程與 Debug 資訊的可操作驗證介面，不只是視覺展示。它必須能用單局結果證明 Config、Simulator 與遊戲規則一致。

- 主入口固定為 `index.html`，使用相對路徑，雙擊即可離線執行。
- Demogame 的模型顯示格式為 `<Config>-<Profile>`，例如 `92A-Oldhand`。
- 遊戲名稱、盤面、輪帶、權重、Paytable、Bet Mode 與 Feature 參數從 Config 取得。
- 不得為演出方便另寫一套簡化數學邏輯。
- Config 無法載入或欄位不完整時要顯示明確錯誤，不得靜默使用舊值。

### 4.2 必要行為

- 支援 Normal Spin，以及遊戲實際存在的 Extra Bet、Buy Feature、Super Feature。
- Bet 顯示與 Credit 扣款使用實際模式成本；Win 依流程加入。
- Auto、Speed、Reset 不得改變 RNG、得分或統計結果。
- BG、Cascade、FG、Retrigger 與 Feature 狀態按真實流程播放。
- Config、Version、Profile、Card System 與 Language 只顯示實際支援的內容。
- Help 與 `game_help_draft.md` 一致，不在 HTML 另維護一份規則。

### 4.3 Debug 與重現

Debug Mode 至少可查看：

- Config、Version、Profile、Bet Mode 與 Card System 狀態。
- Card 抽獎值、卡片區間與 Retry 次數。
- Table、Drop Mode、Reel RNG、總範圍、Stop Index 與 Reel Length。
- 初始盤面、每段 Cascade、Line／Ways Win、Multiplier 與最終結果。
- FG 觸發、局數、Retrigger、整包 Win 及即時 Log。

指定 Card Range 與 Reel RNG 必須互斥。指定值要檢查數量與範圍，且只作用於規格定義的下一個 Spin；不得因指定 RNG 或 Force FG 進入無限重跑。

### 4.4 與 Simulator 對帳

至少準備下列可重現案例：無獎 BG、一般得分、Wild／Scatter、Cascade／Multiplier、FG Trigger／Retrigger、各 Bet Mode、Card System range／free_game／Retry、Max Win 截斷及遊戲專屬 Feature。

逐項確認盤面、RNG、各段得分、Total Win、Coin In、倍率、Feature 狀態與 Retry 計數一致。

### 4.5 交付檢查

- [ ] 離線開啟無錯誤，Console 無未處理例外。
- [ ] Config 切換後所有資料與顯示同步更新。
- [ ] 所有支援的 Bet Mode 均可完成完整流程。
- [ ] Card System Off／On 及 Newbie／Oldhand 行為正確。
- [ ] Debug 資訊足以重現並與 Simulator 對帳。
- [ ] Demo 統計口徑與模擬報表一致。
- [ ] 不存在寫死的舊遊戲名稱、倍率、Table、輪帶或 Help。

---

## 5. Config

### 5.1 定位與轉檔

Config 分為基礎 Config 與 RTP／Variant Config：

| Config | 對應數學文件 | 版本格式 |
|---|---|---|
| `config.js` | `H<遊戲編號>1.xlsx`，例如 `H0161.xlsx` | `excel_version` 為 1 碼 |
| `config_<RTP><Variant>.js` | `H<遊戲編號>1<RTP><Variant>.xlsx`，例如 `config_92A.js` 對應 `H016192A.xlsx` | `excel_version` 為 4 碼，且第 1 碼對應基礎版本 |

- `Newbie`／`Oldhand` 是 Card System 的 Player Profile，不寫入 Config 檔名。
- RTP／Variant 模型的 XLSX、Config、Simulator、Demogame 與報表必須使用相同 Config 代號。

兩種 Config 都是 Simulator 與 Demogame 的執行參數，不是人工獨立維護的第二份數學文件。正式參數必須由各自對應的 `Source/*.xlsx` 透過 `Source/xlsx_to_config.py` 產生。

```text
修改基礎或 RTP／Variant Source XLSX
      ↓
依文件類型更新 1 碼或 4 碼版本
      ↓
執行 update_config.bat 或 xlsx_to_config.py
      ↓
檢查欄位、型別、長度、權重與版本
      ↓
完成 XLSX → Config → 程式讀取對帳
      ↓
執行 Simulator 與 Demogame 驗證
```

禁止直接修改 Config 中由 XLSX 產生的大型陣列來規避轉檔；結果錯誤時應修正 XLSX、mapping 或轉檔程式。

### 5.2 最低資料

Config 至少應提供遊戲實際需要的：

- `game_id`、`game_name`、`excel_version` 與 Config 類型／代號。
- Reel 數、盤面尺寸、Symbol ID／名稱／屬性。
- Reel Strip／Weight／Length、Paytable、Payline／Ways／Cluster。
- Table、Table Weight、Drop Mode 與各 Scene 資料。
- Bet Mode ID、成本倍率、Bet Level／DENOM。
- BG、FG、Cascade、Multiplier、Retrigger 與 Feature 參數。
- Card System 開關、Retry Limit、Profile、卡片區間與權重。
- Max Win／Max Multiplier 與其他產品限制。

同一概念在不同 Config 間必須保持一致，並記錄於 `Source/xlsx_config_usage_mapping.md`。

### 5.3 資料驗證

- `game_id` 與所在遊戲資料夾一致。
- `config.js` 的 `excel_version` 與基礎 XLSX 完全一致，且只能是 1 碼。
- `config_<RTP><Variant>.js` 的 `excel_version` 與對應 RTP／Variant XLSX 完全一致，且必須是 4 碼。
- RTP／Variant Config 的版本第 1 碼，必須與 `config.js` 及基礎 XLSX 的版本相同。
- Config 檔名、類型、內部 RTP／Variant 與來源 XLSX 相符。
- 所有 Weight 非負，啟用選項的總權重大於 0。
- Reel、Weight、Paytable、Symbol 與 Mode 陣列長度相容。
- 所有 ID／索引在有效範圍，無重複或遺漏。
- Min／Max、倍率、局數與 Max Win 限制合法。
- 未支援的 Mode／Profile／Feature 不存在或明確停用。
- 浮點精度足以還原來源數值，不因格式化造成 RTP 偏差。

### 5.4 版本與歷史檔

- 正式 Config 放在遊戲資料夾根層，包括基礎 `config.js` 與實際支援的 `config_92A.js` 等 RTP／Variant Config。
- 歷史 Config 放在對應的 `Versions/` 版本目錄；基礎 Config 與 RTP／Variant Config 都必須保留來源及版本關係。
- `Versions/version_manifest.js` 記錄完整版本、可用 Config、路徑與變更說明。
- Runtime、Simulator 與 Demogame 不得自行覆寫 Config 版本。
- Index 載入 `config.js` 時顯示 1 碼基礎版本；載入 RTP／Variant Config 時顯示完整 4 碼版本。
- RTP／Variant 版本若第 1、2 碼相同，Index 只顯示第 3、4 碼最新的版本。
- Version 與 Config 選單只列出 manifest 中實際存在且相容的組合。

### 5.5 最終交付檢查

- [ ] `config.js` 對應基礎 XLSX；每個 `config_<RTP><Variant>.js` 對應相同 RTP／Variant 的 XLSX。
- [ ] 基礎 XLSX／Config 使用 1 碼版本，RTP／Variant XLSX／Config 使用 4 碼版本，且第 1 碼一致。
- [ ] XLSX、Config、Simulator、Demogame 與文件版本一致。
- [ ] Config 可由 Source 工具重新產生，且不會產生非預期差異。
- [ ] 每個 Config 都有來源 XLSX 與 mapping 說明。
- [ ] Simulator 與 Demogame 沒有重複或覆寫 Config 參數。
- [ ] 所有可選 Config／Version／Profile／Mode 均真實存在且已驗證。
- [ ] 最新模擬報表已保存於 `Record/`，結果符合目標與限制。
- [ ] 代表性單局已完成 Config、Simulator、Demogame 三方對帳。
- [ ] `~$*.xlsx`、`__pycache__/`、臨時檔與測試輸出未列入正式交付。

### 5.6 完成條件

模型只有在下列條件全部成立後才可視為完成：

1. 數學規則與計算口徑明確，無未決定的核心邏輯。
2. Config 可由數學來源重建，版本與參數可追溯。
3. Simulator 已完成所有支援組合的統計驗證。
4. Card System 的權重、區間、Retry 與失敗監控通過。
5. Demogame 的代表性單局可與 Simulator 對帳。
6. 文件、XLSX、Config、報表與 Demogame 均為同一正式版本。
