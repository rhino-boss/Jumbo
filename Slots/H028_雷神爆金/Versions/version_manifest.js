window.H028_VERSION_MANIFEST = {
  "current": "3.5.0.0",
  "version_rule": {
    "main_model": "H0281.xlsx 共用數學參數有變更：第一碼 +1，後三碼歸零。",
    "multiplier_weights": "只調整卡片／倍率權重：第二碼 +1，後兩碼歸零。",
    "scr": "只調整 SCR：第三碼 +1，第四碼歸零。"
  },
  "versions": [
    {
      "version": "3.5.0.0",
      "date": "2026-09-08",
      "base_config": "Versions/3.5.0.0/config.js",
      "configs": {
        "88B": "Versions/3.5.0.0/config_88B.js",
        "88B_Bet100": "Versions/3.5.0.0/config_88B_Bet100.js",
        "90B": "Versions/3.5.0.0/config_90B.js",
        "92A": "Versions/3.5.0.0/config_92A.js",
        "92A_Bet100": "Versions/3.5.0.0/config_92A_Bet100.js",
        "94A": "Versions/3.5.0.0/config_94A.js"
      },
      "changes": [
        "大 Bet（bet_tier_amount > $100）依 H027 實務改為獨立數學模型：新增 H028192A_Bet100.xlsx／H028188B_Bet100.xlsx 與 config_92A_Bet100.js／config_88B_Bet100.js（同版本、同 SCR），Weight_NB_FG 與 Weight_BF 上限 2000x（(2000,3000]、(9000,10000] 歸零，尾端等比配平，NB FG RTP 20%／16%、BF 92.5% 與平均倍數不變）。",
        "原 92A／88B 模型移除 Weight_NB_FG_Big 欄與 config weight_fg_big（大 Bet 權重值原封搬入 Bet100 模型）；Simulator 移除自動切換，批次以 config_rtp_file 指定 Bet100。",
        "Newbie 卡片權重四版統一為 92A 值（QA 要求逐格一致）：修正 88B/90B/94A 建檔時整數化尾差（BG (-1,0]/(2,3]/(7,8]、FG (80,90]/(90,100] 各 ±1~2 單位／1e9）。",
        "統一層級：config newbie weight_bg/weight_fg、Detail_Newbie 的 Fix Num 輸入與 I/J/K/L 公式快取、Multiplier_Weight 的 Weight_NB_BG_Newbie/Weight_NB_FG_Newbie 快取，四本與 92A 逐格 0 差異。",
        "機率影響 ≤2e-9，RTP 4 位小數不變（Newbie 72+21=93%）；NB_Newbie SCR 原即統一採 92A 值，不變。",
        "老手／BF／大 Bet 卡組與其他數學參數皆未動；版本依卡片權重規則第二碼 +1：3.4.0.0 → 3.5.0.0。變更前工作簿備份 Versions/3.4.0.0/Source_Backup/*_before_newbie_unify_260908.xlsx。"
      ]
    },
    {
      "version": "3.4.0.0",
      "date": "2026-09-08",
      "base_config": "Versions/3.4.0.0/config.js",
      "configs": {
        "88B": "Versions/3.4.0.0/config_88B.js",
        "90B": "Versions/3.4.0.0/config_90B.js",
        "92A": "Versions/3.4.0.0/config_92A.js",
        "94A": "Versions/3.4.0.0/config_94A.js"
      },
      "changes": [
        "新增 92A／88B 老手大 Bet（bet_tier_amount > $100）專用 FG 卡組 weight_fg_big（Multiplier_Weight 新欄 Weight_NB_FG_Big）：FG 倍率上限由 10,000x 降為 2,000x，(2000, 3000] 與 (9000, 10000] 權重歸零。",
        "配平方式：20x～200x 主體形狀不變（92A ×0.99840、88B ×0.99931），200x～2,000x 尾端等比放大（92A ×1.18878、88B ×1.05131）吃回 RTP；權重總和精確 1e9、卡片加權平均 FG 倍率不變（FG RTP 到 4 位小數不動）。",
        "Simulator／index 於老手 NB 且押注 > $100 時自動改抽 big 卡組（BG 卡組共用）；90B／94A 為小 Bet 檔不加該欄，執行時自動退回一般 weight_fg。大 Bet SCR 沿用 NB 欄位值。",
        "一般 weight_fg／weight_bg、Newbie、BF 權重與其他數學參數皆未變動；版本依卡片權重規則第二碼 +1：3.3.2.0 → 3.4.0.0。"
      ]
    },
    {
      "version": "3.3.2.0",
      "date": "2026-09-08",
      "base_config": "Versions/3.3.2.0/config.js",
      "configs": {
        "88B": "Versions/3.3.2.0/config_88B.js",
        "90B": "Versions/3.3.2.0/config_90B.js",
        "92A": "Versions/3.3.2.0/config_92A.js",
        "94A": "Versions/3.3.2.0/config_94A.js"
      },
      "changes": [
        "OP Jackpot 頁 BF SCR 由 51,240,310,600（舊口徑外部計算值）更新為 36,921,890,400（betmode2 10^8、規範口徑實測，Record H028194A_03030000_2609072347_betmode2_108）。四版共用同值。",
        "NB／NB_Newbie SCR 維持 3.3.1.0 之值；倍率權重與其他數學參數無變更。",
        "版本依 SCR 規則第三碼 +1：3.3.1.0 → 3.3.2.0。"
      ]
    },
    {
      "version": "3.3.1.0",
      "date": "2026-09-08",
      "base_config": "Versions/3.3.1.0/config.js",
      "configs": {
        "88B": "Versions/3.3.1.0/config_88B.js",
        "90B": "Versions/3.3.1.0/config_90B.js",
        "92A": "Versions/3.3.1.0/config_92A.js",
        "94A": "Versions/3.3.1.0/config_94A.js"
      },
      "changes": [
        "OP Jackpot 頁 SCR 更新為 3.3.0.0 權重、規範口徑（≥1 SC 的 Spin 數 ÷ 付費場數 × 10^10）的 10 億場實測值：NB 依版本 88B 3,618,838,430／90B 3,621,199,650／92A 3,641,035,800／94A 3,641,760,160；NB_Newbie 四版統一採 92A 新手值 3,647,149,360。",
        "BF SCR 維持 51,240,310,600 未動（待 betmode2 大場次重測後另行更新）。",
        "版本依 SCR 規則第三碼 +1：3.3.0.0 → 3.3.1.0；倍率權重與其他數學參數無變更。"
      ]
    },
    {
      "version": "3.3.0.0",
      "date": "2026-09-04",
      "base_config": "Versions/3.3.0.0/config.js",
      "configs": {
        "88B": "Versions/3.3.0.0/config_88B.js",
        "90B": "Versions/3.3.0.0/config_90B.js",
        "92A": "Versions/3.3.0.0/config_92A.js",
        "94A": "Versions/3.3.0.0/config_94A.js"
      },
      "changes": [
        "Oldhand Normal Bet FG 與 Buy Feature FG 的 (9000, 10000] 區間依強制配置例外給權重，該區間 RTP 精確占各版本總 RTP 的 0.1%（NB 權重 88B/90B 34,498、92A 28,853、94A 29,480；BF 7,252～7,253）。",
        "20x～200x 主體區間維持原形狀等比微升（約 +0.05%），200x 以上尾端區間等比縮減（約 −5%），各押注區 FG RTP、FG 週期、Hit Rate 與 4 位小數 RTP 全部不變。",
        "Weight_BF 欄總和由 999,999,992（88B/90B 既有誤差）校正為精確 1,000,000,000；Newbie 權重完全未變動。",
        "已知限制：(9000, 10000] 自然發生率僅 0.00016%，Card Retry Limit 10,000 下抽中該卡約 98.4% 會超限放行一般 FG，實際觸發率遠低於設定權重。"
      ]
    },
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
