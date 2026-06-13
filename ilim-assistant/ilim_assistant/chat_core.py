"""Gradio ve masaüstü API için ortak sohbet mantığı."""

from __future__ import annotations

import os
from typing import Any
import re
import unicodedata

from ilim_assistant.defaults import DEFAULT_OLLAMA_CHAT_MODEL
from ilim_assistant.llm_ollama import chat_completion, chat_completion_stream
from ilim_assistant.text_encoding import finalize_assistant_reply, repair_utf8_mojibake
from ilim_assistant.prompts import (
    append_direct_answer_directive,
    append_wake_instruction,
    build_user_prompt,
    pick_system,
)
from ilim_assistant.persona import WAKE_GREETING, WAKE_GREETING_CODING
from ilim_assistant.rag_store import (
    search,
    search_tarih_hafiza,
    search_tdk_exact_lemma,
    source_is_tdk,
)
from ilim_assistant.web_tools import (
    build_message_link_context,
    build_web_context,
    build_web_context_fast,
    web_fast_mode_enabled,
    refined_search_query,
)


def resolve_model(
    coding_mode: bool,
    *,
    message: str = "",
    mode_norm: str = "genel",
    question_plan: Any | None = None,
) -> str:
    try:
        from ilim_assistant.llm_brain import resolve_brain_model

        return resolve_brain_model(
            coding_mode,
            message=message,
            mode_norm=mode_norm,
            question_plan=question_plan,
        )
    except Exception:
        pass
    if coding_mode:
        return os.environ.get("OLLAMA_CHAT_MODEL_CODING") or os.environ.get(
            "OLLAMA_CHAT_MODEL", DEFAULT_OLLAMA_CHAT_MODEL
        )
    return os.environ.get("OLLAMA_CHAT_MODEL", DEFAULT_OLLAMA_CHAT_MODEL)


def ensure_messages(history: list | None) -> list:
    if history is None:
        return []
    if hasattr(history, "root"):
        try:
            history = list(history.root)
        except Exception:
            return []
    if not isinstance(history, list):
        return []
    out: list = []
    for item in history:
        if isinstance(item, dict) and "role" in item and "content" in item:
            out.append(item)
            continue
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            out.append({"role": "user", "content": str(item[0])})
            out.append({"role": "assistant", "content": str(item[1])})
            continue
        dump = getattr(item, "model_dump", None)
        if callable(dump):
            d = dump()
            if isinstance(d, dict) and "role" in d and "content" in d:
                out.append(d)
    return out


def message_calls_wake_name(message: str) -> bool:
    low = message.lower()
    return "rüzgar" in low or "ruzgar" in low


# Yerel arama + web yok: daha az GPU/CPU (masaüstü modları)
# hafiza: yalnızca ruzgar_genel_hafiza.json + LLM; tam arşiv/indeks taraması dakikalarca sürebilir.
_NO_RAG_MODES = frozenset(
    {"ses", "mimar", "okuma", "tercume", "uretim", "video", "hizli", "hafiza", "programlama"}
)
_NOWEB_MODES = frozenset(
    {"ses", "mimar", "okuma", "tercume", "uretim", "hizli", "hafiza", "programlama"}
)

# İstemciden Türkçe karakterli veya ASCII mod adı gelebilir
_MODE_ALIASES = {
    "üretim": "uretim",
    "gelişim": "gelisim",
    "düzen": "duzen",
    "hızlı": "hizli",
    "tercüme": "tercume",
    "okuma": "mimar",
    "bilim": "mimar",
}


def normalize_mode(mode: str) -> str:
    m = (mode or "genel").strip().lower()
    return _MODE_ALIASES.get(m, m)


def _rag_source_is_archive(rel: str) -> bool:
    p = (rel or "").replace("\\", "/").lower()
    return "/arsiv/" in p or p.startswith("arsiv/")


def _tarih_intent(msg: str) -> bool:
    """
    Tarih / medeniyet soruları — önce TARIH_VE_KULTUR vektör hafızası taranır.
    Kapatmak: RUZGAR_TARIH_INTENT=0
    """
    if os.environ.get("RUZGAR_TARIH_INTENT", "1").strip().lower() in ("0", "false", "no"):
        return False
    raw = (msg or "").strip()
    if len(raw) < 6:
        return False
    if _is_live_weather_query(raw):
        return False
    low = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii").lower()
    low_tr = raw.lower()
    blob = low_tr + " " + low
    needles = (
        "lale devri",
        "gokturk",
        "göktürk",
        "osmanli",
        "osmanlı",
        "selcuklu",
        "selçuklu",
        "turk tarih kurumu",
        "türk tarih kurumu",
        " turk tarih",
        " turk tarih kurumu",
        "ottoman",
        "padisah",
        "padişah",
        "hanedan",
        " malazgirt",
        "manzikert",
        "kurtulus savasi",
        "kurtuluş savaşı",
        "bizans",
        "fatih sultan",
        "fethett",
        "fethi",
        "istanbul",
        "konstantinopolis",
        "4. murat",
        "dorduncu murat",
        "murat ",
        "kanuni sultan",
        "yavuz sultan",
        "orhun",
        "bilge kag",
        "bumin kag",
        "buyuk turk tarihi",
        "büyük türk tarihi",
        "mezopotamya",
        "anadolu selcuk",
        "anzak",
        "canakkale savas",
        "çanakkale savaş",
        "tanzimat",
        "ilk turk ",
        "ilk türk ",
        "gokturkler",
        "göktürkler",
        " osmanli imparator",
        " osmanlı imparator",
        " saltanat",
        " cumhuriyet ilan",
        " cumhuriyet'in ilan",
    )
    if any(n in blob for n in needles):
        return True
    if any(x in blob for x in (" ttk ", " ttk,", " (ttk", "[ttk", "ttk ", "ttk'n")):
        return True
    if "tarih" in blob or "tarihi" in blob:
        hints = (
            "nedir",
            "kim",
            "ne zaman",
            "hangi",
            "nasil",
            "nasıl",
            "donem",
            "dönem",
            "devir",
            "olayi",
            "olayı",
            " savas",
            " savaş",
            " imparator",
            "beylik",
            "yonetimi",
            "yönetimi",
            "hanedan",
            "padişah",
            "padisah",
            "sultan",
        )
        if any(h in blob for h in hints):
            return True
    return False


_FILL_TDK_Q = frozenset(
    {
        "nedir",
        "ne",
        "demek",
        "demektir",
        "dir",
        "dır",
        "dur",
        "tur",
        "tir",
        "tır",
        "mi",
        "mı",
        "mu",
        "mü",
        "midir",
        "mıdır",
        "mudur",
        "müdür",
        "anlamı",
        "anlamıdır",
        "anlamını",
        "tanımı",
        "tanımını",
        "kelimesi",
        "kelimesinin",
        "kelime",
        "için",
        "tdk",
        "gts",
        "sözlük",
        "sözlükte",
        "güncel",
        "türkçe",
        "turkce",
        "olduğu",
        "oldugu",
        "olan",
        "hakkında",
        "hakkinda",
        "kısaca",
        "kisaca",
    }
)


