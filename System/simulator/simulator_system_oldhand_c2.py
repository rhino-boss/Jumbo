# -*- coding: utf-8 -*-
"""老手救援 C-2 版模擬器。

讀取 rowdata/ 的固定自然 Row Data（1000 名老手玩家 × 1000 轉），
套用 C-2 機制後輸出：

* RTP：沒有機制 %（+機制增加 RTP%）
* 10 個觸發點（當日第 40, 80, ..., 400 轉）：
    - 觸發率 = 該觸發點觸發次數 ÷ 該觸發點判定次數
    - 當下原來 RTP%（+機制增加 RTP%）
* 總體用到救援的玩家比例 = 有用到救援的玩家不重複數 ÷ 總玩家數
* 觸發率（總） = 判定成功次數 ÷ 總判定次數

C-2 規則（機制說明_老手救援C-2版.html）：
* 以天為循環；本模擬以每人 800 轉為一日（SPINS_PER_DAY）。
* 每 40 轉一個觸發區間（觸發點前後 5 轉，例如 35–45、75–85），每人每天在區間內
  均勻隨機挑一轉判定「當日累積 RTP」，且須同時符合前 40 轉 RTP < 50%；
  判定回合本身不納入統計（沿用 C 版口徑）。
* 10 個觸發點各訂 RTP 門檻與救援倍數（見 CHECKPOINT_RULES），
  倍數由 20× 隨落點遞增至 100×
* 救援落在判定回合：該轉最終得分 = max(自然得分, 救援倍數 × Bet)，
  成本以增量記帳。
* 延伸救援（當日 440–1,000 轉）：沿用主救援第 395–405 轉那一段的設定——觸發點前後 5 轉
  隨機判定、前 40 轉 RTP < 50%、救 100×；只把「當日累積 RTP」換成「往前抓 400 轉 RTP < 65%」。
* 救援倍數對應卡片區間（例：100× → (90, 100]），模擬一律以區間上限計，屬保守估計。
* 尚未套用救援池／共同池上限（先量測機制的自然增量，供預算評估）。
"""

from __future__ import annotations

import gzip
import time
from pathlib import Path

import numpy as np
import pandas as pd

SYSTEM_VERSION = "c2-1.8"


def _locate_script_dir() -> Path:
    """定位 System 資料夾；避免 Jupyter 沿用其他檔案的 __file__ 或舊工作目錄。"""

    candidates: list[Path] = []
    try:
        file_path = Path(__file__).resolve()
        if file_path.name == "simulator_system_oldhand_c2.py":
            candidates.append(file_path.parent)
    except NameError:
        pass

    current = Path.cwd().resolve()
    for base in (current, *current.parents):
        candidates.extend((base / "System", base))

    # 程式放在 System/simulator/，rowdata 在上一層 System/rowdata/
    for candidate in candidates:
        for base in (candidate, candidate.parent):
            rowdata = base / "rowdata"
            if rowdata.is_dir() and any(rowdata.glob("*人_1000轉.csv.gz")):
                return base.resolve()

    raise FileNotFoundError("找不到 System/rowdata/；請將工作目錄切到 工作區 或 System 底下")


SCRIPT_DIR = _locate_script_dir()
ROWDATA_DIR = SCRIPT_DIR / "rowdata"

# 使用的自然 Row Data（老手基礎，無機制）：
ROWDATA_FILES = {
    "超級寶石": "超級寶石_基礎遊戲_10000人_1000轉.csv.gz",
    "彩罐熱舞": "彩罐熱舞_基礎遊戲_10000人_1000轉.csv.gz",
}
GAMES = ["超級寶石", "彩罐熱舞"]

# ---- C-2 參數 ----
SPINS_PER_DAY = 800                           # 模擬基準：每人一日轉數
CHECKPOINT_INTERVAL = 40                      # SPS 最小監測單位
MAIN_SHORT_WINDOW = 40                        # 主救援共同短期窗口
MAIN_SHORT_THRESHOLD = 0.50                   # 前 40 轉 RTP < 50%

