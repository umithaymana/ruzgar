# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 66: Tam repo sembol rename (Dalga G).

Faz 42 tek dosya rename üzerine: proje kapsamında tüm eşleşen dosyalarda
güvenli kelime sınırı değişimi + önizleme / dry-run.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

FAZ66_VERSION = "programlama-faz66-v1-2026-05-26"

_REPO_RENAME_RE = re.compile(
    r"^\s*(?:rename-repo|repo-rename|tum\s+repo\s+rename|tam\s+rename)\s*:\s*"
    r"(?:projects/)?([\w.\-]+)\s+([\w$]{1,80})\s*(?:->|→|,|to)\s*([\w$]{1,80})"
    r"(?:\s+(?:önizle|onizle|dry(?:-run)?))?\s*$",
    re.I,
)
_SCOPE_RENAME_RE = re.compile(
    r"^\s*(?:rename-scope|rename\s+tum|rename\s+tüm)\s+"
    r"([\w$]{1,80})\s*(?:->|→|,|to)\s*([\w$]{1,80})\s*$",
    re.I,
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ66", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz66_enabled() -> bool:
    return _enabled()


def max_files() -> int:
    try:
        return max(5, min(80, int(os.environ.get("RUZGAR_FAZ66_MAX_FILES", "40"))))
    except ValueError:
        return 40


def max_replacements_per_file() -> int:
    try:
        return max(1, min(200, int(os.environ.get("RUZGAR_FAZ66_MAX_PER_FILE", "80"))))
    except ValueError:
        return 80


def parse_repo_rename_command(message: str) -> dict[str, Any] | None:
    raw = (message or "").strip()
    m = _REPO_RENAME_RE.match(raw)
    if not m:
        return None
    slug, old, new = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
    return {
        "scope_rel": f"projects/{slug}".replace("\\", "/"),
        "old": old,
        "new": new,
        "dry_run": "önizle" in raw.lower() or "onizle" in raw.lower() or "dry" in raw.lower(),
    }


def parse_scope_rename_command(message: str) -> tuple[str, str] | None:
    m = _SCOPE_RENAME_RE.match((message or "").strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None


def wants_repo_rename(message: str) -> bool:
    if not _enabled():
        return False
    low = (message or "").lower()
    if parse_repo_rename_command(message):
        return True
    if parse_scope_rename_command(message):
        return True
    return any(
        k in low
        for k in (
            "rename-repo:",
            "repo-rename:",
            "rename-scope ",
            "rename tum ",
            "rename tüm ",
            "tam rename:",
        )
    )


def _ident_ok(name: str) -> bool:
    try:
        from ilim_assistant.motorlar.programlama_faz42 import _IDENT_RE

        return bool(_IDENT_RE.match(name))
    except Exception:
        return bool(re.match(r"^[A-Za-z_][\w$]{0,79}$", name))


def _files_in_scope(workspace_root: str | Path | None, scope_rel: str) -> list[str]:
    try:
        from ilim_assistant.motorlar.programlama_faz22 import _iter_code_files

        return list(
            _iter_code_files(workspace_root, scope_rel, max_files=max_files())
        )
    except Exception:
        return []


def _replace_in_file(
    workspace_root: str | Path | None,
    rel: str,
    old: str,
    new: str,
    *,
    dry_run: bool,
) -> dict[str, Any]:
    try:
        from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

        tools = ProgramlamaAraclari(workspace_root)
        rep = tools.read(rel, max_chars=200_000)
        if not rep.ok or rep.content is None:
            return {"rel": rel, "ok": False, "replacements": 0, "error": rep.error}
        word = re.compile(rf"\b{re.escape(old)}\b")
        lines = rep.content.splitlines(keepends=True)
        count = 0
        cap = max_replacements_per_file()
        new_lines: list[str] = []
        for line in lines:
            if count < cap and word.search(line):
                new_line, n = word.subn(new, line, cap - count)
                count += n
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        if count == 0:
            return {"rel": rel, "ok": True, "replacements": 0, "skipped": True}
        new_body = "".join(new_lines)
        if dry_run:
            return {"rel": rel, "ok": True, "replacements": count, "dry_run": True}
        wrep = tools.write(rel, new_body)
        return {
            "rel": rel,
            "ok": wrep.ok,
            "replacements": count,
            "detail": wrep.detail,
        }
    except Exception as exc:
        return {"rel": rel, "ok": False, "replacements": 0, "error": str(exc)[:120]}


def rename_symbol_in_scope(
    workspace_root: str | Path | None,
    scope_rel: str,
    old_name: str,
    new_name: str,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Proje kapsamında tüm kod dosyalarında sembol yeniden adlandırma."""
    old = (old_name or "").strip()
    new = (new_name or "").strip()
    scope = (scope_rel or "").strip().replace("\\", "/")
    if not scope.startswith("projects/"):
        scope = f"projects/{scope.lstrip('/')}"
    if not old or not new:
        return {"ok": False, "error": "eski/yeni ad eksik"}
    if not _ident_ok(old) or not _ident_ok(new):
        return {"ok": False, "error": "geçersiz tanımlayıcı"}

    refs_pre: dict[str, Any] = {}
    try:
        from ilim_assistant.motorlar.programlama_faz42 import find_references

        refs_pre = find_references(workspace_root, scope, old, max_hits=80)
    except Exception:
        pass

    rels = _files_in_scope(workspace_root, scope)
    if not rels and refs_pre.get("hits"):
        rels = sorted({str(h.get("rel")) for h in refs_pre.get("hits") or [] if h.get("rel")})
    if not rels:
        return {"ok": False, "error": "kapsamda dosya yok", "scope_rel": scope}

    file_results: list[dict[str, Any]] = []
    total = 0
    changed_files = 0
    for rel in rels:
        fr = _replace_in_file(workspace_root, rel, old, new, dry_run=dry_run)
        file_results.append(fr)
        n = int(fr.get("replacements") or 0)
        if n > 0:
            total += n
            changed_files += 1

    ok = total > 0 or dry_run
    return {
        "ok": ok,
        "scope_rel": scope,
        "old": old,
        "new": new,
        "dry_run": dry_run,
        "files_scanned": len(rels),
        "files_changed": changed_files,
        "replacements": total,
        "file_results": file_results,
        "refs_count": refs_pre.get("count"),
        "version": FAZ66_VERSION,
    }


def format_repo_rename_report(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return (
            f"Ümit abi, **tam repo rename** başarısız: {result.get('error', '?')}\n"
            f"({FAZ66_VERSION})"
        )
    mode = "önizleme" if result.get("dry_run") else "uygulandı"
    lines = [
        f"Ümit abi, **tam repo rename** ({mode}) — Faz 66",
        "",
        f"`{result.get('old')}` → `{result.get('new')}` · `{result.get('scope_rel')}`",
        f"Dosya: {result.get('files_changed')}/{result.get('files_scanned')} · "
        f"değişiklik: {result.get('replacements')}",
    ]
    if result.get("refs_count") is not None:
        lines.append(f"Referans taraması: {result.get('refs_count')} kullanım")
    shown = 0
    for fr in result.get("file_results") or []:
        n = int(fr.get("replacements") or 0)
        if n <= 0:
            continue
        lines.append(f"  · `{fr.get('rel')}` — {n}")
        shown += 1
        if shown >= 15:
            rest = int(result.get("files_changed") or 0) - 15
            if rest > 0:
                lines.append(f"  … +{rest} dosya")
            break
    if result.get("dry_run"):
        lines.append("")
        lines.append("Uygulamak için aynı komutu `önizle` olmadan tekrarlayın.")
    lines.append(f"\n({FAZ66_VERSION})")
    return "\n".join(lines)


def maybe_instant_faz66(
    message: str,
    workspace_root: str | Path | None,
    *,
    active_file: str | None = None,
) -> str | None:
    if not _enabled():
        return None
    parsed = parse_repo_rename_command(message)
    if parsed:
        res = rename_symbol_in_scope(
            workspace_root,
            parsed["scope_rel"],
            parsed["old"],
            parsed["new"],
            dry_run=bool(parsed.get("dry_run")),
        )
        return format_repo_rename_report(res)
    pair = parse_scope_rename_command(message)
    if pair:
        try:
            from ilim_assistant.motorlar.programlama_faz13 import resolve_scope_rel

            scope = resolve_scope_rel(
                workspace_root, active_file=active_file, message=message
            )
        except Exception:
            scope = None
        if not scope:
            return "Ümit abi, proje kapsamı seçin veya `rename-repo: proje eski -> yeni` yazın."
        dry = "önizle" in (message or "").lower() or "onizle" in (message or "").lower()
        old, new = pair
        res = rename_symbol_in_scope(workspace_root, scope, old, new, dry_run=dry)
        return format_repo_rename_report(res)
    return None


def execute_rename_repo_tool(
    workspace_root: str | Path | None,
    scope_rel: str,
    old_name: str,
    new_name: str,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    res = rename_symbol_in_scope(
        workspace_root,
        scope_rel,
        old_name,
        new_name,
        dry_run=dry_run,
    )
    return {
        "ok": bool(res.get("ok")),
        "tool": "rename_repo",
        "output": format_repo_rename_report(res)[:8000],
        "replacements": res.get("replacements", 0),
    }


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["faz66"] = faz66_enabled()
    out["repo_rename_max_files"] = max_files()
    return out


def faz66_directive() -> str:
    return (
        "[LSP REPO RENAME — Faz 66]\n"
        "`rename-repo: proje-adi eski -> yeni` · aktif proje: `rename-scope eski -> yeni`\n"
        "Önizle: komuta `önizle` ekle · Tek dosya: Faz 42 `rename eski -> yeni`\n"
        "Kapat: RUZGAR_FAZ66=0\n"
    )
