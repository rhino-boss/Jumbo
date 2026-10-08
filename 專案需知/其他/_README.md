# Slot 專案需知總覽

本資料夾（工作區根目錄的 `專案需知/`，2026-10-02 自 `Slots/專案需知/` 搬出）整理 Slot Game 從設計、實作、驗證到交付時必須遵循的專案需知。重點是確保數學文件、Card System、模擬程式、Demogame 與 Config 使用同一套規則與參數，避免各端各自解讀或寫死例外。

適用範圍：`Project/Slots/H0xx_遊戲名稱/` 下的新遊戲模型、既有模型改版，以及 RTP、Card System 或 Feature 參數調整。

## 1. 產線結構

| 位置 | 產線 | 內容 |
|---|---|---|
| `專案需知/`（根目錄各 .md） | **Omniplay** | 現行全部規範文件皆屬 Omniplay 產線 |
| `專案需知/Landbase/` | Landbase | Landbase 轉製遊戲的規範，分四頁：[導覽](Landbase/導覽.md)、[系統機制](Landbase/系統機制.md)、[數學文件規範](Landbase/數學文件規範.md)、[送驗規範](Landbase/送驗規範.md)（差異式，未覆寫者沿用 Omniplay），彙整版為 `Landbase/landbase_specification.html` |
| `專案需知/Reskin/` | Reskin | 既有遊戲換皮輸出到 Reskin（SC／GC）、Vietnam 等市場；目前有 [數學模型規範.md](Reskin/數學模型規範.md)（差異式），彙整版為 `Reskin/reskin_specification.html` |
| `專案需知/其他/` | — | 工具腳本（`_build_html.py`、`_check_xlsx_style.py`）與本總覽 |

任何一份 .md（根目錄或產線資料夾）更新後，必須執行 `其他/_build_html.py`；腳本會同時重建根目錄的 `igaming_specification.html` 與各產線資料夾的 HTML。產線規範一律採差異式：只寫該產線與 Omniplay 不同的條款，未覆寫者沿用根目錄規範。

## 2. 文件清單

| 文件 | 內容 |
|---|---|
| [開發流程.md](開發流程.md) | 數學開發流程、必要產出文件、製作順序、階段關卡、各階段操作方式、重跑範圍、禁止事項與數學完成條件。 |
| [數學模型規範.md](數學模型規範.md) | 數學模型必要內容、命名、版本規則、RTP 與 Bet Mode、卡片倍率區間、開發前檢查；Card System。 |
| [數學文件規範.md](數學文件規範.md) | Game Rule、Help、Game Description、PARsheet 的內容與交付規範。 |
| [送驗文件規範.md](送驗文件規範.md) | 送驗交付物（Game Description DOCX、Math Document Description、數學模型送驗版）的命名、格式來源、內容規則、禁止內容與交付前檢查。 |
| [模擬程式規範.md](模擬程式規範.md) | Simulator 程式架構、`BATCH_RUNS`、Console 輸出、報表格式、驗證清單；Config 的轉檔、資料、驗證與版本規範。 |
| [Demogame規範.md](Demogame規範.md) | Demogame 用途與載入、共用／By Game 區域、補牌方式、Debug 與對帳、交付檢查。 |
| [腳本規範.md](腳本規範.md) | 表演腳本（新手體驗、Buy Feature、Free Spin 系統）的清單結構、挑選規則、權重整合與交付檢查。 |
| [壓測說明書.md](壓測說明書.md) | 後端壓測要壓哪些組合、報表怎麼讀、RTP 判定標準、常見異常與處置。 |
| [後端報表筆記.md](後端報表筆記.md) | 後端 SPS（RTP Validator）逐分支 TXT 的命名、Coin in／WTIdx 對應、區段內容、指標換算、倍率權重核對方法與檢查清單。 |
| [機制說明.md](機制說明.md) | 系統機制完整說明：新手體驗（D 版，第 50／150 轉判定）、老手救援（救援池 5% 提撥；救援機制 C-2：主救援 40～400 轉區間隨機判定、延伸救援 440～1,000 轉）；舊版本在附錄。 |
| [天花板說明.md](天花板說明.md) | 系統派彩天花板：BG／FG／系統賠付上限（依押注是否超過 $1,500 分兩級），超過整把重骰；倍率上限驗算方式。 |
| [Landbase/導覽.md](Landbase/導覽.md) | **Landbase 產線**：分「系統機制」（Link 彩金參數、新手體驗、系統限制：新手／低注不拉 Link、最大賠付 $10,000,000）、「數學文件規範」（數學調性、RTP 配置 Link + Game + 新手體驗、低／高注兩級）、「送驗規範」（代號對應、與 OP 遊戲的送驗包差異）三頁；未覆寫者沿用 Omniplay。 |
| [Reskin/數學模型規範.md](Reskin/數學模型規範.md) | **Reskin 產線**：沿用來源遊戲數學，只改押注結構（100 credits × Denom × 44 組 Bet Multiplier）、各市場押注選項（Reskin SC／GC、Vietnam）與 Config 要求；未覆寫者沿用 Omniplay 數學模型規範。 |
| [提案報告規範.md](提案報告規範.md) | 遊戲提案說明簡報（.pptx）的命名、固定章節結構、頁面版式、色彩字型、內容規則與交付檢查。 |

