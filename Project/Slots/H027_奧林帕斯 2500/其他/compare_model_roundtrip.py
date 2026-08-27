from __future__ import annotations

import importlib.util
import json
from pathlib import Path


root = Path(__file__).resolve().parent.parent
module_path = root / "Versions" / "0.0" / "Source" / "model_sync.py"
spec = importlib.util.spec_from_file_location("h027_model_sync", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
expected = module.load_js_config(root / "config.js")
actual = module.build_config(root / "Source" / "H0271.xlsx")


def walk(left, right, path=""):
    if type(left) is not type(right):
        print(path, type(left).__name__, type(right).__name__, left, right)
        return
    if isinstance(left, dict):
        for key in sorted(set(left) | set(right)):
            if key not in left or key not in right:
                print(path + "." + key, left.get(key, "<missing>"), right.get(key, "<missing>"))
            else:
                walk(left[key], right[key], path + "." + key)
    elif isinstance(left, list):
        if len(left) != len(right):
            print(path + ".length", len(left), len(right))
        for index, (a, b) in enumerate(zip(left, right)):
            walk(a, b, f"{path}[{index}]")
    elif left != right:
        print(path, left, right)


walk(expected, actual)
if expected != actual:
    raise SystemExit("H0271.xlsx round-trip mismatch")

physical_keys = (
    "strip_names", "strips", "parameter", "cascade_symbol_source",
    "reel_source_workbook", "reel_set_usage",
)
for filename in ("config_92A.js", "config_94A.js"):
    variant = module.load_js_config(root / filename)
    mismatched = [key for key in physical_keys if variant.get(key) != expected.get(key)]
    if mismatched:
        raise SystemExit(f"{filename} physical model differs: {mismatched}")

print("Round-trip and Base/92A/94A physical model consistency: OK")
