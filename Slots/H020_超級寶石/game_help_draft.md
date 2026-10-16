# 101007 Game Help Draft

這份 md 是 `文件/101007_Help.xlsx` 的前置確認稿。
之後若要重產 xlsx，應先確認並修改這份 md，再轉成結構化 spec / xlsx。
底稿：企劃書 `其他/企劃書/H5企劃書_101007_Super Gems 超級寶石.xlsx` 的 `7.Help`；格式比照 H045 的 `game_help_draft.md`；規則以 `game_rule.md` 為準。

## Game Meta

| Field | Value |
| --- | --- |
| game_id | 101007 |
| parsheet_id | H020192A、H020194A |
| name_zh | 超級寶石 |
| name_en | Super Gems |
| game_type | Video Slot - 5 Lines / Feature Reel / Respin / OP Jackpot |

---

## PAYTABLE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 符號賠付值 | SYMBOL PAYOUT VALUES |
| 規則說明 | ▪ 本遊戲為 {3}X{3} 轉輪加上 {1} 個特色轉輪，共有 {5} 條固定賠付線。 | ▪ THIS IS A {3}X{3} SLOT MACHINE WITH AN ADDITIONAL SPECIAL REEL, AND THERE ARE {5} FIXED PAYLINES. |
| 規則說明 | ▪ 所有中獎符號均沿賠付線由左至右計算。 | ▪ ALL WINNING SYMBOLS PAY FROM LEFT TO RIGHT ON SELECTED PAYLINES. |
| 規則說明 | ▪ 每條賠付線只賠付最高的中獎組合。 | ▪ ONLY THE HIGHEST WIN IS PAID ON EACH PAYLINE. |
| 規則說明 | ▪ 多條賠付線同時中獎時，所有獎金相加為總獎金。 | ▪ WHEN WINNING ON MULTIPLE PAYLINES, ALL WINS ARE ADDED TO THE TOTAL WIN. |
| 規則說明 | ▪ 中獎組合與賠付依照賠率表計算。 | ▪ WINNING COMBINATIONS AND PAYS ARE MADE ACCORDING TO THE PAYTABLE. |
| 規則說明 | ▪ 額外投注模式的獎金依一般投注設定計算，並參照賠率表數值。 | ▪ THE WINNING AMOUNT OF THE EXTRA BET MODE WILL BE CALCULATED BASED ON THE NORMAL BET SETTINGS AND REFER TO THE PAYTABLE VALUES. |

### WILD SYMBOL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 百搭符號 | WILD SYMBOL |
| 規則說明 | ▪ [WW] 出現在第 {1}～{3} 輪，可替代所有符號。 | ▪ [WW] APPEARS ON REELS {1} TO {3} AND SUBSTITUTES FOR ALL SYMBOLS. |

### 賠率表

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 賠率表 | PAYTABLE |

繁中：

| 符號 | {3} 連 |
| --- | ---: |
| [WW] | {500} |
| [M1] | {400} |
| [M2] | {300} |
| [M3] | {240} |
| [A] | {200} |
| [K] | {160} |
| [Q] | {100} |
| [J] | {40} |

英文：

| SYMBOL | {3} OF A KIND |
| --- | ---: |
| [WW] | {500} |
| [M1] | {400} |
| [M2] | {300} |
| [M3] | {240} |
| [A] | {200} |
| [K] | {160} |
| [Q] | {100} |
| [J] | {40} |

### SPECIAL REEL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 特色轉輪 | SPECIAL REEL |
| 規則說明 | ▪ 特色轉輪為贏分倍數轉輪，只包含倍數符號與 [重轉球]。 | ▪ THE SPECIAL REEL IS THE WIN MULTIPLIER WHEEL, AND CONTAINS ONLY MULTIPLIER SYMBOLS AND [RESPIN BALL]. |
| 規則說明 | ▪ 所有獎金將乘以特色轉輪中央的倍數，或觸發重轉特色。 | ▪ ALL WINNINGS WILL BE MULTIPLIED BY THE MULTIPLIER AT THE CENTER OF THE SPECIAL REEL OR BY TRIGGERING THE RESPIN FEATURE. |
| 規則說明 | ▪ 盤面有中獎組合且 [重轉球] 停在特色轉輪中央時，觸發重轉特色。 | ▪ LANDING [RESPIN BALL] AT THE CENTER OF THE SPECIAL REEL WITH ANY WINNING COMBINATION WILL TRIGGER THE RESPIN FEATURE. |
| 規則說明 | ▪ [重轉球] 只會出現在特色轉輪。 | ▪ [RESPIN BALL] ONLY APPEARS ON THE SPECIAL REEL. |

