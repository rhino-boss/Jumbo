window.H016_VERSION_MANIFEST = {
  "current": "1.0",
  "version_rule": {
    "major": "輪帶、賠率、玩法流程或共用數學結構變更：第一碼 +1，第二碼歸零。",
    "minor": "只調整輪帶權重、補牌權重、金框或 Random Wild 等參數：第二碼 +1。"
  },
  "versions": [
    {
      "version": "1.0",
      "date": "2026-08-13",
      "configs": {
        "92": "Versions/1.0/config_92.js"
      },
      "changes": [
        "BG／FG 底層輪帶與停輪權重套用 Super Ace_claude.txt；每輪固定 200 格，停輪權重為正整數且最大／最小不超過 10 倍。",
        "所有 BG 表統一使用 BG_Symbol 設定，所有 FG 表統一使用 FG_Symbol 設定；Table Selection 只啟用 bg_1／fg_1。",
        "依 Super Ace 實機資料校準 BG／FG 各符號、各輪的初始與消除補牌金框比例；R1／R5 金框為 0。",
        "BG Cascade 倍率為 x1／x2／x3／x5，FG 為 x2／x4／x6／x10。",
        "BG Random Wild 權重為 36450／1401／235／18，10 萬場事件率 0.9940%；FG Random Wild 關閉。"
      ]
    }
  ]
};
