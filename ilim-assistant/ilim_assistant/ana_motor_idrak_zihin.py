# Created by Ümit & Gökçenur
"""
Ana Motor Faz AN/AO — İdrak Zihin.

Her turda (LLM öncesi): zaman çerçevesi, niyet, kaynak politikası.
Faz AO: kısa devam cümlelerinde önceki turdan zaman/niyet devralma.

Kapatma: RUZGAR_IDRAK_ZIHIN=0 · RUZGAR_IDRAK_THREAD_INHERIT=0 (AO)
"""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any

IDRAK_ZIHIN_VERSION = "idrak-zihin-faz-ao-v1-2026-06-14"

_TEMPORAL_PRESENT = re.compile(
    r"(?:"
    r"[şs]u\s*an|[şs]imdi|bug[üu]n|g[üu]ncel|son\s+durum|son\s+dakika|"
    r"halen|hala|devam\s+eden|aktif\s+(?:sava[şs]|catisma|çatışma)|"
    r"currently|right\s+now|today|this\s+week"
    r")",
    re.I,
)
_TEMPORAL_PAST = re.compile(
    r"(?:"
    r"ge[çc]mi[şs]te|eskiden|o\s+zaman|ne\s+zaman|hangi\s+y[ıi]l|"
    r"tarihte|tarihsel|d[üu]n\b|ge[çc]en\s+(?:y[ıi]l|ay|hafta)|"
    r"kuruldu|kurmu[şs]|oldu|ya[şs]ad[ıi]|"
    r"daha\s+once|daha\s+[öo]nce|konusmustuk|konu[şs]mu[şs]tuk"
    r")",
    re.I,
)
_TEMPORAL_FUTURE = re.compile(
    r"(?:"
    r"gelecekte|ileride|yarin|yar[ıi]n|onumuzde|önümüzde|"
    r"olacak\s+m[ıi]|olur\s+mu|planlan"
    r")",
    re.I,
)

_CONFLICT_CUES = (
    "savas",
    "savaş",
    "catisma",
    "çatışma",
    "saldir",
    "saldır",
    "operasyon",
    "kimle savas",
    "kimle savaş",
    "carpisma",
    "çarpışma",
    "catism",
    "haber",
    "kriz",
)

_CONTINUATION_EXACT = frozenset(
    {
        "devam",
        "devam et",
        "peki",
        "peki?",
        "tamam",
        "o?",
        "bu?",
        "ne?",
        "nasıl?",
        "nasil?",
        "sonra?",
        "ee?",
        "hmm?",
    }
)
_CONTINUATION_PREFIX = (
    "peki ",
    "peki,",
    "o konuda",
    "bu konuda",
    "aynı konu",
    "ayni konu",
    "devam ",
    "bunun ",
    "onun ",
    "şunun ",
    "sunun ",
)


