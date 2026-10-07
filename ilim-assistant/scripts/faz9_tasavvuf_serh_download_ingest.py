# -*- coding: utf-8 -*-
"""Tasavvuf şerh rafı — İbnü'l-Arabî Fusûs şerhleri (Câmî, Kâşânî, Kayserî).

Politika: Fetva yok. Sayfa/cilt uydurma yasak.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "arsiv" / "_ilim_staging" / "09_tasavvuf" / "raw"
SERH = ROOT / "knowledge" / "ilim" / "din" / "09_ahlak_tasavvuf" / "serh_ve_aciklama"
ORTAK = ROOT / "knowledge" / "ortak_kaynak" / "KAYNAK_KAYIT.json"
KAV = ROOT / "knowledge" / "ilim" / "din" / "09_ahlak_tasavvuf" / "kavramlar_tasavvuf.jsonl"

CHUNK = 1600
OVERLAP = 120
BATCH = 20

SERHLER = [
    {
        "id": "jami_sharh_fusus",
        "eser_tr": "Şerh-i Fusûs (Câmî)",
        "eser_ar": "شرح فصوص الحكم للجامي",
        "yazar": "Abdurrahman Câmî (ö. 898/1492)",
        "ilgili_eser_id": "ibn_arabi_fusus",
        "dil": "ar",
        "ia_id": "sharh_al_jami_ala_fusus_al-hikam",
        "files": ["SJAFH_01_djvu.txt"],
        "kaynak": "Internet Archive (Arapça OCR — Câmî şerhi)",
        "aliases": [
            "jami fusus",
            "cami fusus",
            "şerh fusus",
            "serh fusus",
            "jami sharh",
        ],
        "metin": (
            "Abdurrahman Câmî'nin Fusûsu'l-Hikem şerhi. "
            "İbnü'l-Arabî metninin klasik açıklamalarından biridir. "
            "Kütüphanede Arapça OCR vardır (güven orta; sayfa uydurma yasak). "
            "Rüzgar fetva vermez."
        ),
        "kavram_baslik": "serh fusus",
        "kavram_not": "Şerh rafı — Câmî; fetva yok.",
    },
    {
        "id": "kashani_sharh_fusus",
        "eser_tr": "Şerh-i Fusûs (Kâşânî)",
        "eser_ar": "شرح فصوص الحكم للقاشاني",
        "yazar": "Abdürrezzâk Kâşânî (ö. ~730/1330)",
        "ilgili_eser_id": "ibn_arabi_fusus",
        "dil": "ar",
        "ia_id": "sharh-fusus-kashani",
        "files": ["Sharh Fusus Kashani_djvu.txt"],
        "kaynak": "Internet Archive (Arapça OCR — Kâşânî şerhi)",
        "aliases": [
            "kashani fusus",
            "kasani fusus",
            "kaşani fusus",
            "kâşânî fusus",
            "qashani fusus",
            "şerh kashani",
            "serh kashani",
        ],
        "metin": (
            "Abdürrezzâk Kâşânî'nin Fusûsu'l-Hikem şerhi. "
            "İbnü'l-Arabî okulunun erken ve etkili açıklamalarından biridir. "
            "Kütüphanede Arapça OCR vardır (güven orta; sayfa uydurma yasak). "
            "Rüzgar fetva vermez."
        ),
        "kavram_baslik": "kashani fusus",
        "kavram_not": "Şerh rafı — Kâşânî; fetva yok.",
    },
    {
        "id": "qaysari_sharh_fusus",
        "eser_tr": "Şerh-i Fusûs / Matla‘-ı Husûsi’l-Kelim (Kayserî)",
        "eser_ar": "شرح فصوص الحكم المسمى بمطلع خصوص الكلم في معاني فصوص الحكم",
        "yazar": "Dâvûd el-Kayserî (ö. 751/1350); nşr. Seyyid Celâleddin Âştiyânî",
        "ilgili_eser_id": "ibn_arabi_fusus",
        "dil": "ar",
        # Basılı PDF metin katmanı (presentation-form → NFKC); IA yazma OCR kullanılmaz
        "local_file": "qaysari_sharh_fusus__ashatiyani_nfkc.txt",
        "kaynak": (
            "Basılı Arapça (Âştiyânî nşr., Şirket-i İntişârât-ı İlmî ve Ferhengî 1375ş) "
            "— PDF metin çıkarma + NFKC; güven orta"
        ),
        "aliases": [
            "kayseri fusus",
            "kayserî fusus",
            "qaysari fusus",
            "qaisari fusus",
            "şerh kayseri",
            "serh kayseri",
            "matla khusus",
            "matla husus",
        ],
        "metin": (
            "Dâvûd el-Kayserî'nin Fusûsu'l-Hikem şerhi (Matla‘-ı Husûsi’l-Kelim). "
            "Kütüphanede Arapça basılı metin vardır (güven orta; sayfa uydurma yasak). "
            "Rüzgar fetva vermez."
        ),
        "kavram_baslik": "kayseri fusus",
        "kavram_not": "Şerh rafı — Kayserî tam AR; fetva yok.",
    },
    {
        "id": "qaysari_muqaddima_fusus",
        "eser_tr": "Mukaddimetü'l-Kayserî (Fusûs)",
        "eser_ar": "مقدمة القيصري على فصوص الحكم",
        "yazar": "Dâvûd el-Kayserî (ö. 751/1350); İng. çeviri Mukhtar H. Ali",
        "ilgili_eser_id": "ibn_arabi_fusus",
        "dil": "en",
        "ia_id": "muqadimah-of-qaisari_202204.pdf_202204",
        "files": ["Muqadimah of Qaisari_djvu.txt"],
        "kaynak": (
            "Internet Archive (İngilizce çeviri OCR — Kayserî mukaddimesi; "
            "tam Arapça şerh: qaysari_sharh_fusus)"
        ),
        "aliases": [
            "mukaddime kayseri",
            "muqaddima qaysari",
            "mukaddimat al qaysari",
            "kayseri mukaddime",
        ],
        "metin": (
            "Dâvûd el-Kayserî'nin Fusûs şerhine mukaddimesinin İngilizce çevirisi. "
            "Tam Arapça şerh ayrıca `qaysari_sharh_fusus` rafındadır. "
            "Güven orta; sayfa uydurma yasak. Rüzgar fetva vermez."
        ),
        "kavram_baslik": "mukaddime kayseri",
        "kavram_not": "Şerh rafı — Kayserî mukaddime (EN); fetva yok.",
    },
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _http_get(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Ruzgar-Ilim/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp, open(dest, "wb") as out:
        shutil.copyfileobj(resp, out)


def _strip(text: str) -> str:
    import unicodedata

    # PDF presentation-form Arapça → standart kod noktaları
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[^\S\n]{2,}", " ", text)
    return text.strip()


def _script_ratio(s: str) -> float:
    ar = len(re.findall(r"[\u0600-\u06FF]", s))
    lat = len(re.findall(r"[A-Za-z]", s))
    tot = ar + lat
    return (ar + lat) / tot if tot else 0.0


def _chunk(text: str) -> list[str]:
    text = _strip(text)
    if not text:
        return []
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        if len(p) > CHUNK * 2:
            if buf:
                chunks.append(buf.strip())
                buf = ""
            for i in range(0, len(p), CHUNK - OVERLAP):
                piece = p[i : i + CHUNK].strip()
                if piece and (_script_ratio(piece) >= 0.12 or len(piece) > 100):
                    chunks.append(piece)
            continue
        if len(buf) + len(p) + 2 <= CHUNK:
            buf = f"{buf}\n\n{p}".strip() if buf else p
        else:
            if buf and _script_ratio(buf) >= 0.10:
                chunks.append(buf.strip())
            buf = p
    if buf and _script_ratio(buf) >= 0.10:
        chunks.append(buf.strip())
    return chunks


def _download(w: dict) -> Path:
    local = w.get("local_file")
    if local:
        src = STAGE / local if not Path(local).is_absolute() else Path(local)
        if not src.is_file():
            # staging kökünde ara
            alt = STAGE / Path(local).name
            src = alt if alt.is_file() else src
        if not src.is_file():
            raise FileNotFoundError(f"local_file yok: {local} (STAGE={STAGE})")
        print(f"  [local] {src.name}")
        return src

    parts: list[Path] = []
    for fname in w["files"]:
        url = f"https://archive.org/download/{w['ia_id']}/{urllib.request.quote(fname)}"
        safe = re.sub(r"[^\w.\-]+", "_", fname)[:120]
        dest = STAGE / f"{w['id']}__{safe}"
        if dest.is_file() and dest.stat().st_size > 1000:
            print(f"  [skip] {dest.name}")
            parts.append(dest)
            continue
        print(f"  [get] {fname}")
        _http_get(url, dest)
        parts.append(dest)
    if len(parts) > 1:
        merged = STAGE / f"{w['id']}__merged.txt"
        merged.write_text(
            "\n\n".join(p.read_text(encoding="utf-8", errors="replace") for p in parts),
            encoding="utf-8",
        )
        return merged
    return parts[0]


def _write_batches(dest: Path, w: dict, chunks: list[str]) -> int:
    incr = dest / "incremental"
    if incr.exists():
        for old in incr.glob("*.md"):
            old.unlink()
    incr.mkdir(parents=True, exist_ok=True)
    n = 0
    for i in range(0, len(chunks), BATCH):
        n += 1
        part = chunks[i : i + BATCH]
        body = [
            f"# {w['eser_tr']} — paket {n:04d}",
            "",
            f"Yazar: {w['yazar']}",
            f"İlgili eser: {w['ilgili_eser_id']}",
            "Kaynak: şerh metni (Internet Archive OCR). Fetva değildir; sayfa/cilt uydurulmaz.",
            "",
        ]
        for j, ch in enumerate(part, 1):
            body += [f"## parça {i + j}", "", ch, ""]
        (incr / f"{w['id']}_batch_{n:04d}.md").write_text(
            "\n".join(body), encoding="utf-8"
        )
    return n


def _update_ortak(man: dict) -> None:
    data = json.loads(ORTAK.read_text(encoding="utf-8")) if ORTAK.is_file() else {"kayitlar": []}
    rows = data.get("kayitlar") or []
    found = False
    for r in rows:
        if r.get("kaynak_id") == man["eser_id"]:
            r.update(
                {
                    "kaynak_adi": man["eser_tr"],
                    "yazar": man["yazar"],
                    "ilim_alani": "tasavvuf",
                    "eser_turu": "serh",
                    "dil": man["dil"],
                    "dosya_yolu": man["dosya_yolu"],
                    "guvenilirlik": "orta",
                    "kaynak_sinifi": "kalici",
                    "durum": "hazir",
                    "not": man.get("not") or "",
                }
            )
            found = True
            break
    if not found:
        rows.append(
            {
                "kaynak_id": man["eser_id"],
                "kaynak_adi": man["eser_tr"],
                "yazar": man["yazar"],
                "ilim_alani": "tasavvuf",
                "eser_turu": "serh",
                "dil": man["dil"],
                "yayin": None,
                "cilt": None,
                "bolum": None,
                "sayfa": None,
                "dosya_yolu": man["dosya_yolu"],
                "guvenilirlik": "orta",
                "kaynak_sinifi": "kalici",
                "durum": "hazir",
                "not": man.get("not") or "",
            }
        )
    data["kayitlar"] = rows
    data["guncelleme"] = _utc()
    ORTAK.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _update_kavram(w: dict) -> None:
    rows = []
    if KAV.is_file():
        for line in KAV.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    by = {r.get("id"): r for r in rows}
    by[w["id"]] = {
        "id": w["id"],
        "baslik": w.get("kavram_baslik") or w["id"].replace("_", " "),
        "aliases": w["aliases"],
        "metin": w["metin"],
        "kaynak_notu": w.get("kavram_not") or "Şerh rafı; fetva yok.",
    }
    KAV.write_text(
        "\n".join(json.dumps(by[k], ensure_ascii=False) for k in by) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    STAGE.mkdir(parents=True, exist_ok=True)
    SERH.mkdir(parents=True, exist_ok=True)
    ok = 0
    for w in SERHLER:
        print(f"\n>> {w['id']}")
        src = _download(w)
        text = src.read_text(encoding="utf-8", errors="replace")
        chunks = _chunk(text)
        dest = SERH / w["id"]
        dest.mkdir(parents=True, exist_ok=True)
        n = _write_batches(dest, w, chunks)
        man = {
            "eser_id": w["id"],
            "eser_tr": w["eser_tr"],
            "eser_ar": w["eser_ar"],
            "yazar": w["yazar"],
            "rol": "serh",
            "eser_turu": "serh",
            "ilgili_eser_id": w["ilgili_eser_id"],
            "ilim_alani": "tasavvuf",
            "dil": w["dil"],
            "dosya_yolu": f"knowledge/ilim/din/09_ahlak_tasavvuf/serh_ve_aciklama/{w['id']}",
            "guvenilirlik": "orta",
            "kaynak_sinifi": "kalici",
            "durum": "hazir",
            "kaynak": w["kaynak"],
            "source_file": src.name,
            "sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
            "char_count": len(text),
            "chunk_count": len(chunks),
            "batch_sayisi": n,
            "not": "Fusûs şerhi; sayfa uydurma yasak.",
            "updated_utc": _utc(),
        }
        (dest / "manifest.json").write_text(
            json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        _update_ortak(man)
        _update_kavram(w)
        print(f"  [ok] chunks={len(chunks)} batches={n}")
        ok += 1

    rows_md = [
        "| Şerh | Müellif | Dil | İlgili |",
        "|------|---------|-----|--------|",
    ]
    for w in SERHLER:
        rows_md.append(
            f"| `{w['id']}` | {w['yazar'].split('(')[0].strip()} | {w['dil']} | `{w['ilgili_eser_id']}` |"
        )
    readme = SERH / "README.md"
    readme.write_text(
        "# Şerh ve açıklama rafları\n\n"
        "Özellikle İbnü'l-Arabî (`Fütûhât`, `Fusûs`) için şerh/açıklama kaynakları buraya konur.\n\n"
        + "\n".join(rows_md)
        + "\n\n**Politika:** Fetva yok. Sayfa/cilt uydurma yasak. OCR/PDF metin güven orta.\n"
        "Kayserî: tam AR `qaysari_sharh_fusus` + EN mukaddime `qaysari_muqaddima_fusus`.\n",
        encoding="utf-8",
    )
    print(f"\nTOPLAM serh={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
