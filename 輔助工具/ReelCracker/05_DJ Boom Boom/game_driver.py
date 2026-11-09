"""DJ BOOM BOOM 共用工具：開遊戲、點擊、讀 WebSocket 結果、錄影（Chrome 畫面串流 -> mp4）"""
import os
import sys
import time
import json
import base64
import threading
import subprocess
import urllib.request

from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.actions.action_builder import ActionBuilder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from sfs_decode import decode_packet  # noqa: E402

TARGET_URL = "https://fachaigaming.com/en/games/slot/dj-boom-boom"

# 按鈕在遊戲 iframe 內的相對位置 (x, y)
POS = {
    "spin": (0.5, 0.83),
    "turbo": (0.39, 0.86),
    "plus": (0.548, 0.87),
    "minus": (0.452, 0.87),
    "menu": (0.601, 0.834),
    "buy": (0.5, 0.731),
    "center": (0.5, 0.40),
}


def launch(window=(1600, 1000)):
    path = os.path.join(BASE_DIR, "chromedriver-win64", "chromedriver.exe")
    service = Service(path) if os.path.exists(path) else Service()
    o = webdriver.ChromeOptions()
    o.add_argument(f"--window-size={window[0]},{window[1]}")
    o.add_argument("--force-device-scale-factor=1.0")
    o.add_argument("--mute-audio")
    # 視窗被蓋住時也持續繪製（錄影需要）
    o.add_argument("--disable-backgrounding-occluded-windows")
    o.add_argument("--disable-renderer-backgrounding")
    o.add_argument("--disable-background-timer-throttling")
    sw = {"disable_encoding": True,
          "exclude_hosts": ["google-analytics.com", "googletagmanager.com", "linkedin.com", "datadoghq.com",
                            "doubleclick.net", "googleapis.com", "gstatic.com", "google.com"]}
    drv = webdriver.Chrome(service=service, options=o, seleniumwire_options=sw)
    # 只記錄遊戲 WebSocket（spin 結果都在這），不記圖片等資源，讀取才會快
    drv.scopes = [r".*gs\.fcg666\.net.*"]
    return drv


