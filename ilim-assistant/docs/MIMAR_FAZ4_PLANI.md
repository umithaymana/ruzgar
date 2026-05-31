# Mimar Motoru — Faz 4 Planı

**Onay çerçevesi (Ümit abi):** Mimar motoru içinde **3 bağımsız sayfa** — ortak yan sohbet, farklı backend alt-modülleri.

| Sekme | Sayfa adı | Amaç |
|--------|-----------|------|
| 1 | **Fotoğraf** | Fotoğraf stüdyosu |
| 2 | **Resim · Sanat** | Sanat galerisi |
| 3 | **Tasarım** | Çizim ve mimari |

---

## Mimari ilke

```
Mimar Motoru (UI kabuğu + ortak sohbet)
├── mimar_fotograf/     ← bağımsız API + iş kuyruğu
├── mimar_sanat/        ← bağımsız API + galeri deposu
└── mimar_tasarim/      ← bağımsız API + tuval/vektör
```

- Tercüme, Ses, Video, Programlama motorlarına **dokunulmaz**.
- Ana motor hub: yalnızca `mode=mimar` yönlendirmesi + handoff metni.
- Her alt sayfa kendi `mimar_*_faz*.py` modülü ile büyür.

---

## Sayfa 1 — Fotoğraf

### Yetenekler (sıra)

| Kod | Özellik | Faz 4 alt | Teknik not |
|-----|---------|-----------|------------|
| **4F-a** | Profesyonel fotoğraf moderasyonu | 4F-1 | Kırp, döndür, exposure, renk; PIL/OpenCV + onaylı preset |
| **4F-b** | Eski fotoğraf düzenleme / yenileme | 4F-2 | Scratch removal, upscale (lokal model veya API); önce önizleme |
| **4F-c** | Yapay ses: metin okutma, konuşturma | 4F-3 | Mevcut Edge-TTS / ses motoru köprüsü; fotoğraf OCR → metin → TTS |

### UI (tamamlandı — iskelet)
- Sol: küçük thumbnail şeridi
- Orta: büyük önizleme
- Alt: Moderasyon · Restorasyon · Metin oku · Konuştur

### Backend hedef dosyalar
- `ilim_assistant/motorlar/mimar_fotograf.py`
- `desktop_server.py` → `/api/mimar/fotograf/*`

---

## Sayfa 2 — Resim · Sanat

### Yetenekler

| Kod | Özellik | Faz 4 alt | Teknik not |
|-----|---------|-----------|------------|
| **4S-a** | Profesyonel sanat galerisi | 4S-1 | Grid + metadata (sanatçı, dönem, teknik) JSON |
| **4S-b** | Eser tanıma | 4S-2 | Vision LLM / Gemini görsel; «bu eser nedir?» |
| **4S-c** | Çizebilme / eskiz | 4S-3 | Referans üzerine katman; SVG export |
| **4S-d** | Kopya çıkarma | 4S-4 | Stil transfer veya trace (ileride genişler) |

### UI (tamamlandı — iskelet)
- Sol: galeri grid
- Sağ: büyük eser önizleme + Tanı · Çiz · Kopya + not alanı

### Backend
- `ilim_assistant/motorlar/mimar_sanat.py`
- Galeri: `ilim-assistant/arsiv/mimar-sanat/` (veya merkezi bellek köprüsü)

---

## Sayfa 3 — Tasarım

### Yetenekler

| Kod | Özellik | Faz 4 alt | Teknik not |
|-----|---------|-----------|------------|
| **4T-a** | Verilen resim/fotoğraf/cisimden çizim | 4T-1 | Referans görsel → vektör/eskiz (vision + çizim pipeline) |
| **4T-b** | Sohbet veya konuşma ile betimleme → çizim | 4T-2 | Chat handoff + `mimar_tasarim` prompt; tuval güncelleme |
| **4T-c** | Kayıtlı yapı ve mimari çizimi | 4T-3 | Proje arşivi; daha önce kaydedilen planları yeniden aç/üret |

### UI (tamamlandı — iskelet)
- Üst: Resimden çiz · Sohbetten çiz · Kayıtlı mimari · Referans
- Orta: canvas tuval
- Sağ: katmanlar + not

### Backend
- `ilim_assistant/motorlar/mimar_tasarim.py`
- Proje kayıt: `ilim-assistant/arsiv/mimar-tasarim/*.json` + PNG/SVG

---

## Uygulama sırası (öneri)

1. **4.0** — Panel görünürlük düzeltmesi + 3 farklı UI iskeleti ✅ (bu commit)
2. **4F-1** — Fotoğraf: yükleme + moderasyon (kırp/döndür/kaydet) ✅
3. **4F-2** — Restorasyon (soluk/çizik/gürültü/2×/tam + önizleme) ✅
4. **4F-3** — OCR + TTS köprüsü (ses motoru) ✅
5. **4S-1** — Galeri metadata + eser tanıma ✅
6. **4T-1** — Canvas çizim API + sohbetten betimleme ✅
7. **4S-2** — Detaylı eser tanıma (Gemini rapor) ✅
8. **4S-3** — Referans üzerine eskiz katmanı + SVG ✅
9. **4S-4** — Stil kopya (trace / poster / pencil) ✅
10. **4T-2** — Sohbet handoff → tuval ✅
11. **4T-3** — Kayıtlı mimari yenileme, kopya, PNG ✅

---

## Test checklist

- [ ] Mimar → yalnız **bir** sekme görünür (üçü üst üste değil)
- [ ] Fotoğraf / Sanat / Tasarım görsel olarak birbirinden farklı
- [ ] Yan sohbet her sekmede açık
- [ ] Fotoğraf: dosya ekle → önizleme
- [ ] Sanat: galeri tile → sağda büyük görünüm
- [ ] Tasarım: tuval yüklenir
- [ ] Motor değiştirince Tercüme/Programlama bozulmaz

---

## Not

Eski «İçerik / metin taslak» sayfası kaldırıldı; metin taslak ihtiyacı **Ana Motor** veya ileride ayrı not modülü ile karşılanabilir. Mimar Fotoğraf sekmesi artık görsel odaklıdır.
