# 咚咚金剛 (Dong Dong Kong) 遊戲規則說明

> 文件版本：v0.1（草稿）
> 編號：H029 / JHS104001
> 撰寫日期：2026-08-06

---

## §1. 遊戲基本資訊

| 項目 | 說明 |
| --- | --- |
| 遊戲名稱（內部代號） | 咚咚金剛（H029） |
| 遊戲英文名 | Dong Dong Kong |
| Game ID | JHS104001 |
| 遊戲類型 | Video Slot - Ways / Cascade |
| 盤面規格 | 6 輪盤、4 列固定盤面（Free Game A 可擴列） |
| 中獎方式 | 4,096 Ways，由左至右連續判定 |
| 最小 / 最大 Ways | 4,096 ／ 38,416（Free Game A 擴列後） |
| 押注規格 | 提供 Normal Bet 與 Buy Free Game 兩種押注模式 |
| Buy Feature | 有，價格為 80x Bet |
| 最大派彩倍率 | 9,600x ⏳ |
| 波動性 | Very High（V.I. 14.66） |

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
└────┴────┴────┴────┴────┴────┘
```

文字說明：
* 主盤面為固定 6 輪、4 列，構成 4⁶ = 4,096 Ways。
* 本作沒有獨立 Extra Reel。
* 中獎採 Ways 判定，由最左輪起連續出現才計算，同一輪上多顆相同符號以相乘方式累計。
* 每輪結算後，所有中獎符號會消除並觸發 Cascade，直到沒有新的中獎組合為止。

### 2.1 Free Game A 的擴列盤面

Free Game A（Mystery Symbol）觸發 Expand Bomb 後，中間 R2–R5 會逐步向上開列，最高可達 7 列：

```text
   R1   R2   R3   R4   R5   R6
   ↓    ↓    ↓    ↓    ↓    ↓
        ┌────┬────┬────┬────┐
        │    │    │    │    │
        ├────┼────┼────┼────┤
        │    │    │    │    │
┌────┬──┼────┼────┼────┼────┼──┬────┐
│    │  │    │    │    │    │  │    │
├────┼──┼────┼────┼────┼────┼──┼────┤
│    │  │    │    │    │    │  │    │
├────┼──┼────┼────┼────┼────┼──┼────┤
│    │  │    │    │    │    │  │    │
├────┼──┼────┼────┼────┼────┼──┼────┤
│    │  │    │    │    │    │  │    │
└────┴──┴────┴────┴────┴────┴──┴────┘
  4     7     7     7     7     4  ← 最大列數
