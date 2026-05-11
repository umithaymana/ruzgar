"""
Tarih hafızası için çok kaynaklı veri toplama (Vikiveri / Wikidata ağırlıklı).

- Wikidata SPARQL: Osmanlı, Türkiye Cumhuriyeti, Selçuklu, savaşlar, olaylar,
  arkeolojik yerler, Türk tarihiyle ilişkili kişiler ve varlıklar (sayfalı).
- İsteğe bağlı: Digital Ottomans demo (akademik koleksiyon meta + kronoloji).

Çıktı: `tarih_kaynak_buyuk.json` (varsayılan büyük derleme) veya `tarih_kaynak.json` (demo).

Vikiveri verileri CC0; madde açıklamaları topluluk katkılıdır. Öğretim/RAG için uygun;
tıbbi/hukuki kesin iddia yerine kaynak bağlantısı verilir.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ilim_assistant.rag_store import _KNOWLEDGE_ROOT

_DEFAULT_DEMO = _KNOWLEDGE_ROOT / "TARIH_VE_KULTUR" / "tarih_kaynak.json"
_DEFAULT_BUYUK = _KNOWLEDGE_ROOT / "TARIH_VE_KULTUR" / "tarih_kaynak_buyuk.json"

_WD_ENDPOINT = "https://query.wikidata.org/sparql"
_PAGE = 200
_SLEEP_SEC = 0.45
_MAX_OFFSET_PER_QUERY = 80_000

_DEMO_URLS = (
    "https://digitalottomans.github.io/demo/assets/data/metadata.json",
    "https://digitalottomans.github.io/demo/assets/data/timelinejs.json",
)


def _fetch_json_url(url: str, timeout: float = 120.0) -> Any:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "RuzgarIlimAssistant/1.0 (education RAG; local) Python-urllib"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _wikidata_sparql(query: str, timeout: float = 300.0) -> list[dict[str, Any]]:
    body = urllib.parse.urlencode({"query": query, "format": "json"}).encode("utf-8")
    req = urllib.request.Request(
        _WD_ENDPOINT,
        data=body,
        method="POST",
        headers={
            "User-Agent": "RuzgarIlimAssistant/1.0 (SPARQL; Turkish history education; local)",
            "Accept": "application/sparql-results+json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    last_err: BaseException | None = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
            j = json.loads(raw.decode("utf-8"))
            return list(j.get("results", {}).get("bindings") or [])
        except json.JSONDecodeError as e:
            last_err = e
            time.sleep(2.5 * (attempt + 1))
            continue
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code == 429 or e.code >= 500:
                time.sleep(3.0 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
            time.sleep(2.0 * (attempt + 1))
    if last_err:
        if isinstance(last_err, json.JSONDecodeError):
            print("UYARI: Wikidata yanıtı bozuk/kesik (JSON); bu sayfa atlanıyor.", flush=True)
            return []
        raise last_err
    return []


def _binding_str(b: dict[str, Any], key: str) -> str:
    cell = b.get(key)
    if not cell or not isinstance(cell, dict):
        return ""
    return str(cell.get("value") or "").strip()


def _qid_from_uri(uri: str) -> str:
    if "/entity/" in uri:
        return uri.rsplit("/", 1)[-1].strip()
    if uri.startswith("Q") and uri[1:].isdigit():
        return uri
    return ""


def _paged_wd(
    *,
    name_tr: str,
    query_base: str,
    seen: set[str],
    sink: list[dict[str, Any]],
    min_new_per_page: int = 1,
    stop_at_total: int | None = None,
) -> int:
    """query_base içinde __LIMIT__ ve __OFFSET__ yer tutucuları olmalı. Eklenen benzersiz Q sayısı."""
    added = 0
    offset = 0
    while offset <= _MAX_OFFSET_PER_QUERY:
        if stop_at_total is not None and len(sink) >= stop_at_total:
            break
        q = query_base.replace("__LIMIT__", str(_PAGE)).replace("__OFFSET__", str(offset))
        rows = _wikidata_sparql(q)
        new_here = 0
        for b in rows:
            if stop_at_total is not None and len(sink) >= stop_at_total:
                return added
            qid = _qid_from_uri(_binding_str(b, "item"))
            if not qid or qid in seen:
                continue
            seen.add(qid)
            title = (_binding_str(b, "itemLabel") or qid)[:500]
            desc = _binding_str(b, "itemDescription")
            extra: list[str] = []
            for k in ("time", "start", "end", "point"):
                v = _binding_str(b, k)
                if v:
                    extra.append(f"{k}: {v}")
            body_parts = [desc] if desc else []
            body_parts.extend(extra)
            body_parts.append(f"Konu: {name_tr}")
            body_parts.append(f"Vikiveri: https://www.wikidata.org/wiki/{qid}")
            body = "\n".join(x for x in body_parts if x).strip() or f"Konu: {name_tr}\nVikiveri: https://www.wikidata.org/wiki/{qid}"
            sink.append(
                {
                    "title": title,
                    "body": body[:12000],
                    "category": "wikidata",
                    "wd_q": qid,
                    "topic_tr": name_tr,
                }
            )
            added += 1
            new_here += 1
        print(f"  … {name_tr[:40]}… +{new_here} (ara toplam {len(sink)})", flush=True)
        if len(rows) < _PAGE or new_here < min_new_per_page:
            break
        offset += _PAGE
        time.sleep(_SLEEP_SEC)
    return added


# --- SPARQL şablonları (SERVICE wikibase:label: tr,en) ---
# Q referansları: Osmanlı Q12560, TR Q43, Büyük Selçuklu Q27384, Anadolu Selçuklusu Q166181,
# Türk Kurtuluş Savaşı Q32193, savaş sınıfı Q178561, tarihsel olay Q1190554, arkeolojik yer Q839954,
# İlk Türk Kağanlığı Q163547, Uygur Q27280, Hun devleti Q133873, Göktürkler toplumu Q132752

_WD_QUERIES: list[tuple[str, str]] = [
    (
        "Osmanlı İmparatorluğu — ülke (P17) kapsamındaki varlıklar",
        """SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE {
  ?item wdt:P17 wd:Q12560 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}
