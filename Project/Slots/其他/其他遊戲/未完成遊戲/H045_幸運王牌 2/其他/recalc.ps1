# Recalculate a workbook in Excel and save, so formula cells carry cached values.
#
# IMPORTANT: openpyxl writes formulas but not their results, and it also DROPS
# existing cached results whenever it saves.  So this must be re-run after every
# openpyxl edit, and before xlsx_to_config.py - which reads cached values and
# would otherwise see blanks.
#
#   .\recalc.ps1 -Path .\H045192.xlsx,.\H045194.xlsx
param([Parameter(Mandatory = $true)][string[]]$Path)

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
try {
    foreach ($p in $Path) {
        $full = (Resolve-Path $p).Path
        $wb = $excel.Workbooks.Open($full)
        $excel.CalculateFullRebuild()
        $wb.Save()
        $wb.Close($true)
        Write-Output "recalculated $full"
    }
}
finally {
    $excel.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
}
