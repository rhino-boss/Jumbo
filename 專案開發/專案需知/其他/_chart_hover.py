"""倍率線型滑鼠提示：把 chart_hover.js 內嵌進網頁（<script id="chart-hover-auto">）。

用法：py -X utf8 _chart_hover.py <網頁.html> [...]
- 可重複執行：已內嵌的舊版先換掉。
- 只處理直接畫好的 SVG 折線圖；已有自己提示的圖（.chart[data-hover]、透明 rect 偵測層）腳本會自動略過。
- Demogame 不用跑：demogame_common.js 已帶同一份。
"""
import re
import sys
from pathlib import Path

JS = (Path(__file__).parent / "chart_hover.js").read_text(encoding="utf-8")
TAG = re.compile(r'\s*<script id="chart-hover-auto">.*?</script>', re.S)


def inject_text(html: str) -> str:
    html = TAG.sub("", html)
    block = f'<script id="chart-hover-auto">\n{JS}</script>\n'
    i = html.lower().rfind("</body>")
    return html[:i] + block + html[i:] if i >= 0 else html + block


def inject(path):
    p = Path(path)
    raw = p.read_bytes().decode("utf-8")
    crlf = "\r\n" in raw
    out = inject_text(raw.replace("\r\n", "\n"))
    p.write_bytes((out.replace("\n", "\r\n") if crlf else out).encode("utf-8"))
    print("chart-hover", p)


if __name__ == "__main__":
    for a in sys.argv[1:]:
        inject(a)
