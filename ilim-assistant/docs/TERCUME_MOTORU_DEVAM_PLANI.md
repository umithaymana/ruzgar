# Tercume Motoru Devam Plani

Bu not, ara sonrasinda ayni yerden devam etmek icin birakildi.

## Bu turda tamamlananlar
- Tercume panelinde kaynak dosya acma + calisma listesi
- Kaynak kok klasoru secimi (repo ici goreli yol)
- URL'den kaynak indirme (`/api/tercume/import-url`)
- E-kitap okuma genisletmesi (`/api/workspace/read-ebook`)
  - txt, md, html, rtf, epub, fb2
  - mobi/azw/azw3/kfx (Calibre `ebook-convert` varsa)
  - djvu/djv (`djvutxt` varsa)
- Gorselden OCR okuma (`/api/workspace/read-image-ocr`)
- Ceviri modu: tek parca / sayfa sayfa / tamami
- Sayfa sayfa ceviri sonucunu hedef panelde birlestirme
- Cikti uzantisi secimi (`txt`, `md`, `html`)
- Ciktiyi istenen goreli yola kaydetme + ikinci konuma kopyalama

## Faz 14 (2026-05) — tamamlandi

Bkz. `TERCUME_FAZ14_OZET.md` (14A–14E).

## Sonraki adimlar (oncelik sirasiyla)
1. OCR kalite paketi (kismen var: `tercume_ocr_clean`, UI dil secimi)
2. Book format: EPUB bolum + FB2 metadata
3. Kullanici terim tablosu (TM duzenleme UI)
4. Canli Ollama `tercume_live_smoke.py`

## Teknik notlar
- Sadece Tercume Motoru dosyalarina dokunuldu.
- Diger motorlara bilerek mudahale edilmedi.
- Zor formatlarda sistem araci yoksa net kurulum uyarisi veriliyor.

## Hizli test komutlari
- Backend derleme:
  - `python -m py_compile desktop_server.py`
- Frontend JS kontrol:
  - `node --check ruzgar-desktop/app.js`
