# Created by Ümit & Gökçenur
"""Tercüme Faz 4 — arşiv index.jsonl bağlamı (okuma motoruna dokunmadan)."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

TERCUME_RAG_VERSION = "tercume-context-rag-v4-faz4-2026-05-31"

_INDEX_REL_PATHS = (
    "ilim-assistant/arsiv/Tasavvuf_Kulliyati/Mektubat_i_Rabbani/index.jsonl",
    "ilim-assistant/arsiv/mektubat/index.jsonl",
    "ilim-assistant/arsiv/Tasavvuf_Kulliyati/Kuran_i_Kerim/index.jsonl",
    "ilim-assistant/arsiv/kuran/index.jsonl",
)

_TERM_RE = re.compile(r"[\w\u0600-\u06FF]{4,}", re.UNICODE)


def tercume_rag_enabled() -> bool:
    return os.environ.get("RUZGAR_TERCUME_RAG", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _repo_root() -> Path:
    try:
        from ilim_assistant.motorlar.programlama_motoru import repo_root

        r = repo_root(None)
        if r:
            return Path(r)
    except Exception:
        pass
    return Path(__file__).resolve().parents[2]


def _query_terms(text: str, source_file: str = "") -> list[str]:
    blob = f"{text} {source_file}".lower()
    raw = _TERM_RE.findall(blob)
    seen: set[str] = set()
    out: list[str] = []
    for t in raw:
        k = t.lower()
        if k in seen or len(k) < 4:
            continue
        seen.add(k)
        out.append(k)
    return out[:24]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                hit = json.loads(line)
                if isinstance(hit, dict):
                    rows.append(hit)
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    return rows


def _row_text(row: dict[str, Any]) -> str:
    for key in ("text", "snippet", "content", "body", "ozet"):
        v = row.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    parts = [str(row.get(k) or "") for k in ("title", "mektup_no", "sure", "ayet")]
    return " ".join(p for p in parts if p).strip()


def _score_row(row: dict[str, Any], terms: list[str]) -> float:
    blob = _row_text(row).lower()
    if not blob:
        return 0.0
    score = 0.0
    for t in terms:
        if t in blob:
            score += 10.0
    if row.get("mektup_no") and any("mektubat" in x or "mektup" in x for x in terms):
        score += 3.0
    return score


def archive_context_snippets(
    text: str,
    *,
    source_file: str = "",
    max_snippets: int = 4,
    max_chars: int = 1400,
) -> tuple[str, list[dict[str, Any]]]:
    """index.jsonl satırlarından kısa bağlam (RAG-lite)."""
    if not tercume_rag_enabled():
        return "", []
    terms = _query_terms(text, source_file)
    if not terms:
        return "", []

    root = _repo_root()
    candidates: list[tuple[float, dict[str, Any], str]] = []
    for rel in _INDEX_REL_PATHS:
        path = (root / rel.replace("/", os.sep)).resolve()
        for row in _read_jsonl(path):
            sc = _score_row(row, terms)
            if sc < 8:
                continue
            candidates.append((sc, row, rel))

    candidates.sort(key=lambda x: -x[0])
    hits: list[dict[str, Any]] = []
    parts: list[str] = []
    used = 0
    for sc, row, rel in candidates[: max_snippets * 2]:
        snippet = _row_text(row)[:320]
        if not snippet:
            continue
        if any(h.get("snippet") == snippet for h in hits):
            continue
        hits.append(
            {
                "score": round(sc, 1),
                "source_index": rel,
                "snippet": snippet[:280],
                "meta": {k: row.get(k) for k in ("mektup_no", "sure", "ayet") if row.get(k)},
            }
        )
        label = rel.split("/")[-2] if "/" in rel else rel
        parts.append(f"- [{label}] {snippet[:260]}")
        used += len(parts[-1])
        if len(hits) >= max_snippets or used >= max_chars:
            break

    if not parts:
        return "", []
    block = "ARŞİV BAĞLAMI (tutarlılık için — uydurma ekleme):\n" + "\n".join(parts)
    block += f"\n({TERCUME_RAG_VERSION})\n"
    return block, hits
