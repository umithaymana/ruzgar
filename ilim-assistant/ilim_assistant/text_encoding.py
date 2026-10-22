"""UTF-8 içeriğin Latin-1 / Windows-1252 gibi yanlış kod çözülmesinden doğan mojibake onarımı."""

from __future__ import annotations

import os
import re


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


def strip_web_capability_noise(text: str) -> str:
    """Web cevabındaki «yeteneğimle buldum / görünmez yanıt» meta gürültüsünü kes."""
    if not text:
        return text
    import re

    t = text
    # Soru başlığı olarak markdown yankı
    t = re.sub(r"(?m)^\*{0,2}.{8,120}\?\*{0,2}\s*\n+", "", t, count=1)
    drop_frags = (
        r"görünmez bir yanıt[^.]*\.?",
        r"gorunmez bir yanit[^.]*\.?",
        r"web sorgulama yetene[gğ]imle[^.]*\.?",
        r"web sorgulamas[ıi] yap[ıi]ld[ıi][^.]*\.?",
        r"bilgi için web sorgulamas[ıi][^.]*\.?",
        r"bu sorunun cevab[ıi],\s*soruldu[gğ]unda[^.]*\.?",
        r"ilgili bilgilerimden do[gğ]rudan elde edilemedi[^.]*\.?",
        r"kullan[ıi]c[ıi]ya bu bilgiyi soruldu[gğ]unda[^.!\n]*[.!]?",
        r"webten\s+bakarak[^.]*\.?",
        r"web['’]?\s*den\s+bakarak[^.]*\.?",
        r"internetten\s+bakarak[^.]*\.?",
        r"arama\s+yaparak\s+bu\s+bilgiye[^.]*\.?",
        r"bu\s+bilgiye\s+ula[sş]t[ıi]m\.?",
    )
    for pat in drop_frags:
        t = re.sub(pat, " ", t, flags=re.I)
    # --- sonrası meta blok
    t = re.sub(r"\n---\n[\s\S]*$", "", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def strip_rhetorical_self_question(text: str) -> str:
    """
    Küçük modeller «X hakkında ne düşünüyorum?» diye soruyu yankılayıp sonra tanıma geçer.
    ChatGPT tarzında ilk cümle gerçek cevap olmalı — bu yankıyı kes.
    """
    if not text:
        return text
    try:
        from ilim_assistant.prompts import sohbet_tarz_chatgpt

        if not sohbet_tarz_chatgpt():
            return text
    except Exception:
        return text
    import re

    t = text.lstrip()
    m = re.match(r"^([^.!\n]{6,180}\?)\s+", t)
    if not m:
        return text
    q = m.group(1).lower()
    cues = (
        "düşünüyor",
        "dusunuyor",
        "ne demek",
        "hakkında ne",
        "hakkinda ne",
        "nedir",
        "kimdir",
        "nasıl anlat",
        "nasil anlat",
    )
    if not any(c in q for c in cues):
        return text
    rest = t[m.end() :].lstrip()
    if len(rest) < 24:
        return text
    return rest


def strip_trust_and_faz_noise(text: str) -> str:
    """Güven damgası ve *Not (Faz …)* satırlarını sohbetten temizle."""
    if not text:
        return text
    import re

    t = text
    t = re.sub(r"(?im)^[ \t]*\*{0,2}G[uü]ven:\s*.*$", "", t)
    t = re.sub(r"\*{0,2}G[uü]ven:\s*[^*\n]*\*{0,2}[^\n]*", "", t)
    t = re.sub(r"(?im)^[ \t]*\*Not \(Faz [^)]+\):[^\n]*\*?\s*$", "", t)
    t = re.sub(r"\n+\*Not \(Faz [A-Z0-9]+\):[\s\S]*$", "", t)
    t = re.sub(r"\*Not \(Faz [^)]+\):[^\n]*", "", t)
    t = re.sub(r"\(Talimat:[^)]*\)", "", t, flags=re.I)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def cila_anlik_kart_prose(text: str) -> str:
    """
    Anlık kütüphane kartı (**başlık** + gövde + _dipnot_) → ChatGPT düzyazı (B5).
    Sohbet tarzı kapalıysa dokunma.
    """
    raw = (text or "").strip()
    if not raw.startswith("**"):
        return text
    try:
        from ilim_assistant.prompts import sohbet_tarz_chatgpt

        if not sohbet_tarz_chatgpt():
            return text
    except Exception:
        return text

    m = re.match(
        r"(?s)^\*\*([^*]+)\*\*\s*\n+(.*?)(?:\n+\s*_(.+?)_\s*)?\s*$",
        raw,
    )
    if not m:
        return text
    title = (m.group(1) or "").strip()
    body = (m.group(2) or "").strip()
    # Dipnot / raf etiketi düşer
    if not body:
        return text

    # «Fotosentez: …» tekrarını kır
    lead = re.match(r"^([^:\n]{2,48})\s*:\s+", body)
    if lead:
        lead_t = lead.group(1).strip().casefold()
        tit_cf = title.casefold()
        if lead_t == tit_cf or lead_t in tit_cf or tit_cf in lead_t:
            body = body[lead.end() :].strip()

    # İlk harf küçükse ve başlık biliniyorsa «Başlık, …» doğal açılış
    if body and title and not body.casefold().startswith(title.casefold()[: max(3, len(title) // 2)]):
        # «ışıkla…» → «Fotosentez, ışıkla…»
        if body[0].islower() or (body[0].isalpha() and title[0].isupper()):
            nice = title[:1].upper() + title[1:] if title else title
            # Başlık zaten cümlede geçiyorsa ekleme
            if nice.casefold() not in body[:80].casefold():
                body = f"{nice}, {body[0].lower() + body[1:] if body[0].isupper() else body}"

    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return body or text


def finalize_assistant_reply(raw: str, *, channel: str = "") -> str:
    """Mojibake onarımı, sızan talimat temizliği, sabit karşılama kırpma, Tek Ses (Faz B)."""
    t = repair_utf8_mojibake(raw or "")
    t = strip_answer_scaffold(t)
    t = scrub_leaked_instructions(t)
    t = strip_wake_greeting_echo(t)
    t = strip_hafiza_robot_phrasing(t)
    t = strip_web_capability_noise(t)
    t = strip_rhetorical_self_question(t)
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

    t = strip_trust_and_faz_noise(t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = cila_anlik_kart_prose(t)
    t = cila_sohbet_metni(t)
    return t.strip()


_SES_KART_SATIRI = re.compile(
    r"(?im)^\s*\[(?:edip|alim|âlim|asistan|tecvid)\b[^\n]*\n?"
)
_TEKRAR_SATIRI = re.compile(r"(?im)^\s*\[[^\n]*tekrar etme[^\n]*\n?")
_REFERANS_SATIRI = re.compile(r"(?im)^\s*referans\s*\([^\n]*\n?")
# 17000 / 17.000 / 17 bin / 17.000'den fazla özel okul
_OKUL_SAYISI = re.compile(
    r"(?i)(?:\d{1,3}(?:[.\s]\d{3})+|\d{4,}|\d{1,3}\s*bin)\s*"
    r"(?:['’]?\s*den\s+fazla\s+)?(?:özel|ozel)\s+okul"
)
_OKUL_KAYNAK_OK = re.compile(
    r"(?i)(?:meb\.gov|tuik\.gov|tüik\.gov|www\.meb|resmi\s+istatistik|"
    r"mill[iı]\s+e[gğ]itim)"
)
# 209 üniversite / 200'den fazla üniversite — kaynaksız uydurma (B3)
_UNI_SAYISI = re.compile(
    r"(?i)(?:\d{1,3}(?:[.\s]\d{3})*|\d{2,4}|\d{1,3}\s*bin)\s*"
    r"(?:['’]?\s*den\s+fazla\s+)?(?:üniversite|universite)"
)
_UNI_KAYNAK_OK = re.compile(
    r"(?i)(?:y[oö]k\.gov|www\.y[oö]k|y[oö]k\s+istatistik|y[oö]k\s+atlas|"
    r"y[uü]ksek[öo][gğ]retim\s+kurulu|resmi\s+y[oö]k)"
)
_CUMLE_AYIR = re.compile(r"(?<=[.!?])\s+")
_OKUL_YOK = (
    "Ümit abi, özel okul için net resmi rakamı güvenilir kaynaktan çıkaramadım; "
    "sayı uydurmam. MEB veya TÜİK istatistiğine bakmak daha doğru."
)
_UNI_YOK = (
    "Ümit abi, Türkiye'deki üniversite sayısı için net resmi rakamı güvenilir "
    "kaynaktan çıkaramadım; sayı uydurmam. YÖK istatistiğine bakmak daha doğru."
)


def _cila_kat(parca: str) -> str:
    return re.sub(r"\s+", " ", parca).strip().lower()


def _cila_kaynaksiz_sayi(
    text: str,
    *,
    sayi_re: re.Pattern[str],
    kaynak_re: re.Pattern[str],
    yok_msg: str,
) -> str:
    if not text or not sayi_re.search(text):
        return text
    if kaynak_re.search(text):
        return text
    yeni: list[str] = []
    kondu = False
    for cumle in _CUMLE_AYIR.split(text):
        kat = _cila_kat(cumle)
        if not kat or (yeni and kat == _cila_kat(yeni[-1])):
            continue
        if sayi_re.search(cumle):
            if not kondu:
                yeni.append(yok_msg)
                kondu = True
            continue
        yeni.append(cumle.strip())
    return " ".join(yeni).strip()


def cila_sohbet_metni(text: str) -> str:
    """Ses kartı, tekrar talimatı, aynı paragraf ve kaynaksız okul/üniversite sayısı cevapta kalmaz."""
    if not text:
        return text
    t = _SES_KART_SATIRI.sub("", text)
    t = _TEKRAR_SATIRI.sub("", t)
    t = _REFERANS_SATIRI.sub("", t)
    satirlar: list[str] = []
    once = ""
    for satir in t.splitlines():
        kat = _cila_kat(satir)
        if not kat:
            if satirlar and satirlar[-1] != "":
                satirlar.append("")
            continue
        if kat == once:
            continue
        satirlar.append(satir.strip())
        once = kat
    t = "\n".join(satirlar).strip()
    if not t:
        return t
    t = _cila_kaynaksiz_sayi(
        t, sayi_re=_OKUL_SAYISI, kaynak_re=_OKUL_KAYNAK_OK, yok_msg=_OKUL_YOK
    )
    t = _cila_kaynaksiz_sayi(
        t, sayi_re=_UNI_SAYISI, kaynak_re=_UNI_KAYNAK_OK, yok_msg=_UNI_YOK
    )
    # S3 — fx / skor / nüfus / ilçe geniş scrub
    try:
        from ilim_assistant.sohbet_sayi_hard_gate import scrub_ungrounded_live_numbers

        t = scrub_ungrounded_live_numbers(t)
    except Exception:
        pass
    return t


def strip_answer_scaffold(text: str) -> str:
    """Modelin «Niyet / Cevap / Gerekçe» şablonunu kullanıcıya bırakma.

    ``**Niyet:**`` ve yalnız ``Soru:`` / ``Cevap:`` yankısı da temizlenir (C1).
    """
    if not text:
        return text
    import re

    def _bare_label(st: str) -> str:
        t = (st or "").strip()
        t = re.sub(r"^\*{1,2}\s*", "", t)
        t = re.sub(r"\s*\*{1,2}\s*$", "", t)
        return t.strip()

    label = re.compile(
        r"(?i)^(?:niyet|kimlik(?:/yakınlık)?|üretim|uretim|sevinç|sevinc|soru)\s*:"
    )
    stop = re.compile(r"(?i)^(?:örnek|ornek|gerekçe|gerekce)\s*:")
    cevap_re = re.compile(r"(?i)^cevap\s*:")
    has_scaffold = False
    for ln in text.splitlines():
        st = _bare_label(ln)
        if label.match(st) or cevap_re.match(st):
            has_scaffold = True
            break
    if not has_scaffold:
        return text
    body: list[str] = []
    capture = False
    saw = False
    for ln in text.splitlines():
        st = _bare_label(ln)
        if cevap_re.match(st):
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
    kept = [
        ln
        for ln in text.splitlines()
        if ln.strip() and not label.match(_bare_label(ln))
    ]
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
