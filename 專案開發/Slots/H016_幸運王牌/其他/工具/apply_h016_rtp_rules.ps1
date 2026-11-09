param(
    [Parameter(Mandatory = $true)]
    [string]$PayloadPath,
    [ValidateSet("All", "92", "94")]
    [string]$TargetVersion = "All",
    [ValidateSet("All", "SF")]
    [string]$Scene = "All"
)

$ErrorActionPreference = "Stop"
$toolDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent (Split-Path -Parent $toolDir)
$sourceDir = Join-Path $projectDir "Source"
$payload = Get-Content -LiteralPath $PayloadPath -Raw -Encoding UTF8 | ConvertFrom-Json
$targets = @(
    @{ File = "H016192A.xlsx"; Key = "92"; Normal = 0.92; BG = 0.65; FG = 0.27; NewbieNormal = 0.93; NewbieBG = 0.65; NewbieFG = 0.28 },
    @{ File = "H016194A.xlsx"; Key = "94"; Normal = 0.94; BG = 0.65; FG = 0.29; NewbieNormal = 0.93; NewbieBG = 0.65; NewbieFG = 0.28 }
)
if ($TargetVersion -ne "All") {
    $targets = @($targets | Where-Object { $_.Key -eq $TargetVersion })
}

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

function Set-RegularBlockFormulas(
    [object]$sheet,
    [int]$startRow,
    [int]$endRow
) {
    foreach ($column in @(4, 5, 9, 10, 11, 12, 13, 17, 21)) {
        $sheet.Range(
            $sheet.Cells.Item($startRow, $column),
            $sheet.Cells.Item($endRow, $column)
        ).ClearContents() | Out-Null
    }
    $sheet.Range("D${startRow}:D${endRow}").FormulaR1C1 = "=IFERROR(RC[-2]/SUM(R${startRow}C2:R${endRow}C2),0)"
    $sheet.Range("E${startRow}:E${endRow}").FormulaR1C1 = "=IFERROR(RC[-2]/RC[-3]/R3C2,0)"
    $sheet.Range("I${startRow}:I${endRow}").FormulaR1C1 = "=RC[-5]*RC[-1]"
    $sheet.Range("J${startRow}:J${endRow}").FormulaR1C1 = "=IFERROR(RC[-1]/SUM(R${startRow}C9:R${endRow}C9),0)"
    $sheet.Range("K${startRow}:K${endRow}").FormulaR1C1 = "=INT(RC[-1]*R2C2)"
    $sheet.Range("L${startRow}:L${endRow}").FormulaR1C1 = "=IFERROR(RC[-1]/SUM(R${startRow}C11:R${endRow}C11),0)"
    $sheet.Range("M${startRow}:M${endRow}").FormulaR1C1 = "=RC[-1]*RC[-8]"
    $sheet.Range("Q${startRow}:Q${endRow}").FormulaR1C1 = "=RC[-5]"
    $sheet.Range("U${startRow}:U${endRow}").FormulaR1C1 = "=IFERROR(ROUND(RC[-1]/RC[-9],2),0)"
}

