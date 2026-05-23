# Created by Ümit & Gökçenur
"""Ümit abi ile adım adım eğitim: bulamadım / yanlış cevap / oturum özeti."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_MOTOR_TIPI = "Egitim"

from ilim_assistant.ruzgar_umed_kurallari import (  # noqa: E402
    MISS_PHRASE as _MISS_PHRASE,
    SAVED_CORRECT as _SAVED_CORRECT,
    SAVED_TEACH as _SAVED_TEACH,
    SELAM_RUZGAR,
    WRONG_PROMPT as _WRONG_PROMPT,
    build_persona_context_block,
)


def _egitim_enabled() -> bool:
    return os.environ.get("RUZGAR_EGITIM", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _durum_path() -> Path:
    proje_koku = Path(__file__).resolve().parents[1]
    return proje_koku / "ruzgar_egitim_durum.json"


def _load_durum() -> dict[str, Any]:
    p = _durum_path()
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_durum(data: dict[str, Any]) -> None:
    p = _durum_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def clear_pending() -> None:
    _save_durum({})


def set_pending(mode: str, soru: str) -> None:
    _save_durum(
        {
            "mode": mode,
            "soru": (soru or "").strip(),
            "ts": datetime.now(timezone.utc).isoformat(),
        }
    )


def get_pending() -> dict[str, Any]:
    return _load_durum()


def _last_user_question(history: list) -> str:
    for row in reversed(history or []):
        if not isinstance(row, dict):
            continue
        if str(row.get("role") or "").strip().lower() == "user":
            t = str(row.get("content") or "").strip()
            if t and len(t) < 2000:
                return t
    return ""


def _extract_teaching_body(message: str) -> Optional[str]:
    raw = (message or "").strip()
    patterns = [
        r"(?is)(?:cevab[ıi]n|cevabin)\s+şu\s+olmalı(?:ydı|di)?\s*[:\-–]?\s*(?P<body>.+)$",
        r"(?is)(?:cevab[ıi]n|cevabin)\s+su\s+olmalı(?:ydı|di)?\s*[:\-–]?\s*(?P<body>.+)$",
        r"(?is)^doğru\s+cevap\s*[:\-–]?\s*(?P<body>.+)$",
        r"(?is)^dogru\s+cevap\s*[:\-–]?\s*(?P<body>.+)$",
        r"(?is)^cevap\s*[:\-–]?\s*(?P<body>.+)$",
    ]
    for pat in patterns:
        m = re.search(pat, raw)
        if m:
            body = (m.group("body") or "").strip()
            if len(body) >= 3:
                return body
    if len(raw) >= 8 and len(raw) < 1200:
        low = raw.casefold()
        try:
            from ilim_assistant.ruzgar_bilissel_analiz import is_anlama_empati_sorusu

            if is_anlama_empati_sorusu(raw):
                return None
        except Exception:
            pass
        if not re.search(
            r"yanlış\s*cevap|yanlis\s*cevap|hatırla|hatirla|unut|nebula|\.json",
            low,
        ):
            pend = get_pending()
            if pend.get("mode") in ("await_teaching", "await_correction"):
                return raw
    return None


def _norm_trigger(text: str) -> str:
    t = re.sub(r"\s+", " ", (text or "").strip().lower())
    t = re.sub(r"[.!?…,:;]+$", "", t).strip()
    return t


def _trigger_matches(message: str, trigger: str) -> bool:
    """«selam» yalnızca tek kelimeyken; «selam rüzgar» ayrı tetikleyici."""
    m = _norm_trigger(message)
    tr = _norm_trigger(trigger)
    if not m or not tr:
        return False
    if m == tr:
        return True
    tw = tr.split()
    mw = m.split()
    if len(tw) >= 2:
        return m == tr or tr in m
    if len(mw) == 1:
        return m == tr
    return False


_GREETING_WORDS = frozenset(
    {
        "selam",
        "merhaba",
        "hey",
        "slm",
        "gunaydin",
        "günaydın",
        "iyi",
        "aksam",
        "akşam",
        "geceler",
    }
)
_GREETING_ALIAS_TRIGGERS = (
    "selam",
    "merhaba",
    "selam rüzgar",
    "selam ruzgar",
)


def _is_robot_selam_cevap(cevap: str) -> bool:
    low = (cevap or "").strip().casefold()
    if not low:
        return True
    return (
        "buyur, ne yapmak" in low
        or "ne yapmak istersin" in low
        or low.startswith("selam! ben rüzgar")
        or low.startswith("selam! ben ruzgar")
    )


def _soru_is_greeting_trigger(soru: str) -> bool:
    s = _norm_trigger(soru)
    if not s or s.startswith("davranis:"):
        return False
    words = s.split()
    if len(words) == 1:
        return words[0] in _GREETING_WORDS
    if len(words) <= 3 and words[0] in ("selam", "merhaba", "hey", "slm"):
        rest = {w for w in words[1:] if w not in ("ruzgar", "rüzgar", "abi", "ümit", "umit")}
        return not rest or rest <= _GREETING_WORDS
    return False


def _is_plain_greeting_message(message: str) -> bool:
    m = _norm_trigger(message)
    if not m:
        return False
    words = m.split()
    if len(words) == 1:
        return words[0] in ("selam", "merhaba", "hey", "slm")
    if len(words) <= 3 and words[0] in ("selam", "merhaba"):
        return _soru_is_greeting_trigger(m)
    return False


def _greeting_alias_triggers(soru: str) -> list[str]:
    base = _norm_trigger(soru) or "selam"
    if _soru_is_greeting_trigger(base) or _is_plain_greeting_message(base):
        out: list[str] = []
        for t in (base, *_GREETING_ALIAS_TRIGGERS):
            nt = _norm_trigger(t)
            if nt and nt not in out:
                out.append(nt)
        return out
    return [base] if base else []


def _score_greeting_cevap(cevap: str) -> int:
    c = (cevap or "").strip()
    if not c or cevap_is_davranis_talimati(c):
        return -100
    if _is_robot_selam_cevap(c):
        return -50
    low = c.casefold()
    score = min(len(c), 220)
    for word, pts in (
        ("sohbet", 40),
        ("onur", 35),
        ("gurur", 30),
        ("kardeşim", 25),
        ("kardeş", 25),
        ("ümit abi", 20),
        ("ümit", 15),
        ("hoş geldin", 15),
    ):
        if word in low:
            score += pts
    return score


def lookup_greeting_egitim_reply(message: str) -> Optional[str]:
    """
    Düz «selam» / «merhaba» — hafızadaki «selam rüzgar» vb. öğretilmiş karşılamayı da kullan.
    """
    if not _egitim_enabled() or not _is_plain_greeting_message(message):
        return None
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        motor = get_hafiza_motor()
    except Exception:
        return None

    best: tuple[int, str] | None = None
    for row in reversed(motor._kayitlar):
        if row.get("motor_tipi") != _MOTOR_TIPI:
            continue
        soru = str(row.get("soru") or "").strip()
        cevap = str(row.get("cevap") or "").strip()
        if not soru or not cevap or not _soru_is_greeting_trigger(soru):
            continue
        if cevap_kullaniciya_okunmamali(cevap, user_msg=message):
            continue
        try:
            from ilim_assistant.ruzgar_bilissel_analiz import is_kotu_empati_cevabi

            if is_kotu_empati_cevabi(cevap, soru=soru):
                continue
        except Exception:
            pass
        sc = _score_greeting_cevap(cevap)
        if sc < 0:
            continue
        if best is None or sc > best[0]:
            best = (sc, cevap)
    return best[1] if best else None


def _is_bilgi_sorusu(message: str) -> bool:
    """«uzay nedir» gibi bilgi soruları — hatalı eğitim eşlemesine düşmesin."""
    raw = (message or "").strip()
    if len(raw) < 6 or len(raw) > 400:
        return False
    low = raw.casefold()
    if "?" in raw:
        return True
    return bool(
        re.search(
            r"\b(?:nedir|nelerdir|kimdir|ne demek|ne dir|nasil|nasıl|kaç|kac|nerede|niçin|nicin|niye)\b",
            low,
        )
    )


def is_invalid_egitim_pair(soru: str, cevap: str) -> bool:
    """Yanlış öğretim: cevap başka soru, meta mesaj veya boş."""
    s = (soru or "").strip()
    c = (cevap or "").strip()
    if not s or not c:
        return True
    if s.casefold() == c.casefold():
        return True
    low = c.casefold()
    if any(
        x in low
        for x in (
            "öğrendim ve hafızama",
            "ogrendim ve hafizama",
            "yanlış cevap",
            "doğrusunu bana öğret",
            "empati sorularında",
        )
    ):
        return True
    if c.endswith("?") or re.search(r"\b(?:nedir|nasıl|nasil)\s*\??\s*$", c, re.I):
        return True
    if _is_bilgi_sorusu(s) and _is_bilgi_sorusu(c) and len(c) < 120:
        return True
    if len(c) < 25 and _is_bilgi_sorusu(c):
        return True
    return False


def cevap_is_davranis_talimati(cevap: str) -> bool:
    """Kullanıcıya okunacak cevap değil — nasıl davranacağını anlatan talimat."""
    c = (cevap or "").strip()
    if not c:
        return True
    low = c.casefold()
    if any(
        low.startswith(x)
        for x in (
            "aleyküm",
            "aleykum",
            "merhaba",
            "selam ümit",
            "hoş geldin",
            "hos geldin",
            "olur ümit",
            "edelim",
            "rica ederim",
        )
    ):
        if not any(x in low for x in ("cevap ver", "akışına göre", "akışina göre")):
            return False
    talimat = (
        "cevap ver",
        "sohbetin akış",
        "sohbet akış",
        "akışına göre",
        "akışina göre",
        "geldiğin de",
        "geldiğinde",
        "nasıl cevap",
        "böyle yap",
        "şöyle yap",
        "soyle yap",
        "hareket et",
        "dersen sen",
        "diyorsam sende",
        "yanlış cevap",
        "anladım ve öğrendim",
        "bildiğin bir soru",
    )
    return any(x in low for x in talimat)


def cevap_kullaniciya_okunmamali(cevap: str, *, user_msg: str = "") -> bool:
    """Öğretim talimatı veya kullanıcı metninin kopyası — sohbette birebir okunmaz."""
    c = (cevap or "").strip()
    if not c:
        return True
    if cevap_is_davranis_talimati(c):
        return True
    low = c.lower()
    if len(c) > 90:
        markers = (
            "15 saniye",
            "15 sn",
            "15sn",
            "anladım ve öğrendim",
            "bildiğin bir sorunun",
            "sorunun cevab",
            "cevabını bulamadım",
            "sana şunu desin",
            "şayet cevap",
            "sayet cevap",
            "bekleme",
            "asılı kalma",
        )
        if sum(1 for m in markers if m in low) >= 2:
            return True
    if user_msg and len(c) > 80 and len(user_msg) > 40:
        from difflib import SequenceMatcher

        if SequenceMatcher(None, c.casefold(), user_msg.casefold()).ratio() >= 0.55:
            return True
    return False


def _is_hangi_konuda_message(msg: str) -> bool:
    low = re.sub(r"\s+", " ", (msg or "").strip().casefold())
    return bool(
        re.fullmatch(r"hangi konuda\??|ne konuda\??|konu ne\??|hangi konu\??", low)
    )


def reply_hangi_konuda_from_history(history: list | None) -> str:
    """«Hangi konuda?» — sohbet akışından doğal özet (talimatı okumaz)."""
    snippets: list[str] = []
    for row in history or []:
        if not isinstance(row, dict):
            continue
        role = str(row.get("role") or "").strip().lower()
        if role not in ("user", "assistant"):
            continue
        t = str(row.get("content") or "").strip()
        if not t or len(t) > 220:
            continue
        tl = t.casefold()
        if _is_hangi_konuda_message(t):
            continue
        if cevap_is_davranis_talimati(t):
            continue
        if any(x in tl for x in ("yanlış cevap", "anladım ve öğrendim", "cevap ver")):
            continue
        snippets.append(t[:120])
    snippets = snippets[-8:]
    if not snippets:
        return (
            "Ümit abi, henüz net bir konu açmadık. İstersen sen bir başlık söyle — "
            "beraber oradan gideriz."
        )
    ozet = " · ".join(snippets[-4:])
    return (
        f"Şu ana kadar konuştuğumuz şeyler bunlar: {ozet}. "
        "Hangisinden devam edelim, yoksa yeni bir konu mu açalım?"
    )


def sanitize_egitim_hafiza() -> int:
    """Davranış talimatı / hatalı soru→cevap çiftlerini temizler."""
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        motor = get_hafiza_motor()
    except Exception:
        return 0
    kept: list[dict] = []
    removed = 0
    for row in motor._kayitlar:
        mt = row.get("motor_tipi")
        if mt != _MOTOR_TIPI:
            kept.append(row)
            continue
        soru = str(row.get("soru") or "").strip()
        cevap = str(row.get("cevap") or "").strip()
        if soru.startswith("Oturum özeti") or soru.startswith("davranis:"):
            kept.append(row)
            continue
        if is_invalid_egitim_pair(soru, cevap):
            removed += 1
            continue
        if cevap_is_davranis_talimati(cevap):
            _save_davranis_teach(
                f"{soru or 'davranis'}: {cevap[:40]}",
                ozet=cevap,
            )
            removed += 1
            continue
        kept.append(row)
    if removed:
        motor._kayitlar = kept
        motor._sync_hafiza_view()
        motor._dosyaya_kaydet()
    return removed


def has_egitim_trigger_match(message: str) -> bool:
    """Öğretilmiş tetikleyici var mı (selam rüzgar vb.) — şablondan önce."""
    if lookup_egitim_reply(message):
        return True
    try:
        from ilim_assistant.ruzgar_egitim_anlama import find_matching_rule

        if find_matching_rule(message):
            return True
    except Exception:
        pass
    return False


def _message_is_casual_turn(msg: str) -> bool:
    """İltifat / kısa sohbet — hafızadan uzun talimat dökülmemeli."""
    raw = (msg or "").strip()
    if not raw or len(raw.split()) > 14:
        return False
    low = raw.casefold()
    if re.search(r"\b(?:ruzgar|rüzgar)\b", low) and has_egitim_trigger_match(raw):
        return False
    if any(
        x in low
        for x in (
            "enerjik",
            "harikasın",
            "harikasin",
            "çok iyisin",
            "cok iyisin",
            "güzelsin",
            "guzelsin",
            "aferin",
            "teşekkür",
            "tesekkur",
            "seviyorum",
            "nasılsın",
            "nasilsin",
        )
    ):
        return True
    try:
        from ilim_assistant.ana_motor_plan import looks_like_casual_social_chat

        if looks_like_casual_social_chat(raw) and "?" not in raw:
            if not any(x in low for x in ("nedir", "nasıl", "nasil", "kim", "ne zaman", "kaç", "kac")):
                return True
    except Exception:
        pass
    return False


def is_real_user_question(msg: str) -> bool:
    """15 sn «bulamadım» yalnızca gerçek bilgi sorusunda."""
    raw = (msg or "").strip()
    if len(raw) < 8:
        return False
    if is_wrong_answer_trigger(raw):
        return False
    if _message_is_casual_turn(raw):
        return False
    if _should_use_anlama(raw):
        return False
    low = raw.casefold()
    if any(x in low for x in ("anladım ve öğrendim", "yanlış cevap", "yanlis cevap", "hatırla")):
        return False
    return True


def _looks_like_davranis_teach(text: str) -> bool:
    low = (text or "").lower()
    return ("15" in low and "saniye" in low) or (
        "bulamadım" in low and "soru" in low
    )


def _save_davranis_teach(metin: str, *, ozet: str = "") -> None:
    """Davranış talimatı — arama anahtarı değil, yalnızca LLM bağlamı / miss kuralı."""
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        text = (ozet or metin or "")[:800]
        key = "davranis:15sn_miss"
        if "hangi konuda" in text.casefold() or "akış" in text.casefold():
            key = "davranis:hangi_konuda"
        payload = json.dumps(
            {
                "tip": "davranis",
                "miss_15sn": _MISS_PHRASE,
                "ozet": text,
            },
            ensure_ascii=False,
        )
        get_hafiza_motor().ekle_bilgi(key, payload, motor_tipi=_MOTOR_TIPI)
    except Exception:
        pass


def _looks_like_meta_rule_doc(text: str) -> bool:
    low = (text or "").lower()
    return len(low) > 70 and any(
        x in low for x in (" dersen", "cevap ver", "ama ben", "hitap edersem", "öğret")
    )


def _parse_turkish_egitim_rules(body: str) -> list[tuple[str, str]]:
    """«X dersen Y» / tırnaklı çoklu öğretim kurallarını ayırır."""
    text = (body or "").strip()
    if not text:
        return []
    rules: list[tuple[str, str]] = []

    for m in re.finditer(
        r'(?is)[«"\']([^«"\']{2,80})[«"\']?\s+dersen[^.]{0,120}?(?:sen\s+de\s+)?'
        r'(?:şöyle|soyle|böyle)?\s*(?:söyle|soyle|de\s+)?[:\-]?\s*[«"\']([^«"\']{3,400})[«"\']',
        text,
    ):
        rules.append((m.group(1).strip(), m.group(2).strip()))

    for m in re.finditer(
        r"(?is)\b(selam\s+r[üu]zgar)\s+dersen\s+sen\s+de\s+(.+?)(?=\s+ama\s+|\.\s*ama\b|$)",
        text,
    ):
        rules.append((m.group(1).strip(), m.group(2).strip().strip("«»\"' ")))

    # «sadece selam dersen böyle cevap ver» — yanıt aynı cümlede yoksa ayrı kural yazma

    for m in re.finditer(
        r"(?is)\b([a-zçğıöşü0-9\s]{2,45})\s+dersen\s+sen\s+de\s+([^.!?]{10,400})",
        text,
    ):
        trig = m.group(1).strip()
        resp = m.group(2).strip().strip("«»\"' ")
        if trig and resp and len(trig.split()) <= 6:
            rules.append((trig, resp))

    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for trig, resp in rules:
        key = _norm_trigger(trig)
        rlow = resp.lower()
        if not key or key in seen or len(resp) < 4:
            continue
        if any(x in rlow for x in ("hitap edersem", "ama ben", " dersen", "cevap ver")):
            continue
        if len(trig.split()) == 1 and len(resp) > 160:
            continue
        seen.add(key)
        out.append((trig, resp))
    return out


def _dedupe_rules(rules: list[tuple[str, str]]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for trig, resp in rules:
        k = _norm_trigger(trig)
        if not k or k in seen:
            continue
        seen.add(k)
        out.append((trig.strip(), resp.strip()))
    return out


def _reply_for_trigger(message: str, soru: str, cevap: str) -> str:
    msg = (message or "").strip()
    c = (cevap or "").strip()
    if c and len(c) <= 420 and not cevap_kullaniciya_okunmamali(c, user_msg=msg):
        low = c.casefold()
        if low.startswith(
            ("aleyküm", "aleykum", "merhaba", "selam", "hoş geldin", "hos geldin")
        ):
            return c
    if _looks_like_meta_rule_doc(c):
        for trig, resp in _parse_turkish_egitim_rules(c):
            if _trigger_matches(msg, trig):
                return resp
        return ""
    if c and len(c) <= 400 and not cevap_is_davranis_talimati(c):
        return c
    rules = _parse_turkish_egitim_rules(c)
    for trig, resp in rules:
        if _trigger_matches(msg, trig):
            return resp
    return ""


def lookup_egitim_reply(message: str) -> Optional[str]:
    """Egitim rafında tetikleyici eşleşmesi — en uzun tetikleyici kazanır."""
    if not _egitim_enabled():
        return None
    msg = (message or "").strip()
    if not msg or len(msg) > 500:
        return None
    bilgi = _is_bilgi_sorusu(msg)
    try:
        from ilim_assistant.ruzgar_bilissel_analiz import (
            is_anlama_empati_sorusu,
            is_kotu_empati_cevabi,
        )

        if is_anlama_empati_sorusu(msg):
            return None
    except Exception:
        pass
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        motor = get_hafiza_motor()
    except Exception:
        return None

    matched: list[tuple[int, int, str, str]] = []
    for row in reversed(motor._kayitlar):
        if row.get("motor_tipi") != _MOTOR_TIPI:
            continue
        soru = str(row.get("soru") or "").strip()
        cevap = str(row.get("cevap") or "").strip()
        if not soru or not cevap or soru.startswith("Oturum özeti"):
            continue
        if cevap_kullaniciya_okunmamali(cevap, user_msg=msg):
            continue
        if is_invalid_egitim_pair(soru, cevap):
            continue
        if bilgi and is_invalid_egitim_pair(msg, cevap):
            continue
        if str(soru).startswith("davranis:"):
            continue
        if _trigger_matches(msg, soru):
            try:
                from ilim_assistant.ruzgar_bilissel_analiz import is_kotu_empati_cevabi

                if is_kotu_empati_cevabi(cevap, soru=soru):
                    continue
            except Exception:
                pass
            rep = _reply_for_trigger(msg, soru, cevap)
            if rep and not cevap_kullaniciya_okunmamali(rep, user_msg=msg):
                matched.append((len(soru.split()), len(soru), soru, rep))

    if matched:
        matched.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return matched[0][3]
    return lookup_greeting_egitim_reply(msg)


def taught_reply_for_message(message: str) -> Optional[str]:
    """Öğretilmiş soru→cevap (Egitim rafı) — hızlı, doğrudan."""
    hit = lookup_egitim_reply(message)
    if hit and not cevap_kullaniciya_okunmamali(hit, user_msg=message):
        return hit
    return None


def maybe_egitim_learned_reply(
    message: str,
    history: list | None = None,
) -> Optional[str]:
    """Ümit abi'nin öğrettiği yanıt — talimatı okumaz; sohbet akışını kullanır."""
    hit = taught_reply_for_message(message)
    if hit:
        return hit
    try:
        from ilim_assistant.ruzgar_bilissel_analiz import (
            is_anlama_empati_sorusu,
            maybe_bilissel_instant_reply,
        )

        if is_anlama_empati_sorusu(message):
            return maybe_bilissel_instant_reply(message, history=history)
    except Exception:
        pass
    if _is_hangi_konuda_message(message):
        return reply_hangi_konuda_from_history(history)

    try:
        from ilim_assistant.ruzgar_egitim_anlama import reply_from_understanding

        understood = reply_from_understanding(message)
        if understood and not cevap_kullaniciya_okunmamali(understood, user_msg=message):
            return understood
    except Exception:
        pass
    if _message_is_casual_turn(message):
        return None
    return None


