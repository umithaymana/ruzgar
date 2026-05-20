# Created by Ümit & Gökçenur
"""Tarih soruları — hafif RAG + Ollama (Gemini/prefetch atlanır, 120 sn zaman aşımı önlenir)."""

from __future__ import annotations

import os
from typing import Iterator

from ilim_assistant.chat_core import _tarih_intent, pick_system, prior_messages_for_turn
from ilim_assistant.rag_store import search_tarih_hafiza


def tarih_fast_enabled() -> bool:
    return os.environ.get("RUZGAR_TARIH_FAST", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _format_hits(hits: list[tuple[str, str, float]], max_chars: int = 4500) -> str:
    parts: list[str] = []
    used = 0
    for text, src, score in hits:
        block = f"### Kaynak: {src} (uyum {score:.2f})\n{(text or '').strip()[:1400]}\n"
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n".join(parts).strip()


def iter_tarih_hafiza_reply(
    message: str,
    history: list,
    *,
    mode_norm: str = "genel",
) -> Iterator[str] | None:
    """
    Tarih niyeti + yerel pasaj varsa Ollama ile kısa yanıt üretir.
    None → tam boru hattına devam.
    """
    if not tarih_fast_enabled():
        return None
    msg = (message or "").strip()
    if not msg or not _tarih_intent(msg):
        return None

    try:
        top_k = max(2, min(int(os.environ.get("RUZGAR_TARIH_FAST_TOP_K", "4")), 6))
    except ValueError:
        top_k = 4
    try:
        scan = max(24, int(os.environ.get("RUZGAR_TARIH_FAST_SCAN", "48")))
    except ValueError:
        scan = 48
    try:
        score_min = float(os.environ.get("RUZGAR_TARIH_FAST_SCORE", "0.22"))
    except ValueError:
        score_min = 0.22

    hits = search_tarih_hafiza(msg, top_k=top_k, scan_cap=scan)
    good = [h for h in hits if float(h[2]) >= score_min]
    if not good and hits and float(hits[0][2]) >= 0.12:
        good = [hits[0]]
    if not good:
        return None

    ctx = _format_hits(good)
    system = (
        pick_system(False, mode_norm)
        + "\n\n[TALİMAT — TARİH HAFIZASI HIZLI YOL]\n"
        "Aşağıdaki BAĞLAM parçaları yerel Tarih Hafızasından (TARIH_VE_KULTUR). "
        "Önce bunları kullan; yetersizse genel bilginle tamamla ama uydurma tarih verme. "
        "2–6 cümle veya kısa maddeler; Türkçe; kaynak uydurma.\n"
    )
    user = f"BAĞLAM (Tarih Hafızası):\n{ctx}\n\n---\n\nSORU: {msg}"
    prior = prior_messages_for_turn(history, mode_norm)

    try:
        from ilim_assistant.llm_ollama import chat_completion_stream, ollama_reachable

        if not ollama_reachable():
            return None
    except Exception:
        return None

    def _gen() -> Iterator[str]:
        try:
            for piece in chat_completion_stream(
                system,
                user,
                prior_messages=prior[-4:] if prior else None,
            ):
                if piece:
                    yield piece
        except Exception:
            return

    return _gen()