function Set-RegularDetailFormulas([object]$sheet, [bool]$includeFeatureBlocks) {
    # Base Game has 64 ordinary ranges plus one independent Free Game entry row.
    foreach ($column in @(4, 5, 9, 10, 11, 12, 13)) {
        $endRow = if ($column -in @(4, 10)) { 78 } else { 79 }
        $sheet.Range(
            $sheet.Cells.Item(15, $column),
            $sheet.Cells.Item($endRow, $column)
        ).ClearContents() | Out-Null
    }
    foreach ($column in @(17, 21)) {
        $sheet.Range(
            $sheet.Cells.Item(15, $column),
            $sheet.Cells.Item(78, $column)
        ).ClearContents() | Out-Null
    }
    $sheet.Range("D15:D78").FormulaR1C1 = "=IFERROR(RC[-2]/SUM(R15C2:R78C2),0)"
    $sheet.Range("E15:E79").FormulaR1C1 = "=IFERROR(RC[-2]/RC[-3]/R3C2,0)"
    $sheet.Range("I15:I79").FormulaR1C1 = "=RC[-5]*RC[-1]"
    $sheet.Range("J15:J78").FormulaR1C1 = "=IFERROR(RC[-1]/SUM(R15C9:R78C9),0)"
    $sheet.Range("J79").FormulaR1C1 = "=RC[-1]"
    $sheet.Range("K15:K79").FormulaR1C1 = "=INT(RC[-1]*R2C2)"
    $sheet.Range("L15:L79").FormulaR1C1 = "=IFERROR(RC[-1]/SUM(R15C11:R79C11),0)"
    $sheet.Range("M15:M79").FormulaR1C1 = "=RC[-1]*RC[-8]"
    $sheet.Range("Q15:Q78").FormulaR1C1 = "=RC[-5]"
    $sheet.Range("U15:U78").FormulaR1C1 = "=IFERROR(ROUND(RC[-1]/RC[-9],2),0)"

    Set-RegularBlockFormulas $sheet 86 149
    if ($includeFeatureBlocks) {
        Set-RegularBlockFormulas $sheet 163 226
        $sheet.Range("L156").Formula = "=IFERROR(K156/SUM(K156),0)"
    }

    $sheet.Range("D7").Formula = "=SUM(M86:M149)*F7"
    $sheet.Range("I7").Formula = "=IFERROR(LOOKUP(2,1/(K15:K78<>0),P15:P78),0)"
    $sheet.Range("J7").Formula = "=IFERROR(LOOKUP(2,1/(K86:K149<>0),P86:P149),0)"
    if ($includeFeatureBlocks) {
        $sheet.Range("B7:B8").ClearContents() | Out-Null
        $sheet.Range("B7").Formula = "=Overview!B11"
        $sheet.Range("B8").Formula = "=Overview!B12"
        $sheet.Range("D8").Formula = "=SUM(M163:M226)/B8"
        $sheet.Range("J8").Formula = "=IFERROR(LOOKUP(2,1/(K163:K226<>0),P163:P226),0)"
    }
}

