param([string]$Version = "6.0.0.0")

$ErrorActionPreference = "Stop"
$projectDir = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
$excel = $null
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    foreach ($name in @("H016192A.xlsx", "H016194A.xlsx")) {
        $path = [IO.Path]::GetFullPath((Join-Path $projectDir "Source\$name"))
        $book = $null
        try {
            $book = $excel.Workbooks.Open($path, 0, $false)
            if ($book.ReadOnly) { throw "$name is open or locked" }
            $book.Worksheets.Item("Overview").Range("B3").Value2 = $Version
            $book.Save()
            Write-Output "$name -> $Version"
        }
        finally {
            if ($book) {
                $book.Close($false)
                [Runtime.InteropServices.Marshal]::FinalReleaseComObject($book) | Out-Null
            }
        }
    }
}
finally {
    if ($excel) {
        $excel.Quit()
        [Runtime.InteropServices.Marshal]::FinalReleaseComObject($excel) | Out-Null
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
