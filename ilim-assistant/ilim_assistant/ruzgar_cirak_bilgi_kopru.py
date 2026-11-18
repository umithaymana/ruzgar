# Created by Ümit & Gökçenur
"""Çırak 0A — görev-içi dar bilgi köprüsü.

Programlama turu genel RAG kapalı kalsın; çırak/atölye görevinde
yalnız bilgisayar eserleri sidecar'dan kısa snippet.
Yazım hâlâ projects/cirak-atolyesi (veya görev scope) — burada yalnız OKUMA bağlamı.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

VERSION = "cirak-bilgi-kopru-v1-2026-11-18"
MAX_SNIPPET_CHARS = 900
DEFAULT_TOP_K = 3


def enabled() -> bool:
    return os.environ.get("RUZGAR_CIRAK_BILGI_KOPRU", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def wants_bilgi_kopru(
    *,
    message: str = "",
    scope_rel: str = "",
    goal: str = "",
) -> bool:
    if not enabled():
        return False
    blob = f"{message} {scope_rel} {goal}".lower().replace("\\", "/")
    if "cirak-atolyesi" in blob or "çırak" in blob or "cirak" in blob:
        return True
    return False


def fetch_bilgisayar_snippets(
    query: str,
    *,
    top_k: int = DEFAULT_TOP_K,
) -> list[dict[str, Any]]:
    """Bilgisayar RAG'ten kısa hit listesi. İndeks yoksa kavram jsonl yedek."""
    q = (query or "").strip()
    if not q:
        return []
    rows: list[dict[str, Any]] = []
    try:
        from ilim_assistant.ruzgar_bilgisayar_rag import search_bilgisayar

        for text, source, score in search_bilgisayar(q, top_k=max(1, min(int(top_k), 5))):
            rows.append(
                {
                    "text": (text or "")[:MAX_SNIPPET_CHARS],
                    "source": source or "",
                    "score": float(score),
                    "via": "bilgisayar_rag",
                }
            )
    except Exception:
        rows = []
    if rows:
        return rows
    return _fallback_kavram_hits(q, top_k=top_k)


def _fallback_kavram_hits(query: str, *, top_k: int) -> list[dict[str, Any]]:
    """RAG hazır değilse knowledge/.../kavramlar_bilgisayar.jsonl tarama."""
    path = (
        Path(__file__).resolve().parents[1]
        / "knowledge"
        / "ortak_kaynak"
        / "alanlar"
        / "bilgisayar_muhendisligi"
        / "kavramlar_bilgisayar.jsonl"
    )
    if not path.is_file():
        return []
    low = query.lower()
    keys = [w for w in low.replace(",", " ").split() if len(w) > 3][:8]
    hits: list[dict[str, Any]] = []
    try:
        import json

        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            blob = json.dumps(row, ensure_ascii=False).lower()
            if keys and not any(k in blob for k in keys):
                continue
            text = str(row.get("ozet") or row.get("tanim") or row.get("text") or row)[:MAX_SNIPPET_CHARS]
            hits.append(
                {
                    "text": text,
                    "source": f"kavramlar_bilgisayar.jsonl::{row.get('id') or row.get('ad') or '?'}",
                    "score": 0.0,
                    "via": "kavram_fallback",
                }
            )
            if len(hits) >= top_k:
                break
    except OSError:
        return []
    return hits


def format_prompt_block(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return (
            "[ÇIRAK BİLGİ KÖPRÜSÜ — boş]\n"
            "Kaynak bulunamadı; bilmiyorsan uydurma, Mimar/ustaya sor.\n"
        )
    lines = [
        "[ÇIRAK BİLGİ KÖPRÜSÜ — yalnız oku; yazım yine görev scope]",
        "Aşağıdaki kaynak özetlerini kullan; cevapta kaynak yolunu an.",
        "",
    ]
    for i, r in enumerate(rows, 1):
        src = r.get("source") or "?"
        via = r.get("via") or ""
        lines.append(f"### Kaynak {i} (`{src}` · {via})")
        lines.append((r.get("text") or "").strip())
        lines.append("")
    lines.append(f"({VERSION})")
    return "\n".join(lines)


def build_cirak_bilgi_context(
    goal: str,
    *,
    message: str = "",
    scope_rel: str = "",
    top_k: int = DEFAULT_TOP_K,
) -> dict[str, Any]:
    if not wants_bilgi_kopru(message=message, scope_rel=scope_rel, goal=goal):
        return {"ok": False, "skipped": True, "rows": [], "block": "", "version": VERSION}
    q = (goal or message or "").strip()[:500]
    rows = fetch_bilgisayar_snippets(q, top_k=top_k)
    block = format_prompt_block(rows)
    return {
        "ok": bool(rows),
        "skipped": False,
        "rows": rows,
        "block": block,
        "sources": [str(r.get("source") or "") for r in rows],
        "version": VERSION,
    }
