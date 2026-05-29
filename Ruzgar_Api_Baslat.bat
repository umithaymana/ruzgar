@echo off
chcp 65001 >nul
title RUZGAR — yalnizca API (tarayici icin)
cd /d "%~dp0"
echo.
echo Yerel API baslatiliyor (port 8779)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Ruzgar.ps1" -ApiOnly
if errorlevel 1 (
  echo.
  echo HATA — log: %TEMP%\ruzgar-launch.log
  pause
  exit /b 1
)
echo.
echo Tarayicida acin:
echo   http://127.0.0.1:8779/ui/index.html
echo.
start "" "http://127.0.0.1:8779/ui/index.html"
pause
