# Created by Ümit & Gökçenur
"""Kaynak yolundan eser künyesi (D1/K3).

Kanıt parçasının kaynağı bir yol (örn. ``ilim/din/shamela/18_genel_fikih/shamela_9849/incremental/..._batch_0005.md``).
Yolun üstündeki kitap klasöründe ``manifest.json`` varsa eser adı (Arapça orijinal), müellif ve kimlik
oradan okunur. Eser/raf adına BAĞLI DEĞİLDİR: manifesti olan her kaynak aynı yoldan künyelenir.

- Sentez bağlamında `[K1] <künye>` etiketi için (uydurma künyeyi önler; Arapça orijinale işaret eder).
- Ölçüm: kanıt paketi künyeleri (`tur_teshis.kaynak_kunye`) → uydurma kaynak denetleyicisi.

Kapat: ``RUZGAR_KUNYE=0`` (etiket yol olarak kalır).
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Sequence

_PKG = Path(__file__).resolve().parent.parent
_KNOW = _PKG / "knowledge"

_PLACEHOLDER_MARKS = ("〔", "bekler", "Türkçe tam anlam")


def kunye_enabled() -> bool:
    return os.environ.get("RUZGAR_KUNYE", "1").strip().lower() not in ("0", "false", "no")


def _know_root() -> Path:
    try:
        from ilim_assistant.rag_store import _knowledge_root

        return _knowledge_root()
    except Exception:
        return _KNOW


@lru_cache(maxsize=4096)
def _manifest_for_dir(book_dir: str) -> dict[str, Any] | None:
    p = Path(book_dir) / "manifest.json"
    if not p.is_file():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    return d if isinstance(d, dict) else None


def _find_manifest(src: str) -> tuple[dict[str, Any] | None, Path | None]:
    rel = (src or "").replace("\\", "/").strip().lstrip("/")
    if not rel or ".." in rel:
        return None, None
    root = _know_root()
    cur = (root / rel)
    # dosya → yukarı en çok 4 seviye; manifest.json kitap klasöründe
    for _ in range(5):
        cur = cur.parent
        if cur == root or cur == cur.parent:
            break
        m = _manifest_for_dir(str(cur))
        if m is not None:
            return m, cur
    return None, None


def _tr_ok(s: str) -> bool:
    s = (s or "").strip()
    return bool(s) and not any(m in s for m in _PLACEHOLDER_MARKS)


def kunye_for_source(src: str) -> dict[str, Any] | None:
    """Kaynak yolu → künye sözlüğü (yoksa None)."""
    if not kunye_enabled():
        return None
    m, d = _find_manifest(src)
    if not m:
        return None
    cat = d.parent.name if d is not None else ""
    return {
        "eser_id": str(m.get("eser_id") or (d.name if d else "")),
        "book_id": m.get("book_id"),
        "eser_ar": str(m.get("eser_ar") or "").strip(),
        "eser_tr": str(m.get("eser_tr") or "").strip() if _tr_ok(str(m.get("eser_tr") or "")) else "",
        "yazar": str(m.get("yazar") or "").strip(),
        "yazar_ar": str(m.get("yazar_ar") or "").strip(),
        "kategori": cat,
        "katman": m.get("katman"),
        "hat": m.get("hat"),
    }


def kunye_etiketi(src: str) -> str:
    """Okunur künye satırı: «Arapça eser adı — Arapça müellif (Türkçe ad) · kimlik». Yoksa boş."""
    k = kunye_for_source(src)
    if not k:
        return ""
    ad = k["eser_ar"] or k["eser_tr"]
    if not ad:
        return ""
    s = ad
    if k["yazar_ar"] or k["yazar"]:
        s += f" — {k['yazar_ar'] or k['yazar']}"
    tr_bits = []
    if k["eser_tr"] and k["eser_ar"]:
        tr_bits.append(k["eser_tr"])
    if k["yazar"] and k["yazar_ar"] and k["yazar"] != k["yazar_ar"]:
        tr_bits.append(k["yazar"])
    if tr_bits:
        s += " (" + "; ".join(tr_bits) + ")"
    kimlik = " · ".join(x for x in (k["eser_id"], k["kategori"]) if x)
    if kimlik:
        s += f" [{kimlik}]"
    return s


def kunyeler_for_hits(hits: Iterable[Any], *, limit: int = 8) -> list[dict[str, Any]]:
    """(metin, kaynak, skor) listesi → benzersiz eser künyeleri (telemetri/denetim)."""
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for h in hits or []:
        try:
            src = str(h[1] or "")
        except Exception:
            continue
        if not src:
            continue
        k = kunye_for_source(src)
        if k:
            key = k["eser_id"] or src
            row = dict(k)
        else:
            key = src
            row = {"eser_id": "", "eser_ar": "", "eser_tr": "", "yazar": "", "yazar_ar": "",
                   "kategori": "", "yol_adi": Path(src.replace("\\", "/")).stem}
        if key in seen:
            continue
        seen.add(key)
        row["yol"] = src
        out.append(row)
        if len(out) >= limit:
            break
    return out


def cesitlendir_eser(hits: Sequence[Any], limit: int = 4) -> list[Any]:
    """Aynı kitabın art arda parçaları yerine en çok `limit` farklı eser (şâmile kimliği)."""
    import re

    best: dict[str, Any] = {}
    order: list[str] = []
    for h in hits or []:
        try:
            src = str(h[1] or "")
            sc = float(h[2])
        except Exception:
            continue
        m = re.search(r"shamela_(\d+)", src.replace("\\", "/"))
        key = m.group(1) if m else src
        prev = best.get(key)
        if prev is None:
            order.append(key)
            best[key] = h
        else:
            try:
                if sc > float(prev[2]):
                    best[key] = h
            except Exception:
                pass
    return [best[k] for k in order][: max(1, limit)]


def kaynak_izi_metni(kunyeler: Sequence[dict[str, Any]] | None, *, limit: int = 4) -> str:
    """Cevap sonuna eklenecek künye. Kanıt künyesi yoksa boş."""
    lines: list[str] = []
    for k in kunyeler or []:
        ad = str(k.get("eser_ar") or k.get("eser_tr") or k.get("yol_adi") or "").strip()
        if not ad:
            continue
        yazar = str(k.get("yazar_ar") or k.get("yazar") or "").strip()
        satir = f"[K{len(lines) + 1}] {ad}"
        if yazar:
            satir += f" — {yazar}"
        lines.append(satir)
        if len(lines) >= limit:
            break
    if not lines:
        return ""
    return "\n\nKaynak izi:\n" + "\n".join(lines)


def label_for_source(src: str) -> str:
    """Bağlam bloğu etiketi: künye varsa künye, yoksa yol."""
    et = kunye_etiketi(src)
    return et if et else src
