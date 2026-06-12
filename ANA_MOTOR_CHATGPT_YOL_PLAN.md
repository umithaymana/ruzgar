# Ana Motor — ChatGPT Yol Haritası (E→J)

> **Hedef:** Tek sohbet, güvenilir yanıt, yerel bilgi üstünlüğü — ChatGPT'ye yakın günlük deneyim.
> **Mimar:** Ümit & Gökçenur · **2026-06-11**

## Uygulandı (bu tur)

| Faz | Modül | Özet |
|-----|--------|------|
| **E** | `ruzgar_hub_sse_faz_e.py` | Tüm hub motorları SSE; `motor_action` video köprüsü |
| **F** | `ruzgar_bilgi_hybrid.py` | Bulut hız + kısa RAG özeti |
| **G** | `ana_motor_oturum_ozet.py` | Export API + oturum özeti hafızası |
| **H** | `ana_motor_gorsel_sohbet.py` | Gemini vision + görsel upload |
| **I** | `app.js` + `styles.css` | `ruzgar-unified-face` sade genel mod |
| **J** | `ruzgar_akil_faz_j.py` | Önerilen beyin ortamı + health |

**Build:** `2026-06-11-ruzgar-chatgpt-yol-ej`

## Ortam

```env
RUZGAR_HUB_SSE_FAZ_E=1
RUZGAR_BILGI_HYBRID=1
RUZGAR_ANA_OTURUM_OZET=1
RUZGAR_ANA_GORSEL_SOHBET=1
GROQ_BILGI_MODEL=llama-3.1-8b-instant
RUZGAR_UMED_ILIM_BUDGET_SEC=38
```

## API

- `GET /api/ana-motor/chat-history/export`
- Health: `hub_sse_e`, `bilgi_hybrid_meta`, `gorsel_sohbet`, `akil_faz_j`

## Doğrulama

```bash
python scripts/ana_motor_smoke.py
.\Ruzgar.ps1 -ForceRestart
```

## Faz K — uygulandı (2026-06-11)

| # | Modül | Özet |
|---|--------|------|
| K1 | `ruzgar_canli_slo_faz_k.py` | S1–S10 SLO paketi (offline + `--live --slo-pack`) |
| K2 | `ruzgar_denge70_faz_k.py` | denge70 health + `Pull-RuzgarDenge70.ps1` |
| K3 | `ruzgar_sesli_tur_faz_k.py` | TTS bitince mikrofon yeniden dinler |

**Build:** `2026-06-11-ruzgar-canli-slo-faz-k`

```bash
python scripts/ana_motor_smoke.py --slo-pack
python scripts/ana_motor_smoke.py --live http://127.0.0.1:8779 --slo-pack
```

```env
RUZGAR_CANLI_SLO_FAZ_K=1
RUZGAR_SLO_PACK_MIN_PASS=8
RUZGAR_SESLI_TUR_FAZ_K=1
```

## Sıradaki

- SLO paketini CI’da gece koşusu
- Sürekli sesli tur VAD ince ayarı
- `denge70` otomatik zincir önceliği (RAM yeterliyse)

*Bismillah*
