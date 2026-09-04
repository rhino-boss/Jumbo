from pathlib import Path
import shutil
import win32com.client

root = Path(__file__).resolve().parents[1]
backup = root / "Versions" / "3.2.0.0" / "Source_Backup" / "H028188B_before_op_jackpot_scr_260903.xlsx"
target = root / "Source" / "H028188B_repair_test.xlsx"
shutil.copy2(backup, target)

excel = win32com.client.DispatchEx("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False
excel.AskToUpdateLinks = False
excel.AutomationSecurity = 3
try:
    book = excel.Workbooks.Open(str(target), UpdateLinks=0, ReadOnly=False)
    try:
        excel.Calculation = -4135  # xlCalculationManual
        excel.CalculateBeforeSave = False
        sheet = book.Worksheets("OP Jackpot")
        sheet.Rows(8).Delete()
        sheet.Rows(6).Delete()
        sheet.Range("B5:C7").Value = (
            ("NB_Newbie", 3_864_674_550),
            ("NB", 3_800_982_750),
            ("BF", 51_240_310_600),
        )
        sheet.Range("C5:C7").NumberFormat = "#,##0"
        book.Save()
    finally:
        book.Close(SaveChanges=False)
finally:
    excel.Quit()

print(target)
