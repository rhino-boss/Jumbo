# Gates of Olympus Super Scatter 大量抓資料（多視窗並行）
#
# 用法：
#   python pp_bulk.py 100000 5      <- 總共 10 萬把（付費 spin），同時開 5 個視窗
#   python pp_bulk.py excel         <- 只把已抓到的資料轉成統計表
#
# 一把 = 一次付費 spin 加上它所有的消除（tumble）和 Free Spins，存成 data/bulk/worker_<n>.jsonl 的一行。
# 中斷後重跑會接著抓。每 1000 把輸出 data/bulk_excel/part_XXXX.xlsx。

import os
import sys
import json
import time
import glob
import subprocess
from urllib.parse import parse_qsl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
BULK_DIR = os.path.join(BASE_DIR, "data", "bulk")
os.makedirs(BULK_DIR, exist_ok=True)
PY = sys.executable

CLICK_INTERVAL = 0.35
SESSION_ROUNDS = 2000
STALL_SEC = 90
SPIN = (0.81, 0.909)        # 旋轉鈕（視窗相對位置）
INTRO_NEXT = (0.862, 0.665)  # 開場說明的繼續
TURBO = (0.772, 0.979)       # 快速旋轉 >>
ANYWHERE = (0.5, 0.45)       # 「Press anywhere to continue」畫面中間


CHEVRON3 = (0.7698, 0.9716, 0.7745, 0.9889)  # >> 第三個箭頭（亮 = 最快）


def is_fastest(d):
    import io
    from PIL import Image, ImageStat
    im = Image.open(io.BytesIO(d.get_screenshot_as_png())).convert("L")
    W, H = im.size
    box = (int(CHEVRON3[0] * W), int(CHEVRON3[1] * H), int(CHEVRON3[2] * W), int(CHEVRON3[3] * H))
    return ImageStat.Stat(im.crop(box)).mean[0] > 110


def ensure_fastest(g, d):
    """>> 有三段（1→2→3 個箭頭亮），點到第三段（最快）為止。"""
    for _ in range(4):
        if is_fastest(d):
            return True
        g.click_rel(*TURBO)
        time.sleep(1.2)
    return is_fastest(d)


def P(text):
    return dict(parse_qsl(text, keep_blank_values=True))


def num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0


def count_lines(path):
    if not os.path.exists(path):
        return 0
    with open(path, "rb") as f:
        return sum(1 for _ in f)


# ---------------- worker ----------------

def worker(wid, target):
    from pp_driver import launch, PPGame
    out = os.path.join(BULK_DIR, f"worker_{wid}.jsonl")
    log = os.path.join(BULK_DIR, f"worker_{wid}.log")

    def say(msg):
        with open(log, "a", encoding="utf-8") as f:
            f.write(time.strftime("%m-%d %H:%M:%S ") + msg + "\n")

    done = count_lines(out)
    while done < target:
        say(f"開瀏覽器（已完成 {done}/{target}）")
        d = None
        try:
            d = launch()
            g = PPGame(d)
            g.open(wait=5)
            started, session, last_new = False, 0, time.time()
            cur, prev_ntp = None, None   # 目前這一把的所有步驟
            with open(out, "a", encoding="utf-8") as f:
                while done < target and session < SESSION_ROUNDS:
                    if not started:
                        g.click_rel(*INTRO_NEXT)
                        time.sleep(0.5)
                    g.click_rel(*SPIN)
                    time.sleep(CLICK_INTERVAL)
                    if started and time.time() - last_new > 3:
                        # 有些遊戲（如 Sugar Rush）FG 開始/結束畫面要「點任意處繼續」，點旋轉鈕沒用
                        g.click_rel(*ANYWHERE)
                        time.sleep(0.2)
                    for ts, req, res in g.poll():
                        last_new = time.time()   # 有任何新回應就算有進度（長 FG 不會被誤判卡住）
                        act = req.get("action")
                        if act == "doInit":
                            init_path = os.path.join(BULK_DIR, "game_init.txt")
                            if not os.path.exists(init_path):
                                open(init_path, "w", encoding="utf-8").write(res)
                            continue
                        if act not in ("doSpin", "doCollect", "doBonus", "doCollectBonus"):
                            continue
                        r = P(res)
                        ntp = num(r.get("ntp"))
                        bet = round(num(req.get("c")) * num(req.get("l")), 2) if act == "doSpin" else 0
                        paid = act == "doSpin" and prev_ntp is not None and abs((prev_ntp - ntp) - bet) < 0.005 and bet > 0
                        if prev_ntp is None and act == "doSpin" and "rs_p" not in r and "fs" not in r:
                            paid = True   # 這個 session 的第一把
                        prev_ntp = ntp
                        if paid:
                            recheck = False
                            if cur:
                                f.write(json.dumps(cur, ensure_ascii=False) + "\n")
                                f.flush()
                                done += 1
                                session += 1
                                last_new = time.time()
                                # FG 結束後、或每 200 把，確認還在最快速度
                                recheck = any("fs_total=" in s["res"] for s in cur["steps"]) or session % 200 == 0
                            cur = {"t": ts, "w": wid, "bet": bet, "ntp0": ntp, "steps": []}
                            if not started:
                                started = True
                                time.sleep(1)
                                say(f"開始轉，最快速度：{ensure_fastest(g, d)}")
                            elif recheck:
                                time.sleep(0.5)
                                if not is_fastest(d):
                                    say(f"速度被重設，重新調最快：{ensure_fastest(g, d)}")
                        if cur is not None:
                            cur["steps"].append({"a": act, "res": res})
                            cur["ntp1"] = ntp
                    if started and time.time() - last_new > STALL_SEC:
                        shot = os.path.join(BULK_DIR, f"stall_w{wid}_{done}.png")
                        try:
                            d.save_screenshot(shot)
                        except Exception:
                            pass
                        say(f"太久沒新結果，重開（畫面存 {os.path.basename(shot)}）")
                        if cur and any(s["a"] == "doSpin" for s in cur["steps"]):
                            # 卡住的這把不能丟（多半是大獎 FG），標記後照存，贏分改用 tw
                            cur["stalled"] = True
                            f.write(json.dumps(cur, ensure_ascii=False) + "\n")
                            f.flush()
                            done += 1
                            say(f"卡住的那把已存（stalled），完成 {done}/{target}")
                        break
                    if not started and time.time() - last_new > 180:
                        say("遊戲載入失敗，重開")
                        break
            say(f"session 結束，完成 {done}/{target}")
        except Exception as e:
            say(f"錯誤：{type(e).__name__}: {e}")
            time.sleep(10)
        finally:
            if d:
                try:
                    d.quit()
                except Exception:
                    pass
    say("全部完成")


