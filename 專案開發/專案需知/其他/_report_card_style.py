"""數值報告 HTML 套用卡片版型（開發流程 §5.9，2026-10-22 使用者定）。

用法：py -X utf8 _report_card_style.py <專案>/report.html [...]
- 保留原有樣式與內容，另加 <style id="card-v2"> 覆蓋：淺灰底＋白色圓角卡片（深色模式為深灰卡片）、膠囊頁簽、襯線大標題。
- 每個頁簽（.panel）依 <h3> 分段，各段包成一張卡片；頁簽開頭沒有標題的說明文字，含表格／圖時也包成卡片，否則為說明列。
- 倍率線型圖例：沒有切換按鈕的圖例（<span><i>…</i>名稱</span>）改成按鈕，點選依顏色開關該條線。
- 倍率線型滑鼠提示：同時內嵌 chart_hover.js（見 _chart_hover.py）。
- 個人筆記/ 的修改紀錄、注意事項、上線觀察：先併成頁簽（見 _report_notes.py）。
- 可重複執行：舊的 card-v2 樣式與腳本會先移除，已包好的卡片不再重包。
"""
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

from _chart_hover import inject as inject_hover
from _report_notes import inject as inject_notes

CSS = """
/*card-v2：卡片版型，覆蓋原樣式*/
:root{--surface:#f3f3f1;--panel:#ffffff;--panel-2:#f7f7f5;--ink:#1b1b19;--ink-2:#5c5b57;--ink-3:#8a8882;--rule:#e2e1dc;--grid:#ecebe7;
--font-serif:'Source Serif 4',Georgia,'Noto Serif TC',serif;--font-sans:'IBM Plex Sans','Noto Sans TC',system-ui,-apple-system,'Segoe UI',sans-serif;--font-mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Consolas,monospace;--card-r:12px}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--surface:#1b1b1a;--panel:#262624;--panel-2:#2c2c2a;--ink:#f1f0ec;--ink-2:#b9b7b0;--ink-3:#8f8d87;--rule:#3a3936;--grid:#323130;color-scheme:dark}}
:root[data-theme="dark"]{--surface:#1b1b1a;--panel:#262624;--panel-2:#2c2c2a;--ink:#f1f0ec;--ink-2:#b9b7b0;--ink-3:#8f8d87;--rule:#3a3936;--grid:#323130;color-scheme:dark}
body{background:var(--surface);color:var(--ink)}
header{display:flex;flex-direction:column;gap:9px;padding-bottom:20px}
header .eyebrow{font-family:var(--font-mono);font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3)}
header h1{margin:0;font-family:var(--font-sans);font-weight:600;font-size:32px;letter-spacing:-.02em;text-wrap:balance}
.tabs{gap:4px;border-bottom:1px solid var(--rule);background:var(--surface);padding:8px 0 10px}
.tab{border:1px solid transparent;border-radius:999px;padding:6px 14px;margin:0}
.tab:hover{background:var(--panel-2);color:var(--ink)}
.tab[aria-selected="true"]{color:var(--ink);background:var(--panel);border-color:var(--rule);font-weight:500}
.panel:not([hidden]){display:flex;flex-direction:column;gap:16px;padding-top:20px}
.card{background:var(--panel);border:1px solid var(--rule);border-radius:var(--card-r);padding:20px 22px;min-width:0;margin:0}
.panel>.card,.panel>.intro,.panel>.kpis{margin:0}
.card>h3{margin:0 0 6px;font-size:16px;font-weight:500;border:0;padding:0}
.card>*:last-child{margin-bottom:0}
.card>*,.subcard>*{max-width:none}
.card>p,.card>ul,.subcard>p{width:auto}
.card p,.card ul,.intro{color:var(--ink-2);font-size:13.5px}
.intro p{margin:0 0 6px}
.card blockquote,.intro blockquote,.subcard blockquote{background:var(--panel-2);border:0;border-radius:8px;padding:11px 14px;font-size:12.5px;display:block;width:100%;max-width:none;box-sizing:border-box;margin-left:0;margin-right:0;margin-block:10px}
.card .tbl-wrap{border:0;border-radius:0;background:transparent;margin:6px 0 12px;overflow-x:auto}
.card th{background:transparent;color:var(--ink-3);border-bottom:1px solid var(--rule)}
/*表格淡格線*/
.card table,.subcard table,.intro table{border-collapse:collapse}
.card table th,.card table td,.subcard table th,.subcard table td,.intro table th,.intro table td{border:1px solid var(--grid)}
.card table th,.subcard table th{border-bottom:1px solid var(--rule)}
.card table tr:first-child th{border-top:1px solid var(--rule)}

.card .chart{border:1px solid var(--rule);border-radius:10px;background:var(--chart-bg,var(--panel-2));padding:14px 16px 8px;margin:4px 0 16px}
.card>blockquote,.card .subcard>blockquote,.intro>blockquote{width:100%;box-sizing:border-box;margin-left:0;margin-right:0}
.card>.chart{width:100%;box-sizing:border-box}
.card .chart h4{font-size:15px;margin:0 0 8px}
.chart svg text[font-size="10.5"]{font-size:14px}
.chart svg text[font-size="9"]{font-size:12px}
.chart svg text[font-size="11"]{font-size:14.5px}
.chart g.ser path{stroke-width:2.6px;stroke-opacity:.9}
.chart g.ser circle{r:3.2px}
.card .chart+.chart{padding-top:14px}
.legend .lg{border-radius:999px;padding:3px 10px}
.chart .legend{justify-content:flex-start;gap:8px}.chart .legend .lg{border:1px solid var(--rule);background:transparent;font-size:13px;color:var(--ink-2);display:inline-flex;align-items:center;gap:7px}
.legend .lg[aria-pressed="false"]{opacity:.4;text-decoration:line-through}
ul.rules{margin:0;padding-left:18px;max-width:none}ul.rules li{margin:2px 0}
td.ver{white-space:nowrap;font-family:var(--font-mono)}
.yz-hint{margin:0;font-size:13.5px;color:var(--ink-2);text-align:left}
.chart h4{text-align:center}
:root{--chart-bg:#fbfbf9;--chart-grid:rgba(0,0,0,.07)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--chart-bg:#34342f;--chart-grid:rgba(255,255,255,.07)}}
:root[data-theme="dark"]{--chart-bg:#34342f;--chart-grid:rgba(255,255,255,.07)}
.chart svg line.gl{stroke:var(--chart-grid);stroke-width:1}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(146px,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule);border-radius:3px;overflow:hidden;margin:18px 0 26px}
.kpi{background:var(--panel);padding:12px 15px;display:flex;flex-direction:column;gap:2px}
.kpi .lab{font-size:11.5px;color:var(--ink-3);font-family:var(--font-mono);letter-spacing:.04em}
.kpi .val{font-family:var(--font-mono);font-size:19px;font-weight:500;font-variant-numeric:tabular-nums}
.kpi .sub{font-size:11.5px;color:var(--ink-3)}
"""

