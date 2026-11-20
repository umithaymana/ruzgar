# 2026-11-20 — Çırak hafıza deposu kurulumu

- **tarih:** 2026-11-20 (Europe/Istanbul)
- **branch:** `cursor/cirak-hafiza-9eeb`
- **durum:** hazir (bu kayıtla birlikte)
- **benzer_anahtarlar:** cirak-hafiza, protokol, apprentice-memory, playbook, lessons-learned

## is_ozeti

Ümit: «usta ile konuştuk, yaptım denmiş — bu oturumda görünmüyor.» Doğrulandı: **repoda / artifacts’ta ajan-çırak hafızası yoktu.** Şimdi `docs/cirak_hafiza/` altında gerçekten kuruldu.

## dogrulama (arama sonucu)

| Yer | Sonuç |
|-----|--------|
| `umithaymana/ruzgar` (GitHub code search: cirak hafıza, CIRAK_HAFIZA, apprentice memory, playbook, lessons) | **0** eşleşme (ajan hafızası) |
| `/cursor/stores` + artifacts | Parent’ta sentez/tutarlılık raporları var; **çırak hafıza klasörü yok** |
| `ilim-assistant/hafiza/` | Yalnız `bilge_gunluk.json` (günlük bilgi — ajan hafızası değil) |
| UI «çırak günlüğü» | Tercüme/programlama paneli — **farklı şey** |

Dürüst sonuç: önceki «yapıldı» iddiası **bu repoda kanıtlanamadı**; bu turda kuruldu.

## dosyalar

- `docs/cirak_hafiza/CIRAK_HAFIZA_OKU.md`
- `docs/cirak_hafiza/INDEX.md`
- `docs/cirak_hafiza/kayitlar/*.md`
- `docs/cirak_hafiza/kayitlar.jsonl`

## tuzaklar

- Uygulama hafızası (`hafiza_motoru`, RAG, genel hafıza JSON) ile karıştırmak.
- Artifact yazıp repoya koymamak → sonraki oturumda yine «görünmüyor».
- «Yaptım» demek; INDEX + JSONL satırı olmadan.

## cozum

Kalıcı markdown + JSONL repo içinde; protokol: işlemeden oku → bitince 5–10 satır ekle.
