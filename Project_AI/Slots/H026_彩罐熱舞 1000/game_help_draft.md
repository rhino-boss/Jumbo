# 101014 Game Help Draft

這份 md 是 `Pinata_Beat_1000_Help.xlsx` 的前置確認稿。  
之後若要重產 xlsx，應先確認並修改這份 md，再轉成結構化 spec / xlsx。

## Game Meta

| Field | Value |
| --- | --- |
| game_id | 101014 |
| parsheet_id | H0261 |
| name_zh | 彩罐热舞 |
| name_en | Pinata Beat 1000 |

---

## PAYTABLE

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | 符号赔付值 | SYMBOL PAYOUT VALUES |

### WILD SYMBOL

| Item | 简中 | 英文 |
| --- | --- | --- |
| 副標題 | 百搭符号 | WILD SYMBOL |
| 規則說明 | [WW] 可替代一般符号并帮助形成中奖组合。 | [WW] SUBSTITUTES FOR REGULAR SYMBOLS TO HELP FORM WINNING COMBINATIONS. |

### SCATTER SYMBOL

| Item | 简中 | 英文 |
| --- | --- | --- |
| 副標題 | 散布符号 | SCATTER SYMBOL |
| 規則說明 | 当本次旋转连消结束后，若最终盘面出现 {3} 个或以上 [C1]，将触发免费游戏。 | WHEN ALL CASCADES ARE COMPLETE, {3} OR MORE [C1] ON THE FINAL REELS WILL TRIGGER THE FREE GAME FEATURE. |

### 賠率表

| 中文欄 | 中文欄 | 中文欄 |
| --- | --- | --- |
| [M1] 5 - 50 | [M2] 5 - 20 | [M3] 5 - 10 |
| [M1] 4 - 12.5 | [M2] 4 - 5 | [M3] 4 - 2.5 |
| [M1] 3 - 2.5 | [M2] 3 - 1 | [M3] 3 - 0.75 |
| [M4] 5 - 7.5 | [M5] 5 - 5 | [A] 5 - 2.5 |
| [M4] 4 - 2 | [M5] 4 - 1 | [A] 4 - 0.5 |
| [M4] 3 - 0.5 | [M5] 3 - 0.25 | [A] 3 - 0.1 |
| [K] 5 - 2.5 | [Q] 5 - 2.5 | [J] 5 - 2.5 |
| [K] 4 - 0.5 | [Q] 4 - 0.5 | [J] 4 - 0.5 |
| [K] 3 - 0.1 | [Q] 3 - 0.1 | [J] 3 - 0.1 |

英文欄與中文欄相同，xlsx 會左右各放一份完整賠率表。

---

## CASCADING FEATURE

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | 消除特色 | CASCADING FEATURE |
| 規則說明 | 每轮结算后，中奖符号会被消除；消除后产生的空格由上方符号向下掉落补位。 | AFTER EACH WIN EVALUATION, WINNING SYMBOLS ARE REMOVED AND THE SYMBOLS ABOVE FALL DOWN TO FILL THE EMPTY POSITIONS. |
| 規則說明 | 若前一轮中奖组合中含有金框符号，该位置会保留并转化为 [WW]，因此不视为空格。 | IF THE PREVIOUS WINNING COMBINATION INCLUDES A GOLD FRAMED SYMBOL, THAT POSITION REMAINS ON THE REELS AND CHANGES INTO [WW], SO IT IS NOT TREATED AS AN EMPTY POSITION. |
| 規則說明 | 补牌后会再次检查新的中奖组合，直到不再形成新的中奖组合为止。 | AFTER THE SYMBOLS CASCADE DOWN, NEW WINNING COMBINATIONS ARE EVALUATED AGAIN. THIS PROCESS REPEATS UNTIL NO NEW WINNING COMBINATIONS ARE FORMED. |

---

## MULTIPLIER FEATURE

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | 倍数特色 | MULTIPLIER FEATURE |
| 規則說明 | 金框符号可能附带倍数。倍数等级为：X{2}、X{3}、X{5}、X{8}、X{10}、X{15}、X{20}、X{25}、X{50}、X{100}、X{500}、X{1000}。 | GOLD FRAMED SYMBOLS MAY CARRY A MULTIPLIER VALUE. THE MULTIPLIER LEVELS ARE: X{2}, X{3}, X{5}, X{8}, X{10}, X{15}, X{20}, X{25}, X{50}, X{100}, X{500}, AND X{1000}. |
| 規則說明 | 仅当带倍数的金框符号实际参与得分并被消除时，其倍数才会被收集并累积。 | THE MULTIPLIER IS ONLY COLLECTED AND ADDED TO THE ACCUMULATED TOTAL WHEN THE GOLD FRAMED SYMBOL WITH A MULTIPLIER ACTUALLY PARTICIPATES IN A WIN AND IS CLEARED. |
| 規則說明 | 当本次旋转无法再消除时，若本次旋转有实际收集到倍数，则将当前累积总倍数乘上本次旋转的总赢分。 | WHEN NO MORE CASCADES CAN OCCUR, IF ANY MULTIPLIER WAS COLLECTED DURING THIS SPIN, THE TOTAL ACCUMULATED MULTIPLIER IS APPLIED TO THE TOTAL WIN OF THIS SPIN. |