# 沒有切換按鈕的圖例：span 改成按鈕，依圖例色塊的顏色開關 svg 內同色的線與點
JS = """
(function(){
  var probe=document.createElement('i');document.body.appendChild(probe);
  function norm(c){probe.style.color='';probe.style.color=c;return getComputedStyle(probe).color}
  document.querySelectorAll('.chart .legend').forEach(function(lg){
    if(lg.querySelector('.lg'))return;
    var svg=lg.closest('.chart').querySelector('svg');if(!svg)return;
    lg.querySelectorAll(':scope > span').forEach(function(sp){
      var sw=sp.querySelector('i');if(!sw)return;
      var col=norm(sw.style.background||sw.style.backgroundColor);
      var b=document.createElement('button');b.type='button';b.className='lg';b.setAttribute('aria-pressed','true');
      while(sp.firstChild)b.appendChild(sp.firstChild);sp.replaceWith(b);
      var marks=[].filter.call(svg.querySelectorAll('path,polyline,line,circle,rect'),function(el){
        var cs=getComputedStyle(el);return norm(cs.stroke)===col||norm(cs.fill)===col});
      b.addEventListener('click',function(){var on=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',String(on));
        marks.forEach(function(el){el.style.display=on?'':'none'})});
    });
  });
  probe.remove();
})();
"""

FONT = '<link rel="stylesheet" id="card-v2-font" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=Noto+Sans+TC:wght@400;500;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500&display=swap">'


def has_block(nodes):
    for n in nodes:
        if isinstance(n, Tag) and (n.name in ("table", "svg") or n.find(["table", "svg"])
                                   or "chart" in (n.get("class") or []) or "tbl-wrap" in (n.get("class") or [])):
            return True
    return False


