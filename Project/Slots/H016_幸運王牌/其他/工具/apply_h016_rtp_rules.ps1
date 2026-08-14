param(
    [Parameter(Mandatory = $true)]
    [string]$PayloadPath
)

$ErrorActionPreference = "Stop"
$toolDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent (Split-Path -Parent $toolDir)
$sourceDir = Join-Path $projectDir "Source"
$payload = Get-Content -LiteralPath $PayloadPath -Raw -Encoding UTF8 | ConvertFrom-Json
$targets = @(
    @{ File = "H016192A.xlsx"; Key = "92"; Normal = 0.92; BG = 0.70; FG = 0.22 },
    @{ File = "H016194A.xlsx"; Key = "94"; Normal = 0.94; BG = 0.70; FG = 0.24 }
)

function Set-VerticalValues([object]$sheet, [int]$row, [int]$column, [object[]]$values) {
    $matrix = New-Object 'object[,]' $values.Count, 1
    for ($index = 0; $index -lt $values.Count; $index++) {
        $matrix[$index, 0] = [double]$values[$index]
    }
    $sheet.Range(
        $sheet.Cells.Item($row, $column),
        $sheet.Cells.Item($row + $values.Count - 1, $column)
    ).Value2 = $matrix
}

function Test-RuleRows(
    [object]$sheet,
    [int]$startRow,
    [object[]]$audit,
    [string]$scene
) {
    foreach ($item in $audit) {
        $row = $startRow + [int]$item.index
        $actual = [double]$sheet.Cells.Item($row, 13).Value2
        $target = [double]$item.target_scene_rtp
        if ([math]::Abs($actual - $target) -gt 0.000002) {
            throw "$scene $($item.range) RTP mismatch: actual=$actual target=$target"
        }
    }
}

$excel = $null
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.AskToUpdateLinks = $false

    foreach ($target in $targets) {
        $path = [IO.Path]::GetFullPath((Join-Path $sourceDir $target.File))
        if (-not (Test-Path -LiteralPath $path)) { throw "Missing workbook: $path" }
        $version = $payload.versions.($target.Key)
        $book = $null
        $save = $false
        try {
            $book = $excel.Workbooks.Open($path, 0, $false)
            if ($book.ReadOnly) {
                throw "$($target.File) is open or locked. Close it in Excel before applying weights."
            }
            $excel.Calculation = -4105
            $detail = $book.Worksheets.Item("Detail")
            $newbie = $book.Worksheets.Item("Detail_Newbie")

            Set-VerticalValues $detail 15 8 @($version.bg.fix)
            Set-VerticalValues $detail 86 8 @($version.fg.fix)
            Set-VerticalValues $detail 163 8 @($version.bf.fix)
            # SF is intentionally preserved from the previous version.
            Set-VerticalValues $newbie 15 8 @($version.newbie.bg.fix)
            Set-VerticalValues $newbie 86 8 @($version.newbie.fg.fix)

            $excel.CalculateFullRebuild()

            $normalRtp = [double]$detail.Range("E7").Value2
            $bgRtp = [double]$detail.Range("C7").Value2
            $fgRtp = [double]$detail.Range("D7").Value2
            $bfRtp = [double]$detail.Range("E8").Value2
            $sfRtp = [double]$detail.Range("E9").Value2
            $newbieRtp = [double]$newbie.Range("E7").Value2
            $newbieBgRtp = [double]$newbie.Range("C7").Value2
            $newbieFgRtp = [double]$newbie.Range("D7").Value2
            if ([math]::Abs($normalRtp - [double]$target.Normal) -gt 0.000003) {
                throw "$($target.File) Normal RTP mismatch: $normalRtp"
            }
            if ([math]::Abs($bgRtp - [double]$target.BG) -gt 0.000003) {
                throw "$($target.File) BG RTP mismatch: $bgRtp"
            }
            if ([math]::Abs($fgRtp - [double]$target.FG) -gt 0.000003) {
                throw "$($target.File) FG RTP mismatch: $fgRtp"
            }
            if ([math]::Abs($newbieRtp - 0.93) -gt 0.000003) {
                throw "$($target.File) Newbie RTP mismatch: $newbieRtp"
            }
            if ([math]::Abs($newbieBgRtp - 0.70) -gt 0.000003) {
                throw "$($target.File) Newbie BG RTP mismatch: $newbieBgRtp"
            }
            if ([math]::Abs($newbieFgRtp - 0.23) -gt 0.000003) {
                throw "$($target.File) Newbie FG RTP mismatch: $newbieFgRtp"
            }
            $expectedBfRtp = [double]$version.metrics.bf_rtp
            if ([math]::Abs($bfRtp - $expectedBfRtp) -gt 0.000003) {
                throw "$($target.File) BF RTP mismatch: $bfRtp expected=$expectedBfRtp"
            }
            if ([math]::Abs($sfRtp - 0.925) -gt 0.000003) {
                throw "$($target.File) SF RTP mismatch: $sfRtp"
            }
            foreach ($range in @("K15:K78", "K86:K149", "K163:K226", "K234:K297")) {
                $sum = [double]$excel.WorksheetFunction.Sum($detail.Range($range))
                if ($sum -ne 1000000000) { throw "$($target.File) $range weight sum is $sum" }
            }
            foreach ($range in @("K15:K78", "K86:K149")) {
                $sum = [double]$excel.WorksheetFunction.Sum($newbie.Range($range))
                if ($sum -ne 1000000000) { throw "$($target.File) Newbie $range weight sum is $sum" }
            }

            Test-RuleRows $detail 15 @($version.bg.audit) "BG"
            Test-RuleRows $detail 86 @($version.fg.audit) "FG"
            Test-RuleRows $detail 163 @($version.bf.audit) "BF"
            Test-RuleRows $newbie 15 @($version.newbie.bg.audit) "Newbie BG"
            Test-RuleRows $newbie 86 @($version.newbie.fg.audit) "Newbie FG"

            $formulaErrors = 0
            foreach ($sheetName in @("Overview", "Multiplier_Weight", "Detail", "Detail_Newbie")) {
                try {
                    $formulaErrors += $book.Worksheets.Item($sheetName).UsedRange.SpecialCells(-4123, 16).Count
                }
                catch {}
            }
            if ($formulaErrors -ne 0) { throw "$($target.File) has $formulaErrors formula errors" }

            $book.Save()
            $save = $true
            Write-Output (ConvertTo-Json ([ordered]@{
                file = $target.File
                normal_rtp = $normalRtp
                bg_rtp = $bgRtp
                fg_rtp = $fgRtp
                bf_rtp = $bfRtp
                sf_rtp = $sfRtp
                newbie_rtp = $newbieRtp
                newbie_bg_rtp = $newbieBgRtp
                newbie_fg_rtp = $newbieFgRtp
                bg_fixed_rows = @($version.bg.audit).Count
                fg_fixed_rows = @($version.fg.audit).Count
                bf_fixed_rows = @($version.bf.audit).Count
                sf_fixed_rows = @($version.sf.audit).Count
            }) -Compress)
        }
        finally {
            if ($book) {
                $book.Close($false)
                [Runtime.InteropServices.Marshal]::FinalReleaseComObject($book) | Out-Null
            }
        }
        if (-not $save) { throw "Workbook validation failed before save: $($target.File)" }
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

Write-Output "Applied H016 competitor-relative per-range RTP rules to 92/94 workbooks."
