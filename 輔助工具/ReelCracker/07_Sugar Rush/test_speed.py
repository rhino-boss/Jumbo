# 找 Pragmatic 的速度選項：點 >> 幾次、打開選單，各截一張圖
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pp_driver import launch, PPGame
from pp_bulk import SPIN, INTRO_NEXT, TURBO

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test_speed")
os.makedirs(out, exist_ok=True)
d = launch()
g = PPGame(d)
g.open(wait=5)
t0, started = time.time(), False
while not started and time.time() - t0 < 180:
    g.click_rel(*INTRO_NEXT)
    time.sleep(0.5)
    g.click_rel(*SPIN)
    time.sleep(1)
    started = any(req.get("action") == "doSpin" for _, req, _ in g.poll())
time.sleep(5)
d.save_screenshot(os.path.join(out, "0_before.png"))
for i in range(1, 4):
    g.click_rel(*TURBO)
    time.sleep(1.5)
    d.save_screenshot(os.path.join(out, f"{i}_turbo_click.png"))
g.click_rel(0.057, 0.912)   # 左下 ≡ 選單
time.sleep(2)
d.save_screenshot(os.path.join(out, "4_menu.png"))
d.quit()
print("ok")
