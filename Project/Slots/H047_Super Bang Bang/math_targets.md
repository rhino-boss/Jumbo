# H047 Super Bang Bang：RTP 與卡片區間目標

> 文件版本：v0.2（開案目標）  
> 更新日期：2026-08-21  
> 狀態：依共用新老手期與押注層級規格重整；正式權重須以 H047 Card System Off 自然模擬求解

## 1. 專案定位

- Game ID：`H047`
- 遊戲名稱：`Super Bang Bang`
- 盤面：5×4、1024 Ways、Cascade
- 支援模式：
  - `bet_mode = 0`：Normal Bet，成本 `1x`
  - `bet_mode = 2`：Buy Feature，成本 `100x`
- Player Profile：Newbie、Oldhand。
- Oldhand 依 `bet_tier_amount` 分為小 Bet、中 Bet、大 Bet；Normal Bet 使用實際押注金額，Buy Feature 使用購買價格除以 100x 後的基礎押注。
- 不建立未使用的 Extra Bet、Super Feature 或空白 B Variant。

## 2. 付費遊戲 RTP 目標

### 2.1 Normal Bet

RTP 配置使用 `Link + Bonus Game + Game = Total RTP`：

| Player Profile | 押注層級 | 押注層級判定金額 | Link RTP | Bonus Game RTP | Game RTP | Total RTP | Config 家族 |
|---|---|---:|---:|---:|---:|---:|---|
| Newbie | 不分層級 | 全部 | 0.00% | 2.00% | 93.00% | 95.00% | Newbie 共用 |
| Oldhand | 小 Bet | `< $2` | 0.00% | 2.00% | 94.00% | 96.00% | `94A` |
| Oldhand | 中 Bet | `>= $2` 且 `<= $100` | 2.00% | 2.00% | 92.00% | 96.00% | `92A` |
| Oldhand | 大 Bet | `> $100` | 2.00% | 2.00% | 92.00% | 96.00% | `92A` |

- `$2`、`$100` 都屬於中 Bet。
- Normal Bet：`bet_tier_amount = Normal Bet 實際押注金額`。
- Buy Feature：`bet_tier_amount = Buy Feature 購買價格 ÷ 100`。
- Buy Feature 購買 `$100` 時，`bet_tier_amount = $1`，屬於小 Bet 且不可拉 Link。
- Buy Feature 購買 `$200` 時，`bet_tier_amount = $2`，屬於中 Bet 並可拉 Link。
- H047 的數學文件必須進一步標示實際派彩如何歸入 Link、Bonus Game、Game，三者不可重複計算。

### 2.2 Buy Feature

| Player Profile | 押注層級 | Buy Feature 基礎押注 | Link RTP | Bonus Game RTP | Game RTP | Total RTP |
|---|---|---:|---:|---:|---:|---:|
| Newbie | 不分層級 | 全部 | 0.00% | 4.00% | 92.50% | 96.50% |
| Oldhand | 小 Bet | `< $2` | 0.00% | 4.00% | 92.50% | 96.50% |
| Oldhand | 中 Bet | `>= $2` 且 `<= $100` | 2.00% | 2.00% | 92.50% | 96.50% |
| Oldhand | 大 Bet | `> $100` | 2.00% | 2.00% | 92.50% | 96.50% |

- H047 Buy Feature Price 為 100x，因此 `Buy Feature 基礎押注 = 購買價格 ÷ 100`。
- 92.50% 是 Buy Feature 的 Game RTP 分項；加上 Link 與 Bonus Game 後，Total RTP 為 96.50%。
- Newbie 與 Oldhand 小 Bet 必須使用不同 Player Profile 權重，不得因 RTP 拆分相同而共用同一套權重。

## 3. 倍率上限

| Player Profile | 押注層級 | BG Max Multiplier | FG Max Multiplier |
|---|---|---:|---:|
| Newbie | 不分層級 | `30x` | `120x` |
| Oldhand | 小 Bet | 依 H047 正式遊戲規格 | `20000x` |
| Oldhand | 中 Bet | 依 H047 正式遊戲規格 | `20000x` |
| Oldhand | 大 Bet | 依 H047 正式遊戲規格 | `2000x` |

- 等於上限時可接受；超過上限時必須依正式 Max Win 流程截斷或重跑。
- H047 現有規則草稿仍寫 `1024x`，與新的 Oldhand FG 上限規格衝突；正式模型開始前必須同步修訂 Game Rule。

## 4. 卡片區間與權重組合

