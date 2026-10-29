"""數值報告 HTML 套用卡片版型（開發流程 §5.9，2026-10-22 使用者定）。

用法：py -X utf8 _report_card_style.py <數值報告_xxx.html> [...]
- 保留原有樣式與內容，另加 <style id="card-v2"> 覆蓋：淺灰底＋白色圓角卡片（深色模式為深灰卡片）、膠囊頁簽、襯線大標題。
- 每個頁簽（.panel）依 <h3> 分段，各段包成一張卡片；頁簽開頭沒有標題的說明文字，含表格／圖時也包成卡片，否則為說明列。
- 倍率線型圖例：沒有切換按鈕的圖例（<span><i>…</i>名稱</span>）改成按鈕，點選依顏色開關該條線。
- 倍率線型滑鼠提示：同時內嵌 chart_hover.js（見 _chart_hover.py）。
- 可重複執行：舊的 card-v2 樣式與腳本會先移除，已包好的卡片不再重包。
"""
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

from _chart_hover import inject as inject_hover

CSS = """
/*card-v2：卡片版型，覆蓋原樣式*/
:root{--surface:#f3f3f1;--panel:#ffffff;--panel-2:#f7f7f5;--ink:#1b1b19;--ink-2:#5c5b57;--ink-3:#8a8882;--rule:#e2e1dc;--grid:#ecebe7;
--font-serif:'Source Serif 4',Georgia,'Noto Serif TC',serif;--card-r:12px}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--surface:#1b1b1a;--panel:#262624;--panel-2:#2c2c2a;--ink:#f1f0ec;--ink-2:#b9b7b0;--ink-3:#8f8d87;--rule:#3a3936;--grid:#323130;color-scheme:dark}}
:root[data-theme="dark"]{--surface:#1b1b1a;--panel:#262624;--panel-2:#2c2c2a;--ink:#f1f0ec;--ink-2:#b9b7b0;--ink-3:#8f8d87;--rule:#3a3936;--grid:#323130;color-scheme:dark}
body{background:var(--surface);color:var(--ink)}
header h1{font-family:var(--font-serif);font-weight:400;font-size:34px;letter-spacing:-.01em;text-wrap:balance}
.tabs{gap:4px;border-bottom:1px solid var(--rule);background:var(--surface);padding:8px 0 10px}
.tab{border:1px solid transparent;border-radius:999px;padding:6px 14px;margin:0}
.tab:hover{background:var(--panel-2);color:var(--ink)}
.tab[aria-selected="true"]{color:var(--ink);background:var(--panel);border-color:var(--rule);font-weight:500}
.panel:not([hidden]){display:flex;flex-direction:column;gap:16px;padding-top:20px}
.card{background:var(--panel);border:1px solid var(--rule);border-radius:var(--card-r);padding:20px 22px;min-width:0}
.card>h3{margin:0 0 6px;font-size:16px;font-weight:500;border:0;padding:0}
.card>*:last-child{margin-bottom:0}
.card p,.card ul,.intro{color:var(--ink-2);font-size:13.5px}
.intro p{margin:0 0 6px}
.card blockquote,.intro blockquote{background:var(--panel-2);border:0;border-radius:8px;padding:9px 12px;font-size:12.5px}
.card .tbl-wrap{border:0;border-radius:0;background:transparent;margin:6px 0 12px;overflow-x:auto}
.card th{background:transparent;color:var(--ink-3);border-bottom:1px solid var(--rule)}
.card .chart{border:0;background:transparent;padding:0;margin:0 0 12px}
.card .chart+.chart{padding-top:16px;border-top:1px solid var(--grid)}
.legend .lg{border-radius:999px;padding:3px 10px}
.legend .lg[aria-pressed="false"]{opacity:.4;text-decoration:line-through}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:16px}
.kpi{display:flex;flex-direction:column;gap:4px}
.kpi .lab{font-size:12.5px;color:var(--ink-3)}
.kpi .val{font-family:var(--font-serif);font-size:32px;line-height:1.15;font-variant-numeric:lining-nums tabular-nums}
.kpi .sub{font-size:12.5px;color:var(--ink-2)}
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

FONT = '<link rel="stylesheet" id="card-v2-font" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,500&display=swap">'


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


def apply(path):
    p = Path(path)
    soup = BeautifulSoup(p.read_text(encoding="utf-8"), "html.parser")
    for old in soup.select("#card-v2, #card-v2-js, #card-v2-font"):
        old.decompose()
    head = soup.head or soup
    head.append(BeautifulSoup(FONT, "html.parser"))
    st = soup.new_tag("style", id="card-v2")
    st.string = CSS
    head.append(st)
    for panel in soup.select(".panel"):
        cardify(soup, panel)
    sc = soup.new_tag("script", id="card-v2-js")
    sc.string = JS
    (soup.body or soup).append(sc)
    p.write_text(str(soup), encoding="utf-8")
    inject_hover(p)   # 倍率線型滑鼠提示
    print("card-v2", p, len(soup.select(".panel")), "panels", len(soup.select(".card")), "cards")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        apply(a)
