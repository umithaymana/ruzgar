# Created by Ümit & Gökçenur
"""Tarih soruları — hafif RAG + Ollama (Gemini/prefetch atlanır, 120 sn zaman aşımı önlenir)."""

from __future__ import annotations

import os
import re
import time
import unicodedata
from typing import Any, Iterator

from ilim_assistant.tarih_intent import tarih_intent as _tarih_intent
from ilim_assistant.persona import ASSISTANT_NAME, OWNER_ADDRESS
from ilim_assistant.rag_store import search_tarih_hafiza

_TEACH_FALLBACK_MARKERS = (
    "öğretir misin",
    "ogretir misin",
    "net özet çıkaramadım",
    "net ozet cikaramadi",
    "net bir satır bulamadım",
)


def tarih_fast_enabled() -> bool:
    return os.environ.get("RUZGAR_TARIH_FAST", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _is_archive_metadata_text(text: str) -> bool:
    """Arşiv indeks satırı — kullanıcıya okunmaz (subject/location/source)."""
    t = (text or "").strip()
    if not t:
        return True
    low = t.casefold()
    if low.startswith(("subject:", "location:", "source:")):
        return True
    if sum(1 for k in ("subject:", "location:", "source:") if k in low) >= 2:
        return True
    if re.match(r"^subject:\s*.+;\s*location:\s*.+;\s*source:", low):
        return True
    return False


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


def is_tarih_fast_teach_fallback(text: str) -> bool:
    """tarih_fast başarısızlık metni — Ana Motor'a düşülmeli."""
    low = (text or "").strip().casefold()
    return any(m in low for m in _TEACH_FALLBACK_MARKERS)


def _norm_ascii_blob(msg: str) -> str:
    raw = (msg or "").strip()
    asc = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii").lower()
    return raw.lower() + " " + asc


def looks_like_list_bilgi_question(msg: str) -> bool:
    """Liste / çoklu isim isteği — kısa tarih_fast yetersiz."""
    blob = _norm_ascii_blob(msg)
    if len((msg or "").strip()) > 220:
        return False
    list_cues = (
        "kimlerdir",
        "kimler",
        "isimlerini",
        "ismlerini",
        "listele",
        "sırala",
        "sirala",
        "hepsini",
        "tamamını",
        "tamamini",
        "sayar mısın",
        "sayar misin",
        "kaç tane",
        "kac tane",
        "madde madde",
    )
    return any(c in blob for c in list_cues)


def skip_tarih_fast_for_bilgi_plan() -> bool:
    return os.environ.get("RUZGAR_TARIH_FAST_SKIP_BILGI", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _plan_primary(question_plan: Any | None) -> str:
    if question_plan is None:
        return ""
    if hasattr(question_plan, "primary"):
        return str(getattr(question_plan, "primary", "") or "").strip().lower()
    if isinstance(question_plan, dict):
        return str(question_plan.get("primary") or "").strip().lower()
    return ""


def should_defer_tarih_fast_to_ana_motor(
    message: str,
    *,
    question_plan: Any | None = None,
    mode_norm: str = "genel",
) -> bool:
    """
    Bilgi / liste soruları Ana Motor tam boru hattına (RAG + web + Faz B).
    """
    if mode_norm not in ("genel", "uretim", "gelisim"):
        return False
    if looks_like_list_bilgi_question(message):
        return True
    if not skip_tarih_fast_for_bilgi_plan():
        return False
    plan = question_plan
    if plan is None:
        try:
            from ilim_assistant.ana_motor_plan import plan_question
            from ilim_assistant.idrak_entegrasyon import motor_niyeti_heuristic

            plan = plan_question(message, mode_norm, motor_niyeti_heuristic(message))
        except Exception:
            plan = None
    if _plan_primary(plan) == "bilgi":
        return True
    try:
        from ilim_assistant.ruzgar_egitim import _is_bilgi_sorusu

        if _is_bilgi_sorusu(message):
            return True
    except Exception:
        pass
    return False


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


def _collect_tarih_hits(message: str) -> list[tuple[str, str, float]]:
    msg = (message or "").strip()
    if not msg:
        return []
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
    return good


def _pasaj_reply_from_hits(message: str, good: list[tuple[str, str, float]]) -> str:
    msg = (message or "").strip()
    q = msg.casefold()
    if not good:
        return (
            "Ümit abi, bu tarih sorusunda yerel kayıttan net bir satır bulamadım. "
            "Bana öğretir misin?"
        )
    for text, _src, _score in good[:3]:
        raw = (text or "").strip()
        if not raw:
            continue
        if "wikidata" in raw.casefold() and not re.search(r"\b(12\d{2}|13\d{2}|14\d{2})\b", raw):
            continue
        if ("kurul" in q or "ne zaman" in q or "kim kur" in q) and re.search(r"\b1299\b", raw):
            return (
                "Ümit abi, kayıtlara göre Osmanlı Devleti 1299 yılında, "
                "Osman Bey döneminde kurulmuş kabul edilir."
            )
        if re.search(r"osman\s*bey", q) and re.search(r"kurucu|kurdu|1299|beylik", raw, re.I):
            body = re.sub(r"\s+", " ", raw).strip()
            if len(body) > 280:
                m = re.search(r"^([^.!?…]+[.!?…])", body)
                body = m.group(1).strip() if m else body[:280].rsplit(" ", 1)[0] + "…"
            if body and not _is_archive_metadata_text(body):
                return f"Ümit abi, kısaca: {body}"
        lines: list[str] = []
        if _is_archive_metadata_text(raw):
            continue
        for ln in raw.splitlines():
            s = ln.strip().lstrip("#").strip()
            if not s or len(s) < 10:
                continue
            if s.casefold().startswith("http"):
                continue
            if s.startswith("Konu:") or s.startswith("Vikiveri:"):
                continue
            if _is_archive_metadata_text(s):
                continue
            if "description:" in s.casefold() and len(s) > 120:
                continue
            lines.append(s)
        body = " ".join(lines[:3])
        if _is_archive_metadata_text(body):
            continue
        body = re.sub(r"\s+", " ", body).strip()
        if len(body) > 280:
            m = re.search(r"^([^.!?…]+[.!?…])", body)
            body = m.group(1).strip() if m else body[:280].rsplit(" ", 1)[0] + "…"
        if body:
            return f"Ümit abi, kısaca: {body}"
    return (
        "Ümit abi, yerel tarih kaydı var ama net özet çıkaramadım. "
        "Doğru cevabı bana öğretir misin?"
    )


def try_tarih_instant_pasaj_reply(
    message: str,
    *,
    mode_norm: str = "genel",
    question_plan: Any | None = None,
) -> str | None:
    """Yerel tarih pasajından LLM beklemeden kısa yanıt — bilgi turu defer atlanır."""
    if not tarih_fast_enabled():
        return None
    msg = (message or "").strip()
    if not msg or looks_like_list_bilgi_question(msg):
        return None
    if mode_norm not in ("genel", "uretim", "gelisim"):
        return None
    try:
        from ilim_assistant.chat_core import _is_live_weather_query

        if _is_live_weather_query(msg):
            return None
    except Exception:
        pass
    if not _tarih_intent(msg):
        return None
    good = _collect_tarih_hits(msg)
    if not good:
        return None
    reply = _pasaj_reply_from_hits(msg, good)
    if is_tarih_fast_teach_fallback(reply):
        return None
    return reply


def iter_tarih_hafiza_reply(
    message: str,
    history: list,
    *,
    mode_norm: str = "genel",
    question_plan: Any | None = None,
) -> Iterator[str] | None:
    """
    Tarih niyeti + yerel pasaj varsa Ollama ile kısa yanıt üretir.
    None → tam boru hattına devam.
    """
    if not tarih_fast_enabled():
        return None
    msg = (message or "").strip()
    if not msg:
        return None
    if should_defer_tarih_fast_to_ana_motor(
        msg, question_plan=question_plan, mode_norm=mode_norm
    ):
        return None
    try:
        from ilim_assistant.chat_core import _is_live_weather_query

        if _is_live_weather_query(msg):
            return None
    except Exception:
        pass
    if not _tarih_intent(msg):
        return None

    good = _collect_tarih_hits(msg)

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
        "Ümit abi ile doğal, akıcı Türkçe konuş; paragrafları kopyalama. "
        "En fazla 3 kısa cümle; dosya yolu, wikidata linki veya madde listesi yazma. "
        "Sesli okunacağı için net ve kısa cevap ver. Kaynak uydurma.\n"
    )
    user = f"BAĞLAM (Tarih Hafızası):\n{ctx}\n\n---\n\nSORU: {msg}"
    prior = []
    try:
        from ilim_assistant.chat_core import prior_messages_for_turn

        prior = prior_messages_for_turn(history, mode_norm)
    except Exception:
        prior = []

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

    def _net_pasaj_metni() -> str:
        return _pasaj_reply_from_hits(msg, good)

    def _rag_pasaj_yanit() -> Iterator[str]:
        yield _net_pasaj_metni()

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
                    max_output_tokens=220,
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
        pasaj_first = os.environ.get("RUZGAR_TARIH_PASAJ_FIRST", "1").strip().lower() not in (
            "0",
            "false",
            "no",
        )
        if pasaj_first and good:
            fallback = _net_pasaj_metni()
            if not is_tarih_fast_teach_fallback(fallback):
                yield fallback
                return
        body = ""
        gemini_first = os.environ.get("RUZGAR_TARIH_GEMINI_FIRST", "0").strip().lower() not in (
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
        fallback = _net_pasaj_metni()
        if is_tarih_fast_teach_fallback(fallback):
            return
        yield fallback

    return _gen()
