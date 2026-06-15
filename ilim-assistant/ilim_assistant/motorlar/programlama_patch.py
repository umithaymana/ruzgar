# Created by Ümit & Gökçenur
"""
Programlama motoru — cerrahi patch (search-replace).

Formatlar:
  @@patch yol
  ```patch
  --- eski
  +++ yeni
  ```

  veya fenced search-replace:
  @@patch yol
  ```search-replace
  <<<SEARCH
  eski metin
  ===
  yeni metin
  >>>REPLACE
  ```
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from ilim_assistant.local_tools import safe_read_file_under_root, safe_write_file_under_root
from ilim_assistant.motorlar.programlama_motoru import repo_root

PROG_PATCH_VERSION = "programlama-patch-v1-2026-06-15"


def _normalize_newlines(text: str) -> str:
    return (text or "").replace("\r\n", "\n").replace("\r", "\n")


def _apply_normalized_replace(content: str, search: str, replace: str) -> tuple[str, int]:
    """LF normalize ederek benzersiz eşleşme say."""
    norm_content = _normalize_newlines(content)
    norm_search = _normalize_newlines(search)
    norm_replace = _normalize_newlines(replace)
    count = norm_content.count(norm_search)
    if count != 1:
        return content, count
    patched_norm = norm_content.replace(norm_search, norm_replace, 1)
    if "\r\n" in content:
        return patched_norm.replace("\n", "\r\n"), 1
    return patched_norm, 1

_PATCH_SR_RE = re.compile(
    r"@@patch\s+(\S+)\s*\r?\n```(?:search-replace|patch)\s*\r?\n"
    r"<<<SEARCH\s*\r?\n(.*?)===\s*\r?\n(.*?)>>>REPLACE\s*\r?\n```",
    re.DOTALL | re.IGNORECASE,
)
_PATCH_DIFF_RE = re.compile(
    r"@@patch\s+(\S+)\s*\r?\n```(?:patch|diff)\s*\r?\n(.*?)\r?\n```",
    re.DOTALL | re.IGNORECASE,
)


@dataclass
class PatchReport:
    path: str
    ok: bool
    detail: str = ""
    strategy: str = ""


def patch_enabled() -> bool:
    return os.environ.get("RUZGAR_PROG_SURGICAL_PATCH", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def patch_directive() -> str:
    return (
        "[CERRAHİ PATCH — Faz P1]\n"
        "Küçük değişikliklerde tam dosya yerine `@@patch yol` + search-replace bloğu kullan:\n"
        "```search-replace\n"
        "<<<SEARCH\n"
        "eski satırlar\n"
        "===\n"
        "yeni satırlar\n"
        ">>>REPLACE\n"
        "```\n"
        "Eşleşme tek ve benzersiz olmalı; yoksa @@write ile tam dosya yaz.\n"
    )


def extract_patch_jobs(message: str) -> list[tuple[str, str, str]]:
    """(rel_path, search, replace) listesi."""
    jobs: list[tuple[str, str, str]] = []
    for m in _PATCH_SR_RE.finditer(message or ""):
        rel = m.group(1).strip().replace("\\", "/").lstrip("/")
        search = m.group(2)
        replace = m.group(3)
        if rel and search is not None:
            jobs.append((rel, search, replace if replace is not None else ""))
    for m in _PATCH_DIFF_RE.finditer(message or ""):
        rel = m.group(1).strip().replace("\\", "/").lstrip("/")
        body = m.group(2) or ""
        parsed = _parse_simple_diff(body)
        if rel and parsed:
            jobs.append((rel, parsed[0], parsed[1]))
    return jobs


def _parse_simple_diff(body: str) -> tuple[str, str] | None:
    """--- / +++ satırlarından tek blok çıkar."""
    old_lines: list[str] = []
    new_lines: list[str] = []
    mode = None
    for line in body.splitlines():
        if line.startswith("---"):
            mode = "old"
            rest = line[3:].strip()
            if rest:
                old_lines.append(rest)
            continue
        if line.startswith("+++"):
            mode = "new"
            rest = line[3:].strip()
            if rest:
                new_lines.append(rest)
            continue
        if mode == "old":
            old_lines.append(line)
        elif mode == "new":
            new_lines.append(line)
    if not old_lines and not new_lines:
        return None
    return "\n".join(old_lines), "\n".join(new_lines)


def apply_search_replace(
    workspace_root: str | Path | None,
    rel_path: str,
    search: str,
    replace: str,
) -> PatchReport:
    """Tek search-replace; benzersiz eşleşme zorunlu."""
    root = repo_root(workspace_root)
    if root is None:
        return PatchReport(path=rel_path, ok=False, detail="Proje kökü yok.", strategy="search_replace")
    try:
        from ilim_assistant.motorlar.programlama_faz3 import programlama_write_allowed

        allowed, reason = programlama_write_allowed(root, rel_path)
        if not allowed:
            return PatchReport(path=rel_path, ok=False, detail=reason or "yazma reddedildi", strategy="search_replace")
    except Exception:
        pass

    content, err = safe_read_file_under_root(root, rel_path, 512_000)
    if err:
        return PatchReport(path=rel_path, ok=False, detail=err, strategy="search_replace")

    count = content.count(search)
    if count == 0:
        patched, count = _apply_normalized_replace(content, search, replace)
        if count != 1:
            return PatchReport(
                path=rel_path,
                ok=False,
                detail="SEARCH metni dosyada bulunamadı.",
                strategy="search_replace",
            )
    elif count > 1:
        return PatchReport(
            path=rel_path,
            ok=False,
            detail=f"SEARCH metni {count} kez bulundu — benzersiz olmalı.",
            strategy="search_replace",
        )
    else:
        patched = content.replace(search, replace, 1)

    try:
        from ilim_assistant.motorlar.programlama_faz4 import validate_write_content

        ok_content, creason = validate_write_content(patched)
        if not ok_content:
            return PatchReport(path=rel_path, ok=False, detail=creason, strategy="search_replace")
    except Exception:
        pass

    ok = safe_write_file_under_root(root, rel_path, patched)
    if ok:
        return PatchReport(
            path=rel_path,
            ok=True,
            detail="Patch uygulandı (.bak yedek).",
            strategy="search_replace",
        )
    return PatchReport(path=rel_path, ok=False, detail="Yazma başarısız.", strategy="search_replace")


def apply_patch_jobs(
    message: str,
    workspace_root: str | Path | None,
) -> list[PatchReport]:
    if not patch_enabled():
        return []
    reports: list[PatchReport] = []
    for rel, search, replace in extract_patch_jobs(message):
        reports.append(apply_search_replace(workspace_root, rel, search, replace))
    return reports


def run_monorepo_patch_smoke(workspace_root: str | Path | None) -> dict[str, object]:
    """S6 ladder — geçici dosyada cerrahi patch doğrula."""
    root = repo_root(workspace_root)
    if root is None:
        return {"ok": False, "detail": "root_missing"}
    rel = "projects/.ruzgar_patch_smoke/test_patch.txt"
    full = root / rel.replace("/", os.sep)
    full.parent.mkdir(parents=True, exist_ok=True)
    original = "VERSION = 1\nNAME = smoke\n"
    full.write_text(original, encoding="utf-8")
    msg = (
        f"@@patch {rel}\n"
        "```search-replace\n"
        "<<<SEARCH\n"
        "VERSION = 1\n"
        "===\n"
        "VERSION = 2\n"
        ">>>REPLACE\n"
        "```"
    )
    reps = apply_patch_jobs(msg, root)
    ok = bool(reps) and reps[0].ok
    if ok:
        expected = _normalize_newlines("VERSION = 2\nNAME = smoke\n")
        actual = _normalize_newlines(full.read_text(encoding="utf-8"))
        ok = actual == expected
    try:
        full.unlink(missing_ok=True)
    except OSError:
        pass
    return {
        "ok": ok,
        "detail": reps[0].detail if reps else "no_jobs",
        "version": PROG_PATCH_VERSION,
    }
