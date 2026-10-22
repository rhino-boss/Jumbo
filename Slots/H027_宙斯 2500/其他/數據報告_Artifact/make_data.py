"""把 數值報告_宙斯 2500.md 的表格轉成儀表板資料集（JSON 列物件）。百分比存成小數，「—」存 null。"""
import json
import re
from pathlib import Path

MD = Path(r"C:\Users\rhinshen\Mine\個人工作區\工作區\Slots\H027_宙斯 2500\其他\數值報告_宙斯 2500.md")
OUT = Path(__file__).parent
lines = MD.read_text(encoding="utf-8").split("\n")


def tables():
    """回傳 [(所在 ##/### 標題鏈, header, rows)]"""
    h2 = h3 = ""
    out, i = [], 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("## "):
            h2, h3 = l[3:].strip(), ""
        elif l.startswith("### "):
            h3 = l[4:].strip()
        elif l.startswith("|") and i + 1 < len(lines) and lines[i + 1].startswith("|---"):
            hdr = [c.strip() for c in l.strip().strip("|").split("|")]
            rows, i = [], i + 2
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append((h2, h3, hdr, rows))
            continue
        i += 1
    return out


def num(s):
    s = s.replace(",", "").replace("**", "").strip()
    if s in ("—", "-", ""):
        return None
    m = re.fullmatch(r"([+-]?[\d.]+)\s*(%|x|pp| 局| 次)?", s.replace(" pp", "pp"))
    if not m:
        return s
    v = float(m.group(1))
    return round(v / 100, 6) if m.group(2) in ("%", "pp") else v


T = tables()
pick = lambda h2, h3, k=0: [t for t in T if t[0].endswith(h2) and t[1] == h3][k]
G = {"Gates of Olympus 1000": "goo", "Zeus 2500 A": "a", "Zeus 2500 B": "b"}
data = {}

# 核心指標：值有 %、1/x、x 三種格式，另存 fmt 欄
_, _, hdr, rows = pick("核心指標", "")
core = []
for r in rows:
    fmt = "period" if r[1].startswith("1/") else ("x" if r[1].endswith("x") else "pct")
    conv = (lambda s: float(s[2:].replace(",", ""))) if fmt == "period" else num
    core.append({"metric": r[0], "fmt": fmt, "goo": conv(r[1]), "a": conv(r[2]), "b": conv(r[3])})
data["core"] = core

# 玩法深淺＋存活
_, _, hdr, rows = pick("基本資訊", "玩法深淺")
surv = {r[0]: r for r in pick("基本資訊", "存活模擬")[3]}
depth = []
for r in rows:
    s = surv.get(r[1]) if r[0] == "NB" else None
    depth.append({"row": f"{r[0]} {r[1]}", "mode": r[0], "game": r[1], "rtp": num(r[2]), "std": num(r[3]),
                  "p1000": num(r[4]), "p5000": num(r[5]), "p10000": num(r[6]), "max": num(r[7]),
                  "surv_mean": num(s[1]) if s else None, "surv_median": num(s[2]) if s else None,
                  "surv_p10": num(s[3]) if s else None, "surv_p90": num(s[4]) if s else None})
data["depth"] = depth

# 倍數球：出現率＋倍數值分布
balls = []
for r in pick("倍數球", "出現率與週期")[3]:
    balls.append({"key": f"rate|{r[0]}", "kind": "rate", "scene": r[0], "mult": None,
                  "goo": num(r[1]), "a": num(r[2]), "b": num(r[3])})
for sc in ("BG", "FG", "BF"):
    for r in pick("倍數球", f"倍數值分布 — {sc}")[3]:
        balls.append({"key": f"dist|{sc}|{r[0]}", "kind": "dist", "scene": sc, "mult": r[0],
                      "goo": num(r[1]), "a": num(r[2]), "b": num(r[3])})
data["balls"] = balls

# FG／BF 全程門檻機率
_, _, hdr, rows = pick("倍率線型", "")
data["fg_threshold"] = [{"threshold": r[0], "x": float(r[0][1:].replace(",", "").rstrip("x")),
                         "goo_fg": num(r[1]), "a_fg": num(r[2]), "b_fg": num(r[3]),
                         "goo_bf": num(r[4]), "a_bf": num(r[5]), "b_bf": num(r[6])} for r in rows]

# 連消分布（全部）＋有無倍數球
combo = []
for sc in ("BG", "FG", "BF"):
    for r in pick("連消分布", sc)[3]:
        combo.append({"key": f"{sc}|全部|{r[0]}", "scene": sc, "cond": "全部", "combo": r[0],
                      "goo": num(r[1]), "a": num(r[2]), "b": num(r[4])})
_, _, hdr, rows = pick("有無倍數球的消除分布", "")
tmp = {}
for r in rows:
    for j, c in enumerate(["Hit Rate", "0", "1", "2", "3", "4", "5+"]):
        k = (r[0], r[1], c)
        tmp.setdefault(k, {"key": f"{r[0]}|{r[1]}|{c}", "scene": r[0], "cond": r[1], "combo": c})[G[r[2]]] = num(r[3 + j])
combo += list(tmp.values())
data["combo"] = combo

# 獎項占比
cl = []
for sc in ("BG", "FG", "BF"):
    for r in pick("獎項占比", sc)[3]:
        cl.append({"key": f"{sc}|{r[0]}", "scene": sc, "size": r[0].replace(" 連線", ""),
                   "goo_cnt": num(r[1]), "a_cnt": num(r[2]), "b_cnt": num(r[3]),
                   "goo_pay": num(r[4]), "a_pay": num(r[5]), "b_pay": num(r[6])})
data["cluster"] = cl

for k, v in data.items():
    (OUT / f"{k}.json").write_text(json.dumps(v, ensure_ascii=False, indent=0), encoding="utf-8")
    print(k, len(v), v[0])
