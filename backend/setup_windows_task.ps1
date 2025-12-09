# PowerShell script to create Windows Task Scheduler task for Flow State Collector
# Run this script as Administrator

# Configuration
$TaskName = "FlowStateCollector"
$TaskDescription = "Flow State Tax Monitor - Data Collector Orchestrator"
$ScriptPath = Join-Path $PSScriptRoot "data_collector_orchestrator.py"
$PythonPath = "python"  # Update this to your Python executable path if needed
$WorkingDirectory = $PSScriptRoot
$ConfigFile = "collector_config.json"

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "Task '$TaskName' already exists. Removing old task..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create action
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "data_collector_orchestrator.py --config $ConfigFile" `
    -WorkingDirectory $WorkingDirectory

# Create trigger (run at user logon)
$Trigger = New-ScheduledTaskTrigger -AtLogOn

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

# Create principal (run as current user)
$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

# Register the task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Description $TaskDescription `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal

Write-Host ""
Write-Host "Task '$TaskName' created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "The collector will start automatically when you log in."
Write-Host ""
Write-Host "To manage the task:"
Write-Host "  - View: Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "  - Start: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "  - Stop: Stop-ScheduledTask -TaskName '$TaskName'"
Write-Host "  - Remove: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
Write-Host ""
