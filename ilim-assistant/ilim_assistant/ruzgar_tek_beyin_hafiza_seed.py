# Created by Ümit & Gökçenur
"""Çekirdek kişisel profiller — ruzgar_genel_hafiza.json'a kalıcı tohum kayıtlar."""

from __future__ import annotations

import re
from typing import Any

_SEEDED = False

_GOKCENUR_ES_YANLIS = re.compile(
    r"(?:Mimar\s+)?Ümit(?:\s+Bey)?'?in\s+eşi|senin\s+eşin|eşi\s+ve\s+Rüzgar",
    re.I,
)


def sanitize_gokcenur_hafiza_cevap(cevap: str, *, soru: str = "") -> str:
    """Diskte kalmış yanlış «eşi» ifadelerini yalnızca Gökçenur profillerinde düzelt."""
    c = (cevap or "").strip()
    if not c:
        return c
    blob = f"{soru} {c}".lower()
    if re.search(r"\bemine\b", blob):
        return c
    if not re.search(r"g[oö]k[cç]enur|gokcenur|gokce\s*nur", blob, re.I):
        return c
    if not _GOKCENUR_ES_YANLIS.search(c):
        return c
    c = re.sub(
        r"(?:Mimar\s+)?Ümit(?:\s+Bey)?'?in\s+eşi\s+ve",
        "Mimar Ümit'in kızıdır;",
        c,
        flags=re.I,
    )
    c = re.sub(r"senin\s+eşin", "senin kızın", c, flags=re.I)
    c = re.sub(
        r"(?<!Mimar )Ümit(?:\s+Bey)?'?in\s+eşi\b",
        "Ümit'in kızı",
        c,
        flags=re.I,
    )
    return c.strip()


_EMINE_KIMDIR = (
    "Emine Haymana, Mimar Ümit'in eşidir ve çocuklarının annesidir."
)

_BUSENAZ_KIMDIR = (
    "Busenaz Haymana, Mimar Ümit'in kızıdır; Gökçenur'un kardeşi, senin diğer kızın."
)

_MERTCAN_KIMDIR = (
    "Mertcan Haymana, Mimar Ümit'in en büyük oğludur; yakında nişanı olacak."
)

_KARDELEN_KIMDIR = (
    "Kardelen, Mertcan Haymana'nın nişanlısıdır ve senin gelinindir."
)

_KIZ_KARDESLER_OZET = (
    "Emine Çiçek Haymana, Fadime Penekli Haymana, Süleyla Öztaş Haymana, "
    "Meryem Yıldırım Haymana, Melek Sarıgül Haymana, Filiz Haymana ve Hatice Haymana"
)

_BABA_KIMDIR = (
    "Zeki Haymana senin babandır; rahmetli oldu, vefat tarihi 19 Mayıs 1999."
)

_ANNE_KIMDIR = (
    "Şükriye Haymana senin annendir; rahmetli oldu, vefat tarihi 5 Haziran 1993."
)

_GOKCENUR_KIMDIR = (
    "Gökçenur Haymana, Mimar Ümit'in kızıdır ve Rüzgar projesinin mimarlarından biridir. "
    "Recep Tayyip Erdoğan Üniversitesi Bilgisayar Mühendisliği fakültesinde okuyor; "
    "teknik ve yaratıcı fikirleriyle projeye güç verir; seninle birlikte bu sistemi inşa ediyor."
)

_CORE_SEED_VERSION = "aile-genis-v1-2026-06-14"
_SEED_META_SORU = "__ruzgar_core_seed_version__"

