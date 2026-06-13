# Ana Motor — Faz AG Planı (2026-06-13)

> **Hedef:** Sohbet paneli temizle (UI + sunucu) + SLO birleşik özet kartı.

## AG1 — Sohbet temizle ✅

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AG1a | jsonl temizle | `ana_motor_sohbet_gecmis.py` | `clear_chat_history` |
| AG1b | AG köprü | `ana_motor_faz_ag_sohbet_temiz.py` | Sunucu + UI entegrasyonu |
| AG1c | API | `desktop_server.py` | `POST /api/ana-motor/chat-history/clear` |
| AG1d | UI | `index.html`, `app.js` | **Sohbeti temizle** — yalnızca ekran; arşiv korunur |
| AG1e | API (isteğe bağlı) | `POST …/chat-history/clear` | Yönetici / ileri kullanım — varsayılan UI çağırmaz |

### Ortam

```env
RUZGAR_SOHBET_TEMIZ=1
```

## AG2 — SLO birleşik özet ✅

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AG2a | Özet motor | `ana_motor_faz_ag_slo_ozet.py` | trend + aksiyon + son skor |
| AG2b | API | `desktop_server.py` | `GET /api/ana-motor/slo-pack/ozet` |
| AG2c | UI | `app.js` | SLO panelinde özet satırı |

### Ortam

```env
RUZGAR_SLO_OZET=1
```

*Bismillah — Ümit & Gökçenur — Faz AG tamam*
