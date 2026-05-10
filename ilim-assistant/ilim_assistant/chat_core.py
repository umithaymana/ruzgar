"""Gradio ve masaüstü API için ortak sohbet mantığı."""

from __future__ import annotations

import os

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
from ilim_assistant.rag_store import search
from ilim_assistant.web_tools import (
    build_message_link_context,
    build_web_context,
    strip_urls_for_search,
)


def resolve_model(coding_mode: bool) -> str:
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
_NO_RAG_MODES = frozenset({"ses", "okuma", "tercume", "uretim", "video", "hizli"})
_NOWEB_MODES = frozenset({"ses", "okuma", "tercume", "uretim", "hizli"})

# İstemciden Türkçe karakterli veya ASCII mod adı gelebilir
_MODE_ALIASES = {
    "üretim": "uretim",
    "gelişim": "gelisim",
    "düzen": "duzen",
    "hızlı": "hizli",
    "tercüme": "tercume",
}


def normalize_mode(mode: str) -> str:
    m = (mode or "genel").strip().lower()
    return _MODE_ALIASES.get(m, m)


def _rag_source_is_archive(rel: str) -> bool:
    p = (rel or "").replace("\\", "/").lower()
    return "/arsiv/" in p or p.startswith("arsiv/")


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

    Varsayılan **tam güç**: kapalı (`0`). Daraltmak için ortamda `RUZGAR_MAIN_ONLY_GENEL_HAFIZA=1`.
    """
    return os.environ.get("RUZGAR_MAIN_ONLY_GENEL_HAFIZA", "0").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _genel_only_unknown_reply() -> str:
    raw = (os.environ.get("RUZGAR_GENEL_ONLY_MISS_REPLY") or "").strip()
    if raw:
        return raw
    try:
        from ilim_assistant.hafiza_i_ruzgar import HafizaIRuzgar

        return HafizaIRuzgar.BILINMEYEN_YANIT
    except Exception:
        return "Mimar, bunu henüz öğrenmedim, bana öğretir misin?"


def try_genel_hafiza_reply(message: str, mode: str) -> str | None:
    """
    Ana motor için `ruzgar_genel_hafiza.json` merkezi sözlüğü.
    Eşleşmede (tam / norm / RUZGAR_GENEL_HAFIZA_MIN_SIM) RAG, web ve LLM çalışmaz.

    Kapatmak için: ENABLE_RUZGAR_GENEL_HAFIZA=0 veya ENABLE_OGRENME_MERKEZI=0
    """
    del mode  # öncelik tüm ana sohbet modlarında geçerlidir
    msg = (message or "").strip()
    if not msg or len(msg) > 4000:
        return None
    try:
        from ilim_assistant.hafiza_i_ruzgar import genel_hafiza_lookup

        return genel_hafiza_lookup(msg)
    except Exception:
        return None


def _is_wake_only_message(msg: str) -> bool:
    """Yalnızca isim seslenmesi — web araması gereksiz gecikme yaratmasın."""
    t = (msg or "").strip().lower().strip(".,!?…").strip()
    return t in ("rüzgar", "ruzgar")


def _weather_intent(msg: str) -> bool:
    """Anahtar kelime + (isteğe bağlı) NB sınıflandırıcı — hava niyeti."""
    if _is_live_weather_query(msg):
        return True
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
        "hava durumu",
        "hava bugün",
        "hava yarın",
        "havalar nasıl",
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
        return max(2, int(os.environ.get("CHAT_HISTORY_MSGS_FAST", "8")))
    return max(2, int(os.environ.get("CHAT_HISTORY_MSGS", "14")))


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


def prior_messages_for_turn(history: list, mode: str) -> list:
    """Sohbet geçmişini moda göre kırpar (masaüstü API + Gradio)."""
    return trim_chat_tail(
        ensure_messages(history),
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
):
    """Boş mesajda None; aksi halde (msg, hits, user_payload, system, model, ogrenme_direct).

    Öncelik:
      - Önce `ruzgar_genel_hafiza.json` (eşleşirse anında cevap).
      - `genel` mod + `RUZGAR_MAIN_ONLY_GENEL_HAFIZA=1` ise ve eşleşme yoksa:
        yalnızca `_genel_only_unknown_reply` (RAG/web/LLM kapalı).
      - Varsayılan tam güç (`RUZGAR_MAIN_ONLY_GENEL_HAFIZA` yok veya `0`): eşleşme yoksa
        arşiv doğrudan / RAG + web + LLM.

    Streaming `skip_ogrenme_lookup=True`: (1) atlanır (istemci ön kontrol yaptıysa).
    """
    if not message or not message.strip():
        return None
    msg = message.strip()
    m = normalize_mode(mode)

    if not skip_ogrenme_lookup:
        og_direct = try_genel_hafiza_reply(msg, m)
        if og_direct is not None:
            return msg, [], "", "", "", og_direct
        if _main_chat_genel_only() and m == "genel":
            return msg, [], "", "", "", _genel_only_unknown_reply()

    weather_q = _weather_intent(msg) or _weather_follow_up(msg, history)

    try:
        from ilim_assistant.intent_router import should_use_ilim_rag

        ilim_rag = should_use_ilim_rag(msg)
    except Exception:
        ilim_rag = True

    hits: list = []
    ar_hits: list = []
    blocks: list = []
    if m in _NO_RAG_MODES:
        pass
    elif weather_q:
        # gramer/tecvid md'leri "hava" ile yanlış eşleşir; model dilbilgisi uydurur
        pass
    elif not ilim_rag:
        # knowledge/ şu an ağırlıklı dilbilgisi/tecvid; genel soruda embedding hep oraya düşer
        pass
    else:
        rag_k = int(os.environ.get("RAG_TOP_K", "2"))
        rag_k_clamped = max(1, min(rag_k, 12))
        pool_k = min(max(rag_k_clamped * 3, 10), 28)
        pool_hits = search(msg, top_k=pool_k)
        hits = pool_hits[:rag_k_clamped]
        ar_hits = [
            h for h in pool_hits if _rag_source_is_archive(h[1])
        ][:rag_k_clamped]
        blocks = [(t, s) for t, s, _ in hits]

    archive_direct = try_archive_rag_direct_reply(
        msg, ar_hits, coding_mode=coding_mode, mode_norm=m
    )
    if archive_direct is not None:
        return msg, hits, "", "", "", archive_direct

    web_on = use_web and (m not in _NOWEB_MODES)
    if weather_q and (m not in _NOWEB_MODES):
        web_on = True

    link_on = read_message_links and (m not in _NOWEB_MODES)

    web_extra = ""
    if not _is_wake_only_message(msg):
        web_parts: list[str] = []
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
            text_q = strip_urls_for_search(msg).strip()
            n_fetch = int(min(max(fetch_pages, 0), 5))
            if text_q:
                try:
                    search_ctx = build_web_context(
                        text_q,
                        max_results=int(os.environ.get("WEB_MAX_RESULTS", "10")),
                        fetch_first_n_urls=n_fetch,
                    )
                    if search_ctx:
                        web_parts.append(search_ctx)
                except Exception:
                    pass
        web_extra = "\n\n".join(web_parts)

    live_weather_ctx = ""
    if weather_q and os.environ.get("ENABLE_LIVE_WEATHER", "1").strip() not in (
        "0",
        "false",
        "no",
    ):
        try:
            from ilim_assistant.weather_live import fetch_live_weather_context

            live_weather_ctx = fetch_live_weather_context()
        except Exception:
            live_weather_ctx = ""

    tools_ctx = ""
    try:
        from ilim_assistant.local_tools import build_local_tools_context

        wr = (workspace_root or os.environ.get("LOCAL_TOOLS_ROOT", "") or "").strip() or None
        tools_ctx = build_local_tools_context(msg, wr)
    except Exception:
        tools_ctx = ""

    user_payload = build_user_prompt(msg, blocks)
    if tools_ctx:
        user_payload = tools_ctx + "\n\n" + user_payload
    if live_weather_ctx:
        user_payload = live_weather_ctx + "\n\n" + user_payload
    if web_extra:
        user_payload += "\n\n" + web_extra
        if os.environ.get("WEB_ANSWER_FROM_SOURCES", "1").strip() not in (
            "0",
            "false",
            "no",
        ):
            user_payload += (
                "\n\n[TALİMAT — WEB BİLGİSİ]\n"
                "Yukarıdaki **Web araması** ve/veya **bağlantı** metinlerinden yararlan; "
                "kullanıcıya anlaşılır Türkçe özet veya cevap ver. "
                "Önemli bilgiler için kısaca kaynak (site adı veya URL) belirt. "
                "Sayfa metni çekilemediyse dürüstçe yaz; arama snippet’lerine güvenebilirsin.\n"
            )

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
                "Üstteki **=== Güncel hava ===** bloğu gerçek ölçümdür; kullanıcıya **kısa** (1–3 cümle) aktar.\n"
            )
        tail += (
            "Kullanıcıyı weather.com veya Google’a **yönlendirme**; önce üstteki ölçüm veya web özetini kullan.\n"
            "Ölçüm yoksa web özetine güven veya dürüstçe bilmediğini söyle; **dilbilgisi analizi yazma**.\n"
        )
        user_payload += tail

    if (
        os.environ.get("SESSION_CONTINUITY_HINT", "1").strip()
        not in ("0", "false", "no")
        and len(prior_messages_for_turn(history, m)) >= 2
    ):
        user_payload += (
            "\n\n[TALİMAT — OTURUM BAĞLAMI]\n"
            "Bu mesaj **aynı sohbet oturumunun devamıdır**; modele iletilen önceki kullanıcı ve asistan "
            "mesajları geçerlidir. Son soruyu önceki konuyla ilişkilendir; yeni tanışma veya yalnızca "
            "\"nasıl yardımcı olabilirim\" / sabit karşılama ile yanıtlama. "
            "Kullanıcı bilgi veya iş istiyorsa doğrudan yerine getir.\n"
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
    model = resolve_model(coding_mode)
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

    prior = prior_messages_for_turn(history, mode)

    if stream_reply:
        messages = ensure_messages(history)
        messages.append({"role": "user", "content": msg})
        messages.append({"role": "assistant", "content": ""})
        reply_body = ""
        for piece in chat_completion_stream(
            system, user_payload, model=model, prior_messages=prior
        ):
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
