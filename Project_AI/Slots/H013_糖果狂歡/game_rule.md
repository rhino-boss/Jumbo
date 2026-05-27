# 糖果狂歡 (Sweet Bonanza 1000) 遊戲規則說明

> 文件版本：v0.1
> 編號：H013
> 撰寫日期：2026-05-21

---

## §1. 遊戲基本資訊

| 項目 | 說明 |
| --- | --- |
| 遊戲名稱（內部代號） | 糖果狂歡（H013） |
| 遊戲英文名 | Sweet Bonanza 1000 |
| 遊戲類型 | Video Slot - Cluster Pays / Cascade |
| 盤面規格 | 6 輪盤、5 列固定盤面 |
| 中獎方式 | 同一符號在整個盤面出現達門檻即可得分，無賠線 |
| 最小 / 最大 Ways | 不適用，本作為全盤面計數型玩法 |
| 押注規格 | `Normal Bet`、`Extra Bet (1.25x)`、`Feature Buy (75x)`、`Super Feature Buy (500x)` |
| Buy Feature | 有，`Feature Buy = 75x Bet`；`Super Feature Buy = 500x Bet` |

補充說明：
* Help 畫面標示本作可達 `25,000x Bet`。
* 本文件以目前 `H013_Simulator.py` 與 `H013_Box.py` 的實際程式行為為主來源。

---

## §2. 盤面結構

