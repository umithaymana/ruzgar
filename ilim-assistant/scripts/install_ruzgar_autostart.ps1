# Rüzgar — PC açılınca desktop_server (plan 11 §7.3)
# Yönetici PowerShell: .\install_ruzgar_autostart.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (-not (Test-Path (Join-Path $root "Ruzgar.ps1"))) {
  $root = "D:\ÜMİT\PROJELER\CURSOR PROJELER\YAPAY ZEKA"
}
$ps1 = Join-Path $root "Ruzgar.ps1"
$task = "RuzgarDesktopServer"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ps1`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
Register-ScheduledTask -TaskName $task -Action $action -Trigger $trigger -Principal $principal -Force | Out-Null
Write-Host "OK scheduled task: $task -> $ps1"
