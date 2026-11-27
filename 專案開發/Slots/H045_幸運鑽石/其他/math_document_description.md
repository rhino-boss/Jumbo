<!-- 中英文合併一份（2026-11-26，由 _ZH／_EN.docx 轉出）：前半中文、後半 English；docx 只出英文版 -->

# Math Document Description — 101015 幸運鑽石（Lucky Diamond）

範圍：Normal Bet

| 項目 | 內容 |
| --- | --- |
| Game ID | 101015 |
| Math files | H0451.xlsx（共用自然模型）；H045192.xlsx（RTP 92%）、H045194.xlsx（RTP 94%） |
| Version | 共用模型 6；RTP 模型 6.0.1.2 |
| 對應程式 | simulator.py + config.js（共用模型）+ config_92.js / config_94.js（各 RTP 版本） |
| 盤面 | 5 輪 × 4 列固定盤面，共 20 格 |
| 得分方式 | 1,024 Ways：一般符號由最左輪（R1）起連續出現於相鄰輪即得獎；中獎符號消除後原地補牌（Cascade） |
| Coin In | 100（Base Bet 100 × Price 1） |
| 押注模式 | Normal Bet |
| Game RTP | 92%（H045192.xlsx）／94%（H045194.xlsx）；含 OP Jackpot 的 Total RTP 96% |
| 最大得分 | 每局 20,000 × Coin In |

# 目錄

- 一、工作表說明

- 1-1 程式如何使用 xlsx 的參數

- 1-2 各工作表用途一覽

- 1-3 Overview（共用模型）

- 1-4 Parameter

- 1-5 Symbol 輪帶表

- 1-6 Overview（RTP 版本檔）

- 1-7 Multiplier_Weight、Avg_Multi 與 Nature_Prob

- 1-8 OP Jackpot

- 二、Parameter 工作表的遊戲參數說明

- 2-1 Table Selection Weight - Base Game

- 2-2 Table Selection Weight - Free Game / Retrigger

- 2-3 Gold Count Weight - Base Game

- 2-4 Gold Count Weight - Free Game

- 2-5 Cascade Multiplier Ladder

- 2-6 Game Limit

- 2-7 輪帶表上的特色權重

- 三、遊戲邏輯

- 3-1 盤面

- 3-2 符號與角色

- 3-3 單次 spin 的流程

- 3-4 判獎規則

- 3-5 Cascade 與金框符號

- 3-6 倍數百搭與得分計算

- 3-7 Free Game

- 3-8 一局（一次付費 spin）的完整流程

- 3-9 重要規則整理

- 四、卡片系統說明

- 4-1 用途

- 4-2 卡片的結構

- 4-3 單局的判定流程

- 4-4 重抽上限與最大得分

- 4-5 注意事項

# 一、工作表說明

## 1-1 程式如何使用 xlsx 的參數

本遊戲的數學文件拆成兩類工作簿：共用自然模型（H0451.xlsx：輪帶、停輪權重、補牌權重、賠率、選表、金框與倍數百搭設定、連消倍數階梯、FG 場次，兩個 RTP 版本共用）與 RTP 版本檔（H045192.xlsx／H045194.xlsx：RTP 拆解、卡片權重、區間平均倍率與自然機率、SCR）。理解以下三點，才能正確對照工作表欄位與程式行為：

- 權重只看相對大小。

所有標示為 Weight 的欄位都是相對權重，不需要是機率、也不需要湊成 100%。程式抽樣時是在「該組權重的總和」範圍內取一個隨機值，再依權重比例落到對應項目。每一組權重的總和就是該組的分母，因此在同一組內單獨調高某一項，會同時稀釋其他項的機率。

- 程式讀取的是由 xlsx 轉出的 config。

simulator.py 載入 config.js（對應共用模型）與一份 RTP config：config_92.js 或 config_94.js（對應 RTP 版本檔）。執行前程式會核對兩份 config 都屬於 H045、共用模型版本為 1 碼、RTP 版本為 4 碼且第 1 碼等於共用模型版本。本文件標示「程式使用 ✅」的欄位，指該資料會進入 config 並影響模擬。

- 並非所有欄位都會被程式使用。

各輪帶表左側的張數統計、Symbol 文字欄位與註記儲存格屬於檢核用途，程式不讀取。下方各節逐一標明。

## 1-2 各工作表用途一覽

共用自然模型 `H0451.xlsx`

| 工作表 | 提供什麼 | 影響哪一段玩法 | 程式使用 |
| --- | --- | --- | --- |
| Overview | 遊戲基本規格、FG 場次設定、符號賠率表 | 成本計算、判獎、FG 場次 | ✅ 部分 |
| Parameter | 選表權重、金框顆數權重、連消倍數階梯、FG 場次上限 | 選表、金框、連消倍數、FG 場次 | ✅ |
| BG_Symbol、BG_Symbol (2)、BG_Symbol (3) | Base Game 的三組輪帶：輪帶、停輪權重、補牌權重、金框翻牌權重、分裂顆數權重、百搭倍數權重 | BG 的開局盤面、Cascade 補牌、金框 | ✅ |
| FG_Symbol、FG_Symbol (2)、FG_Symbol (3) | Free Game 的三組輪帶，內容同上 | FG 的開局盤面、Cascade 補牌、金框 | ✅（FG_Symbol (3) 選表權重為 0，不會被使用） |

RTP 版本檔 `H045192.xlsx`／`H045194.xlsx`（結構相同）

| 工作表 | 提供什麼 | 影響哪一段玩法 | 程式使用 |
| --- | --- | --- | --- |
| Overview | 版本號、RTP 拆解 | 版本核對、輸出檔名 | ✅ 版本 |
| Multiplier_Weight | 卡片系統的 BG／FG 卡片權重 | 單局結果的接受／重抽 | ✅ |
| Avg_Multi | 各得分倍率區間的自然平均倍率 | 權重 × 平均倍率 = 各區間的派彩貢獻 | ❌（核對用） |
| Nature_Prob | 各得分倍率區間的自然發生機率 | 卡片權重配置的合格性檢核 | ❌（核對用） |
| OP Jackpot | SCR（Scatter spin 率） | 彩金模組的機率換算 | ❌（由平台彩金模組使用） |

## 1-3 Overview（共用模型）

| 區塊 | 內容 | 程式使用 |
| --- | --- | --- |
| Model / Version | 模型代號 H0451 與共用模型版本 6 | ✅ 版本核對 |
| Base Bet / Multiway | 押注基準 100；最大 1,024 Ways | ✅ Base Bet；Multiway 為參考值（Ways 由程式依盤面計算） |
| Coin in 表 | Normal Bet 的成本（100 × Price 1） | ✅ |
| Reel # / Visible Window Size | 5 輪，每輪 4 格 | ✅ 建立盤面尺寸 |
| Free Spins Setting | Scatter（C1）數量對應免費場次與 Retrigger 場次；總場次上限 50 | ✅（見 3-7） |
| Pay Table | 各符號的代號、Id，連續 1～5 輪的賠率（以 100 credit 投注為單位） | ✅ 判獎 |

Pay Table（以 100 credit 投注為單位；除以 100 即為 Coin In 的倍數）

| Symbol | Id | 3 輪 | 4 輪 | 5 輪 |
| --- | --- | --- | --- | --- |
| WW（Wild） | 0 | — | — | — |
| W2（Split Wild） | 1 | — | — | — |
| C1（Scatter） | 2 | — | — | — |
| M1 | 3 | 25 | 75 | 125 |
| M2 | 4 | 20 | 60 | 100 |
| M3 | 5 | 15 | 45 | 75 |
| M4 | 6 | 10 | 30 | 50 |
| A | 7 | 5 | 15 | 25 |
| K | 8 | 5 | 15 | 25 |
| Q | 9 | 5 | 10 | 15 |
| J | 10 | 5 | 10 | 15 |

1 輪、2 輪欄位所有符號皆為 0。WW、W2、C1 沒有自身賠率；C1 不提供 Scatter 給獎。

Free Spins Setting

| 最終盤面 C1 數 | 初始免費場次 | Retrigger 場次 |
| --- | --- | --- |
| 3 | 10 | 5 |
| 4 | 10 | 5 |
| 5 以上 | 10 | 5 |

免費場次上限 50 場。

Coin In

Coin In = 押注倍數 × Base Bet = 1 × 100

所有 RTP 與倍率統計都以「該局總得分 ÷ Coin In」表示。

## 1-4 Parameter

共用模型的控制面板，各區塊見第二章。

## 1-5 Symbol 輪帶表

Base Game 與 Free Game 各三張，版面相同。每張定義一組 5 輪的環狀輪帶與停輪權重、Cascade 使用的補牌權重，以及該表的金框／百搭權重。

| 欄位群 | 內容 | 程式使用 |
| --- | --- | --- |
| 最左側 Symbol / Description / R1~R5 / ID | 各符號在每輪輪帶上的張數統計與符號 Id 對照 | ❌ 檢核用 |
| Symbol（J:O） | 輪帶內容（文字），含 Line # | ❌ 給人閱讀 |
| Symbol ID（Q:U） | 輪帶內容（代號） | ✅ 實際輪帶 |
| Symbol Weight（W:AA） | 每個輪帶位置的停輪權重 | ✅ 決定停輪位置 |
| Gold_Result_Weight（AC:AD） | 金框翻牌兩種結果（WW／W2）的權重 | ✅（見 2-7） |
| Split_Count_Weight（AC:AD） | W2 丟出的複製 W2 顆數（2／3／4） | ✅（見 2-7） |
| Multiplier_Wild_Weight_WW、Multiplier_Wild_Weight_W2（AC:AD） | 翻出的 WW、W2 各自的倍數權重（×1／×2／×3／×5） | ✅（見 2-7） |
| Symbol Drop Weight（AF:AK） | 每輪各符號的補牌權重 | ✅ Cascade 補牌 |
| Gold_Count_Weight（AC:AH，僅 BG_Symbol (3) 與 FG_Symbol (3)） | 只用於該表的每輪金框顆數 | ✅（該表以此取代 2-3／2-4） |