### PAYLINES

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 賠付線 | PAYLINES |
| 規則說明 | [賠付線示意圖 3X3] | [PAYLINES DIAGRAM 3X3] |

---

## GAME FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 遊戲特色 | GAME FEATURE |

### RESPIN FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 重轉特色 | RESPIN FEATURE |
| 規則說明 | ▪ 重轉特色中，[重轉球(底圖)] 停在特色轉輪中央時會再次重轉，直到 [重轉球(底圖)] 未停在中央為止。 | ▪ DURING THE RESPIN FEATURE, LANDING [RESPIN BALL (BACKGROUND)] AT THE CENTER OF THE SPECIAL REEL WILL TRIGGER ANOTHER RESPIN, UNTIL [RESPIN BALL (BACKGROUND)] DOES NOT LAND AT THE CENTER. |
| 規則說明 | ▪ 重轉次數最多 {50} 次。 | ▪ THE NUMBER OF RESPINS CAN BE UP TO {50}. |
| 規則說明 | ▪ 收集到的倍數相加，即為本次獎金的最終倍數。 | ▪ THE COLLECTED MULTIPLIERS ARE ADDED TOGETHER TO DETERMINE THE FINAL MULTIPLIER FOR THE CURRENT WIN. |
| 規則說明 | ▪ 一般投注模式共有 {11} 種倍數符號：1X、2X、3X、5X、10X、15X、20X、25X、50X、100X 及 500X。 | ▪ THERE ARE {11} MULTIPLIER SYMBOLS IN NORMAL BET MODE: 1X, 2X, 3X, 5X, 10X, 15X, 20X, 25X, 50X, 100X, AND 500X. |

---

## EXTRA BET

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 額外投注 | EXTRA BET MODE |
| 規則說明 | ▪ 點擊額外投注 OFF-ON 按鈕開啟選單。 | ▪ CLICK EXTRA BET OFF-ON BUTTON TO OPEN THE SELECTION MENU. |
| 規則說明 | ▪ 可選擇以下兩種模式之一： | ▪ SELECT ONE OF THE TWO MODES TO PLAY: |
| 規則說明 | ▪ {1.5} 倍投注：特色轉輪移除 1X 倍數符號，只會出現 2X、3X、5X、10X、15X、20X、25X、50X、100X 及 500X，大幅提高獲得高倍數的機會！ | ▪ WITH A {1.5}X BET, THE 1X MULTIPLIER SYMBOL IS REMOVED FROM THE SPECIAL REEL. ONLY 2X, 3X, 5X, 10X, 15X, 20X, 25X, 50X, 100X, AND 500X WILL APPEAR. THE CHANCE OF WINNING HIGH MULTIPLIERS IS GREATLY INCREASED! |
| 規則說明 | ▪ {8} 倍投注：特色轉輪移除 1X、2X、3X 及 5X 倍數符號，只會出現 10X、15X、20X、25X、50X、100X 及 500X，大幅提高獲得高倍數的機會！ | ▪ WITH AN {8}X BET, THE 1X, 2X, 3X, AND 5X MULTIPLIER SYMBOLS ARE REMOVED FROM THE SPECIAL REEL. ONLY 10X, 15X, 20X, 25X, 50X, 100X, AND 500X WILL APPEAR. THE CHANCE OF WINNING HIGH MULTIPLIERS IS GREATLY INCREASED! |
| 規則說明 | ▪ 在基礎遊戲中，可點擊額外投注 OFF-ON 按鈕切換一般投注與額外投注。 | ▪ THE PLAYER CAN SWITCH BETWEEN THE NORMAL BET AND EXTRA BET DURING THE BASE GAME BY CLICKING EXTRA BET OFF-ON BUTTON. |

---

## SUPER FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 超級特色 | SUPER FEATURE |
| 規則說明 | ▪ 可用 {250} 倍總投注的金額購買超級特色。 | ▪ SUPER FEATURE CAN BE PURCHASED BY USING A VALUE EQUAL TO {250}X TOTAL BET. |
| 規則說明 | ▪ 購買後進行 {5} 次旋轉。 | ▪ TRIGGER {5} SPINS. |
| 規則說明 | ▪ 每次中獎的旋轉，特色轉輪中央的倍數（觸發重轉特色時為收集到的倍數總和）會加入目前的倍數。 | ▪ ON EVERY WINNING SPIN, THE MULTIPLIER AT THE CENTER OF THE SPECIAL REEL (OR THE TOTAL MULTIPLIER COLLECTED IN THE RESPIN FEATURE) IS ADDED TO YOUR CURRENT MULTIPLIER. |
| 規則說明 | ▪ 所有獎金乘以目前的倍數。 | ▪ ALL WINNINGS WILL BE MULTIPLIED BY THE CURRENT MULTIPLIER. |
| 規則說明 | ▪ 倍數會保留到超級特色結束。 | ▪ THE MULTIPLIER WILL STAY UNTIL THE END OF THE SUPER FEATURE. |
| 規則說明 | ▪ 此模式下更容易觸發重轉特色。 | ▪ HIGHER CHANCE TO TRIGGER THE RESPIN FEATURE. |

