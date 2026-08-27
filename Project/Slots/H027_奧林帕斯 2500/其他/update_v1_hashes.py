from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "Versions" / "1.0"
FILES = (
    "config.js",
    "config_92A.js",
    "config_94A.js",
    "Simulator.py",
    "index.html",
    "game_rule.md",
    "Source/H0271.xlsx",
    "Source/H027192A.xlsx",
    "Source/H027194A.xlsx",
    "Source/model_sync.py",
)


def main() -> None:
    lines = []
    for relative in FILES:
        path = ROOT / relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {relative}")
    output = ROOT / "SHA256SUMS.txt"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Updated: {output}")


if __name__ == "__main__":
    main()
