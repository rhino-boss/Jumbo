"""Current H027 XLSX/config converter entry point (physical model v1)."""

from pathlib import Path
import runpy


implementation = Path(__file__).resolve().parent.parent / "Versions" / "1.0" / "Source" / "model_sync.py"
runpy.run_path(str(implementation), run_name="__main__")
