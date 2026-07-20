<#
.SYNOPSIS
    Register (or refresh) the AI STACK scheduled refresh tasks.

.DESCRIPTION
    Replaces the copy-paste schtasks prose in how_to_update.md, whose paths
    were stale (C:\Users\imadq\...). Paths here are derived from this script's
    own location, so it cannot drift again.

    Two tasks, matching the documented cadences:

      AIInvest-Daily     06:00 daily   refresh_all.py --deploy --no-congress
      AIInvest-Congress  07:00 day 1   refresh_congress.py --deploy

    Why 06:00 publishes the PRIOR session's close: US markets close 16:00 ET
    = 22:00 Paris, so a 06:00 run is ~8h past close, well after settlement.

    Why the daily task passes --no-congress: PTR filings move monthly and
    re-downloading ~300 PDFs every night is not scraping politely
    (CLAUDE.md 8). The monthly task covers them.

    The daily run self-verifies all 14 bundles plus GF-value coverage and
    raises a Windows toast on failure, so an unattended failure still
    reaches you.

.PARAMETER Deploy
    Include --deploy so a successful nightly run publishes to Vercel prod.
    Off by default: auto-publishing should be a deliberate choice, and
    TERMINAL_KEY must be set first or the gated /terminal desks go public.

.PARAMETER Remove
    Unregister both tasks and exit.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\register_tasks.ps1
    powershell -ExecutionPolicy Bypass -File scripts\register_tasks.ps1 -Deploy
    powershell -ExecutionPolicy Bypass -File scripts\register_tasks.ps1 -Remove
#>
[CmdletBinding()]
param(
    [switch]$Deploy,
    [switch]$Remove
)

$ErrorActionPreference = 'Stop'

$ScriptsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot   = Split-Path -Parent $ScriptsDir

$DailyName    = 'AIInvest-Daily'
$CongressName = 'AIInvest-Congress'

function Remove-TaskIfPresent([string]$Name) {
    if (Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $Name -Confirm:$false
        Write-Output "  removed existing task: $Name"
    }
}

if ($Remove) {
    Remove-TaskIfPresent $DailyName
    Remove-TaskIfPresent $CongressName
    Write-Output 'Done. Both tasks unregistered.'
    exit 0
}

# Resolve the real interpreter. A bare "python" on Windows is often the
# Store stub, which exits without running anything -- a scheduled task built
# on it fails silently every night.
$Python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Python -or $Python -match 'WindowsApps') {
    $Candidate = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
    if (Test-Path $Candidate) {
        $Python = $Candidate
    } else {
        throw "No usable python.exe found (a WindowsApps stub does not count). Set it manually."
    }
}
Write-Output "python      : $Python"
Write-Output "scripts dir : $ScriptsDir"

& $Python -c "import sys; sys.exit(0)"
if ($LASTEXITCODE -ne 0) { throw "python at $Python is not runnable" }

$DailyArgs = 'refresh_all.py --no-congress'
if ($Deploy) { $DailyArgs += ' --deploy' }

Write-Output ''
Write-Output "daily cmd   : $Python $DailyArgs"
Write-Output "congress cmd: $Python refresh_congress.py"
Write-Output ''

# StartWhenAvailable: if the machine was asleep or off at 06:00, run at the
# next opportunity rather than skipping the day entirely.
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 4)

Remove-TaskIfPresent $DailyName
$DailyAction  = New-ScheduledTaskAction -Execute $Python -Argument $DailyArgs -WorkingDirectory $ScriptsDir
$DailyTrigger = New-ScheduledTaskTrigger -Daily -At 06:00
Register-ScheduledTask -TaskName $DailyName -Action $DailyAction -Trigger $DailyTrigger `
    -Settings $Settings -Description 'AI STACK: nightly EOD data refresh (prior session close), self-verifying.' | Out-Null
Write-Output "registered: $DailyName (daily 06:00)"

Remove-TaskIfPresent $CongressName
$CongressAction  = New-ScheduledTaskAction -Execute $Python -Argument 'refresh_congress.py --keep-going' -WorkingDirectory $ScriptsDir
$CongressTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 07:00
Register-ScheduledTask -TaskName $CongressName -Action $CongressAction -Trigger $CongressTrigger `
    -Settings $Settings -Description 'AI STACK: congress PTR refresh (filings move slowly).' | Out-Null
Write-Output "registered: $CongressName (Sundays 07:00)"

Write-Output ''
Write-Output 'Verify with : Get-ScheduledTask AIInvest-*'
Write-Output 'Run now with: Start-ScheduledTask -TaskName AIInvest-Daily'
if (-not $Deploy) {
    Write-Output ''
    Write-Output 'NOTE: --deploy was NOT enabled, so nightly runs refresh data locally'
    Write-Output '      without publishing. Re-run with -Deploy once TERMINAL_KEY is set'
    Write-Output '      in Vercel, or the gated /terminal desks publish openly.'
}
