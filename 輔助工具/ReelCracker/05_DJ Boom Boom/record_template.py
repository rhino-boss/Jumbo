# DJ BOOM BOOM 錄影 + 資料（給 AI 對照「表格 <-> 畫面」）
#
# 用法：python record_template.py [spins|bf|help|all] [把數]
#   all（預設）= 一般轉 10 把 + Buy Feature 4 種 + Help，各自一支 mp4，資料寫進同一份 Excel
#
# 輸出到 tempate/：
#   01_base_10spins.mp4
#   02_bf_x3.mp4 / 03_bf_x4.mp4 / 04_bf_x5.mp4 / 05_bf_x6.mp4
#   06_help.mp4
#   template_data.xlsx  -> 說明 / spin_summary / once_results / cascades / wins / reel_strips / 操作紀錄
#   每列都有 video 檔名 + 秒數（video_sec），可直接對到影片時間點

import os
import sys
import time
import json
import shutil
import datetime

import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from game_driver import launch, Game, Recorder  # noqa: E402

MODE = sys.argv[1] if len(sys.argv) > 1 else "all"
N_SPINS = int(sys.argv[2]) if len(sys.argv) > 2 else 10
OUT_DIR = os.path.join(BASE_DIR, "tempate")
FRAMES_ROOT = os.path.join(BASE_DIR, "_frames_tmp")
os.makedirs(OUT_DIR, exist_ok=True)

# 直式遊戲畫面內的相對座標
G = {
    "spin": (0.5, 0.833),        # Spin / FG 的 START 也在同一位置
    "buy": (0.497, 0.732),
    "bf_confirm": (0.68, 0.835),
    "menu": (0.852, 0.835),
    "help_i": (0.567, 0.832),
    "help_close": (0.5, 0.963),
}
BF_CARDS = {"x3": (0.31, 0.33), "x4": (0.69, 0.33), "x5": (0.31, 0.55), "x6": (0.69, 0.55)}

d = launch()
g = Game(d)
log = []        # 操作紀錄 [(video, video_sec, action)]
segments = []   # [(video_file, recorder, result_index_start, result_index_end)]


def cascades_of(body):
    return sum(len(o.get("fallenResults") or []) for o in body.get("onceResults") or [])


def has_fg(body):
    return bool(body.get("initialFreeTimes"))


def anim_wait(body):
    """依結果估計動畫時間（秒）"""
    onces = body.get("onceResults") or []
    base = onces[0] if onces else {}
    t = 2.5 + 1.8 * max(len(base.get("fallenResults") or []) - 1, 0)
    if body.get("winOdds", 0) >= 7:  # 大獎滾分
        t += 6
    return t


def fg_wait(body):
    onces = (body.get("onceResults") or [])[1:]
    return sum(2.4 + 1.6 * max(len(o.get("fallenResults") or []) - 1, 0) for o in onces) + 4


class Seg:
    def __init__(self, name):
        self.name = name
        self.rec = Recorder(d, os.path.join(FRAMES_ROOT, name))
        self.r0 = len(g.results)

    def __enter__(self):
        self.rec.start()
        time.sleep(1.5)
        return self

    def t(self):
        return round(time.time() - self.rec.start_ts, 2)

    def act(self, text):
        log.append({"video": self.name + ".mp4", "video_sec": self.t(), "action": text})
        print(f"  [{self.name} {self.t():6.1f}s] {text}")

    def __exit__(self, *a):
        time.sleep(1.5)
        self.rec.stop()
        g.poll()
        out = os.path.join(OUT_DIR, self.name + ".mp4")
        self.rec.to_mp4(out, crop=g.game_rect())
        segments.append((self.name + ".mp4", self.rec.start_ts, self.r0, len(g.results)))
        print(f"已輸出 {out}（{len(self.rec.frames)} 張畫面）")


def wait_result(n_before, timeout=12):
    end = time.time() + timeout
    while time.time() < end:
        g.poll()
        if len(g.results) > n_before:
            return g.results[-1][1]
        time.sleep(0.3)
    return None


