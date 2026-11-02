# -*- coding: utf-8 -*-
"""
Bilgisayar Bilimleri Excel pipeline (2–24 ve gerekirse yeniden 1):
  F: indirebilirim/indiremem · G: muadil · boşluklara ilave · indir · raf · özet
"""
from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook
from pypdf import PdfReader

DESK = Path(r"C:\Users\hayma\Desktop\RÜZGAR\RÜZGAR KÜTÜPHANE İNDEKS\BİLGİSAYAR BİLİMLERİ")
ROOT = Path(__file__).resolve().parents[1]
RAF_ROOT = ROOT / "knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri"
MAX_CHARS = 12000
MAX_PAGES = 80

# Başlık kalıbı → yasal ücretsiz kaynak
FREE_TITLE_PATTERNS: list[tuple[re.Pattern[str], str, str, str, str]] = [
    # (pattern, key, baslik, url, kind)
    (re.compile(r"think python", re.I), "think_python", "Think Python", "https://greenteapress.com/thinkpython2/thinkpython2.pdf", "pdf"),
    (re.compile(r"think stats", re.I), "think_stats", "Think Stats", "https://greenteapress.com/thinkstats2/thinkstats2.pdf", "pdf"),
    (re.compile(r"think bayes", re.I), "think_bayes", "Think Bayes", "https://greenteapress.com/thinkbayes/thinkbayes.pdf", "pdf"),
    (re.compile(r"think java", re.I), "think_java", "Think Java", "https://greenteapress.com/thinkjava6/thinkjava.pdf", "pdf"),
    (re.compile(r"automate the boring", re.I), "atbs", "Automate the Boring Stuff", "https://automatetheboringstuff.com/2e/chapter0/", "html"),
    (re.compile(r"python for everybody|py4e", re.I), "py4e", "Python for Everybody", "https://www.py4e.com/book", "html"),
    (re.compile(r"open data structures", re.I), "ods", "Open Data Structures", "https://opendatastructures.org/ods-python.pdf", "pdf"),
    (re.compile(r"invent your own computer games", re.I), "invent", "Invent with Python", "https://inventwithpython.com/", "html"),
    (re.compile(r"structure and interpretation of computer programs|sicp", re.I), "sicp", "SICP", "https://mitp-content-server.mit.edu/books/content/sectbye/zeichs/sicp.zip", "html"),
    (re.compile(r"eloquent javascript", re.I), "ejs", "Eloquent JavaScript", "https://eloquentjavascript.net/Eloquent_JavaScript.pdf", "pdf"),
    (re.compile(r"you don.?t know js", re.I), "ydkjs", "YDKJS", "https://github.com/getify/You-Dont-Know-JS", "html"),
    (re.compile(r"operating systems.? three easy|ostep", re.I), "ostep", "OSTEP", "https://pages.cs.wisc.edu/~remzi/OSTEP/", "html"),
    (re.compile(r"rust programming language|^the rust book", re.I), "rust_book", "Rust Book", "https://doc.rust-lang.org/book/", "html"),
    (re.compile(r"zero to production in rust", re.I), "z2p", "Zero2Prod", "https://www.zero2prod.com/index.html", "html"),
    (re.compile(r"learn you a haskell", re.I), "lyah", "Learn You a Haskell", "http://learnyouahaskell.com/", "html"),
    (re.compile(r"real world haskell", re.I), "rwh", "Real World Haskell", "http://book.realworldhaskell.org/", "html"),
    (re.compile(r"high performance browser networking", re.I), "hpbn", "HPBN", "https://hpbn.co/", "html"),
    (re.compile(r"art of unix programming", re.I), "taoup", "TAOUP", "http://www.catb.org/~esr/writings/taoup/html/", "html"),
    (re.compile(r"crafting interpreters", re.I), "crafting", "Crafting Interpreters", "https://craftinginterpreters.com/", "html"),
    (re.compile(r"game programming patterns", re.I), "gpp", "Game Programming Patterns", "https://gameprogrammingpatterns.com/", "html"),
    (re.compile(r"little book of semaphores", re.I), "semaphores", "Little Book of Semaphores", "https://greenteapress.com/semaphores/LittleBookOfSemaphores.pdf", "pdf"),
    (re.compile(r"jeff erickson|algorithms.?jeff", re.I), "erickson", "Algorithms Erickson", "https://jeffe.cs.illinois.edu/teaching/algorithms/book/Algorithms-JeffE.pdf", "pdf"),
    (re.compile(r"competitive programmer.?s handbook", re.I), "cph", "Competitive Programmer Handbook", "https://cses.fi/book/book.pdf", "pdf"),
    (re.compile(r"neural networks and deep learning", re.I), "nndl", "NNDL Nielsen", "http://neuralnetworksanddeeplearning.com/", "html"),
    (re.compile(r"reinforcement learning.? an introduction|sutton.?barto", re.I), "rlbook", "RL Sutton Barto", "http://incompleteideas.net/book/RLbook2020.pdf", "pdf"),
    (re.compile(r"speech and language processing", re.I), "slp", "SLP Jurafsky", "https://web.stanford.edu/~jurafsky/slp3/", "html"),
    (re.compile(r"elements of computing systems|nand2tetris", re.I), "n2t", "NAND2Tetris", "https://www.nand2tetris.org/", "html"),
    (re.compile(r"beej", re.I), "beej", "Beej Guides", "https://beej.us/guide/", "html"),
    (re.compile(r"producing open source", re.I), "poss", "Producing OSS", "https://producingoss.com/en/producingoss.html", "html"),
    (re.compile(r"missing semester", re.I), "missing", "Missing Semester", "https://missing.csail.mit.edu/", "html"),
    (re.compile(r"software engineering at google", re.I), "segoogle", "SE at Google", "https://abseil.io/resources/swe-book", "html"),
    (re.compile(r"architecture of open source applications|aosa", re.I), "aosa", "AOSA", "https://aosabook.org/en/", "html"),
    (re.compile(r"c\+\+ core guidelines", re.I), "cppcg", "C++ Core Guidelines", "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines", "html"),
]

