# -*- coding: utf-8 -*-
"""Sahne eser indirme listesi — ayrı Word (plan dosyasına dokunulmaz)."""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.shared import Cm, Pt

OUT = Path(r"C:\Users\hayma\Desktop\RÜZGAR") / "RUZGAR_SAHNE_ESER_INDIRME_LISTESI_2026-11-13.docx"


def main() -> None:
    doc = Document()
    for s in doc.sections:
        s.top_margin = Cm(2)
        s.bottom_margin = Cm(2)
        s.left_margin = Cm(2.2)
        s.right_margin = Cm(2.2)

    def h(t: str, level: int = 1) -> None:
        doc.add_heading(t, level=level)

    def p(t: str, bold: bool = False) -> None:
        para = doc.add_paragraph()
        r = para.add_run(t)
        r.bold = bold
        r.font.size = Pt(11)

    def bullets(items: list[str]) -> None:
        for it in items:
            doc.add_paragraph(it, style="List Bullet")

    h("RÜZGAR — SAHNE ESER / KAYNAK İNDİRME LİSTESİ", 0)
    p("Tarih: 2026-11-13")
    p(
        "Bu belge, Sahne Başlama Planı’ndaki yakıt (eser/doküman/yazılım kaynağı) listesidir. "
        "Plan dosyasından ayrıdır. RAG bu listede yok — önce indir+yükle."
    )
    p(
        "Kural: Kütüphanede / tools’ta zaten varsa ikinci kez indirilmez. "
        "Lisans: kamu malı, açık lisans, kurumun açık dokümantasyonu."
    )

    h("A) Zaten var — yeniden indirilmeyecek (omurga)", 1)
    p("Kanıt: bilgisayar_eserleri ileri paketler + sistem yazılımı.", bold=True)
    bullets(
        [
            "MapLibre GL JS dokümantasyonu + offline harita notları (paket: cografya_tarih)",
            "Natural Earth atlas / coğrafya veri notları (paket: atlas_natural_earth)",
            "Uzay / Astropy / orbital-sky ders dokümanları (paket: uzay_astro)",
            "OpenStax derin fen seti (paket: openstax_derin)",
            "MIT OCW seçme açık ders notları (paket: mit_ocw_secme)",
            "FFmpeg filtre/pratik + atölye gece kuyruk notları (paket: ffmpeg, atolye_gece)",
            "OpenCV + WebRTC MDN + Three/Godot kamera notları (paket: opencv, webrtc_mdn, godot_three_cam)",
            "Whisper / Piper / Web Audio MDN (paket: whisper, piper, web_audio_mdn)",
            "Home Assistant + ESP-IDF + FreeRTOS / madde-el (paket: home_assistant, esp_idf…)",
            "Programlama kalın dal (01_programlama vb. binlerce md) + tree-sitter, Ollama, Playwright",
            "IR / Lucene / OpenSearch / SQLite FTS (hafıza yakıtı)",
            "Marian/OPUS, Unicode/ICU, CAMeL/Farasa (tercüme yakıtı)",
            "Sistem: FFmpeg (winget), OpenCV 5.0.0 Python, Ollama köprüsü",
            "İlim / Şamile / nebula / TARIH_VE_KULTUR — mevcut külliyat (yeniden yağma yok)",
        ]
    )

    h("B) Yeni / kalınlaştırılan meslek rafları (indirme turu 2026-11-13)", 1)
    p(
        "Aşağıdakiler SAHNE Y1 meslek script’i ile indirilip knowledge altına yüklenir. "
        "Her satır = paket anahtarı + ana kaynaklar."
    )

    h("B1) Mimar / müteahhit — paket: mimar_bina_3d", 2)
    bullets(
        [
            "Khronos glTF 2.0 spesifikasyonu + GitHub glTF",
            "Three.js docs / manual / README",
            "Blender Manual (docs.blender.org)",
            "GDAL + PROJ + OSGeo wiki",
            "OpenDroneMap docs + OpenSfM",
            "OSM Buildings / Simple 3D buildings wiki",
            "CityGML / 3D geodata (TU Delft açık sayfalar)",
            "Wikipedia: BIM, Architectural drawing, 4D BIM, Photogrammetry, Urban planning, Zoning, FAR",
            "MDN WebGL API",
        ]
    )

    h("B2) Yönetmen / editör — paket: yonetmen_kurgu", 2)
    bullets(
        [
            "OpenTimelineIO (OTIO) docs + GitHub README",
            "W3C WebVTT + Media Fragments",
            "MDN WebVTT API",
            "FFmpeg filters / concatenate / audio channel wiki",
            "ITU-R BS.1770 (loudness)",
            "Wikipedia: Film editing, Continuity, Montage, Storyboard, Subtitle, Loudness war, Dialog normalization",
        ]
    )

    h("B3) Yazılımcı — durum: zaten var (ek tur şart değil)", 2)
    bullets(
        [
            "Mevcut: bilgisayar_eserleri 01–12 + İLERİ_F (tree-sitter, sandbox, Ollama/LoRA, Crafting Interpreters…)",
            "Eksik görülürse sonra ek: resmi Python/JS dil doküman ayna (yalnız eksik sayfalar)",
        ]
    )

    h("B4) Araştırmacı / ilim — kısmen var + metodoloji ek", 2)
    bullets(
        [
            "Mevcut: Şamile/ilim, IR kitabı, Marian/OPUS, CAMeL/Farasa",
            "Ek (meslek turunda / bilimsel yöntem dalı): W3C PROV, annotation model (karşılaştırma/atıf masası)",
            "OpenStax subjects + araştırma yöntemi Wikipedia/açık rehberler (öğrenci paketiyle örtüşenler tek kez)",
        ]
    )

    h("B5) Gezgin / tarihçi rehber — paket: gezgin_rehber", 2)
    bullets(
        [
            "OpenStreetMap about + Map features wiki + Nominatim docs",
            "MapLibre GL JS docs (tamamlama; ana paket zaten vardı)",
            "Natural Earth sitesi",
            "Wikipedia: Travel literature, Historical geography, Chorography",
            "Nebula / İbn Battuta vb. mevcut seyahatname — yeniden indirme yok",
        ]
    )

    h("B6) Doktor / eğitmen — paket: egitim_anatomi (teşhis iddiası YOK)", 2)
    bullets(
        [
            "OpenStax Anatomy and Physiology 2e (sayfalar + details)",
            "Wikipedia: Anatomy, Physiology, Medical education, Pedagogy, Instructional design, Active learning, Bloom’s taxonomy",
            "W3C / MDN erişilebilirlik (ders tahtası a11y)",
            "Etiket zorunlu: eğitim amaçlı; tıbbi teşhis/tedavi iddiası yok",
        ]
    )

    h("B7) Avukat / noter dosya masası — paket: hukuk_dosya_masa (tavsiye değil)", 2)
    bullets(
        [
            "W3C Web Annotation Model",
            "W3C PROV Overview + PROV-DM",
            "RFC 6902 JSON Patch",
            "git-diff dokümantasyonu",
            "Schema.org Legislation / DigitalDocument",
            "Wikipedia: Diff, Chronology, Records management, DMS, Version control",
            "Etiket: hukuki tavsiye değil; dosya/kronoloji masası",
        ]
    )

    h("B8) Mühendis — paket: muhendis_sim", 2)
    bullets(
        [
            "OpenStax University Physics Volume 1 (giriş sayfaları)",
            "SciPy tutorial + Matplotlib tutorials",
            "Wikipedia: Pendulum, Orbital mechanics, Fluid dynamics, Circuit diagram, FEM",
        ]
    )

    h("B9) Gazeteci — paket: gazeteci_acik_veri", 2)
    bullets(
        [
            "Open Data Handbook (guide)",
            "GeoJSON.org + RFC 7946",
            "Schema.org NewsArticle",
            "Wikipedia: Open data, Data journalism, Fact-checking, Source criticism",
        ]
    )

    h("B10) Müzisyen — paket: muzik_partisyon", 2)
    bullets(
        [
            "MusicXML.com",
            "W3C SMuFL / MNX overview",
            "MDN Web Audio API + OscillatorNode",
            "MuseScore handbook",
            "Wikipedia: Music theory, Musical notation, Sheet music, MIDI, Audio bit depth",
        ]
    )

    h("B11) Çiftçi / saha — paket: ciftci_saha", 2)
    bullets(
        [
            "GeoJSON + RFC 7946",
            "Open-Meteo docs (açık hava API dokümanı)",
            "OSM farmland tag wiki",
            "GDAL / PROJ",
            "Wikipedia: Precision agriculture, GIS",
        ]
    )

    h("B12) Öğrenci — paket: ogrenci_quiz", 2)
    bullets(
        [
            "AnkiWeb docs",
            "OpenStax subjects indeksi",
            "Wikipedia: Spaced repetition, Active recall, Testing effect, Feynman technique, Cornell Notes, Bloom’s taxonomy",
        ]
    )

    h("B13) Aile — paket: aile_cihaz", 2)
    bullets(
        [
            "Home Assistant docs (auth, organizing) — homelab ile örtüşenler tek kez tutulur",
            "OWASP IoT project",
            "W3C Permissions API + MDN Permissions",
            "Wikipedia: Home automation, Privacy, Least privilege",
        ]
    )

    h("C) Yazılım (eser değil ama sahne organı için — tekrar kurulum yok)", 1)
    bullets(
        [
            "FFmpeg — yüklü (winget Gyan.FFmpeg) → yeniden kurma",
            "OpenCV Python 5 — yüklü → yeniden kurma",
            "Ollama / Whisper yolları — mevcut köprüler",
            "JDK17 / SadTalker tools — mevcut; sahne omurgası için şart değil",
        ]
    )

    h("D) Bilerek listede olmayanlar", 1)
    bullets(
        [
            "Telifli modern tam kitap yağması",
            "İzinsiz kamera / kapalı yayın kazı listeleri",
            "Ücretli CAD/NLE lisans kırığı",
            "Tıbbi teşhis modeli ağırlıkları (eğitim atlası hariç)",
        ]
    )

    h("E) Takip", 1)
    p(
        "İndirme durumu teknik rapor: "
        "ilim-assistant/knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri/"
        "SAHNE_Y1_MESLEK_RAFLARI_RAPOR.json (script bitince)."
    )
    p("Envanter: SAHNE_Y1_ENVANTER_2026-11-13.json")
    p("Plan (ayrı, müdahale yok): RUZGAR_SAHNE_BASLAMA_PLANI_2026-11-13.docx")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print("WROTE", OUT, OUT.stat().st_size)


if __name__ == "__main__":
    main()
