# RUZGAR - API (8777) + Electron; istege bagli Gradio tarayici (7861): Ruzgar.ps1 -WithGradio veya Ruzgar_Hepsi.bat
# Zorla yeniden baslatma: Ruzgar.ps1 -ForceRestart  (8777 portunu bosaltir, API+Electron)
param(
    [switch]$WithGradio,
    [switch]$ForceRestart
)
$WantGradio = $WithGradio.IsPresent -or ($env:RUZGAR_WITH_GRADIO -eq "1")

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Log = Join-Path $env:TEMP "ruzgar-launch.log"
$ApiErr = Join-Path $env:TEMP "ruzgar-api.err"
$ApiPort = 8777
if ($env:RUZGAR_API_PORT) { [int]$ApiPort = $env:RUZGAR_API_PORT }
$GradioPort = 7861
if ($env:RUZGAR_GRADIO_PORT) { [int]$GradioPort = $env:RUZGAR_GRADIO_PORT }

function Log([string]$m) {
    "$(Get-Date -Format o) $m" | Out-File -FilePath $Log -Append -Encoding utf8
}

function Import-RuzgarEnvFile {
    param([string]$IaRoot)
    $envPath = Join-Path $IaRoot ".env"
    if (-not (Test-Path $envPath)) {
        return $false
    }
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
            $env:GEMINI_API_KEY = $val
            $env:RUZGAR_GEMINI_API_KEY = $val
            continue
        }
        if (-not (Get-Item -Path "Env:$key" -ErrorAction SilentlyContinue)) {
            Set-Item -Path "Env:$key" -Value $val
        }
    }
    return [bool]($env:GLOBAL_API_KEY -and $env:GLOBAL_API_KEY.Trim())
}

function Invoke-RuzgarPortOps {
    param(
        [string]$Command,
        [string]$IaRoot,
        [int]$Port = 8777
    )
    $ops = Join-Path $IaRoot "scripts\ruzgar_port_ops.py"
    if (-not (Test-Path $ops)) {
        Log "ruzgar_port_ops.py yok — $Command atlandi"
        return -1
    }
    & $script:PyExe @($script:PyArgs) $ops $Command --port $Port 2>&1 | ForEach-Object { Log $_; $_ }
    return $LASTEXITCODE
}

function Test-RuzgarGeminiKeyConfigured {
    param([string]$IaRoot)
    if (Import-RuzgarEnvFile -IaRoot $IaRoot) {
        return $true
    }
    $probe = Join-Path $IaRoot "scripts\ruzgar_gemini_ready.py"
    if (-not (Test-Path $probe)) { return $false }
    try {
        $out = & $script:PyExe @($script:PyArgs) $probe 2>$null
        return ($out -match "^\s*1\s*$")
    } catch {
        return $false
    }
}

Log "Basladi Root=$Root port=$ApiPort WantGradio=$WantGradio ForceRestart=$ForceRestart"

function Find-Py {
    try {
        $c = Get-Command py -ErrorAction Stop
        return @($c.Path, @("-3"))
    } catch {}
    try {
        $c = Get-Command python -ErrorAction Stop
        return @($c.Path, @())
    } catch {}
    return $null
}

function Ensure-PythonDeps {
    $req = Join-Path $Root "ilim-assistant\requirements.txt"
    if (-not (Test-Path $req)) { return }
    & $script:PyExe @($script:PyArgs) -c "import fastapi,uvicorn" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Log "pip install..."
        & $script:PyExe @($script:PyArgs) -m pip install -r $req
        if ($LASTEXITCODE -ne 0) { throw "pip basarisiz" }
    }
}

function Test-ApiImport {
    param([string]$Ia)
    Push-Location $Ia
    try {
        & $script:PyExe @($script:PyArgs) -c "import desktop_server; print('desktop_server ok')" 2>&1 | Out-File -FilePath $ApiErr -Encoding utf8
        if ($LASTEXITCODE -ne 0) {
            throw "Python import basarisiz (ruzgar-api.err)"
        }
    } finally {
        Pop-Location
    }
}

