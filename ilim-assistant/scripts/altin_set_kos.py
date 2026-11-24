#!/usr/bin/env python
"""K0 — Altın soru seti koşucusu (salt ölçüm; Rüzgar'ın hiçbir kodunu değiştirmez).

Kullanım:
  python scripts/altin_set_kos.py kos    --etiket baslangic [--raf fizik,din] [--limit 5] [--web] [--devam] [--bekle 4]
  python scripts/altin_set_kos.py rapor  --etiket baslangic
  python scripts/altin_set_kos.py el-puani --etiket baslangic [--adet 30]
  python scripts/altin_set_kos.py karsilastir --a baslangic --b k1_sonrasi [--raf din]
  python scripts/altin_set_kos.py din-rapor --etiket din_baslangic [--onceki din_baslangic]   # D1: ayrı din raporu
  python scripts/altin_set_kos.py din-sade  --etiket din_baslangic [--adet 30]              # (d) sadelik ajan puanı sayfası

Ölçülenler (soru başına): kapsama (anahtar grup eşleşmesi), geçti (>=0,6 ve "bulamadım" değil),
bulamadım (miss), ham_dokum, ümit-abi ön eki, gecikme, sağlayıcı, kütüphane isabeti.
Sonuçlar eval/altin_set/sonuclar/<etiket>.jsonl ; raporlar docs/ALTIN_SET_<etiket>.{md,json}.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import sys
import time
import urllib.request
import zlib
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import din_olcut  # noqa: E402  (D1 din ölçütleri)

ROOT = Path(__file__).resolve().parents[1]
SORULAR = ROOT / "eval" / "altin_set" / "sorular.json"
SONUC_DIR = ROOT / "eval" / "altin_set" / "sonuclar"
DOCS = ROOT / "docs"
RDOCS = ROOT.parent / "docs"  # çalışma alanı kökü docs/ (din raporları burada)
GECTI_ESIK = 0.6

_TR = str.maketrans(
    {"İ": "i", "I": "i", "ı": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g", "ü": "u", "Ü": "u",
     "ö": "o", "Ö": "o", "ç": "c", "Ç": "c", "â": "a", "Â": "a", "î": "i", "Î": "i", "û": "u",
     "Û": "u", "’": "'", "‘": "'", "`": "'", "²": "2"}
)
_HAM_RE = re.compile(
    r"ilim hazinesi|dogrudan pasaj|arsiv pasaj|kaynak pasaj|kutuphaneden okudugum pasaj"
    r"|=== ruzgar kutuphanesi|\(skor=|--- eser #",
    re.I,
)
_MISS_RE = re.compile(r"bulamadim|ogretir misin|cevabini bulamad", re.I)


def fold(s: str) -> str:
    return (s or "").translate(_TR).lower()


def _kw_match(kw: str, text: str) -> bool:
    k = fold(kw)
    if not k:
        return False
    if len(k) <= 3 and re.fullmatch(r"[a-z0-9]+", k):
        return re.search(rf"(?<![a-z0-9]){re.escape(k)}(?![a-z0-9])", text) is not None
    return k in text


def kapsama(cevap: str, gruplar: list[list[str]]) -> tuple[float, list[bool]]:
    t = fold(cevap)
    hit = [any(_kw_match(k, t) for k in g) for g in gruplar]
    return (sum(hit) / len(hit) if hit else 0.0), hit


def yukle_sorular(raflar: set[str] | None = None) -> list[dict]:
    d = json.loads(SORULAR.read_text(encoding="utf-8"))
    out = []
    for raf, items in d["raflar"].items():
        if raflar and raf not in raflar:
            continue
        for i, it in enumerate(items, 1):
            q, gr = it[0], it[1]
            meta = it[2] if len(it) > 2 and isinstance(it[2], dict) else {}
            out.append({"id": f"{raf}-{i:02d}", "raf": raf, "soru": q, "gruplar": gr,
                        "alt": meta.get("alt", ""), "kaynak_iste": bool(meta.get("kaynak")),
                        "cizgi": bool(meta.get("cizgi"))})
    return out


T0 = time.time()  # süreç başlangıcı: koşu başına benzersiz cihaz kapsamı için


def sor(base: str, q: str, etiket: str, web: bool, timeout: float) -> tuple[dict, float]:
    body = json.dumps(
        {
            "message": q,
            "use_web": bool(web),
            "mode": "genel",
            "history": [],
            # Her koşu AYRI cihaz kapsamı: önceki koşunun cevapları «sohbet hafızası» olarak geri dönmesin
            # (aynı soru eski «bulamadım» cevabını hafızadan alıp aramayı atlıyordu).
            # + soru başına ayrı kapsam: «bulamadım → öğretir misin?» bekleme durumu sonraki soruyu yutmasın.
            "device_id": f"altin-set-{etiket}-{int(T0)}-{zlib.crc32(q.encode('utf-8')):08x}",
            "conversation_id": f"altin-set-{etiket}",
        }
    ).encode("utf-8")
    req = urllib.request.Request(base + "/api/chat/full", body, {"Content-Type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.load(r)
    return data, time.time() - t


def kayit_uret(s: dict, data: dict, dt: float) -> dict:
    cevap = (data.get("full_reply") or "").strip()
    cov, hit = kapsama(cevap, s["gruplar"])
    f = fold(cevap)
    miss = bool(_MISS_RE.search(f)) or len(cevap) < 15
    tt = data.get("tur_teshis") or {}
    return {
        "id": s["id"], "raf": s["raf"], "soru": s["soru"], "cevap": cevap,
        "kapsama": round(cov, 3), "gruplar_hit": hit,
        "gecti": bool(cov >= GECTI_ESIK and not miss),
        "bulamadim": miss,
        "ham_dokum": bool(_HAM_RE.search(f)) or len(cevap) > 2500,
        "umit_abi_on_ek": f.startswith("umit abi"),
        "uzunluk": len(cevap),
        "gecikme_sn": round(dt, 2),
        "saglayici": tt.get("provider"),
        "kutuphane_hits": tt.get("hits_count"),
        "top_scores": (tt.get("top_scores") or [])[:3],
        "alt": s.get("alt", ""), "kaynak_iste": bool(s.get("kaynak_iste")), "cizgi": bool(s.get("cizgi")),
        "kaynak_kunye": (tt.get("kaynak_kunye") or [])[:8],
        "k3": tt.get("k3"),
        "hata": None,
    }


def cmd_kos(a) -> int:
    SONUC_DIR.mkdir(parents=True, exist_ok=True)
    out = SONUC_DIR / f"{a.etiket}.jsonl"
    raflar = set(a.raf.split(",")) if a.raf else None
    sorular = yukle_sorular(raflar)
    if getattr(a, "ids", ""):
        _ids = {x.strip() for x in a.ids.split(",") if x.strip()}
        sorular = [s for s in sorular if s["id"] in _ids]
    if a.limit:
        per = defaultdict(int)
        sec = []
        for s in sorular:
            if per[s["raf"]] < a.limit:
                per[s["raf"]] += 1
                sec.append(s)
        sorular = sec
    yapilan = set()
    if a.devam and out.exists():
        for ln in out.read_text(encoding="utf-8").splitlines():
            try:
                yapilan.add(json.loads(ln)["id"])
            except Exception:
                pass
    elif out.exists():
        out.unlink()
    bekleyen = [s for s in sorular if s["id"] not in yapilan]
    print(f"[altin-set] {len(bekleyen)} soru koşulacak (web={'açık' if a.web else 'kapalı'}) -> {out}", flush=True)
    with out.open("a", encoding="utf-8") as fh:
        for n, s in enumerate(bekleyen, 1):
            try:
                data, dt = sor(a.url, s["soru"], a.etiket, a.web, a.timeout)
                k = kayit_uret(s, data, dt)
            except Exception as e:  # noqa: BLE001
                k = {"id": s["id"], "raf": s["raf"], "soru": s["soru"], "cevap": "", "kapsama": 0.0,
                     "gruplar_hit": [], "gecti": False, "bulamadim": True, "ham_dokum": False,
                     "umit_abi_on_ek": False, "uzunluk": 0, "gecikme_sn": a.timeout,
                     "saglayici": None, "kutuphane_hits": None, "top_scores": [], "hata": str(e)[:200],
                     "alt": s.get("alt", ""), "kaynak_iste": bool(s.get("kaynak_iste")),
                     "cizgi": bool(s.get("cizgi")), "kaynak_kunye": [], "k3": None}
            fh.write(json.dumps(k, ensure_ascii=False) + "\n")
            fh.flush()
            isaret = "OK " if k["gecti"] else ("YOK" if k["bulamadim"] else "ZAY")
            print(f"[{n:3d}/{len(bekleyen)}] {isaret} {k['id']:<18} kap={k['kapsama']:.2f} {k['gecikme_sn']:5.1f}s {k['saglayici']}", flush=True)
            if getattr(a, "bekle", 0) and n < len(bekleyen):
                time.sleep(a.bekle)  # bulut kota/dakika sınırını aşmamak için (ölçümü bozmaz)
    cmd_rapor(a)
    return 0


def oku(etiket: str) -> list[dict]:
    p = SONUC_DIR / f"{etiket}.jsonl"
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    for r in rows:  # dedektör güncellenince eski kayıtlar da yeniden değerlendirilir
        r["ham_dokum"] = bool(_HAM_RE.search(fold(r.get("cevap", "")))) or r.get("uzunluk", 0) > 2500
        if r.get("raf") == "din":
            r["din"] = din_olcut.kaynak_denetim(r.get("cevap", ""), r.get("kaynak_kunye") or [], r.get("soru", ""))
    return rows


def ozet(rows: list[dict]) -> dict:
    def pct(x, n):
        return round(100.0 * x / n, 1) if n else 0.0

    n = len(rows)
    lat = sorted(r["gecikme_sn"] for r in rows) or [0]
    p90 = lat[min(len(lat) - 1, int(0.9 * len(lat)))]
    raflar: dict[str, dict] = {}
    for raf in sorted({r["raf"] for r in rows}):
        rr = [r for r in rows if r["raf"] == raf]
        raflar[raf] = {
            "n": len(rr),
            "gecti_pct": pct(sum(r["gecti"] for r in rr), len(rr)),
            "bulamadim_pct": pct(sum(r["bulamadim"] for r in rr), len(rr)),
            "ort_kapsama": round(statistics.mean(r["kapsama"] for r in rr), 3),
            "ham_dokum": sum(r["ham_dokum"] for r in rr),
            "umit_abi_pct": pct(sum(r["umit_abi_on_ek"] for r in rr), len(rr)),
            "medyan_sn": round(statistics.median(r["gecikme_sn"] for r in rr), 2),
        }
    return {
        "n": n,
        "gecti_pct": pct(sum(r["gecti"] for r in rows), n),
        "bulamadim_pct": pct(sum(r["bulamadim"] for r in rows), n),
        "ort_kapsama": round(statistics.mean(r["kapsama"] for r in rows), 3) if rows else 0,
        "ham_dokum": sum(r["ham_dokum"] for r in rows),
        "umit_abi_pct": pct(sum(r["umit_abi_on_ek"] for r in rows), n),
        "medyan_sn": round(statistics.median(lat), 2),
        "p90_sn": round(p90, 2),
        "saglayici": dict(Counter(str(r["saglayici"]) for r in rows).most_common()),
        "hata_sayisi": sum(1 for r in rows if r.get("hata")),
        "raflar": raflar,
    }


def cmd_rapor(a) -> int:
    rows = oku(a.etiket)
    o = ozet(rows)
    DOCS.mkdir(exist_ok=True)
    stem = f"ALTIN_SET_{a.etiket.upper()}_{date.today().isoformat()}"
    (DOCS / f"{stem}.json").write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")
    L = [f"# Altın Set — {a.etiket} ({date.today().isoformat()})", "",
         f"Soru: **{o['n']}** · Geçti: **%{o['gecti_pct']}** · Bulamadım: **%{o['bulamadim_pct']}** · "
         f"Ort. kapsama: **{o['ort_kapsama']}** · Ham döküm: **{o['ham_dokum']}** · "
         f"«Ümit abi» ön eki: **%{o['umit_abi_pct']}** · Medyan: **{o['medyan_sn']} sn** · P90: **{o['p90_sn']} sn** · "
         f"Hata: **{o['hata_sayisi']}**", "",
         f"Sağlayıcılar: {o['saglayici']}", "",
         "| Raf | N | Geçti % | Bulamadım % | Kapsama | Ham | Ümit abi % | Medyan sn |",
         "|-----|---|--------|------------|---------|-----|-----------|-----------|"]
    for raf, v in o["raflar"].items():
        L.append(f"| {raf} | {v['n']} | {v['gecti_pct']} | {v['bulamadim_pct']} | {v['ort_kapsama']} | "
                 f"{v['ham_dokum']} | {v['umit_abi_pct']} | {v['medyan_sn']} |")
    L += ["", "## Kaçırılan sorular (geçmeyenler)", ""]
    for r in rows:
        if not r["gecti"]:
            etiket = "BULAMADIM" if r["bulamadim"] else f"kap={r['kapsama']}"
            L.append(f"- `{r['id']}` {r['soru']} → {etiket} · {r['saglayici']} · {r['gecikme_sn']} sn")
    (DOCS / f"{stem}.md").write_text("\n".join(L), encoding="utf-8")
    print(f"[altin-set] rapor: docs/{stem}.md")
    print(f"  geçti %{o['gecti_pct']} · bulamadım %{o['bulamadim_pct']} · kapsama {o['ort_kapsama']} · "
          f"ham {o['ham_dokum']} · medyan {o['medyan_sn']} sn")
    return 0


def cmd_el_puani(a) -> int:
    rows = oku(a.etiket)
    rnd = random.Random(7)
    by = defaultdict(list)
    for r in rows:
        by[r["raf"]].append(r)
    sec: list[dict] = []
    for raf, rr in sorted(by.items()):
        sec += rnd.sample(rr, min(len(rr), max(2, a.adet // max(1, len(by)))))
    rnd.shuffle(sec)
    sec = sec[: a.adet]
    L = [f"# Doğallık el puanı — {a.etiket}", "",
         "Her cevap için 1–5 yaz: **1** = saçma/alakasız/ham arşiv çıktısı · **3** = doğru ama kitap gibi/ağır · "
         "**5** = doğal, sade, doğru, iyi bir öğretmen gibi.", ""]
    for i, r in enumerate(sec, 1):
        L += [f"## {i}. `{r['id']}` — {r['soru']}", "", f"> {r['cevap'][:1200].replace(chr(10), chr(10) + '> ')}", "",
              "Puan (1–5): ____    Not: ____", ""]
    out = DOCS / f"ALTIN_SET_EL_PUANI_{a.etiket.upper()}_{date.today().isoformat()}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"[altin-set] el puanı sayfası: {out}")
    return 0


def cmd_karsilastir(a) -> int:
    _rf = set(a.raf.split(",")) if getattr(a, "raf", "") else None
    A = ozet([r for r in oku(a.a) if not _rf or r["raf"] in _rf])
    B = ozet([r for r in oku(a.b) if not _rf or r["raf"] in _rf])
    print(f"{'ölçüt':<16}{a.a:>14}{a.b:>14}")
    for k in ("gecti_pct", "bulamadim_pct", "ort_kapsama", "ham_dokum", "umit_abi_pct", "medyan_sn", "p90_sn"):
        print(f"{k:<16}{A[k]:>14}{B[k]:>14}")
    print("\nraf bazında geçti %:")
    for raf in A["raflar"]:
        print(f"  {raf:<14}{A['raflar'][raf]['gecti_pct']:>8}{B['raflar'].get(raf, {}).get('gecti_pct', '-'):>8}")
    return 0


# ---------------------------------------------------------------------------
# D1 — din raporu (ayrı), karşılaştırma, sadelik (ajan puanı)
# ---------------------------------------------------------------------------
def din_ozet(rows: list[dict], sade: dict | None = None) -> dict:
    """Yalnız din satırları için D1 ölçütleri."""
    rr = [r for r in rows if r.get("raf") == "din"]
    n = len(rr)

    def pct(x, m):
        return round(100.0 * x / m, 1) if m else 0.0

    kv = [r for r in rr if r.get("kaynak_iste")]
    kunye_kv = sum(1 for r in kv if (r.get("din") or {}).get("kunye_var"))
    kunye_all = sum(1 for r in rr if (r.get("din") or {}).get("kunye_var"))
    coklu = sum(1 for r in rr if (r.get("din") or {}).get("eser_sayisi", 0) >= 2)
    coklu_kv = sum(1 for r in kv if (r.get("din") or {}).get("eser_sayisi", 0) >= 2)
    supheli_soru = [r["id"] for r in rr if (r.get("din") or {}).get("supheli")]
    supheli_atif = sum(len((r.get("din") or {}).get("supheli") or []) for r in rr)
    alt: dict[str, dict] = {}
    for a in sorted({r.get("alt") or "temel" for r in rr}):
        x = [r for r in rr if (r.get("alt") or "temel") == a]
        alt[a] = {"n": len(x), "gecti_pct": pct(sum(r["gecti"] for r in x), len(x)),
                  "bulamadim_pct": pct(sum(r["bulamadim"] for r in x), len(x))}
    lat = sorted(r["gecikme_sn"] for r in rr) or [0]
    sade = sade or {}
    sd = [float(v) for k, v in sade.items() if any(r["id"] == k for r in rr)]
    return {
        "n": n,
        "gecti_pct": pct(sum(r["gecti"] for r in rr), n),
        "bulamadim_pct": pct(sum(r["bulamadim"] for r in rr), n),
        "ort_kapsama": round(statistics.mean(r["kapsama"] for r in rr), 3) if rr else 0,
        "kaynak_iste_n": len(kv),
        "kaynak_verme_pct": pct(kunye_kv, len(kv)),
        "kunye_genel_pct": pct(kunye_all, n),
        "coklu_eser_pct": pct(coklu, n),
        "coklu_eser_kaynak_iste_pct": pct(coklu_kv, len(kv)),
        "uydurma_supheli_soru": len(supheli_soru),
        "uydurma_supheli_atif": supheli_atif,
        "uydurma_supheli_idler": supheli_soru,
        "sade_ort": round(statistics.mean(sd), 2) if sd else None,
        "sade_n": len(sd),
        "medyan_sn": round(statistics.median(lat), 2),
        "p90_sn": round(lat[min(len(lat) - 1, int(0.9 * len(lat)))], 2),
        "alt": alt,
        "saglayici": dict(Counter(str(r["saglayici"]) for r in rr).most_common()),
    }


def _sade_yukle(etiket: str) -> dict:
    p = SONUC_DIR / f"{etiket}.sade.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def cmd_din_rapor(a) -> int:
    rows = [r for r in oku(a.etiket) if r["raf"] == "din"]
    o = din_ozet(rows, _sade_yukle(a.etiket))
    onceki = None
    if getattr(a, "onceki", ""):
        orows = [r for r in oku(a.onceki) if r["raf"] == "din"]
        onceki = din_ozet(orows, _sade_yukle(a.onceki))
    stem = f"DIN_RAPOR_{a.etiket.upper()}_{date.today().isoformat()}"
    L = [f"# Din raporu — {a.etiket} ({date.today().isoformat()})", "",
         "Yalnız **din rafı** (web kapalı). Koşucu: `scripts/altin_set_kos.py din-rapor`; ölçütler: `scripts/din_olcut.py`.", ""]

    def satir(ad, anahtar, fmt="{}"):
        v = o.get(anahtar)
        if onceki is None:
            return f"| {ad} | {fmt.format(v) if v is not None else '—'} |"
        w = onceki.get(anahtar)
        return f"| {ad} | {fmt.format(w) if w is not None else '—'} | {fmt.format(v) if v is not None else '—'} |"

    if onceki is None:
        L += ["| Ölçüt | Değer |", "|---|---:|"]
    else:
        L += [f"| Ölçüt | {a.onceki} | {a.etiket} |", "|---|---:|---:|"]
    L += [satir("Soru sayısı", "n"),
          satir("Doğru cevap %", "gecti_pct", "%{}"),
          satir("«Bulamadım» %", "bulamadim_pct", "%{}"),
          satir("Ort. kapsama", "ort_kapsama"),
          satir("(a) «Kaynak göster» varyantlarında künye gelen %", "kaynak_verme_pct", "%{}"),
          satir("(a) Tüm din cevaplarında doğrulanmış künye %", "kunye_genel_pct", "%{}"),
          satir("(b) Çoklu eser (≥2 farklı eser anışı) %", "coklu_eser_pct", "%{}"),
          satir("(b) Çoklu eser — yalnız «kaynak göster» varyantlarında %", "coklu_eser_kaynak_iste_pct", "%{}"),
          satir("(c) Uydurma kaynak şüphesi — soru sayısı", "uydurma_supheli_soru"),
          satir("(c) Uydurma kaynak şüphesi — atıf sayısı", "uydurma_supheli_atif"),
          satir("(d) Sadelik ajan puanı (1–5)", "sade_ort"),
          satir("Medyan sn", "medyan_sn"), satir("P90 sn", "p90_sn"), ""]
    L += [f"Sağlayıcılar: {o['saglayici']}", "", "## Alt-raf bazında", "",
          "| Alt-raf | N | Doğru % | Bulamadım % |", "|---|---:|---:|---:|"]
    for k, v in o["alt"].items():
        L.append(f"| {k} | {v['n']} | {v['gecti_pct']} | {v['bulamadim_pct']} |")
    L += ["", "## «Kaynak göster» varyantları", "",
          "| id | Soru | Künye? | Eser sayısı | Şüpheli atıf |", "|---|---|:-:|---:|---|"]
    for r in rows:
        if r.get("kaynak_iste"):
            d = r.get("din") or {}
            L.append(f"| `{r['id']}` | {r['soru'][:60]} | {'✔' if d.get('kunye_var') else '✘'} | {d.get('eser_sayisi', 0)} | {'; '.join(d.get('supheli') or [])[:90]} |")
    L += ["", "## Uydurma kaynak şüphesi (ayrıntı — denetleyici sezgiseldir, el ile doğrula)", ""]
    sup = [r for r in rows if (r.get("din") or {}).get("supheli")]
    if not sup:
        L.append("- (yok)")
    for r in sup:
        d = r["din"]
        L.append(f"- `{r['id']}` {r['soru'][:70]} → şüpheli: {d['supheli']} · doğrulanan: {d['dogrulanan'][:3]} · künyeler: "
                 f"{[k.get('eser_ar') or k.get('yol_adi') for k in (r.get('kaynak_kunye') or [])][:4]}")
    cz = [r for r in rows if r.get("cizgi")]
    L += ["", "## Ehl-i Sünnet çizgisi soruları — el/ajan incelemesi için cevaplar", ""]
    for r in cz:
        L += [f"### `{r['id']}` {r['soru']}", f"*(doğru={'evet' if r['gecti'] else 'hayır'}, sağlayıcı={r['saglayici']})*", "",
              "> " + (r["cevap"][:900].replace("\n", "\n> ")), ""]
    L += ["## Geçmeyen sorular", ""]
    for r in rows:
        if not r["gecti"]:
            e = "BULAMADIM" if r["bulamadim"] else f"kap={r['kapsama']}"
            L.append(f"- `{r['id']}` {r['soru']} → {e} · {r['saglayici']} · hits={r.get('kutuphane_hits')}")
    RDOCS.mkdir(exist_ok=True)
    out = RDOCS / f"{stem}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    (RDOCS / f"{stem}.json").write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[din] rapor: {out}")
    print(f"  doğru %{o['gecti_pct']} · bulamadım %{o['bulamadim_pct']} · kaynak verme %{o['kaynak_verme_pct']} · "
          f"çoklu eser %{o['coklu_eser_pct']} · uydurma şüphe {o['uydurma_supheli_soru']} soru/{o['uydurma_supheli_atif']} atıf")
    return 0


def cmd_din_sade(a) -> int:
    rows = [r for r in oku(a.etiket) if r["raf"] == "din"]
    rnd = random.Random(11)
    sec = rnd.sample(rows, min(len(rows), a.adet))
    sec.sort(key=lambda r: r["id"])
    L = [f"# Din sadelik puanı (ajan puanı) — {a.etiket}", "",
         "1 = ağır/kitap gibi/Arapça yığını/anlaşılmaz · 3 = doğru ama ağır · 5 = herkesin anlayacağı sadelikte, vakur ve net. "
         f"Puanlar `eval/altin_set/sonuclar/{a.etiket}.sade.json` içine {{id: puan}} olarak yazılır.", ""]
    for r in sec:
        L += [f"## `{r['id']}` — {r['soru']}", "", "> " + r["cevap"][:1100].replace("\n", "\n> "), ""]
    RDOCS.mkdir(exist_ok=True)
    out = RDOCS / f"DIN_SADE_PUAN_{a.etiket.upper()}_{date.today().isoformat()}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("[din] sadelik sayfası:", out, "· ids:", ",".join(r["id"] for r in sec))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    k = sp.add_parser("kos")
    k.add_argument("--etiket", required=True)
    k.add_argument("--raf", default="")
    k.add_argument("--limit", type=int, default=0)
    k.add_argument("--ids", default="", help="yalnız bu soru kimlikleri (virgüllü), ör. fizik-11,kimya-18")
    k.add_argument("--web", action="store_true")
    k.add_argument("--devam", action="store_true")
    k.add_argument("--url", default="http://127.0.0.1:8779")
    k.add_argument("--timeout", type=float, default=150.0)
    k.add_argument("--bekle", type=float, default=0.0, help="sorular arası bekleme sn (bulut dakika kotası için)")
    r = sp.add_parser("rapor")
    r.add_argument("--etiket", required=True)
    e = sp.add_parser("el-puani")
    e.add_argument("--etiket", required=True)
    e.add_argument("--adet", type=int, default=30)
    c = sp.add_parser("karsilastir")
    c.add_argument("--a", required=True)
    c.add_argument("--b", required=True)
    c.add_argument("--raf", default="", help="yalnız bu raflar (virgüllü), ör. din")
    dr = sp.add_parser("din-rapor")
    dr.add_argument("--etiket", required=True)
    dr.add_argument("--onceki", default="")
    ds = sp.add_parser("din-sade")
    ds.add_argument("--etiket", required=True)
    ds.add_argument("--adet", type=int, default=30)
    a = p.parse_args()
    return {"kos": cmd_kos, "rapor": cmd_rapor, "el-puani": cmd_el_puani, "karsilastir": cmd_karsilastir,
            "din-rapor": cmd_din_rapor, "din-sade": cmd_din_sade}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
