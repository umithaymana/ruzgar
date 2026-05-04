@echo off
chcp 65001 >nul
title RÜZGAR — ilk kurulum
cd /d "%~dp0ilim-assistant"
if not exist "gradio_chat.py" (
  echo [HATA] ilim-assistant klasoru bulunamadi. Bu dosyayi YAPAY ZEKA klasorunde tutun.
  pause
  exit /b 1
)

where py >nul 2>&1
if not errorlevel 1 (set "PY=py -3") else set "PY=python"

echo Python paketleri kuruluyor ^(bir kez; uzun sürebilir^)...
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
  echo [HATA] pip kurulumu basarisiz.
  pause
  exit /b 1
)

echo Bilgi indeksi olusturuluyor...
%PY% -m ilim_assistant.ingest_cli
if errorlevel 1 (
  echo [HATA] ingest basarisiz.
  pause
  exit /b 1
)

echo.
echo Kurulum tamam. Simdi "Ruzgar_Baslat.bat" dosyasina cift tiklayin.
echo Ollama calismiyorsa once: ollama serve  ve  ollama pull llama3.2:3b
pause