---

## GOLDEN FRAMED FEATURE

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | 金框符号 | GOLDEN FRAMED FEATURE |
| 規則說明 | 第 {2}、{3}、{4} 轮的一般符号有机会带有金框。 | GENERAL SYMBOLS ON REELS {2}, {3}, AND {4} MAY APPEAR WITH A GOLD FRAME. |
| 規則說明 | 金框符号与原始符号具有相同的基础赔率。 | GOLD FRAMED SYMBOLS PAY THE SAME AS THEIR ORIGINAL SYMBOLS. |
| 規則說明 | 主游戏中，第 {3} 轮有机会随机出现整列带倍数的金框符号；免费游戏中，第 {3} 轮必定为整列带倍数的金框符号。 | IN THE BASE GAME, REEL {3} MAY RANDOMLY APPEAR AS AN ENTIRE REEL OF GOLD FRAMED SYMBOLS WITH MULTIPLIERS. DURING FREE GAME, REEL {3} IS GUARANTEED TO BE AN ENTIRE REEL OF GOLD FRAMED SYMBOLS WITH MULTIPLIERS. |
| 規則說明 | 若金框符号参与得分并被消除，该位置会在下一轮转化为 [WW]。 | IF A GOLD FRAMED SYMBOL PARTICIPATES IN A WIN AND IS CLEARED, THAT POSITION IS TRANSFORMED INTO [WW] IN THE NEXT ROUND. |

---

## FREE GAME FEATURE

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | 免费游戏特色 | FREE GAME FEATURE |
| 規則說明 | 当本次旋转连消结束后，若最终盘面出现 {3}、{4} 或 {5} 个 [C1]，将触发免费游戏，并分别获得 {15}、{17} 或 {19} 场免费游戏。 | WHEN ALL CASCADES ARE COMPLETE, IF THE FINAL REELS SHOW {3}, {4}, OR {5} [C1], THE FREE GAME FEATURE IS TRIGGERED WITH {15}, {17}, OR {19} FREE SPINS RESPECTIVELY. |
| 規則說明 | 免费游戏期间，累积倍数不会重置，并会持续保留到整段免费游戏结束。 | DURING FREE GAME, THE ACCUMULATED MULTIPLIER IS NOT RESET BETWEEN SPINS AND IS CARRIED OVER UNTIL THE ENTIRE FREE GAME ENDS. |
| 規則說明 | 免费游戏期间，第 {3} 轮的一般符号必定带有金框与倍数。 | DURING FREE GAME, GENERAL SYMBOLS ON REEL {3} ARE GUARANTEED TO APPEAR WITH GOLD FRAMES AND MULTIPLIERS. |
| 規則說明 | 单次进入免费游戏后，包含加局在内，最多进行 {50} 场。 | AFTER ENTERING THE FREE GAME, INCLUDING RETRIGGERING, THE MAXIMUM NUMBER OF FREE SPINS IS {50}. |
| 規則說明 | 免费游戏可加局。加局条件与一般触发相同：{3}、{4} 或 {5} 个 [C1] 分别对应加 {15}、{17} 或 {19} 场免费游戏。 | FREE GAME CAN BE RETRIGGERED. RETRIGGERING FOLLOWS THE SAME CONDITIONS: {3}, {4}, OR {5} [C1] WILL ADD {15}, {17}, OR {19} FREE SPINS RESPECTIVELY. |

---

## EXTRA BET

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | 额外投注 | EXTRA BET |
| 規則說明 | 玩家可选择额外投注模式进行旋转。 | THE PLAYER MAY SELECT THE EXTRA BET MODE. |
| 規則說明 | 额外投注的价格为 {2}x 总投注。 | EXTRA BET COSTS {2}X TOTAL BET. |
| 規則說明 | 额外投注沿用相同的主游戏、连消与免费游戏流程。 | EXTRA BET USES THE SAME BASE GAME, CASCADING, AND FREE GAME FLOW. |
| 規則說明 | 额外投注的投注金额为 {2}x 总投注，并可提高触发免费游戏的机会。 | EXTRA BET COSTS {2}X TOTAL BET AND INCREASES THE CHANCE TO TRIGGER THE FREE GAME FEATURE. |

---

## BUY FEATURE

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | 购买特色 | BUY FEATURE |
| 規則說明 | 玩家可支付 {75}x 总投注，购买一次免费游戏进场机会。 | BUY FEATURE CAN BE PURCHASED BY USING A VALUE EQUAL TO {75}X TOTAL BET. |
| 規則說明 | 购买免费游戏特色后即可进入免费游戏。 | PURCHASING THE FREE GAME FEATURE GUARANTEES FREE GAME. |
| 規則說明 | 进场旋转的得分会保留，并与后续免费游戏总得分一并结算。 | WINS FROM THE TRIGGER SPIN ARE KEPT AND PAID TOGETHER WITH THE TOTAL WIN FROM THE FREE GAME FEATURE. |

