# 05:30 gece işi — bge-m3 indir + Şâmile yan gömme. Canlı MiniLM indeksine dokunmaz.
$ErrorActionPreference = "Continue"
$ia = "D:\ÜMİT\PROJELER\CURSOR PROJELER\YAPAY ZEKA\ilim-assistant"
Set-Location $ia
$py = "D:\ÜMİT\14-) PROGRAMLAR\venvs\ruzgar\Scripts\python.exe"
& $py -u "$ia\scripts\bge_m3_gece.py"
exit $LASTEXITCODE