## 3. 文件存放位置

本節只說明各文件**做好之後放在哪裡**；每份文件怎麼製作，見表中對應的規範。

遊戲專案資料夾（`Slots/H0xx_遊戲名稱/`）的結構：

```text
H0xx_遊戲名稱/
├─ game_rule.md、game_help_draft.md、game_description.md
├─ config.js、config_<RTP><Variant>.js、Simulator.py、index.html
├─ Source/        數學模型
├─ 文件/          對外文件
│  ├─ PARsheet/
│  └─ {GameID}/   送驗資料夾
├─ 其他/          數值報告等內部文件
├─ Record/        模擬報表
└─ Versions/      版本備份
```

| 存放位置 | 放什麼 | 製作方式見 |
|---|---|---|
| 專案根目錄 | `game_rule.md`、`game_help_draft.md`、`game_description.md`、`config.js`、`config_<RTP><Variant>.js`、`Simulator.py`、`index.html` | 各檔對應規範（見[開發流程.md](開發流程.md)第 2 節） |
| `Source/` | 數學模型 `H0xx1*.xlsx` | [數學模型規範.md](數學模型規範.md) |
| `文件/` | `{GameID}_Help.xlsx`、`{GameID}_Game Description.docx`（完整版）、`{GameID}_Math Document Description.md`＋`_EN.md` | [數學文件規範.md](數學文件規範.md)、[送驗文件規範.md](送驗文件規範.md) |
| `文件/PARsheet/` | PARsheet（原檔名加 `R`） | [數學文件規範.md](數學文件規範.md) PARsheet 節 |
| `文件/{GameID}/` | 送驗資料夾 | [送驗文件規範.md](送驗文件規範.md) 1.1 |
| `其他/` | `數值報告_<遊戲中文名>.md`＋`.html` | [開發流程.md](開發流程.md) 5.9 |
| `Record/` | 模擬報表 `.xlsx` | [模擬程式規範.md](模擬程式規範.md) |
| `Versions/` | 各版本的 Source、Config、Simulator 備份與 `version_manifest` | [模擬程式規範.md](模擬程式規範.md) |

- `文件/{GameID}/` 只放送驗標的，外層文件不得複製進去。
- 範例：`H026_彩罐熱舞 1000/`。

## 4. 開新專案必讀流程

開啟新的遊戲專案（或接手既有模型改版）前，必須依下列順序讀完相關規範：

1. 本 README：共通原則與完成條件。
2. [開發流程.md](開發流程.md)：整體流程、製作順序與階段關卡。
3. [數學模型規範.md](數學模型規範.md)：建立數學模型與 Card System 前必讀。
4. [數學文件規範.md](數學文件規範.md)：撰寫 Game Rule、Help 等文件前必讀。
5. [送驗文件規範.md](送驗文件規範.md)：製作 Game Description DOCX、Math Document Description 與數學模型送驗版前必讀。
6. [模擬程式規範.md](模擬程式規範.md)：撰寫 Simulator 與產生 Config 前必讀。
7. [Demogame規範.md](Demogame規範.md)：製作 Demogame 前必讀。
8. [腳本規範.md](腳本規範.md)：製作表演腳本前必讀。
9. [提案報告規範.md](提案報告規範.md)：製作提案報告（提案說明簡報）前必讀。
10. [壓測說明書.md](壓測說明書.md)：安排後端壓測與判讀壓測報表前必讀。
11. [後端報表筆記.md](後端報表筆記.md)：核對後端 SPS 報表（倍率權重、Card System）前必讀。

