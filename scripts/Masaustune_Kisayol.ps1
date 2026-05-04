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
    $Sc.Description = "RUZGAR - cmd acmaz; VBS ile baslatir"
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

$msg = "RUZGAR kisayolu guncellendi (artik siyah cmd penceresi olmamali).`n`n$primary"
if ($secondaryPath) {
    $msg += "`n`nIkinci konum:`n$secondaryPath"
}
$msg += "`n`nEski kisayolu silip bunu kullanin; cift tiklayinca yalnizca RUZGAR penceresi gelmeli."

[System.Windows.Forms.MessageBox]::Show($msg, "RUZGAR") | Out-Null
