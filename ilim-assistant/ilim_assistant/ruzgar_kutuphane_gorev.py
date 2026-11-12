# -*- coding: utf-8 -*-
"""Rüzgar — kütüphane görev sözleşmesi (TÜM katmanlar).

Mimar kuralı:
- Ne sorulursa sorulsun: önce yerel kütüphane indeksi (Şamile, bilgisayar rafları,
  ayıklama, ana RAG — yarın eklenecek eserler de aynı indeks yoluna girer).
- Kaynak istenmezse: müteber pasajdan doğru anlat/özetle; uydurma yok.
- Kaynak istenirse: eser/yol/bölüm/no/sayfa (yalnızca bağlamda görünen).
- İndekste yoksa: öğret cümlesi — model serbest uydurmasın.
- Eser adı sabit listesi YOK; kural indekse bağlıdır, yeni yüklemeler otomatik kapsanır.

Kapat: RUZGAR_KUTUPHANE_GOREV=0
"""
from __future__ import annotations

import os
import re
import unicodedata
from typing import Sequence


def _fold(s: str) -> str:
    """Türkçe dahil ASCII katlama — ı/İ NFKD ile düşmez."""
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("ı", "i").replace("İ", "i")
    return t.lower().strip()


_STOP = frozenset(
    """
    bir bu su o ve veya ile icin icin mi mi mu mu ne nasil nasil nedir
    anlat soyle soyle ver bak hakkinda hakkinda olan olarak kadar daha
    en cok cok kisa kisa uzun biraz bana abi umit umit
    the a an of to in on for is are was were
    """.split()
)

# Soru kalıbı — içerik tokenı değil (metinde «kimdir» aranmaz)
_QPART = frozenset(
    """
    nedir kimdir nasil neden nicin niye demek acikla ozet ozetle anlat
    tanimla ornek farki karsilastir hangi kac ne zaman
    bin ibn binti bint ebu abu
    """.split()
)

# Latin isim → Arapça köprü (Şamile metninde örtüşme)
_NAME_AR: dict[str, tuple[str, ...]] = {
    "muhammed": ("محمد", "رسول", "النبي", "أحمد"),
    "peygamber": ("محمد", "رسول", "النبي"),
    "ebubekir": ("ابوبكر", "أبو بكر", "بكر", "الصديق", "صديق"),
    "omer": ("عمر", "فاروق", "الخطاب"),
    "osman": ("عثمان", "عفان", "النورين"),
    "ali": ("علي", "طالب", "المرتضى"),
    "hatice": ("خديجة",),
    "aise": ("عائشة", "عائشه"),
    "ayse": ("عائشة", "عائشه"),
    "hamza": ("حمزة",),
    "halid": ("خالد",),
    "velid": ("وليد", "الوليد"),
    "bin": (),  # soyadı bağlacı — içerik sayılmaz
}


def _token_in_blob(tok: str, blob_f: str, blob_raw: str) -> bool:
    if tok in blob_f or tok in blob_raw:
        return True
    for ar in _NAME_AR.get(tok, ()):
        if ar in blob_raw:
            return True
    return False


def _is_pure_social(low: str) -> bool:
    if re.fullmatch(
        r"(?:selam|selamunaleykum|merhaba|naber|ne\s+haber|nasilsin|iyi\s+misin|"
        r"tesekkur|tesekkurler|sagol|eyvallah|rica\s+ederim|iyi\s+geceler|"
        r"gunaydin|iyi\s+aksamlar|hosca\s+kal|gorusuruz)[\s!.?]*",
        low,
    ):
        return True
    if len(low) <= 24 and re.fullmatch(
        r"(?:selam|merhaba|naber|nasilsin)(?:\s+ruzgar)?[\s!.?]*",
        low,
    ):
        return True
    return False


