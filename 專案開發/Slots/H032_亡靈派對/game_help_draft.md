# 101019 Game Help Draft

這份 md 是 `對外文件/101019_Help.xlsx` 的前置確認稿。
之後若要重產 xlsx，應先確認並修改這份 md，再轉成 xlsx。
底稿：超級鑽石（101015）`game_help_draft.md`；規則以 `game_rule.md` 為準；用語依 `專案需知/開發規範/Omniplay/數學文件規範.md` §1.3。
用語：金色符號／GOLDEN SYMBOL、倍數框／MULTIPLIER FRAME（與數學模型 `Source/H0321.xlsx` 的 Golden_Symbol_* 參數同名）。

## Game Meta

| Field | Value |
| --- | --- |
| game_id | 101019 |
| parsheet_id | H0321 |
| name_zh | 亡靈派對 |
| name_en | Calavera Party |
| game_type | Video Slot - 1,024 Ways / Cascade（掉落） / 倍數框 |

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
| 規則說明 | ▪ [WW] 可替代除 [C1] 以外的所有符號。 | ▪ [WW] SUBSTITUTES FOR ALL SYMBOLS EXCEPT [C1]. |
| 規則說明 | ▪ [WW] 只會由參與中獎的金色符號轉換產生。 | ▪ [WW] IS CREATED ONLY FROM GOLDEN SYMBOLS THAT ARE PART OF A WINNING COMBINATION. |

### SCATTER SYMBOL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 散佈符號 | SCATTER SYMBOL |
| 規則說明 | ▪ 所有連消結束後，若最終盤面出現 {3} 個或以上 [C1]，即可觸發免費遊戲特色。 | ▪ AFTER ALL CASCADES END, {3} OR MORE [C1] ON THE FINAL REELS WILL TRIGGER THE FREE GAME FEATURE. |

### 賠率表

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 賠率表 | PAYTABLE |

繁中：

| 符號 | {5} 連 | {4} 連 | {3} 連 |
| --- | ---: | ---: | ---: |
| [M1] | {250} | {150} | {50} |
| [M2] | {200} | {120} | {40} |
| [M3] | {150} | {90} | {30} |
| [M4] | {100} | {60} | {20} |
| [A] | {50} | {30} | {10} |
| [K] | {50} | {30} | {10} |
| [Q] | {25} | {15} | {5} |
| [J] | {25} | {15} | {5} |

英文：

| SYMBOL | {5} OF A KIND | {4} OF A KIND | {3} OF A KIND |
| --- | ---: | ---: | ---: |
| [M1] | {250} | {150} | {50} |
| [M2] | {200} | {120} | {40} |
| [M3] | {150} | {90} | {30} |
| [M4] | {100} | {60} | {20} |
| [A] | {50} | {30} | {10} |
| [K] | {50} | {30} | {10} |
| [Q] | {25} | {15} | {5} |
| [J] | {25} | {15} | {5} |

---

## CASCADING FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 消除特色 | CASCADING FEATURE |
| 規則說明 | ▪ 遊戲中若出現中獎組合，除金色符號外的中獎符號將被消除，上方的符號往下掉落，空位由新的符號補滿。 | ▪ ALL SYMBOLS IN WINNING COMBINATIONS, EXCEPT GOLDEN SYMBOLS, WILL BE REMOVED. THE SYMBOLS ABOVE DROP DOWN AND NEW SYMBOLS FILL THE EMPTY POSITIONS. |
| 規則說明 | ▪ 消除特色會持續發生，直到沒有新的中獎組合為止。 | ▪ THE FEATURE CONTINUES UNTIL THERE ARE NO NEW WINNING COMBINATIONS. |

---

## GOLDEN SYMBOL FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 金色符號特色 | GOLDEN SYMBOL FEATURE |
| 規則說明 | ▪ 金色符號只會出現在第 {2}、{3}、{4}、{5} 輪。 | ▪ GOLDEN SYMBOLS APPEAR ON REELS {2}, {3}, {4} AND {5} ONLY. |
| 規則說明 | ▪ 金色符號與原符號的賠率相同。 | ▪ GOLDEN SYMBOLS PAY THE SAME AS THEIR ORIGINAL SYMBOLS. |
| 規則說明 | ▪ 金色符號參與中獎時不會被消除，而是在原位置變成一個 [WW]。 | ▪ WHEN A GOLDEN SYMBOL IS PART OF A WINNING COMBINATION, IT IS NOT REMOVED AND TURNS INTO A [WW] AT ITS ORIGINAL POSITION. |
| 規則說明 | ▪ 若該位置沒有倍數框，會留下一個倍數框，初始倍數隨機為 X{1}、X{2}、X{3}、X{5}、X{10}、X{20}、X{30}、X{50} 或 X{100}。 | ▪ IF THERE IS NO MULTIPLIER FRAME AT THAT POSITION, A MULTIPLIER FRAME IS LEFT WITH A RANDOM STARTING MULTIPLIER OF X{1}, X{2}, X{3}, X{5}, X{10}, X{20}, X{30}, X{50} OR X{100}. |

