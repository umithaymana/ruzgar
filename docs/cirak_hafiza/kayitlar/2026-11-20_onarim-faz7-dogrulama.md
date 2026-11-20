# 2026-11-20 — onarim-faz7-dogrulama

## 1) Emir
Mimar Ümit: Faz 7 — smoke + doğrulama notu; plan uygulama durumu tablosu.

## 2) Sonuç
37 pytest yeşil; 9 senaryo smoke geçti; indeks sınırlı işaretlendi; ONARIM_DOGRULAMA + plan durumu yazıldı.

## 3) Doğru
İndeks yoksa MISS ayrı işaretlenir; unit smoke kapıları mühürler.

## 4) Yanlış
—
## 5) Nerede
- Dal: cursor/ruzgar-onarim-fazlari-9eeb
- Commit: 3fdef95a6
- Dosyalar: docs/RUZGAR_ONARIM_DOGRULAMA.md, docs/RUZGAR_ONARIM_PLANI.md
- Artifact: /opt/cursor/artifacts/RUZGAR_ONARIM_DOGRULAMA.md

## 6) Nasıl uygula
1. pytest paketleri
2. Kapı smoke (niyet/karşılaştır/anlat/selam)
3. İndeks notu
4. Plan tablosu güncelle

## 7) Tuzaklar
Ollama yoksa zincir buluta düşer — local-first bayrağı yine doğru.

## 8) Çözüm
Kanıt listesi + indeks ayrımı.

## 9) Bir daha yapma
İndeksiz ortamda «RAG kırık» deme.

## 10) Anahtarlar
`dogrulama`, `smoke`, `faz7`, `onarim`, `indeks`

## 11) Durum
`hazir`

---
## El rahatlatma
### Giriş kapısı
docs/RUZGAR_ONARIM_DOGRULAMA.md
### Hazır komutlar
```bash
cd ilim-assistant && python3 -m pytest tests/test_anlik_kapi_orkestra.py tests/test_sohbet_tutarlilik.py tests/test_cok_kaynak_sentez.py tests/test_beyin_sure_faz4.py tests/test_motor_routing_faz5.py -q
```
### Dokunma
—
### Beklenen çıktı
37 passed + doğrulama md
### Bilinen kırık
Şamile tam indeks yok
### İlk güvenli adım
forces_library_rag('Niyet hadisi nedir?')
### Kapsam sınırı
Faz 7
### Geri alma
—
