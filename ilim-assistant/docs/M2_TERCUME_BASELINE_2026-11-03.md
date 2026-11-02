# M2 — Tercüme motor baseline + mühür — 2026-11-03

`ses-m2-tercume-baseline-v1-2026-11-03`

## Ölçüm

| Parça | Durum |
|-------|--------|
| SRT mock çeviri (zaman damgası korunur) | ✓ |
| Hub: çevir → tercume · nedir → genel | ✓ |
| API: srt / translate-chunk / pipeline / config | ✓ |
| Workbench config | ✓ |

## Derin yama (`tercume_faz74`)

1. **Yönelme `-ya`:** `arapcaya` / `fransizcaya` hedef dil artık doğru (önce yanlışlıkla `en`).
2. **`ı` fold:** Türkçe ı → i (Fransızca eşlemesi).
3. **«Hello world turkceye cevir»:** fiilden önceki metin gövdesi çıkarılıyor.

## Smoke

`scripts/smoke_m2_tercume.py` · `tercume_srt_smoke` regresyon.

## Sonraki

**M3 Okuma**.
