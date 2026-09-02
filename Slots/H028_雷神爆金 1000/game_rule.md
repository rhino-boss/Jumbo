# 雷神爆金1000 (Thunder Boost 1000) 遊戲規則說明

> 文件版本：v1.1
> 對標競品：PG - Lucky Neko
> 撰寫依據：`../iGaming 遊戲代號一覽.xlsx`（遊戲名稱、Game ID、PARsheet ID）及 `../其他遊戲/101016/101016 simulation.py`（遊戲邏輯）；本次以 101016 模擬程式的遊戲邏輯為主
> 編號：H028
> 撰寫日期：2026-07-13

---

## §1. 遊戲基本資訊

| 項目 | 說明 |
| --- | --- |
| 遊戲名稱 | 雷神爆金1000 |
| Game ID | 101016 |
| PARsheet ID | H0281 |
| 遊戲英文名 | Thunder Boost 1000 |
| 遊戲類型 | Video Slot - 2,025–32,400 Ways / Megaways / Cascade |
| 盤面規格 | 6 輪盤、主盤面最高 5 列，另有位於 R2-R5 上方的 Extra Reel |
| 中獎方式 | Way Game，自左至右連續相鄰輪判定 |
| 最小 / 最大 Ways | 2,025 Ways / 32,400 Ways |
| 押注模式 | **Normal Bet**：提供，一般押注；**Extra Bet**：不提供；**Buy Feature**：提供，75 × Bet |
| Buy Feature | 有；價格為 75x Bet |
| 共用數學版本 | `H0281.xlsx` / `config.js`：`3` |
| RTP / Card 版本 | `H028192A.xlsx`、`H028194A.xlsx` / `config_92A.js`、`config_94A.js`：`3.2.0.0` |

---

## §2. 盤面結構

```text
       ER2  ER3  ER4  ER5
        ↓    ↓    ↓    ↓
     ┌────┬────┬────┬────┐
     │    │    │    │    │
     └────┴────┴────┴────┘

   R1   R2   R3   R4   R5   R6
   ↓    ↓    ↓    ↓    ↓    ↓
┌────┬────┬────┬────┬────┬────┐
│    │    │    │    │    │    │
├────┼────┼────┼────┼────┼────┤
│    │    │    │    │    │    │
├────┼────┼────┼────┼────┼────┤
│    │    │    │    │    │    │
├────┼────┼────┼────┼────┼────┤
│    │    │    │    │    │    │
├────┼────┼────┼────┼────┼────┤
│    │    │    │    │    │    │
└────┴────┴────┴────┴────┴────┘
```

文字說明：
* 主盤面為 6 輪 Megaways 可變高度盤面，每輪最高 5 格。
* Extra Reel 固定對應 R2、R3、R4、R5 上方各 1 格。
* 中獎採 Way Game，由 R1 開始往右連續相鄰輪出現相同符號即可形成中獎。
* 中獎後觸發 Cascade；中獎符號消除、上方符號掉落並補入新符號，直到沒有新中獎為止。

---

## §3. 符號類別

### 3.1 一般符號

| 類別 | 符號 |
| --- | --- |
| 高分符號（H） | 招財貓、日式鼓、燈籠、扇子、握壽司、壽司 |
| 低分符號（L） | A、K、Q、J、10 |

寫明：
* R2-R5 的一般符號可為大符號，尺寸可覆蓋 1、2、3、4 格。
* 大符號在 Ways 計算時不論覆蓋幾格，都只視為 1 個符號。
* 本作的 **M1** 為倍數來源符號，主盤面採尺寸對應倍數規格；Extra Reel 上依一般倍數符號邏輯處理。
* **Scatter** 亦可為 1x2、1x3、1x4 大符號；觸發 Free Game 時，每一格均視為 1 個 Scatter 計數。

### 3.2 特殊符號