def _should_use_anlama(cevap: str) -> bool:
    c = (cevap or "").strip()
    if len(c) < 55:
        return False
    try:
        from ilim_assistant.ruzgar_egitim_anlama import _looks_like_teaching_narrative

        return _looks_like_teaching_narrative(c) or _looks_like_meta_rule_doc(c)
    except Exception:
        return _looks_like_meta_rule_doc(c)


def save_teaching_pair(
    soru: str, cevap: str, *, correction: bool = False, baglam_soru: str = ""
) -> str:
    """Soru–cevap çiftini Egitim rafına yazar; uzun metin → kavrayış analizi."""
    s = (soru or "").strip()
    c = (cevap or "").strip()
    if not c:
        return "Soru veya cevap boş; kaydedemedim."
    try:
        from ilim_assistant.ruzgar_bilissel_analiz import (
            is_anlama_empati_sorusu,
            is_kotu_empati_cevabi,
            maybe_bilissel_instant_reply,
        )

        if is_anlama_empati_sorusu(s) or is_anlama_empati_sorusu(c):
            clear_pending()
            return maybe_bilissel_instant_reply(s or c) or (
                "Ümit abi, seni duyuyorum — bu empati sorusunu hafızaya kopya olarak "
                "kaydetmiyorum; samimi konuşmaya devam edelim."
            )
        if is_kotu_empati_cevabi(c, soru=s):
            clear_pending()
            return (
                "Ümit abi, bu cevap çok kısa ve mekanik — empati sorularında böyle "
                "kaydetmiyorum. İstersen nasıl hissettirmemi istediğini uzun anlat."
            )
    except Exception:
        pass

    if _looks_like_davranis_teach(c) or cevap_is_davranis_talimati(c):
        _save_davranis_teach(c, ozet=c)
        clear_pending()
        if "hangi konuda" in c.casefold():
            return (
                "Tamam Ümit abi, anladım — «hangi konuda» dediğinde artık sohbetin akışına göre "
                "konu özetleyerek cevap vereceğim; talimatı sana geri okumam."
            )
        return (
            "Tamam Ümit abi, anladım ve öğrendim — bundan sonra bildiğim bir soruda "
            f"~15 saniyede cevap çıkmazsa sana şunu derim: «{_MISS_PHRASE}» "
            "Sonra istersen doğru cevabı öğretirsin."
        )

    greeting_ctx = _soru_is_greeting_trigger(s) or _soru_is_greeting_trigger(
        baglam_soru
    ) or _is_plain_greeting_message(s or baglam_soru)
    skip_anlama = greeting_ctx and (
        correction or len(c) < 220 or _score_greeting_cevap(c) > 30
    )

    if _should_use_anlama(c) and not skip_anlama:
        try:
            from ilim_assistant.ruzgar_egitim_anlama import save_teaching_with_understanding

            ok, msg = save_teaching_with_understanding(
                c, baglam_soru=s or baglam_soru
            )
            if ok and msg:
                clear_pending()
                return msg
        except Exception:
            pass

    rules = _dedupe_rules(_parse_turkish_egitim_rules(c))
    if not rules and s and not _looks_like_meta_rule_doc(c):
        rules = [(s, c)]
    elif s and c and not _looks_like_meta_rule_doc(c):
        rules = _dedupe_rules(rules + [(s, c)])
    if greeting_ctx and rules:
        expanded: list[tuple[str, str]] = []
        for trig, resp in rules:
            for alias in _greeting_alias_triggers(trig or s or "selam"):
                expanded.append((alias, resp))
        rules = _dedupe_rules(expanded)
    if not rules:
        if cevap_kullaniciya_okunmamali(c):
            _save_davranis_teach(c)
            clear_pending()
            return (
                "Tamam Ümit abi, anladım — bunu davranış kuralı olarak kaydettim; "
                "sohbette aynen okumam."
            )
        rules = [(s or c[:80], c)]
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        motor = get_hafiza_motor()
        for trig, resp in rules:
            if (
                trig
                and resp
                and not cevap_kullaniciya_okunmamali(resp)
                and not cevap_is_davranis_talimati(resp)
                and not is_invalid_egitim_pair(trig, resp)
            ):
                motor.ekle_bilgi(trig, resp, motor_tipi=_MOTOR_TIPI)
    except Exception as exc:
        return f"Hafızaya yazamadım: {exc}"
    clear_pending()
    return _SAVED_CORRECT if correction else _SAVED_TEACH


