# Mühür — Sohbet sahne-kaçma + mobil kilit (2026-11-21)

**Karar:** Desktop fix mobilde eşitlendi. Genel sohbet sahneye kaçmaz.

## Ne mühürlü?

1. **Sunucu** `sahne_super_el.py` — osm/foto/tarihi yanlış eşleşme yok; organ tek başına show açmaz.
2. **Desktop** `app.js` + `ruzgar-masa.js` — niyet kapısı + guven&lt;0.72 + meta ortasında yüzey kayması yok.
3. **Mobil PWA** `static/mobil-pwa/app.js` — aynı niyet + guven; send/voice yalnız `looksLikeSahneCmd`.
4. **Ollama** tur bütçesi — ilk token tüm süreyi yutmaz (`llm_brain.py`).

## Smoke

- `scripts/smoke_sohbet_sahne_kacma.py`
- `scripts/smoke_mobil_sahne_kilit.py`

## Sırada

Ses yükselt (askıdan açıldı). Bu mühür bozulmadan üzerine ekle.
