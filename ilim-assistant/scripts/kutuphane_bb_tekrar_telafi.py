# -*- coding: utf-8 -*-
"""
TELAFİ: Bilgisayar eserleri raflarındaki çapraz-dal kopyaları temizle;
her dala yalnız kendi yasal kaynaklarını koy; INDEX/Excel dürüst özet.
"""
from __future__ import annotations

import json
import re
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook
from pypdf import PdfReader

DESK = Path(r"C:\Users\hayma\Desktop\RÜZGAR\RÜZGAR KÜTÜPHANE İNDEKS\BİLGİSAYAR BİLİMLERİ")
ROOT = Path(__file__).resolve().parents[1]
RAF = ROOT / "knowledge/ortak_kaynak/alanlar/bilgisayar_eserleri"
MAX_CHARS = 12000
MAX_PAGES = 80

# Kaynak anahtarı / URL gövdesi → tek sahiplik dalı (diğerlerinden silinir)
CANONICAL_HOME: dict[str, str] = {
    "open_data_structures": "02_algori_tmalar",
    "algorithms_jeff_erickson_": "02_algori_tmalar",
    "competitive_programmer_s_handbook": "02_algori_tmalar",
    "ods": "02_algori_tmalar",
    "erickson": "02_algori_tmalar",
    "cph": "02_algori_tmalar",
    "operating_systems_three_easy_pieces": "06_i_leti_m_si_stemleri_",
    "ostep": "06_i_leti_m_si_stemleri_",
    "rlbook": "03_yapay_zeka",
    "nndl": "03_yapay_zeka",
    "think_stats": "10_veri_bi_li_mi_",
    "think_bayes": "10_veri_bi_li_mi_",
    "hpbn": "05_a_teknoloji_leri_",
    "beej": "05_a_teknoloji_leri_",
    "beej_s_guide_to_network_programming": "05_a_teknoloji_leri_",
    "segoogle": "08_yazilim_mi_mari_leri_",
    "se_google": "08_yazilim_mi_mari_leri_",
    "aosa": "08_yazilim_mi_mari_leri_",
    "gpp": "08_yazilim_mi_mari_leri_",
    "missing_cs": "09_devops_ve_altyapisi",
    "missing_semester": "09_devops_ve_altyapisi",
    "n2t": "12_bi_lgi_sayar_m_hendi_sli_i_",
    "slp": "21_di_l_bi_li_mi_",
    "think_python": "01_programlama",
    "think_java": "01_programlama",
    "atbs": "01_programlama",
    "py4e": "01_programlama",
    "ejs": "01_programlama",
    "rust_book": "01_programlama",
    "crafting": "01_programlama",
    "owasp_scp": "07_si_ber_g_venli_k",
}

