# Ana Motor — Süper Beyin Planı (2026-05-20)

> **Hedef:** Ümit abi'nin tüm sorularına dürüst, kaynaklı, güncel ve tam cevap — tek beyin: Ana Motor + Süper Beyin zinciri.

## Bugün (Faz A — uygulandı / uygulanıyor)

| # | Görev | Dosya | Etki |
|---|--------|-------|------|
| A1 | Ansiklopedik soruda **RAG atlama kaldırıldı** | `main_engine.py` | «Kim kurdu» vb. yerel arşiv+indeks hızlı tur, sonra Gemini |
| A2 | **Numaralı kaynak blokları** | `ana_motor_kaynak.py`, `chat_core.py` | Model [K1][K2] ile bağlama bağlanır |
| A3 | **Süper beyin talimatı** | `ana_motor_super.py` | Bilgi/ilim/tarih: tam cevap + güven satırı |
| A4 | **Cevap kalite geçidi** | `ana_motor_reflection.py` | Kaynak yoksa dürüst uyarı; kısa cevap uyarısı |
| A5 | Smoke + env | `ana_motor_smoke.py`, `RUZGAR_BRAIN.env.example` | Regresyon koruması |

## Faz B — uygulandı (2026-06-10)

| # | Görev | Dosya | Durum |
|---|--------|-------|--------|
| B1 | Çok kaynaklı sentez turu | `ana_motor_sentez.py`, `chat_core.py` | Yerel+web → hızlı model özeti |
| B2 | Self-reflection (9.6) | `ana_motor_reflection.py` | Kaynak ↔ cevap uyumu; «emin değilim» |
| B3 | `genel` modda bilgi planı | `ana_motor_plan.py` | Kısa sorularda `bilgi` + web varsayılan |
| B4 | Programlama → merkezi havuz | `ana_motor_programlama_havuz.py`, `desktop_server.py` | `motor_kv` + `publish_shared` |

## Faz C — uygulandı (2026-06-10)

| # | Görev | Dosya | Durum |
|---|--------|-------|--------|
| C1 / 9.1 | Birleşik araştırma raporu | `ana_motor_arastirma.py`, `chat_core.py` | [Y#] + web envanter kartı |
| C2 / 9.4 | Güncellik damgası | `ana_motor_guncellik.py`, `web_tools.py`, `reflection` | Web bağlam + cevap sonu |
| C3 / 8 | Bilgi beyin zinciri | `llm_brain.py` | Süper beyin açıkken Gemini önce |
| C4 / 12 | Canlı smoke + SLO | `ana_motor_smoke.py --live` | Health + bilgi turu süresi |

## Faz D — uygulandı (2026-06-10)

| # | Görev | Dosya | Durum |
|---|--------|-------|--------|
| D1 / 9.3 | Bilim/tarih derin mod | `ana_motor_bilim_derin.py`, `main_engine.py`, `chat_core.py` | Arşiv öncelik + yüksek RAG |
| D2 / 8 | 70B yerel profil | `llm_brain.py` | `denge70` / `RUZGAR_BRAIN_PROFILE=denge-70b` |
| D3 / 10 | Otonom debug köprüsü | `ana_motor_otonom_debug.py`, `desktop_server.py`, `programlama_faz10.py` | Genel→prog + pytest döngüsü |

## Faz E — uygulandı (2026-06-10)

| # | Görev | Dosya | Durum |
|---|--------|-------|--------|
| E1 | Bilim derin canlı SLO | `ana_motor_smoke.py --live` | `RUZGAR_LIVE_BILIM_DERIN_SLO_SEC` |
| E2 | 70B hazırlık kontrolü | `llm_ollama.py`, `llm_brain.py`, health | `denge70_ready` + pull uyarısı |
| E3 | Patch onay köprüsü + UI kart | `ana_motor_patch_bridge.py`, `app.js` | Delege/debug → staging |
| E4 | Nebula/tarih araştırma kartı | `ana_motor_arastirma.py`, dashboard | Külliyat envanteri |
| E5 | Canlı retrieval + progress | `stream_orchestra.py`, `app.js` | ETA + faz ikonları |

## Faz F — uygulandı (2026-06-10)

| # | Görev | Dosya | Durum |
|---|--------|-------|--------|
| F1 | Sürük-bırak dosya ingest | `ana_motor_dosya_ingest.py`, `app.js` | `POST /api/ana-motor/upload-context` |
| F2 | Nebula otomatik öneri | `ana_motor_nebula_oneri.py`, dashboard kart | düşük Güven → koleksiyon |
| F3 | TDK + tarih + nebula matris | `ana_motor_kaynak_matrisi.py`, `rag_store.py` | `search_tdk_hafiza` / `search_nebula_hafiza` |

## Faz G — uygulandı (2026-06-10)

| # | Görev | Dosya | Durum |
|---|--------|-------|--------|
| G1 | Canlı upload + matris SLO | `ana_motor_smoke.py --live` | `RUZGAR_LIVE_UPLOAD_MATRIS_SLO_SEC` |
| G2 | Nebula tek tık kaynak ekle | `ana_motor_nebula_apply.py`, `app.js` | `POST /api/ana-motor/nebula-oneri/apply` |
| G3 | Çoklu dosya oturum paketi | `ana_motor_dosya_ingest.py` | `session_id` + `ana_motor_session_id` |

## Faz H — uygulandı (2026-06-10)

| # | Görev | Dosya | Durum |
|---|--------|-------|--------|
| H1 | Nebula apply arka plan indeks | `ana_motor_nebula_apply.py`, `app.js` | `GET /api/ana-motor/nebula-apply/status` |
| H2 | Oturum → hafıza köprüsü | `ana_motor_session_hafiza.py` | `POST /api/ana-motor/session/remember` |
| H3 | Upload virüs taraması | `ana_motor_dosya_ingest.py` | `RUZGAR_ANA_UPLOAD_VIRUS_SCAN` |

## Sıradaki (Faz I — öneri)

- Nebula/hatırla birleşik «tek paket» sihirbazı
- Oturum TTL uzatma + kalıcı arşiv klasörü
- Canlı H1 indeks SLO

## Ortam (özet)

```env
GOOGLE_GEMINI_API_KEY=...          # Süper beyin için şart (ücretsiz kota)
RUZGAR_SUPER_BRAIN=1
RUZGAR_ANA_MOTOR_PLAN=1
RUZGAR_FAZ9_GEMINI_FIRST_FOR_FACTS=1   # Artık = hızlı yerel merge, RAG atlama yok
RUZGAR_ANA_MOTOR_REFLECTION=1
RUZGAR_ANA_MOTOR_SUPER_DIRECTIVE=1
ENABLE_WEB_SEARCH=1
```

## Başarı ölçütü

1. Ansiklopedik soru → yerel kaynak veya «yerel kaynak bulunamadı» + web/Gemini
2. Cevap sonunda **Güven:** satırı (yüksek/orta/düşük)
3. `python scripts/ana_motor_smoke.py` yeşil
4. Ümit abi: «bilmiyorum» yerine ya kaynaklı cevap ya dürüst sınır

*Bismillah — Ümit & Gökçenur*