只執行部分工作時，至少要讀完本 README 與該工作對應的文件。

## 5. 維護規則：HTML 同步

本資料夾另提供彙整版 `igaming_specification.html`（根目錄全部規範合併、頁籤式），各產線資料夾另有自己的彙整版（如 `Landbase/landbase_specification.html`），皆由 `_build_html.py` 從 md 自動產生。

- **任何一份 `.md` 更新後，必須在同一次修改中重跑產生器同步 HTML**：

  ```bash
  py _build_html.py
  ```

- 不得直接手改任何一份彙整版 HTML；內容修正一律改 md 再重建。
- 產線資料夾內的 .md 連回根目錄規範時寫 `../檔名.md`，產生器會轉成根 HTML 的對應頁籤。

## 6. 共通原則

```text
數學文件／XLSX
      ↓ AI 轉檔與驗證
    Config
     ├─→ 模擬程式 → Record 報表
     └─→ Demogame  → 操作與逐局對帳
```

- 數學文件與 `Source/*.xlsx` 是規格來源，Config 是程式執行時的共同參數來源。
- Excel 與 Config 之間的轉換（含 `game_help_draft.md` → `{GameID}_Help.xlsx`、數學模型 → PARsheet）一律由 AI 執行；專案內不建立、不維護轉檔工具。
- 模擬程式與 Demogame 必須讀取同一份 Config，不得各自維護另一套輪帶、權重、Paytable 或 Feature 參數。
- `game_rule.md` 必須說明玩法、判獎順序、倍率口徑、Feature 流程與例外；程式不可補猜未定義的規則。
- Game Rule 是遊戲規則的正式說明來源；數學模型、程式與 Help 必須與其一致。
- Help 必須依 Game Rule 編寫，並同時維護 `{GameID}_Help.xlsx` 與對應的 Markdown 文件；兩者內容不得不一致。
- 同一項資料若在多個檔案出現，修改時必須同步更新並完成對帳。
- 未支援的 RTP、Variant、Bet Mode、Profile 或 Feature，不得出現在 Config、Simulator 批次或 Demogame 選單。
- 會影響結果分布、RTP、觸發率、最大獎或 Retry 的修改，都必須更新版本並重新模擬。

## 7. 完成條件

模型只有在下列條件全部成立後才可視為完成：

1. 數學規則與計算口徑明確，無未決定的核心邏輯。
2. Config 可由數學來源重建，版本與參數可追溯。
3. Simulator 已完成所有支援組合的統計驗證。
4. Card System 的權重、區間、Retry 與失敗監控通過。
5. Demogame 的代表性單局可與 Simulator 對帳。
6. [開發流程.md](開發流程.md) 第 2 節的必要產出文件（`game_rule.md`、`game_help_draft.md`／`{GameID}_Help.xlsx`、`game_description.md`、數學模型／PARsheet、`config.js`、`Simulator.py`、`index.html`、`數值報告_<遊戲中文名>.md`＋`.html`、`{GameID}_Game Description.docx`、`{GameID}_Math Document Description.md`＋`_EN.md`）全部齊備，與 Game List 均為同一正式版本，且必要的 Markdown 文件皆已同步更新。

## 8. 專有名詞

| 名詞 | 意義 | 說明 |
|---|---|---|
| 後端報表 | 後端 SPS（RTP Validator）依分支壓測後輸出的 TXT 報表，以壓縮檔交付（例：`JHS101027-RTP-Validator-Mode-6-By-Branch-On-Cloud-876.zip`）；每個分支一個資料夾、一份 TXT，內含 RTP 拆解、救援／JP RTP、符號命中、倍率分桶等。口頭說「SPS 的表格」「SPS 報表」都指這個。 | 讀法、指標換算與核對方法見 [後端報表筆記.md](後端報表筆記.md)；壓測要壓哪些組合與判定標準見 [壓測說明書.md](壓測說明書.md)。 |
