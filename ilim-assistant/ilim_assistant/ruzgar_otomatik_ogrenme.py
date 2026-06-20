# Created by Ümit & Gökçenur
"""Otomatik bilgi öğrenme — web/bilgi yanıtlarını kalıcı kütüphaneye yazar."""

from __future__ import annotations

import os
import re
import threading
import unicodedata
from datetime import datetime, timezone
from typing import Any, Optional

OTOMATIK_OGRENME_VERSION = "otomatik-ogrenme-ac4-v1-2026-06-13"
MOTOR_TIPI_BILGI = "BilgiKutuphane"

_SKIP_USER = re.compile(
    r"(?:"
    r"günaydın|gunaydin|merhaba|selam|naber|hey|"
    r"saçmalama|sacmalama|webten\s+ara|"
    r"öğretmeyeceğim|ogretmeyecegim|"
    r"hatırla\s*[:\-]|hafızaya\s+al|"
    r"cevap\s+bu|doğru\s+cevap"
    r")",
    re.I,
)
_MISS_REPLY = re.compile(
    r"(?:bulamad[ıi]m|öğrenmedim|ogrenmedim|emin\s+değilim|"
    r"hangi\s+konuda\s+sohbet|netleştiremedim)",
    re.I,
)

_index_lock = threading.Lock()
_last_index_ts = 0.0


