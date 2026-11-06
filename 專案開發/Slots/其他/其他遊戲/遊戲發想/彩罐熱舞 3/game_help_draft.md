# 彩罐熱舞 3 Game Help Draft（發想，基底 H026）

這份 md 是 `其他/H5企劃書_101014_Pinata Beat 1000_彩罐熱舞.xlsx` 中 `7.Help` 分頁的前置確認稿。
之後若要重產 xlsx，應先確認並修改這份 md，再轉成結構化 spec / xlsx。

## Game Meta

| Field | Value |
| --- | --- |
| game_id | ⏳（發想） |
| parsheet_id | ⏳（發想） |
| name_zh | 彩罐熱舞 3 |
| name_en | Pinata Beat 3 |
| game_type | Video Slot - 20 Lines / Cascade |

---

## PAYTABLE

| Item | 簡中 | 英文 |
| --- | --- | --- |
| 主要標題 | 符号赔付值 | SYMBOL PAYOUT VALUES |

### WILD SYMBOL

| Item | 簡中 | 英文 |
| --- | --- | --- |
| 副標題 | 百搭符号 | WILD SYMBOL |
| 規則說明 | ▪ [WW] 可替代除 [Scatter] 外的所有符号。 | ▪ [WW] SUBSTITUTES FOR ALL SYMBOLS EXCEPT [Scatter]. |

### SCATTER SYMBOL

| Item | 簡中 | 英文 |
| --- | --- | --- |
| 副標題 | 散布符号 | SCATTER SYMBOL |
| 規則說明 | ▪ 當本次旋轉連消結束後，若最終盤面出現 {3} 個或以上 [C1]，將觸發免費遊戲。 | ▪ WHEN ALL CASCADES ARE COMPLETE, {3} OR MORE [C1] ON THE FINAL REELS WILL TRIGGER THE FREE GAME FEATURE. |

### 賠率表

| Item | 簡中 | 英文 |
| --- | --- | --- |
| 副標題 | 賠率表 | PAYTABLE |

| 中文欄 | 中文欄 | 中文欄 |
| --- | --- | --- |
| [M1] 5 - 5000 | [M2] 5 - 2000 | [M3] 5 - 1000 |
| [M1] 4 - 1250 | [M2] 4 - 500 | [M3] 4 - 250 |
| [M1] 3 - 250 | [M2] 3 - 100 | [M3] 3 - 75 |
| [M4] 5 - 750 | [M5] 5 - 500 | [A] 5 - 250 |
| [M4] 4 - 200 | [M5] 4 - 100 | [A] 4 - 50 |
| [M4] 3 - 50 | [M5] 3 - 25 | [A] 3 - 10 |
| [K] 5 - 250 | [Q] 5 - 250 | [J] 5 - 250 |
| [K] 4 - 50 | [Q] 4 - 50 | [J] 4 - 50 |
| [K] 3 - 10 | [Q] 3 - 10 | [J] 3 - 10 |

---

## CASCADING FEATURE

| Item | 簡中 | 英文 |
| --- | --- | --- |
| 主要標題 | 消除特色 | CASCADING FEATURE |
| 規則說明 | ▪ 每輪結算後，中獎符號會被消除；消除後產生的空格由上方符號向下掉落補位。 | ▪ AFTER EACH WIN EVALUATION, WINNING SYMBOLS ARE REMOVED AND THE SYMBOLS ABOVE FALL DOWN TO FILL THE EMPTY POSITIONS. |
| 規則說明 | ▪ 補牌後會再次檢查新的中獎組合，直到不再形成新的中獎組合為止。 | ▪ AFTER THE SYMBOLS CASCADE DOWN, NEW WINNING COMBINATIONS ARE EVALUATED AGAIN. THIS PROCESS REPEATS UNTIL NO NEW WINNING COMBINATIONS ARE FORMED. |

---

## GOLDEN SYMBOL FEATURE

| Item | 簡中 | 英文 |
| --- | --- | --- |
| 主要標題 | 金色符号特色 | GOLDEN SYMBOL FEATURE |
| 規則說明 | ▪ 所有轉輪都可能出現金色符號，金色符號與原始符號具有相同的基礎賠率。 | ▪ GOLDEN SYMBOLS MAY APPEAR ON ALL REELS AND PAY THE SAME AS THEIR ORIGINAL SYMBOL. |
| 規則說明 | ▪ 金色符號參與中獎後，該位置會保留並轉化為 [WW]。 | ▪ WHEN A GOLDEN SYMBOL IS PART OF A WIN, THAT POSITION REMAINS ON THE REELS AND CHANGES INTO [WW]. |

---

## MULTIPLIER FRAME FEATURE

