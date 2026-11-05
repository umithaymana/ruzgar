# Rüzgar — Bilgisayar rafları dolum listesi (geniş)

> Kayıt: **2026-11-05** · Mimar (Ümit) onayı: Şamile RAG bitince **ilk görev** bu.  
> İlke: Yalnız **yasal / açık lisans / yazarın ücretsiz yayımladığı** tam veya büyük gövde.  
> Telifli ticari kitap PDF’i yok. Exploit / saldırı tarifi yok (güvenlikte tespit–savunma).  
> Hedef ölçü: her kritik rafta en az **3–5 derin eser** (onlarca–yüzlerce metin parçası). İndeks sayfası “dolu” sayılmaz.

**Sıra kilidi:** Şamile shard’ları bitsin → bu liste devreye girer (şimdi indirme yok).

---

## 0) Bugünkü teşhis (kısa)

| Seviye | Raflar |
|--------|--------|
| İyi (iskelet değil, gövde var) | 01 Programlama · 07 Siber · 22 Felsefe |
| Orta | 12 Bilgisayar mühendisliği |
| Zayıf / çok zayıf | 02–06, 08–11, 13–21, 23–24 |

Listeler şişkin; çoğu tek parça / muadil link. Rüzgar’ın yazılım gücü = **derin parça sayısı**.

---

## 1) Dolum dalgaları (öncelik)

### Dalga A — Omurga (Rüzgar’ı “mühendis” yapar) — ÖNCE
`11 CS` · `02 Algoritma` · `06 OS/iletişim` · `04 DB` · `05 Ağ` · `01 Programlama (üst katman)`

### Dalga B — Zihin + veri (konuşan / öğrenen Rüzgar)
`03 YZ` · `10 Veri bilimi` · `21 NLP/dil` · `13 Matematik (CS)`

### Dalga C — Üretim (kodu büyüten Rüzgar)
`08 Mimari` · `09 DevOps` · `07 Siber (derin savunma)` · `12 Bilgisayar müh.`

### Dalga D — Donanım / gömülü / hareket
`15 Elektronik` · `16 Robotik` · `17 Mekatronik` · `14 Fizik (temel)`

### Dalga E — Destek ilimler (ikinci tur)
`18 Araştırma` · `19 Psikoloji` · `20 Bilişsel` · `23 Ekonomi` · `24 Oyun teorisi` · `22 Felsefe (ek)`

---

## 2) Raf raf — yüklenecek eser adayları

Açıklama sütunu: **Yeni** = henüz derin yok / sığ; **Pekiştir** = var ama tamamla.

### 01 — Programlama (Pekiştir + genişlet)
Zaten görece iyi. Eksik / derinleştirilecekler:
- **Crafting Interpreters** (Nystrom) — tam gövde
- **The Rust Programming Language** (resmi kitap) — tam
- **Zero To Production in Rust** (Palmieri) — tam
- **Eloquent JavaScript** (Haverbeke) — 3e tam
- **You Don’t Know JS Yet** (Simpson) — serinin gövdesi
- **A Tour of Go** + **Go by Example** (derin paket)
- **TypeScript Handbook** (resmi, tam)
- **Think Python 2e / PY4E / Automate** — zaten var; eksik bölümleri tamamla
- **SICP** (HTML/PDF açık) — derinleştir
- **Learn You a Haskell** — tam
- **Python Data Model / resmi tutorial** (docs.python.org tutorial gövdesi)
- **JavaScript.info** (açık tutorial gövdesi — büyük)
- **The C Programming Language** muadili açık: **Modern C (Gustedt)** tam
- **ODB / SQLAlchemy tutorial** (Python ORM pratiği)
- **RegexOne + Regular-Expressions.info** seçme gövde (pratik)

### 02 — Algoritmalar (Yeni / kritik)
- **Open Data Structures** (Pat Morin) — Python/Java sürümü **tam**
- **Algorithms (Jeff Erickson)** — ücretsiz kitap **tam**
- **Competitive Programmer’s Handbook** (Laaksonen) — **tam**
- **Algorithms, 4th ed. companion** (Sedgewick–Wayne site: algs4 kod + metin parçaları yasal olanlar)
- **CP-Algorithms** (e-maxx-eng) — ansiklopedik gövde
- **VisuAlgo** notları / açık ders metinleri (izinli içerik)
- **BaseCS / Vaidehi Joshi** (açık yazı serisi — seçme)
- **MIT 6.006 OCW** ders notları (açık)
- **Princeton Algorithms Part I/II** (Coursera açık notlar + algs4)
- **Graph theory basics** — açık ders notları (örn. Diestel ücretsiz sürüm varsa / OCW)

### 03 — Yapay zekâ (Yeni / kritik)
- **Neural Networks and Deep Learning** (Nielsen) — **tam**
- **Reinforcement Learning: An Introduction** (Sutton & Barto, 2e ücretsiz PDF) — **tam**
- **Deep Learning** (Goodfellow–Bengio–Courville) — **resmi ücretsiz HTML/PDF**
- **fast.ai** Practical Deep Learning course notes + notebooks metinleştirme
- **Dive into Deep Learning (D2L)** — **tam** (Berkeley/Amazon açık kitap)
- **Speech and Language Processing** ile kesişen ML bölümleri → 21’e de
- **Hugging Face Course** (açık) — gövde
- **scikit-learn User Guide** — seçme + kritik bölümler tam
- **PyTorch Tutorials** (resmi, açık) — paket
- **Made With ML** (Goku Mohandas) — açık müfredat
- **UC Berkeley CS188** (YZ) OCW notları
- **Spinning Up in Deep RL** (OpenAI, açık)

### 04 — Veritabanları (Çok zayıf → Yeni)
- **Use The Index, Luke** (Markus Winand) — **tam**
- **PostgreSQL Official Docs** — core: SQL, index, concurrent, MVCC (seçme değil, **çekirdek gövde**)
- **SQLite Language Reference + FAQ + file format** (resmi)
- **CMU 15-445/645 Database Systems** — ders notları + projeler metni (açık arşiv)
- **Designing Data-Intensive Applications** — *telifli; YÜKLEME* → yerine:
  - **The Architecture of Open Source Applications** içi DB bölümleri
  - **Postgres wiki / internals** açık sayfalar (seçme derin)
