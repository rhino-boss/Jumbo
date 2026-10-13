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
| 規則說明 | ▪ 所有符號必須由最左至右連續出現，方可獲獎。 | ▪ ALL WINS ARE FROM LEFTMOST TO RIGHT ONLY. |

### WILD SYMBOL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 百搭符號 | WILD SYMBOL |
| 規則說明 | ▪ [WW][W2] 可替代除 [C1] 以外的所有符號。 | ▪ [WW][W2] SUBSTITUTE FOR ALL SYMBOLS EXCEPT [C1]. |
| 規則說明 | ▪ [WW][W2] 只會在金框符號被消除後產生。 | ▪ [WW][W2] ARE AWARDED ONLY AFTER A GOLDEN FRAMED SYMBOL IS REMOVED. |

### SCATTER SYMBOL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 免費遊戲獎賞 | FREE GAME BONUS |
| 規則說明 | ▪ 當 {3} 個以上 [C1] 出現在任一位置，即可觸發免費遊戲特色，獲得 {10} 場免費遊戲。 | ▪ {3} OR MORE [C1] APPEARING IN ANY POSITION WILL TRIGGER THE FREE GAME FEATURE WITH {10} FREE SPINS. |

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
| 規則說明 | ▪ 遊戲中若達成連線，除金框符號外的中獎符號將被消除，並在原位置補上新的符號。 | ▪ ALL SYMBOLS IN WINNING COMBINATIONS, EXCEPT GOLDEN FRAMED SYMBOLS, WILL BE REMOVED AND NEW SYMBOLS WILL FILL THE EMPTY POSITIONS. |
| 規則說明 | ▪ 消除特色會持續發生，直到沒有新的連線為止。 | ▪ THE FEATURE CONTINUES UNTIL THERE ARE NO NEW WINNING COMBINATIONS. |

---

## GOLDEN FRAMED FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 金框符號特色 | GOLDEN FRAMED FEATURE |
| 規則說明 | ▪ 金框符號只會出現在第 {2}、{3}、{4} 輪。 | ▪ GOLDEN FRAMED SYMBOLS APPEAR ON REELS {2}, {3} AND {4} ONLY. |
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
| 規則說明 | ▪ 每次連線時，本次中獎並被消除的帶倍數百搭符號，其倍數會相加，再乘上當次的贏分倍數。 | ▪ ON EACH WIN, THE MULTIPLIERS OF ALL MULTIPLIER WILDS THAT ARE PART OF THE WIN AND REMOVED ARE ADDED TOGETHER, THEN MULTIPLIED BY THE CURRENT WIN MULTIPLIER. |
| 規則說明 | ▪ 未參與中獎的帶倍數百搭符號會保留在盤面上，直到參與中獎時才計入。 | ▪ MULTIPLIER WILDS THAT ARE NOT PART OF A WIN STAY ON THE REELS AND COUNT ONLY WHEN THEY ARE PART OF A LATER WIN. |
| 規則說明 | ▪ 例：贏分倍數 X{3}，本次中獎用到 X{2} 與 X{5} 的百搭符號，所有連線贏分乘以 X{21}（{3} × ({2} + {5})）。 | ▪ EXAMPLE: WITH A WIN MULTIPLIER OF X{3} AND MULTIPLIER WILDS OF X{2} AND X{5} IN THE WIN, ALL WINS ARE MULTIPLIED BY X{21} ({3} × ({2} + {5})). |

---

## WIN MULTIPLIER FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 贏分倍數特色 | WIN MULTIPLIER FEATURE |
| 規則說明 | ▪ 每次旋轉開始時，贏分倍數為 X{1}。 | ▪ AT THE START OF EACH SPIN, THE WIN MULTIPLIER IS X{1}. |
| 規則說明 | ▪ 每次消除後若再達成連線，贏分倍數依序提升為 X{2}、X{3}、X{5}、X{10}。 | ▪ EACH TIME A NEW WINNING COMBINATION OCCURS AFTER A CASCADE, THE WIN MULTIPLIER INCREASES TO X{2}, X{3}, X{5} AND X{10} IN ORDER. |
| 規則說明 | ▪ 贏分倍數達到 X{10} 後維持不變，直到本次旋轉結束。 | ▪ ONCE THE WIN MULTIPLIER REACHES X{10}, IT STAYS AT X{10} UNTIL THE SPIN ENDS. |

