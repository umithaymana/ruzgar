#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2.PLAN+ MOTOR_DALGALARI_VE_USTA — Excel v2 GENİŞ (Plan 1'den SONRA).

Kapı (kilit): Şamile RAG + 1.PLAN (bilgisayar/sahne) bitmeden aksiyon yok.
Bu script yalnız liste üretir; indirme/yükleme sırası bozulmaz.

Çıktı:
  Desktop/.../2.PLAN+_MOTOR_DALGALARI_VE_USTA/<KAT>/...

Sütun mantığı = 1.PLAN ile aynı.
v2: yapı güçlendirildi (14 kategori) + eserler büyütüldü.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

OUT_ROOT = Path(
    r"C:\Users\hayma\Desktop\RÜZGAR\RÜZGAR KÜTÜPHANE ENVANTER"
    r"\2.PLAN+_MOTOR_DALGALARI_VE_USTA"
)

HEADERS = [
    "NO",
    "ESER ADI (ORİJİNAL)",
    "TÜRKÇE KARŞILIĞI / AD",
    "YAZAR / KURUM",
    "RÜZGARA NE KATAR",
    "CİLT",
    "SAYFA (TAHMİNİ)",
    "DALGA",
    "NOT",
]

# Donanım merdiveni YOK (bekler). Web AÇIK — kota bilinçli. Yalnız yasal/açık.
CATS: dict[str, tuple[str, list[tuple]]] = {
    "01_MASA_BAGLARI": (
        "01 MASA BAĞLARI (Belge-Tablo-Çizim-Sunum)",
        [
            ("ProseMirror guide + examples", "ProseMirror", "ProseMirror", "Belge masası omurgası (şema+plugin)", "1", "docs", "Masa", "Açık — kritik"),
            ("TipTap docs + extensions", "TipTap", "TipTap", "Belge UI katmanı", "1", "docs", "Masa", "Açık — kritik"),
            ("Lexical docs (Meta)", "Lexical", "Meta", "Belge editör alternatifi (güçlü)", "1", "docs", "Masa", "Açık"),
            ("Quill documentation", "Quill", "Quill", "Klasik zengin metin", "1", "docs", "Masa", "Açık"),
            ("Slugify/CodeMirror 6 docs", "CodeMirror 6", "CodeMirror", "Belgede kod bloğu / atölye köprüsü", "1", "docs", "Masa/F", "Açık"),
            ("Markdown CommonMark + GFM + MDX spec", "Markdown / MDX Spec", "CommonMark / MDX", "Belge düz-metin dili", "1", "spec", "Masa", "Açık"),
            ("Pandoc User's Guide + API", "Pandoc", "John MacFarlane", "doc↔md↔pdf↔epub köprüsü", "1", "docs — geniş", "Masa", "Açık — kritik"),
            ("PDF.js docs + viewer examples", "PDF.js", "Mozilla", "PDF okuma masası", "1", "docs", "Masa", "Açık — kritik"),
            ("pdf-lib + pdfium / mupdf bindings docs", "PDF Yaz / MuPDF", "pdf-lib / Artifex", "PDF üret-düzenle", "1", "docs", "Masa", "Açık"),
            ("DOCx open XML overview + python-docx docs", "DOCX Açık Format", "ECMA / python-docx", "Word uyumlu belge", "1", "docs", "Masa", "Açık"),
            ("ODF / LibreOffice UNO docs (çekirdek)", "ODF / LibreOffice", "OASIS / TDF", "Açık ofis belgesi", "1", "docs", "Masa", "Açık"),
            ("Univer sheets docs", "Univer Tablo", "Univer", "Modern tablo motoru", "1", "docs", "Masa", "Açık — kritik"),
            ("Luckysheet / FortuneSheet docs", "Luckysheet", "Luckysheet", "Tablo masası (açık)", "1", "docs", "Masa", "Açık"),
            ("Handsontable community docs (açık kullanım)", "Handsontable (açık)", "Handsontable", "Excel-benzeri UX", "1", "docs", "Masa", "Lisans kontrol"),
            ("Apache Arrow + Parquet + DuckDB", "Arrow / Parquet / DuckDB", "ASF / DuckDB", "Büyük tablo yerelde", "1", "docs", "Masa", "Açık — kritik"),
            ("CSV RFC 4180 + frictionless table-schema", "CSV / Table Schema", "IETF / Frictionless", "Tablo içe-dışa", "1", "spec", "Masa", "Açık"),
            ("Pivot / OLAP açık yazılar + Polars docs", "Özet Tablo / Polars", "Polars", "Tablo analitik", "1", "docs", "Masa", "Açık"),
            ("Excalidraw kaynak + docs + scene JSON", "Excalidraw", "Excalidraw", "Çizim masası omurgası", "1", "docs+kod", "Masa", "Açık — kritik"),
            ("tldraw docs + sync notes", "tldraw", "tldraw", "Çizim alternatifi + sync", "1", "docs", "Masa", "Açık"),
            ("SVG 2 + Canvas 2D + Path2D MDN", "SVG / Canvas", "W3C / MDN", "Çizim düşük seviye", "1", "docs", "Masa", "Açık"),
            ("Rough.js + perfect-freehand + perfect-arrows", "El Çizgisi Paketi", "Rough.js vd.", "Doğal çizim hissi", "1", "docs", "Masa", "Açık"),
            ("Paper.js / Fabric.js docs (seçme)", "Paper / Fabric", "Paper.js / Fabric", "Vektör çizim kası", "1", "docs", "Masa", "Açık"),
            ("Reveal.js full docs + plugins", "Reveal.js", "Hakimel", "Sunum masası", "1", "docs", "Masa", "Açık — kritik"),
            ("Slidev docs", "Slidev", "Slidev", "Dev/Markdown sunum", "1", "docs", "Masa", "Açık"),
            ("impress.js + Marp docs", "impress / Marp", "Bartaz / Marp", "Uzamsal + MD sunum", "2", "docs", "Masa", "Açık"),
            ("Spectacle / MDX Deck açık docs (seçme)", "MDX Sunum", "açık", "Bileşenli slayt", "1", "docs", "Masa", "Açık"),
            ("JSON Schema + AJV + TypeBox", "JSON Schema Paketi", "JSON Schema / AJV", "Masa komut/izin şeması", "1", "docs", "Masa/F", "Açık — kritik"),
            ("Command/Memento undo-redo açık tarifler", "Geri Al / Komut", "GoF + açık", "Masa güvenli işlem", "1", "yazı", "Masa", "Açık"),
            ("Clipboard API + execCommand legacy MDN notları", "Pano API", "MDN", "Kes-kopyala-yapıştır (kilit yüz)", "1", "docs", "Masa", "Açık"),
            ("IndexedDB + OPFS + File System Access MDN", "Yerel Dosya Depo", "MDN", "Masa dosyası Electron/web", "1", "docs", "Masa", "Açık — kritik"),
            ("Electron dialog / safeStorage / protocol docs", "Electron Masa Kapısı", "Electron", "Dosya+güvenlik", "1", "docs", "Masa", "Resmi"),
            ("Autosave / CRDT yama (Yjs docs) masa için", "Yjs Çoklu Düzenleme", "Yjs", "Birlikte belge (ileride)", "1", "docs", "Masa/A", "Açık"),
            ("Print CSS + Paged.js docs", "Yazdırma / Sayfa", "Paged.js", "Belge/sunum baskı", "1", "docs", "Masa", "Açık"),
            ("WCAG 2.2 + APG (masa a11y)", "Erişilebilirlik", "W3C", "Herkes masayı kullansın", "1", "standart", "Masa", "Açık"),
            ("i18n masa (FormatJS / Fluent docs)", "Masa Çok Dil", "FormatJS / Fluent", "TR/AR arayüz", "1", "docs", "Masa/C", "Açık"),
        ],
    ),
    "02_A_OKUMA_HAFIZA": (
        "02 A DALGA — OKUMA + HAFIZA",
        [
            ("Introduction to Information Retrieval", "Bilgi Erişimine Giriş", "Manning; Raghavan; Schütze", "Okuma motoru arama teorisi", "1", "~500+", "A", "Ücretsiz — kritik"),
            ("Managing Gigabytes (ücretsizse) / IR sıkıştırma yazıları", "İndeks Sıkıştırma", "Witten et al. / açık", "Büyük kütüphane indeksi", "1", "değişken", "A", "Ücretsizse"),
            ("Apache Lucene + Solr refs", "Lucene / Solr", "ASF", "Kütüphane arama motoru", "2", "docs", "A", "Açık — kritik"),
            ("OpenSearch Documentation", "OpenSearch", "OpenSearch", "Arama kümesi", "1", "docs", "A", "Açık"),
            ("SQLite FTS5 + trigram + spellfix1", "SQLite FTS5", "SQLite", "Yerel metin arama", "1", "docs", "A", "Resmi — kritik"),
            ("Tantivy / Quickwit / Lindera", "Rust Arama Yığını", "Tantivy", "Hızlı yerel indeks", "1", "docs", "A", "Açık"),
            ("Meilisearch + Typesense docs", "Anlık Arama UX", "Meili / Typesense", "Hızlı bul-göster", "2", "docs", "A", "Açık"),
            ("Tesseract + ocrmypdf + Docling + Marker", "OCR / Belge Anlama", "UBM / Docling", "Foto→metin→raf", "1", "docs", "A", "Açık — kritik"),
            ("Unstructured / open parse tarifleri", "Belge Ayrıştırma", "Unstructured / açık", "PDF/HTML temizleme", "1", "docs", "A", "Açık"),
            ("PDF.js + MuPDF + epub.js", "Kitap Yürüyüşü Paketi", "Mozilla / Artifex / epub.js", "Cilt/sayfa/epub gezintisi", "1", "docs", "A", "Açık — kritik"),
            ("Automerge + Yjs + CRDT papers özet", "CRDT Hafıza Birleşimi", "Automerge / Yjs", "Çakışmasız hafıza", "1", "docs+makale", "A", "Açık — kritik"),
            ("OpenStax Psychology — Memory/Learning", "Bellek / Öğrenme", "OpenStax", "Hafıza odası bilimi", "1", "bölüm", "A", "CC"),
            ("Noba Memory + Attention + Learning modules", "Noba Bellek Paketi", "Noba", "Oda tasarımı", "1", "modül seti", "A", "Açık"),
            ("Working memory Baddeley açık review'lar", "Çalışma Belleği", "Baddeley vd.", "Kısa süreli kas", "1", "review", "A", "Açık"),
            ("Zettelkasten / PKM açık yöntem yazıları", "Zettelkasten", "açık yazılar", "Not sarayı yöntemi", "1", "seçme", "A", "Açık"),
            ("Zotero + Better BibTeX docs", "Zotero Künye", "Zotero", "Kaynakça + künye", "1", "docs", "A", "Açık"),
            ("W3C PROV-O + Data Provenance açık", "Kanıt Kökeni", "W3C", "Delil kartı izi", "1", "spec", "A", "Açık"),
            ("CalDAV / iCalendar / rfc5545", "Takvim Standartları", "IETF", "Sabah brifing zamanı", "1", "RFC", "A", "Kamu"),
            ("Myers diff + patience diff açık anlatım", "Diff Algoritması", "açık", "Karşılaştırma stüdyosu", "1", "yazı", "A", "Açık"),
            ("Append-only log / event sourcing kısa rehber", "Olay Günlüğü Hafıza", "açık", "Unutma/denetim izi", "1", "rehber", "A", "Açık"),
            ("Embedding multilingual + bge-reranker", "Gömme + Rerank", "BAAI / HF", "İsabetli hatırlama", "1", "docs", "A", "Açık — kritik"),
            ("ColBERT / SPLADE (ileri retrieval)", "İleri Retrieval", "ColBERT / SPLADE", "Zor soruda bul", "1", "makale+kod", "A", "Açık"),
            ("RAGAS / BEIR eval", "Okuma Kalite Sınavı", "RAGAS / BEIR", "Yalansız alıntı ölçümü", "1", "docs", "A", "Açık"),
            ("Kiwix / ZIM + openZIM format", "Kiwix Ansiklopedi", "Kiwix", "Çevrimdışı ansiklopedi odası", "1", "docs", "A", "Açık"),
            ("Hypothesis annotation / Web Annotation Data Model", "Açık Dipnot / Annotasyon", "W3C / Hypothesis", "Satıra pin", "1", "spec", "A", "Açık"),
            ("Readwise-benzeri açık: Wallabag / Linkding docs", "Okuma Kutusu", "Wallabag / Linkding", "Sonra oku + hafıza", "1", "docs", "A", "Açık"),
            ("Spaced repetition (Anki/FSRS açık algoritma)", "Aralıklı Tekrar", "FSRS / Anki açık", "Öğrenilen kalsın", "1", "docs", "A", "Açık"),
            ("Graph memory (NetworkX + JSON-LD)", "Graf Hafıza", "NetworkX / W3C", "İp-ilişki odası", "1", "docs", "A", "Açık"),
            ("GDPR silme / unutma hakkı kamu rehber", "Unutma Hakkı", "AB kamu", "Hafızadan sil politikası", "1", "rehber", "A", "Kamu"),
            ("Personal search (DocFetcher / Recoll docs)", "Masaüstü Kişisel Arama", "Recoll / DocFetcher", "Ev dosyası hafızası", "1", "docs", "A", "Açık"),
            ("Chunking best practices açık yazılar", "Parçalama (Chunk) Sanatı", "açık RAG yazıları", "İndeks kalitesi", "1", "seçme", "A", "Açık"),
            ("Citation-needed / quote-span şema tasarımı (iç)", "Alıntı Zorunlu Şema", "Rüzgar", "Uydurma değil kaynak", "1", "şema", "A", "İç — kritik"),
        ],
    ),
    "03_B_SES_NEFES": (
        "03 B DALGA — SES (NEFES / SÜPER-EL)",
        [
            ("Whisper paper + openai-whisper + faster-whisper", "Whisper STT", "OpenAI / topluluk", "Kulak — konuş→yazı", "1", "docs+makale", "B", "Açık — kritik"),
            ("Whisper.cpp / ggml audio docs", "Whisper.cpp", "ggerganov", "Hafif yerel kulak", "1", "docs", "B", "Açık"),
            ("Vosk docs + model list", "Vosk STT", "Alpha Cephei", "Düşük kaynak kulak", "1", "docs", "B", "Açık"),
            ("Coqui STT / STT training docs", "Coqui STT", "Coqui", "Eğitilebilir kulak", "1", "docs", "B", "Açık"),
            ("Piper TTS docs + voice packing", "Piper TTS", "Rhasspy", "Nefes — Rüzgar konuşsun", "1", "docs", "B", "Açık — kritik"),
            ("Mimic3 / Kokoro / Coqui TTS docs", "TTS Yığını", "Mycroft / topluluk", "Kimlik sesi seçenekleri", "1", "docs", "B", "Açık"),
            ("ESPnet TTS/ASR recipes", "ESPnet", "ESPnet", "Araştırma seviye ses", "1", "docs", "B", "Açık"),
            ("Speech and Language Processing — speech ch", "SLP Konuşma", "Jurafsky; Martin", "Konuşma bilimi", "1", "bölüm", "B", "Ücretsiz draft"),
            ("Web Speech API + MediaStream MDN", "Web Speech / Mikrofon", "MDN", "Tarayıcı nefes girişi", "1", "docs", "B", "Açık"),
            ("Web Audio API + AudioWorklet + Tone.js", "Web Audio Paketi", "W3C / Tone.js", "Sahne sesi / efekt", "1", "docs", "B", "Açık — kritik"),
            ("Silero VAD + open VAD yazıları", "VAD / Barge-in", "Silero", "Konuşurken kes-dinle", "1", "docs", "B", "Açık — kritik"),
            ("RNNoise / deepFilterNet docs", "Gürültü Bastırma", "RNNoise / DFN", "Ev gürültüsünde netlik", "1", "docs", "B", "Açık"),
            ("SSML 1.1 + prosody rehberleri", "SSML / Prosodi", "W3C", "Ton/vurgu/ders sesi", "1", "spec", "B", "Açık"),
            ("Common Voice + etik veri rehberi", "Common Voice Etik", "Mozilla", "Ses verisi bilinci", "1", "rehber", "B", "Açık"),
            ("openWakeWord / Porcupine (lisans kontrol)", "Uyandırma Sözcüğü", "openWakeWord / Picovoice", "Eller serbest çağrı", "1", "docs", "B", "Lisans kontrol"),
            ("TR+AR STT/TTS açık model kartları (HF)", "Türkçe+Arapça Ses", "HF açık kartlar", "Ana dil + Şamile nefes", "1", "model kartı", "B", "Açık — kritik"),
            ("Speaker diarization (pyannote açık)", "Konuşmacı Ayırma", "pyannote", "Kim konuştu", "1", "docs", "B", "Açık"),
            ("Forced alignment (whisperX / aeneas)", "Ses-Metin Hizalama", "whisperX / aeneas", "Kitap sesli gezinme", "1", "docs", "B", "Açık"),
            ("SoX + FFmpeg audio filtergraph", "Ses Dönüşüm", "SoX / FFmpeg", "Gece ses kuyruğu", "1", "docs", "B", "Açık"),
            ("Room impulse / spatial audio açık (WebAudio Panner)", "Uzamsal Ses", "MDN / açık", "Sahne yönlü ses", "1", "docs", "B/Sahne", "Açık"),
            ("Voice UX patterns (voice lab seçkisi)", "Sesli Arayüz Kalıpları", "açık", "Süper-el konuşma tasarımı", "1", "seçme", "B", "Açık"),
            ("Electron + native audio bridge notları", "Masaüstü Ses Köprüsü", "Electron/Node", "Uygulama nefes hattı", "1", "docs", "B", "Açık"),
            ("Godot audio buses / interactive music docs", "Godot Ses", "Godot", "Sahne nefes birleşimi", "1", "docs", "B", "Açık"),
            ("Latency budgets / real-time audio açık yazılar", "Düşük Gecikme", "açık", "Canlı süper-el hissi", "1", "yazı", "B", "Açık"),
            ("Phonetics açık textbook seçkisi (TR/IPA)", "Sesbilgisi / IPA", "açık", "Telaffuz camı", "1", "seçme", "B/C", "Açık"),
            ("Podcast chapter markers / chapters VTT", "Ses Bölüm İşaretleri", "açık", "Uzun dinlemede gezin", "1", "spec", "B", "Açık"),
        ],
    ),
    "04_C_TERCUME_KOPRU": (
        "04 C DALGA — TERCÜME (KÖPRÜ)",
        [
            ("Speech and Language Processing — MT/NLP", "SLP Çeviri/NLP", "Jurafsky; Martin", "Çeviri bilimi omurgası", "1", "bölüm+kitap", "C", "Ücretsiz draft — kritik"),
            ("Marian NMT + OPUS-MT docs/models", "Marian / OPUS-MT", "Helsinki-NLP", "Yerel makine çevirisi", "1", "docs", "C", "Açık — kritik"),
            ("Argos Translate + LibreTranslate docs", "Argos / LibreTranslate", "Argos / LibreTranslate", "Hafif yerel MT servisi", "1", "docs", "C", "Açık — kritik"),
            ("NLLB-200 / M2M-100 HF docs", "NLLB / M2M", "Meta", "Çok dilli yerel MT", "1", "docs+makale", "C", "Açık ağırlık"),
            ("SentencePiece + tokenizers docs", "SentencePiece", "Google / HF", "Çok dil token", "1", "docs", "C", "Açık"),
            ("Unicode Standard + UAX + ICU User Guide", "Unicode / ICU", "Unicode / ICU", "Harf/dil doğru işlensin", "2", "docs — geniş", "C", "Açık — kritik"),
            ("HarfBuzz + FriBidi + Raqm", "RTL Yazı Motoru", "HarfBuzz", "Arapça cam doğru", "1", "docs", "C", "Açık — kritik"),
            ("CLDR / locale data docs", "CLDR Yerel Veri", "Unicode CLDR", "Tarih/sayı/dil etiketleri", "1", "docs", "C", "Açık"),
            ("CAMeL Tools + Farasa + AraBERT/CAMeLBERT", "Arapça NLP Paketi", "CAMeL Lab vd.", "Şamile satır analizi", "1", "docs", "C", "Açık — kritik"),
            ("Zemberek + İTÜ NLP + Turkish UD", "Türkçe NLP Paketi", "Zemberek / İTÜ / UD", "Ana dil köprüsü", "1", "docs+veri", "C", "Açık — kritik"),
            ("Universal Dependencies guidelines + tools", "Evrensel Bağımlılıklar", "UD", "Morph/syntax camı", "1", "docs", "C", "Açık"),
            ("spaCy + stanza multilingual pipelines", "spaCy / Stanza", "Explosion / Stanford", "Dil boru hattı", "1", "docs", "C", "Açık"),
            ("TBX / TermBase eXchange özet + FreeTerm", "Terim Bankası", "ISO/LISA özet", "İlim terim camı", "1", "spec özet", "C", "Açık"),
            ("OmegaT + Okapi Framework docs", "CAT Çevirmen Tezgâhı", "OmegaT / Okapi", "İnsan+makine köprü", "1", "docs", "C", "Açık"),
            ("OPUS corpus + parallel data ethics", "Paralel Derlem", "OPUS", "Çeviri yakıtı", "1", "docs", "C", "Açık"),
            ("Morphology analyzers TR/AR (açık)", "Biçimbirim Çözümleyici", "açık araçlar", "Klasik satır morph", "1", "docs", "C", "Açık"),
            ("StarDict / DSL / dictd formats", "Sözlük Formatları", "açık", "Çift dilli vitrin", "1", "docs", "C", "Açık"),
            ("WebVTT / SRT / ASS subtitle + çeviri", "Altyazı Çeviri", "W3C / açık", "Ses+video köprüsü", "1", "spec", "C/D", "Açık"),
            ("BLEU / chrF / COMET eval docs", "Çeviri Kalite Ölçümü", "açık metrikler", "Yalansız çeviri sınavı", "1", "docs", "C", "Açık"),
            ("Classical text layering (metin-kritik açık)", "Klasik Metin Katmanları", "açık filoloji", "Meal/şerh/asıl cam", "1", "seçme", "C", "Açık — kritik"),
            ("Bilingual concordance açık araçlar", "Çift Dilli Konkordans", "açık", "Satır satır karşılaştır", "1", "docs", "C", "Açık"),
            ("Transliteration schemes (IJMES/ALA-LC açık)", "Çeviriyazı Şemaları", "Library of Congress vd.", "Arapça→Latin köprü", "1", "rehber", "C", "Açık"),
            ("Gloss / interlinear text açık standartlar", "Satıraltı Gloss", "açık", "Öğretici dil camı", "1", "rehber", "C", "Açık"),
            ("Pivot translation açık yazılar (TR↔AR↔EN)", "Üçlü Dil Köprüsü", "açık", "Rüzgar dil üçgeni", "1", "yazı", "C", "Açık"),
            ("Quality estimation (QE) açık modeller", "Çeviri Kalite Tahmini", "HF açık", "Kötü çeviriyi işaretle", "1", "docs", "C", "Açık"),
            ("Human-in-the-loop MT açık UX yazıları", "İnsan Onaylı Çeviri", "açık", "Cam katmanı onaylı", "1", "yazı", "C", "Açık"),
        ],
    ),
    "05_D_VIDEO_GOZ": (
        "05 D DALGA — VIDEO (GÖZ / HİKÂYE)",
        [
            ("Computer Vision: Algorithms and Applications", "Bilgisayarlı Görü", "Richard Szeliski", "Göz teorisi omurgası", "1", "~800+", "D", "Ücretsiz — kritik"),
            ("OpenCV Tutorials + dnn module", "OpenCV", "OpenCV", "Görüntü/video pratik", "1", "docs — geniş", "D", "Açık — kritik"),
            ("FFmpeg docs + encoding guide + filters", "FFmpeg", "FFmpeg", "Film/render kuyruğu", "1", "docs — geniş", "D", "Açık — kritik"),
            ("OpenTimelineIO + Adaptive docs", "OpenTimelineIO", "ASWF", "Yönetmen timeline", "1", "docs", "D", "Açık — kritik"),
            ("OpenColorIO + OpenEXR docs", "OCIO / OpenEXR", "ASWF", "Renk + HDR kare", "2", "docs", "D", "Açık"),
            ("OBS Studio + Advanced Scene Switcher docs", "OBS Studio", "OBS", "Kayıt / sahne kompozit", "1", "docs", "D", "Açık"),
            ("WebRTC MDN + samples + insertable streams", "WebRTC", "W3C / MDN", "Canlı cam / dünya penceresi", "1", "docs", "D", "Açık"),
            ("Godot Camera3D / AnimationPlayer / MovieWriter", "Godot Film", "Godot", "Sahneyi filme al", "1", "docs", "D", "Açık — kritik"),
            ("Three.js / Babylon render + recorder", "Web 3D Çekim", "Three / Babylon", "Web sahne kayıt", "1", "docs", "D", "Açık"),
            ("Kdenlive + Shotcut + Olive docs", "Açık Video Editörleri", "Kdenlive vd.", "Kes-birleştir masası", "1", "docs", "D", "Açık"),
            ("Blender VSE + Grease Pencil docs (çekirdek)", "Blender Video / Çizim", "Blender", "Ağır üretim (istersen)", "1", "docs", "D", "Açık"),
            ("WhisperX / soft-sub pipeline tarifleri", "Konuşma→Altyazı", "açık tarif", "Ders filmi altyazı", "1", "yazı", "D/B", "Açık"),
            ("ImageMagick + libvips + Pillow docs", "Görüntü Boru Hattı", "IM / libvips", "Kare işleme", "1", "docs", "D", "Açık"),
            ("Lottie + SVG SMIL/CSS animation", "Hareketli Grafik", "Lottie / MDN", "Kısa ders animasyonu", "1", "docs", "D", "Açık"),
            ("Manim Community + plugins", "Manim", "Manim", "Matematik ders filmi", "1", "docs", "D/G", "Açık"),
            ("Dramatiq/RQ + FFmpeg job tarifleri", "Gece Render Kuyruğu", "Dramatiq/RQ", "Sabaha mp4", "1", "docs", "D/F", "Açık — kritik"),
            ("SRT / VTT / ASS + ffmpeg subtitles", "Altyazı Formatları", "açık", "Çok dil altyazı", "1", "spec", "D/C", "Açık"),
            ("Electron desktopCapturer + MediaRecorder", "Ekran Yakalama", "Electron / MDN", "Arşiv / ders kayıt", "1", "docs", "D", "Resmi"),
            ("CLIP / open_clip / SigLIP docs", "Görür-Anlar (yazılım)", "OpenCLIP", "Kareyi metinle anla", "1", "docs", "D", "Açık — kritik"),
            ("Segment Anything (SAM) açık docs", "SAM Segmentasyon", "Meta", "Sahne nesne kes", "1", "docs", "D", "Açık"),
            ("MediaPipe / OpenPose açık (seçme)", "Poz / El İskeleti", "Google / açık", "İnsan hareketi (yasal)", "1", "docs", "D", "Açık"),
            ("CC0 / Pexels-benzeri açık asset etik rehberi", "Yasal Medya Asset", "açık rehber", "Cam/dünya yasal içerik", "1", "rehber", "D", "Açık"),
            ("yt-dlp yasal kullanım + kendi arşiv notu", "İzinli Medya Notu", "yt-dlp / hukuk", "Yalnız izinli kaynak", "1", "not", "D", "Dikkat — yasal"),
            ("Color grading açık (Lift-Gamma-Gain yazıları)", "Renk Düzenleme", "açık", "Film dili", "1", "yazı", "D", "Açık"),
            ("Storyboard / shot list açık şablonlar", "Storyboard Şablon", "açık", "Ders filmi planı", "1", "şablon", "D", "Açık"),
            ("HDR / tone-mapping açık yazılar", "HDR / Tone Map", "açık", "Sahne ışık gerçekliği", "1", "yazı", "D", "Açık"),
            ("Scenedetect / PySceneDetect docs", "Sahne Kes Tespiti", "PySceneDetect", "Otomatik kesim", "1", "docs", "D", "Açık"),
            ("Live streaming protocols (RTMP/SRT) açık", "Canlı Yayın Protokol", "açık", "İsteğe bağlı cam yayın", "1", "docs", "D", "Açık"),
        ],
    ),
    "06_E_MIMAR_ORKESTRA": (
        "06 E DALGA — MİMAR (ORKESTRA / DÜZEN)",
        [
            ("Architecture of Open Source Applications I–II", "Açık Kaynak Mimari", "AOSA", "Gerçek sistem okuma", "2", "~600+/cilt", "E", "Açık — kritik"),
            ("500 Lines or Less", "500 Satır veya Daha Az", "AOSA", "Küçük organ anatomisi", "1", "~400+", "E", "Açık"),
            ("Software Engineering at Google", "Google Yazılım Müh.", "Winters et al.", "Büyük düzen kültürü", "1", "~600", "E", "Açık"),
            ("Google SRE Book + Workbook", "SRE Kitap + Çalışma", "Google", "Güvenilirlik / gece demiri", "2", "~900+", "E", "Açık — kritik"),
            ("C4 Model docs + Structurizr DSL (açık)", "C4 Model", "Simon Brown", "Tek şemada Rüzgar evi", "1", "docs", "E", "Açık — kritik"),
            ("arc42 template + examples", "arc42", "arc42", "Mimari dokümantasyon", "1", "docs", "E", "Açık"),
            ("FastAPI + Starlette + Pydantic docs", "FastAPI Yığını", "tiangolo", "desktop_server omurgası", "1", "docs", "E", "Açık — kritik"),
            ("Uvicorn / Gunicorn / Hypercorn ops docs", "ASGI Sunucu", "encode / açık", "Servis koşumu", "1", "docs", "E", "Açık"),
            ("Electron process model + security checklist", "Electron Güvenlik", "Electron", "Masaüstü ev güvenliği", "1", "docs", "E", "Resmi — kritik"),
            ("JSON-RPC 2.0 + OpenAPI 3 + AsyncAPI", "Motor Sözleşme Spec", "jsonrpc / OpenAPI", "Motor bus sözleşmesi", "3", "spec", "E", "Açık — kritik"),
            ("JSON Schema + TypeBox + Zod docs", "Şema Doğrulama", "JSON Schema vd.", "Komut/izin şema", "1", "docs", "E/F", "Açık"),
            ("OPA / Rego + Cedar (AWS açık?) policy docs", "Policy as Code", "OPA / Cedar", "Fren kuralları kodda", "1", "docs", "E", "Açık — kritik"),
            ("STRIDE / PASTA threat modeling açık rehber", "Tehdit Modelleme", "Microsoft/OWASP", "Güvenli düzen", "1", "rehber", "E", "Açık"),
            ("NATS / ZeroMQ / Redis Streams docs", "Mesaj Otobüsü", "NATS/ZMQ/Redis", "Motorlar arası IPC", "1", "docs", "E", "Açık — kritik"),
            ("Twelve-Factor + Azure/AWS well-architected (çekirdek)", "İyi Mimari Çerçeve", "Heroku / bulut açık", "Servis disiplini", "1", "docs", "E", "Açık"),
            ("DDD Quickly + event storming açık", "DDD / Olay Fırtınası", "InfoQ / açık", "Alan sınırları", "1", "~100+", "E", "Ücretsiz"),
            ("OpenTelemetry + Prometheus + Grafana", "Gözlem Orkestrası", "CNCF / Grafana", "Sağlık panosu", "1", "docs", "E", "Açık — kritik"),
            ("Feature flags (Unleash / GrowthBook docs)", "Özellik Bayrakları", "Unleash / GrowthBook", "Sırayla aç-kapa", "1", "docs", "E", "Açık"),
            ("ADR templates (MADR) + RFCs iç süreç", "Mimari Karar Kayıtları", "MADR", "Neden böyle karar", "1", "şablon", "E", "Açık"),
            ("Scene graph / ECS mimari yazıları", "Sahne Grafiği / ECS", "Bevy/Godot yazılar", "Tiyatro binası iskeleti", "1", "seçme", "E", "Açık"),
            ("Capability security + object-capability özet", "Yeteneğe Dayalı Güvenlik", "açık papers", "Güçlü el + kapı", "1", "özet", "E", "Açık"),
            ("Circuit breaker / bulkhead açık tarifler", "Dayanıklılık Kalıpları", "açık", "Motor çökünce ev ayakta", "1", "yazı", "E", "Açık"),
            ("Backpressure / queue design açık yazılar", "Geri Basınç / Kuyruk", "açık", "Orkestra tıkanmasın", "1", "yazı", "E", "Açık"),
            ("Workspace information architecture seçkisi", "Bilgi Mimarisi", "açık UX", "Odalar/kapılar düzeni", "1", "seçme", "E", "Açık"),
            ("Dependency governance + SBOM (Syft) docs", "Bağımlılık Yönetimi", "Syft", "Ev paket envanteri", "1", "docs", "E", "Açık"),
            ("Versioned config (dynaconf/pydantic-settings)", "Sürümlü Yapılandırma", "açık", "Ortam düzeni", "1", "docs", "E", "Açık"),
            ("Runbook / playbook şablonları (SRE)", "Çalıştırma Kitapçığı", "SRE açık", "Bozulunca ne yapılır", "1", "şablon", "E", "Açık"),
            ("Multi-window Electron + BrowserView güvenlik", "Çok Pencere Düzeni", "Electron", "Sahne+atölye düzeni", "1", "docs", "E", "Resmi"),
        ],
    ),
    "07_F_PROGRAMLAMA_USTA": (
        "07 F DALGA — PROGRAMLAMA (USTA / CURSOR KARDEŞİ)",
        [
            ("Crafting Interpreters", "Yorumlayıcılar İnşa Etmek", "Robert Nystrom", "Organ fabrikası dil temeli", "1", "~600+", "F", "Ücretsiz — kritik"),
            ("Build Your Own Lisp / Writing Interpreter Go açık port", "Dil İnşa Pratik", "Holden / açık port", "Mini DSL organı", "1", "~200+", "F", "Açık"),
            ("tree-sitter docs + query + grammars", "tree-sitter", "tree-sitter", "Kod ağacı / repo aklı", "1", "docs", "F", "Açık — kritik"),
            ("Language Server Protocol + VS Code LSP samples", "LSP", "Microsoft", "Tanım/sembol/refactor", "1", "spec+docs", "F", "Açık — kritik"),
            ("Monaco Editor + CodeMirror 6 docs", "Kod Editör Yüzü", "Microsoft / CM", "Atölye kod yüzü", "1", "docs", "F", "Açık"),
            ("Playwright + trace viewer docs", "Playwright", "Microsoft", "UI smoke / yalansız oldu", "1", "docs", "F", "Açık — kritik"),
            ("pytest + Hypothesis + coverage.py", "Python Test Paketi", "pytest / Hypothesis", "Birim+özellik testi", "1", "docs", "F", "Açık — kritik"),
            ("unittest + tox + nox docs", "Test Matrisi", "Python / tox", "Çok ortam sınavı", "1", "docs", "F", "Açık"),
            ("Pro Git + Git internals docs", "Git Ustalık", "Chacon / Git", "Diff/commit/branch eli", "1", "~500+docs", "F", "Açık — kritik"),
            ("unified diff / patch / git apply", "Yama Araçları", "GNU / Git", "Dosyaya cerrahi yama", "1", "docs", "F", "Açık"),
            ("JSON-RPC tool-calling + OpenAI-compatible tools şema", "Araç Çağırma Şeması", "açık", "Söz→araç döngüsü", "1", "tarif+spec", "F", "Açık — kritik"),
            ("ReAct / Toolformer / Agent papers (açık)", "Ajan Döngüsü Makaleleri", "Yao et al. vd.", "Planla→yap→gözle→düzelt", "1", "makale seti", "F", "Açık — kritik"),
            ("seccomp / Landlock / Bubblewrap / Firejail docs", "Linux Sandbox", "kernel / açık", "Güvenli güç", "1", "docs", "F", "Açık — kritik"),
            ("Wasmtime / WASI / Component Model docs", "Wasm İzole Koşum", "Bytecode Alliance", "Mini organ güvenli koşsun", "1", "docs", "F", "Açık"),
            ("Podman / Docker rootless docs", "Konteyner İzolasyon", "Podman/Docker", "Tehlikeli iş kapalı kutu", "1", "docs", "F", "Açık"),
            ("RQ / Dramatiq / Celery / Huey docs", "İş Kuyruğu", "RQ/Dramatiq", "Gece onarım/üretim", "1", "docs", "F", "Açık — kritik"),
            ("LibCST / Rope / RedBaron docs", "Python AST Refaktör", "LibCST / rope", "Cerrah onarım", "1", "docs", "F", "Açık"),
            ("ripgrep + semgrep + ast-grep docs", "Kod Avı Paketi", "rg / Semgrep / ast-grep", "Projede bul-düzelt", "1", "docs", "F", "Açık — kritik"),
            ("Ollama / llama.cpp tool calling + grammar", "Yerel Araçlı Beyin", "Ollama/ggml", "Usta+yerel model", "1", "docs", "F", "Açık"),
            ("lm-eval-harness + kendi Rüzgar sınav tarifleri", "Usta Sınav Harness", "EleutherAI / Rüzgar", "Oldu mu? ölç", "1", "docs", "F", "Açık — kritik"),
            ("MIT Missing Semester", "Eksik Dönem", "MIT", "Shell/git/debug aletleri", "1", "kurs", "F", "Açık"),
            ("OWASP ASVS + Cheat Sheets (dev)", "Güvenli Organ", "OWASP", "Organ güvenli doğsun", "1", "docs", "F", "Açık"),
            ("SemVer + Keep a Changelog + Conventional Commits", "Sürüm Disiplini", "SemVer / açık", "Organ sürümü net", "1", "spec", "F", "Açık"),
            ("Debug protocols (DAP) specification", "Debug Adapter Protocol", "Microsoft", "Adım adım debug", "1", "spec", "F", "Açık"),
            ("Watchdog / file notify (watchfiles) docs", "Dosya İzleme", "watchfiles", "Değişince test koş", "1", "docs", "F", "Açık"),
            ("Snapshot testing açık (syrupy/jest benzeri py)", "Snapshot Test", "açık", "Çıktı bozulmasın", "1", "docs", "F", "Açık"),
            ("Property-based + fuzz (Atheris/Hypothesis)", "Fuzz / Property", "Hypothesis/Atheris", "Kenar vaka avı", "1", "docs", "F", "Açık"),
            ("Editable installs / hatch / uv docs", "Modern Python Paket", "uv / hatch", "Organ paketleme", "1", "docs", "F", "Açık"),
            ("Prompt-to-diff güvenli tarif (izinli repo)", "Sözden Diff", "açık agent tarif", "Atölye ürünü", "1", "tarif", "F", "Açık"),
            ("Pair-programming UX açık yazılar (editor+chat)", "Çift Usta UX", "açık", "Sohbet|kod|önizleme", "1", "yazı", "F", "Açık"),
            ("Mutation testing (mutmut) docs", "Mutasyon Testi", "mutmut", "Testler gerçek mi", "1", "docs", "F", "Açık"),
            ("CI local (act / pre-commit) docs", "Yerel CI", "nektos/act / pre-commit", "Push etmeden sınav", "1", "docs", "F", "Açık"),
        ],
    ),
    "08_YEREL_AKIL_YAZILIM": (
        "08 YEREL AKIL (YAZILIM — donanım değil)",
        [
            ("Ollama docs + Modelfile + API", "Ollama", "Ollama", "Yerel beyin runtime", "1", "docs", "Akıl", "Açık — kritik"),
            ("llama.cpp / ggml / GGUF / llama-server", "llama.cpp", "ggerganov", "Yerel çıkarım motoru", "1", "docs", "Akıl", "Açık — kritik"),
            ("llamafile docs", "llamafile", "Mozilla", "Tek-binary beyin", "1", "docs", "Akıl", "Açık"),
            ("vLLM / TGI / text-generation-inference docs", "Yerel Sunucu Yığını", "vLLM / HF", "Hızlı sunucu (RAM sonra rahatlar)", "1", "docs", "Akıl", "Açık"),
            ("Hugging Face Transformers + Hub model cards", "HF Transformers / Kartlar", "Hugging Face", "Model seç-yükle bilinci", "1", "docs", "Akıl", "Açık — kritik"),
            ("PEFT / LoRA / QLoRA / DoRA docs+papers", "İnce Ayar Paketi", "HF", "Üslup/ilim ince ayar", "1", "docs+makale", "Akıl", "Açık — kritik"),
            ("TRL / Axolotl / LLaMA-Factory docs (seçme)", "İnce Ayar Araçları", "HF / açık", "Eğitim tezgâhı", "1", "docs", "Akıl", "Açık"),
            ("llama.cpp grammar / json-schema / Mirostat", "Kısıtlı Üretim", "llama.cpp", "Şema-tutarlı cevap", "1", "docs", "Akıl", "Açık"),
            ("Sentence-Transformers + multilingual embeddings", "Cümle Gömme", "UKPLab", "RAG isabeti", "1", "docs", "Akıl", "Açık — kritik"),
            ("bge-m3 / bge-reranker docs", "BGE Gömme/Rerank", "BAAI", "TR+çokdil retrieval", "1", "docs", "Akıl", "Açık"),
            ("RAGAS + BEIR + MTEB", "Akıl/RAG Sınavları", "açık bench", "Kalite ölçümü", "1", "docs", "Akıl", "Açık — kritik"),
            ("lm-evaluation-harness + Open LLM Leaderboard yöntem", "Genel Model Sınavı", "EleutherAI", "Beyin kıyas", "1", "docs", "Akıl", "Açık"),
            ("Chat template / tokenizer docs (HF)", "Sohbet Şablonu", "HF", "Model doğru konuşsun", "1", "docs", "Akıl", "Açık"),
            ("Multi-model router tarifleri (hızlı/derin/kod)", "Çok Beyin Yönlendirici", "Rüzgar + açık", "İşe göre beyin seç", "1", "tarif", "Akıl", "Açık — kritik"),
            ("Semantic cache açık yazılar + Redis/SQLite cache", "Anlamsal Önbellek", "açık", "Aynı soru kotayı yakmasın", "1", "yazı+docs", "Akıl", "Açık — kritik"),
            ("Quota-aware cloud fallback (iç tasarım notu)", "Kota Bilinçli Bulut Yedek", "Rüzgar", "Bulut açık ama ekmek yerel", "1", "tasarım", "Akıl", "İç — kritik"),
            ("Offline model update / GGUF checksum checklist", "Model Güncelleme Listesi", "açık", "USB ile beyin taşı", "1", "liste", "Akıl", "Açık"),
            ("LLaVA / InternVL / open VLM docs", "Yerel VLM", "açık VLM", "Görür-anlar yazılım yolu", "1", "docs", "Akıl/D", "Açık"),
            ("Llama-Guard / Nemo Guardrails / regex policy", "Güvenli Üretim Rayı", "açık guard", "Fren+akıl", "1", "docs", "Akıl", "Açık"),
            ("Speculative decoding / draft-target açık notlar", "Spekülatif Çıkarım", "açık", "Hız (yazılım hilesi)", "1", "yazı", "Akıl", "Açık"),
            ("GGUF quant cheatsheet (Q4/Q5/Q8)", "Niceleme Rehberi", "açık", "Hangi kalite/ hız", "1", "rehber", "Akıl", "Açık"),
            ("Turkish LLM açık model kartları + eval notları", "Türkçe Yerel Modeller", "HF TR kartlar", "Ana dil beyni", "1", "kartlar", "Akıl", "Açık — kritik"),
            ("Arabic LLM açık kartlar (Şamile dili)", "Arapça Yerel Modeller", "HF AR kartlar", "Şamile dili beyni", "1", "kartlar", "Akıl", "Açık — kritik"),
            ("Distillation / small model açık tarifler", "Küçük Beyin Damıtma", "açık", "Hızlı yedek beyin", "1", "yazı", "Akıl", "Açık"),
            ("Prompt library + system policy versioning (iç)", "Politika/Prompt Sürümü", "Rüzgar", "Rüzgar ağzı kilitli sürüm", "1", "şema", "Akıl", "İç"),
            ("Function/tool schema catalog (iç motor araçları)", "Araç Kataloğu", "Rüzgar", "Usta+beyin ortak dil", "1", "katalog", "Akıl/F", "İç"),
            ("Continual learning / memory-augmented açık survey", "Sürekli Öğrenme Survey", "akademik açık", "Öğretince unutmasın", "1", "survey", "Akıl/A", "Açık"),
            ("Eval set oluşturma rehberi (Rüzgar sınavları)", "Kendi Sınav Seti Rehberi", "Rüzgar + açık", "Ümit abi öğretti mi ölç", "1", "rehber", "Akıl", "İç+açık"),
        ],
    ),
    "09_WEB_KOTA_HIBRIT": (
        "09 WEB + KOTA HİBRİT (web açık — ekmek yerel)",
        [
            ("HTTP Caching RFC 9111 + heuristic caching yazıları", "HTTP Önbellek", "IETF", "Web cevabını yerelde tut", "1", "RFC+yazı", "Web", "Kamu — kritik"),
            ("Cache-Control / ETag pratik rehber", "Önbellek Pratik", "MDN", "Tekrar istek yakma", "1", "docs", "Web", "Açık"),
            ("Trafilatura + Readability + Goose3 docs", "İçerik Çıkarıcı Paketi", "Trafilatura vd.", "Sayfadan temiz metin", "1", "docs", "Web", "Açık — kritik"),
            ("Mozilla Readability + reader-mode yazıları", "Okuyucu Modu", "Mozilla", "Gürültüsüz web şeridi", "1", "yazı", "Web", "Açık"),
            ("RSS / Atom / JSON Feed specs", "Besleme Spec", "IETF / JSON Feed", "Güncel abonelik", "1", "spec", "Web", "Kamu — kritik"),
            ("Feedparser / Miniflux docs", "RSS Okuyucu", "feedparser / Miniflux", "Yerel haber kutusu", "1", "docs", "Web", "Açık"),
            ("robots.txt + Crawl-delay etik + IETF AI prefs (takip)", "Tarama Etiği", "açık / IETF", "Web'i nazik kullan", "1", "rehber", "Web", "Açık"),
            ("rate limit / token bucket / exponential backoff", "Kota / Retry Disiplini", "açık tarif", "Bulut kotasını eritme", "1", "tarif", "Web", "Açık — kritik"),
            ("API gateway pattern + quota ledger (iç şema)", "Kota Defteri Şeması", "Rüzgar", "Kaç çağrı kaldı bil", "1", "şema", "Web", "İç — kritik"),
            ("Electron safeStorage + OS keychain docs", "Anahtar Kasası", "Electron", "API anahtarı güvenli", "1", "docs", "Web", "Resmi"),
            ("Gemini API docs (yedek yol)", "Gemini API", "Google", "Geniş zekâ yedek — kota bilinçli", "1", "docs", "Web", "Resmi yedek"),
            ("Groq API docs (yedek yol)", "Groq API", "Groq", "Hızlı bulut yedek", "1", "docs", "Web", "Resmi yedek"),
            ("OpenAI-compatible local+cloud router yazıları", "Uyumluluk Yönlendirici", "açık", "Aynı şema yerel/bulut", "1", "yazı", "Web", "Açık"),
            ("Provider failover + circuit breaker tarif", "Sağlayıcı Yedekleme", "açık", "Biri kotada→öbürü", "1", "tarif", "Web", "Açık — kritik"),
            ("Local-first (Ink & Switch) essays", "Local-first Yazılar", "Ink & Switch", "Ekmek yerel, web ziyafet", "1", "yazı seti", "Web", "Açık — kritik"),
            ("URL allowlist / blocklist politika şablonu", "Web İzin Listesi", "Rüzgar", "Niyet-web ama kapılı kapı", "1", "şablon", "Web", "İç"),
            ("WARC / wget / HTTrack etik arşiv", "Web Arşivleme", "IIPC / wget", "Önemli sayfayı yerelleştir", "1", "docs", "Web", "Açık"),
            ("SingleFile / archivebox docs", "Sayfa Dondurucu", "ArchiveBox / SingleFile", "Kanıtlı web kopyası", "1", "docs", "Web", "Açık"),
            ("Web kaynak kartı JSON şema (iç)", "Web Kaynak Kartı", "Rüzgar", "Şerit künyeli gelsin", "1", "şema", "Web", "İç — kritik"),
            ("S4 niyet-web kural özeti (Ümit emri)", "S4 Niyet-Web", "Rüzgar", "Canlıda web; ansiklopedide yerel", "1", "kural", "Web", "İç — kilit"),
            ("CDN mirror / hash-pinning yazıları", "Ayna / Hash Pin", "açık", "İndirme bütünlüğü", "1", "yazı", "Web", "Açık"),
            ("Privacy: no telemetry + consent UX açık", "Telemetrisiz İstemci", "açık ilkeler", "Web açık olsa da mahrem", "1", "ilke", "Web", "Açık"),
            ("DNS-over-HTTPS seçimli + Unbound (opsiyon)", "DNS Bilinci", "açık", "Ağ mahremi (isteğe)", "1", "docs", "Web", "Açık"),
            ("Cost/latency SLOs açık yazılar", "Maliyet / Gecikme SLO", "açık", "Ne zaman bulut, ne zaman yerel", "1", "yazı", "Web", "Açık"),
            ("Browser fetch hygiene (timeout/size cap)", "İstek Hijyeni", "açık", "Dev sayfa felç etmesin", "1", "tarif", "Web", "Açık"),
            ("Sitemap / feed discovery açık", "Kaynak Keşfi", "açık", "İyi kaynağı bul", "1", "yazı", "Web", "Açık"),
        ],
    ),
    "10_G_FENNI": (
        "10 G — FENNİ KÜLLİYAT (sahne ders yakıtı)",
        [
            ("OpenStax Calculus Vol 1–3", "OpenStax Kalkülüs", "OpenStax", "Matematik ders omurgası", "3", "~1000+/set", "G", "CC — kritik"),
            ("OpenStax Algebra/Trig/Precalculus", "OpenStax Cebir Paketi", "OpenStax", "Temel matematik", "2", "~1500+/set", "G", "CC"),
            ("OpenStax University Physics 1–3", "OpenStax Üniversite Fiziği", "OpenStax", "Fizik sahne", "3", "~1500+/set", "G", "CC — kritik"),
            ("OpenStax College Physics + Astronomy", "Kolej Fizik + Astronomi", "OpenStax", "Uzay/giriş fizik", "2", "~2000+/set", "G", "CC"),
            ("OpenStax Chemistry 2e + Biology 2e (giriş)", "Kimya / Biyoloji Giriş", "OpenStax", "Fen odası (silahsız)", "2", "~2000+/set", "G", "CC — dikkatli"),
            ("OpenStax Economics + Statistics + Psychology", "Ekonomi/İstat/Psikoloji", "OpenStax", "Toplum+ölçü+bellek", "3", "~2000+/set", "G", "CC"),
            ("MIT 6.042 Mathematics for Computer Science", "CS için Matematik", "MIT", "Kanıt tahtası", "1", "~500+", "G", "Açık — kritik"),
            ("Book of Proof + Discrete Math (Levin)", "İspat + Ayrık", "Hammack / Levin", "Mantık omurgası", "2", "~700+", "G", "Açık"),
            ("Interactive Linear Algebra + 3B1B scripts", "Lineer Cebir Paketi", "Georgia Tech / 3B1B", "Görsel matematik", "1", "kitap+script", "G", "Açık"),
            ("Feynman Lectures (açık HTML)", "Feynman Dersleri", "Caltech", "Derin fizik sezgi", "3", "HTML", "G", "Açık"),
            ("Motion Mountain + Light and Matter", "Açık Fizik Kitapları", "Schiller / Crowell", "Ücretsiz fizik gövdesi", "2", "~2000+/set", "G", "Ücretsiz"),
            ("HyperPhysics", "HyperPhysics", "Georgia State", "Kavram ağı", "1", "ansiklopedi", "G", "Eğitim"),
            ("Information Theory Inference Learning (MacKay)", "Bilgi Teorisi MacKay", "David MacKay", "Bilgi+öğrenme", "1", "~600+", "G/B", "Ücretsiz"),
            ("ISLR2 + ESL (istatistik öğrenme)", "İstatistiksel Öğrenme", "James / Hastie", "Veri bilimi dersi", "2", "~1300+", "G/B", "Ücretsiz PDF"),
            ("SymPy + NumPy + SciPy + Matplotlib docs", "Hesap / Çizim Yığını", "SciPy ekosistemi", "Sahne hesabı+grafik", "1", "docs", "G", "Açık — kritik"),
            ("Manim Community + plugins", "Manim", "Manim", "Canlı matematik tahtası", "1", "docs", "G", "Açık — kritik"),
            ("MapLibre + Natural Earth + OSM + Protomaps", "Coğrafya Paketi", "MapLibre / NE / OSM", "Harita sahne", "1", "docs+veri", "G", "Açık — kritik"),
            ("Astropy + Skyfield docs", "Astronomi Hesap", "Astropy / Skyfield", "Uzay odası hesabı", "1", "docs", "G", "Açık"),
            ("PhET HTML5 sims (açık lisans kontrol)", "PhET Simülasyonlar", "University of Colorado", "Etkileşimli fen", "1", "sim seti", "G", "Lisans kontrol"),
            ("MIT OCW 8.01/8.02/6.0001 seçme", "MIT OCW Fen/CS Giriş", "MIT OCW", "Üniversite ders yakıtı", "1", "kurs", "G", "OCW"),
            ("Khan Academy açık lisans içerik politikası + seçme", "Khan Seçme (yasal)", "Khan Academy", "Yalnız izinli parça", "1", "seçme", "G", "Lisans kontrol"),
            ("Chemistry LibreTexts / Physics LibreTexts seçme", "LibreTexts Fen", "LibreTexts", "Açık fen gövdesi", "1", "seçme", "G", "Açık"),
            ("History of science kamu malı klasikler (seçme)", "Bilim Tarihi Klasikleri", "kamu malı", "Tarih+fen köprüsü", "1", "seçme", "G", "Kamu malı"),
            ("Measurement / units (UCUM) docs", "Ölçü Birimleri", "UCUM", "Sahne ölçü dili", "1", "docs", "G", "Açık"),
        ],
    ),
    "11_FREN_ONAY_DENETIM": (
        "11 FREN — ONAY / DENETİM / GÜVENLİ GÜÇ",
        [
            ("OWASP ASVS + Top 10 + Cheat Sheets + SAMM", "OWASP Paketi", "OWASP", "Uygulama güvenlik omurgası", "1", "docs seti", "Fren", "Açık — kritik"),
            ("OWASP WSTG (PoC üretmeden çerçeve)", "OWASP Test Rehberi", "OWASP", "Savunma testi dili", "1", "docs", "Fren", "Açık — PoC yok"),
            ("Security Engineering (Anderson) online", "Güvenlik Mühendisliği", "Ross Anderson", "Savunma düşüncesi", "1", "~1000+", "Fren", "Ücretsiz online — kritik"),
            ("NIST CSF 2.0 + SP 800-53 seçme", "NIST Çerçeve", "NIST", "Kontrol dili", "1", "standart", "Fren", "Kamu"),
            ("MITRE ATT&CK + D3FEND (tespit/savunma)", "ATT&CK / D3FEND", "MITRE", "Tehdit haritası — exploit yok", "2", "bilgi tabanı", "Fren", "Açık"),
            ("OPA/Rego + policy-as-code examples", "Politika Kodu", "OPA", "Kapı kuralları kodda", "1", "docs", "Fren", "Açık — kritik"),
            ("Capability tokens / macaroons / biscuits açık", "Yetki Jetonları", "açık", "İnce taneli izin", "1", "docs", "Fren", "Açık"),
            ("Electron security tutorial + IPC isolation", "Electron Fren", "Electron", "Masaüstü saldırı yüzeyi", "1", "docs", "Fren", "Resmi — kritik"),
            ("CSP / Trusted Types MDN", "İçerik Güvenlik Politikası", "MDN", "XSS freni", "1", "docs", "Fren", "Açık"),
            ("Append-only audit log tarif + hash chain", "Denetim İzi", "açık", "Kim ne yaptı", "1", "tarif", "Fren", "Açık — kritik"),
            ("Consent UX + permission prompt patterns", "İzin / Onay UX", "açık", "Tehlikeli işte sor", "1", "seçme", "Fren", "Açık"),
            ("Secure coding CERT SEI (C/Java/Python seçme)", "CERT Güvenli Kod", "SEI CERT", "Organ güvenli", "1", "docs", "Fren", "Açık"),
            ("SLSA + OpenSSF Scorecard + Syft/Grype", "Tedarik Zinciri Freni", "OpenSSF", "Paket zehirlenmesin", "1", "docs", "Fren", "Açık"),
            ("Secrets management (age + sops docs)", "Sır Yönetimi", "age / sops", "Anahtar sızmasın", "1", "docs", "Fren", "Açık"),
            ("Threat modeling şablonları (STRIDE kartları)", "Tehdit Kartları", "açık", "Her organa tehdit bak", "1", "şablon", "Fren", "Açık"),
            ("Red-team vs blue-team etik sınır yazıları", "Etik Sınır", "açık", "Öğretim ≠ saldırı tarifi", "1", "yazı", "Fren", "Açık"),
            ("Rüzgar kapalı eylem listesi (iç politika)", "Kapalı Eylem Listesi", "Rüzgar", "Yapamam çünkü kural", "1", "politika", "Fren", "İç — kritik"),
            ("Human approval workflow (2-step confirm) tarif", "İki Adımlı Onay", "açık+iç", "Sil/gönder/çalıştır onayı", "1", "tarif", "Fren", "İç"),
            ("Sandbox escape literature özet (savunma)", "Sandbox Kaçış Özeti", "açık survey", "Fren deliklerini kapa", "1", "özet", "Fren", "Açık — savunma"),
            ("Privacy by design (ISO özet / GDPR ilkeler)", "Mahremiyet Tasarımı", "kamu/açık", "Varsayılan gizlilik", "1", "ilke", "Fren", "Açık"),
            ("Abuse reporting / kill-switch tarif", "Acil Durdur", "açık+iç", "Kaçmış işi kes", "1", "tarif", "Fren", "İç"),
            ("Least privilege + role matrix şablon", "En Az Yetki Matrisi", "açık", "Kim neye dokunur", "1", "şablon", "Fren", "Açık"),
        ],
    ),
    "12_GECE_YEDEK_URETIM": (
        "12 GECE DEMİRİ — KUYRUK / YEDEK / ÜRETİM",
        [
            ("Dramatiq docs + best practices", "Dramatiq", "Dramatiq", "Python iş kuyruğu", "1", "docs", "Gece", "Açık — kritik"),
            ("RQ / Celery / Huey / ARQ docs (karşılaştırma)", "Kuyruk Seçenekleri", "RQ/Celery/Huey/ARQ", "Gece işçi ailesi", "1", "docs", "Gece", "Açık"),
            ("systemd timers + cron + anacron docs", "Zamanlayıcılar", "systemd / cron", "Gece tetik", "1", "docs", "Gece", "Açık — kritik"),
            ("Google SRE — toil / automation chapters", "SRE Otomasyon", "Google SRE", "Gece demiri kültürü", "1", "bölüm", "Gece", "Açık"),
            ("Batch processing açık yazılar + idempotency", "Toplu İş / Idempotent", "açık", "İkinci kez çalışınca bozma", "1", "yazı", "Gece", "Açık — kritik"),
            ("FFmpeg gece render pipeline tarifleri", "Gece Film Boru", "FFmpeg + tarif", "Sabaha mp4", "1", "tarif", "Gece/D", "Açık"),
            ("RAG reindex / incremental index tarifleri", "Gece İndeks", "açık+iç", "Kütüphane gece yenilensin", "1", "tarif", "Gece/A", "İç+açık — kritik"),
            ("restic / borg / kopia backup docs", "Yedekleme Motorları", "restic/borg/kopia", "Ömür boyu yedek", "1", "docs", "Gece", "Açık — kritik"),
            ("ZFS / Btrfs snapshot açık rehberler", "Anlık Görüntü Yedek", "açık", "Dosya sistemi yedek", "1", "rehber", "Gece", "Açık"),
            ("Syncthing docs", "Syncthing", "Syncthing", "Cihazlar arası yedek", "1", "docs", "Gece", "Açık"),
            ("age / rclone crypt yedek şifreleme", "Yedek Şifreleme", "age / rclone", "Yedek okunmasın", "1", "docs", "Gece", "Açık"),
            ("Offline mirror: uv/pip cache + verdaccio docs", "Paket Aynası", "uv / verdaccio", "İnternet yokken kurulum", "1", "docs", "Gece", "Açık"),
            ("SBOM gece tarama (Grype) + rapor", "Gece Güvenlik Tarama", "Grype", "Zehirli paket uyarısı", "1", "docs", "Gece/Fren", "Açık"),
            ("Log rotation + structured logging (structlog)", "Log Düzeni", "structlog / açık", "Gece izi okunur kalsın", "1", "docs", "Gece", "Açık"),
            ("Dead letter queue + retry politikası tarif", "Ölü Mektup Kuyruğu", "açık", "Başarısız iş kaybolmasın", "1", "tarif", "Gece", "Açık"),
            ("Progress HUD / sabah brifing iş raporu şema", "Sabah İş Raporu", "Rüzgar", "Gece ne bitti söyle", "1", "şema", "Gece/A", "İç — kritik"),
            ("Model pull / GGUF verify gece işi", "Gece Model Bakım", "Ollama/llama.cpp", "Beyin güncelle (kota dışı USB de)", "1", "tarif", "Gece/Akıl", "Açık"),
            ("Database vacuum / SQLite optimize gece", "DB Bakım", "SQLite", "Hafıza şişmesin", "1", "docs", "Gece/A", "Resmi"),
            ("Thumbnail / preview generate kuyruğu", "Önizleme Üretimi", "açık tarif", "Sahne asset hazır", "1", "tarif", "Gece/D", "Açık"),
            ("Healthcheck + auto-restart (systemd) docs", "Sağlık / Yeniden Başlat", "systemd", "Düşeni kaldır", "1", "docs", "Gece/E", "Açık"),
            ("Disaster recovery runbook şablon", "Felaket Kurtarma", "açık şablon", "Yedekten dönüş", "1", "şablon", "Gece", "Açık"),
            ("Priority queues / fairness açık yazılar", "Öncelikli Kuyruk", "açık", "Önemli iş öne", "1", "yazı", "Gece", "Açık"),
            ("Air-gap sneakernet checklist", "Hava Boşluğu Taşıma", "açık", "USB ile güncelle (ileri)", "1", "liste", "Gece", "Açık"),
            ("Prometheus alerting rules örnekleri", "Gece Alarm", "Prometheus", "Bozulunca haber ver", "1", "docs", "Gece/E", "Açık"),
        ],
    ),
    "13_SAHNE_ODALARI_ILERI": (
        "13 İLERİ SAHNE ODALARI (A→F oturunca yakıt)",
        [
            ("Ömür koridoru — scene.json versioning tarif", "Ömür Koridoru Şema", "Rüzgar", "Yıllara göre hafıza odaları", "1", "şema", "Oda/A", "İç — kritik"),
            ("CRDT + timeline ECS yazıları", "Zaman Çizelgesi ECS", "açık", "Koridor+zaman sync", "1", "yazı", "Oda", "Açık"),
            ("Mahkeme-i kübra — delil kartı JSON Schema", "Delil Kartı Şema", "Rüzgar", "İlim mahkemesi vitrini", "1", "şema", "Oda/A", "İç — kritik"),
            ("Diff + provenance UI açık patternler", "Karşılaştırma Stüdyosu UX", "açık", "Kim ne demiş yüzü", "1", "seçme", "Oda", "Açık"),
            ("Dil camı — HarfBuzz+MT+TTS birleşik tarif", "Dil Camı Laboratuvarı", "açık+iç", "Satır morph+şerh+ses", "1", "tarif", "Oda/C", "İç+açık"),
            ("Coğrafya+tarih sync — MapLibre + timeline", "Harita-Tarih Sync", "MapLibre + açık", "Olay haritada yürüsün", "1", "tarif", "Oda/G", "Açık — kritik"),
            ("Tarih külliyatı açık atlas/kronoloji seçkisi", "Açık Kronoloji / Atlas", "açık/kamu", "Tarih koridoru yakıtı", "1", "seçme", "Oda", "Açık"),
            ("Uzay odası — Astropy + CC0 skybox rehberi", "Uzay Odası Paketi", "Astropy / CC0", "Orbital + gökyüzü", "1", "docs+rehber", "Oda/G", "Açık"),
            ("Atölye gece vardiyası — kod+test+render HUD", "Atölye Gece Vardiyası", "Rüzgar", "Usta+film kuyruk yüzü", "1", "şema", "Oda/F", "İç"),
            ("Brifing tahtı — sabah üç ip HUD", "Brifing Tahtı", "Rüzgar", "Sesle seçilecek ipler", "1", "şema", "Oda/A/B", "İç — kritik"),
            ("Güvenlik kapısı odası — kırmızı çerçeve UX", "Güvenlik Kapısı Odası", "Rüzgar + OWASP", "Tehlikeli iş tiyatrosu", "1", "UX+politika", "Oda/Fren", "İç"),
            ("Müze / eser vitrini — glTF + PDF.js birleşik", "Müze Vitrini", "glTF / PDF.js", "Eseri sahnede gezdir", "1", "tarif", "Oda", "Açık"),
            ("Hafıza sarayı spatialize (2D/3D oda grafı)", "Hafıza Sarayı Grafı", "açık+iç", "Kapıdan gir oda değiş", "1", "tarif", "Oda/A", "İç+açık"),
            ("Ders tahtası — Manim + Excalidraw + ses", "Ders Tahtası Kompozit", "Manim/Excalidraw", "Anlatırken çiz+konuş", "1", "tarif", "Oda", "Açık"),
            ("Cam/dünya penceresi — WebRTC + allowlist", "Dünya Penceresi", "WebRTC + politika", "Yasal canlı cam", "1", "tarif", "Oda/D/Web", "İç+açık"),
            ("Dil laboratuvarı — UD + gloss + audio align", "Dil Laboratuvarı", "UD / whisperX", "Dil öğrenme odası", "1", "tarif", "Oda/C/B", "Açık"),
            ("Kanıt zinciri animasyon (graph viz)", "Kanıt Zinciri Viz", "D3/ECharts", "Delil yağmuru görsel", "1", "docs", "Oda", "Açık"),
            ("VRM avatar + lipsync oda hostu", "Oda Hostu Avatar", "VRM", "Rüzgar yüzü odada", "1", "docs", "Oda", "Açık — kritik"),
            ("Multi-room portal UX açık yazılar", "Oda Portalları UX", "açık", "Odalar arası geçiş", "1", "yazı", "Oda", "Açık"),
            ("Scene save/load + undo stack tarif", "Sahne Kayıt / Geri Al", "açık+iç", "Odayı dondur/geri sar", "1", "tarif", "Oda", "İç"),
            ("Accessibility in spatial UI açık rehber", "Uzamsal UI Erişim", "açık", "Odalar herkese", "1", "rehber", "Oda", "Açık"),
            ("Soundscape per room tarif", "Oda Ses Manzarası", "WebAudio", "Her odanın nefesi", "1", "tarif", "Oda/B", "Açık"),
            ("Lighting / mood presets açık", "Oda Işık / Ruh Hali", "Godot/Three", "Atmosfer", "1", "docs", "Oda", "Açık"),
            ("Export oda→film / oda→pdf tarif", "Oda Dışa Aktarım", "FFmpeg/Pandoc", "Paylaşılabilir çıktı", "1", "tarif", "Oda", "Açık"),
        ],
    ),
    "14_MAHREM_MIRAS_PROFIL": (
        "14 MAHREM / MİRAS / ÇOK PROFİL",
        [
            ("WCAG 2.2 + WAI-ARIA APG", "Erişilebilirlik Omurgası", "W3C", "Herkes kullansın", "1", "standart", "Profil", "Açık — kritik"),
            ("Privacy by Design / GDPR ilkeleri kamu", "Mahremiyet İlkeleri", "AB / PbD", "Varsayılan gizlilik", "1", "ilke", "Profil", "Kamu — kritik"),
            ("ACM Code of Ethics + IEEE EAD", "Meslek Etiği", "ACM / IEEE", "Etik pusula", "2", "metin", "Profil", "Açık"),
            ("UNESCO AI Ethics recommendation", "UNESCO YZ Etiği", "UNESCO", "Küresel etik", "1", "metin", "Profil", "Kamu"),
            ("Multi-profile / multi-user UX açık yazılar", "Çok Profil UX", "açık", "Aile/mahrem ayrımı", "1", "yazı", "Profil", "Açık"),
            ("OS account isolation + Electron session partition", "Oturum İzolasyonu", "Electron / OS", "Profiller karışmasın", "1", "docs", "Profil", "Resmi"),
            ("Encrypted profile vault (age/SQLCipher) docs", "Profil Kasası", "age / SQLCipher", "Mahrem veri kilitli", "1", "docs", "Profil", "Açık — kritik"),
            ("Unutma / silme protokolü şablon (iç)", "Unutma Protokolü", "Rüzgar", "İste→sil→kanıtla", "1", "şablon", "Profil/A", "İç — kritik"),
            ("Digital inheritance / legacy contact açık rehberler", "Dijital Miras", "açık rehber", "Yarınlara emanet", "1", "rehber", "Profil", "Açık"),
            ("Family-friendly / child safety açık (COPPA özet kamu)", "Aile Güvenliği Özeti", "kamu özet", "Çocuk profili freni", "1", "özet", "Profil", "Kamu — dikkat"),
            ("Consent log + purpose limitation tarif", "Onay Günlüğü", "açık+iç", "Ne için veri tutuldu", "1", "tarif", "Profil", "İç"),
            ("Data export (portable JSON) şema", "Veri Taşınabilirliği", "Rüzgar", "Hafızanı al çık", "1", "şema", "Profil", "İç — kritik"),
            ("Differential privacy açık giriş (opsiyon)", "Ayırıcı Mahremiyet Giriş", "açık", "İstatistik sızdırmasın", "1", "yazı", "Profil", "Açık"),
            ("Local-only mode switch UX", "Salt Yerel Mod", "Rüzgar", "Web/bulut kapı tek düğme", "1", "UX", "Profil/Web", "İç"),
            ("Audit for guardians / öğretmen görünümü tarif", "Veli / Öğretmen Görünümü", "açık+iç", "Kontrollü şeffaflık", "1", "tarif", "Profil", "İç"),
            ("Noba / OpenStax ethics-of-tech seçme", "Teknoloji Etiği Okuma", "OpenStax/Noba", "İnsan odaklı", "1", "seçme", "Profil", "Açık"),
            ("Secure deletion / wipe açık rehber", "Güvenli Silme", "açık", "Silince gerçekten sil", "1", "rehber", "Profil", "Açık"),
            ("Profile themes / voice identity ayrımı", "Kimlik Ses+Tema", "Rüzgar", "Her profilin nefesi ayrı", "1", "şema", "Profil/B", "İç"),
            ("Shared library vs private shelf politika", "Ortak Raf / Özel Raf", "Rüzgar", "Kütüphane mahremi", "1", "politika", "Profil/A", "İç"),
            ("Incident response kişisel veri (CISA özet)", "Kişisel Veri Olayı", "CISA özet", "Sızınca ne yapılır", "1", "playbook", "Profil/Fren", "Kamu"),
        ],
    ),
}


