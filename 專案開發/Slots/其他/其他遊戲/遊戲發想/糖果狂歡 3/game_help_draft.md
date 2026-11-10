# 糖果狂歡 3 Sugar Bonanza 3 — Help Draft（發想，基底 H013）

本文件為 Demo Game 內遊戲說明的繁體中文／英文對照稿。賠率與模式成本以目前選擇的 `config_92A.js`／`config_94A.js` 及 `Simulator.py` 實際執行值為準；網頁會依玩家目前選擇的押注即時換算派彩金額。

## Game Meta

| Field | Value |
| --- | --- |
| game_id | ⏳ |
| parsheet_id | ⏳ |
| name_zh | 糖果狂歡 3 |
| name_en | Sugar Bonanza 3 |
| game_type | Video Slot - Pay Anywhere / Cascade / Multiplier |
| board | 6 reels × 5 rows |
| modes | Normal Bet / Extra Bet (1.25x) / Feature Buy (100x) / Super Feature (500x) |
| runtime_note | Feature Buy 依主 Overview、目前 config 與 Simulator 的實際執行值顯示為 100x。 |

---

## PAYTABLE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 符號賠付值 | SYMBOL PAYOUT VALUES |
| 規則說明 | 同一個一般符號在盤面任意位置出現 8 個或以上即可得獎，符號不必相鄰或連線。 | EIGHT OR MORE MATCHING REGULAR SYMBOLS ANYWHERE ON THE GRID AWARD A WIN. SYMBOLS DO NOT NEED TO BE ADJACENT OR CONNECTED. |
| 規則說明 | 以下派彩金額會依目前選擇的押注即時換算。 | THE PAYOUT AMOUNTS BELOW ARE CALCULATED FROM THE CURRENTLY SELECTED BET. |

### 賠率表

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 賠率表 | PAYTABLE |
| [M1] 12+ - 5000 | [M2] 12+ - 2500 | [M3] 12+ - 1500 |
| [M1] 10–11 - 2500 | [M2] 10–11 - 1000 | [M3] 10–11 - 500 |
| [M1] 8–9 - 1000 | [M2] 8–9 - 250 | [M3] 8–9 - 200 |
| [M4] 12+ - 1200 | [A] 12+ - 1000 | [K] 12+ - 800 |
| [M4] 10–11 - 200 | [A] 10–11 - 150 | [K] 10–11 - 120 |
| [M4] 8–9 - 150 | [A] 8–9 - 100 | [K] 8–9 - 80 |
| [Q] 12+ - 500 | [J] 12+ - 400 | [TE] 12+ - 200 |
| [Q] 10–11 - 100 | [J] 10–11 - 90 | [TE] 10–11 - 75 |
| [Q] 8–9 - 50 | [J] 8–9 - 40 | [TE] 8–9 - 25 |

### SCATTER SYMBOL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 分散符號 | SCATTER SYMBOL |
| 規則說明 | [C1] 為分散符號。主遊戲的所有消除結束後，最終盤面出現 4、5 或 6 個 [C1] 時，分別支付 3x、5x 或 100x 押注。 | [C1] IS THE SCATTER SYMBOL. AFTER ALL BASE GAME CASCADES END, 4, 5, OR 6 [C1] ON THE FINAL GRID PAY 3X, 5X, OR 100X BET RESPECTIVELY. |
| [C1] 6 - 10000 | [C1] 5 - 500 | [C1] 4 - 300 |

---

## CASCADING FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 消除掉落特色 | CASCADING FEATURE |
| 規則說明 | 每次得獎後，得獎符號會被消除；其餘符號向下掉落，並由上方補入新符號。 | AFTER EACH WIN, WINNING SYMBOLS ARE REMOVED. THE REMAINING SYMBOLS DROP DOWN AND NEW SYMBOLS ENTER FROM ABOVE. |
| 規則說明 | 只要新盤面再次形成得獎，消除掉落便會繼續，直到不再形成新得獎。 | CASCADES CONTINUE WHILE NEW WINS ARE FORMED AND END WHEN NO NEW WIN REMAINS. |

---

## CORNER FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 四角特色 | CORNER FEATURE |
| 規則說明 | 每次旋轉開始時，盤面四個角會出現同一種一般符號；四個角不隨消除掉落，消除後只會補回同一種符號。 | AT THE START OF EACH SPIN, THE FOUR CORNERS OF THE GRID SHOW THE SAME REGULAR SYMBOL. CORNER POSITIONS DO NOT DROP DURING CASCADES AND ARE ONLY REFILLED WITH THAT SAME SYMBOL. |
| 規則說明 | 當四個角的符號全部被消除時，四個角各出現 1 個 [C2]，並保留到本次旋轉結束；同一次旋轉只會觸發一次。 | WHEN ALL FOUR CORNER SYMBOLS ARE REMOVED, EACH CORNER BECOMES A [C2] THAT STAYS UNTIL THE END OF THE SPIN. THIS CAN HAPPEN ONLY ONCE PER SPIN. |
| 規則說明 | 主遊戲四角出現的 [C2] 倍數為 X{1}、X{2}、X{3} 或 X{5}；免費遊戲中依該局倍數權重取得。 | IN THE BASE GAME, CORNER [C2] MULTIPLIERS ARE X{1}, X{2}, X{3}, OR X{5}; IN FREE GAMES THEY FOLLOW THAT FREE GAME'S MULTIPLIER WEIGHTS. |

