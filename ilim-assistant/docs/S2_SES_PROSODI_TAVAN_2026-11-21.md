# S2 — Prosodi + tilavet/âlim parametre tavanı — 2026-11-21

`ses-s2-prosodi-tavan-v1-2026-11-21` · plan: `RUZGAR_SES_VIDEO_TAVAN_PLAN_2026-11-21.md`

**S2 yapı yeşili:** EVET  
**Kulak skoru:** _(Mimar — checklist aşağıda)_

## Parametre özeti

| Tavan | Rate | Durak çarpanı | Cümle durak ms | Hız üst | Huzur üst |
|-------|------|---------------|----------------|---------|-----------|
| muhabbet | -11% | 0.88 | 170 | 1.0 | 0.96 |
| alim | -36% | 1.22 | 525 | 0.86 | 0.8 |
| tilavet | -48% | 1.42 | 939 | 0.74 | 0.7 |

- Tilavet örnek rate/pitch: `-48%` / `-5Hz`
- Ayet durak ms: **5456**
- Pause ayrımı: True · Rate ayrımı: True

## Kulak checklist (Mimar)

- [ ] **muhabbet** — «Merhaba Ümit abi, nasılsın? Kısa bir muhabbet cümlesi.» → Doğal, robot değil, kısa durak
- [ ] **alim** — «Hadis-i şerifte buyurulur ki: Ameller niyetlere göredir.» → Vakur, tane tane, acele yok
- [ ] **tilavet** — «Rahmân ve Rahîm olan Allah'ın adıyla. Elhamdülillâhi rabbil âlemîn.» → Huşû, uzun nefes / vakıf hissi

## Araçlar

- `ilim_assistant/ses_s2_prosodi_tavan.py`
- `scripts/smoke_s2_ses_prosodi_tavan.py`
- Kapat: `RUZGAR_SES_S2=0`

## Sonraki

**S3** — klon: `BUSENAZ ses` + tilavet `kuran.wav` / Edge yedek.

*Ümit & Gökçenur Haymana'nın ortak projesi.*
