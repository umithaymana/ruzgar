# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 13: proje zekâsı v2.

- Detaylı proje taraması (dosya, boyut, dil)
- Sembol özeti (Python/JS hafif)
- Proje içi arama (@@find)
- «proje özeti» — LLM bağlam bloğu
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

from ilim_assistant.motorlar.programlama_motoru import repo_root

FAZ13_VERSION = "programlama-faz13-v1-2026-05-24"

_SKIP_DIRS = frozenset(
    {
        ".git",
        ".cursor",
        ".ruzgar",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        ".pytest_cache",
        "video_indirilen",
        "hafiza",
    }
)

_EXT_LANG: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".md": "markdown",
    ".toml": "toml",
    ".txt": "text",
}

_PY_SYM = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)|^\s*class\s+(\w+)", re.M)
_JS_SYM = re.compile(
    r"(?:export\s+)?(?:async\s+)?function\s+(\w+)|"
    r"export\s+default\s+function\s*(\w*)|"
    r"class\s+(\w+)",
    re.M,
)
_FIND_CMD_RE = re.compile(
    r"(?:@@find|proje\s+ara|find)\s+[:\"]?\s*([^\n\"']{2,120})",
    re.I,
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


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ13", "1").strip().lower() not in ("0", "false", "no")


def resolve_scope_rel(
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
    message: str = "",
) -> str | None:
    from ilim_assistant.motorlar.programlama_faz10 import resolve_scope_rel as _r10

    scope = _r10(workspace_root, active_file=active_file)
    if scope:
        return scope
    m = re.search(rf"{re.escape(_projects_base())}/[\w.\-]+", message or "", re.I)
    if m:
        return "/".join(_norm_rel(m.group(0)).split("/")[:2])
    return None


def _lang_for(path: Path) -> str:
    return _EXT_LANG.get(path.suffix.lower(), path.suffix.lstrip(".") or "file")


def scan_project_files(
    workspace_root: str | Path | None,
    scope_rel: str,
    *,
    max_files: int = 200,
) -> dict[str, Any]:
    """projects/<ad>/ altındaki dosya envanteri."""
    root = repo_root(workspace_root)
    scope = _norm_rel(scope_rel)
    if root is None:
        return {"ok": False, "error": "workspace_root yok"}
    if not scope.startswith(f"{_projects_base()}/"):
        return {"ok": False, "error": f"Yalnızca {_projects_base()}/<ad>/"}
    base = root / scope.replace("/", os.sep)
    if not base.is_dir():
        return {"ok": False, "error": f"Dizin yok: {scope}"}

    entries: list[dict[str, Any]] = []
    total_bytes = 0
    by_lang: dict[str, int] = {}

    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in _SKIP_DIRS and not d.startswith(".")
        ]
        for name in filenames:
            if len(entries) >= max_files:
                break
            if name.startswith("."):
                continue
            fp = Path(dirpath) / name
            try:
                rel = _norm_rel(str(fp.relative_to(root)))
                size = fp.stat().st_size
            except OSError:
                continue
            lang = _lang_for(fp)
            by_lang[lang] = by_lang.get(lang, 0) + 1
            total_bytes += size
            entries.append(
                {
                    "rel": rel,
                    "size": size,
                    "lang": lang,
                }
            )
        if len(entries) >= max_files:
            break

    return {
        "ok": True,
        "scope_rel": scope,
        "file_count": len(entries),
        "total_bytes": total_bytes,
        "by_lang": by_lang,
        "entries": entries,
        "truncated": len(entries) >= max_files,
        "version": FAZ13_VERSION,
    }


def extract_symbols_from_text(rel: str, text: str, *, cap: int = 40) -> list[str]:
    """Hafif sembol listesi (AST yok)."""
    path = _norm_rel(rel)
    syms: list[str] = []
    if path.endswith(".py"):
        for m in _PY_SYM.finditer(text or ""):
            name = m.group(1) or m.group(2)
            if name and name not in syms:
                syms.append(name)
    elif path.endswith((".js", ".jsx", ".ts", ".tsx")):
        for m in _JS_SYM.finditer(text or ""):
            name = m.group(1) or m.group(2) or m.group(3)
            if name and name not in syms:
                syms.append(name)
    return syms[:cap]


def collect_project_symbols(
    workspace_root: str | Path | None,
    scope_rel: str,
    *,
    max_files: int = 24,
) -> dict[str, Any]:
    scan = scan_project_files(workspace_root, scope_rel, max_files=max_files)
    if not scan.get("ok"):
        return scan
    root = repo_root(workspace_root)
    if root is None:
        return {"ok": False, "error": "workspace_root yok"}
    by_file: dict[str, list[str]] = {}
    code_ext = {".py", ".js", ".jsx", ".ts", ".tsx"}
    for ent in scan.get("entries") or []:
        rel = str(ent.get("rel") or "")
        if not any(rel.endswith(x) for x in code_ext):
            continue
        fp = root / rel.replace("/", os.sep)
        try:
            body = fp.read_text(encoding="utf-8", errors="replace")[:12000]
        except OSError:
            continue
        syms = extract_symbols_from_text(rel, body)
        if syms:
            by_file[rel] = syms
    return {
        "ok": True,
        "scope_rel": scope_rel,
        "symbols_by_file": by_file,
        "version": FAZ13_VERSION,
    }


