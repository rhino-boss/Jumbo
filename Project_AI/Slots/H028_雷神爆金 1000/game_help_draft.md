# Game Help Draft

這份 md 是 `Lucky_Cat_Help.xlsx` 的前置確認稿。  
之後若要重產 xlsx，應先確認並修改這份 md，再轉成結構化 spec / xlsx。

## Game Meta

| Field | Value |
| --- | --- |
| game_id | H028 |
| parsheet_id | 待确认 |
| name_zh | 幸运喵掌 |
| name_en | Lucky Cat |

---

## PAYTABLE

來源：rule-derived

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | 符号赔付值 | SYMBOL PAYOUT VALUES |

### WILD SYMBOL

| Item | 简中 | 英文 |
| --- | --- | --- |
| 副標題 | 百搭符号 | WILD SYMBOL |
| 規則說明 | [WW] 仅出现在第 {2}、{3}、{4}、{5} 轮，并可替代除 [SCATTER] 外的所有符号以帮助形成中奖组合。 | [WW] APPEARS ON REELS {2}, {3}, {4}, AND {5} ONLY, AND SUBSTITUTES FOR ALL SYMBOLS EXCEPT [SCATTER] TO HELP FORM WINNING COMBINATIONS. |

### SCATTER SYMBOL

| Item | 简中 | 英文 |
| --- | --- | --- |
| 副標題 | 散布符号 | SCATTER SYMBOL |
| 規則說明 | [SCATTER] 可出现在主盘面任意转轮位置。出现 {4} 个或以上 [SCATTER] 可触发免费游戏。 | [SCATTER] MAY APPEAR ANYWHERE ON THE MAIN REELS. {4} OR MORE [SCATTER] WILL TRIGGER THE FREE GAME FEATURE. |
| 規則說明 | 大型 [SCATTER] 可能覆盖 {2}、{3} 或 {4} 格；触发判定时，每一格均视为 {1} 个 [SCATTER]。 | A LARGE [SCATTER] MAY COVER {2}, {3}, OR {4} POSITIONS, AND EACH POSITION COUNTS AS {1} [SCATTER] WHEN EVALUATING THE TRIGGER. |

### MULTIPLIER SYMBOL

| Item | 简中 | 英文 |
| --- | --- | --- |
| 副標題 | 倍数符号 | MULTIPLIER SYMBOL |
| 規則說明 | [M1] 为倍数符号，可出现在主盘面与额外转轮位置。 | [M1] IS THE MULTIPLIER SYMBOL AND MAY APPEAR ON THE MAIN REELS AND THE EXTRA REELS. |
| 規則說明 | [M1] 不提供一般连线赔付。 | [M1] DOES NOT AWARD A REGULAR LINE WIN. |

### 賠率表

| 中文欄 | 中文欄 | 中文欄 |
| --- | --- | --- |
| 招财猫 {6} - {4} | 招财猫 {5} - {2.5} | 招财猫 {4} - {2} |
| 招财猫 {3} - {1.5} | 日式鼓 {6} - {2.5} | 日式鼓 {5} - {1.5} |
| 日式鼓 {4} - {1.25} | 日式鼓 {3} - {1} | 灯笼 {6} - {2} |
| 灯笼 {5} - {1.5} | 灯笼 {4} - {1.25} | 灯笼 {3} - {0.5} |
| 扇子 {6} - {1.5} | 扇子 {5} - {1} | 扇子 {4} - {0.75} |
| 扇子 {3} - {0.4} | 握寿司 {6} - {0.75} | 握寿司 {5} - {0.6} |
| 握寿司 {4} - {0.5} | 握寿司 {3} - {0.3} | 寿司 {6} - {0.75} |
| 寿司 {5} - {0.6} | 寿司 {4} - {0.5} | 寿司 {3} - {0.3} |
| [A]、[K] {6} - {0.5} | [A]、[K] {5} - {0.4} | [A]、[K] {4} - {0.3} |
| [A]、[K] {3} - {0.2} | [Q]、[J]、[10] {6} - {0.2} | [Q]、[J]、[10] {5} - {0.15} |
| [Q]、[J]、[10] {4} - {0.1} | [Q]、[J]、[10] {3} - {0.05} |  |

英文欄與中文欄相同，xlsx 會左右各放一份完整賠率表。

---

## CASCADING FEATURE