LIMIT __LIMIT__ OFFSET __OFFSET__""",
    ),
    (
        "Türkiye Cumhuriyeti — ülke (P17) kapsamındaki varlıklar",
        """SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE {
  ?item wdt:P17 wd:Q43 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}
LIMIT __LIMIT__ OFFSET __OFFSET__""",
    ),
    (
        "Büyük Selçuklu İmparatorluğu — ülke ilişkisi",
        """SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE {
  ?item wdt:P17 wd:Q27384 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}
LIMIT __LIMIT__ OFFSET __OFFSET__""",
    ),
    (
        "Anadolu Selçuklu Beyliği / Saltanatı — ülke ilişkisi",
        """SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE {
  ?item wdt:P17 wd:Q166181 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}
LIMIT __LIMIT__ OFFSET __OFFSET__""",
    ),
    (
        "İlk ve İkinci Türk Kağanlığı / erken kağanlık toprakları (ülke)",
        """SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE {
  { ?item wdt:P17 wd:Q163547 } UNION { ?item wdt:P17 wd:Q163549 } .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}
LIMIT __LIMIT__ OFFSET __OFFSET__""",
    ),
    (
        "Uygur Kağanlığı ve Hun devleti alanı (ülke)",
        """SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE {
  { ?item wdt:P17 wd:Q27280 } UNION { ?item wdt:P17 wd:Q133873 } .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}
LIMIT __LIMIT__ OFFSET __OFFSET__""",
    ),
    (
        "Türk Kurtuluş Savaşı — çatışmaya katılım (P607)",
        """SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE {
  ?item wdt:P607 wd:Q32193 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}
LIMIT __LIMIT__ OFFSET __OFFSET__""",
    ),
    (
        "Osmanlı dönemi savaşları (Osmanlı İmparatorluğu taraf olarak P710)",
        """SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE {
  ?item wdt:P31/wdt:P279* wd:Q178561 .
  ?item wdt:P710 wd:Q12560 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}
