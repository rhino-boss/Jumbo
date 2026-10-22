# Zeus 2500 數據報告（Artifact 儀表板）

- 線上版：https://claude.ai/artifact/MzATMTQVaM9Zk2Fh2qj59z（2026-10-22 建立，私人，分享要從頁面 Share）
- `數據報告_宙斯 2500.html`：**本機直接開這個**（單一檔案，資料已內嵌；需連網載入 d3）
- `index.html`：Artifact 儀表板頁面原始碼（只能在 Artifact 內執行，直接開會沒有樣式和資料）
- `*.json`：資料集，由 `make_data.py` 從 `../數值報告_宙斯 2500.md` 的表格轉出（百分比存小數、「—」存 null）
- 報告改版後：重跑 `make_data.py`、`make_standalone.py <輸出路徑>`，再請 Claude 上傳新資料到同一個 Artifact
