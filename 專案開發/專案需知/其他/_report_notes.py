"""數值報告 report.html 的自動頁簽（2026-11-09 使用者定章節）：玩法說明（game_help_draft.md）、修改紀錄、其他（上線觀察＋開發注意事項＋歷史錯誤紀錄）。

用法：py -X utf8 _report_notes.py <專案>/report.html [...]
- md 用 _build_html.py 的 Renderer 轉 HTML；每個 `##` 一張卡片，`#` 標題不放（頁簽名稱已說明）。
- 頁簽接在既有頁簽後面、編號續排；個人筆記/ 沒有該檔就不加。
- 可重複執行：先移除上次加的頁簽（data-notes），再依最新 md 重加。_report_card_style.py 會自動呼叫。
"""
import importlib.util
import sys
from pathlib import Path

from bs4 import BeautifulSoup

NOTES = [("修改紀錄", "修改紀錄.md"), ("注意事項", "注意事項.md"), ("上線觀察", "上線觀察.md")]

_spec = importlib.util.spec_from_file_location("_build_html", Path(__file__).with_name("_build_html.py"))
_bh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bh)


def md_to_cards(md: str) -> str:
    soup = BeautifulSoup(_bh.Renderer("notes").render(md), "html.parser")
    for h1 in soup.find_all("h1"):
        h1.decompose()
    out, cur, intro = [], None, []
    for node in list(soup.contents):
        if getattr(node, "name", None) == "h2":
            cur = soup.new_tag("div", attrs={"class": "card"})
            h3 = soup.new_tag("h3")
            h3.string = node.get_text()
            cur.append(h3)
            out.append(cur)
            continue
        if cur is None:
            intro.append(node)
        else:
            cur.append(node)
    html = ""
    if any(str(n).strip() for n in intro):
        html += '<div class="intro">' + "".join(str(n) for n in intro) + "</div>"
    return html + "".join(str(c) for c in out)


def _section_cards(md: str, rename=None):
    """md 依 ## 切成 [(標題, html)]；rename 可改標題。"""
    soup = BeautifulSoup(_bh.Renderer("notes").render(md), "html.parser")
    for h1 in soup.find_all("h1"):
        h1.decompose()
    out, intro = [], []
    for node in list(soup.contents):
        if getattr(node, "name", None) == "h2":
            t = node.get_text(strip=True)
            out.append([(rename or {}).get(t, t), ""])
            continue
        if out:
            out[-1][1] += str(node)
        else:
            intro.append(str(node))
    return "".join(intro), out


def help_cards(md: str) -> str:
    """game_help_draft.md → 玩法說明：每個 ## 一張卡片（標題＝主要標題中文），規則說明列成清單，賠率表取中文表；
    不放 Game Meta、GAME RULE（一般條款）。大括號 {} 拿掉、走線圖佔位不放。"""
    import re
    def clean(t):
        return re.sub(r"[{}]", "", t).lstrip("▪").strip()
    secs = re.split(r"^## ", md, flags=re.M)[1:]
    rows, pay = [], []
    for sec in secs:
        head, _, body = sec.partition("\n")
        if head.strip().upper() in ("GAME META", "GAME RULE"):
            continue
        title, items, zh_col = head.strip(), [], None
        lines = body.splitlines()
        k = 0
        while k < len(lines):
            ln = lines[k].strip()
            if ln.startswith("### "):
                items.append(("h4", ln[4:].strip()))
            elif ln.startswith("| Item"):
                cols = [c.strip() for c in ln.strip("|").split("|")]
                zh_col = next((n for n, c in enumerate(cols) if c in ("繁中", "簡中", "中文")), 1)
            elif ln == "":
                zh_col = None   # 空行結束 Item 表；英文賠率表等其他表不讀
            elif ln.startswith("|") and not ln.startswith("| ---") and zh_col is not None:
                cells = [c.strip() for c in ln.strip("|").split("|")]
                kind, val = cells[0], cells[zh_col] if len(cells) > zh_col else ""
                if kind == "主要標題":
                    title = clean(val)
                elif kind == "副標題":
                    if items and items[-1][0] == "h4":
                        items[-1] = ("h4", clean(val))
                    else:
                        items.append(("h4", clean(val)))
                elif val and not val.startswith("[走線圖"):
                    items.append(("li", clean(val)))
            elif ln in ("繁中：", "簡中：", "中文："):
                tbl = []
                k += 1
                while k < len(lines) and (lines[k].strip().startswith("|") or not lines[k].strip()):
                    if lines[k].strip():
                        tbl.append(re.sub(r"[{}]", "", lines[k].strip()))
                    elif tbl:
                        break
                    k += 1
                items.append(("table", _bh.Renderer("notes").render("\n".join(tbl))))
                continue
            k += 1
        # 收成表格列（2026-11-09 使用者：卡片一節幾行看起來空，改成「項目｜說明」一張表）
        cur = [title, []]
        rows.append(cur)
        for kind, v in items:
            if kind == "li":
                cur[1].append(v)
            elif kind == "h4":
                if v == "賠率表":
                    continue
                name = v if v not in [r[0] for r in rows] else f"{title}－{v}"
                cur = [name, []]
                rows.append(cur)
            else:
                pay.append(v)
    rows = [r for r in rows if r[1]]
    html = ""
    if pay:   # 賠率表放最上面（2026-11-09 使用者）
        html += '<div class="card"><h3>賠率表</h3>' + "".join(pay) + "</div>"
    if rows:
        trs = "".join(f'<tr><td class="">{n}</td><td class=""><ul class="rules">{"".join(f"<li>{x}</li>" for x in v)}</ul></td></tr>' for n, v in rows)
        html += ('<div class="card"><h3>規則說明</h3><div class="tbl-wrap"><table><thead><tr><th>項目</th><th>說明</th></tr></thead>'
                 f'<tbody>{trs}</tbody></table></div></div>')
    return html


