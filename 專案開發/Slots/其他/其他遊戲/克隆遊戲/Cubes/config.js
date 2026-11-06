// Cubes（Hacksaw Gaming）克隆 Demo Config
// 依 Demogame規範 4.1：遊戲名稱、盤面、權重、Paytable 與 Feature 參數一律由此取得。
// ⚠️ 克隆示意：pay_table、盤面尺寸、乘數上限、FG／Color Blast 數值取自原廠規則；顏色權重為 demo 假值，RTP 未校準。
const data = {
  game_id: "CUBES-CLONE",
  display_name: "Cubes",
  game_name_zh: "Cubes",
  game_type: "Video Slot - Cluster Pay / Expanding Grid / Middle Multiplier / Sticky Free Spins",
  excel_version: "0.1.0.0",
  config_code: "Demo",
  rtp_label: "Demo",
  profile: "Natural",

  max_size: 11,                         // 座標框 11×11
  sizes: [5, 7, 9, 11],                 // 起始 5×5，每次擴展一圈
  min_cluster: 5,                       // 上下左右相連 ≥5

  symbol_codes: ["M1", "M2", "M3", "M4", "M5", "M6"],   // 綠、黃、紅、淺藍、紫、藍（賠率相同）
  symbol_colors: ["#8eff64", "#f2ff55", "#e90056", "#b5fffd", "#9f00da", "#4b7bf4"],   // 取自原廠賠率表色塊

  // 賠率（× bet）：依 Cluster 顆數區間；M1～M6 共用
  pay_table: [
    { min: 5, max: 5, pay: 0.1 },
    { min: 6, max: 6, pay: 0.2 },
    { min: 7, max: 7, pay: 0.3 },
    { min: 8, max: 8, pay: 1.5 },
    { min: 9, max: 9, pay: 3 },
    { min: 10, max: 11, pay: 4 },
    { min: 12, max: 14, pay: 9 },
    { min: 15, max: 19, pay: 24 },
    { min: 20, max: 24, pay: 32 },
    { min: 25, max: 9999, pay: 40 }
  ],

  // 逐格加權抽取（無 reel stop）⏳ demo 假值
  // 模擬（3×10⁵ 局，含中央乘數）：RTP 約 100%、中獎率 19%、FG 約 1/3,300
  symbol_weights_bg: [1.2, 1.12, 1, 0.98, 0.88, 0.82],
  symbol_weights_fg: [1.2, 1.12, 1, 0.98, 0.88, 0.82],

  middle_multiplier: { max: 22 },       // BG 中央格所在同色區塊顆數＝乘數，上限 22（只 BG）

  fg_trigger_colors: 5,                 // 最終盤面 5 種不同顏色的 Cluster 觸發 FG
  fg_spins: 10,                         // 原廠「最多 10 局」⏳ 暫定固定 10 局
  color_blast: { cluster: 70, award: 2500 },   // FG 中 Cluster ≥70 → 2500x（每段 FG 一次）⏳
  max_win: 3000,

  supported_bet_modes: ["normal_bet"],
  bet_options: [0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 150],
  initial_balance: 100000
};
