# S1 — Ses tavanı üç profil (Edge) — 2026-11-21

`ses-s1-tavan-profil-v1-2026-11-21` · plan: `RUZGAR_SES_VIDEO_TAVAN_PLAN_2026-11-21.md`

## Yeşil koşul

Sohbette / API’de `karakter` = **muhabbet | alim | tilavet** (asistan→muhabbet).

**S1 yeşil:** EVET

## Profiller

| Tavan | Edge karakter | Voice | Rate | Pitch |
|-------|---------------|-------|------|-------|
| muhabbet | muhabbet | tr-TR-EmelNeural | -8% | +1Hz |
| alim | alim | tr-TR-AhmetNeural | -27% | -3Hz |
| tilavet | tilavet | tr-TR-AhmetNeural | -38% | -5Hz |

- Alias OK: True
- Rate/pitch ayrımı: True
- Aktif tavan: muhabbet (kayıt: muhabbet)

## Araçlar

- `ilim_assistant/ses_s1_tavan_profil.py`
- `scripts/smoke_s1_ses_tavan_profil.py`

## Sonraki

**S2** — prosodi + tilavet/âlim parametre tavanı (kulak onayı).

*Ümit & Gökçenur Haymana'nın ortak projesi.*
