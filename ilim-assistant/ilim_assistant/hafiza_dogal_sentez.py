# Created by Ümit & Gökçenur
"""Genel hafıza isabeti → doğal Türkçe sentez (ham JSON cevabı kullanıcıya dökülmez)."""

from __future__ import annotations

import os
import re
from typing import Any, Iterator, Optional

_INGEST_SKIP = re.compile(
    r"hat[ıi]rla|haf[ıi]zana\s+kaydet|dosyas[ıi]n[ıi]\s+oku|nebula\s+durum|"
    r"yanl[ıi]ş\s*cevap|yanlis\s*cevap|cevab[ıi]n\s+şu\s+olmalı|cevabin\s+su\s+olmalı|"
    r"doğru\s+cevap|dogru\s+cevap|"
    r"\.json\b|\.txt\b|\.md\b",
    re.I,
)


def dogal_konus_enabled() -> bool:
    return os.environ.get("RUZGAR_HAFIZA_DOGAL_KONUS", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _hint_min_score() -> float:
    raw = (os.environ.get("RUZGAR_HAFIZA_HINT_MIN") or "0.68").strip()
    try:
        return max(0.55, min(float(raw), 0.98))
    except ValueError:
        return 0.68


def _is_miss_answer(ans: str) -> bool:
    from ilim_assistant.hafiza_i_ruzgar import HafizaIRuzgar

    if not (ans or "").strip():
        return True
    if (ans or "").strip() == HafizaIRuzgar.BILINMEYEN_YANIT.strip():
        return True
    a = (ans or "").strip().lower()
    if "öğrenmedim" not in a and "ogrenmedim" not in a:
        return False
    return "mimar" in a or "öğretir" in a or "ogretir" in a


def should_skip_hafiza_dogal(message: str) -> bool:
    m = (message or "").strip()
    if not m or len(m) > 4000:
        return True
    if "=" in m:
        return True
    if bool(_INGEST_SKIP.search(m)):
        return True
    try:
        from ilim_assistant.ruzgar_egitim import lookup_egitim_reply

        if lookup_egitim_reply(m):
            return True
    except Exception:
        pass
    try:
        from ilim_assistant.ana_motor_plan import looks_like_casual_social_chat

        if looks_like_casual_social_chat(m):
            return True
    except Exception:
        pass
    return False


def lookup_genel_hafiza_hint(message: str) -> Optional[dict[str, Any]]:
    """Eşleşen hafıza satırı; yer tutucu ve düşük skor elenir."""
    if not dogal_konus_enabled() or should_skip_hafiza_dogal(message):
        return None
    try:
        from ilim_assistant.hafiza_i_ruzgar import genel_hafiza_lookup_detayli

        detay = genel_hafiza_lookup_detayli(message)
    except Exception:
        return None
    if not detay:
        return None
    cevap = str(detay.get("cevap") or "").strip()
    if _is_miss_answer(cevap):
        return None
    skor = float(detay.get("skor") or 0.0)
    if skor < _hint_min_score():
        return None
    return {
        "cevap": cevap,
        "soru": str(detay.get("soru") or "").strip(),
        "eslesme": str(detay.get("eslesme") or "fuzzy"),
        "skor": skor,
    }


def _dogal_system_tail(mode_norm: str) -> str:
    _ = mode_norm
    return (
        "\n\n[TALİMAT — DOĞAL KONUŞMA]\n"
        "Ümit abi ile akıcı, sıcak Türkçe konuş — bir sohbet arkadaşı gibi; ders kağıdı veya "
        "kelime listesi değil.\n"
        "- Önce kullanıcının **ne sorduğunu** anla; yanıt tamamen buna bağlı olsun.\n"
        "- HAFIZA BLOĞU dahili ipucudur; **aynı kelimeleri kopyalayıp yapıştırma**, madde madde "
        "dökme. Bilgiyi kendi cümlelerinle 2–8 cümlede anlat; gerekirse önceki turla bağ kur.\n"
        "- **Asla** «hafızamda», «kayıtlarımda», «buldum», «hafızaya baktım», «öğrettin» veya "
        "benzeri kaynak/hafıza ifadeleri kullanma — sanki kendin biliyormuşsun gibi konuş.\n"
        "- Emin olmadığın detayı uydurma; bilgi yetersizse kısa ve dürüstçe söyle (öğretme "
        "şablonu veya «hatırla:» komut önerme).\n"
        "- «Nasıl yardımcı olabilirim», sabit karşılama, sürüm etiketi veya konu dışı öneri yazma.\n"
    )


def _build_user_block(message: str, hint: dict[str, Any], extra_ctx: str = "") -> str:
    soru_k = (hint.get("soru") or "").strip()
    ham = (hint.get("cevap") or "").strip()[:2400]
    eslesme = hint.get("eslesme") or "?"
    skor = hint.get("skor") or 0.0
    parts = [
        "HAFIZA BLOĞU (dahili — kullanıcıya aynen okuma):",
        f"- Kayıtlı soru anahtarı: {soru_k or '(yok)'}",
        f"- Eşleşme: {eslesme} (güven {float(skor):.2f})",
        f"- Ham bilgi:\n{ham}",
    ]
    if extra_ctx.strip():
        parts.append(f"\nEK BAĞLAM (RAG):\n{extra_ctx.strip()}")
    parts.append(f"\n---\n\nKULLANICI MESAJI:\n{(message or '').strip()}")
    return "\n".join(parts)


def _optional_rag_context(message: str, mode_norm: str) -> str:
    try:
        from ilim_assistant.chat_core import _tarih_intent
        from ilim_assistant.rag_store import search_arsiv, search_tarih_hafiza

        if _tarih_intent(message):
            hits = search_tarih_hafiza(message, top_k=3, scan_cap=36)
        else:
            hits = search_arsiv(message, top_k=2)
        good = [h for h in (hits or []) if float(h[2]) >= 0.18]
        if not good:
            return ""
        lines = []
        for text, src, score in good[:3]:
            lines.append(
                f"### {src} ({score:.2f})\n{(text or '').strip()[:900]}"
            )
        return "\n\n".join(lines)
    except Exception:
        return ""


def append_hafiza_hint_directive(
    user_payload: str, hint: dict[str, Any], message: str
) -> str:
    """Tam boru hattında (RAG+web) hafıza ipucunu bağlama ekler."""
    block = _build_user_block(message, hint)
    tail = (
        "\n\n[TALİMAT — HAFIZA İPUCU]\n"
        "Üstteki HAFIZA BLOĞU yalnızca dahili ipucudur; cevabı doğal Türkçe cümlelerle sen kur. "
        "Ham metni kopyalama; kaynağı veya hafızayı kullanıcıya belli etme. "
        "BAĞLAM/RAG ile çelişirse önce güncel bağlamı kullan.\n"
    )
    return (user_payload or "").rstrip() + "\n\n" + block + tail


def iter_hafiza_dogal_reply(
    message: str,
    history: list,
    *,
    mode_norm: str = "genel",
    hint: dict[str, Any] | None = None,
) -> Iterator[str] | None:
    """
    Hafıza isabeti varsa Ollama/Groq/Gemini zinciri ile doğal yanıt üretir.
    None → tam boru hattına devam.
    """
    if not dogal_konus_enabled():
        return None
    msg = (message or "").strip()
    if should_skip_hafiza_dogal(msg):
        return None
    h = hint or lookup_genel_hafiza_hint(msg)
    if not h:
        return None

    from ilim_assistant.chat_core import pick_system, prior_messages_for_turn

    extra = ""
    if os.environ.get("RUZGAR_HAFIZA_DOGAL_RAG", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    ):
        extra = _optional_rag_context(msg, mode_norm)

    system = pick_system(False, mode_norm) + _dogal_system_tail(mode_norm)
    user = _build_user_block(msg, h, extra)
    prior = prior_messages_for_turn(history, mode_norm)

    try:
        from ilim_assistant.llm_brain import stream_chat_with_brain

        def _gen() -> Iterator[str]:
            try:
                for piece in stream_chat_with_brain(
                    system,
                    user,
                    model=None,
                    prior_messages=prior[-6:] if prior else None,
                    mode_norm=mode_norm,
                    coding_mode=False,
                ):
                    if piece:
                        yield piece
            except Exception:
                return

        return _gen()
    except Exception:
        return None
