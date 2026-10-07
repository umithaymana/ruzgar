# Rüzgar — Ortak kaynak altyapısı

Ümit & Gökçenur — tüm bilgi alanlarında ortak şema, alan kataloğu ve güvenli atıf.

## Üç katmanı karıştırma

| Katman | Ne | Nerede |
|--------|-----|--------|
| **Kalıcı kütüphane** | Kitap, matın, ansiklopedi | `KAYNAK_KAYIT.json` + `knowledge/ilim`, `kutuphane`, `nebula`… |
| **Web (geçici)** | Güncel internet | `web_cache/` — kalıcı kayıtla aynı dosyaya yazma |
| **Kullanıcı hafızası** | «hatırla» sohbet notları | `ruzgar_genel_hafiza.json` — buraya dokunma |

## Dosyalar

- `SEMA.json` — alan sözlüğü ve atıf kuralları
- `ALANLAR.json` — 9 alan + genişletilebilir kök yollar
- `KAYNAK_KAYIT.json` — kalıcı kaynak kayıtları
- `alanlar/<id>/` — henüz içerik kökü olmayan alanlar için yer tutucu
- `web_cache/` — web erişim notları (ileride)

## Tasavvuf metinlerini nereye koyarım?

```
knowledge/ilim/din/09_ahlak_tasavvuf/eserler/<eser_id>/
```

Örnek: İhyâ → `eserler/gazali_ihya/` (MD/PDF veya sonra `incremental/` batch).  
İbnü'l-Arabî şerhleri → `09_ahlak_tasavvuf/serh_ve_aciklama/<serh_id>/`

Kayıt zaten `KAYNAK_KAYIT.json` içinde; metin gelince `durum` → `hazir` veya ingest sonrası güncelle.

## Yeni bilgi alanı eklemek

1. `ALANLAR.json` içine yeni `id` / `ad` / `kok_yollar` ekle.
2. İstersen `alanlar/<id>/README.md` oluştur.
3. Eserleri ilgili köke koy; `KAYNAK_KAYIT.json`’a kayıt ekle (`ilim_alani` = yeni id).
4. Atıf otomatik ortak şemadan okunur — alan özel atıf kodu gerekmez.

## Kod

- Modül: `ilim_assistant.ruzgar_ortak_kaynak`
- Kapat: `RUZGAR_ORTAK_KAYNAK=0`
