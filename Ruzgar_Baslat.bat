@echo off
chcp 65001 >nul
title RUZGAR — baslat (masaustu + API 8779)
cd /d "%~dp0"
REM Masaustu kisayolu: Masaustune_RUZGAR_Ikon.bat (bir kez) -> RUZGAR.lnk cift tik
REM Kisayol arka planda RuzgarLauncher.vbs calistirir (cmd penceresi yok).
echo.
echo RUZGAR: Electron + API http://127.0.0.1:8779
echo (Eski Gradio 7861 kullanilmiyor.)
echo.
wscript //B //nologo "%~dp0RuzgarLauncher.vbs"
exit /b 0