```

* R1 與 R6 固定 4 列，不參與擴列。
* 中間四輪全數擴至 7 列時，Ways 數為 4 × 7 × 7 × 7 × 7 × 4 = 38,416。

---

## §3. 符號類別

### 3.1 一般符號

| 代號 | 符號 |
| --- | --- |
| M1 | Pic E ⏳ |
| M2 | Pic D ⏳ |
| M3 | Pic C ⏳ |
| M4 | Pic B ⏳ |
| M5 | Pic A ⏳ |
| A | 撲克 A |
| K | 撲克 K |
| Q | 撲克 Q |
| J | 撲克 J |
| TE | 撲克 10 |

### 3.2 特殊符號

| 代號 | 符號 |
| --- | --- |
| C1 | Bonus |
| C2 | Mystery |
| C3 | Wild |
| C4 | Expand Bomb |
| C5 | +1 Free Spin |
| C6 | +2 Free Spin |
| C7 | +3 Free Spin |

---

## §4. 賠率表（Pay Table）

**單位：× total bet**

### 4.1 一般符號賠率表

| 符號 | 代號 | 6 連 | 5 連 | 4 連 | 3 連 |
| --- | --- | --- | --- | --- | --- |
| Pic E | M1 | 25x | 10x | 4x | 1x |
| Pic D | M2 | 10x | 5x | 2x | 0.8x |
| Pic C | M3 | 7.5x | 4x | 1.5x | 0.7x |
| Pic B | M4 | 5x | 3x | 1.2x | 0.6x |
| Pic A | M5 | 2.5x | 1.5x | 1x | 0.5x |
| A / K / Q / J / 10 | A / K / Q / J / TE | 1x | 0.5x | 0.2x | 0.1x |

補充說明：
* Wild（C3）與 Bonus（C1）不提供一般賠付。
* 每種符號只支付最長的一組連線組合。
* 同一輪上出現多顆相同符號時，各輪的顆數以相乘方式累計中獎注數。
* 所有得分皆以 total bet 為基準。

### 4.2 Bonus（C1）賠率表

Bonus 符號本身不派彩，僅用於累積 Star Meter 觸發免費遊戲。

---

## §5. 核心遊戲流程（Base Game）

1. 玩家選擇押注並開始 Spin。
2. 系統依權重從 13 組主輪帶中抽選一組（9 組一般輪帶 ／ 4 組含 Mystery 輪帶），停輪形成 6 輪 × 4 列盤面。
3. 依 Ways 規則由最左輪起連續判定，計算本次所有中獎組合。
4. 若停輪盤面含有 Mystery 符號（C2），本局進入 **Mystery Random Event**（見 §6.2）。
5. 盤面上的中獎符號消除；若消除後形成空格，由上方符號往下掉落，並從 Cascade 補牌輪帶補入新符號，形成 Cascade。
6. Cascade 補牌輪帶依本局是否觸發 Mystery Random Event 分流：未觸發時使用 6 組一般補牌輪帶；已觸發時使用 2 組含 Mystery 的補牌輪帶。
7. Bonus 符號（C1）落入盤面時累積 Star Meter；Bonus 本身不會因自身中獎被消除，但同盤有其他一般符號中獎時會一併消失 ⏳。
8. 重複步驟 3–7，直到盤面不再形成新的中獎組合。
9. 當本次 Spin 無法再消除後，統計 Star Meter 的 Bonus 累積數量；若達門檻則觸發 Free Game（見 §7.1）。

> 單次 Base Game 一局最多可累積 4 顆 Bonus 符號。

---

## §6. 核心特色

### 6.1 Cascade（連鎖消除）

* 所有中獎的一般符號會被消除。
* 剩餘符號向下掉落填補空位，上方由補牌輪帶補入新符號。
* 新盤面重新判獎，若再度中獎則繼續消除，直到無新中獎組合為止。

### 6.2 Mystery Random Event（隨機神秘符號）

* Base Game 停輪盤面若出現 Mystery 符號（C2），該局即進入 Mystery Random Event。
* 事件期間，Mystery 符號**不會因中獎被消除**，會持續保留至下一次 Cascade。
* 事件期間的 Cascade 補牌輪帶也含有 Mystery 符號，可疊出多顆。
* 每次 Cascade 後，盤面上所有 Mystery 符號會**同時揭示為同一個符號**。
* Mystery 可揭示為 10、J、Q、K、A、Pic A–E 共 10 種一般符號，各符號權重相同（不會揭示為 Wild 或 Bonus）。

### 6.3 Wild

* Wild（C3）出現在 R2–R6，R1 不會出現。
* Wild 替代所有一般得分符號，不可替代 Bonus。

### 6.4 Star Meter（星星集點）

* Bonus 符號（C1）落入盤面時累積 Star Meter。
* 集滿 **3 顆** Bonus：觸發一般版 Free Game。
* 集滿 **4 顆** Bonus：直接觸發升級版 Free Game。
* Star Meter 的累積範圍與歸零時點 ⏳

---

## §7. 免費遊戲（Free Spins / Free Game, FG）

### 7.1 觸發

* 集滿 **3 顆** Bonus 符號 → 進入 Free Game 模式選擇，選定後可選擇是否進行 Gamble 賭升級版（見 §7.5）。
* 集滿 **4 顆** Bonus 符號 → 直接進入**升級版**的模式選擇，無需 Gamble。
* 三種 Free Game 模式由玩家自行選擇：

| 模式 | 名稱 | 初始場次 |
| --- | --- | --- |
| FG A | Mystery Symbol Free Spins | 6 |
| FG B | Multiplier Ladder Free Spins | 8 |
| FG C | Expanding Wild Free Spins | 7 |

* 單次進入 Free Game 後，包含所有加場在內，最多進行 **50 場**。

### 7.2 FG A — Mystery Symbol（神秘符號）

* 初始 **6** 場。
* Mystery 符號出現在 R2–R5。
* 每次 Cascade 後，所有 Mystery 符號同時揭示為同一個符號。
* Mystery 符號在 FG 中**永不消除**，消除後會回到 Mystery 狀態，並於下一次 Cascade 重新揭示新符號。
* Mystery 符號**跨局保留**：新的一局開始時，上一局的 Mystery 符號會落到輪盤最下方。
* R6 有 **Expand Bomb（C4）**：落入時向上開啟 R2–R5 各一列，並加 **3** 場免費遊戲。Expand Bomb 本身於落入後消除。
* Expand Bomb 開列時，空缺由**上方符號填補**，不使用 Cascade 補牌輪帶。
* 盤面中間四輪最高可擴至 7 列，形成最高 38,416 Ways。
* 輪帶上有 **+2 Free Spin（C6）**，落入時加 2 場。
* **升級版**：Free Game 開始時，R2–R5 各帶 1 顆 Mystery 符號（共 4 顆）。

### 7.3 FG B — Multiplier Ladder（倍數階梯）

* 初始 **8** 場。
* 盤面上方為倍數階梯，共 36 階：

  `1x → 2x → 3x → 4x → 5x → 6x → 7x → 8x → 9x → 10x → 11x → 12x → 13x → 14x → 15x → 16x → 17x → 18x → 19x → 20x → 25x → 30x → 35x → 40x → 45x → 50x → 60x → 70x → 80x → 90x → 100x → 150x → 200x → 300x → 400x → 500x`

* 倍數由 **1x** 起算。第一場之後的每一場新 Spin、以及每一次 Cascade，倍數各前進一階。
* 倍數到達 **500x** 後停留於該階，直到整段 Free Game 結束。
* 到達特定倍數時追加免費場次：

| 到達倍數 | 追加場次 |
| --- | --- |
| 15x | +3 |
| 20x | +1 |
| 50x | +2 |
| 100x | +2 |
| 500x | +2 |

* 輪帶上有 **+1 Free Spin（C5）**，落入時加 1 場。
* **升級版**：初始場次由 8 場提升為 **9** 場。

### 7.4 FG C — Expanding Wild（擴展百搭）

* 初始 **7** 場。
* 倍數由 **1x** 起算。
* Wild 符號出現在 R2–R5。
* 每一顆落入的 Wild 會**向下擴展**，在其下方所有可用位置生成新的 Wild。
* 盤面上每產生一顆 Wild，倍數 **+1x**。
* 輪帶上有 **+3 Free Spin（C7）**，落入時加 3 場。
* **升級版**：倍數起始值由 1x 提升為 **10x**。
* 倍數於每局結束時是否重置 ⏳

### 7.5 Gamble（賭升級版）

* 集滿 3 顆 Bonus 觸發時，玩家選定 Free Game 模式後，可選擇進行一次 Gamble。
* Gamble 成功：進入該模式的**升級版**。
* Gamble 失敗：返回 Base Game，僅保留觸發該局 Base Game 本身的得分。
* Gamble 僅決定「升級版 ／ 失去」，不影響輪帶權重。
* 各模式的 Gamble 勝率：

| 模式 | 一般觸發勝率 | Buy Feature 觸發勝率 |
| --- | --- | --- |
| FG A Mystery Symbol | 26.38% | 26.95% |
| FG B Multiplier Ladder | 56.60% | 56.09% |
| FG C Expanding Wild | 51.00% | 50.90% |

### 7.6 Retrigger（加局）

* Free Game 期間的加場來源為各模式的 Free Spin 符號與機制加場（見 §7.2–§7.4）。
* Free Game 期間是否可由 Bonus 符號再次觸發 Free Game ⏳

---

## §8. Buy Feature（購買特色）

* 玩家可支付 **80x Bet** 直接購買 Free Game。
* 購買後直接進入 Free Game 模式選擇，取得的是**一般版**，並可選擇 Gamble 賭升級版。
* Buy Feature 進場**不保留** Base Game 的得分。
* Buy Feature 觸發的 Free Game 使用**相同輪帶但不同權重**。
* Buy Feature 的 Gamble 勝率與一般觸發不同（見 §7.5 表）。

---

## §9. 邊界 / 例外情境（Edge Cases）

### 9.1 Ways 判獎相關

* **9.1.1 由最左至右連續才算中獎**。
* **9.1.2 每種符號只支付最長組合**。
* **9.1.3 同輪多顆相乘**：多顆相同符號落在同一輪時，各輪顆數相乘構成中獎注數。
* **9.1.4 Cascade 後新中的組合另行累計**。

### 9.2 Wild 相關

* **9.2.1 Wild 位置受限**：Base Game 的 Wild 出現在 R2–R6，R1 不會出現。
* **9.2.2 Wild 不可替代 Bonus**。
* **9.2.3 FG C 的 Wild 位置**：Expanding Wild 模式的 Wild 出現在 R2–R5。

### 9.3 Mystery 相關

* **9.3.1 Mystery 揭示範圍**：僅揭示為 10、J、Q、K、A、Pic A–E 共 10 種一般符號，權重相同。
* **9.3.2 Mystery 不揭示為特殊符號**：不會揭示為 Wild 或 Bonus。
* **9.3.3 全盤同時揭示**：同一次 Cascade 後，盤面所有 Mystery 揭示為同一符號。
* **9.3.4 BG 的 Mystery 不消除**：Mystery Random Event 期間，Mystery 參與中獎後不會被消除。
* **9.3.5 FG A 的 Mystery 永不消除**：消除後回到 Mystery 狀態並重新揭示。
* **9.3.6 FG A 的 Mystery 跨局保留**：新一局開始時落至輪盤最下方。
* **9.3.7 Mystery 數量超過該輪列數時的處理** ⏳

### 9.4 Cascade 相關

* **9.4.1 補牌輪帶依 Mystery 狀態分流**：Base Game 未觸發 Mystery Random Event 時使用一般補牌輪帶；已觸發時使用含 Mystery 的補牌輪帶。
* **9.4.2 Cascade 結束條件**：盤面不再形成新的中獎組合時結束。
* **9.4.3 Expand Bomb 的填補方式不同於 Cascade**：開列的空缺由上方符號填補，不從補牌輪帶抽取。

### 9.5 Bonus / Star Meter 相關

* **9.5.1 Bonus 不派彩**：僅用於累積 Star Meter。
* **9.5.2 單局 Bonus 上限**：Base Game 一局最多累積 4 顆 Bonus。
* **9.5.3 Bonus 的消除條件**：Bonus 不會因自身中獎被消除，但同盤有其他一般符號中獎時會一併消失 ⏳。
* **9.5.4 Star Meter 累積範圍與歸零時點** ⏳。

### 9.6 Free Game 相關

* **9.6.1 FG 場次硬上限**：單次進入 Free Game 後，含所有加場最多 **50 場**。
* **9.6.2 FG B 倍數封頂**：到達 500x 後停留於該階至整段 FG 結束。
* **9.6.3 FG A 擴列上限**：R2–R5 最高擴至 7 列，R1 / R6 固定 4 列。
* **9.6.4 Gamble 失敗的得分處理**：返回 Base Game，僅保留觸發局本身的得分。
* **9.6.5 FG B / FG C 的倍數是否跨局保留** ⏳。

### 9.7 帳務相關

* **9.7.1 押注鎖定**：Spin 開始後該局押注即鎖定，無法變更。
* **9.7.2 Max Win**：單局最大派彩 9,600x ⏳；達上限後的處理方式 ⏳。
* **9.7.3 故障處理**：Malfunction voids all pays and plays（故障時所有派彩與遊戲無效）。

---

## 附錄 A. 詞彙對照

| 詞彙 | 英文 | 說明 |
| --- | --- | --- |
| BG | Base Game | 主遊戲 |
| FG | Free Game / Free Spins | 免費遊戲 |
| Ways | Ways | 由左至右連續、同輪多顆相乘的判獎方式 |
| Cascade | Cascade / Tumble | 中獎消除後補位，持續連消直到無新中獎 |
| Wild | Wild | 百搭符號，可替代除 Bonus 外的符號 |
| Bonus | Bonus | 累積 Star Meter、觸發免費遊戲的特殊符號 |
| Mystery | Mystery Symbol | 神秘符號，Cascade 後全盤揭示為同一符號 |
| Star Meter | Star Meter | Bonus 集點器，集滿 3／4 顆觸發免費遊戲 |
| Mystery Random Event | Mystery Random Event | Base Game 停輪含 Mystery 時觸發的特殊狀態 |
| Expand Bomb | Expand Bomb | FG A 的開列符號，開列並加 3 場 |
| Multiplier Ladder | Multiplier Ladder | FG B 的倍數階梯機制 |
| Expanding Wild | Expanding Wild | FG C 的 Wild 向下擴展機制 |
| Gamble | Gamble | 賭升級版免費遊戲的選擇性玩法 |
| Feature Buy | Buy Feature | 直接購買免費遊戲功能 |

---

## 附錄 B. 已確認規格

* 盤面為 6 輪 × 4 列，4,096 Ways；FG A 擴列後最高 38,416 Ways。
* Base Bet 為 100。
* 三種 Free Game 初始場次採 **6 / 8 / 7**（FG A / FG B / FG C）。
* 三種 Free Game 的加場符號分別為 **+2 / +1 / +3** Free Spin。
* Free Game 場次硬上限為 **50 場**。
* FG B 倍數階梯共 36 階，`1x` 起、`500x` 封頂。
* FG B 到達 15x / 20x / 50x / 100x / 500x 分別加 **3 / 1 / 2 / 2 / 2** 場。
* FG A 升級版起始 4 顆 Mystery；FG B 升級版初始 9 場；FG C 升級版起始 10x。
* Mystery 揭示範圍為 10、J、Q、K、A、Pic A–E 共 10 種，權重相同。
* Buy Feature 價格為 **80x Bet**，取得一般版並可 Gamble。
* Base Game 的 Wild 出現在 R2–R6；FG C 的 Wild 出現在 R2–R5。
* Base Game 一局最多累積 4 顆 Bonus 符號。

---

## 待確認事項

| 編號 | 章節 | 待確認內容 |
| --- | --- | --- |
| 1 | §1、§9.7.2 | **最大派彩倍率**：主模型檔標示 Max Win 96,000 credits / 9,600x，但 `DongDongKongData.xlsx` 的 RTP_94 / RTP_96 標示 100,000 / x10,000。需確認正式送驗值，以及達上限後的處理方式（強制結束 FG？截斷派彩？） |
| 2 | §3.1 | **高分符號的實際外觀**：模型檔僅有 `Pic A` ～ `Pic E` 的代號，無符號美術名稱或說明。需補中文外觀描述 |
| 3 | §5.7、§9.5.3 | **Bonus 符號的消除條件**：原文 `Bonus symbol will not be destroyed except when there is win in other normal symbols.` 語意不明。是否為「Bonus 本身不會因中獎被消除，但同盤有其他一般符號中獎時會一併消失」？ |
| 4 | §6.4、§9.5.4 | **Star Meter 的累積範圍與歸零時點**：4 顆上限是「一次付費 Spin（含所有 Cascade）」內，還是「單次停輪」內？Star Meter 是否跨局累積？何時歸零？ |
| 5 | §7.4、§9.6.5 | **FG B / FG C 的倍數是否跨局保留**：FG B 明確寫「每一場新 Spin 前進一階」故為累積；FG C 只寫「起始 1x、每顆 Wild +1x」，未說明每局是否重置。升級版起始 10x 之後如何累加亦未說明 |
| 6 | §7.2、§9.3.7 | **FG A 的 Mystery 跨局落底處理**：若上一局有 5 顆 Mystery、新盤面該輪僅 4 格，超出部分如何處理？ |
| 7 | §7.6 | **Free Game 期間是否可由 Bonus 再次觸發 Free Game**：模型檔與設定檔皆未見 FG 內 Bonus 的處理規則 |
| 8 | §7.2 | **Expand Bomb 加場數的參數來源**：規格文字寫 `+3 free spins`，但設定檔 `addRoundPerHit[0] = 2`（FG A 的加場符號為 +2）。Bomb 的 +3 場是寫死在程式或另有參數？ |
| 9 | §6.2 | **Base Game 的 Mystery 出現輪位**：FG A 明確寫 R2–R5，Base Game 僅寫「可出現在任何主遊戲 Spin」，未指明輪位 |
| 10 | 全篇 | **是否有 Jackpot 彩金池**：設定檔存在 `bonusGameSetting.poolCount = 4` 與兩組 `poolInitValue`（一般 ／ Buy 進場），但規格文件完全未提；`RTP_Summary` 亦無彩金 RTP 拆解。若實際啟用，需補彩金章節與 Bonus RTP / Link RTP / Total RTP |
| 11 | §1 | **押注檔位**：設定檔有 30 檔押注（1 ～ 25,000）與上限 25,000 / 50,000，但規格文件未載明是否為正式規格 |
| 12 | 全篇 | **Top-Up Game / Double Game**：設定檔存在完整的 `topUpGameSetting`（3×5、15 符號、9 組輪帶）與 `doubleGameSetting`，規格文件完全未提。需確認是否為本作啟用的機制 |
