# Ana Motor — Faz Z Planı (2026-06-10)

> **Hedef:** Sohbet UX sadeleştirme, katlanır arşiv, motor rehberi (?), multi-hop RAG.

## Faz Z — uygulandı

| # | Görev | Dosya | Davranış |
|---|--------|-------|----------|
| Z1 | Sade sohbet composer | `index.html`, `app.js`, `styles.css` | Gelişmiş seçenekler katlanır |
| Z2 | Motor rehberi | `ana_motor_motor_rehberi.py`, `?` overlay | Aktif motora kaydırma |
| Z3 | Multi-hop RAG | `ana_motor_multihop.py`, `main_engine.py` | İkinci tur genişletilmiş sorgu |
| Z4 | Katlanır arşiv kartı | `index.html`, `app.js` | Varsayılan kapalı, localStorage |

### API

`GET /api/ana-motor/motor-rehberi`

### Ortam

```env
RUZGAR_ANA_CHAT_SIMPLE=1
RUZGAR_ANA_ARCHIVE_FOLD=1
RUZGAR_ANA_MOTOR_REHBERI=1
RUZGAR_ANA_MULTIHOP_RAG=1
RUZGAR_ANA_MULTIHOP_EXTRA_K=2
```

### Başarı ölçütü

1. Composer’da yalnız Web + Sesli yanıt görünür; gelişmiş katlanır
2. Dashboard arşiv kartı kapalı başlar
3. `?` açılınca aktif motor bölümüne kayar
4. Smoke Faz Z yeşil

## Sıradaki (Faz AA — öneri)

- Sohbet geçmişi arama
- Nebula panel birleştirme

*Bismillah — Ümit & Gökçenur*
