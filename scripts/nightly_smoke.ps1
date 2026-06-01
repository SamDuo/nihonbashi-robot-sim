<#
.SYNOPSIS
    Nightly Stage One smoke test for the Nihonbashi testbed.

.DESCRIPTION
    Runs the testbed end-to-end, captures pytest results, writes a dated
    report under outputs/nightly/. Does NOT commit or push - user controls
    that. Safe to schedule via Windows Task Scheduler.

.NOTES
    Register with Task Scheduler:
        schtasks /Create /TN "NihonbashiNightlySmoke" /TR "powershell -NoProfile -File C:\Temp\git-work\nihonbashi-robot-sim\scripts\nightly_smoke.ps1" /SC DAILY /ST 19:00 /F

    Unregister:
        schtasks /Delete /TN "NihonbashiNightlySmoke" /F

    Run once interactively:
        powershell -NoProfile -File scripts\nightly_smoke.ps1

.OUTPUTS
    outputs/nightly/<YYYY-MM-DD>.md  human-readable report
    outputs/nightly/<YYYY-MM-DD>.log full stdout+stderr
#>

[CmdletBinding()]
param(
    [string]$RepoRoot = "C:\Temp\git-work\nihonbashi-robot-sim",
    [string]$PythonExe = "py",
    [string]$Branch = "phase4-6-nvidia-plan"
)

$ErrorActionPreference = "Continue"
$stamp = Get-Date -Format "yyyy-MM-dd"
$started = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$nightlyDir = Join-Path $RepoRoot "outputs\nightly"
New-Item -ItemType Directory -Force -Path $nightlyDir | Out-Null

$reportPath = Join-Path $nightlyDir "$stamp.md"
$logPath = Join-Path $nightlyDir "$stamp.log"

function Write-Section {
    param([string]$Title, [string]$Body)
    Add-Content -Path $reportPath -Value "`n## $Title`n"
    Add-Content -Path $reportPath -Value $Body
}

# Header
Set-Content -Path $reportPath -Value @"
# Nihonbashi Nightly Smoke Test

| | |
|---|---|
| Date | $stamp |
| Started | $started |
| Branch | $Branch |
| Repo | $RepoRoot |
"@

Set-Location $RepoRoot

# 1. Branch + dirty-state check
$branchNow = git rev-parse --abbrev-ref HEAD 2>&1
$dirtyCount = (git status --porcelain 2>&1 | Measure-Object -Line).Lines
$lastCommit = git log -1 --pretty=format:"%h %s (%ar)" 2>&1
Write-Section "Repo state" @"
- Current branch: ``$branchNow``
- Uncommitted changes: $dirtyCount file(s)
- Last commit: ``$lastCommit``
"@

# 2. Smoke: run pytest if tests exist
$testDir = Join-Path $RepoRoot "tests"
$pytestResult = "no tests/ directory - skipped"
$pytestExit = 0
if (Test-Path $testDir) {
    $pytestOutput = & $PythonExe -m pytest tests -q 2>&1 | Out-String
    $pytestExit = $LASTEXITCODE
    Add-Content -Path $logPath -Value "=== pytest ===`n$pytestOutput"
    $pytestResult = if ($pytestExit -eq 0) { "PASS" } else { "FAIL (exit $pytestExit)" }
}
Write-Section "Tests" @"
- Result: **$pytestResult**
- See: ``outputs/nightly/$stamp.log``
"@

# 3. Smoke: run the testbed end-to-end (writes outputs/ artifacts)
$runScript = Join-Path $RepoRoot "scripts\run_testbed.py"
$runResult = "run_testbed.py not found - skipped"
$runExit = 0
$runDurationSec = 0
if (Test-Path $runScript) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $runOutput = & $PythonExe $runScript 2>&1 | Out-String
    $sw.Stop()
    $runDurationSec = [math]::Round($sw.Elapsed.TotalSeconds, 1)
    $runExit = $LASTEXITCODE
    Add-Content -Path $logPath -Value "`n=== run_testbed.py ===`n$runOutput"
    $runResult = if ($runExit -eq 0) { "PASS (${runDurationSec}s)" } else { "FAIL (exit $runExit, ${runDurationSec}s)" }
}
Write-Section "Testbed run" @"
- Result: **$runResult**
- See: ``outputs/nightly/$stamp.log``
"@

# 4. Output artifacts present?
$artifacts = @(
    "outputs/timeseries/metrics.csv",
    "outputs/timeseries/agents.csv",
    "outputs/timeseries/population.csv",
    "outputs/reports/testbed_comparison.md",
    "outputs/reports/provenance.jsonl"
)
$artifactLines = foreach ($a in $artifacts) {
    $p = Join-Path $RepoRoot $a
    if (Test-Path $p) {
        $size = (Get-Item $p).Length
        "- [x] ``$a`` ({0:N0} bytes)" -f $size
    } else {
        "- [ ] ``$a`` MISSING"
    }
}
Write-Section "Artifacts" ($artifactLines -join "`n")

# 5. Summary line at the top for at-a-glance
$overall = if ($pytestExit -eq 0 -and $runExit -eq 0) { "ALL PASS" } else { "FAILURE" }
$summary = "| Summary | **$overall** \| pytest: $pytestResult \| testbed: $runResult |"
$header = Get-Content $reportPath -Raw
$header = $header -replace '(\| Repo \| .*? \|)', "`$1`n$summary"
Set-Content -Path $reportPath -Value $header

$finished = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $reportPath -Value "`n---`n_Finished: $finished_"

if ($pytestExit -ne 0 -or $runExit -ne 0) {
    exit 1
}
exit 0