# Dal numarası → yalnız bu dala ait yasal kaynaklar (tekrar yok)
# (key, baslik, url, kind)
DAL_OZEL: dict[int, list[tuple[str, str, str, str]]] = {
    1: [],  # zaten zengin; dokunma (sadece yabancı kopya yok)
    2: [
        ("ods", "Open Data Structures", "https://opendatastructures.org/ods-python.pdf", "pdf"),
        ("erickson", "Algorithms (Jeff Erickson)", "https://jeffe.cs.illinois.edu/teaching/algorithms/book/Algorithms-JeffE.pdf", "pdf"),
        ("cph", "Competitive Programmer's Handbook", "https://cses.fi/book/book.pdf", "pdf"),
    ],
    3: [
        ("nndl", "Neural Networks and Deep Learning", "http://neuralnetworksanddeeplearning.com/", "html"),
        ("rlbook", "Reinforcement Learning (Sutton & Barto)", "http://incompleteideas.net/book/RLbook2020.pdf", "pdf"),
        ("fastai", "Practical Deep Learning for Coders (fast.ai)", "https://course.fast.ai/", "html"),
    ],
    4: [
        ("sqlite_lang", "SQLite Language Reference", "https://www.sqlite.org/lang.html", "html"),
        ("pg_tutorial", "PostgreSQL Tutorial", "https://www.postgresql.org/docs/current/tutorial.html", "html"),
        ("use_the_index", "Use The Index, Luke", "https://use-the-index-luke.com/", "html"),
    ],
    5: [
        ("hpbn", "High Performance Browser Networking", "https://hpbn.co/", "html"),
        ("beej_net", "Beej's Guide to Network Programming", "https://beej.us/guide/bgnet/html/", "html"),
        ("beej_ipc", "Beej's Guide to Unix IPC", "https://beej.us/guide/bgipc/html/", "html"),
    ],
    6: [
        ("ostep", "Operating Systems: Three Easy Pieces", "https://pages.cs.wisc.edu/~remzi/OSTEP/", "html"),
        ("linux_kernel", "Linux Kernel Documentation (intro)", "https://docs.kernel.org/process/howto.html", "html"),
    ],
    7: [
        ("owasp_top10", "OWASP Top 10", "https://owasp.org/www-project-top-ten/", "html"),
        ("owasp_cheat", "OWASP Cheat Sheet Series", "https://cheatsheetseries.owasp.org/Index.html", "html"),
        ("owasp_asvs", "OWASP ASVS", "https://owasp.org/www-project-application-security-verification-standard/", "html"),
    ],
    8: [
        ("segoogle", "Software Engineering at Google", "https://abseil.io/resources/swe-book", "html"),
        ("aosa", "Architecture of Open Source Applications", "https://aosabook.org/en/", "html"),
        ("gpp", "Game Programming Patterns", "https://gameprogrammingpatterns.com/", "html"),
    ],
    9: [
        ("docker_start", "Docker Get Started", "https://docs.docker.com/get-started/", "html"),
        ("k8s_concepts", "Kubernetes Concepts", "https://kubernetes.io/docs/concepts/", "html"),
        ("missing_cs", "MIT Missing Semester", "https://missing.csail.mit.edu/", "html"),
    ],
    10: [
        ("think_stats", "Think Stats", "https://greenteapress.com/thinkstats2/thinkstats2.pdf", "pdf"),
        ("think_bayes", "Think Bayes", "https://greenteapress.com/thinkbayes/thinkbayes.pdf", "pdf"),
        ("sklearn_ug", "scikit-learn User Guide", "https://scikit-learn.org/stable/user_guide.html", "html"),
    ],
    11: [
        ("teachyourselfcs", "Teach Yourself Computer Science", "https://teachyourselfcs.com/", "html"),
        ("ossu", "OSSU Computer Science", "https://github.com/ossu/computer-science", "html"),
        ("cs50", "CS50 Harvard (açık ders)", "https://cs50.harvard.edu/x/", "html"),
    ],
    12: [
        ("n2t", "Nand2Tetris / Elements of Computing Systems", "https://www.nand2tetris.org/", "html"),
        ("computer_systems", "CMU 15-213 / CSAPP course page", "https://www.cs.cmu.edu/~213/", "html"),
        ("ben_eater", "Ben Eater 8-bit computer (eğitim)", "https://eater.net/8bit", "html"),
    ],
    13: [
        ("openstax_calc1", "OpenStax Calculus Volume 1", "https://openstax.org/details/books/calculus-volume-1", "html"),
        ("openstax_linalg", "OpenStax Algebra and Trigonometry", "https://openstax.org/details/books/algebra-and-trigonometry", "html"),
        ("3blue1brown_essence", "Essence of Linear Algebra (3Blue1Brown index)", "https://www.3blue1brown.com/topics/linear-algebra", "html"),
    ],
    14: [
        ("openstax_physics", "OpenStax University Physics Volume 1", "https://openstax.org/details/books/university-physics-volume-1", "html"),
        ("openstax_colphys", "OpenStax College Physics", "https://openstax.org/details/books/college-physics-2e", "html"),
        ("hyperphysics", "HyperPhysics (Georgia State)", "http://hyperphysics.phy-astr.gsu.edu/hbase/index.html", "html"),
    ],
    15: [
        ("elec_tutorials", "Electronics Tutorials", "https://www.electronics-tutorials.ws/", "html"),
        ("circuitpython", "CircuitPython Documentation", "https://docs.circuitpython.org/en/latest/", "html"),
        ("sparkfun_ohms", "SparkFun — Voltage, Current, Resistance", "https://learn.sparkfun.com/tutorials/voltage-current-resistance-and-ohm-law", "html"),
    ],
    16: [
        ("ros2_humble", "ROS 2 Documentation", "https://docs.ros.org/en/humble/", "html"),
        ("ros2_tutorials", "ROS 2 Tutorials", "https://docs.ros.org/en/humble/Tutorials.html", "html"),
        ("modern_robotics", "Modern Robotics (course materials free)", "https://modernrobotics.northwestern.edu/", "html"),
    ],
    17: [
        ("embedded_esp", "Espressif ESP-IDF Programming Guide", "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/", "html"),
        ("arduino_ref", "Arduino Language Reference", "https://www.arduino.cc/reference/en/", "html"),
        ("platformio", "PlatformIO Documentation", "https://docs.platformio.org/en/latest/", "html"),
    ],
    18: [
        ("openstax_stats", "OpenStax Introductory Statistics", "https://openstax.org/details/books/introductory-statistics-2e", "html"),
        ("reproducible", "Turing Way (reproducible research)", "https://the-turing-way.netlify.app/", "html"),
        ("zenodo", "Zenodo research sharing", "https://about.zenodo.org/", "html"),
    ],
    19: [
        ("openstax_psych", "OpenStax Psychology 2e", "https://openstax.org/details/books/psychology-2e", "html"),
        ("nih_mental", "NIH Mental Health information", "https://www.nimh.nih.gov/health", "html"),
        ("simply_psych", "Simply Psychology (açık makaleler index)", "https://www.simplypsychology.org/", "html"),
    ],
    20: [
        ("cogsci_stanford", "Stanford Encyclopedia — Cognitive Science", "https://plato.stanford.edu/entries/cognitive-science/", "html"),
        ("openmind", "OpenMind cognitive resources index", "https://www.openmind.org/", "html"),
        ("cog_wiki", "Cognitive science overview (WikiBooks)", "https://en.wikibooks.org/wiki/Cognitive_Psychology_and_Cognitive_Neuroscience", "html"),
    ],
    21: [
        ("slp", "Speech and Language Processing (Jurafsky)", "https://web.stanford.edu/~jurafsky/slp3/", "html"),
        ("nltk_book", "NLTK Book", "https://www.nltk.org/book/", "html"),
        ("universal_deps", "Universal Dependencies", "https://universaldependencies.org/", "html"),
    ],
    22: [
        ("sep_index", "Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu/contents.html", "html"),
        ("sep_epistemology", "SEP — Epistemology", "https://plato.stanford.edu/entries/epistemology/", "html"),
        ("iep_index", "Internet Encyclopedia of Philosophy", "https://iep.utm.edu/", "html"),
    ],
    23: [
        ("openstax_econ", "OpenStax Principles of Economics 3e", "https://openstax.org/details/books/principles-economics-3e", "html"),
        ("openstax_micro", "OpenStax Principles of Microeconomics 3e", "https://openstax.org/details/books/principles-microeconomics-3e", "html"),
        ("econlib", "Econlib — Library of Economics and Liberty", "https://www.econlib.org/", "html"),
    ],
    24: [
        ("gametheory_net", "GameTheory.net educational resources", "https://www.gametheory.net/", "html"),
        ("sep_game", "SEP — Game Theory", "https://plato.stanford.edu/entries/game-theory/", "html"),
        ("gametheory_101", "Game Theory 101 (William Spaniel notes index)", "https://gametheory101.com/", "html"),
    ],
}