def miss_phrase() -> str:
    return _MISS_PHRASE


def is_wrong_answer_trigger(message: str) -> bool:
    low = (message or "").strip().casefold()
    if re.fullmatch(r"yanl[ıi]ş(\s*cevap)?|yanlis(\s*cevap)?", low):
        return True
    return bool(re.match(r"^(doğrusu|dogrusu)\s+şu|^(doğru|dogru)\s+cevap\s+şu", low))


def _extract_dogrusu_su_body(message: str) -> Optional[str]:
    raw = (message or "").strip()
    patterns = [
        r"(?is)^(?:doğrusu|dogrusu)\s+şu(?:dur|dur)?\s*[:\-–]?\s*(?P<body>.+)$",
        r"(?is)^(?:doğru|dogru)\s+cevap\s+şu(?:dur|dur)?\s*[:\-–]?\s*(?P<body>.+)$",
    ]
    for pat in patterns:
        m = re.search(pat, raw)
        if m:
            body = (m.group("body") or "").strip()
            if len(body) >= 3:
                return body
    return None


def is_teach_mode_trigger(message: str) -> bool:
    low = (message or "").strip().casefold()
    return bool(re.search(r"\b(?:bunu|şunu|sunu)\s+öğret\b|\b(?:bunu|şunu|sunu)\s+ogret\b", low))