def play_fg(seg, body):
    """FG：等 START 畫面出現 -> 按 START（確認有開始）-> 等 FG 跑完 -> 有結算看板就點掉 -> 回到主畫面"""
    t0 = time.time()
    while time.time() - t0 < 30 and not g.is_start_screen():
        time.sleep(0.7)
    time.sleep(1.0)
    for k in range(6):
        seg.act(f"按 START 開始 FG（{body.get('initialFreeTimes')} 次）" + (f"（重按 {k}）" if k else ""))
        g.click_game(*G["spin"])
        time.sleep(2.5)
        if not g.is_start_screen():
            break
    # 等 FG 自動跑完；超過預估時間還沒回主畫面 = 結算看板，點掉
    est = fg_wait(body) * 1.3 + 5
    t0, clicked, base_hits = time.time(), 0, 0
    while time.time() - t0 < est + 180:
        time.sleep(1.5)
        if g.is_base_screen():
            base_hits += 1
            if base_hits >= 2:
                break
            continue
        base_hits = 0
        if time.time() - t0 > est and clicked < 10:
            seg.act("FG 結束，點掉結算看板")
            g.click_game(*G["spin"])
            clicked += 1
            time.sleep(3)
    seg.act("回到主畫面")
    time.sleep(2)


MIN_WINS = 4        # 10 把裡至少幾把有中獎
MIN_CASCADES = 3    # 而且至少一把有連續消除（>= 3 段）
MAX_SPINS = 120     # 最多轉幾把


def _best_window(meta):
    """meta: [(spin_idx_in_results, body)]，回傳中獎最多的連續 N_SPINS 把起點 (score, start)"""
    best = (-1, 0)
    for s in range(0, len(meta) - N_SPINS + 1):
        w = [b for _, b in meta[s:s + N_SPINS]]
        wins = sum(1 for b in w if b.get("totalWin", 0) > 0)
        casc = max(cascades_of(b) for b in w)
        ok = wins >= MIN_WINS and casc >= MIN_CASCADES
        score = (1000 if ok else 0) + wins * 10 + min(casc, 6)
        best = max(best, (score, s))
    return best


