"""C027 Card-On 閉環校準.

`fit_c027_model.py --cards` 只能用 Card-Off 的自然分布解出卡片權重，但兩件事只有
真的跑 Card-On 才量得到：

1. **BG 倍數球出現率**：卡片依「得分區間」挑結果，而倍數球會放大得分，
   因此有球的 spin 會被過度取樣。零得分卡的 `ball` 維度就是修正這件事的旋鈕。
2. **FG 每轉 Hit Rate**：卡片把 FG 整包壓到目標平均倍數時，會連帶改變被接受場次的
   命中結構。

本工具用少量 Card-On 樣本量出這兩個值，再解出零得分卡的 `ball_share`，
並比較 FG 線型要投影到競品形狀還是自然形狀。

    py tune_c027.py --scan-fg-shape      # 比較兩種 FG 線型來源
    py tune_c027.py --solve-ball-share   # 解 ball_share 並寫回兩份 RTP Config
    py tune_c027.py --set-ball-share X   # 直接套一個 ball_share 並量測
    py tune_c027.py --solve-offset       # 解 BG RTP 的 Newton 補償量
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from competitor_targets import Targets
from fit_c027_model import OTHER, RECORD, ROOT, calibrate_cards, run_simulator

TARGETS = Targets()
MANIFEST = OTHER / "verify_c027_reports.json"
NATURAL_KEYS = ("natural_normal", "natural_buy", "natural_fg_probe")


def natural_paths() -> tuple[Path, Path, Path]:
    """Card-Off baseline reports, read from the manifest verify_c027.py writes."""
    import json
    if not MANIFEST.is_file():
        raise SystemExit("需要 其他/verify_c027_reports.json（先跑 verify_c027.py --natural）")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    missing = [key for key in NATURAL_KEYS if key not in manifest]
    if missing:
        raise SystemExit(f"verify_c027_reports.json 缺少 {missing}")
    return tuple(RECORD / manifest[key] for key in NATURAL_KEYS)


def overview(path: Path) -> dict:
    frame = pd.read_excel(path, sheet_name="Overview")
    return {row["Index"]: row["Value"] for _, row in frame.iterrows() if isinstance(row["Index"], str)}


def as_rate(text) -> float:
    return float(str(text).replace("%", "").replace(",", "").strip()) / 100.0


def cycle_of(text) -> float:
    match = re.search(r"cycle ([\d.]+)", str(text))
    return float(match.group(1)) if match else float("nan")


def measure(config_rtp: str, rounds: int, seed: int, bet_mode: int = 0) -> dict:
    path = run_simulator("config.js", config_rtp, bet_mode, rounds, True, False, seed)
    values = overview(path)
    return {
        "report": path.name,
        "rtp_total": as_rate(values["rtp_total"]),
        "rtp_bg": as_rate(values["rtp_bg"]),
        "rtp_fg": as_rate(values["rtp_fg"]),
        "hit_rate_bg": as_rate(values["hit_rate_bg"]),
        "hit_rate_fg": as_rate(values["hit_rate_fg"]),
        "fg_cycle": cycle_of(values["fg_trigger_rate"]),
        "ball_rate_bg": as_rate(values["multiplier_ball_rate_bg"]),
        "ball_rate_fg": as_rate(values["multiplier_ball_rate_fg"]),
    }


def report(label: str, result: dict) -> None:
    print(f"  {label:<28} RTP {result['rtp_total']:.4%} (BG {result['rtp_bg']:.4%} / FG {result['rtp_fg']:.4%})"
          f"  BG hit {result['hit_rate_bg']:.4%}  FG hit {result['hit_rate_fg']:.4%}"
          f"  cycle 1/{result['fg_cycle']:.1f}  ball BG {result['ball_rate_bg']:.4%} FG {result['ball_rate_fg']:.4%}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan-fg-shape", action="store_true")
    parser.add_argument("--solve-ball-share", action="store_true")
    parser.add_argument("--set-ball-share", type=float, default=None)
    parser.add_argument("--solve-offset", action="store_true")
    parser.add_argument("--ball-share", type=float, default=0.01029)
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--split-max", type=float, default=6.0)
    parser.add_argument("--fg-shape", choices=("competitor", "natural"), default="natural")
    parser.add_argument("--rounds", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=92_001)
    args = parser.parse_args()
    normal, bf, fg = natural_paths()
    ball_target = TARGETS.ball_spin_rate["BG"]

    if args.scan_fg_shape:
        print("[scan] FG 線型來源比較")
        for source in ("competitor", "natural"):
            calibrate_cards(normal, bf, fg, TARGETS.basic["fg_cycle"], ball_share=0.0,
                            fg_shape_source=source, verbose=False)
            report(f"fg_shape={source}", measure("config_92A.js", args.rounds, args.seed))

    if args.solve_ball_share:
        print(f"[solve] zero-win ball share (target BG ball rate {ball_target:.4%}, "
              f"fg_shape={args.fg_shape})")
        calibrate_cards(normal, bf, fg, TARGETS.basic["fg_cycle"], ball_share=0.0,
                        fg_shape_source=args.fg_shape, verbose=False,
                        ball_split_max=args.split_max)
        base = measure("config_92A.js", args.rounds, args.seed)
        report("ball_share=0", base)
        # every split card starts at ball_share = 0, so the measured rate is the
        # floor contributed by the unsplit high-interval tail
        share = (ball_target - base["ball_rate_bg"])
        share = min(max(share, 0.0), 1.0)
        print(f"  floor {base['ball_rate_bg']:.4%} -> ball_share {share:.6f}")
        calibrate_cards(normal, bf, fg, TARGETS.basic["fg_cycle"], ball_share=share,
                        fg_shape_source=args.fg_shape, verbose=False,
                        ball_split_max=args.split_max)
        tuned = measure("config_92A.js", args.rounds, args.seed + 1)
        report(f"ball_share={share:.5f}", tuned)
        print(f"  BG ball rate {base['ball_rate_bg']:.4%} -> {tuned['ball_rate_bg']:.4%}"
              f" (target {ball_target:.4%})")


    if args.set_ball_share is not None:
        share = args.set_ball_share
        print(f"[set] ball_share={share:.6f} fg_shape={args.fg_shape}")
        calibrate_cards(normal, bf, fg, TARGETS.basic["fg_cycle"], ball_share=share,
                        fg_shape_source=args.fg_shape, verbose=False,
                        ball_split_max=args.split_max)
        report(f"ball_share={share:.5f}", measure("config_92A.js", args.rounds, args.seed))


    if args.solve_offset:
        # The card weights are solved from the *natural* per-interval mean pay, but a
        # "without ball" card changes that conditional mean (ball spins sit at the top
        # of their interval).  One Newton step per iteration closes the gap.
        print(f"[offset] solving BG RTP compensation (ball_share={args.ball_share:.5f}, "
              f"fg_shape={args.fg_shape})")
        offset = 0.0
        for iteration in range(args.iterations):
            summary = calibrate_cards(normal, bf, fg, TARGETS.basic["fg_cycle"],
                                      ball_share=args.ball_share, fg_shape_source=args.fg_shape,
                                      bg_rtp_offset=offset, verbose=False,
                                      ball_split_max=args.split_max)
            target_bg = summary["config_92A.js"]["bg_rtp_target"]
            result = measure("config_92A.js", args.rounds, args.seed + iteration)
            report(f"offset={offset:+.5f}", result)
            gap = target_bg - result["rtp_bg"]
            print(f"    BG RTP {result['rtp_bg']:.4%} vs target {target_bg:.4%} -> gap {gap:+.4%}")
            if abs(gap) < 0.002:
                break
            offset += gap
        print(f"  final bg_rtp_offset = {offset:+.6f}")


if __name__ == "__main__":
    main()
