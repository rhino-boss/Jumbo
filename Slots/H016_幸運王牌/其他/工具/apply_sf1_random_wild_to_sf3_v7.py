from __future__ import annotations

from pathlib import Path

import win32com.client


PROJECT_DIR = Path(__file__).resolve().parents[2]
SOURCE_DIR = PROJECT_DIR / "Source"
BASE_PATH = SOURCE_DIR / "H0161.xlsx"
VARIANT_PATHS = (
    SOURCE_DIR / "H016192A.xlsx",
    SOURCE_DIR / "H016194A.xlsx",
)
EXPECTED = [(0, 0), (2, 1000), (3, 300), (4, 100)]


def random_wild_pairs(sheet) -> list[tuple[int, int]]:
    return [
        (int(sheet.Cells(row, 29).Value), int(sheet.Cells(row, 30).Value))
        for row in range(4, 8)
    ]


def main() -> None:
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    opened = []
    try:
        base = excel.Workbooks.Open(str(BASE_PATH.resolve()), UpdateLinks=0, ReadOnly=False)
        opened.append(base)
        source = base.Worksheets("SF_Symbol")
        target = base.Worksheets("SF_Symbol (3)")
        source_pairs = random_wild_pairs(source)
        if source_pairs != EXPECTED:
            raise ValueError(f"Unexpected SF_Symbol Random Wild: {source_pairs!r}")
        for row in range(4, 8):
            target.Cells(row, 29).Value = source.Cells(row, 29).Value
            target.Cells(row, 30).Value = source.Cells(row, 30).Value
        base.Worksheets("Overview").Range("B3").Value = "7"
        base.Save()
        if random_wild_pairs(target) != EXPECTED:
            raise ValueError("SF_Symbol (3) Random Wild verification failed")
        base.Close(SaveChanges=False)
        opened.remove(base)

        for path in VARIANT_PATHS:
            workbook = excel.Workbooks.Open(str(path.resolve()), UpdateLinks=0, ReadOnly=False)
            opened.append(workbook)
            workbook.Worksheets("Overview").Range("B3").Value = "7.0.0.0"
            workbook.Save()
            workbook.Close(SaveChanges=False)
            opened.remove(workbook)
    finally:
        for workbook in reversed(opened):
            workbook.Close(SaveChanges=False)
        excel.Quit()

    print("H016 v7: copied SF_Symbol Random Wild 0/1000/300/100 to SF_Symbol (3)")


if __name__ == "__main__":
    main()
