// 宙斯 2500 月會分享 v04：內容同 v03，重新設計視覺（深藍＋金色、閃電圖示圓圈為主視覺）
const pptxgen = require("pptxgenjs");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa6");
const fs = require("fs");
const path = require("path");

const OUT = process.argv[2];
const SHOT = "data:image/png;base64," + fs.readFileSync(path.join(__dirname, "..", "demo_shot.png")).toString("base64");

const NAVY = "101B3D", NAVY2 = "1D2C5E", GOLD = "E8B53A", GOLDL = "FBF1D6", BLUE = "3D8BFF";
const TEXT = "1A2238", MUTED = "6B7790", TINT = "F3F6FB", LINE = "DCE2EE", WHITE = "FFFFFF", GREYOUT = "B8C0D0";
const FONT = "Microsoft JhengHei";

async function icon(name, color, size = 256) {
  const Comp = fa[name];
  if (!Comp) throw new Error("icon missing: " + name);
  const svg = renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";            // 13.333 x 7.5
  pres.title = "ZEUS 2500 月會分享";
  pres.theme = { headFontFace: FONT, bodyFontFace: FONT };
  const W = 13.333, H = 7.5;

  const IC = {};
  for (const [k, n, c] of [
    ["boltG", "FaBolt", GOLD], ["boltN", "FaBolt", NAVY], ["layers", "FaLayerGroup", NAVY], ["gem", "FaGem", NAVY],
    ["gift", "FaGift", NAVY], ["down", "FaArrowsDownToLine", NAVY], ["chart", "FaChartLine", NAVY],
    ["check", "FaCircleCheck", NAVY], ["db", "FaDatabase", NAVY], ["search", "FaMagnifyingGlass", NAVY],
    ["sliders", "FaSliders", NAVY], ["wand", "FaWandMagicSparkles", NAVY], ["trophy", "FaTrophy", NAVY],
    ["horn", "FaBullhorn", NAVY], ["scale", "FaScaleBalanced", NAVY], ["layersG", "FaLayerGroup", GREYOUT],
    ["boltGrey", "FaBolt", GREYOUT], ["giftGrey", "FaGift", GREYOUT], ["arrow", "FaChevronRight", GOLD],
  ]) IC[k] = await icon(n, c);

  // ---- 共用元件
  let pageNo = 0;
  function base(dark = false) {
    const s = pres.addSlide();
    s.background = { color: dark ? NAVY : WHITE };
    pageNo++;
    if (pageNo > 1) {
      s.addText("ZEUS 2500 · 月會分享", { x: 0.6, y: H - 0.5, w: 4, h: 0.3, fontSize: 10, color: dark ? "8E9AC0" : MUTED, margin: 0, isTextBox: true });
      s.addText(String(pageNo), { x: W - 1.1, y: H - 0.5, w: 0.5, h: 0.3, fontSize: 10, color: dark ? "8E9AC0" : MUTED, align: "right", margin: 0, isTextBox: true });
    }
    return s;
  }
  function title(s, t, kicker) {
    if (kicker) s.addText(kicker, { x: 0.6, y: 0.35, w: 8, h: 0.3, fontSize: 12, bold: true, color: GOLD, charSpacing: 3, margin: 0, isTextBox: true });
    s.addText(t, { x: 0.6, y: 0.62, w: 12, h: 0.8, fontSize: 34, bold: true, color: TEXT, margin: 0, isTextBox: true });
  }
  function circle(s, x, y, d, img, fill = GOLDL) {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill } });
    const pad = d * 0.26;
    s.addImage({ data: img, x: x + pad, y: y + pad, w: d - 2 * pad, h: d - 2 * pad });
  }
  function card(s, x, y, w, h, fill = TINT) {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill }, line: { color: fill },
      shadow: { type: "outer", color: "000000", opacity: 0.08, blur: 8, offset: 2, angle: 90 } });
  }
  function shot(s, x, y, w) {
    const h = w * 672 / 1106;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x - 0.08, y: y - 0.08, w: w + 0.16, h: h + 0.16, rectRadius: 0.14, fill: { color: GOLD }, line: { color: GOLD } });
    s.addImage({ data: SHOT, x, y, w, h });
  }
  function note(s, t, y) {
    s.addText(t, { x: 0.6, y, w: 12.1, h: 0.3, fontSize: 11, color: MUTED, margin: 0, isTextBox: true });
  }
  function table(s, x, y, w, rows, colW, hlCol) {
    const data = rows.map((r, ri) => r.map((v, ci) => ({
      text: v,
      options: {
        bold: ri === 0 || ci === hlCol,
        color: ri === 0 ? WHITE : (ci === hlCol ? NAVY : TEXT),
        fill: { color: ri === 0 ? (ci === hlCol ? "B8892A" : NAVY) : (ci === hlCol ? GOLDL : (ri % 2 ? WHITE : TINT)) },
        align: ci === 0 ? "left" : "center", valign: "middle", fontSize: ri === 0 ? 13 : 14,
      },
    })));
    s.addTable(data, { x, y, w, colW, rowH: 0.5, border: { type: "solid", pt: 0.75, color: LINE }, margin: [0, 0.12, 0, 0.12] });
  }
  function section(no, t, sub) {
    const s = base(true);
    circle(s, 0.9, 2.55, 1.5, IC.boltN, GOLD);
    s.addText(no, { x: 2.8, y: 2.35, w: 3, h: 0.9, fontSize: 54, bold: true, color: GOLD, margin: 0, isTextBox: true });
    s.addText(t, { x: 2.8, y: 3.2, w: 9.5, h: 0.9, fontSize: 40, bold: true, color: WHITE, margin: 0, isTextBox: true });
    if (sub) s.addText(sub, { x: 2.8, y: 4.1, w: 9.5, h: 0.5, fontSize: 16, color: "AEB8D8", margin: 0, isTextBox: true });
  }
  function iconRow(s, x, y, w, img, head, desc, active = true, d = 0.75) {
    circle(s, x, y, d, img, active ? GOLDL : "EEF0F5");
    s.addText(head, { x: x + d + 0.3, y: y - 0.02, w, h: 0.42, fontSize: 20, bold: true, color: active ? TEXT : GREYOUT, margin: 0, isTextBox: true });
    s.addText(desc, { x: x + d + 0.3, y: y + 0.42, w, h: 0.36, fontSize: 15, color: active ? MUTED : GREYOUT, margin: 0, isTextBox: true });
  }
  function bigStat(s, x, y, w, h, num, label, sub, dark = false) {
    card(s, x, y, w, h, dark ? NAVY : TINT);
    s.addText(num, { x: x + 0.35, y: y + 0.3, w: w - 0.7, h: 0.95, fontSize: 40, bold: true, color: dark ? GOLD : NAVY, margin: 0, isTextBox: true });
    s.addText(label, { x: x + 0.35, y: y + 1.25, w: w - 0.7, h: 0.4, fontSize: 16, bold: true, color: dark ? WHITE : TEXT, margin: 0, isTextBox: true });
    if (sub) s.addText(sub, { x: x + 0.35, y: y + 1.7, w: w - 0.7, h: h - 1.9, fontSize: 14, color: dark ? "AEB8D8" : MUTED, margin: 0, valign: "top", isTextBox: true });
  }

  // ---- 1 封面
  {
    const s = base(true);
    s.addText("月會分享", { x: 0.8, y: 1.9, w: 6, h: 0.4, fontSize: 16, bold: true, color: GOLD, charSpacing: 4, margin: 0, isTextBox: true });
    s.addText("ZEUS 2500", { x: 0.8, y: 2.35, w: 6.4, h: 1.2, fontSize: 60, bold: true, color: WHITE, margin: 0, isTextBox: true });
    s.addText("宙斯 2500", { x: 0.8, y: 3.5, w: 6.4, h: 0.8, fontSize: 32, bold: true, color: GOLD, margin: 0, isTextBox: true });
    s.addText("大倍數 ＋ 大基底 ＝ 超大倍數", { x: 0.8, y: 4.45, w: 6.4, h: 0.5, fontSize: 18, color: "AEB8D8", margin: 0, isTextBox: true });
    s.addText("101027 · 數學 7.4.0.0 · JumboRD", { x: 0.8, y: 6.6, w: 6, h: 0.3, fontSize: 12, color: "8E9AC0", margin: 0, isTextBox: true });
    shot(s, 7.3, 1.9, 5.3);
  }


  const IC2 = { arrowM: await icon("FaArrowRight", GREYOUT), up: await icon("FaArrowTrendUp", NAVY), users: await icon("FaUserGroup", NAVY),
                cal: await icon("FaCalendarDay", NAVY), ban: await icon("FaEyeSlash", NAVY), crown: await icon("FaCrown", NAVY) };
  const chip = (s, x, y, w, t, dark) => s.addText(t, { x, y, w, h: 0.38, fontSize: 13, bold: true, align: "center", valign: "middle", margin: 0,
    color: dark ? NAVY : MUTED, fill: { color: dark ? GOLD : "E3E8F2" }, rectRadius: 0.19, shape: pres.shapes.ROUNDED_RECTANGLE, isTextBox: true });

  // ---- 2 目錄
  {
    const s = base();
    title(s, "目錄", "OUTLINE");
    const items = [["01", "遊戲設計", "核心玩法、設計重點、跟競品差異、輪帶設計"], ["02", "跟競品不同的地方", "5000x 大獎、2500x 球、AB Test"], ["03", "AI", "從側錄到調性的 AI 流程"]];
    items.forEach(([n, t, d], i) => {
      const y = 1.75 + i * 1.6;
      card(s, 0.6, y, 12.1, 1.35);
      s.addText(n, { x: 1.0, y, w: 1.4, h: 1.35, fontSize: 44, bold: true, color: GOLD, valign: "middle", margin: 0, isTextBox: true });
      s.addText(t, { x: 2.5, y: y + 0.28, w: 9.8, h: 0.45, fontSize: 22, bold: true, color: TEXT, margin: 0, isTextBox: true });
      s.addText(d, { x: 2.5, y: y + 0.78, w: 9.8, h: 0.35, fontSize: 14, color: MUTED, margin: 0, isTextBox: true });
    });
  }

  // ---- 核心玩法（只留完整版）
  {
    const s = base();
    title(s, "遊戲核心玩法", "CORE GAMEPLAY");
    [["layers", "連消", "全盤 8 個以上就中，消除後掉落"], ["boltN", "倍數球", "最高 2500x，C3 每次消除升一級"], ["gift", "免費遊戲", "倍數跨場累積"]]
      .forEach(([ic, h, d], i) => iconRow(s, 0.6, 1.85 + i * 1.25, 5.0, IC[ic], h, d, true));
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.6, w: 6.1, h: 0.85, rectRadius: 0.42, fill: { color: NAVY }, line: { color: NAVY } });
    s.addText("大倍數 ＋ 大基底 ＝ 超大倍數", { x: 0.6, y: 5.6, w: 6.1, h: 0.85, fontSize: 22, bold: true, color: GOLD, align: "center", valign: "middle", margin: 0, isTextBox: true });
    shot(s, 7.3, 1.85, 5.4);
  }
  {
    const s = base();
    title(s, "設計重點", "DESIGN POINTS");
    const pts = [["gem", "倍數球夠吸引人", "最高 2500x，C3 越消越大"], ["chart", "出球後還能消除", "有球時 Hit Rate 較高"], ["down", "越消越期待掉球", "每輪一顆倍數球，消久必出球"]];
    pts.forEach(([ic, h, d], i) => {
      const x = 0.6 + i * 4.1;
      card(s, x, 1.9, 3.8, 3.1);
      circle(s, x + 0.4, 2.3, 1.0, IC[ic]);
      s.addText(String(i + 1).padStart(2, "0"), { x: x + 2.6, y: 2.35, w: 0.9, h: 0.6, fontSize: 28, bold: true, color: GOLD, align: "right", margin: 0, isTextBox: true });
      s.addText(h, { x: x + 0.4, y: 3.65, w: 3.0, h: 0.5, fontSize: 22, bold: true, color: TEXT, margin: 0, isTextBox: true });
      s.addText(d, { x: x + 0.4, y: 4.25, w: 3.0, h: 1.0, fontSize: 16, color: MUTED, margin: 0, valign: "top", isTextBox: true });
    });
  }

  // 跟競品差異：左條列、右表

  // ---- 跟競品差異：全寬對照列（競品 → 宙斯＋標籤）
  {
    const s = base();
    title(s, "跟競品差異", "VS. GATES OF OLYMPUS 1000");
    const X0 = 0.6, CW = 12.1;
    chip(s, 4.55, 1.55, 2.6, "Gates of Olympus 1000", false);
    chip(s, 8.0, 1.55, 2.6, "宙斯 2500", true);
    const rows = [
      ["boltN", "倍數球上限", "1000x", "2500x", "更大", true],
      ["chart", "BG 倍數球週期", "26.9 轉", "8.4 轉", "更多", true],
      ["check", "有球 Hit Rate（無球 → 有球）", "28.13% → 45.34%", "27.28% → 44.56%", "延續", false],
      ["down", "每輪倍數球", "1 顆", "1 顆", "延續", false],
      ["gift", "Extra Bet FG 週期", "沒有", "90.2 轉", "新增", true],
    ];
    rows.forEach(([ic, label, a, b, tag, hot], i) => {
      const y = 2.1 + i * 0.84;
      card(s, X0, y, CW, 0.72, i % 2 ? WHITE : TINT);
      circle(s, X0 + 0.2, y + 0.11, 0.5, IC[ic]);
      s.addText(label, { x: X0 + 0.85, y, w: 3.0, h: 0.72, fontSize: 15, bold: true, color: TEXT, valign: "middle", margin: 0, isTextBox: true });
      s.addText(a, { x: 4.35, y, w: 3.0, h: 0.72, fontSize: 18, color: MUTED, align: "center", valign: "middle", margin: 0, isTextBox: true });
      s.addImage({ data: IC2.arrowM, x: 7.45, y: y + 0.24, w: 0.24, h: 0.24 });
      s.addText(b, { x: 7.8, y, w: 3.0, h: 0.72, fontSize: 20, bold: true, color: NAVY, align: "center", valign: "middle", margin: 0, isTextBox: true });
      chip(s, 11.35, y + 0.17, 1.1, tag, hot);
    });
    note(s, "※ 宙斯 B 版 Card-On 7.4.0.0（Extra Bet 2 倍押注，一般押注 FG 週期 450.3 轉）；Hit Rate 取自然機率；競品為 3.1 萬局側錄", 6.45);
  }

  // ---- 輪帶設計：左右對照＋示意輪帶
  {
    const s = base();
    title(s, "輪帶設計：每輪一顆倍數球", "REEL DESIGN");
    // 每個陣列＝6 輪各自的倍數球列位置（0～6）
    const layouts = [
      { x: 0.6, dark: true, big: "每輪 1 顆", who: "競品（宙斯採用）", desc: "消得夠久，一定會有倍數球\n出球時仍有較高的連消率", balls: [[2], [5], [1], [4], [0], [3]] },
      { x: 6.8, dark: false, big: "每輪多顆", who: "埃及秘寶", desc: "卡片系統下，出現倍數球後基本上就停止消除", balls: [[0, 2, 5], [1, 3, 6], [0, 4], [2, 3, 5], [1, 4, 6], [0, 3, 5]] },
    ];
    for (const L of layouts) {
      const y = 1.75, h = 4.05;
      card(s, L.x, y, 5.9, h, L.dark ? NAVY : TINT);
      s.addText(L.big, { x: L.x + 0.35, y: y + 0.3, w: 2.9, h: 0.8, fontSize: 32, bold: true, color: L.dark ? GOLD : NAVY, margin: 0, isTextBox: true });
      s.addText(L.who, { x: L.x + 0.35, y: y + 1.15, w: 2.6, h: 0.4, fontSize: 16, bold: true, color: L.dark ? WHITE : TEXT, margin: 0, isTextBox: true });
      s.addText(L.desc, { x: L.x + 0.35, y: y + 1.65, w: 2.5, h: 1.6, fontSize: 14, color: L.dark ? "AEB8D8" : MUTED, margin: 0, valign: "top", isTextBox: true });
      // 示意輪帶：6 輪 × 7 格
      const gx = L.x + 3.15, gy = y + 0.35, cw = 0.36, ch = 0.45, gap = 0.06;
      L.balls.forEach((rowsWithBall, r) => {
        const cx = gx + r * (cw + gap);
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx - 0.03, y: gy - 0.05, w: cw + 0.06, h: 7 * ch + 0.1, rectRadius: 0.06,
          fill: { color: L.dark ? NAVY2 : "E3E8F2" }, line: { color: L.dark ? NAVY2 : "E3E8F2" } });
        for (let k = 0; k < 7; k++) {
          const ball = rowsWithBall.includes(k);
          const d = ball ? 0.3 : 0.14;
          s.addShape(pres.shapes.OVAL, { x: cx + (cw - d) / 2, y: gy + k * ch + (ch - d) / 2, w: d, h: d,
            fill: { color: ball ? GOLD : (L.dark ? "3A4A80" : "C9D1E0") }, line: { color: ball ? GOLD : (L.dark ? "3A4A80" : "C9D1E0") } });
        }
      });
      s.addText("示意：金球＝倍數球", { x: gx, y: gy + 7 * ch + 0.12, w: 2.5, h: 0.3, fontSize: 10, color: L.dark ? "8E9AC0" : MUTED, margin: 0, isTextBox: true });
    }
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 6.05, w: 12.1, h: 0.7, rectRadius: 0.35, fill: { color: GOLDL }, line: { color: GOLDL } });
    s.addImage({ data: IC.boltN, x: 0.95, y: 6.21, w: 0.38, h: 0.38 });
    s.addText("宙斯採用競品做法：出球後仍能連消", { x: 1.55, y: 6.05, w: 10.8, h: 0.7, fontSize: 20, bold: true, color: NAVY, valign: "middle", margin: 0, isTextBox: true });
  }

  // ---- 其他調整：大數字＋佐證列／長條
  {
    const s = base();
    title(s, "其他調整", "ADJUSTMENTS");
    // 左：5000x
    let x = 0.6, y = 1.75, h = 4.7;
    card(s, x, y, 5.9, h, NAVY);
    s.addText("1/892,857", { x: x + 0.4, y: y + 0.3, w: 5.1, h: 0.9, fontSize: 40, bold: true, color: GOLD, margin: 0, isTextBox: true });
    s.addText("≥5000x 週期（局）：5000x 大獎更常出現", { x: x + 0.4, y: y + 1.2, w: 5.1, h: 0.4, fontSize: 16, bold: true, color: WHITE, margin: 0, isTextBox: true });
    [["users", "客戶反應高倍數太少", "2026-10-22"], ["cal", "換算每天約 2～34 次", "皮娜塔線上轉數 2026-10-22"], ["ban", "競品樣本未出現", "3.1 萬局側錄"]].forEach(([ic, t, d], i) => {
      const ry = y + 1.9 + i * 0.88;
      circle(s, x + 0.4, ry, 0.6, IC2[ic], GOLD);
      s.addText(t, { x: x + 1.2, y: ry - 0.02, w: 4.3, h: 0.36, fontSize: 16, bold: true, color: WHITE, margin: 0, isTextBox: true });
      s.addText(d, { x: x + 1.2, y: ry + 0.33, w: 4.3, h: 0.3, fontSize: 12, color: "AEB8D8", margin: 0, isTextBox: true });
    });
    // 右：2500x 球
    x = 6.8;
    card(s, x, y, 5.9, h, TINT);
    s.addText("1/1,955", { x: x + 0.4, y: y + 0.3, w: 5.1, h: 0.9, fontSize: 40, bold: true, color: NAVY, margin: 0, isTextBox: true });
    s.addText("BG 2500x 球（轉）：2500x 球拿得到", { x: x + 0.4, y: y + 1.2, w: 5.1, h: 0.4, fontSize: 16, bold: true, color: TEXT, margin: 0, isTextBox: true });
    const bars = [["倍數球上限", [["競品", 1000, "1000x"], ["宙斯", 2500, "2500x"]], 2500], ["BG 上限", [["A 版", 250, "250x"], ["B 版", 2000, "2000x"]], 2500]];
    bars.forEach(([lab, items, max], gi) => {
      const gy = y + 1.9 + gi * 1.35;
      s.addText(lab, { x: x + 0.4, y: gy, w: 3, h: 0.3, fontSize: 13, bold: true, color: MUTED, margin: 0, isTextBox: true });
      items.forEach(([n, v, t], j) => {
        const by = gy + 0.38 + j * 0.42, bw = 3.6 * v / max, hot = j === 1;
        s.addText(n, { x: x + 0.4, y: by, w: 0.75, h: 0.32, fontSize: 12, color: MUTED, valign: "middle", margin: 0, isTextBox: true });
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 1.2, y: by + 0.04, w: Math.max(bw, 0.12), h: 0.24, rectRadius: 0.12,
          fill: { color: hot ? GOLD : "C9D1E0" }, line: { color: hot ? GOLD : "C9D1E0" } });
        s.addText(t, { x: x + 1.3 + bw, y: by, w: 1.0, h: 0.32, fontSize: 13, bold: hot, color: hot ? NAVY : MUTED, valign: "middle", margin: 0, isTextBox: true });
      });
    });
  }

  // ---- AB Test：指標長條對照
  {
    const s = base();
    title(s, "AB Test：B 版主推", "AB TEST");
    s.addText("只差 BG，FG／BF 相同；上線後觀察新手／老手留存、人均轉數、遊玩時長", { x: 0.6, y: 1.45, w: 12.1, h: 0.35, fontSize: 15, color: MUTED, margin: 0, isTextBox: true });
    // 左：兩版說明
    [["A 版", "貼近競品", false, "BG 倍數球少、上限低，玩起來較平穩"], ["B 版（主推）", "特色更豐富", true, "BG 倍數球多、上限開到 2000x，尾端更深"]].forEach(([n, tag, dark, d], i) => {
      const y = 2.05 + i * 2.25;
      card(s, 0.6, y, 4.0, 2.0, dark ? NAVY : TINT);
      s.addText(n, { x: 0.95, y: y + 0.3, w: 3.3, h: 0.5, fontSize: 24, bold: true, color: dark ? GOLD : TEXT, margin: 0, isTextBox: true });
      chip(s, 0.95, y + 0.9, 1.5, tag, dark);
      s.addText(d, { x: 0.95, y: y + 1.38, w: 3.4, h: 0.5, fontSize: 13, color: dark ? "AEB8D8" : MUTED, margin: 0, isTextBox: true });
    });
    // 右：4 指標，每項 A／B 長條（長度＝頻率或數值相對大小）
    const M = [["BG 倍數球週期", "越短越常看到球", [1 / 13.7, "13.7 轉"], [1 / 8.4, "8.4 轉"]],
               ["BG 上限", "", [250, "250x"], [2000, "2000x"]],
               ["≥1000x 週期", "越短越常出大獎", [1 / 162866, "162,866 局"], [1 / 26364, "26,364 局"]],
               ["標準差", "越大起伏越大", [13.19, "13.19"], [16.18, "16.18"]]];
    card(s, 4.9, 2.05, 7.8, 4.25, WHITE);
    M.forEach(([lab, hint, A, B], i) => {
      const y = 2.3 + i * 1.0, max = Math.max(A[0], B[0]);
      s.addText(lab, { x: 5.2, y, w: 2.0, h: 0.32, fontSize: 15, bold: true, color: TEXT, margin: 0, isTextBox: true });
      if (hint) s.addText(hint, { x: 5.2, y: y + 0.36, w: 2.0, h: 0.28, fontSize: 11, color: MUTED, margin: 0, isTextBox: true });
      [["A", A, false], ["B", B, true]].forEach(([n, [v, t], hot], j) => {
        const by = y + j * 0.4, bw = 3.4 * v / max;
        s.addText(n, { x: 7.35, y: by, w: 0.3, h: 0.32, fontSize: 12, bold: true, color: hot ? NAVY : MUTED, valign: "middle", margin: 0, isTextBox: true });
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.7, y: by + 0.05, w: Math.max(bw, 0.12), h: 0.22, rectRadius: 0.11,
          fill: { color: hot ? GOLD : "C9D1E0" }, line: { color: hot ? GOLD : "C9D1E0" } });
        s.addText(t, { x: 7.8 + bw, y: by, w: 1.4, h: 0.32, fontSize: 13, bold: hot, color: hot ? NAVY : MUTED, valign: "middle", margin: 0, isTextBox: true });
      });
    });
  }
  // ---- 04 AI：流程
  {
    const s = base();
    title(s, "AI", "03 · AI WORKFLOW");
    const steps = [["db", "收集資料", "競品實機側錄 3.1 萬局"], ["search", "AI 分析／破解輪帶", "還原競品輪帶與停點權重"],
                   ["sliders", "AI 還原調性", "卡片權重對齊競品倍率線型"], ["wand", "AI 玩法優化", "B 版新調性：BG 倍數球與大獎更多"]];
    steps.forEach(([ic, h, d], i) => {
      const x = 0.6 + i * 3.1;
      card(s, x, 2.0, 2.75, 3.2);
      circle(s, x + 0.35, 2.35, 0.95, IC[ic]);
      s.addText(String(i + 1).padStart(2, "0"), { x: x + 1.7, y: 2.4, w: 0.8, h: 0.5, fontSize: 24, bold: true, color: GOLD, align: "right", margin: 0, isTextBox: true });
      s.addText(h, { x: x + 0.35, y: 3.55, w: 2.2, h: 0.85, fontSize: 18, bold: true, color: TEXT, margin: 0, valign: "top", isTextBox: true });
      s.addText(d, { x: x + 0.3, y: 4.45, w: 2.4, h: 0.6, fontSize: 14, color: MUTED, margin: 0, valign: "top", isTextBox: true });
      if (i < 3) s.addImage({ data: IC.arrow, x: x + 2.82, y: 3.75, w: 0.24, h: 0.24 });
    });
  }


  await pres.writeFile({ fileName: OUT });
  console.log("saved", OUT, pageNo, "slides");
})();
