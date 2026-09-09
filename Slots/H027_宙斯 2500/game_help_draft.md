# 101027 Game Help Draft

這份 md 是 `101027_Help.xlsx` 的前置確認稿。
之後若要重產 xlsx，應先確認並修改這份 md，再轉成結構化 spec / xlsx。

## Game Meta

| Field | Value |
| --- | --- |
| game_id | 101027 |
| parsheet_id | H0271 |
| name_zh | 宙斯 2500 |
| name_en | Zeus 2500 |
| game_type | Video Slot - Pay Anywhere / Cascade |

---

## PAYTABLE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 符號賠付值 | SYMBOL PAYOUT VALUES |

### SCATTER SYMBOL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 散布符號 | SCATTER SYMBOL |
| 規則說明 | ▪ [C1] 不參與中獎判定，出現後原地保留至該次旋轉的所有連消結束。 | ▪ [C1] DOES NOT TAKE PART IN WIN EVALUATION AND STAYS IN PLACE UNTIL ALL CASCADES OF THE SPIN ARE COMPLETE. |
| 規則說明 | ▪ 所有連消結束後，若最終盤面出現 {4} 個或以上 [C1]，將觸發免費遊戲。 | ▪ WHEN ALL CASCADES ARE COMPLETE, {4} OR MORE [C1] ON THE FINAL REELS WILL TRIGGER THE FREE GAME FEATURE. |
| 規則說明 | ▪ {4}／{5}／{6} 個 [C1] 分別支付 {3}／{5}／{100} × 投注。{3} 個 [C1] 不支付獎金。 | ▪ {4} / {5} / {6} [C1] PAY {3} / {5} / {100} × BET RESPECTIVELY. {3} [C1] DO NOT PAY. |
| 規則說明 | ▪ 同一轉輪最多只會出現 {1} 個 [C1]。 | ▪ AT MOST {1} [C1] APPEARS ON EACH REEL. |

### MULTIPLIER SYMBOL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 倍數符號 | MULTIPLIER SYMBOL |
| 規則說明 | ▪ [C2] 與 [C3] 不參與中獎判定，也不會被消除，會留在盤面直到該次旋轉結束。 | ▪ [C2] AND [C3] DO NOT TAKE PART IN WIN EVALUATION, ARE NEVER CLEARED, AND REMAIN ON THE REELS UNTIL THE SPIN ENDS. |
| 規則說明 | ▪ [C2] 出現時即固定其倍數，之後不再改變。 | ▪ [C2] KEEPS THE VALUE IT APPEARS WITH. |
| 規則說明 | ▪ [C3] 於每次中獎消除後提升一個倍數等級，單顆最高為 {2500}x。 | ▪ [C3] IS UPGRADED BY ONE LEVEL AFTER EACH WINNING CASCADE, UP TO {2500}X PER SYMBOL. |
| 規則說明 | ▪ 該次消除後才掉落進盤面的 [C3] 不追溯升級，須等下一次中獎消除。 | ▪ A [C3] THAT DROPS IN AFTER A CASCADE IS NOT UPGRADED FOR THAT CASCADE AND MUST WAIT FOR THE NEXT ONE. |
| 規則說明 | ▪ 同一最終盤面出現多顆 [C2]／[C3] 時，所有倍數相加。 | ▪ WHEN SEVERAL [C2]／[C3] APPEAR ON THE SAME FINAL REELS, THEIR VALUES ARE ADDED TOGETHER. |
| 規則說明 | ▪ 最終盤面沒有 [C2]／[C3] 時，該次旋轉的倍數為 {1}x。 | ▪ IF THERE IS NO [C2] / [C3] ON THE FINAL REELS, THE MULTIPLIER FOR THAT SPIN IS {1}X. |

### 賠率表

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 賠率表 | PAYTABLE |
| 規則說明 | ▪ 以下賠付值以投注 {100} 顯示。 | ▪ THE PAYOUT VALUES BELOW ARE SHOWN FOR A BET OF {100}. |

| 繁中 | 繁中 | 繁中 |
| --- | --- | --- |
| [M1] 12+ - 5000 | [M2] 12+ - 2500 | [M3] 12+ - 1500 |
| [M1] 10–11 - 2500 | [M2] 10–11 - 1000 | [M3] 10–11 - 500 |
| [M1] 8–9 - 1000 | [M2] 8–9 - 250 | [M3] 8–9 - 200 |
| [M4] 12+ - 1200 | [A] 12+ - 1000 | [K] 12+ - 800 |
| [M4] 10–11 - 200 | [A] 10–11 - 150 | [K] 10–11 - 120 |
| [M4] 8–9 - 150 | [A] 8–9 - 100 | [K] 8–9 - 80 |
| [Q] 12+ - 500 | [J] 12+ - 400 | [TE] 12+ - 200 |
| [Q] 10–11 - 100 | [J] 10–11 - 90 | [TE] 10–11 - 75 |
| [Q] 8–9 - 50 | [J] 8–9 - 40 | [TE] 8–9 - 25 |