function Start-ApiServer {
    param([string]$Ia)
    Remove-Item $ApiErr -ErrorAction SilentlyContinue
    if ($env:GLOBAL_API_KEY -and $env:GLOBAL_API_KEY.Trim()) {
        $len = $env:GLOBAL_API_KEY.Trim().Length
        Log "GLOBAL_API_KEY aktarildi (uzunluk=$len) — Gemini arayuz+API"
    } else {
        Log "UYARI: GLOBAL_API_KEY bos — API Gemini kullanamaz"
    }
    $uargs = @()
    foreach ($x in $script:PyArgs) { $uargs += $x }
    $uargs += "-m"
    $uargs += "uvicorn"
    $uargs += "desktop_server:app"
    $uargs += "--host"
    $uargs += "127.0.0.1"
    $uargs += "--port"
    $uargs += "$ApiPort"
    Log "API: $PyExe $($uargs -join ' ') WD=$Ia"
    try {
        Start-Process -FilePath $script:PyExe -ArgumentList $uargs -WorkingDirectory $Ia `
            -WindowStyle Hidden -RedirectStandardError $ApiErr -PassThru | Out-Null
    } catch {
        Log "Start-Process redirect basarisiz, redirectsiz deneniyor"
        Start-Process -FilePath $script:PyExe -ArgumentList $uargs -WorkingDirectory $Ia -WindowStyle Hidden
    }
}

function Start-ElectronApp {
    param([string]$AppsRoot)
    $rd = Join-Path $AppsRoot "ruzgar-desktop"
    if (-not (Test-Path (Join-Path $rd "package.json"))) {
        throw "ruzgar-desktop eksik"
    }

    $electronCmd = Join-Path $rd "node_modules\.bin\electron.cmd"
    if (-not (Test-Path $electronCmd)) {
        Log "npm install..."
        Push-Location $rd
        & npm install
        $ni = $LASTEXITCODE
        Pop-Location
        if ($ni -ne 0) { throw "npm install basarisiz" }
    }

    if (-not (Test-Path $electronCmd)) {
        throw "electron.cmd yok: $electronCmd"
    }

    Log "Electron: $electronCmd ."
    Start-Process -FilePath $electronCmd -ArgumentList "." -WorkingDirectory $rd -ErrorAction Stop
}

function Read-ApiErrTail {
    if (-not (Test-Path $ApiErr)) { return "(ruzgar-api.err yok)" }
    try {
        return (Get-Content $ApiErr -Tail 25 -ErrorAction Stop) -join "`n"
    } catch {
        return "(log okunamadi)"
    }
}

