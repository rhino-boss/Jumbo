# 101015 Game Help Draft

這份 md 是 H015「賞金列車 / Wild Train」的 Help 前置確認稿。
之後若要調整遊戲 Help，應先修改這份 md，再同步內嵌至 `index.html`。

## Game Meta

| Field | Value |
| --- | --- |
| game_id | 101015 |
| parsheet_id | H0151 |
| name_zh | 賞金列車 |
| name_en | Wild Train |
| game_type | Video Slot - 3,600 Ways / Cascade / Cascade Multiplier |

---

## PAYTABLE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 符號賠付值 | SYMBOL PAYOUT VALUES |

### WILD SYMBOL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 百搭符號 | WILD SYMBOL |
| 規則說明 | [WW] 可替代除 [C1] 外的所有賠付符號。 | [WW] SUBSTITUTES FOR ALL PAYING SYMBOLS EXCEPT [C1]. |

### SCATTER SYMBOL

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 散佈符號 | SCATTER SYMBOL |
| 規則說明 | 所有連消結束後，最終盤面出現 {3} 個或以上 [C1]，將觸發免費遊戲。 | AFTER ALL CASCADES ARE COMPLETE, {3} OR MORE [C1] ON THE FINAL REELS TRIGGER THE FREE GAME FEATURE. |

### 賠率表

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 副標題 | 賠率表 | PAYTABLE |

| 中文欄 | 中文欄 | 中文欄 |
| --- | --- | --- |
| [M1] 3 - 50 | [M1] 4 - 100 | [M1] 5 - 150 |
| [M1] 6 - 250 | [M2] 3 - 40 | [M2] 4 - 75 |
| [M2] 5 - 100 | [M2] 6 - 150 | [M3] 3 - 25 |
| [M3] 4 - 50 | [M3] 5 - 75 | [M3] 6 - 100 |
| [M4] 3 - 25 | [M4] 4 - 50 | [M4] 5 - 75 |
| [M4] 6 - 100 | [A] 3 - 10 | [A] 4 - 20 |
| [A] 5 - 30 | [A] 6 - 50 | [K] 3 - 10 |
| [K] 4 - 20 | [K] 5 - 30 | [K] 6 - 50 |
| [Q] 3 - 5 | [Q] 4 - 10 | [Q] 5 - 15 |
| [Q] 6 - 25 | [J] 3 - 5 | [J] 4 - 10 |
| [J] 5 - 15 | [J] 6 - 25 |  |

---

## WAYS FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 3600 路賠付 | 3600 WAYS |
| 規則說明 | 盤面共有 {6} 輪，有效格數依序為 {3、4、5、5、4、3}。 | THE GAME USES {6} REELS WITH {3, 4, 5, 5, 4, 3} ACTIVE POSITIONS. |
| 規則說明 | 相同符號由最左輪開始，在連續相鄰輪出現至少 {3} 輪即可得獎；每種 Ways 組合分別計獎。 | MATCHING SYMBOLS PAY FROM THE LEFTMOST REEL ACROSS AT LEAST {3} CONSECUTIVE REELS. EACH WAY IS AWARDED SEPARATELY. |

---

## CASCADING FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 連消特色 | CASCADING FEATURE |
| 規則說明 | 每次中獎後，中獎符號會被消除並依掉落表補入新符號，再次檢查中獎組合。 | AFTER EACH WIN, WINNING SYMBOLS ARE REMOVED AND REPLACED USING THE CASCADE TABLE, THEN THE REELS ARE EVALUATED AGAIN. |
| 規則說明 | 連消會持續進行，直到盤面不再形成新的中獎組合。 | CASCADES CONTINUE UNTIL NO NEW WINNING COMBINATION IS FORMED. |

---

## GOLDEN SYMBOL FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 金框符號 | GOLDEN SYMBOL FEATURE |
| 規則說明 | 金框符號以對應的一般符號參與計獎；若金框符號屬於中獎組合，該位置會在下一次連消轉換為 [WW]。 | A GOLDEN SYMBOL PAYS AS ITS MATCHING REGULAR SYMBOL. WHEN IT PARTICIPATES IN A WIN, THAT POSITION CHANGES TO [WW] FOR THE NEXT CASCADE. |