---

## CASCADING FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 連消特色 | CASCADING FEATURE |
| 規則說明 | ▪ 中獎符號消除後，其上方符號向下掉落，空位由同一轉輪依序補入新符號。 | ▪ AFTER WINNING SYMBOLS ARE CLEARED, THE SYMBOLS ABOVE THEM DROP DOWN AND NEW SYMBOLS FILL THE EMPTY POSITIONS FROM THE SAME REEL. |
| 規則說明 | ▪ 補滿後重新判定，若再出現中獎則重複消除與補位，直到沒有新的中獎為止。 | ▪ THE NEW REELS ARE EVALUATED AGAIN. CLEARING AND REFILLING REPEAT UNTIL NO NEW WIN OCCURS. |
| 規則說明 | ▪ 同一次旋轉所有連消的一般符號獎金先相加，再一次套用倍數。 | ▪ ALL REGULAR-SYMBOL WINS FROM EVERY CASCADE OF A SPIN ARE ADDED TOGETHER FIRST, THEN THE MULTIPLIER IS APPLIED ONCE. |
| 規則說明 | ▪ [C1]、[C2] 與 [C3] 不參與連消。 | ▪ [C1], [C2] AND [C3] DO NOT TAKE PART IN CASCADES. |

---

## MULTIPLIER FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 倍數特色 | MULTIPLIER FEATURE |
| 規則說明 | ▪ 一般遊戲中，最終盤面所有 [C2]／[C3] 的倍數總和，於所有連消結束後對該次旋轉的一般符號總獎金套用一次。 | ▪ IN THE BASE GAME, THE SUM OF ALL [C2] / [C3] VALUES ON THE FINAL REELS IS APPLIED ONCE TO THE TOTAL REGULAR-SYMBOL WIN OF THAT SPIN AFTER ALL CASCADES ARE COMPLETE. |
| 規則說明 | ▪ 一般遊戲的倍數只作用於該次旋轉，不累積至下一次旋轉。 | ▪ BASE GAME MULTIPLIERS APPLY ONLY TO THE CURRENT SPIN AND DO NOT CARRY OVER. |
| 規則說明 | ▪ 免費遊戲的倍數會累積。 | ▪ IN THE FREE GAME FEATURE THE MULTIPLIERS ACCUMULATE. |
| 規則說明 | ▪ 乘倍效果不作用於 [C1]。 | ▪ THE MULTIPLIER EFFECT DOES NOT APPLY TO [C1]. |

---

## FREE GAME FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 免費遊戲特色 | FREE GAME FEATURE |
| 規則說明 | ▪ 最終盤面出現 {4} 個或以上 [C1] 時觸發免費遊戲，獲得 {15} 次免費旋轉。 | ▪ {4} OR MORE [C1] ON THE FINAL REELS TRIGGER THE FREE GAME FEATURE AND AWARD {15} FREE SPINS. |
| 規則說明 | ▪ 免費遊戲中最終盤面出現 {3} 個或以上 [C1] 時，增加 {5} 次免費旋轉。 | ▪ {3} OR MORE [C1] ON THE FINAL REELS DURING THE FREE GAME FEATURE AWARD {5} ADDITIONAL FREE SPINS. |
| 規則說明 | ▪ 免費遊戲的總場次上限為 {50} 次。 | ▪ THE FREE GAME FEATURE IS LIMITED TO A TOTAL OF {50} FREE SPINS. |
| 規則說明 | ▪ 當一次免費旋轉同時有一般符號得獎、且最終盤面出現 [C2]／[C3] 時，該次盤面的倍數總和加入累積倍數。 | ▪ WHEN A FREE SPIN HAS BOTH A REGULAR-SYMBOL WIN AND [C2] / [C3] ON THE FINAL REELS, THE SUM OF THOSE VALUES IS ADDED TO THE CARRYING MULTIPLIER. |
| 規則說明 | ▪ 只有 [C1] 得獎或沒有得獎的免費旋轉，倍數不累積。 | ▪ FREE SPINS WITH ONLY A [C1] WIN, OR WITH NO WIN, DO NOT ADD TO THE CARRYING MULTIPLIER. |
| 規則說明 | ▪ 累積倍數只在「該次最終盤面本身有 [C2]／[C3]」時作用。有一般符號得獎但盤面沒有倍數符號時，該次以 {1}x 結算，累積倍數保留不歸零。 | ▪ THE CARRYING MULTIPLIER APPLIES ONLY ON A SPIN WHOSE OWN FINAL REELS CONTAIN [C2] / [C3]. IF A SPIN HAS A REGULAR-SYMBOL WIN BUT NO MULTIPLIER SYMBOL, IT IS PAID AT {1}X AND THE CARRYING MULTIPLIER IS KEPT, NOT RESET. |
| 規則說明 | ▪ 倍數在所有連消結束後，對該次免費旋轉的一般符號總獎金一次套用。 | ▪ THE MULTIPLIER IS APPLIED ONCE TO THE TOTAL REGULAR-SYMBOL WIN OF THE FREE SPIN AFTER ALL CASCADES ARE COMPLETE. |
| 規則說明 | ▪ 累積倍數保留至整場免費遊戲結束後才清除。 | ▪ THE CARRYING MULTIPLIER IS KEPT UNTIL THE FREE GAME FEATURE ENDS. |

