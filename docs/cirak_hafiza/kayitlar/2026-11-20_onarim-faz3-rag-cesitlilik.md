# 2026-11-20 — onarim-faz3-rag-cesitlilik

## 1) Emir
Mimar Ümit: ONARIM PLANI Faz 3 — diversify sonrası dilim; lexical/usable gevşetme; test_cok_kaynak yeşil.

## 2) Sonuç
pack_k ile 3–5 eser dilimi; lexical Arapça köprü + skor 0.75; usable ikinci geçiş; yanlış MISS azaltıldı.

## 3) Doğru
- diversify sonrası `hits[:rag_k]` 2’ye düşürmesin — pack_k.
- Yüksek skor + 1 örtüşme usable.

## 4) Yanlış
- Eskiden usable false → good_hits=[] hemen MISS.

## 5) Nerede
- Dal: `cursor/ruzgar-onarim-fazlari-9eeb`
- Commit: d909a1dd4
- Dosyalar: `chat_core.py`, `ruzgar_kutuphane_gorev.py`, `tests/test_cok_kaynak_sentez.py`

## 6) Nasıl uygula
1. Dilim öncesi diversify; pack_k = max(rag_k, boost, min(5,n)).
2. Lexical’de expand_kutuphane_search_query.
3. usable false → ikinci geçiş / strong hits.

## 7) Tuzaklar
Peygamber/kimdir temizlik kurallarını bozma.

## 8) Çözüm
pack_k + ölçülü lexical + ikinci geçiş.

## 9) Bir daha yapma
usable false deyince tüm hit’leri silme.

## 10) Anahtarlar
`RAG`, `diversify`, `lexical`, `MISS`, `pack_k`, `faz3`, `onarim`

## 11) Durum
`hazir`

---
## El rahatlatma
### Giriş kapısı
`chat_core.py` diversify/pack_k bloğu
### Hazır komutlar
```bash
cd ilim-assistant && python3 -m pytest tests/test_cok_kaynak_sentez.py -q
```
### Dokunma
Faz 1–2 selam/registry
### Beklenen çıktı
test_cok_kaynak_sentez yeşil; ≥3 eser dilim
### Bilinen kırık
Şamile indeksi cloud’da yok
### İlk güvenli adım
library_rag_top_k_boost(2, «niyet…») ≥ 4
### Kapsam sınırı
Faz 3
### Geri alma
revert
