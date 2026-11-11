# -*- coding: utf-8 -*-
"""將 專案需知/ 的 Markdown 文件彙整成三個產線網頁（Omniplay／Landbase／Reskin）、Mine 與開發流程網頁，
再產生最外層入口 igaming_specification.html 切換。

本腳本放在 專案需知/其他/；三產線的 md 各在 開發規範/Omniplay/、Landbase/、Reskin/；
Mine（自己用、不同步出去）的 md 直接放 開發規範/；開發流程的 md 在 開發流程/；
所有網頁（含入口）都輸出到 專案需知/ 最外層。

用法（在 其他/ 內執行）：
    py _build_html.py

規則：任何一份 .md 更新後，必須重跑本腳本同步更新 HTML。
不依賴第三方套件，只支援本規範集實際使用的 Markdown 子集：
標題、表格、圍欄程式碼、清單（含巢狀與核取方塊）、粗體、行內程式碼、連結、分隔線。
"""

import html
import os
import re
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent.parent  # 專案需知/
SPEC_DIR = "開發規範"  # 三產線（Omniplay／Landbase／Reskin）資料夾的上層；Mine 的 md 直接放這層
OMNI_FILE = "omniplay_specification.html"
HUB_NAME = "igaming_specification.html"     # 最外層入口：三產線＋Mine＋開發流程切換
# 不同步出去的站：(key, 按鈕名稱, tab_id, 輸出檔名, 頁首名稱, 分組)；分組見下方 MINE_GROUPS／FLOW_GROUPS／ERRORS_GROUPS
MINE_TAB_IDS = ["overview", "outputs", "gamerule", "sim", "demo", "proposal", "report", "demoreport"]
FLOW_TAB_IDS = ["flow"]
ERRORS_TAB_IDS = ["errors"]
SPS_TAB_IDS = ["sps_oldhand"]   # 對外規格（給 SPS 實作）：獨立網頁，不併入 Omniplay 站

# (tab_id, 頁籤名稱, 檔名：相對 專案需知/)
TABS = [
    ("guide", "總覽", "開發規範/Omniplay/導覽.md"),
    ("overview", "總覽", "其他/_README.md"),
    ("gamerule", "GameRule規範", "開發規範/GameRule規範.md"),
    ("report", "數值報告規範", "開發規範/數值報告規範.md"),
    ("demoreport", "Demo報告規範", "開發規範/Demo報告規範.md"),
    ("knowhow", "Knowhow", "開發規範/Omniplay/Knowhow.md"),
    ("flow", "開發流程", "開發流程/開發流程.md"),
    ("outputs", "產出與紀錄規範", "開發規範/產出與紀錄規範.md"),
    ("errors", "錯誤清單", "開發規範/錯誤清單.md"),
    ("math", "數學模型規範", "開發規範/Omniplay/數學模型規範.md"),
    ("docs", "數學文件規範", "開發規範/Omniplay/數學文件規範.md"),
    ("submission", "送驗文件規範", "開發規範/Omniplay/送驗文件規範.md"),
    ("sim", "模擬程式規範", "開發規範/模擬程式規範.md"),
    ("demo", "Demogame規範", "開發規範/Demogame規範.md"),
    ("script", "腳本規範", "開發規範/Omniplay/腳本規範.md"),
    ("proposal", "提案報告規範", "開發規範/提案報告規範.md"),
    ("stress", "壓測說明書", "開發規範/Omniplay/壓測說明書.md"),
    ("backend", "後端報表", "開發規範/Omniplay/後端報表.md"),
    ("ceiling", "天花板說明", "開發規範/Omniplay/天花板說明.md"),
    ("mechanism", "系統機制", "開發規範/Omniplay/機制說明.md"),
    ("sps_oldhand", "老手救援 C-2版", "開發規範/Omniplay/老手救援實作規格.md"),
]

# 根 HTML 的頁籤分組：(大分類, [tab_id...])。一類多份文件時，左側導覽先列文件名。
# 新增文件時要同時加進 TABS 與這裡，漏加會在建置時報錯。
GROUPS = [
    ("總覽", ["guide"]),
    ("Knowhow", ["knowhow"]),
    ("系統相關", ["mechanism", "ceiling", "script", "stress", "backend"]),
    ("數學設計", ["math"]),
    ("數學文件", ["docs"]),
    ("送驗相關", ["submission"]),
]
# Mine 網頁的頁籤分組
MINE_GROUPS = [
    ("總覽", ["overview"]),
    ("產出與紀錄", ["outputs"]),
    ("遊戲製作", ["gamerule", "sim", "demo"]),
    ("報告", ["proposal", "report", "demoreport"]),
]
# 開發流程網頁的頁籤分組
FLOW_GROUPS = [("開發流程", ["flow"])]
# 錯誤紀錄網頁的頁籤分組
ERRORS_GROUPS = [("錯誤紀錄", ["errors"])]
# 對外規格網頁的頁籤分組
SPS_GROUPS = [("系統相關", ["sps_oldhand"])]
# 不同步出去的站
PRIVATE_SITES = [
    ("mine", "開發規範", MINE_TAB_IDS, "mine_specification.html", "開發規範", MINE_GROUPS),
    ("flow", "開發流程", FLOW_TAB_IDS, "development_process.html", "開發流程", FLOW_GROUPS),
    ("errors", "錯誤紀錄", ERRORS_TAB_IDS, "error_list.html", "錯誤紀錄", ERRORS_GROUPS),
    ("sps", "老手救援 C-2版", SPS_TAB_IDS, "oldhand_rescue_spec.html", "老手救援 C-2版", SPS_GROUPS),
]
# 不另存 HTML、整頁內嵌在入口裡的站（只在 igaming_specification.html 看）
EMBED_KEYS = {"mine", "errors"}
# 入口左側導覽：(大標, [站 key...])，大標下列各站；沒列到的站歸最後一個大標
HUB_SECTIONS = [("我的製程", ["mine", "flow", "errors"]), ("產線須知", ["omniplay", "landbase", "reskin"]), ("對外規格", ["sps"])]
HUB_ORDER = [k for _t, ks in HUB_SECTIONS for k in ks]

# 頁籤 icon（線條圖示，顏色跟著文字）；HIGHLIGHT_GROUPS 的文字另用黃色標示
_SVG = ('<svg class="tab-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>')
HIGHLIGHT_GROUPS: set[str] = set()  # 頁籤不另標顏色（2026-10-20 使用者指示）
GROUP_ICONS = {
    # 總覽：首頁
    "總覽": _SVG.format('<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/>'),
    # Knowhow：燈泡
    "Knowhow": _SVG.format('<path d="M9 18h6"/><path d="M10 21h4"/>'
                           '<path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>'),
    # 開發流程：分支流程
    "開發流程": _SVG.format('<circle cx="6" cy="5" r="2"/><circle cx="6" cy="19" r="2"/>'
                            '<circle cx="18" cy="12" r="2"/><path d="M6 7v10"/><path d="M6 12h4a4 4 0 0 0 4-4V7"/>'
                            '<path d="M16 12h-2"/>'),
    # 報告：簡報
    "報告": _SVG.format('<rect x="3" y="4" width="18" height="12" rx="1"/><path d="M12 16v4"/><path d="M8 20h8"/>'),
    # 產出與紀錄：清單
    "產出與紀錄": _SVG.format('<path d="M9 6h11"/><path d="M9 12h11"/><path d="M9 18h11"/>'
                              '<path d="M4 6l1 1 2-2"/><path d="M4 12l1 1 2-2"/><path d="M4 18l1 1 2-2"/>'),
    # 遊戲製作：規則書
    "遊戲製作": _SVG.format('<path d="M4 4h10a4 4 0 0 1 4 4v12H8a4 4 0 0 1-4-4z"/><path d="M8 9h6"/><path d="M8 13h6"/>'),
    # 數學文件：文件
    "數學文件": _SVG.format('<path d="M14 3H6v18h12V7z"/><path d="M14 3v4h4"/><path d="M9 12h6"/><path d="M9 16h6"/>'),
    # 送驗相關：盾牌勾選
    "送驗相關": _SVG.format('<path d="M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6z"/><path d="M9 12l2 2 4-4"/>'),
    # 模擬程式＋Demogame：播放
    "模擬程式＋Demogame": _SVG.format('<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M10 9l5 3-5 3z"/>'),
    # 數學設計：Σ
    "數學設計": _SVG.format('<path d="M18 4H6l6 8-6 8h12"/>'),
    # 系統相關：齒輪
    "系統相關": _SVG.format(
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 '
        '1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1'
        'a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1'
        'a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 '
        '1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3'
        'l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4'
        'h-.1a1.7 1.7 0 0 0-1.5 1z"/>'),
}

ROOT_TITLE = "Omniplay 開發規範"