def _safe_sheet(title: str) -> str:
    s = title
    for ch in r"\/:*?[]":
        s = s.replace(ch, "-")
    return (s.strip() or "KATEGORI")[:31]


def _safe_filename(title: str) -> str:
    s = title
    for ch in r'\/:*?"<>|':
        s = s.replace(ch, "-")
    return s.strip() or "KATEGORI"


def write_cat(folder: str, title: str, rows: list[tuple]) -> Path:
    out_dir = OUT_ROOT / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.xlsx"):
        try:
            old.unlink()
        except OSError:
            pass
    path = out_dir / f"{_safe_filename(title)}.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = _safe_sheet(title)
    ws["A1"] = (
        f"{title} — 2.PLAN+ MOTOR_DALGALARI_VE_USTA v2 GENİŞ · {len(rows)} eser · "
        f"Kapı: Şamile + 1.PLAN bitince · Web AÇIK (kota bilinçli) · "
        f"Donanım YOK · kategori karıştırılmaz"
    )
    ws["A1"].font = Font(name="Calibri", size=12, bold=True, color="C00000")
    ws.merge_cells("A1:I1")
    hf = Font(name="Calibri", size=11, bold=True)
    fill = PatternFill("solid", fgColor="E2EFDA")
    thin = Border(
        left=Side(style="thin", color="B0B0B0"),
        right=Side(style="thin", color="B0B0B0"),
        top=Side(style="thin", color="B0B0B0"),
        bottom=Side(style="thin", color="B0B0B0"),
    )
    for col, h in enumerate(HEADERS, 1):
        c = ws.cell(2, col, h)
        c.font = hf
        c.fill = fill
        c.border = thin
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for i, (orig, tr, yazar, katar, cilt, sayfa, dalga, not_) in enumerate(rows, 1):
        for col, v in enumerate([i, orig, tr, yazar, katar, cilt, sayfa, dalga, not_], 1):
            cell = ws.cell(2 + i, col, v)
            cell.border = thin
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for i, w in enumerate([6, 46, 42, 30, 52, 12, 16, 12, 26], 1):
        ws.column_dimensions[chr(64 + i)].width = w
    ws.freeze_panes = "A3"
    ws.auto_filter.ref = f"A2:I{2 + len(rows)}"
    note = wb.create_sheet("NOT")
    note["A1"] = (
        "2.PLAN+ MOTOR_DALGALARI_VE_USTA — v2 GENİŞ\n"
        "1.PLAN = Bilgisayar + Sahne.\n"
        "2.PLAN sıra: 01 Masa → 02A → 03B → 04C → 05D → 06E → 07F → "
        "08 Yerel akıl → 09 Web/kota → 10 Fenni → 11 Fren → 12 Gece → "
        "13 Sahne odaları → 14 Mahrem/miras.\n"
        "İyi model = yazılım beyni (Ollama); donanım bekler.\n"
        "Web kapalı değil; yerel ekmek, bulut kota bilinçli yedek.\n"
        "Kategorileri karıştırmayın."
    )
    note["A1"].alignment = Alignment(wrap_text=True)
    note.column_dimensions["A"].width = 110
    wb.save(path)
    return path


