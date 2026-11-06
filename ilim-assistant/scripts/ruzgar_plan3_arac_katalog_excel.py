#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""3.PLAN+ DIS_EL_ARAC_KATALOGU — Excel v2 YÜKSELTME (Plan 2'den SONRA).

Kapı (kilit): Şamile RAG + 1.PLAN + 2.PLAN+ bitmeden aksiyon yok.
Amaç: Rüzgar dışarıda eli ayağına dolaşmayan; yerinde PROFESYONEL,
yerinde BEYEFENDİ, yerinde ÇEVİK (yasal) tam bir operatör olsun.

KİMLİK MODLARI (Mimar hayali — yasal çerçeve):
  · PROFESYONEL — cerrah: plan→test→diff→yalansız oldu
  · BEYEFENDİ GEZGİN — web'de nazik, robots/rate-limit, izinli kapı, iz bırakmayan
  · ÇEVİK OPERATÖR — az adım, isabet, sessiz (metafor); SUÇ/exploit/hırsızlık YOK

v2 üst katmanlar (21–28): diplomasi · zaman/dünya · öğretmen · egemenlik ·
  estetik/huzur · ekonomi/kota · ikiz simülasyon · SON DURUM vizyonu.

Çıktı:
  Desktop/.../3.PLAN+_DIS_EL_ARAC_KATALOGU/<KAT>/...
  + 00_SON_DURUM_3.PLAN_SONRASI.xlsx
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

OUT_ROOT = Path(
    r"C:\Users\hayma\Desktop\RÜZGAR\RÜZGAR KÜTÜPHANE ENVANTER"
    r"\3.PLAN+_DIS_EL_ARAC_KATALOGU"
)

HEADERS = [
    "NO",
    "ARAÇ / ESER / SPEC (ORİJİNAL)",
    "TÜRKÇE AD / ROL",
    "KAYNAK / KURUM",
    "RÜZGARA NE KATAR",
    "MODÜL",
    "KAPSAM",
    "MOD / DALGA",
    "NOT",
]

