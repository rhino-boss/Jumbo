window.H016_VERSION_MANIFEST = {
  "current": "6.1.0.0",
  "version_rule": {
    "format": "遊戲參數.卡片權重.SCR.其他文件",
    "retention": "只有第 1、2 碼不同的數學版本分開保留；第 1、2 碼相同時只保留第 3、4 碼最新版本。"
  },
  "versions": [
    {
      "version": "3.0.0.0",
      "math_key": "3.0",
      "date": "2026-08-17",
      "configs": {
        "base": "Versions/3.0/config.js",
        "92": "Versions/3.0/config_92A.js",
        "94": "Versions/3.0/config_94A.js"
      },
      "changes": [
        "H0161 基底版號改為單碼 3；RTP/Variant 版號同步為 3.0.0.0。",
        "新增 SF_Symbol、SF_Symbol (2)、SF_Symbol (3) 與 SF 初始／Retrigger 選表參數。",
        "Super Feature 依 JHS101003 使用獨立 SF 表，並套用 Super Buy 金框位置排除規則。",
        "Console 與 Overview 依 slot_development_specification.md §3.3 固定順序輸出。",
        "Card Retry Limit 正式統一為 10,000。",
        "92A Super Feature 依 Super Ace SF 線型重配：RTP 92.5%、最低 50x、Hit Rate 隨倍率單調不增、贏錢率 30%、500x 以上 Hit Rate 6%、100x 以下 Hit Rate 不超過 50%，且單區間 RTP 不超過 15%。"
      ]
    },
    {
      "version": "4.0.0.0",
      "math_key": "4.0",
      "date": "2026-08-18",
      "working": false,
      "configs": {
        "base": "Versions/4.0/config.js",
        "92": "Versions/4.0/config_92A.js",
        "94": "Versions/4.0/config_94A.js"
      },
      "changes": [
        "直接使用專案根目錄尚未封版的 H016 4.0 自然數學。",
        "BG／FG 堆疊輪帶已校準為不高於 Super Ace，並同步最新大鬼、金框與 FG 選表設定。",
        "92A／94A 僅同步 v4 自然數學；Card System 倍率區間與權重暫時沿用 3.0 舊版。",
        "v4 已封存至 Versions/4.0，含三份 Config、三份 Source Excel、倍率權重 JSON 與競品比較報告。"
      ]
    },
    {
      "version": "5.0.0.0",
      "math_key": "5.0",
      "date": "2026-08-19",
      "working": false,
      "configs": {
        "base": "Versions/5.0/config.js",
        "92": "Versions/5.0/config_92A.js",
        "94": "Versions/5.0/config_94A.js"
      },
      "changes": [
        "v5 工作版使用專案根目錄 Config；v4 已固定封存在 Versions/4.0。",
        "FG 初始與 Retrigger Table 比例改為 fg_1:fg_2:fg_3 = 0:6500:3500。",
        "僅調整 fg_2／fg_3 停輪權重，輪帶、掉落權重、BG 與 SF 參數不變。",
        "fg_3 啟用與 fg_2 相同的 Random Wild 0/2/3/4 權重 23656:1401:235:18。",
        "92A／94A 倍率區間及倍率權重完整沿用 v4，只同步版本為 5.0.0.0。"
      ]
    },
    {
      "version": "6.0.0.0",
      "math_key": "6.0",
      "date": "2026-08-19",
      "working": false,
      "configs": {
        "base": "Versions/6.0/config.js",
        "92": "Versions/6.0/config_92A.js",
        "94": "Versions/6.0/config_94A.js"
      },
      "changes": [
        "只調整 FG_Symbol (2)／FG_Symbol (3) 初始停輪權重及 FG 初始／Retrigger 選表權重；輪帶、掉落、大鬼、金框、BG、BF、SF 與卡片倍率權重不變。",
        "fg_2／fg_3 的堆疊可見停輪相對權重提高 6 倍；選表維持 fg_1:fg_2:fg_3 = 0:6500:3500。",
        "FG 綜合堆疊事件率由 4.2103% 提升至 20.8561%，為 Super Ace 46.7281% 的 44.63%。",
        "Card-On 500,000 場確認每 Free Spin Hit Rate 38.4992%，Retry Limit Exceeded 為 0。"
      ]
    },
    {
      "version": "6.1.0.0",
      "math_key": "6.1",
      "date": "2026-08-19",
      "working": true,
      "configs": {
        "base": "config.js",
        "92": "config_92A.js",
        "94": "config_94A.js"
      },
      "changes": [
        "自然數學完整沿用 v6.0；只重新計算 Card System 的 BG、FG 與 BF 倍率區間權重。",
        "92／94、新手／老手 Normal 均設定為 BG 65%、FG 27%、Total 92%；Normal FG 進場週期設定為 130 場。",
        "BF RTP 設定為 92.5%；SF 的 Excel 區塊與 Config 卡片陣列完整沿用 v6.0，不參與本次調整。",
        "倍率權重使用 v6 Card-Off 1 億場 Normal 與 1 千萬場 BF 報表重算，並保留自然機率 0.1% 門檻與競品相對 Hit Rate 線型。",
        "Card-On 1,000,000 場驗證 Normal RTP 約 91.90%、FG 週期約 129～130 場，Retry Limit Exceeded 為 0。"
      ]
    }
  ]
};
