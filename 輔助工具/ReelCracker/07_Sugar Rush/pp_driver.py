"""Pragmatic Play 官方試玩（Gates of Olympus Super Scatter, vs20sugarrush）共用工具
遊戲結果走 HTTP POST .../gameService，回應是 a=1&b=2 形式的文字。"""
import os
import time
from urllib.parse import parse_qsl

from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GAME_URL = ("https://demogamesfree.pragmaticplay.net/hub-demo/openGame.do?lang=en&cur=USD"
            "&websiteUrl=https%3A%2F%2Fclienthub.pragmaticplay.com%2F&gcpif=2831&gameSymbol=vs20sugarrush"
            "&jurisdiction=99&lobbyUrl=https://clienthub.pragmaticplay.com/slots/game-library/")


def launch(window=(1280, 960)):
    drv_path = os.path.join(os.path.dirname(BASE_DIR), "05_DJ Boom Boom", "chromedriver-win64", "chromedriver.exe")
    service = Service(drv_path) if os.path.exists(drv_path) else Service()
    o = webdriver.ChromeOptions()
    o.add_argument(f"--window-size={window[0]},{window[1]}")
    o.add_argument("--force-device-scale-factor=1.0")
    o.add_argument("--mute-audio")
    o.add_argument("--disable-backgrounding-occluded-windows")
    o.add_argument("--disable-renderer-backgrounding")
    o.add_argument("--disable-background-timer-throttling")
    sw = {"disable_encoding": True,
          "exclude_hosts": ["google-analytics.com", "googletagmanager.com", "doubleclick.net", "google.com"]}
    d = webdriver.Chrome(service=service, options=o, seleniumwire_options=sw)
    d.scopes = [r".*gameService.*"]
    return d


def parse(text):
    return dict(parse_qsl(text, keep_blank_values=True))


class PPGame:
    def __init__(self, d):
        self.d = d
        self._seen = set()

    def open(self, wait=25):
        self.d.get(GAME_URL)
        time.sleep(wait)

    def key(self, k=Keys.SPACE):
        ActionChains(self.d).send_keys(k).perform()

    def click_rel(self, x, y):
        w = self.d.execute_script("return [innerWidth, innerHeight]")
        from selenium.webdriver.common.actions.action_builder import ActionBuilder
        ab = ActionBuilder(self.d)
        ab.pointer_action.move_to_location(int(w[0] * x), int(w[1] * y))
        ab.pointer_action.pointer_down()
        ab.pointer_action.pause(0.05)
        ab.pointer_action.pointer_up()
        ab.perform()

    def poll(self):
        """回傳新完成的 gameService 呼叫 [(ts, req_dict, res_text)]，依時間排序。"""
        out = []
        for r in list(self.d.requests):
            if r.id in self._seen or not r.response:
                continue
            self._seen.add(r.id)
            try:
                req = parse(r.body.decode("utf-8", "replace"))
                res = r.response.body.decode("utf-8", "replace")
            except Exception:
                continue
            req.pop("mgckey", None)
            out.append((r.date.timestamp(), req, res))
        if len(self._seen) > 500:
            del self.d.requests
            self._seen.clear()
        return sorted(out, key=lambda x: x[0])

