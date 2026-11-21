# S3 — Klon yolu (BUSENAZ + kuran) — 2026-11-21

`ses-s3-klon-yolu-v1-2026-11-21` · plan: `RUZGAR_SES_VIDEO_TAVAN_PLAN_2026-11-21.md`

**S3 yeşil:** EVET  
**XTTS canlı:** EVET  

XTTS hazır — auto+klon_onay ile BUSENAZ / kuran klon yolu açık.

## Referanslar

| Profil | Dosya |
|--------|-------|
| muhabbet (BUSENAZ) | `BUSENAZ ses.wav` |
| alim | `BUSENAZ ses.wav` |
| tilavet | `kuran.wav` |
| kuran WAV | `kuran.wav` |

- busenaz_ok: True · tilavet_kuran_ok: True
- klon_onay: True · xtts: True · edge: True
- Edge yedek sözleşme: True
- klon_canli: True

**Canlı kanıt:** `arsiv/ses-referans/_s3_busenaz_smoke.wav` (BUSENAZ XTTS).

**A3:** XTTS canlı YEŞİL · Fish/F5 ayrı (yoksa KISMI, A3 ile karıştırma).

## Davranış

1. `backend=auto` + `klon_onay` + XTTS → BUSENAZ / kuran klon
2. XTTS yok veya klon hata → **Edge yedek** (S1/S2 profil parametreleri)
3. `RUZGAR_TTS_CLONE_STRICT=1` → yedek yok, 503

## Araçlar

- `ilim_assistant/ses_s3_klon_yolu.py`
- `scripts/smoke_s3_ses_klon_yolu.py`

## Sonraki

**S4 tamam** — V1 video dublaj veya kulak turu.

*Ümit & Gökçenur Haymana'nın ortak projesi.*
