# Rüzgar — oturum açılışında: Ollama + API (8779) + Electron
# Eski API süreci varsa build.rev uyumsuzluğunda yeniden başlatır.

$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Assistant = Join-Path $Repo "ilim-assistant"
$Desktop = $PSScriptRoot
$ApiPort = 8779
$ExpectedBuildRev = "2026-05-20-programlama-faz6-v17"
if ($env:RUZGAR_API_PORT) { [int]$ApiPort = $env:RUZGAR_API_PORT }

function Set-RuzgarGeminiKeyFromValue {
  param([string]$Val)
  if ($Val) {
    $env:GLOBAL_API_KEY = $Val
    $env:GOOGLE_GEMINI_API_KEY = $Val
    $env:GEMINI_API_KEY = $Val
    $env:RUZGAR_GEMINI_API_KEY = $Val
  }
}

function Import-RuzgarDotEnvFile {
  param([string]$Path)
  if (-not (Test-Path $Path)) { return }
  foreach ($raw in Get-Content $Path -Encoding UTF8) {
    $line = $raw.Trim()
    if (-not $line -or $line.StartsWith("#") -or $line -notmatch "=") { continue }
    $key, $val = $line.Split("=", 2)
    $key = $key.Trim()
    $val = $val.Trim().Trim('"').Trim("'")
    if (-not $key) { continue }
    if ($key -eq "RUZGAR_API_PORT" -and $val -match "^\d+$") {
      $script:ApiPort = [int]$val
    }
    if ($key -in @("GLOBAL_API_KEY", "GOOGLE_GEMINI_API_KEY", "GEMINI_API_KEY", "RUZGAR_GEMINI_API_KEY")) {
      if ($val) { Set-RuzgarGeminiKeyFromValue -Val $val }
      continue
    }
    if ($key -eq "GROQ_API_KEY") {
      if ($val) { $env:GROQ_API_KEY = $val }
      continue
    }
    if ($key -match '^(RUZGAR_|OLLAMA_|GROQ_|GLOBAL_|GOOGLE_GEMINI_|GEMINI_)') {
      if ($val) { Set-Item -Path "Env:$key" -Value $val -Force }
    } elseif (-not (Get-Item -Path "Env:$key" -ErrorAction SilentlyContinue)) {
      if ($val) { Set-Item -Path "Env:$key" -Value $val }
    }
  }
}

function Import-RuzgarEnvFile {
  param([string]$IaRoot)
  $envPath = Join-Path $IaRoot ".env"
  if (-not (Test-Path $envPath)) { return $false }
  Import-RuzgarDotEnvFile -Path $envPath
  Import-RuzgarDotEnvFile -Path (Join-Path $IaRoot "RUZGAR_BRAIN.env")
  $geminiTxt = Join-Path $Repo "ruzgar-desktop\google_api_key.txt"
  if ((-not $env:GLOBAL_API_KEY) -and (Test-Path $geminiTxt)) {
    foreach ($raw in Get-Content $geminiTxt -Encoding UTF8) {
      $val = $raw.Trim()
      if ($val -and -not $val.StartsWith("#")) {
        Set-RuzgarGeminiKeyFromValue -Val $val
        break
      }
    }
  }
  if ($env:RUZGAR_OLLAMA_ONLY -eq "1" -or $env:RUZGAR_DISABLE_GEMINI -eq "1") {
    Remove-Item Env:GLOBAL_API_KEY, Env:GOOGLE_GEMINI_API_KEY, Env:GEMINI_API_KEY, Env:RUZGAR_GEMINI_API_KEY, Env:GROQ_API_KEY -ErrorAction SilentlyContinue
    $env:RUZGAR_GEMINI_DAEMON = "0"
  }
  if ($env:RUZGAR_DISABLE_GROQ -eq "1" -or $env:RUZGAR_OLLAMA_ONLY -eq "1") {
    Remove-Item Env:GROQ_API_KEY -ErrorAction SilentlyContinue
  }
  return [bool]($env:GLOBAL_API_KEY -and $env:GLOBAL_API_KEY.Trim())
}

function Test-PortListen {
  param([int]$Port)
  try {
    $l = New-Object System.Net.Sockets.TcpListener([Net.IPAddress]::Loopback, $Port)
    $l.Start()
    $l.Stop()
    return $false
  } catch {
    return $true
  }
}

function Stop-ApiPort {
  param([int]$Port)
  try {
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
      ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
  } catch {}
  Start-Sleep -Seconds 1
}

function Test-ApiHealthCurrent {
  param([int]$Port)
  try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/health" -UseBasicParsing -TimeoutSec 4
    if ($r.StatusCode -ne 200) { return $false }
    $j = $r.Content | ConvertFrom-Json
    if ([string]$j.build.rev -ne $ExpectedBuildRev) { return $false }
    if ($env:RUZGAR_OLLAMA_ONLY -eq "1" -and $j.super_brain.gemini_configured -eq $true) { return $false }
    if ($env:RUZGAR_OLLAMA_ONLY -eq "1" -and $j.ruzgar_mode.ollama_only -ne $true) { return $false }
    return [bool]$j.ok
  } catch {
    return $false
  }
}

function Write-RuzgarRemoteApiTxt {
  param([int]$Port)
  Set-Content -Path (Join-Path $Desktop "ruzgar_remote_api.txt") -Value @(
    "# UI -> yerel API (Start-Ruzgar.ps1)"
    "http://127.0.0.1:$Port"
  ) -Encoding UTF8
}

function Start-ApiOnPort {
  param([int]$Port)
  $env:RUZGAR_API_PORT = "$Port"
  $py = $null
  try { $py = (Get-Command py -ErrorAction Stop).Path } catch {}
  if (-not $py) { $py = (Get-Command python -ErrorAction Stop).Path }
  $args = @("-3", "run_desktop_api.py")
  if ($py -match "python\.exe$") { $args = @("run_desktop_api.py") }
  Start-Process -FilePath $py -ArgumentList $args -WorkingDirectory $Assistant -WindowStyle Hidden
  $deadline = (Get-Date).AddSeconds(90)
  while ((Get-Date) -lt $deadline) {
    if (Test-ApiHealthCurrent -Port $Port) { return }
    Start-Sleep -Milliseconds 500
  }
  throw "API $Port guncel build ile acilmadi (rev $ExpectedBuildRev bekleniyor)."
}

if (-not (Test-PortListen 11434)) {
  if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 4
  }
}

$null = Import-RuzgarEnvFile -IaRoot $Assistant
Write-RuzgarRemoteApiTxt -Port $ApiPort

if (-not (Test-ApiHealthCurrent -Port $ApiPort)) {
  Stop-ApiPort -Port $ApiPort
  Start-ApiOnPort -Port $ApiPort
}

$ruzgarWin = Get-Process -Name "electron" -ErrorAction SilentlyContinue |
  Where-Object { $_.MainWindowTitle -match "Rüzgar|RUZGAR" }
if (-not $ruzgarWin) {
  Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm start" -WorkingDirectory $Desktop
}
