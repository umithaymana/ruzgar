# Ana Motor — Faz W Planı (2026-06-10)

> **Hedef:** Tek sohbetten gerçek iş yürütme — panel/sekme değiştirmeden backend sonuç dönsün.

## Faz W — uygulanıyor

| # | Görev | Dosya | API / davranış |
|---|--------|-------|----------------|
| W1 | Merkezi backend yürütme köprüsü | `ana_motor_backend_yurut.py` | `GET /api/ana-motor/backend-yurut` |
| W2 | Kısa metin çeviri (sohbet içi) | `ana_motor_tercume_yurut.py` | Hub + motor-dispatch |
| W3 | Video URL metadata (indirme yok) | `ana_motor_video_bilgi.py` | Hub öncesi `og_direct` |

### Entegrasyon

- `apply_genel_hub_routing` — delege öncesi `try_backend_before_delegate`
- `build_motor_dispatch_payload` — `execute_backend_motor` öncelikli
- `motor_kabiliyetleri.json` — video/tercüme `backend:*` dispatch

### Ortam

```env
RUZGAR_ANA_BACKEND_YURUT=1
RUZGAR_ANA_TERCUME_INSTANT=1
RUZGAR_ANA_TERCUME_INSTANT_MAX_CHARS=500
RUZGAR_ANA_VIDEO_URL_INFO=1
```

### Başarı ölçütü

1. «ingilizceye çevir: Merhaba» → sohbette çeviri (panel yok)
2. YouTube URL + bilgi → başlık/süre/kanal (indirme yok)
3. `ana_motor_smoke.py` Faz W yeşil

## Sıradaki (Faz X — öneri)

- Ajan 2.0: patch + pytest doğrulama döngüsü
- Çok turlu `RUZGAR_ANA_AGENT_MAX_TURNS` artırımı

*Bismillah — Ümit & Gökçenur*