輪帶長度

| 工作表 | R1 | R2 | R3 | R4 | R5 |
| --- | --- | --- | --- | --- | --- |
| BG_Symbol、BG_Symbol (2) | 176 | 170 | 180 | 172 | 173 |
| BG_Symbol (3) | 176 | 168 | 172 | 169 | 173 |
| FG_Symbol、FG_Symbol (2) | 174 | 169 | 178 | 170 | 169 |
| FG_Symbol (3) | 174 | 167 | 170 | 167 | 169 |

關於 `Symbol Weight`：這是輪帶停點的權重，不是符號的權重。程式依此欄抽出一個輪帶位置，從該位置起連續取 4 格填入該輪（輪帶為環狀）。因此某符號在開局盤面的實際出現率，同時取決於它在輪帶上的張數與所在位置的權重。

關於 `Symbol Drop Weight`：與輪帶無關的「符號 × 輪」權重表。Cascade 消除後留下的每個空格，原地依該輪權重抽一個符號補上，其餘符號不移動。WW、W2 的補牌權重為 0，因此補牌不會補出百搭。

六張表的角色

| 工作表 | 輪帶上的 C1 | 補牌含 C1 | 金框 | 角色 |
| --- | --- | --- | --- | --- |
| BG_Symbol | R1（3 格）、R3（2 格） | 無 | 2-3 | 一般局；盤面最多 2 顆 C1，不會觸發 FG |
| BG_Symbol (2) | R2（3 格）、R5（5 格） | 無 | 2-3 | 高連消局（補牌權重約 98% 為 A／K／Q／J）；最多 2 顆 C1，不會觸發 FG |
| BG_Symbol (3) | 每輪（4／4／4／4／5 格） | 有 | 自帶 Gold_Count_Weight | BG 唯一可觸發 FG 的表；金框只翻出無倍數 WW |
| FG_Symbol | 每輪（2／3／2／2／3 格） | 有 | 2-4 | FG 場次；可 Retrigger |
| FG_Symbol (2) | 每輪（2／3／2／2／3 格） | 有 | 2-4 | 高連消 FG 場次（補牌權重約 97% 為 A／K／Q／J）；可 Retrigger |
| FG_Symbol (3) | 每輪（2／3／2／2／3 格） | 有 | 自帶 Gold_Count_Weight | 未使用（選表權重 0） |

> 各輪帶上的 C1 間距使開局盤面每輪最多看得到 1 顆 C1。同一輪的第 2 顆以上 C1 只可能來自 Cascade 補牌，且只會發生在 BG_Symbol (3) 與 FG 各表。BG_Symbol／BG_Symbol (2) 的 C1 看得到（也計入 1-8 的 SCR），但永遠達不到觸發顆數。

## 1-6 Overview（RTP 版本檔）

| 區塊 | 內容 | 程式使用 |
| --- | --- | --- |
| Model / Version | 模型代號 H045192／H045194 與四碼版本 6.0.1.2 | ✅ 版本核對、輸出檔名 |
| Coin in 表 | Normal Bet 的成本與 Game RTP | 目標值 |
| 彩金列 | Bonus RTP、Link RTP、Total RTP、Hit JP Symbol appear rate | 目標值 |
| Total Pay Back 表 | Base Game／Free Game 派彩率、FG 觸發率（Hit%）與週期（Pulls/Hit） | 目標值 |

兩個 RTP 版本的目標值

| 檔案 | Base Game | Free Game | Game RTP | Bonus RTP | Link RTP | Total RTP | FG 週期 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H045192.xlsx | 67% | 25% | 92% | 2% | 2% | 96% | 1/150 |
| H045194.xlsx | 67% | 27% | 94% | 2% | 0% | 96% | 1/150 |

- FG 觸發率（Hit%）每局 0.6667%，即平均每 150 局觸發一次（Pulls/Hit）。

- Total RTP = Game RTP + Bonus RTP + Link RTP。Bonus／Link 的參數屬於平台 OP Jackpot 模組，不在本模型內；本模型只提供換算用的 SCR（見 1-8）。

- Hit JP Symbol appear rate 取自 OP Jackpot 工作表的 NB SCR，以 Threshold 10,000,000,000 為分母：兩個版本皆為 3,118,318,000。

## 1-7 Multiplier_Weight、Avg_Multi 與 Nature_Prob

`Multiplier_Weight` 是卡片系統的輸入。欄位配置：

| 欄 | 標題 | 用途 |
| --- | --- | --- |
| A | Range | 得分倍率區間標籤 |
| B | Weight_NB_BG | Base Game 卡片權重 |
| C | Weight_NB_FG | Free Game 卡片權重 |

第 3～66 列為 64 個得分倍率區間（得分 ÷ Coin In，左開右閉），由 (-1, 0]（未得分）到 (100000, 9999999]。最後一列 Free Game 是特殊卡：不看金額，只要求這一局觸發 Free Game。詳見第四章。

| 項目 | 92 版 | 94 版 |
| --- | --- | --- |
| Weight_NB_BG | 有權重的區間 (-1, 0]～(350, 400]，合計 1,000,000,000；Free Game 卡 6,711,410；整欄合計 1,006,711,410 | 與 92 版逐格相同 |
| Weight_NB_FG | 有權重的區間 (10, 15]～(10000, 20000]，合計 1,000,000,000（FG 平均 37.50 倍） | 同範圍，FG 平均 40.50 倍 |

- Free Game 卡被抽中的機率為 6,711,410 ÷ 1,006,711,410 = 1/150，即 FG 觸發率。

- 兩份 RTP 版本檔的差異只在 `Weight_NB_FG` 一欄——也就是 FG 的派彩配置。Weight_NB_BG、整份共用模型在兩個版本中完全相同。

`Avg_Multi`（與 Multiplier_Weight 同列對應，兩個版本內容相同；數值格式 0.0000）：

| 欄 | 標題 | 內容 |
| --- | --- | --- |
| A | Range | 得分倍率區間標籤 |
| B | Avg_Multi_NB_BG | 卡片系統關閉的自然模擬中，落在該區間的 BG 局平均倍率（得分 ÷ Coin In，不含觸發 FG 的局）；Free Game 列為觸發局的 BG 平均倍率（只計 BG 得分不超過 400 倍的觸發局，5.4936） |
| C | Avg_Multi_NB_FG | 落在該區間的整段 Free Game（含 Retrigger 的全部場次）平均倍率 |

`Nature_Prob`（同列對應，兩個版本內容相同；數值格式 0.0000%）：

| 欄 | 標題 | 內容 |
| --- | --- | --- |
| A | Range | 得分倍率區間標籤 |
| B | Nature_Prob_NB_BG | 卡片系統關閉時，未觸發 FG 的一局落在該區間的自然機率（64 個區間合計 100%）；Free Game 列為每局的自然 FG 觸發率（0.7709%，約 1/129.72） |
| C | Nature_Prob_NB_FG | 整段 Free Game 落在該區間的自然機率（64 個區間合計 100%） |

核對方式

Base Game 派彩率 = Σ（Weight_NB_BG × Avg_Multi_NB_BG）÷ Weight_NB_BG 整欄合計

（65 列全部，含 Free Game 列）

= 674,495,989 ÷ 1,006,711,410 = 67.00%

FG 平均倍數 = Σ（Weight_NB_FG × Avg_Multi_NB_FG）÷ 10^9

= 37.50（92 版）／40.50（94 版）

Free Game 派彩率 = FG 平均倍數 × FG 觸發率（1/150）

= 25.00%（92 版）／27.00%（94 版）

由於 Weight_NB_BG 的 64 個區間權重合計正好 10⁹，該欄 Σ（權重 × 平均倍率）÷ 10⁹（67.45%）是以「每 10⁹ 次區間卡抽取」表示的同一派彩；改除以整欄合計即換算為每局的派彩率。

Nature_Prob 用來確認每個有權重的區間實際開得出來：所有有權重區間的自然機率皆高於 0.1%；Free Game 列顯示自然觸發率（1/129.72）高於目標觸發率（1/150）。

## 1-8 OP Jackpot

彩金系統參考文件：Math Document Description_JP。OP Jackpot 的獎項階級、起始彩池與提撥比例為所有 OP Jackpot 遊戲共用；OP Jackpot Feature RTP % 的計算細節請參考 BMM 2026 年 8 月 4 日的認證測試報告「JUMBO.1038.A.02」。

記錄 SCR（Scatter spin 率），供平台彩金模組把「每局的理論觸發率」換算成「每個含 Scatter 的 spin 的判定機率」。

| 欄位 | 內容 |
| --- | --- |
| Threshold | 10,000,000,000（SCR 的分母基數） |
| NB | SCR = 3,118,318,000（92 版與 94 版相同） |

SCR 的口徑：最終盤面含至少 1 顆 C1 的 spin 數 ÷ 付費局數 × 10,000,000,000（Base Game 與每一場 Free Game 都各算一次 spin），由卡片系統開啟的模擬實測。

彩金機率的換算公式

Pscatter = SCR ÷ 10,000,000,000 = 0.3118318