function Test-GradioUp {
    try {
        $u = "http://127.0.0.1:$script:GradioPort/"
        $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 2
        return $r.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Start-GradioProcess {
    param([string]$WorkDir)
    $pyPart = "`"$($script:PyExe)`""
    foreach ($a in $script:PyArgs) {
        $pyPart += " $a"
    }
    $pyPart += " gradio_chat.py"
    $cmd = "title RUZGAR - Gradio sohbet & chcp 65001 >nul & cd /d `"$WorkDir`" & $pyPart"
    Log "Gradio cmd /k: $cmd"
    Start-Process -FilePath "cmd.exe" -ArgumentList @("/k", $cmd) -ErrorAction Stop
}

$py = Find-Py
if ($null -eq $py) {
    [void][System.Windows.Forms.MessageBox]::Show("Python bulunamadi (py veya python PATH'te olmali).", "RUZGAR")
    exit 1
}
$script:PyExe = $py[0]
$script:PyArgs = $py[1]

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    [void][System.Windows.Forms.MessageBox]::Show("npm bulunamadi (Node.js LTS kurun).", "RUZGAR")
    exit 1
}

$iaJoin = Join-Path $Root "ilim-assistant"
if (-not (Test-Path (Join-Path $iaJoin "desktop_server.py"))) {
    [void][System.Windows.Forms.MessageBox]::Show("ilim-assistant\desktop_server.py bulunamadi.", "RUZGAR")
    exit 1
}
$ia = (Resolve-Path $iaJoin).Path

if (Test-RuzgarGeminiKeyConfigured -IaRoot $ia) {
    Log "Gemini GLOBAL_API_KEY yuklu — anahtar sorulmadan Gemini-2.0-flash hazir"
    if (-not $env:RUZGAR_GEMINI_MODEL) { $env:RUZGAR_GEMINI_MODEL = "gemini-2.0-flash" }
    if (-not $env:RUZGAR_SUPER_BRAIN) { $env:RUZGAR_SUPER_BRAIN = "1" }
} else {
    Log "Gemini anahtar yok (.env GLOBAL_API_KEY) — yerel Ollama kullanilir"
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

function Start-OllamaIfNeeded {
    if (Test-PortListen 11434) {
        Log "Ollama zaten dinliyor (11434)"
        return
    }
    if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
        Log "Ollama PATH'te yok — https://ollama.com kurulumu gerekir (ucretsiz yerel beyin)"
        return
    }
    Log "Ollama serve baslatiliyor..."
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
    $deadline = (Get-Date).AddSeconds(12)
    while (-not (Test-PortListen 11434) -and (Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 400
    }
    if (Test-PortListen 11434) {
        Log "Ollama hazir (11434)"
        & ollama pull llama3.2:3b 2>$null | Out-Null
    } else {
        Log "Ollama acilmadi — yine de API/Electron baslatilacak"
    }
}

if (-not $env:RUZGAR_FREE_BRAIN) { $env:RUZGAR_FREE_BRAIN = "1" }
if ($env:RUZGAR_FREE_BRAIN -eq "1") {
    Start-OllamaIfNeeded
}

$env:RUZGAR_CORS_PERMISSIVE = "1"

$portCheckRc = Invoke-RuzgarPortOps -Command "port-check" -IaRoot $ia -Port $ApiPort
# 0=saglikli, 1=bos, 2=kilitli/zombi
if ($ForceRestart) {
    Log "force-restart: 8777 portu bosaltiliyor"
    $null = Invoke-RuzgarPortOps -Command "kill-process" -IaRoot $ia -Port $ApiPort
    Start-Sleep -Seconds 1
    $portCheckRc = 1
} elseif ($portCheckRc -eq 2) {
    Log "port-check: kilitli/zombi — kill-process"
    $null = Invoke-RuzgarPortOps -Command "kill-process" -IaRoot $ia -Port $ApiPort
    Start-Sleep -Seconds 1
    $portCheckRc = 1
}

$apiUrl = "http://127.0.0.1:$ApiPort/api/health"
$serverUp = ($portCheckRc -eq 0)
if (-not $serverUp) {
    try {
        $r = Invoke-WebRequest -Uri $apiUrl -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $serverUp = $true }
    } catch {}
}

if (-not $serverUp) {
    try {
        Ensure-PythonDeps
        Test-ApiImport -Ia $ia
        Start-ApiServer -Ia $ia
        $ok = $false
        for ($i = 0; $i -lt 180; $i++) {
            try {
                $r2 = Invoke-WebRequest -Uri $apiUrl -UseBasicParsing -TimeoutSec 2
                if ($r2.StatusCode -eq 200) { $ok = $true; break }
            } catch { }
            Start-Sleep -Milliseconds 500
        }
        if (-not $ok) {
            $tail = Read-ApiErrTail
            [void][System.Windows.Forms.MessageBox]::Show(
                "API acilmadi: $apiUrl`n`nSon hata (ruzgar-api.err):`n$tail`n`nTam log: $Log",
                "RUZGAR"
            )
            exit 1
        }
    } catch {
        Log "API blok hata: $($_.Exception.Message)"
        $tail = Read-ApiErrTail
        [void][System.Windows.Forms.MessageBox]::Show(
            "API kurulum/baslatma hatasi:`n$($_.Exception.Message)`n`n$tail`n`nLog: $Log",
            "RUZGAR"
        )
        exit 1
    }
}

if ($WantGradio) {
    if (-not (Test-Path (Join-Path $ia "gradio_chat.py"))) {
        Log "gradio_chat.py yok, Gradio atlandi"
    } else {
        try {
            if (-not (Test-GradioUp)) {
                Ensure-PythonDeps
                Start-GradioProcess -WorkDir $ia
                $gok = $false
                for ($i = 0; $i -lt 240; $i++) {
                    if (Test-GradioUp) {
                        $gok = $true
                        break
                    }
                    Start-Sleep -Milliseconds 500
                }
                if (-not $gok) {
                    Log "Gradio zaman asimi (port $GradioPort)"
                    [void][System.Windows.Forms.MessageBox]::Show(
                        "Gradio (tarayici) ayaga kalkmadi: http://127.0.0.1:$GradioPort`n`nAcilan cmd penceresindeki Python hatasini kontrol edin.`nYine de masaustu (Electron) acilacak.`nLog: $Log",
                        "RUZGAR"
                    )
                } else {
                    Log "Gradio hazir"
                    Start-Process "http://127.0.0.1:$GradioPort/"
                }
            } else {
                Log "Gradio zaten calisiyor"
                Start-Process "http://127.0.0.1:$GradioPort/"
            }
        } catch {
            Log "Gradio hata: $($_.Exception.Message)"
            [void][System.Windows.Forms.MessageBox]::Show(
                "Gradio baslatilamadi: $($_.Exception.Message)`nElectron yine de denenecek. Log: $Log",
                "RUZGAR"
            )
        }
    }
}

try {
    $finalRc = Invoke-RuzgarPortOps -Command "port-check" -IaRoot $ia -Port $ApiPort
    if ($finalRc -eq 0) {
        Log "Baglanti aktif — port $ApiPort dinleniyor (health OK)"
    } else {
        Log "UYARI: Electron aciliyor ama port-check rc=$finalRc"
    }
    Start-ElectronApp -AppsRoot $Root
    Log "Electron OK — UI: Ruzgar Baslatildi - Baglanti Aktif"
} catch {
    Log "Electron hata: $($_.Exception.Message)"
    [void][System.Windows.Forms.MessageBox]::Show("RUZGAR acilamadi: $($_.Exception.Message)`nLog: $Log", "RUZGAR")
    exit 1
}

exit 0
