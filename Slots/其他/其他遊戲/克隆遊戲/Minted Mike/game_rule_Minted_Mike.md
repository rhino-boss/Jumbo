# Minted Mike 遊戲規則說明

> 文件版本：v0.1（草稿）
> 對標競品：Hacksaw Gaming Minted Mike
> 撰寫日期：2026-10-21

---

## §1. 遊戲基本資訊

| 項目 | 說明 |
| --- | --- |
| Game ID | —（競品，無內部 Game ID） |
| PARsheet ID | —（競品，無 PARsheet） |
| 遊戲中文名稱 | ⏳ |
| 遊戲英文名 | Minted Mike |
| 遊戲類型 | 26 Lines / Sticker 觸發機制（Hot Line 乘數線、Wild 噴漆、FS 貼紙滾輪）/ Respin / 三階段可升級 Free Spins |
| 盤面規格 | 5 Reels × 4 Rows（共 20 格） |
| 中獎方式 | Line Game |
| 押注模式 | Normal Bet、FeatureSpins（BonusHunt／Spray the System）、Buy Feature（Steezy Skater／Ink the City） |

補充設定：

| 項目 | 說明 |
| --- | --- |
| 線數 | 26 條固定線 |
| Bet 範圍 | 0.10 ～ 2,000.00（Feature 購買可超過此上限） |
| 理論 RTP | 96.31%（Normal Bet） |
| Max Win | 5,000x bet（所有模式） |
| 波動性 | Medium |

---

## §2. 盤面結構

### 2.1 盤面示意圖

```
        R1    R2    R3    R4    R5
      ┌─────┬─────┬─────┬─────┬─────┐
Row 0 │     │     │     │     │     │
      ├─────┼─────┼─────┼─────┼─────┤
Row 1 │     │     │     │     │     │
      ├─────┼─────┼─────┼─────┼─────┤
Row 2 │     │     │     │     │     │
      ├─────┼─────┼─────┼─────┼─────┤
Row 3 │     │     │     │     │     │
      └─────┴─────┴─────┴─────┴─────┘
  盤面上方：乘數列（Multiplier Bar）
    左＝粉紅 Hot Line Multiplier、中＝綠色 FS 貼紙滾輪、右＝藍色噴漆
```

### 2.2 Reel／Row 表

| Reel | Row 數 | 位置索引 |
| --- | ---: | --- |
| R1 | 4 | 0–3 |
| R2 | 4 | 0–3 |
| R3 | 4 | 0–3 |
| R4 | 4 | 0–3 |
| R5 | 4 | 0–3 |

### 2.3 得分方向

- 26 條固定線，自 R1 起算、由左至右相鄰輪連續同符號（含替代符號）即得分，最少 3 連。
- 每條線只取最長連線的最高賠率。
- 單線得分 ＝ 賠率（× bet）×（該線為 Hot Line 時乘上 Hot Line Multiplier，否則 ×1）。
- 單局得分 ＝ 所有線得分加總。

### 2.4 線表（Row 索引，0 為最上列）

| 線 | R1 | R2 | R3 | R4 | R5 | 線 | R1 | R2 | R3 | R4 | R5 |
| ---: | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | 0 | 0 | 0 | 0 | 0 | 14 | 2 | 1 | 0 | 1 | 2 |
| 2 | 1 | 1 | 1 | 1 | 1 | 15 | 0 | 1 | 1 | 1 | 0 |
| 3 | 2 | 2 | 2 | 2 | 2 | 16 | 1 | 2 | 2 | 2 | 1 |
| 4 | 3 | 3 | 3 | 3 | 3 | 17 | 2 | 3 | 3 | 3 | 2 |
| 5 | 0 | 1 | 0 | 1 | 0 | 18 | 3 | 2 | 2 | 2 | 3 |
| 6 | 1 | 2 | 1 | 2 | 1 | 19 | 2 | 1 | 1 | 1 | 2 |
| 7 | 2 | 3 | 2 | 3 | 2 | 20 | 1 | 0 | 0 | 0 | 1 |
| 8 | 1 | 0 | 1 | 0 | 1 | 21 | 0 | 0 | 1 | 0 | 0 |
| 9 | 2 | 1 | 2 | 1 | 2 | 22 | 1 | 1 | 2 | 1 | 1 |
| 10 | 3 | 2 | 3 | 2 | 3 | 23 | 2 | 2 | 3 | 2 | 2 |
| 11 | 0 | 1 | 2 | 1 | 0 | 24 | 3 | 3 | 2 | 3 | 3 |
| 12 | 1 | 2 | 3 | 2 | 1 | 25 | 2 | 2 | 1 | 2 | 2 |
| 13 | 3 | 2 | 1 | 2 | 3 | 26 | 1 | 1 | 0 | 1 | 1 |

