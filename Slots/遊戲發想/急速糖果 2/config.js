// 急速糖果 2（Candy Rush 2）發想草稿 Config
// 依 Demogame規範 4.1：遊戲名稱、盤面、權重、Paytable、Bet Mode 與 Feature 參數一律由此取得。
// ⚠️ 發想階段：symbol_weights 與 featurebuy 為假值；pay_table 沿用 H022 linkpoint ÷ 100。
const data = {
  game_id: "TC2-DRAFT",
  display_name: "Candy Rush 2",
  game_name_zh: "急速糖果 2",
  game_type: "Video Slot - Cluster Pay / Cascade / Position Multiplier",
  excel_version: "0.3.1.0",
  config_code: "DRAFT",
  rtp_label: "DRAFT",                   // 共用 Setting 顯示為 DRAFT-Off
  profile: "Off",                       // Card System 未實作
  base_game_source: "H022 糖果轟炸 1000（101008）",

  board_size: 7,                        // 7×7
  min_cluster: 5,                       // 相連 ≥5 成立 Cluster（上下左右）
  refill_mode: "drop",                  // 補牌方式：消除後掉落補牌（規範 4.3 第 2 類）

  symbol_codes: ["M1", "M2", "M3", "M4", "A", "K", "Q", "C1"],
  scatter_index: 7,                     // C1

  // 賠率（× bet）：H022 linkpoint ÷ 100；欄位 = Cluster 5..14、15+
  pay_table: [
    [1, 1.5, 1.75, 2, 2.5, 5, 7.5, 15, 35, 70, 150],
    [0.75, 1, 1.25, 1.5, 2, 4, 6, 12.5, 30, 60, 100],
    [0.5, 0.75, 1, 1.25, 1.5, 3, 4.5, 10, 20, 40, 60],
    [0.4, 0.5, 0.75, 1, 1.25, 2, 3, 5, 10, 20, 40],
    [0.3, 0.4, 0.5, 0.75, 1, 1.5, 2.5, 3.5, 8, 15, 30],
    [0.25, 0.3, 0.4, 0.5, 0.75, 1.25, 2, 3, 6, 12, 25],
    [0.2, 0.25, 0.3, 0.4, 0.5, 1, 1.5, 2.5, 5, 10, 20]
  ],

  // 逐格加權抽取（無 reel stop；Reel RNG 顯示 weighted draw）
  symbol_weights_init: [6, 8, 10, 12, 15, 17, 19],
  symbol_weights_drop: [6, 8, 10, 12, 15, 17, 19],
  scatter_chance_init: 0.055,           // 每輪出 1 顆 C1 的機率（同輪最多 1 顆）
  scatter_chance_drop: 0.0,             // 掉落不補 C1 ⏳

  // 位置倍數（本作主特色）：每次消除 +1（從 1 開始）、計分乘全盤和
  position_multiplier: {
    start_value: 1,
    step: 1,
    score_scope: "board_sum",           // 不論在哪消除，得分一律乘全盤 49 格倍數加總；0 視為 1
    bg_reset: "per_spin",
    fg_reset: "per_session"             // FG 整場保留
  },

  // 同符號連帶消除：中獎 Cluster 成立時，盤面上其餘同符號一併消除；只以 Cluster 本身計分，
  // 連帶消除的格子不計分、位置倍數也不 +1。同段同符號多組 Cluster 時每組各自計分。
  same_symbol_clear: true,

  // FG：最終盤面 C1 數量 → 局數；retrigger 同表
  fg_awards: { "3": 10, "4": 12, "5": 15, "6": 20, "7": 30 },
  fg_cap: 50,                           // ⏳ 上限待確認

  supported_bet_modes: ["normal_bet", "extra_bet", "buy_feature"],
  extrabet: 10,                         // Extra Bet 費用（× bet）；派彩仍以原始押注計算
  // Extra Bet：該次 BG Spin 開場時，隨機 1～3 個位置出現倍數底板（該格起始位置倍數）
  extra_bet_plates: {
    count_values: [1, 2, 3],
    count_weights: [1, 1, 1],           // ⏳ 個數權重
    values: [20, 50, 100, 250, 500, 1000],
    value_weights: [50, 25, 12, 7, 4, 2] // ⏳ 倍數值權重
  },
  featurebuy: 100,                      // ⏳ Buy Feature 價格假值（× bet），直接進 3 顆觸發的 FG
  bet_options: [1, 2, 5, 10, 20, 50, 100],
  initial_balance: 10000
};
