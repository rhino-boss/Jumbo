"""
_survival.py — 數值報告「存活模擬」共用程式（所有遊戲同一套算法）

用法：
    py -X utf8 _survival.py <報表.xlsx> [<報表.xlsx> ...]

輸入：Simulator 的 Card-On 報表 xlsx（NB，betmode0）。

抽樣分布（取自 `Multiplier Line` 工作表，每局總得分 ÷ 底注）：
  - BG 非觸發局：base_game_cnt / base_game_pay。
      若 base_game_cnt 合計＝總局數（報表把觸發局也放進 base，例如 H016），
      則逐區間扣掉觸發把（bg_trigger_fg_cnt_lte_upper / _pay_lte_upper 為累計值，取差分）。
  - 觸發局（含觸發把）：free_game_cnt / free_game_pay（整場 FG 得分區間），
      每局得分＝抽中 FG 區間平均＋觸發把平均 BG 得分（Overview 的 bg_trigger_fg_pay ÷ cnt，
      或 Base Info 的 trigger_fg_bg_pay ÷ count）。
  - 抽中區間後取該區間平均得分。抽樣分布平均＝報表 NB Total RTP（程式會核對並印出差值）。
  - 底注單位自動判斷（coin_in 為每局／總投入，或得分已是倍數），以「各區間平均落在區間上下界內」挑選。

規則：
  - 1000 人各帶 1000 元、每把押 1 元，玩到餘額 < 1（不夠下注）為止。
  - 種子 1～6 各跑一次（每次 1000 人），比例取 6 次平均；每份報表各自用
    numpy.random.default_rng(seed)，不共用亂數流。
  - 「第 N 把仍存活」＝還能下第 N 把注（已下注把數 ≥ N）的人數比例。

輸出：第 1,000／5,000／10,000／20,000 把仍存活比例，附平均把數與中位數（6 次合併 6000 人）。
"""
import re
import sys

import numpy as np
import openpyxl

PLAYERS = 1000
BANKROLL = 1000.0
BET = 1.0
SEEDS = (1, 2, 3, 4, 5, 6)
CHECKPOINTS = (1000, 5000, 10000, 20000)
MAX_SPINS = 2_000_000  # 只為平均／中位數設安全上限
BLOCK = 4000


def _num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "")
    m = re.match(r"^-?[\d.]+(e-?\d+)?", s)
    if not m:
        return None
    x = float(m.group(0))
    return x / 100.0 if s.endswith("%") or "%" in s.split()[0] else x


def _info(wb):
    """讀 Overview 或 Base Info 的 key/value。"""
    for sn in ("Overview", "Base Info"):
        if sn in wb.sheetnames:
            return {r[0]: r[1] for r in wb[sn].iter_rows(values_only=True) if r and r[0] is not None}
    raise ValueError("找不到 Overview／Base Info 工作表")


def _bounds(label):
    s = str(label).strip()
    if s == "0":
        return 0.0, 0.0
    m = re.match(r"^\s*([\d.]+)\s*<\s*X\s*<=\s*([\d.]+)", s)
    if not m:
        raise ValueError(f"無法解析區間：{label}")
    return float(m.group(1)), float(m.group(2))


