# RUZGAR — masaustu (Electron) + API 8779 (Faz 98)
# Temiz baslat = diskteki guncel kod yuklensin diye API her seferinde yeniden baslatilir.

param(
    [switch]$FastReuse
)

$ErrorActionPreference = "Continue"

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
    # ignore
}

Add-Type -AssemblyName System.Windows.Forms -ErrorAction SilentlyContinue

$Root = $PSScriptRoot

$Ia = Join-Path $Root "ilim-assistant"

$Rd = Join-Path $Root "ruzgar-desktop"

$Log = Join-Path $env:TEMP "ruzgar-masaustu-launch.log"

$ApiErr = Join-Path $env:TEMP "ruzgar-api.err"

$ExpectedRev = & py -3 (Join-Path $Ia "scripts\ruzgar_read_build_rev.py") 2>$null
if (-not $ExpectedRev) { $ExpectedRev = "2026-06-15-ruzgar-programlama-pro-v1" }
$ExpectedRev = $ExpectedRev.Trim()

$Port = 8779



function Log([string]$m) {
    Add-Content -Path $Log -Value "$(Get-Date -Format o) $m" -Encoding UTF8
    Write-Host "[RUZGAR] $m"
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

$env:RUZGAR_DEFER_MOTOR_BOOT = "1"

$env:RUZGAR_CORS_PERMISSIVE = "1"



function Test-HealthCurrent {

    try {

        $j = Invoke-RestMethod "http://127.0.0.1:$Port/api/health?lite=1" -TimeoutSec 10

        if (-not $j.ok) { return $false }

        if ($j.booting -eq $true) { return $true }

        $rev = [string]$j.build.rev

        if ($rev -and $rev -ne $ExpectedRev) { return $false }

        if ($j.lite -eq $true) { return $true }

        if ($j.build.programlama_pro_v1 -ne $true) { return $false }

        return $true

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
$skipApiRestart = $false
$ok = $false

# TemizBaslat: varsayilan = API'yi her zaman oldur + taze baslat (eski surec kodu bellekte tutar).
if ($FastReuse -and (Test-HealthCurrent)) {
    Log "FastReuse: API zaten saglikli — yeniden baslatma atlandi (rev=$ExpectedRev)"
    $skipApiRestart = $true
    $ok = $true
} else {
    Log "Taze API: diskteki kod yuklenecek — once eski surec durduruluyor (rev=$ExpectedRev)"
}

if (-not $skipApiRestart) {
    if (Test-Path $ops) {
        Log "Eski API surecleri durduruluyor (port $Port)"
        & py -3 $ops kill-all-api --port $Port 2>&1 | ForEach-Object { Log $_ }
        Start-Sleep -Seconds 2
        if (-not (Test-PortFree)) {
            Log "Port $Port hala dolu - yonetici temizligi deneniyor"
            $bat = Join-Path $Root "Ruzgar_Port_Temizle.bat"
            if (Test-Path $bat) {
                Start-Process -FilePath $bat -Verb RunAs -Wait
                Start-Sleep -Seconds 2
                & py -3 $ops kill-all-api --port $Port 2>&1 | ForEach-Object { Log $_ }
                Start-Sleep -Seconds 1
            }
        }
        if (-not (Test-PortFree)) {
            Log "UYARI port $Port hala dolu - Ruzgar_Port_Temizle.bat (yonetici) gerekebilir"
        }
    }

    if (-not (Test-PortFree)) {
        Log "HATA port $Port bosaltilamadi (zombi surec)"
        $msg = @"
Port $Port hala kilitli - yeni API baslatilamaz.

1) Ruzgar_Port_Temizle.bat dosyasina sag tik - Yonetici olarak calistir
2) Sonra Ruzgar_TemizBaslat.bat tekrar deneyin

Log: $Log
"@
        [System.Windows.Forms.MessageBox]::Show($msg, "RUZGAR") | Out-Null
        exit 1
    }

    Remove-Item $ApiErr -ErrorAction SilentlyContinue
    Log "API baslatiliyor..."
    Start-Process -FilePath "py" -ArgumentList @("-3", "run_desktop_api.py", "--host", "127.0.0.1", "--port", "$Port") -WorkingDirectory $Ia -WindowStyle Hidden -RedirectStandardError $ApiErr

    for ($i = 0; $i -lt 300; $i++) {
        if (Test-HealthCurrent) { $ok = $true; break }
        Start-Sleep -Milliseconds 500
    }
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

try {
    $hj = Invoke-RestMethod "http://127.0.0.1:$Port/api/health" -TimeoutSec 10
    $liveRev = [string]$hj.build.rev
    Log "API build.rev=$liveRev beklenen=$ExpectedRev"
    if ($liveRev -ne $ExpectedRev) {
        Log "UYARI build rev uyumsuz - port temizleyip tekrar deneyin"
    }
} catch {
    Log "UYARI health rev kontrolu atlandi"
}

$env:RUZGAR_EXPECTED_BUILD_REV = $ExpectedRev
$env:RUZGAR_ELECTRON_API_FRESH = "1"

$markerDir = Join-Path $Root ".ruzgar"
if (-not (Test-Path $markerDir)) { New-Item -ItemType Directory -Path $markerDir -Force | Out-Null }
$marker = Join-Path $markerDir "electron_api_fresh.marker"
$ExpectedRev | Set-Content -Path $marker -Encoding UTF8 -NoNewline
Log "Electron fresh marker yazildi rev=$ExpectedRev"



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

