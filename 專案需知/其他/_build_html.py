# -*- coding: utf-8 -*-
"""將 專案需知/ 的 Markdown 文件彙整成單一 igaming_specification.html。

本腳本放在 專案需知/其他/，規範 .md 與輸出 HTML 在上一層（專案需知/，Omniplay 產線）。

用法（在 其他/ 內執行）：
    py _build_html.py

規則：任何一份 .md 更新後，必須重跑本腳本同步更新 HTML。
不依賴第三方套件，只支援本規範集實際使用的 Markdown 子集：
標題、表格、圍欄程式碼、清單（含巢狀與核取方塊）、粗體、行內程式碼、連結、分隔線。
"""

import html
import re
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent.parent  # 專案需知/（規範 .md 所在層）
OUTPUT = HERE / "igaming_specification.html"

# (tab_id, 頁籤名稱, 檔名)
TABS = [
    ("overview", "總覽", "其他/_README.md"),
    ("flow", "開發流程", "開發流程.md"),
    ("math", "數學模型規範", "數學模型規範.md"),
    ("docs", "數學文件規範", "數學文件規範.md"),
    ("submission", "送驗文件規範", "送驗文件規範.md"),
    ("sim", "模擬程式規範", "模擬程式規範.md"),
    ("demo", "Demogame規範", "Demogame規範.md"),
    ("script", "腳本規範", "腳本規範.md"),
    ("proposal", "提案報告規範", "提案報告規範.md"),
    ("stress", "壓測說明書", "壓測說明書.md"),
    ("backend", "後端報表筆記", "後端報表筆記.md"),
]

# 根 HTML 的頁籤分組：(大分類, [tab_id...])。一類多份文件時，左側導覽先列文件名。
# 新增文件時要同時加進 TABS 與這裡，漏加會在建置時報錯。
GROUPS = [
    ("總覽", ["overview"]),
    ("開發流程", ["flow"]),
    ("提案", ["proposal"]),
    ("數學設計", ["math"]),
    ("數學文件", ["docs"]),
    ("送驗相關", ["submission"]),
    ("系統相關", ["script", "stress", "backend"]),
    ("模擬程式＋Demogame", ["sim", "demo"]),
]

ROOT_OUTPUT_NAME = OUTPUT.name

# 其他產線：資料夾內的 .md 各自彙整成該資料夾的 HTML。
# (資料夾, 輸出檔名, 頁首名稱, 頁籤順序偏好)；資料夾內沒有 .md 時略過不產生。
PRODUCT_LINES = [
    ("Landbase", "landbase_specification.html", "Landbase 轉製 開發規範"),
    ("Reskin", "reskin_specification.html", "Reskin 開發規範"),
]
TAB_ORDER_HINT = ["導覽", "系統機制", "開發流程", "數學模型規範", "數學文件規範", "送驗文件規範", "送驗規範",
                  "模擬程式規範", "Demogame規範", "腳本規範", "提案報告規範", "壓測說明書", "後端報表筆記"]

# 目前正在建置的站台：md 相對路徑（如 md 內所寫、已去掉 ./）→ ("tab", tab_id) 或 ("ext", href)
LINKS: dict = {}

_used_ids = set()


def slugify(text: str) -> str:
    """GitHub 風格標題錨點：讓 md 內的 #章節 連結在 HTML 內也可跳轉。"""
    s = text.strip().lower()
    s = s.replace("`", "")
    s = re.sub(r"[^\w一-鿿぀-ヿ\- ]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = s or "section"
    slug = s
    n = 1
    while slug in _used_ids:
        n += 1
        slug = f"{s}-{n}"
    _used_ids.add(slug)
    return slug


def render_inline(text: str) -> str:
    """行內格式：先 escape，再處理 code span、粗體、連結。"""
    text = html.escape(text, quote=False)

    # code span（escape 後反引號仍在）
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # 粗體
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)

    # 連結：同站 .md 轉成頁籤切換（保留錨點）；他站 .md 轉成該站 HTML 的 #tab/anchor；其餘照常
    def link(m):
        label, href = m.group(1), m.group(2)
        base, _, anchor = href.partition("#")
        base = base.removeprefix("./")
        target = LINKS.get(base)
        if target and target[0] == "tab":
            extra = f' data-anchor="{anchor}"' if anchor else ""
            return (
                f'<a href="#" class="tab-link" data-tab="{target[1]}"{extra}>'
                f"{label}</a>"
            )
        if target and target[0] == "ext":
            href = target[1] + (f"/{anchor}" if anchor else "")
        return f'<a href="{href}">{label}</a>'

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)
    return text


