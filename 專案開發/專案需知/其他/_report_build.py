"""數值報告 report.html 由 個人筆記/數值報告.md 重產（2026-11-09）。

用法：py -X utf8 _report_build.py <專案>/report.html [圖表資料.json]
- 以現有 report.html 當外殼（head、頁首、腳本保留），報告頁簽（md 的 `## N. 章名`）全部依 md 重畫；
  「玩法說明／修改紀錄／其他」三章是自動頁簽（_report_notes.py），md 只留一行說明，這裡略過。
- md 的 `<!--CHART:bg-->`／`fg`／`bf` 換成倍率線型圖；資料取 json（{"bg":{title,ymax,labels,series:[{name,color,v}]}}），
  沒給 json 就沿用現有 report.html 內同名圖的 data-hover 資料。名稱含「自然」的系列為虛線、預設隱藏。
- 頁首 KPI 取 md「基本指標」表本作欄（表頭＝game_rule.md 的遊戲英文名）的值；KPI 列沒有的指標不顯示。
- 最後自動跑 _report_card_style.py（卡片版型、頁首、自動頁簽、縱軸縮放）。
"""
import html as H
import importlib.util
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

HERE = Path(__file__).parent
_spec = importlib.util.spec_from_file_location("_build_html", HERE / "_build_html.py")
_bh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bh)

AUTO = {"玩法說明", "修改紀錄", "其他"}
KPI_ROWS = [("Total RTP", "總 RTP"), ("BG RTP", "BG RTP"), ("FG RTP", "FG RTP"), ("BG Hit Rate", "BG Hit Rate"),
            ("FG Hit Rate（每轉）", "FG Hit Rate"), ("FG 週期", "FG 週期"), ("FG 平均倍數（每場）", "FG 平均倍數"), ("BF RTP", "BF RTP")]
W, HH, L, T, IW, IH = 1100, 470, 52, 14, 1030, 324


def chart_html(key, c):
    labels, series = c["labels"], c["series"]
    n = len(labels)
    X = lambda i: L + i / (n - 1) * IW
    hover = {"W": W, "H": HH, "l": L, "t": T, "iw": IW, "ih": IH, "ymax": c["ymax"], "labels": labels,
             "series": [{"name": s["name"], "color": s["color"], "v": s["v"]} for s in series]}
    leg, sers = "", ""
    cid = f"clip{key}"
    for k, s in enumerate(series):
        nat = "自然" in s["name"]
        sw = f"repeating-linear-gradient(90deg,{s['color']} 0 4px,transparent 4px 7px)" if nat else s["color"]
        leg += (f'<button aria-pressed="{"false" if nat else "true"}" class="lg" data-k="{k}" type="button">'
                f'<i style="background:{sw}"></i>{H.escape(s["name"])}</button>')
        dash = ' stroke-dasharray="5 4"' if nat else ""
        dots = "".join(f'<circle cx="{X(i):.2f}" cy="{T + IH:.2f}" fill="{s["color"]}" fill-opacity="0.75" r="2.4"></circle>' for i in range(n))
        sers += (f'<g class="ser{" off" if nat else ""}" clip-path="url(#{cid})" data-k="{k}">'
                 f'<path d="" fill="none" stroke="{s["color"]}"{dash} stroke-linecap="round" stroke-linejoin="round" stroke-opacity="0.55" stroke-width="1.6"></path>{dots}</g>')
    ticks = ""
    for i, lab in enumerate(labels):
        x = X(i)
        ticks += (f'<line stroke="var(--rule)" x1="{x:.1f}" x2="{x:.1f}" y1="{T + IH}" y2="{T + IH + 4}"></line>'
                  f'<text fill="var(--ink-3)" font-family="var(--font-mono)" font-size="9" text-anchor="end" transform="translate({x:.2f},{T + IH + 8}) rotate(-90)">{H.escape(lab)}</text>')
    svg = (f'<svg aria-label="{H.escape(c["title"])}" role="img" viewBox="0 0 {W} {HH}"><defs><clipPath id="{cid}">'
           f'<rect height="{IH + 5}" width="{IW + 8}" x="{L - 4}" y="{T - 1}"></rect></clipPath></defs>'
           f'<line stroke="var(--grid)" x1="{L}" x2="{L + IW}" y1="{T + IH}" y2="{T + IH}"></line>{ticks}'
           f'<text fill="var(--ink-3)" font-size="11" text-anchor="middle" x="{L + IW / 2:.1f}" y="462">倍率區間（× 底注）</text>'
           f'<text fill="var(--ink-3)" font-size="11" text-anchor="middle" transform="translate(12,{T + IH / 2:.1f}) rotate(-90)">Hit Rate</text>'
           f"{sers}</svg>")
    return (f"<div class=\"chart\" data-key=\"{key}\" data-hover='{H.escape(json.dumps(hover, ensure_ascii=False), quote=True)}'>"
            f'<h4>{H.escape(c["title"])}</h4><div class="legend">{leg}</div><div class="plot">{svg}<div class="tip" hidden=""></div></div></div>')


def md_table(body, h3):
    m = re.search(rf"^### {re.escape(h3)}\s*\n(.*?)(?=^### |\Z)", body, re.S | re.M)
    if not m:
        return None
    rows = [r for r in m.group(1).splitlines() if r.startswith("|")]
    cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
    return cells[0], cells[2:]


