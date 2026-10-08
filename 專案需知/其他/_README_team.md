# 專案需知總覽

本資料夾整理 Slot Game 數學從設計、文件、送驗到系統機制時必須遵循的規範，供所有數學人員共同遵守。

適用範圍：新遊戲的數學模型、既有模型改版，以及 RTP、Card System 或 Feature 參數調整。

## 1. 產線結構

| 位置 | 產線 | 內容 |
|---|---|---|
| 根目錄各 .md | **Omniplay** | 主流遊戲的規範 |
| `Landbase/` | Landbase | Landbase 轉製遊戲的規範，分四頁：[導覽](Landbase/導覽.md)、[系統機制](Landbase/系統機制.md)、[數學文件規範](Landbase/數學文件規範.md)、[送驗規範](Landbase/送驗規範.md)；彙整版為 `Landbase/landbase_specification.html` |
| `Reskin/` | Reskin | 既有遊戲換皮輸出到 Reskin（SC／GC）、Vietnam 等市場：[數學模型規範](Reskin/數學模型規範.md)；彙整版為 `Reskin/reskin_specification.html` |
| `其他/` | — | 本總覽與 `_check_xlsx_style.py`（XLSX 格式檢查工具） |

產線規範一律採差異式：只寫該產線與 Omniplay 不同的條款，未覆寫者沿用根目錄規範。

## 2. 文件清單

| 文件 | 內容 |
|---|---|
| [數學模型規範.md](數學模型規範.md) | 數學模型必要內容、命名、版本規則、RTP 與 Bet Mode、卡片倍率區間、開發前檢查；Card System。 |
| [數學文件規範.md](數學文件規範.md) | Game Rule、Help、Game Description、PARsheet 的內容與交付規範。 |
| [送驗文件規範.md](送驗文件規範.md) | 送驗交付物的命名、格式來源、內容規則、禁止內容、SHA1 清單、Game List 更新與交付前檢查。 |
| [機制說明.md](機制說明.md) | 系統機制完整說明：新手體驗、老手救援（救援池、救援機制）；舊版本在附錄。 |
| [天花板說明.md](天花板說明.md) | 系統派彩天花板：BG／FG／系統賠付上限，超過整把重骰；倍率上限驗算方式。 |
| [腳本規範.md](腳本規範.md) | 表演腳本（新手體驗、Buy Feature、Free Spin 系統）的清單結構、挑選規則與交付檢查。 |
| [壓測說明書.md](壓測說明書.md) | 後端壓測要壓哪些組合、報表怎麼讀、RTP 判定標準、常見異常與處置。 |
| [Landbase/導覽.md](Landbase/導覽.md) | **Landbase 產線**：系統機制、數學文件規範（RTP 配置、Link 彩金）、送驗規範。 |
| [Reskin/數學模型規範.md](Reskin/數學模型規範.md) | **Reskin 產線**：押注結構、各市場押注選項與 Config 要求。 |

開始一項工作前，至少讀完本總覽與該工作對應的文件。

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
| `文件/` | `{GameID}_Help.xlsx`、`{GameID}_Game Description.docx`（完整版）、`{GameID}_Math Document Description.md`＋`_EN.md`、`game_setting.json` | [數學文件規範.md](數學文件規範.md)、[送驗文件規範.md](送驗文件規範.md) |
| `文件/PARsheet/` | PARsheet（原檔名加 `R`） | [數學文件規範.md](數學文件規範.md) PARsheet 節 |
| `文件/{GameID}/` | 送驗資料夾 | [送驗文件規範.md](送驗文件規範.md) 1.1 |
| `其他/` | `數值報告_<遊戲中文名>.md`＋`.html` | [開發流程.md](開發流程.md) 5.9 |
| `Record/` | 模擬報表 `.xlsx` | [模擬程式規範.md](模擬程式規範.md) |
| `Versions/` | 各版本的 Source、Config、Simulator 備份與 `version_manifest` | [模擬程式規範.md](模擬程式規範.md) |

- `文件/{GameID}/` 只放送驗標的，外層文件不得複製進去。
- 範例：`H026_彩罐熱舞 1000/`。

## 4. 共通原則

- 數學文件與 `Source/*.xlsx` 是規格來源；程式使用的參數必須由它轉出，不得另外維護一份。
- `game_rule.md` 必須說明玩法、判獎順序、倍率口徑、Feature 流程與例外；Game Rule 是遊戲規則的正式說明來源，數學模型、程式與 Help 必須與其一致。
- Help 必須依 Game Rule 編寫，並同時維護 `{GameID}_Help.xlsx` 與對應的 Markdown 文件；兩者內容不得不一致。
- 同一項資料若在多個檔案出現，修改時必須同步更新並完成對帳。
- 會影響結果分布、RTP、觸發率、最大獎或 Retry 的修改，都必須更新版本並重新模擬。

## 5. 專有名詞

| 名詞 | 意義 | 說明 |
|---|---|---|
| 後端報表 | 後端 SPS（RTP Validator）依分支壓測後輸出的 TXT 報表，以壓縮檔交付（例：`JHS101027-RTP-Validator-Mode-6-By-Branch-On-Cloud-876.zip`）；每個分支一個資料夾、一份 TXT，內含 RTP 拆解、救援／JP RTP、符號命中、倍率分桶等。口頭說「SPS 的表格」「SPS 報表」都指這個。 | 壓測要壓哪些組合、報表怎麼讀與判定標準見 [壓測說明書.md](壓測說明書.md)。 |

## 6. 本資料夾的維護

本資料夾由規範維護者統一更新，各 HTML 由 md 自動產生。內容有疑問或需要修改時，請聯絡維護者，不要直接修改本資料夾的檔案。