LIMIT __LIMIT__ OFFSET __OFFSET__""",
    ),
    (
        "Türkiye ile ilişkili tarihsel olaylar (ülke veya yer: Türkiye)",
        """SELECT DISTINCT ?item ?itemLabel ?itemDescription ?time WHERE {
  ?item wdt:P31 wd:Q1190554 .
  { ?item wdt:P17 wd:Q43 } UNION { ?item wdt:P276 ?l . ?l wdt:P17 wd:Q43 } .
  OPTIONAL { ?item wdt:P585 ?time . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}
LIMIT __LIMIT__ OFFSET __OFFSET__""",
    ),
    (
        "Türkiye’de arkeolojik / tarihî yer",
        """SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE {
  ?item wdt:P31/wdt:P279* wd:Q839954 .
  ?item wdt:P17 wd:Q43 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}
LIMIT __LIMIT__ OFFSET __OFFSET__""",
    ),
    (
        "Osmanlı tebaası / vatandaşı kişiler (insan)",
        """SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE {
  ?item wdt:P31 wd:Q5 .
  ?item wdt:P27 wd:Q12560 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}
LIMIT __LIMIT__ OFFSET __OFFSET__""",
    ),
    (
        "Cumhuriyet öncesi Türkiye vatandaşı kişiler (doğum yılı <1950 veya bilinmiyor)",
        """SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE {
  ?item wdt:P31 wd:Q5 .
  ?item wdt:P27 wd:Q43 .
  OPTIONAL { ?item wdt:P569 ?bd . }
  FILTER(!BOUND(?bd) || YEAR(?bd) < 1950)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}
LIMIT __LIMIT__ OFFSET __OFFSET__""",
    ),
    (
        "Türk boyları / Göktürklerle ilişkili etnik grup (insan, P172)",
        """SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE {
  ?item wdt:P31 wd:Q5 .
  { ?item wdt:P172 wd:Q132752 } UNION { ?item wdt:P172 wd:Q133250 } .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}
LIMIT __LIMIT__ OFFSET __OFFSET__""",
    ),
]


def _norm_title(t: str) -> str:
    return " ".join((t or "").lower().split())


def _body_from_metadata_obj(obj: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("description", "date", "subject", "location", "source", "type", "reference_url"):
        v = obj.get(key)
        if v is None or (isinstance(v, str) and not v.strip()):
            continue
        parts.append(f"{key}: {str(v).strip()}")
    return "\n".join(parts) if parts else "(Özet yok)"


def _body_from_timeline_event(ev: dict[str, Any]) -> str:
    parts: list[str] = []
    tx = ev.get("text") or {}
    if isinstance(tx, dict):
        t2 = (tx.get("text") or "").strip()
        if t2:
            parts.append(t2)
    sd = ev.get("start_date")
    if isinstance(sd, dict):
        y, m, d = sd.get("year"), sd.get("month"), sd.get("day")
        date_bits = [x for x in (y, m, d) if x]
        if date_bits:
            parts.insert(0, "Tarih: " + "-".join(str(x) for x in date_bits))
    med = ev.get("media") or {}
    if isinstance(med, dict):
        link = med.get("link") or med.get("url")
        if link:
            parts.append(f"Bağlantı: {link}")
    return "\n".join(parts) if parts else "(Özet yok)"


def build_wikidata_buyuk_entries(
    *,
    target_min: int = 10_000,
    with_digital_ottomans: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    seen: set[str] = set()
    entries: list[dict[str, Any]] = []
    per_query_counts: list[tuple[str, int]] = []

    stop_cap = max(target_min + 2000, int(target_min * 1.2))
    print(f"Vikiveri toplama başlıyor (hedef ≥{target_min} benzersiz kayıt, üst sınır ~{stop_cap})…", flush=True)
    for name_tr, qtpl in _WD_QUERIES:
        if len(entries) >= target_min:
            print(f"Hedefe ulaşıldı ({len(entries)}), ek sorgular atlanıyor.", flush=True)
            break
        n = _paged_wd(
            name_tr=name_tr,
            query_base=qtpl,
            seen=seen,
            sink=entries,
            min_new_per_page=1,
            stop_at_total=stop_cap,
        )
        per_query_counts.append((name_tr, n))
        time.sleep(_SLEEP_SEC)

    # Hedef altındaysa: geniş Türkiye vatandaşı (doğum <1980)
    if len(entries) < target_min:
        print(f"Hedef altı ({len(entries)}), tamamlama sorgusu çalışıyor…", flush=True)
        fill_tpl = """SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE {
  ?item wdt:P31 wd:Q5 .
  ?item wdt:P27 wd:Q43 .
  OPTIONAL { ?item wdt:P569 ?bd . }
  FILTER(!BOUND(?bd) || YEAR(?bd) < 1980)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}
LIMIT __LIMIT__ OFFSET __OFFSET__"""
        n2 = _paged_wd(
            name_tr="Türkiye Cumhuriyeti — geniş kişi tamamlama (öncelik: tarihsel)",
            query_base=fill_tpl,
            seen=seen,
            sink=entries,
            min_new_per_page=1,
            stop_at_total=stop_cap,
        )
        per_query_counts.append(("fill_tr_citizens_pre1980", n2))

    if with_digital_ottomans:
        try:
            meta = _fetch_json_url(_DEMO_URLS[0])
            objects = meta.get("objects") if isinstance(meta, dict) else None
            if isinstance(objects, list):
                for obj in objects:
                    if not isinstance(obj, dict):
                        continue
                    title = str(obj.get("title") or "").strip()
                    if not title:
                        continue
                    k = "do:" + _norm_title(title)
                    if k in seen:
                        continue
                    seen.add(k)
                    entries.append(
                        {
                            "title": title[:500],
                            "body": _body_from_metadata_obj(obj)[:12000],
                            "category": "digital_ottomans_meta",
                        }
                    )
            tl = _fetch_json_url(_DEMO_URLS[1])
            events = tl.get("events") if isinstance(tl, dict) else None
            if isinstance(events, list):
                for ev in events:
                    if not isinstance(ev, dict):
                        continue
                    tx = ev.get("text") or {}
                    headline = str(tx.get("headline") or "").strip() if isinstance(tx, dict) else ""
                    if not headline:
                        continue
                    k = "do:" + _norm_title(headline)
                    if k in seen:
                        continue
                    seen.add(k)
                    entries.append(
                        {
                            "title": headline[:500],
                            "body": _body_from_timeline_event(ev)[:12000],
                            "category": "digital_ottomans_timeline",
                        }
                    )
        except OSError:
            pass

    meta_block = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target_min_entries": target_min,
        "wikidata_endpoint": _WD_ENDPOINT,
        "per_wikidata_query_counts": [{"topic": a, "added": b} for a, b in per_query_counts],
        "sources": [
            {
                "name": "Wikidata (SPARQL)",
                "license": "CC0 — https://creativecommons.org/publicdomain/zero/1.0/",
                "note": "Etiket ve açıklamalar çok dilli topluluk verisidir; kritik iddialar için birincil kaynak araştırılmalıdır.",
            },
        ],
    }
    if with_digital_ottomans:
        meta_block["sources"].append(
            {
                "name": "Digital Ottomans — demo",
                "urls": list(_DEMO_URLS),
            }
        )
    return entries, meta_block


def load_tarih_entries_for_ingest(path: Path) -> list[tuple[str, str]]:
    """JSON -> (başlık, gövde) listesi (ingest için)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out: list[tuple[str, str]] = []
    if isinstance(data, list):
        for it in data:
            if not isinstance(it, dict):
                continue
            t = str(it.get("title") or it.get("baslik") or it.get("headline") or "").strip()
            b = str(it.get("body") or it.get("metin") or it.get("text") or it.get("description") or "").strip()
            if not t:
                continue
            out.append((t[:500], (b or "(Metin boş)")[:12000]))
        return out
    if not isinstance(data, dict):
        return out
    entries = data.get("entries")
    if isinstance(entries, list):
        for it in entries:
            if not isinstance(it, dict):
                continue
            t = str(it.get("title") or it.get("baslik") or "").strip()
            b = str(it.get("body") or it.get("metin") or "").strip()
            if not t:
                continue
            out.append((t[:500], (b or "(Metin boş)")[:12000]))
        if out:
            return out
    objects = data.get("objects")
    if isinstance(objects, list):
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            t = str(obj.get("title") or "").strip()
            if not t:
                continue
            out.append((t[:500], _body_from_metadata_obj(obj)[:12000]))
        return out
    events = data.get("events")
    if isinstance(events, list):
        for ev in events:
            if not isinstance(ev, dict):
                continue
            tx = ev.get("text") or {}
            headline = str(tx.get("headline") or "").strip() if isinstance(tx, dict) else ""
            if not headline:
                continue
            out.append((headline[:500], _body_from_timeline_event(ev)[:12000]))
        return out
    return out


def write_tarih_kaynak_buyuk(
    dst: str | Path | None = None,
    *,
    target_min: int = 10_000,
    with_digital_ottomans: bool = True,
) -> Path:
    out = Path(dst) if dst else _DEFAULT_BUYUK
    entries, meta = build_wikidata_buyuk_entries(
        target_min=target_min,
        with_digital_ottomans=with_digital_ottomans,
    )
    meta["entry_count"] = len(entries)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"_meta": meta, "entries": entries}, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def write_tarih_kaynak_demo(dst: str | Path | None = None) -> Path:
    """Eski küçük demo birleştirmesi (tarih_kaynak.json)."""
    out = Path(dst) if dst else _DEFAULT_DEMO
    seen: set[str] = set()
    entries: list[dict[str, Any]] = []
    meta = {"built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "sources": []}

    meta_o = _fetch_json_url(_DEMO_URLS[0])
    objects = meta_o.get("objects") if isinstance(meta_o, dict) else None
    if isinstance(objects, list):
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            title = str(obj.get("title") or "").strip()
            if not title:
                continue
            k = _norm_title(title)
            if k in seen:
                continue
            seen.add(k)
            entries.append({"title": title[:500], "body": _body_from_metadata_obj(obj)[:12000], "category": "demo"})
    tl = _fetch_json_url(_DEMO_URLS[1])
    events = tl.get("events") if isinstance(tl, dict) else None
    if isinstance(events, list):
        for ev in events:
            if not isinstance(ev, dict):
                continue
            tx = ev.get("text") or {}
            headline = str(tx.get("headline") or "").strip() if isinstance(tx, dict) else ""
            if not headline:
                continue
            k = _norm_title(headline)
            if k in seen:
                continue
            seen.add(k)
            entries.append(
                {"title": headline[:500], "body": _body_from_timeline_event(ev)[:12000], "category": "demo"}
            )
    meta["sources"] = [{"name": "Digital Ottomans demo", "urls": list(_DEMO_URLS)}]
    meta["entry_count"] = len(entries)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"_meta": meta, "entries": entries}, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Tarih kaynak JSON üret (Wikidata + isteğe bağlı demo)")
    p.add_argument(
        "--mode",
        choices=("buyuk", "demo"),
        default="buyuk",
        help="buyuk: Wikidata ağırlıklı büyük set; demo: yalnızca Digital Ottomans.",
    )
    p.add_argument("--output", type=str, default="", help="Çıktı dosyası (boşsa mod varsayılanı)")
    p.add_argument("--target-min", type=int, default=10_000, help="buyuk modunda hedef minimum kayıt")
    p.add_argument(
        "--no-digital-ottomans",
        action="store_true",
        help="buyuk modunda Digital Ottomans ekini kapat",
    )
    args = p.parse_args()
    if args.mode == "demo":
        path = write_tarih_kaynak_demo(args.output or None)
    else:
        path = write_tarih_kaynak_buyuk(
            args.output or None,
            target_min=max(1000, int(args.target_min)),
            with_digital_ottomans=not args.no_digital_ottomans,
        )
    n = len(json.loads(path.read_text(encoding="utf-8")).get("entries") or [])
    print(f"OK: {n} kayıt yazıldı -> {path}")


if __name__ == "__main__":
    main()