---

## OP JACKPOT

來源說明：
- 文案骨架目前取自 `H000_範例/文件/101010_Help.xlsx` 的 `OP JACKPOT` 區塊
- 這款 `101014` 的 jackpot 類型來自 `Game List_Online.xlsx`
- `game_rule.md` 目前未記載 OP Jackpot 細節，以下內容暫列為待確認版本

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | OP JACKPOT | OP JACKPOT |
| 規則說明 | ▪ 在游戏中，OP JACKPOT 特色由特色转轮上 [C1] 随机触发。 | ▪ OP JACKPOT FEATURE IS TRIGGERED RANDOMLY BY {1} OR MORE [C1] ON THE REELS. |
| 規則說明 | ▪ OP JACKPOT 特色会在画面中出现 {12} 个 [幣]，其中包括 [GRAND]、[MAJOR]、[MINOR] 及 [MINI]。 | ▪ DURING OP JACKPOT FEATURE, THERE ARE {12} [COIN] WHICH CONSIST OF [GRAND], [MAJOR], [MINOR] AND [MINI]. |
| 規則說明 | ▪ 选择 {1} 个 [幣] 以揭示 [GRAND]、[MAJOR]、[MINOR] 或 [MINI]。 | ▪ SELECT A [COIN] TO REVEAL [GRAND], [MAJOR], [MINOR], OR [MINI]. |
| 規則說明 | ▪ 当玩家获得 {3} 个相同的 OP JACKPOT 特色符号，即可获得该 OP JACKPOT 并结算总奖金。 | ▪ IF PLAYER GETS {3} SAME JACKPOT SYMBOLS WILL WIN THE JACKPOT AND CALCULATE TOTAL WINNINGS. |
| 規則說明 | ▪ [GRAND] 为连机累进彩金。单场游戏中，投注选项选择 {2.00} 以上即可解锁 [GRAND]。 | ▪ [GRAND] IS LINKED PROGRESSIVE JACKPOT. IF THE SINGLE GAME BET OPTION IS {2.00} OR ABOVE, THE PLAYER WILL UNLOCK [GRAND]. |
| 規則說明 | ▪ [MAJOR] 为连机累进彩金。单场游戏中，投注选项选择 {2.00} 以上即可解锁 [MAJOR]。 | ▪ [MAJOR] IS LINKED PROGRESSIVE JACKPOT. IF THE SINGLE GAME BET OPTION IS {2.00} OR ABOVE, THE PLAYER WILL UNLOCK [MAJOR]. |
| 規則說明 | ▪ [MINOR] 为红利彩金，依照投注选项改变。 | ▪ [MINOR] WILL CHANGE IF THE PLAYER SELECTS DIFFERENT BET OPTION. |
| 規則說明 | ▪ [MINI] 为红利彩金，依照投注选项改变。 | ▪ [MINI] WILL CHANGE IF THE PLAYER SELECTS DIFFERENT BET OPTION. |
| 規則說明 | ▪ 玩家投注越高，触发 OP JACKPOT 特色的机会越高。 | ▪ THE HIGHER THE PLAYER BETS, THE HIGHER THE CHANCE TO TRIGGER THE OP JACKPOT FEATURE. |

---

## LINE GAME

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | 赔线说明 | LINE GAME |
| 規則說明 | 本游戏共有 {20} 条固定赔线。 | THE GAME HAS {20} FIXED PAY LINES. |
| 規則說明 | 中奖组合必须由最左侧开始，由左至右连续出现才算中奖。 | WINNING COMBINATIONS MUST START FROM THE LEFTMOST REEL AND RUN CONSECUTIVELY FROM LEFT TO RIGHT. |
| 規則說明 | 单一赔线仅支付最高奖项。 | ONLY THE HIGHEST WIN PER PAY LINE IS PAID. |
| 規則說明 | [走线图 20 LINE] | [PAYLINE DIAGRAM 20 LINE] |
| 規則說明 | 请参考走线图了解 {20} 条固定赔线的连线方式。 | PLEASE REFER TO THE PAYLINE DIAGRAM FOR THE {20} FIXED PAY LINE PATTERNS. |

---

## GAME RULE

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | 游戏规则 | GAME RULES |
| 規則說明 | 选择您想要玩的投注选项。 | SELECT BET OPTION YOU WISH TO PLAY. |
| 規則說明 | 所有中奖金额均乘以投注选项，除非是累积奖。 | ALL WINS ARE MULTIPLIED BY BET OPTION EXCEPT PROGRESSIVES BONUSES. |
| 規則說明 | 游戏出现故障，所有赔付和游戏都视为无效。 | MALFUNCTION VOIDS ALL PAYS AND PLAYS. |
| 規則說明 | 若玩家在免费游戏特色期间中断游戏，系统将会自动计算游戏结果，并将获奖金额加入至余额中。 | IF THE PLAYER LOSES CONNECTION DURING THE FREE GAME FEATURE, THE SYSTEM WILL CALCULATE THE GAME RESULTS AUTOMATICALLY AND THE WINNING PRIZES WILL BE ADDED INTO THE BALANCE. |
