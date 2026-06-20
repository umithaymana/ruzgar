@echo off
chcp 65001 >nul
title RUZGAR — API yeniden baslat
cd /d "%~dp0"
echo.
echo [1/3] Eski API surecleri durduruluyor (8777 + 8779)...
py -3 "%~dp0ilim-assistant\scripts\ruzgar_port_ops.py" kill-all-api --port 8779 2>nul
timeout /t 2 /nobreak >nul
echo [2/3] PowerShell ile temiz yeniden baslatma...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Ruzgar.ps1" -ForceRestart -ApiOnly
if errorlevel 1 (
  echo.
  echo [HATA] Yeniden baslatma basarisiz.
  echo Log: %TEMP%\ruzgar-launch.log
  echo Hata: %TEMP%\ruzgar-api.err
  echo.
  echo Cozum: Ruzgar_Port_Temizle.bat sag tik -^> Yonetici olarak calistir
  pause
  exit /b 1
)
echo.
echo [3/3] Tamam — API http://127.0.0.1:8779
echo Ruzgar penceresi aciksa bir kez kapatip Ruzgar_Baslat.bat ile acin.
echo veya tarayici: http://127.0.0.1:8779/ui/index.html
pause