class Game:
    def __init__(self, driver):
        self.d = driver
        self._seen = {}
        self.results = []   # [(recv_epoch, body, bet, cmd_params)]
        self.events = []    # 所有 extension 訊息 [(epoch, dir, cmd, payload)]
        self._last_send = None

    # ---------- 開遊戲 ----------
    def open(self, load_wait=60):
        d = self.d
        d.get(TARGET_URL)
        time.sleep(3)
        self._click_text("Yes")
        time.sleep(1)
        for el in d.find_elements(By.XPATH, "//button[normalize-space()='Play Now']"):
            d.execute_script("arguments[0].scrollIntoView({block:'center'})", el)
            time.sleep(0.5)
            el.click()
            break
        d.execute_script("window.scrollTo(0,0)")
        # 只隱藏 cookie 橫幅（不按 Accept）
        d.execute_script("document.querySelectorAll('[class*=cookie],[id*=cookie],[class*=consent],[id*=consent]')"
                         ".forEach(e=>e.style.display='none')")
        end = time.time() + load_wait
        while time.time() < end:  # 等到收到 GAME_INIT
            self.poll()
            if any(c == "EV_SC_GAME_INIT" for _, _, c, _ in self.events):
                break
            time.sleep(1)
        time.sleep(12)  # 載入畫面跑完

    def _click_text(self, text, timeout=15):
        end = time.time() + timeout
        while time.time() < end:
            for el in reversed(self.d.find_elements(By.XPATH, f"//body//*[normalize-space()='{text}']")):
                if el.is_displayed():
                    self.d.execute_script("arguments[0].click();", el)
                    return True
            time.sleep(0.5)
        return False

    # ---------- 點擊 ----------
    def iframe_rect(self):
        f = self.d.find_element(By.TAG_NAME, "iframe")
        return self.d.execute_script("const r=arguments[0].getBoundingClientRect();return [r.x,r.y,r.width,r.height]", f)

    def game_rect(self):
        """iframe 中間直式遊戲畫面範圍 (x, y, w, h)，給錄影裁切用。"""
        ix, iy, iw, ih = self.iframe_rect()
        gw = ih * 0.5625
        return ix + (iw - gw) / 2, iy, gw, ih

    def click(self, pos):
        if isinstance(pos, str):
            pos = POS[pos]
        ix, iy, iw, ih = self.iframe_rect()
        ab = ActionBuilder(self.d)
        ab.pointer_action.move_to_location(int(ix + iw * pos[0]), int(iy + ih * pos[1]))
        ab.pointer_action.pointer_down()
        ab.pointer_action.pause(0.1)
        ab.pointer_action.pointer_up()
        ab.perform()

    def click_game(self, gx, gy):
        """以直式遊戲畫面為基準的相對座標 (0~1) 點擊。"""
        x, y, w, h = self.game_rect()
        ab = ActionBuilder(self.d)
        ab.pointer_action.move_to_location(int(x + w * gx), int(y + h * gy))
        ab.pointer_action.pointer_down()
        ab.pointer_action.pause(0.1)
        ab.pointer_action.pointer_up()
        ab.perform()

    # ---------- 畫面狀態判斷（跟 ref/ 參考圖比對） ----------
    BUY_BOX = (0.30, 0.69, 0.70, 0.77)  # 主畫面 Buy Feature 按鈕區

    def screen(self):
        import io
        from PIL import Image
        img = Image.open(io.BytesIO(self.d.get_screenshot_as_png()))
        x, y, w, h = self.game_rect()
        return img.crop((int(x), int(y), int(x + w), int(y + h))).convert("L").resize((406, 721))

    @staticmethod
    def _diff(a, b, box=None):
        from PIL import ImageChops, ImageStat
        if box:
            W, H = a.size
            bb = (int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H))
            a, b = a.crop(bb), b.crop(bb)
        a, b = a.resize((60, 60)), b.resize((60, 60))
        return ImageStat.Stat(ImageChops.difference(a, b)).mean[0]

    def _ref(self, name):
        from PIL import Image
        if not hasattr(self, "_refs"):
            self._refs = {}
        if name not in self._refs:
            self._refs[name] = Image.open(os.path.join(BASE_DIR, "ref", name)).convert("L").resize((406, 721))
        return self._refs[name]

    def is_start_screen(self, img=None):
        """FG 的 START 畫面"""
        return self._diff(img or self.screen(), self._ref("start_screen.png")) < 15

    def is_base_screen(self, img=None):
        """主遊戲畫面（看得到 Buy Feature 按鈕；FG 中 / 對話框 / 看板都不算）"""
        return self._diff(img or self.screen(), self._ref("base_screen.png"), self.BUY_BOX) < 15

    # ---------- WebSocket ----------
    def poll(self):
        """解新進的 SmartFox 訊息；回傳新收到的 spin 結果數。"""
        n_new = 0
        for req in list(self.d.requests):
            ws = getattr(req, "ws_messages", None) or []
            start = self._seen.get(req.id, 0)
            for m in ws[start:]:
                if not isinstance(m.content, (bytes, bytearray)):
                    continue
                try:
                    pkt = decode_packet(bytes(m.content))
                except Exception:
                    continue
                if not isinstance(pkt, dict) or pkt.get("c") != 1 or pkt.get("a") != 13:
                    continue
                p = pkt.get("p") or {}
                ts = m.date.timestamp() if m.date else time.time()
                direction = "send" if m.from_client else "recv"
                self.events.append((ts, direction, p.get("c"), p.get("p")))
                if direction == "send" and p.get("c") == "EV_CS_SPIN":
                    self._last_send = p.get("p") or {}
                if direction == "recv" and p.get("c") == "EV_SC_SPIN_RESULT" and (p.get("p") or {}).get("body"):
                    req_p = self._last_send or {}
                    self.results.append((ts, p["p"]["body"], req_p.get("bet"), req_p))
                    n_new += 1
            self._seen[req.id] = len(ws)
        return n_new

    def init_body(self):
        for _, d_, c, p in self.events:
            if d_ == "recv" and c == "EV_SC_GAME_INIT" and p:
                return p.get("body")
        return None


