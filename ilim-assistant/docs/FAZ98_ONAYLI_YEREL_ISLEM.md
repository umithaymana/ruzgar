# Faz 98 — Ümit abi onay kapısı (P12)

**Durum:** 2026-05-27 · `programlama_faz98.py` · varsayılan **açık** (`RUZGAR_FAZ98=1`)

## Amaç

Cursor’daki gibi dosya taşıma, kopyalama, `pip`, `projects/` içi shell — ama **onay olmadan bilgisayara dokunma yok**.

## Akış

1. Sen isteğini yazarsın (doğal Türkçe veya `işlem iste: …`).
2. Rüzgar **önizleme** verir: ne yapacağı, iyi/kötü senaryo, riskler.
3. Sen karar verirsin:
   - **`tamam yap`** / **`tamam`** → uygular, sonuç raporu
   - **`yapma`** / **`iptal`** → hiçbir şey yapmaz
4. Bekleyen işlem `.ruzgar/umit_onay_pending.json` (≈15 dk).

## Örnek diyalog

```
Sen: Masaüstündeki rapor.txt dosyasını projects/demo/ içine kopyala

Rüzgar: Şu işlemi yapmak istiyorum — henüz yapmadım.
        Ne: Dosya kopyalama
        Kaynak: ...
        Hedef: ...
        Beklenen sonuç: ...
        Onay: tamam yap · Vazgeç: yapma

Sen: tamam yap

Rüzgar: Onayladığın işlemi yaptım. Sonuç: Kopyalandı → ...
```

## İzinli yollar

- Rüzgar proje kökü (`YAPAY ZEKA` / `LOCAL_TOOLS_ROOT`)
- Kullanıcı: Masaüstü, İndirilenler, Belgeler
- Ek: `RUZGAR_FAZ98_EXTRA_PATHS` (noktalı virgülle)

**Yasak:** `System32`, `.env`, hafıza JSON, keyfi silme.

## Komutlar

| Tür | Örnek |
|-----|--------|
| Doğal dil | `şu dosyayı şuraya taşı`, `pytest kur` |
| Açık | `işlem iste: move C:\...\a.txt -> projects/foo/b.txt` |
| Onay | `tamam yap`, `tamam` |
| Red | `yapma`, `iptal` |
| Liste | `işlem liste` |
| Geçmiş | `işlem geçmişi`, `işlem geçmişi 20`, `işlem geçmişi sadece fail` |

`işlem iste:` biçimleri: `copy`, `move`, `mkdir`, `shell projects/x/ …`, `pip paket`, `winget install Python.Python.3.12 …`

## Dönüşte devam planı

1. Sunucuyu yeniden başlat; Programlama motorunda dene.
2. Küçük test: `işlem iste: mkdir projects/onay-test` → `tamam yap`.
3. Sıradaki geliştirmeler (istersen):
   - Atölye UI’da «Onay bekliyor» kartı
   - Geçmiş logunu mini panelde canlı göstermek

## Kapatma

`RUZGAR_FAZ98=0` → eski Faz 67 shell / yalnızca @@write davranışı.