---

## FREE GAME FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 免費遊戲特色 | FREE GAME FEATURE |
| 規則說明 | ▪ 當 {3} 個以上 [C1] 出現在任一位置，即可獲得 {10} 場免費遊戲。 | ▪ {3} OR MORE [C1] APPEARING IN ANY POSITION AWARD {10} FREE SPINS. |
| 規則說明 | ▪ 點擊開始啟動免費遊戲特色。 | ▪ CLICK THE START BUTTON TO START THE FREE GAME FEATURE. |
| 規則說明 | ▪ 在免費遊戲中，{3} 個以上 [C1] 可再獲得 {5} 場免費遊戲，最多可獲得 {50} 場免費遊戲。 | ▪ DURING THE FREE GAME, {3} OR MORE [C1] AWARD {5} MORE FREE SPINS. THE MAXIMUM NUMBER OF FREE SPINS IS {50}. |
| 規則說明 | ▪ 在免費遊戲中，投注與觸發免費遊戲特色時相同。 | ▪ DURING THE FREE GAME, BET PER SPIN REMAINS THE SAME AS WHEN THE FREE GAME FEATURE WAS TRIGGERED. |

### WIN MULTIPLIER FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 贏分倍數特色 | WIN MULTIPLIER FEATURE |
| 規則說明 | ▪ 免費遊戲每次旋轉開始時，贏分倍數為 X{2}。 | ▪ AT THE START OF EACH FREE SPIN, THE WIN MULTIPLIER IS X{2}. |
| 規則說明 | ▪ 每次消除後若再達成連線，贏分倍數依序提升為 X{4}、X{6}、X{10}、X{20}。 | ▪ EACH TIME A NEW WINNING COMBINATION OCCURS AFTER A CASCADE, THE WIN MULTIPLIER INCREASES TO X{4}, X{6}, X{10} AND X{20} IN ORDER. |
| 規則說明 | ▪ 贏分倍數達到 X{20} 後維持不變，直到本次旋轉結束。 | ▪ ONCE THE WIN MULTIPLIER REACHES X{20}, IT STAYS AT X{20} UNTIL THE SPIN ENDS. |

---