def otomatik_ogrenme_enabled() -> bool:
    if os.environ.get("RUZGAR_TEK_BEYIN", "1").strip().lower() in ("0", "false", "no"):
        return False
    return os.environ.get("RUZGAR_OTOMATIK_OGRENME", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def kutuphane_once_enabled() -> bool:
    return os.environ.get("RUZGAR_KUTUPHANE_ONCE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def nebula_bridge_enabled() -> bool:
    if not otomatik_ogrenme_enabled():
        return False
    return os.environ.get("RUZGAR_OGRENME_NEBULA_BRIDGE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _default_nebula_collection() -> str:
    return (
        os.environ.get("RUZGAR_OGRENME_NEBULA_COLLECTION", "").strip()
        or "tarih_kaynak"
    )


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKC", (text or "").strip().lower())
    return re.sub(r"\s+", " ", t)


def _min_answer_len() -> int:
    try:
        return max(30, int(os.environ.get("RUZGAR_OGRENME_MIN_CHARS", "48")))
    except ValueError:
        return 48


def _kutuphane_min_score() -> float:
    try:
        return max(0.62, min(float(os.environ.get("RUZGAR_KUTUPHANE_MIN_SCORE", "0.70")), 0.95))
    except ValueError:
        return 0.70


def should_check_bilgi_kutuphane_first(message: str) -> bool:
    """Öğrenilmiş genel kültür — web'den önce kütüphane."""
    if not otomatik_ogrenme_enabled() or not kutuphane_once_enabled():
        return False
    raw = (message or "").strip()
    if not raw or len(raw) > 500 or _SKIP_USER.search(_norm(raw)):
        return False
    if lookup_bilgi_kutuphane_hint(raw):
        return True
    try:
        from ilim_assistant.ruzgar_tek_beyin import looks_like_personal_memory_query

        if looks_like_personal_memory_query(raw):
            return False
    except Exception:
        pass
    try:
        from ilim_assistant.ruzgar_tek_beyin_analiz import classify_question_intent

        intent = classify_question_intent(raw)
        it = str(intent.get("intent") or "")
        if it in ("simple_fact", "meta_feedback", "web_cmd", "sohbet", "personal"):
            return False
        if it in ("bilgi", "temporal_now"):
            return True
    except Exception:
        pass
    blob = _norm(raw)
    return bool(
        re.search(r"\b(kimdir|kimdi|nedir|ne zaman|ka[cç]|nerede|nasıl|nasil)\b", blob)
    )


def lookup_bilgi_kutuphane_hint(message: str) -> Optional[dict[str, Any]]:
    """ruzgar_genel_hafiza.json — BilgiKutuphane + Egitim + tüm raflar."""
    if not otomatik_ogrenme_enabled():
        return None
    try:
        from ilim_assistant.ana_motor_plan import should_stay_on_ana_motor_bilgi

        if should_stay_on_ana_motor_bilgi(message):
            return None
    except Exception:
        pass
    try:
        from ilim_assistant.hafiza_dogal_sentez import _is_miss_answer
        from ilim_assistant.hafiza_i_ruzgar import genel_hafiza_lookup_detayli
        from ilim_assistant.ruzgar_tek_beyin import memory_lookup_variants
    except Exception:
        return None

    best: Optional[dict[str, Any]] = None
    min_sc = _kutuphane_min_score()
    for variant in memory_lookup_variants(message):
        try:
            detay = genel_hafiza_lookup_detayli(variant)
        except Exception:
            continue
        if not detay:
            continue
        cevap = str(detay.get("cevap") or "").strip()
        if _is_miss_answer(cevap) or _MISS_REPLY.search(cevap):
            continue
        try:
            from ilim_assistant.ruzgar_tek_beyin_hafiza_seed import sanitize_gokcenur_hafiza_cevap

            cevap = sanitize_gokcenur_hafiza_cevap(
                cevap, soru=str(detay.get("soru") or "")
            )
        except Exception:
            pass
        if len(cevap) < 20:
            continue
        skor = float(detay.get("skor") or 0.0)
        if skor < min_sc:
            continue
        row = {
            "cevap": cevap,
            "soru": str(detay.get("soru") or "").strip(),
            "eslesme": str(detay.get("eslesme") or "fuzzy"),
            "skor": skor,
        }
        if best is None or skor > float(best.get("skor") or 0.0):
            best = row
    return best


def synthesize_kutuphane_reply(message: str, hint: dict[str, Any]) -> str:
    """Kütüphane eşleşmesi — «kimdir» vb. sorularda doğrudan cevap metni."""
    del message  # soru metni yanıtta tekrarlanmaz; net cevap öncelikli
    ham = str(hint.get("cevap") or "").strip()
    return ham


def try_bilgi_kutuphane_instant_reply(message: str) -> Optional[str]:
    if not should_check_bilgi_kutuphane_first(message):
        return None
    hint = lookup_bilgi_kutuphane_hint(message)
    if not hint:
        return None
    body = synthesize_kutuphane_reply(message, hint)
    return body.strip() or None


def kutuphane_blocks_web_path(message: str) -> bool:
    if not should_check_bilgi_kutuphane_first(message):
        return False
    try:
        from ilim_assistant.ana_motor_plan import (
            looks_like_casual_social_chat,
            looks_like_ruzgar_relational_chat,
        )

        if looks_like_casual_social_chat(message) or looks_like_ruzgar_relational_chat(
            message
        ):
            return False
    except Exception:
        pass
    return lookup_bilgi_kutuphane_hint(message) is not None


def _should_auto_learn_turn(
    user_message: str,
    assistant_message: str,
    *,
    plan_primary: str = "",
    instant: bool = False,
    web_used: bool = False,
) -> bool:
    if not otomatik_ogrenme_enabled():
        return False
    u = (user_message or "").strip()
    a = (assistant_message or "").strip()
    if not u or not a or instant:
        return False
    if len(u) < 4 or len(u) > 600:
        return False
    if len(a) < _min_answer_len() or len(a) > 4500:
        return False
    if _SKIP_USER.search(_norm(u)):
        return False
    if _MISS_REPLY.search(a):
        return False
    try:
        from ilim_assistant.ruzgar_egitim import is_invalid_egitim_pair

        if is_invalid_egitim_pair(u, a):
            return False
    except Exception:
        pass
    prim = (plan_primary or "").strip().lower()
    if prim in ("gundelik", "hafiza", "islem", "dosya", "hava"):
        if not web_used:
            return False
    if prim in ("bilgi", "bilim", "dilbilgisi") or web_used:
        return True
    try:
        from ilim_assistant.ruzgar_tek_beyin_analiz import classify_question_intent

        it = str(classify_question_intent(u).get("intent") or "")
        return it in ("bilgi", "temporal_now")
    except Exception:
        return False


def _schedule_rag_index() -> None:
    """Ağır indeks güncellemesini arka planda — sohbeti bekletmez."""
    global _last_index_ts
    import time

    debounce = 45.0
    now = time.time()
    if now - _last_index_ts < debounce:
        return
    with _index_lock:
        if now - _last_index_ts < debounce:
            return
        _last_index_ts = now

    def _run() -> None:
        try:
            from ilim_assistant.rag_store import build_index

            build_index(force=False, incremental=True)
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()


def _save_to_learned_md(user_message: str, assistant_message: str) -> None:
    try:
        from ilim_assistant.memory import save_exchange

        save_exchange(
            user_message,
            assistant_message,
            title_hint=user_message[:100],
            rebuild_index=False,
        )
        _schedule_rag_index()
    except Exception:
        pass


def auto_learn_from_turn(
    user_message: str,
    assistant_message: str,
    *,
    plan_primary: str = "",
    instant: bool = False,
    web_used: bool = False,
    force_web: bool = False,
    hits: list | None = None,
) -> dict[str, Any]:
    """
    Bilgi turunu kalıcı kütüphaneye yazar:
    - ruzgar_genel_hafiza.json (BilgiKutuphane)
    - knowledge/learned/*.md (RAG)
    """
    meta: dict[str, Any] = {"saved": False, "version": OTOMATIK_OGRENME_VERSION}
    if not _should_auto_learn_turn(
        user_message,
        assistant_message,
        plan_primary=plan_primary,
        instant=instant,
        web_used=web_used or force_web,
    ):
        return meta

    u = (user_message or "").strip()
    a = (assistant_message or "").strip()
    # Kısa özet — hafızada tam metin yerine öz cevap
    cevap_kayit = a
    if len(a) > 1200:
        cevap_kayit = a[:1150].rsplit(" ", 1)[0].rstrip() + "…"

    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor
        from ilim_assistant.ruzgar_tek_beyin import memory_lookup_variants

        motor = get_hafiza_motor()
        keys: list[str] = []
        for variant in memory_lookup_variants(u):
            if variant and variant not in keys:
                keys.append(variant)
        if not keys:
            keys = [u]
        for key in keys[:4]:
            motor.ekle_bilgi(key, cevap_kayit, motor_tipi=MOTOR_TIPI_BILGI)
        meta["saved"] = True
        meta["keys"] = keys[:4]
        meta["motor"] = MOTOR_TIPI_BILGI
    except Exception as exc:
        meta["error"] = str(exc)
        return meta

    _save_to_learned_md(u, cevap_kayit)
    meta["learned_md"] = True
    meta["ts"] = datetime.now(timezone.utc).isoformat()

    nb = maybe_nebula_bridge_from_learn(
        u,
        cevap_kayit,
        plan_primary=plan_primary,
        web_used=web_used,
        force_web=force_web,
        hits=hits,
    )
    if nb.get("ok"):
        meta["nebula_bridge"] = nb
    elif nb.get("skipped"):
        meta["nebula_skipped"] = nb.get("reason")
    return meta


def should_nebula_bridge_for_learn(
    user_message: str,
    assistant_message: str,
    *,
    plan_primary: str = "",
    web_used: bool = False,
    force_web: bool = False,
) -> bool:
    if not nebula_bridge_enabled():
        return False
    prim = (plan_primary or "").strip().lower()
    if prim in ("gundelik", "hafiza", "islem", "dosya", "hava") and not (web_used or force_web):
        return False
    if web_used or force_web:
        return True
    if prim in ("bilgi", "bilim", "dilbilgisi"):
        return True
    if re.search(r"\*\*Güven:\s*(düşük|dusuk|orta)", assistant_message or "", re.I):
        return True
    return False


def resolve_nebula_collection(
    message: str,
    *,
    plan_primary: str = "",
    hits: list | None = None,
) -> str:
    msg = (message or "").strip()
    try:
        from ilim_assistant.ana_motor_nebula_oneri import suggest_nebula_collection

        sug = suggest_nebula_collection(
            msg,
            hits=hits,
            guven="orta",
            web_was_used=True,
        )
        if sug and sug.get("collection"):
            return str(sug["collection"])
    except Exception:
        pass
    low = _norm(msg)
    if prim := (plan_primary or "").strip().lower():
        if prim == "bilim" and "tarih" not in low:
            if any(x in low for x in ("osman", "islam", "medeniyet", "padişah", "padisah")):
                return "tarih_kaynak"
    if any(
        x in low
        for x in (
            "osman",
            "tarih",
            "padişah",
            "padisah",
            "medeniyet",
            "islam",
            "fatih",
            "kanuni",
        )
    ):
        return "tarih_kaynak"
    return _default_nebula_collection()


def maybe_nebula_bridge_from_learn(
    user_message: str,
    assistant_message: str,
    *,
    plan_primary: str = "",
    web_used: bool = False,
    force_web: bool = False,
    hits: list | None = None,
) -> dict[str, Any]:
    """Kalıcı öğrenme sonrası Nebula incremental paket + indeks."""
    meta: dict[str, Any] = {"ok": False, "version": OTOMATIK_OGRENME_VERSION}
    if not should_nebula_bridge_for_learn(
        user_message,
        assistant_message,
        plan_primary=plan_primary,
        web_used=web_used,
        force_web=force_web,
    ):
        return {**meta, "skipped": True, "reason": "bridge_kapali_veya_uygunsuz_tur"}
    collection = resolve_nebula_collection(
        user_message,
        plan_primary=plan_primary,
        hits=hits,
    )
    try:
        from ilim_assistant.ana_motor_nebula_apply import start_nebula_qa_apply_background

        out = start_nebula_qa_apply_background(
            collection,
            user_message,
            assistant_message,
            source="otomatik_ogrenme",
        )
        if out.get("ok"):
            meta.update(out)
            meta["ok"] = True
            meta["collection"] = collection
            return meta
        if out.get("error") == "Arka plan indeksleme sürüyor.":
            return {**meta, "skipped": True, "reason": "nebula_indeks_meşgul"}
        meta["error"] = out.get("error")
        return meta
    except Exception as exc:
        meta["error"] = str(exc)[:200]
        return meta


def otomatik_ogrenme_status() -> dict[str, Any]:
    job: dict[str, Any] = {}
    try:
        from ilim_assistant.ana_motor_nebula_apply import get_nebula_apply_job_status

        job = get_nebula_apply_job_status()
    except Exception:
        pass
    return {
        "enabled": otomatik_ogrenme_enabled(),
        "kutuphane_once": kutuphane_once_enabled(),
        "nebula_bridge": nebula_bridge_enabled(),
        "nebula_collection_default": _default_nebula_collection(),
        "version": OTOMATIK_OGRENME_VERSION,
        "motor_tipi": MOTOR_TIPI_BILGI,
        "nebula_job": job,
    }


def otomatik_ogrenme_panel_payload() -> dict[str, Any]:
    st = otomatik_ogrenme_status()
    st["ok"] = True
    st["hint"] = (
        "Bilgi/bilim yanıtları hafızaya yazılır; uygun turlarda Nebula incremental paket oluşturulur."
    )
    try:
        from ilim_assistant.ana_motor_faz_ae_pro_ogrenme import pro_ogrenme_status

        st["pro_ogrenme"] = pro_ogrenme_status()
    except Exception:
        pass
    return st
