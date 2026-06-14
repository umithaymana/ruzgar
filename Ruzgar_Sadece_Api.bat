@echo off
chcp 65001 >nul
title RUZGAR — sadece API (Faz 98)
cd /d "%~dp0"
set RUZGAR_EXPECTED_BUILD_REV=2026-06-14-ruzgar-web-first-faz-ap2
echo Eski API durduruluyor...
py -3 "%~dp0ilim-assistant\scripts\ruzgar_port_ops.py" kill-all-api --port 8779
timeout /t 3 /nobreak >nul
echo API baslatiliyor...
cd /d "%~dp0ilim-assistant"
start "Ruzgar API" /MIN py -3 run_desktop_api.py --host 127.0.0.1 --port 8779
timeout /t 12 /nobreak >nul
echo.
echo Health kontrol:
py -3 -c "import urllib.request,json; d=json.load(urllib.request.urlopen('http://127.0.0.1:8779/api/health',timeout=5)); print('ok=',d.get('ok'),'rev=',(d.get('build')or{}).get('rev'))"
echo.
echo Tarayici: http://127.0.0.1:8779/ui/index.html
pause
