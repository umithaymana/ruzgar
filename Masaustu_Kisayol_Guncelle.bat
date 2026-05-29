@echo off
chcp 65001 >nul
title RUZGAR — masaustu kisayol guncelle
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Masaustune_Kisayol.ps1"