def _egitim_has_trigger(motor: Any, trigger: str) -> bool:
    tr = _norm_trigger(trigger)
    for row in motor._kayitlar:
        if row.get("motor_tipi") != _MOTOR_TIPI:
            continue
        if _norm_trigger(str(row.get("soru") or "")) == tr:
            return True
    return False


def sync_greeting_egitim_aliases() -> int:
    """Öğretilmiş selam cevabını düz selam/merhaba tetikleyicilerine yayar."""
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor
        from ilim_assistant.ruzgar_umed_kurallari import SELAM_STANDART

        motor = get_hafiza_motor()
    except Exception:
        return 0
    best = lookup_greeting_egitim_reply("selam")
    if not best or _is_robot_selam_cevap(best):
        best = SELAM_STANDART
    added = 0
    for trig in ("selam", "merhaba"):
        if _egitim_has_trigger(motor, trig):
            continue
        motor.ekle_bilgi(trig, best, motor_tipi=_MOTOR_TIPI)
        added += 1
    return added


def ensure_canonical_egitim_pairs() -> None:
    """Çekirdek selam — yalnızca tetikleyici yoksa eklenir (öğretilmiş cevabı ezmez)."""
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor
        from ilim_assistant.ruzgar_umed_kurallari import SELAM_STANDART

        motor = get_hafiza_motor()
        for trig, cevap in (
            ("selam", SELAM_STANDART),
            ("merhaba", SELAM_STANDART),
            ("selam rüzgar", SELAM_RUZGAR),
            ("selam ruzgar", SELAM_RUZGAR),
        ):
            if not _egitim_has_trigger(motor, trig):
                motor.ekle_bilgi(trig, cevap, motor_tipi=_MOTOR_TIPI)
        sync_greeting_egitim_aliases()
    except Exception:
        pass


