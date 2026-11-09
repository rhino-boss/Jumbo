# 統計表：每 1000 筆一列（累計），欄位：筆數 / RTP / BG RTP / FG RTP / Hit Rate / BG Hit Rate /
#         FG Hit Rate（以每一次 Free Spin 計）/ FG 觸發 / FG 週期 / Free Spin 次數
# 用法：python stats_table.py   -> data/統計表.xlsx
import os
import json
import glob
import pandas as pd
pd.set_option("display.width", 300)
pd.set_option("display.max_columns", 30)

BASE = os.path.dirname(os.path.abspath(__file__))
BULK = os.path.join(BASE, "data", "bulk")
STEP = 1000

rows = []
for p in glob.glob(os.path.join(BULK, "worker_*.jsonl")):
    with open(p, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                break
            b = r["body"]
            onces = b.get("onceResults") or []
            # onceResults[0] = Base 那一把；[1:] = 每一次 Free Spin
            bg_hit = bool(onces) and (onces[0].get("winCoins") or 0) > 0
            free = onces[1:]
            rows.append((r["t"], r["bet"] or 0, b.get("totalWin") or 0, b.get("totalWinBase") or 0,
                         b.get("totalWinFree") or 0, (b.get("initialFreeTimes") or 0) > 0,
                         bg_hit, len(free), sum((o.get("winCoins") or 0) > 0 for o in free)))
rows.sort()

out, n = [], 0
bet = win = wb = wf = hit = fg = bgh = fs = fsh = 0
bg_s = bg_s2 = fg_s = fg_s2 = 0.0   # 標準差用（以押注倍數計）
for t, b, w, xb, xf, isfg, h_bg, n_fs, h_fs in rows:
    n += 1
    bet += b; win += w; wb += xb; wf += xf; hit += w > 0; fg += isfg
    bgh += h_bg; fs += n_fs; fsh += h_fs
    x = xb / b if b else 0          # BG：每一把 spin 的 Base 贏分倍數
    bg_s += x; bg_s2 += x * x
    if isfg:                         # FG：每一場 FG 的總贏分倍數
        y = xf / b if b else 0
        fg_s += y; fg_s2 += y * y
    if n % STEP == 0 or n == len(rows):
        out.append({
            "筆數": n,
            "RTP": win / bet,
            "BG RTP": wb / bet,
            "FG RTP": wf / bet,
            "Hit Rate": hit / n,
            "BG Hit Rate": bgh / n,
            "FG Hit Rate": fsh / fs if fs else None,
            "FG 觸發次數": fg,
            "FG 週期 (1/N)": round(n / fg, 1) if fg else None,
            "Free Spin 次數": fs,
            "BG 標準差 (每把, x bet)": round(((bg_s2 - bg_s * bg_s / n) / (n - 1)) ** 0.5, 3) if n > 1 else None,
            "FG 標準差 (每場, x bet)": round(((fg_s2 - fg_s * fg_s / fg) / (fg - 1)) ** 0.5, 3) if fg > 1 else None,
            "FG 平均 (每場, x bet)": round(fg_s / fg, 3) if fg else None,
        })

df = pd.DataFrame(out)
path = os.path.join(BASE, "data", "統計表.xlsx")
with pd.ExcelWriter(path, engine="openpyxl") as w:
    df.to_excel(w, sheet_name="統計", index=False)
    ws = w.sheets["統計"]
    for col in "BCDEFG":
        for c in ws[col][1:]:
            c.number_format = "0.00%"
    for col, width in zip("ABCDEFGHIJKLM", (10, 11, 11, 11, 11, 13, 13, 13, 14, 14, 20, 20, 20)):
        ws.column_dimensions[col].width = width
print(df.to_string(index=False))
print("已輸出", path)