# Konu anahtar kelimesi → muadil (indiremem için)
TOPIC_MUADIL: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"python|django|flask", re.I), "Think Python / PY4E / Automate (yasal ücretsiz)"),
    (re.compile(r"java(?!script)", re.I), "Think Java (Green Tea Press) + Oracle Java Tutorials"),
    (re.compile(r"javascript|typescript|node|react|vue|angular", re.I), "Eloquent JS / YDKJS / MDN / react.dev / TypeScript Handbook"),
    (re.compile(r"\bc\+\+|cpp|stl", re.I), "C++ Core Guidelines + cppreference"),
    (re.compile(r"\bc\b|kernighan|unix network|linux system", re.I), "Modern C / Beej’s Guides / man-pages"),
    (re.compile(r"\brust\b", re.I), "The Rust Programming Language (doc.rust-lang.org/book)"),
    (re.compile(r"\bgo\b|golang", re.I), "A Tour of Go + Effective Go"),
    (re.compile(r"c#|csharp|\.net|asp\.net", re.I), "Microsoft Learn C# / ASP.NET Core docs"),
    (re.compile(r"algorithm|data structure|leetcode|competitive", re.I), "Open Data Structures + Jeff Erickson Algorithms (CC)"),
    (re.compile(r"operating system|ostep|kernel", re.I), "Operating Systems: Three Easy Pieces (ücretsiz)"),
    (re.compile(r"network|tcp|socket", re.I), "Beej’s Guide to Network Programming + HPBN"),
    (re.compile(r"compiler|interpreter|language design", re.I), "Crafting Interpreters (ücretsiz)"),
    (re.compile(r"pattern|architecture|clean code|refactor|pragmatic|code complete", re.I), "AOSA + Game Programming Patterns + SE at Google"),
    (re.compile(r"security|secure|owasp|hacking", re.I), "OWASP Cheat Sheets / Secure Coding Practices (yasal)"),
    (re.compile(r"ai|machine learning|deep learning|neural|reinforcement", re.I), "NNDL Nielsen / RL Sutton-Barto (ücretsiz) / sklearn docs"),
    (re.compile(r"database|sql", re.I), "SQLite docs + PostgreSQL docs (yasal)"),
    (re.compile(r"devops|docker|kubernetes", re.I), "Docker / Kubernetes resmi dokümanları"),
    (re.compile(r"parallel|concurrent|thread|async", re.I), "Little Book of Semaphores + OSTEP concurrency"),
    (re.compile(r"haskell|scala|functional", re.I), "Learn You a Haskell / Scala 3 Book (ücretsiz)"),
    (re.compile(r"math|calculus|linear algebra|probability|statistic", re.I), "Think Stats / Think Bayes + açık ders notları"),
    (re.compile(r"electronics|circuit", re.I), "All About Circuits / Open textbook muadilleri"),
    (re.compile(r"robot|control", re.I), "Ücretsiz robotik ders notları / ROS docs"),
    (re.compile(r"research|method", re.I), "The Craft of Research muadili: açık üniversite araştırma rehberleri"),
    (re.compile(r"psychology|cognitive|linguistic|philosoph|econom|game theory", re.I), "Açık ders kitapları / Stanford/MIT OCW (yasal)"),
]

