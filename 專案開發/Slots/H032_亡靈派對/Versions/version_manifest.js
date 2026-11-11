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
        "輪帶照 JILI Super Ace 還原帶（不重排，BG 帶長 176／168／172／169／173、FG 174／167／170／167／169），只調權重；賠率＝Super Ace（2026-11-11 輪帶表改版）。停輪與補牌權重讓相鄰軸偏重不同符號組（R2/R4 偏 M1、M3、A、Q，R3/R5 偏 M2、M4、K、J；BG 停輪 2 倍／補牌 4 倍、FG 1.6 倍／3 倍），把自然 RTP 壓回約 700%。BG 三張表定位：BG_Symbol 一般表、BG_Symbol (2) 觸發表（唯一能觸發 FG，金色符號多套在高分符號）、BG_Symbol (3) 隱性好表（金色符號數相同、多套在易連線的低分符號，補牌較易連消，單轉 RTP 約一般表 1.5 倍）；非觸發表 C1 只留在 R1／R2（盤面最多 2 顆、補牌不出 C1）。抽表 5:3:2。FG_Symbol／(2) 一般表、FG_Symbol (3) 好表（金色符號 ×1.3 且多套在低分符號，單轉 RTP 約一般表 2.3 倍）、FG_Symbol (4) R1～R3 偏低分（常中）。各表每盤金框數、C1 數差距都在 1.5 倍內。",
        "黃底（金色符號）只在 R2～R4，各軸比例對標 DJ Boom Boom 側錄，整體密度為 DJ Boom Boom 的 80%，2026-11-11 使用者要求出現率（初始盤面＋補牌）×1.5；FG 後段黃底（FG Late Yellow）停用。",
        "倍數框乘數改為「1＋盤面所有框值總和」（2026-11-10，對齊 DJ Boom Boom 實測；原為框值總和、無框 x1）。",
        "計分用本次消除「前」的框（先算分再更新框，2026-11-10 對齊 DJ Boom Boom 封包實測）。規則改版（2026-11-11）：金色符號不帶倍數，中獎變 WW、所在格子沒框就留 1X 框；每段連消全盤所有框 +1（新框從下一消起才 +1）；FG 開場不再有第 3 軸 1X 框，框整場累積到 FG 結束。",
        "自然 RTP NB 約 719%（BG 688%＋FG 31%）、BF 約 122%，BG Hit 27.5%、FG Hit 34.6%、FG 週期約 1/404（2026-11-11 輪帶表改版後）。",
        "卡片權重依 v2 自然機率報表重算（2026-11-11 輪帶表改版後重算，A 版）：NB 老手 BG 67%＋FG 25%（94A FG 27%）、新手 BG 67%＋FG 26%、FG 週期 1/200、BG Hit 25%、FG 保底 5x；BF 價格 100x、RTP 92.5%；拿掉 Extra Bet。B 版未重算。"
      ]
    }
  ]
};
