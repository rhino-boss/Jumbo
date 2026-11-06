# GameRule規範

存放位置：遊戲專案根目錄 `game_rule.md`。

Game Rule 是遊戲規則說明文件。

## 1. 用途

Game Rule 用於設定遊戲玩法規則，是數學模型、Config、Simulator、Demogame、Help 與測試案例共同遵循的規則來源。

## 2. 必要規則

- 每款遊戲必須提供 `game_rule.md`，並明確定義遊戲基礎設定、得分方式、Symbol 功能、判獎順序、Bet Mode、BG／FG 流程、Feature、Retrigger、Multiplier、Max Win、Jackpot 與例外處理。
- Game Rule 必須沿用本節定義的固定章節骨架、標題層級、表格形式及規則表達方式。
- 數學模型、Config、Simulator、Demogame 與 Help 不得自行補充或改寫 `game_rule.md` 未定義的玩法。
- 規則變更時，必須同步檢查並更新數學文件、Config、Simulator、Demogame、`{GameID}_Help.xlsx`、`game_help_draft.md` 與測試案例。
- Game Rule 與其他來源內容衝突時，必須先確認正式規則，不得由開發端自行選擇其中一種實作。

Game Rule 必須保留下列基本結構：

| 順序 | 章節 | 格式要求 |
|---:|---|---|
| 1 | `§1. 遊戲基本資訊` | 使用「項目／說明」表格記錄本節規定的基礎資料。 |
| 2 | `§2. 盤面結構` | 包含盤面示意圖與 Reel／Row、得分方向及補牌流程的文字說明。 |
| 3 | `§3. 符號類別` | 分開定義一般符號與特殊符號，說明出現位置、替代關係及功能。 |
| 4 | `§4. 賠率表（Pay Table）` | 使用表格列出符號、得分數量及倍率口徑。 |
| 5 | `§5. 核心特色` | 依遊戲機制建立子章節，完整說明特色符號、轉換、Multiplier 或其他核心玩法。 |
| 6 | `§6. 免費遊戲（Free Spins / Free Game, FG）` | 分別定義觸發、FG 玩法及 Retrigger。 |
| 7 | `§7. 核心遊戲流程（Base Game）` | 依實際執行順序編號描述 Spin、判獎、消除／補牌、結算與 Feature Trigger。 |
| 8 | `§8. 押注模式` | 依遊戲實際支援內容分別說明 Extra Bet 與 Buy Feature。 |
| 9 | `§9. 邊界 / 例外情境（Edge Cases）` | 依機制分類列出可直接驗證的邊界條件及例外處理。 |

`§1. 遊戲基本資訊` 必須包含下列欄位：

- `Game ID`
- `PARsheet ID`
- `遊戲中文名稱`
- `遊戲英文名`
- `遊戲類型`：依實際遊戲機制列出完整類型，例如 `2,025–32,400 Ways / Megaways / Cascade`。
- `盤面規格`
- `中獎方式`：使用 `Line Game`、`Way Game`、`Pay Anywhere` 或 `Cluster Pay`；只能選擇符合實際判獎邏輯的類型。
- `押注模式`

`§8. 押注模式` 依遊戲實際支援內容包含：

- `Extra Bet`：遊戲有 Extra Bet 時，說明價格、流程與 Normal Bet 的差異；沒有時可省略此子章節。
- `Buy Feature（購買特色）`：遊戲有 Buy Feature 時，說明購買價格、入口 Spin、FG 觸發方式與得分計算；沒有時可省略此子章節。

- §1～§9 的章節名稱與順序不得任意更動；遊戲沒有 FG 時，仍須保留 §6 並明確寫「不適用」或「不提供」。
- 可依各遊戲機制在固定章節下新增子章節，但不得改變核心章節順序。
- 規則必須以開發與測試可直接實作、驗證的方式描述，不得只使用宣傳文案或未定義的概念性敘述。

遊戲類型的統一命名規則見[Demogame規範.md](Demogame規範.md)第 1.1 節；Game Rule、Demogame 與 Help 必須使用相同術語。

## 3. 交付檢查

- [ ] `game_rule.md` 已涵蓋所有實際支援的玩法、模式與 Feature。
- [ ] Game Rule 已依本節規定的 §1～§9 基本格式建立，固定章節、順序與表格形式完整。
- [ ] §1 已包含 Game ID、PARsheet ID、中英文名稱、遊戲類型、盤面規格、中獎方式與押注模式。
- [ ] §8 已依實際支援內容完整說明 Extra Bet 與 Buy Feature。
- [ ] 判獎順序、倍率分母、觸發條件、結束條件與上限均可直接實作及測試。
- [ ] Game Rule 與數學模型、Config、Simulator、Demogame 及 Help 的規則一致。