# 觸發點 →（當日累積 RTP 門檻, 救援倍數）；10 個觸發點各訂門檻
CHECKPOINT_RULES: dict[int, tuple[float, float]] = {
    40:  (0.25, 25.0),
    80:  (0.30, 50.0),
    120: (0.35, 70.0),
    160: (0.40, 80.0),
    200: (0.45, 90.0),
    240: (0.50, 100.0),
    280: (0.55, 100.0),
    320: (0.55, 100.0),
    360: (0.60, 100.0),
    400: (0.65, 100.0),
}
CHECKPOINTS = sorted(CHECKPOINT_RULES)
CHECKPOINT_JITTER = 5                         # 觸發點前後 5 轉內隨機挑一轉判定
MAIN_SEED = 20261008

# ---- 延伸救援（當日 401–1,000 轉）----
EXT_CHECKPOINTS = list(range(440, 1001, 40))  # 440 起每 40 轉，前後 5 轉隨機判定
EXT_MID_WINDOW = 400                          # 往前抓 400 轉
EXT_MID_THRESHOLD = 0.65                      # 同第 395–405 轉的門檻
EXT_SHORT_WINDOW = 40                         # 前 40 轉
EXT_SHORT_THRESHOLD = 0.50                    # 同主救援條件 1
EXT_REWARD = 100.0                            # 同第 395–405 轉：100×（卡片區間 (90, 100]）
EXT_SEED = 20261005


def band_of(spin_no: int) -> tuple[float, float]:
    return CHECKPOINT_RULES[spin_no]


def judge_spins(n_players: int, rng: np.random.Generator, checkpoints=None) -> dict[int, np.ndarray]:
    """每人每個觸發點的判定轉數（1-based），在 [觸發點 − 5, 觸發點 + 5] 均勻隨機。"""
    cps = CHECKPOINTS if checkpoints is None else checkpoints
    return {cp: cp + rng.integers(-CHECKPOINT_JITTER, CHECKPOINT_JITTER + 1, n_players) for cp in cps}


