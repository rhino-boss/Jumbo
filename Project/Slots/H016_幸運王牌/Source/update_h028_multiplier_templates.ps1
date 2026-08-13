param(
    [string]$Python = ".\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"
$sourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$payloadScript = Join-Path $sourceDir "prepare_h028_template_payload.py"
$payloadText = & $Python $payloadScript
if ($LASTEXITCODE -ne 0) { throw "Payload generator failed with exit code $LASTEXITCODE" }
$payload = $payloadText | ConvertFrom-Json -Depth 100

function Set-ColumnValues {
    param($Sheet, [string]$Address, $Values)
    $range = $Sheet.Range($Address)
    $rows = $range.Rows.Count
    if ($rows -ne $Values.Count) { throw "$Address expects $rows values, got $($Values.Count)" }
    $matrix = New-Object 'object[,]' $rows, 1
    for ($index = 0; $index -lt $rows; $index++) { $matrix[$index, 0] = $Values[$index] }
    $range.Value2 = $matrix
}

function Set-RegularFormulas {
    param($Sheet)
    for ($row = 234; $row -le 297; $row++) {
        $Sheet.Cells.Item($row, 4).Formula = "=IFERROR(B$row/SUM(`$B`$234:`$B`$297),0)"
        $Sheet.Cells.Item($row, 5).Formula = "=IFERROR(C$row/B$row/`$B`$3,0)"
        $Sheet.Cells.Item($row, 9).Formula = "=D$row*H$row"
        $Sheet.Cells.Item($row, 10).Formula = "=IFERROR(I$row/SUM(`$I`$234:`$I`$297),0)"
        $Sheet.Cells.Item($row, 11).Formula = "=INT(J$row*`$B`$2)"
        $Sheet.Cells.Item($row, 12).Formula = "=IFERROR(K$row/SUM(`$K`$234:`$K`$297),0)"
        $Sheet.Cells.Item($row, 13).Formula = "=L$row*E$row"
    }
}

$excel = $null
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.AskToUpdateLinks = $false

    foreach ($variant in $payload.variants) {
        $path = [IO.Path]::GetFullPath([string]$variant.path)
        if (-not (Test-Path -LiteralPath $path)) { throw "Workbook not found: $path" }
        $book = $null
        try {
            $book = $excel.Workbooks.Open($path, 0, $false)
            $overview = $book.Worksheets.Item("Overview")
            $weights = $book.Worksheets.Item("Multiplier_Weight")
            $detail = $book.Worksheets.Item("Detail")
            $newbie = $book.Worksheets.Item("Detail_Newbie")

            $overview.Range("B3").Value2 = [string]$variant.excel_version
            $detail.Range("B2").Value2 = [double]$payload.threshold
            $newbie.Range("B2").Value2 = [double]$payload.threshold

            foreach ($sheet in @($detail, $newbie)) {
                $sheet.Range("B13").Value2 = [double]$payload.rounds
                Set-ColumnValues $sheet "B15:B78" $payload.bg_counts
                Set-ColumnValues $sheet "C15:C78" $payload.bg_pay
                $sheet.Range("B79").Value2 = [double]$payload.trigger_count
                $sheet.Range("C79").Value2 = [double]$payload.trigger_bg_pay
                Set-ColumnValues $sheet "B86:B149" $payload.fg_counts
                Set-ColumnValues $sheet "C86:C149" $payload.fg_pay
                Set-ColumnValues $sheet "H15:H79" $variant.base_fix
                Set-ColumnValues $sheet "H86:H149" $variant.free_fix
            }

            Set-ColumnValues $detail "B163:B226" $payload.fg_counts
            Set-ColumnValues $detail "C163:C226" $payload.fg_pay
            Set-ColumnValues $detail "H163:H226" $variant.buy_fix

            # H026 uses a separate complete third purchase-mode block.  Clone
            # the existing H028 Buy Feature block so every visual detail stays
            # native to the supplied template, then leave its data/weights 0.
            $detail.Range("A159:U226").Copy($detail.Range("A230:U297"))
            foreach ($column in @(1, 7, 15)) { $detail.Cells.Item(230, $column).Value2 = "Super Buy" }
            foreach ($column in @(2, 8, 16)) { $detail.Cells.Item(230, $column).Value2 = "Free Game" }
            $detail.Range("B234:C297").Value2 = 0
            $detail.Range("H234:H297").Value2 = 0
            Set-RegularFormulas $detail

            # Summary row for the uncalibrated Super Buy block.
            $detail.Range("A8:J8").Copy($detail.Range("A9:J9"))
            $detail.Range("A9").Value2 = "Super Buy"
            $detail.Range("B9").Value2 = 250
            $detail.Range("C9").Formula = "=0"
            $detail.Range("D9").Formula = "=IFERROR(SUM(M234:M297)/B9,0)"
            $detail.Range("E9").Formula = "=SUM(C9:D9)"
            $detail.Range("F9").Formula = "=1"
            $detail.Range("G9").Formula = "=1/F9"
            $detail.Range("H9").Formula = "=D9*G9*B9"
            $detail.Range("I9").ClearContents()
            $detail.Range("J9").Formula = "=IFERROR(LOOKUP(2,1/(K234:K297<>0),P15:P78),0)"

            # Add Super Buy to Overview using the template's own Buy Feature
            # rows and formulas as the formatting source.
            $overview.Range("A12:D12").Copy($overview.Range("A13:D13"))
            $overview.Range("A13").Value2 = 25000
            $overview.Range("B13").Value2 = 250
            $overview.Range("C13").Formula = "=B25+B26"
            $overview.Range("D13").Value2 = "Super Buy"
            $overview.Range("A20:E22").Copy($overview.Range("A24:E26"))
            $overview.Range("A25").Formula = "=D13"
            $overview.Range("B25").Formula = "=Detail!C9"
            $overview.Range("C25").Formula = "=IFERROR(1/D25,0)"
            $overview.Range("D25").Value2 = 1
            $overview.Range("E25").Value2 = "Base Game"
            $overview.Range("A26").ClearContents()
            $overview.Range("B26").Formula = "=Detail!D9"
            $overview.Range("C26:D26").ClearContents()
            $overview.Range("E26").Value2 = "Free Game"

            # The new card column is formula-driven like the existing columns.
            $weights.Range("F2:F67").Copy($weights.Range("G2:G67"))
            $weights.Range("G2").Value2 = "Weight_SF"
            for ($row = 3; $row -le 66; $row++) {
                $detailRow = 231 + $row
                $weights.Cells.Item($row, 7).Formula = "=Detail!K$detailRow"
            }
            $weights.Range("G67").Formula = "=0"

            $excel.CalculateFullRebuild()
            $book.Save()
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

Write-Output "Updated H028192A.xlsx and H028194A.xlsx in place."
