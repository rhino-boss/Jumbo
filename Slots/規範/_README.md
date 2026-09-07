# Slot 開發規範總覽

本資料夾整理 Slot Game 從設計、實作、驗證到交付時必須遵循的規範。重點是確保數學文件、Card System、模擬程式、Demogame 與 Config 使用同一套規則與參數，避免各端各自解讀或寫死例外。

適用範圍：`Project/Slots/H0xx_遊戲名稱/` 下的新遊戲模型、既有模型改版，以及 RTP、Card System 或 Feature 參數調整。

## 規範文件清單

| 文件 | 內容 |
|---|---|
| [開發流程.md](開發流程.md) | 數學開發流程、必要產出文件、製作順序、階段關卡、各階段操作方式、重跑範圍、禁止事項與數學完成條件。 |
| [數學模型規範.md](數學模型規範.md) | 數學模型必要內容、命名、版本規則、RTP 與 Bet Mode、卡片倍率區間、開發前檢查；Card System；PARsheet。 |
| [數學文件規範.md](數學文件規範.md) | Game Rule、Help、Game Description、Game List 的內容與交付規範。 |
| [送驗文件規範.md](送驗文件規範.md) | 送驗交付物（Game Description DOCX、Math Document Description、數學模型送驗版）的命名、格式來源、內容規則、禁止內容與交付前檢查。 |
| [模擬程式規範.md](模擬程式規範.md) | Simulator 程式架構、`BATCH_RUNS`、Console 輸出、報表格式、驗證清單；Config 的轉檔、資料、驗證與版本規範。 |
| [Demogame規範.md](Demogame規範.md) | Demogame 用途與載入、共用／By Game 區域、補牌方式、Debug 與對帳、交付檢查。 |

## 開新專案必讀流程

開啟新的遊戲專案（或接手既有模型改版）前，必須依下列順序讀完相關規範：

1. 本 README：共通原則與完成條件。
2. [開發流程.md](開發流程.md)：整體流程、製作順序與階段關卡。
3. [數學模型規範.md](數學模型規範.md)：建立數學模型與 Card System 前必讀。
4. [數學文件規範.md](數學文件規範.md)：撰寫 Game Rule、Help 等文件前必讀。
5. [送驗文件規範.md](送驗文件規範.md)：製作 Game Description DOCX、Math Document Description 與數學模型送驗版前必讀。
6. [模擬程式規範.md](模擬程式規範.md)：撰寫 Simulator 與產生 Config 前必讀。
7. [Demogame規範.md](Demogame規範.md)：製作 Demogame 前必讀。

只執行部分工作時，至少要讀完本 README 與該工作對應的規範文件。

## 維護規則：HTML 同步

本資料夾另提供彙整版 `slot_development_specification.html`（全部規範合併、頁籤式），由 `_build_html.py` 從 md 自動產生。

- **任何一份 `.md` 更新後，必須在同一次修改中重跑產生器同步 HTML**：

  ```bash
  py _build_html.py
  ```

- 不得直接手改 `slot_development_specification.html`；內容修正一律改 md 再重建。

## 共通原則

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

## 完成條件

模型只有在下列條件全部成立後才可視為完成：

1. 數學規則與計算口徑明確，無未決定的核心邏輯。
2. Config 可由數學來源重建，版本與參數可追溯。
3. Simulator 已完成所有支援組合的統計驗證。
4. Card System 的權重、區間、Retry 與失敗監控通過。
5. Demogame 的代表性單局可與 Simulator 對帳。
6. [開發流程.md](開發流程.md) 第 2 節的必要產出文件（`game_rule.md`、`game_help_draft.md`／`{GameID}_Help.xlsx`、`game_description.md`、數學模型／PARsheet、`config.js`、`Simulator.py`、`index.html`、`數值報告.html`、`{GameID}_Game Description.docx`、`{GameID}_Math Document Description.md`＋`_EN.md`）全部齊備，與 Game List 均為同一正式版本，且必要的 Markdown 文件皆已同步更新。
