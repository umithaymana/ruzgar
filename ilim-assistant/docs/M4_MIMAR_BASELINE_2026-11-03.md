# M4 — Mimar motor baseline + mühür — 2026-11-03

`ses-m4-mimar-baseline-v1-2026-11-03`

## Ölçüm

| Parça | Durum |
|-------|--------|
| Atölye niyet (çiz / sanat / foto restore / kopya) | ✓ |
| Anlık: yardım + sekme aç | ✓ |
| Hub: atölye → mimar · nedir → genel | ✓ |
| Alt modül capabilities (foto/sanat/tasarım) | ✓ |
| API routes (parse + sketch + restore) | ✓ |
| Motor context (mimar arşiv yolları) | ✓ |

## Derin yama

1. **Foto restore:** `restore` / `duzelt` / `yenile` / `eski foto` → restorasyon paneli; `fotografı` kök eşlemesi.
2. **Bilgi ayrımı:** «fotoğraf nedir» atölye değil (parse `None`).
3. **Hub erken rota:** atölye niyeti registry’den önce mimar; `_hub_stay_on_ana_motor` bilgi kaçışını korur.

## Smoke

`scripts/smoke_m4_mimar.py` · `mimar_faz5_smoke.py` · `mimar_atolye_smoke.py`

## Sonraki

**Faz M mühür** (M1–M4 tamam).
