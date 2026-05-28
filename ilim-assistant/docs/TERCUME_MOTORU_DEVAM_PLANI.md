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

## Sonraki adimlar (oncelik sirasiyla)
1. OCR kalite paketi
   - `lang` secimini UI'dan dinamiklestir (tur/eng/ara/deu/frk vb.)
   - OCR temizleme katmani (satir birlestirme, tire sonu duzeltme)
2. Sayfa sayfa ceviri takip paneli
   - ilerleme cubugu
   - hangi sayfa bitti/hata verdi gorunumu
3. Cikti bicimi iyilestirme
   - `md` icin bolum basliklarini koru
   - `html` icin temel stilablon
4. Book format kalite genisletme
   - epub bolum basliklarini daha iyi cikarma
   - fb2 metadata (yazar/baslik) alma
5. Guvenli kaydetme UX
   - "son kayit klasoru" hafizasi
   - ad cakismasinda otomatik versiyonlama (`_v2`, `_v3`)

## Teknik notlar
- Sadece Tercume Motoru dosyalarina dokunuldu.
- Diger motorlara bilerek mudahale edilmedi.
- Zor formatlarda sistem araci yoksa net kurulum uyarisi veriliyor.

## Hizli test komutlari
- Backend derleme:
  - `python -m py_compile desktop_server.py`
- Frontend JS kontrol:
  - `node --check ruzgar-desktop/app.js`
