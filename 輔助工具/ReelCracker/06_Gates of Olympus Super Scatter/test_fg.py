# 測試 FG 流程：用試玩幣買一次 Free Spins，照正式爬蟲的方式一直點旋轉鈕，記錄所有回應和畫面
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pp_driver import launch, PPGame
from pp_bulk import SPIN, INTRO_NEXT, TURBO

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test_fg")
os.makedirs(out, exist_ok=True)
d = launch()
g = PPGame(d)
g.open(wait=5)
t0 = time.time()
started = False
while not started and time.time() - t0 < 180:
    g.click_rel(*INTRO_NEXT)
    time.sleep(0.5)
    g.click_rel(*SPIN)
    time.sleep(1)
    started = any(req.get("action") == "doSpin" for _, req, _ in g.poll())
print("started", started, round(time.time() - t0))
time.sleep(4)
g.click_rel(*TURBO)
time.sleep(1)
g.click_rel(0.077, 0.124)       # BUY FREE SPINS
time.sleep(2)
d.save_screenshot(os.path.join(out, "a_dialog.png"))
g.click_rel(0.577, 0.608)       # 確認（勾勾）
time.sleep(3)
d.save_screenshot(os.path.join(out, "b_after_confirm.png"))
with open(os.path.join(out, "raw.jsonl"), "w", encoding="utf-8") as f:
    t1, k = time.time(), 0
    while time.time() - t1 < 200:
        g.click_rel(*SPIN)
        time.sleep(0.35)
        for ts, req, res in g.poll():
            f.write(json.dumps({"t": ts, "req": req, "res": res}, ensure_ascii=False) + "\n")
        if time.time() - t1 > k * 15:
            d.save_screenshot(os.path.join(out, f"c_{k:02d}.png"))
            k += 1
d.quit()
print("done")
