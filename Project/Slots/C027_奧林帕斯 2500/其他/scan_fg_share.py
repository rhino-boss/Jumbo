"""掃 BG:FG RTP 拆分，量出「FG 每轉 Hit Rate」與「FG 平均倍數」的取捨曲線.

競品的三個 FG 數字互相綁死：`FG RTP 貢獻 = FG 平均倍數 ÷ FG 週期`。
把 FG 週期釘在競品的 1/433.2 之後，FG 的 RTP 份額就唯一決定了 FG 平均倍數；
而 FG 平均倍數決定卡片要把自然 FG 整包壓多少，壓得越多、被接受的場次命中結構就越偏。

兩個目標的樣本可靠度差很多：

    FG 每轉 Hit Rate   競品 332 轉    ±約 2.7 pp
    FG 平均倍數        競品 21 場     ±約 35%（重尾分布）

因此本工具用「以競品自身抽樣誤差標準化」的偏差來評分：偏差除以該指標的抽樣誤差。

    py scan_fg_share.py --shares 0.294 0.34 0.39 --rounds 300000
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from competitor_targets import Targets
from fit_c027_model import OTHER, calibrate_cards
from tune_c027 import measure, natural_paths, report

TARGETS = Targets()
# competitor sampling errors used to normalise the two objectives
FG_HIT_SE = 0.027       # 332 spins
FG_AVG_SE_REL = 0.35    # 21 heavy-tailed sessions
CYCLE_SE_REL = 0.22     # 21 triggers


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shares", type=float, nargs="+",
                        default=[0.2938, 0.34, 0.39])
    parser.add_argument("--rounds", type=int, default=300_000)
    parser.add_argument("--seed", type=int, default=93_001)
    parser.add_argument("--ball-share", type=float, default=0.00657)
    parser.add_argument("--split-max", type=float, default=6.0)
    args = parser.parse_args()
    normal, buy, probe = natural_paths()

    results = []
    for index, share in enumerate(args.shares):
        calibrate_cards(normal, buy, probe, TARGETS.basic["fg_cycle"],
                        ball_share=args.ball_share, ball_split_max=args.split_max,
                        fg_shape_source="competitor", fg_rtp_share=share, verbose=False)
        measured = measure("config_92A.js", args.rounds, args.seed + index)
        fg_avg = measured["rtp_fg"] * measured["fg_cycle"]
        hit_error = abs(measured["hit_rate_fg"] - TARGETS.basic["fg_hit_rate"]) / FG_HIT_SE
        avg_error = (abs(fg_avg - TARGETS.basic["fg_avg_multiplier"])
                     / TARGETS.basic["fg_avg_multiplier"] / FG_AVG_SE_REL)
        cycle_error = (abs(measured["fg_cycle"] - TARGETS.basic["fg_cycle"])
                       / TARGETS.basic["fg_cycle"] / CYCLE_SE_REL)
        score = hit_error + avg_error + cycle_error
        results.append({"share": share, "fg_avg": fg_avg, "score": score,
                        "hit_error": hit_error, "avg_error": avg_error,
                        "cycle_error": cycle_error, **measured})
        report(f"fg_share={share:.4f}", measured)
        print(f"    FG avg {fg_avg:.2f}x　誤差(以競品抽樣誤差為單位)：hit {hit_error:.2f}σ"
              f" / avg {avg_error:.2f}σ / cycle {cycle_error:.2f}σ　合計 {score:.2f}")

    best = min(results, key=lambda item: item["score"])
    print(f"\n最佳：fg_rtp_share = {best['share']:.4f}"
          f"（FG hit {best['hit_rate_fg']:.4%}、FG avg {best['fg_avg']:.2f}x、"
          f"cycle 1/{best['fg_cycle']:.1f}、總 RTP {best['rtp_total']:.4%}）")
    (OTHER / "scan_fg_share_result.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
