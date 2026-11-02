# AI 製程

本文件寫給**接手開發的 AI**（Claude 或其他模型）：讀完就能在這個工作區開一款新的 Slot 專案、照順序做到交付，並知道每一步該用哪個工具、哪裡要停下來問使用者。

- **做什麼、順序、過關條件**：以 [開發流程.md](開發流程.md) 為準。本文件只補 AI 執行時需要的環境、工具與規則，兩份衝突時以開發流程與各規範為準。
- **怎麼做（格式、命名、欄位）**：查 `專案需知/開發規範/` 下對應的規範。本文件不重寫規格。

## 1. 接手時先做

1. 依序讀完以下文件，再動手：
   1. 本文件
   2. [開發流程.md](開發流程.md)
   3. [_README.md](../其他/_README.md)：Mine 站總覽，有文件清單與專有名詞
   4. [產出與紀錄規範.md](../開發規範/產出與紀錄規範.md)：必要產出、修改紀錄格式、專案目錄
   5. [錯誤清單.md](../開發規範/錯誤清單.md)：過去犯過的錯，新遊戲開工前掃一遍
   6. 產線規範：Omniplay 看 [導覽.md](../開發規範/Omniplay/導覽.md)，Landbase、Reskin 看各自資料夾
2. 接手既有遊戲時，另外要做：
   - 先跑進度條：`py 專案需知/其他/progress.py H0xx`
   - 讀該遊戲的 `進度.md`、`修改紀錄.md`、`注意事項.md`
3. 被問到「之前怎麼決定的」時：
   - 先查 [工作紀錄.md](../../工作紀錄.md)。
   - 客戶與內部的反饋記在 `Slots/其他/一些記錄/反饋紀錄.md`。
4. 不確定的規則一律問使用者，不要從舊遊戲猜。舊專案的命名、版本與報表格式有很多是過渡期做法（見開發流程 §1）。

## 2. 環境