def cardify(soup, panel):
    kids = [k for k in panel.children if not (isinstance(k, NavigableString) and not k.strip())]
    if kids and all(isinstance(k, Tag) and set(k.get("class") or []) & {"card", "intro", "kpis"} for k in kids):
        return
    groups, cur = [], []
    for k in kids:
        done = isinstance(k, Tag) and set(k.get("class") or []) & {"card", "intro", "kpis"}
        if done or (isinstance(k, Tag) and k.name == "h3"):   # 已包好的區塊與 h3 都是分段點
            if cur:
                groups.append(cur)
            cur = []
            if done:
                continue
        if not isinstance(k, Tag) and not cur:                # 段落之間的註解等不單獨成段
            continue
        cur.append(k)
    if cur:
        groups.append(cur)
    for g in groups:
        cls = "card" if (isinstance(g[0], Tag) and g[0].name == "h3") or has_block(g) else "intro"
        wrap = soup.new_tag("div", attrs={"class": cls})
        g[0].insert_before(wrap)
        for n in g:
            wrap.append(n.extract())



def game_names(p):
    """中文名取專案資料夾名（去掉 H0xx_），英文名取 game_rule.md 的「遊戲英文名」；缺的回空字串。"""
    import re
    p = p.resolve()
    zh = re.sub(r"^H\d+_", "", p.parent.name)
    en = ""
    rule = p.parent / "game_rule.md"
    if rule.exists():
        m = re.search(r"^\|\s*遊戲英文名\s*\|\s*([^|]+?)\s*\|", rule.read_text(encoding="utf-8"), re.M)
        if m:
            en = m.group(1).strip()
    return zh, en


def fix_header(soup, p):
    """頁首照競品分析：eyebrow「Omniplay · 數值報告」＋大標題「中文名 英文名」（缺的不顯示），2026-11-09 使用者定。"""
    import re
    hd = soup.find("header")
    if not hd or not re.match(r"H\d+_", p.resolve().parent.name):   # 只處理自家遊戲專案（競品報告不動）
        return
    zh, en = game_names(p)
    for e in hd.select(".eyebrow"):
        e.decompose()
    h1 = hd.find("h1") or soup.new_tag("h1")
    if not h1.parent:
        hd.append(h1)
    h1.string = " ".join(x for x in (zh, en) if x)
    eb = soup.new_tag("div", attrs={"class": "eyebrow"})
    eb.string = "Omniplay · 數值報告"
    h1.insert_before(eb)


def apply(path):
    p = Path(path)
    inject_notes(p)   # 修改紀錄／注意事項／上線觀察頁簽
    soup = BeautifulSoup(p.read_text(encoding="utf-8"), "html.parser")
    for old in soup.select("#card-v2, #card-v2-js, #card-v2-font"):
        old.decompose()
    head = soup.head or soup
    if not soup.find("meta", attrs={"name": "viewport"}):
        # 少了這行，手機會以 980px 版面渲染再縮放，卡片寬度看起來會不一致
        vp = soup.new_tag("meta")
        vp.attrs["name"] = "viewport"
        vp.attrs["content"] = "width=device-width, initial-scale=1"
        head.insert(0, vp)
    head.append(BeautifulSoup(FONT, "html.parser"))
    st = soup.new_tag("style", id="card-v2")
    st.string = CSS
    head.append(st)
    fix_header(soup, p)
    for panel in soup.select(".panel"):
        cardify(soup, panel)
    sc = soup.new_tag("script", id="card-v2-js")
    sc.string = JS + (Path(__file__).with_name("_chart_yzoom.js")).read_text(encoding="utf-8")
    # 報告內建的倍率線型提示與縱軸縮放共用同一份資料物件，縮放後提示圓點才會對位
    for s in soup.find_all("script"):
        a = "document.querySelectorAll('table').forEach(function(tb){var rows"
        b = "document.querySelectorAll('table').forEach(function (tb) {"
        if s.string and b in s.string and "data-nobar" not in s.string:
            s.string = s.string.replace(b, b + " if (tb.hasAttribute('data-nobar')) return;")
        if s.string and a in s.string:   # 表格加 data-nobar 就不畫占比條
            s.string = s.string.replace(a, "document.querySelectorAll('table').forEach(function(tb){if(tb.hasAttribute('data-nobar'))return;var rows")
        if s.string and "const d=JSON.parse(ch.dataset.hover)" in s.string:
            s.string = s.string.replace("const d=JSON.parse(ch.dataset.hover)", "const d=ch._hd||(ch._hd=JSON.parse(ch.dataset.hover))")
    (soup.body or soup).append(sc)
    p.write_text(str(soup), encoding="utf-8")
    inject_hover(p)   # 倍率線型滑鼠提示
    print("card-v2", p, len(soup.select(".panel")), "panels", len(soup.select(".card")), "cards")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        apply(a)
