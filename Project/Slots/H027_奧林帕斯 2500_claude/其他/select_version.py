"""H027 版本挑選 — 沿 FG 週期／FG 平均倍數的取捨軸挑出綜合偏差最小的版本.

為什麼需要挑選
--------------
賠率表固定、總 RTP 固定為版本標籤、BG RTP 固定為競品整數值之後，FG 的貢獻度也被鎖死：

    FG 貢獻 = 總 RTP - BG RTP = FG 平均倍數 / FG 週期

競品的 FG 貢獻只有 107.74 / 433.2 = 24.871%，而 92A 需要 33%、94A 需要 35%。
「FG 週期 1/433.2」與「FG 平均倍數 107.74x」因此不可能同時成立，只能在
「平均倍數 x 週期 = 常數」這條雙曲線上選一個點。

為什麼用解析值比較候選
----------------------
總 RTP、BG RTP、BG Hit Rate、FG 週期、FG 平均倍數是卡片權重的等式約束，解出來就精確成立；
64 區間線型就是卡片權重本身。這些量在模擬裡的偏差幾乎全是抽樣噪音——FG 一場的得分是重尾分布，
15 萬轉只有三百多場 FG，總 RTP 的標準誤就有 2~3 pp，會蓋掉候選之間真正的差異。
因此候選比較用卡片解出來的解析值；挑完之後再跑一次完整模擬做驗證與其餘指標的評分。
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fit_competitor_model as fit
import score_competitor_match as scorer

ROOT = fit.ROOT
OTHER = fit.OTHER
RECORD = fit.RECORD
TARGETS = scorer.TARGETS
COMPETITOR_FG_CONTRIBUTION = TARGETS.basic["fg_avg_multiplier"] / TARGETS.basic["fg_cycle"]

# only the groups that actually differ between candidates
ANALYTIC_GROUPS = ("fg_cycle", "fg_avg_multiplier", "interval_line", "thresholds")


def candidate_cycles(label: float, bg_rtp: float) -> dict[str, float]:
    ratio = (label - bg_rtp) / COMPETITOR_FG_CONTRIBUTION
    base = TARGETS.basic["fg_cycle"]
    return {
        "cycle_first": base,
        "balanced": base / math.sqrt(ratio),
        "avg_first": base / ratio,
    }


def analytic_score(cycle: float, label: float, bg_rtp: float, lines: dict[str, list[float]],
                   uppers: np.ndarray) -> dict:
    shapes = TARGETS.interval_shape()
    errors: dict[str, list[float]] = {group: [] for group in ANALYTIC_GROUPS}
    errors["fg_cycle"].append(abs(cycle - TARGETS.basic["fg_cycle"]) / TARGETS.basic["fg_cycle"])
    fg_avg = (label - bg_rtp) * cycle
    errors["fg_avg_multiplier"].append(
        abs(fg_avg - TARGETS.basic["fg_avg_multiplier"]) / TARGETS.basic["fg_avg_multiplier"])
    for scene in scorer.SCENES:
        model = np.asarray(lines[scene], dtype=float)
        model = model / model.sum()
        errors["interval_line"].extend(abs(model - np.asarray(shapes[scene])).tolist())
    pooled = np.asarray(lines["FG"], dtype=float) / sum(lines["FG"]) * 21.0 \
        + np.asarray(lines["BF"], dtype=float) / sum(lines["BF"]) * 251.0
    pooled = pooled / pooled.sum()
    for level in scorer.THRESHOLDS:
        model = float(pooled[uppers > level].sum())
        errors["thresholds"].append(abs(model - scorer.TARGETS_THRESHOLD[level]))
    groups, weighted, weight_sum = {}, 0.0, 0.0
    for group, values in errors.items():
        tolerance, weight = scorer.SPEC[group]
        normalized = float(np.mean(values)) / tolerance
        groups[group] = {"mean_error": float(np.mean(values)), "max_error": float(np.max(values)),
                         "tolerance": tolerance, "weight": weight,
                         "normalized": normalized, "count": len(values)}
        weighted += weight * normalized
        weight_sum += weight
    return {"cycle": cycle, "fg_avg": fg_avg, "groups": groups, "score": weighted / weight_sum}


def pooled_thresholds(lines: dict[str, list[float]], uppers: np.ndarray) -> dict[int, float]:
    pooled = (np.asarray(lines["FG"], dtype=float) / sum(lines["FG"]) * 21.0
              + np.asarray(lines["BF"], dtype=float) / sum(lines["BF"]) * 251.0)
    pooled = pooled / pooled.sum()
    return {level: float(pooled[uppers > level].sum()) for level in scorer.THRESHOLDS}


def combined_metrics(measured: dict, cycle: float, label: float, bg_rtp: float,
                     lines: dict[str, list[float]], uppers: np.ndarray) -> dict:
    """Measured metrics, with the card-constrained ones replaced by their exact values.

    Total RTP / BG RTP / BG Hit Rate / FG cycle / FG mean / BF RTP are equality
    constraints of the card solve and the 64-interval line *is* the card weight
    vector, so their simulated values only add sampling noise.  Everything else
    (FG per-spin hit rate, ball rate, combo, cluster tiers, ...) is a genuine
    second-order effect of the re-roll and stays as measured.
    """
    merged = dict(measured)
    merged["rtp_total"] = label
    merged["rtp_bg"] = bg_rtp
    merged["hit_rate_bg"] = TARGETS.basic["bg_hit_rate"]
    merged["fg_cycle"] = cycle
    merged["rtp_fg"] = label - bg_rtp
    merged["bf_rtp"] = label
    merged["interval_line"] = {scene: (np.asarray(lines[scene], dtype=float)
                                       / sum(lines[scene])).tolist() for scene in scorer.SCENES}
    merged["thresholds"] = pooled_thresholds(lines, uppers)
    return merged


def natural_reference(natural_rounds: int, reuse: str | None) -> dict:
    """Card-System-off reference runs the card solve reads its interval means from.

    Cached, but keyed on config.js's `competitor_fit` block: rebuilding the strips
    invalidates the cache, so a stale reference can never be silently reused.
    """
    cache = OTHER / "fit_natural_reference.json"
    fingerprint = scorer.load_config(ROOT / "config.js").get("competitor_fit")
    if reuse or cache.exists():
        stored = json.loads(Path(reuse or cache).read_text(encoding="utf-8"))
        if reuse or stored.get("competitor_fit") == fingerprint:
            runs = {k: v for k, v in stored.items() if k != "competitor_fit"}
            print(f"[natural] reusing {runs}")
            return {key: RECORD / value for key, value in runs.items()}
        print("[natural] cached reference predates the current strips; re-running")
    print("[natural] reference runs (Card System off)")
    natural = {
        "normal": fit.run_simulator("config.js", "config.js", 0, natural_rounds, False, False, 27001),
        "bf": fit.run_simulator("config.js", "config.js", 2, natural_rounds, False, False, 27201),
        "fg": fit.probe_natural_fg(natural_rounds),
    }
    payload = {k: v.name for k, v in natural.items()}
    payload["competitor_fit"] = fingerprint
    cache.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return natural


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=300_000)
    parser.add_argument("--bf-rounds", type=int, default=60_000)
    parser.add_argument("--screen-rounds", type=int, default=150_000)
    parser.add_argument("--screen-bf-rounds", type=int, default=40_000)
    parser.add_argument("--natural-rounds", type=int, default=10 ** 6)
    parser.add_argument("--bg-rtp", type=float, default=0.59)
    parser.add_argument("--bg-rtp-offset", type=float, default=0.0039,
                        help="Newton correction for the BG RTP solve; see 數值版本挑選_H027.md §5")
    parser.add_argument("--reuse-natural", default=None)
    parser.add_argument("--skip-verify", action="store_true")
    args = parser.parse_args()

    natural = natural_reference(args.natural_rounds, args.reuse_natural)
    uppers = fit.interval_table(natural["normal"])["Interval_Upper"].to_numpy(dtype=float)

    print(f"[candidates] FG contribution needed 92A {0.92 - args.bg_rtp:.4f} / "
          f"94A {0.94 - args.bg_rtp:.4f} vs competitor {COMPETITOR_FG_CONTRIBUTION:.5f}")
    cycles = candidate_cycles(0.92, args.bg_rtp)
    candidates = {}
    config_92 = scorer.load_config(ROOT / "config_92A.js")
    for index, (name, cycle) in enumerate(cycles.items()):
        summary = fit.calibrate_cards(natural["normal"], natural["bf"], natural["fg"],
                                      cycle, args.bg_rtp, verbose=False,
                                      bg_rtp_offset=args.bg_rtp_offset)
        lines = summary["config_92A.js"]["interval_line"]
        info = analytic_score(cycle, 0.92, args.bg_rtp, lines, uppers)
        normal = fit.run_simulator("config.js", "config_92A.js", 0, args.screen_rounds,
                                   True, False, 28_100 + index * 10)
        bf = fit.run_simulator("config.js", "config_92A.js", 2, args.screen_bf_rounds,
                               True, False, 28_101 + index * 10)
        measured = scorer.report_metrics(normal, bf)
        merged = combined_metrics(measured, cycle, 0.92, args.bg_rtp, lines, uppers)
        full = scorer.compare(config_92, merged, 0.92, args.bg_rtp)
        info["combined_score"] = full["score"]
        info["combined_groups"] = full["groups"]
        info["screen_runs"] = {"normal": normal.name, "bf": bf.name}
        candidates[name] = info
        print(f"[{name}] cycle=1/{cycle:.1f} FG avg={info['fg_avg']:.2f}x "
              f"analytic={info['score']:.3f} combined={full['score']:.3f}")
        for group in ("fg_cycle", "fg_avg_multiplier", "hit_rate_fg", "ball_rate",
                      "combo", "cluster_tiers", "interval_line", "thresholds"):
            data = full["groups"][group]
            print(f"    {group:<18} normalized={data['normalized']:6.2f} mean={data['mean_error']:.5f}")

    best = min(candidates, key=lambda name: candidates[name]["combined_score"])
    print(f"\n[selected] {best}  cycle=1/{cycles[best]:.1f}  FG avg(92A)={candidates[best]['fg_avg']:.2f}x")

    print("[final] writing the selected cycle into both RTP variants")
    final_summary = fit.calibrate_cards(natural["normal"], natural["bf"], natural["fg"],
                                        cycles[best], args.bg_rtp, verbose=True,
                                        bg_rtp_offset=args.bg_rtp_offset)
    payload = {
        "selected": best,
        "bg_rtp_target": args.bg_rtp,
        "candidates": {name: {k: v for k, v in info.items()} for name, info in candidates.items()},
        "calibration": {name: {k: v for k, v in info.items() if k != "interval_line"}
                        for name, info in final_summary.items()},
        "natural": {k: v.name for k, v in natural.items()},
    }

    if not args.skip_verify:
        print("[verify] Card System on, oldhand, small bet")
        runs = {}
        for index, (variant, label) in enumerate((("92A", 0.92), ("94A", 0.94))):
            config_code = f"config_{variant}.js"
            normal = fit.run_simulator("config.js", config_code, 0, args.rounds, True, False, 28_500 + index * 10)
            bf = fit.run_simulator("config.js", config_code, 2, args.bf_rounds, True, False, 28_501 + index * 10)
            metrics = scorer.report_metrics(normal, bf)
            result = scorer.compare(scorer.load_config(ROOT / config_code), metrics, label, args.bg_rtp)
            runs[variant] = {"normal": normal.name, "bf": bf.name, "score": result["score"],
                             "groups": result["groups"]}
            print(f"  {variant}: score={result['score']:.3f} normal={normal.name} bf={bf.name}")
            print(scorer.summary_text(result))
        payload["verification"] = runs

    (OTHER / "select_version_result.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("written 其他/select_version_result.json")


if __name__ == "__main__":
    main()
