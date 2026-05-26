# RUZGAR - API (8779) + Electron; istege bagli Gradio tarayici (7861): Ruzgar.ps1 -WithGradio veya Ruzgar_Hepsi.bat
# Zorla yeniden baslatma: Ruzgar.ps1 -ForceRestart  (8779 + eski 8777 zombi portunu bosaltir)
param(
    [switch]$WithGradio,
    [switch]$ForceRestart,
    [switch]$ApiOnly
)
$WantGradio = $WithGradio.IsPresent -or ($env:RUZGAR_WITH_GRADIO -eq "1")

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Log = Join-Path $env:TEMP "ruzgar-launch.log"
$ApiErr = Join-Path $env:TEMP "ruzgar-api.err"
$ApiPort = 8779
if ($env:RUZGAR_API_PORT) { [int]$ApiPort = $env:RUZGAR_API_PORT }
# 8777'de eski/zombi uvicorn kalabiliyor; varsayilan yeni motor 8779
$GradioPort = 7861
if ($env:RUZGAR_GRADIO_PORT) { [int]$GradioPort = $env:RUZGAR_GRADIO_PORT }

function Log([string]$m) {
    "$(Get-Date -Format o) $m" | Out-File -FilePath $Log -Append -Encoding utf8
}

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
        $forceFromFile = $key -match '^(RUZGAR_|OLLAMA_|GROQ_|GLOBAL_|GOOGLE_GEMINI_|GEMINI_)'
        if ($key -in @("GLOBAL_API_KEY", "GOOGLE_GEMINI_API_KEY", "GEMINI_API_KEY", "RUZGAR_GEMINI_API_KEY")) {
            if ($val) { Set-RuzgarGeminiKeyFromValue -Val $val }
            continue
        }
        if ($key -eq "GROQ_API_KEY") {
            if ($val) { $env:GROQ_API_KEY = $val }
            continue
        }
        if ($forceFromFile -or -not (Get-Item -Path "Env:$key" -ErrorAction SilentlyContinue)) {
            if ($val) { Set-Item -Path "Env:$key" -Value $val -Force }
        }
    }
}

function Import-RuzgarEnvFile {
    param([string]$IaRoot)
    $envPath = Join-Path $IaRoot ".env"
    if (-not (Test-Path $envPath)) {
        return $false
    }
    Import-RuzgarDotEnvFile -Path $envPath
    $brainEnv = Join-Path $IaRoot "RUZGAR_BRAIN.env"
    Import-RuzgarDotEnvFile -Path $brainEnv
    $geminiTxt = Join-Path $Root "ruzgar-desktop\google_api_key.txt"
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
        foreach ($k in @("GLOBAL_API_KEY", "GOOGLE_GEMINI_API_KEY", "GEMINI_API_KEY", "RUZGAR_GEMINI_API_KEY", "GROQ_API_KEY")) {
            Remove-Item "Env:$k" -ErrorAction SilentlyContinue
        }
        $env:RUZGAR_GEMINI_DAEMON = "0"
    }
    if ($env:RUZGAR_DISABLE_GROQ -eq "1" -or $env:RUZGAR_OLLAMA_ONLY -eq "1") {
        Remove-Item Env:GROQ_API_KEY -ErrorAction SilentlyContinue
    }
    return [bool]($env:GLOBAL_API_KEY -and $env:GLOBAL_API_KEY.Trim())
}

function Invoke-RuzgarPortOps {
    param(
        [string]$Command,
        [string]$IaRoot,
        [int]$Port = 8779
    )
    $ops = Join-Path $IaRoot "scripts\ruzgar_port_ops.py"
    if (-not (Test-Path $ops)) {
        Log "ruzgar_port_ops.py yok - $Command atlandi"
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
    $prevEa = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $importOut = & $script:PyExe @($script:PyArgs) -c "import desktop_server; print('desktop_server ok')" 2>&1
        if ($importOut) {
            ($importOut | ForEach-Object { "$_" }) | Out-File -FilePath $ApiErr -Encoding utf8
        }
        if ($LASTEXITCODE -ne 0) {
            throw "Python import basarisiz (ruzgar-api.err)"
        }
    } finally {
        $ErrorActionPreference = $prevEa
        Pop-Location
    }
}

