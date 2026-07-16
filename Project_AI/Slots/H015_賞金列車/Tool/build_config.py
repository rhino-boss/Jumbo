from pathlib import Path
import subprocess
import sys


def main() -> None:
    script_path = Path(__file__).with_name("xlsx_to_config.py")
    result = subprocess.run([sys.executable, str(script_path)], check=False)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