# 其他產線：開發規範/<資料夾> 內的 .md 各自彙整成一份 HTML（輸出到 專案需知/ 最外層）。
# (資料夾, 輸出檔名, 頁首名稱, 頁籤順序偏好)；資料夾內沒有 .md 時略過不產生。
PRODUCT_LINES = [
    ("Landbase", "landbase_specification.html", "Landbase 轉製 開發規範"),
    ("Reskin", "reskin_specification.html", "Reskin 開發規範"),
]
# 產線站直接沿用 Omniplay 的文件（不另寫 md）：{產線資料夾: [Omniplay tab_id...]}
# 目前不共用：各產線只放自己的文件與數值（三站分屬不同團隊，不得看到彼此的設定）
SHARED_TABS = {}

# 產線資料夾的 md（檔名）歸入與 Omniplay 相同的頁籤大分類，標題、icon、顏色、順序三站一致
LINE_GROUP_OF = {
    "導覽": "總覽", "Knowhow": "Knowhow", "開發流程": "開發流程", "提案報告規範": "報告", "產出與紀錄規範": "產出與紀錄",
    "數學模型規範": "數學設計", "數學文件規範": "數學文件", "送驗文件規範": "送驗相關", "送驗規範": "送驗相關",
    "系統機制": "系統相關", "機制說明": "系統相關", "天花板說明": "系統相關", "腳本規範": "系統相關",
    "壓測說明書": "系統相關", "後端報表": "系統相關", "模擬程式規範": "模擬程式＋Demogame",
    "Demogame規範": "模擬程式＋Demogame",
}

# 團隊版（Omniplay 團隊）：只放 Omniplay 站的規範，發佈到共享資料夾（Mine、開發流程、其他產線都不外放）
TEAM_DIR = Path(r"\\192.168.139.6\Simulate\專案需知")
TEAM_TAB_IDS = ["guide", "knowhow", "math", "docs", "submission", "mechanism", "ceiling", "script", "stress"]
TEAM_GROUPS = [
    ("總覽", ["guide"]),
    ("Knowhow", ["knowhow"]),
    ("系統相關", ["mechanism", "ceiling", "script", "stress"]),
    ("數學設計", ["math"]),
    ("數學文件", ["docs"]),
    ("送驗相關", ["submission"]),
]
TEAM_TOOLS = ["其他/_check_xlsx_style.py"]
PLAIN_UNKNOWN_MD = False                      # 團隊版：連到未發佈文件的 .md 連結只留文字

# 相對連結一律以 md 所在資料夾解析（總覽 _README*.md 的慣例是相對 專案需知/ 根目錄），
# 解析後是規範文件就轉成頁籤／他站，否則換算成相對輸出 HTML 的路徑
TREE_ROOT: Path = HERE
MD_DIR: Path = HERE
OUT_DIR: Path = HERE
# 各站只能連自己站內的頁籤：連到其他站或其他檔案的連結只留文字
LOCAL_ONLY = False

# 目前正在建置的站台：規範 md（相對 專案需知/ 的路徑）→ ("tab", tab_id) 或 ("ext", href)
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
    # 可調參數：{{數值}} → 後端可調整的參數標記
    text = re.sub(r"\{\{(.+?)\}\}", r'<span class="tune">\1</span>', text)
    # 粗體
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    # 警示標記：==數值== 標黃（超過目標）、!!數值!! 標紅（超過 100%）
    text = re.sub(r"!!(.+?)!!", r'<mark class="hl-danger">\1</mark>', text)
    text = re.sub(r"==(.+?)==", r'<mark class="hl-warn">\1</mark>', text)

    # 連結：同站 .md 轉成頁籤切換（保留錨點）；他站 .md 轉成該站 HTML 的 #tab/anchor；其餘照常
    def link(m):
        label, href = m.group(1), m.group(2)
        base, _, anchor = href.partition("#")
        target = None
        relative = base and not re.match(r"^([a-z]+:|#|/)", href)
        if relative:
            resolved = os.path.normpath(MD_DIR / base)
            target = LINKS.get(Path(os.path.relpath(resolved, TREE_ROOT)).as_posix())
        if target and target[0] == "tab":
            extra = f' data-anchor="{anchor}"' if anchor else ""
            return (
                f'<a href="#" class="tab-link" data-tab="{target[1]}"{extra}>'
                f"{label}</a>"
            )
        if LOCAL_ONLY and relative:
            return label
        if target and target[0] == "ext":
            href = target[1] + (f"/{anchor}" if anchor else "")
        elif PLAIN_UNKNOWN_MD and ".md" in base and not href.startswith("http"):
            return label
        elif relative:
            href = Path(os.path.relpath(resolved, OUT_DIR)).as_posix() + (f"#{anchor}" if anchor else "")
        return f'<a href="{href}">{label}</a>'

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)
    return trim_inline_margins(text)


# 行內元素（粗體、code、連結…）左右各留 .3em 與文字隔開；
# 但在段落開頭／結尾或緊鄰全形標點時不留，避免內容開頭出現空白、標點旁多一格。
CJK_PUNCT = set("，。、；：！？（）「」『』【】《》〈〉…／～　")
INLINE_ELEMENT = re.compile(r'<(strong|code|mark|a|span)\b([^>]*)>.*?</\1>', re.S)


def trim_inline_margins(text: str) -> str:
    def visible(s):
        return re.sub(r"<[^>]+>", "", s)

    def tag(m):
        before = visible(text[:m.start()]).rstrip(" ")
        after = visible(text[m.end():]).lstrip(" ")
        inner = visible(m.group(0)).strip(" ")
        classes = []
        if not before or before[-1] in CJK_PUNCT or inner[:1] in CJK_PUNCT:
            classes.append("nl")
        if not after or after[0] in CJK_PUNCT or inner[-1:] in CJK_PUNCT:
            classes.append("nr")
        if not classes:
            return m.group(0)
        name, attrs = m.group(1), m.group(2)
        if 'class="' in attrs:
            attrs = attrs.replace('class="', f'class="{" ".join(classes)} ', 1)
        else:
            attrs += f' class="{" ".join(classes)}"'
        return f"<{name}{attrs}>" + m.group(0)[len(f"<{name}{m.group(2)}>"):]

    return INLINE_ELEMENT.sub(tag, text)


def render_timeline(lines) -> str:
    """依轉數比例畫時間軸。

    scale: 0@0, 200@34, 1000@92, 1100@100   轉數→橫向位置（%）的分段對應，可放大前段
    ticks: 1, 41, 60, 200, 1,000             軸上要標的轉數（逗號後要有空白）
    軌道名稱 :: 起-迄, 起-迄 :: 文字 :: 樣式 || 下一個項目 ...
      同一項目可列多個區間（重複事件畫在各自位置，文字只寫一次）；樣式 phase／phase2／event／stop。
      event 可加顏色 s1～s4（例 `event s3`）：文字標在上方（`名稱 | 區間` 分兩行），同一項目的區間用淡色底帶連起來，
      只有第一個區間的起點畫虛線到轉數軸。
    periods: 新手期 1-200 s4, 老手期 201-1100 s1   轉數軸下方的時期色帶（名稱 起-迄 顏色）
    """
    scale, ticks, lanes, periods = [(0.0, 0.0), (1000.0, 100.0)], [], [], []

    def num(t):
        return float(t.replace(",", "").strip())

    for raw in lines:
        text = raw.strip()
        if not text:
            continue
        if text.startswith("scale:"):
            scale = [(num(a), float(b)) for a, b in (x.split("@") for x in re.split(r",\s+", text[6:].strip()))]
            continue
        if text.startswith("ticks:"):
            ticks = [x.strip() for x in re.split(r",\s+", text[6:].strip())]
            continue
        if text.startswith("periods:"):
            for x in re.split(r",\s+", text[8:].strip()):
                pname, prng, pcolor = x.split()
                lo, _, hi = prng.partition("-")
                periods.append((pname, num(lo), num(hi), pcolor))
            continue
        name, _, rest = text.partition("::")
        items = []
        for chunk in rest.split("||"):
            parts = [x.strip() for x in chunk.split("::")]
            spans = []
            for rng in re.split(r",\s+", parts[0]):
                lo, _, hi = rng.partition("-")
                spans.append((num(lo), num(hi or lo)))
            items.append((spans, parts[1] if len(parts) > 1 else "", parts[2] if len(parts) > 2 else "event"))
        lanes.append((name.strip(), items))

    def pos(spin):
        for (x0, p0), (x1, p1) in zip(scale, scale[1:]):
            if spin <= x1:
                return p0 + (p1 - p0) * (spin - x0) / (x1 - x0)
        return scale[-1][1]

    # 軌道高度（px，與 CSS .tl-track 一致；沒有事件的列 36、其餘 60，各含 1px 底線），用來畫事件起點到轉數軸的虛線
    is_event = lambda kind: kind.split()[0] == "event"
    short = [not any(is_event(kind) for _, _, kind in items) for _, items in lanes]
    heights = [36 if s else 78 for s in short]
    band_bottom = 64  # .tl-band top 46 + height 18
    out = ['<div class="tl-wrap"><div class="tl">']
    for row, (name, items) in enumerate(lanes):
        track = "tl-track short" if short[row] else "tl-track"
        out.append(f'<div class="tl-row"><div class="tl-lane">{render_inline(name)}</div><div class="{track}">')
        guide = heights[row] - band_bottom + 1 + sum(h + 1 for h in heights[row + 1:])
        for spans, label, kind in items:
            if not is_event(kind):
                for lo, hi in spans:
                    left = pos(lo - 1)
                    width = max(pos(hi) - left, 0.6)
                    out.append(f'<div class="tl-bar {kind}" style="left:{left:.2f}%;width:{width:.2f}%">{render_inline(label)}</div>')
                continue
            color = kind.split()[1] if len(kind.split()) > 1 else "s2"
            start, end = pos(spans[0][0] - 1), pos(spans[-1][1])
            out.append(f'<div class="tl-group" style="--c:var(--{color})">')
            # 每個區間起點都畫虛線到轉數軸；只有一個區間時（例：41～60 轉）起迄兩端都畫
            marks = [pos(lo - 1) for lo, _ in spans] + ([pos(spans[0][1])] if len(spans) == 1 else [])
            for x in marks:
                out.append(f'<div class="tl-guide" style="left:{x:.2f}%;height:{guide}px"></div>')
            out.append(f'<div class="tl-band" style="left:{start:.2f}%;width:{max(end - start, 0.6):.2f}%"></div>')
            for lo, hi in spans:
                left = pos(lo - 1)
                out.append(f'<div class="tl-bar event" style="left:{left:.2f}%;width:{max(pos(hi) - left, 0.6):.2f}%"></div>')
            if label:
                name_part, _, range_part = label.partition(" | ")
                sub = f'<span class="tl-range">{render_inline(range_part)}</span>' if range_part else ""
                out.append(f'<div class="tl-label" style="left:{start:.2f}%">{render_inline(name_part)}{sub}</div>')
            out.append("</div>")
        out.append("</div></div>")
    dense = " dense" if len(ticks) > 12 else ""
    out.append(f'<div class="tl-row"><div class="tl-lane tl-axis-name">轉數</div><div class="tl-track tl-axis{dense}">')
    for t in ticks:
        out.append(f'<div class="tl-tick" style="left:{pos(num(t)):.2f}%">{render_inline(t)}</div>')
    out.append("</div></div>")
    if periods:
        out.append('<div class="tl-row"><div class="tl-lane tl-axis-name">時期</div><div class="tl-track tl-periods">')
        for pname, lo, hi, pcolor in periods:
            left = pos(lo - 1)
            out.append(f'<div class="tl-period" style="--c:var(--{pcolor});left:{left:.2f}%;width:{pos(hi) - left:.2f}%">{render_inline(pname)}</div>')
        out.append("</div></div>")
    out.append("</div></div>")
    return "".join(out)


