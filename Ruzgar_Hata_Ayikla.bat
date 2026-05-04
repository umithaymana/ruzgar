@echo off
chcp 65001 >nul
title RUZGAR hata ayiklama
cd /d "%~dp0"
echo RUZGAR baslatiliyor (pencere acik, hata gorunur)...
echo.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Ruzgar.ps1"
echo.
echo Cikis kodu: %ERRORLEVEL%
echo Log: %TEMP%\ruzgar-launch.log
echo.
pause