（每一局平均出現「含至少 1 顆 C1 的 spin」的次數）

Ptheory  = 該彩金獎項每一局的理論觸發機率

（由獎項的固定派彩率與獎額反推；參數在平台彩金模組內）

Phit     = Ptheory ÷ Pscatter

（每個含 C1 的 spin 實際進行一次彩金判定的條件機率）

彩金判定只發生在含 C1 的 spin 上，因此以 Pscatter 放大後的 Phit 進行判定，長期觸發率即等於 Ptheory。OP Jackpot 判定與 FG 觸發互相獨立；同一把同時成立時，先結算彩金。

# 二、Parameter 工作表的遊戲參數說明

## 2-1 Table Selection Weight - Base Game

| 工作表 | 權重 |
| --- | --- |
| BG_Symbol | 4 |
| BG_Symbol (2) | 1 |
| BG_Symbol (3) | 5 |

每一次 Base Game spin 的第一個動作就是依此權重抽出本局使用的輪帶表（40%／10%／50%）。抽中的表提供整個 spin（含所有 Cascade）使用的輪帶、補牌權重與金框／百搭權重。BG 只有 BG_Symbol (3) 會觸發 FG（見 1-5），因此這是影響遊戲手感與 FG 頻率最上游的參數。

## 2-2 Table Selection Weight - Free Game / Retrigger

| 工作表 | Free Game | Retrigger |
| --- | --- | --- |
| FG_Symbol | 2 | 2 |
| FG_Symbol (2) | 8 | 8 |
| FG_Symbol (3) | 0 | 0 |

每一場 FG 各自依此權重選表（20%／80%），與其他場次無關。Retrigger 區塊與 Free Game 區塊數值相同；程式對每一場 FG（含 Retrigger 追加的場次）都使用 Free Game 權重選表。FG_Symbol (3) 權重為 0，不會被選到。

## 2-3 Gold Count Weight - Base Game

每輪的金框顆數（權重以 100,000 為基數），用於 BG_Symbol 與 BG_Symbol (2)：

| 金框顆數 | R1 | R2 | R3 | R4 | R5 |
| --- | --- | --- | --- | --- | --- |
| 0 | 100000 | 40398 | 51236 | 64539 | 100000 |
| 1 | 0 | 41096 | 37292 | 29869 | 0 |
| 2 | 0 | 15678 | 10179 | 5184 | 0 |
| 3 | 0 | 2660 | 1235 | 399 | 0 |
| 4 | 0 | 169 | 58 | 10 | 0 |

- 金框只出現在 R2、R3、R4；R1、R5 固定抽到 0 顆。

- 金框是套在一般符號上的旗標，不是符號：輪帶與補牌權重只含符號 Id 0～10。金框符號的賠率與原符號相同。

- 停輪後程式逐輪抽出 R2～R4 的顆數，在該輪隨機挑選非 C1 的格子套上金框（C1 不會有金框）。合格格數少於抽中顆數時，放多少算多少。

- 每次 Cascade 補牌後，有新補符號的輪會重新抽一次顆數（見 3-5）。

## 2-4 Gold Count Weight - Free Game

用法同 2-3，用於 FG_Symbol 與 FG_Symbol (2)：

| 金框顆數 | R1 | R2 | R3 | R4 | R5 |
| --- | --- | --- | --- | --- | --- |
| 0 | 100000 | 43300 | 49434 | 56195 | 100000 |
| 1 | 0 | 40315 | 38084 | 34837 | 0 |
| 2 | 0 | 14075 | 11002 | 8099 | 0 |
| 3 | 0 | 2183 | 1412 | 837 | 0 |
| 4 | 0 | 127 | 67 | 33 | 0 |

BG_Symbol (3) 與 FG_Symbol (3) 在輪帶表上自帶 Gold_Count_Weight 區塊，該表以此取代 2-3／2-4（見 2-7）。

## 2-5 Cascade Multiplier Ladder

| 模式 | 第 1 次中獎 | 第 2 次中獎 | 第 3 次中獎 | 第 4 次中獎 | 第 5 次起 |
| --- | --- | --- | --- | --- | --- |
| Base Game | ×1 | ×2 | ×3 | ×5 | ×10 |
| Free Game | ×2 | ×4 | ×6 | ×10 | ×20 |

連消倍數為固定階梯，不做隨機抽取。同一 spin 的第 n 次中獎使用第 n 階；到達頂階後維持不變，直到該 spin 結束。每一次 spin（含每一場 FG）都從第一階重新開始。

## 2-6 Game Limit

| 欄位 | 數值 | 程式使用 |
| --- | --- | --- |
| Max Free Spins | 50 | ✅ |
| Free Spins Initial / Retrigger | 10 / 5 | ✅（與 1-3 的 Free Spins Setting 相同） |
| Note | 最大得分由卡片系統決定，基礎模型不設定 | ❌ 文字說明 |

## 2-7 輪帶表上的特色權重

以下權重放在各輪帶表（AC:AD 欄），套用於本次 spin 所選的表。

Gold_Result_Weight（中獎金框符號的翻牌結果）

| 工作表 | WW | W2 |
| --- | --- | --- |
| BG_Symbol、BG_Symbol (2) | 90 | 10 |
| BG_Symbol (3) | 1000 | 0 |
| FG_Symbol、FG_Symbol (2) | 88 | 12 |
| FG_Symbol (3) | 100 | 0 |

Split_Count_Weight（W2 丟出的複製 W2 顆數；各表相同）

| 顆數 | 2 | 3 | 4 |
| --- | --- | --- | --- |
| 權重 | 4 | 2 | 1 |

Multiplier_Wild_Weight_WW／Multiplier_Wild_Weight_W2（翻出的百搭倍數；×1 代表無倍數）

| 工作表 | 倍數表 | ×1 | ×2 | ×3 | ×5 |
| --- | --- | --- | --- | --- | --- |
| BG_Symbol、BG_Symbol (2)、FG_Symbol、FG_Symbol (2) | WW | 50 | 120 | 65 | 15 |
| BG_Symbol、BG_Symbol (2)、FG_Symbol、FG_Symbol (2) | W2 | 25 | 55 | 30 | 15 |
| BG_Symbol (3)、FG_Symbol (3) | WW、W2 | 100 | 0 | 0 | 0 |

前四張表翻出的百搭有 80% 帶倍數（×2、×3 或 ×5）；BG_Symbol (3) 翻出的百搭一律無倍數。

Gold_Count_Weight（僅 BG_Symbol (3) 與 FG_Symbol (3)；權重以 100,000 為基數）

| 工作表 | 金框顆數 | R2 | R3 | R4 |
| --- | --- | --- | --- | --- |
| BG_Symbol (3) | 0 / 1 / 2 / 3 / 4 | 52142 / 36875 / 9779 / 1153 / 51 | 61771 / 31623 / 6071 / 518 / 17 | 72894 / 23982 / 2959 / 162 / 3 |
| FG_Symbol (3) | 0 / 1 / 2 / 3 / 4 | 38838 / 41438 / 16580 / 2948 / 197 | 44823 / 39830 / 13272 / 1966 / 109 | 51604 / 37125 / 10016 / 1201 / 54 |

R1、R5 固定為 0 顆（0 顆權重 100,000）。

# 三、遊戲邏輯

## 3-1 盤面

| 項目 | 數值 |
| --- | --- |
| 輪數 | 5（R1～R5） |
| 每輪格數 | 4（固定） |
| 總格數 | 20 |
| 最大 Ways | 4 × 4 × 4 × 4 × 4 = 1,024 |

每輪從停點起連續取 4 格輪帶。判獎與 C1 計數都使用整個 5 × 4 盤面。

## 3-2 符號與角色

| 符號 | Id | 說明 | 角色 |
| --- | --- | --- | --- |
| WW | 0 | Wild（百搭） | 替代 C1 以外的所有符號；只由中獎金框符號產生；可能帶 ×2／×3／×5 |
| W2 | 1 | Split Wild（分裂百搭） | 替代 C1 以外的所有符號；只由中獎金框符號產生，並丟出 2～4 顆相同的 W2；可能帶 ×2／×3／×5 |
| C1 | 2 | Scatter | 只計數；最終盤面 3 顆以上觸發 FG；不參與 Ways、不會被消除、不會被百搭替代、不會有金框 |
| M1～M4 | 3～6 | 高分符號 | 得分 |
| A、K、Q、J | 7～10 | 低分符號 | 得分 |
| 金框符號 | — | 套在 M1～M4、A、K、Q、J 上的旗標（僅 R2～R4） | 以原符號判獎、賠率相同；參與中獎時不消除，翻成 WW 或 W2 |

WW、W2 不在輪帶上，也不會由補牌產生。 盤面上的百搭全部來自中獎的金框符號（或 W2 的複製體）。R1 永遠不會出現百搭：金框不出現在 R1，W2 複製體只放在 R2～R5。

## 3-3 單次 spin 的流程

Base Game 與 Free Game 共用同一套流程，只差在輪帶表、金框顆數權重與連消倍數階梯。

1. 決定本次 spin 的輪帶表

Base Game：依 Table Selection Weight - Base Game 抽出

Free Game：依 Table Selection Weight - Free Game 抽出（每場各自抽）

2. R1～R5：依 Symbol Weight 抽停點，從停點起連續取 4 格填入該輪

3. 依該表的金框顆數權重在 R2～R4 套上金框（見 2-3／2-4／2-7）

4. Cascade 迴圈：

4-1 判定所有 Ways（見 3-4）

4-2 沒有中獎 → 離開迴圈

