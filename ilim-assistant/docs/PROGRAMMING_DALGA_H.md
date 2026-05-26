# Programlama motoru — Dalga H (zayıf nokta kapatma)

> **Build:** `faz78-v87` · **Tarih:** 2026-05-26

## Hedef

Yol haritası E1–E7 ve Cursor kıyasındaki tüm zayıf noktaları programlama motorunda kapatmak.

| Eksik | Faz | Çözüm |
|-------|-----|--------|
| E1 Offline ≠ canlı | **83** | `weakness-report` + canlı/parity köprüsü |
| E2 10+ dosya refactor | **80** | Mega refactor: 30 tur, 16 dosya/tur, 40 dk |
| E3 Groq’suz zayıf araç | **81** | Deterministik `@@write`/`@@read` kurtarma |
| E4 Ana Motor bağlam kopuk | **79** | Handoff v3 (git, hub, başarısız görevler) |
| E5 Git/PR yarım | **83** | `pr hazırla:` + gh komut önerisi |
| E6 Parity seyrek | **83** | Haftalık parity hatırlatıcı + rapor |
| E7 Build uyumsuz | **60** | expected_rev → v87 |
| Kapsam `projects/` only | **78** | `çekirdek:` / `ruzgara patch` → ilim-assistant + desktop |

## Komutlar

- `çekirdek durum` — çekirdek yazım kapsamı özeti
- `mega refactor: …` — uzun görev modu
- `pr hazırla:` — branch + commit + gh pr önerisi
- `zayıflık raporu` / `weakness report` — KPI + açık eksikler

## Kapatma

`RUZGAR_FAZ78=0` … `RUZGAR_FAZ83=0` (modül başına)
