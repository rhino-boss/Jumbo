# H999 幸運王牌2 — Index UI/UX 與動畫 QA

## 比對基準

- Source of truth：`Project/Slots/H015_賞金列車/index.html`
- Implementation：`Project/Slots/H999_幸運王牌2/index.html`（runtime 已內嵌）
- 完整畫面比對：`QA/h015-h999-comparison.png`
- H015 基準截圖：`QA/h015-reference.png`
- H999 實作截圖：`QA/h999-images.png`（已套用專屬圖片）
- H999 互動結果：`QA/h999-interaction.png`
- Viewport：單頁 1440 × 1160，device scale factor 1；合併比對圖 2880 × 1160

## 狀態與互動驗證

- 初始 idle 畫面可正常載入，控制列、倍數列、盤面、統計、設定與說明區均可見。
- Spin 完成一局後，餘額、局數、命中資訊與盤面會更新。
- Debug 開關可顯示 Previous、Next、Force FG、RNG 與 log 控制。
- 命中、消除、補牌、金框轉換分別使用 H015 的 `hit`、`symbol-cleared`、`symbol-refill`、`convert` 動畫狀態。
- Free Game 採 H015 的逐局 UX：觸發後由後續 Spin／Auto 逐局播放，並更新 FG Left。
- 上排倍數依需求固定為 BG `×1、×2、×3、×5、×10`，FG `×2、×4、×6、×10、×20`，不執行 H015 的倍數滾動動畫。

## 五個視覺面向

- Composition：頂部標題與統計、中央盤面、右側控制、下方設定／Help 的區塊順序與 H015 一致。
- Layout：欄距、面板寬度、按鈕排列、資訊密度與 H015 一致；H999 盤面依規則保持 5 × 4。
- Typography：字體族、字級層級、數字與標籤對比沿用 H015。
- Color：背景、面板、金色強調、按鈕狀態與除消動畫色彩沿用 H015。
- Styling：圓角、邊框、陰影、symbol 圖框與互動狀態沿用 H015。

## 差異判定

- 無 P0、P1、P2 問題。
- 預期差異：H999 為 5 × 4／1024 Ways；H015 為不同盤面結構。
- 預期差異：H999 多一個 Buy Super Feature 按鈕。
- 預期差異：依需求固定上排倍數，不套用 H015 的滾動倍數行為。
- H999 已換用專屬 symbol 素材：M1–M8、G1–G8、W1/W2 與 C1；不再依賴 H015 圖片。

## 修正紀錄

- 初版文字 symbol 已改為 H015 圖像式 symbol。
- Free Game 從一次播放完畢改為 H015 的逐局操作流程。
- 補齊 reel spin、hit、clear、refill、gold conversion 動畫階段。
- Cascade 播放順序調整為：滾停 → 顯示得分符號 → 消除並同步轉 WW → 掉落補牌 → 下一 Run。
- 掉落階段依每個保留符號實際下降格數播放 `symbol-settle`；新補入符號由盤面上方播放 `symbol-drop`，並按輪帶入短暫 stagger。
- Simulator 設定解析新增 H999 身分與必要欄位驗證，避免 Notebook／不同工作目錄誤載同名 config。
- CLI 指定 rounds 或 bet mode 時不再被 `RUN_ALL_COMBINATIONS` 改成批次執行。

final result: passed
