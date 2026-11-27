# 三隻小豬 Game Help Draft

這份 md 是三隻小豬（發想，以彩罐熱舞改）Help 的前置確認稿。
之後若要重產 xlsx，應先確認並修改這份 md，再轉成結構化 spec / xlsx。

## Game Meta

| Field | Value |
| --- | --- |
| game_id | — |
| parsheet_id | — |
| name_zh | 三隻小豬 |
| name_en | Three Little Pigs |
| game_type | Video Slot - 20 Lines / Cascade |

---

## PAYTABLE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 符號賠付值 | SYMBOL PAYOUT VALUES |

### WILD SYMBOL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 百搭符號 | WILD SYMBOL |
| 規則說明 | ▪ [WW] 可替代除 [Scatter] 外的所有符號。 | ▪ [WW] SUBSTITUTES FOR ALL SYMBOLS EXCEPT [Scatter]. |

### SCATTER SYMBOL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 散布符號 | SCATTER SYMBOL |
| 規則說明 | ▪ 當本次旋轉連消結束後，若最終盤面出現 {3} 個或以上 [C1]，將觸發免費遊戲。 | ▪ WHEN ALL CASCADES ARE COMPLETE, {3} OR MORE [C1] ON THE FINAL REELS WILL TRIGGER THE FREE GAME FEATURE. |

### 賠率表

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 賠率表 | PAYTABLE |

| 中文欄 | 中文欄 | 中文欄 |
| --- | --- | --- |
| [M1] 5 - 5000 | [M2] 5 - 1000 | [M3] 5 - 750 |
| [M1] 4 - 1250 | [M2] 4 - 300 | [M3] 4 - 225 |
| [M1] 3 - 250 | [M2] 3 - 100 | [M3] 3 - 75 |
| [M4] 5 - 500 | [M5] 5 - 250 | [A] 5 - 100 |
| [M4] 4 - 150 | [M5] 4 - 75 | [A] 4 - 50 |
| [M4] 3 - 50 | [M5] 3 - 25 | [A] 3 - 10 |
| [K] 5 - 100 | [Q] 5 - 100 | [J] 5 - 100 |
| [K] 4 - 50 | [Q] 4 - 50 | [J] 4 - 50 |
| [K] 3 - 10 | [Q] 3 - 10 | [J] 3 - 10 |

---

## CASCADING FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 消除特色 | CASCADING FEATURE |
| 規則說明 | ▪ 每輪結算後，中獎符號會被消除；消除後產生的空格由上方符號向下掉落補位。 | ▪ AFTER EACH WIN EVALUATION, WINNING SYMBOLS ARE REMOVED AND THE SYMBOLS ABOVE FALL DOWN TO FILL THE EMPTY POSITIONS. |
| 規則說明 | ▪ 補牌後會再次檢查新的中獎組合，直到不再形成新的中獎組合為止。 | ▪ AFTER THE SYMBOLS CASCADE DOWN, NEW WINNING COMBINATIONS ARE EVALUATED AGAIN. THIS PROCESS REPEATS UNTIL NO NEW WINNING COMBINATIONS ARE FORMED. |

---

## FRAME MULTIPLIER FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 框倍數特色 | FRAME MULTIPLIER FEATURE |
| 規則說明 | ▪ 金色符號參與得分時，該位置會加上茅草框；同一位置之後再有金色符號參與得分，框依序升級為木頭框、磚頭框，最多 {3} 階。 | ▪ WHEN A GOLDEN SYMBOL TAKES PART IN A WIN, ITS POSITION GAINS A STRAW FRAME. EACH LATER GOLDEN SYMBOL WIN ON THE SAME POSITION UPGRADES IT TO WOOD, THEN BRICK, UP TO {3} LEVELS. |
| 規則說明 | ▪ 框留在原位置，不隨符號消除或掉落移動。 | ▪ FRAMES STAY ON THEIR POSITIONS AND DO NOT MOVE WHEN SYMBOLS ARE CLEARED OR FALL. |
| 規則說明 | ▪ 當本次旋轉無法再消除時，若本次旋轉有得分，每個框會出現隨機倍數：茅草框 {1}X～{2500}X、木頭框 {3}X～{2500}X、磚頭框 {15}X～{2500}X。 | ▪ WHEN NO MORE CASCADES CAN OCCUR AND THE SPIN HAS A WIN, EACH FRAME REVEALS A RANDOM MULTIPLIER: STRAW {1}X–{2500}X, WOOD {3}X–{2500}X, BRICK {15}X–{2500}X. |
| 規則說明 | ▪ 本次旋轉的倍數為 {1} 加上所有框的倍數，乘上本次旋轉的總贏分；沒有框時為 {1}X。 | ▪ THE SPIN MULTIPLIER IS {1} PLUS THE SUM OF ALL FRAME MULTIPLIERS, APPLIED TO THE TOTAL WIN OF THIS SPIN; WITH NO FRAME IT IS {1}X. |
| 規則說明 | ▪ 主遊戲中，框只作用於本次旋轉，下一次旋轉重新開始。 | ▪ IN THE BASE GAME, FRAMES APPLY ONLY TO THE CURRENT SPIN AND RESET ON THE NEXT SPIN. |

