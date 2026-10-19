# Candy Rush 2 Game Help Draft（發想）

這份 md 是「急速糖果 2 / Candy Rush 2」發想 demo 的 Help 稿，機制以 `game_rule.md` 為準。

## Game Meta

| Field | Value |
| --- | --- |
| game_id | ⏳（發想） |
| parsheet_id | ⏳（發想） |
| name_zh | 急速糖果 2 |
| name_en | Candy Rush 2 |
| game_type | Video Slot - Cluster Pay / Cascade / Position Multiplier |

---

## PAYTABLE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 符號賠付值 | SYMBOL PAYOUT VALUES |

### SCATTER SYMBOL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 散佈符號 | SCATTER SYMBOL |
| 規則說明 | 所有連消結束後，最終盤面出現 {3} 個或以上 [C1]，將觸發免費遊戲；同一輪同時最多 {1} 顆 [C1]。 | AFTER ALL CASCADES ARE COMPLETE, {3} OR MORE [C1] ON THE FINAL BOARD TRIGGER THE FREE GAME. AT MOST {1} [C1] PER REEL. |

### 賠率表

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 賠率表 | PAYTABLE |

| 中文欄 | 中文欄 | 中文欄 |
| --- | --- | --- |
| [M1] 4 - 100 | [M1] 8 - 750 | [M1] 10+ - 15000 |
| [M2] 4 - 75 | [M2] 8 - 500 | [M2] 10+ - 10000 |
| [M3] 4 - 50 | [M3] 8 - 450 | [M3] 10+ - 6000 |
| [M4] 4 - 40 | [M4] 8 - 350 | [M4] 10+ - 4000 |
| [M5] 4 - 30 | [M5] 8 - 250 | [M5] 10+ - 3000 |
| [M6] 4 - 25 | [M6] 8 - 150 | [M6] 10+ - 2500 |

---

## CLUSTER PAY FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 群集派彩 | CLUSTER PAY |
| 規則說明 | 盤面為 {5×5}；相同符號以上下左右相鄰連結達 {4} 個以上即中獎，每個群集各自計獎；同一符號同時有多組群集時，每一組都會計獎。 | THE GAME USES A {5×5} GRID. {4} OR MORE IDENTICAL SYMBOLS CONNECTED HORIZONTALLY OR VERTICALLY FORM A WINNING CLUSTER. EACH CLUSTER PAYS SEPARATELY, INCLUDING MULTIPLE CLUSTERS OF THE SAME SYMBOL. |
| 規則說明 | 群集中獎後，盤面上所有相同符號會一併消除；得分只以相連的群集數量計算，連帶消除的符號不另計獎。 | WHEN A CLUSTER WINS, ALL IDENTICAL SYMBOLS ON THE BOARD ARE REMOVED. ONLY THE CONNECTED CLUSTER PAYS; THE OTHER REMOVED SYMBOLS DO NOT PAY. |

---

## CASCADING FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 連消特色 | CASCADING FEATURE |
| 規則說明 | 中獎群集消除後，同一輪上方符號向下補位，空缺由新符號自盤面上方掉入，再次判定，直到沒有新的中獎群集。 | AFTER A WIN, WINNING SYMBOLS ARE REMOVED, SYMBOLS ABOVE FALL DOWN AND NEW SYMBOLS DROP IN FROM THE TOP. EVALUATION REPEATS UNTIL NO NEW CLUSTER IS FORMED. |

---

## POSITION MULTIPLIER FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 位置倍數 | POSITION MULTIPLIER |
| 規則說明 | 每格每發生一次消除，該位置倍數 +{1}（第 1 次為 x1、第 2 次為 x2，依此類推）。 | EACH TIME A POSITION IS PART OF A WIN, ITS MULTIPLIER INCREASES BY {1} (x1, x2, x3 AND SO ON). |
| 規則說明 | 不論在盤面哪個位置消除，每個群集的得分 = 群集賠率 × 押注 × 全盤所有位置倍數的總和；總和為 {0} 時以 x{1} 計。 | WHEREVER A WIN OCCURS, EACH CLUSTER WIN = CLUSTER PAY × BET × THE SUM OF ALL POSITION MULTIPLIERS ON THE BOARD. A SUM OF {0} COUNTS AS x{1}. |
| 規則說明 | 一般遊戲中，位置倍數於每次旋轉開始時歸零；免費遊戲期間整場保留。 | POSITION MULTIPLIERS RESET AT THE START OF EACH BASE GAME SPIN AND PERSIST FOR THE WHOLE FREE GAME SESSION. |

---

## FREE GAME FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 免費遊戲特色 | FREE GAME FEATURE |
| 規則說明 | {3、4、5、6、7} 個 [C1] 分別獲得 {10、12、15、20、30} 次免費旋轉。 | {3, 4, 5, 6 OR 7} [C1] AWARD {10, 12, 15, 20 OR 30} FREE SPINS RESPECTIVELY. |
| 規則說明 | 免費遊戲中再次出現 {3} 個或以上 [C1]，依相同規則追加免費旋轉。 | {3} OR MORE [C1] DURING THE FREE GAME AWARD ADDITIONAL FREE SPINS BY THE SAME RULE. |

---

## EXTRA BET

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 額外押注 | EXTRA BET |
| 規則說明 | 額外押注的費用為目前投注的 {10} 倍，派彩仍以原始投注計算。 | EXTRA BET COSTS {10} TIMES THE CURRENT BET. WINS ARE STILL CALCULATED ON THE ORIGINAL BET. |
| 規則說明 | 該次旋轉開場時，盤面隨機 {3} 個位置出現 {5、6、7、8、9、10、15、20、25、30、35、40、45 或 50} 的倍數底板，第一次消除即計入全盤倍數和。 | AT THE START OF THE SPIN, {3} RANDOM POSITIONS RECEIVE A {5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45 OR 50} MULTIPLIER PLATE THAT COUNTS TOWARD THE BOARD MULTIPLIER SUM FROM THE FIRST WIN. |

---

## BUY FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 購買特色 | BUY FEATURE |
| 規則說明 | 購買特色的費用為目前投注的 {100} 倍（發想暫定），直接進入 {10} 次免費遊戲。 | BUY FEATURE COSTS {100} TIMES THE CURRENT BET (DRAFT VALUE) AND ENTERS THE FREE GAME WITH {10} FREE SPINS. |

---

## GAME RULE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 遊戲規則 | GAME RULES |
| 規則說明 | 本頁為發想草稿：符號權重與購買價格為示意假值，理論返還率尚未定義。 | THIS IS A CONCEPT DRAFT: SYMBOL WEIGHTS AND BUY PRICE ARE PLACEHOLDER VALUES. THEORETICAL RTP IS NOT YET DEFINED. |