def render_flow(lines) -> str:
    """把 flow 區塊畫成帶編號、直線串接的步驟圖；分支以綠（+）／橘（-）標籤呈現。
    縮排的 `> 標題 :: 說明` 是第二層子步驟；同一行用 ` | ` 隔開的多個子步驟為同時進行。"""
    steps = []
    for raw in lines:
        if not raw.strip():
            continue
        text = raw.strip()
        if raw[:1] in (" ", "\t") and text[:1] in "+-":
            kind = "ok" if text[0] == "+" else "stop"
            cond, _, result = text[1:].strip().partition("::")
            if steps:
                steps[-1]["branches"].append((kind, cond.strip(), result.strip()))
            continue
        if raw[:1] in (" ", "	") and text[:1] == ">":
            if steps:
                steps[-1]["subs"].append([tuple(x.strip() for x in part.partition("::")[::2])
                                          for part in text[1:].split(" | ")])
            continue
        title, _, desc = text.partition("::")
        steps.append({"title": title.strip(), "desc": desc.strip(), "branches": [], "subs": []})
    parts = ['<div class="flow">']
    for k, st in enumerate(steps, 1):
        body = f'<div class="step-title">{render_inline(st["title"])}</div>'
        if st["desc"]:
            body += f'<div class="step-desc">{render_inline(st["desc"])}</div>'
        if st["branches"]:
            body += '<div class="branches">' + "".join(
                f'<div class="branch"><span class="pill {kind}">{render_inline(cond)}</span>'
                f'<span>{render_inline(result)}</span></div>'
                for kind, cond, result in st["branches"]) + "</div>"
        if st["subs"]:
            rows = []
            for row in st["subs"]:
                boxes = "".join(
                    f'<div class="sub"><div class="sub-title">{render_inline(t)}</div>'
                    + (f'<div class="sub-desc">{render_inline(d)}</div>' if d else "") + "</div>"
                    for t, d in row)
                if len(row) > 1:
                    rows.append(f'<div class="sub-row par"><div class="par-tag">同時開發</div>'
                                f'<div class="par-boxes">{boxes}</div></div>')
                else:
                    rows.append(f'<div class="sub-row">{boxes}</div>')
            body += '<div class="subs">' + '<div class="sub-arrow">↓</div>'.join(rows) + "</div>"
        parts.append(f'<div class="step"><div class="step-rail"><div class="step-dot">{k}</div>'
                     f'<div class="step-line"></div></div><div class="step-body">{body}</div></div>')
    parts.append("</div>")
    return "".join(parts)


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

            # 時間軸：```timeline 區塊（格式見 render_timeline）
            if stripped.startswith("```timeline"):
                buf = []
                i += 1
                while i < n and not lines[i].strip().startswith("```"):
                    buf.append(lines[i])
                    i += 1
                i += 1
                self.out.append(render_timeline(buf))
                continue

            # 流程圖：```flow 區塊，每行「步驟 :: 說明」，縮排的「+ 條件 :: 結果」「- 條件 :: 結果」為分支
            if stripped.startswith("```flow"):
                buf = []
                i += 1
                while i < n and not lines[i].strip().startswith("```"):
                    buf.append(lines[i])
                    i += 1
                i += 1
                self.out.append(render_flow(buf))
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


GROUP_ORDER = [g for g, _ids in GROUPS + MINE_GROUPS + FLOW_GROUPS + ERRORS_GROUPS]


def line_tabs(folder: Path):
    """列出產線資料夾的 md，依所屬大分類在 GROUPS 的順序排列，其餘依檔名。"""
    # 只寫「待定」的頁先不顯示，有內容再出現
    mds = [p for p in folder.glob("*.md") if not p.name.startswith("_")
           and re.sub(r"^#.*$|[\s。]", "", p.read_text(encoding="utf-8"), flags=re.M) != "待定"]

    # 同大分類內照 Omniplay 的文件順序（以頁籤名稱或檔名比對，例：系統機制、天花板說明、腳本規範…）
    member = []
    for _g, ids in GROUPS + MINE_GROUPS + FLOW_GROUPS + ERRORS_GROUPS:
        for i in ids:
            for t, title, f in TABS:
                if t == i:
                    member += [title, Path(f).stem]

    def key(p):
        g = LINE_GROUP_OF.get(p.stem)
        return (GROUP_ORDER.index(g) if g in GROUP_ORDER else 99,
                member.index(p.stem) if p.stem in member else 99, p.stem)

    return [(tab_id_for(p.stem), p.stem, p.name) for p in sorted(mds, key=key)]


def line_groups(line):
    """產線頁籤分組：同一大分類的多份文件併成一個頁籤（左側導覽列文件名）。"""
    groups = []
    for tab_id, title, _f in line:
        g = LINE_GROUP_OF.get(title, title)
        if groups and groups[-1][0] == g:
            groups[-1][1].append(tab_id)
        else:
            groups.append((g, [tab_id]))
    return groups


