# RUZGAR - API (8777) + Electron; istege bagli Gradio tarayici (7861): Ruzgar.ps1 -WithGradio veya Ruzgar_Hepsi.bat
param(
    [switch]$WithGradio
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
Log "Basladi Root=$Root port=$ApiPort WantGradio=$WantGradio"

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

$apiUrl = "http://127.0.0.1:$ApiPort/api/health"
$serverUp = $false
try {
    $r = Invoke-WebRequest -Uri $apiUrl -UseBasicParsing -TimeoutSec 2
    if ($r.StatusCode -eq 200) { $serverUp = $true }
} catch {}

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
    Start-ElectronApp -AppsRoot $Root
    Log "Electron OK"
} catch {
    Log "Electron hata: $($_.Exception.Message)"
    [void][System.Windows.Forms.MessageBox]::Show("RUZGAR acilamadi: $($_.Exception.Message)`nLog: $Log", "RUZGAR")
    exit 1
}

exit 0
