# Ana Motor — Faz AB Planı (2026-06-13)

> **Hedef:** Sohbet oturumu JSON dışa aktarma + Kaynak panel tek tık Nebula apply.

## Faz AB — uygulandı

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AB1 | Oturum JSON export | `ana_motor_faz_ab.py`, `ana_motor_sohbet_gecmis.py` | Filtre: `session_id`, `mode` |
| AB2 | Birleşik Nebula apply | `ana_motor_faz_ab.py`, UI | Öncelik: öneri → paket özeti → yükleme |

### API

- `GET /api/ana-motor/chat-history/export?limit=&session_id=&mode=`
- `POST /api/ana-motor/kaynak-panel/birlesik-apply`
- `GET /api/ana-motor/kaynak-panel/status` → `faz_ab`

### Ortam

```env
RUZGAR_ANA_FAZ_AB=1
RUZGAR_ANA_SESSION_EXPORT=1
RUZGAR_ANA_KAYNAK_BIRLESIK_APPLY=1
```

### Başarı ölçütü

1. Sohbet arama çubuğunda **Dışa aktar** → `.json` indirilir
2. Kaynak panelde **Nebula'ya uygula** → öneri/özet/oturum tek akış
3. Smoke Faz AB yeşil

## Sıradaki (Faz AC — öneri)

- Canlı SLO gece koşusu doğrulama (sunucu açıkken)
- Sesli tur VAD kullanıcı ayar paneli
- denge70 pull otomasyonu (RAM yeterliyse)

*Bismillah — Ümit & Gökçenur*