def build_site(base: Path, tabs, output: Path, site_title: str, eyebrow: str, links: dict,
               groups=None, embed=False):
    """把 base 下的 tabs（tab_id, 頁籤名稱, 檔名）彙整成一份 HTML。

    groups：[(大分類, [tab_id...])]；省略時每份文件自成一類。
    embed：True 時不寫檔，回傳整頁 HTML（內嵌進入口用）。
    """
    global LINKS, MD_DIR, OUT_DIR
    LINKS = links
    OUT_DIR = output.parent
    _used_ids.clear()
    title_of = {t: title for t, title, _ in tabs}
    if groups is None:
        groups = [(title, [t]) for t, title, _ in tabs]
    grouped = [t for _g, ids in groups for t in ids]
    missing = [t for t in title_of if t not in grouped]
    unknown = [t for t in grouped if t not in title_of]
    assert not missing and not unknown, f"GROUPS 與 TABS 不一致：缺 {missing}、多 {unknown}"
    group_of = {t: ids for _g, ids in groups for t in ids}

    panels, toc_items, toc_raw = [], {}, {}
    first_tab = groups[0][1][0]
    for tab_id, title, filename in tabs:
        md = (base / filename).read_text(encoding="utf-8")
        MD_DIR = TREE_ROOT if Path(filename).name.startswith("_README") else (base / filename).parent
        r = Renderer(tab_id)
        body = r.render(md)
        toc_raw[tab_id] = list(r.toc)   # 第 2、3 層章節
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
        if len(ids) > 1:   # 一類多份文件：列文件名，只有目前這份展開章節
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
            f'<button class="tab{" tab-hi" if gname in HIGHLIGHT_GROUPS else ""}" role="tab" id="tab-g{gi}" data-tab="{ids[0]}" '
            f'data-tabs="{",".join(ids)}" aria-selected="{"true" if first else "false"}" '
            f'tabindex="{0 if first else -1}">{GROUP_ICONS.get(gname, "")}{gname}</button>'
        )

    today = date.today().strftime("%Y-%m-%d")
    src_label = "、".join(f"專案需知/{d}/*.md" for d in
                          sorted({rel_to_tree((base / f).parent).as_posix() for _t, _n, f in tabs}))
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
  --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --s4:#d23b3b; --warn:#a87400;
  --font-sans:'IBM Plex Sans','Noto Sans TC',system-ui,-apple-system,'Segoe UI',sans-serif;
  --font-mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Consolas,monospace;
}}
@media (prefers-color-scheme:dark){{
  :root:where(:not([data-theme="light"])){{
    --surface:#1a1a19; --panel:#212223; --panel-2:#1e1f20;
    --ink:#f3f3f1; --ink-2:#b4b8be; --ink-3:#868c95;
    --rule:#33353a; --grid:#2a2c30;
    --s1:#3987e5; --s2:#d95926; --s3:#199e70; --s4:#ef6060; --warn:#e3b341;
  }}
}}
:root[data-theme="dark"]{{
  --surface:#1a1a19; --panel:#212223; --panel-2:#1e1f20;
  --ink:#f3f3f1; --ink-2:#b4b8be; --ink-3:#868c95;
  --rule:#33353a; --grid:#2a2c30;
  --s1:#3987e5; --s2:#d95926; --s3:#199e70; --s4:#ef6060; --warn:#e3b341;
}}
*{{box-sizing:border-box}}
body{{margin:0; background:var(--surface); color:var(--ink);
  font-family:var(--font-sans); font-size:15px; line-height:1.65; -webkit-font-smoothing:antialiased}}
.wrap{{max-width:1200px; margin:0 auto; padding:38px 22px 80px}}
header.page{{display:flex; flex-direction:column; gap:9px; padding-bottom:20px}}
.eyebrow{{font-family:var(--font-mono); font-size:11.5px; letter-spacing:.14em; text-transform:uppercase; color:var(--ink-3)}}
h1.site{{margin:0; font-size:32px; font-weight:600; letter-spacing:-.02em}}
.meta{{margin:0; color:var(--ink-2); font-size:13.5px}}
.lines{{display:flex; gap:6px; flex-wrap:wrap; margin:2px 0}}
.lines a{{font-size:13px; text-decoration:none; color:var(--ink-2); border:1px solid var(--rule); border-radius:999px; padding:3px 13px; margin:0}}
.lines a:hover{{color:var(--s1); border-color:var(--s1)}}
.lines a.on{{color:var(--panel); background:var(--s1); border-color:var(--s1); font-weight:600}}
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
.tab-ico{{width:14px; height:14px; vertical-align:-2px; margin-right:6px}}
.tab.tab-hi, .tab.tab-hi:hover, .tab.tab-hi[aria-selected="true"]{{color:var(--warn)}}
.tab[aria-selected="true"]{{color:var(--s1); font-weight:600; background:var(--panel);
  border-color:var(--rule); border-bottom-color:var(--panel)}}
.tab:focus-visible{{outline:2px solid var(--s1); outline-offset:-2px}}
.body-row{{display:flex; gap:30px; align-items:flex-start; padding-top:26px}}
.toc{{position:sticky; top:52px; width:236px; flex:none;
  max-height:calc(100vh - 76px); overflow-y:auto;
  font-size:12.5px; line-height:1.5; padding:6px 8px 6px 0}}
.toc[hidden]{{display:none}}
/* 目錄過長時仍可滾動，但不顯示拉條 */
.toc{{scrollbar-width:none; -ms-overflow-style:none}}
.toc::-webkit-scrollbar{{display:none}}
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
table{{border-collapse:collapse; width:100%; font-size:1em}}
th,td{{padding:7px 12px; text-align:left; border-bottom:1px solid var(--grid); vertical-align:top}}
th{{background:var(--panel-2); color:var(--ink-2); font-weight:500; font-size:1em;
  letter-spacing:.03em; white-space:nowrap}}
td.n,th.n{{text-align:right; white-space:nowrap; font-family:var(--font-mono);
  font-variant-numeric:tabular-nums; font-size:1em}}
tbody tr:last-child td{{border-bottom:none}}
tbody tr:hover{{background:var(--panel-2)}}
hr{{border:none; border-top:1px solid var(--rule); margin:34px 0}}
.tune{{color:var(--s4); font-weight:600; border-bottom:1.5px dashed var(--s4); padding:0 1px; white-space:nowrap}}
.tune code{{color:inherit; background:none; border:none; padding:0; font-size:inherit}}
/* 特殊標記（粗體、可調參數、行內程式碼、連結）前後各留約一格，與中文字拉開 */
:is(p,li,td,th,.step-desc,.step-title,.branch) :is(strong,.tune,code,a,mark){{margin:0 .3em}}
:is(strong,.tune,a) :is(strong,.tune,code){{margin:0}}
:is(strong,.tune,code,a,mark).nl{{margin-left:0}}
:is(strong,.tune,code,a,mark).nr{{margin-right:0}}
.tl-wrap{{overflow-x:auto; margin:6px 0 18px; border:1px solid var(--rule); border-radius:3px; background:var(--panel); padding:14px 22px 8px 14px}}
.tl{{min-width:760px; display:flex; flex-direction:column; gap:4px}}
.tl-row{{display:grid; grid-template-columns:6em 1fr; align-items:start}}
.tl-lane{{font-size:1em; font-weight:600; color:var(--ink-2); padding-top:5px}}
.tl-axis-name{{color:var(--ink-3); font-weight:500; padding-top:2px}}
.tl-track{{position:relative; height:78px; border-bottom:1px dashed var(--grid)}}
.tl-track.short{{height:36px}}
.tl-bar{{position:absolute; top:4px; height:26px; border-radius:3px; font-size:1em; line-height:26px;
  text-align:center; white-space:nowrap; overflow:hidden}}
.tl-bar.phase{{background:color-mix(in srgb,var(--s1) 18%,transparent); color:var(--ink); font-weight:600}}
.tl-bar.phase2{{background:color-mix(in srgb,var(--s3) 20%,transparent); color:var(--ink); font-weight:600}}
.tl-bar.stop{{background:var(--panel-2); color:var(--ink-3); border:1px dashed var(--rule); line-height:22px}}
.tl-lane{{padding-top:44px}}
.tl-row:has(.tl-track.short) .tl-lane{{padding-top:5px}}
.tl-lane.tl-axis-name{{padding-top:2px}}
.tl-band{{position:absolute; top:46px; height:18px; border-radius:3px; background:color-mix(in srgb,var(--c) 16%,transparent)}}
.tl-bar.event{{background:var(--c); height:14px; top:48px; border-radius:2px}}
.tl-label{{position:absolute; top:2px; font-size:.95em; font-weight:600; line-height:1.25; color:var(--c); white-space:nowrap}}
.tl-range{{display:block; font-family:var(--font-mono); font-size:.85em; font-weight:500; color:var(--ink-2)}}
.tl-guide{{position:absolute; top:64px; border-left:1px dashed var(--c); opacity:.7; pointer-events:none}}
.tl-axis{{height:30px; border-bottom:none; border-top:1.5px solid var(--ink-3)}}
.tl-tick{{position:absolute; top:0; transform:translateX(-50%); font-family:var(--font-mono); font-size:1em;
  color:var(--ink-3); padding-top:5px; white-space:nowrap}}
.tl-axis.dense{{height:40px}}
.tl-axis.dense .tl-tick{{font-size:.78em}}
.tl-axis.dense .tl-tick:nth-child(even){{top:15px}}
.tl-axis.dense .tl-tick:nth-child(even)::before{{height:20px; top:-16px}}
.tl-periods{{height:30px; border-bottom:none}}
.tl-period{{position:absolute; top:2px; height:24px; line-height:24px; text-align:center; font-weight:600; font-size:.95em; color:var(--c);
  background:color-mix(in srgb,var(--c) 16%,transparent); border:1.5px solid var(--c); border-radius:3px; box-sizing:border-box}}
.tl-tick::before{{content:""; position:absolute; top:-1px; left:50%; height:5px; border-left:1.5px solid var(--ink-3)}}
mark{{font-weight:600; padding:1px 6px; border-radius:3px}}
mark.hl-warn{{color:var(--warn); background:color-mix(in srgb,var(--warn) 18%,transparent)}}
mark.hl-danger{{color:var(--s4); background:color-mix(in srgb,var(--s4) 16%,transparent)}}
.flow{{margin:6px 0 20px; max-width:86ch}}
.step{{display:grid; grid-template-columns:30px 1fr; gap:0 14px}}
.step-rail{{display:flex; flex-direction:column; align-items:center}}
.step-dot{{width:28px; height:28px; border-radius:50%; border:1.5px solid var(--s1); color:var(--s1);
  display:grid; place-items:center; font-family:var(--font-mono); font-size:12.5px; font-weight:600; background:var(--panel)}}
