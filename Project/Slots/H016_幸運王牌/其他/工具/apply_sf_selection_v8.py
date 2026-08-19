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
SF3_RANDOM_WILD = [(0, 0), (2, 1000), (3, 0), (4, 0)]
SF_SELECTION = [0, 5500, 4500]


def main() -> None:
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    opened = []
    try:
        base = excel.Workbooks.Open(str(BASE_PATH.resolve()), UpdateLinks=0, ReadOnly=False)
        opened.append(base)
        parameter = base.Worksheets("Parameter")
        sf3 = base.Worksheets("SF_Symbol (3)")

        for row, (value, weight) in zip(range(4, 8), SF3_RANDOM_WILD):
            sf3.Cells(row, 29).Value = value
            sf3.Cells(row, 30).Value = weight
        for rows in ((25, 26, 27), (32, 33, 34)):
            for row, weight in zip(rows, SF_SELECTION):
                parameter.Cells(row, 3).Value = weight
        base.Worksheets("Overview").Range("B3").Value = "8"
        base.Save()
        base.Close(SaveChanges=False)
        opened.remove(base)

        for path in VARIANT_PATHS:
            workbook = excel.Workbooks.Open(str(path.resolve()), UpdateLinks=0, ReadOnly=False)
            opened.append(workbook)
            workbook.Worksheets("Overview").Range("B3").Value = "8.0.0.0"
            workbook.Save()
            workbook.Close(SaveChanges=False)
            opened.remove(workbook)
    finally:
        for workbook in reversed(opened):
            workbook.Close(SaveChanges=False)
        excel.Quit()

    print("H016 v8: SF3 Random Wild = 0:1000:0:0; SF selection = 0:5500:4500")


if __name__ == "__main__":
    main()
