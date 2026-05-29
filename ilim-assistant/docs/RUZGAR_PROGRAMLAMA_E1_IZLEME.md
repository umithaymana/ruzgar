# Programlama E1 — canlı izleme (task-stats)

API ayaktayken (`Ruzgar_TemizBaslat.bat` → port **8779**).

## Hızlı sağlık

```powershell
curl -s http://127.0.0.1:8779/api/health
```

## Görev başarı istatistikleri (Faz 55)

```powershell
curl -s http://127.0.0.1:8779/api/programlama/task-stats
```

Örnek alanlar: `stats.e1_success_rate`, `stats.window_days`, `stats.total_tasks`, `report` (metin özet).

PowerShell ile okunaklı:

```powershell
(Invoke-RestMethod http://127.0.0.1:8779/api/programlama/task-stats).stats | Format-List
```

## Haftalık KPI (Faz 60)

```powershell
curl -s http://127.0.0.1:8779/api/programlama/weekly-kpi
```

## Bench (komut + otonomi gate)

```powershell
cd "d:\CURSOR PROJELER\YAPAY ZEKA"
.\scripts\Ruzgar_Programlama_Bench.bat
.\scripts\Ruzgar_Programlama_Bench.bat strict
```

Rapor: `scripts/ruzgar_programlama_upgrade_report.json`

## E1 hedef çizgisi

- Rolling pencere: 20–30 görev
- Hedef: **%90+** `e1_success_rate` (Blok C’de UI kartı genişletilir)
