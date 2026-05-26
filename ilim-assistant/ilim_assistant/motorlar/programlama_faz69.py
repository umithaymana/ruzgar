# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 69: Otomatik proje kapsamı (ROK).

Aktif proje yokken: mesajdan mevcut projeyi seç · yoksa «yeni proje» scaffold (Faz 47).
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any

FAZ69_VERSION = "programlama-faz69-v1-2026-05-26"

_CREATE_HINT_RE = re.compile(
    r"(?:sıfırdan|sifirdan|yeni\s+proje|bana\s+bir|bir\s+(?:api|site|uygulama)|"
    r"api\s+yap|site\s+yap|uygulama\s+yap|proje\s+üret|proje\s+uret|bağımsız\s+proje)",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ69", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz69_enabled() -> bool:
    return _enabled()


def _projects_base() -> str:
    return (
        os.environ.get("RUZGAR_SCAFFOLD_BASE", "projects").strip().replace("\\", "/").strip("/")
        or "projects"
    )


def _project_dir(workspace_root: str | Path | None, slug: str) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        root = repo_root(workspace_root)
        if root is None:
            return None
        p = root / _projects_base() / slug.replace("/", os.sep)
        return p if p.is_dir() else None
    except Exception:
        return None


def infer_create_spec(message: str) -> Any | None:
    """Doğal «yeni api/site yap» → ProjeUretSpec."""
    raw = (message or "").strip()
    if not raw or not _CREATE_HINT_RE.search(raw):
        return None
    try:
        from ilim_assistant.motorlar.programlama_faz47 import (
            infer_template_from_text,
            parse_proje_uret_command,
            _extract_project_slug,
            ProjeUretSpec,
            _goal_from_remainder,
        )

        spec = parse_proje_uret_command(raw)
        if spec:
            return spec
        slug = _extract_project_slug(raw)
        if not slug:
            return None
        tid = infer_template_from_text(raw)
        return ProjeUretSpec(
            template_id=tid,
            project_name=slug,
            goal=_goal_from_remainder(raw, slug, tid),
        )
    except Exception:
        return None


def ensure_scope_for_agent(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> dict[str, Any]:
    """
    Kod ajanı öncesi proje kapsamı garantisi.
    action: active | switched | created | none
    """
    if not _enabled():
        return {"ok": False, "action": "none", "reason": "faz69_kapali"}

    try:
        from ilim_assistant.motorlar.programlama_faz33 import active_scope_from_context
    except Exception:
        return {"ok": False, "action": "none", "reason": "scope_module"}

    scope = active_scope_from_context(workspace_root, active_file=active_file)
    if scope:
        return {
            "ok": True,
            "action": "active",
            "scope_rel": scope,
            "slug": scope.split("/")[-1],
        }

    raw = (message or "").strip()
    slug: str | None = None
    try:
        from ilim_assistant.motorlar.programlama_faz33 import resolve_project_slug

        slug = resolve_project_slug(raw, workspace_root, active_file=active_file)
    except Exception:
        pass

    if slug and _project_dir(workspace_root, slug):
        try:
            from ilim_assistant.motorlar.programlama_faz29 import switch_to_project

            sw = switch_to_project(workspace_root, slug)
            if sw.get("ok"):
                rel = str(sw.get("project_rel") or f"{_projects_base()}/{slug}")
                return {
                    "ok": True,
                    "action": "switched",
                    "scope_rel": rel,
                    "slug": slug,
                    "focus_rel": sw.get("focus_rel"),
                }
        except Exception:
            pass
        rel = f"{_projects_base()}/{slug}"
        return {"ok": True, "action": "switched", "scope_rel": rel, "slug": slug}

    spec = infer_create_spec(message)
    if spec is not None:
        try:
            from ilim_assistant.motorlar.programlama_faz47 import run_proje_uret_prepare

            t0 = time.perf_counter()
            rep = run_proje_uret_prepare(workspace_root, spec)
            elapsed = round(time.perf_counter() - t0, 2)
            if rep.scaffold_ok and rep.scope_rel:
                return {
                    "ok": True,
                    "action": "created",
                    "scope_rel": rep.scope_rel,
                    "slug": spec.project_name,
                    "scaffold_ok": True,
                    "verify_ok": rep.verify_ok,
                    "ready_without_agent": rep.ready_without_agent,
                    "elapsed_sec": elapsed,
                    "detail": rep.detail[:300],
                }
            return {
                "ok": False,
                "action": "create_failed",
                "error": rep.detail[:200] or "scaffold",
            }
        except Exception as exc:
            return {"ok": False, "action": "create_failed", "error": str(exc)[:160]}

    try:
        from ilim_assistant.motorlar.programlama_faz29 import get_workspace_projects_state

        st = get_workspace_projects_state(workspace_root)
        recent = list(st.get("recent_projects") or [])
        if len(recent) == 1 and _CREATE_HINT_RE.search(message or "") is None:
            only = recent[0]
            if _project_dir(workspace_root, only):
                from ilim_assistant.motorlar.programlama_faz29 import switch_to_project

                sw = switch_to_project(workspace_root, only)
                if sw.get("ok"):
                    rel = str(sw.get("project_rel") or f"{_projects_base()}/{only}")
                    return {
                        "ok": True,
                        "action": "recent",
                        "scope_rel": rel,
                        "slug": only,
                    }
    except Exception:
        pass

    return {
        "ok": False,
        "action": "none",
        "reason": "proje_yok",
        "hint": "Proje adı yazın veya: «sıfırdan fastapi api yap benim-api»",
    }


def format_scope_report(result: dict[str, Any]) -> str:
    act = result.get("action")
    if act == "created":
        return (
            f"Ümit abi, yeni proje hazır: `{result.get('scope_rel')}` "
            f"({result.get('elapsed_sec', 0)} sn)"
            + (" · pytest yeşil" if result.get("verify_ok") else "")
            + f"\n({FAZ69_VERSION})"
        )
    if act in ("switched", "recent"):
        return (
            f"Ümit abi, aktif proje: `{result.get('scope_rel')}`\n({FAZ69_VERSION})"
        )
    if act == "active":
        return ""
    if not result.get("ok"):
        return (
            f"Ümit abi, proje kapsamı bulunamadı. {result.get('hint') or result.get('reason', '')}\n"
            f"({FAZ69_VERSION})"
        )
    return ""


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["faz69"] = faz69_enabled()
    return out


def faz69_directive() -> str:
    return (
        "[OTOMATİK PROJE — Faz 69]\n"
        "Proje seçili değilse: mesajdaki adı açar veya «sıfırdan api yap adim» ile oluşturur.\n"
        "Kapat: RUZGAR_FAZ69=0\n"
    )