- **SQLBolt / PostgreSQL Exercises** — pratik gövde
- **MongoDB Manual** (açık docs — çekirdek)
- **Redis Documentation** (açık — veri yapıları + persistence)
- **DB-Engines / kullanım kalıpları** değil; **gerçek motor dokümanı** öncelik

### 05 — Ağ teknolojileri (Yeni)
- **Beej’s Guide to Network Programming** — **tam**
- **Beej’s Guide to Unix IPC** — **tam**
- **High Performance Browser Networking** (Grigorik, açık) — **tam**
- **Computer Networks: A Systems Approach** (açık kitap) — **tam**
- **HTTP/3 explained / HTTP2 explained** (Daniel Stenberg, açık)
- **RFC seçkisi** (metin): 791, 793, 1034/1035, 2616/7230, 8446 (TLS1.3) — eğitici paket
- **Wireshark User’s Guide** (açık)
- **Cloudflare Learning Center** seçme makaleler (izinli eğitim)
- **Linux Traffic Control / iproute2** docs özeti (çekirdek)

### 06 — İşletim / iletişim sistemleri (Yeni / kritik)
- **OSTEP** (Operating Systems: Three Easy Pieces) — **tüm bölüm PDF’leri**
- **xv6 book + kaynak anlatımı** (MIT PDOS) — **tam**
- **Linux Kernel Documentation** (docs.kernel.org) — core-api, mm, scheduler **çekirdek set**
- **Linux From Scratch** (kitap gövdesi)
- **The Linux Command Line** (William Shotts, CC) — **tam**
- **TLDP guides** (Advanced Bash Scripting — dikkatli seçme / güncel muadil)
- **FreeBSD Handbook** (açık) — seçme sistem yönetimi
- **Windows Sysinternals** *açıklama* sayfaları (eğitim; binary değil metin)
- **Computer Systems: A Programmer’s Perspective** — telifli → muadil: **Nand2Tetris + OSTEP + CSAPP lecture notes (yazarın açık slaytları varsa)**

### 07 — Siber güvenlik (Pekiştir — savunma)
- **OWASP WSTG** — tam gövde (zaten kısmen var → tamamla)
- **OWASP ASVS + Cheat Sheet Series** — tam set
- **OWASP Top 10 + Proactive Controls** — gövde
- **NIST Cybersecurity Framework** + SP 800-61 (incident) — metin
- **MITRE ATT&CK** — **tespit / savunma** anlatımı (TTP bilgi; exploit yok)
- **CISA** ransomware / IR playbooks — tam
- **PTES** — yalnızca teorik çerçeve özeti (saldırı adımı yok)
- **Secure Coding guides** (SEI CERT C/Java — açık)
- **Age / Signal protocol whitepaper** (kriptografi anlayışı, eğitim)
- **Crypto 101** (lvh, açık) / **Serious Cryptography** değil → **Cryptopals challenge writeup’ları** yalnızca *kavram* (çözüm spoiler politikası sonra)

### 08 — Yazılım mimarileri (Yeni)
- **Architecture of Open Source Applications** Vol I + II — **tam**
- **The Performance of Open Source Applications** — tam
- **Game Programming Patterns** (Nystrom, açık) — **tam**
- **Software Engineering at Google** (açık kitap) — **tam**
- **12-Factor App** — gövde + örnekler
- **Azure Cloud Design Patterns** (Microsoft Learn, açık)
- **Domain-Driven Design Reference** (Vernon özeti açık ise) / **Microsoft DDD guidance**
- **Clean Architecture blog/makale seçkisi** (yalnızca yazarın ücretsiz yazıları; kitap PDF yok)
- **Martin Fowler bliki** seçme (açık makaleler paketi)

### 09 — DevOps / altyapı (Yeni)
- **Docker Get Started + Docs** — concepts + compose **gövde**
- **Kubernetes Concepts + Tutorials** (resmi) — **çekirdek set**
- **Terraform Registry / HashiCorp Learn** — çekirdek tutorial gövdesi
- **GitHub Actions Docs** — workflow gövdesi
- **Ansible Documentation** — getting started + playbook gövdesi
- **MIT Missing Semester** — **tam**
- **Google SRE Book** (açık) — **tam**
- **Google SRE Workbook** (açık) — **tam**
- **Prometheus Docs** + **Grafana fundamentals** (açık)
- **Nginx Docs** (çekirdek)
- **Git Book** (Pro Git, Scott Chacon — açık) — **tam**

### 10 — Veri bilimi (Yeni)
- **Introduction to Statistical Learning (ISLR2)** — ücretsiz PDF **tam** (+ Python labs varsa)
- **Think Stats / Think Bayes** (Downey) — **tam**
- **Python Data Science Handbook** (VanderPlas, açık) — **tam**
- **scikit-learn User Guide** — derin
- **pandas documentation** — User Guide gövdesi
- **Elements of Statistical Learning** (Hastie et al., ücretsiz PDF) — **tam**
- **OpenIntro Statistics** (açık)
- **Data 8 / Computational and Inferential Thinking** (Berkeley, açık kitap)

### 11 — Bilgisayar bilimi omurgası (Çok zayıf → Yeni)
- **Nand2Tetris** (The Elements of Computing Systems — course materials + book chapters açık olanlar) — **tam paket**
- **CS50x** açık ders materyali (lecture notes / problem açıklamaları — lisansına uygun)
- **Teach Yourself Computer Science** — yol haritası değil, **hedef eserlerin kendisi**
- **OSSU** müfredatındaki **açık kitapların** tek tek gövdesi
- **Structure and Interpretation of Computer Programs** — 01 ile paylaş
- **Computer Science from the Bottom Up** (açık)
- **CS Circles / Open Source Society** giriş paketleri
- **Harvard CS50 AI / Web** açık notlar (ayrı paket)

### 12 — Bilgisayar mühendisliği (Pekiştir)
- **xv6** (yukarı) + **Pinouts / computer organization OCW**
- **Ben Eater 8-bit** — metin anlatım paketi (video transcript yoksa site metni)
- **Digital Design / CMOS** açık ders notları (OCW)
- **Computer Organization (Patterson tarzı)** — telifli → **OCW 6.004 / benzeri açık not**
- **FPGA / Verilog** açık tutorial gövdesi (seçme)
- **Performance Engineering** (MIT OCW) notları