def record_spins():
    """一直轉到「連續 N_SPINS 把裡有足夠中獎」，再把影片剪成那 N_SPINS 把"""
    import imageio_ffmpeg
    import subprocess
    raw_name = "01_base_raw"
    meta = []  # (results index, body, click_sec, events[(sec, text)])
    with Seg(raw_name) as seg:
        while len(meta) < MAX_SPINS:
            n0 = len(g.results)
            click_sec = seg.t()
            g.click_game(*G["spin"])
            body = wait_result(n0, timeout=5)
            if body is None:  # 這次點擊是在點掉看板，不是 spin
                if meta:
                    meta[-1][3].append((click_sec, "點掉滾分看板"))
                time.sleep(1.5)
                continue
            meta.append((len(g.results) - 1, body, click_sec, []))
            print(f"  第 {len(meta)} 把：贏 {body.get('totalWin')}，消除 {cascades_of(body)} 段")
            time.sleep(anim_wait(body))
            if has_fg(body):
                play_fg(seg, body)
            score, s = _best_window([(m[0], m[1]) for m in meta])
            if score >= 1000:
                time.sleep(6)  # 讓最後一把的動畫播完
                break
    # 選窗 & 剪片
    score, s = _best_window([(m[0], m[1]) for m in meta])
    win = meta[s:s + N_SPINS]
    raw_path = os.path.join(OUT_DIR, raw_name + ".mp4")
    v_start = max(win[0][2] - 0.5, 0)
    v_end = meta[s + N_SPINS][2] - 0.2 if s + N_SPINS < len(meta) else None
    out = os.path.join(OUT_DIR, "01_base_10spins.mp4")
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-ss", f"{v_start:.2f}", "-i", raw_path]
    if v_end:
        cmd += ["-t", f"{v_end - v_start:.2f}"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", out]
    subprocess.run(cmd, check=True)
    os.remove(raw_path)
    # segments / log 改成剪好的影片
    name, start_ts, _, _ = segments.pop()
    segments.append(("01_base_10spins.mp4", start_ts + v_start, win[0][0], win[-1][0] + 1))
    log[:] = [e for e in log if e["video"] != raw_name + ".mp4"]
    for k, (idx, body, csec, extra) in enumerate(win, 1):
        log.append({"video": "01_base_10spins.mp4", "video_sec": round(csec - v_start, 2), "action": f"按 Spin（第 {k} 把）"})
        for esec, text in extra:
            if v_end is None or esec < v_end:
                log.append({"video": "01_base_10spins.mp4", "video_sec": round(esec - v_start, 2), "action": text})
    wins = sum(1 for m in win if m[1].get("totalWin", 0) > 0)
    print(f"共轉 {len(meta)} 把，取第 {s + 1}~{s + N_SPINS} 把（中獎 {wins} 把）-> {out}")


def record_bf():
    for i, (name, pos) in enumerate(BF_CARDS.items()):
        t0 = time.time()
        while time.time() - t0 < 30 and not g.is_base_screen():  # 確定在主畫面才開始
            time.sleep(1)
        with Seg(f"{i + 2:02d}_bf_{name}") as seg:
            seg.act("按 Buy Feature")
            g.click_game(*G["buy"])
            time.sleep(2.5)
            seg.act(f"選 {name}（起始固定框 {name[1:]} 個）")
            g.click_game(*pos)
            time.sleep(1.5)
            n0 = len(g.results)
            seg.act("按確認購買")
            g.click_game(*G["bf_confirm"])
            body = wait_result(n0, timeout=15)
            if body is None:
                print("沒收到 BF 結果")
                continue
            seg.act(f"收到 BF 結果：FG {body.get('initialFreeTimes')} 次，總贏 {body.get('totalWin')}")
            time.sleep(3)
            play_fg(seg, body)


def record_help():
    with Seg("06_help") as seg:
        seg.act("按選單")
        g.click_game(*G["menu"])
        time.sleep(1.5)
        seg.act("按 i（Help）")
        g.click_game(*G["help_i"])
        time.sleep(6)
        x, y, w, h = g.game_rect()
        origin = ScrollOrigin.from_viewport(int(x + w / 2), int(y + h * 0.5))
        # 捲動直到畫面不再變（內文區比對，忽略小動畫）
        prev, same = None, 0
        for step in range(80):
            img = g.screen()
            if prev is not None and g._diff(img, prev, (0.0, 0.10, 1.0, 0.90)) < 3:
                same += 1
                if same >= 2:
                    break
            else:
                same = 0
            prev = img
            ActionChains(d).scroll_from_origin(origin, 0, 180).perform()
            time.sleep(1.3)
        seg.act("Help 到底，關閉")
        time.sleep(1.5)
        g.click_game(*G["help_close"])
        time.sleep(2)


# ---------------- Excel ----------------

def J(v):
    return json.dumps(v, ensure_ascii=False)


def build_excel(path):
    summary, onces_rows, cascades, wins = [], [], [], []
    for video, start_ts, r0, r1 in segments:
        for k in range(r0, r1):
            ts, body, bet, req = g.results[k]
            sid = k - segments[0][2] + 1  # 從錄影的第一把開始編號
            vsec = round(ts - start_ts, 2)
            onces = body.get("onceResults") or []
            summary.append({
                "spin_id": sid, "video": video, "video_sec": vsec,
                "bet": bet, "betMode": req.get("betMode"), "featureGameType": req.get("featureGameType"),
                "gameModes": J(body.get("gameModes")), "totalWin": body.get("totalWin"),
                "totalWinBase": body.get("totalWinBase"), "totalWinFree": body.get("totalWinFree"),
                "winOdds": body.get("winOdds"), "initialFreeTimes": body.get("initialFreeTimes"),
                "initialFreeFrame": J(body.get("initialFreeFrame")), "comboCount": body.get("comboCount"),
                "nOnceResults": len(onces), "userPoint": body.get("userPoint"),
            })
            for oi, once in enumerate(onces):
                frs = once.get("fallenResults") or []
                onces_rows.append({
                    "spin_id": sid, "video": video, "once": oi,
                    "type": "BASE/BUY 觸發盤" if oi == 0 else f"FG 第 {oi} 次",
                    "freeMode": once.get("freeMode"), "winCoins": once.get("winCoins"),
                    "nCascades": len(frs), "squeezeIndex": J(once.get("squeezeIndex")),
                    "firstPicture": J((frs[0].get("pictureInfo") or {}).get("picture")) if frs else "",
                })
                for ci, fr in enumerate(frs):
                    pi = fr.get("pictureInfo") or {}
                    cascades.append({
                        "spin_id": sid, "video": video, "once": oi, "cascade": ci,
                        "multiple": fr.get("multiple"), "beforeMultipleWinCoins": fr.get("beforeMultipleWinCoins"),
                        "fallenWinCoins": fr.get("fallenWinCoins"),
                        "picture": J(pi.get("picture")), "beforePicture": J(pi.get("beforePicture")),
                        "hit": J(pi.get("hit")), "wild": J(pi.get("wild")), "scatter": J(pi.get("scatter")),
                        "frame": J(pi.get("frame")), "frameHit": J(pi.get("frameHit")),
                    })
                    for nd in fr.get("normalDetail") or []:
                        wins.append({"spin_id": sid, "video": video, "once": oi, "cascade": ci,
                                     "multiple": fr.get("multiple"), "winSymbol": nd.get("winSymbol"),
                                     "winLength": nd.get("winLength"), "winWay": nd.get("winWay"),
                                     "winOdds": nd.get("winOdds"), "winCoins": nd.get("winCoins"),
                                     "winPicture": J(nd.get("winPicture"))})
    init = g.init_body() or {}
    strips = []
    for si, s in enumerate((init.get("probData") or {}).get("wheel") or []):
        for ri, strip in enumerate(s):
            strips.append({"set": si, "reel": ri + 1, "length": len(strip), "strip": J(strip)})
    readme = pd.DataFrame({"項目": [
        "資料來源", "金額單位", "盤面格式", "spin_summary", "once_results", "cascades", "wins",
        "video_sec", "操作紀錄", "BF 價格", "reel_strips"], "說明": [
        "FA CHAI DJ BOOM BOOM (GameID 22092) demo，WebSocket EV_SC_SPIN_RESULT 封包",
        "金額 ÷ 100 = 畫面顯示金額（bet 40 = 0.40）",
        "picture 等陣列 = 6 軸，每軸高度 3/4/5/5/4/3；軸內順序為由上到下（請對照影片確認）",
        "每次送出 spin / 購買一列（一般轉或 BF）",
        "每把裡面的每一次轉動：once=0 是觸發盤，之後是 FG 每一轉",
        "每次轉動裡的每一段消除；multiple = 該段倍數",
        "每段消除裡每個中獎組合；winSymbol = 符號 ID",
        "該筆結果從伺服器回來時，在影片中的秒數（約等於轉輪開始轉的時間）",
        "腳本每個操作（按 Spin / BF / START / Help）在影片中的秒數",
        "x3=bet×50、x4=bet×60、x5=bet×75、x6=bet×100（畫面 0.40 下為 20/24/30/40）",
        "輪帶（EV_SC_GAME_INIT.probData.wheel）"]})
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        readme.to_excel(w, sheet_name="說明", index=False)
        pd.DataFrame(summary).to_excel(w, sheet_name="spin_summary", index=False)
        pd.DataFrame(onces_rows).to_excel(w, sheet_name="once_results", index=False)
        pd.DataFrame(cascades).to_excel(w, sheet_name="cascades", index=False)
        pd.DataFrame(wins).to_excel(w, sheet_name="wins", index=False)
        pd.DataFrame(strips).to_excel(w, sheet_name="reel_strips", index=False)
        pd.DataFrame(log).to_excel(w, sheet_name="操作紀錄", index=False)
    print(f"已輸出 {path}")


if __name__ == "__main__":
    try:
        print("開遊戲...")
        g.open(load_wait=60)
        time.sleep(35)  # 開場載入畫面
        g.click_game(*G["spin"])  # 點掉開場畫面
        time.sleep(3)
        g.poll()
        if MODE in ("spins", "all"):
            record_spins()
        if MODE in ("bf", "all"):
            record_bf()
        if MODE in ("help", "all"):
            record_help()
        final = os.path.join(OUT_DIR, "template_data.xlsx")
        if MODE == "all" or not os.path.exists(final):
            build_excel(final)
        else:
            # 只重錄某段：新資料取代 Excel 裡同一支影片的列，其他影片的資料保留
            tmp = os.path.join(OUT_DIR, "_new.xlsx")
            build_excel(tmp)
            old = pd.read_excel(final, sheet_name=None)
            new = pd.read_excel(tmp, sheet_name=None)
            vids = set(new["spin_summary"]["video"])
            n_new = len(new["spin_summary"])
            merged = {}
            for k, v in old.items():
                if "video" in v.columns and k in new:
                    keep = v[~v["video"].isin(vids)].copy()
                    if "spin_id" in keep.columns:  # 重錄的放最前面，其他往後編號
                        keep["spin_id"] = keep["spin_id"].rank(method="dense").astype(int) + n_new
                    merged[k] = pd.concat([new[k], keep], ignore_index=True)
                else:
                    merged[k] = v
            with pd.ExcelWriter(final, engine="openpyxl") as w:
                for k, v in merged.items():
                    v.to_excel(w, sheet_name=k, index=False)
            os.remove(tmp)
            print(f"已合併進 {final}")
        shutil.rmtree(FRAMES_ROOT, ignore_errors=True)  # 成功才刪暫存畫面
    finally:
        d.quit()
