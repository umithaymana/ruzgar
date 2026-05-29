# RUZGAR — tarayici acilis (masaustu kisayolu)
# API 8779 + http://127.0.0.1:8779/ui/index.html?clearApi=1
$ErrorActionPreference = "Continue"
$Root = $PSScriptRoot
$Ia = Join-Path $Root "ilim-assistant"
$Log = Join-Path $env:TEMP "ruzgar-tarayici-launch.log"
$ExpectedRev = "2026-05-27-ruzgar-faz98-v107"
$Port = 8779
$UiUrl = "http://127.0.0.1:$Port/ui/index.html?clearApi=1&_=$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())"

function Log([string]$m) {
    $line = "$(Get-Date -Format o) $m"
    Add-Content -Path $Log -Value $line -Encoding UTF8
}

Log "Basladi Root=$Root"

$env:RUZGAR_EXPECTED_BUILD_REV = $ExpectedRev
$ops = Join-Path $Ia "scripts\ruzgar_port_ops.py"
$py = "py"
$pyArgs = @("-3")

function Test-HealthOk {
    try {
        $j = Invoke-RestMethod "http://127.0.0.1:$Port/api/health" -TimeoutSec 4
        if (-not $j.ok) { return $false }
        $rev = [string]$j.build.rev
        return $rev -eq $ExpectedRev
    } catch {
        return $false
    }
}

function Stop-OldApi {
    if (-not (Test-Path $ops)) { return }
    & $py @($pyArgs + $ops) kill-all-api --port $Port 2>&1 | ForEach-Object { Log $_ }
    Start-Sleep -Seconds 2
    if (Test-HealthOk) {
        Log "Mevcut API zaten guncel rev=$ExpectedRev"
        return
    }
    try {
        Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
            ForEach-Object {
                Log "taskkill PID $($_.OwningProcess)"
                & taskkill /F /T /PID $_.OwningProcess 2>$null | Out-Null
            }
    } catch {}
    Start-Sleep -Seconds 1
}

function Start-ApiIfNeeded {
    if (Test-HealthOk) { return }
    $run = Join-Path $Ia "run_desktop_api.py"
    if (-not (Test-Path $run)) {
        Log "HATA run_desktop_api.py yok"
        return
    }
    Log "API baslatiliyor port=$Port"
    Start-Process -FilePath $py -ArgumentList @("-3", "run_desktop_api.py", "--host", "127.0.0.1", "--port", "$Port") `
        -WorkingDirectory $Ia -WindowStyle Hidden
    for ($i = 0; $i -lt 60; $i++) {
        if (Test-HealthOk) {
            Log "API hazir"
            return
        }
        Start-Sleep -Milliseconds 500
    }
    Log "UYARI API zaman asimi"
}

Stop-OldApi
Start-ApiIfNeeded

$remote = Join-Path $Root "ruzgar-desktop\ruzgar_remote_api.txt"
if (Test-Path (Split-Path $remote -Parent)) {
    @(
        "# UI -> yerel API (kisayol yazar)"
        "http://127.0.0.1:$Port"
    ) | Set-Content -Path $remote -Encoding UTF8
}

Log "Tarayici: $UiUrl"
Start-Process $UiUrl
Log "Bitti"
