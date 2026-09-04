window.H028_VERSION_MANIFEST = {
  "current": "3.2.0.1",
  "version_rule": {
    "main_model": "H0281.xlsx 共用數學參數有變更：第一碼 +1，後三碼歸零。",
    "multiplier_weights": "只調整卡片／倍率權重：第二碼 +1，後兩碼歸零。"
  },
  "versions": [
    {
      "version": "3.2.0.1",
      "date": "2026-08-14",
      "base_config": "Versions/3.2.0.0/config.js",
      "configs": {
        "88B": "Versions/3.2.0.0/config_88B.js",
        "90B": "Versions/3.2.0.0/config_90B.js",
        "92A": "Versions/3.2.0.0/config_92A.js",
        "94A": "Versions/3.2.0.0/config_94A.js"
      },
      "changes": [
        "新增 88B／90B Oldhand Normal Bet：RTP 分別為 72:16 與 72:18，並以 FG 週期為主要調整方式。",
        "新增 config_88B.js／config_90B.js，index 與 XLSX/config 雙向工具同步支援。",
        "修正共用 Setting 區塊的 Version 控制項被遊戲端 CSS／清除程式隱藏的問題。",
        "Card System Retry Limit 依規範統一調整為 10,000 次。"
      ]
    }
  ]
};