```text
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
* 主盤面為固定 6 輪、5 列。
* 初始盤面由對應場景的 reel strip 滾停產生。
* 中獎後會移除所有得分符號，剩餘符號往下掉落，並依同一 reel 的後續順序補牌，形成 Cascade / Tumble。
* 本作沒有獨立 Extra Reel。

---

## §3. 符號類別

### 3.1 一般符號

| 類別 | 符號 |
| --- | --- |
| 高分符號（M） | Heart、Square、Pentagon、Rectangle |
| 低分符號（L） | Apples、Peaches、Watermelon、Grapes、Bananas |

補充說明：
* 程式內部分別以 `M1 ~ M4`、`A`、`K`、`Q`、`J`、`TE` 表示。
* 一般符號採全盤面計數，不看相鄰、不看路徑、不看連線。

### 3.2 特殊符號

| 符號 | 出現位置 | 行為 |
| --- | --- | --- |
| **WW / Wild** | 目前參考資料中未見自然掉落配置 | 目前程式保留 Wild 代號，但本版數學模型未配置可見出現量與一般得分用途 |
| **C1 / Scatter** | 6 輪皆可出現 | Base Game 結束後若最終盤面有 4、5、6 顆可支付 Scatter 獎；同時觸發 10 場 Free Game |
| **C2 / Multiplier** | 主要在 Free Game / Buy 相關輪帶中出現 | 在 Free Game 結算時提供倍數值，依當局使用的高表 / 低表權重抽出倍數後加總 |

---

## §4. 賠率表（Pay Table）

**單位：100 credit bet**

| 符號 | 4 顆 | 5 顆 | 6 顆 | 8-9 顆 | 10-11 顆 | 12 顆以上 |
| --- | --- | --- | --- | --- | --- | --- |
| Scatter | 300 | 500 | 10000 | 0 | 0 | 0 |
| Heart | 0 | 0 | 0 | 1000 | 2500 | 5000 |
| Square | 0 | 0 | 0 | 250 | 1000 | 2500 |
| Pentagon | 0 | 0 | 0 | 200 | 500 | 1500 |
| Rectangle | 0 | 0 | 0 | 150 | 200 | 1200 |
| Apples | 0 | 0 | 0 | 100 | 150 | 1000 |
| Peaches | 0 | 0 | 0 | 80 | 120 | 800 |
| Watermelon | 0 | 0 | 0 | 50 | 100 | 500 |
| Grapes | 0 | 0 | 0 | 40 | 90 | 400 |
| Bananas | 0 | 0 | 0 | 25 | 75 | 200 |

補充說明：
* `WW / Wild` 與 `C2 / Multiplier` 不提供一般 pay。
* 一次盤面判獎時，會對每一種一般符號各自統計總數；達門檻的符號可同時得分並一起被消除。
* Scatter 獎在 Base Game 連消全部結束後，依最終盤面上的 `C1` 數量單獨結算。

---

## §5. 核心遊戲流程（Base Game）

1. 玩家選擇下注模式並開始 Spin。
2. 系統依下注模式決定使用的 BG 輪帶組與表權重，產生 6 輪、5 列初始盤面。
3. 統計每一種一般符號在盤面上的總數；達到 `8-9 / 10-11 / 12+` 門檻者得分。
4. 所有本輪得分符號會同時移除，剩餘符號往下掉落。
5. 每個 reel 的補牌優先依原 reel 順序承接後續符號，而不是額外獨立掉落池。
6. 補牌完成後重新判定盤面；若再次形成得分符號群，重複步驟 3-5。
7. 當盤面不再形成新的得分組合時，重新統計最終盤面上的 `C1 / Scatter`。
8. 若最終盤面有 `4 / 5 / 6` 顆 Scatter，先支付 Scatter 獎，再觸發 10 場 Free Game。

---

## §6. 核心特色

### 6.1 Tumble / Cascade

* 本作採全盤面消除機制，達門檻的符號會整批移除。
* 每次消除後，未消除的符號往下掉落，並由 reel 後續符號補上。
* 只要盤面持續形成新得分組合，就會一直連消，次數不設硬上限。

### 6.2 Extra Bet

* `Extra Bet` 下注成本為一般下注的 `1.25x`。
* 程式上會切換到 `EB` 專用 BG 輪帶與 `table_extra_bet` 權重。
* Help 畫面標示其目的為提高進入 Feature 的機會。

### 6.3 Free Game 倍數機制

* `C2 / Multiplier` 只在 Free Game / Buy 相關流程中作為主要特色。
* 當單局 Free Game 的連消全部結束後，系統會依最終盤面上的 `C2` 顆數，逐顆抽取倍數值後加總。
* 該局若沒有 `C2`，則該局倍數視為 `1x`。
* 該局 Free Game 的所有一般得分，會以同一個總倍數一起放大。

---

## §7. 免費遊戲（Free Spins / Free Game, FG）

### 7.1 觸發

* Base Game 連消結束後，若最終盤面出現 `4 / 5 / 6` 顆 `C1 / Scatter`，即可觸發 Free Game。
* 目前程式行為中，`4 / 5 / 6 Scatter` 皆固定獲得 **10 場** Free Game。

### 7.2 FG 玩法

* 目前 `H013_Simulator.py` 以固定拆法執行：**2 場高表 + 8 場低表**。
* 高表 / 低表使用不同的 `FG strip` 與不同的 `multiplier_range` 權重。
* 每一局 FG 都會先完整模擬該局的連消結果，再依該局最終盤面上的 `C2` 決定總倍數。
* 該局所有連消得分都乘上同一個總倍數後，累加到本次 FG 總得分。

### 7.3 Retrigger（加局）

* Free Game 可 retrigger。
* 當單局 FG 連消結束後，若最終盤面有 `3 / 4 / 5 / 6` 顆 Scatter，則加 **5 場**。
* 這 5 場的組成在目前程式中為：**1 場高表 + 4 場低表**。
* 單次進入 FG 後，包含 retrigger 在內，總場次上限為 **50 場**。

---

## §8. Buy Feature（購買特色）

* `Feature Buy` 價格為 **75x Bet**。
* `Super Feature Buy` 價格為 **500x Bet**。
* Buy 進場時不先玩一般 Base Game，而是直接切入對應的 Buy 輪帶與 FG 輪帶配置。
* `Feature Buy` 會使用 `FB` 輪帶組；`Super Feature Buy` 會使用 `SB` 輪帶組。

---

## §9. 邊界 / 例外情境（Edge Cases）

### 9.1 判獎相關

* **9.1.1 全盤面計數**：本作不看相鄰、不看連線，只看同一符號在整個盤面的總數。
* **9.1.2 多符號同時得分**：若同一輪盤面有多種一般符號同時達門檻，會同時計獎並一起消除。
* **9.1.3 Scatter 延後判定**：Scatter 不參與一般連消判獎，必須等連消全部結束後，再看最終盤面數量。

### 9.2 掉落相關

* **9.2.1 補牌承接 reel 順序**：消除後補牌不是獨立隨機池，而是沿用對應 reel 後續符號。
* **9.2.2 同輪單顆限制**：目前程式補牌時，若某一 reel 已存在 `C1`，遇到下一顆 `C1` 會跳過；`C2` 亦採相同限制。

### 9.3 Free Game / 倍數相關

* **9.3.1 倍數在該局結束後決定**：Free Game 的總倍數取決於該局連消全部完成後留在最終盤面的 `C2` 數量。
* **9.3.2 無倍數時視為 1x**：若該局最終盤面沒有 `C2`，該局得分不額外放大。
* **9.3.3 Retrigger 低門檻**：BG 需要 `4+ Scatter` 觸發 FG，但 FG 內 retrigger 只需 `3+ Scatter`。
* **9.3.4 FG 總場次封頂**：同一次 FG 流程最多進行 50 場，超過上限時不再加局。

### 9.4 買入相關

* **9.4.1 Feature Buy 與 Super Feature Buy 為不同模式**：兩者成本與使用輪帶不同，不應混用。
* **9.4.2 Buy 模式仍沿用 FG 核心規則**：進入 Buy 後，倍率、retrigger、50 場上限等核心邏輯仍依 Free Game 規則執行。

---

## 附錄 A. 詞彙對照

| 詞彙 | 說明 |
| --- | --- |
| BG | Base Game，主遊戲 |
| FG / Free Game | 免費遊戲 |
| Tumble / Cascade | 中獎後移除得分符號並補牌，直到無新得分 |
| Scatter / C1 | 連消結束後用於支付 Scatter 獎與觸發 FG 的特殊符號 |
| Multiplier / C2 | Free Game 主要倍數符號，按顆數抽倍數並加總 |
| Strip / Reel | 盤面來源輪帶 |
| High Table / Low Table | FG 使用的兩組不同機率配置 |
| Feature Buy | 直接購買進入特色玩法 |

---

## 附錄 B. 文件來源 / 參考

### 主來源

* `C:\Users\rhinshen\Mine\個人工作區\2_Program\Project\Slots\H013_Simulator.py`
* `C:\Users\rhinshen\Mine\個人工作區\2_Program\Project\Slots\Source\H013_Box.py`

### 補充來源

* `C:\Users\rhinshen\Mine\個人工作區\2_Program\Project\Slots\Source\General\Math.py`
* `C:\Users\rhinshen\Mine\個人工作區\2_Program\Project\Slots\Source\General\RedBox.py`
* `C:\Users\rhinshen\Mine\個人工作區\0_Project (專案相關)\IGaming\1_專案\遊戲開發\所有遊戲\H013_糖果狂歡\歷史紀錄\v1\H013197-0.0.0.1.xlsx`
* `C:\Users\rhinshen\Mine\個人工作區\0_Project (專案相關)\IGaming\1_專案\遊戲開發\所有遊戲\H013_糖果狂歡\遊戲畫面_Help\*.png`

### 採信原則

* 若歷史 xlsx / Help 與目前程式行為不一致，**以目前程式行為為準**。
* 本文件已知採用的現行程式規格包含：FG 初始 **2 高表 + 8 低表**、FG retrigger **+1 高表 + 4 低表**、FG 上限 **50 場**。
