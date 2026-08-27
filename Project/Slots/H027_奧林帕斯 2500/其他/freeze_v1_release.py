from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "Versions" / "1.0"
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
)


def main() -> None:
    rows: list[str] = []
    for relative in FILES:
        source = ROOT / relative
        destination = TARGET / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        rows.append(f"{hashlib.sha256(destination.read_bytes()).hexdigest()}  {relative}")
    tool = TARGET / "Source" / "model_sync.py"
    rows.append(f"{hashlib.sha256(tool.read_bytes()).hexdigest()}  Source/model_sync.py")
    (TARGET / "SHA256SUMS.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(TARGET)


if __name__ == "__main__":
    main()
