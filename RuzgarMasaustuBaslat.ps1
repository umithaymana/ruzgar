# RUZGAR — masaustu (Electron) + API 8779 (Faz 98)
$ErrorActionPreference = "Continue"
Add-Type -AssemblyName System.Windows.Forms -ErrorAction SilentlyContinue
$Root = $PSScriptRoot
$Ia = Join-Path $Root "ilim-assistant"
$Rd = Join-Path $Root "ruzgar-desktop"
$Log = Join-Path $env:TEMP "ruzgar-masaustu-launch.log"
$ExpectedRev = "2026-05-27-ruzgar-faz98-v107"
$Port = 8779

function Log([string]$m) {
    Add-Content -Path $Log -Value "$(Get-Date -Format o) $m" -Encoding UTF8
}

Log "=== Masaustu baslat ==="
$env:RUZGAR_EXPECTED_BUILD_REV = $ExpectedRev
$env:RUZGAR_API_MANAGED = "1"

# Eski Electron
Get-CimInstance Win32_Process -Filter "Name='electron.exe'" -EA SilentlyContinue |
    Where-Object { $_.CommandLine -match 'ruzgar-desktop' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue }

$ops = Join-Path $Ia "scripts\ruzgar_port_ops.py"
if (Test-Path $ops) {
    & py -3 $ops kill-all-api --port $Port 2>&1 | ForEach-Object { Log $_ }
    Start-Sleep -Seconds 2
}

function Test-HealthOk {
    try {
        $j = Invoke-RestMethod "http://127.0.0.1:$Port/api/health" -TimeoutSec 5
        return ($j.ok -and ([string]$j.build.rev -eq $ExpectedRev))
    } catch { return $false }
}

if (-not (Test-HealthOk)) {
    Log "API baslatiliyor..."
    Start-Process -FilePath "py" -ArgumentList @("-3", "run_desktop_api.py", "--host", "127.0.0.1", "--port", "$Port") `
        -WorkingDirectory $Ia -WindowStyle Hidden
    $ok = $false
    for ($i = 0; $i -lt 90; $i++) {
        if (Test-HealthOk) { $ok = $true; break }
        Start-Sleep -Milliseconds 500
    }
    if (-not $ok) {
        Log "HATA API hazir degil"
        [System.Windows.Forms.MessageBox]::Show(
            "API acilamadi (port $Port).`n`n1) Ruzgar_Port_Temizle.bat (yonetici)`n2) Tekrar masaustu kisayolu`n`nLog: $Log",
            "RUZGAR"
        ) | Out-Null
        exit 1
    }
}

@(
    "# UI -> yerel API"
    "http://127.0.0.1:$Port"
) | Set-Content -Path (Join-Path $Rd "ruzgar_remote_api.txt") -Encoding UTF8

$electron = Join-Path $Rd "node_modules\.bin\electron.cmd"
if (-not (Test-Path $electron)) {
    Log "npm install..."
    Push-Location $Rd
    & npm install --no-audit --no-fund 2>&1 | ForEach-Object { Log $_ }
    Pop-Location
}
if (-not (Test-Path $electron)) {
    [System.Windows.Forms.MessageBox]::Show("electron.cmd yok: $Rd", "RUZGAR") | Out-Null
    exit 1
}

Log "Electron aciliyor..."
Start-Process -FilePath $electron -ArgumentList @(".") -WorkingDirectory $Rd -WindowStyle Normal
Log "Bitti rev=$ExpectedRev"
