# S4 — Okuma bağ (raftan kısa pasaj sesle oku) — 2026-11-21

`ses-s4-okuma-bag-v1-2026-11-21` · plan: `RUZGAR_SES_VIDEO_TAVAN_PLAN_2026-11-21.md`

**S4 yeşil:** EVET  

Raftan eser → kısa pasaj → S1–S3 profil/prosodi/klon omurgası (`/api/tts`).

## Davranış

1. `POST /api/okuma/pasaj` — pasaj + karakter (TTS yok)
2. `POST /api/okuma/sesle` — pasaj + Edge/klon MP3 (FileResponse)
3. Aksiyonlar: `oku` · `devam` · `tekrar` · `yavas` · `husulu`
4. Masa + mobil aynı API (`mobil_ayni_api`)

## Demo

- Sorgu: `fotosentez` → eser `001_hucre_fotosentez` · karakter **alim**
- Başlık: Hücre ve fotosentez
- Pasaj önizleme: Hücre ve fotosentez Hücre Canlıların temel yapı birimidir. Prokaryot (çekirdeksiz) ve ökaryot (çekirdekli) ayrımı vardır…
- devam_ok: True · tekrar_ok: True

## Kulak checklist (Mimar)

1. Raftan kısa pasaj — âlim edası doğal mı?
2. Devam / tekrar aynı yerden mi?
3. Mobil + masa aynı pasaj / profil?

## Araçlar

- `ilim_assistant/ses_s4_okuma_bag.py`
- `scripts/smoke_s4_okuma_ses_bag.py`

## Sonraki

V1 — video dublaj omurga profili · veya kulak turu S0–S4

*Ümit & Gökçenur Haymana'nın ortak projesi.*
