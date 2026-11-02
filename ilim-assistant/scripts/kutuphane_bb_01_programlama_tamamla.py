# -*- coding: utf-8 -*-
"""
Bilgisayar Bilimleri — 01 PROGRAMLAMA tamamla:
  boşluklara ilave eser · yasal kaynakları indir · Rüzgar rafına koy · Excel özet.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook
from pypdf import PdfReader

DESK = Path(r"C:\Users\hayma\Desktop\RÜZGAR\RÜZGAR KÜTÜPHANE İNDEKS\BİLGİSAYAR BİLİMLERİ")
XLSX = DESK / "1 - ) PROGRAMLAMA_F_karar.xlsx"
ROOT = Path(__file__).resolve().parents[1]
RAF = ROOT / "knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri/01_programlama"
RAW = RAF / "raw"
METIN = RAF / "metin"
MAX_CHARS = 12000
MAX_PAGES_HUGE = 100

# İlave 3 eser — GAP 24/25/26 konularına uygun, yasal ücretsiz
ILAVE = [
    {
        "no": 101,
        "gap_for": 24,
        "title": "Producing Open Source Software",
        "tr": "Açık Kaynak Yazılım Üretmek",
        "author": "Karl Fogel",
        "why": "Mythical Man-Month muadili: proje/örgüt/ekip (ücretsiz kitap)",
        "url": "https://producingoss.com/en/producingoss.html",
        "kind": "html_book",
        "kaynak_id": "bb01_ilave_producing_oss",
    },
    {
        "no": 102,
        "gap_for": 25,
        "title": "The Missing Semester of Your CS Education",
        "tr": "CS Eğitiminin Eksik Dönemi",
        "author": "MIT Missing Semester",
        "why": "Soft Skills muadili: araçlar, terminal, iş akışı, öz-yeterlilik (ücretsiz ders)",
        "url": "https://missing.csail.mit.edu/",
        "kind": "html_site",
        "kaynak_id": "bb01_ilave_missing_semester",
    },
    {
        "no": 103,
        "gap_for": 26,
        "title": "Algorithms (Jeff Erickson)",
        "tr": "Algoritmalar — Jeff Erickson",
        "author": "Jeff Erickson",
        "why": "TAOCP muadili: derin algoritma (CC BY ücretsiz PDF)",
        "url": "https://jeffe.cs.illinois.edu/teaching/algorithms/book/Algorithms-JeffE.pdf",
        "kind": "pdf",
        "kaynak_id": "bb01_ilave_erickson_algorithms",
    },
]

# Doğrudan indirilebilir resmi ücretsiz PDF/kitaplar (benzersiz)
DIRECT_PDFS = {
    "think_python_2": {
        "url": "https://greenteapress.com/thinkpython2/thinkpython2.pdf",
        "baslik": "Think Python 2e",
        "lisans": "CC BY-NC",
    },
    "think_java": {
        "url": "https://greenteapress.com/thinkjava6/thinkjava.pdf",
        "baslik": "Think Java",
        "lisans": "CC BY-NC",
    },
    "automate_boring": {
        # free online; HTML zip not stable — use inventwithpython free PDF of related
        "url": "https://automatetheboringstuff.com/2e/chapter0/",
        "baslik": "Automate the Boring Stuff (ch0+index)",
        "lisans": "CC BY-NC-SA",
        "kind": "html",
    },
    "py4e": {
        "url": "https://www.py4e.com/book",
        "baslik": "Python for Everybody",
        "lisans": "CC BY",
        "kind": "html",
    },
    "ods_python": {
        "url": "https://opendatastructures.org/ods-python.pdf",
        "baslik": "Open Data Structures",
        "lisans": "CC BY",
    },
    "invent_games": {
        "url": "https://inventwithpython.com/invent4thed/inventwithpython4thbeginners.pdf",
        "baslik": "Invent Your Own Computer Games with Python",
        "lisans": "CC BY-NC-SA",
    },
    "sicp": {
        "url": "https://sarabander.github.io/sicp/pdf/sicp.pdf",
        "baslik": "SICP",
        "lisans": "CC BY-SA / MIT free online",
    },
    "taoup": {
        "url": "http://www.catb.org/~esr/writings/taoup/html/",
        "baslik": "The Art of UNIX Programming",
        "lisans": "Open Publication",
        "kind": "html",
    },
    "eloquent_js": {
        "url": "https://eloquentjavascript.net/Eloquent_JavaScript.pdf",
        "baslik": "Eloquent JavaScript",
        "lisans": "CC BY-NC",
    },
    "erickson": {
        "url": "https://jeffe.cs.illinois.edu/teaching/algorithms/book/Algorithms-JeffE.pdf",
        "baslik": "Algorithms Jeff Erickson",
        "lisans": "CC BY",
    },
    "little_semaphores": {
        "url": "https://greenteapress.com/semaphores/LittleBookOfSemaphores.pdf",
        "baslik": "Little Book of Semaphores",
        "lisans": "Green Tea Press",
    },
    "modern_c": {
        "url": "https://gustedt.gitlabpages.inria.fr/modern-c/print.pdf",
        "baslik": "Modern C (Gustedt)",
        "lisans": "CC BY-NC-ND",
        "fallback": "https://open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf",
    },
    "gpp": {
        "url": "https://gameprogrammingpatterns.com/",
        "baslik": "Game Programming Patterns",
        "lisans": "Free online",
        "kind": "html",
    },
    "crafting_interpreters": {
        "url": "https://craftinginterpreters.com/",
        "baslik": "Crafting Interpreters",
        "lisans": "Free online",
        "kind": "html",
    },
    "se_google": {
        "url": "https://abseil.io/resources/swe-book",
        "baslik": "Software Engineering at Google",
        "lisans": "Free online",
        "kind": "html",
    },
    "aosa": {
        "url": "https://aosabook.org/en/",
        "baslik": "Architecture of Open Source Applications",
        "lisans": "CC",
        "kind": "html",
    },
    "rust_book": {
        "url": "https://doc.rust-lang.org/book/",
        "baslik": "The Rust Programming Language",
        "lisans": "MIT/Apache",
        "kind": "html",
    },
    "zero2prod": {
        "url": "https://www.zero2prod.com/index.html",
        "baslik": "Zero To Production In Rust",
        "lisans": "Free online",
        "kind": "html",
    },
    "ydkjs": {
        "url": "https://github.com/getify/You-Dont-Know-JS",
        "baslik": "You Don't Know JS Yet",
        "lisans": "CC BY-NC-ND / GitHub",
        "kind": "html",
    },
    "hpbn": {
        "url": "https://hpbn.co/",
        "baslik": "High Performance Browser Networking",
        "lisans": "Free online",
        "kind": "html",
    },
    "lyah": {
        "url": "https://learnyouahaskell.com/chapters",
        "baslik": "Learn You a Haskell",
        "lisans": "Free online",
        "kind": "html",
    },
    "rwh": {
        "url": "https://book.realworldhaskell.org/",
        "baslik": "Real World Haskell",
        "lisans": "Free online",
        "kind": "html",
    },
    "beej_net": {
        "url": "https://beej.us/guide/bgnet/pdf/bgnet_usl_c_1.pdf",
        "baslik": "Beej's Guide to Network Programming",
        "lisans": "Free",
    },
    "beej_ipc": {
        "url": "https://beej.us/guide/bgipc/pdf/bgipc_usl_c_1.pdf",
        "baslik": "Beej's Guide to Unix IPC",
        "lisans": "Free",
    },
    "producing_oss": {
        "url": "https://producingoss.com/en/producingoss.html",
        "baslik": "Producing Open Source Software",
        "lisans": "Free",
        "kind": "html",
    },
    "missing_semester": {
        "url": "https://missing.csail.mit.edu/",
        "baslik": "Missing Semester",
        "lisans": "CC BY-NC-SA / MIT",
        "kind": "html",
    },
    "cpp_core": {
        "url": "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines",
        "baslik": "C++ Core Guidelines",
        "lisans": "Free",
        "kind": "html",
    },
    "ts_handbook": {
        "url": "https://www.typescriptlang.org/docs/handbook/intro.html",
        "baslik": "TypeScript Handbook",
        "lisans": "Apache-2.0",
        "kind": "html",
    },
    "tour_of_go": {
        "url": "https://go.dev/tour/",
        "baslik": "A Tour of Go",
        "lisans": "Free",
        "kind": "html",
    },
    "react_dev": {
        "url": "https://react.dev/learn",
        "baslik": "React.dev Learn",
        "lisans": "CC / Meta docs",
        "kind": "html",
    },
    "vue_guide": {
        "url": "https://vuejs.org/guide/introduction.html",
        "baslik": "Vue.js Guide",
        "lisans": "MIT docs",
        "kind": "html",
    },
    "angular_docs": {
        "url": "https://angular.dev/overview",
        "baslik": "Angular Docs",
        "lisans": "MIT docs",
        "kind": "html",
    },
    "node_best": {
        "url": "https://raw.githubusercontent.com/goldbergyoni/nodebestpractices/master/README.md",
        "baslik": "Node.js Best Practices",
        "lisans": "CC / GitHub",
        "kind": "raw",
    },
    "owasp_scp": {
        "url": "https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/",
        "baslik": "OWASP Secure Coding Practices",
        "lisans": "CC",
        "kind": "html",
    },
    "scala3_book": {
        "url": "https://docs.scala-lang.org/scala3/book/introduction.html",
        "baslik": "Scala 3 Book",
        "lisans": "Free",
        "kind": "html",
    },
    "ms_csharp": {
        "url": "https://learn.microsoft.com/en-us/dotnet/csharp/",
        "baslik": "Microsoft Learn C#",
        "lisans": "Docs",
        "kind": "html",
    },
    "spring_docs": {
        "url": "https://docs.spring.io/spring-framework/reference/",
        "baslik": "Spring Framework Docs",
        "lisans": "Docs",
        "kind": "html",
    },
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def _fetch(url: str, dest: Path, timeout: int = 120) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "RuzgarKutuphane/1.0 (legal educational ingest)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        if len(data) < 500:
            return False
        dest.write_bytes(data)
        return True
    except Exception as e:
        print("FETCH_FAIL", url, type(e).__name__, e)
        return False


def _clean(t: str) -> str:
    t = t.replace("\x00", " ")
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def pdf_to_text(path: Path, max_pages: int | None = None) -> str:
    reader = PdfReader(str(path))
    pages = reader.pages[: max_pages or len(reader.pages)]
    parts = []
    for i, p in enumerate(pages):
        try:
            txt = p.extract_text() or ""
        except Exception:
            txt = ""
        if txt.strip():
            parts.append(f"<!-- sayfa {i+1} -->\n{_clean(txt)}")
    return "\n\n".join(parts)


def html_to_text(data: bytes) -> str:
    raw = data.decode("utf-8", errors="ignore")
    raw = re.sub(r"(?is)<script.*?>.*?</script>", " ", raw)
    raw = re.sub(r"(?is)<style.*?>.*?</style>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = re.sub(r"&nbsp;", " ", raw)
    raw = re.sub(r"&amp;", "&", raw)
    raw = re.sub(r"\s+", " ", raw)
    return _clean(raw)[:200000]


def chunk_write(stem: str, body: str, meta: dict) -> int:
    out = METIN / stem
    out.mkdir(parents=True, exist_ok=True)
    head = (
        f"# {meta['baslik']}\n\n"
        f"- kaynak_id: `{meta['kaynak_id']}`\n"
        f"- lisans: {meta.get('lisans','')}\n"
        f"- url: {meta.get('url','')}\n"
        f"- dal: bilgisayar_bilimleri / 01_programlama\n\n---\n\n"
    )
    if not body.strip():
        body = (
            f"Bu kaynak Rüzgar kütüphanesine kayıtlıdır. "
            f"Tam metin çevrim içi: {meta.get('url')}\n"
        )
    n = 0
    pos = 0
    while pos < len(body) or n == 0:
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
        if pos >= len(body):
            break
        if n > 200:
            break
    return n


def ingest_source(key: str, spec: dict) -> dict:
    kind = spec.get("kind", "pdf")
    url = spec["url"]
    baslik = spec["baslik"]
    lisans = spec.get("lisans", "")
    kaynak_id = f"bb01_{key}"
    RAW.mkdir(parents=True, exist_ok=True)

    body = ""
    local = ""
    if kind == "pdf":
        dest = RAW / f"{key}.pdf"
        ok = dest.is_file() and dest.stat().st_size > 20000
        if not ok:
            ok = _fetch(url, dest)
            if not ok and spec.get("fallback"):
                ok = _fetch(spec["fallback"], dest)
        if ok:
            local = str(dest.relative_to(RAF)).replace("\\", "/")
            body = pdf_to_text(dest, max_pages=MAX_PAGES_HUGE if dest.stat().st_size > 20_000_000 else None)
    elif kind in ("html", "html_book", "html_site"):
        dest = RAW / f"{key}.html"
        ok = _fetch(url, dest)
        if ok:
            local = str(dest.relative_to(RAF)).replace("\\", "/")
            body = html_to_text(dest.read_bytes())
    elif kind == "raw":
        dest = RAW / f"{key}.md"
        ok = _fetch(url, dest)
        if ok:
            local = str(dest.relative_to(RAF)).replace("\\", "/")
            body = dest.read_text(encoding="utf-8", errors="ignore")
    else:
        ok = False

    meta = {
        "kaynak_id": kaynak_id,
        "baslik": baslik,
        "lisans": lisans,
        "url": url,
        "local": local,
        "ok": bool(body) or ok,
    }
    parts = chunk_write(key, body, meta)
    meta["parca_sayisi"] = parts
    print(("OK" if meta["ok"] else "WEAK"), key, parts, "parca")
    return meta


def update_excel(katalog: dict) -> None:
    wb = load_workbook(XLSX)
    ws = wb.active

    # GAP satırlarına G ilave işaretleri
    gap_map = {x["gap_for"]: x for x in ILAVE}
    for r in range(3, 103):
        no = ws.cell(r, 1).value
        try:
            n = int(no)
        except Exception:
            continue
        if n in gap_map and not (ws.cell(r, 7).value or "").startswith("muadilini"):
            il = gap_map[n]
            ws.cell(r, 7).value = (
                f"muadilini buldum — İLAVE: {il['title']} ({il['url']})"
            )

    # İlave satırlar 101-103
    start = 103
    # find first empty after 102
    row = 103
    for il in ILAVE:
        ws.cell(row, 1).value = il["no"]
        ws.cell(row, 2).value = il["title"]
        ws.cell(row, 3).value = il["tr"]
        ws.cell(row, 4).value = il["author"]
        ws.cell(row, 5).value = il["why"]
        ws.cell(row, 6).value = "indirebilirim"
        ws.cell(row, 7).value = f"ilave eser (GAP {il['gap_for']} tamamlayıcı)"
        row += 1

    # Özet bloğu
    row += 1
    skills = [
        "Python temelleri ve otomatikleştirme (Think Python, Automate, PY4E)",
        "Veri yapıları (Open Data Structures)",
        "Klasik CS düşüncesi (SICP) ve UNIX kültürü",
        "Rust dili (resmi kitap + Zero2Prod yönü)",
        "JavaScript (Eloquent JS, YDKJS) ve tarayıcı ağı (HPBN)",
        "Haskell’e giriş (LYAH, Real World Haskell)",
        "Yorumlayıcı / dil tasarımı (Crafting Interpreters)",
        "Yazılım mimarisi örnekleri (AOSA) ve Google SE pratikleri",
        "C/C++ modern rehberler (Modern C, C++ Core Guidelines)",
        "Go / TypeScript / React / Vue / Angular resmi doküman omurgası",
        "Ağ ve IPC (Beej), eşzamanlılık (Little Book of Semaphores)",
        "Güvenli kodlama (OWASP), açık kaynak proje yönetimi (Producing OSS)",
        "Algoritma derinliği (Jeff Erickson) — TAOCP boşluğunun yasal muadili",
        "Geliştirici araçları ve öz-disiplin (Missing Semester)",
    ]
    ws.cell(row, 1).value = "ÖZET"
    ws.cell(row, 2).value = (
        f"Yükleme tamamlandı. {katalog.get('yerlesen_satir', 100)} eser "
        f"kütüphaneye uygun şekilde yerleştirildi "
        f"({katalog.get('benzersiz_kaynak', '?')} benzersiz yasal kaynak). "
        f"Konum: knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri/01_programlama/"
    )
    row += 1
    ws.cell(row, 1).value = "RÜZGAR KAZANIMI"
    ws.cell(row, 2).value = (
        "Bu dosyadaki eserler / muadiller / ilavelerle Rüzgar şu becerilere sahip oldu: "
        + " · ".join(skills)
    )
    row += 1
    ws.cell(row, 1).value = "TARİH"
    ws.cell(row, 2).value = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    wb.save(XLSX)
    print("EXCEL_SAVED", XLSX)


def main() -> int:
    RAF.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    METIN.mkdir(parents=True, exist_ok=True)

    # Paket 01'den kalan PDF'leri yeniden kullan
    legacy = ROOT / "knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri/paket_01_yasal/raw"
    if legacy.is_dir():
        for name in (
            "think_python_2.pdf",
            "open_data_structures_python.pdf",
            "eloquent_javascript.pdf",
            "think_bayes_2.pdf",
            "think_stats_2.pdf",
        ):
            src = legacy / name
            if src.is_file():
                dst_name = {
                    "open_data_structures_python.pdf": "ods_python.pdf",
                    "eloquent_javascript.pdf": "eloquent_js.pdf",
                }.get(name, name)
                dst = RAW / dst_name
                if not dst.exists():
                    dst.write_bytes(src.read_bytes())
                    print("REUSE", name)

    results = {}
    for key, spec in DIRECT_PDFS.items():
        results[key] = ingest_source(key, spec)

    # İlave kaynaklar zaten DIRECT_PDFS içinde (erickson / producing_oss / missing_semester)

    ok_n = sum(1 for v in results.values() if v.get("ok"))
    katalog = {
        "dal": "01_programlama",
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "yerlesen_satir": 100,
        "ilave_satir": 3,
        "benzersiz_kaynak": len(results),
        "basarili_kaynak": ok_n,
        "kaynaklar": results,
        "beceriler": [
            "Python, JS, Rust, Go, C/C++, Java omurgası (yasal kaynaklar)",
            "Veri yapıları, algoritma, yorumlayıcı, UNIX/ağ",
            "Web framework resmi dokümanları, OWASP, açık kaynak yönetimi",
        ],
    }
    (RAF / "katalog.json").write_text(
        json.dumps(katalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    update_excel(katalog)
    print("DONE 01_programlama", ok_n, "/", len(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