def _ascii_fold_lower(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()


def _extract_lemma_for_tdk(msg: str) -> str | None:
    """Sözlük sorusundan madde metnini çıkarır (TDK `##` başlığı ile tam eşleşecek biçimde)."""
    raw = (msg or "").strip().strip(' "\'«»“”‘’').strip()
    if not raw or len(raw) > 120:
        return None
    parts = re.split(r"\s+", raw)
    tokens: list[str] = []
    for p in parts:
        t = p.strip(".,;:?!\"'«»()[]{}…")
        if t:
            tokens.append(t)
    if not tokens:
        return None
    fold = [_ascii_fold_lower(x) for x in tokens]
    while fold and fold[-1] in _FILL_TDK_Q:
        fold.pop()
        tokens.pop()
    while fold and fold[0] in _FILL_TDK_Q:
        fold.pop(0)
        tokens.pop(0)
    if not tokens:
        return None
    if len(tokens) > 4:
        return None
    core = " ".join(tokens)
    if len(core.replace(" ", "")) < 2:
        return None
    return core


def _tdk_exact_path_allowed(msg: str, lemma: str | None) -> bool:
    """Kısa / sözlük nitelikli sorularda vektör 'hayalet' eşlemesine düşmeden yalnızca tam madde aranır."""
    if not lemma:
        return False
    low = (msg or "").lower()
    hints = (
        "nedir",
        "ne demek",
        "anlamı",
        "tanımı",
        "kelimesi",
        " tdk",
        "tdk ",
        "sözlük",
        "gts ",
        " gts",
    )
    if any(h in low for h in hints):
        return True
    if len(lemma.split()) <= 3 and len((msg or "").strip()) <= 52:
        return True
    return False


def _archive_hits_strong(ar_hits: list) -> bool:
    if not ar_hits:
        return False
    try:
        best = float(ar_hits[0][2])
        th = float(os.environ.get("RUZGAR_ARCHIVE_SCORE_MIN", "0.22"))
        return best >= th
    except (TypeError, ValueError, IndexError):
        return False


def try_archive_rag_direct_reply(
    message: str,
    ar_hits: list,
    *,
    coding_mode: bool,
    mode_norm: str,
) -> str | None:
    """
    Güçlü arşiv (RAG) eşleşmesinde LLM beklemeden doğrudan pasaj döndürür.
    Kapatmak: ENABLE_RAG_ARCHIVE_FAST=0
    """
    if os.environ.get("ENABLE_RAG_ARCHIVE_FAST", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return None
    if coding_mode or mode_norm in _NO_RAG_MODES:
        return None
    if _is_wake_only_message(message):
        return None
    if not ar_hits or not _archive_hits_strong(ar_hits):
        return None
    try:
        max_n = max(1, int(os.environ.get("RUZGAR_ARCHIVE_FAST_MAX_CHUNKS", "3")))
    except ValueError:
        max_n = 3
    try:
        cap = max(400, int(os.environ.get("RUZGAR_ARCHIVE_FAST_MAX_CHARS", "2200")))
    except ValueError:
        cap = 2200

    lines: list[str] = [
        "**İlim Hazinesi (yerel arşiv)** ile sorunuzla eşleşen doğrudan pasajlar:",
        "",
    ]
    for text, src, sc in ar_hits[:max_n]:
        excerpt = (text or "").strip()
        if len(excerpt) > cap:
            excerpt = excerpt[:cap].rsplit(maxsplit=1)[0].rstrip() + " …"
        short_src = (
            src.replace("\\", "/").split("/")[-1].strip()
            if src
            else "kaynak"
        )
        try:
            sc_f = float(sc)
        except (TypeError, ValueError):
            sc_f = 0.0
        lines.append(f"**{short_src}** _(uyum ~{sc_f:.2f})_")
        lines.append(excerpt)
        lines.append("")
    lines.append("*Metinler yerel arşiv dizinine göre otomatik seçilmiştir.*")
    return "\n".join(lines).strip()


def _main_chat_genel_only() -> bool:
    """True ise `genel` modda yalnızca `ruzgar_genel_hafiza.json`; eşleşmezse LLM/RAG/web yok.

    Varsayılan **tam güç**: kapalı. Yalnızca ortamda açıkça `RUZGAR_MAIN_ONLY_GENEL_HAFIZA=1`
    (veya `true` / `yes` / `on`) ise açılır. Boş, tanınmayan veya `0` değerleri tam güç sayılır.
    """
    raw = (os.environ.get("RUZGAR_MAIN_ONLY_GENEL_HAFIZA") or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def _genel_only_unknown_reply() -> str:
    raw = (os.environ.get("RUZGAR_GENEL_ONLY_MISS_REPLY") or "").strip()
    if raw:
        return raw
    try:
        from ilim_assistant.hafiza_i_ruzgar import HafizaIRuzgar

        return HafizaIRuzgar.BILINMEYEN_YANIT
    except Exception:
        return "Mimar, bunu henüz öğrenmedim, bana öğretir misin?"


def _looks_like_genel_hafiza_miss_reply(ans: str) -> bool:
    """Fuzzy eşleşmeyle gelen '… öğrenmedim …' yer tutucularını anında cevap sayma."""
    if not ans or not str(ans).strip():
        return False
    a = unicodedata.normalize("NFKC", str(ans).strip()).lower()
    if "öğrenmedim" not in a and "ogrenmedim" not in a:
        return False
    return "mimar" in a or "öğretir" in a or "ogretir" in a


def try_genel_hafiza_reply(message: str, mode: str) -> str | None:
    """
    Ana motor için `ruzgar_genel_hafiza.json` merkezi sözlüğü.
    Eşleşmede (tam / norm / fuzzy) RAG, web ve LLM çalışmaz.

    `RUZGAR_HAFIZA_DOGAL_KONUS=1` (varsayılan) iken ham cevap döndürülmez;
    doğal sentez için `hafiza_dogal_sentez` kullanılır.

    «Bilinmeyen» yer tutucu cevap JSON’da yanlışlıkla eşleşirse — LLM’e düşsün diye
    **anında cevap sayılmaz** (None döner).

    Anında JSON kısayolunu tamamen kapatmak: `ENABLE_RUZGAR_GENEL_HAFIZA=0`
    (veya `ENABLE_OGRENME_MERKEZI=0`).
    """
    try:
        from ilim_assistant.hafiza_dogal_sentez import dogal_konus_enabled

        if dogal_konus_enabled():
            return None
    except Exception:
        pass
    del mode  # öncelik tüm ana sohbet modlarında geçerlidir
    if os.environ.get("ENABLE_RUZGAR_GENEL_HAFIZA", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return None
    if os.environ.get("ENABLE_OGRENME_MERKEZI", "1").strip().lower() in (
        "0",
        "false",
        "no",
    ):
        return None
    msg = (message or "").strip()
    if not msg or len(msg) > 4000:
        return None
    try:
        from ilim_assistant.hafiza_i_ruzgar import HafizaIRuzgar, genel_hafiza_lookup

        ans = genel_hafiza_lookup(msg)
        if ans is None:
            return None
        if (ans or "").strip() == HafizaIRuzgar.BILINMEYEN_YANIT.strip():
            return None
        if _looks_like_genel_hafiza_miss_reply(ans):
            return None
        return ans
    except Exception:
        return None


def _is_wake_only_message(msg: str) -> bool:
    """Yalnızca isim seslenmesi — web araması gereksiz gecikme yaratmasın."""
    t = (msg or "").strip().lower().strip(".,!?…").strip()
    return t in ("rüzgar", "ruzgar")


def _weather_intent(msg: str) -> bool:
    """Anahtar kelime + isteğe bağlı NB sınıflandırıcı — hava niyeti.

    ÖNEMLİ:
    - Varsayılan artık **yalnızca anahtar kelime temelli** (\"hava\", \"yağmur\", \"kaç derece\" vb.).
    - `intent_router.predict_intent` sadece ortamda açıkça `WEATHER_NB_INTENT=1`
      ise devreye girer. Böylece tarih/siyasi soru gibi metinler yanlışlıkla
      \"weather\" sınıfına düşüp canlı hava motorunu tetiklemez.
    """
    if _is_live_weather_query(msg):
        return True

    raw = (os.environ.get("WEATHER_NB_INTENT") or "").strip().lower()
    if raw not in ("1", "true", "yes", "on"):
        return False
    try:
        from ilim_assistant.intent_router import predict_intent

        return predict_intent(msg) == "weather"
    except Exception:
        return False


def _is_live_weather_query(msg: str) -> bool:
    """
    Güncel hava / anlık durum — yerel RAG (gramer, tecvid md) çekildiğinde model saçma üretir.
    Bu durumda RAG kapatılır; web özetine güvenilir (veya kısa dürüst yanıt).
    """
    low = (msg or "").lower()
    needles = (
        "hava nasıl",
        "hava nasil",
        "hava ne olacak",
        "hava olacak",
        "bugün hava",
        "bugun hava",
        "hava durumu",
        "hava bugün",
        "hava yarın",
        # Cümle sırası değiştiğinde de yakala: "yarın hava nasıl"
        "yarın hava nasıl",
        "yarın hava durumu",
        "yarın hava",
        "havalar nasıl",
        "hava durumuna bak",
        "hava durumu bak",
        "kaç derece",
        "derece mi",
        "yağmur var",
        "yağacak",
        "kar yağıyor",
        "kar var",
        "şemsiye",
        "meteoroloji",
        "sıcaklık",
        "soğuk mu",
        "sıcak mı",
        "rüzgar esiyor",
        "ruzgar esiyor",
    )
    if any(n in low for n in needles):
        return True
    # Çok kısa günlük sorular (RAG gramer metnine düşmesin)
    s = low.strip().strip("?!.")
    if s in ("hava", "hava bugün", "hava şimdi"):
        return True
    return False


def _weather_instant_allowed(msg: str, *, coding_mode: bool) -> bool:
    """Uzun / kod / URL içeren mesajlarda anlık hava şablonunu devre dışı bırak."""
    if coding_mode:
        return False
    try:
        cap = int(os.environ.get("RUZGAR_WEATHER_INSTANT_MAX_CHARS", "360"))
    except ValueError:
        cap = 360
    t = (msg or "").strip()
    if len(t) > cap:
        return False
    low = t.lower()
    if "http://" in low or "https://" in low or "```" in t:
        return False
    try:
        from ilim_assistant.weather_live import _norm_match

        n = _norm_match(t)
    except Exception:
        n = low
    if any(k in n for k in ("def ", "class ", "import ", "fonksiyon ", "kod yaz")):
        return False
    return True


def _weather_follow_up(msg: str, history: list | None) -> bool:
    """
    Önceki tur(lar)da hava konuşulduysa kısa devam cümlelerini hava bağlamında tut.
    ("benim için sen bakıp bilgi ver" gibi — anahtar kelime içermese de.)
    """
    if os.environ.get("WEATHER_FOLLOW_UP", "1").strip() in ("0", "false", "no"):
        return False
    t = (msg or "").strip()
    if len(t) > 220:
        return False
    low = t.lower()
    hints = (
        "benim için",
        "sen bak",
        "bakıp",
        "bilgi ver",
        "bana söyle",
        "bana anlat",
        "anlatır mısın",
        "söyler misin",
        "öğren",
        "neden demedin",
        "niye demedin",
        "peki ",
        "peki?",
        "tamam da",
    )
    if not any(h in low for h in hints):
        return False
    msgs = ensure_messages(history or [])
    if len(msgs) < 2:
        return False
    blob = " ".join((m.get("content") or "").lower() for m in msgs[-12:])
    markers = (
        "hava",
        "derece",
        "yağmur",
        "sıcak",
        "soğuk",
        "meteoroloji",
        "şemsiye",
        "bulut",
        "rüzgar esiyor",
        "hava durumu",
    )
    return any(x in blob for x in markers)


# Hızlı modlar: kısa bağlam = daha az token, daha hızlı üretim
_HISTORY_FAST_MODES = frozenset({"hizli", "ses", "okuma", "tercume", "uretim", "video"})


def _history_msg_cap(mode: str) -> int:
    m = normalize_mode(mode)
    if m == "programlama":
        return max(2, int(os.environ.get("CHAT_HISTORY_MSGS_CODE", "24")))
    if m in _HISTORY_FAST_MODES:
        return max(2, int(os.environ.get("CHAT_HISTORY_MSGS_FAST", "14")))
    return max(2, int(os.environ.get("CHAT_HISTORY_MSGS", "22")))


def _history_char_cap(mode: str) -> int:
    m = normalize_mode(mode)
    if m == "programlama":
        return max(1000, int(os.environ.get("CHAT_HISTORY_CHARS_CODE", "48000")))
    if m in _HISTORY_FAST_MODES:
        return max(1000, int(os.environ.get("CHAT_HISTORY_CHARS_FAST", "12000")))
    return max(1000, int(os.environ.get("CHAT_HISTORY_CHARS", "20000")))


def trim_chat_tail(
    messages: list,
    *,
    max_messages: int,
    max_total_chars: int | None,
) -> list:
    """Ollama bağlamını küçük tutar (hız + VRAM)."""
    if not messages:
        return []
    h = list(messages)
    if len(h) > max_messages:
        h = h[-max_messages:]
    if max_total_chars and max_total_chars > 0:
        total = sum(len(str(x.get("content", ""))) for x in h)
        while len(h) > 2 and total > max_total_chars:
            total -= len(str(h[0].get("content", "")))
            h = h[1:]
    return h


def prior_messages_for_turn(
    history: list,
    mode: str,
    *,
    message: str = "",
    question_plan: Any | None = None,
) -> list:
    """Sohbet geçmişini moda göre kırpar (masaüstü API + Gradio)."""
    try:
        from ilim_assistant.ruzgar_tek_beyin_izolasyon import (
            prior_messages_for_turn_isolated,
            tek_beyin_izolasyon_enabled,
        )

        if tek_beyin_izolasyon_enabled():
            return prior_messages_for_turn_isolated(
                history,
                mode,
                message=message,
                question_plan=question_plan,
            )
    except Exception:
        pass
    try:
        from ilim_assistant.ruzgar_tek_beyin_izolasyon import sanitize_paired_messages

        cleaned = sanitize_paired_messages(history)
    except Exception:
        cleaned = ensure_messages(history)
    return trim_chat_tail(
        cleaned,
        max_messages=_history_msg_cap(mode),
        max_total_chars=_history_char_cap(mode),
    )


def _last_assistant_text(history: list | None) -> str | None:
    for m in reversed(ensure_messages(history or [])):
        if m.get("role") == "assistant":
            t = (m.get("content") or "").strip()
            if t:
                return t
    return None


def _is_mostly_wake_greeting(text: str) -> bool:
    """Önceki tur yalnızca (veya neredeyse yalnızca) sabit karşılamaysa tekrar döngüsünü beslememek için."""
    t = repair_utf8_mojibake((text or "").strip())
    if "*(" in t:
        t = t.split("*(")[0].strip()
    t = t.strip()
    if len(t) > 400:
        return False
    low = t.lower()
    for g in (WAKE_GREETING, WAKE_GREETING_CODING):
        if t == g or t.startswith(g + "\n") or t.startswith(g + " "):
            return True
        gl = g.lower()
        if len(t) <= len(g) + 40 and gl in low and ("yard" in low or "yardim" in low or "yardım" in low):
            return True
    # Mojibake / kısa model çıktıları: sadece hitap cümlesi
    if len(t) < 220 and "efendim" in low and "abi" in low and (
        "yard" in low or "yardım" in low or "nasıl" in low or "nasÄ±l" in low
    ):
        return True
    return False


def _append_anti_repeat_instruction(user_payload: str, history: list | None) -> str:
    """Aynı cevabı ardışık turlarda tekrar etmesini model seviyesinde zorlaştırır."""
    if os.environ.get("ANTI_REPEAT_INSTRUCTION", "1").strip() in ("0", "false", "no"):
        return user_payload
    last = _last_assistant_text(history)
    if not last:
        return user_payload
    last = repair_utf8_mojibake(last)
    cap = max(200, int(os.environ.get("ANTI_REPEAT_MAX_CHARS", "1500")))
    if _is_mostly_wake_greeting(last):
        ref = (
            "(Önceki turda yalnızca kısa karşılama vardı — "
            "onu veya benzeri sabit cümleyi ASLA tekrarlama; şimdi yalnızca kullanıcının son mesajına yanıt ver.)"
        )
    else:
        ref = last[:cap]
        if len(last) > cap:
            ref += "\n[…devamı atıldı…]"
    return (
        user_payload
        + "\n\n[TALİMAT — TEKRAR ETME]\n"
        + "Bir önceki asistan yanıtını aynen veya aynı düzende YENİDEN YAZMA. "
        "Yalnızca bu SORU satırındaki isteğe göre yeni cevap ver.\n"
        + "Referans (kopyalama değil, tekrar etme):\n---\n"
        + ref
        + "\n---\n"
    )


def _web_secondary_policy_enabled() -> bool:
    default = "1"
    try:
        from ilim_assistant.ruzgar_web_arastirma_pro import web_arastirma_pro_enabled

        if web_arastirma_pro_enabled():
            default = "0"
    except Exception:
        pass
    return os.environ.get("RUZGAR_WEB_SECONDARY_ONLY_ON_EMPTY", default).strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _web_suppress_rag_score_floor() -> float:
    try:
        return float(os.environ.get("RUZGAR_WEB_SUPPRESS_RAG_MIN", "0.38"))
    except ValueError:
        return 0.38


def local_rag_strong_enough_to_skip_web(
    hits: list,
    ar_hits: list,
    *,
    archive_primary: bool,
) -> bool:
    """Zayıf vektör eşleşmesi web aramasını kapatmasın (Ana Motor A1)."""
    if archive_primary:
        return True
    if ar_hits:
        try:
            from ilim_assistant.main_engine import archive_match_is_strong

            if archive_match_is_strong(ar_hits):
                return True
        except Exception:
            pass
    if not hits:
        return False
    try:
        best = max(float(h[2]) for h in hits)
    except (TypeError, ValueError, IndexError):
        return False
    return best >= _web_suppress_rag_score_floor()


def _genel_no_context_directive() -> str:
    try:
        from ilim_assistant.ruzgar_dogal_sohbet_faz91 import dogal_sohbet_enabled

        if dogal_sohbet_enabled():
            return (
                "\n\n[TALİMAT — GENEL SOHBET]\n"
                "Bu turda yerel arşiv/indeks veya web özeti taşınmadı. "
                "Ümit abi ile **doğal sohbet** et: akıcı paragraf, şablon karşılama yok. "
                "Soruya göre uzunluk esnek; bilmediğin özel güncel olayı uydurma.\n"
            )
    except Exception:
        pass
    return (
        "\n\n[TALİMAT — GENEL SOHBET]\n"
        "Bu turda yerel arşiv/indeks veya web özeti taşınmadı veya yetersiz kaldı. "
        "Ümit abi'nin sorusunu doğrudan yanıtla: genel bilgin ve mantığınla, kısa ve net Türkçe. "
        "Bilmediğin özel güncel olayı uydurma; kesin kaynak göremedim diyebilirsin. "
        "Nahiv/tecvid dersi gibi çözümleme yapma; günlük sohbet tonunda kal.\n"
    )


def _orkestra_context_for_turn(mode_norm: str, motor_flags: dict[str, bool]) -> bool:
    if os.environ.get("RUZGAR_ORKESTRA_CONTEXT", "1").strip().lower() in ("0", "false", "no"):
        return False
    # Programlama atölyesi: yalnızca programlama motoru bağlamı (ağır çekirdek orkestra yok).
    if mode_norm == "programlama":
        return False
    if mode_norm != "genel":
        return True
    if os.environ.get("RUZGAR_ORKESTRA_CONTEXT_GENEL", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return True
    return any(
        motor_flags.get(k)
        for k in ("ses", "video", "programlama", "tercume", "bilim", "bellek", "hizir")
    )


def _hizir_op_context_for_turn(mode_norm: str, motor_flags: dict[str, bool]) -> bool:
    if mode_norm == "hizir":
        return True
    return bool(motor_flags.get("hizir"))


def empty_reply_fallback(message: str = "", history: list | None = None) -> str:
    """LLM/stream boş döndüğünde kullanıcıya görünür yedek."""
    try:
        from ilim_assistant.ruzgar_tek_beyin_karsilama import (
            looks_like_greeting_complaint,
            looks_like_session_greeting,
            try_session_resume_greeting,
        )

        if looks_like_session_greeting(message) or looks_like_greeting_complaint(message):
            alt = try_session_resume_greeting(message, client_history=history)
            if alt:
                return alt
    except Exception:
        pass
    q = (message or "").strip()
    if len(q) > 80:
        q = q[:77].rstrip() + "…"
    hint = f" («{q}»)" if q else ""
    return (
        "Ümit abi, yanıt üretilirken kesinti oldu"
        f"{hint} — lütfen bir kez daha yaz veya DURDUR sonrası tekrar dene. "
        "(Ollama/Gemini bağlantısı veya süre sınırı olabilir.)"
    )


def prepare_turn(
    message: str,
    history: list,
    use_web: bool,
    fetch_pages: float,
    coding_mode: bool,
    session_wake_used: bool,
    mode: str = "genel",
    workspace_root: str | None = None,
    read_message_links: bool = True,
    *,
    skip_ogrenme_lookup: bool = False,
    reuse_main_engine_bundle: Any | None = None,
    orchestration_out: dict[str, Any] | None = None,
    question_plan: Any | None = None,
    agent_context: str | None = None,
    pazar_kanallari: list[str] | None = None,
    conversation_context: str | None = None,
    user_message_raw: str | None = None,
    cinema_context: dict[str, Any] | None = None,
    ana_motor_upload_ids: list[str] | None = None,
    ana_motor_session_id: str | None = None,
):
    """Boş mesajda None; aksi halde (msg, hits, user_payload, system, model, ogrenme_direct).

    Öncelik:
      - `RUZGAR_HAFIZA_DOGAL_KONUS=1`: hafıza isabeti → LLM sentez (ham JSON yok).
      - `RUZGAR_HAFIZA_DOGAL_KONUS=0`: eski davranış — eşleşirse anında ham cevap.
      - `genel` mod + `RUZGAR_MAIN_ONLY_GENEL_HAFIZA=1` ise ve eşleşme yoksa:
        yalnızca `_genel_only_unknown_reply` (RAG/web/LLM kapalı).
      - Varsayılan tam güç (`RUZGAR_MAIN_ONLY_GENEL_HAFIZA` yok veya `0`): eşleşme yoksa
        arşiv doğrudan / RAG + web + LLM.

    Streaming `skip_ogrenme_lookup=True`: (1) atlanır (istemci ön kontrol yaptıysa).
    """
    if not message or not message.strip():
        return None
    msg = message.strip()
    from ilim_assistant.idrak_on_islem import pretreat_user_turn

    msg = pretreat_user_turn(msg, history).text
    try:
        from ilim_assistant.kullanici_baglami import ingest_message

        ingest_message(msg)
    except Exception:
        pass
    m = normalize_mode(mode)
    if coding_mode and m not in _NO_RAG_MODES:
        m = "programlama"

    try:
        from ilim_assistant.ruzgar_owner_lock import maybe_owner_instant_reply

        owner_hi = maybe_owner_instant_reply(msg, m)
        if owner_hi and m != "programlama":
            return msg, [], "", "", "", owner_hi
    except Exception:
        pass

    if m == "programlama":
        try:
            from ilim_assistant.motorlar.programlama_motoru import (
                maybe_programlama_instant_reply,
            )

            prog_hi = maybe_programlama_instant_reply(
                msg, m, workspace_root=workspace_root
            )
            if prog_hi:
                from ilim_assistant.motorlar.programlama_motoru import (
                    unpack_programlama_instant,
                )

                text, _meta = unpack_programlama_instant(prog_hi)
                if text:
                    return msg, [], "", "", "", text
        except Exception:
            pass
    if m == "video":
        try:
            from ilim_assistant.motorlar.video_faz71 import maybe_instant_faz71

            video_hit = maybe_instant_faz71(msg)
            if video_hit:
                return msg, [], "", "", "", video_hit
        except Exception:
            pass
    if m == "ses":
        try:
            from ilim_assistant.motorlar.ses_faz72 import maybe_instant_faz72

            ses_hit = maybe_instant_faz72(msg)
            if ses_hit:
                return msg, [], "", "", "", ses_hit
        except Exception:
            pass
    if m == "mimar":
        try:
            from ilim_assistant.motorlar.mimar_faz5 import maybe_instant_faz5

            mimar_hit = maybe_instant_faz5(msg)
            if mimar_hit:
                return msg, [], "", "", "", mimar_hit
            from ilim_assistant.motorlar.okuma_faz73 import maybe_instant_faz73

            arsiv_hit = maybe_instant_faz73(msg)
            if arsiv_hit:
                return msg, [], "", "", "", arsiv_hit
        except Exception:
            pass
    if m == "okuma":
        try:
            from ilim_assistant.motorlar.okuma_faz73 import maybe_instant_faz73

            okuma_hit = maybe_instant_faz73(msg)
            if okuma_hit:
                return msg, [], "", "", "", okuma_hit
        except Exception:
            pass
    if m == "tercume":
        try:
            from ilim_assistant.motorlar.tercume_faz74 import maybe_instant_faz74

            tercume_hit = maybe_instant_faz74(msg)
            if tercume_hit:
                return msg, [], "", "", "", tercume_hit
        except Exception:
            pass
    if m == "hafiza":
        try:
            from ilim_assistant.motorlar.hafiza_faz75 import maybe_instant_faz75

            hafiza_hit = maybe_instant_faz75(msg, allow_lookup=False)
            if hafiza_hit:
                return msg, [], "", "", "", hafiza_hit
        except Exception:
            pass
    if m == "hizir":
        try:
            from ilim_assistant.motorlar.hizir_faz84 import maybe_instant_faz84

            hizir_hit = maybe_instant_faz84(msg, mode_norm="hizir")
            if hizir_hit:
                return msg, [], "", "", "", hizir_hit
        except Exception:
            pass

    from ilim_assistant.idrak_entegrasyon import motor_niyeti_heuristic

    motor_flags = motor_niyeti_heuristic(msg)
    _hub_directive = ""
    _hub_meta: dict[str, Any] = {}

    if m in ("genel", "uretim", "gelisim") and not coding_mode:
        try:
            from ilim_assistant.ana_motor_sohbet_gecmis import try_past_conversation_reply

            past_reply = try_past_conversation_reply(msg, client_history=history)
            if past_reply:
                return msg, [], "", "", "", past_reply
        except Exception:
            pass

    if m == "genel" and not coding_mode:
        try:
            from ilim_assistant.motorlar.ana_motor_hub_faz76 import apply_genel_hub_routing

            hub = apply_genel_hub_routing(
                msg,
                motor_flags=motor_flags,
                workspace_root=workspace_root,
            )
            if hub.get("og_direct"):
                if orchestration_out is not None:
                    _hm = dict(hub.get("hub_meta") or {})
                    orchestration_out["hub_delegate"] = _hm
                    _ht = str(_hm.get("target") or "").strip()
                    if _ht:
                        orchestration_out["hub_target"] = _ht
                return msg, [], "", "", "", str(hub["og_direct"])
            if hub.get("mode") and str(hub["mode"]) != "genel":
                m = str(hub["mode"])
                _hub_directive = str(hub.get("hub_directive") or "")
                _hub_meta = dict(hub.get("hub_meta") or {})
                if orchestration_out is not None:
                    orchestration_out["hub_delegate"] = _hub_meta
                    orchestration_out["hub_target"] = m
        except Exception:
            pass

    if m != "programlama" and not coding_mode:
        try:
            from ilim_assistant.motorlar.programlama_faz10 import should_delegate_to_programlama

            if should_delegate_to_programlama(
                msg, m, coding_mode=coding_mode, motor_flags=motor_flags
            ):
                m = "programlama"
        except Exception:
            pass
    turn_plan = question_plan
    try:
        from ilim_assistant.ana_motor_plan import (
            _plan_enabled,
            append_plan_directive,
            maybe_clarification_reply,
            plan_question,
        )

        if turn_plan is None and _plan_enabled():
            turn_plan = plan_question(msg, m, motor_flags)
        if orchestration_out is not None and turn_plan is not None:
            orchestration_out.setdefault("plan", turn_plan.to_dict())
    except Exception:
        turn_plan = question_plan
        append_plan_directive = None  # type: ignore[misc, assignment]
        maybe_clarification_reply = None  # type: ignore[misc, assignment]

    _bilgi_isolated = False
    try:
        from ilim_assistant.ruzgar_tek_beyin_izolasyon import (
            looks_like_bilgi_isolation_turn,
            tek_beyin_izolasyon_enabled,
        )

        _bilgi_isolated = tek_beyin_izolasyon_enabled() and looks_like_bilgi_isolation_turn(
            msg, turn_plan
        )
    except Exception:
        _bilgi_isolated = False

    ilim_merge_tail = ""
    me_suppress_web = False
    archive_primary_flag = False

    weather_q = _weather_intent(msg) or _weather_follow_up(msg, history)
    live_weather_ctx = ""
    weather_instant: str | None = None
    if weather_q and os.environ.get("ENABLE_LIVE_WEATHER", "1").strip() not in (
        "0",
        "false",
        "no",
    ):
        try:
            from ilim_assistant.weather_live import compute_live_weather_outcome

            live_weather_ctx, weather_instant = compute_live_weather_outcome(msg)
        except Exception:
            live_weather_ctx = ""
            weather_instant = None

    # Canlı hava anında yanıtı — `ruzgar_genel_hafiza.json` taramasından ÖNCE (büyük dosyada gecikme yok).
    if (
        os.environ.get("RUZGAR_WEATHER_BEFORE_JSON", "1").strip()
        not in ("0", "false", "no")
        and weather_q
        and weather_instant
        and _weather_instant_allowed(msg, coding_mode=coding_mode)
        and os.environ.get("RUZGAR_WEATHER_INSTANT_REPLY", "1").strip()
        not in ("0", "false", "no")
    ):
        return msg, [], "", "", "", weather_instant

    _gundelik_fast = (
        turn_plan is not None
        and m in ("genel", "uretim", "gelisim")
        and getattr(turn_plan, "primary", "") == "gundelik"
        and not bool(getattr(turn_plan, "use_ilim_rag", True))
    )

    if maybe_clarification_reply is not None and not _gundelik_fast:
        clar = maybe_clarification_reply(msg, m, motor_flags)
        if clar:
            return msg, [], "", "", "", clar

    try:
        from ilim_assistant.ana_motor_plan import maybe_gundelik_instant_reply

        gundelik_direct = maybe_gundelik_instant_reply(
            msg, m, motor_flags, question_plan=turn_plan
        )
        if gundelik_direct:
            return msg, [], "", "", "", gundelik_direct
    except Exception:
        pass

    if not skip_ogrenme_lookup:
        try:
            from ilim_assistant.ana_motor_plan import looks_like_casual_social_chat

            if looks_like_casual_social_chat(msg):
                skip_ogrenme_lookup = True
        except Exception:
            pass
    if turn_plan is not None and getattr(turn_plan, "primary", "") == "gundelik":
        if not bool(getattr(turn_plan, "use_ilim_rag", True)):
            skip_ogrenme_lookup = True
    hafiza_hint = None
    if not skip_ogrenme_lookup:
        try:
            from ilim_assistant.hafiza_dogal_sentez import (
                dogal_konus_enabled,
                lookup_genel_hafiza_hint,
            )

            if dogal_konus_enabled():
                hafiza_hint = lookup_genel_hafiza_hint(msg)
                if orchestration_out is not None and hafiza_hint:
                    orchestration_out["hafiza_hint"] = hafiza_hint
            else:
                og_direct = try_genel_hafiza_reply(msg, m)
                if og_direct is not None:
                    return msg, [], "", "", "", og_direct
        except Exception:
            og_direct = try_genel_hafiza_reply(msg, m)
            if og_direct is not None:
                return msg, [], "", "", "", og_direct
        if _main_chat_genel_only() and m == "genel" and not hafiza_hint:
            return msg, [], "", "", "", _genel_only_unknown_reply()

    if maybe_clarification_reply is not None and _gundelik_fast:
        clar = maybe_clarification_reply(msg, m, motor_flags)
        if clar:
            return msg, [], "", "", "", clar

    if (
        os.environ.get("RUZGAR_WEATHER_BEFORE_JSON", "1").strip() in ("0", "false", "no")
        and weather_q
        and weather_instant
        and _weather_instant_allowed(msg, coding_mode=coding_mode)
        and os.environ.get("RUZGAR_WEATHER_INSTANT_REPLY", "1").strip()
        not in ("0", "false", "no")
    ):
        return msg, [], "", "", "", weather_instant

    # Lokal vektör (knowledge/*.md) araması öncelikli olsun.
    # Varsayılan: tüm mesajlarda RAG denensin; ilgili bağlam skoru alt sınırın altındaysa bağlam eklenmez.
    local_rag_always_on = os.environ.get("RUZGAR_LOCAL_RAG_ALWAYS_ON", "1").strip().lower()
    if local_rag_always_on in ("0", "false", "no"):
        try:
            from ilim_assistant.intent_router import should_use_ilim_rag

            ilim_rag = should_use_ilim_rag(msg)
        except Exception:
            ilim_rag = True
    else:
        ilim_rag = True

    if turn_plan is not None and m in ("genel", "uretim", "gelisim"):
        ilim_rag = bool(turn_plan.use_ilim_rag)

    search_msg = msg
    if turn_plan is not None:
        try:
            from ilim_assistant.ana_motor_plan import rag_search_query_for_turn

            search_msg = rag_search_query_for_turn(msg, turn_plan)
        except Exception:
            search_msg = msg

    hits: list = []
    ar_hits: list = []
    blocks: list = []
    skip_rag_for_plan = (
        turn_plan is not None
        and m in ("genel", "uretim", "gelisim")
        and not bool(getattr(turn_plan, "use_ilim_rag", True))
    )
    if skip_rag_for_plan or m in _NO_RAG_MODES or coding_mode:
        pass
    elif weather_q:
        # gramer/tecvid md'leri "hava" ile yanlış eşleşir; model dilbilgisi uydurur
        pass
    else:
        try:
            from ilim_assistant.ana_motor_plan import rag_top_k_for_turn

            rag_k_clamped = rag_top_k_for_turn(m, turn_plan, message=msg)
        except Exception:
            rag_k = int(os.environ.get("RAG_TOP_K", "2"))
            rag_k_clamped = max(1, min(rag_k, 12))
        pool_k = min(max(rag_k_clamped * 3, 10), 28)
        rag_score_min = float(os.environ.get("RAG_SCORE_MIN", "0.20"))
        tarih_on = _tarih_intent(msg)
        use_tarih_rag_branch = tarih_on
        try:
            from ilim_assistant.tarih_fast import should_defer_tarih_fast_to_ana_motor

            if use_tarih_rag_branch and should_defer_tarih_fast_to_ana_motor(
                msg, question_plan=turn_plan, mode_norm=m
            ):
                use_tarih_rag_branch = False
        except Exception:
            pass
        try:
            from ilim_assistant.ana_motor_plan import looks_like_encyclopedic_fact_question

            encyc_fast = looks_like_encyclopedic_fact_question(msg)
        except Exception:
            encyc_fast = False
        tarih_light = encyc_fast and os.environ.get(
            "RUZGAR_FAZ9_CHAT_CORE_TARIH_LIGHT", "1"
        ).strip().lower() not in ("0", "false", "no")
        tdk_lem: str | None = None
        tdk_exact_on = False
        if (
            not tarih_on
            and os.environ.get("RUZGAR_TDK_EXACT_LEMMA", "1").strip().lower()
            not in ("0", "false", "no")
        ):
            tdk_lem = _extract_lemma_for_tdk(msg)
            tdk_exact_on = _tdk_exact_path_allowed(msg, tdk_lem)

        _bundle_in = reuse_main_engine_bundle
        # Tarih niyeti: prefetch bundle'ı yok sayıp ikinci ağır tarama yapılıyordu (Faz 9 gecikme).
        # Ansiklopedik «kim kurdu» vb. soruda Ana Motor önbelleğini koru.
        if _bundle_in is not None and (
            (tdk_exact_on and tdk_lem) or (use_tarih_rag_branch and not tarih_light)
        ):
            _bundle_in = None

        good_hits: list = []

        if _bundle_in is not None:
            bh = list(_bundle_in.hits)
            good_hits = [h for h in bh if float(h[2]) >= rag_score_min]
            if not good_hits and bh:
                good_hits = bh[:rag_k_clamped]
            ilim_merge_tail = (_bundle_in.ilim_citation_tail or "").strip()
            me_suppress_web = bool(_bundle_in.suppress_main_web_search)
            archive_primary_flag = bool(_bundle_in.archive_was_primary)
        elif tdk_exact_on and tdk_lem:
            # TDK: yalnızca `##` başlığı tam eşleşmesi — semantik yakınlıkla başka maddeye sıçrama yok.
            good_hits = search_tdk_exact_lemma(tdk_lem, top_k=rag_k_clamped)
        elif use_tarih_rag_branch:
            pool_k_use = pool_k
            tarih_scan = max(32, int(os.environ.get("RUZGAR_TARIH_SCAN_CAP", "96")))
            tarih_top = max(rag_k_clamped, int(os.environ.get("RUZGAR_TARIH_TOP_K", "4")))
            if tarih_light:
                try:
                    pool_k_use = min(
                        pool_k,
                        int(os.environ.get("RUZGAR_FAZ9_TARIH_POOL_K_CAP", "12")),
                    )
                except ValueError:
                    pool_k_use = min(pool_k, 12)
                try:
                    tarih_scan = max(
                        16,
                        int(os.environ.get("RUZGAR_FAZ9_TARIH_SCAN_CAP", "40")),
                    )
                except ValueError:
                    tarih_scan = 40
                try:
                    tarih_top = max(
                        2,
                        min(
                            rag_k_clamped,
                            int(os.environ.get("RUZGAR_FAZ9_TARIH_TOP_K", "3")),
                        ),
                    )
                except ValueError:
                    tarih_top = max(2, min(rag_k_clamped, 3))
            pool_hits = search(search_msg, top_k=pool_k_use)
            good_hits = [h for h in pool_hits if h[2] >= rag_score_min]
            good_hits = [h for h in good_hits if not source_is_tdk(h[1])]
            th = search_tarih_hafiza(search_msg, top_k=tarih_top, scan_cap=tarih_scan)
            th_ok = [h for h in th if h[2] >= rag_score_min]
            if not th_ok and th:
                try:
                    weak = float(os.environ.get("RUZGAR_TARIH_WEAK_SCORE", "0.12"))
                except ValueError:
                    weak = 0.12
                if float(th[0][2]) >= weak:
                    th_ok = [th[0]]
            seen: set[tuple[str, str]] = set()
            merged: list = []
            for h in th_ok + good_hits:
                key = (h[1], h[0][:200])
                if key in seen:
                    continue
                seen.add(key)
                merged.append(h)
            good_hits = merged
        elif os.environ.get("RUZGAR_MAIN_ENGINE_FIRST", "1").strip().lower() not in (
            "0",
            "false",
            "no",
        ):
            from ilim_assistant.main_engine import run_retrieval_with_status_events

            me_bundle, _me_unused = run_retrieval_with_status_events(
                msg,
                m,
                weather_q=weather_q,
                ilim_rag=ilim_rag,
                rag_top_k=rag_k_clamped,
                question_plan=turn_plan,
                search_text=search_msg,
                upload_ids=ana_motor_upload_ids,
                session_id=ana_motor_session_id,
            )
            bh = list(me_bundle.hits)
            good_hits = [h for h in bh if float(h[2]) >= rag_score_min]
            if not good_hits and bh:
                good_hits = bh[:rag_k_clamped]
            ilim_merge_tail = (me_bundle.ilim_citation_tail or "").strip()
            me_suppress_web = bool(me_bundle.suppress_main_web_search)
            archive_primary_flag = bool(me_bundle.archive_was_primary)
        else:
            pool_hits = search(search_msg, top_k=pool_k)
            good_hits = [h for h in pool_hits if h[2] >= rag_score_min]
        hits = good_hits[:rag_k_clamped]
        ar_hits = [
            h
            for h in good_hits
            if _rag_source_is_archive(h[1])
        ][:rag_k_clamped]
        try:
            from ilim_assistant.ana_motor_kaynak import format_context_blocks

            blocks = format_context_blocks(
                hits,
                archive_primary=archive_primary_flag,
            )
        except Exception:
            blocks = [(t, s) for t, s, _ in hits]

    archive_direct = try_archive_rag_direct_reply(
        msg, ar_hits, coding_mode=coding_mode, mode_norm=m
    )
    if archive_direct is not None:
        return msg, hits, "", "", "", archive_direct

    web_on = use_web and (m not in _NOWEB_MODES)
    _web_pro = False
    try:
        from ilim_assistant.ruzgar_web_arastirma_pro import should_prioritize_web_research

        _web_pro = should_prioritize_web_research(msg, turn_plan, m)
        if _web_pro:
            web_on = True
    except Exception:
        pass
    try:
        from ilim_assistant.ruzgar_umed_cevap_emri import (
            remaining_sec,
            umed_emri_applies,
        )
        from ilim_assistant.ruzgar_web_arastirma_pro import should_defer_web_for_pro

        if should_defer_web_for_pro(msg, turn_plan, m) and umed_emri_applies(
            mode_norm=m, coding_mode=coding_mode
        ):
            has_local = bool(ar_hits or hits)
            if has_local or remaining_sec() <= 10.0:
                web_on = False
    except Exception:
        try:
            from ilim_assistant.ruzgar_umed_cevap_emri import (
                remaining_sec,
                should_defer_web_to_rest,
                umed_emri_applies,
            )

            if should_defer_web_to_rest() and umed_emri_applies(
                mode_norm=m, coding_mode=coding_mode
            ):
                has_local = bool(ar_hits or hits)
                if has_local or remaining_sec() <= 10.0:
                    web_on = False
        except Exception:
            pass
    if weather_q and (m not in _NOWEB_MODES):
        web_on = True
    if (
        turn_plan is not None
        and m in ("genel", "uretim", "gelisim")
        and not turn_plan.prefer_web
        and not weather_q
        and not _web_pro
    ):
        web_on = False
    if me_suppress_web:
        web_on = False

    link_on = read_message_links and (m not in _NOWEB_MODES)

    web_extra = ""
    if not _is_wake_only_message(msg):
        # Web'i ikinci plana al: lokal hafıza / vektör araması bir bağlam üretmişse
        # (hits/blocks boş değilse) DuckDuckGo + link okuma gecikmeli devreye girer.
        web_secondary_only_on_empty = _web_secondary_policy_enabled() and not _web_pro
        local_rag_present = bool(blocks or hits or ar_hits) or bool(live_weather_ctx)
        allow_web = True
        if web_secondary_only_on_empty and local_rag_present:
            allow_web = not local_rag_strong_enough_to_skip_web(
                hits,
                ar_hits,
                archive_primary=archive_primary_flag,
            )
        if _web_pro:
            allow_web = True
        try:
            from ilim_assistant.ana_motor_plan import looks_like_fast_llm_fact_question
            from ilim_assistant.ruzgar_web_arastirma_pro import should_prioritize_web_research

            _fast_fact_no_web = looks_like_fast_llm_fact_question(msg) and not should_prioritize_web_research(
                msg, turn_plan, m
            )
        except Exception:
            _fast_fact_no_web = False
        if (
            m == "genel"
            and web_on
            and not archive_primary_flag
            and not allow_web
            and not _fast_fact_no_web
        ):
            allow_web = True

        web_parts: list[str] = []
        if allow_web:
            if (
                link_on
                and os.environ.get("ENABLE_WEB_LINK_READ", "1").strip()
                not in ("0", "false", "no")
            ):
                try:
                    link_ctx = build_message_link_context(msg)
                    if link_ctx:
                        web_parts.append(link_ctx)
                except Exception:
                    pass
            if web_on and os.environ.get("ENABLE_WEB_SEARCH", "1") == "1":
                if turn_plan is not None and getattr(turn_plan, "web_query", ""):
                    text_q = str(turn_plan.web_query).strip()
                else:
                    text_q = refined_search_query(msg).strip()
                n_fetch = int(min(max(fetch_pages, 0), 5))
                try:
                    from ilim_assistant.ruzgar_web_arastirma_pro import (
                        pick_web_context_builder,
                        resolve_pro_fetch_pages,
                        resolve_pro_max_results,
                        should_prioritize_web_research,
                    )

                    if should_prioritize_web_research(msg, turn_plan, m):
                        n_fetch = resolve_pro_fetch_pages(fetch_pages)
                except Exception:
                    pass
                skip_ddg = (
                    weather_q
                    and live_weather_ctx
                    and len(live_weather_ctx.strip()) > 48
                    and os.environ.get("RUZGAR_WEATHER_WEB_SUPPLEMENT", "0").strip()
                    not in ("1", "true", "yes", "on")
                )
                try:
                    from ilim_assistant.ana_motor_plan import (
                        looks_like_fast_llm_fact_question,
                    )
                    from ilim_assistant.ruzgar_web_arastirma_pro import (
                        should_prioritize_web_research,
                    )

                    if looks_like_fast_llm_fact_question(msg) and not should_prioritize_web_research(
                        msg, turn_plan, m
                    ):
                        skip_ddg = True
                        n_fetch = 0
                except Exception:
                    pass
                if text_q and not skip_ddg:
                    try:
                        try:
                            from ilim_assistant.ruzgar_web_arastirma_pro import (
                                pick_web_context_builder,
                                resolve_pro_max_results,
                            )

                            _web_builder = pick_web_context_builder(msg, turn_plan, m)
                        except Exception:
                            from ilim_assistant.web_tools import (
                                build_web_context,
                                build_web_context_fast,
                                web_fast_mode_enabled,
                            )

                            _web_builder = (
                                build_web_context_fast
                                if web_fast_mode_enabled()
                                else build_web_context
                            )
                        _max_res = int(
                            os.environ.get(
                                "WEB_FAST_MAX_RESULTS" if web_fast_mode_enabled() else "WEB_MAX_RESULTS",
                                "8" if web_fast_mode_enabled() else "10",
                            )
                        )
                        try:
                            from ilim_assistant.ruzgar_web_arastirma_pro import (
                                resolve_pro_max_results,
                            )

                            _max_res = resolve_pro_max_results(_max_res)
                        except Exception:
                            pass
                        search_ctx = _web_builder(
                            text_q,
                            max_results=_max_res,
                            fetch_first_n_urls=n_fetch,
                        )
                        if search_ctx:
                            web_parts.append(search_ctx)
                    except Exception:
                        pass
        web_extra = "\n\n".join(web_parts)

    _prog_light = False
    if m == "programlama":
        try:
            from ilim_assistant.motorlar.programlama_faz21 import light_context_enabled

            _prog_light = light_context_enabled()
        except Exception:
            _prog_light = False

    tools_ctx = ""
    if not (m == "programlama" and _prog_light):
        try:
            from ilim_assistant.local_tools import build_local_tools_context

            wr = (workspace_root or os.environ.get("LOCAL_TOOLS_ROOT", "") or "").strip() or None
            tools_ctx = build_local_tools_context(msg, wr)
        except Exception:
            tools_ctx = ""

    op_ctx = ""
    if _hizir_op_context_for_turn(m, motor_flags):
        try:
            from ilim_assistant.hizir.tool_bridge import build_dynamic_operasyon_context

            op_ctx = build_dynamic_operasyon_context(
                msg,
                weather_q=weather_q,
                has_live_weather_block=bool((live_weather_ctx or "").strip()),
                mode_norm=m,
                pazar_kanallari=pazar_kanallari if m == "hizir" else None,
            )
        except Exception:
            op_ctx = ""

    session_mem_ctx = ""
    try:
        from ilim_assistant.ruzgar_session_context import build_session_memory_context

        session_mem_ctx = build_session_memory_context(
            msg,
            mode_norm=m,
            history=history,
            include_chat_history=not _bilgi_isolated,
        )
    except Exception:
        session_mem_ctx = ""

    bilissel_ctx = ""
    if not _prog_light:
        try:
            from ilim_assistant.ruzgar_bilissel_analiz import build_bilissel_turn_context

            bilissel_ctx = build_bilissel_turn_context(
                msg,
                history=history if not _bilgi_isolated else None,
            ).strip()
        except Exception:
            bilissel_ctx = ""

    user_payload = build_user_prompt(msg, blocks)
    _conv_ctx = (conversation_context or "").strip()
    _raw_note = (user_message_raw or "").strip()
    _conv_continuation = bool(
        re.search(
            r"\b(?:az\s+önce|biraz\s+önce|o\s+konuda|devam|peki\s+o|onun\s+hakkında)\b",
            msg,
            re.I,
        )
    )
    if (_conv_ctx or _raw_note or cinema_context) and not (
        _bilgi_isolated and not _conv_continuation
    ):
        conv_lines = [
            "[SOHBET BAĞLAMI — kullanıcıya aynen yazdırma; yukarıdaki konuşmayı hatırla]",
        ]
        if _conv_ctx:
            conv_lines.append(_conv_ctx[:7500])
        if cinema_context and isinstance(cinema_context, dict):
            cu = str(cinema_context.get("url") or "")[:240]
            cr = str(cinema_context.get("localRel") or cinema_context.get("local_rel") or "")[:120]
            ct = str(cinema_context.get("title") or "")[:120]
            if cu or cr:
                conv_lines.append(
                    f"Sinemada açık video: {('«' + ct + '» · ') if ct else ''}"
                    f"{('url=' + cu) if cu else ''}{(' · yerel=' + cr) if cr else ''}"
                )
        if _raw_note and _raw_note != msg.strip():
            conv_lines.append(f"Kullanıcının ham cümlesi: {_raw_note[:500]}")
        conv_lines.append(
            "Talimat: Devrik cümle, yazım hatası veya kısa devam ifadelerini bağlamdan çöz; "
            "robotik komut listesi verme; Ümit abi ile doğal konuş."
        )
        conv_lines.append("[/SOHBET BAĞLAMI]")
        user_payload = "\n".join(conv_lines) + "\n\n---\n" + user_payload
    if bilissel_ctx and bilissel_ctx not in (session_mem_ctx or ""):
        user_payload = bilissel_ctx + "\n\n---\n" + user_payload
    if session_mem_ctx:
        user_payload = session_mem_ctx.rstrip() + "\n\n---\n" + user_payload
    _agent_ctx = (agent_context or "").strip()
    if _agent_ctx:
        user_payload = _agent_ctx + "\n\n" + user_payload
    if tools_ctx and not (m == "programlama" and _prog_light):
        user_payload = tools_ctx + "\n\n" + user_payload
    if op_ctx:
        user_payload = op_ctx + "\n\n" + user_payload
    if live_weather_ctx:
        user_payload = live_weather_ctx + "\n\n" + user_payload
    if web_extra:
        user_payload += "\n\n" + web_extra
        _web_pro_addon = False
        try:
            from ilim_assistant.ruzgar_web_arastirma_pro import (
                build_web_pro_system_addon,
                should_prioritize_web_research,
            )

            _web_pro_addon = should_prioritize_web_research(msg, turn_plan, m)
        except Exception:
            pass
        if os.environ.get("WEB_ANSWER_FROM_SOURCES", "1").strip() not in (
            "0",
            "false",
            "no",
        ):
            if _web_pro_addon:
                user_payload += build_web_pro_system_addon(msg)
            else:
                user_payload += (
                    "\n\n[TALİMAT — WEB BİLGİSİ]\n"
                    "Yukarıdaki **Web araması** ve/veya **bağlantı** metinlerinden yararlan; "
                    "kullanıcıya anlaşılır Türkçe özet veya cevap ver. "
                    "Önemli bilgiler için kısaca kaynak (site adı veya URL) belirt. "
                    "Sayfa metni çekilemediyse dürüstçe yaz; arama snippet’lerine güvenebilirsin.\n"
                )
        try:
            from ilim_assistant.ana_motor_arastirma import (
                maybe_build_unified_research_report,
            )

            _rapor = maybe_build_unified_research_report(
                msg,
                hits=hits,
                web_extra=web_extra,
                question_plan=turn_plan,
                mode_norm=m,
            )
            if _rapor:
                user_payload += _rapor
        except Exception:
            pass
        try:
            from ilim_assistant.ana_motor_arastirma import build_research_card_payload

            if orchestration_out is not None:
                _card = build_research_card_payload(
                    msg,
                    hits=hits,
                    web_extra=web_extra,
                    question_plan=turn_plan,
                    mode_norm=m,
                )
                if _card:
                    orchestration_out["research_card"] = _card
        except Exception:
            pass
        try:
            from ilim_assistant.ana_motor_faz_ad_sentez_pro import maybe_build_pro_research_summary
            from ilim_assistant.ruzgar_otomatik_ogrenme import lookup_bilgi_kutuphane_hint

            _sentez = ""
            _kh = None
            try:
                _kh = lookup_bilgi_kutuphane_hint(msg)
            except Exception:
                pass
            _sentez = maybe_build_pro_research_summary(
                msg,
                hits=hits,
                web_extra=web_extra,
                question_plan=turn_plan,
                mode_norm=m,
                kutuphane_hint=_kh,
            )
            if not _sentez:
                from ilim_assistant.ana_motor_sentez import maybe_build_research_summary

                _sentez = maybe_build_research_summary(
                    msg,
                    hits=hits,
                    web_extra=web_extra,
                    question_plan=turn_plan,
                    mode_norm=m,
                )
            if _sentez:
                user_payload += _sentez
                if orchestration_out is not None:
                    orchestration_out["sentez_pro"] = "pro" in _sentez.lower()
            if (
                orchestration_out is not None
                and orchestration_out.get("sentez_pro")
                and orchestration_out.get("research_card")
            ):
                from ilim_assistant.ana_motor_faz_af_arastirma_pro import enrich_research_card_pro

                orchestration_out["research_card"] = enrich_research_card_pro(
                    orchestration_out["research_card"],
                    sentez_pro=True,
                    kutuphane_hint=_kh,
                    web_extra=web_extra,
                    hits=hits,
                )
        except Exception:
            pass
    elif (
        m == "genel"
        and not archive_primary_flag
        and not (live_weather_ctx or "").strip()
        and not blocks
        and not (web_extra or "").strip()
    ):
        user_payload += _genel_no_context_directive()

    intent_classifier_on = os.environ.get("INTENT_CLASSIFIER", "1").strip() not in (
        "0",
        "false",
        "no",
    )
    if (
        intent_classifier_on
        and not weather_q
        and m not in _NO_RAG_MODES
        and not ilim_rag
    ):
        user_payload += (
            "\n\n[TALİMAT — GÜNLÜK]\n"
            "Bu mesaj **genel sohbet veya günlük konu** gibi; nahiv/tecvid/dilbilgisi **dersi gibi** "
            "çözümleme yapma. Sorulanla doğal, düz Türkçe yanıt ver; kullanıcı dil kuralı sormadıysa "
            "gramer analizi açma.\n"
        )

    if weather_q:
        tail = (
            "\n\n[TALİMAT — GÜNCEL HAVA]\n"
            "Bu soru **canlı hava durumu** ile ilgilidir (veya hemen önceki turda hava konuşulmuş olabilir). "
            "BAĞLAM’daki dilbilgisi/tecvid dosyalarını **yok say**.\n"
        )
        if live_weather_ctx:
            tail += (
                "Üstteki **Güncel hava (Open-Meteo / OpenWeatherMap)** bloğu gerçek tahmindir; "
                "Ümit abi’ye **arkadaşça** 2–4 cümlede özetle (şemsiye/layer gibi pratik notlar serbest). "
                "Rakamları abartmadan yorumla; tahmin olduğunu gerektiğinde hafifçe hatırlatabilirsin.\n"
            )
        tail += (
            "Kullanıcıyı weather.com veya Google’a **yönlendirme**; önce üstteki ölçüm veya web özetini kullan.\n"
            "Ölçüm yoksa web özetine güven veya dürüstçe bilmediğini söyle; **dilbilgisi analizi yazma**.\n"
        )
        user_payload += tail

    if (
        os.environ.get("SESSION_CONTINUITY_HINT", "1").strip()
        not in ("0", "false", "no")
        and not _bilgi_isolated
        and len(prior_messages_for_turn(history, m, message=msg, question_plan=turn_plan)) >= 2
    ):
        user_payload += (
            "\n\n[TALİMAT — OTURUM BAĞLAMI]\n"
            "Bu mesaj **aynı sohbet oturumunun devamıdır**; modele iletilen önceki kullanıcı ve asistan "
            "mesajları geçerlidir. Son soruyu önceki konuyla ilişkilendir; yeni tanışma veya yalnızca "
            "\"nasıl yardımcı olabilirim\" / sabit karşılama ile yanıtlama. "
            "Kullanıcı bilgi veya iş istiyorsa doğrudan yerine getir.\n"
        )

    try:
        from ilim_assistant.ana_motor_kaynak import citation_directive_for_turn

        user_payload += citation_directive_for_turn(
            source_count=len(hits),
            archive_primary=archive_primary_flag,
            web_present=bool((web_extra or "").strip()),
        )
    except Exception:
        pass

    if ilim_merge_tail:
        from ilim_assistant.main_engine import merge_ilim_tail

        user_payload = merge_ilim_tail(user_payload, ilim_merge_tail)

    if _bilgi_isolated:
        try:
            from ilim_assistant.ruzgar_tek_beyin_izolasyon import bilgi_isolation_user_addon

            user_payload += bilgi_isolation_user_addon(msg)
        except Exception:
            pass

    if not (m == "programlama" and _prog_light):
        try:
            from ilim_assistant.ana_motor_super import append_super_brain_directive

            user_payload = append_super_brain_directive(
                user_payload,
                question_plan=turn_plan,
                mode_norm=m,
            )
        except Exception:
            pass
        try:
            from ilim_assistant.ana_motor_bilim_derin import append_bilim_deep_directive

            user_payload = append_bilim_deep_directive(
                user_payload,
                turn_plan,
                msg,
                mode_norm=m,
            )
        except Exception:
            pass

    if m == "programlama":
        if _prog_light:
            try:
                from ilim_assistant.motorlar.programlama_faz21 import (
                    build_light_programming_context,
                )

                _pc = build_light_programming_context(
                    msg,
                    workspace_root=workspace_root,
                    include_tools=True,
                ).strip()
                if _pc:
                    user_payload = _pc
            except Exception:
                pass
        else:
            try:
                from ilim_assistant.motorlar.programlama_motoru import (
                    build_motor_context as prog_ctx,
                )

                _pc = prog_ctx(msg, workspace_root=workspace_root).strip()
                if _pc:
                    user_payload = _pc.rstrip() + "\n\n---\n" + user_payload
            except Exception:
                pass
    elif m == "mimar":
        try:
            from ilim_assistant.mimar_motoru import build_motor_context as mimar_ctx

            _mc = mimar_ctx(msg).strip()
            if _mc:
                user_payload = _mc.rstrip() + "\n\n---\n" + user_payload
        except Exception:
            pass
    elif _orkestra_context_for_turn(m, motor_flags) and not _hub_directive:
        try:
            from ilim_assistant.motorlar.ruzgar_cekirdegi import build_core_context

            _oc = build_core_context(msg).strip()
            if _oc:
                user_payload = (
                    "[ORKESTRA ŞEFİ — dahili rehber; kullanıcıya aynen okuma]\n"
                    + _oc
                    + "\n\n---\n"
                    + user_payload
                )
        except Exception:
            pass

    if hafiza_hint:
        try:
            from ilim_assistant.hafiza_dogal_sentez import append_hafiza_hint_directive

            user_payload = append_hafiza_hint_directive(user_payload, hafiza_hint, msg)
        except Exception:
            pass

    if _hub_directive:
        user_payload = _hub_directive.rstrip() + "\n\n---\n" + user_payload
        try:
            from ilim_assistant.motorlar.ana_motor_hub_faz76 import build_delegated_motor_context

            _hc = build_delegated_motor_context(
                m,
                msg,
                workspace_root=workspace_root,
                hub_meta=_hub_meta or None,
            ).strip()
            if _hc:
                user_payload = _hc.rstrip() + "\n\n---\n" + user_payload
        except Exception:
            pass

    from ilim_assistant.ilim_ve_idrak import append_global_directive

    user_payload = append_global_directive(user_payload)

    if turn_plan is not None and append_plan_directive is not None:
        user_payload = append_plan_directive(user_payload, turn_plan, m)

    if not (m == "programlama" and _prog_light):
        from ilim_assistant.idrak_entegrasyon import append_idrak_agent_layer

        user_payload = append_idrak_agent_layer(
            user_payload,
            msg,
            m,
            hits,
            web_on,
            ilim_rag,
            archive_primary=archive_primary_flag,
            orchestration_out=orchestration_out,
        )

    user_payload = append_direct_answer_directive(user_payload, msg)
    user_payload = _append_anti_repeat_instruction(user_payload, history)

    user_payload = append_wake_instruction(
        user_payload,
        msg,
        coding_mode,
        session_wake_already_done=session_wake_used,
    )

    system = pick_system(coding_mode, m)
    if m in ("genel", "uretim", "gelisim") and not coding_mode:
        try:
            from ilim_assistant.ruzgar_dogal_sohbet_faz91 import (
                build_natural_sohbet_system_addon,
                dogal_sohbet_enabled,
                is_natural_conversation_turn,
            )

            if dogal_sohbet_enabled() and is_natural_conversation_turn(
                msg, m, turn_plan, history=history
            ):
                system = system + "\n\n" + build_natural_sohbet_system_addon()
        except Exception:
            pass
        try:
            from ilim_assistant.ruzgar_tek_beyin_tek_ses import (
                append_voice_addon_to_system,
                tek_beyin_tek_ses_enabled,
            )

            if tek_beyin_tek_ses_enabled():
                _voice_path = "genel"
                if _bilgi_isolated:
                    _voice_path = "bilgi"
                elif turn_plan is not None:
                    _prim = str(getattr(turn_plan, "primary", "") or "").strip().lower()
                    if _prim in ("bilgi", "bilim", "dilbilgisi"):
                        _voice_path = "bilgi"
                    elif _prim == "hafiza":
                        _voice_path = "hafiza"
                system = append_voice_addon_to_system(system, _voice_path)
        except Exception:
            pass
        try:
            from ilim_assistant.ruzgar_tek_beyin_analiz import (
                build_analiz_system_addon,
                tek_beyin_analiz_enabled,
            )

            if tek_beyin_analiz_enabled():
                system = system + build_analiz_system_addon(msg)
        except Exception:
            pass
        try:
            from ilim_assistant.ruzgar_tek_beyin_web_arastirma import (
                build_web_research_system_addon,
                is_force_web_research,
                tek_beyin_web_arastirma_enabled,
            )

            _orch = orchestration_out if isinstance(orchestration_out, dict) else {}
            if tek_beyin_web_arastirma_enabled() and is_force_web_research(_orch):
                system = system + build_web_research_system_addon(msg)
        except Exception:
            pass
        try:
            from ilim_assistant.ruzgar_web_arastirma_pro import (
                build_web_pro_system_addon,
                should_prioritize_web_research,
            )

            if should_prioritize_web_research(msg, turn_plan, m) and (web_extra or "").strip():
                system = system + build_web_pro_system_addon(msg)
        except Exception:
            pass
    model = resolve_model(
        coding_mode,
        message=msg,
        mode_norm=m,
        question_plan=question_plan,
    )
    return msg, hits, user_payload, system, model, None


def rag_footer(hits) -> str:
    """Geliştirici için kaynak listesi; varsayılan kapalı (RAG_FOOTER=1 ile açılır)."""
    if os.environ.get("RAG_FOOTER", "0").strip() not in ("1", "true", "yes"):
        return ""
    if not hits:
        return ""
    srcs = sorted({s for _, s, __ in hits[:4]})
    return "\n\n*(Yerel bağlam: " + ", ".join(srcs) + ")*"


def respond(
    message: str,
    history: list,
    use_web: bool,
    fetch_pages: float,
    coding_mode: bool,
    stream_reply: bool,
    session_wake_used: bool,
    read_message_links: bool = True,
    mode: str = "genel",
    workspace_root: str | None = None,
):
    """Gradio ile uyumlu: (messages, empty, last_user, last_reply, status, new_wake)."""
    prep = prepare_turn(
        message,
        history,
        use_web,
        fetch_pages,
        coding_mode,
        session_wake_used,
        mode=mode,
        workspace_root=workspace_root,
        read_message_links=read_message_links,
    )
    if prep is None:
        yield ensure_messages(history), "", "", "", "", session_wake_used
        return

    msg, hits, user_payload, system, model, og_direct = prep
    new_wake_used = session_wake_used or message_calls_wake_name(msg)

    if og_direct is not None:
        reply = finalize_assistant_reply(og_direct)
        if stream_reply:
            messages = ensure_messages(history)
            messages.append({"role": "user", "content": msg})
            messages.append({"role": "assistant", "content": ""})
            yield messages, "", msg, "", "Yazıyor…", new_wake_used
            messages[-1]["content"] = reply
            yield messages, "", msg, reply, "Hazır.", new_wake_used
        else:
            messages = ensure_messages(history)
            messages.append({"role": "user", "content": msg})
            messages.append({"role": "assistant", "content": reply})
            yield messages, "", msg, reply, "Hazır.", new_wake_used
        return

    prior = prior_messages_for_turn(history, mode, message=msg)

    if stream_reply:
        messages = ensure_messages(history)
        messages.append({"role": "user", "content": msg})
        messages.append({"role": "assistant", "content": ""})
        reply_body = ""
        try:
            from ilim_assistant.llm_brain import stream_chat_with_brain

            stream_iter = stream_chat_with_brain(
                system,
                user_payload,
                model=model,
                prior_messages=prior,
                mode_norm=normalize_mode(mode),
                coding_mode=coding_mode,
                message=msg,
            )
        except ImportError:
            stream_iter = chat_completion_stream(
                system, user_payload, model=model, prior_messages=prior
            )
        for piece in stream_iter:
            reply_body += piece
            messages[-1]["content"] = repair_utf8_mojibake(reply_body)
            yield messages, "", msg, messages[-1]["content"], "Yazıyor…", new_wake_used
        reply = finalize_assistant_reply(reply_body) + rag_footer(hits)
        messages[-1]["content"] = reply
        yield messages, "", msg, reply, "Hazır.", new_wake_used
        return

    body = chat_completion(system, user_payload, model=model, prior_messages=prior)
    reply = finalize_assistant_reply(body) + rag_footer(hits)

    messages = ensure_messages(history)
    messages.append({"role": "user", "content": msg})
    messages.append({"role": "assistant", "content": reply})
    yield messages, "", msg, reply, "Hazır.", new_wake_used
