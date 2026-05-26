# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 53: Sembol indeks lite (LLM) + Atölye çok dosya patch önizleme varsayılan.

- Faz 22 indeksini görev bağlamına otomatik özetler
- Faz 45 editör v2 + çok dosya sekmeleri Atölye'de varsayılan
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

FAZ53_VERSION = "programlama-faz53-v1-2026-05-26"

_PRIORITY_KINDS = ("class", "def", "async def", "function", "const")
_ENTRY_HINTS = frozenset(
    {
        "main",
        "app",
        "health",
        "api",
        "service",
        "router",
        "index",
        "server",
        "test",
    }
)


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ53", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def faz53_enabled() -> bool:
    return _enabled()


def symbol_lite_enabled() -> bool:
    return _enabled() and os.environ.get("RUZGAR_FAZ53_SYMBOL_LITE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def atolye_editor_v2_enabled() -> bool:
    """Atölye'de renkli diff + birleşik patch UX varsayılan."""
    if not _enabled():
        return False
    if os.environ.get("RUZGAR_FAZ53_ATOLYE_V2", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return False
    return True


def multi_file_preview_default() -> bool:
    return atolye_editor_v2_enabled()


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _tokens(message: str) -> list[str]:
    low = _ascii_fold(message)
    return [t for t in re.split(r"[^\w]+", low) if len(t) >= 2]


def ensure_scope_symbol_index(
    workspace_root: str | Path | None,
    scope_rel: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    if not symbol_lite_enabled():
        return {"ok": False, "skipped": True}
    try:
        from ilim_assistant.motorlar.programlama_faz22 import build_symbol_index

        return build_symbol_index(workspace_root, scope_rel, force=force)
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120]}


def _load_scope_entries(
    workspace_root: str | Path | None,
    scope_rel: str,
) -> dict[str, list[dict[str, Any]]]:
    try:
        from ilim_assistant.motorlar.programlama_faz22 import _index_path, _load_store

        idx_path = _index_path(workspace_root)
        if idx_path is None or not idx_path.is_file():
            return {}
        store = _load_store(idx_path)
        scopes = store.get("scopes") if isinstance(store.get("scopes"), dict) else {}
        scope_data = scopes.get(scope_rel.strip().replace("\\", "/").lstrip("/"))
        if not isinstance(scope_data, dict):
            return {}
        entries = scope_data.get("entries")
        return entries if isinstance(entries, dict) else {}
    except Exception:
        return {}


def _score_symbol(sym: dict[str, Any], tokens: list[str]) -> float:
    name = _ascii_fold(str(sym.get("name") or ""))
    rel = _ascii_fold(str(sym.get("rel") or ""))
    kind = str(sym.get("kind") or "")
    score = 0.0
    for t in tokens:
        if t in name:
            score += 4.0
        if t in rel:
            score += 1.5
    for h in _ENTRY_HINTS:
        if h in rel:
            score += 1.0
    if kind in ("class", "def", "async def"):
        score += 2.0
    if name in ("health", "main", "app", "create_app"):
        score += 2.5
    return score


def collect_symbol_lite_rows(
    workspace_root: str | Path | None,
    scope_rel: str,
    message: str,
    *,
    max_rows: int = 28,
) -> list[dict[str, Any]]:
    entries = _load_scope_entries(workspace_root, scope_rel)
    if not entries:
        return []
    tokens = _tokens(message)
    rows: list[tuple[float, dict[str, Any]]] = []
    seen: set[str] = set()

    for _key, defs in entries.items():
        if not isinstance(defs, list):
            continue
        for sym in defs:
            if not isinstance(sym, dict):
                continue
            name = str(sym.get("name") or "").strip()
            rel = str(sym.get("rel") or "").strip()
            if not name or not rel:
                continue
            uid = f"{rel}:{name}:{sym.get('line')}"
            if uid in seen:
                continue
            seen.add(uid)
            sc = _score_symbol(sym, tokens)
            if tokens and sc <= 0:
                continue
            if not tokens:
                sc = _score_symbol(sym, list(_ENTRY_HINTS))
            rows.append((sc, sym))

    if not rows and entries:
        for _key, defs in list(entries.items())[:40]:
            for sym in defs[:2] if isinstance(defs, list) else []:
                if isinstance(sym, dict):
                    rows.append((_score_symbol(sym, []), sym))

    rows.sort(key=lambda x: (-x[0], str(x[1].get("rel")), int(x[1].get("line") or 0)))
    return [sym for _, sym in rows[:max_rows]]


def format_symbol_lite_block(
    scope_rel: str,
    rows: list[dict[str, Any]],
    *,
    index_meta: dict[str, Any] | None = None,
) -> str:
    if not rows:
        return ""
    lines = [f"[SEMBOL İNDEKSİ — Faz 53 lite — `{scope_rel}`]"]
    meta = index_meta or {}
    if meta.get("file_count"):
        lines.append(
            f"Dosya: {meta.get('file_count')} · kayıt: {meta.get('symbol_count', len(rows))}"
        )
    for sym in rows:
        name = sym.get("name") or "?"
        kind = sym.get("kind") or "sym"
        rel = sym.get("rel") or "?"
        line = int(sym.get("line") or 0)
        loc = f"`{rel}`:{line}" if line else f"`{rel}`"
        lines.append(f"· **{name}** ({kind}) @ {loc}")
    lines.append(f"({FAZ53_VERSION})")
    return "\n".join(lines)


def build_symbol_lite_block(
    workspace_root: str | Path | None,
    scope_rel: str,
    message: str = "",
    *,
    max_rows: int = 28,
) -> str:
    """LLM bağlamı — otomatik indeks + özet sembol listesi."""
    if not symbol_lite_enabled():
        return ""
    scope = (scope_rel or "").strip().replace("\\", "/").lstrip("/")
    if not scope:
        return ""
    meta = ensure_scope_symbol_index(workspace_root, scope)
    rows = collect_symbol_lite_rows(
        workspace_root, scope, message, max_rows=max_rows
    )
    if not rows and meta.get("ok"):
        rows = collect_symbol_lite_rows(workspace_root, scope, "main health app", max_rows=12)
    return format_symbol_lite_block(scope, rows, index_meta=meta)


def augment_agent_context_parts(
    parts: list[str],
    workspace_root: str | Path | None,
    *,
    scope_rel: str | None = None,
    message: str = "",
) -> list[str]:
    """faz21 bağlam parçalarına sembol lite ekle."""
    if not symbol_lite_enabled() or not scope_rel:
        return parts
    block = build_symbol_lite_block(workspace_root, scope_rel, message)
    if block:
        parts.append(block[:6000])
    return parts


def patch_api_enrichments() -> dict[str, Any]:
    """Atölye patch API bayrakları."""
    if not _enabled():
        return {}
    return {
        "editor_v2_default": atolye_editor_v2_enabled(),
        "multi_file_preview_default": multi_file_preview_default(),
        "faz53_version": FAZ53_VERSION,
    }


def resolve_editor_v2_for_api(workspace_root: Any = None) -> bool:
    """inline-diff / pending için v2 kullan."""
    if atolye_editor_v2_enabled():
        return True
    try:
        from ilim_assistant.motorlar.programlama_faz45 import editor_v2_enabled

        return editor_v2_enabled()
    except Exception:
        return False


def faz53_directive() -> str:
    return (
        "[BAĞLAM + ATÖLYE — Faz 53]\n"
        "Görevde sembol indeks özeti otomatik; Atölye çok dosya patch sekmesi + renkli diff varsayılan.\n"
        "Kapat: RUZGAR_FAZ53=0\n"
    )
