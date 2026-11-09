# DJ BOOM BOOM 大量抓資料（多視窗並行）
#
# 用法：
#   python bulk_run.py 100000 4        <- 總共 10 萬把，同時開 4 個視窗
#   python bulk_run.py excel           <- 只把已抓到的資料轉成 Excel
#
# 資料即時寫在 data/bulk/worker_<n>.jsonl（每把一行），中斷後重跑會接著抓。
# 全部完成後輸出 data/spin_responses_bulk_<把數>.xlsx

import os
import sys
import json
import time
import glob
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
BULK_DIR = os.environ.get("BULK_DIR") or os.path.join(BASE_DIR, "data", "bulk")
os.makedirs(BULK_DIR, exist_ok=True)
PY = sys.executable

CLICK_INTERVAL = 0.6
SESSION_SPINS = 2000   # 每個瀏覽器最多轉幾把就重開（避免記憶體累積、餘額不足）
STALL_SEC = 90         # 這麼久沒新結果就重開


def count_lines(path):
    if not os.path.exists(path):
        return 0
    with open(path, "rb") as f:
        return sum(1 for _ in f)


# ---------------- worker ----------------

def worker(wid, target):
    from game_driver import launch, Game
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
            g = Game(d)
            g.open(load_wait=90)
            # 等主畫面（點掉開場畫面）
            t0 = time.time()
            while time.time() - t0 < 120 and not g.is_base_screen():
                g.click("spin")
                time.sleep(3)
            init = g.init_body()
            init_path = os.path.join(BULK_DIR, "game_init.json")
            if init and not os.path.exists(init_path):
                with open(init_path, "w", encoding="utf-8") as f:
                    json.dump(init, f, ensure_ascii=False)
            g.results.clear()
            turbo_on, fg_pending = False, False
            session, last_new = 0, time.time()
            with open(out, "a", encoding="utf-8") as f:
                while done < target and session < SESSION_SPINS:
                    g.click("spin")
                    time.sleep(CLICK_INTERVAL)
                    n = g.poll()
                    if n:
                        last_new = time.time()
                        for ts, body, bet, req in g.results[-n:]:
                            f.write(json.dumps({"t": ts, "w": wid, "bet": bet, "betMode": req.get("betMode"),
                                                "body": body}, ensure_ascii=False) + "\n")
                        f.flush()
                        done += n
                        session += n
                        # 快速模式：遊戲確定可轉後按一次；FG 會把它刷掉，FG 之後的下一把再按一次
                        # 快速模式有兩段，按兩次 = 最快
                        if not turbo_on or fg_pending:
                            time.sleep(0.3)
                            g.click("turbo")
                            time.sleep(0.5)
                            g.click("turbo")
                            if os.environ.get("DEBUG_SHOT"):
                                time.sleep(0.5)
                                d.save_screenshot(os.path.join(BULK_DIR, f"turbo_w{wid}_{done}.png"))
                            turbo_on, fg_pending = True, False
                        if any(b.get("initialFreeTimes") for _, b, _, _ in g.results[-n:]):
                            fg_pending = True
                        if len(g.results) > 200:
                            del g.results[:-50]
                    elif time.time() - last_new > STALL_SEC:
                        say("太久沒新結果，重開")
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


# ---------------- Excel ----------------

def J(v):
    return json.dumps(v, ensure_ascii=False)


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
                break  # 正在寫的最後一行
    return rows


def read_all():
    rows = []
    for p in sorted(glob.glob(os.path.join(BULK_DIR, "worker_*.jsonl"))):
        rows += read_worker(p)
    rows.sort(key=lambda r: r["t"])
    return rows


