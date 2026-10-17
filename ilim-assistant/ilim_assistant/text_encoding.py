"""UTF-8 içeriğin Latin-1 / Windows-1252 gibi yanlış kod çözülmesinden doğan mojibake onarımı."""

from __future__ import annotations

import os


def repair_utf8_mojibake(s: str) -> str:
    """
    Örnek: 'Ãœmit' → 'Ümit' (UTF-8 baytları yanlışlıkla cp1252 karakter dizisi olarak tutulmuşsa).
    MOJIBAKE_REPAIR=0 ile kapatılabilir.
    """
    if not s or len(s) < 2:
        return s
    raw = os.environ.get("MOJIBAKE_REPAIR", "1").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return s
    if not any(x in s for x in ("Ã", "Ä", "Å", "Â", "�")):
        return s

    def _score(t: str) -> int:
        return sum(t.count(x) for x in ("Ã", "Ä", "Å", "Â"))

    best = s
    best_sc = _score(s)
    for enc in ("cp1252", "cp1254", "latin-1"):
        try:
            cand = s.encode(enc).decode("utf-8")
        except UnicodeError:
            continue
        sc = _score(cand)
        if sc < best_sc:
            best, best_sc = cand, sc
    return best


def strip_wake_greeting_echo(text: str) -> str:
    """
    Model bazen sistemdeki sabit karşılama cümlesini (Ümit abi / yardımcı olabilirim) yanıta kopyalar.
    Metnin başındaki bu satırları kaldırır. STRIP_WAKE_GREETING=0 ile kapatılabilir.
    """
    if not text:
        return text
    raw = os.environ.get("STRIP_WAKE_GREETING", "1").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return text

    from ilim_assistant.persona import OWNER_ADDRESS, WAKE_GREETING, WAKE_GREETING_CODING

    lines = text.replace("\r\n", "\n").split("\n")
    i = 0
    fixed = {WAKE_GREETING.strip(), WAKE_GREETING_CODING.strip()}
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s in fixed:
            i += 1
            continue
        low = s.lower()
        if OWNER_ADDRESS.lower() in low and (
            "yardımcı" in low
            or "yardimci" in low
            or "yardım" in low
        ):
            if (
                "nasıl" in low
                or "nasil" in low
                or "olabilirim" in low
                or "olayım" in low
                or "olayim" in low
            ):
                i += 1
                continue
        break
    return "\n".join(lines[i:]).lstrip("\n")


def strip_hafiza_robot_phrasing(text: str) -> str:
    """Eski Faz 75 anında lookup kalıntılarını kullanıcıdan gizler."""
    if not text:
        return text
    import re

    t = str(text)
    t = re.sub(
        r"(?i)^(?:ümit\s+abi[,:\s]+)?haf[ıi]zamda\s+buldum\s*:\s*",
        "",
        t,
    )
    t = re.sub(
        r"(?i)^(?:ümit\s+abi[,:\s]+)?genel\s+haf[ıi]zada\s+bu\s+soruya\s+net\s+kay[ıi]t\s+bulamad[ıi]m\.?\s*",
        "",
        t,
    )
    t = re.sub(
        r"(?i)\n*öğretmek\s+için\s*:\s*`?hat[ıi]rla:\s*soru\s*=\s*cevap`?.*",
        "",
        t,
        flags=re.DOTALL,
    )
    t = re.sub(r"\n*\(hafiza-faz75-v1[^\)]*\)\s*$", "", t, flags=re.I)
    return t.strip()


