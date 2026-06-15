# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 29: Çoklu proje workspace.

- `projects/` altındaki tüm projeleri listele
- Aktif proje oturumda (`active_project`, `recent_projects`)
- `proje listesi` · `proje sec: <ad>` · API switch
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import repo_root

FAZ29_VERSION = "programlama-faz29-v1-2026-05-25"
_MAX_PROJECTS = 48
_FOCUS_CANDIDATES = (
    "main.py",
    "app/main.py",
    "src/main.py",
    "App.js",
    "src/App.jsx",
    "src/App.tsx",
    "index.html",
    "package.json",
    "README.md",
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ29", "1").strip().lower() not in (
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


def _norm_rel(rel: str) -> str:
    return (rel or "").strip().replace("\\", "/").lstrip("/")


def _slug_ok(name: str) -> bool:
    return bool(re.match(r"^[\w.\-]{1,64}$", (name or "").strip()))


def project_rel(slug: str) -> str:
    return f"{_projects_base()}/{slug.strip()}"


def discover_projects(workspace_root: str | Path | None) -> list[dict[str, Any]]:
    """Workspace altındaki proje klasörleri."""
    root = repo_root(workspace_root)
    if root is None:
        return []
    base = root / _projects_base().replace("/", os.sep)
    if not base.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    try:
        names = sorted(
            p.name
            for p in base.iterdir()
            if p.is_dir() and not p.name.startswith(".")
        )
    except OSError:
        return []
    for name in names[:_MAX_PROJECTS]:
        if not _slug_ok(name):
            continue
        pdir = base / name
        file_count = 0
        try:
            for _ in pdir.rglob("*"):
                if _.is_file():
                    file_count += 1
                    if file_count > 500:
                        break
        except OSError:
            file_count = 0
        rows.append(
            {
                "slug": name,
                "rel": project_rel(name),
                "file_count": file_count,
                "has_git": (pdir / ".git").is_dir(),
            }
        )
    return rows


def pick_default_focus_rel(
    workspace_root: str | Path | None,
    project_rel_path: str,
) -> str | None:
    rel = _norm_rel(project_rel_path)
    if not rel.startswith(f"{_projects_base()}/"):
        return None
    root = repo_root(workspace_root)
    if root is not None:
        for cand in _FOCUS_CANDIDATES:
            full = root / f"{rel}/{cand}".replace("/", os.sep)
            if full.is_file():
                return f"{rel}/{cand}"
    return f"{rel}/main.py"


def get_workspace_projects_state(
    workspace_root: str | Path | None,
) -> dict[str, Any]:
    from ilim_assistant.motorlar.programlama_faz5 import load_session

    projects = discover_projects(workspace_root)
    sess = load_session(workspace_root)
    active = str(sess.get("active_project") or sess.get("project", {}).get("name") or "").strip()
    recent = [str(x).strip() for x in (sess.get("recent_projects") or []) if str(x).strip()]
    if active and active not in recent:
        recent = [active] + recent
    return {
        "ok": True,
        "active_project": active,
        "recent_projects": recent[:8],
        "projects": projects,
        "version": FAZ29_VERSION,
    }


def switch_to_project(
    workspace_root: str | Path | None,
    project_slug: str,
) -> dict[str, Any]:
    slug = (project_slug or "").strip()
    if not slug or not _slug_ok(slug):
        return {"ok": False, "error": "Geçersiz proje adı"}
    root = repo_root(workspace_root)
    if root is None:
        return {"ok": False, "error": "workspace_root yok"}
    rel = project_rel(slug)
    pdir = root / rel.replace("/", os.sep)
    if not pdir.is_dir():
        return {"ok": False, "error": f"Proje yok: {rel}"}

    from ilim_assistant.motorlar.programlama_faz5 import load_session, save_session

    sess = load_session(workspace_root)
    sess["active_project"] = slug
    proj = dict(sess.get("project") or {})
    proj["name"] = slug
    sess["project"] = proj
    recent = [slug] + [x for x in (sess.get("recent_projects") or []) if x != slug]
    sess["recent_projects"] = recent[:8]
    save_session(workspace_root, sess)

    focus_rel = pick_default_focus_rel(workspace_root, rel)
    if focus_rel:
        try:
            from ilim_assistant.motorlar.programlama_faz5 import sync_client_editor_state

            sync_client_editor_state(workspace_root, active_file=focus_rel)
        except Exception:
            pass

    return {
        "ok": True,
        "active_project": slug,
        "project_rel": rel,
        "focus_rel": focus_rel,
        "expand_tree": True,
        "version": FAZ29_VERSION,
    }


def parse_project_switch(message: str) -> str | None:
    m = re.search(
        r"(?:proje\s+sec|proje\s+seç|proje\s+degistir|proje\s+değiştir|aktif\s+proje)\s*[:\"]?\s*([\w.\-]+)",
        message or "",
        re.I,
    )
    if m:
        return m.group(1).strip()
    return None


def wants_project_list(message: str) -> bool:
    try:
        from ilim_assistant.motorlar.programlama_faz5 import wants_project_recall

        if wants_project_recall(message):
            return False
    except Exception:
        pass
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "proje listesi",
            "proje listele",
            "projeler",
            "workspace projeler",
            "hangi proje",
        )
    )


def wants_project_switch(message: str) -> bool:
    return bool(parse_project_switch(message))


def format_projects_report(state: dict[str, Any]) -> str:
    active = state.get("active_project") or "(yok)"
    lines = [
        "Ümit abi, **workspace projeleri** (Faz 29)",
        "",
        f"Aktif: **{active}**",
        "",
    ]
    for p in state.get("projects") or []:
        mark = "→ " if p.get("slug") == state.get("active_project") else "  "
        git = " · git" if p.get("has_git") else ""
        lines.append(
            f"{mark}`{p.get('slug')}` — {p.get('file_count', 0)} dosya{git}"
        )
    if not state.get("projects"):
        lines.append("_(henüz proje yok — + API / + Site ile oluşturun)_")
    lines.append("\n`proje sec: <ad>` ile geçiş yapın.")
    lines.append(f"({FAZ29_VERSION})")
    return "\n".join(lines)


def maybe_instant_faz29(
    message: str,
    workspace_root: str | Path | None,
) -> str | dict[str, Any] | None:
    if not _enabled():
        return None
    if wants_project_switch(message):
        slug = parse_project_switch(message)
        if not slug:
            return "Ümit abi, `proje sec: benim-api` yazın."
        res = switch_to_project(workspace_root, slug)
        if not res.get("ok"):
            return f"Proje geçişi: {res.get('error')} ({FAZ29_VERSION})"
        text = (
            f"Ümit abi, aktif proje **`{slug}`** (`{res.get('project_rel')}`).\n"
            f"({FAZ29_VERSION})"
        )
        return {
            "text": text,
            "focus_rel": res.get("focus_rel"),
            "project_rel": res.get("project_rel"),
            "expand_tree": True,
        }
    if wants_project_list(message):
        return format_projects_report(get_workspace_projects_state(workspace_root))
    return None


def faz29_directive() -> str:
    return (
        "[ÇOKLU PROJE — Faz 29]\n"
        "Komutlar: `proje listesi` · `proje sec: benim-api`\n"
        "Atölye üstündeki proje listesinden de geçiş yapılır.\n"
    )
