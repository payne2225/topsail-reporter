# Install the specials check as a hidden scheduled task on the home PC.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File local\install_task.ps1 [-Times 11:15,16:15]
#
# Clones the repo into %LOCALAPPDATA%\topsail-reporter\repo (the job's own
# checkout; a live check resets it to GitHub's main), then registers
# "Topsail Reporter specials": daily at each time, the days the paper
# runs, through run-hidden.vbs so no window ever shows, and "Topsail
# Reporter hours check": fb_hours.py once at -HoursCheck, before the run
# starts. Re-running replaces both. Remove them with:
#   Unregister-ScheduledTask -TaskName "Topsail Reporter specials" -Confirm:$false
#   Unregister-ScheduledTask -TaskName "Topsail Reporter hours check" -Confirm:$false
param(
    [string[]]$Times = @("11:15", "16:15"),
    [string]$First = "2026-11-07",
    [string]$Last = "2026-11-14",
    [string]$HoursCheck = "2026-11-05 11:15"
)
$ErrorActionPreference = "Stop"
$State = Join-Path $env:LOCALAPPDATA "topsail-reporter"
$Repo = Join-Path $State "repo"
$Hidden = Join-Path $env:USERPROFILE "Projects\silent-launch\run-hidden.vbs"
# The interpreter itself, not the WindowsApps alias that launches it.
$Python = (& python -c "import sys; print(sys.executable)").Trim()
if (-not (Test-Path $Hidden)) { throw "run-hidden.vbs not found at $Hidden" }
if (-not (Test-Path (Join-Path $Repo ".git"))) {
    git clone -q https://github.com/payne2225/topsail-reporter.git $Repo
}
git -C $Repo pull -q --ff-only

$Script = Join-Path $Repo "local\fb_specials.py"
$Log = Join-Path $State "specials.log"
$Action = New-ScheduledTaskAction -Execute "wscript.exe" -WorkingDirectory $Repo `
    -Argument "//nologo //B `"$Hidden`" `"$Python`" `"$Script`" --log `"$Log`""
$Triggers = foreach ($t in $Times) {
    $trig = New-ScheduledTaskTrigger -Daily -At ([datetime]"$First $t")
    $trig.EndBoundary = ([datetime]"$Last 23:59").ToString("s")
    $trig
}
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) -MultipleInstances IgnoreNew
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive
Register-ScheduledTask -TaskName "Topsail Reporter specials" -Action $Action -Trigger $Triggers `
    -Settings $Settings -Principal $Principal -Force `
    -Description "Reads restaurant Facebook pages for the Topsail Reporter Island Edition's specials." | Out-Null

$Hours = Join-Path $Repo "local\fb_hours.py"
$HoursAction = New-ScheduledTaskAction -Execute "wscript.exe" -WorkingDirectory $Repo `
    -Argument "//nologo //B `"$Hidden`" `"$Python`" `"$Hours`" --log `"$Log`""
Register-ScheduledTask -TaskName "Topsail Reporter hours check" -Action $HoursAction `
    -Trigger (New-ScheduledTaskTrigger -Once -At ([datetime]$HoursCheck)) `
    -Settings $Settings -Principal $Principal -Force `
    -Description "Reads the favorite places' Facebook pages for closing or hours posts before the Topsail Reporter's run." | Out-Null
Get-ScheduledTask -TaskName "Topsail Reporter specials", "Topsail Reporter hours check" | Get-ScheduledTaskInfo |
    Select-Object TaskName, NextRunTime | Format-List