def _is_work_or_control(low: str, raw: str) -> bool:
    """Sohbet bilgi sorusu değil — komut / görev / hatırla."""
    if re.match(r"^\s*(?:hatirla|hatırla)\s*:", raw, re.I):
        return True
    if re.match(r"^\s*(?:gorev|görev)\s*:", raw, re.I):
        return True
    if re.match(r"^\s*/", raw):
        return True
    if re.search(
        r"\b(?:commit|push|pytest|refactor|force\s*restart|restart\s+et)\b",
        low,
    ) and not re.search(r"\b(?:nedir|ne\s+demek|acikla|açıkla)\b", low):
        return True
    return False


def is_kutuphane_bilgi_soru(message: str) -> bool:
    """Tüm katmanlar: bilgi isteyen soru → kütüphane sözleşmesi.

    Eser/raf adı sabitlenmez; yarın yüklenen eserler indeks + bu tetikleyici ile kapsanır.
    """
    raw = (message or "").strip()
    low = _fold(raw)
    if not low or len(low) < 3:
        return False
    if _is_pure_social(low):
        return False
    if _is_work_or_control(low, raw):
        return False

    # Soru işareti + anlamlı uzunluk → bilgi
    if "?" in raw or "؟" in raw:
        if len(low) >= 6:
            return True

    # Bilgi kalıpları (alan bağımsız)
    info_patterns = (
        r"\bnedir\b",
        r"\bne\s+demek\b",
        r"\bkimdir\b",
        r"\bne\s+zaman\b",
        r"\bneden\b",
        r"\bnicin\b",
        r"\bniçin\b",
        r"\bnasil\b",
        r"\bnasıl\b",
        r"\bacikla\b",
        r"\baçıkla\b",
        r"\bozet\b",
        r"\bözet\b",
        r"\banlat\b",
        r"\btanimla\b",
        r"\btanımla\b",
        r"\bfarki\b",
        r"\bfarkı\b",
        r"\bkarsilastir\b",
        r"\bkarşılaştır\b",
        r"\bornek\b",
        r"\börnek\b",
        r"\bkaynak\b",
        r"\beser\b",
        r"\bkitap\b",
        r"\bkutuphane\b",
        r"\bkütüphane\b",
        r"\binds?eks\b",
        r"\braf\b",
    )
    if any(re.search(p, low) for p in info_patterns):
        return True

    # Orta-uzun cümle: konu anlatımı / soru niyeti
    if len(low) >= 18 and re.search(
        r"\b(?:hakkinda|hakkında|ile\s+ilgili|konusunda|uzerine|üzerine)\b",
        low,
    ):
        return True

    return False


def user_wants_kaynak(message: str) -> bool:
    low = _fold(message)
    return any(
        k in low
        for k in (
            "kaynak",
            "kaynagi",
            "kaynağı",
            "referans",
            "atif",
            "atıf",
            "hangi kitap",
            "hangi eser",
            "cilt",
            "sayfa",
            "hadis no",
            "numara",
            "nereden",
            "goster",
            "göster",
            "belge",
            "dipnot",
            "link ver",
            "künye",
            "kunye",
        )
    )


def expand_kutuphane_search_query(message: str) -> str:
    """Arama metnini güçlendir — sabit eser kataloğu yok; dil/anahtar ipuçları.

    Yarın yeni eser yüklense de aynı fonksiyon çalışır (indeks içeriği değişir).
    """
    raw = (message or "").strip()
    low = _fold(raw)
    extra: list[str] = []
    # İlim: bilinen kısa Arapça köprüler (eser listesi değil)
    if "niyet" in low and any(k in low for k in ("hadis", "buhari", "sahih", "amal", "amel")):
        extra.extend(["إنما الأعمال بالنيات", "الأعمال بالنيات", "نية", "نيّة"])
    if "tefsir" in low:
        extra.append("تفسير")
    if "hadis" in low and "buhari" in low:
        extra.append("صحيح البخاري")
    if "muhammed" in low or "peygamber" in low:
        extra.extend(["محمد رسول الله", "سيرة", "النبي"])
    if "ebubekir" in low or "ebu bekir" in low or "siddiq" in low or "siddik" in low:
        extra.extend(["أبو بكر الصديق", "ابوبكر"])
    if "omer" in low and ("kimdir" in low or "hz" in low or "halife" in low):
        extra.extend(["عمر بن الخطاب", "الفاروق"])
    if "osman" in low and ("kimdir" in low or "hz" in low or "halife" in low):
        extra.extend(["عثمان بن عفان", "ذي النورين"])
    if re.search(r"\bali\b", low) and ("kimdir" in low or "hz" in low or "halife" in low):
        extra.extend(["علي بن أبي طالب"])
    if "halid" in low and "velid" in low:
        extra.extend(["خالد بن الوليد", "سيف الله"])
    if "fikh" in low or "fikih" in low:
        extra.append("فقه")
    if not extra:
        return raw
    return raw + " | " + " ".join(extra)