## BUY FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 購買特色 | BUY FEATURE |
| 規則說明 | ▪ 點擊「購買特色」按鈕，將開啟「購買特色」選單。 | ▪ BY TAPPING ON THE BUY FEATURE BUTTON, YOU WILL OPEN THE BUY FEATURE MENU. |
| 規則說明 | ▪ 您可以按「+」或「-」按鈕調整投注額與數量。 | ▪ YOU CAN INCREASE OR DECREASE YOUR BET AND QUANTITY BY PRESSING THE "+" OR "-" BUTTONS. |
| 規則說明 | ▪ 以所選投注額的 {50} 倍購買，直接觸發免費遊戲特色。 | ▪ THE FREE GAME FEATURE CAN BE TRIGGERED DIRECTLY BY BUYING IT FOR {50}X THE SELECTED BET. |
| 規則說明 | ▪ 最多可一次購買 {99} 次。 | ▪ THE MAXIMUM SELECTED QUANTITY IS {99}. |
| 規則說明 | ▪ 總價 = 價格 × 數量，顯示在「購買特色」選單中。 | ▪ TOTAL PRICE = PRICE × QUANTITY, WHICH IS DISPLAYED IN THE BUY FEATURE MENU. |
| 規則說明 | ▪ 按下「旋轉」按鈕／「購買並開始遊戲」按鈕後，「購買特色」選單中顯示的價格將從玩家的餘額中扣除。 | ▪ AFTER PRESSING THE SPIN BUTTON / BUY BUTTON, THE PRICE DISPLAYED IN THE BUY FEATURE MENU IS DEDUCTED FROM THE PLAYER'S BALANCE. |
| 規則說明 | ▪ 第一局之後，玩家需按「旋轉」按鈕逐次進行，或點選「自動旋轉」按鈕自動進行剩餘的「購買特色」；剩餘數量為 {0} 時自動旋轉停止。 | ▪ AFTER THE FIRST GAME, THE PLAYER PRESSES THE SPIN BUTTON TO PLAY EACH REMAINING BUY FEATURE, OR TAPS THE AUTO SPIN BUTTON TO PLAY THEM AUTOMATICALLY. AUTO SPIN STOPS WHEN THE REMAINING QUANTITY IS {0}. |
| 規則說明 | ▪ 如果網路中斷／瀏覽器關閉，剩餘的「購買特色」數量將被取消。 | ▪ IN CASE OF NETWORK DISCONNECTION / BROWSER CLOSE, THE REMAINING BUY FEATURE QUANTITY WILL BE CANCELLED. |
| 規則說明 | ▪ 在最後一個「購買特色」完成之前，無法調整投注，也無法取消剩餘的「購買特色」。 | ▪ THE BET CANNOT BE ADJUSTED AND THE REMAINING BUY FEATURE CANNOT BE CANCELLED BEFORE THE LAST BUY FEATURE IS COMPLETED. |
| 規則說明 | ▪ 所有「購買特色」完成後，投注將切換回購買前的投注。 | ▪ AFTER ALL BUY FEATURE ROUNDS ARE COMPLETED, THE BET WILL SWITCH BACK TO THE BET BEFORE THE PURCHASE. |

---

## OP JACKPOT

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | OP JACKPOT | OP JACKPOT |
| 規則說明 | ▪ 在遊戲中，OP JACKPOT 特色由盤面上的 [C1] 隨機觸發。 | ▪ OP JACKPOT FEATURE IS TRIGGERED RANDOMLY BY {1} OR MORE [C1] ON THE REELS. |
| 規則說明 | ▪ OP JACKPOT 特色會在畫面中出現 {12} 個 [幣]，其中包括 [GRAND]、[MAJOR]、[MINOR] 及 [MINI]。 | ▪ DURING OP JACKPOT FEATURE, THERE ARE {12} [COIN] WHICH CONSIST OF [GRAND], [MAJOR], [MINOR] AND [MINI]. |
| 規則說明 | ▪ 選擇 {1} 個 [幣] 以揭示 [GRAND]、[MAJOR]、[MINOR] 或 [MINI]。 | ▪ SELECT A [COIN] TO REVEAL [GRAND], [MAJOR], [MINOR], OR [MINI]. |
| 規則說明 | ▪ 當玩家獲得 {3} 個相同的 OP JACKPOT 特色符號，即可獲得該 OP JACKPOT 並結算總獎金。 | ▪ IF PLAYER GETS {3} SAME JACKPOT SYMBOLS WILL WIN THE JACKPOT AND CALCULATE TOTAL WINNINGS. |
| 規則說明 | ▪ [GRAND] 為連機累進彩金。單場遊戲中，投注選項選擇 {2.00} 以上即可解鎖 [GRAND]。 | ▪ [GRAND] IS LINKED PROGRESSIVE JACKPOT. IF THE SINGLE GAME BET OPTION IS {2.00} OR ABOVE, THE PLAYER WILL UNLOCK [GRAND]. |
| 規則說明 | ▪ [MAJOR] 為連機累進彩金。單場遊戲中，投注選項選擇 {2.00} 以上即可解鎖 [MAJOR]。 | ▪ [MAJOR] IS LINKED PROGRESSIVE JACKPOT. IF THE SINGLE GAME BET OPTION IS {2.00} OR ABOVE, THE PLAYER WILL UNLOCK [MAJOR]. |
| 規則說明 | ▪ [MINOR] 為紅利彩金，依照投注選項改變。 | ▪ [MINOR] WILL CHANGE IF THE PLAYER SELECTS DIFFERENT BET OPTION. |
| 規則說明 | ▪ [MINI] 為紅利彩金，依照投注選項改變。 | ▪ [MINI] WILL CHANGE IF THE PLAYER SELECTS DIFFERENT BET OPTION. |
| 規則說明 | ▪ 玩家投注越高，觸發 OP JACKPOT 特色的機會越高。 | ▪ THE HIGHER BET, THE HIGHER CHANCES TO TRIGGER OP JACKPOT FEATURE. |