4-3 累加本次 Cascade 得分：Ways 得分 × 百搭倍數總和 × 連消倍數（見 3-6）

4-4 中獎的金框符號留在原位，翻成 WW 或 W2 並抽倍數（見 3-5）

4-5 其餘中獎符號（含參與中獎的 WW／W2）消除

4-6 空格依 Symbol Drop Weight 原地補牌；有補牌的輪補足金框

4-7 本次翻出的每顆 W2 丟出 2～4 顆倍數相同的 W2

4-8 連消倍數推進一階，回到 4-1

5. 統計最終盤面的 C1

6. 判定 FG 觸發／Retrigger（3 顆以上 C1）

## 3-4 判獎規則

對每一種一般符號 S（M1～M4、A、K、Q、J）：

從 R1 起，逐輪計算顯示 S 或百搭（WW／W2）的格數

遇到格數為 0 的輪即停止

L = 連續計入的輪數（必須從 R1 開始）

L ≥ 3 才得獎：

Ways = 這 L 輪格數的乘積

符號得分 = Pay Table 的 L 輪賠率 ÷ 100 × Ways

本次 Cascade 的 Ways 得分 = 所有得獎符號相加

要點：

- 金框符號以原符號判獎。

- 每種符號只取最長的連續輪數；同一盤面可有多種符號同時得獎，各自計算後相加。

- 百搭在其位置對每一種符號都計入，因此一顆百搭可同時參與多種符號的得獎；消除時只消除一次。

- C1 不參與 Ways，也不會被百搭替代。

## 3-5 Cascade 與金框符號

- 所有參與中獎 Ways 的格子一併處理；同一格即使參與多個 Ways 也只處理一次。

- 中獎的金框符號不消除。 依 Gold_Result_Weight 在原位翻成 WW 或 W2，再依 Multiplier_Wild_Weight_WW 或 Multiplier_Wild_Weight_W2 抽倍數（×1＝無倍數）。同一次 Cascade 有多顆金框中獎時，每顆各自獨立抽取。

- Base Game 限制：每一次 Base Game spin 最多出現一次 W2。該 spin 已翻出 W2 後，之後再抽到 W2 一律改為 WW，並改用 WW 的倍數權重。Free Game 沒有此限制。

- 其餘中獎格子全部消除，包含參與中獎的 WW／W2（其倍數已計入，見 3-6）。C1 永不消除。

- 原地補牌：每個空格依該輪 Symbol Drop Weight 抽一個符號補上；其餘符號（含剛翻出的 WW／W2）不移動。

- 補足金框：R2～R4 中有新補符號的輪，重新依金框顆數權重抽出顆數 N。仍在該輪的金框保留；若少於 N 顆，從本次新補、非 C1 的格子補上金框直到 N 顆（或已無合格格子）。

- 分裂：本次 Cascade 翻出的每顆 W2，依 Split_Count_Weight 抽出顆數（2／3／4），隨機放到 R2～R5 中非 C1、非 WW／W2、非該 W2 本身的格子。每顆複製體與 W2 本體完全相同、帶相同倍數；複製體不會再分裂。被複製體蓋到的金框符號直接變成 W2，金框消失。合格格數不足時，放多少算多少。

- 以新盤面重新判獎，直到沒有任何 Ways 得獎。

## 3-6 倍數百搭與得分計算

令：

- P = 3-4 的本次 Cascade Ways 得分（賠率 ÷ 100 × Ways，各得獎符號相加）

- W = 本次中獎（本次 Cascade 被消除）的所有 ×2、×3、×5 百搭倍數總和；沒有時 W = 1

- C = 連消倍數階梯（2-5）的當前階

Cascade 得分 = P × W × C × Coin In

Spin 得分    = 該 spin 所有 Cascade 得分相加

- 百搭倍數相加，不相乘；每顆百搭只計一次，不因參與的 Ways 數重複計算。

- 同一次 Cascade 的所有得獎 Ways 都乘上同一個 W × C。

- 未參與中獎的倍數百搭不計入，留在盤面上，等之後參與中獎時才計入。

- 例：連消倍數 ×3，中獎用到一顆 ×2 與一顆 ×5 百搭 → 本次 Cascade 所有得獎 Ways 乘上 3 × (2 + 5) = 21。

- C1 沒有賠率，因此沒有 Scatter 給獎。

## 3-7 Free Game

觸發：Base Game 所有 Cascade 結束後，最終盤面 3 顆以上 C1 觸發 Free Game，獲得 10 場（3、4、5 顆以上一律 10 場）。

FG 場次：每一場各自選表（2-2）、重新停輪產生盤面，以 FG 的金框權重依 3-3 流程進行。每一場的連消倍數都從 ×2 開始，依 ×2／×4／×6／×10／×20 推進。倍數百搭不會帶到下一場。

Retrigger：FG 某一場結束時最終盤面 3 顆以上 C1，追加 5 場。最後一場仍可 Retrigger。

場次上限：單次 Free Game 含 Retrigger 最多 50 場；追加 5 場會超過 50 場時只加到 50 場，達 50 場後不再追加。

FG 得分 = 所有 FG 場次的 spin 得分相加。

## 3-8 一局（一次付費 spin）的完整流程

1. 扣款：Coin In = 押注倍數 × Base Bet = 100

2. 抽一張 Base Game 卡（見第四章）

3. 依 3-3 流程進行一次 Base Game spin，取得 BG 得分

4. 若最終盤面 C1 ≥ 3：

給予 10 場

抽一張 Free Game 卡

進行 Free Game：

每一場：選表 → 以 FG 階梯依 3-3 進行

→ 3 顆以上 C1 追加 5 場（上限 50 場）

5. 該局總得分 = BG 得分 + FG 得分（上限 20,000 × Coin In）

6. 依卡片條件接受或重抽（見 4-3）

## 3-9 重要規則整理

- 1,024 Ways 從 R1 起算：符號連續出現 3 輪以上才得獎；Ways = 各輪命中格數的乘積。

- 金框只出現在 R2～R4，不會套在 C1 上；中獎的金框符號不消除，而是翻成 WW 或 W2。

- 百搭只來自金框（與 W2 複製體）；R1、輪帶與補牌都不會出現百搭。

- 百搭倍數相加：只加總參與本次中獎的百搭，再乘上連消倍數；未使用的倍數百搭留在盤面。

- 原地補牌；有補牌的輪依顆數權重補足金框。

- 每次 Base Game spin 最多一次 W2；Free Game 不限。W2 複製體沿用本體倍數。

- BG 只有 `BG_Symbol (3)` 會觸發 FG；該表只翻出無倍數的 WW。

- C1 以所有 Cascade 結束後的最終盤面計數；3 顆以上觸發 10 場（Base Game）或追加 5 場（Free Game），上限 50 場。

- 只影響畫面、不改變任何得分與 C1 數的規則：某次 spin 最後一次金框翻牌後若沒有再中獎，該次翻出的百搭顯示為無倍數 WW，該次的 W2 不丟出複製體；沒有得分的 spin，在 R2～R4 隨機挑兩個非金框、非 C1 的格子多顯示兩個金框。

# 四、卡片系統說明

## 4-1 用途

卡片系統不改變盤面的機率設定，而是在「整局結果」的層級做接受／重抽（rejection sampling），把自然機率重新塑形成目標分布。它使下列兩件事可以被直接指定：

- 單局得分的分布（各得分區間各佔多少比例）

- FG 觸發率

## 4-2 卡片的結構

卡片來自 Multiplier_Weight，分兩組：

| 卡片組 | 何時抽 | 卡片內容 |
| --- | --- | --- |
| Base Game 卡 | 每一局開始 | 64 個得分倍率區間，外加一張 Free Game 卡 |
| Free Game 卡 | 觸發 FG 後 | 64 個得分倍率區間（判定 FG 得分） |

| 型別 | 判定方式 |
| --- | --- |
| 區間卡（range） | 要求該段得分 ÷ Coin In 落在指定區間內（左開右閉） |
| 免費遊戲卡（free_game） | 不看金額，只要求這一局觸發 Free Game；同時要求觸發局的 BG 得分不超過 Base Game 卡組最高有權重區間的上限（400 倍） |

## 4-3 單局的判定流程

每一局開始：抽一張 Base Game 卡（同一局重抽期間卡片固定不變）

若抽到 free_game 卡：

重複執行 BG spin，直到「最終盤面 C1 ≥ 3」且「BG 得分 ≤ 400 倍」

再抽一張 Free Game 卡

重複執行「整段 Free Game」，直到 FG 總得分落在該卡的區間內

若抽到 range 卡：

執行一次 BG spin

若觸發了 Free Game        → 不接受，重抽

若 BG 得分不在該卡區間內  → 不接受，重抽

否則                      → 接受

每次重抽都依自然選表規則重新產生完整結果；重抽上限 10,000 次（見 4-4）。

要點：

- 判定用的是含小數的倍率（得分 ÷ Coin In），區間為左開右閉；(-1, 0] 為未得分卡。

- 區間卡一旦觸發 FG 就作廢重抽——因此 FG 觸發率由 Free Game 卡的權重決定（1/150）。

- FG 的重抽以「整段 Free Game」為單位，不是單場。

## 4-4 重抽上限與最大得分

- 每張卡最多重抽 10,000 次；達上限時停止，保留最後一次結果並計入統計（Retry Limit Exceeded）。

- 卡片抽到區間 i 後，每次嘗試命中的機率為該區間的自然機率 p_i，10,000 次都未命中的機率為 (1 − p_i)^10000。所有有權重區間的 p_i 皆高於 0.1%（見 1-7），此機率低於 0.005%，因此卡片權重直接以「權重 × 區間平均倍率」校準。

