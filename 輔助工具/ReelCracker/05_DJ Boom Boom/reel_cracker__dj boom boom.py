# %%
# DJ BOOM BOOM (FA CHAI, GameID 22092) 自動抓資料
#
# 用法（PowerShell / VS Code 終端機）：
#   python "reel_cracker__dj boom boom.py" 200          <- 轉 200 把
#   python "reel_cracker__dj boom boom.py" 200 2000     <- 轉 200 把，押注 bet=2000 (= 遊戲顯示 20.00)
#
# 原理：
#   - 遊戲在 iframe 裡，透過 SmartFoxServer WebSocket (wss://gs.fcg666.net/BlueBox/websocket) 溝通
#   - 送出 EV_CS_SPIN，回 EV_SC_SPIN_RESULT（內含完整盤面 / 每次消除 / 倍數 / 中獎明細 JSON）
#   - 進遊戲時的 EV_SC_GAME_INIT 內含輪帶 wheel、押注範圍、Buy Feature 價格
#   - sfs_decode.py 負責解 SmartFox 二進位封包
#
# 輸出到 data/（只輸出 Excel）：
#   spin_responses_<時間>.xlsx  (spin_summary / cascades / wins / reel_strips 四張表)

import sys
import os
import time
import json
import datetime

import pandas as pd
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.actions.action_builder import ActionBuilder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from sfs_decode import decode_packet  # noqa: E402


# %% 設定

TARGET_URL = "https://fachaigaming.com/en/games/slot/dj-boom-boom"
N_SPINS = int(sys.argv[1]) if len(sys.argv) > 1 else 50
TARGET_BET = int(sys.argv[2]) if len(sys.argv) > 2 else None  # None = 預設押注 40 (0.40)
CLICK_INTERVAL = 0.6    # 連點間隔秒數（動畫中點畫面會加速跳過）
TURBO_POS = (0.39, 0.86)  # 左下閃電「快速模式」按鈕
LOAD_WAIT = 60          # 等遊戲載入秒數
SAVE_EVERY = 50         # 每幾把存一次檔（防中途當掉）
SPIN_POS = (0.5, 0.83)  # Spin 按鈕在 iframe 內的相對位置 (x, y)
PLUS_POS = (0.548, 0.87)  # 「+」押注按鈕（TARGET_BET 有設定才會用到）

DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
STAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


# %% 開啟遊戲

chrome_driver_path = os.path.join(BASE_DIR, "chromedriver-win64", "chromedriver.exe")
service = Service(chrome_driver_path) if os.path.exists(chrome_driver_path) else Service()
options = webdriver.ChromeOptions()
options.add_argument("--window-size=1600,1000")
options.add_argument("--force-device-scale-factor=1.0")
options.add_argument("--mute-audio")
sw_options = {
    "disable_encoding": True,
    "exclude_hosts": ["google-analytics.com", "googletagmanager.com", "linkedin.com", "datadoghq.com",
                      "doubleclick.net", "googleapis.com", "gstatic.com", "google.com"],
}
driver = webdriver.Chrome(service=service, options=options, seleniumwire_options=sw_options)


