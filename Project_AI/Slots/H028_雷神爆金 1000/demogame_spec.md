# 101016 Demo Game Spec

## Config
- 預設 Config：`config_92A.js`
- 可切換 Config：目前僅 `config_92A.js`
- DENOM：`0.002`
- Bet Levels：`1、2、3、4、5、6、8、10、12、16、20、30、40、60、100、200、300、600、1000、1500`

## Board
- 盤面：6 輪 x 5 格可變高度，R2-R5 上方另有 4 格 Extra Reel
- 得分方式：Ways，由 R1 起連續 3 輪以上；中獎後 Cascade
- Symbol Assets：目前無圖片素材，依共用規格退化顯示 Symbol Code
- 畫面骨架：直接沿用目前工作區的 H026 `index.html` 區塊、CSS 與操作配置
- Spin 動畫：停輪前逐格更新 Symbol Code；主盤面垂直滾動，Extra Reel 由右至左滾動，Speed x1-x5 控制播放速度

## Bet Modes
- Normal：Mode 0，1x Bet
- Extra：不支援，不顯示
- Feature Buy：Mode 2，一次性支付 75x Bet，直接進入 FG

## Feature Status
- Scene：BASE GAME / FREE GAME
- Cascade：目前 Cascade 次數
- Multiplier：BG 當局倍數；FG 跨局累積倍數
- FG Left：剩餘場次 / 本次 FG 總場次

## Debug RNG
- Card Range：Oldhand Normal BG 卡片區間；與 Reel RNG 互斥
- Table RNG：BG 使用 `ReelWeight`，FG 使用 `FreeReelWeight` / `FreeTriggerReel`
- Reel RNG：7 個值（R1-R6 + Extra Reel），以各輪 `SymbolWeight` 總權重驗證
- 指定 Reel RNG 僅作用於下一個適用 Spin

## Statistics
- Hit：付費 Round 的 BG+FG Total Win > 0
- FG Trigger 分母：可自然觸發的 Normal Round；Buy Feature / Force FG 排除
- Max Multiplier：Session 中實際播放到的最高倍數

## Help
- 規則來源：`game_help_draft.md`
- 排除章節：文件前言、Game Meta、來源說明、待確認事項、編輯備註
- 離線備援：`index.html` 內嵌與來源相同的 Markdown

## Special Cases
- Config 宣告 `mode_extrabet`，但 `supported_bet_modes` 僅含 0 與 2，因此不顯示 Extra Bet。
- Demo 執行邏輯依 `Simulator.py`：4 / 5 / 6 SC 對應 10 / 12 / 14 場，FG 上限 50 場。
- 現有 `game_help_draft.md` 的 4 SC 起始場次文字仍為 8 場；Help 依共用規格逐字顯示來源，不在 HTML 內另行改寫。
