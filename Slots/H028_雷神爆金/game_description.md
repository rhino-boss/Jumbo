# H028 雷神爆金1000（Thunder Boost 1000, 101016）Game Description

> 文件目的：說明遊戲模型參數的使用方式與各參數對應的實際遊戲功能（依《數學文件規範》Game Description 節）。
> 版本：共用模型 `3`／RTP 模型 `3.5.0.0`（2026-09-08）
> 一致性來源：`game_rule.md`、`Source/H0281.xlsx`、`Source/H0281<RTP><版型>.xlsx`（含 `_Bet100` 大 Bet 模型）
> 參數或選表邏輯更新時，本文件必須同步更新。

---

## §1. 模型檔案與資料所有權

| 檔案 | 資料所有權 | 執行檔 |
| --- | --- | --- |
| `Source/H0281.xlsx` | 自然機率：輪帶、停輪權重、賠率、大符號版型、Mystery、Post Scatter、Drop、FG 場數、選表權重 | `config.js`（版本單一整數 `3`） |
| `Source/H028188B.xlsx`／`H028190B.xlsx`／`H028192A.xlsx`／`H028194A.xlsx` | RTP 版本：卡片（倍率）權重、OP Jackpot SCR | `config_88B.js`～`config_94A.js`（四碼 `3.5.0.0`） |
| `Source/H028192A_Bet100.xlsx`／`H028188B_Bet100.xlsx` | 大 Bet（>$100）獨立模型：同 92A／88B，僅老手 FG 卡（`Weight_NB_FG`）與 BF 卡（`Weight_BF`）上限 2,000x | `config_92A_Bet100.js`／`config_88B_Bet100.js`（同版本、同 SCR） |

Simulator 與 index 同時載入 base config 與 RTP config：自然機率以 base 為準、卡片與版本以 RTP config 為準；兩者 `game_id`（101016）與主版本必須相同。

---

## §2. 共用模型參數（`H0281.xlsx` → `config.js`）

| 參數 | 用途 | 使用模式 | 選表條件 | 限制 | 模型／Config 欄位 |
| --- | --- | --- | --- | --- | --- |
| `ReelWeight` | BG 輪帶表 1／2 選擇 | Normal Bet 每局抽一次 | 依權重抽 `BG_Symbol`／`BG_Symbol (2)` | 兩值皆 > 0 | `Parameter!C5:C6` → `ReelWeight` |
| `FreeReelWeight` | FG 初始輪帶表選擇 | 每段 FG 進場抽一次 | 依權重抽 FG 表 1／2／3（40%／30%／30%） | 三值皆 > 0 | `Parameter!C11:C13` → `FreeReelWeight` |
| `FreeTriggerReel` | FG Retrigger 後輪帶表選擇 | FG 內每次 retrigger 抽一次 | 同上（表 1／2／3） | 三值皆 > 0 | `Parameter!C18:C20` → `FreeTriggerReel` |
| 輪帶／停輪權重 | 盤面符號產生 | 每次 Spin | 依所選表 | 7 輪 × 200 格固定 | 各 Symbol 表 `M4:S203`／`AC4:AI203` → `*Symbol*`／`*SymbolWeight*` |
| `MegaWay` 版型 | R1~R6 大符號（1x1~1x4）版型 | 每輪停定時 | 15 種版型權重 | 大符號 Ways 只計 1 | 各表 `C33:H47` → `*MegaWay*` |
| `MY` | Mystery 符號轉換 | 盤面停定後 | 13 個轉換權重 | — | 各表 `C51:C63` → `*MY*` |
| Post Scatter | SC 產生（SC 不在初始輪帶） | 初始盤面停定後 | SC 顆數 0~7 權重 | 主盤面＋Extra Reel 皆可 | 各表 `B67:C74` → `*PostC1` |
| `Drop1~5` | Cascade 補牌符號權重 | 每次消除補牌 | 依 Cascade 段數選 Drop 表 | 7 輪 × 26 符號；可掉 SC | `AL4:AR145` → `*Drop1~5` |
| `linkpoint` | Ways 賠率表 | 每次判獎 | 3~6 連 × 各符號 | 與 game_rule §4 賠率一致 | `Overview` M1 起 `C:F` → `linkpoint` |
| `free_game_spins` | FG 觸發 SC 數與場數 | FG 觸發／retrigger | 4 SC=10 場、每 +1 SC +2 場 | 整段 FG 上限 50 場 | `Overview!A21:B25`、`A27` → `free_game_spins` |
| Bet 模式 | 押注模式定義 | — | Normal Bet（0）／Buy Feature（2，75×Bet）；無 Extra Bet | BF 觸發盤面 BG 派彩為 0 | config 固定 metadata（`supported_bet_modes`、`featurebuy`） |