---

## EXTRA BET

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 額外投注 | EXTRA BET |
| 規則說明 | ▪ 額外投注的扣款為 {2} × 您所選的基礎投注。 | ▪ EXTRA BET COSTS {2} × THE BASE BET YOU SELECT. |
| 規則說明 | ▪ 提高的只有扣款；所有獎金仍依您所選的基礎投注計算。 | ▪ ONLY THE COST IS INCREASED. ALL WINS ARE STILL CALCULATED ON THE BASE BET YOU SELECT. |
| 規則說明 | ▪ 免費遊戲的觸發機率提升為一般投注的 {5} 倍。 | ▪ THE CHANCE TO TRIGGER THE FREE GAME FEATURE IS {5} TIMES THAT OF THE NORMAL BET. |

---

## BUY FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 購買特色 | BUY FEATURE |
| 規則說明 | ▪ 購買特色的扣款為 {100} × 您所選的基礎投注。 | ▪ BUY FEATURE COSTS {100} × THE BASE BET YOU SELECT. |
| 規則說明 | ▪ 直接進入免費遊戲。 | ▪ IT ENTERS THE FREE GAME FEATURE DIRECTLY. |
| 規則說明 | ▪ 進場盤面不進行一般符號的中獎判定，也不執行連消。 | ▪ THE ENTRY REELS ARE NOT EVALUATED FOR REGULAR SYMBOL WINS AND DO NOT CASCADE. |
| 規則說明 | ▪ 進場盤面的 {4} 個 [C1] 依賠率表支付 {3} × 投注。 | ▪ THE {4} [C1] ON THE ENTRY REELS PAY {3} × BET ACCORDING TO THE PAYTABLE. |
| 規則說明 | ▪ 進入後的免費遊戲規則與自然觸發完全相同。 | ▪ ONCE ENTERED, THE FREE GAME FEATURE FOLLOWS EXACTLY THE SAME RULES AS A NATURAL TRIGGER. |
| 規則說明 | ▪ 免費遊戲的獎金依您所選的基礎投注計算，不依購買金額計算。 | ▪ FREE GAME WINS ARE CALCULATED ON THE BASE BET YOU SELECT, NOT ON THE PURCHASE AMOUNT. |
| 規則說明 | ▪ 本遊戲不提供超級購買特色。 | ▪ THIS GAME DOES NOT OFFER A SUPER FEATURE. |

---

