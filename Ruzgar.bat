@echo off
REM cmd az gorunsun diye dogrudan VBS (tercihen masaustu kisayolu wscript ile)
cd /d "%~dp0"
wscript //B //nologo "%~dp0RuzgarLauncher.vbs"
exit /b 0
