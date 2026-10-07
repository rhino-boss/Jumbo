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
| [機制說明.md](機制說明.md) | 系統機制現行版本：新手體驗 D 版、老手救援 C-2（主救援、延伸救援、救援池）。 |
| [天花板說明.md](天花板說明.md) | 系統派彩天花板：BG／FG／系統賠付上限，超過整把重骰；倍率上限驗算方式。 |
| [腳本規範.md](腳本規範.md) | 表演腳本（新手體驗、Buy Feature、Free Spin 系統）的清單結構、挑選規則與交付檢查。 |
| [壓測說明書.md](壓測說明書.md) | 後端壓測要壓哪些組合、報表怎麼讀、RTP 判定標準、常見異常與處置。 |
| [Landbase/導覽.md](Landbase/導覽.md) | **Landbase 產線**：系統機制、數學文件規範（RTP 配置、Link 彩金）、送驗規範。 |
| [Reskin/數學模型規範.md](Reskin/數學模型規範.md) | **Reskin 產線**：押注結構、各市場押注選項與 Config 要求。 |

開始一項工作前，至少讀完本總覽與該工作對應的文件。

## 3. 文件存放位置

本節只說明各文件**做好之後放在哪裡**；每份文件怎麼製作，見表中對應的規範。

遊戲專案的 `文件/` 資料夾統一存放對外文件：

```text
文件/
├─ {GameID}_Help.xlsx
├─ {GameID}_Game Description.docx
├─ PARsheet/
└─ {GameID}/
```

| 存放位置 | 放什麼 | 製作方式見 |
|---|---|---|
| `文件/{GameID}_Help.xlsx` | Help 正式檔 | [數學文件規範.md](數學文件規範.md) Help 節 |
| `文件/{GameID}_Game Description.docx` | Game Description 完整版 | [數學文件規範.md](數學文件規範.md) Game Description 節 |
| `文件/PARsheet/` | PARsheet 精簡規格文件 | [數學文件規範.md](數學文件規範.md) PARsheet 節 |
| `文件/{GameID}/` | 送驗資料夾 | [送驗文件規範.md](送驗文件規範.md) 1.1 |

- `game_rule.md`、`game_description.md`、`game_help_draft.md` 放在遊戲專案根目錄，不放 `文件/`。
- `文件/{GameID}/` 只放送驗標的，外層文件不得複製進去。

## 4. 共通原則

- 數學文件與 `Source/*.xlsx` 是規格來源；程式使用的參數必須由它轉出，不得另外維護一份。
- `game_rule.md` 必須說明玩法、判獎順序、倍率口徑、Feature 流程與例外；Game Rule 是遊戲規則的正式說明來源，數學模型、程式與 Help 必須與其一致。
- Help 必須依 Game Rule 編寫，並同時維護 `{GameID}_Help.xlsx` 與對應的 Markdown 文件；兩者內容不得不一致。
- 同一項資料若在多個檔案出現，修改時必須同步更新並完成對帳。
- 會影響結果分布、RTP、觸發率、最大獎或 Retry 的修改，都必須更新版本並重新模擬。

## 5. 本資料夾的維護

本資料夾由規範維護者統一更新，各 HTML 由 md 自動產生。內容有疑問或需要修改時，請聯絡維護者，不要直接修改本資料夾的檔案。
