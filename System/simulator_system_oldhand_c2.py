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
* 以天為循環；本模擬將 1000 轉視為同一日。
* 每滿 40 轉判定一次「當日累積 RTP」；判定回合本身不納入統計（沿用 C 版口徑）。
* 判定落點 41–100（含第 40 轉檢查點）：RTP < 40% → 預定 50×
  判定落點 101–200：RTP < 40% → 預定 70×
  判定落點 201–400：RTP < 60% → 預定 100×
* 當日最大單局倍數已 ≥ 預定倍數 → 改給 30×；否則給預定倍數。
* 救援落在判定回合：該轉最終得分 = max(自然得分, 救援倍數 × Bet)，
  成本以增量記帳；救援得分計入當日最大單局倍數。
* 尚未套用救援池／共同池上限（先量測機制的自然增量，供預算評估）。
"""

from __future__ import annotations

import gzip
import time
from pathlib import Path

import numpy as np
import pandas as pd

SYSTEM_VERSION = "c2-0.3"


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
    "超級寶石": "超級寶石_基礎遊戲94RTP_10000人_1000轉.csv.gz",
    "彩罐熱舞": "彩罐熱舞_基礎遊戲94RTP_10000人_1000轉.csv.gz",
}
GAMES = ["超級寶石", "彩罐熱舞"]

# ---- C-2 參數 ----
CHECKPOINT_INTERVAL = 40                      # SPS 最小監測單位
CHECKPOINTS = list(range(40, 401, 40))        # 40, 80, ..., 400（10 個觸發點）
CONSOLATION_X = 30.0                          # 已體驗過大倍數時的安慰獎

# (落點下限, 落點上限, 當日累積 RTP 門檻, 預定救援倍數)
BANDS = (
    (40, 100, 0.40, 50.0),
    (101, 200, 0.40, 70.0),
    (201, 400, 0.60, 100.0),
)


def band_of(spin_no: int) -> tuple[float, float]:
    for lo, hi, threshold, reward in BANDS:
        if lo <= spin_no <= hi:
            return threshold, reward
    raise ValueError(f"第 {spin_no} 轉不在任何救援區間內")


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
    n_players, n_spins = nat.shape
    assert n_spins >= CHECKPOINTS[-1], "Row Data 轉數不足以涵蓋所有觸發點"

    adj = nat.copy()                       # 套用機制後的每轉最終得分
    mult = nat / bet                       # 自然單局倍數
    max_mult = np.zeros(n_players)         # 當日最大單局倍數（含救援結果）
    rescued_player = np.zeros(n_players, dtype=bool)

    cum_nat = np.zeros(n_players)          # 判定用：前 c-1 轉累積（自然）
    cum_adj = np.zeros(n_players)          # 判定用：前 c-1 轉累積（套機制）
    cum_bet = np.zeros(n_players)

    checkpoint_rows = []
    total_triggers = 0
    award_totals = {50.0: 0, 70.0: 0, 100.0: 0, CONSOLATION_X: 0}

    prev = 0
    for cp in CHECKPOINTS:
        # 累積到判定回合前一轉（判定回合本身不納入）
        seg = slice(prev, cp - 1)
        cum_nat += nat[:, seg].sum(axis=1)
        cum_adj += adj[:, seg].sum(axis=1)
        cum_bet += bet[:, seg].sum(axis=1)
        max_mult = np.maximum(max_mult, (adj[:, seg] / bet[:, seg]).max(axis=1) if cp - 1 > prev else max_mult)

        threshold, reward = band_of(cp)
        rtp_now = cum_adj / cum_bet
        hit = rtp_now < threshold                          # 判定成功（觸發）

        planned = np.where(max_mult >= reward, CONSOLATION_X, reward)
        spin_idx = cp - 1
        natural_this = nat[:, spin_idx]
        rescue_payout = planned * bet[:, spin_idx]
        final_this = np.where(hit, np.maximum(natural_this, rescue_payout), natural_this)
        adj[:, spin_idx] = final_this

        # 統計
        n_trigger = int(hit.sum())
        total_triggers += n_trigger
        rescued_player |= hit
        for value in (50.0, 70.0, 100.0, CONSOLATION_X):
            award_totals[value] += int((hit & (planned == value)).sum())

        # 當下原來 RTP%（自然、不含機制）與機制到此為止的增量
        base_rtp = cum_nat.sum() / cum_bet.sum()
        uplift = (cum_adj.sum() - cum_nat.sum()) / cum_bet.sum()
        checkpoint_rows.append({
            "checkpoint": cp,
            "threshold": threshold,
            "reward": reward,
            "judged": n_players,
            "triggered": n_trigger,
            "trigger_rate": n_trigger / n_players,
            "base_rtp": base_rtp,
            "uplift": uplift,
            "award_planned": int((hit & (planned == reward)).sum()),
            "award_consolation": int((hit & (planned == CONSOLATION_X)).sum()),
        })

        # 判定回合本身納入後續累積，救援結果計入當日最大倍數
        cum_nat += natural_this
        cum_adj += final_this
        cum_bet += bet[:, spin_idx]
        max_mult = np.maximum(max_mult, final_this / bet[:, spin_idx])
        prev = cp

    total_bet = bet.sum()
    base_rtp_total = nat.sum() / total_bet
    mech_rtp_total = adj.sum() / total_bet
    total_judgments = len(CHECKPOINTS) * n_players
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
    print("checkpoint  band門檻   預定   判定    觸發   觸發率     原RTP(+機制增量)      發放(預定/30x)   30x比例")
    for row in checkpoint_rows:
        print(
            f"第 {row['checkpoint']:>3} 轉   <{row['threshold'] * 100:>2.0f}%     "
            f"{row['reward']:>4.0f}x  {row['judged']:>5,}  {row['triggered']:>5,}  "
            f"{row['trigger_rate'] * 100:>6.2f}%   "
            f"{row['base_rtp'] * 100:>7.4f}% (+{row['uplift'] * 100:.4f}%)   "
            f"{row['award_planned']:>4} / {row['award_consolation']}   "
            f"{(row['award_consolation'] / row['triggered'] * 100) if row['triggered'] else 0.0:>6.2f}%"
        )
    print()
    rescued = int(rescued_player.sum())
    print(f"rescued_player_ratio    : {rescued / n_players * 100:.2f}%  ({rescued:,} / {n_players:,})")
    print(f"trigger_rate_overall    : {total_triggers / total_judgments * 100:.2f}%  ({total_triggers:,} / {total_judgments:,})")
    print(f"awards                  : 50x={award_totals[50.0]:,}  70x={award_totals[70.0]:,}  "
          f"100x={award_totals[100.0]:,}  30x={award_totals[CONSOLATION_X]:,}")
    print()


def main() -> None:
    for game in GAMES:
        simulate(game)


if __name__ == "__main__":
    main()