---

## MULTIPLIER FRAME FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 倍數框特色 | MULTIPLIER FRAME FEATURE |
| 規則說明 | ▪ 倍數框固定在原位置，不會隨符號掉落移動。 | ▪ MULTIPLIER FRAMES STAY AT THEIR POSITIONS AND DO NOT MOVE WITH DROPPING SYMBOLS. |
| 規則說明 | ▪ 每次中獎的得分會乘上目前的累積倍數：盤面上所有倍數框的倍數加總再加 {1}。 | ▪ EACH WIN IS MULTIPLIED BY THE CURRENT ACCUMULATED MULTIPLIER: THE SUM OF ALL MULTIPLIER FRAMES ON THE REELS PLUS {1}. |
| 規則說明 | ▪ 每次中獎計分後，盤面上所有倍數框的倍數各 +{1}。 | ▪ AFTER EACH WIN IS SCORED, EVERY MULTIPLIER FRAME ON THE REELS GAINS +{1}. |
| 規則說明 | ▪ 基礎遊戲中，倍數框會保留在盤面上，直到沒有中獎組合為止。 | ▪ IN THE BASE GAME, MULTIPLIER FRAMES REMAIN ON THE REELS UNTIL NO WINNING COMBINATION OCCURS. |

---

## FREE GAME FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 免費遊戲特色 | FREE GAME FEATURE |
| 規則說明 | ▪ 所有連消結束後，若最終盤面出現 {3} 個或以上 [C1]，即可獲得 {10} 場免費遊戲。 | ▪ AFTER ALL CASCADES END, {3} OR MORE [C1] ON THE FINAL REELS AWARD {10} FREE SPINS. |
| 規則說明 | ▪ 在免費遊戲中，每次旋轉的連消結束後，若最終盤面出現 {3} 個或以上 [C1]，可再獲得 {5} 場免費遊戲。 | ▪ DURING THE FREE GAME, {3} OR MORE [C1] ON THE FINAL REELS AFTER ALL CASCADES OF A SPIN AWARD {5} ADDITIONAL FREE SPINS. |
| 規則說明 | ▪ 每次免費遊戲特色最多可進行 {50} 場免費遊戲。 | ▪ A MAXIMUM OF {50} FREE SPINS MAY BE PLAYED DURING EACH FREE GAME FEATURE. |
| 規則說明 | ▪ 免費遊戲開始時盤面沒有倍數框；免費遊戲中倍數框不會清除，倍數一路累積到免費遊戲特色結束。 | ▪ THE FREE GAME STARTS WITH NO MULTIPLIER FRAMES. DURING THE FREE GAME, MULTIPLIER FRAMES ARE NOT CLEARED AND THEIR MULTIPLIERS KEEP ADDING UP UNTIL THE FREE GAME FEATURE ENDS. |

---

## EXTRA BET

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 額外投注 | EXTRA BET |
| 規則說明 | ▪ 額外投注的扣款為您所選基礎投注的 {2}X。 | ▪ EXTRA BET COSTS {2}X THE BASE BET YOU SELECT. |
| 規則說明 | ▪ 所有獎金仍依您所選的基礎投注計算。 | ▪ ALL WINS ARE STILL CALCULATED ON THE BASE BET YOU SELECT. |
| 規則說明 | ▪ 免費遊戲的觸發機率提升為一般投注的 {5} 倍。 | ▪ THE CHANCE TO TRIGGER THE FREE GAME FEATURE IS {5} TIMES THAT OF THE NORMAL BET. |

---

## BUY FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 購買特色 | BUY FEATURE |
| 規則說明 | ▪ 玩家可支付 {75}x 總投注，直接購買一次免費遊戲進場機會。 | ▪ BUY FEATURE CAN BE PURCHASED FOR {75}X TOTAL BET TO ENTER THE FREE GAME FEATURE DIRECTLY. |
| 規則說明 | ▪ 完成購買後，將直接觸發一次免費遊戲特色。 | ▪ COMPLETING THE PURCHASE WILL TRIGGER THE FREE GAME FEATURE DIRECTLY. |

---

## SUPER FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 超級特色 | SUPER FEATURE |
| 規則說明 | ▪ 玩家可支付 {300}x 總投注，直接購買一次超級免費遊戲進場機會。 | ▪ SUPER FEATURE CAN BE PURCHASED FOR {300}X TOTAL BET TO ENTER THE SUPER FREE GAME DIRECTLY. |
| 規則說明 | ▪ 超級免費遊戲中，金色符號留下的倍數框初始倍數至少為 X{5}，其餘規則與免費遊戲特色相同。 | ▪ DURING THE SUPER FREE GAME, EVERY MULTIPLIER FRAME LEFT BY A GOLDEN SYMBOL STARTS AT X{5} OR HIGHER. ALL OTHER RULES ARE THE SAME AS THE FREE GAME FEATURE. |

---