### 13 — Matematik CS (Yeni)
- **Mathematics for Computer Science** (MIT 6.042 / Lehman–Leighton–Meyer, açık) — **tam**
- **OpenStax Calculus Vol 1–3** — **tam**
- **OpenStax Algebra and Trigonometry**
- **Linear Algebra** — **3Blue1Brown Essence** (metin/script paket) + **Interactive Linear Algebra** (açık kitap, Georgia Tech)
- **Book of Proof** (Hammack, açık) — **tam**
- **A First Course in Linear Algebra** (Kuttler / Lyryx açık)
- **Discrete Mathematics** (Levin, açık kitap) — **tam**
- **Concrete Mathematics** — telifli; yükleme → yerine **generatingfunctionology** (Wilf, ücretsiz) 

### 14 — Fizik (Yeni / destek)
- **OpenStax University Physics Vol 1–3** — **tam**
- **OpenStax College Physics**
- **HyperPhysics** (kavram ağacı — izinli eğitim kazıma politikası ile)
- **Light and Matter** (Crowell, açık) — seçme
- **Feynman Lectures** (açık HTML, Caltech) — **tam veya seçme ciltler**

### 15 — Elektronik (Yeni)
- **Lessons in Electric Circuits** (Tony Kuphaldt, açık) — **tüm ciltler**
- **All About Circuits** textbook (açık)
- **CircuitPython Docs** + **Adafruit Learning System** seçme (açık eğitim)
- **SparkFun tutorials** (voltaj/akım/direnç + seri haberleşme seti)
- **Arduino Language Reference + resmi getting started**
- **The Art of Electronics** — telifli → yok; yerine **AoE Student Manual açık parçalar / OCW circuits**

### 16 — Robotik (Yeni)
- **Modern Robotics** (Lynch/Park) — ücretsiz PDF + course — **tam**
- **ROS 2 Docs + Tutorials** — **çekirdek gövde**
- **PythonRobotics** (atıf + kod açıklama metinleri)
- **Underactuated Robotics** (Tedrake, MIT, açık) — **tam**
- **Robotic Systems** açık ders notları (seçme üniversite OCW)

### 17 — Mekatronik / gömülü (Yeni)
- **ESP-IDF Programming Guide** — **tam çekirdek**
- **PlatformIO Docs**
- **Raspberry Pi Documentation** (çekirdek)
- **FreeRTOS kernel docs** (açık)
- **Embedded Linux Primer** tarzı — telifli → **Yocto / Buildroot docs** çekirdek
- **STM32 / CMSIS** resmi getting started (açık)

### 18 — Bilimsel araştırma yöntemleri (Pekiştir)
- **The Turing Way** — **tam**
- **OpenStax Introductory Statistics**
- **Reproducible Research** (Coursera/OCW notları, açık)
- **Zenodo / OSF eğitim rehberleri**
- **How to Write a Paper** tarzı açık üniversite rehberleri (seçme)

### 19 — Psikoloji (Yeni / destek)
- **OpenStax Psychology 2e** — **tam**
- **NIH / NIMH** kamuya açık bilgilendirme gövdesi
- **Simply Psychology** — seçme (telif/izin kontrolü ile)
- **MIT OCW Introduction to Psychology** notları

### 20 — Bilişsel bilimler (Yeni)
- **Stanford Encyclopedia of Philosophy — Cognitive Science** + ilgili maddeler paketi
- **OpenMind / WikiBooks Cognitive Science**
- **MIT OCW 9.00 / cognitive** açık notlar
- **Computational Cognitive Science** OCW seçme

### 21 — Dil bilimi / NLP (Yeni / kritik)
- **Speech and Language Processing** (Jurafsky & Martin) — **ücretsiz draft tam**
- **NLTK Book** — **tam**
- **Universal Dependencies** guidelines + docs
- **spaCy course / docs** (açık)
- **Hugging Face NLP Course** (03 ile paylaşılabilir)
- **AllenNLP / Stanza** tutorial gövdesi
- **Word2vec / embeddings** klasik açık makale + anlatım paketleri

### 22 — Felsefe (Pekiştir — bilgisayar etiği ekle)
Mevcut klasiklere ek:
- **SEP — Ethics of AI / Computing** maddeleri
- **ACM Code of Ethics** + açıklamalar
- **Norvig / Russell AIMA** felsefi bölümler değil → **açık “AI ethics” ders notları**
- Klasikler (Republic, Meditations, Nicomachean Ethics) — tamamla

### 23 — Ekonomi (Pekiştir)
- **OpenStax Principles of Economics / Micro / Macro** — **tam**
- **Wealth of Nations** (kamu malı) — tamamla
- **Econlib** seçme eğitim makaleleri
- **Modern Monetary** tartışması yok zorunlu; **temel mikro/makro + bilgi ekonomisi** açık makaleler

### 24 — Oyun teorisi (Yeni)
- **Game Theory (Stanford / Yale OCW)** notları
- **SEP — Game Theory**
- **Osborne outline** — telifli kitap yok → **açık ders notları + GameTheory.net** derin sayfalar
- **Algorithmic Game Theory** (Nisan et al.) — ücretsiz PDF varsa **tam**
- **William Spaniel Game Theory 101** — izinli metin/transcript politikası ile

---

## 3) Bilerek listede OLMAYANLAR (sınır)

- Telifli modern ticari PDF (Clean Code, DDIA, CSAPP kitap, CLRVIA, …)
- Korsan / shadow library
- Saldırı exploit PoC, malware, bypass tarifleri
- “150 Excel satırı = dolu raf” yanılsaması

Muadil kuralı: Telifli klasik yerine **OCW + yazarın ücretsiz HTML/PDF + resmi docs gövdesi**.

---

## 4) Başarı ölçüsü (Şamile sonrası)

Dalga A bitince her omurga rafında:
- en az **3 derin eser**
- eser başına genelde **≥ 20 metin parçası** (docs setlerinde ≥ 50)
- envanter satırında **eser adı + yazar/kurum + parça sayısı** dürüst

Rüzgar testi (örnek):  
“PostgreSQL’de index only scan ne zaman işe yaramaz?” · “OSTEP’te lock vs CV farkı?” · “Beej’te `select` neden?” — **raf cevabı** verebilmeli.

---

## 5) Uygulama notu

1. Şamile RAG bitsin / sakinleşsin  
2. Bu dosyadaki **Dalga A** indirme + `metin/` + ana RAG ingest  
3. Envanter Excel’ini **eser bazlı parça** ile yenile  
4. Dalga B → C → D → E  