class Renderer:
    def __init__(self, tab_id: str):
        self.tab_id = tab_id
        self.out = []
        self.toc = []  # (level, id, text)

    def render(self, md: str) -> str:
        lines = md.splitlines()
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                i += 1
                continue

            # 圍欄程式碼
            if stripped.startswith("```"):
                buf = []
                i += 1
                while i < n and not lines[i].strip().startswith("```"):
                    buf.append(lines[i])
                    i += 1
                i += 1  # 收尾 ```
                code = html.escape("\n".join(buf), quote=False)
                self.out.append(f"<pre><code>{code}</code></pre>")
                continue

            # 標題
            m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if m:
                level = len(m.group(1))
                text = m.group(2)
                # md 的「目錄」章節不輸出：HTML 已有左側目錄，避免重複
                if text.strip() == "目錄":
                    i += 1
                    while i < n and not re.match(r"^#{1,6}\s+", lines[i].strip()):
                        i += 1
                    continue
                hid = slugify(text)
                if 2 <= level <= 3:
                    self.toc.append((level, hid, text))
                self.out.append(
                    f'<h{level} id="{hid}">{render_inline(text)}</h{level}>'
                )
                i += 1
                continue

            # 分隔線
            if re.fullmatch(r"-{3,}", stripped):
                self.out.append("<hr>")
                i += 1
                continue

            # 表格
            if stripped.startswith("|") and i + 1 < n and re.match(
                r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]
            ):
                header = [c.strip() for c in stripped.strip("|").split("|")]
                aligns = []
                for cell in lines[i + 1].strip().strip("|").split("|"):
                    cell = cell.strip()
                    if cell.endswith(":") and cell.startswith(":"):
                        aligns.append("center")
                    elif cell.endswith(":"):
                        aligns.append("right")
                    else:
                        aligns.append("left")
                rows = []
                i += 2
                while i < n and lines[i].strip().startswith("|"):
                    rows.append(
                        [c.strip() for c in lines[i].strip().strip("|").split("|")]
                    )
                    i += 1
                def cell_cls(k):
                    a = aligns[k] if k < len(aligns) else "left"
                    return ' class="n"' if a in ("right", "center") else ""

                thead = "".join(
                    f"<th{cell_cls(k)}>{render_inline(c)}</th>"
                    for k, c in enumerate(header)
                )
                body = []
                for row in rows:
                    tds = "".join(
                        f"<td{cell_cls(k)}>{render_inline(c)}</td>"
                        for k, c in enumerate(row)
                    )
                    body.append(f"<tr>{tds}</tr>")
                self.out.append(
                    '<div class="tbl-wrap"><table><thead><tr>'
                    + thead
                    + "</tr></thead><tbody>"
                    + "".join(body)
                    + "</tbody></table></div>"
                )
                continue

            # 清單（無序／有序，含巢狀與核取方塊）
            if re.match(r"^\s*(-|\d+\.)\s+", line):
                block = []
                while i < n and (
                    re.match(r"^\s*(-|\d+\.)\s+", lines[i])
                    or (lines[i].strip() and re.match(r"^\s{2,}\S", lines[i]))
                ):
                    block.append(lines[i])
                    i += 1
                self.out.append(self.render_list(block))
                continue

            # 段落（合併連續行）
            buf = [stripped]
            i += 1
            while i < n and lines[i].strip() and not re.match(
                r"^(\s*(-|\d+\.)\s+|#{1,6}\s|```|\||-{3,}$)", lines[i].strip()
            ):
                buf.append(lines[i].strip())
                i += 1
            self.out.append(f"<p>{render_inline(' '.join(buf))}</p>")

        return "\n".join(self.out)

    def render_list(self, block):
        """遞迴處理縮排巢狀清單。"""
        items = []  # (marker, [own line, continuation lines...])
        base_indent = None
        for raw in block:
            m = re.match(r"^(\s*)(-|\d+\.)\s+(.*)$", raw)
            if m:
                indent = len(m.group(1))
                if base_indent is None:
                    base_indent = indent
                if indent <= base_indent:
                    items.append((m.group(2), [m.group(3)], []))
                    continue
            # 縮排更深：屬於前一項的子內容
            if items:
                items[-1][2].append(raw)

        ordered = items and items[0][0] != "-"
        tag = "ol" if ordered else "ul"
        parts = [f"<{tag}>"]
        for marker, own, children in items:
            text = " ".join(own)
            cb = ""
            m = re.match(r"^\[( |x|X)\]\s*(.*)$", text)
            cls = ""
            if m:
                checked = m.group(1).lower() == "x"
                cb = f'<span class="cb">{"☑" if checked else "☐"}</span> '
                text = m.group(2)
                cls = ' class="check"'
            inner = cb + render_inline(text)
            if children:
                inner += self.render_list(children)
            parts.append(f"<li{cls}>{inner}</li>")
        parts.append(f"</{tag}>")
        return "".join(parts)


