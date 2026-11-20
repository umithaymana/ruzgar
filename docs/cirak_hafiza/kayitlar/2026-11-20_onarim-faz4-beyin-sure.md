# 2026-11-20 — onarim-faz4-beyin-sure

## 1) Emir
Mimar Ümit: Faz 4 — umed vs ILIM_RAG_CLOUD_FIRST tek tablo; prefetch bütçe; classifyChatError dili.

## 2) Sonuç
İlim cloud-first varsayılan kapalı (local-first); prefetch t0 ile bütçe; UI hata dili umed/Ollama.

## 3) Doğru
- RUZGAR_ILIM_RAG_CLOUD_FIRST=1 yalnız açık bayrakla bulut önce.
- Prefetch süresi bütçeden düşer.

## 4) Yanlış
- Eskiden cloud-first=1 varsayılan umed’i eziyordu; bütçe prefetch sonrası sıfırlanıyordu.

## 5) Nerede
- Dal: cursor/ruzgar-onarim-fazlari-9eeb
- Commit: 66a6aaa17
- Dosyalar: ruzgar_genel_faz90.py, ruzgar_umed_cevap_emri.py, ana_motor_faz59.py, desktop_server.py, app.js, tests/test_beyin_sure_faz4.py

## 6) Nasıl uygula
1. Karar tablosu brain_order_decision_table.
2. begin_*_budget(started_monotonic=prefetch_t0).
3. classifyChatError local-first dili.

## 7) Tuzaklar
Colab kurulumları cloud-first=1 ile geri açılır.

## 8) Çözüm
Varsayılan 0 + prefetch t0 + UI metin.

## 9) Bir daha yapma
Bütçeyi prefetch bitince yeniden full başlatma.

## 10) Anahtarlar
`umed`, `local-first`, `prefetch`, `timeout`, `faz4`, `onarim`

## 11) Durum
`hazir`

---
## El rahatlatma
### Giriş kapısı
`ruzgar_genel_faz90.brain_order_decision_table`
### Hazır komutlar
```bash
cd ilim-assistant && python3 -m pytest tests/test_beyin_sure_faz4.py -q
```
### Dokunma
Büyük prompt rewrite yok
### Beklenen çıktı
3 test yeşil; cloud_first default False
### Bilinen kırık
—
### İlk güvenli adım
ilim_rag_cloud_first_enabled() is False
### Kapsam sınırı
Faz 4
### Geri alma
revert; veya env=1
