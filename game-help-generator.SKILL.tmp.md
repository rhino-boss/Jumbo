---
name: game-help-generator
description: Use this skill whenever the user wants to produce a slot-game "Help 頁" (Help page / 企劃書 Help 分頁 / 玩法說明頁) as an .xlsx file based on a Game Rule document. Trigger on phrases like 「做 Help」「Help 頁」「Help 文件」「企劃書 Help」「玩法說明 Excel」「幫我把這份 Game Rule 轉成 Help」, on requests that mention 賞金列車 / Wild Train as a format reference, on slot game documentation tasks where the user supplies rules in any form (pasted text, Drive file, NotebookLM source) and expects a parallel 簡中／英文 Help layout, and on follow-ups about checking an existing Help xlsx for missing rules, contradictions, mixed languages, or repeated content. Default to using this skill even when the user only says "做一份 Help" without further detail — the workflow inside handles the clarification.
---

# Help Create — 老虎機 Help 頁產生器

## 這個 skill 在做什麼

把使用者提供的 Game Rule（任何格式：貼上的文字、Drive 上的 docx/pdf、NotebookLM 連線的來源）先整理成一份可人工確認的 **Help draft md**，待使用者確認後，再轉成符合公司標準格式的 **Help 頁 xlsx**。draft 與 xlsx 產出前後都要跑完整性檢查，整個流程透過 AskUserQuestion 用「選擇題」方式跟使用者互動。

## 為什麼這樣設計

公司的 H5 企劃書 Help 頁有固定的 layout：每個遊戲特色（GAME RULE、FREE GAME、BUY FEATURE、JACKPOT、SYMBOL PAYOUT 等）獨立一個表格區塊，欄位是 `No / 項目 / 簡中 / 英文`，項目分「主要標題、副標題、規則說明、賠率表」。模型容易犯的錯是：把中英文混在同一格、漏掉 Game Rule 寫到的規則、把內部設計或隱藏機制直接寫給玩家看、Buy Feature 倍數和錶底條件對不起來、相同警語重複貼好幾次、或使用口語化文案。整套 skill 的設計就是繞著這幾類錯誤打轉。

## 整體流程

1. **接收 Game Rule** — 確認來源並讀進來
2. **釐清關鍵欄位** — 用選擇題問必要資訊（不是猜）
3. **參考 template** — 讀 `references/help-page-format.md` 了解區塊與欄位
4. **先生成 draft md** — 列出所有準備放進 xlsx 的內容，交給使用者確認
5. **draft 完整性檢查** — 先檢查內容與寫法，再決定能不能轉 xlsx
6. **生成 xlsx** — 只在使用者確認 draft 後呼叫 `scripts/build_help_xlsx.py`
7. **xlsx 檢查 + 優化建議** — 一次跑完，產出檢查清單
8. **跟使用者一起決定怎麼修**

每一步遇到不確定的事情都用 AskUserQuestion 給 2–4 個選項；使用者會直接打字補答案如果選項都不對。

## 第 1 步：接收 Game Rule

使用者通常會直接把 Game Rule 內容貼在對話裡。如果他只丟一個檔名或 Drive 連結，用 Drive MCP 的 `search_files` 搜尋、`read_file_content` 讀內容。如果一開始不清楚 Game Rule 在哪，問（用 AskUserQuestion）：

```
Q: 這次的 Game Rule 在哪裡？
- 我直接貼在下面
- 在 Google Drive（給我檔名/連結）
- 在本機資料夾（請先選資料夾）
```

提醒使用者：「答案不在選項內請直接打字回答」。

## 第 2 步：釐清關鍵欄位

讀完 Game Rule 後，**先檢查下面這些欄位有沒有齊**。缺什麼就用 AskUserQuestion 一次問清，不要邊做邊問：

必填欄位：
- 遊戲名稱（繁中、英文）
- Game ID / PARsheet ID
- 轉輪陣列、路數
- 獎項組成（Symbol 列表）
- 倍數（Base Game / Free Game 各自的倍數階層）
- Scatter 數量對應 Free Spins 場數
- Buy Feature 倍數（如果有）
- Super Feature 倍數（如果有）
- Jackpot 種類（Link JP / OP Jackpot / 無）
- 語系（決定要不要產簡中欄位的內容）

如果 Game Rule 裡沒寫 Buy Feature 或 Jackpot，**不要自己編**，而是問使用者「這款遊戲有 Buy Feature 嗎？」用選擇題：「有 / 沒有 / 我不確定，幫我從 Game Rule 判斷」。

