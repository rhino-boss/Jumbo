from __future__ import annotations

import hashlib
import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "config.js",
    "config_92A.js",
    "config_94A.js",
    "Simulator.py",
    "index.html",
    "Source/H0271.xlsx",
    "Source/H027192A.xlsx",
    "Source/H027194A.xlsx",
)


def main() -> None:
    stamp = datetime.now().strftime("%y%m%d_%H%M%S")
    target = ROOT / "Versions" / "0.0" / f"final_before_v1_{stamp}"
    target.mkdir(parents=True, exist_ok=False)
    hashes: list[str] = []
    for relative in FILES:
        source = ROOT / relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        hashes.append(f"{digest}  {relative.replace('\\', '/')}")
    (target / "SHA256SUMS.txt").write_text("\n".join(hashes) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
