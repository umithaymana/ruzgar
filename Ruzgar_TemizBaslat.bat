@echo off
chcp 65001 >nul
title RUZGAR — temiz baslat (tek pencere)
cd /d "%~dp0"
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RuzgarMasaustuBaslat.ps1"
if errorlevel 1 (
  echo.
  echo HATA — log: %TEMP%\ruzgar-masaustu-launch.log
  pause
  exit /b 1
)
echo.
echo Tamam. Sorun olursa Ctrl+Shift+R ile sert yenile (Electron icinde).
echo.
pause
