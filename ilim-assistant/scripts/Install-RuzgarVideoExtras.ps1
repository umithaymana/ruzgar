# Rüzgar — V7.2 SadTalker + V8 Runway .env yapılandırması
# Kullanım: powershell -ExecutionPolicy Bypass -File scripts/Install-RuzgarVideoExtras.ps1
# Not: Bu makinede NVIDIA GPU yoksa SadTalker CPU'da çok yavaş çalışır.

$ErrorActionPreference = "Stop"
$IaRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Tools = Join-Path $IaRoot "tools"
$SadRoot = Join-Path $Tools "SadTalker"
$Venv = Join-Path $Tools "sadtalker-venv"
$EnvFile = Join-Path $IaRoot ".env"
$Marker = "# --- Ruzgar Video V7.2 / V8 ---"

Write-Host "Ruzgar video ekleri kurulumu"
Write-Host "  IA root: $IaRoot"

New-Item -ItemType Directory -Force -Path $Tools | Out-Null

if (-not (Test-Path $SadRoot)) {
  Write-Host "SadTalker klonlaniyor..."
  git clone --depth 1 https://github.com/OpenTalker/SadTalker.git $SadRoot
} else {
  Write-Host "SadTalker zaten var: $SadRoot"
}

if (-not (Test-Path (Join-Path $SadRoot "inference.py"))) {
  throw "SadTalker inference.py bulunamadi."
}

$py = (Get-Command python -ErrorAction Stop).Path
if (-not (Test-Path (Join-Path $Venv "Scripts/python.exe"))) {
  Write-Host "Sanal ortam olusturuluyor: $Venv"
  & $py -m venv $Venv
}
$Vpy = Join-Path $Venv "Scripts/python.exe"

Write-Host "PyTorch (CPU) + SadTalker bagimliliklari (Python 3.12)..."
& $Vpy -m pip install --upgrade "pip<26" wheel "setuptools>=70,<82"
& $Vpy -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
$req312 = Join-Path $Tools "sadtalker-requirements-py312.txt"
if (-not (Test-Path $req312)) {
  throw "sadtalker-requirements-py312.txt bulunamadi."
}
& $Vpy -m pip install -r $req312

$ckpt = Join-Path $SadRoot "checkpoints"
New-Item -ItemType Directory -Force -Path $ckpt | Out-Null

$releaseBase = "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc"
$models = @(
  @{ Name = "SadTalker_V0.0.2_256.safetensors"; Url = "$releaseBase/SadTalker_V0.0.2_256.safetensors"; MinBytes = 700000000 },
  @{ Name = "mapping_00109-model.pth.tar"; Url = "$releaseBase/mapping_00109-model.pth.tar"; MinBytes = 150000000 },
  @{ Name = "mapping_00229-model.pth.tar"; Url = "$releaseBase/mapping_00229-model.pth.tar"; MinBytes = 150000000 }
)

foreach ($m in $models) {
  $dest = Join-Path $ckpt $m.Name
  $ok = (Test-Path $dest) -and ((Get-Item $dest).Length -ge $m.MinBytes)
  if ($ok) {
    Write-Host "Model tamam: $($m.Name)"
  }
}

$dlScript = Join-Path $IaRoot "scripts/download_sadtalker_models.py"
Write-Host "Model indirme (Python)..."
& $Vpy $dlScript $ckpt
if ($LASTEXITCODE -ne 0) { throw "Model indirme basarisiz." }

function Set-EnvLine {
  param([string]$Key, [string]$Value)
  if (-not (Test-Path $EnvFile)) {
    New-Item -ItemType File -Path $EnvFile -Force | Out-Null
  }
  $raw = Get-Content $EnvFile -Raw -ErrorAction SilentlyContinue
  if ($raw -match "(?m)^$([regex]::Escape($Key))=") {
    $new = [regex]::Replace($raw, "(?m)^$([regex]::Escape($Key))=.*", "$Key=$Value")
    Set-Content -Path $EnvFile -Value $new.TrimEnd() -Encoding UTF8
  } else {
    Add-Content -Path $EnvFile -Value "$Key=$Value" -Encoding UTF8
  }
}

if (-not (Test-Path $EnvFile) -or -not (Select-String -Path $EnvFile -Pattern ([regex]::Escape($Marker)) -Quiet)) {
  Add-Content -Path $EnvFile -Value "" -Encoding UTF8
  Add-Content -Path $EnvFile -Value $Marker -Encoding UTF8
}

Set-EnvLine -Key "RUZGAR_SADTALKER_ROOT" -Value ($SadRoot -replace "\\", "/")
Set-EnvLine -Key "RUZGAR_SADTALKER_PYTHON" -Value ($Vpy -replace "\\", "/")
Set-EnvLine -Key "RUZGAR_PORTRAIT_TIMEOUT" -Value "900"
Set-EnvLine -Key "RUZGAR_RUNWAY_MODEL" -Value "gen4_turbo"
Set-EnvLine -Key "RUZGAR_RUNWAY_API_BASE" -Value "https://api.dev.runwayml.com"
Set-EnvLine -Key "RUZGAR_RUNWAY_POLL_SEC" -Value "4"

if (-not (Select-String -Path $EnvFile -Pattern '^RUNWAY_API_KEY=' -Quiet)) {
  Add-Content -Path $EnvFile -Value '# RUNWAY_API_KEY=  # runway.com/developer - V8 icin doldur' -Encoding UTF8
}

Write-Host ""
Write-Host "Kurulum tamam."
Write-Host "  SadTalker: $SadRoot"
Write-Host "  Python:    $Vpy"
Write-Host "  .env guncellendi."
Write-Host ""
Write-Host "Runway V8 icin ilim-assistant/.env icinde RUNWAY_API_KEY= satirini doldur."
Write-Host "GPU yok - portre modu CPU modunda sahne basina cok uzun surebilir."
Write-Host "Ruzgar yeniden baslat: ruzgar-desktop/Start-Ruzgar.ps1"
