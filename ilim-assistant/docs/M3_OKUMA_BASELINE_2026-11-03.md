# M3 — Okuma motor baseline + mühür — 2026-11-03

`ses-m3-okuma-baseline-v1-2026-11-03`

## Ölçüm

| Parça | Durum |
|-------|--------|
| Metin türü (hadis/gazel/tasavvuf/belirsiz) | ✓ |
| Arşiv anlık (`arsiv durum`) faz73 | ✓ |
| Hub: arşiv/kategori → mimar · nedir → genel | ✓ |
| Workspace read-text/pdf/ebook API | ✓ |
| Motor context | ✓ |

## Derin yama

1. **faz98:** `dosyayı oku …` artık programlama onay kapısına düşmez (salt okuma).
2. **Hub instant:** `okuma`→`mimar` map’inden **önce** `maybe_instant_faz73` (arsiv özeti kaybolmuyordu).
3. **Hub erken rota:** arşiv/kategori/kaynak niyeti → mimar.
4. **ı fold** okuma faz73’te; `metnin`/`turunu` categorize eşlemesi.
5. **Hub UnboundLocal:** tercüme dalındaki yerel `import INTENT_DO` kaldırıldı — bayrak kapalıyken okuma erken dönüşü `except` ile yutuluyordu.

## Smoke

`scripts/smoke_m3_okuma.py` · hub ince ayar regresyon.

## Sonraki

**M4 Mimar**.
