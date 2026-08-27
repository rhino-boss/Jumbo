"""Run the reproducible v1 Card-System validation matrix."""

from __future__ import annotations

import os
import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNS = (
    ("config_92A.js", 0),
    ("config_92A.js", 2),
    ("config_94A.js", 0),
    ("config_94A.js", 2),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=100000)
    parser.add_argument("--only", choices=("92A-normal", "92A-bf", "94A-normal", "94A-bf"))
    parser.add_argument("--natural-bf", action="store_true")
    args = parser.parse_args()
    selected = RUNS
    card_enabled = True
    if args.natural_bf:
        selected = (("config.js", 2),)
        card_enabled = False
    elif args.only:
        code, mode_name = args.only.split("-", 1)
        selected = ((f"config_{code}.js", 0 if mode_name == "normal" else 2),)
    for config_name, bet_mode in selected:
        env = os.environ.copy()
        env.update(
            {
                "H027_CONFIG_FILE": "config.js",
                "H027_CONFIG_RTP_FILE": config_name,
                "H027_BET_MODE": str(bet_mode),
                "H027_TOTAL_ROUNDS": str(args.rounds),
                "H027_CARD_SYSTEM_ENABLED": "true" if card_enabled else "false",
                "H027_CARD_SYSTEM_IS_NEWBIE": "false",
                "H027_BASE_BET": "1",
                "H027_RUN_ALL_COMBINATIONS": "false",
                "H027_OUTPUT_REPORT": "true",
                "H027_SHOW_CONSOLE_SUMMARY": "true",
                "H027_BATCH_CHILD": "1",
                "PYTHONUTF8": "1",
                "PYTHONUNBUFFERED": "1",
            }
        )
        print(f"\n=== {config_name} / bet mode {bet_mode} ===", flush=True)
        subprocess.run([sys.executable, str(ROOT / "Simulator.py")], cwd=ROOT, env=env, check=True)


if __name__ == "__main__":
    main()