---

## OP JACKPOT

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | OP JACKPOT | OP JACKPOT |
| 規則說明 | ▪ 在遊戲中，OP JACKPOT 特色由特色轉輪上的 [重轉球] 隨機觸發。 | ▪ OP JACKPOT FEATURE IS TRIGGERED RANDOMLY BY [RESPIN BALL] ON THE SPECIAL REEL. |
| 規則說明 | ▪ OP JACKPOT 特色會在畫面中出現 {12} 個 [幣]，其中包括 [GRAND]、[MAJOR]、[MINOR] 及 [MINI]。 | ▪ DURING OP JACKPOT FEATURE, THERE ARE {12} [COIN] WHICH CONSIST OF [GRAND], [MAJOR], [MINOR] AND [MINI]. |
| 規則說明 | ▪ 選擇 {1} 個 [幣] 以揭示 [GRAND]、[MAJOR]、[MINOR] 或 [MINI]。 | ▪ SELECT A [COIN] TO REVEAL [GRAND], [MAJOR], [MINOR], OR [MINI]. |
| 規則說明 | ▪ 當玩家獲得 {3} 個相同的 OP JACKPOT 特色符號，即可獲得該 OP JACKPOT 並結算總獎金。 | ▪ IF PLAYER GETS {3} SAME JACKPOT SYMBOLS WILL WIN THE JACKPOT AND CALCULATE TOTAL WINNINGS. |
| 規則說明 | ▪ [GRAND] 為連機累進彩金。單場遊戲中，投注選項選擇 {2.00} 以上即可解鎖 [GRAND]。 | ▪ [GRAND] IS LINKED PROGRESSIVE JACKPOT. IF THE SINGLE GAME BET OPTION IS {2.00} OR ABOVE, THE PLAYER WILL UNLOCK [GRAND]. |
| 規則說明 | ▪ [MAJOR] 為連機累進彩金。單場遊戲中，投注選項選擇 {2.00} 以上即可解鎖 [MAJOR]。 | ▪ [MAJOR] IS LINKED PROGRESSIVE JACKPOT. IF THE SINGLE GAME BET OPTION IS {2.00} OR ABOVE, THE PLAYER WILL UNLOCK [MAJOR]. |
| 規則說明 | ▪ [MINOR] 為紅利彩金，依照投注選項改變。 | ▪ [MINOR] WILL CHANGE IF THE PLAYER SELECTS DIFFERENT BET OPTION. |
| 規則說明 | ▪ [MINI] 為紅利彩金，依照投注選項改變。 | ▪ [MINI] WILL CHANGE IF THE PLAYER SELECTS DIFFERENT BET OPTION. |
| 規則說明 | ▪ 玩家投注越高，觸發 OP JACKPOT 特色的機會越高。 | ▪ THE HIGHER BET, THE HIGHER CHANCES TO TRIGGER OP JACKPOT FEATURE. |

---

## GAME RULE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 遊戲規則 | GAME RULES |
| 規則說明 | ▪ 選擇您想要玩的投注選項。 | ▪ SELECT BET OPTION YOU WISH TO PLAY. |
| 規則說明 | ▪ 所有中獎金額均乘以投注選項，除非是累積獎。 | ▪ ALL WINS ARE MULTIPLIED BY BET OPTION EXCEPT PROGRESSIVES BONUSES. |
| 規則說明 | ▪ 遊戲出現故障時，所有賠付與遊戲結果均視為無效。 | ▪ MALFUNCTION VOIDS ALL PAYS AND PLAYS. |
| 規則說明 | ▪ 若玩家在特色遊戲期間中斷連線，系統將自動完成該局結算，並將中獎金額加入餘額。 | ▪ IF THE PLAYER LOSES CONNECTION DURING THE FEATURE GAME, THE SYSTEM WILL CALCULATE THE GAME RESULTS AUTOMATICALLY AND THE WINNING PRIZES WILL BE ADDED INTO THE BALANCE. |