---

## MULTIPLIER FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 連消倍數 | CASCADE MULTIPLIER |
| 規則說明 | 基礎遊戲每次旋轉由 x1 開始；免費遊戲每次旋轉由 x8 開始。 | EACH BASE GAME SPIN STARTS AT x1. EACH FREE GAME SPIN STARTS AT x8. |
| 規則說明 | 每完成一次中獎連消，倍數等級向上提升一級。倍數等級為 x1、x2、x4、x8、x16、x32、x64、x128、x256、x512、x1024。 | AFTER EACH WINNING CASCADE, THE MULTIPLIER ADVANCES ONE LEVEL: x1, x2, x4, x8, x16, x32, x64, x128, x256, x512 AND x1024. |
| 規則說明 | 閃電效果可能額外提升倍數等級；本次連消的獎金乘以提升後的倍數。 | THE LIGHTNING EFFECT MAY ADVANCE ADDITIONAL MULTIPLIER LEVELS. THE CURRENT CASCADE WIN IS MULTIPLIED BY THE UPDATED VALUE. |

---

## FREE GAME FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 免費遊戲特色 | FREE GAME FEATURE |
| 規則說明 | {3、4、5} 個 [C1] 分別獲得 {10、12、14} 次免費旋轉。 | {3, 4 OR 5} [C1] AWARD {10, 12 OR 14} FREE SPINS RESPECTIVELY. |
| 規則說明 | 免費遊戲中再次出現 {3} 個或以上 [C1]，會依相同規則追加免費旋轉；單次免費遊戲最多進行 {50} 次旋轉。 | {3} OR MORE [C1] DURING THE FREE GAME AWARD ADDITIONAL FREE SPINS BY THE SAME RULE. A FREE GAME SESSION IS CAPPED AT {50} SPINS. |
| 規則說明 | 系統會依權重指定其中一場免費遊戲；若該場首段連消未出現閃電，會強制提升 {1} 階倍數。 | ONE WEIGHTED FREE SPIN IS DESIGNATED PER FEATURE. IF ITS FIRST CASCADE HAS NO LIGHTNING, THE MULTIPLIER IS FORCED UP BY {1} LEVEL. |

---

## BUY FEATURE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 購買特色 | BUY FEATURE |
| 規則說明 | 購買特色的費用為目前投注的 {75} 倍。按下購買特色會立即進行一次保證觸發免費遊戲的旋轉，並直接進入免費遊戲；這不是持續狀態切換。 | BUY FEATURE COSTS {75} TIMES THE CURRENT BET. PRESSING BUY FEATURE IMMEDIATELY PLAYS ONE SPIN GUARANTEED TO TRIGGER THE FREE GAME, THEN ENTERS THE FEATURE. IT IS NOT A PERSISTENT MODE. |
| 規則說明 | 購買特色使用 BF 進場輪帶；進入免費遊戲後，使用 BF 對應的免費遊戲 table 權重。 | BUY FEATURE USES THE BF ENTRY STRIP. AFTER ENTRY, THE FEATURE USES THE BF-SPECIFIC FREE GAME TABLE WEIGHTS. |

---

## GAME RULE

| Item | 繁中 | 英文 |
| --- | --- | --- |
| 主要標題 | 遊戲規則 | GAME RULES |
| 規則說明 | 所有獎金以遊戲點數顯示。基礎投注為 {100} 點，實際投注會依所選 Bet 倍率調整。 | ALL WINS ARE SHOWN IN GAME CREDITS. THE BASE WAGER IS {100} CREDITS AND IS ADJUSTED BY THE SELECTED BET MULTIPLIER. |
| 規則說明 | H015192 理論返還率：一般投注 {92.00%}、購買特色 {92.50%}；H015194 理論返還率：一般投注 {94.00%}、購買特色 {92.50%}。 | H015192 THEORETICAL RTP: NORMAL BET {92.00%}, BUY FEATURE {92.50%}. H015194 THEORETICAL RTP: NORMAL BET {94.00%}, BUY FEATURE {92.50%}. |
