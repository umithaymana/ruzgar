# Created by Umit & Gokcenur
"""Faz 13 — kişisel hafıza komutları.

LLM beklemeden basit "hatırla / unut / profil" komutlarını işler.
"""

from __future__ import annotations

import re


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).strip(" \t\r\n.:;")


def try_consume_memory_command(message: str) -> str | None:
    """Kullanıcı hafıza komutu verdiyse uygular ve tek cevap döner."""
    raw = _clean(message)
    if not raw or len(raw) > 2000:
        return None
    low = raw.casefold()

    remember_match = re.search(
        r"(?is)^(?:bunu\s+)?"
        r"(?:hat[ıi]rla|haf[ıi]zaya\s+al|not\s+al|kaydet)"
        r"(?:\s+ki)?\s*[:\-–]?\s*(?P<body>.+)$",
        raw,
    )
    profile_match = re.search(
        r"(?is)^(?:profilime\s+ekle|beni\s+tan[ıi]|"
        r"benim\s+i[çc]in\s+hat[ıi]rla)"
        r"\s*[:\-–]?\s*(?P<body>.+)$",
        raw,
    )
    if remember_match or profile_match:
        body = _clean((remember_match or profile_match).group("body"))
        if len(body) < 3:
            return "Mimar, neyi hatırlamamı istediğini biraz daha açık yazar mısın?"
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