- 最大得分：每一局的總得分（Base Game + Free Game）上限為 20,000 × Coin In，即兩組卡片最高有權重區間的上限（Free Game 卡的 (10000, 20000]）。累計得分達上限時，該局立即結束，派彩以 20,000 × Coin In 計。

- 卡片系統開啟的模擬驗證（各 10⁷ 局，simulator.py 搭配 config_92.js／config_94.js）：92 版 Game RTP 91.91%（Base Game 66.97%、Free Game 24.94%、FG 週期 1/149.78、SCR 3,111,222,000）；94 版 Game RTP 93.95%（Base Game 66.82%、Free Game 27.13%、FG 週期 1/150.35、SCR 3,115,931,000）。兩版與目標的差距皆在 1.96 倍標準誤內（92 版 0.09%／0.50%；94 版 0.05%／0.71%），Retry Limit Exceeded 為 0。

## 4-5 注意事項

- 卡片權重是影響 RTP 最直接的參數。 調整輪帶、選表或金框權重會改變自然機率，但最終落點仍由卡片決定；只調盤面而不同步更新卡片權重，總 RTP 不會依預期改變，只會讓重抽次數上升。

- 重抽次數是健康度指標。 模擬報表輸出重抽統計與 Retry Limit Exceeded 次數，應一併檢視。

- 兩個 RTP 版本只差 `Weight_NB_FG`。 92 版與 94 版的 BG 卡組、FG 觸發率與共用模型完全相同。

- FG 觸發率由 `Free Game` 卡的權重鎖定。 若要改變 FG 週期，應調整該卡權重，而非調整輪帶上的 C1 分布。

---

<!-- ===== English ===== -->

# Math Document Description — 101015 Lucky Diamond

Scope: Normal Bet

| Item | Content |
| --- | --- |
| Game ID | 101015 |
| Math files | H0451.xlsx (shared natural model); H045192.xlsx (RTP 92%), H045194.xlsx (RTP 94%) |
| Version | Shared model 6; RTP models 6.0.1.2 |
| Programs | simulator.py + config.js (shared model) + config_92.js / config_94.js (RTP versions) |
| Reels | 5 reels × 4 rows, fixed window, 20 positions |
| Win evaluation | 1,024 Ways: a regular symbol pays when it appears on consecutive reels starting from the leftmost reel (R1); winning symbols are removed and refilled in place (Cascade) |
| Coin In | 100 (Base Bet 100 × Price 1) |
| Bet mode | Normal Bet |
| Game RTP | 92% (H045192.xlsx) / 94% (H045194.xlsx); Total RTP including OP Jackpot 96% |
| Max win | 20,000 × Coin In per game |

# Contents

- 1. Worksheets

- 1-1 How the program uses the xlsx parameters

- 1-2 Worksheet overview

- 1-3 Overview (shared model)

- 1-4 Parameter

- 1-5 Symbol reel sheets

- 1-6 Overview (RTP version files)

- 1-7 Multiplier_Weight, Avg_Multi and Nature_Prob

- 1-8 OP Jackpot

- 2. Game Parameters in the Parameter Sheet

- 2-1 Table Selection Weight - Base Game

- 2-2 Table Selection Weight - Free Game / Retrigger

- 2-3 Gold Count Weight - Base Game

- 2-4 Gold Count Weight - Free Game

- 2-5 Cascade Multiplier Ladder

- 2-6 Game Limit

- 2-7 Feature weights on the reel sheets

- 3. Game Logic

- 3-1 Screen layout

- 3-2 Symbols and roles

- 3-3 Flow of a single spin

- 3-4 Win evaluation

- 3-5 Cascade and golden framed symbols

- 3-6 Multiplier Wild and win calculation

- 3-7 Free Game

- 3-8 Complete flow of one paid game

- 3-9 Key rules

- 4. Card System

- 4-1 Purpose

- 4-2 Card structure

- 4-3 Acceptance flow of one game

- 4-4 Retry limit and maximum win

- 4-5 Notes

# 1. Worksheets

## 1-1 How the program uses the xlsx parameters

The math documents are split into two kinds of workbooks: the shared natural model (H0451.xlsx: reels, stop weights, refill weights, paytable, table selection, golden frame and Multiplier Wild settings, Cascade Multiplier ladder and Free Game spin counts, shared by both RTP versions) and the RTP version files (H045192.xlsx / H045194.xlsx: RTP breakdown, card weights, range mean multiples and natural probabilities, SCR). Three points are needed to map worksheet fields to program behaviour:

- Only relative weight matters.

Every field labelled Weight is a relative weight; it need not be a probability or sum to 100%. The program draws a random value within the sum of the group and maps it to an item in proportion to its weight. The sum of each group is its denominator, so raising one item also dilutes the others.

- The program reads configs converted from the xlsx.

simulator.py loads config.js (shared model) and one RTP config, config_92.js or config_94.js (RTP version files). Before running, the program checks that both configs belong to H045, that the shared model version has one digit, and that the RTP version has four parts whose first part equals the shared model version. Fields marked "used ✅" in this document are carried into the configs and affect the simulation.

- Not every field is used by the program.

The symbol count statistics on the left of each reel sheet, the text Symbol columns and the note cells are for checking only and are not read. Each section below states which fields are used.

## 1-2 Worksheet overview

Shared natural model `H0451.xlsx`

| Worksheet | Provides | Affects | Used |
| --- | --- | --- | --- |
| Overview | Basic specification, Free Game spin settings, paytable | Cost, win evaluation, Free Game spins | ✅ partly |
| Parameter | Table selection weights, golden frame count weights, Cascade Multiplier ladder, Free Game spin limit | Table selection, golden frames, Cascade Multiplier, Free Game spins | ✅ |
| BG_Symbol, BG_Symbol (2), BG_Symbol (3) | Three Base Game reel sets: strips, stop weights, refill weights, golden frame result weights, split count weights, Wild multiplier weights | Base Game initial screen, cascade refill, golden frames | ✅ |
| FG_Symbol, FG_Symbol (2), FG_Symbol (3) | Three Free Game reel sets with the same content | Free Game initial screen, cascade refill, golden frames | ✅ (FG_Symbol (3) has selection weight 0 and is never used) |

RTP version files `H045192.xlsx` / `H045194.xlsx` (identical structure)

| Worksheet | Provides | Affects | Used |
| --- | --- | --- | --- |
| Overview | Version, RTP breakdown | Version check, output file name | ✅ version |
| Multiplier_Weight | Base Game / Free Game card weights | Acceptance / retry of each game result | ✅ |
| Avg_Multi | Natural mean multiple of each win-multiple range | Weight × mean multiple = pay contribution of each range | ❌ (for verification) |
| Nature_Prob | Natural probability of each win-multiple range | Eligibility check of the card weights | ❌ (for verification) |
| OP Jackpot | SCR (Scatter spin rate) | Probability conversion in the jackpot module | ❌ (used by the platform jackpot module) |

## 1-3 Overview (shared model)

| Block | Content | Used |
| --- | --- | --- |
| Model / Version | Model H0451, shared model version 6 | ✅ version check |
| Base Bet / Multiway | Bet base 100; 1,024 maximum ways | ✅ Base Bet; Multiway is for reference (the program counts the ways on the screen) |
| Coin in table | Normal Bet cost (100 × Price 1) | ✅ |
| Reel # / Visible Window Size | 5 reels, 4 positions each | ✅ screen size |
| Free Spins Setting | Free spins and retrigger spins by number of Scatters (C1); total limit 50 | ✅ (see 3-7) |
| Pay Table | Symbol code, Id, pays for 1 to 5 consecutive reels (per 100-credit bet) | ✅ win evaluation |

Pay Table (per 100-credit bet; divide by 100 for the multiple of Coin In)

| Symbol | Id | 3 reels | 4 reels | 5 reels |
| --- | --- | --- | --- | --- |
| WW (Wild) | 0 | — | — | — |
| W2 (Split Wild) | 1 | — | — | — |
| C1 (Scatter) | 2 | — | — | — |
| M1 | 3 | 25 | 75 | 125 |
| M2 | 4 | 20 | 60 | 100 |
| M3 | 5 | 15 | 45 | 75 |
| M4 | 6 | 10 | 30 | 50 |
| A | 7 | 5 | 15 | 25 |
| K | 8 | 5 | 15 | 25 |
| Q | 9 | 5 | 10 | 15 |
| J | 10 | 5 | 10 | 15 |

The columns for 1 and 2 reels are 0 for every symbol. WW, W2 and C1 have no pay of their own; C1 pays no Scatter award.

Free Spins Setting

| C1 on the final screen | Initial free spins | Retrigger spins |
| --- | --- | --- |
| 3 | 10 | 5 |
| 4 | 10 | 5 |
| 5 or more | 10 | 5 |

The maximum number of free spins is 50.

Coin In

Coin In = bet multiplier × Base Bet = 1 × 100

All RTP and multiple statistics are expressed as "total win of the game ÷ Coin In".

## 1-4 Parameter

The control panel of the shared model; see Section 2.

## 1-5 Symbol reel sheets

Three Base Game and three Free Game sheets with identical layout. Each sheet defines one set of five circular reel strips with stop weights, the refill weights used by the cascade, and the golden frame / Wild weights of that table.

