# Çırak Hafıza — Protokol (okumadan işe başlama)

**Mimar emri (Ümit):** Çırak her işin ince detayını buraya kaydeder; yeni işe başlamadan önce buraya bakar; benzer geçmiş işi rehber alır.

Bu klasör **Cursor ajan / çırak** içindir. Uygulama içi «çırak günlüğü» (tercüme/programlama UI) veya `ruzgar_genel_hafiza.json` ile karıştırma.

---

## 1) İşe başlamadan (zorunlu)

1. Bu dosyayı oku.
2. `INDEX.md` içinde anahtar kelimelerle benzer kayıt ara.
3. Benzer kayıt varsa: **dosyalar / tuzaklar / çözüm** bölümünü rehber al; kör tekrar etme.
4. Yoksa: yine de `kayitlar/` ve `kayitlar.jsonl` son 3–5 satıra göz at (son oturumlar).

## 2) İş bitince (5–10 satır + ince detay)

Yeni kayıt ekle:

- Markdown: `kayitlar/YYYY-MM-DD_<kisa-slug>.md`
- Aynı anda bir satır: `kayitlar.jsonl` (append)

Şablon alanları:

| Alan | Ne yazılır |
|------|------------|
| tarih | ISO gün + saat dilimi notu |
| is_ozeti | 1–2 cümle: ne yapıldı |
| branch / commit | dal adı + kısa SHA |
| dosyalar | dokunulan kritik yollar |
| tuzaklar | nerede yanıldık / ne kırıldı |
| cozum | ne işe yaradı |
| benzer_anahtarlar | arama için: `sentez`, `main-merge`, `ci-smoke`… |
| durum | hazir / mimar-onay-bekliyor / yarim |

## 3) Kurallar

- Ümit «al» demeden `main`’e zorlama; merge ayrı iş olabilir.
- «Yaptım» demek yetmez: kayıt + branch/commit kanıtı.
- Sırlar / API anahtarları yazılmaz.
- Kısa tut; gelecek çırak 30 saniyede tarayabilsin.

## 4) Hızlı yollar

```text
docs/cirak_hafiza/CIRAK_HAFIZA_OKU.md   ← protokol (bu dosya)
docs/cirak_hafiza/INDEX.md              ← anahtar → kayıt
docs/cirak_hafiza/kayitlar/             ← detaylı markdown
docs/cirak_hafiza/kayitlar.jsonl        ← tek satırlık indeks log
```
