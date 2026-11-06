window.H028_VERSION_MANIFEST = {
  "current": "3.5.0.3",
  "version_rule": {
    "main_model": "H0281.xlsx 共用數學參數有變更：第一碼 +1，後三碼歸零。",
    "multiplier_weights": "只調整卡片／倍率權重：第二碼 +1，後兩碼歸零。",
    "scr": "只調整 SCR：第三碼 +1，第四碼歸零。"
  },
  "versions": [
    {
      "version": "3.5.0.3",
      "date": "2026-09-22",
      "base_config": "Versions/3.5.0.3/config.js",
      "configs": {
        "88B": "Versions/3.5.0.3/config_88B.js",
        "88B_Bet100": "Versions/3.5.0.3/config_88B_Bet100.js",
        "90B": "Versions/3.5.0.3/config_90B.js",
        "92A": "Versions/3.5.0.3/config_92A.js",
        "92A_Bet100": "Versions/3.5.0.3/config_92A_Bet100.js",
        "94A": "Versions/3.5.0.3/config_94A.js"
      },
      "sources": {
        "base": "Versions/3.5.0.3/Source/H0281.xlsx",
        "88B": "Versions/3.5.0.3/Source/H02888B.xlsx",
        "88B_Bet100": "Versions/3.5.0.3/Source/H02888B_Bet100.xlsx",
        "90B": "Versions/3.5.0.3/Source/H02890B.xlsx",
        "92A": "Versions/3.5.0.3/Source/H02892A.xlsx",
        "92A_Bet100": "Versions/3.5.0.3/Source/H02892A_Bet100.xlsx",
        "94A": "Versions/3.5.0.3/Source/H02894A.xlsx"
      },
      "changes": [
        "老手天花板配平（92A／94A／92A_Bet100 三本）：Detail「Free Game」列觸發局 BG 平均倍率 8.814467（自然值）→ 7.7609（1e9 card-off 自然量測 E[X|X≤70]，Record H0281_03_2609221714_betmode0_109）；E15 平均倍率陣列縮至第 64 列（比照 Detail_Newbie 作法，E79 改靜態值）。",
        "老手 BG (60,70] Fix Num（Detail!H35）0.227557583445012 → 0.276912971632214，配平截斷平均造成的 −0.3512pp；BG 權重由公式鏈重生，三本逐格相同（共用欄標準）。",
        "各本微調至理論 Game RTP 六位小數精確：92A 0.920000000794（免微調）、94A 0.940000000108（老手 FG (20,25] −996 → 40,561,600、(180,200] +996 → 14,685,799，總和不變）、92A_Bet100 0.919999997333（FG (60,70] Fix Num 2.0130072935 → 2.0136665013，公式鏈重生）。",
        "修復潛在壞公式（K 欄靜態化後 ANCHORARRAY 必 #REF!，先前僅補快取）：92A/94A Detail!J7/J8 改 =LOOKUP(2,1/(K86:K149<>0),P86:P149)／K163:K226 版（值 3000/3000）、94A Detail_Newbie!J7 同式（值 100）、92A Detail!N163:N226 壞公式殘骸清除。",
        "config_92A／94A／92A_Bet100：老手 normal_bet weight_bg/weight_fg 重生（每組整體縮放至精確 1e9）；新手與 BF 各組保留原值（維持與 88B/90B 系列 config 逐格一致）；excel_version → 3.5.0.3。",
        "PARsheet R 檔三份重產（0 殘留公式）；送驗包 文件/101016 更新：H028192/H028194 Overview 改前作送驗格式 RTP 主列（Base Bet｜Game RTP｜Bonus RTP｜Link RTP｜Total RTP｜Hit JP Symbol appear rate，Game RTP 顯示 6 位小數；92：0.920000+0.02+0.02=0.96、94：0.940000+0.02+0=0.96），Model 名改 H028192/H028194；Simulator config_92/config_94 重生並精簡。",
        "88B／90B／88B_Bet100 未配平（僅做 92/94 兩版，Bet100 因老手 BG 共用欄連動一併配平）：88B/90B 老手 Card-On 實跑將低於帳面約 0.35pp，已知限制。",
        "2026-09-24 Demogame 介面：符號顯示規則統一（Demogame規範 4.2.3）——Image 開時有圖格不顯示符號代號與符號框，Image 關時顯示框＋代號，代號改一般字重；純 CSS 金框加 keep-symbol-frame 保留。未修改 XLSX／Config 數學參數。",
        "2026-10-06 Demogame 介面：符號圖片開局前預載＋改用 WebP（Demogame規範 2.3 圖片預載）——DEMOGAME_IMAGE_TOGGLE 新增 images 清單（52 張，含 1x2～1x4 大符號長圖），由 demogame_common.js?v=4 開局前預載並解碼，期間擋住操作、超過 120 ms 顯示載入遮罩；載入失敗自動改文字顯示。符號圖 PNG 2,595 KB → WebP 490 KB，原 PNG 保留。驗證：本機伺服器 52／52 張預載完成、遮罩消失、Console 無例外。未修改 XLSX／Config 數學參數。"
      ]
    }
  ]
};