.step-line{{flex:1; width:1.5px; background:var(--rule); min-height:12px}}
.step:last-child .step-line{{background:transparent}}
.step-body{{padding:3px 0 18px; min-width:0}}
.step-title{{font-weight:600}}
.step-desc{{color:var(--ink-2); font-size:1em; margin-top:2px}}
.subs{{display:flex; flex-direction:column; align-items:flex-start; gap:2px; margin-top:8px}}
.sub-arrow{{color:var(--ink-3); padding-left:14px; line-height:1.2}}
.sub-row.par{{border:1px dashed var(--rule); border-radius:6px; padding:6px 8px 8px}}
.par-tag{{font-size:.85em; color:var(--ink-3); margin-bottom:4px}}
.par-boxes{{display:flex; gap:8px; flex-wrap:wrap}}
.sub{{border:1px solid var(--rule); border-radius:5px; padding:4px 10px; background:var(--panel)}}
.sub-title{{font-weight:600; font-size:.95em}}
.sub-desc{{color:var(--ink-2); font-size:.88em}}
.branches{{display:flex; flex-direction:column; gap:6px; margin-top:8px; padding-left:11px; border-left:2px solid var(--rule)}}
.branch{{display:flex; gap:10px; align-items:baseline; flex-wrap:wrap; font-size:1em}}
.pill{{font-size:1em; font-weight:600; padding:1px 8px; border-radius:3px; white-space:nowrap}}
.pill.ok{{color:var(--s3); background:color-mix(in srgb,var(--s3) 15%,transparent)}}
.pill.stop{{color:var(--s2); background:color-mix(in srgb,var(--s2) 15%,transparent)}}
@media (max-width:900px){{
  .body-row{{flex-direction:column; gap:14px}}
  .toc{{display:none!important}}
  .toc:not([hidden]):has(.toc-doc){{display:flex!important; position:static; width:auto; max-height:none;
    flex-wrap:wrap; gap:4px 16px; padding:0}}
  .toc a:not(.toc-doc){{display:none}}
  .toc a.toc-doc{{padding:0; margin:0!important}}
}}
/* 表格、程式碼、時間軸：藏拉條，仍可橫向捲動（觸控板／觸控／滑鼠拖曳） */
.tbl-wrap, pre, .tl-wrap{{scrollbar-width:none; -ms-overflow-style:none}}
.tbl-wrap::-webkit-scrollbar, pre::-webkit-scrollbar, .tl-wrap::-webkit-scrollbar{{display:none}}
.drag-x{{cursor:grab}}
.drag-x.dragging{{cursor:grabbing; user-select:none}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
/* 嵌入入口時：頁首、頁籤、左側目錄由入口負責，這裡只留內文；藏拉條、仍可上下捲動 */
html.embedded{{scrollbar-width:none; -ms-overflow-style:none}}
html.embedded::-webkit-scrollbar{{display:none}}
html.embedded body{{background:transparent}}
html.embedded .wrap{{max-width:none; padding:0}}
html.embedded header.page, html.embedded .tabs, html.embedded .toc,
html.embedded .toc:not([hidden]):has(.toc-doc){{display:none!important}}
html.embedded .body-row{{display:block; padding:0}}
html.embedded main{{background:var(--panel); border:1px solid var(--rule); border-radius:4px; padding:26px 32px 60px}}
html.embedded .panel h1{{color:var(--ink); font-weight:600; font-size:30px}}
html.embedded h2{{color:var(--ink); border-bottom-color:var(--grid)}}
html.embedded main{{max-width:1080px}}
html.embedded a{{color:var(--accent); text-decoration:none}}
html.embedded a:hover{{text-decoration:underline}}
html.embedded td code, html.embedded li code{{background:transparent; border:0; padding:0; color:var(--ink)}}
:root{{--accent:#1b3a6b}}
@media (prefers-color-scheme:dark){{:root:where(:not([data-theme="light"])){{--accent:#6f97d8}}}}
:root[data-theme="dark"]{{--accent:#6f97d8}}
@media (max-width:700px){{html.embedded main{{padding:18px 16px 40px}}}}
</style>
<script>if (window.self !== window.top) document.documentElement.classList.add('embedded');</script>
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
  // 嵌入入口時通知入口：左側目錄跟著亮起
  if (window.self !== window.top) window.parent.postMessage({{specTab: tabId, specAnchor: anchor || ''}}, '*');
}}
// 入口左側目錄點選 → 切到對應頁籤／章節
window.addEventListener('message', function(e) {{
  var d = e.data || {{}};
  if (d.goTab && TAB_IDS.indexOf(d.goTab) >= 0) activate(d.goTab, d.goAnchor || null);
}});
// 嵌入時捲動內文，回報目前讀到的章節
window.addEventListener('scroll', function() {{
  if (window.self === window.top) return;
  clearTimeout(window._spy);
  window._spy = setTimeout(function() {{
    var p = document.querySelector('.panel:not([hidden])');
    if (!p) return;
    var cur = '';
    p.querySelectorAll('h2[id], h3[id]').forEach(function(h) {{ if (h.getBoundingClientRect().top < 90) cur = h.id; }});
    window.parent.postMessage({{specTab: p.id.slice(6), specAnchor: cur, spy: true}}, '*');
  }}, 80);
}});
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
// 寬表格／程式碼／時間軸：滑鼠按住左右拖曳捲動（拉條已隱藏）
(function() {{
  var drag = null, moved = false;
  function mark() {{
    document.querySelectorAll('.tbl-wrap, pre, .tl-wrap').forEach(function(el) {{
      el.classList.toggle('drag-x', el.scrollWidth > el.clientWidth + 1);
    }});
  }}
  document.addEventListener('mousedown', function(e) {{
    var el = e.button === 0 && e.target.closest('.drag-x');
    if (!el || e.target.closest('a')) return;
    drag = {{ el: el, x: e.clientX, left: el.scrollLeft }};
    moved = false;
  }});
  document.addEventListener('mousemove', function(e) {{
    if (!drag) return;
    var dx = e.clientX - drag.x;
    if (!moved && Math.abs(dx) < 4) return;
    moved = true;
    drag.el.classList.add('dragging');
    drag.el.scrollLeft = drag.left - dx;
    e.preventDefault();
  }});
  document.addEventListener('mouseup', function() {{
    if (drag) drag.el.classList.remove('dragging');
    drag = null;
  }});
  // 拖曳結束時不要觸發點擊
  document.addEventListener('click', function(e) {{
    if (moved) {{ e.stopPropagation(); e.preventDefault(); moved = false; }}
  }}, true);
  window.addEventListener('resize', mark);
  document.addEventListener('click', function() {{ setTimeout(mark, 0); }});
  mark();
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
    # 給入口左側目錄用：頁籤分組、文件名、各文件的第 2 層章節
    meta = {"groups": groups, "titles": title_of, "toc": toc_raw}
    if embed:   # 不另存檔，整頁內嵌進入口
        return page, meta
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
    print(f"OK: {rel_to_tree(output)} 已更新（{output.stat().st_size:,} bytes）")
    return None, meta


def rel_to_tree(path: Path) -> Path:
    """顯示用路徑：相對於個人版（HERE）或團隊版（TEAM_DIR）的根。"""
    for root in (HERE, TEAM_DIR):
        try:
            return path.relative_to(root)
        except ValueError:
            continue
    return path


def build_hub(root: Path, sites, embedded=None, metas=None, out_name=HUB_NAME, site_title=None):
    """最外層入口（git-scm Cheat Sheet 版型）：左側上方「我的製程（開發規範／開發流程／錯誤紀錄）」「產線須知（Omniplay／Landbase／Reskin）」，
    下方 Table of Contents 列所選站的頁籤與章節；右側內嵌所選站的內文。網址 #站/頁籤/章節 記住所選。

    embedded：{key: 整頁 HTML}；這些站不另存檔，整頁放進入口、以 iframe srcdoc 顯示。
    metas：{key: build_site 回傳的頁籤分組與章節}。
    site_title：只放一個站時（各站單獨的網頁）給頁首名稱；不顯示站切換，網址為 #頁籤/章節。
    """
    import json
    embedded, metas = embedded or {}, metas or {}

    def js(obj):
        return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")

    from datetime import datetime
    stamp = datetime.now().strftime("%Y%m%d%H%M")   # 網頁改版後避免吃到快取的舊 iframe
    info = {key: {"name": name, "src": "" if key in embedded else f"{src}?v={stamp}", "meta": metas.get(key, {})}
            for key, name, src in sites}
    keys = [k for k in HUB_ORDER if k in info] + [k for k in info if k not in HUB_ORDER]
    sections = [(t, [k for k in ks if k in info]) for t, ks in HUB_SECTIONS]
    sections[-1][1].extend(k for k in keys if k not in HUB_ORDER)
    single = site_title is not None
    if single:
        head, _sp, tail = site_title.partition(" ")
        h1, title = (f"<b>{head}</b> {tail}" if tail else f"<b>iGaming</b> {head}"), site_title
    else:
        h1, title = "<b>iGaming</b> 開發需知", "iGaming 開發需知"
    nav = "" if single else "".join(f'<li><span class="top">{t}</span><ul class="sub">'
                  + "".join(f'<li><a href="#{k}" data-key="{k}">{info[k]["name"]}</a></li>' for k in ks)
                  + "</ul></li>" for t, ks in sections if ks)
    docs = "".join(f'<script type="application/json" id="doc-{key}">{js(page)}</script>'
                   for key, page in embedded.items())
    page = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Noto+Sans+TC:wght@400;500;700&display=swap">
<style>
:root{{--surface:#f6f5f1; --panel:#ffffff; --ink:#101418; --ink-2:#4a5462; --ink-3:#7d8794; --rule:#dcdad3;
  --accent:#1b3a6b; --brand:#1b3a6b;
  --font-sans:'IBM Plex Sans','Noto Sans TC',system-ui,-apple-system,'Segoe UI',sans-serif}}
@media (prefers-color-scheme:dark){{:root:where(:not([data-theme="light"])){{
  --surface:#1b1b1a; --panel:#232322; --ink:#e9e8e4; --ink-2:#b9b7b0; --ink-3:#8d8b85; --rule:#3a3936; --accent:#6f97d8}}}}
:root[data-theme="dark"]{{--surface:#1b1b1a; --panel:#232322; --ink:#e9e8e4; --ink-2:#b9b7b0; --ink-3:#8d8b85; --rule:#3a3936; --accent:#6f97d8}}
*{{box-sizing:border-box}}
html,body{{height:100%; margin:0}}
body{{display:flex; flex-direction:column; background:var(--surface); color:var(--ink); font-family:var(--font-sans)}}
/* 不顯示拉條，仍可上下捲動 */
aside, iframe{{scrollbar-width:none; -ms-overflow-style:none}}
aside::-webkit-scrollbar{{display:none}}
header{{display:flex; align-items:center; gap:12px; padding:18px 28px 14px}}
.logo{{width:34px; height:34px; border-radius:8px; background:var(--brand); flex:none; box-shadow:inset 0 0 0 1px rgba(255,255,255,.12);
  display:grid; place-items:center}}
.logo span{{color:#fff; font-weight:700; font-size:17px; font-family:var(--font-sans)}}
h1{{margin:0 0 0 6px; font-size:22px; font-weight:500; color:var(--ink-2); letter-spacing:-.01em}}
h1 b{{color:var(--ink); font-weight:600}}
.layout{{flex:1; min-height:0; display:flex; gap:26px; padding:0 28px 22px}}
aside{{width:236px; flex:none; overflow-y:auto; padding:6px 2px 20px 0}}
.nav{{list-style:none; margin:0 0 22px; padding:0}}
.nav > li{{margin:0 0 6px}}
.nav .top{{display:block; font-size:17px; font-weight:500; color:var(--ink-2); text-decoration:none; padding:3px 0}}
.nav a.top:hover{{color:var(--accent)}}
.nav .sub{{list-style:none; margin:4px 0 0; padding:0 0 0 18px}}
.nav .sub a{{display:block; font-size:14px; color:var(--ink-2); text-decoration:none; padding:3px 0}}
.nav .sub a:hover{{color:var(--accent)}}
.nav a.on, .nav span.top.on{{color:var(--accent); font-weight:600}}
.nav a:focus, .toc a:focus{{outline:none}}
.nav a:focus-visible, .toc a:focus-visible{{outline:2px solid var(--accent); outline-offset:2px}}
.toc{{border:1px solid var(--rule); border-radius:3px; padding:12px 12px 14px; background:var(--panel)}}
.toc[hidden]{{display:none}}
.toc-title{{font-size:16px; font-weight:600; margin:0 0 8px}}
.toc ul{{margin:0; padding-left:18px; list-style:square; color:var(--ink-3)}}
.toc li{{margin:3px 0; font-size:13.5px; line-height:1.4}}
.toc ul ul{{padding-left:14px; margin:3px 0 6px; list-style:none}}
.toc ul ul li{{font-size:12.5px}}
.toc a{{color:var(--ink-3); text-decoration:none}}
.toc a:hover{{color:var(--accent)}}
.toc a.on{{color:var(--accent); font-weight:600}}
.toc .doc{{color:var(--ink-2)}}
main{{flex:1; min-width:0; display:flex}}
iframe{{flex:1; width:100%; height:100%; border:0; display:block; background:transparent}}
@media (max-width:760px){{
  header{{padding:14px 16px 10px}}
  .layout{{flex-direction:column; padding:0 16px 16px; gap:14px}}
  aside{{width:auto; overflow:visible; padding:0}}
  main{{height:80vh; flex:none}}
}}
/* 頂部搜尋框 */
.pv-search{{position:relative; margin-left:auto; flex:0 1 420px; min-width:160px}}
.pv-search input{{width:100%; box-sizing:border-box; padding:8px 12px 8px 34px; border-radius:8px; border:1px solid var(--rule);
  background:var(--panel); color:var(--ink); font:inherit; font-size:14px; outline:none}}
.pv-search input:focus{{border-color:var(--accent); box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 25%,transparent)}}
.pv-search .ico{{position:absolute; left:11px; top:50%; transform:translateY(-50%); color:var(--ink-3); pointer-events:none; font-size:14px}}
.pv-search kbd{{position:absolute; right:9px; top:50%; transform:translateY(-50%); font-size:11px; color:var(--ink-3);
  border:1px solid var(--rule); border-radius:4px; padding:0 5px; background:var(--surface)}}
.pv-res{{position:absolute; top:calc(100% + 6px); right:0; width:min(560px,calc(100vw - 32px)); max-height:70vh; overflow:auto; z-index:50; display:none;
  background:var(--panel); border:1px solid var(--rule); border-radius:10px; box-shadow:0 12px 32px rgba(0,0,0,.35); padding:6px}}
.pv-res.on{{display:block}}
.pv-item{{display:block; padding:8px 10px; border-radius:7px; cursor:pointer; color:var(--ink); text-decoration:none}}
.pv-item:hover,.pv-item.sel{{background:color-mix(in srgb,var(--accent) 18%,transparent)}}
.pv-path{{font-size:11.5px; color:var(--ink-3)}}
.pv-title{{font-weight:600; font-size:14px; margin:1px 0}}
.pv-snip{{font-size:12.5px; color:var(--ink-2); overflow:hidden; text-overflow:ellipsis; white-space:nowrap}}
.pv-snip mark,.pv-title mark{{background:color-mix(in srgb,var(--accent) 45%,transparent); color:inherit; border-radius:2px}}
.pv-empty{{padding:10px; color:var(--ink-3); font-size:13px}}
header{{display:flex; align-items:center}}
@media (min-width:900px){{aside{{position:sticky; top:12px; align-self:flex-start; max-height:calc(100vh - 24px)}}}}
</style>
</head>
<body>
<header><div class="logo"><span>J</span></div><h1>{h1}</h1></header>
<div class="layout">
<aside>
  {'<ul class="nav">' + nav + '</ul>' if nav else ''}
  <nav class="toc" aria-label="Table of Contents"><div class="toc-title">Table of Contents</div><ul id="toc"></ul></nav>
</aside>
<main><iframe id="site" title="規範內文"></iframe></main>
</div>
{docs}
<script>
var SITES = {js(info)};
var KEYS = {js(keys)};
var SINGLE = {js(single)};
var frame = document.getElementById('site');
var cur = {{ key: null, tab: null, anchor: '' }};
function esc(s) {{ return String(s).replace(/[&<>"]/g, function (c) {{ return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]; }}); }}
function setHash() {{
  var h = '#' + (SINGLE ? '' : cur.key + (cur.tab ? '/' : '')) + (cur.tab || '') + (cur.anchor ? '/' + cur.anchor : '');
  if (location.hash !== h) history.replaceState(null, '', h);
}}
// 目錄最多兩層：大類下只有一份文件時列章節；多份文件時只列文件名（章節看內文）
// 文件名去掉「規範」、章節去掉編號，各站寫法一致
var DOC_NAME = {{ 'GameRule規範': 'Game Rule', 'Demo報告規範': 'Demo 報告' }};
function docName(t) {{ return DOC_NAME[t] || t.replace(/規範$/, ''); }}
function secName(t) {{ return t.replace(/^\\d+(\\.\\d+)*\\.?\\s*/, ''); }}
function secLink(t, s, on) {{
  return '<a href="#" data-tab="' + t + '" data-anchor="' + s[1] + '"' + (on ? ' class="on"' : '') + '>' + esc(secName(s[2])) + '</a>';
}}
// 整站只有一份文件（開發流程）：每章當一個大類、小節列在下面，與其他站同一種結構
function renderFlat(m, t) {{
  var out = '', list = (m.toc || {{}})[t] || [], open = false;
  // 目前讀到的小節所屬的章（第 2 層）
  var curChap = '', last2 = '';
  list.forEach(function (s) {{ if (s[0] === 2) last2 = s[1]; if (s[1] === cur.anchor) curChap = last2; }});
  list.forEach(function (s) {{
    if (s[0] === 2) {{
      if (open) out += '</ul></li>';
      out += '<li>' + secLink(t, s, s[1] === curChap) + '<ul>';
      open = true;
    }} else if (open) {{
      out += '<li>' + secLink(t, s, s[1] === cur.anchor) + '</li>';
    }}
  }});
  if (open) out += '</ul></li>';
  return out.replace(/<ul><\\/ul>/g, '');
}}
function renderToc() {{
  var m = SITES[cur.key].meta, out = '';
  var gs = m.groups || [];
  if (gs.length === 1 && gs[0][1].length === 1) {{
    setToc(renderFlat(m, gs[0][1][0]));
    return;
  }}
  gs.forEach(function (g) {{
    var ids = g[1], active = ids.indexOf(cur.tab) >= 0;
    out += '<li><a href="#" data-tab="' + ids[0] + '"' + (active ? ' class="on"' : '') + '>' + esc(g[0]) + '</a>';
    {{   // 全部展開，不折疊
      out += '<ul>';
      if (ids.length > 1) {{
        ids.forEach(function (t) {{
          out += '<li><a href="#" data-tab="' + t + '"' + (t === cur.tab ? ' class="on"' : '') + '>' + esc(docName(m.titles[t])) + '</a></li>';
        }});
      }} else {{
        var lst = (m.toc || {{}})[ids[0]] || [], ch = '', l2 = '';
        lst.forEach(function (s) {{ if (s[0] === 2) l2 = s[1]; if (s[1] === cur.anchor) ch = l2; }});
        lst.filter(function (s) {{ return s[0] === 2; }}).forEach(function (s) {{
          out += '<li><a href="#" data-tab="' + ids[0] + '" data-anchor="' + s[1] + '"' + (active && s[1] === ch ? ' class="on"' : '') + '>' + esc(secName(s[2])) + '</a></li>';
        }});
      }}
      out += '</ul>';
    }}
    out += '</li>';
  }});
  setToc(out);
}}
// 沒有任何目錄項目時整個 Table of Contents 框拿掉
function setToc(h) {{
  var u = document.getElementById('toc');
  u.innerHTML = h;
  u.closest('.toc').hidden = !u.querySelector('a');
}}
function markNav() {{
  document.querySelectorAll('.nav a').forEach(function (a) {{ a.classList.toggle('on', a.dataset.key === cur.key); }});
}}
function go(tab, anchor) {{
  cur.tab = tab; cur.anchor = anchor || '';
  frame.contentWindow && frame.contentWindow.postMessage({{ goTab: tab, goAnchor: anchor || '' }}, '*');
  renderToc(); setHash();
}}
function openSite(key, tab, anchor) {{
  if (!SITES[key]) key = KEYS[0];
  var groups = SITES[key].meta.groups || [];
  cur = {{ key: key, tab: tab || (groups[0] ? groups[0][1][0] : null), anchor: anchor || '' }};
  frame.onload = function () {{ if (cur.tab) frame.contentWindow.postMessage({{ goTab: cur.tab, goAnchor: cur.anchor }}, '*'); }};
  var doc = document.getElementById('doc-' + key);
  if (doc) {{ frame.removeAttribute('src'); frame.srcdoc = JSON.parse(doc.textContent); }}
  else {{ frame.removeAttribute('srcdoc'); frame.src = SITES[key].src; }}
  markNav(); renderToc(); setHash();
}}
document.querySelector('.nav') && document.querySelector('.nav').addEventListener('click', function (e) {{
  var a = e.target.closest('a[data-key]');
  if (!a) return;
  e.preventDefault();
  openSite(a.dataset.key);
}});
document.getElementById('toc').addEventListener('click', function (e) {{
  var a = e.target.closest('a[data-tab]');
  if (!a) return;
  e.preventDefault();
  go(a.dataset.tab, a.dataset.anchor || '');
}});
// 內文切頁籤或捲動時，左側目錄跟著亮起
window.addEventListener('message', function (e) {{
  var d = e.data || {{}};
  if (!d.specTab || e.source !== frame.contentWindow) return;
  if (d.spy && d.specTab !== cur.tab) return;
  cur.tab = d.specTab; cur.anchor = d.specAnchor || '';
  renderToc(); setHash();
}});
(function () {{
  // ===== 全站搜尋：標題＋內文，Ctrl+K 聚焦，結果直接跳到該節 =====
  var idx = [];
  KEYS.forEach(function (key) {{
    var el = document.getElementById('doc-' + key);
    if (!el) return;
    var dom = new DOMParser().parseFromString(JSON.parse(el.textContent), 'text/html');
    var site = SITES[key].name, titles = SITES[key].meta.titles || {{}};
    dom.querySelectorAll('section.panel').forEach(function (sec) {{
      var tab = sec.id.replace(/^panel-/, ''), doc = titles[tab] || '';
      var cur = {{ key: key, tab: tab, anchor: '', title: doc, path: site + ' › ' + doc, text: '' }};
      idx.push(cur);
      var walker = dom.createTreeWalker(sec, NodeFilter.SHOW_ELEMENT);
      for (var n = walker.nextNode(); n; n = walker.nextNode()) {{
        if (/^H[1-4]$/.test(n.tagName) && n.id) {{
          cur = {{ key: key, tab: tab, anchor: n.id, title: n.textContent.trim(), path: site + ' › ' + doc, text: '' }};
          idx.push(cur);
        }} else if (/^(P|LI|TD|TH|PRE|BLOCKQUOTE)$/.test(n.tagName)) {{
          cur.text += ' ' + n.textContent.replace(/\s+/g, ' ');
        }}
      }}
    }});
  }});

  var hdr = document.querySelector('header');
  var box = document.createElement('div');
  box.className = 'pv-search';
  box.innerHTML = '<span class="ico">⌕</span><input type="search" placeholder="搜尋所有規範…" aria-label="搜尋所有規範"><kbd>Ctrl K</kbd><div class="pv-res"></div>';
  hdr.appendChild(box);
  var input = box.querySelector('input'), res = box.querySelector('.pv-res'), hits = [], sel = 0;
  function e(s) {{ return String(s).replace(/[&<>"]/g, function (c) {{ return {{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }}[c]; }}); }}
  function hl(s, q) {{ var i = s.toLowerCase().indexOf(q); return i < 0 ? e(s) : e(s.slice(0, i)) + '<mark>' + e(s.slice(i, i + q.length)) + '</mark>' + e(s.slice(i + q.length)); }}
  function snip(t, q) {{ var i = t.toLowerCase().indexOf(q); if (i < 0) return ''; var a = Math.max(0, i - 30); return (a ? '…' : '') + t.slice(a, i + q.length + 60); }}
  function search() {{
    var q = input.value.trim().toLowerCase();
    if (!q) {{ res.classList.remove('on'); return; }}
    hits = idx.map(function (r) {{
      var t = r.title.toLowerCase().indexOf(q) >= 0, b = r.text.toLowerCase().indexOf(q) >= 0;
      return {{ r: r, s: t ? 2 : b ? 1 : 0 }};
    }}).filter(function (h) {{ return h.s; }}).sort(function (a, b) {{ return b.s - a.s; }}).slice(0, 30);
    sel = 0;
    res.innerHTML = hits.length ? hits.map(function (h, i) {{
      return '<a class="pv-item' + (i === 0 ? ' sel' : '') + '" data-i="' + i + '"><div class="pv-path">' + e(h.r.path) + '</div><div class="pv-title">' + hl(h.r.title, q) + '</div>' +
        (h.s === 1 || snip(h.r.text, q) ? '<div class="pv-snip">' + hl(snip(h.r.text, q), q) + '</div>' : '') + '</a>';
    }}).join('') : '<div class="pv-empty">找不到「' + e(input.value) + '」</div>';
    res.classList.add('on');
  }}
  function pick(i) {{
    var r = hits[i] && hits[i].r; if (!r) return;
    res.classList.remove('on'); input.blur();
    if (cur.key === r.key) go(r.tab, r.anchor); else openSite(r.key, r.tab, r.anchor);
  }}
  input.addEventListener('input', search);
  input.addEventListener('focus', search);
  input.addEventListener('keydown', function (ev) {{
    var items = res.querySelectorAll('.pv-item');
    if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') {{
      ev.preventDefault(); if (!items.length) return;
      items[sel].classList.remove('sel'); sel = (sel + (ev.key === 'ArrowDown' ? 1 : items.length - 1)) % items.length;
      items[sel].classList.add('sel'); items[sel].scrollIntoView({{ block: 'nearest' }});
    }} else if (ev.key === 'Enter') {{ ev.preventDefault(); pick(sel); }}
    else if (ev.key === 'Escape') {{ res.classList.remove('on'); input.blur(); }}
  }});
  res.addEventListener('mousedown', function (ev) {{ var a = ev.target.closest('.pv-item'); if (a) {{ ev.preventDefault(); pick(+a.dataset.i); }} }});
  document.addEventListener('click', function (ev) {{ if (!box.contains(ev.target)) res.classList.remove('on'); }});
  document.addEventListener('keydown', function (ev) {{ if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 'k') {{ ev.preventDefault(); input.focus(); input.select(); }} }});
}})();
(function () {{
  var p = decodeURIComponent(location.hash.slice(1)).split('/');
  if (SINGLE) openSite(KEYS[0], p[0], p.slice(1).join('/'));
  else openSite(p[0], p[1], p.slice(2).join('/'));
}})();
</script>
</body>
</html>
"""
    out = root / out_name
    out.write_text(page, encoding="utf-8")
    print(f"OK: {rel_to_tree(out)} 已更新（{out.stat().st_size:,} bytes）")


def build_tree(root: Path, tabs, groups, private_sites, lines=True):
    """建置一整套：Omniplay／各產線（lines=True 時）／不外放的站（Mine、開發流程）＋ 最外層入口；網頁都在 root。"""
    global TREE_ROOT, LOCAL_ONLY
    TREE_ROOT = root
    omni_tabs = [t for t in tabs if t[0] not in MINE_TAB_IDS + FLOW_TAB_IDS + ERRORS_TAB_IDS + SPS_TAB_IDS]
    # (key, 名稱, md 基準資料夾, tabs, 輸出, 頁首名稱, 分組)
    sites = [("omniplay", "Omniplay", root, omni_tabs, root / OMNI_FILE, ROOT_TITLE, groups)]
    for folder, out_name, site_title in (PRODUCT_LINES if lines else []):
        line = line_tabs(root / SPEC_DIR / folder)
        shared = [(t, title, Path(os.path.relpath(root / f, root / SPEC_DIR / folder)).as_posix())
                  for t, title, f in omni_tabs if t in SHARED_TABS.get(folder, [])]
        if shared:   # 共用 Omniplay 文件併入後，依大分類順序重排
            order = lambda x: GROUP_ORDER.index(LINE_GROUP_OF.get(x[1], x[1])) if LINE_GROUP_OF.get(x[1], x[1]) in GROUP_ORDER else 99
            # 同大分類內照 Omniplay 順序；產線自己的同名文件（如 系統機制）排在 Omniplay 對應文件的位置
            title_of = {t: title for t, title, _f in omni_tabs}
            member = [title_of.get(i, i) for _g, ids in GROUPS for i in ids]
            line = sorted(line + shared, key=lambda x: (order(x), member.index(x[1]) if x[1] in member else 99))
        if line:
            sites.append((folder.lower(), folder, root / SPEC_DIR / folder, line, root / out_name, site_title,
                          line_groups(line)))
    for key, name, ids, out_name, site_title, site_groups in private_sites:
        site_tabs = [t for t in tabs if t[0] in ids]
        if site_tabs:
            sites.append((key, name, root, site_tabs, root / out_name, site_title, site_groups))

    docs = {}   # 規範 md（相對 root）→ (站台序號, tab_id)
    for i, site in enumerate(sites):
        for tab_id, _, filename in site[3]:
            docs.setdefault(Path(os.path.relpath(site[2] / filename, root)).as_posix(), (i, tab_id))

    embedded = {}   # key → 整頁 HTML（內嵌進入口）
    metas = {}      # key → 頁籤分組與章節（入口左側目錄用）
    for i, (key, name, base, site_tabs, output, site_title, site_groups) in enumerate(sites):
        links = {}
        for doc, (j, tab_id) in docs.items():
            if j == i:
                links[doc] = ("tab", tab_id)
            else:
                href = Path(os.path.relpath(sites[j][4], output.parent)).as_posix()
                links[doc] = ("ext", f"{href}#{tab_id}")
        for tab_id, _, filename in site_tabs:   # 站內（含共用文件）一律連到本站頁籤
            links[Path(os.path.relpath(base / filename, root)).as_posix()] = ("tab", tab_id)
        LOCAL_ONLY = True   # 各站（Omniplay／Landbase／Reskin／Mine／開發流程）互不連結，只連站內頁籤
        try:
            page, metas[key] = build_site(base, site_tabs, output, site_title, f"iGaming · {name}", links,
                                          site_groups, embed=True)
            embedded[key] = page
            if key in EMBED_KEYS:
                if output.exists():   # 舊版另存的檔案
                    output.unlink()
            else:   # 單獨的網頁也用入口的版型（左側目錄＋右側內文），只放本站
                build_hub(root, [(key, name, "")], {key: page}, {key: metas[key]},
                          out_name=output.name, site_title=site_title)
        finally:
            LOCAL_ONLY = False

    build_hub(root, [(key, name, Path(os.path.relpath(output, root)).as_posix())
                     for key, name, _b, _t, output, _s, _g in sites], embedded, metas)


def publish_team():
    """把團隊規範複製到共享資料夾並建置 HTML；共享資料夾連不到時略過。"""
    global PLAIN_UNKNOWN_MD
    import shutil
    try:
        reachable = TEAM_DIR.exists()
    except OSError as err:   # 例：網路磁碟要求重新登入（WinError 1326）
        reachable = False
        print(f"略過團隊版：{TEAM_DIR} 無法存取（{err.strerror or err}）")
    if not reachable:
        print(f"略過團隊版：連不到 {TEAM_DIR}")
        return
    tabs = [t for t in TABS if t[0] in TEAM_TAB_IDS]
    files = [f for _, _, f in tabs] + TEAM_TOOLS
    for f in files:
        (TEAM_DIR / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE / f, TEAM_DIR / f)
    print(f"團隊版：已複製 {len(files)} 份到 {TEAM_DIR}")
    PLAIN_UNKNOWN_MD = True
    try:
        build_tree(TEAM_DIR, tabs, TEAM_GROUPS, [], lines=False)
    finally:
        PLAIN_UNKNOWN_MD = False


# SVN 說明書：外團隊用的規範 md（使用者上傳 SVN 後分別開權限）。
# 每個子資料夾依其 數學模型規範.md 的標題判斷是哪條產線；只更新資料夾內「已經有的」檔案，
# 不自動新增（放哪些檔給外團隊由使用者決定），新出現的規範只列出提醒。
SVN_DIR = Path(r"D:\SVN\Slot\IGaming\說明書")


def sync_svn():
    import shutil
    if not SVN_DIR.exists():
        print(f"略過 SVN 說明書：找不到 {SVN_DIR}")
        return
    for target in sorted(d for d in SVN_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")):
        probe = target / "數學模型規範.md"
        title = probe.read_text(encoding="utf-8").split("\n", 1)[0] if probe.exists() else ""
        line = next((f for f, _o, _t in PRODUCT_LINES if f in title), None)
        if not line:
            print(f"略過 SVN 說明書／{target.name}：判斷不出產線")
            continue
        src = HERE / SPEC_DIR / line
        updated = []
        for f in sorted(target.glob("*.md")):
            if (src / f.name).exists() and (src / f.name).read_bytes() != f.read_bytes():
                shutil.copy2(src / f.name, f)
                updated.append(f.name)
        extra = sorted(p.name for p in src.glob("*.md")
                       if not p.name.startswith("_") and not (target / p.name).exists())
        print(f"SVN 說明書／{target.name}（{line}）：更新 {len(updated)} 份"
              + (f"：{'、'.join(updated)}" if updated else "")
              + (f"；未放入的規範：{'、'.join(extra)}" if extra else ""))


# 對外文件：專案開發/對外文件/<YYMMDD_主題>/*.md → 同資料夾同名 .html（單頁，入口站「專案須知」標「對外文件」）
EXTERNAL_DIR = HERE.parent / "對外文件"


def build_external():
    global TREE_ROOT, LOCAL_ONLY
    if not EXTERNAL_DIR.exists():
        return
    for md in sorted(EXTERNAL_DIR.glob("*/*.md")):
        if md.name.startswith("_"):
            continue
        first = md.read_text(encoding="utf-8").lstrip().split("\n", 1)[0]
        title = first.lstrip("#").strip() if first.startswith("#") else md.stem.replace("_", " ")
        tab_id = "doc"
        out = md.with_suffix(".html")
        TREE_ROOT, LOCAL_ONLY = md.parent, True
        try:
            page, meta = build_site(md.parent, [(tab_id, title, md.name)], out, title, "iGaming · 對外文件",
                                    {md.name: ("tab", tab_id)}, [(title, [tab_id])], embed=True)
            build_hub(md.parent, [("ext", title, "")], {"ext": page}, {"ext": meta},
                      out_name=out.name, site_title=title)
        finally:
            TREE_ROOT, LOCAL_ONLY = HERE, False


def build():
    build_tree(HERE, TABS, GROUPS, PRIVATE_SITES)
    build_external()
    publish_team()
    sync_svn()


if __name__ == "__main__":
    build()
