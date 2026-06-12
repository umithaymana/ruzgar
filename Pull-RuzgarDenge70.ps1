# RÜZGAR — denge70 (llama3.1:70b) Ollama çekimi
# Ümit & Gökçenur
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$model = $env:RUZGAR_BRAIN_DENGE70_MODEL
if (-not $model) { $model = "llama3.1:70b" }

Write-Host "Ollama model cekiliyor: $model"
Write-Host "(RAM ~40GB+ gerekebilir; uzun surebilir.)"
ollama pull $model
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Tamam. Kontrol: ollama list"
ollama list | Select-String $model
