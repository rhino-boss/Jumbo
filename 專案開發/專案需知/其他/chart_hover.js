/* 倍率線型滑鼠提示（通用版）：滑鼠移到圖上，鎖定最近的倍率區間，列出各條線的數值。
 * 適用直接畫好的 SVG 折線圖（縱軸 % 刻度＋橫軸旋轉 -90° 的區間標籤），數值由 SVG 座標反推。
 * 已有自己提示的圖（.chart[data-hover]、或 SVG 內有透明 rect 偵測層）不處理。
 * 來源：專案需知/其他/chart_hover.js；由 _chart_hover.py 內嵌進網頁、demogame_common.js 也帶同一份。
 */
(function () {
  if (window.__chartHoverAuto) return;
  window.__chartHoverAuto = true;
  var NS = "http://www.w3.org/2000/svg";
  var tip = null, cur = null;

  function own(svg) {
    return svg.closest(".chart[data-hover]") || svg.querySelector('rect[fill="transparent"]');
  }
  function toSvg(svg, el) {   // el 的座標 → svg viewBox 座標
    var a = svg.getScreenCTM(), b = el.getScreenCTM();
    return a && b ? a.inverse().multiply(b) : null;
  }
  function pt(m, x, y) { return { x: m.a * x + m.c * y + m.e, y: m.b * x + m.d * y + m.f }; }
  function rotated(t) {
    var s = (t.getAttribute("transform") || "") + " " + (t.parentNode.getAttribute && t.parentNode.getAttribute("transform") || "");
    return /rotate\(\s*-?90/.test(s);
  }
  function colorOf(el, prop) {
    var c = getComputedStyle(el)[prop];
    return c && c !== "none" && !/rgba\([^)]*,\s*0(\.0+)?\)$/.test(c) ? c : "";
  }
  function hiddenEl(el) {
    for (var e = el; e && e.nodeType === 1; e = e.parentNode) {
      if (getComputedStyle(e).display === "none") return true;
    }
    return false;
  }
  function parse(svg) {
    var texts = [].slice.call(svg.querySelectorAll("text"));
    var labels = [], ticks = [];
    texts.forEach(function (t) {
      var m = toSvg(svg, t); if (!m) return;
      var p = pt(m, parseFloat(t.getAttribute("x")) || 0, parseFloat(t.getAttribute("y")) || 0);
      var s = t.textContent.trim();
      if (rotated(t)) { if (s) labels.push({ x: p.x, lab: s }); }
      else {
        var v = /^(-?\d+(?:\.\d+)?)\s*%$/.exec(s);
        if (v) ticks.push({ y: p.y, v: parseFloat(v[1]), x: p.x });
      }
    });
    if (labels.length < 3 || ticks.length < 2) return null;
    labels.sort(function (a, b) { return a.x - b.x; });
    // 刻度字的 y 是基線；改用最近的水平格線
    var hlines = [].slice.call(svg.querySelectorAll("line")).map(function (l) {
      var m = toSvg(svg, l); if (!m) return null;
      var p1 = pt(m, +l.getAttribute("x1"), +l.getAttribute("y1")), p2 = pt(m, +l.getAttribute("x2"), +l.getAttribute("y2"));
      return Math.abs(p1.y - p2.y) < 0.5 && Math.abs(p1.x - p2.x) > 50 ? p1.y : null;
    }).filter(function (y) { return y !== null; });
    ticks.forEach(function (k) {
      var best = null;
      hlines.forEach(function (y) { var d = k.y - y; if (d >= 0 && d < 8 && (best === null || d < k.y - best)) best = y; });
      k.gy = best !== null ? best : k.y - 3.5;
    });
    ticks.sort(function (a, b) { return a.v - b.v; });
    var t0 = ticks[0], t1 = ticks[ticks.length - 1];
    if (t1.v === t0.v || t1.gy === t0.gy) return null;
    var k = (t1.v - t0.v) / (t1.gy - t0.gy);
    var val = function (y) { return t0.v + (y - t0.gy) * k; };
    var plotL = Math.max.apply(null, ticks.map(function (t) { return t.x; }));
    var pitch = labels.length > 1 ? (labels[labels.length - 1].x - labels[0].x) / (labels.length - 1) : 10;
    var idxOf = function (x) {
      var best = -1, bd = Infinity;
      labels.forEach(function (l, i) { var d = Math.abs(l.x - x); if (d < bd) { bd = d; best = i; } });
      return bd <= pitch * 0.6 ? best : -1;
    };
    // 各條線：依顏色分組（折線＋單點）
    var series = [], byColor = {};
    function ser(c) {
      if (!byColor[c]) { byColor[c] = { c: c, v: {}, els: [] }; series.push(byColor[c]); }
      return byColor[c];
    }
    [].slice.call(svg.querySelectorAll("path, polyline")).forEach(function (el) {
      if (el.closest("defs, clipPath, clippath") || el.classList.contains("cha-ui")) return;
      var c = colorOf(el, "stroke"); if (!c) return;
      if ((parseFloat(getComputedStyle(el).strokeWidth) || 1) < 1.4) return;
      if (colorOf(el, "fill")) return;
      var m = toSvg(svg, el); if (!m) return;
      var nums = el.tagName.toLowerCase() === "polyline" ? (el.getAttribute("points") || "")
        : (el.getAttribute("d") || "");
      if (/[a-z]/.test(nums.replace(/[ML]/g, "").replace(/e-?\d/gi, ""))) return;   // 只認絕對座標 M/L
      var arr = (nums.match(/-?\d+(?:\.\d+)?(?:e-?\d+)?/gi) || []).map(Number);
      var s = ser(c); s.els.push(el);
      for (var i = 0; i + 1 < arr.length; i += 2) {
        var p = pt(m, arr[i], arr[i + 1]), ix = idxOf(p.x);
        if (ix >= 0) s.v[ix] = p.y;
      }
    });
    [].slice.call(svg.querySelectorAll("circle")).forEach(function (el) {
      if (el.classList.contains("cha-ui") || +el.getAttribute("r") < 1.5) return;
      if (el.getAttribute("opacity") === "0") return;
      var c = colorOf(el, "fill"); if (!c) return;
      var m = toSvg(svg, el); if (!m) return;
      var p = pt(m, +el.getAttribute("cx"), +el.getAttribute("cy")), ix = idxOf(p.x);
      if (ix < 0) return;
      var s = ser(c); s.els.push(el);
      if (s.v[ix] === undefined) s.v[ix] = p.y;
    });
    series = series.filter(function (s) { return Object.keys(s.v).length; });
    if (!series.length) return null;
    // 名稱：附近圖例中同色的項目
    var root = svg.parentNode;
    for (var up = 0; up < 3 && root && !root.querySelector(".legend, .lg, [class*=legend]"); up++) root = root.parentNode;
    var probe = document.createElement("i"); document.body.appendChild(probe);
    var norm = function (c) { probe.style.color = ""; probe.style.color = c; return getComputedStyle(probe).color; };
    var swatches = root ? [].slice.call(root.querySelectorAll(".legend i, .legend span[style], .lg i, [class*=legend] i, [class*=legend] [style*=background]")) : [];
    series.forEach(function (s, i) {
      var c = norm(s.c), name = "";
      swatches.some(function (sw) {
        if (norm(sw.style.background || sw.style.backgroundColor || sw.style.borderColor || "") !== c) return false;
        var host = sw.closest("button, label, li, span:not([style])") || sw.parentNode;
        name = host.textContent.trim(); return !!name;
      });
      s.n = name || (series.length === 1 ? (svg.getAttribute("aria-label") || "") : "線 " + (i + 1));
    });
    probe.remove();
    return { labels: labels, series: series, val: val, top: t1.gy, max: t1.v, bottom: t0.gy, plotL: plotL };
  }
  function fmt(v) {
    if (Math.abs(v) < 1e-9) return "0%";
    return (Math.abs(v) >= 1 ? v.toFixed(2) : Math.abs(v) >= 0.01 ? v.toFixed(4) : v.toPrecision(3)) + "%";
  }
  function ensureTip() {
    if (tip) return tip;
    tip = document.createElement("div");
    tip.setAttribute("style", "position:fixed;z-index:2147483000;pointer-events:none;display:none;background:rgba(10,12,16,.92);color:#f0efec;"
      + "border:1px solid rgba(255,255,255,.15);border-radius:6px;padding:6px 9px;font:12px/1.5 ui-monospace,Consolas,monospace;white-space:nowrap;"
      + "box-shadow:0 4px 14px rgba(0,0,0,.25)");
    document.body.appendChild(tip);
    return tip;
  }
  function clear() {
    if (tip) tip.style.display = "none";
    if (cur) cur.ui.forEach(function (e) { e.remove(); });
    cur = null;
  }
  function esc(s) { return String(s).replace(/[&<>]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); }
  document.addEventListener("mousemove", function (e) {
    var svg = e.target.closest && e.target.closest("svg");
    while (svg && svg.ownerSVGElement) svg = svg.ownerSVGElement;
    if (!svg || own(svg)) { if (cur) clear(); return; }
    if (!cur || cur.svg !== svg) {
      clear();
      var info = parse(svg);
      if (!info) return;
      cur = { svg: svg, info: info, ui: [], ix: -1 };
    }
    var info = cur.info, m = svg.getScreenCTM(); if (!m) return;
    var p = pt(m.inverse(), e.clientX, e.clientY);
    if (p.x < info.plotL || p.y < info.top - 20 || p.y > info.bottom + 10) { if (tip) tip.style.display = "none"; cur.ui.forEach(function (u) { u.remove(); }); cur.ui = []; cur.ix = -1; return; }
    var ix = -1, bd = Infinity;
    info.labels.forEach(function (l, i) { var d = Math.abs(l.x - p.x); if (d < bd) { bd = d; ix = i; } });
    if (ix !== cur.ix) {
      cur.ix = ix;
      cur.ui.forEach(function (u) { u.remove(); }); cur.ui = [];
      var x = info.labels[ix].x;
      var ln = document.createElementNS(NS, "line");
      [["x1", x], ["x2", x], ["y1", info.top], ["y2", info.bottom], ["stroke", "currentColor"], ["stroke-dasharray", "3 3"], ["opacity", ".45"], ["class", "cha-ui"], ["pointer-events", "none"]]
        .forEach(function (a) { ln.setAttribute(a[0], a[1]); });
      svg.appendChild(ln); cur.ui.push(ln);
      var html = "<b style=\"display:block;margin-bottom:2px\">" + esc(info.labels[ix].lab) + "</b>";
      info.series.forEach(function (s) {
        if (s.els.length && s.els.every(hiddenEl)) return;   // 圖例關掉的線不列
        var y = s.v[ix], txt = "—";
        if (y !== undefined) {
          var v = info.val(y);
          txt = y <= info.top + 0.6 && v >= info.max - 1e-9 ? "≥ " + fmt(info.max) : fmt(Math.max(0, v));
          var c = document.createElementNS(NS, "circle");
          [["cx", info.labels[ix].x], ["cy", y], ["r", 4.5], ["fill", s.c], ["stroke", "#fff"], ["stroke-width", 1.5], ["class", "cha-ui"], ["pointer-events", "none"]]
            .forEach(function (a) { c.setAttribute(a[0], a[1]); });
          svg.appendChild(c); cur.ui.push(c);
        }
        html += "<div style=\"display:flex;justify-content:space-between;gap:18px\"><span><i style=\"display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px;background:"
          + s.c + "\"></i>" + esc(s.n) + "</span><span>" + txt + "</span></div>";
      });
      ensureTip().innerHTML = html;
    }
    var t = ensureTip(); t.style.display = "block";
    var lx = e.clientX + 16, ly = e.clientY + 14;
    if (lx + t.offsetWidth > innerWidth - 4) lx = e.clientX - t.offsetWidth - 16;
    if (ly + t.offsetHeight > innerHeight - 4) ly = e.clientY - t.offsetHeight - 14;
    t.style.left = Math.max(4, lx) + "px"; t.style.top = Math.max(4, ly) + "px";
  });
  document.addEventListener("mouseleave", clear);
  window.addEventListener("scroll", function () { if (tip) tip.style.display = "none"; }, true);
})();
