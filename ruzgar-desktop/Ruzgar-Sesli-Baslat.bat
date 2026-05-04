@echo off
chcp 65001 >nul
title Rüzgar — tek tikla (Ollama + API + pencere)
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Ruzgar.ps1"
