@echo off
chcp 65001 >nul
title RUZGAR — tarayici API adresi temizligi
echo.
echo Eski Colab/yanlis API adresi siliniyor (localStorage)...
start "" "http://127.0.0.1:8779/ui/index.html?clearApi=1"
echo.
echo Tarayicida acildi. Sonra Ctrl+Shift+R (sert yenile) yapin.
echo.
pause
