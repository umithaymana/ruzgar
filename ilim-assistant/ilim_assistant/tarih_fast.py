# Created by Ümit & Gökçenur
"""Tarih soruları — hafif RAG + Ollama (Gemini/prefetch atlanır, 120 sn zaman aşımı önlenir)."""

from __future__ import annotations

import os
import time
from typing import Iterator

from ilim_assistant.chat_core import _tarih_intent, prior_messages_for_turn
from ilim_assistant.persona import ASSISTANT_NAME, OWNER_ADDRESS
from ilim_assistant.rag_store import search_tarih_hafiza


def tarih_fast_enabled() -> bool:
    return os.environ.get("RUZGAR_TARIH_FAST", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _llm_body_usable(text: str) -> bool:
    t = (text or "").strip()
    if len(t) < 36:
        return False
    low = t.lower()
    if "kota" in low and ("gemini" in low or "google" in low or "aşıldı" in low or "asildi" in low):
        return False
    if "quota" in low or "rate limit" in low:
        return False
    return True


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

    search_q = msg
    low = msg.casefold()
    if "fatih" in low or "fethett" in low or "istanbul" in low and "feth" in low:
        search_q = f"{msg} fatih sultan mehmet istanbul fethi 1453 konstantinopolis"
    hits = search_tarih_hafiza(search_q, top_k=top_k, scan_cap=scan)
    good = [h for h in hits if float(h[2]) >= score_min]
    if not good and hits and float(hits[0][2]) >= 0.12:
        good = [hits[0]]

    if good:
        ctx = _format_hits(good)
    else:
        ctx = (
            "(Yerel Tarih Hafızasında bu soruya yakın pasaj bulunamadı. "
            "Genel tarih bilginle yanıt ver; emin olmadığın tarih/uydurma detay yazma.)"
        )
    system = (
        f"Sen {ASSISTANT_NAME} asistanısın; {OWNER_ADDRESS} ile konuşuyorsun.\n"
        "\n[TALİMAT — TARİH HAFIZASI HIZLI YOL]\n"
        "Aşağıdaki BAĞLAM parçaları yerel Tarih Hafızasından (TARIH_VE_KULTUR). "
        "Önce bunları kullan; yetersizse genel bilginle tamamla ama uydurma tarih verme. "
        "Ümit abi ile doğal, akıcı Türkçe konuş; paragrafları kopyalama, 2–8 cümlede "
        "kendi cümlelerinle özetle ve bağla. Kaynak uydurma.\n"
    )
    user = f"BAĞLAM (Tarih Hafızası):\n{ctx}\n\n---\n\nSORU: {msg}"
    prior = prior_messages_for_turn(history, mode_norm)

    try:
        from ilim_assistant.llm_ollama import chat_completion_stream, ollama_reachable
    except Exception:
        return None

    try:
        ollama_cap = max(8.0, float(os.environ.get("RUZGAR_TARIH_OLLAMA_MAX_SEC", "18")))
    except ValueError:
        ollama_cap = 18.0
    try:
        gemini_cap = max(8.0, float(os.environ.get("RUZGAR_TARIH_GEMINI_MAX_SEC", "28")))
    except ValueError:
        gemini_cap = 28.0

    def _rag_pasaj_yanit() -> Iterator[str]:
        if not good:
            return
        yield (
            "Ümit abi, şu an model yanıt üretemedi; yerel Tarih Hafızasından özet:\n\n"
        )
        for text, src, score in good[:3]:
            snippet = (text or "").strip().replace("\n\n", "\n")[:560]
            yield f"• ({src}, uyum {score:.2f})\n{snippet}\n\n"

    def _gemini_stream() -> Iterator[str]:
        if os.environ.get("RUZGAR_TARIH_GEMINI_FALLBACK", "1").strip().lower() in (
            "0",
            "false",
            "no",
        ):
            return
        try:
            from ilim_assistant.config import apply_global_api_key_to_runtime, gemini_ready
            from ilim_assistant.gemini_quota_guard import gemini_cooldown_active
            from ilim_assistant.llm_gemini import chat_completion_stream_gemini

            apply_global_api_key_to_runtime()
            if gemini_cooldown_active() or not gemini_ready():
                return
            old_g = os.environ.get("RUZGAR_GEMINI_READ_TIMEOUT_SEC")
            os.environ["RUZGAR_GEMINI_READ_TIMEOUT_SEC"] = str(int(gemini_cap))
            try:
                deadline = time.monotonic() + gemini_cap
                for piece in chat_completion_stream_gemini(
                    system,
                    user,
                    prior_messages=prior[-4:] if prior else None,
                    max_output_tokens=480,
                    temperature=0.35,
                ):
                    if time.monotonic() > deadline:
                        return
                    if piece:
                        yield piece
            finally:
                if old_g is None:
                    os.environ.pop("RUZGAR_GEMINI_READ_TIMEOUT_SEC", None)
                else:
                    os.environ["RUZGAR_GEMINI_READ_TIMEOUT_SEC"] = old_g
        except Exception:
            return

    def _ollama_stream() -> Iterator[str]:
        if os.environ.get("RUZGAR_TARIH_TRY_OLLAMA", "1").strip().lower() in (
            "0",
            "false",
            "no",
        ):
            return
        if not ollama_reachable():
            return
        old_read_to = os.environ.get("RUZGAR_OLLAMA_READ_TIMEOUT_SEC")
        os.environ["RUZGAR_OLLAMA_READ_TIMEOUT_SEC"] = str(int(ollama_cap) + 5)
        try:
            try:
                max_tok = max(
                    120,
                    min(int(os.environ.get("RUZGAR_TARIH_FAST_MAX_TOKENS", "420")), 700),
                )
            except ValueError:
                max_tok = 420
            deadline = time.monotonic() + ollama_cap
            for piece in chat_completion_stream(
                system,
                user,
                prior_messages=prior[-4:] if prior else None,
                max_tokens=max_tok,
            ):
                if time.monotonic() > deadline:
                    return
                if piece:
                    yield piece
        except Exception:
            return
        finally:
            if old_read_to is None:
                os.environ.pop("RUZGAR_OLLAMA_READ_TIMEOUT_SEC", None)
            else:
                os.environ["RUZGAR_OLLAMA_READ_TIMEOUT_SEC"] = old_read_to

    def _gen() -> Iterator[str]:
        body = ""
        gemini_first = os.environ.get("RUZGAR_TARIH_GEMINI_FIRST", "1").strip().lower() not in (
            "0",
            "false",
            "no",
        )
        streams = (
            (_gemini_stream, _ollama_stream)
            if gemini_first
            else (_ollama_stream, _gemini_stream)
        )
        for stream_fn in streams:
            chunk = ""
            for piece in stream_fn():
                chunk += piece or ""
            if _llm_body_usable(chunk):
                body = chunk
                yield chunk
                return
        yield from _rag_pasaj_yanit()

    return _gen()
