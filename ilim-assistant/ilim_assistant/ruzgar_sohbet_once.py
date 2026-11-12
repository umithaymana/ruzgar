# Created by Ümit & Gökçenur
"""
Rüzgar — Sohbet önce (Mimar emri 2026-11-12).

Varsayılan: insan gibi sohbet. Dosya / video / panel / masa işi yalnız net emirde.
Bilgi (kütüphane dahil, tüm konular) sohbet dilinde anlatılır; konu kilidi yok.

Kapat: RUZGAR_SOHBET_ONCE=0
"""

from __future__ import annotations

import os
import re
import unicodedata

VERSION = "ruzgar-sohbet-once-v1-2026-11-12"


def sohbet_once_enabled() -> bool:
    return os.environ.get("RUZGAR_SOHBET_ONCE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("İ", "i").replace("I", "i").lower()
    for a, b in (
        ("ı", "i"),
        ("ğ", "g"),
        ("ü", "u"),
        ("ş", "s"),
        ("ö", "o"),
        ("ç", "c"),
    ):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip()


def is_net_is_emri(message: str) -> bool:
    """
    Açık iş emri — sohbet değil.
    Şüphede False (sohbette kal).
    """
    raw = (message or "").strip()
    if not raw:
        return False
    low = _fold(raw)

    # Bilgi / sohbet sorusu — asla iş emri sayma
    if re.search(
        r"\b(?:nedir|kimdir|ne\s+demek|anlat|acikla|hakkinda|ozetle|"
        r"konusalim|sohbet|sence|ne\s+dersin|bilgi\s+ver|ogret)\b",
        low,
    ):
        # «kaynağını yaz» bilgi; «dosyaya yaz» iş
        if not re.search(r"\b(?:dosyaya|belgeye|hucreye|sayfaya|klasore)\s+yaz\b", low):
            if re.search(
                r"\b(?:tefsir|fik[iı]h|hadis|siyer|tarih|kutuphane|kaynak|eser|"
                r"fetret|islam|osmanli|ayet|meal)\b",
                low,
            ) or re.search(r"\b(?:nedir|kimdir|anlat|konusalim|sohbet)\b", low):
                return False

    if re.match(r"^eylem\s", low):
        return True
    if re.match(r"^(?:gorev|görev|is|iş|yap)\s*:", raw, flags=re.I):
        return True
    if re.search(r"https?://|youtube\.com|youtu\.be", low) and re.search(
        r"\b(?:indir|download|oynat|kes|trim|panel)\b", low
    ):
        return True
    if re.search(
        r"\b(?:dosyaya\s+yaz|belgeye\s+yaz|hucreye\s+yaz|dosyaya\s+ekle|"
        r"klasordekileri\s+say|sayfa\s+yap|projeyi\s+goster)\b",
        low,
    ):
        return True
    if re.search(
        r"\b(?:indir|download|kes\b|trim\b|oynat\b|ffprobe|kurgu\s+yap|"
        r"donustur|dönüştür)\b",
        low,
    ) and re.search(r"\b(?:video|youtube|sinema|film|klip|shorts)\b", low):
        return True
    # Kısa onay / uygulama emri (plan sonrası «yap»)
    if re.match(
        r"^(?:tamam[,.]?\s+)?(?:yap|uygula|kaydet|baslat|basla)\s*[.!]*$",
        low,
    ):
        return True
    if re.match(r"^(?:bunu|onu|sunu|şunu)\s+(?:yap|uygula|kaydet)\b", low):
        return True
    if re.match(r"^(?:yapma|yap\s+ma|iptal|vazgec|vazgeç)\s*[.!]*$", low):
        return True
    if re.search(r"\b(?:programlamada|kodda|atolyede|atölyede)\s*:", low):
        return True
    return False


def prefer_sohbet(message: str) -> bool:
    """Sohbet önce açıkken: net emir yoksa sohbet."""
    if not sohbet_once_enabled():
        return False
    return not is_net_is_emri(message)


def sohbet_once_bilgi_dil_directive() -> str:
    """Tüm konular — kütüphane/indeks bilgisi sohbet dilinde."""
    if not sohbet_once_enabled():
        return ""
    return (
        "\n\n[TALİMAT — SOHBET ÖNCE / BİLGİ DİLİ]\n"
        "Ümit abi ile **insan gibi sohbet et**. Konu ne olursa olsun aynı sıcak dil.\n"
        "- «…hakkında sohbet edelim / konuşalım» derse: hemen kabul et, konuya gir, "
        "kısa bir kapı aç (nereden girelim diye nazikçe sor). Örnek üslup: "
        "«Olur Ümit abi, İslam tarihinden konuşalım. Neresinden girelim — "
        "Mekke günleri mi, Hulefa mi, yoksa aklında başka bir yer mi var?»\n"
        "- «Haberdar oldum», «Bu tur için öncelik sırası», RAG, İnternet özeti, "
        "sistem/motor listesi, «nasıl yardımcı olabilirim» — **yasak**.\n"
        "- Kütüphane/indeks bilgisi varsa ders kitabı gibi değil; sohbet edercesine anlat. "
        "Uydurma yasak; yalnızca bağlama dayan.\n"
        "- Kaynak istemediyse zorunlu kaynak listesi / «Güven:» yazma.\n"
        "- Dosya/video/panel işine yalnız açık «yap / yaz / indir» emrinde geç.\n"
    )


def sohbet_once_hub_stay(message: str) -> bool:
    """Hub: yardımcı motora kaçırma."""
    return prefer_sohbet(message)


def sohbet_once_selam_dinle_directive(message: str) -> str:
    """Kısa selam / nasılsın — kart okuma, dinle ve yanıtla."""
    if not sohbet_once_enabled():
        return ""
    low = _fold(message or "")
    if not re.search(
        r"^(?:selam|merhaba|slm|hey|naber|ne\s+haber|nasilsin|iyi\s+misin|"
        r"gunaydin|iyi\s+aksam|iyi\s+geceler)(?:\s|$|[!.?])",
        low,
    ) and not re.match(r"^(?:selam|merhaba)(?:\s+ruzgar)?\s*$", low):
        return ""
    return (
        "\n\n[TALİMAT — SOHBET ÖNCE / SELAM]\n"
        "Bu tur kısa selam veya hal hatır. Hafızadan ezber kart okuma. "
        "Ümit abi’yi dinlemiş gibi doğal, sıcak cevap ver; hazır şablon yok. "
        "İstersen kısaca halini sor; «öncelik sırası / RAG» yazma.\n"
    )
