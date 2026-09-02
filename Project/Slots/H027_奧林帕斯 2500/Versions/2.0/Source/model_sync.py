"""H027 v1 XLSX/config converter entry point."""

from pathlib import Path
import runpy


implementation = Path(__file__).resolve().parents[2] / "0.0" / "Source" / "model_sync.py"
runpy.run_path(str(implementation), run_name="__main__")
