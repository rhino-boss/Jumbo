# Slot 遊戲開發規範

## 1. 目錄

- [1. 目錄](#1-目錄)
- [2. 模型命名規則](#2-模型命名規則)
- [3. 版本規則](#3-版本規則)
- [4. RTP 設定](#4-rtp-設定)
- [5. Card System](#5-card-system)

---

## 2. 模型命名規則

### 2.1 遊戲與數學模型

| 項目 | 格式 | 範例 |
|---|---|---|
| 遊戲 ID | `H<三位數字>` | `H028` |
| PARsheet／XLSX | `H<遊戲編號>1<RTP><Variant>.xlsx` | `H028192A.xlsx` |
| Config | `config_<RTP><Variant>.js` | `config_92A.js` |
| Demo Game 顯示 | `<Config>-<Profile>` | `92A-Oldhand` |

### 2.2 Config 組成

| 部分 | 定義 |
|---|---|
| `92`／`94` | Oldhand 在 Normal Bet／Extra Bet 使用的 RTP 家族。 |
| `A`／`B` | 同一 RTP 家族下的數學版型；不代表 Newbie／Oldhand。 |
| `Newbie`／`Oldhand` | Card System 的玩家 Profile，不寫入 Config 檔名。 |
| Version | 數學內容版本，獨立保存在 config 欄位及 Version 選單。 |

規則：

- 同一數學模型的 XLSX、config、Simulator 與 Demo Game 必須使用相同的 Config 代號。
- Config 代號不得包含版本號或玩家 Profile。
- 沒有 B 版時只建立 A 版，不得建立內容相同的空白 B 版。
- 遊戲未支援的 RTP 家族或 Variant 不得出現在 Config 選單。
- UI 的 Version 與 Config 順序統一為 `Version → Config → Language`。

---

## 3. 版本規則

### 3.1 版本格式

數學模型使用四段式版本：

```text
Major.Minor.Patch.Build
```

例如：`2.0.0.36`。

| 段位 | 變更時機 |
|---|---|
| `Major` | 數學架構、核心玩法、設定 Schema 或結果相容性有重大變更。 |
| `Minor` | 新增 Bet Mode、Feature、Card Profile 或一組可獨立驗證的模型能力。 |
| `Patch` | 修正玩法、判獎、Runtime／Simulator 邏輯，但不改變主要設定架構。 |
| `Build` | 調整輪帶、權重、RTP、卡片區間、卡片權重、公式快取或重新產生 config。 |

### 3.2 同步規則

- XLSX 的版本欄位與 config 的 `excel_version` 必須完全一致。
- 同一次數學修改涉及 92／94 或 A／B 多份模型時，每份受影響模型都要更新版本。
- Runtime、Simulator 與 Demo Game 不得自行覆蓋或改寫 config 版本。
- 修改數學內容後必須重新產生 config，並完成 XLSX → config → XLSX 的一致性檢查。
- 只修改文件、排版或不影響數學結果的 UI，不更新數學模型版本。
- 修改會影響結果、RTP、觸發率、最大獎或 Retry 的程式邏輯，必須更新版本並重新模擬。

### 3.3 歷史版本

- 目前正式使用的 config 保留在遊戲目錄根層，例如 `config_92A.js`。
- 歷史 config 保存於 `Versions/<Major.Minor>/`，例如 `Versions/2.0/config_92A.js`。
- `Versions/version_manifest.js` 必須記錄完整版本、可用 Config、檔案路徑與變更說明。
- 不得覆寫已封存版本；需要修正時建立新版本。
- Demo Game 的 Version 選單只能列出 manifest 中實際存在的版本與 Config。

---

## 4. RTP 設定

### 4.1 Newbie／Oldhand 與押注模式

下表為共用 RTP target。百分比是產品顯示值；實際計算使用 XLSX 與 config 中未四捨五入的完整數值。

| Config 家族 | Player Profile | Normal Bet | Extra Bet | Buy Feature | Super Feature |
|---|---|---:|---:|---:|---:|
| `92x` | Newbie | 93.00% | 93.00% | 92.50%（共用） | 92.50%（共用） |
| `92x` | Oldhand | 92.00% | 92.00% | 92.50%（共用） | 92.50%（共用） |
| `94x` | Newbie | 93.00% | 93.00% | 92.50%（共用） | 92.50%（共用） |
| `94x` | Oldhand | 94.00% | 94.00% | 92.50%（共用） | 92.50%（共用） |

規則：

- `x` 代表 A、B 等 Variant，Variant 不改變 Profile 的 RTP 定義。
- Newbie 與 Oldhand 使用同一套遊戲玩法，由 Card System 權重產生不同 RTP。
- Buy Feature／Super Feature 預設不分 Newbie／Oldhand，皆使用共用的 92.50%。
- 遊戲沒有某個押注模式時，該模式為不適用，不得顯示或接受該模式。
- 若產品要求不同 target，必須同步更新本規範、遊戲規則、XLSX、config 與版本，不得只在 Runtime 寫死例外。

### 4.2 RTP 計算分母

```text
RTP = Total Win ÷ Total Bet
```

| 押注模式 | RTP 的 Total Bet |
|---|---|
| Normal Bet | Normal Bet 實際成本。 |
| Extra Bet | Extra Bet 加價後的實際成本。 |
| Buy Feature | Buy Feature 的購買成本。 |
| Super Feature | Super Feature 的購買成本。 |

- Scatter Pay、購買進場盤、FG、Retrigger、Jackpot 等是否計入 Total Win，必須與個別遊戲規則及 XLSX 公式一致。
- RTP 分母與 Card System 的卡片倍率分母不同，不得混用。
- Card System Off／On、Newbie／Oldhand，以及所有已支援 Bet Mode 都必須分開模擬及輸出報表。
- Card System On 的 RTP 必須執行實際遊戲與 retry 流程，不得只用卡片權重推算。

---

## 5. Card System

### 5.1 功能目的

Card System 是結果篩選與分流控制機制，不是獨立玩法。遊戲先依原始輪帶、盤面、判獎、消除及 Feature 流程產生結果，再用預先抽出的卡片條件判斷是否接受該結果。

Card System 可用於：

- 控制單局結果落入指定倍率區間。
- 指定單局必須觸發 Free Game。
- 依 Newbie／Oldhand 套用不同結果分布。
- 依 Bet Mode 拆分 BG、FG、Buy Feature 與 Super Feature 的控制目標。
- 支援新手體驗、老手救援、數學驗證與分流測試。

Card System 不得直接修改：

- 輪帶與盤面生成規則。
- Pay Table 與原始判獎公式。
- Wild、Scatter、Multiplier 等符號規則。
- Free Game 局數、Retrigger 與演出流程。

不符合卡片條件的結果會被捨棄並重跑，因此 Card System 仍會影響最終輸出分布與 RTP。

### 5.2 設定結構

```text
card_system
├─ enabled
├─ retry_limit
├─ newbie
│  ├─ normal_bet
│  │  ├─ weight_bg
│  │  └─ weight_fg
│  └─ extra_bet
│     ├─ weight_bg
│     └─ weight_fg
└─ oldhand
   ├─ normal_bet
   │  ├─ weight_bg
   │  └─ weight_fg
   ├─ extra_bet
   │  ├─ weight_bg
   │  └─ weight_fg
   ├─ buy_feature
   │  └─ weight_fg
   └─ super_feature
      └─ weight_fg
```

| 欄位 | 說明 |
|---|---|
| `enabled` | 此遊戲及 Config 是否啟用 Card System。 |
| `retry_limit` | 單局卡片驗證的重跑上限；正式規格為 `10000`。 |
| `newbie`／`oldhand` | 玩家 Profile。 |
| `normal_bet` 等 | 遊戲實際支援的 Bet Mode。 |
| `weight_bg` | BG 卡片及相對權重。 |
| `weight_fg` | FG 或購買特色整包結果的卡片及相對權重。 |

```text
卡片抽中率 = 該卡片權重 ÷ 同一 Profile 內所有正權重總和
```

- `weight > 0`：可被抽中。
- `weight = 0`：保留設定但不會被抽中。
- 權重不得小於 0。
- 啟用的 Profile 至少要有一張正權重卡片。
- 未實作 Card System 的遊戲必須設為不支援，Demo Game 不得顯示 Card System 按鈕。

### 5.3 卡片類型

#### 5.3.1 區間卡 `range`

區間使用 `(min, max]`：

```text
結果倍率 > min 且 結果倍率 <= max
```

例如 `(15, 20]` 不包含 15x、包含 20x。若需要包含 0x，可使用 `(-1, 0]`。

BG 觸發 Free Game 時，即使 `pay_bg` 落在區間內，也不得當作一般 BG 區間卡結果。

#### 5.3.2 Free Game 事件卡 `free_game`

- 未觸發 FG：不符合卡片條件，重跑 BG。
- SPS 的 FG 卡 BG 倍率上限關閉：成功觸發 FG 即通過 BG 條件。
- SPS 開關開啟：成功觸發 FG，且 BG 倍率不超過 BG 卡片權重上限，才可通過。

事件卡只定義接受條件，不得直接放置 Scatter 或直接呼叫 FG。

### 5.4 執行流程

```text
取得 Player Profile 與 Bet Mode
        ↓
選擇對應 BG／FG／BF／SF Profile
        ↓
依權重抽出目標卡片
        ↓
依遊戲原始規則產生結果
        ↓
計算倍率或事件狀態
        ↓
符合 → 接受結果並寫入報表
不符合 → retry + 1 → 未達上限則重跑
                     → 達上限則保留最後結果並記錄失敗
```

- 同一局 retry 期間必須維持原本抽到的卡片，不得每次 retry 重新抽卡。
- BG 與 FG 是兩階段條件時，先固定 BG 卡完成 BG 篩選；BG 觸發 FG 後，再獨立抽 FG 卡並驗證整包 FG。
- FG 不符合時的重跑範圍依遊戲數學流程定義，但不得把 BG 與 FG 錯誤綁成同一次重新抽卡。

### 5.5 各押注模式

| 模式／場景 | 抽取卡片 | 判定內容 | 事件處理 |
|---|---|---|---|
| Normal Bet BG | Profile 的 `weight_bg` | `range` 檢查 `pay_bg` | `free_game` 要求 BG 觸發 FG |
| Normal Bet FG | BG 觸發後抽 `weight_fg` | 檢查整包 `pay_fg` | 不符合時依遊戲流程重跑 |
| Extra Bet BG | Extra Profile 的 `weight_bg` | `range` 檢查 `pay_bg` | `free_game` 要求 BG 觸發 FG |
| Extra Bet FG | BG 觸發後抽 `weight_fg` | 檢查整包 `pay_fg` | 不符合時依遊戲流程重跑 |
| Buy Feature | `buy_feature.weight_fg` | 檢查規格定義的購買結果 | 先確保購買盤成功觸發 FG |
| Super Feature | `super_feature.weight_fg` | 檢查規格定義的購買結果 | 先確保購買盤成功觸發 Feature |

Profile 缺少某個模式時，必須明定不套用 Card System 或指定唯一 fallback；Runtime 不得自行猜測。

### 5.6 卡片倍率分母

```text
卡片判定倍率 = 指定結果得分 ÷ card_system_coin_in
```

| 押注模式 | 實際 RTP 成本 | Card System 判定成本 |
|---|---|---|
| Normal Bet | Normal Bet 實際成本 | Normal Bet 基準成本 |
| Extra Bet | Extra Bet 加價後成本 | Normal Bet 基準成本 |
| Buy／Super Feature | Feature 購買成本 | Normal Bet 基準成本 |

Extra Bet 與 Feature Buy 的卡片倍率不是除以玩家實際支付成本。個別遊戲若採用其他定義，必須同步修改本規範、遊戲規則、XLSX、config、Runtime、Simulator 與 Demo Game。

H025 若採用不同倍率分母，也必須先完成上述所有同步，不可只改其中一處。

### 5.7 Retry 與失敗處理

失敗原因至少分為：

- BG 倍率未命中區間。
- BG 抽到 `free_game` 卡但未觸發 FG。
- FG 卡已觸發 FG，但 BG 倍率超過 SPS 上限。
- FG／Buy／Super Feature 整包倍率未命中。
- 整個 retry 期間從未成功觸發 FG。

達到 `retry_limit = 10000` 時：

1. 停止重跑，避免無限迴圈。
2. 保留最後一次產生的結果。
3. 記錄 Retry Limit Exceeded 與失敗分類。

若某張卡經常達到上限，應檢查區間可達性、權重、倍率分母與 Profile，不得只提高 retry limit。

### 5.8 FG 卡 BG 倍率上限

SPS 的「FG 卡 BG 倍率上限」預設開啟。此開關屬於 SPS 控制，不是 `card_system.enabled`。

```text
BG 卡片權重上限 = 同一 BG Profile 中所有 weight > 0 的 range 卡之 max 最大值
```

- 開啟：FG 卡需成功觸發 FG，且 BG 倍率不得超過上限。
- 關閉：FG 卡只需成功觸發 FG。
- `weight = 0` 的 range 卡與 `free_game` 卡本身不參與上限計算。

例如最高有效區間為 `(90x, 100x]`，上限即為 100x；已觸發 FG 且 BG `<= 100x` 才可通過。

### 5.9 報表與監控

Card System 報表至少記錄：

- Config、Version、Player Profile、Bet Mode 與 Card System 開關。
- SPS 的 FG 卡 BG 倍率上限開關。
- 抽卡次數及各卡實際占比。
- Total retry、平均 retry 與各卡平均 retry。
- Retry Limit Exceeded 總數、比率與失敗分類。
- FG 卡已觸發但 BG 倍率超限次數。
- 整個 retry 期間從未觸發 FG 的次數。

實際抽卡占比應接近設定權重；Card System 開關關閉時，不得執行抽卡或 retry。
