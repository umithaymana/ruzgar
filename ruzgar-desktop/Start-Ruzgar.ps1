# Rüzgar — oturum açılışında: Ollama (yoksa atla) + API + Electron
# Konuşmak için uygulama içinde yalnızca mikrofon düğmesine basmanız yeterli.

$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Assistant = Join-Path $Repo "ilim-assistant"
$Desktop = $PSScriptRoot

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