DAL_SKILLS = {
    1: ["Python/JS/Rust temelleri", "veri yapıları", "yazılım pratiği"],
    2: ["algoritma tasarımı", "karmaşıklık", "graf/ağaç", "yarışma programlama"],
    3: ["YZ/ML", "sinir ağları", "pekiştirmeli öğrenme"],
    4: ["SQL", "SQLite/PostgreSQL", "indeksleme"],
    5: ["TCP/IP", "soket", "tarayıcı ağı (HPBN)"],
    6: ["işletim sistemleri", "süreç/bellek", "OSTEP"],
    7: ["OWASP Top 10", "güvenli kodlama", "ASVS"],
    8: ["yazılım mimarisi", "AOSA", "desenler"],
    9: ["Docker", "Kubernetes kavramları", "Missing Semester"],
    10: ["istatistik", "Bayes", "sklearn"],
    11: ["CS omurgası", "self-study haritası"],
    12: ["Nand2Tetris", "donanım-yazılım köprüsü"],
    13: ["kalkülüs/cebir (OpenStax)", "lineer cebir sezgi"],
    14: ["üniversite fiziği (OpenStax)", "Feynman Lectures erişimi"],
    15: ["DC/AC/yarıiletken (All About Circuits)"],
    16: ["ROS 2", "modern robotik ders omurgası"],
    17: ["gömülü (ESP-IDF)", "Arduino", "mekatronik OCW"],
    18: ["araştırma yöntemi", "Turing Way", "OWL"],
    19: ["psikoloji (OpenStax)", "NIMH sağlık bilgisi"],
    20: ["bilişsel bilim (SEP/OCW)"],
    21: ["NLP (SLP)", "NLTK", "Universal Dependencies"],
    22: ["felsefe (SEP)", "açık klasik metinler"],
    23: ["ekonomi (OpenStax)", "IMF basics"],
    24: ["oyun teorisi (Yale OYC / SEP)"],
}


