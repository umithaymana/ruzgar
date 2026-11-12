# Rüzgar Mobil — masaüstü ikon (PWA / Chrome app mode)
# Mimar: 2026-11-12 «sen chrome al» — Chrome öncelik, uzantısız.
param([switch]$Quiet)

Add-Type -AssemblyName System.Windows.Forms

if ($PSScriptRoot) {
    $Root = Split-Path -Parent $PSScriptRoot
} else {
    $Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}

$url = "http://127.0.0.1:8779/mobil/?v=8"
$ico = Join-Path $Root "ruzgar-desktop\assets\ruzgar.ico"
if (-not (Test-Path $ico)) {
    $ico = "$env:SystemRoot\System32\imageres.dll,110"
}

# Chrome önce; yoksa Edge; yoksa varsayılan tarayıcı URL
$chrome = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

$edge = @(
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

$Wsh = New-Object -ComObject WScript.Shell
$deskShell = $Wsh.SpecialFolders.Item("Desktop")
$deskEnv = [Environment]::GetFolderPath("Desktop")

function New-MobilShortcut {
    param([string]$DesktopFolder)
    $p = Join-Path $DesktopFolder "Rüzgar Mobil.lnk"
    $Sc = $Wsh.CreateShortcut($p)
    if ($chrome) {
        $Sc.TargetPath = $chrome
        $Sc.Arguments = "--app=`"$url`" --disable-extensions --new-window"
    } elseif ($edge) {
        $Sc.TargetPath = $edge
        $Sc.Arguments = "--app=`"$url`" --disable-extensions --new-window"
    } else {
        $Sc.TargetPath = $url
    }
    $Sc.WorkingDirectory = $Root
    $Sc.IconLocation = $ico
    $Sc.Description = "Rüzgar Mobil PWA — Chrome app (kapı 8779/mobil)"
    $Sc.Save()
    return $p
}

$primary = New-MobilShortcut -DesktopFolder $deskShell
$secondaryPath = $null
try {
    $a = (Resolve-Path $deskShell).Path.TrimEnd('\')
    $b = (Resolve-Path $deskEnv).Path.TrimEnd('\')
    if ($a -ne $b -and (Test-Path $deskEnv)) {
        $secondaryPath = New-MobilShortcut -DesktopFolder $deskEnv
    }
} catch {}

if (-not (Test-Path $primary)) {
    if (-not $Quiet) {
        [System.Windows.Forms.MessageBox]::Show("Mobil kisayol yazilamadi: $primary", "Rüzgar Mobil") | Out-Null
    }
    Write-Host "FAIL: $primary"
    exit 1
}

Write-Host "OK $primary"
if ($secondaryPath) { Write-Host "OK2 $secondaryPath" }
Write-Host "URL $url"

if (-not $Quiet) {
    try {
        Start-Process "explorer.exe" -ArgumentList "/select,`"$primary`""
    } catch {}
    $engine = if ($edge) { "Edge app" } elseif ($chrome) { "Chrome app" } else { "varsayilan tarayici" }
    $msg = @"
Rüzgar Mobil masaüstü ikonu hazir.

$primary

Cift tik: $engine ile $url acilir.
Telefonda: ayni adres → «Ana ekrana ekle».
"@
    [System.Windows.Forms.MessageBox]::Show($msg, "Rüzgar Mobil") | Out-Null
}
