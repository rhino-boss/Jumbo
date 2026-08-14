window.H028_VERSION_MANIFEST = {
  "current": "3.2.0.0",
  "version_rule": {
    "main_model": "H0281.xlsx 共用數學參數有變更：第一碼 +1，後三碼歸零。",
    "multiplier_weights": "只調整卡片／倍率權重：第二碼 +1，後兩碼歸零。"
  },
  "versions": [
    {
      "version": "3.2.0.0",
      "date": "2026-08-14",
      "base_config": "Versions/3.2.0.0/config.js",
      "configs": {
        "92A": "Versions/3.2.0.0/config_92A.js",
        "94A": "Versions/3.2.0.0/config_94A.js"
      },
      "changes": [
        "Card System Retry Limit 依規範統一調整為 10,000 次。"
      ]
    },
    {
      "version": "3.1.0.0",
      "date": "2026-08-11",
      "configs": {
        "92A": "Versions/3.1/config_92A.js",
        "94A": "Versions/3.1/config_94A.js"
      },
      "changes": [
        "依 H0281_30_2608111334_betmode0_109.xlsx 的 10 億場自然分布重新計算 92A／94A、Newbie 與 Buy Feature 倍率權重。"
      ]
    },
    {
      "version": "3.0.0.0",
      "date": "2026-08-11",
      "configs": {
        "92A": "Versions/3.0/config_92A.js",
        "94A": "Versions/3.0/config_94A.js"
      },
      "changes": [
        "Free Game 場數統一為 4 SC 10 場，每多 1 SC 加 2 場，上限 50 場；場數規則由 config 統一提供給 index 與 Simulator。",
        "Free Game 所有 Table 的 R1 移除金框；初始輪帶改為同符號普通框，Drop1～Drop5 金框權重回填至對應普通符號，維持各輪總權重不變。",
        "BG、BF、FG 所有 Table 的 Extra Reel／R7 移除金框與 Golden Mystery；權重回填至對應普通符號，合併 Symbol 分布及各表總權重不變。"
      ]
    },
    {
      "version": "2.0.0.0",
      "date": "2026-08-10",
      "configs": {
        "92A": "Versions/2.0/config_92A.js",
        "94A": "Versions/2.0/config_94A.js"
      },
      "changes": [
        "目前 H028 數學基準版本；保留現行 H0281 共用參數與倍率權重。"
      ]
    }
  ]
};
