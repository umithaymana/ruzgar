# Desktop shortcut: wscript + VBS = cmd penceresi acilmaz
param([switch]$Quiet)
Add-Type -AssemblyName System.Windows.Forms
if ($PSScriptRoot) {
    $Root = Split-Path -Parent $PSScriptRoot
} else {
    $Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}

$vbs = Join-Path $Root "RuzgarLauncher.vbs"
$ico = Join-Path $Root "ruzgar-desktop\assets\ruzgar.ico"
$wscript = Join-Path $env:SystemRoot "System32\wscript.exe"

if (-not (Test-Path $vbs)) {
    if (-not $Quiet) {
        [System.Windows.Forms.MessageBox]::Show("RuzgarLauncher.vbs bulunamadi: $vbs", "RUZGAR") | Out-Null
    }
    exit 1
}

if (-not (Test-Path $ico)) {
    $png = Join-Path $Root "ruzgar-desktop\assets\icon.png"
    if ((Test-Path $png)) {
        try {
            $py = $env:RUZGAR_PYTHON
            if (-not $py -or -not (Test-Path $py)) {
                $py = "D:\ÜMİT\PROGRAMLAR\venvs\ruzgar\Scripts\python.exe"
            }
            if (Test-Path $py) {
                & $py -m pip install pillow -q 2>$null
                & $py (Join-Path $Root "scripts\build_ruzgar_ico.py")
            }
        } catch {}
    }
}

if (-not (Test-Path $ico)) {
    $ico = "$env:SystemRoot\System32\imageres.dll,110"
}

$Wsh = New-Object -ComObject WScript.Shell
$deskShell = $Wsh.SpecialFolders.Item("Desktop")
$deskEnv = [Environment]::GetFolderPath("Desktop")

function New-RuzgarShortcut {
    param([string]$DesktopFolder)
    $p = Join-Path $DesktopFolder "RUZGAR.lnk"
    $Sc = $Wsh.CreateShortcut($p)
    $Sc.TargetPath = $wscript
    $Sc.Arguments = '//B //nologo "' + $vbs + '"'
    $Sc.WorkingDirectory = $Root
    $Sc.IconLocation = $ico
    $Sc.Description = "RUZGAR - Electron + API 8779 (cift tik ile ac)"
    $Sc.Save()
    return $p
}

$rev = "8779"
try {
    $revScript = Join-Path $Root "ilim-assistant\scripts\ruzgar_read_build_rev.py"
    $py = $env:RUZGAR_PYTHON
    if (-not $py -or -not (Test-Path $py)) {
        $py = "D:\ÜMİT\PROGRAMLAR\venvs\ruzgar\Scripts\python.exe"
    }
    if ((Test-Path $revScript) -and (Test-Path $py)) {
        $r = (& $py $revScript 2>$null | Out-String).Trim()
        if ($r) { $rev = $r }
    }
} catch {}

$primary = New-RuzgarShortcut -DesktopFolder $deskShell
$secondaryPath = $null
try {
    $a = (Resolve-Path $deskShell).Path.TrimEnd('\')
    $b = (Resolve-Path $deskEnv).Path.TrimEnd('\')
    if ($a -ne $b -and (Test-Path $deskEnv)) {
        $secondaryPath = New-RuzgarShortcut -DesktopFolder $deskEnv
    }
} catch {}

if (-not (Test-Path $primary)) {
    if (-not $Quiet) {
        [System.Windows.Forms.MessageBox]::Show("Kisayol yazilamadi: $primary", "RUZGAR") | Out-Null
    }
    Write-Host "FAIL: $primary"
    exit 1
}

Write-Host "OK $primary"
if ($secondaryPath) { Write-Host "OK2 $secondaryPath" }

if (-not $Quiet) {
    try {
        Start-Process "explorer.exe" -ArgumentList "/select,`"$primary`""
    } catch {}

    $msg = "RUZGAR masaustu kisayolu hazir.`n`n$primary"
    if ($secondaryPath) {
        $msg += "`n`nIkinci konum:`n$secondaryPath"
    }
    $msg += @"

Cift tik: Ruzgar acilir (Electron + API).
Adres: http://127.0.0.1:8779
Build: $rev

Not: Her acilista taze API yuklenir.
"@

    [System.Windows.Forms.MessageBox]::Show($msg, "RUZGAR") | Out-Null
}
