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
        "只改 Super Feature：停輪權重依可視 3 格的 WW 數分類：有 WW 的機率 R1 35%、R2／R3 55%，1 格：2 格：3 格全 WW = 30：25：10（輪帶不變）；R4 重轉球權重 150,000,000 → 73,000,000，R4 倍數權重往小倍數移（2X～500X：13.3M／16.1M／19.6M／14.9M／12.7M／11.3M／3.5M／2.6M／2.0M／1.0M，總和不變）；每次重轉倍數權重各欄往小倍數移（各欄總和不變、權重 0 的倍數維持 0）。重轉次數與 NB／EB 沿用 1.0.1.3。",
        "SF 卡片依新自然分布重解（維持原卡片形狀，只給自然機率 ≥ 0.1% 的區間），RTP 92.5%，最高區間仍為 (10000, 20000]；Card-On 每轉 Hit 26.8% → 45.2%、每轉重轉 16.0% → 12.7%，重轉每次平均倍數 ×12.7 → ×7.0、沒重轉時 ×25.5 → ×9.9。",
        "模型公式修正：Regular Symbol 頁 SF 的 WW＋符號合併張數（第 97～103 列）原本引用 NB 區塊，改為引用 SF 區塊。"
      ]
    }
  ]
};
