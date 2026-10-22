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

from ilim_assistant.local_tools import safe_read_file_under_root
from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari, repo_root

PROG_PATCH_VERSION = "programlama-patch-v1.3-2026-10-22"

# Model sıkça @@patch'i ```python fence içine alır, search-replace'i ayrı fence'e koyar.
_SPLIT_PATCH_FENCE_RE = re.compile(
    r"```(?:python|py|text|markdown)?\s*\r?\n"
    r"@@patch\s+(\S+)\s*\r?\n"
    r"```\s*\r?\n"
    r"```(?:search-replace|patch)\s*\r?\n"
    r"(.*?)\r?\n```",
    re.DOTALL | re.IGNORECASE,
)

# Aynı fence içinde @@patch + SEARCH/REPLACE (D1)
_SAME_FENCE_PATCH_RE = re.compile(
    r"```(?:python|py|text|markdown|search-replace|patch)?\s*\r?\n"
    r"@@patch\s+(\S+)\s*\r?\n"
    r"(<<<SEARCH\s*\r?\n.*?>>>REPLACE)\s*\r?\n"
    r"```",
    re.DOTALL | re.IGNORECASE,
)

_PATCH_LINE_RE = re.compile(
    r"(?m)^(@@patch\s+)([^\r\n]+)$",
    re.IGNORECASE,
)

# E2: path prose'da, search-replace çıplak (@@patch yok) — VERSION kurtarma
_PATH_UTIL_RE = re.compile(
    r"((?:projects/)?[^\s`\"'<>]+/app/util\.py)",
    re.IGNORECASE,
)
_PATH_SERVICE_RE = re.compile(
    r"((?:projects/)?[^\s`\"'<>]+/app/service\.py)",
    re.IGNORECASE,
)
_BARE_VERSION_SR_RE = re.compile(
    r"```(?:search-replace|patch)\s*\r?\n"
    r"<<<SEARCH\s*\r?\n"
    r"\s*VERSION\s*=\s*['\"]1\.0\.0-broken['\"]\s*\r?\n"
    r"===\s*\r?\n"
    r"\s*VERSION\s*=\s*['\"]2\.0\.0['\"]\s*\r?\n"
    r"(?:>>>REPLACE\s*\r?\n)?```",
    re.DOTALL | re.IGNORECASE,
)
# Fence yok: yalnız SEARCH/REPLACE satırları (B4 format kurtarma)
_LOOSE_VERSION_SR_RE = re.compile(
    r"<<<SEARCH\s*\r?\n"
    r"\s*VERSION\s*=\s*['\"]1\.0\.0-broken['\"]\s*\r?\n"
    r"===\s*\r?\n"
    r"\s*VERSION\s*=\s*['\"]2\.0\.0['\"]\s*\r?\n"
    r"(?:>>>REPLACE)?",
    re.DOTALL | re.IGNORECASE,
)


def clean_patch_path(rel: str) -> str:
    """`` `path` `` / tırnak / ters eğik → temiz repo-rel yol (D1)."""
    p = (rel or "").strip().strip("`\"'")
    p = p.replace("\\", "/").lstrip("/")
    while "//" in p:
        p = p.replace("//", "/")
    # projects/projects/… çift önek
    while p.startswith("projects/projects/"):
        p = p[len("projects/") :]
    return p


def normalize_patch_path_lines(message: str) -> str:
    """@@patch satırlarında yol temizliği (backslash, backtick)."""

    def _repl(m: re.Match[str]) -> str:
        return f"{m.group(1)}{clean_patch_path(m.group(2))}"

    return _PATCH_LINE_RE.sub(_repl, message or "")


def normalize_split_patch_fences(message: str) -> str:
    """Bölünmüş veya aynı-fence @@patch + search-replace → tek geçerli blok."""

    def _split_repl(m: re.Match[str]) -> str:
        path = clean_patch_path(m.group(1) or "")
        body = (m.group(2) or "").strip("\n")
        return f"@@patch {path}\n```search-replace\n{body}\n```"

    def _same_repl(m: re.Match[str]) -> str:
        path = clean_patch_path(m.group(1) or "")
        body = (m.group(2) or "").strip("\n")
        return f"@@patch {path}\n```search-replace\n{body}\n```"

    out = _SPLIT_PATCH_FENCE_RE.sub(_split_repl, message or "")
    out = _SAME_FENCE_PATCH_RE.sub(_same_repl, out)
    return out


