# setup_windows_task_user.ps1 - Register Task Scheduler at 00:00 daily using CURRENT USER.
#
# Does NOT need admin rights. Runs only when:
#   - Computer is powered on at 00:00
#   - User is logged in (or "Run whether user is logged in or not" if user opens
#     Task Scheduler GUI later and switches it; default here = only when logged in)
#
# For 24/7 reliability (even when no user logged in) use setup_windows_task.ps1
# (SYSTEM account, requires Run as Administrator).

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

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "[!] Task already exists - replacing"
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Register under current user - no admin needed
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -User $env:USERNAME `
        -Description "EpiWatch daily pipeline - chain sync, build_features, batch_predict at 00:00." `
        -ErrorAction Stop `
        | Out-Null
} catch {
    Write-Error "Register-ScheduledTask failed: $_"
    return
}

Write-Host ""
Write-Host "[OK] Task '$TaskName' registered under user '$env:USERNAME'" -ForegroundColor Green
Write-Host "     Schedule: Daily at 00:00 (local time)"
Write-Host "     Logs:     $LogsDir\daily_pipeline_YYYY-MM-DD.log"
Write-Host "     DB audit: pipeline_runs table"
Write-Host ""
Write-Host "Caveat: only runs when this user is logged in. If you log out at night,"
Write-Host "        the task will be missed (but will catch up next time you login due to -StartWhenAvailable)."
Write-Host ""
Write-Host "Manage:"
Write-Host "  Get-ScheduledTaskInfo -TaskName $TaskName"
Write-Host "  Start-ScheduledTask -TaskName $TaskName"
Write-Host "  .\scripts\setup_windows_task_user.ps1 -Remove"

if ($RunNow) {
    Write-Host ""
    Write-Host "Running task NOW for testing..."
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 3
    Get-ScheduledTaskInfo -TaskName $TaskName | Format-List TaskName, LastRunTime, LastTaskResult, NextRunTime
}