---

## GOLDEN SYMBOL FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 金色符號特色 | GOLDEN SYMBOL FEATURE |
| 規則說明 | ▪ 第 {2}、{3}、{4} 輪的一般符號有機會以金色符號出現。 | ▪ GENERAL SYMBOLS ON REELS 2, 3, AND 4 MAY APPEAR AS GOLDEN SYMBOLS. |
| 規則說明 | ▪ 金色符號與原始符號具有相同的基礎賠率。 | ▪ GOLDEN SYMBOLS PAY THE SAME AS THEIR ORIGINAL SYMBOL. |
| 規則說明 | ▪ 若前一輪中獎組閤中含有金色符號，該位置會保留並轉化為 [WW]。 | ▪ IF THE PREVIOUS WINNING COMBINATION INCLUDES A GOLDEN SYMBOL, THAT POSITION REMAINS ON THE REELS AND CHANGES INTO [WW]. |

---

## FREE GAME FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 免費遊戲特色 | FREE GAME FEATURE |
| 規則說明 | ▪ 當本次旋轉連消結束後，若最終盤面出現 {3}、{4} 或 {5} 個 [Scatter]，即可觸發免費遊戲，分別獲得 {10}、{15} 或 {20} 場免費遊戲。 | ▪ WHEN ALL CASCADES ARE COMPLETE, IF THE FINAL REELS SHOW {3}, {4}, OR {5} [C1], THE FREE GAME FEATURE IS TRIGGERED WITH {10}, {15}, OR {20} FREE SPINS RESPECTIVELY. |
| 規則說明 | ▪ 免費遊戲期間，框不會重置，保留到整段免費遊戲結束並可繼續升級；每次免費旋轉有得分時，所有框出現倍數並乘上該次旋轉的總贏分。 | ▪ DURING FREE GAME, FRAMES ARE NOT RESET AND CAN KEEP UPGRADING UNTIL THE FREE GAME ENDS. ON EACH WINNING FREE SPIN, ALL FRAMES REVEAL MULTIPLIERS THAT APPLY TO THAT SPIN'S TOTAL WIN. |
| 規則說明 | ▪ 單次進入免費遊戲後，包含加局在內，最多進行 {50} 場。 | ▪ AFTER ENTERING THE FREE GAME, INCLUDING RETRIGGERING, THE MAXIMUM NUMBER OF FREE SPINS IS {50}. |
| 規則說明 | ▪ 免費遊戲可加局。加局條件與一般觸發相同：{3}、{4} 或 {5} 個 [C1] 分別對應加 {10}、{15} 或 {20} 場免費遊戲。 | ▪ FREE GAME CAN BE RETRIGGERED. RETRIGGERING FOLLOWS THE SAME CONDITIONS: {3}, {4}, OR {5} [C1] WILL ADD {10}, {15}, OR {20} FREE SPINS RESPECTIVELY. |

---

## EXTRA BET

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 額外投注 | EXTRA BET |
| 規則說明 | ▪ 玩家可選擇額外投注模式進行旋轉。 | ▪ THE PLAYER MAY SELECT THE EXTRA BET MODE. |
| 規則說明 | ▪ 額外投注的投注金額為 {2}x 總投注，並可提高觸發免費遊戲的機會。 | ▪ EXTRA BET COSTS {2}X TOTAL BET AND INCREASES THE CHANCE TO TRIGGER THE FREE GAME FEATURE. |

---

## BUY FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 購買特色 | BUY FEATURE |
| 規則說明 | ▪ 玩家可支付 {75}x 投注，直接購買進入一次免費遊戲。 | ▪ BUY FEATURE CAN BE PURCHASED BY USING A VALUE EQUAL TO {75}X TOTAL BET. |
| 規則說明 | ▪ 購買後直接觸發免費遊戲規格。 | ▪ PURCHASING THE BUY FEATURE GUARANTEES ENTRY INTO FREE GAME. |

---