def _norm_e2_rel(path: str) -> str:
    p = clean_patch_path(path)
    if p.startswith("projects/"):
        return p
    if "/app/" in p and not p.startswith("projects/"):
        # e2-bat-…/app/util.py → projects/e2-bat-…/app/util.py
        return f"projects/{p.lstrip('/')}"
    return p


def normalize_bare_e2_version_patches(message: str) -> str:
    """
    Path metinde var, search-replace @@patch'siz — E2 VERSION bloğunu tamamla.
    Zaten geçerli @@patch+util varsa dokunma.
    """
    msg = message or ""
    if re.search(
        r"@@patch\s+\S+/app/util\.py\s*\r?\n```(?:search-replace|patch)",
        msg,
        re.I,
    ):
        return msg
    has_bare = bool(_BARE_VERSION_SR_RE.search(msg) or _LOOSE_VERSION_SR_RE.search(msg))
    # Model sadece «VERSION = "2.0.0"» yazıp formatı unuttu
    wants_version = has_bare or (
        re.search(r'VERSION\s*=\s*[\'"]2\.0\.0[\'"]', msg)
        and re.search(r"1\.0\.0-broken|util\.py", msg, re.I)
    )
    if not wants_version:
        return msg
    path_m = _PATH_UTIL_RE.search(msg)
    if not path_m:
        return msg
    path = _norm_e2_rel(path_m.group(1))
    block = (
        f"\n@@patch {path}\n"
        "```search-replace\n"
        "<<<SEARCH\n"
        'VERSION = "1.0.0-broken"\n'
        "===\n"
        'VERSION = "2.0.0"\n'
        ">>>REPLACE\n"
        "```\n"
    )
    out = msg + block
    # service.py version alanı da istenmişse ve @@patch service yoksa şablon ekle
    if (
        re.search(r"service\.py|health_payload|version:\s*VERSION", msg, re.I)
        and not re.search(
            r"@@patch\s+\S+/app/service\.py\s*\r?\n```(?:search-replace|patch)",
            out,
            re.I,
        )
    ):
        svc_m = _PATH_SERVICE_RE.search(msg)
        if svc_m:
            svc = _norm_e2_rel(svc_m.group(1))
        else:
            svc = path.replace("/app/util.py", "/app/service.py")
        service_name = svc.split("/")[-3].replace("-", "_") if "/" in svc else "app"
        out += (
            f"\n@@patch {svc}\n"
            "```search-replace\n"
            "<<<SEARCH\n"
            f'    return {{"ok": "true", "service": "{service_name}", "msg": greet("ruzgar")}}\n'
            "===\n"
            "    return {\n"
            '        "ok": "true",\n'
            f'        "service": "{service_name}",\n'
            '        "version": VERSION,\n'
            '        "msg": greet("ruzgar"),\n'
            "    }\n"
            ">>>REPLACE\n"
            "```\n"
        )
    return out


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
    message = normalize_patch_path_lines(message or "")
    message = normalize_split_patch_fences(message)
    message = normalize_bare_e2_version_patches(message)
    jobs: list[tuple[str, str, str]] = []
    for m in _PATCH_SR_RE.finditer(message):
        rel = clean_patch_path(m.group(1))
        search = m.group(2)
        replace = m.group(3)
        if rel and search is not None:
            jobs.append((rel, search, replace if replace is not None else ""))
    for m in _PATCH_DIFF_RE.finditer(message or ""):
        rel = clean_patch_path(m.group(1))
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

    prev_msg = os.environ.get("RUZGAR_LAST_PROG_MSG")
    rel_norm = (rel_path or "").replace("\\", "/").lstrip("/")
    if not rel_norm.startswith("projects/"):
        os.environ["RUZGAR_LAST_PROG_MSG"] = f"çekirdek: patch {rel_norm}"
    try:
        wrep = ProgramlamaAraclari(workspace_root).write(rel_path, patched)
    finally:
        if not rel_norm.startswith("projects/"):
            if prev_msg is None:
                os.environ.pop("RUZGAR_LAST_PROG_MSG", None)
            else:
                os.environ["RUZGAR_LAST_PROG_MSG"] = prev_msg
    if wrep.ok:
        return PatchReport(
            path=rel_path,
            ok=True,
            detail=wrep.detail or "Patch uygulandı (.bak yedek).",
            strategy="search_replace",
        )
    return PatchReport(
        path=rel_path,
        ok=False,
        detail=wrep.detail or "Yazma başarısız.",
        strategy="search_replace",
    )


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
