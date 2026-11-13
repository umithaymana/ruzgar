# -*- coding: utf-8 -*-
"""Tek seferlik: Sahne başlama planı Word. Bu script plan dosyasına sonradan dokunmaz."""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.shared import Cm, Pt

OUT = Path(r"C:\Users\hayma\Desktop\RÜZGAR") / "RUZGAR_SAHNE_BASLAMA_PLANI_2026-11-13.docx"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    for s in doc.sections:
        s.top_margin = Cm(2)
        s.bottom_margin = Cm(2)
        s.left_margin = Cm(2.2)
        s.right_margin = Cm(2.2)

    def h(text: str, level: int = 1) -> None:
        doc.add_heading(text, level=level)

    def p(text: str, bold: bool = False) -> None:
        para = doc.add_paragraph()
        run = para.add_run(text)
        run.bold = bold
        run.font.size = Pt(11)

    h("RÜZGAR — SAHNE BAŞLAMA PLANI", 0)
    p("Tarih: 2026-11-13 · Mimar onayı ile mühür · Takip belgesi")
    p(
        "KESİN EMİR: Bu Word dosyasına yazıldıktan sonra müdahale edilmez. "
        "Takip Mimar tarafından buradan yapılır."
    )
    p(
        "İlke: Hayal sınırsız · inşa sıralı · yakıt kalın · RAG en sonda · "
        "mevcut eser/yazılım varsa ikinci kez yükleme yok"
    )
    p("Kimlik: Konuşursun; Rüzgar senin sahneni ve kütüphaneni yönetir.")
    p(
        "Bağlı kayıtlar: SOHBET_RUZGAR_SAHNE_VIZYON_2026-11-04.md · "
        "RUZGAR_KUTUPHANE_SONRASI_YOL_HARITASI.md · mobil PWA + sahne dilim 1–38 (kabuk)"
    )

    h("A) Kuzey yıldızı ve ürün", 1)
    p(
        "Sahne = tek büyük tiyatro / delil tahtası. Boşken Rüzgar yüzü; iş gelince "
        "harita, cam, TV, uzay, 3D/4D, montaj, kod ürünü, müze masası olur."
    )
    p(
        "Süper-el: söz → niyet → sahne eylemi. Sekiz fiil: göster · odakla · "
        "karşılaştır · zaman kaydır · pin · değiştir · dışarı ver · temizle."
    )
    p(
        "PC = geniş üretim stüdyosu. Mobil = uygulamalı görsel + ses + işaret + onay "
        "(A tam / B güçlü görsel / C kumanda)."
    )
    p(
        "Yasal çizgi: senin cam + resmi açık kapı. İzinsiz kamera / ToS delen kazı yok. "
        "Telifli modern tam metin yağması yok."
    )

    h("B) Meslek odaları (tam liste — hepsi aynı sahne, sürücü seti değişir)", 1)
    meslekler = [
        "Mimar / müteahhit — arsa Earth, plan/kroki, kuş bakışı, 3D kütle, 4D inşaat fazı, yan siluet, şantiye camı, metraj.",
        "Yönetmen / editör — timeline, kes/birleştir, ses masası, altyazı/tercüme, storyboard, önizleme; ağır render PC.",
        "Yazılımcı / programcı — çalışan ürün önizleme, diff, test/health, organ ekleme; yazım/ajan PC, mobil B/C.",
        "Araştırmacı / ilim — eser, karşılaştırma, çeviri, özet, tez iskeleti, kaynak zinciri, tarih koridoru.",
        "Gezgin / coğrafya / saha — atlas, Earth, şehir/kültür, arazi, pin, dil cep.",
        "Doktor / eğitmen — anatomi şeması, ders tahtası adım adım, sesli anlatım (eğitim; teşhis iddiası yok).",
        "Avukat / noter işi — madde karşılaştırma, kronoloji şeridi, belge diff (hukuki tavsiye değil; dosya masası).",
        "Tarihçi / rehber — zaman koridoru + Earth + eser.",
        "Mühendis — şema, simülasyon (sarkaç, yörünge, akış), tablo.",
        "Gazeteci — kaynak masası + harita + yasal yayın açma.",
        "Müzisyen — partisyon + dalga + bölüm tekrarı.",
        "Çiftçi / saha — tarla haritası + kendi cam + açık hava verisi.",
        "Öğrenci — ders → tahta → quiz → hafıza odası Sınav.",
        "Aile — ev camı / kim geldi notu; cihaz defteri; gizlilik sende.",
    ]
    for line in meslekler:
        doc.add_paragraph(line, style="List Bullet")

    h("C) Mobil erişim (A/B/C) — özet", 1)
    p("A Tam kullan: yüz+ses, harita bakış, cam/TV izle, eser oku/özet, kısa çeviri, sunum göster, ilerleme kartı.")
    p("B Güçlü görsel: 3D bak/seç, 4D kaydır, plan işaret, film önizleme+onay, kod ürün önizleme, karşılaştırma dar ekran.")
    p("C Kumanda: uzun tez yazımı, ağır montaj/render, derin debug, ajan kod — başlat/durdur/pin; üretim PC.")

    h("D) Eser / yazılım kuralı", 1)
    p("İndirmeden önce Rüzgar knowledge + tools + masaüstü envanter taranır. Varsa kullanılır; ikinci kez yüklenmez.")
    p("Önce indir + klasöre yükle + lisans/meslek etiketi. RAG (indeks) EN SONDA.")
    p("Cimrilik yok: listedeki tüm odalara kalın raf.")

    h("E) Kesin sıra (atlamasız) — takip buradan", 1)
    p(
        "Aşağıdaki numaralar bozulmaz. RAG her zaman en sonda. "
        "Mevcut eser/yazılım varsa adımda ‘zaten var’ işaretlenir, yeniden indirilmez.",
        bold=True,
    )

    steps = [
        "1) Bu plan mühürlendi (2026-11-13 Word). Takip belgesi; dosyaya sonradan müdahale yok.",
        "2) Mevcut envanter taraması: knowledge/ · tools/ · Desktop RÜZGAR envanter/katalog · yüklü yazılım. Çift yükleme listesi çıkar.",
        "3) Ortak omurga rafı indir+yükle (RAG yok): harita/coğrafya (Natural Earth, MapLibre/OSM notları), uzay/NASA-ISS açık kaynaklar, genel fen (OpenStax/OCW kalın), FFmpeg/medya teknik, homelab-cam-gizlilik, Rüzgar evi teknik (API/Electron/agent).",
        "4) Mimar / müteahhit rafı kalın indir+yükle (mevcut varsa atla): çizim/CAD düşüncesi, yapı/malzeme, şehircilik kavram, 3D/glTF/Three/WebGL, fotogrametri/kuş bakışı, 4D/metraj, kamu malı yapı/şehir görselleri.",
        "5) Yönetmen / editör rafı: kurgu teorisi, FFmpeg pratik set, ses post, SRT/VTT, sinematografi giriş, storyboard, telif/adil kullanım özet.",
        "6) Yazılımcı / programcı rafı: dil/runtime resmi+açık kitaplar, web/API/test, agent/tool, IR/OpenSearch/embedding, OpenCV/FFmpeg bağ, Three/MapLibre/WebRTC/a11y, yazılım mimarisi.",
        "7) Araştırmacı / ilim rafı: metodoloji, atıf/tez, Arapça NLP/ICU/MT doküman, kamu malı karşılaştırmalı korpus; İslami Şamile mevcut yol ile uyum (yeniden indirme yok).",
        "8) Gezgin / coğrafya / saha rafı: OSM ekosistemi, seyahatname/şehir (mevcut İbn Battuta vb. kullan), topo/GeoJSON, dil cep.",
        "9) Doktor / eğitmen rafı: açık anatomi atlas/şema (eğitim), pedagoji, ders tasarımı, tahta dili — teşhis iddiası yok etiketi zorunlu.",
        "10) Avukat / noter dosya masası rafı: belge karşılaştırma/diff pratik, kronoloji, arşiv düzeni — hukuki tavsiye değil etiketi.",
        "11) Tarihçi / rehber rafı: dönem atlası, kronoloji, OpenITI/nebula mevcutları kullan, rehber coğrafya.",
        "12) Mühendis rafı: OpenStax mühendislik, şema/simülasyon kavram (sarkaç/yörünge/akış), tablo/veri.",
        "13) Gazeteci rafı: kaynak doğrulama, açık veri gazeteciliği, harita+yayın yasal kapı notları.",
        "14) Müzisyen rafı: açık müzik teorisi, partisyon okuma, ses/dalga pratik.",
        "15) Çiftçi / saha rafı: tarla/harita Geo, açık hava verisi kullanımı, kendi cam defteri şablonu.",
        "16) Öğrenci rafı: ders çalışma yöntemi, quiz/anki tarzı açık yöntem, hafıza odası Sınav şablonu.",
        "17) Aile rafı: homelab, cihaz defteri şablonu, gizlilik/izin notları (ev camı).",
        "18) Tüm yüklenenlerin envanter tablosu (meslek · lisans · yol · RAG-aday evet/hayır). Eksik varsa tamamla.",
        "19) Sahne kabuğu S1: mobil tam sahne + alt şerit; çift basımı kes; PC+mobil smoke.",
        "20) Sahne kabuğu S2: PC boşken tam sahne ↔ çalışma yüzeyi yumuşak geçiş; yüz kilidi bozulmaz.",
        "21) Süper-el iskeleti: niyet → sahne eylemi köprüsü + 8 fiil.",
        "22) Organ sürücü-1: Harita / Earth (yasal).",
        "23) Organ sürücü-2: Cam / TV / yasal yayın.",
        "24) Organ sürücü-3: Uzay penceresi + Foto katmanı.",
        "25) Organ sürücü-4: Belge / tablo / sunum / çizim araçlarının sahne bağları.",
        "26) Meslek pilot-1 (mimar odası): plan/3D bakış/4D kaydır mobil B + PC üretim.",
        "27) Meslek pilot-2 (yönetmen): timeline önizleme + ses; ağır iş PC.",
        "28) Meslek pilot-3 (yazılımcı): ürün önizleme + diff kartı.",
        "29) Meslek pilot-4 (araştırmacı): eser karşılaştır + çeviri katmanı.",
        "30) Kalan meslek odaları ince dilim: eğitmen, hukuk dosya, tarihçi, mühendis, gazeteci, müzisyen, çiftçi, öğrenci, aile.",
        "31) Motor–sahne iş rozetleri (ses/video/okuma/mimar/tercüme/hafıza/programlama) + hafıza odaları.",
        "32) Mobil A/B/C davranış kilidi + enerji/hafif sahne.",
        "33) RAG EN SON: aday=evet eserler artımlı ingest; domain/meslek boost; ana indeksi körlemesine ezme.",
        "34) Meslek başına canlı smoke pil (5–10 soru + organ denemesi).",
        "35) Güvenli liman: commit + PROJE_DURUMU güncelle + mühür.",
    ]
    for s in steps:
        doc.add_paragraph(s)

    h("F) Bilerek yapılmayacaklar", 1)
    for x in [
        "Bu Word takip dosyasına sonradan müdahale.",
        "Onaysız sıra atlama (özellikle RAG’i öne almak).",
        "Mevcut eser/yazılımı ikinci kez indirmek.",
        "İzinsiz kamera / kapalı yayın kazı.",
        "Boot sırası veya yüz kilidini sessizce kırmak.",
        "Mobilde tam CAD / tam NLE / tam IDE şişirmek.",
    ]:
        doc.add_paragraph(x, style="List Bullet")

    h("G) Başlangıç emri", 1)
    p(
        "2026-11-13 Mimar: Bismillah — yönetici izni verildi; sormadan yürüt. "
        "Usta sıra 1→35. Takip bu belgeden."
    )

    doc.save(OUT)
    print(f"WROTE {OUT}")
    print(f"size={OUT.stat().st_size}")


if __name__ == "__main__":
    main()
