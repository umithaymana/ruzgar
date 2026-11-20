# 2026-11-20 — onarim-faz1-anlik-kapi

## 1) Emir
Mimar Ümit: ONARIM PLANI Faz 1 — anlık kapı orkestrası (çift blok birleştir, registry, covers sıkı, hadis tek politika).

## 2) Sonuç
desktop_server çift anlık kütüphane zinciri tek registry’ye indirildi; `instant_covers` tek-token gevşekliği kalktı; bilgi/karşılaştır/anlat → RAG; hadis_anlik + hadis_kutuphane aynı defer politikası.

## 3) Doğru
- Derin niyetlerde kart yok → RAG/çok kaynak yolu açılır.
- Numaralı matın (`buhari 1`) anlık kalır.
- Tek registry = tek bakım noktası.

## 4) Yanlış
- Eskiden `kutup_hard` iken `should_defer` atlanıyordu; `len(toks)<=1 → True` anlat’ı kartlıyordu.
- «niyet hadisi nedir» sabit kart RAG’i çalıyordu.

## 5) Nerede
- Dal: `cursor/ruzgar-onarim-fazlari-9eeb`
- Commit: ede5cbce0
- Dosyalar:
  - `ilim_assistant/ruzgar_library_instant_registry.py`
  - `desktop_server.py`
  - `ruzgar_kutuphane_gorev.py`, `ruzgar_hadis_anlik.py`, `ruzgar_hadis_kutuphane.py`
  - `ruzgar_anlik_niyet_gate.py`
  - `tests/test_anlik_kapi_orkestra.py`

## 6) Nasıl uygula (benzer işte)
1. Yeni raf eklerken yalnız `LIBRARY_INSTANT_ENTRIES` güncelle.
2. Derin niyet → `forces_library_rag`; covers’a güvenme.
3. Hadis için anlik + kutuphane aynı kapıyı paylaşsın.
4. Unit: niyet nedir / karşılaştır / anlat → None.
5. desktop_server’a ikinci zincir ekleme.

## 7) Tuzaklar
- `is_strict_library_lookup("niyet hadisi nedir")` True olabilir — niyet+hadis istisnası şart.
- Çift import döngüsü: registry forces içinde lazy import kullan.

## 8) Çözüm
`forces_library_rag` + sıkı covers + tek `try_library_instant_from_registry` + ikinci zincir silindi.

## 9) Bir daha yapma
desktop_server’a aynı try_* raf zincirini ikinci kez yapıştırma.

## 10) Anahtarlar
`anlik`, `registry`, `instant_covers`, `hadis`, `RAG`, `faz1`, `onarim`

## 11) Durum
`hazir`

---

## El rahatlatma

### Giriş kapısı
`ilim_assistant/ruzgar_library_instant_registry.py`

### Hazır komutlar
```bash
cd ilim-assistant && python3 -m pytest tests/test_anlik_kapi_orkestra.py tests/test_cok_kaynak_sentez.py -q
```

### Dokunma
Yeni motor/UI/HIZIR; büyük prompt rewrite.

### Beklenen çıktı
24 ilgili test yeşil; niyet/karşılaştır/anlat anlık None.

### Bilinen kırık
Cloud ortamında Şamile indeksi yok — canlı RAG hit ayrı.

### İlk güvenli adım
`forces_library_rag("Niyet hadisi nedir?") is True`

### Kapsam sınırı
Faz 1 — selam/RAG diversify/motor yok.

### Geri alma
`git revert` bu commit; veya `LIBRARY_INSTANT_ENTRIES` eski zincire dönüş (önerilmez).