# ---------------- 解析一把 ----------------

def analyse(r):
    """回傳一把的摘要：bet, win, base_win, fg_win, fg(是否觸發), fs_hits, fs_count, base_hit"""
    bet = r["bet"]
    win = round(r.get("ntp1", r["ntp0"]) - r["ntp0"], 2)   # 這把總贏分（ntp0 已扣押注，ntp1 是收分後）
    if r.get("stalled"):   # 沒等到收分就卡住：用回應裡最大的 tw（本把累計贏分）
        win = max([num(P(s["res"]).get("tw")) for s in r["steps"] if s["a"] == "doSpin"] + [0])
    # Pragmatic 的 FG 標記（實測 Buy FG 確認）：
    #   觸發那把的回應帶 fs=1（表示下一把是第 1 次 Free Spin），中獎（含 scatter 給分）算 Base
    #   之後帶 fs=k 的回應 = 第 k-1 次 Free Spin 的結果（含它的消除）；最後一個帶 fs_total 的回應 = 最後一次 Free Spin
    #   fswin_total = 整場 FG 贏分；tw = Base + FG 總贏分
    base_w, fs_spin_win, fs_total_win = 0.0, {}, None
    fg = False
    for s in r["steps"]:
        if s["a"] != "doSpin":
            continue
        q = P(s["res"])
        w = num(q.get("w"))
        if "fs_total" in q:
            fg = True
            fs_spin_win["end"] = fs_spin_win.get("end", 0) + w
            fs_total_win = num(q.get("fswin_total"))
        elif "fs" in q and q.get("fs") != "1":
            fg = True
            fs_spin_win[q["fs"]] = fs_spin_win.get(q["fs"], 0) + w
        elif "fs" in q:            # fs=1：觸發那把（或觸發後的第一次 FG 結果，看是否已在 FG 中）
            if fg or "accm" in q:
                fs_spin_win["1"] = fs_spin_win.get("1", 0) + w
            else:
                base_w += w
                fg = True
        else:
            base_w += w
    if fg:
        fs_w = fs_total_win if fs_total_win is not None else max(win - base_w, 0)
    else:
        fs_w = 0.0
    return {"bet": bet, "win": win, "base_win": win - fs_w, "fg_win": fs_w, "fg": fg,
            "fs_count": len(fs_spin_win), "fs_hits": sum(1 for v in fs_spin_win.values() if v > 0),
            "base_hit": base_w > 0}


def read_worker(path, skip=0):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i < skip:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                break
    return rows


def read_all():
    rows = []
    for p in sorted(glob.glob(os.path.join(BULK_DIR, "worker_*.jsonl"))):
        rows += read_worker(p)
    rows.sort(key=lambda r: r["t"])
    return rows


def part_excel(rows, path, first_id):
    import pandas as pd
    summ, steps = [], []
    for sid, r in enumerate(rows, first_id):
        a = analyse(r)
        summ.append({"spin_id": sid, "worker": r["w"],
                     "time": time.strftime("%m-%d %H:%M:%S", time.localtime(r["t"])), **a,
                     "n_steps": len(r["steps"])})
        for i, s in enumerate(r["steps"]):
            steps.append({"spin_id": sid, "step": i, "action": s["a"], "response": s["res"]})
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        pd.DataFrame(summ).to_excel(w, sheet_name="spin_summary", index=False)
        pd.DataFrame(steps).to_excel(w, sheet_name="raw_steps", index=False)
    print("已輸出", path)


