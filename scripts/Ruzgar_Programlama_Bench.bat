@echo off
chcp 65001 >nul
title RUZGAR — Programlama bench
cd /d "%~dp0\.."
set "ILIM=%CD%\ilim-assistant"
if not exist "%ILIM%\scripts\programlama_upgrade_runner.py" (
  echo HATA: programlama_upgrade_runner.py bulunamadi.
  exit /b 1
)
cd /d "%ILIM%"
echo.
echo Programlama upgrade gate calisiyor...
if /I "%~1"=="strict" (
  python scripts\programlama_upgrade_runner.py --strict
) else (
  python scripts\programlama_upgrade_runner.py
)
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo OK — rapor: %CD%\..\scripts\ruzgar_programlama_upgrade_report.json
) else (
  echo FAIL — exit %RC% ^(strict icin: Ruzgar_Programlama_Bench.bat strict^)
)
exit /b %RC%
