# -*- coding: utf-8 -*-
"""Kur'an ayet katmanı → RAG markdown batch.

Kaynak: knowledge/ilim/din/01_kuran/ayetler.jsonl (Diyanet mushaf + meal).
Anlık yol zaten jsonl kullanır; RAG yalnız *.md indeksler — bu script boşluğu kapatır.

Politika: Meal çeviridir, fetva/tefsir değildir. Ayet numarası uydurulmaz.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KURAN = ROOT / "knowledge" / "ilim" / "din" / "01_kuran"
AYETLER = KURAN / "ayetler.jsonl"
INCR = KURAN / "incremental" / "ayetler"
ORTAK = ROOT / "knowledge" / "ortak_kaynak" / "KAYNAK_KAYIT.json"
MANIFEST = KURAN / "manifest_ayet_rag.json"

# ~15 ayet/batch → RAG 900 char dilimlerinde sure/ayet bağlamı bozulmaz
BATCH = 15


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_ayetler() -> list[dict]:
    rows: list[dict] = []
    if not AYETLER.is_file():
        raise SystemExit(f"eksik: {AYETLER}")
    for line in AYETLER.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    rows.sort(key=lambda r: (int(r.get("sure_no") or 0), int(r.get("ayet_no") or 0)))
    return rows


def _meal(r: dict) -> str:
    for k in ("meal_tr", "meal_tr_kuran_yolu", "meal_tr_diyanet"):
        t = (r.get(k) or "").strip()
        if t:
            return t
    return ""


def _ayet_block(r: dict) -> str:
    s = int(r.get("sure_no") or 0)
    a = int(r.get("ayet_no") or 0)
    sure = (r.get("sure_adi_tr") or f"Sure {s}").strip()
    ar = (r.get("text_ar") or "").strip()
    meal = _meal(r)
    lines = [
        f"## {sure} {s}:{a}",
        "",
        ar if ar else "(Arapça metin yok)",
        "",
        f"Meal (Kur'an Yolu / Diyanet): {meal}" if meal else "Meal: (yok)",
        "",
        f"ref: kuran#{s}:{a} · kaynak=Diyanet mushaf+meal · meal=çeviri (fetva değil)",
        "",
    ]
    return "\n".join(lines)


def _write_batches(rows: list[dict]) -> tuple[int, int]:
    if INCR.exists():
        for old in INCR.glob("kuran_ayet_batch_*.md"):
            old.unlink()
    INCR.mkdir(parents=True, exist_ok=True)
    n_batch = 0
    n_ayet = 0
    for i in range(0, len(rows), BATCH):
        part = rows[i : i + BATCH]
        if not part:
            continue
        n_batch += 1
        n_ayet += len(part)
        s0 = int(part[0].get("sure_no") or 0)
        a0 = int(part[0].get("ayet_no") or 0)
        s1 = int(part[-1].get("sure_no") or 0)
        a1 = int(part[-1].get("ayet_no") or 0)
        body = [
            f"# Kur'an-ı Kerim — ayet paketi {n_batch:04d}",
            "",
            f"Kapsam: {s0}:{a0} – {s1}:{a1}",
            "Kaynak: Diyanet mushaf (AR) + Kur'an Yolu / Diyanet meal (TR).",
            "Not: Meal çeviridir; tefsir/fetva değildir. Ayet numarası uydurulmaz.",
            "",
        ]
        for r in part:
            body.append(_ayet_block(r))
        (INCR / f"kuran_ayet_batch_{n_batch:04d}.md").write_text(
            "\n".join(body).rstrip() + "\n", encoding="utf-8"
        )
    return n_batch, n_ayet


def _update_ortak(n_batch: int, n_ayet: int) -> None:
    data = json.loads(ORTAK.read_text(encoding="utf-8")) if ORTAK.is_file() else {"kayitlar": []}
    rows = data.get("kayitlar") or []
    entry = {
        "kaynak_id": "kuran_ayetler",
        "kaynak_adi": "Kur'an-ı Kerim (mushaf + meal)",
        "yazar": None,
        "ilim_alani": "kuran",
        "eser_turu": "mushaf_meal",
        "dil": "ar+tr",
        "yayin": "Diyanet İşleri Başkanlığı",
        "cilt": None,
        "bolum": None,
        "sayfa": None,
        "dosya_yolu": "knowledge/ilim/din/01_kuran/incremental/ayetler",
        "guvenilirlik": "yuksek",
        "kaynak_sinifi": "kalici",
        "durum": "hazir",
        "not": (
            f"RAG batch: {n_batch} paket · {n_ayet} ayet. "
            "Meal çeviridir; fetva/tefsir değildir."
        ),
    }
    found = False
    for r in rows:
        if r.get("kaynak_id") == "kuran_ayetler":
            r.update(entry)
            found = True
            break
    if not found:
        rows.append(entry)
    data["kayitlar"] = rows
    data["guncelleme"] = _utc()
    ORTAK.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _update_readme() -> None:
    readme = KURAN / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    block = (
        "\n## RAG ayet batch\n\n"
        "| Dosya | Açıklama |\n"
        "|-------|----------|\n"
        "| `incremental/ayetler/kuran_ayet_batch_*.md` | "
        "6236 ayet — AR + meal (RAG `*.md` indeksi) |\n"
        "| Script | `scripts/faz1_kuran_ayet_rag_ingest.py` |\n"
    )
    if "incremental/ayetler/" in text:
        return
    readme.write_text(text.rstrip() + "\n" + block, encoding="utf-8")


def main() -> int:
    rows = _load_ayetler()
    if len(rows) < 6000:
        raise SystemExit(f"beklenen ~6236 ayet, bulundu: {len(rows)}")
    n_batch, n_ayet = _write_batches(rows)
    man = {
        "collection": "din_01_kuran_ayet_rag",
        "source": "ayetler.jsonl",
        "batch_dir": "knowledge/ilim/din/01_kuran/incremental/ayetler",
        "ayet_count": n_ayet,
        "batch_count": n_batch,
        "batch_size": BATCH,
        "durum": "hazir",
        "politika": "Meal çeviridir; fetva/tefsir değil. Ayet uydurma yasak.",
        "updated_utc": _utc(),
    }
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _update_ortak(n_batch, n_ayet)
    _update_readme()
    print(f"[ok] ayet={n_ayet} batch={n_batch} dir={INCR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
