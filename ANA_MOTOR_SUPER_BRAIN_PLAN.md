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

## Faz I — uygulandı (2026-06-10)

| # | Görev | Dosya | Durum |
|---|--------|-------|--------|
| I1 | Tek paket sihirbazı (arşiv+TTL+hafıza+Nebula) | `ana_motor_paket_sihirbaz.py`, `app.js` | `POST /api/ana-motor/paket-sihirbaz` |
| I2 | Oturum TTL uzatma + kalıcı arşiv | `ana_motor_dosya_ingest.py` | `arsiv/ana_motor_uploads/{session_id}/` |
| I3 | Canlı Nebula indeks SLO | `ana_motor_smoke.py --live` | `RUZGAR_LIVE_NEBULA_INDEX_SLO_SEC` |

## Faz J — uygulandı (2026-06-10)

| # | Görev | Dosya | Durum |
|---|--------|-------|--------|
| J1 | Paket sihirbazı otomatik tetik | `ana_motor_paket_auto.py`, `app.js` | `RUZGAR_ANA_PAKET_AUTO` + `done.paket_auto` |
| J2 | Arşivden RAG geri yükleme | `ana_motor_dosya_ingest.py` | `POST /api/ana-motor/archive/restore` |
| J3 | Çoklu oturum birleştirme | `ana_motor_dosya_ingest.py` | `POST /api/ana-motor/sessions/merge` |

## Faz K — uygulandı (2026-06-10)

| # | Görev | Dosya | Durum |
|---|--------|-------|--------|
| K1 | Otomatik paket UI özet kartı | `ana_motor_paket_ozet.py`, `app.js` | `GET /api/ana-motor/paket-auto/status` → `summary_card` |
| K2 | Birleşik oturum Nebula önerisi | `ana_motor_nebula_oneri.py` | `POST /api/ana-motor/sessions/nebula-oneri` |
| K3 | Arşiv/upload TTL hatırlatıcısı | `ana_motor_arsiv_hatirlat.py` | `GET /api/ana-motor/archive/reminders` |

## Faz L — uygulandı (2026-06-10)

| # | Görev | Dosya | Durum |
|---|--------|-------|--------|
| L1 | Hatırlatıcı → tek tık paket | `ana_motor_reminder_wizard.py` | `POST /api/ana-motor/reminders/paket-sihirbaz` |
| L2 | Özet kartından Nebula apply | `ana_motor_paket_ozet.py` | `POST /api/ana-motor/paket-ozet/nebula-apply` |
| L3 | Oturum zaman çizelgesi | `ana_motor_oturum_timeline.py` | `GET /api/ana-motor/sessions/timeline` |

## Faz M — uygulandı (2026-06-10)

| # | Görev | Dosya | Durum |
|---|--------|-------|--------|
| M1 | Timeline tek tık restore/merge/paket | `ana_motor_timeline_actions.py` | `POST /api/ana-motor/timeline/apply` |
| M2 | Hatırlatıcı masaüstü/e-posta bildirimi | `ana_motor_hatirlat_bildirim.py` | `desktop_notifications` + opsiyonel SMTP |
| M3 | Paket geçmişi CSV | `ana_motor_paket_csv.py` | `GET /api/ana-motor/paket-history/export` |

## Faz N — uygulandı (2026-06-10)

| # | Görev | Dosya | Durum |
|---|--------|-------|--------|
| N1 | CSV'den toplu arşiv geri yükleme | `ana_motor_csv_restore.py` | `POST /api/ana-motor/paket-history/import-restore` |
| N2 | Bildirim tercih paneli (UI + JSON) | `ana_motor_bildirim_tercih.py`, `app.js` | `GET/POST /api/ana-motor/notify-prefs` |
| N3 | Paket geçmişi grafik özeti | `ana_motor_paket_grafik.py` | `GET /api/ana-motor/paket-history/summary` |

## Faz O — uygulandı (2026-06-10)

| # | Görev | Dosya | Durum |
|---|--------|-------|--------|
| O1 | CSV'den toplu paket sihirbaz | `ana_motor_csv_paket.py` | `POST /api/ana-motor/paket-history/import-paket` |
| O2 | Bildirim geçmişi paneli | `ana_motor_bildirim_gecmis.py` | `GET /api/ana-motor/notify-history` |
| O3 | Timeline filtre | `ana_motor_timeline_filtre.py` | `GET /api/ana-motor/sessions/timeline?event_type&session_id&since_days` |

## Faz P — uygulandı (2026-06-10)

| # | Görev | Dosya | Durum |
|---|--------|-------|--------|
| P1 | Paket geçmişi JSON/PDF | `ana_motor_paket_export.py` | `GET /api/ana-motor/paket-history/export-json` · `export-pdf` |
| P2 | Bildirim geçmişi temizle/dışa aktar | `ana_motor_bildirim_gecmis.py` | `POST /notify-history/clear` · `GET /notify-history/export` |
| P3 | Haftalık timeline özet kartı | `ana_motor_haftalik_ozet.py` | `GET /api/ana-motor/sessions/weekly-summary` |

## Faz Q — uygulandı (2026-06-10)

| # | Görev | Dosya | Durum |
|---|--------|-------|--------|
| Q1 | Haftalık özet bildirimi | `ana_motor_haftalik_bildirim.py` | `POST /sessions/weekly-summary/notify` |
| Q2 | Paket geçmişi karşılaştırma | `ana_motor_paket_karsilastir.py` | `GET /paket-history/compare` |
| Q3 | Timeline otomatik hatırla | `ana_motor_timeline_hatirla.py` | `POST /timeline/remember` · `/remember/batch` |

## Sıradaki (Faz R — öneri)

- Karşılaştırma grafiği (çift çubuk bu hafta/geçen hafta)
- Hatırla geçmişi paneli (son 20 timeline→hafıza)
- Haftalık özet otomatik zamanlayıcı (cron/poll)

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
