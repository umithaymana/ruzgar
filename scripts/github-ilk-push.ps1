# RÜZGAR — Yerel Git ilk commit ve GitHub'a gönderme
#
# Önce GitHub.com'da yeni BOŞ bir depo oluşturun (README eklemeden).
#
# Çalıştırma (proje kökünden):
#   .\scripts\github-ilk-push.ps1 -GitHubLogin "github_kullanici_adiniz" -Email "hesabiniz@gmail.com"
#
# Opsiyonel: doğrudan it
#   .\scripts\github-ilk-push.ps1 -GitHubLogin "xxx" -Email "y@mail" -RepoUrl "https://github.com/xxx/ruzgar.git"
#
# RepoUrl vermezseniz sadece commit yapılır; sonra manual:
#   git remote add origin https://github.com/KULLANICI/DEPORA.git
#   git push -u origin main

param(
    [Parameter(Mandatory = $true)]
    [string] $GitHubLogin,

    [Parameter(Mandatory = $true)]
    [string] $Email,

    [string] $RepoUrl = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

git config user.name $GitHubLogin
git config user.email $Email

$nullCommit = $false
git rev-parse HEAD 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { $nullCommit = $true }

if ($nullCommit) {
    git add .
    git commit -m "İlk commit: RÜZGAR (ilim-assistant, ruzgar-desktop)"
    Write-Host "[OK] İlk commit oluşturuldu."
} else {
    Write-Host "Zaten bir commit var; atlama yapılmadı. Yeni kayıt için: git add / git commit"
}

if ($RepoUrl) {
    git remote remove origin 2>$null
    git remote add origin $RepoUrl
    git branch -M main
    git push -u origin main
    Write-Host "[OK] origin eklendi ve push denendi."
} else {
    Write-Host ""
    Write-Host "Sıradaki adım GitHub:"
    Write-Host "  git remote add origin https://github.com/$GitHubLogin/YENI_REPO_ADINIZ.git"
    Write-Host "  git branch -M main"
    Write-Host "  git push -u origin main"
}
