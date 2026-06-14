# Created by Ümit & Gökçenur
"""Ana Motor — soru planı (B1–B3): sınıf, web sorgusu, belirsizlikte tek netleştirme."""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any

from ilim_assistant.web_tools import refined_search_query


def _plan_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_PLAN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _clarify_enabled() -> bool:
    return os.environ.get("RUZGAR_ANA_MOTOR_CLARIFY", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _norm_ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()


def looks_like_encyclopedic_fact_question(msg: str) -> bool:
    """
    Tek cevaplı genel tarih / devlet sorusu (ör. «Osmanlı devletini kim kurdu»).

    Amaç (Faz 9): Ana motor `bilim` → ağır arşiv+tam indeks zincirine düşmeden
    `bilgi` veya hızlı indeks turuna yönlendirmek; tasavvuf/ilim derinliği
    sorusu gibi kalıpları tetiklemez (kim + kurdu / ne zaman + uygarlık vb.).
    """
    if os.environ.get("RUZGAR_FAZ9_ENCYCLOPEDIC_BILGI_BOOST", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return False
    raw = (msg or "").strip()
    if len(raw) < 8:
        return False
    try:
        from ilim_assistant.ruzgar_tek_beyin import personal_hafiza_blocks_bilgi_path

        if personal_hafiza_blocks_bilgi_path(raw):
            return False
    except Exception:
        pass
    asc = _norm_ascii(raw)
    low = raw.lower()
    blob = low + " " + asc

    history_terms = (
        "osmanlı",
        "osmanli",
        "padişah",
        "padisah",
        "devlet",
        "imparator",
        "hanedan",
        "selçuk",
        "selcuk",
        "bizans",
        "roma",
        "kurucu",
        "ilk ",
    )

    # «… kim kurdu / kim kurmuş …» (ASCII türevinde güvenli)
    if re.search(r"\bkim\b", asc) and re.search(
        r"\b(kurdu|kurdular|kuruldu|kurmus|kurmuş|kurduklari|kurdukları|etti)\b",
        asc,
    ):
        return True

    # «İlk Osmanlı padişahı kimdir?» gibi tek cevaplı kısa tarih soruları.
    if (
        re.search(r"\b(kimdir|kimdi|kim)\b", asc)
        and any(x in blob for x in history_terms)
        and len(raw) <= 120
    ):
        return True

    # «Ne zaman …» + büyük devlet / uygarlık adı (yüzeysel genel tarih)
    if re.search(r"\bne zaman\b", asc) or re.search(r"\bhangi yil\b", asc):
        if any(x in blob for x in history_terms + ("halifelik", "abbasi", "abbâsî")):
            return True

    return False


def looks_like_fast_llm_fact_question(msg: str) -> bool:
    """
    Genel bilim / kısa «nedir» / gezegen karşılaştırma — DuckDuckGo + sayfa okuma
  genelde gereksiz; doğrudan LLM hızlı yolu (Faz 49).
    """
    if os.environ.get("RUZGAR_FAZ49_FAST_FACT", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return False
    raw = (msg or "").strip()
    if not raw or len(raw) > 220:
        return False
    if looks_like_encyclopedic_fact_question(msg):
        try:
            from ilim_assistant.ruzgar_tek_beyin import personal_hafiza_blocks_bilgi_path

            if personal_hafiza_blocks_bilgi_path(msg):
                return False
        except Exception:
            pass
        try:
            from ilim_assistant.ana_motor_fast import fast_local_rag_first_enabled

            if fast_local_rag_first_enabled():
                return False
        except Exception:
            pass
        return True
    asc = _norm_ascii(raw)
    low = raw.lower()
    if any(x in low for x in ("güncel", "guncel", "bugün", "bugun", "haber", "son dakika")):
        return False
    if re.search(r"\b(nedir|ne demek|tanımı|tanimi)\b", asc) and len(raw.split()) <= 16:
        return True
    if re.search(
        r"\b(yoksa|hangisi|daha\s+(büyük|buyuk|küçük|kucuk|uzak|ağır|agir))\b", asc
    ):
        return True
    if re.search(r"\b(mu|mı|mi)\s+(daha\s+)?(büyük|buyuk|küçük|kucuk)\b", asc):
        return True
    science = (
        "neptün",
        "neptun",
        "dünya",
        "dunya",
        "mars",
        "jüpiter",
        "jupiter",
        "venüs",
        "venus",
        "merkür",
        "merkur",
        "plüton",
        "pluton",
        "uzay",
        "gezegen",
        "güneş",
        "gunes",
    )
    if re.search(r"\b(en\s+uzak|en\s+yakin|en\s+yakın)\b", asc) and any(
        k in asc for k in science + ("gezegen", "gezegeni")
    ):
        return True
    if "?" in raw and len(raw.split()) <= 20:
        if any(k in asc for k in science):
            return True
    return False


PRIMARY_LABELS_TR: dict[str, str] = {
    "bilgi": "Bilgi araştırması",
    "gundelik": "Sohbet",
    "islem": "Kod / işlem",
    "dosya": "Dosya / workspace",
    "hafiza": "Hafıza / kayıt",
    "bilim": "İlim / tarih",
    "hava": "Güncel hava",
    "dilbilgisi": "Dilbilgisi / nahiv",
}


@dataclass
class QuestionPlan:
    """Tek tur için Ana Motor karar özeti."""

    primary: str  # bilgi | gundelik | islem | dosya | hafiza | bilim | hava | dilbilgisi
    secondary: list[str] = field(default_factory=list)
    use_ilim_rag: bool = True
    prefer_web: bool = True
    prefer_archive: bool = False
    ambiguous: bool = False
    clarification: str | None = None
    web_query: str = ""
    rag_query: str = ""
    status_text: str = "Ana motor düşünüyor…"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["label_tr"] = PRIMARY_LABELS_TR.get(self.primary, self.primary)
        d["sources"] = _sources_summary(self)
        return d


def _sources_summary(plan: QuestionPlan) -> str:
    parts: list[str] = []
    if plan.prefer_archive:
        parts.append("arşiv")
    if plan.use_ilim_rag:
        parts.append("indeks")
    if plan.prefer_web:
        parts.append("web")
    return " + ".join(parts) if parts else "doğrudan yanıt"


def _score_categories(msg: str, mode_norm: str, motor_flags: dict[str, bool]) -> dict[str, float]:
    raw = (msg or "").strip()
    low = raw.lower()
    asc = _norm_ascii(raw)
    blob = low + " " + asc
    s: dict[str, float] = {
        "bilgi": 0.0,
        "gundelik": 0.0,
        "islem": 0.0,
        "dosya": 0.0,
        "hafiza": 0.0,
        "bilim": 0.0,
        "hava": 0.0,
        "dilbilgisi": 0.0,
    }

    if mode_norm in ("programlama",):
        s["islem"] += 3.0
    if mode_norm in ("okuma", "hafiza"):
        s["bilim"] += 2.0
        s["hafiza"] += 1.5
    if mode_norm == "hafiza":
        s["hafiza"] += 3.0

    if motor_flags.get("programlama"):
        s["islem"] += 2.5
    if motor_flags.get("bellek") or motor_flags.get("hafiza"):
        s["hafiza"] += 2.5
    if motor_flags.get("bilim"):
        s["bilim"] += 2.5
    if motor_flags.get("hizir"):
        s["bilgi"] += 1.0

    if any(
        x in blob
        for x in (
            "hava",
            "yağmur",
            "yagmur",
            "derece",
            "sicak",
            "sıcak",
            "meteoroloji",
            "kar yağ",
        )
    ):
        s["hava"] += 3.0
    try:
        from ilim_assistant.chat_core import _is_live_weather_query, _weather_intent

        if _weather_intent(raw) or _is_live_weather_query(raw):
            s["hava"] += 5.0
            s["gundelik"] = max(0.0, s["gundelik"] - 2.0)
            s["bilim"] = max(0.0, s["bilim"] - 2.0)
    except Exception:
        pass

    if any(
        x in blob
        for x in (
            "hatırla",
            "hafiza",
            "hafıza",
            "kaydet",
            "öğren",
            "ogren",
            "not al",
            "geçmiş sohbet",
        )
    ):
        s["hafiza"] += 2.5

    if looks_like_past_conversation_query(raw):
        s["hafiza"] += 7.0
        s["bilgi"] = max(0.0, s["bilgi"] - 4.0)
        s["bilim"] = max(0.0, s["bilim"] - 2.0)
        s["gundelik"] = max(0.0, s["gundelik"] - 1.0)

    try:
        from ilim_assistant.ruzgar_tek_beyin import looks_like_friend_mood_chat

        if looks_like_friend_mood_chat(raw):
            s["gundelik"] += 6.0
            s["bilgi"] = max(0.0, s["bilgi"] - 3.0)
    except Exception:
        pass

    if any(
        x in blob
        for x in (
            "cevir",
            "çevir",
            "tercume",
            "tercüme",
            "translate",
            "ingilizceye",
            "turkceye",
            "türkçeye",
            "arapcaya",
            "arapçaya",
        )
    ):
        s["islem"] += 4.0
        s["bilgi"] = max(0.0, s["bilgi"] - 2.0)

    if re.search(r"\.(py|js|ts|html|css|json|md|txt|pdf)\b", low) or re.search(
        r"[a-z]:\\|/[\w.-]+/", raw
    ):
        s["dosya"] += 2.0
        s["islem"] += 1.0

    _bilgi_soru = any(
        x in blob
        for x in (
            "nedir",
            "ne demek",
            "ne ise",
            "nasıl çalışır",
            "nasil calisir",
            "açıkla",
            "acikla",
            "anlat",
            "farkı",
            "farki",
        )
    )
    if any(
        x in blob
        for x in (
            "kod",
            "python",
            "javascript",
            "debug",
            "refactor",
            "fonksiyon",
            "import ",
            "def ",
            "çalıştır",
            "calistir",
        )
    ):
        if _bilgi_soru and not any(
            x in blob for x in ("yaz", "duzelt", "düzelt", "calistir", "çalıştır", "debug")
        ):
            s["bilgi"] += 2.0
        else:
            s["islem"] += 2.0

    if any(
        x in blob
        for x in (
            "tarih",
            "osmanlı",
            "osmanli",
            "medeniyet",
            "padişah",
            "padisah",
            "kuran",
            "hadis",
            "tecvid",
            "nahiv",
            "fizik",
            "kimya",
            "biyoloji",
        )
    ):
        s["bilim"] += 2.0

    if any(
        x in blob
        for x in (
            "gramer",
            "dilbilgisi",
            "nahiv",
            "tecvid",
            "cümle doğru",
            "cumle dogru",
            "yazım",
            "yazim",
        )
    ):
        s["dilbilgisi"] += 2.5

    if any(
        x in blob
        for x in (
            "nedir",
            "nasıl",
            "nasil",
            "niçin",
            "nicin",
            "kimdir",
            "kaç",
            "kac",
            "ne zaman",
            "nerede",
            "açıkla",
            "acikla",
            "anlat",
            "farkı",
            "farki",
        )
    ):
        s["bilgi"] += 1.5

    if any(
        x in blob
        for x in (
            "selam",
            "merhaba",
            "günaydın",
            "gunaydin",
            "nasılsın",
            "nasilsin",
            "teşekkür",
            "tesekkur",
            "iyi geceler",
            "hoşça kal",
            "sohbet",
            "muhabbet",
            "hal hatir",
            "hal-hatir",
            "konusalim",
            "konuşalım",
            "edelim",
            "yapalim",
            "yapalım",
            "ne dersin",
            "sence",
            "beraber",
            "birlikte",
            "can sıkıntı",
            "can sikinti",
            "bos vakt",
            "boş vakt",
            "ne yapalim",
            "ne yapalım",
        )
    ):
        s["gundelik"] += 2.5
    if "sadece sohbet" in blob or "yalnizca sohbet" in blob:
        s["gundelik"] += 4.0

    if "?" in raw or any(x in blob for x in (" mi", " mı", " mu", " mü")):
        if (
            s["gundelik"] < 1.2
            and s["bilim"] < 1.5
            and not looks_like_casual_social_chat(raw)
            and not _explicit_research_intent(raw)
        ):
            s["bilgi"] += 0.8

    if len(raw) < 14:
        s["gundelik"] += 0.6

    # Genel tarih ansiklopedik soru — bilgi önceliği (ağır arşiv turu yok)
    if looks_like_encyclopedic_fact_question(raw):
        s["bilgi"] += 2.6

    # Faz B3 — genel modda kısa sorular bilgi + web önceliği (sohbet selamı hariç)
    if (
        mode_norm in ("genel", "uretim", "gelisim")
        and len(raw) < 80
        and not looks_like_casual_social_chat(raw)
    ):
        if _explicit_research_intent(raw) or "?" in raw:
            s["bilgi"] += 2.4
            s["gundelik"] = max(0.0, s["gundelik"] - 1.8)
        elif re.search(
            r"\b(nedir|kimdir|ne zaman|nerede|kac|kaç)\b",
            asc,
        ):
            s["bilgi"] += 1.6
            s["gundelik"] = max(0.0, s["gundelik"] - 1.0)

    return s


def _pick_primary_secondary(scores: dict[str, float]) -> tuple[str, list[str]]:
    ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    primary = ordered[0][0]
    top = ordered[0][1]
    secondary = [k for k, v in ordered[1:4] if v >= max(1.2, top * 0.55)]
    return primary, secondary


def _build_clarification(primary: str, secondary: list[str], msg: str) -> str:
    sec = set(secondary)
    if "islem" in sec or primary == "islem":
        if "bilgi" in sec or primary == "bilgi":
            return (
                "Ümit abi, bunu **kod/dosya işi** mi yoksa **genel bilgi araştırması** "
                "olarak mı yanıtlayayım? Tek cümleyle yön verirsen hemen devam ederim."
            )
    if "bilim" in sec and ("gundelik" in sec or primary == "gundelik"):
        return (
            "İlim/tarih kaynaklarından mı arayayım, yoksa **kısa sohbet** olarak mı "
            "yanıtlayayım?"
        )
    if len(msg.strip()) < 12:
        return (
            "Tam olarak ne istediğini bir cümleyle netleştirir misin — "
            "**özet bilgi mi**, **araştırma mı**, yoksa **sohbet mi**?"
        )
    return (
        "Birkaç farklı yöne gidebilirim; **en çok hangisini** istiyorsun: "
        "bilgi araştırması, ilim/tarih, kod/işlem, yoksa kısa sohbet?"
    )


def _status_for_plan(primary: str, web_query: str = "") -> str:
    wq = (web_query or "").strip()
    web_tail = f" (web: {wq[:56]}…)" if len(wq) > 56 else (f" (web: {wq})" if wq else "")
    labels = {
        "bilgi": "Soru analizi: bilgi — web ve yerel kaynaklar taranıyor…",
        "gundelik": "Soru analizi: sohbet — doğrudan yanıt hazırlanıyor…",
        "islem": "Soru analizi: işlem/kod — atölye bağlamı…",
        "dosya": "Soru analizi: dosya/workspace…",
        "hafiza": "Soru analizi: hafıza ve kayıt…",
        "bilim": "Soru analizi: ilim/tarih — arşiv ve indeks öncelikli…",
        "hava": "Soru analizi: güncel hava…",
        "dilbilgisi": "Soru analizi: dilbilgisi — yerel ders notları…",
    }
    base = labels.get(primary, "Ana motor düşünüyor…")
    if primary == "bilgi" and web_tail:
        return base.rstrip("…") + web_tail
    return base


def looks_like_current_geopolitics_question(message: str) -> bool:
    """Güncel jeopolitik / aktif çatışma — web öncelikli (RAG tarih arşivi yetmez)."""
    raw = (message or "").strip()
    if len(raw) < 10:
        return False
    low = raw.lower()
    asc = _norm_ascii(raw)
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
        "tayvan",
        "kore",
    )
    time_cues = (
        "su an",
        "şu an",
        "suan",
        "simdi",
        "şimdi",
        "bugun",
        "bugün",
        "guncel",
        "güncel",
        "son durum",
        "haber",
        "son dakika",
        "halen",
        "hala",
        "devam eden",
    )
    conflict = (
        "savas",
        "savaş",
        "catisma",
        "çatışma",
        "saldir",
        "saldır",
        "operasyon",
        "kimle savas",
        "kimle savaş",
        "aktif savas",
        "aktif savaş",
        "carpisma",
        "çarpışma",
    )
    has_geo = any(g in asc for g in geo)
    has_time = any(t in asc or t in low for t in time_cues)
    has_conflict = any(c in asc or c in low for c in conflict)
    if has_geo and (has_time or has_conflict):
        return True
    if re.search(r"\b(abd|amerika|usa)\b", asc) and has_conflict:
        return True
    if re.search(r"\biran\b", asc) and re.search(r"\b(israil|israel|abd|amerika)\b", asc):
        return True
    return False


def plan_question(
    message: str,
    mode_norm: str,
    motor_flags: dict[str, bool] | None = None,
) -> QuestionPlan:
    flags = motor_flags or {}
    try:
        from ilim_assistant.ruzgar_tek_beyin import resolve_effective_user_query

        effective_msg = resolve_effective_user_query(message)
    except Exception:
        effective_msg = (message or "").strip()
    if looks_like_current_geopolitics_question(effective_msg):
        web_q = rewrite_web_search_query(effective_msg, "bilgi", mode_norm)
        return QuestionPlan(
            primary="bilgi",
            secondary=["bilim"],
            use_ilim_rag=True,
            prefer_web=True,
            prefer_archive=False,
            ambiguous=False,
            clarification=None,
            web_query=web_q,
            rag_query=rewrite_rag_search_query(effective_msg, "bilgi"),
            status_text="Soru analizi: güncel jeopolitik — web ve kaynak taraması…",
        )
    try:
        from ilim_assistant.ruzgar_tek_beyin_analiz import (
            classify_question_intent,
            tek_beyin_analiz_enabled,
        )

        if tek_beyin_analiz_enabled():
            intent = classify_question_intent(message)
            if intent.get("intent") == "simple_fact" and intent.get("direct_answer"):
                return QuestionPlan(
                    primary="bilgi",
                    secondary=[],
                    use_ilim_rag=False,
                    prefer_web=False,
                    prefer_archive=False,
                    ambiguous=False,
                    clarification=None,
                    web_query="",
                    rag_query="",
                    status_text="Soru analizi: basit gerçek — doğrudan yanıt",
                )
    except Exception:
        pass
    try:
        from ilim_assistant.ruzgar_tek_beyin_konusma_akisi import looks_like_meta_feedback

        if looks_like_meta_feedback(message):
            return QuestionPlan(
                primary="gundelik",
                secondary=[],
                use_ilim_rag=False,
                prefer_web=False,
                prefer_archive=False,
                ambiguous=False,
                clarification=None,
                web_query="",
                rag_query="",
                status_text="Soru analizi: geri bildirim — sohbet",
            )
    except Exception:
        pass
    try:
        from ilim_assistant.ana_motor_tercume_yurut import is_instant_translate_message

        if is_instant_translate_message(message):
            return QuestionPlan(
                primary="islem",
                secondary=[],
                use_ilim_rag=False,
                prefer_web=False,
                prefer_archive=False,
                ambiguous=False,
                clarification=None,
                web_query="",
                rag_query="",
                status_text="Soru analizi: çeviri — sohbet içi backend…",
            )
    except Exception:
        pass
    scores = _score_categories(message, mode_norm, flags)
    primary, secondary = _pick_primary_secondary(scores)
    top = scores[primary]
    second_top = scores[secondary[0]] if secondary else 0.0

    use_ilim_rag = primary in ("bilgi", "bilim", "dilbilgisi") or mode_norm in (
        "okuma",
        "hafiza",
    )
    if primary == "gundelik":
        use_ilim_rag = False
    if primary in ("islem", "dosya", "hava"):
        use_ilim_rag = False

    low_msg = (message or "").lower()
    prefer_web = primary in ("bilgi",) or (
        primary == "gundelik"
        and scores.get("bilgi", 0) >= 1.0
        and any(
            x in low_msg
            for x in (
                "nedir",
                "kimdir",
                "kaç",
                "kac",
                "ne zaman",
                "güncel",
                "guncel",
                "hangi",
                "nasıl yap",
                "nasil yap",
            )
        )
    )
    # Faz B3 — genel mod + bilgi: web varsayılan (kısa sorular dahil)
    if (
        mode_norm in ("genel", "uretim", "gelisim")
        and primary == "bilgi"
        and len((message or "").strip()) < 120
    ):
        prefer_web = True
    if primary == "bilim" and any(x in low_msg for x in ("güncel", "guncel", "bugün", "bugun")):
        prefer_web = True
    if primary == "gundelik" and any(
        x in low_msg for x in ("sohbet", "sadece sohbet", "nasilsin", "nasılsın", "naber")
    ):
        prefer_web = False
        use_ilim_rag = False
    if primary in ("gundelik", "hafiza", "dilbilgisi") and scores.get("bilgi", 0) < 1.0:
        prefer_web = False
    if primary == "hava":
        prefer_web = True
    if looks_like_fast_llm_fact_question(message):
        try:
            from ilim_assistant.ruzgar_web_arastirma_pro import web_arastirma_pro_enabled

            if not web_arastirma_pro_enabled():
                prefer_web = False
                if primary == "bilgi":
                    use_ilim_rag = False
        except Exception:
            prefer_web = False
            if primary == "bilgi":
                use_ilim_rag = False
    elif (
        mode_norm in ("genel", "uretim", "gelisim")
        and primary in ("bilgi", "bilim", "dilbilgisi")
    ):
        try:
            from ilim_assistant.ruzgar_web_arastirma_pro import web_arastirma_pro_enabled

            if web_arastirma_pro_enabled():
                prefer_web = True
        except Exception:
            pass

    # Faz B3 — genel kısa bilgi sorusunda web varsayılan (Faz 49 hız yolunun üstüne)
    if (
        mode_norm in ("genel", "uretim", "gelisim")
        and primary == "bilgi"
        and len((message or "").strip()) < 120
        and os.environ.get("RUZGAR_FAZ_B3_WEB_DEFAULT", "1").strip().lower()
        not in ("0", "false", "no")
        and not looks_like_casual_social_chat(message)
    ):
        prefer_web = True

    prefer_archive = primary == "bilim" or flags.get("bilim")

    ambiguous = False
    clarification: str | None = None
    raw_len = len((message or "").strip())
    if mode_norm in ("genel", "uretim", "gelisim") and top > 0:
        if raw_len < 12:
            ambiguous = True
        elif raw_len < 20 and top < 2.2:
            ambiguous = True
        elif secondary and second_top >= top * 0.85 and top < 2.5:
            ambiguous = True
        elif len(secondary) >= 2 and second_top >= 1.8:
            ambiguous = True
    if ambiguous:
        clarification = _build_clarification(primary, secondary, message)

    web_q = (
        rewrite_web_search_query(message, primary, mode_norm) if prefer_web else ""
    )
    rag_q = rewrite_rag_search_query(message, primary) if use_ilim_rag else ""

    status = _status_for_plan(primary, web_q if prefer_web else "")

    if looks_like_past_conversation_query(message):
        primary = "hafiza"
        secondary = [x for x in secondary if x != "hafiza"][:2]
        use_ilim_rag = False
        prefer_web = False
        prefer_archive = False
        ambiguous = False
        clarification = None
        web_q = ""
        rag_q = ""
        status = _status_for_plan("hafiza", "")

    try:
        from ilim_assistant.ruzgar_tek_beyin import tek_beyin_plan_override

        _tb = (
            None
            if looks_like_clarification_short_query(message)
            else tek_beyin_plan_override(message)
        )
        if _tb:
            primary = str(_tb.get("primary") or "hafiza")
            secondary = [x for x in secondary if x != primary][:2]
            use_ilim_rag = False
            prefer_web = False
            prefer_archive = False
            ambiguous = False
            clarification = None
            web_q = ""
            rag_q = ""
            label = str(_tb.get("label_tr") or "").strip()
            status = _status_for_plan(primary, "")
            if label:
                status = f"{label} — {status}" if status else label
    except Exception:
        pass

    try:
        from ilim_assistant.ruzgar_tek_beyin import tek_beyin_dost_plan_override

        _td = tek_beyin_dost_plan_override(message)
        if _td and primary != "hafiza":
            primary = str(_td.get("primary") or "gundelik")
            secondary = [x for x in secondary if x != primary][:2]
            use_ilim_rag = False
            prefer_web = False
            prefer_archive = False
            ambiguous = False
            clarification = None
            web_q = ""
            rag_q = ""
            status = _status_for_plan("gundelik", "")
    except Exception:
        pass

    plan = QuestionPlan(
        primary=primary,
        secondary=secondary,
        use_ilim_rag=use_ilim_rag,
        prefer_web=prefer_web,
        prefer_archive=prefer_archive,
        ambiguous=ambiguous,
        clarification=clarification if _clarify_enabled() else None,
        web_query=web_q,
        rag_query=rag_q,
        status_text=status,
    )
    try:
        from ilim_assistant.ruzgar_web_arastirma_pro import apply_web_pro_plan_overrides

        plan = apply_web_pro_plan_overrides(plan, message)
    except Exception:
        pass
    return plan


def rewrite_rag_search_query(message: str, primary: str) -> str:
    """B2 — vektör / arşiv araması için odaklı sorgu (web ile aynı temizlik, farklı uzunluk)."""
    base = refined_search_query(message)
    if not base:
        return (message or "").strip()[:240]
    low = base.lower()
    if primary == "bilim":
        if any(x in low for x in ("osman", "padisah", "padişah", "devri", "dönem")) and "tarih" not in low:
            base = f"{base} tarih"
    if primary == "dilbilgisi" and "nahiv" not in low and "gramer" not in low:
        if any(x in low for x in ("cümle", "cumle", "fiil", "yüklem")):
            base = f"{base} Türkçe dilbilgisi"
    try:
        cap = max(60, int(os.environ.get("RAG_QUERY_MAX_CHARS", "180")))
    except ValueError:
        cap = 180
    if len(base) > cap:
        base = base[:cap].rsplit(" ", 1)[0].strip()
    return base.strip()


def rag_search_query_for_turn(message: str, plan: QuestionPlan | None) -> str:
    if plan is None or not _plan_enabled():
        return (message or "").strip()
    q = (plan.rag_query or "").strip()
    return q or (message or "").strip()


def rewrite_web_search_query(message: str, primary: str, mode_norm: str) -> str:
    """B2 — DuckDuckGo için odaklı sorgu."""
    base = refined_search_query(message)
    if not base:
        return ""
    low = base.lower()
    if primary == "bilim" and "tarih" not in low and "osman" not in low:
        if any(x in low for x in ("devri", "dönem", "medeniyet", "padişah", "padisah")):
            base = f"{base} tarih"
    if primary == "bilgi" and os.environ.get("RUZGAR_WEB_QUERY_RECENCY", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        recency = any(
            x in low
            for x in (
                "güncel",
                "guncel",
                "bugün",
                "bugun",
                "son",
                "2024",
                "2025",
                "2026",
                "haber",
            )
        )
        try:
            recency = recency or looks_like_current_geopolitics_question(message)
        except Exception:
            pass
        if recency:
            if "2026" not in low and "2025" not in low:
                base = f"{base} 2026"
            if looks_like_current_geopolitics_question(message) and "güncel" not in low:
                base = f"{base} güncel"
    words = base.split()
    if primary == "gundelik" and len(words) > 12:
        base = " ".join(words[:12])
    return base.strip()


def _info_query_blocks_casual(message: str) -> bool:
    """Selam + bilgi sorusu (TDK, anlamı, nedir…) — gündelik/sohbet sayılmasın."""
    raw = (message or "").strip()
    if not raw:
        return False
    if _explicit_research_intent(raw):
        return True
    blob = _norm_ascii(raw.lower()) + " " + raw.lower()
    markers = (
        "tdk",
        "anlami",
        "anlamı",
        "kelime",
        "kelimesi",
        "sozluk",
        "sözlük",
        "sozlukte",
        "sözlükte",
        "ingilizceye",
        "ingilizceye çevir",
        "cevir:",
        "çevir:",
    )
    return any(m in blob for m in markers)


def looks_like_past_conversation_query(message: str) -> bool:
    """Geçmiş sohbet / hafıza geri çağırma — jsonl + oturum geçmişi."""
    raw = (message or "").strip()
    if len(raw) < 8:
        return False
    blob = _norm_ascii(raw.lower()) + " " + raw.lower()
    cues = (
        "dun ",
        "dün ",
        "gecen ",
        "geçen ",
        "daha once",
        "daha önce",
        "konusmustuk",
        "konuşmuştuk",
        "konusmistik",
        "konuşmuştık",
        "ne konus",
        "ne konuş",
        "hangi konulari",
        "hangi konuları",
        "hangi soru",
        "hangi sorular",
        "ne sormu",
        "sormustum",
        "sormuştum",
        "sordum ",
        " sordum",
        "sormus",
        "sormuş",
        "hatirliyor musun",
        "hatırlıyor musun",
        "konuşmuş olabilir",
        "konusmus olabilir",
        "bahsetmiş",
        "bahsettik",
        "hakkında konuş",
        "hakkinda konus",
        "hakkında konus",
        "demiş miydim",
        "demistim",
        "demiştim",
        "kayitli sohbet",
        "kayıtlı sohbet",
        "onceki sohbet",
        "önceki sohbet",
        "gecmis sohbet",
        "geçmiş sohbet",
    )
    if any(c in blob for c in cues):
        return True
    if re.search(
        r"(?:baska|başka)\s+hangi\s+(?:soru|konu|mesaj)",
        blob,
        re.I,
    ):
        return True
    if re.search(
        r"(?:konus|konuş)(?:mus|muş|mustuk|muştuk|mistik|miştik|tuk|tık)?\s*(?:olabilir|miyiz|mu|mı)",
        blob,
        re.I,
    ):
        return True
    return False


def looks_like_educational_code_question(message: str) -> bool:
    """«Python'da liste nasıl ters çevrilir» — atölye delege etme, genel LLM cevaplasın."""
    raw = (message or "").strip()
    if not raw or len(raw) > 320:
        return False
    low = _norm_ascii(raw.lower())
    lang = ("python", "javascript", "typescript", "java", "sql", "html", "css")
    if not any(x in low for x in lang):
        return False
    edu = (
        "nedir",
        "nasil",
        "nasıl",
        "ornek",
        "örnek",
        "acikla",
        "açıkla",
        "anlat",
        "farki",
        "farkı",
        "ters cevr",
        "listeyi",
        "liste ",
    )
    if not any(x in low for x in edu):
        return False
    if any(
        x in low
        for x in (
            "@@write",
            "@@read",
            "projects/",
            "traceback",
            "pytest",
            "main.py",
            "app.py",
            "dosyas",
            "refactor",
            "patch",
            "gorev:",
            "görev:",
        )
    ):
        return False
    return True


_CLARIFY_SHORT_RE = re.compile(
    r"^(?:bu|o|şu|su|ne|hangisi|hangi|kim|nasıl|nasil|neden|niye|mi|mı|mu|mü)\??$",
    re.I,
)


def looks_like_clarification_short_query(message: str) -> bool:
    """«bu?» gibi belirsiz kısa soru — hafıza/chat_history hijack etmesin."""
    raw = (message or "").strip()
    if not raw or len(raw) >= 12:
        return False
    if _CLARIFY_SHORT_RE.match(raw):
        return True
    return "?" in raw and len(raw.split()) <= 2


def looks_like_casual_social_chat(message: str) -> bool:
    """Selam, sohbet daveti, kısa muhabbet — ağır RAG / dev hafıza taraması yok."""
    raw = (message or "").strip().lower()
    if not raw:
        return False
    try:
        from ilim_assistant.ruzgar_tek_beyin import looks_like_friend_mood_chat

        max_len = 280 if looks_like_friend_mood_chat(message) else 140
    except Exception:
        max_len = 140
    if len(raw) > max_len:
        return False
    if _info_query_blocks_casual(message):
        return False
    blob = _norm_ascii(raw) + " " + raw
    cues = (
        "selam",
        "selamunaleykum",
        "selamünaleyküm",
        "aleykumselam",
        "aleykümselam",
        "merhaba",
        "gunaydin",
        "günaydın",
        "iyi aksam",
        "iyi akşam",
        "iyi geceler",
        "nasilsin",
        "nasılsın",
        "naber",
        "ne haber",
        "tesekkur",
        "teşekkür",
        "sagol",
        "sağol",
        "eyvallah",
        "sohbet edelim",
        "sohbet eder",
        "biraz sohbet",
        "konusalim",
        "konuşalım",
        "muhabbet",
        "hasbel kader",
        "vakit var mi",
        "vakit var mı",
        "bos musun",
        "boş musun",
        "ne yapiyorsun",
        "ne yapıyorsun",
        "keyfin nasil",
        "keyfin nasıl",
        "ben geldim",
        "geldim",
        "buradayim",
        "buradayım",
        "hos geldin",
        "hoş geldin",
        "canım sıkıldı",
        "canim sikildi",
        "sıkıldım",
        "sikildim",
        "moralim bozuk",
        "keyfim yok",
        "dertleşelim",
        "dertleşmek",
        "konuşalım mı",
        "sohbet edelim mi",
        "yanımda ol",
        "yanimda ol",
    )
    if any(c in blob for c in cues):
        return True
    if "sohbet" in blob and len(raw.split()) <= 14:
        return True
    if ("mi?" in raw or "mı?" in raw) and len(raw.split()) <= 10:
        if any(x in blob for x in ("sohbet", "konus", "konuş", "muhabbet", "beraber")):
            return True
    return False


def looks_like_greeting_or_smalltalk(message: str) -> bool:
    """Geriye uyumluluk."""
    return looks_like_casual_social_chat(message)


def _explicit_research_intent(message: str) -> bool:
    """Açık bilgi/ilim araştırması — sohbet yoluna düşmesin."""
    raw = (message or "").strip()
    if not raw:
        return False
    blob = _norm_ascii(raw.lower()) + " " + raw.lower()
    cues = (
        "nedir",
        "ne demek",
        "kimdir",
        "kim kurdu",
        "ne zaman",
        "nerede",
        "kaç",
        "kac",
        "açıkla",
        "acikla",
        "detaylı",
        "detayli",
        "araştır",
        "arastir",
        "kaynak",
        "kanıt",
        "kanit",
        "osmanlı",
        "osmanli",
        "hadis",
        "ayet",
        "tefsir",
        "fizik",
        "kimya",
        "tarih",
        "güncel haber",
        "guncel haber",
    )
    return any(c in blob for c in cues)


def is_casual_conversation_turn(
    message: str,
    mode_norm: str,
    question_plan: QuestionPlan | None = None,
    *,
    history: list | None = None,
) -> bool:
    """
    Sohbet / gündelik tur — ağır RAG ve dev hafıza yok; Gemini hızlı yol.
    Tek bir kalıba bağlı değil; plan + mesaj birlikte değerlendirilir.
    Faz 91: doğal sohbet algısı genişletilir (şablon yerine LLM).
    """
    try:
        from ilim_assistant.ruzgar_dogal_sohbet_faz91 import (
            dogal_sohbet_enabled,
            is_natural_conversation_turn,
        )

        if dogal_sohbet_enabled():
            return is_natural_conversation_turn(
                message, mode_norm, question_plan, history=history
            )
    except Exception:
        pass
    if mode_norm not in ("genel", "uretim", "gelisim"):
        return False
    if _explicit_research_intent(message):
        return False
    if looks_like_casual_social_chat(message):
        return True
    if question_plan is None:
        return False
    if question_plan.primary == "gundelik" and not question_plan.use_ilim_rag:
        return len((message or "").strip()) < 220
    return False


def apply_casual_plan_overrides(
    message: str,
    mode_norm: str,
    plan: QuestionPlan,
) -> QuestionPlan:
    """Sohbet niyeti netse planı gündelik + hafif yola kilitle."""
    if mode_norm not in ("genel", "uretim", "gelisim"):
        return plan
    if _explicit_research_intent(message):
        return plan
    if looks_like_casual_social_chat(message) or (
        plan.primary == "gundelik" and len((message or "").strip()) < 180
    ):
        plan.primary = "gundelik"
        plan.use_ilim_rag = False
        plan.prefer_web = False
        plan.prefer_archive = False
        plan.ambiguous = False
        plan.clarification = None
        plan.web_query = ""
        plan.rag_query = ""
        plan.status_text = _status_for_plan("gundelik", "")
    return plan


def maybe_gundelik_instant_reply(
    message: str,
    mode_norm: str,
    motor_flags: dict[str, bool] | None = None,
    question_plan: QuestionPlan | None = None,
) -> str | None:
    """B3b — net sohbet (nasılsın/selam) için Ollama/Gemini beklemeden kısa yanıt."""
    if mode_norm not in ("genel", "uretim", "gelisim"):
        return None
    try:
        from ilim_assistant.ruzgar_tek_beyin_karsilama import try_session_resume_greeting

        karsilama = try_session_resume_greeting(message)
        if karsilama:
            return karsilama
    except Exception:
        pass
    try:
        from ilim_assistant.ruzgar_dogal_sohbet_faz91 import should_skip_instant_shortcuts

        if should_skip_instant_shortcuts(message, mode_norm, question_plan=question_plan):
            return None
    except Exception:
        pass
    raw = (message or "").strip().lower()
    blob = _norm_ascii(raw) + " " + raw
    if any(
        x in blob
        for x in (
            "sohbet edelim",
            "sohbet eder",
            "konuşalım",
            "konusalim",
            "muhabbet",
        )
    ) and len((message or "").split()) <= 12:
        return (
            "Olur Ümit abi — seninle sohbet etmeyi severim. "
            "Bugün hangi konuda konuşmak istersin?"
        )
    if any(x in blob for x in ("enerjik", "çok enerjik", "cok enerjik", "harikasın", "harikasin")):
        return (
            "Teşekkür ederim Ümit abi — enerjimi seninle konuşurken topluyorum. "
            "Sen nasılsın, keyfin nasıl?"
        )
    if any(
        x in blob
        for x in (
            "nasilsin",
            "nasılsın",
            "nasilsiniz",
            "iyi misin",
            "keyfin nasil",
            "naber",
            "ne haber",
        )
    ):
        return (
            "İyiyim, teşekkür ederim — Rüzgar burada, Ümit abi için hazırım. "
            "Sen nasılsın, keyfin nasıl?"
        )
    if any(
        x in blob
        for x in (
            "selam",
            "merhaba",
            "gunaydin",
            "günaydın",
            "iyi aksam",
            "iyi akşam",
            "iyi geceler",
        )
    ):
        if _info_query_blocks_casual(message):
            return None
        if re.search(r"\b(?:ruzgar|rüzgar)\b", blob) and len((message or "").split()) >= 2:
            try:
                from ilim_assistant.ruzgar_umed_kurallari import SELAM_RUZGAR

                return SELAM_RUZGAR
            except Exception:
                return None
        try:
            from ilim_assistant.ruzgar_egitim import lookup_greeting_egitim_reply
            from ilim_assistant.ruzgar_umed_kurallari import SELAM_STANDART

            taught = lookup_greeting_egitim_reply(message)
            return taught or SELAM_STANDART
        except Exception:
            return (
                "Ümit kardeşim, seninle sohbet etmek benim için bir onur. "
                "Hangi konuda sohbet edelim?"
            )
    if any(x in blob for x in ("ben geldim", "geldim", "buradayim", "buradayım")):
        return (
            "Hoş geldin Ümit abi — Rüzgar burada, seni dinliyorum. "
            "Ne üzerinde konuşmak istersin?"
        )
    if any(x in blob for x in ("tesekkur", "teşekkür", "sagol", "sağol", "eyvallah")):
        return "Rica ederim — başka bir konuda yazman yeterli."
    # Sohbet davetleri: şablon yerine Gemini hızlı yol (çeşitli, doğal yanıtlar)

    if not _plan_enabled():
        return None
    plan = question_plan or plan_question(message, mode_norm, motor_flags)
    if plan.primary != "gundelik" or plan.use_ilim_rag:
        return None
    return None


def maybe_clarification_reply(
    message: str,
    mode_norm: str,
    motor_flags: dict[str, bool] | None = None,
) -> str | None:
    """B3 — belirsiz kısa soruda tek netleştirme (anında yanıt)."""
    if not _plan_enabled() or not _clarify_enabled():
        return None
    if mode_norm not in ("genel", "uretim", "gelisim"):
        return None
    plan = plan_question(message, mode_norm, motor_flags)
    if not plan.ambiguous or not plan.clarification:
        return None
    return plan.clarification


def rag_top_k_for_turn(
    mode_norm: str,
    plan: QuestionPlan | None,
    message: str | None = None,
) -> int:
    """C3 — mod ve plana göre RAG parça sayısı (varsayılan genel: 4)."""
    try:
        base = int(os.environ.get("RAG_TOP_K", "2"))
    except ValueError:
        base = 2
    if mode_norm == "genel":
        try:
            base = max(base, int(os.environ.get("RUZGAR_GENEL_RAG_TOP_K", "4")))
        except ValueError:
            base = max(base, 4)
    if plan is not None:
        if plan.primary == "bilim":
            try:
                base = max(base, int(os.environ.get("RUZGAR_BILIM_RAG_TOP_K", "5")))
            except ValueError:
                base = max(base, 5)
        elif plan.primary == "bilgi":
            try:
                base = max(base, int(os.environ.get("RUZGAR_BILGI_RAG_TOP_K", "4")))
            except ValueError:
                base = max(base, 4)
        elif plan.primary == "dilbilgisi":
            try:
                base = max(base, int(os.environ.get("RUZGAR_DILBILGISI_RAG_TOP_K", "3")))
            except ValueError:
                base = max(base, 3)
    try:
        from ilim_assistant.ana_motor_bilim_derin import apply_bilim_derin_rag_top_k

        base = apply_bilim_derin_rag_top_k(base, plan, message, mode_norm)
    except Exception:
        pass
    return max(1, min(base, 12))


def append_plan_directive(user_payload: str, plan: QuestionPlan, mode_norm: str) -> str:
    if not _plan_enabled() or mode_norm not in ("genel", "uretim", "gelisim"):
        return user_payload
    src = []
    if plan.prefer_archive:
        src.append("arşiv/indeks öncelikli")
    if plan.use_ilim_rag:
        src.append("yerel ilim notları")
    if plan.prefer_web:
        src.append("web tamamlayıcı")
    if not src:
        src.append("doğrudan sohbet (ağır arşiv araması yok)")
    kaynak = ", ".join(src)
    return (
        user_payload.rstrip()
        + f"\n\n[TALİMAT — ANA MOTOR PLANI — dahili]\n"
        f"Soru sınıfı: **{plan.primary}**. Bu tur kaynak önceliği: {kaynak}. "
        f"Kullanıcıya bu etiketleri yazma; yalnızca bu plana göre yanıt üret.\n"
    )