function Start-ApiServer {
    param([string]$Ia)
    Remove-Item $ApiErr -ErrorAction SilentlyContinue
    if ($env:GLOBAL_API_KEY -and $env:GLOBAL_API_KEY.Trim()) {
        $len = $env:GLOBAL_API_KEY.Trim().Length
        Log "GLOBAL_API_KEY aktarildi (uzunluk=$len) - Gemini arayuz+API"
    } else {
        Log "UYARI: GLOBAL_API_KEY bos - API Gemini kullanamaz"
    }
    $uargs = @()
    foreach ($x in $script:PyArgs) { $uargs += $x }
    $uargs += "run_desktop_api.py"
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

Import-RuzgarEnvFile -IaRoot $ia | Out-Null
if ($env:RUZGAR_OLLAMA_ONLY -eq "1") {
    Log "RUZGAR_OLLAMA_ONLY=1 - yalnizca yerel Ollama (Gemini/Groq kapali)"
} elseif (Test-RuzgarGeminiKeyConfigured -IaRoot $ia) {
    Log "Gemini GLOBAL_API_KEY yuklu"
} else {
    Log "Bulut kapali - yerel Ollama"
}

$script:RuzgarExpectedBuildRev = "2026-05-26-programlama-faz60-v71"
$env:RUZGAR_EXPECTED_BUILD_REV = $script:RuzgarExpectedBuildRev

function Show-RuzgarFaz60BuildMismatchPrompt {
    param(
        [string]$CurrentRev,
        [string]$ExpectedRev
    )
    if ($env:RUZGAR_FAZ60 -eq "0") { return }
    if ($env:RUZGAR_FAZ60_RESTART_PROMPT -eq "0") { return }
    try {
        Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
        [void][System.Windows.Forms.MessageBox]::Show(
            @"
Eski Ruzgar API calisiyor (Faz 60).

Su an:  $CurrentRev
Beklenen: $ExpectedRev

Otomatik yeniden baslatma deneniyor.
Elle icin: Ruzgar_YenidenBaslat.bat veya .\Ruzgar.ps1 -ForceRestart
"@.Trim(),
            "Ruzgar - build uyumsuz",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Warning
        )
    } catch {
        Log "Faz60 uyari (modal atlandi): $CurrentRev != $ExpectedRev"
    }
}

function Get-RuzgarRemoteApiLine {
    $rd = Join-Path $Root "ruzgar-desktop"
    $p = Join-Path $rd "ruzgar_remote_api.txt"
    if (-not (Test-Path $p)) { return "" }
    foreach ($raw in Get-Content $p -Encoding UTF8) {
        $t = $raw.Trim()
        if ($t -and -not $t.StartsWith("#")) { return $t }
    }
    return ""
}

function Test-RuzgarColabRemote {
    param([string]$Line)
    if (-not $Line) { return $false }
    return ($Line -match '^https?://') -and ($Line -notmatch '(?i)(127\.0\.0\.1|localhost)')
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
        Log "Ollama PATH icinde yok - https://ollama.com kurulumu gerekir"
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
        $ramGb = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 0)
        $defaultMain = if ($ramGb -ge 24) { "llama3.1:70b" } elseif ($ramGb -ge 12) { "llama3.1:8b" } else { "llama3.2:3b" }
        $mainModel = if ($env:OLLAMA_CHAT_MODEL) { $env:OLLAMA_CHAT_MODEL.Trim() } else { $defaultMain }
        $fastModel = if ($env:RUZGAR_BRAIN_HIZLI_MODEL) { $env:RUZGAR_BRAIN_HIZLI_MODEL.Trim() } else { "llama3.2:3b" }
        if ($ramGb -lt 16 -and $mainModel -match "70b") {
            Log "RAM ~${ramGb} GB - 70b uygun degil, llama3.1:8b kullaniliyor"
            $mainModel = "llama3.1:8b"
            $env:OLLAMA_CHAT_MODEL = "llama3.1:8b"
            $env:RUZGAR_BRAIN_DENGE_MODEL = "llama3.1:8b"
        }
        Log "Ollama model: $mainModel (RAM ~${ramGb} GB)"
        & ollama pull $mainModel 2>&1 | ForEach-Object { Log $_ }
        if ($fastModel -and $fastModel -ne $mainModel) {
            Log "Hizli yedek model: $fastModel"
            & ollama pull $fastModel 2>$null | Out-Null
        }
    } else {
        Log "Ollama acilmadi - yine de API/Electron baslatilacak"
    }
}

$script:RuzgarRemoteApiLine = Get-RuzgarRemoteApiLine
$script:RuzgarUseColab = Test-RuzgarColabRemote -Line $script:RuzgarRemoteApiLine

