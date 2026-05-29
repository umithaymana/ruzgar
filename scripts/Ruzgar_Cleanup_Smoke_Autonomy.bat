@echo off
chcp 65001 >nul
title RUZGAR — smoke-autonomy temizlik
cd /d "%~dp0\.."
set "ILIM=%CD%\ilim-assistant"
cd /d "%ILIM%"
if /I "%~1"=="dry" (
  python scripts\cleanup_smoke_autonomy.py --dry-run --days 7
) else (
  python scripts\cleanup_smoke_autonomy.py --days 7
)
exit /b %ERRORLEVEL%
