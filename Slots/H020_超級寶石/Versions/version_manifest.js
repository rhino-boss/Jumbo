window.H020_VERSION_MANIFEST = {
  "current": "2.0.0.0",
  "base_version": "2",
  "next_version": "3.0.0.0",
  "versions": [
    {
      "version": "1.0.1.3",
      "math_key": "1.0",
      "date": "2026-10-15",
      "competitor_initial_version": false,
      "base_config": "Versions/1.0.1.3/config.js",
      "configs": {
        "92A": "Versions/1.0.1.3/config_92A.js",
        "94A": "Versions/1.0.1.3/config_94A.js"
      },
      "workbooks": {
        "92A": "Versions/1.0.1.3/Source/H020192A.xlsx",
        "94A": "Versions/1.0.1.3/Source/H020194A.xlsx"
      },
      "changes": [
        "自 SVN Slot/IGaming/H020 複製的 92／94 版數學（H020192／H020194 改名為 H020192A／H020194A），內容未改。"
      ]
    },
    {
      "version": "2.0.0.0",
      "math_key": "2.0",
      "date": "2026-10-16",
      "competitor_initial_version": false,
      "base_config": "Versions/2.0.0.0/config.js",
      "configs": {
        "92A": "Versions/2.0.0.0/config_92A.js",
        "94A": "Versions/2.0.0.0/config_94A.js"
      },
      "workbooks": {
        "92A": "Versions/2.0.0.0/Source/H020192A.xlsx",
        "94A": "Versions/2.0.0.0/Source/H020194A.xlsx"
      },
      "changes": [
        "只改 Super Feature：停輪權重依可視 3 格的 WW 數分類：有 WW 的機率 R1 25%、R2／R3 45%，1 格：2 格：3 格全 WW = 30：25：10（輪帶不變）；R4 重轉球權重 150,000,000 → 73,000,000，R4 倍數權重往小倍數移（2X～500X：8.4M／11.5M／16.4M／15.3M／14.7M／14.3M／4.7M／4.3M／4.0M／3.4M，總和不變）。重轉次數、每次重轉倍數與 NB／EB 沿用 1.0.1.3。",
        "SF 卡片依新自然分布重解（維持原卡片形狀，只給自然機率 ≥ 0.1% 的區間），RTP 92.5%；Card-On 每轉 Hit 26.8% → 37.9%、每轉重轉 16.0% → 10.5%，沒重轉時平均倍數 ×25.5 → ×14.8、重轉每次 ×12.7 → ×11.9。",
        "模型公式修正：Regular Symbol 頁 SF 的 WW＋符號合併張數（第 97～103 列）原本引用 NB 區塊，改為引用 SF 區塊。"
      ]
    }
  ]
};
