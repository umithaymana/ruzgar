# Mimar Motoru — Faz 5 Planı

**Önkoşul:** Faz 4 (4F–4T) ✅ · smoke `mimar_atolye_smoke.py` ✅

**Hedef:** Kullanıcı Mimar sohbetinde doğal dille söyler → atölye işi yapılır (Cursor kadar serbest değil; motor API sınırları içinde).

---

## Faz 5 alt paketleri

| Kod | Konu | Açıklama |
|-----|------|----------|
| **5H** | Hub / ROK | `mimar` hub listesinde; `okuma`/`bilim` alias |
| **5C** | Sohbet → komut | `mimar_faz5.py` niyet: çiz / foto / sanat / tasarım |
| **5U** | UI köprü | Yan sohbet yanıtı veya `/mimar çiz …` → ilgili sekme + API |
| **5A** | Arşiv ayrımı | Görsel atölye ≠ `okuma_motoru` metin arşivi (uzun vadeli) |

---

## Uygulama sırası

1. **5H** — `ana_motor_hub_faz76`: mimar etiket + yönlendirme ✅
2. **5C** — `mimar_faz5.py` + smoke ✅
3. **5U** — `app.js` + `mimar-atolye.js`: niyet JSON → sekme/aksiyon ✅
4. **5A** — okuma arşiv API’lerini tercüme/okuma’da tut; mimar yalnız `mimar-*` arşivi

---

## Test

- `python ilim-assistant/scripts/mimar_faz5_smoke.py`
- Mimar modunda: «arsiv durumu» (ROK) · «ev planı çiz» (5U sonrası)
