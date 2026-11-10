window.H032_VERSION_MANIFEST = {
  "current": "2.0.0.0",
  "version_rule": {
    "format": "遊戲參數.卡片權重.SCR.其他文件",
    "retention": "只有第 1、2 碼不同的數學版本分開保留；第 1、2 碼相同時只保留第 3、4 碼最新版本。"
  },
  "versions": [
    {
      "version": "1.0.0.0",
      "math_key": "1.0",
      "date": "2026-11-06",
      "working": false,
      "configs": {
        "base": "Versions/1.0/config.js",
        "92A": "Versions/1.0/config_92A.js",
        "94A": "Versions/1.0/config_94A.js"
      },
      "changes": [
        "輪帶以超級鑽石 H045 為底，R2～R5 一般符號重排；賠率沿用 H045。",
        "黃底在 R2～R5、倍數 1X～10X，滾停平均 2.67 顆；FG 後段黃底（FG Late Yellow）與後段表 FG_Symbol (4)。",
        "自然 RTP NB 約 202%、BF 約 160%，BG Hit 25%、FG Hit 49%、FG 週期約 1/206；卡片權重仍是 H045 的。",
        "封存於 Versions/1.0（Source、Config、Simulator、game_rule）。"
      ]
    },
    {
      "version": "2.0.0.0",
      "math_key": "2.0",
      "date": "2026-11-09",
      "working": true,
      "configs": {
        "base": "config.js",
        "92A": "config_92A.js",
        "94A": "config_94A.js",
        "92A_Bet100": "config_92A_Bet100.js"
      },
      "changes": [
        "輪帶、停輪權重、補牌權重與賠率以 JILI Super Ace 為底（側錄還原）；R2～R5 一般符號重排（相鄰軸偏重不同符號組，BG 85%、FG 72%），BG 含 C1 停點權重 ×0.65。",
        "黃底只在 R2～R4，各軸比例與倍數分布（1/2/3/5/10/20/30/50/100）對標 DJ Boom Boom 側錄，整體密度為 DJ Boom Boom 的 80%。",
        "倍數框乘數改為「1＋盤面所有框值總和」（2026-11-10，對齊 DJ Boom Boom 實測；原為框值總和、無框 x1）。",
        "自然 RTP NB 約 476%、BF 約 215%，BG Hit 25.2%、FG Hit 46%、FG 週期約 1/209。",
        "卡片權重依 v2 自然機率報表重算（2026-11-10 乘數改 1＋框總和後重算，A 版）：NB 老手 BG 67%＋FG 25%（94A FG 27%）、新手 BG 67%＋FG 26%、FG 週期 1/200、BG Hit 25%、FG 保底 5x；BF 價格 100x、RTP 92.5%；拿掉 Extra Bet。B 版未重算。"
      ]
    }
  ]
};