# (orig, tr, kaynak, katar, modul, kapsam, mod, not)
CATS: dict[str, tuple[str, list[tuple]]] = {
    "01_AJAN_CEKIRDEK": (
        "01 AJAN ÇEKİRDEĞİ (döngü + beyin-el köprüsü)",
        [
            ("ReAct / tool-calling agent loop papers", "Ajan Döngüsü (ReAct)", "Yao et al. + açık", "Planla→araç→gözle→düzelt omurgası", "çekirdek", "makale+tarif", "Profesyonel", "Açık — kritik"),
            ("OpenAI-compatible tools JSON schema", "Araç Çağırma Şeması", "açık de facto", "Model serbest uydurmasın; şema çağırısın", "çekirdek", "spec", "Profesyonel", "Açık — kritik"),
            ("JSON-RPC 2.0 motor bus", "Motor Otobüsü", "jsonrpc.org", "Her el aynı dilde konuşsun", "çekirdek", "spec", "Profesyonel", "Açık — kritik"),
            ("Planner / Executor / Critic üçlü tarif", "Planlayıcı-Uygulayıcı-Eleştirmen", "açık agent tarif", "Eli ayağına dolanmasın; roller ayrı", "çekirdek", "tarif", "Profesyonel", "Açık — kritik"),
            ("Short-term scratchpad + working memory", "Çalışma Tahtası", "açık+iç", "Adımlar kaybolmasın", "çekirdek", "şema", "Profesyonel", "İç"),
            ("Goal decomposition / tree-of-tasks", "Hedef Ağacı", "açık", "Büyük işi parçala", "çekirdek", "tarif", "Profesyonel", "Açık"),
            ("Timeout / budget / step-limit politikası", "Adım ve Süre Bütçesi", "iç", "Sonsuz döngü yok", "çekirdek", "politika", "Profesyonel", "İç — kritik"),
            ("Human-in-the-loop interrupt", "İnsan Kesmesi", "açık+iç", "Mimar 'dur' deyince dursun", "çekirdek", "tarif", "Profesyonel", "İç — kritik"),
            ("Idempotent tool calls", "Tekrar Güvenli Çağrı", "açık", "İkinci kez bozmasın", "çekirdek", "tarif", "Profesyonel", "Açık"),
            ("Partial success / compensate / rollback", "Kısmi Başarı / Geri Sar", "açık", "Yarım işte toparlan", "çekirdek", "tarif", "Profesyonel/Çevik", "Açık"),
            ("Multi-model router (hızlı/derin/kod)", "Beyin Yönlendirici", "2.PLAN akıl", "İşe göre kafa seç", "çekirdek", "tarif", "Profesyonel", "Çapraz 2.PLAN"),
            ("Cloud fallback quota-aware", "Kota Bilinçli Bulut", "2.PLAN web", "Yerel yetmezse nazikçe bulut", "çekirdek", "tarif", "Beyefendi", "Çapraz"),
            ("Session transcript + replay", "Oturum Kayıt / Replay", "açık+iç", "Ne yaptığını yeniden oyna", "çekirdek", "şema", "Profesyonel", "İç"),
            ("Confidence / abstain politikası", "Emin Değilse Dur", "iç", "Uydurma el hareketi yok", "çekirdek", "politika", "Profesyonel", "İç"),
            ("Parallel tool fan-out + join", "Paralel El / Birleştir", "açık", "Birden fazla araç aynı anda (güvenli)", "çekirdek", "tarif", "Çevik", "Açık"),
            ("Capability token per tool call", "Çağrı Başı Yetki Jetonu", "açık+iç", "Her el kendi izniyle", "çekirdek", "spec", "Profesyonel", "Kritik"),
            ("Daemon agent vs interactive agent", "Arka Plan / Canlı Ajan", "iç", "Gece vardiyası + sohbet eli ayrı", "çekirdek", "mimari", "Profesyonel", "İç"),
            ("Eval harness 'yalansız oldu'", "Ajan Sınavı", "2.PLAN F", "El gerçekten iş bitirdi mi", "çekirdek", "docs", "Profesyonel", "Kritik"),
        ],
    ),
    "02_ARAC_KATALOG_OMURGA": (
        "02 ARAÇ KATALOĞU OMURGASI (kayıt + sürüm + keşif)",
        [
            ("Tool registry JSON Schema (iç)", "Araç Sicili Şeması", "Rüzgar", "Her aracın kimlik kartı", "katalog", "şema", "Profesyonel", "İç — kritik"),
            ("Semantic tool search (embed catalog)", "Anlamsal Araç Arama", "açık+iç", "Doğru eli bul", "katalog", "tarif", "Çevik", "Kritik"),
            ("Tool versioning SemVer", "Araç Sürümü", "SemVer", "Eski el bozulmasın", "katalog", "spec", "Profesyonel", "Açık"),
            ("Deprecation / sunset policy", "Araç Emeklilik", "iç", "Ölü el kalmasın", "katalog", "politika", "Profesyonel", "İç"),
            ("Input/output examples per tool", "Örnek Çağrı Kartı", "iç", "Model doğru kullansın", "katalog", "şablon", "Profesyonel", "İç"),
            ("Risk class A/B/C/D matrix", "Risk Sınıfı Matrisi", "iç", "Tehlike seviyesine göre onay", "katalog", "matris", "Profesyonel", "İç — kritik"),
            ("Side-effect declaration", "Yan Etki Beyanı", "açık+iç", "Salt okunur mu, yazar mı", "katalog", "şema", "Profesyonel", "Kritik"),
            ("Cost / latency / quota tags", "Maliyet Etiketleri", "iç", "Pahalı eli boşuna yakma", "katalog", "şema", "Beyefendi", "İç"),
            ("Locale / TR-AR tool descriptions", "Çift Dil Araç Kartı", "iç", "Türkçe+Arapça keşif", "katalog", "i18n", "Profesyonel", "İç"),
            ("Plugin manifest (organ eklenti)", "Eklenti Manifesti", "açık+iç", "Yeni organ takılabilsin", "katalog", "spec", "Profesyonel", "Kritik"),
            ("Hot-reload tool registry", "Canlı Sicil Yenileme", "iç", "Restart'siz yeni el", "katalog", "tarif", "Çevik", "İç"),
            ("Tool healthcheck probes", "Araç Sağlık Probe", "açık", "Ölü eli çağırma", "katalog", "tarif", "Profesyonel", "Açık"),
            ("Catalog UI / sahne paneli", "Araç Rafı Sahnesi", "iç", "Mimar elleri görsün", "katalog", "UX", "Profesyonel", "İç"),
            ("Import/export catalog", "Sicil İçe-Dışa", "iç", "Yedek / taşınır el seti", "katalog", "şema", "Profesyonel", "İç"),
            ("OpenAPI→tool auto-import", "OpenAPI'den El Üret", "açık", "API fişini otomatik el yap", "katalog", "tarif", "Çevik", "Açık — kritik"),
            ("MCP-style tool server notes (açık fikir)", "Harici Araç Sunucusu Fikri", "açık ekosistem", "İleride dış el sunucusu", "katalog", "not", "Profesyonel", "İleri — yasal"),
        ],
    ),
    "03_DOSYA_BELLEK_DEPO": (
        "03 DOSYA / BELLEK / DEPO ELLERİ",
        [
            ("fs.read / list / search (izinli kök)", "Dosya Oku / Listele / Ara", "iç + ripgrep", "İzinli klasörde bul", "dosya", "araç", "Profesyonel", "Kritik — kök allowlist"),
            ("fs.write / patch / atomic save", "Dosya Yaz / Yama", "iç", "Cerrah yama; atomik kayıt", "dosya", "araç", "Profesyonel", "Kritik"),
            ("fs.move / copy / mkdir (onaylı)", "Taşı / Kopyala / Klasör", "iç", "Düzen eli", "dosya", "araç", "Profesyonel", "Onay eşiği"),
            ("fs.delete (çift onay + çöp kutusu)", "Sil (Çift Onay)", "iç", "Geri dönüşümlü sil", "dosya", "araç", "Profesyonel", "Fren — kritik"),
            ("PDF/DOCX/MD ingest tool", "Belge Yutucu", "Pandoc/pdf", "Kütüphaneye çevir", "dosya", "araç", "Profesyonel", "Kritik"),
            ("OCR photo→text tool", "OCR Eli", "Tesseract/Docling", "Foto raf olsun", "dosya", "araç", "Profesyonel", "Kritik"),
            ("Hash / checksum verify", "Bütünlük Kontrolü", "açık", "Dosya bozulmasın", "dosya", "araç", "Profesyonel", "Açık"),
            ("Dedup / similar file finder", "Çift Dosya Avcısı", "açık", "Kütüphane şişmesin", "dosya", "araç", "Çevik", "Açık"),
            ("Archive zip/tar extract (sandbox)", "Arşiv Açıcı", "iç", "Güvenli aç", "dosya", "araç", "Profesyonel", "Sandbox"),
            ("Quota disk usage reporter", "Disk Kota Raportörü", "iç", "2TB yaklaşınca haber", "dosya", "araç", "Profesyonel", "İç"),
            ("Cold/hot storage mover", "Sıcak-Soğuk Depo", "iç", "Sık kullanılan SSD'de", "dosya", "araç", "Profesyonel", "İç"),
            ("SQLite/FTS personal search tool", "Kişisel Arama Eli", "SQLite FTS5", "Ev dosyası bul", "dosya", "araç", "Çevik", "Kritik"),
            ("Bookmark / pin path tool", "Yol İğnesi", "iç", "Sık yollar hazır", "dosya", "araç", "Beyefendi", "İç"),
            ("Secure delete (profile vault)", "Güvenli Silme", "2.PLAN mahrem", "Mahrem bitince bitsin", "dosya", "araç", "Profesyonel", "Çapraz"),
            ("Export bundle (portable library slice)", "Taşınır Dilim", "iç", "USB ile kütüphane parçası", "dosya", "araç", "Profesyonel", "İç"),
            ("Watch folder → auto-ingest", "Klasör Nöbetçisi", "watchfiles", "Attın mı indekse aday", "dosya", "araç", "Çevik", "Kritik"),
        ],
    ),
    "04_TERMINAL_SANDBOX": (
        "04 TERMİNAL / SANDBOX (güvenli güç)",
        [
            ("Allowlisted shell runner", "İzinli Kabuk", "iç", "Sadece beyaz listedeki komutlar", "terminal", "araç", "Profesyonel", "Kritik"),
            ("Bubblewrap / Landlock / job object isol", "İzolasyon Kutusu", "Linux/Win", "Kaçmasın", "terminal", "docs+araç", "Profesyonel", "Kritik"),
            ("stdout/stderr capture + size cap", "Çıktı Yakalama", "iç", "Log patlamasın", "terminal", "araç", "Profesyonel", "İç"),
            ("cwd jail (project root only)", "Çalışma Dizini Hapisi", "iç", "Sistem köküne çıkmasın", "terminal", "politika", "Profesyonel", "İç"),
            ("Network-off mode for shell", "Ağsız Kabuk Modu", "iç", "İndirmeden derle/test", "terminal", "mod", "Profesyonel", "İç"),
            ("Elevated ops require Mimar PIN", "Yükseltilmiş İş PIN", "iç", "Admin eli kapılı", "terminal", "fren", "Profesyonel", "İç — kritik"),
            ("Playwright/pytest runner tool", "Test Koşucu", "Playwright/pytest", "Yalansız oldu", "terminal", "araç", "Profesyonel", "Kritik"),
            ("Build / lint / format runners", "Derle / Lint / Format", "proje araçları", "Kod cilası", "terminal", "araç", "Profesyonel", "Açık"),
            ("Process kill / timeout", "Süreç Kes / Timeout", "iç", "Takılan işi öldür", "terminal", "araç", "Çevik", "İç"),
            ("Env var vault injection", "Gizli Ortam Değişkeni", "safeStorage", "Anahtar sızmasın", "terminal", "araç", "Profesyonel", "Kritik"),
            ("Wasm WASI runner (mini organ)", "Wasm Koşucu", "Wasmtime", "Daha güvenli mini kod", "terminal", "araç", "Profesyonel", "Açık"),
            ("Container one-shot (podman rootless)", "Tek Atımlık Konteyner", "Podman", "Kirli iş kutuda", "terminal", "araç", "Profesyonel", "Açık"),
            ("Replayable command ledger", "Komut Defteri", "iç", "Ne çalıştı kaydı", "terminal", "audit", "Profesyonel", "İç"),
            ("Diff-after-command", "Komut Sonrası Diff", "git/fs", "Ne değişti gör", "terminal", "araç", "Profesyonel", "Kritik"),
            ("PowerShell + bash dual adapters", "Çift Kabuk Adaptörü", "Win/Unix", "Windows evi uyumlu", "terminal", "araç", "Profesyonel", "Kritik"),
            ("Dry-run mode", "Kuru Koşu", "iç", "Önce göster sonra yap", "terminal", "mod", "Beyefendi", "İç — kritik"),
        ],
    ),
    "05_TARAYICI_BEYEFENDI": (
        "05 TARAYICI — BEYEFENDİ GEZGİN (nazik · çevik · yasal)",
        [
            ("Playwright / Puppeteer controlled browser", "Kontrollü Tarayıcı", "Playwright", "Sayfayı gör-tıkla (izinli)", "tarayıcı", "araç", "Beyefendi/Çevik", "Kritik — allowlist"),
            ("Headless + headed dual mode", "Görünür / Görünmez Mod", "Playwright", "İstersen izle, istersen sessiz", "tarayıcı", "mod", "Beyefendi", "Açık"),
            ("Domain allowlist / blocklist", "Site İzin Kapısı", "iç", "Sadece açık kapılar", "tarayıcı", "politika", "Beyefendi", "İç — kritik"),
            ("robots.txt respect + Crawl-delay", "Robots Saygısı", "açık etik", "Kaba bot değil beyefendi", "tarayıcı", "politika", "Beyefendi", "Kritik"),
            ("Rate limit / jitter / polite concurrency", "Nazik Hız Limiti", "açık", "Sunucuyu ezme", "tarayıcı", "politika", "Beyefendi", "Kritik"),
            ("User-Agent honesty + Rüzgar kimliği", "Dürüst Kimlik", "iç", "Yalanci bot UA yok (politika)", "tarayıcı", "politika", "Beyefendi", "İç"),
            ("Readability extract in-page", "Sayfa Temizleyici", "Readability/Trafilatura", "Çöpü almadan metin", "tarayıcı", "araç", "Çevik", "Kritik"),
            ("Screenshot + a11y snapshot", "Ekran + Erişim Anlığı", "Playwright", "Görüp anla / kanıtla", "tarayıcı", "araç", "Profesyonel", "Kritik"),
            ("Form fill (onaylı) / login vault", "Form / Giriş Kasası", "iç", "Hesap bilgisi kilitli; onaylı", "tarayıcı", "araç", "Profesyonel", "Fren"),
            ("Download to quarantine folder", "İndirme Karantinası", "iç", "Önce tara sonra kabul", "tarayıcı", "araç", "Profesyonel", "Kritik"),
            ("Session cookie jar isolation", "Çerez İzolasyonu", "iç", "Profiller karışmasın", "tarayıcı", "araç", "Profesyonel", "İç"),
            ("Anti-bot detection éthics: stop & ask", "Engelde Dur-Sor", "iç", "Bypass/exploit yok; Mimar'a sor", "tarayıcı", "politika", "Beyefendi", "Kritik — exploit yok"),
            ("Tab/workspace manager", "Sekme / İş Alanı", "iç", "Eli ayağına dolaşmasın", "tarayıcı", "araç", "Çevik", "İç"),
            ("Offline replay of captured pages", "Yakalanmış Sayfa Replay", "WARC/SingleFile", "Tekrar web'e dilenme", "tarayıcı", "araç", "Beyefendi", "Açık"),
            ("Visual regression (izinli kendi UI)", "Görsel Regresyon", "Playwright", "Kendi sahneyi bozma", "tarayıcı", "araç", "Profesyonel", "Açık"),
            ("Gentleman profile presets", "Beyefendi Profili", "iç", "Yavaş/nazik/gece gezinti seti", "tarayıcı", "mod", "Beyefendi", "İç — kritik"),
            ("Agile operator profile presets", "Çevik Operatör Profili", "iç", "Az adım, isabet, sessiz (yasal)", "tarayıcı", "mod", "Çevik", "İç — suç yok"),
            ("CAPTCHA / 2FA: human handoff", "İnsan Devri", "iç", "Otomatik kırma yok", "tarayıcı", "fren", "Beyefendi", "Kritik"),
        ],
    ),
    "06_WEB_NAZIK_GETIRI": (
        "06 WEB GETİRİ — nazik av / arşiv / kaynak kartı",
        [
            ("HTTP GET with cache/ETag", "Önbellekli GET", "RFC9111", "Aynı sayfayı yakma", "web", "araç", "Beyefendi", "Kritik"),
            ("Trafilatura / readability CLI tool", "Metin Avcısı", "Trafilatura", "Temiz gövde", "web", "araç", "Çevik", "Kritik"),
            ("RSS/Atom watcher", "Besleme Nöbetçisi", "feedparser", "Güncel gelsin", "web", "araç", "Beyefendi", "Kritik"),
            ("Sitemap discover (allowlist)", "Site Haritası Keşif", "açık", "İzinli sitede yapı", "web", "araç", "Çevik", "Allowlist"),
            ("Source card builder (citation)", "Kaynak Kartı Üretici", "iç", "Web şeridi künyeli", "web", "araç", "Profesyonel", "Kritik"),
            ("ArchiveBox / SingleFile / WARC", "Sayfa Dondurucu", "ArchiveBox", "Kanıtlı kopya", "web", "araç", "Profesyonel", "Açık"),
            ("Link checker / dead link", "Ölü Bağlantı Avı", "açık", "Kütüphane linkleri sağlam", "web", "araç", "Profesyonel", "Açık"),
            ("Mirror open docs (pip/npm ethics)", "Açık Docs Aynası", "2.PLAN", "Offline docs ekmek", "web", "araç", "Profesyonel", "Çapraz"),
            ("Search API adapters (izinli)", "Arama API Adaptörleri", "sağlayıcı docs", "Bul → getir → yerelleştir", "web", "araç", "Çevik", "Kota bilinçli"),
            ("Content-type / size firewall", "İçerik Duvarı", "iç", "Dev dosya felç etmesin", "web", "politika", "Profesyonel", "İç"),
            ("Malware scan hook (ClamAV ops)", "İndirme Tarama", "ClamAV opsiyon", "Zehirli dosya girsin", "web", "araç", "Profesyonel", "Opsiyon"),
            ("License detector (SPDX/scancode)", "Lisans Dedektörü", "ScanCode/SPDX", "Telif tuzağına düşme", "web", "araç", "Profesyonel", "Kritik"),
            ("Change detect / watch URL", "Sayfa Değişim Nöbeti", "açık", "Önemli sayfa güncellenince haber", "web", "araç", "Beyefendi", "Açık"),
            ("Parallel polite fetch pool", "Nazik Paralel Havuz", "iç", "Çevik ama ezmeden", "web", "araç", "Çevik/Beyefendi", "İç"),
            ("Geo/language prefer TR-AR-EN", "Dil Tercihli Getiri", "iç", "Rüzgar dil üçgeni", "web", "politika", "Beyefendi", "İç"),
            ("Fail-soft + explain blockage", "Engeli Açıkla", "iç", "Neden yapamadım de", "web", "UX", "Beyefendi", "İç"),
        ],
    ),
    "07_KUTUPHANE_OTONOM": (
        "07 KÜTÜPHANE OTONOM (indir · yerleştir · indeks · takip)",
        [
            ("Library add from URL (onaylı)", "URL'den Eser Ekle", "iç", "İzinli indir→rafa koy", "kütüphane", "araç", "Profesyonel", "Onay — kritik"),
            ("Library add from local folder", "Klasörden Eser Ekle", "iç", "Attığın klasörü yut", "kütüphane", "araç", "Profesyonel", "Kritik"),
            ("Category router (Şamile/CS/fenni)", "Raf Yönlendirici", "iç", "Karıştırma", "kütüphane", "araç", "Profesyonel", "Kritik"),
            ("Shard build enqueue", "Shard İndeks Kuyruğu", "RAG shard", "Gece indeks", "kütüphane", "araç", "Profesyonel", "Kritik"),
            ("Index progress reporter", "İndeks İlerleme Raportörü", "watchdog ruhu", "Kaç % / hangi kitap", "kütüphane", "araç", "Profesyonel", "Kritik — Mimar sorusu"),
            ("Stuck detector + auto-restart", "Takılma Dedektörü", "watchdog", "Benim yaptığım takip", "kütüphane", "araç", "Çevik", "Kritik"),
            ("Ready/pending catalog dashboard", "Hazır-Bekleyen Pano", "iç", "Kütüphane nabzı", "kütüphane", "UX", "Profesyonel", "İç"),
            ("Dedup by hash/title/ISBN", "Eser Tekilleştirici", "iç", "Çift kitap yok", "kütüphane", "araç", "Profesyonel", "İç"),
            ("Metadata enrich (künye)", "Künye Zenginleştirici", "açık+iç", "Yazar/cilt/sayfa", "kütüphane", "araç", "Profesyonel", "İç"),
            ("Quality gate before index", "İndeks Öncesi Kalite", "iç", "Boş/çöp metin girme", "kütüphane", "fren", "Profesyonel", "İç"),
            ("Rollback bad shard", "Kötü Shard Geri Al", "iç", "Bozulan indeksi düşür", "kütüphane", "araç", "Profesyonel", "İç"),
            ("Disk forecast before ingest", "Yer Tahmini", "iç", "100GB gelmeden uyar", "kütüphane", "araç", "Profesyonel", "İç"),
            ("Cold archive vs hot RAG", "Soğuk Arşiv / Sıcak RAG", "iç", "2TB'de akıllı katman", "kütüphane", "politika", "Profesyonel", "İç"),
            ("Nightly reindex incremental", "Gece Artımlı İndeks", "2.PLAN gece", "Yeni eserler işlensin", "kütüphane", "kuyruk", "Profesyonel", "Çapraz"),
            ("User teach→shelf tool", "Öğret→Raf", "hafıza", "Ümit öğretti kalıcı olsun", "kütüphane", "araç", "Profesyonel", "İç"),
            ("Export inventory Excel", "Envanter Excel Üret", "openpyxl", "Mimar takip etsin", "kütüphane", "araç", "Profesyonel", "Zaten yolunuz"),
            ("Multi-library search fanout", "Çok Kütüphane Arama", "RAG", "Şamile+CS+fenni birlikte", "kütüphane", "araç", "Çevik", "Kritik"),
            ("Citation-forced answer mode", "Alıntı Zorunlu Cevap", "iç", "Uydurma yok", "kütüphane", "mod", "Profesyonel", "Kritik"),
        ],
    ),
    "08_GIT_PROJE": (
        "08 GIT / PROJE ELLERİ (Cursor kardeşi omurga)",
        [
            ("git status/diff/log tools", "Git Durum / Diff / Log", "git", "Ne değişti gör", "git", "araç", "Profesyonel", "Kritik"),
            ("git add/commit (onaylı mesaj)", "Commit Eli", "git", "Kayıt düş", "git", "araç", "Profesyonel", "Onay"),
            ("branch create/switch", "Dal Eli", "git", "Deney ayrı dalsın", "git", "araç", "Profesyonel", "Açık"),
            ("PR/patch export", "Yama / PR Paketi", "git", "Dışarıya güvenli paket", "git", "araç", "Profesyonel", "Açık"),
            ("blame / pickaxe search", "Suçla / Ara", "git", "Kim ne zaman", "git", "araç", "Çevik", "Açık"),
            ("conflict assist (no force push default)", "Çakışma Asistanı", "git", "Force push varsayılan kapalı", "git", "araç", "Profesyonel", "Fren"),
            ("pre-commit / hooks runner", "Hook Koşucu", "pre-commit", "Çürük commit olmasın", "git", "araç", "Profesyonel", "Açık"),
            ("repo map / symbol index (LSP)", "Repo Haritası", "LSP/tree-sitter", "Projeyi anla", "git", "araç", "Profesyonel", "Kritik"),
            ("multi-root workspace", "Çok Kök Alan", "iç", "Birden fazla proje", "git", "araç", "Profesyonel", "İç"),
            ("changelog generator", "CHANGELOG Üretici", "açık", "Ne geldi yaz", "git", "araç", "Profesyonel", "Açık"),
            ("tag/release notes", "Sürüm Notu", "git", "Organ sürümü", "git", "araç", "Profesyonel", "Açık"),
            ("secret scan before commit", "Commit Öncesi Sır Tarama", "açık", "Anahtar kaçmasın", "git", "fren", "Profesyonel", "Kritik"),
            ("worktree parallel jobs", "Worktree Paralel", "git", "İki iş aynı anda", "git", "araç", "Çevik", "Açık"),
            ("bisect assist", "Bisect Asistanı", "git", "Bozan commiti bul", "git", "araç", "Profesyonel", "Açık"),
            ("sparse checkout large repos", "Seyrek Checkout", "git", "Dev repoda çevik", "git", "araç", "Çevik", "Açık"),
            ("mirror clone offline", "Offline Ayna Klon", "git", "İnternetsiz geliştir", "git", "araç", "Profesyonel", "Açık"),
        ],
    ),
    "09_MASA_ARAC_YUZU": (
        "09 MASA ARAÇ YÜZÜ (Belge-Tablo-Çizim-Sunum ellere bağlı)",
        [
            ("doc.create / edit / export tools", "Belge Elleri", "2.PLAN masa", "Sözden belge", "masa", "araç", "Profesyonel", "Kritik"),
            ("sheet.create / formula / chart", "Tablo Elleri", "Univer vd.", "Sözden tablo", "masa", "araç", "Profesyonel", "Kritik"),
            ("draw.create / annotate", "Çizim Elleri", "Excalidraw", "Sözden çizim", "masa", "araç", "Profesyonel", "Kritik"),
            ("deck.create / reorder / export", "Sunum Elleri", "Reveal/Slidev", "Sözden slayt", "masa", "araç", "Profesyonel", "Kritik"),
            ("cross-masa transfer", "Masalar Arası Aktar", "iç", "Tablodan sunuma", "masa", "araç", "Çevik", "İç"),
            ("undo/redo stack tool", "Geri Al Eli", "iç", "Hata olursa geri", "masa", "araç", "Profesyonel", "Kritik"),
            ("template library", "Şablon Rafı", "iç", "Hızlı profesyonel çıktı", "masa", "araç", "Profesyonel", "İç"),
            ("print/PDF pipeline", "Baskı / PDF Boru", "Pandoc/Paged", "Teslim et", "masa", "araç", "Profesyonel", "Açık"),
            ("collaborate Yjs (ileride)", "Birlikte Düzenle", "Yjs", "İki kişi aynı masa", "masa", "araç", "Beyefendi", "İleri"),
            ("masa permission scopes", "Masa İzin Kapsamı", "iç", "Hangi masa yazılabilir", "masa", "fren", "Profesyonel", "İç"),
            ("scene↔masa bridge", "Sahne-Masa Köprüsü", "iç", "Tiyatroda masa açılsın", "masa", "araç", "Profesyonel", "Kritik"),
            ("batch generate from outline", "Anahat→Ürün", "iç", "Tek emirde paket", "masa", "araç", "Çevik", "İç"),
            ("quality lint (yazım/biçim)", "Biçim / Yazım Lint", "açık", "Profesyonel çıktı", "masa", "araç", "Profesyonel", "Açık"),
            ("version snapshots of masa docs", "Masa Sürüm Anlığı", "iç", "Dünkü belgeye dön", "masa", "araç", "Profesyonel", "İç"),
            ("import office files", "Ofis İçe Aktar", "Pandoc", "Dışarıdan getir", "masa", "araç", "Profesyonel", "Açık"),
            ("export zip pack for share", "Paylaşım Zip", "iç", "Teslim paketi", "masa", "araç", "Beyefendi", "İç"),
        ],
    ),
    "10_SES_GOZ_MEDYA": (
        "10 SES / GÖZ / MEDYA ELLERİ",
        [
            ("stt.transcribe tool", "Kulak Eli (STT)", "Whisper", "Konuş→metin", "medya", "araç", "Profesyonel", "Kritik"),
            ("tts.speak tool", "Nefes Eli (TTS)", "Piper", "Metin→ses", "medya", "araç", "Profesyonel", "Kritik"),
            ("vad/barge-in control", "Kes-Dinle Eli", "Silero", "Süper-el canlı", "medya", "araç", "Çevik", "Kritik"),
            ("ffmpeg.render job", "Film Render Eli", "FFmpeg", "Gece film", "medya", "araç", "Profesyonel", "Kritik"),
            ("otio.timeline edit", "Timeline Eli", "OTIO", "Yönetmen kesimi", "medya", "araç", "Profesyonel", "Açık"),
            ("opencv.analyze frame", "Kare Analiz", "OpenCV", "Görür-ölçer", "medya", "araç", "Profesyonel", "Açık"),
            ("clip.describe image", "Görür-Anlar Eli", "CLIP/VLM", "Resmi anlat", "medya", "araç", "Profesyonel", "Açık"),
            ("screen.capture tool", "Ekran Yakalama", "Electron", "Kanıt / ders", "medya", "araç", "Profesyonel", "Onay"),
            ("subtitle generate/translate", "Altyazı Eli", "WhisperX+MT", "Film köprüsü", "medya", "araç", "Beyefendi", "Açık"),
            ("audio clean / denoise", "Ses Temizleme", "RNNoise", "Net nefes", "medya", "araç", "Beyefendi", "Açık"),
            ("godot.scene command bridge", "Sahne Komut Köprüsü", "Godot", "Tiyatroya emir", "medya", "araç", "Profesyonel", "Kritik"),
            ("manim.render math board", "Matematik Tahta Eli", "Manim", "Ders filmi", "medya", "araç", "Profesyonel", "Açık"),
            ("media quarantine + license tag", "Medya Karantina/Lisans", "iç", "Yasal asset", "medya", "fren", "Profesyonel", "İç"),
            ("playlist / chapter markers", "Bölüm İşaretleri", "açık", "Uzun dinlemede gezin", "medya", "araç", "Beyefendi", "Açık"),
            ("live OBS scene switch (onaylı)", "OBS Sahne Değiştir", "OBS", "Canlı yayın eli", "medya", "araç", "Profesyonel", "Onay"),
            ("avatar lipsync drive", "Avatar Dudak Eli", "VRM", "Yüz konuşsun", "medya", "araç", "Beyefendi", "Açık"),
        ],
    ),
    "11_OFIS_BAGLANTILARI": (
        "11 OFİS BAĞLANTILARI (posta · takvim · not · yazıcı)",
        [
            ("IMAP/SMTP tool (local creds vault)", "Posta Eli", "standart", "Oku/gönder (onaylı gönder)", "ofis", "araç", "Profesyonel", "Onay gönderimde"),
            ("CalDAV calendar tool", "Takvim Eli", "CalDAV", "Brifing + randevu", "ofis", "araç", "Profesyonel", "Açık"),
            ("Contacts CardDAV", "Rehber Eli", "CardDAV", "Kişi bul", "ofis", "araç", "Beyefendi", "Açık"),
            ("Printer spool (onaylı)", "Yazıcı Eli", "OS print", "Bas (onay)", "ofis", "araç", "Profesyonel", "Onay"),
            ("Scanner intake", "Tarayıcı Eli", "OS/TWAIN ops", "Kâğıt→OCR→raf", "ofis", "araç", "Profesyonel", "Opsiyon"),
            ("Clipboard managed paste", "Pano Eli", "OS", "Güvenli yapıştır", "ofis", "araç", "Çevik", "İç"),
            ("Notification center", "Bildirim Merkezi", "OS/Electron", "Bitti haber ver", "ofis", "araç", "Beyefendi", "İç"),
            ("Notes capture quick", "Hızlı Not", "iç", "Fikir kaçmasın", "ofis", "araç", "Çevik", "İç"),
            ("Reminder / alarm tool", "Hatırlatıcı", "iç+DB", "Sabah üç ip", "ofis", "araç", "Profesyonel", "Kritik"),
            ("File share LAN (izinli)", "Yerel Paylaşım", "SMB/HTTP izinli", "Ev içi paylaş", "ofis", "araç", "Profesyonel", "Allowlist"),
            ("PDF sign placeholder (yasal)", "PDF İmza Yer Tutucu", "açık", "İmza alanı hazırla (e-imza ayrı)", "ofis", "araç", "Profesyonel", "Dikkat"),
            ("Meeting notes from STT", "Toplantı Tutanağı", "STT+masa", "Ses→tutanak", "ofis", "araç", "Profesyonel", "Açık"),
            ("Translate mail/doc bridge", "Posta/Belge Tercüme", "MT", "Köprü", "ofis", "araç", "Beyefendi", "Açık"),
            ("Spam/phishing warn (savunma)", "Oltalama Uyarısı", "açık kurallar", "Tuzak mailde fren", "ofis", "fren", "Profesyonel", "Exploit yok"),
            ("Vacation / focus mode", "Odak / Tatil Modu", "iç", "Rahatsız etme", "ofis", "mod", "Beyefendi", "İç"),
            ("Export mailbox slice (mahrem)", "Posta Dilimi Dışa", "iç", "Taşınır/mahkeme yedek", "ofis", "araç", "Profesyonel", "Mahrem"),
        ],
    ),
    "12_API_KONEKTOR": (
        "12 API KONEKTÖR PAZARI (fişler)",
        [
            ("Generic REST connector", "Genel REST Fişi", "OpenAPI", "Her API'yi el yap", "api", "araç", "Profesyonel", "Kritik"),
            ("GraphQL connector", "GraphQL Fişi", "açık", "Modern API", "api", "araç", "Profesyonel", "Açık"),
            ("Webhook receiver/sender", "Webhook Eli", "iç", "Dış olay dinle/gönder", "api", "araç", "Çevik", "Frenli"),
            ("OAuth device/code flow vault", "OAuth Kasası", "standart", "Güvenli yetki", "api", "araç", "Profesyonel", "Kritik"),
            ("Gemini/Groq/OpenAI-compatible adapters", "Bulut Beyin Fişleri", "sağlayıcı", "Yedek zekâ", "api", "araç", "Profesyonel", "Kota"),
            ("GitHub/GitLab API (izinli)", "Kod Hosting Fişi", "GitHub/GitLab", "Issue/PR eli", "api", "araç", "Profesyonel", "Onaylı"),
            ("Telegram/Discord bot bridge (opsiyon)", "Mesaj Bot Köprüsü", "bot API", "Uzaktan emir (sıkı fren)", "api", "araç", "Çevik", "Sıkı onay"),
            ("Home Assistant REST", "Akıllı Ev Fişi", "HA", "Madde el kapısı (sonra)", "api", "araç", "Profesyonel", "İleri"),
            ("Weather/open data adapters", "Açık Veri Fişleri", "kamu API", "Güncel hava/veri", "api", "araç", "Beyefendi", "Açık"),
            ("Maps / geocode open", "Harita Fişi", "Nominatim vd.", "Konum", "api", "araç", "Beyefendi", "Açık nazik"),
            ("Payment APIs — KAPALI varsayılan", "Ödeme API (Kapalı)", "—", "Para eli peşin kapalı", "api", "fren", "Profesyonel", "Kapalı — evet ile"),
            ("Rate-limit & circuit breaker per connector", "Fiş Başı Kota/Kesici", "iç", "Bir fiş evi yakmasın", "api", "politika", "Profesyonel", "Kritik"),
            ("Mock/sandbox connector mode", "Sahte Fiş Modu", "iç", "Testte gerçek API yakma", "api", "mod", "Profesyonel", "İç"),
            ("Contract test per connector", "Fiş Sözleşme Testi", "açık", "Fiş bozulunca anla", "api", "araç", "Profesyonel", "Açık"),
            ("SBOM of connectors", "Fiş Envanteri", "Syft ruhu", "Hangi dış bağımlılık", "api", "audit", "Profesyonel", "İç"),
            ("Air-gap connector pack (USB)", "Hava Boşuğu Fiş Paketi", "iç", "Offline güncelle", "api", "araç", "Profesyonel", "İleri"),
        ],
    ),
    "13_FREN_ONAY_KIMLIK": (
        "13 FREN / ONAY / KİMLİK (eli ayağına dolaşmasın)",
        [
            ("Risk-tier approval UI", "Risk Onay Yüzü", "iç", "Tehlikeli işte sor", "fren", "UX", "Profesyonel", "Kritik"),
            ("Two-person rule (opsiyon)", "İki Kişi Kuralı", "iç", "Çok kritikte çift onay", "fren", "politika", "Profesyonel", "Opsiyon"),
            ("Capability tokens expire", "Süreli Yetki", "iç", "Jeton eskit", "fren", "araç", "Profesyonel", "Kritik"),
            ("Profile isolation locks", "Profil Kilitleri", "2.PLAN", "Mahrem karışmasın", "fren", "politika", "Profesyonel", "Çapraz"),
            ("Kill switch global", "Acil Durdur", "iç", "Tüm eller dursun", "fren", "araç", "Profesyonel", "Kritik"),
            ("Audit log append-only", "Denetim İzi", "iç", "Kim ne yaptı", "fren", "araç", "Profesyonel", "Kritik"),
            ("Policy-as-code OPA hooks", "Politika Kancaları", "OPA", "Kural kodda", "fren", "araç", "Profesyonel", "Açık"),
            ("Deny-by-default new tools", "Varsayılan Red", "iç", "Yeni el kapalı doğsun", "fren", "politika", "Profesyonel", "Kritik"),
            ("Explainability card (neden bu araç)", "Neden Bu El?", "iç", "Şeffaf profesyonel", "fren", "UX", "Beyefendi", "İç"),
            ("Safe vocabulary: no crime tools", "Suç Araç Yasağı", "iç", "Hırsızlık/exploit/izinsiz yok", "fren", "politika", "Profesyonel", "KİLİT — kritik"),
            ("Gentleman mode enforces politeness", "Beyefendi Zorunlu Naziklik", "iç", "Rate-limit/robots açık", "fren", "mod", "Beyefendi", "Kritik"),
            ("Professional mode enforces checklist", "Profesyonel Kontrol Listesi", "iç", "Test/diff/onay bitsin", "fren", "mod", "Profesyonel", "Kritik"),
            ("Agile mode enforces minimal steps", "Çevik Minimal Adım", "iç", "Gereksiz el oynamasın", "fren", "mod", "Çevik", "İç"),
            ("Session risk budget", "Oturum Risk Bütçesi", "iç", "Çok tehlikeli ardışık iş yok", "fren", "politika", "Profesyonel", "İç"),
            ("Anomaly detector (weird tool spam)", "Anomali Dedektörü", "iç", "Eli çıldırırsa kes", "fren", "araç", "Profesyonel", "İç"),
            ("Legal hold / evidence export", "Kanıt Dışa Aktar", "iç", "Gerekirse kayıt paketi", "fren", "araç", "Profesyonel", "İç"),
        ],
    ),
    "14_MODLAR_PRO_BEYEFENDI_CEVIK": (
        "14 KİMLİK MODLARI — Profesyonel · Beyefendi · Çevik (yasal)",
        [
            ("Mode switcher UX", "Mod Değiştirici", "iç", "Yerine göre kimlik", "mod", "UX", "hepsi", "Kritik"),
            ("PROFESSIONAL playbook", "Profesyonel Oyun Kitabı", "iç", "Cerrah: plan-test-diff-teslim", "mod", "playbook", "Profesyonel", "Kritik"),
            ("GENTLEMAN WEB playbook", "Beyefendi Web Oyun Kitabı", "iç", "Nazik, hızlı, izinli, iz bırakmayan", "mod", "playbook", "Beyefendi", "Kritik"),
            ("AGILE OPERATOR playbook", "Çevik Operatör Oyun Kitabı", "iç", "Az adım, isabet, sessiz — SUÇSUZ", "mod", "playbook", "Çevik", "Kritik — suç yok"),
            ("Auto mode suggest by intent", "Niyete Göre Mod Öner", "iç", "Kodda profesyonel; webde beyefendi", "mod", "araç", "hepsi", "İç"),
            ("Dress code: tone/TTS per mode", "Üslup / Ses Kodu", "TTS", "Kimlik duyulsun", "mod", "araç", "Beyefendi", "İç"),
            ("HUD color frame per mode", "Mod Renk Çerçevesi", "sahne", "Mimar hangi kimlikte görsün", "mod", "UX", "hepsi", "İç"),
            ("Forbidden actions matrix per mode", "Moda Göre Yasaklar", "iç", "Çevik bile kapalı eylemleri açmaz", "mod", "matris", "hepsi", "KİLİT"),
            ("Success criteria per mode", "Mod Başarı Ölçütü", "iç", "Profesyonelde test; beyefendide naziklik", "mod", "şema", "hepsi", "İç"),
            ("Mode audit trail", "Mod Denetim İzi", "iç", "Hangi kimlikle yaptı", "mod", "audit", "Profesyonel", "İç"),
            ("Escalation: agile→pro when risk↑", "Riskte Yükselt", "iç", "Tehlike artınca profesyonel", "mod", "politika", "Profesyonel", "İç"),
            ("De-escalation: pro→gentleman on web read", "Web Okumada Beyefendi", "iç", "Sadece okurken nazik gezgin", "mod", "politika", "Beyefendi", "İç"),
            ("Training examples set (eval)", "Mod Eğitim Örnekleri", "iç", "Kimlik sınavları", "mod", "eval", "hepsi", "İç"),
            ("Public promise card", "Kimlik Sözü Kartı", "iç", "Rüzgar neyin efendisi / neyin düşmanı", "mod", "metin", "Beyefendi", "İç — Mimar"),
            ("No-mask rule: never pretend crime", "Maske Yasağı", "iç", "Hırsız rolü yok; çevik metafor yasal kalır", "mod", "politika", "Profesyonel", "KİLİT"),
            ("Guest mode (restricted tools)", "Misafir Modu", "iç", "Dar el seti", "mod", "mod", "Profesyonel", "İç"),
        ],
    ),
    "15_GOZLEM_RAPOR": (
        "15 GÖZLEM / RAPOR / SABAH BRİFİNG",
        [
            ("Live tool timeline HUD", "Canlı El Zaman Çizelgesi", "iç", "Ne yapıyor şimdi", "gözlem", "UX", "Profesyonel", "Kritik"),
            ("Morning briefing generator", "Sabah Brifing", "2.PLAN", "Üç ip + indeks durumu", "gözlem", "araç", "Beyefendi", "Kritik"),
            ("Night shift report", "Gece Vardiya Raporu", "kuyruk", "Ne bitti / ne takıldı", "gözlem", "araç", "Profesyonel", "Kritik"),
            ("KPI: success rate / retries", "Başarı KPI", "iç", "El kalitesi", "gözlem", "metrik", "Profesyonel", "İç"),
            ("Quota burn dashboard", "Kota Yanma Panosu", "iç", "Bulut/web harcama", "gözlem", "UX", "Beyefendi", "Kritik"),
            ("Disk / RAG health", "Disk / RAG Sağlık", "iç", "2TB'ye giden yol", "gözlem", "araç", "Profesyonel", "Kritik"),
            ("Alert rules (Prometheus ruhu)", "Alarm Kuralları", "açık", "Bozulunca seslen", "gözlem", "docs", "Profesyonel", "Açık"),
            ("Postmortem template", "Olay Sonrası Şablon", "SRE", "Neden oldu öğren", "gözlem", "şablon", "Profesyonel", "Açık"),
            ("User-facing plain status", "Sade Durum Cümlesi", "iç", "Mimar anlasın", "gözlem", "UX", "Beyefendi", "İç"),
            ("Export weekly digest", "Haftalık Özet", "iç", "Ne öğrendik / ne yaptık", "gözlem", "araç", "Beyefendi", "İç"),
            ("Silence / Do-not-disturb", "Sessizlik Modu", "iç", "Gereksiz bildirim yok", "gözlem", "mod", "Beyefendi", "İç"),
            ("Trace id across tools", "İz Kimliği", "OTel ruhu", "Bir işin tüm elleri bağlı", "gözlem", "araç", "Profesyonel", "Açık"),
            ("Anomaly weekly review", "Haftalık Anomali", "iç", "Garip el hareketleri", "gözlem", "araç", "Profesyonel", "İç"),
            ("SLA to Mimar (isteğe)", "Mimar SLA", "iç", "Kaç dk içinde rapor", "gözlem", "politika", "Profesyonel", "İç"),
            ("Voice status read aloud", "Sesli Durum", "TTS", "Eller serbest nabız", "gözlem", "araç", "Beyefendi", "Açık"),
            ("Red/green scene ambient", "Sahne Nabız Rengi", "sahne", "Uzaktan sağlık hissi", "gözlem", "UX", "Beyefendi", "İç"),
        ],
    ),
    "16_ORGAN_FABRIKA": (
        "16 ORGAN FABRİKASI (yeni el üreten el)",
        [
            ("Tool scaffold generator", "Araç İskeleti Üretici", "iç", "Yeni el taslağı", "fabrika", "araç", "Profesyonel", "Kritik"),
            ("From OpenAPI generate tool", "OpenAPI→El", "açık", "Fişten el", "fabrika", "araç", "Çevik", "Kritik"),
            ("From example dialogue mine tool", "Diyalogdan El Çıkar", "iç", "Sık işi araca çevir", "fabrika", "araç", "Çevik", "İç"),
            ("Unit+contract test scaffold", "Test İskeleti", "pytest", "Yalansız organ", "fabrika", "araç", "Profesyonel", "Kritik"),
            ("Sandbox trial run", "Deneme Koşumu", "sandbox", "Önce kafeste dene", "fabrika", "araç", "Profesyonel", "Kritik"),
            ("Register to catalog + risk class", "Sicile Yaz + Risk", "katalog", "Yeni el kayıtlı doğsun", "fabrika", "araç", "Profesyonel", "Kritik"),
            ("Docs auto card (TR/AR)", "Otomatik Araç Kartı", "iç", "Keşfedilsin", "fabrika", "araç", "Beyefendi", "İç"),
            ("Canary release tool", "Kanarya Sürüm", "iç", "Az riskle aç", "fabrika", "politika", "Profesyonel", "İç"),
            ("Rollback organ", "Organ Geri Al", "iç", "Bozuk el düşür", "fabrika", "araç", "Profesyonel", "İç"),
            ("Nightly organ ideas queue", "Gece Organ Fikirleri", "kuyruk", "Eksik alet öner", "fabrika", "kuyruk", "Çevik", "İç"),
            ("Mimar approval gate for new organs", "Yeni Organ Onayı", "iç", "İzinsiz el doğmasın", "fabrika", "fren", "Profesyonel", "Kritik"),
            ("Security review checklist", "Güvenlik Kontrol Listesi", "OWASP ruhu", "Organ güvenli", "fabrika", "şablon", "Profesyonel", "Açık"),
            ("Performance budget for organ", "Organ Performans Bütçesi", "iç", "Yavaş el olmasın", "fabrika", "politika", "Profesyonel", "İç"),
            ("Share organ pack (signed)", "İmzalı Organ Paketi", "iç", "Başka Rüzgar evine taşı", "fabrika", "araç", "Profesyonel", "İleri"),
            ("Self-heal flaky organ", "Organ Onarım", "iç", "Kırılgan eli düzelt", "fabrika", "araç", "Çevik", "İç"),
            ("Forbidden organ templates list", "Yasak Organ Şablonları", "iç", "Suç/exploit şablon yok", "fabrika", "politika", "Profesyonel", "KİLİT"),
        ],
    ),
    "17_COKLU_AJAN": (
        "17 ÇOKLU AJAN ORKESTRASI",
        [
            ("Role agents: researcher/writer/coder/critic", "Rol Ajanları", "açık", "İş bölümü", "orkestra", "mimari", "Profesyonel", "Kritik"),
            ("Blackboard / shared memory", "Ortak Tahta", "açık", "Ajanlar paylaşsın", "orkestra", "şema", "Profesyonel", "Açık"),
            ("Arbiter / judge agent", "Hakem Ajan", "iç", "Çatışmada karar", "orkestra", "araç", "Profesyonel", "İç"),
            ("Researcher gentleman web agent", "Araştırmacı Beyefendi", "tarayıcı", "Nazik bilgi topla", "orkestra", "ajan", "Beyefendi", "Kritik"),
            ("Coder professional agent", "Kodcu Profesyonel", "git/terminal", "Cerrah kod", "orkestra", "ajan", "Profesyonel", "Kritik"),
            ("Librarian index agent", "Kütüphaneci Ajan", "RAG", "İndeks/takip", "orkestra", "ajan", "Profesyonel", "Kritik"),
            ("Director scene agent", "Yönetmen Ajan", "sahne", "Tiyatro komutu", "orkestra", "ajan", "Beyefendi", "İç"),
            ("Security sentinel agent", "Nöbetçi Fren Ajan", "fren", "Tehlikeli çağrıda kes", "orkestra", "ajan", "Profesyonel", "Kritik"),
            ("Scheduler / queue boss", "Kuyruk Şefi", "gece", "Gece vardiyası", "orkestra", "ajan", "Profesyonel", "Kritik"),
            ("Message bus between agents", "Ajan Otobüsü", "NATS ruhu", "Konuşsunlar", "orkestra", "araç", "Profesyonel", "Açık"),
            ("Conflict of interest rules", "Çıkar Çatışması Kuralları", "iç", "Ajanlar birbirini ezmesin", "orkestra", "politika", "Profesyonel", "İç"),
            ("Budget per agent", "Ajan Bütçesi", "iç", "Biri kotayı bitirmesin", "orkestra", "politika", "Beyefendi", "İç"),
            ("Human chair (Mimar) always above", "Mimar Başkan", "iç", "Son söz sizde", "orkestra", "politika", "Profesyonel", "Kritik"),
            ("Simulation / tabletop exercise", "Masaüstü Tatbikat", "iç", "Felaket tatbikatı", "orkestra", "eval", "Profesyonel", "İç"),
            ("Agent genealogy / who spawned whom", "Ajan Soy Ağacı", "iç", "Denetim", "orkestra", "audit", "Profesyonel", "İç"),
            ("Idle park / wake policy", "Uyku / Uyanma", "iç", "Gereksiz ajan çalışmasın", "orkestra", "politika", "Çevik", "İç"),
        ],
    ),
    "18_DIS_DUNYA_EV": (
        "18 DIŞ DÜNYA / EV FİŞLERİ (ileri madde eli — kapılı doğar)",
        [
            ("Home Assistant scenes tool", "Ev Sahnesi Eli", "HA", "Işık/ısı (onaylı)", "ev", "araç", "Profesyonel", "İleri — onay"),
            ("ESP/serial bridge", "Seri / ESP Köprüsü", "ESP-IDF", "Gömülü el", "ev", "araç", "Profesyonel", "İleri"),
            ("Camera doorbell intake (yasal)", "Kapı Kamerası (yasal)", "yerel NVR", "Görüntü içeri (mahrem)", "ev", "araç", "Beyefendi", "Mahrem"),
            ("Backup NAS sync", "NAS Yedek Sync", "Syncthing/restic", "Ev yedek", "ev", "araç", "Profesyonel", "Açık"),
            ("UPS / power event hook", "Güç Olayı", "OS", "Kesilince güvenli kapat", "ev", "araç", "Profesyonel", "Opsiyon"),
            ("Printer/3D print queue (onay)", "3D Baskı Kuyruğu", "açık", "Madde üretim (onay)", "ev", "araç", "Profesyonel", "Onay"),
            ("Robot/ROS bridge (sonra)", "Robot Köprüsü", "ROS2", "Madde el ileri", "ev", "araç", "Profesyonel", "Çok sonra"),
            ("Guest Wi-Fi info card (local)", "Misafir Ağ Kartı", "iç", "Beyefendi ev sahipliği", "ev", "UX", "Beyefendi", "İç"),
            ("Physical panic button hook", "Fiziksel Panik Tuşu", "GPIO/HA", "Acil durdur", "ev", "fren", "Profesyonel", "İleri"),
            ("Air-quality / sensor log", "Sensör Günlüğü", "HA", "Ev nabzı", "ev", "araç", "Beyefendi", "Opsiyon"),
            ("Delivery locker / QR guest (opsiyon)", "Misafir QR", "iç", "Kapı protokolü", "ev", "araç", "Beyefendi", "Opsiyon"),
            ("Default DENY all physical actuators", "Fiziksel Varsayılan KAPALI", "iç", "Madde eli peşin kapalı", "ev", "politika", "Profesyonel", "KİLİT"),
            ("Safety interlock matrix", "Emniyet Kilidi Matrisi", "iç", "Tehlikeli cihaz kombosu yok", "ev", "fren", "Profesyonel", "Kritik"),
            ("Maintenance mode", "Bakım Modu", "iç", "Ev elleri uyusun", "ev", "mod", "Profesyonel", "İç"),
            ("Inventory of IoT devices", "IoT Envanteri", "iç", "Ne bağlı bil", "ev", "audit", "Profesyonel", "İç"),
            ("Ethical home AI charter", "Ev YZ Sözleşmesi", "iç", "Mahrem/aile kuralları", "ev", "metin", "Beyefendi", "İç — Mimar"),
        ],
    ),
    "19_SAVUNMA_ELI": (
        "19 SAVUNMA ELİ (saldırı PoC yok — koruma)",
        [
            ("Dependency CVE scan", "CVE Tarama", "Grype", "Zehirli paket", "savunma", "araç", "Profesyonel", "Açık"),
            ("Secret leak scan", "Sır Sızıntı Tarama", "açık", "Anahtar avı (kendi repoda)", "savunma", "araç", "Profesyonel", "Açık"),
            ("Phishing URL check (list)", "Oltalama URL Kontrol", "açık listeler", "Tuzak link", "savunma", "araç", "Beyefendi", "Açık"),
            ("Permission review weekly", "Haftalık İzin Gözden Geçir", "iç", "Gereksiz yetki kes", "savunma", "araç", "Profesyonel", "İç"),
            ("Backup restore drill", "Yedek Dönüş Tatbikatı", "restic", "Felakette dön", "savunma", "araç", "Profesyonel", "Kritik"),
            ("Integrity monitor (hash tripwire)", "Bütünlük Tel Örgü", "iç", "Dosya değişti uyar", "savunma", "araç", "Profesyonel", "İç"),
            ("Network allowlist audit", "Ağ İzin Denetimi", "iç", "Kapılar kapalı mı", "savunma", "audit", "Profesyonel", "İç"),
            ("Update channel verify signatures", "İmzalı Güncelleme", "açık", "Sahte güncelleme yok", "savunma", "araç", "Profesyonel", "Açık"),
            ("Incident playbook runner", "Olay Oyun Kitabı", "CISA ruhu", "Krizde adım adım", "savunma", "araç", "Profesyonel", "Açık"),
            ("No offensive toolkit policy", "Saldırı Seti Yasağı", "iç", "Exploit/hırsızlık aracı yok", "savunma", "politika", "Profesyonel", "KİLİT"),
            ("Hardening checklist Electron/OS", "Sıkılaştırma Listesi", "Electron/OWASP", "Yüzey daralt", "savunma", "şablon", "Profesyonel", "Açık"),
            ("Ransomware hygiene (backup+deny)", "Fidye Hijyeni", "açık", "Yedek+çalıştırma freni", "savunma", "politika", "Profesyonel", "Açık"),
            ("Privacy dashboard", "Mahremiyet Panosu", "iç", "Ne toplanıyor", "savunma", "UX", "Beyefendi", "İç"),
            ("Threat model refresh tool", "Tehdit Model Yenile", "STRIDE", "Periyodik bak", "savunma", "araç", "Profesyonel", "Açık"),
            ("Red-team request = DENY+explain", "Kırmızı Takım İsteği Reddi", "iç", "Saldırı tarifi yok; savunma öner", "savunma", "politika", "Profesyonel", "KİLİT"),
            ("Secure coding gate in organ factory", "Organ Güvenlik Kapısı", "fabrika", "Güvensiz organ doğmasın", "savunma", "fren", "Profesyonel", "Kritik"),
        ],
    ),
    "20_YALANSIZ_OLDU_EVAL": (
        "20 YALANSIZ OLDU — EVAL / KANIT",
        [
            ("End-to-end task suite", "Uçtan Uca Görev Seti", "iç", "Gerçek iş sınavları", "eval", "suite", "Profesyonel", "Kritik"),
            ("Tool-call trace assertions", "Araç İzi Doğrulama", "iç", "Doğru el çağrıldı mı", "eval", "araç", "Profesyonel", "Kritik"),
            ("Diff-based success", "Diff ile Başarı", "git/fs", "Dosya gerçekten değişti mi", "eval", "araç", "Profesyonel", "Kritik"),
            ("Browser golden paths", "Tarayıcı Altın Yollar", "Playwright", "Beyefendi gezinti sınavı", "eval", "suite", "Beyefendi", "Kritik"),
            ("Library ingest+index golden", "Kütüphane Altın Yol", "RAG", "İndir-indeks-takip sınavı", "eval", "suite", "Profesyonel", "Kritik"),
            ("Quota/fallback simulation", "Kota Simülasyonu", "iç", "Bulut bitince ne olur", "eval", "suite", "Beyefendi", "İç"),
            ("Safety refusal suite", "Reddetme Sınavı", "iç", "Yasak işi reddediyor mu", "eval", "suite", "Profesyonel", "Kritik"),
            ("Mode compliance suite", "Mod Uyum Sınavı", "iç", "Kimlik sözünü tutuyor mu", "eval", "suite", "hepsi", "Kritik"),
            ("Latency budgets", "Gecikme Bütçeleri", "iç", "Çevik kalsın", "eval", "metrik", "Çevik", "İç"),
            ("Hallucination vs citation score", "Uydurma / Alıntı Skoru", "RAGAS ruhu", "Kaynaklı mı", "eval", "metrik", "Profesyonel", "Açık"),
            ("Nightly CI for agent", "Ajan Gece CI", "kuyruk", "Her gece sınav", "eval", "kuyruk", "Profesyonel", "Kritik"),
            ("Scoreboard HUD", "Skor Panosu", "sahne", "Mimar görsün", "eval", "UX", "Beyefendi", "İç"),
            ("Regressions quarantine", "Regresyon Karantinası", "iç", "Bozulan senaryoyu kilitle", "eval", "araç", "Profesyonel", "İç"),
            ("Human rating capture", "İnsan Puanı", "iç", "Ümit abi notu", "eval", "araç", "Beyefendi", "İç"),
            ("Release gate: eval green", "Sürüm Kapısı", "iç", "Kırmızıysa çıkış yok", "eval", "fren", "Profesyonel", "Kritik"),
            ("Public honesty: say fail", "Dürüst Başarısızlık", "iç", "Oldu demeden oldu de", "eval", "politika", "Profesyonel", "Kritik"),
            ("Chaos monkey safe (own sandbox)", "Kendi Sandbox Kaos", "iç", "Kendi kafesinde kırılganlığı bul", "eval", "suite", "Profesyonel", "Exploit yok"),
            ("Gentleman politeness score", "Naziklik Skoru", "iç", "Beyefendi sınav metriği", "eval", "metrik", "Beyefendi", "Kritik"),
            ("Agile step-count score", "Adım Sayısı Skoru", "iç", "Gereksiz el oyunu cezası", "eval", "metrik", "Çevik", "İç"),
            ("Mimar trust ledger", "Güven Defteri", "iç", "Ümit abi güven puanı birikir", "eval", "şema", "Profesyonel", "İç — kritik"),
        ],
    ),
    "21_DIPLOMASI_MUZAKERE": (
        "21 DİPLOMASİ / MÜZAKERE / TON (beyefendi dış dünya)",
        [
            ("Intent soften / harden dial", "Sertlik-Yumuşaklık Kadranı", "iç", "Yerine göre ton", "diplomasi", "araç", "Beyefendi", "Kritik"),
            ("Stakeholder map tool", "Paydaş Haritası", "iç", "Kime ne söylenir", "diplomasi", "araç", "Profesyonel", "İç"),
            ("Negotiation brief builder", "Müzakere Brifingi", "iç", "Önce hedef/kırmızı çizgi", "diplomasi", "araç", "Profesyonel", "İç"),
            ("Apology / repair script", "Özür / Onarım", "iç", "Hata sonrası beyefendi", "diplomasi", "şablon", "Beyefendi", "İç"),
            ("Refuse without insult", "Kırmadan Red", "iç", "Yasak işi nazikçe reddet", "diplomasi", "politika", "Beyefendi", "Kritik"),
            ("Escalate to Mimar card", "Mimara Devret Kartı", "iç", "Ben karar vermemeliyim deme", "diplomasi", "UX", "Profesyonel", "Kritik"),
            ("Multi-party thread summarizer", "Çok Taraflı Özet", "iç", "Karma konuşmayı netleştir", "diplomasi", "araç", "Çevik", "İç"),
            ("Cultural etiquette packs TR-AR-EN", "Kültür Adabı Paketi", "iç", "Hitap/selam/üsul", "diplomasi", "paket", "Beyefendi", "Kritik"),
            ("Conflict de-escalation playbook", "Gerilim Düşürme", "iç", "Kavga büyütme", "diplomasi", "playbook", "Beyefendi", "İç"),
            ("Promise tracker (said→done)", "Söz Takibi", "iç", "Söz verdiysen bitir", "diplomasi", "araç", "Profesyonel", "Kritik"),
            ("Silence as tool (when not to speak)", "Sessizlik Eli", "iç", "Her şeye cevap yok", "diplomasi", "politika", "Beyefendi", "İç"),
            ("Public vs private channel router", "Açık/Kapalı Kanal", "iç", "Mahremi yanlış yere yazma", "diplomasi", "araç", "Profesyonel", "Kritik"),
            ("Draft→review→send gate (mail/social)", "Taslak-Gözden-Gönder", "ofis", "Acele gönderim yok", "diplomasi", "fren", "Profesyonel", "Kritik"),
            ("Reputation risk scorer", "İtibar Risk Skoru", "iç", "Bu yazı zarar verir mi", "diplomasi", "araç", "Beyefendi", "İç"),
            ("Guest / family mode tone", "Misafir-Aile Tonu", "iç", "Ev içi nezaket", "diplomasi", "mod", "Beyefendi", "İç"),
            ("Crisis comms template", "Kriz İletişim Şablonu", "iç", "Felakette sakin dil", "diplomasi", "şablon", "Profesyonel", "İç"),
            ("Thank-you / gratitude ledger", "Teşekkür Defteri", "iç", "İyiliği unutma", "diplomasi", "araç", "Beyefendi", "İç"),
            ("No-manipulation rule", "Manipülasyon Yasağı", "iç", "Kandırma/psikolojik tuzak yok", "diplomasi", "politika", "Profesyonel", "KİLİT"),
            ("Translate intent not just words", "Niyet Tercümesi", "MT+iç", "Kelime değil mana köprüsü", "diplomasi", "araç", "Beyefendi", "Kritik"),
            ("Audience-aware rewrite", "Dinleyiciye Göre Yaz", "iç", "Çocuk/usta/avam dili", "diplomasi", "araç", "Çevik", "İç"),
            ("Meeting chair agenda tool", "Toplantı Başkan Gündem", "ofis", "Dağılmadan yönet", "diplomasi", "araç", "Profesyonel", "İç"),
            ("Boundary setter (zaman/kapsam)", "Sınır Koyucu", "iç", "Kapsam şişmesin", "diplomasi", "araç", "Profesyonel", "İç"),
        ],
    ),
    "22_ZAMAN_DUNYA_MODEL": (
        "22 ZAMAN / DÜNYA MODELİ (unutmayan operatör)",
        [
            ("Personal world model store", "Kişisel Dünya Modeli", "iç", "Kim/ne/nerede canlı tut", "zaman", "şema", "Profesyonel", "Kritik"),
            ("Deadline graph + critical path", "Son Tarih Grafı", "iç", "Ne önce bitmeli", "zaman", "araç", "Profesyonel", "Kritik"),
            ("Habit / ritual scheduler", "Alışkanlık / Ritüel", "iç", "Sabah brifing ritmi", "zaman", "araç", "Beyefendi", "İç"),
            ("Timezone-aware planner", "Saat Dilimi Planlayıcı", "açık", "Dünya ile uyum", "zaman", "araç", "Beyefendi", "Açık"),
            ("Seasonal / liturgical calendar hooks", "Mevsim / Takvim Kancası", "iç", "Kültür zamanı (Ramadan vb.)", "zaman", "araç", "Beyefendi", "İç — dikkat"),
            ("Energy budget (CPU/GPU/insan)", "Enerji Bütçesi", "iç", "Gece ağır, gündüz çevik", "zaman", "politika", "Çevik", "İç"),
            ("Procrastination detector", "Erteleme Dedektörü", "iç", "İş sürüncemede uyarı", "zaman", "araç", "Profesyonel", "İç"),
            ("Context restore after sleep", "Uyku Sonrası Bağlam", "iç", "Kalınan yerden devam", "zaman", "araç", "Çevik", "Kritik"),
            ("Long-horizon project boards", "Uzun Ufuk Panosu", "masa", "Aylar süren iş", "zaman", "UX", "Profesyonel", "İç"),
            ("Anniversary / promise reminders", "Yıldönümü / Söz Hatırlat", "hatırlatıcı", "İnsanî bellek", "zaman", "araç", "Beyefendi", "İç"),
            ("Work/rest cadence (pomodoro+)", "Çalış-Dinlen Ritmi", "iç", "Yanma yok", "zaman", "mod", "Beyefendi", "İç"),
            ("Event bus: time triggers tools", "Zaman Tetikli Eller", "kuyruk", "Saat gelince iş", "zaman", "araç", "Profesyonel", "Kritik"),
            ("Stale task composting", "Bayat İş Kompostu", "iç", "Ölü işleri göm/arşivle", "zaman", "politika", "Çevik", "İç"),
            ("World-change journal (what changed)", "Dünya Değişim Günlüğü", "iç", "Dün→bugün fark", "zaman", "araç", "Profesyonel", "İç"),
            ("Travel / away mode", "Yolda / Uzakta Modu", "iç", "Düşük el, yüksek özet", "zaman", "mod", "Beyefendi", "İç"),
            ("Sync with external calendars (onaylı)", "Takvim Senkron", "CalDAV", "Çift takvim yok", "zaman", "araç", "Profesyonel", "Onay"),
            ("Countdown to release gates", "Sürüm Kapısı Geri Sayım", "eval", "Yeşil olmadan çıkma", "zaman", "araç", "Profesyonel", "Kritik"),
            ("Nightly dream queue (safe ideas)", "Gece Fikir Kuyruğu", "fabrika", "Gündüz onaylanacak fikirler", "zaman", "kuyruk", "Çevik", "İç"),
            ("Aging of permissions", "İzin Yaşlanması", "fren", "Eski yetki solsun", "zaman", "politika", "Profesyonel", "Kritik"),
            ("Historical replay of a day", "Gün Replay", "transcript", "O gün ne oldu", "zaman", "araç", "Profesyonel", "İç"),
            ("Priority iron triangle UI", "Öncelik Üçgeni", "UX", "hız×kalite×kapsam", "zaman", "UX", "Profesyonel", "İç"),
            ("Do-not-schedule sacred slots", "Kutsal Zaman Dilimleri", "iç", "Aile/ibadet/uyku dokunulmaz", "zaman", "politika", "Beyefendi", "İç — Mimar"),
        ],
    ),
    "23_OGRETMEN_USTA_DONGU": (
        "23 ÖĞRETMEN / USTA DÖNGÜSÜ (Ümit abi öğretir → kalıcı olur)",
        [
            ("Teach capture (hatırla→shelf)", "Öğret Yakalama", "hafıza", "«hatırla» kalıcı", "usta", "araç", "Profesyonel", "Kritik"),
            ("Correction → rule miner", "Düzelt→Kural", "iç", "Azarlama kurala dönsün", "usta", "araç", "Profesyonel", "Kritik"),
            ("Socratic quiz back to Mimar", "Sokratik Geri Soru", "iç", "Anladım mı doğrula", "usta", "araç", "Beyefendi", "İç"),
            ("Curriculum path per skill", "Beceri Müfredatı", "iç", "El becerisi basamak", "usta", "şema", "Profesyonel", "İç"),
            ("Apprentice / journeyman / master gates", "Çırak-Kalfa-Usta Kapıları", "eval", "El yetkinlik seviyesi", "usta", "fren", "Profesyonel", "Kritik"),
            ("Mistake museum (what we learned)", "Hata Müzesi", "iç", "Aynı hatayı iki kez yapma", "usta", "arşiv", "Profesyonel", "İç"),
            ("Show-your-work mode for teaching", "İşini Göster Modu", "iç", "Nasıl yaptığını öğret", "usta", "mod", "Beyefendi", "İç"),
            ("Flashcard / spaced repetition for facts", "Aralıklı Tekrar", "Anki ruhu", "Künye/kaide unutulmasın", "usta", "araç", "Profesyonel", "Açık"),
            ("Pair-work: Mimar drives, Rüzgar assists", "Çift Sürüş", "iç", "Siz direksiyon, ben alet", "usta", "mod", "Profesyonel", "Kritik"),
            ("Invert: Rüzgar drafts, Mimar grades", "Taslak→Not", "eval", "Güven defteri besler", "usta", "mod", "Profesyonel", "İç"),
            ("Domain mentor agents (fıkıh/kod/sahne)", "Alan Mentor Ajanları", "orkestra", "Her dalda usta sesi", "usta", "ajan", "Profesyonel", "İç"),
            ("Citation-first teaching", "Alıntılı Öğretiş", "RAG", "Uydurma ders yok", "usta", "politika", "Profesyonel", "Kritik"),
            ("Skill gap report weekly", "Beceri Boşluğu Raporu", "gözlem", "Nerede zayıfız", "usta", "araç", "Beyefendi", "İç"),
            ("Safe experiment lab for learners", "Öğrenci Labı", "sandbox", "Kırarak öğren (kafeste)", "usta", "araç", "Çevik", "İç"),
            ("Glossary / istilâh builder", "Istılah Sözlüğü", "iç", "Terim birliği", "usta", "araç", "Profesyonel", "İç"),
            ("Oral tradition mode (sesli ders)", "Sözlü Gelenek Modu", "TTS/STT", "Dinleyerek öğren", "usta", "mod", "Beyefendi", "Açık"),
            ("Exam generator from shelf", "Raftan Sınav", "RAG+eval", "Kütüphane canlı sınav", "usta", "araç", "Profesyonel", "Kritik"),
            ("No-cheat: refuse exam answers when locked", "Sınav Kilit Reddi", "fren", "Hile yok (Mimar kilidi)", "usta", "politika", "Profesyonel", "İç"),
            ("Mastery badge → unlock tools", "Ustalık Rozeti→El Aç", "katalog", "Yetkin olmadan tehlikeli el yok", "usta", "fren", "Profesyonel", "Kritik"),
            ("Teach-back to library (yaz→indeks)", "Öğret→Kütüphane", "kütüphane", "Yeni bilgi rafa", "usta", "araç", "Profesyonel", "Kritik"),
            ("Patience dial (yavaş anlat)", "Sabır Kadranı", "TTS", "Acele etmeden anlat", "usta", "mod", "Beyefendi", "İç"),
            ("Respect: never shame the learner", "Utandırmama Kuralı", "diplomasi", "Sert ama kırıcı değil", "usta", "politika", "Beyefendi", "İç"),
        ],
    ),
    "24_EGEMENLIK_HAVA_BOSLUGU": (
        "24 EGEMENLİK / HAVA BOŞLUĞU (kendi evinin efendisi)",
        [
            ("Local-first runtime charter", "Yerel-Önce Sözleşme", "Faz90", "Bulut dilenci değil", "egemen", "politika", "Profesyonel", "Kritik"),
            ("Air-gap update USB kit", "Hava Boşuğu USB Kiti", "iç", "Offline güncelle", "egemen", "araç", "Profesyonel", "İleri"),
            ("Model weight vault (Ollama)", "Ağırlık Kasası", "Ollama", "İyi model = yerel ağırlık", "egemen", "araç", "Profesyonel", "Kritik"),
            ("Key ceremony / rotate secrets", "Anahtar Töreni", "vault", "Sırlar yaşlanır", "egemen", "araç", "Profesyonel", "Kritik"),
            ("Vendor kill-switch (cloud off)", "Satıcı Kesici", "iç", "Bulutu tek tuş kapat", "egemen", "fren", "Profesyonel", "Kritik"),
            ("Data residency map", "Veri İkamet Haritası", "iç", "Veri nerede yatıyor", "egemen", "audit", "Profesyonel", "İç"),
            ("Offline encyclopedia pack", "Offline Ansiklopedi Paketi", "nebula/RAG", "İnetsiz bilge", "egemen", "paket", "Beyefendi", "Kritik"),
            ("Mirror of critical docs", "Kritik Docs Aynası", "2.PLAN", "Dış bağımlılık kırılınca yaşa", "egemen", "araç", "Profesyonel", "Çapraz"),
            ("Sovereign backup 3-2-1", "Egemen Yedek 3-2-1", "restic", "Felakette diril", "egemen", "araç", "Profesyonel", "Kritik"),
            ("Supply-chain pin (hashes)", "Tedarik Zinciri Pin", "SBOM", "Sahte paket yok", "egemen", "fren", "Profesyonel", "Açık"),
            ("No telemetry by default", "Varsayılan Telemetri Yok", "iç", "Evden dışarı sızma", "egemen", "politika", "Beyefendi", "Kritik"),
            ("Portable home directory", "Taşınır Ev Dizini", "iç", "PC değişince Rüzgar gelir", "egemen", "araç", "Profesyonel", "İç"),
            ("Hardware attest notes (TPM ops)", "Donanım Tanıklığı", "TPM opsiyon", "Cihaz güveni", "egemen", "not", "Profesyonel", "Opsiyon"),
            ("Graceful degrade matrix", "Zarif Düşüş Matrisi", "iç", "GPU/net yokken ne kalır", "egemen", "matris", "Çevik", "Kritik"),
            ("License freedom prefer FOSS", "Özgür Yazılım Tercihi", "SPDX", "Kilitli kapı azalsın", "egemen", "politika", "Profesyonel", "İç"),
            ("Nation/lang pack sovereignty TR", "TR Dil Egemenliği", "iç", "Türkçe birinci sınıf", "egemen", "politika", "Beyefendi", "İç"),
            ("Disaster island mode", "Ada Modu", "iç", "Sadece yerel el seti", "egemen", "mod", "Profesyonel", "Kritik"),
            ("Export entire brain (portable)", "Beyin Dışa Aktar", "iç", "Hafıza+katalog taşınır", "egemen", "araç", "Profesyonel", "İç"),
            ("Import brain with verify", "Beyin İçe + Doğrula", "hash", "Bozuk beyin alma", "egemen", "araç", "Profesyonel", "İç"),
            ("Cloud as guest not landlord", "Bulut Misafir", "kota", "Ev sahibi yerelde", "egemen", "politika", "Beyefendi", "Kritik"),
            ("Legal custody of family data", "Aile Verisi Vesayeti", "mahrem", "Çocuk/aile verisi kilit", "egemen", "politika", "Profesyonel", "Kritik"),
            ("Anti-lock-in connector abstraction", "Kilitlenme Karşıtı Soyutlama", "api", "Tek satıcıya mahkûm olma", "egemen", "mimari", "Profesyonel", "Kritik"),
        ],
    ),
    "25_ESTETIK_SAHNE_HUZUR": (
        "25 ESTETİK / SAHNE / HUZUR (varlık kalitesi)",
        [
            ("Presence director (nefes/pace)", "Varlık Yönetmeni", "sahne+TTS", "Acele etmeyen yüz", "estetik", "araç", "Beyefendi", "Kritik"),
            ("Room tone / ambient scenes", "Oda Tonu / Ambiyans", "sahne", "Huzur atmosferi", "estetik", "UX", "Beyefendi", "İç"),
            ("Typography / color discipline", "Tipografi / Renk Disiplini", "UI kilit", "Ucuz AI yüzü yok", "estetik", "politika", "Profesyonel", "Çapraz arayüz kilidi"),
            ("Gesture / idle animation taste", "Jest / Boşta Zarafet", "Godot", "Titreyen bot değil", "estetik", "araç", "Beyefendi", "İç"),
            ("Silence design (pauses)", "Sessizlik Tasarımı", "TTS", "Nefes alan konuşma", "estetik", "mod", "Beyefendi", "İç"),
            ("Celebration without spam", "Sade Kutlama", "UX", "İş bitince abartısız sevinç", "estetik", "UX", "Beyefendi", "İç"),
            ("Error beauty (honest + calm)", "Hata Güzelliği", "UX", "Kırmızı panik değil sakin dürüstlük", "estetik", "şablon", "Profesyonel", "İç"),
            ("Focus zen workspace layout", "Odak Zen Düzeni", "masa", "Dağınık dashboard yok", "estetik", "UX", "Beyefendi", "İç"),
            ("Soundscape etiquette", "Ses Peyzajı Adabı", "medya", "Gereksiz bip yok", "estetik", "politika", "Beyefendi", "İç"),
            ("Night theme circadian", "Gece Teması", "UI", "Gözü yorma", "estetik", "mod", "Beyefendi", "İç"),
            ("Craft checklist before show", "Gösteri Öncesi Zanaat", "masa", "Teslim kalitesi", "estetik", "şablon", "Profesyonel", "İç"),
            ("Avatar wardrobe / season", "Avatar Gardırop", "VRM", "Mevsime göre varlık", "estetik", "UX", "Beyefendi", "Opsiyon"),
            ("Spatial audio for scene", "Uzamsal Ses", "sahne", "Derinlik hissi", "estetik", "araç", "Beyefendi", "İleri"),
            ("Reduce motion accessibility", "Hareket Azalt", "a11y", "Herkes için huzur", "estetik", "politika", "Profesyonel", "Açık"),
            ("Museum mode (slow browse library)", "Müze Modu", "kütüphane", "Rafta yavaş gez", "estetik", "mod", "Beyefendi", "İç"),
            ("Poetry / hikmet interludes (opt-in)", "Hikmet Ara", "nebula", "İsteğe bağlı güzellik", "estetik", "mod", "Beyefendi", "Opt-in"),
            ("No-emoji-spam / no-cheap-glow", "Ucuz Süs Yasağı", "UI kural", "Marka zevki koru", "estetik", "politika", "Profesyonel", "İç"),
            ("Stage manager cue sheet", "Sahne Amiri İşaret", "sahne", "Işık/ses/metin senkron", "estetik", "araç", "Profesyonel", "İç"),
            ("Hospitality welcome ritual", "Misafir Karşılama", "diplomasi+sahne", "Eve gelen beyefendi", "estetik", "ritüel", "Beyefendi", "İç"),
            ("Clutter debt meter", "Dağınıklık Borcu", "gözlem", "UI/masa şişmesini ölç", "estetik", "metrik", "Çevik", "İç"),
            ("Beauty regression tests (screenshot)", "Güzellik Regresyonu", "Playwright", "Yüzü bozma", "estetik", "eval", "Profesyonel", "Kritik"),
            ("Huzur KPI (interrupt rate)", "Huzur KPI", "gözlem", "Ne kadar bölündük", "estetik", "metrik", "Beyefendi", "İç"),
        ],
    ),
    "26_EKONOMI_KOTA_DEGER": (
        "26 EKONOMİ / KOTA / DEĞER (israfsız güç)",
        [
            ("Unit economics per task", "Görev Birim Maliyeti", "iç", "Bu iş kaç token/dk", "ekonomi", "metrik", "Profesyonel", "Kritik"),
            ("Budget envelopes (gün/hafta)", "Bütçe Zarfı", "iç", "Aşınca yavaşla", "ekonomi", "politika", "Beyefendi", "Kritik"),
            ("Cheap-path planner", "Ucuz Yol Planlayıcı", "ajan", "Önce yerel/hafif el", "ekonomi", "araç", "Çevik", "Kritik"),
            ("Expensive-path justify card", "Pahalı Yol Gerekçe", "iç", "Neden bulut yaktın", "ekonomi", "UX", "Profesyonel", "İç"),
            ("Cache hit rate optimizer", "Önbellek İsabet", "web/RAG", "Tekrar yakma", "ekonomi", "araç", "Çevik", "İç"),
            ("Disk rent forecast", "Disk Kira Tahmini", "kütüphane", "GB başına değer", "ekonomi", "araç", "Profesyonel", "İç"),
            ("GPU queue auction (fair share)", "GPU Kuyruk Adaleti", "iç", "Kim ne zaman GPU", "ekonomi", "politika", "Profesyonel", "İç"),
            ("Value score: impact×urgency/cost", "Değer Skoru", "iç", "Önce yüksek değer", "ekonomi", "araç", "Profesyonel", "İç"),
            ("Waste report (failed retries)", "İsraf Raporu", "gözlem", "Boşa giden el", "ekonomi", "araç", "Profesyonel", "İç"),
            ("Subscription / API spend ledger", "Abonelik Defteri", "api", "Dış para takibi", "ekonomi", "audit", "Profesyonel", "İç"),
            ("Free-tier etiquette", "Ücretsiz Kota Adabı", "beyefendi", "Kota ezme", "ekonomi", "politika", "Beyefendi", "Kritik"),
            ("Batch night jobs for cost", "Gece Toplu İş", "kuyruk", "Ucuz saatte ağır iş", "ekonomi", "politika", "Çevik", "İç"),
            ("Stop-loss on runaway agent", "Ajan Zarar Kes", "fren", "Maliyet çılgınlığında kes", "ekonomi", "fren", "Profesyonel", "Kritik"),
            ("ROI of new organ proposal", "Yeni Organ ROI", "fabrika", "El değmeye değer mi", "ekonomi", "araç", "Profesyonel", "İç"),
            ("Shared family compute fairness", "Aile Paylaşım Adaleti", "iç", "Tek kişi evi yakmasın", "ekonomi", "politika", "Beyefendi", "İç"),
            ("Carbon / power awareness note", "Güç Farkındalığı", "iç", "Gereksiz GPU yakma", "ekonomi", "not", "Beyefendi", "İç"),
            ("Quote before big job", "Büyük İşte Teklif", "UX", "Önce maliyet söyle", "ekonomi", "fren", "Profesyonel", "Kritik"),
            ("Refund of attention (summarize)", "Dikkat İadesi", "özet", "Uzun iş→kısa özet", "ekonomi", "araç", "Çevik", "İç"),
            ("Sunk-cost abandon policy", "Batık Maliyet Terk", "iç", "Ölü projeyi bırak", "ekonomi", "politika", "Profesyonel", "İç"),
            ("Marketplace of internal tools cost tags", "İç Pazar Maliyet Etiketi", "katalog", "Her elin fiyatı", "ekonomi", "şema", "Profesyonel", "Kritik"),
            ("Graceful degrade to zero-cost mode", "Sıfır Maliyet Modu", "egemen", "Sadece yerel ücretsiz el", "ekonomi", "mod", "Çevik", "Kritik"),
            ("Mimar monthly economy brief", "Aylık Ekonomi Brifing", "gözlem", "Ne harcadık ne kazandık", "ekonomi", "araç", "Beyefendi", "İç"),
        ],
    ),
    "27_IKIZ_SIMULASYON": (
        "27 İKİZ / SİMÜLASYON (önce hayalde bitir, sonra gerçekte)",
        [
            ("Digital twin of workspace", "Çalışma Alanı İkizi", "iç", "Gerçek bozmadan dene", "ikiz", "mimari", "Profesyonel", "Kritik"),
            ("Dry-run universe switch", "Kuru Evren Anahtarı", "ajan", "Tüm eller sahte moda", "ikiz", "mod", "Profesyonel", "Kritik"),
            ("What-if planner", "Ya-Olursa Planlayıcı", "iç", "Senaryo ağacı", "ikiz", "araç", "Çevik", "İç"),
            ("Shadow mode (observe only)", "Gölge Modu", "ajan", "Yapmadan izle öğren", "ikiz", "mod", "Beyefendi", "Kritik"),
            ("Canary twin vs prod", "Kanarya İkiz", "eval", "Az trafikte dene", "ikiz", "politika", "Profesyonel", "İç"),
            ("Replay production trace safely", "Üretim İzini Güvenli Oynat", "transcript", "Dünü tekrarla", "ikiz", "araç", "Profesyonel", "İç"),
            ("Fault injection in sandbox only", "Sadece Sandbox Arıza", "eval", "Kırılganlığı bul", "ikiz", "suite", "Profesyonel", "Exploit yok"),
            ("Library twin (index without write)", "Kütüphane İkizi", "RAG", "İndeks denemesi yazmadan", "ikiz", "araç", "Profesyonel", "İç"),
            ("Browser twin with fixtures", "Tarayıcı İkizi", "Playwright", "Web sınavı sabit sayfa", "ikiz", "suite", "Beyefendi", "Kritik"),
            ("Home twin (HA mock)", "Ev İkizi", "HA mock", "Fiziksel el öncesi", "ikiz", "araç", "Profesyonel", "İleri"),
            ("Negotiation simulator", "Müzakere Simülatörü", "diplomasi", "Zor konuşmayı prova", "ikiz", "araç", "Beyefendi", "İç"),
            ("Time-accelerated night shift sim", "Hızlandırılmış Gece Sim", "zaman", "Uzun işi saniyede prova", "ikiz", "araç", "Çevik", "İç"),
            ("Promote sim→real checklist", "Sim→Gerçek Kontrol", "fren", "Hayalden gerçeğe kapı", "ikiz", "şablon", "Profesyonel", "Kritik"),
            ("Never confuse sim success with real", "Sim≠Gerçek Kuralı", "yalansız", "Sim yeşil gerçek kırmızı olabilir", "ikiz", "politika", "Profesyonel", "KİLİT"),
            ("Multi-agent war-game (tabletop)", "Masaüstü Harp Oyunu", "orkestra", "Felaket tatbikatı", "ikiz", "eval", "Profesyonel", "İç"),
            ("User-visible sim badge", "Sim Rozeti", "UX", "Mimar simde olduğunu bilsin", "ikiz", "UX", "Beyefendi", "Kritik"),
            ("Cost of sim vs real estimator", "Sim/Gerçek Maliyet", "ekonomi", "Prova ucuz kalsın", "ikiz", "araç", "Çevik", "İç"),
            ("Rollback after failed promotion", "Başarısız Terfi Geri Al", "fabrika", "Gerçeğe çıkan bozulursa geri", "ikiz", "araç", "Profesyonel", "İç"),
            ("Synthetic data generator (privacy-safe)", "Sentetik Veri", "iç", "Mahrem veri ile prova yok", "ikiz", "araç", "Profesyonel", "Kritik"),
            ("Twin diff: sim plan vs real outcome", "İkiz Diff", "gözlem", "Hayal-gerçek farkı öğren", "ikiz", "araç", "Profesyonel", "Kritik"),
            ("Permission: sim tools wider, real narrower", "Sim Geniş / Gerçek Dar", "fren", "Gerçekte daha sıkı", "ikiz", "politika", "Profesyonel", "Kritik"),
            ("Graduation ceremony when twin stable", "İkiz Mezuniyet", "eval", "Stabilse gerçek el aç", "ikiz", "ritüel", "Beyefendi", "İç"),
        ],
    ),
    "28_SON_DURUM_VIZYON": (
        "28 SON DURUM — 3.PLAN SONRASI RÜZGAR (hedef portre)",
        [
            ("Portrait: local scholar with hands", "Portre: Elli Yerel Âlim", "vizyon", "Kütüphane+ajan+eller birleşik", "son", "vizyon", "Profesyonel", "HEDEF"),
            ("Portrait: gentleman of the web", "Portre: Web Beyefendisi", "vizyon", "İzinli, nazik, hızlı gezgin", "son", "vizyon", "Beyefendi", "HEDEF"),
            ("Portrait: agile lawful operator", "Portre: Yasal Çevik Operatör", "vizyon", "Az adımda isabet — suçsuz", "son", "vizyon", "Çevik", "HEDEF"),
            ("Self-indexing library autonomic", "Kendi İndeksleyen Kütüphane", "07", "İndir-yerleştir-indeks-takip kendi", "son", "yetenek", "Profesyonel", "HEDEF"),
            ("Tool catalog living organism", "Canlı Araç Organizması", "02+16", "Eksik eli üretir, bozuk eli düşürür", "son", "yetenek", "Profesyonel", "HEDEF"),
            ("Masa as real work not theater", "Masa Gerçek İş", "09", "Belge/tablo/çizim/sunum ellere bağlı", "son", "yetenek", "Profesyonel", "HEDEF"),
            ("Cursor-grade coding sibling", "Cursor Kardeşi Kod", "08+04", "Repo anlar, yama atar, testler yeşil", "son", "yetenek", "Profesyonel", "HEDEF"),
            ("Night shift without babysitting", "Bebek Bakıcısız Gece", "15+07", "Takılınca kendi kaldırır, sabah rapor", "son", "yetenek", "Çevik", "HEDEF"),
            ("Quota-aware brain chain", "Kota Bilinçli Beyin", "Faz90", "Yerel→bulut nazik; bitince öğret sor", "son", "yetenek", "Beyefendi", "HEDEF"),
            ("Frictionless teach→memory→shelf", "Öğret→Hafıza→Raf Akışı", "23", "Ümit öğretti kalıcı organ olur", "son", "yetenek", "Profesyonel", "HEDEF"),
            ("Multi-agent under Mimar chair", "Mimar Başkanlı Orkestra", "17", "Roller çalışır, son söz sizde", "son", "yetenek", "Profesyonel", "HEDEF"),
            ("Default-deny physical world", "Fiziksel Dünya Kapalı", "18", "Madde eli onayla açılır", "son", "güven", "Profesyonel", "HEDEF"),
            ("Defense without offense", "Saldırısız Savunma", "19", "Korur; exploit öğretmez", "son", "güven", "Profesyonel", "HEDEF"),
            ("Yalansız oldu as culture", "Yalansız Oldu Kültürü", "20", "Oldu demeden oldu demez", "son", "kültür", "Profesyonel", "HEDEF"),
            ("Sovereign home AI", "Egemen Ev YZ", "24", "Veri evde, bulut misafir", "son", "kültür", "Beyefendi", "HEDEF"),
            ("Presence: calm professional face", "Sakin Profesyonel Yüz", "25", "Ucuz bot değil varlık", "son", "kültür", "Beyefendi", "HEDEF"),
            ("Economy: no waste of attention", "İsrafsız Dikkat", "26", "Pahalı eli boşuna yakmaz", "son", "kültür", "Çevik", "HEDEF"),
            ("Simulate before you touch", "Dokunmadan Önce Sim", "27", "Önce ikizde bitir", "son", "kültür", "Profesyonel", "HEDEF"),
            ("Diplomacy as first weapon", "İlk Silah Diplomasi", "21", "Kırmadan net; manipülasyon yok", "son", "kültür", "Beyefendi", "HEDEF"),
            ("Timeful: remembers world", "Zaman Bilinçli", "22", "Söz, tarih, ritüel unutulmaz", "son", "yetenek", "Beyefendi", "HEDEF"),
            ("Hands never tangle feet", "El Ayağa Dolanmaz", "13", "Fren+bütçe+onay omurgada", "son", "güven", "Profesyonel", "HEDEF"),
            ("After 3.PLAN: ready for life ops", "3.PLAN Sonrası: Hayat Operasyonu", "vizyon", "Planlar bitti → yaşayan operatör", "son", "milestone", "hepsi", "KAPI AÇILIR"),
            ("Not done: GPU scale / robot body", "Henüz Yok: GPU Ölçek / Robot", "not", "Donanım ve madde el sonra", "son", "sınır", "Profesyonel", "Dürüst sınır"),
            ("Not done: crime or gray-hat", "Asla Yok: Suç / Gri Şapka", "kilit", "Çevik ≠ hırsız; kapalı kalır", "son", "sınır", "Profesyonel", "KİLİT"),
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
        f"{title} — 3.PLAN+ v2 YÜKSELTME · {len(rows)} madde · "
        f"Kapı: Şamile + 1.PLAN + 2.PLAN+ bitince · "
        f"Modlar: Profesyonel / Beyefendi / Çevik(yasal) · suç/exploit YOK"
    )
    ws["A1"].font = Font(name="Calibri", size=12, bold=True, color="C00000")
    ws.merge_cells("A1:I1")
    hf = Font(name="Calibri", size=11, bold=True)
    fill = PatternFill("solid", fgColor="FCE4D6")
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
    for i, row in enumerate(rows, 1):
        for col, v in enumerate([i, *row], 1):
            cell = ws.cell(2 + i, col, v)
            cell.border = thin
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for i, w in enumerate([6, 46, 40, 28, 52, 12, 16, 16, 28], 1):
        ws.column_dimensions[chr(64 + i)].width = w
    ws.freeze_panes = "A3"
    ws.auto_filter.ref = f"A2:I{2 + len(rows)}"
    note = wb.create_sheet("NOT")
    note["A1"] = (
        "3.PLAN+ DIS_EL_ARAC_KATALOGU — v2 YÜKSELTME\n"
        "1.PLAN = Bilgisayar+Sahne eserleri.\n"
        "2.PLAN+ = Motor dalgaları + usta omurgası.\n"
        "3.PLAN+ = Dış el araç kataloğu (01–20 omurga + 21–28 üst katman).\n\n"
        "KİMLİKLER:\n"
        "· PROFESYONEL = cerrah hassasiyeti, test, diff, yalansız oldu.\n"
        "· BEYEFENDİ = web'de nazik, robots/rate-limit, izinli kapı, iz bırakmayan.\n"
        "· ÇEVİK = az adım, isabet, sessiz operatör — METAFOR; suç/hırsızlık/exploit YOK.\n\n"
        "Üst katman: diplomasi · zaman/dünya · öğretmen · egemenlik · estetik ·\n"
        "ekonomi · ikiz simülasyon · SON DURUM portresi (kat 28).\n\n"
        "Kapalı: izinsiz erişim, korsan, saldırı PoC, dolandırıcılık, gizlice veri çalma.\n"
        "Kapı: RAG + 1 + 2 bitmeden bu plana aksiyon yok.\n"
        "Kategorileri karıştırmayın."
    )
    note["A1"].alignment = Alignment(wrap_text=True)
    note.column_dimensions["A"].width = 110
    wb.save(path)
    return path


def main() -> int:
    if OUT_ROOT.exists():
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
    ws.append(["NO", "KLASÖR / KATEGORİ", "MADDE SAYISI", "DOSYA"])
    for i, r in enumerate(results, 1):
        ws.append([i, r["cat"], r["rows"], Path(r["path"]).name])
    ws.append([])
    ws.append(["PLAN", "3.PLAN+ DIS_EL_ARAC_KATALOGU v2 YUKSELTME"])
    ws.append(["ONCEKI", "1.PLAN bilgisayar/sahne · 2.PLAN+ motor/usta"])
    ws.append(["KAPI", "Samile RAG + 1.PLAN + 2.PLAN+ bitince"])
    ws.append(["MODLAR", "Profesyonel | Beyefendi gezgin | Cevik(yasal) — suc yok"])
    ws.append(["UST KATMAN", "21 diplomasi … 28 SON DURUM vizyon"])
    ws.append(["TOPLAM MADDE", total])
    ws.append(["KOK", str(OUT_ROOT)])
    ozet = OUT_ROOT / "00_OZET_3.PLAN+_DIS_EL_ARAC_KATALOGU.xlsx"
    wb.save(ozet)

    # 3.PLAN sonrası hedef portre (Mimar'a tek bakış)
    son = Workbook()
    sw = son.active
    sw.title = "SON_DURUM"
    sw["A1"] = (
        "3.PLAN SONRASI RÜZGAR — hedef portre (uygulama RAG+1+2+3 bitince). "
        "Suç/exploit yok; çevik = yasal metafor."
    )
    sw["A1"].font = Font(name="Calibri", size=12, bold=True, color="C00000")
    sw.merge_cells("A1:B1")
    for col, h in enumerate(["BOYUT", "SON DURUM"], 1):
        c = sw.cell(2, col, h)
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DDEBF7")
    portrait = [
        ("Kimlik", "Üç kıyafet: Profesyonel cerrah · Web beyefendisi · Yasal çevik operatör — yerinde giyer"),
        ("Beyin", "Local-first (hafıza→RAG→Ollama→bulut kota bilinçli); uydurmaz, alıntılar; bilmezse öğretir misin der"),
        ("Eller", "Sicilli araç organizması: dosya, terminal, tarayıcı, git, masa, medya, ofis, API — her el risk+frenli"),
        ("Kütüphane", "Otonom: indir→yerleştir→indeks→takip→rapor; gece vardiyası bebek bakıcısız"),
        ("Masa", "Belge/Tablo/Çizim/Sunum sözden gerçek iş; sahne tiyatro değil teslim"),
        ("Kod", "Cursor kardeşi: repo haritası, yama, test, commit onaylı; yalansız oldu kapısı"),
        ("Web", "Beyefendi: robots, rate-limit, allowlist, karantina; engelde bypass yok — Mimara sor"),
        ("Orkestra", "Araştırmacı/kodcu/kütüphaneci/nöbetçi ajanlar; başkan her zaman Mimar"),
        ("Öğrenme", "Ümit öğretti → kural/hafıza/raf; çırak-kalfa-usta kapısı olmadan tehlikeli el açılmaz"),
        ("Egemenlik", "Veri evde; bulut misafir; hava boşuğu/ada modu; telemetri varsayılan kapalı"),
        ("Güven", "Varsayılan red; kill switch; denetim izi; fiziksel dünya kapalı; saldırı seti yok"),
        ("Simülasyon", "Önce ikizde bitir, sonra gerçek; sim yeşili gerçek sanılmaz"),
        ("Huzur", "Sakin varlık, israfsız dikkat, diplomasi ilk silah, kutsal zaman dilimleri dokunulmaz"),
        ("Sınır (dürüst)", "GPU ölçek ve robot beden sonra; suç/gri şapka asla"),
        ("Milestone", "3.PLAN bitince plan rafı kapanır → yaşayan hayat operatörü başlar"),
    ]
    for i, (a, b) in enumerate(portrait, 1):
        sw.cell(2 + i, 1, a)
        sw.cell(2 + i, 2, b)
        sw.cell(2 + i, 1).alignment = Alignment(wrap_text=True, vertical="top")
        sw.cell(2 + i, 2).alignment = Alignment(wrap_text=True, vertical="top")
    sw.column_dimensions["A"].width = 22
    sw.column_dimensions["B"].width = 100
    sw.freeze_panes = "A3"
    # kat 28 satırlarını da ek sayfaya
    if "28_SON_DURUM_VIZYON" in CATS:
        title28, rows28 = CATS["28_SON_DURUM_VIZYON"]
        s2 = son.create_sheet("28_MADDELER")
        s2.append(HEADERS)
        for i, row in enumerate(rows28, 1):
            s2.append([i, *row])
        s2.freeze_panes = "A2"
    son_path = OUT_ROOT / "00_SON_DURUM_3.PLAN_SONRASI.xlsx"
    son.save(son_path)

    print(
        json.dumps(
            {
                "ok": True,
                "plan": "3.PLAN+ DIS_EL_ARAC_KATALOGU v2",
                "cats": len(results),
                "works": total,
                "by_cat": {r["cat"]: r["rows"] for r in results},
                "root": str(OUT_ROOT),
                "ozet": str(ozet),
                "son_durum": str(son_path),
                "commit_hint": "scripts/ruzgar_plan3_arac_katalog_excel.py",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