來源：rule-derived

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | 消除特色 | CASCADING FEATURE |
| 規則說明 | 每次结算后，中奖符号会被移除，剩余符号会向下掉落并由新符号补满空位。 | AFTER EACH WIN EVALUATION, WINNING SYMBOLS ARE REMOVED, THE REMAINING SYMBOLS CASCADE DOWN, AND NEW SYMBOLS FILL THE EMPTY POSITIONS. |
| 規則說明 | 盘面补满后会再次结算新的中奖组合，直到不再形成新的中奖组合为止。 | AFTER THE REELS ARE REFILLED, NEW WINNING COMBINATIONS ARE EVALUATED AGAIN. THIS PROCESS CONTINUES UNTIL NO NEW WINNING COMBINATIONS ARE FORMED. |
| 規則說明 | 若金框符号参与中奖并被移除，该位置会直接转为 [WW] 并保留至下一次结算。 | IF A GOLD FRAMED SYMBOL PARTICIPATES IN A WIN AND IS REMOVED, THAT POSITION CHANGES DIRECTLY INTO [WW] AND REMAINS FOR THE NEXT EVALUATION. |

---

## MULTIPLIER FEATURE

來源：rule-derived

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | 倍数特色 | MULTIPLIER FEATURE |
| 規則說明 | [M1] 为本游戏的主要倍数来源；同一回合出现多个 [M1] 时，倍数会累积相加。 | [M1] IS THE MAIN MULTIPLIER SOURCE IN THIS GAME. IF MULTIPLE [M1] SYMBOLS APPEAR IN THE SAME ROUND, THEIR VALUES ARE ADDED TOGETHER. |
| 規則說明 | 主盘面上的 [M1] 依尺寸提供倍数：{1}x{1} = X{2}、{1}x{2} = X{3}、{1}x{3} = X{4}、{1}x{4} = X{5}。 | ON THE MAIN REELS, [M1] AWARDS A MULTIPLIER BASED ON ITS SIZE: {1}X{1} = X{2}, {1}X{2} = X{3}, {1}X{3} = X{4}, AND {1}X{4} = X{5}. |
| 規則說明 | 额外转轮上的每个 [M1] 固定提供 X{2} 倍数。 | EACH [M1] ON THE EXTRA REELS AWARDS A FIXED X{2} MULTIPLIER. |
| 規則說明 | 当局所有中奖金额会乘上该局累积的总倍数。 | ALL WINS IN THE CURRENT ROUND ARE MULTIPLIED BY THE TOTAL ACCUMULATED MULTIPLIER FOR THAT ROUND. |

---

## GOLDEN FRAMED FEATURE

來源：rule-derived

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | 金框符号特色 | GOLDEN FRAMED FEATURE |
| 規則說明 | 第 {2}、{3}、{4}、{5} 轮的一般符号有机会带有金框。 | GENERAL SYMBOLS ON REELS {2}, {3}, {4}, AND {5} MAY APPEAR WITH A GOLD FRAME. |
| 規則說明 | 金框符号只有在实际参与中奖并被移除时，才会在原位置转为 [WW]。 | A GOLD FRAMED SYMBOL ONLY CHANGES INTO [WW] ON THE SAME POSITION AFTER IT ACTUALLY PARTICIPATES IN A WIN AND IS REMOVED. |
| 規則說明 | 转化后的 [WW] 可参与下一次掉落后的中奖判定。 | THE TRANSFORMED [WW] CAN PARTICIPATE IN THE NEXT WIN EVALUATION AFTER THE CASCADE. |

---

## FREE GAME FEATURE

來源：rule-derived

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | 免费游戏特色 | FREE GAME FEATURE |
| 規則說明 | 主盘面任意位置出现 {4} 个或以上 [SCATTER] 时，可触发免费游戏。 | {4} OR MORE [SCATTER] APPEARING ANYWHERE ON THE MAIN REELS WILL TRIGGER THE FREE GAME FEATURE. |
| 規則說明 | {4} 个 [SCATTER] 可获得 {10} 场免费游戏；每多 {1} 个 [SCATTER]，额外增加 {2} 场。 | {4} [SCATTER] AWARD {10} FREE SPINS, AND EACH ADDITIONAL [SCATTER] AWARDS {2} MORE FREE SPINS. |
| 規則說明 | 进入免费游戏时，累积倍数由 X{2} 开始。 | THE ACCUMULATED MULTIPLIER STARTS AT X{2} WHEN THE FREE GAME FEATURE BEGINS. |
| 規則說明 | 免费游戏期间，累积倍数不会在每场之间重置，并会持续保留至整段免费游戏结束。 | DURING FREE GAME, THE ACCUMULATED MULTIPLIER IS NOT RESET BETWEEN SPINS AND IS CARRIED OVER UNTIL THE ENTIRE FEATURE ENDS. |
| 規則說明 | 免费游戏期间仍可再次出现 {4} 个或以上 [SCATTER] 以加局。 | DURING FREE GAME, {4} OR MORE [SCATTER] CAN APPEAR AGAIN TO RETRIGGER ADDITIONAL FREE SPINS. |

