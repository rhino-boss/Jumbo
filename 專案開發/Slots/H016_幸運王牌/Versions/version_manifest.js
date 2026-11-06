window.H016_VERSION_MANIFEST = {
  "current": "8.0.0.0",
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
        "92": "Versions/3.0/config_92A.js",
        "94": "Versions/3.0/config_94A.js",
        "base": "Versions/3.0/config.js"
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
        "92": "Versions/4.0/config_92A.js",
        "94": "Versions/4.0/config_94A.js",
        "base": "Versions/4.0/config.js"
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
        "92": "Versions/5.0/config_92A.js",
        "94": "Versions/5.0/config_94A.js",
        "base": "Versions/5.0/config.js"
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
      "version": "6.4.0.1",
      "math_key": "6.4",
      "date": "2026-08-19",
      "working": false,
      "configs": {
        "92": "Versions/6.4/config_92A.js",
        "94": "Versions/6.4/config_94A.js",
        "base": "Versions/6.4/config.js"
      },
      "changes": [
        "將 H016 連消倍數英文統一為 Cascade Multiplier；同步 Game Rule、Index Help 與共用玩法規範。",
        "自然輪帶、老手 BG／FG、BF 與 SF 數學完整沿用 v6.3；只修正新手 Normal Bet 倍率權重。",
        "92A／94A 新手期統一為 BG 65%＋FG 28%＝Total 93%；FG 週期維持 130 場。",
        "新手 BG Cap 維持 30x，新手 FG Cap 維持 120x；自然機率與競品相對 Hit Rate 規則不變。",
        "v6.3 已封存至 Versions/6.3，根目錄 Config 與 Index 切換至 v6.4.0.0。",
        "v6.4 已封存至 Versions/6.4，供 Index 切換與追溯。"
      ]
    },
    {
      "version": "8.0.0.0",
      "math_key": "8.0",
      "date": "2026-08-19",
      "working": false,
      "configs": {
        "92": "Versions/8.0/config_92A.js",
        "94": "Versions/8.0/config_94A.js",
        "base": "Versions/8.0/config.js"
      },
      "changes": [
        "SF_Symbol (3) 的 Random Wild 0/2/3/4 權重調整為 0:1000:0:0，每次事件只抽 2 個 WW。",
        "SF 初始與 Retrigger 選表權重同步調整為 sf_1:sf_2:sf_3 = 0:5500:4500。",
        "SF 卡片倍率權重依 v8 的 100 萬場自然報表與 Super Ace SF 倍率線型重算，92／94 共用同一組權重。",
        "SF 最小有權重區間改為 (100, 120]，自然機率需大於 0.07%，目標 RTP 固定 92.5%。",
        "(350, 400] 與 (450, 500] 依競品平滑參考機率額外乘 1.5 倍，其餘區間維持競品遞減線型。",
        "OP Jackpot SCR 依 v8 Card-On 報表補齊 NB 新手、NB 老手、BF、SF，並將六份來源報表收入 Versions/8.0/Record。",
        "依版本規範將 H0161 升為 8，H016192A／H016194A 同步為 8.0.0.0。",
        "v8 已封存至 Versions/8.0，含三份 Config、三份 Source Excel、倍率求解與驗證資料，供 Index 切換與追溯。"
      ]
    }
  ]
};
