# Game Help Draft

這份 md 是 `Thunder_Boost_1000_Help.xlsx` 的前置確認稿。
之後若要重產 xlsx，應先確認並修改這份 md，再轉成結構化 spec / xlsx。

## Game Meta

| Field | Value |
| --- | --- |
| game_id | 101016 |
| parsheet_id | H0281 |
| name_zh | 雷神爆金1000 |
| name_en | Thunder Boost 1000 |

---

## PAYTABLE

來源：rule-derived

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 符號賠付值 | SYMBOL PAYOUT VALUES |

### WILD SYMBOL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 百搭符號 | WILD SYMBOL |
| 規則說明 | [WW] 僅出現在第 {2}、{3}、{4}、{5} 輪，並可替代除 [SCATTER] 外的所有符號以幫助形成中獎組合。 | [WW] APPEARS ON REELS {2}, {3}, {4}, AND {5} ONLY, AND SUBSTITUTES FOR ALL SYMBOLS EXCEPT [SCATTER] TO HELP FORM WINNING COMBINATIONS. |

### SCATTER SYMBOL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 散佈符號 | SCATTER SYMBOL |
| 規則說明 | [SCATTER] 可出現在主盤面任意轉輪位置。 | [SCATTER] MAY APPEAR ANYWHERE ON THE MAIN REELS. |

### MULTIPLIER SYMBOL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 倍數符號 | MULTIPLIER SYMBOL |
| 規則說明 | [M1] 為倍數符號，可出現在主盤面與額外轉輪位置。 | [M1] IS THE MULTIPLIER SYMBOL AND MAY APPEAR ON THE MAIN REELS AND THE EXTRA REELS. |

### 賠率表

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 賠率表 | PAYTABLE |

繁中：

| 符號 | {6} 連 | {5} 連 | {4} 連 | {3} 連 |
| --- | ---: | ---: | ---: | ---: |
| [M1] 招財貓 | {4} | {2.5} | {2} | {1.5} |
| [M2] 日式鼓 | {2.5} | {1.5} | {1.25} | {1} |
| [M3] 燈籠 | {2} | {1.5} | {1.25} | {0.5} |
| [M4] 扇子 | {1.5} | {1} | {0.75} | {0.4} |
| [M5] 握壽司 | {0.75} | {0.6} | {0.5} | {0.3} |
| [M6] 壽司 | {0.75} | {0.6} | {0.5} | {0.3} |
| [A] | {0.5} | {0.4} | {0.3} | {0.2} |
| [K] | {0.5} | {0.4} | {0.3} | {0.2} |
| [Q] | {0.2} | {0.15} | {0.1} | {0.05} |
| [J] | {0.2} | {0.15} | {0.1} | {0.05} |
| [10] | {0.2} | {0.15} | {0.1} | {0.05} |

英文：

| SYMBOL | {6} OF A KIND | {5} OF A KIND | {4} OF A KIND | {3} OF A KIND |
| --- | ---: | ---: | ---: | ---: |
| [M1] | {4} | {2.5} | {2} | {1.5} |
| [M2] | {2.5} | {1.5} | {1.25} | {1} |
| [M3] | {2} | {1.5} | {1.25} | {0.5} |
| [M4] | {1.5} | {1} | {0.75} | {0.4} |
| [M5] | {0.75} | {0.6} | {0.5} | {0.3} |
| [M6] | {0.75} | {0.6} | {0.5} | {0.3} |
| [A] | {0.5} | {0.4} | {0.3} | {0.2} |
| [K] | {0.5} | {0.4} | {0.3} | {0.2} |
| [Q] | {0.2} | {0.15} | {0.1} | {0.05} |
| [J] | {0.2} | {0.15} | {0.1} | {0.05} |
| [10] | {0.2} | {0.15} | {0.1} | {0.05} |

---

## CASCADING FEATURE

來源：rule-derived

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 消除特色 | CASCADING FEATURE |
| 規則說明 | 每次結算後，中獎符號會被移除，剩餘符號會向下掉落並由新符號補滿空位。 | AFTER EACH WIN EVALUATION, WINNING SYMBOLS ARE REMOVED, THE REMAINING SYMBOLS CASCADE DOWN, AND NEW SYMBOLS FILL THE EMPTY POSITIONS. |
| 規則說明 | 盤面補滿後會再次結算新的中獎組合，直到不再形成新的中獎組合為止。 | AFTER THE REELS ARE REFILLED, NEW WINNING COMBINATIONS ARE EVALUATED AGAIN. THIS PROCESS CONTINUES UNTIL NO NEW WINNING COMBINATIONS ARE FORMED. |

---

## MULTIPLIER FEATURE

