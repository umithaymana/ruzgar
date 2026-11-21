# S0 — Ses tavanı ölçüm kartı — 2026-11-21

`ses-s0-tavan-olcum-v1-2026-11-21` · plan: `RUZGAR_SES_VIDEO_TAVAN_PLAN_2026-11-21.md`

## Başarı cümlesi

Kur’an’da huşû; hadis/tefsirde vakur; sohbette doğal; video aynı ses omurgası — mobil = PC.

## Özet

| Alan | Değer |
|------|-------|
| Yapı robot skoru (0–5) | **5.0** |
| Kulak skoru | _(Mimar — S1+)_ |
| Mobil eşitlik (sözleşme) | **YEŞİL** |
| Profil gap (tavan) | `muhabbet, tilavet` |
| TTS live first-byte | 1311.2 |
| S0 yeşil | **EVET** |

## Mühürlü referanslar (ezilmez)

| Ref | ms |
|-----|-----|
| V0 TTS first-byte | 1686.0 |
| V0 STT warm | 10288.0 |
| V3 ölçülen first-byte | 820.0 |
| V3 hedef üstü | 900.0 |
| Aşama D keep | 886.0 |

## Robot / yapı

Edge neural + prosody/tilavet iskelet var; tavan profil ayrımı (S1) ve klon referansı (S3) gelmeden robot hissi yüksek kalabilir.

```
{
  "ses_prosody": true,
  "ses_tilavet": true,
  "ses_klon_motoru": true,
  "ses_v3_ilk_byte": true,
  "ses_v4_barge_in": true,
  "ses_f7_kalite": true
}
```

## Profiller (şimdi → tavan)

- Mevcut Edge: `alim, asistan, edip`
- Tavan hedef: `muhabbet, alim, tilavet`
- Gap: `muhabbet, tilavet` → **S1**

## Mobil = PC

- Aynı `/api/tts`: True
- Desktop barge: True
- Mobil barge: True

## Klon / tilavet WAV

- Tilavet referans: `D:\ÜMİT\PROJELER\CURSOR PROJELER\YAPAY ZEKA\ilim-assistant\arsiv\ses-referans\kuran.wav`
- Mimar kilit: {"klon": "kız sesi (önceden alınmış) verilecek", "tilavet_wav": "şimdi yok — sonra"}

## Canlı TTS

- ran=True ok=True first_byte_ms=1311.2
- note: 

## Araçlar

- `ilim_assistant/ses_s0_olcum.py`
- `scripts/smoke_s0_ses_tavan.py`
- Canlı ölçüm: `RUZGAR_S0_LIVE=1`

## Sonraki

**S1** — üç profil seçici (muhabbet / âlim / tilavet) Edge üzerinde.

*Ümit & Gökçenur Haymana'nın ortak projesi.*