# Geriye uyum
def expand_ilim_search_query(message: str) -> str:
    return expand_kutuphane_search_query(message)


def _query_tokens(message: str) -> list[str]:
    """İçerik tokenları — nedir/kimdir gibi soru ekleri elenir."""
    low = _fold(message)
    ar = re.findall(r"[\u0600-\u06FF]{3,}", message or "")
    toks = re.findall(r"[a-z0-9']{3,}", low)
    out: list[str] = []
    for t in toks:
        if t in _STOP or t in _QPART or len(t) < 3:
            continue
        if t not in out:
            out.append(t)
    for t in ar:
        if t not in out:
            out.append(t)
    if "niyet" in low:
        for h in ("نية", "نيات", "بالنيات", "الاعمال", "الأعمال"):
            if h not in out:
                out.append(h)
    # Arapça köprü tokenları buraya eklenmez — anlık kart örtüşmesini bozar;
    # arama genişletmesi expand_kutuphane_search_query'de.
    return out[:28]


def filter_hits_lexically(
    query: str,
    hits: Sequence[tuple[str, str, float]],
    *,
    min_score_keep: float = 0.70,
) -> list[tuple[str, str, float]]:
    """Soruyla örtüşmeyen parçaları ele — alan/eser bağımsız.

    Çok sözcüklü soruda yalnız skor yetmez: en az bir içerik örtüşmesi şart
    (yüksek skorlu yanlış raf → uydurma LLM yolu kapanır).
    """
    if not hits:
        return []
    toks = _query_tokens(query)
    low = _fold(query)
    kimdir_q = "kimdir" in low or "kim idi" in low
    if not toks:
        kept0 = list(hits)
    else:
        multi = len(toks) >= 2
        kept0 = []
        for text, src, sc in hits:
            blob_f = _fold(f"{text}\n{src}")
            blob_raw = f"{text}\n{src}"
            overlap = sum(1 for t in toks if _token_in_blob(t, blob_f, blob_raw))
            if multi:
                if overlap >= 2 or (overlap >= 1 and float(sc) >= 0.88):
                    kept0.append((text, src, float(sc)))
            elif overlap >= 1:
                # kimdir: skor yetmez — isim metinde/ Arapça köprüde olmalı
                kept0.append((text, src, float(sc)))
            elif (not kimdir_q) and float(sc) >= min_score_keep:
                kept0.append((text, src, float(sc)))

    # Peygamber / kimdir: usul «İmam Muhammed» gürültüsünü kes; siyer rafını öne al
    prophet_q = (
        ("muhammed" in low or "peygamber" in low or "resulullah" in low)
        and "imam" not in low
    )
    if not (prophet_q or kimdir_q):
        return kept0

    cleaned: list[tuple[str, str, float]] = []
    for text, src, sc in kept0:
        blob = _fold(f"{text}\n{src}")
        src_l = _fold(src)
        blob_raw = f"{text}\n{src}"
        # «Halid bin Velid» ≠ «خالد بن يزيد»
        if "halid" in low and "velid" in low:
            if "الوليد" not in blob_raw and "بن الوليد" not in blob_raw:
                if "وليد" not in blob_raw:
                    continue
                if "يزيد" in blob_raw and "الوليد" not in blob_raw:
                    continue
        if prophet_q and (
            "serahsi" in blob
            or "usulu" in src_l
            or "/usul" in src_l
            or "11_usul" in src_l
            or (
                "imam muhammed" in blob
                and "resul" not in blob
                and "peygamber" not in blob
                and "رسول" not in (text or "")
            )
        ):
            continue
        boost = 0.0
        if any(
            x in src_l
            for x in (
                "24_siyer",
                "26_teracim",
                "25_tarih",
                "08_siyer",
                "/siyer",
                "tabakat",
                "teracim",
            )
        ):
            boost = 0.06
        cleaned.append((text, src, float(sc) + boost))
    cleaned.sort(key=lambda h: h[2], reverse=True)
    return cleaned if cleaned else kept0


