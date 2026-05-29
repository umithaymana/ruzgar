@echo off
chcp 65001 >nul
title RUZGAR — tarayicida ac
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Ruzgar_TarayiciBaslat.ps1"
if errorlevel 1 (
    echo HATA — log: %TEMP%\ruzgar-tarayici-launch.log
    pause
    exit /b 1
)
echo Acildi: http://127.0.0.1:8779/ui/index.html
timeout /t 3 /nobreak >nul
