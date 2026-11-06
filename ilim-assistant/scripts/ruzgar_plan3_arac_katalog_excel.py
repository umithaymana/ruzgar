#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""3.PLAN+ DIS_EL_ARAC_KATALOGU — Excel (Plan 2'den SONRA).

Kapı (kilit): Şamile RAG + 1.PLAN + 2.PLAN+ bitmeden aksiyon yok.
Amaç: Rüzgar'ın dışarıda eli ayağı dolaşmayan profesyonel araç yüzeyi.

KİMLİK MODLARI (Mimar hayali — yasal çerçeve):
  · PROFESYONEL — cerrah hassasiyeti; yalansız oldu; kurumsal disiplin
  · BEYEFENDİ GEZGİN — web'de nazik, hızlı, iz bırakmayan; robots/rate-limit;
    izinli kapıdan girer; çöp/kaba bot değil
  · ÇEVİK OPERATÖR — sessiz, isabetli, az adımda iş bitirir (metafor);
    SUÇ / izinsiz erişim / hırsızlık / exploit YOK — kapalı eylem

Çıktı:
  Desktop/.../3.PLAN+_DIS_EL_ARAC_KATALOGU/<KAT>/...
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
        f"{title} — 3.PLAN+ DIS_EL_ARAC_KATALOGU · {len(rows)} madde · "
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
        "3.PLAN+ DIS_EL_ARAC_KATALOGU\n"
        "1.PLAN = Bilgisayar+Sahne eserleri.\n"
        "2.PLAN+ = Motor dalgaları + usta omurgası.\n"
        "3.PLAN+ = Dış el araç kataloğu — Rüzgar'ın eli ayağına dolaşmasın.\n\n"
        "KİMLİKLER:\n"
        "· PROFESYONEL = cerrah hassasiyeti, test, diff, yalansız oldu.\n"
        "· BEYEFENDİ = web'de nazik, robots/rate-limit, izinli kapı, iz bırakmayan.\n"
        "· ÇEVİK = az adım, isabet, sessiz operatör — METAFOR; suç/hırsızlık/exploit YOK.\n\n"
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
    ws.append(["PLAN", "3.PLAN+ DIS_EL_ARAC_KATALOGU"])
    ws.append(["ONCEKI", "1.PLAN bilgisayar/sahne · 2.PLAN+ motor/usta"])
    ws.append(["KAPI", "Samile RAG + 1.PLAN + 2.PLAN+ bitince"])
    ws.append(["MODLAR", "Profesyonel | Beyefendi gezgin | Cevik(yasal) — suc yok"])
    ws.append(["TOPLAM MADDE", total])
    ws.append(["KOK", str(OUT_ROOT)])
    ozet = OUT_ROOT / "00_OZET_3.PLAN+_DIS_EL_ARAC_KATALOGU.xlsx"
    wb.save(ozet)
    print(
        json.dumps(
            {
                "ok": True,
                "plan": "3.PLAN+ DIS_EL_ARAC_KATALOGU",
                "cats": len(results),
                "works": total,
                "by_cat": {r["cat"]: r["rows"] for r in results},
                "root": str(OUT_ROOT),
                "ozet": str(ozet),
                "commit_hint": "scripts/ruzgar_plan3_arac_katalog_excel.py",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
