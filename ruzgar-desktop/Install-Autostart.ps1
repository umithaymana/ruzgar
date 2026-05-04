# Windows oturum acilisinda Rüzgar'i baslat — bir kez calistirin (cift tik).
$ps1 = Join-Path $PSScriptRoot "Start-Ruzgar.ps1"
if (-not (Test-Path $ps1)) {
  Write-Error "Start-Ruzgar.ps1 bulunamadi: $ps1"
  exit 1
}
$startup = [Environment]::GetFolderPath("Startup")
$lnkPath = Join-Path $startup "Ruzgar-Otomatik.lnk"
$shell = New-Object -ComObject WScript.Shell
$sc = $shell.CreateShortcut($lnkPath)
$sc.TargetPath = "powershell.exe"
$sc.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ps1`""
$sc.WorkingDirectory = $PSScriptRoot
$sc.Description = "Ruzgar: Ollama + API + masaustu (otomatik)"
$sc.Save()
Write-Host "Tamam: $lnkPath"
Write-Host "Windows acildiginda Ruzgar arka planda baslayacak; yalnizca mikrofona basin."