def search_in_project(
    workspace_root: str | Path | None,
    scope_rel: str,
    pattern: str,
    *,
    max_hits: int = 20,
    max_file_bytes: int = 200_000,
) -> dict[str, Any]:
    root = repo_root(workspace_root)
    scope = _norm_rel(scope_rel)
    if root is None:
        return {"ok": False, "error": "workspace_root yok"}
    if not scope.startswith(f"{_projects_base()}/"):
        return {"ok": False, "error": f"Yalnızca {_projects_base()}/ altı"}
    base = root / scope.replace("/", os.sep)
    if not base.is_dir():
        return {"ok": False, "error": f"Dizin yok: {scope}"}

    pat = (pattern or "").strip()
    if len(pat) < 2:
        return {"ok": False, "error": "Arama deseni çok kısa"}
    try:
        rx = re.compile(pat, re.I)
    except re.error:
        rx = re.compile(re.escape(pat), re.I)

    hits: list[dict[str, Any]] = []
    for dirpath, dirnames, filenames in os.walk(base):
        if len(hits) >= max_hits:
            break
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if len(hits) >= max_hits:
                break
            fp = Path(dirpath) / name
            try:
                if fp.stat().st_size > max_file_bytes:
                    continue
                body = fp.read_text(encoding="utf-8", errors="replace")
            except (OSError, UnicodeDecodeError):
                continue
            for i, line in enumerate(body.splitlines(), 1):
                if rx.search(line):
                    rel = _norm_rel(str(fp.relative_to(root)))
                    hits.append(
                        {
                            "rel": rel,
                            "line": i,
                            "text": line.strip()[:200],
                        }
                    )
                    if len(hits) >= max_hits:
                        break

    return {
        "ok": True,
        "scope_rel": scope,
        "pattern": pat,
        "hits": hits,
        "version": FAZ13_VERSION,
    }


def detect_entrypoints(scope_rel: str, entries: list[dict[str, Any]]) -> list[str]:
    rels = {str(e.get("rel") or "") for e in entries}
    candidates = [
        f"{scope_rel}/app/main.py",
        f"{scope_rel}/main.py",
        f"{scope_rel}/bot.py",
        f"{scope_rel}/index.html",
        f"{scope_rel}/src/main.jsx",
        f"{scope_rel}/src/App.jsx",
        f"{scope_rel}/package.json",
    ]
    return [c for c in candidates if c in rels]


def build_project_summary_block(
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    active_file: str | None = None,
) -> str:
    """LLM için tek sayfalık proje özeti."""
    if not _enabled():
        return ""
    scope = scope_rel or resolve_scope_rel(workspace_root, active_file=active_file)
    if not scope:
        return ""
    scan = scan_project_files(workspace_root, scope, max_files=120)
    if not scan.get("ok"):
        return f"[PROJE ÖZETİ — hata: {scan.get('error')}]\n"

    sym = collect_project_symbols(workspace_root, scope, max_files=20)
    syms_map = sym.get("symbols_by_file") if isinstance(sym, dict) else {}
    if not isinstance(syms_map, dict):
        syms_map = {}

    lines = [
        f"[PROJE ÖZETİ — Faz 13 — {scope}]",
        f"Dosya sayısı: {scan.get('file_count')} · "
        f"Toplam ~{scan.get('total_bytes', 0) // 1024} KB",
        "",
    ]
    by_lang = scan.get("by_lang") or {}
    if by_lang:
        lang_bits = ", ".join(f"{k}:{v}" for k, v in sorted(by_lang.items()))
        lines.append(f"Diller: {lang_bits}")
    eps = detect_entrypoints(scope, scan.get("entries") or [])
    if eps:
        lines.append("")
        lines.append("Giriş noktaları:")
        for ep in eps:
            lines.append(f"  · {ep}")

    lines.append("")
    lines.append("Semboller (örnek):")
    shown = 0
    for rel, names in syms_map.items():
        if shown >= 12:
            lines.append("  …")
            break
        lines.append(f"  · {rel}: {', '.join(names[:8])}")
        shown += 1

    lines.append("")
    lines.append("Dosyalar (ilk 40):")
    for ent in (scan.get("entries") or [])[:40]:
        rel = ent.get("rel")
        size = int(ent.get("size") or 0)
        lang = ent.get("lang")
        lines.append(f"  · {rel} ({lang}, {size} B)")

    if scan.get("truncated"):
        lines.append("  … (liste kısaltıldı)")
    lines.append("")
    lines.append("Araçlar: `@@find desen` · `proje özeti` · `@@read yol`")
    lines.append(f"({FAZ13_VERSION})")
    return "\n".join(lines)


