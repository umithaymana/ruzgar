@echo off
chcp 65001 >nul
title RUZGAR — temiz baslat (tek pencere)
cd /d "%~dp0"
echo.
echo [1/2] API 8779 yeniden baslatiliyor — guncel kod yuklenecek...
echo       (Eski surec atlanirsa duzeltmeler devreye girmez.)
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RuzgarMasaustuBaslat.ps1"
if errorlevel 1 (
  echo.
  echo HATA — log: %TEMP%\ruzgar-masaustu-launch.log
  pause
  exit /b 1
)
echo.
echo Tamam. Sorun olursa once Ruzgar_YenidenBaslat.bat sonra tekrar bu dosya.
echo Ctrl+Shift+R = Electron sert yenile.
echo.
pause
