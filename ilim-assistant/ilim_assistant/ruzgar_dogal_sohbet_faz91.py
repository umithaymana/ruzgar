# Created by Ümit & Gökçenur
"""
Rüzgar — Faz 91: Doğal sohbet (Cursor benzeri akış).

Amaç: Şablon «yüklenen» cevaplar yerine bağlamı anlayan, akıcı LLM yanıtı.
Kapat: RUZGAR_DOGAL_SOHBET=0
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

FAZ91_VERSION = "ruzgar-dogal-sohbet-faz91-v1-2026-06-06"


def dogal_sohbet_enabled() -> bool:
    return os.environ.get("RUZGAR_DOGAL_SOHBET", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _norm_ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()


def _explicit_research_intent(message: str) -> bool:
    try:
        from ilim_assistant.ana_motor_plan import _explicit_research_intent as _eri

        return bool(_eri(message))
    except Exception:
        raw = (message or "").strip()
        if not raw:
            return False
        blob = _norm_ascii(raw.lower()) + " " + raw.lower()
        cues = ("nedir", "kimdir", "ne zaman", "kaç", "kac", "hadis", "ayet", "tefsir")
        return any(c in blob for c in cues)


def _last_assistant_snippet(history: list | None, *, max_len: int = 120) -> str:
    if not history:
        return ""
    try:
        from ilim_assistant.chat_core import ensure_messages

        msgs = ensure_messages(history)
    except Exception:
        msgs = history or []
    for m in reversed(msgs):
        if isinstance(m, dict) and m.get("role") == "assistant":
            t = str(m.get("content") or "").strip()
            if t:
                return t[:max_len]
    return ""


def is_natural_conversation_turn(
    message: str,
    mode_norm: str,
    question_plan: Any | None = None,
    *,
    history: list | None = None,
) -> bool:
    """
    Sohbet / muhabbet / devam turu — şablon yerine LLM.
    Bilgi araştırması (nedir/kimdir…) hariç.
    """
    if not dogal_sohbet_enabled():
        try:
            from ilim_assistant.ana_motor_plan import is_casual_conversation_turn

            return is_casual_conversation_turn(message, mode_norm, question_plan)
        except Exception:
            return False
    if mode_norm not in ("genel", "uretim", "gelisim"):
        return False
    raw = (message or "").strip()
    if not raw:
        return False
    try:
        from ilim_assistant.ana_motor_plan import looks_like_instant_social_ack

        if looks_like_instant_social_ack(raw):
            return False
    except Exception:
        pass
    try:
        from ilim_assistant.ana_motor_bilgi_turu import should_route_bilgi_turu_pipeline

        if should_route_bilgi_turu_pipeline(raw, question_plan):
            return False
    except Exception:
        pass
    if _explicit_research_intent(raw):
        return False

    try:
        from ilim_assistant.ana_motor_plan import looks_like_casual_social_chat

        if looks_like_casual_social_chat(raw):
            return True
    except Exception:
        pass

    try:
        from ilim_assistant.ana_motor_plan import looks_like_ruzgar_relational_chat

        if looks_like_ruzgar_relational_chat(raw):
            return True
    except Exception:
        pass

    if question_plan is not None:
        primary = str(getattr(question_plan, "primary", "") or "")
        use_rag = bool(getattr(question_plan, "use_ilim_rag", True))
        if primary == "gundelik" and not use_rag and len(raw) < 500:
            return True

    blob = _norm_ascii(raw.lower()) + " " + raw.lower()
    conv_cues = (
        "sohbet",
        "konuş",
        "konus",
        "muhabbet",
        "anlat",
        "düşün",
        "dusun",
        "sence",
        "ne dersin",
        "yardım et",
        "yardim et",
        "senin gibi",
        "robot",
        "anlamalı",
        "anlamali",
        "anlıyor musun",
        "anliyor musun",
        "hadi ",
        "başlayalım",
        "baslayalim",
        "geliştir",
        "gelistir",
        "gelisim",
        "gelişim",
        "ogren",
        "öğren",
        "ogrendin",
        "öğrendin",
        "nasil gidiyor",
        "nasıl gidiyor",
        "yeni seyler",
        "yeni şeyler",
        "güçlendir",
        "guclendir",
        "ana motor",
        "fikrin",
        "öner",
        "oner",
        "devam edelim",
        "ne yapıyoruz",
        "ne yapiyoruz",
        "birlikte",
        "beraber",
        "nasıl hissed",
        "nasil hissed",
        "dinliyor musun",
        "burada mısın",
        "burada misin",
        "canım sıkıldı",
        "canim sikildi",
        "sıkıldım",
        "moralim bozuk",
        "keyfim yok",
        "dertleş",
        "dertles",
        "yalnızım",
        "yalnizim",
        "arkadaş gibi",
        "arkadas gibi",
        "dost gibi",
    )
    if any(c in blob for c in conv_cues) and len(raw) < 700:
        return True

    # Oturum devamı: kısa cevap / onay / yorum (önceki turda asistan konuşmuş)
    if history and len(raw) < 200 and len(raw.split()) >= 2:
        if not re.search(r"\b(?:nedir|kimdir|ne zaman|kaç|kac)\b", blob):
            if _last_assistant_snippet(history):
                return True

    # Uzun düşünce / plan paragrafı — bilgi sorusu işareti yoksa sohbet say
    if len(raw) >= 80 and "?" not in raw:
        if not re.search(
            r"\b(?:nedir|kimdir|kim kurdu|ne zaman|nerede|kaç|kac|açıkla|acikla)\b",
            blob,
        ):
            if any(
                x in blob
                for x in (
                    "istiyorum",
                    "yapalım",
                    "yapalim",
                    "olmalı",
                    "olmali",
                    "hedef",
                    "vizyon",
                    "eksik",
                    "geliştir",
                    "gelistir",
                )
            ):
                return True

    return False


def is_pure_short_greeting(message: str) -> bool:
    """Tek kelimelik selam — anında yanıt; uzun sohbet turu LLM'de kalsın."""
    raw = (message or "").strip()
    if not raw or len(raw) > 56:
        return False
    if len(raw.split()) > 5:
        return False
    low = raw.lower()
    if any(
        x in low
        for x in (
            "test",
            "pytest",
            "proje",
            "kod",
            "yaz",
            "düzelt",
            "duzelt",
            "fix",
            "dogrula",
            "doğrula",
        )
    ):
        return False
    try:
        from ilim_assistant.ana_motor_plan import looks_like_casual_social_chat

        return looks_like_casual_social_chat(raw)
    except Exception:
        return False