def build_distribution(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    info = _info(wb)
    rows = [r for r in wb["Multiplier Line"].iter_rows(values_only=True)]
    head = [str(h) if h is not None else "" for h in rows[0]]
    col = {h: i for i, h in enumerate(head)}
    body = [r for r in rows[1:] if r and r[0] is not None]

    def column(name):
        if name not in col:
            return np.zeros(len(body))
        return np.array([float(r[col[name]] or 0) for r in body])

    bounds = [_bounds(r[0]) for r in body]
    rounds = _num(info.get("total_rounds"))
    rtp_report = _num(info.get("rtp_total"))
    coin_in = _num(info.get("coin_in"))

    base_cnt, base_pay = column("base_game_cnt"), column("base_game_pay")
    fg_cnt, fg_pay = column("free_game_cnt"), column("free_game_pay")

    # 觸發把（累計 → 差分）
    cum_c, cum_p = column("bg_trigger_fg_cnt_lte_upper"), column("bg_trigger_fg_pay_lte_upper")
    trig_c = np.diff(np.concatenate([[0.0], cum_c]))
    trig_p = np.diff(np.concatenate([[0.0], cum_p]))
    trig_n = _num(info.get("bg_trigger_fg_cnt")) or _num(info.get("trigger_fg_bg_count")) or 0.0
    trig_pay = _num(info.get("bg_trigger_fg_pay")) or _num(info.get("trigger_fg_bg_pay")) or 0.0
    if fg_cnt.sum() > 0 and trig_n == 0 and cum_c.sum() > 0:
        trig_n, trig_pay = cum_c[-1], cum_p[-1]

    # base 是否含觸發局
    if fg_cnt.sum() > 0 and abs(base_cnt.sum() - rounds) < 0.5:
        if cum_c.sum() == 0:
            raise ValueError("base 含觸發局但報表沒有觸發把累計欄，無法扣除")
        base_cnt, base_pay = base_cnt - trig_c, base_pay - trig_p
    total_n = base_cnt.sum() + fg_cnt.sum()
    if abs(total_n - rounds) > 0.5:
        raise ValueError(f"非觸發局＋觸發局 {total_n:,.0f} ≠ 總局數 {rounds:,.0f}")

    # 底注單位：coin_in 為每局或總投入，挑讓各區間平均落在界內者
    bet_amt = _num(info.get("bet_amount"))
    cands = [coin_in, coin_in / rounds if coin_in else None, 1.0,
             coin_in / rounds / bet_amt if coin_in and bet_amt else None]
    cands = [u for u in cands if u]
    unit = None
    for u in cands:
        ok = True
        for (lo, hi), c, p in zip(bounds, base_cnt, base_pay):
            if c > 0:
                a = p / c / u
                if not (lo - 1e-6 <= a <= hi + 1e-6 if hi > 0 else abs(a) < 1e-9):
                    ok = False
                    break
        if ok:
            unit = u
            break
    if unit is None:
        raise ValueError(f"找不到一致的底注單位（coin_in={coin_in}）")

    trig_avg = trig_pay / trig_n / unit if trig_n else 0.0
    vals, cnts = [], []
    for c, p in zip(base_cnt, base_pay):
        if c > 0:
            vals.append(p / c / unit)
            cnts.append(c)
    for c, p in zip(fg_cnt, fg_pay):
        if c > 0:
            vals.append(p / c / unit + trig_avg)
            cnts.append(c)
    vals, cnts = np.array(vals), np.array(cnts)
    probs = cnts / cnts.sum()
    return {
        "values": vals,
        "probs": probs,
        "mean": float((vals * probs).sum()),
        "rtp_report": rtp_report,
        "rounds": rounds,
        "trig_rate": float(fg_cnt.sum() / rounds),
    }


def simulate(values, probs, seed):
    """回傳每位玩家已下注把數（int array）。"""
    rng = np.random.default_rng(seed)
    cdf = np.cumsum(probs)
    cdf[-1] = 1.0
    bal = np.full(PLAYERS, BANKROLL)
    spins = np.zeros(PLAYERS, dtype=np.int64)
    alive = np.arange(PLAYERS)
    done = 0
    while alive.size and done < MAX_SPINS:
        n = alive.size
        wins = values[np.searchsorted(cdf, rng.random((n, BLOCK)), side="right")]
        # 第 k 把後餘額 = bal - k*BET + 累計得分；能下第 k+1 把需 ≥ BET
        path = bal[alive, None] + np.cumsum(wins - BET, axis=1)
        before = np.concatenate([bal[alive, None], path[:, :-1]], axis=1)  # 下第 k 把前的餘額
        broke = before < BET - 1e-9
        has = broke.any(axis=1)
        first = np.where(has, broke.argmax(axis=1), BLOCK)
        spins[alive] += first
        bal[alive] = np.where(has, before[np.arange(n), np.minimum(first, BLOCK - 1)], path[:, -1])
        alive = alive[~has]
        done += BLOCK
    return spins


def run(path):
    d = build_distribution(path)
    res = np.zeros(len(CHECKPOINTS))
    all_spins = []
    for s in SEEDS:
        sp = simulate(d["values"], d["probs"], s)
        all_spins.append(sp)
        res += np.array([(sp >= n).mean() for n in CHECKPOINTS])
    res /= len(SEEDS)
    sp = np.concatenate(all_spins)
    return d, res, float(sp.mean()), float(np.median(sp))


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    for p in argv:
        d, res, mean, med = run(p)
        name = p.replace("\\", "/").split("/")[-1]
        diff = (d["mean"] - d["rtp_report"]) * 100
        flag = "OK" if abs(diff) < 0.05 else "不符，請檢查欄位"
        print(f"== {name}")
        print(f"   抽樣平均 {d['mean']*100:.4f}%｜報表 RTP {d['rtp_report']*100:.4f}%｜差 {diff:+.4f}pp {flag}"
              f"｜觸發率 {d['trig_rate']*100:.4f}%")
        print("   " + "｜".join(f"第 {n:,} 把 {r*100:.1f}%" for n, r in zip(CHECKPOINTS, res)))
        print(f"   平均把數 {mean:,.0f}｜中位數 {med:,.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