--- | --- | --- |
| 主要標題 | OP JACKPOT | OP JACKPOT |
| 規則說明 | 在游戏中，OP JACKPOT 特色由特色转轮上 [C1] 随机触发。 | OP JACKPOT FEATURE IS TRIGGERED RANDOMLY BY {1} OR MORE [C1] ON THE REELS. |
| 規則說明 | OP JACKPOT 特色会在画面中出现 {12} 个 [幣]，其中包括 [GRAND]、[MAJOR]、[MINOR] 及 [MINI]。 | DURING OP JACKPOT FEATURE, THERE ARE {12} [COIN] WHICH CONSIST OF [GRAND], [MAJOR], [MINOR] AND [MINI]. |
| 規則說明 | 选择 {1} 个 [幣] 以揭示 [GRAND]、[MAJOR]、[MINOR] 或 [MINI]。 | SELECT A [COIN] TO REVEAL [GRAND], [MAJOR], [MINOR], OR [MINI]. |
| 規則說明 | 当玩家获得 {3} 个相同的 OP JACKPOT 特色符号即可获得该 OP JACKPOT 并结算总奖金。 | IF PLAYER GETS {3} SAME JACKPOT SYMBOLS WILL WIN THE JACKPOT AND CALCULATE TOTAL WINNINGS. |
| 規則說明 | [GRAND] 为连机累进彩金。单场游戏中，投注选项选择 {2.00} 以上即可解锁 [GRAND]。 | [GRAND] IS LINKED PROGRESSIVE JACKPOT. IF THE SINGLE GAME BET OPTION IS {2.00} OR ABOVE, THE PLAYER WILL UNLOCK [GRAND]. |
| 規則說明 | [MAJOR] 为连机累进彩金。单场游戏中，投注选项选择 {2.00} 以上即可解锁 [MAJOR]。 | [MAJOR] IS LINKED PROGRESSIVE JACKPOT. IF THE SINGLE GAME BET OPTION IS {2.00} OR ABOVE, THE PLAYER WILL UNLOCK [MAJOR]. |
| 規則說明 | [MINOR] 为红利彩金，依照投注选项改变。 | [MINOR] WILL CHANGE IF THE PLAYER SELECTS DIFFERENT BET OPTION. |
| 規則說明 | [MINI] 为红利彩金，依照投注选项改变。 | [MINI] WILL CHANGE IF THE PLAYER SELECTS DIFFERENT BET OPTION. |
| 規則說明 | 玩家投注越高触发 OP JACKPOT 特色的机会越高。 | THE HIGHER BET, THE HIGHER CHANCES TO TRIGGER OP JACKPOT FEATURE. |

---

## WAY GAME

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 最多路數 | MAXIMUM WAYS |
| 規則說明 | ▪ 所有符號必須由最左至右連續出現，方可獲獎。 | ▪ ALL WINS ARE FROM LEFTMOST TO RIGHT ONLY. |
| 規則說明 | ▪ 當同一路有多種獲獎組合，僅會賠付最高的獲獎組合。 | ▪ ONLY THE HIGHEST WIN IS PAID WHEN THERE IS MORE THAN ONE WINNING COMBINATION WITH A CERTAIN SYMBOL. |
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