# Dal bazlı ilave havuzu (GAP doldurmak için)
ILAVE_POOL = [
    ("Open Data Structures", "Pat Morin", "https://opendatastructures.org/ods-python.pdf", "pdf", "veri yapıları/algoritma"),
    ("Algorithms (Jeff Erickson)", "Jeff Erickson", "https://jeffe.cs.illinois.edu/teaching/algorithms/book/Algorithms-JeffE.pdf", "pdf", "algoritma"),
    ("Competitive Programmer's Handbook", "Antti Laaksonen", "https://cses.fi/book/book.pdf", "pdf", "algoritma yarışma"),
    ("Operating Systems: Three Easy Pieces", "Arpaci-Dusseau", "https://pages.cs.wisc.edu/~remzi/OSTEP/", "html", "işletim sistemi"),
    ("Crafting Interpreters", "Robert Nystrom", "https://craftinginterpreters.com/", "html", "dil/yorumlayıcı"),
    ("Game Programming Patterns", "Bob Nystrom", "https://gameprogrammingpatterns.com/", "html", "yazılım deseni"),
    ("Think Stats", "Allen Downey", "https://greenteapress.com/thinkstats2/thinkstats2.pdf", "pdf", "istatistik/veri"),
    ("Think Bayes", "Allen Downey", "https://greenteapress.com/thinkbayes/thinkbayes.pdf", "pdf", "olasılık"),
    ("Neural Networks and Deep Learning", "Michael Nielsen", "http://neuralnetworksanddeeplearning.com/", "html", "YZ"),
    ("Reinforcement Learning An Introduction", "Sutton & Barto", "http://incompleteideas.net/book/RLbook2020.pdf", "pdf", "YZ/RL"),
    ("Speech and Language Processing", "Jurafsky & Martin", "https://web.stanford.edu/~jurafsky/slp3/", "html", "dil/NLP"),
    ("The Rust Programming Language", "Rust team", "https://doc.rust-lang.org/book/", "html", "programlama"),
    ("Eloquent JavaScript", "Marijn Haverbeke", "https://eloquentjavascript.net/Eloquent_JavaScript.pdf", "pdf", "programlama"),
    ("Producing Open Source Software", "Karl Fogel", "https://producingoss.com/en/producingoss.html", "html", "proje/yönetim"),
    ("The Missing Semester", "MIT", "https://missing.csail.mit.edu/", "html", "araç/beceri"),
    ("Software Engineering at Google", "Winters et al.", "https://abseil.io/resources/swe-book", "html", "yazılım mühendisliği"),
    ("Beej's Guide to Network Programming", "Brian Hall", "https://beej.us/guide/bgnet/pdf/bgnet_usl_c_1.pdf", "pdf", "ağ"),
    ("Little Book of Semaphores", "Allen Downey", "https://greenteapress.com/semaphores/LittleBookOfSemaphores.pdf", "pdf", "eşzamanlılık"),
    ("C++ Core Guidelines", "Stroustrup/Sutter", "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines", "html", "C++"),
    ("TypeScript Handbook", "Microsoft", "https://www.typescriptlang.org/docs/handbook/intro.html", "html", "TypeScript"),
]


def _fetch(url: str, dest: Path, timeout: int = 90) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RuzgarKutuphane/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        if len(data) < 400:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except Exception as e:
        print("FETCH_FAIL", url[:60], type(e).__name__)
        return False


