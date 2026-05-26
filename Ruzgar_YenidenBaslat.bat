@echo off
chcp 65001 >nul
title RUZGAR — API yeniden baslat (Faz 14)
cd /d "%~dp0"
echo.
echo Eski API surecleri durduruluyor (8777 + 8779)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Ruzgar.ps1" -ForceRestart
if errorlevel 1 (
  echo.
  echo [HATA] Yeniden baslatma basarisiz. Log: %TEMP%\ruzgar-launch.log
  pause
  exit /b 1
)
echo.
echo Tamam. Saglik/build: faz77-v86 (ROK Faz 68-77 + hub + cila).
pause
