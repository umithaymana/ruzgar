@echo off
chcp 65001 >nul
title RÜZGAR — sohbet
cd /d "%~dp0ilim-assistant"
if not exist "gradio_chat.py" (
  echo [HATA] ilim-assistant klasoru bulunamadi.
  pause
  exit /b 1
)

where py >nul 2>&1
if not errorlevel 1 (set "PY=py -3") else set "PY=python"

echo RÜZGAR baslatiliyor...
echo Tarayici bir kac saniye icinde acilacak: http://127.0.0.1:7861
echo Kapatmak icin bu pencerede Ctrl+C
echo.

REM Sunucu ayaga kalkana kadar bekleyip tarayiciyi ac
start "" cmd /c "ping -n 9 127.0.0.1 >nul && start http://127.0.0.1:7861/"

%PY% gradio_chat.py
if errorlevel 1 (
  echo.
  echo [HATA] Calistirma basarisiz. Once "Ruzgar_Kurulum.bat" calistirdiniz mi?
  echo Ollama acik mi? ^(ollama serve^)
)
pause
