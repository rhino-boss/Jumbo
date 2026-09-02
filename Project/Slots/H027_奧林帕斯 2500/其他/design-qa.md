# H027 FG 盤面對比 QA

- Source visual truth：本次對話圖 1（深色、不透明符號格）與圖 2（修改前 FG 灰藍盤面）。
- Implementation：`index.html` 與 `Versions/1.0/index.html`。
- Implementation screenshot：未取得；目前環境沒有可用的本機／雲端瀏覽器介面。
- Viewport：來源截圖約 457×489 px；實作驗證 viewport 未取得。
- Pixel density／CSS size：來源未提供；無法正規化比較。
- State：FG 最終盤面。

**Full-view comparison evidence**

- 來源圖 2 顯示共用 FG 藍色背景透過半透明符號底色，使盤面整體呈灰藍色。
- 程式已將 FG 的一般符號、M 符號、C1、C2、C3 改成不透明深色底，外層 FG 藍色提示維持不變。

**Focused region comparison evidence**

- 目標區域為 6×5 符號盤面；缺少修改後瀏覽器截圖，無法完成視覺並排比較。

**Findings**

- [P1] 修改後 FG 畫面尚未完成瀏覽器視覺驗證。
  - Location：FG 6×5 盤面。
  - Evidence：來源截圖可用，但目前沒有修改後實作截圖。
  - Impact：不能確認實際瀏覽器中的亮度、對比與快取結果。
  - Fix：重新整理 Index、進入 FG 並擷取同尺寸畫面後並排確認。

**Comparison history**

- 初始問題：FG 外層亮藍底透入半透明符號格。
- 修正：FG 符號格改為不透明深底，保留符號框線與外層 FG 狀態色。
- Post-fix evidence：等待修改後 FG 截圖。

**Implementation Checklist**

- [x] 根目錄與正式 v1 樣式同步。
- [x] 保留 6×5 固定比例及各符號框線。
- [x] 更新正式 v1 SHA256。
- [ ] 取得修改後 FG 截圖並完成相同狀態視覺比較。

final result: blocked