## OP JACKPOT

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | OP JACKPOT | OP JACKPOT |
| 規則說明 | ▪ 在遊戲中，OP JACKPOT 特色由盤面上的 {1} 個或以上 [C1] 隨機觸發。 | ▪ THE OP JACKPOT FEATURE IS TRIGGERED RANDOMLY BY {1} OR MORE [C1] ON THE REELS. |
| 規則說明 | ▪ OP JACKPOT 特色會在畫面中出現 {12} 個 [幣]，其中包括 [GRAND]、[MAJOR]、[MINOR] 及 [MINI]。 | ▪ DURING THE OP JACKPOT FEATURE, THERE ARE {12} [COIN], WHICH CONSIST OF [GRAND], [MAJOR], [MINOR], AND [MINI]. |
| 規則說明 | ▪ 選擇 {1} 個 [幣] 以揭示 [GRAND]、[MAJOR]、[MINOR] 或 [MINI]。 | ▪ SELECT A [COIN] TO REVEAL [GRAND], [MAJOR], [MINOR], OR [MINI]. |
| 規則說明 | ▪ 當玩家獲得 {3} 個相同的 OP JACKPOT 特色符號，即可獲得該 OP JACKPOT 並結算總獎金。 | ▪ IF THE PLAYER REVEALS {3} OF THE SAME JACKPOT SYMBOL, THE PLAYER WINS THAT JACKPOT AND IT IS ADDED TO THE TOTAL WIN. |
| 規則說明 | ▪ [GRAND] 為連機累進彩金。單場遊戲中，投注選項選擇 {2.00} 以上即可解鎖 [GRAND]。 | ▪ [GRAND] IS A LINKED PROGRESSIVE JACKPOT. IF THE SINGLE GAME BET OPTION IS {2.00} OR ABOVE, [GRAND] WILL BE UNLOCKED. |
| 規則說明 | ▪ [MAJOR] 為連機累進彩金。單場遊戲中，投注選項選擇 {2.00} 以上即可解鎖 [MAJOR]。 | ▪ [MAJOR] IS A LINKED PROGRESSIVE JACKPOT. IF THE SINGLE GAME BET OPTION IS {2.00} OR ABOVE, [MAJOR] WILL BE UNLOCKED. |
| 規則說明 | ▪ [MINOR] 為紅利彩金，依照投注選項改變。 | ▪ [MINOR] WILL CHANGE IF THE PLAYER SELECTS A DIFFERENT BET OPTION. |
| 規則說明 | ▪ [MINI] 為紅利彩金，依照投注選項改變。 | ▪ [MINI] WILL CHANGE IF THE PLAYER SELECTS A DIFFERENT BET OPTION. |
| 規則說明 | ▪ 玩家投注越高，觸發 OP JACKPOT 特色的機會越高。 | ▪ THE HIGHER THE BET, THE HIGHER THE CHANCE TO TRIGGER THE OP JACKPOT FEATURE. |

---

## WAY GAME

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 最多路數 | MAXIMUM WAYS |
| 規則說明 | ▪ 本遊戲為 {5} 輪 × {4} 列盤面，相同符號須出現在由最左至右連續相鄰的轉輪上方可獲獎。 | ▪ THE GAME USES {5} REELS × {4} ROWS. MATCHING SYMBOLS MUST APPEAR ON CONSECUTIVE ADJACENT REELS FROM LEFTMOST TO RIGHT TO WIN. |
| 規則說明 | ▪ 遊戲設定 = 最多 {1,024} 路。 | ▪ GAME SETTING = {1,024} MAXIMUM WAYS. |
| 規則說明 | [走線圖- 1,024 MAX WAYS] | [走線圖- 1,024 MAX WAYS] |
| 規則說明 | [走線圖-3 OF A KIND PAYS 2 WAYS] | [走線圖-3 OF A KIND PAYS 2 WAYS] |
| 規則說明 | [走線圖-NO WIN] | [走線圖-NO WIN] |

---

## GAME RULE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 遊戲規則 | GAME RULES |
| 規則說明 | ▪ 選擇您想要玩的投注選項。 | ▪ SELECT THE BET OPTION YOU WISH TO PLAY. |
| 規則說明 | ▪ 所有中獎金額均乘以投注選項，除非是累積獎。 | ▪ ALL WINS ARE MULTIPLIED BY THE BET OPTION EXCEPT PROGRESSIVE BONUSES. |
| 規則說明 | ▪ 遊戲出現故障時，所有賠付與遊戲結果均視為無效。 | ▪ MALFUNCTION VOIDS ALL PAYS AND PLAYS. |
| 規則說明 | ▪ 若玩家在免費遊戲期間中斷連線，系統將自動完成該局結算，並將中獎金額加入餘額。 | ▪ IF THE PLAYER LOSES CONNECTION DURING THE FREE GAME FEATURE, THE SYSTEM WILL COMPLETE THE RESULT AUTOMATICALLY AND ADD ANY WINNINGS TO THE BALANCE. |