### 2.5 補牌流程

- 無消除（非 Cascade）。
- 唯一的重轉為 Pink Marker 觸發後的 **Respin**：Hot Lines 保留在盤面上，全盤 20 格重新落下新符號後重新判獎；Respin 中不會出現任何 Sticker 符號（見 §5.2）。

---

## §3. 符號類別

### 3.1 一般符號

| 代號 | 符號 |
| --- | --- |
| M1 | 金色錢字 |
| M2 | 球鞋 |
| M3 | 貼紙包 |
| M4 | 飲料罐 |
| A | 塗鴉字 A |
| K | 塗鴉字 K |
| Q | 塗鴉字 Q |
| J | 塗鴉字 J |

- A／K／Q／J 賠率相同。

### 3.2 特殊符號

| 代號 | 符號 |
| --- | --- |
| C1 | 藍色貼紙（Blue Sticker） |
| C2 | 粉紅貼紙（Pink Sticker） |
| C3 | 綠色貼紙（Green Sticker） |
| WW | Wild（藍色塗鴉 W） |
| C4 | FS（Scatter） |
| C5 | FS Upgrade（黃色箭頭） |

- **WW Wild**：替代所有一般符號；本身有 5 連賠率（見 §4）；只會由 Blue Spray Can 加到盤面上（見 §5.3），落在一般符號之上覆蓋該格。
- **C1／C2／C3 Sticker**：自然落下；替代所有一般符號（可參與連線）；落下時有機率啟動對應機制：C1 → Blue Spray Can、C2 → Pink Marker、C3 → Green Sticker Roll。同一局每種顏色最多 1 個。
- **C4 FS／C5 FS Upgrade**：只會由 Green Sticker Roll 加到盤面上（見 §5.4），可落在一般符號與 C3 之上；不參與連線、無直接派彩；依數量觸發或升級 Free Spins。
- C5 不會出現在 TAG AND DASH；Spray the System FeatureSpins 模式中 C4 不會出現。

---

## §4. 賠率表（Pay Table）

倍率口徑：× bet（總押注），單一條線的賠率。

| 符號 | 3 連 | 4 連 | 5 連 |
| --- | ---: | ---: | ---: |
| WW Wild | — | — | 50x |
| M1 金色錢字 | 1.5x | 5x | 20x |
| M2 球鞋 | 1x | 3x | 10x |
| M3 貼紙包 | 0.8x | 2x | 7x |
| M4 飲料罐 | 0.5x | 1.5x | 5x |
| A | 0.2x | 0.5x | 1x |
| K | 0.2x | 0.5x | 1x |
| Q | 0.2x | 0.5x | 1x |
| J | 0.2x | 0.5x | 1x |

- C4／C5／C2／C1／C3 無賠率。

---

## §5. 核心特色

### 5.1 Sticker 觸發順序

- C2／C1／C3 落下時各自獨立判定是否啟動機制。
- 同一局多個機制同時啟動時，依序執行：**Pink Marker → Blue Spray Can → Green Sticker Roll**。
- Sticker 的啟動動畫不影響機制是否啟動（表演與結果無關）。

### 5.2 Pink Marker（Hot Lines）

- 時機：C2 落下並啟動，於本局得分**派彩後**執行。
- 從 26 條線中隨機挑選下列數量畫成 Hot Lines：2、3、4、5、6、7、10、12、15、20、26 條。盤面同時最多 26 條。
- 所有 Hot Lines 共用一個 Hot Line Multiplier（顯示於上方乘數列粉紅區），值從下列抽出：2x、3x、4x、5x、6x、7x、8x、9x、10x、15x、20x、25x、50x、100x、150x、183x。
- 畫線後觸發 1 次 **Respin**：全盤重新落下，Respin 中不會落下 Sticker。
- Respin 中落在 Hot Line 上的中獎線，該線得分 × Hot Line Multiplier；非 Hot Line 的中獎線照常計分。
- Base Game 中 Hot Lines 與乘數於本局結束後清除（FG 中的保留規則見 §6.3）。

| 參數 | 值 |
| --- | --- |
| 首次畫線數 | {2, 3, 4, 5, 6, 7, 10, 12, 15, 20, 26} ⏳ 權重 |
| Hot Line Multiplier | {2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 50, 100, 150, 183} ⏳ 權重 |
| Respin 次數 | 1 |

### 5.3 Blue Spray Can（Wild 噴漆）

- 時機：C1 落下並啟動，於本局得分**判獎前**執行。
- 隨機在盤面加入下列數量的 WW Wild：3、4、5、6、7、8、9、10、15、20 個（覆蓋原有一般符號）。
- WW 只會透過此機制出現。

