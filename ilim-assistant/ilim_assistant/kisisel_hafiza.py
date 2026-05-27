# Created by Umit & Gokcenur
"""Faz 13 — kişisel hafıza komutları.

LLM beklemeden basit "hatırla / unut / profil" komutlarını işler.
"""

from __future__ import annotations

import re


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).strip(" \t\r\n.:;")


def _parse_teach_qa(body: str) -> tuple[str, str]:
    """Doğal öğretme metninden soru/cevap çifti çıkar."""
    b = _clean(body)
    if not b:
        return "", ""
    eq = re.search(r"(?P<q>.+?)\s*=\s*(?P<a>.+)", b)
    if eq:
        return _clean(eq.group("q")), _clean(eq.group("a"))
    colon = re.search(r"(?P<q>.+?)\s*:\s*(?P<a>.+)", b)
    if colon and len(colon.group("q")) >= 8:
        return _clean(colon.group("q")), _clean(colon.group("a"))
    low = b.casefold()
    if ("güneş sistem" in low or "guness sistem" in low or "gunes sistem" in low) and any(
        x in low for x in ("samanyol", "galax", "galaks")
    ):
        return "bizim güneş sistemimiz hangi galaxide yer alır", b
    return b[:120], b


def _store_qa(soru: str, cevap: str) -> str:
    try:
        from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

        get_hafiza_motor().ekle_bilgi(soru, cevap)
    except Exception as exc:
        return f"Hafızaya yazamadım: {exc}"
    return f"Ümit abi, hafızaya yazdım.\nSoru: {soru[:120]}\nCevap: {cevap[:220]}"


def try_consume_memory_command(message: str) -> str | None:
    """Kullanıcı hafıza komutu verdiyse uygular ve tek cevap döner."""
    raw = _clean(message)
    if not raw or len(raw) > 2000:
        return None
    try:
        from ilim_assistant.nebula_kitap_hafiza import is_nebula_kitap_intent

        if is_nebula_kitap_intent(raw):
            return None
    except Exception:
        pass
    low = raw.casefold()

    teach_match = re.search(
        r"(?is)(?:sana\s+)?(?:öğretiyorum|ogretiyorum|öğret(?:iyorum)?)\s*[:\-–]?\s*(?P<body>.+)$",
        raw,
    )
    if teach_match:
        body = _clean(teach_match.group("body"))
        if len(body) < 6:
            return "Ümit abi, ne öğrettiğini biraz daha açık yazar mısın?"
        soru, cevap = _parse_teach_qa(body)
        if not cevap:
            return "Ümit abi, cevap kısmını anlayamadım — `hatırla: soru = cevap` da olur."
        return _store_qa(soru, cevap)

    remember_match = re.search(
        r"(?is)^(?:bunu\s+)?"
        r"(?:hat[ıi]rla|haf[ıi]zaya\s+al|not\s+al|kaydet)"
        r"(?:\s+ki)?\s*[:\-–]?\s*(?P<body>.+)$",
        raw,
    )
    remember_end_match = re.search(
        r"(?is)(?P<body>.+?)\s*(?:[,.\-–]?\s*)?"
        r"(?:bunu\s+)?(?:hat[ıi]rla|haf[ıi]zaya\s+al|kaydet)\s*[.!?…]*\s*$",
        raw,
    )
    profile_match = re.search(
        r"(?is)^(?:profilime\s+ekle|beni\s+tan[ıi]|"
        r"benim\s+i[çc]in\s+hat[ıi]rla)"
        r"\s*[:\-–]?\s*(?P<body>.+)$",
        raw,
    )
    active_remember = remember_match or remember_end_match
    if active_remember or profile_match:
        body = _clean((active_remember or profile_match).group("body"))
        if len(body) < 3:
            return "Mimar, neyi hatırlamamı istediğini biraz daha açık yazar mısın?"
        if "=" in body:
            soru, cevap = _parse_teach_qa(body)
            if soru and cevap:
                return _store_qa(soru, cevap).replace("Ümit abi", "Mimar", 1)
        key = f"Kişisel not: {body[:80]}"
        try:
            from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

            get_hafiza_motor().ekle_bilgi(key, body, motor_tipi="Hafıza")
        except Exception as exc:
            return f"Hafızaya yazamadım: {exc}"
        return f"Hatırladım Mimar: {body[:220]}"

    forget_match = re.search(
        r"(?is)^(?:unut|haf[ıi]zadan\s+sil)\s*[:\-–]?\s*(?P<body>.+)$",
        raw,
    )
    if forget_match:
        body = _clean(forget_match.group("body"))
        if len(body) < 2:
            return "Mimar, neyi unutacağımı belirtir misin?"
        try:
            from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

            motor = get_hafiza_motor()
            ok = motor.sil_bilgi(body, motor_tipi="Hafıza")
            if not ok:
                ok = motor.sil_bilgi(
                    f"Kişisel not: {body[:80]}",
                    motor_tipi="Hafıza",
                )
        except Exception as exc:
            return f"Hafızadan silemedim: {exc}"
        return "Sildim Mimar." if ok else "Bu anahtarla kayıt bulamadım Mimar."

    if low in {"beni tani", "beni tanı", "profilimi goster", "profilimi göster"}:
        try:
            from ilim_assistant.hafiza_i_ruzgar import get_hafiza_motor

            items = get_hafiza_motor().tum_bilgiler(motor_tipi="Hafıza")
        except Exception as exc:
            return f"Hafıza okunamadı: {exc}"
        notes = [(k, v) for k, v in items.items() if k.startswith("Kişisel not:")]
        if not notes:
            return "Mimar, kişisel profil hafızasında henüz özel not yok."
        lines = ["Mimar, kişisel profilimde şunlar var:"]
        for _, val in notes[-8:]:
            lines.append(f"- {val[:180]}")
        return "\n".join(lines)

    return None