if ($script:RuzgarUseColab) {
    Log "Colab uzak API: $($script:RuzgarRemoteApiLine) - yerel Ollama/API atlanacak"
} elseif ($env:RUZGAR_DISABLE_LOCAL_OLLAMA -eq "1") {
    Log "RUZGAR_DISABLE_LOCAL_OLLAMA=1 - yerel Ollama baslatilmiyor (bulut beyin)"
} elseif (-not $env:RUZGAR_FREE_BRAIN) {
    $env:RUZGAR_FREE_BRAIN = "1"
}
if (-not $script:RuzgarUseColab -and $env:RUZGAR_DISABLE_LOCAL_OLLAMA -ne "1" -and $env:RUZGAR_FREE_BRAIN -eq "1") {
    Start-OllamaIfNeeded
}

$env:RUZGAR_CORS_PERMISSIVE = "1"

$portCheckRc = Invoke-RuzgarPortOps -Command "port-check" -IaRoot $ia -Port $ApiPort
# 0=saglikli, 1=bos, 2=kilitli/zombi
function Stop-RuzgarApiPort {
    param([int]$Port)
    $null = Invoke-RuzgarPortOps -Command "kill-process" -IaRoot $ia -Port $Port
    try {
        Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
            ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    } catch {}
}

function Write-RuzgarRemoteApiTxt {
    param([int]$Port)
    $rd = Join-Path $Root "ruzgar-desktop"
    if (-not (Test-Path $rd)) { return }
    $apiLine = "http://127.0.0.1:$Port"
    $body = @(
        "# UI -> yerel API (Ruzgar.ps1 yazar, elle degistirmeyin)"
        $apiLine
    ) -join "`n"
    $out = Join-Path $rd "ruzgar_remote_api.txt"
    Set-Content -Path $out -Value $body -Encoding UTF8
    Log "ruzgar_remote_api.txt -> $apiLine"
}

function Test-ApiNebulaBuild {
    param([string]$Url)
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 4
        $j = $r.Content | ConvertFrom-Json
        $rev = $j.build.rev
        $neb = $j.build.nebula_kitap
        Log "health build.rev=$rev nebula_kitap=$neb"
        return [bool]$neb
    } catch {
        Log "health okunamadi: $($_.Exception.Message)"
        return $false
    }
}

