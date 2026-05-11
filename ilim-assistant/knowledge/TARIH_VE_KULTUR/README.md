# Tarih ve kültür hafızası (`TARIH_VE_KULTUR`)

Rüzgar’ın **Tarih Hafızası**; vektör aramasında `TARIH_VE_KULTUR/` altındaki Markdown dosyalarından beslenir.

## Alt konular (önerilen yerleşim)

| Klasör / etiket | İçerik örneği |
|-----------------|---------------|
| **TTK / akademik özet** | Türk Tarih Kurumu kaynaklı veya kurumsal özet metinler (telif ve izin kurallarına uygun) |
| **Osmanlı tarihi** | Dönemler, belgeler, isimler — kısa maddeler halinde |
| **Büyük Türk tarihi** | Göktürkler, Selçuklular, Cumhuriyet öncesi/sonrası genel hatlar |

Ham metinleri doğrudan buraya koyabilir veya kademeli yükleme için aşağıdaki protokolü kullanabilirsiniz.

## Büyük derleme: `tarih_kaynak_buyuk.json` (Vikiveri + demo)

On bin+ benzersiz kayıt için (Wikidata SPARQL çoklu sorgular + isteğe bağlı Digital Ottomans):

```text
python -m ilim_assistant.tarih_kaynak_fetch --mode buyuk --target-min 10000
```

Çıktı: `knowledge/TARIH_VE_KULTUR/tarih_kaynak_buyuk.json`. Ardından:

```text
python -m ilim_assistant.tarih_incremental_protocol reset --yes
python -m ilim_assistant.tarih_incremental_protocol init
python -m ilim_assistant.tarih_incremental_protocol ingest --source knowledge/TARIH_VE_KULTUR/tarih_kaynak_buyuk.json --batch-size 500
python -m ilim_assistant.tarih_incremental_protocol finalize
```

## Küçük demo: `tarih_kaynak.json`

```text
python -m ilim_assistant.tarih_kaynak_fetch --mode demo
```

## Kademeli indeksleme

1. Kaynak dosya: satır başına `Başlık<TAB>Paragraf` (veya `|`, `=` ayırıcıları; `tdk_incremental_protocol` ile aynı kural) **veya** `tarih_kaynak.json` (`entries` dizisi).
2. Komutlar (`ilim-assistant` kökünden):

```text
python -m ilim_assistant.tarih_incremental_protocol init
python -m ilim_assistant.tarih_incremental_protocol ingest --source yol/kaynak.txt --batch-size 400
python -m ilim_assistant.tarih_incremental_protocol finalize
```

Paketler `incremental/tarih_batch_#####.md` olarak yazılır; her paketten sonra `build_index(incremental=True)` çalışır.

**Not:** `tarih_incremental_protocol` çalışırken genel `ingest_cli` kilidi devreye girer (`--allow-other-knowledge` ile aşılır).

## Telif

TTK ve yayınevlerine ait metinleri yalnızca **izin verilen** veya **alenî / özet** nitelikteki içerikle sınırlayın.