def build_excel(rows=None, path=None, first_id=1):
    import pandas as pd
    if rows is None:
        rows = read_all()
    summary, onces_rows, cascades, wins = [], [], [], []
    for sid, r in enumerate(rows, first_id):
        b = r["body"]
        onces = b.get("onceResults") or []
        summary.append({
            "spin_id": sid, "worker": r["w"], "time": time.strftime("%m-%d %H:%M:%S", time.localtime(r["t"])),
            "bet": r["bet"], "betMode": r.get("betMode"), "gameModes": J(b.get("gameModes")),
            "totalWin": b.get("totalWin"), "totalWinBase": b.get("totalWinBase"), "totalWinFree": b.get("totalWinFree"),
            "winOdds": b.get("winOdds"), "initialFreeTimes": b.get("initialFreeTimes"),
            "comboCount": b.get("comboCount"), "nOnceResults": len(onces), "userPoint": b.get("userPoint"),
        })
        for oi, once in enumerate(onces):
            frs = once.get("fallenResults") or []
            if oi > 0 or len(onces) > 1:
                onces_rows.append({"spin_id": sid, "once": oi, "freeMode": once.get("freeMode"),
                                   "winCoins": once.get("winCoins"), "nCascades": len(frs)})
            for ci, fr in enumerate(frs):
                pi = fr.get("pictureInfo") or {}
                cascades.append({
                    "spin_id": sid, "once": oi, "cascade": ci, "multiple": fr.get("multiple"),
                    "fallenWinCoins": fr.get("fallenWinCoins"), "beforeMultipleWinCoins": fr.get("beforeMultipleWinCoins"),
                    "picture": J(pi.get("picture")), "wild": J(pi.get("wild")), "frame": J(pi.get("frame")),
                    "hit": J(pi.get("hit")),
                })
                for nd in fr.get("normalDetail") or []:
                    wins.append({"spin_id": sid, "once": oi, "cascade": ci, "multiple": fr.get("multiple"),
                                 "winSymbol": nd.get("winSymbol"), "winLength": nd.get("winLength"),
                                 "winWay": nd.get("winWay"), "winOdds": nd.get("winOdds"), "winCoins": nd.get("winCoins")})
    s = pd.DataFrame(summary)
    bet_sum, win_sum = s["bet"].sum(), s["totalWin"].sum()
    stats = pd.DataFrame({"項目": ["總把數", "總押注", "總贏分", "RTP", "中獎把數", "中獎率", "觸發 FG 次數", "FG 觸發率",
                                   "Base 贏分", "FG 贏分", "最大單把贏分(倍)"],
                          "數值": [len(s), bet_sum / 100, win_sum / 100, f"{win_sum / bet_sum:.4%}",
                                 int((s.totalWin > 0).sum()), f"{(s.totalWin > 0).mean():.4%}",
                                 int((s.initialFreeTimes > 0).sum()), f"{(s.initialFreeTimes > 0).mean():.4%}",
                                 s.totalWinBase.sum() / 100, s.totalWinFree.sum() / 100,
                                 round((s.totalWin / s.bet).max(), 2)]})
    path = path or os.path.join(os.path.dirname(BULK_DIR), f"spin_responses_bulk_{len(s)}.xlsx")
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        stats.to_excel(w, sheet_name="統計", index=False)
        s.to_excel(w, sheet_name="spin_summary", index=False)
        pd.DataFrame(onces_rows).to_excel(w, sheet_name="fg_once_results", index=False)
        pd.DataFrame(cascades).to_excel(w, sheet_name="cascades", index=False)
        pd.DataFrame(wins).to_excel(w, sheet_name="wins", index=False)
        init_path = os.path.join(BULK_DIR, "game_init.json")
        if os.path.exists(init_path):
            init = json.load(open(init_path, encoding="utf-8"))
            strips = [{"set": si, "reel": ri + 1, "length": len(st), "strip": J(st)}
                      for si, ss in enumerate((init.get("probData") or {}).get("wheel") or []) for ri, st in enumerate(ss)]
            pd.DataFrame(strips).to_excel(w, sheet_name="reel_strips", index=False)
    print(f"已輸出 {path}（{len(s)} 把）")
    return path


# ---------------- 主程式 ----------------

if __name__ == "__main__":
    if sys.argv[1] == "excel":
        build_excel()
    elif sys.argv[1] == "worker":
        worker(int(sys.argv[2]), int(sys.argv[3]))
    else:
        total, n_workers = int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 4
        per = [total // n_workers + (1 if i < total % n_workers else 0) for i in range(n_workers)]
        procs = []
        for i, t in enumerate(per, 1):
            procs.append(subprocess.Popen([PY, os.path.abspath(__file__), "worker", str(i), str(t)],
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            time.sleep(20)  # 錯開啟動
        # 每滿 PART_SIZE 筆輸出一份 Excel（part_0001.xlsx ...），中斷也不會掉資料
        PART_SIZE = int(os.environ.get("PART_SIZE", "1000"))
        part_dir = os.path.join(os.path.dirname(BULK_DIR), "bulk_excel")
        os.makedirs(part_dir, exist_ok=True)
        state_path = os.path.join(BULK_DIR, "export_state.json")
        state = json.load(open(state_path)) if os.path.exists(state_path) else {"parts": 0, "upto": {}}

        def export_parts(final=False):
            while True:
                pending = []
                for i in range(1, n_workers + 1):
                    k = str(i)
                    for j, r in enumerate(read_worker(os.path.join(BULK_DIR, f"worker_{i}.jsonl"), state["upto"].get(k, 0))):
                        pending.append((r["t"], k, r))
                cutoff = time.time() - 30
                pending = sorted([p for p in pending if final or p[0] < cutoff], key=lambda x: x[0])
                if len(pending) < PART_SIZE and not (final and pending):
                    return
                chunk = pending[:PART_SIZE]
                state["parts"] += 1
                first_id = (state["parts"] - 1) * PART_SIZE + 1
                build_excel([r for _, _, r in chunk], os.path.join(part_dir, f"part_{state['parts']:04d}.xlsx"), first_id)
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
            print(f"{time.strftime('%m-%d %H:%M')} 進度 {done}/{total}（{rate:.0f} 把/分，預估剩 {eta / 60:.1f} 小時）", flush=True)
            export_parts()
        export_parts(final=True)
        build_excel()
