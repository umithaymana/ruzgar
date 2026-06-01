@echo off
setlocal
cd /d "%~dp0.."
python "ilim-assistant\scripts\mimar_atolye_smoke.py"
exit /b %ERRORLEVEL%