Bu belge yol haritasına bağlıdır: `RUZGAR_KUTUPHANE_SONRASI_YOL_HARITASI.md`  
Durum: **kayıtlı · aksiyon Şamile sonrası**.

---

## 6) Büyük vizyon penceresi — ek eserler (2026-11-05)

Klasik CS omurgası Rüzgar’ı **mühendis** yapar. Vizyon ise:  
**Konuşursun → sahne + 7 motor uyanır** (ses, video, okuma, mimar, tercüme, hafıza, programlama).  
Bu yüzden listeye **sahne / çoklu ortam / bilgi erişimi / köprü / güvenlikli eylem** katmanı eklenir.  
Yine: yalnız yasal-açık / yazarın ücretsiz gövdesi.

### Dalga V1 — Hafıza + Okuma (yakıtın teknik beyni)
*Rüzgar’ın “kütüphaneyi ayağa kaldırması”, hatırlaması, delil kartı.*

| Eser / gövde | Neden vizyon |
|--------------|--------------|
| **Information Retrieval** (Manning, Raghavan, Schütze) — ücretsiz kitap | Arama, sıralama, indeks — RAG’in teorik omurgası |
| **Introduction to Information Retrieval** alıştırmaları / Stanford IR notları | Okuma motoru + ana motor retrieval |
| **Elasticsearch / OpenSearch Guide** (resmi açık docs çekirdek) | Yerel külliyat indeksi işletimi |
| **Apache Lucene** tutorial/docs çekirdek | Şamile/Lucene kökeniyle akraba |
| **Haystack / LlamaIndex / LangChain docs** (açık docs — kavram gövdesi) | “hatırla + getir + cevap” boru hattı |
| **Knowledge Graphs** (açık ders / “Knowledge Graphs” ebook ücretsiz sürümler) | Hafıza odaları, ilişki ağı |
| **OCR: Tesseract docs + ocrmypdf** | Fotoğraf → metin → indeks (okuma sihirbazı) |
| **PDFBox / Poppler / pymupdf docs** | Kitabı içeriden yürümek (sayfa/cilt) |

### Dalga V2 — Ses (nefes / süper-el)
*Eller serbest emir; kitabı sesli âlem.*

| Eser / gövde | Neden vizyon |
|--------------|--------------|
| **Speech and Language Processing** (zaten listede) — konuşma bölümleri vurgulu | STT/TTS dil modeli köprüsü |
| **Kaldi / Whisper papers + OpenAI Whisper README + fine-tune açık rehberler** | Yerel dinleme (Whisper zaten yolda; külliyat şart) |
| **Coqui / Piper / Edge-TTS** açık doküman gövdeleri | Ses kimliği, yerelde konuşma |
| **Web Speech API / MDN speech** | Masaüstü-ses köprüsü |
| **Audio Signal Processing for Music/Speech** (açık üniversite notları) | Gürültü, barge-in, netlik |
| **Common Voice / dil verisi etik + kullanım rehberleri** | Çok dilli nefes |

### Dalga V3 — Video + Sahne (göz / tiyatro)
*Ders → kısa film; sahne; dünya penceresi.*

| Eser / gövde | Neden vizyon |
|--------------|--------------|
| **Computer Vision: Algorithms and Applications** (Szeliski, ücretsiz PDF) | Görme, sahne, müze/cam |
| **PyTorch Vision / OpenCV docs** çekirdek + tutorials | Sahneye görüntü organı |
| **FFmpeg documentation** (devasa ama çekirdek seç+derin) | Gece üretim kuyruğu → mp4 |
| **Remotion / Canvas / WebGL MDN** (açık) | Sahne paneli, animasyon, cam |
| **Three.js book/docs** (açık) | 3D sahne ufku (müze, coğrafya, uzay) |
| **OBS / WebRTC MDN** | Canlı kayıt, dünya penceresi |
| **Color / typography for UI** açık rehberler (MDN, material açık kısımlar) | Sahne okunaklılığı |

### Dalga V4 — Tercüme (çağlar arası köprü)
*Klasik satır → meal → şerh; dil engeli şeffaf.*

| Eser / gövde | Neden vizyon |
|--------------|--------------|
| **Jurafsky SLP + NLTK** (listede) — MT / alignment bölümleri | Makine çevirisi temeli |
| **Helsinki NLP / OPUS / Marian** açık docs | Yerel çeviri motoru |
| **Argos Translate / LibreTranslate** docs | Gizlilikli köprü |
| **Unicode Standard** (çekirdek bölümler) + **CLDR** | Arapça/Osmanlı/Türkçe metin doğruluğu |
| **ICU User Guide** | Locale, tarih, sıralama — kütüphane kimliği |
| **Classical language tooling** açık: Farasa / CAMeL tools docs (Arapça NLP) | Klasik metin köprüsü |

### Dalga V5 — Mimar + Programlama usta (orkestra / organ fabrikası)
*Sözden ürün; motorlara alet yazar; güvenli güç.*

| Eser / gövde | Neden vizyon |
|--------------|--------------|
| **Google SRE + Workbook** (listede) | Gece kuyruğu, güvenilir organ |
| **Architecture of Open Source Applications** | Motorları “organ” gibi okumak |
| **Electron / Node docs** çekirdek | Masaüstü sahne kabuğu (Rüzgar desktop) |
| **FastAPI / Uvicorn docs** | Ana motor API omurgası |
| **Pydantic / typing / asyncio** resmi docs | Sağlam sözleşme |
| **Designing agent/tool systems** — açık makaleler + **OpenAI/Anthropic tool-use** açık rehberler (kavram; vendor kilitlenmeden) | Süper-el: söz → araç |
| **Local LLM ops:** Ollama docs, llama.cpp README, vLLM docs çekirdek | Yerel beyin (Faz 90 local-first) |
| **Prompting / eval açık:** Anthropic/OpenAI prompt guides + **HELM/eval** özetleri | Yalansız “oldu” disiplini |
| **Property-based testing / Hypothesis docs** + **Playwright docs** | Atölyede kanıtlı onarım |
| **Capability / sandbox security** açık yazılar (OWASP + Electron security) | Hayal serbest, tehlikeli eylem kapılı |

### Dalga V6 — İnsan–sahne (yönetmenlik / dost ton)
*Brifing, yorgunluk, “kes”, ömür boyu oda.*