def parse_find_pattern(message: str) -> str | None:
    m = _FIND_CMD_RE.search(message or "")
    if m:
        return m.group(1).strip().strip('"').strip("'")
    if "@@find" in _ascii_fold(message):
        parts = (message or "").split("@@find", 1)
        if len(parts) > 1:
            return parts[1].strip().split("\n")[0][:120]
    return None


def expand_find_paths(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
    max_hits: int = 8,
) -> list[str]:
    """@@find sonuçlarını @@read genişletmesi için yollar."""
    pat = parse_find_pattern(message)
    if not pat:
        return []
    scope = resolve_scope_rel(workspace_root, active_file=active_file, message=message)
    if not scope:
        return []
    res = search_in_project(workspace_root, scope, pat, max_hits=max_hits)
    return [str(h.get("rel") or "") for h in (res.get("hits") or []) if h.get("rel")]


def wants_project_scan_instant(message: str) -> bool:
    """Anında tarama (Faz 5 «proje özeti» = oturum bağlamı)."""
    low = _ascii_fold(message)
    return any(
        k in low
        for k in (
            "proje tara",
            "projeyi tara",
            "proje haritasi",
            "proje haritası",
            "proje indeks detay",
            "proje dosya",
            "project scan",
            "workspace tara",
        )
    )


def wants_find_command(message: str) -> bool:
    low = _ascii_fold(message)
    return "@@find" in low or bool(_FIND_CMD_RE.search(message or "")) or low.startswith("find ")


def format_scan_report(scan: dict[str, Any]) -> str:
    if not scan.get("ok"):
        return f"Proje taraması başarısız: {scan.get('error')}"
    lines = [
        f"Ümit abi, **{scan.get('scope_rel')}** — Faz 13 tarama",
        "",
        f"Dosya: **{scan.get('file_count')}** · ~{int(scan.get('total_bytes', 0)) // 1024} KB",
        "",
    ]
    by_lang = scan.get("by_lang") or {}
    if by_lang:
        lines.append("Diller: " + ", ".join(f"{k} ({v})" for k, v in sorted(by_lang.items())))
    eps = detect_entrypoints(
        str(scan.get("scope_rel") or ""),
        scan.get("entries") or [],
    )
    if eps:
        lines.append("")
        lines.append("Giriş:")
        for ep in eps:
            lines.append(f"  · `{ep}`")
    lines.extend(["", f"({FAZ13_VERSION})"])
    return "\n".join(lines)


def format_find_report(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return f"Arama yapılamadı: {result.get('error')}"
    hits = result.get("hits") or []
    lines = [
        f"Ümit abi, `{result.get('scope_rel')}` içinde **{result.get('pattern')}**:",
        "",
    ]
    if not hits:
        lines.append("Eşleşme yok.")
    else:
        for h in hits:
            lines.append(f"· `{h.get('rel')}`:{h.get('line')} — {h.get('text')}")
    lines.append(f"\n({FAZ13_VERSION})")
    return "\n".join(lines)


def format_summary_instant(
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
    message: str = "",
) -> str | None:
    scope = resolve_scope_rel(workspace_root, active_file=active_file, message=message)
    if not scope:
        return (
            "Ümit abi, `proje özeti` için `projects/<ad>/` yolunu yaz "
            "veya atölyede proje dosyası aç."
        )
    block = build_project_summary_block(workspace_root, scope_rel=scope)
    scan = scan_project_files(workspace_root, scope)
    head = format_scan_report(scan) if scan.get("ok") else ""
    return f"{head}\n\n```\n{block.strip()}\n```"


def maybe_instant_faz13(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> str | None:
    if not _enabled():
        return None
    scope = resolve_scope_rel(workspace_root, active_file=active_file, message=message)

    if wants_project_scan_instant(message):
        return format_summary_instant(
            workspace_root, active_file=active_file, message=message
        )

    if wants_find_command(message):
        pat = parse_find_pattern(message)
        if not pat:
            return "Ümit abi, `@@find <desen>` veya `find: health` yaz."
        if not scope:
            return "Ümit abi, arama için proje kapsamı gerekli (`projects/...` açık veya yol yaz)."
        return format_find_report(search_in_project(workspace_root, scope, pat))

    return None


def faz13_directive() -> str:
    return (
        "[PROJE ZEKÂSI — Faz 13]\n"
        "Komutlar: `proje özeti` · `@@find <desen>` · giriş: app/main.py, index.html, src/App.jsx\n"
    )
