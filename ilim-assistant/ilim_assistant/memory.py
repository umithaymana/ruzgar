"""Sohbetten onaylı notları bilgi tabanına yazma (otomatik 'bilinç' yok — sen kaydedersin)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from ilim_assistant.rag_store import _KNOWLEDGE_ROOT, build_index


def _slug(text: str, max_len: int = 60) -> str:
    t = re.sub(r"[^\w\s\-]", "", text, flags=re.UNICODE)
    t = re.sub(r"[\s\-]+", "-", t).strip("-").lower()
    return (t[:max_len] or "not")[:max_len]


def save_exchange(
    user_message: str,
    assistant_message: str,
    title_hint: str | None = None,
    rebuild_index: bool = True,
) -> tuple[Path, str]:
    """
    knowledge/learned/ altına Markdown yazar; istenirse RAG indeksini yeniler.
    """
    learned = Path(_KNOWLEDGE_ROOT) / "learned"
    learned.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    slug = _slug(title_hint or user_message[:120])
    path = learned / f"{ts}_{slug}.md"

    body = f"""# Öğrenilen not (sohbetten)

**Tarih (UTC):** {ts}

## Soru / istek

{user_message.strip()}

## Asistan özeti / cevap

{assistant_message.strip()}
"""
    path.write_text(body, encoding="utf-8")

    msg = f"Kaydedildi: {path}"
    if rebuild_index:
        info = build_index(force=False, incremental=True)
        msg += f" | İndeks: {info.get('status')} ({info.get('chunks', '?')} parça)"
    return path, msg