def other_cards(base: Path) -> str:
    """其他：上線觀察、開發注意事項、歷史錯誤紀錄（注意事項.md 的 一／二 兩節改名），沒有的不放。"""
    html = ""
    f = base / "上線觀察.md"
    if f.exists():
        intro, secs = _section_cards(f.read_text(encoding="utf-8"))
        html += '<div class="card"><h3>上線觀察</h3>' + intro + "".join(f"<h4>{t}</h4>{b}" for t, b in secs) + "</div>"
    f = base / "注意事項.md"
    if f.exists():
        _, secs = _section_cards(f.read_text(encoding="utf-8"),
                                 {"一、開發注意事項": "開發注意事項", "二、錯誤清單提醒": "歷史錯誤紀錄"})
        html += "".join(f'<div class="card"><h3>{t}</h3>{b}</div>' for t, b in secs)
    return html


def changelog_table(md: str) -> str:
    """修改紀錄：一張「版本｜修改內容」表，內容逐點列出（2026-11-09 使用者：一版一張卡片看起來空）。"""
    intro, secs = _section_cards(md)
    trs = ""
    for t, b in secs:
        frag = BeautifulSoup(b, "html.parser")
        for lst in frag.find_all(["ol", "ul"]):
            lst.name = "ul"
            lst["class"] = ["rules"]
        trs += f'<tr><td class="ver">{t}</td><td class="">{frag}</td></tr>'
    return (f'<div class="card"><h3>修改紀錄</h3>{intro}<div class="tbl-wrap"><table><thead><tr><th>版本</th><th>修改內容</th></tr></thead>'
            f"<tbody>{trs}</tbody></table></div></div>")


def _new_tab(soup, name, html):
    btn = soup.new_tag("button", attrs={"aria-selected": "false", "class": "tab", "role": "tab", "tabindex": "-1", "data-notes": "1"})
    btn.string = name
    sec = soup.new_tag("section", attrs={"class": "panel", "role": "tabpanel", "hidden": "", "data-notes": "1"})
    sec.append(BeautifulSoup(html, "html.parser"))
    return btn, sec


def inject(path):
    """玩法說明（第 2 頁，取 game_help_draft.md）、修改紀錄、其他（上線觀察＋注意事項）併成頁簽，最後重編頁簽號（2026-11-09 使用者定章節）。"""
    import re
    p = Path(path)
    soup = BeautifulSoup(p.read_text(encoding="utf-8"), "html.parser")
    for old in soup.select('[data-notes="1"]'):
        old.decompose()
    tabs = soup.select_one(".tabs")
    panels = soup.select(".panel")
    if tabs is None or not panels:
        print("skip（沒有頁簽結構）", p)
        return
    notes = p.parent / "個人筆記"
    added = []
    hp = p.parent / "game_help_draft.md"
    if hp.exists():
        h = help_cards(hp.read_text(encoding="utf-8"))
        if h:
            btn, sec = _new_tab(soup, "玩法說明", h)
            tabs.select(".tab")[0].insert_after(btn)
            panels[0].insert_after(sec)
            added.append("玩法說明")
    last = soup.select(".panel")[-1]
    tail = []
    if (notes / "修改紀錄.md").exists():
        tail.append(("修改紀錄", changelog_table((notes / "修改紀錄.md").read_text(encoding="utf-8"))))
    oth = other_cards(notes)
    if oth:
        tail.append(("其他", oth))
    for name, html in tail:
        btn, sec = _new_tab(soup, name, html)
        tabs.append(btn)
        last.insert_after(sec)
        last = sec
        added.append(name)
    for i, (t, pn) in enumerate(zip(tabs.select(".tab"), soup.select(".panel"))):
        t["id"], t["aria-controls"] = f"tab-{i}", f"panel-{i}"
        t["aria-selected"], t["tabindex"] = ("true", "0") if i == 0 else ("false", "-1")
        t.string = f"{i + 1}. " + re.sub(r"^\d+\.\s*", "", t.get_text(strip=True))
        pn["id"], pn["aria-labelledby"] = f"panel-{i}", f"tab-{i}"
        if i == 0:
            pn.attrs.pop("hidden", None)
        else:
            pn["hidden"] = ""
    # 自動頁簽的表格樣式對齊報告本身：數字格 class n → num（靠右、等寬字），表頭不另加
    for c in soup.select('[data-notes="1"] td.n, [data-notes="1"] th.n'):
        c["class"] = ["num"] if c.name == "td" else []
        if not c["class"]:
            del c["class"]
    p.write_text(str(soup), encoding="utf-8")
    print("notes", p, added)


if __name__ == "__main__":
    for a in sys.argv[1:]:
        inject(a)
