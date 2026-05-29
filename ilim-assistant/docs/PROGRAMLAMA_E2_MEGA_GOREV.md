# E2 mega görev hedefi (Blok G70)

**Faz 80** · **E2** = uzun / çok dosyalı otonom görevlerde başarı oranı.

## Hedef

| Metrik | Varsayılan | Ortam |
|--------|------------|--------|
| E2 başarı oranı | **≥ %90** | `RUZGAR_E2_TARGET_RATE=0.90` |
| Mega tur | 30 | `RUZGAR_FAZ80_MAX_TURNS` |
| Dosya / tur | 16 | `RUZGAR_FAZ80_MAX_FILES` |
| Bütçe | 2400 sn | `RUZGAR_FAZ80_BUDGET_SEC` |

## Komutlar

```
mega refactor 10+ dosya
görev: projects/benim-api tüm modülleri pytest geçecek şekilde düzenle
```

## UI (atölye)

- **Mega görev** kartı — tur bütçesi, dosya/tur, E2 çizgisi
- **Dokunulan dosyalar** — `touched_files` listesi
- **Patch planı** — bekleyen yollar önizlemesi
- **Verify** — son doğrulama satırı
- **Görev devam** — yarım görevde aynı `görev:` cümlesi

## Ölçüm

- `GET /api/programlama/mega-workbench`
- `python scripts/programlama_mega_stress.py`
- Upgrade raporu `e2` / `rolling_20` (Faz 55)

## Parity (G66)

Tam parity full: `scenario_three_file_refactor` (8/8 full modda).  
Aylık: `PROGRAMLAMA_PARITY_AYLIK_TAKVIM.md`
