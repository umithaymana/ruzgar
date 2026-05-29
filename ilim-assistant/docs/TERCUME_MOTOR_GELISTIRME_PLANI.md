# Tercüme motoru geliştirme planı (Ümit direktifleri)

**Kural:** Yalnızca `#page-tercume`, `tercume-atolye.*`, `tercume_atolye.py`, `desktop_server` tercüme API’leri.  
**Diğer motor sayfalarına ve programlama motoruna dokunulmaz.**

| # | Direktif | Uygulama |
|---|----------|----------|
| 1 | Klasörden dosya aç, çalışma listesi | `tercume-work-root` + Electron klasör seç + `workspace/list` |
| 2 | Tüm kitap uzantıları | `read-ebook` + PDF/DOCX/OCR birleşik açılış |
| 3 | Seçilen dilde çeviri | `translate-chunk` API + sıkı prompt |
| 4 | Hedef dil imla/kuralları | `grammar_directive(tgt)` her istekte |
| 5 | Sayfa sayfa / tamamı | `source-pages` + kuyruk + ilerleme çubuğu |
| 6 | Çıktı uzantısı | `tercume-output-format` txt/md/html |
| 7 | Kaydet + ikinci kopya | `save-target` + `copy_rel` alanı |
| 8 | URL + dosya içe aktar | `import-url` + `import-file` |
| 9 | UI sade, çeviriye alan | Katlanır yardım, tam yükseklik layout |
| 10 | Word benzeri düzenleme | `contenteditable` paneller, zoom, seçim |
| 11 | Sadece bu motor | Scoped CSS/JS |

## Çırak (programlama motoru öğrensin — öneri)

`.ruzgar/tercume_apprentice.jsonl` — her çeviri/kaydet işleminde kısa ders satırı.  
Programlama motoru dosyaları **şimdilik değişmez**; ileride bu günlüğü okuyabilir.  
Tercüme sayfasında küçük «Çırak günlüğü» paneli (salt okunur).

## Test

```powershell
cd ilim-assistant
python scripts/tercume_atolye_smoke.py
node --check ..\ruzgar-desktop\tercume-atolye.js
```