def try_consume_egitim_command(message: str, history: list | None = None) -> Optional[str]:
    """
    Eğitim komutları — anında yanıt (LLM yok).
    Bekleyen düzeltme/öğretme turunda gelen metin cevap olarak kaydedilir.
    """
    if not _egitim_enabled():
        return None
    raw = (message or "").strip()
    if not raw:
        return None

    pend = get_pending()
    if _is_bilgi_sorusu(raw) and str(pend.get("mode") or "") not in (
        "await_teaching",
        "await_correction",
    ):
        return None

    if is_wrong_answer_trigger(raw):
        body = _extract_dogrusu_su_body(raw)
        if body:
            d = _load_durum()
            soru = _last_user_question(history or []) or str(d.get("last_soru") or "").strip()
            if not soru:
                soru = str(d.get("last_soru") or "").strip() or raw[:80]
            return save_teaching_pair(soru, body, correction=True, baglam_soru=soru)
        d = _load_durum()
        soru = _last_user_question(history or []) or str(d.get("last_soru") or "").strip()
        set_pending("await_correction", soru)
        return _WRONG_PROMPT

    if is_teach_mode_trigger(raw):
        body = re.sub(
            r"(?is)^.*?\b(?:bunu|şunu|sunu)\s+öğret\s*[:\-–]?\s*",
            "",
            raw,
        ).strip()
        if len(body) >= 3:
            d = _load_durum()
            soru = _last_user_question(history or []) or str(d.get("last_soru") or "").strip()
            if not soru:
                soru = body[:80]
            return save_teaching_pair(soru, body, correction=False, baglam_soru=soru)

    if len(raw) >= 55 and _should_use_anlama(raw):
        try:
            from ilim_assistant.ruzgar_egitim_anlama import save_teaching_with_understanding

            d = _load_durum()
            baglam = str(d.get("last_soru") or "").strip() or _last_user_question(
                history or []
            )
            ok, msg = save_teaching_with_understanding(raw, baglam_soru=baglam)
            if ok and msg:
                clear_pending()
                return msg
        except Exception:
            pass

    try:
        from ilim_assistant.ruzgar_bilissel_analiz import (
            is_anlama_empati_sorusu,
            maybe_bilissel_instant_reply,
        )

        if is_anlama_empati_sorusu(raw):
            clear_pending()
            return maybe_bilissel_instant_reply(raw, history=history)
    except Exception:
        pass

    body = _extract_teaching_body(raw)
    if body:
        try:
            from ilim_assistant.ruzgar_bilissel_analiz import is_anlama_empati_sorusu

            if is_anlama_empati_sorusu(body):
                clear_pending()
                return (
                    "Ümit abi, bu bir sohbet sorusu — hafızaya soru-cevap olarak kaydetmiyorum. "
                    "Seni duyuyorum ve anlıyorum; devam et."
                )
        except Exception:
            pass
        pend = get_pending()
        mode = str(pend.get("mode") or "")
        soru = (pend.get("soru") or "").strip() or _last_user_question(history or [])
        d = _load_durum()
        if not soru:
            soru = str(d.get("last_soru") or "").strip()
        if not soru:
            soru = raw[:120]
        return save_teaching_pair(
            soru,
            body,
            correction=mode == "await_correction",
            baglam_soru=soru,
        )

    return None