| 符號 | 出現位置 | 行為 |
| --- | --- | --- |
| **Wild** | 僅出現在 R2、R3、R4、R5 | 替代除 Scatter 外的所有符號。 |
| **Scatter** | 不配置於初始輪帶；盤面停定後可由 Post Scatter 於任意輪產生，Cascade Drop 亦依掉落權重補入，且可為 1x1、1x2、1x3、1x4 | 4 個以上觸發 Free Game；FG 內可再次作為 retrigger 來源。 |
| **M1** | 主盤面與 Extra Reel | 主盤面用於累積倍數；Extra Reel 上的 M1 出現即計入當局倍數。 |

---

## §4. 賠率表（Pay Table）

**單位：倍 / Bet x 該符號的 Way 數量**

| 符號 | 6 連 | 5 連 | 4 連 | 3 連 |
| --- | --- | --- | --- | --- |
| 招財貓 | 4 | 2.5 | 2 | 1.5 |
| 日式鼓 | 2.5 | 1.5 | 1.25 | 1 |
| 燈籠 | 2 | 1.5 | 1.25 | 0.5 |
| 扇子 | 1.5 | 1 | 0.75 | 0.4 |
| 握壽司 | 0.75 | 0.6 | 0.5 | 0.3 |
| 壽司 | 0.75 | 0.6 | 0.5 | 0.3 |
| A、K | 0.5 | 0.4 | 0.3 | 0.2 |
| Q、J、10 | 0.2 | 0.15 | 0.1 | 0.05 |

補充說明：
* Wild、Scatter、M1 不提供一般連線賠付。
* 單一符號中獎計算公式為：`賠率 x Ways x Bet`，再乘上當局累積總倍數。

---

## §5. 核心遊戲流程（Base Game）

1. 玩家設定 Bet 後開始 Spin。
2. 主盤面 6 輪與 Extra Reel 同步轉動並停輪。
3. 依 Way Game 規則判定中獎，計算各符號的 Ways 與基礎賠付。
4. 統計當局出現的 M1 倍數，形成當局總倍數。
5. 將當局所有中獎賠付乘上目前累積總倍數。
6. 中獎符號消除並觸發 Cascade；若金框符號參與中獎，消除後直接在原位轉為 Wild。
7. 補入新符號後再次判定中獎、倍數與 Cascade，直到盤面不再形成新中獎。
8. 初始盤面停定後依 Post Scatter 權重產生 Scatter；後續 Cascade 補牌亦可依 Drop 權重補入 Scatter。
9. 當整個 Spin 結束後，再判定 Scatter 是否觸發 Free Game。

---

## §6. 核心特色

### 6.1 金框直轉 Wild

* 出現在 R2、R3、R4、R5 的一般符號可帶有金框。
* 金框符號若參與該回合中獎並被消除，消除後直接轉換為 Wild 留在原位，供下一次掉落與判定使用。
* **Wild 僅停留一個 Cascade 回合**，下一輪判定後若未再次因機制保留，則依盤面正常更新。

### 6.2 M1 倍數機制

* 主盤面上的 M1 依符號尺寸決定本次提供的倍數。
* **主盤面 M1** 的尺寸與倍數對應如下：

| M1 尺寸 | 對應倍數 |
| --- | --- |
| 1x1 | x2 |
| 1x2 | x3 |
| 1x3 | x4 |
| 1x4 | x5 |

* 同一回合若出現多個 M1，倍數採 **加總累積**。
* 主盤面的 M1 參與中獎或留存在盤面時，皆視為該回合可收集的倍數來源。

### 6.3 Extra Reel 的 M1

* Extra Reel 上的 M1 視為獨立倍數來源，出現即計入當局總倍數。
* Extra Reel 不使用 1x2 / 1x3 / 1x4 的尺寸倍數映射，避免與主盤面 Jumbo M1 混用。
* 每顆 Extra Reel M1 固定提供 **x2** 倍數。

---

## §7. 免費遊戲（Free Spins / Free Game, FG）

### 7.1 觸發

* 主盤面任意位置出現 4 個以上 Scatter 即觸發 Free Game。
* 4 個 Scatter 觸發 10 場 Free Game。
* 每多 1 個 Scatter，額外 +2 場。

