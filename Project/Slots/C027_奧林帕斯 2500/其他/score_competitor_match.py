"""C027 競品對齊評分器.

把「競品分析報告中每一項可比較的指標」變成一個可排序的分數，用來在候選版本之間挑選。

評分方式
--------
每個指標群 g 先算平均絕對偏差，再除以該群的容許值 tol_g，得到無因次的 e_g：

    e_g = mean(|model - target|) / tol_g

e_g <= 1 代表「在容許範圍內」。總分為加權平均 sum(w_g * e_g) / sum(w_g)，越小越好。
tol_g 與 w_g 都寫在 SPEC 裡，改權重不需要改程式邏輯。

資料來源
--------
* 結構型指標（符號分布、掉落分布、同輪堆疊）直接由 config.js 的輪帶算出，不含抽樣誤差。
* 行為型指標（RTP、Hit Rate、消除次數、倍數球、64 區間線型）由 Simulator 的 Record xlsx 讀取。
* 報告 5.2（有球／無球 × 消除次數）與 5.3（FG 累積倍數分層）目前的 Record 沒有交叉計數器，
  維持「無法比較」，不計入分數，但會列在輸出裡。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from competitor_targets import NORMAL_SYMBOLS, REELS, SCENES, SYMBOL_ORDER, Targets
from strip_model import window_matrix

ROOT = Path(__file__).resolve().parent.parent
TARGETS = Targets()

# C027 每個場景由兩張子輪帶表混合，評分時必須用混合後的結果，不是單張表
SCENE_TABLES = {
    "BG": ["BG_Symbol", "BG_Symbol (2)"],
    "FG": ["FG_Symbol", "FG_Symbol (2)"],
    "BF": ["FG_Symbol (3)", "FG_Symbol (4)"],
}


def scene_weights(config: dict, scene: str) -> list[float]:
    """Mixture weights of a scene, read from the same config fields the runtime uses."""
    if scene == "BG":
        raw = config["parameter"]["normal"]["base_reel_weights"]
    elif scene == "FG":
        raw = config["parameter"]["normal"]["free_table"].get("weights")
    else:
        raw = config["parameter"]["featurebuy"]["free_table"].get("weights")
    values = [float(value) for value in (raw or [])]
    total = sum(values)
    if total <= 0:
        raise ValueError(f"{scene}: mixture weights missing or all zero")
    return [value / total for value in values]

MULTIPLIER_VALUES = [2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 50, 100, 250, 500]
THRESHOLDS = [10, 20, 50, 100, 200, 500, 1000]

# group -> (tolerance in the group's own unit, weight)
SPEC = {
    "rtp_total": (0.005, 3.0),
    "rtp_bg": (0.005, 3.0),
    "hit_rate_bg": (0.005, 3.0),
    "hit_rate_fg": (0.020, 2.0),
    "fg_cycle": (0.05, 2.0),
    "fg_avg_multiplier": (0.05, 2.0),
    "bf_rtp": (0.005, 2.0),
    "bf_hit_rate": (0.020, 1.5),
    "symbol_initial": (0.0015, 2.0),
    "symbol_drop": (0.0030, 1.5),
    "stack": (0.010, 2.0),
    "combo": (0.015, 2.0),
    "cluster_tiers": (0.015, 1.5),
    "ball_rate": (0.010, 1.5),
    "multiplier_dist": (0.010, 1.5),
    "interval_line": (0.005, 2.0),
    "thresholds": (0.030, 1.0),
}


# ------------------------------------------------------------------ config side

def load_config(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    return json.loads(text[text.index("{"):text.rindex("}") + 1])


def _table_structure(strip: dict, id_to_code: dict) -> dict:
    length = len(strip["symbols"])
    initial, drop = {}, {}
    stack = np.zeros(5)
    for reel_index, reel in enumerate(REELS):
        sequence = [id_to_code[row[reel_index]] for row in strip["symbols"]]
        initial[reel] = {code: sequence.count(code) / length for code in SYMBOL_ORDER}
        windows = window_matrix(sequence, SYMBOL_ORDER)
        longest = np.zeros(length, dtype=np.int64)
        for index in range(len(SYMBOL_ORDER)):
            mask = windows == index
            current = np.zeros(length, dtype=np.int64)
            run = np.zeros(length, dtype=np.int64)
            for column in range(5):
                current = np.where(mask[:, column], current + 1, 0)
                run = np.maximum(run, current)
            longest = np.maximum(longest, run)
        stack += np.bincount(longest, minlength=6)[1:6] / (length * 6)
        column = [row[reel_index] for row in strip["drop_weights"]]
        total = sum(column)
        drop[reel] = {id_to_code[index + 1]: column[index] / total for index in range(len(column))}
    return {"initial": initial, "drop": drop, "stack": stack.tolist()}


def strip_structure(config: dict) -> dict:
    """Mixture-weighted per-reel symbol shares, drop shares and stack distribution."""
    id_to_code = {int(value): code for code, value in zip(config["symbol_codes"], config["symbol_ids"])}
    by_name = dict(zip(config["strip_names"], config["strips"]))
    out = {}
    for scene, names in SCENE_TABLES.items():
        weights = scene_weights(config, scene)
        parts = [_table_structure(by_name[name], id_to_code) for name in names]
        initial = {reel: {code: sum(weight * part["initial"][reel][code]
                                   for weight, part in zip(weights, parts))
                          for code in SYMBOL_ORDER} for reel in REELS}
        drop = {reel: {code: sum(weight * part["drop"][reel].get(code, 0.0)
                                 for weight, part in zip(weights, parts))
                       for code in SYMBOL_ORDER} for reel in REELS}
        stack = [sum(weight * part["stack"][index] for weight, part in zip(weights, parts))
                 for index in range(5)]
        out[scene] = {"initial": initial, "drop": drop, "stack": stack}
    return out


# ----------------------------------------------------------------- report side

def overview(path: Path) -> dict:
    frame = pd.read_excel(path, sheet_name="Overview")
    values = {}
    for _, row in frame.iterrows():
        key = row["Index"]
        if isinstance(key, str):
            values[key] = row["Value"]
    return values


def as_rate(text) -> float:
    return float(str(text).replace("%", "").replace(",", "").strip()) / 100.0


def cycle_from(text) -> float:
    match = re.search(r"cycle ([\d.]+)", str(text))
    if not match:
        raise ValueError(f"cannot read cycle from {text!r}")
    return float(match.group(1))


def report_metrics(normal_path: Path, bf_path: Path) -> dict:
    normal = overview(normal_path)
    bf = overview(bf_path)
    cascade = pd.read_excel(normal_path, sheet_name="Cascade")
    cascade_bf = pd.read_excel(bf_path, sheet_name="Cascade")
    multiplier = pd.read_excel(normal_path, sheet_name="C2-C3 Multiplier")
    multiplier_bf = pd.read_excel(bf_path, sheet_name="C2-C3 Multiplier")
    hits = pd.read_excel(normal_path, sheet_name="Symbol Hit Rate")
    hits_bf = pd.read_excel(bf_path, sheet_name="Symbol Hit Rate")
    line = pd.read_excel(normal_path, sheet_name="Multiplier Line")
    line_bf = pd.read_excel(bf_path, sheet_name="Multiplier Line")

    def combo(frame: pd.DataFrame, column: str) -> list[float]:
        counts = frame[column].to_numpy(dtype=float)
        total = counts.sum()
        if total <= 0:
            return [0.0] * 6
        return [float(counts[i] / total) for i in range(5)] + [float(counts[5:].sum() / total)]

    def tiers(frame: pd.DataFrame, prefix: str) -> list[float]:
        mask = frame["Symbol"].isin(NORMAL_SYMBOLS)
        values = np.array([
            frame.loc[mask, f"{prefix}_8_9_Hit"].sum(),
            frame.loc[mask, f"{prefix}_10_11_Hit"].sum(),
            frame.loc[mask, f"{prefix}_12_Plus_Hit"].sum(),
        ], dtype=float)
        return (values / values.sum()).tolist() if values.sum() else [0.0, 0.0, 0.0]

    def multiplier_share(frame: pd.DataFrame, column: str) -> list[float]:
        share = dict(zip(frame["Multiplier"].astype(int), frame[column].astype(float)))
        total = sum(share.values())
        if total <= 0:
            return [0.0] * len(MULTIPLIER_VALUES)
        return [share.get(value, 0.0) / total for value in MULTIPLIER_VALUES]

    def interval_share(frame: pd.DataFrame, column: str) -> list[float]:
        counts = frame[column].to_numpy(dtype=float)
        total = counts.sum()
        return (counts / total).tolist() if total else [0.0] * len(counts)

    uppers = line["Interval_Upper"].to_numpy(dtype=float)
    fg_line = np.array(interval_share(line, "free_game_cnt"))
    bf_line = np.array(interval_share(line_bf, "free_game_cnt_BF"))
    # The competitor threshold table pools 21 natural FG sessions with 251 purchased
    # ones, so mirror that composition instead of weighting the two runs equally.
    combined = fg_line * 21.0 + bf_line * 251.0
    combined = combined / combined.sum() if combined.sum() else combined

    def threshold_share(shares: np.ndarray, level: float) -> float:
        return float(shares[uppers > level].sum())

    return {
        "rtp_total": as_rate(normal["rtp_total"]),
        "rtp_bg": as_rate(normal["rtp_bg"]),
        "rtp_fg": as_rate(normal["rtp_fg"]),
        "hit_rate_bg": as_rate(normal["hit_rate_bg"]),
        "hit_rate_fg": as_rate(normal["hit_rate_fg"]),
        "fg_cycle": cycle_from(normal["fg_trigger_rate"]),
        "ball_rate": {"BG": as_rate(normal["multiplier_ball_rate_bg"]),
                      "FG": as_rate(normal["multiplier_ball_rate_fg"]),
                      "BF": as_rate(bf["multiplier_ball_rate_fg"])},
        "bf_rtp": as_rate(bf["rtp_total"]),
        "bf_hit_rate": as_rate(bf["hit_rate_fg"]),
        "max_win_x": float(str(normal["max_win_x"]).replace(",", "")),
        "bf_max_win_x": float(str(bf["max_win_x"]).replace(",", "")),
        "combo": {"BG": combo(cascade, "BG_Count"), "FG": combo(cascade, "FG_Count"),
                  "BF": combo(cascade_bf, "FG_Count")},
        "cluster_tiers": {"BG": tiers(hits, "BG"), "FG": tiers(hits, "FG"), "BF": tiers(hits_bf, "FG")},
        "multiplier_dist": {"BG": multiplier_share(multiplier, "BG_Count"),
                            "FG": multiplier_share(multiplier, "FG_Count"),
                            "BF": multiplier_share(multiplier_bf, "FG_Count")},
        "interval_line": {"BG": interval_share(line, "base_game_cnt"),
                          "FG": fg_line.tolist(), "BF": bf_line.tolist()},
        "thresholds": {level: threshold_share(combined, level) for level in THRESHOLDS},
    }


# ------------------------------------------------------------------- comparison

def compare(config: dict, metrics: dict, rtp_label: float, bg_rtp_target: float) -> dict:
    structure = strip_structure(config)
    rows = []

    def add(group: str, name: str, target, model, unit="pp"):
        rows.append({"group": group, "name": name, "target": target, "model": model, "unit": unit})

    add("rtp_total", "總 RTP", rtp_label, metrics["rtp_total"])
    add("rtp_bg", "BG RTP", bg_rtp_target, metrics["rtp_bg"])
    add("hit_rate_bg", "BG Hit Rate", TARGETS.basic["bg_hit_rate"], metrics["hit_rate_bg"])
    add("hit_rate_fg", "FG Hit Rate", TARGETS.basic["fg_hit_rate"], metrics["hit_rate_fg"])
    add("fg_cycle", "FG 週期", TARGETS.basic["fg_cycle"], metrics["fg_cycle"], "rel")
    fg_avg = metrics["rtp_fg"] * metrics["fg_cycle"]
    add("fg_avg_multiplier", "FG 平均倍數", TARGETS.basic["fg_avg_multiplier"], fg_avg, "rel")
    add("bf_rtp", "Buy Feature RTP", rtp_label, metrics["bf_rtp"])
    add("bf_hit_rate", "Buy Feature FG Hit Rate", TARGETS.basic["bf_hit_rate"], metrics["bf_hit_rate"])

    for scene in SCENES:
        for reel in REELS:
            for code in SYMBOL_ORDER:
                add("symbol_initial", f"{scene} {reel} {code}",
                    TARGETS.initial[scene][reel][code], structure[scene]["initial"][reel][code])
                add("symbol_drop", f"{scene}drop {reel} {code}",
                    TARGETS.drop[scene][reel][code], structure[scene]["drop"][reel][code])
        for index, size in enumerate((1, 2, 3, 4, 5)):
            add("stack", f"{scene} {size} 堆疊", TARGETS.stack_overall[scene][index], structure[scene]["stack"][index])
        for index in range(6):
            label = f"combo {index}" if index < 5 else "combo 5+"
            add("combo", f"{scene} {label}", TARGETS.combo[scene][index], metrics["combo"][scene][index])
        for index, tier in enumerate(("8-9", "10-11", "12+")):
            add("cluster_tiers", f"{scene} cluster {tier}",
                TARGETS.cluster_tiers(scene)[tier], metrics["cluster_tiers"][scene][index])
        add("ball_rate", f"{scene} 倍數球出現率", TARGETS.ball_spin_rate[scene], metrics["ball_rate"][scene])
        for index, value in enumerate(MULTIPLIER_VALUES):
            add("multiplier_dist", f"{scene} {value}x",
                TARGETS.multiplier_dist[scene][index], metrics["multiplier_dist"][scene][index])

    shapes = TARGETS.interval_shape()
    for scene in SCENES:
        for index in range(64):
            add("interval_line", f"{scene} interval {index}", shapes[scene][index],
                metrics["interval_line"][scene][index])
    for level in THRESHOLDS:
        add("thresholds", f">={level}x", TARGETS_THRESHOLD[level], metrics["thresholds"][level])

    groups = {}
    for row in rows:
        target, model = float(row["target"]), float(row["model"])
        row["delta"] = model - target
        if row["unit"] == "rel":
            row["error"] = abs(model - target) / max(abs(target), 1e-9)
        else:
            row["error"] = abs(model - target)
        groups.setdefault(row["group"], []).append(row["error"])

    scores = {}
    weighted, weight_sum = 0.0, 0.0
    for group, errors in groups.items():
        tolerance, weight = SPEC[group]
        normalized = float(np.mean(errors)) / tolerance
        scores[group] = {"mean_error": float(np.mean(errors)), "max_error": float(np.max(errors)),
                         "tolerance": tolerance, "weight": weight, "normalized": normalized,
                         "count": len(errors)}
        weighted += weight * normalized
        weight_sum += weight
    return {"rows": rows, "groups": scores, "score": weighted / weight_sum}


TARGETS_THRESHOLD = dict(zip(THRESHOLDS, [0.9191, 0.8235, 0.5515, 0.2904, 0.0993, 0.0074, 0.0000]))


def summary_text(result: dict) -> str:
    lines = [f"總分 {result['score']:.3f}（越小越好，1.0 = 剛好落在容許值上）", ""]
    lines.append(f"{'指標群':<20}{'項數':>5}{'平均偏差':>12}{'最大偏差':>12}{'容許':>10}{'標準化':>9}{'權重':>7}")
    for group, info in sorted(result["groups"].items(), key=lambda item: -item[1]["normalized"] * item[1]["weight"]):
        lines.append(f"{group:<20}{info['count']:>5}{info['mean_error']:>12.5f}{info['max_error']:>12.5f}"
                     f"{info['tolerance']:>10.4f}{info['normalized']:>9.2f}{info['weight']:>7.1f}")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config_92A.js")
    parser.add_argument("--normal", required=True)
    parser.add_argument("--bf", required=True)
    parser.add_argument("--label", type=float, default=None,
                        help="總 RTP 目標；預設讀 config 的 rtp_label")
    parser.add_argument("--bg-rtp", type=float, default=None,
                        help="BG RTP 目標；預設讀 config 的 card_system.calibration")
    args = parser.parse_args()
    config = load_config(ROOT / args.config)
    calibration = config.get("card_system", {}).get("calibration", {})
    if args.label is None:
        args.label = float(calibration.get("total_rtp_target", 0.92))
    if args.bg_rtp is None:
        args.bg_rtp = float(calibration.get("bg_rtp_target", 0.59))
    print(f"目標：總 RTP {args.label:.4%}　BG RTP {args.bg_rtp:.4%}\n")
    metrics = report_metrics(ROOT / "Record" / args.normal, ROOT / "Record" / args.bf)
    result = compare(config, metrics, args.label, args.bg_rtp)
    print(summary_text(result))
