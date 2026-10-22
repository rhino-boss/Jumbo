# 101015 Game Help Draft

這份 md 是 `文件/101015_Help.xlsx` 的前置確認稿。
之後若要重產 xlsx，應先確認並修改這份 md，再轉成結構化 spec / xlsx。
底稿：Lucky Ace（101003）企劃書 `7.Help`；格式比照 H027／H028 的 `game_help_draft.md`；規則以 `game_rule.md` 為準。

## Game Meta

| Field | Value |
| --- | --- |
| game_id | 101015 |
| parsheet_id | H0451 |
| name_zh | 超級鑽石 |
| name_en | Super Diamond |
| game_type | Video Slot - 1,024 Ways / Cascade |

---

## PAYTABLE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 符號賠付值 | SYMBOL PAYOUT VALUES |
| 規則說明 | ▪ 所有符號必須由最左至右連續出現，方可獲獎。 | ▪ ALL WINS MUST BE ON CONSECUTIVE REELS FROM LEFTMOST TO RIGHT. |

### WILD SYMBOL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 百搭符號 | WILD SYMBOL |
| 規則說明 | ▪ [WW][W2] 可替代除 [C1] 以外的所有符號。 | ▪ [WW][W2] SUBSTITUTE FOR ALL SYMBOLS EXCEPT [C1]. |
| 規則說明 | ▪ [WW][W2] 只會由參與中獎的金框符號轉換產生。 | ▪ [WW][W2] ARE CREATED ONLY FROM GOLDEN FRAMED SYMBOLS THAT ARE PART OF A WINNING COMBINATION. |

### SCATTER SYMBOL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 免費遊戲獎賞 | FREE GAME BONUS |
| 規則說明 | ▪ 所有連消結束後，若最終盤面出現 {3} 個以上 [C1]，即可觸發免費遊戲特色，獲得 {10} 場免費遊戲。 | ▪ AFTER ALL CASCADES END, {3} OR MORE [C1] ON THE FINAL REELS WILL TRIGGER THE FREE GAME FEATURE AND AWARD {10} FREE SPINS. |

### 賠率表

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 賠率表 | PAYTABLE |

繁中：

| 符號 | {5} 連 | {4} 連 | {3} 連 |
| --- | ---: | ---: | ---: |
| [M1] | {125} | {75} | {25} |
| [M2] | {100} | {60} | {20} |
| [M3] | {75} | {45} | {15} |
| [M4] | {50} | {30} | {10} |
| [A] | {25} | {15} | {5} |
| [K] | {25} | {15} | {5} |
| [Q] | {15} | {10} | {5} |
| [J] | {15} | {10} | {5} |

英文：

| SYMBOL | {5} OF A KIND | {4} OF A KIND | {3} OF A KIND |
| --- | ---: | ---: | ---: |
| [M1] | {125} | {75} | {25} |
| [M2] | {100} | {60} | {20} |
| [M3] | {75} | {45} | {15} |
| [M4] | {50} | {30} | {10} |
| [A] | {25} | {15} | {5} |
| [K] | {25} | {15} | {5} |
| [Q] | {15} | {10} | {5} |
| [J] | {15} | {10} | {5} |

---

## CASCADING FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 消除特色 | CASCADING FEATURE |
| 規則說明 | ▪ 遊戲中若達成連線，除金框符號外的中獎符號將被消除，並在原位置補上新的符號。 | ▪ ALL SYMBOLS IN WINNING COMBINATIONS, EXCEPT GOLDEN FRAMED SYMBOLS, WILL BE REMOVED AND NEW SYMBOLS WILL FILL THE EMPTY POSITIONS IN PLACE. |
| 規則說明 | ▪ 消除特色會持續發生，直到沒有新的連線為止。 | ▪ THE FEATURE CONTINUES UNTIL THERE ARE NO NEW WINNING COMBINATIONS. |

---