| Field group | Content | Used |
| --- | --- | --- |
| Left Symbol / Description / R1~R5 / ID | Symbol counts per reel and the symbol Id map | ❌ check only |
| Symbol (J:O) | Reel strips (text) with Line # | ❌ for reading |
| Symbol ID (Q:U) | Reel strips (codes) | ✅ actual strips |
| Symbol Weight (W:AA) | Stop weight of each reel position | ✅ stop position |
| Gold_Result_Weight (AC:AD) | Weight of the two golden frame results (WW / W2) | ✅ (see 2-7) |
| Split_Count_Weight (AC:AD) | Number of W2 copies thrown out by a W2 (2 / 3 / 4) | ✅ (see 2-7) |
| Multiplier_Wild_Weight_WW, Multiplier_Wild_Weight_W2 (AC:AD) | Multiplier weights (×1 / ×2 / ×3 / ×5) of a flipped WW and of a flipped W2 | ✅ (see 2-7) |
| Symbol Drop Weight (AF:AK) | Refill weight of each symbol per reel | ✅ cascade refill |
| Gold_Count_Weight (AC:AH, BG_Symbol (3) and FG_Symbol (3) only) | Golden frame count per reel for this table only | ✅ (overrides 2-3 / 2-4 for this table) |

Reel strip lengths

| Sheet | R1 | R2 | R3 | R4 | R5 |
| --- | --- | --- | --- | --- | --- |
| BG_Symbol, BG_Symbol (2) | 176 | 170 | 180 | 172 | 173 |
| BG_Symbol (3) | 176 | 168 | 172 | 169 | 173 |
| FG_Symbol, FG_Symbol (2) | 174 | 169 | 178 | 170 | 169 |
| FG_Symbol (3) | 174 | 167 | 170 | 167 | 169 |

About `Symbol Weight`: this is the weight of a stop position, not of a symbol. The program draws a reel position by this column and fills the reel with the 4 consecutive positions from there (the strip is circular). A symbol's frequency on the initial screen therefore depends on how often it appears on the strip and on the weights of those positions.

About `Symbol Drop Weight`: a symbol × reel weight table, independent of the reel strip. Each empty position left by a cascade is refilled in place with one symbol drawn from the weights of its reel; the other symbols do not move. WW and W2 have refill weight 0, so a Wild never appears from a refill.

Roles of the six sheets

| Sheet | C1 on the strip | C1 in refill | Golden frames | Role |
| --- | --- | --- | --- | --- |
| BG_Symbol | R1 (3 positions), R3 (2) | none | 2-3 | Regular game; at most 2 C1 can be visible, so it cannot trigger the Free Game |
| BG_Symbol (2) | R2 (3), R5 (5) | none | 2-3 | High-cascade game (refill weights about 98% A / K / Q / J); at most 2 C1, cannot trigger the Free Game |
| BG_Symbol (3) | all reels (4 / 4 / 4 / 4 / 5) | yes | own Gold_Count_Weight | The only Base Game table that can trigger the Free Game; golden frames flip to WW without multiplier only |
| FG_Symbol | all reels (2 / 3 / 2 / 2 / 3) | yes | 2-4 | Free Game spins; can retrigger |
| FG_Symbol (2) | all reels (2 / 3 / 2 / 2 / 3) | yes | 2-4 | High-cascade Free Game spins (refill weights about 97% A / K / Q / J); can retrigger |
| FG_Symbol (3) | all reels (2 / 3 / 2 / 2 / 3) | yes | own Gold_Count_Weight | Not used (selection weight 0) |

> On every strip, C1 positions are spaced so that at most one C1 is visible per reel on the initial screen. Additional C1 can only come from cascade refills, which is possible only on BG_Symbol (3) and the Free Game tables. C1 on BG_Symbol / BG_Symbol (2) can be seen (and counts for the SCR in 1-8) but never reaches the trigger count.

## 1-6 Overview (RTP version files)

| Block | Content | Used |
| --- | --- | --- |
| Model / Version | Model H045192 / H045194, four-part version 6.0.1.2 | ✅ version check, output file name |
| Coin in table | Normal Bet cost and Game RTP | Target |
| Jackpot row | Bonus RTP, Link RTP, Total RTP, Hit JP Symbol appear rate | Target |
| Total Pay Back table | Base Game / Free Game pay back, Free Game trigger rate (Hit%) and cycle (Pulls/Hit) | Target |

Targets of the two RTP versions

| File | Base Game | Free Game | Game RTP | Bonus RTP | Link RTP | Total RTP | FG cycle |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H045192.xlsx | 67% | 25% | 92% | 2% | 2% | 96% | 1/150 |
| H045194.xlsx | 67% | 27% | 94% | 2% | 0% | 96% | 1/150 |

- Free Game trigger rate (Hit%) 0.6667% per game, i.e. one trigger every 150 games (Pulls/Hit).

- Total RTP = Game RTP + Bonus RTP + Link RTP. Bonus / Link parameters belong to the platform OP Jackpot module and are not part of this model; this model only provides the SCR for conversion (see 1-8).

- Hit JP Symbol appear rate is the NB SCR of the OP Jackpot sheet, expressed over the Threshold 10,000,000,000: 3,118,318,000 in both versions.

## 1-7 Multiplier_Weight, Avg_Multi and Nature_Prob

`Multiplier_Weight` is the input of the card system. Layout:

| Column | Header | Use |
| --- | --- | --- |
| A | Range | Win multiple range label |
| B | Weight_NB_BG | Base Game card weights |
| C | Weight_NB_FG | Free Game card weights |

Rows 3–66 are 64 win multiple ranges (win ÷ Coin In, left-open, right-closed), from (-1, 0] (no win) to (100000, 9999999]. The last row, Free Game, is a special card that ignores the amount and only requires the game to trigger the Free Game. See Section 4.

| Item | 92 version | 94 version |
| --- | --- | --- |
| Weight_NB_BG | Weighted ranges (-1, 0] to (350, 400], summing to 1,000,000,000; Free Game card 6,711,410; column total 1,006,711,410 | Identical to the 92 version |
| Weight_NB_FG | Weighted ranges (10, 15] to (10000, 20000], summing to 1,000,000,000 (Free Game mean 37.50×) | Same span, Free Game mean 40.50× |

- The Free Game card is drawn with probability 6,711,410 ÷ 1,006,711,410 = 1/150, which is the Free Game trigger rate.

- The two RTP versions differ only in the `Weight_NB_FG` column, i.e. the Free Game pay distribution. Weight_NB_BG and the entire shared model are identical in both versions.

`Avg_Multi` (rows correspond to Multiplier_Weight; identical in both versions; number format 0.0000):

| Column | Header | Content |
| --- | --- | --- |
| A | Range | Win-multiple range label |
| B | Avg_Multi_NB_BG | Mean multiple (win ÷ Coin In) of Base Game games falling in the range in the natural simulation with the card system off, excluding games that trigger the Free Game; the Free Game row is the mean Base Game multiple of triggering games whose Base Game win does not exceed 400× (5.4936) |
| C | Avg_Multi_NB_FG | Mean multiple of the whole Free Game (all spins including retriggers) falling in the range |

`Nature_Prob` (rows correspond; identical in both versions; number format 0.0000%):

| Column | Header | Content |
| --- | --- | --- |
| A | Range | Win-multiple range label |
| B | Nature_Prob_NB_BG | Natural probability, with the card system off, that a game not triggering the Free Game falls in the range (the 64 ranges sum to 100%); the Free Game row is the natural Free Game trigger rate per game (0.7709%, about 1/129.72) |
| C | Nature_Prob_NB_FG | Natural probability that a whole Free Game falls in the range (the 64 ranges sum to 100%) |

How to verify

Base Game pay back = Σ(Weight_NB_BG × Avg_Multi_NB_BG) ÷ column total of Weight_NB_BG

(all 65 rows, including the Free Game row)

= 674,495,989 ÷ 1,006,711,410 = 67.00%

Free Game mean multiple = Σ(Weight_NB_FG × Avg_Multi_NB_FG) ÷ 10^9

= 37.50 (92 version) / 40.50 (94 version)

Free Game pay back = Free Game mean multiple × Free Game trigger rate (1/150)

= 25.00% (92 version) / 27.00% (94 version)

Because the 64 range weights of Weight_NB_BG sum to exactly 10⁹, Σ(Weight × Avg_Multi) ÷ 10⁹ of that column (67.45%) is the same pay back expressed per 10⁹ range-card draws; dividing by the column total instead converts it to the pay back per game.

Nature_Prob is used to check that every weighted range can actually be reached: all weighted ranges have a natural probability above 0.1%, and the Free Game row shows that the natural trigger rate (1/129.72) is higher than the target trigger rate (1/150).

## 1-8 OP Jackpot

Jackpot System Reference: Math Document Description_JP. The OP Jackpot prize levels, start-up pools and contribution rates are shared across all OP Jackpot games; refer to BMM's Certification Test Report "JUMBO.1038.A.02" dated on 4th August 2026 for details of the OP Jackpot Feature RTP % calculations.

Records the SCR (Scatter spin rate) used by the platform jackpot module to convert "the theoretical trigger rate per game" into "the hit probability per spin that contains a Scatter".

| Field | Content |
| --- | --- |
| Threshold | 10,000,000,000 (SCR denominator) |
| NB | SCR = 3,118,318,000 (same for the 92 and 94 versions) |

SCR definition: number of spins whose final screen contains at least one C1 ÷ number of paid games × 10,000,000,000 (the Base Game spin and every Free Game spin each count as one spin), measured by simulation with the card system on.

Jackpot probability conversion

Pscatter = SCR ÷ 10,000,000,000 = 0.3118318

(average number of spins with at least one C1 per game)

Ptheory  = theoretical trigger probability of a jackpot prize per game

