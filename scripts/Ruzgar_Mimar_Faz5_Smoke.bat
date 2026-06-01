@echo off
setlocal
cd /d "%~dp0.."
python "ilim-assistant\scripts\mimar_faz5_smoke.py"
if errorlevel 1 exit /b 1
python "ilim-assistant\scripts\mimar_atolye_smoke.py"
exit /b %ERRORLEVEL%