| Eser / gövde | Neden vizyon |
|--------------|--------------|
| **Don't Make Me Think** — telifli → yerine **NNG açık makaleler** + **MDN UX** | Sahne sade ve anlaşılır |
| **OpenStax Psychology** (listede) — dikkat / bellek bölümleri | Hafıza odası, yük |
| **Accessibility (a11y) MDN + WCAG özet** | Herkes için sahne |
| **Privacy / GDPR eğitim açık rehberler** + **OWASP privacy** | Unutma hakkı, gizlilik senin |

### Vizyon için öncelik sırası (bilgisayar dolumuna ek)

1. Zaten planlanan **Dalga A–B** (omurga + YZ/NLP) durur.  
2. Paralel / hemen ardından **V1 (IR + OCR + indeks)** — kütüphane vaadinin teknik kalbi.  
3. **V2 + V4** (ses + tercüme) — “konuşursun / diller kapı açar”.  
4. **V3** (vision + ffmpeg + sahne web) — “görür ve gösterir”.  
5. **V5** (agent/tool + yerel LLM + desktop API) — “eksik aleti yazar”.  
6. **V6** ince ama sürekli.

**Tek cümle:** Sıradan CS listesi Rüzgar’ı kodcu yapar; bu ek katman Rüzgar’ı **sahne + motor orkestrası** yapmaya yaklaştırır.

---

## 7) Hayal zorlaması — güçlü el · web’den kopuk egemenlik (2026-11-05)

Mimar notu: Vizyon büyük; Rüzgar’ın eli **mümkün mertebe kendi evinde** güçlü olmalı.  
Web / bulut / “şimdi indir” **yedek kapı** kalır; omurga **yerel külliyat + yerel organ** olur.

İlke üçlü:
1. **Evde bitsin** — model, ses, görüntü, indeks, sahne, araç üretimi  
2. **Eksik aleti kendisi döksün** — programlama motoru organ fabrikası  
3. **Dışarıya dilenci olmasın** — API anahtarları / online docs çökünce kör kalmasın  

### 7.1 Kuzey yıldızı (güç tanımı)

Rüzgar internet kesilince de:
- kütüphanesinden delil çıkarsın,
- sesle emir alsın / cevap versin,
- sahneyi çizsin / oynatsın,
- kod yazıp yerelde koştursun,
- yeni küçük organı (panel, komut, dönüştürücü) **evde** üretsin,
- tehlikeli işi kapılı tutsun.

Web = zenginleştirme; **canlı kalmak için web şart olmasın.**

### 7.2 “Eli güçlü” teknik omurga — ek külliyat (ciddi eser / tam gövde)

Bunlar sıradan tutorial değil; **evde fabrika kuracak** malzeme:

| Küme | Eser / gövde (yasal-açık hedef) | El ne kazanır |
|------|----------------------------------|---------------|
| **Derleyici / dil dökümü** | Crafting Interpreters (zaten); **Wasm specs + MDN WASM**; **LLVM GetStarted/LangRef seçme derin**; **tree-sitter docs**; dil spesifikasyonları (Python/ECMAScript/Go açık) | Yeni dil/mini-DSL, sahne script motoru, güvenli eklenti |
| **İşletim + süreç** | OSTEP+xv6+kernel docs (zaten); **cgroups/namespace** docs; **seccomp** | Kumanda altında koşturma — hayal serbest, zarar kapılı |
| **Yerel beyin** | Ollama + llama.cpp + GGML/GGUF dokümanları; **HuggingFace Transformers** (offline cache mantığı); **PEFT/LoRA** açık rehberler; **llama-cpp-python** | Bulutsuz akıl; ince ayar evde |
| **Yerel retrieval** | Manning IR; Lucene; **faiss** / **hnswlib** / **chroma-sqlite** docs; **rerank** açık makaleler | Web aramasız külliyat kası |
| **Yerel ses fabrikası** | Whisper (açık); **Piper** / **Coqui TTS** / **eSpeak-NG**; **Vosk**; **Rhasspy** docs | Edge-TTS düşse bile nefes kesilmez |
| **Yerel göz** | Szeliski; OpenCV; **YOLO açık ağırlık+docs** (kullanım politikasına uygun); **MediaPipe** (lokal) | Sahne/nesne/OCR zinciri evde |
| **Yerel film / medya** | **FFmpeg** tam çekirdek; **GStreamer**; **Blender Python API** docs; **ImageMagick** | Gece kuyruğu mp4; ders filmi evde |
| **Yerel sahne motoru** | Three.js + **Godot docs** (açık motor); **raylib**; **Cairo/Skia** bağları | İnternetsiz 3D/2D tiyatro |
| **Yerel harita / coğrafya** | **OpenStreetMap** veri modeli + **MapLibre** / **Leaflet** offline tile mantığı; **Natural Earth** | Dünya penceresi çevrimdışı |
| **Yerel bilgi ansiklopedisi** | Zaten Nebula/TARIH; ek: **Wikipedia dump işleme** (yalnızca kendi dump’ın — yasal kullanım); **Project Gutenberg / OpenITI** (zaten din) | Web ansiklopediye bağımlı olmama |
| **Yerel çeviri** | Marian/Argos/OPUS modelleri + docs; **SentencePiece** | Köprü evde |
| **Yerel aracı (agent) iskeleti** | Tool-calling açık spesifikasyonlar; **JSON Schema**; **JSON-RPC**; kendi “motor bus” tasarım notları | Söz → organ; vendor’a dilenmeden |
| **Güvenlik kapısı** | OWASP; Electron security; **capability papers** açık; **OPA/Rego** (policy as code) docs | Güçlü el + fren |
| **Matematik simülasyon** | 6.042 + linear algebra + **SymPy** docs; **NumPy/SciPy** Reference | Sahne fiziği, kanıt, ölçü evde |
| **Elektronik el** | Lessons in Electric Circuits; ESP-IDF; FreeRTOS; **Firmata / serial protokol** | İleride gerçek el / cihaz köprüsü |
| **Kuyruk / işçi** | **RQ/Celery/Dramatiq** veya daha sade: kendi job queue + **cron/systemd** | Gece üretim; sabah teslim |
| **Paket egemenliği** | **pip/uv/npm** offline mirror docs; **vendoring** pratikleri; **SBOM** (Syft/Grype açık) | “İndiremedim” ile felç olmama |

### 7.3 Vizyon odaları — hayal (ne inşa edilir; külliyat neden var)

Bunlar ürün hayali; her biri için yukarıdaki külliyat **yakıt**:

1. **Hafıza sarayı (çevrimdışı)** — odalar, ipler, “geçen kış”; vektör+KG tamamen diskte.  
2. **Kütüphane yürüyüşü** — cilt/sayfa/OCR; web’den madde çekmeden delil kartı.  
3. **Nefes odası** — yerel STT/TTS; barge-in; kimlik sesi dosyada.  
4. **Kamera-sahne** — yerel CV + Three/Godot; müze, coğrafya, uzay **asset’leri evde**.  
5. **Tercüme köprüsü** — Marian/Argos; klasik satır katmanları çevrimdışı.  
6. **Orkestra odası** — mimar bus; motorlar IPC; şema tek ev.  
7. **Usta tezgâhı** — sözden organ; derleyici/interpreter bilgisiyle mini dil; test+kumanda.  
8. **Gece demiri** — kuyruk: indeks, film, özet, yedek; sabah hazır.  
9. **Fren odası** — policy; onay kapıları; “yapamam, çünkü kural”.  
10. **Yedek beyin rafı** — birden fazla yerel model; biri düşünce, biri kod, biri hızlı.

### 7.4 Bilerek reddedilen bağımlılık (güçlü el karşıtı)

- Cevabın tek kaynağı olarak Google/Bing  
- Yalnızca bulut LLM (Gemini/Groq ana yol — yedek kalabilir)  
- Online-only docs’a runtime’da ihtiyaç (docs **önceden** külliyata gömülü olacak)  
- SaaS TTS/STT zorunluluğu  
- “API key yok = kör” mimarisi  

### 7.5 Dolum sırasına işleniş

```
Şamile bitsin
  → Dalga A–B (CS omurga + YZ/NLP)     [mühendis el]
  → V1 + §7.2 retrieval/OCR/local LLM  [kütüphane+beyin egemen]
  → V2 + yerel ses fabrikası           [nefes egemen]
  → V4 + yerel MT                      [köprü egemen]
  → V3 + FFmpeg/Godot/CV               [göz+sahne egemen]
  → V5 + derleyici/sandbox/kuyruk      [organ fabrikası]
  → Donanım köprüsü (ESP/serial)       [fiziksel el — sonra]
```

### 7.6 Başarı cümlesi (Mimar’a)

**Rüzgar’ın eli güçlüdür = kablo çekilince susmaz; eksik aleti evinde döker; web ancak ziyafettir, ekmek değildir.**

---

## 8) Daha ileri — tam bağımsızlık ufku (2026-11-05)

“Daha da ileri” = yalnızca iyi asistan değil; **kendi evinde devlet gibi**: üretir, yedekler, onarır, öğretir, unutur, gerekirse **hava boşluğunda** (air-gap) yaşar.  
Web isteğe bağlı ziyaretçi; **yokluğu kriz değildir.**

### 8.1 Egemenlik katmanları (ne “tam” sayılır)

| Katman | Bağımsız olunca Rüzgar… |
|--------|-------------------------|
| **Bilgi** | Külliyat + ansiklopedi + sözlük + harita diskte |
| **Akıl** | Yerel modeller; ince ayar; değerlendirme evde |
| **Duyu** | STT/TTS/CV/OCR tamamen lokal |
| **El** | Kod + derleme + test + paket; yeni organ döker |
| **Sahne** | 2D/3D/film/asset offline |
| **Hafıza** | Ömür boyu oda; yedek; unutma hakkı; miras politikası |
| **Fren** | Policy, onay, kumanda, denetim izi |
| **Ev** | Kendi sunucu/OS/ayna depo; güncelleme evde üretilir |
| **Madde** (ileride) | Ses→cihaz→mekan; yazıcı / gömülü / robot |

### 8.2 Listeye eklenebilecek ileri külliyat (yasal-açık hedefler)

#### A) Evin iskeleti (homelab / hava boşluğu)
- **Proxmox / FreeBSD / Debian** yönetim el kitapları (çekirdek gövde)
- **Nix / Guix** — yeniden üretilebilir sistem (bit-bit aynı ev)
- **QEMU/KVM** — organları izole VM’de koşturma
- **ZFS / Btrfs** + yedekleme (restic/borg docs)
- **age / rage / GnuPG** — disk ve yedek şifreleme
- **WireGuard** (kendi cihazların arası; bulut VPN şart değil)
- **Syncthing** — peer yedek; merkezi sunucuya dilenmeden
- **Local DNS (Unbound) + offline root hints**
- **Air-gap güncelleme:** USB/sneakernet + imzalı paket praktiği (debian offline mirror docs)

#### B) Yazılım egemenliği (ayna + üret)
- **Tam offline mirror:** PyPI/npm/crates **yerel cache** (uv/pip/verdaccio/athens docs)
- **Vendor everything** disiplini + **SBOM** (Syft) + güvenlik tarama (Grype) — evde
- **Reproducible builds** açık rehberler
- **AppImage / Flatpak / portable Electron** paketleme — “kurulum interneti” şart değil
- **Bootc / immutable OS** fikirleri (isteğe bağlı ileri)

#### C) Akıl egemenliği (model evi)
- **GGUF/llama.cpp** derin; **llamafile** tek-binary beyin
- **vLLM / Ollama** ops; **speculative decoding** açık notlar
- **LoRA/QLoRA/PEFT** — kendi üslubunu / ilim dilini evde öğret
- **DPO/ORPO** açık tarifler (hizalama evde; bulut RLHF yok)
- **Eval evde:** lm-eval-harness; kendi “Rüzgar sınavları” (yalansız oldu)
- **Çok beyin:** kod modeli + ilim modeli + hızlı model — hepsi diskte
- **Multimodal yerel:** LLaVA / CLIP açık ağırlık+docs (görür-anlar çevrimdışı)
- **Embedding + rerank** tamamen lokal (bge / multilingual MiniLM — zaten yolunuz var; derinleştir)

#### D) Hafıza egemenliği (ruh)
- **CRDT / local-first** (Automerge, Ink & Switch yazıları) — çakışmasız oda senkronu
- **SQLite advanced** (FTS5, session) — hafıza odası motoru
- **RDF/SPARQL veya property graph** açık kitaplar — bilgi sarayı şeması
- **Provenance:** “bu cevap hangi cilt/sayfadan” izi — kendi protokolünüz
- **Unutma / silme / miras:** politikalar + kriptolu arşiv; “öldüm, anahtar X’te”
- **Zaman çizelgesi:** yerel takvim (CalDAV self-host docs) — brifing bulutsuz

