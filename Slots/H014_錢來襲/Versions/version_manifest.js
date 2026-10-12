window.H014_VERSION_MANIFEST = {
  "current": "4.0.0.0",
  "base_version": "4",
  "next_version": "5.0.0.0",
  "versions": [
    {
      "version": "1.0.0.2",
      "math_key": "1.0",
      "date": "2026-10-06",
      "competitor_initial_version": false,
      "base_config": "Versions/1.0.0.2/config.js",
      "configs": {
        "92A": "Versions/1.0.0.2/config_92A.js"
      },
      "workbooks": {
        "92": "Versions/1.0.0.2/Source/H014192A.xlsx",
        "92_Extra": "Versions/1.0.0.2/Source/H014192A_Extra.xlsx"
      },
      "changes": [
        "自 SVN Slot/IGaming/H014 複製的 92 版數學（H014192／H014192_Extra 改名為 H014192A／H014192A_Extra）。"
      ]
    },
    {
      "version": "3.0.0.0",
      "math_key": "3.0",
      "date": "2026-10-07",
      "competitor_initial_version": false,
      "base_config": "Versions/3.0.0.0/config.js",
      "configs": {
        "92A": "Versions/3.0.0.0/config_92A.js"
      },
      "workbooks": {
        "92": "Versions/3.0.0.0/Source/H014192A.xlsx",
        "92_Extra": "Versions/3.0.0.0/Source/H014192A_Extra.xlsx"
      },
      "changes": [
        "V2：Normal Bet 全部押注改為對齊 JILI Money Coming 的調性（Bet1／Bet5／Bet10 以競品擬合，Bet50／Bet100 以 Bet10 為範本外推、保留 10／00 與紅轉盤）。",
        "卡片權重以多目標非負最小平方擬合（RTP 固定 92%），≥200x 區間沿用 1.0.0.2 的權重與 B 表（Bet1 可開出 525x、Bet50 可到 2,000x）；畫面元素皆可得分（含轉盤每一格）。",
        "Extra Bet 內容沿用 1.0.0.2，版本號同步第 1 碼。"
      ]
    },
    {
      "version": "4.0.0.0",
      "math_key": "4.0",
      "date": "2026-10-12",
      "competitor_initial_version": false,
      "base_config": "Versions/4.0.0.0/config.js",
      "configs": {
        "92A": "Versions/4.0.0.0/config_92A.js"
      },
      "workbooks": {
        "92": "Versions/4.0.0.0/Source/H014192A.xlsx",
        "92_Extra": "Versions/4.0.0.0/Source/H014192A_Extra.xlsx"
      },
      "changes": [
        "相對 3.0.0.0（演出調整、派彩不變）：沒得分時 E 0 E、E E 0 各為 E E E 的 1.5 倍（Bet1 為 E 0 _＝1.5 × E E _）；沒得分時 R4 出現 2X／5X／10X 的占比加 10 個百分點；卡片非零區間等比微調維持 RTP 92%。",
        "Extra Bet 內容沿用 1.0.0.2，版本號同步第 1 碼。"
      ]
    }
  ]
};
