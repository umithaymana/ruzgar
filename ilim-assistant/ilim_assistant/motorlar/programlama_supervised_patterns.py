"""
P1 — Supervised pattern kütüphanesi (2026-10-23).

LLM 0 yazımda deterministik yama: VERSION/health ötesi sık niyetler.
Kapat: RUZGAR_E2_SUPERVISED_BOOT=0 (faz103 ile aynı bayrak).

Sıra (ilk eşleşen + başarılı yazım kazanır):
  1) e2_version
  2) health_fields
  3) import_fix
  4) dict_field
  5) ping_route
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

P1_PATTERNS_VERSION = "programlama-supervised-patterns-p1-v1-2026-10-23"

_IMPORT_GOAL_RE = re.compile(
    r"\b(import\s*(d[uü]zelt|fix|ekle)|eksik\s*import|ImportError|NameError|"
    r"from\s+app\.util\s+import)\b",
    re.I,
)
_DICT_FIELD_RE = re.compile(
    r"""(?:['"]?)([a-z_][a-z0-9_]{1,32})(?:['"]?)\s*(?:alan[ıi]?|field)\s*(?:ekle|yaz|koy)""",
    re.I,
)
_PING_ROUTE_RE = re.compile(
    r"\b(/?ping|ping\s*(endpoint|route|yolu)?|endpoint\s*ekle|route\s*ekle)\b",
    re.I,
)


def patterns_enabled() -> bool:
    return os.environ.get("RUZGAR_E2_SUPERVISED_BOOT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


@dataclass
class PatternHit:
    ok: bool = False
    writes_ok: int = 0
    paths: list[str] = field(default_factory=list)
    detail: str = ""
    pattern_id: str = ""
    source: str = "supervised_pattern"

    def as_boot_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "writes_ok": self.writes_ok,
            "paths": list(self.paths),
            "detail": self.detail,
            "source": self.source or f"pattern:{self.pattern_id}",
            "pattern_id": self.pattern_id,
            "version": P1_PATTERNS_VERSION,
        }


def _repo(workspace_root: str | Path | None) -> Path | None:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        return repo_root(workspace_root)
    except Exception:
        return None


def _scope_dir(root: Path, scope_rel: str) -> Path:
    return root / scope_rel.replace("/", os.sep)


def _ascii(s: str) -> str:
    try:
        from ilim_assistant.motorlar.programlama_faz103_e2 import _ascii_fold

        return _ascii_fold(s or "")
    except Exception:
        return (s or "").lower()


# --- pattern: e2_version (klasik) -------------------------------------------------


def _match_e2_version(goal: str) -> bool:
    try:
        from ilim_assistant.motorlar.programlama_faz103_e2 import _e2_multi_goal

        return bool(_e2_multi_goal(goal) or "version" in _ascii(goal))
    except Exception:
        return "version" in _ascii(goal)


def _apply_e2_version(
    workspace_root: str | Path | None, scope_rel: str, goal: str
) -> PatternHit:
    empty = PatternHit(pattern_id="e2_version", source="pattern:e2_version")
    try:
        from ilim_assistant.motorlar.programlama_faz103_e2 import (
            _e2_multi_goal,
            _e2_multi_version_patch,
            _e2_version_broken_on_disk,
        )
        from ilim_assistant.motorlar.programlama_patch import apply_patch_jobs

        if not (_e2_multi_goal(goal) and _e2_version_broken_on_disk(workspace_root, scope_rel)):
            empty.detail = "e2_version aday değil"
            return empty
        root = _repo(workspace_root)
        if root is None:
            empty.detail = "repo yok"
            return empty
        reps = apply_patch_jobs(_e2_multi_version_patch(scope_rel), root)
        paths = [getattr(r, "path", "") for r in reps if r.ok and getattr(r, "path", "")]
        if not paths:
            empty.detail = "e2_version yazım 0"
            return empty
        return PatternHit(
            ok=True,
            writes_ok=len(paths),
            paths=paths,
            detail=f"pattern e2_version writes={len(paths)}",
            pattern_id="e2_version",
            source="pattern:e2_version",
        )
    except Exception as exc:
        empty.detail = str(exc)[:200]
        return empty


# --- pattern: health_fields -------------------------------------------------------


def _match_health_fields(goal: str) -> bool:
    try:
        from ilim_assistant.motorlar.programlama_faz85 import _goal_wants_health_extra_fields

        return bool(_goal_wants_health_extra_fields(goal or ""))
    except Exception:
        return False


def _apply_health_fields(
    workspace_root: str | Path | None, scope_rel: str, goal: str
) -> PatternHit:
    empty = PatternHit(pattern_id="health_fields", source="pattern:health_fields")
    try:
        from ilim_assistant.motorlar.programlama_faz103_e2 import (
            try_supervised_health_fields_boot,
        )

        boot = try_supervised_health_fields_boot(workspace_root, scope_rel, goal)
        if boot.get("writes_ok"):
            return PatternHit(
                ok=True,
                writes_ok=int(boot.get("writes_ok") or 0),
                paths=list(boot.get("paths") or []),
                detail=str(boot.get("detail") or "health_fields"),
                pattern_id="health_fields",
                source="pattern:health_fields",
            )
        empty.detail = str(boot.get("detail") or "health_fields yok")
        return empty
    except Exception as exc:
        empty.detail = str(exc)[:200]
        return empty


# --- pattern: import_fix --------------------------------------------------------


def _match_import_fix(goal: str) -> bool:
    return bool(_IMPORT_GOAL_RE.search(goal or ""))


def _apply_import_fix(
    workspace_root: str | Path | None, scope_rel: str, goal: str
) -> PatternHit:
    """app/service.py içinde greet kullanımı var, import yok → ekle."""
    empty = PatternHit(pattern_id="import_fix", source="pattern:import_fix")
    root = _repo(workspace_root)
    if root is None:
        empty.detail = "repo yok"
        return empty
    service = _scope_dir(root, scope_rel) / "app" / "service.py"
    if not service.is_file():
        empty.detail = "service.py yok"
        return empty
    text = service.read_text(encoding="utf-8", errors="replace")
    if "greet(" not in text and "greet (" not in text:
        empty.detail = "greet kullanımı yok"
        return empty
    if re.search(r"from\s+app\.util\s+import\s+.*\bgreet\b", text):
        empty.detail = "import zaten var"
        return empty
    # Eksik import: satır ekle (util VERSION import'undan sonra veya dosya başına)
    insert = "from app.util import greet\n"
    if "from app.util import" in text:
        # VERSION-only import → greet ekle
        new_text, n = re.subn(
            r"(from\s+app\.util\s+import\s+)([^\n]+)",
            lambda m: m.group(0)
            if "greet" in m.group(2)
            else f"{m.group(1)}{m.group(2).rstrip()}, greet"
            if m.group(2).strip()
            else f"{m.group(1)}greet",
            text,
            count=1,
        )
        if n == 0 or new_text == text:
            # ayrı satır
            new_text = re.sub(
                r"(from\s+app\.util\s+import\s+[^\n]+\n)",
                r"\1" + insert,
                text,
                count=1,
            )
    else:
        # Dosyanın ilk import bloğundan sonra
        m = re.search(r"(^(?:from |import ).+\n)+", text, re.M)
        if m:
            new_text = text[: m.end()] + insert + text[m.end() :]
        else:
            new_text = insert + text
    if new_text == text:
        empty.detail = "import yaması uygulanamadı"
        return empty
    try:
        from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

        rel = f"{scope_rel}/app/service.py".replace("\\", "/")
        w = ProgramlamaAraclari(workspace_root).write(rel, new_text)
        if not w.ok:
            empty.detail = f"yazım reddi: {w.detail}"
            return empty
        return PatternHit(
            ok=True,
            writes_ok=1,
            paths=[rel],
            detail="pattern import_fix: greet import",
            pattern_id="import_fix",
            source="pattern:import_fix",
        )
    except Exception as exc:
        empty.detail = str(exc)[:200]
        return empty


# --- pattern: dict_field ----------------------------------------------------------


def _extract_dict_field(goal: str) -> str | None:
    m = _DICT_FIELD_RE.search(goal or "")
    if m:
        name = m.group(1).lower()
        if name in {"status", "ok", "version"}:
            # health_fields / version pattern'lerine bırak
            return None
        return name
    # «uptime ekle» kısa kalıp
    m2 = re.search(
        r"\b(uptime|ready|env|build|revision|region)\b.*\b(ekle|yaz|koy)\b",
        goal or "",
        re.I,
    )
    if m2:
        return m2.group(1).lower()
    m3 = re.search(
        r"\b(ekle|yaz|koy)\b.*\b(uptime|ready|env|build|revision|region)\b",
        goal or "",
        re.I,
    )
    if m3:
        return m3.group(2).lower()
    return None


def _match_dict_field(goal: str) -> bool:
    return _extract_dict_field(goal) is not None


def _apply_dict_field(
    workspace_root: str | Path | None, scope_rel: str, goal: str
) -> PatternHit:
    """health_payload (veya benzer) return dict'ine alan ekle."""
    empty = PatternHit(pattern_id="dict_field", source="pattern:dict_field")
    field_name = _extract_dict_field(goal)
    if not field_name:
        empty.detail = "alan adı yok"
        return empty
    root = _repo(workspace_root)
    if root is None:
        empty.detail = "repo yok"
        return empty
    service = _scope_dir(root, scope_rel) / "app" / "service.py"
    if not service.is_file():
        empty.detail = "service.py yok"
        return empty
    text = service.read_text(encoding="utf-8", errors="replace")
    if re.search(rf"""['"]{re.escape(field_name)}['"]\s*:""", text):
        empty.detail = f"{field_name} zaten var"
        return empty
    # return { ... } içine ekle — son } öncesi
    m = re.search(
        r"(def\s+health_payload\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:\s*\n"
        r"(?:[ \t]+.+\n)*?[ \t]+return\s*\{)([^}]*)(\})",
        text,
    )
    if not m:
        empty.detail = "health_payload return bulunamadı"
        return empty
    body = m.group(2).rstrip()
    sep = "" if body.endswith(",") or not body.strip() else ","
    # string değer varsayılan
    addition = f'{sep}\n        "{field_name}": "1"'
    if body.strip():
        new_body = body + addition + "\n    "
    else:
        new_body = f'\n        "{field_name}": "1"\n    '
    new_text = text[: m.start(2)] + new_body + text[m.end(2) :]
    try:
        from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

        rel = f"{scope_rel}/app/service.py".replace("\\", "/")
        w = ProgramlamaAraclari(workspace_root).write(rel, new_text)
        if not w.ok:
            empty.detail = f"yazım reddi: {w.detail}"
            return empty
        return PatternHit(
            ok=True,
            writes_ok=1,
            paths=[rel],
            detail=f"pattern dict_field: {field_name}",
            pattern_id="dict_field",
            source="pattern:dict_field",
        )
    except Exception as exc:
        empty.detail = str(exc)[:200]
        return empty


# --- pattern: ping_route ----------------------------------------------------------


def _match_ping_route(goal: str) -> bool:
    return bool(_PING_ROUTE_RE.search(goal or ""))


def _apply_ping_route(
    workspace_root: str | Path | None, scope_rel: str, goal: str
) -> PatternHit:
    """main.py'ye /ping endpoint ekle (yoksa)."""
    empty = PatternHit(pattern_id="ping_route", source="pattern:ping_route")
    root = _repo(workspace_root)
    if root is None:
        empty.detail = "repo yok"
        return empty
    main = _scope_dir(root, scope_rel) / "app" / "main.py"
    if not main.is_file():
        empty.detail = "main.py yok"
        return empty
    text = main.read_text(encoding="utf-8", errors="replace")
    if re.search(r"""@app\.(get|post)\(\s*['"]/ping['"]""", text):
        empty.detail = "/ping zaten var"
        return empty
    block = (
        "\n\n@app.get(\"/ping\")\n"
        "def ping() -> dict[str, str]:\n"
        "    return {\"ok\": \"true\", \"ping\": \"pong\"}\n"
    )
    new_text = text.rstrip() + block
    try:
        from ilim_assistant.motorlar.programlama_motoru import ProgramlamaAraclari

        rel = f"{scope_rel}/app/main.py".replace("\\", "/")
        w = ProgramlamaAraclari(workspace_root).write(rel, new_text)
        if not w.ok:
            empty.detail = f"yazım reddi: {w.detail}"
            return empty
        return PatternHit(
            ok=True,
            writes_ok=1,
            paths=[rel],
            detail="pattern ping_route: /ping",
            pattern_id="ping_route",
            source="pattern:ping_route",
        )
    except Exception as exc:
        empty.detail = str(exc)[:200]
        return empty


# --- registry ---------------------------------------------------------------------

PatternFn = Callable[[str | Path | None, str, str], PatternHit]
MatchFn = Callable[[str], bool]

PATTERNS: list[tuple[str, MatchFn, PatternFn]] = [
    ("e2_version", _match_e2_version, _apply_e2_version),
    ("health_fields", _match_health_fields, _apply_health_fields),
    ("import_fix", _match_import_fix, _apply_import_fix),
    ("dict_field", _match_dict_field, _apply_dict_field),
    ("ping_route", _match_ping_route, _apply_ping_route),
]


def list_pattern_ids() -> list[str]:
    return [p[0] for p in PATTERNS]


def try_supervised_pattern_library(
    workspace_root: str | Path | None,
    scope_rel: str,
    goal: str = "",
    *,
    pattern_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Niyet eşleşen ilk başarılı pattern'i uygula.
    Dönüş: try_e2_supervised_write_boot ile aynı şekil.
    """
    empty: dict[str, Any] = {
        "ok": False,
        "writes_ok": 0,
        "paths": [],
        "detail": "pattern aday yok",
        "source": "supervised_pattern",
        "pattern_id": "",
        "version": P1_PATTERNS_VERSION,
    }
    if not patterns_enabled():
        empty["detail"] = "supervised boot kapalı"
        return empty
    allow = set(pattern_ids) if pattern_ids else None
    tried: list[str] = []
    for pid, match, apply in PATTERNS:
        if allow is not None and pid not in allow:
            continue
        if not match(goal or ""):
            continue
        tried.append(pid)
        hit = apply(workspace_root, scope_rel, goal or "")
        if hit.writes_ok:
            return hit.as_boot_dict()
        empty["detail"] = hit.detail or f"{pid} yazamadı"
    if tried:
        empty["detail"] = f"denenen={','.join(tried)} · " + str(empty.get("detail") or "")
    return empty


def pattern_nudge_hints(scope_rel: str, goal: str) -> str:
    """Tur mesajına eklenecek kısa şablon ipuçları (yeni pattern'ler)."""
    chunks: list[str] = []
    if _match_import_fix(goal):
        chunks.append(
            f"\n[P1 import_fix] `{scope_rel}/app/service.py` içine "
            "`from app.util import greet` ekle (veya mevcut util import'una greet).\n"
        )
    field = _extract_dict_field(goal)
    if field:
        chunks.append(
            f"\n[P1 dict_field] `{scope_rel}/app/service.py` health_payload "
            f'return dict\'ine `"{field}": "1"` ekle.\n'
        )
    if _match_ping_route(goal):
        chunks.append(
            f"\n[P1 ping_route] `{scope_rel}/app/main.py` içine "
            '@app.get("/ping") → {"ok":"true","ping":"pong"} ekle.\n'
        )
    return "".join(chunks)