## 第 3 步：參考 template

每次都先讀 `references/help-page-format.md`，那份檔案說明每個區塊的欄位排法、CN/EN 並排規則、賠率表的格式。**不要憑印象寫**——template 細節常變。

## 第 4 步：先生成 draft md

在生成 xlsx 前，先產出一份 `game_help_draft.md`。

這份 draft 是給使用者確認的前置文件，必須包含：

- 所有預計放進 xlsx 的區塊
- 每個區塊的標題 / 副標題 / 規則說明
- 中英對照文案
- 賠率表內容
- 必要時標示哪些區塊是 template-copy、哪些是 rule-derived

draft md 的版型固定如下：

- 檔案最上方先放一個總標題，例如 `# Game Help Draft`
- 接著放 `Game Meta`
- 每個 Help 區塊都用二級標題 `##`
- 區塊內的內容用 markdown table 呈現，欄位固定為：
  - `Item`
  - `简中`
  - `英文`
- 如果某區塊內有子小節，例如 `WILD SYMBOL`、`SCATTER SYMBOL`、`TRIGGER`、`GAMEPLAY`，用三級標題 `###`
- 賠率表獨立成一段 markdown table
- 區塊之間用 `---` 分隔

除非使用者明確要求其他格式，後續都固定產出這種 draft md 版型。

draft 的預設區塊順序固定如下：

1. `PAYTABLE`
2. 遊戲特色：
   - `CASCADING FEATURE`
   - `MULTIPLIER FEATURE`
   - `GOLDEN FRAMED FEATURE`
3. `FREE GAME FEATURE`
4. 特殊押注：
   - `EXTRA BET`
   - `BUY FEATURE`
5. `OP JACKPOT`
6. `LINE GAME` 或 `WAY GAME`
7. `GAME RULE`

如果某遊戲沒有其中某個區塊，就跳過；但有出現的區塊仍應維持這個順序。

如果使用者在某次任務中明確指定新的區塊順序，該次任務以使用者要求為準。

檔名固定使用：

```text
game_help_draft.md
```

不要在檔名加 `game id`。

draft 的目的是讓使用者先改內容與順序，而不是直接改 xlsx。

在使用者尚未確認 draft 前，不要直接生成最終 xlsx。

## 第 5 步：draft 完整性檢查

draft 做好後，必須先檢查文件內容完整性。這一步是固定流程，不要省略。

### 檢查 1：文字敘述是否正式

Help 文案必須使用正式、面向玩家的敘述。

不要出現口語化寫法，例如：

- `雖然`
- `但是`
- `其實`
- `等於說`
- `類似`
- `大概`

也不要用明顯是企劃內部討論、備註或工程解釋的句型。

如果發現語氣不正式，先在 draft 階段修掉，再交給使用者確認。

### 檢查 2：有沒有漏掉沒說明的遊戲規則

逐條對照 `game_rule.md` 與其他來源，確認是否有玩家需要知道、且應該進 Help 的規則漏掉。

這裡要抓的是：

- 玩法規則
- 觸發條件
- 場次 / 倍數 / 賠率
- 買入 / 特殊押注的玩家可感知效果
- 路數 / 賠線與走線圖說明
- Jackpot / Free Game / Feature 的玩家可感知內容

### 檢查 3：過濾隱藏設計

玩家通常看不出來、也不知道的隱藏設計，不應直接全部寫進 Help。

判斷規則：

- 如果某個隱藏設計是負面的，或即使說了也不會讓玩家更想玩，且沒有公平性疑慮，**不要寫**
- 如果某個隱藏設計是正面的、對玩家有加分效果、能幫助玩家理解此模式的優勢，**要寫**

例子：

- `Extra Bet` 需要 `2x` 押注，但如果它有提高 FG 觸發率這類正向加分效果，應寫進 Help
- `[WW]` 不自然掉落、不可替代 `[C1]` 這類負面限制，不要特別寫進 Help
- 重抽條件、內部 profile、card system、隱藏權重、補牌限制、工程實作常數，通常不應直接寫

### 檢查 4：若第 2 點與第 3 點衝突，先跟使用者討論

如果某條規則同時符合：

- technically 是真實規則，照完整性似乎應該補
- 但本質上又屬於隱藏設計或負面設計

不要自行決定，先明確列出衝突點，跟使用者討論後再改 draft。

## 第 6 步：生成 xlsx

呼叫 bundled 腳本：