def hits_usable_for_kutuphane(
    query: str,
    hits: Sequence[tuple[str, str, float]],
) -> bool:
    """İndeks isabeti soruyu gerçekten taşıyor mu — yoksa öğret cümlesi."""
    if not hits:
        return False
    toks = _query_tokens(query)
    if not toks:
        return True
    best = 0
    for text, src, _sc in hits[:8]:
        blob_f = _fold(f"{text}\n{src}")
        blob_raw = f"{text}\n{src}"
        best = max(best, sum(1 for t in toks if _token_in_blob(t, blob_f, blob_raw)))
    if len(toks) >= 2:
        return best >= 2
    return best >= 1


def blocks_usable_for_kutuphane(
    query: str,
    blocks: Sequence[tuple[str, str]],
) -> bool:
    """Bağlam blokları (raf/tefsir vb.) soruyla örtüşüyor mu."""
    if not blocks:
        return False
    toks = _query_tokens(query)
    if not toks:
        return True
    need = 2 if len(toks) >= 2 else 1
    blob_raw = "\n".join(f"{t}\n{s}" for t, s in list(blocks)[:12])
    blob_f = _fold(blob_raw)
    return sum(1 for t in toks if _token_in_blob(t, blob_f, blob_raw)) >= need


def kutuphane_enabled_hard() -> bool:
    return os.environ.get("RUZGAR_KUTUPHANE_GOREV", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def instant_covers_query(query: str, reply: str) -> bool:
    """Anlık kart soruyu gerçekten karşılıyor mu? (tüm raflar / yarınki eserler).

    «Python generator» sorusuna yalnız «Python dili» kartı basılmasın → RAG'e bırak.
    """
    reply_s = (reply or "").strip()
    if not reply_s:
        return False
    toks = _query_tokens(query)
    if len(toks) <= 1:
        return True
    blob = _fold(reply_s) + "\n" + reply_s
    covered = sum(1 for t in toks if t in blob)
    # İki+ anlamlı sözcükten en az ikisi kartta olsun; yoksa indeks yolu
    if len(toks) >= 2 and covered < 2:
        return False
    need = max(1, (len(toks) + 1) // 2)
    return covered >= need


def _looks_like_question_only_blob(text: str) -> bool:
    """Başlık/soru parçası — cevap diye basma."""
    t = " ".join((text or "").split()).strip()
    if not t:
        return True
    low = _fold(t)
    if len(t) < 90 and ("?" in t or "؟" in t):
        return True
    if re.search(
        r"(?:anlatacak\s+m[iı]s[iı]n|anlatir\s+m[iı]s[iı]n|ne\s+demektir|nedir\s*\?)\s*$",
        low,
    ):
        return True
    # Tek cümle soru
    if t.count("?") == 1 and len(t) < 160 and not re.search(
        r"\b(?:yield|def |class |function|return|örnek|ornek|yani)\b",
        low,
    ):
        return True
    return False


def format_kutuphane_extractive_reply(
    query: str,
    hits: Sequence[tuple[str, str, float]] | None = None,
    blocks: Sequence[tuple[str, str]] | None = None,
    *,
    want_source: bool = False,
) -> str:
    """LLM yok — indeksteki pasajı oku, anlat. Uydurma kapalı; yarınki eserler aynı yol."""
    pieces: list[tuple[str, str]] = []
    for text, src, _sc in list(hits or [])[:8]:
        t = " ".join((text or "").split())
        if len(t) >= 40 and not _looks_like_question_only_blob(t):
            pieces.append((t[:1100], str(src or "").strip()))
    if not pieces:
        for text, src in list(blocks or [])[:8]:
            t = " ".join((text or "").split())
            if len(t) >= 40 and not _looks_like_question_only_blob(t):
                pieces.append((t[:1100], str(src or "").strip()))
    if not pieces:
        return (
            "Ümit abi, bu sorunun cevabını bulamadım. Bana öğretir misin?"
        )
    toks = _query_tokens(query)
    # En örtüşen pasajı öne al
    def _ov(p: tuple[str, str]) -> int:
        blob = _fold(p[0] + "\n" + p[1])
        return sum(1 for t in toks if t in blob)

    pieces.sort(key=_ov, reverse=True)
    body = pieces[0][0]
    lines = [
        "Ümit abi — kütüphaneden okuduğum pasaj şöyle:",
        "",
        body,
    ]
    if want_source:
        lines.append("")
        lines.append("**Kaynak izi:**")
        seen: set[str] = set()
        for i, (_t, src) in enumerate(pieces[:4], 1):
            if not src or src in seen:
                continue
            seen.add(src)
            lines.append(f"[K{i}] {src}")
    return "\n".join(lines).strip()


def grounding_directive(*, want_source: bool, source_count: int) -> str:
    """Tüm katmanlar — soft sohbet uydurmayı ezer. Eser listesine bağlı değil."""
    if source_count <= 0:
        return (
            "\n\n[TALİMAT — KÜTÜPHANE GÖREV — İNDEKS İSABETİ YOK]\n"
            "Bu tur **kütüphane bilgi sorusu**. Yerel indekste (tüm raflar/Şamile/ayıklama) "
            "kullanılabilir parça yok. Metin, sayı, alıntı, sayfa, eser künyesi **UYDURMA**. "
            "Tek cümle: «Ümit abi, bu sorunun cevabını bulamadım. Bana öğretir misin?»\n"
        )
    lines = [
        "\n\n[TALİMAT — KÜTÜPHANE GÖREV — TÜM KATMANLAR — ZORUNLU]\n",
        f"Bağlamda **{source_count}** yerel kütüphane parçası var ([K1]…). "
        "Bunlar Rüzgar indeksindeki eserlerden gelir (ilim, bilgisayar, fen, ayıklama — "
        "hangi raf doluysa). Cevabını **yalnızca bunlara** dayandır.\n",
        "- Üslup: Ümit abi ile **sohbet eder gibi** anlat. Ders kitabı, kart okuma, "
        "«kütüphaneden okuduğum pasaj şöyle» şablonu yok; doğrudan konuya gir.\n",
        "- Bağlamda olmayan alıntı, sayı, sayfa, cilt, yazar, hadis/ayet, boy/özel isim **uydurma**.\n",
        "- Özel isimleri bağlamdaki harf harf yaz (örn. Kınık ≠ Sınık); yanlış okuma yasak.\n",
        "- Bağlam soruyu karşılamıyorsa öğret cümlesini kullan; genel model bilginle doldurma.\n",
        "- Yarın eklenecek eserler de aynı kurala tabidir: yalnızca bağlamdaki pasaj.\n",
        "- Derin çekirdek eserlerde sayfa/satır atlama yok: oku → analiz et → sohbet dilinde anlat.\n",
    ]
    if want_source:
        lines.append(
            "- Kullanıcı **kaynak istedi**: net göster — eser/yol; mümkünse bölüm, numara, "
            "sayfa (**yalnızca bağlamda varsa**). Sonunda **Kaynak izi:** ile [K1]… listele.\n"
        )
    else:
        lines.append(
            "- Kullanıcı kaynak istemedi: müteber pasajdan **doğal sohbet dilinde anlat**; "
            "zorunlu [K1] listesi / «Güven:» satırı yazma. Uydurma yine yasak.\n"
        )
    return "".join(lines)