class Recorder:
    """用 Chrome DevTools 的 Page.startScreencast 錄分頁畫面（含跨網域 iframe），存成 jpg 序列再轉 mp4。"""

    def __init__(self, driver, frames_dir):
        import websocket
        self.frames_dir = frames_dir
        os.makedirs(frames_dir, exist_ok=True)
        addr = driver.capabilities["goog:chromeOptions"]["debuggerAddress"]
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        targets = json.loads(opener.open(f"http://{addr}/json").read())
        page = next(t for t in targets if t.get("type") == "page" and "fachaigaming" in t.get("url", ""))
        self.ws = websocket.create_connection(page["webSocketDebuggerUrl"], suppress_origin=True,
                                              http_no_proxy=["localhost", "127.0.0.1"])
        self.frames = []  # [(epoch, path)]
        self._id = 0
        self._stop = threading.Event()
        self._t = None

    def _send(self, method, params=None):
        self._id += 1
        self.ws.send(json.dumps({"id": self._id, "method": method, "params": params or {}}))

    def start(self):
        self._send("Page.startScreencast", {"format": "jpeg", "quality": 85, "everyNthFrame": 1})
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()
        self.t0 = time.time()

    def _loop(self):
        self.ws.settimeout(1)
        while not self._stop.is_set():
            try:
                msg = json.loads(self.ws.recv())
            except Exception:
                continue
            if msg.get("method") == "Page.screencastFrame":
                p = msg["params"]
                ts = p["metadata"].get("timestamp") or time.time()
                path = os.path.join(self.frames_dir, f"f{len(self.frames):06d}.jpg")
                with open(path, "wb") as f:
                    f.write(base64.b64decode(p["data"]))
                self.frames.append((ts, path))
                try:
                    self._send("Page.screencastFrameAck", {"sessionId": p["sessionId"]})
                except Exception:
                    pass

    def stop(self):
        try:
            self._send("Page.stopScreencast")
        except Exception:
            pass
        time.sleep(0.5)
        self._stop.set()
        self._t.join(timeout=3)
        self.ws.close()

    @property
    def start_ts(self):
        return self.frames[0][0] if self.frames else self.t0

    def to_mp4(self, out_path, crop=None, fps=30):
        """crop = (x, y, w, h) 以 CSS px 計（scale factor 1）。"""
        import imageio_ffmpeg
        if not self.frames:
            raise RuntimeError("沒有錄到畫面")
        lst = os.path.join(self.frames_dir, "frames.txt")
        with open(lst, "w", encoding="utf-8") as f:
            for i, (ts, p) in enumerate(self.frames):
                dur = (self.frames[i + 1][0] - ts) if i + 1 < len(self.frames) else 1 / fps
                f.write(f"file '{p.replace(chr(92), '/')}'\nduration {max(dur, 0.001):.4f}\n")
            f.write(f"file '{self.frames[-1][1].replace(chr(92), '/')}'\n")
        vf = []
        if crop:
            x, y, w, h = [int(round(v)) for v in crop]
            vf.append(f"crop={w // 2 * 2}:{h // 2 * 2}:{x}:{y}")
        vf.append("scale=trunc(iw/2)*2:trunc(ih/2)*2")
        cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
               "-vf", ",".join(vf), "-r", str(fps), "-fps_mode", "cfr", "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-crf", "20", out_path]
        subprocess.run(cmd, check=True)
        return out_path
