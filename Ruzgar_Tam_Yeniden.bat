@echo off
chcp 65001 >nul
title RUZGAR — tam yeniden baslat (Faz 98)
cd /d "%~dp0"

net session >nul 2>&1
if errorlevel 1 (
    echo Yonetici izni ile tam yeniden baslatma...
    powershell -NoProfile -Command "Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','\"\"%~f0\"\" /elevated' -Verb RunAs -Wait"
    exit /b %ERRORLEVEL%
)

if /i "%~1"=="/elevated" shift

echo Electron kapatiliyor...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='electron.exe'\" -EA SilentlyContinue | Where-Object { $_.CommandLine -match 'ruzgar-desktop' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue }"

set RUZGAR_EXPECTED_BUILD_REV=2026-05-27-ruzgar-faz98-v107
echo Eski API (PID 8779) durduruluyor...
py -3 "%~dp0ilim-assistant\scripts\ruzgar_port_ops.py" kill-all-api --port 8779
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8779.*LISTENING"') do taskkill /F /T /PID %%a 2>nul
timeout /t 3 /nobreak >nul

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Ruzgar.ps1" -ForceRestart
if errorlevel 1 (
    echo HATA — %TEMP%\ruzgar-launch.log
    pause
    exit /b 1
)
echo.
echo Tamam. Build: 2026-05-27-ruzgar-faz98-v107
echo Tarayici: http://127.0.0.1:8779/ui/index.html
pause
