@echo off
REM API (8777) + tarayici Gradio (7861) + Electron masaustu — tek tikla hepsi
chcp 65001 >nul
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Ruzgar.ps1" -WithGradio
exit /b %ERRORLEVEL%
