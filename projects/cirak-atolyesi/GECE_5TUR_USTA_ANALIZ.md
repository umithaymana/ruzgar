# Usta analizi — Gece 5 tur

Tarih: 2026-11-18  
Mimar emri: 5 kademeli iş, kart yeşil olmadan ilerleme, teşhis/onarım, bitince commit+push.

## Özet
- Kart yeşil (disk + pytest): **5/5**
- Çırak LLM kendi yazdı (doğru spec): **4** (Tur 1–4)
- Spec sapması + usta düzeltme: **1** (Tur 5)
- Usta tam kurtarma şablonu (sıfırdan yazım): **0**

## Ne işe yaradı
1. **Yazım kapısı** (`cirak_no_write`): salt grep turu yeşil sayılmıyor.
2. **Dosya kapısı** (`cirak_missing_files`): hedef `.py` diskte yoksa “bitti” yok.
3. **Hedefli pytest**: runner sadece o turun test dosyasını çalıştırdı (atölye genel yalan yeşili azalır).

## Tur tur teşhis
| Tur | Sonuç | Teşhis |
|-----|-------|--------|
| 1 | LLM yeşil ~45sn | write+verify görüldü |
| 2 | 1. deneme: 21 tur grep, dosya yok → kırmızı; 2. deneme yazdı | Kapılar doğru çalıştı |
| 3 | LLM yeşil | Test biraz gevşek ama fonksiyon doğru |
| 4 | LLM yeşil | JSON sort_keys OK |
| 5 | LLM yanlış API (`filtrele_satir`); GOREV `filtre_satirlar` istiyordu | Runner pytest’i LLM’in kendi testine yeşil verdi — **kapı deliği**: davranış sözleşmesi (imza) yoktu. Usta GOREV’e çekti, pytest yeniden yeşil. |

## Kök risk (dürüst)
- Çırak artık daha çok **yazıyor**, ama bazen **yanlış şeyi** yazıp kendi testiyle kendini geçiriyor.
- Sonraki sıkılaştırma: GOREV’deki fonksiyon adını/imzayı smoke’ta assert et (yalnız dosya varlığı yetmez).

## Kapı kodu (bu gece)
- `programlama_faz34.py` v1.2 dosya kapısı
- `programlama_faz14.py` / `faz35.py` çırak yazım önce

## Dosyalar
- Plan: `GECE_5TUR_PLAN.md`, `GOREV_GECE_T1..T5.md`
- Log: `GECE_5TUR_LOG.jsonl`
- Runner: `_gece_5tur_runner.py`
