# Runs every gate for the web redesign in one pass and writes one report.
#
# Sequential on purpose: two npm/pnpm processes on Windows fight over the same
# pnpm store and produce failures that have nothing to do with the code.
#
# Usage:  powershell -NoProfile -ExecutionPolicy Bypass -File run-gates.ps1
# Report: gate-report.txt  (next to this script)
$ErrorActionPreference = 'Continue'
$web = Join-Path $PSScriptRoot 'apps\web'
$report = Join-Path $PSScriptRoot 'gate-report.txt'
Set-Content -LiteralPath $report -Value "TreeQ web gates - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -Encoding utf8

function Invoke-Gate {
    param([string]$Name, [string]$Exe, [string[]]$GateArgs)

    Write-Host ''
    Write-Host "=== $Name ===" -ForegroundColor Cyan
    Add-Content -LiteralPath $report -Value "`n=========== $Name ===========" -Encoding utf8

    Push-Location $web
    # -FilePath, not -LiteralPath: PowerShell 5.1's Tee-Object cannot resolve
    # -LiteralPath together with -Append, and the parameter-binding error left
    # every gate reporting FAIL without npx ever being called.
    # Out-Host is load-bearing. Tee-Object passes its input down the pipeline, and
    # anything left on a function's success stream becomes part of what the
    # function returns - so without it `$results[gate]` held the whole build log
    # with the exit code tacked on the end, and every summary line read FAIL while
    # the gate itself had printed PASS. Out-Host writes to the console and emits
    # nothing, leaving `return $code` as the only output.
    & $Exe @GateArgs 2>&1 | Tee-Object -FilePath $report -Append | Out-Host
    $code = $LASTEXITCODE
    Pop-Location

    Add-Content -LiteralPath $report -Value "exitcode=$code" -Encoding utf8
    # `else` stays on the closing brace's line: a single-line if block ends the
    # statement at the newline, so an `else` on its own line is a parse error and
    # takes the whole function definition down with it. That is exactly what
    # happened on this script's first run - no gate ran at all.
    if ($code -eq 0) { Write-Host "PASS $Name" -ForegroundColor Green } else { Write-Host "FAIL $Name (code $code)" -ForegroundColor Red }
    return $code
}

$results = [ordered]@{}
$results['tests'] = Invoke-Gate 'Unit tests' 'npx' @('vitest', 'run')
$results['type-check'] = Invoke-Gate 'Type-check' 'npx' @('tsc', '--noEmit')
$results['lint'] = Invoke-Gate 'Lint' 'npx' @('next', 'lint', '--max-warnings=0')

# Prettier is deliberately NOT run here. As a `--write` step it reformatted every
# file under src/ and buried nine intentional edits in forty files of whitespace
# churn; as a `--check` step it would fail on files nobody in this change touched,
# since the repo has never been formatted end to end and does not wire prettier
# into eslint. Format the files you edited, by name, before committing:
#
#   npx prettier --write <the files you changed>
$results['build'] = Invoke-Gate 'Build' 'npx' @('next', 'build')

# Last, and after the build on purpose: the journey gates serve the production
# output on 127.0.0.1:3100, and the frozen route verifies artifact hashes over
# HTTP, so running them against a stale build would check the wrong bytes.
$results['journey'] = Invoke-Gate 'Judge journey (browser)' 'npx' @('playwright', 'test')

Write-Host ''
Write-Host '=============== SUMMARY ===============' -ForegroundColor Yellow
Add-Content -LiteralPath $report -Value "`n=============== SUMMARY ===============" -Encoding utf8
foreach ($key in $results.Keys) {
    $verdict = if ($results[$key] -eq 0) { 'PASS' } else { "FAIL (code $($results[$key]))" }
    $line = '{0,-12} {1}' -f $key, $verdict
    Write-Host "  $line"
    Add-Content -LiteralPath $report -Value "  $line" -Encoding utf8
}

# Forbidden-claim scan from the plan's freeze gate. Reported, not enforced.
#
# Test files are excluded: a test asserting not.toContain('93.135') is the
# guard against the claim, not the claim. Including them made the first run
# report two hits that were both proof the guard exists.
Write-Host ''
Write-Host '=== forbidden claims (source only) ===' -ForegroundColor Cyan
Add-Content -LiteralPath $report -Value "`n=========== forbidden claims (source only) ===========" -Encoding utf8
$pattern = '93\.135|25,400\.58|จำนวนต้นไม้|certified carbon credit|รองรับ \.las|รองรับ \.laz'
Push-Location $web
$hits = Get-ChildItem -Path 'src' -Recurse -Include *.ts, *.tsx |
    Where-Object { $_.Name -notmatch '\.test\.tsx?$' } |
    Select-String -Pattern $pattern -ErrorAction SilentlyContinue |
    ForEach-Object { "$($_.Path):$($_.LineNumber): $($_.Line.Trim())" }
Pop-Location
if ($hits) {
    $hits | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    Add-Content -LiteralPath $report -Value $hits -Encoding utf8
} else {
    Write-Host '  none' -ForegroundColor Green
    Add-Content -LiteralPath $report -Value '  none' -Encoding utf8
}

$failed = @($results.Values | Where-Object { $_ -ne 0 }).Count
Write-Host ''
Write-Host "Report written to $report"
if ($failed -gt 0) { Write-Host "$failed gate(s) failed." -ForegroundColor Red } else { Write-Host 'All gates passed.' -ForegroundColor Green }