function Wait-ApiBuildCurrent {
    param(
        [string]$Url,
        [int]$MaxSec = 120
    )
    for ($i = 0; $i -lt $MaxSec; $i++) {
        if (Test-ApiBuildCurrent -Url $Url) {
            return $true
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Test-ApiBuildCurrent {
    param([string]$Url)
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 4
        $j = $r.Content | ConvertFrom-Json
        $rev = [string]$j.build.rev
        if ($rev -ne $script:RuzgarExpectedBuildRev) {
            Log "health rev uyumsuz: '$rev' beklenen '$($script:RuzgarExpectedBuildRev)'"
            return $false
        }
        if ($rev -match "^2024-" -or $rev -match "gemini-env-fix") {
            Log "health rev cok eski: '$rev'"
            return $false
        }
        if ($env:RUZGAR_OLLAMA_ONLY -eq "1") {
            $sb = $j.super_brain
            if ($sb.gemini_configured -eq $true) {
                Log "health: Gemini hala acik - eski API sureci"
                return $false
            }
            if ($sb.ollama_only -ne $true) {
                Log "health: ollama_only bayragi yok - eski kod"
                return $false
            }
        }
        return $true
    } catch {
        return $false
    }
}

$script:ForceRestartFreshApi = $false
if ($ForceRestart) {
    Log "force-restart: portlar bosaltiliyor (port $ApiPort ve 8777 zombi)"
    Stop-RuzgarApiPort -Port $ApiPort
    if ($ApiPort -ne 8777) { Stop-RuzgarApiPort -Port 8777 }
    Start-Sleep -Seconds 2
    $portCheckRc = 1
    $script:ForceRestartFreshApi = $true
} elseif ($portCheckRc -eq 2) {
    Log "port-check: kilitli/zombi - kill-process"
    $null = Invoke-RuzgarPortOps -Command "kill-process" -IaRoot $ia -Port $ApiPort
    Start-Sleep -Seconds 1
    $portCheckRc = 1
}

$apiUrl = "http://127.0.0.1:$ApiPort/api/health"
$serverUp = ($portCheckRc -eq 0)
if ($script:ForceRestartFreshApi) {
    $serverUp = $false
} elseif (-not $serverUp) {
    try {
        $r = Invoke-WebRequest -Uri $apiUrl -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200 -and (Test-ApiBuildCurrent -Url $apiUrl)) {
            $serverUp = $true
        }
    } catch {}
}

if ($serverUp -and (-not (Test-ApiBuildCurrent -Url $apiUrl))) {
    $oldRev = "?"
    try {
        $r0 = Invoke-WebRequest -Uri $apiUrl -UseBasicParsing -TimeoutSec 3
        $j0 = $r0.Content | ConvertFrom-Json
        $oldRev = [string]$j0.build.rev
    } catch {}
    Log "Eski Ruzgar API ($oldRev) - otomatik port yeniden baslatiliyor (Faz 60)"
    $mismatchFixed = $false
    for ($killTry = 0; $killTry -lt 3; $killTry++) {
        Stop-RuzgarApiPort -Port $ApiPort
        if ($ApiPort -ne 8777) { Stop-RuzgarApiPort -Port 8777 }
        Start-Sleep -Seconds 2
        if (Test-ApiBuildCurrent -Url $apiUrl) {
            $mismatchFixed = $true
            $serverUp = $true
            Log "Build uyumu saglandi: $($script:RuzgarExpectedBuildRev)"
            break
        }
    }
    if (-not $mismatchFixed) {
        $serverUp = $false
    }
}

if ($script:RuzgarUseColab) {
    $colabRoot = $script:RuzgarRemoteApiLine.Trim().TrimEnd("/")
    $colabHealth = "$colabRoot/api/health"
    Log "Colab health: $colabHealth"
    $serverUp = $false
    for ($i = 0; $i -lt 24; $i++) {
        try {
            $rc = Invoke-WebRequest -Uri $colabHealth -UseBasicParsing -TimeoutSec 8
            if ($rc.StatusCode -eq 200) {
                $serverUp = $true
                Log "Colab API hazir"
                break
            }
        } catch {
            Log "Colab bekleniyor ($i)..."
        }
        Start-Sleep -Seconds 2
    }
    if (-not $serverUp) {
        [void][System.Windows.Forms.MessageBox]::Show(
            "Colab API yanit vermiyor:`n$colabHealth`n`nColab defterini ve ngrok hucresini calistirin; URL'yi scripts\Set-RuzgarColabUrl.ps1 ile guncelleyin.",
            "RUZGAR"
        )
        exit 1
    }
}

if (-not $serverUp -and -not $script:RuzgarUseColab) {
    try {
        Ensure-PythonDeps
        Test-ApiImport -Ia $ia
        Start-ApiServer -Ia $ia
        $ok = Wait-ApiBuildCurrent -Url $apiUrl -MaxSec 120
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

if (-not $script:RuzgarUseColab) {
    Write-RuzgarRemoteApiTxt -Port $ApiPort
} else {
    Log "ruzgar_remote_api.txt Colab adresi korunuyor"
}
$healthUrl = if ($script:RuzgarUseColab) {
    "$($script:RuzgarRemoteApiLine.Trim().TrimEnd('/'))/api/health"
} else {
    $apiUrl
}
try {
    if ($script:RuzgarUseColab) {
        if (Test-ApiBuildCurrent -Url $healthUrl) {
            Log "Colab baglantisi aktif (health OK)"
        } else {
            Log "UYARI: Colab health build uyumsuz - defteri yeniden calistirin"
        }
    } else {
        $finalRc = Invoke-RuzgarPortOps -Command "port-check" -IaRoot $ia -Port $ApiPort
        if ($finalRc -eq 0) {
            Log "Baglanti aktif - port $ApiPort dinleniyor (health OK)"
            if (-not (Test-ApiNebulaBuild -Url $apiUrl)) {
                Log "UYARI: build.nebula_kitap yok - eski desktop_server, -ForceRestart veya kod guncel mi kontrol edin"
            }
        } else {
            Log "UYARI: Electron aciliyor ama port-check rc=$finalRc"
        }
    }
    if (-not $ApiOnly) {
        Start-ElectronApp -AppsRoot $Root
        Log "Electron OK - UI: Ruzgar Baslatildi - Baglanti Aktif"
    } else {
        Log "ApiOnly - Electron atlandi (API yeniden baslatildi)"
        if (-not (Test-ApiBuildCurrent -Url $apiUrl)) {
            [void][System.Windows.Forms.MessageBox]::Show(
                "API yeniden baslatildi ama build hala uyumsuz.`nBeklenen: $($script:RuzgarExpectedBuildRev)`nLog: $Log",
                "RUZGAR"
            )
            exit 1
        }
    }
} catch {
    Log "Electron hata: $($_.Exception.Message)"
    if (-not $ApiOnly) {
        [void][System.Windows.Forms.MessageBox]::Show("RUZGAR acilamadi: $($_.Exception.Message)`nLog: $Log", "RUZGAR")
    }
    exit 1
}

exit 0