## GOLDEN FRAMED FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 金框符號特色 | GOLDEN FRAMED FEATURE |
| 規則說明 | ▪ 金框符號只會出現在第 {2}、{3}、{4} 輪。 | ▪ GOLDEN FRAMED SYMBOLS APPEAR ON REELS {2}, {3} AND {4} ONLY. |
| 規則說明 | ▪ 金框符號與原符號的賠率相同。 | ▪ GOLDEN FRAMED SYMBOLS PAY THE SAME AS THEIR ORIGINAL SYMBOLS. |
| 規則說明 | ▪ 金框符號參與中獎時不會被消除，而是在原位置隨機轉換為以下兩種模式之一。 | ▪ WHEN A GOLDEN FRAMED SYMBOL IS PART OF A WINNING COMBINATION, IT IS NOT REMOVED AND RANDOMLY TURNS INTO ONE OF THE FOLLOWING TWO MODES AT ITS ORIGINAL POSITION. |
| 規則說明 | ▪ 第一種模式：在原位置變成一個 [WW]。 | ▪ FIRST MODE: THE GOLDEN FRAMED SYMBOL TURNS INTO A [WW]. |
| 規則說明 | ▪ 第二種模式：在原位置變成一個 [W2]，並隨機複製 {2}～{4} 個 [WW] 取代第 {2}～{5} 輪的其他符號（不會取代 [C1] 與百搭符號）。 | ▪ SECOND MODE: THE GOLDEN FRAMED SYMBOL TURNS INTO A [W2] AND REPLICATES {2} TO {4} [WW] THAT RANDOMLY REPLACE OTHER SYMBOLS ON REELS {2} TO {5} ([C1] AND WILD SYMBOLS ARE NOT REPLACED). |

---

## MULTIPLIER WILD FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 倍數百搭特色 | MULTIPLIER WILD FEATURE |
| 規則說明 | ▪ 金框符號轉換出的 [WW][W2] 有機會帶有 X{2}、X{3} 或 X{5} 倍數。 | ▪ [WW][W2] TRANSFORMED FROM GOLDEN FRAMED SYMBOLS MAY CARRY AN X{2}, X{3} OR X{5} MULTIPLIER. |
| 規則說明 | ▪ [W2] 複製出的 [WW] 帶有與該 [W2] 相同的倍數。 | ▪ [WW] REPLICATED BY A [W2] CARRY THE SAME MULTIPLIER AS THAT [W2]. |
| 規則說明 | ▪ 每次連線時，本次中獎並被消除的帶倍數百搭符號，其倍數會相加，再乘上當次的連消倍數，最後作用於本次所有中獎組合的得分。 | ▪ ON EACH WIN, THE MULTIPLIERS OF ALL MULTIPLIER WILDS THAT ARE PART OF THE WIN AND REMOVED ARE ADDED TOGETHER, MULTIPLIED BY THE CURRENT CASCADE MULTIPLIER, AND APPLIED TO ALL WINNING COMBINATIONS OF THAT WIN. |
| 規則說明 | ▪ 本次中獎沒有帶倍數百搭符號時，只乘上連消倍數。 | ▪ WITHOUT MULTIPLIER WILDS IN THE WIN, ONLY THE CASCADE MULTIPLIER APPLIES. |
| 規則說明 | ▪ 未參與中獎的帶倍數百搭符號會保留在盤面上，直到參與中獎時才計入。 | ▪ MULTIPLIER WILDS THAT ARE NOT PART OF A WIN STAY ON THE REELS AND COUNT ONLY WHEN THEY ARE PART OF A LATER WIN. |

---

## CASCADE MULTIPLIER FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 連消倍數特色 | CASCADE MULTIPLIER FEATURE |
| 規則說明 | ▪ 每次旋轉開始時，連消倍數為 X{1}。 | ▪ AT THE START OF EACH SPIN, THE CASCADE MULTIPLIER IS X{1}. |
| 規則說明 | ▪ 每次消除後若再達成連線，連消倍數依序提升為 X{2}、X{3}、X{5}、X{10}。 | ▪ EACH TIME A NEW WINNING COMBINATION OCCURS AFTER A CASCADE, THE CASCADE MULTIPLIER INCREASES TO X{2}, X{3}, X{5} AND X{10} IN ORDER. |
| 規則說明 | ▪ 連消倍數達到 X{10} 後維持不變，直到本次旋轉結束。 | ▪ ONCE THE CASCADE MULTIPLIER REACHES X{10}, IT STAYS AT X{10} UNTIL THE SPIN ENDS. |

