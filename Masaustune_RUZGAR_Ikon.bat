@echo off
chcp 65001 >nul
title RUZGAR - masaustu kisayolu
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Masaustune_Kisayol.ps1"
exit /b 0
