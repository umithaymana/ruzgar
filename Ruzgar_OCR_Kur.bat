@echo off
chcp 65001 >nul
title RUZGAR — OCR kurulum (Arapca + Osmanlica)
cd /d "%~dp0.."
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Ruzgar_OCR_Kur.ps1"
if errorlevel 1 (
  echo.
  echo Kurulum tamamlanamadi.
  pause
  exit /b 1
)
echo.
pause