(derived from the prize's fixed pay back and amount; parameters are in the platform jackpot module)

Phit     = Ptheory ÷ Pscatter

(conditional probability of a jackpot check on each spin containing C1)

Jackpot checks only happen on spins containing C1, so checking with Phit (scaled by Pscatter) gives a long-run trigger rate equal to Ptheory. The OP Jackpot check is independent of the Free Game trigger; when both happen on the same spin, the jackpot is settled first.

# 2. Game Parameters in the Parameter Sheet

## 2-1 Table Selection Weight - Base Game

| Sheet | Weight |
| --- | --- |
| BG_Symbol | 4 |
| BG_Symbol (2) | 1 |
| BG_Symbol (3) | 5 |

The first action of every Base Game spin is to select the reel table with these weights (40% / 10% / 50%). The selected table supplies the strips, refill weights and golden frame / Wild weights for the whole spin, including all its cascades. Only BG_Symbol (3) can trigger the Free Game (see 1-5), so this is the most upstream parameter for game feel and Free Game frequency.

## 2-2 Table Selection Weight - Free Game / Retrigger

| Sheet | Free Game | Retrigger |
| --- | --- | --- |
| FG_Symbol | 2 | 2 |
| FG_Symbol (2) | 8 | 8 |
| FG_Symbol (3) | 0 | 0 |

Every Free Game spin draws its own table with these weights (20% / 80%), independently of the other spins. The Retrigger block holds the same values as the Free Game block; the program draws every Free Game spin, including spins added by a retrigger, with the Free Game weights. FG_Symbol (3) has weight 0 and is never selected.

## 2-3 Gold Count Weight - Base Game

Number of golden frames per reel (weight out of 100,000), used by BG_Symbol and BG_Symbol (2):

| Golden frames | R1 | R2 | R3 | R4 | R5 |
| --- | --- | --- | --- | --- | --- |
| 0 | 100000 | 40398 | 51236 | 64539 | 100000 |
| 1 | 0 | 41096 | 37292 | 29869 | 0 |
| 2 | 0 | 15678 | 10179 | 5184 | 0 |
| 3 | 0 | 2660 | 1235 | 399 | 0 |
| 4 | 0 | 169 | 58 | 10 | 0 |

- Golden frames appear on R2, R3 and R4 only; R1 and R5 always draw 0.

- A golden frame is a flag on a regular symbol, not a symbol: the strips and refill weights hold only symbol Ids 0–10. A golden framed symbol pays the same as its regular symbol.

- After the stop, the program draws the count for each of R2–R4 and places that many frames on randomly chosen non-C1 positions of the reel (C1 is never framed). If the reel has fewer eligible positions than the count, as many as possible are placed.

- After every cascade refill the count is drawn again for each reel that received new symbols (see 3-5).

## 2-4 Gold Count Weight - Free Game

Same use as 2-3, for FG_Symbol and FG_Symbol (2):

| Golden frames | R1 | R2 | R3 | R4 | R5 |
| --- | --- | --- | --- | --- | --- |
| 0 | 100000 | 43300 | 49434 | 56195 | 100000 |
| 1 | 0 | 40315 | 38084 | 34837 | 0 |
| 2 | 0 | 14075 | 11002 | 8099 | 0 |
| 3 | 0 | 2183 | 1412 | 837 | 0 |
| 4 | 0 | 127 | 67 | 33 | 0 |

BG_Symbol (3) and FG_Symbol (3) carry their own Gold_Count_Weight block on the reel sheet, which replaces 2-3 / 2-4 for that table (see 2-7).

## 2-5 Cascade Multiplier Ladder

| Mode | 1st win | 2nd win | 3rd win | 4th win | 5th win and later |
| --- | --- | --- | --- | --- | --- |
| Base Game | ×1 | ×2 | ×3 | ×5 | ×10 |
| Free Game | ×2 | ×4 | ×6 | ×10 | ×20 |

The ladder is fixed, not drawn. The n-th win of a spin uses the n-th step; once the top step is reached it stays there until the spin ends. Every spin, including every Free Game spin, starts again from the first step.

## 2-6 Game Limit

| Field | Value | Used |
| --- | --- | --- |
| Max Free Spins | 50 | ✅ |
| Free Spins Initial / Retrigger | 10 / 5 | ✅ (same as the Free Spins Setting of 1-3) |
| Note | The maximum win is set by the card system, not by the base model | ❌ text |

## 2-7 Feature weights on the reel sheets

These weights are held on each reel sheet (columns AC:AD) and apply to the table selected for the spin.

Gold_Result_Weight (result of a winning golden framed symbol)

| Sheet | WW | W2 |
| --- | --- | --- |
| BG_Symbol, BG_Symbol (2) | 90 | 10 |
| BG_Symbol (3) | 1000 | 0 |
| FG_Symbol, FG_Symbol (2) | 88 | 12 |
| FG_Symbol (3) | 100 | 0 |

Split_Count_Weight (number of W2 copies thrown out by a W2; same on all sheets)

| Copies | 2 | 3 | 4 |
| --- | --- | --- | --- |
| Weight | 4 | 2 | 1 |

Multiplier_Wild_Weight_WW / Multiplier_Wild_Weight_W2 (multiplier of a flipped Wild; ×1 means no multiplier)

| Sheet | Table | ×1 | ×2 | ×3 | ×5 |
| --- | --- | --- | --- | --- | --- |
| BG_Symbol, BG_Symbol (2), FG_Symbol, FG_Symbol (2) | WW | 50 | 120 | 65 | 15 |
| BG_Symbol, BG_Symbol (2), FG_Symbol, FG_Symbol (2) | W2 | 25 | 55 | 30 | 15 |
| BG_Symbol (3), FG_Symbol (3) | WW, W2 | 100 | 0 | 0 | 0 |

On the first four tables 80% of flipped Wilds carry a multiplier (×2, ×3 or ×5); on BG_Symbol (3) no Wild carries a multiplier.

Gold_Count_Weight (BG_Symbol (3) and FG_Symbol (3) only; weight out of 100,000)

| Sheet | Golden frames | R2 | R3 | R4 |
| --- | --- | --- | --- | --- |
| BG_Symbol (3) | 0 / 1 / 2 / 3 / 4 | 52142 / 36875 / 9779 / 1153 / 51 | 61771 / 31623 / 6071 / 518 / 17 | 72894 / 23982 / 2959 / 162 / 3 |
| FG_Symbol (3) | 0 / 1 / 2 / 3 / 4 | 38838 / 41438 / 16580 / 2948 / 197 | 44823 / 39830 / 13272 / 1966 / 109 | 51604 / 37125 / 10016 / 1201 / 54 |

R1 and R5 are always 0 golden frames (weight 100,000 on 0).

# 3. Game Logic

## 3-1 Screen layout

| Item | Value |
| --- | --- |
| Reels | 5 (R1–R5) |
| Positions per reel | 4 (fixed) |
| Total positions | 20 |
| Maximum ways | 4 × 4 × 4 × 4 × 4 = 1,024 |

Each reel takes 4 consecutive strip positions from its stop. Win evaluation and C1 counting use the whole 5 × 4 screen.

## 3-2 Symbols and roles

| Symbol | Id | Description | Role |
| --- | --- | --- | --- |
| WW | 0 | Wild | Substitutes for all symbols except C1; created only from a winning golden framed symbol; may carry ×2 / ×3 / ×5 |
| W2 | 1 | Split Wild | Substitutes for all symbols except C1; created only from a winning golden framed symbol, then throws out 2–4 identical W2; may carry ×2 / ×3 / ×5 |
| C1 | 2 | Scatter | Counted only; 3 or more on the final screen trigger the Free Game; not part of any way, never removed, never substituted, never framed |
| M1–M4 | 3–6 | High symbols | Pay |
| A, K, Q, J | 7–10 | Low symbols | Pay |
| Golden framed symbol | — | Flag on M1–M4, A, K, Q, J (R2–R4 only) | Pays as its regular symbol; when it is part of a win it is not removed and flips into WW or W2 |

WW and W2 are never on the strips and never refilled. Every Wild on the screen comes from a winning golden framed symbol (or is a W2 copy). R1 never shows a Wild: golden frames do not appear on R1 and W2 copies are placed on R2–R5 only.

## 3-3 Flow of a single spin

Base Game and Free Game share the same flow; only the reel table, the golden frame count weights and the Cascade Multiplier ladder differ.

1. Decide the reel table of this spin

Base Game: drawn by Table Selection Weight - Base Game

Free Game: drawn by Table Selection Weight - Free Game (each spin separately)

2. For R1–R5: draw a stop position by Symbol Weight and fill the reel with 4 consecutive positions

3. Place golden frames on R2–R4 by the golden frame count weight of the table (see 2-3 / 2-4 / 2-7)

4. Cascade loop:

4-1 Evaluate all ways (see 3-4)

4-2 No win → exit the loop

4-3 Add this cascade's win: ways win × Wild multiplier sum × Cascade Multiplier (see 3-6)

4-4 Winning golden framed symbols stay in place and flip into WW or W2 with a multiplier (see 3-5)

4-5 All other winning symbols, including WW / W2 that are part of the win, are removed

4-6 Empty positions are refilled in place by Symbol Drop Weight; golden frames are topped up on the refilled reels

4-7 Each W2 flipped in this cascade throws out 2–4 W2 copies with the same multiplier

4-8 Move the Cascade Multiplier to the next step and go back to 4-1

5. Count C1 on the final screen

6. Check Free Game trigger / retrigger (3 or more C1)

## 3-4 Win evaluation

For each regular symbol S (M1–M4, A, K, Q, J):

starting from R1, for each reel count the positions showing S or a Wild (WW / W2)

stop at the first reel with a count of 0

L = number of consecutive reels counted (must start at R1)

pays only when L ≥ 3:

Ways = product of the counts of those L reels

symbol win = Pay Table value (L reels) ÷ 100 × Ways

Ways win of the cascade = sum of all paying symbols

Key points:

- A golden framed symbol is evaluated as its regular symbol.

- Each symbol pays only its longest run of consecutive reels; several symbols can win on the same screen and the wins are added.

- A Wild counts for every symbol at its position, so one Wild can be part of several winning symbols; it is removed once.

- C1 is not part of any way and is never replaced by a Wild.

## 3-5 Cascade and golden framed symbols

- All positions that are part of a winning way are processed together; a position used by several ways is processed once.

- A winning golden framed symbol is not removed. It flips in place into WW or W2 by Gold_Result_Weight, then draws its multiplier from Multiplier_Wild_Weight_WW or Multiplier_Wild_Weight_W2 (×1 = no multiplier). Several golden framed symbols in the same cascade each draw independently.

- Base Game limit: at most one W2 per Base Game spin. After a W2 has been created in the spin, any further W2 result is replaced by WW and uses the WW multiplier weights. The Free Game has no such limit.

- Every other winning position is removed, including WW / W2 that are part of the win (their multipliers have been counted, see 3-6). C1 is never removed.

- Refill in place: each empty position draws one symbol from Symbol Drop Weight of its reel; the other symbols, including the newly flipped WW / W2, do not move.

- Golden frame top-up: for each of R2–R4 that received new symbols, a count N is drawn again from the golden frame count weight. Golden frames still on the reel are kept; if fewer than N remain, frames are added on newly refilled non-C1 positions until N is reached (or no eligible position is left).

- Split: each W2 flipped in this cascade draws a copy count (2 / 3 / 4) from Split_Count_Weight and places that many W2 on randomly chosen positions of R2–R5 that are not C1, WW, W2 or the W2 itself. Each copy is identical to the W2 and carries the same multiplier; copies never split again. A golden framed symbol covered by a copy becomes a W2 and loses its frame. If fewer eligible positions exist, as many copies as possible are placed.

- Wins are evaluated again on the new screen until no way pays.

## 3-6 Multiplier Wild and win calculation

Let:

- P = ways win of the cascade from 3-4 (pay ÷ 100 × Ways, summed over the paying symbols)

- W = sum of the multipliers of all Wilds with ×2, ×3 or ×5 that are part of this win (removed in this cascade); W = 1 when there are none

- C = current step of the Cascade Multiplier ladder (2-5)

Cascade win = P × W × C × Coin In

Spin win    = sum of the cascade wins of the spin

- Wild multipliers are added, not multiplied, and each Wild counts once regardless of how many ways use it.

- The same W × C applies to every winning way of the cascade.

- A Multiplier Wild that is not part of the win is not counted; it stays on the screen and counts only when it is part of a later win.

- Example: Cascade Multiplier ×3 with a ×2 Wild and a ×5 Wild in the win → every winning way of the cascade is multiplied by 3 × (2 + 5) = 21.

- C1 pays nothing, so there is no Scatter award.

## 3-7 Free Game

Trigger: after all Base Game cascades, 3 or more C1 on the final screen trigger the Free Game with 10 spins (same for 3, 4, 5 or more C1).

Free Game spins: each spin draws its own table (2-2), stops a new screen and plays the flow of 3-3 with the Free Game golden frame weights. The Cascade Multiplier of every Free Game spin starts at ×2 and follows ×2 / ×4 / ×6 / ×10 / ×20. Multiplier Wilds do not carry over between spins.

Retrigger: when a Free Game spin ends with 3 or more C1 on the final screen, 5 spins are added. The last spin can retrigger.

Spin limit: at most 50 spins per Free Game, including retriggers; if adding 5 spins would exceed 50, only the spins up to 50 are added, and no spins are added once the total has reached 50.

Free Game win = sum of the spin wins of all Free Game spins.

## 3-8 Complete flow of one paid game

1. Cost: Coin In = bet multiplier × Base Bet = 100

2. Draw a Base Game card (see Section 4)

3. Play one Base Game spin (flow in 3-3) and get the Base Game win

4. If the final screen has 3 or more C1:

award 10 spins

draw a Free Game card

play the Free Game:

each spin: draw its table → play by 3-3 with the Free Game ladder

→ 3 or more C1 add 5 spins (limited to 50)

5. Total game win = Base Game win + Free Game win (limited to 20,000 × Coin In)

6. Accept the game or retry according to the card (see 4-3)

## 3-9 Key rules

- 1,024 Ways from R1: a symbol pays on 3 or more consecutive reels from the leftmost reel; Ways = product of the matching positions per reel.

- Golden frames only on R2–R4, never on C1; a winning golden framed symbol is not removed but flips into WW or W2.

- Wilds come only from golden frames (and W2 copies); no Wild on R1, on the strips or in refills.

- Wild multipliers are added over the Wilds that are part of the win, then multiplied by the Cascade Multiplier; unused Multiplier Wilds stay on the screen.

- Refill in place; golden frames are topped up on refilled reels by the count weights.

- At most one W2 per Base Game spin; no limit in the Free Game. W2 copies carry the W2's multiplier.

- Only `BG_Symbol (3)` can trigger the Free Game in the Base Game; that table creates only WW without multiplier.

- C1 is counted on the final screen after all cascades; 3 or more trigger 10 spins (Base Game) or add 5 spins (Free Game), limited to 50.

- Display-only rules that do not change any win or C1 count: if no further win follows the last golden frame flip of a spin, the Wilds of that flip are shown as WW without multiplier and a W2 of that flip throws out no copies; on a spin with no win, two additional golden frames are shown on random non-framed, non-C1 positions of R2–R4.

# 4. Card System

## 4-1 Purpose

The card system does not change the reel probabilities. It accepts or retries (rejection sampling) at the level of the whole game result, reshaping the natural distribution into the target distribution. It allows two things to be set directly:

- the distribution of the game win (the share of each win range)

- the Free Game trigger rate

## 4-2 Card structure

Cards come from Multiplier_Weight in two groups:

| Card group | Drawn when | Content |
| --- | --- | --- |
| Base Game cards | At the start of every game | 64 win multiple ranges plus one Free Game card |
| Free Game cards | After the Free Game is triggered | 64 win multiple ranges (applied to the Free Game win) |

| Type | Condition |
| --- | --- |
| Range card (range) | The win ÷ Coin In must fall in the range (left-open, right-closed) |
| Free Game card (free_game) | Ignores the amount and requires the game to trigger the Free Game; the Base Game win of the triggering spin must also not exceed the upper bound of the highest weighted Base Game range (400×) |

## 4-3 Acceptance flow of one game

Start of each game: draw one Base Game card (the card stays fixed during retries)

If a free_game card is drawn:

repeat the Base Game spin until "final C1 ≥ 3" and "Base Game win ≤ 400×"

draw one Free Game card

repeat the whole Free Game until its total win falls in the card's range

If a range card is drawn:

play one Base Game spin

Free Game triggered             → reject and retry

Base Game win outside the range → reject and retry

otherwise                       → accept

Every retry regenerates a complete result with the natural table selection; the retry limit is 10,000 (see 4-4).

Key points:

- The check uses the exact multiple (win ÷ Coin In); ranges are left-open, right-closed; (-1, 0] is the no-win card.

- A range card that triggers the Free Game is always rejected, so the Free Game trigger rate is set by the weight of the Free Game card (1/150).

- Free Game retries are done for the whole Free Game, not per spin.

## 4-4 Retry limit and maximum win

- Each card is retried at most 10,000 times; at the limit, the last result is kept and counted in the statistics (Retry Limit Exceeded).

- For a card on range i, each attempt hits with the range's natural probability p_i, so the chance of missing 10,000 times is (1 − p_i)^10000. Every weighted range has p_i above 0.1% (see 1-7), so this chance is below 0.005% and the card weights are calibrated directly as weight × range mean multiple.

- Maximum win: the total win of one game (Base Game + Free Game) is limited to 20,000 × Coin In, the upper bound of the highest weighted range of the two card groups ((10000, 20000] of the Free Game cards). When the accumulated win reaches the limit, the game ends and pays 20,000 × Coin In.

- Simulation with the card system on (10⁷ games each, simulator.py with config_92.js / config_94.js): 92 version Game RTP 91.91% (Base Game 66.97%, Free Game 24.94%, Free Game cycle 1/149.78, SCR 3,111,222,000); 94 version Game RTP 93.95% (Base Game 66.82%, Free Game 27.13%, Free Game cycle 1/150.35, SCR 3,115,931,000). Both deviations from the target are within 1.96 standard errors (92 version: 0.09% vs 0.50%; 94 version: 0.05% vs 0.71%), and Retry Limit Exceeded is 0.

## 4-5 Notes

- Card weights are the most direct RTP control. Changing reels, table selection or golden frame weights changes the natural probabilities, but the final distribution is still decided by the cards; changing the screen settings without updating the card weights does not move the total RTP as expected and only raises the retry count.

- The retry count is a health indicator. The simulation report outputs retry statistics and the Retry Limit Exceeded count; review them together.

- The two RTP versions differ only in `Weight_NB_FG`. The Base Game cards, the Free Game trigger rate and the shared model are identical for 92 and 94.

- The Free Game trigger rate is fixed by the weight of the `Free Game` card. To change the Free Game cycle, adjust that weight rather than the C1 distribution on the reels.