---

## §3. 卡片（倍率權重）系統（RTP 工作簿 `Multiplier_Weight` → `card_system`）

卡片系統控制模擬與 Demo 的結果分布：先抽卡決定目標倍率區間，結果重骰直到落入 `(min, max]`；不改變玩家端判獎與派彩公式。

| 參數 | 用途 | 使用模式 | 選表條件 | 限制 | 模型／Config 欄位 |
| --- | --- | --- | --- | --- | --- |
| Newbie BG 卡 | 新手 BG 結果分布 | Normal Bet | `card_system_is_newbie = true` | BG 上限 30x | `Weight_NB_BG_Newbie` → `newbie.normal_bet.weight_bg` |
| Newbie FG 卡 | 新手 FG Session 分布 | Normal Bet 觸發 FG 後 | 同上 | FG 30~100x | `Weight_NB_FG_Newbie` → `newbie.normal_bet.weight_fg` |
| 老手 BG 卡 | 老手 BG 結果分布 | Normal Bet | 老手（非 newbie） | 含 `free_game` 卡（決定 FG 週期） | `Weight_NB_BG` → `oldhand.normal_bet.weight_bg` |
| 老手 FG 卡 | 老手 FG Session 分布 | Normal Bet 觸發 FG 後 | 老手 | 上限 10,000x（9K 為強制例外格）；大 Bet 模型內上限 2,000x | `Weight_NB_FG` → `oldhand.normal_bet.weight_fg` |
| BF FG 卡 | Buy Feature FG 分布 | Buy Feature | `bet_mode = 2`（四版共用同組） | 上限 10,000x；BF 只計 FG；大 Bet 模型內上限 2,000x | `Weight_BF` → `oldhand.buy_feature.weight_fg` |
| Retry Limit | 重骰次數上限 | 每張卡 | — | 規範固定 10,000 次；超限放行最後一次結果並記錄 | `card_system.retry_limit` |

- 區間規則：`(min, max]`，分母一律用 Normal Bet coin-in；每欄總和精確 1,000,000,000。
- 目標 RTP（BG：FG）：88B 72:16、90B 72:18、92A 72:20、94A 72:22；Newbie 四版共用 72:21；BF 92.5%（全 FG）。
- FG 模型週期＝`sum(weight_bg) ÷ free_game 卡權重`：92A/94A 1/300、90B 1/366.67、88B 1/375；Newbie 1/279.5。
- **大 Bet（`bet_tier_amount > $100`，規範 §1.4.3）使用獨立模型**（H027 實務）：`H028192A_Bet100.xlsx`／`H028188B_Bet100.xlsx`＋`config_92A_Bet100.js`／`config_88B_Bet100.js`。與 92A／88B 的差異只在老手 FG 卡與 BF 卡：上限 2,000x（`(2000,3000]`、`(9000,10000]` 權重 0，最高權重區間 `(1000,2000]`），主體 20~200x 形狀不變、200~2,000x 尾端等比配平——FG RTP（20%／16%）、BF RTP（92.5%）、觸發週期與平均倍數與原模型一致，只有得分分布尾端形狀不同（詳《其他/數值報告_3.5.0.0_Bet100.html》）。批次模擬以 `config_rtp_file` 直接指定 Bet100 config，程式不做自動切換；90B／94A 為小 Bet 檔，無對應 Bet100 模型。SCR 沿用原模型值。

---

