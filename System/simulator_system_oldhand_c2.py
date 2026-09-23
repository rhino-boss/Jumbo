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
* 每滿 40 轉判定一次「當日累積 RTP」，且須同時符合前 40 轉 RTP < 50%；
  判定回合本身不納入統計（沿用 C 版口徑）。
* 10 個觸發點各訂 RTP 門檻與救援倍數（見 CHECKPOINT_RULES），
  倍數由 20× 隨落點遞增至 100×
* 救援落在判定回合：該轉最終得分 = max(自然得分, 救援倍數 × Bet)，
  成本以增量記帳。
* 延伸救援（當日 401 轉起）：每滿 40 轉判定，
  前 200 轉 RTP < 60% 且前 40 轉 RTP < 50% → 送 10× BG 盤面。
* 尚未套用救援池／共同池上限（先量測機制的自然增量，供預算評估）。
"""

from __future__ import annotations

import gzip
import time
from pathlib import Path

import numpy as np
import pandas as pd

SYSTEM_VERSION = "c2-1.3"


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

    for candidate in candidates:
        rowdata = candidate / "rowdata"
        if rowdata.is_dir() and any(rowdata.glob("*_1000人_1000轉.csv.gz")):
            return candidate.resolve()

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
    40:  (0.30, 25.0),
    80:  (0.35, 50.0),
    120: (0.40, 70.0),
    160: (0.45, 80.0),
    200: (0.50, 90.0),
    240: (0.55, 100.0),
    280: (0.60, 100.0),
    320: (0.65, 100.0),
    360: (0.70, 100.0),
    400: (0.70, 100.0),
}
CHECKPOINTS = sorted(CHECKPOINT_RULES)

# ---- 延伸救援（當日 401–1,000 轉）----
EXT_CHECKPOINTS = list(range(440, 1001, 40))  # 440 起每 40 轉，跑到當日轉數為止
EXT_MID_WINDOW = 200                          # 往前抓 200 轉
EXT_MID_THRESHOLD = 0.60
EXT_SHORT_WINDOW = 40                         # 前 40 轉
EXT_SHORT_THRESHOLD = 0.50
EXT_REWARD = 10.0                             # 送 10× BG 盤面


def band_of(spin_no: int) -> tuple[float, float]:
    return CHECKPOINT_RULES[spin_no]


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

    adj = nat.copy()                       # 套用機制後的每轉最終得分
    rescued_player = np.zeros(n_players, dtype=bool)
    total_bet_all = bet.sum()              # 全日總押注（增量貢獻的分母）

    cum_nat = np.zeros(n_players)          # 判定用：前 c-1 轉累積（自然）
    cum_adj = np.zeros(n_players)          # 判定用：前 c-1 轉累積（套機制）
    cum_bet = np.zeros(n_players)

    checkpoint_rows = []
    total_triggers = 0
    award_totals: dict[float, int] = {}

    prev = 0
    for cp in CHECKPOINTS:
        # 累積到判定回合前一轉（判定回合本身不納入）
        seg = slice(prev, cp - 1)
        cum_nat += nat[:, seg].sum(axis=1)
        cum_adj += adj[:, seg].sum(axis=1)
        cum_bet += bet[:, seg].sum(axis=1)

        threshold, reward = band_of(cp)
        rtp_now = cum_adj / cum_bet
        short_start = max(0, cp - 1 - MAIN_SHORT_WINDOW)
        short_rtp = adj[:, short_start:cp - 1].sum(axis=1) / bet[:, short_start:cp - 1].sum(axis=1)
        hit = (rtp_now < threshold) & (short_rtp < MAIN_SHORT_THRESHOLD)   # 判定成功（觸發）

        spin_idx = cp - 1
        natural_this = nat[:, spin_idx]
        rescue_payout = reward * bet[:, spin_idx]
        final_this = np.where(hit, np.maximum(natural_this, rescue_payout), natural_this)
        adj[:, spin_idx] = final_this

        # 統計
        n_trigger = int(hit.sum())
        total_triggers += n_trigger
        rescued_player |= hit
        award_totals[reward] = award_totals.get(reward, 0) + n_trigger

        # 當下原來 RTP%（統計至第 c 轉）；增量 = 該觸發點發放 ÷ 全日總押注
        bet_to_cp = cum_bet.sum() + bet[:, spin_idx].sum()
        base_rtp = (cum_nat.sum() + natural_this.sum()) / bet_to_cp
        uplift = (final_this - natural_this).sum() / total_bet_all
        checkpoint_rows.append({
            "checkpoint": cp,
            "threshold": threshold,
            "reward": reward,
            "judged": n_players,
            "triggered": n_trigger,
            "trigger_rate": n_trigger / n_players,
            "base_rtp": base_rtp,
            "uplift": uplift,
        })

        # 判定回合本身納入後續累積
        cum_nat += natural_this
        cum_adj += final_this
        cum_bet += bet[:, spin_idx]
        prev = cp

    # ---- 延伸救援（401–1,000 轉）：滾動窗口判定 ----
    ext_rows = []
    for cp in EXT_CHECKPOINTS:
        if cp > n_spins:
            break
        i = cp - 1
        mid = adj[:, cp - 1 - EXT_MID_WINDOW:cp - 1]
        short = adj[:, cp - 1 - EXT_SHORT_WINDOW:cp - 1]
        mid_bet = bet[:, cp - 1 - EXT_MID_WINDOW:cp - 1].sum(axis=1)
        short_bet = bet[:, cp - 1 - EXT_SHORT_WINDOW:cp - 1].sum(axis=1)
        hit = (mid.sum(axis=1) / mid_bet < EXT_MID_THRESHOLD) & \
              (short.sum(axis=1) / short_bet < EXT_SHORT_THRESHOLD)
        natural_this = nat[:, i]
        final_this = np.where(hit, np.maximum(natural_this, EXT_REWARD * bet[:, i]), natural_this)
        adj[:, i] = final_this
        n_trigger = int(hit.sum())
        total_triggers += n_trigger
        rescued_player |= hit
        award_totals[EXT_REWARD] = award_totals.get(EXT_REWARD, 0) + n_trigger
        ext_rows.append({
            "checkpoint": cp,
            "triggered": n_trigger,
            "trigger_rate": n_trigger / n_players,
            "uplift": (final_this - natural_this).sum() / total_bet_all,
        })

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
            f"第 {row['checkpoint']:>3} 轉   <{row['threshold'] * 100:>2.0f}%     "
            f"{row['reward']:>4.0f}x  {row['judged']:>5,}  {row['triggered']:>5,}  "
            f"{row['trigger_rate'] * 100:>6.2f}%   "
            f"{row['base_rtp'] * 100:>7.4f}% (+{row['uplift'] * 100:.4f}%)"
        )
    print()
    main_up = sum(r["uplift"] for r in checkpoint_rows)
    ext_up = sum(r["uplift"] for r in ext_rows)
    if ext_rows:
        print(f"延伸救援（401 轉起）：前 200 轉 RTP <{EXT_MID_THRESHOLD * 100:.0f}% 且前 40 轉 RTP <{EXT_SHORT_THRESHOLD * 100:.0f}% → 送 {EXT_REWARD:g}× BG 盤面")
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
