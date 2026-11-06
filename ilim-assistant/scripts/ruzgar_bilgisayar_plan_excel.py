#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bilgisayar + sahne dolum planı — kategori kategori Excel (indirilecek eserler).

Çıktı:
  Desktop/RÜZGAR/RÜZGAR KÜTÜPHANE ENVANTER/BILGISAYAR_VE_SAHNE_YUKLEME_PLANI/<KAT>/...

Kural: yalnız yasal/açık (CC, kamu malı, resmi docs, ücretsiz PDF, OCW).
Telifli ticari klasik (DDIA, Clean Code, CSAPP, AIMA baskı vb.) YOK — açık muadilleri var.
"""
from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

OUT_ROOT = Path(
    r"C:\Users\hayma\Desktop\RÜZGAR\RÜZGAR KÜTÜPHANE ENVANTER\BILGISAYAR_VE_SAHNE_YUKLEME_PLANI"
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

# (orijinal, tr, yazar, katar, cilt, sayfa, dalga, not)
CATS: dict[str, tuple[str, list[tuple]]] = {
    "01_PROGRAMLAMA": (
        "01 PROGRAMLAMA",
        [
            ("Crafting Interpreters", "Yorumlayıcılar İnşa Etmek", "Robert Nystrom", "Dil/organ fabrikası; sahne betiği ve mini-DSL", "1", "~600+", "A/C", "Ücretsiz HTML"),
            ("Writing An Interpreter In Go (açık eşlik/kod)", "Go ile Yorumlayıcı Yazmak (açık kod hattı)", "Thorsten Ball + açık portlar", "Dil motoru pratik hattı", "1", "~200+ kod", "A", "Kitap telifliyse yalnız açık port/kod"),
            ("Build Your Own Lisp", "Kendi Lisp'ini Yaz", "Daniel Holden", "C ile dil inşası", "1", "~200+", "A", "Açık kitap"),
            ("The Rust Programming Language", "Rust Programlama Dili", "Klabnik; Nichols", "Güvenli sistem dili omurgası", "1", "~550", "A", "Resmi"),
            ("Rust By Example", "Örneklerle Rust", "Rust Project", "Pratik Rust kalıpları", "1", "docs", "A", "Resmi"),
            ("Rustonomicon", "Rustonomicon (Unsafe)", "Rust Project", "Unsafe/FFI derinlik", "1", "docs", "A", "Resmi"),
            ("Async Book (Rust)", "Rust Async Kitabı", "Rust Async WG", "Eşzamanlılık", "1", "docs", "A", "Resmi"),
            ("Zero To Production In Rust", "Rust ile Üretime Sıfırdan", "Luca Palmieri", "Gerçek servis/API", "1", "~400", "A", "Açık"),
            ("Comprehensive Rust", "Kapsamlı Rust", "Google Android", "Endüstriyel Rust müfredatı", "1", "kurs", "A", "Açık"),
            ("Eloquent JavaScript (3e)", "Belagatli JavaScript", "Marijn Haverbeke", "JS/web atölyesi", "1", "~450", "A", "CC BY-NC"),
            ("You Don't Know JS Yet", "JavaScript'i Henüz Bilmiyorsun", "Kyle Simpson", "JS derin kavramlar", "6+", "seri", "A", "Açık seri"),
            ("JavaScript.info", "Modern JavaScript Öğretici", "Ilya Kantor", "Büyük JS gövdesi", "1", "docs — geniş", "A", "Açık"),
            ("TypeScript Handbook", "TypeScript El Kitabı", "Microsoft", "Tipli JS / masaüstü", "1", "docs", "A", "Resmi"),
            ("A Tour of Go", "Go'ya Tur", "Go Authors", "Go temeli", "1", "~100", "A", "Resmi"),
            ("Effective Go", "Etkili Go", "Go Authors", "Go idioms", "1", "docs", "A", "Resmi"),
            ("Go by Example", "Örneklerle Go", "Mark McGranaghan", "Pratik Go", "1", "docs", "A", "Açık"),
            ("Learn Go with Tests", "Testlerle Go Öğren", "Chris James", "TDD + Go", "1", "~300+", "A", "Açık"),
            ("Think Python 2e", "Python'u Düşün", "Allen Downey", "Python omurgası", "1", "~240", "A", "CC"),
            ("Python for Everybody", "Herkes için Python", "Charles Severance", "Öğretim gövdesi", "1", "~250", "A", "Açık"),
            ("Automate the Boring Stuff", "Sıkıcı İşleri Otomatikleştir", "Al Sweigart", "Süper-el otomasyon", "1", "~500", "A", "Açık"),
            ("Dive Into Python 3", "Python 3'e Dalış", "Mark Pilgrim", "Klasik Python gövdesi", "1", "~400", "A", "Açık"),
            ("Python Tutorial + Library Ref", "Python Resmi Öğretici + Kütüphane", "PSF", "Dil referansı", "2", "docs — geniş", "A", "Resmi"),
            ("SICP", "Bilgisayar Programlarının Yapısı ve Yorumu", "Abelson; Sussman", "CS düşünce omurgası", "1", "~850", "A", "Açık HTML/PDF"),
            ("How to Design Programs (2e)", "Programları Nasıl Tasarlamalı", "Felleisen et al.", "Tasarım reçeteleri", "1", "~700+", "A", "Açık"),
            ("Composing Programs", "Programları Bileştirmek", "Berkeley CS61A", "Python ile SICP ruhu", "1", "~400+", "A", "Açık"),
            ("Learn You a Haskell", "Haskell Öğrenelim", "Miran Lipovača", "Fonksiyonel ufuk", "1", "~300", "A", "Açık"),
            ("Learn You Some Erlang", "Erlang Öğrenelim", "Fred Hébert", "Dağıtık/aktör modeli", "1", "~500+", "A", "Açık"),
            ("Clojure for the Brave and True", "Cesurlar için Clojure", "Daniel Higginbotham", "Lisp modern pratik", "1", "~300+", "A", "Açık"),
            ("Modern C (Gustedt)", "Modern C", "Jens Gustedt", "C dili omurgası", "1", "~400", "A", "Açık"),
            ("C++ Core Guidelines", "C++ Çekirdek İlkeleri", "Stroustrup; Sutter", "Modern C++ disiplini", "1", "docs", "A", "Açık"),
            ("CPPReference (çekirdek)", "C++ Referans", "cppreference", "Dil ansiklopedisi", "1", "wiki", "A", "Açık"),
            ("The Swift Programming Language", "Swift Programlama Dili", "Apple", "Swift omurgası", "1", "docs", "A", "Resmi"),
            ("Kotlin Docs + Koans", "Kotlin Belgeleri + Koans", "JetBrains", "JVM/Android dili", "1", "docs+alıştırma", "A", "Resmi"),
            ("Oracle Java Tutorials", "Java Öğreticileri", "Oracle", "Java gövdesi", "1", "docs", "A", "Resmi"),
            ("SQLAlchemy Docs", "SQLAlchemy Belgeleri", "SQLAlchemy", "Python ORM", "1", "docs", "A", "Resmi"),
            ("Regular-Expressions.info + RegexOne", "Düzenli İfadeler", "Goyvaerts / RegexOne", "Metin avı", "1", "seçme", "A", "Eğitim"),
            ("Julia Documentation + Manual", "Julia El Kitabı", "Julia Project", "Bilimsel dil", "1", "docs", "A", "Resmi"),
            ("R for Data Science (2e)", "Veri Bilimi için R", "Wickham; Çetinkaya-Rundel; Grolemund", "R veri hattı", "1", "~500+", "A/B", "Açık"),
            ("OCaml From the Ground Up / Real World OCaml (açık)", "OCaml (açık sürümler)", "OCaml ekosistemi", "Tipli fonksiyonel", "1", "docs/kitap", "A", "Açık kısımlar"),
            ("Zig Language Reference + Learn Zig", "Zig Dil Referansı", "Zig Project", "Sistem dili ufku", "1", "docs", "A", "Resmi"),
        ],
    ),
    "02_ALGORITMALAR": (
        "02 ALGORİTMALAR",
        [
            ("Open Data Structures", "Açık Veri Yapıları", "Pat Morin", "Veri yapıları omurgası", "1", "~300+", "A", "Açık"),
            ("Algorithms (Jeff Erickson)", "Algoritmalar", "Jeff Erickson", "Tasarım + ispat", "1", "~450", "A", "Ücretsiz PDF"),
            ("Competitive Programmer's Handbook", "Yarışmacı Programcı El Kitabı", "Antti Laaksonen", "Pratik hız", "1", "~300", "A", "Açık PDF"),
            ("CP-Algorithms", "CP Algoritmaları Ansiklopedisi", "CP-Algorithms", "Referans gövde", "1", "wiki — geniş", "A", "Açık"),
            ("Algorithms for Competitive Programming (USACO guide)", "USACO Algoritma Rehberi", "USACO Guide", "Yarış müfredatı", "1", "geniş", "A", "Açık"),
            ("algs4 açık eşlik (yasal)", "Algorithms 4 — açık eşlik", "Sedgewick; Wayne", "Klasik + kod (yasal parça)", "1", "değişken", "A", "Yalnız açık"),
            ("MIT 6.006 OCW", "MIT 6.006 Algoritmalar", "MIT OCW", "Üniversite dersi", "1", "notlar+video metin", "A", "OCW"),
            ("MIT 6.046 OCW", "MIT 6.046 Tasarım ve Analiz", "MIT OCW", "İleri algoritma", "1", "notlar", "A", "OCW"),
            ("Princeton Algorithms açık notlar", "Princeton Algoritmalar", "Princeton", "Kurs pekiştirme", "1", "notlar", "A", "Açık"),
            ("Tim Roughgarden Algorithms Illuminated (açık not/video transcript seçme)", "Algoritmalar Aydınlatıldı (açık eşlik)", "Tim Roughgarden", "Sezgi + analiz", "4", "seçme açık", "A", "Yalnız açık materyal"),
            ("VisuAlgo + açıklama metinleri", "VisuAlgo", "Steven Halim", "Görsel algoritma sezgisi", "1", "site", "A", "Eğitim"),
            ("BaseCS seri (seçme)", "BaseCS", "Vaidehi Joshi", "Kavram anlatımı", "1", "seçme", "A", "Açık yazılar"),
            ("Graph Algorithms (neo4j açık kitap)", "Graf Algoritmaları", "Needham; Hodler", "Graf düşüncesi", "1", "~250+", "A", "Açık"),
            ("The Algorithm Design Manual — açık slayt/not (Skiena kurs)", "Algoritma Tasarımı Kurs Notları", "Steven Skiena", "Savaş sandığı sezgisi", "1", "notlar", "A", "Kurs açık; kitap telifli değil"),
            ("LeetCode Explore + Editorials (açık olanlar)", "LeetCode Keşif (açık editorial)", "LeetCode", "Problem kası", "1", "seçme", "A", "Açık editorial"),
            ("InterviewBit / NeetCode roadmap metinleri (seçme)", "Algoritma Yol Haritası Metinleri", "topluluk", "Sistematik pratik", "1", "seçme", "A", "Açık"),
            ("Algorithms Notes for Professionals", "Profesyoneller için Algoritma Notları", "Goalkicker", "Kompakt referans", "1", "~200+", "A", "Açık PDF"),
            ("IIT Bombay / NPTEL DSA açık not (seçme)", "DSA Ders Notları (NPTEL seçme)", "NPTEL", "Akademik pekiştirme", "1", "notlar", "A", "Açık"),
            ("GeeksforGeeks DSA self-paced (çekirdek konu seçkisi)", "DSA Konu Seçkisi", "GfG", "Konu ansiklopedisi (seçme)", "1", "seçme", "A", "Eğitim; kalite süz"),
            ("Competitive Programming 4 — açık önizleme/ekler varsa", "Yarışmacı Programlama (açık parça)", "Halim; Halim", "Yalnız açık parça", "1", "değişken", "A", "Telifliyse atla"),
        ],
    ),
    "03_YAPAY_ZEKA": (
        "03 YAPAY ZEKÂ",
        [
            ("Neural Networks and Deep Learning", "Sinir Ağları ve Derin Öğrenme", "Michael Nielsen", "Sezgi + matematik giriş", "1", "~200+", "B", "Ücretsiz"),
            ("Deep Learning (Goodfellow et al.)", "Derin Öğrenme", "Goodfellow; Bengio; Courville", "DL ansiklopedisi", "1", "~800", "B", "Resmi ücretsiz"),
            ("Dive into Deep Learning (D2L)", "Derin Öğrenmeye Dalış", "Zhang et al.", "Uygulamalı DL + kod", "1", "~1000+", "B", "Açık"),
            ("Reinforcement Learning: An Introduction (2e)", "Pekiştirmeli Öğrenme", "Sutton; Barto", "RL omurgası", "1", "~550", "B", "Ücretsiz PDF"),
            ("Spinning Up in Deep RL", "Derin RL'ye Giriş", "OpenAI", "RL pratik müfredat", "1", "~150+", "B", "Açık"),
            ("Probabilistic Machine Learning: An Introduction (Murphy)", "Olasılıksal ML — Giriş", "Kevin Murphy", "Modern ML gövdesi", "1", "~700+", "B", "Ücretsiz PDF"),
            ("Probabilistic Machine Learning: Advanced Topics (Murphy)", "Olasılıksal ML — İleri", "Kevin Murphy", "İleri ML", "1", "~700+", "B", "Ücretsiz PDF"),
            ("Mathematics for Machine Learning", "Makine Öğrenmesi için Matematik", "Deisenroth; Faisal; Ong", "ML matematik omurgası", "1", "~400+", "B", "Ücretsiz PDF"),
            ("Interpretable Machine Learning", "Yorumlanabilir ML", "Christoph Molnar", "Açıklanabilirlik", "1", "~300+", "B", "Açık"),
            ("Machine Learning Yearning", "ML Yearning", "Andrew Ng", "Proje stratejisi", "1", "~100+", "B", "Ücretsiz"),
            ("fast.ai Practical Deep Learning", "fast.ai Pratik DL", "Howard; Gugger", "Hızlı pratik", "1", "kurs", "B", "Açık"),
            ("Hugging Face Course", "Hugging Face Kursu", "Hugging Face", "Transformer pratik", "1", "kurs", "B", "Açık"),
            ("PyTorch Tutorials + Recipes", "PyTorch Öğretici + Tarifler", "PyTorch", "Model kodlama", "1", "docs", "B", "Resmi"),
            ("TensorFlow Tutorials", "TensorFlow Öğreticileri", "Google", "Alternatif çerçeve", "1", "docs", "B", "Resmi"),
            ("JAX / Flax documentation", "JAX / Flax", "Google", "Araştırma hızı", "1", "docs", "B", "Açık"),
            ("scikit-learn User Guide", "scikit-learn Kılavuzu", "scikit-learn", "Klasik ML", "1", "docs", "B", "Resmi"),
            ("Made With ML", "ML ile Yapıldı", "Goku Mohandas", "ML mühendislik yolu", "1", "müfredat", "B", "Açık"),
            ("UC Berkeley CS188", "CS188 YZ Ders Notları", "UC Berkeley", "Klasik YZ", "1", "notlar", "B", "Açık"),
            ("Stanford CS231n notes", "CS231n Görü Notları", "Stanford", "CNN / görü", "1", "notlar", "B", "Açık"),
            ("Stanford CS224n notes", "CS224n NLP Notları", "Stanford", "Derin NLP", "1", "notlar", "B", "Açık"),
            ("Stanford CS234 / CS285 RL notes (açık)", "Derin RL Ders Notları", "Stanford / Berkeley", "İleri RL", "1", "notlar", "B", "Açık"),
            ("Attention Is All You Need (+izleyen temel makaleler seçkisi)", "Transformer Temel Makale Paketi", "Vaswani et al. + seçme", "Modern dil omurgası", "1", "makale seti", "B", "Açık arXiv"),
            ("The Illustrated Transformer / BERT (Jay Alammar seçme)", "Transformer Görsel Anlatım", "Jay Alammar", "Sezgi köprüsü", "1", "yazı seti", "B", "Açık"),
            ("Lilian Weng blog seçkisi (LLM/RL/diffusion)", "Lilian Weng Seçkisi", "Lilian Weng", "Araştırma özeti kalitesi", "1", "seçme", "B", "Açık"),
            ("Karpathy Neural Nets: Zero to Hero (metin/notebook)", "Sıfırdan Kahraman Sinir Ağları", "Andrej Karpathy", "El ile inşa sezgisi", "1", "kurs", "B", "Açık"),
            ("Understanding Deep Learning (Prince) — ücretsiz PDF", "Derin Öğrenmeyi Anlamak", "Simon Prince", "Modern ders kitabı", "1", "~500+", "B", "Ücretsiz"),
            ("Gaussian Processes for Machine Learning", "ML için Gauss Süreçleri", "Rasmussen; Williams", "Belirsizlik modelleme", "1", "~250", "B", "Ücretsiz"),
            ("Multiagent Systems (Shoham; Leyton-Brown)", "Çok Etmenli Sistemler", "Shoham; Leyton-Brown", "Ajan toplumları", "1", "~500+", "B/E", "Ücretsiz PDF"),
            ("An Introduction to MultiAgent Systems (Wooldridge — açık slayt/not)", "Çok Etmenli Sistemlere Giriş (açık not)", "Michael Wooldridge", "Ajan teorisi pekiştirme", "1", "notlar", "B", "Açık not"),
            ("Gymnasium + Stable-Baselines3 docs", "Gymnasium / SB3", "Farama / SB3", "RL yazılım yığını", "1", "docs", "B", "Açık"),
            ("Papers With Code methods (seçme ansiklopedi)", "Papers With Code Yöntemleri", "PWC", "SOTA yöntem haritası", "1", "ansiklopedi", "B", "Açık"),
            ("Distill.pub seçkisi", "Distill Seçkisi", "Distill", "Görsel derin anlatım", "1", "seçme", "B", "Açık"),
        ],
    ),
    "04_VERITABANLARI": (
        "04 VERİTABANLARI",
        [
            ("Use The Index, Luke", "İndeksi Kullan, Luke", "Markus Winand", "SQL indeks/performans", "1", "~200+", "A", "Açık"),
            ("PostgreSQL Official Docs", "PostgreSQL Resmi Belgeler", "PostgreSQL GDG", "DB omurgası", "çok", "docs — geniş", "A", "Resmi"),
            ("The Internals of PostgreSQL", "PostgreSQL İç Yapısı", "Hironobu Suzuki", "Motor anatomisi", "1", "~300+", "A", "Açık"),
            ("SQLite Docs (lang+format+series)", "SQLite Dil ve Format", "SQLite", "Yerel DB / hafıza", "1", "docs", "A", "Resmi"),
            ("SQLite Internals / File Format deep dive (açık)", "SQLite Dosya Formatı Derinliği", "SQLite / topluluk", "Yerel indeks fiziği", "1", "docs", "A", "Açık"),
            ("CMU 15-445/645 Database Systems", "CMU Veritabanı Sistemleri", "Andy Pavlo / CMU", "DB iç yapısı + projeler", "1", "notlar+proje", "A", "Açık arşiv"),
            ("CMU 15-721 Advanced Database Systems", "CMU İleri Veritabanı", "CMU", "İleri motor", "1", "notlar", "A", "Açık"),
            ("Database Design (Adrienne Watt) — Open Textbook", "Veritabanı Tasarımı", "Adrienne Watt", "İlişkisel tasarım", "1", "~200+", "A", "Açık"),
            ("MongoDB Manual", "MongoDB Kılavuzu", "MongoDB", "Doküman DB", "1", "docs", "A", "Resmi"),
            ("Redis Documentation + Commands", "Redis Belgeleri", "Redis", "Önbellek / yapılar", "1", "docs", "A", "Resmi"),
            ("DuckDB Documentation", "DuckDB Belgeleri", "DuckDB", "Yerel analitik SQL", "1", "docs", "A", "Açık"),
            ("Apache Arrow Docs", "Apache Arrow", "ASF", "Sütunsal bellek formatı", "1", "docs", "A", "Açık"),
            ("Apache Parquet / ORC specs", "Parquet / ORC", "ASF", "Depolama formatları", "1", "spec", "A", "Açık"),
            ("ClickHouse Docs", "ClickHouse", "ClickHouse", "OLAP motor", "1", "docs", "A", "Açık"),
            ("Neo4j Graph Database / Cypher manuals", "Neo4j / Cypher", "Neo4j", "Graf DB", "1", "docs", "A", "Resmi açık"),
            ("Cassandra Docs", "Apache Cassandra", "ASF", "Geniş ölçek KV", "1", "docs", "A", "Açık"),
            ("Elasticsearch Guide (çekirdek)", "Elasticsearch Kılavuzu", "Elastic", "Arama indeksi", "1", "docs", "A/Sahne", "Resmi"),
            ("AOSA — Database chapters", "Açık Kaynak Mimari — DB", "AOSA", "DDIA muadili açık", "1", "seçme", "A", "Açık"),
            ("SQLBolt + PGExercises + Select Star SQL", "SQL Alıştırma Üçlüsü", "çeşitli", "Pratik SQL kası", "1", "alıştırma", "A", "Açık"),
            ("Transaction Processing concepts (açık ders notu seçkisi)", "İşlem İşleme Kavramları", "üniversite OCW", "ACID/MVCC sezgisi", "1", "notlar", "A", "Açık"),
            ("Data Engineering Zoomcamp materyali (açık)", "Veri Mühendisliği Kampı", "DataTalksClub", "ETL/boru hattı", "1", "kurs", "A/C", "Açık"),
            ("dbt Docs + Best Practices", "dbt Belgeleri", "dbt Labs", "Analitik dönüşüm", "1", "docs", "A", "Açık"),
        ],
    ),
    "05_AG": (
        "05 AĞ TEKNOLOJİLERİ",
        [
            ("Computer Networks: A Systems Approach", "Bilgisayar Ağları: Sistem Yaklaşımı", "Peterson; Davie", "Ağ teorisi+pratik", "1", "~800+", "A", "Açık kitap"),
            ("Computer Networking: Principles, Protocols and Practice", "Bilgisayar Ağları: İlkeler ve Protokoller", "Olivier Bonaventure", "Avrupa açık ders kitabı", "1", "~500+", "A", "Açık"),
            ("Beej's Guide to Network Programming", "Beej Ağ Programlama", "Brian Hall", "Soket temeli", "1", "~150+", "A", "Açık"),
            ("Beej's Guide to Unix IPC", "Beej Unix IPC", "Brian Hall", "Süreçler arası", "1", "~100+", "A", "Açık"),
            ("High Performance Browser Networking", "Yüksek Performanslı Tarayıcı Ağı", "Ilya Grigorik", "HTTP/2/3, gecikme", "1", "~400", "A", "Açık"),
            ("HTTP/2 & HTTP/3 explained", "HTTP/2 ve HTTP/3", "Daniel Stenberg", "Modern HTTP", "1", "~100+", "A", "Açık"),
            ("MDN HTTP / Fetch / WebSockets", "MDN Ağ Web API", "MDN", "Web ağ yüzeyi", "1", "docs", "A", "Açık"),
            ("RFC çekirdek paketi (791,793,1035,2616/7230,7540,8446,9000)", "Temel RFC Paketi", "IETF", "Standart metinler", "1", "RFC seti", "A", "Kamu"),
            ("QUIC / HTTP3 IETF drafts + açıklama seçkisi", "QUIC Paketi", "IETF + açıklayıcılar", "Yeni taşıma", "1", "RFC+yazı", "A", "Açık"),
            ("Wireshark User's Guide + wiki", "Wireshark Kılavuzu", "Wireshark", "Paket analizi (öğretim)", "1", "docs", "A", "Açık"),
            ("Cloudflare Learning Center (seçme)", "Cloudflare Öğrenme Merkezi", "Cloudflare", "CDN/TLS/edge sezgisi", "1", "seçme", "A", "Açık"),
            ("TLS Illustrated / The New Illustrated TLS Connection", "TLS Görsel Anlatım", "Michael Driscoll vd.", "Şifreli kanal sezgisi", "1", "yazı", "A/C", "Açık"),
            ("Zero Trust Architecture (NIST SP 800-207)", "Sıfır Güven Mimarisi", "NIST", "Modern ağ güven modeli", "1", "standart", "A/C", "Kamu"),
            ("DNS for Rocket Scientists / zytrax DNS", "DNS Rehberi", "Zytrax vd.", "İsim sistemi", "1", "docs", "A", "Açık"),
            ("HAProxy / Envoy / Traefik docs (çekirdek)", "Ters Vekil Üçlüsü", "HAProxy/Envoy/Traefik", "Edge yönlendirme", "1", "docs", "A/C", "Açık"),
            ("gRPC Docs + Proto3 Language Guide", "gRPC + Protobuf", "CNCF / Google", "RPC omurgası", "1", "docs", "A", "Açık"),
            ("WebRTC samples + W3C specs (seçme)", "WebRTC", "W3C / Google örnekleri", "Gerçek zamanlı medya ağı", "1", "docs", "A/Sahne", "Açık"),
            ("npwg / TCP/IP Guide (Charles Kozierok — ücretsiz online)", "TCP/IP Rehberi", "Charles Kozierok", "Klasik protokol ansiklopedisi", "1", "geniş", "A", "Ücretsiz online"),
            ("Stanford CS144 notes (açık)", "CS144 Bilgisayar Ağları", "Stanford", "Üniversite ağ dersi", "1", "notlar", "A", "Açık"),
            ("IBM / Red Hat networking guides (seçme açık)", "Ağ Yönetim Rehberleri", "Red Hat", "Pratik ağ", "1", "seçme", "A", "Açık"),
        ],
    ),
    "06_ISLETIM_SISTEMLERI": (
        "06 İŞLETİM - İLETİŞİM SİSTEMLERİ",
        [
            ("OSTEP", "İşletim Sistemleri: Üç Kolay Parça", "Arpaci-Dusseau", "OS omurgası (kritik)", "1", "~600+", "A", "Ücretsiz"),
            ("xv6 book + source commentary", "xv6 Kitabı", "MIT PDOS", "Küçük Unix öğretimi", "1", "~100+", "A", "Açık"),
            ("Linux Kernel Documentation", "Linux Çekirdek Belgeleri", "kernel.org", "Çekirdek API", "çok", "docs", "A", "Resmi"),
            ("Linux Insides", "Linux İçyüzü", "0xAX", "Çekirdek yürüyüşü", "1", "~400+", "A", "Açık"),
            ("Linux From Scratch", "Sıfırdan Linux", "LFS Project", "Sistem inşa", "1", "~300+", "A", "Açık"),
            ("Beyond Linux From Scratch", "LFS Ötesi", "BLFS", "Masaüstü/servis katmanı", "1", "geniş", "A", "Açık"),
            ("The Linux Command Line", "Linux Komut Satırı", "William Shotts", "CLI ustalık", "1", "~500", "A", "CC"),
            ("GNU Coreutils manual + Bash manual", "Coreutils + Bash", "GNU", "Kabuk omurgası", "2", "docs", "A", "Resmi"),
            ("FreeBSD Handbook", "FreeBSD El Kitabı", "FreeBSD", "Unix yönetim", "1", "geniş", "A", "Açık"),
            ("OpenBSD FAQ + man pages (seçme)", "OpenBSD FAQ", "OpenBSD", "Güvenlik odaklı Unix", "1", "docs", "A/C", "Açık"),
            ("The Little Book of Semaphores", "Semaförlerin Küçük Kitabı", "Allen Downey", "Eşzamanlılık problemleri", "1", "~300", "A", "Açık"),
            ("Operating Systems: From 0 to 1", "İşletim Sistemleri 0'dan 1'e", "Tu Do Hang", "Sıfırdan OS", "1", "~300+", "A", "Açık"),
            ("Writing a Simple Operating System — from Scratch (Seemann açık? / OSDev wiki)", "OSDev Wiki + basit OS tarifleri", "OSDev topluluğu", "Boot/kernel pratik", "1", "wiki", "A", "Açık"),
            ("systemd documentation", "systemd Belgeleri", "systemd", "Modern init", "1", "docs", "A", "Resmi"),
            ("Pro Git", "Pro Git", "Chacon; Straub", "Sürüm kontrolü", "1", "~500", "A/C", "Açık"),
            ("Git Internals (Pro Git ch + git/docs technical)", "Git İç Yapısı", "Git Project", "Nesne modeli", "1", "docs", "A", "Açık"),
            ("Windows Internals — açık Microsoft Learn eşlik (seçme)", "Windows Sistem Kavramları (Learn)", "Microsoft Learn", "Windows yüzey (yasal)", "1", "docs", "A", "Resmi Learn; kitap telifli değil"),
            ("WSL Documentation", "WSL Belgeleri", "Microsoft", "Linux-on-Windows", "1", "docs", "A", "Resmi"),
            ("POSIX.1 özet + man7.org", "POSIX / man7", "Open Group / man7", "Unix API ansiklopedisi", "1", "docs", "A", "Açık"),
            ("eBPF / bpftrace docs + learning (seçme)", "eBPF Öğrenme Paketi", "CNCF / bpftrace", "Canlı çekirdek gözlemi", "1", "docs", "A/C", "Açık"),
            ("QEMU / KVM documentation (çekirdek)", "QEMU / KVM", "QEMU", "Sanallaştırma", "1", "docs", "A", "Açık"),
            ("Containers from Scratch anlatımları (Liz Rice seçme + OCI spec)", "Konteyner Sıfırdan + OCI", "OCI / Liz Rice", "Namespace/cgroup sezgisi", "1", "yazı+spec", "A/C", "Açık"),
        ],
    ),
    "07_SIBER": (
        "07 SİBER GÜVENLİK (SAVUNMA)",
        [
            ("Security Engineering (3e) — ücretsiz online", "Güvenlik Mühendisliği", "Ross Anderson", "Savunma düşüncesi omurgası", "1", "~1000+", "C", "Ücretsiz online"),
            ("OWASP WSTG", "OWASP Web Güvenlik Test Rehberi", "OWASP", "Test çerçevesi (PoC yok)", "1", "geniş", "C", "Açık"),
            ("OWASP ASVS", "OWASP Doğrulama Standardı", "OWASP", "Güvenlik gereksinimleri", "1", "~200+", "C", "Açık"),
            ("OWASP Cheat Sheet Series", "OWASP Kopya Kağıdı", "OWASP", "Güvenli kalıplar", "çok", "seri", "C", "Açık"),
            ("OWASP Top 10 + Proactive Controls + SAMM", "OWASP Top10 + Proaktif + SAMM", "OWASP", "Risk + olgunluk", "3", "set", "C", "Açık"),
            ("OWASP API Security Top 10 + ASVS API", "OWASP API Güvenliği", "OWASP", "API savunması", "1", "docs", "C", "Açık"),
            ("NIST CSF 2.0", "NIST Siber Çerçeve 2.0", "NIST", "Kurumsal dil", "1", "standart", "C", "Kamu"),
            ("NIST SP 800-53 / 800-61 / 800-63 (seçme)", "NIST SP 800 Paketi", "NIST", "Kontrol + IR + kimlik", "3", "standart", "C", "Kamu"),
            ("CIS Controls (ücretsiz sürüm)", "CIS Kontrolleri", "CIS", "Pratik kontrol listesi", "1", "docs", "C", "Ücretsiz sürüm"),
            ("MITRE ATT&CK + D3FEND", "ATT&CK + D3FEND", "MITRE", "Tehdit + savunma haritası", "2", "bilgi tabanı", "C", "Açık — exploit yok"),
            ("CISA IR / ransomware / secure by design", "CISA Oyun Kitapları", "CISA", "Olay müdahalesi", "1", "playbook", "C", "Kamu"),
            ("SEI CERT secure coding (C/C++/Java/Perl)", "CERT Güvenli Kodlama", "SEI CERT", "Güvenli yazılım", "çok", "docs", "C", "Açık"),
            ("Handbook of Applied Cryptography", "Uygulamalı Kriptografi El Kitabı", "Menezes; van Oorschot; Vanstone", "Kripto ansiklopedisi", "1", "~800+", "C", "Ücretsiz PDF"),
            ("Crypto 101", "Kriptografi 101", "lvh", "Kripto sezgi", "1", "~150", "C", "Açık"),
            ("Serious Cryptography — açık not/eşlik yoksa Boneh Coursera notes", "Kripto Ders Notları (Boneh)", "Dan Boneh / Stanford", "Modern kripto dersi", "1", "notlar", "C", "Açık kurs notu"),
            ("The Cryptopals Crypto Challenges (açık challenge metinleri)", "Cryptopals Meydan Okumaları", "Cryptopals", "Kripto pratik (saldırı PoC değil; öğrenme)", "1", "set", "C", "Açık; dikkatli"),
            ("Reverse Engineering for Beginners", "Yeni Başlayanlar için Tersine Mühendislik", "Dennis Yurichev", "Binary okuma (savunma/analiz)", "1", "~1000+", "C", "Ücretsiz"),
            ("Google/Microsoft SDL + Secure Development docs", "Güvenli Geliştirme Yaşam Döngüsü", "Google / Microsoft", "Üretim güvenliği", "1", "docs", "C", "Açık"),
            ("SLSA / Supply-chain Levels for Software Artifacts", "SLSA Tedarik Zinciri", "OpenSSF", "Yazılım tedarik savunması", "1", "spec", "C", "Açık"),
            ("OpenSSF Best Practices + Scorecard docs", "OpenSSF En İyi Uygulamalar", "OpenSSF", "Açık kaynak güvenlik", "1", "docs", "C", "Açık"),
            ("Privacy Patterns + GDPR resmi metin (seçme)", "Gizlilik Kalıpları + GDPR", "privacypatterns / AB", "Mahremiyet tasarımı", "1", "docs+metin", "C/E", "Açık/kamu"),
            ("AGE / age encryption + Signal Protocol specs (seçme)", "Modern Şifreleme Protokolleri (seçme)", "age / Signal", "Mesaj güven modeli", "1", "spec", "C", "Açık"),
        ],
    ),
    "08_YAZILIM_MIMARI": (
        "08 YAZILIM MİMARİLERİ",
        [
            ("Architecture of Open Source Applications I–II", "Açık Kaynak Uygulamaların Mimarisi", "AOSA", "Gerçek sistem okuma", "2", "~600+/cilt", "C", "Açık"),
            ("The Performance of Open Source Applications", "Açık Kaynak Performansı", "POSA", "Performans vakaları", "1", "~400", "C", "Açık"),
            ("500 Lines or Less", "500 Satır veya Daha Az", "AOSA", "Küçük sistem anatomisi", "1", "~400+", "C", "Açık"),
            ("Software Engineering at Google", "Google'da Yazılım Mühendisliği", "Winters et al.", "Büyük kod tabanı", "1", "~600", "C", "Açık"),
            ("Game Programming Patterns", "Oyun Programlama Kalıpları", "Robert Nystrom", "Kalıp + sahne ECS", "1", "~350", "C", "Açık"),
            ("The Twelve-Factor App", "On İki Faktörlü Uygulama", "Heroku", "Servis disiplini", "1", "kısa", "C", "Açık"),
            ("Azure Cloud Design Patterns", "Bulut Tasarım Kalıpları", "Microsoft", "Dağıtık kalıplar", "1", "docs", "C", "Açık"),
            ("AWS Well-Architected (whitepapers)", "AWS İyi Mimari", "Amazon", "Bulut omurgası", "1", "whitepaper", "C", "Açık"),
            ("Google Cloud Architecture Framework", "Google Mimari Çerçeve", "Google", "Bulut çerçeve", "1", "docs", "C", "Açık"),
            ("Domain-Driven Design Reference (Evans)", "Alan Güdümlü Tasarım Referansı", "Eric Evans", "DDD dil kısaltması", "1", "~50+", "C", "Ücretsiz referans"),
            ("Domain-Driven Design Quickly (InfoQ — ücretsiz)", "DDD Hızlı", "InfoQ", "DDD giriş", "1", "~100+", "C", "Ücretsiz"),
            ("Martin Fowler bliki + patterns seçkisi", "Fowler Bliki Seçkisi", "Martin Fowler", "Mimari dil", "1", "seçme", "C", "Açık"),
            ("Enterprise Integration Patterns (açık pattern catalog)", "Kurumsal Entegrasyon Kalıpları (katalog)", "Hohpe; Woolf sitesi", "Mesajlaşma kalıpları", "1", "katalog", "C", "Açık katalog"),
            ("Microservices.io pattern catalog (Newman)", "Mikroservis Kalıp Kataloğu", "Chris Newman sitesi", "Servis sınırları", "1", "katalog", "C", "Açık site"),
            ("Reactive Manifesto + Reactive Design Patterns (açık özet)", "Reaktif Manifesto", "Reactive Manifesto", "Reaktif sistem dili", "1", "manifesto", "C", "Açık"),
            ("Open Application Model / CNCF architecture whitepapers (seçme)", "CNCF Mimari Yazıları", "CNCF", "Bulut-yerel mimari", "1", "seçme", "C", "Açık"),
            ("C4 Model docs (Simon Brown)", "C4 Model", "Simon Brown", "Mimari çizim dili", "1", "docs", "C", "Açık"),
            ("arc42 template + documentation", "arc42", "arc42", "Mimari dokümantasyon", "1", "docs", "C", "Açık"),
            ("SOLID / GRASP açık anlatım seçkisi (akademik)", "SOLID / GRASP Seçkisi", "çeşitli akademik", "Nesne tasarım ilkeleri", "1", "seçme", "C", "Açık"),
            ("A Philosophy of Software Design — Stanford CS190 açık slaytlar", "Yazılım Tasarımı Felsefesi (slayt)", "John Ousterhout", "Karmaşıklık yönetimi (slayt)", "1", "slayt", "C", "Açık slayt; kitap telifli"),
        ],
    ),
    "09_DEVOPS": (
        "09 DEVOPS - ALTYAPI",
        [
            ("Docker Docs (concepts+compose+buildx)", "Docker Belgeleri", "Docker", "Konteyner", "1", "docs", "C", "Resmi"),
            ("Podman / Buildah docs", "Podman / Buildah", "Red Hat", "Daemonless konteyner", "1", "docs", "C", "Açık"),
            ("Kubernetes Concepts + Tutorials + Task docs", "Kubernetes", "CNCF/K8s", "Orkestrasyon", "1", "docs — geniş", "C", "Resmi"),
            ("Kubernetes the Hard Way (Kelsey Hightower)", "Zor Yoldan Kubernetes", "Kelsey Hightower", "Kontrol düzlemi sezgisi", "1", "lab", "C", "Açık"),
            ("Helm Docs", "Helm", "CNCF", "Paket yönetimi", "1", "docs", "C", "Açık"),
            ("Terraform / OpenTofu Learn", "Terraform / OpenTofu", "HashiCorp / OpenTofu", "Altyapı kodu", "1", "docs", "C", "Açık"),
            ("Ansible Documentation", "Ansible", "Red Hat", "Otomasyon", "1", "docs", "C", "Resmi"),
            ("GitHub Actions + GitLab CI docs", "CI Belgeleri", "GitHub / GitLab", "CI kuyruğu", "2", "docs", "C", "Resmi"),
            ("Jenkins User Handbook", "Jenkins El Kitabı", "Jenkins", "Klasik CI", "1", "docs", "C", "Açık"),
            ("Argo CD / Flux docs", "GitOps (Argo/Flux)", "CNCF", "GitOps", "1", "docs", "C", "Açık"),
            ("Prometheus + Grafana + Loki + Tempo (çekirdek)", "Gözlem Yığını", "CNCF / Grafana", "Metrik/log/iz", "1", "docs", "C", "Açık"),
            ("OpenTelemetry Docs", "OpenTelemetry", "CNCF", "Telemetri standardı", "1", "docs", "C", "Açık"),
            ("Nginx / Caddy docs", "Nginx / Caddy", "F5 / Caddy", "Web sunucu / vekil", "2", "docs", "C", "Resmi"),
            ("Google SRE Book", "Google SRE Kitabı", "Google", "Güvenilirlik", "1", "~500+", "C/H", "Açık"),
            ("Google SRE Workbook", "Google SRE Çalışma Kitabı", "Google", "SRE pratik", "1", "~400+", "C/H", "Açık"),
            ("Site Reliability Engineering practices (açık ek yazılar)", "SRE Ek Yazılar", "Google/CNCF", "Pekiştirme", "1", "seçme", "C", "Açık"),
            ("MIT Missing Semester", "Eksik Dönem", "MIT", "Araç ustalık", "1", "kurs", "C", "Açık"),
            ("12-Factor + Beyond (operasyon eşlik)", "12-Factor Operasyon", "Heroku + ekler", "Servis işletimi", "1", "docs", "C", "Açık"),
            ("Packer + Vagrant docs", "Packer / Vagrant", "HashiCorp", "İmaj / dev ortam", "2", "docs", "C", "Açık"),
            ("Istio / Linkerd docs (seçme)", "Servis Ağı", "CNCF", "Service mesh", "1", "docs", "C", "Açık"),
            ("Chaos Engineering principles (PrinciplesofChaos + Litmus/ChaosMesh docs)", "Kaos Mühendisliği", "PrinciplesofChaos / CNCF", "Dayanıklılık deneyi", "1", "docs", "C", "Açık"),
            ("Nix / NixOS manuals (çekirdek)", "Nix / NixOS", "NixOS", "Bildirimsel sistem", "1", "docs", "C", "Açık"),
            ("Nomad / Consul docs (çekirdek)", "Nomad / Consul", "HashiCorp", "Orkestrasyon alternatifi", "2", "docs", "C", "Açık"),
        ],
    ),
    "10_VERI_BILIMI": (
        "10 VERİ BİLİMİ",
        [
            ("Introduction to Statistical Learning (ISLR2)", "İstatistiksel Öğrenmeye Giriş", "James et al.", "İstatistik+ML köprüsü", "1", "~600", "B", "Ücretsiz PDF"),
            ("Elements of Statistical Learning", "İstatistiksel Öğrenmenin Öğeleri", "Hastie et al.", "İleri istatistiksel öğrenme", "1", "~750", "B", "Ücretsiz PDF"),
            ("Think Stats / Think Bayes", "İstatistik / Bayes'i Düşün", "Allen Downey", "Pratik istatistik", "2", "~200+/kitap", "B", "CC"),
            ("Bayesian Methods for Hackers", "Bilgisayar Korsanları için Bayes", "Cam Davidson-Pilon", "Bayes pratik", "1", "~250+", "B", "Açık"),
            ("Python Data Science Handbook", "Python Veri Bilimi El Kitabı", "Jake VanderPlas", "Pandas/NumPy", "1", "~500", "B", "Açık"),
            ("R for Data Science (2e)", "Veri Bilimi için R", "Wickham et al.", "Tidyverse hattı", "1", "~500+", "B", "Açık"),
            ("OpenIntro Statistics", "OpenIntro İstatistik", "OpenIntro", "Temel istatistik", "1", "~400", "B", "Açık"),
            ("Computational and Inferential Thinking (Data 8)", "Hesaplamalı ve Çıkarımsal Düşünme", "Berkeley Data 8", "Veri bilimi girişi", "1", "~400+", "B", "Açık"),
            ("Forecasting: Principles and Practice (3e)", "Tahmin: İlkeler ve Uygulama", "Hyndman; Athanasopoulos", "Zaman serisi", "1", "~500+", "B", "Açık"),
            ("Causal Inference: The Mixtape", "Nedensel Çıkarım: Mixtape", "Scott Cunningham", "Nedensellik", "1", "~500+", "B", "Açık"),
            ("The Effect (Huntington-Klein) — açık", "Etki (Nedensel)", "Nick Huntington-Klein", "Nedensel yöntemler", "1", "~600+", "B", "Açık"),
            ("pandas + Polars + NumPy user guides", "Tablo / Dizi Kütüphaneleri", "pandas/Polars/NumPy", "Veri yapısı pratik", "3", "docs", "B", "Resmi"),
            ("Apache Spark Programming Guide", "Spark Programlama", "ASF", "Büyük veri işleme", "1", "docs", "B/C", "Açık"),
            ("Data Science for Good / DSSG açık müfredat seçkisi", "Toplumsal Veri Bilimi Seçkisi", "DSSG vd.", "Etik veri pratiği", "1", "seçme", "B/E", "Açık"),
            ("Feature Engineering for ML (açık Google/kurs notları seçme)", "Öznitelik Mühendisliği", "Google/çeşitli açık", "Öznitelik sanatı", "1", "notlar", "B", "Açık"),
            ("Visualization Analysis and Design — açık eşlik / Munzner slayt", "Görselleştirme Analizi (slayt)", "Tamara Munzner", "Viz teorisi", "1", "slayt", "B/Sahne", "Açık slayt"),
            ("From Data to Viz + Claus Wilke Fundamentals (açık sürüm)", "Veriden Görsele", "Wilke / data-to-viz", "Görselleştirme ilkeleri", "1", "~300+", "B", "Açık sürüm"),
            ("Google Advanced Data Analytics / Coursera açık not seçkisi", "İleri Veri Analitiği Notları", "Google", "Pratik analitik", "1", "notlar", "B", "Açık kısımlar"),
        ],
    ),
    "11_CS_OMURGA": (
        "11 BİLGİSAYAR BİLİMİ OMURGASI",
        [
            ("Nand2Tetris / Elements of Computing Systems (açık materyal)", "Nand2Tetris", "Nisan; Schocken", "Transistörden OS'a", "1", "~300+ +kurs", "A", "Açık"),
            ("Computer Science from the Bottom Up", "Aşağıdan Yukarı CS", "Bottom Up CS", "Sistem tabanlı CS", "1", "~200+", "A", "Açık"),
            ("CS50x açık ders materyali", "CS50", "Harvard", "Geniş CS girişi", "1", "kurs", "A", "Lisansına uygun"),
            ("Berkeley CS61A/B/C açık materyal", "Berkeley CS61 Üçlüsü", "UC Berkeley", "Programlama+veri+makine", "3", "kurs seti", "A", "Açık"),
            ("MIT 6.0001 / 6.0002 OCW", "MIT Python/CS Giriş", "MIT OCW", "Giriş omurgası", "2", "kurs", "A", "OCW"),
            ("MIT 6.004 / Computation Structures OCW", "Hesaplama Yapıları", "MIT OCW", "Donanım-yazılım köprüsü", "1", "kurs", "A", "OCW"),
            ("OSSU curriculum açık kitap seti", "OSSU Açık Müfredat", "OSSU", "Tam CS yolu (açık olanlar)", "çok", "değişken", "A", "Yalnız açık"),
            ("Teach Yourself Computer Science (tycs) — kaynak listesi + açık hedefler", "Kendin CS Öğret", "TYCS", "Omurga haritası", "1", "müfredat", "A", "Açık liste"),
            ("How to Think Like a Computer Scientist (çok dilli açık)", "Bilgisayar Bilimci Gibi Düşün", "Downey / CS aperitif", "Düşünce disiplini", "1", "~300", "A", "Açık"),
            ("BJC Berkeley / Snap! curriculum", "Güzellik ve Sevinç için CS", "Berkeley BJC", "CS + toplum", "1", "kurs", "A", "Açık"),
            ("Princeton COS 126 / Algs açık materyal", "Princeton CS Giriş", "Princeton", "Giriş+algoritma", "1", "kurs", "A", "Açık"),
            ("Stanford CS107 / CS110 açık notlar (varsa)", "Sistem Programlama Notları", "Stanford", "Sistem CS", "1", "notlar", "A", "Açık olanlar"),
            ("Open Source Society / freeCodeCamp Scientific Computing", "Bilimsel Hesaplama Sertifika Gövdesi", "freeCodeCamp", "Pratik CS", "1", "müfredat", "A", "Açık"),
            ("Missing Semester + The Missing Byte (seçme)", "Eksik Araçlar", "MIT + ek", "CS araç kültürü", "1", "kurs", "A", "Açık"),
            ("Structure and Interpretation of Computer Programs (SICP)", "SICP", "Abelson; Sussman", "Zihin omurgası", "1", "~850", "A", "Açık — 01 ile örtüşür, omurga için şart"),
            ("Concepts, Techniques, and Models of Computer Programming (CTM) — açık?", "Programlama Kavramları (CTM açık sürüm)", "Van Roy; Haridi", "Çok paradigmalı", "1", "~900", "A", "Açık sürüm varsa"),
            ("Computer Science Field Guide (NZ)", "CS Alan Rehberi", "UC Canterbury", "Lise→üniversite köprüsü", "1", "geniş", "A", "Açık"),
            ("PicoCTF / CryptoHack eğitim yazıları (savunma-öğretim seçme)", "Öğretici CTF Yazıları (seçme)", "PicoCTF vd.", "Problem çözme kası — exploit üretme yok", "1", "seçme", "A/C", "Eğitim; dikkat"),
        ],
    ),
    "12_BILGISAYAR_MUH": (
        "12 BİLGİSAYAR MÜHENDİSLİĞİ",
        [
            ("The RISC-V Reader", "RISC-V Okuyucu", "Patterson; Waterman", "Açık ISA omurgası (CSAPP muadili yön)", "1", "~200+", "C", "Ücretsiz PDF"),
            ("RISC-V Specifications (unprivileged + privileged)", "RISC-V Spec", "RISC-V International", "ISA standardı", "2", "spec", "C", "Açık"),
            ("Computer Organization and Design RISC-V — açık ders eşlik (Patterson kurs)", "Bilgisayar Organizasyonu (RISC-V eşlik)", "Patterson kurs materyali", "Organizasyon sezgisi", "1", "notlar", "C", "Açık eşlik; kitap telifli değil"),
            ("MIT 6.004 Computation Structures", "MIT Hesaplama Yapıları", "MIT OCW", "Dijital → işlemci", "1", "kurs", "C", "OCW"),
            ("MIT 6.175 / 6.004 lab notes (açık)", "Donanım Lab Notları", "MIT", "FPGA/işlemci lab", "1", "lab", "C", "Açık"),
            ("Ben Eater 8-bit computer (site metni + şema anlatımı)", "Ben Eater 8-bit", "Ben Eater", "İşlemci sezgisi elle", "1", "site", "C", "Açık"),
            ("Nand2Tetris Part II (VM/compiler/OS) açık", "Nand2Tetris II", "Nisan; Schocken", "Yığın→derleyici→OS", "1", "kurs", "C", "Açık"),
            ("FPGA/Verilog/SystemVerilog açık tutorial seti", "FPGA / HDL Öğretici", "ASIC World / HDLbits / topluluk", "Gömülü mantık", "1", "tutorial", "C", "Seçme açık"),
            ("HDLBits problem set", "HDLBits", "HDLBits", "HDL kası", "1", "alıştırma", "C", "Açık"),
            ("Chisel / SpinalHDL docs (çekirdek)", "Chisel / SpinalHDL", "Berkeley / Spinal", "Donanım-DSL", "1", "docs", "C", "Açık"),
            ("OpenROAD / Skywater PDK docs (çekirdek seçme)", "Açık Silikon Akışı", "OpenROAD / Google-Skywater", "Çip akışı ufku", "1", "docs", "C", "Açık"),
            ("Computer Architecture — Quantitative Approach açık slayt/not (Hennessy kurs)", "Bilgisayar Mimarisi Notları", "Hennessy/Patterson kurs", "İleri mimari (slayt)", "1", "slayt", "C", "Açık slayt"),
            ("Onur Mutlu lecture notes (ETH/CMU) — açık", "Modern Bilgisayar Mimarisi Dersleri", "Onur Mutlu", "Bellek/işlemci araştırma seviyesi", "1", "notlar+video metin", "C", "Açık"),
            ("gem5 documentation", "gem5 Simülatör", "gem5", "Mimari simülasyon", "1", "docs", "C", "Açık"),
            ("QEMU internals docs (seçme) + TCG", "QEMU İç Yapı", "QEMU", "Emülasyon", "1", "docs", "C", "Açık"),
            ("USB / PCIe / AXI açık spec özetleri (seçme)", "Veriyolu Spec Seçkisi", "USB-IF / PCI-SIG özet / ARM AXI", "Donanım arayüzleri", "1", "spec özet", "C", "Açık olanlar"),
            ("Maker/CPU course: From Nand to Tetris + TinyTapeout docs", "TinyTapeout + Nand hattı", "TinyTapeout", "Gerçek çip denemesi ufku", "1", "docs", "C", "Açık"),
            ("Digital Design and Computer Architecture — Harris açık slayt varsa", "Sayısal Tasarım Slaytları", "Harris; Harris", "Ders slaytları", "1", "slayt", "C", "Yalnız açık slayt"),
        ],
    ),
    "13_MATEMATIK_CS": (
        "13 MATEMATİK (CS)",
        [
            ("Mathematics for Computer Science (MIT 6.042)", "CS için Matematik", "Lehman; Leighton; Meyer", "Kesikli omurga", "1", "~500+", "B", "Açık"),
            ("Book of Proof", "İspat Kitabı", "Richard Hammack", "İspat dili", "1", "~350", "B", "Açık"),
            ("Discrete Mathematics (Levin)", "Ayrık Matematik", "Oscar Levin", "Ayrık yapılar", "1", "~400", "B", "Açık"),
            ("Discrete Mathematics and its Applications — açık not eşlik (Rosen kurs)", "Ayrık Matematik Notları", "Rosen kurs açık", "Pekiştirme notları", "1", "notlar", "B", "Açık not"),
            ("A First Course in Linear Algebra (Kuttler)", "Lineer Cebire İlk Kurs", "Ken Kuttler", "Lineer cebir", "1", "~400+", "B", "Açık"),
            ("Interactive Linear Algebra (Georgia Tech)", "Etkileşimli Lineer Cebir", "Georgia Tech", "Görsel lineer", "1", "kitap", "B", "Açık"),
            ("3Blue1Brown Essence of Linear Algebra (script)", "Lineer Cebirin Özü", "Grant Sanderson", "Sezgi", "1", "script", "B", "İzinli metin"),
            ("OpenStax Calculus Vol 1–3", "OpenStax Kalkülüs", "OpenStax", "Analiz", "3", "~1000+/set", "B/G", "CC"),
            ("OpenStax Algebra and Trigonometry + Precalculus", "OpenStax Cebir/Trig/Prekalkülüs", "OpenStax", "Temel matematik", "2", "~1500+/set", "B", "CC"),
            ("Calculus Made Easy (Thompson) — kamu malı", "Kalkülüsü Kolaylaştıran", "Silvanus Thompson", "Klasik sezgi", "1", "~300", "B", "Kamu malı"),
            ("generatingfunctionology (Wilf)", "Üreteç Fonksiyonları", "Herbert Wilf", "Concrete Math muadili açık", "1", "~200+", "B", "Ücretsiz"),
            ("Information Theory, Inference, and Learning Algorithms (MacKay)", "Bilgi Teorisi, Çıkarım, Öğrenme", "David MacKay", "Bilgi+öğrenme omurgası", "1", "~600+", "B", "Ücretsiz"),
            ("Abstract Algebra: Theory and Applications (Judson)", "Soyut Cebir", "Tom Judson", "Cebir", "1", "~400+", "B", "Açık"),
            ("Elementary Number Theory (açık textbook seçkisi)", "Temel Sayılar Teorisi", "açık yazarlar", "Kriptoya köprü", "1", "~300", "B", "Açık"),
            ("Probability and Computing (Mitzenmacher) — açık slayt/not", "Olasılık ve Hesaplama Notları", "Mitzenmacher; Upfal kurs", "Rastgele algoritma", "1", "notlar", "B", "Açık not"),
            ("Introduction to Probability (Blitzstein — Stats 110 açık)", "Olasılığa Giriş", "Blitzstein; Hwang / Stats110", "Olasılık omurgası", "1", "kurs+kitap açık?", "B", "Açık kurs; kitap durumuna bak"),
            ("The Open Logic Project / forall x", "Açık Mantık Projesi", "Open Logic", "Mantık", "1", "~300+", "B/E", "Açık"),
            ("Category Theory for Programmers (Milewski) — açık", "Programcılar için Kategori Teorisi", "Bartosz Milewski", "Soyut kompozisyon", "1", "~500+", "B", "Açık"),
            ("Mathematics for Machine Learning (tekrar çapraz ref)", "ML Matematik", "Deisenroth et al.", "YZ matematik köprüsü", "1", "~400+", "B", "Ücretsiz"),
            ("Euclid's Elements (kamu malı) + modern commentary seçme", "Öklid Elemanları", "Öklid", "Geometri kökü", "13", "klasik", "B/G", "Kamu malı"),
        ],
    ),
    "14_FIZIK": (
        "14 FİZİK",
        [
            ("OpenStax University Physics Vol 1–3", "OpenStax Üniversite Fiziği", "OpenStax", "Fizik omurgası / sahne fiziği", "3", "~1500+/set", "D/G", "CC"),
            ("OpenStax College Physics", "OpenStax Koleji Fiziği", "OpenStax", "Giriş fizik", "1", "~1000", "D", "CC"),
            ("OpenStax Astronomy / College Physics ek", "OpenStax Astronomi", "OpenStax", "Gökyüzü sahnesi", "1", "~1000+", "D/G", "CC"),
            ("Feynman Lectures on Physics (açık HTML)", "Feynman Fizik Dersleri", "Feynman; Leighton; Sands", "Derin sezgi", "3", "açık HTML", "D/G", "Caltech açık"),
            ("Motion Mountain", "Hareket Dağı", "Christoph Schiller", "Ücretsiz fizik ansiklopedisi", "5", "~1500+/set", "D", "Ücretsiz"),
            ("Light and Matter", "Işık ve Madde", "Benjamin Crowell", "Açık fizik kitabı", "1", "~900+", "D", "Açık"),
            ("HyperPhysics", "HyperPhysics", "Georgia State", "Kavram ağı", "1", "ansiklopedi", "D", "Eğitim"),
            ("Physics (Aristotle) + Newton Principia seçme (kamu malı)", "Klasik Fizik Kök Metinleri", "Aristoteles / Newton", "Tarihsel omurga", "2", "klasik", "D/G", "Kamu malı"),
            ("Relativity: The Special and General Theory (Einstein) — kamu malı", "Görelilik", "Albert Einstein", "Görelilik sezgisi", "1", "~200", "D", "Kamu malı"),
            ("Qiskit Textbook", "Qiskit Ders Kitabı", "IBM Quantum", "Kuantum hesaplama pratik", "1", "kurs kitap", "D/B", "Açık"),
            ("Quantum Computing for the Very Curious (Andy Matuschak / Michael Nielsen)", "Çok Meraklılar için Kuantum", "Nielsen; Matuschak", "Kuantum sezgi", "1", "essay-kitap", "D/B", "Açık"),
            ("Quantum Computation and Quantum Information — Nielsen/Chuang açık not eşlik", "Kuantum Bilgi Notları", "Nielsen; Chuang kurs", "QI pekiştirme", "1", "notlar", "D/B", "Açık not"),
            ("MIT 8.01 / 8.02 / 8.03 OCW", "MIT Klasik Fizik Üçlüsü", "MIT OCW", "Mekanik/EM/dalga", "3", "kurs", "D", "OCW"),
            ("MIT 8.04 / 8.05 Quantum OCW", "MIT Kuantum OCW", "MIT OCW", "Kuantum dersi", "2", "kurs", "D", "OCW"),
            ("Structure and Interpretation of Classical Mechanics (SICM) — açık", "Klasik Mekaniğin Yapısı", "Sussman; Wisdom", "Mekanik+Scheme ruhu", "1", "~500+", "D", "Açık"),
            ("Think Physics / Modeling Instruction açık materyal seçkisi", "Fizik Modelleme Seçkisi", "çeşitli", "Öğretim modelleri", "1", "seçme", "D", "Açık"),
            ("NASA / ESA açık eğitim fizik paketleri (seçme)", "Uzay Ajansı Eğitim Paketi", "NASA/ESA", "Uygulamalı fizik", "1", "seçme", "D/G", "Kamu"),
        ],
    ),
    "15_ELEKTRONIK": (
        "15 ELEKTRONİK",
        [
            ("Lessons in Electric Circuits", "Elektrik Devreleri Dersleri", "Tony Kuphaldt", "Elektronik omurgası", "6", "~2000+/set", "D", "Açık"),
            ("All About Circuits Textbook", "All About Circuits", "AAC", "Devre ansiklopedisi", "1", "geniş", "D", "Açık"),
            ("Op Amps for Everyone (TI)", "Herkes için Op-Amp", "Texas Instruments", "Op-amp tasarımı", "1", "~500+", "D", "Ücretsiz TI"),
            ("The Art of Electronics — x-Chapters / açık lab eşlik varsa", "Elektronik Sanatı (açık eşlik)", "Horowitz; Hill eşlik", "Yalnız açık lab/x", "1", "değişken", "D", "Telifli kitap yok"),
            ("Electronics textbooks OpenStax / LibreTexts (seçme)", "LibreTexts Elektronik", "LibreTexts", "Akademik gövde", "1", "seçme", "D", "Açık"),
            ("KiCad Documentation + Getting Started", "KiCad", "KiCad", "PCB tasarım", "1", "docs", "D", "Açık"),
            ("LTspice / ngspice docs + örnekler", "SPICE Simülasyon", "ADI / ngspice", "Devre simülasyonu", "1", "docs", "D", "Açık"),
            ("CircuitPython Docs + Adafruit Learning System (çekirdek)", "CircuitPython + Adafruit", "Adafruit", "MikroPython elektronik", "1", "docs+öğretici", "D", "Açık"),
            ("Arduino Language Reference + Project Hub seçme", "Arduino", "Arduino", "Hobi gömülü giriş", "1", "docs", "D", "Resmi"),
            ("SparkFun Learn (çekirdek set)", "SparkFun Öğreticileri", "SparkFun", "Pratik elektronik", "1", "seçme", "D", "Açık"),
            ("EEVblog datasheet survival + açık lab notları (seçme)", "Datasheet Okuma / Lab", "EEVblog / topluluk", "Ölçüm kültürü", "1", "seçme", "D", "Açık"),
            ("The Hands-on XBEE / RF açık tutorial seçkisi", "RF / Kablosuz Giriş", "çeşitli açık", "Radyo sezgisi", "1", "tutorial", "D", "Seçme"),
            ("IPC-2221 özet / açık PCB design guides (seçme)", "PCB Tasarım Rehberleri", "IPC özet / açık guide", "Kart disiplini", "1", "rehber", "D", "Açık olanlar"),
            ("Falstad Circuit Simulator + dokümantasyon", "Falstad Devre Simülatörü", "Paul Falstad", "Görsel devre sezgisi", "1", "app+docs", "D", "Açık"),
            ("Open Source Hardware Association best practices", "Açık Donanım İlkeleri", "OSHWA", "Açık donanım kültürü", "1", "docs", "D", "Açık"),
            ("Raspberry Pi Pico / RP2040 Datasheet + SDK", "RP2040 / Pico", "Raspberry Pi", "Modern mikrodenetleyici", "1", "datasheet+SDK", "D", "Resmi"),
            ("Espressif ESP32 Hardware docs (çekirdek)", "ESP32 Donanım", "Espressif", "WiFi gömülü donanım", "1", "docs", "D/I", "Resmi"),
        ],
    ),
    "16_ROBOTIK": (
        "16 ROBOTİK",
        [
            ("Modern Robotics (Lynch; Park)", "Modern Robotik", "Lynch; Park", "Kinematik/kontrol omurgası", "1", "~500+", "D", "Ücretsiz PDF+kurs"),
            ("Robotics, Vision and Control (Corke) — ücretsiz PDF", "Robotik, Görü ve Kontrol", "Peter Corke", "Pratik robot+görü", "1", "~700+", "D", "Ücretsiz"),
            ("Underactuated Robotics (Tedrake)", "Eksik Eyleyicili Robotik", "Russ Tedrake", "İleri kontrol", "1", "~400+", "D", "Açık"),
            ("Planning Algorithms (LaValle) — ücretsiz", "Planlama Algoritmaları", "Steven LaValle", "Hareket planlama", "1", "~800+", "D", "Ücretsiz"),
            ("ROS 2 Docs + Tutorials + Design articles", "ROS 2", "Open Robotics", "Robot yazılım yığını", "1", "docs — geniş", "D/I", "Açık"),
            ("MoveIt 2 Documentation", "MoveIt 2", "PickNik / MoveIt", "Manipülasyon planlama", "1", "docs", "D", "Açık"),
            ("Nav2 Documentation", "Nav2", "Open Navigation", "Mobil navigasyon", "1", "docs", "D", "Açık"),
            ("PythonRobotics", "PythonRobotics", "Atsushi Sakai", "Algoritma örnekleri", "1", "kod+anlatım", "D", "Açık"),
            ("Gazebo / Ignition / Webots / CoppeliaSim docs", "Robot Simülatörleri", "Open Robotics / Cyberbotics vd.", "Simülasyon tiyatrosu", "1", "docs", "D/Sahne", "Açık"),
            ("MuJoCo Documentation", "MuJoCo", "Google DeepMind", "Fizik tabanlı robot sim", "1", "docs", "D", "Açık"),
            ("Gymnasium Robotics / MoJoCo environments docs", "Robot RL Ortamları", "Farama", "Öğrenen robot", "1", "docs", "D/B", "Açık"),
            ("Aerial Robotics / PX4 User Guide", "PX4 / İHA", "PX4", "Uçan robot", "1", "docs", "D", "Açık"),
            ("Boston Dynamics / robotics ethics + safety açık rapor seçkisi", "Robot Güvenliği / Etik Seçkisi", "standart kurumlar", "Güvenli robot", "1", "seçme", "D/E", "Açık rapor"),
            ("Coursera Aerial Robotics / Modern Robotics açık not eşlik", "Robotik Kurs Notları", "UPenn / Northwestern açık", "Pekiştirme", "1", "notlar", "D", "Açık"),
            ("OpenCV for Robotics tutorials (seçme)", "Robot için OpenCV", "OpenCV", "Göz-el köprüsü", "1", "docs", "D/Sahne", "Açık"),
            ("URDF / SDF / MJCF format docs", "Robot Tanım Formatları", "ROS / MuJoCo", "Sahne-robot modeli", "1", "docs", "D/Sahne", "Açık"),
            ("Humanoid robotics açık survey/not seçkisi", "İnsansı Robot Seçkisi", "akademik açık", "İnsansı ufuk", "1", "seçme", "D", "Açık"),
        ],
    ),
    "17_MEKATRONIK": (
        "17 MEKATRONİK - GÖMÜLÜ",
        [
            ("ESP-IDF Programming Guide", "ESP-IDF", "Espressif", "ESP32 gömülü yazılım", "1", "docs — geniş", "D/I", "Resmi"),
            ("FreeRTOS Kernel Docs + Mastering FreeRTOS (açık)", "FreeRTOS", "Amazon FreeRTOS", "Gerçek zamanlı OS", "1", "docs", "D/I", "Açık"),
            ("Zephyr Project Documentation", "Zephyr RTOS", "Linux Foundation", "Modern gömülü OS", "1", "docs", "D/I", "Açık"),
            ("PlatformIO Docs", "PlatformIO", "PlatformIO", "Gömülü toolchain", "1", "docs", "D", "Açık"),
            ("Raspberry Pi Documentation (OS+Pico+HAT)", "Raspberry Pi Belgeleri", "Raspberry Pi Ltd.", "Tek kart bilgisayar", "1", "docs", "D", "Resmi"),
            ("Yocto Project Docs + Mega-Manual (çekirdek)", "Yocto", "Yocto Project", "Gömülü Linux imaj", "1", "docs — geniş", "D", "Açık"),
            ("Buildroot Manual", "Buildroot", "Buildroot", "Hafif gömülü Linux", "1", "docs", "D", "Açık"),
            ("STM32 / Cube docs (çekirdek seçme) + libopencm3", "STM32 Gömülü", "ST / libopencm3", "ARM Cortex-M pratik", "1", "docs", "D", "Resmi+açık"),
            ("Nordic nRF Connect SDK docs", "nRF Connect", "Nordic", "BLE gömülü", "1", "docs", "D", "Resmi"),
            ("Embedded C Coding Standard (Barr) — ücretsiz?", "Gömülü C Standardı (Barr açık sürüm)", "Michael Barr", "Gömülü disiplin", "1", "~100", "D", "Ücretsizse"),
            ("Making Embedded Systems — açık eşlik/slayt yoksa Elecia White konuşma notları", "Gömülü Sistem Konuşma/Not", "Elecia White", "Gömülü kültür", "1", "notlar", "D", "Açık not"),
            ("Mastering STM32 (Coletta) — ücretsiz PDF kontrol", "STM32 Ustalık (ücretsizse)", "Carmine Coletta", "STM32 derin", "1", "~700+", "D", "Ücretsizse al; değilse atla"),
            ("CAN / Modbus / I2C / SPI açık protokol rehberleri", "Gömülü Veriyolu Paketi", "çeşitli açık", "Sensör ağı", "1", "rehber seti", "D", "Açık"),
            ("PID without a PhD + control tutorials (Tim Wescott / açık)", "PID / Kontrol Öğretici", "Wescott vd.", "Kontrol döngüsü", "1", "yazı", "D", "Açık"),
            ("Arduino + FreeRTOS + ESP32 mekatronik proje tarifleri (seçme kaliteli)", "Mekatronik Proje Seçkisi", "topluluk süzülmüş", "El-pratik", "1", "seçme", "D", "Kalite süz"),
            ("Open Source Ecology / OpenHardware mekatronik (seçme)", "Açık Mekanik Tasarım", "OSE / OSHW", "Fiziksel üretim", "1", "seçme", "D", "Açık"),
            ("PLC / IEC 61131 açık giriş + OpenPLC docs", "OpenPLC / IEC 61131", "OpenPLC", "Endüstriyel kontrol girişi", "1", "docs", "D", "Açık"),
            ("ros2_control + micro-ROS docs", "ros2_control / micro-ROS", "ROS", "Gömülü↔robot köprüsü", "1", "docs", "D", "Açık"),
        ],
    ),
    "18_ARASTIRMA": (
        "18 BİLİMSEL ARAŞTIRMA",
        [
            ("The Turing Way", "Turing Yolu", "The Turing Way", "Yeniden üretilebilir araştırma omurgası", "1", "geniş rehber", "E", "Açık"),
            ("The Open Science Manual / FOSTER açık kaynaklar", "Açık Bilim El Kitabı", "FOSTER / Open Science", "Açık bilim kültürü", "1", "docs", "E", "Açık"),
            ("Research Data Management açık rehberler (UKRN / Harvard)", "Araştırma Veri Yönetimi", "UKRN / Harvard", "Veri yaşam döngüsü", "1", "rehber", "E", "Açık"),
            ("OpenStax Introductory Statistics", "OpenStax Giriş İstatistik", "OpenStax", "Araştırma istatistiği", "1", "~800", "E", "CC"),
            ("OpenStax Research Methods / Psychology research ch", "Araştırma Yöntemleri (OpenStax)", "OpenStax", "Yöntem", "1", "bölüm/kitap", "E", "CC"),
            ("Reproducible Research with R and RStudio (açık sürüm)", "R ile Yeniden Üretilebilir Araştırma", "Gandrud / açık eşlik", "R araştırma hattı", "1", "~300+", "E", "Açık sürüm"),
            ("Good Enough Practices in Scientific Computing (Paper)", "Bilimsel Hesaplamada Yeterince İyi Pratikler", "Wilson et al.", "Bilim+kod disiplini", "1", "makale", "E", "Açık"),
            ("Software Carpentry / Data Carpentry lessons", "Carpentry Dersleri", "Carpentries", "Araştırmacıya araç", "1", "müfredat", "E", "Açık"),
            ("How to Read a Paper (Keshav) + Three passes", "Makale Nasıl Okunur", "S. Keshav", "Okuma tekniği", "1", "kısa", "E", "Açık"),
            ("Writing for Computer Science — açık eşlik / Zobel slayt", "CS için Yazma (slayt/eşlik)", "Justin Zobel", "Bilimsel yazım", "1", "slayt", "E", "Açık eşlik"),
            ("PhilPapers / SEP scientific method maddeleri", "Bilim Yöntemi (SEP)", "SEP", "Yöntem felsefesi", "1", "maddeler", "E", "Açık"),
            ("PRISMA / CONSORT açık standartlar (seçme)", "Raporlama Standartları", "PRISMA/CONSORT", "Şeffaf rapor", "1", "standart", "E", "Açık"),
            ("Registered Reports + OSF Guides", "Kayıtlı Rapor + OSF", "OSF", "Ön-kayıt disiplini", "1", "rehber", "E", "Açık"),
            ("Citation styles + Zotero documentation", "Zotero / Atıf", "Zotero", "Kaynakça motoru", "1", "docs", "E", "Açık"),
            ("LaTeX / Overleaf Learn + TeXbook açık eşlik seçme", "LaTeX Öğrenme", "Overleaf / TeX", "Bilimsel dizgi", "1", "docs", "E", "Açık"),
            ("Peer Review: The Nuts and Bolts (açık Sense About Science)", "Hakemlik Cevheri", "Sense About Science", "Değerlendirme kültürü", "1", "~50+", "E", "Açık"),
            ("Experimentation for Engineers (açık özet/makale seçkisi)", "Mühendisler için Deney Tasarımı", "açık kaynaklar", "A/B ve deney", "1", "seçme", "E", "Açık"),
            ("UNESCO Open Science Recommendation", "UNESCO Açık Bilim", "UNESCO", "Küresel açık bilim normu", "1", "metin", "E", "Kamu"),
        ],
    ),
    "19_PSIKOLOJI": (
        "19 PSİKOLOJİ",
        [
            ("OpenStax Psychology 2e", "OpenStax Psikoloji", "OpenStax", "Dikkat/bellek/öğrenme — hafıza odası", "1", "~700+", "E", "CC"),
            ("Noba Psychology modules (tam set seçkisi)", "Noba Psikoloji Modülleri", "Noba Project", "Modüler kaliteli gövde", "çok", "modül seti", "E", "Açık"),
            ("MIT OCW Intro Psychology", "MIT Giriş Psikoloji", "MIT OCW", "Üniversite dersi", "1", "notlar", "E", "OCW"),
            ("Yale PSYC 110 Open Yale (Emotion/Intro — Ginger / Bloom)", "Yale Açık Psikoloji", "Open Yale Courses", "Klasik giriş", "1", "kurs", "E", "Açık"),
            ("NIH / NIMH kamu bilgilendirme + DSM özeti değil kamu sayfaları", "NIH Ruh Sağlığı Bilgilendirme", "NIH/NIMH", "Kamuya açık özet", "1", "seçme", "E", "Kamu"),
            ("APA Learning Psychology açık kaynaklar (seçme)", "APA Öğrenme Kaynakları", "APA", "Meslek dili", "1", "seçme", "E", "Açık olanlar"),
            ("Attention (Styles / Posner açık review seçkisi)", "Dikkat Seçkisi", "akademik açık", "Dikkat motoru — Rüzgar odağı", "1", "seçme", "E", "Açık"),
            ("Memory: Open textbook chapters / Baddeley özet açık makaleler", "Bellek Açık Metinler", "çeşitli açık", "Çalışma belleği modeli", "1", "seçme", "E", "Açık"),
            ("Cognitive Biases — Heuristics (Tversky/Kahneman açık makaleler)", "Bilişsel Yanlılıklar (açık makaleler)", "Kahneman; Tversky", "Karar tuzakları", "1", "makale seti", "E", "Açık makaleler"),
            ("Flow (Csikszentmihalyi) — açık makale/özet; kitap telifli", "Akış (açık makaleler)", "Csikszentmihalyi", "Derin odak", "1", "makale", "E", "Açık makale"),
            ("Self-Determination Theory açık kaynaklar", "Öz-Belirleme Kuramı", "Deci; Ryan siteleri", "Motivasyon", "1", "docs", "E", "Açık"),
            ("Open Encyclopedia of Cognitive Science — psychology edges", "Açık Bilişsel Ansiklopedi (psikoloji)", "OECS", "Ansiklopedik", "1", "maddeler", "E", "Açık"),
            ("Simply Psychology / University open course notes (kalite süzülmüş seçme)", "Psikoloji Ders Notu Seçkisi", "çeşitli üniversite", "Pekiştirme", "1", "seçme", "E", "Süzülmüş"),
            ("Sleep / Circadian NIH + açık review", "Uyku ve Ritim", "NIH + açık", "Nefes/uyanıklık tasarımı", "1", "seçme", "E", "Kamu"),
            ("Emotion theory açık SEP + psikoloji maddeleri", "Duygu Kuramı", "SEP + psikoloji", "Sahne duygu modeli", "1", "maddeler", "E", "Açık"),
            ("Developmental Psychology OpenStax / Noba ch", "Gelişim Psikolojisi", "OpenStax/Noba", "Öğrenme yaşı", "1", "bölüm", "E", "Açık"),
            ("Social Psychology Noba + OpenStax ch", "Sosyal Psikoloji", "Noba/OpenStax", "İnsan etkileşimi", "1", "bölüm", "E", "Açık"),
            ("Educational Psychology açık textbook (Seifert/Sutton veya benzeri)", "Eğitim Psikolojisi", "açık textbook", "Öğretme motoru", "1", "~400+", "E", "Açık"),
        ],
    ),
    "20_BILISSEL": (
        "20 BİLİŞSEL BİLİMLER",
        [
            ("SEP — Cognitive Science + Philosophy of Mind seti", "SEP Bilişsel Bilim / Zihin", "Stanford Encyclopedia", "Kavram omurgası", "1", "madde seti", "E", "Açık"),
            ("Open Encyclopedia of Cognitive Science", "Açık Bilişsel Bilim Ansiklopedisi", "OECS", "Modern ansiklopedi", "1", "maddeler", "E", "Açık"),
            ("MIT OCW Introduction to Psychology / Cognitive Science notes", "MIT Bilişsel Notlar", "MIT OCW", "Ders gövdesi", "1", "notlar", "E", "OCW"),
            ("MIT 9.00 / 9.66 OCW (açık olanlar)", "MIT Beyin ve Biliş", "MIT OCW", "Nöro+biliş", "1", "kurs", "E", "OCW"),
            ("How the Brain Works — açık ders/kitap seçkisi (LibreTexts Neuroscience)", "LibreTexts Sinirbilim", "LibreTexts", "Beyin temeli", "1", "seçme", "E", "Açık"),
            ("Computational Cognitive Science açık müfredat (Tenenbaum / Griffiths notlar)", "Hesaplamalı Bilişsel Bilim", "Tenenbaum; Griffiths", "Bayesian zihin", "1", "notlar", "E/B", "Açık not"),
            ("Marr's levels + Vision (açık makale/bölüm)", "Marr Seviyeleri", "David Marr", "Görü hesaplama seviyeleri", "1", "klasik", "E", "Açık olanlar"),
            ("ACT-R / Soar cognitive architecture docs", "ACT-R / Soar", "CMU / Michigan", "Bilişsel mimari", "2", "docs", "E/B", "Açık"),
            ("Predictive Processing açık review seçkisi", "Öngörücü İşleme", "akademik açık", "Modern zihin modeli", "1", "seçme", "E", "Açık"),
            ("Embodied Cognition SEP + açık makaleler", "Bedenselleşmiş Biliş", "SEP", "Beden-zihin", "1", "maddeler", "E", "Açık"),
            ("OpenMind BBVA cognitive series (seçme kitapçık)", "OpenMind Bilişsel Seri", "BBVA OpenMind", "Popüler-bilim kaliteli", "1", "seçme", "E", "Açık"),
            ("Neuroscience: Canadian 1st Edition Open Textbook (veya benzeri açık)", "Açık Sinirbilim Ders Kitabı", "açık textbook", "Sinirbilim gövdesi", "1", "~700+", "E", "Açık"),
            ("The Mind Project / cognitive science open modules", "Mind Project Modülleri", "Illinois State / Mind Project", "Öğretim modülleri", "1", "modül", "E", "Açık"),
            ("Dual Process Theory açık makaleler", "Çift Süreç Kuramı", "Evans/Kahneman açık", "Sistem-1/2", "1", "makale", "E", "Açık"),
            ("Working Memory (Baddeley) açık review'lar", "Çalışma Belleği Review", "Baddeley vd.", "Hafıza mimarisi", "1", "review", "E", "Açık"),
            ("Language and Cognition açık (UD + cognitive linguistics seçme)", "Dil ve Biliş Seçkisi", "çeşitli açık", "Dil-zihin köprüsü", "1", "seçme", "E/B", "Açık"),
            ("Cognitive Load Theory açık makaleler (Sweller)", "Bilişsel Yük Kuramı", "John Sweller", "Öğretim tasarımı", "1", "makale", "E", "Açık"),
            ("Human-Computer Interaction open textbooks (seçme)", "İnsan-Bilgisayar Etkileşimi", "açık HCI book", "Arayüz zihni", "1", "~400+", "E/Sahne", "Açık"),
        ],
    ),
    "21_NLP_DIL": (
        "21 DİL - NLP",
        [
            ("Speech and Language Processing (3e draft)", "Konuşma ve Dil İşleme", "Jurafsky; Martin", "NLP omurgası (kritik)", "1", "~1000+", "B", "Ücretsiz draft"),
            ("NLTK Book", "NLTK Kitabı", "Bird; Klein; Loper", "Pratik NLP", "1", "~500", "B", "Açık"),
            ("spaCy Course + Industrial NLP docs", "spaCy Kurs + Docs", "Explosion", "Endüstriyel NLP", "1", "docs", "B", "Açık"),
            ("Hugging Face NLP Course", "HF NLP Kursu", "Hugging Face", "Transformer NLP", "1", "kurs", "B", "Açık"),
            ("Universal Dependencies guidelines + treebanks", "Evrensel Bağımlılıklar", "UD Project", "Anotasyon standardı", "1", "docs", "B", "Açık"),
            ("WordNet + PropBank + FrameNet docs (çekirdek)", "Sözcük Anlam Kaynakları", "Princeton / Colorado vd.", "Anlam grafı", "1", "docs", "B", "Açık"),
            ("fastText / SentencePiece / BPE yazıları + docs", "Alt-sözcük Tokenizasyon Paketi", "Meta / Google", "Token omurgası", "1", "docs", "B", "Açık"),
            ("Stanford Stanza + CoreNLP docs", "Stanza / CoreNLP", "Stanford NLP", "Klasik boru hattı", "1", "docs", "B", "Açık"),
            ("AllenNLP / Explainable NLP tutorials (açık kalan)", "AllenNLP Öğretici", "AI2", "Araştırma NLP", "1", "docs", "B", "Açık"),
            ("Kaldi / ESPnet / Whisper papers+docs (STT)", "Konuşma Tanıma Yığını", "Kaldi/ESPnet/OpenAI", "Kulak motoru", "1", "docs", "B/Sahne", "Açık"),
            ("TTS açık yığın: Piper / Coqui / VITS docs", "Konuşma Sentezi Yığını", "Rhasspy / Coqui", "Dil motoru", "1", "docs", "B/Sahne", "Açık"),
            ("Multilingual NLP (Masakhane / NLLB papers + docs seçme)", "Çok Dilli NLP", "Meta NLLB / Masakhane", "Dillerarası", "1", "seçme", "B", "Açık"),
            ("Turkish NLP: Zemberek / ITU Turkish NLP / TrTok açık kaynaklar", "Türkçe NLP Paketi", "Zemberek / İTÜ", "Rüzgar ana dili", "1", "docs+kod", "B", "Açık — kritik"),
            ("Turkish Language resources (TDD / Turkish Treebank UD)", "Türkçe Dil Kaynakları", "UD Turkish / TDD", "Türkçe ağaçbank", "1", "veri+docs", "B", "Açık"),
            ("Arabic NLP: CAMeL / Farasa / AraBERT docs (seçme)", "Arapça NLP Paketi", "CAMeL Lab vd.", "Şamile dili köprüsü", "1", "docs", "B", "Açık — kritik"),
            ("Linguistics Open Textbooks (Essentials of Linguistics / OpenStax?)", "Dilbilim Açık Ders Kitabı", "açık linguistics", "Dilbilim temeli", "1", "~400+", "B", "Açık"),
            ("Foundations of Statistical NLP — açık not eşlik (Manning kurs)", "İstatistiksel NLP Notları", "Manning; Schütze kurs", "Klasik istatistiksel", "1", "notlar", "B", "Açık not"),
            ("Information Retrieval + NLP kesişimi (MR + IR chapters çapraz)", "IR↔NLP Köprüsü", "çeşitli açık", "Arama+dil", "1", "seçme", "B/Sahne", "Açık"),
            ("Prompting / LLM evaluation açık rehberler (OpenAI/HF/Anthropic açık)", "LLM Değerlendirme / Prompt Rehberi", "HF/OpenAI açık", "Yerel beyin kalibrasyonu", "1", "docs", "B", "Açık"),
            ("Speech Processing (Rabiner özet) + açık DSP for speech seçkisi", "Konuşma İşleme Seçkisi", "açık DSP", "Ses sinyali", "1", "seçme", "B", "Açık"),
        ],
    ),
    "22_FELSEFE": (
        "22 FELSEFE (EK)",
        [
            ("Stanford Encyclopedia of Philosophy — AI/Mind/Ethics/Language seti", "SEP Çekirdek Felsefe Seti", "SEP", "Ansiklopedik pusula", "1", "madde seti geniş", "E", "Açık"),
            ("Internet Encyclopedia of Philosophy (IEP) seçkisi", "IEP Seçkisi", "IEP", "İkinci ansiklopedi", "1", "maddeler", "E", "Açık"),
            ("Open Logic / forall x / Language Truth and Logic açık mantık", "Açık Mantık Paketi", "Open Logic Project", "Mantık organı", "1", "~300+", "E", "Açık"),
            ("ACM Code of Ethics + IEEE Ethically Aligned Design", "ACM / IEEE Etik", "ACM / IEEE", "Meslek etiği", "2", "metin", "E", "Açık"),
            ("UNESCO Recommendation on the Ethics of AI", "UNESCO YZ Etiği", "UNESCO", "Küresel YZ etik", "1", "metin", "E", "Kamu"),
            ("EU AI Act resmi metin (kamu)", "AB YZ Yasası", "AB", "Hukuki çerçeve bilinci", "1", "metin", "E", "Kamu"),
            ("Platon — Devlet (kamu malı)", "Devlet", "Platon", "Adalet/siyaset kökü", "1", "klasik", "E", "Kamu malı"),
            ("Aristoteles — Nikomakhos'a Etik (kamu malı)", "Nikomakhos'a Etik", "Aristoteles", "Erdem etiği", "1", "klasik", "E", "Kamu malı"),
            ("Marcus Aurelius — Meditations (kamu malı)", "Düşünceler", "Marcus Aurelius", "Stoa özdisiplin", "1", "klasik", "E", "Kamu malı"),
            ("Epictetus — Enchiridion (kamu malı)", "El Kitabı", "Epiktetos", "Stoa pratik", "1", "klasik", "E", "Kamu malı"),
            ("Descartes — Meditations / Discourse (kamu malı)", "Descartes Meditasyonlar", "Descartes", "Özne/şüphe", "1", "klasik", "E", "Kamu malı"),
            ("Hume — Enquiry Concerning Human Understanding (kamu malı)", "İnsanın Anlama Yetisi", "David Hume", "Empirizm", "1", "klasik", "E", "Kamu malı"),
            ("Kant — Groundwork (kamu malı çeviri)", "Ahlak Metafiziğinin Temellendirilmesi", "Immanuel Kant", "Ödev etiği", "1", "klasik", "E", "Kamu malı"),
            ("Wittgenstein — Tractatus (kamu malı)", "Tractatus", "Wittgenstein", "Dil sınırı", "1", "klasik", "E", "Kamu malı"),
            ("Turing — Computing Machinery and Intelligence (makale)", "Makineler ve Zeka", "Alan Turing", "YZ felsefe kökü", "1", "makale", "E", "Açık"),
            ("Searle Chinese Room + yanıtlar (açık makaleler)", "Çin Odası Tartışması", "Searle + yanıtlar", "Anlama sorunu", "1", "makale seti", "E", "Açık"),
            ("Philosophy of Information (Floridi SEP + açık)", "Enformasyon Felsefesi", "Luciano Floridi / SEP", "Bilgi ontolojisi", "1", "maddeler", "E", "Açık"),
            ("Philosophy of Technology SEP seti", "Teknoloji Felsefesi", "SEP", "Araç-insan", "1", "maddeler", "E", "Açık"),
            ("İbn Sînâ / Fârâbî / İbn Rüşd açık metin seçkisi (kamu/açık)", "İslam Felsefesi Seçkisi", "İbn Sînâ; Fârâbî; İbn Rüşd", "Doğu-batı köprü — Rüzgar kimliği", "1", "seçme", "E", "Açık/kamu"),
            ("Gödel incompleteness açık anlatımlar (Nagel-Newman kamu? / SEP)", "Eksiklik Teoremleri Anlatımı", "SEP + açık", "Sınır bilinci", "1", "maddeler", "E", "Açık"),
        ],
    ),
    "23_EKONOMI": (
        "23 EKONOMİ",
        [
            ("The Economy / CORE Econ (The Economy 1.0 & 2.0)", "CORE Ekonomi", "CORE Econ", "Modern açık ders kitabı omurgası", "2", "~1000+/set", "E", "Açık — kritik"),
            ("Economy, Society, and Public Policy (CORE)", "Ekonomi, Toplum, Kamu Politikası", "CORE Econ", "Politika ekonomisi", "1", "~500+", "E", "Açık"),
            ("Doing Economics (CORE)", "Ekonomi Yapmak", "CORE Econ", "Ampirik ekonomi pratik", "1", "kurs kitap", "E", "Açık"),
            ("OpenStax Principles of Economics / Micro / Macro", "OpenStax Ekonomi İlkeleri", "OpenStax", "Klasik giriş seti", "3", "~1000+/set", "E", "CC"),
            ("Wealth of Nations (Adam Smith) — kamu malı", "Ulusların Zenginliği", "Adam Smith", "Klasik ekonomi kökü", "1", "~1000", "E", "Kamu malı"),
            ("General Theory of Employment (Keynes) — kamu malı kontrol", "İstihdam Genel Teori", "John Maynard Keynes", "Makro kök (kamuysa)", "1", "~400", "E", "Kamu malıysa"),
            ("Capital (Marx) Vol 1 — kamu malı", "Kapital Cilt 1", "Karl Marx", "Eleştirel ekonomi tarihi", "1", "~800+", "E", "Kamu malı"),
            ("Econlib / Liberty Fund eğitim seçkisi", "Econlib Eğitim", "Econlib", "Kavram yazıları", "1", "seçme", "E", "Açık"),
            ("MRU / Marginal Revolution University açık kurs metinleri", "MRU Kurs Metinleri", "Cowen; Tabarrok", "Modern öğretici", "1", "kurs", "E", "Açık"),
            ("Our World in Data (metodoloji + konu yazıları)", "Our World in Data", "OWID", "Ampirik dünya resmi", "1", "ansiklopedi", "E/G", "Açık"),
            ("World Bank Open Knowledge + Open Data essentials", "Dünya Bankası Açık Bilgi", "World Bank", "Kalkınma verisi", "1", "seçme", "E", "Açık"),
            ("Behavioral Economics açık kurs (Duke/Chicago açık not)", "Davranışsal Ekonomi Notları", "üniversite açık", "İnsan-ekonomi", "1", "notlar", "E", "Açık"),
            ("Rethinking Economics açık okuma listeleri", "Ekonomiyi Yeniden Düşün", "Rethinking Economics", "Çoğulcu ekonomi", "1", "liste+metin", "E", "Açık"),
            ("Economics of Networks / Information açık not seçkisi", "Ağ / Enformasyon Ekonomisi", "akademik açık", "Dijital ekonomi", "1", "notlar", "E", "Açık"),
            ("Platform / Attention economy açık makale seçkisi", "Platform / Dikkat Ekonomisi", "akademik açık", "Dikkat madenciliği bilinci", "1", "seçme", "E", "Açık"),
            ("Islamic Economics açık giriş metinleri (seçme akademik)", "İslam Ekonomisi Giriş", "akademik açık", "Kimlik köprüsü", "1", "seçme", "E", "Açık süzülmüş"),
            ("Financial Literacy OpenStax / açık rehberler", "Finansal Okuryazarlık", "OpenStax vd.", "Temel finans", "1", "~300+", "E", "Açık"),
            ("Complexity Economics (Santa Fe) açık yazılar", "Karmaşıklık Ekonomisi", "Santa Fe / açık", "Sistem ekonomisi", "1", "seçme", "E", "Açık"),
        ],
    ),
    "24_OYUN_TEORISI": (
        "24 OYUN TEORİSİ",
        [
            ("Multiagent Systems (Shoham; Leyton-Brown) — ücretsiz PDF", "Çok Etmenli Sistemler", "Shoham; Leyton-Brown", "Oyun+ajan omurgası", "1", "~500+", "E", "Ücretsiz — kritik"),
            ("Algorithmic Game Theory (Nisan et al.) — ücretsiz PDF", "Algoritmik Oyun Teorisi", "Nisan et al.", "Algoritma+oyun", "1", "~700", "E", "Ücretsiz"),
            ("SEP — Game Theory + Decision Theory + Social Choice", "SEP Oyun / Karar / Sosyal Seçim", "SEP", "Felsefi çerçeve", "3", "madde", "E", "Açık"),
            ("Game Theory (Open Yale / Ben Polak) — Open Yale Courses", "Yale Oyun Teorisi", "Ben Polak / Open Yale", "Klasik ders", "1", "kurs", "E", "Açık"),
            ("Stanford / MIT game theory OCW notes", "OCW Oyun Teorisi Notları", "Stanford/MIT", "Akademik pekiştirme", "1", "notlar", "E", "OCW"),
            ("GameTheory.net deep pages", "GameTheory.net", "GameTheory.net", "Eğitim ansiklopedisi", "1", "site", "E", "Açık"),
            ("Thinking in Bets / poker-decision açık makale değil — yerine: Rational Choice açık textbook seçkisi", "Rasyonel Seçim Açık Metin", "açık textbook", "Karar teorisi", "1", "~300+", "E", "Açık"),
            ("Auctions and Mechanism Design açık notlar (Roughgarden / Leyton-Brown)", "Mekanizma Tasarımı Notları", "Roughgarden vd.", "İhale/mekanizma", "1", "notlar", "E", "Açık"),
            ("Evolutionary Game Theory açık giriş (Weibull not / SEP)", "Evrimsel Oyun Teorisi", "SEP + notlar", "Evrim+strateji", "1", "maddeler", "E", "Açık"),
            ("Prisoner's Dilemma / Tragedy of Commons klasik makaleler (Hardin kamu?)", "Tutsak İkilemi / Müşterekler", "klasik makaleler", "İşbirliği sorunu", "1", "makale seti", "E", "Açık"),
            ("Cooperative Game Theory açık not seçkisi", "İşbirlikçi Oyun Teorisi", "akademik açık", "Koalisyon", "1", "notlar", "E", "Açık"),
            ("Behavioral Game Theory açık makale seçkisi (Camerer review)", "Davranışsal Oyun Teorisi", "Camerer vd.", "İnsan gerçekliği", "1", "review", "E", "Açık"),
            ("AI and Game Theory (multi-agent RL survey açık)", "YZ ve Oyun Teorisi Survey", "akademik açık", "Ajan toplumları", "1", "survey", "E/B", "Açık"),
            ("Voting theory / Arrow theorem SEP + açık not", "Oylama Teorisi", "SEP", "Sosyal seçim", "1", "maddeler", "E", "Açık"),
            ("Networks, Crowds, and Markets (Easley; Kleinberg) — ücretsiz PDF", "Ağlar, Kalabalıklar, Piyasalar", "Easley; Kleinberg", "Ağ+oyun+ekonomi", "1", "~800+", "E", "Ücretsiz — kritik"),
            ("The Art of Strategy — açık değil; yerine Dixit açık lecture notes varsa", "Strateji Ders Notları", "Dixit kurs açık", "Strateji sezgisi", "1", "notlar", "E", "Açık not"),
            ("Repeated games / folk theorem açık notlar", "Tekrarlı Oyunlar", "akademik açık", "Uzun vadeli işbirliği", "1", "notlar", "E", "Açık"),
            ("Security games / Stackelberg açık survey (savunma)", "Güvenlik Oyunları Survey", "akademik açık", "Savunma stratejisi", "1", "survey", "E/C", "Açık — exploit yok"),
        ],
    ),
    "25_SAHNE_OMURGA": (
        "25 SAHNE OMURGASI (kod+eser yakıtı)",
        [
            ("Godot Engine Documentation + Tutorials", "Godot Motor", "Godot", "2D/3D sahne grafiği tiyatrosu", "1", "docs — geniş", "Sahne", "Açık motor — kritik"),
            ("Bevy Book + ECS writings", "Bevy / ECS", "Bevy", "Varlık-bileşen model", "1", "docs", "Sahne", "Açık"),
            ("LearnOpenGL", "LearnOpenGL", "Joey de Vries", "Modern OpenGL omurgası", "1", "~500+", "Sahne", "Açık"),
            ("Vulkan Tutorial + Khronos specs (çekirdek)", "Vulkan Öğretici", "vulkan-tutorial / Khronos", "Modern GPU API", "1", "docs", "Sahne", "Açık"),
            ("The Book of Shaders", "Shader Kitabı", "Patricio Gonzalez Vivo", "Görsel gölgelendirici", "1", "kitap", "Sahne", "Açık"),
            ("Three.js docs + examples + manual", "Three.js", "Three.js", "WebGL sahne", "1", "docs", "Sahne", "Açık"),
            ("Babylon.js docs", "Babylon.js", "Microsoft / Babylon", "Web 3D alternatifi", "1", "docs", "Sahne", "Açık"),
            ("WebGPU / WGSL specs + MDN", "WebGPU", "W3C / MDN", "Gelecek web grafik", "1", "spec", "Sahne", "Açık"),
            ("Filament docs (Google)", "Filament", "Google", "Fiziksel tabanlı render", "1", "docs", "Sahne", "Açık"),
            ("glTF 2.0 spec + Sample Models", "glTF", "Khronos", "3D asset omurgası", "1", "spec", "Sahne", "Açık"),
            ("OpenUSD docs (Pixar / ASWF)", "OpenUSD", "Pixar / ASWF", "Büyük sahne kompozisyon", "1", "docs", "Sahne", "Açık"),
            ("Blender Manual", "Blender El Kitabı", "Blender Foundation", "3D içerik üretimi", "1", "docs — geniş", "Sahne", "Açık"),
            ("OpenTimelineIO + OpenColorIO", "OTIO / OCIO", "ASWF", "Yönetmen zamanı + renk", "2", "docs", "Sahne", "Açık"),
            ("FFmpeg Documentation + wiki", "FFmpeg", "FFmpeg", "Film/render kuyruğu", "1", "docs — geniş", "Sahne", "Açık"),
            ("Kdenlive / Shotcut / Olive docs (seçme)", "Açık Video Editörleri", "Kdenlive vd.", "Kesme masası", "1", "docs", "Sahne", "Açık"),
            ("PDF.js + mupdf docs", "PDF.js / MuPDF", "Mozilla / Artifex", "Kitabı sahnede yürütmek", "2", "docs", "Sahne", "Açık"),
            ("Excalidraw + tldraw docs", "Excalidraw / tldraw", "açık çizim", "Çizim masası", "2", "docs", "Sahne", "Açık"),
            ("Manim Community docs", "Manim", "Manim Community", "Canlı matematik tahtası", "1", "docs", "Sahne", "Açık"),
            ("Reveal.js / impress.js / Slidev", "Sunum Motorları", "Hakimel / Bartaz / Slidev", "Sunum masası", "1", "docs", "Sahne", "Açık"),
            ("D3 / Chart.js / Apache ECharts / Observable Plot", "Veri Görselleştirme Paketi", "D3/ECharts/Observable", "Tablo-grafik sahnesi", "1", "docs", "Sahne", "Açık"),
            ("HarfBuzz + FriBidi + PanDoc docs", "Yazı / RTL / Pandoc", "HarfBuzz/FriBidi/Pandoc", "Arapça-Türkçe doğru yazı + belge", "1", "docs", "Sahne", "Açık — kritik"),
            ("MapLibre + MBTiles + Natural Earth + OpenStreetMap data", "Çevrimdışı Harita Paketi", "MapLibre / NE / OSM", "Coğrafya turu", "1", "docs+veri", "Sahne", "Açık"),
            ("VRM spec + Three VRM + lipsync/viseme açık tarifler", "VRM Avatar + Dudak Senkronu", "VRM ekosistemi", "Rüzgar yüzü konuşsun", "1", "docs", "Sahne", "Açık — kritik"),
            ("Computer Vision: Algorithms and Applications (Szeliski)", "Bilgisayarlı Görü", "Richard Szeliski", "Göz / sahne görme", "1", "~800+", "Sahne", "Ücretsiz PDF"),
            ("OpenCV Tutorials + PyImageSearch açık seçme", "OpenCV", "OpenCV", "Görüntü işleme", "1", "docs", "Sahne", "Açık"),
            ("Web Audio API + Tone.js + Godot audio + OpenAL", "Uzamsal Ses Paketi", "W3C / Tone.js / Godot", "Sahne sesi", "1", "docs", "Sahne", "Açık"),
            ("Bullet / Rapier / Box2D / Matter.js docs", "Fizik Motorları", "Bullet/Rapier/Box2D", "Sahne fiziği", "1", "docs", "Sahne", "Açık"),
            ("Raylib / Sokol / Dear ImGui docs", "Hafif Sahne / UI Paketi", "Raylib/Sokol/ImGui", "Hızlı araç yüzü", "1", "docs", "Sahne", "Açık"),
            ("Yarn Spinner / Ink (inkle) / Twine docs", "Diyalog Motorları", "Yarn/Ink/Twine", "Anlatı sahnesi", "1", "docs", "Sahne", "Açık"),
            ("Lottie + SVG animation + Rive açık docs", "2D Hareket Grafik", "Lottie/SVG/Rive", "Hareketli illüstrasyon", "1", "docs", "Sahne", "Açık"),
            ("FreeCAD / OpenSCAD docs", "Parametrik 3D Tasarım", "FreeCAD/OpenSCAD", "Sahne prop üretimi", "2", "docs", "Sahne", "Açık"),
            ("Inkscape + GIMP + Krita docs (çekirdek)", "2D Üretim Üçlüsü", "Inkscape/GIMP/Krita", "Görsel atölye", "3", "docs", "Sahne", "Açık"),
            ("Assimp + Draco + meshoptimizer docs", "3D Asset Boru Hattı", "Assimp/Draco", "Model sıkıştırma/yükleme", "1", "docs", "Sahne", "Açık"),
            ("Obs-studio docs (yayın/sahne kompozit)", "OBS Studio", "OBS", "Canlı sahne kompoziti", "1", "docs", "Sahne", "Açık"),
        ],
    ),
    "26_YEREL_BEYIN_IR": (
        "26 YEREL BEYİN - ARAMA (sahne+kütüphane yakıtı)",
        [
            ("Introduction to Information Retrieval", "Bilgi Erişimine Giriş", "Manning; Raghavan; Schütze", "RAG/arama teorisi omurgası", "1", "~500+", "Sahne/A", "Ücretsiz — kritik"),
            ("Managing Gigabytes (Witten et al.) — ücretsiz?", "Gigabaytları Yönetmek", "Witten; Moffat; Bell", "İndeks sıkıştırma klasiği", "1", "~500+", "Sahne", "Ücretsizse"),
            ("Apache Lucene + Solr refs", "Lucene / Solr", "ASF", "İndeks motoru", "2", "docs", "Sahne", "Açık"),
            ("OpenSearch Documentation", "OpenSearch", "OpenSearch Project", "Arama kümesi", "1", "docs", "Sahne", "Açık"),
            ("Tantivy / Quickwit / Lindera docs", "Rust Arama Yığını", "Tantivy ekosistemi", "Yerel hızlı indeks", "1", "docs", "Sahne", "Açık"),
            ("Meilisearch + Typesense docs", "Meilisearch / Typesense", "Meili / Typesense", "Anlık arama UX", "2", "docs", "Sahne", "Açık"),
            ("faiss / hnswlib / usearch docs", "Vektör Arama Paketi", "Meta / hnswlib / usearch", "Embedding arama", "1", "docs", "Sahne", "Açık"),
            ("Qdrant / LanceDB / Chroma / Milvus docs (çekirdek yerel)", "Vektör DB Paketi", "Qdrant/Lance/Chroma", "Yerel vektör hafıza", "1", "docs", "Sahne", "Açık"),
            ("Ollama + llama.cpp + ggml docs", "Ollama / llama.cpp", "Ollama / ggml", "Yerel LLM runtime", "1", "docs", "Sahne", "Açık — kritik"),
            ("vLLM / llama.cpp server / Text Generation Inference docs", "Yerel Sunucu Yığını", "vLLM / HF", "Yerel çıkarım sunucusu", "1", "docs", "Sahne", "Açık"),
            ("PEFT / LoRA / QLoRA papers+docs", "LoRA / PEFT", "Hugging Face", "Yerel ince ayar", "1", "docs+makale", "Sahne", "Açık"),
            ("Hugging Face Transformers / Datasets / Tokenizers docs", "HF Çekirdek Kütüphaneler", "Hugging Face", "Model ekosistemi", "1", "docs", "Sahne", "Açık"),
            ("Whisper + Faster-Whisper + Vosk docs", "Yerel STT", "OpenAI / topluluk", "Kulak", "1", "docs", "Sahne", "Açık"),
            ("Piper / Kokoro / Coqui TTS / Mimic3 docs", "Yerel TTS", "Rhasspy / topluluk", "Nefes/ses", "1", "docs", "Sahne", "Açık"),
            ("Tesseract + ocrmypdf + Docling + Marker docs", "OCR / Belge Anlama", "UB Mannheim / Docling", "Foto→metin→indeks", "1", "docs", "Sahne", "Açık — kritik"),
            ("Unstructured / LlamaParse açık alternatifler docs", "Belge Ayrıştırma", "Unstructured / açık", "PDF/HTML temizleme", "1", "docs", "Sahne", "Açık"),
            ("Haystack / LlamaIndex / LangChain docs (yerel RAG tarifleri)", "RAG Çatıları", "deepset / LlamaIndex", "RAG boru hattı", "1", "docs", "Sahne", "Açık"),
            ("BEIR / MTEB / RAGAS evaluation docs", "IR / RAG Değerlendirme", "BEIR/MTEB/RAGAS", "Kalite ölçümü", "1", "docs", "Sahne", "Açık"),
            ("ColBERT / SPLADE papers + docs", "Geç Nişanlama / Seyrek-Yoğun", "ColBERT / SPLADE", "İleri retrieval", "1", "makale+kod", "Sahne", "Açık"),
            ("BM25 / TF-IDF klasik makaleler + Okapi açıklamaları", "BM25 / TF-IDF", "Robertson vd.", "Klasik sıralama", "1", "makale", "Sahne", "Açık"),
            ("Sentence-Transformers docs + embedding model kartları", "Sentence-Transformers", "UKPLab / HF", "Cümle gömme", "1", "docs", "Sahne", "Açık"),
            ("SQLite FTS5 + usearch + mini-RAG tarifleri (açık yazılar)", "FTS5 Yerel RAG Tarifleri", "SQLite / topluluk", "Hafif yerel arama", "1", "docs+yazı", "Sahne", "Açık"),
            ("DuckDB + VSS / semantic SQL açık yazılar", "DuckDB Anlamsal SQL", "DuckDB", "Analitik+vektör", "1", "docs", "Sahne", "Açık"),
            ("Offline Wiki / Kiwix / ZIM format docs", "Kiwix / ZIM", "Kiwix", "Çevrimdışı ansiklopedi", "1", "docs", "Sahne", "Açık"),
            ("Local LLM alignment / llama-guard açık / constitutional açık metinler", "Yerel Güvenli Üretim", "açık guard modelleri", "Güvenli yerel beyin", "1", "docs", "Sahne/C", "Açık"),
        ],
    ),
}


def _safe_sheet(title: str) -> str:
    # openpyxl: \ / * ? : [ ] yasak
    s = title
    for ch in r"\/:*?[]":
        s = s.replace(ch, "-")
    s = s.strip() or "KATEGORI"
    return s[:31]


def _safe_filename(title: str) -> str:
    s = title
    for ch in r'\/:*?"<>|':
        s = s.replace(ch, "-")
    return s.strip() or "KATEGORI"


def write_cat(folder: str, title: str, rows: list[tuple]) -> Path:
    out_dir = OUT_ROOT / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    # Eski zayıf xlsx kalmasın
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
        f"{title} — Rüzgar bilgisayar/sahne YÜKLEME PLANI (v2 GENİŞ) · "
        f"{len(rows)} eser · Şamile bitince indirilecek · kategori karıştırılmaz · "
        f"yalnız yasal/açık"
    )
    ws["A1"].font = Font(name="Calibri", size=13, bold=True, color="C00000")
    ws.merge_cells("A1:I1")
    hf = Font(name="Calibri", size=11, bold=True)
    fill = PatternFill("solid", fgColor="D9E1F2")
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
        vals = [i, orig, tr, yazar, katar, cilt, sayfa, dalga, not_]
        for col, v in enumerate(vals, 1):
            cell = ws.cell(2 + i, col, v)
            cell.border = thin
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    widths = [6, 44, 42, 30, 50, 12, 16, 10, 24]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + i)].width = w
    ws.freeze_panes = "A3"
    ws.auto_filter.ref = f"A2:I{2 + len(rows)}"
    note = wb.create_sheet("NOT")
    note["A1"] = (
        "v2 GENİŞ liste — Şamile envanterinden AYRI klasör. "
        "Şamile RAG bitince indirilip yüklenecek yasal/açık eserlerdir. "
        "SAYFA tahmini veya docs gövdesidir. "
        "Telifli ticari (DDIA, Clean Code, CSAPP, AIMA baskı vb.) YOK; açık muadilleri var. "
        "NOT sütununda 'ücretsizse / açık sürüm' yazanlar indirmeden önce lisans kontrolü ister. "
        "Dalga: A omurga · B zihin · C üretim · D donanım · E destek · Sahne. "
        "Kategorileri karıştırmayın; her klasör ayrı Excel."
    )
    note["A1"].alignment = Alignment(wrap_text=True)
    note.column_dimensions["A"].width = 100
    wb.save(path)
    return path


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    # kökteki eski özet
    for old in OUT_ROOT.glob("00_*.xlsx"):
        try:
            old.unlink()
        except OSError:
            pass
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
    ws.append(["TOPLAM ESER SATIRI", total])
    ws.append(["SURUM", "v2 GENIS — guclu acik eser genisletmesi"])
    ws.append(["KOK", str(OUT_ROOT)])
    ozet = OUT_ROOT / "00_OZET_YUKLEME_PLANI.xlsx"
    wb.save(ozet)
    by = {r["cat"]: r["rows"] for r in results}
    print(
        json.dumps(
            {"ok": True, "cats": len(results), "works": total, "by_cat": by, "root": str(OUT_ROOT), "ozet": str(ozet)},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