def main() -> int:
    if OUT_ROOT.exists():
        # Eski 10'lu yapı klasörlerini temizle, v2 ile yeniden kur
        for child in OUT_ROOT.iterdir():
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            elif child.suffix.lower() == ".xlsx":
                try:
                    child.unlink()
                except OSError:
                    pass
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    results = []
    total = 0
    for folder, (title, rows) in CATS.items():
        p = write_cat(folder, title, rows)
        results.append({"cat": folder, "rows": len(rows), "path": str(p)})
        total += len(rows)
    wb = Workbook()
    ws = wb.active
    ws.title = "OZET"
    ws.append(["NO", "KLASÖR / KATEGORİ", "ESER SAYISI", "DOSYA"])
    for i, r in enumerate(results, 1):
        ws.append([i, r["cat"], r["rows"], Path(r["path"]).name])
    ws.append([])
    ws.append(["PLAN", "2.PLAN+ MOTOR_DALGALARI_VE_USTA"])
    ws.append(["SURUM", "v2 GENIS — yapi + eser guclendirme"])
    ws.append(["ONCEKI", "1.PLAN = BILGISAYAR_VE_SAHNE_YUKLEME_PLANI"])
    ws.append(["KAPI", "Samile RAG + 1.PLAN bitince aksiyon"])
    ws.append(["TOPLAM ESER", total])
    ws.append(["KATEGORI", len(results)])
    ws.append(["KOK", str(OUT_ROOT)])
    ws.append([])
    ws.append(
        [
            "SIRA",
            "01 Masa → 02A → 03B → 04C → 05D → 06E → 07F → 08 Akıl → "
            "09 Web/kota → 10 Fenni → 11 Fren → 12 Gece → 13 Odalar → 14 Mahrem",
        ]
    )
    ozet = OUT_ROOT / "00_OZET_2.PLAN+_MOTOR_DALGALARI_VE_USTA.xlsx"
    wb.save(ozet)
    print(
        json.dumps(
            {
                "ok": True,
                "plan": "2.PLAN+ MOTOR_DALGALARI_VE_USTA",
                "surum": "v2",
                "cats": len(results),
                "works": total,
                "by_cat": {r["cat"]: r["rows"] for r in results},
                "root": str(OUT_ROOT),
                "ozet": str(ozet),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
