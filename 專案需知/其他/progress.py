# -*- coding: utf-8 -*-
"""遊戲專案工作進度表（Slots/H0xx_名稱/進度.md）。

用法（任何目錄皆可）：
    py progress.py H045          顯示進度條；該遊戲還沒有 進度.md 時依預設工項建立
    py progress.py H045 --init   只建立 進度.md（已存在則不動）

進度.md 是正式紀錄，工項可依遊戲自行增刪；本腳本只負責建立與顯示。
狀態欄規則（見 開發需知/開發流程.md §4.2）：空白＝未完成；`ok`＝使用者確認完成；
之後調整過就在同一列改成 `v2`、`v3`…，紀錄欄依序附日期與調整內容。
"""

import re
import sys
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SLOTS = Path(__file__).resolve().parents[2] / "Slots"

# (階段, 工項) — 依 開發流程 §4 製作順序與階段關卡
DEFAULT_ITEMS = [
    ("1 提案", "提案簡報 `.pptx`"),
    ("2 開案", "`game_rule.md`"),
    ("2 開案", "數學目標表與模型組合確認"),
    ("3.1 模型製作", "基礎數學模型 `H0xx1.xlsx`"),
    ("3.1 模型製作", "RTP／Variant 模型與 Card System 區間"),
    ("3.1 模型製作", "Config（`config*.js`）"),
    ("3.2 模擬程式", "`Simulator.py`"),
    ("3.2 模擬程式", "自然機率報表（Card Off 大場次）"),
    ("3.3 Demogame", "`index.html` 與 Simulator 單局對帳"),
    ("4 調性調整", "倍率權重校準"),
    ("4 調性調整", "Card-On 驗證報表"),
    ("4 調性調整", "數值報告"),
    ("5 後端對接", "交付 SPS（Config、Simulator）"),
    ("5 後端對接", "後端報表驗證"),
    ("5 後端對接", "腳本挑選"),
    ("6 文件製作", "`game_description.md`"),
    ("6 文件製作", "PARsheet"),
    ("6 文件製作", "Math Document Description（中英）"),
    ("6 文件製作", "`game_help_draft.md` → Help.xlsx"),
    ("6 文件製作", "Game Description"),
    ("7 文件檢查", "交付檔案全部檢查、版本凍結"),
    ("7 文件檢查", "`修改紀錄.md`、`注意事項.md`"),
]


def game_dir(code: str) -> Path:
    hits = sorted(p for p in SLOTS.glob(f"{code}_*") if p.is_dir())
    if not hits:
        sys.exit(f"找不到 Slots/{code}_* 專案資料夾")
    return hits[0]


def init(folder: Path) -> Path:
    path = folder / "進度.md"
    if path.exists():
        return path
    rows = "\n".join(f"| {stage} | {item} |  |  |" for stage, item in DEFAULT_ITEMS)
    path.write_text(
        f"# {folder.name} 工作進度\n\n"
        f"建立日期：{date.today():%Y-%m-%d}。工項可依本遊戲增刪；狀態欄：空白＝未完成、`ok`＝使用者確認完成、"
        "之後調整依序改為 `v2`、`v3`…，紀錄欄附日期與內容（規則見 專案需知/開發需知/開發流程.md §4.2）。\n\n"
        "| 階段 | 工項 | 狀態 | 紀錄 |\n|---|---|---|---|\n" + rows + "\n",
        encoding="utf-8")
    return path


def parse(path: Path):
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and line.startswith("|") and cells[0] not in ("階段",) and not set(cells[0]) <= set("-: "):
            items.append((cells[0], cells[1], cells[2]))
    return items


def show(folder: Path, path: Path):
    items = parse(path)
    done = sum(1 for _, _, st in items if st)
    total = len(items) or 1
    width = 30
    fill = round(width * done / total)
    print(f"{folder.name}  [{'█' * fill}{'░' * (width - fill)}] {done}/{len(items)}（{done / total:.0%}）")
    stage = None
    for st_name, item, st in items:
        if st_name != stage:
            stage = st_name
            print(f"  {stage}")
        mark = st if st else "  "
        print(f"    {'✓' if st else '·'} {item.replace('`', '')}{'  ' + mark if st else ''}")
    nxt = next(((s, i) for s, i, st in items if not st), None)
    print(f"下一項：{nxt[0]}／{nxt[1]}" if nxt else "全部完成")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    code = sys.argv[1].upper()
    folder = game_dir(code)
    path = init(folder)
    if "--init" not in sys.argv:
        show(folder, path)