def note_last_user_question(message: str) -> None:
    """Son kullanıcı sorusunu bekleyen duruma yazar (yanlış cevap için)."""
    m = (message or "").strip()
    if not m or len(m) > 2000:
        return
    if is_wrong_answer_trigger(m) or is_teach_mode_trigger(m):
        return
    try:
        from ilim_assistant.ruzgar_bilissel_analiz import is_anlama_empati_sorusu

        if is_anlama_empati_sorusu(m):
            return
    except Exception:
        pass
    low = m.casefold()
    if any(
        x in low
        for x in (
            "hatırla",
            "unut",
            "profil",
            "nebula",
            "cevabın şu",
            "cevabin su",
            "doğru cevap",
            "dogru cevap",
        )
    ):
        return
    d = _load_durum()
    d["last_soru"] = m
    _save_durum(d)


def should_emit_miss_reply(
    reply: str, elapsed_sec: float, *, user_message: str = ""
) -> bool:
    """Yanıt zayıfsa veya süre aşıldıysa «bulamadım» öner."""
    if not _egitim_enabled():
        return False
    if user_message and not is_real_user_question(user_message):
        return False
    try:
        limit = float(os.environ.get("RUZGAR_EGITIM_MISS_SEC", "15"))
    except ValueError:
        limit = 15.0
    t = (reply or "").strip()
    if elapsed_sec >= limit:
        if len(t) < 280:
            return True
        low = t.lower()
        if any(
            x in low
            for x in (
                "nasıl yardımcı olabilirim",
                "merhaba — ben rüzgar",
                "bugün sana nasıl",
            )
        ):
            return True
    if not t or len(t) < 12:
        return True
    low = t.lower()
    if "bulamadım" in low or "öğrenmedim" in low or "ogrenmedim" in low:
        return True
    if "gemini kota" in low or "ollama" in low and "yanıt" in low:
        return True
    return False


