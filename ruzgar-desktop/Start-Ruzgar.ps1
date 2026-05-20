# Rüzgar — oturum açılışında: Ollama (yoksa atla) + API + Electron
# Konuşmak için uygulama içinde yalnızca mikrofon düğmesine basmanız yeterli.

$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Assistant = Join-Path $Repo "ilim-assistant"
$Desktop = $PSScriptRoot

function Import-RuzgarEnvFile {
  param([string]$IaRoot)
  $envPath = Join-Path $IaRoot ".env"
  if (-not (Test-Path $envPath)) { return $false }
  foreach ($raw in Get-Content $envPath -Encoding UTF8) {
    $line = $raw.Trim()
    if (-not $line -or $line.StartsWith("#") -or $line -notmatch "=") { continue }
    $key, $val = $line.Split("=", 2)
    $key = $key.Trim()
    $val = $val.Trim().Trim('"').Trim("'")
    if (-not $key -or -not $val) { continue }
    if ($key -in @("GLOBAL_API_KEY", "GOOGLE_GEMINI_API_KEY", "GEMINI_API_KEY", "RUZGAR_GEMINI_API_KEY")) {
      $env:GLOBAL_API_KEY = $val
      $env:GOOGLE_GEMINI_API_KEY = $val
      continue
    }
    if (-not (Get-Item -Path "Env:$key" -ErrorAction SilentlyContinue)) {
      Set-Item -Path "Env:$key" -Value $val
    }
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

# Ollama zaten dinliyorsa tekrar başlatma
if (-not (Test-PortListen 11434)) {
  if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 4
  }
}

# Kalıcı Gemini anahtarı — oturumda tekrar sorulmaz
$null = Import-RuzgarEnvFile -IaRoot $Assistant
if ($env:GLOBAL_API_KEY) {
  if (-not $env:RUZGAR_GEMINI_MODEL) { $env:RUZGAR_GEMINI_MODEL = "gemini-2.0-flash" }
}

# API (8777) zaten varsa atla
if (-not (Test-PortListen 8777)) {
  if (-not (Test-Path (Join-Path $Assistant "desktop_server.py"))) {
    throw "Bulunamadi: ilim-assistant\desktop_server.py — `$Repo=$Repo"
  }
  Start-Process -FilePath "py" -ArgumentList @("-3", "desktop_server.py") `
    -WorkingDirectory $Assistant -WindowStyle Hidden
  $deadline = (Get-Date).AddSeconds(45)
  while (-not (Test-PortListen 8777) -and (Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 400
  }
}

# Electron — zaten Rüzgar penceresi varsa ikinci kez acma
$ruzgarWin = Get-Process -Name "electron" -ErrorAction SilentlyContinue |
  Where-Object { $_.MainWindowTitle -match "Rüzgar|RUZGAR" }
if (-not $ruzgarWin) {
  Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm start" -WorkingDirectory $Desktop
}
