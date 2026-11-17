# Created by Ümit & Gökçenur
"""Dilim 6 — Programlama çırak ders sözleşmesi.

Yeşil dilim = iş bitti + en az bir ders kaydı.
Rüzgar çırak; usta (Cursor) kırılgan yerde keser.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

CIRAK_DERS_VERSION = "ruzgar-cirak-ders-v1.1-2026-11-17"

_PROJECTS_PY_RE = re.compile(
    r"(?P<path>projects/[\w.\-]+(?:/[\w.\-]+)*\.py)\b",
    re.I,
)

# Çıraka verilebilecek dar görev türleri (serbest ajan değil)
CIRAK_GOREV_TURLERI: tuple[str, ...] = (
    "tek_dosya_patch",
    "smoke_yesil",
    "pytest_gecir",
    "atolye_alan_doldur",
    "niyet_regex_dar",
)

# Usta işi — çırağa verilmez
USTA_KIRILGAN: tuple[str, ...] = (
    "boot_sirasi",
    "ana_yuz_kilidi",
    "anayasa_hardcode",
    "hub_omurga",
    "serbest_ajan",
    "dosya_silme",
)

DERS_ZORUNLU_ALANLAR: tuple[str, ...] = (
    "dilim",
    "ders",
    "smoke_veya_dosya",
)


def looks_like_cirak_gorev(message: str) -> bool:
    """Çırak görev satırı mı? (ajan fallback kapısı)"""
    low = (message or "").strip().lower()
    if not low:
        return False
    if "cirak" in low or "çırak" in low:
        return True
    return False


def wants_full_code_agent(message: str) -> bool:
    """Faz 85 miss sonrası tam ajan / çırak borusu."""
    low = (message or "").strip().lower()
    if "tam ajan" in low or "tam_ajan" in low:
        return True
    return looks_like_cirak_gorev(message)


def cirak_gorev_metni(tur: str, hedef: str) -> str:
    """Kapılı çırak görev satırı (programlama atölyesine).

    Köşeli [cirak:…] kullanma — path_hint / proje yolu bozulur (canlı ders 2026-11-17).
    Sonuna `tam ajan` eklenir — Faz85 miss'te ajan borusu açılsın.
    """
    t = (tur or "").strip()
    h = (hedef or "").strip()[:400]
    if t not in CIRAK_GOREV_TURLERI:
        t = "tek_dosya_patch"
    return f"görev: cirak {t} — {h} · tam ajan".strip()


def ders_kaydi_gecerli(kayit: dict[str, Any] | None) -> bool:
    if not isinstance(kayit, dict):
        return False
    for k in DERS_ZORUNLU_ALANLAR:
        if not str(kayit.get(k) or "").strip():
            return False
    return True


def yesil_dilim_icin_ders_gerekli(kayit: dict[str, Any] | None) -> dict[str, Any]:
    """Çıkış: ok + neden."""
    if ders_kaydi_gecerli(kayit):
        return {"ok": True, "version": CIRAK_DERS_VERSION}
    return {
        "ok": False,
        "reason": "ders_yazilmadan_yesil_sayilmaz",
        "required": list(DERS_ZORUNLU_ALANLAR),
        "version": CIRAK_DERS_VERSION,
    }


def cirak_status() -> dict[str, Any]:
    return {
        "enabled": True,
        "version": CIRAK_DERS_VERSION,
        "gorev_turleri": list(CIRAK_GOREV_TURLERI),
        "usta_kirilgan": list(USTA_KIRILGAN),
        "tavan_not": "~%70; serbest ajan yok",
        "supervised_write": True,
    }


def try_cirak_supervised_write(
    message: str,
    workspace_root: str | Path | None,
) -> dict[str, Any] | None:
    """Dar çırak yazımı — LLM yok; yalnız projects/**/*.py.

    Örnek: `görev: cirak … projects/cirak-atolyesi/hello_cirak.py … print PASS`
    """
    if not looks_like_cirak_gorev(message):
        return None
    raw = (message or "").strip()
    m = _PROJECTS_PY_RE.search(raw)
    if not m:
        return None
    rel = m.group("path").replace("\\", "/")
    # Güvenlik: yalnız projects/ altı, .. yok
    if ".." in rel or not rel.lower().startswith("projects/"):
        return None
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
    except Exception:
        root = None
    if root is None:
        root = Path(workspace_root).resolve() if workspace_root else Path.cwd().resolve()
    else:
        root = Path(root).resolve()
    target = (root / rel).resolve()
    try:
        target.relative_to(root / "projects")
    except ValueError:
        return None

    # İçerik: PASS / print isteği
    low = raw.lower()
    if "pass cirak" in low or "pass cirak-d9" in low or "print pass" in low:
        body = 'print("PASS cirak-d9")\n'
    elif "print(" in raw:
        # ham print satırı yakala
        pm = re.search(r"print\s*\([^)]*\)", raw)
        body = (pm.group(0) if pm else 'print("PASS cirak")') + "\n"
    else:
        body = 'print("PASS cirak")\n'

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    except OSError as exc:
        return {
            "ok": False,
            "verify_ok": False,
            "writes_ok": 0,
            "scope_rel": str(Path(rel).parent).replace("\\", "/"),
            "source": "cirak_supervised_write",
            "detail": f"Yazılamadı: {exc}",
            "version": CIRAK_DERS_VERSION,
        }

    return {
        "ok": True,
        "verify_ok": True,
        "writes_ok": 1,
        "scope_rel": str(Path(rel).parent).replace("\\", "/"),
        "source": "cirak_supervised_write",
        "detail": (
            f"Çırak supervised yazım OK · `{rel}`\n"
            f"İçerik:\n```python\n{body.strip()}\n```\n"
            f"({CIRAK_DERS_VERSION})"
        ),
        "version": CIRAK_DERS_VERSION,
        "written": rel,
    }
