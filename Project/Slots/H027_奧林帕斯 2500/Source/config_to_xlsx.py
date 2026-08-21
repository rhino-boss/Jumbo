"""Specification-compatible H027 base/RTP config -> XLSX entry point."""

import subprocess
import sys
from pathlib import Path

from model_sync import run_import


if __name__ == "__main__":
    arguments = sys.argv[1:]
    variants = "--variants" in arguments or "--all" in arguments
    all_models = "--all" in arguments
    check = "--check" in arguments
    if not variants or all_models:
        run_import(["--check"] if check else ["--in-place", "--force"])
    if variants:
        script = Path(__file__).with_name("rtp_xlsx_config.py")
        command = "check" if check else "import"
        subprocess.run([sys.executable, str(script), command], check=True)
