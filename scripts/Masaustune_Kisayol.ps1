# Desktop shortcut: wscript + VBS = cmd penceresi acilmaz
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
    [System.Windows.Forms.MessageBox]::Show("RuzgarLauncher.vbs bulunamadi: $vbs", "RUZGAR") | Out-Null
    exit 1
}

if (-not (Test-Path $ico)) {
    $png = Join-Path $Root "ruzgar-desktop\assets\icon.png"
    if ((Test-Path $png)) {
        try {
            & py -3 -m pip install pillow -q 2>$null
            & py -3 (Join-Path $Root "scripts\build_ruzgar_ico.py")
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
    $Sc.Description = "RUZGAR Faz 98 - masaustu Electron + API 8779"
    $Sc.Save()
    return $p
}

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
    [System.Windows.Forms.MessageBox]::Show("Kisayol yazilamadi: $primary", "RUZGAR") | Out-Null
    exit 1
}

try {
    Start-Process "explorer.exe" -ArgumentList "/select,`"$primary`""
} catch {}

$msg = "RUZGAR kisayolu guncellendi.`n`n$primary"
if ($secondaryPath) {
    $msg += "`n`nIkinci konum:`n$secondaryPath"
}
$msg += "`n`nCift tik: masaustu Ruzgar (Electron) acilir.`nAPI: http://127.0.0.1:8779`nBuild: faz98-v107"

[System.Windows.Forms.MessageBox]::Show($msg, "RUZGAR") | Out-Null
