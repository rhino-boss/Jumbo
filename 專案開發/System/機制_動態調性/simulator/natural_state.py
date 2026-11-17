# -*- coding: utf-8 -*-
"""動態調性：自然遊戲中「連續沒進 FG」「玩得很平」有多常發生（彩罐熱舞 rowdata，10,000 人 × 1,000 轉）。

只讀既有 rowdata 做統計，不是模擬。輸出 record/natural_state.json。
用法：python natural_state.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent


def find_rowdata() -> Path:
    for base in (HERE, *HERE.parents):
        for d in (base / "rowdata", base / "Else" / "rowdata"):
            f = d / "彩罐熱舞_基礎遊戲_10000人_1000轉.parquet"
            if f.is_file():
                return f
    raise FileNotFoundError("找不到 System/Else/rowdata/彩罐熱舞_基礎遊戲_10000人_1000轉.parquet")


def main() -> None:
    df = pd.read_parquet(find_rowdata(), columns=["Player", "Spin", "Natural_Multiplier", "Natural_FG",
                                                  "Natural_BG_Multiplier", "Natural_FG_Multiplier"])
    df = df.sort_values(["Player", "Spin"])
    P = int(df["Player"].max()); S = int(df["Spin"].max())
    mult = df["Natural_Multiplier"].to_numpy(np.float64).reshape(P, S)
    fg = df["Natural_FG"].to_numpy(bool).reshape(P, S)
    bgm = df["Natural_BG_Multiplier"].to_numpy(np.float64).reshape(P, S)
    fgm = df["Natural_FG_Multiplier"].to_numpy(np.float64).reshape(P, S)
    out: dict = {"players": P, "spins": S}

    # ---- 基本 ----
    out["rtp"] = float(mult.mean())
    out["fg_rate"] = float(fg.mean())
    out["fg_cycle"] = float(1 / fg.mean())
    out["fg_rtp_share"] = float(fgm.sum() / mult.sum())   # FG 得分占總得分
    out["bg_rtp"] = float(bgm.mean())                       # 只看 BG 得分的 RTP

    # ---- 連續沒進 FG ----
    out["no_fg_within"] = {str(n): float((~fg[:, :n].any(axis=1)).mean()) for n in (100, 200, 300, 400, 600, 1000)}
    # 一天 N 轉內最長的「沒進 FG」區段
    def longest_gap(row: np.ndarray) -> int:
        idx = np.flatnonzero(row)
        edges = np.concatenate(([-1], idx, [len(row)]))
        return int(np.diff(edges).max() - 1)
    for n in (400, 1000):
        g = np.array([longest_gap(fg[p, :n]) for p in range(P)])
        out[f"longest_gap_{n}"] = {str(t): float((g >= t).mean()) for t in (200, 300, 400, 500, 700)}
        out[f"longest_gap_{n}_median"] = float(np.median(g))
    # 沒進 FG 的區段內玩家實際 RTP：前 N 轉都沒進 FG 的玩家，前 N 轉 RTP
    out["rtp_first_n_no_fg"] = {}
    out["rtp_first_n_with_fg"] = {}
    for n in (100, 200, 300):
        nofg = ~fg[:, :n].any(axis=1)
        r = mult[:, :n].mean(axis=1)
        out["rtp_first_n_no_fg"][str(n)] = float(r[nofg].mean())
        out["rtp_first_n_with_fg"][str(n)] = float(r[~nofg].mean())

    # ---- 玩得很平：每 100 轉一段，看段內最大單轉倍數 ----
    W = 100
    seg = mult[:, : S // W * W].reshape(P, S // W, W)
    seg_max = seg.max(axis=2); seg_rtp = seg.mean(axis=2)
    out["seg100_max_below"] = {str(t): float((seg_max < t).mean()) for t in (5, 10, 20, 30, 50)}
    out["seg100_rtp_when_max_below"] = {str(t): float(seg_rtp[seg_max < t].mean()) for t in (5, 10, 20)}
    # 一天前 N 轉的最大單轉倍數（對照倍數留存表：當日最大倍數 ≥ M 的人留存較高）
    out["day_max_below"] = {}
    for n in (100, 200, 400):
        m = mult[:, :n].max(axis=1)
        out["day_max_below"][str(n)] = {str(t): float((m < t).mean()) for t in (10, 20, 30, 50, 100)}

    # ---- 兩種狀態有多重疊：前 200 轉沒進 FG 的人，最大倍數 < 20x 的比例 ----
    nofg200 = ~fg[:, :200].any(axis=1)
    max200 = mult[:, :200].max(axis=1)
    out["overlap_200"] = {
        "no_fg": float(nofg200.mean()),
        "max_lt20": float((max200 < 20).mean()),
        "no_fg_and_max_lt20": float((nofg200 & (max200 < 20)).mean()),
        "max_lt20_given_no_fg": float((max200[nofg200] < 20).mean()),
    }

    dest = HERE / "record" / "natural_state.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