#### E) Sahne egemenliği (tiyatro evi)
- **Godot** tam + asset pipeline offline
- **Blender** Python + geometry nodes docs — sahne objesi üretimi
- **glTF / OpenUSD** (açık seçilebilen kısımlar) — asset standardı
- **Offline tile / MBTiles** harita; **Natural Earth**; kendi coğrafya paketi
- **Ücretli stok yok:** kendi prosedürel doku/ses (shader + ses sentezi açık)
- **csound / SuperCollider / FluidSynth** — sahne müziği / ezan-ton / brifing müziği evde
- **Font egemenliği:** açık fontlar (OFL) + Arapça/Osmanlı glif setleri yerelde

#### F) Dil / tercüme egemenliği
- **Kendi MT modelleri** (OPUS fine-tune) + sözlük birleştirme
- **Klasik Arapça araçları** (CAMeL, Farasa) + **Osmanlıca** açık kaynaklar (varsa)
- **Morfoloji / analizör** gövdeleri — meal-şerh katmanı için
- **Kendi terim bankası** (TBX/CSV) — Rüzgar jargonu sabit

#### G) Fren ve hukukî el (güç + ahlak)
- **Policy-as-code** (OPA/Rego veya kendi JSON policy)
- **Audit log** tasarımı (append-only, hash zinciri açık tarifler)
- **Threat model** açık şablonlar (STRIDE eğitim) — kendi evin
- **İslamî / ahlakî sınır** metinleri zaten külliyatta — karar ağacı ile bağ
- **Çocuk / mahrem / silah / suç** kapıları — kod+politika, web filtresine güvenme

#### H) Maddeye inen el (en ileri — sonra)
- **CNC / 3B yazıcı G-code** + FreeCAD docs — “sahneden parçaya”
- **ROS2 + firmware** — ev robotu / kamera kolu
- **SDR (rtl-sdr)** eğitim — dikkat: yasal sınır; yalnızca dinleme/eğitim
- **Home Assistant** + yerel otomasyon — ev “süper-el”in fiziksel uzvu
- **Meshtastic / LoRa** (acil iletişim; bulutsuz komşu ağı) — vizyon uç

#### I) Bilim fabrikası (sahne + ilim)
- **SymPy / SageMath** docs — sembolik kanıt, ders tahtası
- **Astropy / Celestia-benzeri açık** — uzay sahnesi
- **Biopython / kimya açık** (RDKit) — dikkat etik; eğitim
- **TeX Live / typst** — belge/sunum/kitap **evde** dizgi (Ofis’e dilenmeden)

### 8.3 “Tam bağımsız Rüzgar” — hayal sahnesi (ürün dili)

1. **Kabloyu çek** — sohbet, ses, kütüphane, sahne, kod atölyesi ayakta.  
2. **“Bu meselede kim ne demiş?”** — yalnız disk; web yok.  
3. **“Bana yeni bir masa aracı yaz”** — organ fabrikası derler, test eder, sahneye takar.  
4. **Gece** — indeks, yedek, film kuyruğu, model eval; sabah rapor.  
5. **“Bunu unut”** — gerçek siler; miras kuralına uyar.  
6. **İki PC** — Syncthing ile aynı ruh; bulut hesabı yok.  
7. **Yıllar sonra** — hafıza odaları durur; Rüzgar hâlâ senin dilini konuşur (LoRA + külliyat).

### 8.4 Bilinçli sınır (hayal kopmasın, kanun/güven kırılmasın)

- Korsan kitap / crack / lisans kırıcı yok  
- Saldırı silahı / casusluk tarifleri yok  
- “Her şeyi casus gibi dinle” yok — mahremiyet senin  
- SDR / telsiz: yalnızca yasal çerçeve  
- Biyoloji/kimya: eğitim; silahlaştırma yok  

### 8.5 Pratik okuma

§2–§6 = mühendis + motor yakıtı  
§7 = web’siz güçlü el  
**§8 = ev-devlet / hava boşuğu / maddeye inen el** — en dış çember; Şamile + A–B + §7 oturmadan buraya koşulmaz.

**Cümle:** Tam bağımsız Rüzgar, internetten *daha akıllı* olmak zorunda değil — internet *olmadan eksiksiz* olmak zorunda.

---

## 9) Sahne egemenliği — hayal zorlaması (2026-11-05, Mimar netleştirmesi)

**Net ilke (Mimar):** İnterneti kapatmıyoruz.  
- **İlim / bellek / açıklama** → önce hafıza + kütüphane (RAG).  
- **Güncel / canlı** → web (zaten S4 niyet-koşullu).  
- **Sahne** → mümkün mertebe **kendi evinde tam iş yapsın**; sahne çalışmak için siteye, CDN’e, online editöre dilenmesin.

Önceki maddeler (FFmpeg, Godot, Three, CV…) **yakıt**.  
Buradaki liste: **sahnenin kendisini devlet gibi kurmak** için ekstra gerekenler — “tam bağımsız sahnede iş”.

### 9.1 Sahne ne demek (Rüzgar tiyatrosu)

Konuşursun → ana motor niyetler → **tek büyük sahne** cevap verir:  
ders tahtası, delil yağmuru, kitap yürüyüşü, müze camı, coğrafya turu, tarih koridoru, uzay, dil laboratuvarı, hafıza odası, atölye (kod|önizleme|test), brifing.

Sahne bağımsızdır = bu odaların **hepsi yerelde** açılır, kaydolur, geri sarılır, film olur; asset ve motor diskte.

### 9.2 Sahne çekirdeği — mimari külliyat (listeye EK)