| 參數 | 值 |
| --- | --- |
| 加入 Wild 數 | {3, 4, 5, 6, 7, 8, 9, 10, 15, 20} ⏳ 權重 |
| 可覆蓋位置 | 一般符號格（⏳ 是否可覆蓋 Sticker） |

### 5.4 Green Sticker Roll（FS 貼紙滾輪）

- 時機：C3 落下並啟動，於本局得分**派彩後**執行。
- 在盤面加入 C4 FS 與 C5 FS Upgrade（可覆蓋一般符號與 C3）。
- 依加入結果判定 Free Spins（Base Game）：

| 條件 | 獲得 |
| --- | --- |
| C4 ≥ 8 | STEEZY SKATER |
| C4 ≥ 7 且 C5 = 1 | INK THE CITY |
| C4 ≥ 6 且 C5 = 2 | TAG AND DASH（Hidden Epic Bonus） |

- 免費局數 ＝ C4 數 ＋ C5 數（每個 1 局），範圍 8–20 局。
- C4 + C5 未達上表門檻時不觸發 FG。⏳ 是否可能未達門檻
- C4／C5 只會透過此機制出現。

---

## §6. 免費遊戲（Free Spins / Free Game, FG）

三種 FG，皆由 Base Game 的 Green Sticker Roll 觸發（§5.4），亦可在 FG 內升級。

### 6.1 觸發

| FG | 觸發條件 | 初始局數 |
| --- | --- | --- |
| STEEZY SKATER | C4 ≥ 8 | 8–20 |
| INK THE CITY | C4 ≥ 7 ＋ C5 × 1 | 8–20 |
| TAG AND DASH | C4 ≥ 6 ＋ C5 × 2 | 8–20 |

### 6.2 STEEZY SKATER

- 沿用 Base Game 所有機制（§5.2–§5.4），Hot Lines 每局結束後清除。
- C2／C1／C3 出現機率高於 Base Game。
- Green Sticker Roll 啟動時：追加局數 ＝ 落下的 C4 ＋ C5 數，範圍 8–20 局。
  - 落下 1 個 C5 → 升級為 INK THE CITY。
  - 落下 2 個 C5 → 升級為 TAG AND DASH。
  - 升級時，剩餘局數與本次追加局數一併帶入新 FG。

### 6.3 INK THE CITY

- 沿用 Base Game 機制，但 **Hot Lines 為累進式**：
  - Hot Lines 保留在原位置直到 FG 結束，共用一個累進的 Hot Line Multiplier。
  - 每次 Pink Marker 啟動：盤面既有 Hot Lines 啟動，並新增 Hot Lines；同時共用乘數**加上**一個隨機值（2x、3x、4x、5x、6x、7x、8x、9x、10x、15x、20x、25x、50x、100x、150x、183x）。
  - 第 2 次起每次新增 1–24 條 Hot Lines（上限 26 條）。
  - 盤面已滿 26 條時再啟動：只增加乘數，不新增線。
- Green Sticker Roll 啟動時：追加局數 ＝ 落下的 C4 ＋ C5 數，範圍 8–20 局；落下 C5 → 升級為 TAG AND DASH，Hot Lines、共用乘數、剩餘局數連同追加局數一併帶入。

| 參數 | 值 |
| --- | --- |
| 首次畫線數 | 同 §5.2 ⏳ |
| 後續每次新增線數 | 1–24 ⏳ 權重 |
| 乘數累加值 | {2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 50, 100, 150, 183} ⏳ 權重 |
| 乘數初始值 | ⏳（首次啟動前為 0 或 1） |

### 6.4 TAG AND DASH（Hidden Epic Bonus）

- 沿用 INK THE CITY 全部規則。
- 每局保證落下 1 個 Sticker（C2／C1／C3 其一）。⏳ 顏色權重
- C5 不會出現；Green Sticker Roll 啟動時追加局數 ＝ 落下的 C4 數，範圍 8–20 局。
- 不可購買，只能由觸發或升級進入。

### 6.5 Retrigger 與結束

- FG 內 Green Sticker Roll 每次啟動皆追加 8–20 局（見 6.2–6.4），無局數上限。⏳
- 局數用完即結束，回到 Base Game。
- FG 中累計得分達 5,000x 時立即結束，剩餘局數作廢。

---

## §7. 核心遊戲流程（Base Game）