def click_text(text, timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        for el in reversed(driver.find_elements(By.XPATH, f"//body//*[normalize-space()='{text}']")):
            if el.is_displayed():
                driver.execute_script("arguments[0].click();", el)
                return True
        time.sleep(0.5)
    return False


def open_game():
    driver.get(TARGET_URL)
    time.sleep(3)
    click_text("Yes")  # 18 歲確認
    time.sleep(1)
    for el in driver.find_elements(By.XPATH, "//button[normalize-space()='Play Now']"):
        driver.execute_script("arguments[0].scrollIntoView({block:'center'})", el)
        time.sleep(0.5)
        el.click()
        break
    driver.execute_script("window.scrollTo(0,0)")
    # 只隱藏 cookie 橫幅（不按 Accept），避免擋到遊戲下方按鈕
    driver.execute_script(
        "document.querySelectorAll('[class*=cookie],[id*=cookie],[class*=consent],[id*=consent]')"
        ".forEach(e=>e.style.display='none')")
    print(f"等待遊戲載入 {LOAD_WAIT} 秒...")
    time.sleep(LOAD_WAIT)


def iframe_rect():
    f = driver.find_element(By.TAG_NAME, "iframe")
    return driver.execute_script("const r=arguments[0].getBoundingClientRect();return [r.x,r.y,r.width,r.height]", f)


def click_frac(pos):
    ix, iy, iw, ih = iframe_rect()
    ab = ActionBuilder(driver)
    ab.pointer_action.move_to_location(int(ix + iw * pos[0]), int(iy + ih * pos[1]))
    ab.pointer_action.pointer_down()
    ab.pointer_action.pause(0.1)
    ab.pointer_action.pointer_up()
    ab.perform()


# %% 解析 WebSocket


def sfs_messages():
    """回傳 (dir, cmd, payload) 列表；只取 SmartFox extension 訊息 (c=1, a=13)。"""
    out = []
    for req in list(driver.requests):
        for m in (getattr(req, "ws_messages", None) or []):
            if not isinstance(m.content, (bytes, bytearray)):
                continue
            try:
                pkt = decode_packet(bytes(m.content))
            except Exception:
                continue
            if not isinstance(pkt, dict) or pkt.get("c") != 1 or pkt.get("a") != 13:
                continue
            p = pkt.get("p") or {}
            out.append(("send" if m.from_client else "recv", p.get("c"), p.get("p"), str(m.date)))
    return out


def J(v):
    return json.dumps(v, ensure_ascii=False)


def build_tables(spins, init_body):
    summary, cascades, wins = [], [], []
    for i, (t, body, bet) in enumerate(spins, 1):
        ext = body.get("extendData") or {}
        onces = body.get("onceResults") or []
        summary.append({
            "spin": i, "time": t, "bet": ext.get("originalBet", bet),
            "totalWin": body.get("totalWin"), "totalWinBase": body.get("totalWinBase"),
            "totalWinFree": body.get("totalWinFree"), "totalWinBonus": body.get("totalWinBonus"),
            "winOdds": body.get("winOdds"), "initialFreeTimes": body.get("initialFreeTimes"),
            "comboCount": body.get("comboCount"), "gameModes": J(body.get("gameModes")),
            "nOnceResults": len(onces), "nFreeSpins": sum(1 for o in onces if o.get("freeMode")),
            "luckyDraw": body.get("luckyDraw"), "userPoint": body.get("userPoint"),
        })
        for oi, once in enumerate(onces):
            for ci, fr in enumerate(once.get("fallenResults") or []):
                pi = fr.get("pictureInfo") or {}
                cascades.append({
                    "spin": i, "once": oi, "freeMode": once.get("freeMode"), "onceWin": once.get("winCoins"),
                    "cascade": ci, "multiple": fr.get("multiple"),
                    "beforeMultipleWinCoins": fr.get("beforeMultipleWinCoins"),
                    "fallenWinCoins": fr.get("fallenWinCoins"),
                    "picture": J(pi.get("picture")), "beforePicture": J(pi.get("beforePicture")),
                    "wild": J(pi.get("wild")), "scatter": J(pi.get("scatter")),
                    "frame": J(pi.get("frame")), "frameHit": J(pi.get("frameHit")), "hit": J(pi.get("hit")),
                    "squeezeIndex": J(once.get("squeezeIndex")),
                })
                for nd in fr.get("normalDetail") or []:
                    wins.append({"spin": i, "once": oi, "freeMode": once.get("freeMode"), "cascade": ci,
                                 "multiple": fr.get("multiple"), "winSymbol": nd.get("winSymbol"),
                                 "winLength": nd.get("winLength"), "winWay": nd.get("winWay"),
                                 "winOdds": nd.get("winOdds"), "winCoins": nd.get("winCoins"),
                                 "winLine": nd.get("winLine"), "winPicture": J(nd.get("winPicture"))})
    sheets = {"spin_summary": pd.DataFrame(summary), "cascades": pd.DataFrame(cascades), "wins": pd.DataFrame(wins)}
    wheel = ((init_body or {}).get("probData") or {}).get("wheel")
    if wheel:
        rows = []
        for si, strip_set in enumerate(wheel):
            for ri, strip in enumerate(strip_set):
                rows.append({"set": si, "reel": ri + 1, "length": len(strip), "strip": J(strip)})
        sheets["reel_strips"] = pd.DataFrame(rows)
    return sheets


_seen = {}      # request id -> 已處理的 ws 訊息數
_results = []   # 依序收到的 spin 結果 body


def poll_new_results():
    """只解新進的 WebSocket 訊息，回傳這次新收到的 spin 結果 body 列表。"""
    new = []
    for req in list(driver.requests):
        ws = getattr(req, "ws_messages", None) or []
        start = _seen.get(req.id, 0)
        for m in ws[start:]:
            if m.from_client or not isinstance(m.content, (bytes, bytearray)):
                continue
            try:
                pkt = decode_packet(bytes(m.content))
            except Exception:
                continue
            p = (pkt or {}).get("p") or {} if isinstance(pkt, dict) else {}
            if p.get("c") == "EV_SC_SPIN_RESULT" and (p.get("p") or {}).get("body"):
                new.append(p["p"]["body"])
        _seen[req.id] = len(ws)
    _results.extend(new)
    return new


def has_free_game(body):
    return bool(body.get("initialFreeTimes")) or any(o.get("freeMode") for o in body.get("onceResults") or [])


def save_all(limit=None):
    msgs = sfs_messages()
    init_body = next((p.get("body") for d_, c, p, _ in msgs if d_ == "recv" and c == "EV_SC_GAME_INIT" and p), None)
    spins, last_bet = [], None
    for d_, c, p, t in msgs:
        if d_ == "send" and c == "EV_CS_SPIN":
            last_bet = (p or {}).get("bet")
        elif d_ == "recv" and c == "EV_SC_SPIN_RESULT" and p and p.get("body"):
            spins.append((t, p["body"], last_bet))
    if limit:
        spins = spins[:limit]
    if not spins:
        print("還沒抓到 spin 結果")
        return 0
    sheets = build_tables(spins, init_body)
    with pd.ExcelWriter(os.path.join(DATA_DIR, f"spin_responses_{STAMP}.xlsx"), engine="openpyxl") as w:
        for name, df in sheets.items():
            df.to_excel(w, sheet_name=name, index=False)
    return len(spins)


# %% 主流程

if __name__ == "__main__":
    try:
        open_game()
        if TARGET_BET:
            # 從預設 40 往上按「+」直到目標押注（betRange: 40,80,120,200,400,...）
            rng = [40, 80, 120, 200, 400, 800, 1200, 2000, 4000, 8000, 12000, 20000, 40000, 80000, 100000]
            for _ in range(rng.index(TARGET_BET)):
                click_frac(PLUS_POS)
                time.sleep(0.8)
        # 連點 Spin（同時會點掉開場畫面、大獎滾分看板、FG 結算看板）直到收到 N_SPINS 筆結果
        # 快速模式：遊戲確定載入完（收到第 1 把結果）後按一次；
        #           FG 會把快速模式刷掉，所以 FG 那把之後收到下一把結果時再按一次
        clicks, last_saved, t0 = 0, 0, time.time()
        turbo_on, fg_pending, n_fg, n_turbo = False, False, 0, 0
        max_clicks = N_SPINS * 40
        while len(_results) < N_SPINS and clicks < max_clicks:
            click_frac(SPIN_POS)
            clicks += 1
            time.sleep(CLICK_INTERVAL)
            new = poll_new_results()
            if new and (not turbo_on or fg_pending):
                time.sleep(0.3)
                click_frac(TURBO_POS)
                n_turbo += 1
                turbo_on, fg_pending = True, False
            if any(has_free_game(b) for b in new):
                n_fg += sum(1 for b in new if has_free_game(b))
                fg_pending = True
                print(f"  第 {len(_results)} 把進 FG，FG 結束後會重按快速模式")
            if clicks % 20 == 0:
                rate = len(_results) / max(time.time() - t0, 1) * 60
                print(f"點擊 {clicks} 次，已收到 {len(_results)}/{N_SPINS} 把（{rate:.1f} 把/分，FG {n_fg} 次）")
            if len(_results) - last_saved >= SAVE_EVERY:
                save_all(N_SPINS)
                last_saved = len(_results)
        time.sleep(8)
        n = save_all(N_SPINS)
        print(f"完成：共 {n} 筆 spin 結果 -> {DATA_DIR}")
    finally:
        driver.quit()
