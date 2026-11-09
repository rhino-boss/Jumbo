import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pp_driver import launch, PPGame

N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
INTERVAL = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test")
os.makedirs(out, exist_ok=True)
d = launch()
g = PPGame(d)
g.open()
d.save_screenshot(os.path.join(out, "0_loaded.png"))
t0 = time.time()
rows = []
started = False
with open(os.path.join(out, "raw.jsonl"), "w", encoding="utf-8") as f:
    while time.time() - t0 < N:
        if not started:
            g.click_rel(0.862, 0.665)   # 開場說明的繼續（右側圓形箭頭）
            time.sleep(0.5)
        g.click_rel(0.81, 0.909)
        time.sleep(INTERVAL)
        for ts, req, res in g.poll():
            rows.append(req.get("action"))
            if req.get("action") == "doSpin" and not started:
                started = True
                print("first spin at", round(time.time() - t0), "s")
                time.sleep(1)
                g.click_rel(0.772, 0.979)  # 快速旋轉（AUTOPLAY 左邊的 >>）
                time.sleep(1)
                d.save_screenshot(os.path.join(out, "1_main.png"))
            f.write(json.dumps({"t": ts, "req": req, "res": res}, ensure_ascii=False) + "\n")
d.save_screenshot(os.path.join(out, "2_end.png"))
print(len(rows), "requests in", N, "s;", {a: rows.count(a) for a in set(rows)})
d.quit()