```bash
python scripts/build_help_xlsx.py \
  --spec /tmp/help_spec.json \
  --out <outputs>/<game_name>_Help.xlsx
```

`help_spec.json` 是你根據 Game Rule 整理出來的結構化資料，schema 在 `references/help-spec-schema.md`。腳本會處理 openpyxl 的細節（合併儲存格、字型、CN/EN 並排），你只負責內容。

把 xlsx 存到 outputs 資料夾，並用 `computer://` 連結給使用者。

只有在使用者已確認 `game_help_draft.md` 後，才可以執行這一步。

## 第 7 步：xlsx 檢查 + 優化建議

xlsx 生成完，**立刻**跑這四項檢查並把結果整理成清單。不要等使用者問。檢查的細節判斷規則寫在 `references/checks.md`，跑檢查時讀。

四項檢查：

1. **規則漏失**：Game Rule 裡寫到、xlsx 沒有的條目
2. **錯誤或前後矛盾**：xlsx 內部數值對不起來、或和 Game Rule 不符
3. **語言純度**：簡中欄出現英文、英文欄出現中文（變數 `[C1]`、`{3}` 不算）
4. **重複資訊**：同一句話/規則出現多次

跑完再加一段「**內容優化建議**」：段落長度、術語一致性、賠率表排版、規則順序。

除了 `references/checks.md` 的四項檢查外，也要回頭確認 draft 階段的四條完整性規則仍然成立：

1. 文案是否正式
2. 有沒有漏掉玩家應知規則
3. 是否錯放了不該公開的隱藏設計
4. 是否仍有需要跟使用者討論的衝突點

## 第 8 步：跟使用者一起決定怎麼修

把上面四項檢查 + 優化建議**一次給完**（使用者選了「先給清單再一起討論」），格式類似：

```
## 檢查結果

### 漏掉的規則 (3)
1. Free Game 最多 50 場上限 — Game Rule 第 X 段有寫
2. ...

### 矛盾 (1)
1. Buy Feature 倍數：「功能」寫 75 倍、「能使用時機」寫 50 倍

### 語言純度 (2)
1. SYMBOL PAYOUT 區塊簡中欄出現 "PAY"
2. ...

### 重複 (1)
1. Buy Feature / Super Feature 操作說明 90% 相同

### 優化建議
- ...
```

然後問（AskUserQuestion）：

```
Q: 你想怎麼處理這些問題？
- 全部按我的建議改，重產一份
- 我挑幾個改、其他先留著
- 我自己改，告訴你改完哪些
```

如果使用者要改，每改一輪就**重跑檢查**，不要假設改了就一定對。

## 重要的小事

- **不要編內容**：Game Rule 沒寫的就跟使用者確認，不要自己補預設值。這是企劃書、會被拿去開發、不能猜。
- **問題用選擇題，但留空間給使用者打字**：每次 AskUserQuestion 都提示「答案不在選項內請直接打字回答」，這是使用者明確要求的互動方式。
- **xlsx 的 sheet 名稱**用 `Help`（單一分頁就好，使用者不需要 Revision History、Math 等其他分頁）。
- **先 draft、後 xlsx**：預設流程一定是先產出 `game_help_draft.md`，讓使用者確認後再轉 xlsx。
- **檔名格式**：draft 固定叫 `game_help_draft.md`；不要在 draft 檔名前加 `game id`。
- **draft 格式固定**：後續預設都產出同一種 markdown 結構，不要每次隨意變換版型。
- **區塊順序固定**：預設依 `PAYTABLE -> 遊戲特色 -> FREE GAME FEATURE -> 特殊押注 -> OP JACKPOT -> LINE/WAY GAME -> GAME RULE` 排列。
- **檔名格式**：`<遊戲英文名>_Help.xlsx`，例如 `Wild_Train_Help.xlsx`。如果使用者沒有英文名，問：「英文名要怎麼取？」並給 2 個建議。
- **文案要正式**：避免口語化連接詞與企劃備註語氣。
- **隱藏設計要篩選**：不是所有真實規則都要寫進 Help；先判斷是否屬於玩家可感知、且是否對玩家有正向理解價值。

## 參考檔案

- `references/help-page-format.md` — Help 頁的區塊與欄位結構（每次都讀）
- `references/help-spec-schema.md` — `build_help_xlsx.py` 吃的 JSON schema
- `references/checks.md` — 四項檢查的判斷規則細節（檢查時讀）
- `scripts/build_help_xlsx.py` — 生成 xlsx 的腳本