來源：rule-derived

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 倍數特色 | MULTIPLIER FEATURE |
| 規則說明 | 同一回合出現多個 [M1] 時，其倍數數值會累積相加。 | IF MULTIPLE [M1] SYMBOLS APPEAR IN THE SAME ROUND, THEIR MULTIPLIER VALUES ARE ADDED TOGETHER. |
| 規則說明 | 主盤面上的 [M1] 所提供的倍數，將依其符號尺寸決定。 | THE MULTIPLIER AWARDED BY [M1] ON THE MAIN REELS IS DETERMINED BY THE SYMBOL SIZE. |
| 規則說明 | 額外轉輪上的每個 [M1] 固定提供 X{2} 倍數。 | EACH [M1] ON THE EXTRA REELS AWARDS A FIXED X{2} MULTIPLIER. |
| 規則說明 | 當局所有中獎金額會乘上該局累積的總倍數。 | ALL WINS IN THE CURRENT ROUND ARE MULTIPLIED BY THE TOTAL ACCUMULATED MULTIPLIER FOR THAT ROUND. |
| 規則說明 | [M1大小對應倍數示意圖] | [M1大小對應倍數示意圖] |

---

## GOLDEN FRAMED FEATURE

來源：rule-derived

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 金框符號特色 | GOLDEN FRAMED FEATURE |
| 規則說明 | 第 {2}、{3}、{4}、{5} 輪的一般符號有機會帶有金框。 | GENERAL SYMBOLS ON REELS {2}, {3}, {4}, AND {5} MAY APPEAR WITH A GOLD FRAME. |
| 規則說明 | 金框符號只有在實際參與中獎並被移除時，才會在原位置轉為 [WW]。 | A GOLD FRAMED SYMBOL ONLY CHANGES INTO [WW] ON THE SAME POSITION AFTER IT ACTUALLY PARTICIPATES IN A WIN AND IS REMOVED. |
| 規則說明 | 轉化後的 [WW] 可參與下一次掉落後的中獎判定。 | THE TRANSFORMED [WW] CAN PARTICIPATE IN THE NEXT WIN EVALUATION AFTER THE CASCADE. |

---

## FREE GAME FEATURE

來源：rule-derived

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 免費遊戲特色 | FREE GAME FEATURE |
| 規則說明 | 主盤面出現 {4} 個或以上 [SCATTER] 可觸發免費遊戲。 | {4} OR MORE [SCATTER] APPEARING ON THE MAIN REELS WILL TRIGGER THE FREE GAME FEATURE. |
| 規則說明 | {4} 個 [SCATTER] 可獲得 {8} 場免費遊戲；每多出現 {1} 個 [SCATTER]，額外獲得 {2} 場免費遊戲。 | {4} [SCATTER] AWARD {8} FREE SPINS. EACH ADDITIONAL [SCATTER] AWARDS {2} MORE FREE SPINS. |
| 規則說明 | 每次免費遊戲特色最多可進行 {50} 場免費遊戲。 | A MAXIMUM OF {50} FREE SPINS MAY BE PLAYED DURING EACH FREE GAME FEATURE. |
| 規則說明 | 進入免費遊戲時，累積倍數由 X{2} 開始。 | THE ACCUMULATED MULTIPLIER STARTS AT X{2} WHEN THE FREE GAME FEATURE BEGINS. |
| 規則說明 | 免費遊戲期間，累積倍數不會在每場之間重置，並會持續保留至整段免費遊戲結束。 | DURING FREE GAME, THE ACCUMULATED MULTIPLIER IS NOT RESET BETWEEN SPINS AND IS CARRIED OVER UNTIL THE ENTIRE FEATURE ENDS. |
| 規則說明 | 免費遊戲期間再次出現 {4} 個或以上 [SCATTER] 可觸發加局；加局場次與一般觸發規則相同，且總場次不超過 {50} 場。 | DURING FREE GAME, {4} OR MORE [SCATTER] WILL RETRIGGER ADDITIONAL FREE SPINS. THE SAME FREE SPIN AWARD RULE APPLIES, UP TO A MAXIMUM OF {50} FREE SPINS IN TOTAL. |

---

## BUY FEATURE

來源：rule-derived

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 購買特色 | BUY FEATURE |
| 規則說明 | 玩家可支付 {75}x 總投注，直接購買一次免費遊戲進場機會。 | BUY FEATURE CAN BE PURCHASED FOR {75}X TOTAL BET TO ENTER THE FREE GAME FEATURE DIRECTLY. |
| 規則說明 | 完成購買後，將直接觸發一次免費遊戲特色。 | COMPLETING THE PURCHASE WILL TRIGGER THE FREE GAME FEATURE DIRECTLY. |

---

## OP JACKPOT

