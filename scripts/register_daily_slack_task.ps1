$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$ScriptPath = Join-Path $ProjectRoot "scripts\send_slack_briefing.py"

$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory $ProjectRoot

$Trigger = New-ScheduledTaskTrigger -Daily -At 7:30AM
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask `
    -TaskName "Daily Briefing Slack" `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "매일 오전 7시 30분 Daily Briefing Agent 결과를 Slack으로 전송합니다." `
    -Force

Write-Host "Daily Briefing Slack 작업이 등록되었습니다."