## OP JACKPOT

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | OP JACKPOT | OP JACKPOT |
| 規則說明 | ▪ 遊戲中，OP JACKPOT 特色由盤面上的 {1} 個或以上 [C1] 隨機觸發。 | ▪ OP JACKPOT FEATURE IS TRIGGERED RANDOMLY BY {1} OR MORE [C1] ON THE REELS. |
| 規則說明 | ▪ OP JACKPOT 特色會在畫面中顯示 {12} 個 [硬幣]，其中包含 [硬幣-GRAND]、[硬幣-MAJOR]、[硬幣-MINOR] 與 [硬幣-MINI]。 | ▪ DURING OP JACKPOT FEATURE, THERE ARE {12} [COIN] WHICH CONSIST OF [COIN-GRAND], [COIN-MAJOR], [COIN-MINOR], AND [COIN-MINI]. |
| 規則說明 | ▪ 選擇 {1} 個 [硬幣]，以揭示 [硬幣-GRAND]、[硬幣-MAJOR]、[硬幣-MINOR] 或 [硬幣-MINI]。獲得 {3} 個相同的 OP JACKPOT 符號，即可贏得對應彩金並結算總獎金。 | ▪ SELECT {1} [COIN] TO REVEAL [COIN-GRAND], [COIN-MAJOR], [COIN-MINOR], OR [COIN-MINI]. OBTAIN {3} IDENTICAL OP JACKPOT SYMBOLS TO WIN THE CORRESPONDING JACKPOT AND CALCULATE THE TOTAL WIN. |
| 規則說明 | ▪ [GRAND] 與 [MAJOR] 為連機累進彩金。單場遊戲的投注選項達到 {2.00} 或以上時，即可解鎖 [GRAND] 與 [MAJOR]。 | ▪ [GRAND] AND [MAJOR] ARE LINKED PROGRESSIVE JACKPOTS. A BET OPTION OF {2.00} OR ABOVE UNLOCKS [GRAND] AND [MAJOR] FOR THE SINGLE GAME. |
| 規則說明 | ▪ [MINOR] 與 [MINI] 為紅利彩金，彩金數值會依投注選項改變。 | ▪ [MINOR] AND [MINI] ARE BONUS JACKPOTS. THEIR VALUES CHANGE ACCORDING TO THE SELECTED BET OPTION. |
| 規則說明 | ▪ 投注越高，觸發 OP JACKPOT 特色的機會越高。 | ▪ THE HIGHER THE BET, THE HIGHER THE CHANCE TO TRIGGER THE OP JACKPOT FEATURE. |

> **待確認**：本區塊敘述取自 H019，其中 [GRAND]／[MAJOR] 的解鎖門檻 `{2.00}` 是 H019 的值，
> H027 的門檻尚未在 `game_rule.md` 定義。SPS（`JP optionID 28`）的實測支持這個結構——
> pool[1]／pool[2]（對應 GRAND／MAJOR）在 1,000 萬局內 0 次命中，pool[3]／pool[4] 有命中，
> 且 Link JP 只在「老手 ＋ 中／大 Bet」才給獎（小 Bet 與新手皆為 0），確認確實有投注解鎖門檻，
> 但門檻的實際數值要向 JP 設定端確認後回填。

---

## PAY ANYWHERE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 中獎方式 | PAY ANYWHERE |
| 規則說明 | ▪ 盤面為 {6} 輪 × {5} 列，共 {30} 格。 | ▪ THE GAME USES A {6}-REEL BY {5}-ROW GRID WITH {30} POSITIONS. |
| 規則說明 | ▪ 同一種一般符號在整個盤面合計出現 {8} 個或以上即可得獎，不要求相鄰或連線。 | ▪ {8} OR MORE OF THE SAME REGULAR SYMBOL ANYWHERE ON THE GRID FORM A WIN. THEY DO NOT NEED TO BE ADJACENT OR ON A LINE. |
| 規則說明 | ▪ 每種一般符號獨立計數，依 {8}–{9}／{10}–{11}／{12} 個以上支付對應賠率。 | ▪ EACH REGULAR SYMBOL IS COUNTED SEPARATELY AND PAID BY ITS {8}–{9} / {10}–{11} / {12}-OR-MORE TIER. |
| 規則說明 | ▪ 同一盤面可有多種一般符號同時得獎，各自支付一次。 | ▪ SEVERAL REGULAR SYMBOL TYPES MAY WIN ON THE SAME GRID AND EACH IS PAID ONCE. |
| 規則說明 | ▪ 一般符號獎金為「該級距賠率 × 投注」。 | ▪ A REGULAR SYMBOL WIN IS CALCULATED AS ITS TIER VALUE × BET. |
| 規則說明 | ▪ 本遊戲沒有百搭符號。 | ▪ THIS GAME HAS NO WILD SYMBOL. |

---

## GAME RULE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 遊戲規則 | GAME RULES |
| 規則說明 | ▪ 選擇您想要玩的投注選項。 | ▪ SELECT BET OPTION YOU WISH TO PLAY. |
| 規則說明 | ▪ 所有中獎金額均乘以投注選項，除非是累積獎。 | ▪ ALL WINS ARE MULTIPLIED BY BET OPTION EXCEPT PROGRESSIVES BONUSES. |
| 規則說明 | ▪ 遊戲出現故障，所有賠付和遊戲都視為無效。 | ▪ MALFUNCTION VOIDS ALL PAYS AND PLAYS. |
| 規則說明 | ▪ 若玩家在免費遊戲特色期間中斷遊戲，系統將會自動計算遊戲結果，並將獲獎金額加入至餘額中。 | ▪ IF THE PLAYER LOSES CONNECTION DURING THE FREE GAME FEATURE, THE SYSTEM WILL CALCULATE THE GAME RESULTS AUTOMATICALLY AND THE WINNING PRIZES WILL BE ADDED INTO THE BALANCE. |
