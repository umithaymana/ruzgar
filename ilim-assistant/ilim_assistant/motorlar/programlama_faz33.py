# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 33: Doğal cümle = otomatik kod ajanı.

`görev:` şart değil: aktif proje + iş fiili → çok tur ajan (Faz 20/14).
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

FAZ33_VERSION = "programlama-faz33-v1-2026-05-25"
_MIN_LEN = 6
_MAX_LEN = 600

_ACTION_RE = re.compile(
    r"(?:yap|olustur|oluştur|ekle|duzelt|düzelt|geçir|gecir|bitir|tamamla|yaz|güncelle|guncelle|"
    r"implement|fix|add|create|build|refactor|calistir|çalıştır|guncelle|degistir|değiştir|"
    r"endpoint|versiyon|version|pytest|test\s+gecir|test\s+geçir|health|api\s)",
    re.I,
)
_QUESTION_ONLY_RE = re.compile(
    r"^(?:nedir|nasıl|nasil|ne\s+demek|açıkla|acikla|anlat|why|what\s+is|kim|kaç)\b",
    re.I,
)
_RESERVED_ONLY_RE = re.compile(
    r"^(?:git\s+durum|patch\s+liste|patch\s+onayla|proje\s+listesi|pr\s+durum|"
    r"sablon\s+listele|şablon\s+listele|commit\s+oner|commit\s+öner)\b",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ33", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _projects_base() -> str:
    return (
        os.environ.get("RUZGAR_SCAFFOLD_BASE", "projects").strip().replace("\\", "/").strip("/")
        or "projects"
    )


def active_scope_from_context(
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> str | None:
    """Açık dosya veya oturumdaki aktif proje."""
    af = (active_file or "").strip().replace("\\", "/").lstrip("/")
    if af.startswith(f"{_projects_base()}/"):
        parts = af.split("/")
        if len(parts) >= 2:
            return f"{_projects_base()}/{parts[1]}"

    try:
        from ilim_assistant.motorlar.programlama_faz5 import load_session

        sess = load_session(workspace_root)
        slug = str(sess.get("active_project") or sess.get("project", {}).get("name") or "").strip()
        if slug:
            return f"{_projects_base()}/{slug}"
    except Exception:
        pass
    return None


def resolve_project_slug(
    message: str,
    workspace_root: str | Path | None = None,
    *,
    active_file: str | None = None,
) -> str | None:
    scope = active_scope_from_context(workspace_root, active_file=active_file)
    if scope:
        return scope.split("/")[-1]

    raw = (message or "").strip()
    try:
        from ilim_assistant.motorlar.programlama_faz19 import _IMPLICIT_PROJECT_RE

        m = _IMPLICIT_PROJECT_RE.search(raw)
        if m:
            slug = m.group(1).strip().strip("/")
            if slug.lower() not in ("projects", "src", "app", "tests", "test"):
                return slug
    except Exception:
        pass

    for w in re.findall(r"[\w.\-]{2,48}", raw):
        wl = w.lower()
        if wl in ("health", "version", "endpoint", "pytest", "test", "main", "api"):
            continue
        if "-" in w or w.endswith("api") or (w.isidentifier() and len(w) > 3):
            return w
    return None


def build_implicit_task_line(
    message: str,
    workspace_root: str | Path | None = None,
    *,
    active_file: str | None = None,
    mode_norm: str = "programlama",
) -> str | None:
    """
    Doğal cümleyi `görev: <proje> <hedef>` satırına çevirir.
    """
    if not _enabled() or mode_norm != "programlama":
        return None
    raw = (message or "").strip()
    if len(raw) < _MIN_LEN or len(raw) > _MAX_LEN:
        return None
    if _QUESTION_ONLY_RE.search(raw) and "@@write" not in raw.lower():
        return None
    if _RESERVED_ONLY_RE.search(_ascii_fold(raw)):
        return None
    low = _ascii_fold(raw)
    if any(
        k in low
        for k in (
            "gorev:",
            "görev:",
            "iş:",
            "is:",
            "yap:",
            "patch onayla",
            "git durum",
            "proje listesi",
            "pr durum",
            "is akisi",
            "iş akışı",
        )
    ):
        return None

    try:
        from ilim_assistant.motorlar.programlama_faz19 import parse_task_aliases

        if parse_task_aliases(raw):
            return None
    except Exception:
        pass

    if not _ACTION_RE.search(raw) and "@@write" not in raw.lower():
        return None

    slug = resolve_project_slug(raw, workspace_root, active_file=active_file)
    if not slug:
        return None

    goal = raw
    low_slug = _ascii_fold(slug)
    if _ascii_fold(raw).startswith(low_slug):
        goal = raw[len(slug) :].lstrip(" :-\t,.")
    if not goal or len(goal) < 4:
        goal = raw
    return f"görev: {slug} {goal}"


def should_auto_programming_agent(
    message: str,
    mode_norm: str = "",
    *,
    workspace_root: str | Path | None = None,
    active_file: str | None = None,
) -> bool:
    """Faz 33 — ajan döngüsü çalışsın mı (görev: olmadan)."""
    if not _enabled() or mode_norm != "programlama":
        return False
    try:
        from ilim_assistant.motorlar.programlama_faz20 import (
            unified_agent_enabled,
            wants_implementation_agent,
        )

        if not unified_agent_enabled():
            return False
        if not wants_implementation_agent(message, mode_norm):
            return False
        from ilim_assistant.motorlar.programlama_faz20 import resolve_agent_task

        return (
            resolve_agent_task(
                message,
                workspace_root,
                active_file=active_file,
                mode_norm=mode_norm,
            )
            is not None
        )
    except Exception:
        implicit = build_implicit_task_line(
            message,
            workspace_root,
            active_file=active_file,
            mode_norm=mode_norm,
        )
        return bool(implicit)
    return False


def normalize_for_agent(
    message: str,
    mode_norm: str = "",
    *,
    workspace_root: str | Path | None = None,
    active_file: str | None = None,
) -> str:
    """Faz 19 normalize üzerine aktif proje ile genişletilmiş görev satırı."""
    try:
        from ilim_assistant.motorlar.programlama_faz19 import normalize_agent_message

        base = normalize_agent_message(message, mode_norm=mode_norm)
    except Exception:
        base = message
    if mode_norm != "programlama":
        return base
    if parse_explicit_task(base):
        return base
    implicit = build_implicit_task_line(
        message,
        workspace_root,
        active_file=active_file,
        mode_norm=mode_norm,
    )
    if implicit:
        return implicit
    return base


def parse_explicit_task(message: str) -> bool:
    try:
        from ilim_assistant.motorlar.programlama_faz14 import parse_code_agent_task

        return parse_code_agent_task(message) is not None
    except Exception:
        return False


def faz33_directive() -> str:
    return (
        "[OTOMATİK KOD AJANI — Faz 33]\n"
        "Programlama modunda iş cümlesi yazmanız yeterli — `görev:` zorunlu değil.\n"
        "Örn: «health endpointine version ekle ve pytest geçir» (aktif proje açıkken).\n"
    )