### FREE SPINS AWARD

| Item | 简中 | 英文 |
| --- | --- | --- |
| 副標題 | 免费游戏场次 | FREE SPINS AWARD |

### 賠率表

| 中文欄 | 中文欄 | 中文欄 |
| --- | --- | --- |
| {4} SC - {10} FG | {5} SC - {12} FG | {6} SC - {14} FG |

英文欄與中文欄相同，xlsx 會左右各放一份完整賠率表。

---

## BUY FEATURE

來源：rule-derived

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | 购买特色 | BUY FEATURE |
| 規則說明 | 玩家可支付 {75}x 总投注，直接购买一次免费游戏进场机会。 | BUY FEATURE CAN BE PURCHASED FOR {75}X TOTAL BET TO ENTER THE FREE GAME FEATURE DIRECTLY. |
| 規則說明 | 购买后将直接套用一般免费游戏规则与倍数机制。 | AFTER PURCHASE, THE STANDARD FREE GAME RULES AND MULTIPLIER MECHANICS ARE APPLIED DIRECTLY. |

---

## WAY GAME

來源：rule-derived

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | 路数说明 | WAY GAME |
| 規則說明 | 本游戏采用由左至右连续相邻转轮判定的 WAY GAME 玩法。 | THIS GAME USES A WAY GAME MECHANIC THAT PAYS FOR MATCHING SYMBOLS ON CONSECUTIVE ADJACENT REELS FROM LEFT TO RIGHT. |
| 規則說明 | 主盘面为 {6} 轮可变高度盘面，并在第 {2} 至第 {5} 轮上方各配置 {1} 个额外转轮位置。 | THE MAIN REELS CONSIST OF {6} VARIABLE-HEIGHT REELS, WITH {1} EXTRA REEL POSITION ABOVE REELS {2} TO {5}. |
| 規則說明 | 本游戏的路数范围为 {2,025} WAYS 至 {32,400} WAYS。 | THE NUMBER OF WAYS IN THIS GAME RANGES FROM {2,025} WAYS TO {32,400} WAYS. |
| 規則說明 | 大型符号覆盖多个位置时，每一格均视为 {1} 个独立符号参与 WAY 计算。 | WHEN A LARGE SYMBOL COVERS MULTIPLE POSITIONS, EACH POSITION COUNTS AS {1} INDIVIDUAL SYMBOL FOR WAY CALCULATION. |

---

## GAME RULE

來源：mixed（template-copy + rule-derived）

| Item | 简中 | 英文 |
| --- | --- | --- |
| 主要標題 | 游戏规则 | GAME RULES |
| 規則說明 | 选择您想要进行的投注后，主盘面与额外转轮会同步开始旋转。 | AFTER THE PLAYER SELECTS A BET, THE MAIN REELS AND THE EXTRA REELS SPIN TOGETHER. |
| 規則說明 | 中奖组合依 WAY GAME 规则判定，中奖金额会依该局累积的总倍数进行结算。 | WINNING COMBINATIONS ARE EVALUATED BY THE WAY GAME RULE, AND WINS ARE PAID WITH THE TOTAL MULTIPLIER ACCUMULATED IN THAT ROUND. |
| 規則說明 | 游戏出现故障时，所有赔付与游戏结果均视为无效。 | MALFUNCTION VOIDS ALL PAYS AND PLAYS. |
| 規則說明 | 若玩家在免费游戏期间中断连接，系统将自动完成该局结算，并将中奖金额加入余额。 | IF THE PLAYER LOSES CONNECTION DURING THE FREE GAME FEATURE, THE SYSTEM WILL COMPLETE THE RESULT AUTOMATICALLY AND ADD ANY WINNINGS TO THE BALANCE. |
