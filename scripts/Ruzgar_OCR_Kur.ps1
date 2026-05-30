# Ruzgar — Tesseract OCR (Arapca / Osmanlica script) yerel kurulum
param(
    [switch]$SkipWinget
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$TessUserDir = Join-Path $Root ".ruzgar\tessdata"
$Base = "https://raw.githubusercontent.com/tesseract-ocr/tessdata/main"
$Langs = @("ara", "tur", "eng", "osd")
$TessExeDir = "C:\Program Files\Tesseract-OCR"

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
        [System.Environment]::GetEnvironmentVariable("Path", "User")
}

Write-Host ""
Write-Host "=== RUZGAR OCR KURULUM ===" -ForegroundColor Cyan

if (-not (Test-Path $TessExeDir)) {
    if (-not $SkipWinget -and (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host "Tesseract yok, winget ile kuruluyor..." -ForegroundColor Yellow
        winget install --id UB-Mannheim.TesseractOCR -e --accept-source-agreements --accept-package-agreements
        Refresh-Path
    }
}

if (-not (Test-Path (Join-Path $TessExeDir "tesseract.exe"))) {
    Write-Host "HATA: Tesseract bulunamadi." -ForegroundColor Red
    exit 1
}

$env:Path = "$TessExeDir;" + $env:Path
New-Item -ItemType Directory -Force -Path $TessUserDir | Out-Null
Write-Host "tessdata: $TessUserDir"

foreach ($lang in $Langs) {
    $dest = Join-Path $TessUserDir "$lang.traineddata"
    if ((Test-Path $dest) -and ((Get-Item $dest).Length -gt 50000)) {
        Write-Host "  [OK] $lang zaten var"
        continue
    }
    $url = "$Base/$lang.traineddata"
    Write-Host "  Indiriliyor: $lang ..."
    Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
    Write-Host "  [OK] $lang indirildi"
}

[Environment]::SetEnvironmentVariable("TESSDATA_PREFIX", $TessUserDir, "User")
$env:TESSDATA_PREFIX = $TessUserDir

$tessVer = (& "$TessExeDir\tesseract.exe" --version 2>&1 | Select-Object -First 1)
Write-Host "Tesseract: $tessVer"
Write-Host ""
Write-Host "Dil listesi:" -ForegroundColor Green
& "$TessExeDir\tesseract.exe" --list-langs 2>&1 | Select-Object -Skip 1 | ForEach-Object { Write-Host "  $_" }

Write-Host ""
Write-Host "Tamam. Osmanlica metinler icin Arapca OCR (ara) kullanilir." -ForegroundColor Green
Write-Host "Ruzgar yeniden baslatildiktan sonra /api/health -> ocr.cloud_ready true olmali." -ForegroundColor DarkGray
Write-Host ""
