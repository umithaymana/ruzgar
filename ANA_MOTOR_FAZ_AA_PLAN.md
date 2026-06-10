# Ana Motor — Faz AA Planı (2026-06-10)

> **Hedef:** Sohbet geçmişi arama + birleşik Kaynak & Nebula paneli.

## Faz AA — uygulandı

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| AA1 | Sohbet geçmişi | `ana_motor_sohbet_gecmis.py` | jsonl kayıt + arama API |
| AA2 | Kaynak/Nebula panel | `ana_motor_kaynak_panel.py`, UI | Tek katlanır kart |

### API

- `GET /api/ana-motor/chat-history/recent`
- `GET /api/ana-motor/chat-history/search?q=`
- `GET /api/ana-motor/kaynak-panel/status`

### Ortam

```env
RUZGAR_ANA_CHAT_HISTORY=1
RUZGAR_ANA_KAYNAK_PANEL=1
RUZGAR_ANA_KAYNAK_PANEL_FOLD=1
```

### Başarı ölçütü

1. Sohbet üstünde arama çubuğu — balon vurgulama
2. Araştırma + Nebula tek panelde
3. Smoke Faz AA yeşil

## Sıradaki (Faz AB — öneri)

- Sohbet oturumu dışa aktarma (JSON)
- Nebula apply tek tık birleşik akış

*Bismillah — Ümit & Gökçenur*