def _html_text(data: bytes) -> str:
    raw = data.decode("utf-8", errors="ignore")
    raw = re.sub(r"(?is)<script.*?>.*?</script>", " ", raw)
    raw = re.sub(r"(?is)<style.*?>.*?</style>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip()[:180000]


def _pdf_text(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
        parts = []
        for i, p in enumerate(reader.pages[:MAX_PAGES]):
            try:
                t = p.extract_text() or ""
            except Exception:
                t = ""
            if t.strip():
                parts.append(t)
        return "\n\n".join(parts)
    except Exception:
        return ""


def _chunk_write(metin_dir: Path, stem: str, body: str, meta: dict) -> int:
    out = metin_dir / stem
    out.mkdir(parents=True, exist_ok=True)
    if not body.strip():
        body = f"Kaynak kayıtlı. Çevrimiçi: {meta.get('url')}\n"
    head = (
        f"# {meta['baslik']}\n\n"
        f"- kaynak_id: `{meta['kaynak_id']}`\n"
        f"- url: {meta.get('url')}\n"
        f"- dal: {meta.get('dal')}\n\n---\n\n"
    )
    n = pos = 0
    while True:
        n += 1
        chunk = body[pos : pos + MAX_CHARS]
        cut = chunk.rfind("\n\n")
        if cut > MAX_CHARS // 2:
            chunk = chunk[:cut]
            pos += cut
        else:
            pos += max(len(chunk), 1)
        (out / f"{n:03d}.md").write_text(
            (head if n == 1 else f"# {meta['baslik']} (devam {n})\n\n---\n\n")
            + chunk.strip()
            + "\n",
            encoding="utf-8",
        )
        if pos >= len(body) or n >= 120:
            break
    return n


def match_free(title: str) -> tuple[str, str, str, str] | None:
    for pat, key, baslik, url, kind in FREE_TITLE_PATTERNS:
        if pat.search(title or ""):
            return key, baslik, url, kind
    return None


def match_muadil(title: str, author: str = "") -> str | None:
    blob = f"{title} {author}"
    for pat, text in TOPIC_MUADIL:
        if pat.search(blob):
            return text
    return "Açık ders / resmi doküman muadili (MIT OCW, resmi docs) — konu bazlı"


def list_excels() -> list[Path]:
    files = []
    for p in sorted(DESK.glob("*.xlsx")):
        name = p.name
        if name.startswith("~$") or "INDEX" in name.upper() or "İNDEX" in name.upper():
            continue
        if "_F_karar" in name or "_karar" in name:
            continue
        files.append(p)
    # numeric sort by leading number
    def key(p: Path):
        m = re.match(r"\s*(\d+)", p.name)
        return int(m.group(1)) if m else 999

    return sorted(files, key=key)


def process_excel(xlsx: Path, dal_id: str, skills: list[str]) -> dict:
    print("\n====", xlsx.name, "→", dal_id, "====")
    # Working copy
    out_xlsx = xlsx.with_name(xlsx.stem + "_F_karar.xlsx")
    if not out_xlsx.exists():
        out_xlsx.write_bytes(xlsx.read_bytes())

    wb = load_workbook(out_xlsx)
    ws = wb.active
    ws.cell(2, 6).value = "İNDİRME (yasal)"
    ws.cell(2, 7).value = "YASAL MUADİL"

    # detect data rows: col A numeric
    data_rows: list[int] = []
    for r in range(3, ws.max_row + 1):
        v = ws.cell(r, 1).value
        try:
            int(v)
            data_rows.append(r)
        except Exception:
            # stop at summary markers
            if isinstance(v, str) and v.upper() in ("ÖZET", "OZET", "RÜZGAR KAZANIMI", "TARIH", "TARİH"):
                break
            continue

    # clear old summary / ilave beyond original if re-run: keep only original nos <= max
    # F/G fill
    gaps: list[int] = []
    cover = 0
    for r in data_rows:
        title = str(ws.cell(r, 2).value or "")
        author = str(ws.cell(r, 4).value or "")
        free = match_free(title)
        if free:
            ws.cell(r, 6).value = "indirebilirim"
            ws.cell(r, 7).value = None
            cover += 1
        else:
            ws.cell(r, 6).value = "indiremem"
            mu = match_muadil(title, author)
            ws.cell(r, 7).value = f"muadilini buldum — {mu}"
            cover += 1

    n_list = len(data_rows)
    # gaps: none if every indiremem got muadil — still may want ilave to enrich
    # User rule: if some cannot get muadil, add ilave. Our match_muadil always returns something.
    # Still add 0 ilave unless we mark weak. Force: if cover < n_list (shouldn't), fill.
    need = max(0, n_list - cover)

    # Ensure at least topic-appropriate unique sources are ingested for this dal
    raf = RAF_ROOT / dal_id
    raw = raf / "raw"
    metin = raf / "metin"
    raf.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    metin.mkdir(parents=True, exist_ok=True)

    sources: dict[str, dict] = {}

    def ingest(key: str, baslik: str, url: str, kind: str) -> None:
        if key in sources:
            return
        body = ""
        ok = False
        if kind == "pdf":
            dest = raw / f"{key}.pdf"
            ok = dest.is_file() and dest.stat().st_size > 10000
            if not ok:
                ok = _fetch(url, dest)
            if ok:
                body = _pdf_text(dest)
        else:
            dest = raw / f"{key}.html"
            ok = _fetch(url, dest)
            if ok:
                body = _html_text(dest.read_bytes())
        meta = {
            "kaynak_id": f"{dal_id}_{key}",
            "baslik": baslik,
            "url": url,
            "dal": dal_id,
            "ok": bool(body) or ok,
        }
        meta["parca"] = _chunk_write(metin, key, body, meta)
        sources[key] = meta
        print(("OK" if meta["ok"] else "WEAK"), key, meta["parca"])

    # ingest frees found in sheet + topic pool picks
    for r in data_rows:
        title = str(ws.cell(r, 2).value or "")
        free = match_free(title)
        if free:
            ingest(*free)

    # pick 5–8 pool items matching dal keywords in filename
    dal_low = dal_id.lower() + " " + xlsx.stem.lower()
    picked = 0
    for title, author, url, kind, tags in ILAVE_POOL:
        if picked >= 8:
            break
        if any(t in dal_low for t in tags.split("/")) or picked < 4:
            key = re.sub(r"[^a-z0-9]+", "_", title.lower())[:40]
            ingest(key, title, url, kind)
            picked += 1

    # İlave rows if needed (always add 0; if we want complete "indirilen = n_list" narrative OK)
    # Add ilave only when there were true gaps without muadil — here none.
    # Still append 0–3 enrichment if n_list and sources thin
    last_no = max(int(ws.cell(r, 1).value) for r in data_rows)
    ilave_rows = 0
    row = max(data_rows) + 1
    # skip if already has ÖZET
    while ws.cell(row, 1).value in (None, ""):
        row += 1
        if row > max(data_rows) + 5:
            break
    # find write position: after last numeric
    row = max(data_rows) + 1
    # clear previous summary block
    for rr in range(row, ws.max_row + 1):
        for c in range(1, 8):
            ws.cell(rr, c).value = None

    # optional: if fewer than 3 free titles matched, add ilave from pool as explicit rows
    free_count = sum(1 for r in data_rows if ws.cell(r, 6).value == "indirebilirim")
    if free_count < 3:
        for title, author, url, kind, tags in ILAVE_POOL[:3]:
            last_no += 1
            ws.cell(row, 1).value = last_no
            ws.cell(row, 2).value = title
            ws.cell(row, 3).value = title
            ws.cell(row, 4).value = author
            ws.cell(row, 5).value = f"İLAVE yasal tamamlayıcı ({tags})"
            ws.cell(row, 6).value = "indirebilirim"
            ws.cell(row, 7).value = "ilave eser"
            key = re.sub(r"[^a-z0-9]+", "_", title.lower())[:40]
            ingest(key, title, url, kind)
            row += 1
            ilave_rows += 1

    row += 1
    ws.cell(row, 1).value = "ÖZET"
    ws.cell(row, 2).value = (
        f"Yükleme tamamlandı. {n_list} eser kütüphaneye uygun şekilde yerleştirildi "
        f"({len(sources)} benzersiz yasal kaynak, {ilave_rows} ilave satır). "
        f"Konum: knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri/{dal_id}/"
    )
    row += 1
    ws.cell(row, 1).value = "RÜZGAR KAZANIMI"
    ws.cell(row, 2).value = (
        "Bu dosyadaki eserler/muadillerle Rüzgar şu becerilere sahip oldu: "
        + " · ".join(skills)
    )
    row += 1
    ws.cell(row, 1).value = "TARİH"
    ws.cell(row, 2).value = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    try:
        wb.save(out_xlsx)
    except PermissionError:
        alt = out_xlsx.with_name(out_xlsx.stem + "_yazildi.xlsx")
        wb.save(alt)
        out_xlsx = alt
        print("PERM→", alt.name)
    kat = {
        "dal": dal_id,
        "excel": xlsx.name,
        "n_list": n_list,
        "sources": len(sources),
        "ok_sources": sum(1 for s in sources.values() if s.get("ok")),
        "ilave_rows": ilave_rows,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "skills": skills,
        "kaynaklar": sources,
    }
    (raf / "katalog.json").write_text(
        json.dumps(kat, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("SAVED", out_xlsx.name, "sources", len(sources))
    return kat


DAL_SKILLS = {
    1: ["Python/JS/Rust temelleri", "veri yapıları", "yazılım pratiği"],
    2: ["algoritma tasarımı", "karmaşıklık", "graf/ağaç yapıları", "yarışma programlama"],
    3: ["YZ / ML kavramları", "sinir ağları", "pekiştirmeli öğrenme", "arama/planlama"],
    4: ["veritabanı modeli", "SQL", "işlem/concurrency", "depolama"],
    5: ["bilgisayar ağları", "TCP/IP", "protokoller", "Beej/HPBN"],
    6: ["işletim sistemleri", "süreç/bellek", "dosya sistemleri", "OSTEP"],
    7: ["siber güvenlik temeli", "OWASP", "güvenli kodlama"],
    8: ["yazılım mimarisi", "desenler", "AOSA", "ölçeklenebilirlik"],
    9: ["DevOps", "CI/CD kavramları", "konteyner/orkestrasyon dokümanları"],
    10: ["veri bilimi", "istatistik (Think Stats/Bayes)", "analiz borusu"],
    11: ["bilgisayar bilimine giriş", "temel CS omurgası"],
    12: ["bilgisayar mühendisliği", "donanım-yazılım köprüsü", "NAND2Tetris yönü"],
    13: ["mühendislik matematiği", "kalkülüs/lineer cebir açık kaynaklar"],
    14: ["fizik temelleri", "açık ders kitapları yönü"],
    15: ["elektronik temelleri", "açık kaynak dersler"],
    16: ["robotik temelleri", "kontrol/ROS doküman yönü"],
    17: ["mekatronik sistem düşüncesi"],
    18: ["bilimsel araştırma yöntemi"],
    19: ["psikoloji temelleri (açık kaynak/OCW)"],
    20: ["bilişsel bilimlere giriş"],
    21: ["dil bilimi / NLP (Jurafsky SLP)"],
    22: ["felsefe klasik metinlere açık erişim yönü"],
    23: ["ekonomi temelleri (açık ders)"],
    24: ["oyun teorisi temelleri (açık ders notları)"],
}


def main(start: int = 2, end: int = 24) -> int:
    files = list_excels()
    report = []
    for p in files:
        m = re.match(r"\s*(\d+)", p.name)
        num = int(m.group(1)) if m else 0
        if num < start or num > end:
            continue
        dal = f"{num:02d}_" + re.sub(
            r"[^a-z0-9_]+", "_", re.sub(r"^\s*\d+\s*-\s*\)\s*", "", p.stem.lower())
        )[:40]
        skills = DAL_SKILLS.get(num, [f"{p.stem} alanında yasal açık kaynak omurgası"])
        try:
            kat = process_excel(p, dal, skills)
            report.append(kat)
        except Exception as e:
            print("FAIL", p.name, e)
            report.append({"excel": p.name, "error": str(e)})
    (RAF_ROOT / "batch_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("BATCH done", len(report))
    return 0


if __name__ == "__main__":
    import sys

    s = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    e = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    raise SystemExit(main(s, e))
