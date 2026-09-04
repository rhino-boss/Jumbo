# -*- coding: utf-8 -*-
"""將 Slots/規範/ 的 Markdown 規範彙整成單一 slot_development_specification.html。

用法（在本資料夾執行）：
    py _build_html.py

規則：任何一份 .md 更新後，必須重跑本腳本同步更新 HTML。
不依賴第三方套件，只支援本規範集實際使用的 Markdown 子集：
標題、表格、圍欄程式碼、清單（含巢狀與核取方塊）、粗體、行內程式碼、連結、分隔線。
"""

import html
import re
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
OUTPUT = HERE / "slot_development_specification.html"

# (tab_id, 頁籤名稱, 檔名)
TABS = [
    ("overview", "總覽", "_README.md"),
    ("flow", "開發流程", "開發流程.md"),
    ("math", "數學模型規範", "數學模型規範.md"),
    ("docs", "數學文件規範", "數學文件規範.md"),
    ("sim", "模擬程式規範", "模擬程式規範.md"),
    ("demo", "Demogame規範", "Demogame規範.md"),
]

MD_TO_TAB = {filename: tab_id for tab_id, _, filename in TABS}

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

    # 連結：.md 連結轉成頁籤切換（保留錨點），其餘照常
    def link(m):
        label, href = m.group(1), m.group(2)
        base, _, anchor = href.partition("#")
        base = base.removeprefix("./")
        if base in MD_TO_TAB:
            extra = f' data-anchor="{anchor}"' if anchor else ""
            return (
                f'<a href="#" class="tab-link" data-tab="{MD_TO_TAB[base]}"{extra}>'
                f"{label}</a>"
            )
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


def build():
    panels = []
    tabs_html = []
    tocs = []
    for idx, (tab_id, title, filename) in enumerate(TABS):
        md = (HERE / filename).read_text(encoding="utf-8")
        r = Renderer(tab_id)
        body = r.render(md)
        toc_items = "".join(
            f'<a class="toc-{lvl}" href="#{hid}" data-tab="{tab_id}">{html.escape(text)}</a>'
            for lvl, hid, text in r.toc
        )
        first = idx == 0
        tocs.append(
            f'<nav class="toc" id="toc-{tab_id}"{"" if first else " hidden"}>{toc_items}</nav>'
        )
        panels.append(
            f'<section class="panel" role="tabpanel" id="panel-{tab_id}" '
            f'aria-labelledby="tab-{tab_id}"{"" if first else " hidden"}>{body}</section>'
        )
        tabs_html.append(
            f'<button class="tab" role="tab" id="tab-{tab_id}" data-tab="{tab_id}" '
            f'aria-controls="panel-{tab_id}" aria-selected="{"true" if first else "false"}" '
            f'tabindex="{0 if first else -1}">{title}</button>'
        )

    today = date.today().strftime("%Y-%m-%d")
    page = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Slot 開發規範</title>
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
  position:sticky; top:0; background:var(--surface); z-index:20; padding-top:6px}}
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
@media (max-width:900px){{ .toc{{display:none!important}} }}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style>
</head>
<body>
<div class="wrap">
<header class="page">
  <div class="eyebrow">Slots · 開發規範</div>
  <h1 class="site">Slot 開發規範</h1>
  <p class="meta">由 <code>Slots/規範/*.md</code> 產生（<code>_build_html.py</code>）　|　{today}</p>
</header>
<div class="tabs" role="tablist" aria-label="規範文件">{''.join(tabs_html)}</div>
<div class="body-row">
  {''.join(tocs)}
  <main>{''.join(panels)}</main>
</div>
</div>
<script>
var TAB_IDS = {[t[0] for t in TABS]!r};
function activate(tabId, anchor) {{
  document.querySelectorAll('.tab').forEach(function(b) {{
    var on = b.dataset.tab === tabId;
    b.setAttribute('aria-selected', on ? 'true' : 'false');
    b.tabIndex = on ? 0 : -1;
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
  b.addEventListener('click', function() {{ activate(b.dataset.tab); }});
}});
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
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"OK: {OUTPUT.name} 已更新（{OUTPUT.stat().st_size:,} bytes）")


if __name__ == "__main__":
    build()