def stats_table(rows=None, step=1000):
    import pandas as pd
    rows = rows if rows is not None else read_all()
    out = []
    n = bet = win = wb = wf = hit = fg = bgh = fs = fsh = 0
    bg_s = bg_s2 = fg_s = fg_s2 = 0.0
    for r in rows:
        a = analyse(r)
        n += 1
        b = a["bet"]
        bet += b; win += a["win"]; wb += a["base_win"]; wf += a["fg_win"]
        hit += a["win"] > 0; fg += a["fg"]; bgh += a["base_hit"]; fs += a["fs_count"]; fsh += a["fs_hits"]
        x = a["base_win"] / b
        bg_s += x; bg_s2 += x * x
        if a["fg"]:
            y = a["fg_win"] / b
            fg_s += y; fg_s2 += y * y
        if n % step == 0 or n == len(rows):
            out.append({
                "筆數": n, "RTP": win / bet, "BG RTP": wb / bet, "FG RTP": wf / bet,
                "Hit Rate": hit / n, "BG Hit Rate": bgh / n, "FG Hit Rate": fsh / fs if fs else None,
                "FG 觸發次數": fg, "FG 週期 (1/N)": round(n / fg, 1) if fg else None, "Free Spin 次數": fs,
                "BG 標準差 (每把, x bet)": round(((bg_s2 - bg_s * bg_s / n) / (n - 1)) ** 0.5, 3) if n > 1 else None,
                "FG 標準差 (每場, x bet)": round(((fg_s2 - fg_s * fg_s / fg) / (fg - 1)) ** 0.5, 3) if fg > 1 else None,
                "FG 平均 (每場, x bet)": round(fg_s / fg, 3) if fg else None,
            })
    df = pd.DataFrame(out)
    path = os.path.join(BASE_DIR, "data", "統計表.xlsx")
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        df.to_excel(w, sheet_name="統計", index=False)
        ws = w.sheets["統計"]
        for col in "BCDEFG":
            for c in ws[col][1:]:
                c.number_format = "0.00%"
        for col, width in zip("ABCDEFGHIJKLM", (10, 11, 11, 11, 11, 13, 13, 13, 14, 14, 20, 20, 20)):
            ws.column_dimensions[col].width = width
    pd.set_option("display.width", 300)
    pd.set_option("display.max_columns", 30)
    print(df.tail(3).to_string(index=False))
    print("已輸出", path)


# ---------------- 主程式 ----------------

if __name__ == "__main__":
    if sys.argv[1] == "excel":
        stats_table()
    elif sys.argv[1] == "worker":
        worker(int(sys.argv[2]), int(sys.argv[3]))
    else:
        total, n_workers = int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 5
        per = [total // n_workers + (1 if i < total % n_workers else 0) for i in range(n_workers)]
        procs = []
        for i, t in enumerate(per, 1):
            procs.append(subprocess.Popen([PY, os.path.abspath(__file__), "worker", str(i), str(t)],
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            time.sleep(20)
        PART_SIZE = 1000
        part_dir = os.path.join(BASE_DIR, "data", "bulk_excel")
        os.makedirs(part_dir, exist_ok=True)
        state_path = os.path.join(BULK_DIR, "export_state.json")
        state = json.load(open(state_path)) if os.path.exists(state_path) else {"parts": 0, "upto": {}}

        def export_parts(final=False):
            while True:
                pending = []
                for i in range(1, n_workers + 1):
                    k = str(i)
                    for r in read_worker(os.path.join(BULK_DIR, f"worker_{i}.jsonl"), state["upto"].get(k, 0)):
                        pending.append((r["t"], k, r))
                cutoff = time.time() - 30
                pending = sorted([p for p in pending if final or p[0] < cutoff], key=lambda x: x[0])
                if len(pending) < PART_SIZE and not (final and pending):
                    return
                chunk = pending[:PART_SIZE]
                state["parts"] += 1
                part_excel([r for _, _, r in chunk], os.path.join(part_dir, f"part_{state['parts']:04d}.xlsx"),
                           (state["parts"] - 1) * PART_SIZE + 1)
                for _, k, _ in chunk:
                    state["upto"][k] = state["upto"].get(k, 0) + 1
                json.dump(state, open(state_path, "w"))

        t0, done0 = time.time(), None
        while any(p.poll() is None for p in procs):
            time.sleep(60)
            done = sum(count_lines(os.path.join(BULK_DIR, f"worker_{i}.jsonl")) for i in range(1, n_workers + 1))
            done0 = done if done0 is None else done0
            el = (time.time() - t0) / 60
            rate = (done - done0) / max(el - 1, 1)
            eta = (total - done) / max(rate, 0.1)
            print(f"{time.strftime('%m-%d %H:%M')} 進度 {done}/{total}（{rate:.0f} 把/分，預估剩 {eta / 60:.1f} 小時）",
                  flush=True)
            export_parts()
        export_parts(final=True)
        stats_table()
