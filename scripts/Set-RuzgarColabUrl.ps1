# Colab ngrok adresini ruzgar_remote_api.txt dosyasına yazar.
param(
    [Parameter(Mandatory = $true)]
    [string]$Url
)

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
if ((Split-Path -Leaf $Root) -eq "scripts") {
    $Root = Split-Path -Parent $Root
}
$line = ($Url.Trim() -replace "/+$", "")
$out = Join-Path $Root "ruzgar-desktop\ruzgar_remote_api.txt"
$body = @(
    "# Colab ngrok — Rüzgar API (PC'de yerel 8779 yerine bu adres kullanılır)"
    $line
) -join "`n"
Set-Content -Path $out -Value $body -Encoding UTF8
Write-Host "Yazildi: $out"
Write-Host "Simdi: .\Ruzgar.ps1"
