from pathlib import Path
import sys

import pandas as pd


root = Path(__file__).resolve().parent.parent
pattern = sys.argv[1] if len(sys.argv) > 1 else "*.xlsx"
path = max((root / "Record").glob(pattern), key=lambda item: item.stat().st_mtime)
print(path.name)
book = pd.ExcelFile(path)
print(book.sheet_names)
for sheet in ("Overview", "Cascade", "Ball Cascade", "Symbol Hit Rate", "C2-C3 Multiplier", "Multiplier Line"):
    if sheet in book.sheet_names:
        print(f"\n[{sheet}]")
        print(pd.read_excel(path, sheet_name=sheet).to_string(index=False))
