# setup_windows_task.ps1 - Register Windows Task Scheduler daily pipeline at 00:00.
#
# Job is independent of FastAPI - requires only Postgres + Python venv + .env.
# Run as Administrator to register a system-level task.
#
# Usage:
#   .\scripts\setup_windows_task.ps1            # register
#   .\scripts\setup_windows_task.ps1 -Remove    # uninstall
#   .\scripts\setup_windows_task.ps1 -RunNow    # run once now for testing

param(
    [switch]$Remove,
    [switch]$RunNow
)

$TaskName    = "EpiWatch-DailyPipeline"
$ProjectRoot = "F:\BAO_CAO\DO_AN_TOT_NGHIEP\KLTN"
$PythonExe   = "$ProjectRoot\.venv\Scripts\python.exe"
$Script      = "$ProjectRoot\scripts\run_daily_pipeline.py"
$LogsDir     = "$ProjectRoot\logs"

if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
    Write-Host "Created logs dir: $LogsDir"
}

if ($Remove) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "[OK] Task '$TaskName' removed"
    } else {
        Write-Host "[!] Task '$TaskName' not found"
    }
    return
}

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python venv not found: $PythonExe"
    return
}
if (-not (Test-Path $Script)) {
    Write-Error "Pipeline script not found: $Script"
    return
}

$LogFile = "$LogsDir\daily_pipeline_%date:~10,4%-%date:~4,2%-%date:~7,2%.log"
$ActionArg = "/c `"`"$PythonExe`" `"$Script`" >> `"$LogFile`" 2>&1`""

$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument $ActionArg `
    -WorkingDirectory $ProjectRoot

$trigger = New-ScheduledTaskTrigger -Daily -At "00:00"

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 10)

$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "[!] Task already exists - replacing"
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "EpiWatch - chain sync_flunet, sync_weather, build_features, batch_predict daily 00:00." `
    | Out-Null

Write-Host ""
Write-Host "[OK] Task '$TaskName' registered" -ForegroundColor Green
Write-Host "     Schedule: Daily at 00:00 (system local time)"
Write-Host "     Logs:     $LogsDir\daily_pipeline_YYYY-MM-DD.log"
Write-Host "     DB audit: SELECT * FROM pipeline_runs ORDER BY started_at DESC"
Write-Host ""
Write-Host "Manage:"
Write-Host "  Get-ScheduledTask -TaskName $TaskName"
Write-Host "  Get-ScheduledTaskInfo -TaskName $TaskName"
Write-Host "  Start-ScheduledTask -TaskName $TaskName"
Write-Host "  .\scripts\setup_windows_task.ps1 -Remove"

if ($RunNow) {
    Write-Host ""
    Write-Host "Running task NOW for testing..."
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 3
    Get-ScheduledTaskInfo -TaskName $TaskName | Format-List TaskName, LastRunTime, LastTaskResult, NextRunTime
}