def wrap_miss_if_needed(
    reply: str, user_message: str, elapsed_sec: float
) -> tuple[str, bool]:
    """Gerekirse miss metni döner ve öğretme bekler."""
    taught = taught_reply_for_message(user_message)
    if taught:
        return taught, False
    if not should_emit_miss_reply(reply, elapsed_sec, user_message=user_message):
        return reply, False
    soru = (user_message or "").strip()
    if soru:
        set_pending("await_teaching", soru)
    return miss_phrase(), True


def list_egitim_summaries(limit: int = 6) -> list[str]:
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        items = get_hafiza_motor().tum_bilgiler(motor_tipi=_MOTOR_TIPI)
    except Exception:
        return []
    out: list[tuple[str, str]] = []
    for k, v in items.items():
        if str(k).startswith("Oturum özeti"):
            out.append((k, v))
    out.sort(key=lambda x: x[0], reverse=True)
    return [v for _, v in out[:limit]]


def build_egitim_context_block() -> str:
    """Sohbet turuna eklenecek eğitim + oturum özeti bloğu."""
    if not _egitim_enabled():
        return ""
    lines = [
        "[RÜZGAR ÇEKİRDEK KURALLAR — Ümit abi]",
        build_persona_context_block().strip(),
        "[RÜZGAR EĞİTİM — Ümit abi ile öğretilenler ve oturumlar]",
    ]
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        items = get_hafiza_motor().tum_bilgiler(motor_tipi=_MOTOR_TIPI)
        pairs = [
            (k, v)
            for k, v in items.items()
            if k and v and not str(k).startswith("Oturum özeti")
        ][-12:]
        if pairs:
            lines.append("Öğretilmiş kavrayışlar (robotik kopya yok; niyete göre konuş):")
            for s, c in pairs:
                try:
                    from ilim_assistant.ruzgar_egitim_anlama import _parse_stored_rule

                    rule = _parse_stored_rule(c)
                    if rule:
                        tr = ", ".join((rule.get("tetikleyiciler") or [])[:4])
                        lines.append(
                            f"- Tetik: {tr}\n  Kavrayış: {str(rule.get('ruzgar_kavrayisi') or '')[:220]}\n"
                            f"  Yanıt tarzı: {str(rule.get('yanit_rehberi') or '')[:180]}"
                        )
                        continue
                except Exception:
                    pass
                lines.append(f"- Soru: {s[:200]}\n  Bilgi: {c[:400]}")
    except Exception:
        pass
    sums = list_egitim_summaries(5)
    if sums:
        lines.append("Son sohbet oturumu özetleri:")
        for s in sums:
            lines.append(f"- {s[:500]}")
    lines.append(
        "Talimat: Bu blokları kullanıcıya aynen okuma; benzer sorularda bağ kurarak cevap ver."
    )
    lines.append("[/RÜZGAR EĞİTİM]")
    return "\n".join(lines) + "\n"