## OP JACKPOT

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | OP JACKPOT | OP JACKPOT |
| 規則說明 | ▪ 在遊戲中，OP JACKPOT 特色由特色轉輪上 [C1] 隨機觸發。 | ▪ OP JACKPOT FEATURE IS TRIGGERED RANDOMLY BY {1} OR MORE [C1] ON THE REELS. |
| 規則說明 | ▪ OP JACKPOT 特色會在畫面中出現 {12} 個 [幣]，其中包括 [GRAND]、[MAJOR]、[MINOR] 及 [MINI]。 | ▪ DURING OP JACKPOT FEATURE, THERE ARE {12} [COIN] WHICH CONSIST OF [GRAND], [MAJOR], [MINOR] AND [MINI]. |
| 規則說明 | ▪ 選擇 {1} 個 [幣] 以揭示 [GRAND]、[MAJOR]、[MINOR] 或 [MINI]。 | ▪ SELECT A [COIN] TO REVEAL [GRAND], [MAJOR], [MINOR],OR [MINI]. |
| 規則說明 | ▪ 當玩家獲得 {3} 個相同的 OP JACKPOT 特色符號即可獲得該 OP JACKPOT 並結算總獎金。 | ▪ IF PLAYER GETS {3} SAME JACKPOT SYMBOLS WILL WIN THE JACKPOT AND CALCULATE TOTAL WINNINGS. |
| 規則說明 | ▪  [GRAND] 為連機累進彩金。單場遊戲中，投注選項選擇 {2.00} 以上即可解鎖 [GRAND]。 | ▪ [GRAND] IS LINKED PROGRESSIVE JACKPOT. IF THE SINGLE GAME BET OPTION IS {2.00} OR ABOVE, THE PLAYER WILL UNLOCK [GRAND]. |
| 規則說明 | ▪  [MAJOR] 為連機累進彩金。單場遊戲中，投注選項選擇 {2.00} 以上即可解鎖 [MAJOR]。 | ▪ [MAJOR] IS LINKED PROGRESSIVE JACKPOT. IF THE SINGLE GAME BET OPTION IS {2.00} OR ABOVE, THE PLAYER WILL UNLOCK [MAJOR]. |
| 規則說明 | ▪  [MINOR] 為紅利彩金，依照投注選項改變。 | ▪ [MINOR] WILL CHANGE IF THE PLAYER SELECTS DIFFERENT BET OPTION. |
| 規則說明 | ▪  [MINI] 為紅利彩金，依照投注選項改變。 | ▪ [MINI] WILL CHANGE IF THE PLAYER SELECTS DIFFERENT BET OPTION. |
| 規則說明 | ▪ 玩家投注越高觸發 OP JACKPOT 特色的機會越高。 | ▪ THE HIGHER BET, THE HIGHER CHANCES TO TRIGGER OP JACKPOT FEATURE. |

---

## LINE GAME

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 賠線說明 | LINE GAME |
| 規則說明 | ▪ 本遊戲共有 {20} 條固定賠線。 | ▪ THE GAME HAS {20} FIXED PAY LINES. |
| 規則說明 | ▪ 中獎組合必須由最左側開始，由左至右連續出現才算中獎。 | ▪ WINNING COMBINATIONS MUST START FROM THE LEFTMOST REEL AND RUN CONSECUTIVELY FROM LEFT TO RIGHT. |
| 規則說明 | ▪ 單一賠線僅支付最高獎項。 | ▪ ONLY THE HIGHEST WIN PER LINE IS PAID. |
| 規則說明 | ▪ [走線圖 20 LINE] | ▪ [走線圖 20 LINE] |

---

## GAME RULE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 遊戲規則 | GAME RULES |
| 規則說明 | ▪ 選擇您想要玩的投注選項。 | ▪ SELECT BET OPTION YOU WISH TO PLAY. |
| 規則說明 | ▪ 所有中獎金額均乘以投注選項，除非是累積獎。 | ▪ ALL WINS ARE MULTIPLIED BY BET OPTION EXCEPT PROGRESSIVES BONUSES. |
| 規則說明 | ▪ 遊戲出現故障，所有賠付和遊戲都視為無效。 | ▪ MALFUNCTION VOIDS ALL PAYS AND PLAYS. |
| 規則說明 | ▪ 若玩家在免費遊戲特色期間中斷遊戲，系統將會自動計算遊戲結果，並將獲獎金額加入至餘額中。 | ▪ IF THE PLAYER LOSES CONNECTION DURING THE FREE GAME FEATURE, THE SYSTEM WILL CALCULATE THE GAME RESULTS AUTOMATICALLY AND THE WINNING PRIZES WILL BE ADDED INTO THE BALANCE. |