def _fetch(url: str, dest: Path, timeout: int = 90) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RuzgarKutuphaneTelafi/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        if len(data) < 300:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except Exception as e:
        print("FETCH_FAIL", url[:70], type(e).__name__)
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
        for p in reader.pages[:MAX_PAGES]:
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
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    if not body.strip():
        body = f"Kaynak kayıtlı (telafi). Çevrimiçi: {meta.get('url')}\n"
    head = (
        f"# {meta['baslik']}\n\n"
        f"- kaynak_id: `{meta['kaynak_id']}`\n"
        f"- url: {meta.get('url')}\n"
        f"- dal: {meta.get('dal')}\n"
        f"- telafi: true\n\n---\n\n"
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
        if pos >= len(body) or n >= 80:
            break
    return n


def list_dal_dirs() -> list[tuple[int, Path]]:
    out = []
    for d in sorted(RAF.iterdir()):
        if not d.is_dir() or d.name.startswith("paket") or d.name.startswith("_"):
            continue
        m = re.match(r"^(\d+)_", d.name)
        if m:
            out.append((int(m.group(1)), d))
    return out


def key_matches_canonical(key: str) -> str | None:
    kl = key.lower()
    for ck, home in CANONICAL_HOME.items():
        if kl == ck.lower() or kl.startswith(ck.lower()) or ck.lower() in kl:
            return home
    return None


def purge_cross_copies() -> dict:
    report = {"removed": [], "kept": []}
    for num, dal_dir in list_dal_dirs():
        kat_path = dal_dir / "katalog.json"
        if not kat_path.exists():
            continue
        kat = json.loads(kat_path.read_text(encoding="utf-8"))
        srcs = kat.get("kaynaklar") or {}
        new_srcs = {}
        for key, meta in list(srcs.items()):
            home = key_matches_canonical(key)
            if home and home != dal_dir.name:
                # sil metin + raw
                metin = dal_dir / "metin" / key
                if metin.exists():
                    shutil.rmtree(metin, ignore_errors=True)
                raw = dal_dir / "raw"
                if raw.exists():
                    for p in raw.glob(f"{key}.*"):
                        p.unlink(missing_ok=True)
                report["removed"].append({"dal": dal_dir.name, "key": key, "home": home})
                print("PURGE", dal_dir.name, key, "→ home", home)
            else:
                new_srcs[key] = meta
                if home == dal_dir.name:
                    report["kept"].append({"dal": dal_dir.name, "key": key})
        kat["kaynaklar"] = new_srcs
        kat["sources"] = len(new_srcs)
        kat["ok_sources"] = sum(1 for s in new_srcs.values() if isinstance(s, dict) and s.get("ok"))
        kat["telafi_purge_utc"] = datetime.now(timezone.utc).isoformat()
        kat_path.write_text(json.dumps(kat, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def ingest_dal(num: int, dal_dir: Path) -> dict:
    items = DAL_OZEL.get(num) or []
    raf = dal_dir
    raw = raf / "raw"
    metin = raf / "metin"
    raf.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    metin.mkdir(parents=True, exist_ok=True)

    kat_path = raf / "katalog.json"
    kat = json.loads(kat_path.read_text(encoding="utf-8")) if kat_path.exists() else {
        "dal": dal_dir.name,
        "kaynaklar": {},
    }
    sources = kat.get("kaynaklar") or {}

    allowed = {k for k, *_ in items} if items else None
    # Liste tanımlıysa eski/zayıf yabancı anahtarları budar (01 hariç — items boş, dokunma)
    if allowed is not None:
        for old_key in list(sources.keys()):
            if old_key not in allowed:
                metin_old = metin / old_key
                if metin_old.exists():
                    shutil.rmtree(metin_old, ignore_errors=True)
                for p in raw.glob(f"{old_key}.*"):
                    p.unlink(missing_ok=True)
                sources.pop(old_key, None)
                print("DROP_STALE", dal_dir.name, old_key)

    for key, baslik, url, kind in items:
        if key in sources and sources[key].get("ok") and (metin / key).exists():
            print("KEEP", dal_dir.name, key)
            continue
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
            "kaynak_id": f"{dal_dir.name}_{key}",
            "baslik": baslik,
            "url": url,
            "dal": dal_dir.name,
            "ok": bool(body) or ok,
            "telafi": True,
        }
        meta["parca"] = _chunk_write(metin, key, body, meta)
        sources[key] = meta
        print(("OK" if meta["ok"] else "WEAK"), dal_dir.name, key, meta["parca"])

    # 01'de items boş — mevcut (purge sonrası) kalsın
    kat["kaynaklar"] = sources
    kat["sources"] = len(sources)
    kat["ok_sources"] = sum(1 for s in sources.values() if s.get("ok"))
    kat["skills"] = DAL_SKILLS.get(num, [])
    kat["telafi_utc"] = datetime.now(timezone.utc).isoformat()
    kat["telafi_notu"] = (
        "Çapraz-dal kopyalar silindi; bu dalda yalnız konu-özel yasal kaynaklar tutuluyor."
    )
    kat_path.write_text(json.dumps(kat, ensure_ascii=False, indent=2), encoding="utf-8")
    return kat


def patch_excel(num: int, kat: dict) -> None:
    files = list(DESK.glob(f"{num} - )*_F_karar.xlsx")) + list(DESK.glob(f"{num} -)*_F_karar.xlsx"))
    # also pattern without space variants
    if not files:
        for p in DESK.glob("*_F_karar.xlsx"):
            m = re.match(r"\s*(\d+)", p.name)
            if m and int(m.group(1)) == num:
                files.append(p)
    if not files:
        print("NO_EXCEL", num)
        return
    path = files[0]
    try:
        wb = load_workbook(path)
    except PermissionError:
        alt = path.with_name(path.stem + "_telafi.xlsx")
        shutil.copy2(path, alt)
        wb = load_workbook(alt)
        path = alt
    ws = wb.active
    # find/replace ÖZET block
    ozet_row = None
    for r in range(3, ws.max_row + 1):
        v = ws.cell(r, 1).value
        if isinstance(v, str) and v.upper() in ("ÖZET", "OZET"):
            ozet_row = r
            break
    if ozet_row is None:
        ozet_row = ws.max_row + 2
    else:
        for rr in range(ozet_row, ws.max_row + 1):
            for c in range(1, 8):
                ws.cell(rr, c).value = None
    n_src = kat.get("sources") or len(kat.get("kaynaklar") or {})
    n_ok = kat.get("ok_sources") or 0
    skills = kat.get("skills") or DAL_SKILLS.get(num, [])
    r = ozet_row
    ws.cell(r, 1).value = "ÖZET"
    ws.cell(r, 2).value = (
        f"TELAFİ uygulandı. Bu dalda {n_ok}/{n_src} benzersiz yasal kaynak var "
        f"(çapraz-dal kopyalar silindi). Konum: bilgisayar_eserleri/{kat.get('dal')}/"
    )
    r += 1
    ws.cell(r, 1).value = "RÜZGAR KAZANIMI"
    ws.cell(r, 2).value = "Bu dalın kendi kaynaklarıyla: " + " · ".join(skills)
    r += 1
    ws.cell(r, 1).value = "TARİH"
    ws.cell(r, 2).value = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC") + " (telafi)"
    r += 1
    ws.cell(r, 1).value = "DÜRÜSTLÜK"
    ws.cell(r, 2).value = (
        "Önceki turda ortak omurga (ODS/Erickson/CPH/OSTEP) birçok dala kopyalanmıştı; "
        "bu telafi ile her eser yalnız kendi ana dalında tutuluyor."
    )
    try:
        wb.save(path)
        print("EXCEL", path.name)
    except PermissionError:
        alt = path.with_name(path.stem + "_telafi.xlsx")
        wb.save(alt)
        print("EXCEL_ALT", alt.name)


def patch_index(summary: list[dict]) -> None:
    idx = DESK / "İNDEX.xlsx"
    wb = load_workbook(idx)
    ws = wb.active
    by_num = {s["num"]: s for s in summary}
    for r in range(3, ws.max_row + 1):
        try:
            num = int(ws.cell(r, 1).value)
        except Exception:
            continue
        s = by_num.get(num)
        if not s:
            continue
        ws.cell(r, 4).value = s.get("ok_sources") or 0
        ws.cell(r, 5).value = (
            f"TELAFİ · benzersiz yasal {s.get('ok_sources')}/{s.get('sources')} · "
            f"kopya yok · {', '.join((s.get('skills') or [])[:3])}"
        )
    row = ws.max_row + 2
    ws.cell(row, 1).value = "TELAFİ"
    ws.cell(row, 2).value = (
        "Çapraz-dal tekrarlar temizlendi. Her dala konu-özel yasal kaynaklar yerleştirildi. "
        "Önceki '100 tamam' iddiası kopya omurgaya dayanıyordu; bu satır dürüst durumu yansıtır."
    )
    row += 1
    ws.cell(row, 1).value = "TARİH"
    ws.cell(row, 2).value = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    try:
        wb.save(idx)
        print("INDEX updated")
    except PermissionError:
        alt = idx.with_name("İNDEX_TELAFI.xlsx")
        wb.save(alt)
        print("INDEX alt", alt)


def main() -> int:
    print("=== 1) PURGE çapraz kopyalar ===")
    purge = purge_cross_copies()
    print("removed", len(purge["removed"]), "kept_home", len(purge["kept"]))

    print("=== 2) Dala özel kaynaklar ===")
    summary = []
    for num, dal_dir in list_dal_dirs():
        print(f"\n---- {num} {dal_dir.name} ----")
        kat = ingest_dal(num, dal_dir)
        patch_excel(num, kat)
        summary.append(
            {
                "num": num,
                "dal": dal_dir.name,
                "sources": kat.get("sources"),
                "ok_sources": kat.get("ok_sources"),
                "skills": kat.get("skills"),
                "keys": list((kat.get("kaynaklar") or {}).keys()),
            }
        )

    print("=== 3) INDEX ===")
    patch_index(summary)

    out = {
        "purge_removed": len(purge["removed"]),
        "purge_detail": purge["removed"][:50],
        "dals": summary,
        "utc": datetime.now(timezone.utc).isoformat(),
    }
    (RAF / "TELAFI_RAPOR.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md = [
        "# Kütüphane telafi raporu",
        "",
        f"Tarih: {out['utc']}",
        "",
        f"Silinen çapraz kopya kaydı: {out['purge_removed']}",
        "",
        "| Dal | OK kaynak | Anahtarlar |",
        "|---|---:|---|",
    ]
    for s in summary:
        md.append(
            f"| {s['num']:02d} {s['dal']} | {s['ok_sources']}/{s['sources']} | "
            f"{', '.join(s['keys'][:8])} |"
        )
    md += [
        "",
        "## Dürüstlük",
        "Önceki turda ODS/Erickson/CPH/OSTEP ~23 dala kopyalanmıştı. "
        "Telafi: her kaynak tek ana dalda; diğer dallara konu-özel yasal eserler.",
    ]
    (RAF / "TELAFI_RAPOR.md").write_text("\n".join(md), encoding="utf-8")
    print("DONE telafi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
