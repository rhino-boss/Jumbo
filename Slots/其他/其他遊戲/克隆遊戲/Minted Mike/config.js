// Minted Mike（Hacksaw Gaming）克隆 Demo Config
// 依 Demogame規範 4.1：遊戲名稱、盤面、權重、Paytable、Bet Mode 與 Feature 參數一律由此取得。
// ⚠️ 克隆示意：pay_table、線表、機制數值清單、模式價格取自原廠規則；所有權重與機率為 demo 假值，RTP 未校準。
const data = {
  game_id: "MM-CLONE",
  display_name: "Minted Mike",
  game_name_zh: "Minted Mike",
  game_type: "Video Slot - 26 Lines / Sticker Features / Respin / Upgradable Free Spins",
  excel_version: "0.1.0.0",
  config_code: "Demo",
  rtp_label: "Demo",
  profile: "Natural",

  cols: 5,
  rows: 4,

  // 0~7 一般符號，8 起為特殊符號：C4 FS、C5 FS Upgrade、WW Wild、C2 粉貼紙、C1 藍貼紙、C3 綠貼紙
  symbol_codes: ["M1", "M2", "M3", "M4", "A", "K", "Q", "J", "C4", "C5", "WW", "C2", "C1", "C3"],
  symbol_names_zh: ["錢字", "球鞋", "貼紙包", "飲料罐", "A", "K", "Q", "J", "FS", "升級", "Wild", "粉貼紙", "藍貼紙", "綠貼紙"],
  symbol_names_en: ["Cash", "Sneaker", "Sticker Pack", "Can", "A", "K", "Q", "J", "FS", "Upgrade", "Wild", "Pink", "Blue", "Green"],
  normal_count: 8,
  fs_index: 8,
  upgrade_index: 9,
  wild_index: 10,
  sticker_index: { pink: 11, blue: 12, green: 13 },

  // 賠率（× bet）：欄位 = 3／4／5 連；C3 Wild 只有 5 連
  pay_table: [
    [1.5, 5, 20],
    [1, 3, 10],
    [0.8, 2, 7],
    [0.5, 1.5, 5],
    [0.2, 0.5, 1],
    [0.2, 0.5, 1],
    [0.2, 0.5, 1],
    [0.2, 0.5, 1]
  ],
  wild_pay_5: 50,

  // 26 條線（各輪 Row 索引，0＝最上列）
  lines: [
    [0, 0, 0, 0, 0], [1, 1, 1, 1, 1], [2, 2, 2, 2, 2], [3, 3, 3, 3, 3],
    [0, 1, 0, 1, 0], [1, 2, 1, 2, 1], [2, 3, 2, 3, 2], [1, 0, 1, 0, 1],
    [2, 1, 2, 1, 2], [3, 2, 3, 2, 3], [0, 1, 2, 1, 0], [1, 2, 3, 2, 1],
    [3, 2, 1, 2, 3], [2, 1, 0, 1, 2], [0, 1, 1, 1, 0], [1, 2, 2, 2, 1],
    [2, 3, 3, 3, 2], [3, 2, 2, 2, 3], [2, 1, 1, 1, 2], [1, 0, 0, 0, 1],
    [0, 0, 1, 0, 0], [1, 1, 2, 1, 1], [2, 2, 3, 2, 2], [3, 3, 2, 3, 3],
    [2, 2, 1, 2, 2], [1, 1, 0, 1, 1]
  ],

  // 逐格加權抽取（無 reel stop）⏳ demo 假值
  symbol_weights: [4, 6, 8, 10, 18, 18, 18, 18],

  // Sticker：每局每色最多 1 個；land＝出現機率，activate＝出現後啟動機率 ⏳ demo 假值
  stickers: {
    base:   { land: { pink: 0.05, blue: 0.05, green: 0.03 }, activate: { pink: 0.30, blue: 0.35, green: 0.25 } },
    fg:     { land: { pink: 0.18, blue: 0.18, green: 0.12 }, activate: { pink: 0.30, blue: 0.55, green: 0.15 } },             // STEEZY SKATER
    fg_progressive: { land: { pink: 0.40, blue: 0.30, green: 0.12 }, activate: { pink: 0.75, blue: 0.55, green: 0.25 } }, // INK THE CITY／TAG AND DASH
    bonushunt_green_land_mult: 5,     // BonusHunt：綠貼紙出現率 ×5（FG 觸發約 5 倍）
    guaranteed_color_weights: { pink: 40, blue: 40, green: 20 }   // TAG AND DASH 保證 1 個 Sticker 的顏色權重 ⏳
  },

  // Pink Marker／Hot Lines
  hot_lines: {
    // 本作設計：粉色每次只挑 5 條（原廠為 2/3/4/5/6/7/10/12/15/20/26 條）
    count_values:  [5],
    count_weights: [1],
    mult_values:  [2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 50, 100, 150, 183],
    mult_weights: [28, 20, 14, 10, 7, 5, 4, 3, 3, 2, 1.5, 1, 0.5, 0.2, 0.1, 0.05],
    progressive_add_min: 5,            // INK THE CITY 第 2 次起每次也新增 5 條（原廠 1~24 條），滿 26 條後只加乘數
    progressive_add_max: 5,
    max_lines: 26
  },

  // Blue Spray Can：加入 Wild 數
  wild_spray: {
    count_values:  [3, 4, 5, 6, 7, 8, 9, 10, 15, 20],
    count_weights: [30, 22, 16, 11, 8, 5, 3, 2, 1, 0.5]
  },

  // Green Sticker Roll：觸發率與 C1＋C2 總數（8~20）、C2 個數 ⏳ demo 假值
  green_roll: {
    bg_award_chance: 0.7,              // 啟動後達觸發門檻的機率；其餘只落 3~7 顆 FS（未觸發）
    total_values:  [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    total_weights: [30, 20, 14, 10, 7, 5, 4, 3, 2, 2, 1, 1, 1],
    upgrade_weights: [80, 17, 3]       // C2 = 0／1／2 個
  },

  // Spray the System FeatureSpins：每局保證粉＋藍 Sticker，啟動率與熱線權重較強（讓 60x 花費合理）⏳ demo 假值
  spray_mode: {
    activate: { pink: 1, blue: 0.85 },
    hot_count_weights: [1],
    hot_mult_weights: [2, 3, 4, 5, 6, 7, 8, 8, 9, 10, 10, 9, 8, 5, 2.5, 1.2]
  },

  fg_names: { skater: "STEEZY SKATER", ink: "INK THE CITY", tag: "TAG AND DASH" },
  fg_safety_cap: 200,                  // 程式保護用；原廠規則未寫局數上限 ⏳
  max_win: 5000,

  supported_bet_modes: ["normal_bet", "bonushunt", "spray_the_system", "buy_steezy_skater", "buy_ink_the_city"],
  feature_spins: { bonushunt: 3, spray: 60 },           // 每局花費（× bet），持續啟用直到關閉
  featurebuy: { skater: 50, ink: 200 },                 // 一次購買（× bet）
  official_rtp: { normal: 96.31, bonushunt: 96.25, spray: 96.32, skater: 96.34, ink: 96.33 },

  bet_options: [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100],
  initial_balance: 100000
};