| Scatter 數量 | Free Game 場次 |
| --- | --- |
| 4 SC | 10 |
| 5 SC | 12 |
| 6 SC | 14 |
| 7 SC | 16 |
| 8 SC 以上 | 每多 1 SC 再 +2；整段 FG 最多 50 場 |

### 7.2 FG 玩法

* 進入 FG 時，累積倍數從 **x2** 開始。
* FG 期間倍數 **不重置**，會跨局持續累積到整段 FG 結束。
* 金框直轉 Wild 機制於 FG 期間持續有效。
* FG 期間 Scatter 可由每次初始盤面停定後的 Post Scatter 或 Cascade Drop 產生，並可用於 retrigger。
* Extra Reel 上的 M1 出現即計入該局倍數累積。

### 7.3 Retrigger（加局）

* FG 期間再次出現 4 個以上 Scatter，可立即加局。
* 加局場次與一般 FG 觸發一致：

| Scatter 數量 | Retrigger 場次 |
| --- | --- |
| 4 SC | +10 |
| 5 SC | +12 |
| 6 SC | +14 |
| 7 SC | +16 |
| 8 SC 以上 | 每多 1 SC 再 +2；不得使整段 FG 超過 50 場 |

---

## §8. Buy Feature（購買特色）

* 玩家可透過 Buy Feature 直接進入一次 Free Game。
* Buy Feature 價格固定為 **75x Bet**。
* Buy 進場後直接套用一般 Free Game 規格。

---

## §9. 邊界 / 例外情境（Edge Cases）

### 9.1 金框 / Wild 相關

* 金框只作用於 R2-R5 的一般符號，Wild / Scatter / M1 不帶金框。
* 金框符號必須實際參與當回合中獎，才會在消除後直轉 Wild。
* Wild 只保留一個 Cascade 回合，不跨整個 Spin 常駐。

### 9.2 倍數機制相關

* 主盤面 M1 採尺寸決定倍數，Extra Reel M1 不套用尺寸映射。
* 同一回合多個 M1 倍數採加總，不採相乘。
* FG 累積倍數跨局保留；Base Game 則每次新 Spin 重新開始計算。

### 9.3 Scatter 相關

* Scatter 不可被 Wild 替代。
* 1x2、1x3、1x4 的 Scatter 以實際占用格數計入 Scatter 總數。
* FG 期間 Scatter 仍可出現，並可作為 retrigger 來源。
* 觸發與 retrigger 依 `10 + (SC 數 - 4) × 2` 計算，整段 FG 最多 50 場。

### 9.4 Free Game 相關

* FG 起始倍數為 x2。
* FG 結束後，累積倍數清空，下一次新進 FG 重新自 x2 起算。

### 9.5 Buy Feature 相關

* Buy Feature 價格固定為 75x Bet。
* Buy 進場後直接套用一般 FG 規格，沒有額外保證盤面。

### 9.6 Way Game 計算相關

* Ways 自 R1 起由左至右連續相鄰輪計算。
* 大符號無論覆蓋幾格，在單輪 Ways 數量中只計 1 個符號。
* Extra Reel 僅對應 R2-R5 上方位置，不延伸新增第 7 輪。

### 9.7 Simulator 卡片系統（測試功能）

* 卡片系統是模擬器的結果篩選／重試功能，不改變玩家端玩法與派彩公式。
* Normal Bet 可選新手或老手權重；BG 卡與 FG 卡分開抽取。
* 區間卡的倍率邊界為 `(min, max]`，且 Normal Bet 區間卡只接受未觸發 FG 的 BG 結果。
* Free Game 卡會先重試至 BG 觸發 FG，再依同身分的 FG 卡篩選整場 FG 派彩。
* Buy Feature 使用 `Weight_BF_FG` 篩選整場 FG 結果。
* 卡片倍率分母均使用 Normal Bet coin-in；每個階段最多重試 `card_system.retry_limit` 次，超限時保留最後一次結果並記錄於報表。
* 權重來源為 RTP 工作簿的 `Multiplier_Weight`，由 `Source/model_sync.py` 寫入對應 RTP config。

---

## §10. 投注、派彩與 RTP 定義

