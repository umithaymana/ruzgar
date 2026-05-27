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


def finalize_assistant_reply(raw: str) -> str:
    """Mojibake onarımı, sızan talimat temizliği, sabit karşılama kırpma."""
    t = repair_utf8_mojibake(raw or "")
    t = scrub_leaked_instructions(t)
    t = strip_wake_greeting_echo(t)
    t = strip_hafiza_robot_phrasing(t)
    return t.strip()


def scrub_leaked_instructions(text: str) -> str:
    """
    Model bazen kullanıcı mesajında sistem köşeli etiketlerini ([TALİMAT …]) kopyalar.
    Bu satırları çıkarır (asıl içerik silinmez).
    """
    if not text:
        return text
    out_lines: list[str] = []
    for ln in text.split("\n"):
        st = ln.strip()
        if "[TALİMAT" in st or "[TALIMAT" in st.upper():
            continue
        if "TALÄ°MAT" in st or "Ã–NCELÄ°KLÄ°" in st:
            continue
        out_lines.append(ln)
    return "\n".join(out_lines).strip()