def should_skip_instant_shortcuts(
    message: str,
    mode_norm: str,
    *,
    history: list | None = None,
    question_plan: Any | None = None,
) -> bool:
    """Şablon selam/empati yanıtlarını atla — LLM üretsin."""
    if not dogal_sohbet_enabled():
        return False
    if mode_norm not in ("genel", "uretim", "gelisim"):
        return False
    if is_pure_short_greeting(message):
        return False
    return is_natural_conversation_turn(
        message, mode_norm, question_plan, history=history
    )


def natural_turn_budget_sec() -> float:
    try:
        return float(os.environ.get("RUZGAR_DOGAL_BUDGET_SEC", "32"))
    except ValueError:
        return 32.0


def turn_budget_for_message(message: str, mode_norm: str, question_plan: Any | None = None) -> float | None:
    """Doğal sohbet turunda genişletilmiş süre; diğer turlarda None (varsayılan emir)."""
    if not dogal_sohbet_enabled():
        return None
    if mode_norm not in ("genel", "uretim", "gelisim"):
        return None
    if is_natural_conversation_turn(message, mode_norm, question_plan):
        return natural_turn_budget_sec()
    return None


def natural_prior_depth() -> int:
    try:
        return max(4, min(int(os.environ.get("RUZGAR_DOGAL_PRIOR_MSGS", "14")), 24))
    except ValueError:
        return 14


def natural_max_tokens() -> int:
    try:
        return max(200, min(int(os.environ.get("RUZGAR_DOGAL_MAX_TOKENS", "720")), 1200))
    except ValueError:
        return 720


def natural_temperature() -> float:
    try:
        return max(0.35, min(float(os.environ.get("RUZGAR_DOGAL_TEMPERATURE", "0.62")), 0.9))
    except ValueError:
        return 0.62


_NATURAL_BLOCK = """### DOĞAL SOHBET MODU (Faz 91 — zorunlu)
Ümit abi ile **gerçek bir sohbet** ediyorsun; chatbot şablonu veya yükleme metni değilsin.

Üretim kuralları:
- Önceki turları hatırla; kısa devam cümlelerini bağlamdan çöz.
- Uzunluk: soruya göre **esnek** — tek kelimelik soruya kısa, duygu/plan/anlatıma 4–8 tam cümle.
- Kullanıcının cümlesini **kopyalama**; «evet seni anlıyorum» gibi mekanik echo yasak.
- Madde listesi ve ders anlatımı zorunlu değil; akıcı paragraf tercih et.
- «Hafızamda buldum», «kayıtlarımda» gibi meta ifadeler kullanma — doğal anlat.
- Bilmediğin özel güncel olayı uydurma; emin değilsen dürüstçe söyle.
- Samimi «Ümit abi» tonu; soğuk resmi dil veya sürekli yardım teklifi şablonu yok.
"""


def build_natural_sohbet_system_addon() -> str:
    return _NATURAL_BLOCK.strip() + "\n"


def build_natural_user_tail(message: str) -> str:
    return (
        "\n\n[TALİMAT — DOĞAL SOHBET TURU]\n"
        f"Kullanıcı mesajı:\n{(message or '').strip()}\n\n"
        "Bu tur **sohbet veya yakın muhabbet**; doğrudan, sıcak ve akıcı yanıt ver. "
        "Şablon karşılama veya «nasıl yardımcı olabilirim» ile başlama.\n"
    )


def enrich_health_build(build: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(build or {})
    out["dogal_sohbet_faz91"] = dogal_sohbet_enabled()
    out["dogal_budget_sec"] = natural_turn_budget_sec()
    return out


def public_meta() -> dict[str, Any]:
    return {
        "version": FAZ91_VERSION,
        "enabled": dogal_sohbet_enabled(),
        "budget_sec": natural_turn_budget_sec(),
        "skip_instant": True,
    }