| 模式 | `bet_mode` | 每局成本 | 說明 |
| --- | ---: | --- | --- |
| Normal Bet | 0 | `100 × bet_multi` coin | BG 結束後若觸發 FG，FG 不另行扣款 |
| Buy Feature | 2 | `100 × 75 × bet_multi` coin | 觸發盤面 BG 派彩設計為 0，成本全數計入 FG RTP 分母 |

單次 Cascade 派彩：

```text
Cascade Pay = Σ(Paytable × Ways) × 當前累積倍數 × bet_multi
```

RTP 報表定義：

```text
RTP Total = (BG Pay + FG Pay) / Coin In
RTP BG    = BG Pay / Coin In
RTP FG    = FG Pay / Coin In
```

`trigger_fg_bg_pay` 及 `trigger_fg_bg_max_pay` 仍屬 BG Pay，不得重複納入 FG Pay。大符號只計 1 個 Ways 符號，但 Scatter 依實際占用格數計數。

### 10.1 目標 RTP

| Config / Profile | BG RTP | FG RTP | Total RTP | FG 目標週期 |
| --- | ---: | ---: | ---: | ---: |
| 92A Oldhand Normal Bet | 72% | 20% | 92% | 300 局/次 |
| 94A Oldhand Normal Bet | 72% | 22% | 94% | 300 局/次 |
| 92A / 94A Newbie Normal Bet | 72% | 21% | 93% | 依 Newbie BG 卡片權重 |
| 92A / 94A Buy Feature | 0% | 92.5% | 92.5% | 1 |

卡片倍率區間上限為 20,000x；這是 Card 可篩選區間上限，不等於額外對自然遊戲結果進行截斷。

---

## §11. 實作資料來源與版本

| 資料 | 權威範圍 | 版本規則 |
| --- | --- | --- |
| `Source/H0281.xlsx` | 自然機率、輪帶、掉落、版型、賠率、FG 場數 | 單一整數，目前 `3` |
| `config.js` | `H0281.xlsx` 的執行版 | `excel_version` 必須為單一整數 |
| `Source/H028192A.xlsx` / `H028194A.xlsx` | 卡片區間、Fix Num、RTP 權重 | 四碼 `基礎.卡片.SCR.其他`，目前 `3.2.0.0` |
| `config_92A.js` / `config_94A.js` | RTP / Card 執行資料 | 必須與 RTP XLSX 四碼版本一致 |
| `game_help_draft.md` | 玩家可見規則文案 | 不得與本文件遊戲邏輯矛盾 |

Simulator 與 index 同時載入 base config 與 RTP config；自然機率以 base config 為準，版本及 Card System 以 RTP config 為準。載入時必須檢查 `game_id` 與主版本相同。

衝突優先順序：`game_rule.md` 已確認規則 → XLSX 數學資料 → config 執行檔 → Simulator / index 表演。若發現任一層不一致，必須停止對外驗證並先修正轉換或載入來源。

---

## 附錄 A. 詞彙對照

| 詞彙 | 說明 |
| --- | --- |
| BG | Base Game，主遊戲 |
| FG | Free Game，免費遊戲 |
| Way Game | 由左至右相鄰輪連續相同符號的中獎方式 |
| Cascade | 中獎消除後掉落補牌並重新判定 |
| Extra Reel | 位於 R2-R5 上方的額外符號列 |
| M1 | 本作倍數來源符號 |
| Jumbo M1 | 主盤面可占 1 至 4 格的 M1 |
| Retrigger | FG 期間追加免費局數 |

---

## 附錄 B. 文件註記

* 遊戲名稱、Game ID、PARsheet ID：`../iGaming 遊戲代號一覽.xlsx`
* 遊戲邏輯來源：`../其他遊戲/101016/101016 simulation.py`
* 目前實作：`Simulator.py`
* 數學資料：`Source/H0281.xlsx`、`Source/H028192A.xlsx`、`Source/H028194A.xlsx`、`config.js`、`config_92A.js`、`config_94A.js`
* 架構參考：`../H026_彩罐熱舞 1000/Simulator.py`

本文件為 H028《雷神爆金1000》規格說明。