function Set-RegularOverviewFormulas([object]$sheet) {
    $sheet.Range("A11:A12").ClearContents() | Out-Null
    $sheet.Range("A11:A12").FormulaR1C1 = "=RC[1]*R7C1"
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
            if ($null -ne $payload.version) {
                $book.Worksheets.Item("Overview").Range("B3").Value2 = [string]$payload.version
            }
            if ($Scene -eq "SF") {
                if ($null -eq $payload.sf_source_report) {
                    throw "SF-only apply requires sf_source_report"
                }
                Set-RegularBlockFormulas $detail 234 297
                Set-VerticalValues $detail 234 2 @($payload.sf_source_report.sf_count)
                Set-VerticalValues $detail 234 3 @($payload.sf_source_report.sf_pay)
                Set-VerticalValues $detail 234 8 @($version.sf.fix)
                $excel.CalculateFullRebuild()

                $sfRtp = [double]$detail.Range("E9").Value2
                if ([math]::Abs($sfRtp - 0.925) -gt 0.000003) {
                    throw "$($target.File) SF RTP mismatch: $sfRtp"
                }
                $sfWeightTotal = [double]$excel.WorksheetFunction.Sum($detail.Range("K234:K297"))
                if ($sfWeightTotal -ne 1000000000) {
                    throw "$($target.File) SF weight total is $sfWeightTotal"
                }
                Test-RuleRows $detail 234 @($version.sf.audit) "SF"
                $minimumIndex = [int]$version.sf.minimum_weighted_index
                $minimumRow = 234 + $minimumIndex
                $belowMinimumWeight = if ($minimumRow -gt 234) {
                    [double]$excel.WorksheetFunction.Sum($detail.Range("K234:K$($minimumRow - 1)"))
                } else { 0.0 }
                $minimumWeight = [double]$detail.Cells.Item($minimumRow, 11).Value2
                if ($belowMinimumWeight -ne 0 -or $minimumWeight -le 0) {
                    throw "$($target.File) SF minimum weighted range does not match payload index $minimumIndex"
                }
                $sfSceneRtp = [double]$excel.WorksheetFunction.Sum($detail.Range("M234:M297"))
                $maxRangeRtp = 0.0
                for ($row = 234; $row -le 297; $row++) {
                    $weight = [double]$detail.Cells.Item($row, 11).Value2
                    $naturalRate = [double]$detail.Cells.Item($row, 4).Value2
                    $rowRtp = [double]$detail.Cells.Item($row, 13).Value2
                    if ($weight -gt 0 -and $naturalRate -le 0.0007) {
                        throw "$($target.File) SF row $row has weight with natural probability at or below 0.07%"
                    }
                    if ($rowRtp -gt $maxRangeRtp) { $maxRangeRtp = $rowRtp }
                }
                if ($maxRangeRtp / $sfSceneRtp -gt 0.15000001) {
                    throw "$($target.File) SF single-range RTP share exceeds 15%"
                }
                $boostIndices = @($version.sf.boost_indices | ForEach-Object { [int]$_ })
                for ($row = $minimumRow; $row -lt 297; $row++) {
                    $currentHitWeight = [double]$detail.Cells.Item($row, 11).Value2
                    $nextHitWeight = [double]$detail.Cells.Item($row + 1, 11).Value2
                    $nextIndex = $row + 1 - 234
                    if ($currentHitWeight -lt $nextHitWeight -and $nextIndex -notin $boostIndices) {
                        throw "$($target.File) SF Hit Rate rises from row $row to $($row + 1)"
                    }
                }
                $formulaErrors = 0
                foreach ($sheetName in @("Overview", "Multiplier_Weight", "Detail", "Detail_Newbie")) {
                    try {
                        $formulaErrors += $book.Worksheets.Item($sheetName).UsedRange.SpecialCells(-4123, 16).Count
                    }
                    catch {}
                }
                if ($formulaErrors -ne 0) {
                    throw "$($target.File) has $formulaErrors formula errors"
                }
                $book.Save()
                $save = $true
                Write-Output (ConvertTo-Json ([ordered]@{
                    file = $target.File
                    scene = "SF"
                    sf_rtp = $sfRtp
                    sf_fixed_rows = @($version.sf.audit).Count
                    max_range_rtp_share = $maxRangeRtp / $sfSceneRtp
                }) -Compress)
                continue
            }
            Set-RegularOverviewFormulas $book.Worksheets.Item("Overview")
            Set-RegularDetailFormulas $detail $true
            Set-RegularDetailFormulas $newbie $false

            if ($null -ne $payload.source_report) {
                $oldhandTriggerCount = $version.metrics.trigger_bg_count
                $oldhandTriggerPay = $version.metrics.trigger_bg_pay
                $newbieTriggerCount = $version.metrics.newbie_trigger_bg_count
                $newbieTriggerPay = $version.metrics.newbie_trigger_bg_pay
                $entryWeight = $version.metrics.entry_weight
                # Legacy payloads predate per-Profile cap selection.
                if ($null -eq $oldhandTriggerCount) { $oldhandTriggerCount = $payload.source_report.trigger_count }
                if ($null -eq $oldhandTriggerPay) { $oldhandTriggerPay = $payload.source_report.trigger_pay }
                if ($null -eq $newbieTriggerCount) { $newbieTriggerCount = $payload.source_report.trigger_count }
                if ($null -eq $newbieTriggerPay) { $newbieTriggerPay = $payload.source_report.trigger_pay }
                foreach ($sheet in @($detail, $newbie)) {
                    $sheet.Range("B13").Value2 = [double]$payload.source_report.rounds
                    Set-VerticalValues $sheet 15 2 @($payload.source_report.bg_count)
                    Set-VerticalValues $sheet 15 3 @($payload.source_report.bg_pay)
                    Set-VerticalValues $sheet 86 2 @($payload.source_report.fg_count)
                    Set-VerticalValues $sheet 86 3 @($payload.source_report.fg_pay)
                }
                # Trigger-spin BG count/pay are conditional on each Profile's
                # maximum enabled BG range.  They are selected from the report's
                # cumulative <= upper-bound columns by the payload builder.
                $detail.Range("B79").Value2 = [double]$oldhandTriggerCount
                $detail.Range("C79").Value2 = [double]$oldhandTriggerPay
                $newbie.Range("B79").Value2 = [double]$newbieTriggerCount
                $newbie.Range("C79").Value2 = [double]$newbieTriggerPay
                if ($null -ne $entryWeight) {
                    # B79/C79 are cap-eligible trigger samples, while K79 owns the
                    # approved FG entry cycle. Recalculate Fix Num so changing a
                    # Profile cap cannot silently change that cycle weight.
                    $rounds = [double]$payload.source_report.rounds
                    $weightTotal = 1000000000.0
                    $detail.Range("H79").Value2 = (
                        ([double]$entryWeight / $weightTotal) /
                        ([double]$oldhandTriggerCount / $rounds)
                    )
                    $newbie.Range("H79").Value2 = (
                        ([double]$entryWeight / $weightTotal) /
                        ([double]$newbieTriggerCount / $rounds)
                    )
                }
                if ($null -ne $payload.bf_source_report) {
                    Set-VerticalValues $detail 163 2 @($payload.bf_source_report.bf_count)
                    Set-VerticalValues $detail 163 3 @($payload.bf_source_report.bf_pay)
                }
                else {
                    Set-VerticalValues $detail 163 2 @($payload.source_report.fg_count)
                    Set-VerticalValues $detail 163 3 @($payload.source_report.fg_pay)
                }
            }
            if ($null -ne $payload.sf_source_report) {
                Set-VerticalValues $detail 234 2 @($payload.sf_source_report.sf_count)
                Set-VerticalValues $detail 234 3 @($payload.sf_source_report.sf_pay)
            }

            Set-VerticalValues $detail 15 8 @($version.bg.fix)
            Set-VerticalValues $detail 86 8 @($version.fg.fix)
            Set-VerticalValues $detail 163 8 @($version.bf.fix)
            # SF is only updated when a dedicated card-off SF source is present.
            if ($null -ne $payload.sf_source_report) {
                Set-VerticalValues $detail 234 8 @($version.sf.fix)
            }
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
            if ($null -ne $payload.source_report) {
                if ([double]$detail.Range("C79").Value2 -ne [double]$oldhandTriggerPay) {
                    throw "$($target.File) Detail!C79 does not match the oldhand cap selection"
                }
                if ([double]$newbie.Range("C79").Value2 -ne [double]$newbieTriggerPay) {
                    throw "$($target.File) Detail_Newbie!C79 does not match the newbie cap selection"
                }
                if ($null -ne $entryWeight) {
                    if ([math]::Abs([double]$detail.Range("K79").Value2 - [double]$entryWeight) -gt 1) {
                        throw "$($target.File) Detail!K79 changed the approved FG entry cycle"
                    }
                    if ([math]::Abs([double]$newbie.Range("K79").Value2 - [double]$entryWeight) -gt 1) {
                        throw "$($target.File) Detail_Newbie!K79 changed the approved FG entry cycle"
                    }
                }
            }
            if ([math]::Abs($normalRtp - [double]$target.Normal) -gt 0.000003) {
                throw "$($target.File) Normal RTP mismatch: $normalRtp"
            }
            if ([math]::Abs($bgRtp - [double]$target.BG) -gt 0.000003) {
                throw "$($target.File) BG RTP mismatch: $bgRtp"
            }
            if ([math]::Abs($fgRtp - [double]$target.FG) -gt 0.000003) {
                throw "$($target.File) FG RTP mismatch: $fgRtp"
            }
            if ([math]::Abs($newbieRtp - [double]$target.NewbieNormal) -gt 0.000003) {
                throw "$($target.File) Newbie RTP mismatch: $newbieRtp"
            }
            if ([math]::Abs($newbieBgRtp - [double]$target.NewbieBG) -gt 0.000003) {
                throw "$($target.File) Newbie BG RTP mismatch: $newbieBgRtp"
            }
            if ([math]::Abs($newbieFgRtp - [double]$target.NewbieFG) -gt 0.000003) {
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
                if ([math]::Abs($sum - 1000000000) -gt 1) { throw "$($target.File) $range weight sum is $sum" }
            }
            foreach ($range in @("K15:K78", "K86:K149")) {
                $sum = [double]$excel.WorksheetFunction.Sum($newbie.Range($range))
                if ($sum -ne 1000000000) { throw "$($target.File) Newbie $range weight sum is $sum" }
            }

            Test-RuleRows $detail 15 @($version.bg.audit) "BG"
            Test-RuleRows $detail 86 @($version.fg.audit) "FG"
            Test-RuleRows $detail 163 @($version.bf.audit) "BF"
            Test-RuleRows $detail 234 @($version.sf.audit) "SF"
            Test-RuleRows $newbie 15 @($version.newbie.bg.audit) "Newbie BG"
            Test-RuleRows $newbie 86 @($version.newbie.fg.audit) "Newbie FG"

            if ($null -ne $version.sf.profit_hit_rate) {
                $sfWeightTotal = [double]$excel.WorksheetFunction.Sum($detail.Range("K234:K297"))
                $minimumIndex = [int]$version.sf.minimum_weighted_index
                $minimumRow = 234 + $minimumIndex
                $belowMinimumWeight = if ($minimumRow -gt 234) {
                    [double]$excel.WorksheetFunction.Sum($detail.Range("K234:K$($minimumRow - 1)"))
                } else { 0.0 }
                $minimumWeight = [double]$detail.Cells.Item($minimumRow, 11).Value2
                $profitWeight = [double]$excel.WorksheetFunction.Sum($detail.Range("K264:K297"))
                $above500Weight = [double]$excel.WorksheetFunction.Sum($detail.Range("K269:K297"))
                $below100Weight = [double]$excel.WorksheetFunction.Sum($detail.Range("K253:K257"))
                $sfSceneRtp = [double]$excel.WorksheetFunction.Sum($detail.Range("M234:M297"))
                $maxRangeRtp = 0.0
                for ($row = 234; $row -le 297; $row++) {
                    $weight = [double]$detail.Cells.Item($row, 11).Value2
                    $naturalRate = [double]$detail.Cells.Item($row, 4).Value2
                    $rowRtp = [double]$detail.Cells.Item($row, 13).Value2
                    if ($weight -gt 0 -and $naturalRate -le 0.0007) {
                        throw "$($target.File) SF row $row has weight with natural probability at or below 0.07%"
                    }
                    if ($rowRtp -gt $maxRangeRtp) { $maxRangeRtp = $rowRtp }
                }
                if ($sfWeightTotal -ne 1000000000) { throw "$($target.File) SF weight total is $sfWeightTotal" }
                if ($belowMinimumWeight -ne 0 -or $minimumWeight -le 0) {
                    throw "$($target.File) SF minimum weighted range does not match payload index $minimumIndex"
                }
                if ([math]::Abs($profitWeight / $sfWeightTotal - [double]$version.sf.profit_hit_rate) -gt 0.000000001) {
                    throw "$($target.File) SF profit hit rate is $($profitWeight / $sfWeightTotal)"
                }
                if ($maxRangeRtp / $sfSceneRtp -gt 0.15000001) {
                    throw "$($target.File) SF single-range RTP share exceeds 15%"
                }
                $boostIndices = @($version.sf.boost_indices | ForEach-Object { [int]$_ })
                for ($row = $minimumRow; $row -lt 297; $row++) {
                    $currentHitWeight = [double]$detail.Cells.Item($row, 11).Value2
                    $nextHitWeight = [double]$detail.Cells.Item($row + 1, 11).Value2
                    $nextIndex = $row + 1 - 234
                    if ($currentHitWeight -lt $nextHitWeight -and $nextIndex -notin $boostIndices) {
                        throw "$($target.File) SF Hit Rate rises from row $row to $($row + 1)"
                    }
                }
            }

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

Write-Output "Applied H016 competitor-relative per-range RTP rules to target version $TargetVersion."