## §4. OP Jackpot 參數（RTP 工作簿 `OP Jackpot` 頁＋`Slots/OP Jackpot/JP0100{A,B,C}.xlsm`）

| 參數 | 用途 | 使用模式 | 選表條件 | 限制 | 來源欄位 |
| --- | --- | --- | --- | --- | --- |
| SCR | SC-spin 率（觸發率放大分母） | 彩金模擬啟用時 | `NB_Newbie`（C5，四版統一）／`NB`（C6，依版本）／`BF`（C7，四版共用） | 口徑＝含 ≥1 SC 的 Spin 數 ÷ 付費場數 × 10¹⁰；大 Bet 沿用 `NB` 欄 | RTP 工作簿 `OP Jackpot` 頁 |
| JP 檔案 | 彩金組成 | 批次參數 `jackpot_file` | Newbie→A、老手小 Bet(<$2)→C、老手中/大 Bet(≥$2)→B | A＝只貢獻不中 Link、B＝完整 Link、C＝僅 Bonus | `JP0100A/B/C.xlsm` |
| Option | 平台參數組 | 批次參數 `jackpot_option` | 28＝SPS use（H028 採用）；1／2 為其他平台 | — | `Parameter_List` |
| 檔位查表 | 各檔 RTP／Increment／池底／倍數 | 每次載入 | **key＝押注模式倍數**：NB 用 bet option（`bet_multi`）、BF 固定查 75 檔 | Bet Level 只縮放獎金與池，不改檔位；查無檔位即報錯（不內插） | `Parameter_List` 各列 |
| JP1 GRAND／JP2 MAJOR | 連機累進彩金 | 每 SC-spin 判定 | 押注選項 ≥ $2 才解鎖（B 檔） | 派彩＝池底＋累積，命中歸零；startup%＝RTP%−Increment% | `Parameter_List` RTP／Increment／JP1$／JP2$ |
| JP3 MINOR／JP4 MINI | 固定倍數紅利彩金 | 每 SC-spin 判定 | 全部檔案皆可中 | prize＝x × 實際押注 | `Parameter_List` JP3x／JP4x |

RTP 口徑：彩金派彩不入 `rtp_game`，另計 `rtp_link`（JP1+JP2）與 `rtp_bonus`（JP3+JP4），`rtp_total = game + link + bonus`（規範 §1.4：Newbie 0+2+93、小 Bet 0+2+94、中/大 Bet 2+2+92；BF 總 96.5）。

---

## §5. 押注參數與層級判定

| 參數 | 用途 | 使用模式 | 選表條件 | 限制 |
| --- | --- | --- | --- | --- |
| `bet_mode` | 押注模式 | 每批次 | 0＝Normal Bet、2＝Buy Feature | 101016 無 Extra Bet（1） |
| `bet_multi` | Bet Level（押注倍數） | 每批次 | 必須為 OP 模型 Setting 頁真實檔位（1,2,5,…,150,…,25000） | 大 Bet 代表檔位＝150（$150） |
| `bet_tier` | 押注層級 | 報表／卡組選擇 | 小 < $2 ≤ 中 ≤ $100 < 大；BF 以購買價 ÷ 75 判定；Newbie 不分層 | 大 Bet 觸發 big FG 卡組（§3） |

---

## §6. 版本對應

| 對象 | 版本 | 規則 |
| --- | --- | --- |
| `H0281.xlsx`／`config.js` | `3` | 共用數學參數變更：+1 |
| RTP 工作簿／config（含 Bet100） | `3.5.0.0` | `基礎.卡片.SCR.其他`：卡片權重→第 2 碼、SCR→第 3 碼 |
| 歷史版本 | `Versions/<四碼>/`＋`version_manifest.js/.json` | 數學調整寫入 Change Log |

相關文件：`game_rule.md`（完整規則）、`game_help_draft.md`／`文件/101016_Help.xlsx`（玩家文案）、`文件/101016_Math Document Description.md`＋`_EN.md`（數學文件說明）、`文件/PARsheet/`（base＋四版＋兩份 Bet100 的 R 值版）、`其他/數值報告*.html`（權重調整報告）。
