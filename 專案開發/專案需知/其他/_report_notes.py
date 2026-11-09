"""把遊戲 個人筆記/ 的修改紀錄、注意事項、上線觀察併進數值報告 report.html，各成一個頁簽（2026-11-03 使用者定）。

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


def inject(path):
    p = Path(path)
    soup = BeautifulSoup(p.read_text(encoding="utf-8"), "html.parser")
    for old in soup.select('[data-notes="1"]'):
        old.decompose()
    tabs = soup.select_one(".tabs")
    panels = soup.select(".panel")
    if tabs is None or not panels:
        print("skip（沒有頁簽結構）", p)
        return
    n = len(tabs.select(".tab"))
    last = panels[-1]
    added = []
    for name, fn in NOTES:
        md_path = p.parent / "個人筆記" / fn
        if not md_path.exists():
            continue
        btn = soup.new_tag("button", attrs={
            "aria-controls": f"panel-{n}", "aria-selected": "false", "class": "tab", "id": f"tab-{n}",
            "role": "tab", "tabindex": "-1", "data-notes": "1"})
        btn.string = f"{n + 1}. {name}"
        tabs.append(btn)
        sec = soup.new_tag("section", attrs={
            "aria-labelledby": f"tab-{n}", "class": "panel", "id": f"panel-{n}", "role": "tabpanel",
            "hidden": "", "data-notes": "1"})
        sec.append(BeautifulSoup(md_to_cards(md_path.read_text(encoding="utf-8")), "html.parser"))
        last.insert_after(sec)
        last = sec
        added.append(name)
        n += 1
    p.write_text(str(soup), encoding="utf-8")
    print("notes", p, added)


if __name__ == "__main__":
    for a in sys.argv[1:]:
        inject(a)
