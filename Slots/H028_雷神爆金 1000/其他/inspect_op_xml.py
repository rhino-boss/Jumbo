from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
files = [
    root / "Versions" / "3.2.0.0" / "Source_Backup" / "H028192A_before_op_jackpot_scr_260903.xlsx",
    root / "Source" / "H028192A_repaired.xlsx",
]

for path in files:
    print("\nFILE", path.name)
    with zipfile.ZipFile(path) as z:
        print(z.read("xl/workbook.xml").decode("utf-8"))
        print(z.read("xl/_rels/workbook.xml.rels").decode("utf-8"))
        print("SHEET5", z.read("xl/worksheets/sheet5.xml").decode("utf-8"))
        for name in z.namelist():
            if name.startswith("xl/worksheets/sheet"):
                data = z.read(name)
                if b"Threshold" in data or b"NB_Newbie" in data:
                    print("PART", name)
                    print(data.decode("utf-8"))
        if "xl/sharedStrings.xml" in z.namelist():
            data = z.read("xl/sharedStrings.xml")
            print("SHARED size", len(data), "NB index context", data.find(b"NB_Newbie"), "EB context", data.find(b"EB_Newbie"))
