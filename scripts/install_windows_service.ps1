[CmdletBinding()]
param(
    [string]$TaskName = "MOJO-AGENT-Backend",
    [int]$Port = 8766
)
$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = (Get-Command python -ErrorAction Stop).Source
}
if ($Port -lt 1024 -or $Port -gt 65535) { throw "Port must be between 1024 and 65535." }
$Action = New-ScheduledTaskAction -Execute $Python -Argument "-m uvicorn mojo_agent.api:app --host 127.0.0.1 --port $Port" -WorkingDirectory $ProjectRoot
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)
$Principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "MOJO AGENT local-first backend (loopback only)" -Force | Out-Null
Write-Host "Installed scheduled task: $TaskName"
Write-Host "Backend starts at user logon on http://127.0.0.1:$Port"
Write-Host "Start it now with: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "No administrator privileges or Docker are required."