| Gerekli yetenek | Yüklenecek ciddi gövde (yasal-açık) | Sahlede ne olur |
|-----------------|-------------------------------------|-----------------|
| **Sahne grafiği / ECS** | Godot scene tree (derin); **Bevy ECS** / genel ECS yazıları; **entity-component** açık kitapçılar | Her nesne (kart, kitap, kamera, ışık) yönetilir |
| **Kompozitör / katman** | **Porter-Duff** / compositing açık notlar; Cairo/Skia; **CSS/SVG compositing** MDN derin | Cam cam katman: meal üstüne şerh üstüne delil |
| **Zaman çizelgesi / yönetmen** | **OpenTimelineIO**; film kurgusu açık dersler (shot/cut/pace); FFmpeg filtergraph | “Kısa film ders”, gece kuyruğu, geri sar |
| **Kamera & ışık dili** | Sinematografi açık rehberler (shot size, continuity); Three/Godot camera docs | Müze / koridor / brifing hissi |
| **2D çizim masası** | **Excalidraw** (açık) kaynak+docs; **SVG spec** derin; **Rough.js** | Çizim motoru sahnesi — online whiteboard yok |
| **Belge / sayfa çevirici** | **PDF.js**; **mupdf**; epub.js / açık e-kitap; kendi “cilt-sayfa” protokolünüz | Kitabı sahnede yürütmek |
| **Tablo / veri sahnesi** | **Apache ECharts** veya **Chart.js** + **D3** seçme derin; **Observable Plot** açık | Tablo motoru canlı sahne |
| **Sunum / slayt** | **Reveal.js** / **impress.js** (açık); typst/Beamer (TeX) | Sunum masası yerelde |
| **Matematik animasyon** | **Manim** (3Blue1Brown motoru, açık) + docs | Ders tahtası “canlı ispat” |
| **Metin motoru (RTL/Arapça)** | HarfBuzz; **FriBidi**; Unicode bidi; Pango; Arapça font shaping açık yazılar | Klasik satır sahnede kırılmadan |
| **Kart / delil sistemi** | Information design açık (erişilebilir özetler); **JSON Schema** ile kart tipi | “Kim ne demiş?” yağmuru — şablon diskte |
| **Karşılaştırma stüdyosu** | Diff algoritmaları (Myers açık anlatım); **monaco/code mirror** açık; side-by-side UX | Müellif/asır/meşrep karşılaştırma |
| **Hafıza odası = sahne save** | Sahne serializasyonu (glTF + kendi `scene.json`); CRDT (Automerge) | “Geçen kışki oda”ya girmek |
| **Avatar / konuşan yüz** | **VRM** açık; **viseme/lipsync** açık tarifler; Whisper zaman damgası; (Sadtalker yalnızca yasal/lokal politikaya uygunsa) | Rüzgar yüzü sahnede söyler |
| **Uzamsal ses** | Web Audio / OpenAL / Godot audio bus; Tone.js | Sahne yönü; brifing / ders ayrımı |
| **UI chrome yerelde** | **ImGui** veya kendi panel dili; Electron zaten var — **tüm ikon/font/CSS vendor** | CDN söndü diye sahne çıplak kalmaz |
| **Asset evi** | Kendi paket formatı (`raf://`, `sahne://`); MBTiles; glTF; açık texture/HDRI setleri (CC0) | Dış stok sitesine dilenmez |
| **Sahne betiği** | Küçük DSL (Crafting Interpreters ile); veya **Lua** / **WASM** guest | “Sahneye şunu koy” sözden script |
| **Erişilebilir sahne** | WCAG; klavye ile sahne; yüksek kontrast preset | Herkes için tiyatro |
| **Dışa aktarım** | Sahne → PDF/PNG/mp4/pptx (yerel); typst+FFmpeg | Paylaşım web editörsüz |

### 9.3 Sahne odaları — her oda için ekstra “ne lazım” (hayal)

Bunlar ürün odası; yanına **kütüphane yakıtı** şart:

1. **Ders tahtası** — Manim + tahta texture + el yazısı font (açık) + kalem stroke motoru  
2. **Delil mahkemesi** — kart şeması + zincir animasyonu + kaynak künye şablonu  
3. **Kitap koridoru** — PDF.js sayfa kamerası + raf geometrisi + “kaldığın sayfa” pin  
4. **Müze camı** — vitrin shader + etiket + çok dilli plaka (tercüme katmanı)  
5. **Coğrafya turu** — MapLibre offline + yükseklik + güzergâh animasyonu  
6. **Tarih koridoru** — timeline ECS + dönem asset paketi (kıyafet/mimari CC0 veya kendi çizim)  
7. **Uzay penceresi** — astropy + basit orbital + gökyüzü cubemap (CC0)  
8. **Dil laboratuvarı** — satır katmanları (metin|meal|şerh) + morph highlight  
9. **Hafıza sarayı** — mekân-mnemonik (açık memory palace yazıları) + oda mesh  
10. **Atölye sahnesi** — sohbet|kod|önizleme|test dörtlü; Monaco + sandboxed iframe/webview **yerel**  
11. **Brifing sabahı** — HUD + üç ip kartı + ses kimliği  
12. **Yönetmen masası** — OTIO timeline; kes/birleştir; gece render kuyruğu  

### 9.4 Sahne için “eli güçlü” komut dili (külliyat + tasarım)

İndekslenecek / yazılacak (bilgi + kendi spesifikasyon):

- **Sahne niyet sözlüğü** (Türkçe): “tahtaya yaz”, “bu âyeti camla”, “haritadan göster”, “iki müellifi yan yana”, “geri sar”, “film yap”  
- **Motor bus sözleşmesi** (JSON-RPC/Schema) — ana motor → sahne organı  
- **Onay kapıları sahnede** — tehlikeli eylem kırmızı çerçeve (policy)  
- **Yerel asset manifesto** — hangi paket hangi oda için; eksikse “üret / çiz” (programlama motoru)

### 9.5 Bilgi akışı (karışıklık olmasın)

```
Soru (ilim)     → hafıza / kütüphane RAG     → sahneye kart/kitap/tahta
Soru (güncel)   → web (niyet-koşullu)        → sahneye “canlı şerit” (isteğe bağlı)
Emir (sahne)    → yerelde sahne motoru      → CDN/web editör YOK
Emir (yeni alet)→ programlama organ fabrikası → sahneye panel düşer
```

İnternet **var**; sahne ve bellek **ona muhtaç değil**. Web sahneye *misafir şerit* olarak gelebilir (haber, kur, canlı yayın) — omurga değil.

### 9.6 Önceki listelerden ayırım

| Bölüm | Odak |
|-------|------|
| §2–6 | Bilgisayar / motor yakıtı eserleri |
| §7 | Web’siz güçlü el (genel) |
| §8 | Ev-devlet / air-gap ufku |
| **§9** | **Tam bağımsız SAHNE’de iş** — tiyatro omurgası + oda + komut |

### 9.7 Başarı cümlesi

**Sahne bağımsızdır = Rüzgar konuşunca tiyatro ayağa kalkar; kütüphane yakıt verir; güncel bilgi isterse web’den şerit gelir; sahne çalışmak için kimseye online dilenmez.**