### 4.1 區間

- 使用 `slot_development_specification.md` 第 1.5 節的共用倍率區間。
- 所有 `range` 卡使用 `(min, max]`；包含 0x 的首格為 `(-1, 0]`。
- 超過目前 Profile／押注層級 Max Multiplier 的區間保留，但權重固定為 0。

各組合的最高可用 FG 區間：

| Profile／押注層級 | 最高可用 FG 區間 |
|---|---|
| Newbie | `(100, 120]` |
| Oldhand 小 Bet | `(10000, 20000]` |
| Oldhand 中 Bet | `(10000, 20000]` |
| Oldhand 大 Bet | `(1000, 2000]` |

Newbie BG 的最高可用區間為 `(25, 30]`。

### 4.2 權重組合

```text
newbie
├─ normal_bet
│  ├─ weight_bg
│  └─ weight_fg
└─ buy_feature
   └─ weight_fg

oldhand
├─ normal_bet
│  ├─ small_bet
│  │  ├─ weight_bg
│  │  └─ weight_fg
│  ├─ medium_bet
│  │  ├─ weight_bg
│  │  └─ weight_fg
│  └─ big_bet
│     ├─ weight_bg
│     └─ weight_fg
└─ buy_feature
   ├─ small_bet
   │  └─ weight_fg
   ├─ medium_bet
   │  └─ weight_fg
   └─ big_bet
      └─ weight_fg
```

- Oldhand 小／中／大 Bet 三套權重分開求解，不互相 fallback。
- 不得把其中一套權重直接縮放或截斷後當成另一個押注層級。
- Normal Bet 的 FG 觸發事件卡與一般 BG range 分開計算。
- Buy Feature 的 Oldhand 小／中／大 Bet Feature 權重也必須分開求解，不再使用單一共用 Oldhand 權重。

## 5. Link 資格

- Newbie：`link_enabled = false`，不得觸發或獲得 Link 彩金。
- Oldhand 小 Bet：`link_enabled = false`，不得觸發或獲得 Link 彩金。
- Oldhand 中 Bet：`link_enabled = true`，Link RTP 目標 2.00%。
- Oldhand 大 Bet：`link_enabled = true`，Link RTP 目標 2.00%。
- 上述 Link 資格同時適用 Normal Bet 與 Buy Feature；Buy Feature 必須先以購買價格除以 100x 計算 `bet_tier_amount`。
- Link 關閉時不得出現已觸發但不派彩的 Link 結果或演出。

## 6. 正式權重與驗收門檻

- 正式權重只能由 H047 Card System Off 的 `Multiplier Line` 自然資料求解。
- 自然機率不足以支撐 Retry 的區間必須設為 0，不得為了填滿高倍尾段強制給權重。
- `retry_limit = 10000`。
- 每組倍率權重總和固定為 `1,000,000,000`，以 largest remainder 整數化後修正 RTP residual。
- Newbie、Oldhand 小 Bet、Oldhand 中 Bet、Oldhand 大 Bet 必須分開模擬。
- Normal Bet 必須用實際押注金額驗證 `$1.99`、`$2`、`$100`、`$100.01` 邊界。
- Buy Feature 必須用購買價格除以 100x 後的基礎押注驗證相同邊界；至少驗證購買 `$100` 為小 Bet、購買 `$200` 為中 Bet。
- 每一批都必須驗證：
  - `Total RTP = Link RTP + Bonus Game RTP + Game RTP`
  - Normal Bet 與 Buy Feature 各自的 RTP 拆分目標
  - Link 資格與實際 Link RTP
  - BG／FG Max Multiplier
  - 各卡片占比與區間 RTP share
  - 平均 Retry 與 Retry Limit Exceeded

## 7. 開發前必須確認

- 現有草稿中的 Game ID 仍寫成 `H902`，正式移入 H047 時必須統一為 `H047`。
- 規則草稿對 FG 乘數起始方式有互相矛盾的描述：一處寫 8 級池，另一處寫與 BG 相同的 40 格輪帶。
- 原規則草稿的 `1024x` 上限必須依第 3 節的新老手期規格重新定義。
- Scatter 是否有直接派彩、觸發盤 BG Win 是否計入 Game 或 Bonus Game RTP，必須定案。
- Link 玩法、觸發條件與彩金來源尚未出現在 H047 規則草稿，必須補齊後才能驗證 0%／2% Link RTP。
- 上述核心規則未確認前，不產生正式卡片權重。
