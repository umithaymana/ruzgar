# Startup'taki Ruzgar kisayolunu kaldir
$startup = [Environment]::GetFolderPath("Startup")
$lnkPath = Join-Path $startup "Ruzgar-Otomatik.lnk"
if (Test-Path $lnkPath) {
  Remove-Item $lnkPath -Force
  Write-Host "Kaldirildi: $lnkPath"
} else {
  Write-Host "Dosya yoktu: $lnkPath"
}