| 項目 | 位置／用法 |
|---|---|
| 工作區（git repo `rhino-boss/Jumbo`，GitHub Pages 對外） | `C:\Users\rhinshen\Mine\個人工作區\工作區` |
| 遊戲專案 | `Slots/H0xx_遊戲名稱/`（目錄結構見產出與紀錄規範 §3） |
| 遊戲發想 | `Slots/其他/其他遊戲/遊戲發想/{遊戲名稱}/` |
| 克隆遊戲 | `Slots/其他/其他遊戲/克隆遊戲/{英文名}/` |
| 遊戲代號、Game List | `Slots/其他/iGaming 遊戲代號一覽.xlsx`、`Slots/其他/Game List_Online.xlsx` |
| 競品資料 | `競品分析/`（遊戲數據報告）、`市場資訊\H5\遊戲資料庫`（Bigwinboard 爬蟲資料） |
| Demogame 共用檔 | `Slots/demogame_common.js`、`Slots/demogame_common.css` |
| Python | `C:\Users\rhinshen\AppData\Local\Programs\Python\Python313\python.exe` |
| Shell | Windows。PowerShell 會擋部分 `rm` 與 regex 指令，檔案操作改用 Python 腳本 |
| 模擬機 | `ssh sim`（192.168.139.10，24 核、7 GB RAM、Python 3.11）。專案放 `/root/Simulator/H0xx_名稱/` |
| 團隊共享區 | `\\192.168.139.6\Simulate\專案需知`：Omniplay 團隊版，由 `_build_html.py` 自動發佈 |
| 送驗共享區 | `\\192.168.139.6\JIG_Certification\送驗\`：送驗規範完整版與送驗資料 |
| SVN | 外團隊規範在 `D:\SVN\Slot\IGaming\說明書`；數學模型在 `D:\SVN\Slot\IGaming\<MathID>\`；PARsheet 在 `D:\SVN\Math_Release\IGaming\<MathID>\` |
| 個人工具與 Skill | `C:\Users\rhinshen\.claude\skills\<名稱>\SKILL.md`；非 Claude 的 AI 可直接讀 SKILL.md 當操作說明 |

## 3. 不可違反的規則

### 3.1 溝通

- 一律用**繁體中文**回覆。回覆只講重點，不要長篇表格與完整推導。
- 使用者改過的檔名以磁碟現況為準，不得改回；產生器的輸出名與所有引用都要跟進新名。
- 時間戳記一律用實際時間（`Get-Date`／commit 時間），不可自編。

### 3.2 一定要先問使用者

| 情況 | 說明 |
|---|---|
| 跳版本號 | 所有遊戲都不得自行升版。覺得該升時先問；版本號記在 `Source/version.txt`（只寫一行，同遊戲所有模型共用），不寫在 xlsx 裡 |
| 數學模型組合 | 每款不同，開案時確認（預設 92A／92B／94A／94B，各含 Newbie／Oldhand） |
| 規格參數 | Cascade 階梯、賠率表等不得自改；要改先提出 |
| Game Rule 未定義的規則 | 退回確認，程式不補猜 |
| 標記完成 | `進度.md` 只有使用者確認後才可標 `ok` |
| 調性 | 卡片權重的調性要使用者確認才算完成 |
| 既有遊戲套新規則 | 新規則（例：Math Document Description 只出英文版）只套用新遊戲，舊遊戲要改先問 |

### 3.3 權限與對外

- **模擬機**：只碰 `/root/Simulator`；嚴禁改 sshd、密碼、SELinux。AI 不代打任何密碼。
- **SVN**：AI 只負責把檔案放進 SVN 工作資料夾，commit／上傳由使用者做。
- **git**：只 commit 自己改的檔案，不要把別人進行中的修改一起帶上去。
- **產線隔離**：Omniplay（OP）是使用者團隊負責，Landbase（LB）、Reskin（RS）是外團隊。
  - 三方互不知道對方的數值設定，只有使用者可以看全部。
  - 三站的規範、文件、網頁互不提及、不共用。
- **交給 SPS**：只交 `config*.js` 與 `Simulator.py`，不交 xlsx、PARsheet、json（開發流程 §5.8）。

### 3.4 檔案

- 不在專案資料夾留 `.bak` 或暫存檔。暫存放 AI 自己的暫存區，驗證完就刪。
- 用程式改數學模型 xlsx 時：
  - 清值要連格式一起清；寫值要從同檔同類儲存格複製樣式。
  - 存檔後跑 `專案需知/其他/_check_xlsx_style.py`，ERROR 必須為 0（見 math-model-xlsx-edit skill）。
- 共用權重欄跨版本必須**逐格完全相同**，不允許 ±1 的整數化尾差；以代表版複製到其他版。
- `專案需知/` 的任何 `.md` 改完，同一次修改內都要跑 `py 專案需知/其他/_build_html.py`。這支會重建網頁、發佈團隊版並同步 SVN 說明書；HTML 不得手改。
- 改 `demogame_common.js`／`.css` 時，必須同時升所有遊戲 `index.html` 引用的 `?v=` 版號，否則線上會吃到快取的舊檔。

### 3.5 模擬

- **≥ 10⁶ 局一律到模擬機跑**，本機只跑 ≤ 10⁵ 局的流程測試。
  - Simulator 要用 `ProcessPoolExecutor`；ThreadPool 受 GIL 限制只用到 1 核。
  - 模擬機**一次只跑一個多程序工作**。7 GB RAM 會爆，曾經導致整台卡死。
  - 跑法：`nohup bash run_xxx.sh > run_xxx.log &`，跑完用 `scp` 把 `Record/*.xlsx` 拉回本機。
- 臨時、探索性的模擬只跑 10⁶ 局就回報。正式場次只用在正式文件與解權重（NB 10⁹ 局、BF 10⁸ 局）。
- 驗證規則：
  - 相同權重只跑一筆；BF 不跑 Newbie。
  - 先跑 10⁶ 再跑正式場次。
  - 結果表要有「符合」欄，判定方式見模擬程式規範 §1.2.2。
- 調完卡片權重必查：規格上會出現的元素（例如 1000x／2500x 球），會不會因為卡片上限變成只出現、不得分。

## 4. 新專案逐步操作

每一步都依開發流程 §4 的「進入下一階段條件」與 §4.1 的檢查表，通過才往下。表中的「停」是必須停下來讓使用者確認的點。

| 步驟 | AI 要做的事 | 用到的 Skill／工具 | 產出 | 停 |
|---|---|---|---|---|
| 0 建專案 | 在 `Slots/` 建 `H0xx_遊戲名稱/`；用 `progress.py` 建立 `進度.md` | `progress.py` | 專案資料夾、`進度.md` | — |
| 1 提案 | 整理玩法、規格、特色與競品差異 | `game-data-report`（競品數據）、pptx 照 [提案報告規範](../開發規範/提案報告規範.md) | 提案 `.pptx` | 提案通過 |
| 2 開案 | 由截圖、口述或參考整理 Game Rule；確認數學目標與模型組合 | `game-rule-generator`、[GameRule規範](../開發規範/GameRule規範.md) | `game_rule.md`、數學目標表 | 規則、口徑、模型組合全部確認 |
| 3.1 模型 | 基礎模型 → RTP／Variant → Card System → AI 轉出 Config（不建轉檔工具） | `math-model-xlsx-edit`、`math-model-checker`、[數學模型規範](../開發規範/Omniplay/數學模型規範.md) | `Source/*.xlsx`、`version.txt`、`config*.js` | — |
| 3.2 模擬 | 寫 Simulator；固定 Seed 單局驗證；Card-Off 自然機率大場次（模擬機） | [模擬程式規範](../開發規範/模擬程式規範.md) | `Simulator.py`、`Record/` 自然報表 | — |
| 3.3 Demo | 依 Config 做可玩 Demo，與 Simulator 單局對帳 | `game-demo-generator`、[Demogame規範](../開發規範/Demogame規範.md) | `index.html` | — |
| 4 調性 | 依自然報表校準卡片權重 → Card-On 全組合驗證 → 數值報告 | `multiplier-weight-tuner`、`multiplier-line-chart`、`_report_card_style.py`、[數值報告規範](../開發規範/數值報告規範.md) | 校準後的模型與 Config、Card-On 報表、`其他/數值報告_<中文名>.md`＋`.html` | 調性確認 |
| 5 後端 | 打包給 SPS → 讀後端報表比對 → 挑 BF 腳本 | `backend-report`、[後端報表](../開發規範/Omniplay/後端報表.md)、[壓測說明書](../開發規範/Omniplay/壓測說明書.md)、[腳本規範](../開發規範/Omniplay/腳本規範.md) | `其他/To SPS/<GameID>_<版本>.zip`、後端報表彙整、腳本權重 | 報表一致 |
| 6 文件 | Help → Game Description；PARsheet；Math Document Description（只出英文版） | `game-help-generator`、`game-description-generator`、[數學文件規範](../開發規範/Omniplay/數學文件規範.md) | `文件/` 下各檔、`文件/PARsheet/*R.xlsx` | — |
| 7 檢查 | 交付物全部逐項檢查；整理送驗包、產生 SHA1 清單 | `math-doc-checker`、`math-model-checker`、`submission-organizer-ctool`、[送驗文件規範](../開發規範/Omniplay/送驗文件規範.md) | 檢查紀錄、`文件/<GameID>/` 送驗包 | 版本凍結 |
| 8 Demo 報告 | 整理設計重點、獨有巧思、困難與反饋，附數據佐證 | [Demo報告規範](../開發規範/Demo報告規範.md) | `demo_report_draft.md` → `.pptx` | 使用者確認 |
| 送驗後 | 收到 Draft／Letter 時歸檔、檢查、更新狀態 | `submission-intake`（串 `inspection-report-checker`、`report-file-management-ctool`、`submission-status-overview`） | 檢查報告、狀態總覽 | 各關卡 |
| 進測 | 上傳 SVN：PARsheet R 檔與 Source 原檔放進對應資料夾 | — | SVN 工作資料夾內的檔案 | 使用者自己 commit |

### 4.1 每次調參的固定循環

照開發流程 §5.7 做：

1. 改 Source XLSX。
2. **先問使用者是否升版**；要升就改 `version.txt`。
3. 轉 Config。
4. 本機跑小場次確認流程。
5. 到模擬機跑中、大場次。
6. 存新的 Record，並與前版比較。
7. 寫修改紀錄。

會改到哪些東西、要重跑什麼，查開發流程 §6。

## 5. 紀錄要寫在哪

| 紀錄 | 位置 | 寫什麼 |
|---|---|---|
| 修改紀錄 | 各遊戲 `修改紀錄.md` | 只記數學調性；依四碼版本分節，句尾附日期（產出與紀錄規範 §2） |
| 進度 | 各遊戲 `進度.md` | 工項狀態：`ok`、`v2`、`v3`…（開發流程 §4.2） |
| 注意事項 | 各遊戲 `注意事項.md` | 本遊戲的特別操作與已知例外 |
| 錯誤清單 | `專案需知/開發規範/錯誤清單.md` | 跨遊戲「做錯、後來修正」的事，新的在上 |
| 工作紀錄 | `工作區/工作紀錄.md` | 討論與決議：日期、主題、參與人員、內容、決議、適用範圍，新的在上 |
| 反饋紀錄 | `Slots/其他/一些記錄/反饋紀錄.md` | 客戶與內部反饋（客戶常嫌太平、高倍數太少、留存差，調性要參考） |
| 基本資訊 | `Slots/其他/一些記錄/基本資訊.md` | 線上轉數等基本數據指標 |

## 6. 常用工具（`專案需知/其他/`）

| 工具 | 用途 |
|---|---|
| `progress.py H0xx` | 顯示或建立遊戲進度條 |
| `_build_html.py` | 規範 md → 網頁；同時發佈團隊版、同步 SVN 說明書 |
| `_check_xlsx_style.py` | 數學模型 xlsx 格式檢查 |
| `_report_card_style.py <html>` | 數值報告與競品報告套卡片版型；同時內嵌倍率線型的滑鼠提示 |
| `_chart_hover.py <html>` | 單獨補倍率線型滑鼠提示（腳本本體是 `chart_hover.js`） |

## 7. 交接回報格式

每段工作結束時，用以下格式回報，讓下一位接手者（人或 AI）能直接接續：

- **做了什麼**：一兩句，附檔案路徑。
- **驗證結果**：跑了什麼、場次、是否符合；沒驗證的要明說。
- **未完成與待確認**：列出還要使用者決定的事。
- **紀錄**：已更新哪些紀錄檔（修改紀錄、進度、錯誤清單、工作紀錄）。