def thread_inherit_enabled() -> bool:
    if not idrak_zihin_enabled():
        return False
    return os.environ.get("RUZGAR_IDRAK_THREAD_INHERIT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def idrak_zihin_enabled() -> bool:
    return os.environ.get("RUZGAR_IDRAK_ZIHIN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _norm_ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()


def _norm_blob(raw: str) -> str:
    low = (raw or "").strip().lower()
    return low + " " + _norm_ascii(raw)


@dataclass
class TurnIdrak:
    """Tek tur idrak özeti — plan ve hafıza kapıları bunu dinler."""

    temporal: str = "timeless"  # past | present | future | timeless
    intent: str = "bilgi"  # current_events | archive_recall | personal | casual | factual | calendar | bilgi | sohbet
    confidence: float = 0.5
    force_web: bool = False
    block_archive_recall: bool = False
    block_hafiza_first: bool = False
    block_chat_history_hint: bool = False
    prefer_natural_sohbet: bool = False
    status_tr: str = ""
    effective_query: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["version"] = IDRAK_ZIHIN_VERSION
        return d


def _detect_temporal(blob: str, asc: str) -> tuple[str, float]:
    if _TEMPORAL_PRESENT.search(blob) or _TEMPORAL_PRESENT.search(asc):
        return "present", 0.88
    if _TEMPORAL_FUTURE.search(blob) or _TEMPORAL_FUTURE.search(asc):
        return "future", 0.82
    if _TEMPORAL_PAST.search(blob) or _TEMPORAL_PAST.search(asc):
        return "past", 0.8
    return "timeless", 0.45


def _is_current_events(blob: str, asc: str, temporal: str) -> bool:
    try:
        from ilim_assistant.ana_motor_plan import looks_like_current_geopolitics_question

        if looks_like_current_geopolitics_question(blob):
            return True
    except Exception:
        pass
    geo = (
        "iran",
        "israil",
        "israel",
        "abd",
        "amerika",
        "ukrayna",
        "rusya",
        "gazze",
        "filistin",
        "myanmar",
        "cin",
        "china",
        "taiwan",
        "suriye",
        "irak",
        "yemen",
    )
    has_geo = any(g in asc for g in geo)
    has_conflict = any(c in asc or c in blob for c in _CONFLICT_CUES)
    if temporal == "present" and (has_geo or has_conflict):
        return True
    if has_geo and has_conflict:
        return True
    if temporal == "present" and re.search(
        r"\b(kim|kimler|hangi\s+ulke|hangi\s+[üu]lke|ne\s+oluyor)\b", asc
    ):
        if has_geo or any(
            x in asc for x in ("savas", "savaş", "haber", "kriz", "catisma", "çatışma")
        ):
            return True
    return False


def _history_user_lines(history: list | None) -> list[str]:
    out: list[str] = []
    if not history:
        return out
    for item in history:
        if isinstance(item, dict):
            if str(item.get("role") or "").strip().lower() == "user":
                u = str(item.get("content") or "").strip()
                if u:
                    out.append(u)
        elif isinstance(item, (list, tuple)) and len(item) >= 1:
            u = str(item[0] or "").strip()
            if u:
                out.append(u)
    return out


def _last_prior_user_message(history: list | None, *, skip: str = "") -> str:
    skip_n = (skip or "").strip()
    for u in reversed(_history_user_lines(history)):
        if skip_n and u.strip() == skip_n:
            continue
        if len(u.strip()) >= 8:
            return u.strip()
    return ""


def _looks_like_short_continuation(raw: str) -> bool:
    s = (raw or "").strip()
    if not s or len(s) > 140:
        return False
    low = s.casefold().strip(" .,!?\t\r\n")
    if low in _CONTINUATION_EXACT:
        return True
    if any(low.startswith(p) for p in _CONTINUATION_PREFIX):
        return True
    try:
        from ilim_assistant.idrak_on_islem import pretreat_user_turn

        pt = pretreat_user_turn(s, [])
        if pt.continuation:
            return True
    except Exception:
        pass
    words = s.split()
    if len(words) <= 6 and len(s) < 72:
        if "?" in s:
            return True
        if words and words[0].casefold() in ("peki", "ee", "hmm", "tamam", "sonra"):
            return True
    return False


def _should_inherit_thread(raw: str, out: TurnIdrak) -> bool:
    if not thread_inherit_enabled():
        return False
    if out.intent in ("personal", "archive_recall", "casual", "calendar"):
        return False
    if out.intent == "current_events" and out.temporal == "present":
        return False
    if not _looks_like_short_continuation(raw):
        return False
    return True


def _apply_current_events_policy(out: TurnIdrak, *, status_tr: str) -> TurnIdrak:
    out.intent = "current_events"
    out.temporal = "present"
    out.force_web = True
    out.block_archive_recall = True
    out.block_hafiza_first = True
    out.block_chat_history_hint = True
    out.confidence = max(out.confidence, 0.86)
    out.status_tr = status_tr
    return out


def _apply_thread_inheritance(out: TurnIdrak, raw: str, history: list | None) -> TurnIdrak:
    prior = _last_prior_user_message(history, skip=raw)
    if not prior:
        return out
    pb = _norm_blob(prior)
    pa = _norm_ascii(prior)
    pt, _ = _detect_temporal(pb, pa)
    prior_current = _is_current_events(pb, pa, pt)
    out.meta["inherited_from"] = prior[:160]
    out.meta["thread_inherit"] = True
    if len(raw.strip()) < 100:
        if raw.strip().casefold() not in prior.casefold():
            out.effective_query = f"{prior} — {raw.strip()}"
        else:
            out.effective_query = prior
    if prior_current or pt == "present":
        return _apply_current_events_policy(
            out,
            status_tr="Sohbet devamı — önceki güncel konu (web öncelikli)",
        )
    if pt == "past":
        out.temporal = "past"
        out.intent = "factual"
        out.status_tr = "Sohbet devamı — geçmiş konu"
        return out
    if pt == "future":
        out.temporal = "future"
        out.intent = "factual"
        out.status_tr = "Sohbet devamı — gelecek/olasılık"
        return out
    if _is_current_events(pb, pa, "timeless"):
        return _apply_current_events_policy(
            out,
            status_tr="Sohbet devamı — güncel jeopolitik bağlam",
        )
    out.status_tr = "Sohbet devamı — önceki konu"
    out.meta["inherited_intent"] = "bilgi"
    return out


def analyze_turn(
    message: str,
    history: list | None = None,
) -> TurnIdrak:
    """Tur başı idrak — plan, hafıza ve web kapıları için tek kaynak."""
    raw = (message or "").strip()
    out = TurnIdrak(effective_query=raw)
    if not raw:
        out.intent = "sohbet"
        out.prefer_natural_sohbet = True
        return out
    if not idrak_zihin_enabled():
        out.status_tr = "İdrak zihin kapalı"
        return out

    try:
        from ilim_assistant.ruzgar_tek_beyin import resolve_effective_user_query

        effective = resolve_effective_user_query(raw)
    except Exception:
        effective = raw
    out.effective_query = effective

    blob = _norm_blob(effective)
    asc = _norm_ascii(effective)
    temporal, t_conf = _detect_temporal(blob, asc)
    out.temporal = temporal
    out.confidence = t_conf

    # Kişisel hafıza — güncel jeopolitik değilse
    try:
        from ilim_assistant.ruzgar_tek_beyin import (
            matches_known_circle_name,
            should_use_personal_hafiza_first,
        )

        if should_use_personal_hafiza_first(effective, history) or matches_known_circle_name(
            effective
        ):
            if not _is_current_events(blob, asc, temporal):
                out.intent = "personal"
                out.confidence = 0.9
                out.block_archive_recall = True
                out.status_tr = "Kişisel hafıza / tanıdık çevre"
                return out
    except Exception:
        pass

    # Arşiv geri çağırma — açık geçmiş sorusu
    try:
        from ilim_assistant.ana_motor_plan import looks_like_past_conversation_query

        if looks_like_past_conversation_query(raw) and temporal != "present":
            out.intent = "archive_recall"
            out.confidence = 0.92
            out.status_tr = "Geçmiş sohbet / arşiv geri çağırma"
            return out
    except Exception:
        pass

    # Güncel olay / jeopolitik — web zorunlu, hafıza yasak
    if _is_current_events(blob, asc, temporal) or (
        temporal == "present"
        and re.search(r"\b(kim|kimler|ne\s+oluyor|durum)\b", asc)
    ):
        out.intent = "current_events"
        out.confidence = max(out.confidence, 0.9)
        out.force_web = True
        out.block_archive_recall = True
        out.block_hafiza_first = True
        out.block_chat_history_hint = True
        out.status_tr = "Güncel olay — web öncelikli, arşiv kapalı"
        return out

    # Takvim «hangi aydayız»
    try:
        from ilim_assistant.ruzgar_tek_beyin_analiz import _TEMPORAL_NOW

        if _TEMPORAL_NOW.search(blob):
            out.intent = "calendar"
            out.temporal = "present"
            out.confidence = 0.88
            out.status_tr = "Güncel takvim sorusu"
            return out
    except Exception:
        pass

    # Sohbet
    try:
        from ilim_assistant.ana_motor_plan import looks_like_casual_social_chat

        if looks_like_casual_social_chat(raw):
            out.intent = "casual"
            out.prefer_natural_sohbet = True
            out.confidence = 0.85
            out.status_tr = "Gündelik sohbet"
            return out
    except Exception:
        pass

    if temporal == "past":
        out.intent = "factual"
        out.status_tr = "Geçmiş / tarihsel bilgi"
    elif temporal == "future":
        out.intent = "factual"
        out.status_tr = "Gelecek / olasılık sorusu"
    else:
        out.intent = "bilgi"
        out.status_tr = "Genel bilgi"

    if _should_inherit_thread(raw, out):
        out = _apply_thread_inheritance(out, raw, history)
    return out


def should_skip_past_conversation_reply(idrak: TurnIdrak | None) -> bool:
    if not idrak or not idrak_zihin_enabled():
        return False
    return bool(idrak.block_archive_recall or idrak.intent == "current_events")


def should_block_hafiza_path(idrak: TurnIdrak | None) -> bool:
    if not idrak or not idrak_zihin_enabled():
        return False
    return bool(idrak.block_hafiza_first or idrak.block_chat_history_hint)


def build_idrak_zihin_directive(idrak: TurnIdrak | None) -> str:
    """LLM bağlamına kısa idrak talimatı."""
    if not idrak or not idrak_zihin_enabled():
        return ""
    temporal_labels = {
        "present": "ŞİMDİ / güncel",
        "past": "GEÇMİŞ",
        "future": "GELECEK",
        "timeless": "zamansız genel bilgi",
    }
    t_label = temporal_labels.get(idrak.temporal, idrak.temporal)
    lines = [
        "\n\n[TALİMAT — İDRAK ZİHİN — Faz AN/AO — dahili]",
        f"Zaman çerçevesi: **{t_label}**. Niyet: **{idrak.intent}**.",
    ]
    if idrak.meta.get("thread_inherit"):
        lines.append(
            "Bu tur önceki sohbet konusunun **devamı**; kopuk yeni konu açma, "
            "bir önceki sorunun çerçevesinde yanıt ver."
        )
    if idrak.temporal == "present" or idrak.intent == "current_events":
        lines.append(
            "Yanıt **bugünün bilgisine** dayanmalı; eğitim verisindeki eski çatışmaları "
            "«hâlâ sürüyor» diye yazma. Web/kaynak verilmişse onları esas al; "
            "tarih belirt (ör. «son kaynaklara göre…»)."
        )
    elif idrak.temporal == "past":
        lines.append("Kronolojik / dönemsel anlat; «şu an» iddiası kurma.")
    elif idrak.intent == "personal":
        lines.append("Kişisel hafıza kaydına sadık kal; ansiklopedik uydurma yapma.")
    elif idrak.intent == "casual":
        lines.append("Kısa, samimi, doğal sohbet; ağır ansiklopedi veya liste verme.")
    lines.append("Bu etiketleri kullanıcıya yazma.\n")
    return "\n".join(lines)


def apply_idrak_plan_bootstrap(
    message: str,
    mode_norm: str,
    idrak: TurnIdrak,
) -> Any | None:
    """plan_question erken dönüş — güncel olay / arşiv geri çağırma."""
    if not idrak_zihin_enabled():
        return None
    try:
        from ilim_assistant.ana_motor_plan import (
            QuestionPlan,
            rewrite_rag_search_query,
            rewrite_web_search_query,
        )
    except Exception:
        return None

    if idrak.intent == "current_events" or (
        idrak.force_web and idrak.temporal == "present"
    ):
        eq = idrak.effective_query or message
        web_q = rewrite_web_search_query(eq, "bilgi", mode_norm)
        return QuestionPlan(
            primary="bilgi",
            secondary=["bilim"],
            use_ilim_rag=True,
            prefer_web=True,
            prefer_archive=False,
            ambiguous=False,
            clarification=None,
            web_query=web_q,
            rag_query=rewrite_rag_search_query(eq, "bilgi"),
            status_text=idrak.status_tr or "İdrak: güncel olay — web ve kaynak taraması…",
        )

    if idrak.intent == "archive_recall" and not idrak.block_archive_recall:
        return QuestionPlan(
            primary="hafiza",
            secondary=["bilgi"],
            use_ilim_rag=False,
            prefer_web=False,
            prefer_archive=False,
            ambiguous=False,
            clarification=None,
            web_query="",
            rag_query="",
            status_text=idrak.status_tr or "Geçmiş sohbet aranıyor…",
        )

    return None


def idrak_zihin_status() -> dict[str, Any]:
    return {
        "enabled": idrak_zihin_enabled(),
        "version": IDRAK_ZIHIN_VERSION,
        "summary_tr": "Zaman + niyet + kaynak + sohbet devamı devralma (Faz AN/AO)",
    }