def on_chat_turn_done(req: Any, done: dict[str, Any]) -> dict[str, Any]:
    """Tur bitince oturum özeti + zayıf yanıtta «bulamadım»."""
    if not _egitim_enabled():
        return done
    msg = str(done.get("user_message") or getattr(req, "message", "") or "").strip()
    reply = str(done.get("full_reply") or "").strip()
    elapsed = float(done.get("elapsed_sec") or 0.0)
    if not done.get("instant_gundelik") and not done.get("egitim_instant"):
        reply2, miss = wrap_miss_if_needed(reply, msg, elapsed)
        if miss:
            done = dict(done)
            done["full_reply"] = reply2
            done["egitim_miss"] = True
    hist = list(getattr(req, "history", None) or [])
    if msg:
        hist = hist + [
            {"role": "user", "content": msg},
            {"role": "assistant", "content": str(done.get("full_reply") or reply)},
        ]
    try:
        save_session_summary_from_history(hist)
    except Exception:
        pass
    if msg and not is_wrong_answer_trigger(msg):
        note_last_user_question(msg)
    return done


def save_session_summary_from_history(history: list) -> None:
    """Sohbet bitince kısa oturum özeti kaydet (LLM yoksa kural tabanlı)."""
    if not _egitim_enabled():
        return
    msgs = []
    for row in history or []:
        if not isinstance(row, dict):
            continue
        role = str(row.get("role") or "").strip().lower()
        if role not in ("user", "assistant"):
            continue
        t = str(row.get("content") or "").strip()
        if t:
            msgs.append(f"{role}: {t[:300]}")
    if len(msgs) < 2:
        return
    user_bits = [
        str(row.get("content") or "").strip()
        for row in history or []
        if isinstance(row, dict) and str(row.get("role") or "").lower() == "user"
    ]
    topics = " · ".join(user_bits[-6:])[:900]
    summary = (
        f"Oturum ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC): "
        f"Ümit abi ile konuşulan başlıklar — {topics}"
    )
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        key = f"Oturum özeti {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M')}"
        get_hafiza_motor().ekle_bilgi(key, summary, motor_tipi=_MOTOR_TIPI)
    except Exception:
        pass