_CORE_PROFILES: tuple[tuple[str, str], ...] = (
    (
        "Gökçenur kimdir",
        _GOKCENUR_KIMDIR,
    ),
    (
        "gökçenur kimdir",
        _GOKCENUR_KIMDIR,
    ),
    (
        "gökçe nur haymana kimdir",
        "Gökçenur Haymana, Mimar Ümit'in kızıdır ve Rüzgar projesinin mimarlarından biridir. "
        "Recep Tayyip Erdoğan Üniversitesi Bilgisayar Mühendisliği fakültesinde okuyor; "
        "teknik ve yaratıcı fikirleriyle projeye güç verir.",
    ),
    (
        "Gökçenur bu projede ne yapıyor",
        "Gökçenur senin kızın; Rüzgar projesinin mimarlarından biri olarak teknik ve yaratıcı "
        "fikirleriyle sisteme güç veriyor ve seninle birlikte geliştiriyor.",
    ),
    (
        "gökçenur eşim mi",
        "Hayır. Gökçenur Haymana senin kızındır, eşin değil; Rüzgar projesinin mimarlarından biridir.",
    ),
    (
        "gökçenur haymana nerede okuyor",
        "Gökçenur Haymana, Recep Tayyip Erdoğan Üniversitesi Bilgisayar Mühendisliği fakültesinde okuyor.",
    ),
    (
        "Emine Haymana kimdir",
        _EMINE_KIMDIR,
    ),
    (
        "emine haymana kimdir",
        _EMINE_KIMDIR,
    ),
    (
        "eşim emine kim",
        _EMINE_KIMDIR,
    ),
    (
        "emine kimdir",
        "Eşin Emine Haymana'dır. Kız kardeşin Emine Çiçek Haymana'dır — ikisi farklı kişiler.",
    ),
    (
        "eşim kim",
        "Emine Haymana senin eşin ve çocuklarınızın annesidir.",
    ),
    (
        "çocuklarımın annesi kim",
        "Emine Haymana, çocuklarınızın annesi ve senin eşindir.",
    ),
    (
        "Busenaz Haymana kimdir",
        _BUSENAZ_KIMDIR,
    ),
    (
        "busenaz haymana kimdir",
        _BUSENAZ_KIMDIR,
    ),
    (
        "busenaz kimdir",
        _BUSENAZ_KIMDIR,
    ),
    (
        "diğer kızım kim",
        "Busenaz Haymana senin diğer kızın; Gökçenur'un kardeşi.",
    ),
    (
        "kızlarım kim",
        "Kızların Gökçenur Haymana ile Busenaz Haymana; ikisi de senin kızların.",
    ),
    (
        "kizlarim kim",
        "Kızların Gökçenur Haymana ile Busenaz Haymana; ikisi de senin kızların.",
    ),
    (
        "Mertcan Haymana kimdir",
        _MERTCAN_KIMDIR,
    ),
    (
        "mertcan haymana kimdir",
        _MERTCAN_KIMDIR,
    ),
    (
        "mertcan kimdir",
        _MERTCAN_KIMDIR,
    ),
    (
        "en büyük oğlum kim",
        "Mertcan Haymana senin en büyük oğlun; yakında nişanı var.",
    ),
    (
        "en buyuk oglum kim",
        "Mertcan Haymana senin en büyük oğlun; yakında nişanı var.",
    ),
    (
        "oğlum kim",
        "Mertcan Haymana senin oğlun; en büyük çocuğun ve yakında nişanı olacak.",
    ),
    (
        "oglum kim",
        "Mertcan Haymana senin oğlun; en büyük çocuğun ve yakında nişanı olacak.",
    ),
    (
        "mertcanın nişanlısı kim",
        _KARDELEN_KIMDIR,
    ),
    (
        "mertcanin nisanlisi kim",
        _KARDELEN_KIMDIR,
    ),
    (
        "Kardelen kimdir",
        _KARDELEN_KIMDIR,
    ),
    (
        "kardelen kimdir",
        _KARDELEN_KIMDIR,
    ),
    (
        "kardelen kim",
        _KARDELEN_KIMDIR,
    ),
    (
        "gelinim kim",
        "Kardelen senin gelinin; Mertcan Haymana'nın nişanlısı.",
    ),
    (
        "gelinim kimdir",
        "Kardelen, Mertcan'ın nişanlısı ve senin gelinindir.",
    ),
    (
        "ailem kimler",
        "Eşin Emine Haymana; kızların Gökçenur ve Busenaz Haymana; oğlun Mertcan Haymana; "
        "gelinin Kardelen (Mertcan'ın nişanlısı).",
    ),
    (
        "çocuklarım kimler",
        "Çocukların: Mertcan Haymana (en büyük oğlun), Gökçenur Haymana ve Busenaz Haymana (kızların).",
    ),
    # — Anne-baba (yalnızca sorulunca; selam/gündelikte otomatik söylenmez)
    ("babam kim", _BABA_KIMDIR),
    ("babam kimdir", _BABA_KIMDIR),
    ("babamın adı ne", "Baban Zeki Haymana; rahmetli, vefatı 19 Mayıs 1999."),
    ("zeki haymana kimdir", _BABA_KIMDIR),
    ("babam ne zaman öldü", "Baban Zeki Haymana 19 Mayıs 1999'da vefat etti."),
    ("babam ne zaman vefat etti", "Baban Zeki Haymana 19 Mayıs 1999'da vefat etti."),
    ("annem kim", _ANNE_KIMDIR),
    ("annem kimdir", _ANNE_KIMDIR),
    ("annemin adı ne", "Annen Şükriye Haymana; rahmetli, vefatı 5 Haziran 1993."),
    ("şükriye haymana kimdir", _ANNE_KIMDIR),
    ("annem ne zaman öldü", "Annen Şükriye Haymana 5 Haziran 1993'te vefat etti."),
    ("annem ne zaman vefat etti", "Annen Şükriye Haymana 5 Haziran 1993'te vefat etti."),
    # — Erkek kardeşler
    (
        "Murat Haymana kimdir",
        "Murat Haymana senin erkek kardeşindir.",
    ),
    (
        "murat haymana kimdir",
        "Murat Haymana senin erkek kardeşindir.",
    ),
    (
        "murat kimdir",
        "Murat Haymana senin erkek kardeşindir.",
    ),
    (
        "Mesut Haymana kimdir",
        "Mesut Haymana senin erkek kardeşindir.",
    ),
    (
        "mesut haymana kimdir",
        "Mesut Haymana senin erkek kardeşindir.",
    ),
    (
        "mesut kimdir",
        "Mesut Haymana senin erkek kardeşindir.",
    ),
    (
        "erkek kardeşlerim kim",
        "Erkek kardeşlerin Murat Haymana ve Mesut Haymana.",
    ),
    (
        "erkek kardeslerim kim",
        "Erkek kardeşlerin Murat Haymana ve Mesut Haymana.",
    ),
    # — Kız kardeşler (7)
    (
        "Emine Çiçek Haymana kimdir",
        "Emine Çiçek Haymana senin kız kardeşindir; eşin Emine Haymana'dan ayrı — o senin eşindir.",
    ),
    (
        "emine çiçek haymana kimdir",
        "Emine Çiçek Haymana senin kız kardeşindir.",
    ),
    (
        "emine kız kardeşim kim",
        "Kız kardeşin Emine Çiçek Haymana'dır; eşin Emine Haymana ile karıştırma.",
    ),
    (
        "Fadime Penekli Haymana kimdir",
        "Fadime Penekli Haymana senin kız kardeşindir.",
    ),
    (
        "fadime penekli haymana kimdir",
        "Fadime Penekli Haymana senin kız kardeşindir.",
    ),
    (
        "fadime kimdir",
        "Fadime Penekli Haymana senin kız kardeşindir.",
    ),
    (
        "Süleyla Öztaş Haymana kimdir",
        "Süleyla Öztaş Haymana senin kız kardeşindir.",
    ),
    (
        "süleyla öztaş haymana kimdir",
        "Süleyla Öztaş Haymana senin kız kardeşindir.",
    ),
    (
        "süleyla kimdir",
        "Süleyla Öztaş Haymana senin kız kardeşindir.",
    ),
    (
        "Meryem Yıldırım Haymana kimdir",
        "Meryem Yıldırım Haymana senin kız kardeşindir.",
    ),
    (
        "meryem yıldırım haymana kimdir",
        "Meryem Yıldırım Haymana senin kız kardeşindir.",
    ),
    (
        "meryem kimdir",
        "Meryem Yıldırım Haymana senin kız kardeşindir.",
    ),
    (
        "Melek Sarıgül Haymana kimdir",
        "Melek Sarıgül Haymana senin kız kardeşindir.",
    ),
    (
        "melek sarıgül haymana kimdir",
        "Melek Sarıgül Haymana senin kız kardeşindir.",
    ),
    (
        "melek kimdir",
        "Melek Sarıgül Haymana senin kız kardeşindir.",
    ),
    (
        "Filiz Haymana kimdir",
        "Filiz Haymana senin kız kardeşindir.",
    ),
    (
        "filiz haymana kimdir",
        "Filiz Haymana senin kız kardeşindir.",
    ),
    (
        "filiz kimdir",
        "Filiz Haymana senin kız kardeşindir.",
    ),
    (
        "Hatice Haymana kimdir",
        "Hatice Haymana senin kız kardeşindir.",
    ),
    (
        "hatice haymana kimdir",
        "Hatice Haymana senin kız kardeşindir.",
    ),
    (
        "hatice kimdir",
        "Hatice Haymana senin kız kardeşindir.",
    ),
    (
        "kız kardeşlerim kim",
        f"Yedi kız kardeşin: {_KIZ_KARDESLER_OZET}.",
    ),
    (
        "kiz kardeslerim kim",
        f"Yedi kız kardeşin: {_KIZ_KARDESLER_OZET}.",
    ),
    (
        "kız kardeşlerim kimler",
        f"Kız kardeşlerin: {_KIZ_KARDESLER_OZET}.",
    ),
    (
        "kaç kız kardeşim var",
        "Yedi kız kardeşin var: Emine Çiçek, Fadime Penekli, Süleyla Öztaş, Meryem Yıldırım, "
        "Melek Sarıgül, Filiz ve Hatice Haymana.",
    ),
    (
        "kardeşlerim kim",
        "Kardeşlerin: erkek kardeşler Murat ve Mesut Haymana; kız kardeşlerin "
        f"{_KIZ_KARDESLER_OZET}.",
    ),
    (
        "kardeslerim kim",
        "Kardeşlerin: erkek kardeşler Murat ve Mesut Haymana; kız kardeşlerin "
        f"{_KIZ_KARDESLER_OZET}.",
    ),
    (
        "kaç kardeşim var",
        "Dokuz kardeşin var: Murat ve Mesut (erkek), bir de yedi kız kardeşin — "
        f"{_KIZ_KARDESLER_OZET}.",
    ),
    (
        "geniş ailem kimler",
        "Eşin Emine Haymana; çocukların Mertcan, Gökçenur, Busenaz; gelinin Kardelen; "
        "anne-baban Zeki ve Şükriye Haymana (rahmetli); kardeşlerin Murat, Mesut ve "
        f"yedi kız kardeşin ({_KIZ_KARDESLER_OZET}).",
    ),
    (
        "Yavuz Kara kimdir",
        "Yavuz Kara, Mimar Ümit Bey'in teyzesinin oğludur — yakın aile çevresinden, senin "
        "bildiğin biri; ansiklopedik bir isim değil.",
    ),
    (
        "yavuz kara kimdir",
        "Yavuz Kara, Mimar Ümit Bey'in teyzesinin oğludur — yakın aile çevresinden.",
    ),
    (
        "Ümit kimdir",
        "Ümit Bey, Rüzgar projesinin mimarı ve benim kullanıcım; eşi Emine Haymana, "
        "kızları Gökçenur ve Busenaz, oğlu Mertcan Haymana; gelini Kardelen ile birlikte "
        "bu süper asistanı geliştiriyor.",
    ),
    (
        "Rüzgar kimdir",
        "Ben Rüzgar; Mimar Ümit ve Gökçenur tarafından geliştirilen, kişiye özel süper asistanım. "
        "Sohbetlerini, projelerini ve hafızandaki bilgileri takip ederim.",
    ),
)


def ensure_core_hafiza_profiles() -> dict[str, Any]:
    """Çekirdek aile profilleri — sürüm değişince günceller; aynı sürümde tekrar yazmaz."""
    global _SEEDED
    if _SEEDED:
        return {"ok": True, "skipped": True}
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        motor = get_hafiza_motor()
        stored_version = ""
        for row in motor._kayitlar:
            if row.get("motor_tipi") == "Hafıza" and row.get("soru") == _SEED_META_SORU:
                stored_version = str(row.get("cevap") or "").strip()
                break
        if stored_version == _CORE_SEED_VERSION:
            _SEEDED = True
            return {"ok": True, "skipped": True, "reason": "version_ok"}

        updated = 0
        for soru, cevap in _CORE_PROFILES:
            motor._upsert_kayit(
                "Hafıza",
                soru,
                sanitize_gokcenur_hafiza_cevap(cevap, soru=soru),
            )
            updated += 1
        motor._upsert_kayit("Hafıza", _SEED_META_SORU, _CORE_SEED_VERSION)
        motor._sync_hafiza_view()
        motor._dosyaya_kaydet()
        _SEEDED = True
        return {"ok": True, "updated": updated, "version": _CORE_SEED_VERSION}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:160]}
