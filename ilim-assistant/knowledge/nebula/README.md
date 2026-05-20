# Nebula — yapılandırılmış kitap hafızası

**Sohbet:** Yalnızca «hatırla / profil» → `ruzgar_genel_hafiza.json` (küçük, kişisel).

**Kitap / ansiklopedi:** Sohbette dosya yolu + komut ile yüklenir; kayıtlar burada
`<koleksiyon>/incremental/nebula_batch_#####.md` paketlerine **konu başlığı (`##`)** ile yazılır.
Ham 500 sayfalık blok tek dosyaya dökülmez.

## Örnek komut (sohbet)

```text
knowledge/TARIH_VE_KULTUR/tarih_kaynak.json dosyasını oku ve hafızana kaydet
```

```text
D:\veri\osmanli_ozet.txt yolundaki kitabı hafızana al
```

## Kaynak dosya biçimleri

| Biçim | Kural |
|--------|--------|
| `.txt` / `.tab` | `Başlık<TAB>Paragraf` veya `\|` / `=` ayırıcı |
| `.json` | `{ "entries": [ { "title": "...", "body": "..." } ] }` |
| `.md` | `## Başlık` altında paragraflar |

## Teknik

- Modül: `ilim_assistant.nebula_kitap_hafiza`
- Paket boyutu: `RUZGAR_NEBULA_BATCH_SIZE` (varsayılan 400)
- İndeks: `python -m ilim_assistant.ingest_cli --incremental` ile otomatik tetiklenir (ingest sonunda)
