# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 78: Çekirdek kapsam (ilim-assistant + ruzgar-desktop).

«çekirdek:», «ruzgara patch», «motor dosyası» ile projects/ dışı güvenli yazım.
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

FAZ78_VERSION = "programlama-faz78-v1-2026-05-26"

_CORE_PREFIXES = (
    "ilim-assistant/ilim_assistant/",
    "ilim-assistant/ilim_assistant/motorlar/",
    "ilim-assistant/desktop_server.py",
    "ilim-assistant/scripts/",
    "ilim-assistant/tests/monorepo_live/",
    "ilim-assistant/tests/monorepo_refactor/",
    "ruzgar-desktop/",
    "PROGRAMMING_MOTOR_YOL_HARITASI.md",
    "PROGRAMMING_DALGA_H.md",
)

_CORE_CUE_RE = re.compile(
    r"(?:çekirdek|cekirdek|ruzgara\s*patch|ruzgar\s*çekirdek|motor\s+dosyas|"
    r"ilim-assistant|desktop_server|ruzgar-desktop|app\.js)",
    re.I,
)
_STATUS_RE = re.compile(
    r"(?:çekirdek\s+durum|core\s+scope|yazim\s+kapsam)",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ78", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz78_enabled() -> bool:
    return _enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def wants_core_scope(message: str) -> bool:
    if not _enabled():
        return False
    raw = (message or "").strip()
    if not raw:
        return False
    if _STATUS_RE.search(_ascii_fold(raw)):
        return True
    return bool(_CORE_CUE_RE.search(raw))


def resolve_core_scope_rel(message: str) -> str | None:
    """Handoff/ajan için önerilen kök göreli kapsam."""
    raw = (message or "").strip().lower()
    if "ruzgar-desktop" in raw or "app.js" in raw or "index.html" in raw:
        return "ruzgar-desktop"
    if "desktop_server" in raw:
        return "ilim-assistant"
    if "motor" in raw or "faz" in raw or "programlama" in raw:
        return "ilim-assistant/ilim_assistant/motorlar"
    if "script" in raw or "smoke" in raw:
        return "ilim-assistant/scripts"
    return "ilim-assistant/ilim_assistant/motorlar"


def core_write_allowed(rel_path: str) -> tuple[bool, str]:
    """Faz 78 — çekirdek yollar için ek izin (faz3 üzerine)."""
    if not _enabled():
        return True, ""
    rel = (rel_path or "").replace("\\", "/").lstrip("/").lower()
    if not rel:
        return False, "Boş yol."
    if ".." in Path(rel).parts:
        return False, "Path traversal reddedildi."
    allowed = any(rel.startswith(p.lower()) or rel == p.lower().rstrip("/") for p in _CORE_PREFIXES)
    if allowed:
        return True, ""
    if rel.startswith("projects/"):
        return True, ""
    return (
        False,
        "Faz 78: Bu yol çekirdek kapsamında değil. "
        "«çekirdek:» veya `ilim-assistant/...` / `ruzgar-desktop/...` kullanın.",
    )


def augment_write_policy(
    root: Path,
    rel_path: str,
    message: str = "",
) -> tuple[bool, str]:
    """programlama_motoru.write öncesi — çekirdek isteği varsa faz78 kontrolü."""
    try:
        from ilim_assistant.motorlar.programlama_faz3 import programlama_write_allowed

        ok, reason = programlama_write_allowed(root, rel_path)
        if not ok:
            return ok, reason
    except Exception:
        pass
    if wants_core_scope(message) or _path_is_core(rel_path):
        return core_write_allowed(rel_path)
    rel = (rel_path or "").replace("\\", "/").lstrip("/").lower()
    if not rel.startswith("projects/") and not _path_is_core(rel_path):
        if wants_core_scope(message):
            return core_write_allowed(rel_path)
        return (
            False,
            "Atölye varsayılanı: yalnızca `projects/` veya çekirdek yolları. "
            "Rüzgar çekirdeği için mesaja «çekirdek:» ekleyin.",
        )
    return True, ""


def _path_is_core(rel_path: str) -> bool:
    rel = (rel_path or "").replace("\\", "/").lstrip("/").lower()
    return any(rel.startswith(p.lower()) for p in _CORE_PREFIXES)


def format_core_scope_status() -> str:
    lines = [
        "Ümit abi, **çekirdek yazım kapsamı (Faz 78):**",
        "",
        "İzinli önekler:",
    ]
    for p in _CORE_PREFIXES:
        lines.append(f"· `{p}`")
    lines.append("")
    lines.append(
        "Kullanım: «çekirdek: ilim-assistant/... dosyasını düzelt» veya "
        "@@write ile tam yol. `projects/` her zaman açık."
    )
    lines.append(f"\n({FAZ78_VERSION})")
    return "\n".join(lines)


def core_scope_directive(message: str = "") -> str:
    if not wants_core_scope(message):
        return ""
    scope = resolve_core_scope_rel(message)
    return (
        f"[FAZ 78 — ÇEKİRDEK KAPSAM]\n"
        f"Bu tur Rüzgar çekirdeği (`{scope}`) üzerinde çalışılıyor.\n"
        "Yalnızca listelenen önekler altına yaz; hassas bellek/json dosyalarına dokunma.\n"
    )


def maybe_instant_faz78(message: str) -> str | None:
    if not _enabled():
        return None
    raw = (message or "").strip()
    if _STATUS_RE.search(_ascii_fold(raw)):
        return format_core_scope_status()
    return None


def faz78_directive() -> str:
    return (
        "[FAZ 78 — ÇEKİRDEK KAPSAM]\n"
        "Rüzgar çekirdeği: «çekirdek:» + ilim-assistant/ veya ruzgar-desktop/ yolları.\n"
        "Komut: çekirdek durum\n"
    )


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["programlama_faz78"] = faz78_enabled()
    return out