| Item | 簡中 | 英文 |
| --- | --- | --- |
| 主要標題 | OP JACKPOT | OP JACKPOT |
| 規則說明 | ▪ 在游戏中，OP JACKPOT 特色由特色转轮上 [C1] 随机触发。 | ▪ OP JACKPOT FEATURE IS TRIGGERED RANDOMLY BY {1} OR MORE [C1] ON THE REELS. |
| 規則說明 | ▪ OP JACKPOT 特色会在画面中出现 {12} 个 [幣]，其中包括 [GRAND]、[MAJOR]、[MINOR] 及 [MINI]。 | ▪ DURING OP JACKPOT FEATURE, THERE ARE {12} [COIN] WHICH CONSIST OF [GRAND], [MAJOR], [MINOR] AND [MINI]. |
| 規則說明 | ▪ 选择 {1} 个 [幣] 以揭示 [GRAND]、[MAJOR]、[MINOR] 或 [MINI]。 | ▪ SELECT A [COIN] TO REVEAL [GRAND], [MAJOR], [MINOR],OR [MINI]. |
| 規則說明 | ▪ 当玩家获得 {3} 个相同的 OP JACKPOT 特色符号即可获得该 OP JACKPOT 并结算总奖金。 | ▪ IF PLAYER GETS {3} SAME JACKPOT SYMBOLS WILL WIN THE JACKPOT AND CALCULATE TOTAL WINNINGS. |
| 規則說明 | ▪  [GRAND] 为连机累进彩金。单场游戏中，投注选项选择 {2.00} 以上即可解锁 [GRAND]。 | ▪ [GRAND] IS LINKED PROGRESSIVE JACKPOT. IF THE SINGLE GAME BET OPTION IS {2.00} OR ABOVE, THE PLAYER WILL UNLOCK [GRAND]. |
| 規則說明 | ▪  [MAJOR] 为连机累进彩金。单场游戏中，投注选项选择 {2.00} 以上即可解锁 [MAJOR]。 | ▪ [MAJOR] IS LINKED PROGRESSIVE JACKPOT. IF THE SINGLE GAME BET OPTION IS {2.00} OR ABOVE, THE PLAYER WILL UNLOCK [MAJOR]. |
| 規則說明 | ▪  [MINOR] 为红利彩金，依照投注选项改变。 | ▪ [MINOR] WILL CHANGE IF THE PLAYER SELECTS DIFFERENT BET OPTION. |
| 規則說明 | ▪  [MINI] 为红利彩金，依照投注选项改变。 | ▪ [MINI] WILL CHANGE IF THE PLAYER SELECTS DIFFERENT BET OPTION. |
| 規則說明 | ▪ 玩家投注越高触发 OP JACKPOT 特色的机会越高。 | ▪ THE HIGHER BET, THE HIGHER CHANCES TO TRIGGER OP JACKPOT FEATURE. |

---

## WAY GAME

來源：rule-derived

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 路數說明 | WAY GAME |
| 規則說明 | 本遊戲採用由左至右連續相鄰轉輪判定的 WAY GAME 玩法。 | THIS GAME USES A WAY GAME MECHANIC THAT PAYS FOR MATCHING SYMBOLS ON CONSECUTIVE ADJACENT REELS FROM LEFT TO RIGHT. |
| 規則說明 | 主盤面為 {6} 輪可變高度盤面，並在第 {2} 至第 {5} 輪上方各配置 {1} 個額外轉輪位置。 | THE MAIN REELS CONSIST OF {6} VARIABLE-HEIGHT REELS, WITH {1} EXTRA REEL POSITION ABOVE REELS {2} TO {5}. |
| 規則說明 | 本遊戲的路數範圍為 {2,025} WAYS 至 {32,400} WAYS。 | THE NUMBER OF WAYS IN THIS GAME RANGES FROM {2,025} WAYS TO {32,400} WAYS. |
| 規則說明 | 大型符號無論覆蓋多少位置，WAY 計算時均僅視為 {1} 個符號。 | A LARGE SYMBOL COUNTS AS {1} SYMBOL FOR WAY CALCULATION, REGARDLESS OF HOW MANY POSITIONS IT COVERS. |
| 規則說明 | [走線圖- 32,400 MAX WAY] | [走線圖- 32,400 MAX WAY] |
| 規則說明 | [走線圖-3 OF A KIND PAYS 2 WAYS] | [走線圖-3 OF A KIND PAYS 2 WAYS] |
| 規則說明 | [走線圖-NO WIN] | [走線圖-NO WIN] |

---

## GAME RULE

來源：mixed（template-copy + rule-derived）

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 遊戲規則 | GAME RULES |
| 規則說明 | 選擇您想要進行的投注後，主盤面與額外轉輪會同步開始旋轉。 | AFTER THE PLAYER SELECTS A BET, THE MAIN REELS AND THE EXTRA REELS SPIN TOGETHER. |
| 規則說明 | 中獎組合依 WAY GAME 規則判定，中獎金額會依該局累積的總倍數進行結算。 | WINNING COMBINATIONS ARE EVALUATED BY THE WAY GAME RULE, AND WINS ARE PAID WITH THE TOTAL MULTIPLIER ACCUMULATED IN THAT ROUND. |
| 規則說明 | 遊戲出現故障時，所有賠付與遊戲結果均視為無效。 | MALFUNCTION VOIDS ALL PAYS AND PLAYS. |
| 規則說明 | 若玩家在免費遊戲期間中斷連接，系統將自動完成該局結算，並將中獎金額加入餘額。 | IF THE PLAYER LOSES CONNECTION DURING THE FREE GAME FEATURE, THE SYSTEM WILL COMPLETE THE RESULT AUTOMATICALLY AND ADD ANY WINNINGS TO THE BALANCE. |
