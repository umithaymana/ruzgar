# RUZGAR — masaustu (Electron) + API 8779 (Faz 98)

$ErrorActionPreference = "Continue"

Add-Type -AssemblyName System.Windows.Forms -ErrorAction SilentlyContinue

$Root = $PSScriptRoot

$Ia = Join-Path $Root "ilim-assistant"

$Rd = Join-Path $Root "ruzgar-desktop"

$Log = Join-Path $env:TEMP "ruzgar-masaustu-launch.log"

$ApiErr = Join-Path $env:TEMP "ruzgar-api.err"

$ExpectedRev = "2026-06-14-ruzgar-sohbet-aq-faz-aq"

$Port = 8779



function Log([string]$m) {

    Add-Content -Path $Log -Value "$(Get-Date -Format o) $m" -Encoding UTF8

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

        if ($key -match '^(RUZGAR_|OLLAMA_|GROQ_|GLOBAL_|GOOGLE_GEMINI_|GEMINI_)') {

            if ($val) { Set-Item -Path "Env:$key" -Value $val -Force }

        }

    }

}



Log "=== Masaustu baslat ==="

$TessData = Join-Path $Root ".ruzgar\tessdata"

if (Test-Path $TessData) {

    $env:TESSDATA_PREFIX = $TessData

    Log "TESSDATA_PREFIX=$TessData"

}

$TessExe = "C:\Program Files\Tesseract-OCR"

if (Test-Path (Join-Path $TessExe "tesseract.exe")) {

    $env:Path = "$TessExe;" + $env:Path

}

Import-RuzgarDotEnvFile -Path (Join-Path $Ia ".env")

Import-RuzgarDotEnvFile -Path (Join-Path $Ia "RUZGAR_BRAIN.env")

$env:RUZGAR_EXPECTED_BUILD_REV = $ExpectedRev

$env:RUZGAR_API_MANAGED = "1"

$env:RUZGAR_SKIP_RAG_WARMUP = "1"

$env:RUZGAR_CORS_PERMISSIVE = "1"



function Test-HealthOk {

    try {

        $j = Invoke-RestMethod "http://127.0.0.1:$Port/api/health" -TimeoutSec 15

        return [bool]$j.ok

    } catch { return $false }

}



function Test-PortFree {

    try {

        $l = New-Object System.Net.Sockets.TcpListener([Net.IPAddress]::Loopback, $Port)

        $l.Start()

        $l.Stop()

        return $true

    } catch { return $false }

}



$ops = Join-Path $Ia "scripts\ruzgar_port_ops.py"

# Temiz baslat: API her zaman taze baslatilir (yalnizca Electron yenilemek eski Python'u birakir)
if (Test-Path $ops) {

    Log "Eski API surecleri durduruluyor (port $Port)"

    & py -3 $ops kill-all-api --port $Port 2>&1 | ForEach-Object { Log $_ }

    Start-Sleep -Seconds 2

    if (-not (Test-PortFree)) {

        Log "UYARI port $Port hala dolu - Ruzgar_Port_Temizle.bat (yonetici) gerekebilir"

    }

}

if (-not (Test-PortFree)) {

    Log "HATA port $Port bosaltılamadi (zombi surec)"

    $msg = @"

Port $Port hala kilitli — yeni API baslatilamaz.



1) Ruzgar_Port_Temizle.bat dosyasina sag tik → Yonetici olarak calistir

2) Sonra Ruzgar_TemizBaslat.bat tekrar deneyin



Log: $Log

"@

    [System.Windows.Forms.MessageBox]::Show($msg, "RUZGAR") | Out-Null

    exit 1

}

Remove-Item $ApiErr -ErrorAction SilentlyContinue

Log "API baslatiliyor..."

Start-Process -FilePath "py" -ArgumentList @("-3", "run_desktop_api.py", "--host", "127.0.0.1", "--port", "$Port") -WorkingDirectory $Ia -WindowStyle Hidden -RedirectStandardError $ApiErr

$ok = $false

for ($i = 0; $i -lt 180; $i++) {

    if (Test-HealthOk) { $ok = $true; break }

    Start-Sleep -Milliseconds 500

}

if (-not $ok) {

    Log "HATA API hazir degil"

    $errTail = ""
    if (Test-Path $ApiErr) {
        $errTail = (Get-Content $ApiErr -Tail 8 -ErrorAction SilentlyContinue) -join "`n"
        Get-Content $ApiErr -Tail 12 -ErrorAction SilentlyContinue | ForEach-Object { Log "api-err: $_" }
    }

    $msg = @"
API acilamadi (port $Port).

1) Ruzgar_Port_Temizle.bat (yonetici)
2) Ruzgar_TemizBaslat.bat tekrar

Log: $Log
API hata: $ApiErr
$(if ($errTail) { "`nSon hata:`n$errTail" })
"@

    [System.Windows.Forms.MessageBox]::Show($msg, "RUZGAR") | Out-Null

    exit 1

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



Get-CimInstance Win32_Process -Filter "Name='electron.exe'" -EA SilentlyContinue |
    Where-Object { $_.CommandLine -match 'ruzgar-desktop' } |
    ForEach-Object {
        Log "Electron kapatiliyor pid=$($_.ProcessId)"
        Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue
    }
Start-Sleep -Seconds 1

Log "Electron aciliyor..."
Start-Process -FilePath $electron -ArgumentList @(".") -WorkingDirectory $Rd -WindowStyle Normal
Log "Bitti rev=$ExpectedRev"