| Item | 簡中 | 英文 |
| --- | --- | --- |
| 主要標題 | 倍数框特色 | MULTIPLIER FRAME FEATURE |
| 規則說明 | ▪ 金色符號轉化為 [WW] 時，該位置若沒有倍數框則產生 {×1} 倍數框；若已有倍數框則再疊加一層。 | ▪ WHEN A GOLDEN SYMBOL CHANGES INTO [WW], A {×1} MULTIPLIER FRAME IS CREATED ON THAT POSITION, OR ONE MORE LAYER IS ADDED IF A FRAME IS ALREADY THERE. |
| 規則說明 | ▪ 金色符號停在某個位置時，該位置若沒有倍數框則產生 {×1} 倍數框；若已有倍數框則疊加一層。 | ▪ WHEN A GOLDEN SYMBOL LANDS ON A POSITION, A {×1} MULTIPLIER FRAME IS CREATED THERE, OR ONE MORE LAYER IS ADDED IF A FRAME IS ALREADY THERE. |
| 規則說明 | ▪ 每疊加一層倍數加倍：{×1}、{×2}、{×4}、{×8} … 最高 {×1024}。 | ▪ EACH LAYER DOUBLES THE FRAME MULTIPLIER: {×1}, {×2}, {×4}, {×8} … UP TO {×1024}. |
| 規則說明 | ▪ 每次消除的贏分都會乘上盤面上所有倍數框的倍數總和。 | ▪ EVERY CASCADE WIN IS MULTIPLIED BY THE SUM OF ALL MULTIPLIER FRAMES ON THE REELS. |
| 規則說明 | ▪ 主遊戲每次旋轉開始時清除所有倍數框。 | ▪ ALL MULTIPLIER FRAMES ARE CLEARED AT THE START OF EACH BASE GAME SPIN. |

---

## FREE GAME FEATURE

| Item | 簡中 | 英文 |
| --- | --- | --- |
| 主要標題 | 免费游戏特色 | FREE GAME FEATURE |
| 規則說明 | ▪ 当本次旋转连消结束后，若最终盘面出现 {3}、{4} 或 {5} 个 [Scatter]，即可触发免费游戏，分别获得 {12}、{14} 或 {16} 场免费游戏。 | ▪ WHEN ALL CASCADES ARE COMPLETE, IF THE FINAL REELS SHOW {3}, {4}, OR {5} [C1], THE FREE GAME FEATURE IS TRIGGERED WITH {12}, {14}, OR {16} FREE SPINS RESPECTIVELY. |
| 規則說明 | ▪ 免費遊戲期間，倍數框不會清除，會持續保留到整段免費遊戲結束。 | ▪ DURING FREE GAME, MULTIPLIER FRAMES ARE NOT CLEARED BETWEEN SPINS AND REMAIN UNTIL THE ENTIRE FREE GAME ENDS. |
| 規則說明 | ▪ 單次進入免費遊戲後，包含加局在內，最多進行 {50} 場。 | ▪ AFTER ENTERING THE FREE GAME, INCLUDING RETRIGGERING, THE MAXIMUM NUMBER OF FREE SPINS IS {50}. |
| 規則說明 | ▪ 免費遊戲可加局。加局條件與一般觸發相同：{3}、{4} 或 {5} 個 [C1] 分別對應加 {12}、{14} 或 {16} 場免費遊戲。 | ▪ FREE GAME CAN BE RETRIGGERED. RETRIGGERING FOLLOWS THE SAME CONDITIONS: {3}, {4}, OR {5} [C1] WILL ADD {12}, {14}, OR {16} FREE SPINS RESPECTIVELY. |

---

## BUY FEATURE

| Item | 簡中 | 英文 |
| --- | --- | --- |
| 主要標題 | 购买特色 | BUY FEATURE |
| 規則說明 | ▪ 玩家可支付 {75}x 投注，直接购买进入一次免费游戏。 | ▪ BUY FEATURE CAN BE PURCHASED BY USING A VALUE EQUAL TO {75}X TOTAL BET. |
| 規則說明 | ▪ 购买后直接觸發免费游戏规格。 | ▪ PURCHASING THE BUY FEATURE GUARANTEES ENTRY INTO FREE GAME. |

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

## LINE GAME

| Item | 簡中 | 英文 |
| --- | --- | --- |
| 主要標題 | 赔线说明 | LINE GAME |
| 規則說明 | ▪ 本游戏共有 {20} 条固定赔线。 | ▪ THE GAME HAS {20} FIXED PAY LINES. |
| 規則說明 | ▪ 中獎組合必須由最左側開始，由左至右連續出現才算中獎。 | ▪ WINNING COMBINATIONS MUST START FROM THE LEFTMOST REEL AND RUN CONSECUTIVELY FROM LEFT TO RIGHT. |
| 規則說明 | ▪ 单一赔线仅支付最高奖项。 | ▪ ONLY THE HIGHEST WIN PER LINE IS PAID. |
| 規則說明 | ▪ [走線圖 20 LINE] | ▪ [走線圖 20 LINE] |

---

## GAME RULE

| Item | 簡中 | 英文 |
| --- | --- | --- |
| 主要標題 | 游戏规则 | GAME RULES |
| 規則說明 | ▪ 选择您想要玩的投注选项。 | ▪ SELECT BET OPTION YOU WISH TO PLAY. |
| 規則說明 | ▪ 所有中奖金额均乘以投注选项，除非是累积奖。 | ▪ ALL WINS ARE MULTIPLIED BY BET OPTION EXCEPT PROGRESSIVES BONUSES. |
| 規則說明 | ▪ 游戏出现故障，所有赔付和游戏都视为无效。 | ▪ MALFUNCTION VOIDS ALL PAYS AND PLAYS. |
| 規則說明 | ▪ 若玩家在免费游戏特色期间中断游戏，系统将会自动计算游戏结果，并将获奖金额加入至余额中。 | ▪ IF THE PLAYER LOSES CONNECTION DURING THE FREE GAME FEATURE, THE SYSTEM WILL CALCULATE THE GAME RESULTS AUTOMATICALLY AND THE WINNING PRIZES WILL BE ADDED INTO THE BALANCE. |