def apply_ext(nat: np.ndarray, bet: np.ndarray, adj: np.ndarray,
              spins: dict[int, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """在已套主救援的 adj 上套延伸救援，回傳 (adj, reward_at)。

    條件：前 40 轉 RTP < 50% 且往前 400 轉 RTP < 65%，命中救 100×；
    判定轉超出資料長度（玩家當天沒玩到）就不判定。
    """
    n, length = nat.shape
    rows = np.arange(n)
    adj = adj.copy()
    reward_at = np.zeros_like(nat)
    zeros = np.zeros((n, 1))
    cs_b = np.concatenate([zeros, np.cumsum(bet, axis=1)], axis=1)
    for cp in EXT_CHECKPOINTS:
        s = spins[cp]
        played = s <= length
        if not played.any():
            break
        k = np.minimum(s, length) - 1
        cs_a = np.concatenate([zeros, np.cumsum(adj, axis=1)], axis=1)
        mid_lo = np.maximum(0, k - EXT_MID_WINDOW)
        short_lo = np.maximum(0, k - EXT_SHORT_WINDOW)
        mid = (cs_a[rows, k] - cs_a[rows, mid_lo]) / (cs_b[rows, k] - cs_b[rows, mid_lo])
        short = (cs_a[rows, k] - cs_a[rows, short_lo]) / (cs_b[rows, k] - cs_b[rows, short_lo])
        hit = played & (mid < EXT_MID_THRESHOLD) & (short < EXT_SHORT_THRESHOLD)
        natural = nat[rows, k]
        adj[rows, k] = np.where(hit, np.maximum(natural, EXT_REWARD * bet[rows, k]), natural)
        reward_at[rows[hit], k[hit]] = EXT_REWARD
    return adj, reward_at


def apply_main(nat: np.ndarray, bet: np.ndarray, spins: dict[int, np.ndarray],
               skip: tuple[int, ...] = ()) -> tuple[np.ndarray, np.ndarray]:
    """套用主救援，回傳 (adj, reward_at)。

    adj 為套機制後每轉得分；reward_at[p, i] 為該轉觸發的救援倍數（0 = 未觸發）。
    判定轉超出資料長度（玩家當天沒玩到）就不判定；skip 內的觸發點停用。
    觸發區間彼此不重疊，所以依序處理即可。
    """
    n, length = nat.shape
    rows = np.arange(n)
    adj = nat.copy()
    reward_at = np.zeros_like(nat)
    zeros = np.zeros((n, 1))
    cs_b = np.concatenate([zeros, np.cumsum(bet, axis=1)], axis=1)
    for cp in CHECKPOINTS:
        if cp in skip:
            continue
        threshold, reward = CHECKPOINT_RULES[cp]
        s = spins[cp]
        played = s <= length
        k = np.minimum(s, length) - 1              # 判定轉之前已玩的轉數，也是判定轉的 0-based index
        lo = np.maximum(0, k - MAIN_SHORT_WINDOW)
        cs_a = np.concatenate([zeros, np.cumsum(adj, axis=1)], axis=1)
        cum_rtp = cs_a[rows, k] / cs_b[rows, k]
        short_rtp = (cs_a[rows, k] - cs_a[rows, lo]) / (cs_b[rows, k] - cs_b[rows, lo])
        hit = played & (cum_rtp < threshold) & (short_rtp < MAIN_SHORT_THRESHOLD)
        natural = nat[rows, k]
        adj[rows, k] = np.where(hit, np.maximum(natural, reward * bet[rows, k]), natural)
        reward_at[rows[hit], k[hit]] = reward
    return adj, reward_at


def load_rowdata(game: str) -> tuple[np.ndarray, np.ndarray]:
    """回傳 (payout, bet)，shape 均為 (players, spins)。"""

    path = ROWDATA_DIR / ROWDATA_FILES[game]
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        frame = pd.read_csv(fh, usecols=["Player", "Spin", "Bet", "Natural_Payout"])
    players = int(frame["Player"].max())
    spins = int(frame["Spin"].max())
    frame = frame.sort_values(["Player", "Spin"])
    payout = frame["Natural_Payout"].to_numpy(dtype=np.float64).reshape(players, spins)
    bet = frame["Bet"].to_numpy(dtype=np.float64).reshape(players, spins)
    return payout, bet


def simulate(game: str) -> None:
    started = time.perf_counter()
    nat, bet = load_rowdata(game)
    nat = nat[:, :SPINS_PER_DAY]
    bet = bet[:, :SPINS_PER_DAY]
    n_players, n_spins = nat.shape
    assert n_spins >= CHECKPOINTS[-1], "Row Data 轉數不足以涵蓋所有觸發點"

    rescued_player = np.zeros(n_players, dtype=bool)
    total_bet_all = bet.sum()              # 全日總押注（增量貢獻的分母）

    checkpoint_rows = []
    total_triggers = 0
    award_totals: dict[float, int] = {}

    spins = judge_spins(n_players, np.random.default_rng(MAIN_SEED))
    adj, reward_at = apply_main(nat, bet, spins)
    rows = np.arange(n_players)
    for cp in CHECKPOINTS:
        threshold, reward = band_of(cp)
        k = spins[cp] - 1
        hit = reward_at[rows, k] > 0
        n_trigger = int(hit.sum())
        total_triggers += n_trigger
        rescued_player |= hit
        award_totals[reward] = award_totals.get(reward, 0) + n_trigger
        checkpoint_rows.append({
            "checkpoint": cp,
            "threshold": threshold,
            "reward": reward,
            "judged": n_players,
            "triggered": n_trigger,
            "trigger_rate": n_trigger / n_players,
            "base_rtp": nat[:, :cp].sum() / bet[:, :cp].sum(),
            "uplift": (adj[rows, k] - nat[rows, k]).sum() / total_bet_all,
        })

    # ---- 延伸救援（440–1,000 轉）：前後 5 轉隨機判定、往前 400 轉 ----
    ext_rows = []
    ext_spins = judge_spins(n_players, np.random.default_rng(EXT_SEED), EXT_CHECKPOINTS)
    adj_ext, ext_reward_at = apply_ext(nat, bet, adj, ext_spins)
    for cp in EXT_CHECKPOINTS:
        if cp - CHECKPOINT_JITTER > n_spins:
            break
        played = ext_spins[cp] <= n_spins
        k = np.minimum(ext_spins[cp], n_spins) - 1
        hit = played & (ext_reward_at[rows, k] > 0)
        n_trigger = int(hit.sum())
        total_triggers += n_trigger
        rescued_player |= hit
        award_totals[EXT_REWARD] = award_totals.get(EXT_REWARD, 0) + n_trigger
        ext_rows.append({
            "checkpoint": cp,
            "triggered": n_trigger,
            "trigger_rate": n_trigger / n_players,
            "uplift": ((adj_ext[rows, k] - adj[rows, k]) * hit).sum() / total_bet_all,
        })
    adj = adj_ext

    total_bet = bet.sum()
    base_rtp_total = nat.sum() / total_bet
    mech_rtp_total = adj.sum() / total_bet
    total_judgments = (len(CHECKPOINTS) + len(ext_rows)) * n_players
    duration = time.perf_counter() - started

    # ---- 輸出 ----
    print(f"=== 老手救援 C-2 模擬（{SYSTEM_VERSION}） ===")
    print(f"game                    : {game}")
    print(f"rowdata                 : {ROWDATA_FILES[game]}")
    print(f"players / spins         : {n_players:,} / {n_spins:,}")
    print(f"duration                : {duration:.2f} sec")
    print()
    print(f"rtp_base                : {base_rtp_total * 100:.4f}%")
    print(f"rtp_mechanism_uplift    : +{(mech_rtp_total - base_rtp_total) * 100:.4f}%")
    print(f"rtp_with_mechanism      : {mech_rtp_total * 100:.4f}%")
    print()
    print("checkpoint  band門檻   預定   判定    觸發   觸發率     原RTP(+全日增量貢獻)")
    for row in checkpoint_rows:
        print(
            f"第 {row['checkpoint'] - CHECKPOINT_JITTER:>3}–{row['checkpoint'] + CHECKPOINT_JITTER:<3} 轉 <{row['threshold'] * 100:>2.0f}%   "
            f"{row['reward']:>4.0f}x  {row['judged']:>5,}  {row['triggered']:>5,}  "
            f"{row['trigger_rate'] * 100:>6.2f}%   "
            f"{row['base_rtp'] * 100:>7.4f}% (+{row['uplift'] * 100:.4f}%)"
        )
    print()
    main_up = sum(r["uplift"] for r in checkpoint_rows)
    ext_up = sum(r["uplift"] for r in ext_rows)
    if ext_rows:
        print(f"延伸救援（440 轉起，前後 {CHECKPOINT_JITTER} 轉隨機）：前 {EXT_MID_WINDOW} 轉 RTP <{EXT_MID_THRESHOLD * 100:.0f}% 且前 40 轉 RTP <{EXT_SHORT_THRESHOLD * 100:.0f}% → 救 {EXT_REWARD:g}×")
        print("checkpoint   判定    觸發   觸發率     全日增量貢獻")
        for row in ext_rows:
            print(
                f"第 {row['checkpoint']:>4} 轉  {n_players:>5,}  {row['triggered']:>5,}  "
                f"{row['trigger_rate'] * 100:>6.2f}%   +{row['uplift'] * 100:.4f}%"
            )
        ext_trig = sum(r['triggered'] for r in ext_rows)
        print(f"延伸救援小計            : 觸發 {ext_trig:,} 次、增量 +{ext_up * 100:.4f}%")
        print()
    total_up = main_up + ext_up
    if total_up > 0:
        print(f"增量占比                : 400 轉前 +{main_up * 100:.4f}%（{main_up / total_up * 100:.1f}%）"
              f" / 400 轉後 +{ext_up * 100:.4f}%（{ext_up / total_up * 100:.1f}%）")
    rescued = int(rescued_player.sum())
    print(f"rescued_player_ratio    : {rescued / n_players * 100:.2f}%  ({rescued:,} / {n_players:,})")
    print(f"trigger_rate_overall    : {total_triggers / total_judgments * 100:.2f}%  ({total_triggers:,} / {total_judgments:,})")
    awards_txt = "  ".join(f"{k:g}x={v:,}" for k, v in sorted(award_totals.items()))
    print(f"awards                  : {awards_txt}")
    print()


def main() -> None:
    for game in GAMES:
        simulate(game)


if __name__ == "__main__":
    main()