def finalize_assistant_reply(raw: str, *, channel: str = "") -> str:
    """Mojibake onarımı, sızan talimat temizliği, sabit karşılama kırpma, Tek Ses (Faz B)."""
    t = repair_utf8_mojibake(raw or "")
    t = strip_answer_scaffold(t)
    t = scrub_leaked_instructions(t)
    t = strip_wake_greeting_echo(t)
    t = strip_hafiza_robot_phrasing(t)
    try:
        from ilim_assistant.ruzgar_tek_ses_faz_b import polish_tek_ses

        t = polish_tek_ses(t, channel=channel)
    except Exception:
        pass
    try:
        from ilim_assistant.ruzgar_tek_beyin_tek_ses import polish_tek_beyin_voice

        t = polish_tek_beyin_voice(t)
    except Exception:
        pass
    import re

    t = re.sub(r"(?im)^[ \t]*\*{0,2}Güven:\s*.*$", "", t)
    t = re.sub(r"\*{0,2}Güven:\s*[^*\n]+\*{0,2}", "", t)
    t = re.sub(r"\n+\*Not \(Faz [A-Z]\):[\s\S]*$", "", t)
    t = re.sub(r"\*Not \(Faz [^)]+\):[^\n]*", "", t)
    t = re.sub(r"\(Talimat:[^)]*\)", "", t, flags=re.I)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def strip_answer_scaffold(text: str) -> str:
    """Modelin «Niyet / Cevap / Gerekçe» şablonunu kullanıcıya bırakma."""
    if not text:
        return text
    import re

    if not re.search(r"(?im)^(?:niyet|sevinç|sevinc|kimlik)\s*:", text):
        return text
    label = re.compile(
        r"(?i)^(?:niyet|kimlik(?:/yakınlık)?|üretim|uretim|sevinç|sevinc|soru)\s*:"
    )
    stop = re.compile(r"(?i)^(?:örnek|ornek|gerekçe|gerekce)\s*:")
    body: list[str] = []
    capture = False
    saw = False
    for ln in text.splitlines():
        st = ln.strip()
        if re.match(r"(?i)^cevap\s*:", st):
            saw = True
            capture = True
            rest = re.sub(r"(?i)^cevap\s*:\s*", "", st).strip()
            if rest:
                body.append(rest)
            continue
        if capture and stop.match(st):
            break
        if capture:
            body.append(ln)
            continue
        if label.match(st):
            continue
    cleaned = "\n".join(body).strip() if saw else ""
    if cleaned:
        return cleaned
    kept = [ln for ln in text.splitlines() if ln.strip() and not label.match(ln.strip())]
    return "\n".join(kept).strip() or text


def scrub_leaked_instructions(text: str) -> str:
    """
    Model bazen kullanıcı mesajında sistem köşeli etiketlerini ([TALİMAT …]) kopyalar
    veya talimat cümlelerini cevaba yazar. Bu satırları çıkarır (asıl içerik silinmez).
    """
    if not text:
        return text
    import re

    out_lines: list[str] = []
    for ln in text.split("\n"):
        st = ln.strip()
        if not st:
            out_lines.append(ln)
            continue
        if "[TALİMAT" in st or "[TALIMAT" in st.upper():
            continue
        if "TALÄ°MAT" in st or "Ã–NCELÄ°KLÄ°" in st:
            continue
        low = st.lower()
        # Küçük modellerin talimatı cevap diye yazması (2026-10-03).
        if "bu soruya" in low and (
            "yanıt ver" in low or "yanit ver" in low or "cevap ver" in low
        ):
            continue
        if "genel sohbet turunda" in low or "doğal ve akıcı bir şekilde yanıt" in low:
            continue
        if "kullanıcının sorusunu aynen kopyala" in low or "kullanicinin sorusunu aynen kopyala" in low:
            continue
        if re.match(r"(?i)^\[(?:faz|talimat|sistem|dahili)", st):
            continue
        # Ajan / sistem rol sızıntısı
        if "sen yalnızca metin basan" in low or "sen yalnizca metin basan" in low:
            continue
        if "rüzgar temsilcisisin" in low or "ruzgar temsilcisisin" in low:
            continue
        if "önce düşün, sonra üret" in low or "once dusun, sonra uret" in low:
            continue
        if re.search(r"(?i)bilgi\s+turu", st):
            continue
        if re.match(r"(?i)^(?:niyet|güven|guven)\s*:", st):
            continue
        out_lines.append(ln)
    t = "\n".join(out_lines).strip()
    # Tek paragraf sızıntısı (satır kırığı yokken)
    if t and "bu soruya" in t.lower() and "yanıt ver" in t.lower() and len(t) < 400:
        if "kaynar" not in t.lower() and "nedir" not in t.lower():
            # Tamamen talimat gibi görünüyorsa boşalt — üst katman yeniden üretir / miss der.
            if "ümit abi" not in t.lower() and not re.search(r"\d+\s*derece", t.lower()):
                return ""
    return t