def tab_id_for(stem: str) -> str:
    """產線資料夾內的 md 以檔名做頁籤 id：沿用根目錄同名文件的 id，否則取 slug。"""
    for tab_id, _, filename in TABS:
        if Path(filename).stem == stem:
            return tab_id
    return re.sub(r"[^\w\-]", "-", stem.lower()) or "doc"


def line_tabs(folder: Path):
    """列出產線資料夾的 md，依 TAB_ORDER_HINT 排序，其餘依檔名。"""
    mds = [p for p in folder.glob("*.md") if not p.name.startswith("_")]

    def key(p):
        stem = p.stem
        return (TAB_ORDER_HINT.index(stem) if stem in TAB_ORDER_HINT else 99, stem)

    return [(tab_id_for(p.stem), p.stem, p.name) for p in sorted(mds, key=key)]


def build_site(base: Path, tabs, output: Path, site_title: str, eyebrow: str, links: dict,
               groups=None):
    """把 base 下的 tabs（tab_id, 頁籤名稱, 檔名）彙整成一份 HTML。

    groups：[(大分類, [tab_id...])]；省略時每份文件自成一類。
    """
    global LINKS
    LINKS = links
    _used_ids.clear()
    title_of = {t: title for t, title, _ in tabs}
    if groups is None:
        groups = [(title, [t]) for t, title, _ in tabs]
    grouped = [t for _g, ids in groups for t in ids]
    missing = [t for t in title_of if t not in grouped]
    unknown = [t for t in grouped if t not in title_of]
    assert not missing and not unknown, f"GROUPS 與 TABS 不一致：缺 {missing}、多 {unknown}"
    group_of = {t: ids for _g, ids in groups for t in ids}

    panels, toc_items = [], {}
    first_tab = groups[0][1][0]
    for tab_id, title, filename in tabs:
        md = (base / filename).read_text(encoding="utf-8")
        r = Renderer(tab_id)
        body = r.render(md)
        toc_items[tab_id] = "".join(
            f'<a class="toc-{lvl}" href="#{hid}" data-tab="{tab_id}">{html.escape(text)}</a>'
            for lvl, hid, text in r.toc
        )
        panels.append(
            f'<section class="panel" role="tabpanel" id="panel-{tab_id}"'
            f'{"" if tab_id == first_tab else " hidden"}>{body}</section>'
        )

    tocs = []
    for tab_id, _title, _f in tabs:
        ids = group_of[tab_id]
        if len(ids) > 1:   # 一類多份文件：列文件名，目前這份底下展開章節
            inner = "".join(
                f'<a href="#" class="tab-link toc-doc{" on" if t == tab_id else ""}" data-tab="{t}">'
                f'{html.escape(title_of[t])}</a>' + (toc_items[t] if t == tab_id else "")
                for t in ids)
        else:
            inner = toc_items[tab_id]
        tocs.append(f'<nav class="toc" id="toc-{tab_id}"'
                    f'{"" if tab_id == first_tab else " hidden"}>{inner}</nav>')

    tabs_html = []
    for gi, (gname, ids) in enumerate(groups):
        first = gi == 0
        tabs_html.append(
            f'<button class="tab" role="tab" id="tab-g{gi}" data-tab="{ids[0]}" '
            f'data-tabs="{",".join(ids)}" aria-selected="{"true" if first else "false"}" '
            f'tabindex="{0 if first else -1}">{gname}</button>'
        )

    today = date.today().strftime("%Y-%m-%d")
    src_label = f"專案需知/{base.relative_to(HERE)}/*.md".replace("/./", "/")
    page = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{site_title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=Noto+Sans+TC:wght@400;500;700&display=swap">
<style>
:root{{
  --surface:#fcfcfb; --panel:#ffffff; --panel-2:#f6f7f8;
  --ink:#101418; --ink-2:#4a5462; --ink-3:#7d8794;
  --rule:#e3e6ea; --grid:#edf0f3;
  --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a;
  --font-sans:'IBM Plex Sans','Noto Sans TC',system-ui,-apple-system,'Segoe UI',sans-serif;
  --font-mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Consolas,monospace;
}}
@media (prefers-color-scheme:dark){{
  :root:where(:not([data-theme="light"])){{
    --surface:#1a1a19; --panel:#212223; --panel-2:#1e1f20;
    --ink:#f3f3f1; --ink-2:#b4b8be; --ink-3:#868c95;
    --rule:#33353a; --grid:#2a2c30;
    --s1:#3987e5; --s2:#d95926; --s3:#199e70;
  }}
}}
:root[data-theme="dark"]{{
  --surface:#1a1a19; --panel:#212223; --panel-2:#1e1f20;
  --ink:#f3f3f1; --ink-2:#b4b8be; --ink-3:#868c95;
  --rule:#33353a; --grid:#2a2c30;
  --s1:#3987e5; --s2:#d95926; --s3:#199e70;
}}
*{{box-sizing:border-box}}
body{{margin:0; background:var(--surface); color:var(--ink);
  font-family:var(--font-sans); font-size:15px; line-height:1.65; -webkit-font-smoothing:antialiased}}
.wrap{{max-width:1200px; margin:0 auto; padding:38px 22px 80px}}
header.page{{display:flex; flex-direction:column; gap:9px; padding-bottom:20px}}
.eyebrow{{font-family:var(--font-mono); font-size:11.5px; letter-spacing:.14em; text-transform:uppercase; color:var(--ink-3)}}
h1.site{{margin:0; font-size:32px; font-weight:600; letter-spacing:-.02em}}
.meta{{margin:0; color:var(--ink-2); font-size:13.5px}}
.meta code{{font-family:var(--font-mono); font-size:12.5px}}
/* overflow-y 必須釘死：只設 overflow-x:auto 時 overflow-y 會算成 auto，
   頁簽的 -1px margin 會製造 1px 垂直溢出 -> 冒出多餘滾動條 */
.tabs{{display:flex; gap:3px; border-bottom:1px solid var(--rule);
  overflow-x:auto; overflow-y:hidden;
  scrollbar-width:none; -ms-overflow-style:none;   /* 藏拉條，仍可橫向捲動（滾輪／觸控板／拖曳） */
  position:sticky; top:0; background:var(--surface); z-index:20; padding-top:6px}}
.tabs::-webkit-scrollbar{{display:none}}
.tab{{appearance:none; font:inherit; font-size:13.5px; color:var(--ink-2); cursor:pointer;
  background:transparent; border:1px solid transparent; border-bottom:none; margin-bottom:-1px;
  padding:9px 17px; border-radius:3px 3px 0 0; white-space:nowrap; transition:color .12s,background .12s}}
.tab:hover{{color:var(--ink); background:var(--panel-2)}}
.tab[aria-selected="true"]{{color:var(--s1); font-weight:600; background:var(--panel);
  border-color:var(--rule); border-bottom-color:var(--panel)}}
.tab:focus-visible{{outline:2px solid var(--s1); outline-offset:-2px}}
.body-row{{display:flex; gap:30px; align-items:flex-start; padding-top:26px}}
.toc{{position:sticky; top:52px; width:236px; flex:none;
  max-height:calc(100vh - 76px); overflow-y:auto;
  font-size:12.5px; line-height:1.5; padding:6px 8px 6px 0}}
.toc[hidden]{{display:none}}
.toc a{{display:block; color:var(--ink-3); text-decoration:none;
  padding:3px 11px; border-left:2px solid var(--rule)}}
.toc a:hover{{color:var(--s1); border-left-color:var(--s1)}}
.toc a.toc-3{{padding-left:25px}}
.toc a.toc-doc{{color:var(--ink); font-weight:600; border-left-color:transparent; padding:7px 11px 3px}}
.toc a.toc-doc:not(:first-child){{margin-top:8px}}
.toc a.toc-doc.on{{color:var(--s1)}}
main{{flex:1; min-width:0}}
.panel[hidden]{{display:none}}
.panel h1{{margin:0 0 14px; font-size:24px; font-weight:600; letter-spacing:-.015em}}
h2{{margin:34px 0 12px; font-size:19px; font-weight:600; letter-spacing:-.01em;
  padding-bottom:7px; border-bottom:1px solid var(--rule)}}
h3{{margin:28px 0 10px; font-size:16.5px; font-weight:600; letter-spacing:-.008em}}
h4{{margin:24px 0 8px; font-size:14.5px; font-weight:600; color:var(--ink-2)}}
p{{margin:0 0 11px; max-width:86ch}}
ul,ol{{margin:0 0 13px; padding-left:22px; max-width:86ch}}
li{{margin:3px 0}}
li.check{{list-style:none; margin-left:-20px}}
.cb{{color:var(--s1); margin-right:4px}}
code{{font-family:var(--font-mono); font-size:.88em; background:var(--panel-2);
  border:1px solid var(--rule); border-radius:3px; padding:1px 4px}}
pre{{background:var(--panel-2); border:1px solid var(--rule); border-radius:3px;
  padding:13px 16px; overflow-x:auto; margin:0 0 16px;
  font-family:var(--font-mono); font-size:12.5px; line-height:1.6}}
pre code{{background:none; border:none; padding:0; font-size:inherit}}
strong{{font-weight:600; color:var(--ink)}}
a{{color:var(--s1)}}
.tbl-wrap{{overflow-x:auto; overflow-y:hidden; border:1px solid var(--rule); border-radius:3px;
  background:var(--panel); margin:0 0 18px}}
table{{border-collapse:collapse; width:100%; font-size:13px}}
th,td{{padding:7px 12px; text-align:left; border-bottom:1px solid var(--grid); vertical-align:top}}
th{{background:var(--panel-2); color:var(--ink-2); font-weight:500; font-size:11.5px;
  letter-spacing:.03em; white-space:nowrap}}
td.n,th.n{{text-align:right; white-space:nowrap; font-family:var(--font-mono);
  font-variant-numeric:tabular-nums; font-size:12px}}
tbody tr:last-child td{{border-bottom:none}}
tbody tr:hover{{background:var(--panel-2)}}
hr{{border:none; border-top:1px solid var(--rule); margin:34px 0}}
@media (max-width:900px){{
  .body-row{{flex-direction:column; gap:14px}}
  .toc{{display:none!important}}
  .toc:not([hidden]):has(.toc-doc){{display:flex!important; position:static; width:auto; max-height:none;
    flex-wrap:wrap; gap:4px 16px; padding:0}}
  .toc a:not(.toc-doc){{display:none}}
  .toc a.toc-doc{{padding:0; margin:0!important}}
}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style>
</head>
<body>
<div class="wrap">
<header class="page">
  <div class="eyebrow">{eyebrow}</div>
  <h1 class="site">{site_title}</h1>
  <p class="meta">由 <code>{src_label}</code> 產生（<code>_build_html.py</code>）　|　{today}</p>
</header>
<div class="tabs" role="tablist" aria-label="規範文件">{''.join(tabs_html)}</div>
<div class="body-row">
  {''.join(tocs)}
  <main>{''.join(panels)}</main>
</div>
</div>
<script>
var TAB_IDS = {[t[0] for t in tabs]!r};
var LAST = {{}};
function activate(tabId, anchor) {{
  document.querySelectorAll('.tab').forEach(function(b) {{
    var on = b.dataset.tabs.split(',').indexOf(tabId) >= 0;
    if (on) LAST[b.id] = tabId;
    b.setAttribute('aria-selected', on ? 'true' : 'false');
    b.tabIndex = on ? 0 : -1;
    if (on && b.scrollIntoView) b.scrollIntoView({{ block: 'nearest', inline: 'nearest' }});
  }});
  document.querySelectorAll('.panel').forEach(function(p) {{
    p.hidden = (p.id !== 'panel-' + tabId);
  }});
  document.querySelectorAll('.toc').forEach(function(t) {{
    t.hidden = (t.id !== 'toc-' + tabId);
  }});
  if (anchor) {{
    var el = document.getElementById(anchor);
    if (el) el.scrollIntoView();
  }} else {{
    window.scrollTo(0, 0);
  }}
}}
document.querySelectorAll('.tab').forEach(function(b) {{
  b.addEventListener('click', function() {{ activate(LAST[b.id] || b.dataset.tab); }});
}});
(function() {{
  var bar = document.querySelector('.tabs');
  bar.addEventListener('wheel', function(e) {{
    if (Math.abs(e.deltaY) > Math.abs(e.deltaX) && bar.scrollWidth > bar.clientWidth) {{
      bar.scrollLeft += e.deltaY;
      e.preventDefault();
    }}
  }}, {{ passive: false }});
}})();
(function() {{
  var h = decodeURIComponent(location.hash.slice(1));
  if (!h) return;
  var tab = h.split('/')[0], anchor = h.split('/').slice(1).join('/');
  if (TAB_IDS.indexOf(tab) >= 0) activate(tab, anchor || null);
}})();
document.addEventListener('click', function(e) {{
  var a = e.target.closest('a');
  if (!a) return;
  if (a.classList.contains('tab-link')) {{
    e.preventDefault();
    activate(a.dataset.tab, a.dataset.anchor || null);
  }} else if (a.getAttribute('href') && a.getAttribute('href')[0] === '#') {{
    var id = a.getAttribute('href').slice(1);
    var el = document.getElementById(id);
    if (!el) return;
    e.preventDefault();
    var panel = el.closest('.panel');
    activate(a.dataset.tab || (panel ? panel.id.slice(6) : null) || 'overview', id);
  }}
}});
</script>
</body>
</html>
"""
    output.write_text(page, encoding="utf-8")
    print(f"OK: {output.relative_to(HERE)} 已更新（{output.stat().st_size:,} bytes）")


def build():
    # 根目錄（Omniplay）：根 .md 互連為頁籤；連到產線資料夾的 .md 轉成該產線 HTML
    links = {filename: ("tab", tab_id) for tab_id, _, filename in TABS}
    links["_README.md"] = ("tab", "overview")  # 根 .md 內仍以 _README.md 連到總覽
    for folder, out_name, _ in PRODUCT_LINES:
        for tab_id, _, filename in line_tabs(HERE / folder):
            links[f"{folder}/{filename}"] = ("ext", f"{folder}/{out_name}#{tab_id}")
    build_site(HERE, TABS, OUTPUT, "iGaming 開發規範", "iGaming · 開發規範", links, GROUPS)

    # 各產線：資料夾內 .md 互連為頁籤；連回根目錄 .md 轉成根 HTML 的頁籤
    for folder, out_name, site_title in PRODUCT_LINES:
        tabs = line_tabs(HERE / folder)
        if not tabs:
            continue
        links = {filename: ("tab", tab_id) for tab_id, _, filename in tabs}
        for tab_id, _, filename in TABS:
            links[f"../{filename}"] = ("ext", f"../{ROOT_OUTPUT_NAME}#{tab_id}")
        links["../其他/_README.md"] = ("ext", f"../{ROOT_OUTPUT_NAME}#overview")
        build_site(HERE / folder, tabs, HERE / folder / out_name, site_title,
                   f"Slots · {folder}", links)


if __name__ == "__main__":
    build()