---

## MULTIPLIER FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 倍數炸彈特色 | MULTIPLIER BOMB FEATURE |
| 規則說明 | 免費遊戲中，每個 [C2] 會分別取得一個倍數值。 | DURING FREE GAMES, EACH [C2] RECEIVES A MULTIPLIER VALUE. |
| 規則說明 | 可出現的倍數為 X{2}、X{3}、X{4}、X{5}、X{6}、X{8}、X{10}、X{12}、X{15}、X{20}、X{25}、X{50}、X{100} 或 X{1000}。 | AVAILABLE MULTIPLIERS ARE X{2}, X{3}, X{4}, X{5}, X{6}, X{8}, X{10}, X{12}, X{15}, X{20}, X{25}, X{50}, X{100}, OR X{1000}. |
| 規則說明 | 每次旋轉（含主遊戲）所有消除結束後，最終盤面上的 [C2] 倍數會相加；該次旋轉的所有一般符號得獎均乘以倍數總和。若最終盤面沒有 [C2]，則使用 X{1}。 | AFTER ALL CASCADES IN A SPIN (INCLUDING THE BASE GAME) END, THE [C2] MULTIPLIERS ON THE FINAL GRID ARE ADDED TOGETHER. ALL REGULAR-SYMBOL WINS FROM THAT SPIN ARE MULTIPLIED BY THE TOTAL. IF NO [C2] REMAINS, X{1} APPLIES. |

---

## FREE GAME FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 免費遊戲特色 | FREE GAME FEATURE |
| 規則說明 | 主遊戲的所有消除結束後，最終盤面出現 4 個或以上 [C1]，即可觸發 10 次免費遊戲。 | AFTER ALL BASE GAME CASCADES END, 4 OR MORE [C1] ON THE FINAL GRID TRIGGER 10 FREE GAMES. |
| 規則說明 | 每組 10 次免費遊戲由 8 次一般免費遊戲與 2 次高階免費遊戲組成，實際出現順序會隨機排列。 | EACH SET OF 10 FREE GAMES CONSISTS OF 8 REGULAR FREE GAMES AND 2 HIGH-TIER FREE GAMES, PRESENTED IN RANDOM ORDER. |
| 規則說明 | 免費遊戲的所有消除結束後，最終盤面出現 3 個或以上 [C1]，會增加 5 次免費遊戲，其中包含 4 次一般免費遊戲與 1 次高階免費遊戲。 | AFTER ALL CASCADES IN A FREE GAME END, 3 OR MORE [C1] ON THE FINAL GRID ADD 5 FREE GAMES, CONSISTING OF 4 REGULAR FREE GAMES AND 1 HIGH-TIER FREE GAME. |
| 規則說明 | 單次免費遊戲特色最多進行 50 次免費遊戲。 | A SINGLE FREE GAME FEATURE IS CAPPED AT 50 FREE GAMES. |

---

## BET OPTIONS

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 投注模式 | BET OPTIONS |
| 規則說明 | 一般投注的成本為目前選擇押注的 1x。 | NORMAL BET COSTS 1X THE CURRENTLY SELECTED BET. |
| 規則說明 | 額外投注的成本為目前選擇押注的 1.25x，並使用提高特色觸發機會的專用盤帶設定。 | EXTRA BET COSTS 1.25X THE CURRENTLY SELECTED BET AND USES DEDICATED REEL SETTINGS WITH A HIGHER FEATURE CHANCE. |
| 規則說明 | 購買特色的成本為目前選擇押注的 100x，並直接進入免費遊戲特色。 | FEATURE BUY COSTS 100X THE CURRENTLY SELECTED BET AND ENTERS THE FREE GAME FEATURE DIRECTLY. |
| 規則說明 | 超級特色的成本為目前選擇押注的 500x，並直接進入使用強化倍數權重的免費遊戲特色。 | SUPER FEATURE COSTS 500X THE CURRENTLY SELECTED BET AND ENTERS A FREE GAME FEATURE WITH ENHANCED MULTIPLIER WEIGHTS. |

---

## GAME RULE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 遊戲規則 | GAME RULES |
| 規則說明 | 選擇押注與投注模式後，按下 Spin 開始遊戲。 | SELECT A BET AND BET MODE, THEN PRESS SPIN TO PLAY. |
| 規則說明 | 同一局形成多個得獎時，所有得獎金額會加總。 | WHEN MULTIPLE WINS OCCUR IN THE SAME ROUND, ALL WIN AMOUNTS ARE ADDED TOGETHER. |
| 規則說明 | 遊戲發生故障時，所有賠付與遊戲均視為無效。 | MALFUNCTION VOIDS ALL PAYS AND PLAYS. |
