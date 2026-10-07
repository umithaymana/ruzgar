# Created by Ümit & Gökçenur
"""
Rüzgar ortak kaynak altyapısı — tüm bilgi alanlarında ortak şema ve güvenli atıf.

Kalıcı kütüphane kayıtları: knowledge/ortak_kaynak/
Web / hatırla ile karıştırılmaz.
Kapatma: RUZGAR_ORTAK_KAYNAK=0
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

ORTAK_KAYNAK_VERSION = "ortak-kaynak-v1-2026-10-07"

_PKG = Path(__file__).resolve().parent.parent
_ORTAK_ROOT = _PKG / "knowledge" / "ortak_kaynak"
_SEMA = _ORTAK_ROOT / "SEMA.json"
_ALANLAR = _ORTAK_ROOT / "ALANLAR.json"
_KAYIT = _ORTAK_ROOT / "KAYNAK_KAYIT.json"

DOGRULANAMADI = "Bu bilgi mevcut kütüphanedeki kaynaklarda doğrulanamadı."


def ortak_kaynak_enabled() -> bool:
    return os.environ.get("RUZGAR_ORTAK_KAYNAK", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def ortak_kaynak_root() -> Path:
    return _ORTAK_ROOT


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def load_sema() -> dict[str, Any]:
    if not ortak_kaynak_enabled():
        return {}
    return _read_json(_SEMA)


@lru_cache(maxsize=1)
def load_alanlar() -> list[dict[str, Any]]:
    if not ortak_kaynak_enabled():
        return []
    data = _read_json(_ALANLAR)
    rows = data.get("alanlar") or []
    return [r for r in rows if isinstance(r, dict)]


@lru_cache(maxsize=1)
def load_kaynak_kayitlari() -> list[dict[str, Any]]:
    if not ortak_kaynak_enabled():
        return []
    data = _read_json(_KAYIT)
    rows = data.get("kayitlar") or []
    return [r for r in rows if isinstance(r, dict)]


def clear_ortak_kaynak_cache() -> None:
    load_sema.cache_clear()
    load_alanlar.cache_clear()
    load_kaynak_kayitlari.cache_clear()


def _norm_path(p: str) -> str:
    t = (p or "").strip().replace("\\", "/")
    t = re.sub(r"^/+", "", t)
    if t.startswith("ilim-assistant/"):
        t = t[len("ilim-assistant/") :]
    return t.lower()


def lookup_kaynak(key: str) -> Optional[dict[str, Any]]:
    """kaynak_id veya dosya yolu ile kalıcı kayıt bul."""
    if not ortak_kaynak_enabled():
        return None
    q = (key or "").strip()
    if not q:
        return None
    q_low = q.lower()
    q_path = _norm_path(q)
    for row in load_kaynak_kayitlari():
        kid = str(row.get("kaynak_id") or "").strip()
        if kid and kid.lower() == q_low:
            return dict(row)
        dp = _norm_path(str(row.get("dosya_yolu") or ""))
        if dp and (q_path == dp or q_path.startswith(dp.rstrip("/") + "/") or dp in q_path):
            return dict(row)
    return None


def _filled(val: Any) -> bool:
    if val is None:
        return False
    if isinstance(val, str) and not val.strip():
        return False
    return True


def format_atif(kayit: Optional[dict[str, Any]], *, prefix: str = "Kaynak:") -> str:
    """Yalnızca dolu alanları yazar; null sayfa/cilt/bölüm yazılmaz."""
    if not kayit:
        return ""
    yazar = (kayit.get("yazar") or "").strip()
    ad = (kayit.get("kaynak_adi") or kayit.get("eser_tr") or "").strip()
    if not ad and not yazar:
        return ""
    parts: list[str] = []
    if yazar and ad:
        parts.append(f"{yazar}, {ad}")
    elif ad:
        parts.append(ad)
    else:
        parts.append(yazar)
    for label, key in (
        ("cilt", "cilt"),
        ("bölüm", "bolum"),
        ("sayfa", "sayfa"),
    ):
        if _filled(kayit.get(key)):
            parts.append(f"{label} {kayit.get(key)}")
    if kayit.get("durum") == "placeholder":
        parts.append("(kütüphane kaydı — metin henüz dolu değil)")
    body = ", ".join(parts)
    return f"{prefix} {body}".strip() if prefix else body


def atif_yoksa_uyari() -> str:
    rules = (load_sema().get("atif_kurallari") or {}) if ortak_kaynak_enabled() else {}
    msg = rules.get("dogrulanamadi")
    return str(msg).strip() if msg else DOGRULANAMADI


def enrich_source_label(src_path: str) -> str:
    """Dosya yolu için mümkünse bibliyografik satır; yoksa orijinal path."""
    if not ortak_kaynak_enabled():
        return src_path
    hit = lookup_kaynak(src_path)
    if not hit:
        return src_path
    bib = format_atif(hit, prefix="")
    if not bib:
        return src_path
    return f"{bib} — {src_path}"


def ortak_kaynak_status() -> dict[str, Any]:
    alanlar = load_alanlar()
    kayitlar = load_kaynak_kayitlari()
    return {
        "ok": True,
        "enabled": ortak_kaynak_enabled(),
        "version": ORTAK_KAYNAK_VERSION,
        "kok": "knowledge/ortak_kaynak",
        "alan_sayisi": len(alanlar),
        "kayit_sayisi": len(kayitlar),
        "placeholder_sayisi": sum(1 for k in kayitlar if k.get("durum") == "placeholder"),
    }
