from pathlib import Path
import shutil
import win32com.client

root = Path(__file__).resolve().parents[1]
backup_dir = root / "Versions" / "3.2.0.0" / "Source_Backup"
output_dir = root / "Source"

newbie_scr = 3_864_674_550
bf_scr = 51_240_310_600
oldhand = {
    "H028188B.xlsx": 3_800_982_750,
    "H028190B.xlsx": 3_805_450_200,
    "H028192A.xlsx": 3_834_937_400,
    "H028194A.xlsx": 3_836_181_680,
}

jobs = []
for name, nb_scr in oldhand.items():
    backup = backup_dir / f"{Path(name).stem}_before_op_jackpot_scr_260903.xlsx"
    output = output_dir / f"{Path(name).stem}_repaired.xlsx"
    shutil.copy2(backup, output)
    jobs.append((output, nb_scr))

excel = win32com.client.DispatchEx("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False
excel.AskToUpdateLinks = False
excel.AutomationSecurity = 3
try:
    for output, nb_scr in jobs:
        book = excel.Workbooks.Open(str(output), UpdateLinks=0, ReadOnly=False)
        try:
            excel.Calculation = -4135  # xlCalculationManual
            excel.CalculateBeforeSave = False
            sheet = book.Worksheets("OP Jackpot")
            sheet.Rows(8).Delete()
            sheet.Rows(6).Delete()
            sheet.Range("B5:C7").Value = (
                ("NB_Newbie", newbie_scr),
                ("NB", nb_scr),
                ("BF", bf_scr),
            )
            sheet.Range("C5:C7").NumberFormat = "#,##0"
            book.Save()
        finally:
            book.Close(SaveChanges=False)
        print(f"BUILT {output.name}")
finally:
    excel.Quit()