def build(report, curves=None):
    p = Path(report)
    md = (p.parent / "個人筆記" / "數值報告.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    soup = BeautifulSoup(p.read_text(encoding="utf-8"), "html.parser")
    old = {}
    for ch in soup.select(".chart[data-hover]"):
        d = json.loads(ch["data-hover"])
        t = ch.h4.get_text(strip=True) if ch.h4 else ""
        key = ch.get("data-key") or ("bg" if "BG" in t else "bf" if t.startswith("BF") else "fg")
        old.setdefault(key, {"title": t, "ymax": d["ymax"], "labels": d["labels"], "series": d["series"]})
    data = json.loads(Path(curves).read_text(encoding="utf-8")) if curves else old

    chaps = re.split(r"^## \d+\.\s*", md, flags=re.M)[1:]
    panels = []
    for ch in chaps:
        name, _, body = ch.partition("\n")
        name = name.strip()
        if name in AUTO:
            continue
        body = re.sub(r"<!--CHART:(\w+)-->", r"\n\n@@CHART:\1@@\n\n", body)   # 前後補空行：相鄰的標記才不會併成同一段
        h = _bh.Renderer("report").render(body)
        h = re.sub(r"<p>@@CHART:(\w+)@@</p>", lambda m: chart_html(m.group(1), data[m.group(1)]) if m.group(1) in data else "", h)
        frag = BeautifulSoup(h, "html.parser")
        for c in frag.select("td.n, th.n"):
            if c.name == "td":
                c["class"] = ["num"]
            else:
                del c["class"]
        for c in frag.select("td"):   # 儲存格結尾 {+}／{-}：本作比競品好（綠）／差（紅），2026-11-11
            s = c.get_text()
            m = re.search(r"\s*\{([+-])\}\s*$", s)
            if m:
                for t in c.find_all(string=True)[::-1]:
                    if "{" in t:
                        t.replace_with(re.sub(r"\s*\{[+-]\}\s*$", "", str(t)))
                        break
                c["class"] = c.get("class", []) + ["good" if m.group(1) == "+" else "bad"]
        for e in frag.select("[id]"):
            if e.name in ("h3", "h4"):
                del e["id"]
        for e in frag.select("strong.nr"):
            del e["class"]
        for h3 in frag.find_all("h3"):   # 基本指標是混合指標，不畫占比條
            if h3.get_text(strip=True) == "基本指標":
                for t in h3.find_all_next("table"):
                    prev = t.find_previous("h3")
                    if prev is not h3:
                        break
                    t["data-nobar"] = ""
        panels.append((name, str(frag)))

    # 移除舊頁簽（含自動頁簽，card_style 會重加）
    for t in soup.select(".tab"):
        t.decompose()
    olds = soup.select(".panel")
    tabs = soup.select_one(".tabs")
    anchor = olds[0]
    for i, (name, body) in enumerate(panels):
        b = soup.new_tag("button", attrs={"aria-controls": f"panel-{i}", "aria-selected": "true" if i == 0 else "false",
                                          "class": "tab", "id": f"tab-{i}", "role": "tab", "tabindex": "0" if i == 0 else "-1"})
        b.string = f"{i + 1}. {name}"
        tabs.append(b)
        sec = soup.new_tag("section", attrs={"aria-labelledby": f"tab-{i}", "class": "panel", "id": f"panel-{i}", "role": "tabpanel"})
        if i:
            sec["hidden"] = ""
        sec.append(BeautifulSoup(body, "html.parser"))
        anchor.insert_before(sec)
    for o in olds:
        o.decompose()

    # 頁首 KPI
    kp = soup.select_one("#hero-kpis")
    if kp is None and soup.find("header") is not None:   # 舊報告沒有 KPI 容器就補在頁首後面
        kp = soup.new_tag("div", attrs={"class": "kpis", "id": "hero-kpis"})
        soup.find("header").insert_after(kp)
    tb = md_table(md, "基本指標")
    if kp is not None and tb:
        hdr, rows = tb
        en = ""
        rule = p.parent / "game_rule.md"
        if rule.exists():
            m = re.search(r"^\|\s*遊戲英文名\s*\|\s*([^|]+?)\s*\|", rule.read_text(encoding="utf-8"), re.M)
            en = m.group(1).strip() if m else ""
        # 本作欄：表頭等於遊戲英文名的第一欄，找不到就用表頭以英文名開頭的第一欄，再不行用第 2 欄
        col = next((i for i, h in enumerate(hdr) if en and h == en), None) or             next((i for i, h in enumerate(hdr) if en and h.startswith(en)), None) or 1
        rv = {r[0]: r[col] for r in rows}
        kp.clear()
        for k, lab in KPI_ROWS:
            if rv.get(k) not in (None, "", "—"):
                kp.append(BeautifulSoup(f'<div class="kpi"><span class="lab">{lab}</span><span class="val">{rv[k]}</span></div>', "html.parser"))
    p.write_text(str(soup), encoding="utf-8")
    print("build", p, [n for n, _ in panels])
    spec = importlib.util.spec_from_file_location("_report_card_style", HERE / "_report_card_style.py")
    cs = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(HERE))
    spec.loader.exec_module(cs)
    cs.apply(p)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