1. 扣除押注（Normal Bet ＝ 1x bet；FeatureSpins 依 §8.1 扣款）。
2. 5×4 全盤落下一般符號與 C2／C1／C3（每色最多 1 個）。
3. 判定各 Sticker 是否啟動機制。
4. 若 Blue Spray Can 啟動：加入 3–20 個 WW Wild。
5. 依 26 條線判獎並派彩。
6. 若 Pink Marker 啟動：畫上 Hot Lines 與乘數 → Respin（無 Sticker）→ 依 Hot Lines 規則判獎並派彩。
7. 若 Green Sticker Roll 啟動：加入 C4／C5，依 §5.4 判定是否進入 FG。
8. 本局總得分 ＝ 步驟 5 ＋ 步驟 6，上限 5,000x。
9. 若觸發 FG，進入 §6；否則本局結束，清除 Hot Lines。

> ⏳ 規則說明「Pink 先、Blue 次、Green 最後」的執行順序，與「Pink 於派彩後、Blue 於派彩前」的時機描述並存；Blue 加入 Wild 是作用在首轉還是 Respin 結果需再確認。

---

## §8. 押注模式

### 8.1 Extra Bet（FeatureSpins）

FeatureSpins 啟用後每局固定加價，持續有效直到玩家按 DISABLE 關閉。

| 模式 | 每局花費 | 效果 | RTP |
| --- | ---: | --- | ---: |
| BONUSHUNT FEATURESPINS | 3x bet | 觸發 FG 機率為 Normal Bet 的 5 倍 | 96.25% |
| SPRAY THE SYSTEM FEATURESPINS | 60x bet | 每局保證落下 1 個 C2 與 1 個 C1，且保證至少 1 個機制啟動；C4 不會出現（不會觸發 FG） | 96.32% |

- 線賠率仍以 1x bet 計算。

### 8.2 Buy Feature

| 購買項目 | 價格 | 內容 | RTP |
| --- | ---: | --- | ---: |
| STEEZY SKATER | 50x bet | 直接進入 STEEZY SKATER，8 局以上 | 96.34% |
| INK THE CITY | 200x bet | 直接進入 INK THE CITY，8 局以上 | 96.33% |

- TAG AND DASH 不可購買。
- 購買價格可超過 Bet 上限 2,000.00。

---

## §9. 邊界 / 例外情境（Edge Cases）

### 9.1 Sticker

- 同一局同色 Sticker 最多 1 個；三色可同時出現。
- Sticker 落下但未啟動機制：仍作為替代符號參與判獎。
- Pink Marker 的 Respin 中不落下任何 Sticker，Respin 不會再連鎖觸發機制。

### 9.2 Hot Lines

- 畫 26 條時全部線皆為 Hot Line。
- INK THE CITY／TAG AND DASH 盤面已有 26 條 Hot Lines 時，Pink Marker 只累加乘數。
- 同一條線同時中多種連線，只取該線最高賠率 × 乘數一次。

### 9.3 Free Spins

- C4 ＋ C5 合計恰為 8 為最少局數；上限 20。
- STEEZY SKATER 中同時落下 2 個 C5：直接升級至 TAG AND DASH（不經 INK THE CITY）。
- 升級後所有累積（局數、Hot Lines、乘數）完整帶入。
- TAG AND DASH 中不會再出現 C5。

### 9.4 Max Win

- 單局（含 FG 全程）累計達 5,000x：顯示 Max Win 訊息，立即結束並派彩，剩餘 FG 局數與機制作廢。

---

## 附錄 A. 詞彙對照

| 英文 | 中文 |
| --- | --- |
| Pink Marker | 粉紅麥克筆（Hot Lines 機制） |
| Hot Line | 熱線（乘數線） |
| Hot Line Multiplier | 熱線乘數 |
| Blue Spray Can | 藍色噴漆（Wild 機制） |
| Green Sticker Roll | 綠色貼紙滾輪（FS 機制） |
| FeatureSpins | 特色旋轉（持續加價模式） |
| STEEZY SKATER | 滑板 FG（一階） |
| INK THE CITY | 塗滿全城 FG（二階） |
| TAG AND DASH | 塗鴉快閃 FG（隱藏三階） |

---

## 待確認事項

1. 遊戲中文名稱。
2. 三種 Sticker 的出現率與各自的啟動機率（Base／各 FG／FeatureSpins）。
3. Pink Marker 首次畫線數、Hot Line Multiplier、INK THE CITY 後續新增線數（1–24）與乘數累加值的權重。
4. Blue Spray Can 的 Wild 數權重；Wild 是否可覆蓋 Sticker。
5. Blue Spray Can 作用在首轉或 Pink Respin 後的盤面（§7 執行順序）。
6. Green Sticker Roll 的 C4／C5 數量分布；是否存在加入後未達觸發門檻的情況。
7. INK THE CITY 乘數初始值（首次啟動是「設定為」還是「累加自 0」）。
8. TAG AND DASH 保證 Sticker 的顏色權重。
9. FG 內追加局數是否有總局數上限。
10. 各押注模式的轉輪表。