---

## FREE GAME FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 免費遊戲特色 | FREE GAME FEATURE |
| 規則說明 | ▪ 所有連消結束後，若最終盤面出現 {3} 個以上 [C1]，即可獲得 {10} 場免費遊戲。 | ▪ AFTER ALL CASCADES END, {3} OR MORE [C1] ON THE FINAL REELS AWARD {10} FREE SPINS. |
| 規則說明 | ▪ 在免費遊戲中，每次旋轉的連消結束後，若最終盤面出現 {3} 個以上 [C1]，可再獲得 {5} 場免費遊戲，最多可獲得 {50} 場免費遊戲。 | ▪ DURING THE FREE GAME, {3} OR MORE [C1] ON THE FINAL REELS AFTER ALL CASCADES OF A SPIN AWARD {5} MORE FREE SPINS, UP TO A MAXIMUM OF {50} FREE SPINS. |

### CASCADE MULTIPLIER FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 連消倍數特色 | CASCADE MULTIPLIER FEATURE |
| 規則說明 | ▪ 免費遊戲每次旋轉開始時，連消倍數為 X{2}。 | ▪ AT THE START OF EACH FREE SPIN, THE CASCADE MULTIPLIER IS X{2}. |
| 規則說明 | ▪ 每次消除後若再達成連線，連消倍數依序提升為 X{4}、X{6}、X{10}、X{20}。 | ▪ EACH TIME A NEW WINNING COMBINATION OCCURS AFTER A CASCADE, THE CASCADE MULTIPLIER INCREASES TO X{4}, X{6}, X{10} AND X{20} IN ORDER. |
| 規則說明 | ▪ 連消倍數達到 X{20} 後維持不變，直到本次旋轉結束。 | ▪ ONCE THE CASCADE MULTIPLIER REACHES X{20}, IT STAYS AT X{20} UNTIL THE SPIN ENDS. |

---

## EXTRA BET

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 額外投注 | EXTRA BET |
| 規則說明 | ▪ 額外投注的扣款為 {2} × 您所選的基礎投注。 | ▪ EXTRA BET COSTS {2} × THE BASE BET YOU SELECT. |
| 規則說明 | ▪ 所有獎金仍依您所選的基礎投注計算。 | ▪ ALL WINS ARE STILL CALCULATED ON THE BASE BET YOU SELECT. |
| 規則說明 | ▪ 免費遊戲的觸發機率提升為一般投注的 {5} 倍。 | ▪ THE CHANCE TO TRIGGER THE FREE GAME FEATURE IS {5} TIMES THAT OF THE NORMAL BET. |

---

## BUY FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 購買特色 | BUY FEATURE |
| 規則說明 | ▪ 玩家可支付 {50}x 總投注，直接購買一次免費遊戲進場機會。 | ▪ BUY FEATURE CAN BE PURCHASED FOR {50}X TOTAL BET TO ENTER THE FREE GAME FEATURE DIRECTLY. |
| 規則說明 | ▪ 完成購買後，將直接觸發一次免費遊戲特色。 | ▪ COMPLETING THE PURCHASE WILL TRIGGER THE FREE GAME FEATURE DIRECTLY. |

---

