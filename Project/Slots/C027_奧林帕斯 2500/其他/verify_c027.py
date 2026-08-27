"""C027 正式驗證批次.

固定卡片參數後，跑出報告要用的六份 Record：

    Card System Off  Normal Bet / Buy Feature / 自然 FG probe   （自然機率基準）
    Card System On   92A、94A 各 Normal Bet / Buy Feature       （玩家實際版本）

    py verify_c027.py --calibrate      # 用定案參數重寫卡片權重
    py verify_c027.py --run            # 跑六份報表並印出摘要
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from competitor_targets import Targets
from fit_c027_model import OTHER, RECORD, calibrate_cards, probe_natural_fg, run_simulator
from tune_c027 import measure, natural_paths, report

TARGETS = Targets()


# 定案的卡片校準參數
#   ball_share = 0：得分 <= ball_split_max 的區間卡一律要求「最終盤面沒有倍數球」。
#     Card-On 的 BG 倍數球出現率因此由 6.618% 降到 3.750%（競品 2.737%）。
#     再往上調 ball_split_max 會讓「高得分但無球」的卡片打到 Retry Limit，
#     實測 split_max=12 時 BG Hit Rate 掉 1.09 pp、總 RTP 掉到 79.7%，因此停在 6。
#   fg_rtp_share = None：沿用競品的 BG:FG RTP 比例。
FINAL = {
    "cycle": TARGETS.basic["fg_cycle"],
    "ball_share": 0.0,
    "ball_split_max": 6.0,
    "fg_shape_source": "competitor",
    "bg_rtp_offset": 0.0,
    "fg_rtp_share": None,
}

NORMAL_ROUNDS = 1_200_000
BUY_ROUNDS = 200_000
NATURAL_ROUNDS = 1_000_000


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calibrate", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--natural", action="store_true")
    parser.add_argument("--normal-rounds", type=int, default=NORMAL_ROUNDS)
    parser.add_argument("--buy-rounds", type=int, default=BUY_ROUNDS)
    args = parser.parse_args()

    produced: dict[str, str] = {}

    if args.natural:
        print("[natural] Card System Off 基準")
        normal = run_simulator("config.js", "config.js", 0, NATURAL_ROUNDS, False, False, 27001)
        buy = run_simulator("config.js", "config.js", 2, NATURAL_ROUNDS, False, False, 27201)
        probe = probe_natural_fg(NATURAL_ROUNDS)
        produced.update({"natural_normal": normal.name, "natural_buy": buy.name,
                         "natural_fg_probe": probe.name})
        for key, value in produced.items():
            print(f"  {key}: {value}")

    if args.calibrate:
        print("[calibrate] 套用定案卡片參數")
        print(f"  {json.dumps(FINAL, ensure_ascii=False)}")
        normal, buy, probe = natural_paths()
        summary = calibrate_cards(normal, buy, probe, FINAL["cycle"],
                                  ball_share=FINAL["ball_share"],
                                  ball_split_max=FINAL["ball_split_max"],
                                  fg_shape_source=FINAL["fg_shape_source"],
                                  bg_rtp_offset=FINAL["bg_rtp_offset"],
                                  fg_rtp_share=FINAL["fg_rtp_share"])
        (OTHER / "fit_card_summary.json").write_text(
            json.dumps({"parameters": FINAL, "variants": summary}, ensure_ascii=False, indent=2),
            encoding="utf-8")

    if args.run:
        print("[run] Card System On 驗證")
        for config_rtp, seed in (("config_92A.js", 92_001), ("config_94A.js", 94_001)):
            normal_result = measure(config_rtp, args.normal_rounds, seed, bet_mode=0)
            report(f"{config_rtp} Normal", normal_result)
            buy_result = measure(config_rtp, args.buy_rounds, seed + 200, bet_mode=2)
            report(f"{config_rtp} Buy   ", buy_result)
            produced[f"{config_rtp}_normal"] = normal_result["report"]
            produced[f"{config_rtp}_buy"] = buy_result["report"]

    if produced:
        path = OTHER / "verify_c027_reports.json"
        existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        existing.update(produced)
        path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  報表清單寫入 {path.name}")


if __name__ == "__main__":
    main()
