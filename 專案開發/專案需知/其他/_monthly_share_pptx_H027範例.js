// 宙斯 2500 月會分享（v04 起的版式）（深藍＋金色、閃電圖示圓圈為主視覺）
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

  // ---- 2 目錄
  {
    const s = base();
    title(s, "目錄", "OUTLINE");
    const items = [["01", "遊戲設計", "核心玩法、設計重點、跟競品差異"], ["02", "跟競品不同的地方", "5000x 大獎、2500x 球、AB Test"],
                   ["03", "數據佐證", "玩法深淺、每天的大獎推播"], ["04", "AI", "從側錄到調性的 AI 流程"]];
    items.forEach(([n, t, d], i) => {
      const x = 0.6 + (i % 2) * 6.2, y = 1.8 + Math.floor(i / 2) * 2.35;
      card(s, x, y, 5.9, 2.0);
      s.addText(n, { x: x + 0.4, y: y + 0.35, w: 1.4, h: 1.0, fontSize: 44, bold: true, color: GOLD, margin: 0, isTextBox: true });
      s.addText(t, { x: x + 1.8, y: y + 0.45, w: 3.9, h: 0.5, fontSize: 22, bold: true, color: TEXT, margin: 0, isTextBox: true });
      s.addText(d, { x: x + 1.8, y: y + 1.0, w: 3.9, h: 0.4, fontSize: 14, color: MUTED, margin: 0, isTextBox: true });
    });
  }

  // ---- 01 遊戲設計
  section("01", "遊戲設計", "大倍數 ＋ 大基底 ＝ 超大倍數");
  const core = [
    ["layers", "layersG", "連消", "全盤 8 個以上就中，消除後掉落"],
    ["boltN", "boltGrey", "倍數球", "最高 2500x，C3 每次消除升一級"],
    ["gift", "giftGrey", "免費遊戲", "倍數跨場累積"],
  ];
  for (let k = 1; k <= 4; k++) {
    const s = base();
    title(s, "遊戲核心玩法", "CORE GAMEPLAY");
    core.forEach(([on, off, h, d], i) => {
      const visible = i < k;
      const active = k === 4 ? true : i === k - 1;
      if (visible) iconRow(s, 0.6, 1.85 + i * 1.25, 5.0, active ? IC[on] : IC[off], h, d, active);
    });
    if (k === 4) {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.6, w: 6.1, h: 0.85, rectRadius: 0.42, fill: { color: NAVY }, line: { color: NAVY } });
      s.addText("大倍數 ＋ 大基底 ＝ 超大倍數", { x: 0.6, y: 5.6, w: 6.1, h: 0.85, fontSize: 22, bold: true, color: GOLD, align: "center", valign: "middle", margin: 0, isTextBox: true });
    }
    shot(s, 7.3, 1.85, 5.4);
  }

  // 設計重點：三欄
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
  {
    const s = base();
    title(s, "跟競品差異", "VS. GATES OF OLYMPUS 1000");
    const rows = [["chart", "倍數球更多", "BG 每 26.9 → 8.4 轉一次"], ["check", "延續：有球 Hit Rate 較高", "27.28% → 44.56%"],
                  ["down", "延續：每輪一顆球", "消久必出球"], ["boltN", "新增 Extra Bet", "FG 週期 450.3 → 90.2 轉"]];
    rows.forEach(([ic, h, d], i) => iconRow(s, 0.6, 1.8 + i * 1.12, 4.3, IC[ic], h, d, true, 0.65));
    table(s, 6.4, 1.85, 6.3, [
      ["指標", "Gates of Olympus 1000", "宙斯 2500"],
      ["倍數球上限", "1000x", "2500x"],
      ["BG 倍數球週期", "26.9 轉", "8.4 轉"],
      ["無球 Hit Rate", "28.13%", "27.28%"],
      ["有球 Hit Rate", "45.34%", "44.56%"],
      ["EB FG 週期", "沒有", "90.2 轉"],
    ], [1.9, 2.6, 1.8], 2);
    note(s, "※ 宙斯 B 版 Card-On 7.4.0.0；Hit Rate 取自然機率；競品為 3.1 萬局側錄", 6.35);
  }

  // 輪帶設計：左右對照
  {
    const s = base();
    title(s, "輪帶設計：每輪一顆倍數球", "REEL DESIGN");
    bigStat(s, 0.6, 1.85, 5.9, 2.4, "每輪 1 顆", "競品（宙斯採用）", "消得夠久，一定會有倍數球", true);
    bigStat(s, 6.8, 1.85, 5.9, 2.4, "每輪多顆", "埃及秘寶", "卡片系統下，出球後基本上就停止消除");
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 4.65, w: 12.1, h: 0.85, rectRadius: 0.42, fill: { color: GOLDL }, line: { color: GOLDL } });
    s.addImage({ data: IC.boltN, x: 0.95, y: 4.87, w: 0.4, h: 0.4 });
    s.addText("宙斯採用競品做法：出球後仍能連消", { x: 1.55, y: 4.65, w: 10.8, h: 0.85, fontSize: 20, bold: true, color: NAVY, valign: "middle", margin: 0, isTextBox: true });
  }

  // ---- 02 跟競品不同的地方
  section("02", "跟競品不同的地方", "5000x 大獎、2500x 球、AB Test");
  {
    const s = base();
    title(s, "其他調整", "ADJUSTMENTS");
    bigStat(s, 0.6, 1.85, 5.9, 2.9, "1/892,857", "≥5000x 週期（局）", "5000x 大獎更常出現\n客戶反應高倍數太少（2026-10-22）\n競品樣本未出現", true);
    bigStat(s, 6.8, 1.85, 5.9, 2.9, "1/1,955", "BG 2500x 球（轉）", "BG 上限開到 2000x，2500x 球拿得到\n競品倍數球最高 1000x");
  }
  {
    const s = base();
    title(s, "AB Test", "B 版主推");
    s.addText("只差 BG，FG／BF 相同；上線後觀察新手／老手留存、人均轉數、遊玩時長", { x: 0.6, y: 1.5, w: 12.1, h: 0.4, fontSize: 15, color: MUTED, margin: 0, isTextBox: true });
    const cols = [["A 版", "貼近競品", false, ["13.7 轉", "250x", "162,866 局", "13.19"]], ["B 版（主推）", "特色更豐富", true, ["8.4 轉", "2000x", "26,364 局", "16.18"]]];
    const labels = ["BG 倍數球週期", "BG 上限", "≥1000x 週期", "標準差"];
    cols.forEach(([name, tag, dark, vals], i) => {
      const x = 0.6 + i * 6.2;
      card(s, x, 2.15, 5.9, 4.2, dark ? NAVY : TINT);
      s.addText(name, { x: x + 0.4, y: 2.4, w: 3.5, h: 0.55, fontSize: 24, bold: true, color: dark ? GOLD : TEXT, margin: 0, isTextBox: true });
      s.addText(tag, { x: x + 3.7, y: 2.45, w: 1.8, h: 0.45, fontSize: 14, bold: true, color: dark ? NAVY : MUTED, align: "center", valign: "middle",
        fill: { color: dark ? GOLD : "E3E8F2" }, margin: 0, isTextBox: true });
      vals.forEach((v, j) => {
        const y = 3.2 + j * 0.75;
        s.addText(labels[j], { x: x + 0.4, y, w: 2.8, h: 0.5, fontSize: 15, color: dark ? "AEB8D8" : MUTED, valign: "middle", margin: 0, isTextBox: true });
        s.addText(v, { x: x + 3.0, y, w: 2.5, h: 0.5, fontSize: 22, bold: true, color: dark ? WHITE : TEXT, align: "right", valign: "middle", margin: 0, isTextBox: true });
      });
    });
  }

  // ---- 03 數據佐證
  section("03", "數據佐證", "玩法深淺、每天的大獎推播");
  {
    const s = base();
    title(s, "玩法深淺", "VOLATILITY");
    bigStat(s, 0.6, 1.85, 4.6, 2.5, "16.18", "標準差（NB）", "約競品 2 倍（8.05），屬「深」\n輸贏起伏大、大獎集中", true);
    table(s, 5.6, 1.85, 7.1, [
      ["指標（NB）", "Gates of Olympus 1000", "宙斯 2500"],
      ["≥1000x 週期", "樣本未出現", "26,364 局"],
      ["≥5000x 週期", "樣本未出現", "892,857 局"],
      ["≥10000x 週期", "樣本未出現", "4,166,667 局"],
      ["存活中位數", "—", "6,485 把"],
    ], [2.2, 2.6, 2.3], 2);
    note(s, "※ 競品 3.1 萬局側錄，尾端未取樣，標準差會被低估；存活中位數＝1000 元、每把 1 元", 4.7);
  }
  {
    const s = base();
    title(s, "每天看得到幾次大獎推播", "DAILY BIG WINS");
    const st = [["76～1,138", "≥1000x／天", "每天上百次千倍推播", true], ["2～34", "≥5000x／天", "每天都有 5000x 以上", false], ["0.5～7", "≥10000x／天", "", false]];
    st.forEach(([n, l, d, dark], i) => bigStat(s, 0.6 + i * 4.1, 1.85, 3.8, 3.2, n, l, d, dark));
    card(s, 0.6, 5.35, 12.1, 0.75, "FFFFFF");
    s.addText("換算：每天轉數 ÷ 週期；轉數借皮娜塔前 6 名平台一天約 200 萬～3,000 萬轉（2026-10-22）",
      { x: 0.9, y: 5.35, w: 11.6, h: 0.75, fontSize: 14, color: MUTED, valign: "middle", margin: 0, isTextBox: true });
  }

  // ---- 04 AI：流程
  {
    const s = base();
    title(s, "AI", "04 · AI WORKFLOW");
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

  // ---- Q & A
  {
    const s = base(true);
    circle(s, (W - 1.4) / 2, 1.9, 1.4, IC.boltN, GOLD);
    s.addText("Q & A", { x: 0, y: 3.5, w: W, h: 1.2, fontSize: 60, bold: true, color: WHITE, align: "center", margin: 0, isTextBox: true });
    s.addText("ZEUS 2500 · 宙斯 2500", { x: 0, y: 4.7, w: W, h: 0.5, fontSize: 18, color: GOLD, align: "center", margin: 0, isTextBox: true });
  }

  await pres.writeFile({ fileName: OUT });
  console.log("saved", OUT, pageNo, "slides");
})();