## OP JACKPOT

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | OP JACKPOT | OP JACKPOT |
| 規則說明 | ▪ 在遊戲中，OP JACKPOT 特色由盤面上的 {1} 個或以上 [C1] 隨機觸發。 | ▪ OP JACKPOT FEATURE IS TRIGGERED RANDOMLY BY {1} OR MORE [C1] ON THE REELS. |
| 規則說明 | ▪ OP JACKPOT 特色會在畫面中出現 {12} 個 [幣]，其中包括 [GRAND]、[MAJOR]、[MINOR] 及 [MINI]。 | ▪ DURING OP JACKPOT FEATURE, THERE ARE {12} [COIN] WHICH CONSIST OF [GRAND], [MAJOR], [MINOR] AND [MINI]. |
| 規則說明 | ▪ 選擇 {1} 個 [幣] 以揭示 [GRAND]、[MAJOR]、[MINOR] 或 [MINI]。 | ▪ SELECT A [COIN] TO REVEAL [GRAND], [MAJOR], [MINOR], OR [MINI]. |
| 規則說明 | ▪ 當玩家獲得 {3} 個相同的 OP JACKPOT 特色符號，即可獲得該 OP JACKPOT 並結算總獎金。 | ▪ IF PLAYER GETS {3} SAME JACKPOT SYMBOLS WILL WIN THE JACKPOT AND CALCULATE TOTAL WINNINGS. |
| 規則說明 | ▪ [GRAND] 為連機累進彩金。單場遊戲中，投注選項選擇 {2.00} 以上即可解鎖 [GRAND]。 | ▪ [GRAND] IS LINKED PROGRESSIVE JACKPOT. IF THE SINGLE GAME BET OPTION IS {2.00} OR ABOVE, THE PLAYER WILL UNLOCK [GRAND]. |
| 規則說明 | ▪ [MAJOR] 為連機累進彩金。單場遊戲中，投注選項選擇 {2.00} 以上即可解鎖 [MAJOR]。 | ▪ [MAJOR] IS LINKED PROGRESSIVE JACKPOT. IF THE SINGLE GAME BET OPTION IS {2.00} OR ABOVE, THE PLAYER WILL UNLOCK [MAJOR]. |
| 規則說明 | ▪ [MINOR] 為紅利彩金，依照投注選項改變。 | ▪ [MINOR] WILL CHANGE IF THE PLAYER SELECTS DIFFERENT BET OPTION. |
| 規則說明 | ▪ [MINI] 為紅利彩金，依照投注選項改變。 | ▪ [MINI] WILL CHANGE IF THE PLAYER SELECTS DIFFERENT BET OPTION. |
| 規則說明 | ▪ 玩家投注越高，觸發 OP JACKPOT 特色的機會越高。 | ▪ THE HIGHER BET, THE HIGHER CHANCES TO TRIGGER OP JACKPOT FEATURE. |

---

## WAY GAME

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 最多路數 | MAXIMUM WAYS |
| 規則說明 | ▪ 本遊戲為 {5} 輪 × {4} 列盤面，相同符號須出現在由左至右連續相鄰的轉輪上方可獲獎。 | ▪ THE GAME USES {5} REELS × {4} ROWS. MATCHING SYMBOLS MUST APPEAR ON CONSECUTIVE ADJACENT REELS FROM LEFT TO RIGHT TO WIN. |
| 規則說明 | ▪ 遊戲設定 = 最多 {1,024} 路。 | ▪ GAME SETTING = {1,024} MAXIMUM WAYS. |
| 規則說明 | [走線圖- 1,024 MAX WAYS] | [走線圖- 1,024 MAX WAYS] |
| 規則說明 | [走線圖-3 OF A KIND PAYS 2 WAYS] | [走線圖-3 OF A KIND PAYS 2 WAYS] |
| 規則說明 | [走線圖-NO WIN] | [走線圖-NO WIN] |

---

## GAME RULE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 遊戲規則 | GAME RULES |
| 規則說明 | ▪ 選擇您想要玩的投注選項。 | ▪ SELECT BET OPTION YOU WISH TO PLAY. |
| 規則說明 | ▪ 所有中獎金額均乘以投注選項，除非是累積獎。 | ▪ ALL WINS ARE MULTIPLIED BY BET OPTION EXCEPT PROGRESSIVES BONUSES. |
| 規則說明 | ▪ 遊戲出現故障時，所有賠付與遊戲結果均視為無效。 | ▪ MALFUNCTION VOIDS ALL PAYS AND PLAYS. |
| 規則說明 | ▪ 若玩家在免費遊戲期間中斷連線，系統將自動完成該局結算，並將中獎金額加入餘額。 | ▪ IF THE PLAYER LOSES CONNECTION DURING THE FREE GAME FEATURE, THE SYSTEM WILL COMPLETE THE RESULT AUTOMATICALLY AND ADD ANY WINNINGS TO THE BALANCE. |
