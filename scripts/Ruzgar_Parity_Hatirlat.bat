@echo off
chcp 65001 >nul
title RUZGAR — haftalik parity hatirlatma
cd /d "%~dp0\.."
echo.
echo === RUZGAR — Haftalik parity full (8/8) hatirlatma ===
echo.
echo Takvim: ilim-assistant\docs\PROGRAMLAMA_PARITY_AYLIK_TAKVIM.md
echo Gunluk bench: scripts\Ruzgar_Programlama_Bench.bat strict
echo.
echo Parity full calistirmak icin (ilim-assistant klasorunde):
echo   python scripts\ruzgar_parity_smoke.py
echo.
echo veya API acikken: POST /api/programlama/weekly-parity-full
echo.
pause
