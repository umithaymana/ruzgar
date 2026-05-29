# Blok J96 — masaüstü hızlı checklist (opsiyonel)
param(
    [string]$ApiBase = "http://127.0.0.1:8779"
)
$ErrorActionPreference = "Stop"
Write-Host "Rüzgar masaüstü checklist — $ApiBase"

try {
    $h = Invoke-RestMethod -Uri "$ApiBase/api/health" -Method Get -TimeoutSec 8
    Write-Host "[OK] Sunucu" $h.status
} catch {
    Write-Host "[FAIL] Sunucu — Ruzgar_TemizBaslat.bat veya Ruzgar_Sadece_Api.bat"
    exit 1
}

try {
    $m = Invoke-RestMethod -Uri "$ApiBase/api/ruzgar/ui-manifest" -Method Get -TimeoutSec 8
    Write-Host "[OK] Manifest Faz" $m.current_phase
} catch {
    Write-Host "[WARN] Manifest alınamadı"
}

try {
    $t = Invoke-RestMethod -Uri "$ApiBase/api/workspace/list?rel=ilim-assistant/arsiv" -Method Get -TimeoutSec 12
    $n = @($t.items).Count
    Write-Host "[OK] Arşiv listesi ($n öğe)"
} catch {
    Write-Host "[WARN] Arşiv listesi"
}

Write-Host "Manuel: Ctrl+Shift+R · Tercüme · Çevir · Hedefi kaydet"
Write-Host "Bkz. ilim-assistant/docs/RUZGAR_MASAUSTU_ONAYLI_DURUM.md"
