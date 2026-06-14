@echo off
chcp 65001 >nul
title RUZGAR — port 8779 temizle (yonetici)
cd /d "%~dp0"

net session >nul 2>&1
if errorlevel 1 (
    echo Yonetici izni isteniyor...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs -Wait"
    exit /b %ERRORLEVEL%
)

echo.
echo [Yonetici] Port 8779/8777 ve Ruzgar API python surecleri durduruluyor...
set RUZGAR_EXPECTED_BUILD_REV=2026-06-14-ruzgar-web-first-faz-ap2
py -3 "%~dp0ilim-assistant\scripts\ruzgar_port_ops.py" kill-all-api --port 8779
py -3 "%~dp0ilim-assistant\scripts\ruzgar_port_ops.py" kill-process --port 8779
py -3 "%~dp0ilim-assistant\scripts\ruzgar_port_ops.py" kill-process --port 8777
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8779.*LISTENING"') do taskkill /F /T /PID %%a 2>nul
timeout /t 2 /nobreak >nul
py -3 "%~dp0ilim-assistant\scripts\ruzgar_port_ops.py" port-check --port 8779
echo.
echo Bitti. Simdi Ruzgar_TemizBaslat.bat calistirin.
pause
