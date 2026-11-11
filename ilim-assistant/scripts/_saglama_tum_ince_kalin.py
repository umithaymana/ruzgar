# -*- coding: utf-8 -*-
"""Sağlama: tüm ince bilgisayar eserlerini kalınlaştır (MIN_PARCA≥40).

Katalogdaki ince kayıtları tarar; seed URL + BFS ile deepen_kalin uygular.
Kesilirse aynı rapordan devam (kalın olanları atlar).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _ileri_i_madde_kalin as i

MIN = i.MIN_PARCA
RAF = i.RAF
REPORT = RAF / "25_SAGLAMA_INCE_KALIN_RAPOR.json"

# Bilinen açık/yasal seed'ler — katalog URL'si zayıfsa
SEED_OVERRIDE: dict[str, str] = {
    "crafting_interpreters": "https://craftinginterpreters.com/contents.html",
    "rust_book": "https://doc.rust-lang.org/book/",
    "zero2prod": "https://www.zero2prod.com/",
    "ydkjs": "https://github.com/getify/You-Dont-Know-JS",
    "producing_oss": "https://producingoss.com/",
    "ts_handbook": "https://www.typescriptlang.org/docs/handbook/intro.html",
    "tour_of_go": "https://go.dev/tour/",
    "vue_guide": "https://vuejs.org/guide/introduction.html",
    "angular_docs": "https://angular.dev/overview",
    "scala3_book": "https://docs.scala-lang.org/scala3/book/introduction.html",
    "ms_csharp": "https://learn.microsoft.com/en-us/dotnet/csharp/",
    "nndl": "https://neuralnetworksanddeeplearning.com/",
    "aima_site": "https://aima.cs.berkeley.edu/",
    "d2l": "https://d2l.ai/",
    "sqlite_lang": "https://www.sqlite.org/lang.html",
    "pg_tutorial": "https://www.postgresql.org/docs/current/tutorial.html",
    "cmu_15445": "https://15445.courses.cs.cmu.edu/fall2023/schedule.html",
    "hpbn": "https://hpbn.co/",
    "bind9_docs": "https://bind9.readthedocs.io/en/latest/",
    "beej_net": "https://beej.us/guide/bgnet/html/",
    "beej_ipc": "https://beej.us/guide/bgipc/html/split/",
    "systemsapproach": "https://book.systemsapproach.org/",
    "mdn_http": "https://developer.mozilla.org/en-US/docs/Web/HTTP",
    "ostep": "https://pages.cs.wisc.edu/~remzi/OSTEP/",
    "lfs": "https://www.linuxfromscratch.org/lfs/view/stable/",
    "xv6": "https://pdos.csail.mit.edu/6.828/2023/xv6.html",
    "cs50": "https://cs50.harvard.edu/x/2024/",
    "nand2tetris": "https://www.nand2tetris.org/",
    "pandas": "https://pandas.pydata.org/docs/",
    "sklearn": "https://scikit-learn.org/stable/user_guide.html",
    "ansible": "https://docs.ansible.com/",
    "docker": "https://docs.docker.com/",
    "terraform": "https://developer.hashicorp.com/terraform/docs",
    "aosa": "https://aosabook.org/en/",
    "twelve_factor": "https://12factor.net/",
}


def _parca(meta: dict, dal: Path, key: str) -> int:
    p = int(meta.get("parca") or meta.get("parca_sayisi") or 0)
    if p > 0:
        return p
    d = dal / "metin" / key
    if d.is_dir():
        return len(list(d.glob("*.md")))
    return 0


def _seed_from_md(dal: Path, key: str) -> str:
    d = dal / "metin" / key
    if not d.is_dir():
        return ""
    files = sorted(d.glob("*.md"))
    if not files:
        return ""
    text = files[0].read_text(encoding="utf-8", errors="replace")[:4000]
    m = re.search(r"https?://[^\s\)\]\"']+", text)
    return m.group(0).rstrip(".,;") if m else ""


def iter_thin() -> list[dict]:
    out: list[dict] = []
    for dal in sorted(p for p in RAF.iterdir() if p.is_dir() and p.name[:1].isdigit()):
        kat = dal / "katalog.json"
        if not kat.is_file():
            continue
        data = json.loads(kat.read_text(encoding="utf-8"))
        for key, meta in (data.get("kaynaklar") or {}).items():
            parca = _parca(meta, dal, key)
            if parca >= MIN:
                continue
            url = (meta.get("url") or "").strip()
            if not url:
                url = SEED_OVERRIDE.get(key, "") or _seed_from_md(dal, key)
            out.append(
                {
                    "dal": dal.name,
                    "key": key,
                    "parca": parca,
                    "url": url,
                    "baslik": meta.get("baslik") or key,
                }
            )
    return out


def chapter_urls(seed: str) -> list[str]:
    """Bilinen kitap/ders desenleri — BFS yetmezse sabit bölüm listesi."""
    out: list[str] = []
    if "py4e.com/html3" in seed:
        names = [
            "01-intro", "02-variables", "03-conditional", "04-functions", "05-iterations",
            "06-strings", "07-files", "08-lists", "09-dictionaries", "10-tuples",
            "11-regex", "12-network", "13-web", "14-objects", "15-database", "16-viz",
        ]
        out += [f"https://www.py4e.com/html3/{n}" for n in names]
    if "automatetheboringstuff.com" in seed:
        out += [f"https://automatetheboringstuff.com/2e/chapter{n}/" for n in range(0, 21)]
    if "craftinginterpreters.com" in seed:
        pages = [
            "contents.html", "welcome.html", "introduction.html", "a-map-of-the-territory.html",
            "the-javascript-stack.html", "scanning.html", "representing-code.html",
            "parsing-expressions.html", "evaluating-expressions.html", "statements-and-state.html",
            "control-flow.html", "functions.html", "resolving-and-binding.html", "classes.html",
            "inheritance.html", "a-bytecode-virtual-machine.html", "chunks-of-bytecode.html",
            "a-virtual-machine.html", "scanning-on-demand.html", "compiling-expressions.html",
            "types-of-values.html", "strings.html", "hash-tables.html", "calls-and-functions.html",
            "closures.html", "garbage-collection.html", "classes-and-instances.html",
            "methods-and-initializers.html", "superclasses.html", "optimization.html",
        ]
        out += [f"https://craftinginterpreters.com/{p}" for p in pages]
    if "doc.rust-lang.org/book" in seed:
        out += [f"https://doc.rust-lang.org/book/ch{n:02d}-00.html" for n in range(1, 22)]
    if "go.dev/tour" in seed:
        out += [f"https://go.dev/tour/welcome/{n}" for n in range(1, 25)]
        out += [f"https://go.dev/tour/basics/{n}" for n in range(1, 18)]
        out += [f"https://go.dev/tour/flowcontrol/{n}" for n in range(1, 14)]
        out += [f"https://go.dev/tour/moretypes/{n}" for n in range(1, 27)]
        out += [f"https://go.dev/tour/methods/{n}" for n in range(1, 26)]
        out += [f"https://go.dev/tour/concurrency/{n}" for n in range(1, 12)]
    if "sqlite.org/lang" in seed or "sqlite.org" in seed:
        out += [
            "https://www.sqlite.org/lang.html",
            "https://www.sqlite.org/lang_select.html",
            "https://www.sqlite.org/lang_insert.html",
            "https://www.sqlite.org/lang_update.html",
            "https://www.sqlite.org/lang_delete.html",
            "https://www.sqlite.org/lang_createtable.html",
            "https://www.sqlite.org/lang_altertable.html",
            "https://www.sqlite.org/lang_transaction.html",
            "https://www.sqlite.org/lang_with.html",
            "https://www.sqlite.org/lang_corefunc.html",
            "https://www.sqlite.org/lang_aggfunc.html",
            "https://www.sqlite.org/lang_datefunc.html",
            "https://www.sqlite.org/lang_expr.html",
            "https://www.sqlite.org/pragma.html",
            "https://www.sqlite.org/fts5.html",
            "https://www.sqlite.org/json1.html",
            "https://www.sqlite.org/foreignkeys.html",
            "https://www.sqlite.org/queryplanner.html",
            "https://www.sqlite.org/optoverview.html",
            "https://www.sqlite.org/datatype3.html",
        ]
    if "hpbn.co" in seed:
        out += [
            "https://hpbn.co/", "https://hpbn.co/primer-on-latency-and-bandwidth/",
            "https://hpbn.co/building-blocks-of-tcp/", "https://hpbn.co/tls/",
            "https://hpbn.co/http-history/", "https://hpbn.co/http1x/",
            "https://hpbn.co/http2/", "https://hpbn.co/brief-history-of-http/",
            "https://hpbn.co/xhr-xhr2/", "https://hpbn.co/server-sent-events-sse/",
            "https://hpbn.co/websocket/", "https://hpbn.co/webrtc/",
            "https://hpbn.co/transport-layer-security-tls/",
            "https://hpbn.co/optimizing-for-mobile-networks/",
            "https://hpbn.co/http2/", "https://hpbn.co/performance-toolkit/",
        ]
    if "d2l.ai" in seed:
        out += [f"https://d2l.ai/chapter_introduction/index.html"]
        out += [
            "https://d2l.ai/chapter_preliminaries/ndarray.html",
            "https://d2l.ai/chapter_preliminaries/pandas.html",
            "https://d2l.ai/chapter_linear-networks/linear-regression.html",
            "https://d2l.ai/chapter_multilayer-perceptrons/mlp.html",
            "https://d2l.ai/chapter_convolutional-neural-networks/lenet.html",
            "https://d2l.ai/chapter_recurrent-neural-networks/rnn.html",
            "https://d2l.ai/chapter_attention-mechanisms-and-transformers/index.html",
            "https://d2l.ai/chapter_optimization/optimization-intro.html",
            "https://d2l.ai/chapter_computational-performance/hybridize.html",
            "https://d2l.ai/chapter_computer-vision/index.html",
            "https://d2l.ai/chapter_natural-language-processing-pretraining/index.html",
            "https://d2l.ai/chapter_recommender-systems/index.html",
            "https://d2l.ai/chapter_generative-adversarial-networks/gan.html",
        ]
    if "neuralnetworksanddeeplearning.com" in seed:
        out += [
            "https://neuralnetworksanddeeplearning.com/",
            "https://neuralnetworksanddeeplearning.com/chap1.html",
            "https://neuralnetworksanddeeplearning.com/chap2.html",
            "https://neuralnetworksanddeeplearning.com/chap3.html",
            "https://neuralnetworksanddeeplearning.com/chap4.html",
            "https://neuralnetworksanddeeplearning.com/chap5.html",
            "https://neuralnetworksanddeeplearning.com/chap6.html",
            "https://neuralnetworksanddeeplearning.com/app1.html",
            "https://neuralnetworksanddeeplearning.com/app2.html",
        ]
    if "getify/You-Dont-Know-JS" in seed or "You-Dont-Know-JS" in seed:
        books = ["get-started", "scope-closures", "objects-classes", "types-grammar", "sync-async", "es-next-beyond"]
        for b in books:
            out += [
                f"https://raw.githubusercontent.com/getify/You-Dont-Know-JS/2nd-ed/{b}/README.md",
                f"https://raw.githubusercontent.com/getify/You-Dont-Know-JS/2nd-ed/{b}/ch1.md",
                f"https://raw.githubusercontent.com/getify/You-Dont-Know-JS/2nd-ed/{b}/ch2.md",
                f"https://raw.githubusercontent.com/getify/You-Dont-Know-JS/2nd-ed/{b}/ch3.md",
                f"https://raw.githubusercontent.com/getify/You-Dont-Know-JS/2nd-ed/{b}/ch4.md",
            ]
    return out


def expand_urls(seed: str) -> list[str]:
    if not seed:
        return []
    urls = [seed]
    urls.extend(chapter_urls(seed))
    # GitHub repo root → raw README + docs
    if "github.com" in seed and "/blob/" not in seed and "/raw/" not in seed:
        parts = seed.rstrip("/").split("/")
        if len(parts) >= 5:
            owner, repo = parts[3], parts[4]
            urls += [
                f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md",
                f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md",
                f"https://github.com/{owner}/{repo}",
            ]
    # BFS same-host links (depth 2) — PDF tek dosya
    if seed.lower().endswith(".pdf") or ".pdf?" in seed.lower():
        return i.uniq(urls, cap=i.URL_CAP)
    try:
        host = seed.split("/")[2]
    except IndexError:
        return i.uniq(urls)

    def pred(u: str) -> bool:
        if not u.startswith("http"):
            return False
        if host not in u:
            return False
        bad = (".js", ".css", ".png", ".jpg", ".svg", ".zip", ".woff", ".ico")
        return not any(u.lower().endswith(b) for b in bad)

    more = i.bfs([seed], pred, limit=70, max_depth=2)
    urls.extend(more)
    return i.uniq(urls, cap=i.URL_CAP)


def thick_pdf(dal: str, key: str, baslik: str, seed: str) -> dict:
    """Tek PDF indir → metin çıkar → kalın chunk."""
    from datetime import datetime, timezone

    from pypdf import PdfReader

    from kutuphane_bb_dalga_b_tam_eser import _chunk_write, _update_katalog

    dal_path = RAF / dal
    raw = dal_path / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    data = i._fetch(seed, timeout=90)
    if not data:
        return {"parca": 0, "ok": False, "html_pages": 0, "error": "pdf_fetch_fail"}
    pdf_path = raw / f"{key}.pdf"
    pdf_path.write_bytes(data)
    try:
        reader = PdfReader(str(pdf_path))
        pages = []
        for n, page in enumerate(reader.pages):
            try:
                t = page.extract_text() or ""
            except Exception:
                t = ""
            if len(t.strip()) > 40:
                pages.append(f"\n\n## PDF sayfa {n+1}\n\n{t}")
            # tüm metin dolu sayfalar — erken kesme yok (ince PDF kalmasın)
            if len(pages) >= 500:
                break
        body = "\n".join(pages)
    except Exception as e:
        return {"parca": 0, "ok": False, "html_pages": 0, "error": f"pdf_parse:{type(e).__name__}"}
    meta = {
        "kaynak_id": f"{dal}_{key}",
        "baslik": baslik,
        "url": seed,
        "dal": dal,
        "truncated": False,
        "pdf_pages": len(pages),
        "extracted_pages": len(pages),
        "html_pages": len(pages),
        "html_expected": len(pages),
        "updated_utc": datetime.now(timezone.utc).isoformat(),
    }
    meta["parca"] = _chunk_write(dal_path, key, body, meta)
    meta["parca_sayisi"] = meta["parca"]
    kalin_ok = meta["parca"] >= MIN and len(pages) >= 5 and len(body) > 5000
    meta["ok"] = kalin_ok
    meta["tam_eser"] = kalin_ok
    meta["derin_yesil"] = kalin_ok
    _update_katalog(dal_path, key, meta)
    print("DONE_PDF", key, "pages", len(pages), "parca", meta["parca"], "dy", kalin_ok, flush=True)
    return meta


def main() -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    except Exception:
        pass

    i.BODY_TARGET = MIN * 12000
    thin = iter_thin()
    print(f"THIN_TOTAL {len(thin)}", flush=True)

    prev: dict = {}
    if REPORT.is_file():
        try:
            prev = json.loads(REPORT.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            prev = {}
    done_keys = set((prev.get("kalin_keys") or []))

    results: dict = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "min_parca": MIN,
        "items": {},
        "kalin_keys": list(done_keys),
        "failed": [],
        "skipped_no_url": [],
    }

    for n, item in enumerate(thin, 1):
        dal, key = item["dal"], item["key"]
        tag = f"{dal}/{key}"
        if tag in done_keys:
            print(f"SKIP_DONE {n}/{len(thin)} {tag}", flush=True)
            continue
        seed = (item["url"] or "").strip() or SEED_OVERRIDE.get(key, "")
        if not seed:
            print(f"NO_URL {n}/{len(thin)} {tag}", flush=True)
            results["skipped_no_url"].append(tag)
            continue
        print(f"=== {n}/{len(thin)} {tag} seed={seed[:90]}", flush=True)
        if seed.lower().endswith(".pdf") or ".pdf?" in seed.lower():
            meta = thick_pdf(dal, key, item["baslik"], seed)
        else:
            urls = expand_urls(seed)
            print(f"URLS {len(urls)}", flush=True)
            meta = i.thick(dal, key, item["baslik"], seed, urls, expected_pages=22)
        parca = int(meta.get("parca") or 0)
        results["items"][tag] = {
            "parca": parca,
            "pages": meta.get("html_pages"),
            "ok": bool(meta.get("derin_yesil")),
            "url": seed,
        }
        if parca >= MIN:
            done_keys.add(tag)
            results["kalin_keys"] = sorted(done_keys)
            # failed listesinden düş
            results["failed"] = [f for f in results["failed"] if f.get("tag") != tag]
            print(f"KALIN_OK {tag} parca={parca}", flush=True)
        else:
            results["failed"] = [f for f in results["failed"] if f.get("tag") != tag]
            results["failed"].append({"tag": tag, "parca": parca, "pages": meta.get("html_pages")})
            print(f"STILL_THIN {tag} parca={parca}", flush=True)
        # checkpoint
        results["ts"] = datetime.now(timezone.utc).isoformat()
        results["kalin"] = len(results["kalin_keys"])
        results["n_failed"] = len(results["failed"])
        REPORT.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # final recount
    left = iter_thin()
    results["thin_left"] = len(left)
    results["thin_left_sample"] = [
        f"{t['dal']}/{t['key']}:{t['parca']}" for t in sorted(left, key=lambda x: x["parca"])[:40]
    ]
    REPORT.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("DONE_SAGLAMA", "kalin", len(results["kalin_keys"]), "thin_left", len(left), flush=True)
    return 0 if len(left) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
